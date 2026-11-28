---
name: my-agent
description: Starts the app's own CLI for each message and answers its prompts as a user would.
command: [python3, driver.py]
front_door: harness
app: harness
isolation: exclusive
runtime: python
---
Front door: the app's interactive CLI. TODO: name the command a user runs, for
example `python -m cli.main`. The driver runs that same command on a terminal
for each message, so the CLI's own setup and defaults apply.

How a message becomes answers: TODO, for example "the ticker and date come from
the message; every other prompt keeps its default". The reply is what the CLI
prints after the last answer.
This template reads delivery text: listen with wake: text on a channel that has message bodies.

The CLI must be a Python program started with plain `python` (not `python -I`),
so it gets the run's simulated services. `python3` runs the driver; the CLI
command can use the project's own runner, for example `[uv, run, python, -m, cli.main]`.
