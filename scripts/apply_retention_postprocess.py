import os
import sys
import json
import subprocess
import glob
import shutil
import re


def get_system_font():
    # Candidates for Linux, Windows, and macOS
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "C\\:/Windows/Fonts/arialbd.ttf",
        "C\\:/Windows/Fonts/arial.ttf",
        "C\\:/Windows/Fonts/tahoma.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    for c in candidates:
        unescaped = c.replace("C\\:", "C:").replace("\\", "/")
        if os.path.exists(unescaped):
            return c
    return None


def normalize_word(word):
    """Normalize a word for fuzzy matching: lowercase, strip punctuation."""
    return re.sub(r'[^a-z0-9]', '', word.lower().strip())


def match_overlays_to_tts(overlays, tts_words, duration):
    """
    Match each overlay's words to TTS word-level timestamps.
    Returns a list of re-timed overlays with start/end from actual TTS audio.
    """
    synced_overlays = []
    tts_index = 0  # tracks position in TTS words for sequential matching

    # First pass: find exact matches and set to None if unmatched
    for overlay in overlays:
        text = overlay.get("text", "")
        overlay_words = text.split()
        if not overlay_words:
            # Keep original timing for empty overlays
            synced_overlay = dict(overlay)
            synced_overlay["start_time"] = round(float(overlay.get("start_time", 0.0)), 3)
            synced_overlay["end_time"] = round(float(overlay.get("end_time", 0.5)), 3)
            synced_overlay["matched_words"] = 0
            synced_overlay["total_words"] = 0
            synced_overlays.append(synced_overlay)
            continue

        matched_starts = []
        matched_ends = []

        for ow in overlay_words:
            norm_ow = normalize_word(ow)
            if not norm_ow:
                continue

            # Search forward from current tts_index for a matching word
            best_match = None
            best_distance = float('inf')

            # Search window: from current position to +20 words ahead
            search_start = max(0, tts_index - 3)
            search_end = min(len(tts_words), tts_index + 20)

            for i in range(search_start, search_end):
                tts_norm = normalize_word(tts_words[i].get("word", ""))
                if tts_norm == norm_ow:
                    distance = abs(i - tts_index)
                    if distance < best_distance:
                        best_match = i
                        best_distance = distance

            if best_match is not None:
                matched_starts.append(tts_words[best_match]["start"])
                matched_ends.append(tts_words[best_match]["end"])
                # Advance tts_index past the matched word
                tts_index = best_match + 1

        synced_overlay = dict(overlay)
        if matched_starts and matched_ends:
            # Re-time: use actual TTS boundaries + small hold time
            new_start = min(matched_starts)
            new_end = max(matched_ends) + 0.1  # 100ms hold after last word
            synced_overlay["start_time"] = round(new_start, 3)
            synced_overlay["end_time"] = round(new_end, 3)
            synced_overlay["matched_words"] = len(matched_starts)
        else:
            synced_overlay["start_time"] = None
            synced_overlay["end_time"] = None
            synced_overlay["matched_words"] = 0
            
        synced_overlay["total_words"] = len([w for w in overlay_words if normalize_word(w)])
        synced_overlays.append(synced_overlay)

    # Second pass: interpolate unmatched overlays to prevent gaps/overlaps/out-of-order timings
    idx = 0
    n = len(synced_overlays)
    while idx < n:
        if synced_overlays[idx]["start_time"] is None:
            # Found a group of contiguous unmatched overlays
            group_start_idx = idx
            while idx < n and synced_overlays[idx]["start_time"] is None:
                idx += 1
            group_end_idx = idx
            num_unmatched = group_end_idx - group_start_idx
            
            # Find bounds
            prev_end = 0.0
            if group_start_idx > 0:
                prev_end = synced_overlays[group_start_idx - 1]["end_time"]
                
            next_start = duration
            # Find the next matched one
            for j in range(group_end_idx, n):
                if synced_overlays[j]["start_time"] is not None:
                    next_start = synced_overlays[j]["start_time"]
                    break
                    
            # Interpolate
            gap_duration = next_start - prev_end
            margin = 0.05
            usable_duration = gap_duration - (2 * margin)
            
            if usable_duration > 0:
                share = usable_duration / num_unmatched
                for k in range(num_unmatched):
                    curr_idx = group_start_idx + k
                    new_start = prev_end + margin + (k * share)
                    new_end = new_start + share
                    synced_overlays[curr_idx]["start_time"] = round(new_start, 3)
                    synced_overlays[curr_idx]["end_time"] = round(new_end, 3)
            else:
                # Squeeze them into tiny non-overlapping intervals
                share = max(0.01, gap_duration / max(1, num_unmatched))
                for k in range(num_unmatched):
                    curr_idx = group_start_idx + k
                    new_start = prev_end + (k * share)
                    new_end = new_start + share
                    synced_overlays[curr_idx]["start_time"] = round(new_start, 3)
                    synced_overlays[curr_idx]["end_time"] = round(new_end, 3)
        else:
            idx += 1

    return synced_overlays


