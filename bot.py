#!/usr/bin/env python3
import requests
import json
import time
import uuid
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============================================================
# CONFIG
# ============================================================
BOT_TOKEN = '8395696352:AAGMK0ZZM5lqvV4UO9GafUFzeGAUmTqx7LY'
OWNER_ID = 8864524240
API_URL = 'https://custom-sms-seven.vercel.app'

# ============================================================
# DATA STORAGE
# ============================================================
DATA_FILE = 'data.json'
data = {
    'users': {},
    'total_sms_sent': 0,
    'logs': [],
    'protected_numbers': [],
    'banned_users': [],
    'redeem_codes': [],
    'used_codes': [],
    'active_bombs': {}
}

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

load_data()

# ============================================================
# HELPERS
# ============================================================
def is_banned(chat_id):
    return chat_id in data['banned_users']

def is_protected(number):
    return any(p in number for p in data['protected_numbers'])

def get_user(chat_id):
    if str(chat_id) not in data['users']:
        data['users'][str(chat_id)] = {
            'first_seen': time.time(),
            'username': '',
            'first_name': '',
            'credits': 3,
            'daily_bombs': 0,
            'last_bomb_date': None,
            'plan': 'free',
            'plan_expiry': None,
            'state': None
        }
        save_data()
    return data['users'][str(chat_id)]

def can_bomb(chat_id):
    user = get_user(chat_id)
    today = datetime.now().date().isoformat()

    # Check unlimited plan
    if user['plan'] != 'free' and user['plan_expiry']:
        expiry = datetime.fromisoformat(user['plan_expiry'])
        if expiry > datetime.now():
            return {'allowed': True, 'reason': 'unlimited'}
        else:
            user['plan'] = 'free'
            user['plan_expiry'] = None
            user['credits'] = 3
            user['daily_bombs'] = 0
            save_data()

    # Reset daily bombs
    if user['last_bomb_date'] != today:
        user['daily_bombs'] = 0
        user['last_bomb_date'] = today
        save_data()

    if user['daily_bombs'] >= 3:
        return {'allowed': False, 'reason': 'daily_limit'}

    if user['credits'] <= 0:
        return {'allowed': False, 'reason': 'no_credits'}

    return {'allowed': True}

def use_bomb(chat_id):
    user = get_user(chat_id)
    today = datetime.now().date().isoformat()

    if user['plan'] != 'free':
        if user['last_bomb_date'] != today:
            user['daily_bombs'] = 0
            user['last_bomb_date'] = today
        user['daily_bombs'] += 1
        save_data()
        return True

    if user['last_bomb_date'] != today:
        user['daily_bombs'] = 0
        user['last_bomb_date'] = today
    user['daily_bombs'] += 1
    user['credits'] -= 1
    save_data()
    return True

def generate_redeem_code(credits, max_uses=1, expires_in=7):
    code = uuid.uuid4().hex[:8].upper()
    redeem_code = {
        'code': code,
        'credits': credits,
        'max_uses': max_uses,
        'used_count': 0,
        'created': time.time(),
        'expires': time.time() + (expires_in * 24 * 60 * 60),
        'used_by': []
    }
    data['redeem_codes'].append(redeem_code)
    save_data()
    return code

def redeem_code(chat_id, code):
    for redeem in data['redeem_codes']:
        if redeem['code'] == code:
            if code + '_' + str(chat_id) in data['used_codes']:
                return {'success': False, 'reason': 'already_used'}
            if redeem['used_count'] >= redeem['max_uses']:
                return {'success': False, 'reason': 'max_uses'}
            if time.time() > redeem['expires']:
                return {'success': False, 'reason': 'expired'}
            
            user = get_user(chat_id)
            user['credits'] += redeem['credits']
            redeem['used_count'] += 1
            redeem['used_by'].append(chat_id)
            data['used_codes'].append(code + '_' + str(chat_id))
            save_data()
            return {'success': True, 'credits': redeem['credits']}
    
    return {'success': False, 'reason': 'invalid'}

