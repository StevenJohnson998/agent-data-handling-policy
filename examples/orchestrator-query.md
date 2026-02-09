# Orchestrator Query Examples

How an orchestrator uses ADHP to discover and select agents.

---

## Scenario 1: Healthcare Company Processing Patient Records

A hospital's AI system needs to analyze patient records. Requirements:
- HIPAA and GDPR compliant
- No training on patient data
- Health and identity PII protected
- Data processed in the EU
- No third-party sharing
- Minimum ADHP Level 3 (strict)

**Query:**

```
GET /agents?capability=medical-analysis
            &min_adhp_level=strict
            &compliance=HIPAA,GDPR
            &pii_categories=health,identity
            &processing_jurisdiction=EU
            &third_party_sharing=false
```

**Response (simplified):**

```json
{
  "results": [
    {
      "name": "MedAnalyzer EU",
      "adhp_level": "strict",
      "compliance": ["GDPR", "HIPAA"],
      "processing_jurisdiction": ["DE"],
      "execution_environment": "TEE",
      "capability_score": 4.7
    },
    {
      "name": "HealthDoc Pro",
      "adhp_level": "zero-trace",
      "compliance": ["GDPR", "HIPAA", "AI_ACT_EU"],
      "processing_jurisdiction": ["FR"],
      "execution_environment": "enclave",
      "capability_score": 4.2
    }
  ],
  "filtered_out": 47,
  "reason": "Did not meet ADHP, compliance, or jurisdiction requirements"
}
```

The orchestrator sees 2 agents out of 49 meet ALL requirements. It picks MedAnalyzer EU based on higher capability score.

---

## Scenario 2: Startup Looking for Cheapest Compliant Option

A startup needs financial analysis. They care about GDPR compliance but are flexible on everything else. Budget matters.

**Query:**

```
GET /agents?capability=financial-analysis
            &min_adhp_level=standard
            &compliance=GDPR
            &sort=cost_asc
```

**Response:**

```json
{
  "results": [
    {
      "name": "BudgetFinance",
      "adhp_level": "standard",
      "compliance": ["GDPR"],
      "max_retention": "30d",
      "capability_score": 3.8,
      "cost_tier": "free"
    },
    {
      "name": "FinanceAnalyzer Pro",
      "adhp_level": "strict",
      "compliance": ["GDPR", "AI_ACT_EU"],
      "max_retention": "request",
      "capability_score": 4.7,
      "cost_tier": "paid"
    }
  ]
}
```

The startup picks BudgetFinance -- it meets their minimum requirements at the lowest cost.

---

## Scenario 3: Orchestrator with Delegation Requirements

A legal firm needs contract review. The reviewing agent might delegate clause analysis to a specialized sub-agent. The firm requires the ENTIRE chain to be at Level 3+.

**Query:**

```
GET /agents?capability=contract-review
            &min_adhp_level=strict
            &delegation_chain_valid=true
```

The registry checks not just the primary agent, but verifies that any agents it might delegate to ALSO meet Level 3+.

**Response:**

```json
{
  "results": [
    {
      "name": "LegalReview Pro",
      "adhp_level": "strict",
      "delegation_policy": "same_or_higher",
      "known_delegates": [
        {
          "name": "ClauseAnalyzer",
          "adhp_level": "strict",
          "chain_valid": true
        }
      ]
    }
  ],
  "filtered_out_reason": "3 agents had delegation chains below strict level"
}
```

---

## Scenario 4: Maximum Privacy -- Zero Trace

A government agency needs document classification. Absolutely nothing can be logged or stored.

**Query:**

```
GET /agents?capability=document-classification
            &min_adhp_level=zero-trace
            &execution_environment=TEE,enclave
```

By requiring `execution_environment` of TEE or enclave, the agency ensures the zero-trace claim is backed by hardware, not just a promise.
