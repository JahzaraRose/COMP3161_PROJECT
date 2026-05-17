# Railway Deployment

This project can run on Railway as a Flask API backed by MySQL and Redis.

## Start Command

Railway can use the included `Procfile`:

```text
web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 run:app
```

If Railway builds from the included `Dockerfile`, the container command also binds to `0.0.0.0:${PORT:-5000}`.

## Required Variables

Set these in the Railway service variables:

```text
JWT_SECRET_KEY=<long-random-secret>
FLASK_DEBUG=false
```

Railway provides `PORT` automatically. Do not hardcode it.

If you need to create an admin through `POST /api/register`, temporarily set:

```text
ADMIN_REGISTRATION_CODE=<one-time-secret>
```

Then include the same value as `admin_registration_code` in the request body. Remove or rotate it after bootstrapping admins.

## MySQL Variables

The app reads database credentials from environment variables only. It supports any one of these styles:

```text
DATABASE_URL=mysql://user:password@host:3306/database
```

or:

```text
MYSQLHOST=<railway-mysql-host>
MYSQLPORT=<railway-mysql-port>
MYSQLUSER=<railway-mysql-user>
MYSQLPASSWORD=<railway-mysql-password>
MYSQLDATABASE=<railway-mysql-database>
```

or the local development names:

```text
DB_HOST=<host>
DB_PORT=3306
DB_USER=<user>
DB_PASSWORD=<password>
DB_NAME=<database>
```

## Redis Variable

Attach a Redis service and set:

```text
REDIS_URL=<railway-redis-url>
```

If Redis is unavailable, API requests still work; cache operations fail closed.

## Frontend API URL

The React frontend is a Vite app. For deployed frontend builds, set:

```text
VITE_API_BASE_URL=https://your-api-service.up.railway.app/api
```

For local development, the default is `/api`, which works with the Vite proxy in `frontend/vite.config.js`.
The local proxy target defaults to `http://localhost:5000` and can be changed with `VITE_API_PROXY_TARGET`.

## Database Schema

Before using the API, initialize MySQL with:

```text
database/schema.sql
```

Seed data is optional and lives in:

```text
database/populate.sql
```
