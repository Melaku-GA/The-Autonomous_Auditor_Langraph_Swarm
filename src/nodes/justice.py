"""
Chief Justice Node: The Supreme Court

This module implements the synthesis engine that resolves conflicts
between the three judges and generates the final audit report.

The Chief Justice applies deterministic rules to resolve dialectical
conflicts and produce actionable remediation plans.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

from src.state import JudicialOpinion, Evidence


# ============================================================================
# Synthesis Rules (from Rubric)
# ============================================================================

SYNTHESIS_RULES = {
    "security_override": "Confirmed security flaws cap total score at 3.",
    "fact_supremacy": "Forensic evidence always overrules judicial opinion.",
    "dissent_requirement": "Must summarize why Prosecutor and Defense disagreed.",
    "score_averaging": "When no conflicts, average the three scores.",
    "conflict_thresholds": {
        "major": 3,  # Score difference >= 3 is major conflict
        "minor": 1   # Score difference >= 1 is minor conflict
    }
}


# ============================================================================
# Conflict Resolution
# ============================================================================

def resolve_conflict(
    prosecutor_score: int,
    defense_score: int,
    techlead_score: int,
    prosecutor_arg: str,
    defense_arg: str,
    techlead_arg: str,
    evidence_list: List[Evidence]
) -> Dict[str, Any]:
    """
    Resolve conflict between three judges using deterministic rules.
    
    Returns:
        Dict with final_score, dissent_summary, and resolution_reasoning
    """
    # Calculate score differences
    score_range = max(prosecutor_score, defense_score, techlead_score) - \
                  min(prosecutor_score, defense_score, techlead_score)
    
    # Check for security override
    has_security_flaw = any(
        'security' in arg.lower() or 'negligence' in arg.lower() or 'injection' in arg.lower()
        for arg in [prosecutor_arg, defense_arg, techlead_arg]
    )
    
    # Check if evidence supports prosecution
    evidence_supports_prosecution = any(
        e.confidence < 0.5 for e in evidence_list if e.found == False
    )
    
    # Apply rules
    if has_security_flaw and prosecutor_score <= 2:
        # Security override - cap at 3
        return {
            'final_score': 3,
            'dissent_summary': "Prosecutor correctly identified security flaw. Defense and TechLead overruled.",
            'resolution_reasoning': "SECURITY OVERRIDE: Security flaw confirmed, score capped at 3.",
            'rule_applied': 'security_override'
        }
    
    if evidence_supports_prosecution and defense_score >= 4:
        # Fact supremacy - evidence doesn't support high score
        return {
            'final_score': min(techlead_score, 3),
            'dissent_summary': "Defense gave high score but evidence shows gaps.",
            'resolution_reasoning': "FACT SUPREMACY: Evidence does not support Defense's optimistic assessment.",
            'rule_applied': 'fact_supremacy'
        }
    
    if score_range >= SYNTHESIS_RULES['conflict_thresholds']['major']:
        # Major conflict - apply tiebreaker logic
        # Priority: TechLead > Prosecutor > Defense for technical matters
        scores = {
            'prosecutor': prosecutor_score,
            'defense': defense_score,
            'techlead': techlead_score
        }
        
        # For technical criteria, TechLead has highest weight
        final_score = scores['techlead']
        
        return {
            'final_score': final_score,
            'dissent_summary': f"Major conflict: Prosecutor={prosecutor_score}, Defense={defense_score}, TechLead={techlead_score}",
            'resolution_reasoning': f"Major conflict resolved by TechLead tiebreaker. Range={score_range}",
            'rule_applied': 'major_conflict_resolution'
        }
    
    # No major conflicts - average the scores
    avg_score = round((prosecutor_score + defense_score + techlead_score) / 3)
    
    return {
        'final_score': avg_score,
        'dissent_summary': "All judges largely agreed.",
        'resolution_reasoning': f"Scores averaged: ({prosecutor_score} + {defense_score} + {techlead_score}) / 3 = {avg_score}",
        'rule_applied': 'score_averaging'
    }


# ============================================================================
# Chief Justice Node
# ============================================================================

def create_chief_justice_node():
    """Create the Chief Justice synthesis node."""
    
    def chief_justice(state: Dict) -> Dict[str, Any]:
        """
        Synthesize judicial opinions into final verdict.
        
        Applies:
        1. Conflict resolution rules
        2. Score aggregation
        3. Remediation planning
        4. Report generation
        """
        opinions = state.get('opinions', [])
        
        if not opinions:
            return {
                'final_report': "No opinions to synthesize. Audit incomplete.",
                'final_scores': {},
                'remediation_plan': ["Error: No evidence collected"]
            }
        
        # Group opinions by criterion
        opinions_by_criterion = defaultdict(list)
        for opinion in opinions:
            opinions_by_criterion[opinion.criterion_id].append(opinion)
        
        # Resolve each criterion
        final_scores = {}
        conflicts = {}
        all_remediations = []
        
        for criterion_id, criterion_opinions in opinions_by_criterion.items():
            # Find each judge's opinion for this criterion
            prosecutor = next((o for o in criterion_opinions if o.judge == 'Prosecutor'), None)
            defense = next((o for o in criterion_opinions if o.judge == 'Defense'), None)
            techlead = next((o for o in criterion_opinions if o.judge == 'TechLead'), None)
            
            if not all([prosecutor, defense, techlead]):
                continue
            
            # Get evidence for this criterion
            evidences_dict = state.get('evidences', {})
            all_evidence = []
            for evidence_list in evidences_dict.values():
                all_evidence.extend(evidence_list)
            
            # Resolve conflict
            resolution = resolve_conflict(
                prosecutor_score=prosecutor.score,
                defense_score=defense.score,
                techlead_score=techlead.score,
                prosecutor_arg=prosecutor.argument,
                defense_arg=defense.argument,
                techlead_arg=techlead.argument,
                evidence_list=all_evidence
            )
            
            final_scores[criterion_id] = resolution['final_score']
            conflicts[criterion_id] = resolution['dissent_summary']
            
            # Generate remediation based on lowest score
            lowest_judge = min(
                [(prosecutor, prosecutor.score), (defense, defense.score), (techlead, techlead.score)],
                key=lambda x: x[1]
            )
            
            if lowest_judge[1] <= 2:
                remediation = _generate_remediation(
                    criterion_id,
                    lowest_judge[0].argument,
                    lowest_judge[0].judge
                )
                all_remediations.append(remediation)
        
        # Generate final report
        report = _generate_audit_report(
            criterion_scores=final_scores,
            conflicts=conflicts,
            opinions=opinions,
            remediation_plan=all_remediations
        )
        
        return {
            'final_report': report,
            'final_scores': final_scores,
            'remediation_plan': all_remediations
        }
    
    return chief_justice


# ============================================================================
# Report Generation
# ============================================================================

def _generate_remediation(criterion_id: str, argument: str, judge_type: str) -> str:
    """Generate specific remediation advice based on the failing argument."""
    
    remediation_templates = {
        'forensic_accuracy_code': {
            'Prosecutor': "Fix security issues: Use tempfile for git clone, add error handling. Implement Pydantic state models.",
            'Defense': "Improve code structure: Add typed state definitions with Pydantic.",
            'TechLead': "Address technical debt: Add state reducers (operator.add/ior), implement proper error handling."
        },
        'forensic_accuracy_docs': {
            'Prosecutor': "Verify all claims in PDF match actual code. Remove hallucinations.",
            'Defense': "Add more architectural detail to explain implementation choices.",
            'TechLead': "Include specific file paths and implementation details in documentation."
        },
        'judicial_nuance': {
            'Prosecutor': "Create distinct judge personas with separate system prompts. Implement structured JSON output.",
            'Defense': "Ensure judges have unique voices and perspectives.",
            'TechLead': "Add Pydantic validation to judge outputs. Use .with_structured_output() or .bind_tools()."
        },
        'langgraph_architecture': {
            'Prosecutor': "Implement parallel execution (fan-out) for detectives and judges. Add synchronization node (fan-in).",
            'Defense': "The architecture shows understanding but needs parallel branches.",
            'TechLead': "Refactor to use StateGraph with parallel edges. Implement conditional edges for error handling."
        }
    }
    
    base_template = remediation_templates.get(criterion_id, {}).get(judge_type)
    if base_template:
        return f"[{criterion_id}] {base_template}"
    
    return f"[{criterion_id}] Review and improve implementation based on feedback: {argument[:100]}"


def _generate_audit_report(
    criterion_scores: Dict[str, int],
    conflicts: Dict[str, str],
    opinions: List[JudicialOpinion],
    remediation_plan: List[str]
) -> str:
    """Generate the final markdown audit report."""
    
    # Calculate overall score
    overall_score = sum(criterion_scores.values()) / len(criterion_scores) if criterion_scores else 0
    
    # Build report sections
    report = f"""# Automaton Auditor - Final Audit Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Overall Score:** {overall_score:.2f} / 5.00

