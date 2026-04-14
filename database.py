import aiosqlite
from typing import Optional

DB_PATH = "bot.db"


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER UNIQUE NOT NULL,
                    username      TEXT,
                    full_name     TEXT,
                    is_paid       INTEGER DEFAULT 0,
                    joined_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL DEFAULT ''
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payment_requests (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id            INTEGER NOT NULL,
                    status             TEXT DEFAULT 'pending',
                    screenshot_file_id TEXT,
                    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Default settings (only if they don't exist yet)
            defaults = [
                ("price", "10000"),
                ("card_number", "0000 0000 0000 0000"),
                ("card_owner", "Karta Egasi"),
                ("channel_id", ""),
                ("channel_link", ""),
                ("random_min", "1"),
                ("random_max", "1000"),
                ("payment_group_id", ""),
                ("welcome_text", ""),
            ]
            await db.executemany(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                defaults,
            )
            # ── Migrations (add columns to existing tables safely) ─────────
            try:
                await db.execute(
                    "ALTER TABLE payment_requests ADD COLUMN screenshot_file_id TEXT"
                )
            except Exception:
                pass  # column already exists
            await db.commit()

    # ── Users ──────────────────────────────────────────────────────────────

    async def add_user(self, user_id: int, username: str, full_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE
                  SET username  = excluded.username,
                      full_name = excluded.full_name
                """,
                (user_id, username or "", full_name),
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[tuple]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cur:
                return await cur.fetchone()

    async def is_paid(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT is_paid FROM users WHERE user_id = ?", (user_id,)
            ) as cur:
                row = await cur.fetchone()
                return bool(row and row[0])

    async def set_paid(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_paid = 1 WHERE user_id = ?", (user_id,)
            )
            await db.commit()

    async def get_all_user_ids(self) -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users") as cur:
                rows = await cur.fetchall()
                return [r[0] for r in rows]

    # ── Settings ───────────────────────────────────────────────────────────

    async def get_setting(self, key: str) -> str:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ) as cur:
                row = await cur.fetchone()
                return row[0] if row else ""

    async def set_setting(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            await db.commit()

    # ── Payment requests ───────────────────────────────────────────────────

    async def add_payment_request(self, user_id: int) -> int:
        """Creates (or replaces) a pending request and returns its id."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM payment_requests WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            cur = await db.execute(
                "INSERT INTO payment_requests (user_id) VALUES (?)", (user_id,)
            )
            await db.commit()
            return cur.lastrowid  # type: ignore[return-value]

    async def get_pending_requests(self) -> list[tuple]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT pr.id, pr.user_id, u.username, u.full_name, pr.created_at
                FROM payment_requests pr
                JOIN users u ON pr.user_id = u.user_id
                WHERE pr.status = 'pending'
                ORDER BY pr.created_at
                """
            ) as cur:
                return await cur.fetchall()

    async def set_screenshot(self, request_id: int, file_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE payment_requests SET screenshot_file_id = ? WHERE id = ?",
                (file_id, request_id),
            )
            await db.commit()

    async def update_payment_status(self, request_id: int, status: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE payment_requests SET status = ? WHERE id = ?",
                (status, request_id),
            )
            await db.commit()

    # ── Statistics ─────────────────────────────────────────────────────────

    async def get_stats(self) -> tuple[int, int, int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cur:
                total: int = (await cur.fetchone())[0]
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE is_paid = 1"
            ) as cur:
                paid: int = (await cur.fetchone())[0]
            async with db.execute(
                "SELECT COUNT(*) FROM payment_requests WHERE status = 'pending'"
            ) as cur:
                pending: int = (await cur.fetchone())[0]
        return total, paid, pending
