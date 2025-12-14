# CRM App - Technical Assessment

You've joined a team building a CRM system for managing leads and customer deals. The basic application exists, but your product manager has identified several opportunities to make it more valuable for enrollment teams.

Your task: **Extend this application in ways that demonstrate your strongest technical skills.**

This is intentionally vague and open-ended. Pick the direction that best showcases your abilities.

## What's Already Built

A functional full-stack application with:

- **Backend**: Django REST Framework with JWT authentication
- **Frontend**: Vue 3 with Vuetify
- **Core Features**: Basic CRUD operations for customers (institutions), contacts (prospects), interactions, and leads
- **Data Model**: Simple relationships between entities
- **Authentication**: User registration and login

The application works, but enrollment teams need more sophisticated features to be effective. Think of this as an MVP you're building upon.

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+

### Setup

**Backend:**

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server (runs on http://127.0.0.1:8000)
python manage.py runserver
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

Create an account through the UI or use Django admin after creating a superuser with `python manage.py createsuperuser`.

## Project Requirements

We want you to implement a Kanban board for managing the deals at different stages

- You should be able to add or remove pipeline stages
- You should be able to move the deals between stages in the UI
- The initial stage of the deal is based on dollar amount

**Required:**

1. Document your changes in a `SOLUTION.md` file:

   - What you built and why
   - Technical decisions and tradeoffs
   - How to test your features
   - Any new dependencies or setup steps (or add to the instructions above)

2. Ensure your code is clean, well-organized, and demonstrates your best practices

**Bonus Points:**

- If you implemented ML/AI features, explain your approach and model choices
- Thoughtful commit history

We're excited to see what you build!

## Submission Instructions

1. **Request Repository Access:**

   - Email us at [lucas@smartpandatools.com] to request access to the private repository
   - We'll add you as a collaborator so you can clone the project

2. **Create Your Private Fork:**

   - Create a new **private** repository in your GitHub account (e.g., `your-username/repo-name`)
   - Clone our repository locally
   - Push the code to your private repository

3. **Build Your Solution:**

   - Work on your implementation in your private repository
   - Commit regularly with clear, descriptive commit messages

4. **Submit Your Work:**
   - Add **`iwalucas`, `mikinty`** as collaborators to your private repository (Settings → Collaborators)
   - Email us at `lucas@smartpandatools.com`, `michael@smartpandatools.com` with:
     - Link to your private repository
     - Any special instructions for running your solution
   - Ensure your `SOLUTION.md` is complete and included in the repository

**Timeline:** Please submit by Dec 9th

**Questions?** Feel free to reach out at `lucas@smartpandatools.com` or `michael@smartpandatools.com` if you encounter any setup issues.
