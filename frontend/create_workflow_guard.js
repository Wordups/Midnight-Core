(function () {
  const shell = document.querySelector('[data-create-workflow-shell]');
  if (!shell) return;

  const iframe = shell.querySelector('iframe');
  const statusEl = shell.querySelector('[data-create-workflow-status]');
  const lane = shell.getAttribute('data-lane') || 'POLICY';
  const title = shell.getAttribute('data-title') || 'Create Workflow';
  const target = `/midnight_dashboard.html?create_lane=${encodeURIComponent(lane)}&create_focus=1`;

  function setStatus(message) {
    if (statusEl) statusEl.textContent = message;
  }

  function redirect(path) {
    window.location.replace(path);
  }

  async function boot() {
    document.title = title;
    setStatus('Checking your Midnight workspace…');

    try {
      const response = await fetch('/auth/session', {
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
      });

      if (!response.ok) {
        redirect('/login.html');
        return;
      }

      const session = await response.json();
      if (!session?.authenticated) {
        redirect('/login.html');
        return;
      }

      if (session.access_state === 'needs_onboarding' || !session.profile_exists || !session.tenant_assigned || !session.tenant_id) {
        redirect('/onboarding/plan');
        return;
      }

      if (session.access_state === 'upgrade_required') {
        redirect(`/access_denied.html?reason=${encodeURIComponent(session.access_detail || 'Upgrade required to continue.')}`);
        return;
      }

      iframe.src = target;
      shell.classList.add('workflow-ready');
      setStatus('Loading workspace…');
    } catch (_) {
      redirect('/login.html');
    }
  }

  if (iframe) {
    iframe.addEventListener('load', () => {
      setStatus('');
    });
  }

  boot();
})();
