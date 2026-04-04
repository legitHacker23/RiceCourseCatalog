#!/usr/bin/env python3
"""
Rice University Course Assistant - Flask Backend
===============================================

Flask API backend that converts the core functionality from rice_course_assistant.py
into REST API endpoints for the React frontend.

Key Features:
- Course recommendation API endpoints
- GPT-4.1 Nano integration for natural language queries
- Advisor-specific responses
- Course data management
- Fast, efficient API responses

Author: Rice Course Assistant Team
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import re
import openai
from typing import List, Dict, Tuple
from dataclasses import dataclass
import time
from dotenv import load_dotenv

# Vector store import
try:
    from vector_store import RiceVectorStore
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False
    print("⚠️ Vector store not available. Create vector_store.py for RAG functionality.")

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS to allow React frontend
CORS(app, origins=[
    'http://localhost:3000',  # Local development
    'https://ricecatalog.onrender.com',  # Render backend
    'https://main.d138s9ngzid9pl.amplifyapp.com', # Amplify frontend
    'https://www.ricecatalog.org',  # Production frontend
    'https://ricecatalog.org',  # Production frontend (without www)
], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Add a simple test endpoint
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Backend is working!', 'cors': 'enabled'})

@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'Rice Course Assistant API', 'status': 'running'})

# ================================================================
# CORE DATA STRUCTURES AND CONFIGURATION
# ================================================================

# ================================================================
# DIRECT GPT IMPLEMENTATION (NO WRAPPER)
# ================================================================

def get_direct_gpt_response(query: str, context: str, advisor: str = 'unified') -> str:
    """Direct OpenAI API call with unified advisor system."""
    
    # Unified advisor system prompt that covers all academic areas
    unified_prompt = """You are a Rice University Unified Academic Advisor with comprehensive knowledge of all academic programs and departments.

Your expertise covers:
🎓 **All Academic Programs**: Computer Science, Mathematics, Engineering, Chemistry, Physics, Business, Music, Biosciences, Humanities, Social Sciences, Architecture, Pre-Med, Pre-Law, and more.

📚 **Course Knowledge**: You have access to Rice's complete course catalog including:
- Course codes, titles, descriptions, and credit hours
- Prerequisites and course sequences
- Department-specific requirements
- Fall 2025 course offerings with instructors

🎯 **Specialized Guidance**: You can provide advice on:
- Degree requirements for any major
- Course recommendations and sequencing
- Prerequisites and academic planning
- Instructor information and course schedules
- Department-specific requirements
- Pre-professional programs (pre-med, pre-law, etc.)

💡 **CRITICAL GUIDELINES**:
- **Use the course data provided in the context to give specific, actionable advice**
- **If courses are listed in the context, recommend them confidently**
- Provide specific course codes (e.g., COMP 140, MATH 101, CHEM 121) from the context data
- Include credit hours and prerequisites when available in the context
- For prerequisite queries, provide the exact prerequisites listed in the data
- For degree requirements, provide comprehensive course lists from the data
- For instructor queries, list only courses they actually teach according to the data
- Keep responses clear, structured, and actionable
- **Be confident in recommending courses that appear in the provided context**
- **If the context shows available courses, use them to provide specific guidance**
- **Do not be overly conservative - if courses are listed, they are available to recommend**
- **For prerequisite questions, always state the exact prerequisites from the dataset**

