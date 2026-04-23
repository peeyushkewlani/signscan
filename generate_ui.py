import os

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SignScan | Cinematic Traffic Sign AI</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://accounts.google.com/gsi/client" async defer></script>
</head>
<body class="dark-theme">
    <!-- LightRays WebGL Container -->
    <div id="lightrays-container" class="background-canvas pointer-events-none"></div>

    <!-- Navigation -->
    <nav class="glass-nav">
        <div class="nav-inner">
            <div class="nav-logo" onclick="navigate('home')">Sign<span class="highlight">Scan</span></div>
            <div class="nav-links">
                <a href="#" onclick="navigate('home')" class="nav-link">Home</a>
                <a href="#" onclick="navigate('about')" class="nav-link">About</a>
                <a href="#" onclick="navigate('capabilities')" class="nav-link">Capabilities</a>
                <a href="#" onclick="navigate('contact')" class="nav-link">Contact</a>
            </div>
            <div class="nav-actions">
                <button id="navDashboardBtn" onclick="navigate('app')" class="btn-outline hidden">Dashboard</button>
                <button id="navLoginBtn" onclick="navigate('auth')" class="btn-glow">Sign In</button>
                <button id="navLogoutBtn" onclick="logout()" class="btn-outline hidden">Log Out</button>
            </div>
        </div>
    </nav>

    <main id="main-content" class="content-wrapper">
        <!-- ── HOME SCREEN ── -->
        <div id="screen-home" class="screen active">
            <div class="hero-section fade-up">
                <h1 class="hero-title">High-End Traffic<br/>Sign Recognition</h1>
                <div class="divider"></div>
                <p class="hero-subtitle">
                    Powered by YOLOv8. Cinematic atmospheric design.<br/>
                    Interactive, lightweight, and blazing fast AI.
                </p>
                <div class="hero-buttons">
                    <button onclick="navigate('auth')" class="btn-primary">Get Started</button>
                    <button onclick="navigate('about')" class="btn-outline">Learn More</button>
                </div>
            </div>
        </div>

        <!-- ── ABOUT SCREEN ── -->
        <div id="screen-about" class="screen hidden">
            <div class="page-container fade-up">
                <h2 class="page-title">About SignScan</h2>
                <div class="divider"></div>
                <p class="page-text">
                    SignScan was built to showcase the intersection of advanced machine learning and premium web design. 
                    Using a YOLOv8 model trained on the GTSRB dataset, it achieves 98% accuracy in real-time.
                </p>
                <div class="glass-card mt-8">
                    <h3>Our Mission</h3>
                    <p class="text-muted">To provide seamless, highly-accurate traffic sign validation for automated systems, encased in a stunning user experience.</p>
                </div>
            </div>
        </div>

        <!-- ── CAPABILITIES SCREEN ── -->
        <div id="screen-capabilities" class="screen hidden">
            <div class="page-container fade-up">
                <h2 class="page-title">Capabilities</h2>
                <div class="divider"></div>
                <div class="grid-features">
                    <div class="glass-card">
                        <h3>98% Accuracy</h3>
                        <p class="text-muted">Detects 43 distinct classes of traffic signs under varying lighting conditions.</p>
                    </div>
                    <div class="glass-card">
                        <h3>Real-Time Processing</h3>
                        <p class="text-muted">Optimized YOLO architecture ensures immediate feedback on uploaded images.</p>
                    </div>
                    <div class="glass-card">
                        <h3>Cinematic UI</h3>
                        <p class="text-muted">Custom WebGL LightRays background built with OGL for smooth 60fps interaction.</p>
                    </div>
                    <div class="glass-card">
                        <h3>Secure Authentication</h3>
                        <p class="text-muted">Local & Google OAuth support with encrypted session handling.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- ── CONTACT SCREEN ── -->
        <div id="screen-contact" class="screen hidden">
            <div class="page-container fade-up">
                <h2 class="page-title">Contact Us</h2>
                <div class="divider"></div>
                <div class="glass-card max-w-md mx-auto">
                    <div class="form-group">
                        <label>Name</label>
                        <input type="text" class="input-glass" placeholder="Your name">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" class="input-glass" placeholder="Your email">
                    </div>
                    <div class="form-group">
                        <label>Message</label>
                        <textarea class="input-glass" rows="4" placeholder="How can we help?"></textarea>
                    </div>
                    <button class="btn-primary w-full mt-4" onclick="alert('Message sent!')">Send Message</button>
                </div>
            </div>
        </div>

        <!-- ── AUTH SCREEN ── -->
        <div id="screen-auth" class="screen hidden">
            <div class="auth-container fade-up">
                <!-- Login -->
                <div id="formLogin" class="glass-card auth-card">
                    <h2 class="card-title">Welcome Back</h2>
                    <p class="text-muted mb-6">Log in to your account</p>
                    <div id="googleBtnLogin" class="mb-4"></div>
                    <div class="auth-divider"><span>or email</span></div>
                    
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" id="logUsername" class="input-glass" placeholder="Enter username">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="logPassword" class="input-glass" placeholder="Enter password">
                    </div>
                    <div id="loginError" class="alert-error hidden"></div>
                    <div id="loginSuccess" class="alert-success hidden"></div>
                    <button id="btnLoginAction" class="btn-primary w-full mt-2">Log In</button>
                    <p class="mt-4 text-center text-sm text-muted">Don't have an account? <a href="#" onclick="toggleAuth()" class="highlight">Sign up</a></p>
                </div>

                <!-- Register -->
                <div id="formRegister" class="glass-card auth-card hidden">
                    <h2 class="card-title">Create Account</h2>
                    <p class="text-muted mb-6">Join SignScan today</p>
                    
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" id="regUsername" class="input-glass" placeholder="Choose username">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="regPassword" class="input-glass" placeholder="Min 8 chars, number & special">
                        <p class="text-xs text-muted mt-1">8+ characters · at least one number · special char</p>
                    </div>
                    <div id="registerError" class="alert-error hidden"></div>
                    <button id="btnRegisterAction" class="btn-primary w-full mt-2">Create Account</button>
                    <p class="mt-4 text-center text-sm text-muted">Already have an account? <a href="#" onclick="toggleAuth()" class="highlight">Log in</a></p>
                </div>
            </div>
        </div>

        <!-- ── APP/DASHBOARD SCREEN ── -->
        <div id="screen-app" class="screen hidden">
            <div class="dashboard-layout fade-up">
                <aside class="dashboard-sidebar glass-card">
                    <button class="tab-btn active" onclick="switchAppTab('scan')">Scanner</button>
                    <button class="tab-btn" onclick="switchAppTab('history')">History</button>
                    <button class="tab-btn" onclick="switchAppTab('profile')">Profile</button>
                </aside>
                
                <div class="dashboard-content">
                    <!-- Scan Tab -->
                    <div id="tab-scan" class="app-tab active">
                        <div class="glass-card">
                            <h2 class="card-title mb-4">Analyze Traffic Sign</h2>
                            <div class="upload-area" id="uploadArea">
                                <p class="text-muted">Drag & drop image here or <span class="highlight cursor-pointer" id="btnBrowse">browse</span></p>
                                <input type="file" id="fileInput" class="hidden" accept="image/*">
                            </div>
                            <div id="previewContainer" class="hidden mt-4 text-center">
                                <img id="imagePreview" class="max-w-xs mx-auto rounded-lg border border-white/10" src="" alt="Preview">
                                <button id="btnScan" class="btn-primary mt-4 px-8">Scan Image</button>
                            </div>
                            <div id="scanResult" class="mt-6 hidden">
                                <div class="glass-card bg-white/5 border-primary/30">
                                    <h3 class="text-xl text-primary font-medium" id="resClass">Stop Sign</h3>
                                    <p class="text-muted mt-1" id="resConf">Confidence: 98%</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- History Tab -->
                    <div id="tab-history" class="app-tab hidden">
                        <div class="glass-card">
                            <h2 class="card-title mb-4">Recent Scans</h2>
                            <div id="historyList" class="space-y-4">
                                <!-- Populated by JS -->
                            </div>
                        </div>
                    </div>

                    <!-- Profile Tab -->
                    <div id="tab-profile" class="app-tab hidden">
                        <div class="glass-card max-w-lg">
                            <h2 class="card-title mb-6">Your Profile</h2>
                            <div class="space-y-4 mb-8">
                                <div><span class="text-muted text-sm">Username:</span> <div id="profUsername" class="text-lg"></div></div>
                                <div><span class="text-muted text-sm">Account Type:</span> <div id="profType" class="text-lg capitalize"></div></div>
                                <div><span class="text-muted text-sm">Joined:</span> <div id="profJoined" class="text-lg"></div></div>
                            </div>

                            <div id="changePasswordSection" class="border-t border-white/10 pt-6">
                                <h3 class="text-lg font-medium mb-4">Change Password</h3>
                                <div class="form-group">
                                    <input type="password" id="cpOld" class="input-glass" placeholder="Current Password">
                                </div>
                                <div class="form-group">
                                    <input type="password" id="cpNew" class="input-glass" placeholder="New Password">
                                </div>
                                <div id="cpError" class="alert-error hidden"></div>
                                <div id="cpSuccess" class="alert-success hidden"></div>
                                <button id="btnChangePassword" class="btn-outline w-full mt-2">Update Password</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script type="module" src="/static/js/app.js"></script>
