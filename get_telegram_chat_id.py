import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("ERRO: TELEGRAM_BOT_TOKEN no encontrado no .env")
    exit()

print("Buscando atualizacoes do bot (envie um 'Oi' para o bot no Telegram antes)...")
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
try:
    response = requests.get(url).json()
    if response.get("ok") and response.get("result"):
        # Pega a ultima mensagem recebida
        last_message = response["result"][-1]
        chat_id = last_message["message"]["chat"]["id"]
        first_name = last_message["message"]["chat"].get("first_name", "Usuario")
        print(f"\n✅ SUCESSO! Encontrado Chat ID de {first_name}: {chat_id}")
        print(f"\n👉 Copie esse nmero ({chat_id}) e cole como TELEGRAM_CHAT_ID no seu arquivo .env")
    else:
        print("\nNenhuma mensagem recente encontrada.")
        print("Va no seu Telegram, mande qualquer mensagem para o @Obsidian_Py_Bot e rode este script de novo.")
except Exception as e:
    print(f"Erro ao acessar API do Telegram: {e}")
