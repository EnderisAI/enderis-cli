---
name: my-agent
description: Imports the agent and calls it for each message, in the driver's own process.
command: [python3, driver.py]
front_door: harness
app: harness
isolation: exclusive
runtime: python
---
Why a harness: the repository has no front door a driver can use (no HTTP
server, webhook or chat API). TODO: say what you looked for.

What the driver calls: TODO, for example `my_agent.graph.graph`, invoked with
the conversation so far for each delivery. The reply is the last message.

Interpreter: `python3` must have the agent's dependencies. Otherwise use the
project's own runner, for example `[uv, run, python, driver.py]` or
`[poetry, run, python, driver.py]`. It runs in the agent's folder.
