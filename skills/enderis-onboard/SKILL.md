---
name: enderis-onboard
description: >-
  Start here to connect an agent repository to Enderis and open a chat with
  the agent: sign in, run `enderis onboard`, give each boundary a connection
  (a built-in adapter, or one you build), build a small first playground, open
  the chat in the browser, then draft evals behind the chat. Use when asked to
  onboard, register, set up or verify an agent with Enderis, to chat with a
  repository agent, or to unblock a failed onboarding.
---

# Onboarding an agent repository with the enderis CLI

The goal is a chat: the person talks to their own agent in the browser as
soon as possible. Evals come after, behind the chat.

Onboarding reads the repository and uploads one immutable agent revision plus
the APIs the agent calls (its boundaries). It uploads metadata, never file
contents.

A JSON chat front door need not report tool activity. Enderis records gateway calls
that the response does not report without model-turn attribution.
Do not add activity reporting to customer code to make a run work.

Rules for the whole path:

- **Take the default.** Never stop to ask when this skill gives a default. Take
  it, and tell the person in one line which default you took.
- **Never change the agent.** Not its code, config, scripts or prompts. Write
  files only under `.enderis/` (Enderis-owned; the agent never loads it).
- **No production calls.** A run or chat must not reach the agent's real
  services. Every API the agent calls gets an adapter, or a live read where
  step 3 allows one.
- **The real agent, or nothing.** Never build a copy of the agent from its
  prompt. When the real agent cannot run, name the blocker ("Name the
  blocker" below) and stop. Never turn on the agent's own test, demo, offline
  or mock mode (for example `TESTING=true`) to get past a service: that runs
  other code than production. Give the service an adapter, or switch it off
  and name it. Never patch the agent's code at launch either (a wrapper that
  replaces its functions or rewrites its tool calls): a call the agent sends
  to its own built-in stub stays there, as in production. When Enderis does
  not route a call it should, name the blocker.
- **The CLI only.** Do not set up MCP and do not restart the session before the
  first chat. Every step below is an `enderis` command.
- **When a command fails** and the fix is not in this skill, run `enderis faq`
  and find the error there before you retry. Never run a failing command again
  unchanged.

## First run: from the prompt to a chat

Do the steps in order. Each says what to expect and what to do on an error.

### 1. Sign in

Run `enderis auth status`. If it says `Status: connected` to the workspace
the person named, go to step 2.

Otherwise sign in in the background, with the output in a log, so you can
read it while the command waits. If the request gives a sign-in command, run
exactly that command. Otherwise use the workspace the request names:

```sh
mkdir -p .enderis
enderis auth login --no-browser --workspace <org>/<workspace> > .enderis/login.log 2>&1 &
```

Within a few seconds the log has:

```text
Login code: ABCD-EFGH
Open https://app.enderis.ai/cli/auth/<id> and type the code there.
Waiting for browser approval…
```

Give the person the link and the code in one message: open the link, type the
code, choose the workspace if the page asks, approve. Login waits up to 10
minutes.

Do not end your turn to wait. Go on with the steps that do not need sign-in,
such as reading the code for steps 2 and 3. When only signed-in steps remain,
wait inside this turn: read `.enderis/login.log` every 10 seconds, for up to
10 minutes, until it has `Connected to <org>/<workspace>`.

| In the log | Action |
| --- | --- |
| `enderis: command not found` | The installer puts the CLI in `~/.local/bin`. Call it as `~/.local/bin/enderis`. |
| `expired` or `was denied` | Run the same command again and give the person the new link and code. |
| `Nothing was saved` (another workspace was approved) | Run the same command again and tell the person to choose the workspace the request names. |

Never guess an org or workspace name. If a command with a workspace name
fails, do not try that name again: run `enderis auth status` or
`enderis context list`.

### 2. Onboard

From the repository root:

```sh
enderis onboard . --json
```

Read `execution_status`, `name` (the agent's name), `boundaries` (each has an
`id`, a `protocol`, `constructed_at` and `gates`), `prompt_urls`,
`unresolved_clients`, `declaration_errors`, `cannot_mock`, `switched_off`,
`agent` and `next_actions`.

`agent` is there when onboarding recognizes the framework. It names the
`framework` it recognized, the `agent_object`, the `prompt` and the `tools`
(each a `path` and `line`), and how a driver can reach the agent: `reach`
(`server` when `launch` holds the framework's dev-server command, else
`harness`), `launch`, and `driver_template`: the `enderis-agent-driver`
skill's template folder to start from (`http`, `python-harness` or
`node-harness`).

