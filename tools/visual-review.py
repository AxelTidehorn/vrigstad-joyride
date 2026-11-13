#!/usr/bin/env python3
"""Capture a reproducible, playable-map WebGL smoke test for visual PRs.

This is a CI-only review aid. It does not change the game, camera code or
runtime dependencies. Both branches load the same real Vrigstad map.
"""
from pathlib import Path
import json
import subprocess
import time

from playwright.sync_api import sync_playwright

OUT = Path("visual-review")
OUT.mkdir(exist_ok=True)
PORT = 8765
SERVER = f"http://127.0.0.1:{PORT}"
FRAMES = 36


def capture(browser, name, query=""):
    errors = []
    page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    # A fixed frame cap ensures exact camera/NPC timing across slow/fast
    # SwiftShader runs; the game is untouched outside this screenshot process.
    page.add_init_script(
        """(() => {
          const raf = window.requestAnimationFrame.bind(window);
          let n = 0, limit = 36, pending = null;
          window.__visualFrame = 0;
          window.__visualPaused = false;
          window.requestAnimationFrame = callback => raf(() => {
            if (n >= limit) {
              pending = callback;
              window.__visualPaused = true;
              return;
            }
            n += 1;
            window.__visualFrame = n;
            callback(n * 16.6667);
          });
          window.__advanceVisualFrames = extra => {
            limit += extra;
            window.__visualPaused = false;
            if (pending) {
              const callback = pending;
              pending = null;
              window.requestAnimationFrame(callback);
            }
          };
        })();"""
    )
    start = time.monotonic()
    page.goto(f"{SERVER}/{name}/index.html{query}", wait_until="domcontentloaded", timeout=70000)
    page.locator("#go").click(timeout=80000)
    page.wait_for_function("window.__visualPaused === true", polling=100, timeout=180000)
    fail = page.locator("#fail").is_visible()
    # Freeze only after the frame finishes: capture byte-identical camera states.
    stem = name + ("-mist-off" if query else "")
    page.screenshot(path=str(OUT / f"{stem}-torget.png"), animations="disabled")
    page.mouse.move(800, 375)
    page.mouse.down()
    page.mouse.move(470, 345, steps=10)
    page.mouse.up()
    page.evaluate("window.__advanceVisualFrames(18)")
    page.wait_for_function("window.__visualPaused === true", polling=100, timeout=90000)
    page.screenshot(path=str(OUT / f"{stem}-torget-side.png"), animations="disabled")
    result = {"branch": name, "webgl_error": fail, "console_errors": errors[:30],
              "elapsed_s": round(time.monotonic() - start, 2),
              "frames": page.evaluate("window.__visualFrame")}
    page.close()
    return result


def main():
    server = subprocess.Popen(["python3", "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(2)
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader",
                      "--enable-unsafe-swiftshader", "--disable-features=Vulkan"],
            )
            try:
                results = [capture(browser, "before"),
                           capture(browser, "after"),
                           capture(browser, "after", "?mist=off&grain=strong")]
            finally:
                browser.close()
        (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        fatal = ("WebGLProgram", "INVALID_OPERATION", "ReferenceError", "TypeError", "SyntaxError")
        if any(r["webgl_error"] or any(word in err for err in r["console_errors"] for word in fatal) for r in results):
            raise RuntimeError("WebGL or JS errors; inspect visual-review/results.json")
    finally:
        server.terminate()
        server.wait(timeout=15)


if __name__ == "__main__":
    main()
