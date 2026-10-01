"""Picks the storage backend based on config.DB_ENGINE.
sqlite (default): zero setup, pre-seeded with sample movies -> see db_sqlite.py
mysql: your own MySQL server + live TMDB data -> see db_mysql.py"""
import config

if config.DB_ENGINE == "mysql":
    from db_mysql import *  # noqa: F401,F403
else:
    from db_sqlite import *  # noqa: F401,F403
