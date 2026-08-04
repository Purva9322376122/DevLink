/**
 * Opportunity Detail Page - JavaScript
 * Handles interactivity: share buttons, form validation, smooth UX
 */

document.addEventListener('DOMContentLoaded', function () {
  initializeShareButtons();
  initializeFormValidation();
  initializeSmoothScroll();
});

/**
 * Initialize Share Buttons Functionality
 */
function initializeShareButtons() {
  const shareButtons = document.querySelectorAll('.share-btn');
  const pageTitle = document.querySelector('.hero-title')?.textContent || 'Opportunity on DevLink';
  const pageUrl = window.location.href;

  shareButtons.forEach((button) => {
    button.addEventListener('click', function (e) {
      e.preventDefault();

      const shareType = this.getAttribute('data-share');

      if (shareType === 'twitter') {
        shareOnTwitter(pageTitle, pageUrl);
      } else if (shareType === 'linkedin') {
        shareOnLinkedIn(pageUrl);
      } else if (shareType === 'copy') {
        copyToClipboard(pageUrl, this);
      }
    });
  });
}

/**
 * Share on Twitter
 */
function shareOnTwitter(title, url) {
  const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`;
  window.open(twitterUrl, 'twitter', 'width=550,height=420');
}

/**
 * Share on LinkedIn
 */
function shareOnLinkedIn(url) {
  const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
  window.open(linkedInUrl, 'linkedin', 'width=550,height=420');
}

/**
 * Copy Link to Clipboard
 */
function copyToClipboard(text, button) {
  navigator.clipboard.writeText(text).then(function () {
    // Show success feedback
    const originalText = button.textContent;
    const originalHTML = button.innerHTML;

    button.textContent = '✓ Copied!';
    button.classList.add('copied');

    // Reset after 2 seconds
    setTimeout(function () {
      button.innerHTML = originalHTML;
      button.classList.remove('copied');
    }, 2000);
  }).catch(function (err) {
    console.error('Failed to copy:', err);
    // Fallback: select text and use execCommand
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);

    button.textContent = '✓ Copied!';
    setTimeout(function () {
      button.innerHTML = '<i class="bi bi-link-45deg"></i><span>Copy</span>';
    }, 2000);
  });
}

/**
 * Initialize Form Validation
 */
function initializeFormValidation() {
  const applyForm = document.querySelector('.apply-form');

  if (applyForm) {
    const messageField = applyForm.querySelector('#message');
    const submitButton = applyForm.querySelector('[type="submit"]');

    // Real-time validation feedback
    if (messageField) {
      messageField.addEventListener('input', function () {
        const charCount = this.value.length;
        const minLength = parseInt(this.getAttribute('minlength')) || 10;

        if (charCount < minLength) {
          this.classList.add('invalid');
          submitButton.disabled = true;
        } else {
          this.classList.remove('invalid');
          submitButton.disabled = false;
        }
      });
    }

    // Form submission with loading state
    applyForm.addEventListener('submit', function (e) {
      // Validation is handled by HTML5, no need to prevent default
      if (messageField && messageField.value.length < 10) {
        e.preventDefault();
        messageField.focus();
        messageField.classList.add('invalid');
        return false;
      }

      // Add loading state to button
      submitButton.disabled = true;
      const originalHTML = submitButton.innerHTML;
      submitButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Submitting...';

      // Form will submit naturally
      // If you want to handle it with AJAX, uncomment below:
      /*
      e.preventDefault();
      
      const formData = new FormData(this);
      
      fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
      })
      .then(response => {
        if (response.ok) {
          // Show success message
          submitButton.innerHTML = '<i class="bi bi-check-circle"></i> Applied!';
          submitButton.classList.add('success');
          
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        } else {
          throw new Error('Application failed');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        submitButton.innerHTML = '<i class="bi bi-exclamation-circle"></i> Error - Try Again';
        submitButton.classList.add('error');
        submitButton.disabled = false;
        
        setTimeout(() => {
          submitButton.innerHTML = originalHTML;
          submitButton.classList.remove('error');
        }, 2000);
      });
      */
    });
  }
}

/**
 * Smooth Scroll to Section
 */
function initializeSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href === '#') return;

      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();

        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });

        // Add focus for accessibility
        target.focus();
      }
    });
  });
}

/**
 * Keyboard Accessibility Enhancements
 */
document.addEventListener('keydown', function (e) {
  // Close modals/dropdowns on Escape
  if (e.key === 'Escape') {
    // Handle any open modals here
  }
});

/**
 * Intersection Observer for Lazy Loading & Animations
 */
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  // Observe all cards for entrance animation
  document.querySelectorAll('.section-card, .sidebar-card').forEach((card) => {
    observer.observe(card);
  });
}

/**
 * Handle Print Functionality
 */
function printOpportunity() {
  window.print();
}

/**
 * Share Utility - Open Share Dialog
 */
function openShareDialog() {
  const url = window.location.href;
  const title = document.querySelector('.hero-title')?.textContent || 'Opportunity';

  if (navigator.share) {
    navigator.share({
      title: title,
      text: 'Check out this opportunity on DevLink!',
      url: url,
    }).catch(err => console.log('Error sharing:', err));
  } else {
    // Fallback: Show share buttons
    const shareCard = document.querySelector('.share-card');
    if (shareCard) {
      shareCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }
}

/**
 * Responsive Sidebar Sticky Behavior
 */
function updateSidebarPosition() {
  const sidebar = document.querySelector('.detail-sidebar');
  const container = document.querySelector('.opportunity-detail-container');

  if (!sidebar || !container) return;

  if (window.innerWidth <= 1024) {
    sidebar.style.position = 'static';
  } else {
    sidebar.style.position = 'relative';
  }
}

window.addEventListener('resize', updateSidebarPosition);
updateSidebarPosition();
