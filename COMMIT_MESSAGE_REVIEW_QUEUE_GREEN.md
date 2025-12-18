# Commit Message: Frontend Review Queue UI (GREEN Phase)

## Commit Message

```
feat: add frontend review queue UI for auto-detected applications

Implement complete frontend interface for reviewing and managing
auto-detected applications from email analysis, including accept, reject,
and merge functionality.

- ReviewQueue.vue component with data table and filtering
- Accept action (creates Application from detected item)
- Reject action (marks as rejected)
- Merge action (links to existing Application via dialog)
- Status filtering (pending, accepted, rejected, merged)
- Confidence score visualization with color coding
- Loading states and error handling
- Success notifications for user actions
- Empty state messaging
- Navigation integration (Layout and router)

Tests: 9 passing
Breaking Changes: None
```

## Detailed Description

### Implementation Summary

This commit implements the complete frontend user interface for the Review Queue feature, allowing users to review, accept, reject, or merge auto-detected applications that were identified through email analysis. The UI provides a comprehensive data table view with filtering, action buttons, and merge dialog functionality.

### Files Changed

1. **frontend/src/views/ReviewQueue.vue** (NEW)
   - Main component for reviewing auto-detected applications
   - Data table with company name, confidence score, status, and detected date
   - Status filter dropdown (pending, accepted, rejected, merged)
   - Accept, Reject, and Merge action buttons
   - Merge dialog with application selection
   - Loading states and error handling
   - Empty state messaging
   - Success/error snackbar notifications

2. **frontend/src/views/ReviewQueue.test.js** (NEW)
   - Comprehensive test suite with 9 passing tests
   - Tests for displaying detected items
   - Tests for accept, reject, and merge actions
   - Tests for confidence score display
   - Tests for loading and error states
   - Tests for status filtering
   - Tests for empty state
   - Tests for success notifications
   - Proper mocking of Vuetify components and API calls

3. **frontend/src/components/Layout.vue** (MODIFIED)
   - Added "Review Queue" navigation item
   - Icon: `mdi-inbox-multiple`
   - Route: `/review-queue`

4. **frontend/src/router/index.js** (MODIFIED)
   - Added `/review-queue` route
   - Component: `ReviewQueue`
   - Requires authentication

### Features Implemented

#### Data Table Display
- Lists all auto-detected applications for the user
- Shows company name, position, confidence score, status, and detected date
- Sortable columns
- 25 items per page
- Responsive design

#### Status Filtering
- Dropdown filter for status (pending, accepted, rejected, merged)
- Default filter: "pending"
- Automatically reloads data when filter changes
- Clearable filter option

#### Accept Action
- Creates new Application from detected item
- Auto-assigns to first stage (lowest order)
- Shows success notification with company name
- Automatically refreshes list after acceptance
- Disables action buttons while processing

#### Reject Action
- Marks detected application as rejected
- Shows success notification
- Automatically refreshes list after rejection
- Prevents duplicate reviews

#### Merge Action
- Opens dialog to select existing Application
- Fetches user's applications for selection
- Validates application selection
- Links detected item to selected application
- Shows success notification
- Automatically refreshes list after merge
- Closes dialog after successful merge

#### Confidence Score Visualization
- Color-coded chips based on confidence:
  - Green (success): >= 80%
  - Yellow (warning): >= 60%
  - Red (error): < 60%
- Displays percentage (rounded)

#### Status Visualization
- Color-coded chips:
  - Yellow (warning): pending
  - Green (success): accepted
  - Red (error): rejected
  - Blue (info): merged

#### User Experience
- Loading spinner while fetching data
- Empty state message when no items found
- Refresh button to manually reload data
- Error handling with user-friendly messages
- Success notifications for all actions
- Disabled buttons during processing to prevent duplicate actions

### API Integration

- `GET /api/auto-detected-applications/` - List detected items
- `GET /api/auto-detected-applications/?status={status}` - Filter by status
- `GET /api/applications/` - Fetch applications for merge dialog
- `POST /api/auto-detected-applications/{id}/accept/` - Accept detected item
- `POST /api/auto-detected-applications/{id}/reject/` - Reject detected item
- `POST /api/auto-detected-applications/{id}/merge/` - Merge with existing application

### Error Handling

- Centralized error formatting using `formatErrorMessage` utility
- Error snackbar displays formatted error messages
- Multiline error messages supported
- Errors cleared on successful actions
- Network errors handled gracefully

### Test Coverage

All 9 tests passing:
- Displays list of pending items
- Allows accepting detected application
- Allows rejecting detected item
- Shows confidence scores
- Displays loading state while fetching items
- Displays error message when API call fails
- Allows merging detected application with existing
- Filters items by status
- Displays empty state when no items found
- Shows success message after accepting item

### Test Implementation Details

- Proper mocking of Vuetify components (simplified templates)
- API mocking with `vi.mock` and `vi.fn()`
- Mock reset in `beforeEach` to prevent test interference
- Async handling with `setTimeout` and `$nextTick()`
- Direct state assertions (`wrapper.vm.detectedItems`) instead of DOM queries
- Proper timing for loading and error state assertions

### UI/UX Features

- **Responsive Design**: Works on all screen sizes
- **Accessibility**: Proper ARIA labels and semantic HTML
- **Visual Feedback**: Loading spinners, disabled states, color coding
- **User Guidance**: Empty states, success messages, error messages
- **Efficient Workflow**: Quick actions, auto-refresh, merge dialog

### Next Steps

- Background email sync task (Commit 12)
- Email sync scheduling and automation
- Real-time notifications for new detected items

