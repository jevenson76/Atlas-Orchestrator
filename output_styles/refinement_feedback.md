---
name: refinement_feedback
version: 1.0.0
model: claude-sonnet-4-5-20250929
enforcement: strict
schema_type: yaml
temperature: 0.2
max_tokens: 2000
retry_on_parse_error: true
retry_attempts: 2
validation_mode: schema_strict
---

# Refinement Feedback Output Style

## Purpose
Extract actionable feedback from validation results for the refinement loop. Output must be concise, structured YAML that drives code regeneration.

## CRITICAL RULES

1. ❌ **NO natural language explanations** outside YAML structure
2. ❌ **NO conversational text** ("Let me analyze...", "Here's the feedback:")
3. ❌ **NO markdown formatting** except YAML code block (if needed)
4. ✅ **ONLY valid YAML** conforming to schema below
5. ✅ **Prioritize** CRITICAL → HIGH → MEDIUM findings
6. ✅ **Maximum 10 feedback items** (most critical first)
7. ✅ **Include fix_snippet** for actionable items
8. ✅ **Start with** `---` (YAML document start marker)

## Output Schema (YAML)

**REQUIRED TOP-LEVEL KEYS:**
- `iteration` (integer): Current iteration number (1, 2, 3...)
- `validation_status` (string): One of [PASS, FAIL, WARNING]
- `validation_score` (float): Average validation score (0-100)
- `critical_count` (integer): Number of critical findings
- `high_count` (integer): Number of high severity findings
- `feedback` (array): List of actionable feedback items (max 10)
- `regeneration_prompt` (string): Concise instructions for next iteration

**Feedback Item Structure:**
```yaml
- priority: CRITICAL|HIGH|MEDIUM
  location: file.py:line
  issue: Brief description of problem
  action: Specific action to fix
  fix_snippet: |
    Exact code fix (optional but recommended)
```

## Complete Example Output

```yaml
---
iteration: 2
validation_status: FAIL
validation_score: 65.0
critical_count: 2
high_count: 3

feedback:
  - priority: CRITICAL
    location: auth.py:42
    issue: SQL injection vulnerability
    action: Replace string interpolation with parameterized query
    fix_snippet: |
      cursor.execute("SELECT * FROM users WHERE username=%s", (username,))

  - priority: CRITICAL
    location: api.py:78
    issue: Missing authentication check on sensitive endpoint
    action: Add @require_auth decorator to endpoint
    fix_snippet: |
      @require_auth
      def api_endpoint():
          # existing code

  - priority: HIGH
    location: config.py:12
    issue: Hardcoded API key in source code
    action: Move to environment variable
    fix_snippet: |
      api_key = os.environ.get("API_KEY")
      if not api_key:
          raise ValueError("API_KEY environment variable not set")

  - priority: HIGH
    location: auth.py:55
    issue: Weak password validation (minimum 6 characters)
    action: Enforce minimum 12 characters with complexity requirements
    fix_snippet: |
      if len(password) < 12:
          raise ValueError("Password must be at least 12 characters")
      if not re.search(r'[A-Z]', password):
          raise ValueError("Password must contain uppercase letter")

  - priority: HIGH
    location: orders.py:78-82
    issue: N+1 query problem in order processing loop
    action: Use eager loading to fetch all customers in one query
    fix_snippet: |
      customer_ids = [order.customer_id for order in orders]
      customers = db.query(Customer).filter(Customer.id.in_(customer_ids)).all()
      customer_map = {c.id: c for c in customers}

regeneration_prompt: |
  Address the following issues in priority order:

  1. CRITICAL - Fix SQL injection in auth.py:42 by using parameterized queries
  2. CRITICAL - Add authentication check to api.py:78 with @require_auth decorator
  3. HIGH - Remove hardcoded API key from config.py:12, use environment variable
  4. HIGH - Strengthen password validation in auth.py:55 (min 12 chars, complexity)
  5. HIGH - Optimize N+1 query in orders.py:78 with eager loading

  Maintain all existing functionality while applying these fixes. Preserve the original code structure and naming conventions.
```

