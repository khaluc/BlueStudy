# Vercel deployment

The Vercel deployment is an explicitly labelled public frontend preview.
It publishes only apps/web, using scripts/build-vercel.mjs and output folder dist.
No API keys are needed. Local Docker continues to run the full application.

The preview does not call local-session, upload documents, or request microphone
access. AI feature links show that the backend has not been connected.

A functional public deployment requires separate hosting for FastAPI, workers,
PostgreSQL, persistent storage and Ollama, plus individual-user authentication.
Do not expose the shared local demo credentials or bypass localhost access checks.
