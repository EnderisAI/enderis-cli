"""Optional facade extension for Slack. Copy beside interfaces/, without behavior.py.

Adapt the operation to the real API. Invoke as slack.x_count_messages from
an interface tool; it is not a direct service tool.
"""

from enderis.mock import op


class Operations:
    @op(name="x_count_messages", classification="read")
    def count_messages(self, ctx, store, args):
        return {"count": len(store["messages"].values())}
