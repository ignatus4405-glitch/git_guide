/* ============================================================================
   Курс «Git и GitHub» — клиентские скрипты.
   Всё без зависимостей и без обращения к сторонним сервисам:
     1. тема оформления (светлая/тёмная, запоминается в localStorage)
     2. мобильное оглавление
     3. кнопки «Скопировать» у блоков кода
     4. интерактивные вопросы для самопроверки
     5. прогресс по урокам (localStorage) + полоса в шапке
     6. поиск по курсу (search-index.json, собирается build.py)
     7. подсветка текущего раздела в оглавлении страницы
   ========================================================================== */
(function () {
  "use strict";

  var body = document.body;
  var THEME_KEY = "gg-theme";
  var PROGRESS_KEY = "gg-progress";
  var TOTAL_LESSONS = parseInt(body.dataset.lessons || "0", 10) || 0;

  // Корень сайта: вычисляем по адресу самого скрипта, чтобы ссылки работали
  // и при открытии из file://, и из подкаталога /git_guide/.
  var scriptEl = document.querySelector('script[src$="assets/js/app.js"]');
  var siteRoot = "";
  if (scriptEl) {
    siteRoot = scriptEl.src.replace(/assets\/js\/app\.js.*$/, "");
  }

  /* 1. Тема --------------------------------------------------------------- */
  function initTheme() {
    var btn = document.querySelector("[data-theme-toggle]");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
    });
  }

  /* 2. Мобильное оглавление ---------------------------------------------- */
  function initSidebar() {
    var toggle = document.querySelector("[data-sidebar-toggle]");
    var underlay = document.querySelector("[data-sidebar-underlay]");
    if (!toggle) return;
    function setOpen(open) {
      body.classList.toggle("is-sidebar-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      if (underlay) underlay.hidden = !open;
    }
    toggle.addEventListener("click", function () {
      setOpen(!body.classList.contains("is-sidebar-open"));
    });
    if (underlay) underlay.addEventListener("click", function () { setOpen(false); });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") setOpen(false);
    });
  }

  /* 3. Копирование кода -------------------------------------------------- */
  function initCopy() {
    document.querySelectorAll("[data-copy]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var block = btn.closest(".code");
        var code = block ? block.querySelector("code") : null;
        if (!code) return;
        var text = code.innerText.replace(/^\s*\d+\s?/gm, "");
        var done = function () {
          var old = btn.textContent;
          btn.textContent = "Скопировано ✓";
          setTimeout(function () { btn.textContent = old; }, 1600);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
        } else {
          fallback(text, done);
        }
      });
    });
    function fallback(text, done) {
      var area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.left = "-9999px";
      document.body.appendChild(area);
      area.select();
      try { document.execCommand("copy"); done(); } catch (e) {}
      document.body.removeChild(area);
    }
  }

  /* 4. Вопросы для самопроверки ------------------------------------------ */
  function initQuizzes() {
    document.querySelectorAll("[data-quiz]").forEach(function (quiz) {
      var options = quiz.querySelectorAll(".quiz__opt");
      var explain = quiz.querySelector(".quiz__explain");
      var done = quiz.querySelector(".quiz__done");
      options.forEach(function (option) {
        option.addEventListener("click", function () {
          var correct = option.dataset.correct === "1";
          option.classList.add(correct ? "is-correct" : "is-wrong");
          if (correct) {
            options.forEach(function (other) { other.disabled = true; });
            if (done) done.hidden = false;
          }
          if (explain) explain.hidden = false;
        });
      });
    });
  }

  /* 5. Прогресс ---------------------------------------------------------- */
  function readProgress() {
    try { return JSON.parse(localStorage.getItem(PROGRESS_KEY) || "[]"); } catch (e) { return []; }
  }
  function writeProgress(list) {
    try { localStorage.setItem(PROGRESS_KEY, JSON.stringify(list)); } catch (e) {}
  }
  function refreshProgress() {
    var list = readProgress();
    var fill = document.querySelector("[data-progress-fill]");
    var text = document.querySelector("[data-progress-text]");
    var percent = TOTAL_LESSONS ? Math.round((list.length / TOTAL_LESSONS) * 100) : 0;
    if (fill) fill.style.width = Math.min(100, percent) + "%";
    if (text) text.textContent = percent + "%";
  }
  function initProgress() {
    var list = readProgress();
    document.querySelectorAll("[data-lesson-check]").forEach(function (box) {
      var slug = box.dataset.lessonCheck;
      box.checked = list.indexOf(slug) !== -1;
      box.addEventListener("change", function () {
        var current = readProgress();
        var index = current.indexOf(slug);
        if (box.checked && index === -1) current.push(slug);
        if (!box.checked && index !== -1) current.splice(index, 1);
        writeProgress(current);
        document.querySelectorAll('[data-lesson-check="' + slug + '"]').forEach(function (other) {
          other.checked = box.checked;
        });
        refreshProgress();
      });
    });
    refreshProgress();
  }

  /* 6. Поиск ------------------------------------------------------------- */
  function initSearch() {
    var overlay = document.querySelector("[data-search]");
    if (!overlay) return;
    var input = overlay.querySelector("[data-search-input]");
    var list = overlay.querySelector("[data-search-results]");
    var openBtn = document.querySelector("[data-search-open]");
    var index = null;
    var active = -1;

    function open() {
      overlay.hidden = false;
      input.value = "";
      input.focus();
      render([]);
      load();
    }
    function close() {
      overlay.hidden = true;
      active = -1;
    }
    function load() {
      if (index || !siteRoot) return;
      fetch(siteRoot + "search-index.json")
        .then(function (r) { return r.json(); })
        .then(function (data) { index = data.items || []; })
        .catch(function () {
          list.innerHTML = '<li class="search__empty"><span class="s">Поиск недоступен: ' +
            "индекс не загрузился (при открытии файла напрямую браузер блокирует fetch). " +
            "Соберите сайт и откройте его через локальный сервер: python3 tools/serve.py</span></li>";
        });
    }
    function highlight(text, query) {
      if (!query) return text;
      var at = text.toLowerCase().indexOf(query.toLowerCase());
      if (at < 0) return text;
      return text.slice(0, at) + "<mark>" + text.slice(at, at + query.length) + "</mark>" + text.slice(at + query.length);
    }
    function escapeHtml(value) {
      return String(value).replace(/[&<>"]/g, function (ch) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch];
      });
    }
    function render(items) {
      list.innerHTML = items.map(function (item, i) {
        var excerpt = item.s || item.x.slice(0, 150);
        return '<li data-i="' + i + '"><a href="' + siteRoot + item.u + '">' +
          '<span class="m">' + escapeHtml(item.m) + " · " + (item.k === "lesson" ? "урок" : "материал") + "</span>" +
          "<strong>" + highlight(escapeHtml(item.t), input.value) + "</strong>" +
          '<span class="s">' + highlight(escapeHtml(excerpt), input.value) + "</span></a></li>";
      }).join("");
      active = items.length ? 0 : -1;
      mark();
    }
    function mark() {
      list.querySelectorAll("li").forEach(function (li, i) {
        li.classList.toggle("is-active", i === active);
      });
    }
    function search(query) {
      if (!index) return [];
      var words = query.toLowerCase().split(/\s+/).filter(Boolean);
      if (!words.length) return index.slice(0, 6);
      var results = [];
      index.forEach(function (item) {
        var haystack = (item.t + " " + item.s + " " + item.x).toLowerCase();
        var score = 0;
        words.forEach(function (word) {
          var inTitle = item.t.toLowerCase().indexOf(word) !== -1;
          var inBody = haystack.indexOf(word) !== -1;
          if (!inBody) { score = -1e9; return; }
          score += (inTitle ? 12 : 0) + (item.s.toLowerCase().indexOf(word) !== -1 ? 4 : 0) + 1;
        });
        if (score > -1e8) results.push({ item: item, score: score + (item.k === "lesson" ? 0.5 : 0) });
      });
      return results.sort(function (a, b) { return b.score - a.score; }).slice(0, 12)
        .map(function (entry) { return entry.item; });
    }

    if (openBtn) openBtn.addEventListener("click", open);
    overlay.addEventListener("click", function (event) { if (event.target === overlay) close(); });
    input.addEventListener("input", function () { render(search(input.value)); });
    input.addEventListener("keydown", function (event) {
      var items = list.querySelectorAll("li");
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        if (!items.length) return;
        active = (active + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
        mark();
        items[active].scrollIntoView({ block: "nearest" });
      } else if (event.key === "Enter" && active >= 0 && items[active]) {
        items[active].querySelector("a").click();
      } else if (event.key === "Escape") {
        close();
      }
    });
    document.addEventListener("keydown", function (event) {
      var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
      if ((event.key === "/" && !typing) || ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k")) {
        event.preventDefault();
        open();
      }
    });
  }

  /* 7. Оглавление страницы ----------------------------------------------- */
  function initScrollSpy() {
    var links = Array.prototype.slice.call(document.querySelectorAll(".toc a[href^='#']"));
    if (!links.length || !("IntersectionObserver" in window)) return;
    var map = {};
    links.forEach(function (link) { map[link.getAttribute("href").slice(1)] = link; });
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        links.forEach(function (link) { link.classList.remove("is-active"); });
        var link = map[entry.target.id];
        if (link) link.classList.add("is-active");
      });
    }, { rootMargin: "-80px 0px -70% 0px", threshold: 0 });
    Object.keys(map).forEach(function (id) {
      var target = document.getElementById(id);
      if (target) observer.observe(target);
    });
  }

  function boot() {
    initTheme();
    initSidebar();
    initCopy();
    initQuizzes();
    initProgress();
    initSearch();
    initScrollSpy();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
