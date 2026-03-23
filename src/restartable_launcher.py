import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

HOST = os.environ.get("RESTART_CONTROL_HOST", "0.0.0.0")
PORT = int(os.environ.get("RESTART_CONTROL_PORT", "8765"))
RESTART_PATH = os.environ.get("RESTART_CONTROL_PATH", "/internal/restart")
SHUTDOWN_TIMEOUT_SECONDS = float(
    os.environ.get("RESTART_CONTROL_SHUTDOWN_TIMEOUT_SECONDS", "10")
)

LAUNCHER_COMMAND = [sys.executable, "-u", "src/launcher.py", *sys.argv[1:]]


class LauncherSupervisor:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._process: Optional[subprocess.Popen[str]] = None
        self._stopping = False
        self._restart_in_progress = False

    def start_child(self) -> None:
        with self._lock:
            if self._stopping:
                return

            if self._process is not None and self._process.poll() is None:
                return

            print(f"Starting child process: {LAUNCHER_COMMAND}", flush=True)
            self._process = subprocess.Popen(
                LAUNCHER_COMMAND,
                stdout=None,
                stderr=None,
                text=True,
                start_new_session=True,
            )

    def restart_child(self) -> None:
        with self._lock:
            if self._stopping:
                return

            if self._restart_in_progress:
                print(
                    "Restart already in progress; ignoring duplicate request.",
                    flush=True,
                )
                return

            self._restart_in_progress = True

        try:
            self._stop_child()
            self.start_child()
        finally:
            with self._lock:
                self._restart_in_progress = False

    def begin_shutdown(self) -> None:
        with self._lock:
            self._stopping = True

        self._stop_child()

    def is_running(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def wait_forever(self) -> None:
        while True:
            with self._lock:
                if self._stopping:
                    return
                process = self._process

            if process is None:
                time.sleep(0.2)
                continue

            return_code = process.wait()

            with self._lock:
                if self._stopping:
                    print(
                        f"Child exited during shutdown with code {return_code}.",
                        flush=True,
                    )
                    return

                print(
                    f"Child exited unexpectedly with code {return_code}; restarting.",
                    flush=True,
                )
                self._process = None

            time.sleep(1.0)
            self.start_child()

    def _stop_child(self) -> None:
        with self._lock:
            process = self._process

        if process is None:
            return

        if process.poll() is not None:
            with self._lock:
                if self._process is process:
                    self._process = None
            return

        print("", flush=True)
        print("Stopping child process group.", flush=True)
        print("", flush=True)

        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

        try:
            process.wait(timeout=SHUTDOWN_TIMEOUT_SECONDS)
            print("Child process group stopped cleanly.", flush=True)
        except subprocess.TimeoutExpired:
            print("Child did not stop in time; killing process group.", flush=True)
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()

        with self._lock:
            if self._process is process:
                self._process = None


supervisor = LauncherSupervisor()
shutdown_started = False
shutdown_lock = threading.Lock()


class ControlHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != RESTART_PATH:
            self._send_not_found()
            return

        threading.Thread(target=supervisor.restart_child, daemon=True).start()
        self._send_json(202, b'{"ok":true,"message":"Restart requested."}')

    def log_message(self, format: str, *args: object) -> None:
        print(f"[control] {format % args}", flush=True)

    def _send_not_found(self) -> None:
        self._send_json(404, b'{"error":"Not found"}')

    def _send_json(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def install_signal_handlers(server: ThreadingHTTPServer) -> None:
    def handle_shutdown(signum: int, _frame: object) -> None:
        global shutdown_started

        with shutdown_lock:
            if shutdown_started:
                print("Second interrupt received; forcefully exiting.", flush=True)
                os._exit(130)

            shutdown_started = True

        print(f"Received signal {signum}; shutting down.", flush=True)

        def shutdown_worker() -> None:
            try:
                supervisor.begin_shutdown()
            finally:
                server.shutdown()

        threading.Thread(target=shutdown_worker, daemon=True).start()

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)


def main() -> int:
    supervisor.start_child()

    server = ThreadingHTTPServer((HOST, PORT), ControlHandler)
    install_signal_handlers(server)

    print(f"Control server listening on http://{HOST}:{PORT}", flush=True)
    print(f"Restart endpoint: {RESTART_PATH}", flush=True)

    try:
        server.serve_forever()
    finally:
        print("Stopping control server.", flush=True)
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
