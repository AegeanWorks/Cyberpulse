/**
 * CYBERPULSE // NEURAL INTRUSION CYBERDECK CLIENT
 * Pure Vanilla JavaScript: Web Audio Synthesizer, 2D Matrix Canvas, & Interactive Mini-Games
 */

// ==========================================================================
// 1. Web Audio API Sound Synthesizer (Zero External Audio Files)
// ==========================================================================
class SoundFX {
  constructor() {
    this.ctx = null;
    this.enabled = true;
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  playTone(freq, type = "sine", duration = 0.1, gainVal = 0.15) {
    if (!this.enabled) return;
    this.init();
    if (!this.ctx) return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (_) {}
  }

  click() {
    this.playTone(850, "square", 0.03, 0.05);
  }

  scan() {
    if (!this.enabled) return;
    this.init();
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(300, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1400, this.ctx.currentTime + 0.25);
      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.25);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.25);
    } catch (_) {}
  }

  nearMiss() {
    // High-arousal double heart-thump
    this.playTone(180, "triangle", 0.12, 0.35);
    setTimeout(() => this.playTone(220, "triangle", 0.15, 0.4), 140);
  }

  success() {
    // Cyberpunk major arpeggio
    const notes = [523.25, 659.25, 783.99, 1046.50];
    notes.forEach((freq, idx) => {
      setTimeout(() => this.playTone(freq, "sine", 0.2, 0.2), idx * 75);
    });
  }

  jackpot() {
    // 2.5x Jackpot celebration chime
    const notes = [440, 554.37, 659.25, 880, 1108.73, 1318.51];
    notes.forEach((freq, idx) => {
      setTimeout(() => this.playTone(freq, "triangle", 0.28, 0.25), idx * 60);
    });
  }

  failure() {
    this.playTone(140, "sawtooth", 0.35, 0.3);
  }

  alarm() {
    this.playTone(480, "sawtooth", 0.2, 0.3);
    setTimeout(() => this.playTone(360, "sawtooth", 0.2, 0.3), 120);
  }
}

const sfx = new SoundFX();

function loadPreference(key, fallback) {
  try {
    const value = localStorage.getItem(`cyberpulse.${key}`);
    return value === null ? fallback : value;
  } catch (_) {
    return fallback;
  }
}

function savePreference(key, value) {
  try {
    localStorage.setItem(`cyberpulse.${key}`, String(value));
  } catch (_) {
    // Local storage can be unavailable in private or restricted contexts.
  }
}

// ==========================================================================
// 2. Cyberdeck Application State Coordinator
// ==========================================================================
const state = {
  data: null,
  selectedNodeId: null,
  selectedEmployee: null,
  selectedVector: "spear_phish",
  activePuzzle: null,
  bufferInput: [],
  animFrameId: null,
  packetParticles: [],
  tutorialDismissed: false,
  hallFilter: "all",
  careerData: null,
};

// Node matrix layout coordinates on 800x560 canvas
const DESIGN_W = 800;
const DESIGN_H = 560;

function matrixViewport() {
  const canvas = document.getElementById("matrix-canvas");
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (canvas.width !== Math.round(rect.width * dpr) || canvas.height !== Math.round(rect.height * dpr)) {
    canvas.width = Math.max(1, Math.round(rect.width * dpr));
    canvas.height = Math.max(1, Math.round(rect.height * dpr));
  }
  const scale = Math.min(rect.width / DESIGN_W, rect.height / DESIGN_H);
  const offX = (rect.width - DESIGN_W * scale) / 2;
  const offY = (rect.height - DESIGN_H * scale) / 2;
  return { dpr, scale, offX, offY, cssW: rect.width, cssH: rect.height };
}

function toDesignPoint(clientX, clientY) {
  const canvas = document.getElementById("matrix-canvas");
  const rect = canvas.getBoundingClientRect();
  const view = matrixViewport();
  const cssX = clientX - rect.left;
  const cssY = clientY - rect.top;
  return { x: (cssX - view.offX) / view.scale, y: (cssY - view.offY) / view.scale };
}

// Node matrix layout coordinates on the 800x560 design space
const NODE_POSITIONS = {
  node_gateway:       { x: 100, y: 280, label: "GATEWAY" },
  node_proxy_a:       { x: 260, y: 150, label: "PROXY ALPHA" },
  node_proxy_b:       { x: 260, y: 410, label: "PROXY BETA" },
  node_vault_1:       { x: 450, y: 90,  label: "FINANCIAL VAULT" },
  node_vault_2:       { x: 450, y: 470, label: "PROTOTYPE ARCHIVE" },
  node_ice_perimeter: { x: 500, y: 280, label: "BLACK ICE CLUSTER" },
  node_central_core:  { x: 700, y: 280, label: "SUPERCORE" },
};

// Seeded side-subnet hosts reuse these three canvas slots; the label and
// presence come from the current run's snapshot.
const SIDE_NODE_SLOTS = {
  node_side_01: { x: 370, y: 200 },
  node_side_02: { x: 370, y: 360 },
  node_side_03: { x: 620, y: 440 },
};

// ==========================================================================
// 3. API Communication Layer
// ==========================================================================
async function apiGet(endpoint) {
  try {
    const res = await fetch(endpoint);
    return await res.json();
  } catch (err) {
    console.error("API GET Error:", err);
    return null;
  }
}

async function apiPost(endpoint, payload) {
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await res.json();
  } catch (err) {
    console.error("API POST Error:", err);
    return null;
  }
}

// ==========================================================================
// 4. Initial Setup & Event Listeners
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  initUIEvents();
  initMatrixCanvas();
  refreshFullState();
});

function restorePreferences() {
  const themes = ["theme-phosphor", "theme-cyber", "theme-amber"];
  const storedTheme = loadPreference("theme", "theme-cyber");
  const theme = themes.includes(storedTheme) ? storedTheme : "theme-cyber";
  document.body.classList.remove(...themes);
  document.body.classList.add(theme);
  const themeSelector = document.getElementById("theme-selector");
  if (themeSelector) themeSelector.value = theme;

  const audioOn = loadPreference("audio", "on") !== "off";
  sfx.enabled = audioOn;
  const btnAudio = document.getElementById("btn-audio");
  if (btnAudio) btnAudio.textContent = audioOn ? "FX ON" : "FX OFF";

  const crtOn = loadPreference("crt", "off") === "on";
  document.body.classList.toggle("crt-effects", crtOn);
  const btnCrt = document.getElementById("btn-crt");
  if (btnCrt) btnCrt.textContent = crtOn ? "CRT ON" : "CRT OFF";
}

async function handleResetCareer() {
  const answer = window.prompt("Type RESET to back up and clear the career, dossier, and all saves.");
  if (answer !== "RESET") return;
  sfx.click();
  const res = await apiPost("/api/action", { action: "reset_career", confirm: "RESET" });
  if (res && res.ok) {
    sfx.success();
    state.data = res.state;
    state.careerData = null;
    state.selectedNodeId = null;
    state.hallFilter = "all";
    closePuzzleBay();
    renderEmptyTargetCard();
    document.getElementById("modal-career").classList.add("hidden");
    document.getElementById("modal-main-menu").classList.add("hidden");
    addTerminalLog(res.message || "Career reset.", "success");
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "Career reset failed.", "warn");
  }
}

async function handleSaveAlias() {
  const input = document.getElementById("dossier-alias-input");
  const name = input ? input.value.trim() : "";
  if (!name) return;
  sfx.click();
  const res = await apiPost("/api/action", { action: "rename_alias", name });
  if (res && res.ok) {
    sfx.success();
    document.getElementById("dossier-alias").textContent = name;
    if (state.careerData) state.careerData.alias = name;
    state.data = res.state;
    addTerminalLog(res.message || `Alias set to ${name}.`, "success");
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "Alias could not be saved.", "warn");
  }
}

function initUIEvents() {
  // First user interaction unlocks AudioContext
  document.body.addEventListener("click", () => sfx.init(), { once: true });

  // Header toggles
  const btnAudio = document.getElementById("btn-audio");
  btnAudio.addEventListener("click", () => {
    sfx.enabled = !sfx.enabled;
    btnAudio.textContent = sfx.enabled ? "FX ON" : "FX OFF";
    savePreference("audio", sfx.enabled ? "on" : "off");
    if (sfx.enabled) sfx.click();
  });

  const btnCrt = document.getElementById("btn-crt");
  btnCrt.addEventListener("click", () => {
    document.body.classList.toggle("crt-effects");
    const enabled = document.body.classList.contains("crt-effects");
    btnCrt.textContent = enabled ? "CRT ON" : "CRT OFF";
    savePreference("crt", enabled ? "on" : "off");
    sfx.click();
  });

  const themeSelector = document.getElementById("theme-selector");
  themeSelector.addEventListener("change", (e) => {
    document.body.classList.remove("theme-phosphor", "theme-cyber", "theme-amber");
    document.body.classList.add(e.target.value);
    savePreference("theme", e.target.value);
    sfx.click();
  });

  restorePreferences();
  document.getElementById("btn-save-alias").addEventListener("click", handleSaveAlias);
  document.getElementById("btn-reset-career").addEventListener("click", handleResetCareer);

  // Action Buttons
  document.getElementById("btn-scan").addEventListener("click", handleScan);
  document.getElementById("btn-spoof").addEventListener("click", handleSpoof);
  document.getElementById("btn-lay-low").addEventListener("click", handleLayLow);
  document.getElementById("btn-jackout").addEventListener("click", handleJackout);
  document.getElementById("btn-cves-open").addEventListener("click", openCvesModal);
  document.getElementById("btn-rig-open").addEventListener("click", openRigModal);
  document.getElementById("btn-workshop-open").addEventListener("click", openWorkshopModal);
  document.getElementById("btn-shop-open").addEventListener("click", openShopModal);
  document.getElementById("btn-career-open").addEventListener("click", openCareerModal);
  document.getElementById("btn-rival-open").addEventListener("click", openRivalModal);
  document.getElementById("btn-counter-rival").addEventListener("click", handleCounterRival);
  document.getElementById("grid-rival").addEventListener("click", openRivalModal);
  document.querySelectorAll(".hall-filter").forEach((button) => {
    button.addEventListener("click", () => {
      state.hallFilter = button.dataset.hallFilter || "all";
      document.querySelectorAll(".hall-filter").forEach((candidate) => {
        candidate.classList.toggle("active", candidate === button);
      });
      renderHall();
    });
  });
  document.getElementById("btn-reset-run").addEventListener("click", handleReset);
  document.getElementById("btn-reroll-contracts").addEventListener("click", handleRerollContracts);
  document.getElementById("btn-quests-open").addEventListener("click", openQuestsModal);
  document.getElementById("btn-contacts-open").addEventListener("click", openContactsModal);
  document.getElementById("btn-overdrive").addEventListener("click", handleOverdrive);
  document.getElementById("btn-quickhack").addEventListener("click", handleQuickhack);
  document.getElementById("btn-proxy-node").addEventListener("click", handleAddProxy);
  const revealBtn = document.getElementById("btn-intel-reveal");
  const forgeBtn = document.getElementById("btn-intel-forge");
  if (revealBtn) revealBtn.addEventListener("click", () => handleIntel("reveal"));
  if (forgeBtn) forgeBtn.addEventListener("click", () => handleIntel("forge"));

  document.querySelectorAll(".stance-btn").forEach((btn) => {
    btn.addEventListener("click", () => handleStance(btn.dataset.stance));
  });

  const consolePanel = document.getElementById("console-panel");
  const consoleToggle = document.getElementById("btn-console-toggle");
  if (consolePanel && consoleToggle) {
    consoleToggle.addEventListener("click", () => {
      const open = consolePanel.classList.toggle("open");
      consoleToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Main menu
  document.getElementById("menu-load-run").addEventListener("click", handleLoad);
  document.getElementById("btn-save-run").addEventListener("click", handleSave);
  document.getElementById("menu-jack-in").addEventListener("click", () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    sfx.success();
  });
  document.getElementById("menu-new-run").addEventListener("click", async () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    await handleReset();
  });
  document.getElementById("menu-daily-run").addEventListener("click", handleDailyReset);
  document.getElementById("menu-story").addEventListener("click", () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    openQuestsModal();
  });
  document.getElementById("menu-contacts").addEventListener("click", () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    openContactsModal();
  });
  document.getElementById("menu-career").addEventListener("click", () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    openCareerModal();
  });
  document.getElementById("menu-help").addEventListener("click", () => {
    document.getElementById("main-menu-help").classList.toggle("hidden");
  });

  // Target Actions
  document.getElementById("btn-probe-node").addEventListener("click", handleProbeNode);
  document.getElementById("btn-init-hack").addEventListener("click", handleStartHack);
  document.getElementById("btn-bypass-fw").addEventListener("click", openBypassModal);
  document.getElementById("btn-evade-av").addEventListener("click", handleEvadeAv);
  document.getElementById("btn-social-eng").addEventListener("click", openSocialModal);
  document.getElementById("btn-move-node").addEventListener("click", handleMoveNode);
  document.getElementById("btn-keylogger-node").addEventListener("click", handleDeployKeylogger);
  document.getElementById("btn-wipe-logs").addEventListener("click", handleWipeLogs);
  document.getElementById("btn-close-viewer").addEventListener("click", () => {
    document.getElementById("fs-file-viewer").classList.add("hidden");
    sfx.click();
  });

  // Modals
  document.getElementById("btn-close-shop").addEventListener("click", () => {
    document.getElementById("modal-shop").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-career").addEventListener("click", () => {
    document.getElementById("modal-career").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-rival").addEventListener("click", () => {
    document.getElementById("modal-rival").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-tutorial-close").addEventListener("click", () => {
    state.tutorialDismissed = true;
    document.getElementById("tutorial-panel").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-saves").addEventListener("click", () => {
    document.getElementById("modal-saves").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-rig").addEventListener("click", () => {
    document.getElementById("modal-rig").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-workshop").addEventListener("click", () => {
    document.getElementById("modal-workshop").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-cves").addEventListener("click", () => {
    document.getElementById("modal-cves").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-social").addEventListener("click", () => {
    document.getElementById("modal-social").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-quests").addEventListener("click", () => {
    document.getElementById("modal-quests").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-contacts").addEventListener("click", () => {
    document.getElementById("modal-contacts").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-bypass").addEventListener("click", () => {
    document.getElementById("modal-bypass").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-execute-social").addEventListener("click", executeSocialAttack);

  // Frequency slider live readout
  const freqSlider = document.getElementById("freq-slider");
  freqSlider.addEventListener("input", (e) => {
    document.getElementById("freq-val").textContent = `${parseFloat(e.target.value).toFixed(1)} GHz`;
  });
  document.getElementById("btn-tune-freq").addEventListener("click", handleTuneFrequency);

  // Buffer controls
  document.getElementById("btn-clear-buf").addEventListener("click", () => {
    state.bufferInput = [];
    renderBufferPlayerSequence();
    sfx.click();
  });
  document.getElementById("btn-inject-buf").addEventListener("click", handleInjectBuffer);

  // Banner action button
  document.getElementById("btn-banner-action").addEventListener("click", () => {
    document.getElementById("announcement-banner").classList.add("hidden");
    handleReset();
  });

  // Global Keyboard Navigation
  window.addEventListener("keydown", (e) => {
    if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      return;
    }

    if (e.key === "Escape") {
      closeAllModals();
      return;
    }

    const mainMenu = document.getElementById("modal-main-menu");
    if (mainMenu && !mainMenu.classList.contains("hidden")) {
      return;
    }

    const key = e.code;
    if (key === "KeyS") {
      e.preventDefault();
      handleScan();
    } else if (key === "KeyP") {
      e.preventDefault();
      handleProbeNode();
    } else if (key === "KeyE") {
      e.preventDefault();
      handleStartHack();
    } else if (key === "KeyJ") {
      e.preventDefault();
      handleJackout();
    } else if (key === "KeyC") {
      e.preventDefault();
      toggleModal("modal-cves", openCvesModal);
    } else if (key === "KeyR") {
      e.preventDefault();
      toggleModal("modal-rig", openRigModal);
    } else if (key === "KeyM") {
      e.preventDefault();
      toggleModal("modal-workshop", openWorkshopModal);
    } else if (key === "KeyB") {
      e.preventDefault();
      toggleModal("modal-shop", openShopModal);
    } else if (key === "KeyD") {
      e.preventDefault();
      toggleModal("modal-career", openCareerModal);
    } else if (key === "KeyF") {
      e.preventDefault();
      openBypassModal();
    } else if (key === "KeyA") {
      e.preventDefault();
      handleEvadeAv();
    } else if (key === "KeyQ") {
      e.preventDefault();
      toggleModal("modal-quests", openQuestsModal);
    } else if (key === "KeyN") {
      e.preventDefault();
      toggleModal("modal-contacts", openContactsModal);
    } else if (key === "KeyO") {
      e.preventDefault();
      handleOverdrive();
    } else if (key === "KeyL") {
      e.preventDefault();
      handleLayLow();
    } else if (key === "KeyV") {
      e.preventDefault();
      handleSpoof();
    } else if (key === "KeyH") {
      e.preventDefault();
      handleQuickhack();
    }
  });
}

function closeAllModals() {
  document.querySelectorAll(".modal-overlay").forEach(m => m.classList.add("hidden"));
  const viewer = document.getElementById("fs-file-viewer");
  if (viewer) viewer.classList.add("hidden");
  sfx.click();
}

function toggleModal(modalId, openFn) {
  const el = document.getElementById(modalId);
  if (!el) return;
  if (el.classList.contains("hidden")) {
    openFn();
  } else {
    el.classList.add("hidden");
    sfx.click();
  }
}

// ==========================================================================
// 5. State Synchronization & HUD Rendering
// ==========================================================================
async function refreshFullState() {
  const data = await apiGet("/api/state");
  if (!data) return;
  state.data = data;
  renderHUD(data);
  updateExploitChips(data.deck.exploits);
  if (state.selectedNodeId) {
    updateTargetCard(state.selectedNodeId);
  } else {
    renderEmptyTargetCard();
  }
}

function formatShiftDoctrine(world) {
  const mods = world.shift_modifiers || {};
  const parts = [];
  if (mods.resecure_chance_delta) {
    const pct = Math.round(mods.resecure_chance_delta * 100);
    parts.push(`RESEC ${pct > 0 ? "+" : ""}${pct}%`);
  }
  if (mods.market_bias) {
    const pct = Math.round(mods.market_bias * 100);
    parts.push(`MKT ${pct > 0 ? "+" : ""}${pct}%`);
  }
  if (mods.alert_decay_bonus) {
    parts.push(`COOLDOWN +${mods.alert_decay_bonus}`);
  }
  if (mods.hunter_threshold) {
    parts.push(`HUNT ${mods.hunter_threshold}%`);
  }
  return parts.length ? parts.join(" · ") : "STANDARD POSTURE";
}

