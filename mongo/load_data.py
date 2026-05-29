from pymongo import MongoClient
from sqlalchemy import create_engine
import pandas as pd
import json

PG = create_engine("postgresql+psycopg2://itc6050:itc6050@localhost:5432/shop_lab")
MG = MongoClient("mongodb://itc6050:itc6050@localhost:27017/?authSource=admin")
db = MG["shop_lab"]

# --- Wipe any prior runs ---
for c in ["customer", "product", "orders", "orders_embedded"]:
    db.drop_collection(c)

# --- Customers ---
customers = pd.read_sql("SELECT * FROM shop.customer", PG)
db.customer.insert_many(customers.to_dict(orient="records"))
print(f"Loaded {db.customer.count_documents({})} customers")

# --- Products ---
products = pd.read_sql("""
    SELECT p.product_id, p.name, p.unit_price, c.name AS category
    FROM shop.product p
    JOIN shop.category c USING (category_id)
""", PG)
db.product.insert_many(products.to_dict(orient="records"))
print(f"Loaded {db.product.count_documents({})} products")

# --- Orders (referenced) ---
orders = pd.read_sql("SELECT * FROM shop.orders", PG)
db.orders.insert_many(orders.to_dict(orient="records"))

# --- Orders (embedded) ---
embedded = pd.read_sql("""
    SELECT o.order_id, o.customer_id, o.order_date, o.status, o.total,
        json_agg(
            json_build_object(
                'product_id', oi.product_id,
                'quantity', oi.quantity,
                'unit_price_at_sale', oi.unit_price_at_sale
            )
        ) AS items
    FROM shop.orders o
    JOIN shop.order_item oi USING (order_id)
    GROUP BY o.order_id, o.customer_id, o.order_date, o.status, o.total
""", PG, parse_dates=["order_date"])

embedded["items"] = embedded["items"].apply(
    lambda x: x if isinstance(x, list) else json.loads(x)
)
db.orders_embedded.insert_many(embedded.to_dict(orient="records"))
print(f"Loaded {db.orders.count_documents({})} reference-style orders")
print(f"Loaded {db.orders_embedded.count_documents({})} embedded-style orders")

# --- Indexes ---
db.customer.create_index("customer_id", unique=True)
db.customer.create_index("email", unique=True)
db.product.create_index("product_id", unique=True)
db.orders.create_index([("order_date", 1)])
db.orders.create_index("customer_id")
db.orders_embedded.create_index([("order_date", 1)])
db.orders_embedded.create_index("customer_id")
print("✅ Indexes created.")