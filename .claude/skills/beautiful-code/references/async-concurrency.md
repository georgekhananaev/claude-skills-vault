# Async & Concurrency Standards

Production-grade patterns for asynchronous and concurrent code.

## Resource Lifecycle

### Always Clean Up Resources

```typescript
// TypeScript - try/finally
const connection = await pool.connect();
try {
    await connection.query('...');
} finally {
    connection.release();  // Always runs
}

// TypeScript - using (Stage 3 proposal / TypeScript 5.2+)
await using connection = await pool.connect();
await connection.query('...');
// Automatically released
```

```python
# Python - context managers (ALWAYS use)
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()
# Automatically closed

# BAD: Manual management
session = aiohttp.ClientSession()
response = await session.get(url)  # Leaks if exception
await session.close()
```

```go
// Go - defer for cleanup
file, err := os.Open(path)
if err != nil {
    return err
}
defer file.Close()  // Always runs

// Multiple defers - LIFO order
func process() error {
    db := openDB()
    defer db.Close()

    tx, _ := db.Begin()
    defer tx.Rollback()  // Safe - no-op if committed

    // ... work ...
    return tx.Commit()
}
```

```rust
// Rust - Drop trait (automatic)
{
    let file = File::open(path)?;
    // file.read_to_string(...)?
}  // file automatically closed here

// For async - use async_trait
impl Drop for Connection {
    fn drop(&mut self) {
        // Sync cleanup only - for async use explicit close()
    }
}
```

## Async Patterns

### TypeScript (Promises)

```typescript
// GOOD: Concurrent execution
const [users, orders, products] = await Promise.all([
    fetchUsers(),
    fetchOrders(),
    fetchProducts(),
]);

// GOOD: Concurrent with error handling
const results = await Promise.allSettled([
    fetchUsers(),
    fetchOrders(),
]);
results.forEach(r => {
    if (r.status === 'fulfilled') console.log(r.value);
    else console.error(r.reason);
});

// BAD: Sequential when not needed
const users = await fetchUsers();    // Wait
const orders = await fetchOrders();  // Then wait
const products = await fetchProducts();  // Then wait

// BAD: Floating promise (not awaited)
fetchUsers();  // Error - no await, unhandled rejection
```

### Python (asyncio)

```python
# GOOD: Concurrent tasks
async def fetch_all():
    users, orders = await asyncio.gather(
        fetch_users(),
        fetch_orders(),
        return_exceptions=True  # Don't fail fast
    )

# GOOD: Task groups (Python 3.11+)
async def fetch_all():
    async with asyncio.TaskGroup() as tg:
        users_task = tg.create_task(fetch_users())
        orders_task = tg.create_task(fetch_orders())
    return users_task.result(), orders_task.result()

# BAD: Blocking the event loop
async def bad():
    time.sleep(1)  # BLOCKS entire loop!
    requests.get(url)  # BLOCKS entire loop!

# GOOD: Non-blocking
async def good():
    await asyncio.sleep(1)  # Yields control
    async with aiohttp.ClientSession() as s:
        await s.get(url)  # Yields control

# Run blocking code in thread pool
result = await asyncio.to_thread(blocking_function, arg1, arg2)
```

### Go (Goroutines)

```go
// GOOD: Structured concurrency with errgroup
import "golang.org/x/sync/errgroup"

func fetchAll(ctx context.Context) ([]User, []Order, error) {
    g, ctx := errgroup.WithContext(ctx)

    var users []User
    var orders []Order

    g.Go(func() error {
        var err error
        users, err = fetchUsers(ctx)
        return err
    })

    g.Go(func() error {
        var err error
        orders, err = fetchOrders(ctx)
        return err
    })

    if err := g.Wait(); err != nil {
        return nil, nil, err
    }
    return users, orders, nil
}

// BAD: Goroutine leak
func bad() {
    go func() {
        for {
            // No way to stop this!
        }
    }()
}

// GOOD: Cancellation via context
func good(ctx context.Context) {
    go func() {
        for {
            select {
            case <-ctx.Done():
                return  // Clean exit
            default:
                // Work
            }
        }
    }()
}
```

### Rust (Tokio)

```rust
// GOOD: Concurrent tasks
async fn fetch_all() -> Result<(Users, Orders), Error> {
    let (users, orders) = tokio::try_join!(
        fetch_users(),
        fetch_orders()
    )?;
    Ok((users, orders))
}

// GOOD: Spawn with handle
let handle = tokio::spawn(async {
    expensive_computation().await
});
let result = handle.await?;

// BAD: Blocking in async context
async fn bad() {
    std::thread::sleep(Duration::from_secs(1));  // BLOCKS runtime!
}

// GOOD: Use tokio's async sleep
async fn good() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}

// For CPU-bound work
let result = tokio::task::spawn_blocking(|| {
    expensive_sync_computation()
}).await?;
```

