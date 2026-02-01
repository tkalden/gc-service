# Test Suite Recommendations

This document outlines recommended testing frameworks and strategies for both the React Native frontend and Python/FastAPI backend.

## Overview

We recommend a comprehensive testing strategy covering:
1. **Unit Tests** - Test individual functions/components in isolation
2. **Integration Tests** - Test API endpoints and service interactions
3. **End-to-End Tests** - Test complete user flows
4. **Performance Tests** - Test API response times and load handling

## React Native Frontend Testing

### Recommended Testing Stack

#### 1. **Jest** (Unit & Integration Testing)
- **Why**: Industry standard for React Native, built-in with Expo
- **What it tests**: Components, hooks, utilities, services
- **Installation**: Already included in Expo projects

#### 2. **React Native Testing Library** (Component Testing)
- **Why**: Best practices for testing React components, focuses on user behavior
- **What it tests**: Component rendering, user interactions, accessibility
- **Installation**: `npm install --save-dev @testing-library/react-native @testing-library/jest-native`

#### 3. **Detox** (E2E Testing)
- **Why**: Reliable E2E testing for React Native, supports both iOS and Android
- **What it tests**: Complete user flows, navigation, API integration
- **Installation**: `npm install --save-dev detox`

#### 4. **MSW (Mock Service Worker)** (API Mocking)
- **Why**: Intercept network requests, test API integration without backend
- **What it tests**: API service calls, error handling, response parsing
- **Installation**: `npm install --save-dev msw`

### Test Structure

```
gc-ui/
├── __tests__/
│   ├── components/
│   │   ├── ClothingItemCard.test.tsx
│   │   ├── CommonHeader.test.tsx
│   │   ├── OutfitCard.test.tsx
│   │   └── ...
│   ├── screens/
│   │   ├── HomeScreen.test.tsx
│   │   ├── LoginScreen.test.tsx
│   │   ├── AddClothesScreen.test.tsx
│   │   └── ...
│   ├── services/
│   │   ├── authService.test.ts
│   │   ├── clothingService.test.ts
│   │   ├── outfitService.test.ts
│   │   └── ...
│   ├── hooks/
│   │   ├── useAuth.test.ts
│   │   ├── useGlobalData.test.ts
│   │   └── ...
│   ├── utils/
│   │   ├── clothingStorage.test.ts
│   │   ├── seasonDetection.test.ts
│   │   └── ...
│   └── integration/
│       ├── auth-flow.test.ts
│       ├── clothing-upload-flow.test.ts
│       ├── outfit-creation-flow.test.ts
│       └── ...
├── e2e/
│   ├── auth.e2e.ts
│   ├── clothing-management.e2e.ts
│   ├── outfit-management.e2e.ts
│   ├── virtual-tryon.e2e.ts
│   └── ...
└── jest.config.js
```

### Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All critical user flows
- **E2E Tests**: All major user journeys

## Python/FastAPI Backend Testing

### Recommended Testing Stack

#### 1. **pytest** (Primary Testing Framework)
- **Why**: Most popular Python testing framework, excellent fixtures, plugins
- **What it tests**: All backend code (routes, services, utilities)
- **Installation**: `pip install pytest pytest-asyncio pytest-cov`

#### 2. **pytest-asyncio** (Async Testing)
- **Why**: Required for testing async FastAPI endpoints
- **What it tests**: Async functions, database operations, API endpoints
- **Installation**: `pip install pytest-asyncio`

#### 3. **httpx** (API Testing)
- **Why**: Async HTTP client, perfect for testing FastAPI
- **What it tests**: API endpoints, request/response validation
- **Installation**: `pip install httpx`

#### 4. **pytest-mock** (Mocking)
- **Why**: Easy mocking for external dependencies
- **What it tests**: Services with mocked dependencies (Supabase, AI models)
- **Installation**: `pip install pytest-mock`

#### 5. **pytest-cov** (Coverage)
- **Why**: Measure test coverage
- **What it tests**: Coverage reporting
- **Installation**: `pip install pytest-cov`

#### 6. **faker** (Test Data Generation)
- **Why**: Generate realistic test data
- **What it tests**: Test data creation
- **Installation**: `pip install faker`

### Test Structure

