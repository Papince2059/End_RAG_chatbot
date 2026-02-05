# Endee RAG Chatbot - Homeopathy Assistant

A Retrieval-Augmented Generation (RAG) system for homeopathy remedies, built with Endee Vector DB, FastAPI, and a modern web UI.

## What This App Does

- Ingests remedy text into Endee as vector embeddings.
- Accepts symptom queries from the UI.
- Retrieves the top-k most similar remedies from Endee.
- Uses Gemini to summarize the top results and answer the query.
- Falls back to pure vector search if Gemini is unavailable.

## Live Ports (Docker Compose)

- Frontend: `http://localhost:3001`
- Backend: `http://localhost:8000`
- Endee: `http://localhost:8080`

## Project Structure

**Root**
- `docker-compose.yml` defines the Endee, backend, and frontend services.
- `.env` provides the Gemini API key and Endee host/port.
- `README.md` this guide.

**Backend (`backend/`)**
- `main.py` FastAPI app with `/api/search` and `/api/chat`.
- `ingest.py` ingestion script (Endee SDK + embeddings).
- `Dockerfile` Python runtime and dependencies.
- `requirements.txt` Python dependencies.

**Frontend (`frontend/`)**
- `index.html` UI layout.
- `app.js` API calls and rendering.
- `styles.css` styling.
- `Dockerfile` Nginx static server.

**Data (`data/`)**
- `remedy_chunks.json` pre-chunked remedy data.
- `boericke_full_text.txt` raw source text.
- `symptom_remedy_examples.txt` sample symptom queries.

**Scripts (`scripts/`)**
- `chunk_remedies.py` builds `remedy_chunks.json`.
- `ingest_remedies_to_endee_sdk.py` ingestion script (SDK variant).

## End-to-End Flow

1. Ingestion (one-time or when data changes)
- Chunk text into remedy chunks.
- Embed each chunk with `all-MiniLM-L6-v2`.
- Upsert vectors + metadata into Endee (`homeopathy_remedies` index).

2. Query
- UI sends query to backend.
- Backend embeds query and retrieves top-k from Endee.

3. RAG Answer
- Backend builds a prompt from retrieved chunks.
- Gemini produces a short summary + final answer.
- UI shows the summary above the top results.

## API Endpoints

- `GET /` health check.
- `GET /api/stats` index status.
- `POST /api/search` vector search only.
- `POST /api/chat` vector search + Gemini summary/answer.

## How To Run (Docker)

1. Set environment variables
- Update `.env` with your `GEMINI_API_KEY`.

2. Start services
```bash
docker compose up -d
```

3. Open the app
- `http://localhost:3001`

4. Stop services
```bash
docker compose down
```

## Ingestion

If you change the source text or want to rebuild the index:

```bash
python backend/ingest.py
```

Make sure Endee is running and reachable at `http://localhost:8080`.

## Notes & Troubleshooting

- Backend uses `http://endee:8080/api/v1` inside Docker.
- If Gemini is unavailable, the UI automatically falls back to `/api/search`.
- If you only see results and no summary, check `GEMINI_API_KEY` and backend logs.
- Frontend runs on port `3001` because port `3000` was already in use.

## Recent Changes

- Frontend port mapped to `3001:80` in `docker-compose.yml`.
- Frontend now falls back to `/api/search` if `/api/chat` fails.
- Gemini prompt updated to include a short summary above results.
- Gemini model selection updated to valid models for your API key.

## Output Screenshot

![Output](https://github.com/user-attachments/assets/74de92ae-e879-4cc5-8943-f55c92a88c0d)
