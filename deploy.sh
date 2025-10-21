#!/bin/bash

# 🐳 NotesApp Docker Deployment Script
# This script helps you deploy NotesApp with Docker quickly and safely

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║                   NotesApp Docker                    ║"
echo "║              Deployment Assistant                    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

print_success "All prerequisites are met!"

# Check for Google Cloud credentials
if [ ! -f "google-credentials.json" ]; then
    print_warning "Google Cloud credentials file not found!"
    echo "Please place your Google Cloud Vision API credentials in 'google-credentials.json'"
    read -p "Do you want to continue without it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check environment file
if [ ! -f ".env" ]; then
    print_status "Creating environment file from template..."
    cp .env.docker .env
    print_warning "Please edit .env file with your settings before continuing"
    read -p "Press Enter when ready..."
fi

# Function to show menu
show_menu() {
    echo
    echo "What would you like to do?"
    echo "1) 🚀 Start all services"
    echo "2) 🛑 Stop all services"
    echo "3) 🔄 Restart all services"
    echo "4) 🏗️  Build and start (force rebuild)"
    echo "5) 📊 View logs"
    echo "6) 📈 Check service status"
    echo "7) 🧹 Clean up (remove containers and volumes)"
    echo "8) 🔧 Open shell in app container"
    echo "9) ❓ Show service URLs"
    echo "0) 🚪 Exit"
    echo
}

# Function to start services
start_services() {
    print_status "Starting NotesApp services..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully!"
        show_urls
    else
        print_error "Failed to start services"
        return 1
    fi
}

# Function to stop services
stop_services() {
    print_status "Stopping NotesApp services..."
    docker-compose down
    print_success "Services stopped!"
}

# Function to restart services
restart_services() {
    print_status "Restarting NotesApp services..."
    docker-compose restart
    print_success "Services restarted!"
}

# Function to build and start
build_and_start() {
    print_status "Building and starting services..."
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        print_success "Services built and started successfully!"
        show_urls
    else
        print_error "Failed to build and start services"
        return 1
    fi
}

# Function to view logs
view_logs() {
    echo "Choose service to view logs:"
    echo "1) All services"
    echo "2) NotesApp only"
    echo "3) Ollama only"
    echo "4) ChromaDB only"
    read -p "Enter choice (1-4): " log_choice
    
    case $log_choice in
        1) docker-compose logs -f ;;
        2) docker-compose logs -f notesapp ;;
        3) docker-compose logs -f ollama ;;
        4) docker-compose logs -f chromadb ;;
        *) print_error "Invalid choice" ;;
    esac
}

# Function to check status
check_status() {
    print_status "Service Status:"
    docker-compose ps
    echo
    print_status "Container Health:"
    docker inspect notesapp --format='{{.State.Health.Status}}' 2>/dev/null || echo "Health check not available"
}

# Function to clean up
cleanup() {
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        docker-compose down -v --rmi local
        print_success "Cleanup completed!"
    fi
}

# Function to open shell
open_shell() {
    print_status "Opening shell in NotesApp container..."
    docker-compose exec notesapp /bin/bash
}

# Function to show URLs
show_urls() {
    echo
    print_success "🌐 Service URLs:"
    echo "  📝 NotesApp:  http://localhost:5000"
    echo "  🤖 Ollama:    http://localhost:11434"
    echo "  📊 ChromaDB:  http://localhost:8000"
    echo
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (0-9): " choice
    
    case $choice in
        1) start_services ;;
        2) stop_services ;;
        3) restart_services ;;
        4) build_and_start ;;
        5) view_logs ;;
        6) check_status ;;
        7) cleanup ;;
        8) open_shell ;;
        9) show_urls ;;
        0) 
            print_success "Goodbye! 👋"
            exit 0 
            ;;
        *)
            print_error "Invalid choice. Please try again."
            ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
done
