from fastmcp import FastMCP
import asyncio
from typing import Optional, Dict, Any, List
from database import (
    init_db,
    add_expense as db_add_expense,
    list_expenses as db_list_expenses,
    summarize_expenses as db_summarize_expenses,
    get_categories
)
import json

# Initialize FastMCP
mcp = FastMCP("ExpenseTracker")

# ----------------- Tools -----------------

@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
) -> Dict[str, Any]:
    """Add a new expense entry."""
    try:
        result = await db_add_expense(date, amount, category, subcategory, note)
        return result
    except Exception as e:
        return {"status": "error", "message": f"Failed to add expense: {str(e)}"}

@mcp.tool()
async def list_expenses(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """List expenses within a date range."""
    try:
        return await db_list_expenses(start_date, end_date)
    except Exception as e:
        print(f"Error listing expenses: {e}")
        return []

@mcp.tool()
async def summarize(
    start_date: str,
    end_date: str,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Summarize expenses by category."""
    try:
        return await db_summarize_expenses(start_date, end_date, category)
    except Exception as e:
        print(f"Error summarizing expenses: {e}")
        return []

# ----------------- Resources -----------------

@mcp.resource("expense:///categories", mime_type="application/json")
async def categories() -> str:
    """Return the list of available categories as JSON."""
    try:
        categories_data = await get_categories()
        return json.dumps(categories_data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Could not load categories: {str(e)}"})

# ----------------- Server Startup -----------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the Expense Tracker MCP server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    # Initialize database before starting the server
    try:
        asyncio.run(init_db())
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        raise

    # Start MCP server
    mcp.run(
        transport="http",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
