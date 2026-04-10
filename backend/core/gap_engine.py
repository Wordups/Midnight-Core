"""
Midnight — Gap Engine
Takeoff LLC

Takes the output of framework_mapper.py and computes what's missing.

Flow:
    mapped_document → get_required_controls(framework, doc_type)
                    → compare against covered_controls
                    → return GapReport

Rules:
    - Deterministic. No AI guessing. Required controls are defined per framework.
    - Every gap has a control ID, severity, description, and suggested action.
    - One document can cover controls across multiple frameworks simultaneously.
    - Engine never touches template logic. Pure analysis only.
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Data models ────────────────────────────────────────────────────────────────

@dataclass
class Control:
    id: str                         # e.g. "HIPAA-164.308(a)(1)"
    framework: str                  # e.g. "HIPAA"
    name: str                       # e.g. "Security Management Process"
    description: str
    severity: str                   # "critical" | "medium" | "low"
    doc_types: list[str]            # which doc types are expected to cover this
    suggested_action: str


@dataclass
class Gap:
    control: Control
    reason: str                     # why it's a gap
    affected_frameworks: list[str]  # may appear in multiple frameworks


@dataclass
class GapReport:
    document_name: str
    doc_type: str
    frameworks_checked: list[str]
    covered_control_ids: list[str]
    gaps: list[Gap]
    coverage_by_framework: dict     # {"HIPAA": 78, "PCI DSS": 44, ...}

    @property
    def total_gaps(self): return len(self.gaps)

    @property
    def critical_gaps(self): return [g for g in self.gaps if g.control.severity == "critical"]

    @property
    def medium_gaps(self): return [g for g in self.gaps if g.control.severity == "medium"]

    @property
    def low_gaps(self): return [g for g in self.gaps if g.control.severity == "low"]

    def to_dict(self) -> dict:
        return {
            "document_name": self.document_name,
            "doc_type": self.doc_type,
            "frameworks_checked": self.frameworks_checked,
            "covered_control_ids": self.covered_control_ids,
            "total_gaps": self.total_gaps,
            "gaps_critical": len(self.critical_gaps),
            "gaps_medium": len(self.medium_gaps),
            "gaps_low": len(self.low_gaps),
            "coverage_by_framework": self.coverage_by_framework,
            "gaps": [
                {
                    "control_id": g.control.id,
                    "framework": g.control.framework,
                    "name": g.control.name,
                    "description": g.control.description,
                    "severity": g.control.severity,
                    "reason": g.reason,
                    "affected_frameworks": g.affected_frameworks,
                    "suggested_action": g.control.suggested_action,
                }
                for g in self.gaps
            ],
        }


# ── Control registry ───────────────────────────────────────────────────────────
# This is your compliance intelligence layer.
# Add controls here as you expand framework coverage.
# Each control maps to which doc_types are expected to address it.

CONTROL_REGISTRY: list[Control] = [

    # ── HIPAA ──────────────────────────────────────────────────────────────────
    Control(
        id="HIPAA-164.308(a)(1)",
        framework="HIPAA",
        name="Security Management Process",
        description="Risk analysis and risk management procedures required",
        severity="critical",
        doc_types=["POLICY", "PLAN"],
        suggested_action="Create or update Information Security Policy with risk management section",
    ),
    Control(
        id="HIPAA-164.308(a)(3)",
        framework="HIPAA",
        name="Workforce Security",
        description="Access authorization and termination procedures required",
        severity="critical",
        doc_types=["POLICY", "PROCEDURE", "SOP"],
        suggested_action="Build access control policy with onboarding and offboarding procedures",
    ),
    Control(
        id="HIPAA-164.308(a)(5)",
        framework="HIPAA",
        name="Security Awareness Training",
        description="Security awareness and training program required for all staff",
        severity="critical",
        doc_types=["POLICY", "PLAN"],
        suggested_action="Build security awareness training policy",
    ),
    Control(
        id="HIPAA-164.308(a)(6)",
        framework="HIPAA",
        name="Security Incident Procedures",
        description="Incident response and reporting procedures required",
        severity="critical",
        doc_types=["PLAN", "PLAYBOOK", "PROCEDURE"],
        suggested_action="Build incident response plan",
    ),
    Control(
        id="HIPAA-164.308(a)(7)",
        framework="HIPAA",
        name="Contingency Plan",
        description="Data backup, disaster recovery, and emergency mode procedures",
        severity="critical",
        doc_types=["PLAN"],
        suggested_action="Build business continuity and disaster recovery plan",
    ),
    Control(
        id="HIPAA-164.312(a)(1)",
        framework="HIPAA",
        name="Access Control",
        description="Unique user identification and access control required",
        severity="critical",
        doc_types=["POLICY", "STANDARD"],
        suggested_action="Create or update access control policy",
    ),
    Control(
        id="HIPAA-164.312(a)(2)",
        framework="HIPAA",
        name="Encryption and Decryption",
        description="Encryption of ePHI at rest and in transit required",
        severity="medium",
        doc_types=["POLICY", "STANDARD"],
        suggested_action="Update encryption policy to current standards",
    ),
    Control(
        id="HIPAA-164.312(e)(2)",
        framework="HIPAA",
        name="Transmission Security",
        description="Guard against unauthorized access to ePHI in transit",
        severity="medium",
        doc_types=["POLICY", "STANDARD"],
        suggested_action="Add transmission security section to encryption policy",
    ),

    # ── PCI DSS ────────────────────────────────────────────────────────────────
    Control(
        id="PCI-3.5.1",
        framework="PCI DSS",
        name="Cryptographic Key Protection",
        description="Procedures to protect cryptographic keys",
        severity="critical",
        doc_types=["POLICY", "PROCEDURE", "STANDARD"],
        suggested_action="Build cryptographic key management policy",
    ),
    Control(
        id="PCI-6.3",
        framework="PCI DSS",
        name="Vulnerability Management",
        description="Security vulnerabilities identified and addressed",
        severity="critical",
        doc_types=["POLICY", "PROCEDURE", "SOP"],
        suggested_action="Build vulnerability management policy and patch SOP",
    ),
    Control(
        id="PCI-7.1",
        framework="PCI DSS",
        name="Access Control",
        description="Access to system components limited by business need",
        severity="critical",
        doc_types=["POLICY", "STANDARD", "PROCEDURE"],
        suggested_action="Create access control review procedure",
    ),
    Control(
        id="PCI-12.1",
        framework="PCI DSS",
        name="Security Policy",
        description="Information security policy established and maintained",
        severity="critical",
        doc_types=["POLICY"],
        suggested_action="Establish formal information security policy",
    ),
    Control(
        id="PCI-12.8",
        framework="PCI DSS",
        name="Vendor Risk Management",
        description="Policies to manage service providers and vendors",
        severity="critical",
        doc_types=["POLICY", "PROCEDURE"],
        suggested_action="Generate vendor risk management policy",
    ),

    # ── NIST CSF ───────────────────────────────────────────────────────────────
    Control(
        id="NIST-PR.DS-5",
        framework="NIST CSF",
        name="Data Protection",
        description="Protections against data leaks implemented",
        severity="critical",
        doc_types=["POLICY", "STANDARD"],
        suggested_action="Build data protection policy",
    ),
    Control(
        id="NIST-PR.IP-9",
        framework="NIST CSF",
        name="Response and Recovery Plans",
        description="Response and recovery plans in place and managed",
        severity="critical",
        doc_types=["PLAN", "PLAYBOOK"],
        suggested_action="Build business continuity and IR plan",
    ),
    Control(
        id="NIST-AC-2",
        framework="NIST CSF",
        name="Account Management",
        description="Account management procedures documented",
        severity="medium",
        doc_types=["POLICY", "PROCEDURE", "SOP"],
        suggested_action="Create account management procedure",
    ),
    Control(
        id="NIST-PR.AT-1",
        framework="NIST CSF",
        name="Awareness Training",
        description="All users informed and trained on security risks",
        severity="medium",
        doc_types=["POLICY", "PLAN"],
        suggested_action="Build security awareness training plan",
    ),

    # ── HITRUST ────────────────────────────────────────────────────────────────
    Control(
        id="HITRUST-01.a",
        framework="HITRUST",
        name="Access Control Policy",
        description="Access control policy documented and implemented",
        severity="critical",
        doc_types=["POLICY"],
        suggested_action="Create or update access control policy",
    ),
    Control(
        id="HITRUST-06.d",
        framework="HITRUST",
        name="Vendor Management",
        description="Third-party service delivery managed and monitored",
        severity="critical",
        doc_types=["POLICY", "PROCEDURE"],
        suggested_action="Build vendor risk management policy",
    ),
    Control(
        id="HITRUST-11.a",
        framework="HITRUST",
        name="Incident Management",
        description="Information security incident management procedures",
        severity="critical",
        doc_types=["PLAN", "PLAYBOOK", "PROCEDURE"],
        suggested_action="Build incident response plan and playbooks",
    ),

    # ── ISO 27001 ──────────────────────────────────────────────────────────────
    Control(
        id="ISO-A.8.1",
        framework="ISO 27001",
        name="Responsibility for Assets",
        description="Assets identified and clear ownership assigned",
        severity="medium",
        doc_types=["POLICY"],
        suggested_action="Update access control policy with user responsibility definitions",
    ),
    Control(
        id="ISO-A.9.1",
        framework="ISO 27001",
        name="Access Control Policy",
        description="Access control policy established and reviewed",
        severity="critical",
        doc_types=["POLICY"],
        suggested_action="Create or review access control policy",
    ),
    Control(
        id="ISO-A.16.1",
        framework="ISO 27001",
        name="Incident Management",
        description="Responsibilities and procedures for incident management",
        severity="critical",
        doc_types=["PLAN", "PLAYBOOK"],
        suggested_action="Build incident response plan",
    ),

    # ── SOC 2 ──────────────────────────────────────────────────────────────────
    Control(
        id="SOC2-CC6.1",
        framework="SOC 2",
        name="Logical Access Controls",
        description="Logical access security software, infrastructure, and architectures",
        severity="low",
        doc_types=["POLICY", "STANDARD"],
        suggested_action="Document logical access controls",
    ),
    Control(
        id="SOC2-CC7.2",
        framework="SOC 2",
        name="Monitoring",
        description="System components monitored for anomalies",
        severity="low",
        doc_types=["SOP", "PROCEDURE"],
        suggested_action="Build monitoring and alerting SOP",
    ),
    Control(
        id="SOC2-CC9.2",
        framework="SOC 2",
        name="Vendor Risk",
        description="Vendor and partner risk management",
        severity="medium",
        doc_types=["POLICY"],
        suggested_action="Build vendor risk management policy",
    ),
]

# Controls that map across multiple frameworks (cross-reference table)
CROSS_FRAMEWORK_MAP: dict[str, list[str]] = {
    # Incident response appears in all four primary frameworks
    "HIPAA-164.308(a)(6)": ["HITRUST-11.a", "NIST-PR.IP-9", "ISO-A.16.1"],
    # Access control is universal
    "PCI-7.1":             ["HIPAA-164.312(a)(1)", "HITRUST-01.a", "NIST-AC-2", "ISO-A.9.1"],
    # Vendor management
    "PCI-12.8":            ["HITRUST-06.d", "SOC2-CC9.2"],
    # Awareness training
    "HIPAA-164.308(a)(5)": ["NIST-PR.AT-1"],
}


# ── Framework → required controls lookup ──────────────────────────────────────

FRAMEWORK_CONTROLS: dict[str, list[str]] = {}

for ctrl in CONTROL_REGISTRY:
    FRAMEWORK_CONTROLS.setdefault(ctrl.framework, []).append(ctrl.id)

_CONTROL_LOOKUP: dict[str, Control] = {c.id: c for c in CONTROL_REGISTRY}


def get_equivalent_controls(control_id: str) -> set[str]:
    equivalents = set(CROSS_FRAMEWORK_MAP.get(control_id, []))
    for primary, mapped_controls in CROSS_FRAMEWORK_MAP.items():
        if control_id in mapped_controls:
            equivalents.add(primary)
            equivalents.update(c for c in mapped_controls if c != control_id)
    return equivalents


def is_control_covered(control_id: str, covered_set: set[str]) -> bool:
    if control_id in covered_set:
        return True
    return any(equivalent in covered_set for equivalent in get_equivalent_controls(control_id))


# ── Core engine ────────────────────────────────────────────────────────────────

def get_required_controls(frameworks: list[str], doc_type: str) -> list[Control]:
    """
    Return all controls required for the given frameworks
    that are expected to be addressed by this doc_type.
    """
    required = []
    seen = set()
    for framework in frameworks:
        for ctrl_id in FRAMEWORK_CONTROLS.get(framework, []):
            ctrl = _CONTROL_LOOKUP.get(ctrl_id)
            if ctrl and doc_type in ctrl.doc_types and ctrl_id not in seen:
                required.append(ctrl)
                seen.add(ctrl_id)
    return required


def compute_gaps(
    document_name: str,
    doc_type: str,
    covered_control_ids: list[str],
    frameworks: list[str],
) -> GapReport:
    """
    Core gap computation.

    Args:
        document_name:      name of the document being analyzed
        doc_type:           POLICY | SOP | PLAYBOOK | STANDARD | PLAN | PROCEDURE
        covered_control_ids: control IDs already addressed in this document
                            (output of framework_mapper.py)
        frameworks:         which frameworks to check against

    Returns:
        GapReport with all gaps, severities, and per-framework coverage %
    """
    required = get_required_controls(frameworks, doc_type)
    covered_set = set(covered_control_ids)

    gaps = []
    for ctrl in required:
        if not is_control_covered(ctrl.id, covered_set):
            affected = {ctrl.framework}
            for equivalent_id in get_equivalent_controls(ctrl.id):
                equivalent = _CONTROL_LOOKUP.get(equivalent_id)
                if equivalent:
                    affected.add(equivalent.framework)

            gaps.append(Gap(
                control=ctrl,
                reason=f"No content mapped to {ctrl.id} in uploaded document",
                affected_frameworks=sorted(affected),
            ))

    # Coverage % per framework
    coverage = {}
    for framework in frameworks:
        fw_controls = [
            c for c in CONTROL_REGISTRY
            if c.framework == framework and doc_type in c.doc_types
        ]
        if not fw_controls:
            coverage[framework] = 100
            continue
        covered_count = sum(1 for c in fw_controls if is_control_covered(c.id, covered_set))
        coverage[framework] = round((covered_count / len(fw_controls)) * 100)

    return GapReport(
        document_name=document_name,
        doc_type=doc_type,
        frameworks_checked=frameworks,
        covered_control_ids=covered_control_ids,
        gaps=sorted(gaps, key=lambda g: {"critical": 0, "medium": 1, "low": 2}[g.control.severity]),
        coverage_by_framework=coverage,
    )


def run_program_gap_analysis(
    documents: list[dict],
    frameworks: list[str],
) -> dict:
    """
    Run gap analysis across an entire compliance program
    (multiple documents of different types).

    Args:
        documents: list of {name, doc_type, covered_control_ids}
        frameworks: frameworks to check

    Returns:
        Program-level summary with total coverage + all gaps
    """
    all_covered: set[str] = set()
    for doc in documents:
        all_covered.update(doc.get("covered_control_ids", []))

    # Get all required controls across all doc types
    all_required = []
    seen = set()
    for doc in documents:
        for ctrl in get_required_controls(frameworks, doc["doc_type"]):
            if ctrl.id not in seen:
                all_required.append(ctrl)
                seen.add(ctrl.id)

    # Compute program-level gaps
    gaps = []
    for ctrl in all_required:
        if ctrl.id not in all_covered:
            cross = CROSS_FRAMEWORK_MAP.get(ctrl.id, [])
            if not any(c in all_covered for c in cross):
                gaps.append({
                    "control_id": ctrl.id,
                    "framework": ctrl.framework,
                    "name": ctrl.name,
                    "description": ctrl.description,
                    "severity": ctrl.severity,
                    "suggested_action": ctrl.suggested_action,
                    "affected_frameworks": [ctrl.framework],
                })

    # Program coverage per framework
    coverage = {}
    for framework in frameworks:
        fw_controls = [c for c in CONTROL_REGISTRY if c.framework == framework]
        if not fw_controls:
            coverage[framework] = 100
            continue
        covered_count = sum(1 for c in fw_controls if is_control_covered(c.id, all_covered))
        coverage[framework] = round((covered_count / len(fw_controls)) * 100)

    gaps_sorted = sorted(gaps, key=lambda g: {"critical": 0, "medium": 1, "low": 2}[g["severity"]])

    return {
        "frameworks_checked": frameworks,
        "documents_analyzed": len(documents),
        "total_controls_required": len(all_required),
        "total_controls_covered": len(all_covered),
        "total_gaps": len(gaps),
        "gaps_critical": sum(1 for g in gaps if g["severity"] == "critical"),
        "gaps_medium": sum(1 for g in gaps if g["severity"] == "medium"),
        "gaps_low": sum(1 for g in gaps if g["severity"] == "low"),
        "coverage_by_framework": coverage,
        "overall_coverage_pct": round(
            sum(coverage.values()) / len(coverage) if coverage else 0
        ),
        "gaps": gaps_sorted,
    }


# ── Quick test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Simulate: access control policy that covers some HIPAA + PCI controls
    report = compute_gaps(
        document_name="Access Control Policy v2",
        doc_type="POLICY",
        covered_control_ids=[
            "HIPAA-164.308(a)(1)",
            "HIPAA-164.312(a)(1)",
            "PCI-7.1",
            "PCI-12.1",
            "HITRUST-01.a",
        ],
        frameworks=["HIPAA", "PCI DSS", "HITRUST", "NIST CSF"],
    )

    print(f"\nDocument: {report.document_name}")
    print(f"Doc type: {report.doc_type}")
    print(f"Frameworks: {', '.join(report.frameworks_checked)}")
    print(f"\nCoverage:")
    for fw, pct in report.coverage_by_framework.items():
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        print(f"  {fw:<12} {bar} {pct}%")
    print(f"\nGaps: {report.total_gaps} total "
          f"({len(report.critical_gaps)} critical, "
          f"{len(report.medium_gaps)} medium, "
          f"{len(report.low_gaps)} low)")
    print("\nCritical gaps:")
    for gap in report.critical_gaps:
        print(f"  [{gap.control.id}] {gap.control.name}")
        print(f"    → {gap.control.suggested_action}")
