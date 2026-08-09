from playwright.sync_api import sync_playwright
import json
import os
import requests
import time
from datetime import datetime


# ==================================================
# 基本設定
# ==================================================

URL = "https://store.usj.co.jp/ja/jp/store/c/extra/PCCSPRFD2A?config=true"

ADULT_PLUS_LABEL = (
    "¥7,000 の サンジの海賊レストラン（2名以上） "
    "を1枚追加する"
)

# 5分ごとにチェック
CHECK_INTERVAL_SECONDS = 5 * 60

# 5時間50分監視
MONITOR_DURATION_SECONDS = 5 * 60 * 60 + 50 * 60


# ==================================================
# ログ
# ==================================================

def log(message=""):
    print(message, flush=True)


# ==================================================
# 大人7,000円の＋ボタンを探す
# ==================================================

def find_adult_plus(page):

    log("大人7,000円の＋ボタンを探しています...")

    locator = page.locator(
        f'button[aria-label="{ADULT_PLUS_LABEL}"]'
    )

    count = locator.count()

    log(
        f"大人＋ボタン候補数: {count}"
    )

    if count == 0:
        raise RuntimeError(
            "大人7,000円の＋ボタンが見つかりませんでした。"
        )

    # --------------------------------------------------
    # 今回の修正点
    #
    # is_visible() に頼らず、
    # 候補の中から実際に操作できるものを探す
    # --------------------------------------------------

    for i in range(count):

        try:

            button = locator.nth(i)

            log(
                f"大人＋ボタン候補 {i + 1} を確認しています..."
            )

            # DOM上のボタンまでスクロール
            try:
                button.scroll_into_view_if_needed(
                    timeout=5000
                )
            except Exception:
                pass

            page.wait_for_timeout(500)

            # disabledかどうか確認
            aria_disabled = button.get_attribute(
                "aria-disabled"
            )

            disabled = button.get_attribute(
                "disabled"
            )

            log(
                f"aria-disabled: {aria_disabled}, "
                f"disabled: {disabled}"
            )

            if aria_disabled == "true":
                log(
                    f"候補 {i + 1} は無効なので次へ進みます。"
                )
                continue

            if disabled is not None:
                log(
                    f"候補 {i + 1} はdisabledなので次へ進みます。"
                )
                continue

            log(
                f"大人＋ボタンを使用: {i + 1} / {count}"
            )

            return button

        except Exception as e:

            log(
                f"候補 {i + 1} の確認中にエラー: {e}"
            )

    raise RuntimeError(
        "使用可能な大人7,000円の＋ボタンを"
        "見つけられませんでした。"
    )


# ==================================================
# 大人選択部分のテキスト取得
# ==================================================

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

        log(
            f"大人選択部分取得エラー: {e}"
        )

        return ""


# ==================================================
# 大人2名を選択
# ==================================================

def select_two_adults(page):

    log(
        "大人7,000円の＋ボタンを探しています..."
    )

    adult_plus = find_adult_plus(page)

    before_text = get_adult_area_text(
        page,
        adult_plus
    )

    log(
        f"大人選択部分: {before_text}"
    )

    # ----------------------------------------------
    # すでに2名の場合
    # ----------------------------------------------

    if "2 selected 2" in before_text:

        log(
            "すでに大人2名になっています。"
        )

        return

    # ----------------------------------------------
    # 1回目クリック
    # ----------------------------------------------

    log(
        "大人＋ボタンを1回クリックします..."
    )

    adult_plus.scroll_into_view_if_needed()

    page.wait_for_timeout(500)

    adult_plus.click(
        timeout=30000
    )

    page.wait_for_timeout(1500)

    # ----------------------------------------------
    # クリック後の状態確認
    # ----------------------------------------------

    adult_plus = find_adult_plus(page)

    after_first_text = get_adult_area_text(
        page,
        adult_plus
    )

    log(
        f"大人選択部分: {after_first_text}"
    )

    log(
        f"1回目クリック後の大人人数情報: "
        f"{after_first_text}"
    )

    # 1回目で2名になった場合
    if "2 selected 2" in after_first_text:

        log(
            "1回目のクリックですでに大人2名になりました。"
        )

        return

    # ----------------------------------------------
    # 2回目クリック
    # ----------------------------------------------

    log(
        "大人＋ボタンを2回目クリックします..."
    )

    adult_plus.scroll_into_view_if_needed()

    page.wait_for_timeout(500)

    adult_plus.click(
        timeout=30000
    )

    page.wait_for_timeout(2000)

    # ----------------------------------------------
    # 最終確認
    # ----------------------------------------------

    adult_plus = find_adult_plus(page)

    final_text = get_adult_area_text(
        page,
        adult_plus
    )

    log(
        f"最終的な大人選択部分: {final_text}"
    )

    if "2 selected 2" in final_text:

        log(
            "大人2名を確認しました。"
        )

    else:

        log(
            "大人2名の表示を確認できませんでしたが、"
            "カレンダー取得を続行します。"
        )


