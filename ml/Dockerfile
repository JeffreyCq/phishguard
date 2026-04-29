FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    fastapi uvicorn[standard] huggingface_hub

COPY src/          ./src/
COPY api/          ./api/
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

# Model files live in a named volume — downloaded on first start
VOLUME ["/app/model"]

EXPOSE 8001

ENTRYPOINT ["./entrypoint.sh"]
