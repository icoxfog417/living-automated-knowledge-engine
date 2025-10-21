# Fundamental Development Principles

## 1. Separation of Concerns

**Principle**: Separate I/O operations from business logic
- **I/O Layer**: Handle file operations, data loading/saving
- **Processing Layer**: Pure functions with no external dependencies
- **Orchestration Layer**: Coordinate between I/O and processing

**Benefits**: Testability, maintainability, flexibility

## 2. Single Responsibility

**Principle**: Each class should have one clear purpose
- Avoid classes that mix multiple responsibilities
- Eliminate duplicate functionality across classes
- Consolidate related operations into single classes

**Example**: DataStore handles all I/O, not split across multiple classes

## 3. Dependency Injection

**Principle**: Pass dependencies explicitly rather than hardcoding them
- Classes receive their dependencies as constructor parameters
- Enables easy testing with mock objects
- Allows swapping implementations without code changes

**Anti-pattern**: Hardcoded file paths or direct instantiation of dependencies

## 4. Session Safety

**Principle**: Manage resource lifecycle carefully
- Track resource state to prevent duplicate allocation
- Use context managers for automatic cleanup
- Handle partial failures gracefully

**Implementation**: Session state tracking, conditional initialization

## 5. Configuration Over Convention

**Principle**: Make behavior configurable rather than hardcoded
- Allow users to specify file names, paths, parameters
- Provide sensible defaults while enabling customization
- Support multiple input sources (local files, S3, etc.)

## 6. Granular Operations

**Principle**: Provide both atomic and composite operations
- Enable users to run specific steps independently
- Support partial pipeline execution
- Allow resuming from intermediate states

**Benefits**: Debugging, development flexibility, resource efficiency

## 7. Pure Functions Where Possible

**Principle**: Prefer functions without side effects
- Input → Processing → Output (no external state changes)
- Easier to test, reason about, and parallelize
- Separate pure logic from I/O operations

## 8. Fail Fast with Clear Messages

**Principle**: Detect and report errors early with specific information
- Validate inputs at entry points
- Provide actionable error messages with context
- Include relevant identifiers (file names, patient IDs, etc.)

## 9. Encapsulation

**Principle**: Hide implementation details behind clean interfaces
- Use private methods for internal operations
- Expose only necessary public methods
- Group related functionality together

## 10. Resource Management

**Principle**: Handle temporary resources responsibly
- Use temporary directories for session isolation
- Clean up resources automatically
- Prevent resource leaks and contamination between sessions

## Application Guidelines

### When Designing Classes
1. Define single, clear responsibility
2. Identify dependencies and inject them
3. Separate pure logic from I/O operations
4. Provide granular and composite operations

### When Handling Data
1. Use temporary directories for session isolation
2. Support multiple input sources
3. Make file names configurable
4. Implement session safety

### When Building Pipelines
1. Enable partial execution
2. Allow resuming from intermediate states
3. Provide clear error messages
4. Separate orchestration from processing

### When Integrating Components
1. Use dependency injection
2. Avoid tight coupling
3. Enable easy testing
4. Support configuration over hardcoding

These principles ensure maintainable, testable, and flexible code that can adapt to changing requirements while remaining robust and reliable.
