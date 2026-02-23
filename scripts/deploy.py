import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    # Load environment variables from .env
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        sys.exit(1)
        
    load_dotenv(env_path)
    
    # Get configuration from environment
    project_id = os.getenv("GCP_PROJECT_ID")
    service_name = os.getenv("GCP_SERVICE_NAME", "photo-gallery")
    region = os.getenv("GCP_REGION", "us-central1")
    public_bucket = os.getenv("GCP_BUCKET_NAME")
    private_bucket = os.getenv("GCP_DB_BUCKET_NAME")
    
    if not project_id:
        print("Error: GCP_PROJECT_ID not set in .env")
        sys.exit(1)
    if not public_bucket or not private_bucket:
        print("Error: GCP_BUCKET_NAME or GCP_DB_BUCKET_NAME not set in .env")
        sys.exit(1)

    print(f"--- Cloud Run Deployment (Python) ---")
    print(f"Project ID:   {project_id}")
    print(f"Service Name: {service_name}")
    print(f"Region:       {region}")
    print(f"Public Bkt:   {public_bucket}")
    print(f"Private Bkt:  {private_bucket}")
    print("-" * 38)

    # Construct the gcloud command
    # Using --set-env-vars to specify the backend and bucket names for production
    cmd = [
        "gcloud", "run", "deploy", service_name,
        f"--project={project_id}",
        f"--region={region}",
        "--source=.",
        "--allow-unauthenticated",
        f"--set-env-vars=STORAGE_BACKEND=gcp,ADMIN_MODE=false,GCP_BUCKET_NAME={public_bucket},GCP_DB_BUCKET_NAME={private_bucket}"
    ]

    print("\nExecuting deployment...")
    try:
        # Run the command and stream output to terminal
        # On Windows, we need shell=True to resolve gcloud (which is often gcloud.cmd)
        is_windows = os.name == 'nt'
        result = subprocess.run(cmd, check=True, shell=is_windows)
        print("\nDeployment successful!")
    except subprocess.CalledProcessError as e:
        print(f"\nDeployment failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("\nError: 'gcloud' command not found. Please ensure Google Cloud CLI is installed and in your PATH.")
        sys.exit(1)

if __name__ == "__main__":
    main()
