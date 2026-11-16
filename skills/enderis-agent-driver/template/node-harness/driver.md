---
name: my-agent
description: Imports the agent and calls it for each message, in the driver's own process.
command: [node, driver.mjs]
front_door: harness
app: harness
isolation: exclusive
runtime: node
---
Why a harness: the repository has no front door a driver can use (no HTTP
server, chat route or webhook). TODO: say what you looked for.

What the driver calls: TODO, for example the `agent` exported by
`src/agent.js`, given the conversation so far for each delivery.

Toolchain: the repository's own `node`, started as `node` so Enderis loads
`@enderis/driver` first. A TypeScript agent needs its compiled output, or a
loader the repository already has (`node --import tsx driver.mjs`).
