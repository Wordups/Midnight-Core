# Bird Eye Review — Expected Findings (Validation Key)

**Use this to grade Bird Eye's output.** This corpus has 8 documents with intentional issues planted across all five finding types. If Bird Eye works, it should find these. If it misses them — or hallucinates findings that aren't here — you have bugs to fix.

---

## Document inventory

| ID | Title | Type | Status |
|---|---|---|---|
| TKO-POL-001 | Information Security Policy | Policy | Active |
| TKO-POL-002 | Access Control Policy | Policy | Active |
| TKO-POL-003 | Incident Response Policy | Policy | Active |
| TKO-POL-004 | Acceptable Use Policy | Policy | Active |
| TKO-STD-001 | Identity and Authentication Standard | Standard | Active |
| TKO-POL-005 | Data Retention Policy | Policy | Active (stale) |
| TKO-POL-006 | Vendor Management Policy | Policy | Active |
| TKO-STD-002 | Encryption Standard | Standard | Active |

---

## Expected findings

### Duplicate content (semantic similarity)

**Finding D1 — High severity**
- Documents: TKO-POL-002 (Access Control Policy §4.1) ↔ TKO-STD-001 (Identity & Auth Standard §4.1)
- Similarity: ~95%+ (text is nearly verbatim)
- Section: "Authentication Requirements"
- Expected recommendation: Merge or designate one as authoritative source

**Finding D2 — High severity**
- Documents: TKO-POL-002 (§4.3 Privileged Access) ↔ TKO-STD-001 (§4.3 Privileged Identity Management)
- Similarity: ~88%
- Expected recommendation: Consolidate privileged access requirements

**Finding D3 — Medium severity**
- Documents: TKO-POL-002 (§4.4 Service Accounts) ↔ TKO-STD-001 (§4.5 Service Account Credentials)
- Similarity: ~80%
- Expected recommendation: Move service account language to standard, reference from policy

**Finding D4 — Medium severity**
- Documents: TKO-POL-001 (§4.3 Encryption) ↔ TKO-STD-002 (§4.1 Encryption at Rest)
- Similarity: ~85% (intentional verbatim copy of "All customer data is encrypted at rest using AES-256...")
- Expected recommendation: Standard should be authoritative; policy should reference it

---

### Conflicting controls (numeric or directive mismatches)

**Finding C1 — Critical severity**
- Conflict: Password minimum length
- TKO-POL-002 §4.2: minimum 14 characters
- TKO-STD-001 §4.2: minimum 12 characters
- Expected recommendation: Standardize on 14 (stronger of the two) and update both documents

**Finding C2 — High severity**
- Conflict: Password rotation cadence
- TKO-POL-002 §4.2: every 180 days for privileged accounts
- TKO-STD-001 §4.2: every 90 days for all accounts
- Expected recommendation: Align with NIST 800-63B current guidance (no forced rotation absent compromise) or pick one cadence

**Finding C3 — High severity**
- Conflict: Password reuse history
- TKO-POL-002 §4.2: previous 12 passwords prohibited
- TKO-STD-001 §4.2: previous 8 passwords prohibited
- Expected recommendation: Standardize on 12 (stronger of the two)

**Finding C4 — Medium severity**
- Conflict: Account lockout threshold
- TKO-POL-002 §4.2: 5 failed attempts / 15 min window / 30 min lockout
- TKO-STD-001 §4.2: 3 failed attempts / 10 min window / 60 min lockout
- Expected recommendation: Standardize lockout policy

**Finding C5 — High severity**
- Conflict: TLS version requirement
- TKO-POL-001 §4.3: "TLS 1.3 or higher"
- TKO-STD-002 §4.1 and §4.2: "TLS 1.2 or higher"
- Expected recommendation: TLS 1.3 is the modern standard; update standard to align with policy

---

### Stale governance

**Finding S1 — High severity**
- Document: TKO-POL-005 (Data Retention Policy)
- Issue: Last reviewed 2024-08-15, next review was 2025-08-15 — overdue by ~9 months as of build date
- Expected recommendation: Schedule immediate review and re-approval

