---
name: enderis-demo-builder
description: >-
  Build a customer demo in Enderis from a source (a web page, call
  transcripts, customer documents or a folder), or from a default business
  when there is none: a cited brief, a hosted demo agent, a playground, a chat
  with the agent, then evals that run in an Enderis workspace. Use when a
  salesperson or engineer at a systems integrator, agency or dev shop asks to
  build an Enderis demo, create a demo agent, prototype an agent for a
  prospect, turn a discovery call into a demo, or replace a PRD with a working
  example the customer can review.
---

# Building a customer demo

The goal is a working answer to "is this what you mean?" The demo is an
Enderis workspace with three parts:

- a **hosted demo agent** that Enderis runs (an `agents/<name>.md` file);
- a **playground** that models the business and its systems;
- **evals**, one or more per scenario the business has.

The user first sees the agent working in a chat. The evals come next, behind
the chat: they are the demo's proof now and the acceptance tests later, when
the real agent is built.

Work in the folder the user gave you (an empty folder is fine) and in the
workspace the request names.

## Who you work for

The user is often a salesperson, not an engineer. Write to them in plain
words:

- Say "folder", not "repository". Say "tests", not "evals", and "practice
  world", not "playground". Do not mention git, the CLI, MCP or import.
- Run every command yourself. Never ask the user to type a command or edit a
  file. When a command needs their OK, say in one sentence what it does.
- Do not ask them to use git or make a repository. A plain folder is enough.
- **Never stop to ask when a default exists.** Take the default, say in one
  line which default you took, and keep going. Stop only for the sign-in
  approval and for a fact no default can supply.

## The source

The request usually has a line `Source: <source>`. It can be:

- **a URL**: the business's web page. Fetch it and save what you read under
  `research/`. It is source `W1`.
- **a document or a folder** of transcripts, documents and notes: the
  material for intake (step 2).
- **none**: `Source: none`, or no `Source:` line and no files in the
  folder. Use the default business below.

### The default business

With no source, build the demo for **Bee's Plumbing & Heating**, a real
family-owned plumbing, heating and electrical company in Seattle,
Washington. Source `W1` is its FAQ page:
https://www.beesplumbingandheating.com/about-us/faq/. Fetch it with your web
tool and cite it like any other source. If that fails or returns no FAQ text,
fetch it with plain `curl -sL <url>` (some sites refuse browser-like clients
and answer `curl`). The page cannot be fetched only when both fail.

Assume these systems. Nothing on the page says the business uses them:

| System | Enderis service |
|---|---|
| WhatsApp, where customers write in | `whatsapp` |
| Google Calendar, with its Gmail mailbox | `google_workspace` |
| Stripe, for deposits and invoices | `stripe` |
| HubSpot, for customer records | `hubspot` |
| A document library with the FAQ and policies | `doc_library` |

Before you build anything, tell the user, in these words or close to them:

> You gave no source, so Enderis picked a random real business from the
> Pacific Northwest: Bee's Plumbing & Heating in Seattle. The demo assumes it
> uses WhatsApp, Google Calendar and Gmail, Stripe, HubSpot and a document
> library. Those systems are assumptions, not facts from the business. To
> build the demo for your own business, run this again with your own source:
> a web page, a document or a folder.

Put the five systems under **Assumed** in the brief. Facts about the
business (services, service area, emergency hours, pricing policy,
membership) come from `W1` and are cited. Customers, staff, jobs,
appointments, prices for jobs and payments are simulated: the brief and the
playground's `description` say so, and no record text does.

If the page cannot be fetched, build a small invented plumbing business
instead, with the same five systems. Give it a name that is clearly not a
real company. There is then no `W1` and no sourced fact: label all of it
simulated, in the brief and in the playground's `description`. Tell the user
this instead of the message above:

> You gave no source, and the default business's page could not be read, so
> Enderis invented a small plumbing business. Everything in it is simulated,
> including its systems: WhatsApp, Google Calendar and Gmail, Stripe, HubSpot
> and a document library. To build the demo for your own business, run this
> again with your own source: a web page, a document or a folder.

