# Webhooks Tools

Manage and test webhooks in Home Assistant.

## Available Tools

### `manage_webhooks` (Unified Tool)

Unified webhooks tool that replaces `list_webhooks` and `test_webhook`.

**Parameters:**
- `action` (required): Action to perform. Options:
  - `"list"`: List registered webhooks
  - `"test"`: Test webhook endpoint (requires `webhook_id`)
- `webhook_id` (optional): Webhook ID to test (required for `"test"` action)
- `payload` (optional): Payload to send with webhook request (for `"test"` action)

**Example Usage:**
```
User: "How do I configure webhooks?"
Claude: [Uses manage_webhooks with action="list"]
✅ Webhook Information:
   Webhooks are typically defined in configuration.yaml
   Format: /api/webhook/{webhook_id}

User: "Test webhook 'my_webhook'"
Claude: [Uses manage_webhooks with action="test", webhook_id="my_webhook"]
✅ Webhook tested successfully

User: "Test webhook with data"
Claude: [Uses manage_webhooks with action="test", webhook_id="my_webhook", payload={"entity_id": "light.living_room"}]
✅ Webhook tested with payload
```

## Use Cases

### Webhook Testing

```
"Test my webhook endpoint"
"Send test data to webhook XYZ"
```

### Configuration

```
"How do I configure webhooks?"
"What webhooks are available?"
```
