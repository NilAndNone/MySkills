import { GROUPS, PERSONAS, VERDICT } from "./panel-data.js";

const heroCastList = document.querySelector("#hero-cast-list");
const groupNav = document.querySelector("#group-nav");
const chapterRailList = document.querySelector("#chapter-rail-list");
const chaptersRoot = document.querySelector("#chapters");
const consensusList = document.querySelector("#consensus-list");
const riskList = document.querySelector("#risk-list");
const verdictQuote = document.querySelector("#verdict-quote");

const reader = document.querySelector("#reader");
const readerPanel = document.querySelector(".reader-panel");
const readerContent = document.querySelector("#reader-content");
const readerTitle = document.querySelector("#reader-title");
const readerTagline = document.querySelector("#reader-tagline");
const readerGroupLabel = document.querySelector("#reader-group-label");
const readerSidebarList = document.querySelector("#reader-sidebar-list");
const readerPrev = document.querySelector("#reader-prev");
const readerNext = document.querySelector("#reader-next");

const personasByGroup = GROUPS.map((group) => ({
  ...group,
  personas: PERSONAS.filter((persona) => persona.group === group.slug),
}));

const personaMap = new Map(PERSONAS.map((persona, index) => [persona.slug, { ...persona, index }]));
let activePersonaSlug = PERSONAS[0]?.slug ?? null;
let lastTrigger = null;

