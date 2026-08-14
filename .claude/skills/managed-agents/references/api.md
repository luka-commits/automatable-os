# Managed Agents API Reference

Base URL `https://api.anthropic.com`. All requests: `x-api-key`, `anthropic-version: 2023-06-01`, `anthropic-beta: managed-agents-2026-04-01`. Skill upload endpoints use `anthropic-beta: skills-2025-10-02` instead.

## Contents

1. [Endpoints overview](#endpoints-overview)
2. [Agent configuration](#agent-configuration)
3. [Tools](#tools)
4. [Environment configuration](#environment-configuration)
5. [Vaults and credentials](#vaults-and-credentials)
6. [Sessions](#sessions)
7. [Event type catalog](#event-type-catalog)
8. [Skills API (upload)](#skills-api-upload)
9. [Limits](#limits)

## Endpoints overview

| Method + path | Purpose |
|---|---|
| `POST /v1/agents` | Create agent |
| `GET /v1/agents` / `GET /v1/agents/{id}` | List / retrieve |
| `POST /v1/agents/{id}` | Update (pass current `version`, creates new version on change) |
| `GET /v1/agents/{id}/versions` | Version history |
| `POST /v1/agents/{id}/archive` | Archive (read-only) |
| `POST /v1/environments` | Create environment |
| `GET /v1/environments` / `GET .../{id}` | List / retrieve |
| `POST /v1/environments/{id}/archive` | Archive |
| `DELETE /v1/environments/{id}` | Delete (only if no sessions reference it) |
| `POST /v1/vaults` | Create vault |
| `POST /v1/vaults/{id}/credentials` | Add credential |
| `POST /v1/vaults/{vid}/credentials/{cid}` | Rotate credential (secret values + display_name only) |
| `POST /v1/vaults/{vid}/credentials/{cid}/mcp_oauth_validate` | Diagnose OAuth refresh failure (valid/invalid/unknown) |
| `POST /v1/vaults/{id}/archive`, `DELETE /v1/vaults/{id}` | Archive (purges secrets, keeps audit record) / hard delete |
| `POST /v1/sessions` | Create session (provisions sandbox, runs nothing yet) |
| `POST /v1/sessions/{id}/events` | Send events (`?beta=true` query also accepted) |
| `GET /v1/sessions/{id}/events` | List event history (paginated) |
| `GET /v1/sessions/{id}/events/stream` | SSE stream |
| `GET /v1/sessions/{id}/threads` | List multiagent threads |
| `GET /v1/sessions/{sid}/threads/{tid}/events` / `.../stream` | Per-thread events |
| `POST /v1/sessions/{sid}/threads/{tid}/archive` | Archive thread (must be idle, frees the 25-thread cap) |
| `DELETE /v1/sessions/{id}` | Delete session + its server-side data |
| `POST /v1/skills` | Upload custom skill (beta header `skills-2025-10-02`) |
| `POST /v1/skills/{id}/versions` | New skill version |
| `GET /v1/skills?source=custom` | List skills |
| `DELETE /v1/skills/{id}` | Delete (all versions must be deleted first, else 400) |

## Agent configuration

```json
{
  "name": "required, human-readable",
  "model": "claude-opus-4-8  (or object: {\"id\": \"claude-opus-4-8\", \"speed\": \"fast\"})",
  "system": "system prompt, persona + behavior. User messages carry the actual task",
  "description": "optional",
  "tools": [ ... ],
  "mcp_servers": [{"type": "url", "name": "github", "url": "https://..."}],
  "skills": [
    {"type": "anthropic", "skill_id": "xlsx"},
    {"type": "custom", "skill_id": "skill_abc123", "version": "latest"}
  ],
  "multiagent": {
    "type": "coordinator",
    "agents": [
      {"type": "agent", "id": "agent_..."},
      {"type": "agent", "id": "agent_...", "version": 2},
      {"type": "self"}
    ]
  },
  "metadata": {"any": "tracking keys"}
}
```

- All Claude 4.5-family and later models supported. Fast mode: pass model as object with `"speed": "fast"` (Opus 4.6/4.7/4.8).
- Response adds `id`, `version` (starts at 1), `created_at`, `updated_at`, `archived_at`.
- Update semantics: omitted fields preserved, scalars replaced (`system`/`description` clearable with null), arrays fully replaced, metadata merged per key (empty string deletes a key), no-op updates create no version.
- Multiagent: roster entries pin to the version resolved at coordinator create/update time. Max 20 unique agents, 1 level of delegation, coordinator can spawn multiple copies of one agent. `{"type": "self"}` lets it clone itself.

## Tools

### Built-in toolset

`{"type": "agent_toolset_20260401"}` enables: `bash`, `read`, `write`, `edit`, `glob`, `grep`, `web_fetch`, `web_search`. Tool output over 100k tokens is auto-written to a sandbox file, model gets a truncated preview + path.

Per-tool config:

```json
{"type": "agent_toolset_20260401",
 "configs": [{"name": "web_fetch", "enabled": false}]}
```

Allowlist style (everything off, enable selected):

```json
{"type": "agent_toolset_20260401",
 "default_config": {"enabled": false},
 "configs": [{"name": "bash", "enabled": true}, {"name": "read", "enabled": true}]}
```

`default_config` also carries `permission_policy`, e.g. `{"type": "always_allow"}`. A policy requiring confirmation makes the session stop with `requires_action` and wait for `user.tool_confirmation`.

### MCP tools

Declare server in `mcp_servers`, expose via `{"type": "mcp_toolset", "mcp_server_name": "github"}`. Remote HTTP servers (streamable HTTP transport) or private servers via MCP tunnels (research preview). Auth via vault credentials matched on `mcp_server_url` (exact match incl. scheme + trailing slash).

### Custom tools

Client-executed tools, same idea as Messages API user-defined tools:

```json
{"type": "custom", "name": "get_weather", "description": "3-4+ sentences: what, when, params, caveats",
 "input_schema": {"type": "object", "properties": {...}, "required": [...]}}
```

Flow: agent emits `agent.custom_tool_use` event, session goes idle with `stop_reason.type = "requires_action"`, you execute and reply with `user.custom_tool_result`. This is also the HITL mechanism (patterns.md Pattern 1).

Best practices from the docs: very detailed descriptions, consolidate related ops into one tool with an `action` param, namespace names (`db_query`), return only high-signal fields.

## Environment configuration

```json
{
  "name": "unique-per-workspace",
  "config": {
    "type": "cloud",
    "packages": {
      "apt": ["ffmpeg"], "pip": ["pandas==2.2.0"], "npm": ["express@4.18.0"],
      "cargo": ["ripgrep@14.0.0"], "gem": ["rails:7.1.0"], "go": ["golang.org/x/tools/cmd/goimports@latest"]
    },
    "networking": {"type": "unrestricted"}
  }
}
```

- Package managers run alphabetically: apt, cargo, gem, go, npm, pip. Installed before agent starts, cached across sessions of the same environment. Version pinning optional, default latest.
- Networking `limited`: `{"type": "limited", "allowed_hosts": ["api.example.com", "*.example.com"], "allow_mcp_servers": true, "allow_package_managers": true}`. Bare hostnames or wildcards, no scheme. Does not affect `web_search`/`web_fetch` tools.
- Environments are NOT versioned. Each session gets a fresh isolated sandbox, no filesystem sharing between sessions.
- Cloud sandboxes ship common runtimes preinstalled (python3, node, etc.), see cloud-sandboxes-reference doc page.
- Self-hosted sandboxes exist (`type: self_hosted`) for compliance/data residency: you run a worker (`ant beta:worker`) on your own infra. Env-var vault credentials not supported there.

## Vaults and credentials

Vault = collection of credentials for one end user. Workspace-scoped (any API key in the workspace can reference). Pass at session creation: `"vault_ids": ["vlt_..."]`.

Three credential types (`auth.type`):

| Type | Key field | Use for | Notes |
|---|---|---|---|
| `mcp_oauth` | `mcp_server_url` | OAuth MCP servers | Supply `access_token` + optional `refresh` block; Anthropic auto-refreshes. Validate failures via `mcp_oauth_validate` |
| `static_bearer` | `mcp_server_url` | MCP servers with fixed token | API key / PAT |
| `environment_variable` | `secret_name` | CLIs, SDKs, direct API calls | Sandbox sees an opaque placeholder; real value substituted at EGRESS only, scoped by credential-level `networking.allowed_hosts` |

Egress substitution caveats (critical): clients that validate key format locally may reject the placeholder; signature schemes (AWS SigV4) produce invalid signatures; OAuth client-credentials exchanges return live tokens unredacted into the sandbox (do the exchange yourself, store the result instead). Plain "send the secret verbatim in a header" clients work.

Constraints: keys unique per vault (409 on duplicate), keys immutable (archive + recreate to change), max 20 credentials/vault. Secret values are write-only, never returned. Credentials re-resolve periodically during sessions, so rotation propagates without restart. Webhooks exist for `vault.archived/deleted`, `vault_credential.archived/deleted/refresh_failed`.

Runtime: no matching credential = unauthenticated attempt; multiple matching vaults = first match wins; in multiagent sessions vault credentials apply to every thread, but only agents that declare the matching MCP server in their own definition connect to it.

## Sessions

Create:

```json
{"agent": "agent_id-or-object", "environment_id": "env_...", "vault_ids": ["vlt_..."], "title": "optional"}
```

Pin version: `"agent": {"type": "agent", "id": "...", "version": 1}`.

Lifecycle: created idle → first `user.message` starts work → statuses `running` / `idle` (with `stop_reason`) / `rescheduled` (auto-retrying transient error) / `terminated` (unrecoverable). Steer mid-run by sending more `user.message` events; stop with `user.interrupt`. Delete session to purge server-side data.

Multiagent: session-level event stream = primary thread (condensed view: thread starts/ends + blocking events cross-posted with `session_thread_id`). Drill into a specific agent via thread endpoints. Session status aggregates: one running thread = session running.

## Event type catalog

You send (user/system events):

| Type | Purpose |
|---|---|
| `user.message` | Text content blocks. Starts/continues/steers work |
| `user.interrupt` | Stop mid-execution. With `session_thread_id` targets one thread. Against `requires_action` it denies pending calls; against idle it is a no-op |
| `user.tool_confirmation` | `{tool_use_id, result: "allow"/"deny"}` for permission-gated tools |
| `user.custom_tool_result` | `{custom_tool_use_id, content}` answering an `agent.custom_tool_use` |
| `user.define_outcome` | Define an outcome the agent works toward (see define-outcomes docs) |
| `user.tool_result` | Self-hosted environments only |
| `system.message` | Update system prompt between turns. Opus 4.8 only |

You receive (agent events):

| Type | Purpose |
|---|---|
| `agent.message` | Text response blocks |
| `agent.thinking` | Thinking content |
| `agent.tool_use` / `agent.tool_result` | Built-in tool calls + results |
| `agent.mcp_tool_use` / `agent.mcp_tool_result` | MCP calls |
| `agent.custom_tool_use` | Custom tool call, answer it via `user.custom_tool_result` |
| `agent.thread_context_compacted` | History compacted to fit context |
| `agent.thread_message_received` / `agent.thread_message_sent` | Multiagent: result delivered to coordinator / follow-up sent |

You receive (session events):

| Type | Purpose |
|---|---|
| `session.status_running` / `status_idle` / `status_rescheduled` / `status_terminated` | Lifecycle. `idle` carries `stop_reason`; `requires_action` includes `event_ids` of blocking calls |
| `session.updated`, `session.deleted`, `session.error` | Admin + errors (`error.retry_status`) |
| `session.thread_created` / `thread_status_*` | Multiagent thread lifecycle (with `agent_name`) |

Span events (observability): `span.model_request_start` / `span.model_request_end` (carries `model_usage` token counts, use for cost tracking), `span.outcome_evaluation_*`.

Every event has `processed_at` (null = still queued).

## Skills API (upload)

Beta header: `skills-2025-10-02`. Multipart form. `SKILL.md` required at top level of a common root dir. Max 30 MB total.

```bash
curl -fsS -X POST "https://api.anthropic.com/v1/skills" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "display_title=My Skill" \
  -F "files[]=@myskill.zip"
```

Response: `{"id": "skill_01...", "latest_version": "1759178010641129", "source": "custom", ...}`. Versions are epoch timestamps. New version: `POST /v1/skills/{id}/versions` with new files. List: `GET /v1/skills?source=custom`. Delete: all versions first (`DELETE /v1/skills/{id}/versions/{v}`), then the skill, else 400.

Frontmatter constraints: `name` max 64 chars, lowercase/numbers/hyphens, no XML tags, must NOT contain "anthropic" or "claude". `description` non-empty, max 1024 chars, no XML tags.

Attach to agent: `"skills": [{"type": "custom", "skill_id": "skill_01...", "version": "latest"}]`. Pre-built Anthropic skills: `{"type": "anthropic", "skill_id": "xlsx"}` (also pptx, docx, pdf). Max 20 skills per session counted across all agents.

Custom skills are workspace-wide on the API surface. They do NOT sync from claude.ai or Claude Code; upload separately.

## Limits

| Limit | Value |
|---|---|
| Create endpoints | 300 requests/min/org |
| Read endpoints | 600 requests/min/org |
| Concurrent multiagent threads | 25 |
| Roster size | 20 unique agents |
| Delegation depth | 1 |
| Skills per session | 20 |
| Credentials per vault | 20 |
| Skill upload size | 30 MB |
| Tool output before file-spill | 100k tokens |

Branding note for customer-facing products: "Claude Agent" or "Powered by Claude" allowed, "Claude Code" branding not permitted. ZDR and HIPAA BAA not available for Managed Agents.
