# MoneyFlow Backend

## Start
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Testing

Per la documentazione completa sulla test suite, consulta [Test Suite Documentation](./docs/TESTING.md)

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