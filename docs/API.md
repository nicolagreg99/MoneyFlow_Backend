# API Documentation

## Base URL
```
http://localhost:5000/api/v1
```

## Authentication

All endpoints except `/login` require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints

### Authentication

#### POST /login

Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "nicola",
    "currency": "EUR"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": "Invalid credentials"
}
```

---

### User Management

#### GET /me

Get current user profile information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "nicola",
  "email": "user@example.com",
  "currency": "EUR",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### PATCH /edit_user

Update user settings, including preferred currency.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "currency": "USD"
}
```

**Response (200 OK):**
```json
{
  "message": "User updated successfully",
  "user": {
    "id": 1,
    "username": "nicola",
    "currency": "USD"
  }
}
```

**Supported Currencies:**
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- JPY (Japanese Yen)
- CHF (Swiss Franc)
- And more...

---

### Expenses

#### POST /expenses/insert

Create a new expense record.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "valore": 100.00,
  "tipo": "Food",
  "giorno": "2024-01-15",
  "currency": "USD",
  "fields": {
    "descrizione": "Grocery shopping"
  }
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "valore": 100.00,
  "tipo": "Food",
  "giorno": "2024-01-15",
  "currency": "USD",
  "converted_value": 91.37,
  "user_currency": "EUR",
  "fields": {
    "descrizione": "Grocery shopping"
  },
  "created_at": "2024-01-15T14:30:00Z"
}
```

#### GET /expenses/list

List all expenses for the authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `from_date` (optional): Filter from date (YYYY-MM-DD)
- `to_date` (optional): Filter to date (YYYY-MM-DD)
- `tipo` (optional): Filter by category

**Response (200 OK):**
```json
{
  "expenses": [
    {
      "id": 123,
      "valore": 100.00,
      "tipo": "Food",
      "giorno": "2024-01-15",
      "currency": "USD",
      "converted_value": 91.37,
      "user_currency": "EUR",
      "conversion_rate": 0.9137,
      "fields": {
        "descrizione": "Grocery shopping"
      }
    }
  ],
  "total": 1,
  "user_currency": "EUR"
}
```

#### GET /expenses/total

Get total expenses amount with optional date range filtering.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD)
- `to_date` (optional): End date (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "total": 1250.50,
  "currency": "EUR",
  "count": 15,
  "from_date": "2024-01-01",
  "to_date": "2024-01-31"
}
```

#### GET /expenses/list_categories

List all expense categories with totals.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD)
- `to_date` (optional): End date (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "categories": [
    {
      "tipo": "Food",
      "total": 450.00,
      "count": 12
    },
    {
      "tipo": "Transport",
      "total": 200.00,
      "count": 8
    },
    {
      "tipo": "Entertainment",
      "total": 150.00,
      "count": 5
    }
  ],
  "currency": "EUR"
}
```

#### DELETE /expenses/{id}

Delete a specific expense record.

**Headers:**
```
Authorization: Bearer <token>
```

**URL Parameters:**
- `id`: Expense ID (integer)

**Response (200 OK):**
```json
{
  "message": "Expense deleted successfully",
  "id": 123
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Expense not found"
}
```

---

### Incomes

#### POST /incomes/insert

Create a new income record.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "valore": 2000.00,
  "tipo": "Salary",
  "giorno": "2024-01-01",
  "currency": "USD",
  "fields": {
    "descrizione": "Monthly salary"
  }
}
```

**Response (201 Created):**
```json
{
  "id": 456,
  "valore": 2000.00,
  "tipo": "Salary",
  "giorno": "2024-01-01",
  "currency": "USD",
  "converted_value": 1827.40,
  "user_currency": "EUR",
  "fields": {
    "descrizione": "Monthly salary"
  },
  "created_at": "2024-01-01T10:00:00Z"
}
```

#### GET /incomes/list

List all incomes for the authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `from_date` (optional): Filter from date (YYYY-MM-DD)
- `to_date` (optional): Filter to date (YYYY-MM-DD)
- `tipo` (optional): Filter by category

**Response (200 OK):**
```json
{
  "incomes": [
    {
      "id": 456,
      "valore": 2000.00,
      "tipo": "Salary",
      "giorno": "2024-01-01",
      "currency": "USD",
      "converted_value": 1827.40,
      "user_currency": "EUR",
      "conversion_rate": 0.9137,
      "fields": {
        "descrizione": "Monthly salary"
      }
    }
  ],
  "total": 1,
  "user_currency": "EUR"
}
```

