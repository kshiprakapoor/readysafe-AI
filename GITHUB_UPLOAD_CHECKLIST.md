# GitHub Upload Checklist

Upload the **contents of this folder**, not the ZIP itself.

Your repository root should show:

- `app.py`
- `README.md`
- `DEPLOYMENT.md`
- `requirements.txt`
- `Dockerfile`
- `.gitignore`
- `.streamlit/`
- `agent/`
- `observability/`
- `data/`
- `tests/`
- `infrastructure/`

## Suggested repository

**Name:** `readysafe-ai`

**Description:**  
`Governed enterprise-agent prototype for worker readiness: tool calling, RBAC, human approvals, retries, auditability, and AWS production mapping.`

## Suggested Streamlit custom URL

`kshipra-readysafe-ai`

## After GitHub upload

1. Confirm the `data/` folder contains all six synthetic datasets.
2. Confirm `.streamlit/config.toml` exists.
3. Confirm no `__pycache__` or `.pyc` files were uploaded.
4. Connect the GitHub repo to Streamlit Community Cloud.
5. Entry point: `app.py`.
6. Make the app public.
7. Test these scenarios:
   - Emergency replacement → should require human approval.
   - Emergency replacement + simulated 503 → should retry once.
   - Unauthorized allowance change as Customer Service → should be denied.
   - Same allowance change as Program Administrator → should succeed.
   - Return request → embellished item should not be automatically returned.
