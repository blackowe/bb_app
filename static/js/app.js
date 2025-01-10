// General shared logic for the BB_App
document.addEventListener("DOMContentLoaded", function () {
  console.log("BB_App initialized.");
  // Add any shared functionality here, e.g., navbar interactions or global event listeners.

  // Example: Highlight active navigation link
  const navLinks = document.querySelectorAll("nav a");
  const currentPath = window.location.pathname;

  navLinks.forEach(link => {
      if (link.getAttribute("href") === currentPath) {
          link.classList.add("active");
      }
  });
});
