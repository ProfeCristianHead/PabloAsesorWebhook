import os
import requests
import openai
from flask import Flask, request

app = Flask(__name__)

# Carga las variables de entorno
VERIFY_TOKEN     = os.environ.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
OPENAI_API_KEY   = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# 👉 1) GET para verificación del webhook
@app.route('/', methods=['GET'])
def verify():
    mode      = request.args.get('hub.mode')
    token     = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Error de verificación', 403

# 👉 2) POST para recibir mensajes de Facebook/Instagram/WhatsApp
@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    # Asegúrate de que el objeto sea "page" (para páginas)
    if data.get("object") == "page":
        for entry in data.get('entry', []):
            for msg_event in entry.get('messaging', []):
                sender_id = msg_event['sender']['id']
                # Solo procesamos si hay un texto
                if 'message' in msg_event and 'text' in msg_event['message']:
                    user_text = msg_event['message']['text']

                    # 👉 3) Llamada a OpenAI GPT-4
                    resp = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system",
                             "content": "Eres un asesor espiritual cristiano, amable y sabio."},
                            {"role": "user", "content": user_text}
                        ]
                    )
                    answer = resp.choices[0].message.content

                    # 👉 4) Envía la respuesta de vuelta al usuario
                    send_message(sender_id, answer)

    return 'EVENT_RECEIVED', 200

def send_message(recipient_id, text):
    url = "https://graph.facebook.com/v16.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    payload = {
        "messaging_type": "RESPONSE",
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    requests.post(url, params=params, json=payload, headers=headers)

if __name__ == '__main__':
    # Mismo puerto que configuraste en Render
    app.run(host='0.0.0.0', port=10000)

