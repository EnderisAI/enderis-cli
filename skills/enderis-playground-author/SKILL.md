---
name: enderis-playground-author
description: >-
  Build an Enderis playground: the people, organizations and starting records
  an agent works against in its evals. Use when asked to create a playground,
  model a real business or a team's inbox for evals, or make a second
  playground from an existing one. Carries the rules builders get wrong: never
  invent a fact a source could supply, label simulated data, give synthetic
  worlds history and noise, and audit provenance before writing evals.
---

# Building Enderis playgrounds

Print the playground guide with
`enderis skills show enderis-playground-author playground-authoring.md` and
follow it. It is short and covers sourced and synthetic worlds, source routes
when pages are blocked, the builder-script workflow, the blueprint format, and
second playgrounds. The same text is the MCP resource
`enderis://docs/playground-authoring`.

When a skill this one names is not loaded, run `enderis skills show <skill>`
to print it. Do not read skill files from your home folder.

Read the schemas of the services you seed before you write any row
(`enderis tools schemas <service>... --json`), and build the playground with a
re-runnable script that writes `playgrounds/<name>/blueprint.yaml`. Import it
with `enderis import playgrounds/<name>` and fix every error it reports; if an
error is not clear, run `enderis faq`. Then read the consistency lines the
import returns: fix each "Not fixed" line or record why it stays under
`exceptions:`, and import again. The web app cannot generate or copy a
playground. Use import for every new playground and every big change in this
workflow. The guide opens its blueprint section
with a complete example that imports as it is: start from it.

## Rules builders get wrong

- **Keep one fact in one form.** Import fixes a person's name or email where a
  row mirrors it (a row tied to its person only by an id, such as a driver's
  `customer_id`, is listed, not fixed) and lists dangling ids, handles that
  name no record, and unknown addresses at an org's domain. New and changed rows
  must match the rows already there: their fields, unique values, dates up to
  the playground clock, ids in text, snippets of their bodies, and what other
  text already says. A mismatch you want, such as a phishing sender, goes under
  `exceptions:` with a `record`, an optional `field` and a `reason`. When you
  change a fact, import lists text that still says the old value, often with a
  suggested rewrite; it never rewrites text, so fix them in your file.
- **Never invent a sourced fact.** A product spec, price, policy rule or
  document line comes from a public source, with its URL and the date you
  checked it, or from a transcript or document the user gave you, cited by
  its id and a timestamp, page or section. If no source has it, leave it out
  or mark it unverified.
- **Label simulated data once, not on every record.** Customers, stock, orders
  and capacity cannot come from a public page. Invent them, and say which data
  is simulated in the blueprint's top-level `description`. Records read like
  the real system: never put "simulated" or "demo" in message text, names,
  titles, account names or extra fields.
- **Depth, not a demo.** A synthetic world has weeks of history: threads with
  replies, sent and read mail, past and upcoming events, chat history. A
  business has its staff and dozens of customers, with open and settled work.
  Write each customer's records by hand in `customers.yaml`, as the service
  rows themselves; the build script copies them unchanged. The
  records an eval depends on sit among ordinary noise, and one event shows up
  consistently across services.
- **Give every resident a persona.** A person who holds a direct channel (a
  Slack DM, a WhatsApp chat, a mailbox) is a resident. Give each one an
  `actors:` entry with a library `persona` for how they talk and a
  `description` for who they are. Import warns about each resident without
  one and names the default persona `enderis-everyday@1`.
- **Real-sounding names.** No acme, example, test or foo, for people or
  domains.
- **Audit before evals.** A fresh session that did not build the playground
  checks a sample of sourced facts against their sources, and checks that the
  `description` names the simulated data and no record text says so. Fix what it finds, re-import, then write
  evals.
