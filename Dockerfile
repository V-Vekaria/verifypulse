# VerifyPulse — Docker Container
# Build: docker build -t verifypulse .
# Run:   docker run -p 8000:8000 verifypulse

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy frontend (served separately or via FastAPI static files)
COPY frontend/ ./frontend/

# Expose port
EXPOSE 8000

# Run
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
