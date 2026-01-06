# Microservices & Event-Driven Architecture

## Celery Integration

### Configuration

```python
from celery import Celery
from pydantic_settings import BaseSettings

class CelerySettings(BaseSettings):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"

settings = CelerySettings()

celery_app = Celery(
    "tasks",
    broker=settings.broker_url,
    backend=settings.result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min hard limit
    task_soft_time_limit=240,  # 4 min soft limit
    worker_prefetch_multiplier=1,  # One task at a time
    task_acks_late=True,  # Acknowledge after completion
)
```

### Task Definitions

```python
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

@shared_task(bind=True, max_retries=3)
def send_email(self, to: str, subject: str, body: str):
    try:
        email_service.send(to, subject, body)
    except ConnectionError as exc:
        raise self.retry(exc=exc, countdown=60)  # Retry in 60s

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True)
def process_order(self, order_id: int):
    """Process order with automatic retry and exponential backoff."""
    try:
        order = Order.get(order_id)
        order.process()
    except SoftTimeLimitExceeded:
        # Graceful handling of timeout
        order.mark_as_failed("Processing timeout")
        raise

# Async task from FastAPI
@router.post("/orders")
async def create_order(order: OrderCreate):
    db_order = await order_service.create(order)

    # Dispatch async task
    process_order.delay(db_order.id)

    return {"order_id": db_order.id, "status": "processing"}
```

### Task Routing

```python
celery_app.conf.task_routes = {
    "tasks.email.*": {"queue": "email"},
    "tasks.orders.*": {"queue": "orders"},
    "tasks.reports.*": {"queue": "reports"},
}

# Run workers for specific queues
# celery -A tasks worker -Q email -c 2
# celery -A tasks worker -Q orders -c 4
```

### Celery Beat (Scheduling)

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "tasks.cleanup_sessions",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
    "generate-daily-report": {
        "task": "tasks.generate_report",
        "schedule": crontab(minute=0, hour=8),  # 8 AM daily
        "args": ("daily",),
    },
    "health-check": {
        "task": "tasks.health_check",
        "schedule": 60.0,  # Every 60 seconds
    },
}
```

## RabbitMQ Integration

### Publisher

```python
import aio_pika
import json
from pydantic import BaseModel

class EventPublisher:
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self._connection = None
        self._channel = None

    async def connect(self):
        self._connection = await aio_pika.connect_robust(self.connection_url)
        self._channel = await self._connection.channel()

    async def publish(
        self,
        exchange: str,
        routing_key: str,
        message: BaseModel | dict,
        headers: dict = None
    ):
        if isinstance(message, BaseModel):
            body = message.model_dump_json().encode()
        else:
            body = json.dumps(message).encode()

        await self._channel.default_exchange.publish(
            aio_pika.Message(
                body=body,
                headers=headers or {},
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )

    async def close(self):
        if self._connection:
            await self._connection.close()

# Usage
publisher = EventPublisher("amqp://guest:guest@localhost/")

@app.on_event("startup")
async def startup():
    await publisher.connect()

@app.on_event("shutdown")
async def shutdown():
    await publisher.close()

@router.post("/orders")
async def create_order(order: OrderCreate):
    db_order = await order_service.create(order)

    await publisher.publish(
        exchange="",
        routing_key="order.created",
        message=OrderCreatedEvent(order_id=db_order.id, total=db_order.total)
    )

    return db_order
```

### Consumer

```python
import asyncio
import aio_pika

class EventConsumer:
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.handlers: dict[str, callable] = {}

    def on(self, routing_key: str):
        def decorator(func):
            self.handlers[routing_key] = func
            return func
        return decorator

    async def start(self):
        connection = await aio_pika.connect_robust(self.connection_url)
        channel = await connection.channel()

        for routing_key, handler in self.handlers.items():
            queue = await channel.declare_queue(routing_key, durable=True)

            async def process_message(message: aio_pika.IncomingMessage):
                async with message.process():
                    data = json.loads(message.body)
                    await handler(data)

            await queue.consume(process_message)

        # Keep running
        await asyncio.Future()

consumer = EventConsumer("amqp://guest:guest@localhost/")

@consumer.on("order.created")
async def handle_order_created(event: dict):
    order_id = event["order_id"]
    await inventory_service.reserve(order_id)
    await notification_service.send(order_id)

# Run: python -m consumer
```

## Kafka Integration

### Producer

```python
from aiokafka import AIOKafkaProducer
import json

class KafkaProducer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self._producer = None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        await self._producer.start()

    async def send(self, topic: str, value: dict, key: str = None):
        await self._producer.send_and_wait(
            topic,
            value=value,
            key=key.encode() if key else None,
        )

    async def stop(self):
        await self._producer.stop()

producer = KafkaProducer("localhost:9092")

@router.post("/events")
async def create_event(event: EventCreate):
    await producer.send(
        topic="events",
        value=event.model_dump(),
        key=str(event.user_id)
    )
```

### Consumer

```python
from aiokafka import AIOKafkaConsumer

class KafkaConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str, topics: list[str]):
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode()),
            auto_offset_reset="earliest",
        )

    async def start(self):
        await self.consumer.start()

    async def consume(self):
        async for message in self.consumer:
            yield message

    async def stop(self):
        await self.consumer.stop()

