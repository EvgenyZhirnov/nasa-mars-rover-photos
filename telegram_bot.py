"""
Telegram bot module for sending Mars Rover animations.
"""
import os
import logging
import telegram
from telegram.ext import Updater, CommandHandler
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# Get Telegram bot token from environment variable
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEFAULT_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_animation_async(chat_id=None):
    """
    Send the latest Mars Rover animation to a Telegram chat.
    
    Args:
        chat_id (str): Telegram chat ID to send the animation to
        
    Returns:
        bool: True if animation was sent successfully, False otherwise
    """
    if not TELEGRAM_TOKEN:
        logger.error("Telegram bot token not set")
        return False
        
    if not chat_id and not DEFAULT_CHAT_ID:
        logger.error("No chat ID provided or set in environment variables")
        return False
        
    chat_id = chat_id or DEFAULT_CHAT_ID
    animation_path = "/data/nasa_animation.mp4"
    gif_path = "/data/nasa_animation.gif"
    
    # Check if animation file exists
    if not os.path.exists(animation_path) and not os.path.exists(gif_path):
        logger.error("No animation file found to send")
        return False
        
    file_path = animation_path if os.path.exists(animation_path) else gif_path
    
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logger.info(f"Sending animation to Telegram chat {chat_id}")
        
        caption = f"Mars Rover Daily Animation - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Send file based on type
        if file_path.endswith('.mp4'):
            await bot.send_video(
                chat_id=chat_id,
                video=open(file_path, 'rb'),
                caption=caption,
                supports_streaming=True
            )
        else:
            await bot.send_animation(
                chat_id=chat_id,
                animation=open(file_path, 'rb'),
                caption=caption
            )
            
        logger.info("Animation sent successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error sending animation to Telegram: {e}")
        return False

def send_animation(chat_id=None):
    """
    Synchronous wrapper for sending the animation.
    """
    asyncio.run(send_animation_async(chat_id))

class TelegramBot:
    """Class to manage Telegram bot commands and operations."""
    
    def __init__(self):
        """Initialize the Telegram bot."""
        if not TELEGRAM_TOKEN:
            logger.warning("Telegram bot token not set, bot will not start")
            self.bot = None
            return
            
        try:
            self.updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
            self.dispatcher = self.updater.dispatcher
            
            # Register command handlers
            self.dispatcher.add_handler(CommandHandler("start", self.start_command))
            self.dispatcher.add_handler(CommandHandler("help", self.help_command))
            self.dispatcher.add_handler(CommandHandler("animation", self.animation_command))
            
            logger.info("Telegram bot initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}")
            self.updater = None
    
    def start(self):
        """Start the Telegram bot."""
        if not self.updater:
            logger.warning("Telegram bot not initialized, cannot start")
            return
            
        try:
            self.updater.start_polling()
            logger.info("Telegram bot started successfully")
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
    
    def stop(self):
        """Stop the Telegram bot."""
        if not self.updater:
            return
            
        try:
            self.updater.stop()
            logger.info("Telegram bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
    
    def start_command(self, update, context):
        """Handle /start command."""
        chat_id = update.effective_chat.id
        context.bot.send_message(
            chat_id=chat_id,
            text="Welcome to the Mars Rover Animation Bot! Use /help to see available commands."
        )
        logger.info(f"Start command received from chat {chat_id}")
    
    def help_command(self, update, context):
        """Handle /help command."""
        chat_id = update.effective_chat.id
        help_text = (
            "Mars Rover Animation Bot Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/animation - Get the latest Mars Rover animation"
        )
        context.bot.send_message(chat_id=chat_id, text=help_text)
        logger.info(f"Help command received from chat {chat_id}")
    
    def animation_command(self, update, context):
        """Handle /animation command."""
        chat_id = update.effective_chat.id
        context.bot.send_message(
            chat_id=chat_id,
            text="Fetching the latest Mars Rover animation for you..."
        )
        
        # Send the animation
        success = send_animation(chat_id)
        
        if not success:
            context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, I couldn't find a recent animation to send. Please try again later."
            )
        
        logger.info(f"Animation command received from chat {chat_id}, success: {success}")
