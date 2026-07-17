(function () {
  'use strict';

  var hero = document.querySelector('[data-wild-hero]');
  var cards = Array.prototype.slice.call(document.querySelectorAll('[data-tilt-card]'));
  var reactiveCards = Array.prototype.slice.call(document.querySelectorAll('[data-reactive-card]'));
  var portrait = document.querySelector('[data-portrait-morph]');
  var portraitToggle = portrait ? portrait.querySelector('[data-portrait-toggle]') : null;
  var proofCounters = Array.prototype.slice.call(document.querySelectorAll('[data-count-to]'));
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = window.matchMedia('(pointer: fine)').matches;

  /* A thin signal line keeps the long homepage feeling connected. */
  var updateProgress = function () {
    var max = document.documentElement.scrollHeight - window.innerHeight;
    var progress = max > 0 ? Math.min(1, Math.max(0, window.pageYOffset / max)) : 0;
    document.body.style.setProperty('--portfolio-progress', progress.toFixed(4));
  };
  var progressTicking = false;
  window.addEventListener('scroll', function () {
    if (progressTicking) return;
    progressTicking = true;
    window.requestAnimationFrame(function () {
      updateProgress();
      progressTicking = false;
    });
  }, { passive: true });
  updateProgress();

  /* Real Tim first; dog Tim is keyboard- and touch-operable too. */
  if (portrait && portraitToggle) {
    var portraitToggleText = portraitToggle.querySelector('span');
    var revertTimer = 0;
    var playReverseGate = function () {
      portrait.classList.remove('is-reverting');
      void portrait.offsetWidth;
      portrait.classList.add('is-reverting');
      window.clearTimeout(revertTimer);
      revertTimer = window.setTimeout(function () {
        portrait.classList.remove('is-reverting');
      }, 1100);
    };

    portraitToggle.addEventListener('click', function () {
      var isDog = portrait.classList.toggle('is-dog');
      portrait.classList.toggle('is-human-lock', !isDog);
      portraitToggle.setAttribute('aria-pressed', String(isDog));
      if (portraitToggleText) portraitToggleText.textContent = isDog ? 'ORIGINAL HUMAN' : 'ALT SPECIMEN';
      if (!isDog) playReverseGate();
    });

    if (finePointer && !reducedMotion) {
      portrait.addEventListener('pointerenter', function () {
        portrait.classList.remove('is-reverting');
        window.clearTimeout(revertTimer);
      });
      portrait.addEventListener('pointerleave', function () {
        if (portrait.classList.contains('is-human-lock')) {
          portrait.classList.remove('is-human-lock');
          return;
        }
        if (!portrait.classList.contains('is-dog')) playReverseGate();
      });
    }
  }

  /* Count the proof only when it reaches the page. */
  var animateCounter = function (counter) {
    var target = parseInt(counter.getAttribute('data-count-to'), 10) || 0;
    var suffix = counter.getAttribute('data-count-suffix') || '';
    var duration = 1050 + Math.min(target * 2, 500);
    var startedAt = 0;
    counter.classList.add('is-counted');

    var step = function (time) {
      if (!startedAt) startedAt = time;
      var progress = Math.min(1, (time - startedAt) / duration);
      var eased = 1 - Math.pow(1 - progress, 3);
      counter.textContent = Math.round(target * eased) + suffix;
      if (progress < 1) window.requestAnimationFrame(step);
    };
    window.requestAnimationFrame(step);
  };

  if (proofCounters.length && !reducedMotion && 'IntersectionObserver' in window) {
    var counterObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        counterObserver.unobserve(entry.target);
        animateCounter(entry.target);
      });
    }, { threshold: 0.45 });

    proofCounters.forEach(function (counter) {
      counter.textContent = '0' + (counter.getAttribute('data-count-suffix') || '');
      counterObserver.observe(counter);
    });
  }

  if (!hero || reducedMotion || !finePointer) return;

  hero.addEventListener('pointermove', function (event) {
    var rect = hero.getBoundingClientRect();
    var x = ((event.clientX - rect.left) / rect.width) * 100;
    var y = ((event.clientY - rect.top) / rect.height) * 100;
    hero.style.setProperty('--spot-x', x.toFixed(1) + '%');
    hero.style.setProperty('--spot-y', y.toFixed(1) + '%');
  }, { passive: true });

  /* Ease toward the pointer instead of binding rotation directly to it. */
  cards.forEach(function (card) {
    var state = { rx: 0, ry: 0, scale: 1, targetRx: 0, targetRy: 0, targetScale: 1, frame: 0 };

    var draw = function () {
      state.rx += (state.targetRx - state.rx) * 0.12;
      state.ry += (state.targetRy - state.ry) * 0.12;
      state.scale += (state.targetScale - state.scale) * 0.12;
      card.style.setProperty('--deck-rx', state.rx.toFixed(3) + 'deg');
      card.style.setProperty('--deck-ry', state.ry.toFixed(3) + 'deg');
      card.style.setProperty('--deck-scale', state.scale.toFixed(4));

      var unsettled = Math.abs(state.targetRx - state.rx) > 0.015 ||
        Math.abs(state.targetRy - state.ry) > 0.015 ||
        Math.abs(state.targetScale - state.scale) > 0.001;
      state.frame = unsettled ? window.requestAnimationFrame(draw) : 0;
    };

    var wake = function () {
      if (!state.frame) state.frame = window.requestAnimationFrame(draw);
    };

    card.addEventListener('pointerenter', function () {
      state.targetScale = 1.018;
      wake();
    });

    card.addEventListener('pointermove', function (event) {
      var rect = card.getBoundingClientRect();
      var x = (event.clientX - rect.left) / rect.width - 0.5;
      var y = (event.clientY - rect.top) / rect.height - 0.5;
      state.targetRx = -y * 4.8;
      state.targetRy = x * 6.4;
      card.style.setProperty('--deck-glow-x', ((x + 0.5) * 100).toFixed(1) + '%');
      card.style.setProperty('--deck-glow-y', ((y + 0.5) * 100).toFixed(1) + '%');
      wake();
    }, { passive: true });

    card.addEventListener('pointerleave', function () {
      state.targetRx = 0;
      state.targetRy = 0;
      state.targetScale = 1;
      card.style.setProperty('--deck-glow-x', '50%');
      card.style.setProperty('--deck-glow-y', '50%');
      wake();
    });
  });

  reactiveCards.forEach(function (card) {
    card.addEventListener('pointermove', function (event) {
      var rect = card.getBoundingClientRect();
      var x = ((event.clientX - rect.left) / rect.width) * 100;
      var y = ((event.clientY - rect.top) / rect.height) * 100;
      card.style.setProperty('--reactive-x', x.toFixed(1) + '%');
      card.style.setProperty('--reactive-y', y.toFixed(1) + '%');
    }, { passive: true });

    card.addEventListener('pointerleave', function () {
      card.style.setProperty('--reactive-x', '50%');
      card.style.setProperty('--reactive-y', '50%');
    });
  });
}());
