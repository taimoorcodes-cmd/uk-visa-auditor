"""Dark / orange 3D style. __VIDEO__ is replaced by the video link in app.py."""
CSS_TEMPLATE = r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');
:root{--orange:#ff4d00;--orange-dark:#b33500;--line:#262626;--muted:#a3a3a3;}
html, body{background:#0a0a0a;}
.stApp{background:transparent !important; font-family:'Inter',sans-serif;}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"]{display:none;}
header[data-testid="stHeader"]{display:none;}
.block-container{padding-top:1.2rem; max-width:1300px;}

/* Background video + dark overlay + orange glow (like the reference site) */
#bg-video{position:fixed; top:0; left:0; width:100vw; height:100vh; object-fit:cover; z-index:-3; opacity:.45;}
.video-overlay{position:fixed; inset:0; z-index:-2; background:linear-gradient(180deg, rgba(10,10,10,.90), rgba(10,10,10,.96));}
.glow{position:fixed; left:0; right:0; bottom:0; height:50vh; z-index:-1; pointer-events:none;
  background:radial-gradient(ellipse at 50% 100%, rgba(255,77,0,.30), transparent 70%);}

/* Top bar */
.topbar{display:flex; justify-content:space-between; align-items:center; padding:.8rem 1.2rem; margin-bottom:1.2rem;
  background:rgba(17,17,17,.85); border:1px solid var(--line); border-radius:14px; backdrop-filter:blur(10px);}
.logo{font-family:'Space Mono',monospace; font-weight:700; letter-spacing:.12em; font-size:1.05rem; color:#fff;}
.chip{display:inline-block; margin-left:8px; padding:6px 14px; border:1px solid var(--line); border-radius:10px;
  background:#151515; font-size:.78rem; font-weight:600; letter-spacing:.04em; color:#e5e5e5;}
.chip.hot{background:var(--orange); border-color:var(--orange); color:#fff;}

/* Hero */
.hero-title{text-align:center; font-weight:800; font-size:clamp(2.1rem,5vw,3.8rem); line-height:1.1; letter-spacing:-.02em; margin:.2rem 0 1rem;
  text-shadow:0 1px 0 #3a3a3a, 0 2px 0 #2e2e2e, 0 3px 0 #232323, 0 18px 30px rgba(0,0,0,.85);}
.hero-title .hl{color:var(--orange);}
.hero-sub{text-align:center; color:var(--muted); font-size:1.05rem; margin-bottom:1.6rem;}
.sec{font-weight:800; letter-spacing:.05em; text-transform:uppercase; font-size:1rem;
  border-left:3px solid var(--orange); padding-left:10px; margin:1.2rem 0 .8rem;}
.disclaimer{font-size:.8rem; color:#8a8a8a;}

/* Cards = the Streamlit containers themselves (uploader sits truly inside) */
[class*="st-key-card_"], .st-key-chat_panel, .st-key-result_panel, .st-key-login_card, .st-key-details_panel{
  background:linear-gradient(145deg,#151515,#0d0d0d); border:1px solid var(--line); border-radius:18px; padding:1rem 1.2rem;
  box-shadow:0 1px 0 rgba(255,255,255,.05) inset, 0 24px 40px -22px rgba(0,0,0,.95);
  transition:transform .35s cubic-bezier(.2,.8,.2,1), border-color .3s, box-shadow .3s;
  transform-style:preserve-3d;}
/* 3D tilt on hover */
[class*="st-key-card_"]:hover{
  transform:perspective(900px) rotateX(4deg) rotateY(-5deg) translateY(-8px) scale(1.02);
  border-color:var(--orange);
  box-shadow:0 1px 0 rgba(255,255,255,.06) inset, 16px 30px 50px -22px rgba(0,0,0,.95), 0 0 28px rgba(255,77,0,.25);}
.card-icon{width:56px; height:56px; margin:0 auto .5rem; display:flex; align-items:center; justify-content:center; font-size:1.8rem;
  background:#1a1a1a; border:1px solid #2c2c2c; border-radius:14px;
  box-shadow:0 1px 0 rgba(255,255,255,.07) inset, 0 10px 18px -6px rgba(0,0,0,.9);}
.card-title{font-size:1.02rem; font-weight:700; text-align:center; margin-bottom:.5rem; color:#fff;}
.badge{display:inline-block; margin-left:6px; padding:1px 7px; font-size:.62rem; font-weight:700; letter-spacing:.06em;
  color:#ffb08a; border:1px solid #5a2a14; border-radius:6px; vertical-align:middle;}

/* Uploader */
[data-testid="stFileUploaderDropzone"]{background:#0d0d0d; border:1px dashed #3a3a3a; border-radius:12px; transition:.25s;}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--orange);}
[data-testid="stFileUploaderDropzoneInstructions"]{display:none;}

/* 3D push buttons */
[data-testid="stBaseButton-primary"]{background:var(--orange) !important; border:none !important; color:#fff !important;
  font-weight:700 !important; border-radius:12px !important; margin-bottom:6px;
  box-shadow:0 6px 0 var(--orange-dark), 0 16px 26px rgba(255,77,0,.30); transition:transform .15s, box-shadow .15s;}
[data-testid="stBaseButton-primary"]:hover{transform:translateY(-2px); box-shadow:0 8px 0 var(--orange-dark), 0 20px 30px rgba(255,77,0,.40);}
[data-testid="stBaseButton-primary"]:active{transform:translateY(5px); box-shadow:0 1px 0 var(--orange-dark), 0 6px 12px rgba(255,77,0,.30);}
[data-testid="stBaseButton-secondary"]{background:#151515 !important; border:1px solid var(--line) !important; border-radius:12px !important; color:#e5e5e5 !important;}
[data-testid="stBaseButton-secondary"]:hover{border-color:var(--orange) !important; color:#fff !important;}

/* Inputs */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div{background:#141414 !important; border-color:var(--line) !important; border-radius:12px !important;}

/* 3D rotating cube */
.cube-wrap{perspective:700px; margin:0 auto;}
.cube-lg{--s:84px; width:var(--s); height:var(--s); margin:26px auto 34px;}
.cube-sm{--s:42px; width:var(--s); height:var(--s); margin:6px 22px 6px 12px; flex:none;}
.cube{position:relative; width:100%; height:100%; transform-style:preserve-3d; animation:spin 14s linear infinite;}
.face{position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:calc(var(--s) * .5);
  background:rgba(255,77,0,.10); border:1px solid rgba(255,77,0,.65); box-shadow:0 0 18px rgba(255,77,0,.18) inset;}
.f1{transform:rotateY(0deg) translateZ(calc(var(--s) / 2));}
.f2{transform:rotateY(90deg) translateZ(calc(var(--s) / 2));}
.f3{transform:rotateY(180deg) translateZ(calc(var(--s) / 2));}
.f4{transform:rotateY(-90deg) translateZ(calc(var(--s) / 2));}
.f5{transform:rotateX(90deg) translateZ(calc(var(--s) / 2));}
.f6{transform:rotateX(-90deg) translateZ(calc(var(--s) / 2));}
@keyframes spin{from{transform:rotateX(-22deg) rotateY(0deg);} to{transform:rotateX(-22deg) rotateY(360deg);}}

/* 3D score ring */
.ring{width:170px; height:170px; border-radius:50%; margin:10px auto; padding:14px; box-sizing:border-box;
  transform:perspective(600px) rotateX(14deg); animation:floaty 4s ease-in-out infinite;}
.ring-in{width:100%; height:100%; border-radius:50%; background:#0d0d0d; display:flex; align-items:center; justify-content:center;
  font-size:2.9rem; font-weight:800; color:#fff; box-shadow:inset 0 10px 22px rgba(0,0,0,.95), 0 0 0 1px #262626;}
.ring-label{text-align:center; font-weight:700; letter-spacing:.05em; text-transform:uppercase; font-size:.8rem; color:var(--muted);}
@keyframes floaty{0%,100%{transform:perspective(600px) rotateX(14deg) translateY(0);} 50%{transform:perspective(600px) rotateX(14deg) translateY(-8px);}}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{gap:6px; border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{background:#141414; border:1px solid var(--line); border-radius:10px 10px 0 0; padding:8px 14px; color:#d4d4d4;}
.stTabs [aria-selected="true"]{background:var(--orange) !important; color:#fff !important; border-color:var(--orange);}
.stTabs [data-baseweb="tab-highlight"]{display:none;}
.chip.pro{background:#16a34a; border-color:#16a34a; color:#fff;}
.st-key-pay_panel, .st-key-iv_panel, .st-key-shot_panel, .st-key-hist_panel, .st-key-admin_panel{
  background:linear-gradient(145deg,#151515,#0d0d0d); border:1px solid var(--line); border-radius:18px; padding:1rem 1.2rem;}
.status-line{padding:6px 0; border-bottom:1px solid #1f1f1f; font-size:.92rem;}
.tip-box{background:#141414; border-left:3px solid var(--orange); padding:8px 12px; border-radius:8px; font-size:.9rem; color:#d4d4d4;}
</style>
<video autoplay loop muted playsinline id="bg-video"><source src="__VIDEO__" type="video/mp4"></video>
<div class="video-overlay"></div>
<div class="glow"></div>
'''