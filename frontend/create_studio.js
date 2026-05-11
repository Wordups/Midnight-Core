const WORKFLOW_API = window.location.origin;

const WORKFLOW_STEPS = [
  { id: 'metadata', label: 'Metadata' },
  { id: 'content', label: 'Content' },
  { id: 'frameworks', label: 'Frameworks' },
  { id: 'assets', label: 'Embedded Assets' },
  { id: 'review', label: 'Review' },
  { id: 'export', label: 'Export' },
];

const WORKFLOW_CONFIG = {
  POLICY: {
    queryType: 'policy',
    title: 'Policy',
    subtitle: 'Build a compliance-ready policy with structured sections, framework mapping, and export controls.',
    exportOptions: ['Word (.docx)', 'PDF'],
  },
  SOP: {
    queryType: 'procedure',
    title: 'Procedure / SOP',
    subtitle: 'Author operating procedures with structured steps, role ownership, timers, and embedded media.',
    exportOptions: ['Word (.docx)', 'Interactive HTML', 'PDF', 'QR Poster'],
  },
  STANDARD: {
    queryType: 'standard',
    title: 'Standard',
    subtitle: 'Capture enforceable technical requirements, evidence expectations, and control-aligned baseline language.',
    exportOptions: ['Word (.docx)', 'PDF'],
  },
  PROCESS_FLOW: {
    queryType: 'process_flow',
    title: 'Process Flow',
    subtitle: 'Shape process narratives into storyboard-ready flow outputs with supporting evidence and visual structure.',
    exportOptions: ['Word (.docx)', 'PowerPoint (.pptx)', 'PDF'],
  },
  TRAINING_MODULE: {
    queryType: 'training',
    title: 'Training Module',
    subtitle: 'Build training content with teaching objectives, quiz prompts, and export-ready learning artifacts.',
    exportOptions: ['Word (.docx)', 'PowerPoint (.pptx)', 'PDF'],
  },
  INCIDENT_RUNBOOK: {
    queryType: 'incident_runbook',
    title: 'Incident Runbook',
    subtitle: 'Design response playbooks with trigger conditions, escalation paths, timers, and operational checkpoints.',
    exportOptions: ['Word (.docx)', 'Interactive HTML', 'PDF'],
  },
  RISK_ASSESSMENT: {
    queryType: 'risk_assessment',
    title: 'Risk Assessment',
    subtitle: 'Document risks, mitigations, scoring rationale, and control gap framing inside a cleaner workspace.',
    exportOptions: ['Word (.docx)', 'PDF'],
  },
  AUDIT_PACKAGE: {
    queryType: 'audit_package',
    title: 'Audit Package',
    subtitle: 'Organize evidence requests, findings, and checklist artifacts into one tenant-owned audit workspace.',
    exportOptions: ['Word (.docx)', 'PDF', 'Audit Package ZIP'],
  },
  AI_GOVERNANCE: {
    queryType: 'ai_governance',
    title: 'AI Governance',
    subtitle: 'Collect AI system context, policy boundaries, and regulatory mapping inside a dedicated governance workspace.',
    exportOptions: ['Word (.docx)', 'PDF', 'Regulatory Summary'],
  },
};

const QUERY_TYPE_TO_LANE = Object.fromEntries(
  Object.entries(WORKFLOW_CONFIG).map(([lane, config]) => [config.queryType, lane]),
);

let workflowSession = null;
let workflowState = {
  lane: 'POLICY',
  activeStep: 'metadata',
  draft: {},
  previewText: '',
  previewData: null,
  exporting: false,
};

function workflowToast(message, isError = false) {
  const toast = document.getElementById('wf-toast');
  if (!toast) return;
  toast.textContent = message;
  toast.className = `wf-toast show${isError ? ' error' : ''}`;
  clearTimeout(window.__wfToastTimer);
  window.__wfToastTimer = setTimeout(() => {
    toast.classList.remove('show');
    toast.classList.remove('error');
  }, isError ? 4200 : 2600);
}

