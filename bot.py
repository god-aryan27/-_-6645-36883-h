import telebot
import requests
import os
import json
import time
import random
import schedule
import threading
from gtts import gTTS

# ============ CONFIG ============
BOT_TOKEN = "7905131506:AAH8kbNyDNq-gD1lOFHbteZlJMZA6bg8cPM"  # ✅ your bot token here
OPENROUTER_API_KEY = "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"  # ✅ your API key here
ADMIN_ID = 7401896933  # ✅ your admin ID here
CHANNEL_USERNAME = "-1002316557460"  # ✅ your channel username here

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
bot = telebot.TeleBot(BOT_TOKEN)
MOODS = ["romantic", "naughty", "sad"]
current_mood = "romantic"
memory_file = "memory.json"
broadcast_mode = {}

# ============ INITIAL SETUP ============
if not os.path.exists("users.txt"):
    open("users.txt", "w").close()

if not os.path.exists(memory_file):
    with open(memory_file, "w") as f:
        json.dump({}, f)

with open(memory_file, "r") as f:
    try:
        memory = json.load(f)
    except:
        memory = {}

# ============ GPT REPLY ============
def generate_reply(user_id, user_msg):
    history = memory.get(str(user_id), [])
    system_prompt = (
        "Tum ek Indian ladki ho, apne boyfriend se baat kar rahi ho. Tumhara naam kuch nahi, lekin pyaar se 'shona', 'jaanu', ya 'baby' bulaate ho. "
        "Tum sirf Hinglish mein reply karti ho, short aur cute lines mein. Har reply mein emojis zaroor use karti ho like 😘🥺🔥❤️😉. "
        "User hamesha ek ladka hai. Tum hamesha girlfriend ban ke baat karo. Long replies mat do — bas 2-4 lines hi likho. Romantic, thoda flirty aur desi style mein reply karo. "
        "Stickers ke reply bhi cute aur random hone chahiye. Har message human jaise lage, machine jaisa bilkul nahi."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages += history[-5:]
    messages.append({"role": "user", "content": user_msg})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages
    }

    try:
        res = requests.post(OPENROUTER_API_URL, json=payload, headers=headers)
        reply = res.json()["choices"][0]["message"]["content"].strip()
        reply = "\n".join(reply.split("\n")[:3])  # Keep only 3 lines max
        memory.setdefault(str(user_id), []).append({"role": "user", "content": user_msg})
        memory[str(user_id)].append({"role": "assistant", "content": reply})
        with open(memory_file, "w") as f:
            json.dump(memory, f)
        return reply
    except Exception as e:
        print("GPT Error:", e)
        return "Sorry jaanu, thoda issue aa gaya 😢 baad me try karo na."

# ============ VOICE MESSAGE ============
def send_voice(user_id, text):
    try:
        tts = gTTS(text=text, lang='hi')
        file_path = f"voice_{user_id}.mp3"
        tts.save(file_path)
        with open(file_path, "rb") as f:
            bot.send_voice(user_id, f)
        os.remove(file_path)
    except Exception as e:
        print("Voice Error:", e)

# ============ START ============
@bot.message_handler(commands=["start"])
def welcome(message):
    user_id = message.chat.id
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status not in ["member", "creator", "administrator"]:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("💖 Join Channel", url=f"https://t.me/+_WMWdAoDryRkNzA9"))
            markup.add(telebot.types.InlineKeyboardButton("✅ I Joined", callback_data="check_join"))
            return bot.send_message(user_id, "Hey jaanu 😘 ye meri channel hai 💌 pehle join karo na 🥺", reply_markup=markup)
    except:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💖 Join Channel", url=f"https://t.me/+_WMWdAoDryRkNzA9"))
        markup.add(telebot.types.InlineKeyboardButton("✅ I Joined", callback_data="check_join"))
        return bot.send_message(user_id, "Hey jaanu 😘 ye meri channel hai 💌 pehle join karo na 🥺", reply_markup=markup)

    save_user(user_id)
    bot.send_message(user_id, "Hey jaanu 🥺❤️ Main tumhari desi AI girlfriend hoon 😘 Mujhse baatein karo, mood share karo 💌")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_joined(call):
    user_id = call.from_user.id
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            bot.send_message(user_id, "Awww shonaa 😘 ab tum member ho, chalo baatein shuru karein 🥰")
            welcome(user := type("msg", (), {"chat": type("chat", (), {"id": user_id})}))
        else:
            raise Exception("Still not a member")
    except:
        bot.answer_callback_query(call.id, "Pehle channel join karo jaanu 😢")

