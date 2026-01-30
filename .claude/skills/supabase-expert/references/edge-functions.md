# Edge Functions

Server-side TypeScript/JavaScript functions running on Deno at the edge, globally distributed.

## When to Use

| Use Case | Edge Functions | Database Functions |
|----------|---------------|-------------------|
| Webhooks | ✅ | ❌ |
| Third-party APIs | ✅ | Limited |
| File processing | ✅ | ❌ |
| Scheduled jobs | ✅ | Via pg_cron |
| Complex auth | ✅ | ❌ |
| Heavy compute | ✅ | ❌ |
| Simple DB logic | ❌ | ✅ |

## Project Structure

```
supabase/
└── functions/
    ├── _shared/           # Shared utilities
    │   ├── cors.ts
    │   ├── supabase.ts
    │   └── validators.ts
    ├── hello-world/
    │   └── index.ts
    ├── stripe-webhook/
    │   └── index.ts
    └── send-email/
        └── index.ts
```

## Basic Function

```typescript
// supabase/functions/hello-world/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';

serve(async (req: Request) => {
  const { name } = await req.json();

  return new Response(
    JSON.stringify({ message: `Hello ${name}!` }),
    { headers: { 'Content-Type': 'application/json' } }
  );
});
```

## With Supabase Client

```typescript
// supabase/functions/_shared/supabase.ts
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

export const supabaseAdmin = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
);

export const getSupabaseClient = (req: Request) => {
  const authHeader = req.headers.get('Authorization');
  return createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!,
    {
      global: { headers: { Authorization: authHeader! } }
    }
  );
};
```

```typescript
// supabase/functions/get-profile/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { getSupabaseClient } from '../_shared/supabase.ts';

serve(async (req: Request) => {
  const supabase = getSupabaseClient(req);

  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return new Response('Unauthorized', { status: 401 });
  }

  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single();

  return new Response(JSON.stringify(profile), {
    headers: { 'Content-Type': 'application/json' }
  });
});
```

## CORS Handling

```typescript
// supabase/functions/_shared/cors.ts
export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

export const handleCors = (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  return null;
};
```

```typescript
// Usage in function
import { corsHeaders, handleCors } from '../_shared/cors.ts';

serve(async (req: Request) => {
  const corsResponse = handleCors(req);
  if (corsResponse) return corsResponse;

  // Process request...

  return new Response(JSON.stringify(data), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
});
```

## Webhook Handler (Stripe Example)

```typescript
// supabase/functions/stripe-webhook/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import Stripe from 'https://esm.sh/stripe@13?target=deno';
import { supabaseAdmin } from '../_shared/supabase.ts';

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY')!, {
  apiVersion: '2023-10-16',
  httpClient: Stripe.createFetchHttpClient(),
});

const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET')!;

serve(async (req: Request) => {
  const signature = req.headers.get('stripe-signature')!;
  const body = await req.text();

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    return new Response(`Webhook Error: ${err.message}`, { status: 400 });
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;

      await supabaseAdmin
        .from('orders')
        .update({ status: 'paid', stripe_session_id: session.id })
        .eq('id', session.metadata?.order_id);
      break;
    }

    case 'customer.subscription.updated': {
      const subscription = event.data.object as Stripe.Subscription;

      await supabaseAdmin
        .from('subscriptions')
        .update({
          status: subscription.status,
          current_period_end: new Date(subscription.current_period_end * 1000)
        })
        .eq('stripe_subscription_id', subscription.id);
      break;
    }
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { 'Content-Type': 'application/json' }
  });
});
```

## Scheduled Functions (Cron)

```sql
-- Create schedule in database
SELECT cron.schedule(
  'daily-cleanup',
  '0 3 * * *',  -- 3 AM daily
  $$
  SELECT net.http_post(
    url := 'https://your-project.supabase.co/functions/v1/cleanup',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || vault.read_secret('edge_function_token')
    ),
    body := '{}'::jsonb
  )
  $$
);

-- Store token in vault
SELECT vault.create_secret('edge_function_token', 'your-service-role-key');
```

