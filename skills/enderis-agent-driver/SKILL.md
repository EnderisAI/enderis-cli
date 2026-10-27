---
name: enderis-agent-driver
description: >-
  Write an Enderis agent driver for an agent whose front door `enderis onboard`
  cannot drive: triage the agent, write driver.md and driver.py from the
  template into .enderis/driver/, check it, onboard, run one eval and read the
  run.
  Use when onboarding reports needs_ingress, needs_worker or no_agent_target,
  or when asked to connect an unusual agent (webhook, events or simulator API,
  queue, own clock or outbox) to Enderis.
---

# Writing an agent driver

A driver is a small local program that carries each Enderis wake to the agent
the way its real channel does and returns what the agent answered. It lives in
`.enderis/driver/` in the agent repository: `driver.md` (the manifest) and the
code it names. `.enderis/` belongs to Enderis and the agent never loads it, so
adding it does not change the agent. Reference:
https://enderis.ai/docs/agents/drivers.

The rule that decides everything: **never change the agent.** Not its code,
config, scripts or prompts. You may start it with your own compose file or
environment overrides. If the agent cannot be reached without a change, stop
and report the gap.

## 1. Triage

Answer these before writing code. Write the answers into the body of
`driver.md`.

1. **Why inspection missed it.** Read `enderis inspect <path> --json`. Note the
   blocker (`no_agent_target`, `needs_ingress`, `needs_worker`) and the reason.
2. **Front door.** Is there an entry point real users reach (a webhook, a chat
   API)? Or only a test harness (a simulator, an events API)? Prefer the real
   one. Set `front_door: production` or `harness` honestly; the run page shows it.
3. **Start.** How does the app start without edits? Find the existing compose
   file, script or command and the environment it reads. Either you start the
   app yourself before the run (`app: attached`), or the driver's `start` and
   `stop` hooks start and stop one copy of it per run slot (`app: managed`).
4. **Time.** Does the app answer at once, or on a timer, a batch or a
   scheduler? If it has its own clock, find how to make it run now (a tick
   endpoint, a debug flag, a short interval set by environment).
5. **Isolation.** The default is `isolation: exclusive`: one run at a time uses
   the app. Use `isolation: namespace` only when each run gets its own
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
   channel records and escalations. The app's own API calls are not mocked and
   not seen, so an eval cannot grade them.
7. **Knowledge.** Where does the agent's knowledge and data live (files,
   database, an API)? The app keeps using it during runs. It decides which evals
   make sense: ones whose answer shows in what the agent says.

## 2. Write the driver

Copy `template/` to `.enderis/driver/` at the agent repository root (or in
the agent's package, for a monorepo). Use another directory only if the owner
asks; then pass `--driver <dir>` to `enderis onboard`. Then:

- `driver.md`: set `name`, `description` (for people), `command` (it runs in
  the driver directory), the `settings` it reads (environment variable names
  such as the app URL, never model keys or `PYTHONPATH`), and `files` (every
  file the driver needs). Keep `app: attached` and `isolation: exclusive`;
  change to `namespace` only when triage item 5 allows it.
- For `app: managed`, add `start` and `stop` (lists that run in the driver
  directory; list their scripts in `files`). `start` exits 0 only when the copy
  is ready; `stop` removes the copy and succeeds when there is nothing to stop.
  Both hooks and the driver get `ENDERIS_SLOT`, `ENDERIS_APP_PORT` (the copy's
  port), `ENDERIS_INSTANCE` (use it for the compose project name and state
  files) and `ENDERIS_REPO` (the full path of the folder you onboarded), plus `HOME`, `USER`
  and the `DOCKER_*` variables. `stop` must reach what its `start` made even if
  the environment changed in between (for example the default Docker context):
  record what it needs at `start`, keyed by `ENDERIS_INSTANCE`, and exit
  non-zero when it cannot reach it.
- `driver.py`: change the requests marked TODO. Keep these parts as they are:
  - every chat id or user id comes from `ctx.run_id`;
  - when `wake["waiting"]` is above zero, the driver may hold back the app's
    output (its clock stays paused) and return it on a later wake; when it is
    zero, it must drain everything before it answers;
  - replies name the delivery they answer (`reply(delivery["id"], text)`);
  - escalations name the channel (`escalate(wake["channel"], reason)`);
  - the app's outbox is acknowledged, by message id, only for wakes up to
    `ctx.accepted_through`;
  - an unreachable or failing app raises `AgentError`; an app that does not
    answer in time raises `AgentTimeout`. Any other exception is reported as
    a driver bug.

The CLI provides `enderis.driver` to the driver when it starts it. You do not
install anything. `print` and the output of programs the driver starts go to
stderr; use `ctx.log` for the stop log.

## 3. Check, onboard, run

```sh
enderis driver check .enderis/driver           # manifest, hash, describe; runs local code
enderis onboard <agent-path> --name <agent-name> # finds .enderis/driver/ and says so
# start the app as in driver.md, then
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
  a bad result, a deadline missed by the driver). Read the stop log for output
  the driver held but could not deliver.

Then run a second eval right after the first and confirm nothing from the first
run appears in it.

## Rules

- Never edit customer code, config or scripts. Add files only under
  `.enderis/`. Compose or environment overrides that start the app are allowed.
- Never put a secret in `driver.md`. Settings name variables; values come from
  the environment.
- Never acknowledge the app's output for a wake Enderis did not accept.
- If an `enderis` command fails and the fix is not clear, run `enderis faq`
  before you try again.
- Never commit or push unless asked.
