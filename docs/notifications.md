# Notifications Tools

Send and test notifications through Home Assistant notification services.

## Available Tools

### `list_notification_services`

List all available notification services.

**Example Usage:**
```
User: "What notification services are available?"
Claude: [Uses list_notification_services]
✅ Notification Services:
- mobile_app.iphone
- mobile_app.android
- notify.telegram
...
```

### `send_notification`

Send a notification.

**Parameters:**
- `service` (required): Notification service name
- `message` (required): Notification message
- `title` (optional): Notification title
- `data` (optional): Additional notification data

**Example Usage:**
```
User: "Send a notification to my phone saying 'Hello'"
Claude: [Uses send_notification]
✅ Notification sent successfully
```

### `test_notification`

Test a notification service.

**Parameters:**
- `service` (required): Notification service to test

**Example Usage:**
```
User: "Test the mobile_app.iphone notification service"
Claude: [Uses test_notification]
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