function renderEmptyTargetCard() {
  const card = document.getElementById("target-card");
  if (!card) return;
  card.classList.add("is-empty");
  const nameEl = document.getElementById("target-name");
  if (nameEl) nameEl.textContent = "Select a node on the matrix";
  const badgeEl = document.getElementById("target-badge");
  if (badgeEl) badgeEl.textContent = "NO SELECTION";
}

function renderTutorial(data) {
  const panel = document.getElementById("tutorial-panel");
  const container = document.getElementById("tutorial-steps");
  if (!panel || !container) return;
  const career = data.career || {};
  const settled = (career.successful_runs || 0) + (career.failed_runs || 0);
  const steps = Array.isArray(data.tutorial) ? data.tutorial : [];
  const complete = steps.length > 0 && steps.every((step) => step.done);
  if (!steps.length || settled > 0 || complete || state.tutorialDismissed) {
    panel.classList.add("hidden");
    return;
  }

  panel.classList.remove("hidden");
  container.innerHTML = "";
  steps.forEach((step) => {
    const row = document.createElement("div");
    row.className = `tutorial-step${step.done ? " done" : ""}`;
    const mark = document.createElement("span");
    mark.className = "tutorial-mark";
    mark.textContent = step.done ? "[x]" : "[ ]";
    const copy = document.createElement("div");
    copy.className = "tutorial-copy";
    const title = document.createElement("span");
    title.className = "tutorial-step-title";
    title.textContent = step.title;
    const hint = document.createElement("span");
    hint.className = "tutorial-step-hint";
    hint.textContent = step.hint;
    copy.append(title, hint);
    row.append(mark, copy);
    container.appendChild(row);
  });
}

function renderGridTicker(world) {
  const bar = document.getElementById("grid-bar");
  if (!bar || !world) return;

  const clockText = (world.clock || "Day 1 08:00").replace(/\s*\([^)]*\)\s*/g, " ").trim();
  document.getElementById("grid-clock").textContent = clockText.toUpperCase();
  document.getElementById("grid-shift").textContent = (world.shift || "Morning").toUpperCase();
  const effectEl = document.getElementById("grid-shift-effect");
  effectEl.textContent = formatShiftDoctrine(world);
  effectEl.title = (world.shift_effect || "Standard posture").toUpperCase();

  const alertEl = document.getElementById("grid-alert");
  const alertLevel = world.alert_level || 0;
  const alertTier = world.alert_tier || "";
  alertEl.textContent = `GRID ALERT ${alertLevel}%${alertTier ? ` [${alertTier}]` : ""}`;
  alertEl.classList.toggle("hot", alertLevel >= 50);

  const market = world.market_multiplier || 1;
  document.getElementById("grid-market").textContent = `MARKET x${Number(market).toFixed(3)}`;

  const hunterEl = document.getElementById("grid-hunter");
  if (hunterEl) {
    const hunters = world.hunters || [];
    const activeHunters = hunters.filter(h => h.status === "hunting" || h.status === "confused" || h.status === "intercepted");
    if (activeHunters.length > 0) {
      hunterEl.style.display = "inline-block";
      const h = activeHunters[0];
      const dist = world.nearest_hunter_distance;
      const distStr = dist === 0 ? "INTERCEPT!" : (dist > 0 ? `${dist} HOP${dist > 1 ? "S" : ""}` : "UNKNOWN");
      hunterEl.textContent = `HUNTER: ${h.name.toUpperCase()} (${distStr})`;
      hunterEl.classList.toggle("hot", dist <= 1);
    } else {
      hunterEl.style.display = "none";
    }
  }

  const ticker = document.getElementById("grid-ticker");
  const headlines = world.news || [];
  if (ticker && headlines.length) {
    const latest = headlines[headlines.length - 1];
    const text = `${latest.source || "GRIDWIRE"}: ${latest.headline}`;
    if (ticker.textContent !== text) {
      ticker.textContent = text;
      ticker.classList.remove("ticker-flash");
      void ticker.offsetWidth;
      ticker.classList.add("ticker-flash");
    }
  }
}

function renderHUD(data) {
  const { deck, state: gState, current_node, career } = data;
  if (data.nodes) syncSideNodePositions(data.nodes);

  // CPU Gauge
  const cpuPercent = (deck.cpu_cycles / deck.max_cpu) * 100;
  document.getElementById("fill-cpu").style.width = `${cpuPercent}%`;
  document.getElementById("val-cpu").textContent = `${deck.cpu_cycles}/${deck.max_cpu}`;

  // RAM Gauge
  document.getElementById("val-ram").textContent = `${deck.ram_mb}MB`;
  const ramPercent = deck.max_ram ? (deck.ram_mb / deck.max_ram) * 100 : 100;
  document.getElementById("fill-ram").style.width = `${ramPercent}%`;

  // Stance switcher reflects the active operating bus
  document.querySelectorAll(".stance-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.stance === (deck.operating_stance || "balanced"));
  });
  renderProxyStrip(data);

  // Trace Danger Meter
  const trace = gState.trace_percent;
  document.getElementById("fill-trace").style.width = `${trace}%`;
  const extRisk = data.extraction_risk || { surge: 0, lethal: false, projected_trace: trace };
  const traceEl = document.getElementById("val-trace");
  traceEl.textContent = extRisk.surge
    ? `${trace}% · JACK +${extRisk.surge}%`
    : `${trace}%`;
  document.getElementById("gauge-trace").classList.toggle("hot", trace >= 60);
  traceEl.title = extRisk.lethal
    ? `LETHAL: pulling the jack now projects ${extRisk.projected_trace}% trace and will burn the deck.`
    : extRisk.surge
      ? `Extraction surge +${extRisk.surge}% (projected ${extRisk.projected_trace}%).`
      : "Extraction surge safe.";

  if (trace >= 80 && trace < 100) {
    sfx.alarm();
    addTerminalLog(`⚠️ CRITICAL TRACE: ${trace}%! Black ICE locks tightening!`, "danger");
    const stage = document.getElementById("matrix-stage");
    if (stage && motionSafe()) {
      stage.classList.remove("trace-shake");
      void stage.offsetWidth;
      stage.classList.add("trace-shake");
    }
  }

  // Unbanked & Career Bank
  document.getElementById("val-loot").textContent = `${gState.unbanked_creds} CR`;
  document.getElementById("val-bank").textContent = `${career.banked_creds} CR`;
  const comboEl = document.getElementById("val-combo");
  const prevCombo = state._prevCombo || 0;
  comboEl.textContent = `x${gState.combo_streak || 0}`;
  if ((gState.combo_streak || 0) > prevCombo && motionSafe()) {
    comboEl.classList.remove("combo-pop");
    void comboEl.offsetWidth;
    comboEl.classList.add("combo-pop");
  }
  state._prevCombo = gState.combo_streak || 0;
  const cpuBox = document.getElementById("gauge-cpu");
  if (cpuBox) cpuBox.classList.toggle("low-cpu", (deck.cpu_cycles || 0) <= 2);
  const vignette = document.getElementById("damage-vignette");
  if (vignette) {
    const heat = Math.max(0, Math.min(1, trace / 100));
    vignette.style.opacity = (heat * 0.55).toFixed(2);
  }
  if (motionSafe() && (gState.combo_streak === 5 || gState.combo_streak === 10) && gState.combo_streak > (prevCombo || 0)) {
    const stage = document.getElementById("matrix-stage");
    if (stage) {
      stage.classList.add("breach-flash");
      setTimeout(() => stage.classList.remove("breach-flash"), 320);
    }
    addTerminalLog(`COMBO MILESTONE x${gState.combo_streak}: next breach +${Math.min(50, 10 * gState.combo_streak)}%. Bank before the grid answers.`, "success");
  }
  const intelEl = document.getElementById("val-intel");
  if (intelEl) {
    const intel = deck.threat_intel_count || 0;
    intelEl.textContent = `${intel}`;
    intelEl.classList.toggle("highlight-value", intel > 0);
    intelEl.parentElement.title = "Threat intel: harvest in ANALYSIS stance, spend in the LAB.";
  }

  // Living grid ticker: clock, alert, market, and the newest headline
  renderGridTicker(data.world || gState.world);
  {
    const damp = (data.deck && data.deck.ice_dampener_level) || 0;
    const stance = (data.deck && data.deck.operating_stance) || "balanced";
    const proxies = (data.deck && data.deck.proxy_chain ? data.deck.proxy_chain.length : 0);
    const mit = `Mitigation: dampener L${damp}, ${stance}, ${proxies}/3 proxies.`;
    const setTitle = (id, text) => { const el = document.getElementById(id); if (el) el.title = `${text} ${mit}`; };
    setTitle("btn-scan", "SCAN: +1 CPU, +5% raw trace, 1 turn. Reveals adjacent nodes.");
    const odCost = (data.arcs && data.arcs.live && data.arcs.live.kilo_overdrive) ? 1 : 2;
    setTitle("btn-overdrive", `OVERDRIVE: -${odCost} CPU, +8% raw trace, +1 combo, +10 CR unbanked. Blocked at 92%+ trace.${odCost === 1 ? " Kilo arc discount." : ""}`);
    setTitle("btn-spoof", "SPOOF: -3 CPU, trace -25% (floor 0%), scrambles hunters 2 turns.");
    setTitle("btn-lay-low", "LAY LOW: +1 CPU/turn for 1-3 turns; the grid keeps moving.");
    const comboEl2 = document.getElementById("val-combo");
    if (comboEl2) comboEl2.title = `Next breach +${Math.min(50, 10 * (gState.combo_streak + 1))}%; combo breaks on any detected failure.`;
  }

  updateMatrixCoords();

  renderTutorial(data);

  const dailyChip = document.getElementById("grid-daily");
  if (dailyChip) {
    const dailyKey = data.daily_key || "";
    const dailyStreak = data.career && data.career.daily_streak
      ? ` · STREAK ${data.career.daily_streak}`
      : "";
    const dailyMod = data.daily_modifier && data.daily_modifier.name
      ? ` · ${data.daily_modifier.name}`
      : "";
    dailyChip.textContent = dailyKey ? `DAILY ${dailyKey}${dailyStreak}${dailyMod}` : "";
    dailyChip.style.display = dailyKey ? "" : "none";
    dailyChip.title = data.daily_modifier ? data.daily_modifier.description : "";
  }

  const difficultyChip = document.getElementById("grid-difficulty");
  if (difficultyChip) {
    const difficulty = String(data.difficulty || "normal").toLowerCase();
    difficultyChip.textContent = `DIFFICULTY ${difficulty.toUpperCase()}`;
    difficultyChip.classList.toggle("hard", difficulty === "hard");
    difficultyChip.classList.toggle("easy", difficulty === "easy");
  }

  const allegianceChip = document.getElementById("grid-allegiance");
  if (allegianceChip) {
    const allegiance = String(data.allegiance || "none").toLowerCase();
    allegianceChip.textContent = allegiance === "none"
      ? "INDEPENDENT"
      : `PATRON ${allegiance.toUpperCase()}`;
    allegianceChip.style.display = allegiance === "none" ? "none" : "";
  }

  const rivalChip = document.getElementById("grid-rival");
  if (rivalChip) {
    const rival = data.rival;
    rivalChip.textContent = rival
      ? `RIVAL ${rival.name} · ${rival.turns_until}T · ${rival.contracts_stolen} STOLEN`
      : "";
    rivalChip.style.display = rival ? "" : "none";
    rivalChip.title = rival ? `${rival.tagline} ${rival.handle}` : "";
  }

  // Story beat and active objective
  if (data.story) {
    document.getElementById("story-act").textContent =
      `${data.story.act_title} // ${data.story.chapter_title}`;
    const activeQuest = (data.quests || []).find(q => q.accepted && !q.completed);
    document.getElementById("story-objective").textContent = activeQuest
      ? activeQuest.description
      : "Open MISSIONS or talk to an operative to pick up the next job.";
    const menuStory = document.getElementById("main-menu-story");
    if (menuStory) menuStory.textContent = `${data.story.act_title} // ${data.story.chapter_title}`;
    const menuSub = document.getElementById("main-menu-sub");
    if (menuSub && data.story.intro) menuSub.textContent = data.story.intro;
  }

  const loadBtn = document.getElementById("menu-load-run");
  if (loadBtn) loadBtn.classList.toggle("hidden", !data.has_save);
  const saveBtn = document.getElementById("btn-save-run");
  if (saveBtn) {
    saveBtn.title = "Save or load a run from the slot archive";
  }
  const rerollBtn = document.getElementById("btn-reroll-contracts");
  if (rerollBtn) {
    const terminal = Boolean(gState.is_victory || gState.is_game_over || gState.is_jacked_out);
    rerollBtn.disabled = terminal || (data.deck && data.deck.cryptocreds < 50);
  }

  // Syndicate Bounty Contract
  const contract = gState.active_contract;
  if (contract) {
    document.getElementById("contract-card").classList.remove("hidden");
    document.getElementById("contract-bounty-val").textContent = `+${contract.reward_creds} CR`;
    document.getElementById("contract-title").textContent = contract.title;
    let contractStatus = contract.completed
      ? "STATUS: COMPLETED [FUNDS GRANTED]"
      : `${(contract.risk_tier || "standard").toUpperCase()} | TARGET: ${contract.target_node_type} | TRACE LIMIT: ${contract.max_trace_limit}%`;
    if (!contract.completed && contract.expires_turn) {
      const remaining = Math.max(0, contract.expires_turn - gState.turns_elapsed);
      contractStatus += ` | DEADLINE: ${remaining} TURN${remaining === 1 ? "" : "S"}`;
      if (contract.bonus_creds) {
        contractStatus += ` | RUSH +${contract.bonus_creds} BY TURN ${contract.rush_turn}`;
      }
    }
    if (gState.contract_notice) {
      contractStatus += ` | ${gState.contract_notice}`;
    }
    document.getElementById("contract-status").textContent = contractStatus;
  } else if ((gState.contract_offers || []).length) {
    document.getElementById("contract-card").classList.remove("hidden");
    document.getElementById("contract-bounty-val").textContent = `${gState.contract_offers.length} JOBS`;
    document.getElementById("contract-title").textContent = "SYNDICATE JOB BOARD OPEN";
    document.getElementById("contract-status").textContent =
      "Open MISSION BOARD to accept a posted contract." +
      (gState.contract_notice ? ` | ${gState.contract_notice}` : "");
  } else {
    document.getElementById("contract-card").classList.add("hidden");
  }

  // Check Game Over / Victory Overlays
  if (gState.is_victory) {
    const summary = data.run_summary || {};
    const legacy = (summary.epilogue || []).join(" ");
    showBanner(
      summary.outcome_title || "MISSION ACCOMPLISHED",
      legacy || "The supercore falls and the Syndicate owes you a favor.",
      buildRunStats(summary, gState)
    );
    sfx.jackpot();
  } else if (gState.is_game_over) {
    const summary = data.run_summary || {};
    const legacy = (summary.epilogue || []).join(" ");
    showBanner(
      summary.outcome_title || "CONNECTION TERMINATED",
      legacy || "Trace hit 100%. The deck burned and the grid forgot your name.",
      buildRunStats(summary, gState)
    );
    sfx.failure();
  }
}

function buildRunStats(summary, gState) {
  const turns = summary.turns_elapsed || (gState && gState.turns_elapsed) || 0;
  const breached = summary.nodes_breached;
  const bestCombo = summary.best_combo || (gState && gState.best_combo) || 0;
  const questsDone = summary.quests_completed_count || 0;
  const questsTotal = summary.quests_total || 0;
  const stats = [];
  if (typeof breached === "number") {
    stats.push({ label: "HOSTS BREACHED", value: `${breached}` });
  }
  if (Array.isArray(summary.districts_compromised) && summary.districts_compromised.length) {
    stats.push({ label: "GRID HELD", value: `${summary.districts_compromised.length}/5 — ${summary.districts_compromised.join(", ")}` });
  }
  if (turns) {
    stats.push({ label: "TURNS", value: `${turns}` });
  }
  stats.push({ label: "BEST COMBO", value: `x${bestCombo}` });
  if (questsTotal) {
    stats.push({ label: "MISSIONS", value: `${questsDone}/${questsTotal}` });
  }
  const milestones = Array.isArray(summary.achievements_unlocked) ? summary.achievements_unlocked.length : 0;
  if (milestones) {
    stats.push({ label: "MILESTONES", value: `+${milestones}` });
  }
  if (summary.daily_key) {
    stats.push({ label: "DAILY", value: summary.daily_key });
  }
  if (typeof summary.score === "number") {
    const rank = summary.hall_rank ? ` #${summary.hall_rank}` : "";
    stats.push({ label: "SCORE", value: `${summary.score.toLocaleString()}${rank}` });
  }
  if (summary.difficulty) {
    stats.push({ label: "DIFFICULTY", value: String(summary.difficulty).toUpperCase() });
  }
  if (summary.allegiance && summary.allegiance !== "none") {
    stats.push({ label: "PATRON", value: String(summary.allegiance).toUpperCase() });
  }
  if (summary.daily_modifier && summary.daily_modifier.name) {
    stats.push({ label: "DAILY MOD", value: summary.daily_modifier.name });
  }
  const promotions = Array.isArray(summary.rank_ups) ? summary.rank_ups.length : 0;
  if (promotions) {
    stats.push({ label: "PROMOTIONS", value: `+${promotions}` });
  }
  return stats;
}

function applyStateSnapshot(res) {
  if (!res || !res.state) return false;
  state.data = res.state;
  renderHUD(res.state);
  return true;
}

function sideNodeLabel(name) {
  return String(name || "SIDE HOST").toUpperCase();
}

function syncSideNodePositions(nodes) {
  if (!nodes) return;
  for (const nid of Object.keys(SIDE_NODE_SLOTS)) {
    delete NODE_POSITIONS[nid];
  }
  for (const [nid, node] of Object.entries(nodes)) {
    const slot = SIDE_NODE_SLOTS[nid];
    if (!slot) continue;
    NODE_POSITIONS[nid] = { x: slot.x, y: slot.y, label: sideNodeLabel(node.name) };
  }
}

function updateExploitChips(exploits) {
  const container = document.getElementById("exploit-chips-container");
  container.innerHTML = "";
  if (!exploits || exploits.length === 0) {
    container.innerHTML = '<span class="empty-chips">No consumable chips loaded.</span>';
    return;
  }

  exploits.forEach((name) => {
    const btn = document.createElement("button");
    btn.className = "exploit-chip-btn";
    btn.textContent = name.replace(/_/g, " ").toUpperCase();
    btn.title = `Deploy exploit chip: ${name}`;
    btn.addEventListener("click", () => handleUseExploit(name));
    container.appendChild(btn);
  });
}

