---
name: enderis-onboard
description: >-
  Connect an agent repository to Enderis: read capabilities and onboarding
  diagnostics, declare boundaries, check the real agent, build a playground,
  open its chat, then run one live eval. Use when asked to onboard, register,
  set up or verify a repository agent, chat with it, or unblock onboarding.
---

# Onboard a repository agent

Get the person to a browser chat with their own agent, then run one live eval.
Use the CLI throughout; do not set up MCP or restart the session.

## Rules throughout

- Take the defaults below without asking. Tell the person which you took.
- Customer code is read-only. Write only under `.enderis/`; never change the
  agent's code, config, scripts or prompts, including through launch patches.
  Never write a launcher under `.enderis/` (`driver_launch_in_enderis`).
- Never copy one model key into another key name: not in a driver, a launch
  command or an override file (`driver_reads_model_key`). Never put a model key
  under `app_env:` or `settings:` (`model_key_copied`). When the agent reads
  its key under another name, such as `LLM_API_KEY`, declare it under
  `model_keys:` and have the person approve it with `enderis model-keys`.
- When a run reports the agent changed since its baseline, undo your own edit.
  Never delete the baseline file; only the person may.
- Find the agent's main job and how production reaches it. Use that front
  door over a test route, demo or sub-agent. Use a harness when no front door
  can be launched or driven, as `enderis-agent-driver` describes.
- Run the repository agent with production settings in the launch environment.
  Never use its demo, test, offline, mock or sample mode, a hosted copy, or a
  new agent made from its prompt. Let its real clients reach Enderis adapters.
- The app's own datastore is outside Enderis simulation: use its local database
  or its own local fallback store as it normally runs locally. That is not demo
  mode; the rule above forbids replacing its model, tools or outside services with fakes.
- A person approves each sign-in in the browser. Never approve it for them.
- After a failure, run `enderis faq` and read the matching entry before retrying.
  Change what caused the failure; never repeat a failing command unchanged.
- Never print secret values or write them into the repository. Never probe a
  production source without explicit consent. Never commit or push unless asked.

## 1. Read the evidence and sign in

From the repository, run:

```sh
enderis capabilities
enderis inspect . --json
enderis auth status
```

Read the prompt and production entry point; compare them with inspection's
targets, `agent`, boundaries and unresolved clients. Choose the package with
the main agent's prompt. A framework name alone does not prove support.

Keep the context if connected to the requested workspace. Otherwise run the
person's exact sign-in command, or use:

```sh
enderis auth login --workspace <org>/<workspace>
```

Run it in the foreground; it opens the sign-in page in the person's
browser, prints `Sign in at <link> with the code <code>` and exits at once.
Your next message always gives the person that line as it is, before
anything else, in case the page did not open: they cannot see your shell, and the code
expires in ten minutes. Never guess the org or workspace; omit
`--workspace` if none was named and let the person choose. Then start the
`--wait` command it printed, in the background:

```sh
mkdir -p .enderis
enderis auth login <the flags on that line> --wait > .enderis/login.log 2>&1 &
```

Continue reading code while it waits. Poll the log within the turn until
connected; if it says expired or denied, sign in again from the start and
give the new `Sign in at ...` line at once. Leave approval to the person.
If `enderis` is not on PATH, try `~/.local/bin/enderis`.
Contexts and credentials are user-local; repository files cannot select them.

Then run from the selected package:

```sh
enderis onboard . --json
```

Read `execution_status`, `boundaries`, `model_keys`, `prompt_urls`, `agent`,
`driver_written`, `unresolved_clients`, `declaration_errors`, `cannot_mock`,
`corrections`, `switched_off` and `next_actions`. Show selected model key names once.
Shell values win over the existing package `.env`; onboarding uploads names only.

## 2. Declare what the code actually does

