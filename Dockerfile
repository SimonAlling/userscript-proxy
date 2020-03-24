FROM python:3.7-slim AS base

FROM base AS builder

COPY requirements.txt .
# We're not going to run anything in the build container, so we'll suppress the script location warnings.
RUN pip install --user --no-warn-script-location -r requirements.txt


FROM base

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY src src
COPY rules rules
COPY userscripts /usr/share/userscripts

EXPOSE 8080
ENTRYPOINT [ "python", "-u", "src/launcher.py" ]
