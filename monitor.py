from playwright.sync_api import sync_playwright
import json
import re

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(
        viewport={"width":390,"height":844}
    )

    page.goto(URL, wait_until="networkidle")

    # ページの読み込み待ち
    page.wait_for_timeout(3000)

    # 「＋」ボタンが表示されるまで待つ（最大60秒）
    page.wait_for_selector(
        '[aria-label*="1枚追加する"]',
        timeout=60000
    )

    # 大人2名にする
    adult_plus = page.get_by_label(
        "¥7,000 の サンジの海賊レストラン（2名以上） を1枚追加する"
    )

    adult_plus.click()
    page.wait_for_timeout(500)
    adult_plus.click()

    # カレンダーが更新されるまで待つ
    page.wait_for_timeout(3000)

    # 最後までスクロール（10月・11月読み込み用）
    last_height = 0

    for _ in range(20):
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(1200)

        height = page.evaluate("document.body.scrollHeight")

        if height == last_height:
            break

        last_height = height

    # カレンダー取得
    calendar = []

    buttons = page.locator("button")
    count = buttons.count()

    for i in range(count):
        try:
            aria = buttons.nth(i).get_attribute("aria-label")

            if aria is None:
                continue

            if "2026年" not in aria:
                continue

            m = re.match(r"(.*?)\s*-\s*(.*)", aria)

            if m:
                date = m.group(1).strip()
                price = m.group(2).strip()
            else:
                date = aria.strip()
                price = ""

            calendar.append({
                "date": date,
                "price": price
            })

        except:
            pass

    print("========== CALENDAR ==========")

    for c in calendar:
        print(c)

    with open("calendar.json", "w", encoding="utf-8") as f:
        json.dump(calendar, f, ensure_ascii=False, indent=2)

    page.screenshot(path="page.png", full_page=True)

    browser.close()
