import sqlite3

db_path = r"E:\Ai Projects\ai_agents\9_shopping_agent\product.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Enable foreign key support
cursor.execute("PRAGMA foreign_keys = ON;")

# ==========================================
# 1. PRODUCTS TABLE
# ==========================================
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

# Check if products already exist
cursor.execute("SELECT COUNT(*) FROM products")
if cursor.fetchone()[0] == 0:
    sample_products = [
        ("Wireless Noise-Canceling Headphones", "Electronics", 99.99, 25, "Over-ear Bluetooth headphones with 30h battery life."),
        ("Mechanical Gaming Keyboard", "Electronics", 79.50, 15, "RGB backlit mechanical keyboard with tactile blue switches."),
        ("Stainless Steel Water Bottle", "Home & Kitchen", 18.00, 50, "Insulated 750ml leak-proof flask."),
        ("Running Shoes", "Apparel", 65.00, 30, "Lightweight breathable athletic sneakers."),
        ("Ergonomic Office Chair", "Furniture", 199.99, 8, "Adjustable lumbar support with breathable mesh back.")
    ]
    cursor.executemany("""
        INSERT INTO products (name, category, price, stock, description)
        VALUES (?, ?, ?, ?, ?)
    """, sample_products)
    print("[OK] Seeded products table.")

# ==========================================
# 2. ORDERS TABLE
# ==========================================
cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
        total_price REAL NOT NULL,
        status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
        order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    )
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id);")

cursor.execute("SELECT COUNT(*) FROM orders")
if cursor.fetchone()[0] == 0:
    sample_orders = [
        (1, "Alice Johnson", 1, 99.99, "delivered", "2026-10-15 10:30:00"),
        (2, "Bob Smith", 2, 159.00, "shipped", "2026-10-17 14:15:00"),
        (3, "Charlie Brown", 3, 54.00, "delivered", "2026-10-18 09:00:00"),
        (4, "Diana Prince", 1, 65.00, "processing", "2026-10-19 11:45:00"),
        (5, "Evan Wright", 1, 199.99, "pending", "2026-10-19 18:20:00"),
        (1, "Fiona Gallagher", 2, 199.98, "delivered", "2026-10-12 16:50:00")
    ]
    cursor.executemany("""
        INSERT INTO orders (product_id, customer_name, quantity, total_price, status, order_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_orders)
    print("[OK] Seeded orders table.")

# ==========================================
# 3. REVIEWS TABLE
# ==========================================
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

cursor.execute("SELECT COUNT(*) FROM reviews")
if cursor.fetchone()[0] == 0:
    sample_reviews = [
        (1, "Alice Johnson", 5, "Amazing sound quality and battery life lasts for days!", "2026-10-16 11:00:00"),
        (1, "Fiona Gallagher", 4, "Comfortable for long study sessions, noise cancelling is solid.", "2026-10-14 08:30:00"),
        (2, "Bob Smith", 5, "Very clicky and responsive. The RGB backlighting looks gorgeous.", "2026-10-18 19:20:00"),
        (3, "Charlie Brown", 4, "Keeps water cold all day, easy to carry around.", "2026-10-19 12:10:00"),
        (4, "Diana Prince", 5, "Super lightweight and comfortable for morning runs.", "2026-10-19 15:00:00"),
        (5, "Evan Wright", 4, "Great back support for working from home. Easy to assemble.", "2026-10-19 20:00:00")
    ]
    cursor.executemany("""
        INSERT INTO reviews (product_id, customer_name, rating, comment, review_date)
        VALUES (?, ?, ?, ?, ?)
    """, sample_reviews)
    print("[OK] Seeded reviews table.")

conn.commit()

# Print summary
print("\n--- Database Summary ---")
for table_name in ["products", "orders", "reviews"]:
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  - {table_name}: {count} rows")

conn.close()