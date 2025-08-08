document.addEventListener('DOMContentLoaded', function () {
  const bar = document.getElementById('progress-bar');
  const text = document.getElementById('progress-text');
  if (!bar || !text) return;

  const steps = [
    { p: 20, t: 'Connexion au service…' },
    { p: 45, t: 'Création de la vignette clinique…' },
    { p: 70, t: 'Formulation de la question…' },
    { p: 90, t: "Finalisation de l'exercice…" }
  ];
  let i = 0;
  function advance() {
    if (i < steps.length) {
      bar.style.width = steps[i].p + '%';
      text.textContent = steps[i].t;
      i++;
      setTimeout(advance, 900);
    }
  }
  advance();

  function prepare() {
    fetch('/national/quiz_prepare', { method: 'GET', credentials: 'same-origin' })
      .then(async (res) => {
        if (!res.ok) throw new Error('prepare_failed');
        const data = await res.json();
        if (data && data.ok) {
          bar.style.width = '100%';
          text.textContent = 'Prêt !';
          setTimeout(() => { window.location.href = '/national/quiz'; }, 300);
        } else {
          throw new Error((data && data.error) || 'unknown_error');
        }
      })
      .catch((e) => {
        text.textContent = 'Une erreur est survenue. Veuillez réessayer.';
        bar.style.background = 'var(--danger)';
        console.error('quiz_prepare error', e);
      });
  }

  setTimeout(prepare, 300);
});

