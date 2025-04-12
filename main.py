import telebot
import time
import re
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

BOT_TOKEN = "7277046901:AAEZpktSUC_Q9PkcYShXaAGn4tuBojfIXuU"
bot = telebot.TeleBot(BOT_TOKEN)

# ---------- بريد مؤقت من 1secmail ----------
def gen():
    name = f"user{int(time.time())}"
    email = f"{name}@1secmail.com"
    return email

def get_messages(email):
    login, domain = email.split('@')
    url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
    r = requests.get(url)
    return r.json()

def read_message(email, message_id):
    login, domain = email.split('@')
    url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={message_id}"
    r = requests.get(url)
    return r.json()

def wait_for_verification_code(email, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            messages = get_messages(email)
            if messages:
                message_id = messages[0]['id']
                msg = read_message(email, message_id)
                body = msg.get("body", "")
                code = extract_code_from_text(body)
                if code:
                    return code
        except Exception as e:
            print(f"Email check error: {e}")
        time.sleep(5)
    return None

def extract_code_from_text(text):
    match = re.search(r'\b(\d{4,8})\b', text)
    if match:
        return match.group(1)
    return None

def log_account(platform, email, password, username=None):
    entry = {
        "platform": platform,
        "email": email,
        "password": password,
        "username": username,
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        with open("logs.json", "r", encoding="utf-8") as f:
            logs = json.load(f)
    except:
        logs = []
    logs.append(entry)
    with open("logs.json", "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

# ---------- تسجيل TikTok ----------
def register_tiktok(email, password="Test12345!"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("https://www.tiktok.com/signup/phone-or-email/email")
            time.sleep(2)
            page.select_option('select[aria-label="Month"]', '1')
            page.select_option('select[aria-label="Day"]', '1')
            page.select_option('select[aria-label="Year"]', '2000')
            page.fill('input[name="email"]', email)
            page.fill('input[name="password"]', password)
            page.click('button:has-text("Next")')
            code = wait_for_verification_code(email)
            if not code:
                return False, "لم يتم استلام كود التفعيل."
            page.fill('input[name="code"]', code)
            page.click('button:has-text("Next")')
            time.sleep(5)
            log_account("tiktok", email, password)
            return True, {"email": email, "password": password}
        except Exception as e:
            return False, str(e)
        finally:
            browser.close()

# ---------- تسجيل Instagram ----------
def register_instagram(email, password="Test12345!"):
    import random
    username = f"user{random.randint(1000,9999)}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("https://www.instagram.com/accounts/emailsignup/")
            time.sleep(3)
            page.fill("input[name='emailOrPhone']", email)
            page.fill("input[name='fullName']", "Test User")
            page.fill("input[name='username']", username)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")
            code = wait_for_verification_code(email)
            if not code:
                return False, "لم يتم استلام كود التفعيل."
            log_account("instagram", email, password, username)
            return True, {"email": email, "password": password, "username": username}
        except Exception as e:
            return False, str(e)
        finally:
            browser.close()

# ---------- تسجيل Facebook ----------
def register_facebook(email, password="Test12345!"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("https://www.facebook.com/r.php")
            time.sleep(2)
            page.fill("input[name='firstname']", "John")
            page.fill("input[name='lastname']", "Doe")
            page.fill("input[name='reg_email__']", email)
            page.fill("input[name='reg_passwd__']", password)
            page.select_option("select[name='birthday_day']", '1')
            page.select_option("select[name='birthday_month']", '1')
            page.select_option("select[name='birthday_year']", '2000')
            page.click("input[name='sex'][value='2']")
            page.click("button[name='websubmit']")
            code = wait_for_verification_code(email)
            if not code:
                return False, "لم يتم استلام كود التفعيل."
            log_account("facebook", email, password)
            return True, {"email": email, "password": password}
        except Exception as e:
            return False, str(e)
        finally:
            browser.close()

# ---------- أوامر البوت ----------
@bot.message_handler(commands=["start"])
def start(message):
    print(f"✅ استُقبل أمر /start من: {message.from_user.username} (ID: {message.from_user.id})")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("إنشاء حساب TikTok")
    markup.row("إنشاء حساب Instagram")
    markup.row("إنشاء حساب Facebook")
    bot.reply_to(message, "مرحبًا بك في SmartAccounts Bot، اختر نوع الحساب:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text.startswith("إنشاء حساب"))
def handle_create(message):
    platform_map = {
        "إنشاء حساب TikTok": "tiktok",
        "إنشاء حساب Instagram": "instagram",
        "إنشاء حساب Facebook": "facebook"
    }
    platform = platform_map.get(message.text)
    user_id = message.chat.id
    if not platform:
        bot.send_message(user_id, "❌ نوع الحساب غير مدعوم.")
        return

    bot.send_message(user_id, "⏳ جاري إنشاء بريد مؤقت...")
    email = gen()
    bot.send_message(user_id, f"✅ البريد المؤقت: {email}\n⏳ جاري التسجيل...")

    if platform == "tiktok":
        success, data = register_tiktok(email)
    elif platform == "instagram":
        success, data = register_instagram(email)
    elif platform == "facebook":
        success, data = register_facebook(email)
    else:
        success = False
        data = "منصة غير معروفة."

    if success:
        msg = f"✅ الحساب جاهز:\nEmail: `{data['email']}`\nPassword: `{data['password']}`"
        if 'username' in data:
            msg += f"\nUsername: `{data['username']}`"
        bot.send_message(user_id, msg, parse_mode="Markdown")
    else:
        bot.send_message(user_id, f"❌ فشل التسجيل:\n{data}")

print("✅ البوت يعمل الآن على Replit بكل الميزات")

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "❗ لم أفهم الأمر. أرسل /start لبدء الاستخدام.")

bot.infinity_polling()
