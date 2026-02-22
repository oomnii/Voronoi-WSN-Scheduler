FROM python:3.11-slim
WORKDIR /app
COPY web/backend/requirements_web.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn web.backend.main:app --host 0.0.0.0 --port ${PORT}"]