Model key names come from source evidence. Native Node `fetch` calls to the literal OpenAI HTTPS Chat Completions or Responses endpoint can name `OPENAI_API_KEY` without an SDK. A Python `openai-agents` package using the default client can name its default `OPENAI_API_KEY` without an explicit environment read. Custom model/client/provider configuration suppresses that guess. Onboarding never reads the values; the local runner resolves the named keys from the environment or the package's `.env`.

| Result | Action |
| --- | --- |
| `execution_status: ready` | Go on below. |
| Several packages found | Run again with the `--target` the CLI shows. Default: the package that holds the agent's prompt. |
| `driver_written` in the JSON | Onboarding found an AI SDK chat route, a LangGraph server, Google ADK or Mastra, wrote a standard driver in `.enderis/driver/` and onboarded with it. Go on below with it unchanged. Edit it only when a run shows that the app's input differs (for example a graph whose input is not `messages`); `driver.md` says which graph or app it uses; the Mastra driver uses the first agent `GET /api/agents` lists. If the error names a written driver folder, delete that folder to onboard without it. |
| `needs_ingress` or `needs_worker` | The agent needs a driver. See "Driver agents" below. When the JSON has `agent`, write the driver to reach the agent the way `agent.reach` and `agent.launch` say. |
| Exit 2: `no agent target found (no_agent_target)` | If the folder holds an app that answers messages (a web server, a simulator, a queue worker), it needs a driver: see "Driver agents" below. If it holds no agent at all, take the default at once: build a demo agent with the `enderis-demo-builder` skill, and say so. |
| `needs_substitution`, or `cannot_mock` not empty | A boundary cannot be mocked; each `cannot_mock` entry gives the reason. Switch that service off ("Switch a service off" below) and onboard again. |
| Exit 2: no boundaries found | Read the code. Declare each REST API or MCP server it calls ("Declare a boundary onboarding missed", "REST boundaries"), and list each service Enderis cannot mock under `off:` ("Switch a service off"). Pass `--no-boundaries` only when it calls none. |
| The code passes a server map to a client (langchain `MultiServerMCPClient`, or a `servers` map) | Onboarding reads a map written inline (`MultiServerMCPClient({...})`): each key is a boundary. A map built elsewhere and passed as a variable or call is listed in `unresolved_clients`: declare one boundary per map key ("Declare a boundary onboarding missed"). |
| `unresolved_clients` or `declaration_errors` not empty | Fix them ("Declare a boundary onboarding missed"), then onboard again. |

Then check the code before step 3. Onboard again after any
change to `.enderis/boundaries.md` or `.enderis/launch.md`; unchanged metadata deduplicates.

For a normal HTTP-agent setting such as an account ID or base ID, write only
its environment name in `.enderis/launch.md` YAML frontmatter, for example
`settings: [AIRTABLE_BASE_ID]`. A file in the package takes precedence over
the repository root. Export its value for the runner, or use the package's
existing `.env`; never edit customer configuration. Onboarding uploads names
only. The local receipt pins them before a run reads values; missing values
stop launch and values are scrubbed from output. Do not declare a model key,
reserved interpreter/adapter/proxy variable, port variable or boundary gate as
a normal setting. Driver settings remain in `driver.md`.

1. **Gate variables.** For each boundary, open its `constructed_at` file (where
   the client is built or, for a known vendor SDK, its first import) and
   compare the variables the code checks before it builds the client with
   the boundary's `gates` ("Declare gate variables").
