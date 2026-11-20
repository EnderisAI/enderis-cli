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

For an exported handler, set front_door: production, app: launched and runtime:
node or python. Use launch: {handler: {format: vercel}} for static TS/JS api/
routes, or launch: {handler: {format: lambda, module: app.py, export: handler}}.
Remove settings: [APP_URL], ready and port_env; read ENDERIS_APP_URL in driver.py.
Enderis supplies the server and tracks background work. Keep only request
mapping or app-specific setup in this driver; never write a handler server here.
Handler execution requires a v3 runner. Current runners advertise v3.

For Slack Events API input, use template/slack-events/driver.md instead. Declare
events: {platform: slack_events_v1, path: /api/events, signing_secret_env: SLACK_SIGNING_SECRET}.
Remove command, settings and driver.py; Enderis builds, signs and posts the
event, waits for completion and returns no synthetic replies. Declare the
signing secret as a boundary gate, and listen with wake: full.

What the driver maps: each delivery goes to POST /inbox under a chat id made
from the run id and the conversation. Answers come from GET /outbox. A message
with `handoff: true` is an escalation. POST /outbox/ack acknowledges, by message
id, only what Enderis accepted.
