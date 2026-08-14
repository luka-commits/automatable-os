# Judging code: inherited criteria

Read when `/audit` should judge a single repo — that is, when the user says "take a closer look at X" after the report. **Not** on the default run: there the code tile measures mechanically only (README, uncommitted work, dormant repos) and reads no code.

## Two sources, both without an API

**First source: what counts as a real finding.** The exclusion list further down comes from Anthropic's `claude-code-security-review` (public on GitHub; the substance sits in `claudecode/claude_api_client.py` and `claudecode/findings_filter.py`).

**That Python is not executed.** It calls the Anthropic API directly (`ANTHROPIC_API_KEY` is mandatory, or the client aborts) and is cut for pull-request diffs, not folders. Neither fits: the API would be billed on top of the subscription for a judgement that the session makes with the same criteria anyway, and a folder is not a diff.

**What we take is the valuable part:** a tested list of false-alarm patterns. That is exactly where review tools otherwise fail — not at finding, at not-reporting.

**Second source: how to arrive at a confident judgement.** The official `code-review` plugin does it without an API, entirely with subagents, and its structure carries over:

- **Several angles in parallel rather than one thorough pass.** There: compliance with the CLAUDE.md · a shallow bug scan over the changes only · git history of the affected code · earlier remarks on the same files · code comments as instructions. A single pass systematically finds less, because it only asks one question.
- **Then a separate confidence round.** Every find is scored 0 to 100 by its own cheap agent — 0 means "would not survive a light check", 100 means "directly evidenced". **Anything under 80 is dropped.** That the checker is not the finder is the point: whoever found something wants to keep it.
- **Its false-alarm examples apply here too:** pre-existing problems · things that look like a bug and are not · trivia an experienced developer would not raise · anything a linter, type checker or compiler catches anyway · general quality topics such as missing tests, unless the CLAUDE.md explicitly demands them.

**Why we still do not call it directly:** `/code-review` works on a pull request (`gh pr diff`), not on a folder. For a single repo with an open PR it is the right command and gets recommended. For a folder audit the form is wrong, but the method is right.

## Approach

Three phases, in this order:

1. **Understand the context.** Which security building blocks does the repo already use (framework, validation, auth)? What is its threat model? Without that you judge patterns instead of risks.
2. **Compare.** Does new code deviate from the repo's established patterns? Deviation is the strongest signal, stronger than any pattern list.
3. **Assess.** Follow the data flow from input to the sensitive operation. Where are trust boundaries crossed?

## Severities

- **high** — directly exploitable: code execution, data exfiltration, bypassed authentication
- **medium** — needs particular conditions, but has real effect once they hold. **Only report when obvious and concrete**
- **low** — defence in depth. When in doubt, leave it out

**Confidence below 0.7 is not reported.** The test: can you name a concrete attack path, or is it a pattern that theoretically looks dangerous?

## The exclusion list

The heart of it. These things are **not** reported, even when they stand out:

**Out on principle**
- Denial of service, resource exhaustion, missing rate limiting, memory or CPU consumption
- Missing hardening. Code does not have to satisfy a best-practice collection, only avoid obvious holes
- Outdated third-party libraries. That is managed elsewhere
- Files that are purely tests
- Crashes that are not a vulnerability (an undefined variable is not a security problem)
- Missing or mutable audit logs
- Resource leaks (memory, file descriptors)

**Harmless despite looking dangerous**
- Environment variables and CLI flags are **trusted**. An attack that presupposes controlling them is not one
- UUIDs count as unguessable and do not need validating
- React is safe against XSS by default, except for `dangerouslySetInnerHTML` and relatives
- Client-side TypeScript needs no permission check. That is the server's job. The same goes for anything that sends data to a backend
- SSRF and path traversal in client code (`.js`, `.ts`, `.tsx`) are invalid: client code does not reach internal resources
- SSRF that only controls the path is not SSRF. Only host or protocol count
- `../` in HTTP requests is usually uncritical. It matters when reading files
- User input in AI prompts is not in itself a vulnerability
- Log spoofing through unsanitised echo is not a vulnerability. Logging URLs counts as safe, logging request headers as dangerous (credentials)
- Logging non-personal data is not a vulnerability, even when the data feels sensitive. Only report what exposes secrets, passwords or personal data
- Command injection in shell scripts only with a concrete path for foreign input: shell scripts rarely run on foreign input
- Vulnerabilities in GitHub Action workflows and notebooks only with a very concrete attack path
- Subtle web topics: tabnabbing, XS-leaks, prototype pollution, open redirects
- Race conditions and timing attacks, unless genuinely severe
- Memory safety in Rust (it does not exist there)

**In after all:** logging secrets in clear text is a vulnerability.

## Output

Per finding: file and line · severity · category · what happens · **concrete attack scenario** · what helps against it · confidence.

The attack scenario is the filter. Anyone who cannot write it down concretely does not have a finding, they have a bad feeling.

**The guiding line:** better to miss a theoretical problem than to flood the report with false alarms. Every finding has to be something an experienced person would raise in a review without hesitating.
