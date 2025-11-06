# Vector DB Testing Guide

This document provides comprehensive information about testing the Vector DB integration, including unit tests, integration tests, and performance benchmarks.

## Overview

The Vector DB integration includes comprehensive test coverage across multiple layers:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test components working together with real Home Assistant instances
- **Performance Tests**: Benchmark operations with large datasets

## Test Structure

```
tests/
├── unit/
│   ├── test_vectordb_backend.py          # Abstract backend interface tests
│   ├── test_vectordb_chroma_backend.py    # Chroma backend implementation tests
│   ├── test_vectordb_config.py           # Configuration tests
│   ├── test_vectordb_config_enhanced.py  # Enhanced configuration tests
│   ├── test_vectordb_embeddings.py       # Embedding model tests
│   ├── test_vectordb_manager.py          # Manager singleton tests
│   ├── test_vectordb_indexing.py         # Entity indexing tests
│   ├── test_vectordb_search.py          # Semantic search tests
│   ├── test_vectordb_classification.py   # Query classification tests
│   ├── test_vectordb_history.py         # Query history tests
│   ├── test_vectordb_relationships.py   # Relationship graph tests
│   └── test_vectordb_description.py      # Description generation tests
├── integration/
│   ├── test_vectordb_indexing.py         # Integration tests for indexing
│   ├── test_vectordb_search.py           # Integration tests for search
│   ├── test_vectordb_query_processing.py # Integration tests for query processing
│   └── test_vectordb_entity_suggestions.py # Integration tests for suggestions
└── performance/
    └── test_vectordb_performance.py       # Performance benchmarks
```

## Running Tests

### Unit Tests

Run all unit tests:

```bash
uv run pytest tests/unit/test_vectordb*.py -v
```

Run specific test file:

```bash
uv run pytest tests/unit/test_vectordb_manager.py -v
```

Run with coverage:

```bash
uv run pytest tests/unit/test_vectordb*.py --cov=app/core/vectordb --cov-report=term-missing
```

### Integration Tests

Integration tests require a running Home Assistant instance. Set environment variables:

```bash
export HA_URL=http://localhost:8123
export HA_TOKEN=your_token_here
```

Run integration tests:

```bash
uv run pytest tests/integration/test_vectordb*.py -v -m integration
```

### Performance Tests

Run performance benchmarks:

```bash
uv run pytest tests/performance/test_vectordb_performance.py -v -m performance
```

## Test Coverage

The Vector DB codebase aims for >90% test coverage. Current coverage includes:

- **Backend Interface**: 100% coverage
- **Chroma Backend**: ~58% coverage (needs improvement)
- **Configuration**: ~95% coverage
- **Embeddings**: ~63% coverage (needs improvement)
- **Manager**: ~63% coverage (needs improvement)
- **Indexing**: ~79% coverage
- **Search**: ~80% coverage
- **Classification**: ~99% coverage
- **History**: ~79% coverage
- **Relationships**: ~80% coverage
- **Description**: ~87% coverage

### New Test Suites

The following new test suites have been added to improve coverage:

- **Error Handling Tests** (`test_vectordb_error_handling.py`): Comprehensive tests for error handling and fallback behavior
  - Manager initialization errors
  - Backend health check failures
  - Search fallback to keyword search
  - Disabled vector DB handling
  - Empty results handling
  - Runtime errors for uninitialized manager

- **Batch Operations Tests** (`test_vectordb_batch_operations.py`): Tests for batch operations
  - Batch entity indexing (success, partial failure, all failures)
  - Empty batch handling
  - Large batch processing (100+ entities)
  - Batch embedding generation
  - Batch vector addition
  - Vector DB disabled handling
  - Embedding errors

- **Backend Fallback Tests** (`test_vectordb_backend_fallbacks.py`): Tests for backend fallback behavior
  - Unsupported backends (Qdrant, Weaviate, Pinecone)
  - Invalid backend handling
  - Chroma backend import errors
  - Chroma backend initialization errors
  - Embedding model fallbacks
  - Missing API keys (OpenAI, Cohere)
  - Sentence-transformers import errors

## Unit Test Details

### Backend Tests

Tests for the abstract `VectorDBBackend` interface ensure all implementations follow the contract:

```python
def test_abstract_methods():
    """Test that all abstract methods are defined."""
    # Ensures all backends implement required methods
```

### Chroma Backend Tests

Comprehensive tests for the Chroma implementation:

- Initialization (success and failure cases)
- Health checks
- Collection operations (create, exists, stats)
- Vector operations (add, search, update, delete)
- Error handling

### Configuration Tests

Tests for configuration loading and validation:

- Default configuration
- Environment variable overrides
- Config file loading (JSON/YAML)
- Configuration validation
- Error handling for invalid configurations

### Embedding Model Tests

Tests for embedding model initialization and usage:

- Sentence-transformers initialization
- OpenAI initialization
- Cohere initialization
- Embedding generation
- Error handling for missing dependencies

### Manager Tests

Tests for the VectorDBManager singleton:

- Initialization (success, disabled, unsupported backend)
- Health checks
- Embedding generation
- Vector operations
- Singleton pattern enforcement

### Indexing Tests

Tests for entity indexing:

