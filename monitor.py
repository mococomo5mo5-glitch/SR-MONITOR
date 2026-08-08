from playwright.sync_api import sync_playwright
import json
import os
import re
import requests


URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

ADULT_PLUS_LABEL = (
    "¥7,000 の サンジの海賊レストラン（2名以上） "
    "を1枚追加する"
)


def get_adult_quantity(page, adult_plus):
    """
    大人7,000円の＋ボタン周辺から、
    現在の大人人数を取得する。
    """

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

        # 例:
        # 大人 ¥7,000（税込） - 0 +
        # のような表示から数字を取得する。
        #
        # 7,000は価格なので除外し、
        # 0～9の単独数字の最後を人数として扱う。
        numbers = re.findall(r"(?<![\d,])\d+(?![\d,])", text)

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


def find_visible_adult_plus(page):
    """
    大人7,000円の＋ボタンのうち、
    実際に表示されているものを探す。
    """

    locator = page.locator(
        f'button[aria-label="{ADULT_PLUS_LABEL}"]'
    ).filter(
        visible=True
    )

    # 最大60秒待つ
    locator.first.wait_for(
        state="visible",
        timeout=60000
    )

    count = locator.count()

    print("表示されている大人＋ボタン:", count)

    # 複数ある場合でも、表示されているものだけを対象にする。
    for i in range(count):
        candidate = locator.nth(i)

        try:
            if not candidate.is_visible():
                continue

            candidate.scroll_into_view_if_needed()

            page.wait_for_timeout(500)

            print(
                "大人＋ボタンを使用:",
                i + 1,
                "/",
                count
            )

            return candidate

        except Exception:
            continue

    raise RuntimeError(
        "表示されている大人7,000円の＋ボタンを"
        "見つけられませんでした。"
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

    # --------------------------------------------------
    # 1. USJページを開く
    # --------------------------------------------------

    print("USJページを開いています...")

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(5000)

    print("USJページ読み込み完了")

    # --------------------------------------------------
    # 2. 大人2名にする
    # --------------------------------------------------

    print("大人7,000円の＋ボタンを探しています...")

    adult_plus = find_visible_adult_plus(page)

    # 現在の人数を確認
    quantity_before = get_adult_quantity(
        page,
        adult_plus
    )

    print(
        "クリック前の大人人数:",
        quantity_before
    )

    # すでに2名ならクリックしない
    if quantity_before == 2:

        print(
            "すでに大人2名になっています。"
        )

    else:

        # ----------------------------------------------
        # 1回目のクリック
        # ----------------------------------------------

        print(
            "大人＋ボタンを1回クリックします..."
        )

        adult_plus.click(
            timeout=30000
        )

        page.wait_for_timeout(1500)

        # ボタンは画面更新で入れ替わる可能性があるので、
        # もう一度探し直す。
        adult_plus = find_visible_adult_plus(
            page
        )

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
                "大人＋ボタンを1回押した後、"
                "大人人数が1になりませんでした。"
                f"現在の人数={quantity_after_first}"
            )

        # ----------------------------------------------
        # 2回目のクリック
        # ----------------------------------------------

        print(
            "大人＋ボタンを2回目クリックします..."
        )

        adult_plus.click(
            timeout=30000
        )

        page.wait_for_timeout(2000)

        # ----------------------------------------------
        # 2名になったことを確認
        # ----------------------------------------------

        adult_plus = find_visible_adult_plus(
            page
        )

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
                "大人＋ボタンを2回押した後、"
                "大人人数が2になりませんでした。"
                f"現在の人数={quantity_after_second}"
            )

    # --------------------------------------------------
    # 3. 大人2名を確認
    # --------------------------------------------------

    print(
        "大人2名を確認しました。"
    )

    page.wait_for_timeout(3000)

    # この時点の画面を保存
    page.screenshot(
        path="after_adult_2.png",
        full_page=True
    )

    # --------------------------------------------------
    # 4. カレンダーを最後まで読み込む
    # --------------------------------------------------

    print(
        "カレンダーを読み込んでいます..."
    )

    last_height = 0

    for _ in range(25):

        page.mouse.wheel(
            0,
            3000
        )

        page.wait_for_timeout(
            1200
        )

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

    # --------------------------------------------------
    # 5. カレンダー取得
    # --------------------------------------------------

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

            # 例:
            # 2026年8月14日金曜日 - 7000
            #
            # または:
            # 2026年8月1日土曜日 -
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

    # --------------------------------------------------
    # 6. カレンダー表示
    # --------------------------------------------------

    print(
        "========== CALENDAR =========="
    )

    for item in calendar:
        print(item)

    print(
        "カレンダー件数:",
        len(calendar)
    )

    # --------------------------------------------------
    # 7. JSON保存
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 8. Discord通知
    # --------------------------------------------------

    webhook = os.getenv(
        "DISCORD_WEBHOOK"
    )

    if webhook:

        print(
            "DISCORD_WEBHOOK: 設定されています"
        )

        hits = []

        for item in calendar:

            price = item.get(
                "price",
                ""
            )

            if (
                "7000" in price
                or "¥7,000" in price
            ):

                hits.append(
                    f"{item['date']} : {price}"
                )

        if hits:

            message = (
                "🎉 サンジの海賊レストラン"
                "に販売情報がありました！\n\n"
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
            "DISCORD_WEBHOOK が"
            "設定されていません"
        )

    # --------------------------------------------------
    # 9. 最終スクリーンショット
    # --------------------------------------------------

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
