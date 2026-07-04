"""Helper per Google Cloud Storage — upload, delete e signed URL."""

from datetime import timedelta
from google.cloud import storage
from flask import current_app

SIGNED_URL_EXPIRATION = timedelta(minutes=5)


def _get_bucket():
    client = storage.Client()
    return client.bucket(current_app.config['GCS_BUCKET_NAME'])


def upload_file(file, destination_name):
    """Carica un file nel bucket GCS e restituisce un signed URL."""
    bucket = _get_bucket()
    blob = bucket.blob(f"uploads/{destination_name}")
    blob.upload_from_file(file, content_type=file.content_type)
    return blob.generate_signed_url(expiration=SIGNED_URL_EXPIRATION)


def delete_file(filename):
    """Elimina un file dal bucket GCS (ignora se non esiste)."""
    bucket = _get_bucket()
    blob = bucket.blob(f"uploads/{filename}")
    if blob.exists():
        blob.delete()


def get_file_url(filename):
    """Restituisce un signed URL per un file nel bucket."""
    bucket = _get_bucket()
    blob = bucket.blob(f"uploads/{filename}")
    return blob.generate_signed_url(expiration=SIGNED_URL_EXPIRATION)
