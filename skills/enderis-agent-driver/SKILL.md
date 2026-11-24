---
name: enderis-agent-driver
description: >-
  Write an Enderis agent driver for an agent whose front door `enderis onboard`
  cannot drive: triage the agent, write driver.md and any needed code from the
  template into .enderis/driver/, check it, onboard, run one eval and read the
  run.
  Use when onboarding reports needs_ingress, needs_worker or no_agent_target,
  or when asked to connect an unusual agent (webhook, events or simulator API,
  queue, own clock or outbox) to Enderis.
---

# Writing an agent driver

A driver carries each Enderis wake to the agent the way its real channel does
and returns what the agent answered. It lives in
`.enderis/driver/` in the agent repository: `driver.md` (the manifest) and any
code it names. Slack Events API apps need only the manifest; Enderis builds,
signs and posts their events. `.enderis/` belongs to Enderis and the agent never
loads it, so adding it does not change the agent. Reference:
https://enderis.ai/docs/agents/drivers.

The rule that decides everything: **never change the agent.** Not its code,
config, scripts or prompts. You may start it with your own compose file or
environment overrides. If the agent cannot be reached without a change, stop
and report the gap.

**When onboarding already wrote a standard driver** (`driver_written` in its
JSON, for an AI SDK chat route in Next.js, a LangGraph server, Google ADK or
Mastra), do not write another. Run one eval with it first (section 3). Edit
`.enderis/driver/driver.py` only if the run shows that the app's input
differs, for example a graph whose input is not `messages`, a route that
reads other fields, or a different graph or Mastra agent than the one the
driver uses (`GRAPH` or `AGENT` in driver.py). Then run
`enderis driver check` and `enderis onboard` again. Build output and local
databases the app writes during runs (`.next/`, `.mastra/`, a SQLite file)
are fine, even when git ignores them: overlapping runs use copies of the
repository; without a copy, runs use the folder itself, one at a time. Do not
add symlinks, copies or launchers to move them.

A driver is for a front door onboarding cannot drive. If the front door works
but onboarding missed some of the agent's MCP clients, do not write a driver:
declare those boundaries as the `enderis-onboard` skill describes in
"2. Declare what the code actually does".

## 1. Triage

Answer these before writing code. Write the answers into the body of
`driver.md`.

1. **Why inspection missed it.** Read `enderis inspect <path> --json`. Note the
   blocker (`no_agent_target`, `needs_ingress`, `needs_worker`) and the reason.
2. **Front door.** Is there an entry point real users reach (a webhook, a chat
   API)? Or only a test harness (a simulator, an events API)? Prefer the real
   one. Set `front_door: production` or `harness` honestly; the run page shows it.
   A framework's dev route to one agent (such as Mastra's
   `/api/agents/{agent}/generate`) is not the front door when production input
   arrives as a webhook that starts a workflow: drive the webhook, signed the
   way the app checks it. A step that waits for a person, such as an approval,
   is part of the job: send that person's answer the way the app's approval
   route takes it. Any secret the app checks (a webhook or approval secret,
   JWT verification key or JWKS, or API bearer token) is made by the driver for
   the run and set in the app's environment, not supplied by the owner.
   For JWTs, make a throwaway key pair, set the verification key and sign the
   driver's requests with the private key.
3. **Start.** How does the app start without edits? Find the existing script
   or command and the environment it reads. Use `app: launched` when you can:
   Enderis starts the app for each run with the run's simulated services and
   switched-off services (section 2, "A launched app"). It is required when
   the app calls any outside service, because only an app Enderis starts gets
   the simulated services. Use `app: attached` (you start the app before the run) or
   `app: managed` (the driver's `start` and `stop` hooks start one copy per run
   slot) only for an app that calls no outside service, or one Enderis cannot
   launch yet (an app that is not Node or Python). If the
   repository has no front door Enderis can launch or drive, use `app: harness`
   (section "A harness"), including when the only entry point is a terminal CLI,
   console script or serverless platform other than Vercel/Lambda.
   Use `launch.handler` below for Vercel or Lambda. Next.js keeps its own server
   command. Never write a server or handler launcher under `.enderis/`.