function renderProxyStrip(data) {
  const strip = document.getElementById("proxy-strip");
  if (!strip) return;
  const chain = (data && data.deck && data.deck.proxy_chain) || [];
  strip.innerHTML = '<span class="dock-label">PROXY</span>';
  if (!chain.length) {
    const empty = document.createElement("span");
    empty.className = "proxy-empty";
    empty.textContent = "NONE";
    strip.appendChild(empty);
    return;
  }
  chain.forEach((nodeId) => {
    const node = data.nodes ? data.nodes[nodeId] : null;
    const chip = document.createElement("span");
    chip.className = "proxy-chip";
    chip.textContent = node ? node.hostname : nodeId;
    const sever = document.createElement("button");
    sever.type = "button";
    sever.title = "Sever this proxy hop";
    sever.textContent = "×";
    sever.addEventListener("click", () => handleSeverProxy(nodeId));
    chip.appendChild(sever);
    strip.appendChild(chip);
  });
}

async function handleStance(stance) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "stance", stance });
  if (res && res.ok) {
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Stance shift refused.", "warn");
  }
}

async function handleIntel(mode) {
  if (mode === "reveal" && !state.selectedNodeId) {
    addTerminalLog("Select a host before spending intel on a reveal.", "warn");
    return;
  }
  sfx.click();
  const res = await apiPost("/api/action", {
    action: "intel",
    mode,
    target: state.selectedNodeId || "",
  });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateExploitChips(res.state.deck.exploits);
    if (state.selectedNodeId) updateTargetCard(state.selectedNodeId);
    if (document.getElementById("modal-workshop").classList.contains("hidden")) {
      return;
    }
    openWorkshopModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Threat intel refused.", "warn");
  }
}

async function handleAddProxy() {
  const target = state.selectedNodeId;
  if (!target) {
    addTerminalLog("Select a breached host first.", "warn");
    return;
  }
  sfx.click();
  const res = await apiPost("/api/action", { action: "proxy", target });
  if (res && res.ok) {
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(target);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Cannot route a proxy through that host.", "warn");
  }
}

async function handleSeverProxy(nodeId) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "sever_proxy", target: nodeId });
  if (res && res.ok) {
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "No proxy hop to sever.", "warn");
  }
}

async function handleQuickhack() {
  const target = state.selectedNodeId;
  if (!target) {
    addTerminalLog("Select an adjacent host to quickhack.", "warn");
    return;
  }
  sfx.scan();
  addTerminalLog(`Rapid-injecting ICE breaker into ${target}...`, "info");
  const res = await apiPost("/api/action", { action: "quickhack", target });
  if (res && res.ok) {
    sfx.jackpot();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(target);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Quickhack failed.", "warn");
    if (res.state) {
      state.data = res.state;
      renderHUD(res.state);
      updateTargetCard(target);
    }
  }
}

function addTerminalLog(msg, type = "info") {
  const stream = document.getElementById("terminal-stream");
  const clean = stripGlyphs(msg);
  const line = document.createElement("div");
  line.className = `log-line ${type}`;
  line.textContent = `> ${clean}`;
  stream.appendChild(line);
  stream.scrollTop = stream.scrollHeight;
  const latest = document.getElementById("console-latest");
  if (latest) latest.textContent = clean;
}

function stripGlyphs(text) {
  return String(text || "")
    .replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{2B00}-\u{2BFF}]/gu, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function showBanner(title, sub, stats = null) {
  const banner = document.getElementById("announcement-banner");
  const kicker = document.getElementById("banner-kicker");
  document.getElementById("banner-heading").textContent = stripGlyphs(title);
  document.getElementById("banner-sub").textContent = stripGlyphs(sub);
  const statsEl = document.getElementById("banner-stats");
  if (statsEl) {
    statsEl.innerHTML = "";
    (stats || []).forEach((entry) => {
      const cell = document.createElement("div");
      cell.className = "banner-stat";
      const label = document.createElement("span");
      label.className = "banner-stat-label";
      label.textContent = entry.label;
      const value = document.createElement("span");
      value.className = "banner-stat-value";
      value.textContent = entry.value;
      cell.appendChild(label);
      cell.appendChild(value);
      statsEl.appendChild(cell);
    });
    statsEl.classList.toggle("hidden", !(stats && stats.length));
  }
  if (kicker) {
    const bad = /terminated|burn|burnout|lockout|severed/i.test(title);
    kicker.textContent = bad ? "CONNECTION LOST" : "RUN COMPLETE";
    kicker.classList.toggle("bad", bad);
  }
  banner.classList.remove("hidden");
}

// ==========================================================================
// 6. Action Handlers (Scan, Spoof, Jackout, Reset, Exploits)
// ==========================================================================
async function handleScan() {
  sfx.scan();
  addTerminalLog("Emitting neural pulse across adjacent subnet...", "info");
  const res = await apiPost("/api/action", { action: "scan" });
  if (res && res.ok) {
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  }
}

async function handleSpoof() {
  sfx.click();
  const res = await apiPost("/api/action", { action: "spoof" });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Failed to bounce proxy.", "warn");
  }
}

async function handleOverdrive() {
  sfx.scan();
  const res = await apiPost("/api/action", { action: "overdrive" });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Overdrive refused.", "warn");
  }
}

async function handleLayLow() {
  sfx.click();
  addTerminalLog("Ghosting the connection and letting the grid move...", "info");
  const turns = parseInt(document.getElementById("lay-low-turns").value, 10);
  const res = await apiPost("/api/action", { action: "lay_low", turns });
  if (res && res.ok) {
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Cannot lay low right now.", "warn");
  }
}

async function handleJackout() {
  sfx.click();
  const res = await apiPost("/api/action", { action: "jackout" });
  if (res && res.ok) {
    sfx.jackpot();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    showBanner(
      "EXTRACTION CONFIRMED",
      stripGlyphs(res.message),
      buildRunStats(res.state.run_summary || {}, res.state.state || {})
    );
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Cannot jack out here.", "warn");
    applyStateSnapshot(res);
  }
}

function selectedDifficulty() {
  const select = document.getElementById("difficulty-select");
  return select ? select.value : "normal";
}

function selectedAllegiance() {
  const select = document.getElementById("allegiance-select");
  return select ? select.value : "none";
}

async function handleReset() {
  sfx.click();
  const res = await apiPost("/api/action", {
    action: "reset",
    difficulty: selectedDifficulty(),
    allegiance: selectedAllegiance(),
  });
  if (res && res.ok) {
    addTerminalLog("Rebooted terminal with fresh cyberspace seed.", "info");
    state.data = res.state;
    state.selectedNodeId = null;
    state._seenBreaches = {};
    closePuzzleBay();
    renderEmptyTargetCard();
    renderHUD(res.state);
  }
}

async function handleReplaySeed(seed) {
  if (!Number.isFinite(seed)) return;
  if (!window.confirm(`Replay seed ${seed}? The live run will be replaced.`)) return;

  sfx.click();
  const res = await apiPost("/api/action", { action: "reset", seed });
  if (res && res.ok) {
    document.getElementById("modal-career").classList.add("hidden");
    document.getElementById("modal-main-menu").classList.add("hidden");
    addTerminalLog(`Replaying archived seed ${seed}.`, "info");
    state.data = res.state;
    state.selectedNodeId = null;
    state._seenBreaches = {};
    closePuzzleBay();
    renderEmptyTargetCard();
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "Seed replay failed.", "warn");
  }
}

async function handleDailyReset() {
  sfx.click();
  const res = await apiPost("/api/action", {
    action: "reset",
    daily: true,
    difficulty: selectedDifficulty(),
    allegiance: selectedAllegiance(),
  });
  if (res && res.ok) {
    document.getElementById("modal-main-menu").classList.add("hidden");
    addTerminalLog(res.message || "Daily run started.", "info");
    state.data = res.state;
    state.selectedNodeId = null;
    state._seenBreaches = {};
    closePuzzleBay();
    renderEmptyTargetCard();
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "Daily run could not start.", "warn");
  }
}

async function handleRerollContracts() {
  sfx.click();
  const res = await apiPost("/api/action", { action: "reroll_contracts" });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message || "Contract board rerolled.", "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "Reroll failed.", "warn");
    applyStateSnapshot(res);
  }
}

async function handleSave() {
  sfx.click();
  await openSavesModal();
}

async function handleLoad() {
  sfx.click();
  await openSavesModal();
}

async function openSavesModal() {
  if (!state.data) {
    await refreshFullState();
  }
  renderSavesModal();
}

function saveSlotRow(slot, label, entry, terminal) {
  const row = document.createElement("div");
  row.className = `save-slot-row${entry ? "" : " empty"}`;

  const copy = document.createElement("div");
  copy.className = "save-slot-copy";
  const name = document.createElement("span");
  name.className = "save-slot-name";
  name.textContent = label;
  const meta = document.createElement("span");
  meta.className = "save-slot-meta";
  meta.textContent = entry
    ? `TURN ${entry.turns} · ${entry.creds} CR · TRACE ${entry.trace}% · ACT ${entry.act}`
    : "EMPTY";
  const time = document.createElement("span");
  time.className = "save-slot-time";
  time.textContent = entry ? entry.saved_at_display : "No checkpoint stored";
  copy.append(name, meta, time);

  const nameInput = slot !== "auto" ? document.createElement("input") : null;
  if (nameInput) {
    nameInput.className = "save-slot-name-input";
    nameInput.maxLength = 32;
    nameInput.placeholder = "Run label";
    nameInput.value = entry ? (entry.name || "") : "";
    nameInput.setAttribute("aria-label", `${label} run label`);
    copy.appendChild(nameInput);
  }

  const actions = document.createElement("div");
  actions.className = "save-slot-actions";
  if (slot !== "auto") {
    const saveBtn = document.createElement("button");
    saveBtn.className = "action-btn";
    saveBtn.textContent = "SAVE";
    saveBtn.disabled = terminal;
    saveBtn.title = terminal ? "This run is over" : `Write the live run to ${label}`;
    saveBtn.addEventListener("click", () => handleSaveSlot(slot, nameInput.value));
    actions.appendChild(saveBtn);

    if (entry) {
      const renameBtn = document.createElement("button");
      renameBtn.className = "action-btn";
      renameBtn.textContent = "RENAME";
      renameBtn.title = `Rename ${label} without changing its checkpoint`;
      renameBtn.addEventListener("click", () => handleRenameSlot(slot, nameInput.value));
      actions.appendChild(renameBtn);

      const deleteBtn = document.createElement("button");
      deleteBtn.className = "action-btn danger-action";
      deleteBtn.textContent = "DELETE";
      deleteBtn.title = `Delete ${label} checkpoint`;
      deleteBtn.addEventListener("click", () => handleDeleteSlot(slot, label));
      actions.appendChild(deleteBtn);
    }
  }
  const loadBtn = document.createElement("button");
  loadBtn.className = "action-btn";
  loadBtn.textContent = "LOAD";
  loadBtn.disabled = !entry || entry.terminal;
  loadBtn.title = !entry ? `No checkpoint in ${label}` : `Restore ${label}`;
  loadBtn.addEventListener("click", () => handleLoadSlot(slot));
  actions.appendChild(loadBtn);

  row.append(copy, actions);
  return row;
}

function renderSavesModal() {
  const container = document.getElementById("saves-list");
  if (!container) return;
  const data = state.data || {};
  const bySlot = {};
  (data.saves || []).forEach((entry) => {
    bySlot[entry.slot] = entry;
  });
  const runState = data.state || {};
  const terminal = Boolean(runState.is_victory || runState.is_game_over || runState.is_jacked_out);

  container.innerHTML = "";
  container.appendChild(saveSlotRow("auto", "AUTOSAVE", bySlot.auto, terminal));
  ["1", "2", "3"].forEach((slot) => {
    container.appendChild(saveSlotRow(slot, `SLOT ${slot}`, bySlot[slot], terminal));
  });
  document.getElementById("modal-saves").classList.remove("hidden");
}

async function handleSaveSlot(slot, name = "") {
  sfx.click();
  const res = await apiPost("/api/action", { action: "save", slot, name });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message || "Infiltration progress saved.", "success");
    state.data = res.state;
    renderHUD(res.state);
    renderSavesModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "Save failed.", "warn");
    if (applyStateSnapshot(res)) renderSavesModal();
  }
}

async function handleRenameSlot(slot, name = "") {
  sfx.click();
  const res = await apiPost("/api/action", { action: "rename_save", slot, name });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message || "Checkpoint renamed.", "success");
    state.data = res.state;
    renderHUD(res.state);
    renderSavesModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "Rename failed.", "warn");
    if (applyStateSnapshot(res)) renderSavesModal();
  }
}

async function handleDeleteSlot(slot, label) {
  const entry = ((state.data && state.data.saves) || []).find((save) => save.slot === slot);
  const suffix = entry && entry.name ? ` (${entry.name})` : "";
  if (!window.confirm(`Delete ${label}${suffix}? The live run is not affected.`)) return;

  sfx.click();
  const res = await apiPost("/api/action", { action: "delete_save", slot });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message || `Deleted ${label} checkpoint.`, "success");
    state.data = res.state;
    renderHUD(res.state);
    renderSavesModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "Delete failed.", "warn");
    if (applyStateSnapshot(res)) renderSavesModal();
  }
}

async function handleLoadSlot(slot) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "load", slot });
  if (res && res.ok) {
    state.selectedNodeId = null;
    closePuzzleBay();
    renderEmptyTargetCard();
    addTerminalLog(res.message || "Loaded saved infiltration session.", "success");
    state.data = res.state;
    renderHUD(res.state);
    document.getElementById("modal-saves").classList.add("hidden");
    document.getElementById("modal-main-menu").classList.add("hidden");
    sfx.success();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "No saved run found.", "warn");
  }
}

async function handleUseExploit(name) {
  sfx.click();
  const target = state.selectedNodeId;
  const res = await apiPost("/api/action", { action: "exploit", name, target });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateExploitChips(res.state.deck.exploits);
    if (state.selectedNodeId) {
      updateTargetCard(state.selectedNodeId);
    }
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Exploit execution failed.", "warn");
    applyStateSnapshot(res);
  }
}

// ==========================================================================
// 7. Interactive Cyberspace Node Matrix Canvas (2D Topology Graph)
// ==========================================================================
function initMatrixCanvas() {
  const canvas = document.getElementById("matrix-canvas");
  const ctx = canvas.getContext("2d");

  function hitNode(clientX, clientY) {
    const pt = toDesignPoint(clientX, clientY);
    for (const [nid, pos] of Object.entries(NODE_POSITIONS)) {
      if (!state.data || !state.data.nodes[nid]) continue;
      if (Math.hypot(pt.x - pos.x, pt.y - pos.y) <= 28) return nid;
    }
    return null;
  }
  // Mouse interaction
  canvas.addEventListener("click", (e) => {
    sfx.init();
    const nid = hitNode(e.clientX, e.clientY);
    if (nid) {
      selectNode(nid);
      sfx.click();
    }
  });
  canvas.addEventListener("mousemove", (e) => {
    const nid = hitNode(e.clientX, e.clientY);
    canvas.style.cursor = nid ? "pointer" : "crosshair";
    const coords = document.getElementById("matrix-coords");
    if (coords && state.data && nid && state.data.nodes[nid]) {
      const n = state.data.nodes[nid];
      coords.textContent = `HOVER // ${(n.hostname || n.node_id).toUpperCase()} · ${n.ip_address || "--"} · ${n.node_type} · SEC ${n.security_level}`;
    } else if (!state.selectedNodeId) {
      updateMatrixCoords();
    } else if (coords && state.data) {
      updateMatrixCoords();
    }
  });
  canvas.addEventListener("mouseleave", () => updateMatrixCoords());

  updateMatrixCoords();

  // Continuous animation loop
  function renderLoop(time) {
    drawMatrix(ctx, time);
    state.animFrameId = requestAnimationFrame(renderLoop);
  }
  state.animFrameId = requestAnimationFrame(renderLoop);
}

function updateMatrixCoords() {
  const coords = document.getElementById("matrix-coords");
  const chip = document.getElementById("matrix-sel-ip");
  if (!coords || !state.data) return;
  const nodes = Object.values(state.data.nodes || {});
  const breached = nodes.filter((n) => n.status === "BREACHED").length;
  coords.textContent = `GRID // ${nodes.length} NODES · ${breached} OPEN`;
  if (!chip) return;
  const sel = state.selectedNodeId ? state.data.nodes[state.selectedNodeId] : null;
  if (!sel) {
    chip.textContent = "NO TARGET";
    chip.classList.remove("hot", "open");
    chip.title = "Selected host address";
    return;
  }
  chip.textContent = `${sel.ip_address || "--"} · ${sel.hostname || sel.node_id}`;
  chip.title = `${sel.name} // ${sel.node_type} // SEC ${sel.security_level} // ${sel.status}`;
  chip.classList.toggle("hot", sel.status === "LOCKED");
  chip.classList.toggle("open", sel.status === "BREACHED");
}

function selectNode(nodeId) {
  state.selectedNodeId = nodeId;
  updateMatrixCoords();
  updateTargetCard(nodeId);
}

