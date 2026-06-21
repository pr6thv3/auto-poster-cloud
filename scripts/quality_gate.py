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

def get_scene_duration(time_range):
    parts = time_range.split("-")
    if len(parts) == 2:
        try:
            t1 = parse_time_to_seconds(parts[0].strip())
            t2 = parse_time_to_seconds(parts[1].strip())
            return t2 - t1
        except Exception:
            pass
    return 0

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
    
    # Check for hook engaging patterns (time saved, workflow improvement, problem/solution, benefit, curiosity gap)
    patterns = {
        "time_saved": ["hour", "minute", "second", "time", "fast", "quick", "speed", "save", "day"],
        "workflow_improvement": ["work", "job", "task", "workflow", "easier", "better", "productivity", "smarter", "automate", "automation", "improve", "hard", "use", "using", "simple", "easy", "change", "new"],
        "problem_solution": ["stop", "prevent", "solve", "fix", "instead", "tired", "stuck", "wrong", "error", "fail", "broken", "break"],
        "benefit_value": ["free", "earn", "make", "help", "benefit", "create", "build", "generate", "cheap", "worth", "value", "profit", "win", "best"],
        "curiosity_gap": ["why", "how", "secret", "reveal", "hidden", "discover", "must", "missing", "need", "find", "show", "believe", "know", "question", "actually", "what", "who", "where", "look", "watch", "see"]
    }
    
    hook_lower = hook.lower()
    has_pattern = False
    for pat_name, keywords in patterns.items():
        if any(kw in hook_lower for kw in keywords):
            has_pattern = True
            break
            
    if not has_pattern:
        warnings.append("Hook does not match any engaging patterns (problem/solution, benefit, curiosity gap, time saved, or workflow improvement).")
        
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
        if target_length > 58 and brief.get("format_id") != "viral_curiosity_24s":
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

    # 8. Viral curiosity format specific validations
    format_id = brief.get("format_id", "")
    if format_id == "viral_curiosity_24s":
        target_len = brief.get("target_length_seconds", 0)
        hard_max = brief.get("hard_max_duration_seconds", 0)
        hard_min = brief.get("hard_min_duration_seconds", 0)
        
        # Check target length is in preferred 20-30s range
        if target_len < 20 or target_len > 30:
            reasons.append(f"Target length ({target_len}s) must be between 20 and 30 seconds for viral format.")
        
        # Check hard limits
        if hard_max > 32:
            reasons.append(f"Hard max duration ({hard_max}s) cannot exceed 32 seconds for viral format.")
        if hard_min < 18:
            reasons.append(f"Hard min duration ({hard_min}s) cannot be below 18 seconds for viral format.")
            
        # Hook greetings check
        greetings = ["hey", "hello", "welcome", "hi", "what's up", "yo "]
        if any(hook.lower().startswith(g) for g in greetings):
            reasons.append(f"Hook starts with a greeting: '{hook}'")
            
        # Scene plan checks
        scene_plan = brief.get("scene_plan", [])
        if len(scene_plan) < 10:
            reasons.append(f"Scene plan has only {len(scene_plan)} scenes (minimum required for viral format is 10).")
            
        has_long_scene = False
        has_movement_missing = False
        for s in scene_plan:
            tr = s.get("time_range", "")
            dur = get_scene_duration(tr)
            if dur > 2:
                has_long_scene = True
            if not s.get("movement", "").strip():
                has_movement_missing = True
                
        if has_long_scene:
            reasons.append("One or more scenes have a duration longer than 2 seconds.")
        if has_movement_missing:
            reasons.append("One or more scenes are missing movement instructions.")
            
        # Text overlay plan checks
        overlay_plan = brief.get("text_overlay_plan", [])
        if not overlay_plan:
            reasons.append("Text overlay plan is missing or empty.")
        else:
            long_captions = []
            for item in overlay_plan:
                words = item.get("text", "").split()
                if len(words) > 4:
                    long_captions.append(item.get("text"))
            if long_captions:
                warnings.append(f"Captions too long (some contain more than 4 words: {long_captions[:3]}).")
                
        # Narration greetings/filler check
        fillers = [" um ", " ah ", " basically ", " literally ", " actually ", " like "]
        combined_audio = " ".join([s.get("audio", "") for s in scene_plan]).lower()
        if any(f in f" {combined_audio} " for f in fillers):
            warnings.append("Narration contains filler words (um, ah, basically, literally, etc.).")
            
        # Safety rules check
        safety_rules = brief.get("safety_rules", [])
        if not safety_rules:
            reasons.append("Safety rules are missing or empty.")
            
        # Copyright check
        copyright_keywords = ["simpsons", "disney", "fox", "mickey", "marvel", "star wars", "pixar"]
        found_copyright = []
        combined_text_to_check = (brief.get("topic", "") + " " + hook + " " + " ".join([s.get("visual", "") for s in scene_plan])).lower()
        for keyword in copyright_keywords:
            if keyword in combined_text_to_check:
                found_copyright.append(keyword)
        if found_copyright:
            reasons.append(f"Copyrighted character or clip dependency detected: {found_copyright}")
            
        # Warnings for curiosity gap, sound cues, payoff
        curiosity_gap = brief.get("narration_beats", [""])[1] if len(brief.get("narration_beats", [])) > 1 else ""
        if not curiosity_gap or len(str(curiosity_gap).strip()) < 5:
            warnings.append("Weak curiosity gap: No clear curiosity gap defined.")
            
        sound_design = brief.get("sound_design", {})
        transitions = sound_design.get("transitions", [])
        if not sound_design or len(transitions) < 2:
            warnings.append("Too few sound cues / transitions defined in sound design.")
            
        payoff = brief.get("narration_beats", [""])[3] if len(brief.get("narration_beats", [])) > 3 else ""
        if not payoff or len(str(payoff).strip()) < 5:
            warnings.append("Payoff is unclear or missing.")
            
    # 9. Claim Safety Checks (Phase 1)
    unsafe_phrases = [
        "clone any website",
        "clones any website",
        "copy any website",
        "copies any website",
        "steal website",
        "steals website",
        "stealing website",
        "duplicate any site",
        "duplicates any site",
        "rip a website",
        "rips a website",
        "one click clone",
        "one-click clone",
        "one click clones",
        "one-click clones",
        "copy someone's site",
        "copy someone\u2019s site",
        "copies someone's site",
        "copies someone\u2019s site"
    ]
    safe_override_terms = [
        "user-owned",
        "draft",
        "mockup",
        "layout recreation",
        "recreate a landing page",
        "rebuild your own"
    ]
    
    topic_val = brief.get("topic", "")
    hook_val = brief.get("hook", "")
    if not hook_val:
        hook_val = brief.get("hook_0_3s", "")
    payoff_val = brief.get("payoff", "")
    if not payoff_val:
        payoff_val = brief.get("narration_beats", [""])[3] if len(brief.get("narration_beats", [])) > 3 else ""
        
    for field_name, val in [("topic", topic_val), ("hook", hook_val), ("payoff", payoff_val)]:
        val_lower = val.lower()
        has_unsafe = any(unsafe in val_lower for unsafe in unsafe_phrases)
        if has_unsafe:
            has_override = any(override in val_lower for override in safe_override_terms)
            if not has_override:
                reasons.append(f"Unsafe cloning/copying phrasing detected in {field_name}: '{val}' without safe override terms.")

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

