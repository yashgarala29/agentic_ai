import sqlite3
import os

# Connect to database
db_path = os.path.join(os.path.dirname(__file__), "product.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON;")

# Ensure tables exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        price REAL NOT NULL,
        stock INTEGER DEFAULT 0,
        description TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
        comment TEXT,
        review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    )
""")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);")

# Sample products including near-duplicates (variations of running/walking/athletic shoes, etc.)
products_to_insert = [
    # Running shoes variations
    ("Running Shoes", "Apparel", 65.00, 30, "Lightweight breathable athletic sneakers for daily road running."),
    ("Walking Shoes", "Apparel", 58.00, 45, "Comfortable cushioned walking shoes designed for daily strolls and long walks."),
    ("Trail Running Shoes", "Apparel", 74.99, 20, "Rugged trail running shoes with aggressive grip outsole for outdoor terrains."),
    ("Athletic Running Sneakers", "Apparel", 62.50, 25, "Breathable mesh road running sneakers with responsive foam sole."),
    ("Men's Daily Walking Shoes", "Apparel", 52.00, 35, "Slip-on lightweight walking shoes with memory foam arch support."),
    ("Pro Marathon Running Shoes", "Apparel", 89.99, 15, "Ultra-lightweight carbon plate racing and marathon running shoes."),
    
    # Other items
    ("Wireless Noise-Canceling Headphones", "Electronics", 99.99, 25, "Over-ear Bluetooth headphones with active noise cancellation."),
    ("Mechanical Gaming Keyboard", "Electronics", 79.50, 18, "RGB backlit mechanical keyboard with tactile blue switches."),
    ("Stainless Steel Water Bottle", "Home & Kitchen", 18.00, 50, "Insulated 750ml leak-proof flask for hot and cold beverages.")
]

# Insert products and keep track of inserted IDs
inserted_product_ids = {}
for name, category, price, stock, description in products_to_insert:
    cursor.execute("""
        INSERT INTO products (name, category, price, stock, description)
        VALUES (?, ?, ?, ?, ?)
    """, (name, category, price, stock, description))
    inserted_product_ids[name] = cursor.lastrowid

print(f"[OK] Inserted {len(products_to_insert)} products.")

# Sample reviews for products (linked dynamically via inserted IDs)
reviews_to_insert = [
    (inserted_product_ids["Running Shoes"], "Diana Prince", 5, "Super lightweight and comfortable for morning runs.", "2026-10-19 15:00:00"),
    (inserted_product_ids["Walking Shoes"], "George Miller", 4, "Very soft insoles, perfect for evening walks. No foot fatigue.", "2026-10-22 10:15:00"),
    (inserted_product_ids["Trail Running Shoes"], "Hannah Montana", 5, "Great traction on wet rocky trails and muddy slopes. Highly recommend!", "2026-10-23 17:40:00"),
    (inserted_product_ids["Athletic Running Sneakers"], "Ian Malcolm", 4, "Fit true to size, great ventilation for 10k training.", "2026-10-24 09:10:00"),
    (inserted_product_ids["Men's Daily Walking Shoes"], "Julia Roberts", 5, "Easy slip-on design, extremely comfortable for walking all day.", "2026-10-25 13:25:00"),
    (inserted_product_ids["Pro Marathon Running Shoes"], "Kevin Vance", 5, "Incredible energy return and bouncy feel, cut 2 minutes off my pace!", "2026-10-25 16:40:00"),
    (inserted_product_ids["Wireless Noise-Canceling Headphones"], "Alice Johnson", 5, "Amazing sound quality and battery life lasts for days!", "2026-10-16 11:00:00"),
    (inserted_product_ids["Mechanical Gaming Keyboard"], "Bob Smith", 5, "Very clicky and responsive. The RGB backlighting looks gorgeous.", "2026-10-18 19:20:00"),
    (inserted_product_ids["Stainless Steel Water Bottle"], "Charlie Brown", 4, "Keeps water ice cold all day, easy to carry around.", "2026-10-19 12:10:00")
]

cursor.executemany("""
    INSERT INTO reviews (product_id, customer_name, rating, comment, review_date)
    VALUES (?, ?, ?, ?, ?)
""", reviews_to_insert)

print(f"[OK] Inserted {len(reviews_to_insert)} reviews.")

# Commit changes and close
conn.commit()

# Print summary
print("\n--- Current Table Counts ---")
for table in ["products", "reviews"]:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  - {table}: {cursor.fetchone()[0]} rows")

conn.close()