Write YAML frontmatter in `.enderis/boundaries.md` in the package. Keep only
claims you checked in source. Full syntax: [onboarding reference](https://enderis.ai/docs/agents/onboarding).

- Choose an inspected package with `target: <id>`; `--target` overrides it.
  It cannot select an undiscovered package: use a driver in that package.
- Use `not_boundaries: [<id>]` only for an observed guess the code never calls.
  An inferred or unreached boundary alone is no reason to remove it.
- Read each client's construction and startup conditions. Declare missing gate
  variables under its boundary id as `secret`, `flag`, `url` or `file`.
- A base-URL `url` gate is needed only for a required read with no default.
  Keep the full SDK base path in the declared `url`; leave optional overrides unset.
- Search for outside REST, GraphQL, SDK and MCP clients inspection missed.
  Declare each real boundary; for a server map, the map key is the boundary id.
  Do not redeclare a correctly inferred SDK boundary.
- Use boundary `hosts` only for passthrough; for simulated HTTP boundaries,
  list the client's extra bootstrap and auth origins as a space-separated
  string in the interface's `upstream.auth_origins` and serve their routes there.
  Onboarding records them; onboard again after changing them, or runs refuse.
  A model provider's API is never simulated: its boundary stays live. These are
  Anthropic, OpenAI (also `*.api.openai.com`), Gemini, Vertex AI, Azure OpenAI
  and Azure AI (`*.openai.azure.com`, `*.cognitiveservices.azure.com`,
  `*.services.ai.azure.com`), Amazon Bedrock runtime, Mistral, Groq, xAI,
  DeepSeek, Cohere, Together AI, Fireworks AI, OpenRouter, the Vercel AI Gateway
  and the Cloudflare AI Gateway.
  After the first run, read `blocked_egress` warnings for missing hosts of declared boundaries.
  For a client that needs a bootstrap cookie, return it with `http_response(..., cookies=[...])` and give it the production `Domain` (such as `Domain=.example.com`), so the client sends it to the other origins too; list `Cookie` in `http_headers` to read it back as the `cookie` argument. Only the cookies a simulated interface set earlier in the run reach an interface that lists `Cookie`; any other cookie the agent holds is removed. A kept `Cookie` is recorded in the run like any other argument.
- A `declare:` block replaces a wrong inferred transport or target under the
  same id. For known MCP clients, cite the constructor as `constructed_at: path:line`
  and its literal `server` or `url`; follow declaration errors to correct it.
- For unknown URL clients, use `declare: {transport: streamable_http, url: <url>}`
  for MCP, or `transport: http` for REST, without `constructed_at`.
- For an app with `runtime: other`, declare every service this way. When the
  app reads the service's address from a variable, add it as a `url` gate (for
  example `CRM_URL: url`). Enderis reads no source in that language: each gate
  name must appear in some file of the repository (build output, vendored
  code, docs and files Git ignores do not count). In a run the `url` gate names
  the service's door, which forwards the app's requests to the simulation. A
  service whose declared `url` is HTTPS on port 443 is also answered at that
  host in the run (a fixed host), so it needs no `url` gate. A boundary with
  neither shows in `cannot_mock`, and a call to its host is refused. Report
  that to the person.
- Fallback URLs need HTTP(S), no credentials, query or fragment. An MCP fallback
  needs its own origin; stdio and SSE still need a known constructor/hook.
