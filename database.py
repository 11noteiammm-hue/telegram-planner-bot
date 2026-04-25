import aiosqlite
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    timezone TEXT DEFAULT 'UTC',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица долгосрочных задач (неделя, месяц, год)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS long_term_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_text TEXT,
                    period TEXT,
                    is_completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица планирования (будильники)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS schedule_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_text TEXT,
                    scheduled_time TEXT,
                    is_started BOOLEAN DEFAULT 0,
                    reminder_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица упражнений для тренинга
            await db.execute("""
                CREATE TABLE IF NOT EXISTS training_exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exercise_text TEXT,
                    category TEXT
                )
            """)

            # Таблица выполненных упражнений пользователями
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_training (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    exercise_id INTEGER,
                    completed_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (exercise_id) REFERENCES training_exercises(id)
                )
            """)

            await db.commit()
            logger.info("База данных инициализирована")

    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Добавление нового пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                (user_id, username, first_name)
            )
            await db.commit()

    async def get_user_stats(self, user_id: int):
        """Получение статистики пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_tasks
                FROM long_term_tasks
                WHERE user_id = ?
            """, (user_id,))
            row = await cursor.fetchone()

            total = row[0] if row[0] else 0
            completed = row[1] if row[1] else 0

            if total > 0:
                percentage = round((completed / total) * 100, 2)
                grade = int(percentage // 10)
                if grade > 10:
                    grade = 10
            else:
                percentage = 0.0
                grade = 0

            return {
                'total_tasks': total,
                'completed_tasks': completed,
                'percentage': percentage,
                'grade': grade
            }

    async def add_long_term_task(self, user_id: int, task_text: str, period: str):
        """Добавление долгосрочной задачи"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO long_term_tasks (user_id, task_text, period) VALUES (?, ?, ?)",
                (user_id, task_text, period)
            )
            await db.commit()

    async def complete_task(self, task_id: int, user_id: int):
        """Отметка задачи как выполненной"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE long_term_tasks SET is_completed = 1, completed_at = ? WHERE id = ? AND user_id = ?",
                (datetime.now(), task_id, user_id)
            )
            await db.commit()

    async def add_schedule_task(self, user_id: int, task_text: str, scheduled_time: str):
        """Добавление задачи в расписание"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO schedule_tasks (user_id, task_text, scheduled_time) VALUES (?, ?, ?)",
                (user_id, task_text, scheduled_time)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_schedule_tasks(self, user_id: int):
        """Получение всех задач расписания пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, task_text, scheduled_time, is_started FROM schedule_tasks WHERE user_id = ? ORDER BY scheduled_time",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [{'id': r[0], 'text': r[1], 'time': r[2], 'started': r[3]} for r in rows]

    async def mark_task_started(self, task_id: int):
        """Отметка что пользователь начал задачу"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE schedule_tasks SET is_started = 1 WHERE id = ?",
                (task_id,)
            )
            await db.commit()

    async def increment_reminder(self, task_id: int):
        """Увеличение счетчика напоминаний"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE schedule_tasks SET reminder_count = reminder_count + 1 WHERE id = ?",
                (task_id,)
            )
            await db.commit()

    async def get_pending_schedule_tasks(self):
        """Получение всех незавершенных задач расписания"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, user_id, task_text, scheduled_time, reminder_count FROM schedule_tasks WHERE is_started = 0"
            )
            rows = await cursor.fetchall()
            return [{'id': r[0], 'user_id': r[1], 'text': r[2], 'time': r[3], 'reminder_count': r[4]} for r in rows]

    async def delete_schedule_task(self, task_id: int):
        """Удаление задачи из расписания"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM schedule_tasks WHERE id = ?", (task_id,))
            await db.commit()

    async def init_training_exercises(self):
        """Инициализация упражнений для тренинга"""
        exercises = [
            ("Решите анаграмму: ЛОСКВО → ?", "логика"),
            ("Назовите 10 необычных способов использования обычной ложки", "креативность"),
            ("Найдите закономерность: 2, 4, 8, 16, ? ", "логика"),
            ("Опишите обычный день с точки зрения вашей обуви", "креативность"),
            ("Сколько будет 17 × 23 (без калькулятора)?", "математика"),
            ("Придумайте 5 слов, начинающихся на последнюю букву предыдущего", "память"),
            ("Что общего между яблоком и книгой?", "ассоциации"),
            ("Запомните: 7, 3, 9, 1, 5. Повторите в обратном порядке", "память"),
            ("Как бы вы объяснили интернет человеку из 1800 года?", "креативность"),
            ("Решите: если 5 кошек ловят 5 мышей за 5 минут, сколько кошек нужно для 100 мышей за 100 минут?", "логика"),
            ("Придумайте историю из 3 предложений со словами: космос, кофе, кот", "креативность"),
            ("Какое число должно быть следующим: 1, 1, 2, 3, 5, 8, ?", "логика"),
            ("Перечислите 7 красных предметов за 30 секунд", "внимание"),
            ("Прочитайте слово задом наперед: ТЕЛЕФОН", "внимание"),
            ("Сколько треугольников в пятиконечной звезде?", "геометрия"),
        ]

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM training_exercises")
            count = await cursor.fetchone()

            if count[0] == 0:
                await db.executemany(
                    "INSERT INTO training_exercises (exercise_text, category) VALUES (?, ?)",
                    exercises
                )
                await db.commit()
                logger.info(f"Добавлено {len(exercises)} упражнений")

    async def get_daily_exercise(self, user_id: int):
        """Получение упражнения дня для пользователя"""
        today = datetime.now().date()

        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, выполнял ли пользователь упражнение сегодня
            cursor = await db.execute("""
                SELECT exercise_id FROM user_training
                WHERE user_id = ? AND completed_date = ?
            """, (user_id, today))

            completed_today = await cursor.fetchone()

            if completed_today:
                cursor = await db.execute(
                    "SELECT exercise_text FROM training_exercises WHERE id = ?",
                    (completed_today[0],)
                )
                exercise = await cursor.fetchone()
                return {'text': exercise[0], 'already_completed': True}

            # Получаем случайное упражнение, которое пользователь не делал недавно
            cursor = await db.execute("""
                SELECT id, exercise_text FROM training_exercises
                WHERE id NOT IN (
                    SELECT exercise_id FROM user_training
                    WHERE user_id = ? AND completed_date >= date('now', '-7 days')
                )
                ORDER BY RANDOM() LIMIT 1
            """, (user_id,))

            exercise = await cursor.fetchone()

            if exercise:
                # Записываем что пользователь получил это упражнение
                await db.execute(
                    "INSERT INTO user_training (user_id, exercise_id, completed_date) VALUES (?, ?, ?)",
                    (user_id, exercise[0], today)
                )
                await db.commit()
                return {'text': exercise[1], 'already_completed': False}

            return None
