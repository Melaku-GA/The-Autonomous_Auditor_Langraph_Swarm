"""
Example: Running a self-audit

This script demonstrates how to run the Automaton Auditor
against your own Week 2 implementation.
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import run_audit


def main():
    """Run audit on the current repository."""
    
    # Configuration - modify these for your setup
    REPO_URL = os.environ.get("AUDIT_REPO_URL", "")
    PDF_PATH = os.environ.get("AUDIT_PDF_PATH", "")
    OUTPUT_DIR = "audit/report_onself_generated"
    
    if not REPO_URL or not PDF_PATH:
        print("Error: Please set AUDIT_REPO_URL and AUDIT_PDF_PATH environment variables")
        print("\nUsage:")
        print("  export AUDIT_REPO_URL=\"https://github.com/user/week2-repo\"")
        print("  export AUDIT_PDF_PATH=\"./week2-report.pdf\"")
        print("  python examples/self_audit.py")
        sys.exit(1)
    
    print("=" * 60)
    print("AUTOMATON AUDITOR - Self Audit")
    print("=" * 60)
    print(f"Repository: {REPO_URL}")
    print(f"Report: {PDF_PATH}")
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        # Run the audit
        result = run_audit(
            repo_url=REPO_URL,
            pdf_path=PDF_PATH
        )
        
        # Save the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(OUTPUT_DIR, f"audit_report_{timestamp}.md")
        
        with open(report_file, 'w') as f:
            f.write(result['final_report'])
        
        # Save scores as JSON
        import json
        scores_file = os.path.join(OUTPUT_DIR, f"scores_{timestamp}.json")
        with open(scores_file, 'w') as f:
            json.dump({
                'scores': result['final_scores'],
                'remediation': result['remediation_plan'],
                'timestamp': datetime.now().isoformat(),
                'repo_url': REPO_URL
            }, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 60)
        print("AUDIT COMPLETE")
        print("=" * 60)
        
        avg_score = sum(result['final_scores'].values()) / len(result['final_scores']) if result['final_scores'] else 0
        print(f"\nOverall Score: {avg_score:.2f}/5")
        print(f"Evidence Items: {result['total_evidence']}")
        print(f"Judicial Opinions: {result['total_opinions']}")
        
        print("\nScores by Criterion:")
        for criterion, score in result['final_scores'].items():
            bar = "█" * score + "░" * (5 - score)
            print(f"  {criterion}: [{bar}] {score}/5")
        
        print("\nRemediation Items:")
        for i, item in enumerate(result['remediation_plan'][:5], 1):
            print(f"  {i}. {item[:100]}...")
        
        print(f"\nFull report saved to: {report_file}")
        print(f"Scores saved to: {scores_file}")
        
    except Exception as e:
        print(f"\nError during audit: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
