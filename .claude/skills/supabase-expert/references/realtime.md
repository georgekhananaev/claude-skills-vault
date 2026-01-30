# Realtime

Supabase Realtime enables live data synchronization via WebSockets. Three main features: Broadcast, Presence, and Postgres Changes.

## Channel Types

| Type | Use Case | Data Source |
|------|----------|-------------|
| Broadcast | Chat, notifications, live updates | Client messages |
| Presence | Online users, typing indicators | Client state |
| Postgres Changes | Database sync, live feeds | Database CDC |

## Broadcast

Send messages between clients without database involvement.

```typescript
// Subscribe to channel
const channel = supabase.channel('room-1');

channel
  .on('broadcast', { event: 'cursor-move' }, (payload) => {
    console.log('Cursor moved:', payload);
  })
  .subscribe();

// Send message
channel.send({
  type: 'broadcast',
  event: 'cursor-move',
  payload: { x: 100, y: 200, userId: 'user-123' }
});
```

### Broadcast Use Cases

- Real-time cursors (Figma-style)
- Chat messages (before persistence)
- Game state updates
- Live notifications

## Presence

Track and sync client state across users.

```typescript
const channel = supabase.channel('room-1');

// Track presence
channel
  .on('presence', { event: 'sync' }, () => {
    const state = channel.presenceState();
    console.log('Online users:', Object.keys(state));
  })
  .on('presence', { event: 'join' }, ({ key, newPresences }) => {
    console.log('User joined:', newPresences);
  })
  .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
    console.log('User left:', leftPresences);
  })
  .subscribe(async (status) => {
    if (status === 'SUBSCRIBED') {
      await channel.track({
        user_id: 'user-123',
        username: 'john_doe',
        online_at: new Date().toISOString()
      });
    }
  });

// Update presence
await channel.track({
  user_id: 'user-123',
  username: 'john_doe',
  status: 'typing'
});

// Remove presence (on logout)
await channel.untrack();
```

### Presence Use Cases

