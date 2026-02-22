import os
from google.cloud import storage

GCP_DB_BUCKET_NAME = os.environ.get("GCP_DB_BUCKET_NAME")

def get_db_bucket():
    if not GCP_DB_BUCKET_NAME:
        return None
    client = storage.Client()
    return client.bucket(GCP_DB_BUCKET_NAME)

def upload_db_to_gcp(db_path: str = "photos.db"):
    """
    Uploads the local SQLite database file to the private GCP bucket.
    """
    bucket = get_db_bucket()
    if not bucket:
        print(f"Skipping DB upload to GCP. GCP_DB_BUCKET_NAME is not set.")
        return False
        
    try:
        blob = bucket.blob("photos.db")
        blob.upload_from_filename(db_path)
        print(f"Successfully uploaded {db_path} to GCP bucket {GCP_DB_BUCKET_NAME}.")
        return True
    except Exception as e:
        print(f"Failed to upload DB to GCP: {e}")
        return False

def download_db_from_gcp(dest_path: str = "photos.db"):
    """
    Downloads the SQLite database file from the private GCP bucket.
    Should be called during app startup in production.
    """
    bucket = get_db_bucket()
    if not bucket:
        print(f"Skipping DB download from GCP. GCP_DB_BUCKET_NAME is not set.")
        return False
        
    try:
        blob = bucket.blob("photos.db")
        if not blob.exists():
             print(f"photos.db does not exist in GCP bucket {GCP_DB_BUCKET_NAME}. A new one will be created.")
             return False
             
        blob.download_to_filename(dest_path)
        print(f"Successfully downloaded photos.db from GCP bucket {GCP_DB_BUCKET_NAME} to {dest_path}.")
        return True
    except Exception as e:
        print(f"Failed to download DB from GCP: {e}")
        return False
