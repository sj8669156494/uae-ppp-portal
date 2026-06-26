FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY scripts/ ./scripts/

ENV APP_ENV=production
ENV DATABASE_URL=sqlite+aiosqlite:///./uae_ppp.db
ENV LOG_LEVEL=INFO
ENV SCRAPER_DELAY_SECONDS=2
ENV SCRAPER_TIMEOUT_SECONDS=30
ENV MAX_RETRIES=3

EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
