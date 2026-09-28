import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Groq Configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-70b-versatile')
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1024'))
    
    # ChromaDB Configuration
    CHROMA_PERSIST_DIRECTORY = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    # Scraper Configuration
    COLLEGE_URL = 'https://www.mjrcet.org/'
    SCRAPED_DATA_PATH = './data/scraped_data.json'
