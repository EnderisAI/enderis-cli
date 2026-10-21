---
name: enderis-onboard
description: >-
  Start here to connect an agent repository to Enderis: run `enderis onboard`,
  read its JSON, choose a connection for each boundary, and hand off to the
  driver, playground or eval skill when the next step needs one. Use when asked
  to onboard, register, set up or verify an agent with Enderis, or to unblock a
  failed onboarding.
---

# Onboarding an agent repository with the enderis CLI

The CLI is the contract. Onboarding reads the repository and uploads one
immutable agent revision plus the APIs the agent calls (its boundaries). It
uploads metadata, never file contents.

## The loop

1. From the repository root: `enderis onboard . --json` (add
   `--context <ctx> --workspace <workspace-id>` if not configured). Interactive runs
   can drop `--json`.
2. If several packages are found, run again with the `--target` the CLI shows.
   Running from a package directory prefers that package.
3. Read the output: source, prompt pointers, boundaries, front-door status. Running
   onboard again refreshes them; unchanged metadata deduplicates.
4. Declare each boundary's gate variables (below), then run onboard again.
5. Choose a connection for each boundary (below), then run an eval:
   `enderis run . --list`, then `enderis run . --eval <name>`.

## Hand-offs

- **No front door the CLI can drive** (`no_agent_target`, `needs_ingress` or
  `needs_worker`): use the `enderis-agent-driver` skill. It puts a driver in
  `.enderis/driver/`, and `enderis onboard` then finds it without `--driver`.
- **The agent needs a playground** (the people, records and data its evals run
  against): use the `enderis-playground-author` skill.
- **Writing or fixing evals:** use the `enderis-eval-author` skill.

## Declare gate variables

An agent often builds a client only when some variables are set: a token, a
flag such as `ENABLE_SLACK=true`, a base URL, or a credentials file path. If a
run cannot set them, the agent never connects and the run reports
`Not reached: <boundary>`. For a boundary that is not mocked, `enderis run`
passes your real values only for the gates listed here or found in the code;
it skips any other name with a warning.

For each boundary in the JSON, open its `constructed_at` file and read the code
that decides whether the client is built. List every variable it checks. Compare
the list with the boundary's `gates`. If any is missing or has the wrong kind,
write `.enderis/boundaries.md` in the package:

```markdown
---
boundaries:
  slack:              # a boundary id from the onboard JSON
    SLACK_BOT_TOKEN: secret
    ENABLE_SLACK: flag
    SLACK_API_URL: url
    SLACK_CA_BUNDLE: file
---
```

Kinds: `secret` (a token or key), `flag` (any non-empty value turns it on),
`url` (an endpoint), `file` (a path the code opens). Run `enderis onboard . --json`
again and check that `gates` now lists them. Never edit the agent's code to
change how it connects.

## Choose a connection for each boundary

Open the agent's **Connections** section in Agent Details. Each boundary gets one
choice. A run stops before it starts while any boundary still needs one.

- **Mocked with an adapter:** an Enderis adapter serves the API, seeded from the
  eval's playground. Use this for evals you want to reproduce.
- **Not mocked:** the agent calls the real service. Enderis records the calls
  but seeds nothing. Use only when that service is safe to call from a test.
- **Routed to your own host:** runs reach an MCP URL you give, such as your
  staging system. The URL must carry no credential.

From the terminal, `enderis connections list` shows each boundary and its
candidate adapters, best match first. `enderis connections set <boundary>`
saves one choice: `--adapter <id or name>`, `--suggested`, `--passthrough` or
`--external <url>`. The Enderis MCP tools `list_connections` and
`set_connection` do the same.

Reference: https://enderis.ai/docs/agents/onboarding.

## `needs_substitution`

The front door works, but Enderis has no shipped adapter that can redirect the
agent's API client. Onboarding reports this with the source evidence. It is an
Enderis gap: report it, do not patch the agent to work around it.

## Which side is the blocker on?

- **Repository side:** a wrong package, launch command or prompt pointer comes
  from the source. Report it with the exact evidence; the owner fixes the
  source, then onboards again.
- **Enderis side:** missing adapters, unavailable evals, or control-plane
  failures. Fix these in Enderis, never in the customer repository.

## Configuration and receipts

Contexts, credentials and onboarding receipts are user-local. The repository
never selects an endpoint, workspace, context or credential. Use
`enderis context use`, CLI flags or environment variables to select a workspace.
`enderis inspect`, `onboard`, `import`, `pull`, `run` and `test` are listed with
every flag and exit code in the [CLI reference](https://enderis.ai/docs/cli/reference).

## Rules

- Never change the agent's code, config or scripts. The only files you may add
  are under `.enderis/` (Enderis-owned; the agent never loads it).
- Never add an Enderis import, variable or file to the agent's own code.
- Never probe a production source without explicit consent.
- Never commit or push unless asked.
