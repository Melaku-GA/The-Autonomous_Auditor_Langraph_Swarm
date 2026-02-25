"""
Tools package for the Automaton Auditor.

This package contains the forensic tools used by the Detective Layer:
- RepoInvestigator: Code and repository analysis
- DocAnalyst: PDF document analysis
- VisionInspector: Diagram and image analysis
"""

from src.tools.repo_investigator import (
    RepoInvestigator,
    GitForensicReport,
    StateManagementReport,
    GraphOrchestrationReport,
    SecurityReport,
    StructuredOutputReport
)

from src.tools.doc_analyst import (
    DocAnalyst,
    TheoreticalDepthReport,
    ClaimVerificationReport,
    DocumentStructureReport,
    analyze_pdf
)

from src.tools.vision_inspector import (
    VisionInspector,
    DiagramClassification,
    SwarmVisualReport,
    inspect_diagram
)

__all__ = [
    # RepoInvestigator
    'RepoInvestigator',
    'GitForensicReport',
    'StateManagementReport', 
    'GraphOrchestrationReport',
    'SecurityReport',
    'StructuredOutputReport',
    # DocAnalyst
    'DocAnalyst',
    'TheoreticalDepthReport',
    'ClaimVerificationReport',
    'DocumentStructureReport',
    'analyze_pdf',
    # VisionInspector
    'VisionInspector',
    'DiagramClassification',
    'SwarmVisualReport',
    'inspect_diagram',
]
