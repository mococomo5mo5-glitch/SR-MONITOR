from playwright.sync_api import sync_playwright

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(
        viewport={"width": 390, "height": 844}
    )

    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(3000)

    print("===== BUTTON LIST =====")

    buttons = page.locator("button")
    count = buttons.count()

    print(f"ボタン数: {count}")

    for i in range(count):
        try:
            b = buttons.nth(i)
            print("--------------------")
            print(f"No.{i}")

            text = b.inner_text(timeout=1000)
            print("text:", text)

            aria = b.get_attribute("aria-label")
            print("aria:", aria)

        except Exception:
            pass

    page.screenshot(path="page.png", full_page=True)

    with open("page.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    print("Finished.")

    browser.close()