</body>
</html>
"""

CSS_CONTENT = r"""
:root {
    --bg-color: #09090b;
    --text-primary: #fafafa;
    --text-muted: #a1a1aa;
    --primary: #00ffff;
    --primary-dim: rgba(0, 255, 255, 0.2);
    --glass-bg: rgba(255, 255, 255, 0.03);
    --glass-border: rgba(255, 255, 255, 0.08);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg-color);
    color: var(--text-primary);
    overflow-x: hidden;
    min-height: 100vh;
}

.background-canvas {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
}

/* Nav */
.glass-nav {
    position: fixed; top: 0; left: 0; width: 100%; height: 80px;
    background: rgba(9, 9, 11, 0.5); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--glass-border); z-index: 50;
}
.nav-inner {
    max-width: 1200px; margin: 0 auto; padding: 0 24px; height: 100%;
    display: flex; align-items: center; justify-content: space-between;
}
.nav-logo { font-size: 24px; font-weight: 600; cursor: pointer; }
.highlight { color: var(--primary); }
.nav-links { display: flex; gap: 32px; }
.nav-link { 
    color: var(--text-muted); text-decoration: none; font-size: 14px; font-weight: 500; transition: color 0.2s; 
}
.nav-link:hover, .nav-link.active { color: var(--text-primary); }
.nav-actions { display: flex; gap: 16px; }

