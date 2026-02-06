from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.agents.intake import intake_agent
from src.agents.policy_retrieval import policy_retrieval_agent
from src.agents.compliance import compliance_agent
from src.agents.market import market_insight_agent
from src.agents.listing_generator import listing_generator_agent
from src.agents.eval import eval_agent

def run_intake(state: AgentState):
    return intake_agent.run(state)

def run_policy_retrieval(state: AgentState):
    return policy_retrieval_agent.run(state)

def run_compliance(state: AgentState):
    return compliance_agent.run(state)

def run_market(state: AgentState):
    return market_insight_agent.run(state)

def run_listing_generator(state: AgentState):
    return listing_generator_agent.run(state)

def run_eval(state: AgentState):
    return eval_agent.run(state)

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("intake", run_intake)
workflow.add_node("policy_retrieval", run_policy_retrieval)
workflow.add_node("compliance", run_compliance)
workflow.add_node("market", run_market)
workflow.add_node("listing_generator", run_listing_generator)
workflow.add_node("eval", run_eval)

# Define edges
workflow.set_entry_point("intake")
workflow.add_edge("intake", "policy_retrieval")
workflow.add_edge("policy_retrieval", "compliance")
workflow.add_edge("compliance", "market")
workflow.add_edge("market", "listing_generator")
workflow.add_edge("listing_generator", "eval")
workflow.add_edge("eval", END)

# Compile
app = workflow.compile()
