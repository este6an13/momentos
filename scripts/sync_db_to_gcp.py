import os
import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Ensure environment variables are loaded before anything else
load_dotenv()

from app.gcp_utils import upload_db_to_gcp, download_db_from_gcp

def main():
    print("--- GCP Database Sync Tool ---")
    print("1. Upload local photos.db to GCP")
    print("2. Download photos.db from GCP to local")
    print("3. Exit")
    
    choice = input("Enter your choice (1/2/3): ")
    
    if choice == '1':
        print("\nUploading...")
        upload_db_to_gcp("photos.db")
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
