from pymongo import MongoClient
from pprint import pprint
import time

client = MongoClient("mongodb://itc6050:itc6050@localhost:27017/?authSource=admin")
db = client["shop_lab"]

def timed(label, func):
    t = time.time()
    result = list(func())
    print(f"{label:35s} {(time.time() - t) * 1000:7.1f} ms")
    return result

# Q1 - Monthly revenue trend
print("\n--- Q1: Monthly revenue ---")
q1 = db.orders.aggregate([
    {"$group": {
        "_id": {
            "year": {"$year": "$order_date"},
            "month": {"$month": "$order_date"},
        },
        "orders": {"$sum": 1},
        "revenue": {"$sum": "$total"},
    }},
    {"$sort": {"_id.year": 1, "_id.month": 1}},
])
for row in list(q1)[:3]:
    pprint(row)

# Q2 - Top 10 products by revenue
print("\n--- Q2: Top 10 products ---")
q2 = db.orders_embedded.aggregate([
    {"$unwind": "$items"},
    {"$group": {
        "_id": "$items.product_id",
        "total_qty": {"$sum": "$items.quantity"},
        "revenue": {"$sum": {"$multiply": ["$items.quantity", "$items.unit_price_at_sale"]}},
    }},
    {"$sort": {"revenue": -1}},
    {"$limit": 10},
])
for row in list(q2):
    pprint(row)

# Q3 - Order count + avg by status
print("\n--- Q3: Orders by status ---")
q3 = db.orders.aggregate([
    {"$group": {
        "_id": "$status",
        "count": {"$sum": 1},
        "avg_total": {"$avg": "$total"},
    }},
    {"$sort": {"_id": 1}},
])
for row in list(q3):
    pprint(row)

# Q4 - Dormant customers
print("\n--- Q4: Dormant customers ---")
q4 = db.orders.aggregate([
    {"$group": {
        "_id": "$customer_id",
        "last_order": {"$max": "$order_date"},
    }},
    {"$match": {
        "last_order": {"$lt": __import__('datetime').datetime.now() - __import__('datetime').timedelta(days=90)}
    }},
    {"$lookup": {
        "from": "customer",
        "localField": "_id",
        "foreignField": "customer_id",
        "as": "cust_info",
    }},
    {"$unwind": "$cust_info"},
    {"$project": {
        "email": "$cust_info.email",
        "last_order": 1,
    }},
    {"$limit": 5},
])
for row in list(q4):
    pprint(row)

# Q5 - Top 20 customers by lifetime spend
print("\n--- Q5: Top 20 customers by lifetime spend ---")
q5 = db.orders.aggregate([
    {"$group": {
        "_id": "$customer_id",
        "lifetime_spend": {"$sum": "$total"},
    }},
    {"$sort": {"lifetime_spend": -1}},
    {"$setWindowFields": {
        "sortBy": {"lifetime_spend": -1},
        "output": {
            "rank": {"$rank": {}},
            "prev_spend": {
                "$shift": {"output": "$lifetime_spend", "by": -1}
            },
        },
    }},
    {"$addFields": {
        "gap_to_previous": {
            "$cond": {
                "if": {"$eq": ["$prev_spend", None]},
                "then": None,
                "else": {"$subtract": ["$prev_spend", "$lifetime_spend"]}
            }
        }
    }},
    {"$project": {"rank": 1, "lifetime_spend": 1, "gap_to_previous": 1}},
    {"$limit": 20},
])
for row in list(q5)[:5]:
    pprint(row)