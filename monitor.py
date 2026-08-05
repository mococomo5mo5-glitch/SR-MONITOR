from playwright.sync_api import sync_playwright

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(
        viewport={"width":390,"height":844}
    )

    page.goto(URL, wait_until="networkidle")

    page.wait_for_timeout(3000)

    # 大人の＋を2回
    page.locator("button").filter(has=page.locator("svg")).nth(1).click()
    page.wait_for_timeout(500)
    page.locator("button").filter(has=page.locator("svg")).nth(1).click()

    page.wait_for_timeout(1000)

    page.screenshot(path="page.png", full_page=True)

    browser.close()
