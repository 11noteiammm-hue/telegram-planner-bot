import asyncio
import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import aiohttp

from database import Database

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL", None)

# Настройка сессии с прокси (если указан)
if PROXY_URL:
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=BOT_TOKEN, session=session)
    logger.info(f"Используется прокси: {PROXY_URL}")
else:
    bot = Bot(token=BOT_TOKEN)
    logger.info("Прокси не используется")

dp = Dispatcher(storage=MemoryStorage())
router = Router()
db = Database()
scheduler = AsyncIOScheduler()

# FSM States
class PlanningStates(StatesGroup):
    waiting_for_task = State()

# Клавиатуры
def get_main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📅 Планирование", callback_data="planning")],
        [InlineKeyboardButton(text="🧠 Тренинг", callback_data="training")],
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")]
    ])
    return keyboard

def get_info_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📅 Планирование", callback_data="planning")],
        [InlineKeyboardButton(text="🧠 Тренинг", callback_data="training")]
    ])
    return keyboard

def get_profile_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
        [InlineKeyboardButton(text="📅 Планирование", callback_data="planning")],
        [InlineKeyboardButton(text="🧠 Тренинг", callback_data="training")],
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")]
    ])
    return keyboard

def get_planning_keyboard(tasks_count: int = 0):
    buttons = []

    # Кнопки для существующих задач
    for i in range(min(tasks_count, 10)):
        buttons.append([InlineKeyboardButton(text=f"📝 Задача {i+1}", callback_data=f"view_task_{i}")])

    # Кнопка добавления задачи (если меньше 10)
    if tasks_count < 10:
        buttons.append([InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")])

    # Навигационные кнопки
    buttons.extend([
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🧠 Тренинг", callback_data="training")],
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_training_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📅 Планирование", callback_data="planning")],
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")]
    ])
    return keyboard

def get_task_start_keyboard(task_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Начинаю!", callback_data=f"start_task_{task_id}")]
    ])
    return keyboard

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    await db.add_user(user_id, username, first_name)

    # Если есть картинка для главного меню, используй FSInputFile
    # photo = FSInputFile("images/main_menu.jpg")
    # await message.answer_photo(photo, caption="...", reply_markup=get_main_menu_keyboard())

    text = (
        f"Привет, {first_name}! 👋\n\n"
        "Добро пожаловать в бот для планирования и саморазвития!\n\n"
        "Здесь ты сможешь:\n"
        "📅 Планировать свой день по минутам\n"
        "✅ Ставить и выполнять задачи\n"
        "🧠 Тренировать мышление\n"
        "📊 Отслеживать свой прогресс\n\n"
        "Выбери раздел:"
    )

    await message.answer(text, reply_markup=get_main_menu_keyboard())

# Обработчик кнопки "Меню"
@router.callback_query(F.data == "menu")
async def show_menu(callback: CallbackQuery):
    text = (
        f"Главное меню 🏠\n\n"
        "Выбери нужный раздел:"
    )
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()

# Обработчик кнопки "Инфо"
@router.callback_query(F.data == "info")
async def show_info(callback: CallbackQuery):
    text = (
        "ℹ️ О боте\n\n"
        "Этот бот создан для того, чтобы помочь тебе стать лучшей версией себя! 🚀\n\n"
        "Каждый день - это возможность для роста. Планируй, выполняй, развивайся!\n\n"
        "Помни: успех - это сумма маленьких усилий, повторяемых изо дня в день. 💪\n\n"
        "Начни прямо сейчас - выбери раздел и действуй!"
    )
    await callback.message.edit_text(text, reply_markup=get_info_keyboard())
    await callback.answer()

# Обработчик кнопки "Профиль"
@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = await db.get_user_stats(user_id)

    grade_emoji = ["😢", "😟", "😐", "🙂", "😊", "😄", "😁", "🤩", "🔥", "⭐", "🏆"]

    text = (
        f"👤 Твой профиль\n\n"
        f"📊 Статистика:\n"
        f"• Всего задач: {stats['total_tasks']}\n"
        f"• Выполнено: {stats['completed_tasks']}\n"
        f"• Процент выполнения: {stats['percentage']}%\n"
        f"• Оценка: {stats['grade']}/10 {grade_emoji[stats['grade']]}\n\n"
    )

    if stats['grade'] <= 3:
        text += "Не сдавайся! Каждый шаг приближает к цели. 💪"
    elif stats['grade'] <= 6:
        text += "Хороший прогресс! Продолжай в том же духе! 👍"
    else:
        text += "Отличная работа! Ты на верном пути! 🔥"

    await callback.message.edit_text(text, reply_markup=get_profile_keyboard())
    await callback.answer()

# Обработчик кнопки "Планирование"
@router.callback_query(F.data == "planning")
async def show_planning(callback: CallbackQuery):
    user_id = callback.from_user.id
    tasks = await db.get_schedule_tasks(user_id)

    text = (
        "📅 Планирование\n\n"
        "Здесь ты можешь распланировать свой день по часам и минутам.\n"
        "Это твой личный будильник для продуктивности! ⏰\n\n"
    )

    if tasks:
        text += "Твои задачи:\n\n"
        for i, task in enumerate(tasks[:10], 1):
            status = "✅" if task['started'] else "⏳"
            text += f"{i}. {status} {task['time']} - {task['text']}\n"
    else:
        text += "У тебя пока нет задач. Добавь первую!\n\n"
        text += "Для добавления задачи нажми кнопку ниже и отправь сообщение в формате:\n"
        text += "Текст задачи (до 120 символов)\nВремя (например: 09:30)"

    await callback.message.edit_text(text, reply_markup=get_planning_keyboard(len(tasks)))
    await callback.answer()

# Обработчик кнопки "Добавить задачу"
@router.callback_query(F.data == "add_task")
async def add_task_prompt(callback: CallbackQuery, state: FSMContext):
    text = (
        "➕ Добавление задачи\n\n"
        "Отправь сообщение в формате:\n\n"
        "Текст задачи (до 120 символов)\n"
        "Время (например: 14:30)\n\n"
        "Пример:\n"
        "Позвонить клиенту\n"
        "15:00"
    )
    await callback.message.edit_text(text)
    await state.set_state(PlanningStates.waiting_for_task)
    await callback.answer()

# Обработчик получения задачи от пользователя
@router.message(StateFilter(PlanningStates.waiting_for_task))
async def process_new_task(message: Message, state: FSMContext):
    lines = message.text.strip().split('\n')

    if len(lines) < 2:
        await message.answer("❌ Неверный формат! Отправь текст задачи и время на разных строках.")
        return

    task_text = lines[0][:120]
    time_str = lines[1].strip()

    # Проверка формата времени
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await message.answer("❌ Неверный формат времени! Используй формат ЧЧ:ММ (например: 14:30)")
        return

    user_id = message.from_user.id
    task_id = await db.add_schedule_task(user_id, task_text, time_str)

    await message.answer(
        f"✅ Задача добавлена!\n\n"
        f"📝 {task_text}\n"
        f"⏰ {time_str}\n\n"
        f"Я напомню тебе в указанное время!",
        reply_markup=get_main_menu_keyboard()
    )

    await state.clear()

# Обработчик кнопки "Тренинг"
@router.callback_query(F.data == "training")
async def show_training(callback: CallbackQuery):
    user_id = callback.from_user.id
    exercise = await db.get_daily_exercise(user_id)

    if exercise:
        if exercise['already_completed']:
            text = (
                "🧠 Тренинг мышления\n\n"
                "Твое упражнение на сегодня:\n\n"
                f"💡 {exercise['text']}\n\n"
                "Ты уже получил это упражнение сегодня. Возвращайся завтра за новым!"
            )
        else:
            text = (
                "🧠 Тренинг мышления\n\n"
                "Ежедневные упражнения для развития мышления помогут тебе:\n"
                "• Улучшить концентрацию\n"
                "• Развить креативность\n"
                "• Укрепить память\n"
                "• Повысить продуктивность\n\n"
                "Твое упражнение на сегодня:\n\n"
                f"💡 {exercise['text']}\n\n"
                "Подумай над ним и возвращайся завтра за новым!"
            )
    else:
        text = (
            "🧠 Тренинг мышления\n\n"
            "Упражнения временно недоступны. Попробуй позже!"
        )

    await callback.message.edit_text(text, reply_markup=get_training_keyboard())
    await callback.answer()

# Обработчик кнопки "Начинаю!"
@router.callback_query(F.data.startswith("start_task_"))
async def start_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[2])
    await db.mark_task_started(task_id)

    await callback.message.edit_text(
        "✅ Отлично! Удачи с выполнением задачи! 💪"
    )
    await callback.answer("Задача отмечена как начатая!")

