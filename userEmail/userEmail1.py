import sys
from playwright.sync_api import sync_playwright
import time
import os
import json
import requests
import datetime

CONFIG_PATH = "userEmail1_config.json"
# 全局已通知集合
notified_set = set()


def reserve_slot(page, slot_td_elem, slot):
    """
    预订指定时间段的函数示例。
    这里只做点击操作，具体流程请根据实际页面调整。
    """
    def handle_dialog(dialog):
        print(f"弹窗内容: {dialog.message}")
        dialog.accept()
        print("已自动点击弹窗的确定按钮")
    try:
        page.on("dialog", handle_dialog)
        slot_td_elem.click()
        page.wait_for_timeout(500)
        # 新增：点击 class 为 form-control btn btn-go btn-lg my-2 btn-width 的按钮
        btns = page.query_selector_all(
            'button.form-control.btn.btn-go.btn-lg.my-2.btn-width')
        if btns and len(btns) > 0:
            btns[0].click()
            page.wait_for_timeout(1000)
            print("已点击 form-control btn btn-go btn-lg my-2 btn-width 按钮")
        page.wait_for_timeout(1000)
        # 新增：输入人数
        people_input = page.query_selector('input#peoples0')
        if people_input:
            people_input.fill("2")
            print("已输入人数2")
            btns = page.query_selector_all(
                'button.form-control.btn.btn-go.btn-lg.mb-2')
            if btns and len(btns) > 0:
                btns[0].hover()
                btns[0].click()
                print("已点击预约按钮")
                page.wait_for_timeout(2000)
            page.screenshot(path=f"2_after_first_btn_{int(time.time())}.png")
            page.wait_for_timeout(3000)
        page.screenshot(path=f"error_purpose_home_{int(time.time())}.png")
        print("已截图当前页面为 error_purpose_home_时间戳.png")
        print(f"已尝试预订: {slot}")
        return True
    except Exception as e:
        print(f"预订失败: {slot}, 错误: {e}")
        return False


def same_month(date1, date2):
    return date1[:7] == date2[:7]


