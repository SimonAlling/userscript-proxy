FROM python:3.7.10-slim AS base

FROM base AS builder

COPY requirements.txt .
# We're not going to run anything in the build container, so we'll suppress the script location warnings.
RUN pip install --user --no-warn-script-location -r requirements.txt


FROM base

WORKDIR /app

COPY --from=builder /root/.local/lib /root/.local/lib
COPY --from=builder /root/.local/bin/mitmdump /root/.local/bin/mitmdump
ENV PATH=/root/.local/bin:$PATH
COPY src src
COPY default-rules default-rules
COPY default-userscripts default-userscripts

EXPOSE 8080
ENTRYPOINT [ "python", "-u", "src/launcher.py" ]
