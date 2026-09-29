(function () {
  var prefix = window.DASH_PREFIX || "";
  var input = document.getElementById("search");
  var box = document.getElementById("search-results");
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }
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
  }
  var here = decodeURIComponent(location.pathname.split("/").slice(-1)[0]);
  var links = document.querySelectorAll(".sidebar a");
  for (var j = 0; j < links.length; j++) {
    var h = decodeURIComponent(links[j].getAttribute("href") || "").split("#")[0].split("/").slice(-1)[0];
    if (h && h === here && links[j].className.indexOf("nav-home") < 0) {
      links[j].classList.add("current");
      var det = links[j].closest("details"); while (det) { det.open = true; det = det.parentElement.closest("details"); }
    }
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
})();
