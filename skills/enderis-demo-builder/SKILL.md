---
name: enderis-demo-builder
description: >-
  Build a customer demo in Enderis from discovery material: call transcripts,
  customer documents and web research become a cited brief, a hosted demo
  agent, a playground and evals that run in an Enderis workspace. Use when a
  salesperson or engineer at a systems integrator, agency or dev shop asks to
  build an Enderis demo, prototype an agent for a prospect, turn a discovery
  call into a demo, or replace a PRD with a working example the customer can
  review.
---

# Building a customer demo

The goal is a working answer to "is this what you mean?" The demo is an
Enderis workspace with three parts:

- a **hosted demo agent** that Enderis runs (an `agents/<name>.md` file);
- a **playground** that models the customer's business and systems;
- **evals**, one or more per scenario the customer described.

The user first sees the agent working in a chat. The evals come next: they
are the demo's proof now and the acceptance tests later, when the real agent
is built.

Work in the folder the user gave you and in a workspace of the
integrator's own organization.

## Who you work for

The user is often a salesperson, not an engineer. Write to them in plain
words:

- Say "folder", not "repository". Say "tests", not "evals", and "practice
  world", not "playground". Do not mention git, the CLI, MCP or import.
- Run every command yourself. Never ask the user to type a command or edit a
  file. When a command needs their OK, say in one sentence what it does.
- Do not ask them to use git or make a repository. A plain folder is enough.
- Ask them only what they can answer: facts about the customer, a choice of
  workspace, a yes before a long run.

## Folder layout

```text
discovery/sources.md              # one row per source, with a source id
discovery/transcripts/*.md        # text call transcripts
discovery/docs/*                  # customer documents and notes
research/*                        # saved web research
brief.md                          # the cited brief, scenarios S1..Sn
agents/<name>.md                  # the hosted demo agent
services/<name>/behavior.py       # only for systems with no built-in service
tests/tools/<name>.yaml           # cases for each custom service
playgrounds/<name>/blueprint.yaml
evals/<eval>/                     # eval.md, playground.yaml, evaluator.py, scripted.json
standards/<name>.py               # optional checks every run is graded on
```

`discovery/`, `research/` and `brief.md` stay in this folder. `enderis import` reads
only `services/`, `personas/`, `playgrounds/`, `agents/` and `evals/`, plus the
agent's `standards:` file. It reads each service, playground and eval only
from its own folder, and fails one with a symbolic link that leads out of it.
Customer material reaches Enderis only where you put it into those files: the
agent's prompt, the evals, and the playground (for example a policy document
seeded into `doc_library`).

## Steps

The order gets the user to a working chat with the demo agent first. Web
research runs in the background; tests and test runs wait for the user's yes.

### 0. Setup

Do this yourself, every time, before anything else. Each check is quick when
the step is already done.

1. **CLI.** Run `enderis --version`. If it fails, install it:
   `curl -fsSL https://enderis.ai/install.sh | sh`. The installer puts
   `enderis` in `~/.local/bin` and adds that folder to the user's shell
   profile, which your current shell has not read: call it by its full path,
   `~/.local/bin/enderis`. The installer also installs the Enderis skills.
2. **Sign-in.** Run `enderis auth status`. If it is not connected, run
   `enderis auth login` in the background, so you can read its output while
   it waits. It prints a login code and a link, and tries to open the link in
   the user's browser. Always give the user both the link and the code: the
   browser may not open. Tell them to type the code on that page, choose the
   workspace for this demo and approve. The code works for 10 minutes. If the
   command says the login expired, run it again and give the user the new
   link and code. Wait for the command to finish, then check
   `enderis auth status` again.
3. **Enderis tools.** The later steps call Enderis tools such as
   `get_service_schemas`. If you do not have them, connect `enderis mcp`,
   which uses the sign-in from step 2, for this folder:
   - **Claude:** write `.mcp.json` in the folder:
     `{"mcpServers": {"enderis": {"command": "<full path to enderis>", "args": ["mcp"]}}}`.
   - **Codex:** run `codex mcp add enderis -- <full path to enderis> mcp`.
   - **Other assistants:** add a local MCP server that runs
     `<full path to enderis> mcp`.

   The tools appear only in a new session. Tell the user, in one message:
   setup is done; start a new session in this same folder, paste the same
   message again, and allow the Enderis tools if asked. Then stop.

