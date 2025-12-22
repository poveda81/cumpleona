import { createPuzzleManager } from "./puzzles.js";
import GameAnalytics from "./analytics.js";

const analytics = new GameAnalytics();

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
const landingAgentImageEl = document.getElementById("landingAgentImage");
const startMissionBtnEl = document.getElementById("startMissionBtn");
const backBtnEl = document.getElementById("backBtn");
const puzzleTriggerEl = document.getElementById("puzzleTrigger");
const puzzleTriggerTextEl = document.getElementById("puzzleTriggerText");
const puzzleAcceptBtnEl = document.getElementById("puzzleAcceptBtn");
const resetProgressBtnEl = document.getElementById("resetProgressBtn");
const switchAgentBtnEl = document.getElementById("switchAgentBtn");
const agentSelectorModalEl = document.getElementById("agentSelectorModal");
const agentSelectorBackdropEl = document.getElementById("agentSelectorBackdrop");
const agentSelectorCloseEl = document.getElementById("agentSelectorClose");
const agentSelectorGridEl = document.getElementById("agentSelectorGrid");
const agentModalMessageEl = document.getElementById("agentModalMessage");

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
  showBackButton: false,
  showSceneIdInHeader: false,
  showLanding: true,
  requireAllEndingsToSwitchAgent: true // Cambia a false para testear el selector de agentes sin restricciones
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

let friendAgents = {
  friend1: null,
  friend2: null,
  friend3: null,
  friend4: null,
  friend5: null,
  friend6: null
};

// Sistema de tracking de finales
const ENDINGS_STORAGE_PREFIX = "portal27_endings_";

function getAgentStorageKey() {
  if (!currentAgent) return null;
  const params = new URLSearchParams(window.location.search);
  const agentId = params.get("agent") || "generic";
  return `${ENDINGS_STORAGE_PREFIX}${agentId}`;
}

function getAllEndings() {
  const endings = [];
  for (const [sceneId, scene] of Object.entries(scenes)) {
    if (scene.ending === true) {
      endings.push(sceneId);
    }
  }
  return endings;
}

function getFoundEndings() {
  const storageKey = getAgentStorageKey();
  if (!storageKey) return [];

  try {
    const stored = localStorage.getItem(storageKey);
    return stored ? JSON.parse(stored) : [];
  } catch (e) {
    return [];
  }
}

function addFoundEnding(sceneId) {
  const storageKey = getAgentStorageKey();
  if (!storageKey) return;

  const found = getFoundEndings();
  if (!found.includes(sceneId)) {
    found.push(sceneId);
    try {
      localStorage.setItem(storageKey, JSON.stringify(found));
      console.log(`Final encontrado: ${sceneId}. Total: ${found.length}`);
    } catch (e) {
      console.error("No se pudo guardar el progreso de finales", e);
    }
  }
}

function getEndingsProgress() {
  const allEndings = getAllEndings();
  const foundEndings = getFoundEndings();
  return {
    found: foundEndings.length,
    total: allEndings.length,
    percentage: allEndings.length > 0 ? Math.round((foundEndings.length / allEndings.length) * 100) : 0
  };
}

function resetEndingsProgress() {
  const storageKey = getAgentStorageKey();
  if (storageKey) {
    localStorage.removeItem(storageKey);
    console.log("Progreso de finales reseteado para este agente");
    if (currentAgent) {
      renderAgent(currentAgent);
    }
  }
}

// Función de debug (puedes llamarla desde la consola)
window.debugEndings = function() {
  console.log("=== DEBUG FINALES ===");
  console.log("Agente actual:", currentAgent?.name);
  console.log("Storage key:", getAgentStorageKey());
  console.log("Todos los finales:", getAllEndings());
  console.log("Finales encontrados:", getFoundEndings());
  console.log("Progreso:", getEndingsProgress());
};

window.resetProgress = resetEndingsProgress;

function agentNameValue() {
  return currentAgent?.name || "Agente";
}

function applyLandingVisibility() {
  if (!gameConfig.showLanding || missionStarted) {
    landingScreenEl.style.display = "none";
  } else {
    landingScreenEl.style.display = "flex";
  }
}

function getRandomFriends() {
  // Obtener todos los agentes excepto el actual
  const allAgentIds = Object.keys(agents);
  const availableAgents = allAgentIds.filter(id => {
    const agent = agents[id];
    return agent && agent !== currentAgent;
  });

  // Seleccionar hasta 6 amigos aleatorios
  const shuffled = availableAgents.sort(() => Math.random() - 0.5);
  friendAgents.friend1 = agents[shuffled[0]] || null;
  friendAgents.friend2 = agents[shuffled[1]] || null;
  friendAgents.friend3 = agents[shuffled[2]] || null;
  friendAgents.friend4 = agents[shuffled[3]] || null;
  friendAgents.friend5 = agents[shuffled[4]] || null;
  friendAgents.friend6 = agents[shuffled[5]] || null;
}