4. **Time.** Does the app answer at once, or on a timer, a batch or a
   scheduler? If it has its own clock, find how to make it run now (a tick
   endpoint, a debug flag, a short interval set by environment).
5. **Isolation.** For `app: launched` or a harness, keep `isolation: exclusive`;
   it changes nothing: each run starts its own app, in its own copy of the
   repository folder when Enderis can make one, so runs overlap and an open
   `enderis chat` never makes an `enderis run` wait. When the copy fails, the
   run uses the folder itself, one run at a time. An app that ignores the port Enderis gives it goes one
   run at a time on its own. For `app: attached`, the default
   `isolation: exclusive` means one run at a time uses the app. Use
   `isolation: namespace` only when each run gets its own
   namespace in the shared app (chat ids, user ids, tenant) derived from the
   run id, the driver reads only that namespace's output, and the app keeps no
   other state one run can change for another. To run evals in parallel
   against an app that keeps state, use `app: managed`. A driver written before
   `exclusive` existed has `namespace`; check it against this rule. With
   `namespace`, a command that runs more than one run at once warns that the
   runs use the same app.
6. **Outcomes.** Besides messages, what can the agent do that an eval must see?
   A hand-off to a human is an escalation, which the driver reports. An eval
   sees only channel messages (replies and the simulated people's messages),
   channel records and escalations, and, for a launched app or a harness, the
   records its simulated boundaries change and its MCP calls (the driver does not
   report them). An attached or managed app's own API calls are
   not simulated and not seen, so an eval cannot grade them.
7. **Knowledge.** Where does the agent's knowledge and data live (files,
   database, an API)? The app keeps using it during runs. It decides which evals
   make sense: ones whose answer shows in what the agent says.

## 2. Write the driver

For a Slack Events API app, copy `template/slack-events/driver.md` only and use
the events declaration below. For other HTTP front doors, copy `template/http/` (`driver.md` and `driver.py`) to `.enderis/driver/` at
the agent repository root (or in the agent's package, for a monorepo). It is
the template onboarding names as `driver_template: http`, for an agent with an
HTTP front door, such as a framework's own dev server (`reach: server`, with
the command in `launch`). For a harness, copy a harness template instead
(section "A harness"). Use another
directory only if the owner asks; then pass `--driver <dir>` to
`enderis onboard`. Then:

- `driver.md`: set `name`, `description` (for people), `command` (it runs in
  the driver directory), the `settings` it reads (environment variable names
  file the driver needs). Set `app: launched` (section "A launched app") or
  `app: attached` as triage item 3 says, and keep `isolation: exclusive`;
  change to `namespace` only when triage item 5 allows it.
- Optional `timeout:` is seconds per wake answer: default 300, allowed 1..=3600; use 600 for a ten-minute agent, then onboard again. It sets `ctx.request_timeout` and the driver, HTTP and settle budgets.
- For `app: managed`, add `start` and `stop` (lists that run in the driver
  directory; list their scripts in `files`). `start` exits 0 only when the copy
  is ready; `stop` removes the copy and succeeds when there is nothing to stop.
  Both hooks and the driver get `ENDERIS_SLOT`, `ENDERIS_APP_PORT` (the copy's
  port), `ENDERIS_INSTANCE` (use it for the compose project name and state
  files) and `ENDERIS_REPO` (the full path of the folder you onboarded), plus `HOME`, `USER`,
  the `DOCKER_*` variables and the CA paths (`SSL_CERT_FILE`, `SSL_CERT_DIR`,
  `REQUESTS_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS`, `CURL_CA_BUNDLE`). `stop` must reach what its
  `start` made even if the environment changed in between (for example the default Docker context):
  record what it needs at `start`, keyed by `ENDERIS_INSTANCE`, and exit
  non-zero when it cannot reach it.
