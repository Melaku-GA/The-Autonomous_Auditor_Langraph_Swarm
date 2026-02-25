import argparse
import os
import json
from datetime import datetime
from .graph import create_audit_graph
from pydantic.v1.fields import FieldInfo
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()
    parser = argparse.ArgumentParser(description="Automaton Auditor CLI")
    parser.add_argument("--repo", required=True, help="Target GitHub Repository URL")
    parser.add_argument("--pdf", required=True, help="Path to the Architectural PDF Report")
    parser.add_argument("--mode", choices=["self", "peer"], default="self", help="Audit mode")
    args = parser.parse_args()

    # 2. Load the Constitution (Rubric)
    with open("rubric/week2_rubric.json", "r") as f:
        rubric_data = json.load(f)

    # 3. Initialize Agent State
    initial_state = {
        "repo_url": args.repo,
        "pdf_path": args.pdf,
        "rubric_dimensions": rubric_data["dimensions"],
        "evidences": {},
        "opinions": [],
        "final_report": ""
    }

    # 4. Execute the Swarm
    print(f"Running audit on: {args.repo}...")
    app = create_audit_graph()
    final_state = app.invoke(initial_state)

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