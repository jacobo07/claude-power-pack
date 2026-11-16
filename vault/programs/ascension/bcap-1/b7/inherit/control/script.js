(function () {
  // Mobile navigation
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');

  function setNav(open) {
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  }

  toggle.addEventListener('click', function () {
    setNav(toggle.getAttribute('aria-expanded') !== 'true');
  });

  nav.addEventListener('click', function (e) {
    if (e.target.closest('a')) setNav(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) {
      setNav(false);
      toggle.focus();
    }
  });

  // Monthly / yearly billing toggle
  var options = document.querySelectorAll('.toggle-option');
  var priced = document.querySelectorAll('[data-monthly][data-yearly]');

  options.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var period = btn.getAttribute('data-period');
      options.forEach(function (o) {
        var active = o === btn;
        o.classList.toggle('is-active', active);
        o.setAttribute('aria-pressed', String(active));
      });
      priced.forEach(function (el) {
        el.textContent = el.getAttribute('data-' + period);
      });
    });
  });

  // Footer year
  document.getElementById('year').textContent = new Date().getFullYear();
})();
