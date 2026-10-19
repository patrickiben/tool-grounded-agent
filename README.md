# tool-grounded-agent

**A grounding *harness* for agentic drafting — not a safe agent.** A tool-calling "agent" drafts a clinical adverse-event narrative by filling template slots **only** from a recorded tool-call ledger, and the assembled text is then re-validated by a vendored [`numguard`](https://github.com/patrickiben/numguard)-style guard. Provenance and grounding in two independent layers. *Agents WITH guardrails, not vibes.*

![ci](https://github.com/patrickiben/tool-grounded-agent/actions/workflows/ci.yml/badge.svg)
&nbsp;·&nbsp; Python ≥ 3.9 · zero runtime dependencies · MIT

> **Read this first.** This is a grounding **harness**, not a safe autonomous agent. The "agent" is a **deterministic, scripted stand-in** for a function-calling LLM — *it is not a language model.* The rogue behaviors below are **author-written injections** chosen to exercise each guard layer, **not** bypasses discovered by an adversarial model. This demonstrates a guard *architecture*; it is **not** an adversarial-robustness evaluation. "Grounded" here means **traceable, not trustworthy.**

---

## The idea

```
facts ─► tools ─► ledger ─► slot-fill render ─► [Layer 1] ─► numguard guard + ledger check ─► [Layer 2] ─► human signs
        (the only      (audit     (a slot can only        (every number must be an allowed
         number         trail)     hold a tool result)      fact AND actually fetched this run)
         source)
```

- **Layer 1 — structural (prevention).** A `{slot}` can only be filled by a successful tool result; the agent has no API to type a bare number. A slot with no backing result renders as `«UNSOURCED»` and raises an error — the breach is *visible in the draft*, not hidden.
- **Layer 2 — text guard (detection / backstop).** Run on the final text regardless of how the planner behaved: `numbers_grounded` (every number is an allowed fact), `numbers_from_ledger` (every number was *actually produced by a tool this run* — strictly stronger), `unsupported_claims` (banned phrases), `required_facts`.

### The centerpiece: the two layers are not redundant

An agent that recites a **real, correct fact it never looked up** *passes* numguard's set-membership but *fails* the ledger provenance check:

```
[fail] rogue_unqueried_real_fact
  draft: In the safety population (N=24), adverse events were assessed.
         Overall, 79.2% of participants reported a treatment-emergent adverse event.
  verdict: FAIL  (layer1 errors=0, layer2 errors=1)
   - [ERROR] {layer2} numbers_from_ledger: Number '79.2' was not produced by any tool call this run.
```

`79.2%` is a genuine fact (so plain `numguard` with no ledger **passes** it) — but it was never fetched, so the ledger check catches it. That gap is the whole point: *provenance ≠ membership.* (Asserted in `tests/test_agent.py::test_centerpiece_ledger_only_and_numguard_passes`.)

---

## Quickstart (no install, no dependencies)

```bash
python selftest.py
```

It runs every scenario and classifies each candidate `OK` / `KNOWN-GAP` / `UNEXPECTED`. Real summary:

```
[OK]        well_behaved              expected=pass  passed=True
[OK]        rogue_hallucinated_number expected=fail  passed=False   (81.5 caught by numbers_grounded + numbers_from_ledger)
[OK]        rogue_unqueried_real_fact expected=fail  passed=False   (numbers_from_ledger ONLY)
[OK]        rogue_fabricated_slot     expected=fail  passed=False   («UNSOURCED» in draft)
[OK]        rogue_banned_claim        expected=fail  passed=False   (unsupported_claims; zero layer-1 errors)
[KNOWN-GAP] garbage_in_fact           expected=miss  passed=True    (store itself is wrong; no layer validates truth)
[KNOWN-GAP] unit_swap                 expected=miss  passed=True    ('19%' of a count; both layers unit-blind)
...
summary: 8 OK, 5 KNOWN-GAP, 0 UNEXPECTED
SELFTEST PASSED
```

Run a scenario through the CLI and emit CI artifacts (JSON carries the ledger + which layer caught each finding):

```bash
python -m toolagent scenarios/ae_overview.json --json results.json --junit results.xml
```

---

## ⚠️ What this does NOT catch (equal weight to the features)

The harness ships its own blind spots as **executable `known-gap` tests** (`tests/test_known_gaps.py`) — they assert the problem *passes*, so if behavior ever silently changes, the tests break and this list must be updated honestly.

- **Garbage-in facts.** If the `FactStore` holds a wrong value, every layer certifies the wrong number. No layer validates upstream truth.
- **Spelled-out / non-ASCII numbers.** "nineteen", Roman numerals, full-width digits, `grade3`, leading-decimal `.5`, signed `-2.3`, ranges `1-4`, European `79,2` — the extractor doesn't see them, and it backs *both* layers.
- **Qualitative claims beyond a finite denylist.** Paraphrase ("encouraging tolerability profile"), whitespace evasion ("well  tolerated"), implied causality, unsupported comparison, framing/quantifier spin ("only 79.2%"). The entire class of qualitative harm is essentially unguarded.
- **Unit blindness.** "19% of participants" where 19 is a *count* passes both layers.
- **Selective omission.** A draft that truthfully reports the AE rate while silently dropping serious events passes; `required_facts` checks presence, not completeness or balance.
- **Provenance is value-membership, not per-occurrence.** One legitimate fetch of `0` licenses every other `0` in the prose.
- **Tolerance coincidences.** A fabricated number within ±0.05 of any fact grounds (especially dangerous near `0`).

> **Bottom line:** tool-discipline says where numbers *should* come from; the ledger check verifies they *actually* came from a tool this run; the grounding guard verifies they are an allowed fact and that no enumerated banned phrase appears. **None of the three certify the numbers are correct, complete, correctly-united, in the right sentence, or fairly framed — that is the human's job.** This harness exists to make that review smaller and sharper, not to remove it. A qualified human still authors the interpretation and signs.

---

## The two-layer boundary

| | catches | blind to |
|---|---|---|
| **Layer 1** (render) | numbers typed outside a tool-backed slot; fabricated/empty slots | claim semantics; anything in free prose |
| **Layer 2** (guard) | ungrounded numbers; numbers never fetched; banned phrases; missing required facts | spelled-out/unit-swapped numbers; paraphrased claims; upstream truth; placement |

Neither is sufficient; together they cover more — and the `wrong_denominator_disagree` scenario shows them *disagreeing* (a tool-derived value passes the ledger check but fails grounding), which is exactly the point.

---

## From mock to a real model

The planner is a `Planner` Protocol; `MockPlanner`/`ReplayPlanner` are scripted stand-ins. A real function-calling LLM implements the same protocol, receives `BUILTIN_TOOLS` as its tool schema, and the `ToolRegistry` / `ToolLedger` / `render` / guard run **unchanged**. Crucially: **a real model makes the planning step *less* trustworthy, not more** — which is precisely why the Layer-2 ledger backstop exists. (`tests/test_agent.py::test_planner_protocol_swappable` proves the seam is real.)

---

## Project layout

```
toolagent/   facts · extract · tools (registry+ledger) · render (Layer 1) · guard (Layer 2)
             planner (seam) · agent (run_agent) · report · loader · export · __main__ (CLI)
scenarios/   ae_overview.json · lab_summary.json · misleading_but_grounded.json
tests/       7 modules, 34 tests (agent, tools, render, guard, known_gaps, export, selftest)
selftest.py  zero-dependency runnable proof
```

`pytest -q` → **34 passed**. CI runs the self-test, the CLI export, the suite (Python 3.9 + 3.12), and a clean-env import check.

---

## Status & honesty note

A **working proof-of-concept, not validated software for production regulatory use.** Bundled data is synthetic (CP-101). Per a standing terminology rule, the narrative uses *participant*, never *subject*. This demonstrates a safety **pattern** — tool-ledger provenance plus deterministic grounding — that I believe regulated agentic systems need; it is not a finished compliance tool.

## License

MIT — see [LICENSE](LICENSE). Built by Patrick Iben (`p.iben@saeny.net`). Companion projects: [`numguard`](https://github.com/patrickiben/numguard), [`grounded-rag`](https://github.com/patrickiben/grounded-rag), [`guarded-llm-service`](https://github.com/patrickiben/guarded-llm-service).
