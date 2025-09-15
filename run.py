import os
import logging

# Disable ChromaDB telemetry before any imports
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_DISABLED"] = "True" 
os.environ["POSTHOG_DISABLED"] = "True"

# Completely suppress chromadb telemetry logging
logging.getLogger('chromadb.telemetry').disabled = True
logging.getLogger('chromadb.telemetry.product').disabled = True
logging.getLogger('chromadb.telemetry.product.posthog').disabled = True

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('vector_db', exist_ok=True)
    
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5002))
    
    app.run(debug=debug, host='0.0.0.0', port=port)
