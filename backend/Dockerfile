FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/data/hf

# Set to "false" if you use EMBEDDING_PROVIDER=ollama|openai and want a much smaller image.
ARG INSTALL_LOCAL_EMBEDDINGS=true
ARG APP_UID=1000
# Package sources (set these in .env when PyPI is unreachable, e.g. a company Nexus/Artifactory mirror)
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
ENV PIP_INDEX_URL=${PIP_INDEX_URL} PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=10

WORKDIR /app

COPY requirements.txt requirements-embeddings.txt ./
RUN pip install -r requirements.txt \
    && if [ "$INSTALL_LOCAL_EMBEDDINGS" = "true" ]; then \
         pip install torch --index-url https://download.pytorch.org/whl/cpu \
         && pip install -r requirements-embeddings.txt; \
       fi

RUN useradd --uid ${APP_UID} --create-home app \
    && mkdir -p /data/hf /data/docs \
    && chown -R app:app /data

COPY --chown=app:app . .
RUN chmod +x /app/entrypoint.sh

USER app
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
