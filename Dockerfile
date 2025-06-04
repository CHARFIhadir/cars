FROM python:3.10-slim

WORKDIR /app

COPY users_service.py .

RUN pip install fastapi uvicorn psycopg2-binary redis httpx

CMD ["uvicorn", "users_service:app", "--host", "0.0.0.0", "--port", "8000"]
