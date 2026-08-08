from playwright.sync_api import sync_playwright
import json
import os
import requests

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

ADULT_PLUS_LABEL = (
    "¥7,000 の サンジの海賊レストラン（2名以上） "
    "を1枚追加する"
)


def find_adult_plus(page):
    locator = page.locator(
        f'button[aria-label="{ADULT_PLUS_LABEL}"]'
    )

    count = locator.count()

    print(
        "大人＋ボタン候補数:",
        count
    )

    if count == 0:
        raise RuntimeError(
            "大人7,000円の＋ボタンが見つかりませんでした。"
        )

    for i in range(count):

        try:

            button = locator.nth(i)

            print(
                "大人＋ボタンを使用:",
                i + 1,
                "/",
                count
            )

            button.scroll_into_view_if_needed()

            page.wait_for_timeout(500)

            return button

        except Exception as e:

            print(
                "ボタン取得エラー:",
                e
            )

    raise RuntimeError(
        "大人7,000円の＋ボタンを取得できませんでした。"
    )


def get_adult_area_text(page, adult_plus):

    try:

        text = adult_plus.evaluate(
            """
            (el) => {
                let node = el;

                for (let i = 0; i < 8 && node; i++) {
                    const text = (node.innerText || "")
                        .replace(/\\s+/g, " ")
                        .trim();

                    if (
                        text.includes("大人") &&
                        text.includes("7,000")
                    ) {
                        return text;
                    }

                    node = node.parentElement;
                }

                return "";
            }
            """
        )

        return text

    except Exception as e:

        print(
            "大人選択部分取得エラー:",
            e
        )

        return ""


