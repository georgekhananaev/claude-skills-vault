# AI & Vectors (pgvector)

Supabase provides a complete AI toolkit using PostgreSQL and pgvector for embeddings, semantic search, and RAG applications.

## Why Supabase for AI

- Store vectors alongside relational data (no separate vector DB needed)
- Hybrid search (semantic + keyword)
- RLS applies to vector data
- Scale with PostgreSQL infrastructure
- Integrate with any LLM (OpenAI, Hugging Face, etc.)

## Setup

### Enable pgvector Extension

```sql
-- Enable in Dashboard: Database > Extensions
-- Or via SQL:
CREATE EXTENSION IF NOT EXISTS vector;
```

### Create Vector Table

```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  embedding vector(1536),  -- OpenAI ada-002 dimensions
  created_at TIMESTAMPTZ DEFAULT now()
);

-- For other models:
-- text-embedding-3-small: vector(1536)
-- text-embedding-3-large: vector(3072)
-- Cohere embed-english-v3: vector(1024)
-- Hugging Face all-MiniLM-L6-v2: vector(384)
```

## Indexing Strategies

### HNSW Index (Recommended)

Best for most use cases. Faster queries, more memory.

```sql
-- Create HNSW index
CREATE INDEX ON documents
USING hnsw (embedding vector_cosine_ops);

-- With tuning parameters
CREATE INDEX ON documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- m: Max connections per node (default 16)
-- ef_construction: Build-time quality (default 64)
```

### IVFFlat Index

Better for memory-constrained environments.

```sql
-- Create IVFFlat index
-- lists = sqrt(rows) is a good starting point
CREATE INDEX ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Set probes at query time (higher = better recall, slower)
SET ivfflat.probes = 10;
```

### Distance Functions

| Function | Use Case | Index Ops |
|----------|----------|-----------|
| `<->` (L2) | Euclidean distance | `vector_l2_ops` |
| `<=>` (Cosine) | Semantic similarity | `vector_cosine_ops` |
| `<#>` (Inner Product) | Dot product | `vector_ip_ops` |

## Embedding Generation

### With OpenAI

```typescript
import OpenAI from 'openai';

const openai = new OpenAI();

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: text,
  });
  return response.data[0].embedding;
}

// Store document with embedding
async function storeDocument(content: string, metadata: object) {
  const embedding = await generateEmbedding(content);

  const { data, error } = await supabase
    .from('documents')
    .insert({
      content,
      metadata,
      embedding
    });

  return data;
}
```

### With Edge Function

```typescript
// supabase/functions/embed/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

serve(async (req) => {
  const { content, metadata } = await req.json();

  // Generate embedding
  const embeddingResponse = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'text-embedding-3-small',
      input: content
    })
  });

  const { data } = await embeddingResponse.json();
  const embedding = data[0].embedding;

  // Store in database
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );

  const { data: doc, error } = await supabase
    .from('documents')
    .insert({ content, metadata, embedding })
    .select()
    .single();

  return new Response(JSON.stringify(doc));
});
```

## Semantic Search

### Basic Similarity Search

```sql
-- Create search function
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  match_threshold FLOAT DEFAULT 0.78,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) AS similarity
  FROM documents
  WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

### Query from Client

```typescript
async function searchDocuments(query: string, limit = 10) {
  // Generate query embedding
  const queryEmbedding = await generateEmbedding(query);

  // Search similar documents
  const { data, error } = await supabase.rpc('match_documents', {
    query_embedding: queryEmbedding,
    match_threshold: 0.78,
    match_count: limit
  });

  return data;
}
```

### Hybrid Search (Semantic + Keyword)

```sql
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text TEXT,
  query_embedding vector(1536),
  match_count INT DEFAULT 10,
  full_text_weight FLOAT DEFAULT 1,
  semantic_weight FLOAT DEFAULT 1,
  rrf_k INT DEFAULT 50
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  score FLOAT
)
LANGUAGE sql
AS $$
WITH full_text AS (
  SELECT
    id,
    ROW_NUMBER() OVER (ORDER BY ts_rank_cd(to_tsvector('english', content), plainto_tsquery(query_text)) DESC) AS rank_ix
  FROM documents
  WHERE to_tsvector('english', content) @@ plainto_tsquery(query_text)
  ORDER BY rank_ix
  LIMIT LEAST(match_count, 30) * 2
),
semantic AS (
  SELECT
    id,
    ROW_NUMBER() OVER (ORDER BY embedding <=> query_embedding) AS rank_ix
  FROM documents
  ORDER BY rank_ix
  LIMIT LEAST(match_count, 30) * 2
)
SELECT
  documents.id,
  documents.content,
  documents.metadata,
  COALESCE(1.0 / (rrf_k + full_text.rank_ix), 0.0) * full_text_weight +
  COALESCE(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight AS score
FROM documents
LEFT JOIN full_text ON documents.id = full_text.id
LEFT JOIN semantic ON documents.id = semantic.id
WHERE full_text.rank_ix IS NOT NULL OR semantic.rank_ix IS NOT NULL
ORDER BY score DESC
LIMIT match_count;
$$;
```

## RAG (Retrieval-Augmented Generation)

### Complete RAG Pipeline

```typescript
async function ragQuery(userQuestion: string) {
  // 1. Search relevant documents
  const relevantDocs = await searchDocuments(userQuestion, 5);

  // 2. Build context from documents
  const context = relevantDocs
    .map(doc => doc.content)
    .join('\n\n---\n\n');

  // 3. Generate response with LLM
  const response = await openai.chat.completions.create({
    model: 'gpt-4-turbo-preview',
    messages: [
      {
        role: 'system',
        content: `You are a helpful assistant. Answer questions based on the following context. If the answer isn't in the context, say you don't know.

Context:
${context}`
      },
      {
        role: 'user',
        content: userQuestion
      }
    ]
  });

  return {
    answer: response.choices[0].message.content,
    sources: relevantDocs.map(d => ({ id: d.id, metadata: d.metadata }))
  };
}
```

### RAG with Streaming

```typescript
// Edge Function with streaming response
import { OpenAIStream, StreamingTextResponse } from 'ai';

serve(async (req) => {
  const { question } = await req.json();

  // Get context
  const docs = await searchDocuments(question);
  const context = docs.map(d => d.content).join('\n\n');

  // Stream response
  const response = await openai.chat.completions.create({
    model: 'gpt-4-turbo-preview',
    stream: true,
    messages: [
      { role: 'system', content: `Context:\n${context}` },
      { role: 'user', content: question }
    ]
  });

  const stream = OpenAIStream(response);
  return new StreamingTextResponse(stream);
});
```

## LangChain Integration

```typescript
import { SupabaseVectorStore } from '@langchain/community/vectorstores/supabase';
import { OpenAIEmbeddings } from '@langchain/openai';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, key);

