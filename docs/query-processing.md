# Natural Language Query Processing

The natural language query processing tool processes user queries to automatically extract entities, actions, and parameters for executing commands.

## Overview

The query processing tool enables:

- **Intent Classification**: Identifies query intent (CONTROL, STATUS, SEARCH, etc.)
- **Entity Resolution**: Resolves entity references to actual entity IDs using semantic search
- **Action Extraction**: Extracts actions (on, off, set, etc.) from queries
- **Parameter Extraction**: Extracts parameters (temperature, brightness, etc.)
- **Execution Plan**: Builds structured execution plans for commands

## Usage

### Basic Usage

```python
from app.tools.query_processing import process_natural_language_query

# Process a natural language query
result = await process_natural_language_query("Turn on the living room lights")

print(result["intent"])  # "CONTROL"
print(result["entities"])  # [{"entity_id": "light.living_room", "confidence": 0.92}, ...]
print(result["action"])  # "on"
print(result["execution_plan"])  # [{"entity": "light.living_room", "action": "on"}, ...]
```

### Control Queries

```python
# Turn on lights
result = await process_natural_language_query("Turn on the living room lights")

# Set temperature
result = await process_natural_language_query("Set kitchen temperature to 22 degrees")

# Control with parameters
result = await process_natural_language_query("Set brightness to 50 percent")
```

### Status Queries

```python
# Check temperature
result = await process_natural_language_query("What's the temperature in the bedroom?")

# Check status
result = await process_natural_language_query("Is the garage door open?")
```

### Search Queries

```python
# Find entities
result = await process_natural_language_query("Find all lights in the kitchen")

# Search with filters
result = await process_natural_language_query("Show me temperature sensors")
```

## Response Format

### Control Query Response

```json
{
  "intent": "CONTROL",
  "confidence": 0.95,
  "entities": [
    {
      "entity_id": "light.living_room",
      "confidence": 0.92,
      "match_reason": "Entity 'Living Room Light' (light) matched with 92% similarity"
    }
  ],
  "action": "on",
  "action_params": {},
  "parameters": {},
  "execution_plan": [
    {
      "entity": "light.living_room",
      "action": "on"
    }
  ],
  "domain": "light",
  "refined_query": "turn on the living room lights"
}
```

### Control Query with Parameters

```json
{
  "intent": "CONTROL",
  "confidence": 0.90,
  "entities": [
    {
      "entity_id": "climate.kitchen",
      "confidence": 0.95,
      "match_reason": "Entity 'Kitchen Thermostat' (climate) matched with 95% similarity"
    }
  ],
  "action": "set",
  "action_params": {"temperature": 22},
  "parameters": {
    "temperature": 22,
    "unit": "celsius"
  },
  "execution_plan": [
    {
      "entity": "climate.kitchen",
      "action": "set_temperature",
      "parameters": {"temperature": 22}
    }
  ],
  "domain": "climate",
  "refined_query": "set kitchen temperature to 22 degrees"
}
```

### Status Query Response

```json
{
  "intent": "STATUS",
  "confidence": 0.90,
  "entities": [
    {
      "entity_id": "sensor.bedroom_temperature",
      "confidence": 0.88,
      "match_reason": "Entity 'Bedroom Temperature' (sensor) matched with 88% similarity"
    }
  ],
  "action": null,
  "action_params": {},
  "parameters": {},
  "execution_plan": [],
  "domain": "sensor",
  "refined_query": "what is the temperature in the bedroom"
}
```

## Intent Types

The tool classifies queries into the following intent types:

- **CONTROL**: Control entities (turn on, set, etc.)
- **STATUS**: Check entity status (what's the temperature, is it on, etc.)
- **SEARCH**: Find entities (find all lights, show sensors, etc.)
- **CONFIGURE**: Configure settings (setup, install, etc.)
- **DISCOVER**: Discover related entities (find similar, show related, etc.)
- **ANALYZE**: Analyze data (statistics, history, trends, etc.)

## Entity Resolution

The tool uses semantic search to resolve entity references:

- **Natural Language**: "living room lights" → `["light.living_room", "light.salon_spot_01", ...]`
- **Domain Filtering**: Uses predicted domain to filter results
- **Area Filtering**: Uses area references to filter results
- **Confidence Scores**: Returns confidence scores for each resolved entity

## Action Extraction

The tool extracts actions from queries:

- **on**: "turn on", "switch on", "activate"
- **off**: "turn off", "switch off", "deactivate"
- **set**: "set to", "configure to", "adjust to"
- **increase**: "increase", "raise", "brighten"
- **decrease**: "decrease", "lower", "dim"
- **toggle**: "toggle", "switch", "flip"

## Parameter Extraction

The tool extracts parameters from queries:

- **Numeric Values**: "22 degrees" → `{"temperature": 22, "unit": "celsius"}`
- **Percentages**: "50 percent" → `{"value": 50, "unit": "percent"}`
- **Attributes**: "brightness" → `{"attribute": "brightness"}`
- **Time References**: "in 5 minutes" → `{"delay": 300}`

## Execution Plans

The tool builds execution plans for control queries:

### Simple Control

```json
[
  {
    "entity": "light.living_room",
    "action": "on"
  }
]
```

### Control with Parameters

```json
[
  {
    "entity": "climate.kitchen",
    "action": "set_temperature",
    "parameters": {"temperature": 22}
  }
]
```

### Multiple Entities

```json
[
  {
    "entity": "light.living_room",
    "action": "on"
  },
  {
    "entity": "light.salon_spot_01",
    "action": "on"
  }
]
```

## Domain-Specific Execution Plans

The tool maps actions to domain-specific service calls:

- **Climate**: `set` → `set_temperature` with temperature parameter
- **Light**: `on` → `on` with optional brightness parameter
- **Cover**: `on`/`off` → `open`/`close`

## Integration with Other Modules

The query processing tool integrates with:

- **Query Intent Classification** (US-VD-006): Uses `process_query` for classification
- **Semantic Entity Search** (US-VD-004): Uses `semantic_search` for entity resolution
- **Entity Embedding and Indexing** (US-VD-002): Uses indexed entities for resolution

## Best Practices

1. **Use for Natural Language**: Use this tool for processing natural language queries from users
2. **Check Confidence**: Check confidence scores before executing commands
3. **Validate Entities**: Validate resolved entities before executing commands
4. **Use Execution Plans**: Use execution plans for structured command execution
5. **Handle Errors**: Handle errors gracefully when processing fails

## Limitations

- **Language Support**: Currently supports English queries primarily
- **Ambiguity**: May resolve ambiguous references to multiple entities
- **Complex Queries**: Complex multi-step queries may require manual processing

## Future Enhancements

Future versions may include:
- Multi-language support
- Improved ambiguity resolution
- Complex query decomposition
- Context-aware processing
- Query history integration
