(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // Theme toggle (remembered per browser)
  const root = document.documentElement;
  try { const t = localStorage.getItem("theme"); if (t) root.dataset.theme = t; } catch (e) {}
  $(".nav__theme")?.addEventListener("click", () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
  });

  // Nav: active section + sliding pill
  const links = $$(".nav__links a");
  const pill = $(".nav__pill");
  const sections = links.map(a => $(a.getAttribute("href")));
  const movePill = a => {
    if (!a) return;
    pill.style.width = a.offsetWidth + "px";
    pill.style.transform = `translateX(${a.offsetLeft}px)`;
  };
  let current;
  const setActive = i => {
    if (current === i) return;
    current = i;
    links.forEach((a, j) => a.classList.toggle("is-active", j === i));
    movePill(links[i]);
    links[i].scrollIntoView({ block: "nearest", inline: "nearest", behavior: reduce ? "auto" : "smooth" });
  };

  // Scroll-driven: progress bar, active section, timeline fill
  const bar = $(".progress");
  const timeline = $(".timeline");
  const fill = $(".timeline__fill");
  const onScroll = () => {
    const h = document.documentElement.scrollHeight - innerHeight;
    bar.style.transform = `scaleX(${h > 0 ? scrollY / h : 0})`;
    const mid = innerHeight * 0.4;
    let idx = 0;
    sections.forEach((s, i) => { if (s && s.getBoundingClientRect().top <= mid) idx = i; });
    if (innerHeight + scrollY >= document.documentElement.scrollHeight - 4) idx = sections.length - 1;
    setActive(idx);
    if (timeline) {
      const r = timeline.getBoundingClientRect();
      const p = Math.min(1, Math.max(0, (innerHeight * 0.6 - r.top) / r.height));
      fill.style.setProperty("--p", p);
    }
  };
  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", () => movePill(links[current]));
  onScroll();

  // Reveal on scroll: only items below the fold get hidden first, so the page is complete at rest
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      e.target.classList.remove("is-pre");
      e.target.classList.add("is-seen");
      io.unobserve(e.target);
    });
  }, { rootMargin: "0px 0px -12% 0px" });
  $$(".reveal, .job").forEach((el, i) => {
    if (!reduce && el.classList.contains("reveal") && el.getBoundingClientRect().top > innerHeight) {
      el.classList.add("is-pre");
      el.style.transitionDelay = (i % 3) * 70 + "ms";
    }
    io.observe(el);
  });

  // Rotating role in hero
  const roles = $$(".roles > span");
  if (roles.length > 1 && !reduce) {
    let r = 0;
    setInterval(() => {
      const prev = roles[r];
      r = (r + 1) % roles.length;
      prev.classList.replace("is-on", "is-out");
      setTimeout(() => prev.classList.remove("is-out"), 600);
      roles[r].classList.add("is-on");
    }, 2600);
  }

  // Count-up stats
  const countIO = new IntersectionObserver(entries => entries.forEach(e => {
    if (!e.isIntersecting) return;
    countIO.unobserve(e.target);
    const el = e.target, end = +el.dataset.count, suffix = el.dataset.suffix || "";
    if (reduce) return;
    const t0 = performance.now();
    const tick = t => {
      const k = Math.min(1, (t - t0) / 1400);
      el.textContent = Math.round(end * (1 - Math.pow(1 - k, 3))) + suffix;
      if (k < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }));
  $$("[data-count]").forEach(el => countIO.observe(el));

  // Spotlight that follows the cursor on project cards
  $$(".project").forEach(card => card.addEventListener("pointermove", e => {
    const r = card.getBoundingClientRect();
    card.style.setProperty("--mx", e.clientX - r.left + "px");
    card.style.setProperty("--my", e.clientY - r.top + "px");
  }));

  // Reviews: pick an author, auto-advance unless hovered
  const reviews = $(".reviews");
  if (reviews) {
    const data = $$("template[data-review]", reviews).map(t => t.content);
    const quote = $(".quote", reviews);
    const buttons = $$(".author", reviews);
    let i = 0, timer;
    const DUR = 9000;
    const show = n => {
      i = n;
      const c = data[n];
      quote.innerHTML = "";
      quote.append(c.cloneNode(true));
      quote.classList.remove("is-swapping"); void quote.offsetWidth; quote.classList.add("is-swapping");
      buttons.forEach((b, j) => {
        b.setAttribute("aria-pressed", j === n);
        const bar = $(".author__bar", b);
        bar.style.animation = "none"; void bar.offsetWidth; bar.style.animation = "";
      });
      schedule();
    };
    let remaining = DUR, started = 0;
    const schedule = (ms = DUR) => {
      clearTimeout(timer);
      if (reduce) return;
      remaining = ms; started = performance.now();
      timer = setTimeout(() => show((i + 1) % data.length), ms);
    };
    reviews.style.setProperty("--dur", DUR / 1000 + "s");
    buttons.forEach((b, j) => b.addEventListener("click", () => show(j)));
    reviews.addEventListener("pointerenter", () => {
      clearTimeout(timer); remaining -= performance.now() - started; reviews.classList.add("is-paused");
    });
    reviews.addEventListener("pointerleave", () => { reviews.classList.remove("is-paused"); schedule(Math.max(remaining, 400)); });
    show(0);
  }

  // Copy email
  $$(".copy").forEach(btn => btn.addEventListener("click", async () => {
    const text = btn.dataset.copy;
    try { await navigator.clipboard.writeText(text); btn.textContent = "Copied"; }
    catch (e) {
      const sel = getSelection(), range = document.createRange();
      range.selectNodeContents($(".email code")); sel.removeAllRanges(); sel.addRange(range);
      btn.textContent = "Selected";
    }
    setTimeout(() => (btn.textContent = "Copy"), 1800);
  }));

  $("#year").textContent = new Date().getFullYear();
})();
