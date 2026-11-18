---
name: enderis-adapter-author
description: >-
  Build an Enderis adapter for an API the agent calls that no built-in adapter
  covers, an MCP server or a REST API: read its real tools or routes, write an
  interface over a built-in service that already models the API (such as
  Gmail or Google Calendar over REST), or else a small service and an
  interface under .enderis/services/ from the template; test it, import it
  and connect the boundary. Use when
  `enderis connections list` shows no adapter that fits a boundary, or when
  asked to mock a private or custom MCP server or REST API for Enderis runs.
---

# Building an adapter for one boundary

During a run, an adapter answers the agent's calls to one server, from the
playground's records instead of production. An adapter is two files in
`.enderis/services/<service>/` in the agent repository:

- `behavior.py`, the **service**: the records it holds (seeded from a
  playground) and the operations that read and change them.
- `interfaces/<short>.py`, the **interface**: the server's real tools (an MCP
  server) or routes (a REST API), each mapped onto service operations. Its
  name is the adapter name.

`.enderis/` belongs to Enderis and the agent never loads it, so adding these
files does not change the agent. Never edit the agent's code, config or
scripts.

A REST API the person will use only as a live read needs no adapter: declare
it without `interface:` (the `enderis-onboard` skill, "REST boundaries").

`template/` in this skill folder (installed at
`~/.agents/skills/enderis-adapter-author/template/`) is a complete adapter
that imports as it is: a parts desk service with two operations, an MCP
interface (`interfaces/mcp.py`) with two tools, a REST interface
(`interfaces/rest.py`) with one route, and a tool test file. Start from it,
and keep the interface you need.

## An interface over a built-in service

First run `enderis tools schemas`. When a built-in service there already
models the API (for example `google_workspace` for Gmail and Google
Calendar), do not write a service. Write only the interface, in a folder
named for the built-in, with no `behavior.py`:

```text
.enderis/services/google_workspace/interfaces/gmail_rest.py
.enderis/services/google_workspace/interfaces/calendar_rest.py
```

- `service=` is the built-in's name, and `name=` is `<builtin>-<short>`. Do
  not use a name the built-in already has; import refuses it.
- For a REST client, `protocol="http"` and `upstream["endpoint"]` is the
  origin the client calls. Write one file per origin.
- Take op names and their inputs from `enderis tools schemas <builtin> --json`.
  Each `canonical` must name one of those ops.
- Each file must import on its own: do not import a sibling file.

```python
# gmail_rest.py
from enderis.interface import http_response, interface, tool

@interface(service="google_workspace", name="google_workspace-gmail_rest", protocol="http",
           upstream={"name": "Gmail API v1", "url": "https://developers.google.com/gmail/api",
                     "endpoint": "https://gmail.googleapis.com"},
           http_auth=["Authorization"])
class GmailRest:
    @tool(name="list_messages", canonical="google_workspace.search_emails",
          classification="read", route=("GET", "/gmail/v1/users/{userId}/messages"),
          schema={"parameters": {"type": "object", "properties": {
              "userId": {"type": "string"}, "q": {"type": "string"}}}})
    def list_messages(self, call):
        got = call.invoke("google_workspace.search_emails", {"query": call.args.get("q", "")})
        if not got:
            return http_response(400, {"error": {"code": 400, "message": got.error.message}})
        found = got.result["messages"]
        return {"messages": [{"id": m["id"], "threadId": m["threadId"]} for m in found],
                "resultSizeEstimate": len(found)}
```

```python
# calendar_rest.py
from enderis.interface import http_response, interface, tool

@interface(service="google_workspace", name="google_workspace-calendar_rest", protocol="http",
           upstream={"name": "Google Calendar API v3",
                     "url": "https://developers.google.com/calendar/api",
                     "endpoint": "https://www.googleapis.com"},
           http_auth=["Authorization"])
class CalendarRest:
    @tool(name="list_events", canonical="google_workspace.list_events",
          classification="read", route=("GET", "/calendar/v3/calendars/{calendarId}/events"),
          schema={"parameters": {"type": "object", "properties": {
              "calendarId": {"type": "string"}, "timeMin": {"type": "string"},
              "timeMax": {"type": "string"}}}})
    def list_events(self, call):
        args = {k: call.args[k] for k in ("calendarId", "timeMin", "timeMax") if k in call.args}
        got = call.invoke("google_workspace.list_events", args)
        if not got:
            return http_response(404, {"error": {"code": 404, "message": got.error.message}})
        return {"items": got.result["events"]}

    @tool(name="insert_event", canonical="google_workspace.create_event",
          classification="write", route=("POST", "/calendar/v3/calendars/{calendarId}/events"),
          schema={"parameters": {"type": "object", "properties": {
              "calendarId": {"type": "string"}, "summary": {"type": "string"},
              "start": {"type": "object"}, "end": {"type": "object"}}}})
    def insert_event(self, call):
        start, end = call.args["start"], call.args["end"]
        args = {"calendarId": call.args["calendarId"], "summary": call.args.get("summary", ""),
                "start": start["dateTime"], "end": end["dateTime"]}
        if "timeZone" in start:
            args["timeZone"] = start["timeZone"]
        got = call.invoke("google_workspace.create_event", args)
        if not got:
            return http_response(400, {"error": {"code": 400, "message": got.error.message}})
        return got.result
```

