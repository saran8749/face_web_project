/* ============================================================
   FACE WEB PROJECT — Scroll Animation Engine
   Uses IntersectionObserver for performant scroll-triggered reveals.
   ============================================================ */

(function () {
  'use strict';

  // ── Scroll Animation Observer ──
  function initScrollAnimations() {
    const elements = document.querySelectorAll('[data-animate]');
    if (!elements.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const delay = parseInt(el.getAttribute('data-delay') || '0', 10);
            setTimeout(() => {
              el.classList.add('animated');
            }, delay);
            observer.unobserve(el);
          }
        });
      },
      {
        threshold: 0.08,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    elements.forEach((el) => observer.observe(el));
  }

  // ── Count-Up Animation for Stat Cards ──
  function initCountUp() {
    const counters = document.querySelectorAll('.count-up');
    if (!counters.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const target = parseInt(el.getAttribute('data-count') || el.textContent, 10);
            if (isNaN(target)) return;
            animateNumber(el, 0, target, 1200);
            observer.unobserve(el);
          }
        });
      },
      { threshold: 0.5 }
    );

    counters.forEach((el) => observer.observe(el));
  }

  function animateNumber(el, start, end, duration) {
    const startTime = performance.now();
    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutExpo
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const current = Math.round(start + (end - start) * eased);
      el.textContent = current;
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  // ── Button Ripple Effect ──
  function initRipple() {
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn, .capture-btn');
      if (!btn) return;

      const ripple = document.createElement('span');
      ripple.classList.add('ripple');
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = e.clientX - rect.left - size / 2 + 'px';
      ripple.style.top = e.clientY - rect.top - size / 2 + 'px';
      btn.appendChild(ripple);
      ripple.addEventListener('animationend', () => ripple.remove());
    });
  }

  // ── Flash Message Auto-Dismiss ──
  function initFlashDismiss() {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach((flash) => {
      setTimeout(() => {
        flash.style.transition = 'opacity 0.5s ease, transform 0.5s ease, max-height 0.5s ease';
        flash.style.opacity = '0';
        flash.style.transform = 'translateY(-10px)';
        flash.style.maxHeight = '0';
        flash.style.padding = '0';
        flash.style.margin = '0';
        flash.style.overflow = 'hidden';
        setTimeout(() => flash.remove(), 500);
      }, 5000);
    });
  }

  // ── Photo Upload Preview ──
  function initUploadPreview() {
    const zone = document.querySelector('.upload-zone');
    const input = zone ? zone.querySelector('input[type="file"]') : null;
    const preview = document.querySelector('.upload-preview');
    if (!zone || !input || !preview) return;

    // Dragover styling
    ['dragenter', 'dragover'].forEach((event) => {
      zone.addEventListener(event, (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
      });
    });
    ['dragleave', 'drop'].forEach((event) => {
      zone.addEventListener(event, () => {
        zone.classList.remove('dragover');
      });
    });

    // File change preview
    input.addEventListener('change', () => {
      const file = input.files[0];
      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          preview.src = e.target.result;
          preview.classList.add('visible');
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // ── Particles Generator (Login Page) ──
  function initParticles() {
    const container = document.querySelector('.particles');
    if (!container) return;

    for (let i = 0; i < 30; i++) {
      const span = document.createElement('span');
      span.style.left = Math.random() * 100 + '%';
      span.style.width = span.style.height = Math.random() * 4 + 2 + 'px';
      span.style.animationDuration = Math.random() * 15 + 10 + 's';
      span.style.animationDelay = Math.random() * 10 + 's';
      span.style.opacity = Math.random() * 0.5 + 0.1;
      container.appendChild(span);
    }
  }

  // ── Initialize Everything on DOMContentLoaded ──
  document.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
    initCountUp();
    initRipple();
    initFlashDismiss();
    initUploadPreview();
    initParticles();
  });
})();
