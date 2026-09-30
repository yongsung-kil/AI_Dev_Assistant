(function () {
  var prefix = window.DASH_PREFIX || "";
  var root = document.documentElement;
  function store(key, value) { try { localStorage.setItem(key, value); } catch (e) {} }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }
  var input = document.getElementById("search");
  var box = document.getElementById("search-results");
  if (input && box) {
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      if (!q || !window.DASH_INDEX) { box.hidden = true; box.innerHTML = ""; return; }
      var hits = [];
      for (var i = 0; i < window.DASH_INDEX.length && hits.length < 20; i++) {
        var d = window.DASH_INDEX[i];
        var t = d.title.toLowerCase(), b = d.text.toLowerCase();
        var at = t.indexOf(q) >= 0 ? -1 : b.indexOf(q);
        if (t.indexOf(q) >= 0 || at >= 0) {
          var snip = at >= 0 ? d.text.substring(Math.max(0, at - 40), at + 60) : d.text.substring(0, 80);
          hits.push('<a href="' + prefix + d.path + '">' + esc(d.title) + '<div class="snippet">' + esc(snip) + '</div></a>');
        }
      }
      box.innerHTML = hits.length ? hits.join("") : '<div class="snippet">결과 없음</div>';
      box.hidden = false;
    });
    document.addEventListener("click", function (e) { if (!box.contains(e.target) && e.target !== input) { box.hidden = true; } });
    document.addEventListener("keydown", function (e) { if ((e.ctrlKey || e.metaKey) && e.key === "k") { e.preventDefault(); input.focus(); } });
  }
  var navToggle = document.getElementById("nav-toggle");
  if (navToggle) {
    navToggle.addEventListener("click", function () {
      var closed = root.classList.toggle("nav-closed");
      store("dash-nav", closed ? "closed" : "open");
    });
  }
  var themeBox = document.getElementById("theme-toggle");
  if (themeBox) {
    var buttons = themeBox.querySelectorAll("button");
    function mark() {
      var cur = root.getAttribute("data-theme") || "";
      for (var i = 0; i < buttons.length; i++) { buttons[i].classList.toggle("on", buttons[i].getAttribute("data-theme") === cur); }
    }
    for (var j = 0; j < buttons.length; j++) {
      buttons[j].addEventListener("click", function () {
        var v = this.getAttribute("data-theme");
        if (v) { root.setAttribute("data-theme", v); } else { root.removeAttribute("data-theme"); }
        store("dash-theme", v);
        mark();
      });
    }
    mark();
  }
  var heads = document.querySelectorAll(".content h2, .content h3");
  var tocLinks = document.querySelectorAll(".toc a");
  if (heads.length && tocLinks.length && "IntersectionObserver" in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          for (var k = 0; k < tocLinks.length; k++) { tocLinks[k].classList.toggle("active", tocLinks[k].getAttribute("href") === "#" + en.target.id); }
        }
      });
    }, { rootMargin: "0px 0px -70% 0px" });
    for (var m = 0; m < heads.length; m++) { obs.observe(heads[m]); }
  }
  var from = document.getElementById("range-from"), to = document.getElementById("range-to");
  if (from && to) {
    var month = "";
    function applyFilter() {
      var lo = from.value, hi = to.value;
      if (lo > hi) { var tmp = lo; lo = hi; hi = tmp; }
      var changes = document.querySelectorAll(".change");
      var shown = {};
      for (var i = 0; i < changes.length; i++) {
        var d = changes[i].getAttribute("data-date");
        var ok = d >= lo && d <= hi && (!month || changes[i].getAttribute("data-month") === month);
        changes[i].classList.toggle("hidden", !ok);
        if (ok) { shown[d] = true; }
      }
      var vers = document.querySelectorAll(".ver");
      for (var v = 0; v < vers.length; v++) { vers[v].classList.toggle("hidden", !shown[vers[v].getAttribute("data-date")]); }
      var grids = document.querySelectorAll(".changes");
      for (var g = 0; g < grids.length; g++) { grids[g].classList.toggle("hidden", !shown[grids[g].getAttribute("data-date")]); }
    }
    from.addEventListener("change", applyFilter);
    to.addEventListener("change", applyFilter);
    var tabs = document.querySelectorAll(".tab");
    for (var t = 0; t < tabs.length; t++) {
      tabs[t].addEventListener("click", function () {
        month = this.getAttribute("data-month") || "";
        for (var u = 0; u < tabs.length; u++) { tabs[u].classList.toggle("active", tabs[u] === this); }
        applyFilter();
      });
    }
    applyFilter();
  }
})();
