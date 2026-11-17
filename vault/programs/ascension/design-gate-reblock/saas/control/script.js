(function () {
  var buttons = document.querySelectorAll(".toggle-btn");
  var amounts = document.querySelectorAll(".amount");
  var billed = document.querySelectorAll(".billed");

  function setPeriod(period) {
    buttons.forEach(function (btn) {
      var active = btn.dataset.period === period;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    amounts.forEach(function (el) {
      el.textContent = "$" + el.dataset[period];
    });
    billed.forEach(function (el) {
      el.textContent = el.dataset[period];
    });
  }

  buttons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      setPeriod(btn.dataset.period);
    });
  });

  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
