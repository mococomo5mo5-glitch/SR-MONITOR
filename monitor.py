from playwright.sync_api import sync_playwright
import json
import re

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

ADULT_PLUS_LABEL = (
    "¥7,000 の サンジの海賊レストラン（2名以上） "
    "を1枚追加する"
)


def get_adult_quantity(page, adult_plus):
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

        print("大人選択部分:", text)

        numbers = re.findall(
            r"(?<![\\d,])\\d+(?![\\d,])",
            text
        )

        candidates = []

        for number in numbers:
            try:
                value = int(number)

                if 0 <= value <= 9:
                    candidates.append(value)

            except ValueError:
                pass

        if candidates:
            return candidates[-1]

    except Exception as e:
        print("人数取得エラー:", e)

    return None


def find_adult_plus(page):
    """
    前回成功した方法。
    aria-labelが一致するボタンを探し、
    最初に見つかったボタンを使用する。
    """

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
            candidate = locator.nth(i)

            print(
                "大人＋ボタンを使用:",
                i + 1,
                "/",
                count
            )

            candidate.scroll_into_view_if_needed()

            page.wait_for_timeout(500)

            return candidate

        except Exception as e:

            print(
                "ボタン取得エラー:",
                e
            )

    raise RuntimeError(
        "大人7,000円の＋ボタンを取得できませんでした。"
    )


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
    # 2. 大人2名にする
    # ==================================================

    print(
        "大人7,000円の＋ボタンを探しています..."
    )

    adult_plus = find_adult_plus(page)

    quantity_before = get_adult_quantity(
        page,
        adult_plus
    )

    print(
        "クリック前の大人人数:",
        quantity_before
    )

    # ----------------------------------------------
    # すでに2名の場合
    # ----------------------------------------------

    if quantity_before == 2:

        print(
            "すでに大人2名になっています。"
        )

    else:

        # ------------------------------------------
        # 1回目
        # ------------------------------------------

        print(
            "大人＋ボタンを1回クリックします..."
        )

        adult_plus.click(
            timeout=30000
        )

        page.wait_for_timeout(1500)

        # ページ更新でボタンが入れ替わる可能性が
        # あるため、もう一度取得
        adult_plus = find_adult_plus(page)

        quantity_after_first = (
            get_adult_quantity(
                page,
                adult_plus
            )
        )

        print(
            "1回目クリック後の大人人数:",
            quantity_after_first
        )

        if quantity_after_first != 1:

            page.screenshot(
                path="error_after_first_click.png",
                full_page=True
            )

            raise RuntimeError(
                "1回目のクリック後に"
                "大人人数が1になりませんでした。"
                f"現在の人数={quantity_after_first}"
            )

        # ------------------------------------------
        # 2回目
        # ------------------------------------------

        print(
            "大人＋ボタンを2回目クリックします..."
        )

        adult_plus.click(
            timeout=30000
        )

        page.wait_for_timeout(2000)

        adult_plus = find_adult_plus(page)

        quantity_after_second = (
            get_adult_quantity(
                page,
                adult_plus
            )
        )

        print(
            "2回目クリック後の大人人数:",
            quantity_after_second
        )

        if quantity_after_second != 2:

            page.screenshot(
                path="error_after_second_click.png",
                full_page=True
            )

            raise RuntimeError(
                "2回目のクリック後に"
                "大人人数が2になりませんでした。"
                f"現在の人数={quantity_after_second}"
            )

    print(
        "大人2名を確認しました。"
    )

    page.wait_for_timeout(3000)

    # ==================================================
    # 3. カレンダーを最後まで読み込む
    # ==================================================

    print(
        "カレンダーを読み込んでいます..."
    )

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
    # 4. カレンダー取得
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
    # 5. 通常カレンダーを表示
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
    # 6. calendar.json保存
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
    # 7. 7000円の日を詳細調査
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

    # ボタン数をもう一度取得
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

            # ------------------------------------------
            # 日付と価格
            # ------------------------------------------

            if " - " in aria:

                date, price = aria.split(
                    " - ",
                    1
                )

            else:

                date = aria
                price = ""

            # ------------------------------------------
            # disabled
            # ------------------------------------------

            try:

                disabled = button.is_disabled()

            except Exception:

                disabled = None

            # ------------------------------------------
            # aria-disabled
            # ------------------------------------------

            aria_disabled = button.get_attribute(
                "aria-disabled"
            )

            # ------------------------------------------
            # class
            # ------------------------------------------

            class_name = button.get_attribute(
                "class"
            )

            # ------------------------------------------
            # id
            # ------------------------------------------

            button_id = button.get_attribute(
                "id"
            )

            # ------------------------------------------
            # text
            # ------------------------------------------

            text_content = button.text_content()

            if text_content:
                text_content = text_content.strip()
            else:
                text_content = ""

            # ------------------------------------------
            # HTML
            # ------------------------------------------

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

            # ------------------------------------------
            # ログ出力
            # ------------------------------------------

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
    # 8. 詳細JSON保存
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
    # 9. 今回はDiscord通知しない
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
    # 10. スクリーンショット
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
