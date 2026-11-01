import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from ollama import Client
from duckduckgo_search import DDGS

app = FastAPI(title="OSAI OS Core")

# Conexão com o Ollama hospedado no sistema operacional (host)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
client = Client(host=OLLAMA_HOST)

# Modelo LLM padrão otimizado para raciocínio e português
MODELO_LLM = 'qwen2.5:3b'

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

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    return """
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