/**
 * devlink.js — reusable UI helpers
 * Exports: copyCode, initBookmarkToggle, initReportModal
 */

// ── Copy code ──────────────────────────────────────────────────────────────
function copyCode(button) {
  const pre = button.closest('.position-relative')?.querySelector('code')
            || button.closest('.code-block')?.querySelector('code');
  if (!pre) return;
  navigator.clipboard.writeText(pre.textContent.trim()).then(() => {
    const orig = button.innerHTML;
    button.innerHTML = '<i class="bi bi-check2"></i>';
    setTimeout(() => { button.innerHTML = orig; }, 1500);
    if (typeof showToast !== 'undefined') showToast('Code copied!', 'success');
  });
}

// ── Report modal ───────────────────────────────────────────────────────────
function initReportModal(formId = 'reportForm', modalId = 'reportModal') {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const data = new FormData(form);
    const resp = await fetch('/problems/report/', { method: 'POST', body: data });
    const json = await resp.json();
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (json.status === 'ok') {
      modal?.hide();
      if (typeof showToast !== 'undefined') showToast('Report submitted. Thank you.', 'success');
    } else {
      if (typeof showToast !== 'undefined') showToast(json.message || 'Error submitting report.', 'error');
    }
  });
}

// ── Markdown preview ───────────────────────────────────────────────────────
function initMarkdownPreview(textareaId, previewId) {
  const textarea = document.getElementById(textareaId);
  const preview = document.getElementById(previewId);
  if (!textarea || !preview) return;
  let debounce;
  textarea.addEventListener('input', function () {
    clearTimeout(debounce);
    debounce = setTimeout(async () => {
      const csrf = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
      const fd = new FormData();
      fd.append('text', textarea.value);
      const resp = await fetch('/solutions/preview/', { method: 'POST', headers: { 'X-CSRFToken': csrf }, body: fd });
      if (resp.ok) {
        const data = await resp.json();
        preview.innerHTML = data.html;
        if (typeof Prism !== 'undefined') Prism.highlightAllUnder(preview);
      }
    }, 400);
  });
}

// ── Auto-init on DOMContentLoaded ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  // Bookmark feature removed from UI — initBookmarkToggle disabled
  initReportModal();
});
