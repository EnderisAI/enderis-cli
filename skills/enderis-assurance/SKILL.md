---
name: enderis-assurance
description: >-
  Show which Enderis evals test each control of a compliance or safety
  framework loaded in the workspace: read the controls, propose claims and the
  control-to-claim map, set which controls apply to the agent, tag assertions
  with claims, import, run, and read the gaps. Use when asked to prepare an
  agent against a framework, map evals to controls, close coverage gaps, or
  get an agent ready for an assurance artifact. Beta.
---

# Framework assurance with Enderis

This feature is beta. The CLI and MCP work in every workspace. The web app
screens (map approval, coverage, artifacts) show only when Enderis turns on
the `claims` feature for the organization. Reference:
https://enderis.ai/docs/evals/claims.

## The model

- A **framework** is a list of **controls**, loaded into the workspace. Each
  control has a kind: `testable`, `third_party_testing` or `policy`. Only
  `testable` controls get coverage.
- A **claim** is one testable sentence about the agent, with a slug, such as
  `no-unrequested-record-writes`. It names no framework.
- A **map row** links one control to one claim. You propose rows; a person
  approves them in the web app. Only approved rows count.
- A **tag** links one `@assertion` to claims: `@assertion(claims=[...])`.
- A claim is **covered** when a tagged assertion has a graded, non-scripted
  result on the agent revision. Enderis does not check that a tag is right.
  An auditor reads the tags, the evaluator source and who wrote them. So tag
  only what the assertion really tests.

## The loop

1. Read the agent repository: its tools, the data it touches, its users and
   its domain.
2. Read the frameworks: `enderis frameworks list`, then
   `enderis frameworks controls <framework>`. Never copy control text into a
   file, a claim or an eval. Refer to controls by id only.
3. Read the claims that exist: `enderis claims list`. Reuse a claim before you
   write a new one.
4. Write new claims and apply them with `enderis claims put claims.yaml`.
5. Propose map rows with `enderis claims map put map.yaml`.
6. Set which controls apply with
   `enderis claims applicability put --agent <agent> applicability.yaml`.
7. Tell the person to approve the proposed map rows in the web app. The CLI,
   MCP and API keys cannot approve (403); only a web app session can. Until a
   row is approved, its claim counts toward nothing. If the person cannot see
   the claims screens, they ask Enderis (founders@enderis.ai) to turn on the
   feature.
8. Read the gaps: `enderis claims gaps --agent <agent> --framework <framework>`.
9. Write or fix evals for the gaps with the `enderis-eval-author` skill. Tag
   the assertions (below), then import with
   `enderis import evals/<name> --agent <agent> --authored-by coding-agent`.
10. Run each tagged eval at least 3 times on the current agent revision:
    `enderis run . --eval <name> --reps 3` (repository agent) or
    `enderis run --agent <agent> --eval <name> --reps 3` (hosted agent).
11. Read the gaps again. Repeat from step 9 until no gap remains that a test
    can close.
12. Tell the person they can freeze an assurance artifact in the web app.
    You do not create it.

## Files

`claims.yaml`. A slug is lowercase letters, digits and single hyphens. A slug
that exists is updated in place, and putting it again without `description`
clears the description. Leave `status` out: a new claim starts as `proposed`,
and approving a map row makes it `active`.

```yaml
claims:
  - slug: no-unrequested-record-writes
    name: No unrequested record changes
    statement: The agent never changes a record the user did not ask it to change.
    description: Optional. Why it matters.
```

`map.yaml`. One row per control and claim. A control can map to many claims,
and a claim to many controls.

```yaml
framework: acme-safety
rows:
  - {control_id: AS-4, claim: no-unrequested-record-writes}
```

`applicability.yaml`. `state` is `selected`, `not_selected` or
`not_applicable`. `not_applicable` needs a `reason`. Controls you leave out
keep their state. A control with no decision gets no gaps, so set every
control you will test to `selected`.

```yaml
framework: acme-safety
controls:
  - {control_id: AS-4, state: selected}
  - {control_id: AS-9, state: not_applicable, reason: The agent sends no payments.}
```

## Tagging assertions

```python
from enderis import assertion

@assertion(claims=["no-unrequested-record-writes"])
def changed_only_the_requested_record(db):
    """Only the requested appointment changed."""
    ...
```

- Only `@assertion` functions carry tags. A helper outcome that the tagged
  `@assertion` returns (alone or in a dict) carries its tags. A helper that
  is called but not returned keeps its own result, with no tags.
- Import `assertion` under its own name. `from enderis import assertion as x`
  is not supported for claims.
- Write `claims=` as a literal list of strings. Import reads it without
  running the evaluator and refuses anything else.
- Tag a claim only when the assertion fails when the claim is false. A check
  that the task got done is not evidence for a safety claim.
- An unknown slug does not fail import. Import warns, and the tag counts
  toward nothing until the claim exists.
- A tag is part of the eval version. Changing it makes a new version.

## Reading gaps

Gaps cover only `testable` controls whose state is `selected`. Each gap has a
`kind`:

| Kind | What to do |
| --- | --- |
| `control_unmapped` | Propose a claim and a map row for the control. |
| `claim_untested` | Write an eval with an assertion tagged with the claim. |
| `claim_not_run` | Run the tagged evals on the current agent revision. |
| `claim_failing` | Read the failing runs. Fix the agent, or fix the eval if the test is wrong. |

Counts read the last 3 graded runs of each eval at its latest version on the
agent revision. Scripted runs never count. A new eval version starts with no
runs, so run it again after each import that changes it.

## Rules

- Never write framework or control text from memory or from a licensed
  catalog. Read controls from the workspace.
- Never set a claim's `status`, and never approve map rows. A person decides.
- Never pass `--provider scripted` for these runs. Scripted runs never count.
- Do not tag an assertion to make a gap go away. The auditor reads the tags.
- Over MCP, the same reads are `claims_list`, `framework_controls` and
  `claims_gaps`.
- If a command fails and the fix is not clear, run `enderis faq`.
