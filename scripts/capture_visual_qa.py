"""Capture evidence-section QA screenshots through Chrome DevTools Protocol.

This uses only the Python standard library so the visual QA remains available
without adding a browser-automation dependency to the project.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import socket
import struct
import time
import urllib.request


class DevToolsSocket:
    def __init__(self, websocket_url: str) -> None:
        rest = websocket_url.removeprefix("ws://")
        host_port, path = rest.split("/", 1)
        host, port = host_port.split(":")
        self.socket = socket.create_connection((host, int(port)), timeout=20)
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.socket.sendall(request.encode())
        headers = b""
        while b"\r\n\r\n" not in headers:
            headers += self.socket.recv(4096)
        if b" 101 " not in headers.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"WebSocket upgrade failed: {headers[:300]!r}")
        self.identifier = 0

    def _read_exact(self, size: int) -> bytes:
        data = b""
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                raise EOFError("Chrome closed the DevTools socket")
            data += chunk
        return data

    def _send_text(self, value: str) -> None:
        payload = value.encode()
        mask = os.urandom(4)
        header = bytearray([0x81])
        if len(payload) < 126:
            header.append(0x80 | len(payload))
        elif len(payload) < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", len(payload)))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", len(payload)))
        header.extend(mask)
        header.extend(bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload)))
        self.socket.sendall(header)

    def _receive_text(self) -> str:
        while True:
            first, second = self._read_exact(2)
            opcode = first & 0x0F
            size = second & 0x7F
            if size == 126:
                size = struct.unpack("!H", self._read_exact(2))[0]
            elif size == 127:
                size = struct.unpack("!Q", self._read_exact(8))[0]
            mask = self._read_exact(4) if second & 0x80 else None
            payload = self._read_exact(size)
            if mask:
                payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
            if opcode == 9:
                continue
            if opcode in (1, 2):
                return payload.decode()

    def command(self, method: str, params: dict | None = None, timeout: float = 30) -> dict:
        self.identifier += 1
        identifier = self.identifier
        self._send_text(json.dumps({"id": identifier, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = json.loads(self._receive_text())
            if message.get("id") == identifier:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})
        raise TimeoutError(method)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug-port", type=int, default=9222)
    parser.add_argument("--url", default="http://127.0.0.1:4321/stereopatch/")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1800)
    parser.add_argument("--height", type=int, default=1100)
    arguments = parser.parse_args()

    targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{arguments.debug_port}/json"))
    page = next(target for target in targets if target["type"] == "page")
    client = DevToolsSocket(page["webSocketDebuggerUrl"])
    client.command("Page.enable")
    client.command("Runtime.enable")
    client.command(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": arguments.width,
            "height": arguments.height,
            "deviceScaleFactor": 1,
            "mobile": False,
        },
    )
    client.command("Page.navigate", {"url": arguments.url})
    time.sleep(3)

    arguments.output.mkdir(parents=True, exist_ok=True)
    sections = (
        "method",
        "tasks",
        "compatibility",
        "position-learning",
        "metric-ambiguity",
        "resolution",
        "latency",
    )
    for section in sections:
        expression = f"""
          (async () => {{
            document.documentElement.classList.remove('motion-ready');
            document.querySelectorAll('[data-reveal]').forEach((node) => node.classList.add('is-revealed'));
            document.querySelectorAll('video').forEach((video) => video.pause());
            const target = document.getElementById({json.dumps(section)});
            if (!target) return 'missing';
            target.scrollIntoView({{ block: 'start', behavior: 'auto' }});
            await new Promise((resolve) => setTimeout(resolve, 1300));
            return [window.scrollY, target.getBoundingClientRect().top, target.offsetHeight];
          }})()
        """
        result = client.command(
            "Runtime.evaluate",
            {"expression": expression, "awaitPromise": True, "returnByValue": True},
        )
        screenshot = client.command(
            "Page.captureScreenshot",
            {"format": "png", "fromSurface": True, "captureBeyondViewport": False},
        )
        output = arguments.output / f"{section}.png"
        output.write_bytes(base64.b64decode(screenshot["data"]))
        value = result.get("result", {}).get("value")
        print(f"{section}: {value} -> {output}")


if __name__ == "__main__":
    main()
