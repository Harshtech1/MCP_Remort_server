import os
import aiosqlite
import aiofiles
import json

# Paths for database and categories file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")


# ----------------- Database Initialization -----------------
async def init_db():
    """Initialize the database and create the expenses table if it doesn't exist."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                );
            """)
            await db.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise


# ----------------- CRUD Operations -----------------
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = "") -> dict:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "INSERT INTO expenses (date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
                (date, amount, category, subcategory, note)
            )
            await db.commit()
            return {"status": "success", "id": cur.lastrowid, "message": "Expense added successfully"}
    except Exception as e:
        if "readonly" in str(e).lower():
            return {"status": "error", "message": "Database is read-only. Check file permissions."}
        return {"status": "error", "message": str(e)}


async def list_expenses(start_date: str, end_date: str):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (start_date, end_date)
            )
            columns = [col[0] for col in cur.description]
            rows = await cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def summarize_expenses(start_date: str, end_date: str, category: str = None):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            query = """
                SELECT category, SUM(amount) AS total_amount, COUNT(*) AS count
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " GROUP BY category ORDER BY total_amount DESC"

            cur = await db.execute(query, params)
            columns = [col[0] for col in cur.description]
            rows = await cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ----------------- Categories -----------------
async def get_categories():
    default_categories = {
        "categories": [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Travel",
            "Education",
            "Business",
            "Other"
        ]
    }
    try:
        if os.path.exists(CATEGORIES_PATH):
            async with aiofiles.open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                data = await f.read()
            return json.loads(data)
        else:
            return default_categories
    except Exception as e:
        return {"error": f"Could not load categories: {str(e)}"}


# ----------------- Main -----------------
if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    print("Database initialized successfully")
