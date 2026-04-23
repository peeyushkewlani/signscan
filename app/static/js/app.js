
import { Renderer, Program, Triangle, Mesh } from 'https://esm.sh/ogl@1.0.11';

// ── WebGL LightRays Component (Vanilla JS Port) ──────────────────────────
class LightRays {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;
    
    this.options = {
      raysOrigin: 'top-center', raysColor: '#00ffff', raysSpeed: 1.5,
      lightSpread: 1.2, rayLength: 1.8, pulsating: false, fadeDistance: 1.0,
      saturation: 1.0, followMouse: true, mouseInfluence: 0.3,
      noiseAmount: 0.03, distortion: 0.08, ...options
    };
    
    this.mouse = { x: 0.5, y: 0.5 };
    this.smoothMouse = { x: 0.5, y: 0.5 };
    this.init();
  }

  hexToRgb(hex) {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return m ? [parseInt(m[1], 16)/255, parseInt(m[2], 16)/255, parseInt(m[3], 16)/255] : [1,1,1];
  }

  getAnchorAndDir(origin, w, h) {
    const out = 0.2;
    switch(origin) {
      case 'top-left': return { a: [0, -out*h], d: [0.7, 0.7] };
      case 'top-right': return { a: [w, -out*h], d: [-0.7, 0.7] };
      case 'bottom-center': return { a: [0.5*w, (1+out)*h], d: [0, -1] };
      default: return { a: [0.5*w, -out*h], d: [0, 1] }; // top-center
    }
  }

  init() {
    this.renderer = new Renderer({ dpr: Math.min(window.devicePixelRatio, 2), alpha: true });
    const gl = this.renderer.gl;
    this.container.appendChild(gl.canvas);

    const vert = `attribute vec2 position; varying vec2 vUv; void main() { vUv = position * 0.5 + 0.5; gl_Position = vec4(position, 0.0, 1.0); }`;
    const frag = `
      precision highp float;
      uniform float iTime; uniform vec2 iResolution; uniform vec2 rayPos; uniform vec2 rayDir;
      uniform vec3 raysColor; uniform float raysSpeed; uniform float lightSpread; uniform float rayLength;
      uniform float fadeDistance; uniform vec2 mousePos; uniform float mouseInfluence;
      uniform float noiseAmount; uniform float distortion;
      
      float noise(vec2 st) { return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123); }
      
      float rayStrength(vec2 src, vec2 dir, vec2 coord, float sA, float sB, float spd) {
        vec2 diff = coord - src; vec2 norm = normalize(diff);
        float cosA = dot(norm, dir);
        float distA = cosA + distortion * sin(iTime*1.5 + length(diff)*0.005);
        float spread = pow(max(distA, 0.0), 1.0/max(lightSpread, 0.001));
        float d = length(diff); float maxD = max(iResolution.x, iResolution.y) * rayLength;
        float falloff = clamp((maxD - d)/maxD, 0.0, 1.0);
        float fadeF = fadeDistance * max(iResolution.x, iResolution.y);
        float fadeOff = clamp((fadeF - d)/fadeF, 0.0, 1.0);
        float base = clamp((0.5 + 0.2*sin(distA*sA + iTime*spd)) + (0.3 + 0.2*cos(-distA*sB + iTime*spd*0.8)), 0.0, 1.0);
        return base * falloff * fadeOff * spread;
      }
      
      void main() {
        vec2 coord = gl_FragCoord.xy; vec2 fDir = normalize(rayDir);
        if(mouseInfluence > 0.0) {
          vec2 mDir = normalize((mousePos * iResolution.xy) - rayPos);
          fDir = normalize(mix(fDir, mDir, mouseInfluence));
        }
        float r1 = rayStrength(rayPos, fDir, coord, 45.2, 31.4, 0.8*raysSpeed);
        float r2 = rayStrength(rayPos, fDir, coord, 28.5, 19.8, 1.2*raysSpeed);
        float r3 = rayStrength(rayPos, fDir, coord, 12.1, 56.2, 0.5*raysSpeed);
        float comb = pow(r1*0.4 + r2*0.4 + r3*0.2, 0.7) * 1.5;
        vec3 col = raysColor * comb;
        if(noiseAmount > 0.0) col *= (1.0 - noiseAmount + noiseAmount*noise(coord*0.01 + iTime*0.05));
        gl_FragColor = vec4(col, comb);
      }
    `;

    this.uniforms = {
      iTime: { value: 0 }, iResolution: { value: [1,1] }, rayPos: { value: [0,0] }, rayDir: { value: [0,1] },
      raysColor: { value: this.hexToRgb(this.options.raysColor) }, raysSpeed: { value: this.options.raysSpeed },
      lightSpread: { value: this.options.lightSpread }, rayLength: { value: this.options.rayLength },
      fadeDistance: { value: this.options.fadeDistance }, mousePos: { value: [0.5,0.5] },
      mouseInfluence: { value: this.options.mouseInfluence }, noiseAmount: { value: this.options.noiseAmount },
      distortion: { value: this.options.distortion }
    };

    const geometry = new Triangle(gl);
    const program = new Program(gl, { vertex: vert, fragment: frag, uniforms: this.uniforms, transparent: true });
    this.mesh = new Mesh(gl, { geometry, program });

    this.resize = () => {
      const wCSS = this.container.clientWidth, hCSS = this.container.clientHeight;
      this.renderer.setSize(wCSS, hCSS);
      const w = wCSS * this.renderer.dpr, h = hCSS * this.renderer.dpr;
      this.uniforms.iResolution.value = [w, h];
      const { a, d } = this.getAnchorAndDir(this.options.raysOrigin, w, h);
      this.uniforms.rayPos.value = a; this.uniforms.rayDir.value = d;
    };
    window.addEventListener('resize', this.resize);
    this.resize();

    window.addEventListener('mousemove', e => {
      this.mouse.x = e.clientX / window.innerWidth;
      this.mouse.y = e.clientY / window.innerHeight;
    });

    requestAnimationFrame(t => this.loop(t));
  }

  loop(t) {
    this.uniforms.iTime.value = t * 0.001;
    this.smoothMouse.x = this.smoothMouse.x * 0.95 + this.mouse.x * 0.05;
    this.smoothMouse.y = this.smoothMouse.y * 0.95 + this.mouse.y * 0.05;
    this.uniforms.mousePos.value = [this.smoothMouse.x, 1.0 - this.smoothMouse.y];
    this.renderer.render({ scene: this.mesh });
    requestAnimationFrame(t => this.loop(t));
  }
}

