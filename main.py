from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
import asyncio
import sys
from contextlib import redirect_stdout
import io
import uuid  # для генерации уникальных ID для inline ответов

API_TOKEN = '7149788600:AAEf47b99LjZHYzG2NkD4I-a0YbHIwP-3tw'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def execute_python_code(code: str):
    try:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exec(code)
        return buffer.getvalue()
    except Exception as e:
        return str(e)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Привет!\nЯ бот, который может выполнять Python код. Используй команду вида /run ваш_код для выполнения Python кода или используй меня в инлайн режиме.\nПример: /run print(\"hi\")")

@dp.message_handler(commands=['run'])
async def execute_code(message: types.Message):
    code = message.get_args()

    if not code:
        await message.reply("Пожалуйста, введите код после команды. Пример: /run print(\"hi\")")
        return

    result = execute_python_code(code)
    if len(result) > 4000:
        result = result[:4000] + "\n... Output truncated."

    formatted_message = f"Результат: <pre><code class=\"language-python\"> {result}</code></pre>"
    await message.answer(formatted_message, parse_mode=types.ParseMode.HTML)

@dp.inline_handler()
async def inline_echo(inline_query: types.InlineQuery):
    # Обрабатываем код, переданный через инлайн запрос
    code = inline_query.query or 'print("Введите код...")'
    result = execute_python_code(code)

    # если результат пустой, заменяем его на предупреждающее сообщение
    if not result.strip():
        result = "Код не вернул результат. Пожалуйста, убедитесь, что ваш код выводит данные."

    input_content = InputTextMessageContent(result)
    item = InlineQueryResultArticle(
        id=str(uuid.uuid4()), 
        title="Выполнить код (dir() и help() не работают в инлайне)",
        description=result[:100] if len(result) > 100 else result,
        input_message_content=input_content
    )
    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