2. **REST, GraphQL and SDK clients.** Onboarding finds MCP clients and these
   vendor SDKs, and connects each SDK to the built-in interface for its
   service: npm `@linear/sdk`, npm and PyPI `stripe`, npm `airtable` and PyPI
   `pyairtable`. Each shows in `boundaries` as `<service>-api` (for example
   `linear-api`) with its `interface`. Do not write a mock or a declaration
   for one of them. Search the code for other clients of outside services:
   `fetch(`, `axios`, `got`, `httpx`, `requests`, `aiohttp`, GraphQL clients,
   and other vendor SDKs such as Octokit, jsforce or `openai`-style API
   clients (not the agent's own model client). Each one reaches production in
   a chat unless it gets an adapter. For each, build a REST adapter and
   declare the boundary as `transport: http` ("REST boundaries" below). For a
   service the person will use only as a live read (step 3, item 3), declare it
   without `interface:` and do not build an adapter.

#### Driver agents

A driver carries each message to an agent whose front door onboarding cannot
drive. Follow the `enderis-agent-driver` skill through its
`enderis onboard`, then come back here. Do not run evals from that skill.
When onboarding wrote a standard driver (`driver_written`), skip that skill:
run an eval with the driver first, and edit it only if the app's input
differs. Build output and local databases the app writes during runs
(`.next/`, `.mastra/`, a SQLite file) are fine, even when git ignores them:
each run starts the app in its own copy of the repository.

Onboarding with a driver finds boundaries, reads `.enderis/boundaries.md`
and finds the model keys the same way as without one: the keys the code
names or, when it names none, the default key of each model SDK it imports
or each provider-prefixed model string (`"openai/gpt-5"`). A run passes each
key that is set. It needs at least one key the code names (the others are
optional); when every key is a guess from imports, it needs at least one. An
AI SDK string model implies only `AI_GATEWAY_API_KEY`, not the provider's key.
Do checks 1 and 2 above for the app's code. Then:

- If the app calls any outside service (a boundary, or a service under
  `off:`), the driver must say `app: launched`: Enderis starts the app for
  each run with the run's mocks, and switched-off services stay off. An
  `app: attached` or `app: managed` driver with services to mock stops
  onboarding with an error that names the change. The `enderis-agent-driver`
  skill says how to write `launch`, `runtime`, the port and `ready`.
- **Docker apps.** If developers start the app with Docker Compose, the
  launched driver uses `launch: {compose: {files, service, port}}`. Each run
  gets its own compose project and removes it afterwards. Enderis refuses a
  compose project that would share or reach state outside the run (for
  example `container_name` or an external volume) and names the cause: then
  write a compose file for runs in `.enderis/` (the `enderis-agent-driver`
  skill, "A Docker Compose app"). Docker with Compose 2.24 or later must run
  on the machine that runs the evals.
- If the repository has no front door at all (no server, webhook or chat
  route: only an agent object that other code imports), the driver says
  `app: harness`: it imports the agent and calls it in its own process, with
  the same mocks and switched-off services. Pick a harness only when there is
  no front door; the run page shows it as a test entry point.
- If it uses only its own database and its model, `app: attached` also works.

Before you start an attached app:

- **Port.** Check that the app's port is free (`lsof -i :<port>`). If it is
  taken, pick a free port and set it through the override below.
- **Model key or other credential.** If the app needs a key the person
  already has in their environment (for example `OPENAI_API_KEY`), pass it to
  the app through an override outside the app's code: a compose override in
  `.enderis/` that reads the environment variable, or a key file in a
  temporary directory outside the repository when the app reads a key file
  or key directory. Never write a secret into the repository. If the app
  turns model calls off by default, turn them on in the same override.

Then start the app and open the first chat with the real agent through the
driver (step 5). If the real agent cannot answer (for example, no key in the
environment, or the app does not start), name the blocker.

### 3. A connection for each boundary

Every boundary needs a connection before any run, a chat included. List them
with every candidate adapter (the text output shows only five):

```sh
enderis connections list --json
```

For each boundary that still needs a choice:

1. **A clear built-in match** (the same product: a Gmail client and a
   `google_workspace-*` adapter, a Slack server and `slack-official`): take it.

   ```sh
   enderis connections set <boundary> --adapter <adapter name>
   ```

   Do not use `--suggested`: its ranking reads names only and often picks the
   wrong adapter.
2. **No clear match:** build an adapter with the `enderis-adapter-author`
   skill, then come back here.
3. **An information source with no state the eval needs** (web search, page
   fetch, a document or knowledge library), whose credential is in the person's
   environment: give it a live read. Reads reach the real service; writes
   Enderis recognizes (by method, declared reads or tool annotation) are
   refused. That is best effort, so tell the person to give the agent a
   read-only key or role for it.

   ```sh
   enderis connections set <boundary> --passthrough --read-only
   ```

   A REST boundary declared without `interface:` shows `no_mock` in
   `boundaries`. It can only be a live read (or own host): it cannot be
   mocked, and a run that leaves it mocked is refused with `needs_adapter`.

   Do this only when Enderis starts the app (behind its HTTP front door, or
   through a launched or harness driver; not an attached or managed app), and
   not for an MCP connection through
   `@langchain/mcp-adapters` or the AI SDK's `createMCPClient` in Node: the
   run refuses those. A REST read is
   `GET`, `HEAD` or `OPTIONS`, and an MCP read a tool marked `readOnlyHint`.
   When the code reads with another method (`POST /v1/search`) or an
   unannotated tool, list it under the boundary's `reads:` in
   `.enderis/boundaries.md`, and say so in the hand-off. Never declare
   `POST /graphql`: it lets mutations through too. A system of record (CRM, tickets, mail, payments, calendar) is
   mocked, by building an adapter if needed. Do not seed a live-read product in
   the playground: that makes the run `inconclusive`.
4. **Never choose `--passthrough` without `--read-only`.** A plain passthrough
   sends the agent's writes to production. Use it only when the person asks.
5. **Own host with writes** only when the person names the host and says
   writes are allowed there. Its origin must be in `.enderis/credential-hosts`,
   and it may not be the service's production host:

   ```sh
   enderis connections set <boundary> --external <url> --allow-writes
   ```

   The hand-off repeats both: the host, and that the person allowed writes to
   it. Runs of that agent then go one at a time.

Say in one line which state each service got. The person can change any of
them.

A REST boundary gets its adapter when onboarding picks its interface ("REST
boundaries" below); `enderis connections list` then shows it as mocked.

#### No adapter possible

An adapter cannot be built when neither the code nor a consented probe shows
the tool names and inputs, or when a client is one no Enderis origin adapter
covers (`needs_substitution`, `cannot_mock`). Then switch that service off
("Switch a service off" below) and go on with every other service mocked. One
service that cannot be mocked never stops the agent.

## Switch a service off

Each outside service ends in one state. Take the first that fits, and say in
one line which state you took for each service:

1. **A clear built-in adapter:** mock it (step 3).
2. **An information source with no state that matters to the eval** (web
   search, page fetch, a document library), whose key is in the person's
   environment: a live read, when the CLI offers read-only connections for its
   transport. Until then, mock it or switch it off.
3. **A system of record** (CRM, tickets, mail, payments, calendar): mock it,
   building the adapter when there is none (`enderis-adapter-author`).
4. **Otherwise:** switch it off.

To switch a service off, remove its declare block and list it under `off:` in
`.enderis/boundaries.md`:

```markdown
---
off:
  - name: salesforce
    hosts: [login.salesforce.com]
    gates: [SALESFORCE_TOKEN, SALESFORCE_INSTANCE_URL]
    why: jsforce runs on node-fetch 2, which no adapter covers yet
---
```

- `hosts`: the hosts its client calls. `gates`: the variables the code reads
  to turn the service on (read its `constructed_at` file). `why`: one line.
- In a run, the gates are absent from the app's environment, so the agent
  does not register the service's tools, and a request to its hosts is
  refused and listed as `blocked_egress`.
- A raw TCP socket (a client that ignores proxies and adapters) is not
  refused. The run lists it under `unobserved_connections` (address and port).
  Find the library that opens it and tell the person: Enderis cannot mock it.
- Every agent whose app Enderis starts runs with undeclared destinations
  denied. The app can reach its boundaries, loopback and the default host
  of each model key the run passes. Add any other host it needs under
  `allow:`, each with a
  `why` of `model`, `install` or `telemetry`, for example a model at a custom
  host:

  ```markdown
  allow:
    - host: my-resource.openai.azure.com
      why: model
  ```

  Onboarding warns when a model key has no default host (`AZURE_OPENAI_API_KEY`)
  and no `allow` entry of kind `model`. A run that refuses a host prints a
  `Blocked:` line for it; take the same fix. A cloud metadata probe
  (`169.254.169.254`) is refused but recorded without a warning: ignore it.

Onboard again. `switched_off` lists each service that is off.

### 4. A first playground

A playground is the people and records the agent works against. Build a small
one now; it gets deeper in step 6.

Read the guide `playground-authoring.md` in the `enderis-playground-author`
skill folder, installed at
`~/.agents/skills/enderis-playground-author/playground-authoring.md`. Follow
its blueprint format and its rules on labels and names. For this first
playground, skip its interview and audit steps and take these defaults:

- **Sources:** the agent's system prompt (open the file and line that
  `prompt_urls` points to, or search the code for it), the tools it calls, and
  the person's "About the agent" line when they gave one.
- **Services:** the service behind each connection from step 3. For a driver
  agent, the channel service its driver uses (for example `whatsapp`), with
  the people who write to the agent. Read the row schemas before you write a
  row:

  ```sh
  enderis tools schemas <service> [<service>...] --json
  ```

- **Size:** the agent's person, the person who chats (the user), two to four
  other people, and 5 to 15 records per service, enough for the agent's main
  job. Everything is simulated: say so in the blueprint's `description`.
- **Where:** `.enderis/playgrounds/<agent name>-first/blueprint.yaml`, with
  `name: <agent name>-first`.

Import it and fix every error until the import is clean:

```sh
enderis import .enderis/playgrounds/<agent name>-first
```

### 5. Start the chat and open it

For a driver agent whose `driver.md` says `app: attached`, start the app
first, the way `driver.md` says, with the port and key from "Driver agents".
Give each setting that `driver.md` lists (for example
`APP_URL=http://127.0.0.1:<port>`) in the environment of every `enderis chat`
and `enderis run` command: `APP_URL=… enderis chat …`. Never write it into the
repository's `.env`.

Start the chat in the background, exactly as below, before any eval. It waits
for messages the person types in the browser. Without `< /dev/null` and `&`,
the chat ends when your command ends, and the person finds a dead link:

```sh
enderis chat --playground <agent name>-first < /dev/null > .enderis/chat.log 2>&1 &
```

Wait for the line in `.enderis/chat.log` that starts with `chat: ` and holds
the link. Try once to open it: `open <link>` on macOS, `xdg-open <link>` on
Linux. If that fails or is refused, print the link once for the person and
go on. Do not try other browsers. Tell them they can type in the chat.

| In `.enderis/chat.log` | Action |
| --- | --- |
| `needs_adapter: <boundary>` | That boundary has no connection. Go back to step 3. When the hint says it has no mock, run the `enderis connections set … --read-only` command it gives. |
| `This package changed since … was onboarded` | Run `enderis onboard . --json` again, then start the chat again. |
| A required model key is missing | Check the environment for the variable. If it is set, pass it to the agent (for an attached app, through the override in "Driver agents") and start the chat again. If not, tell the person the variable name and wait until they set it. |
| `Not reached: <boundary>` | The agent did not connect to that boundary. That is fine when the messages did not need it. If they did, a gate variable is usually missing: see "Declare gate variables", onboard again, start the chat again. |
| No `chat: ` line, and the chat ended | Run `enderis update`, then start the chat again. |

### 6. Behind the chat: playground, evals, one live run

Do this while the person chats. Do not ask for a yes.

1. **Deepen the playground** per the guide: history, ordinary noise, and the
   records the evals below need. Import it again. Every version is kept, so
   the open chat keeps its copy.
2. **Draft three to five evals** with the `enderis-eval-author` skill, in
   `.enderis/evals/<eval name>/`, on that playground. Cover the agent's main
   job, one hard case from its prompt, and one case where it must refuse or
   ask. In each `eval.md`, list the adapter of every connection under
   `interfaces:` (`- {service: <service>, interface: <adapter name>}`), so the
   eval measures the tools the agent really sees. Without it, the eval
   measures `<service>-canonical`. A `scripted.json` is optional here: it
   never runs for a repository agent. If you write one, its tool calls use the
   names the adapter presents (for example `lookup_part`), not
   `<service>.<op>`.
3. **Import them.** Import checks each eval against its playground and
   services:

   ```sh
   enderis import .enderis/evals --agent <agent name> --acceptance --authored-by coding-agent
   ```

   Fix every error until the import is clean. A scripted replay cannot run
   against a repository agent (it makes its own model calls), so the live run
   below is the first real test.
4. **Run one eval once, live,** the one for the main job:

   ```sh
   enderis run . --eval <eval name>
   ```

   It prints the run link at the end. Open it the same way as the chat link.
   Run only this one; more live runs wait for the person. If it prints
   `waiting: … is in use by another command`, the open chat holds the app (a
   driver app that one run at a time may use). Leave the run waiting in the
   background, or run it after the chat ends, and tell the person which.
5. **Report** in a few lines: the chat link, the defaults you took, the
   adapters you built, the evals and the live run's verdict. If the run
   failed, say whether the eval or the agent is at fault (see the
   `enderis-eval-author` skill). If the eval was at fault, fix it, import it
   and run it once more. Do not weaken an eval to make it pass.

## Name the blocker

When the real agent cannot run at all (no front door a driver can use, the
app does not start, no model key), stop before the chat. A copy of the agent
made from its prompt is not the person's agent, so never build one. Tell the
person in a few lines:

- what blocks it: what stops the app, its file and line, and the reason
  (for example: the server at `cmd/server/main.go` is Go, and Enderis
  launches only Node and Python apps);
- which side the fix is on ("Which side is the blocker on?" below);
- what is done: sign-in, onboarding, the adapters you built.

Do not draft evals for an agent that cannot run.

## REST boundaries

A REST, GraphQL or SDK client gets its adapter in this order:

1. **Build the adapter** with the `enderis-adapter-author` skill: a service
   and a `protocol="http"` interface whose `upstream["endpoint"]` is the
   origin the client calls, with one tool per route the agent uses. Import it.
2. **Declare the boundary** in `.enderis/boundaries.md` with
   `transport: http`, the same origin as `url`, and the interface name
   ("Declare a REST API boundary" below). A live-read-only service skips
   step 1 and has no `interface:`.
3. **Onboard again.** Onboarding assigns that interface to the boundary.
   `execution_status` stays `ready` only when an Enderis origin adapter covers
   the client's library (Node `fetch`, undici and `node:http`/`node:https`
   clients such as axios, got and node-fetch; Python `httpx`, `requests`,
   urllib3, `urllib`/`http.client` and `aiohttp`). A gRPC or HTTP/2-only
   client is not covered: see "No adapter possible".

