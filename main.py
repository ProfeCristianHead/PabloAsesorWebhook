import os
import requests
import openai
from flask import Flask, request

app = Flask(__name__)

# 1) Variables de entorno (defínelas en Render tal y como hablamos)
VERIFY_TOKEN      = os.environ["VERIFY_TOKEN"]
PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
OPENAI_API_KEY    = os.environ["OPENAI_API_KEY"]
openai.api_key    = OPENAI_API_KEY

# 2) GET  /  – Verificación del webhook con Meta
@app.route("/", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# 3) POST /  – Recibe todos los callbacks
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for msg_event in entry.get("messaging", []):
                sender_id = msg_event["sender"]["id"]

                # — Mensaje de texto —
                if "message" in msg_event and "text" in msg_event["message"]:
                    user_text = msg_event["message"]["text"]

                    # 4) Llamada a OpenAI GPT-4
                    resp = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Eres un asesor espiritual cristiano, amable y sabio."},
                            {"role": "user", "content": user_text}
                        ]
                    )
                    answer = resp.choices[0].message.content

                    # 5) Envía la respuesta de vuelta al usuario
                    send_message(sender_id, answer)

                # — Reacción a mensaje —
                if "reaction" in msg_event:
                    reaction = msg_event["reaction"]["reaction"]
                    send_message(sender_id, f"¡Gracias por tu reacción {reaction}!")

                # — Feed (comentarios/loves en la página) —
                # Aquí podrías capturar msg_event["feed"] si lo configuras
                # y responder, por ejemplo:
                # if "feed" in msg_event:
                #     send_message(sender_id, "¡Gracias por comentar en la página!")

    return "EVENT_RECEIVED", 200

def send_message(recipient_id: str, text: str):
    url = "https://graph.facebook.com/v16.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    payload = {
        "messaging_type": "RESPONSE",
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    requests.post(url, params=params, json=payload, headers=headers)

if __name__ == "__main__":
    # El puerto lo lee de la variable de entorno PORT o usa 10000 por defecto
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
