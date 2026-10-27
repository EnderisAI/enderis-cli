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
`name` must match `@eval(name=...)`, unless the evaluator file registers exactly one
`@eval`: then it is shared and grades every eval that points at it. A file with several
`@eval`s errors when none matches.

**The description is labelled lines in a fixed order**, as above: Ask, Why it's
hard (omit if nothing lures the agent), Deciding rule, Right answer, Fails if.
Every fact comes from the seed or the evaluator; anything the evaluator does not
grade stays out of Right answer. No preamble, no restated trigger, no tool-call
narration. Format: https://enderis.ai/docs/evals/writing-evals.

**Mark key records.** List in `key_records:` each seed record the deciding rule
depends on that no check names, such as a consent row. Name a row some tool
returns whole. Display-only; see https://enderis.ai/docs/evals/writing-evals.

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

**`persona:` is who the simulated person is**: a registry persona (`terse`,
`terse@2`) or an inline `{name, prompt}`; without one, the neutral `cooperative`.
A cast entry without `listens:` inherits its roster entry's; `listens: []`
subscribes to nothing.

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
  `epoch:`. Seed timestamps agree with it and carry a UTC offset. A hosted
  agent reads the time through its built-in `clock.now`. A repository
  agent reads its own machine's clock, so if the trigger says "tomorrow", state
  the absolute date. Otherwise the run grades the agent's own calendar.
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
a hand-off to a human there.

**Hand the judge the right text.** `run.transcript` for anything about the
conversation (asked first, waited, refused). `run.final_answer` only for the last
reply on its own. For an email the agent wrote, read its text from `db`. Pass
extra material a rubric needs, such as tool calls, as `evidence=`, never glued
onto the transcript. Keep times, recipients and counts in deterministic checks;
use the judge only for meaning.

**Soft-collect by default.** A failed check records and the evaluator keeps
going. A check that only makes sense if another passed takes
`@assertion(depends_on=other)`. Use `require(...)` only to stop everything.

**Critical by default.** Mark a check minor (`@assertion(severity="minor")` or
`minor(outcome)`) only when the task was done but less well; minor failures alone
make the run `partial`, which is not a pass. Rules:
https://enderis.ai/docs/evals/assertions#mark-severity-and-dependencies.

**General checks live in the agent's standards file, not in each evaluator.**
List the ones that apply under `standards:` in `eval.md`: all of them unless one
cannot apply to the scenario.

**Prereqs check the agent reached the decision.** `@assertion(prereq=True)`
checks the agent faced the decision the eval tests; a failed prereq makes the run
`blocked`, which still counts as a failure. Must-not-act evals need one most;
the task itself and a seeded record are never prereqs. Rules and an example:
https://enderis.ai/docs/evals/assertions#mark-prerequisites.

**Metrics never gate**, and an evaluator that records nothing else gets the
`error` verdict. Any other uncaught exception is an evaluator error. Rules:
https://enderis.ai/docs/evals/assertions#record-metrics-without-gating.

**Put every `assert` inside an `@assertion` function.** There, a failing `assert`
fails that assertion. A bare `assert` directly in `check` stops the evaluator at
that line and skips every later check. Validation (**Run draft** and **Import
eval** in Create Eval, and the MCP tools `validate_eval`, `create_eval` and
`build_eval`) refuses an evaluator whose bare `assert` fails in its trial run on
the untouched seed. Plain `enderis import` does not run the evaluator, so it does
not catch this.

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

- **Persona entries are strict.** `reply` is required (`""` stays silent);
  only `satisfied`, `give_up` and `form_values` may join it.
- **One user reply per no-tool agent turn.** A turn with tool calls keeps
  control and gets no reply. Turns 0 and 2 above face the user: two replies.
- **Disclosures contain the fact text** `asked_before` looks for ("Tran").
- **Tool names are `product.tool`**, validated at import. `judge` entries answer
  `judge.with_rubric` calls in order. Replay runs at seed 0, so run-generated
  ids like `msg-0-1` only match there; evaluators must not depend on them.

## Voice agents

An agent that answers the phone gets calls, not chats: each eval is a live call
between the agent's voice and the simulated caller's voice. The trigger channel
is `voice:call:<agent principal>`, the eval's `listens` is `voice:call:<caller>`,
the caller's own `listens` is `voice:call:<agent principal>`, and the playground
seeds the `voice` service. Read the rules before writing one:
https://enderis.ai/docs/evals/writing-evals#voice-evals (MCP: the resource
`enderis://docs/authoring-brief`).

- **Grade what the caller heard**, from `run.call` and `run.timeline`, not
  only what the agent said. Every call already gets a `call_experience` check;
  do not write your own. Never grade the pauses between turns.
- **Do not make the scenario depend on an id the caller must say aloud** (an
  email, an order number). Speech recognition mangles it. Seed it where the agent
  can read it.
- **`scripted.json` needs a `call`.** A scripted voice run replays a call
  timeline recorded from one live run of the eval, so the fixture carries that
  `call` next to `turns` and `judge`. Without a recording from a live run, leave
  `scripted.json` out: import and launch refuse a voice fixture that has no
  `call`. A scripted voice run tests the pipeline, not the voice.

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

If an `enderis` command or MCP call fails and the fix is not clear, run
`enderis faq` (MCP: read `enderis://docs/agent-faq`) before you try again.

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
