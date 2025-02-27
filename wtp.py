import os
from dotenv import load_dotenv
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq

# Carregar variáveis de ambiente
load_dotenv()

# Configurações da API Groq
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY não encontrada nas variáveis de ambiente")

# Configurações da API Twilio
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
USER_WHATSAPP_NUMBER = os.getenv('USER_WHATSAPP_NUMBER')

# Inicializa clientes Twilio e Groq
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
#modelo = "gemma2-9b-it"
modelo = "llama-3.3-70b-versatile"
modelo = "whisper-large-v3-turbo"# Criar aplicativo Flask
app = Flask(__name__)

# Histórico da conversa (mantém contexto)s
user_sessions = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    """Recebe mensagens do WhatsApp e responde como Gandalf."""
    incoming_msg = request.values.get("Body", "").strip()
    sender_number = request.values.get("From", "")

    # Permitir apenas seu número de WhatsApp
    if sender_number != f"whatsapp:{USER_WHATSAPP_NUMBER}":
        return "Acesso negado", 403

    print(f"Mensagem recebida de {sender_number}: {incoming_msg}")

    if not incoming_msg:
        return "Nenhuma mensagem recebida", 400

    # Criar ou recuperar histórico da conversa
    if sender_number not in user_sessions:
        user_sessions[sender_number] = [
            {"role": "system", "content": f"Você é Gandalf, o Cinzento, o grande mago da Terra Média. Fale sempre como ele, de forma sábia, "
             "mística e majestosa. Responda como um mentor épico."}
        ]
    
    # Adicionar nova mensagem ao histórico
    user_sessions[sender_number].append({"role": "user", "content": incoming_msg})

    # Chamar IA Groq para gerar resposta
    try:
        response = groq_client.chat.completions.create(
            model=modelo,
            messages=user_sessions[sender_number],
            temperature=0.8,
            max_tokens=200
        )

        resposta_ia = response.choices[0].message.content

        # Adicionar resposta ao histórico
        user_sessions[sender_number].append({"role": "assistant", "content": resposta_ia})

    except Exception as e:
        resposta_ia = f"Erro ao processar mensagem: {str(e)}"

    # Criar resposta para WhatsApp
    resp = MessagingResponse()
    resp.message(resposta_ia)

    return str(resp)


'''para rodar em producao'''
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)


'''para rodar local'''
#if __name__ == "__main__":
#    app.run(port=5000, debug=True)
