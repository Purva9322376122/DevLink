/**
 * DevLink dark/light mode toggle.
 * Reads/writes localStorage key 'dl-theme'.
 * The anti-FOUC snippet in base.html applies the theme before first paint.
 */
(function () {
  window.applyDevlinkTheme = function (theme) {
    var activeTheme = theme === 'dark' ? 'dark' : 'light';
    var html = document.documentElement;

    html.setAttribute('data-bs-theme', activeTheme);
    html.setAttribute('data-theme', activeTheme);
    
    try {
      localStorage.setItem('dl-theme', activeTheme);
    } catch (e) {}

    var sunIcon = document.getElementById('theme-icon-light');
    var moonIcon = document.getElementById('theme-icon-dark');
    var toggleBtn = document.getElementById('theme-toggle');

    if (activeTheme === 'dark') {
      if (sunIcon) sunIcon.classList.add('d-none');
      if (moonIcon) moonIcon.classList.remove('d-none');
      if (toggleBtn) {
        toggleBtn.setAttribute('title', 'Switch to light mode');
        toggleBtn.setAttribute('aria-label', 'Switch to light mode');
      }
    } else {
      if (moonIcon) moonIcon.classList.add('d-none');
      if (sunIcon) sunIcon.classList.remove('d-none');
      if (toggleBtn) {
        toggleBtn.setAttribute('title', 'Switch to dark mode');
        toggleBtn.setAttribute('aria-label', 'Switch to dark mode');
      }
    }

    // Notify any listening components (e.g. Monaco editor, charts)
    window.dispatchEvent(new CustomEvent('dl-theme-change', { detail: { theme: activeTheme } }));
  };

  window.toggleDevlinkTheme = function (e) {
    if (e && e.preventDefault) e.preventDefault();
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    var nextTheme = current === 'dark' ? 'light' : 'dark';
    window.applyDevlinkTheme(nextTheme);
  };

  // Immediate init on script load
  try {
    var stored = localStorage.getItem('dl-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    window.applyDevlinkTheme(stored);
  } catch (e) {}

  document.addEventListener('DOMContentLoaded', function () {
    try {
      var stored = localStorage.getItem('dl-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      window.applyDevlinkTheme(stored);
    } catch (e) {}

    var toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.removeEventListener('click', window.toggleDevlinkTheme);
      toggle.addEventListener('click', window.toggleDevlinkTheme);
    }
  });
})();
