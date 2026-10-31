---
name: enderis-demo-builder
description: >-
  Build a customer demo in Enderis from discovery material: call transcripts,
  customer documents and web research become a cited brief, a hosted demo
  agent, a playground and evals that run in an Enderis workspace. Use when a
  systems integrator, agency or dev shop asks to prototype an agent for a
  prospect, turn a discovery call into a demo, or replace a PRD with a working
  example the customer can review.
---

# Building a customer demo

The goal is a working answer to "is this what you mean?" The demo is an
Enderis workspace with three parts:

- a **hosted demo agent** that Enderis runs (an `agents/<name>.md` file);
- a **playground** that models the customer's business and systems;
- **evals**, one or more per scenario the customer described.

The evals are the demo now and the acceptance tests later: when the real
agent is built, the same evals grade it.

Work in the integrator's own repository and in a workspace of the
integrator's own organization. Check the workspace with `enderis auth status`.

## Repository layout

```text
discovery/sources.md              # one row per source, with a source id
discovery/transcripts/*.md        # text call transcripts
discovery/docs/*                  # customer documents and notes
brief.md                          # the cited brief, scenarios S1..Sn
agents/<name>.md                  # the hosted demo agent
services/<name>/behavior.py       # only for systems with no built-in service
tests/tools/<name>.yaml           # cases for each custom service
playgrounds/<name>/blueprint.yaml
evals/<eval>/                     # eval.md, playground.yaml, evaluator.py, scripted.json
standards/<name>.py               # optional checks every run is graded on
```

`discovery/` and `brief.md` stay in this repository. `enderis import` reads
only `services/`, `personas/`, `playgrounds/`, `agents/` and `evals/`, plus the
agent's `standards:` file. Customer material reaches Enderis only where you put
it into those files: the agent's prompt, the evals, and the playground (for
example a policy document seeded into `doc_library`).

## Steps

### 1. Intake

Accept text transcripts only (`.md`, `.txt`, `.vtt`, `.srt`). If the user has
only audio, ask them to export a transcript from their call or meeting tool.
Do not transcribe audio.

Write `discovery/sources.md` as a table: source id (`T1`, `D1`, `W1`), kind
(transcript, document, web), title or file, date, and who was present or who
wrote it. Every later claim cites these ids.

### 2. Research

Research the customer on the public web: products, prices, policies, public
process documents, the systems they use. Follow the source rules of the
`enderis-playground-author` skill: every fact gets a URL and the date you
checked it, and each web source gets a `W` id in `discovery/sources.md`.

### 3. Brief

Write `brief.md`. It replaces the PRD and is short: one or two pages.

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
- S1. <Situation in the customer's words>. Expected: <the outcome>. Covers R1, R3. Evals: s1_<name>. [T1 18:05]

## Assumed
- Claims with no source. Each one is a question for the customer.

## Open questions
- What the material does not answer and the demo cannot guess.
```

Cite every claim: a transcript timestamp, a document page or section, or a
web id. A claim with no source goes under **Assumed**. Never move an
assumption into **Rules** without a source. Write scenarios in the
customer's own words and situations, not in tool names. Aim for 8 to 15
scenarios: the main path, the hard cases the customer named, and one or two
cases where the agent must refuse, escalate or ask.

Show the brief to the user before you build. The assumed claims and open
questions are what they take back to the customer.

### 4. Systems map

For each system in the brief, pick a service:

1. Call `get_service_schemas` and use a built-in service when one fits
   (mail, calendar, chat, CRM, tickets, commerce, claims, documents and
   others). Google mail and calendar are one service, `google_workspace`: a
   customer on Google gets both, so never model a Google calendar without its
   mailbox.
2. Put customer documents and policies in the built-in `doc_library`.
3. Write a custom service only when no built-in fits. Read section 8,
   "Authoring a mocked service", of the MCP resource
   `enderis://docs/authoring-evals`. Give it only the operations the
   scenarios need. Use the customer's own names for the system, its records
   and its fields, so a real interface can replace the demo one later.
   Write cases for each operation in `tests/tools/<name>.yaml` and run
   `enderis tools test` before you build the playground.

Write the chosen service in the brief's **Systems** table.

### 5. Playground

Follow the `enderis-playground-author` skill. Discovery transcripts and
documents are sources, the same as web pages: cite them by source id. Records
that no source supplies (customers, orders, cases) are simulated and must be
labelled. Seed the records that the scenarios need among ordinary history
and noise.

### 6. Agent

Write `agents/<name>.md`. The body is the system prompt; take it from the
brief's job, actors and rules. Do not write the evals' answers into the
prompt: the prompt states the rules, the evals test them.

```markdown
---
name: <customer>-<job>
kind: vendor
vendor:
  platform: langgraph
  model: gpt-5.6-luna
  credentials_ref: OPENAI_API_KEY
interfaces:
  - {service: doc_library, interface: doc_library-canonical}
  - {service: <custom service>, interface: <custom service>-canonical}
standards: ../standards/<name>.py
---
You are the <job> assistant for <customer>. ...
```

`credentials_ref: OPENAI_API_KEY` uses the Enderis server's model key, so the
integrator needs no key of their own. Every service has a generated interface
named `<service>-canonical`; use it unless the service ships another.

### 7. Evals

Follow the `enderis-eval-author` skill. Write at least one eval per scenario.
Start each eval's name with its scenario id, for example `s3_late_pickup`, and
list each scenario's eval names in the brief, so the brief and the evals trace
in both directions. Every eval has a `scripted.json`, except a voice eval
without a recorded call (see the eval-author skill). Use rules shared by every scenario as
standards in `standards/<name>.py`, not as copies in each evaluator.

### 8. Import and run

```sh
enderis import . --acceptance
enderis test --agent <name>
```

Fix every import error. Run each eval once with `--provider scripted`
(`enderis run --agent <name> --eval <eval> --provider scripted`) to prove
the evaluator. Then read each live failure:

- **Eval fault** (wrong seed, a check that grades the wrong thing, a judge
  rubric that is too loose or too strict): fix the eval and import again.
- **Agent fault**: improve the prompt when the brief has the rule. Leave the
  failure when the rule is an assumption or an open question. An honest
  failure is part of the demo: it shows the customer what still needs a
  decision.

Do not weaken an eval to make it pass.

### 9. Hand-off

Report to the user:

- the workspace link and the agent name;
- a table of scenarios: id, eval names, last verdict;
- the **Assumed** claims and **Open questions** from the brief.

Tell them they can try the demo agent by hand: `enderis chat --agent <name>`,
or **New chat** on the agent's **Chats** tab in the web app. The web app works
for a customer with no CLI.

Tell them how to show the demo to the customer:

- **Now:** invite the customer's people to this workspace as outside
  collaborators (viewer or editor) from workspace settings.
- **Later:** when the customer creates their own Enderis organization, they
  invite the integrator to their workspace as an editor. The integrator signs
  in with a separate context (`enderis auth login --context <customer>`),
  picks that workspace, and runs `enderis import . --acceptance` from this
  repository. The copy belongs to the customer.

When the customer's real agent exists, connect it with the
`enderis-onboard` skill. Every eval belongs to one agent, so import the evals
again for the real agent:

```sh
enderis import evals --agent <real agent> --acceptance
```

They run unchanged when the real agent uses the same services.
Where it calls the customer's own API, add an interface for that API to the
custom service from step 4.
