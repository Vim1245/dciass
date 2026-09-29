from langgraph.graph import StateGraph, START, END

from graph.state import BusinessState
from graph.nodes import (
    plan_node,
    retrieve_node,
    decision_node,
    action_node,
    final_response_node,
)


def route_action(state: BusinessState):
    """
    Action router:
    - CREATE_TICKET: executes external action node (MCP create_ticket).
    - MORE_INFORMATION_REQUIRED / NO_ACTION: proceeds directly to final response.
    """
    decision = state.get("decision", "NO_ACTION")
    if decision == "CREATE_TICKET":
        return "action"
    return "final_response"


def create_business_graph():
    """
    Build the complete Agentic AI Business Support Workflow:
    START
      ↓
    UNDERSTAND & PLAN (plan_node)
      ↓
    SELECTIVE RETRIEVAL (retrieve_node: MCP Customer / Complaint / RAG Policy)
      ↓
    BUSINESS ANALYSIS & DECISION (decision_node: Ollama analysis)
      ↓
    DECISION ROUTER
      ├── CREATE_TICKET → ACTION (action_node: MCP create_ticket) → FINAL RESPONSE
      └── MORE_INFO / NO_ACTION → FINAL RESPONSE
      ↓
    END
    """
    graph = StateGraph(BusinessState)  # type: ignore

    # Register workflow nodes
    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("decision", decision_node)
    graph.add_node("action", action_node)
    graph.add_node("final_response", final_response_node)

    # Linear planning and selective retrieval
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "decision")

    # Conditional branching based on structured business decision
    graph.add_conditional_edges(
        "decision",
        route_action,
        {
            "action": "action",
            "final_response": "final_response",
        },
    )

    # Action node flows into final response
    graph.add_edge("action", "final_response")

    # Terminal edge
    graph.add_edge("final_response", END)

    return graph.compile()


business_graph = create_business_graph()