// ── Application Logic ────────────────────────────────────────────────────
let currentUser = null;

const $ = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

// Init
document.addEventListener("DOMContentLoaded", async () => {
  new LightRays('lightrays-container');
  checkToken();
  bindEvents();
});

// Auth Routing Logic
window.handleHeroAction = () => {
    if (localStorage.getItem("auth_token")) {
        navigate('app');
    } else {
        navigate('auth');
    }
};

window.navigate = (screenId) => {
  // If navigating to home and logged in, redirect to dashboard silently or just let them see home but ensure button works.
  // We will let them see home, handleHeroAction will do the right thing.
  $$('.screen').forEach(s => {
    if(s.id === `screen-${screenId}`) {
      s.style.display = 'block';
      setTimeout(() => s.classList.add('active'), 10);
    } else {
      s.classList.remove('active');
      s.style.display = 'none';
    }
  });
  $$('.nav-link').forEach(l => l.classList.remove('active'));
  const link = document.querySelector(`.nav-link[onclick="navigate('${screenId}')"]`);
  if(link) link.classList.add('active');
  
  if(screenId === 'app') loadProfile();
};

window.switchAppTab = (tabId) => {
  $$('.app-tab').forEach(t => t.style.display = 'none');
  $(`tab-${tabId}`).style.display = 'block';
  $$('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`button[onclick="switchAppTab('${tabId}')"]`).classList.add('active');
  if(tabId === 'history') loadHistory();
};

window.toggleAuth = () => {
  const login = $('formLogin');
  const reg = $('formRegister');
  login.style.display = login.style.display === 'none' ? 'block' : 'none';
  reg.style.display = reg.style.display === 'none' ? 'block' : 'none';
  $('loginError').style.display = 'none'; 
  $('registerError').style.display = 'none';
};

// Auth
function checkToken() {
  const t = localStorage.getItem("auth_token");
  const u = localStorage.getItem("username");
  if(t && u) {
    currentUser = u;
    $('navLoginBtn').style.display = 'none';
    $('navLogoutBtn').style.display = 'block';
    $('navDashboardBtn').style.display = 'block';
    $('navUsernameDisplay').textContent = u;
    
    // Auth Flow: update hero button text
    if ($('heroActionBtn')) {
        $('heroActionBtn').textContent = 'Go to Dashboard';
    }
  } else {
    currentUser = null;
    $('navLoginBtn').style.display = 'block';
    $('navLogoutBtn').style.display = 'none';
    $('navDashboardBtn').style.display = 'none';
    $('navUsernameDisplay').textContent = 'Dashboard';
    
    if ($('heroActionBtn')) {
        $('heroActionBtn').textContent = 'Get Started';
    }
  }
}

window.logout = () => {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("username");
  localStorage.removeItem("account_type");
  localStorage.removeItem("join_date");
  checkToken();
  navigate('home');
};

async function handleLogin() {
  const u = $('logUsername').value.trim(), p = $('logPassword').value;
  const btn = $('btnLoginAction'), err = $('loginError');
  err.style.display = 'none';
  if(!u || !p) { err.textContent = "Please fill all fields."; err.style.display = 'block'; return; }
  
  btn.textContent = "Loading..."; btn.disabled = true;
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({username: u, password: p})
    });
    const data = await res.json();
    if(res.ok) {
      localStorage.setItem("auth_token", data.token);
      localStorage.setItem("username", data.username);
      localStorage.setItem("account_type", data.account_type);
      localStorage.setItem("join_date", data.join_date);
      checkToken(); navigate('app');
    } else {
      err.textContent = data.error || "Login failed"; err.style.display = 'block';
    }
  } catch(e) { err.textContent = "Network error"; err.style.display = 'block'; }
  btn.textContent = "Log In"; btn.disabled = false;
}

