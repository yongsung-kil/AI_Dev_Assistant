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
  var table = document.getElementById("paper-table");
  if (table && window.PAPERS) {
    var papers = window.PAPERS, labels = window.PAPER_LABELS || {};
    var q = document.getElementById("paper-search"), yMin = document.getElementById("year-min"), yMax = document.getElementById("year-max");
    var countBox = document.getElementById("paper-count"), more = document.getElementById("paper-more"), tbody = table.querySelector("tbody");
    var facetBoxes = document.querySelectorAll(".facet"), shownRows = 0, matched = [], PAGE = 100;
    function checked() {
      var sel = {};
      for (var i = 0; i < facetBoxes.length; i++) {
        var key = facetBoxes[i].getAttribute("data-facet"), boxes = facetBoxes[i].querySelectorAll("input:checked");
        if (boxes.length) { sel[key] = {}; for (var j = 0; j < boxes.length; j++) { sel[key][boxes[j].value] = true; } }
      }
      return sel;
    }
    function label(key, value) { return (labels[key] && labels[key][value]) || value; }
    function rowHtml(p) {
      var href = p.doc ? prefix + p.doc : (/^https?:\/\//.test(p.url || "") ? p.url : "");
      var title = href ? '<a href="' + esc(href) + '">' + esc(p.title) + "</a>" : esc(p.title);
      var chips = "";
      for (var k in p.facets) { if (k !== "source" && k !== "status" && k !== "analysis") { chips += '<span class="chip" title="' + esc(k) + '">' + esc(label(k, p.facets[k])) + "</span>"; } }
      return "<tr><td>" + title + (p.desc ? '<div class="card-desc">' + esc(p.desc) + "</div>" : "") + '</td><td class="num">' + (p.year || "") +
        "</td><td>" + esc(label("source", p.facets.source)) + "</td><td>" + esc(label("status", p.facets.status)) + "</td><td>" + chips + "</td></tr>";
    }
    function renderMore() {
      var end = Math.min(matched.length, shownRows + PAGE), html = "";
      for (var i = shownRows; i < end; i++) { html += rowHtml(matched[i]); }
      tbody.insertAdjacentHTML("beforeend", html);
      shownRows = end;
      more.classList.toggle("hidden", shownRows >= matched.length);
      countBox.textContent = matched.length + "편 중 " + shownRows + "편 표시";
    }
    function applyPapers() {
      var text = (q.value || "").trim().toLowerCase(), lo = parseInt(yMin.value, 10), hi = parseInt(yMax.value, 10), sel = checked();
      matched = [];
      for (var i = 0; i < papers.length; i++) {
        var p = papers[i], ok = true;
        if (text) { ok = ((p.title || "") + " " + (p.desc || "") + " " + (p.abstract || "")).toLowerCase().indexOf(text) >= 0; }
        if (ok && (!isNaN(lo) || !isNaN(hi)) && !p.year) { ok = false; }  // 연도 조건이 있으면 연도 없는 논문은 빠진다
        if (ok && !isNaN(lo) && p.year < lo) { ok = false; }
        if (ok && !isNaN(hi) && p.year > hi) { ok = false; }
        for (var key in sel) { if (ok && !sel[key][p.facets[key]]) { ok = false; } }
        if (ok) { matched.push(p); }
      }
      tbody.innerHTML = "";
      shownRows = 0;
      renderMore();
    }
    function applyPreset() {  // 주소의 #source=값: 그 글자가 든 출처를 모두 체크한다 (patent, google_patent 등)
      var preset = /source=([^&]+)/.exec(location.hash || "");
      if (!preset) { return; }
      var want = preset[1];
      try { want = decodeURIComponent(want); } catch (e) {}
      var boxes = document.querySelectorAll('.facet[data-facet="source"] input');
      for (var i = 0; i < boxes.length; i++) { boxes[i].checked = boxes[i].value.indexOf(want) >= 0; }
    }
    applyPreset();
    window.addEventListener("hashchange", function () { applyPreset(); applyPapers(); });
    q.addEventListener("input", applyPapers);
    yMin.addEventListener("input", applyPapers);
    yMax.addEventListener("input", applyPapers);
    for (var f = 0; f < facetBoxes.length; f++) { facetBoxes[f].addEventListener("change", applyPapers); }
    more.addEventListener("click", renderMore);
    var reset = document.getElementById("paper-reset");
    if (reset) {
      reset.addEventListener("click", function () {
        q.value = ""; yMin.value = ""; yMax.value = "";
        var all = document.querySelectorAll(".facet input:checked");
        for (var i = 0; i < all.length; i++) { all[i].checked = false; }
        applyPapers();
      });
    }
    applyPapers();
  }
})();
