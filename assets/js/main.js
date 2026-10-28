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

  // Owner-only link to the VC pages: visit ?me once to turn it on in this browser, ?me=off to turn it off.
  // The same flag keeps the owner's own visits out of Umami analytics (umami.disabled is read by the tracker).
  try {
    const me = new URLSearchParams(location.search).get("me");
    if (me !== null) {
      if (me === "off") { localStorage.removeItem("owner"); localStorage.removeItem("umami.disabled"); }
      else localStorage.setItem("owner", "1");
      history.replaceState(null, "", location.pathname + location.hash);
    }
    if (localStorage.getItem("owner")) {
      localStorage.setItem("umami.disabled", "1");
      $(".nav__owner")?.removeAttribute("hidden");
    }
  } catch (e) {}

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

  // Retro decorations drift, rotate and breathe as the page scrolls
  const shapes = $$(".shape");
  if (shapes.length && !reduce) {
    let ticking = false;
    const drift = () => {
      ticking = false;
      const y = scrollY, h = innerHeight;
      shapes.forEach((el, k) => {
        const amp = +el.dataset.y || 0, rot = +el.dataset.r || 0, sc = +el.dataset.s || 0;
        const t = y / h;
        const dy = Math.sin(t * 0.9 + k) * amp;
        const r = t * rot;
        const s = 1 + Math.sin(t * 1.3 + k * 2) * sc;
        el.style.transform = `translate3d(0, ${dy.toFixed(1)}px, 0) rotate(${r.toFixed(1)}deg) scale(${s.toFixed(3)})`;
      });
    };
    addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(drift); } }, { passive: true });
    drift();
  }

  // Retro window loads with page progress; counter shows pixels scrolled
  const load = $(".retro-win__progress b");
  const digits = $(".retro-counter__digits");
  const retro = () => {
    const h = document.documentElement.scrollHeight - innerHeight;
    if (load) load.style.setProperty("--load", Math.max(6, Math.round((h > 0 ? scrollY / h : 0) * 100)) + "%");
    if (digits) digits.textContent = String(Math.round(scrollY)).padStart(6, "0");
  };
  addEventListener("scroll", retro, { passive: true });
  retro();

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
    const templates = $$("template[data-review]", reviews);
    const data = templates.map(t => t.content);
    const pins = $$(".pin", reviews);
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
      const city = templates[n].dataset.city;
      pins.forEach(p => p.setAttribute("aria-pressed", p.dataset.city === city));
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
    // Map pin: open the city's first review, or cycle through that city's reviews
    pins.forEach(p => p.addEventListener("click", () => {
      const idx = templates.map((t, k) => t.dataset.city === p.dataset.city ? k : -1).filter(k => k >= 0);
      const pos = idx.indexOf(i);
      show(pos >= 0 ? idx[(pos + 1) % idx.length] : idx[0]);
    }));
    // Local time in each city
    const clock = () => pins.forEach(p => {
      $(".pin__time", p).textContent = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: p.dataset.tz }).format(new Date());
    });
    clock(); setInterval(clock, 30000);
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
