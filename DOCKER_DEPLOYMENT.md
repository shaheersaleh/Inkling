# 🐳 Docker Deployment Guide for NotesApp

This guide will help you deploy NotesApp using Docker for easy setup and deployment.

## 📋 Prerequisites

- **Docker** installed ([Get Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** installed (included with Docker Desktop)
- **Google Cloud Vision API credentials** (JSON file)
- **Git** (to clone the repository)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/shaheersaleh/Inkling.git
cd Inkling
```

### 2. Set Up Google Cloud Credentials
```bash
# Place your Google Cloud Vision API credentials file in the project root
cp /path/to/your/google-credentials.json ./google-credentials.json
```

### 3. Configure Environment
```bash
# Copy the Docker environment template
cp .env.docker .env

# Edit the .env file with your settings
nano .env
```

### 4. Build and Run
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 5. Access the Application
- **NotesApp**: http://localhost:5000
- **Ollama API**: http://localhost:11434
- **ChromaDB**: http://localhost:8000

## 🏗️ Architecture

The Docker setup includes:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NotesApp      │    │     Ollama      │    │   ChromaDB      │
│   (Flask)       │◄──►│   (AI Model)    │    │  (Vector DB)    │
│   Port: 5000    │    │   Port: 11434   │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Volume Mounts

Data is persisted using Docker volumes:
- `./instance` → Database files
- `./uploads` → User uploaded images  
- `./vector_db` → Vector embeddings
- `ollama_data` → AI model data
- `chroma_data` → Vector database

## 🔧 Configuration Options

### Environment Variables

Edit `.env` file:
```bash
# Security
SECRET_KEY=your-secure-key-here

# Database
DATABASE_URL=sqlite:///instance/notes_app.db

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json

# AI Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3
```

### Custom Ports

Edit `docker-compose.yml`:
```yaml
services:
  notesapp:
    ports:
      - "8080:5000"  # Change 8080 to your preferred port
```

## 🛠️ Development vs Production

### Development Mode
```bash
# Use development compose file
docker-compose -f docker-compose.dev.yml up
```

### Production Mode
```bash
# Use production settings
FLASK_ENV=production docker-compose up -d
```

## 📊 Monitoring & Logs

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f notesapp
docker-compose logs -f ollama
```

### Health Checks
```bash
# Check service status
docker-compose ps

# Check container health
docker inspect notesapp --format='{{.State.Health.Status}}'
```

## 🔄 Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Update Services
```bash
# Pull latest images and rebuild
docker-compose pull
docker-compose up -d --build
```

### Scale Services (if needed)
```bash
# Run multiple NotesApp instances
docker-compose up -d --scale notesapp=3
```

## 💾 Data Backup

### Backup Data
```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup database
cp -r instance/ backups/$(date +%Y%m%d)/

# Backup uploads
cp -r uploads/ backups/$(date +%Y%m%d)/

# Backup vector database
cp -r vector_db/ backups/$(date +%Y%m%d)/
```

### Restore Data
```bash
# Stop services
docker-compose down

# Restore from backup
cp -r backups/20241215/* ./

# Start services
docker-compose up -d
```

## 🐛 Troubleshooting

### Common Issues

**1. Ollama model not downloading:**
```bash
# Manually pull the model
docker-compose exec ollama ollama pull llama3
```

**2. Permission errors:**
```bash
# Fix permissions
sudo chown -R $USER:$USER instance/ uploads/ vector_db/
```

**3. Google Vision API errors:**
```bash
# Check credentials file exists
ls -la google-credentials.json

# Verify file is mounted in container
docker-compose exec notesapp ls -la /app/google-credentials.json
```

**4. Port conflicts:**
```bash
# Check what's using port 5000
lsof -i :5000

# Change port in docker-compose.yml
```

### Reset Everything
```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
docker-compose up -d --build
```

## 🚀 Deployment Options

### 1. Local Development
Use `docker-compose.yml` as-is for local development.

### 2. VPS/Cloud Server
```bash
# On your server
git clone https://github.com/shaheersaleh/Inkling.git
cd Inkling
cp .env.docker .env
# Edit .env with production values
docker-compose up -d
```

### 3. Docker Hub
```bash
# Build and push to Docker Hub
docker build -t yourusername/notesapp .
docker push yourusername/notesapp
```

### 4. Cloud Platforms
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **DigitalOcean App Platform**

## 📈 Performance Optimization

### For Production:
1. **Use external database** (PostgreSQL instead of SQLite)
2. **Add Redis for caching**
3. **Use nginx as reverse proxy**
4. **Configure proper logging**
5. **Set up monitoring**

## 🔒 Security Considerations

1. **Change default SECRET_KEY**
2. **Use HTTPS in production**
3. **Restrict network access**
4. **Regular security updates**
5. **Backup encryption**

## 📞 Support

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `.env` file
3. Check service status: `docker-compose ps`
4. Review troubleshooting section above

Your NotesApp is now Dockerized and ready for deployment! 🎉
