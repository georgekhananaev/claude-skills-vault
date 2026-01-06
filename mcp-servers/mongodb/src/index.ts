#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { MongoClient, Db, Document } from "mongodb";
import { z } from "zod";

// Configuration from environment
const config = {
  connectionString: process.env.MONGODB_CONNECTION_STRING || "mongodb://localhost:27017",
  database: process.env.MONGODB_DATABASE || "test",
  maxDocuments: parseInt(process.env.MAX_DOCUMENTS || "100"),
  queryTimeout: parseInt(process.env.QUERY_TIMEOUT || "30000"),
  allowWrites: process.env.ALLOW_WRITES === "true",
};

let client: MongoClient;
let db: Db;

// Connect to MongoDB
async function connect(): Promise<Db> {
  if (!client) {
    client = new MongoClient(config.connectionString, {
      serverSelectionTimeoutMS: 5000,
      connectTimeoutMS: 10000,
    });
    await client.connect();
    db = client.db(config.database);
  }
  return db;
}

// Input schemas
const FindSchema = z.object({
  collection: z.string().describe("Collection name"),
  filter: z.record(z.unknown()).optional().describe("Query filter (MongoDB query syntax)"),
  projection: z.record(z.number()).optional().describe("Fields to include/exclude"),
  sort: z.record(z.number()).optional().describe("Sort order"),
  limit: z.number().optional().describe("Maximum documents to return"),
  skip: z.number().optional().describe("Documents to skip"),
});

const AggregateSchema = z.object({
  collection: z.string().describe("Collection name"),
  pipeline: z.array(z.record(z.unknown())).describe("Aggregation pipeline stages"),
});

const CollectionSchema = z.object({
  collection: z.string().describe("Collection name"),
});

const InsertSchema = z.object({
  collection: z.string().describe("Collection name"),
  documents: z.array(z.record(z.unknown())).describe("Documents to insert"),
});

const UpdateSchema = z.object({
  collection: z.string().describe("Collection name"),
  filter: z.record(z.unknown()).describe("Query filter"),
  update: z.record(z.unknown()).describe("Update operations"),
  upsert: z.boolean().optional().describe("Insert if not found"),
  multi: z.boolean().optional().describe("Update multiple documents"),
});

const DeleteSchema = z.object({
  collection: z.string().describe("Collection name"),
  filter: z.record(z.unknown()).describe("Query filter"),
  multi: z.boolean().optional().describe("Delete multiple documents"),
});

const IndexSchema = z.object({
  collection: z.string().describe("Collection name"),
  keys: z.record(z.number()).optional().describe("Index keys"),
  options: z.record(z.unknown()).optional().describe("Index options"),
});

// Helper: Infer schema from sample documents
function inferSchema(documents: Document[]): Record<string, { type: string; nullable: boolean; sample?: unknown }> {
  const schema: Record<string, { types: Set<string>; nullable: boolean; sample?: unknown }> = {};

  for (const doc of documents) {
    for (const [key, value] of Object.entries(doc)) {
      if (!schema[key]) {
        schema[key] = { types: new Set(), nullable: false };
      }

      if (value === null || value === undefined) {
        schema[key].nullable = true;
      } else {
        const type = Array.isArray(value) ? "array" : typeof value;
        schema[key].types.add(type);
        if (!schema[key].sample) {
          schema[key].sample = value;
        }
      }
    }
  }

  const result: Record<string, { type: string; nullable: boolean; sample?: unknown }> = {};
  for (const [key, value] of Object.entries(schema)) {
    result[key] = {
      type: Array.from(value.types).join(" | ") || "unknown",
      nullable: value.nullable,
      sample: value.sample,
    };
  }
  return result;
}

