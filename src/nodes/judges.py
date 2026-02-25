"""
Judge Nodes: The Dialectical Bench

This module implements the three judge personas for the Judicial Layer:
- Prosecutor: Critical lens, charges violations
- Defense: Optimistic lens, finds mitigating factors
- TechLead: Pragmatic lens, assesses technical viability

Each judge operates with structured output to ensure consistent JSON responses.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.state import JudicialOpinion, Evidence


# ============================================================================
# Structured Output Schemas
# ============================================================================

class JudgeScore(BaseModel):
    """Structured output for judge scoring."""
    score: int = Field(ge=1, le=5, description="Score from 1-5")
    reasoning: str = Field(description="Detailed reasoning for the score")
    cited_evidence: List[str] = Field(
        default_factory=list,
        description="List of evidence IDs or locations cited"
    )


# ============================================================================
# Judge System Prompts
# ============================================================================

PROSECUTOR_SYSTEM_PROMPT = """You are THE PROSECUTOR in a digital courtroom. Your role is to be CRITICAL and SUSPICIOUS of all evidence.

CORE PHILOSOPHY: "Trust No One. Assume Vibe Coding."
- Question every claim
- Look for security flaws, shortcuts, and laziness
- If something seems too good to be true, it probably is

YOUR JOB:
1. Analyze the evidence provided for each rubric criterion
2. Apply STRICT interpretation of the requirements
3. Charge specific violations when evidence doesn't meet standards
4. Assign LOW scores when you find issues

VIOLATIONS TO LOOK FOR:
- "Orchestration Fraud": Linear pipeline instead of parallel fan-out
- "Security Negligence": Raw os.system without sandboxing
- "Hallucination Liability": Free-text outputs instead of structured JSON
- "Persona Collusion": Judges that share 90% of the same prompt
- "Auditor Hallucination": Claims in report not backed by code

SCORING GUIDELINES:
- Score 1: Fundamental failure, missing core requirements
- Score 2: Major gaps, security issues, or significant omissions
- Score 3: Acceptable but with notable issues
- Score 4: Good but not perfect
- Score 5: Only if everything is genuinely excellent

You MUST return a structured JSON response with:
- score: integer 1-5
- reasoning: your argument for this score
- cited_evidence: list of evidence locations you reference
- charge: (optional) specific violation being charged

Remember: You are the skeptic. Don't let mediocre work slide."""


DEFENSE_SYSTEM_PROMPT = """You are THE DEFENSE ATTORNEY in a digital courtroom. Your role is to be OPTIMISTIC and FIND MERIT in the work.

CORE PHILOSOPHY: "Reward Effort and Intent. Look for the Spirit of the Law."
- Give credit for deep understanding even if implementation is flawed
- Look for creative workarounds and clever solutions
- Consider the "struggle" and iteration shown in git history

YOUR JOB:
1. Analyze the evidence provided for each rubric criterion  
2. Find MITIGATING factors that warrant higher scores
3. Highlight creative solutions and deep thought
4. Argue for GENEROUS scores when there's genuine effort

MITIGATION ARGUMENTS TO CONSIDER:
- "Deep Code Comprehension": Sophisticated AST parsing despite syntax issues
- "Engineering Process": Meaningful git commit progression shows struggle/learning
- "Partial Implementation": Even if not complete, the approach is sound
- "Role Separation Success": Distinct personas despite some overlap

SCORING GUIDELINES:
- Be generous with scores 3-5 when there's genuine effort
- If the core idea is sound, overlook minor implementation issues
- Look for what they TRIED to do, not just what they succeeded at

You MUST return a structured JSON response with:
- score: integer 1-5  
- reasoning: your argument for this score
- cited_evidence: list of evidence locations you reference
- mitigation: (optional) the mitigating argument you're making

Remember: You're the advocate. Find the merit in their work."""


