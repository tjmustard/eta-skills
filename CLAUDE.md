@AGENTS.md

## Claude Code specifics

- Run `make validate` before committing; it also runs `claude plugin validate .` when the CLI is available.
- Test locally with `claude plugin marketplace add ./` then `claude plugin install <bundle>@eta-skills`.
- Local-path marketplaces load files in place; edits show after `/reload-plugins`.
