/* Header menu and home-page showcase. No dependencies. */

  (function () {
    var header = document.querySelector('.site-header');
    if (!header) return;
    var toggle = header.querySelector('.menu-toggle');
    var navEl = header.querySelector('.site-nav');
    var groups = header.querySelectorAll('.nav-group__btn');
    function closeGroups(except) {
      groups.forEach(function (b) { if (b !== except) b.setAttribute('aria-expanded', 'false'); });
    }
    groups.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var open = btn.getAttribute('aria-expanded') === 'true';
        closeGroups(btn);
        btn.setAttribute('aria-expanded', String(!open));
      });
    });
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      navEl.classList.toggle('is-open', !open);
      if (open) closeGroups();
    });
    document.addEventListener('click', function (e) { if (!header.contains(e.target)) closeGroups(); });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      closeGroups();
      if (toggle.getAttribute('aria-expanded') === 'true') { toggle.click(); toggle.focus(); }
    });
    navEl.addEventListener('click', function (e) {
      if (e.target.closest('a') && toggle.getAttribute('aria-expanded') === 'true') toggle.click();
    });
  })();


  (function () {
    var root = document.querySelector('.showcase');
    if (!root) return;
    var panels = root.querySelectorAll('[data-panel]');
    var tabs = root.querySelectorAll('[data-tab]');
    var current = root.querySelector('[data-current]');
    var index = 0;
    function show(i) {
      index = (i + panels.length) % panels.length;
      panels.forEach(function (p, n) { p.classList.toggle('is-active', n === index); });
      tabs.forEach(function (t, n) { t.setAttribute('aria-pressed', String(n === index)); });
      current.textContent = String(index + 1).padStart(2, '0');
    }
    root.classList.add('is-enhanced');
    root.querySelector('.showcase__controls').hidden = false;
    root.querySelector('.showcase__tabs').hidden = false;
    tabs.forEach(function (t, n) { t.addEventListener('click', function () { show(n); }); });
    root.querySelector('[data-prev]').addEventListener('click', function () { show(index - 1); });
    root.querySelector('[data-next]').addEventListener('click', function () { show(index + 1); });
    show(0);
  })();