## Folder layout

```text
discovery/sources.md              # one row per source, with a source id
discovery/transcripts/*.md        # text call transcripts
discovery/docs/*                  # customer documents and notes
research/*                        # saved web research
brief.md                          # the cited brief, scenarios S1..Sn
agents/<name>.md                  # the hosted demo agent
playgrounds/<name>/blueprint.yaml
playgrounds/<name>/build.py       # the script that writes blueprint.yaml
playgrounds/<name>/customers.yaml # each customer's records, written by hand
evals/<eval>/                     # eval.md, playground.yaml, evaluator.py, scripted.json
standards/<name>.py               # optional checks every run is graded on
```

`discovery/`, `research/` and `brief.md` stay in this folder. `enderis import`
reads only `services/`, `personas/`, `playgrounds/`, `agents/` and `evals/`,
plus the agent's `standards:` file. It reads each service, playground and eval
only from its own folder, and fails one with a symbolic link that leads out
of it. Customer material reaches Enderis only where you put it into those
files: the agent's prompt, the evals, and the playground (for example a
policy document seeded into `doc_library`).

## Steps

Steps 1 to 6 get the user to a chat with the demo agent. They need only the
`enderis` command and the files of the Enderis skills. Steps 7 to 9 run
behind the chat, without asking for a yes.

### 1. Setup

Do this yourself, every time. Each check is quick when the step is already
done.

1. **CLI.** Run `enderis --version`. If it fails, install it with the
   command the request gives, else `curl -fsSL https://enderis.ai/install.sh | sh`.
   The installer puts `enderis` in `~/.local/bin`, which your current shell
   may not have on its PATH: call it by its full path,
   `~/.local/bin/enderis`. The installer also installs the Enderis skills
   into `~/.agents/skills` (and `~/.claude/skills` when Claude Code is set
   up). If the skills are missing, run `enderis skills install`.
2. **Sign-in.** Check it with
   `enderis auth status --workspace <org>/<workspace>`, using the workspace
   the request names (its id or `org/workspace`). When it prints
   `Status: connected`, go on. Otherwise, if the request gives a sign-in
   command, run exactly that command in the foreground; else:

   ```sh
   enderis auth login --workspace <org>/<workspace>
   ```

   Run it in the foreground too. It opens the sign-in page in the user's browser, prints
   `Sign in at <link> with the code <code>` and exits at once. Your next message always gives the
   user that line as it is, before anything else, in case the page did not open, and tells them to
   open the link, type the code, choose the workspace if the page asks, and
   approve. If the login names a workspace id, as the user's copied command does, they can also
   type the code into the box on the Agents page they copied the prompt from. The code works for
   10 minutes. Then start the `--wait` command
   it printed, in the background:

   ```sh
   enderis auth login <the flags on that line> --wait > login.log 2>&1 &
   ```

   Do not end your turn to wait: go on with the steps that do not need
   sign-in (intake, research, the brief, the playground and agent files).
   When only signed-in steps remain, wait inside this turn: read
   `login.log` every 10 seconds, for up to 10 minutes, until it ends with
   `Connected to <org>/<workspace>`. Then check `enderis auth status`
   again. When `login.log` instead says:

   - the login `expired` or `was denied`: run the sign-in command again,
     give the new `Sign in at ...` line at once, and start `--wait` again;
   - `Nothing was saved` (the browser approved another workspace): do the
     same, and tell the user to choose the workspace the request names on
     the page.

You do not need the Enderis MCP tools for this flow. If you already have
them, you may use them later as extra help.

### 2. Intake

With a source, put call transcripts in `discovery/transcripts/` and
documents and notes in `discovery/docs/`. Move files that are already in
this folder. Copy files from anywhere else; never link to them, because
import refuses a link that leads out of a folder. Tell the user what you
moved and copied.

Accept text transcripts only (`.md`, `.txt`, `.vtt`, `.srt`, `.docx` or
`.pdf` of a transcript). If the user has only audio or video, tell them to
export a transcript from their call or meeting tool (Zoom, Teams, Google
Meet, Gong and most others can), and build from the other material
meanwhile. Do not transcribe audio.