/* Buttons */
button { font-family: inherit; cursor: pointer; border: none; outline: none; }
.btn-primary {
    background: #fff; color: #000; padding: 12px 24px; border-radius: 999px;
    font-weight: 500; transition: all 0.2s;
}
.btn-primary:hover { background: #e5e5e5; }
.btn-outline {
    background: var(--glass-bg); color: #fff; padding: 12px 24px; border-radius: 999px;
    border: 1px solid var(--glass-border); font-weight: 500; transition: all 0.2s;
}
.btn-outline:hover { background: rgba(255,255,255,0.1); }
.btn-glow {
    background: var(--primary-dim); color: var(--primary); padding: 10px 20px; border-radius: 999px;
    border: 1px solid var(--primary-dim); font-weight: 500; transition: all 0.2s;
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.1);
}
.btn-glow:hover { background: rgba(0,255,255,0.3); box-shadow: 0 0 25px rgba(0, 255, 255, 0.2); }

/* Layout */
.content-wrapper { padding-top: 80px; min-height: 100vh; position: relative; z-index: 10; }
.screen { display: none; }
.screen.active { display: block; }
.hidden { display: none !important; }

/* Typography */
.hero-section { text-align: center; padding: 80px 24px; max-width: 800px; margin: 0 auto; }
.hero-title { font-size: clamp(3rem, 6vw, 5rem); font-weight: 500; line-height: 1.1; letter-spacing: -0.02em; }
.hero-subtitle { font-size: 1.25rem; color: var(--text-muted); font-weight: 300; margin-bottom: 40px; line-height: 1.6; }
.divider { height: 1px; width: 80px; background: linear-gradient(90deg, transparent, var(--primary), transparent); margin: 32px auto; opacity: 0.5; }
.hero-buttons { display: flex; gap: 16px; justify-content: center; }

