/**
 * DevLink — real-time notification WebSocket client.
 *
 * Connects to ws(s)://<host>/ws/notifications/
 * Handles:
 *   notification.new          → prepend item to dropdown, show toast
 *   notification.count_update → update bell badge
 *
 * NOTE: WebSocket requires the ASGI server (Daphne) to be running.
 * When using plain `runserver` (WSGI), the connection will fail silently
 * after a few retries — this is expected in development.
 */
(function () {
  const badge = document.getElementById('notif-badge');
  const dropdownContainer = document.getElementById('notif-dropdown-container');
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${protocol}://${location.host}/ws/notifications/`;

  let socket = null;
  let reconnectDelay = 2000;
  let failCount = 0;
  const MAX_FAILURES = 3;  // Stop retrying after 3 consecutive failures in dev

  function connect() {
    // Don't retry indefinitely — stop after MAX_FAILURES to avoid console spam
    if (failCount >= MAX_FAILURES) {
      return;
    }

    try {
      socket = new WebSocket(wsUrl);
    } catch (e) {
      // WebSocket constructor itself threw — environment doesn't support it
      return;
    }

    socket.onopen = function () {
      reconnectDelay = 2000;
      failCount = 0;  // Reset on successful connection
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

    socket.onclose = function (event) {
      // Code 4001 = unauthenticated, 1000 = normal close — don't retry
      if (event.code === 4001 || event.code === 1000) {
        return;
      }
      failCount++;
      if (failCount < MAX_FAILURES) {
        setTimeout(connect, Math.min(reconnectDelay, 30000));
        reconnectDelay = Math.min(reconnectDelay * 2, 30000);
      }
      // else: silently stop — ASGI server is likely not running (dev mode)
    };

    socket.onerror = function () {
      // Let onclose handle the retry logic
      socket.close();
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
      .catch(() => {}); // Ignore network errors silently
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
    event.preventDefault();
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
