"""Takes the app screenshots of the guide (shiny_files/www/guide/<lang>/app.png and sensitivity.png).

Needs a running app and Playwright (not part of the app's requirements):
    cd shiny_files && shiny run app.py --port 8000
    pip install playwright   # uses the installed Google Chrome, no browser download needed
    python tools/guide_screenshots.py http://localhost:8000
"""

import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shiny_files", "www", "guide")
LANGS = ("en", "de", "fil")


def shoot(browser, url, lang):
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    page.add_init_script(f"localStorage.setItem('optisense-lang', '{lang}')")
    page.goto(url)
    page.wait_for_selector("#btn_example", state="visible")
    page.wait_for_timeout(1500)
    page.click("#btn_example")
    page.wait_for_selector("#btn_opt:not([disabled])")
    page.click("#btn_opt")
    page.wait_for_selector("#btn_opt.is-active")
    page.wait_for_timeout(2500)   # graph redraw
    os.makedirs(os.path.join(OUT, lang), exist_ok=True)
    page.add_style_tag(content="#shiny-notification-panel { display: none !important; }")
    page.mouse.move(0, 0)
    page.screenshot(path=os.path.join(OUT, lang, "app.png"))

    page.click("#btn_sens")
    page.wait_for_selector("#btn_sens.is-active")
    last = page.locator(".os-results .tab-pane.active .os-table").last
    last.wait_for(state="visible")
    page.wait_for_timeout(500)
    card = page.locator(".os-results > .card").bounding_box()
    bottom = page.evaluate("""() => Math.max(...[...document.querySelectorAll('.os-results .tab-pane.active *')]
        .map(e => e.getBoundingClientRect()).filter(r => r.height > 0).map(r => r.bottom))""")
    height = bottom - card["y"] + 24
    page.screenshot(path=os.path.join(OUT, lang, "sensitivity.png"),
                    clip={"x": card["x"], "y": card["y"], "width": card["width"], "height": min(height, card["height"])})
    page.close()


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for lang in LANGS:
            shoot(browser, url, lang)
        browser.close()
    print("written to", OUT)


if __name__ == "__main__":
    main()
