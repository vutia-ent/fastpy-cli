# AI-Powered Generation

Generate models, controllers, routes, and entire resource systems using natural language.

## Basic Usage

```bash
# Generate from description
fastpy ai "Create a blog with posts, categories, and tags"

# Auto-execute commands
fastpy ai "E-commerce with products, orders, and customers" --execute

# Preview without executing
fastpy ai "User management system" --dry-run
```

## Providers

### Anthropic Claude (Default)

The default provider uses Claude for code generation.

```bash
# Set API key
export ANTHROPIC_API_KEY=your-key
# or
fastpy ai:config -k your-key

# Generate
fastpy ai "Create a user authentication system"
```

Get your key at [console.anthropic.com](https://console.anthropic.com)

### OpenAI GPT

```bash
export OPENAI_API_KEY=your-key
fastpy ai "Create a REST API for tasks" --provider openai
```

Get your key at [platform.openai.com](https://platform.openai.com/api-keys)

### Google Gemini

```bash
export GOOGLE_API_KEY=your-key
fastpy ai "Create a blog system" --provider google
```

Get your key at [aistudio.google.com](https://aistudio.google.com/apikey)

### Groq Cloud

```bash
export GROQ_API_KEY=your-key
fastpy ai "Create an inventory system" --provider groq
```

Get your key at [console.groq.com](https://console.groq.com/keys)

### Ollama (Local)

Run AI locally without API keys.

```bash
# Install Ollama from https://ollama.ai
# Start the server
ollama serve

# Generate
fastpy ai "Create a blog system" --provider ollama
```

## Configuration

### Set Default Provider

```bash
fastpy ai:config -p anthropic
```

### Set API Key

API keys are saved to your project's `.env` file:

```bash
fastpy ai:config -k YOUR_API_KEY
```

### Test Connection

```bash
fastpy ai:config --test
```

### View Status

```bash
fastpy ai:config
```

## Examples

### Blog System

```bash
fastpy ai "Create a blog with:
- Posts (title, content, slug, published_at)
- Categories (name, slug)
- Tags (name, slug)
- Post can have many tags
- Post belongs to one category"
```

### E-Commerce

```bash
fastpy ai "Create an e-commerce system with:
- Products (name, price, stock, description)
- Categories
- Orders (status, total)
- Order items
- Customers" --execute
```

### Task Management

```bash
fastpy ai "Create a task management API with:
- Projects (name, description, status)
- Tasks (title, description, priority, due_date)
- Task belongs to project
- Task can be assigned to user" --execute
```

### User Management

```bash
fastpy ai "Create user management with:
- Users (name, email, role)
- Roles (name, permissions)
- User profiles
- Password reset tokens"
```

## Workflow

1. **Generate** - AI creates commands based on your description
2. **Review** - See the generated commands before execution
3. **Execute** - Run commands manually or with `--execute`
4. **Migrate** - After generation, run `fastpy db:migrate`
5. **Test** - Start server with `fastpy serve`

## Tips

- Be specific about field types and relationships
- Use `--dry-run` to preview before executing
- Generated code follows Fastpy conventions
- Always review generated commands before executing
- Run migrations after generating models
