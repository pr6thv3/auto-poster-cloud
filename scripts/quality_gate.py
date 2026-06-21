import os
import sys
import json

def main():
    brief_path = os.path.join("docs", "video-brief.json")
    
    if not os.path.exists(brief_path):
        print(f"Error: Video brief file not found at {brief_path}")
        sys.exit(1)
        
    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief = json.load(f)
    except Exception as e:
        print(f"Error reading video brief: {e}")
        sys.exit(1)
        
    reasons = []
    
    # 1. Check Hook Strength
    hook = brief.get("hook", "").strip()
    if len(hook) < 15:
        reasons.append("Hook is too short (less than 15 characters).")
    
    # Check for hook engaging keywords
    engaging_keywords = ["want", "stop", "how", "secret", "illegal", "free", "amazing", "must", "mind-blowing", "need", "discover", "reveal"]
    has_engaging = any(kw in hook.lower() for kw in engaging_keywords)
    if not has_engaging:
        reasons.append("Hook is weak or generic (does not contain engaging trigger words).")
        
    # 2. Check Title Guidance
    title_guidance = brief.get("title_guidance", "").strip()
    if len(title_guidance) < 10:
        reasons.append("Title guidance is too generic or missing.")
        
    # 3. Check for Banned Words
    banned_words = brief.get("banned_words", [])
    text_to_check = []
    text_to_check.append(brief.get("topic", ""))
    text_to_check.append(brief.get("hook", ""))
    text_to_check.extend(brief.get("script_outline", []))
    
    found_banned = []
    for text in text_to_check:
        for word in banned_words:
            if word.lower() in text.lower():
                found_banned.append(word)
                
    if found_banned:
        reasons.append(f"Banned words/topics detected: {list(set(found_banned))}")
        
    # 4. Check Freshness Score Threshold
    freshness_score = brief.get("freshness_score", 100)
    if freshness_score < 60:
        reasons.append(f"Freshness score ({freshness_score}) is below the required quality threshold (60).")
        
    # 5. Check Script Outline
    script_outline = brief.get("script_outline", [])
    if not script_outline:
        reasons.append("Script outline is missing or empty.")
        
    # Compile Report
    status = "passed" if not reasons else "failed"
    report = {
        "status": status,
        "reasons": reasons
    }
    
    output_path = os.path.join("docs", "quality-report.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Quality gate complete. Status: {status.upper()}. Saved report to {output_path}")
        if reasons:
            print("Failures:")
            for r in reasons:
                print(f" - {r}")
    except Exception as e:
        print(f"Error writing quality report: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
