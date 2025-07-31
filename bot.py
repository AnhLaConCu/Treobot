import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import time, json, os

# ====== CẤU HÌNH BOT ======
TOKEN = '8334644593:AAEU62snunojSoDORLnAia2d19Qcb8xLqM8'
ADMIN_ID = 7623590839
WEBAPP_URL = "https://radiant-moonbeam-e11184.netlify.app/"
bot = telebot.TeleBot(TOKEN)
DATA_FILE = 'data.json'

# ====== INITIALIZE DATA ======
def initialize_data():
    default_data = {
        "keys": {},
        "user_keys": {},
        "key_users": {},
        "admins": [ADMIN_ID]
    }
    
    # Create file if not exists
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    # Try to load existing data
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read()
            if not content.strip():
                raise ValueError("Empty file")
            return json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error loading data: {e}. Reinitializing...")
        with open(DATA_FILE, 'w') as f:
            json.dump(default_data, f, indent=4)
        return default_data

# Load data
data = initialize_data()

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

def is_admin(user_id):
    return user_id in data["admins"]

def get_key_info(key):
    expiry = data["keys"].get(key)
    if not expiry:
        return None, "❌ Key không tồn tại"
    remaining = max(0, int((expiry - time.time()) / 86400))
    if remaining <= 0:
        return None, "⚠️ Key đã hết hạn"
    return remaining, None

# ====== COMMAND HANDLERS ======
@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "👋 Chào mừng!\n\n"
        "🔑 /nhapkey <MAKEY> – Nhập key truy cập tool\n"
        "🌐 /moweb – Mở Web App\n"
        "📊 /stats – Xem thông tin cá nhân\n"
        "ℹ️ /info – Xem UID & Key\n"
        "📋 /list – (admin) Xem danh sách user\n"
        "🛠️ /addkey, /removekey, /addadmin, /resetkey – (admin)"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['addkey'])
def add_key(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "⛔ Bạn không có quyền.")
    try:
        _, key, days = message.text.strip().split()
        days = int(days)
        expire_time = time.time() + days * 86400
        if key in data["keys"]:
            remaining, _ = get_key_info(key)
            bot.reply_to(message, f"⚠️ Key {key} đã tồn tại (còn {remaining} ngày). Ghi đè.", parse_mode="Markdown")
        data["keys"][key] = expire_time
        save_data()
        bot.reply_to(message, f"✅ Đã thêm/cập nhật key {key} hiệu lực {days} ngày.", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Cú pháp: /addkey MAKEY số_ngày")

@bot.message_handler(commands=['removekey'])
def remove_key(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "⛔ Bạn không có quyền.")
    try:
        _, key = message.text.strip().split()
        if key in data["keys"]:
            data["keys"].pop(key)
            data["key_users"].pop(key, None)
            save_data()
            bot.reply_to(message, f"✅ Đã xoá key {key}", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Key không tồn tại.")
    except:
        bot.reply_to(message, "❌ Cú pháp: /removekey MAKEY")

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Chỉ admin gốc mới có quyền.")
    try:
        _, uid = message.text.strip().split()
        uid = int(uid)
        if uid not in data["admins"]:
            data["admins"].append(uid)
            save_data()
            bot.reply_to(message, f"✅ Đã thêm admin {uid}", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ Người này đã là admin.")
    except:
        bot.reply_to(message, "❌ Cú pháp: /addadmin user_id")

@bot.message_handler(commands=['resetkey'])
def reset_key(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "⛔ Bạn không có quyền.")
    try:
        _, uid = message.text.strip().split()
        key = data["user_keys"].pop(uid, None)
        if key:
            if data["key_users"].get(key) == uid:
                data["key_users"].pop(key, None)
            save_data()
            bot.reply_to(message, f"✅ Đã xoá key khỏi user {uid}", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ User này chưa nhập key.")
    except:
        bot.reply_to(message, "❌ Cú pháp: /resetkey user_id")

@bot.message_handler(commands=['nhapkey'])
def nhap_key(message):
    try:
        _, key = message.text.strip().split()
        uid = str(message.from_user.id)

        if key not in data["keys"]:  
            return bot.reply_to(message, "❌ Key không tồn tại.")  
        if data["keys"][key] < time.time():  
            return bot.reply_to(message, "⚠️ Key đã hết hạn.")  

        owner = data.get("key_users", {}).get(key)  
        if owner and owner != uid:  
            return bot.reply_to(message, "⛔ Key này đã được sử dụng bởi người khác.")  

        data["user_keys"][uid] = key  
        data.setdefault("key_users", {})[key] = uid  
        save_data()  
        bot.reply_to(message, "✅ Key hợp lệ. Bạn có thể dùng /moweb để mở tool.")  
    except:  
        bot.reply_to(message, "❌ Cú pháp: /nhapkey MAKEY")

@bot.message_handler(commands=['moweb'])
def moweb(message):
    uid = str(message.from_user.id)
    key = data["user_keys"].get(uid)
    if not key:
        return bot.reply_to(message, "🔒 Bạn chưa nhập key. Dùng /nhapkey MAKEY")
    if key not in data["keys"] or data["keys"][key] < time.time():
        return bot.reply_to(message, "❌ Key đã hết hạn hoặc không tồn tại.")
    if data["key_users"].get(key) != uid:
        return bot.reply_to(message, "⛔ Key này không thuộc về bạn.")
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚀 Mở Web Tool", web_app=WebAppInfo(url=WEBAPP_URL)))
    bot.send_message(message.chat.id, "✅ Nhấn vào để mở Tool:", reply_markup=markup)

@bot.message_handler(commands=['stats'])
def stats(message):
    uid = str(message.from_user.id)
    key = data["user_keys"].get(uid)
    if not key:
        return bot.reply_to(message, "📊 Bạn chưa từng nhập key.")
    remaining, error = get_key_info(key)
    if error:
        return bot.reply_to(message, error)
    admin_status = "✅" if is_admin(message.from_user.id) else "❌"
    text = (
        f"🆔 User ID: {uid}\n"
        f"🔑 Key: {key}\n"
        f"⏳ Còn lại: {remaining} ngày\n"
        f"🛡️ Admin: {admin_status}"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['info'])
def info(message):
    uid = str(message.from_user.id)
    key = data["user_keys"].get(uid, "Chưa có")
    bot.reply_to(message, f"🆔 UID của bạn: {uid}\n🔑 Key đã nhập: {key}", parse_mode="Markdown")

@bot.message_handler(commands=['list'])
def list_users(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "⛔ Bạn không có quyền.")
    text = "📋 Danh sách người dùng đã nhập key:\n\n"
    count = 0
    for uid, key in data["user_keys"].items():
        remaining, error = get_key_info(key)
        days = error if error else f"{remaining} ngày"
        text += f"👤 {uid} | 🔑 {key} | ⏳ {days}\n"
        count += 1
    if count == 0:
        text = "📭 Chưa có ai nhập key."
    bot.reply_to(message, text, parse_mode="Markdown")

# ====== RUN BOT ======
if __name__ == '__main__':
    print("🤖 Bot đang hoạt động...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot stopped with error: {e}")
        time.sleep(5)
        # Try to restart
        bot.infinity_polling()
