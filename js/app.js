import { createPuzzleManager } from "./puzzles.js";

const storyEl = document.getElementById("story");
const choicesEl = document.getElementById("choices");
const resetBtn = document.getElementById("resetBtn");
const statusEl = document.getElementById("status");
const sceneImageEl = document.getElementById("sceneImage");
const sceneDateEl = document.getElementById("sceneDate");
const scenePlaceEl = document.getElementById("scenePlace");

const agentAvatarThumbEl = document.getElementById("agentAvatarThumb");
const agentModalEl = document.getElementById("agentModal");
const agentModalBackdropEl = document.getElementById("agentModalBackdrop");
const agentModalCloseEl = document.getElementById("agentModalClose");
const agentModalAvatarEl = document.getElementById("agentModalAvatar");
const agentModalNameEl = document.getElementById("agentModalName");
const agentModalTagEl = document.getElementById("agentModalTag");
const agentModalQualitiesEl = document.getElementById("agentModalQualities");
const agentModalItemEl = document.getElementById("agentModalItem");
const agentAvatarBtnEl = document.getElementById("agentAvatarBtn");
const footerAgentEl = document.getElementById("footerAgent");
const landingScreenEl = document.getElementById("landingScreen");
const landingTitleEl = document.getElementById("landingTitle");
const startMissionBtnEl = document.getElementById("startMissionBtn");
const backBtnEl = document.getElementById("backBtn");
const puzzleTriggerEl = document.getElementById("puzzleTrigger");
const puzzleTriggerTextEl = document.getElementById("puzzleTriggerText");
const puzzleAcceptBtnEl = document.getElementById("puzzleAcceptBtn");

let scenes = {};
let agents = {};
let puzzles = {};
let currentAgent = null;
let typewriterTimers = [];
let startSceneId = "intro";
let missionStarted = false;
let sceneHistory = [];
let initialSceneId = "intro";
let dataReady = false;
let pendingStart = false;
let pendingPuzzle = null;

const gameConfig = {
  showBackButton: true,
  showSceneIdInHeader: true,
  showLanding: false
};

const puzzleManager = createPuzzleManager({
  modal: document.getElementById("puzzleModal"),
  backdrop: document.getElementById("puzzleModalBackdrop"),
  closeBtn: document.getElementById("puzzleModalClose"),
  title: document.getElementById("puzzleTitle"),
  hint: document.getElementById("puzzleHint"),
  description: document.getElementById("puzzleDescription"),
  content: document.getElementById("puzzleContent"),
  message: document.getElementById("puzzleMessage"),
  checkBtn: document.getElementById("puzzleCheckBtn"),
  resetBtn: document.getElementById("puzzleResetBtn"),
  continueBtn: document.getElementById("puzzleContinueBtn")
});

function agentNameValue() {
  return currentAgent?.name || "Agente";
}

function applyLandingVisibility() {
  if (!gameConfig.showLanding) {
    landingScreenEl.style.display = "none";
  } else if (!missionStarted) {
    landingScreenEl.style.display = "flex";
  }
}

function injectAgentName(text) {
  if (typeof text !== "string") return text;
  return text.replaceAll("{{agentName}}", agentNameValue());
}

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`No se pudo cargar ${path}`);
  }
  return response.json();
}

function formatDatetime(raw) {
  if (!raw) return "—";
  const [datePart, timePart] = raw.split(" ");
  if (!datePart || !timePart) return raw;
  const [y, m, d] = datePart.split("-");
  if (!y || !m || !d) return raw;
  return `${d}/${m} · ${timePart}`;
}

function clearTypewriter() {
  typewriterTimers.forEach(timer => clearTimeout(timer));
  typewriterTimers = [];
}

