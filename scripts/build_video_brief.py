import os
import sys
import json
import yaml

def get_script_and_scenes_for_format(format_type, topic, hook, curiosity_gap="", visual_promise="", payoff="", final_question_or_twist="", niche="tech"):
    if format_type == "viral_curiosity_24s":
        # Build narration beats
        narration_beats = [
            hook,
            curiosity_gap if curiosity_gap else "But there is a catch.",
            visual_promise if visual_promise else "Watch how it works.",
            payoff if payoff else "This changes everything.",
            final_question_or_twist if final_question_or_twist else "Follow for more daily tips!"
        ]
        
        # Build 12 scenes (2 seconds each for a total of 24 seconds)
        scenes = []
        scene_details = [
            ("0:00 - 0:02", f"Fast visual showing {topic}. Large center text overlay.", "Slow zoom-in"),
            ("0:02 - 0:04", f"Show the interface or starting point of {topic}.", "Pan right"),
            ("0:04 - 0:06", f"Reveal the setup: {visual_promise}.", "Rapid zoom-in"),
            ("0:06 - 0:08", "Zoom-in on key menu option or selector.", "Click zoom"),
            ("0:08 - 0:10", "Fast scroll showing processing/creation.", "Fast scroll down"),
            ("0:10 - 0:12", f"Highlight the friction point: {curiosity_gap}.", "Icon shake"),
            ("0:12 - 0:14", "Side-by-side template comparison.", "Split-screen slide"),
            ("0:14 - 0:16", "Toggle the advanced config switch to active.", "Toggle zoom"),
            ("0:16 - 0:18", f"Output generation screen showing the magic.", "Slide-in"),
            ("0:18 - 0:20", f"Final result reveal: {payoff}.", "Slow pan left"),
            ("0:20 - 0:22", "High-retention analytics graph or final usage demo.", "Device rotation"),
            ("0:22 - 0:24", "Pulsing Call to Action button with subscribe icon.", "Button pulse")
        ]
        
        for i, (time_range, visual, movement) in enumerate(scene_details):
            # Distribute narration beats across scenes
            beat_index = min(i // 2.5, len(narration_beats) - 1)
            beat_index = int(beat_index)
            audio_beat = narration_beats[beat_index]
            scenes.append({
                "scene_id": i + 1,
                "time_range": time_range,
                "visual": visual,
                "audio": audio_beat,
                "movement": movement
            })
            
        outline = [f"{s['time_range']}: {s['visual']}" for s in scenes]
        return outline, scenes
    elif format_type == "list_top_3":
        outline = [
            "0:00 - 0:05: Hook: " + hook,
            "0:05 - 0:15: Introduction and first tool highlight",
            "0:15 - 0:30: Second tool highlight with major utility",
            "0:30 - 0:45: Third tool highlight (the best one)",
            "0:45 - 0:50: Outro and Call-To-Action (CTA)"
        ]
        scenes = [
            {"scene_id": 1, "time_range": "0:00 - 0:05", "visual": "Fast cuts of the 3 tools, zoom on text overlay with topic name.", "audio": "Hook narration with high energy.", "movement": "Zoom-in"},
            {"scene_id": 2, "time_range": "0:05 - 0:15", "visual": "Screen recording of Tool 1 interface showing a quick demo.", "audio": "Explain what Tool 1 is and why it helps.", "movement": "Pan left"},
            {"scene_id": 3, "time_range": "0:15 - 0:30", "visual": "Screen recording of Tool 2 showing automated processing.", "audio": "Explain the major benefit of Tool 2.", "movement": "Pan right"},
            {"scene_id": 4, "time_range": "0:30 - 0:45", "visual": "Screen recording of Tool 3 executing a complex task in 1-click.", "audio": "Show the mind-blowing feature of Tool 3.", "movement": "Zoom-out"},
            {"scene_id": 5, "time_range": "0:45 - 0:50", "visual": "CTA overlay text (e.g. Subscribe/Link in bio) with animated button.", "audio": "Encourage user to follow/subscribe for more tech hacks.", "movement": "Pulse"}
        ]
    elif format_type == "tutorial":
        outline = [
            "0:00 - 0:05: Hook: " + hook,
            "0:05 - 0:15: Step 1: Preparation / Setup",
            "0:15 - 0:35: Step 2: Implementation core steps",
            "0:35 - 0:45: Step 3: Final result / Output check",
            "0:45 - 0:50: Outro / Try it yourself CTA"
        ]
        scenes = [
            {"scene_id": 1, "time_range": "0:00 - 0:05", "visual": "Before/After split screen showing the final tutorial result.", "audio": "Hook narration with engaging tone.", "movement": "Split-zoom"},
            {"scene_id": 2, "time_range": "0:05 - 0:15", "visual": "Navigate to the site and show where to click first.", "audio": "Step 1 details: Go to the website and import your file.", "movement": "Pan left"},
            {"scene_id": 3, "time_range": "0:15 - 0:35", "visual": "Clicking buttons and adjusting sliders in real time.", "audio": "Step 2 details: Adjust settings and hit generate to process it.", "movement": "Zoom-in"},
            {"scene_id": 4, "time_range": "0:35 - 0:45", "visual": "Show the final downloaded asset/output in high quality.", "audio": "Step 3 details: Look at this perfect output. It took just seconds.", "movement": "Pan right"},
            {"scene_id": 5, "time_range": "0:45 - 0:50", "visual": "CTA social buttons and text overlays.", "audio": "Outro: Try it out and follow for more tutorials!", "movement": "Pulse"}
        ]
    else: # one_tool_highlight or generic
        outline = [
            "0:00 - 0:05: Hook: " + hook,
            "0:05 - 0:20: The major problem faced by users",
            "0:20 - 0:45: The tool demo showing how it solves the problem",
            "0:45 - 0:50: CTA and outro"
        ]
        scenes = [
            {"scene_id": 1, "time_range": "0:00 - 0:05", "visual": "Headline overlay text with tool logo.", "audio": "Hook narration.", "movement": "Zoom-in"},
            {"scene_id": 2, "time_range": "0:05 - 0:20", "visual": "Frustrated user clip or slow paid software loading screen.", "audio": "Explain the pain point of paying too much or wasting hours.", "movement": "Pan left"},
            {"scene_id": 3, "time_range": "0:20 - 0:45", "visual": "Screen recording of the tool executing the solution automatically.", "audio": "Showcase the features of this specific tool.", "movement": "Pan right"},
            {"scene_id": 4, "time_range": "0:45 - 0:50", "visual": "Subscribe CTA overlay.", "audio": "Follow for daily tool breakdowns.", "movement": "Pulse"}
        ]
    return outline, scenes

def main():
    scored_path = os.path.join("docs", "scored-ideas.json")
    
    if not os.path.exists(scored_path):
        print(f"Error: Scored ideas file not found at {scored_path}")
        sys.exit(1)
        
    try:
        with open(scored_path, "r", encoding="utf-8") as f:
            scored_ideas = json.load(f)
    except Exception as e:
        print(f"Error reading scored ideas: {e}")
        sys.exit(1)
        
    # Find selected idea
    selected_idea = next((i for i in scored_ideas if i.get("selected")), None)
    if not selected_idea:
        print("Error: No selected idea found in scored-ideas.json.")
        sys.exit(1)
        
    profile_id = selected_idea.get("profile_id")
    profile_path = os.path.join("profiles", f"{profile_id}.yml")
    
    if not os.path.exists(profile_path):
        print(f"Error: Profile configuration not found at {profile_path}")
        sys.exit(1)
        
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading profile configuration: {e}")
        sys.exit(1)
        
    format_type = selected_idea.get("format", "")
    topic = selected_idea.get("topic", "")
    hook = selected_idea.get("hook", "")
    curiosity_gap = selected_idea.get("curiosity_gap", "")
    visual_promise = selected_idea.get("visual_promise", "")
    payoff = selected_idea.get("payoff", "")
    final_question_or_twist = selected_idea.get("final_question_or_twist", "")
    niche = profile.get("niche", "tech")
    
    # Load format preset if configured
    format_preset_path = profile.get("format_preset")
    format_preset = {}
    if format_preset_path and os.path.exists(format_preset_path):
        try:
            with open(format_preset_path, "r", encoding="utf-8") as f:
                format_preset = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not read format preset {format_preset_path}: {e}")
            
    outline, scenes = get_script_and_scenes_for_format(
        format_type, topic, hook, curiosity_gap, visual_promise, payoff, final_question_or_twist, niche
    )
    
    # Enforce defaults from format preset if present
    target_len = profile.get("preferred_duration_seconds", 48)
    hard_max = profile.get("hard_max_duration_seconds", 58)
    
    min_len = 20
    max_len = 30
    hard_min = 18
    
    if format_preset:
        duration_cfg = format_preset.get("duration", {})
        target_len = duration_cfg.get("preferred_seconds", target_len)
        min_len = duration_cfg.get("min_seconds", min_len)
        max_len = duration_cfg.get("max_seconds", max_len)
        hard_min = duration_cfg.get("hard_min_seconds", hard_min)
        hard_max = duration_cfg.get("hard_max_seconds", hard_max)
        
    # Build text overlay plan for viral_curiosity_24s
    text_overlay_plan = []
    if format_type == "viral_curiosity_24s":
        narration_beats = [
            hook,
            curiosity_gap if curiosity_gap else "But there is a catch.",
            visual_promise if visual_promise else "Watch how it works.",
            payoff if payoff else "This changes everything.",
            "Follow for more daily tips!"
        ]
        all_words = []
        for beat in narration_beats:
            all_words.extend(beat.split())
        if not all_words:
            all_words = ["WATCH", "THIS", "VIRAL", "VIDEO"]
            
        word_index = 0
        for sec in range(target_len):
            chunk = []
            for _ in range(3):
                if word_index < len(all_words):
                    chunk.append(all_words[word_index])
                    word_index += 1
            if not chunk:
                chunk = ["CHECK", "THIS", "OUT"]
            text_overlay_plan.append({
                "time_range": f"0:{sec:02d} - 0:{sec+1:02d}",
                "text": " ".join(chunk).upper()
            })
            
    # Compile brief
    brief = {
        "profile_id": profile_id,
        "idea_id": selected_idea.get("idea_id"),
        "topic": topic,
        "hook": hook,
        "freshness_score": selected_idea.get("freshness_score", 100),
        "script_outline": outline,
        "scene_plan": scenes,
        "voice_style": {
            "tone": profile.get("tone", ["professional"]),
            "style_rules": profile.get("style", {}).get("audio", ["voiceover first"])
        },
        "subtitle_style": {
            "style_rules": profile.get("style", {}).get("visuals", ["clean subtitle text"])
        },
        "title_guidance": "Create an engaging title under 50 characters summarizing: " + topic,
        "hashtag_guidance": "Include #Shorts, the niche #" + niche + ", and keywords: " + ", ".join(selected_idea.get("keywords", [])),
        "banned_words": profile.get("banned_words", []),
        
        # Storytelling checkpoints (v2.1a)
        "hook_claim": hook,
        "proof_event": visual_promise if visual_promise else "Watch the proof.",
        "payoff_line": payoff if payoff else "This solves the problem.",
        "final_resolution_line": final_question_or_twist if final_question_or_twist else "Will you try this?",
        "loop_tieback": selected_idea.get("loop_tieback", "") or f"Loop back to: {hook}",

        # Viral format attributes
        "format_id": format_preset.get("format_id") if format_preset else format_type,
        "target_length_seconds": target_len,
        "preferred_duration_seconds": target_len,
        "min_duration_seconds": min_len,
        "max_duration_seconds": max_len,
        "hard_min_duration_seconds": hard_min,
        "hard_max_duration_seconds": hard_max,
        "hook_0_3s": hook,
        "curiosity_gap": curiosity_gap,
        "visual_promise": visual_promise,
        "payoff": payoff,
        "final_question_or_twist": final_question_or_twist,
        "narration_beats": [
            hook,
            curiosity_gap,
            visual_promise,
            payoff,
            final_question_or_twist if final_question_or_twist else "Follow for more."
        ] if format_type == "viral_curiosity_24s" else [hook],
        "text_overlay_plan": text_overlay_plan,
        "editing_rhythm": format_preset.get("editing", {}),
        "sound_design": format_preset.get("sound_design", {}),
        "visual_rules": format_preset.get("text_overlay", {}),
        "safety_rules": profile.get("safety_rules", [])
    }
    
    output_path = os.path.join("docs", "video-brief.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(brief, f, indent=2)
        print(f"Successfully generated video brief for topic '{topic}' to {output_path}")
    except Exception as e:
        print(f"Error writing video brief: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
