from playwright.sync_api import sync_playwright
import json

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
    """
    「1 selected 1」「2 selected 2」のように
    現在の選択人数が表示されているか確認する。
    """

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
    # 2. 大人7,000円の＋ボタンを取得
    # ==================================================

    print(
        "大人7,000円の＋ボタンを探しています..."
    )

    adult_plus = find_adult_plus(page)

    # ==================================================
    # 3. クリック前
    # ==================================================

    before_text = get_adult_area_text(
        page,
        adult_plus
    )

    print(
        "大人選択部分:",
        before_text
    )

    print(
        "クリック前の大人人数表示を確認します..."
    )

    if "0 selected 0" in before_text:
        print(
            "クリック前の大人人数: 0"
        )
    elif "1 selected 1" in before_text:
        print(
            "クリック前の大人人数: 1"
        )
    elif "2 selected 2" in before_text:
        print(
            "クリック前の大人人数: 2"
        )
    else:
        print(
            "クリック前の大人人数を判定できませんでした。"
        )

    # ==================================================
    # 4. 大人1名
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
    # 5. 大人2名
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
    # 6. カレンダー更新待ち
    # ==================================================

    page.wait_for_timeout(3000)

    print(
        "カレンダーを読み込んでいます..."
    )

    # ==================================================
    # 7. 最後までスクロール
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
    # 8. カレンダー取得
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

            calendar.append(
                {
                    "date": date.strip(),
                    "price": price.strip(),
                    "text": (
                        text.strip()
                        if text
                        else ""
                    )
                }
            )

        except Exception:
            pass

    # ==================================================
    # 9. カレンダー表示
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
    # 10. calendar.json
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
    # 11. 7000円の日を詳細調査
    # ==================================================

    print("")
    print(
        "=========================================="
    )
    print(
        "7000円の日の詳細調査"
    )
    print(
        "=========================================="
    )

    detailed_calendar = []

    buttons = page.locator("button")

    count = buttons.count()

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

            if (
                "7000" not in aria
                and "¥7,000" not in aria
            ):
                continue

            if " - " in aria:

                date, price = aria.split(
                    " - ",
                    1
                )

            else:

                date = aria
                price = ""

            # disabled
            try:
                disabled = button.is_disabled()
            except Exception:
                disabled = None

            # aria-disabled
            aria_disabled = button.get_attribute(
                "aria-disabled"
            )

            # class
            class_name = button.get_attribute(
                "class"
            )

            # id
            button_id = button.get_attribute(
                "id"
            )

            # text
            text_content = button.text_content()

            if text_content:
                text_content = text_content.strip()
            else:
                text_content = ""

            # HTML
            outer_html = button.evaluate(
                "(el) => el.outerHTML"
            )

            detail = {
                "date": date.strip(),
                "price": price.strip(),
                "text": text_content,
                "disabled": disabled,
                "aria_disabled": aria_disabled,
                "class": class_name,
                "id": button_id,
                "outer_html": outer_html
            }

            detailed_calendar.append(
                detail
            )

            print("")
            print(
                "========== 7000円詳細 =========="
            )

            print(
                "date:",
                detail["date"]
            )

            print(
                "price:",
                detail["price"]
            )

            print(
                "text:",
                detail["text"]
            )

            print(
                "disabled:",
                detail["disabled"]
            )

            print(
                "aria-disabled:",
                detail["aria_disabled"]
            )

            print(
                "class:",
                detail["class"]
            )

            print(
                "id:",
                detail["id"]
            )

            print(
                "HTML:"
            )

            print(
                detail["outer_html"]
            )

            print(
                "================================"
            )

        except Exception as e:

            print(
                "7000円詳細取得エラー:",
                e
            )

    # ==================================================
    # 12. 詳細JSON
    # ==================================================

    with open(
        "calendar_detail.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            detailed_calendar,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        "calendar_detail.json を保存しました"
    )

    # ==================================================
    # 13. Discord通知は今回しない
    # ==================================================

    print("")
    print(
        "=========================================="
    )

    print(
        "今回は調査用のため、Discord通知は行いません。"
    )

    print(
        "=========================================="
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
