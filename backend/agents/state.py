# backend/agents/state.py
from typing import TypedDict, List, Dict, Any, Annotated
import operator

class AgentState(TypedDict):
    active_disruptions: List[Dict[str, Any]]
    current_spr_days: float
    calculated_route: List[str]
    route_cost_metric: float
    chemically_viable_suppliers: List[Dict[str, Any]]
    debate_transcript: Annotated[List[Dict[str, str]], operator.add]
    final_procurement_decision: Dict[str, Any]
    current_turn: int
    max_turns: int
    # New state variables tracking individual agent stances
    cost_agent_stance: str
    safety_agent_stance: str