# Auto-Revert Timer — MoodLights

## Goal

Let users automatically revert a mood's lights and covers back to their pre-activation state after a configurable duration — without writing automations. All controls live on the dashboard as native HA entities.

---

## Design

HA's `timer` component is a helper, not an entity platform — custom integrations cannot create timer entities via `Platform.TIMER`. Instead, we use three standard HA entity types:

| Entity | HA Type | Purpose |
|---|---|---|
| **Revert Timer** | `switch` | Enable/disable auto-revert for this mood |
| **Revert After** | `number` | Set how long the mood stays active (in minutes). Greyed out when Revert Timer is OFF. |
| **Revert Countdown** | `sensor` (`device_class: duration`) | Shows remaining time — HA auto-formats to mins/hrs/days |

The `sensor` with `device_class: duration` is the proper HA entity type that handles time unit display automatically without custom formatting.

---

## Dashboard per mood (after change)

| Entity | Type | Name | Status |
|---|---|---|---|
| `button.<mood>_activate` | Button | Activate | Existing |
| `button.<mood>_revert` | Button | Revert | Existing |
| `binary_sensor.<mood>_active` | Binary Sensor | Active | Existing |
| `switch.<mood>_revert_timer` | Switch | Revert Timer | **New** |
| `number.<mood>_revert_after` | Number | Revert After | **New** |
| `sensor.<mood>_revert_countdown` | Sensor | Revert Countdown | **New** |

All entities belong to the mood's device. Entity names are "Revert Timer", "Revert Duration", "Revert Countdown" — HA auto-prefixes with the mood name.

---

## Behaviour

### Activation flow (button press or service call)

1. Mood is applied (existing logic, unchanged)
2. Manager checks auto-revert state:
   - If `duration` param is passed in service call → start timer with that duration (override)
   - Else if `switch.revert_timer` is ON → read `number.revert_after` value → start timer
   - Else → no timer (current behaviour, fully backward compatible)
3. Timer uses `async_call_later` from `homeassistant.helpers.event`

### Timer finishes

Callback fires → manager calls `restore_previous(mood_id)` → lights/covers revert.

### Timer cancelled (switch turned OFF or `cancel_auto_revert` service called)

No restore happens. User explicitly chose to keep the mood on.

### Manual revert while timer is active

User presses the Revert button (or calls `restore_previous`). Timer is cancelled internally, state is restored.

### Reactivation while timer is active

Manager cancels the running timer and starts a new one with the current duration.

### HA restart

Timer is lost (consistent with ephemeral state snapshots). Switch and number values persist via `RestoreEntity`.

### Integration unload

All active timers are cancelled in `async_unload()`.

---

## User workflows

### "Enable auto-revert for a mood"

1. Toggle ON `switch.<mood>_revert_timer`
2. Set `number.<mood>_revert_duration` to desired minutes (e.g. 90)
3. Press Activate button
4. Timer starts, countdown sensor shows remaining time
5. When timer finishes, mood reverts automatically

### "One-time override via service call"

```yaml
service: moodlights.activate_mood
data:
  mood_name: Movie Night
  duration: 120  # revert in 120 minutes regardless of switch state
```

### "Cancel auto-revert"

Option A: Toggle the switch OFF → cancels active timer
Option B: Call `moodlights.cancel_auto_revert` service
Option C: Press the Revert button → timer is cancelled, state restored immediately

### "Never auto-revert"

Leave the switch OFF. Mood stays on indefinitely (current behaviour).

---

## Files added

| File | Content |
|---|---|
| `switch.py` | `MoodAutoRevertSwitch` — toggle per mood. Uses `RestoreEntity` to persist ON/OFF across restarts. Calls `manager.set_auto_revert_enabled()`. Turning OFF cancels active timer. |
| `number.py` | `MoodRevertAfterNumber` — duration input per mood. Uses `RestoreEntity`. Min 1, max 1440 (24h), step 1, unit "min". Calls `manager.set_auto_revert_duration()`. Greyed out (unavailable) when Revert Timer switch is OFF via dispatcher signal. |
| `sensor.py` | `MoodRevertCountdownSensor` — countdown display per mood. `device_class: duration`, unit "s". Polls `manager.get_auto_revert_remaining()` every 5 seconds. HA auto-formats the display. |

## Files modified

| File | Changes |
|---|---|
| `const.py` | Added `DEFAULT_REVERT_DURATION_MIN`, `MIN_REVERT_DURATION_MIN`, `MAX_REVERT_DURATION_MIN` |
| `manager.py` | Timer state dicts. `activate_mood` accepts optional `duration` param. `_schedule_auto_revert()`, `_make_revert_callback()`, `cancel_auto_revert()`, `get_auto_revert_remaining()`, `is_timer_active()`, `set_auto_revert_enabled()`, `set_auto_revert_duration()`. Cancels timer in `restore_previous()` and `async_unload()`. |
| `__init__.py` | Added `Platform.SWITCH`, `Platform.NUMBER`, `Platform.SENSOR` to `PLATFORMS`. Added `cancel_auto_revert` service + handler. Added `duration` field to `activate_mood` schema. |
| `services.yaml` | Added `duration` field to `activate_mood`. Added `cancel_auto_revert` service. |
| `translations/en.json` | Added entity name strings for switch/number/sensor. Added service strings for `cancel_auto_revert` and `duration` field. |

## Files NOT changed

| File | Reason |
|---|---|
| `button.py` | Still calls `manager.activate_mood(mood_id)` — manager handles timer internally |
| `binary_sensor.py` | Matching logic untouched |
| `state.py` | Save/restore logic untouched |
| `config_flow.py` | No new options flow fields needed |

---

## Backward compatibility

- `activate_mood` service `duration` param is fully optional — existing calls work unchanged
- Switch defaults to OFF — existing moods won't auto-revert unless user explicitly enables
- Number defaults to 60 minutes — sensible default when first enabled
- No config flow changes — no migrations needed
- New platforms auto-discover all existing moods

---

## Timer mechanism

Uses `homeassistant.helpers.event.async_call_later(hass, delay_seconds, callback)`:
- Returns a cancel callback stored in `manager._revert_timers[mood_id]`
- Deadline tracked in `manager._revert_deadlines[mood_id]` via `time.monotonic()`
- Countdown sensor reads `deadline - monotonic()` every 5 seconds
