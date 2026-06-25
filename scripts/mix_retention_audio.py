"""
Retention Audio Mixer — v2.0a pass-through.

In v2.0a this script is a deliberate no-op: it copies the raw MPT output
to pre-overlay.mp4 so the downstream compositor has a consistent input path.

Background music mixing (suspense loops, mood-based track selection,
loudnorm-based level matching) is deferred to v2.0b, which requires
committing curated CC0 music assets and resolving mood-to-content mapping.

When v2.0b ships, this script will:
  - Select a music loop from assets/music/ based on content category/mood
  - Loop it to match video duration
  - Run ffmpeg loudnorm to match integrated LUFS (not a flat dB offset)
  - Mix under the TTS narration track
  - Output to pre-overlay.mp4
"""

import os
import sys
import json
import glob
import shutil


def main():
    print("--- Running Retention Audio Mixer (v2.0a pass-through) ---")

    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    if not os.path.exists(storyboard_path):
        print("No retention storyboard found. Skipping audio mixing.")
        sys.exit(0)

    try:
        with open(storyboard_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
    except Exception as e:
        print(f"Error reading storyboard: {e}")
        sys.exit(1)

    if sb.get("format_id") != "viral_retention_engine_24s":
        print("Storyboard format is not viral_retention_engine_24s. Skipping audio mixing.")
        sys.exit(0)

    # Locate the MPT output video
    search_pattern = os.path.join("storage", "tasks", "**", "*.mp4")
    files = glob.glob(search_pattern, recursive=True)
    files = [f for f in files if not f.endswith("final-retention.mp4") and not f.endswith("pre-overlay.mp4")]

    if not files:
        print("Error: No input MP4 files found for audio mixing.")
        sys.exit(1)

    files.sort(key=os.path.getmtime, reverse=True)
    input_video = files[0]
    output_video = os.path.join(os.path.dirname(input_video), "pre-overlay.mp4")

    file_size_kb = os.path.getsize(input_video) / 1024
    print(f"Input video: {input_video} ({file_size_kb:.2f} KB)")

    # v2.0a: pass-through — copy input to pre-overlay.mp4 without music mixing.
    # Background music mixing is deferred to v2.0b.
    print("[v2.0a] Music mixing deferred to v2.0b. Copying input to pre-overlay.mp4.")
    try:
        shutil.copy2(input_video, output_video)
        print(f"Copied to {output_video}")
    except Exception as e:
        print(f"Error copying file: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
