# MoodLights

Easy mood-based light management for Home Assistant.

[![GitHub Release](https://img.shields.io/github/v/release/pranjal-joshi/moodlights)](https://github.com/pranjal-joshi/moodlights/releases)
[![HACS Installations](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=HACS%20Installations&query=$count&url=https://api.github.com/repos/pranjal-joshi/moodlights)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pranjal-joshi&repository=moodlights)
[![License](https://img.shields.io/github/license/pranjal-joshi/moodlights)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/)

## Features

- **Mood Entities**: Create mood entities that appear as select entities in Home Assistant
- **Dynamic Light Groups**: Select lights by area, entity pattern, or manually
- **Presets**: Define multiple presets per mood (brightness, color, transition)
- **State Save & Restore**: Automatically saves light states before mood changes, allows easy rollback
- **Exclusion Rules**: Block mood changes when certain conditions are met (media playing, person away, etc.)
- **Optional Confirmation**: Send notifications or require approval before mood changes
- **Smooth Transitions**: Configure transition times for smooth light changes

## Installation

### Option 1: HACS (Recommended)

1. Open Home Assistant
2. Go to HACS -> Integrations
3. Click the "+" button
4. Search for "MoodLights"
5. Click Install

### Option 2: Manual

1. Download the latest release
2. Extract the `custom_components/moodlights` folder to your Home Assistant's `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

### Via UI

1. Go to Settings -> Devices & Services
2. Click "Add Integration"
3. Search for "MoodLights"
4. Follow the configuration wizard

### Creating a Mood

1. Start the configuration wizard
2. Give your mood a name (e.g., "Living Room Evening")
3. Select lights for this mood (by area, pattern, or manually)
4. Add presets (e.g., "Movie Night", "Bright", "Relaxed")
5. Configure exclusion rules (optional)
6. Set confirmation mode (optional)
7. Configure state save settings

## Usage

### Via UI

- Select a mood preset from the dropdown to activate
- The entity shows current preset and whether restore is available

### Via Services

```yaml
# Activate a mood
service: moodlights.activate_mood
data:
  mood_id: "mood_0"
  preset: "Movie Night"

# Restore previous state
service: moodlights.restore_previous
data:
  mood_id: "mood_0"

# Manually save current state
service: moodlights.save_state
data:
  mood_id: "mood_0"
  preset_name: "Before Movie"
```

## Exclusion Rules

MoodLights can automatically block mood changes based on:

- **Helper Entities**: `input_boolean`, `switch`, `binary_sensor` (when on)
- **Entity States**:
  - `media_player` (when playing/paused)
  - `person` (when home)
  - `binary_sensor` (when on)

## State Management

MoodLights automatically saves light states before applying a new mood:

- Saves up to 3 previous states (configurable)
- States are stored in memory and cleared on HA restart
- Use `restore_previous` service to revert to the previous state

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
