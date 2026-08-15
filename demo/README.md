# demo/

A populated state, so a fresh clone shows you something instead of five empty
tabs. The dashboard falls back to these files while `context/` has no real ones,
and says so in a banner at the top so nothing here is ever mistaken for yours.

**The setup deletes this folder** as its last step. From then on the dashboard
reads your files only, and there is no fallback left to be confused by.

You can also drop it yourself at any time:

```bash
rm -rf demo/
```

## Where the numbers come from

The job titles, client countries, ratings, hire counts and budget shapes are
taken from a real Upwork search, so the pipeline looks like an actual day rather
than like a mock-up: the same spread of scores, the same mix of fixed and hourly,
the same pattern of clients with 600 hires next to clients with four.

**The descriptions are written, not copied.** A real posting belongs to the
business that wrote it, and republishing one indefinitely in a public repo is not
something a demo needs. What is real here is the shape; what is invented is any
detail that would identify somebody.

Client names are likewise invented. Upwork's search does not return them anyway,
which is why the Client column shows a rating and a hire ratio rather than a
company.
