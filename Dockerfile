FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user backend/ ./backend/
COPY --chown=user scripts/ ./scripts/

ENV APP_ENV=production
ENV DATABASE_URL=sqlite+aiosqlite:///./uae_ppp.db
ENV LOG_LEVEL=INFO
ENV SCRAPER_DELAY_SECONDS=2
ENV SCRAPER_TIMEOUT_SECONDS=30
ENV MAX_RETRIES=3
ENV FRONTEND_URL=https://uae-ppp-portal.vercel.app

EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