function updateTargetCard(nodeId) {
  if (!state.data || !state.data.nodes[nodeId]) return;
  const card = document.getElementById("target-card");
  if (card) card.classList.remove("is-empty");
  const node = state.data.nodes[nodeId];
  const deck = state.data.deck;
  const curr = state.data.current_node;

  const lockedDown = (node.lockdown_until_turn || -1) > (state.data.state.turns_elapsed || 0);
  document.getElementById("target-badge").textContent = lockedDown
    ? `${node.status} · LOCKDOWN`
    : node.status;
  document.getElementById("target-name").textContent = node.name;
  document.getElementById("target-ip").textContent = node.ip_address || "127.0.0.1";
  document.getElementById("target-hostname").textContent = node.hostname || "localhost";
  document.getElementById("target-type").textContent = node.node_type;
  document.getElementById("target-sec").textContent = `LEVEL ${node.security_level}`;
  document.getElementById("target-ram").textContent = `${node.security_level * 16}MB (Deck: ${deck.ram_mb}MB)`;
  document.getElementById("target-trace").textContent = `+${node.trace_rate}%`;
  const distEl = document.getElementById("target-district");
  if (distEl) {
    const dName = node.district || "--";
    const dPatrol = node.district_patrol || "standard";
    distEl.textContent = `${dName} // ${dPatrol.toUpperCase()}`;
    distEl.title = `${dName}: NetWatch patrol ${dPatrol}`;
  }
  const osEl = document.getElementById("target-os");
  if (osEl) {
    osEl.textContent = node.os_name || "Unknown OS";
    osEl.title = `Patch train: ${node.patch_level || "patch-unknown"}`;
  }
  const upEl = document.getElementById("target-uptime");
  if (upEl) {
    const hrs = Number(node.uptime_hours || 0);
    upEl.textContent = hrs >= 24 ? `${(hrs / 24).toFixed(1)}d` : `${hrs}h`;
    upEl.title = `${hrs}h since last reboot - ${node.patch_level || "patch-unknown"}`;
  }
  const routeEl = document.getElementById("target-route");
  if (routeEl) {
    routeEl.textContent = "…";
    fetch(`/api/route?target=${encodeURIComponent(nodeId)}`)
      .then((r) => r.json())
      .then((route) => {
        if (route && route.ok) {
          routeEl.textContent = `${route.hop_count} hops · ${route.total_latency_ms}ms`;
          routeEl.title = route.hops.map((h, i) => `${i + 1}. ${h.hostname} (${h.ip_address}) +${h.latency_ms}ms`).join("\n");
        } else {
          routeEl.textContent = "unreachable";
          routeEl.title = (route && route.reason) || "No route from current host.";
        }
      })
      .catch(() => { routeEl.textContent = "--"; });
  }

  // Firewall Status Indicator
  const fwEl = document.getElementById("target-firewall");
  if (fwEl) {
    if (node.firewall && node.firewall.enabled) {
      const blockedRules = (node.firewall.rules || []).filter(r => r.action === "BLOCK");
      const activeBlocks = blockedRules.filter(r => !r.bypassed);
      if (activeBlocks.length > 0) {
        fwEl.textContent = `FILTERING (${activeBlocks.length} BLOCKED)`;
        fwEl.className = "val fw-blocked";
      } else if (blockedRules.length > 0) {
        fwEl.textContent = "BYPASSED";
        fwEl.className = "val fw-bypassed";
      } else {
        fwEl.textContent = "ALLOW ALL";
        fwEl.className = "val fw-allowed";
      }
    } else {
      fwEl.textContent = "DISABLED";
      fwEl.className = "val";
    }
  }

  // Antivirus / EDR Indicator
  const avEl = document.getElementById("target-antivirus");
  if (avEl) {
    if (node.antivirus && node.antivirus.enabled) {
      if (node.antivirus.evaded) {
        avEl.textContent = `${node.antivirus.name} [EVADED]`;
        avEl.className = "val av-evaded";
      } else {
        const alertLvl = node.antivirus.alert_level || 0;
        avEl.textContent = `${node.antivirus.name} (${alertLvl}%)`;
        if (alertLvl >= 50) {
          avEl.className = "val av-alert-high";
        } else if (alertLvl >= 20) {
          avEl.className = "val av-alert-med";
        } else {
          avEl.className = "val";
        }
      }
    } else {
      avEl.textContent = "NONE";
      avEl.className = "val";
    }
  }

  const btnProbe = document.getElementById("btn-probe-node");
  const btnHack = document.getElementById("btn-init-hack");
  const btnMove = document.getElementById("btn-move-node");
  const btnKeylogger = document.getElementById("btn-keylogger-node");
  const btnWipe = document.getElementById("btn-wipe-logs");
  const btnBypass = document.getElementById("btn-bypass-fw");
  const btnEvade = document.getElementById("btn-evade-av");
  const btnSocial = document.getElementById("btn-social-eng");
  const btnQuickhack = document.getElementById("btn-quickhack");
  const btnProxy = document.getElementById("btn-proxy-node");


  const isAdjacent = curr.connected_ids.includes(nodeId) || curr.node_id === nodeId;
  const isBreached = node.status === "BREACHED";

  btnProbe.disabled = node.status === "LOCKED" && !isAdjacent;
  btnHack.disabled = isBreached || !isAdjacent || lockedDown;
  btnHack.title = lockedDown
    ? `Host ICE is rotating until turn ${node.lockdown_until_turn}. Lay low or target another host.`
    : (node.district_patrol === "heavy" && !isBreached
      ? `Initiate intrusion. WARNING: ${node.district || "district"} patrols are heavy (+1% district heat trace).`
      : "Initiate intrusion.");
  btnMove.disabled = !isBreached || curr.node_id === nodeId;
  btnKeylogger.disabled = !isBreached;
  btnWipe.disabled = !isBreached;

  if (btnBypass) {
    const hasBlocked = node.firewall && node.firewall.enabled && (node.firewall.rules || []).some(r => r.action === "BLOCK" && !r.bypassed);
    btnBypass.disabled = !isAdjacent || !hasBlocked || isBreached;
  }
  if (btnEvade) {
    const hasAv = node.antivirus && node.antivirus.enabled && !node.antivirus.evaded;
    btnEvade.disabled = !isAdjacent || !hasAv;
  }
  if (btnSocial) {
    btnSocial.disabled = isBreached || (node.status === "LOCKED" && !isAdjacent);
  }
  if (btnQuickhack) {
    btnQuickhack.disabled = isBreached || !isAdjacent || lockedDown || node.security_level > 2;
    if (!btnQuickhack.disabled) {
      fetch(`/api/forecast?action=quickhack&target=${encodeURIComponent(nodeId)}`)
        .then((r) => r.json())
        .then((fc) => {
          if (fc && fc.ok) {
            btnQuickhack.title = `Quickhack ${node.hostname}: ${-fc.cpu_delta} CPU, +${fc.trace_gain}% trace (mitigated), 1 turn. Skips the mini-game.`;
          }
        })
        .catch(() => {});
    }
    btnQuickhack.title = node.security_level > 2
      ? "Quickhack cannot pierce security tier 3+; probe and exploit instead."
      : "Instant breach: steep CPU and trace cost, no mini-game.";
    btnQuickhack.classList.toggle("available", !btnQuickhack.disabled);
  }
  if (btnProxy) {
    const chain = deck.proxy_chain || [];
    btnProxy.disabled = !isBreached || curr.node_id === nodeId || chain.includes(nodeId) || chain.length >= 3;
    btnProxy.title = chain.length >= 3
      ? "Proxy chain is full (3 hops)."
      : "Route telemetry through this breached host (-15% trace per hop, 1 CPU).";
  }

  if (isBreached) {
    document.getElementById("probed-ports-container").classList.add("hidden");
    loadFilesystemView(nodeId);
  } else if ((state.data.state.probed_nodes || []).includes(nodeId) && node.ports && node.ports.length > 0) {
    renderProbedPortsBay(node);
  } else {
    document.getElementById("probed-ports-container").classList.add("hidden");
    document.getElementById("filesystem-container").classList.add("hidden");
    document.getElementById("puzzle-idle").classList.remove("hidden");
  }
}

function renderProbedPortsBay(node) {
  const container = document.getElementById("probed-ports-container");
  const grid = document.getElementById("probed-ports-grid");
  document.getElementById("probed-target-host").textContent = `${node.hostname} (${node.ip_address})`;

  document.getElementById("puzzle-idle").classList.add("hidden");
  document.getElementById("filesystem-container").classList.add("hidden");
  document.getElementById("puzzle-frequency").classList.add("hidden");
  document.getElementById("puzzle-buffer").classList.add("hidden");
  document.getElementById("puzzle-hash").classList.add("hidden");
  container.classList.remove("hidden");

  grid.innerHTML = "";
  if (!node.ports || node.ports.length === 0) {
    grid.innerHTML = '<div style="color:var(--c-text-dim); font-size:11px; padding:6px;">No open ports identified. Click PROBE PORTS [P] to scan.</div>';
    return;
  }

  node.ports.forEach((p) => {
    const card = document.createElement("div");
    card.className = "probed-port-card";

    let fwBlocked = false;
    let fwBypassed = false;
    if (node.firewall && node.firewall.enabled) {
      const rule = (node.firewall.rules || []).find(r => r.port === p.port);
      if (rule) {
        if (rule.bypassed) fwBypassed = true;
        else if (rule.action === "BLOCK") fwBlocked = true;
      }
    }

    let badgeClass = "badge-secure";
    let badgeText = "SECURE";
    if (p.breached) {
      badgeClass = "badge-breached";
      badgeText = "BREACHED";
    } else if (fwBlocked) {
      badgeClass = "badge-blocked";
      badgeText = "FW BLOCKED";
    } else if (p.vulnerable) {
      badgeClass = "badge-vuln";
      badgeText = "VULNERABLE";
    }

    const fwNotice = fwBypassed ? '<span style="color:var(--c-warning); font-size:9px;">[FW BYPASSED]</span> ' : '';

    card.innerHTML = `
      <div class="port-card-info">
        <div class="port-card-title">PORT ${p.port}/tcp : ${p.service.toUpperCase()} ${fwNotice}</div>
        <div class="port-card-service">${p.version || "Service Banner"}</div>
        <span class="port-status-badge ${badgeClass}">${badgeText}</span>
      </div>
      <div class="port-card-actions">
        ${fwBlocked ? `<button class="port-action-btn bypass-btn" data-port="${p.port}">BYPASS FW</button>` : ''}
        ${p.vulnerable && !p.breached && !fwBlocked ? `<button class="port-action-btn exploit-btn" data-port="${p.port}">EXPLOIT</button>` : ''}
      </div>
    `;

    const bypassBtn = card.querySelector(".bypass-btn");
    if (bypassBtn) {
      bypassBtn.onclick = (e) => {
        e.stopPropagation();
        openBypassModal(p.port);
      };
    }

    const exploitBtn = card.querySelector(".exploit-btn");
    if (exploitBtn) {
      exploitBtn.onclick = async (e) => {
        e.stopPropagation();
        sfx.click();
        addTerminalLog(`⚡ Launching targeted exploit against port ${p.port}/tcp (${p.service})...`, "info");
        const res = await apiPost("/api/action", {
          action: "exploit_service",
          target: node.node_id,
          port: p.port,
        });
        if (res && res.ok) {
          sfx.success();
          addTerminalLog(res.message, "success");
          state.data = res.state;
          renderHUD(res.state);
          updateTargetCard(node.node_id);
          loadFilesystemView(node.node_id);
        } else if (res) {
          sfx.failure();
          addTerminalLog(res.message || "Exploit execution failed.", "danger");
          state.data = res.state;
          renderHUD(res.state);
        }
      };
    }

    grid.appendChild(card);
  });
}

async function loadFilesystemView(nodeId) {
  const node = state.data.nodes[nodeId];
  if (!node || node.status !== "BREACHED") {
    document.getElementById("filesystem-container").classList.add("hidden");
    return;
  }

  document.getElementById("puzzle-idle").classList.add("hidden");
  document.getElementById("puzzle-frequency").classList.add("hidden");
  document.getElementById("puzzle-buffer").classList.add("hidden");
  document.getElementById("puzzle-hash").classList.add("hidden");
  document.getElementById("probed-ports-container").classList.add("hidden");
  document.getElementById("filesystem-container").classList.remove("hidden");
  document.getElementById("fs-target-host").textContent = `${node.hostname} (${node.ip_address})`;

  const portsList = document.getElementById("target-ports-list");
  portsList.innerHTML = "";
  if (node.ports && node.ports.length > 0) {
    node.ports.forEach((p) => {
      const pDiv = document.createElement("div");
      pDiv.className = "port-item";
      let fwTag = "";
      if (node.firewall && node.firewall.enabled) {
        const rule = (node.firewall.rules || []).find(r => r.port === p.port);
        if (rule) {
          if (rule.bypassed) {
            fwTag = ' <span style="color:var(--c-warning); font-size:9px;">[FW: BYPASSED]</span>';
          } else if (rule.action === "BLOCK") {
            fwTag = ' <span style="color:var(--c-danger); font-size:9px;">[FW: BLOCKED]</span>';
          }
        }
      }
      const tagClass = p.breached ? "port-tag-breached" : (p.vulnerable ? "port-tag-vulnerable" : "");
      const tagText = p.breached ? "BREACHED" : (p.vulnerable ? "VULNERABLE" : "SECURE");
      pDiv.innerHTML = `<span><strong>${p.port}/tcp</strong> ${p.service} (${p.version})${fwTag}</span><span class="${tagClass}">[${tagText}]</span>`;
      portsList.appendChild(pDiv);
    });
  }

  const res = await apiPost("/api/action", { action: "list_files", target: nodeId });
  const tbody = document.getElementById("fs-file-tbody");
  tbody.innerHTML = "";
  if (res && res.ok && res.files) {
    res.files.forEach((f) => {
      const tr = document.createElement("tr");
      const targetMark = f.is_target_data ? '<strong class="highlight-value">★ TARGET</strong>' : "";
      const valStr = f.value_creds > 0 ? `${f.value_creds} CR` : "---";
      tr.innerHTML = `
        <td>${f.path} ${targetMark}</td>
        <td>${f.size_kb}KB</td>
        <td>${valStr}</td>
        <td>
          <button class="icon-btn small-btn btn-cat" data-path="${f.path}">CAT</button>
          <button class="icon-btn small-btn btn-steal" data-path="${f.path}">STEAL</button>
        </td>
      `;
      tr.querySelector(".btn-cat").addEventListener("click", () => handleCatFile(nodeId, f.path));
      tr.querySelector(".btn-steal").addEventListener("click", () => handleStealFile(nodeId, f.path));
      tbody.appendChild(tr);
    });
  }
}

const NODE_SPRITES = {
  GATEWAY: { shape: "diamond", glow: "185, 100%, 55%", core: "hsl(185, 100%, 62%)", glyph: "◆" },
  FIREWALL: { shape: "hexagon", glow: "42, 100%, 60%", core: "hsl(42, 100%, 62%)", glyph: "⬡" },
  DATA_VAULT: { shape: "vault", glow: "145, 95%, 58%", core: "hsl(145, 95%, 60%)", glyph: "▤" },
  ICE_DEFENSE: { shape: "triangle", glow: "352, 100%, 64%", core: "hsl(352, 100%, 64%)", glyph: "▲" },
  CENTRAL_CORE: { shape: "core", glow: "315, 100%, 68%", core: "hsl(315, 100%, 70%)", glyph: "⬢" },
};

const ENTITY_SPRITES = {
  mira: { glyph: "\u25C6", cls: "avatar-fixer" },
  kilo: { glyph: "\u2B22", cls: "avatar-techie" },
  archivist: { glyph: "\u2524", cls: "avatar-broker" },
  zero: { glyph: "\u2B23", cls: "avatar-zero" },
  Vex: { glyph: "\u2715", cls: "avatar-rival-vex" },
  Marrow: { glyph: "\u25CD", cls: "avatar-rival-marrow" },
  Static: { glyph: "\u26A1", cls: "avatar-rival-static" },
  hunter: { glyph: "\u25C9", cls: "avatar-hunter" },
  logic_bomb: { glyph: "\u2738", cls: "item-exploit" },
  ghost_protocol: { glyph: "\u25C8", cls: "item-exploit" },
  overclock_cpu: { glyph: "\u26A1", cls: "item-hardware" },
  expand_ram: { glyph: "\u2524", cls: "item-hardware" },
  ice_dampener: { glyph: "\u2744", cls: "item-hardware" },
  dead_mans_switch: { glyph: "\u26E8", cls: "item-consumable" },
};

function avatarHTML(key, fallback) {
  const meta = ENTITY_SPRITES[key] || ENTITY_SPRITES[fallback] || { glyph: "\u25C7", cls: "avatar-unknown" };
  return `<span class="entity-avatar ${meta.cls}" aria-hidden="true">${meta.glyph}</span>`;
}

function puzzleFlash(kind) {
  if (!motionSafe()) return;
  const bay = document.getElementById("puzzle-bay");
  if (!bay) return;
  bay.classList.remove("flash-success", "flash-near", "shake");
  void bay.offsetWidth;
  bay.classList.add(kind === "success" ? "flash-success" : kind === "near" ? "flash-near" : "shake");
  setTimeout(() => bay.classList.remove("flash-success", "flash-near", "shake"), 420);
}