function injectAgentData(text) {
  if (typeof text !== "string") return text;

  let result = text;

  // Reemplazar datos del agente principal
  if (currentAgent) {
    result = result.replaceAll("{{agent.name}}", currentAgent.name || "Agente");
    result = result.replaceAll("{{agent.tag}}", currentAgent.tag || "");
    result = result.replaceAll("{{agent.specialItem}}", currentAgent.specialItem || "objeto especial");
    result = result.replaceAll("{{agent.fear}}", currentAgent.fear || "lo desconocido");
    result = result.replaceAll("{{agent.luckyNumber}}", currentAgent.luckyNumber || "7");

    // Reemplazar qualities por índice
    if (Array.isArray(currentAgent.qualities)) {
      currentAgent.qualities.forEach((quality, index) => {
        result = result.replaceAll(`{{agent.qualities[${index}]}}`, quality);
      });
    }
  }

  // Reemplazar datos de friend1
  if (friendAgents.friend1) {
    result = result.replaceAll("{{friend1.name}}", friendAgents.friend1.name || "Amiga");
    result = result.replaceAll("{{friend1.tag}}", friendAgents.friend1.tag || "");

    if (Array.isArray(friendAgents.friend1.qualities)) {
      friendAgents.friend1.qualities.forEach((quality, index) => {
        result = result.replaceAll(`{{friend1.qualities[${index}]}}`, quality);
      });
    }
  }

  // Reemplazar datos de friend2
  if (friendAgents.friend2) {
    result = result.replaceAll("{{friend2.name}}", friendAgents.friend2.name || "Amiga");
    result = result.replaceAll("{{friend2.tag}}", friendAgents.friend2.tag || "");

    if (Array.isArray(friendAgents.friend2.qualities)) {
      friendAgents.friend2.qualities.forEach((quality, index) => {
        result = result.replaceAll(`{{friend2.qualities[${index}]}}`, quality);
      });
    }
  }

  // Reemplazar datos de friend3
  if (friendAgents.friend3) {
    result = result.replaceAll("{{friend3.name}}", friendAgents.friend3.name || "Amiga");
    result = result.replaceAll("{{friend3.tag}}", friendAgents.friend3.tag || "");

    if (Array.isArray(friendAgents.friend3.qualities)) {
      friendAgents.friend3.qualities.forEach((quality, index) => {
        result = result.replaceAll(`{{friend3.qualities[${index}]}}`, quality);
      });
    }
  }

  // Reemplazar datos de friend4
  if (friendAgents.friend4) {
    result = result.replaceAll("{{friend4.name}}", friendAgents.friend4.name || "Amiga");
    result = result.replaceAll("{{friend4.tag}}", friendAgents.friend4.tag || "");

    if (Array.isArray(friendAgents.friend4.qualities)) {
      friendAgents.friend4.qualities.forEach((quality, index) => {
        result = result.replaceAll(`{{friend4.qualities[${index}]}}`, quality);
      });
    }
  }

  // Reemplazar datos de friend5
  if (friendAgents.friend5) {
    result = result.replaceAll("{{friend5.name}}", friendAgents.friend5.name || "Amiga");
    result = result.replaceAll("{{friend5.tag}}", friendAgents.friend5.tag || "");

    if (Array.isArray(friendAgents.friend5.qualities)) {
      friendAgents.friend5.qualities.forEach((quality, index) => {
        result = result.replaceAll(`{{friend5.qualities[${index}]}}`, quality);
      });
    }
  }

  // Reemplazar datos de friend6
  if (friendAgents.friend6) {
    result = result.replaceAll("{{friend6.name}}", friendAgents.friend6.name || "Amiga");
    result = result.replaceAll("{{friend6.tag}}", friendAgents.friend6.tag || "");

    if (Array.isArray(friendAgents.friend6.qualities)) {
      friendAgents.friend6.qualities.forEach((quality, index) => {
        result = result.replaceAll(`{{friend6.qualities[${index}]}}`, quality);
      });
    }
  }

  // Mantener compatibilidad con el formato antiguo
  result = result.replaceAll("{{agentName}}", agentNameValue());

  return result;
}

