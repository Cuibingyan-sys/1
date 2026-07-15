// ============================================
//   健康计算器 - 全局脚本
//   Health Tools - Global Scripts
// ============================================

// Mobile menu
document.addEventListener('DOMContentLoaded', function() {
  const menuBtn = document.querySelector('.mobile-menu-btn');
  const navLinks = document.querySelector('.nav-links');

  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', function() {
      navLinks.classList.toggle('show');
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
      if (!menuBtn.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('show');
      }
    });
  }

  // Unit toggle buttons
  document.querySelectorAll('.unit-toggle').forEach(function(toggle) {
    toggle.querySelectorAll('button').forEach(function(btn) {
      btn.addEventListener('click', function() {
        toggle.querySelectorAll('button').forEach(function(b) { b.classList.remove('active'); });
        this.classList.add('active');
        // Trigger unit change event
        const event = new CustomEvent('unitChange', {
          detail: { unit: this.dataset.unit }
        });
        toggle.dispatchEvent(event);
      });
    });
  });

  // Highlight current page in nav
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(function(link) {
    if (link.getAttribute('href') === currentPath ||
        (currentPath.includes(link.getAttribute('href')) && link.getAttribute('href') !== '/')) {
      link.classList.add('active');
    }
  });
});

// Track tool usage (for analytics - replace with your analytics code)
function trackToolUsage(toolName) {
  if (typeof gtag !== 'undefined') {
    gtag('event', 'tool_usage', {
      'event_category': 'tools',
      'event_label': toolName
    });
  }
  console.log('Tool used:', toolName);
}

// Track ad click
function trackAdClick(adName) {
  if (typeof gtag !== 'undefined') {
    gtag('event', 'ad_click', {
      'event_category': 'monetization',
      'event_label': adName
    });
  }
}