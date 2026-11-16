# How a harness calls the agent

Use these with `template/python-harness/` and `template/node-harness/`.
`load_agent` / `loadAgent` returns the agent object the repository already
builds; `ask` sends one message and returns the reply text. Keep the
conversation in `ctx.state`: the same process, and the same agent object,
serve every wake of one run. Checked against the versions named; check the
repository's own version before you copy.

## Python (`template/python-harness/driver.py`)

| Framework | `load_agent` returns | `ask` calls | Memory between wakes |
|---|---|---|---|
| LangGraph 1.x, no `langgraph.json` | the compiled graph | `graph.invoke({"messages": ...})` | the messages, in `ctx.state` |
| LangChain 1.x `create_agent` | the agent (a compiled graph) | `agent.invoke({"messages": ...})` | the messages, in `ctx.state` |
| LangChain `AgentExecutor` | the executor (`langchain_classic.agents`) | `executor.invoke({"input", "chat_history"})` | `chat_history`, in `ctx.state` |
| Deep Agents `create_deep_agent` | the agent (a compiled graph) | `agent.invoke({"messages": ...})` | the messages, in `ctx.state` |
| OpenAI Agents SDK 0.24 | the `Agent` | `Runner.run(agent, items)` | `result.to_input_list()` |
| CrewAI 1.x | the `Crew` | `crew.kickoff(inputs=...)` | only through the crew's own inputs |
| LlamaIndex 0.14 | the `FunctionAgent` or `AgentWorkflow` | `agent.run(text, ctx=...)` | a workflow `Context` |
| Strands 1.x | the `Agent` | `agent(text)` | the agent object keeps it |
| Claude Agent SDK 0.2 | the `ClaudeAgentOptions` | `ClaudeSDKClient.query` | one connected client |
| pydantic-ai | the `Agent` | `agent.run_sync(text, message_history=...)` | `result.all_messages()` |
| No framework | the repository's loop function | `respond(messages)` | the messages, in `ctx.state` |

**LangGraph** (langgraph 1.2). If the graph has a checkpointer, pass only the new
message and `{"configurable": {"thread_id": ctx.run_id}}` instead. A graph with
async-only nodes needs `run(graph.ainvoke(...))`.

```python
def ask(graph, ctx, text):
    messages = ctx.state.setdefault("messages", [])
    messages.append({"role": "user", "content": text})
    out = graph.invoke({"messages": messages})
    ctx.state["messages"] = out["messages"]
    return out["messages"][-1].text  # text, even from a list of content blocks
```

**LangChain `create_agent`** (langchain 1.5): the same as LangGraph, with
`agent.invoke`.

**Deep Agents `create_deep_agent`**: the same as LangGraph. MCP tools are
async-only, so an agent that has them needs `run(agent.ainvoke(...))`.

**LangChain `AgentExecutor`** (langchain-classic 1.0; `langchain.agents` before
1.0). The `chat_history` key must be the prompt's own variable.

```python
from langchain_core.messages import AIMessage, HumanMessage

def ask(executor, ctx, text):
    history = ctx.state.setdefault("history", [])
    answer = executor.invoke({"input": text, "chat_history": history})["output"]
    history += [HumanMessage(text), AIMessage(answer)]
    return answer
```

**OpenAI Agents SDK** (openai-agents 0.24). `final_output` is not a string when
the agent has an `output_type`.

```python
from agents import Runner

def ask(agent, ctx, text):
    items = ctx.state.get("items", []) + [{"role": "user", "content": text}]
    result = run(Runner.run(agent, items))
    ctx.state["items"] = result.to_input_list()
    return str(result.final_output)
```

**CrewAI** (crewai 1.15). `kickoff` keeps nothing between calls; history
reaches the crew only if its task text uses an input such as `{history}`.

```python
def ask(crew, ctx, text):
    history = ctx.state.setdefault("history", [])
    out = crew.kickoff(inputs={"message": text, "history": "\n".join(history)})
    history += [f"User: {text}", f"Assistant: {out.raw}"]
    return out.raw
```

**LlamaIndex** (llama-index-core 0.14). `agent.run` must start inside the
event loop, so it is wrapped in a coroutine.

```python
from llama_index.core.workflow import Context

def ask(agent, ctx, text):
    memory = ctx.state.setdefault("context", Context(agent))
    async def go():
        return str(await agent.run(text, ctx=memory))
    return run(go())
```

**Strands** (strands-agents 1.64). Its default callback prints the streamed
text; the helper sends that to stderr.

