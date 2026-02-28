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
from langchain_ollama import ChatOllama
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

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
# Local LangSmith-Style JSON Trace Handler
# ============================================================================

class LocalTraceHandler(BaseCallbackHandler):
    """
    Custom callback handler that saves LangSmith-style traces to local JSON files.
    Saves traces to the langsmith_logs/ directory.
    """
    
    def __init__(self, log_dir: str = "langsmith_logs"):
        self.log_dir = log_dir
        self.traces = []
        self.current_trace = None
        os.makedirs(log_dir, exist_ok=True)
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts processing."""
        try:
            trace_id = kwargs.get('run_id')
            if trace_id:
                trace_id = str(trace_id)
            else:
                trace_id = 'unknown'
            
            # Safely get the model name
            model_name = 'unknown'
            if serialized:
                name = serialized.get('name') or serialized.get('id')
                if name:
                    model_name = name if isinstance(name, str) else str(name[-1] if name else 'unknown')
            
            self.current_trace = {
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat(),
                "event": "llm_start",
                "model": model_name,
                "prompts": [p[:500] + "..." if len(p) > 500 else p for p in prompts] if prompts else [],
            }
        except Exception as e:
            print(f"Error in on_llm_start: {e}")
            self.current_trace = None
    
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Called when LLM finishes processing."""
        try:
            if self.current_trace:
                self.current_trace["event"] = "llm_end"
                # Extract token usage if available
                try:
                    if response.llm_output:
                        self.current_trace["llm_output"] = str(response.llm_output)[:500]
                except:
                    pass
                self.traces.append(self.current_trace)
                self.current_trace = None
        except Exception as e:
            print(f"Error in on_llm_end: {e}")
            if self.current_trace:
                self.traces.append(self.current_trace)
                self.current_trace = None
    
    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called when LLM errors."""
        if self.current_trace:
            self.current_trace["event"] = "llm_error"
            self.current_trace["error"] = str(error)[:500]
            self.traces.append(self.current_trace)
            self.current_trace = None
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        """Called when a chain/node starts."""
        try:
            trace_id = kwargs.get('run_id')
            if trace_id:
                trace_id = str(trace_id)
            else:
                trace_id = 'unknown'
            
            # Safely get the node name
            node_name = 'unknown'
            if serialized:
                name = serialized.get('name') or serialized.get('id')
                if name:
                    node_name = name if isinstance(name, str) else str(name[-1] if name else 'unknown')
            
            self.current_trace = {
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat(),
                "event": "chain_start",
                "node": node_name,
                "inputs": self._sanitize_inputs(inputs)
            }
        except Exception as e:
            print(f"Error in on_chain_start: {e}")
            self.current_trace = None
    
    def on_chain_end(self, outputs: Any, **kwargs) -> None:
        """Called when a chain/node finishes."""
        try:
            if self.current_trace:
                self.current_trace["event"] = "chain_end"
                self.current_trace["outputs"] = self._sanitize_outputs(outputs)
                self.traces.append(self.current_trace)
                self.current_trace = None
        except Exception as e:
            print(f"Error in on_chain_end: {e}")
            if self.current_trace:
                self.traces.append(self.current_trace)
                self.current_trace = None
    
    def on_chain_error(self, error: Exception, **kwargs) -> None:
        """Called when a chain/node errors."""
        if self.current_trace:
            self.current_trace["event"] = "chain_error"
            self.current_trace["error"] = str(error)[:500]
            self.traces.append(self.current_trace)
            self.current_trace = None
    
    def _sanitize_inputs(self, inputs: Any) -> Any:
        """Sanitize inputs for logging (truncate long values)."""
        if inputs is None:
            return "None"
        
        if isinstance(inputs, dict):
            sanitized = {}
            for k, v in inputs.items():
                if v is None:
                    sanitized[k] = "None"
                elif isinstance(v, str) and len(v) > 1000:
                    sanitized[k] = v[:1000] + "... [truncated]"
                elif hasattr(v, 'to_json'):  # Handle ChatPromptValue etc
                    sanitized[k] = str(v)[:1000]
                else:
                    sanitized[k] = str(v)[:1000]
            return sanitized
        else:
            return str(inputs)[:1000]
    
    def _sanitize_outputs(self, outputs: Any) -> Any:
        """Sanitize outputs for logging."""
        return self._sanitize_inputs(outputs)
    
    def save_traces(self, filename: str = None) -> str:
        """Save all collected traces to a JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trace_{timestamp}.json"
        
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "exported_at": datetime.now().isoformat(),
                "total_traces": len(self.traces),
                "traces": self.traces
            }, f, indent=2, ensure_ascii=False)
        
        return filepath


