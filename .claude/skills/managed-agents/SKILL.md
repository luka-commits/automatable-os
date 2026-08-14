---
name: managed-agents
description: Create and operate Anthropic Claude Managed Agents (hosted cloud agents) via the beta API, directly from Claude Code with curl. Use this whenever the user wants to create a managed agent, run an agent in Anthropic's cloud, build a customer-facing hosted agent, package or upload a Claude Code skill so a hosted agent can invoke it, set up multiagent coordinator sessions, store credentials in vaults, or wire human-in-the-loop gates into an API-driven agent. Also use for operating existing managed agents, sessions, environments, events, debugging runs, or any mention of /v1/agents, /v1/sessions, /v1/environments, /v1/skills, agent sessions, or "managed agent" in any language.
---

# Claude Managed Agents

Build and operate hosted agents on Anthropic's infrastructure from inside Claude Code. Everything runs over plain curl, no SDK install needed.

## Core mental model

Four resources, created in this order, referenced by ID:

| Resource | What it is | Endpoint |
|----------|-----------|----------|
| **Agent** | Versioned config: model, system prompt, tools, MCP servers, skills, multiagent roster | `/v1/agents` |
| **Environment** | Sandbox config: packages, networking. Each session gets a FRESH isolated Linux container | `/v1/environments` |
| **Vault** (optional) | Per-user credentials: MCP auth + env-var secrets, injected at runtime | `/v1/vaults` |
| **Session** | A running agent instance. Driven by events you send; emits events you stream | `/v1/sessions` |

Create agent + environment once, reuse across many sessions. A session does nothing until you send a `user.message` event.

## Prerequisites

- `ANTHROPIC_API_KEY` lives in `~/.config/credentials.env`. Source it: `source ~/.config/credentials.env`
- Every Managed Agents request needs these headers (define once per script):

```bash
H=(-H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" -H "anthropic-beta: managed-agents-2026-04-01" -H "content-type: application/json")
BASE=https://api.anthropic.com
```

- Skill UPLOAD uses a DIFFERENT beta header: `skills-2025-10-02` (see `references/patterns.md`).

## Cost gate, check before creating anything

Managed agents bill the **API account** (tokens + session runtime), not the Claude subscription. Before creating a session that will do real work, confirm scope with the user: which model, roughly how long, what budget. For work Claude can do in-session or via subagents, do it in-session instead, that is already paid for. Managed agents are for genuinely autonomous, hosted, or customer-facing runs. Reads (list/get/stream) are cheap; sessions doing work are not.

## Build flow

### 1. Create the agent

```bash
agent=$(curl -fsS "$BASE/v1/agents" "${H[@]}" -d '{
  "name": "My Agent",
  "model": "claude-opus-4-8",
  "system": "You are ...",
  "tools": [{"type": "agent_toolset_20260401"}]
}')
AGENT_ID=$(jq -r '.id' <<<"$agent")
```

- `agent_toolset_20260401` = bash, read, write, edit, glob, grep, web_fetch, web_search. Disable per tool via `configs: [{"name": "web_fetch", "enabled": false}]`.
- Add `skills`, `mcp_servers`, `multiagent`, custom tools as needed (see references).
- Model choice matters for cost: haiku for mechanical work, sonnet default, opus for orchestration/synthesis.
- Updates create a new version; sessions can pin a version. Omitted fields are preserved, arrays are fully replaced.

### 2. Create the environment

```bash
env_id=$(curl -fsS "$BASE/v1/environments" "${H[@]}" -d '{
  "name": "my-env",
  "config": {
    "type": "cloud",
    "packages": {"pip": ["httpx"], "npm": []},
    "networking": {"type": "unrestricted"}
  }
}' | jq -r '.id')
```

- `name` must be unique in the workspace. Packages are cached across sessions of the same environment.
- Production: use `"networking": {"type": "limited", "allowed_hosts": [...], "allow_package_managers": true, "allow_mcp_servers": true}`.

