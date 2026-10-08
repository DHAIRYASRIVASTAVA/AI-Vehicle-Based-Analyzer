FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=7860
# HF Spaces runs as uid 1000; same user works everywhere
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=user . .
USER user
ENV HOME=/home/user FASTEMBED_CACHE_PATH=/home/user/.cache/fastembed


EXPOSE 7860
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
