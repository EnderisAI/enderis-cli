"""Adapter template: a REST API the agent calls with fetch, httpx or requests.

Each `@tool` serves one real route: its method and path, and the reply the
real API sends. `upstream["endpoint"]` is the API's production origin; a run
sends the agent's requests to that origin here instead. Path parameters,
query parameters and a JSON or form body become `call.args`.

List extra bootstrap and auth origins in `upstream["auth_origins"]`
as a space-separated string and serve their routes in this interface.
A client that only checks an extra origin's status can use a `route=("GET", "/")`
tool returning `http_response(200, raw="")`.
An interface cannot set cookies, so report a client that needs a bootstrap cookie as a gap.
"""

from enderis.interface import http_response, interface, tool


@interface(
    service="parts_desk",  # TODO: the `name` in behavior.py
    name="parts_desk-rest",  # TODO: `<service>-<short>`; this is the adapter name
    protocol="http",
    upstream={
        "name": "parts-desk-api",  # TODO: the real API's name
        "url": "https://github.com/harborline/parts-desk-api",  # TODO: its docs or source
        "endpoint": "https://parts.harborline.example",  # TODO: the origin the agent calls
    },
    http_auth=["Authorization"],
)
class PartsDeskRest:
    @tool(
        name="get_part",
        canonical="parts_desk.get_part",
        classification="read",
        route=("GET", "/v1/parts/{part_number}"),  # TODO: the real method and path
        schema={
            "description": "One part by part number.",
            "parameters": {
                "type": "object",
                "properties": {"part_number": {"type": "string"}},
                "required": ["part_number"],
            },
        },
    )
    def get_part(self, call):
        found = call.invoke("parts_desk.get_part", {"part_id": call.args["part_number"]})
        if not found:
            return http_response(404, {"error": found.error.message})
        part = found.result
        return {"part_number": part["id"], "name": part["name"], "stock": part["stock"]}
