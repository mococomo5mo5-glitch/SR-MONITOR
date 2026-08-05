from playwright.sync_api import sync_playwright

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(
        viewport={"width": 390, "height": 844}
    )

    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(3000)

    # 大人を2名にする
    adult_plus = page.get_by_label(
        "¥7,000 の サンジの海賊レストラン（2名以上） を1枚追加する"
    )

    adult_plus.click()
    page.wait_for_timeout(500)
    adult_plus.click()

    page.wait_for_timeout(1000)

    print("===== NEXT BUTTONS =====")

    buttons = page.locator("button")
    count = buttons.count()

    for i in range(count):
        try:
            b = buttons.nth(i)

            text = b.inner_text(timeout=500).strip()
            aria = b.get_attribute("aria-label")

            if text or aria:
                print("--------------------")
                print(f"No.{i}")
                print("text:", text)
                print("aria:", aria)

        except Exception:
            pass

    page.screenshot(path="page.png", full_page=True)

    with open("page.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    print("Finished.")

    browser.close()
