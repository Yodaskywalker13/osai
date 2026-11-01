import requests
import time

URL_COMANDO = "http://localhost:8000/api/comando"
URL_STATUS = "http://localhost:8000/api/status"

bateria_testes = [
    # 1. Automações de luz e clima
    "liga a luz da sala",
    "ajusta a temperatura do ar condicionado da sala para 20 graus",
    "desliga a luz da sala",
    
    # 2. Consultas de status direto
    "status",
    "como está a casa",
    
    # 3. Adição dinâmica de hardware lógico
    "adicione um sensor de presença no corredor",
    
    # 4. Roteamento web
    "Qual é a distância da Terra até a Lua?",
    
    # 5. Estresse e entradas caóticas
    "abcdefghijklmnopqrstuvwxyz",
    "faz o inversor solar fazer café"
]

print("==================================================")
print("  OSAI OS - Bateria Avançada de Testes (Etapa 2)  ")
print("==================================================")

# Testa primeiro o endpoint GET puro de status
print("\n[TESTE GET] Consultando /api/status diretamente...")
try:
    resp_status = requests.get(URL_STATUS, timeout=5)
    print(f"Status HTTP: {resp_status.status_code}")
    print(f"Resposta: {resp_status.json()}")
except Exception as e:
    print(f"Erro no GET status: {e}")

print("\n--- Iniciando testes de POST (Comandos e IA) ---")
for i, teste in enumerate(bateria_testes, 1):
    print(f"\n[{i}] Enviando: '{teste}'")
    try:
        inicio = time.time()
        resposta = requests.post(URL_COMANDO, json={"texto": teste}, timeout=30)
        duracao = time.time() - inicio
        
        print(f"Status HTTP: {resposta.status_code} (Tempo: {duracao:.2f}s)")
        print(f"Resposta: {resposta.json()}")
    except Exception as e:
        print(f"Erro no teste: {e}")
    time.sleep(0.5)

print("\n==================================================")
print("  Fim da Bateria Avançada de Testes               ")
print("==================================================")