def create_trace_handler() -> LocalTraceHandler:
    """Create a new trace handler instance."""
    return LocalTraceHandler(log_dir="langsmith_logs")


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


def check_detective_failure(state: AgentState) -> str:
    """
    Check if any detective failed and route accordingly.
    
    Returns:
        "success" if detective succeeded, "failure" if it failed
    """
    # Check for errors in the state
    if state.get('error'):
        return "failure"
    
    # Check if evidence was collected
    evidences = state.get('evidences', {})
    if not evidences or all(not v for v in evidences.values()):
        return "failure"
    
    return "success"


def should_aggregate_evidence(state: AgentState) -> str:
    """
    Determine if evidence aggregation should proceed.
    
    Checks:
    - All detectives have run (have evidences or errors)
    - At least some evidence was collected
    """
    evidences = state.get('evidences', {})
    
    # Check if we have evidence from any detective
    has_any_evidence = any(
        isinstance(v, list) and len(v) > 0 
        for v in evidences.values()
    )
    
    # Check for errors
    has_error = state.get('error') is not None
    
    # If we have evidence OR an error (even partial success), proceed
    if has_any_evidence or has_error:
        return "aggregate"
    
    # No evidence and no error - might still be running
    return "wait"


def check_judges_completion(state: AgentState) -> str:
    """
    Check if all judges have completed their assessments.
    
    Returns:
        END if complete, otherwise continue
    """
    opinions = state.get('opinions', [])
    rubric_dims = state.get('rubric_dimensions', [])
    
    # If we have opinions covering all rubric dimensions, we're done
    if opinions and len(rubric_dims) > 0:
        opinion_criteria = set(op.criterion_id for op in opinions)
        required_criteria = set(d.id for d in rubric_dims)
        
        if opinion_criteria >= required_criteria:
            return END
    
    # Also check if we have a final report
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
        # Try to use Ollama (local), fall back to OpenAI if not available
        try:
            llm = ChatOllama(model="llama3", temperature=0.2)
        except Exception:
            llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    
    # Initialize default vision LLM if not provided
    if vision_llm is None:
        try:
            vision_llm = ChatOllama(model="llama3", temperature=0.2)
        except Exception:
            vision_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add the rubric loader node
    workflow.add_node("load_rubric", load_rubric)
    
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
    
    # Load rubric transitions - fan-out to all detectives
    workflow.add_edge("load_rubric", "repo_investigator")
    workflow.add_edge("load_rubric", "doc_analyst")
    workflow.add_edge("load_rubric", "vision_inspector")
    
    # ========================================================================
    # Detective Layer with Conditional Edges for Failures
    # ========================================================================
    
    # Add conditional edges for repo_investigator failure handling
    workflow.add_conditional_edges(
        "repo_investigator",
        check_detective_failure,
        {
            "success": "evidence_aggregator",
            "failure": "evidence_aggregator"  # Still aggregate, but with error evidence
        }
    )
    
    # Add conditional edges for doc_analyst failure handling
    workflow.add_conditional_edges(
        "doc_analyst",
        check_detective_failure,
        {
            "success": "evidence_aggregator",
            "failure": "evidence_aggregator"
        }
    )
    
    # Add conditional edges for vision_inspector failure handling
    workflow.add_conditional_edges(
        "vision_inspector",
        check_detective_failure,
        {
            "success": "evidence_aggregator",
            "failure": "evidence_aggregator"
        }
    )
    
    # Parallel detectives fan-in to evidence aggregator
    # Note: In LangGraph, parallel nodes completing triggers their edges
    # The aggregator waits for all three to complete before proceeding
    
    # Evidence aggregation to judicial layer (fan-out)
    workflow.add_edge("evidence_aggregator", "prosecutor")
    workflow.add_edge("evidence_aggregator", "defense")
    workflow.add_edge("evidence_aggregator", "techlead")
    
    # All judges run in parallel, then fan-in to chief justice
    # Connect judges to chief_justice (fan-in)
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("techlead", "chief_justice")
    
    # Add conditional edge for judges completion check
    workflow.add_conditional_edges(
        "chief_justice",
        check_completion,
        {
            END: END,
            "continue": "chief_justice"  # If not complete, stay (shouldn't happen)
        }
    )
    
    # Chief justice to end (direct edge as fallback)
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
