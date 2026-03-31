import * as panelData from "./panel-data.js";

const REPORT_META = panelData.REPORT_META ?? {};
const REPORT_SUMMARY = panelData.REPORT_SUMMARY ?? {};
const GROUPS = panelData.GROUPS ?? [];
const PERSONAS = panelData.PERSONAS ?? [];

const DEFAULT_META = {
  title: "Worldview Panel",
  description: "多个人格对同一个问题的原文档案。",
  question: "",
  preset: "editorial",
};

const DEFAULT_SUMMARY_TITLES = {
  strong_but_risky: "解释力强但不宜照做",
  harsh_but_actionable: "虽然难听但有操作性",
  recommended_lenses: "最该借的人格",
};

const pageMeta = { ...DEFAULT_META, ...REPORT_META };
const personasByGroup = GROUPS.map((group) => ({
  ...group,
  personas: PERSONAS.filter((persona) => persona.group === group.slug),
})).filter((group) => group.personas.length > 0);
const personaMap = new Map(PERSONAS.map((persona) => [persona.slug, persona]));
const activePersonaByGroup = new Map(
  personasByGroup.map((group) => [group.slug, group.personas[0]?.slug || ""]),
);
let activeGroupSlug = personasByGroup[0]?.slug || "";

const nodes = {
  brandName: document.querySelector("#brand-name"),
  heroTitle: document.querySelector("#hero-title"),
  heroLead: document.querySelector("#hero-lead"),
  heroQuestion: document.querySelector("#hero-question"),
  personaCount: document.querySelector("#meta-persona-count"),
  groupCount: document.querySelector("#meta-group-count"),
  heroQuote: document.querySelector("#hero-quote"),
  heroProsecutionTitle: document.querySelector("#hero-prosecution-title"),
  heroProsecutionSummary: document.querySelector("#hero-prosecution-summary"),
  heroDefenseTitle: document.querySelector("#hero-defense-title"),
  heroDefenseSummary: document.querySelector("#hero-defense-summary"),
  heroCenterlineTitle: document.querySelector("#hero-centerline-title"),
  heroCenterlineSummary: document.querySelector("#hero-centerline-summary"),
  heroFrontline: document.querySelector("#hero-frontline"),
  commonGroundList: document.querySelector("#common-ground-list"),
  biggestSplitList: document.querySelector("#biggest-split-list"),
  campSidebar: document.querySelector("#camp-sidebar"),
  campDetailStage: document.querySelector("#camp-detail-stage"),
  endgameSupportTitle: document.querySelector("#endgame-support-title"),
  endgameSupportSummary: document.querySelector("#endgame-support-summary"),
  endgameSupportPersonas: document.querySelector("#endgame-support-personas"),
  endgameOpposeTitle: document.querySelector("#endgame-oppose-title"),
  endgameOpposeSummary: document.querySelector("#endgame-oppose-summary"),
  endgameOpposePersonas: document.querySelector("#endgame-oppose-personas"),
  endgameRedirectTitle: document.querySelector("#endgame-redirect-title"),
  endgameRedirectSummary: document.querySelector("#endgame-redirect-summary"),
  endgameRedirectPersonas: document.querySelector("#endgame-redirect-personas"),
};

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
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function formatInline(text) {
  return escapeHtml(text).replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderRichText(content) {
  const lines = String(content || "").split("\n");
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
      parts.push(`<h5>${escapeHtml(headingMatch[1])}</h5>`);
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

function shorten(text, limit = 72) {
  const compact = String(text || "").replace(/\s+/g, " ").trim();
  if (!compact) {
    return "";
  }
  return compact.length > limit ? `${compact.slice(0, limit).trim()}…` : compact;
}

function fillList(node, items, fallback) {
  node.innerHTML = "";
  const values = Array.isArray(items) && items.length ? items : [fallback];
  values.forEach((item) => {
    const li = createEl("li", "", item);
    node.append(li);
  });
}

function personaStance(persona) {
  return persona.stance || persona.tagline || persona.label || "";
}

function personaConflict(persona) {
  return persona.conflict || "这个人格的关键分歧未单独提炼。";
}

function personaPosition(persona) {
  if (persona.answer_status === "conditional") {
    return "条件回答";
  }
  return persona.position || "";
}

function groupStance(group) {
  return group.stance || group.summary || "这一派没有单独提供总立场说明。";
}

function groupConflict(group) {
  return group.conflict || "这一派没有单独提供关键冲突说明。";
}

function groupSplit(group) {
  return group.split || "这一派没有单独提供内部裂缝说明。";
}

function summaryList(key, fallback) {
  const direct = REPORT_SUMMARY[key];
  if (Array.isArray(direct) && direct.length) {
    return direct;
  }

  const legacyKeyBySummaryKey = {
    strong_but_risky: "support_bucket",
    harsh_but_actionable: "oppose_bucket",
  };
  const legacy = REPORT_SUMMARY[legacyKeyBySummaryKey[key]];
  if (legacy?.summary) {
    return [legacy.summary];
  }
  return [fallback];
}

function recommendedLenses() {
  const direct = REPORT_SUMMARY.recommended_lenses;
  if (Array.isArray(direct) && direct.length) {
    return direct.filter((item) => item?.slug && item?.reason);
  }

  const legacy = REPORT_SUMMARY.redirect_bucket;
  if (legacy?.summary && Array.isArray(legacy.personas)) {
    return legacy.personas
      .filter((slug) => personaMap.has(slug))
      .map((slug) => ({ slug, reason: legacy.summary }));
  }

  return [];
}

function lensLead(lenses) {
  const first = Array.isArray(lenses) ? lenses[0] : null;
  if (!first) {
    return "这一页没有单独指定推荐人格，默认按共同点和分歧点对读。";
  }
  const persona = personaMap.get(first.slug);
  return `${persona?.nameZh || first.slug}：${first.reason}`;
}

function applyReportMeta() {
  const title = pageMeta.title || DEFAULT_META.title;
  const description = pageMeta.description || DEFAULT_META.description;
  const question = pageMeta.question?.trim();
  const condensedTitleLength = title.replace(/[\s，。！？、,.!?]/g, "").length;

  document.body.dataset.preset = pageMeta.preset || DEFAULT_META.preset;
  document.body.classList.toggle("has-long-title", condensedTitleLength > 11);
  document.title = title;

  const descriptionNode = document.querySelector('meta[name="description"]');
  if (descriptionNode) {
    descriptionNode.setAttribute("content", description);
  }

  nodes.brandName.textContent = title;
  nodes.heroTitle.textContent = title;
  nodes.heroLead.textContent = description;
  nodes.heroQuestion.textContent = question
    ? `问题：${question}`
    : "问题：本页未提供问题说明。";
  nodes.personaCount.textContent = String(PERSONAS.length || 0);
  nodes.groupCount.textContent = String(personasByGroup.length || 0);

  const strongButRisky = summaryList(
    "strong_but_risky",
    "这页没有单独提炼“解释力强但不宜照做”的提醒，默认按各派证词自己衡量代价。",
  );
  const harshButActionable = summaryList(
    "harsh_but_actionable",
    "这页没有单独提炼“虽然难听但有操作性”的提醒，默认按各派行动主张对读。",
  );
  const lenses = recommendedLenses();

  nodes.heroProsecutionTitle.textContent = DEFAULT_SUMMARY_TITLES.strong_but_risky;
  nodes.heroProsecutionSummary.textContent = strongButRisky[0];
  nodes.heroDefenseTitle.textContent = DEFAULT_SUMMARY_TITLES.harsh_but_actionable;
  nodes.heroDefenseSummary.textContent = harshButActionable[0];
  nodes.heroCenterlineTitle.textContent = DEFAULT_SUMMARY_TITLES.recommended_lenses;
  nodes.heroCenterlineSummary.textContent = lensLead(lenses);

  const quote = typeof REPORT_META.quote === "string" && REPORT_META.quote.trim()
    ? REPORT_META.quote.trim()
    : "";
  if (quote) {
    nodes.heroQuote.textContent = quote;
    nodes.heroQuote.classList.remove("is-hidden");
  } else {
    nodes.heroQuote.classList.add("is-hidden");
  }
}

function buildHeroFrontline() {
  nodes.heroFrontline.innerHTML = "";
  const fragment = document.createDocumentFragment();

  personasByGroup.forEach((group, index) => {
    const button = createEl("button", "hero-frontline-button");
    button.type = "button";
    button.dataset.group = group.slug;
    button.innerHTML = `
      <span class="hero-frontline-index">${String(index + 1).padStart(2, "0")}</span>
      <div class="hero-frontline-copy">
        <strong>${group.labelZh}</strong>
        <p>${shorten(group.summary || groupStance(group), 32)}</p>
      </div>
      <span class="hero-frontline-count">${group.personas.length}</span>
    `;
    button.addEventListener("click", () => {
      const firstSlug = activePersonaByGroup.get(group.slug) || group.personas[0]?.slug || "";
      selectGroup(group.slug, { scrollIntoView: true });
      if (firstSlug) {
        activePersonaByGroup.set(group.slug, firstSlug);
        renderCampDetail();
      }
    });
    fragment.append(button);
  });

  nodes.heroFrontline.append(fragment);
}

function buildVerdictBand() {
  fillList(
    nodes.commonGroundList,
    REPORT_SUMMARY.common_ground,
    "这一页没有单独提供最大共识，默认按各派证词阅读。",
  );
  fillList(
    nodes.biggestSplitList,
    REPORT_SUMMARY.biggest_split,
    "这一页没有单独提供最大分歧，默认按各派对照阅读。",
  );
}

function personaChipMarkup(slug, toneClass) {
  const persona = personaMap.get(slug);
  if (!persona) {
    return "";
  }
  return `
    <button class="persona-chip ${toneClass}" type="button" data-slug="${persona.slug}">
      ${persona.nameZh}
    </button>
  `;
}

function buildEndgame() {
  const strongButRisky = summaryList(
    "strong_but_risky",
    "暂无单独提炼，默认按各派最强解释与代价一起阅读。",
  );
  const harshButActionable = summaryList(
    "harsh_but_actionable",
    "暂无单独提炼，默认按各派行动主张中最硬的部分阅读。",
  );
  const lenses = recommendedLenses();

  nodes.endgameSupportTitle.textContent = DEFAULT_SUMMARY_TITLES.strong_but_risky;
  nodes.endgameSupportSummary.textContent = strongButRisky[0];
  nodes.endgameOpposeTitle.textContent = DEFAULT_SUMMARY_TITLES.harsh_but_actionable;
  nodes.endgameOpposeSummary.textContent = harshButActionable[0];
  nodes.endgameRedirectTitle.textContent = DEFAULT_SUMMARY_TITLES.recommended_lenses;
  nodes.endgameRedirectSummary.textContent = lensLead(lenses);

  const textTargets = [
    [nodes.endgameSupportPersonas, strongButRisky.slice(1), "persona-chip--red"],
    [nodes.endgameOpposePersonas, harshButActionable.slice(1), "persona-chip--blue"],
  ];

  textTargets.forEach(([target, items, toneClass]) => {
    target.innerHTML = "";
    if (!Array.isArray(items) || !items.length) {
      target.textContent = "暂无更多补充";
      target.classList.add("is-empty");
      return;
    }

    target.classList.remove("is-empty");
    target.innerHTML = items.map((item) => `<span class="persona-chip ${toneClass}">${item}</span>`).join("");
  });

  nodes.endgameRedirectPersonas.innerHTML = "";
  if (!lenses.length) {
    nodes.endgameRedirectPersonas.textContent = "暂无明确推荐人格";
    nodes.endgameRedirectPersonas.classList.add("is-empty");
    return;
  }

  nodes.endgameRedirectPersonas.classList.remove("is-empty");
  nodes.endgameRedirectPersonas.innerHTML = lenses.map((lens) => {
    const persona = personaMap.get(lens.slug);
    const label = persona?.nameZh || lens.slug;
    return `
      <button class="persona-chip persona-chip--neutral" type="button" data-slug="${lens.slug}" title="${lens.reason}">
        ${label}
      </button>
    `;
  }).join("");
  nodes.endgameRedirectPersonas.querySelectorAll(".persona-chip").forEach((button) => {
    button.addEventListener("click", () => jumpToPersona(button.dataset.slug));
  });
}

function renderCampSidebar() {
  nodes.campSidebar.innerHTML = "";
  const header = createEl("div", "camp-sidebar-header");
  header.innerHTML = `
    <p class="eyebrow">Camp Index</p>
    <h3>五派总览</h3>
    <p>左侧固定阵线，右侧只展开当前战区。</p>
  `;
  nodes.campSidebar.append(header);

  personasByGroup.forEach((group, index) => {
    const button = createEl("button", "camp-nav");
    button.type = "button";
    button.dataset.group = group.slug;
    if (group.slug === activeGroupSlug) {
      button.classList.add("is-active");
    }
    button.innerHTML = `
      <span class="camp-nav-index">${String(index + 1).padStart(2, "0")}</span>
      <div class="camp-nav-copy">
        <strong>${group.labelZh}</strong>
        <p>${shorten(group.summary || groupStance(group), 48)}</p>
      </div>
      <span class="camp-nav-count">${group.personas.length}</span>
    `;
    button.addEventListener("click", () => selectGroup(group.slug));
    nodes.campSidebar.append(button);
  });
}

function personaCardMarkup(persona, isOpen) {
  const positionLabel = personaPosition(persona);
  const statusNote = persona.answer_status_note
    ? `
          <div class="brief-block">
            <span>条件说明</span>
            <p>${persona.answer_status_note}</p>
          </div>
      `
    : "";
  return `
    <article class="persona-card ${isOpen ? "is-open" : ""}" data-group="${persona.group}" data-slug="${persona.slug}">
      <button class="persona-toggle" type="button" data-slug="${persona.slug}" aria-expanded="${String(isOpen)}">
        <div class="persona-topline">
          ${positionLabel ? `<span class="position-pill">${positionLabel}</span>` : ""}
          <span class="persona-slug">${persona.slug}</span>
        </div>
        <div class="persona-heading">
          <h4>${persona.nameZh}</h4>
          <p>${persona.label}</p>
        </div>
        <div class="persona-briefs">
          <div class="brief-block">
            <span>立场一句话</span>
            <p>${personaStance(persona)}</p>
          </div>
          <div class="brief-block">
            <span>关键分歧一句话</span>
            <p>${personaConflict(persona)}</p>
          </div>
          ${statusNote}
        </div>
      </button>
      <div class="persona-detail" ${isOpen ? "" : "hidden"}>
        <div class="persona-detail-inner">${renderRichText(persona.content || "")}</div>
      </div>
    </article>
  `;
}

function renderCampDetail() {
  const group = personasByGroup.find((item) => item.slug === activeGroupSlug);
  if (!group) {
    nodes.campDetailStage.innerHTML = "";
    return;
  }

  let activePersonaSlug = activePersonaByGroup.get(group.slug);
  if (!activePersonaSlug) {
    activePersonaSlug = group.personas[0]?.slug || "";
    activePersonaByGroup.set(group.slug, activePersonaSlug);
  }

  nodes.campDetailStage.innerHTML = `
    <article class="camp-detail" data-group="${group.slug}">
      <header class="camp-detail-header">
        <div class="camp-detail-copy">
          <p class="eyebrow">${group.labelEn}</p>
          <h3>${group.labelZh}</h3>
          <p class="camp-detail-summary">${group.summary}</p>
        </div>
        <div class="camp-evidence-grid">
          <article class="evidence-card">
            <span>这一派总立场</span>
            <p>${groupStance(group)}</p>
          </article>
          <article class="evidence-card">
            <span>最在意的冲突</span>
            <p>${groupConflict(group)}</p>
          </article>
          <article class="evidence-card">
            <span>内部裂缝</span>
            <p>${groupSplit(group)}</p>
          </article>
        </div>
      </header>

      <div class="witness-bar">
        <div>
          <p class="eyebrow">Witness Files</p>
          <h4>${group.personas.length} 份证词</h4>
        </div>
        <p class="witness-note">同一时间只展开一份详细证词。</p>
      </div>

      <div class="persona-list">
        ${group.personas.map((persona) => personaCardMarkup(persona, persona.slug === activePersonaSlug)).join("")}
      </div>
    </article>
  `;

  nodes.campDetailStage.querySelectorAll(".persona-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      const slug = button.dataset.slug || "";
      if (!slug || activePersonaByGroup.get(group.slug) === slug) {
        return;
      }
      activePersonaByGroup.set(group.slug, slug);
      renderCampDetail();
    });
  });
}

function selectGroup(groupSlug, options = {}) {
  if (!groupSlug || groupSlug === activeGroupSlug && !options.force) {
    if (options.scrollIntoView) {
      document.querySelector("#camps")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    return;
  }

  activeGroupSlug = groupSlug;
  renderCampSidebar();
  renderCampDetail();

  if (options.scrollIntoView) {
    document.querySelector("#camps")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function jumpToPersona(slug) {
  const persona = personaMap.get(slug);
  if (!persona) {
    return;
  }
  activeGroupSlug = persona.group;
  activePersonaByGroup.set(persona.group, persona.slug);
  renderCampSidebar();
  renderCampDetail();
  document.querySelector("#camps")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function boot() {
  applyReportMeta();
  buildHeroFrontline();
  buildVerdictBand();
  renderCampSidebar();
  renderCampDetail();
  buildEndgame();
  window.requestAnimationFrame(() => {
    document.body.classList.add("is-ready");
  });
}

boot();
