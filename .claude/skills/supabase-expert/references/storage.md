# Storage

Supabase Storage for file uploads, downloads, and transformations with S3-compatible API.

## Bucket Types

| Type | Access | Use Case |
|------|--------|----------|
| Public | Anyone with URL | Avatars, public assets |
| Private | Authenticated + RLS | User documents, sensitive files |

## Bucket Management

### Create Bucket

```sql
-- Via SQL
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true);

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'documents',
  'documents',
  false,
  52428800,  -- 50MB
  ARRAY['application/pdf', 'image/png', 'image/jpeg']
);
```

```typescript
// Via client (requires service_role)
const { data, error } = await supabaseAdmin.storage.createBucket('avatars', {
  public: true,
  fileSizeLimit: 1024 * 1024 * 5, // 5MB
  allowedMimeTypes: ['image/png', 'image/jpeg', 'image/webp']
});
```

### List Buckets

```typescript
const { data: buckets } = await supabase.storage.listBuckets();
```

## Storage RLS Policies

**Important:** Storage RLS is separate from database RLS. Configure policies in Dashboard or SQL.

### Policy Structure

```sql
-- Storage policies use storage.objects table
-- Columns: bucket_id, name (path), owner, metadata

-- Allow authenticated users to upload to their folder
CREATE POLICY "Users can upload own avatar"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'avatars' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow users to read their own files
CREATE POLICY "Users can read own files"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'documents' AND
  owner = auth.uid()
);

-- Allow users to update their own files
CREATE POLICY "Users can update own files"
ON storage.objects FOR UPDATE
TO authenticated
USING (owner = auth.uid());

-- Allow users to delete their own files
CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE
TO authenticated
USING (owner = auth.uid());
```

### Public Bucket Policies

```sql
-- Anyone can read from public bucket
CREATE POLICY "Public read"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'public-assets');

-- Only authenticated can upload
CREATE POLICY "Authenticated upload"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'public-assets');
```

### Multi-Tenant Storage

```sql
-- Files organized by tenant: {tenant_id}/{user_id}/filename
CREATE POLICY "Tenant isolation"
ON storage.objects FOR ALL
TO authenticated
USING (
  (storage.foldername(name))[1] = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')
)
WITH CHECK (
  (storage.foldername(name))[1] = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')
);
```

## File Operations

### Upload

```typescript
// Simple upload
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`${userId}/avatar.png`, file, {
    cacheControl: '3600',
    upsert: true,  // Overwrite if exists
    contentType: 'image/png'
  });

// Upload from base64
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`${userId}/avatar.png`, decode(base64String), {
    contentType: 'image/png'
  });

// Upload with progress
const { data, error } = await supabase.storage
  .from('documents')
  .upload(path, file, {
    onUploadProgress: (progress) => {
      const percent = (progress.loaded / progress.total) * 100;
      console.log(`Upload progress: ${percent}%`);
    }
  });
```

### Resumable Upload (Large Files)

```typescript
// For files >6MB, use resumable uploads
const { data, error } = await supabase.storage
  .from('large-files')
  .uploadToSignedUrl(path, token, file, {
    // Automatically resumes on failure
  });

// Create upload URL for external upload
const { data: { signedUrl } } = await supabase.storage
  .from('large-files')
  .createSignedUploadUrl(path);

// Upload with TUS protocol client
import * as tus from 'tus-js-client';

const upload = new tus.Upload(file, {
  endpoint: signedUrl,
  retryDelays: [0, 1000, 3000, 5000],
  onProgress: (bytesUploaded, bytesTotal) => {
    console.log(`${(bytesUploaded / bytesTotal * 100).toFixed(2)}%`);
  }
});

upload.start();
```

### Download

```typescript
// Download file
const { data, error } = await supabase.storage
  .from('documents')
  .download(`${userId}/document.pdf`);

// data is a Blob
const url = URL.createObjectURL(data);

// Get public URL (public buckets only)
const { data: { publicUrl } } = supabase.storage
  .from('avatars')
  .getPublicUrl(`${userId}/avatar.png`);

// Get signed URL (private buckets)
const { data: { signedUrl } } = await supabase.storage
  .from('documents')
  .createSignedUrl(`${userId}/document.pdf`, 3600); // 1 hour expiry
```

### List Files

```typescript
const { data: files, error } = await supabase.storage
  .from('documents')
  .list(userId, {
    limit: 100,
    offset: 0,
    sortBy: { column: 'created_at', order: 'desc' }
  });

// files = [{ name, id, created_at, updated_at, metadata }]
```

### Delete

```typescript
// Single file
const { error } = await supabase.storage
  .from('documents')
  .remove([`${userId}/document.pdf`]);

// Multiple files
const { error } = await supabase.storage
  .from('documents')
  .remove([
    `${userId}/doc1.pdf`,
    `${userId}/doc2.pdf`
  ]);

// Delete folder (all files in path)
const { data: files } = await supabase.storage
  .from('documents')
  .list(userId);

await supabase.storage
  .from('documents')
  .remove(files.map(f => `${userId}/${f.name}`));
```

