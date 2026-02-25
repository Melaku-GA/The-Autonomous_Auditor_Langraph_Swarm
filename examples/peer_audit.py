"""
Example: Running a peer audit

This script demonstrates how to audit a peer's Week 2 implementation.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import run_audit


def main():
    """Run audit on a peer's repository."""
    
    # Configuration
    REPO_URL = os.environ.get("PEER_REPO_URL", "")
    PDF_PATH = os.environ.get("PEER_PDF_PATH", "")
    OUTPUT_DIR = "audit/report_onpeer_generated"
    
    if not REPO_URL or not PDF_PATH:
        print("Error: Please set PEER_REPO_URL and PEER_PDF_PATH environment variables")
        print("\nUsage:")
        print("  export PEER_REPO_URL=\"https://github.com/peer/user-week2\"")
        print("  export PEER_PDF_PATH=\"./peer-report.pdf\"")
        print("  python examples/peer_audit.py")
        sys.exit(1)
    
    print("=" * 60)
    print("AUTOMATON AUDITOR - Peer Audit")
    print("=" * 60)
    print(f"Repository: {REPO_URL}")
    print(f"Report: {PDF_PATH}")
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        result = run_audit(
            repo_url=REPO_URL,
            pdf_path=PDF_PATH
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(OUTPUT_DIR, f"peer_audit_{timestamp}.md")
        
        with open(report_file, 'w') as f:
            f.write(result['final_report'])
        
        import json
        scores_file = os.path.join(OUTPUT_DIR, f"peer_scores_{timestamp}.json")
        with open(scores_file, 'w') as f:
            json.dump({
                'scores': result['final_scores'],
                'remediation': result['remediation_plan'],
                'timestamp': datetime.now().isoformat(),
                'repo_url': REPO_URL
            }, f, indent=2)
        
        print("\n" + "=" * 60)
        print("PEER AUDIT COMPLETE")
        print("=" * 60)
        
        avg_score = sum(result['final_scores'].values()) / len(result['final_scores']) if result['final_scores'] else 0
        print(f"\nOverall Score: {avg_score:.2f}/5")
        
        print("\nScores by Criterion:")
        for criterion, score in result['final_scores'].items():
            bar = "█" * score + "░" * (5 - score)
            print(f"  {criterion}: [{bar}] {score}/5")
        
        print(f"\nReport saved to: {report_file}")
        
    except Exception as e:
        print(f"\nError during audit: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