- `driver.py`: change the requests marked TODO. Keep these parts as they are:
  - every chat id or user id comes from `ctx.run_id`;
  - when `wake["waiting"]` is above zero, the driver may hold back the app's
    output (its clock stays paused) and return it on a later wake; when it is
    zero, it must drain everything before it answers;
  - replies name the delivery they answer (`reply(delivery["id"], text)`); each
    reply must contain non-whitespace text and may be up to 200,000 characters,
    and one answer's replies together at most 6 MiB as JSON.
    Stored messages and evaluator evidence keep it whole; a destination service
    may have its own smaller limit;
  - escalations name the channel (`escalate(wake["channel"], reason)`);
  - the app's outbox is acknowledged, by message id, only for wakes up to
    `ctx.accepted_through`;
  - an unreachable or failing app raises `AgentError`; an app that does not
    answer in time raises `AgentTimeout`. Any other exception is reported as
    a driver bug.

The CLI provides `enderis.driver` to the driver when it starts it. You do not
install anything. `print` and the output of programs the driver starts go to
stderr; use `ctx.log` for the stop log.

### A launched app

Set `app: launched` and these fields in `driver.md`; remove `start` and
`stop`:

```markdown
app: launched
isolation: exclusive
runtime: node                      # or python: the app's language
launch:
  process: [npm, run, dev]         # the command a developer runs, no shell
port_env: PORT                     # or a "{port}" argument in launch instead
ready: /api/health                 # GET path that answers 2xx when ready
app_env: [NEXT_PUBLIC_SITE_NAME]   # non-secret settings the app needs
```

- `launch`: the start command from the README, `package.json` scripts or the
  Procfile, as a list. It runs in the folder you onboard. It must start a Node
  or Python process that serves the front door. For an app that runs with
  Docker Compose, see "A Docker Compose app" below.
- If the nearest `package.json` sets `engines.node`, Enderis checks the app's
  Node before it starts the app: the `node` first on `PATH` when `launch`
  starts with `node`, `npm`, `npx`, `pnpm` or `yarn`, or the binary when it
  starts with an absolute path to `node`, run with the app's empty `HOME`. A
  package script that starts bun or deno is not checked. On a mismatch the run
  stops. Put a
  matching Node first on `PATH`, or start `launch` with the absolute path of a
  matching `node`; do not edit the range.
- Port: find where the app reads its port. If it reads a variable, set
  `port_env` to it. If the port is a command-line flag, put `"{port}"` (quoted)
  in that argument, for example `[uvicorn, app:app, --port, "{port}"]`. Never
  both. If the app opens another port, Enderis finds it.
- `ready`: a path that answers a plain GET with 2xx once the app takes
  messages (a health route, or `/` when the app serves a page there). Not a
  path behind a sign-in. Enderis does not follow redirects.
- `app_env`: only settings the app needs that are not secret. Never list a
  model key, a boundary gate or a secret: model keys reach the app from
  onboarding, and gate variables are set by Enderis. Simulated secret gates get
  deterministic placeholders shaped for the service's credentials.
- The driver reads the app's address from `ENDERIS_APP_URL`. Do not list it
  in `settings`, and never list a model key or the gate variable of a simulated
  or switched-off service there: onboarding refuses it.
- Start the driver with plain `python3` or `node` in `command`. A driver that
  skips `PYTHONPATH` (`python3 -I` or `-S`) cannot load the network guard, and
  the run stops before the first message. The driver runs from the run's copy
  of the repository when there is one, otherwise from the original folder.
- The app and the driver get an empty `HOME` of the run's own, not yours, so
  nothing in your home folder (a CLI login, its plugins or settings) reaches
  the run. `app_env` cannot name `HOME`.

Enderis starts the app with undeclared destinations denied. If the app needs
a host other than its boundaries and its model provider's default host, add
it under `allow:` in `.enderis/boundaries.md` (the `enderis-onboard` skill).