## Hand-offs

- **No front door the CLI can drive** (`no_agent_target`, `needs_ingress` or
  `needs_worker`): the `enderis-agent-driver` skill.
- **A boundary with no built-in adapter:** the `enderis-adapter-author` skill.
- **Playgrounds:** the `enderis-playground-author` skill.
- **Evals:** the `enderis-eval-author` skill.
- **No agent at all:** the `enderis-demo-builder` skill.

When you hand the agent to the person, name each switched-off service, why it
is off, and that the evals cannot see what the agent would do with it.

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
again and check that `gates` now lists them.

When the client loads a credential file before its first call (an OAuth token
file, a service-account JSON) and a mocked run must still reach the service,
write a fake one in the format the client reads under `.enderis/` (no real
secret; the mock accepts any credential) and point the agent's own setting at
it, for example through the driver's environment.

## Declare a boundary onboarding missed

Onboarding finds common MCP client patterns on its own: an inline server map,
and a client or transport that names one server with a literal URL or command
(the official `mcp` and `@modelcontextprotocol/sdk` transports and the
framework clients built on them). It does not follow config objects or helper
functions, so it can miss a client whose server comes from a config value. Do this when the JSON lists `unresolved_clients`, or when
the code clearly builds an MCP client that is not in `boundaries`:

