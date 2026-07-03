import requests
import time
import config

SERVER_URL = "http://192.168.3.13:8000/process"


def start_network_client():
    print(f"� [Network Client]: ماژول شبکه فعال شد. در انتظار پیام برای ارسال به {SERVER_URL}")

    while config.is_running:
        if not config.text_fa_queue.empty():
            text_fa = config.text_fa_queue.get()
            payload = {"text_fa": text_fa}

            try:
                print(f"� [Network]: در حال ارسال پیام به سرور: '{text_fa}'")
                response = requests.post(SERVER_URL, json=payload, timeout=120)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get("status") == "success":
                            print(f"✅ [Network]: پردازش موفقیت‌آمیز بود. ترجمه: {data.get('translated_text')}")
                        else:
                            print(f"⚠️ [Network Warning]: سرور ویندوز پیام داد: {data.get('message')}")
                    except ValueError:
                        print("❌ [Network Error]: پاسخ سرور قابل پردازش نبود.")
                else:
                    print(f"❌ [Network Error]: خطای سرور با کد {response.status_code}")

            except requests.exceptions.Timeout:
                print("❌ [Network Error]: سرور بیش از حد طول داد (Timeout).")
            except requests.exceptions.ConnectionError:
                print("❌ [Network Error]: ارتباط با سرور قطع شد! IP را بررسی کنید.")
            except Exception as e:
                print(f"❌ [Network Exception]: {e}")

        time.sleep(0.1)