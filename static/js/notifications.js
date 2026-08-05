/**
 * DevLink — real-time notification client.
 *
 * Connects to ws(s)://<host>/ws/notifications/
 * Handles:
 *   notification.new          → prepend item to dropdown, show toast
 *   notification.count_update → update bell badge
 *
 * Fallback:
 *   If WebSockets are unavailable or server runs on standard WSGI (manage.py runserver),
 *   it cleanly switches to HTTP polling (/notifications/unread-count/) every 30 seconds
 *   without logging repeated console errors.
 */
(function () {
  const badge = document.getElementById('notif-badge');
  const dropdownContainer = document.getElementById('notif-dropdown-container');

  // Exit cleanly if notification UI elements are missing
  if (!badge && !dropdownContainer) return;

  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${protocol}://${location.host}/ws/notifications/`;

  let socket = null;
  let usePollingFallback = false;
  let pollInterval = null;

  function startPolling() {
    if (pollInterval) return;
    usePollingFallback = true;
    fetchUnreadCount();
    pollInterval = setInterval(fetchUnreadCount, 30000); // Poll every 30s
  }

  function fetchUnreadCount() {
    fetch('/notifications/unread-count/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data && typeof data.unread_count === 'number') {
          updateBadge(data.unread_count);
        }
      })
      .catch(() => {}); // Suppress network errors
  }

  function connect() {
    if (usePollingFallback) return;

    try {
      socket = new WebSocket(wsUrl);
    } catch (e) {
      startPolling();
      return;
    }

    socket.onopen = function () {
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    };

    socket.onmessage = function (e) {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'notification.count_update') {
          updateBadge(data.unread_count);
        }
        if (data.type === 'notification.new') {
          showToastNotification(data);
          refreshDropdown();
        }
      } catch (err) {
        // Ignore malformed messages
      }
    };

    socket.onclose = function () {
      // On WebSocket close/failure (e.g. 404 on WSGI dev server), gracefully fall back to polling
      startPolling();
    };

    socket.onerror = function () {
      if (socket) {
        try { socket.close(); } catch (e) {}
      }
      startPolling();
    };
  }

  function updateBadge(count) {
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.style.display = '';
    } else {
      badge.style.display = 'none';
    }
  }

  function showToastNotification(data) {
    if (typeof Toastify !== 'undefined') {
      Toastify({
        text: data.preview || 'You have a new notification',
        duration: 4000,
        gravity: 'bottom',
        position: 'right',
        onClick: function () { if (data.target_url) location.href = data.target_url; },
        style: { background: 'linear-gradient(135deg,#6366f1,#0ea5e9)', borderRadius: '8px' },
        stopOnFocus: true,
      }).showToast();
    }
  }

  function refreshDropdown() {
    if (!dropdownContainer) return;
    fetch('/notifications/dropdown/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(r => r.ok ? r.text() : null)
      .then(html => { if (html) dropdownContainer.innerHTML = html; })
      .catch(() => {});
  }

  // Mark single notification read via AJAX
  window.markRead = function (event, notifId) {
    fetch(`/notifications/${notifId}/read/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf(), 'X-Requested-With': 'XMLHttpRequest' },
    }).then(() => refreshDropdown()).catch(() => {});
  };

  // Mark all read via AJAX
  window.markAllRead = function (event) {
    if (event) event.preventDefault();
    fetch('/notifications/mark-all-read/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf(), 'X-Requested-With': 'XMLHttpRequest' },
    }).then(() => {
      updateBadge(0);
      refreshDropdown();
    }).catch(() => {});
  };

  function getCsrf() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  connect();
})();
