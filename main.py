import os
import openai
import requests
from flask import Flask, request

app = Flask(__name__)

# 1️⃣ Variables de entorno (defínelas en Render tal y como hablamos)
VERIFY_TOKEN      = os.environ['VERIFY_TOKEN']
PAGE_ACCESS_TOKEN = os.environ['PAGE_ACCESS_TOKEN']
openai.api_key    = os.environ['OPENAI_API_KEY']

GRAPH_API_URL     = 'https://graph.facebook.com/v12.0'

# 2️⃣ GET / – Verifica el webhook con Meta
@app.route('/', methods=['GET'])
def verify():
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
    return 'Forbidden', 403

# 3️⃣ POST / – Recibe todos los callbacks
@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()

    for entry in data.get('entry', []):

        # —— A) Mensajes de Messenger ——
        for msg in entry.get('messaging', []):
            if 'message' in msg and 'text' in msg['message']:
                user_id = msg['sender']['id']
                text    = msg['message']['text']

                # Genera respuesta con GPT-4
                chat = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role":"system","content":"Eres Pablo Asesor Espiritual Online, amable y breve."},
                        {"role":"user","content": text}
                    ]
                )
                reply = chat.choices[0].message.content

                # Envía la respuesta al usuario
                payload = {
                    "recipient": {"id": user_id},
                    "message":   {"text": reply}
                }
                requests.post(
                    f"{GRAPH_API_URL}/me/messages",
                    params={"access_token": PAGE_ACCESS_TOKEN},
                    json=payload
                )

        # —— B) Comentarios en posts de la página ——
        for change in entry.get('changes', []):
            if change['field'] == 'feed':
                val          = change['value']
                comment_id   = val['comment_id']
                comment_text = val.get('message', '')
                commenter_id = val.get('from', {}).get('id')

                # Genera respuesta con GPT-4
                chat = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role":"system","content":"Eres Pablo Asesor Espiritual Online. Responde como comentario."},
                        {"role":"user","content": comment_text}
                    ]
                )
                reply = chat.choices[0].message.content

                # Publica la respuesta como comentario
                requests.post(
                    f"{GRAPH_API_URL}/{comment_id}/comments",
                    params={"access_token": PAGE_ACCESS_TOKEN},
                    json={"message": reply}
                )

        # —— C) Reacciones a mensajes/posts ——
        # Actualmente Meta solo envía 'message_reactions' dentro de messaging[],
        # así que podrías manejarlo ahí mismo. Si recibes cambios de tipo 'message_reactions'
        # aparecerán en entry.get('changes') también:
        for change in entry.get('changes', []):
            if change['field'] == 'message_reactions':
                val = change['value']
                # val tendrá algo como: { "reaction_type": "...", "sender_id": "...", ... }
                # Decide si contestas con un mensaje en el chat o con un comentario.
                # Por simplicidad, aquí enviamos un mensaje de texto al chat original:
                sender = val.get('sender_id')
                reaction = val.get('reaction_type')
                reply = f"¡Gracias por tu reacción «{reaction}»!"
                requests.post(
                    f"{GRAPH_API_URL}/me/messages",
                    params={"access_token": PAGE_ACCESS_TOKEN},
                    json={"recipient": {"id": sender}, "message": {"text": reply}}
                )

    return 'EVENT_RECEIVED', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

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

