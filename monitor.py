from playwright.sync_api import sync_playwright

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    page.goto(URL)

    page.wait_for_timeout(5000)

    with open("page.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    print("HTML saved.")

    browser.close()