def compute_alignment_stats(synced_overlays):
    """Compute alignment coverage and drift statistics."""
    total_overlay_words = 0
    total_matched = 0
    drifts = []

    for ov in synced_overlays:
        if ov.get("is_filler", False):
            continue
        total_overlay_words += ov.get("total_words", 0)
        total_matched += ov.get("matched_words", 0)

    coverage = (total_matched / max(total_overlay_words, 1)) * 100.0
    return {
        "total_overlay_words": total_overlay_words,
        "total_matched_words": total_matched,
        "alignment_coverage_pct": round(coverage, 1)
    }


def main():
    print("--- Running Audio-Synced Retention Post-Processing ---")

    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    if not os.path.exists(storyboard_path):
        print("No retention storyboard found. Skipping post-processing.")
        sys.exit(0)

    try:
        with open(storyboard_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
    except Exception as e:
        print(f"Error reading storyboard: {e}")
        sys.exit(1)

    if sb.get("format_id") != "viral_retention_engine_24s":
        print("Storyboard format is not viral_retention_engine_24s. Skipping post-processing.")
        sys.exit(0)

    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()

    # Explicit safety check: bottom subtitles must remain disabled.
    # If MPT was run with subtitles enabled, we'd have two caption channels
    # (bottom paragraphs + center overlays) which is the dual-channel bug.
    if generation_mode == "real":
        log_path = "moneyprinter-log.txt"
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as lf:
                    log_content = lf.read()
                if "--no-subtitle-enabled" not in log_content:
                    print("Error: Bottom subtitles are NOT disabled (--no-subtitle-enabled missing from MPT logs).")
                    print("This would create a dual-caption-channel video. Aborting post-processing.")
                    sys.exit(1)
                print("[REAL] Confirmed: bottom subtitles disabled (--no-subtitle-enabled present in MPT logs).")
            except Exception as e:
                print(f"Warning: Could not verify subtitle state from logs: {e}")

    # Scan for input video — prefer pre-overlay.mp4 (from music mixer), fallback to raw MPT output
    search_pattern = os.path.join("storage", "tasks", "**", "*.mp4")
    files = glob.glob(search_pattern, recursive=True)
    files = [f for f in files if not f.endswith("final-retention.mp4")]

    # Prefer pre-overlay.mp4 if it exists (has background music mixed in)
    pre_overlay_files = [f for f in files if f.endswith("pre-overlay.mp4")]
    other_files = [f for f in files if not f.endswith("pre-overlay.mp4")]

    if pre_overlay_files:
        pre_overlay_files.sort(key=os.path.getmtime, reverse=True)
        input_video = pre_overlay_files[0]
        print(f"Using pre-overlay (music-mixed) video: {input_video}")
    elif other_files:
        other_files.sort(key=os.path.getmtime, reverse=True)
        input_video = other_files[0]
        print(f"Using raw MPT video (no music mixer output found): {input_video}")
    else:
        print("Error: No input MP4 files found for post-processing.")
        sys.exit(1)

    file_size_kb = os.path.getsize(input_video) / 1024
    print(f"Input video: {input_video} ({file_size_kb:.2f} KB)")

    output_video = os.path.join(os.path.dirname(input_video), "final-retention.mp4")
    is_mock = generation_mode == "mock" or file_size_kb < 100

    # --- MOCK MODE ---
    if is_mock:
        print("[MOCK] Mock mode or dummy file detected. Bypassing ffmpeg post-processing.")
        try:
            shutil.copy2(input_video, output_video)
            print(f"[MOCK] Copied mock video to {output_video}")

            # Still write synced storyboard for validation in mock
            overlays = sb.get("text_overlays", [])
            synced_storyboard = dict(sb)
            synced_storyboard["text_overlays_synced"] = overlays
            synced_storyboard["alignment_stats"] = {
                "total_overlay_words": 0,
                "total_matched_words": 0,
                "alignment_coverage_pct": 0.0,
                "caption_overlap_count": 0,
                "mode": "mock"
            }
            synced_path = os.path.join("docs", "retention-storyboard-synced.json")
            with open(synced_path, "w", encoding="utf-8") as f:
                json.dump(synced_storyboard, f, indent=2)
            print(f"[MOCK] Wrote mock synced storyboard to {synced_path}")

            sys.exit(0)
        except Exception as e:
            print(f"Failed to copy mock file: {e}")
            sys.exit(1)

    # --- REAL MODE ---
    print("[REAL] Running audio-synced overlay compositor...")

    overlays = sb.get("text_overlays", [])
    if not overlays:
        print("Error: No text overlays defined in storyboard.")
        sys.exit(1)

    # Load TTS timestamps for audio-synced re-timing
    tts_path = os.path.join("docs", "tts-timestamps.json")
    tts_words = []
    if os.path.exists(tts_path):
        try:
            with open(tts_path, "r", encoding="utf-8") as f:
                tts_data = json.load(f)
            tts_words = tts_data.get("words", [])
            print(f"[REAL] Loaded {len(tts_words)} TTS word timestamps for audio sync.")
        except Exception as e:
            print(f"Warning: Could not read TTS timestamps: {e}. Using storyboard timing.")
    else:
        print("Warning: docs/tts-timestamps.json not found. Using storyboard fixed-grid timing.")

    # Re-time overlays to TTS audio boundaries
    if tts_words:
        last_word_end = max([w["end"] for w in tts_words]) if tts_words else 0.0
        print("[REAL] Matching overlay words to TTS timestamps for audio sync...")
        synced_overlays = match_overlays_to_tts(overlays, tts_words, duration=last_word_end)
        
        # Shift and filter filler overlays to prevent visual overlap/double exposure
        print(f"[REAL] Narration ends at {last_word_end:.3f}s. Adjusting filler overlays...")
        
        adjusted_overlays = []
        filler_count = 0
        for ov in synced_overlays:
            if ov.get("is_filler", False):
                new_start = last_word_end + (filler_count * 0.5)
                new_end = new_start + 0.5
                ov["start_time"] = round(new_start, 3)
                ov["end_time"] = round(new_end, 3)
                filler_count += 1
            adjusted_overlays.append(ov)
        synced_overlays = adjusted_overlays
        
        # Resolve caption overlaps (v2.1a)
        caption_overlap_count = 0
        active_overlays = [ov for ov in synced_overlays if ov.get("text", "").strip() != ""]
        for i in range(len(active_overlays) - 1):
            curr = active_overlays[i]
            nxt = active_overlays[i+1]
            curr_end = curr.get("end_time", 0.0)
            nxt_start = nxt.get("start_time", 0.0)
            if curr_end > nxt_start + 0.02:
                caption_overlap_count += 1
                curr["end_time"] = round(max(curr.get("start_time", 0.0) + 0.01, nxt_start - 0.03), 3)
                
        print(f"[REAL] Resolved {caption_overlap_count} caption overlaps.")
        
        stats = compute_alignment_stats(synced_overlays)
        # Calculate actual unresolved overlaps remaining
        unresolved_overlap_count = 0
        for i in range(len(active_overlays) - 1):
            curr = active_overlays[i]
            nxt = active_overlays[i+1]
            curr_end = curr.get("end_time", 0.0)
            nxt_start = nxt.get("start_time", 0.0)
            if curr_end > nxt_start:
                unresolved_overlap_count += 1
        stats["caption_overlap_count"] = unresolved_overlap_count
        print(f"[REAL] Alignment coverage: {stats['alignment_coverage_pct']}% "
              f"({stats['total_matched_words']}/{stats['total_overlay_words']} words matched)")
    else:
        synced_overlays = overlays
        stats = {
            "total_overlay_words": 0,
            "total_matched_words": 0,
            "alignment_coverage_pct": 0.0,
            "caption_overlap_count": 0,
            "mode": "fallback_fixed_grid"
        }

    # Write the synced storyboard for audit
    synced_storyboard = dict(sb)
    synced_storyboard["text_overlays_synced"] = synced_overlays
    synced_storyboard["alignment_stats"] = stats
    synced_path = os.path.join("docs", "retention-storyboard-synced.json")
    try:
        with open(synced_path, "w", encoding="utf-8") as f:
            json.dump(synced_storyboard, f, indent=2)
        print(f"[REAL] Wrote audio-synced storyboard to {synced_path}")
    except Exception as e:
        print(f"Warning: Could not write synced storyboard: {e}")

    # Build ffmpeg drawtext filter graph using the synced overlay timestamps
    font_path = get_system_font()
    if not font_path:
        print("Warning: No system fonts found. Text overlays might fail.")

    filters = []
    font_clause = f"fontfile='{font_path}':" if font_path else ""

    for item in synced_overlays:
        text = item.get("text", "").replace("'", "\\'").replace(":", "\\:")
        start = float(item.get("start_time", 0.0))
        end = float(item.get("end_time", 0.0))

        if not text or end <= start:
            continue

        # Center-screen overlay drawtext filter with large bold styling
        f_str = (
            f"drawtext={font_clause}"
            f"text='{text}':"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"fontsize=72:fontcolor=white:"
            f"borderw=4:bordercolor=black:"
            f"shadowcolor=black:shadowx=4:shadowy=4:"
            f"enable='between(t\\,{start:.3f}\\,{end:.3f})'"
        )
        filters.append(f_str)

    if not filters:
        print("Warning: No valid overlay filters generated. Copying video as-is.")
        shutil.copy2(input_video, output_video)
        sys.exit(0)

    filter_graph = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", filter_graph,
        "-codec:a", "copy",
        output_video
    ]

    print(f"Executing ffmpeg post-processing with {len(filters)} overlay filters...")
    print(f"Output: {output_video}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Successfully completed audio-synced overlay rendering! Output: {output_video}")
            sys.exit(0)
        else:
            print(f"Error: ffmpeg post-processing failed with exit code {res.returncode}.")
            print("stderr:", res.stderr[:1000])
            sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to execute post-processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
