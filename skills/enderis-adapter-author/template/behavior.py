"""Adapter template: the service (physics) behind one MCP server the agent calls.

A working example: a parts desk with one collection and two operations. Rename
the service, the collection and the operations to match the real system, and
keep only the operations the agent's tools need. Keep the rest: no state on
`self`, no clock or random numbers (use `ctx.tick()` and `ctx.new_id()`), and
errors through `ctx.domain()` and `ctx.bad_arguments()`.
"""

from enderis.mock import MockError, op, op_schema, seed_normalizer, service

_STRING = {"type": "string"}

_PART_ROW = {
    "type": "object",
    "properties": {
        "id": _STRING,
        "name": _STRING,
        "stock": {"type": "integer"},
        "bin": _STRING,
    },
    "required": ["id", "name", "stock"],
}

_RESERVATION_ROW = {
    "type": "object",
    "properties": {
        "id": _STRING,
        "part_id": _STRING,
        "quantity": {"type": "integer"},
        "for_person": _STRING,
    },
    "required": ["part_id", "quantity", "for_person"],
}


@service(
    name="parts_desk",  # TODO: a new name; never a built-in service name
    display_name="Parts desk",  # TODO: the product's own name
    state={"parts": "id", "reservations": None},  # keyed collection, then an append-only log
    # One row schema per collection: `enderis tools schemas` shows them to playground authors.
    seed_authoring={"collections": {"parts": _PART_ROW, "reservations": _RESERVATION_ROW}},
)
class PartsDesk:
    @seed_normalizer
    def normalize_seed(self, playground_slice):
        parts = playground_slice.get("parts", []) or []
        if not isinstance(parts, list):
            raise MockError(MockError.BAD_SEED, "parts_desk `parts` must be a list")
        for part in parts:
            if not isinstance(part, dict) or not isinstance(part.get("id"), str):
                raise MockError(MockError.BAD_SEED, "each part needs a string `id`")
            if not isinstance(part.get("stock"), int) or part["stock"] < 0:
                raise MockError(MockError.BAD_SEED, f"part {part['id']}: stock must be >= 0")
        return {"parts": parts, "reservations": playground_slice.get("reservations", []) or []}

    @op(
        name="get_part",
        classification="read",
        schema=op_schema("Look up one part by its part number.", {"part_id": _STRING}, ["part_id"]),
    )
    def get_part(self, ctx, store, args):
        part = store["parts"].get(args["part_id"])
        if part is None:
            raise ctx.domain(f"unknown part: {args['part_id']}")
        return part

    @op(
        name="reserve_part",
        classification="write",
        schema=op_schema(
            "Reserve stock of one part for a person.",
            {"part_id": _STRING, "quantity": {"type": "integer"}, "for_person": _STRING},
            ["part_id", "quantity", "for_person"],
        ),
    )
    def reserve_part(self, ctx, store, args):
        quantity = args["quantity"]
        if not isinstance(quantity, int) or quantity < 1:
            raise ctx.bad_arguments("quantity must be a whole number of at least 1")
        part = store["parts"].get(args["part_id"])
        if part is None:
            raise ctx.domain(f"unknown part: {args['part_id']}")
        if part["stock"] < quantity:
            raise ctx.domain(f"only {part['stock']} of {part['id']} in stock")
        store["parts"].put({**part, "stock": part["stock"] - quantity})
        reservation = {
            "id": ctx.new_id("res"),
            "part_id": part["id"],
            "quantity": quantity,
            "for_person": args["for_person"],
            "logical_time": ctx.tick(),
        }
        store["reservations"].append(reservation)
        return reservation
