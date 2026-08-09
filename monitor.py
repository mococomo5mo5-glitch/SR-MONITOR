from playwright.sync_api import sync_playwright
import json
import os
import requests
import time
from datetime import datetime

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

ADULT_PLUS_LABEL = (
    "¥7,000 の サンジの海賊レストラン（2名以上） "
    "を1枚追加する"
)

# ==================================================
# 監視設定
# ==================================================

# 5分ごとに確認
CHECK_INTERVAL_SECONDS = 5 * 60

# 5時間50分間、連続監視
MONITOR_DURATION_SECONDS = 5 * 60 * 60 + 50 * 60


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

            if button.is_visible():

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
        "表示されている大人7,000円の＋ボタンを"
        "見つけられませんでした。"
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


def select_two_adults(page):

    print(
        "大人7,000円の＋ボタンを探しています..."
    )

    adult_plus = find_adult_plus(page)

    before_text = get_adult_area_text(
        page,
        adult_plus
    )

    print(
        "大人選択部分:",
        before_text
    )

    # すでに2名なら終了
    if "2 selected 2" in before_text:

        print(
            "すでに大人2名になっています。"
        )

        return

    # ----------------------------------------------
    # 1回目
    # ----------------------------------------------

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

    # 画面によってテキスト取得ができない場合があるため、
    # selected文字列が取れなくても次へ進む。
    if "2 selected 2" in after_first_text:

        print(
            "1回目のクリックですでに2名になりました。"
        )

        return

    # ----------------------------------------------
    # 2回目
    # ----------------------------------------------

    print(
        "大人＋ボタンを2回目クリックします..."
    )

    adult_plus.click(
        timeout=30000
    )

    page.wait_for_timeout(2000)

    print(
        "大人2名の選択処理が完了しました。"
    )


def get_calendar(page):

    print(
        "カレンダーを読み込んでいます..."
    )

    # ----------------------------------------------
    # カレンダーが表示されるまで待つ
    # ----------------------------------------------

    page.wait_for_timeout(3000)

    # ----------------------------------------------
    # 最後までスクロール
    # ----------------------------------------------

    last_height = 0

    for _ in range(25):

        page.mouse.wheel(
            0,
            3000
        )

        page.wait_for_timeout(1000)

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

    # ----------------------------------------------
    # カレンダー取得
    # ----------------------------------------------

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

            # --------------------------------------
            # 日付・価格
            # --------------------------------------

            if " - " in aria:

                date, price = aria.split(
                    " - ",
                    1
                )

            else:

                date = aria
                price = ""

            # --------------------------------------
            # 日付ボタンの文字
            # --------------------------------------

            text = button.text_content()

            if text:

                text = text.strip()

            else:

                text = ""

            # --------------------------------------
            # disabled
            # --------------------------------------

            try:

                disabled = button.is_disabled()

            except Exception:

                disabled = None

            # --------------------------------------
            # aria-disabled
            # --------------------------------------

            aria_disabled = button.get_attribute(
                "aria-disabled"
            )

            # --------------------------------------
            # class / id
            # --------------------------------------

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

    return calendar


def find_available_dates(calendar):

    available_dates = []

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
        # 7000円か
        # ------------------------------------------

        price_is_7000 = (
            "7000" in price
            or "¥7,000" in price
        )

        # ------------------------------------------
        # ボタンが有効か
        # ------------------------------------------

        is_enabled = (
            disabled is False
        )

        # ------------------------------------------
        # aria-disabledも確認
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

    return available_dates


