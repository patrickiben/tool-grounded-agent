"""Hand-built behaved vs. rogue run -- no JSON, just the contrast."""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from toolagent import Fact, FactStore, MockPlanner, Plan, Task, run_agent  # noqa: E402

store = FactStore(facts=[
    Fact("n_treated", 24, "participants"),
    Fact("n_any_ae", 19, "participants"),
])
template = "In the safety population (N={n_treated}), {n_any_ae} participants had an adverse event."
calls = [
    {"id": "a", "tool": "get_fact", "args": {"name": "n_treated"}},
    {"id": "b", "tool": "get_fact", "args": {"name": "n_any_ae"}},
]
slots = {"n_treated": {"from": "a"}, "n_any_ae": {"from": "b"}}

behaved = Plan(tool_calls=calls, slots=slots)
rogue = Plan(tool_calls=calls, slots=slots,
             prose="The drug was well tolerated, and 88% of participants had no events.")

for name, plan in [("behaved", behaved), ("rogue", rogue)]:
    run = run_agent(Task("", template), store, MockPlanner(plan),
                    banned_phrases=["well tolerated"], required_names=["n_treated"])
    print(f"\n[{name}] {run.text}")
    print(run.scorecard())
    print(run.ledger_table())
