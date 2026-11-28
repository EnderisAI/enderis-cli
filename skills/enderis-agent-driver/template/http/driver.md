---
name: my-agent
description: Sends each message to the agent's HTTP inbox and returns what its outbox answers.
command: [python3, driver.py]
files: [driver.md, driver.py]
front_door: harness
app: launched
isolation: exclusive
runtime: python                    # TODO: node or python, the app's language
launch:
  process: [python3, app.py]       # TODO: the command that starts the app, no shell
port_env: PORT                     # TODO: the app's port variable, or a "{port}" argument in launch
ready: /health                     # TODO: a GET path that answers 2xx when ready, or remove it
---
How to start the app: Enderis runs `launch` for each run, in the folder you
onboard (no change to the agent's code or config). For a Docker Compose app,
use launch: {compose: {files: [compose.yaml], service: <name>, port: <port>}}
and remove port_env. The driver reads the app's address from ENDERIS_APP_URL.

For an exported handler, set front_door: production, app: launched and runtime:
node or python. Use launch: {handler: {format: vercel}} for static TS/JS api/
routes, or launch: {handler: {format: lambda, module: app.py, export: handler}}.
Remove ready and port_env.
Enderis supplies the server and tracks background work. Keep only request
mapping or app-specific setup in this driver; never write a handler server here.
Handler execution requires a v3 runner. Current runners advertise v3.

For Slack Events API input, use the slack-events template instead
(`enderis skills show enderis-agent-driver template/slack-events/driver.md`). Declare
events: {platform: slack_events_v1, path: /api/events, signing_secret_env: SLACK_SIGNING_SECRET}.
Remove command and driver.py; Enderis builds, signs and posts the
event, waits for completion and returns no synthetic replies. Declare the
signing secret as a boundary gate, and listen with wake: full.

What the driver maps: each delivery goes to POST /inbox under a chat id made
from the run id and the conversation. Answers come from GET /outbox. A message
with `handoff: true` is an escalation. POST /outbox/ack acknowledges, by message
id, only what Enderis accepted.
This template reads delivery text: listen with wake: text on a channel that has message bodies.
