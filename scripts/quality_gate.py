import os
import sys
import json
import re

def parse_time_to_seconds(time_str):
    parts = time_str.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def get_outline_duration(outline):
    max_seconds = 0
    time_pattern = re.compile(r'(\d+:\d+(?::\d+)?)')
    for item in outline:
        matches = time_pattern.findall(item)
        for m in matches:
            try:
                sec = parse_time_to_seconds(m)
                if sec > max_seconds:
                    max_seconds = sec
            except ValueError:
                pass
    return max_seconds

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
    warnings = []
    
    # 1. Check Hook Strength, Length, and Vague/Concrete
    hook = brief.get("hook", "").strip()
    if len(hook) < 15:
        reasons.append("Hook is too short (less than 15 characters).")
        
    hook_words = hook.split()
    if len(hook_words) > 16:
        reasons.append(f"Hook is too long ({len(hook_words)} words, maximum allowed is 16 words).")
        
    if len(hook_words) < 6:
        reasons.append("Hook is too short and vague (less than 6 words).")
    else:
        # Check if hook is vague/not concrete (no overlap of meaningful words with topic)
        hook_words_set = set(hook.lower().replace("?", "").replace("!", "").replace(".", "").split())
        stop_words = {"this", "that", "these", "those", "is", "are", "was", "were", "the", "a", "an", "and", "or", "but", "if", "you", "your", "my", "to", "for", "in", "on", "at", "with"}
        meaningful_hook_words = hook_words_set - stop_words
        
        topic_words_set = set(brief.get("topic", "").lower().replace("?", "").replace("!", "").replace(".", "").split())
        meaningful_topic_words = topic_words_set - stop_words
        
        overlap = meaningful_hook_words.intersection(meaningful_topic_words)
        if not overlap:
            warnings.append("Hook is vague or not concrete (contains no overlapping subject keywords from the topic).")
    
    # Check for hook engaging keywords (but not weak generic ones)
    engaging_keywords = ["want", "stop", "how", "secret", "free", "must", "mind-blowing", "need", "discover", "reveal"]
    has_engaging = any(kw in hook.lower() for kw in engaging_keywords)
    if not has_engaging:
        warnings.append("Hook has no engaging trigger words (want, stop, how, free, need, discover, etc.).")
        
    # Weak generic hooks check
    weak_hooks = [
        "you won't believe",
        "you won’t believe",
        "this is amazing",
        "check this out"
    ]
    found_weak_hooks = []
    hook_lower = hook.lower()
    for weak in weak_hooks:
        if weak in hook_lower:
            found_weak_hooks.append(weak)
    if found_weak_hooks:
        reasons.append(f"Weak generic hook phrase detected: {list(set(found_weak_hooks))}")
    
    # Overpromising / unsafe phrases check (with warnings for soft ones)
    overpromising_fail_phrases = [
        "do all the work for you",
        "guaranteed income",
        "make money fast",
        "illegal",
        "no effort",
        "infinite money",
        "get rich"
    ]
    overpromising_warn_phrases = [
        "make money online",
        "passive income",
        "earn thousands",
        "earn money",
        "secret hack",
        "financial freedom",
        "double your money"
    ]
    found_fail = []
    found_warn = []
    
    text_to_check = []
    text_to_check.append(brief.get("topic", ""))
    text_to_check.append(brief.get("hook", ""))
    text_to_check.extend(brief.get("script_outline", []))
    
    for text in text_to_check:
        for phrase in overpromising_fail_phrases:
            if phrase in text.lower() and phrase not in found_fail:
                found_fail.append(phrase)
        for phrase in overpromising_warn_phrases:
            if phrase in text.lower() and phrase not in found_warn:
                found_warn.append(phrase)
                
    if found_fail:
        reasons.append(f"Overpromising/unsafe phrases detected: {list(set(found_fail))}")
    if found_warn:
        warnings.append(f"Overpromising/unsafe productivity/money claims detected: {list(set(found_warn))}")
        
    # 2. Check Title Guidance
    title_guidance = brief.get("title_guidance", "").strip()
    if len(title_guidance) < 15:
        reasons.append(f"Title guidance is too generic or short ({len(title_guidance)} chars, minimum required is 15).")
        
    # 3. Check for Banned Words
    banned_words = brief.get("banned_words", [])
    found_banned = []
    for text in text_to_check:
        for word in banned_words:
            if word.lower() in text.lower():
                found_banned.append(word)
                
    if found_banned:
        reasons.append(f"Banned words/topics detected: {list(set(found_banned))}")
        
    # 4. Check Freshness Score Threshold
    freshness_score = brief.get("freshness_score", 100)
    if freshness_score < 70:
        reasons.append(f"Freshness score ({freshness_score}) is below the required quality threshold (70).")
        
    # 5. Check Script Outline and Durations
    script_outline = brief.get("script_outline", [])
    if not script_outline:
        reasons.append("Script outline is missing or empty.")
    else:
        target_length = brief.get("target_length_seconds", 48)
        hard_max = brief.get("hard_max_duration_seconds", 58)
        
        # Check target length limits
        if target_length > 58:
            reasons.append(f"Target length ({target_length}s) is above the maximum allowed duration of 58 seconds.")
            
        outline_duration = get_outline_duration(script_outline)
        if outline_duration > hard_max:
            reasons.append(f"Script outline duration ({outline_duration}s) exceeds the hard maximum duration of {hard_max}s.")
        elif outline_duration > target_length:
            warnings.append(f"Script outline duration ({outline_duration}s) is longer than the target duration of {target_length}s.")
        
    # 6. Check for Concrete Value Proposition (Warning)
    value_prop_indicators = ["free", "save", "learn", "how", "help", "tool", "website", "app", "automate", "improve", "increase", "fast", "easy", "reduce", "optimize", "create", "build", "generate", "extension", "workflow", "design"]
    combined_text = (brief.get("topic", "") + " " + brief.get("hook", "") + " " + " ".join(script_outline)).lower()
    has_value_prop = any(indicator in combined_text for indicator in value_prop_indicators)
    if not has_value_prop:
        warnings.append("Missing concrete value proposition (does not explicitly mention tools, benefits, or actionable steps).")
        
    # 7. Check Voice Cloning safety
    combined_text_lower = combined_text.lower()
    if "clone" in combined_text_lower and "voice" in combined_text_lower:
        safe_voice_phrases = ["your own voice", "consent", "permission", "personal voiceover"]
        if not any(phrase in combined_text_lower for phrase in safe_voice_phrases):
            reasons.append("Voice cloning topic/script lacks safety consent/self-use framing. Must include phrases like: 'your own voice', 'consent', 'permission', or 'personal voiceover'.")
            
    # Compile Report
    if reasons:
        status = "failed"
    elif warnings:
        status = "warning"
    else:
        status = "passed"
        
    report = {
        "status": status,
        "reasons": reasons,
        "warnings": warnings
    }
    
    output_path = os.path.join("docs", "quality-report.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Quality gate complete. Status: {status.upper()}. Saved report to {output_path}")
        if warnings:
            print("Warnings:")
            for w in warnings:
                print(f" - {w}")
        if reasons:
            print("Failures:")
            for r in reasons:
                print(f" - {r}")
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        print(f"Error writing quality report: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