Always provide practical, actionable advice based on the course data available."""

    try:
        # Configure OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            return "I apologize, but I'm unable to access the AI service at the moment. Please try again later."
        
        # Create OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Create the message
        messages = [
            {"role": "system", "content": unified_prompt},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
        ]
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."

# ================================================================
# MAIN APPLICATION CLASS
# ================================================================

class RiceCourseAssistant:
    """Main application class for the Rice Course Assistant backend."""
    
    def __init__(self):
        """Initialize the Rice Course Assistant."""
        self.setup_openai()
        self.load_organized_data()
        self.load_fall2025_data()
        self.load_program_requirements()
        self.load_comprehensive_courses()
        
    def setup_openai(self):
        """Setup OpenAI client for direct API access."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Warning: OpenAI API key not found. Chat functionality will be limited.")
            self.openai_available = False
            self.client = None
        else:
            print("✅ OpenAI API key configured")
            self.openai_available = True
            self.client = openai.OpenAI(api_key=api_key)
        
    def load_organized_data(self):
        """Load organized course data from JSON file."""
        try:
            # Try multiple possible paths
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'data', 'organized', 'rice_organized_data.json'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'organized', 'rice_organized_data.json'),
                os.path.join(os.getcwd(), 'data', 'organized', 'rice_organized_data.json'),
                os.path.join(os.getcwd(), '..', 'data', 'organized', 'rice_organized_data.json'),
                'data/organized/rice_organized_data.json',
                '../data/organized/rice_organized_data.json'
            ]
            
            data_path = None
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    data_path = abs_path
                    break
            
            if data_path:
                print(f"Loading course data from: {data_path}")
                with open(data_path, 'r') as f:
                    self.organized_data = json.load(f)
                    self.departments = self.organized_data.get('departments', {})
                    
                    # Extract all courses from departments since there's no top-level all_courses key
                    self.all_courses = []
                    for dept_code, dept_data in self.departments.items():
                        dept_courses = dept_data.get('courses', [])
                        for course in dept_courses:
                            # Add department code to each course for easier filtering
                            course['department'] = dept_code
                            self.all_courses.append(course)
                    
                    print(f"Successfully loaded {len(self.all_courses)} courses from {len(self.departments)} departments")
            else:
                print("Warning: Course data file not found in any of the expected locations:")
                for path in possible_paths:
                    print(f"  - {os.path.abspath(path)}")
                # Fallback data if file doesn't exist
                self.organized_data = {}
                self.departments = {}
                self.all_courses = []
        except Exception as e:
            print(f"Error loading course data: {e}")
            self.organized_data = {}
            self.departments = {}
            self.all_courses = []
    
    def load_fall2025_data(self):
        """Load Fall 2025 course data from JSON file."""
        try:
            # Try multiple possible paths for Fall 2025 data
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'rice_courses_202610_with_instructors.json'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw', 'rice_courses_202610_with_instructors.json'),
                os.path.join(os.getcwd(), 'data', 'raw', 'rice_courses_202610_with_instructors.json'),
                os.path.join(os.getcwd(), '..', 'data', 'raw', 'rice_courses_202610_with_instructors.json'),
                'data/raw/rice_courses_202610_with_instructors.json',
                '../data/raw/rice_courses_202610_with_instructors.json'
            ]
            
            data_path = None
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    data_path = abs_path
                    break
            
            if data_path:
                print(f"Loading Fall 2025 course data from: {data_path}")
                with open(data_path, 'r') as f:
                    fall2025_data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(fall2025_data, list):
                        # If it's a flat array of courses (rice_courses_202610.json format)
                        self.fall2025_courses = fall2025_data
                        self.fall2025_metadata = {}
                        self.fall2025_stats = {}
                    else:
                        # If it has nested structure (fall2025_courses_*.json format)
                        self.fall2025_courses = fall2025_data.get('courses', [])
                        self.fall2025_metadata = fall2025_data.get('metadata', {})
                        self.fall2025_stats = fall2025_data.get('statistics', {})
                    
                    # Add department field to Fall 2025 courses for consistency
                    for course in self.fall2025_courses:
                        course['department'] = course.get('subject_code', '')
                    
                    print(f"Successfully loaded {len(self.fall2025_courses)} Fall 2025 courses")
            else:
                print("Warning: Fall 2025 course data file not found in any of the expected locations:")
                for path in possible_paths:
                    print(f"  - {os.path.abspath(path)}")
                # Fallback data if file doesn't exist
                self.fall2025_courses = []
                self.fall2025_metadata = {}
                self.fall2025_stats = {}
        except Exception as e:
            print(f"Error loading Fall 2025 course data: {e}")
            self.fall2025_courses = []
            self.fall2025_metadata = {}
            self.fall2025_stats = {}

    def load_program_requirements(self):
        """Load program requirements data from JSON file."""
        try:
            # Try multiple possible paths
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'selenium_rice_programs_with_content_20250715_193707.json'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw', 'selenium_rice_programs_with_content_20250715_193707.json'),
                os.path.join(os.getcwd(), 'data', 'raw', 'selenium_rice_programs_with_content_20250715_193707.json'),
                os.path.join(os.getcwd(), '..', 'data', 'raw', 'selenium_rice_programs_with_content_20250715_193707.json'),
                'data/raw/selenium_rice_programs_with_content_20250715_193707.json',
                '../data/raw/selenium_rice_programs_with_content_20250715_193707.json'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        self.program_requirements = json.load(f)
                    print(f"Successfully loaded {len(self.program_requirements)} program requirements")
                    return
            
            print("⚠️ Program requirements file not found")
            self.program_requirements = []
            
        except Exception as e:
            print(f"Error loading program requirements: {e}")
            self.program_requirements = []

    def load_comprehensive_courses(self):
        """Load comprehensive course data with prerequisites from JSON file."""
        try:
            # Try multiple possible paths
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'rice_all_courses.json'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw', 'rice_all_courses.json'),
                os.path.join(os.getcwd(), 'data', 'raw', 'rice_all_courses.json'),
                os.path.join(os.getcwd(), '..', 'data', 'raw', 'rice_all_courses.json'),
                'data/raw/rice_all_courses.json',
                '../data/raw/rice_all_courses.json'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        self.comprehensive_courses = json.load(f)
                    print(f"Successfully loaded {len(self.comprehensive_courses)} comprehensive courses")
                    
                    # Test: Check if COMP 182 is loaded
                    comp_182 = next((course for course in self.comprehensive_courses if course.get('course_code') == 'COMP 182'), None)
                    if comp_182:
                        print(f"✅ COMP 182 found in comprehensive dataset")
                        print(f"   Title: {comp_182.get('title')}")
                        print(f"   Prerequisites: {comp_182.get('prerequisites')}")
                    else:
                        print(f"❌ COMP 182 NOT found in comprehensive dataset")
                    
                    return
            
            print("⚠️ Comprehensive courses file not found")
            self.comprehensive_courses = []
            
        except Exception as e:
            print(f"Error loading comprehensive courses: {e}")
            self.comprehensive_courses = []

    def get_degree_requirements(self, query: str) -> str:
        """Get complete degree requirements for a specific program."""
        query_lower = query.lower()
        
        # Common degree keywords
        degree_keywords = ['bs', 'ba', 'bachelor', 'degree', 'requirements', 'course requirements']
        
        # Check if this is a degree requirements query
        is_degree_query = any(keyword in query_lower for keyword in degree_keywords)
        
        if not is_degree_query:
            return None
        
        # Extract degree type from query
        degree_type = None
        if 'bs' in query_lower or 'bachelor of science' in query_lower:
            degree_type = 'BS'
        elif 'ba' in query_lower or 'bachelor of arts' in query_lower:
            degree_type = 'BA'
        
        # Search for matching program in requirements data
        best_match = None
        best_score = 0
        
        # Safety check: ensure program_requirements is a list and not empty
        if not self.program_requirements or not isinstance(self.program_requirements, list):
            print(f"⚠️ Program requirements data is invalid or empty: {type(self.program_requirements)}")
            return None
        
        for program in self.program_requirements:
            # Safety check: ensure program is a dictionary
            if not isinstance(program, dict):
                print(f"⚠️ Invalid program data type: {type(program)}")
                continue
                
            if not program.get('has_requirements'):
                continue
                
            program_department = program.get('department', '').lower()
            program_type = program.get('program_type', '')
            program_name = program.get('program_name', '').lower()
            requirements_content = program.get('requirements_content', '')
            
            if not requirements_content:
                continue
            
            # Calculate match score based on how well the query matches the program
            score = 0
            
            # Check if degree type matches
            if degree_type and degree_type in program_type:
                score += 10
            
            # Check if any words in the query match the department or program name
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2:  # Only consider words longer than 2 characters
                    if word in program_department:
                        score += 5
                    if word in program_name:
                        score += 5
                    if word in program_type.lower():
                        score += 3
            
            # Check for exact phrase matches
            if any(phrase in query_lower for phrase in [program_department, program_name]):
                score += 15
            
            # If this is a better match than what we've found so far
            if score > best_score:
                best_score = score
                best_match = program
        
        # Only return a result if we found a reasonable match (score > 0)
        if best_match and best_score > 0:
            requirements_content = best_match.get('requirements_content', '')
            
            # Format the requirements content to be more readable
            formatted_content = self.format_degree_requirements(
                best_match.get('program_name', ''),
                best_match.get('program_type', ''),
                requirements_content
            )
            
            return formatted_content
        
        return None

    def format_degree_requirements(self, program_name: str, program_type: str, requirements_content: str) -> str:
        """Format degree requirements into a more readable structure."""
        
        # Extract key information from the requirements content
        lines = requirements_content.split('\n')
        
        # Find summary information
        summary_info = {}
        core_requirements = []
        elective_requirements = []
        additional_info = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Extract credit hours information
            if 'credit hours' in line.lower() and 'total' in line.lower():
                if 'major' in line.lower():
                    summary_info['major_credits'] = line
                elif 'degree' in line.lower():
                    summary_info['total_credits'] = line
            
            # Extract core requirements
            elif 'core requirements' in line.lower():
                current_section = 'core'
            elif 'elective requirements' in line.lower():
                current_section = 'elective'
            elif 'additional' in line.lower() and 'information' in line.lower():
                current_section = 'additional'
            elif current_section == 'core' and line and not line.startswith('*'):
                core_requirements.append(line)
            elif current_section == 'elective' and line and not line.startswith('*'):
                elective_requirements.append(line)
            elif current_section == 'additional' and line and not line.startswith('*'):
                additional_info.append(line)
        
        # Build formatted output
        formatted = f"# {program_name} ({program_type}) Requirements\n\n"
        
        # Summary section
        if summary_info:
            formatted += "## 📋 Summary\n"
            if 'major_credits' in summary_info:
                formatted += f"**{summary_info['major_credits']}**\n"
            if 'total_credits' in summary_info:
                formatted += f"**{summary_info['total_credits']}**\n"
            formatted += "\n"
        
        # Core requirements section
        if core_requirements:
            formatted += "## 🎯 Core Requirements\n\n"
            
            # Group requirements by category
            current_category = None
            for line in core_requirements:
                if ':' in line and not line.startswith('Select'):
                    current_category = line
                    formatted += f"### {current_category}\n"
                elif line.startswith('Select'):
                    formatted += f"**{line}**\n"
                elif line and not line.startswith('*'):
                    # Check if it's a course line (contains course code)
                    if any(char.isdigit() for char in line) and any(char.isalpha() for char in line):
                        # Format course line
                        parts = line.split()
                        if len(parts) >= 3:
                            course_code = parts[0]
                            course_name = ' '.join(parts[1:-1])
                            credits = parts[-1]
                            formatted += f"• **{course_code}** - {course_name} ({credits} credits)\n"
                        else:
                            formatted += f"• {line}\n"
                    else:
                        formatted += f"• {line}\n"
            formatted += "\n"
        
        # Elective requirements section
        if elective_requirements:
            formatted += "## 📚 Elective Requirements\n\n"
            for line in elective_requirements:
                if line.startswith('Select'):
                    formatted += f"**{line}**\n"
                elif line and not line.startswith('*'):
                    formatted += f"• {line}\n"
            formatted += "\n"
        
        # Additional information section
        if additional_info:
            formatted += "## ℹ️ Additional Information\n\n"
            for line in additional_info:
                if line.startswith('*'):
                    formatted += f"• {line[1:].strip()}\n"
                else:
                    formatted += f"• {line}\n"
        
        return formatted

    def validate_course_exists(self, course_code: str) -> bool:
        """Check if a course code exists in our dataset."""
        course_code = course_code.upper().strip()
        for course in self.all_courses:
            if course.get('course_code', '').upper() == course_code:
                return True
        return False
    
    def get_available_courses_by_department(self, department: str) -> List[str]:
        """Get list of available course codes for a specific department."""
        department = department.upper()
        available_courses = []
        for course in self.all_courses:
            if course.get('department', '').upper() == department:
                available_courses.append(course.get('course_code', ''))
        return available_courses

    def smart_search(self, query, limit=10):
        """Enhanced search with prerequisite detection and multiple strategies."""
        relevant_courses = []
        
        # Check if this is a prerequisite query - much more robust detection
        prerequisite_keywords = ['pre', 'req', 'requisite', 'prerequisite', 'prereq']
        is_prerequisite_query = any(keyword in query.lower() for keyword in prerequisite_keywords)
        
        if is_prerequisite_query:
            print(f"🔍 PREREQUISITE QUERY DETECTED: {query}")
            
            # Extract course code from query (e.g., "COMP 182", "MATH 101")
            import re
            course_code_match = re.search(r'([A-Z]{2,4})\s*(\d{3})', query.upper())
            
            if course_code_match:
                target_course_code = f"{course_code_match.group(1)} {course_code_match.group(2)}"
                print(f"🎯 Looking for prerequisites for: {target_course_code}")
                
                # DIRECT LOOKUP in comprehensive dataset
                if hasattr(self, 'comprehensive_courses') and self.comprehensive_courses:
                    found_course = None
                    for course in self.comprehensive_courses:
                        if course.get('course_code', '').upper() == target_course_code:
                            found_course = course
                            print(f"✅ FOUND COURSE: {course.get('course_code')} - {course.get('title')}")
                            break
                    
                    if found_course:
                        relevant_courses.append(found_course)
                        prerequisites = found_course.get('prerequisites', '')
                        print(f"📋 PREREQUISITES: {prerequisites}")
                        
                        # If prerequisites exist, also add those courses to context
                        if prerequisites:
                            prereq_codes = re.findall(r'([A-Z]{2,4})\s*(\d{3})', prerequisites.upper())
                            for dept, num in prereq_codes:
                                prereq_code = f"{dept} {num}"
                                for course in self.comprehensive_courses:
                                    if course.get('course_code', '').upper() == prereq_code:
                                        relevant_courses.append(course)
                                        print(f"📚 Added prerequisite course: {course.get('course_code')} - {course.get('title')}")
                                        break
                    else:
                        print(f"❌ Course {target_course_code} NOT FOUND in comprehensive dataset")
                        # Show available courses for debugging
                        comp_courses = [c for c in self.comprehensive_courses if c.get('department', '').upper() == course_code_match.group(1)]
                        print(f"🔍 Available {course_code_match.group(1)} courses: {[c.get('course_code') for c in comp_courses[:10]]}")
                else:
                    print("❌ Comprehensive courses dataset not loaded")
            
            print(f"📊 Final prerequisite search count: {len(relevant_courses)}")
            return relevant_courses
        
        # For non-prerequisite queries, use the original search logic
        query_lower = query.lower()
        relevant_courses = []
        
        # Check if query contains a course code pattern (e.g., "COMP 140", "MATH 101")
        import re
        course_code_match = re.search(r'([A-Z]{2,4})\s*(\d{3})', query.upper())
        
        if course_code_match:
            # Direct course code search
            dept = course_code_match.group(1)
            number = course_code_match.group(2)
            course_code = f"{dept} {number}"
            
            print(f"🔍 Looking for course: {course_code}")
            
            # Search in all courses
            for course in self.all_courses:
                if course.get('course_code', '').upper() == course_code.upper():
                    relevant_courses.append(course)
                    print(f"✅ Found course: {course.get('course_code')} - {course.get('title')}")
                    break
            
            # If not found in all_courses, try fall2025_courses
            if not relevant_courses:
                for course in self.fall2025_courses:
                    if course.get('course_code', '').upper() == course_code.upper():
                        relevant_courses.append(course)
                        print(f"✅ Found course in Fall 2025: {course.get('course_code')} - {course.get('title')}")
                        break
            
            if not relevant_courses:
                print(f"❌ Course {course_code} not found")
        else:
            # General keyword search
            for course in self.all_courses:
                course_code = course.get('course_code', '').lower()
                course_title = course.get('title', '').lower()
                course_desc = course.get('description', '').lower()
                department = course.get('department', '').lower()
                
                # Strategy 1: Direct keyword matching
                query_terms = query_lower.split()
                course_text = f"{course_code} {course_title} {course_desc} {department}"
                
                # Strategy 2: Department-specific matching for common queries
                if any(term in query_lower for term in ['comp', 'computer', 'programming', 'software']) and department == 'comp':
                    relevant_courses.append(course)
                    continue
                elif any(term in query_lower for term in ['math', 'calculus', 'statistics', 'algebra']) and department == 'math':
                    relevant_courses.append(course)
                    continue
                
                # Strategy 3: Keyword matching
                if any(term in course_text for term in query_terms):
                    relevant_courses.append(course)
                    continue
        
        # Remove duplicates and limit results
        seen_codes = set()
        unique_courses = []
        for course in relevant_courses:
            code = course.get('course_code', '')
            if code not in seen_codes:
                seen_codes.add(code)
                unique_courses.append(course)
        
        return unique_courses[:limit]

    def get_answer(self, question: str, selected_advisor: str = 'unified') -> str:
        """Get answer using OpenAI API with enhanced context."""
        try:
            # Enhanced search with prerequisite detection
            relevant_courses = self.smart_search(question)
            
            # Check if this is a prerequisite query
            prerequisite_keywords = ['pre', 'req', 'requisite', 'prerequisite', 'prereq']
            is_prerequisite_query = any(keyword in question.lower() for keyword in prerequisite_keywords)
            
            if is_prerequisite_query and relevant_courses:
                # Extract course code from question
                import re
                course_code_match = re.search(r'([A-Z]{2,4})\s*(\d{3})', question.upper())
                
                if course_code_match:
                    target_course_code = f"{course_code_match.group(1)} {course_code_match.group(2)}"
                    
                    # Find the target course in results
                    target_course = None
                    for course in relevant_courses:
                        if course.get('course_code', '').upper() == target_course_code:
                            target_course = course
                            break
                    
                    if target_course:
                        prerequisites = target_course.get('prerequisites', '')
                        course_title = target_course.get('title', '')
                        
                        if prerequisites:
                            return f"The prerequisites for {target_course_code} - {course_title} are: {prerequisites}"
                        else:
                            return f"{target_course_code} - {course_title} has no prerequisites listed."
                    else:
                        return f"I couldn't find {target_course_code} in the course database. Please check the course code and try again."
            
            # For non-prerequisite queries, use the existing logic
            context = self.format_context(relevant_courses)
            
            # Enhanced prompt for better responses
            prompt = f"""You are a helpful academic advisor at Rice University. Answer the student's question based on the provided course information.

Available course information:
{context}

Student question: {question}

Instructions:
- If the student is asking about a specific course (like "what is COMP 140"), provide detailed information about that course
- If asking about prerequisites, provide the exact prerequisite information from the course data
- If asking about course recommendations, suggest courses that match their interests
- Be specific and helpful
- If you don't have enough information, say so clearly
- Always mention course codes when discussing specific courses
- If a course is found, provide its title, description, and other relevant details

Answer:"""

            # Check if OpenAI client is available
            if not self.client or not self.openai_available:
                return "I'm sorry, but the AI assistant is currently unavailable. Please try again later or contact support if the issue persists."

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error in get_answer: {e}")
            return "I'm having trouble processing your request right now. Please try again."

    def format_context(self, relevant_courses):
        """Format course information for context."""
        if not relevant_courses:
            return "No relevant course information available."
        
        context_parts = []
        for course in relevant_courses[:10]:  # Limit to 10 courses
            context_parts.append(f"Course: {course.get('course_code', '')} - {course.get('title', '')}")
            if course.get('description'):
                desc = course.get('description', '')[:200]  # Truncate
                context_parts.append(f"Description: {desc}")
            if course.get('prerequisites'):
                context_parts.append(f"Prerequisites: {course.get('prerequisites')}")
            context_parts.append("")
        
        return "\n".join(context_parts)

