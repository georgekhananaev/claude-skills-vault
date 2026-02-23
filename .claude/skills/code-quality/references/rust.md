# Rust Standards

Safe, performant Rust with strict Clippy enforcement.

## Core Principles

- **No unwrap in production**: Use `?` or proper handling
- **Justify unsafe**: Comments required for unsafe blocks
- **Clippy pedantic**: Enable pedantic lints
- **Document public APIs**: All `pub` items documented

## Error Handling

### No unwrap/expect in Production

```rust
// CRITICAL: No unwrap in production code
let value = data.unwrap();        // Error
let value = data.expect("msg");   // Error - still panics

// OK: Use ? operator
fn process() -> Result<Value, Error> {
    let value = data?;            // OK - propagates error
    Ok(value)
}

// OK: Provide defaults
let value = data.unwrap_or_default();          // OK
let value = data.unwrap_or(fallback);          // OK
let value = data.unwrap_or_else(|| compute()); // OK - lazy

// OK: Handle explicitly
let value = match data {
    Some(v) => v,
    None => return Err(Error::NotFound),
};

// OK: if let for optional handling
if let Some(value) = data {
    process(value);
}
```

### Error Types

```rust
use thiserror::Error;

// Define domain-specific errors
#[derive(Error, Debug)]
pub enum AppError {
    #[error("User not found: {0}")]
    NotFound(String),

    #[error("Invalid input: {0}")]
    Validation(String),

    #[error("Database error")]
    Database(#[from] sqlx::Error),

    #[error("IO error")]
    Io(#[from] std::io::Error),
}

// Use Result everywhere
pub fn get_user(id: &str) -> Result<User, AppError> {
    let user = db.find(id)
        .map_err(|e| AppError::Database(e))?
        .ok_or_else(|| AppError::NotFound(id.to_string()))?;
    Ok(user)
}
```

## Unsafe Code

```rust
// ERROR: Unsafe without justification
unsafe {
    ptr::read(ptr)
}

// OK: Document safety requirements
// SAFETY: `ptr` is valid for reads, properly aligned, and
// points to an initialized value of type T. The caller
// guarantees these invariants through the function contract.
unsafe {
    ptr::read(ptr)
}

// Prefer safe abstractions
fn safe_wrapper(data: &[u8]) -> u32 {
    // SAFETY: We verify the slice has at least 4 bytes
    assert!(data.len() >= 4);
    unsafe { *(data.as_ptr() as *const u32) }
}
```

## Documentation

```rust
// WARNING: Missing documentation on public items
pub fn process() {}               // Warning

/// Processes the input data and returns the result.
///
/// # Arguments
///
/// * `input` - The raw input bytes to process
///
/// # Returns
///
/// The processed output, or an error if processing fails.
///
/// # Errors
///
/// Returns `ProcessError::InvalidInput` if the input is malformed.
///
/// # Examples
///
/// ```
/// let result = process(b"hello")?;
/// assert_eq!(result, "HELLO");
/// ```
pub fn process(input: &[u8]) -> Result<String, ProcessError> {
    // ...
}
```

## Clippy Configuration

```toml
# clippy.toml or in Cargo.toml
[lints.clippy]
# Deny these - always errors
unwrap_used = "deny"
expect_used = "deny"
panic = "deny"
todo = "deny"
unimplemented = "deny"
unreachable = "deny"
indexing_slicing = "deny"

# Warn on these
pedantic = "warn"
nursery = "warn"
cargo = "warn"
all = "warn"

# Allow specific pedantic lints that are too noisy
module_name_repetitions = "allow"
must_use_candidate = "allow"
missing_errors_doc = "allow"
```

### In Cargo.toml

```toml
[lints.rust]
unsafe_code = "warn"
missing_docs = "warn"

[lints.clippy]
all = "warn"
pedantic = "warn"
unwrap_used = "deny"
expect_used = "deny"
```

## Memory Safety Patterns

### Ownership and Borrowing

```rust
// Prefer borrowing over ownership when possible
fn process(data: &str) -> String {  // OK - borrows
    data.to_uppercase()
}

fn process(data: String) -> String {  // Only if ownership needed
    // ... modifies and returns ...
}

// Use Cow for flexibility
use std::borrow::Cow;

fn process(data: Cow<'_, str>) -> Cow<'_, str> {
    if needs_modification(&data) {
        Cow::Owned(modify(&data))
    } else {
        data  // No allocation if no modification
    }
}
```

### Lifetimes

```rust
// Explicit lifetimes when needed
struct Parser<'a> {
    input: &'a str,
}

impl<'a> Parser<'a> {
    fn parse(&self) -> Result<Token<'a>, Error> {
        // Token borrows from input
    }
}

// Elide when possible
fn first_word(s: &str) -> &str {  // Lifetime elision OK
    s.split_whitespace().next().unwrap_or("")
}
```

## Concurrency

```rust
use std::sync::{Arc, Mutex, RwLock};
use tokio::sync::mpsc;

// Shared state with Arc + Mutex
let shared = Arc::new(Mutex::new(Vec::new()));

let handle = {
    let shared = Arc::clone(&shared);
    tokio::spawn(async move {
        let mut data = shared.lock().unwrap();
        data.push(1);
    })
};

// Prefer channels for message passing
let (tx, mut rx) = mpsc::channel(100);

tokio::spawn(async move {
    while let Some(msg) = rx.recv().await {
        process(msg).await;
    }
});

tx.send(message).await?;
```

## Anti-Patterns

| Bad | Good | Why |
|-----|------|-----|
| `.unwrap()` | `?` or `unwrap_or` | No panics in prod |
| `.expect("msg")` | Proper error handling | No panics in prod |
| `unsafe {}` | Safe abstractions | Memory safety |
| `clone()` everywhere | Borrowing | Performance |
| `pub` on everything | Minimal visibility | Encapsulation |
| No docs on `pub` | Document everything | Usability |
| `String` params | `&str` params | Flexibility |
| `.to_string()` in loops | Cow or pre-allocate | Allocations |

## Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_process_valid_input() {
        let result = process(b"hello").unwrap();
        assert_eq!(result, "HELLO");
    }

    #[test]
    fn test_process_empty_input() {
        let result = process(b"");
        assert!(matches!(result, Err(ProcessError::EmptyInput)));
    }

    // Property-based testing with proptest
    proptest! {
        #[test]
        fn doesnt_crash(s: String) {
            let _ = process(s.as_bytes());
        }
    }
}
```

## Dependencies

```bash
# Audit dependencies
cargo audit

# Check for outdated deps
cargo outdated

# Security advisories
cargo deny check
```