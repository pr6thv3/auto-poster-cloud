import os
import sys
import subprocess
import shutil

def main():
    topic = os.environ.get('TOPIC', 'Default Topic')
    title = os.environ.get('TITLE', 'Default Title')
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'

    print(f"--- Running MoneyPrinterTurbo Integration ---")
    print(f"Topic: {topic}")
    print(f"Title: {title}")
    print(f"Mock Mode: {mock_mode}")

    if mock_mode:
        print("[MOCK] Simulating MoneyPrinterTurbo generation...")
        # Create a mock video directory and file
        output_dir = "storage/tasks/mock-task"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "final-1.mp4")
        
        # Write dummy data to the file to make it look valid (>100KB)
        print(f"[MOCK] Writing dummy MP4 file of size ~150KB to {output_path}")
        with open(output_path, "wb") as f:
            f.write(b"0" * 150000)
        
        print("[MOCK] Mock video generation completed successfully.")
    else:
        print("[REAL] Setting up and running real MoneyPrinterTurbo...")
        
        repo_dir = "moneyprinter-repo"
        # 1. Clone repo if it doesn't exist
        if not os.path.exists(repo_dir):
            print(f"[REAL] Cloning harry0703/MoneyPrinterTurbo into {repo_dir}...")
            subprocess.run([
                "git", "clone", "https://github.com/harry0703/MoneyPrinterTurbo.git", repo_dir
            ], check=True)
        
        # 2. Write config.toml inside the cloned repo
        llm_provider = os.environ.get('LLM_PROVIDER', 'openai')
        video_source = os.environ.get('VIDEO_SOURCE', 'pexels')
        pexels_key = os.environ.get('PEXELS_API_KEY', '')
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        openai_model = os.environ.get('OPENAI_MODEL_NAME', '').strip() or 'gpt-4o-mini'
        gemini_key = os.environ.get('GEMINI_API_KEY', '')
        gemini_model = os.environ.get('GEMINI_MODEL_NAME', '').strip() or 'gemini-1.5-flash'
        
        config_path = os.path.join(repo_dir, "config.toml")
        print(f"[REAL] Generating config.toml at {config_path}...")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(f"""[app]
video_source = "{video_source}"
pexels_api_keys = ["{pexels_key}"]
llm_provider = "{llm_provider}"
openai_api_key = "{openai_key}"
openai_model_name = "{openai_model}"
gemini_api_key = "{gemini_key}"
gemini_model_name = "{gemini_model}"
subtitle_provider = "edge"
""")
            
        # 3. Install dependencies in GHA
        print("[REAL] Installing MoneyPrinterTurbo dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", os.path.join(repo_dir, "requirements.txt")
        ], check=True)
        
        # 4. Run CLI script
        print("[REAL] Executing MoneyPrinterTurbo CLI...")
        cmd = [
            sys.executable,
            "cli.py",
            "--video-subject", topic,
            "--video-language", "en-US",
            "--voice-name", "en-US-AndrewNeural",
            "--paragraph-number", "1"
        ]
        subprocess.run(cmd, cwd=repo_dir, check=True)
        
        # 5. Locate the generated output and copy it to our storage directory
        src_storage = os.path.join(repo_dir, "storage")
        dst_storage = "storage"
        if os.path.exists(src_storage):
            print(f"[REAL] Copying generated storage files from {src_storage} to {dst_storage}...")
            if os.path.exists(dst_storage):
                shutil.rmtree(dst_storage)
            shutil.copytree(src_storage, dst_storage)
            print("[REAL] Storage folder copied successfully.")
        else:
            print("Error: No storage directory generated inside MoneyPrinterTurbo repository.")
            sys.exit(1)

if __name__ == "__main__":
    main()
