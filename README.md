# Automaton Auditor - Week 2 Challenge

## Overview

The **Automaton Auditor** is a production-grade multi-agent system built with LangGraph that performs automated code governance and quality assurance audits. It implements a "Digital Courtroom" paradigm where specialized agents operate as detectives, judges, and a supreme court to evaluate code submissions.

## Architecture

### The Digital Courtroom Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 1: DETECTIVE LAYER                           │
│  (Forensic Evidence Collection - Parallel Execution)                       │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │ RepoInvestigator │  │   DocAnalyst     │  │ VisionInspector │       │
│  │  (Code Detective)│  │ (Paperwork Dt.) │  │ (Diagram Dt.)   │       │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘       │
│           │                      │                      │                  │
│           └──────────────────────┼──────────────────────┘                  │
│                                  ↓                                          │
│                    ┌────────────────────────┐                             │
│                    │ Evidence Aggregator     │                             │
│                    │     (Fan-In Sync)       │                             │
│                    └───────────┬────────────┘                             │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 2: JUDICIAL LAYER                            │
│            (Dialectical Evaluation - Parallel Execution)                    │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │    PROSECUTOR   │  │     DEFENSE      │  │    TECH LEAD     │       │
│  │  (Critical Lens)│  │ (Optimistic Lens)│  │(Pragmatic Lens)  │       │
│  │  - Find flaws   │  │  - Find merit    │  │  - Assess tech   │       │
│  │  - Charge viol. │  │  - Mitigate      │  │  - Tie-break     │       │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘       │
│           │                      │                      │                  │
│           └──────────────────────┼──────────────────────┘                  │
│                                  ↓                                          │
│                    ┌────────────────────────┐                             │
│                    │   Opinion Aggregator   │                             │
│                    └───────────┬────────────┘                             │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 3: SUPREME COURT                             │
│                    (Synthesis & Final Verdict)                             │
│                                                                             │
│                    ┌────────────────────────┐                             │
│                    │   Chief Justice Node   │                             │
│                    │  - Conflict resolution │                             │
│                    │  - Apply synthesis     │                             │
│                    │    rules               │                             │
│                    │  - Generate report     │                             │
│                    └───────────┬────────────┘                             │
│                                ↓                                           │
│                    ┌────────────────────────┐                             │
│                    │    Final Audit Report │                             │
│                    │  - Verdict (1-5)      │                             │
│                    │  - Dissent summary    │                             │
│                    │  - Remediation plan   │                             │
│                    └────────────────────────┘                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
automaton-auditor/
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment variables template
├── README.md                # This file
│
├── rubric/
│   └── week2_rubric.json   # Machine-readable grading rubric
│
├── src/
│   ├── __init__.py         # Package exports
│   ├── graph.py            # LangGraph orchestration
│   ├── state.py            # Pydantic state definitions
│   │
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── detectives.py   # Detective nodes
│   │   ├── judges.py       # Judge nodes (Prosecutor, Defense, TechLead)
│   │   └── justice.py      # Chief Justice synthesis
│   │
│   └── tools/
│       ├── __init__.py
│       ├── repo_investigator.py   # Git/code analysis
│       ├── doc_analyst.py          # PDF analysis
│       └── vision_inspector.py    # Diagram analysis
│
└── audit/                   # Generated audit reports
    ├── report_bypeer_received/
    ├── report_onpeer_generated/
    ├── report_onself_generated/
    └── langsmith_logs/
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd automaton-auditor
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   # or with uv
   uv pip install -e .
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Required API Keys:**
   - `OPENAI_API_KEY` - For GPT-4 (required for judges)
   - `ANTHROPIC_API_KEY` - Optional, for Claude as alternative
   - `LANGCHAIN_API_KEY` - Optional, for LangSmith tracing

## Usage

### Basic Usage

```python
from src.graph import run_audit

result = run_audit(
    repo_url="https://github.com/user/repo",
    pdf_path="./path/to/report.pdf"
)

print(result['final_report'])
print(result['final_scores'])
print(result['remediation_plan'])
```

### Command Line

```bash
python -m src.graph <repo_url> <pdf_path>
```

### Streaming Mode

```python
from src.graph import run_audit_stream

for state in run_audit_stream(repo_url, pdf_path):
    print(f"Current node: {list(state.keys())}")
```

## The Digital Courtroom

### Layer 1: Detective Layer

These agents collect **objective evidence** without opinion:

| Detective | Focus | Tools |
|-----------|-------|-------|
| RepoInvestigator | Code structure | Git, AST parsing |
| DocAnalyst | Documentation | PDF text extraction |
| VisionInspector | Diagrams | Image analysis |

### Layer 2: Judicial Layer

Three distinct personas evaluate the evidence through different lenses:

- **Prosecutor**: Critical lens - finds flaws and violations
- **Defense**: Optimistic lens - finds merit and mitigating factors  
- **TechLead**: Pragmatic lens - assesses technical viability

### Layer 3: Supreme Court

The Chief Justice resolves conflicts using deterministic rules:
- Security Override: Security flaws cap scores at 3
- Fact Supremacy: Evidence overrides opinion
- Dissent Requirement: All conflicts are documented

## Evaluation Rubric

The system evaluates submissions on four dimensions:

1. **Forensic Accuracy (Codebase)**: Code analysis, security practices
2. **Forensic Accuracy (Documentation)**: Report quality, claim verification
3. **Judicial Nuance & Dialectics**: Judge persona separation, structured output
4. **LangGraph Orchestration Rigor**: Parallel execution, state management

### Scoring Guide

| Score | Level | Description |
|-------|-------|-------------|
| 1 | Vibe Coder | Generic, no specific evidence |
| 2 | Basic | Basic verification, simple parsing |
| 3 | Competent | Role separation, functional graph |
| 4 | Advanced | Deep parsing, distinct personas |
| 5 | Master | Dialectical synthesis, deterministic rules |

## Configuration

### Custom Rubric

Edit `rubric/week2_rubric.json` to modify evaluation criteria:

```json
{
  "dimensions": [
    {
      "id": "custom_criterion",
      "name": "Custom Criterion",
      "target_artifact": "github_repo",
      "forensic_instruction": "Instructions for detectives",
      "judicial_logic": {
        "prosecutor": "Prosecutor rules",
        "defense": "Defense rules",
        "tech_lead": "TechLead rules"
      }
    }
  ]
}
```

### Custom LLM

```python
from src.graph import create_audit_graph
from langchain_openai import ChatOpenAI

# Use different model
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.1)
graph = create_audit_graph(llm=llm)
```

## Development

### Running Tests

```bash
pytest
```

### Type Checking

```bash
mypy src/
```

### Code Formatting

```bash
ruff check src/
black src/
```

## Key Features

- **Hierarchical Multi-Agent Architecture**: Specialized agents at each layer
- **Parallel Execution**: Detectives and judges run concurrently
- **Structured Output**: Pydantic-validated JSON throughout
- **Dialectical Evaluation**: Three-judge panel with conflict resolution
- **Production-Grade**: Type hints, error handling, observability

## Troubleshooting

### API Key Errors
Ensure your `.env` file has valid API keys. The system requires OpenAI API access.

### Clone Failures
The RepoInvestigator uses shallow clones. Some repositories may have branch restrictions.

### PDF Parsing Issues
Install additional dependencies:
```bash
pip install PyPDF2 pdf2image pillow
```

## License

MIT License

## Credits

Built as part of the FDE Challenge Week 2: The Automaton Auditor
