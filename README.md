# NotesApp - Intelligent Handwritten Notes Digitization with AI Assistant

A comprehensive web application for digitizing, organizing, and intelligently interacting with handwritten notes through advanced AI features including image text extraction, semantic search, and an intelligent AI assistant.

## 🚀 Key Features

### � **Smart Note Digitization**
- **Image Text Extraction**: Upload photos of handwritten notes with automatic text extraction using Google Cloud Vision API
- **Handwriting-Style Display**: View digitized notes in beautiful cursive handwriting fonts for authentic feel
- **Multiple Image Support**: Handle various image formats and sizes

### � **AI-Powered Assistant**
- **Intelligent Chat Interface**: Ask questions about your notes in natural language
- **Contextual Responses**: Get answers based on your specific note content
- **Source References**: See which notes were used to generate responses
- **Dynamic Chat Titles**: Conversations automatically titled based on content

### �🧠 **Advanced AI Features**
- **Subject Classification**: Automatically categorize notes using Llama3 AI model
- **Semantic Search**: Find notes using natural language queries with vector embeddings
- **RAG (Retrieval-Augmented Generation)**: Combine search with AI generation for intelligent responses
- **Vector Database**: ChromaDB for efficient similarity search

### 📚 **Organization & Management**
- **Subject Management**: Create and manage custom subjects with color coding
- **User Profiles**: Personalized dashboards with profile images
- **Multi-User Support**: Secure user authentication and data isolation
- **Note Editing**: Full CRUD operations for notes and subjects

### 🎨 **Modern Interface**
- **Clean Design**: Professional UI with subtle borders and visual hierarchy
- **Responsive Layout**: Three-panel design (chat history, main chat, notes panel)
- **Real-time Updates**: Auto-scrolling chat, dynamic content loading
- **Interactive Elements**: Hover effects, smooth transitions

## 🛠️ Technology Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Database
- **Flask-Login** - User session management

### AI & ML Services
- **Google Cloud Vision API** - Text extraction from images
- **Ollama + Llama3** - Local AI model for subject classification
- **ChromaDB** - Vector database for semantic search
- **Sentence Transformers** - Text embeddings
- **Langchain** - RAG framework integration

### Deployment
- **Docker** - Containerization for easy deployment
- **Docker Compose** - Multi-service orchestration
- **Multi-stage builds** - Optimized container images
- **Health checks** - Service monitoring and reliability

### Frontend
- **HTML5 & CSS3**
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript** - Interactive features
- **Font Awesome** - Icons

## 🆕 Latest Enhancements

### 🎨 **UI/UX Improvements**
- **Enhanced Visual Boundaries**: Subtle borders for better content separation
- **Improved Chat Interface**: Auto-scrolling, dynamic titles, message borders
- **Professional Design**: Balanced shadows, clean layout, consistent spacing

### ✍️ **Handwriting Experience**
- **Cursive Font Integration**: Notes display in beautiful Dancing Script cursive font
- **Paper-like Background**: Notebook aesthetic with ruled lines and margins
- **Authentic Feel**: Slight rotation and ink effects for realistic handwriting appearance

### 🔄 **Smart Interactions**
- **Auto-opening Notes Panel**: Referenced notes automatically open in side panel
- **Real-time Chat Scrolling**: Smooth auto-scroll to latest messages
- **Contextual Chat Titles**: Dynamic headers showing conversation topics
- **Enhanced Source References**: Clickable note references with hover effects

## 📋 Prerequisites

Before running the application, ensure you have:

