"use strict";

// ── State ─────────────────────────────────────────────────────────────────
let token        = localStorage.getItem("ss_token") || "";
let username     = localStorage.getItem("ss_user")  || "";
let selectedFile = null;
let currentResult= null;
let scanHistory  = loadHistory();
let googleInited = false;

// ── Helpers ───────────────────────────────────────────────────────────────
const $  = id  => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);
function esc(s) { const d = document.createElement("div"); d.textContent = String(s||""); return d.innerHTML; }
function fmtBytes(b) { return b < 1048576 ? `${(b/1024).toFixed(1)} KB` : `${(b/1048576).toFixed(1)} MB`; }
function authHeader() { return token ? `Bearer ${token}` : ""; }
function showScreen(id) { $$(".screen").forEach(s => s.classList.remove("active")); $(id).classList.add("active"); }

// ── Sign data ─────────────────────────────────────────────────────────────
const SIGN_INFO = [
  { cat:"speed",       meaning:"Speed limit: 20 km/h. You must not drive faster than 20 km/h." },
  { cat:"speed",       meaning:"Speed limit: 30 km/h. You must not drive faster than 30 km/h." },
  { cat:"speed",       meaning:"Speed limit: 50 km/h. Common in town and city areas." },
  { cat:"speed",       meaning:"Speed limit: 60 km/h. Slow down and stay below 60 km/h." },
  { cat:"speed",       meaning:"Speed limit: 70 km/h. You must not exceed 70 km/h ahead." },
  { cat:"speed",       meaning:"Speed limit: 80 km/h. Keep your speed at or below 80 km/h." },
  { cat:"speed",       meaning:"End of 80 km/h speed restriction. Normal speed rules apply again." },
  { cat:"speed",       meaning:"Speed limit: 100 km/h. Common on motorways and highways." },
  { cat:"speed",       meaning:"Speed limit: 120 km/h. Found on high-speed roads." },
  { cat:"prohibition", meaning:"No overtaking allowed for all vehicles. Wait until the restriction ends." },
  { cat:"prohibition", meaning:"No overtaking for trucks. Applies to heavy goods vehicles." },
  { cat:"priority",    meaning:"Right of way at the next intersection. Other vehicles must yield to you." },
  { cat:"priority",    meaning:"You are on a priority road. You have right of way over side roads." },
  { cat:"priority",    meaning:"Yield! Give way to all traffic on the main road ahead." },
  { cat:"prohibition", meaning:"Stop completely! You must stop and give way before proceeding." },
  { cat:"prohibition", meaning:"No vehicles allowed. This road is closed to all traffic." },
  { cat:"prohibition", meaning:"No trucks allowed on this road." },
  { cat:"prohibition", meaning:"No entry. You cannot enter this road — it is one-way or restricted." },
  { cat:"warning",     meaning:"General hazard ahead. Proceed with caution and be alert." },
  { cat:"warning",     meaning:"Dangerous left curve ahead. Slow down and steer carefully." },
  { cat:"warning",     meaning:"Dangerous right curve ahead. Slow down and steer carefully." },
  { cat:"warning",     meaning:"Double bend ahead. First curves left, then right (or opposite)." },
  { cat:"warning",     meaning:"Bumpy road ahead. Reduce speed to avoid damage or loss of control." },
  { cat:"warning",     meaning:"Slippery road surface ahead. Drive slowly and avoid hard braking." },
  { cat:"warning",     meaning:"Road narrows on the right ahead. Allow room for other vehicles." },
  { cat:"warning",     meaning:"Road works ahead. Expect delays, reduced speed, and workers on road." },
  { cat:"warning",     meaning:"Traffic lights ahead. Be prepared to stop." },
  { cat:"warning",     meaning:"Pedestrians crossing ahead. Watch out for people on the road." },
  { cat:"warning",     meaning:"Children crossing ahead. Drive very carefully near schools or play areas." },
  { cat:"warning",     meaning:"Cyclists crossing ahead. Watch for bicycles entering the road." },
  { cat:"warning",     meaning:"Ice or snow on road ahead. Use extreme caution; road may be slippery." },
  { cat:"warning",     meaning:"Wild animals may cross the road ahead. Be ready to brake." },
  { cat:"speed",       meaning:"End of all speed and overtaking restrictions. Normal rules resume." },
  { cat:"direction",   meaning:"Turn right ahead. You must turn right at the next junction." },
  { cat:"direction",   meaning:"Turn left ahead. You must turn left at the next junction." },
  { cat:"direction",   meaning:"Ahead only. You must continue straight — no turning allowed." },
  { cat:"direction",   meaning:"Go straight or turn right. Both options are permitted ahead." },
  { cat:"direction",   meaning:"Go straight or turn left. Both options are permitted ahead." },
  { cat:"direction",   meaning:"Keep right. You must stay to the right of the obstacle or lane divider." },
  { cat:"direction",   meaning:"Keep left. You must stay to the left of the obstacle or lane divider." },
  { cat:"direction",   meaning:"Roundabout ahead. Give way to traffic already on the roundabout." },
  { cat:"prohibition", meaning:"End of no-overtaking zone. You may now overtake again." },
  { cat:"prohibition", meaning:"End of no-overtaking zone for trucks. Trucks may now overtake." },
];
const CAT_LABELS = { speed:"Speed Limit", prohibition:"Prohibition", warning:"Warning", direction:"Direction", priority:"Priority" };
const CLASS_NAMES_UI = [
  "Speed Limit 20","Speed Limit 30","Speed Limit 50","Speed Limit 60","Speed Limit 70",
  "Speed Limit 80","End Speed Limit 80","Speed Limit 100","Speed Limit 120",
  "No Passing","No Passing (Trucks)","Priority Road Intersection","Priority Road",
  "Yield","Stop","No Vehicles","No Trucks","No Entry","General Caution",
  "Dangerous Curve Left","Dangerous Curve Right","Double Curve","Bumpy Road",
  "Slippery Road","Road Narrows Right","Road Work","Traffic Signals","Pedestrians",
  "Children Crossing","Bicycles Crossing","Beware Ice/Snow","Wild Animals Crossing",
  "End Speed & Pass Limits","Turn Right Ahead","Turn Left Ahead","Ahead Only",
  "Straight or Right","Straight or Left","Keep Right","Keep Left",
  "Roundabout","End No Passing","End No Passing (Trucks)",
];