```
gc-service/
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_database_service.py
│   │   │   ├── test_storage_service.py
│   │   │   ├── test_background_removal.py
│   │   │   ├── test_clothing_classifier.py
│   │   │   └── ...
│   │   ├── utils/
│   │   │   └── test_utils.py
│   │   └── models/
│   │       └── test_models.py
│   ├── integration/
│   │   ├── api/
│   │   │   ├── test_auth_endpoints.py
│   │   │   ├── test_clothes_endpoints.py
│   │   │   ├── test_outfits_endpoints.py
│   │   │   ├── test_avatar_endpoints.py
│   │   │   ├── test_upload_endpoints.py
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── test_auth_integration.py
│   │   │   ├── test_clothing_workflow.py
│   │   │   ├── test_outfit_workflow.py
│   │   │   └── ...
│   │   └── database/
│   │       └── test_database_operations.py
│   ├── fixtures/
│   │   ├── conftest.py
│   │   ├── test_users.py
│   │   ├── test_clothing_items.py
│   │   └── test_outfits.py
│   └── e2e/
│       ├── test_auth_flow.py
│       ├── test_clothing_management_flow.py
│       ├── test_outfit_management_flow.py
│       ├── test_virtual_tryon_flow.py
│       └── ...
├── pytest.ini
└── requirements-test.txt
```

## Test Coverage by Feature

### Authentication Features
- [ ] User registration (success, validation errors, duplicate email)
- [ ] User login (success, invalid credentials, expired token)
- [ ] User logout (token invalidation)
- [ ] Password reset (email sending, token validation)
- [ ] Token refresh (valid refresh, expired refresh)
- [ ] Get current user (authenticated, unauthenticated)

### Clothing Item Management
- [ ] Create clothing item (success, validation errors, image upload)
- [ ] Get all clothing items (empty, with items, pagination)
- [ ] Get item by ID (exists, not found, unauthorized)
- [ ] Get items by category (valid category, invalid category, empty)
- [ ] Get items by season (valid season, multiple seasons)
- [ ] Update clothing item (success, not found, validation)
- [ ] Delete clothing item (success, not found, cascade delete)

### Avatar & Virtual Try-On
- [ ] Upload avatar (success, invalid image, pose detection)
- [ ] Get user avatar (exists, not found)
- [ ] Get avatar by ID (exists, not found, unauthorized)
- [ ] Virtual try-on (success, missing avatar, missing clothing)
- [ ] Get try-on history (empty, with results, pagination)
- [ ] Avatar service status (available, unavailable)

### Outfit Management
- [ ] Create outfit from items (success, invalid items, validation)
- [ ] Create outfit with images (success, multiple images, validation)
- [ ] Get user outfits (empty, with outfits, pagination)
- [ ] Filter outfits (by season, occasion, date, rating, tags)
- [ ] Get outfit details (with items, not found)
- [ ] Update outfit (success, not found, validation)
- [ ] Delete outfit (success, not found, cascade delete)

### Image Processing & AI
- [ ] Background removal (success, failure, service unavailable)
- [ ] Clothing classification (success, low confidence, failure)
- [ ] Enhanced classification (category + season, failure)
- [ ] Title generation (single, multiple options)
- [ ] Smart upload async (parallel processing, partial failure)

### Search & Discovery
- [ ] Search clothing items (by name, by category, no results)
- [ ] Filter by season (valid season, all items)
- [ ] Filter by category (valid category, empty)

### Image Management
- [ ] Unified image upload (success, invalid file, wrong bucket)
- [ ] Image serving (signed URLs, expired URLs)

## Test Configuration Files

### React Native (Jest Config)
```javascript
// jest.config.js
module.exports = {
  preset: 'jest-expo',
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-ng/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg)'
  ],
  setupFilesAfterEnv: ['@testing-library/jest-native/extend-expect'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/__tests__/**',
    '!src/**/__mocks__/**',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
};
```

### Python (pytest.ini)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

## Running Tests

### Frontend (React Native)
```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- ClothingItemCard.test.tsx

# Run E2E tests
detox test
```

### Backend (Python)
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/services/test_auth_service.py

# Run by marker
pytest -m unit
pytest -m integration
pytest -m e2e

# Run with verbose output
pytest -v
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-test.txt
      - run: pytest

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm install
      - run: npm test -- --coverage
```

## Test Data Management

### Frontend
- Use MSW to mock API responses
- Create test fixtures for common data structures
- Use factories for generating test data

### Backend
- Use pytest fixtures for test data
- Create test database (separate from production)
- Use factories (faker) for generating test data
- Clean up test data after tests

## Performance Testing

### Backend
- Use `pytest-benchmark` for performance tests
- Test API response times
- Test concurrent request handling (1000+ users)
- Test database query performance

### Frontend
- Use React DevTools Profiler
- Test component render times
- Test image loading performance
- Test navigation performance

## Next Steps

1. **Review this document** with the team
2. **Install testing dependencies** for both projects
3. **Set up test infrastructure** (config files, fixtures)
4. **Write initial test suite** starting with critical features
5. **Set up CI/CD** with automated testing
6. **Monitor coverage** and aim for 70%+ coverage

## Questions to Consider

Before writing tests, please confirm:
1. Do you want to test against a real Supabase instance or use mocks?
2. Should AI model tests use real models or mocked responses?
3. What's the target test coverage percentage?
4. Should we include performance/load testing?
5. Do you want E2E tests for both iOS and Android?