# ============================================================
# API CALL
# ============================================================
def call_api(number, msg):
    try:
        url = f"{API_URL}/?number={number}&msg={msg}"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {'error': f'HTTP {response.status_code}', 'details': response.text}
    except Exception as e:
        return {'error': str(e)}

# ============================================================
# BOT COMMANDS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    
    if update.effective_user:
        user['username'] = update.effective_user.username or ''
        user['first_name'] = update.effective_user.first_name or ''
        save_data()
    
    if is_banned(chat_id):
        await update.message.reply_text('🚫 You are banned from using this bot.')
        return
    
    if chat_id == OWNER_ID:
        await show_admin_menu(update, context)
    else:
        await show_user_menu(update, context)

async def show_user_menu(update, context):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    today = datetime.now().date().isoformat()
    
    if user['plan'] != 'free' and user['plan_expiry']:
        expiry = datetime.fromisoformat(user['plan_expiry'])
        days_left = (expiry - datetime.now()).days
        credits_display = f"👑 {user['plan'].upper()} ({days_left}d left)"
        plan_info = '♾️ Unlimited Bombs'
    else:
        credits_display = f"🎫 Credits: {user['credits']}"
        daily_left = user['daily_bombs'] if user['last_bomb_date'] == today else 0
        plan_info = f"📊 Daily Bombs Left: {3 - daily_left}/3"
    
    keyboard = [
        [InlineKeyboardButton("💣 Start Bombing", callback_data="start_bomb")],
        [InlineKeyboardButton("🎫 My Credits", callback_data="my_credits")],
        [InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem_code")],
        [InlineKeyboardButton("💰 Buy Credits", callback_data="buy_credits")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    
    await update.message.reply_text(
        f"🔥 *Shakti SMS Bomber*\n\n{credits_display}\n{plan_info}\n\nSelect an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_admin_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("💣 Start Bombing", callback_data="start_bomb")],
        [InlineKeyboardButton("🎫 My Credits", callback_data="my_credits")],
        [InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem_code")],
        [InlineKeyboardButton("💰 Buy Credits", callback_data="buy_credits")],
        [InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    
    await update.message.reply_text(
        "👑 *Shakti SMS Bomber (Admin)*\n\nSelect an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ============================================================
# CALLBACK HANDLERS
# ============================================================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    data_cb = query.data
    
    await query.answer()
    
    if is_banned(chat_id):
        await query.edit_message_text('🚫 You are banned from using this bot.')
        return
    
    user = get_user(chat_id)
    
    # Start Bombing
    if data_cb == 'start_bomb':
        user['state'] = 'waiting_number'
        save_data()
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        await query.edit_message_text(
            "📱 *Enter target phone number*\n\nFormat: 9876543210 (10 digits)\nExample: 9999999999\n\nSend number:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # My Credits
    if data_cb == 'my_credits':
        today = datetime.now().date().isoformat()
        if user['plan'] != 'free' and user['plan_expiry']:
            expiry = datetime.fromisoformat(user['plan_expiry'])
            days_left = (expiry - datetime.now()).days
            response = f"🎫 *Your Credits & Plan*\n\n👑 Plan: {user['plan'].upper()}\n📅 Expires: {expiry.date()} ({days_left}d left)\n♾️ Unlimited bombs"
        else:
            daily_left = user['daily_bombs'] if user['last_bomb_date'] == today else 0
            response = f"🎫 *Your Credits & Plan*\n\n🎫 Credits: {user['credits']}\n📊 Daily Bombs Left: {3 - daily_left}/3\n\n🕐 Last Reset: {user['last_bomb_date'] or 'First time'}"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_menu")]]
        await query.edit_message_text(
            response,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Redeem Code
    if data_cb == 'redeem_code':
        user['state'] = 'waiting_redeem'
        save_data()
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        await query.edit_message_text(
            "🔑 Enter your redeem code:\n(Or send /cancel)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Buy Credits
    if data_cb == 'buy_credits':
        await query.edit_message_text(
            "💳 *Buy Credits & Plans*\n\n*Credit Packs:*\n🎫 10 Credits - ₹50\n🎫 25 Credits - ₹100\n🎫 50 Credits - ₹180\n🎫 100 Credits - ₹300\n\n*Unlimited Plans:*\n👑 7 Days Unlimited - ₹150\n👑 15 Days Unlimited - ₹250\n👑 30 Days Unlimited - ₹400\n\n*Contact Admin for payment and activation.*",
            parse_mode='Markdown'
        )
        return
    
    # Admin Panel
    if data_cb == 'admin_panel':
        if chat_id != OWNER_ID:
            await query.edit_message_text('⛔ Admin only!')
            return
        
        # Get status from API
        status_msg = await query.edit_message_text('⏳ Fetching status...')
        
        try:
            resp = requests.get(f"{API_URL}/?number=+919999999999&msg=ping", timeout=10)
            api_status = resp.json() if resp.status_code == 200 else {'error': 'API down'}
        except:
            api_status = {'error': 'API unreachable'}
        
        devices = api_status.get('devicesUsed', 0) if isinstance(api_status, dict) else 0
        
        response = f"""
👑 *Admin Panel*

📊 *Real-Time Status*

🟢 Online Devices: {devices}

📨 *Total SMS Sent:* {data['total_sms_sent']}
👥 *Total Users:* {len(data['users'])}
🚫 *Banned Users:* {len(data['banned_users'])}
📋 *Protected Numbers:* {len(data['protected_numbers'])}
🎫 *Total Redeem Codes:* {len(data['redeem_codes'])}

*Options:*
"""
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_status")],
            [InlineKeyboardButton("👥 All Users", callback_data="list_users")],
            [InlineKeyboardButton("➕ Add Protected", callback_data="add_protected")],
            [InlineKeyboardButton("🚫 Ban User", callback_data="ban_user")],
            [InlineKeyboardButton("✅ Unban User", callback_data="unban_user")],
            [InlineKeyboardButton("📋 View Logs", callback_data="view_logs")],
            [InlineKeyboardButton("📊 Live Bombing", callback_data="live_bombing")],
            [InlineKeyboardButton("🎫 Generate Code", callback_data="gen_code")],
            [InlineKeyboardButton("📋 Codes List", callback_data="list_codes")],
            [InlineKeyboardButton("🗑️ Clear Logs", callback_data="clear_logs")],
            [InlineKeyboardButton("📊 Full Stats", callback_data="full_stats")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
        ]
        
        await query.edit_message_text(
            response,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Cancel
    if data_cb == 'cancel':
        user['state'] = None
        save_data()
        await query.edit_message_text('❌ Cancelled.')
        if chat_id == OWNER_ID:
            await show_admin_menu(update, context)
        else:
            await show_user_menu(update, context)
        return
    
    # Back to Menu
    if data_cb == 'back_menu':
        if chat_id == OWNER_ID:
            await show_admin_menu(update, context)
        else:
            await show_user_menu(update, context)
        return
    
    # Help
    if data_cb == 'help':
        await query.edit_message_text(
            "🔥 *Shakti SMS Bomber*\n\n*Free Users:*\n- 3 bombs per day (FREE)\n- 1 bomb = 1 credit\n- Redeem codes for extra credits\n\n*Plans:*\n- 7/15/30 days unlimited\n\n*How to use:*\n1. Click 💣 Start Bombing\n2. Enter 10-digit number\n3. Enter message\n4. Watch progress!\n\n*Commands:*\n/start - Main menu",
            parse_mode='Markdown'
        )
        return

# ============================================================
# MESSAGE HANDLER
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if is_banned(chat_id):
        await update.message.reply_text('🚫 You are banned from using this bot.')
        return
    
    user = get_user(chat_id)
    
    # Cancel
    if text.lower() == '/cancel':
        user['state'] = None
        save_data()
        await update.message.reply_text('❌ Cancelled.')
        if chat_id == OWNER_ID:
            await show_admin_menu(update, context)
        else:
            await show_user_menu(update, context)
        return
    
    # Waiting for number
    if user.get('state') == 'waiting_number':
        if not text.isdigit() or len(text) != 10:
            await update.message.reply_text('⚠️ Invalid! Enter 10 digits only.\nExample: 9999999999')
            return
        
        if is_protected(text):
            await update.message.reply_text('🔒 This number is protected! Cannot bomb.')
            return
        
        check = can_bomb(chat_id)
        if not check['allowed']:
            msg = '⛔ Cannot bomb!\n\n'
            if check['reason'] == 'daily_limit':
                msg += '📊 Daily limit (3) reached. Try again tomorrow.'
            elif check['reason'] == 'no_credits':
                msg += '🎫 No credits left! Buy credits or redeem a code.'
            user['state'] = None
            save_data()
            await update.message.reply_text(msg)
            return
        
        user['target_number'] = text
        user['state'] = 'waiting_message'
        save_data()
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        await update.message.reply_text(
            f"📝 *Enter message to send:*\n\nTarget: +91{text}\n\nSend your message:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Waiting for message
    if user.get('state') == 'waiting_message':
        number = user['target_number']
        full_number = f"+91{number}"
        message = text
        
        user['state'] = None
        save_data()
        
        # Call API
        status_msg = await update.message.reply_text(f'⏳ Bombing {full_number} with "{message}"...')
        
        result = call_api(full_number, message)
        
        if 'error' in result:
            await status_msg.edit_text(f'❌ Error: {result["error"]}')
            return
        
        # Use bomb (deduct credit/daily)
        use_bomb(chat_id)
        
        # Update total
        data['total_sms_sent'] += result.get('smsSent', 0)
        data['logs'].append({
            'timestamp': time.time(),
            'user': chat_id,
            'number': full_number,
            'message': message,
            'devices': result.get('devicesUsed', 0),
            'sent': result.get('smsSent', 0)
        })
        save_data()
        
        response = f"""
✅ *Bombing Complete!*

📱 Target: {full_number}
💬 Message: {message}
📡 Devices Used: {result.get('devicesUsed', 0)}
📨 SMS Sent: {result.get('smsSent', 0)}
"""
        
        # Remaining credits
        updated_user = get_user(chat_id)
        today = datetime.now().date().isoformat()
        if updated_user['plan'] != 'free':
            expiry = datetime.fromisoformat(updated_user['plan_expiry'])
            days_left = (expiry - datetime.now()).days
            response += f"\n👑 {updated_user['plan'].upper()} ({days_left}d remaining)"
        else:
            daily_left = updated_user['daily_bombs'] if updated_user['last_bomb_date'] == today else 0
            response += f"\n📊 Remaining daily bombs: {3 - daily_left}\n🎫 Credits left: {updated_user['credits']}"
        
        await status_msg.edit_text(response, parse_mode='Markdown')
        
        if chat_id == OWNER_ID:
            await show_admin_menu(update, context)
        else:
            await show_user_menu(update, context)
        return
    
    # Waiting for redeem
    if user.get('state') == 'waiting_redeem':
        result = redeem_code(chat_id, text.upper())
        user['state'] = None
        save_data()
        
        if result['success']:
            await update.message.reply_text(f"✅ Code redeemed! +{result['credits']} credits added.")
        else:
            messages = {
                'invalid': '❌ Invalid code!',
                'already_used': '❌ Code already used by you!',
                'max_uses': '❌ Code has reached maximum uses!',
                'expired': '❌ Code has expired!'
            }
            await update.message.reply_text(messages.get(result['reason'], '❌ Failed to redeem.'))
        
        if chat_id == OWNER_ID:
            await show_admin_menu(update, context)
        else:
            await show_user_menu(update, context)
        return

# ============================================================
# MAIN
# ============================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🔥 Shakti Python Bot Active!")
    print("✅ Bot is running...")
    
    app.run_polling()

if __name__ == '__main__':
    main()