What `launch` may start:

- If the repository runs its own server (an entry point that listens, such as
  `app_oauth.py`), launch that entry point unchanged. Never write a server or
  wrapper around its app object.
- For an exported serverless handler, declare `launch.handler` below. Enderis
  supplies the server in the run's temporary directory. A custom driver only
  maps requests or performs supported setup through the app's own routes.
- For a Slack OAuth app, a custom driver's `start` uses the app's own install
  and callback routes (for example `/slack/install`, then
  `/slack/oauth_redirect`), preserving the app's OAuth state and cookies. The
  exchange goes to the served `oauth.v2.access`; the run principal must be a bot.

### An exported handler

For TS/JS Vercel functions, keep `command`, `front_door: production`,
`app: launched` and `runtime: node`, and replace the process launch with:

```yaml
launch:
  handler: {format: vercel}
```

Remove `port_env` and `ready`: Enderis owns both. It serves static `api/`
routes (`api/foo.ts` and `api/foo/index.ts` both map to `/api/foo`) and detects
Web method exports, default `{fetch}`, and Node `(req, res)` default exports.
Files and folders starting with `_` or `.` are private and are not routed.
Dynamic `[segment]` routes and Python Vercel files are reported as gaps.

For Lambda, use `runtime: node` or `python` and
`launch: {handler: {format: lambda, module: src/app.py, export: handler}}`.
The module is a file inside the onboarded package, outside `.enderis/`;
`export` defaults to `handler`. Input is API Gateway v2 / function URL format.
Only results with `statusCode` are structured responses; strings are sent as-is
and other objects are JSON with status 200. Python also loads imports from the
module directory (SAM CodeUri layouts); a missing or non-callable export is a gap.
TS uses the repository's `tsx` root entry (ESM and CJS hooks) when installed,
else Node type stripping with `module.registerHooks`, plus
extensionless import and tsconfig-path resolution. Explicit `.cjs`/`.cts`
handlers also resolve extensionless `require` calls; unsupported cases stop
with a gap. Enderis installs nothing. JSONC/extended tsconfig files need the
repository's `typescript` or `tsx` package.

Enderis waits for the response and registered background work, including nested
`waitUntil` registrations, before accepting a wake. Rejection in an Enderis
launcher is an agent failure; exceeding the wake budget is an agent timeout.
Next.js keeps its own server and uses the same completion hooks; rejected
`after()` tasks keep Next's error logging and are graded through their effects.
Tracking starts only when `waitUntil` registers work; an unrelated open request
does not hold the wake open. Late `waitUntil` calls log and are ignored.
The Node request context supplies incoming headers for framework tracing;
`waitUntil` accepts promises and callbacks returning promises.
No driver-written completion endpoint is needed. Handler and events revisions
need a v3 runner; current CLI runners advertise v3. Update an older runner
that reports `needs_driver_runner`.

### A chat service front door

For a bot on a chat service (Slack, Microsoft Teams, Discord), the service
sends the bot an event, the bot answers 200 at once, and it posts its answer
later through the service's API.

- The person's message is already in the service: Enderis posted it as that
  person, because the eval (or the chat) starts on the service's channel.
- For Slack Events API input, declare `events` below; Enderis builds, signs
  and posts the event. Other chat platforms need a custom driver to map the
  wake's delivery (`entity`, `thread`, `sender`, `data`) to their event.
- Never post through the agent's route, and never read the service through it
  to look for the answer: each call shows on the run page as the agent's own
  action.