TECHLEAD_SYSTEM_PROMPT = """You are THE TECH LEAD in a digital courtroom. Your role is to be PRACTICAL and ASSESS REAL-WORLD VIABILITY.

CORE PHILOSOPHY: "Does it actually work? Is it maintainable?"
- Focus on whether the code is functional and maintainable
- Ignore "vibe" and "effort" - focus on artifacts
- Assess technical debt and practical concerns

YOUR JOB:
1. Analyze the evidence provided for each rubric criterion
2. Assess TECHNICAL soundness and maintainability
3. Identify specific technical issues and remediation steps
4. Provide realistic scores based on what actually works

TECHNICAL THINGS TO CHECK:
- Are state reducers (operator.add, operator.ior) preventing data loss?
- Are tool calls isolated and safe?
- Is the graph structure actually compilable/runnable?
- Is there proper error handling?
- Is the code maintainable by a team?

SCORING GUIDELINES:
- Score 1: Broken, won't work, high technical debt
- Score 2: Works but with significant issues
- Score 3: Functional but not ideal
- Score 4: Good technical implementation
- Score 5: Production-ready, excellent engineering

You MUST return a structured JSON response with:
- score: integer 1-5
- reasoning: your technical assessment
- cited_evidence: list of evidence locations you reference
- technical_assessment: specific technical issues found

Remember: You're the tie-breaker. Be objective about what works."""


# ============================================================================
# Judge Node Functions
# ============================================================================

def create_prosecutor_judge(llm=None):
    """Create a Prosecutor judge agent with structured output."""
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    
    parser = PydanticOutputParser(pydantic_object=JudgeScore)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", PROSECUTOR_SYSTEM_PROMPT),
        ("human", """Analyze the following evidence for criterion: {criterion_name}

EVIDENCE TO ANALYZE:
{evidence_summary}

RUBRIC CRITERION:
{criterion_description}

INSTRUCTIONS:
- Apply strict interpretation
- Look for violations and failures
- Charge specific issues you find
- Return structured JSON with your verdict

{format_instructions}""")
    ])
    
    chain = prompt | llm.with_structured_output(JudgeScore)
    
    def prosecutor_judge(state: Dict) -> Dict[str, Any]:
        """Execute the Prosecutor judge on the evidence."""
        opinions = []
        
        for dimension in state.get('rubric_dimensions', []):
            # Handle both dict and Pydantic model formats
            if hasattr(dimension, 'model_dump'):
                # It's a Pydantic model
                dimension_id = dimension.id
                dimension_name = dimension.name
                dimension_desc = dimension.forensic_instruction
            else:
                # It's a dict
                dimension_id = dimension.get('id', '')
                dimension_name = dimension.get('name', '')
                dimension_desc = dimension.get('forensic_instruction', '')
            
            # Get relevant evidence from state
            all_evidence = []
            evidences_dict = state.get('evidences', {})
            for evidence_list in evidences_dict.values():
                all_evidence.extend(evidence_list)
            
            # Build evidence summary
            evidence_summary = "\n\n".join([
                f"- {e.goal}: {e.rationale} (found={e.found}, location={e.location})"
                for e in all_evidence[:20]  # Limit for context
            ])
            
            try:
                result = chain.invoke({
                    'criterion_name': dimension_name,
                    'criterion_description': dimension_desc,
                    'evidence_summary': evidence_summary,
                    'format_instructions': parser.get_format_instructions()
                })
                
                opinion = JudicialOpinion(
                    judge="Prosecutor",
                    criterion_id=dimension_id,
                    criterion_name=dimension_name,
                    score=result.score,
                    argument=result.reasoning,
                    cited_evidence=result.cited_evidence,
                    charge=_extract_charge(result.reasoning)
                )
                opinions.append(opinion)
                
            except Exception as e:
                # Handle parse errors - still generate opinion
                opinion = JudicialOpinion(
                    judge="Prosecutor",
                    criterion_id=dimension_id,
                    criterion_name=dimension_name,
                    score=2,  # Default low score on error
                    argument=f"Error parsing structured output: {str(e)}. Evidence shows significant gaps.",
                    cited_evidence=[],
                    charge="Hallucination Liability"
                )
                opinions.append(opinion)
        
        return {'opinions': opinions}
    
    return prosecutor_judge


