# Build a playground with your coding agent

A playground is the world your agent works in during an eval: the people, the
organizations, and the starting records of every service the agent can use (a
mailbox, a calendar, a store catalog, an insurer's policies and claims). Every
eval runs against it, so an eval is only as real as its playground.

Enderis does not generate a playground from nothing. A real world needs real
facts, and real facts need research with a browser and a shell. You build the
first playground for a use case here, with research and a script, and import it
with `enderis import`. Later playgrounds can start from that one.

## Two kinds of world

- **Sourced world**: a real business, such as a retailer or an insurer. Its
  products, prices, policies and documents come from public sources.
- **Synthetic world**: a team or inbox with no public record, such as a chief of
  staff's mail, calendar and chat. Its realism comes from depth: history, noise
  and connections between services.

Most sourced worlds also hold simulated operations: customers, stock, orders,
appointments. Nobody can read those from a public page, so you invent them, and
you label them as simulated.

## Workflow

1. **Ask the user first.** Find the services the agent uses: for a hosted
   agent, the `interfaces:` of its `agents/<name>.md`; for a repository
   agent, the services of the adapters `enderis connections list` shows;
   over MCP, `get_agent` (or `list_agents`, and ask which one). Then ask the user only what you cannot
   find yourself, in one message:
   - which business, and which part of it, the agent serves: the company,
     and the store, branch, product line or team;
   - any call transcripts or documents the user has from the business;
   - what the agent does there, for whom, and the situations they want to test;
   - the public sources that hold the facts (website, policy documents,
     product pages), and any source you must not use;
   - anything private the playground should reflect that no public page has,
     such as internal policies or team names. Label what they give you as
     provided by the user, not sourced.

   Skip a question the request already answers. Do not start research until
   you have the answers. When the request says to take the defaults, state
   the answers you assume in one message and go on without waiting.
2. **Read the service schemas.** Run
   `enderis tools schemas <service>... --json` for the services your agent
   uses (over MCP: `get_service_schemas { services: [...] }`, the same data).
   It returns each service's collections and key fields, the row schema a seed
   must follow (`seed_authoring`), the fields that name a person
   (`person_fields`), the channels people can listen on (`channels`), and
   each tool with its arguments (`tools`). Write no row before you read this.
   Read the `description` on each field: inside object fields (for example a
   commerce retailer's `policies`) it names the keys the service reads. Some
   object fields refuse a key they do not read, such as commerce
   `policies.refunds`; elsewhere an unlisted key is ignored, so a misspelled
   or invented key fails silently. Put a rule the service cannot express in a
   policy document instead of inventing a key.
   **When two services fit,** compare their tools with what your agent
   actually calls, and prefer the one a starter for a similar business uses.
   For a store, `commerce` holds a real retailer's catalog, stock, promotions,
   appointments, receipts and refunds; `retail` is the fixed tau2-bench
   benchmark world of orders, exchanges and returns.
3. **Study a stored playground that uses the same services.** Use it for its
   structure, never its content. First import a starter agent that uses the
   service from **Agents** in the web app, for example
   `retail-rei-assistant` for `commerce`. Then either:
   - over MCP, call `get_playground { agent_id }` for the starter: it shows
     every collection's fields and one sample row, and `get_records` returns
     more rows; or
   - with a signed-in CLI (`enderis auth login` first), in a new empty folder
     run `git init`, `mkdir evals` and
     `enderis pull --agent <starter agent name>`. Pull writes the starter's
     playground to `playgrounds/<name>/blueprint.yaml`, its evals beside it,
     and the agent itself to `agents/<name>.md`.
4. **Research, and save what you find.** Save each source pass as a dated data
   file, for example `research/catalog_2026-09-10.json`. Each fact carries the
   URL it came from and the date you checked it.
5. **Write a builder script.** The script reads the snapshot files and writes
   `playgrounds/<name>/blueprint.yaml`. It must run again from scratch with the
   same result. A new research pass is then one new data file and a re-run, and
   the diff is easy to review. Keep stable ids, so a re-run does not move
   existing records. Simulated customers are not research: write their
   records by hand in `playgrounds/<name>/customers.yaml`, as the service
   rows themselves, and have the script copy them unchanged (see "Stories,
   not templates").
6. **Import.** Run `enderis import playgrounds/<name>`. Import checks every row
   against the service, every person reference against `people`, every email
   against its org's domains, and every cross-record reference. Fix each error
   in the script, re-run it, and import again until the import is clean.
   Then read the consistency lines the import returns (warnings from
   `enderis import`, `consistency` in an MCP result; see
   [Consistency](#consistency)). Fix each "Not fixed" line, or record why it
   stays with an `exceptions:` entry, and import again.
7. **Audit with fresh eyes.** Start a separate agent session that did not
   build the playground and give it only the blueprint, the research
   snapshots and a browser, not the builder script or your notes. Ask it to
   check every sourced fact in the blueprint against the snapshot it came
   from, re-open a sample of sources live, confirm that the `description`
   names the simulated data, that no record text, name or title says
   "simulated", and that no fact is invented where a source could supply it, and judge the playground against the [quality
   bar](#quality-bar). Fix what it finds, then re-import.
8. **Write evals.** Follow the `enderis-eval-author` skill (over MCP, the
   `enderis://docs/authoring-brief` resource) and write evals against the
   imported playground.

## The blueprint

This is a complete blueprint. It imports as it is, so you can copy it into
`playgrounds/northwind-ops/blueprint.yaml` to start.

```yaml
name: northwind-ops                 # the playground name; matches its folder
description: >-
  Northwind's operations inbox. All people, mail and dates are simulated.
identity_namespace: northwind/ops
epoch: "2026-06-17T09:00:00-07:00"  # "now" for every run on this playground

orgs:
  - {key: northwind, name: Northwind Logistics, kind: internal, domains: [northwind.io]}
  - {key: halcyon, name: Halcyon Foods, kind: customer, domains: [halcyonfoods.com]}

people:
  - key: assistant
    kind: agent
    name: Rhea Malik
    emails: [rhea@northwind.io]
    handles: {slack: U_rhea}
    orgs: [northwind]
  - {key: tomas, name: Tomás Ferreira, emails: [tomas@northwind.io], handles: {slack: U_tomas}, orgs: [northwind]}
  - {key: june, name: June Okafor, emails: [june.okafor@halcyonfoods.com], orgs: [halcyon]}

actors:
  - person: june
    description: Halcyon's supply manager. Writes when a delivery slips.
    listens: [google_workspace:mailbox:june]

services:
  google_workspace:
    labels:
      - {id: CATEGORY_UPDATES, name: CATEGORY_UPDATES, type: system}
    messages:
      - id: m-halcyon-1
        threadId: t-halcyon-dock
        from: june.okafor@halcyonfoods.com
        to: [rhea@northwind.io]
        subject: Dock 4 closed next week
        body: Our dock 4 is closed for repairs from Monday the 22nd. Can you route to dock 2?
        internalDate: 1781543520000       # Mon 2026-06-15 10:12, two days before the epoch
        labelIds: [INBOX, CATEGORY_UPDATES]
      - id: m-halcyon-2
        threadId: t-halcyon-dock
        inReplyTo: m-halcyon-1
        from: rhea@northwind.io
        to: [june.okafor@halcyonfoods.com]
        subject: "Re: Dock 4 closed next week"
        body: Noted. I'll update the route plan and confirm by Friday.
        internalDate: 1781559600000       # Mon 2026-06-15 14:40
        labelIds: [SENT]
```

- `orgs` and `people` are the cast. Each person has a stable `key`. Records
  refer to people by key, email or handle, in the fields `person_fields` lists,
  and import refuses a record that names someone not in `people`. Each email must use a domain of the person's org.
  Mark your own team's org `kind: internal`.
- The `agent` person is the agent under test.
- `actors` are the people a simulated person can play in an eval, with the
  channels they listen on by default. A channel is
  `<service>:<kind>:<key>`; the key is a person or the catalog's channel/record id: `google_workspace:mailbox:june` is June's mailbox,
  and `chat:direct:assistant` is a direct chat with the agent whose key is
  `assistant`.
- `services` holds each service's starting records, in the shape the
  service schemas give.
- `epoch` sets the playground clock. Date every record relative to it.
- `description` is a note for the people who build and review the
  playground. Say there which data is simulated. Agents and evals do not see it.
- Gmail creates only its basic system labels (`INBOX`, `SENT`, `DRAFT`,
  `UNREAD`, `STARRED`, `IMPORTANT`, `TRASH`, `SPAM`). Declare any other label a
  message uses, such as `CATEGORY_UPDATES`, under `labels`, or import fails.

## Consistency

Every save checks the world against itself. A row about a person whose name or
email differs from the people list (a Slack user's `real_name`, a customer
record) is set to match it, and the response lists each fix. A dangling id and
an address at an org's domain that no person has are listed, not changed. Rows
a save adds or changes are compared with the rows already there: a reused
sequence number, a missing field, a message time after the playground
clock and an id in text that names no record are listed; a snippet follows its
body. Keep
an inconsistency on purpose with an `exceptions:` entry and a reason:

```yaml
exceptions:
  - record: google_workspace.messages/m_phish   # service.collection/key
    field: from                                 # optional; without it, the whole record
    reason: Sent from a lookalike domain; the mismatch is the trap.
```

An eval's `playground.yaml` can carry its own `exceptions:` beside `blueprint:`.

When an import changes a fact (a name, an amount, a status), the response also
lists text in the playground that still says the old value; re-pinning an eval
lists the same for that eval. A text check then reads related text against the changed records, and new
text against what the playground says about the records it names. It never
changes text: each line names the field and the problem, often with a suggested
rewrite, so fix your file and import again. If the check cannot run, the import
goes on and one line says so.

## Quality bar

Importing cleanly is the start, not the finish. Expect a good sourced
playground to take hours, not minutes.

- **Start from the decisions.** List the decisions the agent must make: which
  pack fits a 19" torso, which sleeping bag for 25°F, is this return allowed,
  is this claim covered. Source the facts those decisions turn on from spec
  sheets, manufacturer pages and policy wordings, not only listing tiles.
  Store numbers as numbers (`max_load_lb: 35`), not inside prose.
- **Variants match the facts.** If a product lists sizes (including wide,
  half and tall sizes) or colors, seed a variant for each. Never list a size
  that has no variant.
- **Give the agent something to advise from.** Add short guidance documents
  (how to fit a pack, what a temperature rating means, how an excess works),
  not only policy pages. Strip page chrome, keep documents to this playground
  (only its stores, only its products), and paraphrase long pages into
  faithful summaries that keep their source.
- **Seed real edge cases.** A recall, a promotion that is active and one that
  has expired, an item sold out everywhere, stock that differs between
  stores, low stock, stale inventory at one location, a prior-generation
  model, a member versus non-member difference, a customer with several
  policies. In an inbox: a phishing lookalike, a double-booked meeting, a
  thread that changed its mind. Identical records everywhere make evals that
  guessing can pass.
- **Simulated operations agree with the rest.** Receipts only for items the
  location carries, past purchases at past prices, history that matches the
  catalog and the dates.
- **The agent can read every fact it needs.** Put each such fact in a field
  the service's tools return. Where a service has custom fields, use a
  standard field or declare the custom one (a HubSpot custom property needs
  a `properties` row). A HubSpot read returns only email, name and dates
  unless the agent asks for properties by name, so the agent's prompt must
  name them. In the first chat, ask about one record and check that the
  agent reads the fact.
- **Enough breadth.** Enough categories that ordinary questions can be
  answered, and at least one case that needs a safety handoff.

## Sourced worlds

- **Use public sources, and the material the user gives you.** Never work
  around a login, a paywall or a bot block. Call transcripts and documents
  from the user are sources too: give each one an id (for example `T1`, `D1`)
  and cite the id with a timestamp, page or section. Keep them in the user's
  repository, not in the playground, unless the agent must read them.
- **Find another route when a page is blocked.** Category and listing pages
  often work when product pages do not. Page source often holds JSON-LD
  product data. Sitemaps list the pages that exist. Manufacturer sites carry
  specifications. Search snippets fill small gaps. Policy documents are often
  PDFs. A real browser in new headless mode often loads pages that a plain
  fetch cannot.
- **Never invent a fact a source could supply.** If you cannot find it, leave
  it out, or put it in a separate field the agent is told not to quote. Never
  mix unverified values into the verified specs. A guessed price, rating or
  policy rule makes every eval that touches it wrong.
- **Trust the business's own page first.** Where sources disagree, the page
  the business publishes for that exact product wins, then the manufacturer,
  then everyone else. Reviews and resale listings can fill a gap but never
  overrule either. Check that a manufacturer page is for the same model year.
- **Do not seed a rule the service cannot enforce.** If a promotion has a
  condition the schema cannot express (buy all three together) or a price
  differs by customer type, put the rule in a document and leave the record
  out, rather than seeding a record that gives the wrong answer.
- **Store the source on the record.** Commerce products take `source_url`,
  `source_checked_at` and `model_status` (for example `source_snapshot`,
  `discontinued`, `prior_generation`). Commerce documents take `source_url`,
  `source_checked_at` and `source_status` (for example `reviewed_snapshot`, or
  an unverified status). Document library rows have no source field: put the
  document's own code in its `id` and its date in `prepared`, and keep the URL
  and the date you checked it in your research snapshot.
- **Keep text faithful.** Copy document text page by page, in reading order,
  with headings, lists and tables intact. Paraphrase product facts briefly; do
  not copy reviews or marketing.
- **Label simulated operations once.** Customers, stock, prices used for the
  simulation, orders and service capacity are simulated. Say so in the
  blueprint's `description`, for the people who review it. Records read like
  the real system: no "simulated" or "demo" in message text, names, titles,
  account names or extra fields, and the business's own accounts carry its
  name.
- **Operations at real scale.** A working business has staff and dozens of
  customers. Seed the people who do the work (owner, office, technicians or
  clerks) with their calendars or queues; weeks of past and upcoming work,
  with open capacity; open and settled estimates, deals or tickets; paid,
  open and overdue invoices; and noise (supplier mail, newsletters, spam).
  The agent's own past replies do the job: they answer, book and quote, not
  only "please call". Give the agent what it needs to act: availability, the
  prices it may quote, and the records it must update.
- **Stories, not templates.** Write each simulated customer's records by hand
  in `customers.yaml`: one entry per customer holding the actual rows for
  each service (their messages on the channel they chose with the replies,
  their visits, invoices and deals), each with its own text, amounts and
  times. The script copies these rows unchanged; it never makes a row from a
  pattern (one message and a reply per customer, a technician picked by turn,
  every job two hours). Customers differ: one only asked a question, another
  has three jobs over a year, a thread goes back and forth before a booking.
  Dates follow the story: an invoice comes after its visit, a night
  emergency is handled that night. Check: put five customers side by side.
  If their records have the same shape, rewrite them.

## Synthetic worlds

- **A believable cast.** Your team, plus outside contacts: customers, vendors,
  investors, recruiters, a newsletter or two. Real-sounding names and domains.
  No placeholders such as acme, example, test or foo.
- **Weeks of history.** Mail threads with replies, sent mail as well as
  received, read and unread, starred and archived. Past and upcoming calendar
  events, including regular one-to-ones. Chat history in several channels,
  with threads.
- **Noise around the signal.** Most of a real inbox needs no action:
  newsletters, receipts, automated notices, settled threads. The records an
  eval depends on must sit among them, not alone.
- **Cross-references.** One event shows up in several services: an outage is
  in mail, in chat and on the calendar, and the names, times and numbers
  agree.
- **Dates on everything,** relative to the epoch, and in order inside each
  thread.

## A second playground

Get the source playground into your repository. `enderis pull` only refreshes
playgrounds already in the repository, or adds the ones the agent's
acceptance-set evals need. It runs from the root of a git repository and needs
an agent (`--agent`, or the one agent in `agents/`). Copy the folder to
`playgrounds/<new-name>/`, set `name` to the same new name (import warns when
the folder name and `name` differ) and a new `identity_namespace`, edit the
copy, and run `enderis import`.