- Single entity indexing
- Batch entity indexing
- Entity description generation
- Metadata generation
- Update and removal operations
- Error handling

### Search Tests

Tests for semantic search:

- Basic semantic search
- Search with filters (domain, area)
- Similarity threshold filtering
- Hybrid search (semantic + keyword)
- Result ranking and boosting
- Error handling and fallbacks

### Classification Tests

Tests for query intent classification:

- Intent classification (SEARCH, CONTROL, STATUS, etc.)
- Domain prediction
- Action extraction
- Entity extraction
- Parameter extraction
- Query refinement

### History Tests

Tests for query history and learning:

- Storing query history
- Retrieving query history
- Query statistics
- Entity popularity calculation
- Personalized ranking

### Relationship Tests

Tests for entity relationship graph:

- Building relationship graph
- Querying related entities
- Relationship statistics
- Various relationship types

### Description Tests

Tests for entity description generation:

- Template-based descriptions
- Domain-specific templates
- Batch description generation
- Error handling

## Integration Test Details

### Indexing Integration Tests

Test entity indexing with real Home Assistant instances:

- Index single entity
- Index multiple entities
- Update entity index
- Remove entity from index
- Get indexing status

### Search Integration Tests

Test semantic search with real data:

- Basic semantic search
- Search with domain filter
- Search with area filter
- Search with similarity threshold
- Hybrid search

### Query Processing Integration Tests

Test query processing pipeline:

- Intent classification
- Domain prediction
- Action extraction
- Entity extraction
- Parameter extraction
- Query refinement
- Full pipeline processing

### Entity Suggestions Integration Tests

Test entity suggestions with real data:

- Suggestions by area
- Suggestions by device
- Suggestions by domain
- Multiple relationship types

## Performance Test Details

### Indexing Performance

Benchmarks entity indexing with different batch sizes:

- Small batches (10 entities)
- Medium batches (50 entities)
- Large batches (100 entities)
- Measures entities per second

### Search Performance

Benchmarks search operations:

- Different query types
- Response time measurements
- Result count analysis

### Embedding Generation Performance

Benchmarks embedding generation:

- Different text lengths
- Generation time measurements

### Concurrent Operations

Tests concurrent operations:

- Multiple simultaneous searches
- Performance under load

### Large Entity Sets

Tests with large datasets (1000+ entities):

- Indexing performance
- Search performance
- Memory usage

## Writing New Tests

### Unit Test Template

```python
"""Unit tests for module_name."""

import pytest
from unittest.mock import MagicMock, patch

from app.core.vectordb.module_name import FunctionName


class TestFunctionName:
    """Test the FunctionName class/function."""

    @pytest.fixture
    def mock_dependency(self):
        """Create a mock dependency."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_success_case(self, mock_dependency):
        """Test successful operation."""
        with patch("module.dependency", mock_dependency):
            result = await FunctionName()
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            await FunctionName(invalid_input)
```

### Integration Test Template

```python
"""Integration tests for module_name."""

import pytest

from app.core.vectordb.module_name import FunctionName


@pytest.mark.integration
@pytest.mark.asyncio
async def test_function_with_real_ha():
    """Test function with real Home Assistant."""
    from app.core.vectordb.manager import get_vectordb_manager

    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Test with real data
    result = await FunctionName()
    assert result is not None
```

### Performance Test Template

```python
"""Performance tests for module_name."""

import time
import pytest

from app.core.vectordb.module_name import FunctionName


@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_benchmark():
    """Benchmark function performance."""
    from app.core.vectordb.manager import get_vectordb_manager

    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    start_time = time.time()
    result = await FunctionName()
    elapsed_time = time.time() - start_time

    assert result is not None
    print(f"\nTime: {elapsed_time:.3f}s")
```

## Test Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Mocking**: Use mocks for external dependencies
3. **Coverage**: Aim for >90% code coverage
4. **Edge Cases**: Test error conditions and edge cases
5. **Performance**: Include performance tests for critical operations
6. **Documentation**: Document test purpose and expected behavior

## Troubleshooting

### Tests Failing Due to Missing Dependencies

If tests fail with import errors for optional dependencies (e.g., `chromadb`, `sentence_transformers`), ensure they are installed:

```bash
uv pip install chromadb sentence-transformers
```

Or install all vector DB dependencies:

```bash
uv pip install -e ".[vectordb-all]"
```

### Integration Tests Skipped

Integration tests are automatically skipped if Home Assistant is not available. To run them:

1. Start Home Assistant
2. Set `HA_URL` and `HA_TOKEN` environment variables
3. Run tests with `-m integration` marker

### Performance Tests Slow

Performance tests may take longer to run. Use pytest markers to skip them during regular test runs:

```bash
# Skip performance tests
uv run pytest -m "not performance"
```

## Continuous Integration

Tests are automatically run in CI/CD pipelines:

- Unit tests run on every commit
- Integration tests run on pull requests (if HA available)
- Performance tests run on scheduled basis

## Contributing

When adding new Vector DB features:

1. Write unit tests first (TDD approach)
2. Add integration tests for real-world scenarios
3. Add performance tests for critical operations
4. Ensure >90% code coverage
5. Update this documentation
