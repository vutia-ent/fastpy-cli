---
layout: home

hero:
  name: Fastpy CLI
  text: Production-Ready FastAPI Projects
  tagline: Create, configure, and generate resources with one command
  image:
    src: /logo.svg
    alt: Fastpy CLI
  actions:
    - theme: brand
      text: Get Started
      link: /guide/quick-start
    - theme: alt
      text: View on GitHub
      link: https://github.com/vutia-ent/fastpy-cli

features:
  - icon: ⚡
    title: One-Command Setup
    details: Create a complete FastAPI project with venv, dependencies, and configuration in seconds.
  - icon: 🤖
    title: AI-Powered Generation
    details: Generate models, controllers, and routes using natural language with Claude, GPT, or Ollama.
  - icon: 📦
    title: Laravel-Style Libs
    details: Clean, expressive APIs for HTTP, Mail, Cache, Storage, Queue, Events, and more.
  - icon: 🔧
    title: Smart Detection
    details: Seamlessly works inside Fastpy projects, proxying commands to your project's CLI.
---

## Quick Install

```bash
pip install fastpy-cli
```

## Create Your First Project

```bash
# Create with automatic setup
fastpy new my-api --install

# Or step by step
fastpy new my-api
cd my-api
fastpy install
```

## What's Included

- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL databases with Python types
- **JWT Auth** - Secure authentication
- **MVC Architecture** - Clean code structure
- **Multi-DB Support** - PostgreSQL, MySQL, SQLite
- **Alembic** - Database migrations
