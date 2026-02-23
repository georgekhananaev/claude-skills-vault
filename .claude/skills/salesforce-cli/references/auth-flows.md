# Salesforce Authentication Flows

Detailed setup instructions for each authentication method.

## 1. Web Login (Interactive — Development)

Best for local development. Opens a browser for OAuth 2.0 authorization.

```bash
# Default org (login.salesforce.com)
sf org login web --alias my-org --set-default

# Sandbox (test.salesforce.com)
sf org login web --alias my-sandbox --instance-url https://test.salesforce.com

# Custom domain
sf org login web --alias my-org --instance-url https://mycompany.my.salesforce.com

# Set as default Dev Hub
sf org login web --alias my-hub --set-default-dev-hub
```

### After Login

Verify the connection:

```bash
sf org display --target-org my-org
sf auth list
```

Tokens are stored in `~/.sf/` and auto-refreshed.

---

## 2. JWT Bearer Flow (CI/CD — Non-Interactive)

Best for automated pipelines. Requires a Connected App with digital certificate.

### Setup Steps

1. **Generate key pair:**

```bash
# Generate private key
openssl genrsa -out server.key 2048

# Generate certificate
openssl x509 -req -in server.csr -signkey server.key -out server.crt -days 365

# Or self-signed in one step
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes \
  -subj "/CN=SalesforceCLI"
```

2. **Create Connected App in Salesforce:**
   - Setup → App Manager → New Connected App
   - Enable OAuth Settings
   - Callback URL: `http://localhost:1717/OauthRedirect`
   - Select scopes: `api`, `refresh_token`, `offline_access`
   - Enable "Use digital signatures" → upload `server.crt`

3. **Pre-authorize the Connected App:**
   - Setup → Manage Connected Apps → Edit policies
   - Permitted Users: "Admin approved users are pre-authorized"
   - Add Profiles or Permission Sets

4. **Login via JWT:**

```bash
sf org login jwt \
  --client-id <connected_app_consumer_key> \
  --jwt-key-file server.key \
  --username user@example.com \
  --instance-url https://login.salesforce.com \
  --alias my-org \
  --set-default
```

### Security Notes

- **Never commit** `server.key` to git — add to `.gitignore`
- Store Consumer Key in CI/CD secrets (e.g., GitHub Actions secrets)
- Rotate certificates periodically
- Use separate Connected Apps per environment (dev, staging, prod)

---

## 3. SFDX Auth URL (Transfer Auth Between Systems)

Best for sharing auth context between machines without raw credentials.

### Export Auth URL

```bash
# Get the auth URL from an authorized org
sf org display --target-org my-org --verbose --json | jq -r '.result.sfdxAuthUrl' > auth.txt
```

### Import Auth URL

```bash
sf org login sfdx-url --sfdx-url-file auth.txt --alias my-org --set-default
```

### Format

The SFDX Auth URL format:
```
force://<clientId>:<clientSecret>:<refreshToken>@<instanceUrl>
```

### Security Notes

- Auth URL contains refresh token — treat as a secret
- Never commit to git
- Use CI/CD secrets or encrypted storage
- Delete file after use: `rm auth.txt`

---

## 4. Device Flow (Headless Environments)

For environments where a browser is not available (SSH servers, containers).

```bash
sf org login device
```

This outputs:
1. A URL to visit on any device
2. A code to enter on that page

After authorizing on the device, the CLI session is authenticated.

---

## 5. Access Token (One-Off Operations)

For quick operations when you already have a valid access token.

```bash
# Interactive (prompts for token)
sf org login access-token --instance-url https://mycompany.my.salesforce.com

# Non-interactive (pipe token)
echo $SALESFORCE_TOKEN | sf org login access-token \
  --instance-url https://mycompany.my.salesforce.com --no-prompt --alias my-org
```

**Note:** Access tokens expire (typically 2 hours). Not suitable for long-running operations.

---

## Managing Auth

### List All Authorized Orgs

```bash
sf org list          # Active orgs
sf org list --all    # Include expired scratch orgs
sf auth list         # Auth connections
```

### Set Default Org

```bash
sf config set target-org my-org        # Default target org
sf config set target-dev-hub my-hub    # Default Dev Hub
```

### Remove Auth

```bash
sf org logout --target-org my-org      # Remove single org (Destructive — confirm first)
sf org logout --all                    # Remove all (Forbidden — triple confirmation)
```

### Refresh Expired Auth

```bash
# Web login re-auth
sf org login web --alias my-org

# JWT re-auth (uses existing key)
sf org login jwt --client-id <key> --jwt-key-file server.key --username user@example.com --alias my-org
```

---

## CI/CD Configuration Examples

### GitHub Actions

```yaml
- name: Authenticate Salesforce
  run: |
    echo "${{ secrets.SFDX_AUTH_URL }}" > auth.txt
    sf org login sfdx-url --sfdx-url-file auth.txt --alias target-org --set-default
    rm auth.txt
```

### JWT in GitHub Actions

```yaml
- name: Authenticate via JWT
  run: |
    echo "${{ secrets.SF_JWT_KEY }}" > server.key
    sf org login jwt \
      --client-id ${{ secrets.SF_CONSUMER_KEY }} \
      --jwt-key-file server.key \
      --username ${{ secrets.SF_USERNAME }} \
      --alias target-org \
      --set-default
    rm server.key
```

---

## Auth Storage

| Location | Contents |
|----------|----------|
| `~/.sf/` | Auth files, org configs |
| `~/.sf/org/` | Per-org auth data |
| Project `sfdx-project.json` | Project config (no secrets) |

**Never share or commit** the `~/.sf/` directory contents.
