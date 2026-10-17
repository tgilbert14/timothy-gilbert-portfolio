(function () {
  'use strict';

  /* The demo hub field desk: three workspace plates, one working miniature queue,
     and a tortoise that only moves when something actually gets done. */
  var desk = document.querySelector('[data-field-desk]');
  if (!desk) return;

  var plates = Array.prototype.slice.call(desk.querySelectorAll('[data-plate]'));
  var tabs = Array.prototype.slice.call(desk.querySelectorAll('[data-desk-tab]'));
  var link = desk.querySelector('[data-desk-link]');
  var linkName = desk.querySelector('[data-desk-link-name]');
  var tortoise = desk.querySelector('[data-desk-tortoise]');
  var transect = tortoise ? tortoise.parentNode : null;
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var keys = plates.map(function (plate) { return plate.getAttribute('data-plate'); });
  var active = 0;
  var touched = false;
  var cycleTimer = 0;
  var walkTimer = 0;

  if (!plates.length) return;

  var queueItems = function (plate) {
    return Array.prototype.slice.call(plate.querySelectorAll('[data-queue-item]'));
  };

  var updateProgress = function () {
    var plate = plates[active];
    var items = queueItems(plate);
    var done = items.filter(function (item) { return item.getAttribute('aria-pressed') === 'true'; }).length;
    var open = items.length - done;
    var count = plate.querySelector('[data-queue-count]');
    var reset = plate.querySelector('[data-queue-reset]');
    var headline = plate.querySelector('[data-plate-headline]');

    if (count) count.textContent = open === 0 ? 'All clear' : open + ' open';
    if (reset) reset.hidden = done === 0;
    if (headline) {
      if (!headline.getAttribute('data-original')) headline.setAttribute('data-original', headline.textContent);
      headline.textContent = open === 0
        ? (plate.getAttribute('data-plate-done') || headline.getAttribute('data-original'))
        : headline.getAttribute('data-original');
    }
    plate.classList.toggle('is-complete', open === 0);
    if (transect) {
      var pct = items.length ? (done / items.length) * 100 : 0;
      transect.style.setProperty('--tortoise-x', pct.toFixed(1) + '%');
    }
  };

  var walk = function () {
    if (reducedMotion || !transect) return;
    transect.classList.add('is-walking');
    window.clearTimeout(walkTimer);
    walkTimer = window.setTimeout(function () { transect.classList.remove('is-walking'); }, 1500);
  };

  var layout = function () {
    plates.forEach(function (plate, index) {
      var rel = (index - active + plates.length) % plates.length;
      var offstage = rel !== 0;
      plate.classList.toggle('is-active', rel === 0);
      plate.classList.toggle('is-next', rel === 1);
      plate.classList.toggle('is-prev', rel === 2);
      plate.setAttribute('aria-hidden', String(offstage));
      if (offstage) plate.setAttribute('inert', '');
      else plate.removeAttribute('inert');
    });
    tabs.forEach(function (tab) {
      var on = tab.getAttribute('data-desk-tab') === keys[active];
      tab.classList.toggle('is-active', on);
      tab.setAttribute('aria-pressed', String(on));
    });
    if (link) {
      var href = link.getAttribute('data-href-' + keys[active]);
      if (href) link.setAttribute('href', href);
      if (linkName) {
        var tab = tabs.filter(function (t) { return t.getAttribute('data-desk-tab') === keys[active]; })[0];
        linkName.textContent = tab ? tab.textContent.trim() : keys[active];
      }
    }
    updateProgress();
  };

  var stopCycle = function () {
    if (cycleTimer) { window.clearInterval(cycleTimer); cycleTimer = 0; }
  };

  var startCycle = function () {
    if (reducedMotion || touched || cycleTimer) return;
    cycleTimer = window.setInterval(function () {
      active = (active + 1) % plates.length;
      layout();
      walk();
    }, 4600);
  };

  var setActive = function (index) {
    touched = true;
    stopCycle();
    var next = (index + plates.length) % plates.length;
    var changed = next !== active;
    active = next;
    layout();
    if (changed) walk();
  };

  desk.addEventListener('click', function (event) {
    var item = event.target.closest('[data-queue-item]');
    if (item) {
      touched = true;
      stopCycle();
      item.setAttribute('aria-pressed', item.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      updateProgress();
      walk();
      return;
    }
    var reset = event.target.closest('[data-queue-reset]');
    if (reset) {
      var plate = reset.closest('[data-plate]');
      queueItems(plate).forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      updateProgress();
      walk();
      return;
    }
    var tab = event.target.closest('[data-desk-tab]');
    if (tab) setActive(keys.indexOf(tab.getAttribute('data-desk-tab')));
  });

  /* Keyboard users and anyone hovering get a still desk; the auto-tour is only for passers-by. */
  desk.addEventListener('focusin', function () { touched = true; stopCycle(); });
  desk.addEventListener('pointerenter', stopCycle);
  desk.addEventListener('pointerleave', startCycle);

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) startCycle();
        else stopCycle();
      });
    }, { threshold: 0.35 }).observe(desk);
  }

  layout();
}());
