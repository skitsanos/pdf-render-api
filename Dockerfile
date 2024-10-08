FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y libgirepository1.0-dev libglib2.0-dev libpango1.0-dev

COPY requirements.txt /app
COPY server.py /app
COPY routes /app/routes
COPY templates /app/templates

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV NAME AUTH_TOKEN

CMD ["python", "server.py"]