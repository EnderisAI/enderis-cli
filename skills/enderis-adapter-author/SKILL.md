---
name: enderis-adapter-author
description: >-
  Build an Enderis adapter for an API the agent calls that no built-in adapter
  covers, an MCP server or a REST API: read its real tools or routes, write a
  small service and an interface under .enderis/services/ from the template,
  test it, import it and connect the boundary. Use when
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
  `enderis tools schemas` to list those. The folder name is the same.
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
until every case passes. The test calls the service's operations
(`<service>.<op>`), not the interface's tools; the first chat tests the
tools.

## 4. Import and connect

From the repository root:

```sh
enderis import .enderis/services/<service>
```

Import prints `services: 1 created, 0 unchanged, 0 failed` (or `1 unchanged`).
An error names the file and the problem; fix it and import again. A built-in
name is refused: rename the service.

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
