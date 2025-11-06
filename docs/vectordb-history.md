# Query History and Learning

The query history and learning module provides query history storage, pattern analysis, personalized ranking, and learning from user query patterns.

## Overview

The history module enables:

- **Query History Storage**: Store queries with metadata, results, and user interactions
- **Query Pattern Analysis**: Analyze frequent queries, identify patterns, and detect trends
- **Personalized Entity Ranking**: Boost entities based on popularity and user preferences
- **Query Statistics**: Get insights into query patterns and usage
- **History Management**: View, clear, and manage query history

## Usage

### Storing Query History

```python
from app.core.vectordb.history import store_query_history

# Store a query with results
results = await semantic_search("living room lights")
result = await store_query_history(
    query="living room lights",
    results=results,
    selected_entity_id="light.living_room",
    user_id="user123",  # Optional
)

print(result["query_id"])  # Unique query ID
print(result["success"])  # True if stored successfully
```

### Getting Query History

```python
from app.core.vectordb.history import get_query_history
from datetime import datetime, timedelta, UTC

# Get recent queries
history = await get_query_history(limit=50)

# Get queries for a specific user
history = await get_query_history(limit=50, user_id="user123")

# Get queries within a date range
start_date = datetime.now(UTC) - timedelta(days=7)
end_date = datetime.now(UTC)
history = await get_query_history(
    limit=50,
    start_date=start_date,
    end_date=end_date,
)
```

### Getting Query Statistics

```python
from app.core.vectordb.history import get_query_statistics

# Get statistics for the last 30 days
stats = await get_query_statistics(days=30)

print(stats["total_queries"])  # Total number of queries
print(stats["unique_queries"])  # Number of unique queries
print(stats["most_common_queries"])  # Most common queries
print(stats["most_common_intents"])  # Most common intents
print(stats["most_common_domains"])  # Most common domains
print(stats["most_selected_entities"])  # Most selected entities
print(stats["queries_by_time_of_day"])  # Distribution by time of day
```

### Entity Popularity

```python
from app.core.vectordb.history import get_entity_popularity

# Get entity popularity count
popularity = await get_entity_popularity("light.living_room")
print(popularity)  # Number of times entity was selected
```

### Personalized Entity Ranking

```python
from app.core.vectordb.history import boost_entity_ranking

# Boost entity ranking based on popularity
results = await semantic_search("lights")
boosted_results = await boost_entity_ranking(
    results,
    boost_factor=0.1,  # Boost factor (0.0-1.0)
)

# Results are re-sorted with popularity boost
for result in boosted_results:
    print(result["entity_id"])
    print(result["similarity_score"])  # May include popularity boost
    if "popularity_boost" in result:
        print(result["popularity_boost"])  # Boost amount
```

### Clearing Query History

```python
from app.core.vectordb.history import clear_query_history
from datetime import datetime, timedelta, UTC

# Clear all query history
result = await clear_query_history()

# Clear history for a specific user
result = await clear_query_history(user_id="user123")

# Clear history before a specific date
before_date = datetime.now(UTC) - timedelta(days=90)
result = await clear_query_history(before_date=before_date)

print(result["deleted_count"])  # Number of queries deleted
print(result["success"])  # True if successful
```

## Query History Schema

Each stored query includes:

- **query_id**: Unique identifier for the query
- **query_text**: Original query text
- **timestamp**: When the query was stored (ISO format)
- **intent**: Query intent (SEARCH, CONTROL, STATUS, etc.)
- **domain**: Predicted entity domain (light, sensor, etc.)
- **result_count**: Number of results returned
- **selected_entity_id**: Entity ID that was selected/used (if any)
- **user_id**: Optional user identifier
- **context**: Context information (time_of_day, area, etc.)
- **results**: Summary of top results with rankings

## Learning from Queries

The module learns from user queries and selections:

1. **Entity Popularity**: Tracks how often entities are selected
2. **Query Patterns**: Identifies common query patterns
3. **Personalization**: Adapts to user preferences over time

### Example: Learning from User Selection

```python
# User searches for "living room lights"
results = await semantic_search("living room lights")

# User selects "light.living_room"
await store_query_history(
    query="living room lights",
    results=results,
    selected_entity_id="light.living_room",
)

# Future searches will boost "light.living_room" based on popularity
future_results = await semantic_search("lights")
boosted_results = await boost_entity_ranking(future_results)
```

## Integration with Semantic Search

The history module integrates seamlessly with semantic search:

```python
from app.core.vectordb.history import store_query_history, boost_entity_ranking
from app.core.vectordb.search import semantic_search

# Perform semantic search
results = await semantic_search("living room lights")

# Boost results based on popularity
boosted_results = await boost_entity_ranking(results)

# Store query history
await store_query_history(
    query="living room lights",
    results=boosted_results,
    selected_entity_id=boosted_results[0]["entity_id"] if boosted_results else None,
)
```

## Query Statistics

The statistics module provides insights into query patterns:

### Most Common Queries

```python
stats = await get_query_statistics(days=30)
for query_info in stats["most_common_queries"]:
    print(f"{query_info['query']}: {query_info['count']} times")
```

### Most Common Intents

```python
stats = await get_query_statistics(days=30)
for intent_info in stats["most_common_intents"]:
    print(f"{intent_info['intent']}: {intent_info['count']} times")
```

### Most Selected Entities

```python
stats = await get_query_statistics(days=30)
for entity_info in stats["most_selected_entities"]:
    print(f"{entity_info['entity_id']}: {entity_info['count']} times")
```

### Time-Based Patterns

```python
stats = await get_query_statistics(days=30)
print(stats["queries_by_time_of_day"])
# {
#     "morning": 50,
#     "afternoon": 30,
#     "evening": 40,
#     "night": 10
# }
```

## Privacy Considerations

The history module supports privacy controls:

- **User Identification**: Optional user IDs for multi-user scenarios
- **History Clearing**: Clear history for specific users or time periods
- **Data Retention**: Control how long history is retained

### Example: Privacy Controls

```python
# Clear history for a specific user
await clear_query_history(user_id="user123")

# Clear old history (older than 90 days)
before_date = datetime.now(UTC) - timedelta(days=90)
await clear_query_history(before_date=before_date)
```

## Best Practices

1. **Store queries after user interaction**: Store query history after the user selects an entity or performs an action.

2. **Use popularity boosting judiciously**: Don't over-boost popular entities; maintain a balance with semantic similarity.

3. **Clear old history regularly**: Implement retention policies to clear old history and maintain performance.

4. **Respect user privacy**: Provide users with controls to view and clear their query history.

5. **Monitor statistics**: Use query statistics to understand user patterns and improve search accuracy.

## Limitations

- **Simplified popularity tracking**: Current implementation uses a simplified popularity counter. Future versions may include more sophisticated learning algorithms.

- **No conversation context**: Each query is stored independently. Future versions may support conversation context.

- **Storage limitations**: Query history is stored in the vector database. Large histories may require additional storage management.

## Future Enhancements

Future versions may include:
- ML-based learning algorithms
- Conversation context tracking
- Advanced pattern recognition
- Multi-user personalization
- Query correction and refinement
- Auto-complete suggestions
