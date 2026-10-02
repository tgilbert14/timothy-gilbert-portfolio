(function () {
  'use strict';

  var consoles = Array.prototype.slice.call(document.querySelectorAll('[data-demolition-console]'));
  var motion = window.matchMedia('(prefers-reduced-motion: reduce)');

  consoles.forEach(function (console) {
    var test = console.querySelector('[data-demolition-test]');
    var launch = console.querySelector('[data-demolition-launch]');
    var timer = 0;

    var clear = function () {
      window.clearTimeout(timer);
      timer = 0;
      console.classList.remove('is-hit');
    };
    var hit = function () {
      clear();
      // Restart one restrained, reversible hit. The page and its links stay intact.
      void console.offsetWidth;
      console.classList.add('is-hit');
      timer = window.setTimeout(clear, 500);
    };

    if (test) {
      test.addEventListener('click', hit);
      test.disabled = false;
      test.setAttribute('aria-label', 'Test a shot on the miniature target');
      var caption = test.querySelector('[data-demolition-test-label]');
      if (caption) caption.textContent = 'Test shot';
    }
    if (launch) {
      launch.addEventListener('pointerdown', function (event) {
        if (event.button === 0) hit();
      });
      launch.addEventListener('pointercancel', clear);
      launch.addEventListener('click', function (event) {
        // Native Enter activation earns the same feedback. Never intercept navigation.
        if (event.detail === 0) hit();
      });
    }

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) clear();
    });
    window.addEventListener('pagehide', clear);
    if (motion.addEventListener) motion.addEventListener('change', clear);
    else if (motion.addListener) motion.addListener(clear);
  });
}());
