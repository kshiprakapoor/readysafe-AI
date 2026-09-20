# ReadySafe AI
### Agentic automation that helps workers start every shift protected

ReadySafe AI is a **synthetic enterprise-agent portfolio project** inspired by the operational
challenge of managed protective-apparel programs. It demonstrates how an AI agent can coordinate
worker profiles, employer program rules, approved products, inventory, allowances, approvals,
orders, and audit logging without allowing the model to override controlled safety policy.

> **No Tyndale or customer data are used.** Every employee, program, order, product, inventory
> record, and rule in this repository is fictional and created solely for demonstration.

## Why this project exists

A production AI agent should do more than answer questions. It should be able to:

- identify the correct business workflow;
- retrieve information through explicit tools;
- respect role-based permissions;
- apply deterministic business rules;
- pause for human approval when required;
- handle transient system failures;
- execute authorized actions; and
- leave an auditable trace of what happened.

ReadySafe demonstrates those ideas in a small, transparent application.

## Demo scenarios

1. **Emergency replacement** — resolve a backordered FR jacket before a worker's next shift.
2. **New employee setup** — retrieve the worker's program, approved categories, and allowance.
3. **Better fit** — find an approved women's-fit garment in the worker's size and allowance.
4. **Return request** — apply deterministic return rules to an embellished garment.
5. **Unauthorized allowance change** — demonstrate role-based access control.

The emergency replacement scenario intentionally creates a small allowance exception so the
workflow must pause for **human approval** before creating the replacement.

## Core architecture

```text
Worker request
      |
      v
Intent / workflow planner
      |
      v
Explicit enterprise tools
      |
      +--> worker.get_profile
      +--> program.get_rules
      +--> orders.find_recent
      +--> inventory.search
      +--> allowance.check
      +--> orders.create_replacement
      +--> returns.evaluate
      +--> notifications.send
      |
      v
Deterministic policy + guardrails
      |
      v
Human approval (when required)
      |
      v
Authorized transaction
      |
      v
Audit / observability trace
```

## Engineering features

- **Python tool layer** that mirrors REST/OpenAPI enterprise integrations.
- **Role-based access control** for Customer Service vs Program Administrator.
- **Human-in-the-loop approval** for exceptions.
- **Retry logic** with a user-controlled synthetic HTTP 503 failure.
- **Deterministic safety guardrails** that prevent workflow logic from overriding PPE policy.
- **Execution telemetry** for tool calls, latency, retries, denials, and approvals.
- **Synthetic enterprise data** exposed in the app for transparency.
- **Unit tests** for policy, permissions, and end-to-end workflows.
- **Dockerfile** and Streamlit deployment configuration.
- **AWS production mapping** for Bedrock/AgentCore, Lambda, API Gateway, IAM,
  Secrets Manager, CloudWatch/OpenTelemetry, and Dev/UAT/Production promotion.

## Repository structure

```text
readysafe-ai/
├── app.py
├── agent/
│   ├── orchestrator.py
│   ├── tools.py
│   ├── planner.py
│   ├── policy_engine.py
│   ├── guardrails.py
│   └── bedrock_adapter.py
├── observability/
│   └── telemetry.py
├── data/
│   ├── employees.csv
│   ├── products.csv
│   ├── inventory.csv
│   ├── orders.csv
│   ├── programs.json
│   └── scenarios.json
├── tests/
│   ├── test_policies.py
│   ├── test_permissions.py
│   └── test_workflows.py
├── infrastructure/
│   └── aws_architecture.md
├── .streamlit/
│   └── config.toml
├── DEPLOYMENT.md
├── Dockerfile
├── requirements.txt
└── README.md
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

## Public demo vs production

The public app intentionally uses a deterministic planner so it can run safely and
reproducibly without cloud credentials. In production, an approved Bedrock model can interpret
free-form requests and emit structured plans, while the deterministic policy, permission,
approval, and transaction layers remain authoritative.

See [`infrastructure/aws_architecture.md`](infrastructure/aws_architecture.md).

## Interview talking point

> I built an end-to-end enterprise-agent prototype that turns a worker request into a governed
> business workflow. The agent calls explicit tools, applies source-controlled program rules,
> enforces role-based permissions, pauses for human approval on exceptions, retries transient
> failures, executes authorized actions, and exposes a full audit trace. I designed the public
> version to run on synthetic data with no credentials, while mapping the same architecture to
> Bedrock/AgentCore and AWS production services.
