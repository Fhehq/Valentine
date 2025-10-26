import sqlite3

DB_PATH = "users.db"

class UserManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _connect(self):
        """Создаёт соединение с базой"""
        return sqlite3.connect(self.db_path)

    def is_new_user(self, user_id: int) -> bool:
        """Проверяет, новый ли пользователь"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
            return cursor.fetchone() is None

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь админом"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT admin FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return bool(row[0]) if row else False

    def get_users(self) -> list[int]:
        """Возвращает список всех пользователей"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users")
            users = [row[0] for row in cursor.fetchall()]
        return users

    def add_user(self, user_id: int, admin: bool = False):
        """Добавляет нового пользователя (если его ещё нет)"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (id, admin) VALUES (?, ?)",
                (user_id, int(admin))
            )
            conn.commit()

    def add_admin(self, user_id: int):
        """Назначает пользователя админом"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET admin = 1 WHERE id = ?",
                (user_id,)
            )
            conn.commit()

    def remove_admin(self, user_id: int):
        """Снимает права админа"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET admin = 0 WHERE id = ?",
                (user_id,)
            )
            conn.commit()
