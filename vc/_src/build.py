#!/usr/bin/env python3
"""Build one targeted landing page per VC.

Usage:  python3 vc/_src/build.py            (from the repo root)
Reads   vc/_src/data/_profile.json and vc/_src/data/<slug>.json
Writes  vc/<slug>/index.html  (self-contained: inline CSS, SVG charts, small JS)
        vc/index.html         (private hub: overview table + one tab per VC)

Scoring
- Each company gets six 0-5 scores, in this order:
  Domain fit, Business model, AI & data, Stage & momentum, RevOps leverage, Portugal presence.
  Overall = sum / 30 * 100. Tiers: strong 70+ (green), medium 50-69 (orange), low < 50 (yellow).
- VC level (0-5): Thesis overlap, Stage fit and Platform support are set by hand in the JSON;
  Top matches (mean of the three best company scores) and Portugal footprint
  (share of active companies scoring >= 4 on Portugal presence, 60%+ = 5) are computed.
  Overall = mean * 20.
"""
import json
import math
import pathlib
from datetime import date
from html import escape as e

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "vc" / "_src" / "data"
OUT = ROOT / "vc"

DIMS = [
    ("Domain fit", "Domain", "Overlap with what I've shipped: fintech, KYC and fraud, martech and ad tech, edtech, geolocation, crypto and identity."),
    ("Business model", "Model", "B2B or B2C software, SaaS or platform, versus hardware, biotech or physical goods."),
    ("AI & data", "AI & data", "Machine learning or LLMs at the core of the product, where my OCR, fraud, RL and LLM-evaluation work applies."),
    ("Stage & momentum", "Stage", "Seed to Series C, plus a recent round or visible hiring (checked for the top matches)."),
    ("RevOps leverage", "RevOps", "A sales- or CS-led motion with CRM complexity, where pipeline, SLA, health-score and dashboard work pays off."),
    ("Portugal presence", "Portugal", "HQ or team in Portugal, so I can work on-site or hybrid from Lisbon."),
]
VC_DIMS = [
    ("thesis", "Thesis overlap"),
    ("stage", "Stage fit"),
    ("top", "Top matches"),
    ("pt", "Portugal footprint"),
    ("platform", "Platform support"),
]
TIERS = [  # (min score, key, label)
    (70, "strong", "Strong"),
    (50, "medium", "Medium"),
    (0, "low", "Low"),
]
RANGES = {"strong": "70+", "medium": "50–69", "low": "under 50"}


def tier(score):
    for floor, key, label in TIERS:
        if score >= floor:
            return key, label
    return "low", "Low"


def company_score(c):
    return round(sum(c["s"]) / 30 * 100)


def vc_scores(vc):
    active = vc["companies"]
    ranked = sorted((company_score(c) for c in active), reverse=True)
    top = sum(ranked[:3]) / min(3, len(ranked)) / 20
    pt_share = sum(1 for c in active if c["s"][5] >= 4) / len(active)
    pt = min(5.0, 5 * pt_share / 0.6)
    vals = {
        "thesis": vc["vc_manual"]["thesis"],
        "stage": vc["vc_manual"]["stage"],
        "top": round(top, 1),
        "pt": round(pt, 1),
        "platform": vc["vc_manual"]["platform"],
    }
    overall = round(sum(vals.values()) / len(vals) * 20)
    notes = dict(vc.get("vc_notes", {}))
    notes["top"] = f"Mean of the three best company scores ({', '.join(str(x) for x in ranked[:3])})."
    notes["pt"] = f"{round(pt_share * 100)}% of active companies have an HQ or team in Portugal."
    return vals, overall, notes


def fmt(v):
    return str(int(v)) if float(v).is_integer() else f"{v:.1f}"


def radar(values, labels, *, size, r, label_gap, full_labels=None, cls="", avg=None, rid=""):
    """Inline SVG radar. values 0-5. Colour comes from the CSS custom property --line/--c."""
    w, h = size
    cx, cy = w / 2, h / 2
    n = len(values)
    angles = [(-90 + i * 360 / n) * math.pi / 180 for i in range(n)]
    names = full_labels or labels

    def pts(vals):
        return " ".join(f"{cx + r * v / 5 * math.cos(a):.1f},{cy + r * v / 5 * math.sin(a):.1f}" for v, a in zip(vals, angles))

    idattr = f' id="{rid}" data-cx="{cx}" data-cy="{cy}" data-r="{r}"' if rid else ""
    out = [f'<svg class="radar {cls}"{idattr} viewBox="0 0 {w} {h}" role="img" aria-label="'
           + e("; ".join(f"{names[i]} {fmt(values[i])} of 5" for i in range(n))) + '">']
    for ring in range(1, 6):
        ring_pts = " ".join(f"{cx + r * ring / 5 * math.cos(a):.1f},{cy + r * ring / 5 * math.sin(a):.1f}" for a in angles)
        out.append(f'<polygon class="radar__ring{" radar__ring--outer" if ring == 5 else ""}" points="{ring_pts}"/>')
    for a in angles:
        out.append(f'<line class="radar__spoke" x1="{cx}" y1="{cy}" x2="{cx + r * math.cos(a):.1f}" y2="{cy + r * math.sin(a):.1f}"/>')
    if avg:
        out.append(f'<polygon class="radar__avg" points="{pts(avg)}"/>')
    out.append(f'<polygon class="radar__area" points="{pts(values)}"/>')
    for i, (v, a) in enumerate(zip(values, angles)):
        x, y = cx + r * v / 5 * math.cos(a), cy + r * v / 5 * math.sin(a)
        out.append(f'<g class="radar__pt"><circle class="radar__hit" cx="{x:.1f}" cy="{y:.1f}" r="11"/>'
                   f'<circle class="radar__dot" cx="{x:.1f}" cy="{y:.1f}" r="4"/>'
                   f'<title>{e(names[i])}: {fmt(v)} / 5</title></g>')
    for i, a in enumerate(angles):
        lx, ly = cx + (r + label_gap) * math.cos(a), cy + (r + label_gap) * math.sin(a)
        c = math.cos(a)
        anchor = "middle" if abs(c) < 0.2 else ("start" if c > 0 else "end")
        dy = "0.35em"
        if math.sin(a) < -0.9:
            dy = "0"
        elif math.sin(a) > 0.9:
            dy = "0.8em"
        out.append(f'<text class="radar__label" x="{lx:.1f}" y="{ly:.1f}" dy="{dy}" text-anchor="{anchor}">'
                   f'{e(labels[i])} <tspan class="radar__val">{fmt(values[i])}</tspan></text>')
    out.append("</svg>")
    return "".join(out)


