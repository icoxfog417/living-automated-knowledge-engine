# Project Rules and Coding Guidelines

## Python Environment Management

Use `uv` for all Python operations:
```bash
uv run python script.py
uv run pytest
uv run ruff check
```

## Development Workflow

Follow this sequence for all changes:

### 1. Planning Phase
If changes affect other components (side effects), write design documentation in `spec/history/`:
- File naming: `01_change_how_to_interact_with_knowledge.md`, `02_delete_agent_ui.md`, etc.
- Document architectural impacts and component interactions

### 2. Package Exploration
For first-time package usage, write temporary sample codes in `.workspace/`:
```bash
mkdir -p .workspace
# Write draft scripts to examine package APIs
# Confirm usage patterns before implementation
```

### 3. Test-First Interface Design
Implement test codes to determine class interfaces:
- Define expected behavior through tests
- Do not run tests yet (they will fail without implementation)
- Focus on interface design, not implementation details

### 4. Implementation
Implement the actual code based on test-defined interfaces

### 5. Test Validation
Update test codes and confirm behavior:
- Run tests to validate implementation
- Refine both tests and implementation as needed

### 6. Checkpoint Commit
Commit changes regardless of test pass/fail status:
- Creates checkpoint to prevent dishonest test modifications
- Enables rollback to clean state if needed
- Maintains development history integrity

### 7. Proceed to Next Task
Move to next development cycle after implementation completion

## Python Best Practices

### Import Standards
- Use absolute imports from project root
- Group imports: standard library, third-party, local
- Use type hints and adhere best practice for function comments

```python
import os
from pathlib import Path

from strands import Agent
from bedrock import BedrockClient

from src.agent.support_agent import SupportAgent
```

### Type Hinting
- All function parameters and return types must be annotated
- Use modern type syntax (Python 3.9+)

```python
def search_knowledge(self, query: str) -> list[str]:
    return results
```

### String Formatting
- Use f-strings for string interpolation
- Use `.format()` for complex formatting only

```python
message = f"Found {len(results)} results for query: {query}"
```

## Testing and Code Quality

### Testing with pytest
```bash
uv run pytest tests/
uv run pytest tests/unit/test_agent.py -v
```

### Code Formatting
```bash
uv run ruff check .
uv run ruff check --fix
```

## Project Structure Adherence

Follow the design document structure:
- `src/agent/` - Strands Agent implementation
- `src/knowledge/` - Knowledge source classes (I/O only)
- `src/config/` - Configuration management
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests

## Architecture Principles

1. **Separation of Concerns**: Agent handles search logic, knowledge sources handle I/O only
2. **Dependency Injection**: Pass dependencies explicitly in constructors
3. **Single Responsibility**: Each class has one clear purpose
4. **Use Strands Framework**: Leverage `@tool` decorator, don't build custom tool execution

## Required Dependencies

Core dependencies for the project:
- `strands-agent` - Agent framework
- `boto3` - AWS SDK
- `pytest` - Testing framework
- `ruff` - Code formatting and linting
