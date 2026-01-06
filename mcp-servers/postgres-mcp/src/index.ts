#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import pg from "pg";
import { z } from "zod";

const { Pool } = pg;

// Configuration from environment
const config = {
  host: process.env.POSTGRES_HOST || "localhost",
  port: parseInt(process.env.POSTGRES_PORT || "5432"),
  user: process.env.POSTGRES_USER || "postgres",
  password: process.env.POSTGRES_PASSWORD || "",
  database: process.env.POSTGRES_DATABASE || "postgres",
  ssl: process.env.POSTGRES_SSL === "true",
  maxRows: parseInt(process.env.MAX_ROWS || "1000"),
  queryTimeout: parseInt(process.env.QUERY_TIMEOUT || "30000"),
  allowWrites: process.env.ALLOW_WRITES === "true",
};

// Create connection pool
const pool = new Pool({
  host: config.host,
  port: config.port,
  user: config.user,
  password: config.password,
  database: config.database,
  ssl: config.ssl ? { rejectUnauthorized: false } : false,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

// Input schemas
const QuerySchema = z.object({
  sql: z.string().describe("SQL query to execute"),
  params: z.array(z.unknown()).optional().describe("Query parameters"),
});

const TableSchema = z.object({
  table: z.string().describe("Table name"),
  schema: z.string().default("public").describe("Schema name"),
});

const SchemaSchema = z.object({
  schema: z.string().default("public").describe("Schema name"),
});

const ExplainSchema = z.object({
  sql: z.string().describe("SQL query to explain"),
  analyze: z.boolean().default(false).describe("Run EXPLAIN ANALYZE"),
});

// Helper: Check if query is read-only
function isReadOnlyQuery(sql: string): boolean {
  const normalized = sql.trim().toLowerCase();
  const writeKeywords = [
    "insert",
    "update",
    "delete",
    "drop",
    "create",
    "alter",
    "truncate",
    "grant",
    "revoke",
  ];
  return !writeKeywords.some((keyword) => normalized.startsWith(keyword));
}

// Helper: Execute query with timeout and row limit
async function executeQuery(
  sql: string,
  params: unknown[] = []
): Promise<{ rows: Record<string, unknown>[]; rowCount: number }> {
  const client = await pool.connect();
  try {
    await client.query(`SET statement_timeout = ${config.queryTimeout}`);

    // Add LIMIT if SELECT without LIMIT
    let finalSql = sql;
    if (
      sql.trim().toLowerCase().startsWith("select") &&
      !sql.toLowerCase().includes("limit")
    ) {
      finalSql = `${sql} LIMIT ${config.maxRows}`;
    }

    const result = await client.query(finalSql, params);
    return {
      rows: result.rows,
      rowCount: result.rowCount ?? 0,
    };
  } finally {
    client.release();
  }
}

// Create MCP server
const server = new Server(
  {
    name: "postgres-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "query",
      description:
        "Execute a SQL query against the PostgreSQL database. Returns up to " +
        config.maxRows +
        " rows.",
      inputSchema: {
        type: "object",
        properties: {
          sql: { type: "string", description: "SQL query to execute" },
          params: {
            type: "array",
            items: {},
            description: "Query parameters for parameterized queries",
          },
        },
        required: ["sql"],
      },
    },
    {
      name: "list_tables",
      description: "List all tables in a schema",
      inputSchema: {
        type: "object",
        properties: {
          schema: {
            type: "string",
            description: "Schema name (default: public)",
          },
        },
      },
    },
    {
      name: "describe_table",
      description:
        "Get detailed information about a table including columns, types, and constraints",
      inputSchema: {
        type: "object",
        properties: {
          table: { type: "string", description: "Table name" },
          schema: {
            type: "string",
            description: "Schema name (default: public)",
          },
        },
        required: ["table"],
      },
    },
    {
      name: "table_stats",
      description: "Get statistics about a table including row count and size",
      inputSchema: {
        type: "object",
        properties: {
          table: { type: "string", description: "Table name" },
          schema: {
            type: "string",
            description: "Schema name (default: public)",
          },
        },
        required: ["table"],
      },
    },
    {
      name: "explain_query",
      description: "Get the execution plan for a query",
      inputSchema: {
        type: "object",
        properties: {
          sql: { type: "string", description: "SQL query to explain" },
          analyze: {
            type: "boolean",
            description: "Run EXPLAIN ANALYZE (actually executes query)",
          },
        },
        required: ["sql"],
      },
    },
    {
      name: "list_indexes",
      description: "List indexes for a table or schema",
      inputSchema: {
        type: "object",
        properties: {
          table: { type: "string", description: "Table name (optional)" },
          schema: {
            type: "string",
            description: "Schema name (default: public)",
          },
        },
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "query": {
        const { sql, params } = QuerySchema.parse(args);

        if (!config.allowWrites && !isReadOnlyQuery(sql)) {
          return {
            content: [
              {
                type: "text",
                text: "Error: Write operations are not allowed. Set ALLOW_WRITES=true to enable.",
              },
            ],
            isError: true,
          };
        }

        const result = await executeQuery(sql, params || []);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  rows: result.rows,
                  rowCount: result.rowCount,
                  note:
                    result.rowCount >= config.maxRows
                      ? `Results limited to ${config.maxRows} rows`
                      : undefined,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "list_tables": {
        const { schema } = SchemaSchema.parse(args);
        const result = await executeQuery(
          `
          SELECT
            table_name,
            table_type,
            (SELECT count(*) FROM information_schema.columns c
             WHERE c.table_schema = t.table_schema AND c.table_name = t.table_name) as column_count
          FROM information_schema.tables t
          WHERE table_schema = $1
          ORDER BY table_name
        `,
          [schema]
        );
        return {
          content: [{ type: "text", text: JSON.stringify(result.rows, null, 2) }],
        };
      }

      case "describe_table": {
        const { table, schema } = TableSchema.parse(args);

        // Get columns
        const columns = await executeQuery(
          `
          SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
          FROM information_schema.columns
          WHERE table_schema = $1 AND table_name = $2
          ORDER BY ordinal_position
        `,
          [schema, table]
        );

        // Get constraints
        const constraints = await executeQuery(
          `
          SELECT
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name
          FROM information_schema.table_constraints tc
          JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
          WHERE tc.table_schema = $1 AND tc.table_name = $2
        `,
          [schema, table]
        );

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  table: `${schema}.${table}`,
                  columns: columns.rows,
                  constraints: constraints.rows,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "table_stats": {
        const { table, schema } = TableSchema.parse(args);

        const stats = await executeQuery(
          `
          SELECT
            relname as table_name,
            n_live_tup as row_count,
            pg_size_pretty(pg_total_relation_size('"${schema}"."${table}"')) as total_size,
            pg_size_pretty(pg_table_size('"${schema}"."${table}"')) as table_size,
            pg_size_pretty(pg_indexes_size('"${schema}"."${table}"')) as indexes_size
          FROM pg_stat_user_tables
          WHERE schemaname = $1 AND relname = $2
        `,
          [schema, table]
        );

        return {
          content: [{ type: "text", text: JSON.stringify(stats.rows[0] || {}, null, 2) }],
        };
      }

      case "explain_query": {
        const { sql, analyze } = ExplainSchema.parse(args);

        if (!isReadOnlyQuery(sql)) {
          return {
            content: [
              {
                type: "text",
                text: "Error: Can only explain read-only queries",
              },
            ],
            isError: true,
          };
        }

        const explainSql = analyze
          ? `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ${sql}`
          : `EXPLAIN (FORMAT JSON) ${sql}`;

        const result = await executeQuery(explainSql);
        return {
          content: [{ type: "text", text: JSON.stringify(result.rows, null, 2) }],
        };
      }

      case "list_indexes": {
        const parsed = z
          .object({
            table: z.string().optional(),
            schema: z.string().default("public"),
          })
          .parse(args);

        let sql = `
          SELECT
            indexname,
            tablename,
            indexdef
          FROM pg_indexes
          WHERE schemaname = $1
        `;
        const params: string[] = [parsed.schema];

        if (parsed.table) {
          sql += ` AND tablename = $2`;
          params.push(parsed.table);
        }

        sql += ` ORDER BY tablename, indexname`;

        const result = await executeQuery(sql, params);
        return {
          content: [{ type: "text", text: JSON.stringify(result.rows, null, 2) }],
        };
      }

      default:
        return {
          content: [{ type: "text", text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      content: [{ type: "text", text: `Error: ${message}` }],
      isError: true,
    };
  }
});

// List resources (database schema as resources)
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  try {
    const result = await executeQuery(`
      SELECT table_schema, table_name
      FROM information_schema.tables
      WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
      ORDER BY table_schema, table_name
    `);

    return {
      resources: result.rows.map((row) => ({
        uri: `postgres://${row.table_schema}/${row.table_name}`,
        name: `${row.table_schema}.${row.table_name}`,
        mimeType: "application/json",
        description: `Table ${row.table_schema}.${row.table_name}`,
      })),
    };
  } catch {
    return { resources: [] };
  }
});

// Read resource (table schema)
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;
  const match = uri.match(/^postgres:\/\/([^/]+)\/(.+)$/);

  if (!match) {
    throw new Error(`Invalid resource URI: ${uri}`);
  }

  const [, schema, table] = match;

  const columns = await executeQuery(
    `
    SELECT
      column_name,
      data_type,
      is_nullable,
      column_default
    FROM information_schema.columns
    WHERE table_schema = $1 AND table_name = $2
    ORDER BY ordinal_position
  `,
    [schema, table]
  );

  return {
    contents: [
      {
        uri,
        mimeType: "application/json",
        text: JSON.stringify(
          {
            schema,
            table,
            columns: columns.rows,
          },
          null,
          2
        ),
      },
    ],
  };
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("PostgreSQL MCP server started");
}

main().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});
