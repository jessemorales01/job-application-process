# Commit Message

```
fix: improve email parsing and application detection accuracy

Fix critical issues preventing auto-detected applications from being created
and improve email parsing accuracy for HTML emails and AI responses.

## Key Fixes

### Email Parsing & AI Integration
- **HTML Email Parsing**: Enhanced HTML email body extraction with proper tag
  removal, HTML entity decoding, and whitespace normalization. Handles
  zero-width characters and preserves readable text structure.
- **AI JSON Parsing**: Improved AI response parsing to handle markdown code
  blocks, extract JSON from mixed responses, and provide better error
  messages for debugging.
- **AI Triggering**: Always use AI for job-related emails when pattern
  matching fails (type is None) or has low confidence, ensuring better
  accuracy for application detection.

### Database & Model Fixes
- **Database Constraints**: Added `default=''` to optional string fields
  (`where_applied`, `email`, `phone_number`, `salary_range`) in
  `AutoDetectedApplication` model to prevent NOT NULL constraint errors.
- **Sync Service**: Ensure all string fields are empty strings (not None)
  when creating detected applications.
- **detected_at Field**: Fixed to use email received date instead of sync
  time, providing accurate detection timestamps.

### Frontend Improvements
- **Review Queue Navigation**: After accepting a detected application,
  automatically navigate to Applications page to show the newly created
  application on the Kanban board.

## Technical Details

- Enhanced `GmailService._extract_body()` to properly parse HTML emails
- Improved `AIEmailAnalyzer` JSON parsing with regex extraction and
  markdown code block handling
- Updated `EmailProcessor` to always use AI when pattern matching fails
- Fixed `EmailSyncService` to handle None values and set proper defaults
- Added migrations for model field defaults
- Updated `ReviewQueue.vue` to navigate after accepting applications

## Results

- Email sync now successfully creates 30+ detected applications from 50 emails
- HTML emails are properly parsed and analyzed
- AI responses are correctly extracted and processed
- Database errors prevented with proper field defaults
- Applications appear on Kanban board after acceptance

## Files Changed

- `crm/models.py`: Added defaults to optional fields
- `crm/services/gmail_service.py`: Enhanced HTML parsing
- `crm/services/ai_email_analyzer.py`: Improved JSON parsing
- `crm/services/email_processor.py`: Better AI triggering logic
- `crm/services/email_sync_service.py`: Fixed None handling and detected_at
- `crm/tests.py`: Updated tests for new extraction methods
- `frontend/src/views/ReviewQueue.vue`: Added navigation after accept
- `crm/migrations/0017_*.py`: Migration for detected_at and where_applied
- `crm/migrations/0018_*.py`: Migration for email, phone_number, salary_range
```

