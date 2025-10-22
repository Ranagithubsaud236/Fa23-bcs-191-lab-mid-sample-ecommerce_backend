# ecommerce_backend/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
import json
import os
from config import settings

MONGO_URL = settings.mongodb_uri
DATABASE_NAME = settings.mongodb_db_name

class MongoDB:
    client: AsyncIOMotorClient = None

mongo_db = MongoDB()

def get_database():
    return mongo_db.client[DATABASE_NAME]

def parse_mongo_json(data):
    if isinstance(data, dict):
        if "$oid" in data:
            return ObjectId(data["$oid"])
        elif "$date" in data:
            return datetime.fromisoformat(data["$date"].replace("Z", "+00:00"))
        else:
            return {k: parse_mongo_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [parse_mongo_json(item) for item in data]
    return data

async def load_data_from_json(collection_name: str, file_path: str):
    db = get_database()
    collection = db[collection_name]

    if await collection.count_documents({}) > 0:
        print(f"Collection '{collection_name}' already has data. Skipping...")
        return

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            parsed_data = parse_mongo_json(data)
            if parsed_data:
                await collection.insert_many(parsed_data)
                print(f"Loaded {len(parsed_data)} documents into '{collection_name}'")
    else:
        print(f"File not found: {file_path}")

async def init_db():
    mongo_db.client = AsyncIOMotorClient(MONGO_URL)
    db = get_database()
    print("Connected to MongoDB")

    products_col = db["products"]
    users_col = db["users"]
    orders_col = db["orders"]
    reviews_col = db["reviews"]

    print("Creating indexes...")

    existing_indexes = await products_col.index_information()
    if "text_search_index" not in existing_indexes:
        await products_col.create_index([
            ("name", "text"), ("description", "text"),
            ("brand", "text"), ("category", "text")
        ], name="text_search_index", weights={"name": 10, "brand": 5, "category": 3, "description": 1})
        print("✓ Created text search index")

    if "price_category_index" not in existing_indexes:
        await products_col.create_index([("price", 1), ("category", 1)], name="price_category_index")
        print("✓ Created compound index on price + category")

    if "rating_index" not in existing_indexes:
        await products_col.create_index([("rating.average", -1)], name="rating_index")
        print("✓ Created index on rating")

    if "brand_index" not in existing_indexes:
        await products_col.create_index("brand", name="brand_index")
        print("✓ Created index on brand")

    existing_order_indexes = await orders_col.index_information()
    def has_index_with_keys(index_info: dict, keys: list):
        try:
            for info in index_info.values():
                if list(info.get('key', [])) == keys:
                    return True
        except Exception:
            pass
        return False
    if "user_id_index" not in existing_order_indexes:
        await orders_col.create_index("user_id", name="user_id_index")
        print("✓ Created index on orders.user_id")

    if "timestamp_index" not in existing_order_indexes:
        await orders_col.create_index([("timestamp", -1)], name="timestamp_index")
        print("✓ Created index on orders.timestamp")

    # Index to speed up lookups on products in orders for popularity counts
    products_pid_keys = [("products.product_id", 1)]
    if not has_index_with_keys(existing_order_indexes, products_pid_keys):
        await orders_col.create_index(products_pid_keys, name="order_products_product_id_idx")
        print("✓ Created index on orders.products.product_id")
    else:
        print("✓ Index on orders.products.product_id already exists (skipped)")

    existing_review_indexes = await reviews_col.index_information()
    if "product_id_index" not in existing_review_indexes:
        await reviews_col.create_index("product_id", name="product_id_index")
        print("✓ Created index on reviews.product_id")

    if "user_id_review_index" not in existing_review_indexes:
        await reviews_col.create_index("user_id", name="user_id_review_index")
        print("✓ Created index on reviews.user_id")

    existing_user_indexes = await users_col.index_information()
    if "email_index" not in existing_user_indexes:
        await users_col.create_index("email", unique=True, name="email_index")
        print("✓ Created unique index on users.email")

    print("\nLoading data from JSON files...")
    data_dir = settings.data_path

    await load_data_from_json("products", os.path.join(data_dir, "products.json"))
    await load_data_from_json("users", os.path.join(data_dir, "users.json"))
    await load_data_from_json("orders", os.path.join(data_dir, "orders.json"))
    await load_data_from_json("reviews", os.path.join(data_dir, "reviews.json"))

    print("\n✓ Database initialization complete!")

async def close_db():
    if mongo_db.client:
        mongo_db.client.close()
        print("MongoDB connection closed.")

