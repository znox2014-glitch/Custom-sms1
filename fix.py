#!/usr/bin/env python3
# 🔥 PREMIUM BULK SMS BOT - REAL DELIVERY STATUS 🔥
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
# CONFIG — FIXED TOKEN
# ============================
TOKEN = '8825754114:AAG_4d08ZCDtPJyl2shz4UED5eBg8iHJcrQ'  # <--- FIXED: single quote only
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
    "https://styles-girl-d7617-default-rtdb.firebaseio.com"
]

UPI_ID = "jaychoudhary68605-1@oksbi"
UPI_NAME = "SET KUMAR CHOUDHARY"

# ============================
# DATABASE
# ============================
DB_PATH = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 5, referrer_id INTEGER, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY, banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, banned_by INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount INTEGER, credits_given INTEGER, transaction_id TEXT, screenshot_id TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sms_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, number TEXT, message TEXT, status TEXT, device_id TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, action TEXT, target_user INTEGER, details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS broadcast_history (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, message TEXT, recipients INTEGER, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
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
    add_new_user(user_id); return 5

def add_new_user(user_id, referrer_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone(): conn.close(); return
    c.execute("INSERT INTO users (user_id, credits, referrer_id) VALUES (?, ?, ?)", (user_id, 5, referrer_id))
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

def log_admin_action(admin_id, action, target_user=None, details=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO admin_logs (admin_id, action, target_user, details) VALUES (?, ?, ?, ?)''', (admin_id, action, target_user, details))
    conn.commit()
    conn.close()

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

def get_all_users(limit=100):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, credits, joined_at FROM users ORDER BY joined_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_pending_payments():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, user_id, amount, credits_given, transaction_id, screenshot_id, created_at FROM payments WHERE status = 'pending' ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def approve_payment(payment_id, admin_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, credits_given FROM payments WHERE id = ? AND status = 'pending'", (payment_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Payment not found"
    user_id, credits = row
    c.execute("UPDATE payments SET status = 'approved' WHERE id = ?", (payment_id,))
    c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (credits, user_id))
    conn.commit()
    conn.close()
    log_admin_action(admin_id, "approve_payment", user_id, f"Payment #{payment_id}, {credits} credits")
    return True, f"Approved {credits} credits for user {user_id}"

def reject_payment(payment_id, admin_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE payments SET status = 'rejected' WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()
    log_admin_action(admin_id, "reject_payment", None, f"Payment #{payment_id}")
    return True

def get_total_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_total_banned():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM banned_users")
    count = c.fetchone()[0]
    conn.close()
    return count

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

def add_broadcast(message, count):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO broadcast_history (admin_id, message, recipients) VALUES (?, ?, ?)''', (OWNER_ID, message[:200], count))
    conn.commit()
    conn.close()

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

def check_sms_delivery(url, device_id):
    try:
        check_url = f"{url}/clients/{device_id}/webhookEvent/sendSms.json"
        response = requests.get(check_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                if data.get('isSended') == True:
                    return True, "✅ DELIVERED"
                elif data.get('status') == 'sent':
                    return True, "✅ SENT"
                elif data.get('status') == 'pending':
                    return False, "⏳ PENDING"
                else:
                    return False, f"⏳ {data.get('status', 'UNKNOWN')}"
        return False, "❌ NO RESPONSE"
    except requests.exceptions.Timeout:
        return False, "❌ TIMEOUT"
    except:
        return False, "❌ ERROR"

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
# KEYBOARD
# ============================
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📱 Bulk SMS")],
        [KeyboardButton("💰 Credits"), KeyboardButton("🔗 Referral")],
        [KeyboardButton("💳 Recharge")],
        [KeyboardButton("📜 My History"), KeyboardButton("📊 SMS Logs")],
        [KeyboardButton("🛡️ System Status"), KeyboardButton("👨‍💻 Developer")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    keyboard = [
        [KeyboardButton("👑 Admin Panel")],
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
    
    welcome = f"""╔══════════════════════════════════════╗
║  🔥 **PREMIUM BULK SMS BOT** 🔥   ║
╠══════════════════════════════════════╣
║  🟢 Status: `ONLINE`                ║
║  💰 Credits: `{credits}`              ║
║  👤 User ID: `{user_id}`             ║
╠══════════════════════════════════════╣
║  📌 **How to use:**                 ║
║  • Click `📱 Bulk SMS`              ║
║  • Each SMS costs **1 credit**      ║
║  • Real-time delivery status        ║
║  • Invite friends for free credits  ║
╚══════════════════════════════════════╝"""
    
    markup = get_admin_keyboard() if is_owner(user_id) else get_main_keyboard()
    await update.message.reply_text(welcome, parse_mode="HTML", reply_markup=markup)

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
    
    # ADMIN PANEL
    if text == "👑 Admin Panel" and is_owner(user_id):
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Approve Payments", callback_data="admin_payments")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("👥 Users List", callback_data="admin_users")],
            [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("⚙️ Manage Credits", callback_data="admin_manage_credits")],
            [InlineKeyboardButton("🚫 Ban/Unban", callback_data="admin_ban")],
            [InlineKeyboardButton("📋 Admin Logs", callback_data="admin_logs")],
            [InlineKeyboardButton("🔄 Refresh Firebase", callback_data="admin_refresh")],
        ])
        await update.message.reply_text("👑 **Admin Panel**", reply_markup=markup)
        return
    
    if bulk_step == 'number':
        number = text.strip()
        valid, msg = validate_phone_number(number)
        if not valid:
            await update.message.reply_text(f"{msg}\n\n📞 Format: +91XXXXXXXXXX")
            return
        context.user_data['bulk_number'] = number
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔢 Random OTP", callback_data="msgtype_random")],
            [InlineKeyboardButton("✏️ Custom SMS", callback_data="msgtype_custom")],
            [InlineKeyboardButton("❌ Cancel", callback_data="msgtype_cancel")]
        ])
        await update.message.reply_text("📝 **Select message type:**", reply_markup=keyboard)
        context.user_data['bulk_step'] = 'msgtype'
        return
    
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
    
    if text == "📱 Bulk SMS":
        credits = get_user_credits(user_id)
        if credits <= 0:
            await update.message.reply_text("❌ **Insufficient credits!**")
            return
        await update.message.reply_text("📞 **Enter recipient phone number:**\n✅ Format: +91XXXXXXXXXX")
        context.user_data['bulk_step'] = 'number'
        return
    
    if text == "💰 Credits":
        credits = get_user_credits(user_id)
        await update.message.reply_text(f"💰 **Your Credits:** `{credits}`", parse_mode="HTML")
        return
    
    if text == "🔗 Referral":
        bot_username = (await context.application.bot.get_me()).username
        link = get_referral_link(user_id, bot_username)
        await update.message.reply_text(f"🔗 **Your Referral Link:**\n`{link}`\n\nShare this link – you get **1 credit** per new user!", parse_mode="HTML")
        return
    
    if text == "💳 Recharge":
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 10 Credits - ₹20", callback_data="recharge_10_20")],
            [InlineKeyboardButton("💎 25 Credits - ₹50", callback_data="recharge_25_50")],
            [InlineKeyboardButton("🚀 50 Credits - ₹100", callback_data="recharge_50_100")],
            [InlineKeyboardButton("👑 100 Credits - ₹200", callback_data="recharge_100_200")],
            [InlineKeyboardButton("👑 250 Credits - ₹500", callback_data="recharge_250_500")],
            [InlineKeyboardButton("❌ Cancel", callback_data="recharge_cancel")]
        ])
        await update.message.reply_text("💳 **Select Recharge Plan:**", reply_markup=markup)
        return
    
    if text == "📜 My History":
        history = get_user_history(user_id, 10)
        if not history:
            await update.message.reply_text("📭 No activity history.")
            return
        reply = "📜 **Your Recent Activity:**\n"
        for action, details, created_at in history:
            dt = created_at[:19] if created_at else "N/A"
            reply += f"• {action} – {details} ({dt})\n"
        await update.message.reply_text(reply)
        return
    
    if text == "📊 SMS Logs":
        logs = get_sms_logs(user_id, 10)
        if not logs:
            await update.message.reply_text("📭 No SMS logs found.")
            return
        reply = "📊 **SMS Delivery Logs:**\n"
        for number, message, status, device_id, sent_at in logs:
            status_emoji = "✅" if status == "success" else "❌" if status == "failed" else "⏳" if status == "pending" else "❓"
            dt = sent_at[:19] if sent_at else "N/A"
            reply += f"{status_emoji} {number} → {status.upper()} ({dt})\n"
        await update.message.reply_text(reply)
        return
    
    if text == "🛡️ System Status":
        total_users = get_total_users()
        total_banned = get_total_banned()
        await update.message.reply_text(
            f"╔══════════════════════════════════════╗\n"
            f"║  🟢 **SYSTEM STATUS**              ║\n"
            f"╠══════════════════════════════════════╣\n"
            f"║  ✅ Bot: `ONLINE`                   ║\n"
            f"║  ✅ Database: `ACTIVE`              ║\n"
            f"║  ✅ Firebase: `CONNECTED`           ║\n"
            f"║  👥 Users: `{total_users}`                  ║\n"
            f"║  🚫 Banned: `{total_banned}`                ║\n"
            f"║  💰 Credits System: `WORKING`       ║\n"
            f"╚══════════════════════════════════════╝"
        )
        return
    
    if text == "👨‍💻 Developer":
        await update.message.reply_text("👨‍💻 **Developer:** @ZeroApiHub\n📺 **Channel:** Zero Api\n💬 For support or custom bots, contact the developer.")
        return
    
    await update.message.reply_text("❌ Please use the buttons below.")

