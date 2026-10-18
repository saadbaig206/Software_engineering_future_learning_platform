"""
FutureLearning Learning Engine - PERT / CPM Analytical Engine
Calculates:
- Expected Durations (Te) & Variances (sigma^2)
- Forward Pass: Early Start (ES) & Early Finish (EF)
- Backward Pass: Late Start (LS) & Late Finish (LF)
- Slack / Float: Total Float (TF) & Free Float (FF)
- Critical Path Identification
- Project Total Expected Duration, Variance, Standard Deviation
- Probability of Project Completion within Target Deadlines (Z-score)
- Mermaid Flowchart (CPM Network) & Gantt Chart Generation
"""
import math
from typing import Dict, List, Any


ACTIVITIES = [
    {
        "id": "A",
        "name": "Requirements Engineering & Scope Freeze",
        "wbs": "1.0",
        "predecessors": [],
        "a": 2.0, "m": 3.0, "b": 5.0,
        "lead": "Lead Architect",
        "deliverable": "docs/01-requirements.md (47 FRs, 12 NFRs)",
    },
    {
        "id": "B",
        "name": "System Architecture, ERD & API Specification",
        "wbs": "2.0",
        "predecessors": ["A"],
        "a": 3.0, "m": 4.0, "b": 7.0,
        "lead": "Lead Architect",
        "deliverable": "docs/02-system-design.md, docs/diagrams/*.mmd",
    },
    {
        "id": "C",
        "name": "Infrastructure, Neon DB, Redis & Celery Scaffolding",
        "wbs": "3.0",
        "predecessors": ["B"],
        "a": 2.0, "m": 3.0, "b": 4.0,
        "lead": "DevOps / Backend",
        "deliverable": "infra/docker-compose.yml, Neon Postgres pool",
    },
    {
        "id": "D",
        "name": "Identity, RBAC, SimpleJWT & GDPR Consent",
        "wbs": "4.0",
        "predecessors": ["C"],
        "a": 3.0, "m": 4.0, "b": 6.0,
        "lead": "Backend Engineer",
        "deliverable": "backend/apps/users, 5-tier role model",
    },
    {
        "id": "E",
        "name": "Course, Module, Lesson Hierarchy & Content Blocks",
        "wbs": "5.0",
        "predecessors": ["D"],
        "a": 4.0, "m": 5.0, "b": 8.0,
        "lead": "Backend / Frontend",
        "deliverable": "apps/courses, apps/content, /studio authoring UI",
    },
    {
        "id": "F",
        "name": "Public Catalog, Preview & Idempotent Enrollment",
        "wbs": "6.0",
        "predecessors": ["D", "E"],
        "a": 3.0, "m": 4.0, "b": 5.0,
        "lead": "Fullstack Engineer",
        "deliverable": "/courses catalog, enrollment transaction API",
    },
    {
        "id": "G",
        "name": "Progress Heartbeats, Telemetry Stream & Completion",
        "wbs": "7.0",
        "predecessors": ["F"],
        "a": 3.0, "m": 4.0, "b": 6.0,
        "lead": "Backend Engineer",
        "deliverable": "apps/progress, LearningEvent append-only stream",
    },
    {
        "id": "H",
        "name": "Assessment Engine (Quizzes, Grading, Attempt Limits)",
        "wbs": "8.0",
        "predecessors": ["E", "F"],
        "a": 4.0, "m": 5.0, "b": 7.0,
        "lead": "Backend / QA",
        "deliverable": "apps/assessments, server-side grading engine",
    },
    {
        "id": "I",
        "name": "Adaptive Learning Engine (KST Skill DAG & Remediation)",
        "wbs": "9.0",
        "predecessors": ["G", "H"],
        "a": 4.0, "m": 5.0, "b": 8.0,
        "lead": "Lead Architect",
        "deliverable": "apps/learning, KnowledgeSpaceStrategy, DAG sort",
    },
    {
        "id": "J",
        "name": "Discussion Forums, Upvotes, Endorsements & Moderation",
        "wbs": "10.0",
        "predecessors": ["D", "F"],
        "a": 3.0, "m": 4.0, "b": 6.0,
        "lead": "Fullstack Engineer",
        "deliverable": "apps/discussions, moderation triage, DiscussionPanel",
    },
    {
        "id": "K",
        "name": "Sandboxed Interactive Simulations (postMessage)",
        "wbs": "11.0",
        "predecessors": ["E", "G"],
        "a": 2.0, "m": 3.0, "b": 5.0,
        "lead": "Frontend Engineer",
        "deliverable": "SimulationRunner.tsx, telemetry score ingestion",
    },
    {
        "id": "L",
        "name": "Analytics Dashboards, Daily Celery Rollups & GDPR Rights",
        "wbs": "12.0",
        "predecessors": ["G", "H", "J"],
        "a": 3.0, "m": 4.0, "b": 6.0,
        "lead": "Backend / Frontend",
        "deliverable": "apps/analytics, /studio/analytics, /profile GDPR",
    },
    {
        "id": "M",
        "name": "Security Hardening, DRF Rate Throttles & WCAG A11y",
        "wbs": "13.0",
        "predecessors": ["I", "K", "L"],
        "a": 3.0, "m": 4.0, "b": 6.0,
        "lead": "Security / DevOps",
        "deliverable": "CSP, DRF throttles, WCAG 2.1 AA audit",
    },
    {
        "id": "N",
        "name": "Comprehensive Test Suite (E2E Journey, Locust Load)",
        "wbs": "14.0",
        "predecessors": ["M"],
        "a": 3.0, "m": 4.0, "b": 5.0,
        "lead": "QA Engineer",
        "deliverable": "docs/03-test-plan.md, test_e2e_journey.py, locustfile",
    },
    {
        "id": "O",
        "name": "Deployment Validation & Database Disaster Recovery",
        "wbs": "15.0",
        "predecessors": ["N"],
        "a": 2.0, "m": 3.0, "b": 5.0,
        "lead": "DevOps / Lead",
        "deliverable": "Neon point-in-time restore, Docker production stack",
    },
    {
        "id": "P",
        "name": "Validation Report, Package Compilation & Handover",
        "wbs": "16.0",
        "predecessors": ["O"],
        "a": 2.0, "m": 3.0, "b": 5.0,
        "lead": "Entire Team (4)",
        "deliverable": "docs/05-validation.md, master index, submission package",
    },
]


