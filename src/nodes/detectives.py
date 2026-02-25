"""
Detective Nodes: The Forensic Layer

This module implements the three detective agents:
- RepoInvestigatorNode: Code and repository analysis
- DocAnalystNode: PDF document analysis  
- VisionInspectorNode: Diagram analysis

Each detective collects specific evidence based on the rubric.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.state import Evidence
from src.tools.repo_investigator import RepoInvestigator
from src.tools.doc_analyst import DocAnalyst
from src.tools.vision_inspector import VisionInspector


# ============================================================================
# Repo Investigator Node
# ============================================================================

def create_repo_investigator_node():
    """Create a Repo Investigator detective node."""
    
    def repo_investigator(state: Dict) -> Dict[str, Any]:
        """
        Analyze the GitHub repository for forensic evidence.
        
        Collects evidence for:
        - Git forensic analysis
        - State management rigor
        - Graph orchestration
        - Security practices
        - Structured output enforcement
        """
        repo_url = state.get('repo_url', '')
        
        if not repo_url:
            return {'evidences': {'repo': []}, 'error': 'No repository URL provided'}
        
        # Initialize investigator
        investigator = RepoInvestigator()
        evidences = []
        
        try:
            # Clone and analyze repository
            success, message = investigator.clone_repository(repo_url)
            
            if not success:
                evidences.append(Evidence(
                    goal="Clone Repository",
                    found=False,
                    content=message,
                    location=repo_url,
                    rationale=f"Failed to clone: {message}",
                    confidence=1.0,
                    evidence_class="Git Forensic",
                    timestamp=datetime.now().isoformat()
                ))
                return {'evidences': {'repo': evidences}}
            
            # Run forensic analysis
            analysis = investigator.run_full_forensic_analysis(repo_url)
            
            # Extract evidence from analysis
            if analysis.get('clone_success'):
                evidences.append(Evidence(
                    goal="Repository Clone",
                    found=True,
                    content=f"Successfully cloned to {analysis.get('repo_path')}",
                    location=analysis.get('repo_path', ''),
                    rationale="Repository successfully cloned to sandboxed temp directory",
                    confidence=1.0,
                    evidence_class="Git Forensic",
                    timestamp=datetime.now().isoformat()
                ))
            
            # Git history evidence
            git_data = analysis.get('git_forensics', {})
            evidences.append(Evidence(
                goal="Git Commit History",
                found=git_data.get('commit_count', 0) > 0,
                content=json.dumps(git_data.get('commits', [])[:10]),
                location="git log",
                rationale=git_data.get('analysis', ''),
                confidence=0.9 if git_data.get('commit_count', 0) > 0 else 0.0,
                evidence_class="Git Forensic",
                timestamp=datetime.now().isoformat()
            ))
            
            # State management evidence
            state_data = analysis.get('state_management', {})
            evidences.append(Evidence(
                goal="Typed State Definition",
                found=state_data.get('has_typed_state', False),
                content=state_data.get('state_definition'),
                location=state_data.get('state_location', 'Not found'),
                rationale=f"Uses Pydantic: {state_data.get('uses_pydantic')}, "
                         f"Uses TypedDict: {state_data.get('uses_typed_dict')}, "
                         f"Has Reducers: {state_data.get('has_reducers')}",
                confidence=0.9 if state_data.get('has_typed_state') else 0.3,
                evidence_class="State Management",
                timestamp=datetime.now().isoformat()
            ))
            
            # Graph orchestration evidence
            graph_data = analysis.get('graph_orchestration', {})
            evidences.append(Evidence(
                goal="LangGraph StateGraph",
                found=graph_data.get('has_stategraph', False),
                content=json.dumps({
                    'nodes': graph_data.get('node_definitions', []),
                    'edges': graph_data.get('edge_definitions', [])
                }),
                location=graph_data.get('graph_file_location', 'Not found'),
                rationale=f"Has parallel branches: {graph_data.get('has_parallel_branches')}, "
                         f"Fan-out: {graph_data.get('has_fan_out')}, "
                         f"Fan-in: {graph_data.get('has_fan_in')}",
                confidence=0.8 if graph_data.get('has_stategraph') else 0.2,
                evidence_class="Graph Orchestration",
                timestamp=datetime.now().isoformat()
            ))
            
            # Security practices evidence
            security_data = analysis.get('security_practices', {})
            evidences.append(Evidence(
                goal="Secure Tool Engineering",
                found=security_data.get('has_sandboxed_clone', False),
                content=security_data.get('clone_function_code'),
                location="Tool implementations",
                rationale=security_data.get('analysis', ''),
                confidence=0.9 if security_data.get('has_sandboxed_clone') else 0.5,
                evidence_class="Security",
                timestamp=datetime.now().isoformat()
            ))
            
            # Structured output evidence
            structured_data = analysis.get('structured_output', {})
            evidences.append(Evidence(
                goal="Structured Output Enforcement",
                found=structured_data.get('has_pydantic_validation', False),
                content=structured_data.get('judge_file_location'),
                location=structured_data.get('judge_file_location', 'Not found'),
                rationale=f"Uses with_structured_output: {structured_data.get('uses_with_structured_output')}, "
                         f"Uses bind_tools: {structured_data.get('uses_bind_tools')}",
                confidence=0.9 if structured_data.get('has_pydantic_validation') else 0.3,
                evidence_class="Structured Output",
                timestamp=datetime.now().isoformat()
            ))
            
            return {
                'evidences': {'repo': evidences},
                'repo_local_path': analysis.get('repo_path'),
                'git_history': analysis.get('git_forensics', {}).get('commits', []),
                'repo_structure': analysis.get('graph_orchestration', {})
            }
            
        except Exception as e:
            evidences.append(Evidence(
                goal="Repository Analysis",
                found=False,
                content=str(e),
                location=repo_url,
                rationale=f"Error during analysis: {str(e)}",
                confidence=0.0,
                evidence_class="Error",
                timestamp=datetime.now().isoformat()
            ))
            return {'evidences': {'repo': evidences}}
        finally:
            investigator.cleanup()
    
    return repo_investigator


# ============================================================================
# Document Analyst Node
# ============================================================================

def create_doc_analyst_node():
    """Create a Document Analyst detective node."""
    
    def doc_analyst(state: Dict) -> Dict[str, Any]:
        """
        Analyze the PDF report for forensic evidence.
        
        Collects evidence for:
        - Theoretical depth
        - Claim verification
        - Document structure
        """
        pdf_path = state.get('pdf_path', '')
        repo_path = state.get('repo_local_path')
        
        if not pdf_path:
            return {'evidences': {'doc': []}, 'error': 'No PDF path provided'}
        
        analyst = DocAnalyst()
        evidences = []
        
        try:
            # Load and analyze PDF
            success, message = analyst.load_pdf(pdf_path)
            
            if not success:
                evidences.append(Evidence(
                    goal="Load PDF Document",
                    found=False,
                    content=message,
                    location=pdf_path,
                    rationale=f"Failed to load PDF: {message}",
                    confidence=1.0,
                    evidence_class="Document Analysis",
                    timestamp=datetime.now().isoformat()
                ))
                return {'evidences': {'doc': evidences}}
            
            # Theoretical depth analysis
            theory_report = analyst.analyze_theoretical_depth()
            evidences.append(Evidence(
                goal="Theoretical Depth",
                found=theory_report.depth_score > 0,
                content=json.dumps(theory_report.keyword_matches),
                location=pdf_path,
                rationale=theory_report.analysis,
                confidence=min(theory_report.depth_score / 5, 1.0),
                evidence_class="Document Analysis",
                timestamp=datetime.now().isoformat()
            ))
            
            # Key concepts evidence
            key_concepts = []
            if theory_report.has_dialectical_synthesis:
                key_concepts.append("Dialectical Synthesis")
            if theory_report.has_metacognition:
                key_concepts.append("Metacognition")
            if theory_report.has_fan_in_out:
                key_concepts.append("Fan-In/Fan-Out")
            if theory_report.has_state_sync:
                key_concepts.append("State Synchronization")
            
            evidences.append(Evidence(
                goal="Key Concepts",
                found=len(key_concepts) > 0,
                content=", ".join(key_concepts),
                location=pdf_path,
                rationale=f"Found {len(key_concepts)} key concepts in document",
                confidence=0.8 if key_concepts else 0.2,
                evidence_class="Document Analysis",
                timestamp=datetime.now().isoformat()
            ))
            
            # Document structure analysis
            structure_report = analyst.analyze_document_structure()
            evidences.append(Evidence(
                goal="Document Structure",
                found=structure_report.structure_score > 0,
                content=json.dumps({
                    'has_executive_summary': structure_report.has_executive_summary,
                    'has_architecture': structure_report.has_architecture_section,
                    'has_implementation': structure_report.has_implementation_details,
                    'has_remediation': structure_report.has_remediation_plan
                }),
                location=pdf_path,
                rationale=structure_report.analysis,
                confidence=structure_report.structure_score / 5,
                evidence_class="Document Analysis",
                timestamp=datetime.now().isoformat()
            ))
            
            # Claim verification if repo available
            if repo_path:
                claims = analyst.extract_file_claims()
                verification = analyst.verify_claims_against_code(claims, repo_path)
                
                evidences.append(Evidence(
                    goal="Claim Verification",
                    found=verification.total_claims > 0,
                    content=json.dumps({
                        'verified': len(verification.verified_claims),
                        'hallucinated': len(verification.hallucinated_claims),
                        'accuracy': verification.verification_accuracy
                    }),
                    location=pdf_path,
                    rationale=f"Verified: {len(verification.verified_claims)}, "
                             f"Hallucinated: {len(verification.hallucinated_claims)}",
                    confidence=verification.verification_accuracy,
                    evidence_class="Claim Verification",
                    timestamp=datetime.now().isoformat()
                ))
            
            return {
                'evidences': {'doc': evidences},
                'pdf_content': analyst.text_content[:5000] if analyst.text_content else None
            }
            
        except Exception as e:
            evidences.append(Evidence(
                goal="PDF Analysis",
                found=False,
                content=str(e),
                location=pdf_path,
                rationale=f"Error analyzing PDF: {str(e)}",
                confidence=0.0,
                evidence_class="Error",
                timestamp=datetime.now().isoformat()
            ))
            return {'evidences': {'doc': evidences}}
    
    return doc_analyst


# ============================================================================
# Vision Inspector Node
# ============================================================================

def create_vision_inspector_node(vision_client=None):
    """Create a Vision Inspector detective node."""
    
    def vision_inspector(state: Dict) -> Dict[str, Any]:
        """
        Analyze diagrams extracted from PDF.
        
        Note: This is optional and requires a vision-capable LLM.
        Without a client, it provides basic image extraction.
        """
        pdf_path = state.get('pdf_path', '')
        
        if not pdf_path:
            return {'evidences': {'vision': []}}
        
        inspector = VisionInspector()
        evidences = []
        
        try:
            # Try to extract images
            success, message = inspector.extract_images_from_pdf(pdf_path)
            
            if not success:
                evidences.append(Evidence(
                    goal="Image Extraction",
                    found=False,
                    content=message,
                    location=pdf_path,
                    rationale=f"Failed to extract images: {message}",
                    confidence=0.0,
                    evidence_class="Vision Analysis",
                    timestamp=datetime.now().isoformat()
                ))
                return {'evidences': {'vision': evidences}}
            
            # Record that we found images
            evidences.append(Evidence(
                goal="Diagram Extraction",
                found=len(inspector.images) > 0,
                content=f"Extracted {len(inspector.images)} images",
                location=pdf_path,
                rationale=f"Found {len(inspector.images)} images for analysis",
                confidence=0.5,  # Lower without vision model
                evidence_class="Vision Analysis",
                timestamp=datetime.now().isoformat()
            ))
            
            # If we have a vision client, do deeper analysis
            if vision_client:
                swarm_report = inspector.analyze_swarm_visual()
                
                evidences.append(Evidence(
                    goal="Swarm Visualization",
                    found=swarm_report.has_accurate_stategraph,
                    content=json.dumps({
                        'has_stategraph': swarm_report.has_accurate_stategraph,
                        'has_parallel': any(d.has_parallel_flow for d in swarm_report.classified_diagrams)
                    }),
                    location=pdf_path,
                    rationale=f"Accuracy score: {swarm_report.accuracy_score:.2f}",
                    confidence=swarm_report.accuracy_score,
                    evidence_class="Vision Analysis",
                    timestamp=datetime.now().isoformat()
                ))
            
            return {
                'evidences': {'vision': evidences},
                'extracted_images': [f"page_{i}" for i in range(len(inspector.images))]
            }
            
        except Exception as e:
            evidences.append(Evidence(
                goal="Vision Analysis",
                found=False,
                content=str(e),
                location=pdf_path,
                rationale=f"Error in vision analysis: {str(e)}",
                confidence=0.0,
                evidence_class="Error",
                timestamp=datetime.now().isoformat()
            ))
            return {'evidences': {'vision': evidences}}
    
    return vision_inspector


# ============================================================================
# Parallel Detective Execution
# ============================================================================

def run_parallel_detectives(state: Dict, vision_client=None) -> Dict[str, Any]:
    """
    Run all three detectives in parallel.
    
    This is the entry point for the Detective Layer.
    Note: In the actual LangGraph, this will be handled by fan-out edges.
    """
    repo_node = create_repo_investigator_node()
    doc_node = create_doc_analyst_node()
    vision_node = create_vision_inspector_node(vision_client)
    
    # Each returns their evidence
    repo_result = repo_node(state)
    doc_result = doc_node(state)
    vision_result = vision_node(state)
    
    # Combine all evidence
    combined_evidences = {}
    combined_evidences.update(repo_result.get('evidences', {}))
    combined_evidences.update(doc_result.get('evidences', {}))
    combined_evidences.update(vision_result.get('evidences', {}))
    
    return {
        'evidences': combined_evidences,
        'repo_local_path': repo_result.get('repo_local_path'),
        'pdf_content': doc_result.get('pdf_content'),
        'extracted_images': vision_result.get('extracted_images')
    }
