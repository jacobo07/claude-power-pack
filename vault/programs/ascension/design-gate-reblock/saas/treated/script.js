document.addEventListener("DOMContentLoaded", () => {
  // Hero action items: keep the open count in sync with the checkboxes.
  const count = document.getElementById("task-count");
  const boxes = document.querySelectorAll(".tasks input[type=checkbox]");
  const updateCount = () => {
    const open = [...boxes].filter((b) => !b.checked).length;
    count.textContent = open === 0 ? "All done" : `${open} open`;
  };
  boxes.forEach((b) => b.addEventListener("change", updateCount));

  // Billing toggle: swap plan prices between monthly and annual.
  const options = document.querySelectorAll(".billing__opt");
  const amounts = document.querySelectorAll(".plan__amount");
  options.forEach((opt) => {
    opt.addEventListener("click", () => {
      const period = opt.dataset.period;
      options.forEach((o) => o.setAttribute("aria-pressed", String(o === opt)));
      amounts.forEach((a) => { a.textContent = `$${a.dataset[period]}`; });
      document.querySelectorAll("[data-billed]").forEach((b) => {
        b.textContent = period === "annual" ? "Billed annually" : "Billed monthly";
      });
    });
  });
});