def check_selected(text, number):

    target = f"{number} selected {number}"

    return target in text


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page(
        viewport={
            "width": 390,
            "height": 844
        }
    )

    # ==================================================
    # 1. USJページを開く
    # ==================================================

    print(
        "USJページを開いています..."
    )

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(5000)

    print(
        "USJページ読み込み完了"
    )

    # ==================================================
    # 2. 大人7,000円の＋ボタンを探す
    # ==================================================

    print(
        "大人7,000円の＋ボタンを探しています..."
    )

    adult_plus = find_adult_plus(page)

    # ==================================================
    # 3. 現在の人数を確認
    # ==================================================

    before_text = get_adult_area_text(
        page,
        adult_plus
    )

    print(
        "大人選択部分:",
        before_text
    )

    # ==================================================
    # 4. すでに2名ならそのまま進む
    # ==================================================

    if "2 selected 2" in before_text:

        print(
            "すでに大人2名になっています。"
        )

    else:

        # ==================================================
        # 5. 1回目のクリック
        # ==================================================

        print(
            "大人＋ボタンを1回クリックします..."
        )

        adult_plus.click(
            timeout=30000
        )

        page.wait_for_timeout(1500)

        adult_plus = find_adult_plus(page)

        after_first_text = get_adult_area_text(
            page,
            adult_plus
        )

        print(
            "大人選択部分:",
            after_first_text
        )

        print(
            "1回目クリック後の大人人数表示:",
            after_first_text
        )

        if not check_selected(
            after_first_text,
            1
        ):

            page.screenshot(
                path="error_after_first_click.png",
                full_page=True
            )

            raise RuntimeError(
                "1回目のクリック後に"
                "「1 selected 1」を確認できませんでした。"
                f"現在の表示={after_first_text}"
            )

        print(
            "1回目クリック成功：大人1名を確認しました。"
        )

        # ==================================================
        # 6. 2回目のクリック
        # ==================================================

        print(
            "大人＋ボタンを2回目クリックします..."
        )

        adult_plus.click(
            timeout=30000
        )

        page.wait_for_timeout(2000)

        adult_plus = find_adult_plus(page)

        after_second_text = get_adult_area_text(
            page,
            adult_plus
        )

        print(
            "大人選択部分:",
            after_second_text
        )

        print(
            "2回目クリック後の大人人数表示:",
            after_second_text
        )

        if not check_selected(
            after_second_text,
            2
        ):

            page.screenshot(
                path="error_after_second_click.png",
                full_page=True
            )

            raise RuntimeError(
                "2回目のクリック後に"
                "「2 selected 2」を確認できませんでした。"
                f"現在の表示={after_second_text}"
            )

        print(
            "2回目クリック成功：大人2名を確認しました。"
        )

    # ==================================================
    # 7. カレンダー更新待ち
    # ==================================================

    page.wait_for_timeout(3000)

    print(
        "カレンダーを読み込んでいます..."
    )

    # ==================================================
    # 8. 最後までスクロール
    # ==================================================

    last_height = 0

    for _ in range(25):

        page.mouse.wheel(
            0,
            3000
        )

        page.wait_for_timeout(1200)

        height = page.evaluate(
            "document.body.scrollHeight"
        )

        print(
            "ページ高さ:",
            height
        )

        if height == last_height:
            break

        last_height = height

    # ==================================================
    # 9. カレンダー取得
    # ==================================================

    calendar = []

    buttons = page.locator("button")

    count = buttons.count()

    print(
        "ボタン総数:",
        count
    )

    for i in range(count):

        try:

            button = buttons.nth(i)

            aria = button.get_attribute(
                "aria-label"
            )

            if not aria:
                continue

            if "2026年" not in aria:
                continue

            if " - " in aria:

                date, price = aria.split(
                    " - ",
                    1
                )

            else:

                date = aria
                price = ""

            text = button.text_content()

            if text:
                text = text.strip()
            else:
                text = ""

            # ------------------------------------------
            # 販売可否を確認
            # ------------------------------------------

            try:

                disabled = button.is_disabled()

            except Exception:

                disabled = None

            aria_disabled = button.get_attribute(
                "aria-disabled"
            )

            class_name = button.get_attribute(
                "class"
            )

            button_id = button.get_attribute(
                "id"
            )

            calendar.append(
                {
                    "date": date.strip(),
                    "price": price.strip(),
                    "text": text,
                    "disabled": disabled,
                    "aria_disabled": aria_disabled,
                    "class": class_name,
                    "id": button_id
                }
            )

        except Exception:
            pass

    # ==================================================
    # 10. カレンダー表示
    # ==================================================

    print(
        "========== CALENDAR =========="
    )

    for item in calendar:

        print(
            item
        )

    print(
        "カレンダー件数:",
        len(calendar)
    )

    # ==================================================
    # 11. calendar.json保存
    # ==================================================

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

    print(
        "calendar.json を保存しました"
    )

    # ==================================================
    # 12. 販売可能日の判定
    # ==================================================

    available_dates = []

    print("")
    print(
        "=========================================="
    )
    print(
        "販売可能日を確認しています..."
    )
    print(
        "=========================================="
    )

    for item in calendar:

        price = item.get(
            "price",
            ""
        )

        disabled = item.get(
            "disabled"
        )

        aria_disabled = item.get(
            "aria_disabled"
        )

        # ------------------------------------------
        # 価格判定
        # ------------------------------------------

        price_is_7000 = (
            "7000" in price
            or "¥7,000" in price
        )

        # ------------------------------------------
        # disabled判定
        # ------------------------------------------

        is_enabled = (
            disabled is False
        )

        # ------------------------------------------
        # aria-disabled判定
        # ------------------------------------------

        aria_is_enabled = (
            aria_disabled != "true"
        )

        # ------------------------------------------
        # 最終判定
        # ------------------------------------------

        if (
            price_is_7000
            and is_enabled
            and aria_is_enabled
        ):

            available_dates.append(
                item
            )

            print(
                "★ 販売可能:",
                item
            )

        else:

            # 調査用ログ
            if price_is_7000:

                print(
                    "販売不可:",
                    item["date"],
                    "| price=",
                    price,
                    "| disabled=",
                    disabled,
                    "| aria-disabled=",
                    aria_disabled
                )

    print(
        "販売可能日数:",
        len(available_dates)
    )

    # ==================================================
    # 13. Discord通知
    # ==================================================

    webhook = os.getenv(
        "DISCORD_WEBHOOK"
    )

    if webhook:

        print(
            "DISCORD_WEBHOOK: 設定されています"
        )

        if available_dates:

            lines = []

            for item in available_dates:

                lines.append(
                    f"{item['date']} : "
                    f"{item['price']}"
                )

            message = (
                "🎉 サンジの海賊レストラン"
                "販売開始の可能性があります！\n\n"
                + "\n".join(lines)
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
                "販売可能日はありません。"
            )

            print(
                "Discord通知は行いません。"
            )

    else:

        print(
            "DISCORD_WEBHOOK が"
            "設定されていません。"
        )

    # ==================================================
    # 14. スクリーンショット
    # ==================================================

    page.screenshot(
        path="page.png",
        full_page=True
    )

    print(
        "スクリーンショットを保存しました"
    )

    browser.close()

    print(
        "========== MONITOR COMPLETE =========="
    )
