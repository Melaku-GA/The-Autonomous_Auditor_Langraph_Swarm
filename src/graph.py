"""
Automaton Auditor - LangGraph Orchestration

This module defines the hierarchical StateGraph that orchestrates
the multi-agent audit swarm.

Architecture:
    Layer 1 (Detective Layer):
        - RepoInvestigator (parallel)
        - DocAnalyst (parallel)  
        - VisionInspector (parallel)
                    ↓ Fan-In
    Layer 2 (Judicial Layer):
        - Prosecutor (parallel)
        - Defense (parallel)
        - TechLead (parallel)
                    ↓ Fan-In
    Layer 3 (Supreme Court):
        - ChiefJustice (synthesis)
                    ↓
        - Final Report
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from operator import ior, add

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

from src.state import AgentState, RubricDimension
from src.nodes.detectives import (
    create_repo_investigator_node,
    create_doc_analyst_node,
    create_vision_inspector_node
)
from src.nodes.judges import (
    create_prosecutor_judge,
    create_defense_judge,
    create_techlead_judge
)
from src.nodes.justice import (
    create_chief_justice_node,
    create_evidence_aggregator_node
)


# ============================================================================
# Graph State Reducers
# ============================================================================

def reduce_evidences(existing: Dict, new: Dict) -> Dict:
    """
    Reducer for evidence dictionaries.
    Uses operator.ior to merge dicts from parallel agents.
    """
    if existing is None:
        existing = {}
    if new is None:
        new = {}
    
    # Merge the dictionaries
    result = dict(existing)
    for key, value in new.items():
        if key in result:
            # Append to existing list or merge
            if isinstance(result[key], list) and isinstance(value, list):
                result[key].extend(value)
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result


def reduce_opinions(existing: List, new: List) -> List:
    """
    Reducer for opinion lists.
    Uses operator.add to append lists from parallel judges.
    """
    if existing is None:
        existing = []
    if new is None:
        new = []
    
    return existing + new


# ============================================================================
# Node Functions
# ============================================================================

def load_rubric(state: AgentState) -> AgentState:
    """Load the rubric dimensions from the JSON file."""
    rubric_path = os.path.join(os.path.dirname(__file__), '..', 'rubric', 'week2_rubric.json')
    
    if not os.path.exists(rubric_path):
        # Use default rubric
        return state
    
    with open(rubric_path, 'r') as f:
        rubric_data = json.load(f)
    
    dimensions = [RubricDimension(**d) for d in rubric_data['dimensions']]
    
    return {
        **state,
        'rubric_dimensions': dimensions
    }


def should_run_vision(state: AgentState) -> bool:
    """Conditional edge: decide if vision analysis is needed."""
    # Always run - can be configured based on needs
    return True


def check_completion(state: AgentState) -> str:
    """Conditional edge: check if audit is complete."""
    if state.get('final_report'):
        return END
    return "continue"


# ============================================================================
# Graph Construction
# ============================================================================

def create_audit_graph(
    llm=None,
    vision_llm=None,
    checkpointer=None
) -> StateGraph:
    """
    Create the Automaton Auditor StateGraph.
    
    Args:
        llm: LLM for judges (default: GPT-4o)
        vision_llm: Vision-capable LLM for diagram analysis
        checkpointer: LangGraph checkpointer for memory
        
    Returns:
        Compiled StateGraph
    """
    
    # Initialize default LLM if not provided
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # ========================================================================
    # Layer 1: Detective Layer (Parallel Fan-Out)
    # ========================================================================
    
    # Add detective nodes
    workflow.add_node("repo_investigator", create_repo_investigator_node())
    workflow.add_node("doc_analyst", create_doc_analyst_node())
    workflow.add_node("vision_inspector", create_vision_inspector_node(vision_llm))
    
    # ========================================================================
    # Layer 2: Evidence Aggregation (Fan-In)
    # ========================================================================
    
    workflow.add_node("evidence_aggregator", create_evidence_aggregator_node())
    
    # ========================================================================
    # Layer 3: Judicial Layer (Parallel Fan-Out)
    # ========================================================================
    
    workflow.add_node("prosecutor", create_prosecutor_judge(llm))
    workflow.add_node("defense", create_defense_judge(llm))
    workflow.add_node("techlead", create_techlead_judge(llm))
    
    # ========================================================================
    # Layer 4: Supreme Court (Synthesis)
    # ========================================================================
    
    workflow.add_node("chief_justice", create_chief_justice_node())
    
    # ========================================================================
    # Define Edges
    # ========================================================================
    
    # Entry point - load rubric first
    workflow.set_entry_point("load_rubric")
    
    # Load rubric transitions
    workflow.add_edge("load_rubric", "repo_investigator")
    workflow.add_edge("load_rubric", "doc_analyst")
    workflow.add_edge("load_rubric", "vision_inspector")
    
    # Detective parallel execution - all detectives run simultaneously
    # Then fan-in to evidence aggregator
    workflow.add_edge("repo_investigator", "evidence_aggregator")
    workflow.add_edge("doc_analyst", "evidence_aggregator")
    workflow.add_edge("vision_inspector", "evidence_aggregator")
    
    # Evidence aggregation to judicial layer (fan-out)
    workflow.add_edge("evidence_aggregator", "prosecutor")
    workflow.add_edge("evidence_aggregator", "defense")
    workflow.add_edge("evidence_aggregator", "techlead")
    
    # All judges run in parallel, then fan-in to chief justice
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("techlead", "chief_justice")
    
    # Chief justice to end
    workflow.add_edge("chief_justice", END)
    
    # ========================================================================
    # Compile the graph
    # ========================================================================
    
    if checkpointer:
        graph = workflow.compile(checkpointer=checkpointer)
    else:
        graph = workflow.compile()
    
    return graph


# ============================================================================
# Convenience Functions
# ============================================================================

def run_audit(
    repo_url: str,
    pdf_path: str,
    llm=None,
    vision_llm=None,
    config=None
) -> Dict[str, Any]:
    """
    Run a complete audit on a repository and PDF report.
    
    Args:
        repo_url: GitHub repository URL
        pdf_path: Path to the PDF architectural report
        llm: Optional LLM override
        vision_llm: Optional vision LLM override
        config: Optional configuration dict
        
    Returns:
        Dict with final_report, scores, and remediation_plan
    """
    
    # Create the graph
    graph = create_audit_graph(llm=llm, vision_llm=vision_llm)
    
    # Initial state
    initial_state = {
        'repo_url': repo_url,
        'pdf_path': pdf_path,
        'repo_local_path': None,
        'rubric_dimensions': [],
        'evidences': {},
        'opinions': [],
        'git_history': None,
        'repo_structure': None,
        'pdf_content': None,
        'extracted_images': None,
        'final_report': '',
        'final_scores': {},
        'remediation_plan': []
    }
    
    # Run the graph
    result = graph.invoke(initial_state, config=config)
    
    return {
        'final_report': result.get('final_report', ''),
        'final_scores': result.get('final_scores', {}),
        'remediation_plan': result.get('remediation_plan', []),
        'total_evidence': sum(
            len(v) for v in result.get('evidences', {}).values()
        ),
        'total_opinions': len(result.get('opinions', []))
    }


def run_audit_stream(
    repo_url: str,
    pdf_path: str,
    llm=None,
    vision_llm=None
):
    """
    Run audit with streaming output for progress tracking.
    
    Yields:
        State updates at each node
    """
    
    graph = create_audit_graph(llm=llm, vision_llm=vision_llm)
    
    initial_state = {
        'repo_url': repo_url,
        'pdf_path': pdf_path,
        'repo_local_path': None,
        'rubric_dimensions': [],
        'evidences': {},
        'opinions': [],
        'git_history': None,
        'repo_structure': None,
        'pdf_content': None,
        'extracted_images': None,
        'final_report': '',
        'final_scores': {},
        'remediation_plan': []
    }
    
    for state in graph.stream(initial_state):
        yield state


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python -m src.graph <repo_url> <pdf_path>")
        print("Example: python -m src.graph https://github.com/user/repo ./report.pdf")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    pdf_path = sys.argv[2]
    
    print("Starting Automaton Auditor...")
    print(f"Repository: {repo_url}")
    print(f"Report: {pdf_path}")
    print()
    
    result = run_audit(repo_url, pdf_path)
    
    print("\n" + "="*60)
    print("AUDIT COMPLETE")
    print("="*60)
    print(f"\nOverall Score: {sum(result['final_scores'].values()) / len(result['final_scores']) if result['final_scores'] else 0:.2f}/5")
    print(f"Evidence Collected: {result['total_evidence']}")
    print(f"Judicial Opinions: {result['total_opinions']}")
    print("\nScores by Criterion:")
    for criterion, score in result['final_scores'].items():
        print(f"  {criterion}: {score}/5")
    
    print("\nRemediation Plan:")
    for item in result['remediation_plan']:
        print(f"  - {item}")
    
    print("\n" + "="*60)
    print("FULL REPORT:")
    print("="*60)
    print(result['final_report'])
