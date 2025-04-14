import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from playwright.async_api import async_playwright

# Load bot token and whitelist from environment variables
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USERS = set(map(int, os.getenv("TELEGRAM_ALLOWED_IDS", "").split(",")))

if not API_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN environment variable is required")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Capture a full-page screenshot
async def render_screenshot(url: str, filename: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=120000)
        await page.screenshot(path=filename, full_page=True)
        await browser.close()

# Generate a PDF of the page
async def render_pdf(url: str, filename: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=120000)
        await page.pdf(
            path=filename,
            format="A4",
            print_background=True,
            margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"}
        )
        await browser.close()

# Check if the user is in the whitelist
def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

# Handle /start command
@dp.message(CommandStart())
async def cmd_start(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return
    await message.answer("Welcome. Use /pdf or /screenshot followed by a URL.")

# Handle /screenshot command
@dp.message(Command("screenshot"))
async def cmd_screenshot(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        await message.answer("Usage: /screenshot https://example.com")
        return

    url = args[1]
    if not url.startswith("http"):
        url = "http://" + url

    await message.answer("Rendering screenshot...")
    filename = f"screenshot_{message.from_user.id}.png"

    try:
        await render_screenshot(url, filename)
        await message.answer_photo(types.FSInputFile(filename), caption="Screenshot ready.")
        os.remove(filename)
    except Exception as e:
        await message.answer(f"An error occurred while rendering the screenshot: {e}")

# Handle /pdf command
@dp.message(Command("pdf"))
async def cmd_pdf(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        await message.answer("Usage: /pdf https://example.com")
        return

    url = args[1]
    if not url.startswith("http"):
        url = "http://" + url

    await message.answer("Generating PDF...")
    filename = f"page_{message.from_user.id}.pdf"

    try:
        await render_pdf(url, filename)
        await message.answer_document(types.FSInputFile(filename), caption="PDF generated.")
        os.remove(filename)
    except Exception as e:
        await message.answer(f"An error occurred while generating the PDF: {e}")

# Start the bot polling loop
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
