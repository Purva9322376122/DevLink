/**
 * devlink-monaco.js
 * Reusable Monaco Editor helper.
 *
 * Usage:
 *   <div id="monaco-container" style="height:300px"></div>
 *   <textarea name="code" id="id_code" class="d-none"></textarea>
 *   <select id="language-select">…</select>
 *
 *   Then call: DevLinkMonaco.init({ container, textarea, langSelect })
 */
const DevLinkMonaco = (() => {
  const LANG_MAP = {
    python: 'python', javascript: 'javascript', java: 'java',
    cpp: 'cpp', c: 'c', go: 'go', rust: 'rust', php: 'php',
    typescript: 'typescript', sql: 'sql', json: 'json', yaml: 'yaml',
  };

  function isDark() {
    return document.documentElement.getAttribute('data-bs-theme') === 'dark';
  }

  function init({ containerId = 'monaco-container', textareaId = 'id_code', langSelectId = 'language-select', readOnly = false } = {}) {
    const container = document.getElementById(containerId);
    const textarea = document.getElementById(textareaId);
    const langSelect = document.getElementById(langSelectId);
    if (!container) return;

    require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.47.0/min/vs' } });
    require(['vs/editor/editor.main'], function () {
      const editor = monaco.editor.create(container, {
        value: textarea ? textarea.value : '',
        language: LANG_MAP[langSelect ? langSelect.value : 'python'] || 'plaintext',
        theme: isDark() ? 'vs-dark' : 'vs',
        automaticLayout: true,
        readOnly: readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        scrollBeyondLastLine: false,
        lineNumbers: 'on',
      });

      if (langSelect) {
        langSelect.addEventListener('change', () => {
          monaco.editor.setModelLanguage(editor.getModel(), LANG_MAP[langSelect.value] || 'plaintext');
        });
      }

      // Dark mode sync
      document.getElementById('theme-toggle')?.addEventListener('click', () => {
        monaco.editor.setTheme(isDark() ? 'vs-dark' : 'vs');
      });

      // Sync to textarea on form submit
      if (textarea) {
        const form = container.closest('form');
        form?.addEventListener('submit', () => { textarea.value = editor.getValue(); });
      }

      // Expose for external use
      container._monacoEditor = editor;
    });
  }

  return { init, LANG_MAP };
})();
