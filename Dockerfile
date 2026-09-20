# =============================================================
#  OptiSense - Dockerfile
#
#  Wichtigste Aenderung gegenueber der bisherigen Version:
#  lp_solve wird NICHT mehr als mitgelieferte Binary benutzt,
#  sondern im Build aus den Quellen kompiliert. Die im Repo
#  liegende Linux-Binary ist ARM (aarch64) und laeuft auf einem
#  x86-Server nicht ("Exec format error").
# =============================================================

# ---------- Stage 1: lp_solve fuer die Zielarchitektur bauen ----------
FROM python:3.11-slim-bookworm AS lpsolve-builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY lp_solve_5.5/ ./lp_solve_5.5/

# Das ccc-Skript legt das Ergebnis in bin/ux64/ (64 Bit) ab.
RUN cd lp_solve_5.5/lp_solve \
 && sh ccc \
 && cp bin/ux*/lp_solve /usr/local/bin/lp_solve \
 && chmod +x /usr/local/bin/lp_solve

# Smoke-Test: bricht den Build ab, falls die Binary nicht laeuft.
RUN printf 'max: 3x + 2y;\nR1: x + y <= 4;\nR2: x + 3y <= 6;\n' > /tmp/smoke.lp \
 && /usr/local/bin/lp_solve -S5 /tmp/smoke.lp | grep -q "Value of objective function" \
 && rm /tmp/smoke.lp


# ---------- Stage 2: App-Image ----------
FROM python:3.11-slim-bookworm

WORKDIR /app

COPY --from=lpsolve-builder /usr/local/bin/lp_solve /usr/local/bin/lp_solve

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LP_SOLVE_BIN=/usr/local/bin/lp_solve \
    MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1

# App laeuft nicht als root - sinnvoll, weil die Seite oeffentlich erreichbar ist.
RUN useradd --create-home --uid 10001 appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "shiny run --host 0.0.0.0 --port ${PORT:-8000} shiny_files/app.py"]
