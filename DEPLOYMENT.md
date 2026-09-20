# Deployment Guide

## Streamlit Community Cloud

1. Create a GitHub repository, e.g. `readysafe-ai`.
2. Upload the complete contents of this project.
3. Connect the repository to Streamlit Community Cloud.
4. Select branch `main`.
5. Set the entry point to `app.py`.
6. Deploy.

The public demo requires no API keys.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

Windows activation:

```text
.venv\Scripts\activate
```

## Docker

```bash
docker build -t readysafe-ai .
docker run -p 8501:8501 readysafe-ai
```

Then open `http://localhost:8501`.

## Recommended GitHub description

`Governed enterprise-agent prototype for worker readiness: tool calling, RBAC, human approvals, retries, auditability, and AWS production mapping.`

## Recommended Streamlit URL

`kshipra-readysafe-ai.streamlit.app`

If unavailable, use `readysafe-agent.streamlit.app` or `readysafe-ops-ai.streamlit.app`.
