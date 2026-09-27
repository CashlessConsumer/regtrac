/* Stack search — one query across the sousveillance stack.
   Byte-identical in RegTrac / SROTrac / LobbyWatch (js/search.js).
   Config: window.STACK_SEARCH.layers = [{key,label,base,self}]. */
(function () {
  "use strict";
  var cfg = window.STACK_SEARCH || { layers: [] };
  var input = document.getElementById("stack-search-input");
  var results = document.getElementById("stack-search-results");
  var statusEl = document.getElementById("stack-search-status");
  if (!input || !results) return;

  var corpus = {};   // key -> {label, base, self, pages, state, err}

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function snippet(text, tokens) {
    if (!text) return "";
    var low = text.toLowerCase(), pos = -1;
    for (var i = 0; i < tokens.length; i++) {
      pos = low.indexOf(tokens[i]);
      if (pos >= 0) break;
    }
    if (pos < 0) return esc(text.slice(0, 140)) + (text.length > 140 ? "\u2026" : "");
    var start = Math.max(0, pos - 70), end = Math.min(text.length, pos + 90);
    return (start > 0 ? "\u2026" : "") + esc(text.slice(start, end)) + (end < text.length ? "\u2026" : "");
  }

  function score(p, tokens) {
    var title = (p.title || "").toLowerCase();
    var desc = (p.desc || "").toLowerCase();
    var text = (p.text || "").toLowerCase();
    var total = 0;
    for (var i = 0; i < tokens.length; i++) {
      var t = tokens[i], s = 0;
      var ti = title.indexOf(t);
      if (ti >= 0) { s += 25; if (ti === 0 || title.charAt(ti - 1) === " ") s += 8; }
      if (desc.indexOf(t) >= 0) s += 8;
      if (text.indexOf(t) >= 0) s += 3;
      if (s === 0) return -1; // every token must hit somewhere
      total += s;
    }
    return total;
  }

  function search(q) {
    var tokens = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!tokens.length) { render(null); return; }
    var hits = [];
    Object.keys(corpus).forEach(function (key) {
      var layer = corpus[key];
      if (!layer.pages) return;
      var n = 0;
      layer.pages.forEach(function (p) {
        var s = score(p, tokens);
        if (s > 0 && n < 8) {
          hits.push({ layer: key, p: p, s: s });
          n++;
        }
      });
    });
    hits.sort(function (a, b) { return b.s - a.s; });
    render(hits, tokens);
  }

  function render(hits, tokens) {
    var html = "";
    cfg.layers.forEach(function (l) {
      var layer = corpus[l.key] || {};
      var group = (hits || []).filter(function (h) { return h.layer === l.key; });
      html += '<div class="ss-layer"><h2>' + esc(l.label);
      if (layer.state === "ok") {
        html += ' <span class="ss-count">' + group.length + "</span>";
      } else {
        html += ' <span class="ss-mute">index unavailable</span>';
      }
      html += "</h2>";
      if (layer.state === "ok") {
        group.forEach(function (h) {
          var url = (l.base || "") + h.p.url;
          html += '<div class="ss-hit"><a href="' + esc(url) + '">' + esc(h.p.title) + "</a>";
          if (h.p.desc) html += '<span class="ss-desc">' + esc(h.p.desc) + "</span>";
          if (tokens) html += '<span class="ss-snip">' + snippet(h.p.text || "", tokens) + "</span>";
          html += "</div>";
        });
        if (!group.length && hits) html += '<div class="ss-mute">no matches</div>';
      } else if (layer.state === "err") {
        html += '<div class="ss-mute">Could not load this layer\u2019s index' +
          (l.self ? "" : " (cross-site fetch blocked)") +
          '. Browse it directly: <a href="' + (l.base || "") + '">' + esc(l.label) + "</a></div>";
      }
      html += "</div>";
    });
    results.innerHTML = html;
    if (hits === null) results.innerHTML = "";
  }

  function fetchLayer(l) {
    var url = (l.self ? "" : l.base) + "search-index.json";
    corpus[l.key] = { label: l.label, base: l.base, state: "loading" };
    fetch(url, { credentials: "omit" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) {
        corpus[l.key].pages = data.pages || [];
        corpus[l.key].state = "ok";
        if (input.value.trim()) search(input.value);
        refreshStatus();
      })
      .catch(function () {
        corpus[l.key].state = "err";
        refreshStatus();
      });
  }

  function refreshStatus() {
    var ok = 0, err = 0, load = 0;
    Object.keys(corpus).forEach(function (k) {
      if (corpus[k].state === "ok") ok++;
      else if (corpus[k].state === "err") err++;
      else load++;
    });
    var bits = [];
    if (load) bits.push("loading " + load + " index\u2026");
    if (ok) bits.push(ok + " layer" + (ok > 1 ? "s" : "") + " ready");
    if (err) bits.push(err + " unavailable");
    statusEl.textContent = bits.join(" \u00b7 ");
  }

  var timer = null;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { search(input.value); }, 120);
  });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      var first = results.querySelector(".ss-hit a");
      if (first) first.click();
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== input) {
      e.preventDefault();
      input.focus();
    }
  });

  cfg.layers.forEach(fetchLayer);
})();
