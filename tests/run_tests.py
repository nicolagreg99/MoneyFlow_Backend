#!/usr/bin/env python3
import pytest
import sys
import argparse
import os

def run_tests(test_type=None, verbose=False):
    # Base args - usa doppio -s per forzare l'output
    args = ["-s", "-s"]  # Doppio -s per essere sicuri
    
    if verbose:
        args.append("-v")
    
    if test_type == "unit":
        args.append("tests/unit")
    elif test_type == "integration":
        args.append("tests/integration")
    elif test_type == "currency":
        args.append("tests/integration/test_currency.py")
    elif test_type == "expenses":
        args.append("tests/integration/test_expenses.py")
    elif test_type == "incomes":
        args.append("tests/integration/test_incomes.py")
    else:
        args.append("tests/")
    
    args.extend([
        "--tb=short",      # Traceback corto
        "--durations=0",   # Mostra tutti i tempi
        "--color=yes",     # Output colorato
        "--capture=no"     # Disabilita completamente la cattura
    ])
    
    print("Starting MoneyFlow Backend Test Suite...")
    print("Real-time API monitoring enabled")
    print("=" * 80)
    
    sys.stdout.flush()
    sys.stderr.flush()
    
    result = pytest.main(args)
    
    print("=" * 80)
    if result == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("💥 SOME TESTS FAILED!")
    
    sys.exit(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Esegui i test API")
    parser.add_argument("--type", choices=["all", "unit", "integration", "currency", "expenses", "incomes"], 
                       default="all", help="Tipo di test da eseguire")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output verboso")
    
    args = parser.parse_args()
    
    test_type = None if args.type == "all" else args.type
    run_tests(test_type, args.verbose)