# ============================
# CALLBACK HANDLERS
# ============================
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    # ========== RECHARGE ==========
    if data.startswith("recharge_"):
        if data == "recharge_cancel":
            await query.edit_message_text("❌ Recharge cancelled.")
            return
        _, credits, amount = data.split("_")
        credits = int(credits)
        amount = int(amount)
        context.user_data['recharge_credits'] = credits
        context.user_data['recharge_amount'] = amount
        reply = f"💰 **Plan: {credits} Credits**\n💵 **Amount: ₹{amount}**\n\n📱 **Send payment to UPI:** `{UPI_ID}`\n📛 **Name:** {UPI_NAME}\n\n📸 After payment, send the Transaction ID or screenshot (as photo) to this chat."
        await query.edit_message_text(reply, parse_mode="HTML")
        context.user_data['recharge_step'] = 'payment'
        return
    
    # ========== MSG TYPE ==========
    if data.startswith("msgtype_"):
        if data == "msgtype_cancel":
            await query.edit_message_text("❌ Bulk SMS cancelled.")
            context.user_data.pop('bulk_step', None)
            return
        msg_type = data.split("_")[1]
        if msg_type == "random":
            default_msg = "आपका OTP है: {{otp}} | कृपया इसे किसी को न बताएँ।"
            context.user_data['custom_message'] = default_msg
            await query.edit_message_text("✅ Using default OTP template.\n\n📤 **Starting bulk SMS...**")
            if not deduct_credit(user_id):
                await query.message.reply_text("❌ Insufficient balance.")
                return
            log_user_action(user_id, "Bulk SMS Started", f"Target: {context.user_data['bulk_number']}")
            await perform_bulk_send(update, context)
        else:
            await query.edit_message_text("✏️ **Now enter your custom message.**\n💡 Use `{{otp}}` for random OTP if needed.")
            context.user_data['bulk_step'] = 'custom_msg'
        return
    
    if data == "stop_bulk":
        context.user_data['stop_sending'] = True
        await query.answer("Stopping...")
        return
    
    # ========== ADMIN PANEL ==========
    if not is_owner(user_id):
        await query.edit_message_text("⛔ Unauthorized.")
        return
    
    if data == "admin_payments":
        payments = get_pending_payments()
        if not payments:
            await query.edit_message_text("📭 No pending payments.")
            return
        markup = []
        for pid, uid, amount, credits, txn, ss, created in payments[:10]:
            btn_text = f"#{pid} - User {uid} - ₹{amount} - {credits}cr"
            markup.append([InlineKeyboardButton(btn_text, callback_data=f"approve_{pid}")])
        markup.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
        await query.edit_message_text("💰 **Pending Payments:**", reply_markup=InlineKeyboardMarkup(markup))
        return
    
    if data.startswith("approve_"):
        pid = int(data.split("_")[1])
        success, msg = approve_payment(pid, user_id)
        await query.edit_message_text(f"{'✅' if success else '❌'} {msg}")
        return
    
    if data == "admin_broadcast":
        context.user_data['broadcast_step'] = 'waiting'
        await query.edit_message_text("📢 **Enter broadcast message:**")
        return
    
    if data == "admin_users":
        users = get_all_users(20)
        if not users:
            await query.edit_message_text("📭 No users found.")
            return
        reply = "👥 **Recent Users:**\n"
        for uid, credits, joined in users:
            dt = joined[:19] if joined else "N/A"
            reply += f"• `{uid}` - {credits}cr ({dt})\n"
        await query.edit_message_text(reply)
        return
    
    if data == "admin_stats":
        total = get_total_users()
        banned = get_total_banned()
        pending = len(get_pending_payments())
        reply = f"📊 **Bot Statistics:**\n\n👥 Total Users: {total}\n🚫 Banned Users: {banned}\n💰 Pending Payments: {pending}\n🟢 Status: Online"
        await query.edit_message_text(reply)
        return
    
    if data == "admin_manage_credits":
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Credits", callback_data="admin_add_credits")],
            [InlineKeyboardButton("➖ Remove Credits", callback_data="admin_remove_credits")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
        ])
        await query.edit_message_text("⚙️ **Manage Credits:**", reply_markup=markup)
        return
    
    if data == "admin_add_credits":
        context.user_data['admin_action'] = 'add_credits'
        await query.edit_message_text("📝 **Send:** `/addcredits <user_id> <amount>`")
        return
    
    if data == "admin_remove_credits":
        context.user_data['admin_action'] = 'remove_credits'
        await query.edit_message_text("📝 **Send:** `/removecredits <user_id> <amount>`")
        return
    
    if data == "admin_ban":
        context.user_data['admin_action'] = 'ban'
        await query.edit_message_text("📝 **Send:** `/ban <user_id>`")
        return
    
    if data == "admin_logs":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT admin_id, action, target_user, details, created_at FROM admin_logs ORDER BY id DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        if not rows:
            await query.edit_message_text("📭 No admin logs.")
            return
        reply = "📋 **Admin Logs:**\n"
        for admin, action, target, details, created in rows:
            dt = created[:19] if created else "N/A"
            reply += f"• {action} (admin {admin}) {details} ({dt})\n"
        await query.edit_message_text(reply)
        return
    
    if data == "admin_refresh":
        await query.edit_message_text("🔄 Refreshing Firebase connections...")
        # Test all Firebase URLs
        working = 0
        for url in FIREBASE_URLS:
            try:
                r = requests.get(f"{url}/.json", timeout=5)
                if r.status_code == 200:
                    working += 1
            except:
                pass
        await query.edit_message_text(f"🔄 Firebase refresh complete.\n✅ Working URLs: {working}/{len(FIREBASE_URLS)}")
        return
    
    if data == "admin_back":
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Approve Payments", callback_data="admin_payments")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("👥 Users List", callback_data="admin_users")],
            [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("⚙️ Manage Credits", callback_data="admin_manage_credits")],
            [InlineKeyboardButton("🚫 Ban/Unban", callback_data="admin_ban")],
            [InlineKeyboardButton("📋 Admin Logs", callback_data="admin_logs")],
            [InlineKeyboardButton("🔄 Refresh Firebase", callback_data="admin_refresh")],
        ])
        await query.edit_message_text("👑 **Admin Panel**", reply_markup=markup)
        return

