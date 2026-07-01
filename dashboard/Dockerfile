FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

COPY dashboard ./dashboard

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