# Функция проверки и отправки напоминаний
async def check_schedule():
    """Проверяет расписание и отправляет напоминания"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    tasks = await db.get_pending_schedule_tasks()

    for task in tasks:
        if task['time'] == current_time and task['reminder_count'] == 0:
            # Первое напоминание
            await bot.send_message(
                task['user_id'],
                f"⏰ Пора начинать!\n\n📝 {task['text']}",
                reply_markup=get_task_start_keyboard(task['id'])
            )
            await db.increment_reminder(task['id'])

        elif task['reminder_count'] > 0 and task['reminder_count'] < 5:
            # Проверяем, прошло ли 5 минут с последнего напоминания
            task_time = datetime.strptime(task['time'], "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            minutes_passed = (now - task_time).total_seconds() / 60

            if minutes_passed >= task['reminder_count'] * 5:
                await bot.send_message(
                    task['user_id'],
                    f"⏰ Напоминание #{task['reminder_count'] + 1}\n\n📝 {task['text']}\n\nНе забудь начать!",
                    reply_markup=get_task_start_keyboard(task['id'])
                )
                await db.increment_reminder(task['id'])

        elif task['reminder_count'] >= 5:
            # Удаляем задачу после 5 напоминаний
            await db.delete_schedule_task(task['id'])

async def main():
    await db.init_db()
    await db.init_training_exercises()

    # Запуск планировщика для проверки расписания каждую минуту
    scheduler.add_job(check_schedule, CronTrigger(second=0))
    scheduler.start()

    dp.include_router(router)

    logger.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