def create_defense_judge(llm=None):
    """Create a Defense judge agent with structured output."""
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    
    parser = PydanticOutputParser(pydantic_object=JudgeScore)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", DEFENSE_SYSTEM_PROMPT),
        ("human", """Analyze the following evidence for criterion: {criterion_name}

EVIDENCE TO ANALYZE:
{evidence_summary}

RUBRIC CRITERION:
{criterion_description}

INSTRUCTIONS:
- Look for merit and effort in the work
- Find mitigating factors
- Consider the "spirit" of the requirements, not just literal interpretation
- Return structured JSON with your verdict

{format_instructions}""")
    ])
    
    chain = prompt | llm.with_structured_output(JudgeScore)
    
    def defense_judge(state: Dict) -> Dict[str, Any]:
        """Execute the Defense judge on the evidence."""
        opinions = []
        
        for dimension in state.get('rubric_dimensions', []):
            # Handle both dict and Pydantic model formats
            if hasattr(dimension, 'model_dump'):
                # It's a Pydantic model
                dimension_id = dimension.id
                dimension_name = dimension.name
                dimension_desc = dimension.forensic_instruction
            else:
                # It's a dict
                dimension_id = dimension.get('id', '')
                dimension_name = dimension.get('name', '')
                dimension_desc = dimension.get('forensic_instruction', '')
            
            all_evidence = []
            evidences_dict = state.get('evidences', {})
            for evidence_list in evidences_dict.values():
                all_evidence.extend(evidence_list)
            
            evidence_summary = "\n\n".join([
                f"- {e.goal}: {e.rationale} (found={e.found})"
                for e in all_evidence[:20]
            ])
            
            try:
                result = chain.invoke({
                    'criterion_name': dimension_name,
                    'criterion_description': dimension_desc,
                    'evidence_summary': evidence_summary,
                    'format_instructions': parser.get_format_instructions()
                })
                
                opinion = JudicialOpinion(
                    judge="Defense",
                    criterion_id=dimension_id,
                    criterion_name=dimension_name,
                    score=result.score,
                    argument=result.reasoning,
                    cited_evidence=result.cited_evidence,
                    mitigation=_extract_mitigation(result.reasoning)
                )
                opinions.append(opinion)
                
            except Exception as e:
                opinion = JudicialOpinion(
                    judge="Defense",
                    criterion_id=dimension_id,
                    criterion_name=dimension_name,
                    score=3,  # Neutral score on error
                    argument=f"Error in analysis: {str(e)}. Based on available evidence, there appears to be genuine effort.",
                    cited_evidence=[],
                    mitigation="Genuine effort despite implementation issues"
                )
                opinions.append(opinion)
        
        return {'opinions': opinions}
    
    return defense_judge


