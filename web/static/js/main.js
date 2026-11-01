/**
 * BookEase Web Portal — Main JavaScript
 * Handles: navigation, sticky CTA, toast, loading overlay, PWA, global utilities.
 */

/* ── Navigation ───────────────────────────────────────────────────────────── */
(function initNav() {
  const toggle = document.getElementById('navToggle');
  const menu   = document.getElementById('navMenu');
  if (!toggle || !menu) return;

  function openMenu() {
    menu.classList.add('open');
    menu.setAttribute('aria-hidden', 'false');
    toggle.setAttribute('aria-expanded', 'true');
    toggle.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    menu.classList.remove('open');
    menu.setAttribute('aria-hidden', 'true');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.classList.remove('open');
    document.body.style.overflow = '';
  }

  toggle.addEventListener('click', () => {
    const isOpen = menu.classList.contains('open');
    isOpen ? closeMenu() : openMenu();
  });

  // Close on nav-link click (mobile)
  menu.querySelectorAll('.nav-link, .nav-cta').forEach(link => {
    link.addEventListener('click', closeMenu);
  });

  // Close on outside click
  document.addEventListener('click', e => {
    if (menu.classList.contains('open') && !menu.contains(e.target) && !toggle.contains(e.target)) {
      closeMenu();
    }
  });

  // Close on Escape
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu.classList.contains('open')) closeMenu();
  });

  // Close menu on resize to desktop
  window.addEventListener('resize', () => {
    if (window.innerWidth >= 768) closeMenu();
  });
}());


/* ── Sticky Book Button ───────────────────────────────────────────────────── */
(function initStickyBook() {
  const sticky = document.getElementById('stickyBook');
  if (!sticky) return;

  let lastY = window.scrollY;
  let ticking = false;

  function update() {
    const scrollY = window.scrollY;
    const docH    = document.documentElement.scrollHeight;
    const winH    = window.innerHeight;
    // Hide near the very bottom (footer area)
    const nearBottom = scrollY + winH > docH - 200;
    // Show after scrolling 300px down
    const pastHero = scrollY > 300;

    sticky.style.display = (pastHero && !nearBottom) ? 'block' : 'none';
    lastY = scrollY;
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(update);
      ticking = true;
    }
  }, { passive: true });

  // Initial check
  update();
}());


/* ── Toast Notification ───────────────────────────────────────────────────── */
let _toastTimer = null;

/**
 * Show a toast notification.
 * @param {string} message
 * @param {'success'|'error'|'info'} type
 * @param {number} duration ms
 */
function showToast(message, type = 'info', duration = 3500) {
  const toast    = document.getElementById('toast');
  const iconEl   = document.getElementById('toast-icon');
  const msgEl    = document.getElementById('toast-message');
  if (!toast) return;

  const icons = { success: '✓', error: '✕', info: 'ℹ' };

  toast.className = `toast ${type}`;
  if (iconEl) iconEl.textContent = icons[type] || icons.info;
  if (msgEl)  msgEl.textContent  = message;

  // Animate in
  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  // Clear previous timer
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, duration);
}
window.showToast = showToast;


/* ── Loading Overlay ──────────────────────────────────────────────────────── */
function showLoading() {
  const el = document.getElementById('loading-overlay');
  if (el) el.classList.add('active');
}
function hideLoading() {
  const el = document.getElementById('loading-overlay');
  if (el) el.classList.remove('active');
}
window.showLoading = showLoading;
window.hideLoading = hideLoading;


/* ── PWA Service Worker ───────────────────────────────────────────────────── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js').then(reg => {
      console.log('[BookEase] Service Worker registered:', reg.scope);
    }).catch(err => {
      console.warn('[BookEase] Service Worker registration failed:', err);
    });
  });
}


/* ── Smooth Anchor Scroll ─────────────────────────────────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', e => {
    const target = document.querySelector(anchor.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});


/* ── Lazy-Load Images ─────────────────────────────────────────────────────── */
if ('IntersectionObserver' in window) {
  const imgs = document.querySelectorAll('img[data-src]');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        observer.unobserve(img);
      }
    });
  });
  imgs.forEach(img => observer.observe(img));
}


/* ── Animate sections on scroll ──────────────────────────────────────────── */
(function initFadeIn() {
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const sections = document.querySelectorAll('.section, .page-hero');
  if (!sections.length) return;

  sections.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  });

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  sections.forEach(el => observer.observe(el));
}());

