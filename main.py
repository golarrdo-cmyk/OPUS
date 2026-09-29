"""Точка входа для платформ, которые запускают main.py (то же, что python -m dietbot)."""
import asyncio

from dietbot.__main__ import main

if __name__ == "__main__":
    asyncio.run(main())
