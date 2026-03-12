from flask import Flask, request, jsonify, send_file, render_template
from drive_service import get_drive_service
import io

app = Flask(__name__)

PASTAS_EMPREENDIMENTOS = {
    "empreendimento.a": "1hBgBLAKp3WldLthPyJIRySelEHaGsbEE",
    "empreendimento.b": "1uOYSq4W38BLLdTPgMr5om4HoGzgSdkZQ"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/enviar", methods=["POST"])
def enviar():
    nome = request.form.get("nome")
    cpf = request.form.get("cpf")
    empreendimento = request.form.get("empreendimento")

    if not nome or not cpf or not empreendimento:
        return jsonify({"success": False, "message": "Dados incompletos"}), 400

    if empreendimento not in PASTAS_EMPREENDIMENTOS:
        return jsonify({"success": False, "message": "Empreendimento inválido"}), 400

    cpf_limpo = cpf.replace(".", "").replace("-", "")
    nome_arquivo = f"{cpf_limpo}.pdf"

    pasta_id = PASTAS_EMPREENDIMENTOS[empreendimento]

    service = get_drive_service()

    query = (
        f"name = '{nome_arquivo}' and "
        f"'{pasta_id}' in parents and "
        "mimeType = 'application/pdf' and trashed = false"
    )

    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])

    if not files:
        return jsonify({"success": False, "message": "PDF não encontrado"}), 404

    file_id = files[0]["id"]

    request_drive = service.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()

    from googleapiclient.http import MediaIoBaseDownload
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

if __name__ == "__main__":
    print("Servidor Flask iniciado 🚀")
    app.run(debug=False)
