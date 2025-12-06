# Quick Start

This guide will get you from zero to a running FastAPI application in under a minute.

## One-Command Setup

The fastest way to get started:

```bash
# Create project with automatic setup
fastpy new my-api --install
```

This will:
1. Clone the Fastpy template
2. Create a virtual environment
3. Install all dependencies
4. Display next steps

Then:

```bash
cd my-api
source venv/bin/activate  # or venv\Scripts\activate on Windows
fastpy setup              # Configure database, secrets, etc.
fastpy serve              # Start development server
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) to see your API documentation.

## Step-by-Step Setup

If you prefer more control:

### 1. Create a Project

```bash
fastpy new my-api
cd my-api
```

### 2. Install Dependencies

```bash
fastpy install
```

This creates a virtual environment, upgrades pip, installs requirements, and runs the interactive setup wizard.

### 3. Activate Environment

::: code-group
```bash [macOS/Linux]
source venv/bin/activate
```

```cmd [Windows CMD]
venv\Scripts\activate
```

```powershell [Windows PowerShell]
venv\Scripts\Activate.ps1
```
:::

### 4. Start the Server

```bash
fastpy serve
```

## Project Structure

After setup, your project looks like this:

```
my-api/
├── app/
│   ├── controllers/     # Request handlers
│   ├── models/          # SQLModel models
│   ├── services/        # Business logic
│   ├── routes/          # API routes
│   └── config.py        # Configuration
├── alembic/             # Database migrations
├── tests/               # Test files
├── .env                 # Environment variables
├── cli.py               # Project CLI
├── main.py              # Application entry
└── requirements.txt     # Dependencies
```

## Generate Resources

Create a complete CRUD resource with AI:

```bash
fastpy ai "Create a blog with posts, categories, and tags" --execute
```

Or use the make commands:

```bash
# Generate model, controller, service, and routes
fastpy make:resource Post -m

# Run migrations
fastpy db:migrate
```

## Next Steps

- [Commands Reference](/guide/commands) - All available commands
- [AI Generation](/guide/ai) - Generate code with AI
- [Libs](/guide/libs) - Laravel-style facades
- [Configuration](/guide/configuration) - Customize settings
