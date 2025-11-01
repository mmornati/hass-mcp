# Webhooks Tools

Manage and test webhooks in Home Assistant.

## Available Tools

### `list_webhooks`

Get information about webhook configuration.

**Example Usage:**
```
User: "How do I configure webhooks?"
Claude: [Uses list_webhooks]
✅ Webhook Information:
   Webhooks are typically defined in configuration.yaml
   Format: /api/webhook/{webhook_id}
```

### `test_webhook`

Test a webhook endpoint.

**Parameters:**
- `webhook_id` (required): The webhook ID to test
- `data` (optional): Data to send to the webhook

**Example Usage:**
```
User: "Test webhook 'my_webhook'"
Claude: [Uses test_webhook]
✅ Webhook tested successfully
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
