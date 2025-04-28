import os
import requests
import openai
from flask import Flask, request

app = Flask(__name__)

# ─── 1) Variables de entorno ─────────────────────────────────
VERIFY_TOKEN      = os.environ["VERIFY_TOKEN"]
PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
openai.api_key    = os.environ["OPENAI_API_KEY"]

GRAPH_API_URL = "https://graph.facebook.com/v16.0"

# Tu prompt de sistema
SYSTEM_PROMPT = (
    "Eres Pablo un asesor espiritual online, un asesor pastoral inspirado en el apóstol Pablo. "
    "Respondes con un versículo apropiado, un breve consejo bíblico y una oración final de no más de dos líneas. "
    "Si es pertinente, mencionas cómo contactar a la iglesia o un próximo servicio. "
    "Usa lenguaje cálido, apasionado y desafiante a la fe, sin listas ni repeticiones."
)

# ─── 2) GET / — Verificación de Meta ───────────────────────────────
@app.route("/", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# ─── 3) POST / — Webhook de mensajes y callbacks ──────────────────
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data["entry"]:
            for msg_event in entry.get("messaging", []):
                sender_id = msg_event["sender"]["id"]

                # — Mensaje de texto —
                text = msg_event.get("message", {}).get("text")
                if text:
                    # ─── 4) Llamada a OpenAI con tu SYSTEM_PROMPT ─────────
                    resp = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user",   "content": text}
                        ],
                        temperature=0.7,
                        max_tokens=300
                    )
                    answer = resp.choices[0].message.content
                    send_message(sender_id, answer)

    return "EVENT_RECEIVED", 200

# ─── 5) Función auxiliar para enviar el mensaje ────────────────────
def send_message(recipient_id, text):
    url     = f"{GRAPH_API_URL}/me/messages"
    params  = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    payload = {
        "messaging_type": "RESPONSE",
        "recipient":      {"id": recipient_id},
        "message":        {"text": text}
    }
    requests.post(url, params=params, json=payload, headers=headers)

# ─── 6) Run ────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
