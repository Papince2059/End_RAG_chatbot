# Endee RAG Chatbot - Homeopathy Assistant

A high-performance Retrieval-Augmented Generation (RAG) system dedicated to homeopathy, built using the Endee Vector Database, FastAPI, and a modern frontend.

## 🚀 Project Overview

This project provides a semantic search interface for finding homeopathic remedies based on symptoms. It leverages:
- **Endee Vector Database**: For efficient storage and retrieval of vector embeddings.
- **Sentence Transformers**: For generating high-quality text embeddings (`all-MiniLM-L6-v2`).
- **FastAPI Backend**: A robust API handling search logic and database communication.
- **Dockerized Architecture**: Fully containerized for easy deployment.

## 📂 Project Structure & File Roles

Here is a breakdown of the key components and files in the repository:

### 1. Root Directory
- **`docker-compose.yml`**: The orchestration file. It defines three services:
    - `endee`: The vector database server.
    - `backend`: The Python API service.
    - `frontend`: The Nginx-based web interface.
- **`README.md`**: This documentation file.

### 2. Backend (`/backend`)
- **`main.py`**: The core application logic.
    - Initializes the connection to the Endee database.
    - Loads the embedding model.
    - Exposes the `/api/search` endpoint.
    - *Crucial Update*: Manually configures the Endee SDK to connect via `http://endee:8080/api/v1` for Docker compatibility.
- **`Dockerfile`**: Defines the environment for the Python backend (Python 3.10, dependencies).
- **`requirements.txt`**: Lists Python dependencies (`fastapi`, `uvicorn`, `endee`, `sentence-transformers`).

### 3. Frontend (`/frontend`)
- **`index.html`**: The main user interface. A clean, responsive search page.
- **`app.js`**: Client-side logic that captures user input, calls the backend API, and renders results.
- **`Dockerfile`**: Uses Nginx to serve the static files on port 80 (mapped to 3000).

### 4. Data & Scripts (`/data`, `/scripts`)
- **`data/symptom_remedy_examples.txt`**: The source dataset containing symptoms and their corresponding remedies.
- **`scripts/chunk_remedies.py`**: A utility script to parse the raw text data into structured chunks suitable for embedding.
- **`scripts/ingest_remedies_to_endee.py`**: The ingestion script that:
    1. Reads the chunked data.
    2. Generates embeddings using the local model.
    3. Uploads vectors to the Endee database.

## 🔄 Project Sequence: How It Works

1.  **Data Ingestion (Pre-computation)**:
    - Raw text is processed by script.
    - Embeddings are generated and stored in the persistent volume `rag-chatbot_endee_data`.
    *(Note: This is already done for you!)*

2.  **Service Startup**:
    - `docker compose up` starts all three containers.
    - **Endee** starts and loads the `homeopathy_remedies` index.
    - **Backend** waits for Endee, then initializes the SDK and connection.
    - **Frontend** serves the UI.

3.  **Search Flow**:
    - User types a symptom (e.g., "headache") in the UI.
    - Frontend sends a POST request to `localhost:8000/api/search`.
    - Backend converts "headache" into a vector embedding.
    - Backend queries Endee for the nearest semantic matches.
    - Endee returns the top matching remedies.
    - Backend formats the response and sends it back to the UI.
    - UI displays the remedies, similarity scores, and details.

## 🛠️ How to Run

### Prerequisites
- Docker & Docker Compose installed.

### Steps
1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Papince2059/End_RAG_chatbot.git
    cd End_RAG_chatbot
    ```

2.  **Start the Application**
    ```bash
    docker compose up -d
    ```
    *Wait a few moments for the "Backend initialized successfully" log.*

3.  **Access the App**
    - Open your browser to: **[http://localhost:3000](http://localhost:3000)**

4.  **Stop the Application**
    ```bash
    docker compose down
    ```

## 🐛 Troubleshooting & Debugging History
- **Endee Connection**: The backend was modified to explicitly set `endee_client.base_url = "http://endee:8080/api/v1"` to resolve connectivity issues within the Docker network.
- **Port Mapping**: Frontend is mapped to `3000`, Backend to `8000`, Endee to `8080`.

---
*Built with ❤️ for Homeopathy & AI.*
