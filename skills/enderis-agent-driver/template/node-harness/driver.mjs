// Harness template (Node): import the agent and call it in this process.
//
// Enderis starts this file in the agent's folder with the run's simulated
// services, switched-off services and model keys already in place, and with
// `@enderis/driver` loaded first, so stdout and stdin are off the protocol
// before agent code loads. Change the parts marked TODO;
// `harness-frameworks.md` in the skill shows `ask` for each framework.

import path from "node:path";
import { pathToFileURL } from "node:url";
import { AgentError, reply, serve } from "@enderis/driver";

/** Import a module of the agent by its path in the agent's folder. */
const fromAgent = (file) => import(pathToFileURL(path.resolve(file)).href);

async function loadAgent() {
  // TODO: import the agent object, for example:
  // const { agent } = await fromAgent("src/agent.js");
  // return agent;
  throw new AgentError("TODO: import the agent in loadAgent()");
}

async function ask(agent, ctx, text) {
  // TODO: call the agent for one message and return its reply text. Keep the
  // conversation in ctx.state; the same process serves every wake of the run.
  throw new AgentError("TODO: call the agent in ask()");
}

let agent;

serve({
  name: "my-agent", // TODO: the name in driver.md
  async start() {
    agent = await loadAgent();
  },
  async wake(ctx, wake) {
    const replies = [];
    for (const delivery of wake.deliveries ?? []) {
      let answer;
      try {
        answer = await ask(agent, ctx, delivery.text ?? "");
      } catch (error) {
        if (error instanceof AgentError) throw error;
        throw new AgentError(`the agent failed: ${error?.message ?? error}`);
      }
      if (answer) replies.push(reply(delivery.id, String(answer)));
    }
    return { replies };
  },
});