function motionSafe() {
  try {
    return !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (_) { return true; }
}

function traceBurst(sx, sy, color, n) {
  const stage = document.getElementById("matrix-stage");
  if (stage && motionSafe()) {
    stage.classList.add("breach-flash");
    setTimeout(() => stage.classList.remove("breach-flash"), 320);
  }
  if (!motionSafe()) return;
  const vp = matrixViewport();
  const inv = 1 / Math.max(0.001, vp.scale);
  for (let i = 0; i < (n || 10); i++) {
    const a = Math.random() * Math.PI * 2;
    const sp = 0.6 + Math.random() * 2.2;
    state.packetParticles.push({ x: (sx - vp.offX) * inv, y: (sy - vp.offY) * inv, vx: Math.cos(a) * sp * inv, vy: Math.sin(a) * sp * inv, life: 1, color });
  }
  if (state.packetParticles.length > 320) {
    state.packetParticles.splice(0, state.packetParticles.length - 320);
  }
}

function drawSpriteShape(ctx, shape, cx, cy, r, rot) {
  ctx.beginPath();
  if (shape === "diamond") {
    ctx.moveTo(cx, cy - r); ctx.lineTo(cx + r * 0.8, cy);
    ctx.lineTo(cx, cy + r); ctx.lineTo(cx - r * 0.8, cy);
    ctx.closePath();
  } else if (shape === "triangle") {
    for (let i = 0; i < 3; i++) {
      const a = (rot || 0) + i * (Math.PI * 2 / 3) - Math.PI / 2;
      const px = cx + Math.cos(a) * r, py = cy + Math.sin(a) * r;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
  } else if (shape === "hexagon") {
    for (let i = 0; i < 6; i++) {
      const a = (rot || 0) + i * (Math.PI / 3);
      const px = cx + Math.cos(a) * r, py = cy + Math.sin(a) * r;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
  } else if (shape === "vault") {
    const w = r * 1.7, h = r * 1.4;
    ctx.rect(cx - w / 2, cy - h / 2, w, h);
  } else if (shape === "core") {
    for (let i = 0; i < 8; i++) {
      const a = (rot || 0) + i * (Math.PI / 4);
      const px = cx + Math.cos(a) * r, py = cy + Math.sin(a) * r;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
  } else {
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
  }
}

let lastBreachSig = "";
function drawMatrix(ctx, time) {
  const view = matrixViewport();
  ctx.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
  ctx.clearRect(0, 0, view.cssW, view.cssH);

  if (!state.stars) {
    state.stars = [];
    for (let i = 0; i < 90; i++) {
      state.stars.push({ x: Math.random() * DESIGN_W, y: Math.random() * DESIGN_H, r: 0.4 + Math.random() * 1.1, tw: Math.random() * Math.PI * 2 });
    }
  }
  if (!state.data) return;
  // Deep-space backdrop: nebula wash + faint grid + drifting stars + scan sweep
  ctx.save();
  {
    const nx = view.offX, ny = view.offY, nw = DESIGN_W * view.scale, nh = DESIGN_H * view.scale;
    let neb = ctx.createRadialGradient(nx + nw * 0.22, ny + nh * 0.28, 10, nx + nw * 0.22, ny + nh * 0.28, Math.max(nw, nh) * 0.45);
    neb.addColorStop(0, 'rgba(40,140,190,0.07)');
    neb.addColorStop(1, 'rgba(40,140,190,0)');
    ctx.fillStyle = neb;
    ctx.fillRect(nx, ny, nw, nh);
    neb = ctx.createRadialGradient(nx + nw * 0.82, ny + nh * 0.8, 10, nx + nw * 0.82, ny + nh * 0.8, Math.max(nw, nh) * 0.4);
    neb.addColorStop(0, 'rgba(190,60,140,0.05)');
    neb.addColorStop(1, 'rgba(190,60,140,0)');
    ctx.fillStyle = neb;
    ctx.fillRect(nx, ny, nw, nh);
  }
  ctx.strokeStyle = 'rgba(110,170,200,0.05)';
  ctx.lineWidth = 1;
  for (let gx = 0; gx <= DESIGN_W; gx += 56) {
    ctx.beginPath();
    const gxPx = view.offX + gx * view.scale;
    ctx.moveTo(gxPx, view.offY); ctx.lineTo(gxPx, view.offY + DESIGN_H * view.scale);
    ctx.stroke();
  }
  for (let gy = 0; gy <= DESIGN_H; gy += 56) {
    ctx.beginPath();
    const gyPx = view.offY + gy * view.scale;
    ctx.moveTo(view.offX, gyPx); ctx.lineTo(view.offX + DESIGN_W * view.scale, gyPx);
    ctx.stroke();
  }
  for (const st of state.stars) {
    const sa = motionSafe() ? 0.25 + 0.35 * Math.abs(Math.sin(time * 0.001 + st.tw)) : 0.3;
    ctx.beginPath();
    ctx.arc(view.offX + st.x * view.scale, view.offY + st.y * view.scale, st.r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(150,210,240,' + sa.toFixed(2) + ')';
    ctx.fill();
  }
  if (motionSafe()) {
    const sweepY = view.offY + ((time * 0.035) % (DESIGN_H * view.scale + 80)) - 40;
    const grad = ctx.createLinearGradient(0, sweepY - 26, 0, sweepY);
    grad.addColorStop(0, 'rgba(90,220,255,0)');
    grad.addColorStop(1, 'rgba(90,220,255,0.07)');
    ctx.fillStyle = grad;
    ctx.fillRect(view.offX, sweepY - 26, DESIGN_W * view.scale, 26);
  }
  ctx.restore();

  const nodes = state.data.nodes;
  const currNodeId = state.data.state.current_node_id;

  // Project design-space coordinates into fixed-size screen coordinates so that
  // node glyphs and labels stay legible at any panel size.
  const sx = (x) => view.offX + x * view.scale;
  const sy = (y) => view.offY + y * view.scale;
  const compact = view.scale < 0.8;
  // Labels are painted in CSS px while positions shrink with view.scale, so
  // scale fonts down on narrow panels to keep neighbours from colliding.
  const labelScale = Math.max(0.7, Math.min(1, view.scale));
  const nodeR = compact ? 16 : 20;
  const coreR = compact ? 7 : 9;
  const labelSize = (compact ? 10 : 11) * labelScale;
  const ipSize = (compact ? 8.5 : 9) * labelScale;
  const tagSize = 8 * labelScale;

  // 1. Draw Network Connection Edges
  for (const [nid, node] of Object.entries(nodes)) {
    const p1 = NODE_POSITIONS[nid];
    if (!p1) continue;

    for (const cid of node.connected_ids) {
      const p2 = NODE_POSITIONS[cid];
      if (!p2 || nid > cid) continue; // Draw each edge once

      const x1 = sx(p1.x);
      const y1 = sy(p1.y);
      const x2 = sx(p2.x);
      const y2 = sy(p2.y);

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      // Flowing energy pulses: breached links glow green, sealed links dim cyan.
      const breachedLink = nodes[nid] && nodes[cid] && nodes[nid].status === "BREACHED" && nodes[cid].status === "BREACHED";
      ctx.strokeStyle = breachedLink ? "rgba(80, 255, 150, 0.4)" : "rgba(40, 160, 90, 0.24)";
      ctx.lineWidth = breachedLink ? 2.25 : 1.5;
      ctx.stroke();
      const flow = motionSafe() ? time * 0.0009 : 0;
      for (let k = 0; k < 2; k++) {
        const packetPhase = (flow + (p1.x * 0.013) + k * 0.5) % 1;
        const px = x1 + (x2 - x1) * packetPhase;
        const py = y1 + (y2 - y1) * packetPhase;
        const tail = 0.35 + 0.65 * Math.abs(Math.sin(packetPhase * Math.PI));
        ctx.beginPath();
        ctx.arc(px, py, breachedLink ? 2.6 : 1.8, 0, Math.PI * 2);
        ctx.fillStyle = breachedLink
          ? `rgba(80, 255, 150, ${0.35 + 0.45 * tail})`
          : `rgba(90, 220, 255, ${0.2 + 0.35 * tail})`;
        ctx.shadowBlur = breachedLink ? 8 : 5;
        ctx.shadowColor = breachedLink ? "rgba(80,255,150,0.8)" : "rgba(90,220,255,0.7)";
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }
  }

  // 2. Draw Host Nodes
  for (const [nid, node] of Object.entries(nodes)) {
    const pos = NODE_POSITIONS[nid];
    if (!pos) continue;

    const cx = sx(pos.x);
    const cy = sy(pos.y);
    const isCurrent = nid === currNodeId;
    const isSelected = nid === state.selectedNodeId;
    const isBreached = node.status === "BREACHED";
    const isDiscovered = node.status === "DISCOVERED";

    const sprite = NODE_SPRITES[node.node_type] || NODE_SPRITES.GATEWAY;
    const pulse = motionSafe() ? Math.sin(time * 0.003 + pos.x * 0.05) : 0;
    const breathe = 1 + pulse * 0.04;
    const R = nodeR * breathe;
    // Soft halo under every sprite
    const halo = ctx.createRadialGradient(cx, cy, 2, cx, cy, R + 14);
    if (isCurrent) { halo.addColorStop(0, "rgba(90,220,255,0.22)"); halo.addColorStop(1, "rgba(90,220,255,0)"); }
    else if (isBreached) { halo.addColorStop(0, "rgba(80,255,150,0.20)"); halo.addColorStop(1, "rgba(80,255,150,0)"); }
    else if (isDiscovered) { halo.addColorStop(0, "rgba(255,190,80,0.16)"); halo.addColorStop(1, "rgba(255,190,80,0)"); }
    else { halo.addColorStop(0, "rgba(120,140,160,0.10)"); halo.addColorStop(1, "rgba(120,140,160,0)"); }
    ctx.fillStyle = halo;
    ctx.beginPath(); ctx.arc(cx, cy, R + 14, 0, Math.PI * 2); ctx.fill();
    // Lockdown rotating dashed ring
    const lockedDown = (node.lockdown_until_turn || -1) > ((state.data.state && state.data.state.turns_elapsed) || 0);
    if (lockedDown) {
      ctx.beginPath();
      ctx.arc(cx, cy, R + 5, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255,80,90,0.7)";
      ctx.lineWidth = 1.2;
      ctx.setLineDash([3, 5]);
      ctx.lineDashOffset = motionSafe() ? -time * 0.02 : 0;
      ctx.stroke();
      ctx.setLineDash([]);
    }
    // Glowing Outer Ring (sprite-shaped)
    if (isCurrent) {
      ctx.fillStyle = "rgba(90, 220, 255, 0.14)";
      ctx.strokeStyle = "hsl(185, 100%, 62%)";
      ctx.lineWidth = 2;
    } else if (isBreached) {
      ctx.fillStyle = "rgba(80, 255, 150, 0.12)";
      ctx.strokeStyle = sprite.core;
      ctx.lineWidth = 1.6;
    } else if (isDiscovered) {
      ctx.fillStyle = "rgba(255, 190, 80, 0.09)";
      ctx.strokeStyle = "hsl(45, 100%, 60%)";
      ctx.lineWidth = 1.3;
    } else {
      ctx.fillStyle = "rgba(40, 44, 54, 0.45)";
      ctx.strokeStyle = "rgba(140, 150, 165, 0.4)";
      ctx.lineWidth = 1;
    }
    drawSpriteShape(ctx, sprite.shape, cx, cy, R, motionSafe() ? time * 0.0004 : 0);
    ctx.fill();
    ctx.stroke();
    // Inner etched glyph ring for type readability
    drawSpriteShape(ctx, sprite.shape, cx, cy, R * 0.55, motionSafe() ? -time * 0.0006 : 0);
    ctx.strokeStyle = isBreached || isCurrent ? sprite.core : "rgba(160,170,185,0.35)";
    ctx.lineWidth = 1;
    ctx.stroke();

    // Node Center Icon / Circle (current node cools cyan, heats red with trace)
    const traceHeat = isCurrent
      ? Math.max(0, Math.min(1, (((state.data.state && state.data.state.trace_percent) || 0) - 25) / 75))
      : 0;
    const currentCore = traceHeat > 0
      ? `hsl(${Math.round(185 - 150 * traceHeat)}, 100%, ${Math.round(60 - 4 * traceHeat)}%)`
      : "hsl(185, 100%, 60%)";
    ctx.beginPath();
    ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
    ctx.fillStyle = isCurrent
      ? currentCore
      : (isBreached ? sprite.core : (isDiscovered ? "hsl(45, 100%, 58%)" : "#3c4450"));
    ctx.shadowBlur = (isBreached || isCurrent) ? 10 + (Number(node.security_level) || 1) * 1.5 : (Number(node.security_level) || 0);
    ctx.shadowColor = (isBreached || isCurrent) ? sprite.core : "rgba(140,150,165,0.35)";
    ctx.fill();
    ctx.shadowBlur = 0;

    // Breached hosts wear a thin outer trace-ring in their sprite color.
    if (isBreached) {
      ctx.beginPath();
      ctx.arc(cx, cy, R + 4, 0, Math.PI * 2);
      ctx.globalAlpha = 0.45;
      ctx.strokeStyle = sprite.core;
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Type glyph etched into the core dot (dark on lit cores, lit on dim ones).
    ctx.font = `${Math.max(8, coreR * 1.1)}px 'Cascadia Mono', 'Consolas', monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.globalAlpha = isBreached || isCurrent ? 0.9 : 0.75;
    ctx.fillStyle = (isBreached || isCurrent) ? "rgba(4, 10, 12, 0.9)" : sprite.core;
    ctx.fillText(sprite.glyph || "◆", cx, cy + 0.5);
    ctx.globalAlpha = 1;
    ctx.textBaseline = "alphabetic";

    // Heavy-patrol district ring: hosts on NetWatch's active sweep grid
    // wear a dashed red cordon so hot streets read at a glance.
    if (node.district_patrol === "heavy" && !isBreached) {
      ctx.save();
      ctx.strokeStyle = "rgba(255,70,70,0.55)";
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.arc(cx, cy, coreR + 6, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    // Target Selection Halo (rotating corner brackets)
    if (isSelected) {
      const rr = R + 8;
      const rot = motionSafe() ? time * 0.0012 : 0;
      ctx.save();
      ctx.translate(cx, cy); ctx.rotate(rot);
      ctx.strokeStyle = "rgba(255,255,255,0.85)";
      ctx.lineWidth = 1.4;
      for (let q = 0; q < 4; q++) {
        const a0 = q * Math.PI / 2;
        ctx.beginPath();
        ctx.arc(0, 0, rr, a0, a0 + 0.5);
        ctx.stroke();
      }
      ctx.restore();
    }

    // Node Label & IP (side hosts hide their name on narrow panels unless
    // selected; IP pill + type tag still identify them).
    const isSideHost = !!SIDE_NODE_SLOTS[nid];
    ctx.textAlign = "center";
    ctx.font = `600 ${labelSize}px 'Cascadia Mono', 'Consolas', monospace`;
    ctx.fillStyle = isCurrent
      ? "hsl(185, 100%, 88%)"
      : (isBreached ? "hsl(140, 60%, 74%)" : (isDiscovered ? "hsl(45, 55%, 78%)" : "rgba(170, 180, 195, 0.7)"));
    if (!compact || !isSideHost || isSelected) {
      ctx.save();
      ctx.strokeStyle = "rgba(2, 6, 8, 0.9)";
      ctx.lineWidth = 3;
      ctx.strokeText(pos.label, cx, cy + nodeR + 15);
      ctx.restore();
      ctx.fillText(pos.label, cx, cy + nodeR + 15);
    }

    ctx.font = `${ipSize}px 'Cascadia Mono', 'Consolas', monospace`;
    {
      const ipText = node.ip_address || "";
      const ipW = ctx.measureText(ipText).width;
      const pillW = ipW + 10, pillH = ipSize + 7;
      const px = cx - pillW / 2, py = cy + nodeR + 28 - pillH / 2 - 1;
      ctx.fillStyle = isSelected
        ? "rgba(10, 18, 24, 0.92)"
        : isCurrent
          ? "rgba(6, 20, 26, 0.85)"
          : "rgba(4, 8, 12, 0.78)";
      ctx.strokeStyle = isSelected
        ? "rgba(255,255,255,0.7)"
        : isCurrent
          ? "hsl(185, 100%, 55%)"
          : (isBreached ? "hsla(145, 95%, 58%, 0.5)" : (isDiscovered ? "hsla(45, 100%, 52%, 0.4)" : "rgba(140, 150, 165, 0.25)"));
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(px, py, pillW, pillH, 3);
      else ctx.rect(px, py, pillW, pillH);
      ctx.fill();
      ctx.stroke();
    }
    ctx.fillStyle = isSelected || isCurrent
      ? "hsl(185, 100%, 90%)"
      : (isBreached
        ? "rgba(140, 255, 190, 0.95)"
        : (isDiscovered ? "rgba(255, 210, 110, 0.9)" : "rgba(180, 190, 205, 0.8)"));
    ctx.save();
    ctx.strokeStyle = "rgba(2, 6, 8, 0.9)";
    ctx.lineWidth = 3;
    ctx.strokeText(node.ip_address || "", cx, cy + nodeR + 28);
    ctx.restore();
    ctx.fillText(node.ip_address || "", cx, cy + nodeR + 28);

    if (isCurrent) {
      ctx.font = `700 ${tagSize}px 'Cascadia Mono', 'Consolas', monospace`;
      ctx.fillStyle = "rgba(0, 230, 255, 0.85)";
      ctx.fillText("ACTIVE TERMINAL", cx, cy - nodeR - 10);
    }

    // Breach celebration particles (fires once per newly breached node)
    const breachSig = nid + ":" + (isBreached ? "1" : "0");
    if (isBreached && lastBreachSig !== "__init__") {
      state._seenBreaches = state._seenBreaches || {};
      if (!state._seenBreaches[nid]) {
        state._seenBreaches[nid] = true;
        traceBurst(cx, cy, "120,255,170", 22);
      }
    }
    // Check if an active NetWatch Hunter is at this node
    const huntersAtNode = (state.data && state.data.world && state.data.world.hunters)
      ? state.data.world.hunters.filter(h => h.current_node_id === nid && h.status !== "neutralized")
      : [];
    if (huntersAtNode.length > 0) {
      const pulse = motionSafe() ? Math.sin(time * 0.006) * 3 : 0;
      ctx.save();
      ctx.translate(cx, cy); ctx.rotate(motionSafe() ? time * 0.001 : 0);
      ctx.strokeStyle = "rgba(255, 30, 60, 0.9)";
      ctx.lineWidth = 2;
      const hr = nodeR + 10 + pulse;
      for (let q = 0; q < 4; q++) {
        const a0 = q * Math.PI / 2 + Math.PI / 4;
        ctx.beginPath(); ctx.arc(0, 0, hr, a0, a0 + 0.42); ctx.stroke();
      }
      ctx.restore();
      ctx.beginPath();
      ctx.arc(cx, cy, nodeR + 8 + pulse, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255, 30, 60, 0.35)";
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.font = `700 ${tagSize}px 'Cascadia Mono', 'Consolas', monospace`;
      ctx.fillStyle = "rgba(255, 70, 90, 0.95)";
      ctx.fillText(
        `HUNTER: ${huntersAtNode[0].name.toUpperCase()}`,
        cx,
        cy - nodeR - (isCurrent ? 24 : 10)
      );
    }
    // Type tag under IP for fast scanning
    ctx.font = `700 ${tagSize}px 'Cascadia Mono', 'Consolas', monospace`;
    ctx.fillStyle = isBreached ? "rgba(140,255,190,0.75)" : "rgba(140,150,165,0.5)";
    const spriteTag = (NODE_SPRITES[node.node_type] || NODE_SPRITES.GATEWAY).shape.toUpperCase();
    ctx.save();
    ctx.strokeStyle = "rgba(2, 6, 8, 0.9)";
    ctx.lineWidth = 3;
    ctx.strokeText(spriteTag, cx, cy + nodeR + 40);
    ctx.restore();
    ctx.fillText(spriteTag, cx, cy + nodeR + 40);
  }
  lastBreachSig = "__init__";
  // Particle integrator (breach sparks drift and fade)
  if (state.packetParticles.length) {
    const dt = 1;
    state.packetParticles = state.packetParticles.filter((pt) => pt.life > 0);
  for (const pt of state.packetParticles) {
    const vpx = view.offX + (pt.x / DESIGN_W) * view.cssW;
    void vpx;
    pt.x += pt.vx * dt; pt.y += pt.vy * dt; pt.vx *= 0.965; pt.vy *= 0.965; pt.life -= 0.014;
    const sxp = view.offX + pt.x * view.scale;
    const syp = view.offY + pt.y * view.scale;
    ctx.beginPath();
    ctx.arc(sxp, syp, 2.4 * Math.max(0, pt.life), 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${pt.color},${Math.max(0, pt.life).toFixed(2)})`;
      ctx.fill();
    }
  }
}

// ==========================================================================
// 8. Move, Probe & Intrusion Handlers
// ==========================================================================
async function handleMoveNode() {
  if (!state.selectedNodeId) return;
  sfx.click();
  const res = await apiPost("/api/action", { action: "move", target: state.selectedNodeId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
    if (state.data.nodes[state.selectedNodeId].status === "BREACHED") {
      loadFilesystemView(state.selectedNodeId);
    }
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Move disallowed.", "warn");
  }
}

async function handleProbeNode() {
  if (!state.selectedNodeId) return;
  sfx.scan();
  addTerminalLog(`Scanning open ports on ${state.selectedNodeId}...`, "info");
  const res = await apiPost("/api/action", { action: "probe", target: state.selectedNodeId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
    if (state.data.nodes[state.selectedNodeId] && state.data.nodes[state.selectedNodeId].status !== "BREACHED") {
      renderProbedPortsBay(state.data.nodes[state.selectedNodeId]);
    }
    if (res.report && res.report.ports) {
      res.report.ports.forEach((p) => {
        addTerminalLog(`  [PORT ${p.port}/tcp] ${p.service} (${p.version}) - ${p.vulnerable ? 'VULNERABLE' : 'SECURE'}`, p.vulnerable ? 'warn' : 'info');
      });
    }
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Port scan failed.", "warn");
  }
}

async function handleStartHack() {
  if (!state.selectedNodeId) return;
  const node = state.data.nodes[state.selectedNodeId];
  if (!node) return;

  // 1-Click Zero-Day Exploit if vulnerable port is present
  const vulnPort = (node.ports || []).find(p => p.vulnerable && !p.breached);
  if (vulnPort) {
    sfx.click();
    addTerminalLog(`⚡ Infiltrating via port ${vulnPort.port}/tcp (${vulnPort.service})...`, "info");
    const res = await apiPost("/api/action", {
      action: "exploit_service",
      target: state.selectedNodeId,
      port: vulnPort.port,
    });
    if (res && res.ok) {
      sfx.success();
      addTerminalLog(res.message, "success");
      state.data = res.state;
      renderHUD(res.state);
      updateTargetCard(state.selectedNodeId);
      loadFilesystemView(state.selectedNodeId);
      return;
    } else if (res) {
      sfx.failure();
      addTerminalLog(res.message || "Exploit payload failed.", "danger");
      state.data = res.state;
      renderHUD(res.state);
      return;
    }
  }

  // Fallback to minigame puzzle
  sfx.click();
  const data = await apiGet(`/api/puzzle?node_id=${state.selectedNodeId}`);
  if (!data || !data.ok) {
    sfx.failure();
    addTerminalLog(data ? data.error : "Failed to initiate intrusion.", "warn");
    return;
  }

  sfx.scan();
  addTerminalLog(`⚡ Commencing cyber-attack on ${data.node_name}...`, "info");
  state.activePuzzle = data;
  displayPuzzle(data);
}

async function handleCatFile(nodeId, path) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "read_file", target: nodeId, path });
  if (res && res.ok) {
    document.getElementById("viewer-path").textContent = path;
    document.getElementById("viewer-content").textContent = res.content || "(empty file)";
    document.getElementById("fs-file-viewer").classList.remove("hidden");
  }
}

async function handleStealFile(nodeId, path) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "download_file", target: nodeId, path });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateExploitChips(res.state.deck.exploits);
    if (state.selectedNodeId) {
      updateTargetCard(state.selectedNodeId);
    }
  } else if (res) {

    sfx.failure();
    addTerminalLog(res.message || "Failed to steal file.", "warn");
    applyStateSnapshot(res);
  }
}

async function handleWipeLogs() {
  if (!state.selectedNodeId) return;
  sfx.click();
  const res = await apiPost("/api/action", { action: "wipe_logs", target: state.selectedNodeId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Failed to wipe logs.", "warn");
    applyStateSnapshot(res);
  }
}

async function handlePhishNode() {
  if (!state.selectedNodeId) return;
  sfx.scan();
  addTerminalLog(`Dispatching spear-phishing credential lure to ${state.selectedNodeId}...`, "info");
  const res = await apiPost("/api/action", { action: "phish", target: state.selectedNodeId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Phishing lure ignored.", "warn");
    if (res.state) {
      state.data = res.state;
      renderHUD(res.state);
    }
  }
}

async function handleDeployKeylogger() {
  if (!state.selectedNodeId) return;
  sfx.click();
  addTerminalLog(`Injecting background keylogger listener into ${state.selectedNodeId}...`, "info");
  const res = await apiPost("/api/action", { action: "deploy_daemon", target: state.selectedNodeId, daemon_type: "keylogger" });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Keylogger deployment failed.", "warn");
  }
}

function closePuzzleBay() {
  document.getElementById("puzzle-idle").classList.remove("hidden");
  document.getElementById("puzzle-frequency").classList.add("hidden");
  document.getElementById("puzzle-buffer").classList.add("hidden");
  document.getElementById("puzzle-hash").classList.add("hidden");
  document.getElementById("probed-ports-container").classList.add("hidden");
  document.getElementById("filesystem-container").classList.add("hidden");
  state.activePuzzle = null;
}

function displayPuzzle(pData) {
  document.getElementById("puzzle-idle").classList.add("hidden");
  document.getElementById("puzzle-frequency").classList.add("hidden");
  document.getElementById("puzzle-buffer").classList.add("hidden");
  document.getElementById("puzzle-hash").classList.add("hidden");

  if (pData.puzzle_type === "frequency") {
    document.getElementById("puzzle-frequency").classList.remove("hidden");
    const tol = Number(pData.tolerance);
    const tolText = Number.isFinite(tol) ? ` · ±${tol.toFixed(1)} GHz` : "";
    document.getElementById("freq-tries").textContent = `TRIES: ${pData.attempts_left}${tolText}`;
    const slider = document.getElementById("freq-slider");
    const lo = Number(pData.min_freq), hi = Number(pData.max_freq);
    if (Number.isFinite(lo) && Number.isFinite(hi) && hi > lo) {
      slider.min = String(lo); slider.max = String(hi);
      slider.value = String((lo + hi) / 2);
      const val = document.getElementById("freq-val");
      if (val) val.textContent = `${Number(slider.value).toFixed(1)} GHz`;
    }
    startOscilloscopeAnimation();
  } else if (pData.puzzle_type === "buffer") {
    document.getElementById("puzzle-buffer").classList.remove("hidden");
    renderBufferTarget(pData.target_seq);
    renderBufferMatrix(pData.matrix);
    state.bufferInput = [];
    renderBufferPlayerSequence();
  } else if (pData.puzzle_type === "hash") {
    document.getElementById("puzzle-hash").classList.remove("hidden");
    document.getElementById("hash-tries").textContent = `TRIES: ${pData.attempts_left}`;
    renderHashPool(pData.word_list);
    document.getElementById("hash-history").innerHTML = "";
  }
}

// --------------------------------------------------------------------------
// Mini-Game 1: Oscilloscope Frequency Tuning
// --------------------------------------------------------------------------
let oscTimer = null;
function startOscilloscopeAnimation() {
  const oscCanvas = document.getElementById("osc-canvas");
  const ctx = oscCanvas.getContext("2d");
  let t = 0;

  if (oscTimer) cancelAnimationFrame(oscTimer);

  function drawOsc() {
    ctx.fillStyle = "rgba(2, 6, 8, 0.32)";
    ctx.fillRect(0, 0, oscCanvas.width, oscCanvas.height);
    // Scope graticule
    ctx.strokeStyle = "rgba(120, 180, 200, 0.12)";
    ctx.lineWidth = 1;
    for (let gx = 0; gx < oscCanvas.width; gx += 36) {
      ctx.beginPath(); ctx.moveTo(gx + 0.5, 0); ctx.lineTo(gx + 0.5, oscCanvas.height); ctx.stroke();
    }
    for (let gy = 0; gy < oscCanvas.height; gy += 24) {
      ctx.beginPath(); ctx.moveTo(0, gy + 0.5); ctx.lineTo(oscCanvas.width, gy + 0.5); ctx.stroke();
    }

    const dialVal = parseFloat(document.getElementById("freq-slider").value);
    const midY = oscCanvas.height / 2;
    const still = !motionSafe();

    // Target Carrier Wave (Cyan glow)
    ctx.save();
    ctx.shadowBlur = 8; ctx.shadowColor = "rgba(0,220,255,0.6)";
    ctx.beginPath();
    ctx.strokeStyle = "rgba(0, 220, 255, 0.55)";
    ctx.lineWidth = 1.5;
    for (let x = 0; x < oscCanvas.width; x += 2) {
      const y = midY + Math.sin(x * 0.05 + t * (still ? 0 : 0.05)) * 30;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.restore();

    // Tuned Player Wave (Green glow + alignment bloom)
    const align = 1 - Math.min(1, Math.abs(dialVal - 50) / 30);
    ctx.save();
    ctx.shadowBlur = 6 + align * 12; ctx.shadowColor = "hsla(140,100%,55%,0.7)";
    ctx.beginPath();
    ctx.strokeStyle = "hsl(140, 100%, 58%)";
    ctx.lineWidth = 2;
    for (let x = 0; x < oscCanvas.width; x += 2) {
      const y = midY + Math.sin(x * (dialVal * 0.001) + t * (still ? 0 : 0.05)) * 35;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.restore();

    t++;
    if (!document.getElementById("puzzle-frequency").classList.contains("hidden")) {
      if (motionSafe()) oscTimer = requestAnimationFrame(drawOsc);
    }
  }
  oscTimer = requestAnimationFrame(drawOsc);
}

async function handleTuneFrequency() {
  sfx.click();
  const guess = parseFloat(document.getElementById("freq-slider").value);
  const res = await apiPost("/api/puzzle/solve", { guess });
  if (!res) return;

  if (res.solved) {
    sfx.success();
    puzzleFlash("success");
    addTerminalLog(res.message, "success");
    closePuzzleBay();
    refreshFullState();
  } else {
    if (res.near_miss) {
      sfx.nearMiss();
      puzzleFlash("near");
      addTerminalLog("⚡ NEAR-MISS DETECTED! Resonance harmonic almost aligned!", "warn");
    } else {
      sfx.failure();
    }
    const keepTol = (document.getElementById("freq-tries").textContent.match(/±[\d.]+ GHz/) || [""])[0];
    document.getElementById("freq-tries").textContent = `TRIES: ${res.attempts_left}${keepTol ? ` · ${keepTol}` : ""}`;
    addTerminalLog(res.message, "warn");
    if (res.attempts_left <= 0) {
      closePuzzleBay();
      refreshFullState();
    }
  }
}

// --------------------------------------------------------------------------
// Mini-Game 2: Buffer Overflow Matrix
// --------------------------------------------------------------------------
function renderBufferTarget(targetSeq) {
  const container = document.getElementById("buf-target-seq");
  container.innerHTML = "";
  targetSeq.forEach((hex) => {
    const el = document.createElement("span");
    el.className = "hex-block";
    el.textContent = hex;
    container.appendChild(el);
  });
}

function renderBufferMatrix(matrix) {
  const grid = document.getElementById("buf-matrix-grid");
  grid.innerHTML = "";
  matrix.forEach((row) => {
    row.forEach((hex) => {
      const cell = document.createElement("div");
      cell.className = "matrix-cell";
      cell.textContent = hex;
      cell.addEventListener("click", () => {
        sfx.click();
        state.bufferInput.push(hex);
        renderBufferPlayerSequence();
      });
      grid.appendChild(cell);
    });
  });
}

function renderBufferPlayerSequence() {
  const container = document.getElementById("buf-player-seq");
  container.innerHTML = "";
  state.bufferInput.forEach((hex) => {
    const el = document.createElement("span");
    el.className = "hex-block";
    el.textContent = hex;
    container.appendChild(el);
  });
  const triesEl = document.getElementById("buf-tries");
  if (triesEl) {
    const target = (state.activePuzzle && state.activePuzzle.target_seq) || [];
    triesEl.textContent = `BLOCKS ${state.bufferInput.length}/${target.length || 2}`;
  }
}

async function handleInjectBuffer() {
  sfx.click();
  const res = await apiPost("/api/puzzle/solve", { guess: state.bufferInput });
  if (!res) return;

  if (res.solved) {
    sfx.success();
    addTerminalLog(res.message, "success");
    closePuzzleBay();
    refreshFullState();
  } else {
    if (res.near_miss) {
      sfx.nearMiss();
      puzzleFlash("near");
      addTerminalLog("⚡ NEAR-MISS! Primary buffer block aligned!", "warn");
    } else {
      sfx.failure();
    }
    addTerminalLog(res.message, "warn");
    state.bufferInput = [];
    renderBufferPlayerSequence();
    if (res.near_miss_bonus) {
      state.data = res.state;
      renderHUD(res.state);
      return;
    }
    closePuzzleBay();
    refreshFullState();
  }
}

// --------------------------------------------------------------------------
// Mini-Game 3: Cryptographic Hash Cipher
// --------------------------------------------------------------------------
function renderHashPool(wordList) {
  const container = document.getElementById("hash-word-pool");
  container.innerHTML = "";
  wordList.forEach((word) => {
    const btn = document.createElement("button");
    btn.className = "hash-word-btn";
    btn.textContent = word;
    btn.addEventListener("click", () => handleGuessHash(word));
    container.appendChild(btn);
  });
}

async function handleGuessHash(word) {
  sfx.click();
  const res = await apiPost("/api/puzzle/solve", { guess: word });
  if (!res) return;

  const history = document.getElementById("hash-history");
  const entry = document.createElement("div");
  entry.className = "hash-entry";
  entry.textContent = `${word} >> ${res.message}`;
  history.prepend(entry);

  if (res.solved) {
    sfx.success();
    addTerminalLog(res.message, "success");
    closePuzzleBay();
    refreshFullState();
  } else {
    if (res.near_miss) {
      sfx.nearMiss();
      puzzleFlash("near");
      addTerminalLog("⚡ CRITICAL NEAR-MISS! Only 1 character off!", "warn");
    } else {
      sfx.failure();
    }
    document.getElementById("hash-tries").textContent = `TRIES: ${res.attempts_left}`;
    if (res.attempts_left <= 0) {
      addTerminalLog("Lockout threshold reached on cipher node.", "danger");
      closePuzzleBay();
      refreshFullState();
    }
  }
}

// ==========================================================================
// 9. Story, Mission Board & Operative Interactions
// ==========================================================================
function openQuestsModal() {
  sfx.click();
  if (!state.data) return;
  const story = state.data.story || {};
  const quests = state.data.quests || [];

  document.getElementById("story-brief").innerHTML = `
    <div class="story-brief-act">${story.act_title || "ACT I"} // ${story.chapter_title || "Ghost in the Gateway"}</div>
    <div class="story-brief-text">${story.intro || ""}</div>
    ${story.choice_label ? `<div class="story-choice">CHOICE LOCKED: ${story.choice_label}</div>` : ""}
  `;

  const logEl = document.getElementById("story-log");
  logEl.innerHTML = "";
  (story.log || []).slice(-10).forEach((line) => {
    const entry = document.createElement("div");
    entry.className = "story-log-line";
    entry.textContent = `> ${line}`;
    logEl.appendChild(entry);
  });

  const grid = document.getElementById("quests-grid");
  grid.innerHTML = "";
  quests.forEach((quest) => {
    const card = document.createElement("div");
    const complete = quest.completed;
    const active = quest.accepted && !complete;
    const locked = quest.locked;
    card.className = `quest-card ${complete ? "quest-complete" : locked ? "quest-locked" : active ? "quest-active" : "quest-available"}`;
    const status = complete ? "COMPLETE" : locked ? "LOCKED" : active ? `${quest.progress}/${quest.required}` : "AVAILABLE";
    card.innerHTML = `
      <div class="quest-card-head">
        <span class="quest-title">${quest.title}</span>
        <span class="quest-status">${status}</span>
      </div>
      <div class="quest-desc">${quest.description}</div>
      <div class="quest-meta">GIVER: ${quest.giver} | REWARD: ${quest.reward_creds} CR${locked && quest.lock_reason ? ` | LOCK: ${quest.lock_reason}` : ""}</div>
      ${!quest.accepted && !complete && !locked ? `<button class="hack-btn small-btn accept-quest-btn" data-quest="${quest.quest_id}">ACCEPT JOB</button>` : ""}
    `;
    const acceptBtn = card.querySelector(".accept-quest-btn");
    if (acceptBtn) {
      acceptBtn.addEventListener("click", () => handleAcceptQuest(quest.quest_id));
    }
    grid.appendChild(card);
  });

  const gState = state.data.state || {};
  const active = gState.active_contract;
  const offers = gState.contract_offers || [];
  const jobBoard = document.getElementById("job-board");
  jobBoard.innerHTML = "";

  if (active) {
    const remaining = active.expires_turn ? active.expires_turn - gState.turns_elapsed : null;
    const card = document.createElement("div");
    card.className = "quest-card quest-active";
    card.innerHTML = `
      <div class="quest-card-head">
        <span class="quest-title">ACTIVE: ${active.title}</span>
        <span class="quest-status">${(active.risk_tier || "standard").toUpperCase()}</span>
      </div>
      <div class="quest-desc">${active.description || ""}</div>
      <div class="quest-meta">TARGET: ${active.target_ip || active.target_node_type}${active.district ? ` [${active.district}]` : ""} | TRACE LIMIT: ${active.max_trace_limit}% | ${remaining === null ? "NO DEADLINE" : `${Math.max(0, remaining)} TURNS LEFT`} | PAY: ${active.reward_creds} CR</div>
      <button class="hack-btn small-btn decline-job-btn">DECLINE CONTRACT</button>
    `;
    card.querySelector(".decline-job-btn").addEventListener("click", handleDeclineContract);
    jobBoard.appendChild(card);
  }

  offers.forEach((offer) => {
    const card = document.createElement("div");
    card.className = `quest-card ${active ? "quest-locked" : "quest-available"}`;
    const offerLeft = offer.offer_expires_turn ? offer.offer_expires_turn - gState.turns_elapsed : null;
    card.innerHTML = `
      <div class="quest-card-head">
        <span class="quest-title">${offer.title}</span>
        <span class="quest-status">${(offer.risk_tier || "standard").toUpperCase()}</span>
      </div>
      <div class="quest-desc">${offer.description || ""}</div>
      <div class="quest-meta">TARGET: ${offer.target_ip || offer.target_node_type}${offer.district ? ` [${offer.district}]` : ""} | WINDOW: ${offer.deadline_turns} TURNS | PAY: ${offer.reward_creds} CR (+${offer.bonus_creds} RUSH)${offerLeft === null ? "" : ` | OFFER ${Math.max(0, offerLeft)} TURNS`}</div>
      ${active ? "" : `<button class="hack-btn small-btn accept-contract-btn" data-contract="${offer.contract_id}">ACCEPT CONTRACT</button><button class="hack-btn small-btn pass-offer-btn" data-contract="${offer.contract_id}">PASS (30 CR / 1 TURN)</button>`}
    `;
    const acceptBtn = card.querySelector(".accept-contract-btn");
    if (acceptBtn) {
      acceptBtn.addEventListener("click", () => handleAcceptContract(offer.contract_id));
    }
    const passBtn = card.querySelector(".pass-offer-btn");
    if (passBtn) {
      passBtn.addEventListener("click", () => handleDropOffer(offer.contract_id));
    }
    jobBoard.appendChild(card);
  });

  if (!active && offers.length === 0) {
    const empty = document.createElement("div");
    empty.className = "quest-desc";
    empty.textContent = "No fresh Syndicate work. Advance the grid or wait for a host to re-secure.";
    jobBoard.appendChild(empty);
  }

  document.getElementById("modal-quests").classList.remove("hidden");
}

async function handleAcceptContract(contractId) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "accept_contract", contract_id: contractId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    openQuestsModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Contract unavailable.", "warn");
    applyStateSnapshot(res);
  }
}

async function handleDropOffer(contractId) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "drop_offer", contract_id: contractId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "warn");
    state.data = res.state;
    renderHUD(res.state);
    openQuestsModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Offer could not be dropped.", "warn");
    applyStateSnapshot(res);
  }
}

