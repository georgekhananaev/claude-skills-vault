#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { z } from "zod";

// Configuration from environment
const config = {
  url: process.env.SUPABASE_URL || "",
  serviceKey: process.env.SUPABASE_SERVICE_KEY || "",
  anonKey: process.env.SUPABASE_ANON_KEY || "",
  maxRows: parseInt(process.env.MAX_ROWS || "100"),
  allowWrites: process.env.ALLOW_WRITES === "true",
};

if (!config.url) {
  console.error("Error: SUPABASE_URL is required");
  process.exit(1);
}

// Use service key for full access, fallback to anon key
const supabaseKey = config.serviceKey || config.anonKey;
if (!supabaseKey) {
  console.error("Error: SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY is required");
  process.exit(1);
}

const supabase: SupabaseClient = createClient(config.url, supabaseKey, {
  auth: { persistSession: false },
});

// Input schemas
const QuerySchema = z.object({
  table: z.string().describe("Table name"),
  select: z.string().optional().describe("Columns to select (default: *)"),
  filter: z.record(z.unknown()).optional().describe("Filter conditions"),
  order: z.object({
    column: z.string(),
    ascending: z.boolean().default(true),
  }).optional().describe("Order by column"),
  limit: z.number().optional().describe("Max rows to return"),
  offset: z.number().optional().describe("Rows to skip"),
});

const InsertSchema = z.object({
  table: z.string().describe("Table name"),
  data: z.union([z.record(z.unknown()), z.array(z.record(z.unknown()))]).describe("Row(s) to insert"),
  upsert: z.boolean().optional().describe("Upsert on conflict"),
});

const UpdateSchema = z.object({
  table: z.string().describe("Table name"),
  data: z.record(z.unknown()).describe("Data to update"),
  match: z.record(z.unknown()).describe("Match conditions"),
});

const DeleteSchema = z.object({
  table: z.string().describe("Table name"),
  match: z.record(z.unknown()).describe("Match conditions"),
});

const RpcSchema = z.object({
  function: z.string().describe("Function name"),
  params: z.record(z.unknown()).optional().describe("Function parameters"),
});

const StorageSchema = z.object({
  bucket: z.string().describe("Bucket name"),
  path: z.string().optional().describe("File path"),
});

const UserSchema = z.object({
  email: z.string().optional(),
  userId: z.string().optional(),
});

