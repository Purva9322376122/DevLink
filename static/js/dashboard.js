/**
 * Dashboard - JavaScript Enhancement
 * 
 * Features:
 * - Smooth scroll animations
 * - Theme detection and persistence
 * - Keyboard accessibility enhancements
 * - Dynamic notification handling
 * - Real-time activity feed updates
 * - Responsive interactions
 */

(function () {
  'use strict';

  /**
   * Initialize the dashboard on page load
   */
  function initializeDashboard() {
    initializeTheme();
    initializeFocusIndicators();
    initializeSmoothScroll();
    initializeAnimation();
    initializeKeyboardNavigation();
  }

  /**
   * Initialize theme detection and switching
   */
  function initializeTheme() {
    // Check system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Get user preference from localStorage
    const savedTheme = localStorage.getItem('theme-preference');
    
    if (savedTheme) {
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else if (prefersDark.matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }

    // Listen for system preference changes
    prefersDark.addEventListener('change', (e) => {
      if (!localStorage.getItem('theme-preference')) {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      }
    });
  }

  /**
   * Initialize focus indicators
   */
  function initializeFocusIndicators() {
    const style = document.createElement('style');
    style.textContent = `
      a:focus-visible,
      button:focus-visible,
      .nav-link:focus {
        outline: 3px solid rgba(37, 99, 235, 0.18);
        outline-offset: 2px;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Initialize smooth scrolling
   */
  function initializeSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href === '#') return;

        const target = document.querySelector(href);
        if (!target) return;

        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  /**
   * Initialize entrance animations
   */
  function initializeAnimation() {
    // Use Intersection Observer for scroll animations if available
    if ('IntersectionObserver' in window) {
      const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      };

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            observer.unobserve(entry.target);
          }
        });
      }, observerOptions);

      // Observe cards
      document.querySelectorAll('.card').forEach((card) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(8px)';
        card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        observer.observe(card);
      });
    }
  }

  /**
   * Initialize keyboard navigation
   */
  function initializeKeyboardNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach((link, index) => {
      link.addEventListener('keydown', (e) => {
        // Arrow Down
        if (e.key === 'ArrowDown' && index < navLinks.length - 1) {
          e.preventDefault();
          navLinks[index + 1].focus();
        }
        // Arrow Up
        else if (e.key === 'ArrowUp' && index > 0) {
          e.preventDefault();
          navLinks[index - 1].focus();
        }
        // Home
        else if (e.key === 'Home') {
          e.preventDefault();
          navLinks[0].focus();
        }
        // End
        else if (e.key === 'End') {
          e.preventDefault();
          navLinks[navLinks.length - 1].focus();
        }
      });
    });
  }

  /**
   * Handle notification interactions
   */
  function handleNotifications() {
    const notificationItems = document.querySelectorAll('.notification-item');
    
    notificationItems.forEach((item) => {
      item.addEventListener('click', () => {
        item.classList.toggle('unread');
      });
    });
  }

  /**
   * Format relative time
   */
  function formatTime(date) {
    const now = new Date();
    const diff = now - date;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString();
  }

  /**
   * Initialize activity feed real-time updates
   */
  function initializeActivityFeed() {
    const activityTimeline = document.querySelector('.activity-timeline');
    if (!activityTimeline) return;

    const items = activityTimeline.querySelectorAll('.activity-item');
    
    // Update timestamps every minute
    setInterval(() => {
      items.forEach((item) => {
        const timeElement = item.querySelector('.activity-time');
        if (timeElement && timeElement.dataset.timestamp) {
          const timestamp = new Date(timeElement.dataset.timestamp);
          timeElement.textContent = formatTime(timestamp) + ' ago';
        }
      });
    }, 60000);
  }

  /**
   * Handle responsive sidebar behavior
   */
  function handleResponsiveSidebar() {
    const sidebar = document.querySelector('.dashboard-sidebar');
    const sidebarRight = document.querySelector('.dashboard-sidebar-right');
    
    if (!sidebar || !sidebarRight) return;

    const handleResize = () => {
      const width = window.innerWidth;
      
      if (width <= 768) {
        // Mobile: collapse sidebars
        sidebar.style.maxHeight = 'none';
        sidebarRight.style.maxHeight = 'none';
      } else if (width <= 1200) {
        // Tablet: show as grid
        sidebar.style.maxHeight = 'none';
        sidebarRight.style.maxHeight = 'none';
      }
      // Desktop: sticky positioning via CSS
    };

    window.addEventListener('resize', debounce(handleResize, 250));
    handleResize();
  }

  /**
   * Debounce utility
   */
  function debounce(fn, delay) {
    let timeoutId;
    return function (...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    };
  }

  /**
   * Add breadcrumb-style current page indicator
   */
  function updateNavigationState() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach((link) => {
      const href = link.getAttribute('href');
      if (href && currentPath.includes(href)) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }

  /**
   * Initialize stats hover effects
   */
  function initializeStatsInteraction() {
    const statItems = document.querySelectorAll('.stat-item');
    
    statItems.forEach((item) => {
      item.addEventListener('mouseenter', () => {
        item.style.transform = 'translateX(2px)';
      });

      item.addEventListener('mouseleave', () => {
        item.style.transform = 'translateX(0)';
      });
    });
  }

  /**
   * Initialize copy-to-clipboard for share
   */
  function initializeShareButtons() {
    const shareButtons = document.querySelectorAll('[data-share]');
    
    shareButtons.forEach((button) => {
      button.addEventListener('click', async (e) => {
        e.preventDefault();
        
        const shareUrl = button.dataset.share;
        
        try {
          await navigator.clipboard.writeText(shareUrl);
          
          // Show feedback
          const originalText = button.innerHTML;
          button.innerHTML = '<i class="bi bi-check"></i>Copied!';
          button.style.color = '#10b981';
          
          setTimeout(() => {
            button.innerHTML = originalText;
            button.style.color = '';
          }, 2000);
        } catch (err) {
          console.error('Failed to copy:', err);
        }
      });
    });
  }

  /**
   * Handle section expansion/collapse
   */
  function initializeSectionToggle() {
    const sectionHeaders = document.querySelectorAll('.section-header');
    
    sectionHeaders.forEach((header) => {
      const section = header.closest('.content-section');
      if (!section) return;

      header.style.cursor = 'pointer';
      
      header.addEventListener('click', () => {
        const card = section.querySelector('.card');
        if (card) {
          card.style.maxHeight = card.style.maxHeight ? '' : '0';
          card.style.overflow = 'hidden';
          card.style.transition = 'max-height 0.3s ease';
        }
      });
    });
  }

  /**
   * Initialize print styles
   */
  function initializePrintButton() {
    if (window.location.search.includes('print')) {
      document.body.classList.add('print-mode');
      window.addEventListener('afterprint', () => {
        document.body.classList.remove('print-mode');
      });
    }
  }

  /**
   * Entry point
   */
  document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
    handleNotifications();
    initializeActivityFeed();
    handleResponsiveSidebar();
    updateNavigationState();
    initializeStatsInteraction();
    initializeShareButtons();
    initializeSectionToggle();
    initializePrintButton();
  });

  // Handle visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      // Page became visible - could refresh activity feed here
      updateNavigationState();
    }
  });
})();
