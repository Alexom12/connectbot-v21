FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y build-essential gcc libpq-dev dos2unix --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# copy requirements first for caching
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy project
COPY . /app/

# no entrypoint for now
# copy entrypoint
# COPY ./docker/web-entrypoint.sh /app/web-entrypoint.sh
# RUN dos2unix /app/web-entrypoint.sh && chmod +x /app/web-entrypoint.sh

# ENTRYPOINT ["/app/web-entrypoint.sh"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
