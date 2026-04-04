#!/usr/bin/env python3
"""
Rice University Course Assistant v4.0 - Standalone Application
==============================================================

This is a standalone Streamlit application that provides fast, accurate
course recommendations and academic planning for Rice University students.
The app is designed to be lightweight and efficient while maintaining
high-quality recommendations.

Key Features:
- Direct access to organized Rice course data
- Hierarchical course selection interface (Department -> Courses)
- Balanced schedule generation with prerequisite checking
- GPT-4 powered natural language query processing
- Real-time course search and filtering
- Prerequisite validation and course availability checking

Architecture:
- Loads organized course data from data/organized/rice_organized_data.json
- Uses FastGPTWrapper for efficient OpenAI API interactions
- Implements balanced scheduling algorithms for realistic course recommendations
- Provides both chat interface and schedule builder functionality

Data Sources:
- Rice course catalog data (organized by department)
- Distribution requirement information
- Program and degree requirement data
- Course prerequisite and credit hour information

Author: Rice Course Assistant Team
Last Updated: 2024-07-15
Version: 4.0
"""

import streamlit as st
import json
import os
import re
import openai
from typing import List, Dict, Tuple
from dataclasses import dataclass
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ================================================================
# CORE DATA STRUCTURES AND CONFIGURATION
# ================================================================

@dataclass
class FastGPTWrapper:
    """
    A fast, efficient wrapper for OpenAI GPT API interactions.
    
    This class handles all GPT-4 communication with optimized prompts
    and response formatting for course-related queries.
    
    Attributes:
        client: OpenAI client instance for API calls
    """
    client: openai.OpenAI
    
    def format_context_smart(self, relevant_data: List[Dict], context_type: str, user_question: str) -> str:
        """
        Format course data into optimized context for GPT processing.
        
        This method creates context-specific prompts that help GPT understand
        the type of query and provide more accurate responses.
        
        Args:
            relevant_data (List[Dict]): List of relevant course data
            context_type (str): Type of context (cs_related, math_related, etc.)
            user_question (str): The original user question
            
        Returns:
            str: Formatted context string for GPT processing
        """
        if not relevant_data:
            return "No relevant course data found."
        
        # Create context-specific formatting
        context_intro = {
            'cs_related': "Here are relevant Computer Science and related courses from Rice University:",
            'math_related': "Here are relevant Mathematics and related courses from Rice University:",
            'engineering': "Here are relevant Engineering courses from Rice University:",
            'distribution': "Here are relevant Distribution courses from Rice University:",
            'general': "Here are relevant courses from Rice University:"
        }
        
        intro = context_intro.get(context_type, "Here are relevant courses from Rice University:")
        
        # Format course data efficiently
        formatted_courses = []
        for course in relevant_data[:15]:  # Limit to prevent context overflow
            course_info = f"Course: {course.get('course_code', 'N/A')}"
            if course.get('title'):
                course_info += f" - {course.get('title')}"
            if course.get('credit_hours'):
                course_info += f" ({course.get('credit_hours')} credits)"
            if course.get('description'):
                # Truncate long descriptions
                desc = course.get('description', '')
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                course_info += f"\nDescription: {desc}"
            if course.get('prerequisites'):
                course_info += f"\nPrerequisites: {course.get('prerequisites')}"
            
            formatted_courses.append(course_info)
        
        return f"{intro}\n\n" + "\n\n".join(formatted_courses)
    
    def get_fast_response(self, user_question: str, context: str, context_type: str, selected_advisor: str = None) -> str:
        """
        Get a fast, accurate response from GPT-4 using specialized advisor prompts.
        
        This method uses advisor-specific system prompts to ensure GPT provides
        accurate, helpful responses about Rice University courses from the perspective
        of different academic advisors.
        
        Args:
            user_question (str): The user's question
            context (str): Formatted course context
            context_type (str): Type of context for prompt optimization
            selected_advisor (str): User-selected advisor type
            
        Returns:
            str: GPT-4 response with course recommendations and information
        """
        # Specialized advisor system prompts
        advisor_prompts = {
            'general': """You are a Rice University General Academic Advisor.
            Use ONLY the provided Rice course data. You can help with courses from any department.
            
            Instructions:
            1. Answer the user's question completely using the provided course data
            2. After your answer, suggest the most appropriate specialized advisor for follow-up
            3. Be specific about which advisor would be best (e.g., "For more detailed chemistry guidance, I recommend switching to the Chemistry Advisor")
            
            Available specialized advisors:
            - Computer Science Advisor (COMP, MATH, STAT, ELEC courses)
            - Mathematics Advisor (MATH, STAT, CAAM courses)
            - Chemistry Advisor (CHEM courses and pre-med requirements)
            - Physics Advisor (PHYS courses and applied physics)
            - Business Advisor (MGMT, ECON, business courses)
            - Music Advisor (MUSI courses from Shepherd School)
            - Engineering Advisor (all engineering departments)
            - Biosciences Advisor (BIOC, BIOS, life sciences)
            - Humanities Advisor (ENGL, HIST, PHIL, languages)
            - Social Sciences Advisor (POLI, PSYC, ANTH, SOCI)
            - Architecture Advisor (ARCH courses and design)
            - Pre-Medical Advisor (medical school requirements)
            - Pre-Law Advisor (law school preparation)
            
            Provide specific course codes, prerequisites, and credit hours from the data.
            Never mention courses not in the provided data.""",
            
            'computer_science': """You are a Rice University Computer Science Academic Advisor.
            Use ONLY the provided Rice course data. Rice uses 'COMP' (not 'CS') for computer science courses.
            Key courses: COMP 140 (intro programming), COMP 182 (algorithms), COMP 215 (program design).
            Focus on COMP, MATH, STAT, and ELEC courses. Provide specific course codes, prerequisites, and credit hours.""",
            
            'mathematics': """You are a Rice University Mathematics Academic Advisor.
            Use ONLY the provided Rice course data. Focus on MATH, STAT, and CAAM courses.
            Key courses: MATH 101/102 (calculus), MATH 211/212 (advanced calculus), STAT 305/310.
            Help with pure math, applied math, statistics, and computational math. Provide specific course codes and prerequisites.""",
            
            'chemistry': """You are a Rice University Chemistry Academic Advisor.
            Use ONLY the provided Rice course data. Focus on CHEM courses and related sciences.
            Key courses: CHEM 121/123 (general chemistry), CHEM 211/212 (organic chemistry).
            Help with chemistry coursework, pre-med requirements, and research opportunities. Provide specific course codes and prerequisites.""",
            
            'physics': """You are a Rice University Physics Academic Advisor.
            Use ONLY the provided Rice course data. Focus on PHYS courses and related math.
            Key courses: PHYS 101/102 (mechanics/E&M), PHYS 201/202 (modern physics).
            Help with physics coursework, astronomy, and applied physics. Provide specific course codes and prerequisites.""",
            
            'business': """You are a Rice University Business Academic Advisor.
            Use ONLY the provided Rice course data. Focus on MGMT, ECON, and business-related courses.
            Key courses: ECON 100 (intro economics), MGMT courses for business skills.
            Help with business coursework, entrepreneurship, and career preparation. Provide specific course codes and prerequisites.""",
            
            'music': """You are a Rice University Music Academic Advisor from the Shepherd School of Music.
            Use ONLY the provided Rice course data. Focus on MUSI courses and performance.
            Key courses: MUSI theory, performance, and composition courses.
            Help with music coursework, performance requirements, and music career preparation. Provide specific course codes and prerequisites.""",
            
            'engineering': """You are a Rice University Engineering Academic Advisor.
            Use ONLY the provided Rice course data. Focus on engineering departments (COMP, ELEC, MECH, CIVE, BIOE, etc.).
            Key courses: foundational math, physics, and department-specific engineering courses.
            Help with engineering coursework, design projects, and technical careers. Provide specific course codes and prerequisites.""",
            
            'biosciences': """You are a Rice University Biosciences Academic Advisor.
            Use ONLY the provided Rice course data. Focus on BIOC, BIOS, and related life sciences.
            Key courses: BIOC 201 (molecular biology), BIOS courses, and related chemistry/physics.
            Help with biology coursework, pre-med requirements, and research opportunities. Provide specific course codes and prerequisites.""",
            
            'humanities': """You are a Rice University Humanities Academic Advisor.
            Use ONLY the provided Rice course data. Focus on ENGL, HIST, PHIL, language courses, and liberal arts.
            Key courses: foundational writing, literature, philosophy, and cultural studies.
            Help with humanities coursework, critical thinking, and communication skills. Provide specific course codes and prerequisites.""",
            
            'social_sciences': """You are a Rice University Social Sciences Academic Advisor.
            Use ONLY the provided Rice course data. Focus on POLI, PSYC, ANTH, SOCI, and related social sciences.
            Key courses: POLI 200 (intro politics), PSYC 101 (intro psychology), ANTH courses.
            Help with social science coursework, research methods, and social policy. Provide specific course codes and prerequisites.""",
            
            'architecture': """You are a Rice University Architecture Academic Advisor.
            Use ONLY the provided Rice course data. Focus on ARCH courses and design.
            Key courses: ARCH design studios, theory, and technical courses.
            Help with architecture coursework, design projects, and career preparation. Provide specific course codes and prerequisites.""",
            
            'pre_med': """You are a Rice University Pre-Medical Academic Advisor.
            Use ONLY the provided Rice course data. Focus on pre-med requirements: CHEM, BIOS, PHYS, MATH.
            Key courses: CHEM 121/123, BIOS 201, PHYS 101/102, MATH 101/102.
            Help with pre-medical coursework, MCAT preparation, and medical school requirements. Provide specific course codes and prerequisites.""",
            
            'pre_law': """You are a Rice University Pre-Law Academic Advisor.
            Use ONLY the provided Rice course data. Focus on courses that develop critical thinking, writing, and analytical skills.
            Key courses: ENGL, HIST, PHIL, POLI courses that build argumentation and writing skills.
            Help with pre-law coursework, LSAT preparation, and law school preparation. Provide specific course codes and prerequisites."""
        }
        
        # Use selected advisor or fall back to context-based selection
        if selected_advisor and selected_advisor in advisor_prompts:
            system_prompt = advisor_prompts[selected_advisor]
        else:
            # Legacy context-based selection for backward compatibility
            legacy_mapping = {
                'cs_related': 'computer_science',
                'math_related': 'mathematics',
                'engineering': 'engineering',
                'distribution': 'general',
                'general': 'general'
            }
            advisor_key = legacy_mapping.get(context_type, 'general')
            system_prompt = advisor_prompts[advisor_key]
        
        try:
            # Make API call with optimized parameters
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_question}"}
                ],
                max_tokens=1000,  # Increased due to GPT-4.1 Nano's larger context window
                temperature=0.1,  # Low temperature for consistent, factual responses
                timeout=30
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error getting response: {e}. Please try again."

