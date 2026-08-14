# The gws CLI — the advanced route to Google Workspace

**Who this is for.** The simple route to mail and calendar is a connector in Claude Cowork (`reference/mcp.md`) — sign in once, done, and that stays the recommendation. The `gws` CLI is the **advanced route** for people on Google Workspace who want more than the connector offers: it talks to the full Google API surface (append Sheets rows, upload Drive files, batch calendar queries), it works in scripts and scheduled routines without a Cowork session, and it keeps working when the connector needs a re-login. The price: a one-time setup in the Google Cloud Console. Reckon with 15 minutes.

**You do not need both.** If the connector covers your daily briefing, stop reading. Come back when a task genuinely needs the API surface (typically: writing to Sheets, uploading to Drive, or a routine that runs while no Cowork session is open).

## What it is

`gws` is Google's open-source Workspace CLI (npm package `@googleworkspace/cli`). One command per API call:

```
gws gmail users messages list --params '{"userId": "me", "maxResults": 10}'
gws calendar events list --params '{"calendarId": "primary"}'
gws sheets spreadsheets get --params '{"spreadsheetId": "..."}'
```

The draft-only promise holds on this route too: this package never calls a send method, drafts stay drafts, the calendar is read, never written.

## Setup

### Requirements

- **Node.js** (already there if the dashboard renders)
- A **Google account** on the Workspace in question
- For the automatic route: the **gcloud CLI** ([cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install))

### Route 1 — automatic (recommended)

`gws` can configure the Google Cloud side itself; it needs gcloud once for that:

```
npm install -g @googleworkspace/cli
gcloud auth login
gws auth setup --login
```

`gws auth setup` creates (or reuses) a Google Cloud project, configures the OAuth client, and `--login` opens the browser straight after so you sign in and pick the services (a scope picker appears — Gmail, Calendar, Drive, Sheets is the sensible set for this package). Then check:

```
gws auth status
gws calendar events list --params '{"calendarId": "primary", "maxResults": 3}'
```

If the events of your next days come back, the route stands.

### Route 2 — by hand (when gcloud is not an option)

In the [Google Cloud Console](https://console.cloud.google.com):

1. Create a project (or pick an existing one)
2. **APIs & Services → Enable APIs**: enable Gmail API, Google Calendar API, Google Drive API, Google Sheets API
3. **OAuth consent screen**: type *Internal* on a Workspace domain (no verification hassle); otherwise *External* and add yourself as a test user
4. **Credentials → Create credentials → OAuth client ID**, type **Desktop app**, download the client file
5. Then sign in: `gws auth login` (limit the scopes with `-s gmail,calendar,drive,sheets` if you want)

### Good to know

- **Least privilege exists:** `gws auth login --readonly` requests read-only scopes. Enough for the briefing; creating mail drafts needs the normal login.
- **"Unverified app" warning** on an External consent screen is expected for your own OAuth client — you are the developer and the only user. Internal (Workspace) screens do not show it.
- **Where credentials live:** locally, managed by `gws` (`gws auth status` shows the state, `gws auth logout` clears it). They never belong in the repo or in `context/`.
- **IT policy:** on a managed Workspace, creating OAuth clients may be restricted. If step 4 is greyed out, that is IT policy, not an error — use the connector route and mention it to your admin if the need is real.

## Telling the workspace about it

After the setup, two entries so the system actually uses it:

1. `context/config.yaml → inventory.clis`: `- {name: "gws", purpose: "Google Workspace: Gmail, Calendar, Drive, Sheets", status: true}` — the dashboard's setup overview then shows it, and marks the Google connectors as covered by it.
2. Say it in the chat once ("gws is set up") — the routing then prefers it for Google tasks that the connector cannot do.