// Create MCP server
const server = new Server(
  { name: "supabase-mcp", version: "1.0.0" },
  { capabilities: { tools: {}, resources: {} } }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    // Database tools
    {
      name: "query",
      description: `Query a table with filters, ordering, and pagination. Returns up to ${config.maxRows} rows.`,
      inputSchema: {
        type: "object",
        properties: {
          table: { type: "string", description: "Table name" },
          select: { type: "string", description: "Columns to select (e.g., 'id, name, email')" },
          filter: { type: "object", description: "Filter conditions (e.g., { status: 'active' })" },
          order: {
            type: "object",
            properties: {
              column: { type: "string" },
              ascending: { type: "boolean" },
            },
          },
          limit: { type: "number" },
          offset: { type: "number" },
        },
        required: ["table"],
      },
    },
    {
      name: "list_tables",
      description: "List all tables in the database with row counts",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "describe_table",
      description: "Get table schema including columns, types, and constraints",
      inputSchema: {
        type: "object",
        properties: { table: { type: "string" } },
        required: ["table"],
      },
    },
    {
      name: "insert",
      description: "Insert row(s) into a table (requires ALLOW_WRITES=true)",
      inputSchema: {
        type: "object",
        properties: {
          table: { type: "string" },
          data: { oneOf: [{ type: "object" }, { type: "array" }] },
          upsert: { type: "boolean" },
        },
        required: ["table", "data"],
      },
    },
    {
      name: "update",
      description: "Update rows in a table (requires ALLOW_WRITES=true)",
      inputSchema: {
        type: "object",
        properties: {
          table: { type: "string" },
          data: { type: "object" },
          match: { type: "object" },
        },
        required: ["table", "data", "match"],
      },
    },
    {
      name: "delete",
      description: "Delete rows from a table (requires ALLOW_WRITES=true)",
      inputSchema: {
        type: "object",
        properties: {
          table: { type: "string" },
          match: { type: "object" },
        },
        required: ["table", "match"],
      },
    },
    {
      name: "rpc",
      description: "Call a database function (RPC)",
      inputSchema: {
        type: "object",
        properties: {
          function: { type: "string", description: "Function name" },
          params: { type: "object", description: "Function parameters" },
        },
        required: ["function"],
      },
    },
    {
      name: "sql",
      description: "Execute raw SQL query (read-only unless ALLOW_WRITES=true)",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "SQL query" },
        },
        required: ["query"],
      },
    },
    // RLS tools
    {
      name: "list_policies",
      description: "List RLS policies for a table",
      inputSchema: {
        type: "object",
        properties: { table: { type: "string" } },
        required: ["table"],
      },
    },
    // Auth tools
    {
      name: "list_users",
      description: "List auth users (requires service key)",
      inputSchema: {
        type: "object",
        properties: {
          page: { type: "number" },
          perPage: { type: "number" },
        },
      },
    },
    {
      name: "get_user",
      description: "Get user by ID or email",
      inputSchema: {
        type: "object",
        properties: {
          userId: { type: "string" },
          email: { type: "string" },
        },
      },
    },
    {
      name: "create_user",
      description: "Create a new user (requires ALLOW_WRITES=true and service key)",
      inputSchema: {
        type: "object",
        properties: {
          email: { type: "string" },
          password: { type: "string" },
          userData: { type: "object" },
        },
        required: ["email", "password"],
      },
    },
    // Storage tools
    {
      name: "list_buckets",
      description: "List storage buckets",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "list_files",
      description: "List files in a bucket",
      inputSchema: {
        type: "object",
        properties: {
          bucket: { type: "string" },
          path: { type: "string" },
          limit: { type: "number" },
        },
        required: ["bucket"],
      },
    },
    {
      name: "get_file_url",
      description: "Get public or signed URL for a file",
      inputSchema: {
        type: "object",
        properties: {
          bucket: { type: "string" },
          path: { type: "string" },
          expiresIn: { type: "number", description: "Expiry in seconds (for signed URL)" },
        },
        required: ["bucket", "path"],
      },
    },
    // Edge Functions
    {
      name: "invoke_function",
      description: "Invoke an Edge Function",
      inputSchema: {
        type: "object",
        properties: {
          function: { type: "string", description: "Function name" },
          body: { type: "object", description: "Request body" },
        },
        required: ["function"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      // Database operations
      case "query": {
        const { table, select, filter, order, limit, offset } = QuerySchema.parse(args);
        let query = supabase.from(table).select(select || "*", { count: "exact" });

        if (filter) {
          for (const [key, value] of Object.entries(filter)) {
            query = query.eq(key, value);
          }
        }
        if (order) {
          query = query.order(order.column, { ascending: order.ascending });
        }
        query = query.limit(Math.min(limit || config.maxRows, config.maxRows));
        if (offset) query = query.range(offset, offset + (limit || config.maxRows) - 1);

        const { data, error, count } = await query;
        if (error) throw error;

        return {
          content: [{
            type: "text",
            text: JSON.stringify({ rows: data, count, returned: data?.length }, null, 2),
          }],
        };
      }

      case "list_tables": {
        const { data, error } = await supabase.rpc("get_tables_info");
        if (error) {
          // Fallback: query information_schema
          const { data: tables, error: err2 } = await supabase
            .from("information_schema.tables")
            .select("table_name, table_type")
            .eq("table_schema", "public");
          if (err2) throw err2;
          return { content: [{ type: "text", text: JSON.stringify(tables, null, 2) }] };
        }
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      }

      case "describe_table": {
        const { table } = z.object({ table: z.string() }).parse(args);
        const { data, error } = await supabase
          .from("information_schema.columns")
          .select("column_name, data_type, is_nullable, column_default")
          .eq("table_schema", "public")
          .eq("table_name", table);
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify({ table, columns: data }, null, 2) }] };
      }

      case "insert": {
        if (!config.allowWrites) {
          return { content: [{ type: "text", text: "Error: Write operations disabled. Set ALLOW_WRITES=true" }], isError: true };
        }
        const { table, data, upsert } = InsertSchema.parse(args);
        const query = upsert
          ? supabase.from(table).upsert(data).select()
          : supabase.from(table).insert(data).select();
        const { data: result, error } = await query;
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify({ inserted: result }, null, 2) }] };
      }

      case "update": {
        if (!config.allowWrites) {
          return { content: [{ type: "text", text: "Error: Write operations disabled. Set ALLOW_WRITES=true" }], isError: true };
        }
        const { table, data, match } = UpdateSchema.parse(args);
        let query = supabase.from(table).update(data);
        for (const [key, value] of Object.entries(match)) {
          query = query.eq(key, value);
        }
        const { data: result, error } = await query.select();
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify({ updated: result }, null, 2) }] };
      }

      case "delete": {
        if (!config.allowWrites) {
          return { content: [{ type: "text", text: "Error: Write operations disabled. Set ALLOW_WRITES=true" }], isError: true };
        }
        const { table, match } = DeleteSchema.parse(args);
        let query = supabase.from(table).delete();
        for (const [key, value] of Object.entries(match)) {
          query = query.eq(key, value);
        }
        const { data: result, error } = await query.select();
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify({ deleted: result }, null, 2) }] };
      }

      case "rpc": {
        const { function: fn, params } = RpcSchema.parse(args);
        const { data, error } = await supabase.rpc(fn, params || {});
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify({ result: data }, null, 2) }] };
      }

      case "sql": {
        const { query } = z.object({ query: z.string() }).parse(args);
        const isWrite = /^\s*(insert|update|delete|drop|create|alter|truncate)/i.test(query);
        if (isWrite && !config.allowWrites) {
          return { content: [{ type: "text", text: "Error: Write operations disabled" }], isError: true };
        }
        // Use rpc to execute raw SQL (requires a helper function in Supabase)
        const { data, error } = await supabase.rpc("execute_sql", { query_text: query });
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      }

      // RLS policies
      case "list_policies": {
        const { table } = z.object({ table: z.string() }).parse(args);
        const { data, error } = await supabase
          .from("pg_policies")
          .select("*")
          .eq("tablename", table);
        if (error) {
          // Alternative query
          const { data: policies, error: err2 } = await supabase.rpc("get_policies", { p_table: table });
          if (err2) throw err2;
          return { content: [{ type: "text", text: JSON.stringify(policies, null, 2) }] };
        }
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      }

      // Auth operations
      case "list_users": {
        const { page, perPage } = z.object({
          page: z.number().default(1),
          perPage: z.number().default(50),
        }).parse(args || {});
        const { data, error } = await supabase.auth.admin.listUsers({ page, perPage });
        if (error) throw error;
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              users: data.users.map((u) => ({
                id: u.id,
                email: u.email,
                created_at: u.created_at,
                last_sign_in_at: u.last_sign_in_at,
              })),
              total: data.users.length,
            }, null, 2),
          }],
        };
      }

      case "get_user": {
        const { userId, email } = UserSchema.parse(args);
        if (userId) {
          const { data, error } = await supabase.auth.admin.getUserById(userId);
          if (error) throw error;
          return { content: [{ type: "text", text: JSON.stringify(data.user, null, 2) }] };
        }
        if (email) {
          const { data, error } = await supabase.auth.admin.listUsers();
          if (error) throw error;
          const user = data.users.find((u) => u.email === email);
          return { content: [{ type: "text", text: JSON.stringify(user || null, null, 2) }] };
        }
        return { content: [{ type: "text", text: "Error: Provide userId or email" }], isError: true };
      }

      case "create_user": {
        if (!config.allowWrites) {
          return { content: [{ type: "text", text: "Error: Write operations disabled" }], isError: true };
        }
        const { email, password, userData } = z.object({
          email: z.string(),
          password: z.string(),
          userData: z.record(z.unknown()).optional(),
        }).parse(args);
        const { data, error } = await supabase.auth.admin.createUser({
          email,
          password,
          user_metadata: userData,
          email_confirm: true,
        });
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify({ user: data.user }, null, 2) }] };
      }

      // Storage operations
      case "list_buckets": {
        const { data, error } = await supabase.storage.listBuckets();
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      }

      case "list_files": {
        const { bucket, path, limit } = z.object({
          bucket: z.string(),
          path: z.string().default(""),
          limit: z.number().default(100),
        }).parse(args);
        const { data, error } = await supabase.storage.from(bucket).list(path, { limit });
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      }

      case "get_file_url": {
        const { bucket, path, expiresIn } = z.object({
          bucket: z.string(),
          path: z.string(),
          expiresIn: z.number().optional(),
        }).parse(args);

        if (expiresIn) {
          const { data, error } = await supabase.storage.from(bucket).createSignedUrl(path, expiresIn);
          if (error) throw error;
          return { content: [{ type: "text", text: JSON.stringify({ signedUrl: data.signedUrl }, null, 2) }] };
        }

        const { data } = supabase.storage.from(bucket).getPublicUrl(path);
        return { content: [{ type: "text", text: JSON.stringify({ publicUrl: data.publicUrl }, null, 2) }] };
      }

      // Edge Functions
      case "invoke_function": {
        const { function: fn, body } = z.object({
          function: z.string(),
          body: z.record(z.unknown()).optional(),
        }).parse(args);
        const { data, error } = await supabase.functions.invoke(fn, { body });
        if (error) throw error;
        return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
      }

      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
  }
});

// List resources (tables)
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  try {
    const { data } = await supabase
      .from("information_schema.tables")
      .select("table_name")
      .eq("table_schema", "public");

    return {
      resources: (data || []).map((t) => ({
        uri: `supabase://${config.url}/table/${t.table_name}`,
        name: t.table_name,
        mimeType: "application/json",
        description: `Table: ${t.table_name}`,
      })),
    };
  } catch {
    return { resources: [] };
  }
});

// Read resource (table schema)
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;
  const match = uri.match(/\/table\/(.+)$/);

  if (!match) {
    throw new Error(`Invalid resource URI: ${uri}`);
  }

  const table = match[1];
  const { data } = await supabase
    .from("information_schema.columns")
    .select("column_name, data_type, is_nullable, column_default")
    .eq("table_schema", "public")
    .eq("table_name", table);

  return {
    contents: [{
      uri,
      mimeType: "application/json",
      text: JSON.stringify({ table, columns: data }, null, 2),
    }],
  };
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Supabase MCP server started");
}

main().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});
