from groq import Groq
from typing import List, Dict
from app.config import Config
from app.knowledge_base import KnowledgeBase


class LLMHandler:
    def __init__(self):
        self.config = Config()
        
        if not self.config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Initialize Groq client
        self.client = Groq(api_key=self.config.GROQ_API_KEY)
        self.knowledge_base = KnowledgeBase()
        
        # System prompt for the chatbot
        self.system_prompt = """You are the official AI assistant for MJRCET, an engineering college affiliated with JNTUA.

Your role is to answer questions about the college including:
- Courses and departments (B.Tech, M.Tech, Diploma programs)
- Admissions process, eligibility, and requirements
- Fee structures and scholarships
- College timings and schedules
- Facilities: hostels, transport, library, labs, canteen, sports
- Examination patterns, syllabus, and results
- Placements and career opportunities
- Faculty, administration, and contact details

Guidelines:
1. Answer directly and confidently, as if you know the college well — synthesize the context into a natural answer
2. NEVER mention "context", "sources", "documents", "according to the website", or include citation markers, source numbers, or raw URLs in your answer
3. Source attribution is displayed separately by the interface — your job is only to give a clean, readable answer
4. Use markdown formatting: **bold** for key terms, bullet points for lists, tables for structured data like fees or comparisons
5. Give exact details (names, numbers, dates) when the information is available
6. ALWAYS include phone numbers when they appear in the context — for questions about contacting the college, admissions, or any department, list the relevant phone numbers prominently (use the main office numbers for general queries and department help-desk numbers for department queries)
6b. For contact-related questions, format phone numbers clearly, e.g. **Phone:** +91-9491054763
7. If the information is genuinely missing, briefly say what you do know and suggest contacting the college office — don't over-apologize or list what's missing
7. If a relevant official document (like a syllabus or fee PDF) exists, you may mention its name in plain text, e.g. "the Fee Structure document on the college website"
8. Keep answers focused — answer what was asked, don't pad with disclaimers

Remember: You represent MJRCET, so maintain a warm, professional, and welcoming tone."""
    
    def create_context(self, search_results: List[Dict]) -> str:
        """Create context from search results"""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            content = result['content']
            title = result['metadata'].get('title', 'Unknown')
            url = result['metadata'].get('url', '')
            
            context_parts.append(f"[Source {i}: {title}]\n{content}\nURL: {url}\n")
        
        return "\n---\n".join(context_parts)
    
    def generate_response(self, user_query: str, chat_history: List[Dict] = None) -> Dict:
        """Generate response using Groq LLM with RAG"""
        try:
            # Search knowledge base
            search_results = self.knowledge_base.search(user_query, n_results=5)

            # For contact-type questions, ensure the main contact page is in context
            contact_keywords = ('contact', 'phone', 'call', 'email', 'mail', 'reach', 'help desk', 'helpdesk', 'talk to', 'speak to')
            if any(k in user_query.lower() for k in contact_keywords):
                contact_results = self.knowledge_base.search(
                    'contact phone email office', n_results=3,
                    where={'url': 'https://www.mjrcet.org/contact.php'})
                seen = {r['content'] for r in search_results}
                contact_results = [r for r in contact_results if r['content'] not in seen]
                search_results = contact_results + search_results[:max(0, 7 - len(contact_results))]
            
            if not search_results:
                return {
                    'response': "I apologize, but I don't have enough information to answer that question. Could you please rephrase or ask about specific aspects of MJRCET like admissions, courses, facilities, or fees?",
                    'sources': []
                }
            
            # Create context from search results
            context = self.create_context(search_results)
            
            # Prepare messages for Groq
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": f"""Context from MJRCET website:
{context}

---

User Question: {user_query}

Answer the question using only the context above. Write a clean, natural response — do NOT mention the sources, context, or URLs in your answer text."""
                }
            ]
            
            # Add chat history if provided
            if chat_history:
                # Insert history before the current question
                for msg in chat_history[-4:]:  # Last 4 messages for context
                    messages.insert(-1, msg)
            
            # Call Groq API
            completion = self.client.chat.completions.create(
                model=self.config.GROQ_MODEL,
                messages=messages,
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_TOKENS,
                top_p=1,
                stream=False
            )
            
            # Extract response
            response_text = completion.choices[0].message.content
            
            # Prepare sources
            sources = [
                {
                    'title': result['metadata'].get('title', 'Unknown'),
                    'url': result['metadata'].get('url', ''),
                    'snippet': result['content'][:200] + '...'
                }
                for result in search_results[:3]  # Top 3 sources
            ]
            
            return {
                'response': response_text,
                'sources': sources,
                'model': self.config.GROQ_MODEL
            }
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return {
                'response': f"I encountered an error while processing your question. Please try again. Error: {str(e)}",
                'sources': [],
                'error': str(e)
            }
    
    def test_connection(self) -> bool:
        """Test Groq API connection"""
        try:
            completion = self.client.chat.completions.create(
                model=self.config.GROQ_MODEL,
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"Groq API connection failed: {str(e)}")
            return False


def main():
    """Test the LLM handler"""
    print("Initializing LLM Handler...")
    llm = LLMHandler()
    
    # Test connection
    print("Testing Groq API connection...")
    if llm.test_connection():
        print("✓ Groq API connection successful!")
    else:
        print("✗ Groq API connection failed!")
        return
    
    # Test query
    print("\nTesting query...")
    test_query = "What courses are offered in CSE department?"
    result = llm.generate_response(test_query)
    
    print(f"\nQuery: {test_query}")
    print(f"\nResponse:\n{result['response']}")
    print(f"\nSources: {len(result.get('sources', []))}")
    for i, source in enumerate(result.get('sources', []), 1):
        print(f"{i}. {source['title']}")


if __name__ == "__main__":
    main()
