"""
VisionInspector: The Diagram Detective

This module provides forensic analysis of architectural diagrams extracted
from PDF documents using multimodal LLM vision capabilities.

Note: This is an optional component. Full implementation requires a vision-capable
LLM (GPT-4o, Claude 3 Opus, or Gemini Pro Vision).
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Optional imports for image extraction
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class DiagramClassification:
    """Classification of a diagram."""
    diagram_type: str = ""
    confidence: float = 0.0
    description: str = ""
    has_parallel_flow: bool = False
    has_judges: bool = False
    has_detectives: bool = False
    has_synthesis: bool = False


@dataclass
class SwarmVisualReport:
    """Report on swarm visualization in diagrams."""
    total_diagrams: int = 0
    classified_diagrams: List[DiagramClassification] = field(default_factory=list)
    has_accurate_stategraph: bool = False
    has_sequential_diagram: bool = False
    has_generic_boxes: bool = False
    accuracy_score: float = 0.0


class VisionInspector:
    """
    The Diagram Detective - analyzes architectural diagrams using vision models.
    
    Forensic Protocols:
    - Protocol A: Flow Analysis (classify diagram type)
    - Protocol B: Swarm Verification (verify parallel patterns)
    """
    
    # Diagram type classifications
    VALID_DIAGRAM_TYPES = [
        'stategraph',
        'state_machine', 
        'flowchart',
        'sequence_diagram',
        'uml',
        'generic_boxes',
        'unknown'
    ]
    
    def __init__(self):
        self.images: List[Image.Image] = []
        self.diagram_analyses: List[Dict[str, Any]] = []
        
    def extract_images_from_pdf(self, pdf_path: str) -> Tuple[bool, str]:
        """
        Extract images from PDF pages.
        
        Returns:
            Tuple of (success, message)
        """
        if not os.path.exists(pdf_path):
            return False, f"PDF not found: {pdf_path}"
        
        if not HAS_PDF2IMAGE:
            return False, "pdf2image not installed. Run: pip install pdf2image"
        
        if not HAS_PIL:
            return False, "Pillow not installed. Run: pip install pillow"
        
        try:
            # Convert PDF to images
            self.images = convert_from_path(pdf_path, dpi=150)
            return True, f"Extracted {len(self.images)} images from PDF"
        except Exception as e:
            return False, f"Error extracting images: {str(e)}"
    
    def analyze_diagram_with_vision(
        self, 
        image: Image.Image,
        vision_client=None,
        prompt: Optional[str] = None
    ) -> DiagramClassification:
        """
        Analyze a diagram using a vision-capable LLM.
        
        Args:
            image: PIL Image to analyze
            vision_client: Optional LLM client with vision support
            prompt: Optional custom prompt
            
        Returns:
            DiagramClassification with analysis results
        """
        classification = DiagramClassification()
        
        if prompt is None:
            prompt = """Analyze this architectural diagram and classify it. 
            Look for:
            1. Is this a StateGraph/State Machine diagram?
            2. Is it a sequence diagram?
            3. Is it a generic flowchart with boxes?
            4. Does it show parallel execution (fan-out/fan-in)?
            5. Does it show Detectives, Judges, or Synthesis nodes?
            
            Provide your analysis in JSON format with these fields:
            - diagram_type: one of [stategraph, sequence_diagram, flowchart, generic_boxes, unknown]
            - confidence: float 0-1
            - description: brief description of what you see
            - has_parallel_flow: boolean
            - has_judges: boolean  
            - has_detectives: boolean
            - has_synthesis: boolean
            """
        
        # This would call a vision LLM in production
        # For now, return a placeholder
        if vision_client is None:
            classification.diagram_type = "unknown"
            classification.confidence = 0.0
            classification.description = "No vision client provided - analysis skipped"
            return classification
        
        # In production, this would make an API call
        # response = vision_client.analyze_image(image, prompt)
        # return parse_vision_response(response)
        
        return classification
    
    def analyze_swarm_visual(self) -> SwarmVisualReport:
        """
        Analyze all extracted diagrams for swarm representation accuracy.
        
        Returns:
            Report on swarm visualization quality
        """
        report = SwarmVisualReport()
        report.total_diagrams = len(self.images)
        
        # Analyze each diagram
        for i, img in enumerate(self.images):
            analysis = self.analyze_diagram_with_vision(img)
            report.classified_diagrams.append(analysis)
            
            if analysis.diagram_type == 'stategraph':
                report.has_accurate_stategraph = True
            elif analysis.diagram_type == 'sequence_diagram':
                report.has_sequential_diagram = True
            elif analysis.diagram_type == 'generic_boxes':
                report.has_generic_boxes = True
        
        # Calculate accuracy score
        if report.total_diagrams > 0:
            accurate_count = sum(
                1 for d in report.classified_diagrams 
                if d.has_parallel_flow and (d.has_judges or d.has_detectives)
            )
            report.accuracy_score = accurate_count / report.total_diagrams * 5
        
        return report
    
    def basic_image_analysis(self, image_path: str) -> Dict[str, Any]:
        """
        Perform basic image analysis without vision model.
        
        Uses heuristics to guess diagram type based on image characteristics.
        """
        if not HAS_PIL:
            return {'error': 'Pillow not available'}
        
        try:
            img = Image.open(image_path)
            width, height = img.size
            
            # Basic heuristics (very rough)
            result = {
                'dimensions': {'width': width, 'height': height},
                'format': img.format,
                'mode': img.mode,
                'analysis': 'Basic image metadata only. Vision analysis requires LLM client.'
            }
            
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def run_full_visual_analysis(
        self, 
        pdf_path: str,
        vision_client=None
    ) -> Dict[str, Any]:
        """
        Run complete visual analysis on PDF diagrams.
        
        Args:
            pdf_path: Path to PDF file
            vision_client: Optional vision-capable LLM client
            
        Returns:
            Dictionary containing visual analysis results
        """
        # Extract images
        success, message = self.extract_images_from_pdf(pdf_path)
        
        result = {
            'extraction_success': success,
            'message': message,
            'diagram_count': len(self.images)
        }
        
        if not success:
            result['error'] = message
            return result
        
        # Analyze swarm visuals
        if vision_client:
            swarm_report = self.analyze_swarm_visual()
            result['swarm_visual_report'] = {
                'total_diagrams': swarm_report.total_diagrams,
                'has_accurate_stategraph': swarm_report.has_accurate_stategraph,
                'has_sequential_diagram': swarm_report.has_sequential_diagram,
                'has_generic_boxes': swarm_report.has_generic_boxes,
                'accuracy_score': swarm_report.accuracy_score
            }
        
        return result


# Standalone function for LangGraph tool
def inspect_diagram(image_path: str, vision_client=None) -> str:
    """
    LangGraph tool function for diagram inspection.
    
    Args:
        image_path: Path to image file
        vision_client: Optional vision-capable LLM client
        
    Returns:
        JSON string of analysis results
    """
    inspector = VisionInspector()
    
    if os.path.isfile(image_path):
        result = inspector.basic_image_analysis(image_path)
    else:
        result = {'error': 'File not found'}
    
    return json.dumps(result, indent=2)
