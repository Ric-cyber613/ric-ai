"""Utility to initialize the web app database (users).

Run: python web/init_db.py
"""
from web.auth import init_db

if __name__ == '__main__':
    init_db()
    print('Initialized DB')