(function () {
  'use strict';

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 02 · Power-4 Girth Index: spin a direct matchup ---------- */
  (function matchupSpinner() {
    var root = document.querySelector('[data-matchup]');
    if (!root) return;

    var conferences = [
      ['ACC', ['Boston College', 'California', 'Clemson', 'Duke', 'Florida State', 'Georgia Tech', 'Louisville', 'Miami', 'North Carolina', 'NC State', 'Pitt', 'SMU', 'Stanford', 'Syracuse', 'Virginia', 'Virginia Tech', 'Wake Forest']],
      ['Big Ten', ['Illinois', 'Indiana', 'Iowa', 'Maryland', 'Michigan', 'Michigan State', 'Minnesota', 'Nebraska', 'Northwestern', 'Ohio State', 'Oregon', 'Penn State', 'Purdue', 'Rutgers', 'UCLA', 'USC', 'Washington', 'Wisconsin']],
      ['Big 12', ['Arizona', 'Arizona State', 'Baylor', 'BYU', 'Cincinnati', 'Colorado', 'Houston', 'Iowa State', 'Kansas', 'Kansas State', 'Oklahoma State', 'TCU', 'Texas Tech', 'UCF', 'Utah', 'West Virginia']],
      ['SEC', ['Alabama', 'Arkansas', 'Auburn', 'Florida', 'Georgia', 'Kentucky', 'LSU', 'Mississippi State', 'Missouri', 'Oklahoma', 'Ole Miss', 'South Carolina', 'Tennessee', 'Texas', 'Texas A&M', 'Vanderbilt']]
    ];

    var programs = [];
    conferences.forEach(function (entry) {
      entry[1].forEach(function (name) { programs.push({ name: name, conf: entry[0] }); });
    });

    var board = root.querySelector('[data-matchup-board]');
    var dots = [];
    if (board) {
      programs.forEach(function (program) {
        var dot = document.createElement('i');
        dot.setAttribute('data-conf', program.conf);
        dot.title = program.name;
        board.appendChild(dot);
        dots.push(dot);
      });
    }

    var slotEls = { a: root.querySelector('[data-matchup-slot="a"]'), b: root.querySelector('[data-matchup-slot="b"]') };
    var nameEls = { a: root.querySelector('[data-matchup-name="a"]'), b: root.querySelector('[data-matchup-name="b"]') };
    var confEls = { a: root.querySelector('[data-matchup-conf="a"]'), b: root.querySelector('[data-matchup-conf="b"]') };
    var spin = root.querySelector('[data-matchup-spin]');
    var live = root.querySelector('[data-matchup-live]');
    var rolling = false;

    var indexOf = function (name) {
      for (var i = 0; i < programs.length; i++) if (programs[i].name === name) return i;
      return -1;
    };

    var show = function (key, index) {
      var program = programs[index];
      if (nameEls[key]) nameEls[key].textContent = program.name;
      if (confEls[key]) confEls[key].textContent = program.conf;
      if (slotEls[key]) slotEls[key].setAttribute('data-conf', program.conf);
    };

    var highlight = function (ia, ib) {
      dots.forEach(function (dot, i) {
        dot.classList.toggle('is-picked', i === ia || i === ib);
        dot.classList.remove('is-rolling');
      });
    };

    var pickPair = function () {
      var ia = Math.floor(Math.random() * programs.length);
      var ib = Math.floor(Math.random() * (programs.length - 1));
      if (ib >= ia) ib += 1;
      return [ia, ib];
    };

    var settle = function (pair) {
      show('a', pair[0]);
      show('b', pair[1]);
      highlight(pair[0], pair[1]);
      ['a', 'b'].forEach(function (key) { if (slotEls[key]) slotEls[key].classList.remove('is-rolling'); });
      if (spin) spin.classList.remove('is-rolling');
      if (live) live.textContent = programs[pair[0]].name + ' versus ' + programs[pair[1]].name;
      rolling = false;
    };

    var roll = function () {
      if (rolling) return;
      rolling = true;
      var pair = pickPair();
      if (reducedMotion) { settle(pair); return; }

      ['a', 'b'].forEach(function (key) { if (slotEls[key]) slotEls[key].classList.add('is-rolling'); });
      if (spin) spin.classList.add('is-rolling');
      dots.forEach(function (dot) { dot.classList.remove('is-picked'); });

      var ticks = 0;
      var total = 14;
      var step = function () {
        ticks += 1;
        var ra = Math.floor(Math.random() * programs.length);
        var rb = Math.floor(Math.random() * programs.length);
        show('a', ra);
        show('b', rb);
        dots.forEach(function (dot, i) { dot.classList.toggle('is-rolling', i === ra || i === rb); });
        if (ticks < total) window.setTimeout(step, 45 + ticks * 9);
        else settle(pair);
      };
      step();
    };

    highlight(indexOf('Arizona'), indexOf('Arizona State'));
    if (spin) spin.addEventListener('click', roll);
  }());

  /* ---------- 03 · Small Mammal Tracker: check the trap line ---------- */
  (function trapLine() {
    var root = document.querySelector('[data-trapline]');
    if (!root) return;

    var traps = Array.prototype.slice.call(root.querySelectorAll('[data-trap]'));
    var count = root.querySelector('[data-trapline-count]');
    var readout = root.querySelector('[data-trapline-readout]');
    var reset = root.querySelector('[data-trapline-reset]');
    var total = traps.length;

    var checked = function () {
      return traps.filter(function (trap) { return trap.getAttribute('aria-pressed') === 'true'; });
    };

    var summarize = function () {
      var done = checked();
      var captures = done.filter(function (trap) { return trap.getAttribute('data-trap'); });
      if (count) count.textContent = 'Trap check · ' + done.length + ' of ' + total;
      if (reset) reset.hidden = done.length === 0;
      if (done.length === total && readout) {
        var tally = {};
        captures.forEach(function (trap) {
          var species = trap.getAttribute('data-trap');
          tally[species] = (tally[species] || 0) + 1;
        });
        var best = 0;
        Object.keys(tally).forEach(function (k) { if (tally[k] > best) best = tally[k]; });
        var leaders = Object.keys(tally).filter(function (k) { return tally[k] === best; });
        readout.innerHTML = 'Night complete: ' + captures.length + ' captures in ' + total + ' traps. Hall of Fame: <em>' +
          leaders.join('</em> and <em>') + '</em>, ' + best + ' each.';
      }
    };

    var describe = function (trap) {
      if (!readout) return;
      var id = trap.getAttribute('aria-label').replace('Trap ', '');
      var species = trap.getAttribute('data-trap');
      var tag = trap.getAttribute('data-tag');
      var note = trap.getAttribute('data-note');
      if (!species) {
        readout.textContent = id + ' · empty. Bait gone, door sprung, nobody home.';
        return;
      }
      readout.innerHTML = id + ' · <em>' + species + '</em> · tag ' + tag + (note ? ' · ' + note + ', already in the history' : ' · new capture');
    };

    root.addEventListener('click', function (event) {
      var trap = event.target.closest('[data-trap]');
      if (trap) {
        var open = trap.getAttribute('aria-pressed') === 'true';
        if (open) {
          trap.setAttribute('aria-pressed', 'false');
          trap.classList.remove('is-capture', 'is-empty');
          if (readout) readout.textContent = trap.getAttribute('aria-label') + ' reset and re-baited.';
        } else {
          trap.setAttribute('aria-pressed', 'true');
          trap.classList.add(trap.getAttribute('data-trap') ? 'is-capture' : 'is-empty');
          describe(trap);
        }
        summarize();
        return;
      }
      if (event.target.closest('[data-trapline-reset]')) {
        traps.forEach(function (t) {
          t.setAttribute('aria-pressed', 'false');
          t.classList.remove('is-capture', 'is-empty');
        });
        if (readout) readout.textContent = 'Fresh night. Traps baited with peanut butter and oats. Tap one to check it.';
        summarize();
      }
    });

    summarize();
  }());

  /* ---------- 04 · Plants in Movies: the specimen lens ---------- */
  (function specimenLens() {
    var root = document.querySelector('[data-lens]');
    if (!root) return;

    var glass = root.querySelector('[data-lens-glass]');
    var art = root.querySelector('.lens-art');
    var worlds = Array.prototype.slice.call(root.querySelectorAll('[data-lens-world]'));
    if (!glass || !art) return;

    var zoom = 2.3;
    var rest = { x: 0.40, y: 0.58 };
    var frame = 0;
    var pending = null;

    /* Match object-fit: cover so the lens shows the same pixels, magnified. */
    var paint = function (fx, fy) {
      var w = root.clientWidth;
      var h = root.clientHeight;
      var natural = (art.naturalWidth && art.naturalHeight) ? art.naturalWidth / art.naturalHeight : 1100 / 733;
      var scale = Math.max(w / natural, h);
      var drawnW = scale * natural;
      var drawnH = scale;
      var offsetX = (w - drawnW) * 0.06;
      var offsetY = (h - drawnH) * 0.58;
      var size = glass.offsetWidth || 112;
      var px = fx * w;
      var py = fy * h;
      var bgX = size / 2 - (px - offsetX) * zoom;
      var bgY = size / 2 - (py - offsetY) * zoom;
      glass.style.setProperty('--lens-x', (fx * 100).toFixed(2) + '%');
      glass.style.setProperty('--lens-y', (fy * 100).toFixed(2) + '%');
      glass.style.backgroundSize = (drawnW * zoom) + 'px ' + (drawnH * zoom) + 'px';
      glass.style.backgroundPosition = bgX + 'px ' + bgY + 'px';
    };

    var schedule = function (fx, fy) {
      pending = { x: fx, y: fy };
      if (frame) return;
      frame = window.requestAnimationFrame(function () {
        frame = 0;
        if (pending) paint(pending.x, pending.y);
      });
    };

    var fromEvent = function (event) {
      var rect = root.getBoundingClientRect();
      var fx = Math.min(0.96, Math.max(0.04, (event.clientX - rect.left) / rect.width));
      var fy = Math.min(0.96, Math.max(0.04, (event.clientY - rect.top) / rect.height));
      return { x: fx, y: fy };
    };

    var tracking = false;
    root.addEventListener('pointermove', function (event) {
      if (event.pointerType === 'touch' && !tracking) return;
      root.classList.add('is-tracking');
      var p = fromEvent(event);
      schedule(p.x, p.y);
    }, { passive: true });

    root.addEventListener('pointerdown', function (event) {
      if (event.target.closest('button')) return;
      tracking = true;
      root.classList.add('is-tracking');
      var p = fromEvent(event);
      schedule(p.x, p.y);
    }, { passive: true });

    var release = function () {
      tracking = false;
      root.classList.remove('is-tracking');
    };
    root.addEventListener('pointerleave', function () {
      release();
      schedule(rest.x, rest.y);
    });
    root.addEventListener('pointerup', release);
    root.addEventListener('pointercancel', release);

    worlds.forEach(function (button) {
      button.addEventListener('click', function () {
        var key = button.getAttribute('data-lens-world');
        root.setAttribute('data-world', key);
        worlds.forEach(function (b) {
          var on = b === button;
          b.classList.toggle('is-active', on);
          b.setAttribute('aria-pressed', String(on));
        });
      });
    });

    var ready = function () { paint(rest.x, rest.y); };
    if (art.complete) ready();
    else art.addEventListener('load', ready);
    window.addEventListener('resize', function () { schedule(rest.x, rest.y); });
  }());
}());
