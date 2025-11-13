import sqlite3
import os

db_path = './Database/tasks.db'
os.makedirs(os.path.dirname(db_path), exist_ok=True)

categories = [
    "Electronics",
    "Groceries",
    "Clothing",
    "Books",
    "Toys",
    "Furniture",
    "Sports",
    "Beauty",
    "Home & Garden",
    "Automotive"
]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for category in categories:
    try:
        cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (category,))
        print(f"Added category: {category}")
    except sqlite3.IntegrityError:
        print(f"Category already exists: {category}")

conn.commit()
conn.close()

