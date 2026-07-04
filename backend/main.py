# ─── STANDARD PACKAGES & MIDDLEWARE IMPORTS ─────────────────────────────
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Initialize local environment keys
load_dotenv()

# ─── MODERNIZE LANGCHAIN IMPORTS (BYPASSING BROKEN NAMESPACES) ─────────
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ─── APP BASE ───────────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory mock store tracking the last active simulation state
STATE_DB: Dict[str, Any] = {
    "last_decision": None,
    "last_transcript": [],
    "spr_days": 9.5,
    "last_summary": "System tracking baseline parameters. Nominal operation limits active."
}

class CrisisInput(BaseModel):
    target_chokepoint: str
    simulated_intensity: float
    compromise_domestic_pipeline: bool

class ChatInput(BaseModel):
    message: str

# ─── CORE AGENTIC SIMULATION LOGIC ──────────────────────────────────────
def execute_simulation_logic(chokepoint: str, intensity: float, pipeline_fault: bool) -> dict:
    intensity_pct = int(intensity * 100)
    summary = f"CRITICAL SHOCK ACTIVE: Forced {intensity_pct}% failure across {chokepoint} corridor."
    if pipeline_fault:
        summary += " Compounding cyber-kinetic onshore asset strike confirmed."
        
    adjusted_spr = max(9.5 - (intensity * 4.5), 1.2) if pipeline_fault else max(9.5 - (intensity * 2.5), 3.0)
    
    mock_transcript = [
        {"role": "chaos_monkey", "content": f"Injected {intensity_pct}% vector block at {chokepoint}."},
        {"role": "safety_sentinel", "content": f"SPR warning issued. Core margins dropped to {adjusted_spr:.1f} days cover."},
        {"role": "cost_appraisal", "content": f"Freight rates re-indexed. Alternative routing required due to high volatility risk."},
        {"role": "graph_solver", "content": f"Recalculating multi-commodity matrix bounds. Rerouting traffic through alternative channels."}
    ]
    
    decision_payload = {
        "active_visual_route": [chokepoint, "Arabian Sea", "Paradip Port"],
        "routing_cost_metric": 84.50 + (intensity * 35.0),
        "allocated_crude_source": "Alternative Strategic Storage Allocation",
        "reconciliation_summary": summary
    }
    
    STATE_DB["last_decision"] = decision_payload
    STATE_DB["last_transcript"] = mock_transcript
    STATE_DB["spr_days"] = round(adjusted_spr, 1)
    STATE_DB["last_summary"] = summary
    
    return {
        "simulation_alert": summary,
        "adjusted_spr_days_remaining": round(adjusted_spr, 1),
        "complete_chaos_execution_audit": mock_transcript,
        "final_decision_payload": decision_payload
    }

# ─── TOOLS CONFIGURATION ────────────────────────────────────────────────
@tool
def trigger_black_swan_simulation(target_chokepoint: str, simulated_intensity: float, compromise_domestic_pipeline: bool) -> str:
    """Useful when the user wants to simulate an attack, push a crisis vector, force a failure, or test a disruption strategy on a maritime chokepoint."""
    result = execute_simulation_logic(target_chokepoint, simulated_intensity, compromise_domestic_pipeline)
    return f"SIMULATION_EXECUTED: {result['simulation_alert']}. SPR dropped to {result['adjusted_spr_days_remaining']} days cover."

@tool
def query_active_audit_logs() -> str:
    """Useful when the user asks 'why' a routing decision was made, asks for reasoning behind an action, or requests an audit breakdown of the current logs."""
    context_summary = f"Current Status: {STATE_DB['last_summary']}. SPR Cover: {STATE_DB['spr_days']} days. "
    if STATE_DB['last_decision']:
        context_summary += f"Route cost is index ${STATE_DB['last_decision']['routing_cost_metric']} per barrel."
    return f"AUDIT_DATA: {context_summary} Execution Path details: {json.dumps(STATE_DB['last_transcript'])}"