```typescript
// supabase/functions/cleanup/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { supabaseAdmin } from '../_shared/supabase.ts';

serve(async (req: Request) => {
  // Verify it's a cron call (from internal network)
  const authHeader = req.headers.get('Authorization');
  if (!authHeader?.includes(Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!)) {
    return new Response('Unauthorized', { status: 401 });
  }

  // Cleanup old records
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const { count } = await supabaseAdmin
    .from('logs')
    .delete()
    .lt('created_at', thirtyDaysAgo.toISOString());

  console.log(`Deleted ${count} old log entries`);

  return new Response(JSON.stringify({ deleted: count }));
});
```

## Background Jobs with Queues

```sql
-- Create jobs table
CREATE TABLE background_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
  attempts INT DEFAULT 0,
  max_attempts INT DEFAULT 3,
  created_at TIMESTAMPTZ DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  error TEXT
);

-- Index for job processing
CREATE INDEX idx_jobs_pending ON background_jobs(created_at)
  WHERE status = 'pending';
```

```typescript
// supabase/functions/process-jobs/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { supabaseAdmin } from '../_shared/supabase.ts';

serve(async (req: Request) => {
  // Claim a job
  const { data: job, error } = await supabaseAdmin
    .from('background_jobs')
    .update({
      status: 'processing',
      started_at: new Date().toISOString(),
      attempts: supabaseAdmin.sql`attempts + 1`
    })
    .eq('status', 'pending')
    .lt('attempts', supabaseAdmin.sql`max_attempts`)
    .order('created_at', { ascending: true })
    .limit(1)
    .select()
    .single();

  if (!job) {
    return new Response(JSON.stringify({ message: 'No jobs' }));
  }

  try {
    // Process based on job type
    switch (job.type) {
      case 'send_email':
        await sendEmail(job.payload);
        break;
      case 'generate_report':
        await generateReport(job.payload);
        break;
    }

    // Mark completed
    await supabaseAdmin
      .from('background_jobs')
      .update({ status: 'completed', completed_at: new Date().toISOString() })
      .eq('id', job.id);

  } catch (err) {
    // Mark failed
    await supabaseAdmin
      .from('background_jobs')
      .update({
        status: job.attempts >= job.max_attempts ? 'failed' : 'pending',
        error: err.message
      })
      .eq('id', job.id);
  }

  return new Response(JSON.stringify({ processed: job.id }));
});
```

## Performance Best Practices

### 1. Minimize Cold Starts

```typescript
// Import at top level (cached between invocations)
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

// Initialize outside handler
const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
);

serve(async (req) => {
  // Use pre-initialized client
});
```

### 2. Keep Functions Focused

```typescript
// BAD: One function does everything
// GOOD: Separate functions for separate concerns
// - /process-payment
// - /send-notification
// - /generate-invoice
```

### 3. Use Streaming for Large Responses

```typescript
serve(async (req) => {
  const stream = new ReadableStream({
    async start(controller) {
      for await (const chunk of processLargeData()) {
        controller.enqueue(new TextEncoder().encode(JSON.stringify(chunk) + '\n'));
      }
      controller.close();
    }
  });

  return new Response(stream, {
    headers: { 'Content-Type': 'application/x-ndjson' }
  });
});
```

## Local Development

```bash
# Start local Supabase
supabase start

# Serve functions locally
supabase functions serve

# Serve specific function with env file
supabase functions serve hello-world --env-file .env.local

# Test with curl
curl -X POST http://localhost:54321/functions/v1/hello-world \
  -H "Authorization: Bearer $ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

## Deployment

```bash
# Deploy single function
supabase functions deploy hello-world

# Deploy all functions
supabase functions deploy

# Set secrets
supabase secrets set STRIPE_SECRET_KEY=sk_live_xxx

# List secrets
supabase secrets list
```

## Monitoring

```typescript
// Log for observability
console.log(JSON.stringify({
  level: 'info',
  function: 'stripe-webhook',
  event: event.type,
  timestamp: new Date().toISOString()
}));

// View logs
// supabase functions logs hello-world
// Or in Dashboard: Edge Functions > Logs
```
