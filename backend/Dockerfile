FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt /app/requirements.txt
COPY requirements-image.txt /app/requirements-image.txt
RUN pip install --no-cache-dir -r /app/requirements.txt -r /app/requirements-image.txt

COPY . /app
RUN useradd --create-home copycat && mkdir -p /app/data && chown -R copycat:copycat /app
USER copycat

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