// ── Boot ──────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  await fetchConfig();   // loads Google client ID
  if (token && username) {
    enterApp();
  } else {
    showScreen("screenLanding");
  }
  bindLanding();
  bindAuth();
  bindApp();
});

// ── Google OAuth ──────────────────────────────────────────────────────────
async function fetchConfig() {
  try {
    const res  = await fetch("/api/config");
    const data = await res.json();
    const gid  = data.google_client_id || "";
    if (gid) {
      // Wait for the GIS script to load (it's async)
      await waitForGoogle();
      initGoogleAuth(gid);
    }
  } catch { /* config endpoint not critical */ }
}

function waitForGoogle(ms = 5000) {
  return new Promise(resolve => {
    if (typeof google !== "undefined" && google.accounts) { resolve(); return; }
    const t = Date.now();
    const poll = setInterval(() => {
      if (typeof google !== "undefined" && google.accounts) { clearInterval(poll); resolve(); }
      if (Date.now() - t > ms) { clearInterval(poll); resolve(); }
    }, 100);
  });
}

function initGoogleAuth(clientId) {
  if (googleInited || !clientId) return;
  googleInited = true;
  google.accounts.id.initialize({
    client_id: clientId,
    callback:  handleGoogleCredential,
    auto_select: false,
  });
  const opts = { theme: "outline", size: "large", width: 350, text: "continue_with" };
  const b1   = $("googleBtnLogin");
  const b2   = $("googleBtnRegister");
  if (b1) google.accounts.id.renderButton(b1, opts);
  if (b2) google.accounts.id.renderButton(b2, opts);
  // Show dividers
  ["loginDivider","registerDivider"].forEach(id => {
    const el = $(id); if (el) el.style.display = "";
  });
}

async function handleGoogleCredential(response) {
  try {
    const res  = await fetch("/api/auth/google", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential: response.credential }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Google sign-in failed.");
    token    = data.token;
    username = data.username;
    localStorage.setItem("ss_token", token);
    localStorage.setItem("ss_user",  username);
    enterApp();
    toast(`Welcome, ${username}! 👋`, "success");
  } catch (err) {
    toast(err.message || "Google sign-in failed. Please try again.", "error");
  }
}