# ==================================================
# カレンダー取得
# ==================================================

def get_calendar(page):

    log(
        "カレンダーを読み込んでいます..."
    )

    page.wait_for_timeout(3000)

    # ----------------------------------------------
    # ページを最後までスクロール
    # ----------------------------------------------

    last_height = 0

    for i in range(25):

        page.mouse.wheel(
            0,
            3000
        )

        page.wait_for_timeout(1000)

        height = page.evaluate(
            "document.body.scrollHeight"
        )

        log(
            f"ページ高さ: {height}"
        )

        if height == last_height:
            break

        last_height = height

    # ----------------------------------------------
    # ボタン取得
    # ----------------------------------------------

    calendar = []

    buttons = page.locator("button")

    count = buttons.count()

    log(
        f"ボタン総数: {count}"
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
            # 日付の表示文字
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


# ==================================================
# 販売可能日を判定
# ==================================================

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

        # 7000円か
        price_is_7000 = (
            "7000" in price
            or "¥7,000" in price
        )

        # disabledではない
        is_enabled = (
            disabled is False
        )

        # aria-disabledでも確認
        aria_is_enabled = (
            aria_disabled != "true"
        )

        # ------------------------------------------
        # 7000円 + disabledではない
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


# ==================================================
# Discord通知
# ==================================================

def send_discord(available_dates):

    webhook = os.getenv(
        "DISCORD_WEBHOOK"
    )

    if not webhook:

        log(
            "DISCORD_WEBHOOK が設定されていません。"
        )

        return False

    if not available_dates:

        log(
            "販売可能日はありません。"
        )

        log(
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

        log(
            f"Discord response: {response.status_code}"
        )

        if response.status_code == 204:

            log(
                "Discord通知に成功しました"
            )

            return True

        log(
            "Discord通知に失敗しました"
        )

        log(
            f"Discord response body: {response.text}"
        )

        return False

    except Exception as e:

        log(
            f"Discord notification error: {e}"
        )

        return False


# ==================================================
# 1回分の監視
# ==================================================

def run_one_check(page, notified_dates):

    log("")
    log(
        "=========================================="
    )

    log(
        "監視チェック開始: "
        + datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    log(
        "=========================================="
    )

    # ----------------------------------------------
    # USJページ
    # ----------------------------------------------

    log(
        "USJページを開いています..."
    )

    try:

        page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

    except Exception as e:

        log(
            "ページ読み込みでエラーが発生しました:"
        )

        log(
            str(e)
        )

        log(
            "今回のチェックを終了し、次回チェックへ進みます。"
        )

        return

    log(
        "USJページ読み込み完了"
    )

    page.wait_for_timeout(5000)

    # ----------------------------------------------
    # 大人2名
    # ----------------------------------------------

    try:

        select_two_adults(page)

    except Exception as e:

        log(
            "大人2名選択でエラーが発生しました:"
        )

        log(
            str(e)
        )

        try:

            page.screenshot(
                path="error_adult.png",
                full_page=True
            )

            log(
                "error_adult.png を保存しました"
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

        log(
            "カレンダー取得でエラーが発生しました:"
        )

        log(
            str(e)
        )

        return

    # ----------------------------------------------
    # カレンダー表示
    # ----------------------------------------------

    log(
        "========== CALENDAR =========="
    )

    for item in calendar:

        log(
            str(item)
        )

    log(
        f"カレンダー件数: {len(calendar)}"
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

        log(
            "calendar.json を保存しました"
        )

    except Exception as e:

        log(
            f"calendar.json保存エラー: {e}"
        )

    # ----------------------------------------------
    # 販売可能日
    # ----------------------------------------------

    available_dates = find_available_dates(
        calendar
    )

    log(
        f"販売可能日数: {len(available_dates)}"
    )

    if available_dates:

        log(
            "========== 販売可能日 =========="
        )

        for item in available_dates:

            log(
                str(item)
            )

    # ----------------------------------------------
    # Discord
    # ----------------------------------------------

    webhook = os.getenv(
        "DISCORD_WEBHOOK"
    )

    if webhook:

        log(
            "DISCORD_WEBHOOK: 設定されています"
        )

    else:

        log(
            "DISCORD_WEBHOOK: 設定されていません"
        )

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

        log(
            f"新しく見つかった販売可能日: "
            f"{len(new_available_dates)}"
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

            log(
                "販売可能日はありますが、"
                "この監視セッションでは通知済みです。"
            )

        else:

            log(
                "販売可能日はありません。"
            )

            log(
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

        log(
            "スクリーンショットを保存しました"
        )

    except Exception as e:

        log(
            f"スクリーンショット保存エラー: {e}"
        )


# ==================================================
# メイン
# ==================================================

log(
    "### MONITOR.PY START ###"
)

log(
    "Pythonが開始しました。"
)

log(
    f"監視間隔: {CHECK_INTERVAL_SECONDS} 秒"
)

log(
    f"監視時間: {MONITOR_DURATION_SECONDS} 秒"
)

log(
    "Playwrightを開始します..."
)


notified_dates = set()

start_time = time.time()

try:

    with sync_playwright() as p:

        log(
            "Playwright開始成功"
        )

        log(
            "Chromiumを起動します..."
        )

        browser = p.chromium.launch(
            headless=True
        )

        log(
            "Chromium起動成功"
        )

        page = browser.new_page(
            viewport={
                "width": 390,
                "height": 844
            }
        )

        log(
            "ブラウザページ作成成功"
        )

        check_number = 0

        while True:

            elapsed = (
                time.time()
                - start_time
            )

            if elapsed >= MONITOR_DURATION_SECONDS:

                log(
                    "設定した監視時間が終了しました。"
                )

                break

            check_number += 1

            log("")
            log(
                "##########################################"
            )

            log(
                f"監視回数: {check_number}"
            )

            log(
                f"経過時間: {int(elapsed)} 秒"
            )

            log(
                "##########################################"
            )

            try:

                run_one_check(
                    page,
                    notified_dates
                )

            except Exception as e:

                log(
                    "監視チェック中に予期しないエラー:"
                )

                log(
                    str(e)
                )

            # --------------------------------------
            # 次回チェック
            # --------------------------------------

            elapsed = (
                time.time()
                - start_time
            )

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

            log("")
            log(
                f"次回チェックまで "
                f"{int(wait_seconds)} 秒待機します。"
            )

            time.sleep(
                wait_seconds
            )

        log(
            "ブラウザを終了します..."
        )

        browser.close()

        log(
            "ブラウザ終了"
        )

except Exception as e:

    log(
        "=========================================="
    )

    log(
        "MONITOR.PYで致命的なエラーが発生しました"
    )

    log(
        str(e)
    )

    log(
        "=========================================="
    )

    raise


log("")
log(
    "========== MONITOR COMPLETE =========="
        )