// Alias para mantener compatibilidad
function injectAgentName(text) {
  return injectAgentData(text);
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

function getCurrentAgentId() {
  const params = new URLSearchParams(window.location.search);
  const idFromUrl = params.get("agent");
  if (idFromUrl && agents[idFromUrl]) {
    return idFromUrl;
  }
  if (agents.generic) return "generic";
  const [firstAgentId] = Object.keys(agents);
  return firstAgentId || null;
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

  // Mostrar progreso de finales
  const progress = getEndingsProgress();
  const progressContainer = document.getElementById("agentEndingsProgress");
  if (progressContainer) {
    progressContainer.innerHTML = `
      <div class="endings-progress">
        <div class="endings-progress__title">Finales descubiertos</div>
        <div class="endings-progress__bar">
          <div class="endings-progress__fill" style="width: ${progress.percentage}%"></div>
        </div>
        <div class="endings-progress__text">${progress.found} de ${progress.total} finales encontrados</div>
      </div>
    `;
  }

  // El botón siempre está habilitado, la validación se hace al hacer click
  const allEndingsFound = progress.found === progress.total && progress.total > 0;
  if (switchAgentBtnEl) {
    if (gameConfig.requireAllEndingsToSwitchAgent && !allEndingsFound) {
      switchAgentBtnEl.title = `Encuentra todos los finales (${progress.found}/${progress.total}) para desbloquear`;
    } else if (allEndingsFound) {
      switchAgentBtnEl.title = "¡Todos los finales encontrados! Cambia de agente";
    } else {
      switchAgentBtnEl.title = "Cambiar de agente";
    }
  }

  if (agent.avatar) {
    agentAvatarThumbEl.src = agent.avatar;
    agentModalAvatarEl.src = agent.avatar;
  } else {
    agentAvatarThumbEl.src = "";
    agentModalAvatarEl.src = "";
  }

  const agentModalFullbodyEl = document.getElementById("agentModalFullbody");
  if (agentModalFullbodyEl) {
    agentModalFullbodyEl.src = agent.fullbody || "";
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

  // Track scene view
  analytics.trackSceneView(id, scene);

  // Si la escena es un final, registrarla
  if (scene.ending === true) {
    addFoundEnding(id);
    analytics.trackEnding(id);
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
    scene.image === null ? null : scene.image || `img/scenarios/${id}.png`;
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
      analytics.trackChoice(id, choice.text, choice.next);
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

    // Asignar amigos aleatorios
    getRandomFriends();

    renderAgent(currentAgent);
    landingTitleEl.textContent = `${agentNameValue()} & Ona · Operación Portal 27`;

    // Configurar imagen del agente en la landing
    if (currentAgent) {
      const agentId = getCurrentAgentId();
      landingAgentImageEl.src = `img/agents/${agentId}_fullbody.png`;
      landingAgentImageEl.alt = currentAgent.name;
    }

    // Track session start
    analytics.trackSessionStart(currentAgent);

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
  analytics.trackMissionStart();
  renderScene(initialSceneId);
}

resetBtn.addEventListener("click", () => {
  analytics.trackReset();
  sceneHistory = [];
  renderScene(startSceneId);
});
backBtnEl.addEventListener("click", () => {
  if (!gameConfig.showBackButton) return;
  const previous = sceneHistory.pop();
  if (previous) {
    const currentSceneId = new URLSearchParams(window.location.search).get("scene");
    analytics.trackBackButton(currentSceneId, previous);
    renderScene(previous);
  }
});

function showAgentMessage(message, type = "info", actions = null) {
  if (!agentModalMessageEl) return;

  agentModalMessageEl.className = `agent-modal__message agent-modal__message--${type}`;

  if (actions) {
    // Mensaje con botones de acción
    const actionsHtml = actions.map(action =>
      `<button class="agent-modal__message-btn ${action.danger ? 'agent-modal__message-btn--danger' : ''}" data-action="${action.id}">${action.text}</button>`
    ).join('');

    agentModalMessageEl.innerHTML = `
      <div>${message}</div>
      <div class="agent-modal__message-actions">${actionsHtml}</div>
    `;

    // Añadir event listeners a los botones
    actions.forEach(action => {
      const btn = agentModalMessageEl.querySelector(`[data-action="${action.id}"]`);
      if (btn) {
        btn.addEventListener("click", () => {
          action.callback();
        });
      }
    });
  } else {
    // Mensaje simple
    agentModalMessageEl.textContent = message;
  }

  agentModalMessageEl.style.display = "block";
}

function hideAgentMessage() {
  if (agentModalMessageEl) {
    agentModalMessageEl.style.display = "none";
    agentModalMessageEl.innerHTML = "";
  }
}

function openAgentModal() {
  hideAgentMessage(); // Limpiar mensajes previos
  renderAgent(currentAgent); // Actualizar el progreso cada vez que se abre
  agentModalEl.classList.add("is-open");
  agentModalEl.setAttribute("aria-hidden", "false");
}

function closeAgentModal() {
  hideAgentMessage();
  agentModalEl.classList.remove("is-open");
  agentModalEl.setAttribute("aria-hidden", "true");
}

function openAgentSelector() {
  const progress = getEndingsProgress();
  const allEndingsFound = progress.found === progress.total && progress.total > 0;

  // Validar si se requieren todos los finales y no los tiene
  if (gameConfig.requireAllEndingsToSwitchAgent && !allEndingsFound) {
    showAgentMessage(
      `Debes encontrar todos los finales para cambiar de agente.\n\nProgreso actual: ${progress.found}/${progress.total} finales encontrados.`,
      "warning"
    );
    return;
  }

  // Renderizar grid de agentes
  agentSelectorGridEl.innerHTML = "";
  const currentAgentId = new URLSearchParams(window.location.search).get("agent");

  Object.entries(agents).forEach(([agentId, agent]) => {
    const card = document.createElement("div");
    card.className = "agent-card";
    if (agentId === currentAgentId) {
      card.classList.add("is-current");
    }

    const avatar = document.createElement("img");
    avatar.className = "agent-card__avatar";
    avatar.src = agent.avatar || "";
    avatar.alt = agent.name;

    const name = document.createElement("div");
    name.className = "agent-card__name";
    name.textContent = agent.name;

    const tag = document.createElement("div");
    tag.className = "agent-card__tag";
    tag.textContent = agent.tag;

    card.appendChild(avatar);
    card.appendChild(name);
    card.appendChild(tag);

    card.addEventListener("click", () => {
      switchToAgent(agentId);
    });

    agentSelectorGridEl.appendChild(card);
  });

  agentSelectorModalEl.classList.add("is-open");
  agentSelectorModalEl.setAttribute("aria-hidden", "false");
}

function closeAgentSelector() {
  agentSelectorModalEl.classList.remove("is-open");
  agentSelectorModalEl.setAttribute("aria-hidden", "true");
}

function switchToAgent(agentId) {
  const currentAgentId = getCurrentAgentId();
  analytics.trackAgentSwitch(currentAgentId, agentId);
  const params = new URLSearchParams(window.location.search);
  params.set("agent", agentId);
  params.delete("scene"); // Reiniciar desde el inicio
  window.location.search = params.toString();
}

function handleResetProgress() {
  const progress = getEndingsProgress();

  if (progress.found === 0) {
    showAgentMessage("No hay progreso para reiniciar.", "info");
    return;
  }

  const message = `¿Estás seguro/a de que quieres reiniciar tu progreso?\n\nSe borrarán los ${progress.found} finales encontrados.\n\nEsta acción no se puede deshacer.`;

  showAgentMessage(message, "confirm", [
    {
      id: "cancel",
      text: "Cancelar",
      danger: false,
      callback: () => {
        hideAgentMessage();
      }
    },
    {
      id: "confirm",
      text: "Sí, reiniciar",
      danger: true,
      callback: () => {
        resetEndingsProgress();
        showAgentMessage("✓ Progreso reiniciado correctamente.", "info");
        setTimeout(() => {
          hideAgentMessage();
        }, 3000);
      }
    }
  ]);
}

agentAvatarBtnEl.addEventListener("click", openAgentModal);
agentModalCloseEl.addEventListener("click", closeAgentModal);
agentModalBackdropEl.addEventListener("click", closeAgentModal);
startMissionBtnEl.addEventListener("click", startMission);
puzzleAcceptBtnEl.addEventListener("click", () => {
  if (!pendingPuzzle) return;
  const { sceneId, config } = pendingPuzzle;
  const agentId = getCurrentAgentId();
  puzzleManager.render(sceneId, config, nextScene => {
    sceneHistory.push(sceneId);
    renderScene(nextScene);
  }, agentId);
});

// Event listeners para el modal de agente
resetProgressBtnEl.addEventListener("click", handleResetProgress);
switchAgentBtnEl.addEventListener("click", openAgentSelector);

// Event listeners para el selector de agentes
agentSelectorCloseEl.addEventListener("click", closeAgentSelector);
agentSelectorBackdropEl.addEventListener("click", closeAgentSelector);

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
