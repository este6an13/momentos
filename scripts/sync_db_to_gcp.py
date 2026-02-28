import os
import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Ensure environment variables are loaded before anything else
load_dotenv()

import urllib.request
import urllib.parse
import urllib.error
import ssl

from app.gcp_utils import upload_db_to_gcp, download_db_from_gcp

def main():
    print("--- GCP Database Sync Tool ---")
    print("1. Upload local photos.db to GCP")
    print("2. Download photos.db from GCP to local")
    print("3. Exit")
    
    choice = input("Enter your choice (1/2/3): ")
    
    if choice == '1':
        print("\nUploading...")
        success = upload_db_to_gcp("photos.db")
        if success:
            production_url = os.environ.get("PRODUCTION_URL")
            webhook_token = os.environ.get("WEBHOOK_TOKEN")
            if production_url and webhook_token:
                print(f"Triggering webhook at {production_url}...")
                try:
                    # Strip trailing slash if present
                    base_url = production_url.rstrip("/")
                    url = f"{base_url}/api/internal/db-update?token={urllib.parse.quote(webhook_token)}"
                    req = urllib.request.Request(url, method="POST")
                    # Bypass SSL verification for local testing if necessary, but ideally we have valid certs
                    with urllib.request.urlopen(req) as response:
                        if response.status == 200:
                            print("Webhook triggered successfully. Production instance is updating its DB.")
                        else:
                            print(f"Webhook returned unexpected status: {response.status}")
                except urllib.error.URLError as e:
                    print(f"Failed to trigger webhook: {e}")
            else:
                print("Webhook not triggered (PRODUCTION_URL or WEBHOOK_TOKEN not set in .env)")
    elif choice == '2':
        print("\nDownloading...")
        # Be careful not to overwrite a local db with uncommitted changes
        confirm = input("This will overwrite your local photos.db. Are you sure? (y/N): ")
        if confirm.lower() == 'y':
            download_db_from_gcp("photos.db")
        else:
            print("Download cancelled.")
    elif choice == '3':
        print("Exiting.")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
