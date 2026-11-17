// Scroll reveal via IntersectionObserver and the live counter in the hero sample.
(function () {
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  }

  // Plan buttons carry their plan into the signup form; the form itself posts to /signup.
  var planField = document.querySelector('[data-plan-field]');
  var planLabel = document.querySelector('[data-plan-label]');
  var email = document.getElementById('email');
  document.querySelectorAll('[data-plan]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var plan = btn.getAttribute('data-plan');
      if (planField) planField.value = plan;
      if (planLabel) planLabel.textContent = plan === 'solo' ? 'Solo' : 'Team';
      if (email) setTimeout(function () { email.focus({ preventScroll: true }); }, 400);
    });
  });

  var form = document.querySelector('.signup__form');
  var error = document.getElementById('email-error');
  if (form && email && error) {
    form.addEventListener('submit', function (e) {
      if (!email.checkValidity() || !email.value.trim()) {
        e.preventDefault();
        email.setAttribute('aria-invalid', 'true');
        error.hidden = false;
        email.focus();
      }
    });
    email.addEventListener('input', function () {
      if (email.getAttribute('aria-invalid') === 'true' && email.checkValidity()) {
        email.removeAttribute('aria-invalid');
        error.hidden = true;
      }
    });
  }

  var boxes = document.querySelectorAll('.task input[type="checkbox"]');
  var count = document.querySelector('[data-count]');
  if (!count || !boxes.length) return;
  function update() {
    var done = 0;
    boxes.forEach(function (b) { if (b.checked) done += 1; });
    count.textContent = done + ' of ' + boxes.length + ' done';
  }
  boxes.forEach(function (b) { b.addEventListener('change', update); });
  update();
})();
