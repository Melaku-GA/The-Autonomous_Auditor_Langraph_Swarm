"""
Automaton Auditor - Deep LangGraph Swarm for Autonomous Governance

This package provides a hierarchical multi-agent system for automated
code governance and quality assurance.

Architecture:
- Layer 1: Detective Layer (Forensic evidence collection)
- Layer 2: Judicial Layer (Dialectical evaluation)
- Layer 3: Supreme Court (Synthesis and verdict)

Usage:
    from src.graph import run_audit
    
    result = run_audit(
        repo_url="https://github.com/user/repo",
        pdf_path="./report.pdf"
    )
    
    print(result['final_report'])
"""

from src.graph import (
    create_audit_graph,
    run_audit,
    run_audit_stream
)

from src.state import (
    AgentState,
    Evidence,
    JudicialOpinion,
    RubricDimension
)

__version__ = "2.0.0"

__all__ = [
    'create_audit_graph',
    'run_audit',
    'run_audit_stream',
    'AgentState',
    'Evidence',
    'JudicialOpinion',
    'RubricDimension',
]