function workflowSetLoading(visible, title = 'Working…', copy = 'Midnight is preparing your document workspace.') {
  const shell = document.getElementById('wf-loading');
  if (!shell) return;
  shell.classList.toggle('show', visible);
  const titleEl = document.getElementById('wf-loading-title');
  const copyEl = document.getElementById('wf-loading-copy');
  if (titleEl) titleEl.textContent = title;
  if (copyEl) copyEl.textContent = copy;
}

async function workflowSessionCheck() {
  const response = await fetch('/auth/session', {
    credentials: 'include',
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    window.location.replace('/login.html');
    throw new Error('Unable to verify session.');
  }
  const session = await response.json();
  if (!session?.authenticated) {
    window.location.replace('/login.html');
    throw new Error('Authentication required.');
  }
  if (session.access_state === 'needs_onboarding' || !session.profile_exists || !session.tenant_assigned || !session.tenant_id) {
    window.location.replace('/onboarding/plan');
    throw new Error('Tenant provisioning required.');
  }
  if (session.access_state === 'upgrade_required') {
    const reason = encodeURIComponent(session.access_detail || 'Upgrade required to continue.');
    window.location.replace(`/access_denied.html?reason=${reason}`);
    throw new Error('Upgrade required.');
  }
  return session;
}

async function workflowApi(path, options = {}) {
  const response = await fetch(WORKFLOW_API + path, {
    credentials: 'include',
    ...options,
  });
  if (response.status === 401) {
    window.location.replace('/login.html');
    throw new Error('Session expired.');
  }
  if (response.status === 403) {
    const err = await response.json().catch(() => ({}));
    const reason = encodeURIComponent(err.detail || 'Access denied.');
    window.location.replace(`/access_denied.html?reason=${reason}`);
    throw new Error(err.detail || 'Access denied.');
  }
  return response;
}

function workflowDraftKey() {
  const tenantId = workflowSession?.tenant_id || 'unknown';
  return `midnight-workflow-draft:${tenantId}:${workflowState.lane}`;
}

function loadWorkflowDraft() {
  try {
    const raw = localStorage.getItem(workflowDraftKey());
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') workflowState.draft = parsed;
  } catch (_) {}
}

function saveWorkflowDraft() {
  localStorage.setItem(workflowDraftKey(), JSON.stringify(workflowCollectDraft()));
  workflowToast('Draft saved locally for this workspace.');
}

function workflowCollectDraft() {
  const data = { ...workflowState.draft };
  document.querySelectorAll('[data-draft-field]').forEach((field) => {
    data[field.getAttribute('data-draft-field')] = field.value;
  });
  data.frameworks = getSelectedFrameworks();
  return data;
}

function workflowApplyDraft() {
  document.querySelectorAll('[data-draft-field]').forEach((field) => {
    const key = field.getAttribute('data-draft-field');
    if (workflowState.draft[key] != null) field.value = workflowState.draft[key];
  });
  const selected = Array.isArray(workflowState.draft.frameworks) ? workflowState.draft.frameworks : [];
  document.querySelectorAll('[data-framework-pill]').forEach((pill) => {
    pill.classList.toggle('active', selected.includes(pill.getAttribute('data-framework-pill')));
  });
}

function workflowSyncTopbar() {
  const lane = WORKFLOW_CONFIG[workflowState.lane];
  document.getElementById('wf-breadcrumb-lane').textContent = lane.title;
  document.getElementById('wf-breadcrumb-state').textContent = workflowState.previewData ? 'Preview Ready' : 'Draft';
  document.getElementById('wf-tenant-badge').innerHTML = `<strong>${workflowSession.organization_name || 'Workspace'}</strong> · ${String(workflowSession.plan_type || 'trial').toUpperCase()}`;
  const initials = ((workflowSession.display_name || workflowSession.email || 'MW').trim().split(/\s+/).map((part) => part[0]).join('').slice(0, 2) || 'MW').toUpperCase();
  document.getElementById('wf-profile-chip').innerHTML = `<span class="wf-profile-avatar">${initials}</span><span><strong>${workflowSession.display_name || 'Workspace User'}</strong> · ${workflowSession.role || 'Owner'}</span>`;
}

function renderWorkflowChrome() {
  const config = WORKFLOW_CONFIG[workflowState.lane];
  document.getElementById('wf-title').textContent = `Create ${config.title}`;
  document.getElementById('wf-subtitle').textContent = config.subtitle;

  document.getElementById('wf-step-list').innerHTML = WORKFLOW_STEPS.map((step, index) => `
    <button class="wf-step-btn${workflowState.activeStep === step.id ? ' active' : ''}" type="button" onclick="setWorkflowStep('${step.id}')">
      <span class="wf-step-meta">
        <span class="wf-step-index">Step ${index + 1}</span>
        <span class="wf-step-name">${step.label}</span>
      </span>
      <span class="wf-step-state">${workflowState.activeStep === step.id ? 'Open' : 'Ready'}</span>
    </button>
  `).join('');
}

function renderRightPanel() {
  const missing = [];
  if (workflowState.lane === 'POLICY') {
    if (!getFieldValue('policy_name')) missing.push('Policy name is required.');
    if (!getFieldValue('purpose_scope')) missing.push('Purpose and scope still need author input.');
    if (!getSelectedFrameworks().length) missing.push('No frameworks selected yet.');
  }
  const statusMarkup = missing.length
    ? missing.map((item) => `<div class="wf-status-item warn">${item}</div>`).join('')
    : '<div class="wf-status-item ok">The current draft has the core fields needed for preview generation.</div>';

  document.getElementById('wf-right-panel').innerHTML = `
    <div>
      <div class="wf-panel-kicker">Validation</div>
      <div class="wf-status-list">${statusMarkup}</div>
    </div>
    <div class="wf-stat-card">
      <div class="wf-stat-title">Selected Frameworks</div>
      <div class="wf-stat-value">${getSelectedFrameworks().length}</div>
    </div>
    <div class="wf-stat-card">
      <div class="wf-stat-title">Draft State</div>
      <div class="wf-stat-value">${workflowState.previewData ? 'Previewed' : 'Drafting'}</div>
    </div>
    <div class="wf-stat-card">
      <div class="wf-stat-title">Tenant Guard</div>
      <div class="wf-status-item ok">Authenticated as <strong>${workflowSession.email || 'workspace user'}</strong> inside tenant <strong>${workflowSession.tenant_id}</strong>.</div>
    </div>
  `;
}

function renderMainStep() {
  const main = document.getElementById('wf-main-content');
  main.innerHTML = `
    ${renderMetadataStep()}
    ${renderContentStep()}
    ${renderFrameworksStep()}
    ${renderAssetsStep()}
    ${renderReviewStep()}
    ${renderExportStep()}
  `;
  workflowApplyDraft();
}

function panelClass(step) {
  return `wf-step-panel${workflowState.activeStep === step ? ' active' : ''}`;
}

function renderMetadataStep() {
  const genericType = WORKFLOW_CONFIG[workflowState.lane].title;
  return `
    <section class="${panelClass('metadata')}">
      <div class="wf-grid">
        <div class="wf-card">
          <div class="wf-panel-kicker">Step 1 · Metadata</div>
          <h3>Document identity</h3>
          <div class="wf-field-grid">
            <label class="wf-field"><span class="wf-label">Title</span><input class="wf-input" data-draft-field="policy_name" placeholder="e.g. IT Asset Disposal Policy" oninput="handleDraftChange()"></label>
            <label class="wf-field"><span class="wf-label">Document Type</span><input class="wf-input" value="${genericType}" readonly></label>
            <label class="wf-field"><span class="wf-label">Organization</span><input class="wf-input" value="${escapeHtml(workflowSession.organization_name || 'Midnight Workspace')}" readonly></label>
            <label class="wf-field"><span class="wf-label">Owner</span><input class="wf-input" data-draft-field="owner" placeholder="Brian Word" oninput="handleDraftChange()"></label>
            <label class="wf-field"><span class="wf-label">Industry</span>
              <select class="wf-select" data-draft-field="industry" onchange="handleDraftChange()">
                ${['Healthcare', 'Technology', 'Financial Services', 'Manufacturing', 'Professional Services'].map((opt) => `<option value="${opt}">${opt}</option>`).join('')}
              </select>
            </label>
            <label class="wf-field"><span class="wf-label">Version</span><input class="wf-input" data-draft-field="version" placeholder="1.0" oninput="handleDraftChange()"></label>
            <label class="wf-field"><span class="wf-label">Policy Number</span><input class="wf-input" data-draft-field="policy_number" placeholder="e.g. AC-001" oninput="handleDraftChange()"></label>
            <label class="wf-field"><span class="wf-label">GRC ID</span><input class="wf-input" data-draft-field="grc_id" placeholder="e.g. GRC-AC-001" oninput="handleDraftChange()"></label>
          </div>
        </div>
      </div>
    </section>
  `;
}

function renderContentStep() {
  return `
    <section class="${panelClass('content')}">
      <div class="wf-grid">
        <div class="wf-card">
          <div class="wf-panel-kicker">Step 2 · Content</div>
          <h3>Author the core draft</h3>
          <div class="wf-field-grid single">
            <label class="wf-field"><span class="wf-label">Purpose and Scope</span><textarea class="wf-textarea" data-draft-field="purpose_scope" placeholder="Describe the purpose, scope, and business context for this document…" oninput="handleDraftChange()"></textarea></label>
            <label class="wf-field"><span class="wf-label">Definitions</span><textarea class="wf-textarea" data-draft-field="definitions_text" placeholder="List key terms and definitions…" oninput="handleDraftChange()"></textarea></label>
            <label class="wf-field"><span class="wf-label">Policy Statement</span><textarea class="wf-textarea" data-draft-field="policy_statement" placeholder="Capture the enforceable policy direction…" oninput="handleDraftChange()"></textarea></label>
            <label class="wf-field"><span class="wf-label">Procedures / Requirements</span><textarea class="wf-textarea" data-draft-field="procedures_text" placeholder="Describe operating procedures, controls, or implementation requirements…" oninput="handleDraftChange()"></textarea></label>
          </div>
        </div>
      </div>
    </section>
  `;
}

function renderFrameworksStep() {
  const frameworks = ['HIPAA', 'HITRUST Domains', 'PCI DSS', 'NIST CSF', 'SOC 2', 'ISO 27001'];
  return `
    <section class="${panelClass('frameworks')}">
      <div class="wf-grid">
        <div class="wf-card">
          <div class="wf-panel-kicker">Step 3 · Frameworks</div>
          <h3>Select framework mappings</h3>
          <p style="margin-bottom:16px;color:var(--wf-text-soft);">Your framework selection shapes the compliance language Midnight emphasizes during generation and review.</p>
          <div class="wf-framework-list">
            ${frameworks.map((fw) => `<button type="button" class="wf-pill" data-framework-pill="${fw}" onclick="toggleFramework('${fw}')">${fw}</button>`).join('')}
          </div>
        </div>
      </div>
    </section>
  `;
}

function renderAssetsStep() {
  return `
    <section class="${panelClass('assets')}">
      <div class="wf-grid three">
        <div class="wf-card"><div class="wf-panel-kicker">Step 4 · Embedded Assets</div><h4>Screenshot</h4><p>Upload a PNG or JPG to pair evidence, walkthrough context, or asset snapshots with this document.</p><div style="margin-top:16px;"><button type="button" class="wf-btn" onclick="workflowToast('Media ingestion stays tenant-aware and will be wired into this standalone workspace next.')">Upload Screenshot</button></div></div>
        <div class="wf-card"><div class="wf-panel-kicker">Step 4 · Embedded Assets</div><h4>Video Clip</h4><p>Attach short clips for walkthroughs, operational training, or recorded evidence without leaving the workflow.</p><div style="margin-top:16px;"><button type="button" class="wf-btn" onclick="workflowToast('Video clip capture is staged for this lane and remains protected by the same tenant session.')">Upload Video Clip</button></div></div>
        <div class="wf-card"><div class="wf-panel-kicker">Step 4 · Embedded Assets</div><h4>Diagram</h4><p>Describe a process in plain English and stage a future diagram or swimlane artifact for the export package.</p><div style="margin-top:16px;"><button type="button" class="wf-btn" onclick="workflowToast('Diagram generation is staged for this module.')">Stage Diagram</button></div></div>
      </div>
    </section>
  `;
}

function renderReviewStep() {
  return `
    <section class="${panelClass('review')}">
      <div class="wf-grid">
        <div class="wf-card">
          <div class="wf-panel-kicker">Step 5 · Review</div>
          <h3>Structured draft review</h3>
          <div class="wf-review-surface" id="wf-review-surface">${workflowState.previewText ? escapeHtml(workflowState.previewText) : 'Run preview to review the draft output here before exporting.'}</div>
          <div class="wf-actions-row" style="margin-top:18px;">
            <button type="button" class="wf-btn wf-btn-primary" onclick="runPolicyPreview()">Generate Preview</button>
            <button type="button" class="wf-btn" onclick="saveWorkflowDraft()">Save Draft</button>
          </div>
        </div>
      </div>
    </section>
  `;
}

function renderExportStep() {
  const config = WORKFLOW_CONFIG[workflowState.lane];
  const manualCard = workflowState.lane === 'POLICY' ? `
    <div class="wf-card wf-export-card">
      <div>
        <div class="wf-export-badge">Manual fallback</div>
        <h4 style="margin-top:16px;">Export draft (manual content only)</h4>
        <p>Render whatever you've authored in the Content step into a DOCX without waiting on AI preview. AI-generated sections will be skipped and labeled in the export.</p>
      </div>
      <button type="button" class="wf-btn" onclick="runPolicyManualExport()">Export Manual Draft</button>
    </div>
  ` : '';
  return `
    <section class="${panelClass('export')}">
      <div class="wf-grid">
        <div class="wf-card">
          <div class="wf-panel-kicker">Step 6 · Export</div>
          <h3>Export path</h3>
          <div class="wf-export-grid">
            ${config.exportOptions.map((name) => `
              <div class="wf-card wf-export-card">
                <div>
                  <div class="wf-export-badge">${workflowState.previewData ? 'Ready path' : 'Queued path'}</div>
                  <h4 style="margin-top:16px;">${name}</h4>
                  <p>${workflowState.lane === 'POLICY' ? 'This export will be rendered from the tenant-owned draft after preview/generation completes.' : 'This lane now has a dedicated export workspace shell and will stay on this route as export capabilities deepen.'}</p>
                </div>
                <button type="button" class="wf-btn${workflowState.lane === 'POLICY' ? ' wf-btn-primary' : ''}" ${workflowState.lane === 'POLICY' ? 'onclick="runPolicyGenerate()"' : 'onclick="workflowToast(\'Export flow for this lane is staged in the standalone workspace.\')"'} ${workflowState.lane === 'POLICY' && !workflowState.previewData ? 'disabled' : ''}>${workflowState.lane === 'POLICY' ? 'Generate Export' : 'Export Path'}</button>
              </div>
            `).join('')}
            ${manualCard}
          </div>
        </div>
      </div>
    </section>
  `;
}

function getFieldValue(key) {
  const field = document.querySelector(`[data-draft-field="${key}"]`);
  return field ? String(field.value || '').trim() : '';
}

function getSelectedFrameworks() {
  return Array.from(document.querySelectorAll('[data-framework-pill].active')).map((el) => el.getAttribute('data-framework-pill'));
}

function toggleFramework(name) {
  const pill = document.querySelector(`[data-framework-pill="${CSS.escape(name)}"]`);
  if (!pill) return;
  pill.classList.toggle('active');
  handleDraftChange();
}

function setWorkflowStep(stepId) {
  workflowState.activeStep = stepId;
  renderWorkflowChrome();
  renderMainStep();
  renderRightPanel();
}

function handleDraftChange() {
  workflowState.draft = workflowCollectDraft();
  renderRightPanel();
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function buildPolicyDescription() {
  return [
    getFieldValue('purpose_scope'),
    getFieldValue('definitions_text'),
    getFieldValue('policy_statement'),
    getFieldValue('procedures_text'),
  ].filter(Boolean).join('\n\n');
}

function buildPolicyPreviewText(policyData) {
  if (!policyData || !Array.isArray(policyData.sections)) return 'No policy preview is available yet.';
  return policyData.sections.map((section) => `${section.heading || section.title || 'Section'}\n${section.content || section.body || ''}`.trim()).join('\n\n');
}

async function runPolicyPreview() {
  if (workflowState.lane !== 'POLICY') {
    workflowToast('Preview generation is currently active for the Policy lane first.', true);
    return;
  }

  const name = getFieldValue('policy_name');
  if (!name) {
    setWorkflowStep('metadata');
    workflowToast('Please enter a policy name before previewing.', true);
    return;
  }

  workflowSetLoading(true, 'Bird Eye Drafting', 'Midnight is assembling a structured policy preview for review.');
  const controller = new AbortController();
  const abortTimer = setTimeout(() => controller.abort(), 22000);
  try {
    const response = await workflowApi('/pipeline/create/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        policy_name: name,
        doc_type: 'POLICY',
        industry: getFieldValue('industry') || 'Healthcare',
        frameworks: getSelectedFrameworks(),
        owner: getFieldValue('owner') || workflowSession.display_name || 'Compliance Team',
        description: buildPolicyDescription(),
        policy_number: getFieldValue('policy_number'),
        version: getFieldValue('version') || '1.0',
        grc_id: getFieldValue('grc_id'),
        purpose_scope: getFieldValue('purpose_scope'),
        definitions_text: getFieldValue('definitions_text'),
        policy_statement: getFieldValue('policy_statement'),
        procedures_text: getFieldValue('procedures_text'),
      }),
      signal: controller.signal,
    });

    if (response.status === 504) {
      const body = await response.json().catch(() => ({}));
      workflowToast(body.detail || 'Midnight is taking longer than usual. Try again, or open Bird Talk to refine your input.', true);
      return;
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${response.status}`);
    }

    const data = await response.json();
    workflowState.previewData = data.policy_data;
    workflowState.previewText = buildPolicyPreviewText(data.policy_data);
    workflowState.draft = { ...workflowCollectDraft() };
    document.getElementById('wf-breadcrumb-state').textContent = 'Preview Ready';
    setWorkflowStep('review');
    workflowToast('Policy preview ready.');
  } catch (error) {
    if (error && error.name === 'AbortError') {
      workflowToast('Midnight is taking longer than usual. Try again, or open Bird Talk to refine your input.', true);
    } else {
      workflowToast(error.message || 'Policy preview failed.', true);
    }
  } finally {
    clearTimeout(abortTimer);
    workflowSetLoading(false);
  }
}

async function runPolicyManualExport() {
  if (workflowState.lane !== 'POLICY') {
    workflowToast('Manual export is currently available for the Policy lane only.', true);
    return;
  }
  const name = getFieldValue('policy_name');
  if (!name) {
    setWorkflowStep('metadata');
    workflowToast('Please enter a policy name before exporting.', true);
    return;
  }

  const manualPayload = {
    policy_name: name,
    doc_type: 'POLICY',
    industry: getFieldValue('industry') || 'Healthcare',
    frameworks: getSelectedFrameworks(),
    owner: getFieldValue('owner') || workflowSession.display_name || 'Compliance Team',
    version: getFieldValue('version') || '1.0',
    policy_number: getFieldValue('policy_number') || null,
    purpose_scope: getFieldValue('purpose_scope') || null,
    definitions_text: getFieldValue('definitions_text') || null,
    policy_statement: getFieldValue('policy_statement') || null,
    procedures_text: getFieldValue('procedures_text') || null,
  };

  workflowSetLoading(true, 'Manual Export', 'Rendering manually-authored content into a DOCX. AI-generated sections will be skipped.');
  try {
    const response = await workflowApi('/pipeline/create/manual-export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(manualPayload),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${response.status}`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${name.replace(/\s+/g, '_')}_manual.docx`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    workflowToast('Manual export ready — unfilled sections were skipped with a placeholder note.');
  } catch (error) {
    workflowToast(error.message || 'Manual export failed.', true);
  } finally {
    workflowSetLoading(false);
  }
}

async function runPolicyGenerate() {
  if (workflowState.lane !== 'POLICY') {
    workflowToast('Export generation is currently staged for non-policy lanes.', true);
    return;
  }
  if (!workflowState.previewData) {
    setWorkflowStep('review');
    workflowToast('Generate a preview first so Midnight has a validated draft to export.', true);
    return;
  }

  workflowSetLoading(true, 'Bird Eye Rendering', 'Midnight is rendering the tenant-owned draft into a document export.');
  try {
    const response = await workflowApi('/pipeline/create/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ policy_data: workflowState.previewData }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${response.status}`);
    }
    const data = await response.json();
    if (data?.download?.url) {
      window.open(data.download.url, '_blank', 'noopener');
    }
    workflowToast(`Policy generated — ${data?.policy_data?.policy_name || getFieldValue('policy_name') || 'policy'}`);
  } catch (error) {
    workflowToast(error.message || 'Document generation failed.', true);
  } finally {
    workflowSetLoading(false);
  }
}

