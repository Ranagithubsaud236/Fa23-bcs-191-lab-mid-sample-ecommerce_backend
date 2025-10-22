# E-Commerce Backend - ADB Assignment

> **Complete implementation of Sample Paper B - E-Commerce Marketplace Backend**

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start MongoDB

Ensure MongoDB is running on `localhost:27017`

### 3. Run the Application

```bash
python -m uvicorn main:app --reload
```

### 4. Access API Documentation

Open in browser: **http://127.0.0.1:8000/docs**

---

## Features Implemented

**5 RESTful APIs**:

1. `GET /products/search` - Advanced search with keyword + fuzzy + hybrid ranking
2. `GET /users/{user_id}/orders` - User's order history
3. `GET /products/{product_id}/reviews` - Product reviews with user details
4. `GET /orders/{order_id}` - Order details by ID
5. `GET /analytics/top-products` - Top products aggregation pipeline

**Advanced Search**:

- Keyword search (MongoDB text index)
- Fuzzy search (typo tolerance)
- Hybrid ranking: 40% similarity + 40% popularity + 20% price

  **Database**:

- 4 collections (products, users, orders, reviews)
- 10 strategic indexes
- Hybrid schema design (embedded + referenced)

---

## Project Structure

```
ecommerce_backend/
├── main.py                     # FastAPI application
├── models.py                   # Pydantic models
├── database.py                 # MongoDB setup
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
│
├── data/                       # JSON datasets
│   ├── products.json
│   ├── users.json
│   ├── orders.json
│   └── reviews.json
│
├── screenshots/                # Optional screenshots (can be empty)
├── PROJECT_REPORT.txt          # Consolidated project report (this repo)
```

---

## Test

```bash
# Test search API
curl "http://127.0.0.1:8000/products/search?query=laptop&limit=5"

# Test fuzzy search (with typo)
curl "http://127.0.0.1:8000/products/search?query=leptop"

# Test analytics
curl "http://127.0.0.1:8000/analytics/top-products?days=30&limit=5"
```

---

---

## Assignment Requirements Met

- [x] MongoDB schema with embedded + referenced documents
- [x] 10+ indexes created
- [x] 4+ RESTful APIs
- [x] Keyword search
- [x] Fuzzy search
- [x] Hybrid ranking (BONUS)
- [x] Aggregation pipeline
- [x] Data seeding from JSON
- [x] Comprehensive documentation

---

## Technology Stack

- **Framework**: FastAPI
- **Database**: MongoDB
- **Driver**: Motor (async)
- **Validation**: Pydantic
- **Server**: Uvicorn

---

**Date**: October 2025

This project implements the backend for an e-commerce marketplace, designed using FastAPI and MongoDB. It covers product management, user orders, reviews, and advanced search functionalities including keyword, fuzzy, and hybrid ranking.

## Assignment Requirements Covered

**Question 1: Design Scenario**

- **MongoDB Schema Design:** Detailed schema for `products`, `users`, `orders`, and `reviews` collections, utilizing embedded and referenced documents where appropriate, with justifications provided in the documentation.
- **Indexes Optimization:** Suggested indexes for all collections to optimize common queries and search operations, including compound indexes.
- **API Design:** Comprehensive API designs for `/products/search`, `/users/<id>/orders`, `/products/<id>/reviews`, and `/orders/<id>`, including methods, parameters, and example responses.
- **Aggregation Pipeline:** One aggregation pipeline designed to find the "Top 5 most frequently purchased products in the last month, grouped by category."

**Question 2: Mini-Project Implementation**

- **MongoDB Data Seeding:** Implemented a script to seed the MongoDB database with provided JSON data on application startup.
- **Implemented 3 APIs:**
  - `GET /products/search`
  - `GET /users/{user_id}/orders`
  - `GET /products/{product_id}/reviews`
  - Additionally, `GET /products/top-5-purchased-by-category` for the aggregation pipeline.
- **Search Endpoint (`/products/search`):** Supports keyword search (using MongoDB's text index) and basic fuzzy search (using regex).
- **Hybrid Ranking:** The `/products/search` endpoint includes a simplified hybrid ranking formula (40% similarity/relevance, 40% popularity, 20% inverse price) when no explicit `sort_by` parameter is provided.

## Technologies Used

- **Python 3.8+**
- **FastAPI:** For building the asynchronous web APIs.
- **Uvicorn:** ASGI server to run the FastAPI application.
- **PyMongo:** Python driver for MongoDB.
- **Pydantic:** For data validation and serialization/deserialization.
- **MongoDB:** NoSQL database for storing application data.

## Project Structure
