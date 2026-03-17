from flask import Flask, request, jsonify, send_file, render_template
from drive_service import get_drive_service
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import re
import requests
import unicodedata

app = Flask(__name__)

# Limite global básico + limite forte na rota sensível
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

PASTAS_EMPREENDIMENTOS = {
    "empreendimento.a": "1hBgBLAKp3WldLthPyJIRySelEHaGsbEE",
    "empreendimento.b": "1uOYSq4W38BLLdTPgMr5om4HoGzgSdkZQ"
}

TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY")
TURNSTILE_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def normalizar_nome(nome: str) -> str:
    nome = (nome or "").strip()
    nome = unicodedata.normalize("NFD", nome)
    nome = "".join(c for c in nome if unicodedata.category(c) != "Mn")
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome.upper()


def normalizar_numero(numero: str) -> str:
    return re.sub(r"\D", "", numero or "")


def normalizar_letra(letra: str) -> str:
    letra = (letra or "").strip().upper()
    letra = re.sub(r"[^A-Z]", "", letra)
    return letra[:1]


def validar_turnstile(token: str, remote_ip: str | None = None) -> bool:
    if not TURNSTILE_SECRET_KEY:
        raise RuntimeError("Variável TURNSTILE_SECRET_KEY não configurada.")

    if not token:
        return False

    data = {
        "secret": TURNSTILE_SECRET_KEY,
        "response": token
    }

    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        response = requests.post(
            TURNSTILE_SITEVERIFY_URL,
            data=data,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return bool(result.get("success"))
    except requests.RequestException:
        return False


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://challenges.cloudflare.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://wa.me; "
        "connect-src 'self'; "
        "frame-src https://challenges.cloudflare.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response


@app.route("/")
def index():
    turnstile_site_key = os.environ.get("TURNSTILE_SITE_KEY", "")
    return render_template("index.html", turnstile_site_key=turnstile_site_key)


@app.route("/enviar", methods=["POST"])
@limiter.limit("5 per minute")
def enviar():
    nome = normalizar_nome(request.form.get("nome") or "")
    numero = normalizar_numero(request.form.get("numero") or "")
    letra = normalizar_letra(request.form.get("letra") or "")
    empreendimento = request.form.get("empreendimento") or ""
    turnstile_token = request.form.get("cf-turnstile-response") or ""

    if not nome or not numero or not empreendimento:
        return jsonify({"success": False, "message": "Dados incompletos."}), 400

    if empreendimento not in PASTAS_EMPREENDIMENTOS:
        return jsonify({"success": False, "message": "Empreendimento inválido."}), 400

    # Validação anti-bot obrigatória
    if not validar_turnstile(turnstile_token, request.remote_addr):
        return jsonify({"success": False, "message": "Falha na verificação de segurança. Tente novamente."}), 403

    prefixo = f"{numero}{letra}"
    nome_arquivo = f"{prefixo}_{nome}.pdf"
    pasta_id = PASTAS_EMPREENDIMENTOS[empreendimento]

    try:
        service = get_drive_service()

        query = (
            f"name = '{nome_arquivo}' and "
            f"'{pasta_id}' in parents and "
            "mimeType = 'application/pdf' and trashed = false"
        )

        results = service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            pageSize=1
        ).execute()

        files = results.get("files", [])

        if not files:
            return jsonify({"success": False, "message": "Documento não encontrado."}), 404

        file_id = files[0]["id"]
        request_drive = service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request_drive)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        file_stream.seek(0)

        return send_file(
            file_stream,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=nome_arquivo
        )

    except Exception:
        return jsonify({"success": False, "message": "Erro interno ao processar a solicitação."}), 500


if __name__ == "__main__":
    print("Servidor Flask iniciado 🚀")
    app.run(debug=False)