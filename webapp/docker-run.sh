#!/bin/bash
# Docker helper script for Anime4K Web UI

set -e

show_help() {
    echo "Anime4K Web UI Docker Helper"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build    Build the Docker image"
    echo "  run      Run the webapp with Flask (default)"
    echo "  simple   Run the webapp with simple server"
    echo "  compose  Start with docker-compose"
    echo "  prod     Build and run production version"
    echo "  stop     Stop running containers"
    echo "  clean    Remove containers and images"
    echo "  logs     Show container logs"
    echo "  help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 run"
    echo "  $0 simple"
    echo "  $0 compose"
    echo "  $0 prod"
}

build_image() {
    echo "Building Anime4K Web UI Docker image..."
    docker build -t anime4k-webapp .
    echo "Build complete!"
}

run_flask() {
    echo "Starting Anime4K Web UI with Flask..."
    docker run -d \
        --name anime4k-webapp \
        -p 5000:5000 \
        -v "$(pwd)/uploads:/app/uploads" \
        -v "$(pwd)/outputs:/app/outputs" \
        anime4k-webapp
    echo "Flask app started on http://localhost:5000"
}

run_simple() {
    echo "Starting Anime4K Web UI with simple server..."
    docker run -d \
        --name anime4k-simple \
        -p 8000:8000 \
        -v "$(pwd)/uploads:/app/uploads" \
        -v "$(pwd)/outputs:/app/outputs" \
        anime4k-webapp python simple_server.py
    echo "Simple server started on http://localhost:8000"
}

run_compose() {
    echo "Starting with docker compose..."
    docker compose up -d
    echo "Services started. Flask app on http://localhost:5000"
}

run_prod() {
    echo "Starting Anime4K Web UI in production mode..."
    docker compose -f docker-compose.prod.yml up -d
    echo "Production app started on http://localhost:5000"
}

stop_containers() {
    echo "Stopping containers..."
    docker stop anime4k-webapp anime4k-simple anime4k-webapp-prod 2>/dev/null || true
    docker compose down 2>/dev/null || true
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true
    echo "Containers stopped."
}

clean_up() {
    echo "Cleaning up containers and images..."
    stop_containers
    docker rm anime4k-webapp anime4k-simple anime4k-webapp-prod 2>/dev/null || true
    docker rmi anime4k-webapp 2>/dev/null || true
    docker image prune -f 2>/dev/null || true
    echo "Cleanup complete."
}

show_logs() {
    echo "Container logs:"
    docker logs anime4k-webapp 2>/dev/null || docker logs anime4k-simple 2>/dev/null || docker logs anime4k-webapp-prod 2>/dev/null || echo "No running containers found."
}

# Create directories if they don't exist
mkdir -p uploads outputs

case "${1:-help}" in
    build)
        build_image
        ;;
    run)
        build_image
        run_flask
        ;;
    simple)
        build_image
        run_simple
        ;;
    compose)
        run_compose
        ;;
    prod)
        run_prod
        ;;
    stop)
        stop_containers
        ;;
    clean)
        clean_up
        ;;
    logs)
        show_logs
        ;;
    help|*)
        show_help
        ;;
esac