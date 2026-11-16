"""Adapter template: the MCP tools the agent sees, mapped onto the service.

Each `@tool` copies one real tool of the server: its exact name, description
and input schema, from `enderis inspect --probe-tools` or from the code. The
method maps the arguments onto a service operation with `call.invoke` and
shapes the reply the way the real server does. Tools the agent never calls can
be left out.
"""

from enderis.interface import interface, tool


@interface(
    service="parts_desk",  # TODO: the `name` in behavior.py
    name="parts_desk-mcp",  # TODO: `<service>-<short>`; this is the adapter name
    upstream={
        "name": "parts-desk-mcp",  # TODO: the real server's package or name
        "url": "https://github.com/harborline/parts-desk-mcp",  # TODO: where the server is defined
    },
)
class PartsDeskMcp:
    @tool(
        name="lookup_part",  # TODO: the real tool name, exactly
        canonical="parts_desk.get_part",
        classification="read",
        annotations={"readOnlyHint": True},
        schema={
            "description": "Look up a part by part number. Returns name, stock and bin.",
            "parameters": {
                "type": "object",
                "properties": {"part_number": {"type": "string", "description": "e.g. HB-1042"}},
                "required": ["part_number"],
            },
        },
    )
    def lookup_part(self, call):
        found = call.invoke("parts_desk.get_part", {"part_id": call.args["part_number"]})
        if not found:
            return {"error": found.error.message}
        part = found.result
        return {
            "part_number": part["id"],
            "name": part["name"],
            "stock": part["stock"],
            "bin": part.get("bin"),
        }

    @tool(
        name="reserve_part",
        canonical="parts_desk.reserve_part",
        classification="write",
        schema={
            "description": "Reserve stock of a part for a technician.",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_number": {"type": "string"},
                    "quantity": {"type": "integer", "minimum": 1},
                    "technician": {"type": "string"},
                },
                "required": ["part_number", "quantity", "technician"],
            },
        },
    )
    def reserve_part(self, call):
        reserved = call.invoke(
            "parts_desk.reserve_part",
            {
                "part_id": call.args["part_number"],
                "quantity": call.args["quantity"],
                "for_person": call.args["technician"],
            },
        )
        if not reserved:
            return {"error": reserved.error.message}
        return {"reservation_id": reserved.result["id"], "status": "reserved"}
