# MoneyFlow Backend

## Overview

MoneyFlow Backend is a RESTful API service built with Flask that provides comprehensive financial management capabilities. The application enables users to track expenses and incomes across multiple currencies with real-time conversion rates, detailed financial analytics and reporting.

## Key Features

- **Multi-Currency Support**: Handle transactions in multiple currencies with automatic conversion
- **Real-time Exchange Rates**: Live currency conversion using up-to-date exchange rates
- **Expense and Income Management**: Create, read, update, and delete expense records with categorization
- **Financial Analytics**: Calculate totals and balances across date ranges
- **User Profiles**: Manage user preferences including default currency settings

## Technology Stack

- **Framework**: Flask - Python
- **Database**: PostgreSQL
- **Authentication**: JWT-based authentication (Keycloak OAuth2 integration ongoing)
- **Server**: Gunicorn WSGI server
- **Testing**: Pytest integration tests

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone 
cd MoneyFlow_Backend
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

#### Development Mode
```bash
python app.py
```

#### Production Mode
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Options:
- `-w 4`: Number of worker processes (adjust based on CPU cores)
- `-b 0.0.0.0:5000`: Bind to all network interfaces on port 5000
- `app:app`: Module name and application instance

The API will be available at `http://localhost:5000`

## API Documentation

### Base URL
```
http://localhost:5000/api/v1
```

### Main Endpoints

#### Authentication
- `POST /login` - User authentication

#### User Management
- `GET /me` - Get current user profile
- `PATCH /edit_user` - Update user settings (including currency)

#### Expenses
- `POST /expenses/insert` - Create new expense
- `GET /expenses/list` - List all expenses
- `GET /expenses/total` - Get total expenses (with date range)
- `GET /expenses/list_categories` - List expense categories
- `DELETE /expenses/{id}` - Delete specific expense

#### Incomes
- `POST /incomes/insert` - Create new income
- `GET /incomes/list` - List all incomes
- `GET /incomes/total` - Get total incomes (with date range)
- `GET /incomes/list_categories` - List income categories
- `DELETE /incomes/{id}` - Delete specific income

#### Balances
- `GET /balances/total` - Calculate net balance (incomes - expenses)


## Testing

For complete documentation on the test suite, see [Test Suite Documentation](./docs/TESTING.md)

The test suite includes:
-Integration tests for Currency, Expenses and Incomes
-Automatic cleanup system
-Real-time API performance monitoring
-Comprehensive reporting with detailed metrics

### Quick Start Testing
```bash
# Execute all tests
python3 tests/run_tests.py

# Execute specific tests
python3 tests/run_tests.py --type currency
python3 tests/run_tests.py --type expenses
python3 tests/run_tests.py --type incomes
```