Skip the service steps. Before importing, test each tool that writes: one
case that calls it by its `@tool` name, with the arguments the route passes
(path, query and body together), and checks the built-in's records. Most
`google_workspace` operations need a principal, so the seed names one:

```yaml
# .enderis/tests/tools/calendar_rest.yaml
services: [google_workspace]
seed:
  people:
    - {key: ana, name: Ana, emails: [ana@acme.example]}
  principal: ana
cases:
  - name: insert_event keeps the time zone
    calls:
      - tool: insert_event
        args:
          calendarId: primary
          summary: Standup
          start: {dateTime: "2026-03-03T09:00:00", timeZone: Europe/Berlin}
          end: {dateTime: "2026-03-03T09:15:00", timeZone: Europe/Berlin}
    state:
      google_workspace: {events: [{summary: Standup, timeZone: Europe/Berlin}]}
```

```sh
(cd .enderis && enderis tools test)
```

The test runs over the workspace's latest built-in and stores nothing. A
reply with status 400 or more is the call's error (`HTTP <status>: <body>`).
Fix the interface until the case passes. Then import the folder and onboard
again:

```sh
enderis import .enderis/services/google_workspace
enderis onboard . --json
```

Import prints the interfaces it stored over the built-in. Onboarding gives
each REST boundary the interface whose `upstream["endpoint"]` has the
boundary's origin. If more than one interface has that origin, onboarding
asks for `interface:` in the boundary's declaration: name yours there. This
works for repository-agent runs (`enderis run`, `enderis serve`).

Google clients: a recent `google-api-python-client` uses the discovery
documents bundled with it, so it reads nothing from the network to build a
client. Its token refresh goes to `oauth2.googleapis.com`, which a run does
not mock, so give the run a static test token with a far-future expiry.

## 1. Read the real surface

Find the boundary id with `enderis connections list` (the word before
`(mcp)` or `(http)`). The interface must present what the agent calls with
the exact names and inputs. Get them in this order:

1. **Read the code first.** The tool names the agent filters or calls, the
   routes and request bodies it sends, and the server's own definitions in
   its installed package (`node_modules/<package>`, the Python
   `site-packages/<package>`, or the published package source). For each tool
   write down its name, description and input schema; for each route its
   method, path, inputs and reply.
2. **Probe an MCP server** only if the code does not show the tools, and only
   after you ask the person and they say yes. The probe starts the server with
   their configuration, which may use their credentials or contact the real
   service. Name the server when you ask. With no answer, or when the request
   says to take defaults, do not probe: use what the code shows.

   ```sh
   enderis inspect . --probe-tools --allow-probe <source id> --json
   ```

   `<source id>` is the `source_id` of that server's entry in
   `production_tool_sources`, usually the boundary id (`enderis inspect .
   --json` shows it). The probe lists tools only; it calls none. The entry's
   `surface_status` becomes `probed`, and `descriptor.tools` holds each tool's
   `name`, `description` and `input_schema`.

3. **Read the server's published definition** when the code does not show
   the tools and you may not probe (no answer, or the request says to take
   defaults). This is the usual case for a remote MCP server that the agent
   reaches by URL, with no package in the repository. Find the server's
   source repository or reference docs (for a vendor's hosted server, its
   open-source server or its tool reference page) and copy each tool's name,
   description and input schema from there. Do not ask the person for a
   capture or a credential, and do not stop. Pin what you read: put the exact
   source URL, with a commit or version where one exists, in the interface's
   `upstream["url"]`, and tell the person in one line that the tools come
   from published docs, not a capture.