async function handleRegister() {
  const u = $('regUsername').value.trim(), p = $('regPassword').value;
  const btn = $('btnRegisterAction'), err = $('registerError');
  err.style.display = 'none';
  if(!u || !p) { err.textContent = "Please fill all fields."; err.style.display = 'block'; return; }
  
  btn.textContent = "Loading..."; btn.disabled = true;
  try {
    const res = await fetch("/api/auth/register", {
      method: "POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({username: u, password: p})
    });
    const data = await res.json();
    if(res.ok) {
      alert("Account created! Please log in.");
      toggleAuth();
      $('logUsername').value = u;
    } else {
      err.textContent = data.error || "Registration failed"; err.style.display = 'block';
    }
  } catch(e) { err.textContent = "Network error"; err.style.display = 'block'; }
  btn.textContent = "Create Account"; btn.disabled = false;
}

// Profile Header
function loadProfile() {
  $('profUsernameHeading').textContent = localStorage.getItem("username") || "User";
  $('profTypeHeader').textContent = localStorage.getItem("account_type") || "Local";
  $('profJoinedHeader').textContent = localStorage.getItem("join_date") || "Unknown";
}

// Scanner
let selectedFile = null;
let currentScanId = 0;

window.resetScan = () => {
    currentScanId++;
    selectedFile = null;
    $('uploadArea').style.display = 'block';
    $('previewContainer').style.display = 'none';
    $('scanActions').style.display = 'none';
    $('scanResult').style.display = 'none';
    
    // reset placeholder
    $('scanPlaceholder').style.display = 'block';
    $('scanPlaceholder').innerHTML = '<svg class="w-16 h-16 mx-auto mb-4 opacity-20" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg><p>Upload an image to see results here</p>';
    
    $('fileInput').value = '';
};

function handleFileSelect(e) {
  currentScanId++;
  const file = e.target.files ? e.target.files[0] : e.dataTransfer?.files[0];
  if(!file) return;
  selectedFile = file;
  
  $('uploadArea').style.display = 'none';
  $('previewContainer').style.display = 'block';
  $('scanActions').style.display = 'flex';
  $('scanResult').style.display = 'none';
  
  // UX: Show ready text in placeholder instead of "Upload an image"
  $('scanPlaceholder').style.display = 'block';
  $('scanPlaceholder').innerHTML = '<svg class="w-16 h-16 mx-auto mb-4 opacity-50 text-primary" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9v-2h2v2zm0-4H9V7h2v5z"/></svg><p class="text-primary font-medium text-lg">Ready to scan!</p><p class="text-sm mt-2">Click the <b>Scan Image</b> button to analyze.</p>';
  
  const reader = new FileReader();
  reader.onload = e => $('imagePreview').src = e.target.result;
  reader.readAsDataURL(file);
}

const loaderTexts = [
    "Reading your photo...",
    "Detecting the sign...",
    "Reading visible text...",
    "Preparing your result..."
];

