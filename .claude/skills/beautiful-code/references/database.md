# Database Standards

Production-grade database patterns for data integrity and performance.

## Transaction Management

### When to Use Transactions

```typescript
// REQUIRED: Multiple writes that must succeed together
async function transferFunds(from: string, to: string, amount: number): Promise<void> {
    await db.transaction(async (tx) => {
        await tx.account.update({ where: { id: from }, data: { balance: { decrement: amount } } });
        await tx.account.update({ where: { id: to }, data: { balance: { increment: amount } } });
        await tx.auditLog.create({ data: { action: 'transfer', from, to, amount } });
    });
    // All succeed or all rollback
}

// NOT NEEDED: Single write
async function updateUser(id: string, name: string): Promise<User> {
    return db.user.update({ where: { id }, data: { name } });
}
```

### Transaction Isolation Levels

| Level | Dirty Read | Non-Repeatable | Phantom |
|-------|------------|----------------|---------|
| READ UNCOMMITTED | Yes | Yes | Yes |
| READ COMMITTED | No | Yes | Yes |
| REPEATABLE READ | No | No | Yes |
| SERIALIZABLE | No | No | No |

**Default**: READ COMMITTED (most DBs)
**Use SERIALIZABLE**: Financial transactions, inventory

```python
# Python (SQLAlchemy)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

with Session(engine) as session:
    session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
    # ... critical operations
    session.commit()
```

```go
// Go
tx, err := db.BeginTx(ctx, &sql.TxOptions{
    Isolation: sql.LevelSerializable,
})
if err != nil {
    return err
}
defer tx.Rollback()

// ... operations
return tx.Commit()
```

## N+1 Query Prevention

### The Problem

```typescript
// BAD: N+1 queries
const users = await db.user.findMany();
for (const user of users) {
    const orders = await db.order.findMany({ where: { userId: user.id } });
    // 1 query for users + N queries for orders = N+1
}
```

### Solutions

```typescript
// GOOD: Include (JOIN)
const users = await db.user.findMany({
    include: { orders: true }
});

// GOOD: Batch loading (DataLoader pattern)
const ordersByUser = await db.order.findMany({
    where: { userId: { in: users.map(u => u.id) } }
});
const ordersMap = groupBy(ordersByUser, 'userId');
users.forEach(u => u.orders = ordersMap[u.id] || []);

// GOOD: Select only needed fields
const users = await db.user.findMany({
    select: { id: true, name: true, email: true }  // Not loading relations
});
```

```python
# Python (SQLAlchemy)
# BAD
users = session.query(User).all()
for user in users:
    print(user.orders)  # N+1

# GOOD: Eager loading
from sqlalchemy.orm import joinedload
users = session.query(User).options(joinedload(User.orders)).all()

# GOOD: Subquery loading
from sqlalchemy.orm import subqueryload
users = session.query(User).options(subqueryload(User.orders)).all()
```

```go
// Go (GORM)
// BAD
var users []User
db.Find(&users)
for _, u := range users {
    db.Model(&u).Association("Orders").Find(&u.Orders)  // N+1
}

// GOOD: Preload
var users []User
db.Preload("Orders").Find(&users)
```

## Migration Safety

### Safe Migrations (Zero Downtime)

**Expand-Contract Pattern**:
1. **Expand**: Add new column/table (nullable or with default)
2. **Migrate**: Copy data, update application
3. **Contract**: Remove old column/table

```sql
-- Step 1: Add new column (safe - nullable)
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT NULL;

-- Step 2: Backfill data (batched, off-peak)
UPDATE users SET email_verified = true WHERE verified_at IS NOT NULL;

-- Step 3: Make non-nullable (after app handles it)
ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL;

-- Step 4: Drop old column (after app doesn't use it)
ALTER TABLE users DROP COLUMN verified_at;
```

### Unsafe Operations (Require Maintenance Window)

| Operation | Risk | Safe Alternative |
|-----------|------|-----------------|
| DROP COLUMN | Data loss | Deprecate first, drop later |
| ALTER TYPE | Lock table | Add new column, migrate |
| ADD NOT NULL | Fails if NULLs exist | Add nullable, backfill, alter |
| RENAME COLUMN | App breaks | Add alias, migrate, drop |
| ADD INDEX | Locks table | CREATE INDEX CONCURRENTLY |