### Move/Copy

```typescript
// Move file
const { error } = await supabase.storage
  .from('documents')
  .move('old/path/file.pdf', 'new/path/file.pdf');

// Copy file
const { error } = await supabase.storage
  .from('documents')
  .copy('source/file.pdf', 'destination/file.pdf');
```

## Image Transformations

Transform images on-the-fly via URL parameters.

### Transform Options

```typescript
const { data: { publicUrl } } = supabase.storage
  .from('avatars')
  .getPublicUrl('user/avatar.png', {
    transform: {
      width: 200,
      height: 200,
      resize: 'cover',     // cover, contain, fill
      format: 'webp',      // origin, webp
      quality: 80          // 1-100
    }
  });
```

### URL-based Transforms

```
https://project.supabase.co/storage/v1/render/image/public/avatars/user/avatar.png?width=200&height=200&resize=cover
```

### Common Transform Patterns

```typescript
// Thumbnail
const thumbnail = supabase.storage
  .from('images')
  .getPublicUrl('photo.jpg', {
    transform: { width: 150, height: 150, resize: 'cover' }
  });

// Optimized for web
const webOptimized = supabase.storage
  .from('images')
  .getPublicUrl('photo.jpg', {
    transform: { width: 1200, format: 'webp', quality: 80 }
  });

// Avatar circle (use CSS for actual circle)
const avatar = supabase.storage
  .from('avatars')
  .getPublicUrl('user.jpg', {
    transform: { width: 100, height: 100, resize: 'cover' }
  });
```

## CDN & Caching

### Cache Headers

```typescript
// Set cache control on upload
await supabase.storage
  .from('assets')
  .upload('logo.png', file, {
    cacheControl: '31536000', // 1 year
    upsert: true
  });
```

### CDN URLs

```
// Direct storage URL
https://project.supabase.co/storage/v1/object/public/bucket/file.png

// CDN URL (faster, cached globally)
https://project.supabase.co/storage/v1/object/public/bucket/file.png
// Supabase automatically serves through CDN
```

## File Validation

### Client-Side

```typescript
const MAX_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

const validateFile = (file: File) => {
  if (file.size > MAX_SIZE) {
    throw new Error('File too large');
  }
  if (!ALLOWED_TYPES.includes(file.type)) {
    throw new Error('Invalid file type');
  }
  return true;
};
```

### Server-Side (Bucket Config)

```sql
UPDATE storage.buckets
SET
  file_size_limit = 5242880,  -- 5MB
  allowed_mime_types = ARRAY['image/jpeg', 'image/png', 'image/webp']
WHERE id = 'avatars';
```

## Signed URLs for External Access

### Upload URL (Allow External Upload)

```typescript
// Generate signed upload URL
const { data: { signedUrl, token, path } } = await supabase.storage
  .from('uploads')
  .createSignedUploadUrl(`user-${userId}/file.pdf`);

// Client can upload directly
await fetch(signedUrl, {
  method: 'PUT',
  body: file,
  headers: {
    'Content-Type': 'application/pdf'
  }
});
```

### Download URL (Time-Limited Access)

```typescript
// Generate signed download URL
const { data: { signedUrl } } = await supabase.storage
  .from('private-docs')
  .createSignedUrl('sensitive-report.pdf', 300); // 5 minutes

// Multiple signed URLs
const { data: signedUrls } = await supabase.storage
  .from('documents')
  .createSignedUrls(['doc1.pdf', 'doc2.pdf'], 3600);
```

## Database Integration

### Store File References

```sql
CREATE TABLE user_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  bucket_id TEXT NOT NULL DEFAULT 'documents',
  file_path TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_size INTEGER,
  mime_type TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Trigger to clean up storage on delete
CREATE OR REPLACE FUNCTION delete_storage_object()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM storage.delete_object(OLD.bucket_id, OLD.file_path);
  RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER delete_document_file
  BEFORE DELETE ON user_documents
  FOR EACH ROW EXECUTE FUNCTION delete_storage_object();
```

### Query with URLs

```typescript
const { data: documents } = await supabase
  .from('user_documents')
  .select('*')
  .eq('user_id', userId);

// Add signed URLs
const docsWithUrls = await Promise.all(
  documents.map(async (doc) => {
    const { data: { signedUrl } } = await supabase.storage
      .from(doc.bucket_id)
      .createSignedUrl(doc.file_path, 3600);

    return { ...doc, url: signedUrl };
  })
);
```

## Best Practices

1. **Use appropriate bucket visibility** - Public for avatars/assets, private for documents
2. **Set file size limits** - Prevent abuse
3. **Validate MIME types** - Both client and server side
4. **Use signed URLs for sensitive files** - Never expose permanent URLs
5. **Implement RLS policies** - Separate from database RLS
6. **Cache aggressively** - Set appropriate cache headers
7. **Use image transforms** - Don't store multiple sizes
8. **Clean up orphaned files** - Use database triggers