def send_discord(available_dates):

    webhook = os.getenv(
        "DISCORD_WEBHOOK"
    )

    if not webhook:

        print(
            "DISCORD_WEBHOOK が設定されていません。"
        )

        return False

    if not available_dates:

        print(
            "販売可能日はありません。"
        )

        print(
            "Discord通知は行いません。"
        )

        return False

    lines = []

    for item in available_dates:

        lines.append(
            f"{item['date']} : {item['price']}"
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

            return True

        print(
            "Discord通知に失敗しました"
        )

        print(
            "Discord response body:",
            response.text
        )

        return False

    except Exception as e:

        print(
            "Discord notification error:",
            e
        )

        return False


def run_one_check(page, notified_dates):

    print("")
    print(
        "=========================================="
    )
    print(
        "監視チェック開始:",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    print(
        "=========================================="
    )

    # ----------------------------------------------
    # USJページを開く
    # ----------------------------------------------

    print(
        "USJページを開いています..."
    )

    try:

        page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

    except Exception as e:

        print(
            "ページ読み込みでエラーが発生しました:"
        )

        print(
            e
        )

        print(
            "60秒待たずにページ読み込みを終了し、"
            "次回チェックへ進みます。"
        )

        return

    page.wait_for_timeout(5000)

    print(
        "USJページ読み込み完了"
    )

    # ----------------------------------------------
    # 大人2名
    # ----------------------------------------------

    try:

        select_two_adults(page)

    except Exception as e:

        print(
            "大人2名選択でエラーが発生しました:"
        )

        print(
            e
        )

        try:

            page.screenshot(
                path="error_adult.png",
                full_page=True
            )

        except Exception:

            pass

        return

    # ----------------------------------------------
    # カレンダー
    # ----------------------------------------------

    try:

        calendar = get_calendar(page)

    except Exception as e:

        print(
            "カレンダー取得でエラーが発生しました:"
        )

        print(
            e
        )

        return

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

    # ----------------------------------------------
    # calendar.json
    # ----------------------------------------------

    try:

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

    except Exception as e:

        print(
            "calendar.json保存エラー:",
            e
        )

    # ----------------------------------------------
    # 販売可能日
    # ----------------------------------------------

    available_dates = find_available_dates(
        calendar
    )

    print(
        "販売可能日数:",
        len(available_dates)
    )

    if available_dates:

        print(
            "========== 販売可能日 =========="
        )

        for item in available_dates:

            print(
                item
            )

    # ----------------------------------------------
    # Discord通知
    # ----------------------------------------------

    new_available_dates = []

    for item in available_dates:

        date = item.get(
            "date",
            ""
        )

        if date not in notified_dates:

            new_available_dates.append(
                item
            )

    if new_available_dates:

        print(
            "新しく見つかった販売可能日:",
            len(new_available_dates)
        )

        success = send_discord(
            new_available_dates
        )

        if success:

            for item in new_available_dates:

                notified_dates.add(
                    item.get(
                        "date",
                        ""
                    )
                )

    else:

        if available_dates:

            print(
                "販売可能日はありますが、"
                "すでにこの監視セッションで通知済みです。"
            )

        else:

            print(
                "販売可能日はありません。"
            )

            print(
                "Discord通知は行いません。"
            )

    # ----------------------------------------------
    # スクリーンショット
    # ----------------------------------------------

    try:

        page.screenshot(
            path="page.png",
            full_page=True
        )

        print(
            "スクリーンショットを保存しました"
        )

    except Exception as e:

        print(
            "スクリーンショット保存エラー:",
            e
        )


# ==================================================
# メイン
# ==================================================

print(
    "=========================================="
)

print(
    "USJ Monitor 開始"
)

print(
    "監視間隔:",
    CHECK_INTERVAL_SECONDS,
    "秒"
)

print(
    "監視時間:",
    MONITOR_DURATION_SECONDS,
    "秒"
)

print(
    "=========================================="
)

notified_dates = set()

start_time = time.time()

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

    check_number = 0

    while True:

        elapsed = time.time() - start_time

        if elapsed >= MONITOR_DURATION_SECONDS:

            print(
                "監視時間終了です。"
            )

            break

        check_number += 1

        print("")
        print(
            "##########################################"
        )

        print(
            "監視回数:",
            check_number
        )

        print(
            "経過時間:",
            int(elapsed),
            "秒"
        )

        print(
            "##########################################"
        )

        try:

            run_one_check(
                page,
                notified_dates
            )

        except Exception as e:

            print(
                "監視チェック中に予期しないエラー:"
            )

            print(
                e
            )

        # ------------------------------------------
        # 次回チェック
        # ------------------------------------------

        elapsed = time.time() - start_time

        remaining = (
            MONITOR_DURATION_SECONDS
            - elapsed
        )

        if remaining <= 0:

            break

        wait_seconds = min(
            CHECK_INTERVAL_SECONDS,
            remaining
        )

        print("")
        print(
            "次回チェックまで",
            int(wait_seconds),
            "秒待機します。"
        )

        time.sleep(
            wait_seconds
        )

    browser.close()

print("")
print(
    "========== MONITOR COMPLETE =========="
        )
