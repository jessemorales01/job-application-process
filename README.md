# Job Process Tracker

A full-stack web application for managing your job application process, from initial applications through job offers and assessments. Built with Django REST Framework and Vue 3.

## Overview

Job Process Tracker helps you organize and track your job search process. Manage applications through a Kanban board, track job offers, record assessments and take-home projects, and log interactions with recruiters—all in one place.

## Features

### Core Functionality

- **Job Applications Management**
  - Kanban board with customizable pipeline stages
  - Drag-and-drop to move applications between stages
  - Auto-assignment to the first stage when creating new applications
  - Track company name, position, tech stack, and salary range

- **Job Offers**
  - Track job offers linked to applications
  - Auto-populate company details from the associated application
  - Record offer dates, response deadlines, status, and compensation details
  - Store the actual salary/compensation offered

- **Assessments & Activities**
  - Unified Activities view combining Assessments and Interactions
  - Track take-home projects and assessments with deadlines
  - Store recruiter contact information for submissions
  - Filter activities by job application
  - Sort by date (most recent first)

- **Interactions**
  - Log interactions with companies (emails, phone calls, meetings, interviews)
  - Track interaction type, direction (inbound/outbound), and notes
  - Link interactions to specific applications

### Technical Features

- **User Authentication**: JWT-based authentication with user registration
- **User Scoping**: Users can only see their own data (staff can see all)
- **RESTful API**: Clean Django REST Framework API
- **Responsive UI**: Modern Vue 3 + Vuetify interface
- **Test Coverage**: Comprehensive backend tests (50+ tests) and frontend component tests

## Tech Stack

### Backend
- **Django 5.2.8** - Web framework
- **Django REST Framework** - API framework
- **SQLite** - Database (default, easily switchable to PostgreSQL)
- **JWT Authentication** - Secure token-based auth

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **Vuetify 3** - Material Design component framework
- **Vue Router** - Client-side routing
- **Axios** - HTTP client for API calls
- **Vitest** - Fast unit test framework

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- pip (Python package manager)
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jessemorales01/job-application-process.git
   cd job-application-process
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt

   # Run database migrations
   python manage.py migrate

   # Create a superuser (optional, for admin access)
   python manage.py createsuperuser

   # Start the development server
   python manage.py runserver
   ```
   The backend will run on `http://127.0.0.1:8000`

3. **Frontend Setup**
   ```bash
   cd frontend

   # Install Node.js dependencies
   npm install

   # Start the development server
   npm run dev
   ```
   The frontend will run on `http://localhost:5173`

### First Steps

1. Open `http://localhost:5173` in your browser
2. Create an account through the signup page
3. Log in with your credentials
4. Start by creating your first job application!

## Project Structure

```
job-application-process/
├── crm/                    # Django app (backend)
│   ├── models.py          # Database models (Application, JobOffer, Assessment, Interaction, Stage)
│   ├── views.py            # API ViewSets
│   ├── serializers.py      # DRF serializers
│   ├── urls.py             # API routes
│   ├── admin.py            # Django admin configuration
│   ├── tests.py            # Backend tests
│   └── migrations/         # Database migrations
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── views/          # Page components (Applications, JobOffers, Activities, Dashboard)
│   │   ├── components/     # Reusable components (Layout)
│   │   ├── router/         # Vue Router configuration
│   │   └── services/       # API service layer
│   └── package.json
├── crm_project/            # Django project settings
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## API Endpoints

All API endpoints are prefixed with `/api/` and require authentication (JWT token).

- `POST /api/register/` - User registration
- `POST /api/token/` - Get JWT token (login)
- `GET /api/applications/` - List applications
- `POST /api/applications/` - Create application
- `GET /api/job-offers/` - List job offers
- `POST /api/job-offers/` - Create job offer
- `GET /api/assessments/` - List assessments
- `POST /api/assessments/` - Create assessment
- `GET /api/interactions/` - List interactions
- `POST /api/interactions/` - Create interaction
- `GET /api/stages/` - List pipeline stages
- `POST /api/stages/` - Create stage

## Testing

### Backend Tests
```bash
# Run all backend tests
python manage.py test crm

# Run specific test class
python manage.py test crm.tests.ApplicationAPITests

# Run with verbose output
python manage.py test crm -v 2
```

### Frontend Tests
```bash
cd frontend
npm test

# Run specific test file
npm test -- Activities.test.js
```

## Development

### Database Migrations

When you modify models, create and apply migrations:

```bash
# Create migration
python manage.py makemigrations crm

# Apply migrations
python manage.py migrate
```

### Code Style

- **Backend**: Follow PEP 8 Python style guide
- **Frontend**: Follow Vue.js style guide and ESLint rules

## Key Models

- **Application**: Job applications with company, position, stack, salary range, and stage
- **JobOffer**: Job offers linked to applications with offer details and deadlines
- **Assessment**: Take-home projects and assessments with deadlines and recruiter contact info
- **Interaction**: Logged interactions (emails, calls, meetings) with companies
- **Stage**: Pipeline stages for organizing applications in the Kanban board

## License

This project is private and proprietary.

## Support

For questions or issues, please contact the repository maintainer.