## Minimal Example (Few Issues)

```yaml
---
iteration: 1
validation_status: WARNING
validation_score: 85.0
critical_count: 0
high_count: 1

feedback:
  - priority: HIGH
    location: utils.py:23
    issue: Missing error handling in file read operation
    action: Add try-except block to handle FileNotFoundError
    fix_snippet: |
      try:
          with open(filepath, 'r') as f:
              return f.read()
      except FileNotFoundError:
          logger.error(f"File not found: {filepath}")
          return None

regeneration_prompt: |
  Add error handling to file read operation in utils.py:23. Catch FileNotFoundError and return None with logging.
```

## Validation Rules

**Schema Compliance:**
- Response MUST parse as valid YAML (use yaml.safe_load() without errors)
- MUST contain all required top-level keys
- `validation_status` MUST be one of: PASS, FAIL, WARNING
- `feedback` MUST be an array (list) of objects
- `regeneration_prompt` MUST be a non-empty string

**Feedback Array:**
- Each item MUST have: priority, location, issue, action
- `fix_snippet` is OPTIONAL but strongly recommended
- Maximum 10 items (prioritize most critical)
- Items MUST be ordered by priority (CRITICAL first, then HIGH, then MEDIUM)

**Priority Values:**
- MUST use exactly: CRITICAL, HIGH, MEDIUM (case-sensitive)
- NO LOW or INFO priorities in feedback (filter those out)

**Location Format:**
- MUST be "file.py:line" or "file.py:start-end"
- Example: "auth.py:42" or "orders.py:78-82"

**Regeneration Prompt:**
- MUST be actionable instructions for next iteration
- Should reference specific locations and fixes
- Should maintain original intent and functionality
- Should be concise (max 500 words)

## Feedback Extraction Logic

**Prioritization Rules:**
1. Include ALL CRITICAL findings (up to 10 total)
2. If < 10 items, include HIGH findings (most impactful first)
3. If < 10 items, include MEDIUM findings (most impactful first)
4. Never include LOW or INFO in feedback (too minor for iteration)

**Impact Assessment (for prioritization within same severity):**
- Security vulnerabilities → Highest impact
- Correctness bugs → High impact
- Performance issues → Medium impact
- Code quality issues → Lower impact

## Output Format Requirements

**YAML Structure:**
- Start with `---` (document start marker)
- Use 2-space indentation
- Use `|` for multiline strings (fix_snippet, regeneration_prompt)
- Use flow style for simple values (priority: CRITICAL)

**Code Snippets:**
- Use literal block scalar (`|`) for fix_snippet
- Include proper indentation in code
- Include necessary imports if relevant
- Keep snippets focused (5-15 lines max)

## Error Prevention

**Common Mistakes to AVOID:**
1. ❌ Adding "Here's the feedback:" before YAML
2. ❌ Using lowercase priority ("critical" instead of CRITICAL)
3. ❌ Missing required keys (iteration, feedback, etc.)
4. ❌ Using objects where arrays expected (feedback should be list)
5. ❌ Including LOW/INFO priority items in feedback
6. ❌ Empty regeneration_prompt
7. ❌ More than 10 feedback items
8. ❌ Feedback items not ordered by priority

## Enforcement

This output style uses **SONNET 4.5** with **STRICT enforcement**:
- Model override: claude-sonnet-4-5-20250929
- Temperature: 0.2 (slightly creative for fix suggestions)
- Retries: Up to 2 attempts on parse failure
- Validation: Schema-strict mode (all requirements enforced)

**If validation fails, the system will:**
1. YAML parse error → Retry with syntax correction hints
2. Missing required key → Retry highlighting missing field
3. Max retries exceeded → Raise OutputStyleValidationError

Your output MUST be valid YAML on first attempt.
