"""
DocAnalyst: The Paperwork Detective

This module provides forensic analysis of PDF reports using text extraction,
keyword search, and cross-reference verification. It verifies claims made
in documentation against actual code artifacts.
"""

import os
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Try to import PDF libraries, with fallbacks
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


@dataclass
class ChunkedPDF:
    """
    A queryable, chunked PDF interface for efficient text search and retrieval.
    
    Allows for:
    - Chunked text storage with metadata
    - Semantic search across chunks
    - Context-aware retrieval
    """
    
    def __init__(self, text_content: str, chunk_size: int = 1000, overlap: int = 100):
        self.chunks: List[str] = []
        self.chunk_metadata: List[Dict[str, Any]] = []
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._chunk_text(text_content)
    
    def _chunk_text(self, text: str):
        """Split text into overlapping chunks with metadata."""
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Store chunk with metadata
            self.chunks.append(chunk)
            self.chunk_metadata.append({
                'chunk_id': chunk_idx,
                'start_char': start,
                'end_char': min(end, len(text)),
                'length': len(chunk)
            })
            
            start = end - self.overlap
            chunk_idx += 1
    
    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the PDF chunks for relevant content.
        
        Args:
            query_text: Text to search for
            top_k: Number of top results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        query_lower = query_text.lower()
        results = []
        
        for i, chunk in enumerate(self.chunks):
            chunk_lower = chunk.lower()
            # Simple keyword matching score
            query_words = query_lower.split()
            score = sum(1 for word in query_words if word in chunk_lower)
            
            if score > 0:
                results.append({
                    'chunk_id': i,
                    'score': score,
                    'content': chunk,
                    'metadata': self.chunk_metadata[i]
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def get_context_around(self, keyword: str, context_chars: int = 200) -> List[Dict[str, Any]]:
        """Get context around keyword occurrences."""
        results = []
        keyword_lower = keyword.lower()
        
        for i, chunk in enumerate(self.chunks):
            if keyword_lower in chunk.lower():
                # Find position and extract context
                pos = chunk.lower().find(keyword_lower)
                start = max(0, pos - context_chars)
                end = min(len(chunk), pos + len(keyword) + context_chars)
                
                results.append({
                    'chunk_id': i,
                    'context': chunk[start:end],
                    'metadata': self.chunk_metadata[i]
                })
        
        return results


@dataclass
class TheoreticalDepthReport:
    """Report on theoretical depth of the document."""
    keyword_matches: Dict[str, int] = field(default_factory=dict)
    keywords_found: List[str] = field(default_factory=list)
    has_dialectical_synthesis: bool = False
    has_metacognition: bool = False
    has_fan_in_out: bool = False
    has_state_sync: bool = False
    depth_score: float = 0.0
    analysis: str = ""


@dataclass
class ClaimVerificationReport:
    """Report on verification of claims made in the document."""
    total_claims: int = 0
    verified_claims: List[Dict[str, str]] = field(default_factory=list)
    hallucinated_claims: List[Dict[str, str]] = field(default_factory=list)
    unverified_claims: List[Dict[str, str]] = field(default_factory=list)
    verification_accuracy: float = 0.0


@dataclass
class DocumentStructureReport:
    """Report on document structure and quality."""
    page_count: int = 0
    has_executive_summary: bool = False
    has_architecture_section: bool = False
    has_implementation_details: bool = False
    has_diagrams: bool = False
    has_remediation_plan: bool = False
    structure_score: float = 0.0


class DocAnalyst:
    """
    The Paperwork Detective - performs forensic analysis of PDF reports.
    
    Forensic Protocols:
    - Protocol A: Citation Check (cross-reference claims with code)
    - Protocol B: Concept Verification (verify understanding, not just keywords)
    """
    
    # Key concepts to search for
    KEY_CONCEPTS = {
        'Dialectical Synthesis': {
            'keywords': ['dialectical', 'synthesis', 'thesis', 'antithesis'],
            'weight': 1.0
        },
        'Metacognition': {
            'keywords': ['metacognition', 'self-awareness', 'reflection', 'self-evaluation'],
            'weight': 1.0
        },
        'Fan-In/Fan-Out': {
            'keywords': ['fan-out', 'fan in', 'parallel', 'concurrent', 'branching'],
            'weight': 0.8
        },
        'State Synchronization': {
            'keywords': ['state reducer', 'operator.add', 'operator.ior', 'synchronization'],
            'weight': 0.9
        },
        'Multi-Agent Systems': {
            'keywords': ['multi-agent', 'agent swarm', 'swarm', 'delegation'],
            'weight': 0.7
        }
    }
    
    # Common file path patterns to look for
    CLAIM_PATTERNS = [
        r"src/[\w/]+\.py",
        r"src/nodes/[\w_]+\.py",
        r"src/tools/[\w_]+\.py",
        r"src/graph\.py",
        r"src/state\.py",
    ]
    
    def __init__(self):
        self.pdf_path: Optional[str] = None
        self.text_content: str = ""
        self.pages: List[str] = []
        self.chunked_pdf: Optional[ChunkedPDF] = None
        
    def load_pdf(self, pdf_path: str) -> Tuple[bool, str]:
        """
        Load and parse a PDF document.
        
        Returns:
            Tuple of (success, message)
        """
        if not os.path.exists(pdf_path):
            return False, f"PDF file not found: {pdf_path}"
        
        self.pdf_path = pdf_path
        
        try:
            # Try pypdf (newer library)
            if HAS_PYPDF:
                reader = PdfReader(pdf_path)
                self.pages = [page.extract_text() for page in reader.pages]
                self.text_content = "\n\n".join(self.pages)
                # Create chunked PDF for querying
                self.chunked_pdf = ChunkedPDF(self.text_content)
                return True, f"Loaded PDF with {len(self.pages)} pages"
            
            # Fallback to PyPDF2
            elif HAS_PYPDF2:
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    self.pages = [reader.pages[i].extract_text() for i in range(len(reader.pages))]
                    self.text_content = "\n\n".join(self.pages)
                # Create chunked PDF for querying
                self.chunked_pdf = ChunkedPDF(self.text_content)
                return True, f"Loaded PDF with {len(self.pages)} pages"
            else:
                return False, "No PDF library available. Install pypdf2 or pypdf"
                
        except Exception as e:
            return False, f"Error loading PDF: {str(e)}"
    
    def query_pdf(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the loaded PDF document using the chunked interface.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with scores
        """
        if self.chunked_pdf is None:
            return [{'error': 'No PDF loaded'}]
        
        return self.chunked_pdf.query(query, top_k)
    
    def get_pdf_context(self, keyword: str, context_chars: int = 200) -> List[Dict[str, Any]]:
        """
        Get context around keyword occurrences in the PDF.
        
        Args:
            keyword: Keyword to search for
            context_chars: Characters of context to include
            
        Returns:
            List of context snippets
        """
        if self.chunked_pdf is None:
            return [{'error': 'No PDF loaded'}]
        
        return self.chunked_pdf.get_context_around(keyword, context_chars)
    
    def analyze_theoretical_depth(self) -> TheoreticalDepthReport:
        """
        Analyze the theoretical depth of the document.
        
        Checks for:
        - Keyword presence (not just buzzwords)
        - Contextual understanding of concepts
        - Depth of explanation
        """
        report = TheoreticalDepthReport()
        
        if not self.text_content:
            report.analysis = "No document loaded"
            return report
        
        text_lower = self.text_content.lower()
        
        # Search for each key concept
        for concept, config in self.KEY_CONCEPTS.items():
            matches = 0
            for keyword in config['keywords']:
                matches += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            
            if matches > 0:
                report.keywords_found.append(concept)
                report.keyword_matches[concept] = matches
                
                # Check if it's used in context (not just mentioned)
                if self._has_contextual_usage(concept, config['keywords']):
                    if concept == 'Dialectical Synthesis':
                        report.has_dialectical_synthesis = True
                    elif concept == 'Metacognition':
                        report.has_metacognition = True
                    elif concept == 'Fan-In/Fan-Out':
                        report.has_fan_in_out = True
                    elif concept == 'State Synchronization':
                        report.has_state_sync = True
        
        # Calculate depth score
        max_possible = sum(config['weight'] for config in self.KEY_CONCEPTS.values())
        actual = sum(
            config['weight'] 
            for concept, config in self.KEY_CONCEPTS.items() 
            if concept in report.keywords_found
        )
        report.depth_score = (actual / max_possible) * 5 if max_possible > 0 else 0
        
        # Build analysis
        found_concepts = ", ".join(report.keywords_found) if report.keywords_found else "None"
        report.analysis = f"Found key concepts: {found_concepts}. Depth score: {report.depth_score:.2f}/5"
        
        return report
    
    def _has_contextual_usage(self, concept: str, keywords: List[str]) -> bool:
        """
        Check if a concept is used in context (explained) vs just mentioned.
        
        Looks for sentences with multiple keywords or explanatory phrases.
        """
        sentences = re.split(r'[.!?]+', self.text_content)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            keyword_count = sum(1 for kw in keywords if kw in sentence_lower)
            
            # Consider it contextual if:
            # - Multiple keywords in same sentence, OR
            # - Contains explanatory words
            if keyword_count >= 2:
                return True
            if any(word in sentence_lower for word in ['which', 'means', 'refers to', 'describes', 'involves']):
                if any(kw in sentence_lower for kw in keywords):
                    return True
        
        return False
    
    def extract_file_claims(self) -> List[Dict[str, str]]:
        """
        Extract all file path claims from the document.
        
        Returns:
            List of claims with file paths and context
        """
        claims = []
        
        for pattern in self.CLAIM_PATTERNS:
            matches = re.finditer(pattern, self.text_content)
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 100)
                end = min(len(self.text_content), match.end() + 100)
                context = self.text_content[start:end].replace('\n', ' ')
                
                claims.append({
                    'file_path': match.group(),
                    'context': context,
                    'verified': False  # Will be set by cross-reference
                })
        
        return claims
    
    def verify_claims_against_code(
        self, 
        file_claims: List[Dict[str, str]], 
        repo_path: str
    ) -> ClaimVerificationReport:
        """
        Cross-reference file claims in document with actual code.
        
        Args:
            file_claims: List of file path claims from document
            repo_path: Path to the cloned repository
            
        Returns:
            Report with verified, hallucinated, and unverified claims
        """
        report = ClaimVerificationReport()
        report.total_claims = len(file_claims)
        
        for claim in file_claims:
            file_path = claim['file_path']
            
            # Try different path variations
            possible_paths = [
                os.path.join(repo_path, file_path),
                os.path.join(repo_path, 'src', file_path),
                os.path.join(repo_path, file_path.replace('src/', '')),
            ]
            
            found = any(os.path.exists(p) for p in possible_paths)
            
            claim['verified'] = found
            
            if found:
                report.verified_claims.append(claim)
            else:
                # Check if it's a reasonable claim that might just be a different path
                filename = os.path.basename(file_path)
                if any(f for f in os.listdir(repo_path) if filename in f):
                    report.unverified_claims.append(claim)
                else:
                    report.hallucinated_claims.append(claim)
        
        # Calculate accuracy
        if report.total_claims > 0:
            report.verification_accuracy = len(report.verified_claims) / report.total_claims
        
        return report
    
    def analyze_document_structure(self) -> DocumentStructureReport:
        """
        Analyze the structure and quality of the document.
        
        Checks for:
        - Executive summary
        - Architecture section
        - Implementation details
        - Diagrams
        - Remediation plan
        """
        report = DocumentStructureReport()
        
        if not self.pages:
            report.analysis = "No document loaded"
            return report
        
        report.page_count = len(self.pages)
        text_lower = self.text_content.lower()
        
        # Check for sections
        section_indicators = {
            'has_executive_summary': ['executive summary', 'overview', 'introduction'],
            'has_architecture_section': ['architecture', 'system design', 'high-level'],
            'has_implementation_details': ['implementation', 'code', 'source'],
            'has_diagrams': ['diagram', 'figure', 'flowchart', 'architecture'],
            'has_remediation_plan': ['recommendation', 'remediation', 'action item', 'next steps']
        }
        
        for section, indicators in section_indicators.items():
            if any(ind in text_lower for ind in indicators):
                setattr(report, section, True)
        
        # Calculate structure score
        sections_found = sum([
            report.has_executive_summary,
            report.has_architecture_section,
            report.has_implementation_details,
            report.has_diagrams,
            report.has_remediation_plan
        ])
        report.structure_score = (sections_found / 5) * 5
        
        report.analysis = f"Found {sections_found}/5 key sections. Structure score: {report.structure_score:.2f}/5"
        
        return report
    
    def run_full_document_analysis(
        self, 
        pdf_path: str, 
        repo_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete forensic analysis on a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            repo_path: Optional path to repository for cross-reference
            
        Returns:
            Dictionary containing all analysis reports
        """
        # Load PDF
        success, message = self.load_pdf(pdf_path)
        if not success:
            return {
                'error': message,
                'load_success': False
            }
        
        result = {
            'load_success': True,
            'page_count': len(self.pages),
            'theoretical_depth': self.analyze_theoretical_depth().__dict__,
            'document_structure': self.analyze_document_structure().__dict__
        }
        
        # If repo path provided, verify claims
        if repo_path:
            claims = self.extract_file_claims()
            verification = self.verify_claims_against_code(claims, repo_path)
            result['claim_verification'] = verification.__dict__
        
        return result


# Standalone function for use as LangGraph tool
def analyze_pdf(pdf_path: str, repo_path: Optional[str] = None) -> str:
    """
    LangGraph tool function for PDF analysis.
    
    Args:
        pdf_path: Path to PDF file
        repo_path: Optional path to code for verification
        
    Returns:
        JSON string of analysis results
    """
    analyst = DocAnalyst()
    result = analyst.run_full_document_analysis(pdf_path, repo_path)
    return json.dumps(result, indent=2)