# ================================================================
# MAIN APPLICATION CLASS
# ================================================================

class RiceCourseAssistantV4:
    """
    Main application class for the Rice Course Assistant.
    
    This class handles all core functionality including:
    - Course data loading and organization
    - Smart search and filtering
    - Schedule generation and optimization
    - GPT integration for natural language queries
    - Prerequisite parsing and validation
    """
    
    def __init__(self):
        """
        Initialize the Rice Course Assistant.
        
        Sets up OpenAI client and loads organized course data from JSON files.
        """
        self.setup_openai()
        self.load_organized_data()
        
    def setup_openai(self):
        """
        Setup OpenAI client for GPT-4 API access.
        
        Loads API key from environment variables and initializes the client
        with the FastGPTWrapper for efficient interactions.
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            st.error("❌ OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
            st.stop()
        
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.gpt_wrapper = FastGPTWrapper(self.client)
        
    def load_organized_data(self):
        """
        Load the organized course data structure from JSON files.
        
        This method loads the preprocessed course data that's organized by
        department for efficient searching and filtering. The data includes:
        - Course information by department
        - Program requirements by school
        - Distribution group classifications
        - Quick lookup indexes for fast searching
        """
        try:
            with open('data/organized/rice_organized_data.json', 'r') as f:
                self.organized_data = json.load(f)
                
            # Extract main data structures
            self.departments = self.organized_data['departments']
            self.programs_by_school = self.organized_data['programs_by_school']
            self.distribution_groups = self.organized_data['distribution_groups']
            self.quick_indexes = self.organized_data['quick_indexes']
            self.metadata = self.organized_data['metadata']
            
            st.success(f"✅ Fast assistant loaded: {self.metadata['total_courses']} courses ready")
            
        except FileNotFoundError:
            st.error("❌ Organized data not found. Please run organize_data.py first.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error loading organized data: {e}")
            st.stop()
    
    def smart_search(self, query: str) -> Tuple[List[Dict], str]:
        """
        Intelligent search through course data based on query content.
        
        This method analyzes the user's query to determine intent and searches
        only relevant departments, making responses faster and more accurate.
        
        Key features:
        - Intent detection (CS, Math, Engineering, Distribution, etc.)
        - Department-specific searching
        - Level-based filtering (freshman, advanced, etc.)
        - Relevance scoring and ranking
        
        Args:
            query (str): User's search query
            
        Returns:
            Tuple[List[Dict], str]: List of relevant courses and context type
        """
        query_lower = query.lower()
        relevant_depts = []
        
        # Smart intent detection based on keywords
        # This allows the system to search only relevant departments
        
        # CS-related queries
        if any(word in query_lower for word in ['comp', 'computer', 'programming', 'coding', 'software', 'algorithm', 'cs']):
            relevant_depts.extend(['COMP', 'MATH', 'STAT'])
            context_type = 'cs_related'
        
        # Math-related queries
        elif any(word in query_lower for word in ['math', 'calculus', 'statistics', 'linear algebra', 'differential']):
            relevant_depts.extend(['MATH', 'STAT', 'CAAM'])
            context_type = 'math_related'
        
        # Engineering-related queries
        elif any(word in query_lower for word in ['engineering', 'elec', 'mech', 'civil', 'bioe']):
            relevant_depts.extend(['COMP', 'ELEC', 'MECH', 'CIVIL', 'BIOE'])
            context_type = 'engineering'
        
        # Distribution requirement queries
        elif any(word in query_lower for word in ['distribution', 'requirement', 'group i', 'group ii']):
            all_dist_courses = []
            for group_data in self.distribution_groups.values():
                all_dist_courses.extend(group_data['courses'])
            return all_dist_courses[:20], 'distribution'
        
        # General queries (search core departments)
        else:
            relevant_depts = ['COMP', 'MATH', 'PHYS', 'HIST', 'ENGL']
            context_type = 'general'
        
        # Get courses from relevant departments
        courses = []
        for dept in relevant_depts:
            if dept in self.departments:
                dept_courses = self.departments[dept]['courses']
                
                # Level-based filtering
                if any(word in query_lower for word in ['freshman', 'intro', 'beginning', 'first year']):
                    dept_courses = [c for c in dept_courses if c.get('course_number', '999')[0] in '12']
                elif any(word in query_lower for word in ['advanced', 'upper', 'senior']):
                    dept_courses = [c for c in dept_courses if c.get('course_number', '0')[0] in '345']
                
                courses.extend(dept_courses)
        
        # Sort by relevance using custom scoring
        def relevance_score(course):
            """
            Calculate relevance score for a course based on query content.
            
            Args:
                course (Dict): Course data dictionary
                
            Returns:
                int: Relevance score (higher = more relevant)
            """
            score = 0
            title = course.get('title', '').lower()
            desc = course.get('description', '').lower()
            
            # Keyword matching in title and description
            query_words = query_lower.split()
            for word in query_words:
                if word in title:
                    score += 3  # Title matches are more important
                if word in desc:
                    score += 1  # Description matches are less important
            
            # Freshman-friendly scoring
            if any(word in query_lower for word in ['freshman', 'intro', 'beginning']):
                if course.get('course_number', '999')[0] in '12':
                    score += 2
            
            return score
        
        courses.sort(key=relevance_score, reverse=True)
        return courses[:20], context_type
    
    def get_answer(self, user_question: str, selected_advisor: str = None) -> str:
        """
        Get a comprehensive answer to user's question using GPT-4.
        
        This method combines smart search with GPT-4 processing to provide
        accurate, contextual responses about Rice University courses from
        the perspective of a selected academic advisor.
        
        Args:
            user_question (str): The user's question
            selected_advisor (str): The selected advisor type (e.g., 'computer_science', 'chemistry')
            
        Returns:
            str: Comprehensive answer with course recommendations
        """
        # Search for relevant data
        relevant_data, context_type = self.smart_search(user_question)
        
        # Format context for GPT processing
        context_str = self.gpt_wrapper.format_context_smart(relevant_data, context_type, user_question)
        
        # Get GPT response with selected advisor
        response = self.gpt_wrapper.get_fast_response(user_question, context_str, context_type, selected_advisor)
        
        return response

    def parse_prerequisites(self, prereq_text: str) -> List[str]:
        """
        Parse prerequisite text to extract course codes.
        
        This method uses regex to find course codes in prerequisite
        descriptions, handling various formats used in course catalogs.
        
        Args:
            prereq_text (str): Raw prerequisite text from course data
            
        Returns:
            List[str]: List of course codes that are prerequisites
        """
        if not prereq_text or prereq_text.strip() == 'None':
            return []
        
        # Extract course codes using regex pattern
        # Matches patterns like "COMP 140", "MATH 101", etc.
        course_codes = re.findall(r'\b[A-Z]{2,4}\s*\d{3}\b', prereq_text.upper())
        return course_codes
    
    def get_advisor_specific_schedule_guidelines(self, advisor_type: str) -> Dict:
        """
        Get advisor-specific scheduling guidelines and constraints.
        
        This method provides detailed guidelines for each advisor type to ensure
        that schedule recommendations align with the advisor's area of expertise
        and the student's academic goals.
        
        Args:
            advisor_type (str): The type of advisor (e.g., 'computer_science', 'chemistry')
            
        Returns:
            Dict: Comprehensive scheduling guidelines for the advisor
        """
        
        guidelines = {
            'general': {
                'priority_departments': ['COMP', 'MATH', 'PHYS', 'CHEM', 'ENGL', 'HIST'],
                'max_courses_per_dept': 2,
                'recommended_credit_range': (12, 18),
                'difficulty_balance': 'moderate',
                'sequence_priorities': ['prerequisites', 'major_core', 'distribution', 'electives'],
                'special_considerations': ['Balanced across multiple departments', 'Foundation courses first']
            },
            'computer_science': {
                'priority_departments': ['COMP', 'MATH', 'STAT', 'ELEC'],
                'max_courses_per_dept': 3,  # Allow more CS courses
                'recommended_credit_range': (15, 18),
                'difficulty_balance': 'high',  # CS students can handle more difficulty
                'sequence_priorities': ['COMP core', 'MATH requirements', 'STAT foundations', 'technical electives'],
                'required_sequences': {
                    'freshman': ['COMP 140', 'MATH 101', 'MATH 102'],
                    'sophomore': ['COMP 182', 'COMP 215', 'MATH 211'],
                    'junior': ['COMP 280', 'COMP 330', 'STAT 305'],
                    'senior': ['COMP 400-level', 'Capstone courses']
                },
                'special_considerations': [
                    'Programming courses need time for practice',
                    'Math is crucial for CS success',
                    'Balance theory with practical courses'
                ]
            },
            'mathematics': {
                'priority_departments': ['MATH', 'STAT', 'CAAM', 'COMP', 'PHYS'],
                'max_courses_per_dept': 3,
                'recommended_credit_range': (15, 18),
                'difficulty_balance': 'high',
                'sequence_priorities': ['MATH core', 'STAT foundations', 'Applied math', 'Theoretical courses'],
                'required_sequences': {
                    'freshman': ['MATH 101', 'MATH 102', 'MATH 211'],
                    'sophomore': ['MATH 212', 'MATH 355', 'STAT 305'],
                    'junior': ['MATH 400-level', 'Advanced topics'],
                    'senior': ['Research', 'Capstone']
                },
                'special_considerations': [
                    'Sequential nature of math courses',
                    'Strong foundation before advanced topics',
                    'Balance pure and applied mathematics'
                ]
            },
            'chemistry': {
                'priority_departments': ['CHEM', 'MATH', 'PHYS', 'BIOC'],
                'max_courses_per_dept': 3,
                'recommended_credit_range': (15, 18),
                'difficulty_balance': 'high',
                'sequence_priorities': ['CHEM core', 'Lab requirements', 'Supporting sciences', 'Specialization'],
                'required_sequences': {
                    'freshman': ['CHEM 121', 'CHEM 123', 'MATH 101'],
                    'sophomore': ['CHEM 211', 'CHEM 212', 'PHYS 101'],
                    'junior': ['CHEM 300-level', 'Advanced lab'],
                    'senior': ['Research', 'Capstone']
                },
                'special_considerations': [
                    'Lab courses require significant time',
                    'Chemistry builds on previous knowledge',
                    'Balance lecture and laboratory work'
                ]
            },
            'physics': {
                'priority_departments': ['PHYS', 'MATH', 'CAAM', 'COMP'],
                'max_courses_per_dept': 3,
                'recommended_credit_range': (15, 18),
                'difficulty_balance': 'very_high',
                'sequence_priorities': ['PHYS core', 'MATH requirements', 'Computational physics', 'Specialization'],
                'required_sequences': {
                    'freshman': ['PHYS 101', 'PHYS 102', 'MATH 101', 'MATH 102'],
                    'sophomore': ['PHYS 201', 'PHYS 202', 'MATH 211', 'MATH 212'],
                    'junior': ['PHYS 300-level', 'Advanced math'],
                    'senior': ['Research', 'Advanced physics']
                },
                'special_considerations': [
                    'Heavy mathematical requirements',
                    'Conceptual difficulty requires time',
                    'Balance theory and experimental work'
                ]
            },
            'business': {
                'priority_departments': ['MGMT', 'ECON', 'STAT', 'MATH'],
                'max_courses_per_dept': 2,
                'recommended_credit_range': (12, 16),
                'difficulty_balance': 'moderate',
                'sequence_priorities': ['Business foundations', 'Economics', 'Quantitative skills', 'Specialization'],
                'required_sequences': {
                    'freshman': ['ECON 100', 'MATH 101', 'ENGL 103'],
                    'sophomore': ['ECON 212', 'STAT 305', 'MGMT courses'],
                    'junior': ['Advanced business', 'Internship prep'],
                    'senior': ['Capstone', 'Advanced specialization']
                },
                'special_considerations': [
                    'Practical application focus',
                    'Communication skills important',
                    'Balance quantitative and qualitative'
                ]
            },
            'pre_med': {
                'priority_departments': ['CHEM', 'BIOC', 'PHYS', 'MATH'],
                'max_courses_per_dept': 3,
                'recommended_credit_range': (15, 18),
                'difficulty_balance': 'very_high',
                'sequence_priorities': ['Pre-med requirements', 'MCAT prep', 'Research experience', 'Clinical exposure'],
                'required_sequences': {
                    'freshman': ['CHEM 121', 'CHEM 123', 'MATH 101'],
                    'sophomore': ['CHEM 211', 'CHEM 212', 'BIOC 201'],
                    'junior': ['PHYS 101', 'PHYS 102', 'Advanced sciences'],
                    'senior': ['MCAT prep', 'Research', 'Clinical experience']
                },
                'special_considerations': [
                    'GPA is crucial for medical school',
                    'MCAT preparation timing',
                    'Research experience valuable',
                    'Balance science load carefully'
                ]
            },
            'engineering': {
                'priority_departments': ['COMP', 'ELEC', 'MECH', 'MATH', 'PHYS'],
                'max_courses_per_dept': 3,
                'recommended_credit_range': (15, 18),
                'difficulty_balance': 'high',
                'sequence_priorities': ['Engineering fundamentals', 'Math/science foundation', 'Design courses', 'Specialization'],
                'required_sequences': {
                    'freshman': ['MATH 101', 'MATH 102', 'PHYS 101', 'Intro engineering'],
                    'sophomore': ['MATH 211', 'PHYS 102', 'Core engineering'],
                    'junior': ['Advanced engineering', 'Design projects'],
                    'senior': ['Capstone design', 'Specialization']
                },
                'special_considerations': [
                    'ABET accreditation requirements',
                    'Design project timing',
                    'Balance theory and practical application'
                ]
            },
            'humanities': {
                'priority_departments': ['ENGL', 'HIST', 'PHIL', 'RELI'],
                'max_courses_per_dept': 3,
                'recommended_credit_range': (12, 16),
                'difficulty_balance': 'moderate',
                'sequence_priorities': ['Writing skills', 'Critical thinking', 'Cultural literacy', 'Specialization'],
                'required_sequences': {
                    'freshman': ['ENGL 103', 'HIST survey', 'Language'],
                    'sophomore': ['Advanced writing', 'Literature', 'Philosophy'],
                    'junior': ['Major concentration', 'Research methods'],
                    'senior': ['Capstone', 'Advanced seminars']
                },
                'special_considerations': [
                    'Writing intensive courses need time',
                    'Reading load varies significantly',
                    'Balance breadth and depth'
                ]
            }
        }
        
        return guidelines.get(advisor_type, guidelines['general'])
    
    def build_advisor_optimized_schedule(self, completed_courses: List[str], 
                                       advisor_type: str = 'general',
                                       target_credits: int = 15,
                                       student_level: str = None) -> Dict:
        """
        Build an optimized schedule using advisor-specific guidelines.
        
        This method creates a schedule that follows the selected advisor's
        expertise and recommendations for course selection, sequencing,
        and workload balance.
        
        Args:
            completed_courses (List[str]): List of completed course codes
            advisor_type (str): Type of advisor for specialized guidance
            target_credits (int): Target number of credits
            student_level (str): Student level
            
        Returns:
            Dict: Optimized schedule with advisor-specific recommendations
        """
        
        # Get advisor-specific guidelines
        guidelines = self.get_advisor_specific_schedule_guidelines(advisor_type)
        
        # Determine student level
        if student_level is None:
            student_level = self.classify_student_level(completed_courses)
        
        # Get available courses based on prerequisites
        available_courses = self.get_available_courses(completed_courses)
        
        # Filter courses based on advisor priorities
        priority_courses = self.filter_courses_by_advisor_priority(
            available_courses, guidelines, student_level
        )
        
        # Build optimized schedule
        schedule = self.optimize_course_selection(
            priority_courses, guidelines, target_credits, student_level
        )
        
        # Add advisor-specific recommendations
        schedule['advisor_recommendations'] = self.generate_advisor_recommendations(
            schedule, guidelines, advisor_type, student_level
        )
        
        return schedule
    
    def classify_student_level(self, completed_courses: List[str]) -> str:
        """
        Classify student level based on completed courses.
        
        Args:
            completed_courses (List[str]): List of completed course codes
            
        Returns:
            str: Student level classification
        """
        course_count = len(completed_courses)
        
        if course_count < 8:
            return 'freshman'
        elif course_count < 16:
            return 'sophomore' 
        elif course_count < 24:
            return 'junior'
        else:
            return 'senior'
    
    def get_available_courses(self, completed_courses: List[str]) -> List[Dict]:
        """
        Get courses available to take based on completed prerequisites.
        
        Args:
            completed_courses (List[str]): List of completed course codes
            
        Returns:
            List[Dict]: List of available courses with metadata
        """
        available_courses = []
        
        for dept_code, dept_data in self.departments.items():
            for course in dept_data.get('courses', []):
                course_code = course.get('course_code', '')
                
                # Skip already completed courses
                if course_code in completed_courses:
                    continue
                
                # Check prerequisites
                if self.check_prerequisites_met(course, completed_courses):
                    # Add metadata for optimization
                    course_with_meta = course.copy()
                    course_with_meta['department'] = dept_code
                    course_with_meta['difficulty_score'] = self.calculate_difficulty_score(course)
                    course_with_meta['career_relevance'] = self.calculate_career_relevance(course)
                    available_courses.append(course_with_meta)
        
        return available_courses
    
    def filter_courses_by_advisor_priority(self, courses: List[Dict], 
                                         guidelines: Dict, 
                                         student_level: str) -> List[Dict]:
        """
        Filter and prioritize courses based on advisor guidelines.
        
        Args:
            courses (List[Dict]): Available courses
            guidelines (Dict): Advisor guidelines
            student_level (str): Student classification
            
        Returns:
            List[Dict]: Filtered and prioritized courses
        """
        priority_depts = guidelines['priority_departments']
        required_sequences = guidelines.get('required_sequences', {})
        
        # Filter courses by priority departments and appropriate starting courses
        filtered_courses = [
            course for course in courses 
            if course.get('department') in priority_depts
            and self.is_appropriate_starting_course(course, student_level)
        ]
        
        # Add priority scores
        for course in filtered_courses:
            course['priority_score'] = self.calculate_priority_score(
                course, guidelines, student_level, required_sequences
            )
        
        # Sort by priority score (highest first)
        filtered_courses.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return filtered_courses
    
    def is_appropriate_starting_course(self, course: Dict, student_level: str) -> bool:
        """
        Check if a course is appropriate as a starting course for the student level.
        
        Args:
            course (Dict): Course to check
            student_level (str): Student level
            
        Returns:
            bool: True if course is appropriate
        """
        course_code = course.get('course_code', '')
        
        # Inappropriate starting courses
        inappropriate_starters = {
            'PHYS 100': 'Should start with PHYS 101 or PHYS 124 (honors)',
            'MATH 100': 'Should start with MATH 101 or MATH 102',
            'COMP 100': 'Should start with COMP 140',
            'CHEM 100': 'Should start with CHEM 121'
        }
        
        if course_code in inappropriate_starters:
            return False
        
        # For freshmen, prioritize proper sequence starters
        if student_level == 'freshman':
            proper_starters = {
                'PHYS 101', 'PHYS 124',  # Physics starters
                'MATH 101', 'MATH 102',  # Math starters
                'COMP 140',              # CS starter
                'CHEM 121',              # Chemistry starter
                'ENGL 103',              # English starter
                'HIST 100'               # History starter
            }
            
            # If it's a physics course, must be a proper starter
            if course_code.startswith('PHYS') and course_code not in proper_starters:
                return False
        
        return True
    
    def calculate_priority_score(self, course: Dict, guidelines: Dict, 
                               student_level: str, required_sequences: Dict) -> int:
        """
        Calculate priority score for a course based on advisor guidelines.
        
        Args:
            course (Dict): Course data
            guidelines (Dict): Advisor guidelines
            student_level (str): Student level
            required_sequences (Dict): Required course sequences
            
        Returns:
            int: Priority score (higher = more important)
        """
        score = 0
        course_code = course.get('course_code', '')
        dept = course.get('department', '')
        
        # Check if course is in required sequence for student level
        if student_level in required_sequences:
            if course_code in required_sequences[student_level]:
                score += 20
        
        # Department priority
        priority_depts = guidelines['priority_departments']
        if dept in priority_depts:
            score += 10 - priority_depts.index(dept)  # Earlier in list = higher priority
        
        # Course level appropriateness
        import re
        course_num_match = re.search(r'(\d+)', course_code)
        if course_num_match:
            course_num = int(course_num_match.group(1))
            level_scores = {
                'freshman': {100: 5, 200: 2, 300: 0, 400: -5},
                'sophomore': {100: 2, 200: 5, 300: 3, 400: 0},
                'junior': {100: 0, 200: 2, 300: 5, 400: 3},
                'senior': {100: -2, 200: 0, 300: 3, 400: 5}
            }
            
            level_hundred = (course_num // 100) * 100
            if student_level in level_scores and level_hundred in level_scores[student_level]:
                score += level_scores[student_level][level_hundred]
        
        # Boost for appropriate starting courses
        if student_level == 'freshman':
            proper_starters = {
                'PHYS 101', 'PHYS 124',  # Physics starters
                'MATH 101', 'MATH 102',  # Math starters
                'COMP 140',              # CS starter
                'CHEM 121',              # Chemistry starter
                'ENGL 103',              # English starter
                'HIST 100'               # History starter
            }
            
            if course_code in proper_starters:
                score += 15  # High boost for proper starting courses
        
        return score
    
    def optimize_course_selection(self, priority_courses: List[Dict], 
                                guidelines: Dict, target_credits: int, 
                                student_level: str) -> Dict:
        """
        Select optimal courses for the schedule based on constraints.
        
        Args:
            priority_courses (List[Dict]): Prioritized course list
            guidelines (Dict): Advisor guidelines
            target_credits (int): Target number of credits
            student_level (str): Student level
            
        Returns:
            Dict: Optimized schedule
        """
        selected_courses = []
        total_credits = 0
        dept_counts = {}
        
        max_per_dept = 1  # Enforce strict limit of 1 course per department
        credit_range = guidelines['recommended_credit_range']
        
        for course in priority_courses:
            # Check credit limits
            course_credits = self.parse_credit_hours(course.get('credit_hours', '3'))
            if total_credits + course_credits > credit_range[1]:
                continue
                
            # Check department limits - only 1 course per department allowed
            dept = course.get('department', '')
            if dept_counts.get(dept, 0) >= max_per_dept:
                continue
            
            # Check for sequential course conflicts
            if self.has_sequential_conflict(course, selected_courses):
                continue
                
            # Add course to schedule
            selected_courses.append(course)
            total_credits += course_credits
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
            
            # Stop if we have enough courses or credits
            if len(selected_courses) >= 5 or total_credits >= target_credits:
                break
        
        return {
            'courses': selected_courses,
            'total_credits': total_credits,
            'departments_used': list(dept_counts.keys()),
            'dept_distribution': dept_counts,
            'student_level': student_level,
            'guidelines_followed': guidelines
        }
    
    def has_sequential_conflict(self, course: Dict, selected_courses: List[Dict]) -> bool:
        """
        Check if a course conflicts with already selected courses (sequential/prerequisite conflicts).
        
        Args:
            course (Dict): Course to check
            selected_courses (List[Dict]): Already selected courses
            
        Returns:
            bool: True if there's a conflict
        """
        course_code = course.get('course_code', '')
        
        # Define known sequential course chains
        sequential_chains = {
            # Math sequences
            'MATH 101': ['MATH 102', 'MATH 211', 'MATH 212'],
            'MATH 102': ['MATH 211', 'MATH 212'],
            'MATH 211': ['MATH 212'],
            
            # Computer Science sequences
            'COMP 140': ['COMP 182', 'COMP 215'],
            'COMP 182': ['COMP 215'],
            
            # Physics sequences
            'PHYS 101': ['PHYS 102', 'PHYS 201', 'PHYS 202'],
            'PHYS 102': ['PHYS 201', 'PHYS 202'],
            'PHYS 124': ['PHYS 125', 'PHYS 201', 'PHYS 202'],
            'PHYS 125': ['PHYS 201', 'PHYS 202'],
            'PHYS 201': ['PHYS 202'],
            
            # Chemistry sequences
            'CHEM 121': ['CHEM 122', 'CHEM 211', 'CHEM 212'],
            'CHEM 122': ['CHEM 211', 'CHEM 212'],
            'CHEM 211': ['CHEM 212']
        }
        
        selected_codes = [c.get('course_code', '') for c in selected_courses]
        
        # Check if current course is in a chain where a later course is already selected
        for selected_code in selected_codes:
            if course_code in sequential_chains.get(selected_code, []):
                return True  # Can't take prerequisite with its follow-up
        
        # Check if current course has a follow-up that's already selected
        follow_ups = sequential_chains.get(course_code, [])
        for follow_up in follow_ups:
            if follow_up in selected_codes:
                return True  # Can't take course with its follow-up
        
        return False
    
    def generate_advisor_recommendations(self, schedule: Dict, guidelines: Dict, 
                                       advisor_type: str, student_level: str) -> List[str]:
        """
        Generate advisor-specific recommendations for the schedule.
        
        Args:
            schedule (Dict): Generated schedule
            guidelines (Dict): Advisor guidelines
            advisor_type (str): Type of advisor
            student_level (str): Student level
            
        Returns:
            List[str]: List of advisor recommendations
        """
        recommendations = []
        
        # Check if schedule meets advisor guidelines
        if schedule['total_credits'] < guidelines['recommended_credit_range'][0]:
            recommendations.append(f"Consider adding more credits to reach the recommended {guidelines['recommended_credit_range'][0]}-{guidelines['recommended_credit_range'][1]} range")
        
        # Check department balance
        if len(schedule['departments_used']) < 3:
            recommendations.append("Consider adding courses from different departments for a more balanced education")
        
        # Add department limit explanation
        recommendations.append("📋 Schedule Policy: Maximum 1 course per department to ensure breadth of learning")
        
        # Add advisor-specific recommendations
        special_considerations = guidelines.get('special_considerations', [])
        if special_considerations:
            recommendations.append(f"💡 {advisor_type.replace('_', ' ').title()} Advisor Notes:")
            recommendations.extend([f"• {consideration}" for consideration in special_considerations])
        
        return recommendations
    
    def parse_credit_hours(self, credit_hours_str: str) -> int:
        """
        Parse credit hours from various formats into an integer.
        
        Args:
            credit_hours_str (str): Credit hours string (e.g., "3", "1 TO 4", "3-4")
            
        Returns:
            int: Parsed credit hours as integer
        """
        if not credit_hours_str:
            return 3  # Default
        
        # Convert to string if it's not already
        credit_str = str(credit_hours_str).strip().upper()
        
        # Handle simple integer cases
        if credit_str.isdigit():
            return int(credit_str)
        
        # Handle range formats
        import re
        
        # Pattern for "1 TO 4", "3 TO 6", etc.
        to_pattern = r'(\d+(?:\.\d+)?)\s*TO\s*(\d+(?:\.\d+)?)'
        to_match = re.search(to_pattern, credit_str)
        if to_match:
            min_credits = float(to_match.group(1))
            max_credits = float(to_match.group(2))
            # Return the maximum for planning purposes
            return int(max_credits)
        
        # Pattern for "1-4", "3-6", etc.
        dash_pattern = r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)'
        dash_match = re.search(dash_pattern, credit_str)
        if dash_match:
            min_credits = float(dash_match.group(1))
            max_credits = float(dash_match.group(2))
            # Return the maximum for planning purposes
            return int(max_credits)
        
        # Extract first number found
        number_pattern = r'(\d+(?:\.\d+)?)'
        number_match = re.search(number_pattern, credit_str)
        if number_match:
            return int(float(number_match.group(1)))
        
        # Default fallback
        return 3
    
    def format_restrictions_text(self, restrictions_text: str) -> str:
        """
        Format restrictions text by adding proper spacing between level types.
        
        Args:
            restrictions_text (str): Raw restrictions text
            
        Returns:
            str: Formatted restrictions text with proper spacing
        """
        if not restrictions_text:
            return ""
        
        # Common patterns that need spacing
        patterns_to_fix = [
            ('UndergraduateUndergraduate', 'Undergraduate Undergraduate'),
            ('ProfessionalVisiting', 'Professional Visiting'),
            ('VisitingUndergraduate', 'Visiting Undergraduate'),
            ('UndergraduateProfessional', 'Undergraduate Professional'),
            ('GraduateUndergraduate', 'Graduate Undergraduate'),
            ('UndergraduateGraduate', 'Undergraduate Graduate'),
            ('ProfessionalGraduate', 'Professional Graduate'),
            ('GraduateProfessional', 'Graduate Professional'),
            ('VisitingGraduate', 'Visiting Graduate'),
            ('GraduateVisiting', 'Graduate Visiting'),
            ('ProfessionalUndergraduate', 'Professional Undergraduate'),
            ('UndergraduateVisiting', 'Undergraduate Visiting'),
        ]
        
        formatted_text = restrictions_text
        
        # Apply all pattern fixes
        for pattern, replacement in patterns_to_fix:
            formatted_text = formatted_text.replace(pattern, replacement)
        
        return formatted_text
    
    def check_prerequisites_met(self, course: Dict, completed_courses: List[str]) -> bool:
        """
        Check if prerequisites are met for a course.
        
        Args:
            course (Dict): Course data
            completed_courses (List[str]): List of completed courses
            
        Returns:
            bool: True if prerequisites are met
        """
        prereq_text = course.get('prerequisites', '')
        if not prereq_text or prereq_text.strip() in ['None', 'N/A', '']:
            return True
        
        # Simple prerequisite parsing (can be enhanced)
        import re
        required_courses = re.findall(r'\b[A-Z]{2,4}\s*\d{3}\b', prereq_text.upper())
        
        return all(req in completed_courses for req in required_courses)
    
    def calculate_difficulty_score(self, course: Dict) -> float:
        """
        Calculate difficulty score for a course.
        
        Args:
            course (Dict): Course data
            
        Returns:
            float: Difficulty score (0.0 to 1.0)
        """
        # Simple heuristic based on course number
        course_code = course.get('course_code', '')
        import re
        course_num_match = re.search(r'(\d+)', course_code)
        if course_num_match:
            course_num = int(course_num_match.group(1))
            return min(course_num / 500.0, 1.0)  # Normalize to 0-1
        return 0.5  # Default moderate difficulty
    
    def calculate_career_relevance(self, course: Dict) -> float:
        """
        Calculate career relevance score for a course.
        
        Args:
            course (Dict): Course data
            
        Returns:
            float: Career relevance score (0.0 to 1.0)
        """
        # Simple heuristic - can be enhanced with actual career data
        dept = course.get('department', '')
        
        # Core departments tend to be more career-relevant
        if dept in ['COMP', 'MATH', 'PHYS', 'CHEM', 'MGMT', 'ECON']:
            return 0.8
        elif dept in ['ENGL', 'HIST', 'PHIL']:
            return 0.6
        else:
            return 0.4

# ================================================================
# STREAMLIT USER INTERFACE
# ================================================================

def main():
    """
    Main application function that creates the Streamlit interface.
    
    This function sets up the page configuration, creates the interface
    with tabs for different functionalities, and handles user interactions.
    """
    
    # Page configuration
    st.set_page_config(
        page_title="🦉 Rice Course Assistant v4.0",
        page_icon="🦉",
        layout="wide"
    )
    
    # Custom CSS for beautiful Rice University themed design
    # Using official Rice colors: Rice Blue (#002469) and Rice Gray (#5E6062)
    st.markdown("""
    <style>
        /* Import Rice-inspired fonts */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lato:wght@300;400;600;700&display=swap');
        
        /* Main app background with Rice theme */
        .main > div {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            min-height: 100vh;
        }
        
        /* Rice branding header */
        .rice-branding {
            background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%);
            color: white;
            padding: 2rem;
            border-radius: 20px;
            margin: 2rem 0;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,36,105,0.3);
            font-family: 'Lato', sans-serif;
        }
        
        /* Rice owl animation */
        .owl-icon {
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        /* Rice-themed stats cards */
        .stats-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 2rem;
            border-radius: 20px;
            margin: 1.5rem 0;
            border-left: 6px solid #002469;
            box-shadow: 0 8px 25px rgba(0,36,105,0.15);
            font-family: 'Lato', sans-serif;
        }
        
        /* Rice-themed buttons */
        .rice-button {
            background: linear-gradient(135deg, #002469 0%, #1a4b8c 100%);
            color: white;
            padding: 0.8rem 2rem;
            border: none;
            border-radius: 25px;
            font-weight: 600;
            font-family: 'Lato', sans-serif;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,36,105,0.3);
        }
        
        /* Course cards with Rice styling */
        .course-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            border-left: 5px solid #002469;
            box-shadow: 0 6px 20px rgba(0,36,105,0.15);
            font-family: 'Lato', sans-serif;
        }
        
        /* Feature highlights */
        .feature-highlight {
            background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            border-left: 5px solid #ffa726;
            box-shadow: 0 4px 12px rgba(255,167,38,0.2);
            font-family: 'Lato', sans-serif;
        }
        
        /* Rice success messages */
        .rice-success {
            background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
            color: #2e7d32;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #4caf50;
            margin: 1rem 0;
            font-family: 'Lato', sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Rice University themed header with owl mascot
    st.markdown("""
    <div class="rice-branding">
        <div class="owl-icon" style="font-size: 3.5rem; margin-bottom: 1rem;">🦉</div>
        <h1 style="color: white; margin-bottom: 0.5rem; font-family: 'Playfair Display', serif;">Rice Course Assistant v4.0</h1>
        <p style="color: #e8f4f8; margin-bottom: 1rem; font-family: 'Lato', sans-serif;">Fast & Accurate - Optimized for Speed and Quality</p>
        <div style="font-size: 1.1rem; font-style: italic; color: #e8f4f8; font-family: 'Playfair Display', serif;">"Unconventional Wisdom" • Est. 1912</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Rice-themed welcome message
    st.markdown("""
    <div class="feature-highlight">
        <h3 style="color: #002469; margin-bottom: 1rem;">⚡ High-Performance Academic Assistant</h3>
        <p style="margin-bottom: 0.5rem;"><strong>Lightning Fast:</strong> Optimized for speed with GPT-4 accuracy</p>
        <p style="margin-bottom: 0.5rem;"><strong>Smart Prompting:</strong> Few-shot examples for consistent quality</p>
        <p style="margin-bottom: 0;"><strong>Comprehensive:</strong> Course chat and schedule building in one place</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize assistant (cached for performance)
    if 'assistant' not in st.session_state:
        st.session_state.assistant = RiceCourseAssistantV4()
    
    assistant = st.session_state.assistant
    
    # Create main interface tabs
    tab1, tab2, tab3 = st.tabs(["💬 Course Chat", "📅 Schedule Builder", "🔍 Discover Courses"])
    
    # ================================================================
    # SIDEBAR INFORMATION AND CONTROLS
    # ================================================================
    
    with st.sidebar:
        st.markdown("""
        <div class="rice-branding" style="padding: 1.5rem; margin-bottom: 2rem;">
            <div class="owl-icon" style="font-size: 2.5rem; margin-bottom: 0.5rem;">🦉</div>
            <h2 style="color: white; margin-bottom: 0.5rem; font-family: 'Playfair Display', serif;">Rice Assistant</h2>
            <p style="color: #e8f4f8; margin-bottom: 0; font-family: 'Lato', sans-serif;">Your Academic Guide</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Advisor Selection
        st.markdown("""
        <div class="stats-card">
            <h3 style="color: #002469; margin-bottom: 1rem;">🎓 Choose Your Advisor</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Advisor options with emojis and descriptions
        advisor_options = {
            'general': '🎓 General Academic Advisor',
            'computer_science': '💻 Computer Science Advisor',
            'mathematics': '🔢 Mathematics Advisor',
            'chemistry': '🧪 Chemistry Advisor',
            'physics': '⚛️ Physics Advisor',
            'business': '📊 Business Advisor',
            'music': '🎵 Music Advisor (Shepherd School)',
            'engineering': '🔧 Engineering Advisor',
            'biosciences': '🧬 Biosciences Advisor',
            'humanities': '📚 Humanities Advisor',
            'social_sciences': '🌍 Social Sciences Advisor',
            'architecture': '🏗️ Architecture Advisor',
            'pre_med': '⚕️ Pre-Medical Advisor',
            'pre_law': '⚖️ Pre-Law Advisor'
        }
        
        # Create advisor descriptions
        advisor_descriptions = {
            'general': 'Helps with courses from any department',
            'computer_science': 'COMP, MATH, STAT, ELEC courses',
            'mathematics': 'MATH, STAT, CAAM courses',
            'chemistry': 'CHEM courses and pre-med requirements',
            'physics': 'PHYS courses and applied physics',
            'business': 'MGMT, ECON, business courses',
            'music': 'MUSI courses and performance',
            'engineering': 'All engineering departments',
            'biosciences': 'BIOC, BIOS, life sciences',
            'humanities': 'ENGL, HIST, PHIL, languages',
            'social_sciences': 'POLI, PSYC, ANTH, SOCI',
            'architecture': 'ARCH courses and design',
            'pre_med': 'Medical school requirements',
            'pre_law': 'Law school preparation'
        }
        
        # Initialize selected advisor in session state
        if 'selected_advisor' not in st.session_state:
            st.session_state.selected_advisor = 'general'
        
        # Advisor selection dropdown
        selected_advisor = st.selectbox(
            "Select Your Advisor:",
            options=list(advisor_options.keys()),
            format_func=lambda x: advisor_options[x],
            index=list(advisor_options.keys()).index(st.session_state.selected_advisor),
            key="advisor_selector"
        )
        
        # Update session state
        st.session_state.selected_advisor = selected_advisor
        
        # Show advisor description
        st.markdown(f"""
        <div class="feature-highlight" style="margin-top: 1rem;">
            <p style="margin-bottom: 0; font-size: 0.9rem;"><strong>Focus:</strong> {advisor_descriptions[selected_advisor]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Special info box for general advisor
        if selected_advisor == 'general':
            st.markdown("""
            <div class="stats-card" style="margin-top: 1rem; border-left: 6px solid #ffa726;">
                <h4 style="color: #002469; margin-bottom: 0.5rem;">💡 How General Advisor Works</h4>
                <p style="margin-bottom: 0.5rem; font-size: 0.9rem;">• Answers questions from any department</p>
                <p style="margin-bottom: 0.5rem; font-size: 0.9rem;">• Suggests specialized advisors for detailed guidance</p>
                <p style="margin-bottom: 0; font-size: 0.9rem;">• Perfect starting point when unsure which advisor to choose</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick advisor switching buttons (only show if not general advisor)
        if selected_advisor != 'general':
            st.markdown("""
            <div class="stats-card" style="margin-top: 1rem;">
                <h4 style="color: #002469; margin-bottom: 0.5rem;">💡 Quick Switch</h4>
                <p style="margin-bottom: 0.5rem; font-size: 0.9rem;">Need help from another department?</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show quick switch buttons for related advisors
            related_advisors = {
                'computer_science': ['mathematics', 'engineering', 'general'],
                'mathematics': ['computer_science', 'physics', 'general'],
                'chemistry': ['pre_med', 'biosciences', 'general'],
                'physics': ['mathematics', 'engineering', 'general'],
                'business': ['social_sciences', 'general'],
                'music': ['humanities', 'general'],
                'engineering': ['computer_science', 'mathematics', 'general'],
                'biosciences': ['chemistry', 'pre_med', 'general'],
                'humanities': ['social_sciences', 'general'],
                'social_sciences': ['humanities', 'business', 'general'],
                'architecture': ['engineering', 'general'],
                'pre_med': ['chemistry', 'biosciences', 'general'],
                'pre_law': ['humanities', 'social_sciences', 'general']
            }
            
            quick_switches = related_advisors.get(selected_advisor, ['general'])
            cols = st.columns(len(quick_switches))
            
            for i, advisor_key in enumerate(quick_switches):
                with cols[i]:
                    if st.button(f"Switch to {advisor_options[advisor_key]}", key=f"switch_{advisor_key}"):
                        st.session_state.selected_advisor = advisor_key
                        st.rerun()
        
        # Performance metrics display with Rice styling
        st.markdown("""
        <div class="stats-card">
            <h3 style="color: #002469; margin-bottom: 1rem;">⚡ Performance</h3>
            <div class="rice-success">
                <strong>Model:</strong> GPT-4 (High accuracy)
            </div>
            <div class="rice-success">
                <strong>Response Time:</strong> < 5 seconds
            </div>
            <div class="rice-success">
                <strong>Features:</strong> Specialized advisor prompts
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick test questions for easy access with Rice styling
        st.markdown("""
        <div class="stats-card">
            <h3 style="color: #002469; margin-bottom: 1rem;">🧪 Test Questions</h3>
            <p style="margin-bottom: 1rem; font-size: 0.9rem;">Try these questions to see how different advisors help:</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Diverse test questions to demonstrate advisor switching
        test_questions = [
            "What is the first chemistry course I should take?",
            "What physics courses are available for freshmen?",
            "What is the first computer science course I should take?",
            "What math courses do I need for engineering?",
            "What music courses are available at Rice?",
            "What business courses should I consider?",
            "What are the pre-med requirements?",
            "What English courses fulfill distribution requirements?",
            "What psychology courses are offered?",
            "What architecture courses are available?"
        ]
        
        # Create buttons for test questions
        for question in test_questions:
            if st.button(question, key=f"test_{question}"):
                st.session_state.user_input = question
                st.rerun()
    
    # ================================================================
    # TAB 1: COURSE CHAT INTERFACE
    # ================================================================
    
    with tab1:
        st.header("💬 Ask Your Questions")
        
        # Initialize chat history
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Handle user input from chat or test questions
        user_input = st.chat_input("Ask about Rice courses...")
        
        # Handle test question input from sidebar
        if 'user_input' in st.session_state and st.session_state.user_input:
            user_input = st.session_state.user_input
            st.session_state.user_input = ""
        
        # Process user input
        if user_input:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Get and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Getting answer..."):
                    # Measure response time
                    import time
                    start_time = time.time()
                    response = assistant.get_answer(user_input, st.session_state.selected_advisor)
                    end_time = time.time()
                    
                    # Display response
                    st.markdown(response)
                    st.caption(f"⚡ Response time: {end_time - start_time:.1f} seconds")
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # ================================================================
    # TAB 2: SCHEDULE BUILDER INTERFACE
    # ================================================================
    
    with tab2:
        st.header("📅 Build Your Next Semester Schedule")
        st.markdown("Plan your next semester based on courses you've completed and prerequisites.")
        
        # Add helpful info for freshmen
        st.info("""
        **👋 New to Rice?** 
        - **Freshmen**: Leave completed courses empty to get a freshman-friendly schedule
        - **Continuing students**: Select courses you've already completed to get advanced recommendations
        - **Transfer students**: Add your transfer credits and equivalent courses
        """, icon="💡")
        
        # Add schedule policy information
        st.warning("""
        **📋 Schedule Policy:** 
        - Maximum **1 course per department** to ensure breadth of learning
        - No sequential courses (e.g., Math 101 & 102) in the same semester
        - Appropriate starting courses prioritized for each level
        """, icon="📚")
        
        # Create two-column layout for schedule builder
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🎓 Select Completed Courses (Optional for Freshmen)")
            
            # Department selection with searchable dropdown
            st.markdown("**🏫 Select Department Code**")
            
            # Get all departments with course counts
            dept_options = []
            for dept_code, dept_data in assistant.departments.items():
                course_count = len(dept_data['courses'])
                dept_options.append(f"{dept_code} ({course_count} courses)")
            
            dept_options.sort()
            
            # Department selection dropdown (searchable by default)
            selected_dept_option = st.selectbox(
                "Department (type to search)",
                ["Select a department..."] + dept_options,
                help="Choose a department to see its courses - type to search"
            )
            
            # Extract department code from selection
            selected_dept = None
            if selected_dept_option != "Select a department...":
                selected_dept = selected_dept_option.split(" (")[0]
            
            # Course selection within department
            if selected_dept and selected_dept in assistant.departments:
                dept_courses = assistant.departments[selected_dept]['courses']
                
                if dept_courses:
                    st.markdown(f"**📖 {selected_dept} Courses**")
                    
                    # Create course options with detailed information
                    course_options = []
                    for course in dept_courses:
                        course_code = course.get('course_code', 'N/A')
                        course_title = course.get('title', 'No title')
                        credit_hours = course.get('credit_hours', 'N/A')
                        course_options.append(f"{course_code} - {course_title} ({credit_hours} credits)")
                    
                    # Course selection (searchable multiselect)
                    selected_course_options = st.multiselect(
                        f"Select {selected_dept} courses you've completed (type to search)",
                        course_options,
                        help=f"Choose courses from {selected_dept} department - type to search"
                    )
                    
                    # Extract course codes from selections
                    selected_courses_from_dept = [opt.split(" - ")[0] for opt in selected_course_options]
                    
                    # Initialize session state for all selected courses
                    if 'all_completed_courses' not in st.session_state:
                        st.session_state.all_completed_courses = []
                    
                    # Add current selection to total
                    for course in selected_courses_from_dept:
                        if course not in st.session_state.all_completed_courses:
                            st.session_state.all_completed_courses.append(course)
                    
                    # Show selection confirmation
                    if selected_courses_from_dept:
                        st.success(f"✅ Selected {len(selected_courses_from_dept)} courses from {selected_dept}")
                else:
                    st.info(f"No courses available in {selected_dept}")
            
            # Display all selected courses with management options
            if 'all_completed_courses' in st.session_state and st.session_state.all_completed_courses:
                st.markdown("**📋 All Selected Courses**")
                
                # Create columns for course display and removal
                for i, course in enumerate(st.session_state.all_completed_courses):
                    col_course, col_remove = st.columns([4, 1])
                    with col_course:
                        st.write(f"• {course}")
                    with col_remove:
                        if st.button("❌", key=f"remove_{course}_{i}", help="Remove course"):
                            st.session_state.all_completed_courses.remove(course)
                            st.rerun()
                
                # Clear all courses button
                if st.button("🗑️ Clear All Selected Courses", help="Clear all selected courses"):
                    st.session_state.all_completed_courses = []
                    st.rerun()
                
                # Show helpful summary
                st.markdown(f"**Total: {len(st.session_state.all_completed_courses)} courses selected**")
                
                # Use the selected courses for schedule building
                selected_courses = st.session_state.all_completed_courses
            else:
                selected_courses = []
                st.info("📘 **No courses selected** - Perfect for freshmen starting their first semester!")
        
        # Right column: Schedule settings and controls
        with col2:
            st.subheader("⚙️ Settings")
            
            # Credit hour target setting
            target_credits = st.slider(
                "Target credit hours:",
                min_value=12,
                max_value=18,
                value=15,
                help="Recommended: 15-16 credits"
            )
            
            # Show selected courses count
            st.metric("Completed Courses", len(selected_courses))
        
        # ================================================================
        # SCHEDULE GENERATION AND DISPLAY
        # ================================================================
        
        # Build Schedule Button
        if st.button("🚀 Build Optimized Schedule", key="build_schedule"):
            with st.spinner("Building your optimized schedule..."):
                # Allow freshmen to build schedules without completed courses
                if not selected_courses:
                    st.info("📘 Building freshman schedule with no completed courses...")
                    # Get the selected advisor from session state
                    selected_advisor = st.session_state.get('selected_advisor', 'general')
                    
                    # Use the new advisor-optimized schedule builder
                    schedule_result = assistant.build_advisor_optimized_schedule(
                        completed_courses=selected_courses,
                        advisor_type=selected_advisor,
                        target_credits=15
                    )
                    
                    # Display the optimized schedule
                    st.success("✅ Schedule Generated!")
                    
                    # Show schedule summary
                    st.markdown(f"**📊 Schedule Summary:**")
                    st.markdown(f"- **Total Credits:** {schedule_result['total_credits']}")
                    st.markdown(f"- **Departments:** {', '.join(schedule_result['departments_used'])}")
                    st.markdown(f"- **Student Level:** {schedule_result['student_level'].title()}")
                    
                    # Show recommended courses
                    st.markdown("**📚 Recommended Courses:**")
                    for course in schedule_result['courses']:
                        course_code = course.get('course_code', 'N/A')
                        course_title = course.get('title', 'No title')
                        credit_hours = course.get('credit_hours', 'N/A')
                        department = course.get('department', 'N/A')
                        
                        # Create expandable course card
                        with st.expander(f"📚 {course_code} - {course_title} ({credit_hours} credits)"):
                            st.write(f"**Department:** {department}")
                            st.write(f"**Description:** {course.get('description', 'No description available')}")
                            st.write(f"**Prerequisites:** {course.get('prerequisites', 'None')}")
                            
                            # Show priority score if available
                            if 'priority_score' in course:
                                st.write(f"**Priority Score:** {course['priority_score']}")
                    
                    # Show advisor recommendations
                    if schedule_result.get('advisor_recommendations'):
                        st.markdown("**💡 Advisor Recommendations:**")
                        for rec in schedule_result['advisor_recommendations']:
                            st.markdown(f"- {rec}")
                    
                    # Show department distribution
                    st.markdown("**🏫 Department Distribution:**")
                    for dept, count in schedule_result['dept_distribution'].items():
                        st.markdown(f"- **{dept}:** {count} course{'s' if count > 1 else ''}")
                    
                    # Show guidelines followed
                    guidelines = schedule_result['guidelines_followed']
                    st.markdown("**📋 Guidelines Applied:**")
                    st.markdown(f"- **Priority Departments:** {', '.join(guidelines['priority_departments'])}")
                    st.markdown(f"- **Credit Range:** {guidelines['recommended_credit_range'][0]}-{guidelines['recommended_credit_range'][1]}")
                    st.markdown(f"- **Difficulty Balance:** {guidelines['difficulty_balance'].title()}")
                    
                    # Show special considerations
                    if 'special_considerations' in guidelines:
                        st.markdown("**⚠️ Special Considerations:**")
                        for consideration in guidelines['special_considerations']:
                            st.markdown(f"- {consideration}")
        
        # Right column: Schedule building tips and advisor info
        with col2:
            st.subheader("💡 Schedule Building Tips")
            
            # Show current advisor info
            selected_advisor = st.session_state.get('selected_advisor', 'general')
            advisor_name = selected_advisor.replace('_', ' ').title()
            
            st.markdown(f"""
            <div class="feature-highlight">
                <h4 style="color: #002469; margin-bottom: 0.5rem;">🎯 Active Advisor: {advisor_name}</h4>
                <p style="margin-bottom: 0; font-size: 0.9rem;">Your schedule will be optimized based on this advisor's expertise</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Get advisor-specific guidelines to show tips
            guidelines = assistant.get_advisor_specific_schedule_guidelines(selected_advisor)
            
            # Show advisor-specific tips
            st.markdown("**📚 Advisor-Specific Tips:**")
            for priority in guidelines['sequence_priorities']:
                st.markdown(f"• {priority}")
            
            # Show recommended credit range
            credit_range = guidelines['recommended_credit_range']
            st.markdown(f"**📊 Recommended Credits:** {credit_range[0]}-{credit_range[1]} per semester")
            
            # Show difficulty balance
            difficulty = guidelines['difficulty_balance']
            st.markdown(f"**⚖️ Difficulty Balance:** {difficulty.title()}")
            
            # Show special considerations
            if 'special_considerations' in guidelines:
                st.markdown("**⚠️ Special Notes:**")
                for consideration in guidelines['special_considerations']:
                    st.markdown(f"• {consideration}")
            
            # General tips
            st.markdown("**🎯 General Tips:**")
            st.markdown("• Select courses you've completed")
            st.markdown("• Higher-level courses unlock as you progress")
            st.markdown("• Balance difficulty across departments")
            st.markdown("• Consider prerequisite chains")
            st.markdown("• Plan for future semesters")
    
    # ================================================================
    # TAB 3: DISCOVER COURSES INTERFACE
    # ================================================================
    
    with tab3:
        st.header("🔍 Discover Rice Courses")
        st.markdown("Browse and search through Rice University's course catalog with advanced filters and detailed information.")
        
        # Search and Filter Section
        st.markdown("---")
        
        # Create filter columns
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            st.subheader("🔍 Search")
            
            # Text search
            search_query = st.text_input(
                "Search courses by title, code, or description:",
                placeholder="e.g., 'calculus', 'COMP 140', 'machine learning'",
                help="Search across course titles, codes, and descriptions"
            )
            
            # Department filter
            all_departments = sorted(list(assistant.departments.keys()))
            selected_departments = st.multiselect(
                "Filter by Department:",
                all_departments,
                help="Select one or more departments to filter courses"
            )
        
        with filter_col2:
            st.subheader("📊 Filters")
            
            # Course level filter
            course_levels = st.multiselect(
                "Course Level:",
                ["100-level", "200-level", "300-level", "400-level", "500-level"],
                help="Filter by course difficulty level"
            )
            
            # Credit hours filter
            credit_range = st.slider(
                "Credit Hours Range:",
                min_value=1,
                max_value=6,
                value=(1, 6),
                help="Filter courses by credit hours"
            )
        
        with filter_col3:
            st.subheader("⚙️ Options")
            
            # Display options
            results_per_page = st.selectbox(
                "Results per page:",
                [10, 25, 50, 100],
                index=1,
                help="Number of courses to display"
            )
            
            # Sort options
            sort_by = st.selectbox(
                "Sort by:",
                ["Course Code", "Title", "Department", "Credit Hours"],
                help="Choose how to sort the results"
            )
            
            # Advanced options
            show_prerequisites = st.checkbox("Show Prerequisites", value=True)
            show_descriptions = st.checkbox("Show Full Descriptions", value=True)
        
        # Search button
        if st.button("🔍 Search Courses", type="primary"):
            # Perform search and filtering
            filtered_courses = []
            
            # Get all courses from all departments
            all_courses = []
            for dept_code, dept_data in assistant.departments.items():
                for course in dept_data.get('courses', []):
                    course_with_dept = course.copy()
                    course_with_dept['department'] = dept_code
                    all_courses.append(course_with_dept)
            
            # Apply filters
            for course in all_courses:
                # Department filter
                if selected_departments and course['department'] not in selected_departments:
                    continue
                
                # Course level filter
                if course_levels:
                    course_code = course.get('course_code', '')
                    course_num = ''.join(filter(str.isdigit, course_code))
                    if course_num:
                        level = f"{course_num[0]}00-level"
                        if level not in course_levels:
                            continue
                
                # Credit hours filter
                credit_str = course.get('credit_hours', '3')
                try:
                    credits = assistant.parse_credit_hours(credit_str)
                    if not (credit_range[0] <= credits <= credit_range[1]):
                        continue
                except:
                    continue
                
                # Text search filter
                if search_query:
                    search_text = search_query.lower()
                    course_title = course.get('title', '').lower()
                    course_code = course.get('course_code', '').lower()
                    course_desc = course.get('description', '').lower()
                    
                    if (search_text not in course_title and 
                        search_text not in course_code and 
                        search_text not in course_desc):
                        continue
                
                filtered_courses.append(course)
            
            # Sort results
            if sort_by == "Course Code":
                filtered_courses.sort(key=lambda x: x.get('course_code', ''))
            elif sort_by == "Title":
                filtered_courses.sort(key=lambda x: x.get('title', ''))
            elif sort_by == "Department":
                filtered_courses.sort(key=lambda x: x.get('department', ''))
            elif sort_by == "Credit Hours":
                filtered_courses.sort(key=lambda x: assistant.parse_credit_hours(x.get('credit_hours', '3')))
            
            # Display results
            st.markdown("---")
            st.markdown(f"### 📚 Found {len(filtered_courses)} courses")
            
            if len(filtered_courses) == 0:
                st.info("No courses found matching your criteria. Try adjusting your filters.")
            else:
                # Paginate results
                start_idx = 0
                end_idx = min(results_per_page, len(filtered_courses))
                
                for i, course in enumerate(filtered_courses[start_idx:end_idx], 1):
                    course_code = course.get('course_code', 'N/A')
                    course_title = course.get('title', 'No title')
                    department = course.get('department', 'N/A')
                    credit_hours = course.get('credit_hours', 'N/A')
                    
                    # Create course card
                    with st.expander(f"📚 {course_code} - {course_title}", expanded=False):
                        
                        # Course basic info
                        info_col1, info_col2 = st.columns(2)
                        
                        with info_col1:
                            st.markdown(f"**Department:** {department}")
                            st.markdown(f"**Credits:** {credit_hours}")
                            
                            # Course URL (construct based on Rice course catalog pattern)
                            course_url = f"https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=COURSE&p_term=202420&p_crn={course_code.replace(' ', '%20')}"
                            st.markdown(f"**Course URL:** [View on Rice Catalog]({course_url})")
                        
                        with info_col2:
                            # Distribution requirements
                            if 'distribution' in course:
                                st.markdown(f"**Distribution:** {course['distribution']}")
                            
                            # Prerequisites
                            if show_prerequisites and course.get('prerequisites'):
                                prereq_text = course['prerequisites']
                                if prereq_text and prereq_text.strip() not in ['None', 'N/A', '']:
                                    st.markdown(f"**Prerequisites:** {prereq_text}")
                        
                        # Course description
                        if show_descriptions and course.get('description'):
                            st.markdown("**Description:**")
                            st.markdown(course['description'])
                        
                        # Additional info
                        if course.get('restrictions'):
                            formatted_restrictions = assistant.format_restrictions_text(course['restrictions'])
                            st.markdown(f"**Restrictions:** {formatted_restrictions}")
                        
                        # Action buttons
                        button_col1, button_col2, button_col3 = st.columns(3)
                        
                        with button_col1:
                            if st.button(f"📋 Add to Schedule", key=f"add_{course_code}_{i}"):
                                st.info(f"Course {course_code} added to your planning list!")
                        
                        with button_col2:
                            if st.button(f"❓ Ask About Course", key=f"ask_{course_code}_{i}"):
                                st.info(f"Switch to Chat tab to ask about {course_code}!")
                        
                        with button_col3:
                            if st.button(f"🔗 Open Official Page", key=f"open_{course_code}_{i}"):
                                st.markdown(f"[Open {course_code} on Rice Catalog]({course_url})")
                
                # Show pagination info
                if len(filtered_courses) > results_per_page:
                    st.markdown(f"*Showing {end_idx} of {len(filtered_courses)} results*")
                    st.info("💡 Use the 'Results per page' filter to see more courses at once.")
        
        # Default view when no search is performed
        else:
            st.markdown("---")
            st.markdown("### 🌟 Getting Started")
            
            # Quick stats
            total_courses = sum(len(dept_data.get('courses', [])) for dept_data in assistant.departments.values())
            total_departments = len(assistant.departments)
            
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            
            with stat_col1:
                st.metric("Total Courses", total_courses)
            
            with stat_col2:
                st.metric("Departments", total_departments)
            
            with stat_col3:
                st.metric("Search Features", "Advanced")
            
            # Popular departments
            st.markdown("### 🏫 Popular Departments")
            
            # Get department course counts
            dept_counts = []
            for dept_code, dept_data in assistant.departments.items():
                course_count = len(dept_data.get('courses', []))
                dept_counts.append((dept_code, course_count))
            
            # Sort by course count
            dept_counts.sort(key=lambda x: x[1], reverse=True)
            
            # Show top departments
            dept_cols = st.columns(4)
            for i, (dept_code, count) in enumerate(dept_counts[:8]):
                with dept_cols[i % 4]:
                    if st.button(f"{dept_code}\n({count} courses)", key=f"dept_{dept_code}"):
                        st.rerun()
            
            # Search tips
            st.markdown("### 💡 Search Tips")
            st.markdown("""
            - **Quick Search:** Type course codes like "COMP 140" or keywords like "calculus"
            - **Department Filter:** Select specific departments to narrow results
            - **Level Filter:** Choose 100-level for introductory, 400-level for advanced
            - **Credit Filter:** Find courses that match your credit hour needs
            - **Sort Options:** Organize results by code, title, or department
            """)
            
            # Featured courses (sample)
            st.markdown("### ⭐ Featured Courses")
            
            featured_courses = [
                ("COMP 140", "Computational Thinking", "Great introduction to programming"),
                ("MATH 101", "Single Variable Calculus I", "Essential calculus foundation"),
                ("ENGL 103", "Critical Writing", "Develops strong writing skills"),
                ("PHYS 101", "Mechanics", "Classical physics fundamentals")
            ]
            
            for course_code, title, description in featured_courses:
                with st.expander(f"⭐ {course_code} - {title}"):
                    st.markdown(f"**Description:** {description}")
                    st.markdown(f"**Quick Link:** [View on Rice Catalog](https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=COURSE&p_term=202420&p_crn={course_code.replace(' ', '%20')})")
    
    # ================================================================
    # FOOTER AND BRANDING
    # ================================================================
    
    st.markdown("---")
    st.markdown("🎓 **Rice Course Assistant v4.0** - Fast, accurate, and reliable")

# ================================================================
# APPLICATION ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main() 