function createEl(tag, className, text) {
  const el = document.createElement(tag);
  if (className) {
    el.className = className;
  }
  if (text !== undefined) {
    el.textContent = text;
  }
  return el;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function formatInline(text) {
  return escapeHtml(text).replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderRichText(content) {
  const lines = content.split("\n");
  const parts = [];
  let inList = false;

  const closeList = () => {
    if (inList) {
      parts.push("</ul>");
      inList = false;
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (!line.trim()) {
      closeList();
      continue;
    }

    const headingMatch = line.match(/^\[(.+?)\]$/);
    if (headingMatch) {
      closeList();
      parts.push(`<h3>${escapeHtml(headingMatch[1])}</h3>`);
      continue;
    }

    if (line.startsWith("- ")) {
      if (!inList) {
        parts.push("<ul>");
        inList = true;
      }
      parts.push(`<li>${formatInline(line.slice(2))}</li>`);
      continue;
    }

    closeList();
    parts.push(`<p>${formatInline(line)}</p>`);
  }

  closeList();
  return parts.join("");
}

function buildHeroCast() {
  const fragment = document.createDocumentFragment();
  PERSONAS.forEach((persona, index) => {
    const button = createEl("button", "cast-item");
    button.type = "button";
    button.style.setProperty("--delay", String(index));
    button.dataset.slug = persona.slug;
    button.innerHTML = `
      <span>${persona.slug}</span>
      <strong>${persona.nameZh}</strong>
    `;
    button.addEventListener("click", () => openReader(persona.slug, button));
    fragment.append(button);
  });
  heroCastList.append(fragment);
}

function buildGroupNav() {
  const fragment = document.createDocumentFragment();
  personasByGroup.forEach((group, index) => {
    const button = createEl("button", "group-link");
    button.type = "button";
    button.dataset.target = group.slug;
    button.style.setProperty("--delay", String(index));
    button.innerHTML = `
      <span class="group-index">0${index + 1}</span>
      <span class="group-title">
        <strong>${group.labelZh}</strong>
        <span>${group.labelEn}</span>
      </span>
      <span class="group-summary">${group.summary}</span>
      <span class="group-count">${group.personas.length} 人格</span>
    `;
    button.addEventListener("click", () => {
      document.querySelector(`#chapter-${group.slug}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    fragment.append(button);
  });
  groupNav.append(fragment);
}

function buildChapters() {
  const fragment = document.createDocumentFragment();

  personasByGroup.forEach((group, groupIndex) => {
    const chapter = createEl("article", "chapter reveal");
    chapter.id = `chapter-${group.slug}`;
    chapter.dataset.group = group.slug;
    chapter.dataset.index = `0${groupIndex + 1}`;

    const head = createEl("div", "chapter-head");
    head.innerHTML = `
      <p class="eyebrow">${group.labelEn}</p>
      <div class="chapter-title-row">
        <span class="chapter-index">0${groupIndex + 1}</span>
        <h3 class="chapter-title">${group.labelZh}</h3>
        <span class="chapter-subtitle">${group.labelEn}</span>
      </div>
      <p class="chapter-intro">${group.summary}</p>
    `;

    const personaList = createEl("div", "persona-list");
    group.personas.forEach((persona, personaIndex) => {
      const row = createEl("button", "persona-row");
      row.type = "button";
      row.style.setProperty("--delay", String(personaIndex));
      row.innerHTML = `
        <span class="persona-row-slug">${persona.slug}</span>
        <span class="persona-row-name">
          <strong>${persona.nameZh}</strong>
          <span>${persona.label}</span>
        </span>
        <span class="persona-tagline">${persona.tagline}</span>
      `;
      row.addEventListener("click", () => openReader(persona.slug, row));
      personaList.append(row);
    });

    chapter.append(head, personaList);
    fragment.append(chapter);
  });

  chaptersRoot.append(fragment);
}

function buildRail() {
  const fragment = document.createDocumentFragment();
  personasByGroup.forEach((group, index) => {
    const item = createEl("li");
    item.dataset.target = group.slug;
    item.innerHTML = `
      <span class="group-index">0${index + 1}</span>
      <strong>${group.labelZh}</strong>
    `;
    fragment.append(item);
  });
  chapterRailList.append(fragment);
}

function buildVerdict() {
  VERDICT.consensus.forEach((item) => {
    const li = createEl("li", "", item);
    consensusList.append(li);
  });

  VERDICT.risks.forEach((item) => {
    const li = createEl("li", "", item);
    riskList.append(li);
  });

  verdictQuote.textContent = VERDICT.quote;
}

function buildReaderSidebar(groupSlug, activeSlug) {
  readerSidebarList.innerHTML = "";
  const currentGroup = personasByGroup.find((group) => group.slug === groupSlug);
  if (!currentGroup) {
    return;
  }

  currentGroup.personas.forEach((persona) => {
    const button = createEl("button", "sidebar-item");
    button.type = "button";
    button.dataset.slug = persona.slug;
    if (persona.slug === activeSlug) {
      button.classList.add("is-active");
    }
    button.innerHTML = `
      <span class="sidebar-slug">${persona.slug}</span>
      <span class="sidebar-name">
        ${persona.nameZh}
        <small>${persona.label}</small>
      </span>
    `;
    button.addEventListener("click", () => openReader(persona.slug, button));
    readerSidebarList.append(button);
  });
}

function openReader(slug, trigger) {
  const persona = personaMap.get(slug);
  if (!persona) {
    return;
  }

  activePersonaSlug = slug;
  lastTrigger = trigger ?? lastTrigger;

  readerGroupLabel.textContent = `${personasByGroup.find((group) => group.slug === persona.group)?.labelZh ?? ""} / ${persona.label}`;
  readerTitle.textContent = persona.nameZh;
  readerTagline.textContent = persona.tagline;
  readerContent.innerHTML = renderRichText(persona.content);
  buildReaderSidebar(persona.group, slug);

  const prevIndex = (persona.index - 1 + PERSONAS.length) % PERSONAS.length;
  const nextIndex = (persona.index + 1) % PERSONAS.length;
  readerPrev.dataset.target = PERSONAS[prevIndex].slug;
  readerNext.dataset.target = PERSONAS[nextIndex].slug;

  reader.classList.add("is-open");
  reader.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
  readerPanel.focus();
}

function closeReader() {
  reader.classList.remove("is-open");
  reader.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  if (lastTrigger instanceof HTMLElement) {
    lastTrigger.focus();
  }
}

function setupReaderControls() {
  document.querySelectorAll("[data-close-reader]").forEach((node) => {
    node.addEventListener("click", closeReader);
  });

  readerPrev.addEventListener("click", () => {
    if (readerPrev.dataset.target) {
      openReader(readerPrev.dataset.target, readerPrev);
    }
  });

  readerNext.addEventListener("click", () => {
    if (readerNext.dataset.target) {
      openReader(readerNext.dataset.target, readerNext);
    }
  });

  window.addEventListener("keydown", (event) => {
    if (!reader.classList.contains("is-open")) {
      return;
    }
    if (event.key === "Escape") {
      closeReader();
    }
    if (event.key === "ArrowLeft" && readerPrev.dataset.target) {
      openReader(readerPrev.dataset.target, readerPrev);
    }
    if (event.key === "ArrowRight" && readerNext.dataset.target) {
      openReader(readerNext.dataset.target, readerNext);
    }
  });
}

function setupScrollObservers() {
  const sections = [...document.querySelectorAll(".chapter")];
  const railItems = [...chapterRailList.querySelectorAll("li")];
  const navItems = [...groupNav.querySelectorAll(".group-link")];

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];

      if (!visible) {
        return;
      }

      const activeGroup = visible.target.dataset.group;
      railItems.forEach((item) => {
        item.classList.toggle("is-active", item.dataset.target === activeGroup);
      });
      navItems.forEach((item) => {
        item.classList.toggle("is-active", item.dataset.target === activeGroup);
      });
    },
    {
      rootMargin: "-20% 0px -50% 0px",
      threshold: [0.2, 0.4, 0.6],
    },
  );

  sections.forEach((section) => observer.observe(section));

  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    {
      rootMargin: "0px 0px -12% 0px",
      threshold: 0.12,
    },
  );

  document.querySelectorAll(".reveal").forEach((node) => revealObserver.observe(node));
}

function boot() {
  buildHeroCast();
  buildGroupNav();
  buildChapters();
  buildRail();
  buildVerdict();
  setupReaderControls();
  setupScrollObservers();
  window.requestAnimationFrame(() => {
    document.body.classList.add("is-ready");
  });
}

boot();
