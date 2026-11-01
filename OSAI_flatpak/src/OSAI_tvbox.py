import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from ollama import Client
from duckduckgo_search import DDGS

app = FastAPI(title="OSAI OS Core TVBox")

# Conexão com o Ollama hospedado no sistema operacional (host)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
client = Client(host=OLLAMA_HOST)

# Modelo LLM padrão otimizado para raciocínio e português
MODELO_LLM = 'qwen2.5:3b'

# Interface padrão na raiz: auto (detecta TV pelo User-Agent), tv ou web
UI_PADRAO = os.getenv("OSAI_UI", "auto").lower()

# Estado inicial simulado da residência
ESTADO_CASA = {
    "sala": {
        "lampada_principal": {"tipo": "light", "estado": "ligado"},
        "televisao": {"tipo": "tv", "estado": "desligado"}
    },
    "quarto": {
        "ar_condicionado": {"tipo": "climate", "estado": "ligado", "temp": 22},
        "lampada_cabeceira": {"tipo": "light", "estado": "desligado"}
    },
    "cozinha": {
        "iluminacao_led": {"tipo": "light", "estado": "desligado"}
    }
}

class ComandoRequest(BaseModel):
    comando: str

class ToggleRequest(BaseModel):
    comodo: str
    dispositivo: str

