# Testing Configuration - Admin Token Bypass

## Overview

The `REQUIRE_ADMIN_TOKEN` environment variable allows you to disable admin token authentication during testing and development. This is useful when you want to rapidly test configuration updates without needing to manage authentication tokens.

## Configuration

### Disabling Admin Token (For Testing)

Add this to your `.env` file:

```env
REQUIRE_ADMIN_TOKEN=False
```

When set to `False`:
- ✅ All `/config/update` requests will be accepted without authentication
- ✅ No admin token required in the frontend
- ⚠️ **WARNING**: Only use this in development/testing environments!

### Enabling Admin Token (Production)

For production environments, set:

```env
REQUIRE_ADMIN_TOKEN=True
RUNTIME_ADMIN_TOKEN=your-secure-token-here
```

When set to `True`:
- 🔒 Admin token validation is enforced
- 🔒 Requires valid `RUNTIME_ADMIN_TOKEN` or `ADMIN_API_TOKEN` in environment
- 🔒 Requests must include token via `Authorization: Bearer <token>` header

## Quick Start

1. **Edit your `.env` file:**
   ```bash
   # Add or update this line
   REQUIRE_ADMIN_TOKEN=False
   ```

2. **Restart your backend:**
   ```bash
   # Stop the backend if running (Ctrl+C)
   # Then restart:
   cd backend
   python main.py
   ```

3. **Test configuration updates:**
   - Open the frontend (Streamlit)
   - Go to "Runtime Settings" → "Credentials & Mode"
   - You can now update settings without providing an admin token!

## How It Works

The configuration changes are in `backend/config.py`:

- **`REQUIRE_ADMIN_TOKEN` env var**: Controls whether token validation is enforced
- **`validate_admin_token()` method**: Returns `True` immediately if `REQUIRE_ADMIN_TOKEN=False`
- **Logging**: Shows clear warning message when token validation is disabled

## Security Note

⚠️ **IMPORTANT**: 
- `REQUIRE_ADMIN_TOKEN=False` should **NEVER** be used in production
- This setting bypasses all authentication for configuration endpoints
- Only use in local development or testing environments
- In production, always set `REQUIRE_ADMIN_TOKEN=True` with a strong token

## Troubleshooting

### Still getting "Invalid or missing admin token" error?

1. Check your `.env` file has `REQUIRE_ADMIN_TOKEN=False`
2. Restart the backend completely (Ctrl+C and restart)
3. Check backend logs for: `"REQUIRE_ADMIN_TOKEN is False - admin token validation is DISABLED"`
4. Clear your browser cache or try in incognito mode

### Can't find `.env` file?

If you don't have a `.env` file:
```bash
# Copy the template
cp .env.template .env

# Then edit it to add REQUIRE_ADMIN_TOKEN=False
```

## Example Log Output

When `REQUIRE_ADMIN_TOKEN=False`, you should see this in your backend logs:

```
WARNING:root:REQUIRE_ADMIN_TOKEN is False - admin token validation is DISABLED for testing/development
INFO:root:Configuration loaded in TEST_MODE - external API keys are optional
```

This confirms the setting is active and working correctly.
