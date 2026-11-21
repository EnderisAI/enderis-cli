---
name: my-agent
description: Imports the agent and calls it for each message, in the driver's own process.
command: [python3, driver.py]
front_door: harness
app: harness
isolation: exclusive
runtime: python
---
Why a harness: no front door can be launched or driven. TODO: name the front
door this stands in for, if any (terminal CLI, console script or unsupported
serverless platform), and keep its prompt, tools, model and settings.

What the driver calls: TODO, for example `my_agent.graph.graph`, invoked with
the conversation so far for each delivery. The reply is the last message.
This template reads delivery text: listen with wake: text on a channel that has message bodies.

Interpreter: `python3` must have the agent's dependencies. Otherwise use the
project's own runner, for example `[uv, run, python, driver.py]` or
`[poetry, run, python, driver.py]`. It runs in the agent's folder.