# =====================================================================
# INTERFACE DE TV (D-PAD / 10-foot UI)
# Sem CDNs externos (tailwind/font-awesome removidos), ideal para as
# webviews lentas de TV Box. Navegação 100% pelo controle remoto:
# setas movem o foco geometricamente, OK/Enter seleciona/toggle.
# =====================================================================
HTML_TV = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>OSAI OS TV</title>
<style>
:root{
  --bg:#05070f; --panel:#0d1424; --panel2:#131b30; --line:#22314f;
  --txt:#e8ecf7; --dim:#8fa0c0; --ind:#6366f1; --ind2:#818cf8;
  --amber:#f59e0b; --green:#34d399; --red:#f87171;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  background:var(--bg); color:var(--txt);
  font-family:"Noto Sans",Roboto,sans-serif;
  display:flex; flex-direction:column;
  padding:20px 30px 0; overflow:hidden;
  -webkit-user-select:none; user-select:none;
}
.topbar{display:flex; align-items:center; gap:26px; padding-bottom:16px; border-bottom:2px solid var(--line)}
.logo{display:flex; align-items:center; gap:12px; font-size:30px; font-weight:800; letter-spacing:1px; color:var(--ind2)}
.chip{background:var(--ind); border-radius:14px; padding:8px 12px; display:flex}
.chip svg{width:30px;height:30px;stroke:#fff}
.on-air{display:flex;align-items:center;gap:8px;font-size:19px;color:var(--green);font-family:monospace}
.on-air .dot{width:11px;height:11px;border-radius:50%;background:var(--green);box-shadow:0 0 10px var(--green)}
.tabs{display:flex; gap:14px; margin-left:auto}
.tab{font-size:24px; font-weight:700; padding:14px 30px; border-radius:16px;
     background:var(--panel); border:3px solid var(--line); color:var(--dim);
     display:flex; align-items:center; gap:10px; cursor:pointer}
.tab svg{width:26px;height:26px;stroke:currentColor}
.tab.active{background:var(--ind); color:#fff; border-color:var(--ind2); box-shadow:0 6px 18px rgba(99,102,241,.35)}
main{flex:1; overflow-y:auto; padding:22px 6px 8px; scroll-behavior:smooth}
main::-webkit-scrollbar{width:0}
.cards{display:grid; grid-template-columns:repeat(3,1fr); gap:20px}
.card{background:var(--panel); border:2px solid var(--line); border-radius:20px; padding:18px 18px 12px}
.card header{display:flex; align-items:center; justify-content:space-between;
             border-bottom:2px solid var(--line); padding-bottom:12px; margin-bottom:12px}
.card h3{font-size:25px; color:var(--ind2); display:flex; align-items:center; gap:10px; text-transform:capitalize}
.card h3 svg{width:24px;height:24px;stroke:var(--ind)}
.count{font-size:16px; color:var(--dim); background:var(--panel2); border:2px solid var(--line);
       padding:5px 14px; border-radius:999px; white-space:nowrap}
.dev{width:100%; display:flex; align-items:center; justify-content:space-between; gap:12px;
     padding:12px 14px; margin-bottom:10px; text-align:left; cursor:pointer;
     background:#0a1020; border:3px solid #1a2440; border-radius:16px;
     color:inherit; font-family:inherit}
.dev .left{display:flex; align-items:center; gap:14px; min-width:0}
.dev .ico{width:50px;height:50px; min-width:50px; border-radius:14px; background:#19233c;
          display:flex; align-items:center; justify-content:center}
.dev .ico svg{width:28px;height:28px;stroke:#7e8bab;fill:none;stroke-width:2;stroke-linecap:round}
.dev .nome{font-size:23px; font-weight:700; text-transform:capitalize; white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
.dev .st{font-size:17px; font-family:monospace; margin-top:4px; color:var(--dim)}
.acl{font-size:20px; font-weight:800; padding:11px 20px; border-radius:13px;
     background:#19233c; color:#8892ad; border:2px solid #26334f; white-space:nowrap}
.dev.on .acl{color:var(--amber); border-color:rgba(245,158,11,.45); background:rgba(245,158,11,.10)}
.dev.on .ico{background:rgba(245,158,11,.16)}
.dev.on .ico svg{stroke:var(--amber)}
.dev.on .st{color:var(--amber)}

#chat-sec{height:100%; display:none; flex-direction:column; gap:0}
#chat-box{flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:14px; padding:6px 6px 14px}
#chat-box::-webkit-scrollbar{width:0}
.msgbot,.msguser{max-width:72%; padding:16px 20px; border-radius:20px; font-size:23px; line-height:1.45}
.msguser{align-self:flex-end; background:#263148; border:2px solid #33425f; color:#dbe3f5}
.msgbot{align-self:flex-start; background:#171e33; border:2px solid #2b3a60}
.msgbot .who{font-size:17px; font-weight:800; color:var(--ind2); margin-bottom:6px; display:flex; align-items:center; gap:8px}
.msgbot .who svg{width:18px;height:18px;stroke:var(--ind2)}
.msgerr{align-self:flex-start; background:#331417; border:2px solid #5f2029; color:#fca5a5; padding:16px 20px; border-radius:20px; font-size:22px}
.msginfo{align-self:center; background:#0a1020; color:var(--dim); font-size:19px; padding:10px 18px; border-radius:999px}
.pensando{display:inline-flex; gap:6px; align-items:center}
.pensando i{width:10px;height:10px;border-radius:50%;background:var(--ind2);animation:b 1.2s infinite}
.pensando i:nth-child(2){animation-delay:.2s}.pensando i:nth-child(3){animation-delay:.4s}
@keyframes b{0%,60%,100%{opacity:.25}30%{opacity:1}}

#form-chat{display:flex; gap:14px; padding:16px 0 20px}
#input-chat{flex:1; font-size:24px; padding:16px 20px; border-radius:16px;
            background:#0a1020; border:3px solid #1a2440; color:var(--txt); outline:none; font-family:inherit}
#btn-send{display:flex; align-items:center; gap:10px; font-size:23px; font-weight:800; padding:0 30px;
          border-radius:16px; background:var(--ind); border:3px solid var(--ind2); color:#fff; cursor:pointer}
#btn-send svg{width:24px;height:24px;stroke:#fff}

.hint{position:fixed; left:0; right:0; bottom:0; z-index:10;
      display:flex; gap:26px; justify-content:center; align-items:center;
      padding:12px; background:#070b15; border-top:2px solid var(--line);
      font-size:18px; color:var(--dim)}
.hint b{color:var(--txt); background:#19233c; border:1px solid #2b3a5f; border-radius:8px; padding:2px 10px; font-family:monospace}

:focus{outline:none}
.f:focus{border-color:var(--ind2); box-shadow:0 0 0 6px rgba(129,140,248,.35); background:#1c2846; color:#fff}
.dev.f{background:#1c2846}
.dev.f .ico{background:#2b3a60}
.btn{width:46px; height:46px; min-width:46px; display:flex; align-items:center; justify-content:center;
     background:var(--panel); border:3px solid var(--line); border-radius:14px; cursor:pointer; color:var(--dim)}
.btn svg{width:24px;height:24px;stroke:currentColor}
</style>
</head>
<body>

<div class="topbar">
  <div class="logo">
    <span class="chip"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><rect x="5" y="5" width="14" height="14" rx="3"/><rect x="9" y="9" width="6" height="6" rx="1.5" fill="#fff" stroke="none"/></svg></span>
    OSAI OS <span class="on-air"><span class="dot"></span>TV</span>
  </div>

  <nav class="tabs">
    <button class="tab f active" id="tab-casa" data-view="casa">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><path d="M3 11 12 4l9 7"/><path d="M5 10v9h14v-9"/></svg>
      Casa Inteligente
    </button>
    <button class="tab f" id="tab-chat" data-view="chat">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><rect x="3" y="4" width="18" height="13" rx="3"/><path d="M8 21l2-4h9"/><circle cx="8.5" cy="10.5" r="1" fill="currentColor"/><circle cx="12" cy="10.5" r="1" fill="currentColor"/><circle cx="15.5" cy="10.5" r="1" fill="currentColor"/></svg>
      Assistente IA
    </button>
    <button class="btn f" id="btn-refresh" title="Atualizar">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 3v5h-5"/></svg>
    </button>
  </nav>
</div>

<main id="sec-casa">
  <div class="cards" id="grid"></div>
</main>

<div id="sec-chat">
  <div id="chat-box">
    <div class="msgbot">
      <div class="who"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><rect x="5" y="6" width="14" height="12" rx="3"/><circle cx="9.5" cy="12" r="1.2" fill="#818cf8"/><circle cx="14.5" cy="12" r="1.2" fill="#818cf8"/></svg> OSAI OS</div>
      Ola, Alvaro! Pode ligar/desligar dispositivos ou me pedir pesquisas gerais.
    </div>
  </div>
  <form id="form-chat">
    <input id="input-chat" class="f" type="text" autocomplete="off" enterkeyhint="send"
           placeholder="Ex: desligar luz do quarto / quem foi Gyro Zeppeli?">
    <button id="btn-send" class="f" type="submit">Enviar
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><path d="M3 11 21 4l-7 18-3-8-8-3z"/></svg>
    </button>
  </form>
</div>

<div class="hint">
  <span><b>&#8592;&#8593;&#8595;&#8594;</b> navegar</span>
  <span><b>OK</b> selecionar</span>
  <span><b>MENU</b> servidor</span>
</div>

<script>
const SVG_LIGHT='<svg viewBox="0 0 24 24"><path d="M9 18h6"/><path d="M10 21h4"/><path d="M12 3a6 6 0 0 1 3.6 10.8c-.6.5-.9 1.2-.9 2v.2h-5.4v-.2c0-.8-.3-1.5-.9-2A6 6 0 0 1 12 3z"/></svg>';
const SVG_CLIMATE='<svg viewBox="0 0 24 24"><path d="M12 2v20"/><path d="m4 6 16 6L4 18"/><path d="m4 18 16-6-16-6z"/><path d="m6 4-1.5-1.5M18 4l1.5-1.5M6 20l-1.5 1.5M18 20l1.5 1.5"/></svg>';
const SVG_TV='<svg viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>';
const SVG_SENSOR='<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="2"/><path d="M7.8 7.8a6 6 0 0 0 0 8.4M16.2 16.2a6 6 0 0 0 0-8.4M4.9 4.9a10 10 0 0 0 0 14.2M19.1 19.1a10 10 0 0 0 0-14.2"/></svg>';
const SVG_ROOM='<svg viewBox="0 0 24 24"><path d="M3 4h9l3 3h6v12H3z"/></svg>';
const SVG_BOT='<svg viewBox="0 0 24 24"><rect x="5" y="6" width="14" height="12" rx="3"/><circle cx="9.5" cy="12" r="1.2"/><circle cx="14.5" cy="12" r="1.2"/></svg>';

const ICO={light:SVG_LIGHT,climate:SVG_CLIMATE,tv:SVG_TV};

const grid=document.getElementById('grid');
const chatBox=document.getElementById('chat-box');
const inputChat=document.getElementById('input-chat');
const secCasa=document.getElementById('sec-casa');
const secChat=document.getElementById('sec-chat');
let view='casa';
let estadoCache=null;
let lastFocusKey=null;

function switchView(v){
  view=v;
  lastFocusKey=null;
  document.getElementById('tab-casa').classList.toggle('active',v==='casa');
  document.getElementById('tab-chat').classList.toggle('active',v==='chat');
  if(v==='casa'){
    secChat.style.display='none';
    secCasa.style.display='block';
    renderCasa();
  }else{
    secCasa.style.display='none';
    secChat.style.height='100%';
    secChat.style.display='flex';
    setTimeout(()=>inputChat.focus(),60);
    chatBox.scrollTop=chatBox.scrollHeight;
  }
}

function renderCasa(){
  if(!estadoCache)return;
  grid.innerHTML='';
  for(const[comodo,dispositivos]of Object.entries(estadoCache)){
    let linhaDevs='';
    for(const[disp,dados]of Object.entries(dispositivos)){
      const isLigado=dados.estado==='ligado';
      const ico=ICO[dados.tipo]||SVG_SENSOR;
      const st=dados.estado.toUpperCase()+(dados.temp?' - '+dados.temp+'\u00B0C':'');
      linhaDevs+=`
        <button class="dev f ${isLigado?'on':'off'}" data-key="${comodo}|${disp}"
                onclick="toggleDispositivo('${comodo}','${disp}')">
          <div class="left">
            <div class="ico">${ico}</div>
            <div><div class="nome">${disp.replace(/_/g,' ')}</div><div class="st">${st}</div></div>
          </div>
          <div class="acl">${isLigado?'Desligar':'Ligar'}</div>
        </button>`;
    }
    grid.innerHTML+=`
      <div class="card">
        <header>
          <h3>${SVG_ROOM} ${comodo}</h3>
          <span class="count">${Object.keys(dispositivos).length} disp.</span>
        </header>
        ${linhaDevs}
      </div>`;
  }
  if(lastFocusKey){
    const el=grid.querySelector('[data-key="'+lastFocusKey+'"]');
    if(el)el.focus();
  }
}

async function carregarEstadoCasa(auto){
  try{
    const r=await fetch('/api/estado');
    estadoCache=await r.json();
    if(view==='casa'||auto)renderCasa();
  }catch(e){}
}

async function toggleDispositivo(comodo,dispositivo){
  lastFocusKey=comodo+'|'+dispositivo;
  const el=document.activeElement;
  try{
    const r=await fetch('/api/toggle',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({comodo,dispositivo})
    });
    const d=await r.json();
    if(d.status==='erro'){addBot('Erro: '+d.mensagem,true);}
  }catch(e){}
  await carregarEstadoCasa();
  if(el&&el.isConnected)el.focus();
}

function addBot(texto,erro){
  const div=document.createElement('div');
  div.className=erro?'msgerr':'msgbot';
  if(erro){div.textContent=texto;}
  else{div.innerHTML='<div class="who">'+SVG_BOT+' OSAI OS</div>';}
  if(!erro){const corpo=document.createElement('div');corpo.textContent=texto;div.appendChild(corpo);}
  chatBox.appendChild(div);
  chatBox.scrollTop=chatBox.scrollHeight;
}

function addPensando(){
  const div=document.createElement('div');
  div.id='pensando';
  div.className='msginfo pensando';
  div.innerHTML='<i></i><i></i><i></i> processando...';
  chatBox.appendChild(div);
  chatBox.scrollTop=chatBox.scrollHeight;
}

function removePensando(){const p=document.getElementById('pensando');if(p)p.remove();}

document.getElementById('form-chat').addEventListener('submit',async e=>{
  e.preventDefault();
  const texto=inputChat.value.trim();
  if(!texto)return;
  const divU=document.createElement('div');
  divU.className='msguser';
  divU.textContent=texto;
  chatBox.appendChild(divU);
  inputChat.value='';
  chatBox.scrollTop=chatBox.scrollHeight;
  addPensando();
  try{
    const r=await fetch('/api/comando',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({comando:texto})
    });
    const d=await r.json();
    removePensando();
    if(d.tipo==='resposta_web'){addBot(d.resposta);}
    else if(d.tipo==='automacao'){
      addBot(d.mensagem||'Dispositivo atualizado com sucesso!');
      carregarEstadoCasa(true);
    }
    else if(d.tipo==='erro'){addBot('Erro: '+d.detalhe,true);}
    else{addBot('Comando processado.');}
  }catch(err){
    removePensando();
    addBot('Erro de conexao com o servidor.',true);
  }
  setTimeout(()=>inputChat.focus(),80);
});

document.getElementById('tab-casa').addEventListener('click',()=>switchView('casa'));
document.getElementById('tab-chat').addEventListener('click',()=>switchView('chat'));
document.getElementById('btn-refresh').addEventListener('click',()=>carregarEstadoCasa(true));

function getFocusables(){
  return Array.from(document.querySelectorAll('.f')).filter(el=>{
    if(el.id==='input-chat'&&view==='chat')return true;
    const r=el.getBoundingClientRect();
    return r.width>0&&r.height>0;
  });
}
function centerRect(el){
  const r=el.getBoundingClientRect();
  return{x:r.left+r.width/2,y:r.top+r.height/2,r:r};
}
function moveFocus(dir){
  const all=getFocusables();
  if(!all.length)return;
  const cur=document.activeElement;
  if(!all.includes(cur)){
    all[0].focus();
    return;
  }
  const c=centerRect(cur),r=c.r;
  let best=null,bestScore=Infinity;
  for(const el of all){
    if(el===cur)continue;
    const t=centerRect(el),tr=t.r;
    if(dir==='right'&&tr.left<=r.right-8)continue;
    if(dir==='left'&&tr.right>=r.left+8)continue;
    if(dir==='down'&&tr.top<=r.bottom-8)continue;
    if(dir==='up'&&tr.bottom>=r.top+8)continue;
    const distX=Math.abs((tr.left+tr.right)/2-(r.left+r.right)/2);
    const distY=Math.abs((tr.top+tr.bottom)/2-(r.top+r.bottom)/2);
    const score=(dir==='left'||dir==='right')?distX*3+distY*8:distY*3+distX*8;
    if(score<bestScore){bestScore=score;best=el;}
  }
  if(best)best.focus();
}

function osaiArrow(dir){
  if(document.activeElement===inputChat)return false;
  moveFocus(dir);
  return true;
}

document.addEventListener('keydown',e=>{
  const k=e.key;
  if(k==='ArrowUp'||k==='ArrowDown'||k==='ArrowLeft'||k==='ArrowRight'){
    e.preventDefault();
    if(document.activeElement!==inputChat){
      moveFocus(k.replace('Arrow','').toLowerCase());
    }
    return;
  }
  if(k==='Enter'){
    if(view==='casa'){
      const el=document.activeElement;
      if(el&&el.classList.contains('dev')){e.preventDefault();el.click();}
      else if(el&&(el.id==='btn-refresh'||el.classList.contains('tab'))){e.preventDefault();el.click();}
    }
    return;
  }
  if(k==='Escape'&&view==='chat'){switchView('casa');return;}
  if(k==='0'&&view==='casa'){carregarEstadoCasa(true);return;}
});

window.osaiArrow=osaiArrow;
window.osaiToggleTab=function(){
  switchView(view==='casa'?'chat':'casa');
};

setInterval(()=>{if(view==='casa'&&!document.hidden)carregarEstadoCasa(true);},5000);

switchView('casa');
carregarEstadoCasa();
</script>
</body>
</html>
"""

# =====================================================================
# INTERFACE DESKTOP ORIGINAL (com atalho para a versão TV)
# =====================================================================
HTML_DESKTOP = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OSAI OS - Control Center</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body class="bg-gray-950 text-gray-100 min-h-screen flex flex-col md:flex-row font-sans">

        <!-- BARRA LATERAL (SIDEBAR) -->
        <aside class="w-full md:w-64 bg-gray-900 border-b md:border-b-0 md:border-r border-gray-800 flex flex-col justify-between p-4 shrink-0">
            <div>
                <div class="flex items-center gap-3 px-2 py-3 mb-6 border-b border-gray-800">
                    <div class="bg-indigo-600 p-2 rounded-lg text-white">
                        <i class="fa-solid fa-microchip text-xl"></i>
                    </div>
                    <div>
                        <h1 class="font-bold text-lg tracking-wide text-indigo-400">OSAI OS</h1>
                        <span class="text-xs text-emerald-400 font-mono flex items-center gap-1">
                            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Online
                        </span>
                    </div>
                </div>

                <!-- MENU DE NAVEGAÇÃO ENTRE ABAS -->
                <nav class="flex md:flex-col gap-2">
                    <button id="tab-btn-casa" onclick="switchTab('casa')"
                            class="tab-btn flex-1 flex items-center gap-3 px-4 py-3 rounded-xl bg-indigo-600 text-white font-medium transition shadow-lg shadow-indigo-900/20">
                        <i class="fa-solid fa-house"></i>
                        <span>Casa Inteligente</span>
                    </button>
                    <button id="tab-btn-chat" onclick="switchTab('chat')"
                            class="tab-btn flex-1 flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-800/60 hover:bg-gray-800 text-gray-400 hover:text-white font-medium transition">
                        <i class="fa-solid fa-robot"></i>
                        <span>Assistente IA</span>
                    </button>
                    <a href="/tv" target="_blank"
                       class="flex-1 flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-800/60 hover:bg-gray-800 text-gray-400 hover:text-white font-medium transition border border-gray-700/60">
                        <i class="fa-solid fa-tv"></i>
                        <span>Modo TV Box</span>
                    </a>
                </nav>
            </div>

            <div class="hidden md:block p-3 bg-gray-950/50 rounded-xl border border-gray-800/80 text-xs text-gray-500">
                <p><i class="fa-solid fa-network-wired text-indigo-400 mr-1"></i> Host: 192.168.1.105</p>
                <p><i class="fa-solid fa-brain text-indigo-400 mr-1"></i> Engine: Qwen 2.5 (3B)</p>
            </div>
        </aside>

        <!-- CONTEÚDO PRINCIPAL DA APLICAÇÃO -->
        <main class="flex-1 p-4 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">

            <!-- ABA 1: DASHBOARD DA CASA INTELIGENTE -->
            <section id="sec-casa" class="space-y-6">
                <header class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-800">
                    <div>
                        <h2 class="text-2xl font-bold text-white flex items-center gap-2">
                            <i class="fa-solid fa-sliders text-indigo-400"></i> Painel de Controle Residencial
                        </h2>
                        <p class="text-sm text-gray-400">Gerencie todos os cômodos e dispositivos conectados em tempo real.</p>
                    </div>
                    <button onclick="carregarEstadoCasa()" class="self-start sm:self-auto px-4 py-2 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition flex items-center gap-2 border border-gray-700">
                        <i class="fa-solid fa-rotate"></i> Atualizar Mapa
                    </button>
                </header>

                <!-- GRID DINÂMICO DOS CÔMODOS -->
                <div id="grid-comodos" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Cards injetados dinamicamente pelo JavaScript -->
                </div>
            </section>

            <!-- ABA 2: ASSISTENTE / CHATBOT -->
            <section id="sec-chat" class="hidden space-y-4 h-[calc(100vh-6rem)] flex flex-col">
                <header class="pb-2 border-b border-gray-800">
                    <h2 class="text-2xl font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-sparkles text-indigo-400"></i> Assistente OSAI
                    </h2>
                    <p class="text-sm text-gray-400">Pergunte qualquer coisa sobre a casa ou faça pesquisas gerais.</p>
                </header>

                <div id="chat-box" class="flex-1 bg-gray-900 rounded-2xl p-4 overflow-y-auto flex flex-col gap-3 border border-gray-800 shadow-inner">
                    <div class="bg-indigo-950/60 border border-indigo-800/50 rounded-2xl p-4 text-sm max-w-[85%] self-start shadow-sm">
                        <p class="font-semibold text-indigo-300 mb-1"><i class="fa-solid fa-robot mr-1"></i> OSAI OS</p>
                        Olá, Álvaro! Estou pronto. Pode controlar seus dispositivos por voz/texto ou me pedir pesquisas gerais!
                    </div>
                </div>

                <form id="form-comando" class="flex gap-2 pt-2">
                    <input type="text" id="input-comando" placeholder="Ex: 'desligar luz do quarto' ou 'quem foi Gyro Zeppeli?'"
                           class="flex-1 bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 shadow-sm transition">
                    <button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-xl font-medium transition shadow-lg shadow-indigo-900/30 flex items-center gap-2">
                        <span>Enviar</span>
                        <i class="fa-solid fa-paper-plane text-xs"></i>
                    </button>
                </form>
            </section>

        </main>

        <script>
            // LÓGICA DE TROCA DE ABAS NA INTERFACE
            function switchTab(tab) {
                const secCasa = document.getElementById('sec-casa');
                const secChat = document.getElementById('sec-chat');
                const btnCasa = document.getElementById('tab-btn-casa');
                const btnChat = document.getElementById('tab-btn-chat');

                if (tab === 'casa') {
                    secCasa.classList.remove('hidden');
                    secChat.classList.add('hidden');
                    btnCasa.className = "tab-btn flex-1 flex items-center gap-3 px-4 py-3 rounded-xl bg-indigo-600 text-white font-medium transition shadow-lg shadow-indigo-900/20";
                    btnChat.className = "tab-btn flex-1 flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-800/60 hover:bg-gray-800 text-gray-400 hover:text-white font-medium transition";
                    carregarEstadoCasa();
                } else {
                    secCasa.classList.add('hidden');
                    secChat.classList.remove('hidden');
                    btnChat.className = "tab-btn flex-1 flex items-center gap-3 px-4 py-3 rounded-xl bg-indigo-600 text-white font-medium transition shadow-lg shadow-indigo-900/20";
                    btnCasa.className = "tab-btn flex-1 flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-800/60 hover:bg-gray-800 text-gray-400 hover:text-white font-medium transition";
                }
            }

            // CARREGAR E RENDERIZAR MAPA DA CASA
            async function carregarEstadoCasa() {
                try {
                    const res = await fetch('/api/estado');
                    const casa = await res.json();
                    const grid = document.getElementById('grid-comodos');
                    grid.innerHTML = '';

                    for (const [comodo, dispositivos] of Object.entries(casa)) {
                        let dispHTML = '';
                        for (const [disp, dados] of Object.entries(dispositivos)) {
                            const isLigado = dados.estado === 'ligado';
                            const iconClass = dados.tipo === 'light' ? 'fa-lightbulb' : (dados.tipo === 'climate' ? 'fa-snowflake' : 'fa-tv');

                            dispHTML += `
                                <div class="flex items-center justify-between p-3 bg-gray-950/60 rounded-xl border border-gray-800/80">
                                    <div class="flex items-center gap-3">
                                        <div class="w-9 h-9 rounded-lg flex items-center justify-center ${isLigado ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-800 text-gray-500'}">
                                            <i class="fa-solid ${iconClass}"></i>
                                        </div>
                                        <div>
                                            <p class="text-sm font-medium capitalize text-gray-200">${disp.replace(/_/g, ' ')}</p>
                                            <span class="text-xs ${isLigado ? 'text-amber-400' : 'text-gray-500'} font-mono">${dados.estado.toUpperCase()} ${dados.temp ? '- ' + dados.temp + '°C' : ''}</span>
                                        </div>
                                    </div>
                                    <button onclick="toggleDispositivo('${comodo}', '${disp}')"
                                            class="px-3 py-1.5 rounded-lg text-xs font-semibold transition ${isLigado ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}">
                                        ${isLigado ? 'Desligar' : 'Ligar'}
                                    </button>
                                </div>
                            `;
                        }

                        grid.innerHTML += `
                            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-5 shadow-sm hover:border-gray-700 transition flex flex-col gap-4">
                                <div class="flex items-center justify-between border-b border-gray-800/80 pb-3">
                                    <h3 class="font-bold text-lg capitalize text-indigo-300 flex items-center gap-2">
                                        <i class="fa-solid fa-door-open text-sm text-indigo-500"></i> ${comodo}
                                    </h3>
                                    <span class="text-xs bg-indigo-950 text-indigo-400 px-2.5 py-1 rounded-full border border-indigo-800/50">
                                        ${Object.keys(dispositivos).length} disp.
                                    </span>
                                </div>
                                <div class="flex flex-col gap-2.5">
                                    ${dispHTML}
                                </div>
                            </div>
                        `;
                    }
                } catch (e) {
                    console.error("Erro ao carregar estado da casa", e);
                }
            }

            // TOGGLE DIRETO VIA BOTÃO
            async function toggleDispositivo(comodo, dispositivo) {
                await fetch('/api/toggle', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({comodo, dispositivo})
                });
                carregarEstadoCasa();
            }

            // ENVIO DE COMANDOS E PESQUISAS NO CHATBOT
            const form = document.getElementById('form-comando');
            const input = document.getElementById('input-comando');
            const chatBox = document.getElementById('chat-box');

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const texto = input.value.trim();
                if (!texto) return;

                chatBox.innerHTML += `
                    <div class="bg-gray-800 border border-gray-700/60 rounded-2xl p-3 text-sm text-gray-200 self-end max-w-[85%] shadow-sm">
                        ${texto}
                    </div>
                `;
                input.value = '';
                chatBox.scrollTop = chatBox.scrollHeight;

                try {
                    const res = await fetch('/api/comando', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({comando: texto})
                    });
                    const data = await res.json();

                    let msgResposta = "Comando processado.";
                    if (data.tipo === "resposta_web") {
                        msgResposta = data.resposta;
                    } else if (data.tipo === "automacao") {
                        msgResposta = data.mensagem || `Dispositivo ${data.dispositivo || ''} atualizado com sucesso!`;
                        carregarEstadoCasa();
                    } else if (data.tipo === "erro") {
                        msgResposta = `Erro: ${data.detalhe}`;
                    }

                    chatBox.innerHTML += `
                        <div class="bg-indigo-950/60 border border-indigo-800/50 rounded-2xl p-4 text-sm text-gray-100 max-w-[85%] self-start shadow-sm">
                            <p class="font-semibold text-indigo-300 mb-1"><i class="fa-solid fa-robot mr-1"></i> OSAI OS</p>
                            ${msgResposta}
                        </div>
                    `;
                    chatBox.scrollTop = chatBox.scrollHeight;
                } catch (err) {
                    chatBox.innerHTML += `
                        <div class="bg-red-950/60 border border-red-800/50 rounded-2xl p-3 text-sm text-red-200 max-w-[85%] self-start">
                            Erro de conexão com o servidor.
                        </div>
                    `;
                }
            });

            // Carrega estado inicial
            carregarEstadoCasa();
        </script>
    </body>
    </html>
    """

def is_tv_user_agent(user_agent: str) -> bool:
    ua = (user_agent or "").lower()
    marcadores = [
        "android tv", "googletv", "google-tv", "smart tv", "smarttv", "crkey",
        "bravia", "aftb", "aftm", "aftmm", "aftjm", "aftem", "aftg", "aftn",
        "shield", "tv box", "t95", "x96", "h96", "mxq", "kodi", "tv bro",
    ]
    if any(m in ua for m in marcadores):
        return True
    return "android" in ua and "linux" in ua and "tv" in ua

@app.get("/", response_class=HTMLResponse)
def raiz(request: Request):
    ua = request.headers.get("user-agent", "")
    if UI_PADRAO == "tv" or (UI_PADRAO == "auto" and is_tv_user_agent(ua)):
        return HTML_TV
    return HTML_DESKTOP

@app.get("/tv", response_class=HTMLResponse)
def interface_tv():
    return HTML_TV

@app.get("/api/estado")
def get_estado():
    return ESTADO_CASA

@app.post("/api/toggle")
def toggle_dispositivo(req: ToggleRequest):
    if req.comodo in ESTADO_CASA and req.dispositivo in ESTADO_CASA[req.comodo]:
        atual = ESTADO_CASA[req.comodo][req.dispositivo].get("estado", "desligado")
        novo = "desligado" if atual == "ligado" else "ligado"
        ESTADO_CASA[req.comodo][req.dispositivo]["estado"] = novo
        return {"status": "sucesso", "novo_estado": novo}
    return {"status": "erro", "mensagem": "Dispositivo não encontrado."}

@app.post("/api/comando")
def post_comando(req: ComandoRequest):
    texto = req.comando.lower().strip()

    # 1. MAPEAMENTO POR PALAVRAS-CHAVE (ROTEAMENTO RÁPIDO PARA AUTOMAÇÃO)
    VERBOS_AUTOMACAO = ["ligar", "liga", "desligar", "desliga", "apagar", "apaga", "acender", "acende", "mudar", "alterar"]
    VERBOS_CADASTRO = ["adicionar", "adicione", "criar", "crie", "cadastrar", "cadastre"]
    DISPOSITIVOS = ["luz", "lampada", "lâmpada", "ar", "ar-condicionado", "tv", "televisao", "televisão", "led", "sensor"]
    COMODOS = list(ESTADO_CASA.keys()) + ["sala", "quarto", "cozinha", "banheiro", "varanda", "garagem", "fundos"]

    tem_verbo_auto = any(v in texto for v in VERBOS_AUTOMACAO)
    tem_verbo_cad = any(v in texto for v in VERBOS_CADASTRO)
    tem_dispositivo = any(d in texto for d in DISPOSITIVOS)
    tem_comodo = any(c in texto for c in COMODOS)

    # EXECUTA AUTOMAÇÃO SE HOUVER INTENÇÃO DE CASA
    if (tem_verbo_auto or tem_verbo_cad) and (tem_dispositivo or tem_comodo):
        prompt_json = f"""
Você é o controlador de automação do OSAI OS.
Converta o comando do usuário em JSON estruturado para a casa.

REGRAS:
1. Se for para LIGAR, DESLIGAR ou MUDAR:
   {{"acao": "atualizar", "comodo": "nome_do_comodo", "dispositivo": "nome_do_dispositivo", "alteracoes": {{"estado": "ligado/desligado"}}}}

2. Se for para ADICIONAR ou CRIAR novo cômodo/dispositivo:
   {{"acao": "adicionar", "comodo": "nome_do_comodo", "dispositivo": "nome_do_dispositivo", "dados": {{"tipo": "light/climate/tv/sensor", "estado": "desligado"}}}}

Estado Atual da Casa: {ESTADO_CASA}
Comando: "{req.comando}"

Responda APENAS o JSON puro:
"""
        try:
            resp = client.chat(model=MODELO_LLM, messages=[{'role': 'user', 'content': prompt_json}])
            content = resp['message']['content'].strip()
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            parsed = json.loads(content.strip())

            if parsed.get("acao") == "atualizar":
                comodo = parsed.get("comodo")
                disp = parsed.get("dispositivo")
                alts = parsed.get("alteracoes", {})
                if comodo in ESTADO_CASA and disp in ESTADO_CASA[comodo]:
                    ESTADO_CASA[comodo][disp].update(alts)
                    return {"tipo": "automacao", "status": "sucesso", "mensagem": f"Dispositivo '{disp}' em '{comodo}' atualizado!", "dados_casa": ESTADO_CASA}
                return {"tipo": "resposta_web", "resposta": f"Não encontrei o dispositivo '{disp}' no cômodo '{comodo}'."}

            elif parsed.get("acao") == "adicionar":
                comodo = parsed.get("comodo")
                disp = parsed.get("dispositivo")
                dados = parsed.get("dados", {"tipo": "light", "estado": "desligado"})
                if comodo not in ESTADO_CASA:
                    ESTADO_CASA[comodo] = {}
                ESTADO_CASA[comodo][disp] = dados
                return {"tipo": "automacao", "status": "sucesso", "mensagem": f"Cadastrado '{disp}' em '{comodo}'.", "dados_casa": ESTADO_CASA}
        except Exception as e:
            return {"tipo": "erro", "detalhe": f"Erro no processamento da automação: {str(e)}"}

    # 2. PESQUISA WEB EXPLICÍTA (SE O USUÁRIO PEDIR PESQUISA ONLINE)
    PALAVRAS_PESQUISA = ["pesquise", "pesquisar", "busque", "procurar na web", "notícias de", "noticias de"]
    e_pesquisa_web = any(p in texto for p in PALAVRAS_PESQUISA)

    if e_pesquisa_web:
        snippets = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(req.comando, max_results=3))
                for r in results:
                    b = r.get('body', '').strip()
                    if b and len(b) > 20: snippets.append(b)
        except Exception:
            pass

        if snippets:
            contexto = "\n".join(snippets)
            prompt_rag = f"Com base nas informações abaixo, responda em português à pergunta: {req.comando}\n\nInformações:\n{contexto}"
            resp = client.chat(model=MODELO_LLM, messages=[{'role': 'user', 'content': prompt_rag}])
            return {"tipo": "resposta_web", "resposta": resp['message']['content'].strip()}

    # 3. CONHECIMENTO GERAL / CHAT DIRETO (RESPOSTA FACTUAL COM TEMPERATURA ZERO)
    try:
        messages = [
            {
                'role': 'system',
                'content': 'Você é um assistente factual, preciso e direto. Responda apenas com fatos históricos, científicos e de cultura pop reais e corretos em português. Não invente detalhes.'
            },
            {
                'role': 'user',
                'content': req.comando
            }
        ]

        # Chamada forcando temperatura 0.0 para zerar a alucinação
        resp_chat = client.chat(
            model=MODELO_LLM,
            messages=messages,
            options={'temperature': 0.0}
        )
        return {"tipo": "resposta_web", "resposta": resp_chat['message']['content'].strip()}
    except Exception as e:
        return {"tipo": "erro", "detalhe": "Erro de comunicação com o Ollama."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
