(function () {
  const input = document.getElementById("password");
  const rules = document.getElementById("password-rules");
  if (!input || !rules) return;

  const checks = {
    length: (v) => v.length >= 8,
    upper: (v) => /[A-Z]/.test(v),
    lower: (v) => /[a-z]/.test(v),
    digit: (v) => /\d/.test(v),
    special: (v) => /[!@#$%^&*(),.?":{}|<>\[\]\\/_+=\-~`]/.test(v),
  };

  function updateRules() {
    const value = input.value;
    rules.querySelectorAll("li[data-rule]").forEach((item) => {
      const rule = item.dataset.rule;
      const met = checks[rule] ? checks[rule](value) : false;
      item.classList.toggle("is-met", met);
      const icon = item.querySelector(".password-rule-icon");
      if (icon) icon.textContent = met ? "✓" : "○";
    });
  }

  input.addEventListener("input", updateRules);
})();
