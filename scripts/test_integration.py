import os
import sys
import json
import subprocess

def run_cmd(args, env_override=None):
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    print(f"Running: {' '.join(args)}")
    res = subprocess.run(args, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Command failed with code {res.returncode}")
        print("stdout:", res.stdout)
        print("stderr:", res.stderr)
        sys.exit(res.returncode)
    else:
        print("stdout:", res.stdout)
    return res

def parse_time_to_seconds(time_str):
    parts = time_str.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

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
    print("=== STARTING LOCAL INTEGRATION TESTS ===")

    # 1. Clear any old build/output files
    files_to_clear = [
        "docs/generated-ideas.json",
        "docs/scored-ideas.json",
        "docs/video-brief.json",
        "docs/quality-report.json",
        "docs/retention-storyboard.json",
        "docs/retention-storyboard-synced.json",
        "docs/tts-timestamps.json",
        "youtube-metadata.json",
        "run-log.json",
        "platform-results.json",
        "step-summary-mock.md"
    ]
    for f in files_to_clear:
        if os.path.exists(f):
            os.remove(f)

    # 2. Run the Content Engine steps locally with a clean history sandbox
    print("\n--- Running Content Engine Steps ---")
    history_file = "docs/content-history.json"
    main_history_backup = None
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            main_history_backup = json.load(f)
            
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump([], f)
        
    try:
        run_cmd([sys.executable, "scripts/generate_ideas.py", "--profile", "profiles/ai_tools.yml"])
        run_cmd([sys.executable, "scripts/score_idea_freshness.py"])
        run_cmd([sys.executable, "scripts/build_video_brief.py"])
        run_cmd([sys.executable, "scripts/build_retention_storyboard.py"])
        run_cmd([sys.executable, "scripts/quality_gate.py"])
    finally:
        if main_history_backup is not None:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(main_history_backup, f, indent=2)
        elif os.path.exists(history_file):
            os.remove(history_file)

    # 3. Verify Content Engine output files
    assert os.path.exists("docs/video-brief.json"), "docs/video-brief.json was not created"
    assert os.path.exists("docs/quality-report.json"), "docs/quality-report.json was not created"

    with open("docs/video-brief.json", "r", encoding="utf-8") as f:
        brief = json.load(f)
    print("Generated Brief Topic:", brief.get("topic"))
    print("Banned Words in Brief:", brief.get("banned_words"))

    # 4. Set up mock pipeline environment and run downstream integration scripts
    print("\n--- Running Downstream mock GHA Steps ---")
    env = {
        "USE_VIDEO_BRIEF": "true",
        "TOPIC": brief.get("topic"),
        "NICHE": "ai",
        "METADATA_MODE": "mock",
        "GENERATION_MODE": "mock",
        "POSTING_MODE": "mock",
        "PRIVACY": "private",
        "GITHUB_STEP_SUMMARY": "step-summary-mock.md"
    }

    run_cmd([sys.executable, "scripts/generate_youtube_metadata.py"], env_override=env)
    run_cmd([sys.executable, "scripts/run_moneyprinterturbo.py"], env_override=env)
    run_cmd([sys.executable, "scripts/extract_tts_timestamps.py"], env_override=env)
    run_cmd([sys.executable, "scripts/mix_retention_audio.py"], env_override=env)
    run_cmd([sys.executable, "scripts/write_summary.py"], env_override=env)

    # 5. Assert output file generation and verification
    assert os.path.exists("youtube-metadata.json"), "youtube-metadata.json was not created"
    assert os.path.exists("run-log.json"), "run-log.json was not created"
    assert os.path.exists("platform-results.json"), "platform-results.json was not created"
    assert os.path.exists("step-summary-mock.md"), "step-summary-mock.md was not created"

    # 6. Read and check youtube-metadata.json for banned words
    with open("youtube-metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    print("\nGenerated Metadata:")
    print("Title:", meta.get("title"))
    print("Description:", meta.get("description"))
    print("Tags:", meta.get("tags"))
    print("Hashtags:", meta.get("hashtags"))

    for word in brief.get("banned_words", []):
        word_lower = word.lower()
        assert word_lower not in meta.get("title", "").lower(), f"Banned word '{word}' found in Title!"
        assert word_lower not in meta.get("description", "").lower(), f"Banned word '{word}' found in Description!"
        for tag in meta.get("tags", []):
            assert word_lower not in tag.lower(), f"Banned word '{word}' found in Tag: {tag}"
        for ht in meta.get("hashtags", []):
            assert word_lower not in ht.lower(), f"Banned word '{word}' found in Hashtag: {ht}"

    print("Verification: All banned words successfully avoided in metadata!")

    # 7. Read and check run-log.json for audit properties
    with open("run-log.json", "r", encoding="utf-8") as f:
        run_log = json.load(f)
    
    assert run_log.get("use_video_brief") is True, "use_video_brief should be True in run-log.json"
    assert run_log.get("profile_id") == brief.get("profile_id"), "profile_id does not match in run-log.json"
    assert run_log.get("selected_idea") == brief.get("topic"), "selected_idea does not match brief topic in run-log.json"
    assert run_log.get("freshness_score") == brief.get("freshness_score"), "freshness_score does not match brief score in run-log.json"
    assert run_log.get("quality_status") in ["passed", "warning"], f"quality_status was {run_log.get('quality_status')}"

    print("Verification: run-log.json includes correct Content Engine Audit properties!")

    # 8. Read step summary mock
    with open("step-summary-mock.md", "r", encoding="utf-8") as f:
        summary_text = f.read()
    print("\nMock Step Summary Markdown content:")
    print(summary_text)

    assert "Content Engine Audit" in summary_text, "Content Engine Audit section missing in step summary markdown"
    assert f"**Use Video Brief**: `True`" in summary_text, "Use Video Brief field missing or incorrect in step summary markdown"
    assert f"**Profile ID**: `{brief.get('profile_id')}`" in summary_text, "Profile ID field incorrect in step summary markdown"
    assert "**Quality Gate Status**: `PASSED`" in summary_text or "**Quality Gate Status**: `WARNING`" in summary_text, "Quality Gate Status incorrect in step summary markdown"

    print("Verification: step-summary-mock.md contains the correct Content Engine Audit markdown section!")

    # === TEST FRESHNESS PENALTIES AND SCORING LOGIC ===
    print("\n--- Testing Freshness Penalties and Scoring Logic ---")
    ideas_file = "docs/generated-ideas.json"
    history_file = "docs/content-history.json"
    scored_file = "docs/scored-ideas.json"

    # Backup original files if they exist
    ideas_backup = None
    if os.path.exists(ideas_file):
        with open(ideas_file, "r", encoding="utf-8") as f:
            ideas_backup = json.load(f)
            
    history_backup = None
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history_backup = json.load(f)

    # Setup mock history
    mock_history = [
        {
            "idea_id": "hist_ai_1",
            "profile_id": "ai_tools",
            "topic": "3 AI tools to start a side hustle",
            "angle": "side hustle automation",
            "hook": "Want to start a side hustle? These 3 AI tools will do all the work for you.",
            "keywords": ["side hustle", "ai tools", "make money online"],
            "format": "list_top_3",
            "created_at": "2026-06-20T12:00:00Z",
            "status": "success",
            "youtube_video_id": "mock_yt_1"
        }
    ]
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(mock_history, f, indent=2)

    # Setup mock ideas
    mock_ideas = [
        {
            "idea_id": "idea_test_1",
            "profile_id": "ai_tools",
            "topic": "3 AI tools to start a side hustle", # Exact Topic Overlap, Money Repetition
            "angle": "side hustle automation",
            "hook": "Want to start a side hustle? These 3 AI tools will do all the work for you.",
            "keywords": ["side hustle", "ai tools", "make money online"],
            "format": "list_top_3",
            "freshness_window_days": 14
        },
        {
            "idea_id": "idea_test_2",
            "profile_id": "ai_tools",
            "topic": "This AI website writes all your emails", # Fresh
            "angle": "email productivity",
            "hook": "Stop wasting hours writing emails. Let this free AI website do it in seconds.",
            "keywords": ["write emails", "ai website", "productivity hacks"],
            "format": "one_tool_highlight",
            "freshness_window_days": 7
        },
        {
            "idea_id": "idea_test_3",
            "profile_id": "ai_tools",
            "topic": "Another money making idea", # Money Repetition, Keyword Fatigue, Hook overlap
            "angle": "different angle",
            "hook": "Want to start something?",
            "keywords": ["side hustle", "ai tools", "something else"],
            "format": "tutorial",
            "freshness_window_days": 7
        }
    ]
    with open(ideas_file, "w", encoding="utf-8") as f:
        json.dump(mock_ideas, f, indent=2)

    # Run scorer
    run_cmd([sys.executable, "scripts/score_idea_freshness.py"])

    # Load scored ideas and assert penalties
    with open(scored_file, "r", encoding="utf-8") as f:
        scored = json.load(f)

    # Idea 1 asserts
    idea1 = next(i for i in scored if i["idea_id"] == "idea_test_1")
    assert "exact_topic_overlap" in idea1["penalty_reasons"], "Expected exact_topic_overlap penalty"
    assert "money_repetition" in idea1["penalty_reasons"], "Expected money_repetition penalty"
    assert "keyword_fatigue" in idea1["penalty_reasons"], "Expected keyword_fatigue penalty"
    assert "hook_pattern_overlap" in idea1["penalty_reasons"], "Expected hook_pattern_overlap penalty"
    assert "format_fatigue" in idea1["penalty_reasons"], "Expected format_fatigue penalty"
    assert idea1["freshness_score"] == 0, f"Expected freshness score 0 for regenerated exact topic, got {idea1['freshness_score']}"

    # Idea 2 asserts
    idea2 = next(i for i in scored if i["idea_id"] == "idea_test_2")
    assert len(idea2["penalty_reasons"]) == 0, "Expected no penalties for fresh idea"
    assert idea2["freshness_score"] == 100, "Expected freshness score 100 for fresh idea"

    # Idea 3 asserts
    idea3 = next(i for i in scored if i["idea_id"] == "idea_test_3")
    assert "money_repetition" in idea3["penalty_reasons"], "Expected money_repetition penalty on idea 3"
    assert "keyword_fatigue" in idea3["penalty_reasons"], "Expected keyword_fatigue penalty on idea 3"
    print("Verification: Freshness penalties scoring tests passed.")

    # === TEST QUALITY GATE HARDENING ===
    print("\n--- Testing Quality Gate Hardening ---")
    brief_file = "docs/video-brief.json"
    report_file = "docs/quality-report.json"

    # Backup original brief/report
    brief_backup = None
    if os.path.exists(brief_file):
        with open(brief_file, "r", encoding="utf-8") as f:
            brief_backup = json.load(f)
            
    report_backup = None
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            report_backup = json.load(f)

    # Helper function to run quality gate on a test brief
    def check_brief(test_brief):
        with open(brief_file, "w", encoding="utf-8") as f:
            json.dump(test_brief, f, indent=2)
        env = os.environ.copy()
        env["GENERATION_MODE"] = "real"
        res = subprocess.run([sys.executable, "scripts/quality_gate.py"], env=env, capture_output=True, text=True)
        with open(report_file, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        return res.returncode, report_data

    # (a) Overpromising hook failure
    res_code, report_data = check_brief({
        "topic": "Clean topic",
        "hook": "This secret hack gives you guaranteed income.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": ["scam", "illegal"],
        "freshness_score": 100
    })
    assert res_code == 1, "Expected quality gate to fail for overpromising hook"
    assert report_data["status"] == "failed", "Expected status failed"
    assert any("Overpromising" in r for r in report_data["reasons"]), "Expected overpromising reasons"

    # (b) Banned wording failure
    res_code, report_data = check_brief({
        "topic": "Clean topic",
        "hook": "This is a scam tool that is illegal.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": ["scam", "illegal"],
        "freshness_score": 100
    })
    assert res_code == 1, "Expected quality gate to fail for banned words"
    assert report_data["status"] == "failed"
    assert any("Banned words" in r for r in report_data["reasons"]), "Expected banned words warning"

    # (c) Weak hook failure
    res_code, report_data = check_brief({
        "topic": "Clean topic",
        "hook": "You won't believe this is amazing.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 1, "Expected quality gate to fail for weak generic hook"
    assert report_data["status"] == "failed"
    assert any("Weak generic" in r for r in report_data["reasons"])

    # (d) Hook longer than 16 words failure
    res_code, report_data = check_brief({
        "topic": "Clean topic",
        "hook": "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 1, "Expected quality gate to fail for long hook"
    assert report_data["status"] == "failed"
    assert any("too long" in r for r in report_data["reasons"])

    # (e) Freshness score below 70 failure
    res_code, report_data = check_brief({
        "topic": "Clean topic",
        "hook": "Discover this cool tool today.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 65
    })
    assert res_code == 1, "Expected quality gate to fail for low freshness score"
    assert report_data["status"] == "failed"
    assert any("Freshness score" in r for r in report_data["reasons"])

    # (f) Title too generic failure
    res_code, report_data = check_brief({
        "topic": "Clean topic",
        "hook": "Discover this cool tool today.",
        "title_guidance": "Short Title",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 1, "Expected quality gate to fail for generic title guidance"
    assert report_data["status"] == "failed"
    assert any("Title guidance" in r for r in report_data["reasons"])

    # (g) Safe rewritten hook passes
    res_code, report_data = check_brief({
        "topic": "Clean topic about productivity website",
        "hook": "Stop wasting hours writing emails. Let this free website help you.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": ["scam", "illegal"],
        "freshness_score": 100
    })
    assert res_code == 0, "Expected quality gate to pass for safe brief"
    assert report_data["status"] in ["passed", "warning"], f"Expected status passed or warning, got {report_data['status']}"

    # (h) Target length above 58 seconds (Fail)
    res_code, report_data = check_brief({
        "topic": "Clean topic",
        "hook": "Stop wasting hours writing emails. Let this free website help you.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100,
        "target_length_seconds": 60,
        "hard_max_duration_seconds": 58
    })
    assert res_code == 1, "Expected failure for target length > 58s"
    assert any("Target length" in r for r in report_data["reasons"])

    # (i) Script outline too long for target duration (Fail when exceeds hard max)
    res_code, report_data = check_brief({
        "topic": "Clean topic",
        "hook": "Stop wasting hours writing emails. Let this free website help you.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["0:00 - 0:05: Hook", "0:05 - 0:59: Loop"],
        "banned_words": [],
        "freshness_score": 100,
        "target_length_seconds": 48,
        "hard_max_duration_seconds": 58
    })
    assert res_code == 1, "Expected failure for outline duration exceeding hard max"
    assert any("exceeds the hard maximum" in r for r in report_data["reasons"])

    # (j) Script outline duration warn when exceeds target length
    res_code, report_data = check_brief({
        "topic": "Clean topic",
        "hook": "Stop wasting hours writing emails. Let this free website help you.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["0:00 - 0:05: Hook", "0:05 - 0:50: Loop"],
        "banned_words": [],
        "freshness_score": 100,
        "target_length_seconds": 48,
        "hard_max_duration_seconds": 58
    })
    assert res_code == 0, "Expected success/warning status, not fail"
    assert any("longer than the target duration" in w for w in report_data["warnings"])

    # (k) Hook vague / not concrete: less than 6 words (Fail)
    res_code, report_data = check_brief({
        "topic": "Clean topic about productivity website",
        "hook": "Check this tool",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 1, "Expected failure for hook < 6 words"
    assert any("too short and vague" in r for r in report_data["reasons"])

    # (l) Hook vague / not concrete: no overlapping keywords with topic (Warn)
    res_code, report_data = check_brief({
        "topic": "This website helps with programming",
        "hook": "Stop scrolling! Look at this incredible new software today.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 0, "Expected warning, not failure, for vague hook with no overlap"
    assert any("overlapping subject keywords" in w for w in report_data["warnings"])

    # (m) Topic overpromising money/productivity claims (Fail)
    res_code, report_data = check_brief({
        "topic": "How to get rich with infinite money",
        "hook": "Stop scrolling! Here is a cool way to program apps.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 1, "Expected failure for overpromising topic"
    assert any("Overpromising/unsafe phrases" in r for r in report_data["reasons"])

    # (n) Topic overpromising claims (Warn)
    res_code, report_data = check_brief({
        "topic": "How to make money online easily",
        "hook": "Stop scrolling! Here is a cool way to program apps.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 0, "Expected warning, not failure, for soft overpromising claim"
    assert any("productivity/money claims detected" in w for w in report_data["warnings"])

    # (o) Voice-cloning lacks consent framing (Fail)
    res_code, report_data = check_brief({
        "topic": "How to clone anyone's voice",
        "hook": "This tool lets you clone any voice for free.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 1, "Expected failure for voice cloning lacking safety terms"
    assert any("safety consent/self-use framing" in r for r in report_data["reasons"])

    # (p) Voice-cloning with consent framing (Pass)
    res_code, report_data = check_brief({
        "topic": "How to create an AI voiceover using your own voice",
        "hook": "You can create an AI voiceover using your own voice with consent in seconds.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 0, "Expected quality gate to pass with safety voice cloning framing"

    # (q) Hook lacks engaging pattern (Warn)
    res_code, report_data = check_brief({
        "topic": "Clean topic about productivity website",
        "hook": "A brief overview of the tool. Nothing special here.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 0, "Expected warning, not failure, for hook with no engaging pattern"
    assert any("does not match any engaging patterns" in w for w in report_data["warnings"])

    # (r) Unsafe cloning/copying phrasing fails
    res_code, report_data = check_brief({
        "topic": "This AI tool clones any website in one click",
        "hook": "Stop coding website designs from scratch today.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 1, "Expected failure for unsafe cloning phrase"
    assert any("Unsafe cloning/copying phrasing" in r for r in report_data["reasons"]), "Expected unsafe cloning reason"

    # (s) Safe rewritten cloning/copying phrasing passes
    res_code, report_data = check_brief({
        "topic": "This AI tool turns a website idea into a landing page",
        "hook": "Stop coding landing page mockups from scratch today.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 0, "Expected success for safe rewritten cloning phrasing"

    # (t) Unsafe cloning phrase with safe override term passes
    res_code, report_data = check_brief({
        "topic": "This AI tool clones any website to recreate a landing page layout",
        "hook": "Stop coding landing page mockups from scratch today.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100
    })
    assert res_code == 0, "Expected success for unsafe cloning phrase with safe override"

    print("Verification: Quality gate hardening tests passed.")

    # Cleanup and restore files
    for f, b in [(ideas_file, ideas_backup), (history_file, history_backup)]:
        if b is not None:
            with open(f, "w", encoding="utf-8") as file_obj:
                json.dump(b, file_obj, indent=2)
        elif os.path.exists(f):
            os.remove(f)

    for f, b in [(brief_file, brief_backup), (report_file, report_backup)]:
        if b is not None:
            with open(f, "w", encoding="utf-8") as file_obj:
                json.dump(b, file_obj, indent=2)
        elif os.path.exists(f):
            os.remove(f)

    # === TEST VIRAL FORMAT AND DURATION GUARDS ===
    print("\n--- Testing Viral Format and Duration Guards ---")
    
    # 1. Test viral format preset loads and brief properties
    run_cmd([sys.executable, "scripts/generate_ideas.py", "--profile", "profiles/ai_tools.yml"])
    run_cmd([sys.executable, "scripts/score_idea_freshness.py"])
    run_cmd([sys.executable, "scripts/build_video_brief.py"])
    
    with open(brief_file, "r", encoding="utf-8") as f:
        viral_brief = json.load(f)
        
    assert viral_brief.get("format_id") == "viral_retention_engine_24s", "Expected format_id to be viral_retention_engine_24s"
    assert viral_brief.get("target_length_seconds") == 24, "Expected target duration 24s"
    assert viral_brief.get("hard_max_duration_seconds") == 32, "Expected hard max duration 32s"
    assert len(viral_brief.get("scene_plan", [])) >= 10, "Expected at least 10 scenes"
    assert len(viral_brief.get("text_overlay_plan", [])) > 0, "Expected text overlay plan to exist"
    print("Verification: Viral format preset loaded successfully with correct target values.")

    # 2. Test Hook greeting failure
    res_code, report_data = check_brief({
        "topic": "This AI tool builds apps",
        "hook": "Hey guys, this AI tool builds apps in minutes.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100,
        "format_id": "viral_curiosity_24s",
        "target_length_seconds": 24,
        "hard_min_duration_seconds": 18,
        "hard_max_duration_seconds": 32,
        "scene_plan": [{"scene_id": i, "time_range": f"0:{i*2:02d} - 0:{(i+1)*2:02d}", "visual": "visual", "audio": "audio", "movement": "zoom"} for i in range(12)],
        "text_overlay_plan": [{"time_range": "0:00 - 0:01", "text": "text"}],
        "safety_rules": ["no copyright issues"]
    })
    assert res_code == 1, "Expected quality gate to fail for hook starting with greeting"
    assert any("starts with a greeting" in r for r in report_data["reasons"]), "Expected greeting failure reason"

    # 3. Test Copyrighted clip dependency failure
    res_code, report_data = check_brief({
        "topic": "Simpsons style cartoon builder",
        "hook": "This AI tool builds cartoon videos.",
        "title_guidance": "Clean Title Guidance of length 15+",
        "script_outline": ["Step 1", "Step 2", "Step 3"],
        "banned_words": [],
        "freshness_score": 100,
        "format_id": "viral_curiosity_24s",
        "target_length_seconds": 24,
        "hard_min_duration_seconds": 18,
        "hard_max_duration_seconds": 32,
        "scene_plan": [{"scene_id": i, "time_range": f"0:{i*2:02d} - 0:{(i+1)*2:02d}", "visual": "visual", "audio": "audio", "movement": "zoom"} for i in range(12)],
        "text_overlay_plan": [{"time_range": "0:00 - 0:01", "text": "text"}],
        "safety_rules": ["no copyright issues"]
    })
    assert res_code == 1, "Expected quality gate to fail for copyrighted character"
    assert any("Copyrighted character" in r for r in report_data["reasons"]), "Expected copyright failure reason"
    print("Verification: Hook greetings and copyrighted character checks failed as expected.")

    # 4. Test Duration Validation Logic (Below 18 fails, above 32 fails, 20-30 passes, 10 fails)
    def validate_duration_checks(actual_dur, hard_m=18, hard_mx=32, pref_m=20, pref_mx=30, target_dur=24):
        warnings_list = []
        if actual_dur < hard_m or actual_dur > hard_mx:
            return "failed", f"Duration {actual_dur}s is outside hard limits"
        if actual_dur < pref_m or actual_dur > pref_mx:
            warnings_list.append("outside preferred range")
        if abs(actual_dur - target_dur) > 8.0:
            warnings_list.append("differs from target by > 8s")
        status = "warning" if warnings_list else "passed"
        return status, "; ".join(warnings_list)

    # Actual duration 10 fails
    status, msg = validate_duration_checks(10.0)
    assert status == "failed", "Expected 10.0s to fail duration checks"
    
    # Actual duration 17.5 fails (below 18)
    status, msg = validate_duration_checks(17.5)
    assert status == "failed", "Expected 17.5s to fail duration checks"
    
    # Actual duration 33.0 fails (above 32)
    status, msg = validate_duration_checks(33.0)
    assert status == "failed", "Expected 33.0s to fail duration checks"
    
    # Actual duration 24.5 passes (between 20-30)
    status, msg = validate_duration_checks(24.5)
    assert status == "passed", f"Expected 24.5s to pass duration checks, got {status}: {msg}"
    
    # Actual duration 19.0 warning (outside preferred 20-30 but inside hard 18-32)
    status, msg = validate_duration_checks(19.0)
    assert status == "warning", f"Expected 19.0s to warn, got {status}: {msg}"
    
    # Re-run brief builder to restore the correct brief for history writeback tests
    run_cmd([sys.executable, "scripts/build_video_brief.py"])
    with open(brief_file, "r", encoding="utf-8") as f:
        brief = json.load(f)

    # 9. Test History Writeback
    print("\n--- Testing History Writeback ---")
    
    # Save original content history
    history_file = "docs/content-history.json"
    original_history = []
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            original_history = json.load(f)
            
    # Create a mock youtube-result.json
    yt_mock_res = {
        "youtube_video_id": "mock_test_video_999",
        "youtube_status": "success",
        "youtube_error": ""
    }
    with open("youtube-result.json", "w", encoding="utf-8") as f:
        json.dump(yt_mock_res, f)
        
    # (a) Run with ALLOW_MOCK_HISTORY=false (should skip writeback)
    env_no_history = env.copy()
    env_no_history["ALLOW_MOCK_HISTORY"] = "false"
    run_cmd([sys.executable, "scripts/update_content_history.py"], env_override=env_no_history)
    
    # Verify no change occurred
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            current_history = json.load(f)
        assert len(current_history) == len(original_history), "History was modified when ALLOW_MOCK_HISTORY=false!"
    print("Verification: History writeback skipped mock upload successfully by default.")

    # (b) Run with ALLOW_MOCK_HISTORY=true (should write back)
    env_with_history = env.copy()
    env_with_history["ALLOW_MOCK_HISTORY"] = "true"
    run_cmd([sys.executable, "scripts/update_content_history.py"], env_override=env_with_history)
    
    # Verify change occurred and mock video ID is recorded
    with open(history_file, "r", encoding="utf-8") as f:
        current_history = json.load(f)
    assert len(current_history) == len(original_history) + 1, "History was not updated when ALLOW_MOCK_HISTORY=true!"
    assert current_history[-1]["youtube_video_id"] == "mock_test_video_999", "Incorrect video ID in written history!"
    assert current_history[-1]["idea_id"] == brief["idea_id"], "Incorrect idea ID in written history!"
    print("Verification: History writeback wrote mock upload successfully when ALLOW_MOCK_HISTORY=true.")

    # Restore original content history
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(original_history, f, indent=2)
    print("Restored original docs/content-history.json.")

    # Clean up mock youtube result
    if os.path.exists("youtube-result.json"):
        os.remove("youtube-result.json")

    # 10. Test Analytics Loop
    print("\n--- Testing Analytics Loop ---")
    # Save current docs/content-history.json
    original_history_for_analytics = []
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            original_history_for_analytics = json.load(f)
            
    # Write a mock history with a mix of real-looking IDs, mock IDs, and empty IDs
    mock_history_for_analytics = [
        {
            "idea_id": "idea_test_1",
            "youtube_video_id": "pJ0zoo0nPAY",  # Real-looking
            "topic": "Topic 1"
        },
        {
            "idea_id": "idea_test_2",
            "youtube_video_id": "mock_yt_123",  # Mock ID
            "topic": "Topic 2"
        },
        {
            "idea_id": "idea_test_3",
            "youtube_video_id": "",             # Empty
            "topic": "Topic 3"
        }
    ]
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(mock_history_for_analytics, f, indent=2)
        
    # Run fetch analytics script in mock mode
    env_analytics = env.copy()
    env_analytics["MOCK_MODE"] = "true"
    run_cmd([sys.executable, "scripts/fetch_youtube_analytics.py"], env_override=env_analytics)
    
    # Load and verify history changes
    with open(history_file, "r", encoding="utf-8") as f:
        updated_history = json.load(f)
        
    # All entries must have an analytics block
    for entry in updated_history:
        assert "analytics" in entry, "Expected entry to have 'analytics' dictionary"
        assert isinstance(entry["analytics"], dict), "Expected 'analytics' to be a dictionary"
        
    # Entry 1 (real-looking video id) must have simulated stats
    entry1 = next(i for i in updated_history if i["idea_id"] == "idea_test_1")
    assert entry1["analytics"]["views"] == 420, "Expected views to be updated to 420"
    assert entry1["analytics"]["likes"] == 69, "Expected likes to be updated to 69"
    assert entry1["analytics"]["comments"] == 7, "Expected comments to be updated to 7"
    assert entry1["analytics"]["privacy"] == "private", "Expected privacy to be updated"
    assert entry1["analytics"]["checked_at"] is not None, "Expected checked_at to be populated"
    assert entry1["analytics"]["source"] == "mock", f"Expected source to be 'mock', got {entry1['analytics'].get('source')}"
    
    # Entry 2 (mock video id) should not be updated with live stats (remains default null)
    entry2 = next(i for i in updated_history if i["idea_id"] == "idea_test_2")
    assert entry2["analytics"]["views"] is None, "Expected mock ID views to remain None"
    assert entry2["analytics"]["checked_at"] is None, "Expected mock ID checked_at to remain None"
    assert entry2["analytics"]["source"] == "not_checked", f"Expected source to be 'not_checked', got {entry2['analytics'].get('source')}"
    
    # Entry 3 (empty video id) should not be updated
    entry3 = next(i for i in updated_history if i["idea_id"] == "idea_test_3")
    assert entry3["analytics"]["views"] is None, "Expected empty ID views to remain None"
    assert entry3["analytics"]["source"] == "not_checked", f"Expected source to be 'not_checked', got {entry3['analytics'].get('source')}"
    
    # Restore original content history
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(original_history_for_analytics, f, indent=2)
    print("Verification: Analytics loop testing passed and content history restored.")

    # === TEST RETENTION STORYBOARD AND POST-PROCESSING ===
    print("\n--- Testing Retention Storyboard and Post-Processing ---")
    
    # 1. Test Storyboard Generation
    run_cmd([sys.executable, "scripts/build_retention_storyboard.py"])
    storyboard_path = "docs/retention-storyboard.json"
    assert os.path.exists(storyboard_path), "Retention storyboard was not generated!"
    
    with open(storyboard_path, "r", encoding="utf-8") as f:
        storyboard = json.load(f)
        
    assert storyboard.get("format_id") == "viral_retention_engine_24s", "Expected format_id to be viral_retention_engine_24s"
    assert 14 <= len(storyboard["scenes"]) <= 24, f"Expected 14-24 scenes, got {len(storyboard['scenes'])}"
    
    for s in storyboard["scenes"]:
        dur = get_scene_duration(s["time_range"])
        assert dur <= 1.5, f"Scene duration {dur}s exceeds 1.5s max: {s['time_range']}"
        
    for o in storyboard["text_overlays"]:
        words = o["text"].split()
        assert 1 <= len(words) <= 4, f"Text overlay words count {len(words)} outside [1, 4]: '{o['text']}'"
        
    assert len(storyboard.get("hook_0_3s", "").strip()) > 0, "Hook missing or empty in storyboard"
    assert len(storyboard.get("sound_cues", [])) > 0, "No sound cues found in storyboard"
    for sc in storyboard["sound_cues"]:
        assert sc.get("effect"), "Sound cue effect is empty"
    assert len(storyboard.get("camera_motion", [])) > 0, "No camera motion cues found in storyboard"
    
    print("Verification: Retention storyboard generated successfully with valid format specs.")

    # Backup the valid storyboard
    sb_backup = storyboard.copy()

    def check_storyboard(sb_data):
        with open(storyboard_path, "w", encoding="utf-8") as f:
            json.dump(sb_data, f, indent=2)
        res = subprocess.run([sys.executable, "scripts/quality_gate.py"], capture_output=True, text=True)
        with open("docs/quality-report.json", "r", encoding="utf-8") as f:
            report_data = json.load(f)
        return res.returncode, report_data

    try:
        # 2. Test Hook greeting failure on storyboard
        bad_sb = sb_backup.copy()
        bad_sb["hook_0_3s"] = "Hey this is my hook"
        res_code, report_data = check_storyboard(bad_sb)
        assert res_code == 1, "Expected storyboard quality gate to fail for hook starting with greeting"
        assert any("starts with a greeting" in r for r in report_data["reasons"]), "Expected greeting failure reason"

        # 3. Test Copyright failure on storyboard
        bad_sb = sb_backup.copy()
        bad_scenes = [s.copy() for s in sb_backup["scenes"]]
        bad_scenes[0]["visual_prompt"] = "Visual showing mickey mouse on screen"
        bad_sb["scenes"] = bad_scenes
        res_code, report_data = check_storyboard(bad_sb)
        assert res_code == 1, "Expected storyboard quality gate to fail for copyrighted character"
        assert any("copyrighted character" in r.lower() or "disney" in r.lower() for r in report_data["reasons"]), "Expected copyright failure reason"

        # 4. Test Filler words failure on storyboard
        bad_sb = sb_backup.copy()
        bad_sb["narration_script"] = ["Step 1.", "Basically this is a test.", "Step 2."]
        res_code, report_data = check_storyboard(bad_sb)
        assert res_code == 1, "Expected storyboard quality gate to fail for filler words"
        assert any("contains filler words" in r for r in report_data["reasons"]), "Expected filler words failure reason"

        # 5. Test Overlay word count failure on storyboard
        bad_sb = sb_backup.copy()
        bad_sb["text_overlays"] = [{"start_time": 0.0, "end_time": 1.0, "text": "ONE TWO THREE FOUR FIVE"}]
        res_code, report_data = check_storyboard(bad_sb)
        assert res_code == 1, "Expected storyboard quality gate to fail for text overlay words > 4"
        assert any("overlay has more than 4 words" in r for r in report_data["reasons"]), "Expected overlay length failure reason"

        # 6. Test Scene count failure on storyboard
        bad_sb = sb_backup.copy()
        bad_scenes = [s.copy() for s in sb_backup["scenes"]]
        bad_sb["scenes"] = bad_scenes[:10]
        res_code, report_data = check_storyboard(bad_sb)
        assert res_code == 1, "Expected storyboard quality gate to fail for scene count < 14"
        assert any("scene count" in r.lower() and "below" in r.lower() for r in report_data["reasons"]), "Expected scene count failure reason"

        # 7. Test Static scene failure on storyboard
        bad_sb = sb_backup.copy()
        bad_scenes = [s.copy() for s in sb_backup["scenes"]]
        bad_scenes[0]["motion_instruction"] = ""
        bad_sb["scenes"] = bad_scenes
        res_code, report_data = check_storyboard(bad_sb)
        assert res_code == 1, "Expected storyboard quality gate to fail for missing camera motion"
        assert any("missing camera motion" in r for r in report_data["reasons"]), "Expected static scene failure reason"

    finally:
        # Restore the valid storyboard
        with open(storyboard_path, "w", encoding="utf-8") as f:
            json.dump(sb_backup, f, indent=2)
            
    print("Verification: Storyboard quality gate validations failed and warned as expected.")

    # 8. Test Post-processing script fallback and execution
    os.makedirs("storage/tasks/mock-task", exist_ok=True)
    test_mock_mp4 = "storage/tasks/mock-task/test-dummy.mp4"
    with open(test_mock_mp4, "wb") as f:
        f.write(b"0" * 500)
        
    run_cmd([sys.executable, "scripts/apply_retention_postprocess.py"])
    
    expected_retention_mp4 = "storage/tasks/mock-task/final-retention.mp4"
    assert os.path.exists(expected_retention_mp4), "Mock post-processed output was not created!"

    # 8b. Test mock synced storyboard was written
    synced_storyboard_path = "docs/retention-storyboard-synced.json"
    assert os.path.exists(synced_storyboard_path), "Mock synced storyboard was not created!"
    with open(synced_storyboard_path, "r", encoding="utf-8") as f:
        synced_sb = json.load(f)
    assert "alignment_stats" in synced_sb, "Synced storyboard missing alignment_stats"
    assert synced_sb["alignment_stats"].get("mode") == "mock", "Expected mock mode in alignment stats"
    print("Verification: Synced storyboard written correctly in mock mode.")
    
    if os.path.exists(test_mock_mp4):
        os.remove(test_mock_mp4)
    if os.path.exists(expected_retention_mp4):
        os.remove(expected_retention_mp4)
    if os.path.exists(synced_storyboard_path):
        os.remove(synced_storyboard_path)
        
    print("Verification: Post-processing script handled mock input and fallbacks gracefully.")

    # === TEST CONTENT ENGINE V1.8 SPECIFIC CHECKS ===
    print("\n--- Testing Content Engine v1.8 Formats and Validator ---")
    
    # 9. Blacklist check in storyboard query builder
    from build_retention_storyboard import sanitize_text
    assert "follow" in sanitize_text("please subscribe to my channel").lower()
    assert "modern desk workspace" in sanitize_text("working in a random office").lower()
    print("Verification: Blacklist sanitization functions correctly.")

    # 10. Test format validation success/failure cases
    # Setup a valid video-info.json for validation testing
    test_video_info = {
        "video_path": "storage/tasks/mock-task/final-retention.mp4",
        "duration": 24.0,
        "width": 1080,
        "height": 1920
    }
    with open("video-info.json", "w", encoding="utf-8") as f:
        json.dump(test_video_info, f, indent=2)

    # Re-create mock files
    os.makedirs("storage/tasks/mock-task", exist_ok=True)
    with open("storage/tasks/mock-task/final-retention.mp4", "wb") as f:
        f.write(b"0" * 150000)

    # Create logs with disable subtitle mode flag
    with open("moneyprinter-log.txt", "w", encoding="utf-8") as f:
        f.write("Executing MoneyPrinterTurbo cli.py with --no-subtitle-enabled flag")

    # Run validation (should pass)
    res_val = subprocess.run([sys.executable, "scripts/validate_retention_format.py"], env={"GENERATION_MODE": "real"})
    assert res_val.returncode == 0, f"Expected validator to pass on valid storyboard and logs, got code {res_val.returncode}"
    assert os.path.exists("docs/retention-contact-sheet.jpg"), "Contact sheet was not generated!"

    # Test Duplicate subtitle mode failure (if .srt exists in task directory)
    with open("storage/tasks/mock-task/subtitles.srt", "w", encoding="utf-8") as f:
        f.write("1\n00:00:01,000 --> 00:00:03,000\nHello World")

    res_val_srt = subprocess.run([sys.executable, "scripts/validate_retention_format.py"], capture_output=True, text=True)
    assert res_val_srt.returncode == 1, "Expected validator to fail when .srt exists in task directory"
    assert "Bottom subtitles are not allowed" in res_val_srt.stdout or "Bottom subtitles are not allowed" in res_val_srt.stderr

    # Clean up .srt file
    os.remove("storage/tasks/mock-task/subtitles.srt")

    # Test Subscribe overlay failure
    bad_sb = sb_backup.copy()
    bad_sb["text_overlays"] = [o.copy() for o in sb_backup["text_overlays"]]
    bad_sb["text_overlays"][0]["text"] = "SUBSCRIBE NOW"
    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(bad_sb, f, indent=2)
    res_val_sub = subprocess.run([sys.executable, "scripts/validate_retention_format.py"], capture_output=True, text=True)
    assert res_val_sub.returncode == 1, "Expected validator to fail for forbidden word 'subscribe' in overlay"
    assert "contains forbidden word" in res_val_sub.stdout or "contains forbidden word" in res_val_sub.stderr

    # Test Overlay word count failure
    bad_sb = sb_backup.copy()
    bad_sb["text_overlays"] = [o.copy() for o in sb_backup["text_overlays"]]
    bad_sb["text_overlays"][0]["text"] = "ONE TWO THREE FOUR FIVE"
    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(bad_sb, f, indent=2)
    res_val_word = subprocess.run([sys.executable, "scripts/validate_retention_format.py"], capture_output=True, text=True)
    assert res_val_word.returncode == 1, "Expected validator to fail for text overlay words > 4"
    assert "more than 4 words" in res_val_word.stdout or "more than 4 words" in res_val_word.stderr

    # Restore storyboard
    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(sb_backup, f, indent=2)

    # 11. Test visual blacklist in scene search query failure
    bad_sb = sb_backup.copy()
    bad_sb["scenes"] = [s.copy() for s in sb_backup["scenes"]]
    bad_sb["scenes"][0]["stock_search_query"] = "protest crowd"
    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(bad_sb, f, indent=2)
    res_val_blacklist = subprocess.run([sys.executable, "scripts/validate_retention_format.py"], capture_output=True, text=True)
    assert res_val_blacklist.returncode == 1, "Expected validator to fail for blacklisted term in query"
    assert "contains blacklisted term" in res_val_blacklist.stdout or "contains blacklisted term" in res_val_blacklist.stderr

    # Restore storyboard
    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(sb_backup, f, indent=2)

    # 12. Test missing storyboard fails when format is retention
    if os.path.exists(storyboard_path):
        os.rename(storyboard_path, storyboard_path + ".bak")
    try:
        res_val_missing_sb = subprocess.run([sys.executable, "scripts/validate_retention_format.py"], capture_output=True, text=True)
        assert res_val_missing_sb.returncode == 1, "Expected validator to fail when storyboard is missing during retention run"
        assert "Retention storyboard is missing" in res_val_missing_sb.stdout or "Retention storyboard is missing" in res_val_missing_sb.stderr
    finally:
        if os.path.exists(storyboard_path + ".bak"):
            os.rename(storyboard_path + ".bak", storyboard_path)

    # 13. Test missing postprocessed video fails for retention runs in real mode
    retention_mp4_path = "storage/tasks/mock-task/final-retention.mp4"
    if os.path.exists(retention_mp4_path):
        os.rename(retention_mp4_path, retention_mp4_path + ".bak")
    try:
        res_find_missing = subprocess.run([sys.executable, "scripts/find_latest_video.py"], env={"GENERATION_MODE": "real"}, capture_output=True, text=True)
        assert res_find_missing.returncode == 1, "Expected find_latest_video to fail when final-retention.mp4 is missing in real mode"
    finally:
        if os.path.exists(retention_mp4_path + ".bak"):
            os.rename(retention_mp4_path + ".bak", retention_mp4_path)

    # 14. Test final-retention.mp4 preference
    res_find = subprocess.run([sys.executable, "scripts/find_latest_video.py"], env={"GENERATION_MODE": "real"})
    assert res_find.returncode == 0
    with open("video-info.json", "r", encoding="utf-8") as f:
        v_info = json.load(f)
    assert v_info.get("video_path").endswith("final-retention.mp4"), "Expected video_path to point to final-retention.mp4"

    # 15. Test subtitle enabled in logs fails validation
    with open("moneyprinter-log.txt", "w", encoding="utf-8") as f:
        f.write("Executing MoneyPrinterTurbo cli.py with subtitles enabled")
    res_val_log_fail = subprocess.run([sys.executable, "scripts/validate_retention_format.py"], env={"GENERATION_MODE": "real"}, capture_output=True, text=True)
    assert res_val_log_fail.returncode == 1, "Expected validator to fail when --no-subtitle-enabled is missing in logs"
    
    # Restore valid logs
    with open("moneyprinter-log.txt", "w", encoding="utf-8") as f:
        f.write("Executing MoneyPrinterTurbo cli.py with --no-subtitle-enabled flag")

    # Clean up test task directory files and temporary test logs
    if os.path.exists("storage/tasks/mock-task/final-retention.mp4"):
        os.remove("storage/tasks/mock-task/final-retention.mp4")
    if os.path.exists("docs/retention-contact-sheet.jpg"):
        os.remove("docs/retention-contact-sheet.jpg")
    if os.path.exists("moneyprinter-log.txt"):
        os.remove("moneyprinter-log.txt")

    # === TEST CONTENT ENGINE v2.0 — AUDIO-SYNCED RETENTION COMPOSITOR ===
    print("\n--- Testing v2.0 TTS Timestamp Extraction (Mock) ---")

    # 16. Test TTS timestamp extraction in mock mode
    os.makedirs("storage/tasks/mock-task", exist_ok=True)
    with open("storage/tasks/mock-task/test-tts.mp4", "wb") as f:
        f.write(b"0" * 500)

    run_cmd([sys.executable, "scripts/extract_tts_timestamps.py"], env_override={"GENERATION_MODE": "mock"})

    tts_path = "docs/tts-timestamps.json"
    assert os.path.exists(tts_path), "TTS timestamps file was not created in mock mode!"
    with open(tts_path, "r", encoding="utf-8") as f:
        tts_data = json.load(f)
    assert tts_data.get("mode") == "mock", "Expected mock mode in TTS timestamps"
    assert "words" in tts_data, "TTS timestamps missing 'words' field"
    assert len(tts_data["words"]) > 0, "TTS timestamps has no words"
    assert "total_duration" in tts_data, "TTS timestamps missing 'total_duration'"
    print(f"TTS mock extraction: {tts_data['word_count']} words, {tts_data['total_duration']}s duration")
    print("Verification: TTS timestamp extraction works correctly in mock mode.")

    # 17. Test background music mixer bypass in mock mode
    print("\n--- Testing v2.0 Background Music Mixer (Mock) ---")
    run_cmd([sys.executable, "scripts/mix_retention_audio.py"], env_override={"GENERATION_MODE": "mock"})

    pre_overlay_path = "storage/tasks/mock-task/pre-overlay.mp4"
    assert os.path.exists(pre_overlay_path), "pre-overlay.mp4 was not created in mock mode!"
    print("Verification: Background music mixer bypasses correctly in mock mode.")

    # 18. Test audio-synced overlay compositor in mock mode
    print("\n--- Testing v2.0 Audio-Synced Overlay Compositor (Mock) ---")
    run_cmd([sys.executable, "scripts/apply_retention_postprocess.py"], env_override={"GENERATION_MODE": "mock"})

    final_ret_path = "storage/tasks/mock-task/final-retention.mp4"
    assert os.path.exists(final_ret_path), "final-retention.mp4 was not created in mock compositor!"

    synced_sb_path = "docs/retention-storyboard-synced.json"
    assert os.path.exists(synced_sb_path), "Synced storyboard was not created in mock compositor!"
    with open(synced_sb_path, "r", encoding="utf-8") as f:
        synced_sb = json.load(f)
    assert "alignment_stats" in synced_sb, "Synced storyboard missing alignment_stats"
    assert "text_overlays_synced" in synced_sb, "Synced storyboard missing text_overlays_synced"
    print("Verification: Audio-synced overlay compositor works correctly in mock mode.")

    # 19. Test narration-derived B-roll query extraction
    print("\n--- Testing v2.0 Narration-Derived B-Roll Queries ---")
    if os.path.exists(storyboard_path):
        with open(storyboard_path, "r", encoding="utf-8") as f:
            sb_check = json.load(f)
        scenes = sb_check.get("scenes", [])
        narr_derived_count = 0
        for s in scenes:
            if s.get("narration_derived_query"):
                narr_derived_count += 1
            assert "narration_derived_query" in s, f"Scene {s.get('scene_id')} missing narration_derived_query"
            assert "preset_fallback_query" in s, f"Scene {s.get('scene_id')} missing preset_fallback_query"
        print(f"Narration-derived queries present in {narr_derived_count}/{len(scenes)} scenes")
        print("Verification: Narration-derived B-roll query fields are present in storyboard.")

    # Clean up v2.0 test artifacts
    for cleanup_path in [
        "storage/tasks/mock-task/test-tts.mp4",
        "storage/tasks/mock-task/pre-overlay.mp4",
        "storage/tasks/mock-task/final-retention.mp4",
        "docs/tts-timestamps.json",
        "docs/retention-storyboard-synced.json"
    ]:
        if os.path.exists(cleanup_path):
            os.remove(cleanup_path)

    print("\n=== ALL LOCAL INTEGRATION TESTS PASSED SUCCESSFULLY ===")

if __name__ == '__main__':
    main()