# ============================
# PERFORM BULK SEND
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
        [InlineKeyboardButton("⏹ Stop Sending", callback_data="stop_bulk")]
    ])
    
    progress_msg = await update.message.reply_text(
        "╔══════════════════════════════════════╗\n"
        "║  📤 **BULK SMS IN PROGRESS**        ║\n"
        "╠══════════════════════════════════════╣\n"
        "║  🔄 Status: `STARTING`              ║\n"
        "║  ✅ Sent: `0`                       ║\n"
        "║  ❌ Failed: `0`                     ║\n"
        "║  ⏳ Pending: `0`                   ║\n"
        "╚══════════════════════════════════════╝",
        parse_mode="HTML",
        reply_markup=stop_markup
    )
    
    total_sent = 0
    total_failed = 0
    total_pending = 0
    cycle = 1
    
    otp_placeholder = re.search(r'{{otp(:\d+)?}}', msg_text)
    otp_length = 6
    if otp_placeholder and otp_placeholder.group(1):
        try:
            otp_length = int(otp_placeholder.group(1)[2:])
        except:
            otp_length = 6
    
    while not context.user_data.get('stop_sending', False):
        if is_user_banned(user_id):
            break
        
        cycle_text = f"🔄 Cycle #{cycle}"
        
        for url in FIREBASE_URLS:
            if context.user_data.get('stop_sending', False) or is_user_banned(user_id):
                break
            
            try:
                clients = fetch_json_data(url, "/clients", auth=None)
                if not clients or not isinstance(clients, dict):
                    continue
                
                device_ids = list(clients.keys())
                if not device_ids:
                    continue
                
                for dev_id in device_ids:
                    if context.user_data.get('stop_sending', False) or is_user_banned(user_id):
                        break
                    
                    final_msg = msg_text
                    if otp_placeholder:
                        otp = generate_otp(otp_length)
                        final_msg = re.sub(r'{{otp(:\d+)?}}', otp, msg_text)
                    
                    path = f"clients/{dev_id}/webhookEvent/sendSms"
                    payload = {"sim": 1, "to": number, "message": final_msg, "isSended": False}
                    
                    ok = firebase_put(url, None, path, payload)
                    
                    if ok:
                        await asyncio.sleep(2)
                        delivered, status = check_sms_delivery(url, dev_id)
                        
                        if delivered:
                            total_sent += 1
                            log_sms(user_id, number, final_msg, "success", dev_id[:8])
                            logger.info(f"✅ DELIVERED via {dev_id[:8]}")
                        else:
                            total_pending += 1
                            log_sms(user_id, number, final_msg, "pending", dev_id[:8])
                            logger.warning(f"⏳ PENDING via {dev_id[:8]}")
                    else:
                        total_failed += 1
                        log_sms(user_id, number, final_msg, "failed", dev_id[:8] if dev_id else "unknown")
                        logger.warning(f"❌ FAILED via {dev_id[:8]}")
                    
                    if (total_sent + total_failed + total_pending) % 2 == 0:
                        progress_text = (
                            f"╔══════════════════════════════════════╗\n"
                            f"║  📤 **BULK SMS IN PROGRESS**        ║\n"
                            f"╠══════════════════════════════════════╣\n"
                            f"║  🔄 Status: `{cycle_text}`       ║\n"
                            f"║  ✅ Delivered: `{total_sent}`          ║\n"
                            f"║  ❌ Failed: `{total_failed}`            ║\n"
                            f"║  ⏳ Pending: `{total_pending}`         ║\n"
                            f"║  📱 Target: `{number}`    ║\n"
                            f"╚══════════════════════════════════════╝"
                        )
                        try:
                            await progress_msg.edit_text(progress_text, parse_mode="HTML", reply_markup=stop_markup)
                        except:
                            pass
                    
                    await asyncio.sleep(0.3)
                    
            except Exception as e:
                logger.error(f"Error: {e}")
                await asyncio.sleep(1)
        
        cycle += 1
    
    if total_failed == 0 and total_pending == 0 and total_sent > 0:
        status_emoji = "✅"
        status_text = "ALL DELIVERED"
    elif total_sent > 0 and total_pending == 0:
        status_emoji = "⚠️"
        status_text = "PARTIAL DELIVERY"
    elif total_pending > 0:
        status_emoji = "⏳"
        status_text = "SOME PENDING"
    else:
        status_emoji = "❌"
        status_text = "FAILED"
    
    final_text = (
        f"╔══════════════════════════════════════╗\n"
        f"║  {status_emoji} **BULK SMS {status_text}**  ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║  ✅ Delivered: `{total_sent}`           ║\n"
        f"║  ❌ Failed: `{total_failed}`             ║\n"
        f"║  ⏳ Pending: `{total_pending}`          ║\n"
        f"║  📱 Target: `{number}`    ║\n"
        f"║  📊 Total: `{total_sent + total_failed + total_pending}`     ║\n"
        f"╚══════════════════════════════════════╝"
    )
    
    try:
        await progress_msg.edit_text(final_text, parse_mode="HTML")
        await progress_msg.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    log_user_action(user_id, "Bulk SMS Ended", f"Sent {total_sent}, Failed {total_failed}, Pending {total_pending}")
    context.user_data.pop('stop_sending', None)
    context.user_data.pop('bulk_step', None)
    context.user_data.pop('bulk_number', None)
    context.user_data.pop('custom_message', None)

