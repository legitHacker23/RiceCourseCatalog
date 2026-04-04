import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from typing import Dict, List
import time

from .vector_store import RiceVectorStore
from .app import FastGPTWrapper
import openai
import os

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat with RAG"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vector_store = None
        self.gpt_wrapper = None
        self.session_id = None
        self.user_profile = {}
        
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Initialize components
            await self.initialize_components()
            
            # Accept connection
            await self.accept()
            
            # Send welcome message
            await self.send_json({
                'type': 'system_message',
                'message': '🦉 Rice Course Assistant connected! How can I help you today?',
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        logger.info(f"Chat session {self.session_id} disconnected")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'user_profile_update':
                await self.handle_profile_update(data)
            elif message_type == 'session_init':
                await self.handle_session_init(data)
                
        except json.JSONDecodeError:
            await self.send_error("Invalid message format")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send_error("An error occurred processing your message")
    
    async def handle_chat_message(self, data: Dict):
        """Handle chat message with RAG pipeline"""
        user_message = data.get('message', '').strip()
        if not user_message:
            return
        
        # Extract parameters
        space_id = data.get('space_id', 'default')
        selected_advisor = data.get('advisor', 'general')
        
        # Send typing indicator
        await self.send_json({
            'type': 'typing_start',
            'timestamp': time.time()
        })
        
        try:
            # Start RAG pipeline
            response = await self.process_rag_query(
                user_message, 
                selected_advisor,
                space_id
            )
            
            # Send final response
            await self.send_json({
                'type': 'chat_response',
                'message': response['content'],
                'metadata': response['metadata'],
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            await self.send_error("Sorry, I encountered an error. Please try again.")
        
        finally:
            # Stop typing indicator
            await self.send_json({
                'type': 'typing_stop',
                'timestamp': time.time()
            })
    
    async def process_rag_query(self, query: str, advisor: str, space_id: str) -> Dict:
        """Complete RAG pipeline implementation"""
        
        # Step 1: Enhanced Prompt (with agents if needed)
        enhanced_query = await self.enhance_prompt_with_agents(query, advisor)
        
        # Step 2: Context Retrieval (Vector Search)
        relevant_docs = await self.retrieve_context(enhanced_query)
        
        # Step 3: Response Generation with Streaming
        response = await self.generate_response_with_streaming(
            enhanced_query, 
            relevant_docs, 
            advisor
        )
        
        return response
    
    async def enhance_prompt_with_agents(self, query: str, advisor: str) -> str:
        """Enhance prompt with personal assistant features"""
        
        # Add user context from profile
        context_parts = [query]
        
        if self.user_profile.get('major'):
            context_parts.append(f"Student major: {self.user_profile['major']}")
        
        if self.user_profile.get('completed_courses'):
            completed = ', '.join(self.user_profile['completed_courses'][:5])  # Limit for token management
            context_parts.append(f"Completed courses: {completed}")
        
        if self.user_profile.get('current_year'):
            context_parts.append(f"Academic level: {self.user_profile['current_year']}")
        
        # Add advisor-specific context
        advisor_context = {
            'computer_science': "Focus on COMP, MATH, STAT, ELEC courses and programming skills",
            'pre_med': "Focus on medical school requirements: CHEM, BIOS, PHYS sequences",
            'engineering': "Focus on engineering fundamentals and math/physics foundation",
            'mathematics': "Focus on MATH, STAT courses and theoretical foundations"
        }
        
        if advisor in advisor_context:
            context_parts.append(advisor_context[advisor])
        
        return " | ".join(context_parts)
    
    async def retrieve_context(self, query: str, k: int = 8) -> List[Dict]:
        """Retrieve relevant context using vector search"""
        
        # Perform vector search
        search_results = self.vector_store.search(query, k=k)
        
        # Send search progress update
        await self.send_json({
            'type': 'search_progress',
            'found_documents': len(search_results),
            'timestamp': time.time()
        })
        
        return search_results
    
    async def generate_response_with_streaming(self, query: str, context_docs: List[Dict], advisor: str) -> Dict:
        """Generate response with streaming output"""
        
        # Build context for GPT
        context_text = self.build_gpt_context(context_docs, advisor)
        
        # Create system prompt
        system_prompt = self.get_advisor_system_prompt(advisor)
        
        # Token count management
        max_context_tokens = 6000  # Leave room for response
        context_text = self.manage_token_count(context_text, max_context_tokens)
        
        # Send context info
        await self.send_json({
            'type': 'context_info',
            'documents_count': len(context_docs),
            'context_length': len(context_text.split()),
            'timestamp': time.time()
        })
        
        # Generate streaming response
        full_response = ""
        
        try:
            # Make OpenAI API call with streaming
            response = await self.make_streaming_openai_call(
                system_prompt,
                f"Context:\n{context_text}\n\nQuestion: {query}"
            )
            
            # Stream response chunks
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    full_response += chunk_text
                    
                    # Send streaming chunk
                    await self.send_json({
                        'type': 'response_chunk',
                        'chunk': chunk_text,
                        'timestamp': time.time()
                    })
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            full_response = "I apologize, but I encountered an error generating the response. Please try again."
        
        return {
            'content': full_response,
            'metadata': {
                'context_docs_count': len(context_docs),
                'advisor': advisor,
                'processing_time': time.time()
            }
        }
    
    async def make_streaming_openai_call(self, system_prompt: str, user_message: str):
        """Make streaming OpenAI API call"""
        
        client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        return await client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4" for higher quality
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1500,
            temperature=0.1,
            stream=True
        )
    
    def build_gpt_context(self, docs: List[Dict], advisor: str) -> str:
        """Build context string from retrieved documents"""
        
        context_parts = []
        
        for i, doc in enumerate(docs[:8]):  # Limit for token management
            course = doc['document']['metadata']['course']
            context_parts.append(f"""
Course {i+1}: {course.get('course_code', 'N/A')}
Title: {course.get('title', 'N/A')}
Description: {course.get('description', 'N/A')[:300]}...
Department: {doc['document']['department']}
Credits: {course.get('credit_hours', course.get('credits', 'N/A'))}
Prerequisites: {course.get('prerequisites', 'None')}
""")
        
        return "\n".join(context_parts)
    
    def get_advisor_system_prompt(self, advisor: str) -> str:
        """Get advisor-specific system prompt"""
        
        base_prompt = """You are a Rice University Academic Advisor. Use ONLY the provided course data to answer questions. 
        Be specific, helpful, and provide course codes, prerequisites, and credits when relevant.
        If information isn't in the provided context, say so rather than making assumptions."""
        
        advisor_specializations = {
            'computer_science': base_prompt + " Focus on computer science, programming, and technical courses.",
            'pre_med': base_prompt + " Focus on pre-medical requirements and course sequences.",
            'engineering': base_prompt + " Focus on engineering programs and technical foundations.",
            'mathematics': base_prompt + " Focus on mathematics and statistics courses."
        }
        
        return advisor_specializations.get(advisor, base_prompt)
    
    def manage_token_count(self, text: str, max_tokens: int) -> str:
        """Simple token management by word count approximation"""
        words = text.split()
        # Rough approximation: 1 token ≈ 0.75 words
        max_words = int(max_tokens * 0.75)
        
        if len(words) > max_words:
            return ' '.join(words[:max_words]) + "... [truncated]"
        
        return text
    
    async def initialize_components(self):
        """Initialize vector store and GPT wrapper"""
        
        # Initialize vector store
        self.vector_store = RiceVectorStore()
        await asyncio.get_event_loop().run_in_executor(
            None, 
            self.vector_store.load_and_index_courses
        )
        
        # Initialize GPT wrapper
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        client = openai.OpenAI(api_key=api_key)
        self.gpt_wrapper = FastGPTWrapper(client)
        
        # Generate session ID
        self.session_id = f"session_{int(time.time())}"
        
        logger.info(f"Initialized chat session {self.session_id}")
    
    async def send_json(self, data: Dict):
        """Send JSON message to WebSocket"""
        await self.send(text_data=json.dumps(data))
    
    async def send_error(self, message: str):
        """Send error message"""
        await self.send_json({
            'type': 'error',
            'message': message,
            'timestamp': time.time()
        })
    
    async def handle_profile_update(self, data: Dict):
        """Handle user profile updates"""
        self.user_profile.update(data.get('profile', {}))
        
        await self.send_json({
            'type': 'profile_updated',
            'message': 'Profile updated successfully',
            'timestamp': time.time()
        })
    
    async def handle_session_init(self, data: Dict):
        """Handle session initialization"""
        self.user_profile = data.get('user_profile', {})
        
        await self.send_json({
            'type': 'session_initialized',
            'session_id': self.session_id,
            'timestamp': time.time()
        })
