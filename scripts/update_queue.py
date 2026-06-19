import os
import sys
import json

def main():
    print("--- Updating Content Queue ---")
    queue_item_id = os.environ.get('QUEUE_ITEM_ID', '').strip()
    if not queue_item_id:
        print("No QUEUE_ITEM_ID provided. Skipping queue update.")
        return
        
    status = os.environ.get('YT_STATUS', 'failed').lower()
    video_id = os.environ.get('YT_VIDEO_ID', '')
    error_msg = os.environ.get('YT_ERROR', '')
    
    queue_path = os.path.join("docs", "content-queue.json")
    if not os.path.exists(queue_path):
        print(f"Error: Queue file not found at {queue_path}")
        sys.exit(1)
        
    try:
        with open(queue_path, "r", encoding="utf-8") as f:
            queue = json.load(f)
    except Exception as e:
        print(f"Error reading queue file: {e}")
        sys.exit(1)
        
    found = False
    for item in queue:
        # Cast both to string to be safe
        if str(item.get("id")) == str(queue_item_id):
            found = True
            item["attempts"] = item.get("attempts", 0) + 1
            if status == "success":
                item["posted"] = True
                item["status"] = "success"
                item["youtube_video_id"] = video_id
                item["last_error"] = ""
            else:
                item["status"] = "failed"
                item["last_error"] = error_msg or "Unknown error"
            print(f"Updated item ID {queue_item_id}: posted={item['posted']}, status={item['status']}")
            break
            
    if not found:
        print(f"Warning: Queue item with ID {queue_item_id} not found in queue.")
        return
        
    try:
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2)
        print("Queue saved successfully.")
    except Exception as e:
        print(f"Error writing queue file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