### 1. Intake

The user's files may be anywhere in the folder. Move call transcripts to
`discovery/transcripts/` and documents and notes to `discovery/docs/`. Tell
the user what you moved.

Accept text transcripts only (`.md`, `.txt`, `.vtt`, `.srt`, `.docx` or
`.pdf` of a transcript). If the user has only audio or video, ask them to
export a transcript from their call or meeting tool (Zoom, Teams, Google
Meet, Gong and most others can). Do not transcribe audio.

Write `discovery/sources.md` as a table: source id (`T1`, `D1`, `W1`), kind
(transcript, document, web), title or file, date, and who was present or who
wrote it. Every later claim cites these ids.

If the folder already has a brief, research, an agent or a practice world
(from an earlier session or the user's own work), use them. Do not rebuild
what is there; fill only what is missing.

### 2. Research, in the background

Research the customer on the public web: products, prices, policies, public
process documents, the systems they use. It improves the demo but must not
delay the first chat. When you can start a background agent, give it this
step now and go on to step 3. When you cannot, do this step after step 6.

Follow the source rules of the `enderis-playground-author` skill: every fact
gets a URL and the date you checked it, and each web source gets a `W` id in
`discovery/sources.md`. Save what you find under `research/`. When it is
done, add the facts to the brief, the agent's prompt and the practice world,
import again (step 6), and tell the user in one or two lines what changed.

### 3. Brief

Write `brief.md` from the transcripts and documents. It replaces the PRD and
is short: one page. Scenarios come later, in step 7.

```markdown
# <Customer> — <agent name> brief

## Job
One paragraph: who the agent serves, on which channel, and what it does. [T1 12:40]

## Actors
- Who talks to the agent, who it acts for, who it must not act for. [T1, D2 p.3]

## Systems
| System | What the agent does there | Enderis service | Source |

## Rules
- R1. One rule per line, with its source. [D1 §4.2]

## Scenarios
(Added in step 7.)

## Assumed
- Claims with no source. Each one is a question for the customer.

## Open questions
- What the material does not answer and the demo cannot guess.
```

Cite every claim: a transcript timestamp, a document page or section, or a
web id. A claim with no source goes under **Assumed**. Never move an
assumption into **Rules** without a source.

Show the user the job, the rules and the assumed claims in one short message,
and keep building. Do not wait for their answer. Apply their corrections when
they come, and import again.

### 4. Systems map

For each system in the brief, pick a service:

1. Call `get_service_schemas` and use a built-in service when one fits
   (mail, calendar, chat, CRM, tickets, commerce, claims, documents and
   others). Google mail and calendar are one service, `google_workspace`: a
   customer on Google gets both, so never model a Google calendar without its
   mailbox.
   SharePoint and OneDrive are one service, `microsoft_365`: each person
   with an email gets a OneDrive, and a Microsoft 365 group gets a team site.
2. Put customer documents and policies in the built-in `doc_library`.
3. Write a custom service only when no built-in fits. Read section 8,
   "Authoring a mocked service", of the MCP resource
   `enderis://docs/authoring-evals`. Give it only the operations the agent's
   main job needs; add more when a test needs them. Use the customer's own
   names for the system, its records and its fields, so a real interface can
   replace the demo one later. Write cases for each operation in
   `tests/tools/<name>.yaml` and run `enderis tools test` before you build the
   practice world.

Write the chosen service in the brief's **Systems** table.

### 5. One practice world and the agent

Build one playground, following the `enderis-playground-author` skill.
Discovery transcripts and documents are sources, the same as web pages: cite
them by source id. Records that no source supplies (customers, orders, cases)
are simulated and must be labelled. For the first chat, seed what the
agent's main job needs and a few ordinary records around it. Add more history
and noise in step 7, when the tests need them.

Write `agents/<name>.md`. The body is the system prompt; take it from the
brief's job, actors and rules. Do not write test answers into the prompt: the
prompt states the rules, the tests check them.

```markdown
---
name: <customer>-<job>
kind: vendor
vendor:
  platform: langgraph
  model: gpt-6-luna
  credentials_ref: OPENAI_API_KEY
interfaces:
  - {service: doc_library, interface: doc_library-canonical}
  - {service: <custom service>, interface: <custom service>-canonical}
---
You are the <job> assistant for <customer>. ...
```

`credentials_ref: OPENAI_API_KEY` uses the Enderis server's model key, so the
integrator needs no key of their own. Every service has a generated interface
named `<service>-canonical`; use it unless the service ships another.

### 6. Import, check, open the chat

```sh
enderis import . --acceptance
```

Fix every import error. Then send the agent one message the customer's own
user would send, to check that it answers:

```sh
printf '%s\n' '<message>' | enderis chat --agent <name> --playground <playground> --idle-timeout 1m
```

Fix the agent or the practice world until the reply is sensible. The command
prints `Run: <link>`. Make the chat link from it: keep the part before
`/runs/`, then add `/agents/<agent id>?tab=chats&playground=<playground>`.
Get the agent id from `list_agents`. Open the chat link in the user's
browser (`open <link>` on a Mac, `xdg-open <link>` on Linux), and tell them:
select **New chat**, and each reply is drafted for them; **Autopilot** sends
the drafts by itself. If the agent page has no **Chats** tab, the workspace
does not have chats turned on: tell the user to ask their Enderis contact.

This is the first stop. Ask the user if they want tests next.

### 7. Tests, when the user says yes

Suggest 8 to 15 test topics as a numbered list, in the customer's own words
and situations, not tool names: the main path, the hard cases the customer
named, and one or two cases where the agent must refuse, escalate or ask.
Cite each one. Let the user pick, drop or add topics, then add the chosen ones
to the brief as scenarios:

```markdown
- S1. <Situation in the customer's words>. Expected: <the outcome>. Covers R1, R3. Evals: s1_<name>. [T1 18:05]
```

Follow the `enderis-eval-author` skill. Write at least one eval per scenario.
Start each eval's name with its scenario id, for example `s3_late_pickup`, and
list each scenario's eval names in the brief, so the brief and the evals trace
in both directions. Every eval has a `scripted.json`, except a voice eval
without a recorded call (see the eval-author skill). Use rules shared by every
scenario as standards in `standards/<name>.py`, set with `standards:` in the
agent's frontmatter, not as copies in each evaluator.

Import again and fix every error. Run each eval once with `--provider
scripted` (`enderis run --agent <name> --eval <eval> --provider scripted`) to
prove the evaluator. Tell the user the tests are in the web app, and that
**Load eval** on the **Chats** tab starts a chat from one of them.

### 8. Live run, when the user says yes

Offer one live run of the tests. Live runs are slow. Do not start it without
their yes, and do not repeat it. It runs each test once:

```sh
enderis test --agent <name>
```

Read each live failure:

- **Eval fault** (wrong seed, a check that grades the wrong thing, a judge
  rubric that is too loose or too strict): fix the eval and import again.
- **Agent fault**: improve the prompt when the brief has the rule. Leave the
  failure when the rule is an assumption or an open question. An honest
  failure is part of the demo: it shows the customer what still needs a
  decision.

Do not weaken an eval to make it pass.

### 9. Hand-off

When the user stops, report:

- the chat link and the agent name;
- when there are tests, a table of scenarios: id, eval names, last verdict;
- the **Assumed** claims and **Open questions** from the brief.

Tell them how to show the demo to the customer:

- **Now:** invite the customer's people to this workspace as outside
  collaborators (viewer or editor) from workspace settings.
- **Later:** when the customer creates their own Enderis organization, they
  invite the user to their workspace as an editor. The user then opens this
  folder with you again and asks you to copy the demo there. Sign in with a
  separate context (`enderis auth login --context <customer>`), have the user
  pick the customer's workspace, and run `enderis import . --acceptance` from
  this folder. The copy belongs to the customer.

The rest of this section is for the engineers who build the real agent. Do
not explain it to a salesperson; tell them to hand this folder to those
engineers.

When the customer's real agent exists, connect it with the
`enderis-onboard` skill. Every eval belongs to one agent, so import the evals
again for the real agent:

```sh
enderis import evals --agent <real agent> --acceptance
```

They run unchanged when the real agent uses the same services.
Where it calls the customer's own API, add an interface for that API to the
custom service from step 4.
