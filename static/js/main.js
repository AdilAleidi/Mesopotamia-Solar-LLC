document.addEventListener("DOMContentLoaded", function () {
  const menuToggle = document.getElementById("menuToggle");
  const nav = document.getElementById("mainNav");

  if (menuToggle && nav) {
    // Initialize ARIA
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-controls", "mainNav");

    menuToggle.addEventListener("click", function () {
      const isOpen = nav.classList.toggle("active");
      menuToggle.setAttribute("aria-expanded", isOpen);
      document.body.style.overflow = isOpen ? "hidden" : "auto";
    });

    // Handle all clicks
    document.addEventListener("click", function (e) {
      // Close when clicking outside
      if (
        window.innerWidth <= 768 &&
        nav.classList.contains("active") &&
        !e.target.closest("#mainNav") &&
        !e.target.closest("#menuToggle")
      ) {
        nav.classList.remove("active");
        menuToggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "auto";
      }

      // Close when clicking links
      if (e.target.closest("#mainNav a") && window.innerWidth <= 768) {
        nav.classList.remove("active");
        menuToggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "auto";
      }
    });

    // Close with Escape key
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("active")) {
        nav.classList.remove("active");
        menuToggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "auto";
        menuToggle.focus();
      }
    });
  }
});
