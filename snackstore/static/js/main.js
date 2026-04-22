// Main JavaScript for Bookstore

document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 Bookstore JavaScript loaded!");

  // Auto hide alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      if (alert) {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      }
    }, 5000);
  });

  // Add loading state to buttons
  const buttons = document.querySelectorAll('button[type="submit"]');
  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
      button.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status"></span> Đang xử lý...';
      button.disabled = true;
    });
  });

  // Cart functionality
  updateCartCount();
});

function updateCartCount() {
  // Placeholder for cart count update
  const cartCount = document.getElementById("cart-count");
  if (cartCount) {
    // TODO: Get actual cart count from session/API
    cartCount.textContent = "0";
  }
}

function addToCart(bookId) {
  // Placeholder for add to cart functionality
  console.log("Adding book " + bookId + " to cart");
  // TODO: Implement AJAX add to cart
}
