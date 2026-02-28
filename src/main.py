import argparse
import os
import json
from datetime import datetime
from .graph import create_audit_graph, create_trace_handler
from pydantic.v1.fields import FieldInfo
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()
    parser = argparse.ArgumentParser(description="Automaton Auditor CLI")
    parser.add_argument("--repo", required=False, default="", help="Target GitHub Repository URL (optional)")
    parser.add_argument("--pdf", required=False, default="", help="Path to the Architectural PDF Report (optional)")
    parser.add_argument("--mode", choices=["self", "peer"], default="self", help="Audit mode")
    args = parser.parse_args()

    # Validate that at least one input is provided
    if not args.repo and not args.pdf:
        parser.error("At least one of --repo or --pdf must be provided")

    # Determine which inputs are available
    has_repo = bool(args.repo)
    has_pdf = bool(args.pdf)

    print(f"Audit Configuration:")
    print(f"  - GitHub Repository: {args.repo if has_repo else 'Not provided'}")
    print(f"  - PDF Report: {args.pdf if has_pdf else 'Not provided'}")
    print()

    # 2. Load the Constitution (Rubric)
    with open("rubric/week2_rubric.json", "r") as f:
        rubric_data = json.load(f)

    # 3. Initialize Agent State
    initial_state = {
        "repo_url": args.repo,
        "pdf_path": args.pdf,
        "has_repo": has_repo,
        "has_pdf": has_pdf,
        "rubric_dimensions": rubric_data["dimensions"],
        "evidences": {},
        "opinions": [],
        "final_report": ""
    }

    # Create trace handler for local logging
    trace_handler = create_trace_handler()
    
    # 4. Execute the Swarm
    target = args.repo if has_repo else args.pdf
    print(f"Running audit on: {target}...")
    app = create_audit_graph()
    
    # Run with tracing callbacks
    final_state = app.invoke(
        initial_state,
        config={"callbacks": [trace_handler]}
    )

    # Save traces to langsmith_logs/
    trace_file = trace_handler.save_traces()
    print(f"Traces saved to: {trace_file}")

    # 5. Determine Output Folder
    if args.mode == "self":
        output_dir = "audit/report_onself_generated"
    else:
        output_dir = "audit/report_onpeer_generated"

    os.makedirs(output_dir, exist_ok=True)
    
    # 6. Save the Audit Report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"audit_report_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        f.write(final_state["final_report"])

    print(f"Audit Complete! Report saved to: {filepath}")

if __name__ == "__main__":
    main()