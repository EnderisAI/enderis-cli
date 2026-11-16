---
name: my-agent
description: Sends each message to the agent's HTTP inbox and returns what its outbox answers.
command: [python3, driver.py]
settings: [APP_URL]
files: [driver.md, driver.py]
front_door: harness
app: attached
isolation: exclusive
---
How to start the app: `docker compose up` from the agent repository (no change
to the agent's code or config). It listens on APP_URL.

What the driver maps: each delivery goes to POST /inbox under a chat id made
from the run id and the conversation. Answers come from GET /outbox. A message
with `handoff: true` is an escalation. POST /outbox/ack acknowledges, by message
id, only what Enderis accepted.
