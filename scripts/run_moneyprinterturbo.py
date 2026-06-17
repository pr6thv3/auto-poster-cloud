import os
import sys

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
        print("[REAL] Running real MoneyPrinterTurbo is not implemented in Phase 1.")
        # This will be wired to actual CLI execution in a future phase
        sys.exit(1)

if __name__ == "__main__":
    main()
