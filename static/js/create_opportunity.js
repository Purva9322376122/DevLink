/**
 * Create Opportunity Form - JavaScript Enhancement
 * 
 * Features:
 * - Real-time form validation with visual feedback
 * - Character count display for title and description
 * - Submit button state management
 * - Smooth scroll to first error on validation failure
 * - Entrance animations
 * - Keyboard accessibility enhancements
 */

(function () {
  'use strict';

  // Configuration
  const CONFIG = {
    TITLE_MIN: 20,
    DESCRIPTION_MIN: 20,
    TRANSITION_DURATION: 300,
    ANIMATION_DURATION: 0.3,
  };

  // State
  let isFormValid = false;
  let isSubmitting = false;

  /**
   * Initialize the form on page load
   */
  function initializeForm() {
    const form = document.querySelector('.create-opportunity-form');
    if (!form) return;

    // Get form elements
    const titleInput = document.getElementById('id_title');
    const descriptionInput = document.getElementById('id_description');
    const submitBtn = document.querySelector('[type="submit"]');

    // Initialize validation
    if (titleInput) {
      titleInput.addEventListener('input', debounce(() => validateTitle(titleInput), 150));
      titleInput.addEventListener('blur', () => validateTitle(titleInput));
    }

    if (descriptionInput) {
      descriptionInput.addEventListener('input', debounce(() => validateDescription(descriptionInput), 150));
      descriptionInput.addEventListener('blur', () => validateDescription(descriptionInput));
    }

    // Form submission
    form.addEventListener('submit', (e) => handleFormSubmit(e, form));

    // Initial validation state
    validateForm();
  }

  /**
   * Debounce utility function
   */
  function debounce(fn, delay) {
    let timeoutId;
    return function (...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    };
  }

  /**
   * Validate title field
   */
  function validateTitle(input) {
    const value = input.value.trim();
    const isValid = value.length >= CONFIG.TITLE_MIN;
    const fieldContainer = input.closest('.form-field');

    if (fieldContainer) {
      if (!isValid && value.length > 0) {
        fieldContainer.classList.add('field-invalid');
        showValidationMessage(
          fieldContainer,
          `Title must be at least ${CONFIG.TITLE_MIN} characters (${value.length}/${CONFIG.TITLE_MIN})`
        );
      } else {
        fieldContainer.classList.remove('field-invalid');
        clearValidationMessage(fieldContainer);
      }
    }

    // Update character count
    updateCharacterCount(input, CONFIG.TITLE_MIN);

    // Update overall form validity
    validateForm();

    return isValid;
  }

  /**
   * Validate description field
   */
  function validateDescription(input) {
    const value = input.value.trim();
    const isValid = value.length >= CONFIG.DESCRIPTION_MIN;
    const fieldContainer = input.closest('.form-field');

    if (fieldContainer) {
      if (!isValid && value.length > 0) {
        fieldContainer.classList.add('field-invalid');
        showValidationMessage(
          fieldContainer,
          `Description must be at least ${CONFIG.DESCRIPTION_MIN} characters (${value.length}/${CONFIG.DESCRIPTION_MIN})`
        );
      } else {
        fieldContainer.classList.remove('field-invalid');
        clearValidationMessage(fieldContainer);
      }
    }

    // Update character count
    updateCharacterCount(input, CONFIG.DESCRIPTION_MIN);

    // Update overall form validity
    validateForm();

    return isValid;
  }

  /**
   * Update character count display
   */
  function updateCharacterCount(input, minLength) {
    const value = input.value.trim();
    const fieldContainer = input.closest('.form-field');

    if (!fieldContainer) return;

    let countDisplay = fieldContainer.querySelector('.char-count');

    if (!countDisplay) {
      countDisplay = document.createElement('div');
      countDisplay.className = 'char-count';
      countDisplay.style.cssText = `
        font-size: 12px;
        color: var(--muted);
        margin-top: 4px;
        text-align: right;
      `;
      input.parentElement.appendChild(countDisplay);
    }

    countDisplay.textContent = `${value.length}/${minLength}`;

    // Color based on progress
    if (value.length < minLength) {
      countDisplay.style.color = 'var(--muted)';
    } else {
      countDisplay.style.color = '#10b981';
    }
  }

  /**
   * Show validation message
   */
  function showValidationMessage(fieldContainer, message) {
    let errorContainer = fieldContainer.querySelector('.field-error-msg');

    if (!errorContainer) {
      errorContainer = document.createElement('div');
      errorContainer.className = 'field-error-msg';
      errorContainer.style.cssText = `
        font-size: 12px;
        color: #dc2626;
        margin-top: 4px;
        animation: slideDown 0.18s ease forwards;
      `;
      fieldContainer.appendChild(errorContainer);

      // Add CSS animation if not exists
      if (!document.querySelector('style[data-error-animation]')) {
        const style = document.createElement('style');
        style.setAttribute('data-error-animation', '');
        style.textContent = `
          @keyframes slideDown {
            from {
              opacity: 0;
              transform: translateY(-4px);
            }
            to {
              opacity: 1;
              transform: none;
            }
          }
        `;
        document.head.appendChild(style);
      }
    }

    errorContainer.textContent = message;
  }

  /**
   * Clear validation message
   */
  function clearValidationMessage(fieldContainer) {
    const errorContainer = fieldContainer.querySelector('.field-error-msg');
    if (errorContainer) {
      errorContainer.remove();
    }
  }

  /**
   * Validate entire form
   */
  function validateForm() {
    const titleInput = document.getElementById('id_title');
    const descriptionInput = document.getElementById('id_description');

    const titleValid = titleInput ? titleInput.value.trim().length >= CONFIG.TITLE_MIN : true;
    const descriptionValid = descriptionInput ? descriptionInput.value.trim().length >= CONFIG.DESCRIPTION_MIN : true;

    isFormValid = titleValid && descriptionValid;

    // Update submit button state
    updateSubmitButtonState();
  }

  /**
   * Update submit button state based on form validity
   */
  function updateSubmitButtonState() {
    const submitBtn = document.querySelector('[type="submit"]');
    if (!submitBtn) return;

    if (isFormValid && !isSubmitting) {
      submitBtn.disabled = false;
      submitBtn.style.opacity = '1';
      submitBtn.style.cursor = 'pointer';
    } else {
      submitBtn.disabled = true;
      submitBtn.style.opacity = '0.6';
      submitBtn.style.cursor = 'not-allowed';
    }
  }

  /**
   * Handle form submission
   */
  function handleFormSubmit(e, form) {
    e.preventDefault();

    // Validate form before submission
    if (!isFormValid) {
      // Scroll to first error
      scrollToFirstError();
      return;
    }

    // Set loading state
    isSubmitting = true;
    updateSubmitButtonState();

    const submitBtn = document.querySelector('[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Creating...';

    // Simulate minimum UI feedback time (0.5s)
    setTimeout(() => {
      // Allow form to submit
      form.submit();
    }, 500);
  }

  /**
   * Scroll to first error field
   */
  function scrollToFirstError() {
    const firstErrorField = document.querySelector('.form-field.field-invalid');
    if (firstErrorField) {
      firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Focus the input after scroll
      const input = firstErrorField.querySelector('input, textarea');
      if (input) {
        setTimeout(() => input.focus(), CONFIG.TRANSITION_DURATION);
      }
    }
  }

  /**
   * Initialize entrance animations
   */
  function initializeAnimations() {
    const formCard = document.querySelector('.form-card');
    if (formCard) {
      // Animation is handled by CSS - just ensure visibility
      formCard.style.opacity = '1';
    }

    // Animate form fields with stagger
    const formFields = document.querySelectorAll('.form-field');
    formFields.forEach((field, index) => {
      field.style.animationDelay = `${index * 0.05}s`;
      field.style.animation = 'fadeInUp 0.3s ease forwards';
    });

    // Add animation keyframe
    if (!document.querySelector('style[data-field-animation]')) {
      const style = document.createElement('style');
      style.setAttribute('data-field-animation', '');
      style.textContent = `
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: none;
          }
        }
      `;
      document.head.appendChild(style);
    }
  }

  /**
   * Initialize keyboard shortcuts
   */
  function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      const form = document.querySelector('.create-opportunity-form');
      if (!form) return;

      // Ctrl/Cmd + Enter to submit
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const submitBtn = document.querySelector('[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
          submitBtn.click();
        }
      }

      // Escape to cancel
      if (e.key === 'Escape') {
        const cancelBtn = document.querySelector('[href*="opportunities"]');
        if (cancelBtn) {
          const goBack = confirm('Discard changes and go back?');
          if (goBack) {
            window.history.back();
          }
        }
      }
    });
  }

  /**
   * Initialize theme detection
   */
  function initializeTheme() {
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      // Check if user has set a preference
      const savedTheme = localStorage.getItem('theme-preference');
      if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
      }
    }

    // Listen for changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
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
      .form-field input:focus-visible,
      .form-field textarea:focus-visible {
        outline: 3px solid rgba(37, 99, 235, 0.18);
        outline-offset: 2px;
      }

      button:focus-visible {
        outline: 3px solid rgba(37, 99, 235, 0.18);
        outline-offset: 2px;
      }

      a:focus-visible {
        outline: 3px solid rgba(37, 99, 235, 0.18);
        outline-offset: 2px;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Entry point
   */
  document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
    initializeAnimations();
    initializeKeyboardShortcuts();
    initializeTheme();
    initializeFocusIndicators();
  });

  // Handle page visibility - reset form state if user returns to page
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      isSubmitting = false;
      updateSubmitButtonState();
    }
  });
})();
