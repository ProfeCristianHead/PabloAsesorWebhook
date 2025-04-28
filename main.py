from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def verify():
    verify_token = 'tu-token-verificacion'  # 👈 Aquí después cambias "tu-token-verificacion" por el token real que pongas en Meta
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == verify_token:
            return challenge, 200
        else:
            return 'Error de verificación', 403
    return 'Hola desde Pablo Asesor Espiritual Online!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