#### GET /incomes/total

Get total incomes amount with optional date range filtering.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD)
- `to_date` (optional): End date (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "total": 6000.00,
  "currency": "EUR",
  "count": 3,
  "from_date": "2024-01-01",
  "to_date": "2024-03-31"
}
```

#### GET /incomes/list_categories

List all income categories with totals.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD)
- `to_date` (optional): End date (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "categories": [
    {
      "tipo": "Salary",
      "total": 6000.00,
      "count": 3
    },
    {
      "tipo": "Freelance",
      "total": 1500.00,
      "count": 5
    }
  ],
  "currency": "EUR"
}
```

#### DELETE /incomes/{id}

Delete a specific income record.

**Headers:**
```
Authorization: Bearer <token>
```

**URL Parameters:**
- `id`: Income ID (integer)

**Response (200 OK):**
```json
{
  "message": "Income deleted successfully",
  "id": 456
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Income not found"
}
```

---

### Balances

#### GET /balances/total

Calculate net balance (total incomes minus total expenses).

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `from_date` (optional): Start date (YYYY-MM-DD)
- `to_date` (optional): End date (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "balance": 4750.50,
  "total_incomes": 6000.00,
  "total_expenses": 1249.50,
  "currency": "EUR",
  "from_date": "2024-01-01",
  "to_date": "2024-03-31"
}
```
---

### Assets

Assets represent the user’s wealth distribution across banks, asset types, and currencies.
All amounts are automatically converted to the user’s preferred currency when aggregated.

---

#### POST /assets/insert

Create a new asset entry.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "bank": "Revolut",
  "asset_type": "LIQUIDITY",
  "currency": "EUR",
  "amount": 1000,
  "is_payable": false
}
```
**Response (201 Created):**
```json
{
  "message": "Asset added successfully."
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Invalid asset data"
}
```

#### GET /assets/list

List all assets for the authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `is_payable` (optional): If `true` returns only payable assets (No stocks, ETF ecc.)


**Response:**
```json
{
[
  {
    "id": 1,
    "bank": "Revolut",
    "asset_type": "LIQUIDITY",
    "currency": "EUR",
    "amount": "1000",
    "exchange_rate": "1.0",
    "last_updated": "2026-01-25T09:47:20Z"
  },
  {
    "id": 2,
    "bank": "Revolut",
    "asset_type": "ETF",
    "currency": "EUR",
    "amount": "2800",
    "exchange_rate": "1.0",
    "last_updated": "2026-01-25T10:03:04Z"
  }
]
}
```

#### GET /assets/total

Total assets

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `asset_type` (optional): Filter by asset type
- `group_by` (optional): Aggregate results by bank or asset_type

**Response:**
```json
{
  "total": 8021.69,
  "currency": "EUR"
}
```

**Response (group by):**
```json
{
  "currency": "EUR",
  "group_by": "asset_type",
  "results": [
    {
      "asset_type": "LIQUIDITY",
      "total": 1507.23
    },
    {
      "asset_type": "STOCK",
      "total": 1014.46
    }
  ]
}
```
































---

## Currency Conversion

All monetary values are automatically converted to the user's preferred currency. The conversion process:

1. Each transaction stores its original amount and currency
2. When retrieved, amounts are converted to the user's current currency preference
3. Conversion rates are fetched in real-time from external APIs
4. Both original and converted values are returned in responses

**Example:**
- User currency: EUR
- Expense created: 100 USD
- Response includes:
  - `valore`: 100.00 (original)
  - `currency`: "USD" (original)
  - `converted_value`: 91.37 (in EUR)
  - `user_currency`: "EUR"
  - `conversion_rate`: 0.9137

---

## Error Responses

The API uses standard HTTP status codes:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

**Error Response Format:**
```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "details": {}
}
```

---

## Rate Limiting

Currently, there are no rate limits implemented. This may change in future versions.

---

## Versioning

The API is versioned through the URL path (`/api/v1`). Breaking changes will result in a new version number.

---

## Support

For issues or questions regarding the API, please open an issue on the GitHub repository.