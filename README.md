# AI Code Review Agent

An autonomous code review system that leverages Google's Gemini AI to analyze GitHub pull requests. The system processes reviews asynchronously using Celery and provides a structured API for developer interactions.

## Project Structure
```
code-review-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py        # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pr_analysis.py      # AI agent interaction and analysis logic
│   │   ├── task_status.py      # Task status management
│   │   ├── github_integration.py  # Code fetching and diff handling
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request_models.py   # Pydantic models for request/response
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── analyze.py          # Celery task definition
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Configurations (DB, Celery, etc.)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py           # Database models
│   │   ├── crud.py             # Database operations
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Structured logging
│       ├── cache.py            # Caching utilities
├── tests/
│   ├── __init__.py
│   ├── test_endpoints.py       # API endpoint tests
│   ├── test_tasks.py           # Task functionality tests
│   ├── test_integration.py     # Integration tests
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Multi-service setup
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
├── .env               # Environment variable 
└── .gitignore                  # Ignored files
```

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- PostgreSQL 13
- Redis
- GitHub account and access token
- Google Cloud account (for Gemini AI API)

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/code-review-agent.git
cd code-review-agent
```

2. Create environment file:
```bash
cp .env.example .env
```

Edit the `.env` file with your configurations:
- Set your GitHub access token
- Configure your Google Cloud credentials for Gemini AI
- Adjust database and Redis settings if needed

3. Start the services using Docker Compose:
```bash
docker-compose up -d
```

This will start:
- FastAPI application (accessible at http://localhost:8000)
- Celery worker for async tasks
- Redis for message broker
- PostgreSQL database

## API Endpoints

Access the interactive API documentation at `http://localhost:8000/docs`

## Task Processing

The system uses Celery for asynchronous task processing. The main workflow is defined in `app/tasks/analyze.py`:

1. Task submission triggers `full_review_workflow_task`
2. GitHub service fetches PR details
3. Code review agent analyzes changes using Gemini AI
4. Results are cached and stored in database
5. Task status can be monitored via API

## Docker Services

The `docker-compose.yml` file defines four services:

- `web`: FastAPI application
- `celery_worker`: Celery task processor
- `redis`: Message broker and caching
- `db`: PostgreSQL database

## Caching

Redis is used for:
- Celery message broker
- Task result caching
- General application caching

## Error Handling

The system implements retry logic for tasks:
- Maximum 3 retries
- 60-second delay between retries

## Environment Variables

Key variables in `.env`:

```
APP_ENV=development
APP_SECRET_KEY=
DATABASE_URL=postgresql://postgres:postgres@db:5432/code_review
GITHUB_TOKEN=
GEMINI_API_KEY=
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
REDIS_CLIENT_URL=redis://redis:6379/0
```

