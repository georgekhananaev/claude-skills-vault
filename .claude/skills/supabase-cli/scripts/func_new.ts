#!/usr/bin/env bun
/**
 * Edge Function Creator
 * Creates a new Edge Function with templates.
 *
 * Usage:
 *   bun func_new.ts <function-name> [--template <template>]
 *
 * Templates:
 *   basic    - Minimal function (default)
 *   cors     - Function with CORS headers
 *   webhook  - Webhook handler with signature verification
 *   cron     - Scheduled function
 *
 * Example:
 *   bun func_new.ts hello-world
 *   bun func_new.ts stripe-webhook --template webhook
 */

import { existsSync, mkdirSync, writeFileSync } from "fs";
import { join } from "path";

const args = process.argv.slice(2);

// Get function name
const name = args.filter((a) => !a.startsWith("--"))[0];

// Get template
let template = "basic";
const templateIndex = args.findIndex((a) => a === "--template");
if (templateIndex !== -1 && args[templateIndex + 1]) {
  template = args[templateIndex + 1];
}

if (!name) {
  console.error("Usage: bun func_new.ts <function-name> [--template <template>]");
  console.error("\nTemplates:");
  console.error("  basic    - Minimal function (default)");
  console.error("  cors     - Function with CORS headers");
  console.error("  webhook  - Webhook handler with signature verification");
  console.error("  cron     - Scheduled function");
  console.error("\nExample:");
  console.error("  bun func_new.ts hello-world");
  console.error("  bun func_new.ts stripe-webhook --template webhook");
  process.exit(1);
}

// Validate function name
const validName = /^[a-z][a-z0-9-]*$/;
if (!validName.test(name)) {
  console.error("Error: Function name must be lowercase alphanumeric with dashes");
  console.error("Example: hello-world, process-order, send-email");
  process.exit(1);
}

const templates: Record<string, string> = {
  basic: `// Edge Function: ${name}
// Created: ${new Date().toISOString().split("T")[0]}

import "jsr:@supabase/functions-js/edge-runtime.d.ts"

Deno.serve(async (req) => {
  const { name } = await req.json()
  const data = {
    message: \`Hello \${name}!\`,
  }

  return new Response(
    JSON.stringify(data),
    { headers: { "Content-Type": "application/json" } },
  )
})
`,

  cors: `// Edge Function: ${name}
// Created: ${new Date().toISOString().split("T")[0]}
// Template: CORS-enabled

import "jsr:@supabase/functions-js/edge-runtime.d.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { name } = await req.json()
    const data = {
      message: \`Hello \${name}!\`,
    }

    return new Response(
      JSON.stringify(data),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      },
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      },
    )
  }
})
`,

  webhook: `// Edge Function: ${name}
// Created: ${new Date().toISOString().split("T")[0]}
// Template: Webhook handler with signature verification

import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from 'jsr:@supabase/supabase-js@2'

// Verify webhook signature (example for Stripe)
async function verifySignature(
  payload: string,
  signature: string,
  secret: string
): Promise<boolean> {
  const encoder = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['verify']
  )

  const signatureBuffer = Uint8Array.from(
    signature.split('').map((c) => c.charCodeAt(0))
  )

  return await crypto.subtle.verify(
    'HMAC',
    key,
    signatureBuffer,
    encoder.encode(payload)
  )
}

Deno.serve(async (req) => {
  const signature = req.headers.get('x-signature')
  const webhookSecret = Deno.env.get('WEBHOOK_SECRET')

  if (!signature || !webhookSecret) {
    return new Response(
      JSON.stringify({ error: 'Missing signature or secret' }),
      { status: 401, headers: { 'Content-Type': 'application/json' } }
    )
  }

  const body = await req.text()

  // Verify signature
  const isValid = await verifySignature(body, signature, webhookSecret)
  if (!isValid) {
    return new Response(
      JSON.stringify({ error: 'Invalid signature' }),
      { status: 401, headers: { 'Content-Type': 'application/json' } }
    )
  }

  // Parse webhook payload
  const payload = JSON.parse(body)
  console.log('Webhook received:', payload.type)

  // Initialize Supabase client
  const supabaseUrl = Deno.env.get('SUPABASE_URL')!
  const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  const supabase = createClient(supabaseUrl, supabaseServiceKey)

  // Handle webhook event
  try {
    switch (payload.type) {
      case 'example.event':
        // Handle specific event type
        break
      default:
        console.log('Unhandled event type:', payload.type)
    }

    return new Response(
      JSON.stringify({ received: true }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Webhook error:', error)
    return new Response(
      JSON.stringify({ error: 'Webhook processing failed' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
})
`,

  cron: `// Edge Function: ${name}
// Created: ${new Date().toISOString().split("T")[0]}
// Template: Scheduled/Cron function
//
// Deploy with: supabase functions deploy ${name}
// Schedule via pg_cron in dashboard or with:
//   SELECT cron.schedule(
//     '${name}',
//     '*/5 * * * *', -- Every 5 minutes
//     \$\$
//     SELECT net.http_post(
//       url := 'https://YOUR_PROJECT.supabase.co/functions/v1/${name}',
//       headers := '{"Authorization": "Bearer YOUR_ANON_KEY"}'::jsonb
//     );
//     \$\$
//   );

import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from 'jsr:@supabase/supabase-js@2'

Deno.serve(async (req) => {
  // Verify this is from pg_cron or has proper authorization
  const authHeader = req.headers.get('Authorization')
  if (!authHeader) {
    return new Response(
      JSON.stringify({ error: 'Unauthorized' }),
      { status: 401, headers: { 'Content-Type': 'application/json' } }
    )
  }

  console.log('Cron job started:', new Date().toISOString())

  // Initialize Supabase client
  const supabaseUrl = Deno.env.get('SUPABASE_URL')!
  const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  const supabase = createClient(supabaseUrl, supabaseServiceKey)

  try {
    // Your scheduled task logic here
    // Example: Clean up old records
    // const { data, error } = await supabase
    //   .from('logs')
    //   .delete()
    //   .lt('created_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString())

    console.log('Cron job completed:', new Date().toISOString())

    return new Response(
      JSON.stringify({ success: true, timestamp: new Date().toISOString() }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Cron job error:', error)
    return new Response(
      JSON.stringify({ error: 'Job failed', message: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
})
`,
};

