document.addEventListener('DOMContentLoaded', function () {
  var form = document.querySelector('form[action$="submit_answer"]');
  if (!form) return;

  var btn = form.querySelector('button[type="submit"]');
  form.addEventListener('submit', function () {
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Évaluation en cours…';
    }

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
      label.textContent = 'Évaluation de votre réponse…';

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
  });
});

