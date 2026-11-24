---
name: enderis-run-review
description: >-
  Review an agent's earlier Enderis runs: find them, choose which runs count,
  read each transcript and failed assertion, sum up the results per eval, and
  help the person decide what to change in the agent. Use when asked how an
  agent is doing, why its evals fail, what to fix next, or to review runs
  before or after a change. Carries the rule reviewers get wrong: never make
  the agent do less for its legitimate callers without asking first.
---

# Reviewing Enderis runs

## 1. Find the runs

```sh
enderis runs list --agent <agent> --limit 200 --json
enderis runs list --agent <agent> --eval <eval> --verdict fail
```

Over MCP, use `list_runs { agent_id }`, with optional `eval_id`, `status`,
`verdict` and `limit`. If `enderis runs list` or `enderis runs get` is not a
command, run `enderis update`. For each run, note its eval and eval version, its agent
version, its verdict and when it started. List the agent's evals too
(`enderis run . --list`, or `enderis run --agent <agent> --list` for a hosted
agent), so you can see which evals have no runs.

## 2. Choose which runs count

- Group the runs by eval.
- Use the runs of each eval on the newest agent version and the newest eval
  version. If there are several, read all of them: several runs show how
  stable the agent is. Give counts, such as "failed 1 of 2". Do not report an
  intermittent result as a pass or a fail. Runs on an older agent or eval
  version are history: they can fail for a cause that is already fixed, or
  for an assertion that has changed.
- Check whether the agent changed after its newest runs. For a repository
  agent, compare `git log` of the agent's code and prompts with the run times.
  If it changed, say plainly that the runs describe an older agent.
- An eval with no runs on the newest version has no data. Say so. Do not
  guess its result.

## 3. Read each run, not only the verdict

```sh
enderis runs get <run_id> [<run_id>...]          # verdict, assertions, tools called
enderis runs get <run_id> --full                 # the whole trajectory, as JSON
```

`enderis runs get` gives each assertion's result and the tools the agent
called in order. `--full` gives the whole trajectory: the agent's messages,
its tool calls with their arguments and results, and each assertion's result.
Over MCP, use `get_run { run_id, view: "summary" }`, then `get_run { run_id }`.
A person can open the same run in the web app.

- Read the eval's `evaluator.py` (in the repository, with
  `enderis evals get <eval> --agent <agent> --full`, or with
  `get_eval { eval_id }` over MCP) so you know what each failed assertion
  wants.
- Find the agent's own words or the tool call that caused each failure, and
  quote it.
- Decide where the fault is: in the agent, or in the eval. An assertion that
  checks the wrong thing, or a trigger that misleads the agent, is an eval
  problem. Fix it with the `enderis-eval-author` skill, not with an agent
  change.
- A run with status `error`, `timeout`, `canceled` or `unrunnable`, or
  verdict `error`, did not test the agent. Report it as a setup problem. A
  `queued` or `running` run has no result yet: wait for it or leave it out.

## 4. Sum up

When you read more than one run, work in two steps:

1. Reduce each run to its pattern: one line that says what the agent did and
   why the run passed or failed. Do this for one run at a time, before you
   compare runs.
2. Then put the patterns of all the runs together. Count how many runs show
   each pattern, for each eval and across evals. A pattern in every run is a
   stable behavior. A pattern in some runs is an intermittent one.

Give one row per eval: its result as counts, and what the agent did, with the
quote. Then list the patterns across evals, such as the same wrong tool
argument in three evals, with the number of runs that show each one.

## 5. Recommend only what the runs support

- Each proposed change names the run and the failure it answers.
- Drop an idea that no run supports, and say that you dropped it.
- For an intermittent failure, a guard in code (a check before the tool call,
  a validated argument) is usually more reliable than a new prompt rule. Say
  which you recommend and why.
- Label each proposal as untested until a run shows that it works.

## 6. Do not make the agent do less without asking

This is the most important rule. A change that makes the agent refuse,
withhold or stop something it does today for a legitimate caller reduces what
the agent can do.

First look for the narrowest change that stops the failure you saw and keeps
the capability. Example: a clinic front-desk agent read a patient's home
address to a co-parent who does not live there. "Never read out contact
details from a chart" stops the failure, but it also stops the patient. "Read
contact details back only to the person they belong to, or to someone the
chart lists as allowed" stops the failure and keeps the service.

If you still think a reduction is right, do not apply it on your own. Tell the
person:

- what the agent will no longer do, and who loses it;
- how the rule plays out for each person in the playground: who still gets
  an answer and who is declined;
- why a narrower rule does not work;
- the other options you rejected, and why.

Then ask the person to decide.

Before you propose any rule, check it against the passing runs too. A rule
that would have changed a passing run's correct answer breaks that eval.

## 7. Close the loop

- Ask before you edit the agent.
- After the change, onboard again if the package changed since its revision
  was onboarded: `enderis onboard .` (with the same `--name`, and `--driver`
  if you onboarded with one). `enderis run` stops and says so when the
  revision no longer matches. For a hosted agent, import the changed file
  with `enderis import agents/<name>.md`.
- Run each affected eval several times:
  `enderis run . --eval <name> --reps 3` (repository agent) or
  `enderis run --agent <agent> --eval <name> --reps 3` (hosted agent).
  Also run the evals that passed before, so you see whether the change broke
  them.
- Compare the new runs with the earlier ones, eval by eval, and report what
  changed. Do not call a fix done on one passing run of an intermittent
  failure.
- If a command fails and the fix is not clear, run `enderis faq`.