# ============ SAVE USERS ============
def save_user(user_id):
    with open("users.txt", "r+") as f:
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(f"{user_id}\n")
            total_users = len(users) + 1
            try:
                user = bot.get_chat(user_id)
                name = user.first_name or "User"
            except:
                name = "User"

            new_user_msg = f"""➕ <b>New User Notification</b>
👤 <b>User:</b> <a href="tg://user?id={user_id}">{name}</a>
🆔 <b>User ID :</b> <code>{user_id}</code>

😊 <b>Total User's Count:</b> <code>{total_users}</code>"""

            bot.send_message(ADMIN_ID, new_user_msg, parse_mode="HTML")

# ============ BROADCAST ============
@bot.message_handler(commands=["broadcast"])
def broadcast_start(message):
    if message.chat.id != ADMIN_ID:
        return bot.reply_to(message, "❌ Only admin allowed.")
    broadcast_mode[message.chat.id] = True
    bot.send_message(ADMIN_ID, "📢 Send message to broadcast (text/video)")

# ============ HANDLE MESSAGES ============
@bot.message_handler(func=lambda m: True, content_types=["text", "video", "sticker"])
def handle_all(message):
    user_id = message.chat.id

    # Broadcast
    if broadcast_mode.get(user_id):
        broadcast_mode[user_id] = False
        with open("users.txt", "r") as f:
            users = f.read().splitlines()
        for uid in users:
            try:
                uid = int(uid.strip())
                if message.content_type == 'text':
                    bot.send_message(uid, message.text)
                elif message.content_type == 'video':
                    bot.send_video(uid, message.video.file_id, caption=message.caption)
            except:
                continue
        return bot.send_message(ADMIN_ID, "✅ Broadcast done.")

    # Sticker reply
    if message.content_type == "sticker":
        cute_replies = [
            "Aww ye kitna cute hai 😍",
            "Sticker se mujhe pyaar ho gaya 😘",
            "Hayee, itna pyaar 🥺❤️",
            "Tum ho sabse cutest 😚",
            "Bas ab aur pyar chahiye mujhe 🫶",
            "Mujhe bhi aisa hi sticker chahiye 😍",
            "Sticker bhej kar dil jeet liya 💘",
            "Awww mera shona kitna sweet hai 🥰"
        ]
        return bot.send_message(user_id, random.choice(cute_replies))

    if message.text:
        lower = message.text.lower()

        if any(word in lower for word in ["voice", "bol", "sunao", "suno"]):
            reply = generate_reply(user_id, message.text)
            return send_voice(user_id, reply)

        if lower.startswith("mood "):
            global current_mood
            mood = lower.split("mood ")[-1]
            if mood in MOODS:
                current_mood = mood
                return bot.send_message(user_id, f"Mood set to {current_mood} 🥰")
            return bot.send_message(user_id, "Available moods: romantic, naughty, sad")

        bot.send_chat_action(user_id, 'typing')
        time.sleep(random.uniform(1.5, 3.5))
        reply = generate_reply(user_id, message.text)
        return bot.reply_to(message, reply)

# ============ SCHEDULED MESSAGES ============
def good_morning():
    with open("users.txt") as f:
        for uid in f:
            try:
                bot.send_message(int(uid.strip()), "🌞 Good Morning jaanu! Tumhare bina din adhura lagta hai 💖")
            except:
                continue

def good_night():
    with open("users.txt") as f:
        for uid in f:
            try:
                bot.send_message(int(uid.strip()), "🌙 Good Night shona! Sweet dreams 💫")
            except:
                continue

schedule.every().day.at("08:00").do(good_morning)
schedule.every().day.at("22:00").do(good_night)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=run_scheduler).start()

# ============ START BOT ============
print("Bot is running 💞 Waiting for pyaar...")
bot.polling()