1. Open each constructor (`new Client(`, `new StdioClientTransport(`,
   `MCPServerStdio(`, `MultiServerMCPClient(` and similar). For a langchain
   `MultiServerMCPClient`, declare one boundary per key of its server map,
   with the key as the boundary id: runs match its servers by key.
2. Trace the transport arguments to the real server: the package or executable
   a stdio transport launches, or the URL an HTTP transport opens. Follow config
   defaults and environment schemas until you reach a literal value.
3. Add a `declare` block to `.enderis/boundaries.md`, next to the boundary's
   gate variables:

   ```yaml
   boundaries:
     calendar:
       declare:
         transport: stdio                     # stdio | streamable_http | sse
         constructed_at: src/mcp.ts:114       # path:line in the package
         server: "@cocal/google-calendar-mcp" # stdio: the package it launches
       GOOGLE_OAUTH_CREDENTIALS: file
     slack:
       declare:
         transport: streamable_http
         constructed_at: src/mcp.ts:172
         url: https://mcp.slack.com/mcp       # HTTP: the URL it opens
       SLACK_MCP_ACCESS_TOKEN: secret
   ```

4. Run `enderis onboard . --json` again. The CLI checks each claim against the
   source: the constructor is on that line or the 5 after it and matches the
   transport (`constructed_at`), the server is a whole word of a string literal
   in the source, scope and version included, or the URL starts a string
   literal (`server_literal`, `url_literal`), and every gate variable is read
   somewhere (`gate_read`). A claim that fails is listed in
   `declaration_errors` with what the CLI found there; the others still count.
