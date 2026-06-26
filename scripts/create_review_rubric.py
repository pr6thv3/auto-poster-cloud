import os
import json
import sys

def main():
    print("--- Creating Manual Review Rubric ---")
    rubric_path = os.path.join("docs", "manual-review-rubric.json")
    
    rubric = {
        "hook_frame_clarity": None,
        "caption_readability": None,
        "proof_asset_visible": None,
        "proof_asset_repetition_score": None,
        "final_payoff_clarity": None,
        "visual_relevance": None,
        "bgm_level": None,
        "overall_post_ready": False,
        "review_notes": ""
    }
    
    try:
        os.makedirs(os.path.dirname(rubric_path), exist_ok=True)
        with open(rubric_path, "w", encoding="utf-8") as f:
            json.dump(rubric, f, indent=2)
        print(f"Created manual review rubric at {rubric_path}")
    except Exception as e:
        print(f"Error creating rubric: {e}")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
