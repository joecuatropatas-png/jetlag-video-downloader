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

@app.route("/download")
def download():

    url = request.args.get("url")
    filename = f"{uuid.uuid4()}.mp4"

    subprocess.run([
    "yt-dlp",
    "-f", "best",
    "-o", filename,
    "--no-playlist",
    url
])

if not os.path.exists(filename):
    return jsonify({
        "error": "video download failed"
    }), 500
    
    s3.upload_file(filename, R2_BUCKET, filename)

    public_url = f"https://pub-953880307ee54af28bbea36d6f00a07c.r2.dev/{filename}"

    os.remove(filename)

    return jsonify({
        "video_url": public_url
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
