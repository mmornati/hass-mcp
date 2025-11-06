# Query Intent Classification

The query intent classification module provides natural language understanding for user queries, extracting intent, domain, actions, entities, and parameters.

## Overview

The classification module processes natural language queries to understand user intent and extract relevant information:

- **Intent Classification**: Identifies the user's intent (SEARCH, CONTROL, STATUS, CONFIGURE, DISCOVER, ANALYZE)
- **Domain Prediction**: Predicts the entity domain from natural language
- **Action Extraction**: Extracts actions like "turn on", "set", "increase"
- **Entity Extraction**: Extracts entity references and filters (area, domain, type)
- **Parameter Extraction**: Extracts numeric values, attributes, and time references
- **Query Refinement**: Normalizes and refines queries

## Usage

### Basic Usage

```python
from app.core.vectordb.classification import process_query

# Process a query
result = await process_query("turn on the living room lights")

print(result["intent"])  # "CONTROL"
print(result["action"])  # "on"
print(result["entity_filters"]["area_id"])  # "living_room"
```

### Individual Functions

You can also use individual classification functions:

```python
from app.core.vectordb.classification import (
    classify_intent,
    predict_domain,
    extract_action,
    extract_entities,
    extract_parameters,
    refine_query,
)

# Classify intent
intent, confidence = await classify_intent("find all lights")
# Returns: ("SEARCH", 0.95)

# Predict domain
domain, confidence = await predict_domain("turn on the lights")
# Returns: ("light", 0.85)

# Extract action
action, params = await extract_action("set temperature to 22")
# Returns: ("set", {"value": 22})

# Extract entities
entities, filters = await extract_entities("turn on lights in living room")
# Returns: ([], {"area_id": "living_room", "domain": "light"})

# Extract parameters
params = await extract_parameters("set brightness to 50%")
# Returns: {"value": 50, "unit": "percent", "attribute": "brightness"}

# Refine query
refined = await refine_query("turn  on   the  lights")
# Returns: "turn on the lights"
```

## Intent Classification

The module classifies queries into six intent types:

### SEARCH
Find or discover entities.

**Examples:**
- "find all lights in the kitchen"
- "show me all temperature sensors"
- "what lights are in the living room"

### CONTROL
Control or modify entities.

**Examples:**
- "turn on the living room lights"
- "set temperature to 22"
- "dim the kitchen lights"

### STATUS
Get the current status of entities.

**Examples:**
- "what is the temperature in the kitchen"
- "are the lights on"
- "check the status of all lights"

### CONFIGURE
Configure or setup entities.

**Examples:**
- "configure the thermostat settings"
- "setup the alarm system"
- "install a new sensor"

### DISCOVER
Discover related entities.

**Examples:**
- "what other lights are in the kitchen"
- "show me similar entities"
- "what devices are in this room"

### ANALYZE
Analyze entity data or patterns.

**Examples:**
- "analyze the energy consumption"
- "show me usage statistics"
- "what is the trend for temperature"

## Domain Prediction

The module predicts entity domains from natural language:

- **light**: lights, lamps, bulbs, illumination
- **sensor**: sensors, temperature, humidity, motion
- **switch**: switches, toggles, outlets
- **climate**: thermostat, heating, cooling, AC
- **cover**: covers, blinds, curtains, garage
- **fan**: fans, ventilation
- **lock**: locks, door locks, security
- **media_player**: media, music, audio, speakers, TV
- **camera**: cameras, video, streams
- **alarm_control_panel**: alarms, security, alerts

## Action Extraction

The module extracts actions from queries:

- **on**: turn on, switch on, activate, enable, open
- **off**: turn off, switch off, deactivate, disable, close
- **set**: set, set to, configure to, adjust to
- **increase**: increase, raise, up, higher, more, brighten
- **decrease**: decrease, lower, down, less, dim
- **toggle**: toggle, switch, flip

Actions can include parameters:
- **value**: Numeric value (e.g., "set to 22")
- **unit**: Unit of measurement (e.g., "50%")
- **attribute**: Attribute name (e.g., "brightness")

## Entity Extraction

The module extracts entity references and filters:

### Explicit Entity IDs
Extracts explicit entity IDs from queries:
- "turn on light.living_room" → `["light.living_room"]`

### Area/Room Names
Extracts area names from queries:
- "turn on lights in living room" → `{"area_id": "living_room"}`

### Domain Filters
Extracts domain from queries:
- "turn on the lights" → `{"domain": "light"}`

### Type Hints
Extracts entity type hints:
- "what is the temperature" → `{"type": "temperature"}`

## Parameter Extraction

The module extracts various parameters:

### Numeric Values
- Integers: "set to 22" → `{"value": 22}`
- Floats: "set to 22.5" → `{"value": 22.5}`
- Percentages: "set to 50%" → `{"value": 50, "unit": "percent"}`

### Attributes
- "increase brightness" → `{"attribute": "brightness"}`
- "set color temperature" → `{"attribute": "color_temp"}`

### Time References
- "show me data from last 24 hours" → `{"time": "24 hours"}`
- "what is the temperature today" → `{"time": "today"}`

## Query Refinement

The module refines queries by:
- Normalizing whitespace
- Expanding synonyms (e.g., "switch on" → "turn on")
- Preserving plurals (e.g., "lights" stays as "lights")

## Complete Example

```python
from app.core.vectordb.classification import process_query

# Process a complex query
result = await process_query("turn on the living room lights to 50% brightness")

print(result)
# {
#     "intent": "CONTROL",
#     "confidence": 0.95,
#     "domain": "light",
#     "domain_confidence": 0.85,
#     "action": "on",
#     "action_params": {
#         "value": 50,
#         "unit": "percent",
#         "attribute": "brightness"
#     },
#     "entities": [],
#     "entity_filters": {
#         "area_id": "living_room",
#         "domain": "light"
#     },
#     "parameters": {
#         "value": 50,
#         "unit": "percent",
#         "attribute": "brightness"
#     },
#     "refined_query": "turn on the living room lights to 50% brightness"
# }
```

## Integration with Semantic Search

The classification module integrates seamlessly with semantic search:

```python
from app.core.vectordb.classification import process_query
from app.core.vectordb.search import semantic_search

# Classify query
classification = await process_query("find all temperature sensors in the kitchen")

# Use classification results for semantic search
results = await semantic_search(
    query=classification["refined_query"],
    domain=classification["domain"],
    area_id=classification["entity_filters"].get("area_id"),
    limit=10,
)
```

## Best Practices

1. **Use `process_query` for complete classification**: It performs all classification steps in one call.

2. **Use individual functions for specific needs**: If you only need intent or domain, use the specific function.

3. **Handle confidence scores**: Lower confidence scores indicate uncertainty. Consider fallback strategies.

4. **Combine with semantic search**: Use classification results to improve semantic search accuracy.

5. **Refine queries before searching**: Use `refine_query` to normalize queries before semantic search.

## Limitations

- **Pattern-based classification**: Uses pattern matching, not ML models. May not handle complex or ambiguous queries perfectly.

- **Domain ambiguity**: Some queries may match multiple domains. The module returns the highest scoring domain.

- **Language support**: Currently optimized for English. Other languages may have reduced accuracy.

- **Context awareness**: Does not maintain conversation context. Each query is processed independently.

## Future Enhancements

Future versions may include:
- ML-based intent classification
- Multi-intent support
- Context-aware classification
- Multi-language support
- Improved ambiguity handling