async function handleDeclineContract() {
  sfx.click();
  const res = await apiPost("/api/action", { action: "decline_contract" });
  if (res && res.ok) {
    sfx.warning ? sfx.warning() : sfx.click();
    addTerminalLog(res.message, "warn");
    state.data = res.state;
    renderHUD(res.state);
    openQuestsModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "No active contract.", "warn");
    applyStateSnapshot(res);
  }
}

async function handleAcceptQuest(questId) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "accept_quest", quest_id: questId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    openQuestsModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Quest unavailable.", "warn");
  }
}

function openContactsModal() {
  sfx.click();
  if (!state.data) return;
  const grid = document.getElementById("contacts-grid");
  grid.innerHTML = "";

  (state.data.contacts || []).forEach((contact) => {
    const card = document.createElement("div");
    if (contact.locked) {
      card.className = "contact-card contact-locked";
      card.innerHTML = `
        <div class="contact-name">${contact.name}</div>
        <div class="contact-role">${contact.handle} // SIGNAL LOCKED</div>
        <div class="contact-tagline">Advance the story to open this channel.</div>
      `;
      grid.appendChild(card);
      return;
    }

    card.className = "contact-card";
    const av = avatarHTML(contact.contact_id, contact.name);
    card.innerHTML = `
      <div class="contact-head">
        ${av}
        <div>
          <div class="contact-name">${contact.name}</div>
          <div class="contact-role">${contact.handle} // ${contact.role}</div>
        </div>
        <span class="contact-trust">TRUST ${contact.trust} // ${(contact.trust_tier || "Neutral").toUpperCase()}</span>
      </div>
      <div class="contact-tagline">${contact.tagline}</div>
      <div class="contact-dialogue">"${contact.dialogue}"</div>
      ${contact.trust_dialogue ? `<div class="contact-dialogue">"${contact.trust_dialogue}"</div>` : ""}
      ${contact.arc_title ? `<div class="contact-arc">ARC: ${contact.arc_title} — ${contact.arc_label} (${contact.arc_stage}/3)</div>` : ""}
      <div class="contact-favor">${contact.favor_description}</div>
      <div class="contact-actions">
        <button class="action-btn small-btn contact-action" data-mode="talk">TALK</button>
        <button class="action-btn small-btn contact-action" data-mode="job">JOB</button>
        <button class="action-btn small-btn contact-action" data-mode="favor" ${contact.favor_available ? "" : "disabled"}>
          ${contact.favor_available ? (contact.favor_used ? "INNER CIRCLE FAVOR" : "CALL FAVOR") : "FAVOR SPENT"}
        </button>
      </div>
      ${contact.pact_available ? `
        <div class="contact-pact">
          <div class="contact-pact-label">ACT III ALLIANCE // ONE CHOICE</div>
          <div class="contact-actions">
            <button class="action-btn small-btn contact-action pact-ally" data-mode="ally">ALLY WITH ZERO</button>
            <button class="action-btn small-btn contact-action pact-defy" data-mode="defy">DEFY ZERO</button>
          </div>
        </div>
      ` : ""}
    `;
    card.querySelectorAll(".contact-action").forEach((button) => {
      button.addEventListener("click", () => handleContactInteraction(contact.contact_id, button.dataset.mode));
    });
    grid.appendChild(card);
  });

  document.getElementById("modal-contacts").classList.remove("hidden");
}