// Create MCP server
const server = new Server(
  { name: "mongodb-mcp", version: "1.0.0" },
  { capabilities: { tools: {}, resources: {} } }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "find",
      description: `Find documents in a collection. Returns up to ${config.maxDocuments} documents.`,
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          filter: { type: "object", description: "Query filter (MongoDB syntax)" },
          projection: { type: "object", description: "Fields to include (1) or exclude (0)" },
          sort: { type: "object", description: "Sort order: { field: 1 } for asc, { field: -1 } for desc" },
          limit: { type: "number", description: "Max documents to return" },
          skip: { type: "number", description: "Documents to skip" },
        },
        required: ["collection"],
      },
    },
    {
      name: "aggregate",
      description: "Run an aggregation pipeline on a collection",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          pipeline: { type: "array", description: "Aggregation pipeline stages" },
        },
        required: ["collection", "pipeline"],
      },
    },
    {
      name: "list_collections",
      description: "List all collections in the database",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "collection_stats",
      description: "Get statistics about a collection (document count, size, indexes)",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
        },
        required: ["collection"],
      },
    },
    {
      name: "analyze_schema",
      description: "Analyze and infer schema from sample documents in a collection",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          sampleSize: { type: "number", description: "Number of documents to sample (default: 100)" },
        },
        required: ["collection"],
      },
    },
    {
      name: "list_indexes",
      description: "List all indexes on a collection",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
        },
        required: ["collection"],
      },
    },
    {
      name: "create_index",
      description: "Create an index on a collection (requires ALLOW_WRITES=true)",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          keys: { type: "object", description: "Index keys: { field: 1 } for asc, { field: -1 } for desc" },
          options: { type: "object", description: "Index options (unique, sparse, etc.)" },
        },
        required: ["collection", "keys"],
      },
    },
    {
      name: "explain",
      description: "Explain query execution plan",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          filter: { type: "object", description: "Query filter" },
        },
        required: ["collection"],
      },
    },
    {
      name: "insert",
      description: "Insert documents into a collection (requires ALLOW_WRITES=true)",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          documents: { type: "array", description: "Documents to insert" },
        },
        required: ["collection", "documents"],
      },
    },
    {
      name: "update",
      description: "Update documents in a collection (requires ALLOW_WRITES=true)",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          filter: { type: "object", description: "Query filter" },
          update: { type: "object", description: "Update operations ($set, $inc, etc.)" },
          upsert: { type: "boolean", description: "Insert if not found" },
          multi: { type: "boolean", description: "Update multiple documents" },
        },
        required: ["collection", "filter", "update"],
      },
    },
    {
      name: "delete",
      description: "Delete documents from a collection (requires ALLOW_WRITES=true)",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          filter: { type: "object", description: "Query filter" },
          multi: { type: "boolean", description: "Delete multiple documents" },
        },
        required: ["collection", "filter"],
      },
    },
    {
      name: "count",
      description: "Count documents matching a filter",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          filter: { type: "object", description: "Query filter" },
        },
        required: ["collection"],
      },
    },
    {
      name: "distinct",
      description: "Get distinct values for a field",
      inputSchema: {
        type: "object",
        properties: {
          collection: { type: "string", description: "Collection name" },
          field: { type: "string", description: "Field name" },
          filter: { type: "object", description: "Query filter" },
        },
        required: ["collection", "field"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    const database = await connect();

    switch (name) {
      case "find": {
        const { collection, filter, projection, sort, limit, skip } = FindSchema.parse(args);
        const coll = database.collection(collection);
        const cursor = coll.find(filter || {}, {
          projection,
          sort: sort as Record<string, 1 | -1>,
          limit: Math.min(limit || config.maxDocuments, config.maxDocuments),
          skip,
          maxTimeMS: config.queryTimeout,
        });
        const docs = await cursor.toArray();
        return {
          content: [{
            type: "text",
            text: JSON.stringify({ documents: docs, count: docs.length }, null, 2),
          }],
        };
      }

      case "aggregate": {
        const { collection, pipeline } = AggregateSchema.parse(args);
        const coll = database.collection(collection);
        const docs = await coll.aggregate(pipeline, { maxTimeMS: config.queryTimeout }).toArray();
        return {
          content: [{
            type: "text",
            text: JSON.stringify({ results: docs, count: docs.length }, null, 2),
          }],
        };
      }

      case "list_collections": {
        const collections = await database.listCollections().toArray();
        const stats = await Promise.all(
          collections.map(async (c) => {
            const count = await database.collection(c.name).estimatedDocumentCount();
            return { name: c.name, type: c.type, documentCount: count };
          })
        );
        return {
          content: [{ type: "text", text: JSON.stringify(stats, null, 2) }],
        };
      }

      case "collection_stats": {
        const { collection } = CollectionSchema.parse(args);
        const coll = database.collection(collection);
        const [count, indexes, stats] = await Promise.all([
          coll.estimatedDocumentCount(),
          coll.indexes(),
          database.command({ collStats: collection }),
        ]);
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              collection,
              documentCount: count,
              indexCount: indexes.length,
              size: stats.size,
              avgObjSize: stats.avgObjSize,
              storageSize: stats.storageSize,
              totalIndexSize: stats.totalIndexSize,
            }, null, 2),
          }],
        };
      }

      case "analyze_schema": {
        const parsed = z.object({
          collection: z.string(),
          sampleSize: z.number().default(100),
        }).parse(args);
        const coll = database.collection(parsed.collection);
        const sample = await coll.aggregate([{ $sample: { size: parsed.sampleSize } }]).toArray();
        const schema = inferSchema(sample);
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              collection: parsed.collection,
              sampleSize: sample.length,
              fields: schema,
            }, null, 2),
          }],
        };
      }

      case "list_indexes": {
        const { collection } = CollectionSchema.parse(args);
        const indexes = await database.collection(collection).indexes();
        return {
          content: [{ type: "text", text: JSON.stringify(indexes, null, 2) }],
        };
      }

      case "create_index": {
        if (!config.allowWrites) {
          return {
            content: [{ type: "text", text: "Error: Write operations disabled. Set ALLOW_WRITES=true" }],
            isError: true,
          };
        }
        const { collection, keys, options } = IndexSchema.parse(args);
        const result = await database.collection(collection).createIndex(
          keys as Record<string, 1 | -1>,
          options as Record<string, unknown>
        );
        return {
          content: [{ type: "text", text: JSON.stringify({ indexName: result }, null, 2) }],
        };
      }

      case "explain": {
        const parsed = z.object({
          collection: z.string(),
          filter: z.record(z.unknown()).optional(),
        }).parse(args);
        const coll = database.collection(parsed.collection);
        const explanation = await coll.find(parsed.filter || {}).explain("executionStats");
        return {
          content: [{ type: "text", text: JSON.stringify(explanation, null, 2) }],
        };
      }

      case "insert": {
        if (!config.allowWrites) {
          return {
            content: [{ type: "text", text: "Error: Write operations disabled. Set ALLOW_WRITES=true" }],
            isError: true,
          };
        }
        const { collection, documents } = InsertSchema.parse(args);
        const result = await database.collection(collection).insertMany(documents);
        return {
          content: [{
            type: "text",
            text: JSON.stringify({ insertedCount: result.insertedCount, insertedIds: result.insertedIds }, null, 2),
          }],
        };
      }

      case "update": {
        if (!config.allowWrites) {
          return {
            content: [{ type: "text", text: "Error: Write operations disabled. Set ALLOW_WRITES=true" }],
            isError: true,
          };
        }
        const { collection, filter, update, upsert, multi } = UpdateSchema.parse(args);
        const coll = database.collection(collection);
        const result = multi
          ? await coll.updateMany(filter, update, { upsert })
          : await coll.updateOne(filter, update, { upsert });
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              matchedCount: result.matchedCount,
              modifiedCount: result.modifiedCount,
              upsertedId: result.upsertedId,
            }, null, 2),
          }],
        };
      }

      case "delete": {
        if (!config.allowWrites) {
          return {
            content: [{ type: "text", text: "Error: Write operations disabled. Set ALLOW_WRITES=true" }],
            isError: true,
          };
        }
        const { collection, filter, multi } = DeleteSchema.parse(args);
        const coll = database.collection(collection);
        const result = multi
          ? await coll.deleteMany(filter)
          : await coll.deleteOne(filter);
        return {
          content: [{ type: "text", text: JSON.stringify({ deletedCount: result.deletedCount }, null, 2) }],
        };
      }

      case "count": {
        const parsed = z.object({
          collection: z.string(),
          filter: z.record(z.unknown()).optional(),
        }).parse(args);
        const count = await database.collection(parsed.collection).countDocuments(parsed.filter || {});
        return {
          content: [{ type: "text", text: JSON.stringify({ count }, null, 2) }],
        };
      }

      case "distinct": {
        const parsed = z.object({
          collection: z.string(),
          field: z.string(),
          filter: z.record(z.unknown()).optional(),
        }).parse(args);
        const values = await database.collection(parsed.collection).distinct(parsed.field, parsed.filter || {});
        return {
          content: [{ type: "text", text: JSON.stringify({ field: parsed.field, values, count: values.length }, null, 2) }],
        };
      }

      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
  }
});

// List resources (collections)
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  try {
    const database = await connect();
    const collections = await database.listCollections().toArray();
    return {
      resources: collections.map((c) => ({
        uri: `mongodb://${config.database}/${c.name}`,
        name: c.name,
        mimeType: "application/json",
        description: `Collection: ${c.name}`,
      })),
    };
  } catch {
    return { resources: [] };
  }
});

// Read resource (collection schema)
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;
  const match = uri.match(/^mongodb:\/\/[^/]+\/(.+)$/);

  if (!match) {
    throw new Error(`Invalid resource URI: ${uri}`);
  }

  const collection = match[1];
  const database = await connect();
  const sample = await database.collection(collection).aggregate([{ $sample: { size: 10 } }]).toArray();
  const schema = inferSchema(sample);

  return {
    contents: [{
      uri,
      mimeType: "application/json",
      text: JSON.stringify({ collection, schema }, null, 2),
    }],
  };
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MongoDB MCP server started");
}

main().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});
