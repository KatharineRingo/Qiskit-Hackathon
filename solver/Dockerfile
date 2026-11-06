# Build from the repo root:  docker build -f solver/Dockerfile -t undertow-solver .
FROM python:3.12-slim

WORKDIR /app
COPY solver/requirements.txt solver/requirements.txt
RUN pip install --no-cache-dir -r solver/requirements.txt

COPY src ./src
COPY solver ./solver
COPY data ./data
COPY results/sampling_results.csv ./results/sampling_results.csv

ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn solver.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
