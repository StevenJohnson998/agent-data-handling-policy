# Third-Party Sharing Rules

How ADHP handles third-party data sharing, including non-agent third parties.

---

## The Problem

An agent might be Level 3 (strict) in how IT handles your data. But if it sends your data to Google Analytics, an advertising network, or an undisclosed "partner" -- your data ends up at Level 0 regardless of the agent's own practices.

ADHP treats third-party sharing as part of the trust chain.

---

## Types of Third Parties

### 1. Agent (in registry)

The third party is another AI agent registered in the same registry. Its ADHP level is known and verified.

```json
{
  "name": "ClauseAnalyzer",
  "type": "agent",
  "purpose": "subprocessing",
  "data_shared": ["financial"],
  "adhp_level": "strict",
  "registry_id": "a1b2c3d4-uuid"
}
```

This is the best case -- the registry can validate the full chain.

### 2. Non-Agent (external service)

The third party is an external service that is not an AI agent (analytics, payment processor, cloud storage, marketing tool).

```json
{
  "name": "Google Analytics",
  "type": "non_agent",
  "purpose": "analytics",
  "data_shared": ["usage_metadata"],
  "adhp_level": null
}
```

Since non-agents don't have ADHP levels, the effective level depends on what data is shared:
- Metadata only (timestamps, counts) -> no impact on ADHP level
- Any PII or content -> treated as Level 0

### 3. Undisclosed

The agent shares data with third parties but won't say who.

```json
{
  "type": "undisclosed",
  "purpose": "unspecified"
}
```

**Always treated as Level 0.** If an agent has undisclosed third parties, its effective ADHP level for callers drops to Level 0 regardless of its own declared level.

---

## Effective Level Calculation

An agent's **effective ADHP level** (what the caller actually gets) is the minimum of:

1. The agent's own declared level
2. The lowest third-party level in the chain

**Examples:**

| Agent Level | Third Parties | Effective Level |
|-------------|--------------|-----------------|
| strict (3) | None | strict (3) |
| strict (3) | Agent at strict (3) | strict (3) |
| strict (3) | Agent at standard (1) | standard (1) |
| strict (3) | Non-agent, metadata only | strict (3) |
| strict (3) | Non-agent, shares PII | open (0) |
| strict (3) | Undisclosed | open (0) |
| standard (1) | None | standard (1) |

---

## Full Manifest Example: Honest Agent with Third Parties

```json
{
  "agent_name": "SmartAssistant",
  "data_handling": {
    "level": "sensitive",
    "training_opt_out": true,
    "max_retention": "7d",
    "content_logging": false,
    "delegation_policy": "same_or_higher",
    "output_sanitization": true,
    "compliance": ["GDPR"],
    "third_party_sharing": {
      "enabled": true,
      "parties": [
        {
          "name": "Stripe",
          "type": "non_agent",
          "purpose": "subprocessing",
          "data_shared": ["financial"],
          "adhp_level": null
        },
        {
          "name": "AnalyticsBot",
          "type": "agent",
          "purpose": "analytics",
          "data_shared": ["usage_metadata"],
          "adhp_level": "standard",
          "registry_id": "x9y8z7-uuid"
        }
      ],
      "opt_out_available": true
    }
  }
}
```

This agent is transparent: it shares financial data with Stripe (non-agent) and usage metadata with AnalyticsBot (a registered agent at Level 1). A caller requesting Level 2 would need to evaluate whether Stripe's handling of financial data is acceptable.

---

## Recommendations for Agent Operators

1. **Disclose everything.** Undisclosed third parties automatically drop you to Level 0.
2. **Use registered agents** for delegation when possible -- their ADHP level is verifiable.
3. **Minimize data shared** with non-agents. Share metadata instead of content.
4. **Offer opt-out** for third-party sharing when practical.
5. **Separate analytics from processing.** Don't mix usage tracking with data handling.
