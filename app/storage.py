import os
import uuid
from pathlib import Path

import boto3
from flask import current_app, send_file
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "png", "jpg", "jpeg", "gif", "mp4", "webm"}


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def save_upload(file, namespace):
    original = secure_filename(file.filename or "")
    if not original or _extension(original) not in ALLOWED_EXTENSIONS:
        raise ValueError("File type is not allowed.")
    key = f"{namespace}/{uuid.uuid4().hex}.{_extension(original)}"
    content_type = file.mimetype or "application/octet-stream"
    if current_app.config["STORAGE_BACKEND"] == "s3":
        bucket = current_app.config["S3_BUCKET"]
        if not bucket:
            raise RuntimeError("S3_BUCKET must be configured for S3 storage.")
        client = boto3.client("s3", region_name=current_app.config["AWS_REGION"])
        file.stream.seek(0)
        client.upload_fileobj(file.stream, bucket, key, ExtraArgs={"ContentType": content_type, "ServerSideEncryption": "AES256"})
    else:
        path = Path(current_app.config["UPLOAD_FOLDER"]) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        file.save(path)
    return key, original, content_type


def download_response(key, download_name):
    if current_app.config["STORAGE_BACKEND"] == "s3":
        client = boto3.client("s3", region_name=current_app.config["AWS_REGION"])
        signed = client.generate_presigned_url("get_object", Params={"Bucket": current_app.config["S3_BUCKET"], "Key": key, "ResponseContentDisposition": f'attachment; filename="{secure_filename(download_name)}"'}, ExpiresIn=180)
        from flask import redirect
        return redirect(signed)
    path = Path(current_app.config["UPLOAD_FOLDER"]) / key
    return send_file(path, as_attachment=True, download_name=secure_filename(download_name))
