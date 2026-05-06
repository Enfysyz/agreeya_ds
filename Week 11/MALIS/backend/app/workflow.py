from langgraph.graph import StateGraph, END
from app.schema import WorkflowState
from app.agents import fraud_detection_node, funding_node, billing_node, compliance_node

def build_logistics_graph(checkpointer=None):
    workflow = StateGraph(WorkflowState)

    # Add agent nodes
    workflow.add_node("fraud", fraud_detection_node)
    workflow.add_node("funding", funding_node)
    workflow.add_node("billing", billing_node)
    workflow.add_node("compliance", compliance_node)

    # Define the strict pipeline dependencies
    workflow.set_entry_point("fraud")
    workflow.add_edge("fraud", "funding")
    workflow.add_edge("funding", "billing")
    workflow.add_edge("billing", "compliance")
    workflow.add_edge("compliance", END)

    # Compile with the checkpointer passed from main.py
    return workflow.compile(checkpointer=checkpointer)