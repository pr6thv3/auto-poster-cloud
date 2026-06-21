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

def main():
    print("=== STARTING LOCAL INTEGRATION TESTS ===")

    # 1. Clear any old build/output files
    files_to_clear = [
        "docs/generated-ideas.json",
        "docs/scored-ideas.json",
        "docs/video-brief.json",
        "docs/quality-report.json",
        "youtube-metadata.json",
        "run-log.json",
        "platform-results.json",
        "step-summary-mock.md"
    ]
    for f in files_to_clear:
        if os.path.exists(f):
            os.remove(f)

    # 2. Run the Content Engine steps locally
    print("\n--- Running Content Engine Steps ---")
    run_cmd([sys.executable, "scripts/generate_ideas.py", "--profile", "profiles/ai_tools.yml"])
    run_cmd([sys.executable, "scripts/score_idea_freshness.py"])
    run_cmd([sys.executable, "scripts/build_video_brief.py"])
    run_cmd([sys.executable, "scripts/quality_gate.py"])

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
    assert run_log.get("quality_status") == "passed", "quality_status does not match in run-log.json"

    print("Verification: run-log.json includes correct Content Engine Audit properties!")

    # 8. Read step summary mock
    with open("step-summary-mock.md", "r", encoding="utf-8") as f:
        summary_text = f.read()
    print("\nMock Step Summary Markdown content:")
    print(summary_text)

    assert "Content Engine Audit" in summary_text, "Content Engine Audit section missing in step summary markdown"
    assert f"**Use Video Brief**: `True`" in summary_text, "Use Video Brief field missing or incorrect in step summary markdown"
    assert f"**Profile ID**: `{brief.get('profile_id')}`" in summary_text, "Profile ID field incorrect in step summary markdown"
    assert "**Quality Gate Status**: `PASSED`" in summary_text, "Quality Gate Status incorrect in step summary markdown"

    print("Verification: step-summary-mock.md contains the correct Content Engine Audit markdown section!")

    print("\n=== ALL LOCAL INTEGRATION TESTS PASSED SUCCESSFULLY ===")

if __name__ == '__main__':
    main()