# ─── SYSTEM INITIALIZATION USING LCEL (STABLE PROMPT RUNNER) ───────────
tools_map = {
    "trigger_black_swan_simulation": trigger_black_swan_simulation,
    "query_active_audit_logs": query_active_audit_logs
}

# Bind tools straight to the LLM interface
llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_with_tools = llm.bind_tools([trigger_black_swan_simulation, query_active_audit_logs])

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the Aegis Strategic Copilot, an elite geopolitical energy intelligence AI. "
               "Analyze the user's intent. If they command a scenario change, use your tool execution calls to implement it. "
               "If they ask for reasoning or statistics, pull from the active audits. "
               "Provide concise, highly scannable bullet points for your final answer summary response."),
    ("human", "{input}"),
])

# Build our execution chain link
agent_chain = prompt | llm_with_tools

# ─── ENDPOINTS ─────────────────────────────────────────────────────────
@app.post("/chaos/inject_crisis")
async def inject_crisis(payload: CrisisInput):
    try:
        return execute_simulation_logic(payload.target_chokepoint, payload.simulated_intensity, payload.compromise_domestic_pipeline)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chaos/chat")
async def copilot_chat(payload: ChatInput):
    try:
        # 1. Try to invoke the live OpenAI LangChain Agent Core
        ai_msg = agent_chain.invoke({"input": payload.message})
        output_text = ai_msg.content
        
        tool_calls = getattr(ai_msg, "tool_calls", None) or ai_msg.additional_kwargs.get("tool_calls", [])
        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)
                tool_args = tool_call.get("args") if isinstance(tool_call, dict) else getattr(tool_call, "args", {})
                if tool_name in tools_map:
                    output_text = tools_map[tool_name].invoke(tool_args)

    except Exception as api_exception:
        # 2. FAIL-SAFE FALLBACK: If OpenAI/Quota fails, switch to local execution logic
        print(f"FALLBACK ACTIVATED due to API Exception: {str(api_exception)}")
        user_query = payload.message.lower()

        if any(word in user_query for word in ["simulate", "disrupt", "force", "trigger", "attack"]):
            # Auto-extract parameters from prompt keywords to simulate copilot execution
            target = "Red Sea" if "red sea" in user_query else "Arabian Sea" if "arabian" in user_query else "Strait of Hormuz"
            intensity_val = 0.60 if "60" in user_query else 0.50
            cyber_kinetic = "pipeline" in user_query or "cyber" in user_query
            
            # Execute logic block internally to update the global memory maps
            sim_res = execute_simulation_logic(target, intensity_val, cyber_kinetic)
            output_text = f"### ⚡ FAIL-SAFE EXECUTION INITIATED\n* **Target Corridor:** {target}\n* **Disruption Matrix:** Locked at {int(intensity_val*100)}%\n* **System Action:** Disruption successfully injected into downstream network models. SPR level re-indexed to {sim_res['adjusted_spr_days_remaining']} days cover."
        else:
            # Fallback for routing analysis queries
            current_cost = STATE_DB["last_decision"]["routing_cost_metric"] if STATE_DB["last_decision"] else 84.50
            output_text = f"### 📋 LOCAL CORE ANALYTICAL REPORT\n* **Routing Constraint:** Multi-commodity flow optimized for least-cost path variants.\n* **Current Cost Index:** ${current_cost:.2f} per barrel equivalent.\n* **Operational Status:** Bypassing high-volatility transit lanes to preserve regional supply line stability."

    # Return valid payload data block to keep Next.js happy
    return {
        "output": output_text,
        "current_state": {
            "simulation_alert": STATE_DB["last_summary"],
            "adjusted_spr_days_remaining": STATE_DB["spr_days"],
            "complete_chaos_execution_audit": STATE_DB["last_transcript"],
            "final_decision_payload": STATE_DB["last_decision"]
        }
    }