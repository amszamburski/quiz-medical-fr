document.addEventListener('DOMContentLoaded', function () {
  var form = document.querySelector('form[action$="select_team"]');
  if (!form) return;

  function showOverlay(text) {
    var overlay = document.getElementById('eval-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'eval-overlay';
      overlay.style.position = 'fixed';
      overlay.style.inset = '0';
      overlay.style.background = 'rgba(255,255,255,0.8)';
      overlay.style.display = 'flex';
      overlay.style.alignItems = 'center';
      overlay.style.justifyContent = 'center';
      overlay.style.zIndex = '9999';

      var spinner = document.createElement('div');
      spinner.style.width = '48px';
      spinner.style.height = '48px';
      spinner.style.border = '4px solid var(--border)';
      spinner.style.borderTopColor = 'var(--accent-primary)';
      spinner.style.borderRadius = '50%';
      spinner.style.margin = '0 auto';
      spinner.style.animation = 'sfardle-spin 1s linear infinite';

      var label = document.createElement('div');
      label.style.marginTop = '12px';
      label.style.color = 'var(--text-secondary)';
      label.textContent = text || 'Préparation de votre question…';

      var wrap = document.createElement('div');
      wrap.style.textAlign = 'center';
      wrap.appendChild(spinner);
      wrap.appendChild(label);
      overlay.appendChild(wrap);

      document.body.appendChild(overlay);

      if (!document.getElementById('sfardle-spin-style')) {
        var style = document.createElement('style');
        style.id = 'sfardle-spin-style';
        style.textContent = '@keyframes sfardle-spin { to { transform: rotate(360deg); } }';
        document.head.appendChild(style);
      }
    } else {
      overlay.style.display = 'flex';
    }
  }

  function hideOverlay() {
    var overlay = document.getElementById('eval-overlay');
    if (overlay) overlay.style.display = 'none';
  }

  async function prepareQuiz() {
    try {
      var res = await fetch('/national/quiz_prepare', { method: 'GET', credentials: 'same-origin' });
      if (res.ok) {
        var data = await res.json();
        if (data && data.ok) return true;
      }
    } catch (e) {}
    await new Promise(r => setTimeout(r, 1000));
    try {
      var res2 = await fetch('/national/quiz_prepare', { method: 'GET', credentials: 'same-origin' });
      if (res2.ok) {
        var data2 = await res2.json();
        if (data2 && data2.ok) return true;
      }
    } catch (e2) {}
    return false;
  }

  form.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    var team = (form.querySelector('[name="team"]') || {}).value;
    if (!team) return;

    showOverlay('Préparation de votre question…');

    var csrf = (form.querySelector('[name="csrf_token"]') || {}).value || '';
    var body = new URLSearchParams();
    body.set('team', team);
    if (csrf) body.set('csrf_token', csrf);

    try {
      await fetch(form.action, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString()
      });
      var ok = await prepareQuiz();
      if (ok) {
        window.location.href = '/national/quiz';
      } else {
        hideOverlay();
        alert('Une erreur est survenue lors de la préparation. Réessayez.');
      }
    } catch (e) {
      hideOverlay();
      alert('Erreur réseau. Réessayez.');
    }
  });
});