- Return no `replies` (the bot's own post is the reply). When the driver
  cannot see when the bot's work ends, return
  `WakeResult(settle_timeout_s=60)` (at least 5, never with `replies`):
  Enderis waits until the agent's calls delivered a message with text to every
  sender of the wake (a streamed post counts once it is filled) and then
  stopped for 3 seconds. The wait ends by `ctx.request_timeout` after
  the wake was sent. When it runs out, the wake is accepted as it is and the
  eval grades it: staying silent can be right. A driver that already waits for
  registered background work through Enderis's completion hooks needs no settle.

### A Slack Events API app

A Slack bot's front door is its Events API route (often `/api/events`). Declare
it in `driver.md`; omit `command` and driver code:

```yaml
front_door: production
app: launched
isolation: exclusive
runtime: node
launch: {handler: {format: vercel}}
events:
  platform: slack_events_v1
  path: /api/events
  signing_secret_env: SLACK_SIGNING_SECRET
```

Use the app's own process command for Next.js or a server, or `launch.handler`
for Vercel or Lambda. Declare `SLACK_SIGNING_SECRET: secret` on exactly one
simulated boundary in `.enderis/boundaries.md`. Do not put it in `settings` or
`app_env`: Enderis gives the app and its poster the same deterministic, credential-shaped placeholder.
The poster sends only to the declared loopback path and starts no driver process.

Every listened channel must use `wake: full`: `slack:mention:<bot>`,
`slack:dm:<person>` or `slack:assistant:<person>`. A DM from any other cast
member reaches the bot as a full `message` event without a `listens` entry.
Seed one Slack team and one
bot user whose id is the eval principal's single Slack handle. Missing or
ambiguous identities are setup gaps, refused before a run starts. After route
assignment, Enderis also refuses a signing secret with no single simulated owner.
Do not put team, bot or app ids in driver settings.

Enderis renders `app_mention`, `message` with `channel_type: im`, or
`assistant_thread_started` from the recipient's record. It keeps message and
thread timestamps and derives `event_id` from the delivery id. The app id is
stable and matches `auth.test.api_app_id`.
Assistant thread `context` is empty: a run has no channel the user was viewing.
The unsigned body is part of the scrubbed wake. Enderis serializes it once and
signs those exact bytes with the gate placeholder and a fresh wall-clock Slack
timestamp. Signing headers never enter spans or evidence.

The app answers through its own simulated Slack API calls. Enderis adds no
synthetic replies. Handler launches wait for registered background work;
server launches settle for up to `timeout:` (default 300 s). Next tracks only
completion; its own output keeps rejected `after()` errors. Rejected tasks in
Enderis-owned Vercel and Lambda launchers are agent failures.

No `url_verification` challenge is sent: runs deliver events directly, and Bolt's
request verifier needs no challenge to start. The built-in poster has no custom
`start` hook. For apps that need install setup, use the custom driver's `start`
flow above through the app's own routes and the served `oauth.v2.access`.
Do not fake install state or edit the app.

#### Known gaps

Bolt Python lazy listeners on a Lambda handler launch use boto3 to call
`lambda.invoke`. That targets real AWS and Enderis refuses it, so those lazy
listeners do not run.

### A Docker Compose app

When developers start the app with Docker Compose, launch the compose project:

```markdown
app: launched
isolation: exclusive
runtime: node                      # the language of the front door service
launch:
  compose: {files: [compose.yaml], service: web, port: 3000}
ready: /healthz
```

- `files`: the compose files a developer passes with `-f`, relative to the
  folder you onboard. `service`: the service that serves the front door.
  `port`: its port inside the container (the right side of its `ports:`
  entry). A compose launch takes no `port_env`.
- Each run is its own compose project, `enderis-<run id>`, in its own copy of
  the repository. If runs cannot get a copy, Enderis does not start the run.
  Enderis starts the services with no profile plus the front door's profiles.
  It publishes only the front door's port, on a free loopback port, and
  removes every other published port. No service restarts. Database and cache
  services start empty for the run. After the run, Enderis removes the
  containers, networks, volumes and the images the run built. If the command
  is killed, the next `enderis run` of the agent removes them.
- The front door service and every service built from the repository get the
  network guard, the simulated services and the model keys. Their containers must run Node
  18.19 or later, or Python. If the guard does not load in one of them (for
  example, an entrypoint that clears the environment, such as `env -i`), the
  run stops before the first message.
- Every other service (a prebuilt image) gets no guard, no model key, and
  every simulated or switched-off gate empty. Under the deny policy it joins only
  a network with no route out, and the run prints its name. A prebuilt service
  that shares another network (`network_mode`) is refused under deny.
- A switched-off service's gate is absent in the guarded services, even when
  the compose file, an `env_file` or the image sets it. A shell entrypoint that
  runs before Node or Python sees it as empty.
- Secrets reach the guarded containers only through `${NAME}` references in
  the override Enderis writes. Enderis never writes them to a file.
- Enderis refuses, and names, what would share or reach state outside the
  run: `container_name`; a volume or network with a fixed `name` or
  `external: true`; a bind mount, build context, extra build context,
  Dockerfile, `env_file` or secret file outside the repository; a remote build
  context; a volume driver with a host path; `network_mode: host` or
  `container:…`; `volumes_from: container:…`; `pid`, `ipc` or `userns_mode:
  host`; `privileged`; `devices`; `cap_add`; `build.ssh`; `build.network:
  host`. Do not edit the customer's compose files. Write a compose file for
  runs in `.enderis/` without these and list it in `files`. Paths in a compose
  file are relative to the folder of the first file.
- The machine that runs the evals needs Docker with Compose 2.24 or later.
  macOS and Windows use Docker Desktop on that machine. Linux needs a local
  Docker Engine; Docker Desktop for Linux and remote engines are unsupported.
  Enderis connects containers back to this machine. Do not change the agent
  or driver to allow `host.docker.internal`.
  Under deny, a container reaches host loopback only at this run's own listeners
  or an explicitly allowed destination.

### A harness

When no front door can be launched or driven, the harness calls the same function
or agent object the front door calls, with the same prompt, tools, model and
settings; name the front door it stands in for in `driver.md` and the report.
Copy `template/python-harness/` or `template/node-harness/` (the names
onboarding prints as `driver_template`) to `.enderis/driver/`, then fill in
`load_agent` and `ask`. Read [harness-frameworks.md](harness-frameworks.md)
for the framework calls.

```markdown
front_door: harness
app: harness
isolation: exclusive
runtime: python                    # or node
command: [python3, driver.py]      # node: [node, driver.mjs]
app_env: [SITE_NAME]               # non-secret settings the agent needs
```

- Enderis starts the driver in the folder you onboard, with the run's simulated
  services, switched-off services, model keys and `app_env` already in place,
  before the driver imports anything. One process serves one run, so the same
  agent object answers every wake; keep the conversation in `ctx.state`.
- The command must start `python` or `node` with the agent's dependencies:
  for example `[uv, run, python, driver.py]`. Nothing is installed at run time.
- The helper (`enderis.driver`, or `@enderis/driver` in Node) must be the
  driver's first import. It moves the protocol off stdout and stdin, so what
  the agent, a native library or a child process prints goes to the log.
- Load the agent in `start`, not at import, so `enderis driver check` works.
- The harness gets an empty `HOME` of the run's own, as a launched app does.
- `settings`, `app_env` and model keys share the one process: a name in two of
  them is refused. Never list a model key or a boundary gate.
- Claude Agent SDK: its `claude` CLI is a native program the in-process guard
  does not reach. Its model traffic goes through the run's proxy
  (`HTTPS_PROXY`), which allows only the model host and declared hosts. MCP
  servers given in `mcp_servers` are not simulated yet: switch them off under
  `off:` or keep the agent's tools in-process (SDK MCP tools, which the guard
  covers).

