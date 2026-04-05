FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if required (e.g. for building some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn python-multipart

# Download NLP Models for BAM Engine
RUN python -m spacy download en_core_web_sm
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

# Copy the entire project to ensure backend.main can import src.
COPY . .

# Expose the Railway dynamically assigned port, default to 8000
EXPOSE $PORT

# Start the FastAPI server using Uvicorn
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