CSS = r"""
:root{--paper:#fcfbf8;--surface:#fff;--ink:#121a17;--muted:#5d625e;--line:#e2e0d9;--accent:#3a3df0;--accent-ink:#fff;--hl:#ffd84d;
--shadow:0 1px 2px rgb(18 26 23/.06),0 12px 32px -12px rgb(18 26 23/.18);
--t-strong:#0ca30c;--t-medium:#ec835a;--t-low:#fab219;
--t-strong-line:#0a7f0a;--t-medium-line:#c4552a;--t-low-line:#a87300;
--dot-ring:rgb(18 26 23/.28);
--f-display:"Bricolage Grotesque","Avenir Next","Segoe UI",sans-serif;--f-body:"Hanken Grotesk","Helvetica Neue",Arial,sans-serif;--f-mono:"JetBrains Mono",ui-monospace,Menlo,monospace;
--s-xs:.8125rem;--s-sm:.9375rem;--s-md:1.0625rem;--s-lg:1.375rem;--s-xl:clamp(1.75rem,1.2rem + 2vw,2.75rem);--col:1180px;--radius:14px;--ease:cubic-bezier(.2,.7,.1,1)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0f1413;--surface:#171e1c;--ink:#e7eeea;--muted:#94a29c;--line:#2a3431;--accent:#8f92ff;--accent-ink:#0f1413;--hl:rgb(230 194 58/.38);--shadow:0 1px 2px rgb(0 0 0/.3),0 16px 40px -16px rgb(0 0 0/.6);
--t-strong-line:#2fc52f;--t-medium-line:#ec835a;--t-low-line:#fab219;--dot-ring:rgb(255 255 255/.18);color-scheme:dark}}
:root[data-theme="dark"]{--paper:#0f1413;--surface:#171e1c;--ink:#e7eeea;--muted:#94a29c;--line:#2a3431;--accent:#8f92ff;--accent-ink:#0f1413;--hl:rgb(230 194 58/.38);--shadow:0 1px 2px rgb(0 0 0/.3),0 16px 40px -16px rgb(0 0 0/.6);
--t-strong-line:#2fc52f;--t-medium-line:#ec835a;--t-low-line:#fab219;--dot-ring:rgb(255 255 255/.18);color-scheme:dark}
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font:400 var(--s-md)/1.6 var(--f-body);-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit}
h1,h2,h3{font-family:var(--f-display);font-weight:600;line-height:1.05;margin:0;letter-spacing:-.02em;text-wrap:balance}
p{margin:0}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:6px}
.wrap{max-width:var(--col);margin-inline:auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
@media (min-width:720px){.wrap{padding-left:max(32px,env(safe-area-inset-left,0px));padding-right:max(32px,env(safe-area-inset-right,0px))}}
.eyebrow{font-family:var(--f-mono);font-size:var(--s-xs);text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}

body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:11;background:var(--paper)}
.top{position:sticky;top:env(safe-area-inset-top,0px);z-index:10;background:color-mix(in srgb,var(--paper) 86%,transparent);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.top__in{display:flex;align-items:center;gap:12px;min-height:60px}
.top__me{font:600 var(--s-md)/1 var(--f-display);text-decoration:none;margin-right:auto;white-space:nowrap}
.top__me span{color:var(--muted);font-weight:400}
.top a.link{font-size:var(--s-sm);color:var(--muted);text-decoration:none}
.top a.link:hover{color:var(--ink)}
.theme{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;border:0;background:transparent;color:var(--ink);cursor:pointer}
.theme:hover{background:var(--line)}
.theme svg{width:18px;height:18px}
@media (max-width:560px){.top a.link,.top__me span{display:none}}

.btn{display:inline-flex;align-items:center;gap:10px;padding:13px 20px;border-radius:999px;font:600 var(--s-sm)/1 var(--f-body);text-decoration:none;border:1px solid var(--ink);color:var(--ink);background:transparent;cursor:pointer;transition:transform .3s var(--ease),background .3s,color .3s;white-space:nowrap}
.btn:hover{transform:translateY(-2px)}
.btn--solid{background:var(--ink);color:var(--paper)}
.btn--solid:hover{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.btn--sm{padding:9px 14px}
.btn svg{width:16px;height:16px}
.ctas{display:flex;flex-wrap:wrap;gap:12px}

section{padding-block:clamp(56px,8vw,104px)}
section+section{border-top:1px solid var(--line)}
.head{display:grid;gap:12px;margin-bottom:clamp(28px,4vw,44px);max-width:760px}
.head h2{font-size:var(--s-xl)}
.head p:not(.eyebrow){color:var(--muted);font-size:var(--s-lg);line-height:1.4}

.dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--c);box-shadow:0 0 0 1px var(--dot-ring);flex:none}
.t-strong{--c:var(--t-strong);--cl:var(--t-strong-line)}
.t-medium{--c:var(--t-medium);--cl:var(--t-medium-line)}
.t-low{--c:var(--t-low);--cl:var(--t-low-line)}

.hero{padding-block:clamp(48px,7vw,96px)}
.hero__grid{display:grid;gap:clamp(32px,5vw,64px);align-items:center}
@media (min-width:920px){.hero__grid{grid-template-columns:1.25fr 1fr}}
.hero__text{display:grid;gap:22px;min-width:0}
.hero h1{font-size:clamp(2.3rem,1rem + 4vw,4rem);letter-spacing:-.035em;line-height:1}
.hero h1 .x{color:var(--accent)}
.hero__lede{font-size:var(--s-lg);line-height:1.45;color:var(--muted);max-width:56ch}

.vcscore{background:var(--surface);border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow);padding:clamp(18px,3vw,28px);display:grid;gap:14px}
.vcscore__top{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;flex-wrap:wrap}
.vcscore__num{font:600 clamp(3rem,2rem + 3vw,4.25rem)/.9 var(--f-display);letter-spacing:-.04em}
.vcscore__num small{font-size:.35em;color:var(--muted);letter-spacing:0;margin-left:4px}
.vcscore__notes{display:grid;gap:6px;margin:0;padding:0;list-style:none;font-size:var(--s-xs);color:var(--muted)}
.vcscore__notes b{color:var(--ink);font-weight:600}
.pill{display:inline-flex;align-items:center;gap:8px;padding:6px 12px;border-radius:999px;border:1px solid var(--line);font:600 var(--s-xs)/1 var(--f-body);background:var(--paper);white-space:nowrap}

.radar{width:100%;height:auto;display:block;overflow:visible}
.radar__ring{fill:none;stroke:var(--line);stroke-width:1}
.radar__ring--outer{stroke-width:1.5}
.radar__spoke{stroke:var(--line);stroke-width:1}
.radar__avg{fill:none;stroke:var(--muted);stroke-width:1.5;stroke-dasharray:4 4;opacity:.8}
.radar__area{fill:var(--c);fill-opacity:.22;stroke:var(--cl);stroke-width:2;stroke-linejoin:round;transition:fill .35s,stroke .35s}
.radar__dot{fill:var(--cl);stroke:var(--surface);stroke-width:2;transition:fill .35s}
.radar__hit{fill:transparent}
.radar__label{font:500 11.5px var(--f-body);fill:var(--muted)}
.radar__val{font-weight:700;fill:var(--ink)}
.radar--big .radar__label{font-size:12.5px}

.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));border-top:1px solid var(--line);margin:0 0 28px}
.fact{padding:16px 16px 16px 0;display:grid;gap:4px;border-bottom:1px solid var(--line)}
.fact dt{font-family:var(--f-mono);font-size:var(--s-xs);text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}
.fact dd{margin:0;font-weight:600}
.about{display:grid;gap:24px}
@media (min-width:900px){.about{grid-template-columns:1.4fr 1fr;align-items:start}}
.about p{font-size:var(--s-lg);line-height:1.5}
.about__links{display:flex;flex-wrap:wrap;gap:10px}

.reasons{display:grid;gap:16px;counter-reset:r}
@media (min-width:860px){.reasons{grid-template-columns:repeat(3,1fr)}}
.reason{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:24px;display:grid;gap:10px;align-content:start}
.reason::before{counter-increment:r;content:"0" counter(r);font-family:var(--f-mono);font-size:var(--s-xs);color:var(--accent)}
.reason h3{font-size:var(--s-lg)}
.reason p{color:var(--muted)}

.tools{display:flex;flex-wrap:wrap;gap:14px 28px;align-items:center;justify-content:space-between;margin-bottom:20px}
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;margin:0;padding:0;list-style:none;font-size:var(--s-sm)}
.legend li{display:inline-flex;align-items:center;gap:8px}
.legend span{color:var(--muted);font-size:var(--s-xs)}
.sort{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.sort label{font-size:var(--s-xs);color:var(--muted);margin-right:4px;font-family:var(--f-mono);text-transform:uppercase;letter-spacing:.1em}
.sort button{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:6px 12px;font:500 var(--s-xs)/1 var(--f-body);cursor:pointer}
.sort button[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}

.explorer{display:grid;gap:20px}
@media (min-width:1000px){.explorer{grid-template-columns:minmax(380px,430px) 1fr;align-items:start}.panel{position:sticky;top:calc(76px + env(safe-area-inset-top,0px))}}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:20px;box-shadow:var(--shadow);padding:22px;display:grid;gap:12px;scroll-margin-top:76px}
.panel__head{display:flex;align-items:center;gap:10px}
.panel__head .dot{width:12px;height:12px}
.panel__name{font-size:var(--s-lg);margin-right:auto}
.panel__name a{text-decoration:none}
.panel__name a:hover{text-decoration:underline;text-underline-offset:3px}
.panel__score{font:600 var(--s-lg)/1 var(--f-display);white-space:nowrap}
.panel__score small{font-size:.6em;color:var(--muted);font-weight:400;margin-left:2px}
.panel__meta{font-family:var(--f-mono);font-size:var(--s-xs);color:var(--muted)}
.panel__meta b{color:var(--ink);font-weight:500}
.panel__desc{font-size:var(--s-sm)}
.panel .radar{max-width:380px;margin:4px auto 0}
.panel__key{display:flex;gap:16px;justify-content:center;font-size:var(--s-xs);color:var(--muted)}
.panel__key span{display:inline-flex;align-items:center;gap:6px}
.sw{display:inline-block;width:18px;height:0;border-top:2px solid var(--cl)}
.sw--avg{border-top:2px dashed var(--muted)}
.panel__why{font-size:var(--s-sm);color:var(--muted);border-top:1px dashed var(--line);padding-top:12px}
.panel__why b{color:var(--ink);font-weight:600}
.panel__nav{display:flex;justify-content:space-between;gap:8px}
.panel__nav button{border:1px solid var(--line);background:transparent;border-radius:999px;padding:7px 12px;font-size:var(--s-xs);cursor:pointer;color:var(--ink)}
.panel__nav button:hover{background:var(--line)}

.cards{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(min(100%,232px),1fr));align-content:start}
.co{all:unset;box-sizing:border-box;cursor:pointer;display:grid;gap:6px;align-content:start;padding:14px 14px 13px;border:1px solid var(--line);border-radius:12px;background:var(--surface);transition:border-color .2s,transform .2s var(--ease),box-shadow .2s}
.co:hover{border-color:color-mix(in srgb,var(--ink) 35%,var(--line));transform:translateY(-1px)}
.co:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.co[aria-pressed="true"]{border-color:var(--ink);box-shadow:0 0 0 1px var(--ink),var(--shadow)}
.co__top{display:flex;align-items:center;gap:8px}
.co__name{font:600 var(--s-md)/1.2 var(--f-display);margin-right:auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.co__score{font:600 var(--s-sm)/1 var(--f-body);font-variant-numeric:tabular-nums}
.co__meta{font-family:var(--f-mono);font-size:11.5px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.co__desc{font-size:var(--s-xs);line-height:1.45;color:var(--muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}

.formats{display:grid;gap:16px}
@media (min-width:860px){.formats{grid-template-columns:repeat(3,1fr)}}
.format{border:1px solid var(--line);border-radius:var(--radius);padding:24px;display:grid;gap:10px;align-content:start;background:var(--surface)}
.format h3{font-size:var(--s-lg)}
.format p{color:var(--muted)}
.format .tag{font-family:var(--f-mono);font-size:var(--s-xs);color:var(--accent)}

.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));border-top:1px solid var(--line);margin-bottom:32px}
.stat{padding:20px 20px 0 0;display:grid;gap:4px}
.stat b{font:600 var(--s-xl)/1 var(--f-display);letter-spacing:-.03em}
.stat span{color:var(--muted);font-size:var(--s-sm)}
.proof{display:grid;gap:16px}
@media (min-width:760px){.proof{grid-template-columns:repeat(2,1fr)}}
.proof__item{display:grid;gap:6px;padding:20px 0;border-top:1px solid var(--line)}
.proof__item h3{font-size:var(--s-md)}
.proof__item .role{font-family:var(--f-mono);font-size:var(--s-xs);color:var(--muted)}
.proof__item p{color:var(--muted);font-size:var(--s-sm)}

.method{display:grid;gap:28px}
@media (min-width:900px){.method{grid-template-columns:1fr 1fr}}
.method dl{margin:0;display:grid;gap:12px}
.method dt{font-weight:600}
.method dd{margin:2px 0 0;color:var(--muted);font-size:var(--s-sm)}
.method ul{margin:0;padding-left:18px;color:var(--muted);font-size:var(--s-sm);display:grid;gap:6px}
.small{font-size:var(--s-sm)}

.cta{text-align:center;padding-block:clamp(64px,9vw,120px)}
.cta .head{margin-inline:auto;text-align:center;justify-items:center}
.cta .ctas{justify-content:center}
.foot{padding-block:28px;border-top:1px solid var(--line);font-size:var(--s-xs);color:var(--muted);font-family:var(--f-mono)}
.foot .wrap{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""

JS = r"""
(function(){
var root=document.documentElement;
try{var t=localStorage.getItem("theme");if(t)root.dataset.theme=t}catch(e){}
var tb=document.querySelector(".theme");
if(tb)tb.addEventListener("click",function(){var d=root.dataset.theme?root.dataset.theme==="dark":matchMedia("(prefers-color-scheme: dark)").matches;root.dataset.theme=d?"light":"dark";try{localStorage.setItem("theme",root.dataset.theme)}catch(e){}});

var dataEl=document.getElementById("co-data");if(!dataEl)return;
var DATA=JSON.parse(dataEl.textContent),DIMS=["Domain fit","Business model","AI & data","Stage & momentum","RevOps leverage","Portugal presence"];
var panel=document.getElementById("panel"),svg=document.getElementById("pr"),grid=document.querySelector(".cards");
var cx=+svg.dataset.cx,cy=+svg.dataset.cy,R=+svg.dataset.r,N=6;
var ang=[];for(var i=0;i<N;i++)ang.push((-90+i*360/N)*Math.PI/180);
var area=svg.querySelector(".radar__area"),dots=svg.querySelectorAll(".radar__dot"),hits=svg.querySelectorAll(".radar__hit"),tips=svg.querySelectorAll(".radar__pt title"),vals=svg.querySelectorAll(".radar__val");
var cur=DATA[0].s.slice(),raf=0,reduce=matchMedia("(prefers-reduced-motion: reduce)").matches;
function xy(v,a){return[cx+R*v/5*Math.cos(a),cy+R*v/5*Math.sin(a)]}
function draw(v){area.setAttribute("points",v.map(function(x,i){return xy(x,ang[i]).join(",")}).join(" "));
for(var i=0;i<N;i++){var p=xy(v[i],ang[i]);dots[i].setAttribute("cx",p[0]);dots[i].setAttribute("cy",p[1]);hits[i].setAttribute("cx",p[0]);hits[i].setAttribute("cy",p[1])}}
function animate(to){cancelAnimationFrame(raf);var from=cur.slice(),t0=performance.now(),D=reduce?0:480;
function step(now){var k=D?Math.min(1,(now-t0)/D):1;k=1-Math.pow(1-k,3);cur=from.map(function(f,i){return f+(to[i]-f)*k});draw(cur);if(k<1)raf=requestAnimationFrame(step)}raf=requestAnimationFrame(step)}
function $(s){return panel.querySelector(s)}
function select(idx,scroll){var c=DATA[idx];
panel.className="panel t-"+c.k;
$(".panel__name").innerHTML="";var nm=document.createTextNode(c.n);
if(c.u){var a=document.createElement("a");a.href=c.u;a.target="_blank";a.rel="noopener";a.appendChild(nm);a.appendChild(document.createTextNode(" ↗"));$(".panel__name").appendChild(a)}else{$(".panel__name").appendChild(nm)}
$(".panel__score b").textContent=c.t;$(".panel__tier").textContent=c.kl+" match";
$(".panel__meta-text").textContent=c.m;$(".panel__desc").textContent=c.d;$(".panel__why-text").textContent=c.w;
for(var i=0;i<N;i++){vals[i].textContent=c.s[i];tips[i].textContent=DIMS[i]+": "+c.s[i]+" / 5"}
svg.setAttribute("aria-label",c.n+": "+DIMS.map(function(d,i){return d+" "+c.s[i]+" of 5"}).join("; "));
grid.querySelectorAll(".co").forEach(function(b){b.setAttribute("aria-pressed",+b.dataset.i===idx?"true":"false")});
animate(c.s);
if(scroll&&matchMedia("(max-width: 999px)").matches)panel.scrollIntoView({behavior:reduce?"auto":"smooth",block:"start"})}
grid.addEventListener("click",function(ev){var b=ev.target.closest(".co");if(b)select(+b.dataset.i,true)});
function step(dir){var list=[].slice.call(grid.querySelectorAll(".co")),pos=list.findIndex(function(b){return b.getAttribute("aria-pressed")==="true"});var nx=list[(pos+dir+list.length)%list.length];select(+nx.dataset.i,false);nx.focus({preventScroll:true})}
$(".panel__prev").addEventListener("click",function(){step(-1)});$(".panel__next").addEventListener("click",function(){step(1)});

var sb=document.querySelectorAll(".sort button");
sb.forEach(function(btn){btn.addEventListener("click",function(){var k=btn.dataset.k;sb.forEach(function(x){x.setAttribute("aria-pressed",x===btn?"true":"false")});
var cards=[].slice.call(grid.children);cards.sort(function(a,b){return(+b.dataset[k])-(+a.dataset[k])||(+b.dataset.total)-(+a.dataset.total)});cards.forEach(function(c){grid.appendChild(c)})})});
})();
"""

MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>'
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'


def meta_line(c):
    return " · ".join(x for x in (c.get("sector"), c.get("hq")) if x)


def card(c, i, selected):
    total = company_score(c)
    key, label = tier(total)
    data = " ".join(f'data-k{j}="{v}"' for j, v in enumerate(c["s"]))
    return (f'<button type="button" class="co t-{key}" data-i="{i}" data-total="{total}" {data} aria-pressed="{"true" if selected else "false"}" '
            f'aria-label="{e(c["name"])}, {label.lower()} match, {total} out of 100">'
            f'<span class="co__top"><span class="dot" aria-hidden="true"></span><span class="co__name">{e(c["name"])}</span>'
            f'<span class="co__score">{total}</span></span>'
            f'<span class="co__meta">{e(meta_line(c))}</span>'
            f'<span class="co__desc">{e(c["desc"])}</span></button>')


def page(vc, me, built):
    vals, overall, notes = vc_scores(vc)
    vkey, vlabel = tier(overall)
    comps = sorted(vc["companies"], key=lambda c: (-company_score(c), c["name"].lower()))
    counts = {k: sum(1 for c in comps if tier(company_score(c))[0] == k) for _, k, _ in TIERS}
    avg = [round(sum(c["s"][j] for c in comps) / len(comps), 2) for j in range(6)]
    name = e(vc["name"])
    first, _, rest = vc["name"].partition(" ")
    h1_name = e(first) + "&nbsp;" + e(rest) if rest and len(first) <= 2 else name
    built_h = built.strftime("%-d %b %Y")

    vc_chart = radar([vals[k] for k, _ in VC_DIMS], [l for _, l in VC_DIMS], size=(400, 300), r=96, label_gap=16, cls="radar--big")
    notes_html = "".join(f'<li><b>{e(l)}:</b> {e(notes.get(k, ""))}</li>' for k, l in VC_DIMS if notes.get(k))
    facts = "".join(f'<div class="fact"><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in vc["facts"])
    reasons = "".join(f'<div class="reason"><h3>{e(r["title"])}</h3><p>{e(r["body"])}</p></div>' for r in vc["reasons"])
    legend = "".join(f'<li><span class="dot t-{k}" aria-hidden="true"></span>{lab} <span>{RANGES[k]} · {counts[k]}</span></li>' for _, k, lab in TIERS)
    sort_btns = '<button type="button" data-k="total" aria-pressed="true">Overall</button>' + "".join(
        f'<button type="button" data-k="k{i}" aria-pressed="false">{e(d[1])}</button>' for i, d in enumerate(DIMS))
    cards = "".join(card(c, i, i == 0) for i, c in enumerate(comps))

    data = []
    for c in comps:
        t = company_score(c)
        k, kl = tier(t)
        data.append({"n": c["name"], "u": c.get("url", ""), "d": c["desc"], "m": meta_line(c), "s": c["s"], "t": t, "k": k, "kl": kl, "w": c["why"]})
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    first = comps[0]
    ft = company_score(first)
    fk, fkl = tier(ft)
    first_name = (f'<a href="{e(first["url"])}" target="_blank" rel="noopener">{e(first["name"])} ↗</a>' if first.get("url") else e(first["name"]))
    panel_chart = radar(first["s"], [d[1] for d in DIMS], size=(380, 280), r=96, label_gap=15,
                        full_labels=[d[0] for d in DIMS], avg=avg, rid="pr", cls="radar--big")

    formats = "".join(f'<div class="format"><span class="tag">{e(f["fit"])}</span><h3>{e(f["title"])}</h3><p>{e(f["body"])}</p></div>' for f in me["engagements"])
    stats = "".join(f'<div class="stat"><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in me["stats"])
    proof = "".join(f'<div class="proof__item"><h3>{e(p["org"])}</h3><span class="role">{e(p["role"])}</span><p>{e(p["body"])}</p></div>' for p in me["proof"])
    dims = "".join(f'<div><dt>{e(d[0])}</dt><dd>{e(d[2])}</dd></div>' for d in DIMS)
    sources = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></li>' for t, u in vc["sources"])
    inactive = ", ".join(e(x) for x in vc.get("inactive", []))
    inactive_html = f"<li>Not scored (no longer active): {inactive}.</li>" if inactive else ""
    extra_notes = "".join(f"<li>{e(n)}</li>" for n in vc.get("method_notes", []))
    tally = " · ".join(f"{counts[k]} {lab.lower()}" for _, k, lab in TIERS if counts[k])
    prepared = e(vc.get("prepared_for") or f"the {vc['name']} team")
    website_btn = f'<a class="btn btn--sm" href="{e(vc["website"])}" target="_blank" rel="noopener">Website ↗</a>' if vc.get("website") else ""
    portfolio_btn = f'<a class="btn btn--sm" href="{e(vc["portfolio_url"])}" target="_blank" rel="noopener">Portfolio ↗</a>' if vc.get("portfolio_url") else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>Enzo Garry × {name}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(vc['lede'])}">
<meta property="og:title" content="Enzo Garry × {name}: Product &amp; RevOps for your portfolio">
<meta property="og:description" content="{e(vc['lede'])}">
<link rel="icon" href="../../assets/icons/Favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap top__in">
  <a class="top__me" href="{e(me['portfolio'])}">Enzo Garry <span>· {e(me['role'])}</span></a>
  <a class="link" href="{e(me['portfolio'])}">Portfolio</a>
  <a class="link" href="{e(me['linkedin'])}" target="_blank" rel="noopener">LinkedIn</a>
  <button class="theme" type="button" aria-label="Toggle dark mode">{MOON}</button>
  <a class="btn btn--solid btn--sm" href="{e(me['calendly'])}" target="_blank" rel="noopener">Book a call</a>
</div></header>

<main>
<section class="hero"><div class="wrap hero__grid">
  <div class="hero__text">
    <p class="eyebrow">Prepared for {prepared} · {built_h}</p>
    <h1>Enzo Garry <span class="x">×</span> {h1_name}</h1>
    <p class="hero__lede">{e(vc['lede'])}</p>
    <div class="ctas">
      <a class="btn btn--solid" href="{e(me['calendly'])}" target="_blank" rel="noopener">Book a 30-min call {ARROW}</a>
      <a class="btn" href="#matches">Explore portfolio matches</a>
    </div>
  </div>
  <aside class="vcscore t-{vkey}" aria-label="Match with {name}">
    <div class="vcscore__top">
      <div><p class="eyebrow">Match with {name}</p><p class="vcscore__num">{overall}<small>/ 100</small></p></div>
      <span class="pill"><span class="dot" aria-hidden="true"></span>{vlabel} match</span>
    </div>
    {vc_chart}
    <ul class="vcscore__notes">{notes_html}</ul>
  </aside>
</div></section>

<section id="vc"><div class="wrap">
  <div class="head"><p class="eyebrow">01 · {name} at a glance</p><h2>Who you back, and how.</h2></div>
  <dl class="facts">{facts}</dl>
  <div class="about">
    <p>{e(vc['position'])}</p>
    <div class="about__links">{website_btn}{portfolio_btn}</div>
  </div>
</div></section>

<section id="why"><div class="wrap">
  <div class="head"><p class="eyebrow">02 · Why we should work together</p><h2>Three reasons this fits.</h2>
    <p>{e(vc['summary'])}</p></div>
  <div class="reasons">{reasons}</div>
</div></section>

<section id="matches"><div class="wrap">
  <div class="head"><p class="eyebrow">03 · Portfolio match</p><h2>Where I can help across your portfolio.</h2>
    <p>{e(vc.get('matches_intro') or f"{len(comps)} active companies")}, each scored on six dimensions from 0 to 5. Click a company to see its profile; the dashed outline is the portfolio average.</p></div>
  <div class="tools">
    <ul class="legend" aria-label="Match levels">{legend}</ul>
    <div class="sort" role="group" aria-label="Sort companies"><label>Sort by</label>{sort_btns}</div>
  </div>
  <div class="explorer">
    <aside class="panel t-{fk}" id="panel" aria-live="polite">
      <div class="panel__head"><span class="dot" aria-hidden="true"></span><h3 class="panel__name">{first_name}</h3>
        <span class="panel__score"><b>{ft}</b><small>/100</small></span></div>
      <p class="panel__meta"><b class="panel__tier">{fkl} match</b> · <span class="panel__meta-text">{e(meta_line(first))}</span></p>
      <p class="panel__desc">{e(first['desc'])}</p>
      {panel_chart}
      <p class="panel__key"><span><i class="sw" aria-hidden="true"></i>Selected company</span><span><i class="sw sw--avg" aria-hidden="true"></i>Portfolio average</span></p>
      <p class="panel__why"><b>Where I’d help.</b> <span class="panel__why-text">{e(first['why'])}</span></p>
      <div class="panel__nav"><button type="button" class="panel__prev">← Previous</button><button type="button" class="panel__next">Next →</button></div>
    </aside>
    <div class="cards" aria-label="Portfolio companies">{cards}</div>
  </div>
  <script type="application/json" id="co-data">{data_json}</script>
</div></section>

<section id="formats"><div class="wrap">
  <div class="head"><p class="eyebrow">04 · How I can plug in</p><h2>Three ways to work together.</h2>
    <p>Freelance or full-time, for one company or several in your portfolio.</p></div>
  <div class="formats">{formats}</div>
</div></section>

<section id="proof"><div class="wrap">
  <div class="head"><p class="eyebrow">05 · Track record</p><h2>What I’ve shipped.</h2>
    <p>{e(me['base'])}-based · {e(me['languages'])} · Hong Kong, New York, Lisbon.</p></div>
  <div class="stats">{stats}</div>
  <div class="proof">{proof}</div>
  <div class="ctas" style="margin-top:28px">
    <a class="btn" href="{e(me['portfolio'])}">Full portfolio</a>
    <a class="btn" href="{e(me['resume'])}" target="_blank" download>Download resume</a>
  </div>
</div></section>

<section id="method"><div class="wrap">
  <div class="head"><p class="eyebrow">06 · How the scores work</p><h2>Method and sources.</h2></div>
  <div class="method">
    <dl>{dims}</dl>
    <div class="small">
      <ul>
        <li>Each dimension is scored 0 to 5; the company score is the total out of 30, scaled to 100. Strong match (green) 70+, medium (orange) 50–69, low (yellow) under 50.</li>
        <li>The {name} score averages five dimensions: thesis overlap, stage fit and platform support are my assessment; top matches and Portugal footprint are computed from the company scores.</li>
        <li>Scores measure how well my experience maps to each company, not the company’s quality. They’re my own read of public information as of {built_h}.</li>
        {inactive_html}{extra_notes}
      </ul>
      <p class="eyebrow" style="margin:20px 0 8px">Sources</p>
      <ul>{sources}</ul>
    </div>
  </div>
</div></section>

<section class="cta"><div class="wrap">
  <div class="head"><h2>Got a company in mind?</h2><p>Tell me who needs a hand. I’ll come back with a concrete first-month plan.</p></div>
  <div class="ctas">
    <a class="btn btn--solid" href="{e(me['calendly'])}" target="_blank" rel="noopener">Book a 30-min call {ARROW}</a>
    <a class="btn" href="{e(me['linkedin'])}" target="_blank" rel="noopener">LinkedIn</a>
  </div>
</div></section>
</main>
<footer class="foot"><div class="wrap"><span>Enzo Garry · Product &amp; RevOps · {e(me['base'])}</span><span>Updated {built_h}</span></div></footer>
<script>{JS}</script>
</body>
</html>
"""


