"""Harness template (Python): import the agent and call it in this process.

Enderis starts this file in the agent's folder with the run's mocked services,
switched-off services and model keys already in place. Change the parts marked
TODO; `harness-frameworks.md` in the skill shows `ask` for each framework.
"""

import asyncio
import os
import sys

# First import: it moves the protocol off stdout and stdin before agent code loads.
from enderis.driver import AgentError, WakeResult, reply, serve

sys.path.insert(0, os.getcwd())  # the agent's folder

_loop = asyncio.new_event_loop()


def run(coro):
    """Run a coroutine on one event loop for the whole run, so async clients
    the agent keeps between messages stay usable."""
    return _loop.run_until_complete(coro)


def load_agent():
    # TODO: import the agent object, for example:
    # from my_agent.graph import graph
    # return graph
    raise AgentError("TODO: import the agent in load_agent()")


def ask(agent, ctx, text):
    # TODO: call the agent for one message and return its reply text. Keep the
    # conversation in ctx.state; the same process serves every wake of the run.
    raise AgentError("TODO: call the agent in ask()")


class Harness:
    name = "my-agent"  # TODO: the name in driver.md

    def start(self, ctx):
        self.agent = load_agent()

    def wake(self, ctx, wake):
        result = WakeResult()
        for delivery in wake.get("deliveries", []):
            try:
                answer = ask(self.agent, ctx, delivery.get("text") or "")
            except AgentError:
                raise
            except Exception as exc:  # noqa: BLE001 - the agent's own failure
                raise AgentError(f"the agent failed: {exc}") from exc
            if answer:
                result.replies.append(reply(delivery["id"], str(answer)))
        return result


if __name__ == "__main__":
    serve(Harness())
