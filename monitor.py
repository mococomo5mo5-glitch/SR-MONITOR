from playwright.sync_api import sync_playwright
import json
import re
import os
import requests

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(
        viewport={"width": 390, "height": 844}
    )

    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    # 大人2名の「＋」ボタンを探す
    adult_plus = page.get_by_label(
        "¥7,000 の サンジの海賊レストラン（2名以上） を1枚追加する"
    ).first

    # ボタンがDOM上に現れるまで最大60秒待つ
    adult_plus.wait_for(
        state="attached",
        timeout=60000
    )

    # 表示状態になるまで少し待つ
    page.wait_for_timeout(5000)

    # 画面内にスクロール
    adult_plus.scroll_into_view_if_needed()

    # 大人2名にする
    adult_plus.click(force=True)

    page.wait_for_timeout(500)

    adult_plus.click(force=True)

    # 大人2名にする
    adult_plus.click()
    page.wait_for_timeout(500)

    adult_plus.click()

    # カレンダー更新待ち
    page.wait_for_timeout(3000)

    # 最後までスクロール
    # 11月まで読み込ませる
    last_height = 0

    for _ in range(20):
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(1200)

        height = page.evaluate(
            "document.body.scrollHeight"
        )

        if height == last_height:
            break

        last_height = height

    # カレンダー取得
    calendar = []

    buttons = page.locator("button")
    count = buttons.count()

    for i in range(count):
        try:
            btn = buttons.nth(i)

            aria = btn.get_attribute("aria-label")

            if not aria:
                continue

            if "2026年" not in aria:
                continue

            # 例：
            # 2026年9月30日水曜日 - 7000
            #
            # または
            # 2026年9月30日水曜日 -
            if " - " in aria:
                date, price = aria.split(
                    " - ",
                    1
                )
            else:
                date = aria
                price = ""

            text = btn.text_content()

            calendar.append({
                "date": date.strip(),
                "price": price.strip(),
                "text": text.strip() if text else ""
            })

        except Exception:
            pass

    print("========== CALENDAR ==========")

    for item in calendar:
        print(item)

    # calendar.json保存
    with open(
        "calendar.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            calendar,
            f,
            ensure_ascii=False,
            indent=2
        )

    # Discord Webhook
    webhook = os.getenv("DISCORD_WEBHOOK")

    if webhook:
        print("DISCORD_WEBHOOK: 設定されています")

        hits = []

        for item in calendar:
            price = item.get(
                "price",
                ""
            )

            # 7000円の販売情報を検出
            if "7000" in price or "¥7,000" in price:
                hits.append(
                    f"{item['date']} : {price}"
                )

        if hits:
            message = (
                "🎉 サンジの海賊レストランに"
                "販売情報がありました！\n\n"
                + "\n".join(hits)
            )

            try:
                response = requests.post(
                    webhook,
                    json={
                        "content": message
                    },
                    timeout=20
                )

                print(
                    "Discord response:",
                    response.status_code
                )

                if response.status_code == 204:
                    print(
                        "Discord通知に成功しました"
                    )
                else:
                    print(
                        "Discord通知に失敗しました"
                    )

            except Exception as e:
                print(
                    "Discord notification error:",
                    e
                )

        else:
            print(
                "販売情報なし"
            )

    else:
        print(
            "DISCORD_WEBHOOK が設定されていません"
        )

    # スクリーンショット
    page.screenshot(
        path="page.png",
        full_page=True
    )

    browser.close()