// Create vector store
const vectorStore = await SupabaseVectorStore.fromTexts(
  ['Document 1 content', 'Document 2 content'],
  [{ source: 'doc1' }, { source: 'doc2' }],
  new OpenAIEmbeddings(),
  {
    client: supabase,
    tableName: 'documents',
    queryName: 'match_documents'
  }
);

// Similarity search
const results = await vectorStore.similaritySearch('query', 5);

// As retriever for chains
const retriever = vectorStore.asRetriever();
```

## Performance Optimization

### 1. Batch Embeddings

```typescript
// BAD: One at a time
for (const doc of documents) {
  const embedding = await generateEmbedding(doc.content);
  await supabase.from('documents').insert({ ...doc, embedding });
}

// GOOD: Batch embedding + insert
const embeddings = await openai.embeddings.create({
  model: 'text-embedding-3-small',
  input: documents.map(d => d.content)
});

const docsWithEmbeddings = documents.map((doc, i) => ({
  ...doc,
  embedding: embeddings.data[i].embedding
}));

await supabase.from('documents').insert(docsWithEmbeddings);
```

### 2. Partial Index for Filtered Queries

```sql
-- If you always filter by a column, create partial index
CREATE INDEX ON documents
USING hnsw (embedding vector_cosine_ops)
WHERE metadata->>'type' = 'article';
```

### 3. Approximate vs Exact Search

```sql
-- For exact results (slower, more accurate)
SET hnsw.ef_search = 200;  -- Higher = more accurate
SELECT * FROM documents
ORDER BY embedding <=> query_embedding
LIMIT 10;

-- For approximate results (faster)
SET hnsw.ef_search = 40;  -- Default
```

## RLS for Vector Data

```sql
-- Apply same RLS patterns as regular tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own documents" ON documents
  FOR SELECT USING (user_id = auth.uid());

-- Vector search respects RLS automatically
```

## Chunking Strategies

### Fixed Size Chunks

```typescript
function chunkText(text: string, chunkSize = 1000, overlap = 200): string[] {
  const chunks: string[] = [];
  let start = 0;

  while (start < text.length) {
    const end = Math.min(start + chunkSize, text.length);
    chunks.push(text.slice(start, end));
    start = end - overlap;
  }

  return chunks;
}
```

### Semantic Chunking

```typescript
// Split by paragraphs/sections
function semanticChunk(text: string): string[] {
  return text
    .split(/\n\n+/)
    .filter(chunk => chunk.trim().length > 100);
}
```

## Monitoring & Debugging

```sql
-- Check index usage
SELECT
  indexrelname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexrelname LIKE '%embedding%';

-- Analyze query performance
EXPLAIN ANALYZE
SELECT * FROM documents
ORDER BY embedding <=> '[...]'::vector
LIMIT 10;
```

## Best Practices

1. **Choose right embedding model** - Balance cost, dimensions, and quality
2. **Index appropriately** - HNSW for speed, IVFFlat for memory
3. **Batch operations** - Embed and insert in batches
4. **Chunk intelligently** - Semantic boundaries > fixed size
5. **Hybrid search** - Combine semantic + keyword for better results
6. **Monitor performance** - Track index usage and query times
7. **Apply RLS** - Same security model as regular data
