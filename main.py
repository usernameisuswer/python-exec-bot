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
import uuid
import subprocess
import shlex 
import Command
import openai

API_TOKEN = 'ваш токен'
OPENAI_API_KEY = 'ваш ключ OpenAI'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Словарь для хранения счетчиков запросов пользователей
user_requests = {}

# Список администраторов
admins = []

# Функция для проверки лимита запросов
def check_limit(user_id):
    if user_id in user_requests:
        requests, timestamp = user_requests[user_id]
        # Проверяем, прошел ли час с момента первого запроса
        if (time.time() - timestamp) > 3600:
            user_requests[user_id] = (1, time.time())
            return True
        else:
            # Проверяем лимит запросов
            if requests < 10:
                user_requests[user_id] = (requests + 1, timestamp)
                return True
            else:
                return False
    else:
        user_requests[user_id] = (1, time.time())
        return True

# Функция для выполнения запросов к ChatGPT
async def ask_openai(prompt):
    try:
        response = openai.Completion.create(
            engine="davinci",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return str(e)

# Команда /ask
@dp.message_handler(commands=['ask'])
async def ask_command(message: types.Message):
    user_id = message.from_user.id
    if user_id not in admins and not check_limit(user_id):
        await message.reply("Вы исчерпали лимит запросов. Попробуйте позже.")
        return

    prompt = message.get_args()
    if not prompt:
        await message.reply("Пожалуйста, введите запрос после команды. Пример: /ask Какой сегодня день?")
        return

    response = await ask_openai(prompt)
    await message.reply(response)

# Команда /ban
@dp.message_handler(commands=['ban'])
async def ban_command(message: types.Message):
    if message.from_user.id not in admins:
        await message.reply("У вас нет прав для использования этой команды.")
        return

    user_id = int(message.get_args())
    if user_id:
        user_requests.pop(user_id, None)
        await message.reply(f"Пользователь {user_id} заблокирован.")

# Команды для управления администраторами
@dp.message_handler(commands=['adminadd'])
async def admin_add_command(message: types.Message):
    if message.from_user.id not in admins:
        await message.reply("У вас нет прав для использования этой команды.")
        return

    admin_id = int(message.get_args())
    if admin_id and admin_id not in admins:
        admins.append(admin_id)
        await message.reply(f"Пользователь {admin_id} добавлен в администраторы.")

@dp.message_handler(commands=['adminremove'])
async def admin_remove_command(message: types.Message):
    if message.from_user.id not in admins:
        await message.reply("У вас нет прав для использования этой команды.")
        return

    admin_id = int(message.get_args())
    if admin_id and admin_id in admins:
        admins.remove(admin_id)
        await message.reply(f"Пользователь {admin_id} удален из администраторов.")


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
    await message.reply("Привет!\nЯ бот, который может выполнять Python код. Используй команду вида /py ваш код для выполнения Python кода или используй меня в инлайн режиме.\nПример: /py print(\"hi\")")

@dp.message_handler(commands=['py'])
async def execute_code(message: types.Message):
    code = message.get_args()

    if not code:
        await message.reply("Пожалуйста, введите код после команды. Пример: /py print(\"hi\")")
        return

    result = execute_python_code(code)
    if len(result) > 4000:
        result = result[:4000] + "\n... Output truncated."

    formatted_message = f"Результат: <pre><code class=\"language-python\"> {result}</code></pre>"
    await message.answer(formatted_message, parse_mode=types.ParseMode.HTML)

# Функция для выполнения C++ кода
def execute_cpp_code(code: str):
    try:
        # Проверка на использование std::cin и других небезопасных команд
        if "гитлер" in code or "system" in code or "exit" in code:
            return "Использование слова гитлер, system или exit запрещено."

        # Сохраняем код C++ во временный файл
        with open('temp.cpp', 'w') as file:
            file.write(code)

        # Компилируем C++ код
        compile_process = subprocess.run(['g++', 'temp.cpp', '-o', 'temp'], capture_output=True, text=True)
        if compile_process.returncode != 0:
            # В случае ошибки компиляции возвращаем сообщение об ошибке
            return compile_process.stderr

        # Выполняем скомпилированную программу с таймаутом
        execute_process = subprocess.run(['./temp'], capture_output=True, text=True, timeout=5)
        if execute_process.returncode != 0:
            # В случае ошибки выполнения возвращаем сообщение об ошибке
            return execute_process.stderr

        # Возвращаем результат выполнения программы
        return execute_process.stdout
    except subprocess.TimeoutExpired:
        return "Время выполнения кода превысило ограничение."
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
    
# Функция для выполнения Java кода
def execute_java_code(code: str):
    try:
        # Проверка на использование System.exit и других небезопасных команд
        if "System.exit" in code or "Runtime.getRuntime().exec" in code:
            return "Использование System.exit или Runtime.getRuntime().exec запрещено."

        # Сохраняем код Java во временный файл
        with open('Temp.java', 'w') as file:
            file.write(code)

        # Компилируем Java код
        compile_process = subprocess.run(['javac', 'Temp.java'], capture_output=True, text=True)
        if compile_process.returncode != 0:
            # В случае ошибки компиляции возвращаем сообщение об ошибке
            return compile_process.stderr

        # Выполняем скомпилированную программу с таймаутом
        execute_process = subprocess.run(['java', 'Temp'], capture_output=True, text=True, timeout=5)
        if execute_process.returncode != 0:
            # В случае ошибки выполнения возвращаем сообщение об ошибке
            return execute_process.stderr

        # Возвращаем результат выполнения программы
        return execute_process.stdout
    except subprocess.TimeoutExpired:
        return "Время выполнения кода превысило ограничение."
    except Exception as e:
        return str(e)
    finally:
        # Удаляем временные файлы
        subprocess.run(['rm', 'Temp.java', 'Temp.class'])

# Обработчик команды /java
@dp.message_handler(commands=['java'])
async def execute_java(message: types.Message):
    code = message.get_args()
    if not code:
        await message.reply("Пожалуйста, введите код Java после команды. Пример: /java код")
        return

    # Проверка на небезопасные команды
    if "Runtime.getRuntime().exec" in code or "System.exit" in code:
        await message.reply("Использование небезопасных команд запрещено.")
        return

    # Выполнение кода
    result = execute_java_code(code)
    if len(result) > 4000:
        result = result[:4000] + "\n... Output truncated."

    # Отправка результата пользователю
    await message.reply(f"Результат:\n```\n{result}\n```", parse_mode=types.ParseMode.MARKDOWN)

# Исправление инлайн режима для Java
@dp.inline_handler()
async def inline_echo(inline_query: types.InlineQuery):
    query = inline_query.query
    result = ""
    if query.startswith("py "):
        code = query[3:]
        result = execute_python_code(code)
    elif query.startswith("cpp "):
        code = query[4:]
        result = execute_cpp_code(code)
    elif query.startswith("java "):
        code = query[5:]
        result = execute_java_code(code)
    else:
        result = "Введите префикс 'py' для Python кода, 'cpp' для C++ кода или 'java' для Java кода."

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
    openai.api_key = OPENAI_API_KEY
    executor.start_polling(dp, skip_updates=True)