// ── Password validation ───────────────────────────────────────────────────
function validatePassword(p) {
  if (p.length < 8)            return "Password must be at least 8 characters long.";
  if (!/\d/.test(p))           return "Password must contain at least one number (0-9).";
  if (!/[!@#$%^&*()\-_=+\[\]{}|;:'",.<>?\/\\`~]/.test(p))
                               return "Password must contain at least one special character (!@#$%…).";
  return null;
}

// ── Landing ───────────────────────────────────────────────────────────────
function bindLanding() {
  $("btnGoLogin").addEventListener("click",    () => { showScreen("screenAuth"); showAuthForm("login"); });
  $("btnGoRegister").addEventListener("click", () => { showScreen("screenAuth"); showAuthForm("register"); });
  $("btnHeroStart").addEventListener("click",  () => { showScreen("screenAuth"); showAuthForm("register"); });
}

// ── Auth ──────────────────────────────────────────────────────────────────
function showAuthForm(which, opts = {}) {
  $("formLogin").classList.toggle("hidden",    which !== "login");
  $("formRegister").classList.toggle("hidden", which !== "register");
  $("loginError").classList.add("hidden");
  $("registerError").classList.add("hidden");
  $("loginSuccess").classList.add("hidden");

  if (opts.successMsg) {
    const el = $("loginSuccess");
    el.textContent = opts.successMsg;
    el.classList.remove("hidden");
  }
  if (opts.prefillUsername) {
    $("loginUsername").value = opts.prefillUsername;
    $("loginPassword").value = "";
    $("loginPassword").focus();
  }
}

function bindAuth() {
  $("btnSwitchRegister").addEventListener("click", () => showAuthForm("register"));
  $("btnSwitchLogin").addEventListener("click",    () => showAuthForm("login"));
  $("btnAuthBackLogin").addEventListener("click",    () => showScreen("screenLanding"));
  $("btnAuthBackRegister").addEventListener("click", () => showScreen("screenLanding"));
  $("btnLogin").addEventListener("click", doLogin);
  $("btnRegister").addEventListener("click", doRegister);
  $("loginPassword").addEventListener("keydown", e => { if (e.key === "Enter") doLogin(); });
  $("regPassword").addEventListener("keydown",   e => { if (e.key === "Enter") doRegister(); });
}

async function doRegister() {
  const u    = $("regUsername").value.trim();
  const p    = $("regPassword").value;
  const errEl = $("registerError");
  errEl.classList.add("hidden");
  if (!u)           { showFormError(errEl, "Please enter a username."); return; }
  const pwErr = validatePassword(p);
  if (pwErr)        { showFormError(errEl, pwErr); return; }

  $("btnRegister").disabled = true;
  $("btnRegister").textContent = "Creating account…";
  try {
    const res  = await fetch("/api/auth/register", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Registration failed.");

    // ✅ IMPORTANT: Do NOT auto-login. Redirect to login with success message.
    showScreen("screenAuth");
    showAuthForm("login", {
      successMsg: "✓ Account created successfully! Please log in.",
      prefillUsername: u,
    });
    toast("Account created! Please log in.", "success");
  } catch (err) {
    showFormError(errEl, err.message);
  } finally {
    $("btnRegister").disabled = false;
    $("btnRegister").textContent = "Create account";
  }
}

async function doLogin() {
  const u    = $("loginUsername").value.trim();
  const p    = $("loginPassword").value;
  const errEl = $("loginError");
  errEl.classList.add("hidden");
  if (!u || !p) { showFormError(errEl, "Please enter your username and password."); return; }

  $("btnLogin").disabled = true;
  $("btnLogin").textContent = "Logging in…";
  try {
    const res  = await fetch("/api/auth/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed.");
    token    = data.token;
    username = data.username;
    localStorage.setItem("ss_token", token);
    localStorage.setItem("ss_user",  username);
    enterApp();
  } catch (err) {
    showFormError(errEl, err.message);
  } finally {
    $("btnLogin").disabled = false;
    $("btnLogin").textContent = "Log in";
  }
}

function showFormError(el, msg) { el.textContent = msg; el.classList.remove("hidden"); }

// ── App entry ─────────────────────────────────────────────────────────────
function enterApp() {
  $("userGreeting").textContent = `👋 Hi, ${username}!`;
  showScreen("screenApp");
  showTab("scan");
  showScanState("upload");
  renderHistory();
}

// ── App bindings ──────────────────────────────────────────────────────────
function bindApp() {
  $$(".tab-btn").forEach(btn => btn.addEventListener("click", () => showTab(btn.dataset.tab)));

  $("btnLogout").addEventListener("click", async () => {
    await fetch("/api/auth/logout", { method: "POST", headers: { Authorization: authHeader() } }).catch(()=>{});
    token = ""; username = "";
    localStorage.removeItem("ss_token"); localStorage.removeItem("ss_user");
    showScreen("screenLanding");
    toast("Logged out.", "info");
  });

  const zone = $("uploadArea");
  zone.addEventListener("click",  () => $("fileInput").click());
  zone.addEventListener("keydown", e => { if (e.key==="Enter"||e.key===" ") $("fileInput").click(); });
  zone.addEventListener("dragover",  e => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", e => { e.preventDefault(); zone.classList.remove("dragover"); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); });
  $("fileInput").addEventListener("change", e => { if (e.target.files[0]) handleFile(e.target.files[0]); });

  $("btnChangeImage").addEventListener("click", () => { resetFile(); showScanState("upload"); });
  $("btnScan").addEventListener("click", runScan);
  $("btnScanAnother").addEventListener("click",  () => { resetFile(); showScanState("upload"); });
  $("btnTryAgain").addEventListener("click",     () => { resetFile(); showScanState("upload"); });
  $("btnDownloadResult").addEventListener("click", downloadResult);
  $("btnClearHistory").addEventListener("click", clearHistory);
  $("btnGoScan").addEventListener("click",       () => showTab("scan"));
  $("togAnnotated").addEventListener("click", () => toggleResultImg("annotated"));
  $("togOriginal").addEventListener("click",  () => toggleResultImg("original"));
}

function showTab(name) {
  $$(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === name));
  // IMPORTANT: must toggle the 'hidden' class (display:none !important) not just style.display
  const isScan = name === "scan";
  $( "panelScan").classList.toggle("hidden", !isScan);
  $("panelScan").classList.toggle("active",  isScan);
  $("panelHistory").classList.toggle("hidden",  isScan);
  $("panelHistory").classList.toggle("active", !isScan);
  if (name === "history") renderHistory();
}

function showScanState(name) {
  ["upload","preview","processing","result"].forEach(s => {
    const el = $(`state${s.charAt(0).toUpperCase()+s.slice(1)}`);
    el.classList.toggle("hidden", s !== name);
  });
}

// ── File handling ─────────────────────────────────────────────────────────
function handleFile(file) {
  const ok = (file.type && file.type.startsWith("image/")) || file.name.toLowerCase().endsWith(".ppm");
  if (!ok)                      return toast("Please choose a valid image file.", "error");
  if (file.size > 50*1024*1024) return toast("File is too large (max 50 MB).", "error");
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = ev => {
    $("previewImg").src          = ev.target.result;
    $("previewName").textContent = file.name;
    $("previewSz").textContent   = fmtBytes(file.size);
    showScanState("preview");
  };
  reader.readAsDataURL(file);
}

function resetFile() { selectedFile = null; $("fileInput").value = ""; }

// ── Scan ──────────────────────────────────────────────────────────────────
async function runScan() {
  if (!selectedFile) return;
  showScanState("processing");
  const steps = ["ps1","ps2","ps3","ps4"];
  const timer = animSteps(steps);
  try {
    const fd = new FormData();
    fd.append("file", selectedFile);
    const res  = await fetch("/api/analyze?confidence=0.25", {
      method: "POST", body: fd,
      headers: { Authorization: authHeader() },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Scan failed.");
    clearInterval(timer); finishSteps(steps);
    currentResult = data;
    saveHistory(data);
    setTimeout(() => { resetSteps(steps); renderResult(data); showScanState("result"); }, 400);
  } catch (err) {
    clearInterval(timer); resetSteps(steps);
    showScanState("upload");
    toast(err.message || "Scan failed. Please try again.", "error");
  }
}

function animSteps(ids) {
  let i = 0;
  return setInterval(() => {
    if (i >= ids.length) return;
    if (i > 0) { $(ids[i-1]).classList.remove("active"); $(ids[i-1]).classList.add("done"); }
    $(ids[i]).classList.add("active"); i++;
  }, 700);
}
function finishSteps(ids) { ids.forEach(id => { $(id).classList.remove("active"); $(id).classList.add("done"); }); }
function resetSteps(ids)  { ids.forEach(id => $(id).classList.remove("active","done")); }

// ── Result ────────────────────────────────────────────────────────────────
function renderResult(data) {
  const dets = data.detections || [];
  const n    = dets.length;

  $("bannerFound").textContent = n === 0 ? "No signs detected" : n === 1 ? "We found 1 traffic sign" : `We found ${n} traffic signs`;
  $("bannerTop").textContent   = n > 0 ? `Top result: ${CLASS_NAMES_UI[dets[0].class_id] || dets[0].class_name} — ${(dets[0].confidence*100).toFixed(0)}% confident` : "";

  const cards = $("detectedCards");
  cards.innerHTML = "";
  if (n === 0) {
    $("noSign").classList.remove("hidden");
    cards.classList.add("hidden");
  } else {
    $("noSign").classList.add("hidden");
    cards.classList.remove("hidden");
    dets.forEach(d => {
      const info     = SIGN_INFO[d.class_id] || { cat:"direction", meaning:"Traffic sign detected." };
      const name     = CLASS_NAMES_UI[d.class_id] || d.class_name;
      const pct      = (d.confidence * 100).toFixed(0);
      const lvl      = d.confidence >= 0.7 ? "high" : d.confidence >= 0.4 ? "med" : "low";
      const catLabel = CAT_LABELS[info.cat] || "Sign";
      const card     = document.createElement("div");
      card.className = "det-result-card";
      card.innerHTML = `
        <div class="det-result-head">
          <div class="det-result-name">${esc(name)}</div>
          <span class="det-result-cat cat-${info.cat}">${esc(catLabel)}</span>
        </div>
        <p class="det-meaning">${esc(info.meaning)}</p>
        <div class="conf-row">
          <span class="conf-label">Confidence</span>
          <div class="conf-bar"><div class="conf-fill conf-${lvl}" style="width:${pct}%"></div></div>
          <span class="conf-pct">${pct}%</span>
        </div>
        ${d.extracted_text ? `<div class="det-ocr-text">📝 Text on sign: "${esc(d.extracted_text)}"</div>` : ""}
      `;
      cards.appendChild(card);
    });
  }

  $("resultImg").src = data.annotated_image;
  $("togAnnotated").classList.add("active");
  $("togOriginal").classList.remove("active");

  const ocrText = data.extracted_text || data.global_text || "";
  if (ocrText && n > 0) {
    $("ocrWrap").classList.remove("hidden");
    $("ocrText").textContent = ocrText;
  } else {
    $("ocrWrap").classList.add("hidden");
  }
}

function toggleResultImg(which) {
  if (!currentResult) return;
  $("resultImg").src = which === "annotated" ? currentResult.annotated_image : (currentResult.original_image || currentResult.annotated_image);
  $("togAnnotated").classList.toggle("active", which === "annotated");
  $("togOriginal").classList.toggle("active",  which === "original");
}

function downloadResult() {
  if (!currentResult?.annotated_image) return toast("No image to download.", "error");
  const a = document.createElement("a");
  a.href = currentResult.annotated_image;
  a.download = `signscan_${currentResult.filename || "result"}.jpg`;
  a.click();
}

// ── History ───────────────────────────────────────────────────────────────
function saveHistory(data) {
  const entry = {
    id: Date.now(), filename: data.filename || "image",
    detections: data.total_detections || 0,
    topSign: data.detections?.[0] ? (CLASS_NAMES_UI[data.detections[0].class_id] || data.detections[0].class_name) : "—",
    time: new Date().toLocaleString(), thumbnail: data.annotated_image, data,
  };
  scanHistory = [entry, ...scanHistory].slice(0, 10);
  try { localStorage.setItem("ss_history", JSON.stringify(scanHistory)); } catch { scanHistory = scanHistory.slice(0,5); }
}

function loadHistory() { try { return JSON.parse(localStorage.getItem("ss_history") || "[]"); } catch { return []; } }

function renderHistory() {
  const grid = $("historyGrid"), empty = $("historyEmpty");
  grid.innerHTML = "";
  if (!scanHistory.length) { empty.classList.remove("hidden"); grid.classList.add("hidden"); return; }
  empty.classList.add("hidden"); grid.classList.remove("hidden");
  scanHistory.forEach(e => {
    const card = document.createElement("article");
    card.className = "hist-card";
    card.innerHTML = `
      <img src="${e.thumbnail}" alt="${esc(e.filename)}">
      <div class="hist-card-body">
        <div class="hist-card-name">${esc(e.topSign !== "—" ? e.topSign : e.filename)}</div>
        <div class="hist-card-meta">${e.detections} sign(s) · ${e.time}</div>
      </div>`;
    card.addEventListener("click", () => { currentResult = e.data; renderResult(e.data); showTab("scan"); showScanState("result"); });
    grid.appendChild(card);
  });
}

function clearHistory() { scanHistory = []; localStorage.removeItem("ss_history"); renderHistory(); toast("Scan history cleared.", "info"); }

// ── Toasts ────────────────────────────────────────────────────────────────
function toast(msg, type = "info") {
  const t = document.createElement("div");
  t.className = `toast ${type}`; t.textContent = msg;
  $("toastWrap").appendChild(t);
  setTimeout(() => t.remove(), 3800);
}
