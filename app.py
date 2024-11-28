from flask import Flask, render_template, request, redirect, url_for
import os
import subprocess
import requests

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "converted"
ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg", "flac"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# Certifique-se de que as pastas existam
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_audio(input_path, output_path):
    """Converte um arquivo de áudio para uma taxa de amostragem de 8000 Hz."""
    try:
        command = [
            "ffmpeg", "-i", input_path, 
            "-ar", "8000", "-ac", "1", output_path, 
            "-y"
        ]
        result = subprocess.run(command, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        return True, f"Arquivo convertido com sucesso: {output_path}"
    except subprocess.CalledProcessError as e:
        return False, f"Erro na conversão: {e.stderr}"

@app.route("/")
def index():
    """Renderiza a página inicial."""
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    """Recebe um arquivo de upload ou URL e converte o áudio."""
    if "audio_file" in request.files:
        audio_file = request.files["audio_file"]
        if audio_file.filename == "":
            return render_template("result.html", success=False, message="Nenhum arquivo selecionado.", file=None)
        
        if not allowed_file(audio_file.filename):
            return render_template("result.html", success=False, message="Formato de arquivo não suportado.", file=None)

        input_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
        audio_file.save(input_path)
        output_path = os.path.join(OUTPUT_FOLDER, f"converted_{audio_file.filename}")
        
        success, message = convert_audio(input_path, output_path)

        # Apagar o arquivo de upload após a conversão
        if success:
            try:
                os.remove(input_path)
            except Exception as e:
                message += f" (Erro ao apagar o arquivo de upload: {str(e)})"

        return render_template("result.html", success=success, message=message, file=output_path if success else None)

    elif "audio_url" in request.form:
        audio_url = request.form["audio_url"]
        if audio_url.strip() == "":
            return render_template("result.html", success=False, message="Nenhuma URL fornecida.", file=None)
        
        try:
            response = requests.get(audio_url, stream=True)
            if response.status_code == 200:
                filename = audio_url.split("/")[-1]
                input_path = os.path.join(UPLOAD_FOLDER, filename)
                with open(input_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                output_path = os.path.join(OUTPUT_FOLDER, f"converted_{filename}")
                success, message = convert_audio(input_path, output_path)

                # Apagar o arquivo de upload após a conversão
                if success:
                    try:
                        os.remove(input_path)
                    except Exception as e:
                        message += f" (Erro ao apagar o arquivo de upload: {str(e)})"

                return render_template("result.html", success=success, message=message, file=output_path if success else None)
            else:
                return render_template("result.html", success=False, message="Falha ao baixar o arquivo da URL.", file=None)
        except Exception as e:
            return render_template("result.html", success=False, message=f"Erro ao processar a URL: {str(e)}", file=None)

    else:
        return render_template("result.html", success=False, message="Nenhuma ação válida foi recebida.", file=None)

if __name__ == "__main__":
    app.run(debug=True)