def run_pert_cpm():
    nodes: Dict[str, Dict[str, Any]] = {}
    for act in ACTIVITIES:
        aid = act["id"]
        a, m, b = act["a"], act["m"], act["b"]
        te = (a + 4 * m + b) / 6.0
        var = ((b - a) / 6.0) ** 2
        nodes[aid] = {
            **act,
            "te": round(te, 2),
            "var": round(var, 4),
            "sigma": round(math.sqrt(var), 3),
            "es": 0.0,
            "ef": 0.0,
            "ls": 0.0,
            "lf": 0.0,
            "tf": 0.0,
            "ff": 0.0,
            "successors": [],
            "is_critical": False,
        }

    # Populate successors
    for aid, node in nodes.items():
        for pred in node["predecessors"]:
            nodes[pred]["successors"].append(aid)

    # Forward Pass
    for aid in [act["id"] for act in ACTIVITIES]:
        node = nodes[aid]
        if not node["predecessors"]:
            node["es"] = 0.0
        else:
            node["es"] = max(nodes[pred]["ef"] for pred in node["predecessors"])
        node["ef"] = round(node["es"] + node["te"], 2)

    total_project_duration = max(node["ef"] for node in nodes.values())

    # Backward Pass
    for aid in reversed([act["id"] for act in ACTIVITIES]):
        node = nodes[aid]
        if not node["successors"]:
            node["lf"] = total_project_duration
        else:
            node["lf"] = min(nodes[succ]["ls"] for succ in node["successors"])
        node["ls"] = round(node["lf"] - node["te"], 2)
        node["tf"] = round(node["ls"] - node["es"], 2)
        node["is_critical"] = abs(node["tf"]) < 0.01

    # Free float
    for aid, node in nodes.items():
        if not node["successors"]:
            node["ff"] = round(total_project_duration - node["ef"], 2)
        else:
            node["ff"] = round(min(nodes[succ]["es"] for succ in node["successors"]) - node["ef"], 2)

    # Critical Path calculation
    critical_path = [aid for aid, node in nodes.items() if node["is_critical"]]
    cp_duration = sum(nodes[aid]["te"] for aid in critical_path)
    cp_variance = sum(nodes[aid]["var"] for aid in critical_path)
    cp_std = math.sqrt(cp_variance)

    # Probabilities
    # Target deadlines: 50 days, 55 days, 60 days (12 weeks = 60 days)
    deadlines = [48.0, 50.0, 52.0, 55.0, 60.0]
    prob_results = []
    for d in deadlines:
        z = (d - cp_duration) / cp_std
        # Normal CDF approximation
        prob = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_results.append((d, round(z, 2), round(prob * 100, 1)))

    return {
        "nodes": nodes,
        "total_duration": total_project_duration,
        "critical_path": critical_path,
        "cp_duration": cp_duration,
        "cp_variance": cp_variance,
        "cp_std": cp_std,
        "probabilities": prob_results,
    }


