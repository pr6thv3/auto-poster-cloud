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

## Example Entry

```json
{
  "asset_id": "calendar_agent_demo_001",
  "file_path": "assets/proof_capture/calendar_agent/calendar_agent_demo_001.mp4",
  "project": "calendar_agent",
  "descriptor": "AI scheduling assistant automatically fills a weekly calendar",
  "keywords": ["calendar", "schedule", "meeting", "week", "automation"],
  "supported_scene_roles": ["proof", "payoff"],
  "supported_topics": ["ai_tools", "productivity", "calendar automation"],
  "duration_seconds": 6.0,
  "orientation": "vertical_or_crop_safe",
  "source_type": "manual_screen_recording",
  "approved_for_private_validation": true,
  "approved_for_public_use": false,
  "contains_private_data": false,
  "notes": "Demo recording only. Public approval required after manual review."
}
```
