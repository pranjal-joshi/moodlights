# 🎭 MoodLights

One-click smart lighting presets with auto state backup and instant revert.

## What It Does

Transform your lights into a mood engine:
- **Create moods** → Named lighting presets (brightness, color temp, RGB, blind position)
- **Activate with one click** → Apply all settings instantly
- **Revert instantly** → Back to previous state (auto-saved)
- **Automate everything** → Control via remote, button, time, or any Home Assistant trigger

## Perfect For

🎬 **Movie Nights** — Dim + warm color + blinds closed  
🎮 **Gaming** — Full brightness + cool white + RGB accents  
😴 **Sleep** — Red lights only + covers closed  
🍽️ **Dinners** — Restaurant ambiance  
🌅 **Mornings** — Auto brightness ramp  
📚 **Focus** — Neutral whites  

## Key Features

✅ Unlimited mood presets  
✅ Per-light brightness, color temp, RGB control  
✅ Blind/curtain/cover support  
✅ Auto state backup (up to 3 per mood)  
✅ One-click revert  
✅ Callable HA services for automations  

## Why MoodLights Over Scenes?

| Feature | Scenes | **MoodLights** |
|---------|:---:|:---:|
| One-click activation | ✅ | ✅ |
| **Auto state backup** | ❌ | ✅ |
| **One-button revert** | ❌ | ✅ |
| Cover support | ❌ | ✅ |

## Quick Start

1. **Install via HACS** or manually copy to `custom_components/moodlights`
2. **Restart** Home Assistant
3. **Go to Settings → Devices & Services → MoodLights**
4. **Create a mood** → Name it, select lights, set brightness/color/etc.
5. **Use it** → Click Activate/Revert on dashboard OR call via service in automation

## Example: Movie Night Automation

```yaml
automation:
  - alias: "Remote Button: Movie Night"
    trigger:
      platform: device
      device_id: your_remote
      type: short_press
    action:
      - service: moodlights.activate_mood
        data:
          mood_name: "Movie Night"
```

## Services

- `moodlights.activate_mood` — Apply a mood
- `moodlights.restore_previous` — Revert to previous state
- `moodlights.save_state` — Manually save current state

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pranjal-joshi&repository=moodlights&category=integration)

**Via HACS:**
1. Go to HACS → Integrations → "+" → Search "MoodLights" → Install

**Manual:**
1. Download latest release
2. Extract `custom_components/moodlights` to `config/custom_components/`
3. Restart Home Assistant

## Support

- [Issues](https://github.com/pranjal-joshi/moodlights/issues)
- [Discussions](https://github.com/pranjal-joshi/moodlights/discussions)
- [Full Documentation](https://github.com/pranjal-joshi/moodlights)

## Requirements

- Home Assistant 2024.10.0+
- Python 3.12+
