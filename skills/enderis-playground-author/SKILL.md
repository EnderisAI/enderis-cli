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

Read the MCP resource `enderis://docs/playground-authoring` and follow it. It
is short and covers sourced and synthetic worlds, source routes when pages are
blocked, the builder-script workflow, the blueprint format, and second
playgrounds. Web version: https://enderis.ai/docs/evals/build-a-playground.

Call `get_service_schemas` before you write any row, and build the playground
with a re-runnable script that writes `playgrounds/<name>/blueprint.yaml`.
Import it with `enderis import playgrounds/<name>` and fix every error it
reports; if an error is not clear, run `enderis faq`. The resource opens its
blueprint section with a complete example that imports as it is: start from
it.

## Rules builders get wrong

- **Never invent a sourced fact.** A product spec, price, policy rule or
  document line comes from a public source, with its URL and the date you
  checked it, or from a transcript or document the user gave you, cited by
  its id and a timestamp, page or section. If no source has it, leave it out
  or mark it unverified.
- **Label simulated data.** Customers, stock, orders and capacity cannot come
  from a public page. Invent them, and say they are simulated where the
  service has a place for it, and in the blueprint's top-level `description`.
- **Depth, not a demo.** A synthetic world has weeks of history: threads with
  replies, sent and read mail, past and upcoming events, chat history. The
  records an eval depends on sit among ordinary noise, and one event shows up
  consistently across services.
- **Real-sounding names.** No acme, example, test or foo, for people or
  domains.
- **Audit before evals.** A fresh session that did not build the playground
  checks a sample of sourced facts against their sources, and checks that
  simulated records are labelled. Fix what it finds, re-import, then write
  evals.
