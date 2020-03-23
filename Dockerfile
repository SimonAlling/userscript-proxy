FROM python:3.7-alpine as base

RUN apk add -U --no-cache \
    gcc \
    build-base \
    linux-headers \
    ca-certificates \
    python3-dev \
    libffi-dev \
    openssl-dev \
    libxslt-dev
WORKDIR /app
RUN pip install mitmproxy
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . ./
EXPOSE 8080
ENTRYPOINT [ "python", "-u", "launcher.py" ]