## 3. Check, onboard, run

- `driver_launch_in_enderis`: start the repository's own server or use
  `launch.handler`. This check does not inspect `launch.compose` overrides.
- `driver_listening_socket`: make the driver call the app instead of opening a
  server; the app and a harness driver may listen.
- `driver_imports_app`: call the app's front door from launched or attached
  drivers; harness drivers may import it.
- `driver_reads_model_key`: do not read, set or copy a model key (a built-in
  one or one listed under `model_keys:`) where the app's process would get it:
  a harness driver's code or `command`, a launched app's `launch.process`, a
  `.env` in the driver folder, or a compose override under `.enderis/`.
  Enderis gives model keys to the app only under their own names. When the
  app reads its key under another name, such as `LLM_API_KEY`, list that name
  under `model_keys:` in `.enderis/boundaries.md`, have the runner operator
  approve it with `enderis model-keys <NAME> --host <HOST>`, and onboard again.
- `model_key_copied`: a run stops when an `app_env:` or `settings:` value is
  the value of a model key. Never put a model key under `app_env:` or
  `settings:`; declare it under `model_keys:`.
- `onboarding_changed_customer_file`: undo the change. Only the repository
  owner may keep an edit they made: they delete the baseline file the message
  names and onboard again. Edits before the first onboard are not checked.
