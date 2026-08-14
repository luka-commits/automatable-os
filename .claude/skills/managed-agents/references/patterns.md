# Managed Agents: Working Patterns

Recipes for the recurring builds. All assume the header array from SKILL.md:

```bash
source ~/.config/credentials.env
H=(-H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" -H "anthropic-beta: managed-agents-2026-04-01" -H "content-type: application/json")
BASE=https://api.anthropic.com
```

## Contents

1. [Pattern 1: Human-in-the-loop gates via custom tools](#pattern-1-hitl)
2. [Pattern 2: Multiagent coordinator + specialist roster](#pattern-2-multiagent)
3. [Pattern 3: Package a Claude Code skill and let the hosted agent invoke it](#pattern-3-skill-packaging)
4. [Pattern 4: Secrets in the sandbox (vault env-var credentials)](#pattern-4-secrets)
5. [Pattern 5: Operate, monitor, debug, track cost](#pattern-5-operate)

<a name="pattern-1-hitl"></a>
## Pattern 1: Human-in-the-loop gates via custom tools

The mechanism: define a custom tool the agent is instructed to call whenever it needs a human decision. The agent calls it, the session goes idle with `stop_reason.type = "requires_action"`, and stays paused (no billing for model time while idle) until you send the answer back. Works for external users answering via a web UI just as well as for yourself.

### 1. Define the gate tool on the agent

```json
{
  "type": "custom",
  "name": "ask_user",
  "description": "Ask the human a question and wait for their answer before continuing. Use this at every decision gate: when assumptions need sign-off, when a plan needs approval before execution, or when a choice between alternatives requires human judgment. Pass clear context and concrete options. Do not proceed past a gate without calling this tool.",
  "input_schema": {
    "type": "object",
    "properties": {
      "question": {"type": "string", "description": "The question, with enough context to answer it cold"},
      "options": {"type": "array", "items": {"type": "string"}, "description": "Concrete answer options, if applicable"}
    },
    "required": ["question"]
  }
}
```

Reinforce in the system prompt WHERE the gates are ("after drafting assumptions, call ask_user and wait", etc.). The tool description tells it how, the system prompt tells it when.

### 2. Detect the pause

Poll or stream until idle + requires_action, then read the pending question:

```bash
# Wait for the gate
while :; do
  status=$(curl -fsS "$BASE/v1/sessions/$session_id" "${H[@]}" | jq -r '.status')
  [ "$status" = "idle" ] && break
  sleep 10
done

# Find the unanswered custom tool call (the question payload)
curl -fsS "$BASE/v1/sessions/$session_id/events" "${H[@]}" \
  | jq -r '.data[] | select(.type == "agent.custom_tool_use") | {id, name: .name, input}'
```

In multiagent sessions the blocking event is cross-posted to the primary thread with `session_thread_id`; reply at the session level, routing is automatic.

### 3. Send the human's answer, run resumes

```bash
curl -fsS "$BASE/v1/sessions/$session_id/events" "${H[@]}" -d "{
  \"events\": [{
    \"type\": \"user.custom_tool_result\",
    \"custom_tool_use_id\": \"$TOOL_USE_ID\",
    \"content\": [{\"type\": \"text\", \"text\": \"Answer: option B. Also tighten the target customer to X.\"}]
  }]
}"
```

The session picks up exactly where it stopped, full context intact. The same shape with `user.tool_confirmation` (`{tool_use_id, result: "allow"|"deny"}`) answers permission-gated built-in/MCP tools.

For a customer-facing product: your backend streams events, renders each `agent.custom_tool_use` as a UI form, POSTs the customer's answer back as `user.custom_tool_result`. The session ID is the only state you need to store.

<a name="pattern-2-multiagent"></a>
## Pattern 2: Multiagent coordinator + specialist roster

Use when work fans out (parallel research lanes, review + synthesis pipelines). All agents share one sandbox and filesystem, so file-based handoff works: specialists write files, coordinator reads them. Each agent has its own context, config, model, and skills.

### Build order matters

Specialists first, coordinator last (the roster references their IDs and pins their versions):

```bash
researcher_id=$(curl -fsS "$BASE/v1/agents" "${H[@]}" -d '{
  "name": "researcher",
  "model": "claude-sonnet-4-6",
  "system": "<the specialist persona, methodology, honesty rules, output file conventions>",
  "tools": [{"type": "agent_toolset_20260401"}]
}' | jq -r '.id')

critic_id=$(... same shape ...)

coordinator_id=$(curl -fsS "$BASE/v1/agents" "${H[@]}" -d "{
  \"name\": \"orchestrator\",
  \"model\": \"claude-opus-4-8\",
  \"system\": \"<orchestration logic: what to delegate, in what waves, where outputs land>\",
  \"tools\": [{\"type\": \"agent_toolset_20260401\"}, <custom gate tools>],
  \"multiagent\": {
    \"type\": \"coordinator\",
    \"agents\": [
      {\"type\": \"agent\", \"id\": \"$researcher_id\"},
      {\"type\": \"agent\", \"id\": \"$critic_id\"}
    ]
  }
}" | jq -r '.id')
```

- The coordinator can invoke multiple copies of one roster agent (parallel lanes), up to 25 concurrent threads.
- Migrating a Claude Code setup: each `.claude/agents/*.md` body becomes a specialist's `system` prompt. The orchestrating skill's "spawn subagent X" instructions translate to "delegate to the X agent in your roster".
- **After updating any specialist, update the coordinator** (even a no-op-looking update that re-lists the roster), otherwise it keeps delegating to the pinned old version.
- Skills count: max 20 across ALL agents in a session. MCP servers are per-agent; vault credentials are session-wide.

Monitor per-specialist work via thread endpoints (`GET /v1/sessions/$sid/threads`, then `/threads/$tid/events`). The primary stream shows thread starts/ends + results delivered (`agent.thread_message_received`).

<a name="pattern-3-skill-packaging"></a>
## Pattern 3: Package a Claude Code skill and let the hosted agent invoke it

The highest-leverage pattern: an existing `.claude/skills/<name>/` or `.claude/commands/<name>.md` becomes a custom skill the hosted agent invokes on demand (progressive disclosure: metadata always loaded, body on trigger, bundled files on use). Scripts bundled in the skill ARE the way to ship code into the sandbox.

### 3a. Convert to Agent Skill layout

```
my-skill/
├── SKILL.md          required at top level
├── reference-*.md    optional deep-dive docs
└── scripts/          optional executables the agent runs via bash
```

- `.claude/skills/<name>/` sources: often already this shape, copy as-is.
- `.claude/commands/<name>.md` sources: the command body becomes the SKILL.md body below a fresh frontmatter.

Frontmatter rules (upload validates them): `name` lowercase/numbers/hyphens, max 64 chars, must NOT contain "claude" or "anthropic"; `description` non-empty, max 1024 chars, no XML tags.

### 3b. Adapt Claude-Code-isms before upload

Scan the skill body for constructs that mean nothing in the Managed Agents harness and translate them:

| Claude Code construct | Managed Agents translation |
|---|---|
| `AskUserQuestion` / "wait for user" | Call the `ask_user` custom tool (Pattern 1); define it on the agent |
| `Agent` tool / "spawn subagent_type X" | "Delegate to the X agent" via multiagent roster (Pattern 2) |
| References to `.claude/rules/`, other skills, CLAUDE.md | Inline the needed content into the skill bundle as reference files |
| Local repo paths (`scripts/foo.py`, `clients/<slug>/...`) | Bundle scripts inside the skill; have the session create working dirs in the sandbox |
| Tool CLIs assumed installed (firecrawl etc.) | Environment `packages` (pip/npm) + vault env-var secrets (Pattern 4) |
| `/effort max`, model switches | Set per-agent `model` at agent creation |

### 3c. Upload (note the DIFFERENT beta header)

```bash
cd /path/to/parent && zip -r my-skill.zip my-skill/

skill=$(curl -fsS -X POST "$BASE/v1/skills" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "display_title=My Skill" \
  -F "files[]=@my-skill.zip")
SKILL_ID=$(jq -r '.id' <<<"$skill")
```

New version after edits: `POST /v1/skills/$SKILL_ID/versions` with the new zip. Agents referencing `"version": "latest"` pick it up on the next session.

### 3d. Attach + verify

```bash
# Attach (update agent; arrays are replaced wholesale, include ALL skills)
curl -fsS "$BASE/v1/agents/$AGENT_ID" "${H[@]}" -d "{
  \"version\": $AGENT_VERSION,
  \"skills\": [{\"type\": \"custom\", \"skill_id\": \"$SKILL_ID\", \"version\": \"latest\"}]
}"
```

Verify with a cheap smoke session: send "List the skills available to you, then read the main instructions of <skill name> and summarize its workflow in 5 bullets. Do not execute it." If the summary matches the skill, the wiring works.

### Keep the local skill canonical

Treat the local Claude Code skill as the single source of truth and the uploaded copy as a build artifact. Re-upload (new version) whenever the local one changes; a small sync script (zip + POST versions) makes drift a non-issue.

<a name="pattern-4-secrets"></a>
## Pattern 4: Secrets in the sandbox (vault env-var credentials)

For CLIs/SDKs/API calls inside the sandbox that need keys (OpenRouter, Firecrawl, Apify, ...):

```bash
vault_id=$(curl -fsS "$BASE/v1/vaults" "${H[@]}" -d '{"display_name": "project-secrets"}' | jq -r '.id')

curl -fsS "$BASE/v1/vaults/$vault_id/credentials" "${H[@]}" -d '{
  "display_name": "OpenRouter key",
  "auth": {
    "type": "environment_variable",
    "secret_name": "OPENROUTER_API_KEY",
    "secret_value": "sk-or-...",
    "networking": {"type": "limited", "allowed_hosts": ["openrouter.ai", "*.openrouter.ai"]}
  }
}'
```

Then pass `"vault_ids": ["$vault_id"]` at session creation.

How it actually works, and what breaks:
- The sandbox env var contains an opaque placeholder. The real value is substituted at network egress, only toward `allowed_hosts`.
- The TARGET HOST must also be reachable per the ENVIRONMENT networking config. Both layers must allow it.
- Works: any client that sends the key verbatim in a header/body (typical bearer-token APIs: OpenRouter, Firecrawl, Apify).
- Breaks: clients validating key format at startup, request-signing schemes (AWS SigV4). OAuth client-credential exchanges return live tokens unredacted; do the exchange outside and store the resulting token instead.
- One vault per end user is the intended model for customer products (`metadata.external_user_id` maps to your user records). Max 20 credentials per vault.

For MCP servers use `mcp_oauth` (auto-refresh) or `static_bearer`, keyed by exact `mcp_server_url`.

<a name="pattern-5-operate"></a>
## Pattern 5: Operate, monitor, debug, track cost

```bash
# Session status at a glance
curl -fsS "$BASE/v1/sessions/$session_id" "${H[@]}" | jq '{id, status, title}'

# Tail recent activity (types only)
curl -fsS "$BASE/v1/sessions/$session_id/events" "${H[@]}" | jq -r '.data[-15:][] | .type'

# Pull the latest agent text
curl -fsS "$BASE/v1/sessions/$session_id/events" "${H[@]}" \
  | jq -r '[.data[] | select(.type == "agent.message")][-1].content[] | select(.type == "text") | .text'

# Stop a runaway session
curl -fsS "$BASE/v1/sessions/$session_id/events" "${H[@]}" -d '{"events": [{"type": "user.interrupt"}]}'

# Cost: sum model usage from span events
curl -fsS "$BASE/v1/sessions/$session_id/events" "${H[@]}" \
  | jq '[.data[] | select(.type == "span.model_request_end") | .model_usage] | length as $calls | {model_calls: $calls, usage: .}'
```

Operating notes:
- `session.status_rescheduled` = transient error, auto-retrying, no action needed. `session.status_terminated` = dead, read `session.error` for the typed reason.
- There is no built-in per-session budget cap. Cost control = model choice per agent, scoped task prompts, watching `span.model_request_end` usage, and `user.interrupt` when something runs long. For customer products, meter on your side before starting sessions.
- Long-running session with intermittent input: the session persists server-side indefinitely until deleted; idle time costs nothing in model tokens. Resume any time by sending the next event to the same session ID.
- Cleanup discipline: archive agents/environments you iterate away from (keeps history), DELETE sessions containing data you do not want retained (Managed Agents is not ZDR-eligible).
- Live debugging of one specialist in a multiagent run: `GET /v1/sessions/$sid/threads` to find the thread, then stream `/threads/$tid/stream?beta=true` to watch its reasoning and tool calls.