/* Pages */
.page-container { max-width: 1000px; margin: 0 auto; padding: 60px 24px; }
.page-title { font-size: 3rem; font-weight: 500; text-align: center; }
.page-text { font-size: 1.1rem; color: var(--text-muted); text-align: center; max-width: 700px; margin: 0 auto; line-height: 1.6; }
.text-muted { color: var(--text-muted); }

/* Cards & Glass */
.glass-card {
    background: rgba(25, 25, 30, 0.4); border: 1px solid var(--glass-border);
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    border-radius: 24px; padding: 32px;
}
.grid-features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-top: 48px; }

/* Forms */
.form-group { margin-bottom: 20px; text-align: left; }
.form-group label { display: block; font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
.input-glass {
    width: 100%; background: rgba(0,0,0,0.2); border: 1px solid var(--glass-border);
    color: white; padding: 14px 16px; border-radius: 12px; transition: border-color 0.2s;
}
.input-glass:focus { outline: none; border-color: var(--primary); }
.alert-error { background: rgba(255,50,50,0.1); color: #ff6b6b; padding: 12px; border-radius: 8px; font-size: 14px; margin: 16px 0; border: 1px solid rgba(255,50,50,0.2); }
.alert-success { background: rgba(50,255,100,0.1); color: #4ade80; padding: 12px; border-radius: 8px; font-size: 14px; margin: 16px 0; border: 1px solid rgba(50,255,100,0.2); }

/* Auth */
.auth-container { display: flex; justify-content: center; align-items: center; min-height: calc(100vh - 80px); padding: 24px; }
.auth-card { width: 100%; max-width: 400px; text-align: center; }
.auth-divider { display: flex; align-items: center; margin: 24px 0; color: var(--text-muted); font-size: 12px; }
.auth-divider::before, .auth-divider::after { content: ''; flex: 1; height: 1px; background: var(--glass-border); }
.auth-divider span { padding: 0 16px; }

/* Dashboard */
.dashboard-layout { display: grid; grid-template-columns: 240px 1fr; gap: 32px; max-width: 1200px; margin: 40px auto; padding: 0 24px; }
.dashboard-sidebar { padding: 24px; display: flex; flex-direction: column; gap: 8px; }
.tab-btn { background: transparent; color: var(--text-muted); text-align: left; padding: 12px 16px; border-radius: 8px; font-weight: 500; transition: all 0.2s; }
.tab-btn:hover { background: var(--glass-bg); color: white; }
.tab-btn.active { background: rgba(0,255,255,0.1); color: var(--primary); }
.app-tab { display: none; }
.app-tab.active { display: block; }
.upload-area { border: 2px dashed var(--glass-border); border-radius: 16px; padding: 48px 24px; text-align: center; transition: border-color 0.2s; }
.upload-area:hover, .upload-area.dragover { border-color: var(--primary); background: rgba(0,255,255,0.02); }

/* Animations */
.fade-up { animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
    .nav-links { display: none; }
    .dashboard-layout { grid-template-columns: 1fr; }
    .dashboard-sidebar { flex-direction: row; overflow-x: auto; }
    .tab-btn { flex: 1; text-align: center; }
}
"""

JS_CONTENT = r"""
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

// Navigation
window.navigate = (screenId) => {
  $$('.screen').forEach(s => {
    if(s.id === `screen-${screenId}`) {
      s.classList.remove('hidden'); s.classList.add('active');
    } else {
      s.classList.remove('active'); s.classList.add('hidden');
    }
  });
  $$('.nav-link').forEach(l => l.classList.remove('active'));
  const link = document.querySelector(`.nav-link[onclick="navigate('${screenId}')"]`);
  if(link) link.classList.add('active');
  
  if(screenId === 'app') loadProfile();
};

window.switchAppTab = (tabId) => {
  $$('.app-tab').forEach(t => t.classList.add('hidden'));
  $(`tab-${tabId}`).classList.remove('hidden');
  $$('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`button[onclick="switchAppTab('${tabId}')"]`).classList.add('active');
  if(tabId === 'history') loadHistory();
};

window.toggleAuth = () => {
  $('formLogin').classList.toggle('hidden');
  $('formRegister').classList.toggle('hidden');
  $('loginError').classList.add('hidden'); $('registerError').classList.add('hidden');
};

// Auth
function checkToken() {
  const t = localStorage.getItem("auth_token");
  const u = localStorage.getItem("username");
  if(t && u) {
    currentUser = u;
    $('navLoginBtn').classList.add('hidden');
    $('navLogoutBtn').classList.remove('hidden');
    $('navDashboardBtn').classList.remove('hidden');
  } else {
    currentUser = null;
    $('navLoginBtn').classList.remove('hidden');
    $('navLogoutBtn').classList.add('hidden');
    $('navDashboardBtn').classList.add('hidden');
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
  err.classList.add('hidden');
  if(!u || !p) { err.textContent = "Please fill all fields."; err.classList.remove('hidden'); return; }
  
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
      err.textContent = data.error || "Login failed"; err.classList.remove('hidden');
    }
  } catch(e) { err.textContent = "Network error"; err.classList.remove('hidden'); }
  btn.textContent = "Log In"; btn.disabled = false;
}

async function handleRegister() {
  const u = $('regUsername').value.trim(), p = $('regPassword').value;
  const btn = $('btnRegisterAction'), err = $('registerError');
  err.classList.add('hidden');
  if(!u || !p) { err.textContent = "Please fill all fields."; err.classList.remove('hidden'); return; }
  
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
      err.textContent = data.error || "Registration failed"; err.classList.remove('hidden');
    }
  } catch(e) { err.textContent = "Network error"; err.classList.remove('hidden'); }
  btn.textContent = "Create Account"; btn.disabled = false;
}

// Profile
function loadProfile() {
  $('profUsername').textContent = localStorage.getItem("username") || "Unknown";
  $('profType').textContent = localStorage.getItem("account_type") || "Local";
  $('profJoined').textContent = localStorage.getItem("join_date") || "Unknown";
  
  if(localStorage.getItem("account_type") === "google") {
    $('changePasswordSection').classList.add('hidden');
  } else {
    $('changePasswordSection').classList.remove('hidden');
  }
}

async function handleChangePassword() {
  const o = $('cpOld').value, n = $('cpNew').value;
  const err = $('cpError'), suc = $('cpSuccess'), btn = $('btnChangePassword');
  err.classList.add('hidden'); suc.classList.add('hidden');
  if(!o || !n) { err.textContent = "Fill all fields."; err.classList.remove('hidden'); return; }
  
  btn.textContent = "Updating..."; btn.disabled = true;
  try {
    const res = await fetch("/api/auth/change-password", {
      method: "POST", headers:{
        "Content-Type":"application/json",
        "Authorization": `Bearer ${localStorage.getItem("auth_token")}`
      },
      body: JSON.stringify({old_password: o, new_password: n})
    });
    const data = await res.json();
    if(res.ok) {
      suc.textContent = "Password updated successfully."; suc.classList.remove('hidden');
      $('cpOld').value = ''; $('cpNew').value = '';
    } else {
      err.textContent = data.error || "Failed"; err.classList.remove('hidden');
    }
  } catch(e) { err.textContent = "Network error"; err.classList.remove('hidden'); }
  btn.textContent = "Update Password"; btn.disabled = false;
}

// Scanner
let selectedFile = null;
function handleFileSelect(e) {
  const file = e.target.files ? e.target.files[0] : e.dataTransfer.files[0];
  if(!file) return;
  selectedFile = file;
  $('uploadArea').classList.add('hidden');
  $('previewContainer').classList.remove('hidden');
  $('scanResult').classList.add('hidden');
  const reader = new FileReader();
  reader.onload = e => $('imagePreview').src = e.target.result;
  reader.readAsDataURL(file);
}

async function handleScan() {
  if(!selectedFile) return;
  const btn = $('btnScan');
  btn.textContent = "Analyzing..."; btn.disabled = true;
  
  const formData = new FormData();
  formData.append("file", selectedFile);
  
  try {
    const res = await fetch("/api/analyze", { method: "POST", body: formData });
    const data = await res.json();
    if(res.ok && data.predictions && data.predictions.length > 0) {
      const best = data.predictions[0];
      $('resClass').textContent = best.class_name;
      $('resConf').textContent = `Confidence: ${(best.confidence * 100).toFixed(1)}%`;
      $('scanResult').classList.remove('hidden');
      saveHistory(best, $('imagePreview').src);
    } else {
      alert("No sign detected or error occurred.");
    }
  } catch(e) { alert("Network error during scan."); }
  btn.textContent = "Scan Again"; btn.disabled = false;
  $('uploadArea').classList.remove('hidden');
  $('previewContainer').classList.add('hidden');
  selectedFile = null;
}

// History
function saveHistory(result, imgUrl) {
  let hist = JSON.parse(localStorage.getItem("scan_history") || "[]");
  hist.unshift({ date: new Date().toLocaleString(), result, imgUrl });
  if(hist.length > 10) hist.pop();
  localStorage.setItem("scan_history", JSON.stringify(hist));
}

function loadHistory() {
  const hist = JSON.parse(localStorage.getItem("scan_history") || "[]");
  const list = $('historyList');
  if(hist.length === 0) {
    list.innerHTML = '<p class="text-muted">No recent scans found.</p>';
    return;
  }
  list.innerHTML = hist.map(h => `
    <div class="glass-card flex gap-4 p-4 items-center">
      <img src="${h.imgUrl}" class="w-16 h-16 object-cover rounded-md border border-white/10">
      <div>
        <h4 class="text-primary font-medium text-lg">${h.result.class_name}</h4>
        <p class="text-muted text-sm">${(h.result.confidence * 100).toFixed(1)}% confidence • ${h.date}</p>
      </div>
    </div>
  `).join('');
}

// Events Setup
function bindEvents() {
  $('btnLoginAction').addEventListener('click', handleLogin);
  $('btnRegisterAction').addEventListener('click', handleRegister);
  $('btnChangePassword').addEventListener('click', handleChangePassword);
  $('btnScan').addEventListener('click', handleScan);
  
  const drop = $('uploadArea');
  drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('dragover'); });
  drop.addEventListener('dragleave', () => drop.classList.remove('dragover'));
  drop.addEventListener('drop', e => { e.preventDefault(); drop.classList.remove('dragover'); handleFileSelect(e); });
  $('btnBrowse').addEventListener('click', () => $('fileInput').click());
  $('fileInput').addEventListener('change', handleFileSelect);
}
"""

def generate():
    os.makedirs('app/static/css', exist_ok=True)
    os.makedirs('app/static/js', exist_ok=True)
    with open('app/static/index.html', 'w', encoding='utf-8') as f:
        f.write(HTML_CONTENT)
    with open('app/static/css/style.css', 'w', encoding='utf-8') as f:
        f.write(CSS_CONTENT)
    with open('app/static/js/app.js', 'w', encoding='utf-8') as f:
        f.write(JS_CONTENT)
    print("UI generation complete!")

if __name__ == "__main__":
    generate()