**Finding S2 — High severity**
- Document: TKO-POL-005 (Data Retention Policy)
- Issue: Owner field is `[unassigned]`
- Expected recommendation: Assign an owner before next review cycle

**Finding S3 — Low severity**
- Document: TKO-POL-005 (Data Retention Policy)
- Issue: Version 0.9 indicates pre-release / draft status while document is marked Active
- Expected recommendation: Promote to v1.0 or change status

---

### Framework gaps

**Finding F1 — Medium severity**
- Document: TKO-POL-005 (Data Retention Policy)
- Issue: Only tagged for SOC 2 but contains HIPAA-implicating retention requirements (customer PHI retention windows)
- Expected recommendation: Add HIPAA framework tag

**Finding F2 — Medium severity**
- Document: TKO-POL-006 (Vendor Management Policy)
- Issue: Document body explicitly references HIPAA Business Associate Agreements, but `Frameworks:` field only lists SOC 2
- Expected recommendation: Add HIPAA framework tag

**Finding F3 — Low severity**
- Document: TKO-POL-004 (Acceptable Use Policy)
- Issue: Tagged for SOC 2 and ISO 27001 but not NIST CSF, which has equivalent AUP-style controls (PR.IP-11, PR.AT-1)
- Expected recommendation: Add NIST CSF tag if NIST CSF is a target framework for Takeoff

---

### Orphaned documents

**Finding O1 — Medium severity**
- Document: TKO-POL-003 (Incident Response Policy)
- Issue: Policy references incident response procedures, but no Incident Response Runbook exists in the document inventory
- Expected recommendation: Create an Incident Response Runbook (procedure-level artifact)

**Finding O2 — Medium severity**
- Document: TKO-POL-006 (Vendor Management Policy)
- Issue: Policy requires vendor security questionnaires and assessments, but no Vendor Assessment Procedure or questionnaire template exists
- Expected recommendation: Create vendor assessment procedure

**Finding O3 — Low severity**
- Document: TKO-POL-005 (Data Retention Policy)
- Issue: Policy requires automated retention enforcement and cryptographic erasure, but no Data Disposal Procedure exists
- Expected recommendation: Create data disposal procedure

---

## Expected executive summary

```
8 documents reviewed
17 findings detected
  - 4 duplicate content findings
  - 5 conflicting control findings
  - 3 stale governance findings
  - 3 framework gap findings
  - 3 orphaned document findings

Severity breakdown:
  - Critical: 1
  - High: 6
  - Medium: 7
  - Low: 3
```

---

## How to use this validation key

1. Upload all 8 policies into Midnight via your migration tool
2. Trigger Bird Eye Review (manual)
3. Compare actual output to this expected findings list
4. Grade each detector:
   - **Duplicate detector**: should find at least 4 findings; threshold-tune until D1-D4 surface without false positives
   - **Conflict detector**: should find all 5 numeric conflicts; if it misses any, the numeric_requirements extraction in metadata is incomplete
   - **Stale detector**: should flag TKO-POL-005 for all 3 issues; if it misses the unassigned owner, the metadata extraction needs work
   - **Framework gap detector**: should detect when document body references a framework that isn't in the tags field
   - **Orphan detector**: should detect policies that reference procedures/runbooks that don't exist in the document inventory

If Bird Eye finds significantly fewer or significantly more findings than this list, that's a tuning signal — not necessarily a bug. Documents are noisy. The point is: every finding above represents a real governance issue you'd want flagged in production, and the bar for v1 is catching the spirit of these findings, not exact 1:1 matching.

---

## After validation: clean these up and keep them

Once Bird Eye validates clean, fix the planted issues:
- Resolve the password length conflict (pick 14)
- Resolve the TLS conflict (pick 1.3)
- Assign an owner to the Data Retention Policy and bring it current
- Build the missing runbook and procedures (or accept the gap with documented justification)

You now have 8 real governance documents for Takeoff LLC. That's the SOC 2 starter pack you needed anyway.