# Initialize vector store globally to avoid rebuilding on each request
global_vector_store = None

def initialize_vector_store():
    """Initialize the vector store once."""
    global global_vector_store
    if VECTOR_STORE_AVAILABLE and global_vector_store is None:
        try:
            print("🔄 Initializing vector store...")
            global_vector_store = RiceVectorStore()
            global_vector_store.load_and_index_courses()
            print(f"✅ Vector store ready with {len(global_vector_store.documents)} documents")
        except Exception as e:
            print(f"⚠️ Vector store initialization failed: {e}")
            global_vector_store = None

# ================================================================
# FLASK API ENDPOINTS
# ================================================================

# Initialize the assistant
try:
    assistant = RiceCourseAssistant()
    print("✅ Assistant initialized successfully")
except Exception as e:
    print(f"⚠️ Assistant initialization failed: {e}")
    assistant = None

# Initialize vector store for Gunicorn
try:
    initialize_vector_store()
    print("✅ Vector store initialized successfully")
except Exception as e:
    print(f"⚠️ Vector store initialization failed: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Rice Course Assistant API is running',
        'version': '1.0.0'
    })

@app.route('/api/advisors', methods=['GET'])
def get_advisors():
    """Get list of available advisors."""
    advisors = {
        'unified': '🎓 Unified Academic Advisor'
    }
    
    return jsonify({
        'advisors': advisors,
        'default': 'unified'
    })

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Main endpoint for asking questions to the course assistant - old implementation for compatibility."""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({'error': 'Question is required'}), 400
        
        question = data['question']
        selected_advisor = data.get('advisor', 'unified')
        
        # Measure response time
        start_time = time.time()
        
        # Get answer from assistant
        answer = assistant.get_answer(question, selected_advisor)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return jsonify({
            'question': question,
            'answer': answer,
            'advisor': selected_advisor,
            'response_time': round(response_time, 2),
            'model': 'gpt-4o-mini'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """REST endpoint for chat messages with enhanced RAG pipeline"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        advisor = data.get('advisor', 'unified')
        user_profile = data.get('user_profile', {})
        test_mode = data.get('test_mode', False)  # New parameter for testing without OpenAI
        
        # Measure response time
        start_time = time.time()
        
        # Step 1: Check if this is a degree requirements query
        degree_requirements = assistant.get_degree_requirements(message)
        if degree_requirements:
            print(f"🎓 Detected degree requirements query: {message}")
            return jsonify({
                'message': message,
                'response': degree_requirements,
                'advisor': advisor,
                'search_results_count': 0,
                'response_time': round(time.time() - start_time, 2),
                'model': 'degree-requirements',
                'metadata': {
                    'degree_requirements_detected': True,
                    'query_type': 'degree_requirements'
                }
            })
        
        # Step 1.5: Check if this is a distribution requirements query
        distribution_keywords = ['distribution', 'distributions', 'distribution credits', 'distribution requirements', 'group i', 'group ii', 'group iii', 'distribution groups']
        message_lower = message.lower()
        is_distribution_query = any(keyword in message_lower for keyword in distribution_keywords)
        
        if is_distribution_query:
            print(f"📚 Detected distribution requirements query: {message}")
            distribution_response = """Rice University's distribution requirements are designed to give students a broad-based education across three key areas: humanities (Group I), social sciences (Group II), and natural sciences and engineering (Group III). These courses introduce students to different modes of inquiry, intellectual skills, and ways of thinking characteristic of each field. Group I courses develop critical thinking about history, culture, and the arts. Group II courses focus on understanding human behavior and social institutions through theoretical and empirical approaches. Group III emphasizes scientific reasoning, engineering design, and quantitative analysis to help students understand the natural world and its complexities. These courses are accessible to non-majors and foster the integration of knowledge across disciplines.

To fulfill the requirement, students must complete at least three distribution courses in each group, with a minimum of three credit hours per course. Each group must include courses from at least two different departments. Courses must be designated as distribution courses at the time of registration, and approved transfer courses may count if they meet credit and designation requirements. However, courses that focus on technical skills without academic analysis, independent research, internships, or practica do not qualify for distribution credit. The distribution system ensures that students gain a well-rounded education and the ability to approach problems from multiple perspectives.

To find out more, click this link: https://ga.rice.edu/undergraduate-students/academic-policies-procedures/graduation-requirements/#text"""
            
            return jsonify({
                'message': message,
                'response': distribution_response,
                'advisor': advisor,
                'search_results_count': 0,
                'response_time': round(time.time() - start_time, 2),
                'model': 'distribution-requirements',
                'metadata': {
                    'distribution_requirements_detected': True,
                    'query_type': 'distribution_requirements'
                }
            })
        
        # Step 2: Enhanced Vector search for relevant context
        if VECTOR_STORE_AVAILABLE and global_vector_store is not None:
            search_results = []
            
            # Check if query is about an instructor
            instructor_keywords = ['professor', 'prof', 'instructor', 'teacher', 'teaches', 'teaching', 'who teaches']
            is_instructor_query = any(keyword in message.lower() for keyword in instructor_keywords)
            
            # Check if query contains a course code pattern (e.g., "COMP 140", "MATH 101")
            import re
            course_code_match = re.search(r'([A-Z]{2,4})\s*(\d{3})', message.upper())
            
            # Check if this is asking about who teaches a specific course
            who_teaches_course = course_code_match and any(keyword in message.lower() for keyword in ['who teaches', 'who is teaching', 'instructor', 'professor', 'professors', 'teach'])
            
            if is_instructor_query and not course_code_match:
                # Pure instructor query (e.g., "what does Anjum Chida teach")
                print(f"👨‍🏫 Detected instructor query: {message}")
                
                # Extract instructor name from query
                instructor_name = None
                
                # Try to extract name after "who teaches" or similar patterns
                who_teaches_match = re.search(r'who\s+(?:teaches|is\s+teaching)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', message, re.IGNORECASE)
                if who_teaches_match:
                    instructor_name = who_teaches_match.group(1)
                
                # Try to extract name after "what does [name] teach"
                what_teaches_match = re.search(r'what\s+(?:does|do)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+teach', message, re.IGNORECASE)
                if what_teaches_match:
                    instructor_name = what_teaches_match.group(1)
                
                # Try to extract name from "what are all the courses that [name] teaches"
                all_courses_match = re.search(r'what\s+are\s+all\s+the\s+courses\s+that\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+teaches', message, re.IGNORECASE)
                if all_courses_match:
                    instructor_name = all_courses_match.group(1)
                
                # Try to extract name from "what does [name] teach"
                what_does_teach_match = re.search(r'what\s+does\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+teach', message, re.IGNORECASE)
                if what_does_teach_match:
                    instructor_name = what_does_teach_match.group(1)
                
                # Try to extract name from "what other courses are taught by [name]"
                other_courses_match = re.search(r'what\s+other\s+courses\s+are\s+taught\s+by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', message, re.IGNORECASE)
                if other_courses_match:
                    instructor_name = other_courses_match.group(1)
                
                # Try to extract name from "taught by [name]" pattern
                taught_by_match = re.search(r'taught\s+by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', message, re.IGNORECASE)
                if taught_by_match:
                    instructor_name = taught_by_match.group(1)
                
                # Try to extract capitalized names (likely instructor names) - more flexible pattern
                if not instructor_name:
                    # Look for two consecutive capitalized words
                    name_matches = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', message)
                    if name_matches:
                        # Filter out common words that aren't names
                        common_words = ['what', 'does', 'teach', 'teaches', 'teaching', 'professor', 'professors', 'instructor', 'instructors', 'who', 'are', 'all', 'the', 'courses', 'that']
                        for match in name_matches:
                            words = match.split()
                            if not any(word.lower() in common_words for word in words):
                                instructor_name = match
                                break
                
                if instructor_name:
                    print(f"👤 Extracted instructor name: {instructor_name}")
                    
                    # Search for courses by this instructor
                    matching_courses = []
                    instructor_lower = instructor_name.lower()
                    
                    for course in assistant.fall2025_courses:
                        instructors = course.get('instructors', [])
                        
                        # Handle different instructor formats
                        if isinstance(instructors, str):
                            instructor_list = [i.strip() for i in instructors.replace(';', ',').split(',')]
                        elif isinstance(instructors, list):
                            instructor_list = instructors
                        else:
                            instructor_list = []
                        
                        # Check if instructor name matches
                        for instructor in instructor_list:
                            instructor_clean = str(instructor).strip()
                            instructor_lower_clean = instructor_clean.lower()
                            
                            # Direct exact match
                            if instructor_lower == instructor_lower_clean:
                                matching_courses.append(course)
                                break
                            
                            # Handle "Last, First" format
                            if ',' in instructor_clean:
                                last_first = instructor_clean.split(',')
                                if len(last_first) >= 2:
                                    last_name = last_first[0].strip().lower()
                                    first_name = last_first[1].strip().lower()
                                    
                                    # Check for exact matches
                                    if (instructor_lower == last_name or 
                                        instructor_lower == first_name or
                                        instructor_lower == f"{first_name} {last_name}" or 
                                        instructor_lower == f"{last_name} {first_name}"):
                                        matching_courses.append(course)
                                        break
                    
                    if matching_courses:
                        # Create search results format for instructor courses
                        for course in matching_courses:
                            text_parts = []
                            text_parts.append(f"Course: {course.get('course_code', '')}")
                            text_parts.append(f"Title: {course.get('title', '')}")
                            text_parts.append(f"Department: {course.get('subject_code', '')}")
                            text_parts.append(f"Instructor: {', '.join(course.get('instructors', []))}")
                            text_parts.append(f"Meeting Time: {course.get('meeting_time', '')}")
                            text_parts.append(f"Credits: {course.get('credits', '')}")
                            
                            search_results.append({
                                'course_code': course.get('course_code', ''),
                                'title': course.get('title', ''),
                                'department': course.get('subject_code', ''),
                                'score': 1.0,  # Perfect match for instructor search
                                'text': " ".join(text_parts)
                            })
                        
                        print(f"✅ Found {len(matching_courses)} courses for {instructor_name}")
                    else:
                        print(f"❌ No courses found for {instructor_name}")
                        search_results = []
                else:
                    print(f"⚠️ Could not extract instructor name from query")
                    search_results = []
            
            elif who_teaches_course:
                # Course-specific instructor query (e.g., "Who teaches COMP 182")
                dept = course_code_match.group(1)
                number = course_code_match.group(2)
                course_code = f"{dept} {number}"
                
                print(f"👨‍🏫 Looking for instructor of {course_code}")
                
                # Search in Fall 2025 data for this course
                matching_courses = []
                for course in assistant.fall2025_courses:
                    if course.get('course_code', '').upper() == course_code.upper():
                        matching_courses.append(course)
                
                if matching_courses:
                    # Create search results format for course instructor
                    for course in matching_courses:
                        text_parts = []
                        text_parts.append(f"Course: {course.get('course_code', '')}")
                        text_parts.append(f"Title: {course.get('title', '')}")
                        text_parts.append(f"Department: {course.get('subject_code', '')}")
                        text_parts.append(f"Instructor: {', '.join(course.get('instructors', []))}")
                        text_parts.append(f"Meeting Time: {course.get('meeting_time', '')}")
                        text_parts.append(f"Credits: {course.get('credits', '')}")
                        text_parts.append(f"CRN: {course.get('crn', '')}")
                        text_parts.append(f"Section: {course.get('section', '')}")
                        
                        search_results.append({
                            'course_code': course.get('course_code', ''),
                            'title': course.get('title', ''),
                            'department': course.get('subject_code', ''),
                            'score': 1.0,  # Perfect match for instructor search
                            'text': " ".join(text_parts)
                        })
                    
                    print(f"✅ Found instructor information for {course_code}")
                else:
                    print(f"❌ No instructor information found for {course_code}")
                    search_results = []
            
            elif course_code_match:
                dept = course_code_match.group(1)
                number = course_code_match.group(2)
                course_code = f"{dept} {number}"
                
                print(f"🔍 Detected course code: {course_code}")
                
                # Check if this is asking about who teaches the course
                who_teaches_course = any(keyword in message.lower() for keyword in ['who teaches', 'who is teaching', 'instructor', 'professor', 'professors', 'teach'])
                
                if who_teaches_course:
                    print(f"👨‍🏫 Looking for instructor of {course_code}")
                    
                    # Search in Fall 2025 data for this course
                    matching_courses = []
                    for course in assistant.fall2025_courses:
                        if course.get('course_code', '').upper() == course_code.upper():
                            matching_courses.append(course)
                    
                    if matching_courses:
                        # Create search results format for course instructor
                        for course in matching_courses:
                            text_parts = []
                            text_parts.append(f"Course: {course.get('course_code', '')}")
                            text_parts.append(f"Title: {course.get('title', '')}")
                            text_parts.append(f"Department: {course.get('subject_code', '')}")
                            text_parts.append(f"Instructor: {', '.join(course.get('instructors', []))}")
                            text_parts.append(f"Meeting Time: {course.get('meeting_time', '')}")
                            text_parts.append(f"Credits: {course.get('credits', '')}")
                            text_parts.append(f"CRN: {course.get('crn', '')}")
                            text_parts.append(f"Section: {course.get('section', '')}")
                            
                            search_results.append({
                                'course_code': course.get('course_code', ''),
                                'title': course.get('title', ''),
                                'department': course.get('subject_code', ''),
                                'score': 1.0,  # Perfect match for instructor search
                                'text': " ".join(text_parts)
                            })
                        
                        print(f"✅ Found instructor information for {course_code}")
                    else:
                        print(f"❌ No instructor information found for {course_code}")
                        search_results = []
                else:
                    # Strategy 1: Direct course code search
                    exact_search = global_vector_store.search(course_code, k=10)
                    exact_matches = [r for r in exact_search if r['course_code'] == course_code]
                    
                    if exact_matches:
                        print(f"✅ Found {len(exact_matches)} exact matches for {course_code}")
                        search_results = exact_matches[:5]
                    else:
                        print(f"⚠️ No exact matches for {course_code}, trying enhanced search...")
                    
                    # Strategy 2: Search with course title keywords
                    enhanced_queries = [
                        f"Course: {course_code}",
                        f"{course_code} {dept}",
                        f"{dept} {number}",
                        course_code
                    ]
                    
                    for query in enhanced_queries:
                        results = global_vector_store.search(query, k=10)
                        exact_matches = [r for r in results if r['course_code'] == course_code]
                        if exact_matches:
                            print(f"✅ Found matches with query: '{query}'")
                            search_results = exact_matches[:5]
                            break
                    
                    # Strategy 3: Fallback to regular course data
                    if not search_results:
                        print(f"🔄 Trying fallback data for {course_code}")
                        
                        # Search in assistant's course data as final fallback
                        matching_courses = [
                            course for course in assistant.all_courses 
                            if course.get('course_code', '').upper() == course_code.upper()
                        ]
                        
                        if matching_courses:
                            print(f"✅ Found {len(matching_courses)} matches in fallback data")
                            
                            # Convert to search result format
                            for course in matching_courses[:5]:
                                # Create text similar to vector store format
                                text_parts = []
                                text_parts.append(f"Course: {course.get('course_code', '')}")
                                text_parts.append(f"Title: {course.get('title', '')}")
                                text_parts.append(f"Department: {course.get('department', '')}")
                                description = course.get('description', '')
                                if description:
                                    text_parts.append(f"Description: {description}")
                                
                                search_results.append({
                                    'course_code': course.get('course_code', ''),
                                    'title': course.get('title', ''),
                                    'department': course.get('department', ''),
                                    'score': 1.0,  # Perfect match for fallback
                                    'text': " ".join(text_parts)
                                })
                        else:
                            # Strategy 4: Department fallback (only if course-specific fallback fails)
                            dept_results = [r for r in exact_search if r['department'] == dept]
                            if dept_results:
                                print(f"🔄 Using department fallback for {dept}")
                                search_results = dept_results[:5]
                            else:
                                print(f"❌ No results found for {course_code}")
                                search_results = []
            else:
                # Regular semantic search for non-course-code queries
                search_results = global_vector_store.search(message, k=5)
            
            search_count = len(search_results)
            print(f"📊 Final search count: {search_count}")
            
        else:
            search_results = []
            search_count = 0
            print("❌ Vector store not available")
        
        # Step 2: Enhance query with user context
        enhanced_query = message
        if user_profile.get('major'):
            enhanced_query += f" | Student major: {user_profile['major']}"
        
        # Step 3: Get GPT response using vector results
        if search_results:
            # Format context from vector search
            context_parts = []
            for result in search_results:
                context_parts.append(f"Course: {result['course_code']} - {result['title']}")
                context_parts.append(f"Department: {result['department']}")
                if len(result['text']) > 300:
                    context_parts.append(f"Description: {result['text'][:300]}...")
                else:
                    context_parts.append(f"Description: {result['text']}")
                context_parts.append("")  # Add spacing
            
            context = "\n".join(context_parts)
            
            # Test mode: Return search results instead of calling OpenAI
            if test_mode:
                response = f"TEST MODE - Found {len(search_results)} courses:\n\n{context}"
                print(f"🧪 TEST MODE: Returning search results instead of calling OpenAI")
            else:
                # Check if this is a prerequisite query
                prerequisite_keywords = ['pre', 'req', 'requisite', 'prerequisite', 'prereq']
                is_prerequisite_query = any(keyword in message.lower() for keyword in prerequisite_keywords)
                
                if is_prerequisite_query:
                    # Use smart_search for prerequisite queries
                    response = assistant.get_answer(message, advisor)
                else:
                    # Use original logic for everything else
                    response = get_direct_gpt_response(enhanced_query, context, advisor)
        else:
            # Enhanced fallback - try to find course in regular data
            if course_code_match:
                dept = course_code_match.group(1)
                number = course_code_match.group(2)
                course_code = f"{dept} {number}"
                
                # Search in assistant's course data as final fallback
                matching_courses = [
                    course for course in assistant.all_courses 
                    if course.get('course_code', '').upper() == course_code.upper()
                ]
                
                if matching_courses:
                    course = matching_courses[0]
                    fallback_context = f"Course: {course.get('course_code')} - {course.get('title')}\n"
                    fallback_context += f"Department: {course.get('department')}\n"
                    fallback_context += f"Description: {course.get('description', 'No description available.')}"
                    print(f"✅ Found {course_code} in fallback data")
                else:
                    fallback_context = f"Course {course_code} not found in the database."
                    print(f"❌ {course_code} not found even in fallback data")
            else:
                fallback_context = "No specific course data available."
            
            # Test mode: Return fallback context instead of calling OpenAI
            if test_mode:
                response = f"TEST MODE - Fallback data:\n\n{fallback_context}"
                print(f"🧪 TEST MODE: Returning fallback data instead of calling OpenAI")
            else:
                # Check if this is a prerequisite query
                prerequisite_keywords = ['pre', 'req', 'requisite', 'prerequisite', 'prereq']
                is_prerequisite_query = any(keyword in message.lower() for keyword in prerequisite_keywords)
                
                if is_prerequisite_query:
                    # Use smart_search for prerequisite queries
                    response = assistant.get_answer(message, advisor)
                else:
                    # Use original logic for everything else
                    response = get_direct_gpt_response(enhanced_query, fallback_context, advisor)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return jsonify({
            'message': message,
            'response': response,
            'advisor': advisor,
            'search_results_count': search_count,
            'response_time': round(response_time, 2),
            'model': 'gpt-4o-mini' if not test_mode else 'test-mode',
            'metadata': {
                'vector_search_used': search_count > 0,
                'user_profile_used': bool(user_profile),
                'enhanced_query': enhanced_query != message,
                'course_code_detected': bool(course_code_match),
                'test_mode': test_mode
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/search', methods=['POST'])
def search_courses():
    """Enhanced vector search endpoint for testing with course code detection"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        k = data.get('k', 5)
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Step 1: Enhanced search logic (same as chat/message)
        search_results = []
        search_method = "none"
        
        if VECTOR_STORE_AVAILABLE and global_vector_store is not None:
            # Check if query contains a course code pattern (e.g., "COMP 140", "MATH 101")
            import re
            course_code_match = re.search(r'([A-Z]{2,4})\s*(\d{3})', query.upper())
            
            if course_code_match:
                dept = course_code_match.group(1)
                number = course_code_match.group(2)
                course_code = f"{dept} {number}"
                
                print(f"🔍 [SEARCH] Detected course code: {course_code}")
                
                # Strategy 1: Direct course code search
                exact_search = global_vector_store.search(course_code, k=k*2)
                exact_matches = [r for r in exact_search if r['course_code'] == course_code]
                
                if exact_matches:
                    print(f"✅ [SEARCH] Found {len(exact_matches)} exact matches for {course_code}")
                    search_results = exact_matches[:k]
                    search_method = "exact_vector_match"
                else:
                    print(f"⚠️ [SEARCH] No exact matches for {course_code}, trying enhanced search...")
                    
                    # Strategy 2: Search with course title keywords
                    enhanced_queries = [
                        f"Course: {course_code}",
                        f"{course_code} {dept}",
                        f"{dept} {number}",
                        course_code
                    ]
                    
                    for enhanced_query in enhanced_queries:
                        results = global_vector_store.search(enhanced_query, k=k*2)
                        exact_matches = [r for r in results if r['course_code'] == course_code]
                        if exact_matches:
                            print(f"✅ [SEARCH] Found matches with query: '{enhanced_query}'")
                            search_results = exact_matches[:k]
                            search_method = "enhanced_vector_match"
                            break
                    
                    # Strategy 3: Fallback to regular course data
                    if not search_results:
                        print(f"🔄 [SEARCH] Trying fallback data for {course_code}")
                        
                        # Search in assistant's course data as final fallback
                        matching_courses = [
                            course for course in assistant.all_courses 
                            if course.get('course_code', '').upper() == course_code.upper()
                        ]
                        
                        if matching_courses:
                            print(f"✅ [SEARCH] Found {len(matching_courses)} matches in fallback data")
                            search_method = "fallback_data"
                            
                            # Convert to search result format
                            for course in matching_courses[:k]:
                                # Create text similar to vector store format
                                text_parts = []
                                text_parts.append(f"Course: {course.get('course_code', '')}")
                                text_parts.append(f"Title: {course.get('title', '')}")
                                text_parts.append(f"Department: {course.get('department', '')}")
                                description = course.get('description', '')
                                if description:
                                    text_parts.append(f"Description: {description}")
                                
                                search_results.append({
                                    'course_code': course.get('course_code', ''),
                                    'title': course.get('title', ''),
                                    'department': course.get('department', ''),
                                    'score': 1.0,  # Perfect match for fallback
                                    'text': " ".join(text_parts)
                                })
                        else:
                            print(f"❌ [SEARCH] {course_code} not found even in fallback data")
            else:
                # Regular semantic search for non-course-code queries
                search_results = global_vector_store.search(query, k=k)
                search_method = "semantic_search"
                print(f"🔍 [SEARCH] Using semantic search for: '{query}'")
        else:
            print("❌ [SEARCH] Vector store not available")
            return jsonify({
                'error': 'Vector store not available or not initialized'
            }), 500
        
        print(f"📊 [SEARCH] Final search count: {len(search_results)} using {search_method}")
        
        # Format results for API response
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                'course_code': result['course_code'],
                'title': result['title'],
                'department': result['department'],
                'score': result['score'],
                'text_preview': result['text'][:200] + '...' if len(result['text']) > 200 else result['text']
            })
        
        return jsonify({
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results),
            'search_method': search_method,
            'course_code_detected': bool(re.search(r'([A-Z]{2,4})\s*(\d{3})', query.upper())),
            'search_metadata': {
                'total_documents': len(global_vector_store.documents) if global_vector_store else 0,
                'search_time': time.time(),
                'vector_store_available': VECTOR_STORE_AVAILABLE and global_vector_store is not None
            }
        })
        
    except Exception as e:
        print(f"❌ [SEARCH] Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/init', methods=['POST'])
def initialize_chat():
    """Initialize chat session and vector store"""
    try:
        if not VECTOR_STORE_AVAILABLE or global_vector_store is None:
            return jsonify({
                'error': 'Vector store not available or not initialized'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Chat system initialized',
            'documents_indexed': len(global_vector_store.documents),
            'vector_store_available': VECTOR_STORE_AVAILABLE
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/status', methods=['GET'])
def chat_system_status():
    """Get status of chat system components"""
    try:
        status = {
            'vector_store_support': VECTOR_STORE_AVAILABLE,
            'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
            'system_ready': VECTOR_STORE_AVAILABLE and bool(os.getenv('OPENAI_API_KEY'))
        }
        
        # Test vector store if available
        if VECTOR_STORE_AVAILABLE and global_vector_store is not None:
            status['vector_store_documents'] = len(global_vector_store.documents)
            status['vector_store_ready'] = True
        elif VECTOR_STORE_AVAILABLE:
            status['vector_store_ready'] = False
            status['vector_store_error'] = 'Vector store not initialized'
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get course data."""
    try:
        department = request.args.get('department')
        search = request.args.get('search')
        
        courses = assistant.all_courses
        
        # Filter by department if specified
        if department:
            courses = [course for course in courses if course.get('department') == department]
        
        # Filter by search term if specified
        if search:
            search_lower = search.lower()
            courses = [
                course for course in courses 
                if search_lower in f"{course.get('course_code', '')} {course.get('title', '')} {course.get('description', '')}".lower()
            ]
        
        return jsonify({
            'courses': courses[:50],  # Limit to 50 courses for performance
            'total': len(courses),
            'filters': {
                'department': department,
                'search': search
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/departments', methods=['GET'])
def get_departments():
    """Get list of departments."""
    try:
        departments = list(assistant.departments.keys())
        return jsonify({
            'departments': departments,
            'total': len(departments)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/search', methods=['GET'])
def search_catalog():
    """Advanced course catalog search with filters."""
    try:
        # Get search parameters
        search_query = request.args.get('search', '').lower()
        departments = request.args.getlist('departments')
        min_credits = request.args.get('min_credits', type=int)
        max_credits = request.args.get('max_credits', type=int)
        course_level = request.args.get('course_level')  # 100, 200, 300, 400, 500
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        course_type = request.args.get('course_type', 'all')  # 'all' or 'fall2025'
        
        # Select appropriate course dataset
        if course_type == 'fall2025':
            courses_to_search = assistant.fall2025_courses
        else:
            courses_to_search = assistant.all_courses
        
        # Start with all courses
        filtered_courses = []
        
        for course in courses_to_search:
            # Text search filter
            if search_query:
                searchable_text = f"{course.get('course_code', '')} {course.get('title', '')} {course.get('description', '')}".lower()
                if search_query not in searchable_text:
                    continue
            
            # Department filter
            if departments and course.get('department') not in departments:
                continue
            
            # Credit hours filter
            try:
                course_credits = int(course.get('credit_hours', course.get('credits', 0)))
                if min_credits and course_credits < min_credits:
                    continue
                if max_credits and course_credits > max_credits:
                    continue
            except (ValueError, TypeError):
                pass
            
            # Course level filter
            if course_level:
                course_code = course.get('course_code', '')
                course_num_match = re.search(r'(\d+)', course_code)
                if course_num_match:
                    course_num = int(course_num_match.group(1))
                    level_ranges = {
                        '100': (100, 199),
                        '200': (200, 299),
                        '300': (300, 399),
                        '400': (400, 499),
                        '500': (500, 999)
                    }
                    if course_level in level_ranges:
                        min_level, max_level = level_ranges[course_level]
                        if not (min_level <= course_num <= max_level):
                            continue
            
            filtered_courses.append(course)
        
        # Sort courses by department and course number
        def sort_key(course):
            dept = course.get('department', 'ZZZ')
            course_code = course.get('course_code', '')
            course_num_match = re.search(r'(\d+)', course_code)
            course_num = int(course_num_match.group(1)) if course_num_match else 999
            return (dept, course_num)
        
        filtered_courses.sort(key=sort_key)
        
        # Pagination
        total_courses = len(filtered_courses)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_courses = filtered_courses[start_idx:end_idx]
        
        return jsonify({
            'courses': paginated_courses,
            'total': total_courses,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_courses + per_page - 1) // per_page,
            'course_type': course_type,
            'filters': {
                'search': search_query,
                'departments': departments,
                'min_credits': min_credits,
                'max_credits': max_credits,
                'course_level': course_level
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/stats', methods=['GET'])
def get_catalog_stats():
    """Get catalog statistics."""
    try:
        course_type = request.args.get('course_type', 'all')
        
        # Select appropriate course dataset
        if course_type == 'fall2025':
            courses_to_analyze = assistant.fall2025_courses
        else:
            courses_to_analyze = assistant.all_courses
        
        # Calculate department statistics
        dept_stats = {}
        total_courses = 0
        credit_distribution = {}
        level_distribution = {'100': 0, '200': 0, '300': 0, '400': 0, '500+': 0}
        
        for course in courses_to_analyze:
            dept = course.get('department', 'Unknown')
            dept_stats[dept] = dept_stats.get(dept, 0) + 1
            total_courses += 1
            
            # Credit distribution
            try:
                credits = int(course.get('credit_hours', course.get('credits', 0)))
                credit_distribution[credits] = credit_distribution.get(credits, 0) + 1
            except (ValueError, TypeError):
                pass
            
            # Level distribution
            course_code = course.get('course_code', '')
            course_num_match = re.search(r'(\d+)', course_code)
            if course_num_match:
                course_num = int(course_num_match.group(1))
                if 100 <= course_num < 200:
                    level_distribution['100'] += 1
                elif 200 <= course_num < 300:
                    level_distribution['200'] += 1
                elif 300 <= course_num < 400:
                    level_distribution['300'] += 1
                elif 400 <= course_num < 500:
                    level_distribution['400'] += 1
                elif course_num >= 500:
                    level_distribution['500+'] += 1
        
        # Sort departments by course count
        sorted_depts = sorted(dept_stats.items(), key=lambda x: x[1], reverse=True)
        
        return jsonify({
            'total_courses': total_courses,
            'total_departments': len(dept_stats),
            'department_stats': dict(sorted_depts),
            'credit_distribution': credit_distribution,
            'level_distribution': level_distribution,
            'popular_departments': sorted_depts[:10],  # Top 10 departments
            'course_type': course_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fall2025/search', methods=['GET'])
def search_fall2025():
    """Search Fall 2025 courses specifically."""
    try:
        # Get search parameters
        search_query = request.args.get('search', '').lower()
        departments = request.args.getlist('departments')
        min_credits = request.args.get('min_credits', type=int)
        max_credits = request.args.get('max_credits', type=int)
        course_level = request.args.get('course_level')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Use Fall 2025 courses
        courses_to_search = assistant.fall2025_courses
        
        # Start with all courses
        filtered_courses = []
        
        for course in courses_to_search:
            # Text search filter
            if search_query:
                searchable_text = f"{course.get('course_code', '')} {course.get('title', '')}".lower()
                if search_query not in searchable_text:
                    continue
            
            # Department filter
            if departments and course.get('department') not in departments:
                continue
            
            # Credit hours filter
            try:
                course_credits = int(course.get('credits', 0))
                if min_credits and course_credits < min_credits:
                    continue
                if max_credits and course_credits > max_credits:
                    continue
            except (ValueError, TypeError):
                pass
            
            # Course level filter
            if course_level:
                course_code = course.get('course_code', '')
                course_num_match = re.search(r'(\d+)', course_code)
                if course_num_match:
                    course_num = int(course_num_match.group(1))
                    level_ranges = {
                        '100': (100, 199),
                        '200': (200, 299),
                        '300': (300, 399),
                        '400': (400, 499),
                        '500': (500, 999)
                    }
                    if course_level in level_ranges:
                        min_level, max_level = level_ranges[course_level]
                        if not (min_level <= course_num <= max_level):
                            continue
            
            filtered_courses.append(course)
        
        # Sort courses by department and course number
        def sort_key(course):
            dept = course.get('department', 'ZZZ')
            course_code = course.get('course_code', '')
            course_num_match = re.search(r'(\d+)', course_code)
            course_num = int(course_num_match.group(1)) if course_num_match else 999
            return (dept, course_num)
        
        filtered_courses.sort(key=sort_key)
        
        # Pagination
        total_courses = len(filtered_courses)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_courses = filtered_courses[start_idx:end_idx]
        
        return jsonify({
            'courses': paginated_courses,
            'total': total_courses,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_courses + per_page - 1) // per_page,
            'course_type': 'fall2025',
            'filters': {
                'search': search_query,
                'departments': departments,
                'min_credits': min_credits,
                'max_credits': max_credits,
                'course_level': course_level
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fall2025/stats', methods=['GET'])
def get_fall2025_stats():
    """Get Fall 2025 course statistics."""
    try:
        # Use Fall 2025 courses
        courses_to_analyze = assistant.fall2025_courses
        
        # Calculate department statistics
        dept_stats = {}
        total_courses = 0
        credit_distribution = {}
        level_distribution = {'100': 0, '200': 0, '300': 0, '400': 0, '500+': 0}
        
        for course in courses_to_analyze:
            dept = course.get('department', 'Unknown')
            dept_stats[dept] = dept_stats.get(dept, 0) + 1
            total_courses += 1
            
            # Credit distribution
            try:
                credits = int(course.get('credits', 0))
                credit_distribution[credits] = credit_distribution.get(credits, 0) + 1
            except (ValueError, TypeError):
                pass
            
            # Level distribution
            course_code = course.get('course_code', '')
            course_num_match = re.search(r'(\d+)', course_code)
            if course_num_match:
                course_num = int(course_num_match.group(1))
                if 100 <= course_num < 200:
                    level_distribution['100'] += 1
                elif 200 <= course_num < 300:
                    level_distribution['200'] += 1
                elif 300 <= course_num < 400:
                    level_distribution['300'] += 1
                elif 400 <= course_num < 500:
                    level_distribution['400'] += 1
                elif course_num >= 500:
                    level_distribution['500+'] += 1
        
        # Sort departments by course count
        sorted_depts = sorted(dept_stats.items(), key=lambda x: x[1], reverse=True)
        
        return jsonify({
            'total_courses': total_courses,
            'total_departments': len(dept_stats),
            'department_stats': dict(sorted_depts),
            'credit_distribution': credit_distribution,
            'level_distribution': level_distribution,
            'popular_departments': sorted_depts[:10],  # Top 10 departments
            'course_type': 'fall2025',
            'metadata': assistant.fall2025_metadata,
            'statistics': assistant.fall2025_stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instructor/search', methods=['GET'])
def search_instructor():
    """Search for courses by instructor name"""
    try:
        instructor_name = request.args.get('name', '').strip()
        
        if not instructor_name:
            return jsonify({'error': 'Instructor name is required'}), 400
        
        # Search in Fall 2025 data which has instructor information
        matching_courses = []
        instructor_lower = instructor_name.lower()
        
        for course in assistant.fall2025_courses:
            instructors = course.get('instructors', [])
            
            # Handle different instructor formats
            if isinstance(instructors, str):
                instructor_list = [i.strip() for i in instructors.replace(';', ',').split(',')]
            elif isinstance(instructors, list):
                instructor_list = instructors
            else:
                instructor_list = []
            
            # Check if instructor name matches
            for instructor in instructor_list:
                instructor_clean = str(instructor).strip()
                instructor_lower_clean = instructor_clean.lower()
                
                # Direct exact match
                if instructor_lower == instructor_lower_clean:
                    matching_courses.append(course)
                    break
                
                # Handle "Last, First" format
                if ',' in instructor_clean:
                    last_first = instructor_clean.split(',')
                    if len(last_first) >= 2:
                        last_name = last_first[0].strip().lower()
                        first_name = last_first[1].strip().lower()
                        
                        # Check for exact matches
                        if (instructor_lower == last_name or 
                            instructor_lower == first_name or
                            instructor_lower == f"{first_name} {last_name}" or 
                            instructor_lower == f"{last_name} {first_name}"):
                            matching_courses.append(course)
                            break
                        
                        # Check for partial matches (more restrictive)
                        if ((instructor_lower in last_name and len(instructor_lower) >= 3) or 
                            (instructor_lower in first_name and len(instructor_lower) >= 3)):
                            matching_courses.append(course)
                            break
        
        # Sort by course code for consistency
        matching_courses.sort(key=lambda x: x.get('course_code', ''))
        
        return jsonify({
            'instructor': instructor_name,
            'courses': matching_courses,
            'total_courses': len(matching_courses)
        })
        
    except Exception as e:
        print(f"Error in instructor search: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/course/instructor/<course_code>', methods=['GET'])
def get_course_instructor(course_code):
    """Get instructor information for a specific course"""
    try:
        # Search in Fall 2025 data
        matching_courses = []
        
        for course in assistant.fall2025_courses:
            if course.get('course_code', '').upper() == course_code.upper():
                matching_courses.append(course)
        
        if matching_courses:
            # Return the first match (most relevant)
            course = matching_courses[0]
            return jsonify({
                'course_code': course.get('course_code', ''),
                'title': course.get('title', ''),
                'instructors': course.get('instructors', []),
                'meeting_time': course.get('meeting_time', ''),
                'credits': course.get('credits', ''),
                'department': course.get('subject_code', ''),
                'crn': course.get('crn', ''),
                'section': course.get('section', ''),
                'part_of_term': course.get('part_of_term', ''),
                'distribution_group': course.get('distribution_group', ''),
                'course_url': course.get('course_url', '')
            })
        else:
            return jsonify({'error': f'Course {course_code} not found in Fall 2025 schedule'}), 404
            
    except Exception as e:
        print(f"Error getting course instructor: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize vector store
    initialize_vector_store()
    
    print("\n" + "="*60)
    print("🦉 RICE COURSE ASSISTANT BACKEND")
    print("="*60)
    print(f"🔧 Chat Mode: ✅ REST API")
    print(f"🔍 Vector Store Support: {'✅ Available' if VECTOR_STORE_AVAILABLE else '❌ Not Available'}")
    print(f"🤖 OpenAI API: {'✅ Configured' if os.getenv('OPENAI_API_KEY') else '❌ Not Configured'}")
    # Get port from environment variable (for Render) or default to 8000
    port = int(os.getenv('PORT', 8000))
    print(f"🌐 Server starting on: http://0.0.0.0:{port}")
    print(f"💬 Chat endpoints: /api/chat/*")
    print(f"🔌 REST Chat endpoint: POST /api/chat/message")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)