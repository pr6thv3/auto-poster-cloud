import os
import sys
import uuid
import time

def main():
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
    niche = os.environ.get('NICHE', 'general')
    
    print("--- Running Cloudflare R2 Upload Script ---")
    print(f"Niche: {niche}")
    print(f"Mock Mode: {mock_mode}")
    
    # Generate unique key for R2
    unique_id = uuid.uuid4().hex[:12]
    r2_key = f"videos/{niche}/{unique_id}.mp4"
    
    # We will get the public URL base from env, default to example.com for mock
    public_base = os.environ.get('R2_PUBLIC_BASE_URL', 'https://media.example.com')
    public_url = f"{public_base}/{r2_key}"
    
    if mock_mode:
        print("[MOCK] Uploading video to Cloudflare R2...")
        print(f"[MOCK] Key: {r2_key}")
        print(f"[MOCK] Simulated upload complete. Public URL: {public_url}")
    else:
        # Real Boto3 Upload (implemented for future reference/run phases)
        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            print("Error: boto3 package not installed. Run pip install boto3")
            sys.exit(1)
            
        account_id = os.environ.get('R2_ACCOUNT_ID')
        access_key = os.environ.get('R2_ACCESS_KEY_ID')
        secret_key = os.environ.get('R2_SECRET_ACCESS_KEY')
        bucket_name = os.environ.get('R2_BUCKET', 'shorts-staging')
        
        if not all([account_id, access_key, secret_key]):
            print("Error: Missing Cloudflare R2 credentials (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY)")
            sys.exit(1)
            
        # We need to find the video path from previous step (or we scan storage/tasks/)
        # For simplicity, we search glob for *.mp4 under storage/tasks/ again
        import glob
        search_pattern = os.path.join("storage", "tasks", "**", "*.mp4")
        files = glob.glob(search_pattern, recursive=True)
        if not files:
            print("Error: No video file found to upload.")
            sys.exit(1)
        files.sort(key=os.path.getmtime, reverse=True)
        video_path = files[0]
        
        print(f"[REAL] Uploading {video_path} to R2 bucket '{bucket_name}' with key '{r2_key}'...")
        
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        
        try:
            s3 = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=Config(signature_version='s3v4')
            )
            
            # Upload file
            s3.upload_file(
                Filename=video_path,
                Bucket=bucket_name,
                Key=r2_key,
                ExtraArgs={'ContentType': 'video/mp4'}
            )
            print("[REAL] Upload successful!")
        except Exception as e:
            print(f"Error uploading to Cloudflare R2: {str(e)}")
            sys.exit(1)

    # Write output to GITHUB_OUTPUT
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"public_video_url={public_url}\n")
            f.write(f"r2_key={r2_key}\n")
        print(f"Wrote outputs to GITHUB_OUTPUT: public_video_url={public_url}, r2_key={r2_key}")

if __name__ == "__main__":
    main()
