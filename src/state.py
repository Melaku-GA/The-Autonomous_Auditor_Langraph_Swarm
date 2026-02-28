"""
State definitions for the Automaton Auditor.

This module defines the typed state structures used throughout the LangGraph
orchestration. Using Pydantic ensures strict typing and validation at every
node transition.
"""

import operator
from typing import Annotated, Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Evidence(BaseModel):
    """Represents a piece of forensic evidence collected by detectives."""
    
    goal: str = Field(
        description="The investigative goal this evidence addresses"
    )
    found: bool = Field(
        description="Whether the artifact or pattern was successfully found"
    )
    content: Optional[str] = Field(
        default=None,
        description="The actual content or code snippet extracted"
    )
    location: str = Field(
        description="File path, commit hash, or URL where evidence was found"
    )
    rationale: str = Field(
        description="Explanation of why this evidence supports or refutes the goal"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for this evidence (0-1)"
    )
    evidence_class: str = Field(
        description="Classification of evidence (e.g., 'Git Forensic', 'State Management')"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="When this evidence was collected"
    )


class JudicialOpinion(BaseModel):
    """Represents a judge's evaluation of evidence for a specific criterion."""
    
    judge: Literal["Prosecutor", "Defense", "TechLead"] = Field(
        description="The persona of the judge rendering this opinion"
    )
    criterion_id: str = Field(
        description="The rubric criterion this opinion addresses"
    )
    criterion_name: str = Field(
        description="Human-readable name of the criterion"
    )
    score: int = Field(
        ge=1, le=5,
        description="Score from 1-5 based on the rubric"
    )
    argument: str = Field(
        description="The judge's reasoning for this score"
    )
    cited_evidence: List[str] = Field(
        description="List of evidence IDs or locations cited in the argument"
    )
    charge: Optional[str] = Field(
        default=None,
        description="If Prosecutor, the specific violation being charged"
    )
    mitigation: Optional[str] = Field(
        default=None,
        description="If Defense, the mitigation argument being made"
    )
    technical_assessment: Optional[str] = Field(
        default=None,
        description="If TechLead, the technical viability assessment"
    )


class RubricDimension(BaseModel):
    """A single dimension of the evaluation rubric."""
    
    id: str = Field(description="Unique identifier for the dimension")
    name: str = Field(description="Human-readable name")
    target_artifact: Literal["github_repo", "pdf_report", "images"] = Field(
        description="What type of artifact this dimension evaluates"
    )
    forensic_instruction: str = Field(
        description="Instructions for detectives collecting evidence"
    )
    judicial_logic: Dict[str, str] = Field(
        description="Persona-specific judicial instructions"
    )


class AgentState(TypedDict):
    """
    The master state dict for the entire audit workflow.
    
    Uses Annotated with reducers to handle parallel execution:
    - evidences: Uses operator.ior (OR) to merge dicts from parallel detectives
    - opinions: Uses operator.add to append lists from parallel judges
    """
    
    # Input parameters
    repo_url: str
    pdf_path: str
    has_repo: bool  # Whether GitHub repo input is provided
    has_pdf: bool   # Whether PDF report input is provided
    repo_local_path: Optional[str]
    
    # Rubric configuration
    rubric_dimensions: List[RubricDimension]
    
    # Evidence collected by detectives (merged via reducer)
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]
    
    # Judicial opinions from judges (appended via reducer)
    opinions: Annotated[List[JudicialOpinion], operator.add]
    
    # Intermediate states
    git_history: Optional[List[Dict[str, str]]]
    repo_structure: Optional[Dict[str, Any]]
    pdf_content: Optional[str]
    extracted_images: Optional[List[str]]
    
    # Final output
    final_report: str
    final_scores: Dict[str, int]
    remediation_plan: List[str]


class EvidenceAggregationState(BaseModel):
    """Intermediate state for evidence aggregation before judicial review."""
    
    all_evidence: List[Evidence] = Field(default_factory=list)
    missing_evidence_goals: List[str] = Field(default_factory=list)
    evidence_summary: str = Field(
        description="Natural language summary of all collected evidence"
    )


class SynthesisState(BaseModel):
    """State for the Chief Justice synthesis phase."""
    
    all_opinions: List[JudicialOpinion] = Field(default_factory=list)
    conflict_summary: Dict[str, Dict[str, Any]] = Field(
        description="Summary of conflicts between judges per criterion"
    )
    final_verdict: str = Field(
        description="The final verdict text"
    )
    scores: Dict[str, int] = Field(
        description="Final scores per criterion"
    )
    remediation: List[str] = Field(
        description="Actionable remediation steps"
    )