- `onboarding_baseline_missing` (unknown): there is no baseline, and a passing
  check never starts one. Only the repository owner onboards again to start it.

During Enderis-launched runs in the repository folder itself (no run copy),
changes to JSON, YAML, TXT and other data,
lockfiles, caches, databases, logs, build output and configuration are allowed,
except source code, shell scripts, Markdown files, manifests (including
`langgraph.json`, `Containerfile*` and `Procfile`) and nested repositories or
submodules; file-name and extension exclusions ignore case.
The check covers the onboarded package plus files directly at the repository
root. An open baseline older than 24 hours reports unknown
(`onboarding_baseline_expired`); onboard again to recheck.

An unavailable Git check reports unknown and does not fail onboarding.

```sh
enderis driver check .enderis/driver           # manifest, hash, describe; runs local code
enderis onboard <agent-path> --name <agent-name> # finds .enderis/driver/ and says so
# for app: attached, start the app as in driver.md; a launched app starts with each run
enderis run <agent-path> --list
enderis run <agent-path> --eval <name>
```

`--name` is the agent's product name (a slug); without it the agent takes the
driver's `name`. Each name is its own agent, so keep it the same on every
onboard. Any change to a listed file, including `driver.md`, needs
`enderis onboard` again. Status `ready` means the driver is registered, not that the app is up.

## 4. Read the run

Open the printed run link.

- **Conversation:** every reply the driver returned is a message from the
  agent, in order. A wake with no reply is silence, which can be correct.
- **Outcomes:** escalations are listed with their wake. Evaluators read them as
  `run.outcomes`.
- **Front door and app:** check they say what the driver really does.
- **Failures:** an agent failure or agent timeout is the app's side (down,
  error, slow). An Enderis error at the driver is the driver's side (crash,
  a bad result, an unanswered call other than a wake). A missed wake deadline is
  an agent failure when some run of the agent has answered a wake through this
  driver; otherwise (a new or changed driver) the run has no verdict, because the
  driver may be the stuck part. Set `timeout:` if the agent normally takes longer. `AgentTimeout` raised in
  `start` is an Enderis error too: the app never started, so the run is not
  graded. Read the stop log for output the driver held but could not deliver.

Then run a second eval right after the first and confirm nothing from the first
run appears in it.

## Rules

- Never edit customer code, config or scripts. Add files only under
  `.enderis/`. Compose or environment overrides that start the app are allowed.
- Never write a stand-in for an app that has its own server: launch its entry
  point. Never write the app's storage, fake its sign-in or install state, or
  call framework internals. Create that state through the app's own routes.
- Never put a secret in `driver.md`. Settings name variables; values come from
  the environment.
- Never acknowledge the app's output for a wake Enderis did not accept.
- If an `enderis` command fails and the fix is not clear, run `enderis faq`
  before you try again.
- Never commit or push unless asked.