Write `discovery/sources.md` as a table: source id (`T1`, `D1`, `W1`), kind
(transcript, document, web), title or file, date, and who was present or who
wrote it. Every later claim cites these ids. For the default business, the
table has one row, `W1`.

If the folder already has a brief, research, an agent or a practice world
(from an earlier session or the user's own work), use them. Do not rebuild
what is there; fill only what is missing.

### 3. Research, in the background

Research the business on the public web: services, prices, policies, public
process documents, the systems they use. It improves the demo but must not
delay the first chat. When you can start a background agent, give it this
step now and go on to step 4. When you cannot, do this step after step 6.

Follow the source rules in the playground guide (step 5): every fact gets a
URL and the date you checked it, and each web source gets a `W` id in
`discovery/sources.md`. Save what you find under `research/`. When it is
done, add the facts to the brief, the agent's prompt and the practice world,
import again, and tell the user in one or two lines what changed.

### 4. Brief and systems

Write `brief.md` from the sources. It replaces the PRD and is short: one
page.

```markdown
# <Business> — <agent name> brief

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
- Claims with no source. Each one is a question for the business.

## Open questions
- What the material does not answer and the demo cannot guess.
```

Cite every claim: a transcript timestamp, a document page or section, or a
web id. A claim with no source goes under **Assumed**. Never move an
assumption into **Rules** without a source. Never invent a fact a source
could supply.

For each system, pick a built-in service. Read the services' schemas:

```sh
enderis tools schemas whatsapp google_workspace stripe hubspot doc_library --json
```

Pass the services the brief needs; the default business's five are shown.
It prints, for each service, its
collections, the row shape a seed must follow (`seed_authoring`), the fields
that name a person (`person_fields`), the channels people listen on
(`channels`) and the tools with their arguments (`tools`). If the command
itself is unknown, the CLI is old: run `enderis update` and try again.

- Google mail and calendar are one service, `google_workspace`: a business on
  Google gets both, so never model a Google calendar without its mailbox.
- SharePoint, OneDrive, Outlook and Teams share the `microsoft_365` service.
  Outlook mail and calendar can be reached through Graph, Softeria, Work IQ,
  or the Agent 365 Mail and Calendar MCP servers (`microsoft_365-mail`,
  `microsoft_365-calendar`), all on one mailbox and calendar model.
- Put documents and policies in `doc_library`.
- When no built-in service fits a system, leave that system out of the first
  chat and put it under **Open questions**. A custom service comes later
  (step 7).

Show the user the job, the rules and the assumed claims in one short
message, and keep building. Do not wait for an answer. Apply corrections
when they come, and import again.

### 5. One small practice world and the agent

Read the playground guide, `playground-authoring.md` in the
`enderis-playground-author` skill folder (installed at
`~/.agents/skills/enderis-playground-author/playground-authoring.md`), and
the rules in that skill's `SKILL.md`. Before the first chat, do the guide's
workflow steps 2 and 4 to 6 only. Step 1 (ask the user) is done: the request
and the source answer it. Skip step 3 (study a starter): the shapes below
replace it. The guide's audit (its step 7) and evals (its step 8) come
after the chat, in step 7 of this skill. The guide's blueprint section opens with a complete
example that imports as it is: start from it. Sources include the user's
transcripts and documents, cited by id.

For the first chat, keep the practice world small but real: the agent as a
person, the business as an `internal` org, its staff, some customers with
their records in each service, and the business's own documents. For the
default business that is:

- the agent, with a WhatsApp number (`handles.whatsapp`, digits only) and a
  mailbox on the business's domain;
- an office manager and two or three technicians, as people in the
  business's org, each with a working calendar that has booked jobs and
  open slots;
- six to eight customers, each with a WhatsApp number, an email, a HubSpot
  contact and, for most, a past job, an upcoming appointment or a Stripe
  invoice;
- the FAQ from `W1` in `doc_library`, paraphrased faithfully, with the URL
  and date in your research file, and an internal price guide for common
  jobs (see step 7).

No record says "simulated" or "demo"; the `description` does. The business's
own accounts carry its name: the WhatsApp account and the Stripe account
(`stripe: {account: {id: acct_bees, business_name: Bee's Plumbing & Heating}}`).

Write it with a script, `playgrounds/<name>/build.py`, that writes
`playgrounds/<name>/blueprint.yaml`, so you can re-run it when you deepen the
world in step 7. JSON is valid YAML, so a plain Python script can write the
file with `json.dumps`. Say in the blueprint's `description` which data is
simulated.

Shapes the schemas do not spell out, for the default business:

```yaml
people:
  - {key: assistant, kind: agent, name: Bee's Assistant, emails: [assistant@beesplumbingandheating.com], handles: {whatsapp: "12065550100"}, orgs: [bees]}
  - {key: tom, name: Tom Brannigan, emails: [tbrannigan@icloud.com], handles: {whatsapp: "14255550144"}}
actors:
  - {person: tom, listens: ["whatsapp:chat:assistant"]}   # hears the agent's WhatsApp replies
services:
  whatsapp:
    accounts: [{phone: "12065550100", name: Bee's Plumbing & Heating}]
    messages: [{id: wamid-tom-1, from: "14255550144", to: "12065550100", text: "...", timestamp: "2026-11-10T17:05:00-08:00"}]
  hubspot:
    properties: [{object: contacts, name: bees_club_member, type: bool, label: Bee's Club member}]
    owners: [{id: "1", email: assistant@beesplumbingandheating.com}]
    contacts: [{id: "101", firstname: Tom, lastname: Brannigan, email: tbrannigan@icloud.com, phone: "14255550144", city: Everett, bees_club_member: false, hubspot_owner_id: "1"}]
```

**HubSpot: the agent must be able to read every fact it needs.** Put each
such fact in a standard property (`email`, `firstname`, `lastname`, `phone`,
`company`, `city`, `state`, `country` and others), or give its custom
property a `properties` row, as `bees_club_member` has above. A HubSpot read
returns only email, name and dates unless the agent asks for properties by
name, so name each property the agent must read in its prompt (for example,
"read `bees_club_member` and `phone` on the contact"). In the first chat, ask
about one customer and check that the agent reads the fact.

A Stripe customer's `email` must belong to a person in `people`.

Write `agents/<name>.md`. The body is the system prompt; take it from the
brief's job, actors and rules. Do not write test answers into the prompt: the
prompt states the rules, the tests check them.

```markdown
---
name: bees-plumbing-assistant
kind: vendor
vendor:
  platform: langgraph
  model: gpt-6-luna
  credentials_ref: OPENAI_API_KEY
interfaces:
  - {service: whatsapp, interface: whatsapp-canonical}
  - {service: google_workspace, interface: google_workspace-canonical}
  - {service: stripe, interface: stripe-canonical}
  - {service: hubspot, interface: hubspot-canonical}
  - {service: doc_library, interface: doc_library-canonical}
---
You are the customer assistant for Bee's Plumbing & Heating in Seattle. ...

Answer on the channel the message came in. When a message arrives on
WhatsApp, reply with whatsapp.send_message to that sender. In a direct chat,
reply in the chat. Never answer a WhatsApp message only in your final
response.
```

Put the last paragraph in every prompt as written. Leave out its WhatsApp
sentences only when the agent does not listen on WhatsApp.

`credentials_ref: OPENAI_API_KEY` uses the Enderis server's model key, so the
user needs no key of their own. Every service has an interface named
`<service>-canonical`; use it. The agent reads the date and time with its
built-in clock tool, which follows the playground's `epoch`.

### 6. Import and open the chat

```sh
enderis import . --acceptance --authored-by coding-agent
```

It prints how many services, personas, playgrounds, agents and evals it
created, left unchanged or failed, then one line per failure. Fix every
failure and run it again until nothing fails; if an error is not clear, run
`enderis faq`. Then start the chat in the background:

```sh
enderis chat --agent <agent name> --playground <playground name> < /dev/null > chat.log 2>&1 &
```

The first line of `chat.log` is `chat: <link>`. Wait up to 30 seconds for
it, then try once to open it: `open <link>` on a Mac, `xdg-open <link>` on
Linux. If that fails or is refused, print the link once for the user and go
on. Do not try other browsers. The chat
waits for messages the user types in the browser, and ends after 30 minutes
with no message.

Tell the user: the chat with the demo agent is open; type what a customer
would write. Each reply is drafted for them, and **Autopilot** sends the
drafts by itself. Say that you are now building the tests behind the chat.

When `chat.log` has no `chat:` line:

- it names a missing playground or agent: the import did not store it; fix
  the import and run it again;
- it says `needs OPENAI_API_KEY` (on Enderis's servers:
  `needs OPENAI_API_KEY, which is not configured on this server`): the
  server has no model key for `credentials_ref`; tell the user the chat
  needs the Enderis team to add one, and go on with step 7 (scripted
  self-tests need no key; skip step 8);
- it ends with `Nothing was sent, so the chat was not saved.`: the CLI is
  too old to wait for browser messages; run `enderis update`, then start the
  chat again;
- anything else: run `enderis faq`, fix what it names, and start the chat
  again.

### 7. Behind the chat: a deeper world and the tests

Do this without asking for a yes, while the user chats.

1. **Deepen the practice world** to a working business, as the guide's
   "Operations at real scale" says. For the default business: at least 30
   customers in HubSpot and Stripe; three weeks of past jobs and two weeks
   of booked work on the technicians' calendars, with open slots; open
   estimates as HubSpot deals; paid, open and overdue invoices; WhatsApp and
   email threads at different stages; noise (supplier invoices, newsletters,
   a spam message); and the real edge cases the brief implies (an emergency
   at night, a customer outside the service area, a member discount). Follow
   the guide's "Stories, not templates": each customer's records are written
   by hand in `customers.yaml`, with their own problem, messages and replies
   in their own words, and amounts from the price guide. Take
   every published amount, such as a discount rate or a fee, from a source.
   The amounts of the simulated operations (an invoice total, the price of a
   common job) are simulated: keep them plausible and consistent, put the
   job prices the agent may quote in one internal price guide document, and
   name it in the `description` as simulated. Re-run the script and import
   again.
2. **Audit the world.** Give a background agent, when you can start one,
   only the blueprint, the research files and a browser, and ask it to run
   the guide's audit (workflow step 7). Otherwise do it yourself: re-check a
   sample of sourced facts against their sources, check that the
   `description` names the simulated data, and that no record text says so. Fix what it finds, re-run the script and
   import again.
3. **Pick the scenarios.** Choose four to six from the brief, in the
   business's own words: the main path, the hard cases the source names, and
   one or two where the agent must refuse, escalate or ask. Cite each. Add
   them to the brief:

   ```markdown
   - S1. <Situation in the business's words>. Expected: <the outcome>. Covers R1, R3. Evals: <eval_name>. [W1]
   ```

   Tell the user the list in one short message. They can add or drop
   scenarios at any time; do not wait for them.
4. **Write the evals.** Follow the `enderis-eval-author` skill, and take its
   proposed answers without waiting. Write one eval per scenario. Name each
   eval with a short phrase that says what it tests, for example
   `night_emergency_burst_pipe`, never with the scenario id (`s3_...`): owners
   see the name in every list. List each scenario's eval names in the brief,
   so the brief and the evals trace in both directions. Every eval has a `scripted.json`. Use rules
   shared by every scenario as standards in `standards/<name>.py`, set with
   `standards:` in the agent's frontmatter, not as copies in each evaluator.

   A customer who writes in on WhatsApp starts the eval on WhatsApp. With the
   people above, the eval's frontmatter has:

   ```yaml
   principal: assistant
   listens: [whatsapp:chat:tom]           # the agent hears Tom's messages
   cast:
     - person: tom
       role: user                         # the person who starts the eval
       kind: persona
       persona: cooperative
       listens: ["whatsapp:chat:assistant"]
       goal: Get a time for a visit, then stop.
   trigger: {kind: message, from: tom, channel: "whatsapp:chat:assistant"}
   ```

   The agent answers with `whatsapp.send_message` to Tom's number, so grade
   the reply in the `whatsapp` service's added `messages`.
5. **Import and self-test.** Run
   `enderis import . --acceptance --authored-by coding-agent` and fix every
   error. Then run each eval once on its script:

   ```sh
   enderis run --agent <agent name> --eval <eval> --provider scripted
   ```

   It prints one line, `<eval> <verdict> <run link>`, then one indented line
   per failed assertion. A scripted run must pass. When it does not, the eval
   is wrong (the evaluator, the seed or the script), not the agent: fix the
   eval, import again and rerun it.
6. **A custom service, only if step 4 of this skill left a system out.**
   Follow the `enderis-adapter-author` skill: it writes the service and its
   interface, tests them with `enderis tools test` and imports them. Give it
   only the operations the agent's main job needs, and use the business's
   own names for the system, its records and its fields. Then add the
   service to the agent and the world. If that skill is not installed, leave
   the system under **Open questions**.

### 8. One live run

When every scripted self-test passes, run the main-path eval once against
the live agent. Apart from the one rerun below, do not start more live runs
on your own: live runs are slow and use model credit.

```sh
enderis run --agent <agent name> --eval <main-path eval>
```

Open the run link on its result line in the user's browser and tell them
the result in one line. If the line says `error` and `needs
OPENAI_API_KEY`, the server has no model key: tell the user and stop here. Read the failure, if any:

- **Eval fault** (wrong seed, a check that grades the wrong thing, a judge
  rubric that is too loose or too strict): fix the eval and import again.
- **Agent fault**: improve the prompt when the brief has the rule. Leave the
  failure when the rule is an assumption or an open question. An honest
  failure is part of the demo: it shows the business what still needs a
  decision.

After a fix to the eval or the prompt, import and run that eval live once
more before the hand-off, and give the user the new link. This rerun is
part of the step, not an extra run to ask about. Do not weaken an eval to make it pass. Offer the user a live run of every
test (`enderis test --agent <agent name>`, which runs each acceptance test
once), and start it only on their yes.

### 9. Hand-off

When you are done, report:

- the chat link and the agent name;
- the defaults you took, including the default business when there was no
  source;
- a table of scenarios: id, eval names, scripted result, live result;
- the **Assumed** claims and **Open questions** from the brief.

Tell them how to show the demo to the customer:

- **Try the demo without an account:** use **Share** on the agent page. The link
  pins the agent and playground versions and lets visitors chat and comment.
  It shares all records in that playground and their chat's tool actions, so
  review that data before sharing. Create a new link to share later changes.
- **Review the workspace:** invite the customer's people as outside
  collaborators (viewer or editor) from workspace settings.
- **Later:** when the customer creates their own Enderis organization, they
  invite the user to their workspace as an editor. The user then opens this
  folder with you again and asks you to copy the demo there. Sign in with a
  separate context (`enderis auth login --context <customer>`), have the user
  pick the customer's workspace, and run
  `enderis import . --acceptance --authored-by coding-agent --context <customer>`
  from this folder. The login makes `<customer>` the current context, so
  switch back with `enderis context use <your context>` (names from
  `enderis context list`) before you work on this workspace again. The copy
  belongs to the customer.

The rest of this section is for the engineers who build the real agent. Do
not explain it to a salesperson; tell them to hand this folder to those
engineers.

When the customer's real agent exists, connect it with the
`enderis-onboard` skill. Every eval belongs to one agent, so import the evals
again for the real agent:

```sh
enderis import evals --agent <real agent> --acceptance --authored-by coding-agent
```

They run unchanged when the real agent reaches the same services through the
same interfaces (`enderis connections list` shows them).
Where it calls the customer's own API, add an interface for that API with
the `enderis-adapter-author` skill.