HUB_CSS = r"""
html,body{height:100%}
body{display:flex;flex-direction:column;overflow:hidden}
.top__me{margin-right:0}
.hub__count{font-family:var(--f-mono);font-size:var(--s-xs);color:var(--muted);margin-right:auto}
.tabs{display:flex;gap:6px;overflow-x:auto;padding:10px max(16px,env(safe-area-inset-left,0px));border-bottom:1px solid var(--line);background:var(--paper);scrollbar-width:thin;flex:none}
.tab{all:unset;box-sizing:border-box;cursor:pointer;display:inline-flex;align-items:center;gap:8px;padding:8px 13px;border:1px solid var(--line);border-radius:999px;background:var(--surface);font:500 var(--s-xs)/1 var(--f-body);white-space:nowrap}
.tab:hover{border-color:color-mix(in srgb,var(--ink) 35%,var(--line))}
.tab:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tab[aria-selected="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.tab b{font-variant-numeric:tabular-nums;font-weight:600}
.view{flex:1;min-height:0;position:relative}
.view>[hidden]{display:none!important}
.frame{position:absolute;inset:0;display:flex;flex-direction:column}
.frame__bar{display:flex;align-items:center;gap:8px 12px;padding:8px max(16px,env(safe-area-inset-left,0px));border-bottom:1px solid var(--line);font-size:var(--s-xs);color:var(--muted);flex:none}
.frame__url{font-family:var(--f-mono);margin-right:auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;flex:1 1 0}
.frame__bar .btn{flex:none}
.frame iframe{flex:1;width:100%;border:0;background:var(--paper)}
.overview{position:absolute;inset:0;overflow:auto;padding-block:clamp(28px,5vw,56px)}
.tbl{width:100%;border-collapse:collapse;font-size:var(--s-sm)}
.tbl th{font:500 var(--s-xs)/1.2 var(--f-mono);text-transform:uppercase;letter-spacing:.1em;color:var(--muted);text-align:left;padding:10px 12px 10px 0;border-bottom:1px solid var(--line);white-space:nowrap}
.tbl td{padding:12px 12px 12px 0;border-bottom:1px solid var(--line);vertical-align:middle}
.tbl td.n,.tbl th.n{text-align:right;font-variant-numeric:tabular-nums}
.tbl tr{cursor:pointer}
.tbl tbody tr:hover td{background:color-mix(in srgb,var(--line) 40%,transparent)}
.tbl .nm{display:inline-flex;align-items:center;gap:10px;font-weight:600}
.tbl a{color:var(--muted)}
.tblwrap{overflow-x:auto}
@media (max-width:640px){.tbl .opt{display:none}}
"""

