FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN find /app/lp_solve_5.5 -type f -name "lp_solve" -exec chmod +x {} \; || true

EXPOSE 8000

CMD ["sh", "-c", "shiny run --host 0.0.0.0 --port ${PORT:-8000} shiny_files/app.py"]