def create_techlead_judge(llm=None):
    """Create a Tech Lead judge agent with structured output."""
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    
    parser = PydanticOutputParser(pydantic_object=JudgeScore)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", TECHLEAD_SYSTEM_PROMPT),
        ("human", """Analyze the following evidence for criterion: {criterion_name}

EVIDENCE TO ANALYZE:
{evidence_summary}

RUBRIC CRITERION:
{criterion_description}

INSTRUCTIONS:
- Focus on technical viability and maintainability
- Assess whether the code actually works
- Ignore "vibe" - look at artifacts
- Return structured JSON with your technical assessment

{format_instructions}""")
    ])
    
    chain = prompt | llm.with_structured_output(JudgeScore)
    
    def techlead_judge(state: Dict) -> Dict[str, Any]:
        """Execute the Tech Lead judge on the evidence."""
        opinions = []
        
        for dimension in state.get('rubric_dimensions', []):
            # Handle both dict and Pydantic model formats
            if hasattr(dimension, 'model_dump'):
                # It's a Pydantic model
                dimension_id = dimension.id
                dimension_name = dimension.name
                dimension_desc = dimension.forensic_instruction
            else:
                # It's a dict
                dimension_id = dimension.get('id', '')
                dimension_name = dimension.get('name', '')
                dimension_desc = dimension.get('forensic_instruction', '')
            
            all_evidence = []
            evidences_dict = state.get('evidences', {})
            for evidence_list in evidences_dict.values():
                all_evidence.extend(evidence_list)
            
            evidence_summary = "\n\n".join([
                f"- {e.goal}: {e.content[:200] if e.content else 'N/A'}... (found={e.found})"
                for e in all_evidence[:20]
            ])
            
            try:
                result = chain.invoke({
                    'criterion_name': dimension_name,
                    'criterion_description': dimension_desc,
                    'evidence_summary': evidence_summary,
                    'format_instructions': parser.get_format_instructions()
                })
                
                opinion = JudicialOpinion(
                    judge="TechLead",
                    criterion_id=dimension_id,
                    criterion_name=dimension_name,
                    score=result.score,
                    argument=result.reasoning,
                    cited_evidence=result.cited_evidence,
                    technical_assessment=_extract_technical(result.reasoning)
                )
                opinions.append(opinion)
                
            except Exception as e:
                opinion = JudicialOpinion(
                    judge="TechLead",
                    criterion_id=dimension_id,
                    criterion_name=dimension_name,
                    score=3,
                    argument=f"Analysis error: {str(e)}. Cannot verify technical viability.",
                    cited_evidence=[],
                    technical_assessment="Unable to assess due to analysis error"
                )
                opinions.append(opinion)
        
        return {'opinions': opinions}
    
    return techlead_judge


# ============================================================================
# Helper Functions
# ============================================================================

def _extract_charge(reasoning: str) -> Optional[str]:
    """Extract violation charge from reasoning."""
    charges = [
        "Orchestration Fraud",
        "Security Negligence", 
        "Hallucination Liability",
        "Persona Collusion",
        "Auditor Hallucination"
    ]
    reasoning_lower = reasoning.lower()
    for charge in charges:
        if charge.lower() in reasoning_lower:
            return charge
    return None


def _extract_mitigation(reasoning: str) -> Optional[str]:
    """Extract mitigation argument from reasoning."""
    mitigations = [
        "Deep Code Comprehension",
        "Engineering Process",
        "Partial Implementation",
        "Role Separation Success",
        "Genuine Effort"
    ]
    reasoning_lower = reasoning.lower()
    for mitigation in mitigations:
        if mitigation.lower() in reasoning_lower:
            return mitigation
    return "Reasoning effort shown in implementation"


def _extract_technical(reasoning: str) -> str:
    """Extract technical assessment from reasoning."""
    # Return first 200 chars as technical summary
    return reasoning[:200] if reasoning else "No technical assessment"


# ============================================================================
# Parallel Judge Execution
# ============================================================================

def run_parallel_judges(state: Dict, llm=None) -> Dict[str, List[JudicialOpinion]]:
    """
    Run all three judges in parallel on the same evidence.
    
    This is the entry point for the Judicial Layer.
    """
    # This will be called from the graph with proper parallel execution
    prosecutor = create_prosecutor_judge(llm)
    defense = create_defense_judge(llm)
    techlead = create_techlead_judge(llm)
    
    # Each judge returns their opinions
    prosecutor_result = prosecutor(state)
    defense_result = defense(state)
    techlead_result = techlead(state)
    
    # Combine all opinions
    all_opinions = []
    all_opinions.extend(prosecutor_result.get('opinions', []))
    all_opinions.extend(defense_result.get('opinions', []))
    all_opinions.extend(techlead_result.get('opinions', []))
    
    return {'opinions': all_opinions}