5. Fix each error and onboard again until `declaration_errors` is empty.

If an unresolved constructor only builds transports for boundaries onboarding
already reports (for example a shared helper fed by a server map it found),
it needs no declaration. Use `declare` only for an id that is not in
`boundaries`. Never edit the agent's code to make a declaration pass.

## Declare a REST API boundary (`transport: http`)

Onboarding finds MCP clients and the known vendor SDKs listed under "2.
Onboard". An agent that calls another REST API with its own
`fetch`, or with another vendor SDK built on it, has no boundary for that API,
and its calls reach production. A declaration for a known SDK's origin, or its
service under `off:`, replaces the boundary onboarding would add for it. Declare each origin you find in the code before
the first chat ("REST boundaries" above). A run also reports each call to an
undeclared origin as `unmodeled_egress`; declare that origin too:

```yaml
boundaries:
  whatsapp-cloud:
    declare:
      transport: http
      constructed_at: src/whatsapp.ts:12   # path:line where the client is built
      url: https://graph.facebook.com      # the origin: scheme, host, port only
      package: "@acme/whatsapp-sdk"        # only when a vendor SDK builds it
      interface: whatsapp-cloud-http       # only when the origin picks no interface
    WHATSAPP_TOKEN: secret
    WHATSAPP_BASE_URL: url                 # a config variable that holds the base URL
```

