#!/bin/bash
# OpenAlgo Docker Quick Start Script

set -e

echo "================================================"
echo "   OpenAlgo Docker Quick Start"
echo "================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first:"
    echo "   https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is installed and running"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .sample.env..."
    cp .sample.env .env
    
    echo ""
    echo "⚠️  IMPORTANT: You must edit .env file before continuing!"
    echo ""
    echo "Required changes:"
    echo "  1. Set APP_KEY (generate with: python -c \"import secrets; print(secrets.token_hex(32))\")"
    echo "  2. Set API_KEY_PEPPER (generate with: python -c \"import secrets; print(secrets.token_hex(32))\")"
    echo "  3. Set your broker in REDIRECT_URL (e.g., http://127.0.0.1:5000/zerodha/callback)"
    echo "  4. Set BROKER_API_KEY and BROKER_API_SECRET"
    echo ""
    read -p "Press Enter after you've edited .env file..."
else
    echo "✅ .env file found"
fi

# Create required directories
echo ""
echo "📁 Creating required directories..."
mkdir -p log log/strategies strategies strategies/scripts keys db
echo "✅ Directories created"

# Build and start services
echo ""
echo "🐳 Building and starting Docker containers..."
echo "   (This may take a few minutes on first run)"
echo ""

docker-compose up -d --build

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if container is running
if docker-compose ps | grep -q "openalgo-web.*Up"; then
    echo ""
    echo "================================================"
    echo "   ✅ OpenAlgo is running!"
    echo "================================================"
    echo ""
    echo "Access your services at:"
    echo "  🌐 Web UI:     http://localhost:5000"
    echo "  🔌 WebSocket:  ws://localhost:8765"
    echo "  📡 API:        http://localhost:5000/api/v1/"
    echo ""
    echo "Useful commands:"
    echo "  View logs:     docker-compose logs -f"
    echo "  Stop:          docker-compose down"
    echo "  Restart:       docker-compose restart"
    echo ""
    echo "See DOCKER_SETUP.md for detailed documentation"
    echo "================================================"
else
    echo ""
    echo "❌ Container failed to start. Checking logs..."
    echo ""
    docker-compose logs --tail=50
    echo ""
    echo "Please check the errors above and see DOCKER_SETUP.md for troubleshooting."
fi
