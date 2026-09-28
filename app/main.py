from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from app.config import Config
from app.llm_handler import LLMHandler
from app.knowledge_base import KnowledgeBase
from app.scraper import MJRCETScraper
import os

app = Flask(__name__)

# Configure CORS
config = Config()
CORS(app, resources={
    r"/api/*": {
        "origins": config.CORS_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize LLM handler
llm_handler = None

def init_llm():
    """Initialize LLM handler"""
    global llm_handler
    try:
        llm_handler = LLMHandler()
        print("✓ LLM Handler initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize LLM Handler: {str(e)}")
        return False


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    kb = KnowledgeBase()
    stats = kb.get_collection_stats()
    
    return jsonify({
        'status': 'healthy',
        'llm_initialized': llm_handler is not None,
        'knowledge_base': stats
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint - main interaction point"""
    try:
        if not llm_handler:
            return jsonify({
                'error': 'LLM handler not initialized. Please check your GROQ_API_KEY.'
            }), 500
        
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing message in request body'
            }), 400
        
        user_message = data['message']
        chat_history = data.get('history', [])
        
        # Generate response
        result = llm_handler.generate_response(user_message, chat_history)
        
        return jsonify({
            'response': result['response'],
            'sources': result.get('sources', []),
            'model': result.get('model', config.GROQ_MODEL)
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/refresh-knowledge', methods=['POST'])
def refresh_knowledge():
    """Refresh knowledge base by re-scraping and re-indexing"""
    try:
        # Scrape website
        scraper = MJRCETScraper()
        data = scraper.scrape_website(max_pages=50, delay=1.0)
        scraper.save_data(config.SCRAPED_DATA_PATH)
        
        # Re-index data
        kb = KnowledgeBase()
        success = kb.load_and_index_data(config.SCRAPED_DATA_PATH)
        
        if success:
            stats = kb.get_collection_stats()
            return jsonify({
                'status': 'success',
                'message': 'Knowledge base refreshed successfully',
                'stats': stats
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to refresh knowledge base'
            }), 500
            
    except Exception as e:
        print(f"Error refreshing knowledge: {str(e)}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get knowledge base statistics"""
    try:
        kb = KnowledgeBase()
        stats = kb.get_collection_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/search', methods=['POST'])
def search():
    """Direct search endpoint (for testing)"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing query in request body'
            }), 400
        
        kb = KnowledgeBase()
        results = kb.search(data['query'], n_results=data.get('n_results', 5))
        
        return jsonify({
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/', methods=['GET'])
def index():
    """Serve the chat interface"""
    return render_template('index.html')


if __name__ == '__main__':
    print("=" * 60)
    print("MJRCET AI FAQ Assistant - Backend Server")
    print("=" * 60)
    
    # Check if data exists
    if not os.path.exists(config.SCRAPED_DATA_PATH):
        print("\n⚠ Warning: Scraped data not found!")
        print(f"Please run: python -m app.scraper")
        print("Or use the /api/refresh-knowledge endpoint\n")
    
    # Check if knowledge base exists
    if not os.path.exists(config.CHROMA_PERSIST_DIRECTORY):
        print("\n⚠ Warning: Knowledge base not initialized!")
        print(f"Please run: python -m app.knowledge_base")
        print("This will create embeddings from scraped data\n")
    
    # Initialize LLM
    print("\nInitializing LLM Handler...")
    if init_llm():
        print("✓ Ready to serve requests!\n")
    else:
        print("⚠ LLM Handler initialization failed. Check your GROQ_API_KEY\n")
    
    print("=" * 60)
    print(f"Server starting on http://localhost:5000")
    print("=" * 60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.FLASK_DEBUG
    )
