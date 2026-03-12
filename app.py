from flask import Flask, request, jsonify
import subprocess
import uuid
import boto3
import os

app = Flask(__name__)

R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET")

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY
)

PUBLIC_URL = "https://pub-953880307ee54af28bbea36d6f00a07c.r2.dev"


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

    s3.upload_file(filename, R2_BUCKET, filename)

    public_url = f"{PUBLIC_URL}/{filename}"

    os.remove(filename)

    return jsonify({
        "video_url": public_url
    })


@app.route("/process", methods=["POST"])
def process_video():

    data = request.json
    video_url = data.get("video_url")

    watermark_width = data.get("watermark_width", 0.22)
    opacity = data.get("opacity", 0.6)
    position = data.get("position", "top-right")
    margin = data.get("margin", 30)

    # calcular posición
    if position == "top-right":
        overlay_position = f"W-w-{margin}:{margin}"
    elif position == "top-left":
        overlay_position = f"{margin}:{margin}"
    elif position == "bottom-right":
        overlay_position = f"W-w-{margin}:H-h-{margin}"
    elif position == "bottom-left":
        overlay_position = f"{margin}:H-h-{margin}"
    else:
        overlay_position = f"W-w-{margin}:{margin}"

    # crear filtro dinámico
    filter_complex = f"[1][0]scale2ref=w=iw*{watermark_width}:h=ow/mdar[wm][vid];[wm]format=rgba,colorchannelmixer=aa={opacity}[wm2];[vid][wm2]overlay={overlay_position}"

    input_file = f"{uuid.uuid4()}.mp4"
    output_file = f"processed-{uuid.uuid4()}.mp4"

    # descargar video desde R2
    subprocess.run(["curl", "-L", video_url, "-o", input_file])

    # aplicar watermark
    subprocess.run([
        "ffmpeg",
        "-i", input_file,
        "-i", "Watermark-escapexperts.png",
        "-filter_complex", filter_complex,
        "-codec:a", "copy",
        output_file
    ])

    # subir a R2
    s3.upload_file(output_file, R2_BUCKET, output_file)

    public_url = f"{PUBLIC_URL}/{output_file}"

    os.remove(input_file)
    os.remove(output_file)

    return jsonify({
        "deliverie_url": public_url
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