async function handleScan() {
  if(!selectedFile) return;
  const btn = $('btnScan');
  btn.textContent = "Analyzing..."; btn.disabled = true;
  
  const scanId = ++currentScanId;
  
  // Show animated loader
  const loader = $('scanLoader');
  const loaderText = $('loaderText');
  loader.style.display = 'flex';
  
  let textIndex = 0;
  loaderText.textContent = loaderTexts[0];
  const interval = setInterval(() => {
      textIndex = (textIndex + 1) % loaderTexts.length;
      loaderText.textContent = loaderTexts[textIndex];
  }, 800);
  
  const formData = new FormData();
  formData.append("file", selectedFile);
  
  try {
    const res = await fetch("/api/analyze", { 
        method: "POST", 
        body: formData,
        headers: {
            "Authorization": `Bearer ${localStorage.getItem("auth_token")}`
        }
    });
    
    if (scanId !== currentScanId) {
        clearInterval(interval);
        return; // User canceled or uploaded a new image while waiting
    }
    
    if (res.status === 401) {
        alert("Session expired. Please log in again.");
        logout();
        return;
    }
    
    const data = await res.json();
    
    // Stop loader
    clearInterval(interval);
    loader.style.display = 'none';
    $('scanPlaceholder').style.display = 'none';
    
    if(res.ok && data.detections && data.detections.length > 0) {
      const best = data.detections[0];
      $('resClass').textContent = best.class_name;
      $('resConf').textContent = `Confidence: ${(best.confidence * 100).toFixed(1)}%`;
      $('scanResult').style.display = 'block';
      saveHistory(best, $('imagePreview').src);
    } else {
      $('resClass').textContent = "No Sign Detected";
      $('resConf').textContent = "Please try another image.";
      $('scanResult').style.display = 'block';
    }
  } catch(e) { 
      if (scanId === currentScanId) {
          clearInterval(interval);
          loader.style.display = 'none';
          alert("Network error during scan."); 
      }
  }
  if (scanId === currentScanId) {
      btn.textContent = "Scan Image"; btn.disabled = false;
  }
}

// History
function saveHistory(result, imgUrl) {
  if (!currentUser) return;
  const key = `scan_history_${currentUser}`;
  let hist = [];
  try {
      hist = JSON.parse(localStorage.getItem(key) || "[]");
  } catch(e) {
      hist = [];
  }
  
  // Create a clean object to save
  const newScan = {
      date: new Date().toLocaleString(),
      className: result.class_name || "Unknown",
      confidence: result.confidence || 0,
      imgUrl: imgUrl
  };
  
  hist.unshift(newScan);
  if(hist.length > 20) hist.pop();
  localStorage.setItem(key, JSON.stringify(hist));
}

function loadHistory() {
  if (!currentUser) return;
  const key = `scan_history_${currentUser}`;
  let hist = [];
  try {
      hist = JSON.parse(localStorage.getItem(key) || "[]");
  } catch(e) {
      hist = [];
  }
  const list = $('historyList');
  if(!hist || hist.length === 0) {
    list.innerHTML = '<p class="text-muted text-center py-8">No recent scans found.</p>';
    return;
  }
  
  let html = '';
  hist.forEach(h => {
      // Handle both old and new data structures gracefully
      if (!h) return;
      const conf = h.confidence !== undefined ? h.confidence : (h.result && h.result.confidence ? h.result.confidence : 0);
      const name = h.className || (h.result && h.result.class_name) || 'Unknown';
      const confPercent = (conf * 100).toFixed(1);
      
      html += `
        <div class="glass-card flex gap-4 p-4 items-center mb-4 border border-white/5 bg-white/5">
          <img src="${h.imgUrl}" class="w-20 h-20 object-cover rounded-md border border-white/10">
          <div>
            <h4 class="text-primary font-medium text-xl">${name}</h4>
            <p class="text-muted text-sm mt-1">${confPercent}% confidence • ${h.date}</p>
          </div>
        </div>
      `;
  });
  list.innerHTML = html || '<p class="text-muted text-center py-8">No valid scans found.</p>';
}

// Events Setup
function bindEvents() {
  $('btnLoginAction').addEventListener('click', handleLogin);
  $('btnRegisterAction').addEventListener('click', handleRegister);
  $('btnScan').addEventListener('click', handleScan);
  
  const drop = $('uploadArea');
  drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('dragover'); });
  drop.addEventListener('dragleave', () => drop.classList.remove('dragover'));
  drop.addEventListener('drop', e => { e.preventDefault(); drop.classList.remove('dragover'); handleFileSelect(e); });
  
  $('uploadArea').addEventListener('click', () => $('fileInput').click());
  $('fileInput').addEventListener('change', handleFileSelect);
}