- You decide where the client is built; the CLI checks only that `url` is an
  origin with no credentials, path or query (`origin`), that the
  `constructed_at` file exists, and that each gate variable is read
  (`gate_read`).
- If the base URL comes from configuration, list that variable as a `url` gate.
- Onboarding picks the interface whose production origin equals `url`. When
  more than one has it, the error is `declaration_needed`: add `interface:`
  with a name from the message. When none has it and you name none, the
  boundary stays with `no_mock`: it runs only as a live read. To mock it,
  build an interface first ("REST boundaries" above).
- `execution_status` is `ready` only when Enderis ships an origin adapter for
  the package's language (today: Node `fetch`, undici and
  `node:http`/`node:https`; Python `httpx`, `requests`, urllib3,
  `urllib`/`http.client` and `aiohttp`); otherwise it is
  `needs_substitution` (see "No adapter possible").
- An Enderis API that does not accept HTTP boundaries yet stops onboarding
  with "does not accept transport: http boundaries yet". Remove those
  `declare` blocks to onboard without them.

## Connections in the web app

The agent's **Connections** section in Agent Details shows the same choices:
**Mocked with an adapter**, **Not mocked** (the real service), or **Routed to
your own host** (an MCP URL such as a staging system; the URL must carry no
credential). By default a routed run removes the credentials the agent
configured on its client. To keep them, the owner lists the origin
(`https://host[:port]`), one per line, in the repository's
`.enderis/credential-hosts`. Never add an origin the owner did not name. The
Enderis MCP tools `list_connections` and `set_connection` do the same as
`enderis connections`.

Reference: https://enderis.ai/docs/agents/onboarding.

## Which side is the blocker on?

- **Repository side:** a wrong package, launch command or prompt pointer comes
  from the source. Report it with the exact evidence; the owner fixes the
  source, then onboards again.
- **A missing adapter** is not a blocker: build one with the
  `enderis-adapter-author` skill.
- **Enderis side:** an API error you cannot fix from here, or a client no
  route adapter covers (`needs_substitution`). Report it with the command and
  its output ("Name the blocker").

## Configuration and receipts

Contexts, credentials and onboarding receipts are user-local. The repository
never selects an endpoint, workspace, context or credential. Use
`enderis context use`, CLI flags or environment variables to select a workspace.
`enderis inspect`, `onboard`, `import`, `pull`, `run`, `test` and `chat` are
listed with every flag and exit code in the
[CLI reference](https://enderis.ai/docs/cli/reference).

## Rules

- A person approves each login in their browser. Never approve it for them.
- Never change the agent's code, config or scripts. The only files you may add
  are under `.enderis/`.
- Never add an Enderis import, variable or file to the agent's own code.
- Never probe a production source without explicit consent.
- Never commit or push unless asked.
