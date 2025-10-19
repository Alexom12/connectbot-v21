FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y build-essential gcc libpq-dev --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# copy requirements first for caching
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy project
COPY . /app

EXPOSE 8000

# default command is handled by docker-compose to run migrations and server

# Ensure container runs the Django development server when deployed as an image
# so the service does not immediately exit after running one-off commands.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
