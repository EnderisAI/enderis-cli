---
name: enderis-eval-author
description: >-
  Write or review an Enderis eval: eval.md, playground.yaml, evaluator.py and
  scripted.json. Use when asked to create an eval, add assertions, fix a flaky
  or misleading evaluator, or check an eval before import. Carries the
  judgment rules authors get wrong: grade outcomes not tool calls, one
  assertion per claim, dates from the playground clock, and a scripted
  self-test.
---

# Authoring Enderis evals

An eval is a directory: `eval.md` (config, description, trigger),
`playground.yaml` (a stored playground plus this scenario's delta),
`evaluator.py` (assertions), and an optional `scripted.json` (a canned agent run
that tests the eval). Enderis imports it as an immutable version and returns a
pass, partial, fail, blocked or error verdict plus a result for every assertion and check. Write the pass
condition first, then the seed that decides it, then the trigger. Reference:
https://enderis.ai/docs/evals/writing-evals, `/docs/evals/assertions`,
`/docs/evals/authoring`. Over MCP, the full authoring guide is the resource
`enderis://docs/authoring-evals`; open it only when a rule here is not enough.

## eval.md

```markdown
---
name: book_with_right_alice
description: |-
  **Ask.** Set up 30 minutes with "Alice" on Thursday and send her the invite.
  **Why it's hard.** Alice Walsh's Thursday is emptier, so the wrong Alice books cleanly.
  **Deciding rule.** Two people are named Alice. Only the user can say which; asked, she says Alice Tran.
  **Right answer.** One 30-minute Thursday event inviting alice.tran@example.com and not Walsh.
  **Fails if** the agent books before asking, or guesses and invites Walsh.
principal: avery
max_turns: 12
npc:
  facts:
    - reveal: when_asked
      fact: I mean Alice Tran on the platform team, alice.tran@example.com.
      assert_elicited: true
trigger: chat
---
Set up a 30-minute meeting with Alice on Thursday and send her the invite.
```

`playground`, `evaluator` and `scripted_fixture` default to those file names.
`name` must match `@eval(name=...)`.

**The description is labelled lines in a fixed order.** A `|-` block, one or two
sentences per line, under about 900 characters. The agent never sees it. Every
fact comes from the seed or the evaluator. No preamble, no restating the
trigger, no tool-call narration.

- **Ask.** Who wants what, with the names, amounts and dates that matter.
- **Why it's hard.** The green lights that lure a naive agent. Omit if none.
- **Deciding rule.** The one fact or policy that decides the case, and its source.
- **Right answer.** The durable outcome the evaluator grades, with identifiers.
  Anything the evaluator does not grade stays out.
- **Fails if** The one or two ways an agent gets it wrong.

**Mark key records.** List in `key_records:` each seed record the deciding rule
depends on that no check names, such as a consent or restriction row:
`{service, collection, id, why}`, with `why` one line. Display-only: the eval
page shows whether the latest run read it; grading ignores it. "Read" means a
tool returned that row with its id, so name a row some tool returns whole, not
one only seen through a summary such as a stock count or price quote.

**The trigger is a natural opener.** It is delivered verbatim. A real person
states a problem in their own words and does not recite ids, emails or exact
figures. Write it the way that person would type it: the problem first, in
plain words, with only the detail they would naturally have to hand.

**Facts a person gives only when asked go in `when_asked`.** Mark the one fact
the scenario is about with `assert_elicited: true`, then grade it with
`run.asked_before` inside an `@assertion` (it records nothing on its own). It
passes when the disclosing turn came before every call to the tool, or the tool
was never called; pass alternate spellings as extra arguments. Write facts as
"my order" or "you are", never "the customer is". Gate a tool on a hidden fact
only when the agent cannot learn it any other way: if the playground holds the
answer, asking was optional and the check fails a correct run.

**`persona:` is who the simulated person is.** Under `npc:` or a `cast:` entry
it names a registry persona (`terse`, or `terse@2` to pin a version) or is the
persona inline, `{name, prompt, model?, voice?}` with a non-empty name and
prompt and `voice` shaped as in a `persona.md`, stored exactly as written.
`npc:` without one uses the neutral built-in `cooperative`.

**A cast entry without `listens:` or `interfaces:` inherits its roster entry's.**
Write `listens: []` for a person who should subscribe to nothing.

## playground.yaml

```yaml
blueprint: cos              # the shared stored playground; pin with cos@3
services:
  google_calendar:
    events:
      - id: ev_tran_review  # adds a row, or replaces the row with this key
        calendarId: alice.tran@example.com
        start: '2026-06-18T10:00:00-07:00'
        end: '2026-06-18T11:30:00-07:00'
    $remove:
      events: [ev_focus]    # drop shared rows this scenario must not see
```

- **A matching key replaces the whole record.** To change an existing record,
  restate every field of it, not just the changed ones; missing fields fail
  import (for example "car.year is required"). Over MCP, read the current
  record with `get_records` first and restate it with your change.
- **Seed only what the scenario needs.** Shared people and background data live
  in the stored playground; the delta carries this scenario's decision and trap.
  The trigger is the first runtime post, not seed data.
- **Dates come from the playground clock.** The stored playground declares an
  `epoch:`. Seed timestamps agree with it and carry a UTC offset. If the trigger
  says "tomorrow", either state the absolute date or make sure the agent has a
  tool that tells it the time. Otherwise the run grades the model's calendar.
- **Money is decimal dollars in yaml** (`balance: 120.00`). Tools and snapshots
  use integer cents (`balance_cents: 12000`), so assert in cents.

## evaluator.py

```python
from datetime import date, datetime, timedelta
from enderis import assertion, eval, judge, record_metric

RIGHT, WRONG = "alice.tran@example.com", "alice.walsh@example.com"

def _created_event(db):
    created = list(db.service("google_calendar").added("events", key="id"))
    return created[0] if len(created) == 1 else None

def _thursday(db):
    today = date.fromisoformat(db.playground.seed.clock.epoch[:10])
    return (today + timedelta(days=(3 - today.weekday()) % 7)).isoformat()

@assertion
def asked_which_alice_before_booking(run):
    return run.asked_before("google_calendar.create_event", "tran")

@assertion
def exactly_one_event_created(db):
    return _created_event(db) is not None

@assertion
def booked_correct_alice(db):
    event = _created_event(db) or {}
    emails = {a.get("email") for a in event.get("attendees", [])}
    return {"invited_tran": RIGHT in emails, "did_not_invite_walsh": WRONG not in emails}

@assertion
def booked_requested_slot(db):
    event = _created_event(db) or {}
    start, end = event.get("start", ""), event.get("end", "")
    if not (start and end):
        return False
    minutes = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() / 60
    return {"on_thursday": start.startswith(_thursday(db)), "thirty_minutes": minutes == 30}

@eval(name="book_with_right_alice")
def check(run, db):
    asked_which_alice_before_booking(run)
    exactly_one_event_created(db)
    booked_correct_alice(db)
    booked_requested_slot(db)
    judge.with_rubric(run.transcript,
                      rubric="Asks which Alice before booking, then confirms the time with Tran.")
    record_metric("llm_calls", run.llm_call_count)
```

**Every helper records when you call it.** `assert_exists`, `assert_absent`,
`assert_count`, `assert_all`, `called_with`, `was_called`, `judge.with_rubric`
and `record_metric` record and return a truthy or falsy result. Call them as
statements. `assertion` only decorates your own functions; wrapping a matcher,
as in `assertion(x.was_called())`, is wrong.

**Judge the transcript, add the rest as evidence.** When several rubrics
judge the conversation, give each the same `run.transcript` and pass anything
else a rubric needs (tool calls, records) as `evidence=`. The judge caches the
content across calls; extras glued onto it defeat the cache.

**Grade outcomes, not tool calls.** Assert on what is durably true in the
playground after the run (`where=` is exact equality, `containing=` is
case-insensitive substring, `added`/`removed` diff against the seed). There is
usually more than one way to make the same row, and `create_event.was_called()`
passes a rejected write and fails a valid alternative path. Never put a positive
call check next to a state check of the same action. Call checks are for three
cases only: a traceless read (including a prereq that the agent reached the
decision), a mandated verification or safety gate, and a must-not-act boundary.

```python
run.tool("google_calendar.list_events").was_called()            # traceless read
run.tool("google_calendar.delete_event").was_called(times=0)    # boundary...
db.service("google_calendar").assert_absent("events", containing={"summary": "cancelled"})  # ...and its effect
```

**One assertion, one claim.** The function name is what a reader sees when it
fails, so every check inside must be evidence for that name. A check that can
fail for a reason the name does not cover is a separate assertion. Test: when
only this assertion fails, does its name alone say what went wrong? Above, who
was invited and when are separate claims; the `_created_event` helper keeps the
split cheap. Names are stable keys across evals, so do not rename them casually.

**Use `Check` when a failure should show what it compared.** A dict value of
`Check("balance", actual == 5_000, expected=5_000, actual=actual)` renders
expected against actual instead of "returned false". Emit one check per
expectation in the scenario, not one per row in a table.

**Service and collection names fail closed. Field names do not.** A typo in
`db.service("google_calender")` or a collection name fails the assertion and
lists the real names. A typo in a `where=` or `containing=` key matches nothing,
so `assert_exists` fails and `assert_absent` passes vacuously. Check every field
name against `playground.yaml` yourself.

**Escalations are outcomes.** For an agent run through a driver, `run.outcomes`
lists each `{kind: "escalated", channel, reason, wake}` the agent reported. Grade
a hand-off to a human there; its replies are ordinary messages.

**Hand the judge the right text.** `run.transcript` for anything about the
conversation (asked first, waited, refused). `run.final_answer` only for the last
reply on its own. For an email the agent wrote, read its text from `db`. A
judge check passes when `score >= threshold`. Keep times, recipients and counts in
deterministic checks; use the judge only for meaning.

**Soft-collect by default.** A failed check records and the evaluator keeps
going, so one run shows every failure. When a check only makes sense if an
earlier one passed, declare it with `@assertion(depends_on=earlier)` (or a
list): if `earlier` failed, the dependent is recorded as not reached and never
gates, so one miss shows as one failure, not a cascade. Call `earlier` first in
`check()`. Use `require(...)` only to stop everything.

**Mark each check critical or minor.** Assertions are critical by default: a
failed one fails the run. Mark a check minor (`@assertion(severity="minor")`,
or `minor(outcome)` / `outcome.minor()` on a helper's result) when the task was
done but done less well: a missing courtesy, a clumsy message, an unneeded
detail. Wrong records, wrong amounts, broken promises and crossed boundaries
stay critical. Only minor failures make the run `partial`, which is not a pass.

**General checks belong in the agent's standards, not in each evaluator.**
Checks that apply to every conversation (gives a contact route, invents no
facts, takes no unrequested action, keeps its promises) live in the agent's
standards file (`agent.md` frontmatter `standards:`), which runs after every
eval through its `@standard` functions. Do not copy them into an evaluator; the
evaluator grades what this scenario is about. List the standards that apply to
the scenario under `standards:` in `eval.md` (all of them unless one cannot
apply); without the key every standard applies.

**Prereqs check the agent reached the decision.** `@assertion(prereq=True)`
checks the agent faced the decision the eval tests; a failed prereq makes the run
`blocked`, which still counts as a failure. Must-not-act evals need one most;
the task itself and a seeded record are never prereqs. Rules and an example:
https://enderis.ai/docs/evals/assertions#mark-prerequisites.

**Metrics never gate.** The verdict passes only when at least one pass/fail
assertion was recorded and all passed; not-reached assertions never gate. An
evaluator that records nothing, or only metrics, gets the `error` verdict:
neither a pass nor a failure, and outside every pass rate. A failing bare
`assert` fails the `@assertion` it is in (its severity applies); outside one
it records a failed critical check and stops the evaluator. Any other
uncaught exception is an evaluator error: the run is `error` unless a
prerequisite or critical check already failed.

## scripted.json

A fixture replays the intended agent so the eval tests itself, free and keyless.

```json
{
  "model": "scripted-v1",
  "turns": [
    {"text": "There are two Alices, Tran on platform and Walsh in design. Which one?"},
    {"text": "Booking 2:00pm.", "tool_calls": [{"name": "google_calendar.create_event",
      "arguments": {"calendarId": "avery@example.com", "summary": "Alice Tran",
        "start": "2026-06-18T14:00:00-07:00", "end": "2026-06-18T14:30:00-07:00",
        "attendees": [{"email": "alice.tran@example.com"}]}}]},
    {"text": "Booked 30 minutes with Alice Tran on Thursday at 2:00pm."}
  ],
  "personas": {"user": ["{\"reply\": \"I mean Alice Tran, alice.tran@example.com.\", \"satisfied\": false}",
                        "{\"reply\": \"\", \"satisfied\": true}"]},
  "judge": [{"score": 0.95, "reasoning": "asked first, confirmed Tran"}]
}
```

- **One user reply per no-tool agent turn.** A turn with tool calls keeps
  control and gets no reply. Turns 0 and 2 above face the user: two replies.
- **Disclosures contain the fact text** `asked_before` looks for ("Tran").
- **Tool names are `product.tool`**, validated at import. `judge` entries answer
  `judge.with_rubric` calls in order. Replay runs at seed 0, so run-generated
  ids like `msg-0-1` only match there; evaluators must not depend on them.

## Submit, run and read results

Three paths store an eval:

- **CLI**: `enderis import evals/<name> --agent <agent-name>` uploads the eval
  directory; add `--acceptance` to put it in the acceptance set. See
  https://enderis.ai/docs/cli/import.
- **Dashboard, Create Eval** on the agent's page: a guided draft with **Run
  draft** against the agent before it is saved. The **Edit** tab of an existing
  eval saves a new version and, when it has a fixture, launches the scripted
  self-test, which must pass.
- **MCP** from a coding agent: `get_authoring_packet`, `validate_eval` while
  drafting, then `create_eval` with `scripted_json` to launch the seed-0
  self-test; poll the returned `run_id` with `get_run` until it passes.

```sh
enderis run . --list                          # from the onboarded agent's repo
enderis run . --eval book_with_right_alice    # add --reps 5 for repeats
```

Open the printed run link and read **Assertions** first: one row per assertion,
each check with expected against actual where recorded. Then read the
conversation. A failure means the agent and the test disagree, and the test can
be wrong. Unrunnable means a setup problem. See https://enderis.ai/docs/quickstart.

## Checklist before importing

- [ ] Description lines are in order; every fact is seeded or graded.
- [ ] The trigger reads like a real person; looked-up ids are `when_asked` facts.
- [ ] The delta seeds only this scenario's decision and trap.
- [ ] Relative dates resolve; expected dates derive from the playground epoch.
- [ ] Assertions grade state. Each `was_called` is a traceless read, a mandated
      gate, or a `times=0` boundary paired with `assert_absent`.
- [ ] Each assertion's name says what went wrong when only it fails.
- [ ] Each `@assertion` has a one-line docstring stating the outcome in business
      terms; the run page shows it as Expected.
- [ ] Every `where=` and `containing=` field exists in the seed.
- [ ] `asked_before` sits in an `@assertion`; the fixture discloses its substring.
- [ ] The scripted self-test passes. Change one fact at a time (wrong Alice,
      wrong day) and only the matching assertion fails. A do-nothing run fails.
