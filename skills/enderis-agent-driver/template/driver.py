"""Driver template: an agent with an HTTP inbox and outbox.

Change the paths and fields marked TODO to match the app. Keep the rest:
run-scoped chat ids, draining before each answer, and acknowledging only
what Enderis accepted.
"""

import json
import os
import time
import urllib.parse
import urllib.request

from enderis.driver import AgentError, AgentTimeout, WakeResult, escalate, reply, serve

APP_URL = os.environ.get("APP_URL", "").rstrip("/")


def call(ctx, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        APP_URL + path, data=data, method=method, headers={"content-type": "application/json"}
    )
    timeout = min(30, ctx.request_timeout or 30)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read() or b"null")
    except (OSError, ValueError) as exc:  # unreachable, HTTP error or a non-JSON body
        raise AgentError(f"{method} {path}: {exc}") from exc


class Driver:
    name = "my-agent"  # TODO: the name in driver.md

    def start(self, ctx):
        if not APP_URL:
            raise AgentError("APP_URL is not set")
        call(ctx, "GET", "/health")  # TODO: the app's health path
        ctx.state["unacked"] = {}  # wake index -> outbox message ids returned on that wake

    def wake(self, ctx, wake):
        self.ack(ctx)
        chats = {}
        for delivery in wake.get("deliveries", []):
            # Everything sent to the shared app is scoped to this run.
            chat = f"{ctx.run_id}:{delivery['conversation']}"
            chats[chat] = delivery
            # TODO: the app's inbox request.
            call(
                ctx,
                "POST",
                "/inbox",
                {
                    "chat_id": chat,
                    "from": delivery["sender"]["handle"],
                    "text": delivery.get("text"),
                },
            )
        # This template always drains. With wake["waiting"] > 0 a driver may
        # instead hold the app's clock until a later wake; at 0 it must drain.
        replies, outcomes, returned = [], [], []
        deadline = time.monotonic() + 0.8 * (ctx.request_timeout or 60)
        for chat, delivery in chats.items():
            for message in self.drain(ctx, chat, deadline):
                returned.append(message["id"])  # TODO: the app's message id field
                if message.get("handoff"):  # TODO: how the app hands a chat to staff
                    outcomes.append(escalate(wake["channel"], message.get("reason", "")))
                elif message.get("text"):
                    replies.append(reply(delivery["id"], message["text"]))
        ctx.state["unacked"][wake.get("index", 0)] = returned
        return WakeResult(replies=replies, outcomes=outcomes)

    def drain(self, ctx, chat, deadline):
        """Read the chat's outbox until the app is idle. Silence is a valid answer."""
        query = urllib.parse.urlencode({"chat_id": chat})
        while True:
            outbox = call(ctx, "GET", f"/outbox?{query}")  # TODO: {"busy": bool, "messages": [...]}
            if not outbox.get("busy"):
                return outbox.get("messages", [])
            if time.monotonic() > deadline:
                raise AgentTimeout(f"the app was still busy with {chat}")
            time.sleep(0.5)

    def ack(self, ctx):
        """Acknowledge only what Enderis accepted: wakes up to accepted_through."""
        accepted = ctx.accepted_through
        for index in sorted(ctx.state["unacked"]):
            if accepted is None or index > accepted:
                break
            ids = ctx.state["unacked"].pop(index)
            if ids:
                call(ctx, "POST", "/outbox/ack", {"ids": ids})  # TODO: the app's ack request

    def stop(self, ctx, accepted_through):
        self.ack(ctx)
        if ctx.state["unacked"]:
            ctx.log(f"left unacknowledged: wakes {sorted(ctx.state['unacked'])}")


serve(Driver())