async function handleContactInteraction(contactId, mode) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "contact", contact_id: contactId, mode });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    openContactsModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "No response on the channel.", "warn");
  }
}

// ==========================================================================
// 10. Black Market Shop & Career Dossier Modals
// ==========================================================================
async function openShopModal() {
  sfx.click();
  const data = await apiGet("/api/shop");
  if (!data) return;

  document.getElementById("shop-creds").textContent = data.creds;
  const shopDiscount = document.getElementById("shop-discount");
  if (shopDiscount) {
    shopDiscount.textContent = data.street_discount
      ? `STREET -${Math.round(data.street_discount * 100)}%`
      : "";
  }
  const grid = document.getElementById("shop-items-grid");
  grid.innerHTML = "";

  data.items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "shop-item-card";

    let statusText = item.max_level > 1
      ? `Level ${item.current_level}/${item.max_level}`
      : (item.current_level > 0 ? "LOADED IN FIRMWARE" : "AVAILABLE");
    if (item.category === "consumable") {
      statusText = item.current_level > 0 ? "ARMED" : "ONE USE";
    }

    const icon = avatarHTML(item.item_id, item.category);
    card.innerHTML = `
      ${icon}
      <div class="shop-item-info">
        <div class="item-name">${item.name} (${statusText})</div>
        <div class="item-desc">${item.description}</div>
      </div>
      <div class="shop-item-action">
        <span class="item-cost">${item.cost} CR</span>
        <button class="buy-btn" ${!item.can_buy ? "disabled" : ""}>PURCHASE</button>
      </div>
    `;

    const buyBtn = card.querySelector(".buy-btn");
    buyBtn.addEventListener("click", async () => {
      sfx.click();
      const res = await apiPost("/api/action", { action: "shop_buy", item_id: item.item_id });
      if (res && res.ok) {
        sfx.success();
        addTerminalLog(res.message, "success");
        openShopModal(); // Refresh modal
        refreshFullState();
      } else if (res) {
        sfx.failure();
        addTerminalLog(res.message || "Purchase denied.", "warn");
      }
    });

    grid.appendChild(card);
  });

  document.getElementById("modal-shop").classList.remove("hidden");
}

function formatRunStamp(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "--";
  try {
    return new Date(value * 1000).toLocaleString([], {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (_) {
    return "--";
  }
}

async function openCareerModal() {
  sfx.click();
  const data = await apiGet("/api/career");
  if (!data) return;

  document.getElementById("dossier-alias").textContent = data.alias;
  const aliasInput = document.getElementById("dossier-alias-input");
  if (aliasInput) aliasInput.value = data.alias;
  document.getElementById("dossier-banked").textContent = `${data.banked_creds} CR`;
  document.getElementById("dossier-lifetime").textContent = `${data.lifetime_creds} CR`;
  document.getElementById("dossier-wins").textContent = data.successful_runs;
  document.getElementById("dossier-fails").textContent = data.failed_runs;
  document.getElementById("dossier-streak").textContent = `${data.current_streak} HEISTS`;
  document.getElementById("dossier-best").textContent = `${data.best_streak} HEISTS`;
  document.getElementById("dossier-combo").textContent = `x${data.best_combo || 0}`;
  document.getElementById("dossier-upgrades").textContent = data.purchased_upgrades.length > 0
    ? data.purchased_upgrades.join(", ")
    : "Standard Factory Rig";

  state.careerData = data;
  const factionsEl = document.getElementById("dossier-factions");
  if (factionsEl) {
    const standing = data.faction_standing || {};
    const syndicate = Number(standing.syndicate || 0);
    const street = Number(standing.street || 0);
    factionsEl.innerHTML = "";
    const ranks = data.faction_ranks || {};
    const rows = [
      ["SYNDICATE", syndicate, ranks.syndicate || "Associate", `+${Math.min(20, syndicate)}% contract pay`],
      ["STREET", street, ranks.street || "Lookout", `-${Math.min(15, street)}% shop prices`],
    ];
    rows.forEach(([name, value, rank, bonus]) => {
      const row = document.createElement("div");
      row.className = "dossier-run-row";
      const chip = document.createElement("span");
      chip.className = "run-outcome jackout";
      chip.textContent = name;
      const meta = document.createElement("span");
      meta.className = "run-meta";
      meta.textContent = `${rank} · STANDING ${value} · ${bonus}`;
      row.append(chip, meta);
      factionsEl.appendChild(row);
    });
  }
  renderHall();

  const dailyStreakEl = document.getElementById("dossier-daily-streak");
  if (dailyStreakEl) {
    dailyStreakEl.textContent = data.daily_streak
      ? `// STREAK ${data.daily_streak} (BEST ${data.best_daily_streak || 0})`
      : "";
  }

  const dailyEl = document.getElementById("dossier-daily");
  if (dailyEl) {
    dailyEl.innerHTML = "";
    const bests = data.daily_best && typeof data.daily_best === "object"
      ? Object.entries(data.daily_best).sort((a, b) => b[0].localeCompare(a[0])).slice(0, 5)
      : [];
    if (!bests.length) {
      const empty = document.createElement("span");
      empty.className = "empty-chips";
      empty.textContent = "No daily runs yet. Launch DAILY RUN from the main menu.";
      dailyEl.appendChild(empty);
    } else {
      bests.forEach(([day, creds]) => {
        const row = document.createElement("div");
        row.className = "dossier-run-row";
        const chip = document.createElement("span");
        chip.className = "run-outcome jackout";
        chip.textContent = "DAILY";
        const meta = document.createElement("span");
        meta.className = "run-meta";
        meta.textContent = `${day} · BEST +${creds} CR`;
        row.append(chip, meta);
        dailyEl.appendChild(row);
      });
    }
  }

  const achievementsEl = document.getElementById("dossier-achievements");
  if (achievementsEl) {
    achievementsEl.innerHTML = "";
    const catalog = Array.isArray(data.achievement_catalog) ? data.achievement_catalog : [];
    if (!catalog.length) {
      const empty = document.createElement("span");
      empty.className = "empty-chips";
      empty.textContent = "Milestone catalog unavailable.";
      achievementsEl.appendChild(empty);
    }
    catalog.forEach((entry) => {
      const badge = document.createElement("div");
      badge.className = `achievement-badge ${entry.unlocked ? "unlocked" : "locked"}`;
      badge.title = entry.description || "";
      const badgeName = document.createElement("span");
      badgeName.className = "achievement-name";
      badgeName.textContent = entry.name || entry.achievement_id || "MILESTONE";
      const badgeDesc = document.createElement("span");
      badgeDesc.className = "achievement-desc";
      badgeDesc.textContent = entry.description || "";
      badge.append(badgeName, badgeDesc);
      achievementsEl.appendChild(badge);
    });
  }

  const historyEl = document.getElementById("dossier-history");
  if (historyEl) {
    historyEl.innerHTML = "";
    const history = Array.isArray(data.run_history)
      ? data.run_history.slice(-6).reverse()
      : [];
    if (!history.length) {
      const empty = document.createElement("span");
      empty.className = "empty-chips";
      empty.textContent = "No settled runs yet. Jack out or burn a deck to record a legacy.";
      historyEl.appendChild(empty);
    } else {
      history.forEach((record) => {
        const row = document.createElement("div");
        row.className = "dossier-run-row";
        const outcome = String(record.outcome || "unknown").toLowerCase();
        const chip = document.createElement("span");
        chip.className = `run-outcome ${outcome}`;
        chip.textContent = outcome.toUpperCase();
        const meta = document.createElement("span");
        meta.className = "run-meta";
        const seed = record.seed !== undefined ? record.seed : "?";
        const turns = record.turns !== undefined ? record.turns : 0;
        const creds = record.creds !== undefined ? record.creds : 0;
        const combo = record.best_combo !== undefined ? record.best_combo : 0;
        const difficulty = String(record.difficulty || "normal").toUpperCase();
        meta.textContent = `${difficulty} · SEED ${seed} · TURN ${turns} · ${creds} CR · COMBO x${combo}`;
        const time = document.createElement("span");
        time.className = "run-time";
        time.textContent = formatRunStamp(record.finished_at);
        const replay = document.createElement("button");
        replay.className = "action-btn run-replay-btn";
        replay.textContent = "REPLAY";
        replay.title = `Start a new run with seed ${record.seed}`;
        replay.disabled = !Number.isFinite(record.seed);
        replay.addEventListener("click", () => handleReplaySeed(record.seed));
        row.append(chip, meta, time, replay);
        historyEl.appendChild(row);
      });
    }
  }

  document.getElementById("modal-career").classList.remove("hidden");
}

async function openRivalModal() {
  sfx.click();
  if (!state.data) {
    await refreshFullState();
  }
  renderRivalModal();
  document.getElementById("modal-rival").classList.remove("hidden");
}

function renderRivalModal() {
  const rival = state.data && state.data.rival;
  const cpu = state.data && state.data.deck ? state.data.deck.cpu_cycles : 0;
  const rivalAv = document.getElementById("rival-name");
  rivalAv.textContent = rival ? rival.name : "NO ACTIVE RIVAL";
  if (rivalAv && rival) {
    rivalAv.setAttribute("data-rival", rival.name);
  }
  document.getElementById("rival-handle").textContent = rival ? `@${rival.handle} // SKILL ${rival.skill}/3` : "";
  document.getElementById("rival-tagline").textContent = rival ? rival.tagline : "";
  document.getElementById("rival-skill").textContent = rival ? `${rival.skill}/3` : "0/3";
  document.getElementById("rival-stolen").textContent = rival ? rival.contracts_stolen : 0;
  document.getElementById("rival-next").textContent = rival ? `${rival.turns_until}T` : "--";
  const counterBtn = document.getElementById("btn-counter-rival");
  if (counterBtn) {
    counterBtn.disabled = !rival || cpu < 2;
    counterBtn.textContent = rival && cpu < 2 ? "COUNTER-TRACE (NEED 2 CPU)" : "COUNTER-TRACE (2 CPU)";
  }
}

async function handleCounterRival() {
  sfx.click();
  const res = await apiPost("/api/action", { action: "counter_rival" });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message || "Rival counter-traced.", "success");
    state.data = res.state;
    renderHUD(res.state);
    renderRivalModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || res.error || "Counter-trace failed.", "warn");
    if (applyStateSnapshot(res)) renderRivalModal();
  }
}

function renderHall() {
  const hallEl = document.getElementById("dossier-hall");
  const data = state.careerData;
  if (!hallEl || !data) return;
  const filter = state.hallFilter || "all";
  const all = Array.isArray(data.hall_of_fame) ? data.hall_of_fame : [];
  const hall = filter === "all"
    ? all
    : all.filter((entry) => String(entry.difficulty || "normal").toLowerCase() === filter);
  hallEl.innerHTML = "";
  if (!hall.length) {
    const empty = document.createElement("span");
    empty.className = "empty-chips";
    empty.textContent = filter === "all"
      ? "No ranked runs yet. Finish a run to enter the board."
      : `No ranked ${filter.toUpperCase()} runs yet.`;
    hallEl.appendChild(empty);
    return;
  }
  hall.slice(0, 5).forEach((entry, index) => {
    const row = document.createElement("div");
    row.className = "dossier-run-row";
    const rank = document.createElement("span");
    rank.className = "run-outcome hall-rank";
    rank.textContent = `#${index + 1}`;
    const meta = document.createElement("span");
    meta.className = "run-meta";
    const score = Number(entry.score || 0).toLocaleString();
    const outcome = String(entry.outcome || "unknown").toUpperCase();
    const seed = entry.seed !== undefined ? entry.seed : "?";
    const turns = entry.turns !== undefined ? entry.turns : 0;
    const difficulty = String(entry.difficulty || "normal").toUpperCase();
    meta.textContent = `${score} PTS · ${outcome} · ${difficulty} · SEED ${seed} · TURN ${turns}`;
    row.append(rank, meta);
    hallEl.appendChild(row);
  });
}

async function openRigModal() {
  sfx.click();
  const data = await apiGet("/api/local_files");
  if (!data) return;

  document.getElementById("rig-ip").textContent = data.ip;
  document.getElementById("rig-hostname").textContent = data.hostname;
  if (state.data && state.data.deck && state.data.deck.model_name) {
    document.getElementById("rig-model").textContent = state.data.deck.model_name;
  }

  // Render Local Files
  const tbody = document.getElementById("rig-file-tbody");
  tbody.innerHTML = "";
  if (data.files && data.files.length > 0) {
    data.files.forEach((f) => {
      const tr = document.createElement("tr");
      const valStr = f.value_creds > 0 ? `${f.value_creds} CR` : "---";
      tr.innerHTML = `
        <td>${f.path}</td>
        <td>${f.size_kb}KB</td>
        <td>${valStr}</td>
        <td>
          <button class="icon-btn small-btn btn-cat-local" data-path="${f.path}">CAT</button>
        </td>
      `;
      tr.querySelector(".btn-cat-local").addEventListener("click", () => {
        document.getElementById("viewer-path").textContent = `[LOCAL] ${f.path}`;
        document.getElementById("viewer-content").textContent = f.content || "(empty file)";
        document.getElementById("fs-file-viewer").classList.remove("hidden");
        document.getElementById("modal-rig").classList.add("hidden");
      });
      tbody.appendChild(tr);
    });
  } else {
    tbody.innerHTML = '<tr><td colspan="4">No local files stored.</td></tr>';
  }

  // Render Active Daemons
  const daemonsGrid = document.getElementById("rig-daemons-grid");
  daemonsGrid.innerHTML = "";
  if (data.daemons && data.daemons.length > 0) {
    data.daemons.forEach((d) => {
      const card = document.createElement("div");
      card.className = "daemon-card";
      card.innerHTML = `
        <div>
          <span class="daemon-title">${d.daemon_type.toUpperCase()}</span>
          <span class="daemon-target">on node ${d.target_node_id} (active ${d.turns_active} turns)</span>
        </div>
        <div class="daemon-yield">+${d.yield_per_turn} CR / turn (${d.detection_risk}% trace)</div>
      `;
      daemonsGrid.appendChild(card);
    });
  } else {
    daemonsGrid.innerHTML = '<span class="empty-chips">No active background daemons deployed.</span>';
  }

  document.getElementById("modal-rig").classList.remove("hidden");
}

