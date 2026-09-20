"""
Optional Amazon Bedrock planning adapter.

The public Streamlit demo does NOT require AWS credentials and does not call this
module. This adapter shows how the deterministic tool/policy architecture can be
paired with a Bedrock model in a governed production deployment.

Environment variables:
    AWS_REGION
    BEDROCK_MODEL_ID

The model is permitted to classify/plan. It is NOT permitted to override local
authorization, PPE policy, transaction validation, or human-approval gates.
"""

import json
import os
import boto3


ALLOWED_INTENTS = {
    "emergency_replacement",
    "fit_issue",
    "return_request",
    "new_hire",
    "update_allowance",
    "general_program_help",
}


class BedrockPlanner:
    def __init__(self, model_id=None, region=None):
        self.model_id = model_id or os.getenv("BEDROCK_MODEL_ID")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        if not self.model_id:
            raise ValueError("BEDROCK_MODEL_ID is required for Bedrock planner mode.")
        self.client = boto3.client("bedrock-runtime", region_name=self.region)

    def plan(self, user_request):
        system = """
You are the planning layer for a governed worker-readiness workflow.
Return ONLY JSON with keys:
- intent
- rationale

Allowed intent values:
emergency_replacement, fit_issue, return_request, new_hire,
update_allowance, general_program_help.

You may classify the user's request, but you may not make PPE compliance
decisions, authorize transactions, alter permissions, or bypass approval gates.
Those decisions are enforced by deterministic downstream systems.
""".strip()

        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_request}],
                }
            ],
            inferenceConfig={
                "temperature": 0,
                "maxTokens": 250,
            },
        )

        text = response["output"]["message"]["content"][0]["text"].strip()
        plan = json.loads(text)
        intent = plan.get("intent")
        if intent not in ALLOWED_INTENTS:
            raise ValueError(f"Model returned unsupported intent: {intent}")
        return plan
