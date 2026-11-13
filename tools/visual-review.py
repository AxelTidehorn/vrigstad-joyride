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
FRAMES = 12
# Actual road positions derived from the current OSM map. The HTML is patched
# in-memory by the screenshot harness only; the checked-in game is unmodified.
SITES = {
    "torget": None,
    "villa": (28.7, -67.1),       # Gästgivaregatan near catalogue houses
    "historic": (248.4, -278.7), # Parkvägen near eligible red two-storey house
    "garden": (67.7, 346.9),     # Kopparslagarevägen residential environment
}


def capture(browser, name, query="", site="torget"):
    errors = []
    page = browser.new_page(viewport={"width": 960, "height": 540}, device_scale_factor=1)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    if site != "torget":
        x, z = SITES[site]
        def redirect_home(route):
            response = route.fetch()
            body = response.text()
            original = "const HOME = { x: -8.9, z: 30.1 };"
            if body.count(original) != 1:
                raise RuntimeError("Missing default HOME site in real game")
            body = body.replace(original, f"const HOME = {{ x: {x}, z: {z} }};", 1)
            route.fulfill(response=response, body=body)
        page.route("**/index.html*", redirect_home)
    # A fixed frame cap ensures exact camera/NPC timing across slow/fast
    # SwiftShader runs; the game is untouched outside this screenshot process.
    page.add_init_script(
        """(() => {
          const raf = window.requestAnimationFrame.bind(window);
          let n = 0, limit = 12, pending = null;
          window.__visualFrame = 0;
          window.__visualPaused = false;
          window.__visualError = null;
          window.addEventListener('error', e => {
            window.__visualError = e.message || 'Uncaught error';
          });
          window.addEventListener('unhandledrejection', e => {
            window.__visualError = String(e.reason || 'Unhandled promise rejection');
          });
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
    try:
        page.wait_for_function(
            "window.__visualPaused === true || !!window.__visualError",
            polling=200, timeout=95000
        )
    except Exception as exc:
        page.screenshot(path=str(OUT / f"{name}-{site}-timeout.png"), animations="disabled")
        state = page.evaluate("({frames:window.__visualFrame, "
                              "error:window.__visualError, stats:window.__residentialStats || null})")
        raise RuntimeError(f"Timed out rendering {name}/{site}: {state}, "
                           f"JS errors: {errors[:10]}") from exc
    if page.evaluate("window.__visualError"):
        state = page.evaluate("window.__visualError")
        page.screenshot(path=str(OUT / f"{name}-{site}-error.png"), animations="disabled")
        raise RuntimeError(f"Uncaught JS while rendering {name}/{site}: {state}; {errors[:10]}")
    fail = page.locator("#fail").is_visible()
    # Freeze only after the frame finishes: capture byte-identical camera states.
    # Keep each mode's screenshots distinct; no game-specific test UI.
    suffix = "-neighborhood-off" if "neighborhood=off" in query else ""
    stem = name + suffix + "-" + site
    page.screenshot(path=str(OUT / f"{stem}.png"), animations="disabled")
    page.mouse.move(800, 375)
    page.mouse.down()
    page.mouse.move(470, 345, steps=10)
    page.mouse.up()
    page.evaluate("window.__advanceVisualFrames(6)")
    page.wait_for_function("window.__visualPaused === true || !!window.__visualError", polling=200, timeout=45000)
    page.screenshot(path=str(OUT / f"{stem}-side.png"), animations="disabled")
    result = {"branch": name, "site": site, "query": query,
              "webgl_error": fail, "console_errors": errors[:30],
              "elapsed_s": round(time.monotonic() - start, 2),
              "frames": page.evaluate("window.__visualFrame"),
              "neighborhood": page.evaluate("window.__residentialStats || null")}
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
                results = [
                    capture(browser, "before", site="torget"),
                    capture(browser, "after", site="torget"),
                    capture(browser, "before", site="villa"),
                    capture(browser, "after", site="villa"),
                    capture(browser, "after", "?neighborhood=off", site="villa"),
                    capture(browser, "before", site="historic"),
                    capture(browser, "after", site="historic"),
                    capture(browser, "before", site="garden"),
                    capture(browser, "after", site="garden"),
                ]
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
