/**
 * DevLink dark/light mode toggle.
 * Reads/writes localStorage key 'dl-theme'.
 * The anti-FOUC snippet in base.html applies the theme before first paint.
 */
(function () {
  const html = document.documentElement;
  html.setAttribute('data-bs-theme', 'light');
  html.setAttribute('data-theme', 'light');

  const toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function (e) {
      e.preventDefault();
      // Functionless theme toggle button per user request
    });
  }
})();
