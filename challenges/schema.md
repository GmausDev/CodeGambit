# Challenge YAML Schema

## Overview

Each challenge in CodeGambit is defined as a YAML file following a strict schema. Challenges are used across three interaction modes (socratic, adversarial, collaborative) and span five difficulty bands.

## Schema Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (e.g., `cal-001-hello-langchain`) |
| `title` | string | Human-readable challenge title |
| `description` | string (markdown) | Detailed challenge description |
| `domain` | string | Always `"langchain"` for MVP |
| `domain_version` | string | Target LangChain version (e.g., `"0.3.x"`) |
| `difficulty` | enum | One of: `beginner`, `intermediate`, `advanced`, `expert`, `master` |
| `elo_band` | integer | One of: `800`, `1000`, `1200`, `1400`, `1600` |
| `mode` | enum | One of: `socratic`, `adversarial`, `collaborative` |
| `category` | enum | One of: `calibration`, `training` |
| `tags` | list[string] | Topical tags for filtering |
| `estimated_minutes` | integer | Estimated completion time |
| `rubric` | object | Evaluation rubric with weighted criteria |
| `test_cases` | list[object] | At least 2 test cases |
| `reference_solution` | string | Complete working reference solution |
| `constraints` | list[string] | Rules and restrictions for the challenge |

### Mode-Specific Fields

#### Socratic Mode
| Field | Type | Description |
|-------|------|-------------|
| `starter_code` | string | Optional starting code template |
| `socratic_questions` | list[string] | 3-5 guiding questions |

#### Adversarial Mode
| Field | Type | Description |
|-------|------|-------------|
| `buggy_code` | string | Pre-loaded code with intentional bugs |
| `bugs` | list[object] | Bug descriptions with id, description, severity |

#### Collaborative Mode
| Field | Type | Description |
|-------|------|-------------|
| `steps` | list[object] | 3-5 incremental build steps |
| `starter_code` | string | Optional starting code template |

### Rubric Structure

```yaml
rubric:
  architecture:
    weight: 0.30           # float, all weights must sum to 1.0
    criteria:
      - "Specific criterion"
  framework_depth:
    weight: 0.40
    criteria:
      - "Specific criterion"
  complexity_mgmt:
    weight: 0.30
    criteria:
      - "Specific criterion"
```

### Bug Structure (Adversarial)

```yaml
bugs:
  - id: "bug-1"
    description: "What the bug is"
    severity: "critical"   # critical | major | minor
```

### Step Structure (Collaborative)

```yaml
steps:
  - id: "step-1"
    title: "Step title"
    description: "What to build in this step"
```

### Test Case Structure

```yaml
test_cases:
  - name: "Test name"
    code: |
      result = function_under_test()
      assert result is not None
```

## Difficulty Bands

| Band | Difficulty | Topics |
|------|-----------|--------|
| 800 | Beginner | Basic LLM calls, ChatPromptTemplate, simple chains |
| 1000 | Intermediate | LCEL composition, output parsers, basic retrieval |
| 1200 | Advanced | RAG pipelines, conversation memory, agent basics |
| 1400 | Expert | Custom tools, multi-retriever, advanced agents |
| 1600 | Master | LangGraph workflows, production patterns, error handling |

## LangChain 0.3.x API Notes

- Use LCEL pipe (`|`) syntax, not legacy `Chain` classes
- Use `ChatPromptTemplate`, not `PromptTemplate`
- Use `RunnableWithMessageHistory`, not `ConversationBufferMemory` (deprecated)
- Use `create_react_agent` with LangGraph, not `AgentExecutor`
- Use `TypedDict` for LangGraph state, not plain `dict`
