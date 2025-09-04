#!/bin/bash
set -e

# Docker entrypoint script for Erasmus Partner Agent
echo "🚀 Starting Erasmus Partner Agent..."

# Check if required environment variables are set
if [ -z "$LLM_API_KEY" ]; then
    echo "❌ Error: LLM_API_KEY environment variable is required"
    echo "Please set your OpenAI API key in the .env file"
    exit 1
fi

# Validate API key format (basic check)
if [[ ! "$LLM_API_KEY" =~ ^sk-[a-zA-Z0-9]{48}$ ]]; then
    echo "⚠️  Warning: LLM_API_KEY format looks invalid (should start with sk- and be 51 characters)"
fi

# Create necessary directories
mkdir -p /app/exports /app/logs

# Set permissions
chmod 755 /app/exports /app/logs

# Run health check to ensure dependencies are working
echo "🔍 Running startup health check..."
python -c "
try:
    from erasmus_partner_agent.settings import load_settings
    from erasmus_partner_agent.providers import get_llm_model
    
    # Test settings loading
    settings = load_settings()
    print('✅ Settings loaded successfully')
    
    # Test LLM model configuration
    model = get_llm_model()
    print('✅ LLM model configured successfully')
    
    print('🎉 Startup health check passed!')
except Exception as e:
    print(f'❌ Startup health check failed: {e}')
    exit(1)
"

# Check if this is a CLI command or server command
if [ "$1" = "cli" ]; then
    echo "🖥️  Starting CLI mode..."
    shift  # Remove 'cli' from arguments
    exec python -m erasmus_partner_agent.cli "$@"
elif [ "$1" = "server" ] || [ -z "$1" ]; then
    echo "🌐 Starting MCP server..."
    exec python -m erasmus_partner_agent.mcp_server
else
    # Custom command
    echo "🔧 Running custom command: $@"
    exec "$@"
fi