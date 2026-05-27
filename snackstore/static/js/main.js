document.addEventListener("DOMContentLoaded", function () {
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = "opacity .25s ease, transform .25s ease";
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-6px)";
      setTimeout(function () {
        if (alert.parentNode) alert.parentNode.removeChild(alert);
      }, 260);
    }, 5000);
  });
});

function toggleDropdown() {
  const dropdown = document.getElementById("userDropdown");
  if (!dropdown) return;
  dropdown.classList.toggle("show");
}

document.addEventListener("click", function (event) {
  const dropdown = document.getElementById("userDropdown");
  if (!dropdown) return;
  const isInside = event.target.closest(".user-dropdown");
  if (!isInside) dropdown.classList.remove("show");
});
