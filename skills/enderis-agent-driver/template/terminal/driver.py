"""Terminal template (Python): run the app's own interactive CLI for each
message and answer its prompts the way a user would.

Enderis starts this file in the agent's folder with the run's simulated services,
switched-off services and model keys already in place; the CLI inherits them.
Change the parts marked TODO.
"""

# First import: it moves the protocol off stdout and stdin before anything else.
from enderis.driver import AgentError, Terminal, WakeResult, reply, serve

# TODO: the command a user runs to start the app's CLI.
COMMAND = ["python3", "-m", "cli.main"]


def drive(term, ctx, text):
    # TODO: answer the CLI's prompts for this message and return the reply text,
    # for example:
    # term.expect("Ticker symbol", 60)
    # term.line(ticker_in(text))
    # term.expect("Research depth", 60)
    # term.send("down", "enter")  # named keys: enter, up, down, space, tab
    # term.wait(ctx.request_timeout or 300)
    # report = term.screen()  # what the CLI printed after the last keys
    # return report[report.find("Final report"):]  # the part a user reads as the answer
    raise AgentError("TODO: answer the CLI's prompts in drive()")


class Driver:
    name = "my-agent"  # TODO: the name in driver.md

    def wake(self, ctx, wake):
        result = WakeResult()
        for delivery in wake.get("deliveries", []):
            if delivery.get("text") is None:
                raise AgentError(
                    "this wake has no text; listen with `wake: text` on a channel that has message bodies"
                )
            term = Terminal(COMMAND)
            try:
                answer = drive(term, ctx, delivery["text"])
            finally:
                term.close()
            if answer and answer.strip():
                result.replies.append(reply(delivery["id"], answer.strip()))
        return result


if __name__ == "__main__":
    serve(Driver())
