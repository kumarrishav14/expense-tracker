# Expenses Tool 2 - Development Makefile
# =====================================

.PHONY: help install test test-db test-sanity clean lint format

# Default target
help:
	@echo "Expenses Tool 2 - Available Commands"
	@echo "==================================="
	@echo ""
	@echo "🔧 Development Commands:"
	@echo "  make install      Install dependencies using uv"
	@echo "  make test         Run all tests"
	@echo "  make test-db      Run all database tests"
	@echo "  make test-sanity  Run database sanity tests (CRITICAL for DB changes)"
	@echo "  make lint         Run code linting"
	@echo "  make format       Format code"
	@echo "  make clean        Clean temporary files"
	@echo ""
	@echo "🔍 Database Sanity Tests:"
	@echo "  make sanity-quick    Quick sanity validation (~10 seconds)"
	@echo "  make sanity-verbose  Detailed sanity test output"
	@echo "  make sanity-coverage Sanity tests with coverage analysis"
	@echo ""
	@echo "📋 Usage Notes:"
	@echo "  • Run 'make test-sanity' before committing database changes"
	@echo "  • Use 'make sanity-quick' for fast validation in CI/CD"
	@echo "  • All sanity tests MUST pass before production deployment"

# Installation
install:
	@echo "📦 Installing dependencies with uv..."
	uv sync
	@echo "✅ Dependencies installed!"

# Test Commands
test:
	@echo "🧪 Running all tests..."
	python -m pytest tests/ -v

test-db:
	@echo "🗄️ Running all database tests..."
	python -m pytest tests/db_tests/ --tb=no

test-sanity:
	@echo "🔍 Running database sanity tests..."
	@./tests/db_tests/run_sanity_tests.sh

# Database Sanity Test Variants
sanity-quick:
	@echo "⚡ Running quick database sanity validation..."
	@./tests/db_tests/run_sanity_tests.sh --quick

sanity-verbose:
	@echo "📝 Running verbose database sanity tests..."
	@./tests/db_tests/run_sanity_tests.sh --verbose

sanity-coverage:
	@echo "📊 Running database sanity tests with coverage..."
	@./tests/db_tests/run_sanity_tests.sh --coverage

# Code Quality
lint:
	@echo "🔍 Running code linting..."
	python -m flake8 core/ tests/
	@echo "✅ Linting complete!"

format:
	@echo "🎨 Formatting code..."
	python -m black core/ tests/
	python -m isort core/ tests/
	@echo "✅ Code formatted!"

# Cleanup
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -f tests/db_tests/test_db_*.sqlite
	@echo "✅ Cleanup complete!"

# Pre-commit validation (recommended for developers)
pre-commit: sanity-quick lint
	@echo "✅ Pre-commit validation passed!"
	@echo "🚀 Ready to commit database changes!"

# CI/CD target
ci-db-validation: sanity-quick
	@echo "✅ CI/CD database validation passed!"

# Development workflow targets
dev-setup: install
	@echo "🛠️ Development environment setup complete!"
	@echo "💡 Next steps:"
	@echo "   1. Make your database changes"
	@echo "   2. Run 'make test-sanity' to validate"
	@echo "   3. Run 'make pre-commit' before committing"

# Database change workflow
db-change-workflow:
	@echo "🔄 Database Change Workflow Guide"
	@echo "================================="
	@echo ""
	@echo "1️⃣ Before making changes:"
	@echo "   make test-sanity  # Ensure baseline is clean"
	@echo ""
	@echo "2️⃣ During development:"
	@echo "   make sanity-quick # Quick validation after changes"
	@echo ""
	@echo "3️⃣ Before committing:"
	@echo "   make pre-commit   # Full validation + linting"
	@echo ""
	@echo "4️⃣ CI/CD validation:"
	@echo "   make ci-db-validation  # Automated pipeline check"
	@echo ""
	@echo "⚠️  CRITICAL: All sanity tests MUST pass before production!"
