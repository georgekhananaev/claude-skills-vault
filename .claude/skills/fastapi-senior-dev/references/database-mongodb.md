# MongoDB with Beanie/Motor

## Setup

### Beanie Configuration

```python
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings

class MongoSettings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "myapp"

settings = MongoSettings()

async def init_db():
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db],
        document_models=[User, Order, Product]  # All document classes
    )

# In main.py
@app.on_event("startup")
async def startup():
    await init_db()
```

## Document Models

### Basic Document

```python
from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime

class User(Document):
    email: Indexed(str, unique=True)
    name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"  # Collection name
        indexes = [
            "email",
            [("name", 1), ("created_at", -1)],  # Compound index
        ]
```

### Embedded Documents

```python
from beanie import Document
from pydantic import BaseModel

class Address(BaseModel):
    """Embedded document (not a collection)."""
    street: str
    city: str
    country: str
    zip_code: str

class User(Document):
    email: str
    addresses: list[Address] = []

    class Settings:
        name = "users"
```

### Document Links (References)

```python
from beanie import Document, Link, BackLink

class Author(Document):
    name: str
    books: list[BackLink["Book"]] = []  # Reverse reference

    class Settings:
        name = "authors"

class Book(Document):
    title: str
    author: Link[Author]  # Reference to Author

    class Settings:
        name = "books"

# Usage
author = await Author(name="John").insert()
book = await Book(title="My Book", author=author).insert()

# Fetch with linked document
book = await Book.find_one(Book.title == "My Book", fetch_links=True)
print(book.author.name)  # "John"
```

## CRUD Operations

### Create

```python
# Single insert
user = User(email="test@example.com", name="Test")
await user.insert()

# Bulk insert
users = [User(email=f"user{i}@example.com", name=f"User {i}") for i in range(100)]
await User.insert_many(users)
```

### Read

```python
# Find by ID
user = await User.get("64a1b2c3d4e5f6g7h8i9j0k1")

# Find one
user = await User.find_one(User.email == "test@example.com")

# Find many
active_users = await User.find(User.is_active == True).to_list()

# Find with projection
emails = await User.find(
    User.is_active == True,
    projection_model=EmailOnly  # Pydantic model with only email field
).to_list()

# Pagination
users = await User.find().skip(20).limit(10).to_list()

# Sorting
users = await User.find().sort(-User.created_at).to_list()
```

### Update

```python
# Update single document
user = await User.get(user_id)
user.name = "New Name"
await user.save()

# Update with operators
await user.update({"$set": {"name": "New Name"}})

# Atomic update
await User.find_one(User.id == user_id).update(
    {"$inc": {"login_count": 1}}
)

# Bulk update
await User.find(User.is_active == False).update(
    {"$set": {"deleted_at": datetime.utcnow()}}
)
```

### Delete

```python
# Delete single
user = await User.get(user_id)
await user.delete()

# Delete many
await User.find(User.is_active == False).delete()
```

## Aggregation Pipelines

```python
# Basic aggregation
pipeline = [
    {"$match": {"is_active": True}},
    {"$group": {"_id": "$country", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
results = await User.aggregate(pipeline).to_list()

# Using Beanie's aggregation builder
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import In

class OrderStats(BaseModel):
    user_id: PydanticObjectId
    total_orders: int
    total_spent: float

stats = await Order.find(
    Order.user_id == user_id
).aggregate([
    {"$group": {
        "_id": "$user_id",
        "total_orders": {"$sum": 1},
        "total_spent": {"$sum": "$total"}
    }}
], projection_model=OrderStats).to_list()
```

## Index Strategies

```python
from beanie import Document, Indexed
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT

class Product(Document):
    # Simple index
    sku: Indexed(str, unique=True)

    # Text search index
    name: str
    description: str

    class Settings:
        name = "products"
        indexes = [
            IndexModel([("name", TEXT), ("description", TEXT)]),
            IndexModel([("category", ASCENDING), ("price", DESCENDING)]),
            IndexModel(
                [("created_at", ASCENDING)],
                expireAfterSeconds=86400 * 30  # TTL index: 30 days
            ),
        ]

# Text search
products = await Product.find(
    {"$text": {"$search": "laptop gaming"}}
).to_list()
```

## Transactions

```python
from beanie import Document
from motor.motor_asyncio import AsyncIOMotorClient

async def transfer_credits(from_user_id: str, to_user_id: str, amount: int):
    client = AsyncIOMotorClient(settings.mongo_uri)

    async with await client.start_session() as session:
        async with session.start_transaction():
            from_user = await User.get(from_user_id, session=session)
            to_user = await User.get(to_user_id, session=session)

            if from_user.credits < amount:
                raise InsufficientCredits()

            from_user.credits -= amount
            to_user.credits += amount

            await from_user.save(session=session)
            await to_user.save(session=session)
```

## FastAPI Integration

### Dependency

```python
from beanie import PydanticObjectId
from fastapi import Depends, HTTPException

async def get_user_or_404(user_id: PydanticObjectId) -> User:
    user = await User.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.get("/users/{user_id}")
async def get_user(user: User = Depends(get_user_or_404)):
    return user
```

### Pagination Pattern

```python
from pydantic import BaseModel

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int

async def paginate(
    query,
    page: int = 1,
    per_page: int = 20
) -> PaginatedResponse:
    total = await query.count()
    items = await query.skip((page - 1) * per_page).limit(per_page).to_list()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )

@router.get("/users")
async def list_users(page: int = 1, per_page: int = 20):
    query = User.find(User.is_active == True)
    return await paginate(query, page, per_page)
```

## Testing

```python
import pytest
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie

@pytest.fixture
async def db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["test_db"],
        document_models=[User, Order]
    )
    yield
    # Cleanup
    await User.delete_all()
    await Order.delete_all()

@pytest.mark.asyncio
async def test_create_user(db):
    user = await User(email="test@test.com", name="Test").insert()
    assert user.id is not None

    fetched = await User.get(user.id)
    assert fetched.email == "test@test.com"
```

## Required Packages

```bash
pip install beanie motor
pip install mongomock-motor  # Testing
```