# Usage
consumer = KafkaConsumer("localhost:9092", "my-group", ["events"])

async def process_events():
    await consumer.start()
    async for message in consumer.consume():
        await handle_event(message.value)
```

## Saga Pattern

### Orchestrator-Based Saga

```python
from enum import Enum
from dataclasses import dataclass

class SagaStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    FAILED = "failed"

@dataclass
class SagaStep:
    name: str
    action: callable
    compensation: callable

class OrderSaga:
    def __init__(self, db: AsyncSession, publisher: EventPublisher):
        self.db = db
        self.publisher = publisher
        self.steps: list[SagaStep] = []
        self.completed_steps: list[str] = []

    def add_step(self, name: str, action: callable, compensation: callable):
        self.steps.append(SagaStep(name, action, compensation))

    async def execute(self, context: dict) -> bool:
        try:
            for step in self.steps:
                await step.action(context)
                self.completed_steps.append(step.name)
            return True

        except Exception as e:
            await self.compensate(context)
            raise

    async def compensate(self, context: dict):
        # Execute compensations in reverse order
        for step_name in reversed(self.completed_steps):
            step = next(s for s in self.steps if s.name == step_name)
            try:
                await step.compensation(context)
            except Exception as e:
                logger.error(f"Compensation failed for {step_name}: {e}")

# Usage
async def create_order_saga(order: Order):
    saga = OrderSaga(db, publisher)

    saga.add_step(
        "reserve_inventory",
        action=lambda ctx: inventory_service.reserve(ctx["order_id"]),
        compensation=lambda ctx: inventory_service.release(ctx["order_id"])
    )

    saga.add_step(
        "charge_payment",
        action=lambda ctx: payment_service.charge(ctx["order_id"]),
        compensation=lambda ctx: payment_service.refund(ctx["order_id"])
    )

    saga.add_step(
        "create_shipment",
        action=lambda ctx: shipping_service.create(ctx["order_id"]),
        compensation=lambda ctx: shipping_service.cancel(ctx["order_id"])
    )

    await saga.execute({"order_id": order.id})
```

## Circuit Breaker

### Tenacity Implementation

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    CircuitBreaker,
)
import httpx

# Simple retry with exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
)
async def call_external_service(data: dict):
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post("https://external-api.com/endpoint", json=data)
        response.raise_for_status()
        return response.json()

# Circuit breaker pattern
class ServiceCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise CircuitOpenError("Circuit is open")

        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"

            raise

payment_circuit = ServiceCircuitBreaker()

async def charge_payment(order_id: int):
    return await payment_circuit.call(payment_service.charge, order_id)
```

## Autoscaling with HPA/KEDA

### Kubernetes HPA

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
```

### KEDA for Event-Driven Scaling

```yaml
# kubernetes/keda-scaler.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: celery-worker-scaler
spec:
  scaleTargetRef:
    name: celery-worker
  minReplicaCount: 1
  maxReplicaCount: 20
  triggers:
    - type: rabbitmq
      metadata:
        host: amqp://guest:guest@rabbitmq:5672/
        queueName: orders
        queueLength: "10"  # Scale when queue > 10 messages

    - type: redis
      metadata:
        address: redis:6379
        listName: celery
        listLength: "5"
```

## CQRS Basics

**Warning: CQRS adds significant complexity. Only use when you have clear read/write asymmetry or need event sourcing.**

```python
# Write side (Commands)
class OrderCommandService:
    async def create_order(self, command: CreateOrderCommand) -> str:
        order = Order.from_command(command)
        await self.repository.save(order)

        # Publish event for read side
        await self.publisher.publish(
            "order.created",
            OrderCreatedEvent(order_id=order.id, data=order.to_dict())
        )

        return order.id

# Read side (Queries)
class OrderQueryService:
    async def get_order(self, order_id: str) -> OrderReadModel:
        # Read from denormalized read store
        return await self.read_store.get(order_id)

    async def list_orders(self, user_id: str) -> list[OrderSummary]:
        # Optimized for queries
        return await self.read_store.list_by_user(user_id)

# Event handler updates read model
@consumer.on("order.created")
async def update_read_model(event: dict):
    await read_store.upsert(OrderReadModel.from_event(event))
```

## Required Packages

```bash
# Celery
pip install celery[redis]
pip install flower  # Monitoring

# RabbitMQ
pip install aio-pika

# Kafka
pip install aiokafka

# Resilience
pip install tenacity

# HTTP Client
pip install httpx
```