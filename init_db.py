import sqlite3
import os

DB_PATH = "db.sqlite3"

# Remove existing database if needed (optional)
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Create items table
c.execute("""
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    location TEXT,
    category TEXT,
    photo TEXT,
    status TEXT DEFAULT 'approved',
    approved INTEGER DEFAULT 0
)
""")

# Create claims table
c.execute("""
CREATE TABLE claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    student_name TEXT,
    email TEXT,
    message TEXT,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY(item_id) REFERENCES items(id)
)
""")

# Insert sample items
c.execute("""
INSERT INTO items (name, description, location, category, status, approved)
VALUES
('Blue Backpack', 'Lost near cafeteria', 'Cafeteria', 'Accessories', 'approved', 1),
('Math Textbook', 'Calculus book, red cover', 'Library', 'Books', 'approved', 1),
('Headphones', 'Black wireless', 'Gym', 'Electronics', 'approved', 1)
""")

# Insert sample claims
c.execute("""
INSERT INTO claims (item_id, student_name, email, message, status)
VALUES
(1, 'Alice Johnson', 'alice@example.com', 'Lost my blue backpack', 'pending')
""")

conn.commit()
conn.close()

print("Database initialized successfully!")
