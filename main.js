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
// Back to Top
(function() {
  var btn = document.getElementById('backToTop');
  if (!btn) return;
  window.addEventListener('scroll', function() {
    if (window.scrollY > 400) {
      btn.classList.add('show');
    } else {
      btn.classList.remove('show');
    }
  });
  btn.addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

// ============================================
//   Adsterra Direct Link - 底部浮层广告
// ============================================
(function() {
  var adUrl = 'https://www.effectivecpmnetwork.com/f0qb315fz?key=10d1d7465a1f8bb980cadc99b4a64ed7';
  var bar = document.createElement('div');
  bar.id = 'adsterra-bar';
  bar.style.cssText = 'position:fixed;bottom:0;left:0;width:100%;z-index:9997;background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:10px 16px;display:none;align-items:center;justify-content:center;gap:12px;font-size:0.9rem;font-family:inherit;box-shadow:0 -2px 12px rgba(0,0,0,0.2);';
  bar.innerHTML = '<span style="font-weight:600;">🔥 发现更多精彩内容</span>' +
    '<a href="' + adUrl + '" target="_blank" rel="nofollow" style="background:#ff6b35;color:#fff;padding:8px 20px;border-radius:20px;font-weight:700;text-decoration:none;white-space:nowrap;font-size:0.85rem;transition:transform 0.2s;" onmouseover="this.style.transform=\'scale(1.05)\'" onmouseout="this.style.transform=\'scale(1)\'">立即查看</a>' +
    '<button onclick="document.getElementById(\'adsterra-bar\').style.display=\'none\';localStorage.setItem(\'ab_closed\',Date.now());" style="background:none;border:none;color:rgba(255,255,255,0.5);font-size:20px;cursor:pointer;padding:0 4px;line-height:1;" title="关闭">&times;</button>';
  document.body.appendChild(bar);

  // 5秒后显示，24小时内关闭过不重复
  setTimeout(function() {
    var lastClosed = localStorage.getItem('ab_closed');
    if (!lastClosed || (Date.now() - parseInt(lastClosed)) > 86400000) {
      bar.style.display = 'flex';
    }
  }, 5000);
})();

// ============================================
//   浮动分享按钮 - Floating Share Button
// ============================================
(function() {
  var toggle = document.getElementById('shareToggle');
  var menu = document.getElementById('shareMenu');
  if (toggle && menu) {
    toggle.addEventListener('click', function(e) {
      e.stopPropagation();
      menu.classList.toggle('show');
    });
    document.addEventListener('click', function(e) {
      if (!toggle.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.remove('show');
      }
    });
  }
})();

window.copyShareLink = function() {
  var url = 'https://cuibingyan-sys.github.io/1';
  navigator.clipboard.writeText(url).then(function() {
    alert('链接已复制！快去分享给朋友吧 🎉');
  });
  try { gtag('event', 'share_copy'); } catch(e) {}
  try { _hmt.push(['_trackEvent', 'share', 'copy']); } catch(e) {}
};

// Cookie Consent
function acceptCookies() {
  var banner = document.getElementById('cookieBanner');
  if (banner) banner.classList.remove('show');
  localStorage.setItem('cookies_accepted', 'true');
  try { gtag('event', 'cookies_accepted'); } catch(e) {}
}

(function() {
  var banner = document.getElementById('cookieBanner');
  if (!banner) return;
  if (localStorage.getItem('cookies_accepted') === 'true') {
    banner.style.display = 'none';
  } else {
    setTimeout(function() { banner.classList.add('show'); }, 1000);
  }
})();

// ============================================
//   邮件订阅弹窗 - Newsletter Popup
// ============================================
(function() {
  var overlay = document.createElement('div');
  overlay.id = 'newsletter-overlay';
  overlay.className = 'newsletter-overlay';
  overlay.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:9999;justify-content:center;align-items:center;';
  overlay.innerHTML = '<div class="newsletter-popup" style="background:#fff;border-radius:16px;padding:32px;max-width:420px;width:90%;position:relative;box-shadow:0 20px 60px rgba(0,0,0,0.3);text-align:center;">' +
    '<button onclick="closeNewsletter()" style="position:absolute;top:12px;right:16px;background:none;border:none;font-size:24px;cursor:pointer;color:#9ca3af;">&times;</button>' +
    '<div style="font-size:48px;margin-bottom:12px;">📬</div>' +
    '<h3 style="margin:0 0 8px;font-size:1.3rem;color:#1f2937;">免费获取健康减脂指南</h3>' +
    '<p style="color:#6b7280;font-size:0.9rem;margin:0 0 20px;line-height:1.5;">每周推送科学减脂技巧、食谱和工具更新，<br>帮你轻松瘦下来！</p>' +
    '<form id="newsletter-form" onsubmit="return submitNewsletter(event)" style="display:flex;flex-direction:column;gap:10px;">' +
    '<input type="email" id="newsletter-email" placeholder="输入你的邮箱地址" required style="padding:12px 16px;border:2px solid #e5e7eb;border-radius:8px;font-size:1rem;outline:none;">' +
    '<button type="submit" style="padding:12px;background:#059669;color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;">免费订阅</button></form>' +
    '<p style="font-size:0.72rem;color:#9ca3af;margin:12px 0 0;">不打扰，每周一封，随时可退订</p>' +
    '<div id="newsletter-success" style="display:none;padding:24px 0;"><div style="font-size:48px;">✅</div><h4 style="color:#059669;margin:8px 0;">订阅成功！</h4><p style="color:#6b7280;font-size:0.9rem;">请查收确认邮件，感谢订阅！</p></div></div>';
  document.body.appendChild(overlay);

  window.showNewsletter = function() {
    document.getElementById('newsletter-overlay').style.display = 'flex';
    document.body.style.overflow = 'hidden';
    try { gtag('event', 'newsletter_show'); } catch(e) {}
  };
  window.closeNewsletter = function() {
    document.getElementById('newsletter-overlay').style.display = 'none';
    document.body.style.overflow = '';
    localStorage.setItem('nl_closed', Date.now());
  };
  window.submitNewsletter = function(e) {
    e.preventDefault();
    var email = document.getElementById('newsletter-email').value;
    try { gtag('event', 'newsletter_submit', { event_label: email }); } catch(e) {}
    try { _hmt.push(['_trackEvent', 'newsletter', 'submit', email]); } catch(e) {}
    document.getElementById('newsletter-form').style.display = 'none';
    document.getElementById('newsletter-success').style.display = 'block';
    setTimeout(function() { closeNewsletter(); }, 3000);
    return false;
  };

  // 20秒后自动弹出，24小时内不重复
  setTimeout(function() {
    var lastClosed = localStorage.getItem('nl_closed');
    if (!lastClosed || (Date.now() - parseInt(lastClosed)) > 86400000) {
      showNewsletter();
    }
  }, 20000);
})();

// ============================================
//   浮动广告条 - Floating Ad Banner
// ============================================
(function() {
  var floater = document.createElement('div');
  floater.id = 'floating-ad';
  floater.style.cssText = 'position:fixed;bottom:0;left:0;width:100%;background:linear-gradient(135deg,#059669,#047857);color:#fff;z-index:9998;padding:12px 16px;display:flex;align-items:center;justify-content:center;gap:12px;font-size:0.9rem;box-shadow:0 -4px 20px rgba(0,0,0,0.15);transform:translateY(100%);transition:transform 0.3s ease;';
  floater.innerHTML = '<span style="font-weight:600;">🔥 夏季减肥必备好物，京东正品限时优惠！</span>' +
    '<a href="shop.html" style="background:#fff;color:#059669;padding:6px 16px;border-radius:20px;font-weight:600;text-decoration:none;white-space:nowrap;font-size:0.85rem;">立即查看</a>' +
    '<button onclick="closeFloatingAd()" style="background:none;border:none;color:rgba(255,255,255,0.7);font-size:18px;cursor:pointer;padding:0 4px;" title="关闭">&times;</button>';
  document.body.appendChild(floater);

  window.closeFloatingAd = function() {
    document.getElementById('floating-ad').style.transform = 'translateY(100%)';
    localStorage.setItem('fa_closed', Date.now());
  };

  // 5秒后显示，24小时内不重复
  setTimeout(function() {
    var lastClosed = localStorage.getItem('fa_closed');
    if (!lastClosed || (Date.now() - parseInt(lastClosed)) > 86400000) {
      document.getElementById('floating-ad').style.transform = 'translateY(0)';
      try { gtag('event', 'floating_ad_show'); } catch(e) {}
    }
  }, 5000);
})();
