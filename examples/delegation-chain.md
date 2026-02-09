# Delegation Chain Scenarios

How ADHP's delegation cascading rule works in practice.

---

## The Core Rule

When a caller requests processing at a certain ADHP level, **every agent in the delegation chain** must meet or exceed that level. The constraint comes from the **caller's requirement**, not the delegating agent's own level.

---

## Scenario 1: Valid Chain -- All Agents Meet Requirement

```
Caller requests: Level 2 (sensitive)

Agent A          Agent B          Agent C
[strict L3] ---> [sensitive L2] ---> [strict L3]
    OK               OK                 OK

Result: VALID
All agents are Level 2 or above, satisfying the caller's requirement.
```

---

## Scenario 2: Invalid Chain -- Weak Link

```
Caller requests: Level 3 (strict)

Agent A          Agent B          Agent C
[strict L3] ---> [standard L1] ---> [strict L3]
    OK              FAIL               --

Result: INVALID
Agent B (Level 1) is below the caller's Level 3 requirement.
The chain breaks at Agent B. Agent C is not evaluated.
```

---

## Scenario 3: High-Level Agent, Low-Level Request

```
Caller requests: Level 1 (standard)

Agent A            Agent B
[zero-trace L4] is selected, but it cannot delegate at all.

Result: VALID (but no delegation possible)
Level 4 agents cannot delegate regardless of caller's request level.
If Agent A needs help, it must handle everything itself.
```

---

## Scenario 4: High-Level Agent Delegating to Lower (But Sufficient)

```
Caller requests: Level 1 (standard)

Agent A          Agent B
[strict L3] ---> [standard L1]
    OK               OK

Result: VALID
Agent A is Level 3, but the caller only needs Level 1.
Agent B at Level 1 meets the caller's requirement. This is allowed.
```

This is important: agents don't need to delegate "at their own level." They delegate at or above the **caller's level**.

---

## Scenario 5: Third-Party Breaks the Chain

```
Caller requests: Level 2 (sensitive)

Agent A (strict L3) processes data
  |
  |--> delegates to Agent B (sensitive L2) -- OK
  |
  |--> shares with "Analytics Corp" (undisclosed, no ADHP) -- TREATED AS LEVEL 0

Result: INVALID
The undisclosed third party is treated as Level 0, which breaks the chain.
Agent A must either stop sharing with Analytics Corp or disclose their ADHP level.
```

---

## Scenario 6: Complex Multi-Hop Chain

```
Caller requests: Level 2 (sensitive)

Agent A [strict L3]
  |
  |--> Agent B [sensitive L2]
  |      |
  |      |--> Agent D [strict L3]     -- OK
  |      |
  |      |--> Agent E [standard L1]   -- FAIL
  |
  |--> Agent C [strict L3]            -- OK

Result: INVALID
Even though most of the chain is valid, Agent E (Level 1) fails.
The entire chain is invalid because of one weak link.
```

---

## How to Validate

Use the included validation tool:

```bash
python tools/validate_chain.py
```

Or programmatically:

```python
from tools.validate_chain import validate_chain

chain = [
    {"name": "Agent A", "level": "strict"},
    {"name": "Agent B", "level": "sensitive"},
    {"name": "Agent C", "level": "strict"}
]

result = validate_chain(chain, caller_requires="sensitive")
print(result)
# {"valid": True, "reason": "All agents meet caller's minimum level (sensitive)"}
```