HUB_JS = r"""
(function(){
var root=document.documentElement;
try{var t=localStorage.getItem("theme");if(t)root.dataset.theme=t}catch(e){}
var tb=document.querySelector(".theme");
if(tb)tb.addEventListener("click",function(){var d=root.dataset.theme?root.dataset.theme==="dark":matchMedia("(prefers-color-scheme: dark)").matches;root.dataset.theme=d?"light":"dark";try{localStorage.setItem("theme",root.dataset.theme)}catch(e){}
document.querySelectorAll("iframe").forEach(function(f){try{f.contentDocument.documentElement.dataset.theme=root.dataset.theme}catch(e){}})});
var tabs=[].slice.call(document.querySelectorAll(".tab")),frame=document.getElementById("frame"),ov=document.getElementById("overview"),
ifr=frame.querySelector("iframe"),url=frame.querySelector(".frame__url"),open=frame.querySelector(".frame__open"),copy=frame.querySelector(".frame__copy");
function abs(slug){return new URL(slug+"/",location.href).href}
function show(slug){
  var t=tabs.find(function(x){return x.dataset.slug===slug})||tabs[0];slug=t.dataset.slug;
  tabs.forEach(function(x){x.setAttribute("aria-selected",x===t?"true":"false")});
  t.scrollIntoView({block:"nearest",inline:"nearest"});
  if(slug==="all"){ov.hidden=false;frame.hidden=true;document.title="VC pages";return}
  ov.hidden=true;frame.hidden=false;
  var u=abs(slug);if(ifr.dataset.slug!==slug){ifr.src=slug+"/";ifr.dataset.slug=slug}
  url.textContent=u;open.href=u;copy.textContent="Copy link";document.title=t.dataset.name+" · VC pages";
}
function route(){show(decodeURIComponent(location.hash.slice(1))||"all")}
tabs.forEach(function(t,i){
  t.addEventListener("click",function(){location.hash=t.dataset.slug});
  t.addEventListener("keydown",function(ev){var d=ev.key==="ArrowRight"?1:ev.key==="ArrowLeft"?-1:0;if(!d)return;ev.preventDefault();var n=tabs[(i+d+tabs.length)%tabs.length];n.focus();n.click()});
});
document.querySelectorAll("tr[data-slug]").forEach(function(r){r.addEventListener("click",function(ev){if(ev.target.closest("a"))return;location.hash=r.dataset.slug})});
copy.addEventListener("click",function(){var u=url.textContent;(navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(function(){copy.textContent="Copied"},function(){copy.textContent="Copy failed"})});
ifr.addEventListener("load",function(){try{if(root.dataset.theme)ifr.contentDocument.documentElement.dataset.theme=root.dataset.theme}catch(e){}});
addEventListener("hashchange",route);route();
})();
"""


