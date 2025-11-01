# Services Tools

Service tools allow you to call any Home Assistant service directly, providing low-level access to Home Assistant functionality.

## Available Tools

### `call_service`

Call any Home Assistant service.

**Parameters:**
- `domain` (required): Service domain, e.g., `light`, `switch`, `automation`
- `service` (required): Service name, e.g., `turn_on`, `turn_off`, `toggle`
- `data` (optional): Service data dictionary

**Example Usage:**
```
User: "Turn on the living room light at 80% brightness"
Claude: [Uses call_service]
✅ Service called successfully

User: "Call the notify.mobile_app service to send a test message"
Claude: [Uses call_service]
✅ Notification sent successfully
```

**Common Services:**

**Lights:**
- `light.turn_on` - Turn on a light
- `light.turn_off` - Turn off a light
- `light.toggle` - Toggle a light

**Switches:**
- `switch.turn_on` - Turn on a switch
- `switch.turn_off` - Turn off a switch
- `switch.toggle` - Toggle a switch

**Climate:**
- `climate.set_temperature` - Set temperature
- `climate.set_hvac_mode` - Set HVAC mode

**Media Players:**
- `media_player.play_media` - Play media
- `media_player.volume_set` - Set volume

**Automation:**
- `automation.trigger` - Trigger an automation
- `automation.toggle` - Toggle automation state

## Use Cases

### Direct Service Calls

```
"Call the light.turn_on service for light.living_room with brightness 200"
"Trigger the automation.morning_routine service"
"Call climate.set_temperature for climate.living_room to 22 degrees"
```

### Advanced Control

```
"Use the media_player.play_media service to play music"
"Call the input_number.set_value service to set input_number.volume to 75"
"Use notify.mobile_app to send a message"
```

## Best Practices

1. **Use entity_action** when possible for simpler entity control
2. **Use call_service** for advanced service calls with specific parameters
3. **Check service documentation** in Home Assistant for available parameters
4. **Validate service data** before calling complex services
