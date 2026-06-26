# Proof Asset Metadata Schema

Proof assets are cataloged in `assets/proof_capture/proof_assets.json`. Below is the schema specification and field descriptions.

## Schema Fields

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `asset_id` | `string` | Unique identifier (e.g., `calendar_agent_demo_001`). |
| `file_path` | `string` | Absolute or relative path to the asset file in the workspace. |
| `project` | `string` | The project identifier (e.g. `calendar_agent`, `ai_tool_demo`). |
| `descriptor` | `string` | Clear textual description of the visual action shown. |
| `keywords` | `array` | Keywords used for semantic/token matching with storyboards. |
| `supported_scene_roles` | `array` | Supported storyboard roles. Allowed values: `["proof", "payoff"]`. |
| `supported_topics` | `array` | Niche topics or categories this asset is valid for. |
| `duration_seconds` | `float` | Duration of the clip in seconds. |
| `orientation` | `string` | Aspect orientation, e.g. `vertical_or_crop_safe`. |
| `source_type` | `string` | Origin of the asset, e.g. `manual_screen_recording`, `synthetic_mock_asset`. |
| `approved_for_private_validation` | `boolean` | If true, allowed in private testing runs. |
| `approved_for_public_use` | `boolean` | If true, allowed in public production posts. |
| `contains_private_data` | `boolean` | Flag indicating if any private information exists (must be false). |
| `notes` | `string` | Additional administrative comments or review dates. |
| `asset_variant` | `string` | Visual variant category: `hook_visual`, `process_visual`, `proof_visual`, `payoff_visual`, `final_result_visual`. |
| `visual_strength_score` | `integer` | Subjective visual strength/clarity score (e.g. 1 to 5). |
| `best_for_scene_position` | `array` | Preferred positions in storyboard, e.g. `["final_payoff", "last_3_seconds"]`. |
| `allowed_reuse_count` | `integer` | Maximum times this asset can be reused across a single video. |
| `allow_single_asset_private_validation` | `boolean` | If true, allows this single asset to cover all proof/payoff scenes during private real validation. |
| `payoff_strength` | `string` | Strengths of visual payoff, e.g. `strong`, `medium`, `weak`. |
| `visual_notes` | `string` | Details of the visual components shown. |

## Example Entry

```json
{
  "asset_id": "calendar_agent_final_payoff_001",
  "file_path": "assets/proof_capture/calendar_agent/calendar_agent_final_payoff_001.mp4",
  "project": "calendar_agent",
  "descriptor": "AI scheduling assistant weekly calendar with WEEK PLANNED overlay",
  "keywords": ["calendar", "schedule", "meeting", "week", "automation", "planned"],
  "supported_scene_roles": ["payoff"],
  "supported_topics": ["ai_tools", "productivity", "calendar automation"],
  "duration_seconds": 7.0,
  "orientation": "vertical_or_crop_safe",
  "source_type": "synthetic_private_validation_asset",
  "approved_for_private_validation": true,
  "approved_for_public_use": false,
  "contains_private_data": false,
  "notes": "Demo recording. Public approval required after manual review.",
  "asset_variant": "final_result_visual",
  "visual_strength_score": 5,
  "best_for_scene_position": ["final_payoff", "last_3_seconds"],
  "allowed_reuse_count": 2,
  "allow_single_asset_private_validation": true,
  "payoff_strength": "strong",
  "visual_notes": "Shows completed weekly calendar with WEEK PLANNED text."
}
```
