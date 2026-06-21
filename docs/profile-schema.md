# Content Profile Schema Specification

This document defines the schema structure used by the Content Engine v1 profiles (stored in `profiles/*.yml`). These profiles parameterize the idea generator, freshness scorer, brief builder, and quality gate.

## Schema Fields

### `profile_id`
- **Type**: String (Unique, Alphanumeric)
- **Description**: The machine identifier for the profile. Matches the filename (e.g. `ai_tools`).
- **Example**: `ai_tools`

### `display_name`
- **Type**: String
- **Description**: The human-readable name of the channel or page profile.
- **Example**: `"AI Tools & Productivity Hacks"`

### `niche`
- **Type**: String
- **Description**: The general category or theme. Used by the idea generator to pull niche-specific topics.
- **Example**: `ai`

### `tone`
- **Type**: List of Strings
- **Description**: Adjectives describing the voice and attitude of the script and narration.
- **Example**: `["energetic", "educational", "fast-paced"]`

### `audience`
- **Type**: List of Strings
- **Description**: The target demographics and user types intended for the content.
- **Example**: `["content creators", "tech-savvy professionals"]`

### `content_types`
- **Type**: List of Strings
- **Description**: Allowed content structures/formats that this profile supports.
- **Example**: `["list_top_3", "one_tool_highlight", "tutorial"]`

### `avoid`
- **Type**: List of Strings
- **Description**: Rules defining concepts, topics, or practices to stay away from.
- **Example**: `["outdated tool versions", "promo code scams"]`

### `style`
- **Type**: Map/Dictionary
- **Description**: Visual and auditory stylistic requirements.
  - `visuals`: Directions for editing, footage, overlays, and subtitle styles.
  - `audio`: Guidelines for pacing, narration style, background music, and sounds.
- **Example**:
  ```yaml
  style:
    visuals:
      - high hook focus (first 3 seconds)
      - caption animations
    audio:
      - voiceover first
  ```

### `sources`
- **Type**: List of Strings
- **Description**: Recommended content platforms, forums, or portals where content is sourced or verified.
- **Example**: `["ProductHunt", "HackerNews", "Reddit"]`

### `safety_rules`
- **Type**: List of Strings
- **Description**: Regulatory, compliance, and strict safety guidelines that the content must adhere to.
- **Example**: `["no financial advice", "verify tool legality", "keep video length under 60 seconds"]`

### `banned_words`
- **Type**: List of Strings
- **Description**: Specific terms, phrases, or clickbait trigger words that are strictly prohibited in the script, title, or tags.
- **Example**: `["scam", "cheat", "hack", "illegal"]`

### `format_preset`
- **Type**: String (Path to format YAML file)
- **Description**: Points to a reusable format configuration preset defining aspect ratios, duration targets, structural beats, overlay, editing rhythm, narration flow, and safety parameters.
- **Example**: `formats/viral_curiosity_24s.yml`

### `preferred_duration_seconds`
- **Type**: Integer
- **Description**: Target duration of the generated video output in seconds.
- **Example**: `24`

### `hard_min_duration_seconds`
- **Type**: Integer
- **Description**: The absolute lower limit for video duration. Values below this trigger a pipeline failure.
- **Example**: `18`

### `hard_max_duration_seconds`
- **Type**: Integer
- **Description**: The absolute upper limit for video duration. Values above this trigger a pipeline failure.
- **Example**: `32`