def query_tokyo_reservation(url, user_id, password, building_id, building_name, query_dates, query_time_slots, email):
    """
    查询指定场馆、指定日期、指定时间段的预约情况。
    :param url: 预约系统URL
    :param user_id: 用户ID
    :param password: 密码
    :param building_id: 场馆ID
    :param building_name: 场馆名称
    :param query_date: 查询日期，格式"YYYY-MM-DD"
    :param query_time_slots: 时间段列表，如["09:00-11:00", "11:00-13:00"]
    :return: dict，key为时间段，value为"空き"或"予約あり"
    """
    result = {}
    
    slot_map = {
        "09:00-11:00": "10",
        "11:00-13:00": "20",
        "13:00-15:00": "30",
        "15:00-17:00": "40",
        "17:00-19:00": "50",
        "19:00-21:00": "60"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,zh;q=0.5",
        "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
    }
    global notified_set
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="ja-JP",
                timezone_id="Asia/Tokyo",
                user_agent=headers["User-Agent"]
            )
            page = context.new_page()
            page.set_extra_http_headers(headers)

            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(500)
            
            # 新增：检测“現在、ご指定のページはアクセスできません。”，如有则快速刷新10次
            for i in range(10):
                error_elem = page.query_selector(':has-text("現在、ご指定のページはアクセスできません。")')
                if error_elem:
                    page.reload()
                    page.wait_for_timeout(100)
                else:
                    break
            page.wait_for_timeout(1000)
            # 在查找btn-login前，先检查异常提示
            error_elem1 = page.query_selector(':has-text("システム異常が発生しました。")')
            error_elem2 = page.query_selector(':has-text("不正な画面遷移でアクセスされた可能性があります。")')
            error_elem3 = page.query_selector(':has-text("現在、ご指定のページはアクセスできません。")')
            if error_elem1 or error_elem2 or error_elem3:
                print("检测到系统异常或不正画面，尝试点击返回按钮")
                retry_count = 0
                max_retry = 100
                while retry_count < max_retry:
                    # 如果已回到主页面（找到select#purpose-home），直接跳过
                    if page.query_selector('select#purpose-home'):
                        print("已回到主页面，跳过异常处理")
                        break                    
                    btn_back = page.query_selector('button.form-control.btn.btn-light.mb-2.mr-2')
                    if btn_back:
                        btn_back.click()
                        print("已点击返回按钮")
                        page.wait_for_timeout(1000)
                        break
                    else:
                        page.reload()
                        page.wait_for_timeout(100)
                        # reload后立即再查一次
                        btn_back = page.query_selector('button.form-control.btn.btn-light.mb-2.mr-2')
                        if btn_back:
                            btn_back.click()
                            print("reload后已找到并点击返回按钮")
                            page.wait_for_timeout(1000)
                            break
                        retry_count += 1
                if retry_count == max_retry:
                    print("多次reload后仍未找到返回按钮，跳过")
                    
            # 新增：尝试多次加载页面，若找不到btn-login则刷新
            # max_retry = 3
            # for attempt in range(max_retry):
            #     page.goto(url, wait_until="domcontentloaded")
            #     page.wait_for_timeout(500)
            #     try:
            #         btn_login = page.wait_for_selector(
            #             'button#btn-login', timeout=5000)
            #         break  # 找到就退出循环
            #     except Exception:
            #         if attempt < max_retry - 1:
            #             print("未找到登录按钮，刷新页面重试...")
            #             page.reload()
            #             page.wait_for_timeout(1000)
            #         else:
            #             raise  # 最后一次还失败则抛出异常
            # btn_login.click()
            # page.wait_for_timeout(2000)
            # user_input = page.wait_for_selector('input#userId', timeout=5000)
            # user_input.fill(user_id)
            # pwd_input = page.wait_for_selector('input#password', timeout=5000)
            # pwd_input.fill(password)
            # btn_login = page.wait_for_selector('button#btn-go', timeout=5000)
            # btn_login.click()
            # page.wait_for_timeout(1000)

            # 选择项目 テニス（人工芝）
            try:
                purpose_select = page.wait_for_selector(
                    'select#purpose-home', timeout=5000, state="attached")
                purpose_select.click()
                # 判断是否为室内场馆
                indoor_ids = ["1310", "1315", "1350", "1370"]
                if building_id in indoor_ids:
                    purpose_select.select_option("1000_1020")  # 室内项目
                    print(f"{building_name}({building_id}) 为室内场馆，选择项目 1000_1020")
                else:
                    purpose_select.select_option("1000_1030")  # 人工芝项目
                    print(f"{building_name}({building_id}) 为室外场馆，选择项目 1000_1030")
                page.wait_for_timeout(500)
            except Exception as e:
                print(f"查询异常: {e}")
                browser.close()
                return None

            # 选择场馆
            bname_select = page.wait_for_selector(
                'select#bname-home', timeout=5000)
            bname_select.click()
            bname_select.select_option(building_id)
            page.wait_for_timeout(500)

            # 设置日期
            daystart_home_input = page.wait_for_selector(
                'input#daystart-home', state="attached", timeout=5000)
            daystart_home_input.click()
            daystart_home_input.fill(query_dates[0])
            page.evaluate("""
                el => {
                    el.value = '%s';
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """ % query_dates[0], daystart_home_input)
            page.wait_for_timeout(500)

            # 点击搜索按钮
            search_btn = page.wait_for_selector(
                'button.form-control.btn.btn-go.btn-lg.my-5.btn-width', state="attached", timeout=5000)
            search_btn.click()
            page.wait_for_timeout(5000)

            # 展开日历
            calendar_btns = page.query_selector_all(
                'span.span-icon.span-icon-down')
            if calendar_btns and len(calendar_btns) > 0:
                calendar_btns[0].click()
                if building_id == "1140":
                    page.wait_for_timeout(30000)  # 舎人公园特殊等待20秒
                else:
                    page.wait_for_timeout(15000)
                
            # 判断是否只有一个日期
            first_date = query_dates[0]
            if len(query_dates) == 1:
                dates_to_query = query_dates
                other_month_dates = []
            else:
                dates_to_query = [
                    d for d in query_dates if same_month(d, first_date)]
                other_month_dates = [
                    d for d in query_dates if not same_month(d, first_date)]                     

            # 新增：遍历所有查询日期，先点击日历格，再查时间段
            for query_date in dates_to_query:
                td_id = f"month_{query_date.replace('-', '')}"
                print(f"正在处理日期: {query_date} (td ID: {td_id})")
                td_elem = page.query_selector(f'td#{td_id}')
                if not td_elem:
                    print(f"{query_date} 未找到对应的日历格，跳过")
                    continue

                # 检查是否有 class="calendar-status calendar-status-mb" 的 img
                status_img = td_elem.query_selector(
                    'img.calendar-status.calendar-status-mb')
                if status_img:
                    alt_text = status_img.get_attribute('alt')
                    if alt_text == "予約あり":
                        print(f"{query_date} 已有预约，跳过")
                        continue  # 跳过该日期

                # 如果不是予約あり，则点击该td_elem
                td_elem.click()
                page.wait_for_timeout(2000)

                # 查询每个时间段
                for slot in query_time_slots:
                    slot_td_id = f"{query_date.replace('-', '')}_{slot_map.get(slot, '10')}"
                    slot_td_elem = page.query_selector(
                        f'td[id="{slot_td_id}"]')
                    if not slot_td_elem:
                        result[slot] = "无数据"
                        continue
                    slot_img = slot_td_elem.query_selector(
                        'img.calendar-status')
                    if slot_img:
                        slot_alt = slot_img.get_attribute('alt')
                        result[slot] = slot_alt
                        notify_key = f"{building_name}_{query_date}_{slot}"
                        if slot_alt == "空き" and notify_key not in notified_set:
                            # reserve_slot(page, slot_td_elem, slot)
                            # 新增：有空位时调用 send-venue-email 的 API
                            try:
                                payload = {
                                    "venueName": building_name,
                                    "timeRange": slot,
                                    "date": query_date,
                                    "email": email
                                }
                                resp = requests.post(
                                    "https://awake-helped-fish.ngrok-free.app/api/send-venue-email",  # 替换为你的API地址
                                    json=payload,
                                    timeout=10
                                )
                                if resp.ok:
                                    print(f"已发送空位通知邮件: {building_name} {slot}")
                                    notified_set.add(notify_key)
                                else:
                                    print(f"邮件API调用失败: {resp.text}")
                            except Exception as e:
                                print(f"调用邮件API异常: {e}")
                    else:
                        result[slot] = "无状态"

            # 如果有其他月份的日期且当前日期大于当月18号时，点击“次月”按钮后处理
            today = datetime.date.today()
            if other_month_dates and today.day > 18:
                print("切换到次月，处理其他月份日期：", other_month_dates)
                next_month_btn = page.query_selector('a#next-month')
                print("next_month_btn:", next_month_btn)
                if next_month_btn:
                    next_month_btn.click()
                    if building_id == "1140":
                        page.wait_for_timeout(20000)  # 舎人公园特殊等待20秒
                    else:
                        page.wait_for_timeout(20000)
                    # 遍历次月所有日期
                    for query_date in other_month_dates:
                        td_id = f"month_{query_date.replace('-', '')}"
                        print(f"正在处理日期: {query_date} (td ID: {td_id})")
                        td_elem = page.query_selector(f'td#{td_id}')
                        if not td_elem:
                            print(f"{query_date} 未找到对应的日历格，跳过")
                            continue
                        status_img = td_elem.query_selector(
                            'img.calendar-status.calendar-status-mb')
                        if not status_img:
                            print(f"{query_date} 已有预约，跳过")
                            continue
                        alt_text = status_img.get_attribute('alt')
                        if alt_text == "予約あり":
                            print(f"{query_date} 已有预约，跳过")
                            continue
                        td_elem.click()
                        page.wait_for_timeout(5000)
                        for slot in query_time_slots:
                            slot_td_id = f"{query_date.replace('-', '')}_{slot_map.get(slot, '10')}"
                            slot_td_elem = page.query_selector(
                                f'td[id="{slot_td_id}"]')
                            if not slot_td_elem:
                                result[slot] = "无数据"
                                continue
                            slot_img = slot_td_elem.query_selector(
                                'img.calendar-status')
                            if slot_img:
                                slot_alt = slot_img.get_attribute('alt')
                                result[slot] = slot_alt
                                notify_key = f"{building_name}_{query_date}_{slot}"
                                if slot_alt == "空き" and notify_key not in notified_set:
                                    try:
                                        payload = {
                                            "venueName": building_name,
                                            "timeRange": slot,
                                            "date": query_date,
                                            "email": email
                                        }
                                        resp = requests.post(
                                            "https://awake-helped-fish.ngrok-free.app/api/send-venue-email",
                                            json=payload,
                                            timeout=10
                                        )
                                        if resp.ok:
                                            print(
                                                f"已发送空位通知邮件: {building_name} {slot}")
                                            notified_set.add(notify_key)
                                        else:
                                            print(f"邮件API调用失败: {resp.text}")
                                    except Exception as e:
                                        print(f"调用邮件API异常: {e}")
                            else:
                                result[slot] = "无状态"

            browser.close()
    except Exception as e:
        print(f"查询异常: {e}")
        if browser:
            try:
                browser.close()
            except Exception as close_e:
                print(f"关闭浏览器时异常: {close_e}")
        return None
    return result


# 示例调用
if __name__ == "__main__":
    # 读取配置
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    url = "https://kouen.sports.metro.tokyo.lg.jp/web/index.jsp"
    user_id = config["user_id"]
    password = config["password"]
    query_dates = config["query_dates"]
    query_time_slots = config["query_time_slots"]
    building_dict = config["buildings"]
    interval_seconds = config.get("interval_seconds", 60)
    email = config.get("email", "")

    last_reset_date = None
    while True:
        today = datetime.date.today()
        if last_reset_date != today:
            notified_set.clear()
            last_reset_date = today
            print("已重置今日的已通知集合。")
        all_results = {}
        for building_id, building_name in building_dict.items():
            print(f"查询场馆: {building_name} ({building_id})")
            result = query_tokyo_reservation(
                url, user_id, password, building_id, building_name, query_dates, query_time_slots, email
            )
            all_results[building_name] = result
            time.sleep(2)  # 场馆间隔，防止请求过快

        print("本轮所有场馆查询结果：")
        print(json.dumps(all_results, ensure_ascii=False, indent=2))
        print(f"等待{interval_seconds}秒后再次执行查询...（Ctrl+C可终止）")
        time.sleep(interval_seconds)
