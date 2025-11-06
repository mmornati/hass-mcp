# Notifications Tools

Send and test notifications through Home Assistant notification services.

## Available Tools

### `manage_notifications` (Unified Tool)

Unified notifications tool that replaces `list_notification_services`, `send_notification`, and `test_notification`.

**Parameters:**
- `action` (required): Action to perform. Options:
  - `"list"`: List available notification services
  - `"send"`: Send a notification (requires `message`)
  - `"test"`: Test notification delivery (requires `message` and `target`)
- `message` (optional): Notification message (required for `"send"` and `"test"` actions)
- `target` (optional): Target notification service/platform (required for `"test"`, optional for `"send"`)
- `data` (optional): Dictionary of additional notification data (for `"send"` action)

**Example Usage:**
```
User: "What notification services are available?"
Claude: [Uses manage_notifications with action="list"]
✅ Notification Services:
- mobile_app.iphone
- mobile_app.android
- notify.telegram
...

User: "Send a notification to my phone saying 'Hello'"
Claude: [Uses manage_notifications with action="send", message="Hello", target="mobile_app.iphone"]
✅ Notification sent successfully

User: "Test the mobile_app.iphone notification service"
Claude: [Uses manage_notifications with action="test", message="Test", target="mobile_app.iphone"]
✅ Test notification sent
```

## Use Cases

### Sending Notifications

```
"Send a notification to my phone: 'Motion detected in living room'"
"Notify me about the temperature alert"
"Send a test notification"
```

### Service Management

```
"What notification services do I have?"
"Test the Telegram notification service"
```