function renderWorkflowApp() {
  document.getElementById('app').innerHTML = `
    <div class="wf-app">
      <div class="wf-topbar">
        <div class="wf-breadcrumb">
          <strong>Midnight</strong>
          <span>/</span>
          <span id="wf-breadcrumb-lane">${WORKFLOW_CONFIG[workflowState.lane].title}</span>
          <span>/</span>
          <span id="wf-breadcrumb-state">Draft</span>
        </div>
        <div class="wf-topbar-actions">
          <div class="wf-badge" id="wf-tenant-badge"></div>
          <div class="wf-profile-chip" id="wf-profile-chip"></div>
          <button type="button" class="wf-btn" onclick="saveWorkflowDraft()">Save Draft</button>
          <button type="button" class="wf-btn" onclick="setWorkflowStep('export')">Export</button>
          <button type="button" class="wf-btn wf-btn-primary" onclick="window.location.href='/midnight_dashboard.html'">Back to Dashboard</button>
        </div>
      </div>
      <div class="wf-shell">
        <aside class="wf-sidebar">
          <div class="wf-sidebar-kicker">Document Studio</div>
          <h2 class="wf-sidebar-title">${WORKFLOW_CONFIG[workflowState.lane].title}</h2>
          <p class="wf-sidebar-copy">${WORKFLOW_CONFIG[workflowState.lane].subtitle}</p>
          <div class="wf-step-list" id="wf-step-list"></div>
        </aside>
        <main class="wf-main-card">
          <div class="wf-main-head">
            <div class="wf-panel-kicker">Tenant-Aware Workspace</div>
            <h1 class="wf-main-title" id="wf-title"></h1>
            <p class="wf-main-copy" id="wf-subtitle"></p>
          </div>
          <div id="wf-main-content"></div>
        </main>
        <aside class="wf-right-panel" id="wf-right-panel"></aside>
      </div>
    </div>
    <div class="wf-loading" id="wf-loading">
      <div class="wf-loading-card">
        <h2 class="wf-loading-title" id="wf-loading-title">Working…</h2>
        <p class="wf-loading-copy" id="wf-loading-copy">Midnight is preparing your document workspace.</p>
      </div>
    </div>
    <div class="wf-toast" id="wf-toast"></div>
  `;
  workflowSyncTopbar();
  renderWorkflowChrome();
  renderMainStep();
  renderRightPanel();
}

function getLaneFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const type = (params.get('type') || 'policy').toLowerCase();
  return QUERY_TYPE_TO_LANE[type] || 'POLICY';
}

function syncDocumentTitle() {
  const config = WORKFLOW_CONFIG[workflowState.lane];
  document.title = `Create ${config.title}`;
}

async function bootWorkflowPage() {
  const app = document.getElementById('app');
  if (!app) return;
  workflowState.lane = getLaneFromQuery();
  syncDocumentTitle();

  try {
    workflowSession = await workflowSessionCheck();
  } catch (_) {
    return;
  }

  loadWorkflowDraft();
  renderWorkflowApp();
}

window.setWorkflowStep = setWorkflowStep;
window.toggleFramework = toggleFramework;
window.handleDraftChange = handleDraftChange;
window.saveWorkflowDraft = saveWorkflowDraft;
window.runPolicyPreview = runPolicyPreview;
window.runPolicyGenerate = runPolicyGenerate;

window.addEventListener('DOMContentLoaded', bootWorkflowPage);
