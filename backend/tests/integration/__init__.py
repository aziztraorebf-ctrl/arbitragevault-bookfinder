"""
Integration Tests Package
=========================

Tests avec vraies donnees API externes (Keepa, etc.)

IMPORTANT:
- Ces tests consomment des tokens API reels
- Run manuellement avant releases production
- Skip par defaut dans CI/CD (mark: integration)

Usage:
    # Run all integration tests
    pytest tests/integration/ -v -m integration

    # Run specific test file
    pytest tests/integration/test_keepa_parser_real_api.py -v

    # Run avec coverage
    pytest tests/integration/ -v --cov=app.services
"""