```python
def ask(agent, ctx, text):
    return str(agent(text))
```

**Claude Agent SDK** (claude-agent-sdk 0.2). Keep one client for the run; no
person approves tools, so the options need a tool allowlist or a permission
mode. See "Claude Agent SDK" in the skill for the limits.

```python
from claude_agent_sdk import ClaudeSDKClient, ResultMessage

def ask(options, ctx, text):
    async def go():
        if "client" not in ctx.state:
            ctx.state["client"] = ClaudeSDKClient(options)
            await ctx.state["client"].connect()
        await ctx.state["client"].query(text)
        answers = [m.result async for m in ctx.state["client"].receive_response()
                   if isinstance(m, ResultMessage)]
        return answers[-1] if answers else ""
    return run(go())
```

**pydantic-ai** (pydantic-ai 2.x). Use `run(agent.run(...))` instead when the
agent's model client is async.

```python
def ask(agent, ctx, text):
    result = agent.run_sync(text, message_history=ctx.state.get("history"))
    ctx.state["history"] = result.all_messages()
    return result.output
```

**No framework**: a loop that calls a model SDK with `tools=`, behind a
function such as `respond(messages)`.

```python
def ask(respond, ctx, text):
    messages = ctx.state.setdefault("messages", [])
    messages.append({"role": "user", "content": text})
    answer = respond(messages)
    messages.append({"role": "assistant", "content": answer})
    return answer
```

## Node (`template/node-harness/driver.mjs`)

| Framework | `loadAgent` returns | `ask` calls | Memory between wakes |
|---|---|---|---|
| Vercel AI SDK 7, no chat route | the `ToolLoopAgent` | `agent.generate({ messages })` | `result.response.messages` |
| LangGraph.js 1.x, no server | the compiled graph | `graph.invoke({ messages })` | the messages, in `ctx.state` |
| langchain 1.x `createAgent` | the agent | `agent.invoke({ messages })` | the messages, in `ctx.state` |
| OpenAI Agents JS 0.22 | the `Agent` | `run(agent, input)` | `result.history` |
| Claude Agent SDK TS 0.3 | the `query` options | `query({ prompt, options })` | `resume` with the session id |
| Custom loop | the repository's loop function | `respond(messages)` | the messages, in `ctx.state` |

**Vercel AI SDK** (ai 7). For an app that wraps `generateText` in its own
function instead, call that function with the same `messages`.

```js
async function ask(agent, ctx, text) {
  const messages = (ctx.state.messages ??= []);
  messages.push({ role: "user", content: text });
  const result = await agent.generate({ messages });
  messages.push(...result.response.messages);
  return result.text;
}
```

**LangGraph.js** (@langchain/langgraph 1.7). With a checkpointer, pass only
the new message and `{ configurable: { thread_id: ctx.runId } }`.

```js
async function ask(graph, ctx, text) {
  const messages = (ctx.state.messages ??= []);
  messages.push({ role: "user", content: text });
  const out = await graph.invoke({ messages });
  ctx.state.messages = out.messages;
  return out.messages.at(-1).text; // text, even from a list of content blocks
}
```

**langchain `createAgent`** (langchain 1.6): the same as LangGraph.js, with
`agent.invoke`.

**OpenAI Agents JS** (@openai/agents 0.22).

```js
import { run } from "@openai/agents";

async function ask(agent, ctx, text) {
  const input = [...(ctx.state.history ?? []), { role: "user", content: text }];
  const result = await run(agent, input);
  ctx.state.history = result.history;
  return String(result.finalOutput);
}
```

**Claude Agent SDK** (@anthropic-ai/claude-agent-sdk 0.3). Each `query` starts
the CLI again and resumes the session from disk.

```js
import { query } from "@anthropic-ai/claude-agent-sdk";

async function ask(options, ctx, text) {
  let answer = "";
  for await (const m of query({ prompt: text, options: { ...options, resume: ctx.state.sessionId } })) {
    if (m.type === "result") ctx.state.sessionId = m.session_id;
    if (m.type === "result" && m.subtype === "success") answer = m.result;
  }
  return answer;
}
```

**Custom loop**: a loop that calls a model SDK with `tools`, behind a function
such as `respond(messages)`.

```js
async function ask(respond, ctx, text) {
  const messages = (ctx.state.messages ??= []);
  messages.push({ role: "user", content: text });
  const answer = await respond(messages);
  messages.push({ role: "assistant", content: answer });
  return answer;
}
```
