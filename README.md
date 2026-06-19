# 🎭 MoodLights

![Icon](custom_components/moodlights/brand/logo@2x.png)

**One-Click Smart Lighting for Every Moment**

Turn your lights into a mood engine. Create named lighting presets, activate them with a single click, and instantly revert when you're done. Perfect for automations, manual control, and everything in between.

[![GitHub Release](https://img.shields.io/github/v/release/pranjal-joshi/moodlights?style=for-the-badge&logo=github&logoColor=white&label=RELEASE&color=10B981)](https://github.com/pranjal-joshi/moodlights/releases)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/pranjal-joshi/moodlights/total?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=2341BDF5&label=HACS%20Downloads&color=341BDF5)
[![License](https://img.shields.io/github/license/pranjal-joshi/moodlights?style=for-the-badge&logo=scroll&logoColor=white&label=LICENSE&color=orange)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

## ✨ Why MoodLights?

| Feature | Home Assistant Scenes | Light Groups | **MoodLights** |
|---------|:---:|:---:|:---:|
| One-click mood activation | ✅ | ✅ | ✅ |
| **Auto state backup before change** | ❌ | ❌ | ✅ |
| **One-button revert** | ❌ | ❌ | ✅ |
| **Auto-revert timer** | ❌ | ❌ | ✅ |
| Per-light brightness + color config | ✅ | Limited | ✅ |
| Blind/curtain/cover support | Limited | ❌ | ✅ |
| Built for automations & buttons | ✅ | ✅ | ✅ |

## 🎭 Perfect For

- **🎬 Movie Nights** — Dim to 20%, warm color temp, close blinds. One click.
- **🎮 Gaming Sessions** — Full brightness, cool white, RGB accents. Activate, adjust, revert when done.
- **😴 Sleep Mode** — Red lights only, covers closed, easy one-tap wake-up revert.
- **🍽️ Dinner Parties** — Restaurant ambiance with RGB lighting at specific brightness.
- **🌅 Morning Routine** — Trigger from automation: brightness ramp + color temp shift.
- **📚 Focus Time** — Neutral whites, moderate brightness, no distractions.

## Features

- ✅ **Mood Entities** — Create unlimited mood presets with instant Activate & Revert buttons
- ✅ **Per-Light Config** — Set brightness, color temperature, and RGB for each light independently
- ✅ **Cover Support** — Control blinds, curtains, and shades with position and tilt
- ✅ **Auto State Backup** — Saves up to 3 light/cover states before mood changes (instant rollback)
- ✅ **Auto-Revert Timer** — Per-mood toggle and duration. Mood auto-reverts after a set time. Countdown visible on dashboard.
- ✅ **Automation-Ready** — Call via services for buttons, remotes, time-based triggers, or anything else

## 🚀 Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pranjal-joshi&repository=moodlights&category=integration)

### Option 1: HACS (Recommended) — 1 Minute

1. Open Home Assistant
2. Go to **HACS** → **Integrations**
3. Click the **"+"** button
4. Search for **"MoodLights"**
5. Click **Install**
6. Restart Home Assistant

### Option 2: Manual

1. [Download the latest release](https://github.com/pranjal-joshi/moodlights/releases)
2. Extract `custom_components/moodlights` to your `config/custom_components/` directory
3. Restart Home Assistant

## ⚙️ Quick Setup — 2 Minutes

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=moodlights)

### Step 1: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"Create Integration"** → Search **"MoodLights"**
3. You're done! The integration is configured.

### Step 2: Create Your First Mood

1. Go to **Settings** → **Devices & Services** → **MoodLights**
2. Click **"Create Mood"**
3. **Name it** (e.g., `Movie Night`, `Sleep Mode`, `Dinner`)
4. **Select lights** to control
5. **Set brightness**, color temp, and/or RGB for each light
6. **Save**

### Step 3: Use Your Mood

**Via Dashboard:**
- Find your mood entity in **Dashboard**
- Click **"Activate"** to apply the mood
- Click **"Revert"** to restore previous state

**Via Automation (see examples below)**

## 💡 Usage

### Dashboard & UI — One Click

- **Activate** a mood to apply settings instantly
- **Revert** to restore lights to their previous state (saved automatically)

### Services — Automation & Scripts

#### Activate a Mood
```yaml
service: moodlights.activate_mood
data:
  mood_name: "Movie Night"
```

#### Activate with Auto-Revert (override timer)
```yaml
service: moodlights.activate_mood
data:
  mood_name: "Movie Night"
  duration: 120  # auto-revert after 120 minutes
```

#### Restore Previous State
```yaml
service: moodlights.restore_previous
data:
  mood_name: "Movie Night"
```

#### Cancel Auto-Revert Timer
```yaml
service: moodlights.cancel_auto_revert
data:
  mood_name: "Movie Night"
```

#### Manually Save Current State
```yaml
service: moodlights.save_state
data:
  mood_name: "Movie Night"
  preset_name: "Before Movie"
```

## 🤖 Automation Examples

### Example 1: Remote Button → Movie Night
```yaml
automation:
  - alias: "Remote: Movie Night Button"
    trigger:
      platform: device
      device_id: living_room_remote
      domain: remote
      type: short_press
      subtype: button_1
    action:
      - service: moodlights.activate_mood
        data:
          mood_name: "Movie Night"
```

### Example 2: Time-Based Morning Routine
```yaml
automation:
  - alias: "Morning: Brightness Ramp"
    trigger:
      platform: time
      at: "06:30:00"
    action:
      - service: moodlights.activate_mood
        data:
          mood_name: "Morning Wake"
```

### Example 3: Sunset → Evening Mood
```yaml
automation:
  - alias: "Sunset: Evening Lighting"
    trigger:
      platform: sun
      event: sunset
      offset: "-00:30:00"
    action:
      - service: moodlights.activate_mood
        data:
          mood_name: "Evening Ambiance"
```

### Example 4: Leave Home → Revert All
```yaml
automation:
  - alias: "Leaving: Revert Moods"
    trigger:
      platform: state
      entity_id: person.you
      to: "not_home"
    action:
      - service: moodlights.restore_previous
        data:
          mood_name: "Movie Night"
      - service: moodlights.restore_previous
        data:
          mood_name: "Dinner"
```

### Example 5: Input Button Helper
```yaml
# Dashboard button → MoodLights activation
automation:
  - alias: "Dashboard: Toggle Gaming Mode"
    trigger:
      platform: state
      entity_id: input_button.gaming_mode
    action:
      - service: moodlights.activate_mood
        data:
          mood_name: "Gaming"
```

## 📮 Smart State Management

**Auto-Backup:** When you activate a mood, MoodLights saves your lights' current state automatically.

- **Saves up to 3 states** per mood (stack-based)
- **Stored in memory** (cleared on HA restart)
- **One-click revert** — restore lights to any previous state
- **Why this matters:** Forget about fiddling with individual lights. Activate a mood, enjoy it, then revert when you want back to normal.

**Example Flow:**
1. Lights: Kitchen 50%, Warm White
2. Activate "Movie Night" → Saves current state → Dims to 20%, warm color temp
3. Activate "Gaming" → Saves current state → Full brightness, cool white
4. Click "Revert" → Restores lights back to Gaming settings
5. Click "Revert" again → Restores lights back to Movie Night state
6. Click "Revert" again → Back to original Kitchen 50%

### Auto-Revert Timer

Each mood gets three dashboard controls:

- **Revert Timer** (switch) — Enable/disable auto-revert for this mood
- **Revert After** (number) — Set duration in minutes (1 min – 24 hrs). Greyed out when timer is off.
- **Revert Countdown** (sensor) — Shows remaining time, auto-formatted by HA

Toggle the switch ON, set your duration, activate the mood — it auto-reverts when the timer finishes. You can also pass `duration` in the `activate_mood` service call to override per-activation.

## Requirements

- Home Assistant 2024.10.0 or higher
- Python 3.12+

## Support

- [Issue Tracker](https://github.com/pranjal-joshi/moodlights/issues)
- [Discussions](https://github.com/pranjal-joshi/moodlights/discussions)

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*If you find this integration useful, please consider giving it a star on GitHub!*

## Star History

[![Star History Chart](https://api.star-history.com/image?repos=pranjal-joshi/moodlights&type=date&legend=top-left)](https://www.star-history.com/?repos=pranjal-joshi%2Fmoodlights&type=date&legend=top-left)
