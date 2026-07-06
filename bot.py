import os
import logging
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_TOKEN environment variable is not set!")
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
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        api_url = f"{POLLINATIONS_API}{encoded_prompt}?width=512&height=768&nologo=true"

        logger.info(f"Generating image for prompt: {prompt}")

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
            logger.info(f"Successfully generated image for: {prompt}")
        else:
            await status_msg.edit_text(
                f"❌ Sorry, something went wrong (Status: {response.status_code}). Please try again later."
            )
            logger.error(f"API error: {response.status_code} - {response.text}")

    except requests.exceptions.Timeout:
        await status_msg.edit_text("⏰ The image generation took too long. Please try again.")
        logger.error("Image generation timeout")
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

async def main():
    """Main function to run the bot."""
    try:
        # Create the application
        application = Application.builder().token(TOKEN).build()

        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("generate", generate_image))

        # Add handler for all text messages (except commands)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

        # Start the bot with long polling
        logger.info("🚀 Starting Bimgs AI Bot...")
        logger.info(f"Bot token: {TOKEN[:10]}...")  # Log first 10 chars for debugging
        
        # Initialize the application (new in v21+)
        await application.initialize()
        
        # Start polling
        await application.start()
        await application.updater.start_polling()
        
        logger.info("✅ Bot is running and waiting for messages!")
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
