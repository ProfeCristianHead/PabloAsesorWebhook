import os
import requests
import openai
from flask import Flask, request

# Inicializa Flask
app = Flask(__name__)

# 1️⃣ Carga las variables de entorno
env = os.environ\VERIFY_TOKEN = env.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = env.get("PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = env.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 2️⃣ GET para verificación de webhook
@app.route("/", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# 3️⃣ POST para recibir eventos (mensajes, reacciones, etc.)
@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.get_json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                # Procesa solo mensajes de texto
                message = event.get("message", {})
                text = message.get("text")
                if text:
                    # Llamada a OpenAI GPT-4
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Eres un asesor espiritual cristiano, amable y sabio."},
                            {"role": "user", "content": text}
                        ]
                    )
                    answer = response.choices[0].message.content

                    # Envía la respuesta de vuelta al usuario
                    send_message(sender_id, answer)

        return "EVENT_RECEIVED", 200

    return "No page object", 404

# 4️⃣ Función auxiliar para enviar mensajes
def send_message(recipient_id: str, text: str):
    url = "https://graph.facebook.com/v16.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {
        "messaging_type": "RESPONSE",
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, params=params, json=payload, headers=headers)

# Punto de entrada\if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
