import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set!")

# Pollinations.ai API endpoint for image generation
POLLINATIONS_API = "https://image.pollinations.ai/prompt/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    welcome_message = (
        "🎨 Welcome to Bimgs AI Bot!\n\n"
        "I can generate images from text descriptions using AI.\n\n"
        "How to use:\n"
        "• Send any text message to generate an image\n"
        "• Or use /generate <your description>\n\n"
        "Example: /generate a beautiful sunset over mountains\n"
        "Or just type: a cute cat wearing a hat"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help information."""
    help_text = (
        "📖 Help Guide\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/generate <prompt> - Generate an image from text\n\n"
        "You can also just type any description directly!\n\n"
        "Tips for better images:\n"
        "• Be specific and descriptive\n"
        "• Mention style (photorealistic, cartoon, oil painting)\n"
        "• Include details about lighting and colors"
    )
    await update.message.reply_text(help_text)

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate an image from the user's prompt."""
    # Get the prompt from the command or the message text
    if context.args:
        # /generate command with arguments
        prompt = ' '.join(context.args)
    else:
        # Direct message without command
        prompt = update.message.text

    if not prompt or len(prompt.strip()) < 3:
        await update.message.reply_text("Please provide a longer description (at least 3 characters).")
        return

    # Send a "processing" message
    status_msg = await update.message.reply_text(f"🎨 Generating image for: \"{prompt}\"...\n\n⏳ This may take 10-30 seconds.")

    try:
        # Build the Pollinations API URL with the prompt
        # The prompt is URL-encoded automatically by requests
        api_url = f"{POLLINATIONS_API}{prompt}?width=512&height=768&nologo=true"

        # Send the GET request to generate the image
        response = requests.get(api_url, timeout=60)

        if response.status_code == 200:
            # Delete the status message
            await status_msg.delete()

            # Send the generated image back to the user
            await update.message.reply_photo(
                photo=response.content,
                caption=f"🖼️ Generated from: \"{prompt}\""
            )
        else:
            await status_msg.edit_text(
                f"❌ Sorry, something went wrong generating your image. Please try again later."
            )

    except requests.exceptions.Timeout:
        await status_msg.edit_text("⏰ The image generation took too long. Please try again.")
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        await status_msg.edit_text("❌ An error occurred. Please try again later.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages that aren't commands."""
    # Don't process if it's a command
    if update.message.text and update.message.text.startswith('/'):
        return

    # Use the same generate function
    await generate_image(update, context)

def main():
    """Main function to run the bot."""
    # Create the application
    application = ApplicationBuilder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate_image))

    # Add handler for all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start the bot with long polling
    logger.info("Starting bot with long polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