---

## Executive Summary

This audit report evaluates the Week 2 submission against the Automaton Auditor rubric.
The evaluation was performed using a hierarchical swarm of specialized agents operating
in a digital courtroom paradigm.

### Verdict
"""

    # Determine verdict level
    if overall_score >= 4.5:
        report += "**MASTER THINKER** - Exceptional implementation demonstrating deep understanding of multi-agent orchestration."
    elif overall_score >= 3.5:
        report += "**ADVANCED IMPLEMENTER** - Strong implementation with minor areas for improvement."
    elif overall_score >= 2.5:
        report += "**COMPETENT ORCHESTRATOR** - Functional implementation meeting basic requirements."
    elif overall_score >= 1.5:
        report += "**DEVELOPING ENGINEER** - Basic implementation with significant gaps."
    else:
        report += "**VIBE CODER** - Minimal implementation requiring substantial rework."

    report += "\n\n---\n\n## Criterion Breakdown\n\n"
    
    # Add each criterion
    criterion_names = {
        'forensic_accuracy_code': 'Forensic Accuracy (Codebase)',
        'forensic_accuracy_docs': 'Forensic Accuracy (Documentation)',
        'judicial_nuance': 'Judicial Nuance & Dialectics',
        'langgraph_architecture': 'LangGraph Orchestration Rigor'
    }
    
    for criterion_id, score in criterion_scores.items():
        criterion_name = criterion_names.get(criterion_id, criterion_id)
        
        report += f"""### {criterion_name}