Stop only if none of the three gives the names and inputs the agent needs:
then the adapter cannot be built. Report it (the `enderis-onboard` skill then
names the blocker).

**Which tools to keep.** When the agent calls named tools or routes, keep
those. When it hands the model the server's whole tool list, keep the tools
its prompt and main job need. Copy each one whole: name, description and
input schema. Add more later when an eval needs them.

## 2. Write the service and the interface

Copy the template into the repository:

```text
.enderis/services/<service>/behavior.py             # from template/behavior.py
.enderis/services/<service>/interfaces/mcp.py       # from template/interfaces/mcp.py, for an MCP server
.enderis/services/<service>/interfaces/rest.py      # from template/interfaces/rest.py, for a REST API
.enderis/tests/tools/<service>.yaml                 # from template/tests/tools/parts_desk.yaml
```

Then change the parts marked TODO:

- **Service name:** lower case with underscores, named for the product (for
  example `harbor_inventory`). It must not be a built-in service name; run
  `enderis tools schemas` to list those. If a built-in already models the
  API, write only an interface over it ("An interface over a built-in
  service"). The folder name is the same.
- **Collections:** the records the tools read and change, in `state=`, with a
  row schema for each in `seed_authoring`. The playground seeds them.
- **Operations:** one `@op` per thing the tools do (look up, list, create,
  change). Raise `ctx.domain("...")` for a refusal the real system would give
  (unknown id, not enough stock) and `ctx.bad_arguments("...")` for a bad
  input. Use `ctx.new_id(prefix)` and `ctx.tick()` for ids and order, never
  the clock or random numbers. Keep no state on `self`.
- **Interface:** `service=` is the service name, and `name=` is
  `<service>-<short>`, for example `harbor_inventory-mcp`; that is the adapter
  name. `upstream` names the real server (`name` or `package`, plus a `url`
  where it is defined).
- **Each tool** reads `call.args`, calls `call.invoke("<service>.<op>", {...})`
  and returns what the real server returns. `call.invoke` never raises on a
  refusal: check `if not result:` and return the server's error shape with
  `result.error.message`. `classification` is `read` or `write`; `canonical`
  names the main operation the tool calls. Required inputs are checked before
  the method runs.

### An MCP server

One `@tool` per real tool, with its exact `name`, its `description` and its
input schema under `schema["parameters"]`:

```python
from enderis.interface import interface, tool

@interface(service="parts_desk", name="parts_desk-mcp",
           upstream={"name": "parts-desk-mcp",
                     "url": "https://github.com/harborline/parts-desk-mcp"})
class PartsDeskMcp:
    @tool(name="lookup_part", canonical="parts_desk.get_part", classification="read",
          annotations={"readOnlyHint": True},
          schema={"description": "Look up a part by part number.",
                  "parameters": {"type": "object",
                                 "properties": {"part_number": {"type": "string"}},
                                 "required": ["part_number"]}})
    def lookup_part(self, call):
        found = call.invoke("parts_desk.get_part", {"part_id": call.args["part_number"]})
        if not found:
            return {"error": found.error.message}
        return {"part_number": found.result["id"], "stock": found.result["stock"]}
```

To preserve an upstream MCP result with several content blocks, an error flag,
structured data or metadata, return `mcp_response(content, is_error=...,
structured_content=..., meta=...)` from `enderis.interface`. Optional arguments
left as `None` stay absent. Plain return values keep their usual serialization.

For upstream-specific input validation, an MCP interface may declare
`input_validator=fn`. It receives `(tool_spec, args)` and replaces the default
input checks. Return `None` for valid input, or `mcp_response(...)` for the real
server's rejection before any command runs. It can normalize its private copy
of the arguments. Use the pinned server's rules, not invented error strings.

When you have a pinned `tools/list` capture, prefer
`@tool(mcp_tool=captured_tool, canonical="service.op", classification="read")`.
This copies the full real descriptor, including optional metadata and omitted
fields. Do not supply a different name, schema or annotations alongside it.

### A REST API

Use this for a client built on `fetch`, `node:http` (axios, got), `httpx`,
`requests`, `urllib`, `aiohttp`, a GraphQL client or a vendor SDK. The interface has `protocol="http"`, and
`upstream["endpoint"]` is the origin the client calls (scheme, host and port
only). Each tool serves one route; path parameters, query parameters and a
JSON or form body become `call.args`:

```python
from enderis.interface import http_response, interface, tool

@interface(service="parts_desk", name="parts_desk-rest", protocol="http",
           upstream={"name": "parts-desk-api",
                     "url": "https://github.com/harborline/parts-desk-api",
                     "endpoint": "https://parts.harborline.example"},
           http_auth=["Authorization"])
class PartsDeskRest:
    @tool(name="get_part", canonical="parts_desk.get_part", classification="read",
          route=("GET", "/v1/parts/{part_number}"),
          schema={"description": "One part by part number.",
                  "parameters": {"type": "object",
                                 "properties": {"part_number": {"type": "string"}},
                                 "required": ["part_number"]}})
    def get_part(self, call):
        found = call.invoke("parts_desk.get_part", {"part_id": call.args["part_number"]})
        if not found:
            return http_response(404, {"error": found.error.message})
        return {"part_number": found.result["id"], "stock": found.result["stock"]}
```

A returned value is a 200 JSON reply; `http_response(status, body)` sends
another status. A GraphQL API is one `POST` route (for example `/graphql`)
whose tool reads `call.args["query"]` and `call.args["variables"]`. Full
route rules: https://enderis.ai/docs/cli/import#custom-tools.

## 3. Test the service

Edit the test file: a seed with a few rows, and one case per operation,
including one refusal. Run it from `.enderis/`, where the CLI finds
`services/` and `tests/tools/`:

```sh
(cd .enderis && enderis tools test)
```

Each case prints `pass` or `FAIL` with the first mismatch. Fix the service
until every case passes. For your own service the test calls its operations
(`<service>.<op>`), not the interface's tools; the first chat tests the
tools. Only an interface over a built-in service is tested by tool name.

## 4. Import and connect

From the repository root:

```sh
enderis import .enderis/services/<service>
```

Import prints `services: 1 created, 0 unchanged, 0 failed` (or `1 unchanged`).
An error names the file and the problem; fix it and import again. A
`behavior.py` with a built-in name is refused: rename the service, or delete
`behavior.py` and keep only an interface over the built-in ("An interface
over a built-in service").

- **An MCP boundary:**

  ```sh
  enderis connections set <boundary> --adapter <service>-<short>
  ```

  It prints `<boundary> (mcp): mocked with <service>-<short> (revision N)`.
- **A REST boundary:** declare it in `.enderis/boundaries.md` with
  `transport: http`, `url:` the same origin as `upstream["endpoint"]`, and
  `interface: <service>-<short>`, then run `enderis onboard . --json`.
  Onboarding assigns the interface to the boundary. The `enderis-onboard`
  skill has the full declaration format ("Declare a REST API boundary").

After any change to a file in `.enderis/services/<service>/`, import again.
A new import makes a new adapter revision, and a connection stays on the
revision it was set to: run the same `connections set` command again (for a
REST boundary, onboard again). A run uses the interface code of that
revision. The operations and records come from the service version that the
playground pinned when it was imported, so after a change to `behavior.py`,
import the playground and its evals again too.

## 5. Prove it

**When the `enderis-onboard` skill sent you here,** stop after step 4 and go
back to it. Its first playground and chat are the proof; do not build a
playground here.

**On its own,** prove the adapter once every boundary of the agent has a
connection (`enderis connections list` shows none that still needs one), with
a playground that seeds the service. Send one message that needs the tool:

```sh
echo "<a message that needs the tool>" | enderis chat --playground <playground>
```

The CLI starts the agent, sends the message, prints the reply after
`agent>`, and ends with the run link. Check that the reply carries data from
the playground's seed. On the run page, the call shows as a step named for
the service operation it reached (`<service>.<op>`).

| Problem | Action |
| --- | --- |
| `needs_adapter: <boundary>` | Some boundary has no connection. Run `enderis connections list`. |
| The agent says the tool does not exist, or calls a name the interface lacks | A tool name differs from the real one. Fix `name=`, import, connect again, try again. |
| The tool answers `unknown <thing>` | The playground has no matching row. Add it to the playground and import it again. |
| `Internal error` with an exception | A bug in `behavior.py` or the interface. Fix it, test, import, try again. |

## Rules

- Never change the agent's code, config or scripts. Write only under
  `.enderis/`.
- Never probe a server without the person's yes.
- Use the real tool names, routes and input schemas. Never rename a tool to
  suit the service.
- Never default a boundary to `--passthrough`.
- If an `enderis` command fails and the fix is not clear, run `enderis faq`
  before you try again.
- Never commit or push unless asked.
