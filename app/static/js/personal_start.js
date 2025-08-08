document.addEventListener('DOMContentLoaded', function () {
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
      label.textContent = text || 'Préparation du challenge personnel…';

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

  // Spinner when starting personal challenge from topic selection
  var startForm = document.getElementById('personal-topics-form') || document.querySelector('form[action$="select_topic"]');
  if (startForm) {
    startForm.addEventListener('submit', function () {
      var btn = document.querySelector('button[form="' + startForm.id + '"]') || startForm.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Préparation…';
      }
      showOverlay('Préparation du challenge personnel…');
    });
  }

  // Spinner when requesting a new personal question from results page
  var nextForms = document.querySelectorAll('form[action$="next_question"]');
  nextForms.forEach(function (nf) {
    nf.addEventListener('submit', function () {
      var btn = nf.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Préparation…';
      }
      showOverlay('Préparation de la nouvelle question…');
    });
  });
});