- Online user indicators
- Typing indicators
- Live collaboration (who's viewing)
- Game lobbies

## Postgres Changes (CDC)

Listen to database changes in real-time via Change Data Capture.

### Enable Realtime on Table

```sql
-- Enable in Dashboard: Database > Replication
-- Or via SQL:
ALTER PUBLICATION supabase_realtime ADD TABLE posts;

-- Enable specific events only
ALTER PUBLICATION supabase_realtime ADD TABLE posts
  WITH (publish = 'insert, update');
```

### Subscribe to Changes

```typescript
const channel = supabase
  .channel('db-changes')
  .on(
    'postgres_changes',
    {
      event: '*',           // INSERT, UPDATE, DELETE, or *
      schema: 'public',
      table: 'posts'
    },
    (payload) => {
      console.log('Change received:', payload);
      // payload.eventType: 'INSERT' | 'UPDATE' | 'DELETE'
      // payload.new: new row data
      // payload.old: old row data (UPDATE/DELETE only)
    }
  )
  .subscribe();
```

### Filtered Subscriptions

```typescript
// Only listen to specific user's posts
const channel = supabase
  .channel('user-posts')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'posts',
      filter: 'author_id=eq.user-123'
    },
    (payload) => {
      console.log('New post:', payload.new);
    }
  )
  .subscribe();

// Multiple filters
const channel = supabase
  .channel('priority-items')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'items',
      filter: 'status=eq.active'
    },
    handleActiveItems
  )
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'items',
      filter: 'priority=eq.high'
    },
    handleHighPriority
  )
  .subscribe();
```

## Realtime Authorization

### RLS for Realtime

Realtime respects RLS policies. Users only receive changes they're authorized to see.

```sql
-- Enable RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Users can only see messages in their rooms
CREATE POLICY "users_see_room_messages" ON messages
  FOR SELECT USING (
    room_id IN (
      SELECT room_id FROM room_members WHERE user_id = auth.uid()
    )
  );
```

### Broadcast/Presence Authorization

```typescript
// Server-side: Create authorized channel token
const { data, error } = await supabase.auth.admin.generateLink({
  type: 'magiclink',
  email: user.email,
  options: {
    data: {
      channel_access: ['room-1', 'room-2']
    }
  }
});

// Client checks authorization
const channel = supabase.channel('room-1', {
  config: {
    broadcast: { self: true },
    presence: { key: userId }
  }
});
```

## Performance Optimization

### 1. Enable Only What You Need

```sql
-- BAD: Enable realtime on entire table
ALTER PUBLICATION supabase_realtime ADD TABLE users;

-- GOOD: Enable only necessary events
ALTER PUBLICATION supabase_realtime ADD TABLE posts
  WITH (publish = 'insert');  -- Only INSERTs, not updates/deletes
```

### 2. Use Filters

```typescript
// BAD: Subscribe to all posts, filter client-side
.on('postgres_changes', { event: '*', table: 'posts' }, ...)

// GOOD: Filter at subscription level
.on('postgres_changes', {
  event: 'INSERT',
  table: 'posts',
  filter: 'author_id=eq.${userId}'
}, ...)
```

### 3. Debounce Updates

```typescript
import { debounce } from 'lodash';

const debouncedUpdate = debounce((data) => {
  setItems(data);
}, 100);

channel.on('postgres_changes', { ... }, (payload) => {
  debouncedUpdate(payload.new);
});
```

### 4. Cleanup Subscriptions

```typescript
// React example
useEffect(() => {
  const channel = supabase.channel('my-channel').subscribe();

  return () => {
    supabase.removeChannel(channel);
  };
}, []);
```

## Common Patterns

### Live Feed

```typescript
const [posts, setPosts] = useState<Post[]>([]);

useEffect(() => {
  // Initial fetch
  supabase.from('posts').select('*').order('created_at', { ascending: false })
    .then(({ data }) => setPosts(data || []));

  // Subscribe to new posts
  const channel = supabase
    .channel('live-feed')
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'posts'
    }, (payload) => {
      setPosts((current) => [payload.new as Post, ...current]);
    })
    .subscribe();

  return () => { supabase.removeChannel(channel); };
}, []);
```

### Chat Room

```typescript
const [messages, setMessages] = useState<Message[]>([]);
const [onlineUsers, setOnlineUsers] = useState<string[]>([]);

useEffect(() => {
  const channel = supabase.channel(`room:${roomId}`);

  // Messages
  channel.on('broadcast', { event: 'message' }, ({ payload }) => {
    setMessages((m) => [...m, payload]);
  });

  // Online users
  channel.on('presence', { event: 'sync' }, () => {
    const state = channel.presenceState();
    setOnlineUsers(Object.values(state).flat().map((p: any) => p.username));
  });

  channel.subscribe(async (status) => {
    if (status === 'SUBSCRIBED') {
      await channel.track({ username: currentUser.name });
    }
  });

  return () => { supabase.removeChannel(channel); };
}, [roomId]);

const sendMessage = (text: string) => {
  channel.send({
    type: 'broadcast',
    event: 'message',
    payload: { text, user: currentUser.name, timestamp: Date.now() }
  });

  // Also persist to database
  supabase.from('messages').insert({ room_id: roomId, text, user_id: currentUser.id });
};
```

### Typing Indicator

```typescript
const [typingUsers, setTypingUsers] = useState<string[]>([]);

useEffect(() => {
  const channel = supabase.channel(`typing:${roomId}`);

  channel.on('presence', { event: 'sync' }, () => {
    const state = channel.presenceState();
    const typing = Object.values(state)
      .flat()
      .filter((p: any) => p.is_typing)
      .map((p: any) => p.username);
    setTypingUsers(typing);
  });

  channel.subscribe();

  return () => { supabase.removeChannel(channel); };
}, [roomId]);

const setTyping = async (isTyping: boolean) => {
  await channel.track({
    username: currentUser.name,
    is_typing: isTyping
  });
};
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No events received | RLS blocking | Check RLS policies allow SELECT |
| Missing old data on UPDATE | Replica identity | `ALTER TABLE x REPLICA IDENTITY FULL;` |
| High latency | Too many subscriptions | Consolidate channels, use filters |
| Connection drops | Network issues | Implement reconnection logic |

### Debug Realtime

```typescript
// Enable debug logging
const channel = supabase.channel('debug', {
  config: { log_level: 'debug' }
});

// Check connection status
channel.subscribe((status, err) => {
  console.log('Status:', status);
  if (err) console.error('Error:', err);
});
```

## Limitations

- Max 200 concurrent connections per client (configurable)
- Broadcast messages: 1MB max payload
- Presence state: 1MB max per user
- Postgres Changes: Subject to RLS performance
