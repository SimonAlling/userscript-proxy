FROM python:3.9.23-slim AS base

FROM base AS builder

WORKDIR /builddir

COPY requirements.txt .
# We're not going to run anything in the build container, so we'll suppress the script location warnings.
RUN pip install --user --no-warn-script-location -r requirements.txt
ENV PATH=/root/.local/bin:$PATH
COPY typecheck .
COPY src src
RUN ./typecheck

FROM base

WORKDIR /app

COPY --from=builder /root/.local/lib /root/.local/lib
COPY --from=builder /root/.local/bin/mitmdump /root/.local/bin/mitmdump
COPY --from=builder /builddir/src src
ENV PATH=/root/.local/bin:$PATH
COPY default-rules default-rules
COPY default-userscripts default-userscripts

EXPOSE 8080
ENTRYPOINT [ "python", "-u", "src/restartable_launcher.py" ]
