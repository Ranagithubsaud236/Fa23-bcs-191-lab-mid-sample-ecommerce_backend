from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")


class Rating(BaseModel):
    average: float = 0
    count: int = 0


# Product Models 
class ProductInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: str
    category: str
    price: float
    brand: str
    rating: Rating = Field(default_factory=Rating)
    stock: int
    created_at: datetime
    updated_at: datetime
    score: Optional[float] = None
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True, "populate_by_name": True}


class SearchProductResponse(ProductInDB):
    pass


# User Models 
class UserInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    email: EmailStr
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True, "populate_by_name": True}


class UserResponse(UserInDB):
    pass


# Order Models 
class OrderProduct(BaseModel):
    product_id: PyObjectId
    name: str
    price_at_purchase: float
    quantity: int
    model_config = {"arbitrary_types_allowed": True}


class OrderInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    products: List[OrderProduct]
    total_cost: float
    status: str
    timestamp: datetime
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True, "populate_by_name": True}


class OrderResponse(OrderInDB):
    pass


class EnhancedOrderProduct(BaseModel):
    product_id: PyObjectId
    name: str
    price_at_purchase: float
    quantity: int
    # Additional product details from products collection
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    current_price: Optional[float] = None
    model_config = {"arbitrary_types_allowed": True}


class EnhancedOrderResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    # User details
    user_id: PyObjectId
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_location: Optional[str] = None
    # Order details
    products: List[EnhancedOrderProduct]
    total_cost: float
    status: str
    timestamp: datetime
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True, "populate_by_name": True}


# Review Models 
class ReviewInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    product_id: PyObjectId
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None
    timestamp: datetime
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True, "populate_by_name": True}


class ReviewWithUser(ReviewInDB):
    user_name: Optional[str] = None
    user_email: Optional[str] = None


# Aggregation Response Models 
class TopProductResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    category: str
    brand: str
    price: float
    purchase_count: int
    total_quantity_sold: int
    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