1. **Python 3.8 or higher** installed
2. **Ollama** installed and running ([Installation Guide](https://ollama.ai/))
3. **Google Cloud Vision API** credentials ([Setup Guide](https://cloud.google.com/vision/docs/setup))
4. **Git** for version control

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd notesApp
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Ollama
```bash
# Install Ollama (follow instructions at https://ollama.ai/)
ollama pull llama3
```

### 5. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_DEBUG=True
PORT=5000

# Database
DATABASE_URL=sqlite:///notes_app.db

# Google Cloud Vision API
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

### 6. Set Up Google Cloud Vision API
1. Create a Google Cloud Project
2. Enable the Vision API
3. Create a service account and download the JSON key file
4. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your JSON key file

### 7. Run the Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## 🐳 Docker Deployment (Recommended)

For easier setup and deployment, use Docker:

### Quick Start with Docker
```bash
# Clone the repository
git clone <repository-url>
cd notesApp

# Place your Google Cloud credentials
cp /path/to/your/service-account-key.json ./google-credentials.json

# Start all services
./deploy.sh
```

Or manually:
```bash
# Copy environment template
cp .env.docker .env

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Services
- **NotesApp**: http://localhost:5000
- **Ollama AI**: http://localhost:11434  
- **ChromaDB**: http://localhost:8000

For detailed Docker deployment instructions, see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).

## 📖 Usage Guide

### Getting Started
1. **Register**: Create a new account at `/register`
2. **Login**: Sign in to your account at `/login`
3. **Create Subjects**: Organize your notes by creating subjects
4. **Upload Notes**: Take photos of handwritten notes and upload them
5. **Search**: Use semantic search to find specific notes

### Key Features

#### Image Upload & Text Extraction
- Upload clear photos of handwritten notes
- The system automatically extracts text using Google Cloud Vision API
- Confidence scores are provided for extraction accuracy

#### AI Subject Classification
- When uploading notes, the AI automatically suggests the most appropriate subject
- Classification is based on the extracted text content
- You can override AI suggestions manually

#### Semantic Search
- Search notes using natural language queries
- The system understands context and meaning, not just keywords
- Results are ranked by relevance

#### Note Management
- Edit and update notes after creation
- Vector embeddings are automatically updated when notes are modified
- Organize notes by subjects with color coding

## 🏗️ Project Structure

```
notesApp/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models
│   ├── routes/                  # Route handlers
│   │   ├── auth.py             # Authentication routes
│   │   ├── main.py             # Main dashboard routes
│   │   ├── notes.py            # Notes management routes
│   │   └── subjects.py         # Subject management routes
│   ├── services/               # Core services
│   │   ├── text_extraction.py  # Google Cloud Vision integration
│   │   ├── ai_classification.py # Ollama/Llama3 integration
│   │   └── vector_embeddings.py # ChromaDB integration
│   ├── templates/              # HTML templates
│   │   ├── base.html           # Base template
│   │   ├── index.html          # Landing page
│   │   ├── auth/               # Authentication templates
│   │   ├── main/               # Dashboard templates
│   │   ├── notes/              # Note templates
│   │   └── subjects/           # Subject templates
│   └── static/                 # Static files
├── uploads/                    # Uploaded images storage
├── vector_db/                  # ChromaDB storage
├── requirements.txt            # Python dependencies
├── run.py                     # Application entry point
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Required |
| `FLASK_DEBUG` | Enable debug mode | `False` |
| `PORT` | Application port | `5000` |
| `DATABASE_URL` | Database connection string | `sqlite:///notes_app.db` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud service account key | Required |

### Google Cloud Vision API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Vision API
4. Create a service account with Vision API permissions
5. Download the JSON key file
6. Set the file path in `GOOGLE_APPLICATION_CREDENTIALS`

### Ollama Configuration
- Ensure Ollama is running: `ollama serve`
- Install required model: `ollama pull llama3`
- The application will automatically detect if Ollama is available

## 🚀 Deployment

### Local Development
```bash
python run.py
```

### Production Deployment
For production deployment, consider:

1. **Use a production WSGI server** (e.g., Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

2. **Use a production database** (PostgreSQL, MySQL)
3. **Set up reverse proxy** (Nginx, Apache)
4. **Configure environment variables** properly
5. **Set up SSL/HTTPS**
6. **Configure file storage** for uploaded images

### Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

## 🧪 Testing

### Running Tests
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Coverage report
pip install pytest-cov
python -m pytest --cov=app tests/
```

## 🐛 Troubleshooting

### Common Issues

#### Google Cloud Vision API Errors
- Verify your service account key is valid
- Check that the Vision API is enabled in your project
- Ensure proper permissions are set

#### Ollama Connection Issues
- Verify Ollama is running: `ollama list`
- Check if Llama3 model is installed: `ollama pull llama3`
- Restart Ollama service if needed

#### ChromaDB Issues
- Check write permissions in the `vector_db` directory
- Clear the database if corrupted: `rm -rf vector_db/`

#### File Upload Issues
- Verify the `uploads` directory exists and is writable
- Check file size limits in Flask configuration
- Ensure proper image file formats

### Debug Mode
Enable debug mode for detailed error messages:
```bash
export FLASK_DEBUG=True
python run.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 coding standards
- Add docstrings to functions and classes
- Write unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Cloud Vision API for text extraction capabilities
- Ollama team for local AI model infrastructure
- ChromaDB for vector database functionality
- Tailwind CSS for the beautiful UI framework
- Flask community for the excellent web framework

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the documentation thoroughly

---

**Built with ❤️ for efficient note management and AI-powered organization**