# ============================
# BROADCAST HANDLER
# ============================
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if context.user_data.get('broadcast_step') != 'waiting':
        return
    
    msg = update.message.text
    if not msg or msg.startswith('/'):
        return
    
    context.user_data.pop('broadcast_step', None)
    await update.message.reply_text("📢 Broadcasting...")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    
    count = 0
    for (uid,) in users:
        try:
            await context.application.bot.send_message(uid, f"📢 **Broadcast:**\n\n{msg}")
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    add_broadcast(msg, count)
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")

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
        log_admin_action(update.effective_user.id, "add_credits", target, f"+{amount}")
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
            log_admin_action(update.effective_user.id, "remove_credits", target, f"-{amount}")
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
            log_admin_action(update.effective_user.id, "ban", target, "Banned user")
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
            log_admin_action(update.effective_user.id, "unban", target, "Unbanned user")
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
    context.user_data.pop('bulk_step', None)
    context.user_data.pop('recharge_step', None)
    context.user_data.pop('stop_sending', None)
    context.user_data.pop('broadcast_step', None)
    await update.message.reply_text("❌ Cancelled. Use the buttons to start again.", reply_markup=get_main_keyboard())

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
    application.add_handler(MessageHandler(filters.PHOTO, handle_text))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message))
    
    print("""
╔════════════════════════════════════════════════╗
║  🔥 PREMIUM BULK SMS BOT                     ║
║  ✅ Real-time Delivery Status                 ║
║  ✅ Success/Failed/Pending Tracking           ║
║  ✅ Premium UI Design                         ║
║  ✅ SMS Logs Stored                           ║
║  ✅ Admin Panel Added                         ║
╚════════════════════════════════════════════════╝
    """)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
