# Configuration Design Discussion

## Current Config Analysis

### Problems with Complex Rule-Based Approach

**Developer Experience Issues:**
- Multiple rule types (path, file_type, precedence) create cognitive overhead
- Developer needs to understand 4 different extraction mechanisms
- Hard to predict which rule will fire for a given file
- Debugging requires tracing through multiple rule layers

**Maintenance Burden:**
- Regex-like patterns `/{department}/{sensitivity_level}/` are error-prone
- Inconsistent structure: `file_path_rules` (array) vs `file_type_rules` (object)
- Different extraction syntaxes (`from_path` vs `{year}-{month}`)
- Mixed concerns (metadata schema + extraction rules)

**Operational Risks:**
- Brittle path matching requires perfect folder organization
- No clear handling when path doesn't match any pattern
- Complex precedence logic can produce unexpected results

## Alternative Approaches

### Option 1: Simplified Rule Format

**Single, consistent rule syntax:**
```yaml
metadata_schema:
  department: ["sales", "engineering", "hr", "finance"]
  document_type: ["report", "contract", "memo", "minutes"]
  sensitivity_level: ["public", "internal", "confidential"]

extraction_rules:
  - match: "path:/sales/confidential/"
    extract: {department: "sales", sensitivity_level: "confidential"}
  
  - match: "filename:*report*.pdf"
    extract: {document_type: "report"}
  
  - match: "extension:.csv"
    extract: {document_type: "tabular_data"}
```

**Pros:**
- Consistent syntax across all rule types
- Easy to understand and debug
- Clear match conditions

**Cons:**
- Still requires manual rule definition
- Path organization dependency remains

### Option 2: Convention Over Configuration

**Minimal config, maximum automation:**
```yaml
# Define what to extract, let LLM figure out how
metadata_fields:
  department:
    type: "enum"
    values: ["sales", "engineering", "hr", "finance"]
    
  document_type:
    type: "enum" 
    values: ["report", "contract", "memo", "minutes", "tabular_data"]
    
  sensitivity_level:
    type: "enum"
    values: ["public", "internal", "confidential"]
    
  creation_date:
    type: "date"
    
  summary:
    type: "text"
    max_length: 100

# Optional hints for common patterns
extraction_hints:
  department_from_path: 1      # Extract from 1st folder
  sensitivity_from_path: 2     # Extract from 2nd folder
  date_from_filename: true     # Look for YYYY-MM-DD patterns
```

**Pros:**
- Minimal configuration required
- LLM handles complex extraction logic
- Adapts to different folder structures
- Easy to add new metadata fields

**Cons:**
- Less predictable extraction
- Higher LLM costs for complex logic
- Requires robust LLM prompting

### Option 3: Hybrid Approach

**Combine simple rules with LLM fallback:**
```yaml
metadata_schema:
  department: ["sales", "engineering", "hr", "finance"]
  document_type: ["report", "contract", "memo", "minutes"]
  sensitivity_level: ["public", "internal", "confidential"]

# Simple path conventions
path_extraction:
  pattern: "/{department}/{sensitivity_level}/"
  fallback_to_llm: true

# File-type specific processing
file_processing:
  csv_files:
    extract_columns: true
    extract_row_count: true
  
  pdf_files:
    extract_page_count: true
    max_content_analysis: 5000  # chars

# LLM handles everything else
llm_extraction:
  required_fields: ["department", "document_type", "sensitivity_level"]
  optional_fields: ["author", "creation_date", "summary", "keywords"]
```

**Pros:**
- Simple for common cases
- Flexible for edge cases
- Predictable path extraction with LLM backup
- Clear separation of concerns

**Cons:**
- Still some complexity
- Requires both rule engine and LLM integration

## Recommendation

**Choose Option 2: Convention Over Configuration**

**Rationale:**
1. **Simplicity**: Minimal config reduces maintenance burden
2. **Flexibility**: Adapts to different organizational structures
3. **Future-proof**: Easy to add new metadata fields
4. **LLM-native**: Leverages AI strengths rather than fighting them

**Implementation Strategy:**
1. Start with basic enum-based extraction
2. Add path hints for common patterns
3. Use structured prompting for consistent results
4. Implement validation and fallbacks

**Migration Path:**
- Current complex rules → Simple field definitions
- Path patterns → Optional hints
- File-type rules → Processing flags
- Precedence logic → LLM prompt engineering

This approach aligns with the project's AI-first philosophy while maintaining developer productivity and operational simplicity.
## Conversion Example: Current → Option 2

### Current Config (100+ lines)
```yaml
rules:
  file_patterns:
    - pattern: "**/*.pdf"
      schema:
        type: "object"
        properties:
          department:
            type: "string"
            description: "Department name (e.g., Sales, Engineering, HR)"
          document_type:
            type: "string"
            enum: ["contract", "report", "proposal", "manual", "others"]
          # ... 20+ more lines per file type
    - pattern: "reports/**/*.csv"
      # ... another 20+ lines
    # ... 4 more file patterns
```

### Option 2 Config (30 lines)
```yaml
# Define what to extract, let LLM figure out how
metadata_fields:
  department:
    type: "enum"
    values: ["sales", "engineering", "hr", "finance", "marketing", "operations"]
    
  document_type:
    type: "enum"
    values: ["contract", "report", "proposal", "manual", "memo", "minutes", "tabular_data", "others"]
    
  sensitivity_level:
    type: "enum"
    values: ["public", "internal", "confidential", "restricted"]
    
  author:
    type: "text"
    description: "Author name or creator"
    
  creation_date:
    type: "date"
    description: "Creation date in YYYY-MM-DD format"
    
  summary:
    type: "text"
    max_length: 100

required_fields: ["department", "document_type", "sensitivity_level"]

# File-specific additions
file_type_fields:
  csv:
    data_period: {type: "text", description: "Data period (e.g., 2024Q1)"}
    columns_summary: {type: "text", description: "Main columns summary"}
    record_count: {type: "integer", description: "Number of records"}
    required: ["data_period"]

# Optional hints for common patterns
extraction_hints:
  department_from_path: 1      # 1st folder
  sensitivity_from_path: 2     # 2nd folder
  date_from_filename: true     # YYYY-MM-DD patterns
```

### Key Changes

**Eliminated:**
- File pattern matching (`**/*.pdf`, `reports/**/*.csv`)
- Duplicate field definitions across file types
- Complex schema structures
- Path-specific rules

**Simplified:**
- Single field definition applies to all files
- LLM handles extraction logic
- Optional hints replace rigid rules
- File-specific fields only where needed

**Benefits:**
- 70% reduction in config size
- No more duplicate field definitions
- Works with any folder structure
- Easy to add new metadata fields
- LLM adapts to content variations

This approach transforms a complex rule engine into a simple field definition that leverages AI for intelligent extraction.
