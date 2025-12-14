# SOLUTION

## Analysis
The assignment references "deals" for the Kanban board, but the original codebase does not include a separate Deal model. The existing Lead model already contains `estimated_value` (dollar amount) and represents potential sales opportunities. This makes it a great candidate for pipeline management. Using Leads as deals avoids creating redundant data models while satisfying the requirements.

## Features Implemented

**Core Requirements**
- Kanban board display with pipeline stages
- Add/remove stages dynamically
- Move leads between stages via drag-and-drop
- Auto-assign leads to stages based on estimated value (<$1K, $1K-$10K, ≥$10K)

**Bonus Features**
- Drag-and-drop with vuedraggable
- Inline stage name editing with validation
- Backend validation preventing stage deletion with leads
- Empty board state with user guidance
- Dropdown menus for stage/lead actions
- ML win probability prediction using Logistic Regression (cached for performance)
- Unit tests for auto-assign, ML predictions, stage deletion, lead movement, win_score caching, and lead validation (28 backend tests)
- Frontend component tests with Vitest and Vue Test Utils (5 tests)

## Dependencies Added

**Frontend**
- `vuedraggable@next` - Drag-and-drop for Vue 3 Kanban board

**Backend**
- `scikit-learn` - Logistic Regression for win probability
- `pandas`, `numpy` - Data manipulation for model training
- `joblib` - Model serialization

**Testing**
- `vitest` - Fast unit test framework for Vite
- `@vue/test-utils` - Vue component testing utilities
- `jsdom` - DOM environment for tests

**Design Philosophy**: Minimized external dependencies. Used native JavaScript instead of Lodash, browser confirm() instead of toast libraries, component state instead of Pinia.

## How to Run

```bash
# Backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver  # http://127.0.0.1:8000

# Frontend
cd frontend
npm install
npm run dev  # http://localhost:5173

# Tests
# Backend tests (28 tests)
python manage.py test crm

# Frontend tests (5 tests)
cd frontend
npm install 
npm test  # Runs Vitest test suite
```

## Technical Decisions

**Lead as Deal** - Used existing Lead model instead of creating a new Deal model. Lead already has `estimated_value`, `status`, and contact info. Avoids data duplication and unnecessary complexity.

**Nullable Stage ForeignKey** - Allows leads to exist without a stage. Handles migration of existing data before Stage model was added.

**Auto-assign in Serializer** - Stage assignment happens in `LeadSerializer.create()` rather than frontend or `Model.save()`. Ensures all API clients get auto-assignment, prevents reassignment on every edit, and centralizes validation.

**Position-based Auto-assign** - Uses first 3 existing stages with hardcoded thresholds rather than configurable per-stage values. Simpler implementation, predictable behavior, meets requirements without additional UI.

**Frontend Filtering with Caching** - `leadsByStage` computed property groups leads by stage and caches the result. Only recalculates when `this.leads` changes, avoiding unnecessary filtering on every render. Acceptable for current scale; would need backend pagination for large datasets.

**Local State Updates** - After drag operations, update `this.leads` locally instead of reloading from API. Prevents visual flash/flicker, with fallback reload on errors.

**vuedraggable** - External dependency for drag-and-drop. Worth the 30KB bundle cost for cross-browser support, animations, and edge case handling that would be complex to implement natively.

**ML Win Prediction** - Logistic Regression trained on synthetic data (1000 samples). Features: estimated_value, status, has_phone, has_company. Chose Logistic Regression for binary classification (win/lose) that outputs probabilities (0-1) via sigmoid function.

**Cached Win Score** - ML predictions stored in database field `win_score` instead of calculating on every serialization. Calculated once on lead creation, recalculated only when relevant fields change (estimated_value, status, phone, company). Irrelevant changes (name, notes, stage) skip recalculation. Reduces API response time from O(N) predictions to O(1) database reads.

**Stage Deletion Validation** - Backend prevents stage deletion if leads exist, returning 400 error with lead count. Users must move leads before deleting stage. Validation in backend ensures it can't be bypassed via direct API calls.

**select_related Optimization** - LeadViewSet uses `select_related('stage', 'created_by')` to fetch related data in a single query. Prevents N+1 query problem when serializing leads with stage_name and created_by_username fields.

**User-Facing Error Messages** - All API errors display specific backend validation messages instead of generic alerts. Handles Django REST Framework error formats: field errors, non-field errors, and custom error messages. Users see exactly what went wrong (e.g., "Cannot create lead: no stages exist" instead of "Failed to save lead").

## Issues Encountered & Solutions

| Issue | Solution |
|-------|----------|
| Empty columns not droppable | Added min-height to kanban-cards CSS |
| Stage name truncation hid icons | Applied CSS truncation to text span only, not header |
| Deleted stages broke auto-assign | Changed to use first N existing stages; backend now prevents deletion with leads |

## Future Improvements (Not Implemented)
- Configurable stage thresholds via UI
- JWT auto-refresh with axios interceptor
- Stage reordering via drag-and-drop
- Toast notifications instead of alert() for better UX (currently using alert with detailed error messages)
- Extract LeadCard as reusable Vue component
- Pagination for large datasets
