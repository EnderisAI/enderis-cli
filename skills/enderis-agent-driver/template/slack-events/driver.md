---
name: my-slack-agent
description: Delivers Slack Events API input through Enderis's built-in poster.
front_door: production
app: launched
isolation: exclusive
runtime: node
launch: {handler: {format: vercel}}
events:
  platform: slack_events_v1
  path: /api/events
  signing_secret_env: SLACK_SIGNING_SECRET
---
Use the app's actual event path. For Next.js or another server, replace launch
with its own process command; for Lambda, use its module and export.

Declare SLACK_SIGNING_SECRET as a secret gate on exactly one simulated boundary in
.enderis/boundaries.md. Use wake: full for each listened Slack mention, DM or
assistant channel. Seed one Slack team and a bot user matching the eval
principal's single Slack handle. Enderis supplies the app and event ids.

No driver code or command is needed. Enderis signs and posts the event, waits
for registered background work, and adds no synthetic replies. A server also
uses bounded settle. This poster has no custom install or OAuth setup hook.
