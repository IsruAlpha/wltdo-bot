import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters,
    MessageHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Get token from environment variable
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_TOKEN found in environment variables")

# Webhook settings (for production)
PORT = int(os.environ.get("PORT", 8443))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! I'm a bot that tracks when users leave groups. "
        "Add me to a group and I'll message users who leave."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "Add me to a group and I'll automatically message users who leave."
    )

async def handle_member_left(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle members leaving the chat."""
    if update.message and update.message.left_chat_member:
        left_user = update.message.left_chat_member
        chat = update.effective_chat
        
        # Don't message if the bot itself was removed
        if left_user.id == context.bot.id:
            logger.info(f"Bot was removed from {chat.title} ({chat.id})")
            return
        
        # Log the departure
        logger.info(
            f"User {left_user.full_name} (ID: {left_user.id}) left "
            f"group {chat.title} (ID: {chat.id}) at {datetime.now()}"
        )
        
        try:
            # Try to send a direct message to the user who left
            await context.bot.send_message(
                chat_id=left_user.id,
                text=f"Hi {left_user.first_name}, we noticed you left {chat.title}. "
                     f"We hope you enjoyed your time in the group! "
                     f"If you have any feedback, please let us know."
            )
            logger.info(f"Sent farewell message to {left_user.full_name} ({left_user.id})")
        except Exception as e:
            # This can happen if the user has blocked the bot or never interacted with it
            logger.error(f"Could not send message to {left_user.full_name}: {e}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add handler for members leaving chat
    application.add_handler(
        MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_member_left)
    )

    # Start the Bot
    if WEBHOOK_URL:
        # Use webhooks in production
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
        logger.info(f"Bot started with webhook on port {PORT}")
    else:
        # Use polling for development
        application.run_polling()
        logger.info("Bot started with polling")

if __name__ == "__main__":
    main()
