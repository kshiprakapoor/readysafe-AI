# Production AWS Mapping

The public Streamlit demo intentionally uses synthetic data and an in-memory deterministic planner.
A production enterprise implementation can preserve the same separation of concerns while moving
the components onto governed AWS services.

| Demo responsibility | Production-oriented AWS mapping |
|---|---|
| User / event entry point | API Gateway, application UI, EventBridge |
| Natural-language planning | Amazon Bedrock model |
| Governed agent runtime / tools | Bedrock AgentCore / AgentCore Gateway |
| Business-process orchestration | Step Functions or Amazon Quick Automate |
| Tool execution | Lambda or internal REST/OpenAPI services |
| Identity / authorization | IAM + application RBAC |
| Credentials / secrets | Secrets Manager |
| State / audit data | DynamoDB, S3, enterprise source systems |
| Logs / traces / metrics | CloudWatch + OpenTelemetry |
| Deployment | GitHub Actions / CodePipeline with Dev → UAT → Production |

## Safety design

The agent should never be the authoritative source of PPE policy. Program eligibility,
approved product catalogs, transaction rules, authorization, and approval thresholds should
remain deterministic, versioned, source-controlled, and independently testable.

## Recommended production controls

- least-privilege IAM roles per tool;
- explicit allow-list of agent-callable APIs;
- schema validation for every tool call;
- idempotency keys on transactional actions;
- human approval for exceptions and high-impact changes;
- immutable audit events;
- retry budgets and dead-letter handling;
- latency, denial, token/cost, and tool-error dashboards;
- prompt/version tracking and regression evaluation;
- Dev/UAT/Production separation;
- rollback plans for both application and agent configuration.