### Migration Best Practices

```python
# Python (Alembic)
def upgrade():
    # Always use batching for large tables
    connection = op.get_bind()
    connection.execute(text("""
        DO $$
        DECLARE
            batch_size INT := 1000;
            affected INT;
        BEGIN
            LOOP
                UPDATE users
                SET email_verified = true
                WHERE id IN (
                    SELECT id FROM users
                    WHERE email_verified IS NULL
                    AND verified_at IS NOT NULL
                    LIMIT batch_size
                );
                GET DIAGNOSTICS affected = ROW_COUNT;
                EXIT WHEN affected = 0;
                COMMIT;
            END LOOP;
        END $$;
    """))
```

## Connection Pooling

### Configuration

```typescript
// TypeScript (Prisma)
datasource db {
    provider = "postgresql"
    url      = env("DATABASE_URL")
}

// Connection string
// postgresql://user:pass@host:5432/db?connection_limit=20&pool_timeout=10
```

```python
# Python (SQLAlchemy)
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Connections to maintain
    max_overflow=10,       # Additional connections under load
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=1800,     # Recycle connections after 30 min
)
```

```go
// Go
db, err := sql.Open("postgres", connStr)
db.SetMaxOpenConns(20)
db.SetMaxIdleConns(10)
db.SetConnMaxLifetime(30 * time.Minute)
db.SetConnMaxIdleTime(5 * time.Minute)
```

### Pool Size Formula

```
pool_size = (core_count * 2) + effective_spindle_count
```

For SSD with 4 cores: `(4 * 2) + 1 = 9` connections

## Query Safety

### Timeouts

```typescript
// TypeScript (Prisma)
const user = await prisma.$queryRaw`
    SELECT * FROM users WHERE id = ${id}
`.timeout(5000);  // 5 second timeout
```

```python
# Python
from sqlalchemy import text

result = session.execute(
    text("SELECT * FROM users WHERE id = :id"),
    {"id": user_id},
    execution_options={"timeout": 5}
)
```

```go
// Go
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

row := db.QueryRowContext(ctx, "SELECT * FROM users WHERE id = $1", id)
```

### Pagination

```typescript
// NEVER: Load all records
const all = await db.user.findMany();  // Error - memory bomb

// GOOD: Cursor pagination (best for large datasets)
const users = await db.user.findMany({
    take: 20,
    skip: 1,  // Skip the cursor
    cursor: { id: lastId },
    orderBy: { id: 'asc' },
});

// OK: Offset pagination (for small datasets)
const users = await db.user.findMany({
    take: 20,
    skip: (page - 1) * 20,
});
```

## Soft Deletes

```typescript
// Schema
model User {
    id        String    @id
    deletedAt DateTime? // NULL = active
    // ...
}

// Query (always filter)
const users = await db.user.findMany({
    where: { deletedAt: null }  // Active only
});

// "Delete"
await db.user.update({
    where: { id },
    data: { deletedAt: new Date() }
});
```

## Audit Logging

```typescript
// Automatic timestamps
model User {
    id        String   @id
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
    createdBy String?
    updatedBy String?
}

// Audit trail table
model AuditLog {
    id        String   @id @default(uuid())
    tableName String
    recordId  String
    action    String   // CREATE, UPDATE, DELETE
    oldData   Json?
    newData   Json?
    userId    String
    timestamp DateTime @default(now())
}
```

## Anti-Patterns

| Bad | Good | Why |
|-----|------|-----|
| No transactions for multi-write | Wrap in transaction | Data inconsistency |
| SELECT * | Select specific fields | Performance, security |
| No query timeout | Always set timeout | Hung queries |
| Unbounded queries | Always paginate | Memory explosion |
| No connection pooling | Use pool | Connection exhaustion |
| Immediate hard deletes | Soft delete first | Data recovery |
| No migration strategy | Expand-contract | Zero downtime |
| N+1 in loops | Eager load or batch | Performance |