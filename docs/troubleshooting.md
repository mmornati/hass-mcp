# Troubleshooting

Common issues and their solutions when using Hass-MCP.

## Connection Issues

### Problem: "Cannot connect to Home Assistant"

**Symptoms:**
- Tools fail with connection errors
- "Connection timeout" messages
- "Connection refused" errors

**Solutions:**

1. **Verify `HA_URL` is correct:**
   - Check the URL format: `http://hostname:port` or `https://hostname:port`
   - Ensure the port is correct (default: 8123)
   - Test the URL in a browser

2. **Check network connectivity:**
   - Ping the Home Assistant host
   - Verify firewall rules allow connections
   - For Docker, check network configuration

3. **Verify Home Assistant is running:**
   - Check Home Assistant status
   - Ensure API is enabled (enabled by default)

### Problem: "401 Unauthorized" or "403 Forbidden"

**Symptoms:**
- Authentication errors
- "Invalid token" messages

**Solutions:**

1. **Verify `HA_TOKEN` is correct:**
   - Check token hasn't been revoked
   - Ensure token is copied completely
   - Try creating a new token

2. **Check token permissions:**
   - Ensure token has necessary permissions
   - Some operations may require admin permissions

3. **Token expiration:**
   - Long-lived tokens don't expire by default
   - Check if token was set with expiration

## Tool-Specific Issues

### Problem: Entity Not Found

**Symptoms:**
- "Entity not found" errors
- Entity appears as unavailable

**Solutions:**

1. **Verify entity ID format:**
   - Format: `domain.entity_name`
   - Example: `light.living_room`
   - Check for typos

2. **Check entity exists:**
   - Use `list_entities` to find the correct ID
   - Use `search_entities_tool` to find similar entities

3. **Check entity state:**
   - Entity may be unavailable
   - Use `diagnose_entity` to investigate

### Problem: Automation Not Working

**Symptoms:**
- Automation doesn't trigger
- Automation fails to execute

**Solutions:**

1. **Check automation status:**
   - Use `get_automation_config` to verify configuration
   - Check if automation is enabled
   - Review execution logs with `get_automation_execution_log`

2. **Verify triggers:**
   - Check trigger conditions
   - Verify trigger entities exist and are working
   - Test trigger conditions manually

3. **Check conditions:**
   - Review condition logic
   - Verify condition entities are in correct states

4. **Review actions:**
   - Verify action entities exist
   - Check for errors in action execution

### Problem: Service Call Fails

**Symptoms:**
- Service calls return errors
- "Service not found" messages

**Solutions:**

1. **Verify service name:**
   - Format: `domain.service`
   - Check service documentation for correct name

2. **Check service parameters:**
   - Review required parameters
   - Verify parameter types (string, number, etc.)
   - Check parameter values are valid

3. **Verify entity exists:**
   - If service requires `entity_id`, verify it exists
   - Check entity is in a state that allows the service call

## Performance Issues

### Problem: Slow Response Times

**Symptoms:**
- Tools take a long time to execute
- Timeout errors

**Solutions:**

1. **Increase timeout:**
   - Set `HA_TIMEOUT` environment variable
   - Default is 30 seconds, increase if needed

2. **Use lean format:**
   - Use `lean=True` when listing entities
   - Specify `limit` to reduce result size

3. **Filter results:**
   - Use domain filters
   - Use search queries instead of listing all entities

4. **Check Home Assistant performance:**
   - Review Home Assistant logs
   - Check system resources
   - Review integration performance

### Problem: High Token Usage

**Symptoms:**
- Conversations consume many tokens
- Responses are too verbose

**Solutions:**

1. **Use lean format:**
   - Default format is already lean
   - Avoid `detailed=True` unless necessary

2. **Limit results:**
   - Use `limit` parameter
   - Use domain filters

3. **Be specific:**
   - Ask for specific entities
   - Use search instead of listing all

## Docker-Specific Issues

### Problem: Docker Container Can't Reach Home Assistant

**Symptoms:**
- Connection errors from Docker container
- "Connection refused" from container

**Solutions:**

1. **Use `host.docker.internal`:**
   - For Mac/Windows Docker Desktop
   - Use `http://host.docker.internal:8123`

2. **Use host network (Linux only):**
   - Add `--network host` to Docker args
   - Allows container to use host network

3. **Use actual IP address:**
   - Instead of hostname, use IP address
   - Example: `http://192.168.1.100:8123`

4. **Check Docker network:**
   - Verify Docker network configuration
   - Ensure container can reach host network

### Problem: Environment Variables Not Working

**Symptoms:**
- Tools fail with "missing configuration" errors

**Solutions:**

1. **Verify environment variable format:**
   - Use `-e` flag in Docker args
   - Format: `-e HA_URL -e HA_TOKEN`

2. **Check Claude Desktop configuration:**
   - Verify `env` section is correct
   - Ensure JSON is valid

3. **Test environment variables:**
   - Check variables are passed correctly
   - Review Docker logs for errors

## Getting Additional Help

### Debug Mode

Enable debug logging:

```json
{
  "env": {
    "LOG_LEVEL": "DEBUG"
  }
}
```

This provides detailed logging for troubleshooting.

### Check Logs

1. **Claude Desktop logs:**
   - Check Claude Desktop console for errors
   - Review MCP server connection logs

2. **Home Assistant logs:**
   - Check Home Assistant logs for API errors
   - Review integration logs

3. **Docker logs:**
   - `docker logs <container-id>`
   - Review container output

### Community Resources

- **GitHub Issues**: Report bugs or ask questions
- **Home Assistant Forums**: Community support
- **Home Assistant Discord**: Real-time help

### Reporting Issues

When reporting issues, include:

1. **Error messages**: Exact error text
2. **Configuration**: Relevant parts (without tokens!)
3. **Steps to reproduce**: What you did to trigger the issue
4. **Environment**: Home Assistant version, Python version, etc.
5. **Logs**: Relevant log entries (sanitize tokens!)