- REST declarations use `transport: http` and `url`; add `interface:` when the
  origin does not select one. Follow `no_mock` to build the missing interface.
  Never put a token in the url path (such as Telegram's `/bot<token>/`).
- `model_keys: [<NAME>]` restricts which set keys pass; absent passes all set
  built-in keys, and `[]` passes none. A declaration cannot approve an extra key.
- For an extra key, have the operator run `enderis model-keys <NAME> --host <HOST>`
  and approve its terminal prompt themselves for every declared model host.
- Keep undeclared egress denied. Extra model, install or telemetry hosts go under
  `allow:`, each with the matching `why: model`, `install` or `telemetry`.
- Use `off:` only when the app runs without the service and no adapter can be built
  (a confirmed registry gap, or an information source with no live read).
- Each `off:` entry names the boundary id, `hosts`, `gates` and `why`; remove its
  `declare:` block. Report the service and what the evals can no longer test.
- Declare synthetic shapes under `credential_files`; see [credential files](https://enderis.ai/docs/agents/onboarding#credential-files).
  Never create a real key fixture or change the customer's credential file.
- Normal HTTP-agent settings go in `.enderis/launch.md` as `settings: [<ENV_NAME>]`;
  driver settings go in `driver.md`. Export values or use the existing `.env`.
  Never list model keys, boundary gates, port or reserved variables as settings.
- If the HTTP app already reads the current time from a variable, add `clock: <NAME>`
  there (for example `clock: AGENT_NOW`). Each run sets it to the playground time,
  ISO 8601 with an offset, so "today" matches the eval. Never add one to the code.
- Standing checks for every run go in `.enderis/standards.py` (at most 256 KiB);
  an eval's `standards:` list picks which apply. Onboard again after a change.

Raw sockets and clients bypassing hooks and proxies may reach production; report this limit.
`unobserved_connections` reports only observations; `browser: true` marks an agent's own web browser, which Enderis neither simulates nor blocks, even under deny (allowed for reading only). Never claim containment or change customer code.

For `needs_ingress`, `needs_worker` or `no_agent_target` when an app exists, use
`enderis-agent-driver` to write, check and onboard `.enderis/driver/`; return
before running evals. When `enderis inspect` reports `compiled_app` (Rust, Go,
the JVM, .NET or another language that is not Node or Python), the status is
`ready` but no target is selected: do not run `enderis onboard` yet. The next
step is that skill's "An app in another language" (a driver with
`runtime: other` and `launch.compose`); onboard after the driver exists. Use `agent.reach` and `agent.launch` only for the real front door.
If no agent exists, use `enderis-demo-builder` and say which default you took.

Keep and test `driver_written` before editing if it reaches the main job;
replace it if it reaches a test route or sub-agent instead of the production front door.
Driver, signing, handler and Compose details belong to `enderis-agent-driver`.
That skill also covers throwaway request-auth keys the app checks; do not ask
the owner for production JWT verification keys, JWKS or bearer tokens.

Example frontmatter; replace names and source locations with facts from the app:

```yaml
---
boundaries:
  <id>: {NAME: secret}
  calendar:
    declare: {transport: stdio, constructed_at: src/mcp.py:40, server: "@cocal/google-calendar-mcp"}
  tools:
    declare: {transport: streamable_http, url: https://tools.example.com/mcp}
not_boundaries: [headers]
off:
  - {name: search, hosts: [search.example.com], gates: [SEARCH_TOKEN], why: No adapter or live read}
allow:
  - {host: models.example.com, why: model}
---
```
Run `enderis onboard . --json` again until `declaration_errors` is empty.

## 3. Connect boundaries and check onboarding again

```sh
enderis connections list --json
```

- A built-in adapter for the same product: assign it with
  `enderis connections set <boundary> --adapter <adapter name>`.
  Do not use `--suggested`; its name ranking is not evidence.
- No clear match for a service needing simulation: use `enderis-adapter-author`.
  Prefer an interface over a built-in service that models the API; otherwise build both.
  Every system of record gets a simulation, even with placeholder credentials.
- An information source whose state the eval does not need and whose key is
  available may use `enderis connections set <boundary> --passthrough --read-only`
  when supported. Tell the person it reaches the real service and needs a
  read-only key or role. Never seed that live-read product in the playground.
  Declare a REST live read without `interface:`; it needs no adapter.
- With no key, or when in doubt (including a keyless source), build an adapter
  with `enderis-adapter-author`; never stop to ask for live access.
- If reads use other methods or unannotated tools, declare `reads:` under that
  boundary and report it. Never declare `POST /graphql` as a read.
- Plain passthrough needs the person's explicit request. An external host with
  writes needs their named non-production host and permission for writes;
  use `enderis connections set <boundary> --external <url> --allow-writes`.
  Add only owner-approved origins to `.enderis/credential-hosts`; report the host
  and permission. Routed connections otherwise drop customer credentials.

After declaration or launch changes, onboard again. Read diagnostics by `code`;
follow their `next` or `next_actions` description before running the command.

- `confirm_boundary` is a guess: correct the declaration or build the adapter.
- `sdk_interface` can be checked live only when `execution_status` is `ready`.
- `no_boundaries` needs a source review; use `--no-boundaries` only if it calls none.

Do not attempt a chat while execution is blocked. If the real app cannot run,
report the blocker, command/output, file and line, which side must fix it, and
what is done. Do not draft evals for it. A missing adapter is work to do first.
Repository errors belong to the owner; a mismatched local runtime belongs to
this machine; an unsupported route or API defect belongs to Enderis.

## 4. Build a first playground and run the health check

Use `enderis-playground-author` and its `playground-authoring.md`. For this first
playground, skip the interview and audit; take these defaults:

- Sources: the real system prompt, its tools and the person's agent description.
- Services: every simulated connection's service, plus the driver's channel service.
  Seed the underlying built-in service when an interface uses one. Read schemas
  with `enderis tools schemas <service> --json` before writing rows.
- Size: the agent, the person chatting, two to four others, 5–15 records per service.
  Label the blueprint's description as simulated data.
- Path and name: `.enderis/playgrounds/<agent name>-first/blueprint.yaml`,
  with `name: <agent name>-first`.

```sh
enderis import .enderis/playgrounds/<agent name>-first
enderis chat --check --json --playground <agent name>-first
```

For a service front door, add the same `--channel` and `--as` to the check and
chat; seed the conversation and its participants. For example, a Slack DM uses
`--channel slack:dm:<agent person> --as <person>` and an IM with both Slack ids.

Read every check's `code`, `detail`, `next` and any `correction`. Fix failed
checks and repeat until `ok: true`. `ok: null` means unknown; follow its `next`.
Every code: [diagnostic codes](https://enderis.ai/docs/cli/reference#diagnostic-codes).
A `next` for the repository owner is theirs: tell the person, never do it yourself.
Do not drop a boundary because this greeting did not use it. After changes to
`.enderis/`, connections or the playground, onboard again when metadata changed, then repeat the check.
Read live run findings the same way. Fix drivers or declarations, never the agent.

## 5. Start the chat and give the link

For an attached app, check the port is free (`lsof -i :<port>`); if taken, set
another through an environment override. Start the app as `driver.md` says.
Pass driver settings to each chat and run: `APP_URL=… enderis chat …`, never in `.env`.
Start chat in the background before authoring evals:

```sh
enderis chat --playground <agent name>-first < /dev/null > .enderis/chat.log 2>&1 &
```

Wait for the `chat: ` link in the log. Open it once with the available browser and
give it to the person. If opening fails, print it and continue. Keep the chat process running.

## 6. Evals, one live run, report

While the person chats, deepen the playground with history, ordinary noise and
the records the evals need; import it again. The open chat keeps its own version.
Use `enderis-eval-author` to draft three to five evals under `.enderis/evals/`:
the main job, a hard prompt case, and a case that needs refusal or a question.
Use the real service channel for a service front door.
Under `interfaces:`, list each adapter as `- {service: <service>, interface: <adapter name>}`;
otherwise the eval uses `<service>-canonical`. A scripted fixture is optional here;
it cannot replay the repository agent's own model calls.

```sh
enderis import .enderis/evals --agent <agent name> --acceptance --authored-by coding-agent
enderis run . --eval <main job eval>
```

Fix import errors. Run only this one eval live; further runs wait for the person.
Open its run link. If `enderis run` prints `waiting: … is in use by another command`,
the open chat holds the app or folder: leave the run waiting in the background,
or run it after the chat ends, and say which. If the eval is at fault, fix it,
import it and run once more. Never weaken it to pass.

Report: chat link; defaults taken; connection choices and adapters built;
switched-off services, reasons and lost coverage; eval names; live run link and verdict.
For failure, name whether the eval, agent, machine or Enderis is at fault, with run evidence.
Name any remaining blocker and what is already complete.

Then keep listening: run `enderis feedback --wait`. In the web app the person
marks replies, checks and evals as good or wrong and sends the notes to you.
Act on each batch as the `enderis-eval-author` skill says ("Feedback from the
web app"), close each note, and wait again. Tell the person once that they can
do this.