**Score:** {score}/5

**Dissent:** {conflicts.get(criterion_id, 'No significant conflict')}

"""
    
    # Add judicial opinions summary
    report += "---\n\n## Judicial Opinions Summary\n\n"
    
    # Group by criterion
    opinions_by_criterion = defaultdict(list)
    for opinion in opinions:
        opinions_by_criterion[opinion.criterion_name].append(opinion)
    
    for criterion_name, criterion_opinions in opinions_by_criterion.items():
        report += f"### {criterion_name}\n\n"
        
        for opinion in criterion_opinions:
            report += f"**{opinion.judge}:** Score {opinion.score}/5\n"
            report += f"_{opinion.argument[:200]}..._\n\n"
        
        report += "\n"
    
    # Add remediation plan
    report += "---\n\n## Remediation Plan\n\n"
    
    if remediation_plan:
        for i, remediation in enumerate(remediation_plan, 1):
            report += f"{i}. {remediation}\n"
    else:
        report += "No critical remediation items identified. The implementation is satisfactory.\n"
    
    # Add synthesis rules applied
    report += f"""
---

## Methodology

This audit was conducted using a three-layer agent swarm:

1. **Detective Layer**: Specialized forensic agents (RepoInvestigator, DocAnalyst, VisionInspector)
   collected objective evidence through AST parsing, git history analysis, and document verification.

2. **Judicial Layer**: Three distinct judges analyzed the evidence through different lenses:
   - **Prosecutor**: Critical assessment looking for violations
   - **Defense**: Optimistic assessment finding mitigating factors  
   - **TechLead**: Technical assessment of viability

3. **Supreme Court**: The Chief Justice resolved conflicts using deterministic rules:
   - Security Override: Confirmed security flaws cap scores at 3
   - Fact Supremacy: Forensic evidence overrides judicial opinion
   - Dissent Requirement: All conflicts are documented

---

*Report generated by Automaton Auditor v2.0*
"""
    
    return report


# ============================================================================
# Evidence Aggregator Node
# ============================================================================

def create_evidence_aggregator_node():
    """
    Aggregate evidence from all detectives before passing to judges.
    
    This node acts as the fan-in synchronization point.
    """
    
    def evidence_aggregator(state: Dict) -> Dict[str, Any]:
        """Aggregate and summarize all collected evidence."""
        
        evidences_dict = state.get('evidences', {})
        
        # Flatten all evidence
        all_evidence = []
        for source, evidence_list in evidences_dict.items():
            all_evidence.extend(evidence_list)
        
        # Generate summary
        summary_parts = []
        
        # Count by evidence class
        by_class = defaultdict(list)
        for e in all_evidence:
            by_class[e.evidence_class].append(e)
        
        for evidence_class, evidence_list in by_class.items():
            found_count = sum(1 for e in evidence_list if e.found)
            summary_parts.append(
                f"{evidence_class}: {found_count}/{len(evidence_list)} items found"
            )
        
        summary = "\n".join(summary_parts)
        
        return {
            'evidence_summary': summary,
            'total_evidence_count': len(all_evidence)
        }
    
    return evidence_aggregator
