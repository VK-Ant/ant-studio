FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ /app/backend/
COPY templates/ /app/templates/
COPY run_workflow.py /app/
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
