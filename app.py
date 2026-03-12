from flask import Flask, request, jsonify
import subprocess
import uuid

app = Flask(__name__)

@app.route("/download")
def download():

    url = request.args.get("url")
    filename = f"{uuid.uuid4()}.mp4"

    subprocess.run([
        "yt-dlp",
        "-f", "mp4",
        "-o", filename,
        url
    ])

    return jsonify({
        "file": filename
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
