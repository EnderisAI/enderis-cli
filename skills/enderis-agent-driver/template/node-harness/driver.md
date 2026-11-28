---
name: my-agent
description: Imports the agent and calls it for each message, in the driver's own process.
command: [node, driver.mjs]
front_door: harness
app: harness
isolation: exclusive
runtime: node
---
Why a harness: no front door can be launched or driven. TODO: name the front
door this stands in for, if any (full-screen terminal UI, console script or
unsupported serverless platform), and keep its prompt, tools, model and settings.

What the driver calls: TODO, for example the `agent` exported by
`src/agent.js`, given the conversation so far for each delivery.
This template reads delivery text: listen with wake: text on a channel that has message bodies.

Toolchain: the repository's own `node`, started as `node` so Enderis loads
`@enderis/driver` first. A TypeScript agent needs its compiled output, or a
loader the repository already has (`node --import tsx driver.mjs`).