## Timeout Handling

### Always Set Timeouts

```typescript
// TypeScript
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 5000);

try {
    const response = await fetch(url, { signal: controller.signal });
} finally {
    clearTimeout(timeout);
}

// With axios
const response = await axios.get(url, { timeout: 5000 });
```

```python
# Python
async with asyncio.timeout(5):  # Python 3.11+
    result = await slow_operation()

# Or with wait_for
result = await asyncio.wait_for(slow_operation(), timeout=5)
```

```go
// Go - context timeout
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

result, err := slowOperation(ctx)
if errors.Is(err, context.DeadlineExceeded) {
    // Handle timeout
}
```

```rust
// Rust
let result = tokio::time::timeout(
    Duration::from_secs(5),
    slow_operation()
).await?;
```

## Rate Limiting & Backpressure

### Semaphore Pattern

```typescript
// TypeScript - limit concurrent operations
import { Semaphore } from 'async-mutex';

const semaphore = new Semaphore(10);  // Max 10 concurrent

async function processAll(items: Item[]): Promise<void> {
    await Promise.all(items.map(async (item) => {
        const [, release] = await semaphore.acquire();
        try {
            await processItem(item);
        } finally {
            release();
        }
    }));
}
```

```python
# Python
semaphore = asyncio.Semaphore(10)

async def process_item(item):
    async with semaphore:
        await do_work(item)

await asyncio.gather(*[process_item(i) for i in items])
```

```go
// Go - worker pool
func processAll(ctx context.Context, items []Item) error {
    sem := make(chan struct{}, 10)  // Buffered channel as semaphore
    g, ctx := errgroup.WithContext(ctx)

    for _, item := range items {
        item := item
        g.Go(func() error {
            sem <- struct{}{}        // Acquire
            defer func() { <-sem }() // Release
            return processItem(ctx, item)
        })
    }
    return g.Wait()
}
```

## Deadlock Prevention

### Lock Ordering

```go
// BAD: Deadlock risk
func transferBad(from, to *Account, amount int) {
    from.mu.Lock()  // Thread 1: locks A
    to.mu.Lock()    // Thread 1: waits for B (Thread 2 has B, waits for A)
    // ... deadlock
}

// GOOD: Consistent lock ordering
func transferGood(from, to *Account, amount int) {
    // Always lock lower ID first
    first, second := from, to
    if from.ID > to.ID {
        first, second = to, from
    }
    first.mu.Lock()
    second.mu.Lock()
    defer first.mu.Unlock()
    defer second.mu.Unlock()
    // ... safe
}
```

### Avoid Holding Locks During I/O

```go
// BAD: Lock held during network call
func bad(mu *sync.Mutex) {
    mu.Lock()
    defer mu.Unlock()
    response, _ := http.Get(url)  // Network I/O while locked!
}

// GOOD: Minimize lock scope
func good(mu *sync.Mutex) {
    response, _ := http.Get(url)  // No lock during I/O

    mu.Lock()
    defer mu.Unlock()
    // Quick update only
    cache[key] = response
}
```

## Channel Patterns (Go)

```go
// Fan-out: One producer, multiple consumers
func fanOut(in <-chan int, workers int) []<-chan int {
    outs := make([]<-chan int, workers)
    for i := 0; i < workers; i++ {
        out := make(chan int)
        outs[i] = out
        go func() {
            for n := range in {
                out <- process(n)
            }
            close(out)
        }()
    }
    return outs
}

// Fan-in: Multiple producers, one consumer
func fanIn(channels ...<-chan int) <-chan int {
    out := make(chan int)
    var wg sync.WaitGroup

    for _, ch := range channels {
        wg.Add(1)
        go func(c <-chan int) {
            defer wg.Done()
            for n := range c {
                out <- n
            }
        }(ch)
    }

    go func() {
        wg.Wait()
        close(out)
    }()

    return out
}
```

## Anti-Patterns

| Bad | Good | Why |
|-----|------|-----|
| No cleanup on error | try/finally, defer, Drop | Resource leaks |
| Blocking in async | Use async I/O | Blocks event loop |
| Goroutine without cancel | Pass context | Goroutine leaks |
| No timeout | Always set timeout | Hung operations |
| Unbounded concurrency | Semaphore/pool | Resource exhaustion |
| Lock during I/O | Minimize lock scope | Deadlocks, contention |
| Fire and forget async | Always await/handle | Lost errors |