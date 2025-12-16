# TDD (Test-Driven Development) Guide

## Current Status ✅
- **32 tests passing** - Good coverage for Applications, JobOffers, Stages, Interactions
- **Code is working** - No need to revert commits
- **Gaps identified**: Contact CRUD tests, User registration tests

## TDD Workflow Going Forward

### 1. **Red-Green-Refactor Cycle**

```
┌─────────┐
│   RED   │  Write a failing test
└────┬────┘
     │
     ▼
┌─────────┐
│  GREEN  │  Write minimal code to pass
└────┬────┘
     │
     ▼
┌──────────┐
│ REFACTOR │  Improve code, keep tests green
└──────────┘
```

### 2. **When to Write Tests**

#### ✅ **BEFORE** (TDD):
- Adding new features
- Fixing bugs (write test that reproduces bug first)
- Refactoring (write tests to preserve behavior)

#### ❌ **AFTER** (Not TDD, but acceptable):
- Legacy code without tests (add tests incrementally)
- Emergency hotfixes (add test immediately after)

### 3. **Commit Strategy**

#### **Option A: TDD Commits (Ideal)**
```bash
# 1. Write failing test
git commit -m "test: add test for feature X (failing)"

# 2. Implement feature
git commit -m "feat: implement feature X"

# 3. Refactor if needed
git commit -m "refactor: improve feature X"
```

#### **Option B: Feature Commits (Current - Acceptable)**
```bash
# Single commit with test + implementation
git commit -m "feat: add feature X with tests"
```

### 4. **Test Coverage Goals**

- **Critical paths**: 100% coverage (API endpoints, business logic)
- **Models**: Test relationships, validations, methods
- **Serializers**: Test validation, transformations
- **Views**: Test permissions, filtering, CRUD operations

### 5. **Best Practices**

1. **Test one thing per test** - Each test should verify one behavior
2. **Use descriptive names** - `test_cannot_delete_stage_with_applications` not `test_delete`
3. **Arrange-Act-Assert** - Setup, execute, verify
4. **Test edge cases** - Empty states, invalid inputs, boundary conditions
5. **Keep tests fast** - Use `TestCase` for DB, `APITestCase` for API
6. **Test user isolation** - Verify users only see their own data

## Current Test Gaps

### Missing Tests:
- [ ] Contact CRUD operations
- [ ] User registration endpoint
- [ ] Staff vs non-staff permissions for all viewsets
- [ ] Contact-Interaction relationships

## Example: Adding a New Feature with TDD

```python
# Step 1: RED - Write failing test
def test_application_can_have_tags(self):
    """Test that applications can have multiple tags"""
    app = Application.objects.create(company_name="Test")
    app.tags.add("python", "remote")
    self.assertEqual(app.tags.count(), 2)
    # ❌ This will fail - tags field doesn't exist yet

# Step 2: GREEN - Minimal implementation
class Application(models.Model):
    # ... existing fields ...
    tags = models.ManyToManyField('Tag', blank=True)

# Step 3: REFACTOR - Improve if needed
# Add validation, optimize queries, etc.
```

## Resources

- [Django Testing Docs](https://docs.djangoproject.com/en/stable/topics/testing/)
- [DRF Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [Test-Driven Development by Example (Kent Beck)](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)