async function openWorkshopModal() {
  sfx.click();
  const data = await apiGet("/api/workshop");
  if (!data) return;

  const unbanked = (state.data && state.data.state) ? state.data.state.unbanked_creds : 0;
  const banked = (state.data && state.data.deck) ? state.data.deck.cryptocreds : 0;
  const totalCreds = unbanked + banked;
  document.getElementById("workshop-creds").textContent = `${totalCreds} (${banked} BANKED + ${unbanked} UNBANKED)`;
  const deckNow = (state.data && state.data.deck) || {};
  const intelNow = deckNow.threat_intel_count || 0;
  const intelCountEl = document.getElementById("workshop-intel-count");
  if (intelCountEl) intelCountEl.textContent = `${intelNow} FRAGMENTS`;
  const revealBtn = document.getElementById("btn-intel-reveal");
  const forgeBtn = document.getElementById("btn-intel-forge");
  if (revealBtn) revealBtn.disabled = intelNow < 1 || !state.selectedNodeId;
  if (forgeBtn) forgeBtn.disabled = intelNow < 2 || (deckNow.exploits || []).includes("zero_day_forge");
  const grid = document.getElementById("workshop-recipes-grid");
  grid.innerHTML = "";

  data.recipes.forEach((recipe) => {
    const card = document.createElement("div");
    card.className = "workshop-recipe-card";
    const canCraft = totalCreds >= recipe.cost_creds;

    card.innerHTML = `
      <div class="recipe-info">
        <div class="recipe-name">${recipe.name} [${recipe.vector}]</div>
        <div class="recipe-desc">${recipe.description}</div>
      </div>
      <div class="recipe-action">
        <span class="recipe-cost">${recipe.cost_creds} CR</span>
        <button class="craft-btn" ${!canCraft ? "disabled" : ""}>SYNTHESIZE</button>
      </div>
    `;

    const craftBtn = card.querySelector(".craft-btn");
    craftBtn.addEventListener("click", async () => {
      sfx.click();
      const res = await apiPost("/api/action", { action: "craft", recipe: recipe.name });
      if (res && res.ok) {
        sfx.jackpot();
        addTerminalLog(res.message, "success");
        state.data = res.state;
        renderHUD(res.state);
        updateExploitChips(res.state.deck.exploits);
        openWorkshopModal(); // Refresh modal
      } else if (res) {
        sfx.failure();
        addTerminalLog(res.message || "Synthesis failed.", "warn");
      }
    });

    grid.appendChild(card);
  });

  document.getElementById("modal-workshop").classList.remove("hidden");
}

// ==========================================================================
// 10. Weaponized CVE Exploit Arsenal Modal
// ==========================================================================
async function openCvesModal() {
  sfx.click();
  const data = await apiGet("/api/cves");
  const cves = (data && data.cves) ? data.cves : (state.data && state.data.known_cves ? state.data.known_cves : []);

  document.getElementById("cves-count").textContent = cves.length;
  const grid = document.getElementById("cves-grid");
  grid.innerHTML = "";

  cves.forEach((c) => {
    const card = document.createElement("div");
    card.className = "cve-card";
    card.innerHTML = `
      <div class="cve-header">
        <span class="cve-id">${c.cve_id}</span>
        <span class="cve-badge">${c.target_service.toUpperCase()} SERVICE</span>
      </div>
      <div class="cve-name">${c.name}</div>
      <div class="cve-meta-row">
        <span>RAM: <strong>${c.required_ram_mb}MB</strong></span>
        <span>CPU: <strong>${c.cpu_cost} Cycles</strong></span>
        <span>STEALTH: <strong>${c.stealth_rating}/5</strong></span>
        <span>TRACE: <strong>+${c.damage_trace}%</strong></span>
      </div>
      <div class="cve-desc">${c.description}</div>
    `;
    grid.appendChild(card);
  });

  document.getElementById("modal-cves").classList.remove("hidden");
}

// ==========================================================================
// 11. Multi-Vector Social Engineering Suite
// ==========================================================================
function openSocialModal() {
  if (!state.selectedNodeId) return;
  const node = state.data.nodes[state.selectedNodeId];
  if (!node) return;

  sfx.click();
  document.getElementById("social-target-name").textContent = node.hostname;
  document.getElementById("social-target-ip").textContent = node.ip_address;

  // Render employees
  const empGrid = document.getElementById("social-employees-grid");
  empGrid.innerHTML = "";
  const employees = node.employees || [];

  if (employees.length === 0) {
    empGrid.innerHTML = '<span class="empty-chips">No identifiable staff on host. Using default associate.</span>';
    state.selectedEmployee = null;
  } else {
    state.selectedEmployee = employees[0].name;
    employees.forEach((emp, idx) => {
      const card = document.createElement("div");
      card.className = `employee-card ${idx === 0 ? "selected" : ""}`;
      const badgeClass = (emp.awareness_level || "STANDARD").toLowerCase();
      card.innerHTML = `
        <div class="employee-name">${emp.name}</div>
        <div class="employee-role">${emp.role}</div>
        <span class="employee-badge ${badgeClass}">${emp.awareness_level}</span>
        <span class="employee-shift shift-${(emp.work_shift || "day").toLowerCase()}">${(emp.work_shift || "day").toUpperCase()} SHIFT</span>
      `;
      card.addEventListener("click", () => {
        sfx.click();
        empGrid.querySelectorAll(".employee-card").forEach(c => c.classList.remove("selected"));
        card.classList.add("selected");
        state.selectedEmployee = emp.name;
      });
      empGrid.appendChild(card);
    });
  }

  // Setup vector cards selection
  const vectorCards = document.querySelectorAll("#social-vectors-grid .vector-card");
  vectorCards.forEach((card) => {
    card.onclick = () => {
      sfx.click();
      vectorCards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      state.selectedVector = card.dataset.vector;
    };
  });

  document.getElementById("modal-social").classList.remove("hidden");
}

async function executeSocialAttack() {
  if (!state.selectedNodeId) return;
  sfx.scan();
  addTerminalLog(`⚡ Launching ${state.selectedVector.toUpperCase()} campaign against ${state.selectedNodeId}...`, "info");
  document.getElementById("modal-social").classList.add("hidden");

  const res = await apiPost("/api/action", {
    action: "social",
    target: state.selectedNodeId,
    vector: state.selectedVector || "spear_phish",
    employee: state.selectedEmployee,
  });

  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
  } else if (res) {
    sfx.alarm();
    addTerminalLog(res.message || "Social engineering campaign failed.", "danger");
    if (res.state) {
      state.data = res.state;
      renderHUD(res.state);
      updateTargetCard(state.selectedNodeId);
    }
  }
}

// ==========================================================================
// 12. Firewall Ingress Bypass & Antivirus Evasion Handlers
// ==========================================================================
function openBypassModal(port) {
  if (!state.selectedNodeId) return;
  const node = state.data.nodes[state.selectedNodeId];
  if (!node || !node.firewall) return;

  sfx.click();
  const blockedRules = (node.firewall.rules || []).filter(r => r.action === "BLOCK" && !r.bypassed);
  if (blockedRules.length === 0) {
    addTerminalLog("No active blocked firewall rules to bypass on this host.", "info");
    return;
  }

  const requestedRule = blockedRules.find(r => r.port === port);
  const targetPort = (requestedRule || blockedRules[0]).port;
  document.getElementById("bypass-target-info").innerHTML = `
    <div>TARGET HOST: <strong>${node.hostname} (${node.ip_address})</strong></div>
    <div>BLOCKED PORT: <strong style="color:var(--c-danger);">${targetPort}/tcp</strong> | POLICY: <strong>${node.firewall.policy}</strong></div>
  `;

  const grid = document.getElementById("bypass-methods-grid");
  grid.innerHTML = "";

  const methods = [
    { key: "knock", name: "Port Knocking Sequence (TCP SYN)", cost: "1 CPU", trace: "+5% TRACE", desc: "Craft sequence of closed-port connection attempts to trigger dynamic firewall rule opening." },
    { key: "fragment", name: "Packet Fragmentation Cloak", cost: "1 CPU", trace: "+7% TRACE", desc: "Split malicious TCP headers across microscopic MTU IP fragments to evade stateful inspection." },
    { key: "tunnel", name: "Proxy Tunnel Injection", cost: "2 CPU", trace: "+9% TRACE", desc: "Encapsulate port payloads inside legitimate SSH/HTTP tunnel to silently pass ingress inspection." },
  ];

  methods.forEach((m) => {
    const card = document.createElement("div");
    card.className = "bypass-method-card";
    card.innerHTML = `
      <div>
        <div class="bypass-method-name">${m.name}</div>
        <div class="bypass-method-desc">${m.desc}</div>
      </div>
      <div style="text-align:right;">
        <span style="font-size:10px; color:var(--c-accent);">${m.cost}</span><br>
        <span style="font-size:9px; color:var(--c-warning);">${m.trace}</span>
      </div>
    `;
    card.addEventListener("click", async () => {
      sfx.click();
      document.getElementById("modal-bypass").classList.add("hidden");
      addTerminalLog(`Injecting ${m.name} on ${node.hostname}:${targetPort}...`, "info");
      const res = await apiPost("/api/action", {
        action: "bypass",
        target: state.selectedNodeId,
        port: targetPort,
        method: m.key,
      });
      if (res && res.ok) {
        sfx.success();
        addTerminalLog(res.message, "success");
        state.data = res.state;
        renderHUD(res.state);
        updateTargetCard(state.selectedNodeId);
      } else if (res) {
        sfx.failure();
        addTerminalLog(res.message || "Firewall bypass failed.", "warn");
        applyStateSnapshot(res);
      }
    });
    grid.appendChild(card);
  });

  document.getElementById("modal-bypass").classList.remove("hidden");
}

async function handleEvadeAv() {
  if (!state.selectedNodeId) return;
  const node = state.data.nodes[state.selectedNodeId];
  if (!node || !node.antivirus) return;

  sfx.click();
  addTerminalLog(`Deploying Kernel Rootkit Evasion Hook against ${node.antivirus.name}...`, "info");
  const res = await apiPost("/api/action", {
    action: "evade",
    target: state.selectedNodeId,
    method: "rootkit",
  });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "AV evasion failed.", "warn");
    applyStateSnapshot(res);
  }
}

/* === Cyberpulse 0.5.0: SIM + ARCS + DeckOS panels, alert theming, shortcuts === */
(function cyberpulseSimArcs() {
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function snapshot() { try { return (typeof state !== "undefined" && state.data) || null; } catch (_) { return null; } }

  function renderSimPanels(data) {
    data = data || snapshot();
    if (!data) return;
    try {
      var tier = (data.world && data.world.alert_tier) || "";
      if (tier) document.body.dataset.alertTier = tier;
    } catch (_) {}
    try {
      var traceLevel = (data.state && data.state.trace_percent) || 0;
      document.body.classList.toggle("trace-critical", traceLevel >= 80);
    } catch (_) {}
    try {
      var districts = data.districts || (data.world && data.world.districts) || [];
      var chip = $("grid-districts");
      if (chip && districts.length) {
        var hot = districts.filter(function (d) { return d.patrol === "heavy"; }).length;
        var avg = Math.round(districts.reduce(function (a, d) { return a + (d.load || 0); }, 0) / districts.length);
        chip.textContent = "DISTRICTS AVG " + avg + "%" + (hot ? " // " + hot + " HOT" : "");
      }
      var grid = $("districts-grid");
      if (grid && districts.length) {
        var nodeStatus = {};
        try {
          var allNodes = data.nodes || {};
          for (var nk in allNodes) { if (allNodes[nk]) nodeStatus[nk] = allNodes[nk].status; }
        } catch (_) {}
        grid.innerHTML = districts.map(function (d) {
          return '<div class="district-card" tabindex="0" aria-label="' + esc(d.name) + " load " + d.load + " percent, " + esc(d.patrol) + ' patrol">' +
            '<div class="d-name">' + esc(d.name) + "</div>" +
            '<div class="d-meta">' + esc(d.flavor || "") + " · patrol " + esc(d.patrol || "") + " · " + esc(d.market_mood || "") + "</div>" +
            (d.hosts && d.hosts.length ? '<div class="d-hosts">' + d.hosts.length + " HOSTS: " + d.hosts.slice(0, 6).map(function (h) { return '<button class="d-host-chip' + (nodeStatus[h] === "BREACHED" ? " breached" : "") + '" data-node="' + esc(h) + '" title="Select ' + esc(h) + ' on the matrix">' + esc(h.replace(/^node_/, "")) + "</button>"; }).join("") + (d.hosts.length > 6 ? '<span class="d-more">+' + (d.hosts.length - 6) + " more</span>" : "") + "</div>" : "") +
            '<div class="load-track" aria-hidden="true"><div class="load-fill" style="width:' + Math.max(0, Math.min(100, d.load || 0)) + '%;"></div></div></div>';
        }).join("");
        Array.prototype.forEach.call(grid.querySelectorAll("[data-node]"), function (chip) {
          chip.onclick = function (ev) {
            ev.stopPropagation();
            try { if (typeof sfx !== "undefined") sfx.click(); } catch (_) {}
            var nid = chip.getAttribute("data-node");
            var m = $("modal-sim");
            if (m) m.classList.add("hidden");
            try {
              state.selectedNodeId = nid;
              if (typeof updateTargetCard === "function") updateTargetCard(nid);
            } catch (_) {}
          };
        });
      }
    } catch (_) {}
    try {
      var deckos = data.deckos || null;
      var meta = $("deckos-meta"), procs = $("deckos-grid");
      if (deckos && meta && procs) {
        meta.textContent = deckos.hostname + " (" + deckos.ip + ") · uptime " + deckos.uptime + " · CPU " + deckos.cpu + " · trace " + deckos.trace + "% · procs " + deckos.processes;
        if (Array.isArray(deckos.processes_list || deckos.processes) && false) { void 0; }
        if (Array.isArray(deckos.processes)) {
          procs.innerHTML = deckos.processes.map(function (p) {
            return '<div class="deckos-proc"><span>[' + p.pid + "] " + esc(p.name) + " <em>" + esc(p.owner) + "</em></span>" +
              (p.killable ? '<button data-kill="' + p.pid + '" aria-label="Kill process ' + p.pid + '">KILL</button>' : "<span>" + esc(p.desc || "") + "</span>") + "</div>";
          }).join("");
        } else {
          procs.innerHTML = '<div class="deckos-proc"><span>No user processes. Daemons and hunters appear here.</span></div>';
        }
        Array.prototype.forEach.call(procs.querySelectorAll("[data-kill]"), function (btn) {
          btn.onclick = function (ev) {
            ev.stopPropagation();
            try { if (typeof sfx !== "undefined") sfx.click(); } catch (_) {}
            apiPost("/api/action", { action: "kill_process", pid: Number(btn.getAttribute("data-kill")) }).then(function (res) {
              if (res && res.state) { try { renderHUD(res.state); } catch (_) {} renderSimPanels(res.state); }
              if (res && typeof addTerminalLog === "function") addTerminalLog((res && res.message) || "kill dispatched.", (res && res.ok) ? "success" : "warn");
            });
          };
        });
      }
      try {
        var hist = (data.state && data.state.cmd_history) || [];
        var histEl = $("deckos-history");
        if (histEl) {
          histEl.innerHTML = hist.length
            ? hist.slice(-8).map(function (entry, idx) {
              return '<div class="deckos-hist-line"><span>' + (hist.length > 8 ? hist.length - 8 + idx + 1 : idx + 1) + "</span> " + esc(entry) + "</div>";
            }).join("")
            : '<div class="deckos-hist-line">No commands logged this run yet. Terminal and cyberdeck share this log.</div>';
        }
      } catch (_) {}
    } catch (_) {}
    try {
      var arcs = (data.arcs && data.arcs.arcs) || [];
      var live = (data.arcs && data.arcs.live) || {};
      var liveByContact = { "Mira Voss": "mira_decay", "Kilo": "kilo_yield", "The Archivist": "archivist_wipe", "Agent Zero": "zero_counter" };
      varagrid = $("arcs-grid");
      if (agrid && arcs.length) {
        agrid.innerHTML = arcs.map(function (a) {
          var tag = live[liveByContact[a.name]] ? ' <span class="a-live">BONUS LIVE</span>' : "";
          return '<div class="arc-card" tabindex="0" aria-label="' + esc(a.name) + " arc stage " + a.stage + ' of 3">' +
            '<div class="a-name">' + esc(a.name) + " // " + esc(a.arc) + tag + "</div>" +
            '<div class="a-stage">' + esc(a.stage_label) + " (" + a.stage + "/3" + (a.next_trust ? " · next @ trust " + a.next_trust : " · MAX") + ")</div>" +
            '<div class="a-text">' + esc(a.stage_text) + "</div>" +
            (a.bonus ? '<div class="a-bonus">BONUS: ' + esc(a.bonus) + "</div>" : "") + "</div>";
        }).join("");
      }
    } catch (_) {}
  }

  function bindModal(openId, modalId, closeId) {
    var open = $(openId), modal = $(modalId), close = $(closeId);
    if (open && modal) open.addEventListener("click", function () {
      try { if (typeof sfx !== "undefined") sfx.click(); } catch (_) {}
      renderSimPanels(); modal.classList.remove("hidden");
    });
    if (close && modal) close.addEventListener("click", function () { modal.classList.add("hidden"); });
    if (modal) modal.addEventListener("click", function (ev) { if (ev.target === modal) modal.classList.add("hidden"); });
  }

  function bindShortcuts() {
    document.addEventListener("keydown", function (ev) {
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      var tag = (document.activeElement && document.activeElement.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      var k = (ev.key || "").toLowerCase();
      function click(id) { var el = $(id); if (el && !el.disabled) { el.click(); ev.preventDefault(); } }
      if (k === "g") { renderSimPanels(); var m = $("modal-sim"); if (m) { m.classList.remove("hidden"); ev.preventDefault(); } }
      else if (k === "t") { renderSimPanels(); var m2 = $("modal-arcs"); if (m2) { m2.classList.remove("hidden"); ev.preventDefault(); } }
      else if (k === "h") {
        document.body.classList.toggle("hc");
        try { localStorage.setItem("cyberpulse-hc", document.body.classList.contains("hc") ? "1" : "0"); } catch (_) {}
      }
      else if (k === "s") click("btn-scan");
      else if (k === "o") click("btn-overdrive");
      else if (k === "v") click("btn-spoof");
      else if (k === "l") click("btn-lay-low");
      else if (k === "j") click("btn-jackout");
      else if (k === "q") click("btn-quests-open");
      else if (k === "n") click("btn-contacts-open");
      else if (k === "d") click("btn-career-open");
    });
    try { if (localStorage.getItem("cyberpulse-hc") === "1") document.body.classList.add("hc"); } catch (_) {}
  }

  bindModal("btn-sim-open", "modal-sim", "btn-close-sim");
  bindModal("btn-arcs-open", "modal-arcs", "btn-close-arcs");
  bindShortcuts();
  setInterval(function () { try { renderSimPanels(); } catch (_) {} }, 2000);
  document.addEventListener("visibilitychange", function () { if (!document.hidden) { try { renderSimPanels(); } catch (_) {} } });
  window.cyberpulseRenderSimPanels = renderSimPanels;
})();
