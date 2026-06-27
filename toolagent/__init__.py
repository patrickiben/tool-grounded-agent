"""tool-grounded-agent -- a grounding HARNESS for agentic drafting (not a safe agent).

A tool-calling "agent" (a deterministic scripted stand-in for a function-calling
LLM) drafts a clinical adverse-event narrative by filling template slots ONLY
from a recorded tool-call ledger, then the assembled text is re-validated by a
vendored numguard-style guard. Two independent layers:

  Layer 1 (structural)  -- every template slot must be filled by a real tool
                           result, or it renders as «UNSOURCED».
  Layer 2 (text guard)  -- on the final text: numbers must be allowed facts
                           (numbers_grounded) AND must have actually been
                           produced by a tool this run (numbers_from_ledger);
                           plus banned-claim and required-fact checks.

The centerpiece: an agent that recites a real, correct fact it never queried
PASSES numguard's set-membership but FAILS the ledger provenance check -- proving
the two layers are non-redundant. Zero third-party dependencies.
"""
from .agent import AgentRun, run_agent
from .facts import Fact, FactStore
from .guard import evaluate
from .loader import candidate_plan, load_scenario
from .planner import MockPlanner, Plan, Planner, ReplayPlanner, Task
from .render import render, slot_names
from .report import Finding, Report
from .tools import BUILTIN_TOOLS, ToolCall, ToolLedger, ToolRegistry, ToolResult

__all__ = [
    "Fact", "FactStore", "ToolResult", "ToolCall", "ToolLedger", "ToolRegistry",
    "BUILTIN_TOOLS", "render", "slot_names", "evaluate", "Finding", "Report",
    "run_agent", "AgentRun", "Planner", "MockPlanner", "ReplayPlanner", "Task",
    "Plan", "load_scenario", "candidate_plan",
]
__version__ = "0.1.0"