### 3. Create a session and start work

```bash
session_id=$(curl -fsS "$BASE/v1/sessions" "${H[@]}" -d "{
  \"agent\": \"$AGENT_ID\",
  \"environment_id\": \"$env_id\"
}" | jq -r '.id')

curl -fsS "$BASE/v1/sessions/$session_id/events" "${H[@]}" -d '{
  "events": [{"type": "user.message", "content": [{"type": "text", "text": "Do the task..."}]}]
}'
```

Optional session params: `vault_ids` (credentials), `title`, pin agent version via `"agent": {"type": "agent", "id": ..., "version": N}`.

### 4. Stream or poll the results

```bash
# Stream (SSE). agent.message = text output, session.status_idle = turn done
curl -fsSN "$BASE/v1/sessions/$session_id/events/stream?beta=true" "${H[@]}"

# Or poll the event list
curl -fsS "$BASE/v1/sessions/$session_id/events" "${H[@]}" | jq -r '.data[] | .type'
```

Watch for `session.status_idle` with `stop_reason`. `requires_action` means the agent is blocked waiting for you: a tool confirmation or a custom tool result. Answer with `user.tool_confirmation` or `user.custom_tool_result` events. That mechanism is the human-in-the-loop bridge (full pattern in `references/patterns.md`).

## Go deeper

- **`references/api.md`**: full endpoint reference, agent/environment/vault config fields, complete event-type catalog, session operations, rate limits.
- **`references/patterns.md`**: working recipes. Read it when the task involves any of:
  - HITL gates (external human answers questions mid-run) → Pattern 1
  - Multiagent coordinator + specialist roster → Pattern 2
  - Packaging an existing Claude Code skill / command and uploading it so the hosted agent invokes it → Pattern 3
  - Secrets for CLIs/APIs in the sandbox (vault env-var credentials) → Pattern 4
  - Monitoring, debugging, interrupting, cost tracking → Pattern 5

## Gotchas that bite (learned from the docs, save yourself the debugging)

1. **Two different beta headers.** Managed Agents = `managed-agents-2026-04-01`. Skill upload = `skills-2025-10-02`. Mixing them up gives confusing 4xx errors.
2. **Fresh sandbox per session.** Sessions sharing an environment do NOT share filesystem state. Anything the agent needs (repo, data) must arrive via skill bundle, git clone at runtime, or instructions.
3. **Skill `name` constraints**: lowercase/numbers/hyphens, max 64 chars, and the words "anthropic" and "claude" are FORBIDDEN in the name. `description` max 1024 chars. Upload max 30 MB, `SKILL.md` required at top level.
4. **Coordinator pins roster versions.** Updating a sub-agent does NOT propagate to coordinators that list it. After updating any roster agent, update the coordinator too, or it keeps delegating to the old version.
5. **Vault env-var secrets substitute at EGRESS only.** Inside the sandbox the agent sees an opaque placeholder. Clients that validate key format at startup, or compute signatures (AWS SigV4), break. OAuth token exchanges return tokens unredacted. Plain bearer-token API calls work fine.
6. **Vault networking AND environment networking must both allow a host** for a secret-substituted request to succeed.
7. **Limits**: 20 skills/session, 20 credentials/vault, 20 agents in a roster, 25 concurrent threads, 1 level of delegation depth. Rate limits: 300 rpm create, 600 rpm read.
8. **`system.message` (live system-prompt update) only works on Opus 4.8.**
9. **Archive vs delete**: archive = read-only, running sessions continue. Delete vault/credential = hard delete. Skill delete requires deleting all versions first.
10. **Not ZDR/HIPAA eligible.** Session data is retained server-side until you delete the session. Flag this for sensitive client data.
11. **Sessions are created idle.** Creating a session provisions the sandbox but runs nothing until the first `user.message` event arrives.
