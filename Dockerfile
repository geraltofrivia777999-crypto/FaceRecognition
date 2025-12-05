FROM python:3.11-slim

WORKDIR /app

# Install dependencies first to leverage Docker cache
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and static frontend
COPY backend ./backend
COPY frontend ./frontend

# Prepare runtime directories for SQLite and uploads
RUN mkdir -p /app/data/photos /app/data/embeddings

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
