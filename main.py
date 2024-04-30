from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.handler import SkipHandler
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
import asyncio
import sys
from contextlib import redirect_stdout
import io
import uuid  # для генерации уникальных ID для inline ответов
import subprocess
import shlex

API_TOKEN = 'ваш токен'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def execute_python_code(code: str):
    try:
        if "exit()" in code or "os.system" in code:
            return "Использовать exit() или os.system не разрешается."
        
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

# Функция для выполнения C++ кода
def execute_cpp_code(code: str):
    try:
        # Сохраняем код C++ во временный файл
        with open('temp.cpp', 'w') as file:
            file.write(code)
        
        # Компилируем C++ код
        compile_process = subprocess.run(['g++', 'temp.cpp', '-o', 'temp'], capture_output=True, text=True)
        if compile_process.returncode != 0:
            # В случае ошибки компиляции возвращаем сообщение об ошибке
            return compile_process.stderr

        # Выполняем скомпилированную программу
        execute_process = subprocess.run(['./temp'], capture_output=True, text=True)
        if execute_process.returncode != 0:
            # В случае ошибки выполнения возвращаем сообщение об ошибке
            return execute_process.stderr
        
        # Возвращаем результат выполнения программы
        return execute_process.stdout
    except Exception as e:
        return str(e)
    finally:
        # Удаляем временные файлы
        subprocess.run(['rm', 'temp.cpp', 'temp'])

# Обработчик команды /cpp
@dp.message_handler(commands=['cpp'])
async def execute_cpp(message: types.Message):
    code = message.get_args()
    if not code:
        await message.reply("Пожалуйста, введите код C++ после команды. Пример: /cpp код")
        return
    
    # Проверка на небезопасные команды
    if "system" in code or "exit" in code:
        await message.reply("Использование небезопасных команд запрещено.")
        return

    # Выполнение кода
    result = execute_cpp_code(code)
    if len(result) > 4000:
        result = result[:4000] + "\n... Output truncated."

    # Отправка результата пользователю
    await message.reply(f"Результат:\n```\n{result}\n```", parse_mode=types.ParseMode.MARKDOWN)
    

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
        title="Выполнить код",
        description=result[:100] if len(result) > 100 else result,
        input_message_content=input_content
    )
    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