function typewriter(el, text, speed = 22) {
  return new Promise(resolve => {
    const safeText = text || "—";
    let index = 0;
    el.classList.remove("is-static");
    const write = () => {
      const partial = safeText.slice(0, index);
      el.textContent = partial;
      index += 1;
      if (index <= safeText.length) {
        const t = setTimeout(write, speed);
        typewriterTimers.push(t);
      } else {
        el.textContent = safeText;
        el.classList.add("is-static");
        resolve();
      }
    };
    write();
  });
}

function getCurrentAgent() {
  const params = new URLSearchParams(window.location.search);
  const idFromUrl = params.get("agent");
  if (idFromUrl && agents[idFromUrl]) {
    return agents[idFromUrl];
  }
  if (agents.generic) return agents.generic;
  const [firstAgent] = Object.values(agents);
  return firstAgent || null;
}

function renderAgent(agent) {
  if (!agent) return;
  agentModalNameEl.textContent = agent.name || "Agente desconocido";
  agentModalTagEl.textContent = agent.tag || "";
  agentModalQualitiesEl.innerHTML = "";
  if (Array.isArray(agent.qualities) && agent.qualities.length) {
    agent.qualities.forEach(quality => {
      const span = document.createElement("span");
      span.textContent = quality;
      agentModalQualitiesEl.appendChild(span);
    });
  }
  agentModalItemEl.textContent = agent.specialItem
    ? "Objeto especial: " + agent.specialItem
    : "";
  if (agent.avatar) {
    agentAvatarThumbEl.src = agent.avatar;
    agentModalAvatarEl.src = agent.avatar;
  } else {
    agentAvatarThumbEl.src = "";
    agentModalAvatarEl.src = "";
  }
  footerAgentEl.textContent =
    "OPERACIÓN PORTAL 27 · Agente: " + (agent.name || "________");
}

function renderScene(id) {
  const scene = scenes[id];
  if (!scene) {
    storyEl.textContent = "No se encuentra la escena: " + id;
    choicesEl.innerHTML = "";
    puzzleManager.hide();
    return;
  }

  const textLines = Array.isArray(scene.textLines)
    ? scene.textLines
    : Array.isArray(scene.text)
      ? scene.text
      : typeof scene.text === "string"
        ? [scene.text]
        : [];

  const linesToRender = Array.isArray(textLines) ? [...textLines] : [];
  if (
    linesToRender.length &&
    typeof linesToRender[0] === "string" &&
    linesToRender[0].trim().startsWith("[") &&
    linesToRender[0].includes("]")
  ) {
    linesToRender.shift();
  }

  storyEl.innerHTML = "";
  if (linesToRender.length) {
    linesToRender.forEach(line => {
      const div = document.createElement("div");
      div.textContent = injectAgentName(line || "");
      storyEl.appendChild(div);
    });
  } else {
    storyEl.textContent = "";
  }
  choicesEl.innerHTML = "";
  statusEl.textContent = `Misión: Portal_27 · Escena: ${id}`;
  if (!gameConfig.showSceneIdInHeader) {
    statusEl.textContent = "Misión: Portal_27.ACTIVA";
  }

  const imgSrc =
    scene.image === null ? null : scene.image || `img/scenes/${id}.png`;
  if (imgSrc) {
    sceneImageEl.src = imgSrc;
    sceneImageEl.style.visibility = "visible";
  } else {
    sceneImageEl.src = "";
    sceneImageEl.style.visibility = "hidden";
  }

  pendingPuzzle = null;
  puzzleManager.hide();
  puzzleTriggerEl.style.display = "none";

  if (scene.puzzle) {
    const puzzleConfig = scene.puzzle;
    const fallback = puzzleConfig.id ? puzzles[puzzleConfig.id] : null;
    const mergedConfig = fallback
      ? {
          ...fallback,
          ...puzzleConfig,
          data: { ...(fallback.data || {}), ...(puzzleConfig.data || {}) }
        }
      : puzzleConfig;
    pendingPuzzle = { sceneId: id, config: mergedConfig };
    puzzleTriggerEl.style.display = "flex";
    puzzleTriggerTextEl.textContent =
      mergedConfig.title || "Reto activo: resuélvelo para continuar";
  }

  (scene.choices || []).forEach(choice => {
    const btn = document.createElement("button");
    btn.className = "choice-btn" + (scene.ending ? " ending" : "");
    btn.textContent = injectAgentName(choice.text);
    btn.addEventListener("click", () => {
      sceneHistory.push(id);
      renderScene(choice.next);
    });
    choicesEl.appendChild(btn);
  });

  clearTypewriter();
  const displayDate = formatDatetime(scene.datetime);
  typewriter(sceneDateEl, displayDate || "—");
  typewriter(scenePlaceEl, scene.place || "—");

  const params = new URLSearchParams(window.location.search);
  params.set("scene", id);
  const newUrl = `${window.location.pathname}?${params.toString()}`;
  window.history.replaceState({}, "", newUrl);

  updateBackButtonState();
}