if (!templates[template]) {
  console.error(`Error: Unknown template '${template}'`);
  console.error(`Available: ${Object.keys(templates).join(", ")}`);
  process.exit(1);
}

const functionsDir = join(process.cwd(), "supabase", "functions");
const functionDir = join(functionsDir, name);
const indexPath = join(functionDir, "index.ts");

console.log("=" + "=".repeat(59));
console.log(" EDGE FUNCTION CREATOR");
console.log("=" + "=".repeat(59));
console.log(`\nFunction: ${name}`);
console.log(`Template: ${template}`);
console.log(`Location: ${functionDir}`);

// Check if function already exists
if (existsSync(functionDir)) {
  console.error(`\n❌ Error: Function '${name}' already exists at ${functionDir}`);
  process.exit(1);
}

// Create directories
if (!existsSync(functionsDir)) {
  mkdirSync(functionsDir, { recursive: true });
}
mkdirSync(functionDir);

// Create _shared directory if it doesn't exist
const sharedDir = join(functionsDir, "_shared");
if (!existsSync(sharedDir)) {
  mkdirSync(sharedDir);
  // Create a shared cors.ts file
  const corsContent = `// Shared CORS headers for Edge Functions
export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}
`;
  writeFileSync(join(sharedDir, "cors.ts"), corsContent);
  console.log("\n📁 Created _shared/cors.ts");
}

// Write the function file
writeFileSync(indexPath, templates[template]);

console.log("\n✓ Edge Function created!");
console.log("\nNext steps:");
console.log(`  1. Edit: ${indexPath}`);
console.log(`  2. Test locally: supabase functions serve ${name}`);
console.log(`  3. Deploy: bun .claude/skills/supabase-cli/scripts/func_deploy.ts ${name}`);

if (template === "webhook") {
  console.log("\n⚠️  Webhook template notes:");
  console.log("  - Set WEBHOOK_SECRET: supabase secrets set WEBHOOK_SECRET=xxx");
  console.log("  - Customize signature verification for your webhook provider");
}

if (template === "cron") {
  console.log("\n⚠️  Cron template notes:");
  console.log("  - Schedule via pg_cron in Supabase Dashboard");
  console.log("  - See comments in index.ts for scheduling SQL");
}