def hub(rows, me, built):
    """Private index of every VC page: an overview table plus one tab per VC (each page in an iframe)."""
    rows = sorted(rows, key=lambda r: (-r["overall"], r["name"].lower()))
    built_h = built.strftime("%-d %b %Y")
    tabs = '<button type="button" role="tab" class="tab" data-slug="all" data-name="Overview" aria-selected="true">Overview</button>' + "".join(
        f'<button type="button" role="tab" class="tab" data-slug="{e(r["slug"])}" data-name="{e(r["name"])}" aria-selected="false">'
        f'<span class="dot t-{r["key"]}" aria-hidden="true"></span>{e(r.get("short") or r["name"])} <b>{r["overall"]}</b></button>' for r in rows)
    trs = "".join(
        f'<tr data-slug="{e(r["slug"])}"><td><span class="nm"><span class="dot t-{r["key"]}" aria-hidden="true"></span>{e(r["name"])}</span></td>'
        f'<td class="n"><b>{r["overall"]}</b></td><td class="n opt">{r["n"]}</td>'
        f'<td class="opt">{" · ".join(f"{r["counts"][k]} {lab.lower()}" for _, k, lab in TIERS if r["counts"][k])}</td>'
        f'<td class="opt">{e(r["best"])}</td>'
        f'<td><a href="{e(r["slug"])}/" target="_blank" rel="noopener">Open ↗</a></td></tr>' for r in rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>VC pages</title>
<link rel="icon" href="../assets/icons/Favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}{HUB_CSS}</style>
</head>
<body>
<header class="top" style="position:static"><div class="wrap top__in">
  <a class="top__me" href="{e(me['portfolio'])}">Enzo Garry <span>· VC pages</span></a>
  <span class="hub__count">{len(rows)} VCs · built {built_h}</span>
  <button class="theme" type="button" aria-label="Toggle dark mode">{MOON}</button>
</div></header>
<nav class="tabs" role="tablist" aria-label="VC pages">{tabs}</nav>
<main class="view">
  <div class="overview" id="overview"><div class="wrap">
    <div class="head"><p class="eyebrow">Private · not linked from the site</p><h2>All VC pages.</h2>
      <p>Sorted by match score. Click a row or a tab to preview the page; copy its link to send it.</p></div>
    <div class="tblwrap"><table class="tbl">
      <thead><tr><th>VC</th><th class="n">Score</th><th class="n opt">Cos.</th><th class="opt">Matches</th><th class="opt">Top company</th><th></th></tr></thead>
      <tbody>{trs}</tbody>
    </table></div>
  </div></div>
  <div class="frame" id="frame" hidden>
    <div class="frame__bar"><span class="frame__url"></span>
      <button type="button" class="btn btn--sm frame__copy">Copy link</button>
      <a class="btn btn--sm frame__open" target="_blank" rel="noopener">Open ↗</a></div>
    <iframe title="VC page preview"></iframe>
  </div>
</main>
<script>{HUB_JS}</script>
</body>
</html>
"""


LIVE = "https://nzoops.github.io/Portfolio/"
ART = pathlib.Path(__import__("os").environ["ARTIFACT_DIR"]) if __import__("os").environ.get("ARTIFACT_DIR") else None


def artifact_variant(html):
    """Same page for a claude.ai artifact: no document skeleton, absolute links to the live site."""
    head, rest = html.split("<title>", 1)
    html = "<title>" + rest
    html = html.replace("</head>\n<body>\n", "").replace("</body>\n</html>\n", "")
    html = html.replace('<link rel="icon" href="../../assets/icons/Favicon.svg" type="image/svg+xml">\n', "")
    html = html.replace('target="_blank" download>', 'target="_blank" rel="noopener">')
    html = html.replace('href="../../', 'href="' + LIVE)
    meta_robots = '<meta name="robots" content="noindex, nofollow">\n'
    return html.replace(meta_robots, "")


def main():
    me = json.loads((SRC / "_profile.json").read_text())
    built = date.today()
    made = []
    rows = []
    for f in sorted(SRC.glob("*.json")):
        if f.name.startswith("_"):
            continue
        vc = json.loads(f.read_text())
        d = OUT / vc["slug"]
        d.mkdir(parents=True, exist_ok=True)
        html = page(vc, me, built)
        (d / "index.html").write_text(html)
        if ART:
            ART.mkdir(parents=True, exist_ok=True)
            (ART / f"vc-{vc['slug']}.html").write_text(artifact_variant(html))
        vals, overall, _ = vc_scores(vc)
        counts = {k: sum(1 for c in vc["companies"] if tier(company_score(c))[0] == k) for _, k, _ in TIERS}
        made.append((vc["name"], overall, vals, len(vc["companies"]), counts))
        best = max(vc["companies"], key=lambda c: company_score(c))
        rows.append({"slug": vc["slug"], "name": vc["name"], "short": vc.get("short"), "overall": overall, "key": tier(overall)[0],
                     "n": len(vc["companies"]), "counts": counts, "best": f'{best["name"]} ({company_score(best)})'})
    (OUT / "index.html").write_text(hub(rows, me, built))
    for n, o, v, c, k in made:
        print(f"{n:30s} {o:3d}  {v}  companies={c} {k}")


if __name__ == "__main__":
    main()