def generate_mermaid_network(res):
    lines = ["```mermaid", "flowchart LR"]
    lines.append("    classDef critical fill:#fee2e2,stroke:#ef4444,stroke-width:3px,color:#991b1b,font-weight:bold;")
    lines.append("    classDef normal fill:#f8fafc,stroke:#64748b,stroke-width:1.5px,color:#0f172a;")
    
    for aid, n in res["nodes"].items():
        label = f"\"{aid}: {n['name'][:24]}...<br/>Te={n['te']}d | TF={n['tf']}d<br/>[{n['es']:.1f} -> {n['ef']:.1f}]\""
        lines.append(f"    {aid}[{label}]")
    
    for aid, n in res["nodes"].items():
        for succ in n["successors"]:
            if n["is_critical"] and res["nodes"][succ]["is_critical"]:
                lines.append(f"    {aid} == \"Critical\" ==> {succ}")
            else:
                lines.append(f"    {aid} --> {succ}")
                
    for aid, n in res["nodes"].items():
        cname = "critical" if n["is_critical"] else "normal"
        lines.append(f"    class {aid} {cname}")
        
    lines.append("```")
    return "\n".join(lines)


if __name__ == "__main__":
    res = run_pert_cpm()
    print("=" * 80)
    print("FUTURELEARNING PERT / CPM SCHEDULE COMPUTATION")
    print("=" * 80)
    print(f"Total Expected Project Duration: {res['total_duration']:.2f} business days")
    print(f"Critical Path Sequence:        {' -> '.join(res['critical_path'])}")
    print(f"Critical Path Expected Time:   {res['cp_duration']:.2f} days")
    print(f"Critical Path Variance:        {res['cp_variance']:.4f}")
    print(f"Critical Path Std Dev (sigma): {res['cp_std']:.3f} days")
    print("\nProbability of Completion:")
    for d, z, p in res["probabilities"]:
        print(f"  Target: {d:4.1f} days | Z-Score: {z:+5.2f} | Probability: {p:5.1f}%")

    print("\nDetailed Activity Table:")
    print(f"{'ID':<3} {'WBS':<5} {'Name':<42} {'Te':<6} {'Var':<7} {'ES':<6} {'EF':<6} {'LS':<6} {'LF':<6} {'TF':<6} {'FF':<6} {'Crit':<4}")
    print("-" * 108)
    for aid, n in res["nodes"].items():
        crit_str = "YES" if n["is_critical"] else "NO"
        print(f"{aid:<3} {n['wbs']:<5} {n['name'][:40]:<42} {n['te']:<6.2f} {n['var']:<7.4f} {n['es']:<6.2f} {n['ef']:<6.2f} {n['ls']:<6.2f} {n['lf']:<6.2f} {n['tf']:<6.2f} {n['ff']:<6.2f} {crit_str:<4}")

    print("\nMermaid CPM Network Diagram:")
    print(generate_mermaid_network(res))