async function init() {
  try {
    const [agentsData, storyData, puzzlesData] = await Promise.all([
      loadJson("data/agents.json"),
      loadJson("data/story.json"),
      loadJson("data/puzzles.json")
    ]);
    agents = agentsData.agents || agentsData || {};
    scenes = storyData.scenes || {};
    puzzles = puzzlesData.puzzles || {};
    startSceneId = storyData.meta?.start || "intro";
    const urlScene = new URLSearchParams(window.location.search).get("scene");
    initialSceneId = urlScene && scenes[urlScene] ? urlScene : startSceneId;
    currentAgent = getCurrentAgent();
    renderAgent(currentAgent);
    landingTitleEl.textContent = `${agentNameValue()} & Ona · Operación Portal 27`;
    if (!gameConfig.showBackButton) {
      backBtnEl.style.display = "none";
    }
    applyLandingVisibility();
    dataReady = true;
    if (!gameConfig.showLanding) {
      startMission();
    } else if (pendingStart && gameConfig.showLanding) {
      pendingStart = false;
      startMission();
    }
  } catch (error) {
    storyEl.textContent = "No se pudo cargar la historia. Revisa los ficheros JSON.";
    choicesEl.innerHTML = "";
    console.error(error);
  }
}

function startMission() {
  if (!dataReady) {
    pendingStart = true;
    return;
  }
  missionStarted = true;
  applyLandingVisibility();
  sceneHistory = [];
  renderScene(initialSceneId);
}

resetBtn.addEventListener("click", () => {
  sceneHistory = [];
  renderScene(startSceneId);
});
backBtnEl.addEventListener("click", () => {
  if (!gameConfig.showBackButton) return;
  const previous = sceneHistory.pop();
  if (previous) {
    renderScene(previous);
  }
});

function openAgentModal() {
  agentModalEl.classList.add("is-open");
  agentModalEl.setAttribute("aria-hidden", "false");
}

function closeAgentModal() {
  agentModalEl.classList.remove("is-open");
  agentModalEl.setAttribute("aria-hidden", "true");
}

agentAvatarBtnEl.addEventListener("click", openAgentModal);
agentModalCloseEl.addEventListener("click", closeAgentModal);
agentModalBackdropEl.addEventListener("click", closeAgentModal);
startMissionBtnEl.addEventListener("click", startMission);
puzzleAcceptBtnEl.addEventListener("click", () => {
  if (!pendingPuzzle) return;
  const { sceneId, config } = pendingPuzzle;
  puzzleManager.render(sceneId, config, nextScene => {
    sceneHistory.push(sceneId);
    renderScene(nextScene);
  });
});

document.addEventListener("DOMContentLoaded", init);

function updateBackButtonState() {
  if (!gameConfig.showBackButton) return;
  if (sceneHistory.length === 0) {
    backBtnEl.classList.add("is-disabled");
    backBtnEl.setAttribute("disabled", "disabled");
  } else {
    backBtnEl.classList.remove("is-disabled");
    backBtnEl.removeAttribute("disabled");
  }
}
