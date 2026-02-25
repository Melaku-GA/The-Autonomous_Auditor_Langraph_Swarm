"""
Nodes package for the Automaton Auditor.

This package contains the node implementations:
- detectives: Forensic evidence collection agents
- judges: Dialectical bench with three personas
- justice: Chief Justice synthesis engine
"""

from src.nodes.detectives import (
    create_repo_investigator_node,
    create_doc_analyst_node,
    create_vision_inspector_node,
    run_parallel_detectives
)

from src.nodes.judges import (
    create_prosecutor_judge,
    create_defense_judge,
    create_techlead_judge,
    run_parallel_judges
)

from src.nodes.justice import (
    create_chief_justice_node,
    create_evidence_aggregator_node,
    resolve_conflict,
    SYNTHESIS_RULES
)

__all__ = [
    # Detectives
    'create_repo_investigator_node',
    'create_doc_analyst_node',
    'create_vision_inspector_node',
    'run_parallel_detectives',
    # Judges
    'create_prosecutor_judge',
    'create_defense_judge',
    'create_techlead_judge',
    'run_parallel_judges',
    # Justice
    'create_chief_justice_node',
    'create_evidence_aggregator_node',
    'resolve_conflict',
    'SYNTHESIS_RULES',
]
