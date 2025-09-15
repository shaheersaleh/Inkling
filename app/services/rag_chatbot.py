import logging
from typing import List, Dict, Any, Optional
from app.services.vector_embeddings import VectorEmbeddingService
from app.services.ai_classification import SubjectClassificationService
import ollama

class RAGChatbotService:
    def __init__(self):
        self.vector_service = VectorEmbeddingService()
        self.classification_service = SubjectClassificationService()
        self.enabled = False
        
        # Check if services are available
        if self.vector_service.enabled and self.classification_service.enabled:
            self.enabled = True
            logging.info("RAG Chatbot service initialized successfully")
        else:
            logging.warning("RAG Chatbot service disabled - dependencies not available")
    
    def search_and_answer(self, question: str, user_id: int, max_context_notes: int = 3) -> Dict[str, Any]:
        """
        Search through user's notes and provide an AI-generated answer
        
        Args:
            question (str): User's question
            user_id (int): User ID for note filtering
            max_context_notes (int): Maximum number of notes to use as context (reduced for relevance)
            
        Returns:
            Dict containing answer, sources, and metadata
        """
        if not self.enabled:
            return {
                "answer": "Sorry, the chatbot service is currently unavailable.",
                "sources": [],
                "sources_detailed": [],
                "confidence": 0.0
            }
        
        try:
            # Detect if the question mentions specific subjects
            subject_filter = self._detect_subject_in_question(question, user_id)
            
            # Search for relevant notes using vector similarity
            search_results = self.vector_service.search_notes(
                query=question,
                user_id=user_id,
                n_results=max_context_notes * 2,  # Get more to filter later
                subject_filter=subject_filter
            )
            
            if not search_results:
                return {
                    "answer": "I couldn't find any relevant notes to answer your question. Try asking about topics you have notes on.",
                    "sources": [],
                    "sources_detailed": [],
                    "confidence": 0.0
                }
            
            # Build context from search results
            context = self._build_context(search_results)
            
            # Generate answer using Ollama
            answer = self._generate_answer(question, context)
            
            # Extract source information - filter for high relevance only
            sources = []
            sources_detailed = []
            
            for result in search_results:
                # Only include sources with relevance score > 0.3 (adjust threshold as needed)
                if result.get("relevance_score", 0) > 0.3:
                    # Basic source info for web display
                    sources.append({
                        "note_id": result["note_id"],
                        "title": result["title"],
                        "relevance_score": result["relevance_score"],
                        "excerpt": result.get("matched_text", "")[:150] + "..." if len(result.get("matched_text", "")) > 150 else result.get("matched_text", "")
                    })
                    
                    # Detailed source info for tkinter display
                    sources_detailed.append({
                        "note_id": result["note_id"],
                        "title": result["title"],
                        "content": result.get("matched_text", ""),
                        "subject": result.get("subject_name", ""),
                        "created_at": result.get("created_at", ""),
                        "similarity_score": result["relevance_score"]
                    })
            
            # Limit to top 3 most relevant sources
            sources = sources[:max_context_notes]
            sources_detailed = sources_detailed[:max_context_notes]
            
            return {
                "answer": answer,
                "sources": sources,
                "sources_detailed": sources_detailed,
                "confidence": min([r["relevance_score"] for r in search_results])
            }
            
        except Exception as e:
            logging.error(f"Error in RAG chatbot: {e}")
            return {
                "answer": "Sorry, I encountered an error while processing your question.",
                "sources": [],
                "sources_detailed": [],
                "confidence": 0.0
            }
    
    def _build_context(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context with subject organization from search results"""
        context_parts = []
        subjects_info = {}
        
        for i, result in enumerate(search_results, 1):
            subject = result.get('subject', 'No Subject')
            
            # Organize by subject
            if subject not in subjects_info:
                subjects_info[subject] = []
            
            subjects_info[subject].append({
                'index': i,
                'title': result['title'],
                'content': result.get('matched_text', ''),
                'relevance': result.get('relevance_score', 0)
            })
            
            # Build context part
            context_parts.append(
                f"Note {i} - Subject: {subject} (Title: {result['title']}):\n{result.get('matched_text', '')}\n"
            )
        
        return {
            'context_text': "\n".join(context_parts),
            'subjects_info': subjects_info,
            'total_notes': len(search_results)
        }
    
    def _generate_answer(self, question: str, context: Dict[str, Any]) -> str:
        """Generate answer using Ollama with subject-aware prompting"""
        try:
            # Build subject summary
            subjects_summary = []
            for subject, notes in context['subjects_info'].items():
                note_count = len(notes)
                subjects_summary.append(f"- {subject}: {note_count} note{'s' if note_count > 1 else ''}")
            
            subjects_text = "\n".join(subjects_summary) if subjects_summary else "No specific subjects identified"
            
            # Create enhanced prompt with subject awareness
            prompt = f"""You are a helpful assistant that answers questions based on the user's personal study notes. You have access to notes from multiple subjects and should be aware of the subject context.

AVAILABLE SUBJECTS IN NOTES:
{subjects_text}

RELEVANT NOTES FOUND:
{context['context_text']}

USER QUESTION: {question}

INSTRUCTIONS:
1. If the question asks about a specific subject, focus on notes from that subject
2. If multiple subjects are relevant, mention which subjects contain relevant information
3. Provide specific references to note titles when possible
4. If the context doesn't contain enough information to answer the question, say so clearly
5. Keep your response concise but informative
6. When mentioning information, indicate which subject/note it comes from

Answer:"""

            response = ollama.chat(
                model='llama3',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful study assistant that answers questions based on personal notes. Be aware of different subjects and provide subject-specific responses when appropriate. Be concise and accurate.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            return response['message']['content'].strip()
            
        except Exception as e:
            logging.error(f"Error generating answer with Ollama: {e}")
            return "I'm having trouble generating an answer right now. Please try again later."

    def _detect_subject_in_question(self, question: str, user_id: int) -> str:
        """Detect if the question mentions a specific subject"""
        try:
            # Get user's subjects from database
            from app.models import Subject
            user_subjects = Subject.query.filter_by(user_id=user_id).all()
            
            question_lower = question.lower()
            
            # Check for exact subject name matches
            for subject in user_subjects:
                if subject.name.lower() in question_lower:
                    return subject.name
            
            # Check for common subject keywords
            subject_keywords = {
                'math': ['math', 'mathematics', 'calculus', 'algebra', 'geometry', 'trigonometry'],
                'physics': ['physics', 'mechanics', 'thermodynamics', 'electricity', 'magnetism'],
                'chemistry': ['chemistry', 'organic', 'inorganic', 'chemical', 'molecule'],
                'biology': ['biology', 'anatomy', 'physiology', 'genetics', 'cell'],
                'computer science': ['programming', 'coding', 'algorithm', 'data structure', 'software'],
                'history': ['history', 'historical', 'ancient', 'medieval', 'modern'],
                'literature': ['literature', 'poetry', 'novel', 'author', 'writing'],
                'economics': ['economics', 'market', 'economy', 'finance', 'money']
            }
            
            for subject_name, keywords in subject_keywords.items():
                if any(keyword in question_lower for keyword in keywords):
                    # Check if user has a subject that matches
                    for subject in user_subjects:
                        if subject_name.lower() in subject.name.lower() or subject.name.lower() in subject_name.lower():
                            return subject.name
            
            return None  # No specific subject detected
            
        except Exception as e:
            logging.error(f"Error detecting subject in question: {e}")
            return None
    
    def generate_chat_title(self, question: str) -> str:
        """Generate a descriptive title for a chat based on the first question"""
        try:
            # Use Ollama to generate a concise title
            prompt = f"""Generate a short, descriptive title (max 6 words) for a chat conversation that starts with this question: "{question}"

The title should capture the main topic or subject being asked about. Do not include quotes or extra formatting.

Examples:
- "What is photosynthesis?" → "Photosynthesis Questions"
- "Help me understand calculus derivatives" → "Calculus Derivatives Help"
- "Explain quantum physics concepts" → "Quantum Physics Concepts"

Question: {question}
Title:"""

            response = ollama.chat(
                model='llama3',
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            title = response['message']['content'].strip()
            
            # Clean up and limit length
            if len(title) > 50:
                title = title[:47] + "..."
            
            return title if title else "Chat Session"
            
        except Exception as e:
            logging.error(f"Error generating chat title: {e}")
            # Fallback: extract key words from question
            words = question.split()[:4]
            return " ".join(words).title() + "..."

    def get_suggested_questions(self, user_id: int) -> List[str]:
        """Generate suggested questions based on user's notes and subjects"""
        try:
            # Get user's subjects
            from app.models import Subject
            user_subjects = Subject.query.filter_by(user_id=user_id).limit(3).all()
            
            suggestions = [
                "What are the main topics in my notes?",
                "Can you summarize my recent notes?",
                "What have I been studying recently?",
                "What questions should I review for my exams?"
            ]
            
            # Add subject-specific suggestions
            if user_subjects:
                for subject in user_subjects[:2]:  # Limit to 2 subjects
                    suggestions.append(f"What have I learned about {subject.name}?")
                
                # Add a general subject overview question
                subject_names = [s.name for s in user_subjects]
                if len(subject_names) > 1:
                    suggestions.append(f"Compare my notes on {subject_names[0]} and {subject_names[1]}")
            
            return suggestions[:5]  # Return max 5 suggestions
            
        except Exception as e:
            logging.error(f"Error generating suggestions: {e}")
            return [
                "What can you help me with?",
                "What topics do I have notes on?",
                "Summarize my study materials"
            ]
