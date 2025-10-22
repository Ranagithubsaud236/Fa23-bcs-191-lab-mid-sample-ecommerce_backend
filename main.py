from fastapi import FastAPI, HTTPException, Query, Depends, Path
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from database import mongo_db, init_db, get_database
from models import (
    ProductInDB, SearchProductResponse, 
    OrderResponse, OrderInDB, EnhancedOrderResponse,
    ReviewWithUser, UserResponse,
    TopProductResponse
)

app = FastAPI(
    title="E-commerce Marketplace Backend",
    description="Backend for an e-commerce platform using FastAPI and MongoDB.",
    version="1.0.0"
)

@app.get("/")
def home():
    return {"message": "E-commerce backend is running successfully!"}

@app.on_event("startup")
async def startup_db_client():
    await init_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    mongo_db.client.close()
    print("MongoDB connection closed.")

def get_products_collection():
    db = get_database()
    return db["products"]

def get_orders_collection():
    db = get_database()
    return db["orders"]

def get_users_collection():
    db = get_database()
    return db["users"]

def get_reviews_collection():
    db = get_database()
    return db["reviews"]

@app.get("/products/search", response_model=List[SearchProductResponse])
async def search_products(
    query: str = Query(..., min_length=1),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    sort_by: Optional[str] = None,
    products_collection=Depends(get_products_collection),
    orders_collection=Depends(get_orders_collection)
):
    try:
        normalized_sort = None
        if sort_by:
            s = str(sort_by).strip().lower().replace('-', ' ').replace('_', ' ')
            if s in {"hybrid", "hybrid search", "hybridscore", "hybrid score"}:
                normalized_sort = None
            else:
                if s in {"price asc", "price low", "price low to high", "price_asc"}:
                    normalized_sort = "price_asc"
                elif s in {"price desc", "price high", "price high to low", "price_desc"}:
                    normalized_sort = "price_desc"
                elif s in {"popularity", "popular"}:
                    normalized_sort = "popularity"
                elif s in {"rating", "ratings"}:
                    normalized_sort = "rating"
                else:
                    normalized_sort = None
        sort_by_effective = normalized_sort

        q = (query or "").strip()
        fuzzy_query = ".*" + ".*".join(list(q.lower())) + ".*"

        filters: dict = {}
        if min_price is not None:
            filters["price"] = {"$gte": min_price}
        if max_price is not None:
            filters.setdefault("price", {})["$lte"] = max_price
        if category:
            filters["category"] = {"$regex": category, "$options": "i"}
        if brand:
            filters["brand"] = {"$regex": brand, "$options": "i"}

        def build_sort_stage():
            sort_map = {
                "price_asc": {"price": 1},
                "price_desc": {"price": -1},
                "popularity": {"popularity": -1},
                "rating": {"rating.average": -1},
            }
            return {"$sort": sort_map.get(sort_by_effective, {"hybrid_score": -1})}

        need_popularity = (not sort_by_effective) or (sort_by_effective == "popularity")

        def compose_pipeline(match_stage: Optional[dict] = None, use_text_score: bool = False, pre_stages: Optional[List[dict]] = None):
            pipe: List[dict] = []
            if pre_stages:
                pipe.extend(pre_stages)
            if match_stage is not None:
                pipe.append({"$match": match_stage})
            if need_popularity:
                pipe.append({
                    "$lookup": {
                        "from": "orders",
                        "let": {"pid": "$_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$in": ["$$pid", "$products.product_id"]}}},
                            {"$group": {"_id": 1, "c": {"$sum": 1}}}
                        ],
                        "as": "pop"
                    }
                })
                pipe.append({
                    "$addFields": {
                        "popularity": {"$ifNull": [{"$arrayElemAt": ["$pop.c", 0]}, 0]}
                    }
                })
            if not sort_by_effective:
                if use_text_score:
                    pipe.append({
                        "$addFields": {
                            "text_score": {"$meta": "textScore"},
                            "hybrid_score": {
                                "$add": [
                                    {"$multiply": [0.4, {"$meta": "textScore"}]},
                                    {"$multiply": [0.4, {"$min": [1, {"$divide": ["$popularity", 100]}]}]},
                                    {"$multiply": [0.2, {"$cond": [{"$gt": ["$price", 0]}, {"$divide": [1, "$price"]}, 0]}]}
                                ]
                            }
                        }
                    })
                else:
                    pipe.append({
                        "$addFields": {
                            "hybrid_score": {
                                "$add": [
                                    {"$multiply": [0.4, {"$min": [1, {"$divide": ["$popularity", 100]}]}]},
                                    {"$multiply": [0.2, {"$cond": [{"$gt": ["$price", 0]}, {"$divide": [1, "$price"]}, 0]}]}
                                ]
                            }
                        }
                    })
                pipe.append({"$sort": {"hybrid_score": -1}})
            else:
                pipe.append(build_sort_stage())

            pipe.extend([{"$skip": skip}, {"$limit": limit}])
            pipe.append({
                "$project": {
                    "_id": 1, "name": 1, "description": 1, "category": 1,
                    "price": 1, "brand": 1, "rating": 1, "stock": 1,
                    "created_at": 1, "updated_at": 1,
                    "score": {"$ifNull": ["$hybrid_score", 0]}
                }
            })
            return pipe

        results: List[ProductInDB] = []

        used_text = False
        if len(q) >= 3:
            text_match = {"$text": {"$search": q}}
            text_match.update(filters)
            text_pipeline = compose_pipeline(text_match, use_text_score=True)
            cursor = products_collection.aggregate(text_pipeline)
            results = [ProductInDB(**doc) async for doc in cursor]
            used_text = True

        if not results:
            regex_match = {
                "$or": [
                    {"name": {"$regex": fuzzy_query, "$options": "i"}},
                    {"description": {"$regex": fuzzy_query, "$options": "i"}},
                    {"brand": {"$regex": fuzzy_query, "$options": "i"}},
                    {"category": {"$regex": fuzzy_query, "$options": "i"}},
                ]
            }
            if filters:
                pre_stages = [{"$match": filters}, {"$match": regex_match}]
                regex_pipeline = compose_pipeline(match_stage=None, use_text_score=False, pre_stages=pre_stages)
            else:
                regex_pipeline = compose_pipeline(regex_match, use_text_score=False)
            cursor = products_collection.aggregate(regex_pipeline)
            results = [ProductInDB(**doc) async for doc in cursor]

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/orders", response_model=List[EnhancedOrderResponse])
async def get_user_orders(
    user_id: str = Path(..., description="User ID"),
    users_collection=Depends(get_users_collection),
    orders_collection=Depends(get_orders_collection),
    products_collection=Depends(get_products_collection)
):
    try:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        user_obj_id = ObjectId(user_id)
        user = await users_collection.find_one({"_id": user_obj_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        pipeline = [
            {"$match": {"user_id": user_obj_id}},
            {"$sort": {"timestamp": -1}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$products", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "products.product_id",
                    "foreignField": "_id",
                    "as": "product_info"
                }
            },
            {"$unwind": {"path": "$product_info", "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": "$_id",
                    "user_id": {"$first": "$user_id"},
                    "user_name": {"$first": "$user_info.name"},
                    "user_email": {"$first": "$user_info.email"},
                    "user_location": {"$first": "$user_info.location"},
                    "total_cost": {"$first": "$total_cost"},
                    "status": {"$first": "$status"},
                    "timestamp": {"$first": "$timestamp"},
                    "products": {
                        "$push": {
                            "product_id": "$products.product_id",
                            "name": "$products.name",
                            "price_at_purchase": "$products.price_at_purchase",
                            "quantity": "$products.quantity",
                            "description": "$product_info.description",
                            "category": "$product_info.category",
                            "brand": "$product_info.brand",
                            "current_price": "$product_info.price"
                        }
                    }
                }
            },
            {"$sort": {"timestamp": -1}}
        ]
        
        cursor = orders_collection.aggregate(pipeline)
        orders = []
        async for order in cursor:
            orders.append(EnhancedOrderResponse(**order))
        
        return orders
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}/reviews", response_model=List[ReviewWithUser])
async def get_product_reviews(
    product_id: str = Path(..., description="Product ID"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    products_collection=Depends(get_products_collection),
    reviews_collection=Depends(get_reviews_collection)
):
    try:
        if not ObjectId.is_valid(product_id):
            raise HTTPException(status_code=400, detail="Invalid product ID format")
        
        product_obj_id = ObjectId(product_id)
        product = await products_collection.find_one({"_id": product_obj_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        pipeline = [
            {"$match": {"product_id": product_obj_id}},
            {"$sort": {"timestamp": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {
                "$addFields": {
                    "user_name": {"$arrayElemAt": ["$user_info.name", 0]},
                    "user_email": {"$arrayElemAt": ["$user_info.email", 0]}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "user_id": 1,
                    "product_id": 1,
                    "rating": 1,
                    "review_text": 1,
                    "timestamp": 1,
                    "user_name": 1,
                    "user_email": 1
                }
            }
        ]
        
        cursor = reviews_collection.aggregate(pipeline)
        reviews = []
        async for review in cursor:
            reviews.append(ReviewWithUser(**review))
        
        return reviews
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str = Path(..., description="Order ID"),
    orders_collection=Depends(get_orders_collection)
):
    try:
        if not ObjectId.is_valid(order_id):
            raise HTTPException(status_code=400, detail="Invalid order ID format")
        
        order_obj_id = ObjectId(order_id)
        order = await orders_collection.find_one({"_id": order_obj_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return OrderInDB(**order)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/top-products", response_model=List[TopProductResponse])
async def get_top_products_by_category(
    days: int = Query(1000, ge=1, le=3650, description="Days to look back"),
    limit: int = Query(5, ge=1, le=20, description="Top products per category"),
    category: Optional[str] = Query(None, description="Filter by category"),
    orders_collection=Depends(get_orders_collection),
    products_collection=Depends(get_products_collection)
):
    try:
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": date_threshold}}},
            {"$unwind": "$products"},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "products.product_id",
                    "foreignField": "_id",
                    "as": "product_info"
                }
            },
            {"$unwind": "$product_info"},
            {
                "$group": {
                    "_id": "$products.product_id",
                    "name": {"$first": "$product_info.name"},
                    "category": {"$first": "$product_info.category"},
                    "brand": {"$first": "$product_info.brand"},
                    "price": {"$first": "$product_info.price"},
                    "purchase_count": {"$sum": 1},
                    "total_quantity_sold": {"$sum": "$products.quantity"}
                }
            }
        ]
        
        if category:
            pipeline.append({"$match": {"category": category}})
        
        pipeline.append({"$sort": {"purchase_count": -1}})
        pipeline.append({"$limit": limit})
        
        cursor = orders_collection.aggregate(pipeline)
        top_products = []
        async for product in cursor:
            top_products.append(TopProductResponse(**product))
        
        return top_products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
