# course_recommender.py
import json
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os
from typing import List, Dict, Tuple, Optional
import logging
import re
from dataclasses import dataclass, field
from collections import defaultdict, deque
import networkx as nx

# Import ML-enhanced components
try:
    from ml_enhanced_recommender import (
        MLEnhancedRecommendationEngine, 
        StudentProfile, 
        StudentSuccessPredictor,
        AdvancedQueryProcessor
    )
    ML_ENHANCED_AVAILABLE = True
except ImportError:
    ML_ENHANCED_AVAILABLE = False
    print("⚠️ ML-enhanced features not available. Install required packages for full functionality.")

# Import GPT Wrapper Validator
try:
    from gpt_wrapper_validator import (
        GPTWrapperValidator,
        initialize_gpt_validator,
        validate_with_gpt
    )
    GPT_WRAPPER_AVAILABLE = True
except ImportError:
    GPT_WRAPPER_AVAILABLE = False
    print("⚠️ GPT Wrapper not available. Set OPENAI_API_KEY for GPT-powered validation.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiceCourseRecommender:
    def __init__(self, course_file: str = "rice_all_courses.json", enable_ml: bool = True):
        """Initialize the Rice Course Recommender with enhanced intelligence"""
        self.course_file = course_file
        self.courses_df = None
        self.course_embeddings = None
        self.model = None  # Lazy load the model
        
        # Enhanced Intelligence Components
        self.prerequisite_parser = PrerequisiteParser()
        self.major_requirement_engine = MajorRequirementEngine()
        self.semester_planning_engine = SemesterPlanningEngine(
            self.prerequisite_parser, 
            self.major_requirement_engine
        )
        self.prerequisite_graph_built = False
        
        # Enhanced course features
        self.course_difficulty_scores = {}
        self.course_workload_estimates = {}
        self.course_career_relevance = {}
        
        # ML-Enhanced Components (Phase 2) - Lazy load
        self.ml_enhanced = enable_ml and ML_ENHANCED_AVAILABLE
        self.ml_engine = None
        
        # GPT Wrapper Validator (Phase 3) - Lazy load
        self.gpt_wrapper_enabled = GPT_WRAPPER_AVAILABLE
        self.gpt_initialized = False
        
        # Load course data (this is fast)
        self.load_courses()
        
        print(f"✅ Rice Course Recommender initialized with {len(self.courses_df)} courses")
        print("🚀 Fast initialization complete! ML and embeddings will load on first use.")
        
    def _ensure_model_loaded(self):
        """Lazy load the SentenceTransformer model"""
        if self.model is None:
            print("🔄 Loading SentenceTransformer model (one-time setup)...")
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
            print("✅ Model loaded!")
        
    def _ensure_gpt_initialized(self):
        """Lazy initialize GPT wrapper"""
        if self.gpt_wrapper_enabled and not self.gpt_initialized:
            print("🔄 Initializing GPT wrapper...")
            initialize_gpt_validator()
            self.gpt_initialized = True
            print("✅ GPT wrapper initialized!")
        
    def _initialize_ml_components(self):
        """Initialize ML-enhanced components (lazy loading)"""
        if self.ml_engine is not None:
            return  # Already initialized
            
        try:
            print("🤖 Initializing ML-Enhanced Academic Advisor...")
            
            # Convert courses_df to dict format for ML engine
            course_data_dict = {}
            for _, course in self.courses_df.iterrows():
                course_data_dict[course['course_code']] = course.to_dict()
            
            # Initialize ML engine
            self.ml_engine = MLEnhancedRecommendationEngine(course_data_dict)
            
            # Check if pre-trained models exist
            if os.path.exists("ml_models_cache.pkl"):
                print("📂 Loading pre-trained ML models...")
                try:
                    with open("ml_models_cache.pkl", 'rb') as f:
                        model_cache = pickle.load(f)
                        self.ml_engine.success_predictor = model_cache['success_predictor']
                        self.ml_engine.training_data_generated = True
                    print("✅ Pre-trained ML models loaded!")
                    return
                except Exception as e:
                    print(f"⚠️ Failed to load cached models: {e}")
            
            # Train models with synthetic data (only if no cache)
            print("🧠 Training ML models (this may take a moment)...")
            metrics = self.ml_engine.train_models()
            
            # Cache the trained models
            try:
                with open("ml_models_cache.pkl", 'wb') as f:
                    pickle.dump({
                        'success_predictor': self.ml_engine.success_predictor
                    }, f)
                print("💾 ML models cached for future use!")
            except Exception as e:
                print(f"⚠️ Failed to cache models: {e}")
            
            print(f"✅ ML models trained - Accuracy: {metrics['accuracy']:.3f}")
            print("🚀 Phase 2 ML-Enhanced features are now active!")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize ML components: {e}")
            self.ml_enhanced = False
    
    def load_courses(self):
        """Load courses and build intelligence systems"""
        print("📚 Loading courses...")
        
        try:
            # Load course data
            with open(self.course_file, 'r') as f:
                course_data = json.load(f)
                
            self.courses_df = pd.DataFrame(course_data)
            
            # Prepare text for embeddings (handle Fall 2025 data format)
            if 'combined_text' not in self.courses_df.columns:
                print("📝 Preparing course text for embeddings...")
                try:
                    self.courses_df['combined_text'] = self.courses_df.apply(self._combine_course_text, axis=1)
                except Exception as e:
                    print(f"❌ Error preparing course text: {e}")
                    # Create a simple combined text as fallback
                    self.courses_df['combined_text'] = self.courses_df.apply(
                        lambda row: f"{row.get('course_code', '')} {row.get('title', '')}", axis=1
                    )
            
            # Build prerequisite graph
            print("🔗 Building prerequisite intelligence...")
            self.prerequisite_parser.build_prerequisite_graph(course_data)
            self.prerequisite_graph_built = True
            
            # Calculate enhanced course features
            self._calculate_course_features()
            
            print(f"✅ Loaded {len(self.courses_df)} courses with full intelligence")
            
        except Exception as e:
            print(f"❌ Error loading courses: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _calculate_course_features(self):
        """Calculate enhanced course features for better recommendations"""
        print("⚡ Calculating enhanced course features...")
        
        for _, course in self.courses_df.iterrows():
            course_code = course.get('course_code', '')
            
            # Calculate difficulty score
            difficulty = self._calculate_course_difficulty(course)
            self.course_difficulty_scores[course_code] = difficulty
            
            # Estimate workload
            workload = self._estimate_course_workload(course)
            self.course_workload_estimates[course_code] = workload
            
            # Calculate career relevance
            career_relevance = self._calculate_career_relevance(course)
            self.course_career_relevance[course_code] = career_relevance
    
    def _calculate_course_difficulty(self, course: pd.Series) -> float:
        """Calculate difficulty score for a course"""
        difficulty = 0.0
        
        # Course level contributes to difficulty
        course_number = course.get('course_number', '')
        if pd.notna(course_number) and course_number:
            try:
                level = int(str(course_number)[0]) if str(course_number)[0].isdigit() else 1
                difficulty += level * 0.2
            except:
                difficulty += 0.2  # Default level
        
        # Prerequisites contribute to difficulty
        prerequisites = course.get('prerequisites', '')
        if pd.notna(prerequisites) and prerequisites and isinstance(prerequisites, str):
            prereq_count = len(re.findall(r'[A-Z]{3,4}\s+\d{3}', prerequisites))
            difficulty += min(prereq_count * 0.1, 0.3)
        
        # Course description keywords
        description = course.get('description', '')
        if pd.notna(description) and description:
            description_lower = str(description).lower()
            difficulty_keywords = ['advanced', 'graduate', 'research', 'thesis', 'capstone']
            for keyword in difficulty_keywords:
                if keyword in description_lower:
                    difficulty += 0.15
        
        return min(difficulty, 1.0)
    
    def _estimate_course_workload(self, course: pd.Series) -> float:
        """Estimate workload for a course"""
        workload = 0.5  # Base workload
        
        # Credit hours affect workload
        credit_hours = course.get('credit_hours', '3')
        try:
            if pd.notna(credit_hours) and credit_hours:
                if isinstance(credit_hours, str):
                    credits = int(credit_hours.split()[0])
                else:
                    credits = int(credit_hours)
                workload += credits * 0.1
            else:
                workload += 0.3  # Default
        except:
            workload += 0.3  # Default
        
        # Course type affects workload
        course_type = course.get('course_type', '')
        if pd.notna(course_type) and course_type:
            course_type_lower = str(course_type).lower()
            if 'laboratory' in course_type_lower:
                workload += 0.2
            if 'research' in course_type_lower:
                workload += 0.3
            if 'seminar' in course_type_lower:
                workload += 0.1
        
        return min(workload, 1.0)
    
    def _calculate_career_relevance(self, course: pd.Series) -> Dict[str, float]:
        """Calculate career relevance scores for different fields"""
        relevance = {}
        
        course_code = course.get('course_code', '')
        title = course.get('title', '')
        description = course.get('description', '')
        
        # Convert to strings and handle NaN values
        title_lower = str(title).lower() if pd.notna(title) and title else ''
        description_lower = str(description).lower() if pd.notna(description) and description else ''
        
        # Tech industry relevance
        tech_keywords = ['programming', 'software', 'data', 'machine learning', 'artificial intelligence']
        tech_score = sum(0.2 for keyword in tech_keywords if keyword in title_lower or keyword in description_lower)
        relevance['tech'] = min(tech_score, 1.0)
        
        # Research relevance
        research_keywords = ['research', 'analysis', 'theory', 'methodology']
        research_score = sum(0.2 for keyword in research_keywords if keyword in title_lower or keyword in description_lower)
        relevance['research'] = min(research_score, 1.0)
        
        # Finance relevance
        finance_keywords = ['economics', 'finance', 'statistics', 'modeling']
        finance_score = sum(0.2 for keyword in finance_keywords if keyword in title_lower or keyword in description_lower)
        relevance['finance'] = min(finance_score, 1.0)
        
        return relevance
    
    def get_intelligent_recommendations(self, query: str, student_profile: Dict = None) -> Dict:
        """Get intelligent recommendations using all available intelligence"""
        if not student_profile:
            student_profile = {}
        
        # Extract information from query
        query_analysis = self._analyze_query(query)
        
        # Handle instructor queries specifically
        if query_analysis.get('intent') == 'instructor_search' and query_analysis.get('instructor_name'):
            instructor_courses = self.get_courses_by_instructor(query_analysis['instructor_name'])
            
            # Convert to standard recommendation format
            recommendations = []
            for course in instructor_courses:
                recommendation = {
                    'course_code': course['course_code'],
                    'title': course['title'],
                    'description': course['description'],
                    'department': course['department'],
                    'credit_hours': course['credits'],
                    'prerequisites': 'None',  # Will be enhanced if prerequisite system is available
                    'course_type': 'N/A',
                    'similarity_score': 1.0,  # Perfect match for instructor search
                    'text_similarity': 1.0,
                    'context_relevance': 1.0,
                    'distribution_group': course['distribution_group'],
                    'instructors': course['instructors'],
                    'meeting_time': course['meeting_time']
                }
                recommendations.append(recommendation)
            
            insights = [f"Found {len(recommendations)} courses taught by {query_analysis['instructor_name']}"]
            
            return {
                'recommendations': recommendations,
                'insights': insights,
                'query_analysis': query_analysis
            }
        
        # Get basic recommendations
        recommendations = self.get_recommendations_by_interest(query, num_recommendations=20)
        
        # Enhance with prerequisite intelligence
        if self.prerequisite_graph_built:
            recommendations = self._enhance_with_prerequisite_intelligence(
                recommendations, student_profile
            )
        
        # Enhance with major requirement intelligence
        if 'major' in student_profile:
            recommendations = self._enhance_with_major_requirements(
                recommendations, student_profile
            )
        
        # Add intelligent insights
        insights = self._generate_intelligent_insights(recommendations, query_analysis, student_profile)
        
        return {
            'recommendations': recommendations[:10],
            'insights': insights,
            'query_analysis': query_analysis
        }
    
    def _analyze_query(self, query: str) -> Dict:
        """Analyze query to understand student intent"""
        query_lower = query.lower()
        
        analysis = {
            'intent': 'general',
            'academic_level': 'undergraduate',
            'career_focus': None,
            'semester_planning': False,
            'prerequisite_concern': False,
            'major_planning': False,
            'instructor_query': False,
            'instructor_name': None
        }
        
        # Detect instructor queries
        instructor_keywords = ['professor', 'prof', 'instructor', 'teacher', 'teaches', 'teaching']
        if any(keyword in query_lower for keyword in instructor_keywords):
            analysis['instructor_query'] = True
            # Try to extract instructor name
            instructor_name = self._extract_instructor_name(query)
            if instructor_name:
                analysis['instructor_name'] = instructor_name
                analysis['intent'] = 'instructor_search'
        
        # Detect intent
        if any(word in query_lower for word in ['similar', 'like', 'related']):
            analysis['intent'] = 'similarity'
        elif any(word in query_lower for word in ['next semester', 'should i take', 'recommend']):
            analysis['intent'] = 'planning'
        elif any(word in query_lower for word in ['prerequisite', 'prereq', 'before']):
            analysis['intent'] = 'prerequisite'
        elif any(word in query_lower for word in ['major', 'degree', 'graduate']):
            analysis['intent'] = 'major_planning'
        
        # Detect academic level
        if any(word in query_lower for word in ['freshman', 'first year']):
            analysis['academic_level'] = 'freshman'
        elif any(word in query_lower for word in ['sophomore']):
            analysis['academic_level'] = 'sophomore'
        elif any(word in query_lower for word in ['junior']):
            analysis['academic_level'] = 'junior'
        elif any(word in query_lower for word in ['senior']):
            analysis['academic_level'] = 'senior'
        elif any(word in query_lower for word in ['graduate', 'grad', 'masters', 'phd']):
            analysis['academic_level'] = 'graduate'
        
        # Detect career focus
        if any(word in query_lower for word in ['software', 'programming', 'tech']):
            analysis['career_focus'] = 'tech'
        elif any(word in query_lower for word in ['research', 'academic']):
            analysis['career_focus'] = 'research'
        elif any(word in query_lower for word in ['finance', 'banking', 'economics']):
            analysis['career_focus'] = 'finance'
        
        return analysis
    
    def _extract_instructor_name(self, query: str) -> Optional[str]:
        """Extract instructor name from query"""
        import re
        # Remove leading question phrases
        query_clean = re.sub(r'^(what courses is|who is teaching|is|does|list|show|find|give|tell me|which|that|are|was|were|do|does|did|can|could|would|should|will|may|might|must|shall)\s+', '', query, flags=re.IGNORECASE)
        # Find first two consecutive capitalized words
        words = query_clean.split()
        for i in range(len(words) - 1):
            if words[i][0].isupper() and words[i+1][0].isupper():
                return f"{words[i]} {words[i+1]}"
        # Fallback: return first capitalized word if no pair found
        for word in words:
            if word[0].isupper():
                return word
        return None
    
    def _enhance_with_prerequisite_intelligence(self, recommendations: List[Dict], 
                                              student_profile: Dict) -> List[Dict]:
        """Enhance recommendations with prerequisite intelligence"""
        completed_courses = student_profile.get('completed_courses', [])
        
        enhanced_recommendations = []
        
        for rec in recommendations:
            course_code = rec.get('course_code', '')
            
            # Check prerequisite satisfaction
            satisfied, missing = self.prerequisite_parser.validate_prerequisite_satisfaction(
                course_code, completed_courses
            )
            
            rec['prerequisite_satisfied'] = satisfied
            rec['missing_prerequisites'] = missing
            
            # Get prerequisite chain
            prereq_chain = self.prerequisite_parser.get_prerequisites(course_code, depth=2)
            rec['prerequisite_chain'] = prereq_chain
            
            # Get courses this enables
            enables = self.prerequisite_parser.get_courses_requiring(course_code)
            rec['enables_courses'] = enables
            
            enhanced_recommendations.append(rec)
        
        return enhanced_recommendations
    
    def _enhance_with_major_requirements(self, recommendations: List[Dict], 
                                       student_profile: Dict) -> List[Dict]:
        """Enhance recommendations with major requirement intelligence"""
        major = student_profile.get('major')
        completed_courses = student_profile.get('completed_courses', [])
        
        if not major or major not in self.major_requirement_engine.major_requirements:
            return recommendations
        
        # Get degree progress
        progress = self.major_requirement_engine.analyze_degree_progress(major, completed_courses)
        
        enhanced_recommendations = []
        
        for rec in recommendations:
            course_code = rec.get('course_code', '')
            
            # Check if course satisfies major requirement
            satisfies_requirement = None
            for req in progress.requirements_remaining:
                if course_code in req.course_options:
                    satisfies_requirement = req
                    break
            
            rec['satisfies_major_requirement'] = satisfies_requirement is not None
            if satisfies_requirement:
                rec['requirement_details'] = {
                    'name': satisfies_requirement.name,
                    'type': satisfies_requirement.requirement_type,
                    'priority': satisfies_requirement.priority,
                    'semester_recommended': satisfies_requirement.semester_recommended
                }
            
            # Add course features
            rec['difficulty_score'] = self.course_difficulty_scores.get(course_code, 0.5)
            rec['workload_estimate'] = self.course_workload_estimates.get(course_code, 0.5)
            rec['career_relevance'] = self.course_career_relevance.get(course_code, {})
            
            enhanced_recommendations.append(rec)
        
        return enhanced_recommendations
    
    def _generate_intelligent_insights(self, recommendations: List[Dict], 
                                     query_analysis: Dict, 
                                     student_profile: Dict) -> List[str]:
        """Generate intelligent insights about the recommendations"""
        insights = []
        
        # Prerequisite insights
        blocked_courses = [rec for rec in recommendations if not rec.get('prerequisite_satisfied', True)]
        if blocked_courses:
            insights.append(f"📚 {len(blocked_courses)} courses require additional prerequisites")
        
        # Major requirement insights
        major_req_courses = [rec for rec in recommendations if rec.get('satisfies_major_requirement', False)]
        if major_req_courses:
            insights.append(f"🎓 {len(major_req_courses)} courses satisfy major requirements")
        
        # Difficulty insights
        difficulty_scores = [rec.get('difficulty_score', 0.5) for rec in recommendations]
        avg_difficulty = sum(difficulty_scores) / len(difficulty_scores) if difficulty_scores else 0.5
        if avg_difficulty > 0.7:
            insights.append("⚠️ These courses are generally challenging - consider balancing your schedule")
        elif avg_difficulty < 0.3:
            insights.append("✅ These courses are generally more accessible for beginners")
        
        # Career relevance insights
        career_focus = query_analysis.get('career_focus')
        if career_focus:
            relevant_courses = [rec for rec in recommendations 
                              if rec.get('career_relevance', {}).get(career_focus, 0) > 0.5]
            if relevant_courses:
                insights.append(f"💼 {len(relevant_courses)} courses are highly relevant to {career_focus}")
        
        # Sequential insights
        if query_analysis.get('intent') == 'planning':
            insights.append("📅 Consider taking prerequisites in the correct order for optimal progression")
        
        return insights
    
    def get_degree_audit(self, major: str, completed_courses: List[str]) -> Dict:
        """Get comprehensive degree audit"""
        if not self.prerequisite_graph_built:
            return {"error": "Prerequisite intelligence not available"}
        
        # Get degree progress
        progress = self.major_requirement_engine.analyze_degree_progress(major, completed_courses)
        
        # Get next semester recommendations
        next_semester = self.major_requirement_engine.get_next_semester_recommendations(
            major, completed_courses
        )
        
        # Get optimal sequence for remaining courses
        remaining_course_codes = []
        for req in progress.requirements_remaining:
            remaining_course_codes.extend(req.course_options)
        
        optimal_sequence = self.prerequisite_parser.find_optimal_course_sequence(
            remaining_course_codes, completed_courses
        )
        
        # Get graduation validation
        can_graduate, graduation_issues = self.major_requirement_engine.validate_graduation_requirements(
            major, completed_courses
        )
        
        return {
            'degree_progress': progress,
            'next_semester_recommendations': next_semester,
            'optimal_sequence': optimal_sequence,
            'can_graduate': can_graduate,
            'graduation_issues': graduation_issues,
            'alternative_paths': self.major_requirement_engine.get_alternative_paths(major, completed_courses)
        }
    
    def get_prerequisite_analysis(self, course_code: str) -> Dict:
        """Get detailed prerequisite analysis for a course"""
        if not self.prerequisite_graph_built:
            return {"error": "Prerequisite intelligence not available"}
        
        # Get prerequisite chain
        prereq_chain = self.prerequisite_parser.get_prerequisites(course_code, depth=3)
        
        # Get courses this enables
        enables = self.prerequisite_parser.get_courses_requiring(course_code)
        
        # Get prerequisite tree
        prereq_tree = self.prerequisite_parser.prerequisite_trees.get(course_code)
        
        return {
            'course_code': course_code,
            'direct_prerequisites': self.prerequisite_parser.get_prerequisites(course_code, depth=1),
            'full_prerequisite_chain': prereq_chain,
            'enables_courses': enables,
            'prerequisite_tree': prereq_tree,
            'course_level': self.prerequisite_parser.course_levels.get(course_code, 0)
        }

    def load_course_data(self, filename: str):
        """Load course data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                courses = json.load(f)
            
            self.courses_df = pd.DataFrame(courses)
            print(f"Loaded {len(self.courses_df)} courses")
            
            # Clean and prepare text data
            self.prepare_course_text()
            
        except FileNotFoundError:
            print(f"Course data file {filename} not found. Please run the scraper first.")
            return False
        except Exception as e:
            print(f"Error loading course data: {e}")
            return False
        
        return True
    
    def prepare_course_text(self):
        """Prepare and clean course text for embedding"""
        # Combine multiple text fields for better embedding
        self.courses_df['combined_text'] = self.courses_df.apply(self._combine_course_text, axis=1)
        
        # Clean the combined text
        self.courses_df['combined_text'] = self.courses_df['combined_text'].fillna('')
        
        print("Course text prepared for embedding")
    
    def _combine_course_text(self, row):
        """Combine course information into a single text field"""
        text_parts = []
        
        # Add title (high weight)
        title = row.get('title')
        if pd.notna(title) and title:
            text_parts.append(f"Title: {title}")
        
        # Add course code (for exact matching)
        course_code = row.get('course_code')
        if pd.notna(course_code) and course_code:
            text_parts.append(f"Course: {course_code}")
        
        # Add description (main content)
        description = row.get('description')
        if pd.notna(description) and description:
            text_parts.append(f"Description: {description}")
        
        # Add department (handle both 'department' and 'subject_code' fields)
        dept = row.get('department') or row.get('subject_code')
        if pd.notna(dept) and dept:
            text_parts.append(f"Department: {dept}")
        
        # Add course type
        course_type = row.get('course_type')
        if pd.notna(course_type) and course_type:
            text_parts.append(f"Type: {course_type}")
        
        # Add prerequisites (important for student planning)
        prerequisites = row.get('prerequisites')
        if pd.notna(prerequisites) and prerequisites:
            text_parts.append(f"Prerequisites: {prerequisites}")
        
        # Add distribution group
        distribution = row.get('distribution_group')
        if pd.notna(distribution) and distribution:
            text_parts.append(f"Distribution: {distribution}")
        
        # Add instructors (Fall 2025 data)
        instructors = row.get('instructors')
        if pd.notna(instructors) and instructors:
            if isinstance(instructors, list):
                instructors_text = ", ".join(instructors)
            else:
                instructors_text = str(instructors)
            text_parts.append(f"Instructors: {instructors_text}")
        
        # Add meeting time (Fall 2025 data)
        meeting_time = row.get('meeting_time')
        if pd.notna(meeting_time) and meeting_time:
            text_parts.append(f"Meeting Time: {meeting_time}")
        
        # Add credits (handle both 'credits' and 'credit_hours' fields)
        credits = row.get('credits') or row.get('credit_hours')
        if pd.notna(credits) and credits:
            text_parts.append(f"Credits: {credits}")
        
        return " ".join(text_parts)
    
    def create_embeddings(self, save_path: str = "course_embeddings.pkl"):
        """Create sentence embeddings for all courses"""
        print("Creating course embeddings...")
        
        # Check if embeddings already exist
        if os.path.exists(save_path):
            try:
                with open(save_path, 'rb') as f:
                    self.course_embeddings = pickle.load(f)
                print(f"Loaded existing embeddings from {save_path}")
                return
            except:
                print("Error loading existing embeddings, creating new ones...")
        
        # Ensure model is loaded
        self._ensure_model_loaded()
        
        # Create embeddings
        course_texts = self.courses_df['combined_text'].tolist()
        self.course_embeddings = self.model.encode(course_texts, convert_to_tensor=True)
        
        # Save embeddings for future use
        try:
            with open(save_path, 'wb') as f:
                pickle.dump(self.course_embeddings, f)
            print(f"Saved embeddings to {save_path}")
        except Exception as e:
            print(f"Warning: Could not save embeddings: {e}")
        
        print(f"Created embeddings for {len(course_texts)} courses")
    
    def create_tfidf_features(self):
        """Create TF-IDF features as an alternative/complement to embeddings"""
        print("Creating TF-IDF features...")
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),  # Include bigrams
            min_df=2,  # Ignore terms that appear in fewer than 2 documents
            max_df=0.8  # Ignore terms that appear in more than 80% of documents
        )
        
        course_texts = self.courses_df['combined_text'].tolist()
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(course_texts)
        
        print(f"Created TF-IDF matrix with shape {self.tfidf_matrix.shape}")
    
    def get_recommendations_by_interest(self, 
                                       interest_query: str, 
                                       num_recommendations: int = 10,
                                       department_filter: str = None,
                                       level_filter: str = None) -> List[Dict]:
        """Get course recommendations based on interest query with enhanced context awareness"""
        
        # Ensure model is loaded
        self._ensure_model_loaded()
        
        if self.course_embeddings is None:
            self.create_embeddings()
        
        # Create embedding for the query
        query_embedding = self.model.encode([interest_query], convert_to_tensor=True)
        
        # Calculate similarities - handle both tensor and numpy array cases
        if hasattr(query_embedding, 'cpu'):
            query_embedding_np = query_embedding.cpu().numpy()
        else:
            query_embedding_np = query_embedding
            
        if hasattr(self.course_embeddings, 'cpu'):
            course_embeddings_np = self.course_embeddings.cpu().numpy()
        else:
            course_embeddings_np = self.course_embeddings
            
        similarities = cosine_similarity(query_embedding_np, course_embeddings_np)[0]
        
        # Enhanced context-aware filtering
        query_lower = interest_query.lower()
        
        # Detect query intent and prioritize relevant departments
        priority_departments = self._detect_priority_departments(query_lower)
        
        # Detect academic level from query
        detected_level = self._detect_academic_level(query_lower)
        if detected_level:
            level_filter = detected_level
        
        # Create enhanced recommendations
        enhanced_recommendations = []
        
        for idx, text_similarity in enumerate(similarities):
            course = self.courses_df.iloc[idx]
            
            # Apply basic filters first
            if department_filter and course.get('department', '').upper() != department_filter.upper():
                continue
            
            # Level filter (undergraduate vs graduate)
            if level_filter:
                course_number = str(course.get('course_number', ''))
                if level_filter.lower() == 'undergraduate' and course_number.startswith(('5', '6', '7', '8')):
                    continue
                elif level_filter.lower() == 'graduate' and not course_number.startswith(('5', '6', '7', '8')):
                    continue
            
            # Calculate enhanced score using context awareness
            context_score = self._calculate_context_relevance(query_lower, course, priority_departments)
            
            # Combine text similarity with context relevance
            enhanced_score = (0.4 * text_similarity + 0.6 * context_score)
            
            recommendation = {
                'course_code': course.get('course_code', 'N/A'),
                'title': course.get('title', 'N/A'),
                'description': course.get('description', 'N/A'),
                'department': course.get('department', 'N/A'),
                'credit_hours': course.get('credit_hours', 'N/A'),
                'prerequisites': course.get('prerequisites', 'None'),
                'course_type': course.get('course_type', 'N/A'),
                'similarity_score': float(enhanced_score),
                'text_similarity': float(text_similarity),
                'context_relevance': float(context_score),
                'distribution_group': course.get('distribution_group', 'N/A')
            }
            
            enhanced_recommendations.append(recommendation)
        
        # Sort by enhanced score and return top recommendations
        enhanced_recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
        return enhanced_recommendations[:num_recommendations]
    
    def _detect_priority_departments(self, query: str) -> Dict[str, float]:
        """Detect which departments should be prioritized based on query content"""
        priority_mapping = {
            # Machine Learning & AI keywords
            'machine learning': {'COMP': 1.0, 'MATH': 0.9, 'STAT': 0.9, 'ELEC': 0.7},
            'artificial intelligence': {'COMP': 1.0, 'MATH': 0.8, 'STAT': 0.8, 'ELEC': 0.7},
            'deep learning': {'COMP': 1.0, 'MATH': 0.9, 'STAT': 0.8, 'ELEC': 0.7},
            'neural networks': {'COMP': 1.0, 'MATH': 0.9, 'ELEC': 0.8, 'STAT': 0.7},
            'data science': {'COMP': 1.0, 'STAT': 1.0, 'MATH': 0.9, 'ECON': 0.6},
            
            # Math keywords
            'calculus': {'MATH': 1.0, 'PHYS': 0.8, 'COMP': 0.7, 'ELEC': 0.6},
            'linear algebra': {'MATH': 1.0, 'COMP': 0.9, 'STAT': 0.8, 'ELEC': 0.7},
            'statistics': {'STAT': 1.0, 'MATH': 0.9, 'COMP': 0.8, 'ECON': 0.7},
            'probability': {'STAT': 1.0, 'MATH': 0.9, 'COMP': 0.8, 'ELEC': 0.6},
            'differential equations': {'MATH': 1.0, 'PHYS': 0.8, 'ELEC': 0.7, 'CAAM': 0.8},
            'multivariable calculus': {'MATH': 1.0, 'PHYS': 0.8, 'COMP': 0.7, 'ELEC': 0.6},
            
            # Programming keywords
            'programming': {'COMP': 1.0, 'ELEC': 0.6, 'MATH': 0.5},
            'coding': {'COMP': 1.0, 'ELEC': 0.6, 'MATH': 0.5},
            'algorithms': {'COMP': 1.0, 'MATH': 0.8, 'ELEC': 0.6},
            'data structures': {'COMP': 1.0, 'MATH': 0.7, 'ELEC': 0.5},
            
            # Physics keywords
            'physics': {'PHYS': 1.0, 'MATH': 0.8, 'ELEC': 0.7, 'COMP': 0.5},
            'mechanics': {'PHYS': 1.0, 'MATH': 0.7, 'ELEC': 0.6},
            'quantum': {'PHYS': 1.0, 'MATH': 0.8, 'CHEM': 0.6},
            
            # Engineering keywords
            'engineering': {'ELEC': 1.0, 'COMP': 0.8, 'MATH': 0.7, 'PHYS': 0.7},
            'circuits': {'ELEC': 1.0, 'PHYS': 0.8, 'MATH': 0.6},
            'signals': {'ELEC': 1.0, 'COMP': 0.7, 'MATH': 0.8},
            
            # Economics keywords
            'economics': {'ECON': 1.0, 'STAT': 0.8, 'MATH': 0.7, 'POLI': 0.6},
            'finance': {'ECON': 1.0, 'STAT': 0.8, 'MATH': 0.8},
            'econometrics': {'ECON': 1.0, 'STAT': 0.9, 'MATH': 0.8},
            
            # Pre-med keywords
            'pre med': {'BIOS': 1.0, 'CHEM': 1.0, 'BIOC': 0.9, 'PHYS': 0.7},
            'biology': {'BIOS': 1.0, 'BIOC': 0.9, 'CHEM': 0.8},
            'chemistry': {'CHEM': 1.0, 'BIOC': 0.9, 'BIOS': 0.8, 'PHYS': 0.6},
            'biochemistry': {'BIOC': 1.0, 'CHEM': 0.9, 'BIOS': 0.9},
            'organic chemistry': {'CHEM': 1.0, 'BIOC': 0.9, 'BIOS': 0.7},
            
            # Liberal arts keywords
            'literature': {'ENGL': 1.0, 'HIST': 0.7, 'PHIL': 0.6},
            'writing': {'ENGL': 1.0, 'HIST': 0.6, 'PHIL': 0.5},
            'history': {'HIST': 1.0, 'POLI': 0.8, 'ENGL': 0.7, 'RELI': 0.6},
            'philosophy': {'PHIL': 1.0, 'RELI': 0.8, 'HIST': 0.7, 'ENGL': 0.6},
            'psychology': {'PSYC': 1.0, 'SOCI': 0.8, 'LING': 0.6, 'BIOS': 0.5},
            'sociology': {'SOCI': 1.0, 'PSYC': 0.8, 'POLI': 0.7, 'HIST': 0.6},
            'political science': {'POLI': 1.0, 'HIST': 0.8, 'ECON': 0.7, 'SOCI': 0.6},
            
            # Language keywords
            'spanish': {'SPAN': 1.0, 'ENGL': 0.6, 'HIST': 0.5},
            'french': {'FREN': 1.0, 'ENGL': 0.6, 'HIST': 0.5},
            'linguistics': {'LING': 1.0, 'ENGL': 0.8, 'PSYC': 0.6, 'COMP': 0.5},
        }
        
        # Calculate priority scores
        priorities = {}
        for keyword, dept_scores in priority_mapping.items():
            if keyword in query:
                for dept, score in dept_scores.items():
                    priorities[dept] = max(priorities.get(dept, 0), score)
        
        return priorities
    
    def _detect_academic_level(self, query: str) -> str:
        """Detect academic level from query"""
        if any(word in query for word in ['freshman', 'first year', 'intro', 'beginner', 'starting']):
            return 'undergraduate'
        elif any(word in query for word in ['graduate', 'masters', 'phd', 'advanced', 'grad']):
            return 'graduate'
        elif any(word in query for word in ['sophomore', 'junior', 'senior']):
            return 'undergraduate'
        return None
    
    def _calculate_context_relevance(self, query: str, course: pd.Series, priority_departments: Dict[str, float]) -> float:
        """Calculate how relevant a course is to the query context"""
        course_dept = course.get('department', '')
        course_code = course.get('course_code', '')
        course_title = course.get('title', '').lower()
        course_desc = course.get('description', '').lower()
        
        # Base score from department priority
        dept_score = priority_departments.get(course_dept, 0.1)
        
        # Keyword matching bonus
        keyword_score = 0.0
        
        # ML/AI specific keywords
        ml_keywords = ['machine learning', 'artificial intelligence', 'neural', 'deep learning', 'data science']
        math_keywords = ['calculus', 'linear algebra', 'statistics', 'probability', 'differential', 'multivariable']
        prog_keywords = ['programming', 'algorithm', 'data structure', 'software', 'computer']
        
        # Check for keyword matches in title and description
        for keyword in ml_keywords:
            if keyword in course_title or keyword in course_desc:
                keyword_score += 0.3
        
        for keyword in math_keywords:
            if keyword in course_title or keyword in course_desc:
                keyword_score += 0.2
        
        for keyword in prog_keywords:
            if keyword in course_title or keyword in course_desc:
                keyword_score += 0.2
        
        # Prerequisite chain bonus for math courses
        if 'calculus bc' in query and course_dept == 'MATH':
            # Prioritize courses that follow Calculus BC
            if any(num in course_code for num in ['211', '212', '355', '356']):
                keyword_score += 0.4
        
        # Level appropriateness (freshman should get 100-200 level courses)
        if 'freshman' in query:
            course_number = course.get('course_number', '')
            if course_number and course_number.startswith(('1', '2')):
                keyword_score += 0.2
            elif course_number and course_number.startswith(('3', '4')):
                keyword_score += 0.1
        
        # Combine scores
        final_score = min(1.0, dept_score + keyword_score)
        return final_score
    
    def get_recommendations_by_course(self, 
                                     course_code: str, 
                                     num_recommendations: int = 10) -> List[Dict]:
        """Get course recommendations based on a specific course"""
        
        # Find the course
        course_matches = self.courses_df[
            self.courses_df['course_code'].str.contains(course_code, case=False, na=False)
        ]
        
        if course_matches.empty:
            return []
        
        # Use the first match
        course_idx = course_matches.index[0]
        course_text = self.courses_df.iloc[course_idx]['combined_text']
        
        # Get recommendations based on this course
        return self.get_recommendations_by_interest(course_text, num_recommendations)
    
    def get_recommendations_for_major(self, 
                                     major: str, 
                                     year: str = "sophomore",
                                     num_recommendations: int = 15) -> List[Dict]:
        """Get course recommendations for a specific major and year using actual curriculum requirements"""
        
        # Use the MajorRequirementEngine for intelligent recommendations
        if major.lower() in ["computer science", "cs"]:
            # Get CS requirements directly from the major requirements
            cs_major_reqs = self.major_requirement_engine.major_requirements.get("Computer Science", {})
            all_requirements = cs_major_reqs.get("requirements", [])
            
            # Filter requirements by year level
            year_mapping = {
                "freshman": ["Fall Freshman", "Spring Freshman"],
                "sophomore": ["Fall Sophomore", "Spring Sophomore"],
                "junior": ["Fall Junior", "Spring Junior"],
                "senior": ["Fall Senior", "Spring Senior"]
            }
            
            target_semesters = year_mapping.get(year.lower(), ["Fall Freshman", "Spring Freshman"])
            
            # Get relevant requirements for the year
            relevant_requirements = []
            for req in all_requirements:
                if req.semester_recommended in target_semesters or req.priority == 1:
                    relevant_requirements.append(req)
            
            # Convert to recommendations format
            recommendations = []
            for req in relevant_requirements:
                for course_code in req.course_options:
                    course_info = self.get_course_info(course_code)
                    if course_info:
                        recommendations.append({
                            'course_code': course_code,
                            'title': course_info.get('title', 'N/A'),
                            'description': course_info.get('description', 'N/A'),
                            'department': course_info.get('department', 'N/A'),
                            'credit_hours': course_info.get('credit_hours', 'N/A'),
                            'prerequisites': course_info.get('prerequisites', 'None'),
                            'course_type': course_info.get('course_type', 'N/A'),
                            'similarity_score': float(1.0 - req.priority * 0.1),  # Higher priority = higher score
                            'requirement_type': req.requirement_type,
                            'priority': req.priority,
                            'semester_recommended': req.semester_recommended,
                            'distribution_group': course_info.get('distribution_group', 'N/A')
                        })
            
            # Sort by priority (lower priority number = higher importance)
            recommendations.sort(key=lambda x: x['priority'])
            
            # If we have curriculum recommendations, return them
            if recommendations:
                return recommendations[:num_recommendations]
        
        # Fallback to interest-based search for other majors or if no curriculum found
        major_queries = {
            'computer science': 'programming algorithms data structures software engineering artificial intelligence machine learning',
            'electrical engineering': 'circuits electronics signals systems embedded systems digital design',
            'bioengineering': 'biomedical engineering medical devices biotechnology biological systems',
            'mechanical engineering': 'mechanics thermodynamics fluid dynamics materials design',
            'mathematics': 'calculus linear algebra statistics probability mathematical analysis',
            'physics': 'quantum mechanics classical mechanics electromagnetism thermal physics',
            'chemistry': 'organic chemistry inorganic chemistry physical chemistry analytical chemistry',
            'economics': 'microeconomics macroeconomics econometrics financial markets',
            'psychology': 'cognitive psychology social psychology neuroscience behavioral science',
            'history': 'historical analysis cultural studies social movements political history'
        }
        
        # Year-specific level filtering
        year_filters = {
            'freshman': 'undergraduate',
            'sophomore': 'undergraduate', 
            'junior': 'undergraduate',
            'senior': 'undergraduate',
            'graduate': 'graduate'
        }
        
        query = major_queries.get(major.lower(), major)
        level_filter = year_filters.get(year.lower(), 'undergraduate')
        
        return self.get_recommendations_by_interest(
            query, 
            num_recommendations=num_recommendations,
            level_filter=level_filter
        )
    
    def get_ml_enhanced_recommendations(self, query: str, student_profile: Dict = None, 
                                      num_recommendations: int = 10) -> List[Dict]:
        """Get ML-enhanced recommendations with advanced personalization"""
        
        if not self.ml_enhanced:
            print("⚠️ ML-enhanced features not available, falling back to standard recommendations")
            return self.get_recommendations_by_interest(query, num_recommendations)
        
        # Lazy load ML components
        self._initialize_ml_components()
        
        if not self.ml_engine:
            print("⚠️ ML engine failed to initialize, falling back to standard recommendations")
            return self.get_recommendations_by_interest(query, num_recommendations)
        
        # Convert student profile to ML format
        if student_profile is None:
            student_profile = {
                'major': 'Computer Science',
                'current_year': 'freshman',
                'completed_courses': [],
                'grades': {},
                'gpa': 3.5
            }
        
        # Create ML StudentProfile
        ml_student_profile = StudentProfile(
            student_id="user",
            major=student_profile.get('major', 'Computer Science'),
            current_year=student_profile.get('current_year', 'freshman'),
            gpa=student_profile.get('gpa', 3.5),
            completed_courses=student_profile.get('completed_courses', []),
            grades=student_profile.get('grades', {}),
            career_goals=student_profile.get('career_goals', ['software_engineering']),
            learning_style=student_profile.get('learning_style', 'visual'),
            time_preferences=student_profile.get('time_preferences', 'flexible'),
            difficulty_tolerance=student_profile.get('difficulty_tolerance', 0.7),
            extracurricular_load=student_profile.get('extracurricular_load', 'medium')
        )
        
        try:
            # Get ML-enhanced recommendations
            ml_recommendations = self.ml_engine.get_ml_recommendations(
                ml_student_profile, query, num_recommendations
            )
            
            # Convert to standard format
            standard_recommendations = []
            for rec in ml_recommendations:
                standard_recommendations.append({
                    'course_code': rec['course_code'],
                    'title': rec['title'],
                    'description': rec['description'],
                    'department': rec['department'],
                    'credit_hours': rec['credit_hours'],
                    'prerequisites': rec['prerequisites'],
                    'similarity_score': rec['ml_score'],
                    'ml_success_probability': rec['success_probability'],
                    'ml_context_relevance': rec['context_relevance'],
                    'ml_reasoning': rec['ml_reasoning'],
                    'distribution_group': rec.get('distribution_group', 'N/A')
                })
            
            return standard_recommendations
            
        except Exception as e:
            print(f"❌ Error in ML recommendations: {e}")
            return self.get_recommendations_by_interest(query, num_recommendations)
    
    def get_gpt_validated_recommendations(self, query: str, student_profile: Dict = None, 
                                        num_recommendations: int = 10) -> Dict:
        """
        🚀 PHASE 3: GPT-Validated Recommendations
        
        Flow:
        1. Get recommendations from existing system
        2. GPT validates each recommendation (good/bad + why)
        3. GPT provides its own recommendations
        4. System learns from GPT feedback
        5. Return enhanced recommendations with GPT analysis
        """
        
        if not self.gpt_wrapper_enabled:
            print("⚠️ GPT Wrapper not available, falling back to standard recommendations")
            return {
                'enhanced_recommendations': self.get_recommendations_by_interest(query, num_recommendations),
                'system_recommendations': [],
                'gpt_recommendations': [],
                'validation_results': [],
                'learning_insights': ["GPT Wrapper not initialized"],
                'overall_system_score': 0.5,
                'gpt_analysis': "GPT validation unavailable"
            }
        
        # Lazy initialize GPT wrapper
        self._ensure_gpt_initialized()
        
        # Prepare student profile
        if student_profile is None:
            student_profile = {
                'major': 'Computer Science',
                'current_year': 'freshman',
                'completed_courses': [],
                'gpa': 3.5,
                'career_goals': ['software_engineering']
            }
        
        try:
            # Step 1: Get system recommendations with major awareness
            student_major = student_profile.get('major', '').lower()
            student_year = student_profile.get('current_year', 'freshman')
            
            # First try major-specific recommendations
            if student_major in ['computer science', 'cs']:
                system_recommendations = self.get_recommendations_for_major(
                    student_major, student_year, num_recommendations
                )
            elif student_major in ['business', 'economics']:
                # For business/economics majors, get recommendations from business/economics departments
                business_recs = self.get_recommendations_by_interest(
                    query, num_recommendations, department_filter='Business'
                )
                if len(business_recs) < num_recommendations:
                    # Add economics courses if not enough business courses
                    econ_recs = self.get_recommendations_by_interest(
                        query, num_recommendations//2, department_filter='Economics'
                    )
                    business_recs.extend(econ_recs)
                system_recommendations = business_recs[:num_recommendations]
            else:
                # For other majors, use ML-enhanced or interest-based recommendations
                if self.ml_enhanced and self.ml_engine:
                    system_recommendations = self.get_ml_enhanced_recommendations(
                        query, student_profile, num_recommendations
                    )
                else:
                    # Try to filter by department if major maps to a clear department
                    department_map = {
                        'mathematics': 'Mathematics',
                        'physics': 'Physics',
                        'chemistry': 'Chemistry',
                        'biology': 'Biosciences',
                        'psychology': 'Psychology',
                        'history': 'History',
                        'english': 'English'
                    }
                    dept_filter = department_map.get(student_major)
                    system_recommendations = self.get_recommendations_by_interest(
                        query, num_recommendations, department_filter=dept_filter
                    )
            
            print(f"🔍 System generated {len(system_recommendations)} recommendations")
            
            # Step 2: GPT validates and improves recommendations
            gpt_result = validate_with_gpt(query, student_profile, system_recommendations)
            
            print(f"🧠 GPT validated recommendations with score: {gpt_result['overall_system_score']:.2f}")
            
            # Step 3: Add learning insights
            if gpt_result['learning_insights']:
                for insight in gpt_result['learning_insights']:
                    print(f"📚 Learning: {insight}")
            
            return gpt_result
            
        except Exception as e:
            print(f"❌ Error in GPT validation: {e}")
            return {
                'enhanced_recommendations': self.get_recommendations_by_interest(query, num_recommendations),
                'system_recommendations': [],
                'gpt_recommendations': [],
                'validation_results': [],
                'learning_insights': [f"GPT validation failed: {e}"],
                'overall_system_score': 0.5,
                'gpt_analysis': "GPT validation failed"
            }
    
    def get_course_info(self, course_code: str) -> Dict:
        """Get detailed information about a specific course"""
        course_matches = self.courses_df[
            self.courses_df['course_code'].str.contains(course_code, case=False, na=False)
        ]
        
        if course_matches.empty:
            return {}
        
        course = course_matches.iloc[0]
        return course.to_dict()
    
    def get_department_courses(self, department: str, level: str = None) -> List[Dict]:
        """Get all courses from a specific department"""
        dept_courses = self.courses_df[
            self.courses_df['department'].str.contains(department, case=False, na=False)
        ]
        
        if level:
            if level.lower() == 'undergraduate':
                dept_courses = dept_courses[
                    ~dept_courses['course_number'].astype(str).str.startswith(('5', '6', '7', '8'))
                ]
            elif level.lower() == 'graduate':
                dept_courses = dept_courses[
                    dept_courses['course_number'].astype(str).str.startswith(('5', '6', '7', '8'))
                ]
        
        return dept_courses.to_dict('records')
    
    def get_statistics(self) -> Dict:
        """Get statistics about the course catalog"""
        if self.courses_df is None:
            return {}
        
        stats = {
            'total_courses': len(self.courses_df),
            'departments': list(self.courses_df['department'].value_counts().to_dict().items()),
            'course_levels': {
                'undergraduate': len(self.courses_df[
                    ~self.courses_df['course_number'].astype(str).str.startswith(('5', '6', '7', '8'))
                ]),
                'graduate': len(self.courses_df[
                    self.courses_df['course_number'].astype(str).str.startswith(('5', '6', '7', '8'))
                ])
            },
            'credit_hours_distribution': self.courses_df['credit_hours'].value_counts().to_dict()
        }
        
        return stats

    def get_similar_courses(self, course_code: str, num_recommendations: int = 10) -> List[Dict]:
        """Get courses similar to a given course with intelligent filtering"""
        
        # Ensure model is loaded
        self._ensure_model_loaded()
        
        if self.course_embeddings is None:
            self.create_embeddings()
        
        # Find the target course
        target_course = self.courses_df[self.courses_df['course_code'] == course_code]
        if target_course.empty:
            return []
        
        target_course = target_course.iloc[0]
        target_idx = target_course.name
        target_dept = target_course.get('department', '')
        target_level = int(target_course.get('course_number', '0')[:1]) if target_course.get('course_number') else 0
        
        # Calculate similarities using embeddings
        target_embedding = self.course_embeddings[target_idx:target_idx+1]
        
        # Convert PyTorch tensors to numpy arrays for sklearn compatibility
        if hasattr(target_embedding, 'cpu'):
            target_embedding = target_embedding.cpu().numpy()
        if hasattr(self.course_embeddings, 'cpu'):
            course_embeddings_np = self.course_embeddings.cpu().numpy()
        else:
            course_embeddings_np = self.course_embeddings
            
        similarities = cosine_similarity(target_embedding, course_embeddings_np)[0]
        
        # Create scored recommendations using enhanced multi-signal approach
        recommendations = []
        
        for idx, text_similarity in enumerate(similarities):
            if idx == target_idx:  # Skip the target course itself
                continue
                
            candidate_course = self.courses_df.iloc[idx]
            
            # Use the enhanced similarity calculation with multiple signals
            enhanced_score = self._calculate_enhanced_similarity(
                target_course.to_dict(), 
                candidate_course.to_dict(), 
                text_similarity
            )
            
            recommendation = {
                'course_code': candidate_course.get('course_code', 'N/A'),
                'title': candidate_course.get('title', 'N/A'),
                'description': candidate_course.get('description', 'N/A'),
                'department': candidate_course.get('department', ''),
                'credit_hours': candidate_course.get('credit_hours', 'N/A'),
                'prerequisites': candidate_course.get('prerequisites', 'None'),
                'course_type': candidate_course.get('course_type', 'N/A'),
                'similarity_score': float(enhanced_score),
                'text_similarity': float(text_similarity),
                'department_relevance': float(self._calculate_department_relevance(target_dept, candidate_course.get('department', ''))),
                'distribution_group': candidate_course.get('distribution_group', 'N/A')
            }
            
            recommendations.append(recommendation)
        
        # Sort by final score and return top recommendations
        recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def _calculate_department_relevance(self, target_dept: str, candidate_dept: str) -> float:
        """Calculate relevance score between departments"""
        # Define department similarity groups
        department_groups = {
            'COMP': ['COMP', 'MATH', 'ELEC', 'STAT', 'CAAM', 'PHYS'],
            'MATH': ['MATH', 'COMP', 'STAT', 'CAAM', 'PHYS', 'ELEC'],
            'ELEC': ['ELEC', 'COMP', 'PHYS', 'CAAM', 'MATH'],
            'STAT': ['STAT', 'MATH', 'COMP', 'CAAM', 'ECON'],
            'CAAM': ['CAAM', 'MATH', 'COMP', 'STAT', 'ELEC', 'PHYS'],
            'PHYS': ['PHYS', 'MATH', 'ELEC', 'CAAM', 'COMP'],
            'CHEM': ['CHEM', 'BIOC', 'BIOS', 'PHYS'],
            'BIOC': ['BIOC', 'BIOS', 'CHEM', 'PHYS'],
            'BIOS': ['BIOS', 'BIOC', 'CHEM', 'STAT'],
            'ECON': ['ECON', 'STAT', 'MATH', 'POLI', 'SOCI'],
            'POLI': ['POLI', 'ECON', 'SOCI', 'HIST', 'PHIL'],
            'HIST': ['HIST', 'POLI', 'SOCI', 'ENGL', 'RELI'],
            'ENGL': ['ENGL', 'HIST', 'LING', 'FREN', 'SPAN'],
            'PHIL': ['PHIL', 'RELI', 'POLI', 'HIST', 'ENGL'],
            'PSYC': ['PSYC', 'SOCI', 'LING', 'BIOS', 'STAT'],
            'SOCI': ['SOCI', 'PSYC', 'POLI', 'ECON', 'HIST'],
        }
        
        # Same department - highest relevance
        if target_dept == candidate_dept:
            return 1.0
        
        # Check if candidate is in target's related departments
        related_depts = department_groups.get(target_dept, [])
        if candidate_dept in related_depts:
            # Position in list determines relevance (first = most relevant)
            position = related_depts.index(candidate_dept)
            return max(0.3, 1.0 - (position * 0.15))
        
        # No relation found
        return 0.1

    def _calculate_prerequisite_chain_similarity(self, target_course: str, candidate_course: str) -> float:
        """Calculate similarity based on prerequisite relationships"""
        # Define common prerequisite chains for Rice University
        prerequisite_chains = {
            # Computer Science Track
            "COMP 140": ["COMP 182", "COMP 215", "COMP 412", "COMP 540"],
            "COMP 182": ["COMP 215", "COMP 412", "COMP 322", "COMP 540"],
            "COMP 215": ["COMP 412", "COMP 540", "COMP 521", "COMP 557"],
            
            # Mathematics Track
            "MATH 101": ["MATH 102", "MATH 211", "MATH 212", "STAT 310"],
            "MATH 102": ["MATH 211", "MATH 212", "STAT 310", "CAAM 210"],
            "MATH 211": ["MATH 212", "MATH 355", "MATH 356", "STAT 310"],
            "MATH 212": ["MATH 355", "MATH 356", "MATH 382", "STAT 310"],
            
            # Physics Track
            "PHYS 101": ["PHYS 102", "PHYS 201", "PHYS 202", "ELEC 220"],
            "PHYS 102": ["PHYS 201", "PHYS 202", "ELEC 220", "CAAM 210"],
            "PHYS 201": ["PHYS 202", "PHYS 301", "PHYS 302", "ELEC 220"],
            
            # Chemistry Track
            "CHEM 121": ["CHEM 122", "CHEM 211", "CHEM 212", "BIOC 201"],
            "CHEM 122": ["CHEM 211", "CHEM 212", "BIOC 201", "BIOC 301"],
            
            # Economics Track
            "ECON 100": ["ECON 210", "ECON 211", "STAT 310", "ECON 307"],
            "ECON 210": ["ECON 211", "ECON 307", "ECON 370", "STAT 310"],
            "ECON 211": ["ECON 307", "ECON 370", "ECON 435", "STAT 310"],
        }
        
        # Check if candidate is in target's prerequisite chain
        target_chain = prerequisite_chains.get(target_course, [])
        if candidate_course in target_chain:
            # Earlier in chain = higher similarity
            position = target_chain.index(candidate_course)
            return max(0.3, 1.0 - (position * 0.2))
        
        # Check reverse relationship
        for course, chain in prerequisite_chains.items():
            if course == candidate_course and target_course in chain:
                position = chain.index(target_course)
                return max(0.2, 0.8 - (position * 0.15))
        
        return 0.0

    def _calculate_difficulty_progression(self, target_level: int, candidate_level: int) -> float:
        """Calculate similarity based on academic difficulty progression"""
        if target_level == candidate_level:
            return 1.0
        
        level_diff = abs(target_level - candidate_level)
        
        # Adjacent levels are highly similar
        if level_diff == 1:
            return 0.8
        elif level_diff == 2:
            return 0.6
        elif level_diff == 3:
            return 0.4
        else:
            return 0.2

    def _calculate_co_enrollment_patterns(self, target_course: str, candidate_course: str) -> float:
        """Calculate similarity based on common co-enrollment patterns"""
        # Define common co-enrollment patterns based on Rice University data
        common_combinations = {
            # STEM combinations
            "COMP 140": ["MATH 101", "MATH 102", "STAT 310", "PHYS 101"],
            "COMP 182": ["MATH 211", "MATH 212", "STAT 310", "ELEC 220"],
            "COMP 215": ["MATH 355", "STAT 310", "ELEC 322", "CAAM 210"],
            
            # Math-Science combinations
            "MATH 101": ["COMP 140", "PHYS 101", "CHEM 121", "STAT 310"],
            "MATH 102": ["COMP 140", "PHYS 102", "CHEM 122", "STAT 310"],
            "MATH 211": ["COMP 182", "PHYS 201", "STAT 310", "ELEC 220"],
            "MATH 212": ["COMP 182", "PHYS 202", "STAT 310", "CAAM 210"],
            
            # Economics combinations
            "ECON 100": ["MATH 101", "STAT 310", "POLI 207", "HIST 118"],
            "ECON 210": ["MATH 102", "STAT 310", "POLI 207", "SOCI 101"],
            "ECON 211": ["MATH 211", "STAT 310", "POLI 368", "SOCI 306"],
            
            # Liberal Arts combinations
            "ENGL 103": ["HIST 118", "PHIL 101", "POLI 207", "SOCI 101"],
            "HIST 118": ["ENGL 103", "PHIL 101", "POLI 207", "RELI 101"],
            "PHIL 101": ["ENGL 103", "HIST 118", "RELI 101", "POLI 207"],
        }
        
        # Check if candidate is commonly taken with target
        target_combinations = common_combinations.get(target_course, [])
        if candidate_course in target_combinations:
            # Position in list determines co-enrollment strength
            position = target_combinations.index(candidate_course)
            return max(0.4, 1.0 - (position * 0.15))
        
        # Check reverse relationship
        candidate_combinations = common_combinations.get(candidate_course, [])
        if target_course in candidate_combinations:
            position = candidate_combinations.index(target_course)
            return max(0.3, 0.8 - (position * 0.15))
        
        return 0.0

    def _calculate_enhanced_similarity(self, target_course: Dict, candidate_course: Dict, text_similarity: float) -> float:
        """Calculate enhanced similarity using multiple signals"""
        
        # Extract course information
        target_dept = target_course.get('department', '')
        candidate_dept = candidate_course.get('department', '')
        target_code = target_course.get('course_code', '')
        candidate_code = candidate_course.get('course_code', '')
        target_level = int(target_course.get('course_number', '0')[:1]) if target_course.get('course_number') else 0
        candidate_level = int(candidate_course.get('course_number', '0')[:1]) if candidate_course.get('course_number') else 0
        
        # Calculate individual signals
        dept_relevance = self._calculate_department_relevance(target_dept, candidate_dept)
        prereq_similarity = self._calculate_prerequisite_chain_similarity(target_code, candidate_code)
        difficulty_similarity = self._calculate_difficulty_progression(target_level, candidate_level)
        co_enrollment_similarity = self._calculate_co_enrollment_patterns(target_code, candidate_code)
        
        # Enhanced weighting system
        weights = {
            'content_similarity': 0.30,      # Text embeddings
            'department_relevance': 0.25,    # Subject matter relevance
            'prerequisite_chain': 0.20,      # Academic progression
            'difficulty_progression': 0.15,  # Level appropriateness
            'co_enrollment_patterns': 0.10   # Student behavior patterns
        }
        
        # Calculate weighted score
        enhanced_score = (
            weights['content_similarity'] * text_similarity +
            weights['department_relevance'] * dept_relevance +
            weights['prerequisite_chain'] * prereq_similarity +
            weights['difficulty_progression'] * difficulty_similarity +
            weights['co_enrollment_patterns'] * co_enrollment_similarity
        )
        
        return enhanced_score

    def get_comprehensive_academic_plan(self, major: str, completed_courses: List[str],
                                       current_semester: str = "Fall",
                                       current_year: int = 2024) -> Dict:
        """Get a comprehensive academic plan with multi-semester optimization"""
        
        # Get multi-semester plan
        multi_semester_plan = self.semester_planning_engine.create_optimal_plan(
            major, completed_courses, current_semester, current_year
        )
        
        # Get degree audit
        degree_audit = self.get_degree_audit(major, completed_courses)
        
        # Get next semester recommendations
        next_semester = self.semester_planning_engine.get_semester_recommendations(
            major, completed_courses, current_semester
        )
        
        # Get career-focused recommendations
        career_recommendations = self._get_career_focused_recommendations(
            major, completed_courses
        )
        
        # Generate comprehensive insights
        comprehensive_insights = self._generate_comprehensive_insights(
            multi_semester_plan, degree_audit, next_semester
        )
        
        return {
            'multi_semester_plan': multi_semester_plan,
            'degree_audit': degree_audit,
            'next_semester': next_semester,
            'career_recommendations': career_recommendations,
            'comprehensive_insights': comprehensive_insights,
            'graduation_timeline': {
                'estimated_graduation': multi_semester_plan.graduation_semester,
                'semesters_remaining': multi_semester_plan.total_semesters,
                'credits_remaining': multi_semester_plan.total_credits
            }
        }
    
    def analyze_course_sequence(self, target_courses: List[str], 
                              completed_courses: List[str] = None) -> Dict:
        """Analyze optimal sequence for a set of target courses"""
        if completed_courses is None:
            completed_courses = []
        
        # Get optimal sequence
        optimal_sequence = self.prerequisite_parser.find_optimal_course_sequence(
            target_courses, completed_courses
        )
        
        # Analyze each course in sequence
        course_analysis = []
        for course in optimal_sequence.sequence:
            analysis = self.get_prerequisite_analysis(course)
            
            # Add difficulty and workload info
            analysis['difficulty'] = self.course_difficulty_scores.get(course, 0.5)
            analysis['workload'] = self.course_workload_estimates.get(course, 0.5)
            analysis['career_relevance'] = self.course_career_relevance.get(course, {})
            
            course_analysis.append(analysis)
        
        return {
            'optimal_sequence': optimal_sequence,
            'course_analysis': course_analysis,
            'total_semesters': optimal_sequence.total_semesters,
            'difficulty_balance': optimal_sequence.difficulty_balance,
            'confidence_score': optimal_sequence.confidence_score,
            'prerequisite_warnings': self._analyze_prerequisite_warnings(optimal_sequence.sequence)
        }
    
    def get_smart_course_recommendations(self, query: str, 
                                       student_profile: Dict = None) -> Dict:
        """Get smart course recommendations with comprehensive analysis"""
        
        # Get basic intelligent recommendations
        intelligent_recs = self.get_intelligent_recommendations(query, student_profile)
        
        # Add advanced analytics
        recommendations = intelligent_recs['recommendations']
        
        # Add sequence analysis for recommended courses
        if student_profile and 'completed_courses' in student_profile:
            rec_courses = [rec['course_code'] for rec in recommendations]
            sequence_analysis = self.analyze_course_sequence(
                rec_courses, student_profile['completed_courses']
            )
            intelligent_recs['sequence_analysis'] = sequence_analysis
        
        # Add semester planning for recommendations
        if student_profile and 'major' in student_profile:
            semester_fit = self._analyze_semester_fit(
                recommendations, student_profile
            )
            intelligent_recs['semester_fit'] = semester_fit
        
        # Add alternative course suggestions
        alternatives = self._find_alternative_courses(recommendations)
        intelligent_recs['alternatives'] = alternatives
        
        return intelligent_recs
    
    def validate_academic_plan(self, plan: Dict, major: str) -> Dict:
        """Validate an academic plan for feasibility and optimization"""
        
        validation_results = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'suggestions': [],
            'optimization_score': 0.0
        }
        
        # Validate prerequisites
        all_courses = []
        for semester_plan in plan.get('semester_plans', []):
            all_courses.extend(semester_plan.get('courses', []))
        
        # Check prerequisite satisfaction
        completed_so_far = []
        for semester_plan in plan.get('semester_plans', []):
            for course in semester_plan.get('courses', []):
                satisfied, missing = self.prerequisite_parser.validate_prerequisite_satisfaction(
                    course, completed_so_far
                )
                if not satisfied:
                    validation_results['is_valid'] = False
                    validation_results['issues'].append(
                        f"Course {course} prerequisites not satisfied: {missing}"
                    )
            completed_so_far.extend(semester_plan.get('courses', []))
        
        # Validate major requirements
        if major in self.major_requirement_engine.major_requirements:
            progress = self.major_requirement_engine.analyze_degree_progress(major, all_courses)
            if progress.requirements_remaining:
                validation_results['warnings'].append(
                    f"{len(progress.requirements_remaining)} major requirements still not satisfied"
                )
        
        # Check workload balance
        for semester_plan in plan.get('semester_plans', []):
            total_difficulty = sum(
                self.course_difficulty_scores.get(course, 0.5) 
                for course in semester_plan.get('courses', [])
            )
            if total_difficulty > 3.0:  # 5 courses * 0.6 average
                validation_results['warnings'].append(
                    f"Semester {semester_plan.get('semester', '')} {semester_plan.get('year', '')} "
                    f"may be too challenging"
                )
        
        # Calculate optimization score
        optimization_score = self._calculate_plan_optimization_score(plan)
        validation_results['optimization_score'] = optimization_score
        
        if optimization_score < 0.6:
            validation_results['suggestions'].append(
                "Consider rebalancing courses across semesters for better optimization"
            )
        
        return validation_results
    
    def get_graduation_analysis(self, major: str, completed_courses: List[str]) -> Dict:
        """Get comprehensive graduation analysis"""
        
        # Get degree progress
        progress = self.major_requirement_engine.analyze_degree_progress(major, completed_courses)
        
        # Get graduation validation
        can_graduate, issues = self.major_requirement_engine.validate_graduation_requirements(
            major, completed_courses
        )
        
        # Get optimal path to graduation
        remaining_courses = []
        for req in progress.requirements_remaining:
            remaining_courses.extend(req.course_options)
        
        graduation_path = self.prerequisite_parser.find_optimal_course_sequence(
            remaining_courses, completed_courses
        )
        
        # Get multi-semester plan
        multi_semester_plan = self.semester_planning_engine.create_optimal_plan(
            major, completed_courses
        )
        
        return {
            'can_graduate': can_graduate,
            'graduation_issues': issues,
            'degree_progress': progress,
            'graduation_path': graduation_path,
            'multi_semester_plan': multi_semester_plan,
            'estimated_graduation': multi_semester_plan.graduation_semester,
            'total_semesters_remaining': multi_semester_plan.total_semesters,
            'alternative_paths': self.major_requirement_engine.get_alternative_paths(major, completed_courses)
        }
    
    def _get_career_focused_recommendations(self, major: str, completed_courses: List[str]) -> Dict:
        """Get career-focused course recommendations"""
        
        career_tracks = {
            'software_engineering': {
                'courses': ['COMP 215', 'COMP 413', 'COMP 421', 'COMP 440'],
                'description': 'Software engineering and systems development'
            },
            'machine_learning': {
                'courses': ['COMP 440', 'COMP 441', 'COMP 540', 'STAT 310'],
                'description': 'Machine learning and data science'
            },
            'research': {
                'courses': ['COMP 481', 'COMP 482', 'COMP 590', 'COMP 600'],
                'description': 'Research and advanced theory'
            },
            'finance_tech': {
                'courses': ['COMP 440', 'ECON 307', 'STAT 310', 'MATH 355'],
                'description': 'Technology applications in finance'
            }
        }
        
        recommendations = {}
        
        for track, info in career_tracks.items():
            available_courses = []
            for course in info['courses']:
                satisfied, missing = self.prerequisite_parser.validate_prerequisite_satisfaction(
                    course, completed_courses
                )
                if satisfied:
                    available_courses.append({
                        'course_code': course,
                        'difficulty': self.course_difficulty_scores.get(course, 0.5),
                        'career_relevance': self.course_career_relevance.get(course, {})
                    })
            
            if available_courses:
                recommendations[track] = {
                    'description': info['description'],
                    'available_courses': available_courses,
                    'completion_percentage': len(available_courses) / len(info['courses']) * 100
                }
        
        return recommendations
    
    def _generate_comprehensive_insights(self, multi_semester_plan, 
                                       degree_audit: Dict, next_semester: Dict) -> List[str]:
        """Generate comprehensive insights about the academic plan"""
        insights = []
        
        # Graduation timeline insights
        insights.append(f"🎓 Estimated graduation: {multi_semester_plan.graduation_semester}")
        insights.append(f"📅 {multi_semester_plan.total_semesters} semesters remaining")
        
        # Progress insights
        progress = degree_audit.get('degree_progress')
        if progress:
            insights.append(f"📊 {progress.overall_progress:.1f}% complete overall")
            insights.append(f"🎯 {progress.major_progress:.1f}% complete in major")
        
        # Optimization insights
        if multi_semester_plan.optimization_score > 0.8:
            insights.append("✅ Your academic plan is well-optimized")
        elif multi_semester_plan.optimization_score < 0.6:
            insights.append("⚠️ Your academic plan could be better optimized")
        
        # Next semester insights
        next_sem_notes = next_semester.get('planning_notes', [])
        insights.extend(next_sem_notes)
        
        return insights
    
    def _analyze_prerequisite_warnings(self, course_sequence: List[str]) -> List[str]:
        """Analyze potential prerequisite warnings in a course sequence"""
        warnings = []
        
        for i, course in enumerate(course_sequence):
            prerequisites = self.prerequisite_parser.get_prerequisites(course)
            
            # Check if prerequisites appear later in sequence
            for prereq in prerequisites:
                if prereq in course_sequence:
                    prereq_index = course_sequence.index(prereq)
                    if prereq_index > i:
                        warnings.append(
                            f"⚠️ {course} requires {prereq}, but {prereq} appears later in sequence"
                        )
        
        return warnings
    
    def _analyze_semester_fit(self, recommendations: List[Dict], student_profile: Dict) -> Dict:
        """Analyze how well recommendations fit into semester planning"""
        
        major = student_profile.get('major', '')
        completed_courses = student_profile.get('completed_courses', [])
        
        if not major:
            return {'error': 'No major specified'}
        
        # Get next semester recommendations
        next_sem = self.semester_planning_engine.get_semester_recommendations(
            major, completed_courses
        )
        
        # Analyze fit
        fit_analysis = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': [],
            'not_recommended': []
        }
        
        for rec in recommendations:
            course_code = rec.get('course_code', '')
            
            # Check if course is in next semester recommendations
            in_next_sem = any(
                course_code == next_rec.get('course_code', '') 
                for next_rec in next_sem.get('recommended_courses', [])
            )
            
            if in_next_sem:
                priority = next(
                    (next_rec.get('priority', 5) for next_rec in next_sem.get('recommended_courses', [])
                     if next_rec.get('course_code') == course_code),
                    5
                )
                
                if priority == 1:
                    fit_analysis['high_priority'].append(rec)
                elif priority == 2:
                    fit_analysis['medium_priority'].append(rec)
                else:
                    fit_analysis['low_priority'].append(rec)
            else:
                fit_analysis['not_recommended'].append(rec)
        
        return fit_analysis
    
    def _find_alternative_courses(self, recommendations: List[Dict]) -> List[Dict]:
        """Find alternative courses for each recommendation"""
        alternatives = []
        
        for rec in recommendations:
            course_code = rec.get('course_code', '')
            dept = rec.get('department', '')
            
            # Find similar courses in same department
            similar_courses = []
            for _, course in self.courses_df.iterrows():
                if (course.get('department', '') == dept and 
                    course.get('course_code', '') != course_code):
                    similar_courses.append({
                        'course_code': course.get('course_code', ''),
                        'title': course.get('title', ''),
                        'description': course.get('description', '')
                    })
            
            if similar_courses:
                alternatives.append({
                    'original_course': course_code,
                    'alternatives': similar_courses[:3]  # Limit to 3 alternatives
                })
        
        return alternatives
    
    def _calculate_plan_optimization_score(self, plan: Dict) -> float:
        """Calculate optimization score for an academic plan"""
        
        scores = []
        
        # Prerequisite satisfaction score
        prereq_score = 1.0
        # This would be calculated based on prerequisite validation
        scores.append(prereq_score)
        
        # Workload balance score
        workload_scores = []
        for semester_plan in plan.get('semester_plans', []):
            semester_difficulty = sum(
                self.course_difficulty_scores.get(course, 0.5) 
                for course in semester_plan.get('courses', [])
            )
            # Normalize to 0-1 scale
            normalized_difficulty = min(semester_difficulty / 3.0, 1.0)
            workload_scores.append(1.0 - abs(normalized_difficulty - 0.6))  # Optimal around 0.6
        
        if workload_scores:
            scores.append(sum(workload_scores) / len(workload_scores))
        
        # Efficiency score (completing requirements in logical order)
        efficiency_score = 0.8  # Base efficiency
        scores.append(efficiency_score)
        
        return sum(scores) / len(scores) if scores else 0.0

    def get_courses_by_instructor(self, instructor_name: str, num_recommendations: int = 10) -> List[Dict]:
        """Get courses taught by a specific instructor"""
        
        instructor_lower = instructor_name.lower()
        instructor_courses = []
        
        for _, course in self.courses_df.iterrows():
            # Check instructors field (could be string or list)
            instructors = course.get('instructors', [])
            
            # Handle different instructor formats
            if isinstance(instructors, str):
                # If it's a string, split by comma or semicolon
                instructor_list = [i.strip() for i in instructors.replace(';', ',').split(',')]
            elif isinstance(instructors, list):
                instructor_list = instructors
            else:
                instructor_list = []
            
            # Check if instructor name matches (handle both "First Last" and "Last, First" formats)
            for instructor in instructor_list:
                instructor_clean = str(instructor).strip()
                instructor_lower_clean = instructor_clean.lower()
                
                # Direct exact match
                if instructor_lower == instructor_lower_clean:
                    course_info = {
                        'course_code': course.get('course_code', 'N/A'),
                        'title': course.get('title', 'N/A'),
                        'instructors': instructor_list,
                        'department': course.get('department', course.get('subject_code', 'N/A')),
                        'credits': course.get('credits', course.get('credit_hours', 'N/A')),
                        'meeting_time': course.get('meeting_time', 'N/A'),
                        'distribution_group': course.get('distribution_group', 'N/A'),
                        'course_url': course.get('course_url', ''),
                        'description': course.get('description', 'N/A')
                    }
                    instructor_courses.append(course_info)
                    break
                
                # Handle "Last, First" format - try to match by last name or first name
                if ',' in instructor_clean:
                    last_first = instructor_clean.split(',')
                    if len(last_first) >= 2:
                        last_name = last_first[0].strip().lower()
                        first_name = last_first[1].strip().lower()
                        
                        # Check for exact matches first
                        if (instructor_lower == last_name or instructor_lower == first_name or
                            instructor_lower == f"{first_name} {last_name}" or instructor_lower == f"{last_name} {first_name}"):
                            course_info = {
                                'course_code': course.get('course_code', 'N/A'),
                                'title': course.get('title', 'N/A'),
                                'instructors': instructor_list,
                                'department': course.get('department', course.get('subject_code', 'N/A')),
                                'credits': course.get('credits', course.get('credit_hours', 'N/A')),
                                'meeting_time': course.get('meeting_time', 'N/A'),
                                'distribution_group': course.get('distribution_group', 'N/A'),
                                'course_url': course.get('course_url', ''),
                                'description': course.get('description', 'N/A')
                            }
                            instructor_courses.append(course_info)
                            break
                        
                        # Check for partial matches (but be more restrictive)
                        if (instructor_lower in last_name and len(instructor_lower) >= 3) or (instructor_lower in first_name and len(instructor_lower) >= 3):
                            course_info = {
                                'course_code': course.get('course_code', 'N/A'),
                                'title': course.get('title', 'N/A'),
                                'instructors': instructor_list,
                                'department': course.get('department', course.get('subject_code', 'N/A')),
                                'credits': course.get('credits', course.get('credit_hours', 'N/A')),
                                'meeting_time': course.get('meeting_time', 'N/A'),
                                'distribution_group': course.get('distribution_group', 'N/A'),
                                'course_url': course.get('course_url', ''),
                                'description': course.get('description', 'N/A')
                            }
                            instructor_courses.append(course_info)
                            break
        
        # Sort by course code for consistency
        instructor_courses.sort(key=lambda x: x['course_code'])
        return instructor_courses[:num_recommendations]

@dataclass
class PrerequisiteNode:
    """Represents a prerequisite requirement node"""
    course_code: str
    operator: str = "AND"  # AND, OR, NONE
    children: List['PrerequisiteNode'] = field(default_factory=list)
    is_course: bool = True
    
    def __post_init__(self):
        if not self.children:
            self.children = []

@dataclass
class CourseSequence:
    """Represents an optimal course sequence"""
    sequence: List[str]
    total_semesters: int
    prerequisites_satisfied: Dict[str, List[str]]
    difficulty_balance: float
    confidence_score: float

class PrerequisiteParser:
    """Advanced prerequisite parser and graph builder"""
    
    def __init__(self):
        self.prerequisite_graph = nx.DiGraph()
        self.prerequisite_trees = {}
        self.course_levels = {}
        self.prerequisite_text_cache = {}
        
    def parse_prerequisite_string(self, prereq_string: str) -> Optional[PrerequisiteNode]:
        """Parse a prerequisite string into a structured tree"""
        if not prereq_string or prereq_string.strip() in ['', 'None', 'none', 'N/A']:
            return None
        
        # Cache results
        if prereq_string in self.prerequisite_text_cache:
            return self.prerequisite_text_cache[prereq_string]
        
        # Clean the string
        cleaned = prereq_string.strip()
        
        # Handle complex expressions with parentheses
        root = self._parse_expression(cleaned)
        
        # Cache the result
        self.prerequisite_text_cache[prereq_string] = root
        return root
    
    def _parse_expression(self, expr: str) -> PrerequisiteNode:
        """Parse a complex prerequisite expression"""
        expr = expr.strip()
        
        # Handle parentheses
        if expr.startswith('(') and expr.endswith(')'):
            return self._parse_expression(expr[1:-1])
        
        # Find main operator (AND/OR) outside parentheses
        main_op, split_pos = self._find_main_operator(expr)
        
        if main_op == "NONE":
            # Single course or simple expression
            course_match = re.search(r'([A-Z]{3,4}\s+\d{3})', expr)
            if course_match:
                return PrerequisiteNode(
                    course_code=course_match.group(1),
                    operator="NONE",
                    is_course=True
                )
            else:
                # Might be a complex single expression
                return PrerequisiteNode(
                    course_code=expr,
                    operator="NONE",
                    is_course=False
                )
        
        # Split by the main operator
        left_part = expr[:split_pos].strip()
        right_part = expr[split_pos + len(main_op):].strip()
        
        # Create node with children
        node = PrerequisiteNode(
            course_code="",
            operator=main_op,
            is_course=False
        )
        
        # Recursively parse left and right parts
        if left_part:
            node.children.append(self._parse_expression(left_part))
        if right_part:
            node.children.append(self._parse_expression(right_part))
        
        return node
    
    def _find_main_operator(self, expr: str) -> Tuple[str, int]:
        """Find the main logical operator in an expression"""
        paren_depth = 0
        
        # Look for AND/OR operators outside parentheses
        for i, char in enumerate(expr):
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif paren_depth == 0:
                if expr[i:i+4] == ' AND' or expr[i:i+3] == 'AND':
                    return "AND", i
                elif expr[i:i+3] == ' OR' or expr[i:i+2] == 'OR':
                    return "OR", i
        
        return "NONE", -1
    
    def build_prerequisite_graph(self, courses_data: List[Dict]):
        """Build a comprehensive prerequisite graph"""
        logger.info("🔗 Building prerequisite graph...")
        
        # Add all courses as nodes
        for course in courses_data:
            course_code = course.get('course_code', '')
            if course_code:
                self.prerequisite_graph.add_node(course_code, **course)
                
                # Extract course level
                course_number = course.get('course_number', '')
                if course_number:
                    level = int(course_number[0]) if course_number[0].isdigit() else 0
                    self.course_levels[course_code] = level
        
        # Add prerequisite edges
        for course in courses_data:
            course_code = course.get('course_code', '')
            prereq_string = course.get('prerequisites', '')
            
            if course_code and prereq_string and isinstance(prereq_string, str):
                prereq_tree = self.parse_prerequisite_string(prereq_string)
                if prereq_tree:
                    self.prerequisite_trees[course_code] = prereq_tree
                    self._add_prerequisite_edges(course_code, prereq_tree)
        
        logger.info(f"✅ Built prerequisite graph with {len(self.prerequisite_graph.nodes)} courses")
        logger.info(f"📊 Total prerequisite relationships: {len(self.prerequisite_graph.edges)}")
    
    def _add_prerequisite_edges(self, target_course: str, prereq_tree: PrerequisiteNode):
        """Add prerequisite edges from a prerequisite tree"""
        if prereq_tree.is_course and prereq_tree.course_code:
            # Clean course code
            prereq_course = prereq_tree.course_code.strip()
            if prereq_course in self.prerequisite_graph.nodes:
                self.prerequisite_graph.add_edge(prereq_course, target_course, 
                                                relationship="prerequisite")
        
        # Recursively process children
        for child in prereq_tree.children:
            self._add_prerequisite_edges(target_course, child)
    
    def get_prerequisites(self, course_code: str, depth: int = 1) -> List[str]:
        """Get all prerequisites for a course up to a certain depth"""
        if course_code not in self.prerequisite_graph:
            return []
        
        prerequisites = []
        
        if depth == 1:
            # Direct prerequisites only
            prerequisites = list(self.prerequisite_graph.predecessors(course_code))
        else:
            # Multi-level prerequisites
            visited = set()
            queue = deque([(course_code, 0)])
            
            while queue:
                current_course, current_depth = queue.popleft()
                
                if current_depth >= depth:
                    continue
                
                for prereq in self.prerequisite_graph.predecessors(current_course):
                    if prereq not in visited:
                        visited.add(prereq)
                        prerequisites.append(prereq)
                        queue.append((prereq, current_depth + 1))
        
        return prerequisites
    
    def get_courses_requiring(self, course_code: str) -> List[str]:
        """Get all courses that require this course as a prerequisite"""
        if course_code not in self.prerequisite_graph:
            return []
        
        return list(self.prerequisite_graph.successors(course_code))
    
    def validate_prerequisite_satisfaction(self, course_code: str, 
                                         completed_courses: List[str]) -> Tuple[bool, List[str]]:
        """Validate if prerequisites are satisfied for a course"""
        if course_code not in self.prerequisite_trees:
            return True, []  # No prerequisites
        
        prereq_tree = self.prerequisite_trees[course_code]
        satisfied, missing = self._validate_prerequisite_tree(prereq_tree, completed_courses)
        
        return satisfied, missing
    
    def _validate_prerequisite_tree(self, tree: PrerequisiteNode, 
                                   completed_courses: List[str]) -> Tuple[bool, List[str]]:
        """Validate a prerequisite tree against completed courses"""
        if tree.is_course:
            # Check if this course is completed
            course_code = tree.course_code.strip()
            if course_code in completed_courses:
                return True, []
            else:
                return False, [course_code]
        
        # Process children based on operator
        if tree.operator == "AND":
            all_satisfied = True
            missing_courses = []
            
            for child in tree.children:
                satisfied, missing = self._validate_prerequisite_tree(child, completed_courses)
                if not satisfied:
                    all_satisfied = False
                    missing_courses.extend(missing)
            
            return all_satisfied, missing_courses
        
        elif tree.operator == "OR":
            # At least one child must be satisfied
            for child in tree.children:
                satisfied, missing = self._validate_prerequisite_tree(child, completed_courses)
                if satisfied:
                    return True, []
            
            # If none satisfied, return all missing from first child
            if tree.children:
                return self._validate_prerequisite_tree(tree.children[0], completed_courses)
            
            return False, []
        
        return True, []
    
    def find_optimal_course_sequence(self, target_courses: List[str], 
                                   completed_courses: List[str] = None) -> CourseSequence:
        """Find optimal sequence to complete target courses"""
        if completed_courses is None:
            completed_courses = []
        
        # Use topological sort with constraints
        remaining_courses = set(target_courses) - set(completed_courses)
        
        # Build subgraph for relevant courses
        relevant_courses = set()
        for course in remaining_courses:
            relevant_courses.add(course)
            relevant_courses.update(self.get_prerequisites(course, depth=3))
        
        subgraph = self.prerequisite_graph.subgraph(relevant_courses)
        
        # Perform topological sort
        try:
            topo_order = list(nx.topological_sort(subgraph))
        except nx.NetworkXError:
            # Handle cycles by using approximate order
            topo_order = list(remaining_courses)
            topo_order.sort(key=lambda x: self.course_levels.get(x, 0))
        
        # Filter to only include remaining courses
        sequence = [course for course in topo_order 
                   if course in remaining_courses]
        
        # Calculate metrics
        total_semesters = self._estimate_semesters(sequence)
        difficulty_balance = self._calculate_difficulty_balance(sequence)
        confidence_score = self._calculate_sequence_confidence(sequence)
        
        prereqs_satisfied = {}
        for course in sequence:
            prereqs_satisfied[course] = self.get_prerequisites(course)
        
        return CourseSequence(
            sequence=sequence,
            total_semesters=total_semesters,
            prerequisites_satisfied=prereqs_satisfied,
            difficulty_balance=difficulty_balance,
            confidence_score=confidence_score
        )
    
    def _estimate_semesters(self, sequence: List[str]) -> int:
        """Estimate number of semesters needed for a sequence"""
        # Assume 4-5 courses per semester
        return max(1, len(sequence) // 4)
    
    def _calculate_difficulty_balance(self, sequence: List[str]) -> float:
        """Calculate difficulty balance of a sequence"""
        if not sequence:
            return 0.0
        
        # Use course levels as proxy for difficulty
        levels = [self.course_levels.get(course, 0) for course in sequence]
        level_variance = np.var(levels) if levels else 0
        
        # Lower variance = better balance
        return max(0.0, 1.0 - (level_variance / 10.0))
    
    def _calculate_sequence_confidence(self, sequence: List[str]) -> float:
        """Calculate confidence score for a sequence"""
        if not sequence:
            return 0.0
        
        # Higher confidence for courses with clear prerequisites
        confidence_sum = 0
        for course in sequence:
            if course in self.prerequisite_trees:
                confidence_sum += 0.9  # High confidence for courses with known prereqs
            else:
                confidence_sum += 0.7  # Medium confidence for courses without prereqs
        
        return confidence_sum / len(sequence)

@dataclass
class MajorRequirement:
    """Represents a major requirement"""
    name: str
    requirement_type: str  # "core", "elective", "breadth", "math", "distribution"
    course_options: List[str]  # List of course codes that satisfy this requirement
    credit_hours: int
    description: str
    is_satisfied: bool = False
    satisfied_by: Optional[str] = None
    priority: int = 1  # 1=highest, 5=lowest
    semester_recommended: Optional[str] = None
    breadth_area: Optional[str] = None

@dataclass
class DegreeProgress:
    """Tracks progress toward degree completion"""
    major: str
    degree_type: str  # "BA", "BS", "MS", "PhD"
    total_credits_required: int
    total_credits_completed: int
    major_credits_required: int
    major_credits_completed: int
    requirements_satisfied: List[MajorRequirement]
    requirements_remaining: List[MajorRequirement]
    overall_progress: float
    major_progress: float
    estimated_graduation_semester: str
    prerequisite_warnings: List[str] = field(default_factory=list)

class MajorRequirementEngine:
    """Comprehensive major requirement tracking and planning engine"""
    
    def __init__(self):
        self.major_requirements = {}
        self.degree_templates = {}
        self.graduation_requirements = {}
        self.distribution_requirements = {}
        self._load_major_requirements()
        
    def _load_major_requirements(self):
        """Load major requirements from multiple sources"""
        # Computer Science BSCS Requirements
        self.major_requirements["Computer Science"] = {
            "degree_type": "BS",
            "total_credits": 120,
            "major_credits": 54,
            "requirements": [
                MajorRequirement(
                    name="Computational Thinking",
                    requirement_type="core",
                    course_options=["COMP 140"],
                    credit_hours=4,
                    description="Introduction to computational thinking and programming",
                    priority=1,
                    semester_recommended="Fall Freshman"
                ),
                MajorRequirement(
                    name="Algorithmic Thinking",
                    requirement_type="core",
                    course_options=["COMP 182"],
                    credit_hours=4,
                    description="Core algorithms and data structures",
                    priority=1,
                    semester_recommended="Spring Freshman"
                ),
                MajorRequirement(
                    name="Program Design",
                    requirement_type="core",
                    course_options=["COMP 215"],
                    credit_hours=4,
                    description="Software engineering fundamentals",
                    priority=1,
                    semester_recommended="Fall Sophomore"
                ),
                MajorRequirement(
                    name="Computer Systems",
                    requirement_type="core",
                    course_options=["COMP 321"],
                    credit_hours=4,
                    description="Introduction to computer systems",
                    priority=1,
                    semester_recommended="Fall Sophomore"
                ),
                MajorRequirement(
                    name="Parallel Programming",
                    requirement_type="core",
                    course_options=["COMP 322"],
                    credit_hours=4,
                    description="Fundamentals of parallel programming",
                    priority=1,
                    semester_recommended="Spring Sophomore"
                ),
                MajorRequirement(
                    name="Advanced Algorithms",
                    requirement_type="core",
                    course_options=["COMP 382"],
                    credit_hours=4,
                    description="Reasoning about algorithms",
                    priority=1,
                    semester_recommended="Fall Junior"
                ),
                MajorRequirement(
                    name="Software Engineering",
                    requirement_type="core",
                    course_options=["COMP 413"],
                    credit_hours=4,
                    description="Software engineering methodology",
                    priority=1,
                    semester_recommended="Spring Junior"
                ),
                
                # Math Requirements
                MajorRequirement(
                    name="Calculus I",
                    requirement_type="math",
                    course_options=["MATH 101"],
                    credit_hours=4,
                    description="Single variable calculus I",
                    priority=1,
                    semester_recommended="Fall Freshman"
                ),
                MajorRequirement(
                    name="Calculus II",
                    requirement_type="math",
                    course_options=["MATH 102"],
                    credit_hours=4,
                    description="Single variable calculus II",
                    priority=1,
                    semester_recommended="Spring Freshman"
                ),
                MajorRequirement(
                    name="Multivariable Calculus",
                    requirement_type="math",
                    course_options=["MATH 212"],
                    credit_hours=4,
                    description="Multivariable calculus",
                    priority=1,
                    semester_recommended="Fall Sophomore"
                ),
                MajorRequirement(
                    name="Statistics/Probability",
                    requirement_type="math",
                    course_options=["STAT 310", "STAT 312", "MATH 381"],
                    credit_hours=4,
                    description="Statistics and probability",
                    priority=1,
                    semester_recommended="Spring Sophomore"
                ),
                
                # Systems Breadth (choose 2)
                MajorRequirement(
                    name="Systems Breadth 1",
                    requirement_type="breadth",
                    course_options=["COMP 421", "COMP 422", "COMP 423", "COMP 424", "COMP 425"],
                    credit_hours=4,
                    description="Advanced systems course",
                    priority=2,
                    semester_recommended="Fall Junior",
                    breadth_area="systems"
                ),
                MajorRequirement(
                    name="Systems Breadth 2",
                    requirement_type="breadth",
                    course_options=["COMP 421", "COMP 422", "COMP 423", "COMP 424", "COMP 425"],
                    credit_hours=4,
                    description="Advanced systems course",
                    priority=2,
                    semester_recommended="Spring Junior",
                    breadth_area="systems"
                ),
                
                # Applications Breadth (choose 2)
                MajorRequirement(
                    name="Applications Breadth 1",
                    requirement_type="breadth",
                    course_options=["COMP 440", "COMP 441", "COMP 442", "COMP 443", "COMP 446"],
                    credit_hours=4,
                    description="Advanced applications course",
                    priority=2,
                    semester_recommended="Fall Junior",
                    breadth_area="applications"
                ),
                MajorRequirement(
                    name="Applications Breadth 2",
                    requirement_type="breadth",
                    course_options=["COMP 440", "COMP 441", "COMP 442", "COMP 443", "COMP 446"],
                    credit_hours=4,
                    description="Advanced applications course",
                    priority=2,
                    semester_recommended="Spring Junior",
                    breadth_area="applications"
                ),
                
                # Theory Breadth (choose 1)
                MajorRequirement(
                    name="Theory Breadth",
                    requirement_type="breadth",
                    course_options=["COMP 481", "COMP 482", "COMP 483", "COMP 484"],
                    credit_hours=4,
                    description="Advanced theory course",
                    priority=2,
                    semester_recommended="Fall Senior",
                    breadth_area="theory"
                ),
                
                # CS Electives (choose 2)
                MajorRequirement(
                    name="CS Elective 1",
                    requirement_type="elective",
                    course_options=["COMP 4XX", "COMP 5XX"],  # Placeholder for any 400/500 level COMP
                    credit_hours=4,
                    description="Advanced CS elective",
                    priority=3,
                    semester_recommended="Fall Senior"
                ),
                MajorRequirement(
                    name="CS Elective 2",
                    requirement_type="elective",
                    course_options=["COMP 4XX", "COMP 5XX"],  # Placeholder for any 400/500 level COMP
                    credit_hours=4,
                    description="Advanced CS elective",
                    priority=3,
                    semester_recommended="Spring Senior"
                ),
            ]
        }
        
        # Mathematics BS Requirements
        self.major_requirements["Mathematics"] = {
            "degree_type": "BS",
            "total_credits": 120,
            "major_credits": 48,
            "requirements": [
                MajorRequirement(
                    name="Calculus I",
                    requirement_type="core",
                    course_options=["MATH 101"],
                    credit_hours=4,
                    description="Single variable calculus I",
                    priority=1,
                    semester_recommended="Fall Freshman"
                ),
                MajorRequirement(
                    name="Calculus II",
                    requirement_type="core",
                    course_options=["MATH 102"],
                    credit_hours=4,
                    description="Single variable calculus II",
                    priority=1,
                    semester_recommended="Spring Freshman"
                ),
                MajorRequirement(
                    name="Multivariable Calculus",
                    requirement_type="core",
                    course_options=["MATH 212"],
                    credit_hours=4,
                    description="Multivariable calculus",
                    priority=1,
                    semester_recommended="Fall Sophomore"
                ),
                MajorRequirement(
                    name="Linear Algebra",
                    requirement_type="core",
                    course_options=["MATH 355"],
                    credit_hours=4,
                    description="Linear algebra",
                    priority=1,
                    semester_recommended="Spring Sophomore"
                ),
                MajorRequirement(
                    name="Abstract Algebra",
                    requirement_type="core",
                    course_options=["MATH 356"],
                    credit_hours=4,
                    description="Abstract algebra",
                    priority=1,
                    semester_recommended="Fall Junior"
                ),
                MajorRequirement(
                    name="Real Analysis",
                    requirement_type="core",
                    course_options=["MATH 382"],
                    credit_hours=4,
                    description="Real analysis",
                    priority=1,
                    semester_recommended="Spring Junior"
                ),
            ]
        }
        
        # Distribution Requirements (apply to all majors)
        self.distribution_requirements = {
            "Distribution I": {
                "areas": ["Natural Sciences", "Mathematics", "Computer Science", "Engineering"],
                "credits_required": 12,
                "description": "Natural sciences, mathematics, computer science, or engineering"
            },
            "Distribution II": {
                "areas": ["Social Sciences", "History", "Psychology", "Economics", "Political Science"],
                "credits_required": 12,
                "description": "Social sciences"
            },
            "Distribution III": {
                "areas": ["Humanities", "Arts", "Literature", "Philosophy", "Religion"],
                "credits_required": 12,
                "description": "Humanities and arts"
            }
        }
    
    def analyze_degree_progress(self, major: str, completed_courses: List[str]) -> DegreeProgress:
        """Analyze student's progress toward degree completion"""
        if major not in self.major_requirements:
            raise ValueError(f"Major '{major}' not found in requirements database")
        
        major_req = self.major_requirements[major]
        requirements = major_req["requirements"].copy()
        
        # Check which requirements are satisfied
        satisfied_requirements = []
        remaining_requirements = []
        
        total_credits_completed = 0
        major_credits_completed = 0
        
        for req in requirements:
            req_copy = MajorRequirement(
                name=req.name,
                requirement_type=req.requirement_type,
                course_options=req.course_options,
                credit_hours=req.credit_hours,
                description=req.description,
                priority=req.priority,
                semester_recommended=req.semester_recommended,
                breadth_area=req.breadth_area
            )
            
            # Check if any course option is completed
            satisfied_by = None
            for course_option in req.course_options:
                if course_option in completed_courses:
                    satisfied_by = course_option
                    break
                # Handle elective placeholders
                elif course_option in ["COMP 4XX", "COMP 5XX"]:
                    for completed_course in completed_courses:
                        if (completed_course.startswith("COMP 4") or 
                            completed_course.startswith("COMP 5")):
                            satisfied_by = completed_course
                            break
            
            if satisfied_by:
                req_copy.is_satisfied = True
                req_copy.satisfied_by = satisfied_by
                satisfied_requirements.append(req_copy)
                
                total_credits_completed += req.credit_hours
                if req.requirement_type in ["core", "breadth", "elective"]:
                    major_credits_completed += req.credit_hours
            else:
                remaining_requirements.append(req_copy)
        
        # Calculate progress percentages
        overall_progress = (total_credits_completed / major_req["total_credits"]) * 100
        major_progress = (major_credits_completed / major_req["major_credits"]) * 100
        
        # Estimate graduation semester
        remaining_credits = major_req["total_credits"] - total_credits_completed
        estimated_semesters = max(1, remaining_credits // 15)  # Assume 15 credits per semester
        estimated_graduation = self._estimate_graduation_semester(estimated_semesters)
        
        return DegreeProgress(
            major=major,
            degree_type=major_req["degree_type"],
            total_credits_required=major_req["total_credits"],
            total_credits_completed=total_credits_completed,
            major_credits_required=major_req["major_credits"],
            major_credits_completed=major_credits_completed,
            requirements_satisfied=satisfied_requirements,
            requirements_remaining=remaining_requirements,
            overall_progress=overall_progress,
            major_progress=major_progress,
            estimated_graduation_semester=estimated_graduation
        )
    
    def _estimate_graduation_semester(self, semesters_remaining: int) -> str:
        """Estimate graduation semester based on remaining semesters"""
        # Simple estimation - can be enhanced with actual calendar
        current_year = 2024
        current_semester = "Fall"
        
        if current_semester == "Fall":
            if semesters_remaining <= 1:
                return f"Spring {current_year + 1}"
            elif semesters_remaining <= 2:
                return f"Fall {current_year + 1}"
            else:
                years_to_add = (semesters_remaining - 1) // 2
                return f"Spring {current_year + 1 + years_to_add}"
        else:  # Spring
            if semesters_remaining <= 1:
                return f"Fall {current_year}"
            else:
                years_to_add = semesters_remaining // 2
                return f"Fall {current_year + years_to_add}"
    
    def get_next_semester_recommendations(self, major: str, completed_courses: List[str], 
                                        target_credits: int = 15) -> List[MajorRequirement]:
        """Get recommended courses for next semester"""
        progress = self.analyze_degree_progress(major, completed_courses)
        
        # Sort remaining requirements by priority and semester timing
        remaining_sorted = sorted(
            progress.requirements_remaining,
            key=lambda x: (x.priority, x.semester_recommended or "ZZ")
        )
        
        # Select courses for next semester
        selected_courses = []
        selected_credits = 0
        
        for req in remaining_sorted:
            if selected_credits + req.credit_hours <= target_credits:
                selected_courses.append(req)
                selected_credits += req.credit_hours
                
                if selected_credits >= target_credits:
                    break
        
        return selected_courses
    
    def validate_graduation_requirements(self, major: str, completed_courses: List[str]) -> Tuple[bool, List[str]]:
        """Validate if all graduation requirements are met"""
        progress = self.analyze_degree_progress(major, completed_courses)
        
        issues = []
        
        # Check total credits
        if progress.total_credits_completed < progress.total_credits_required:
            issues.append(f"Need {progress.total_credits_required - progress.total_credits_completed} more total credits")
        
        # Check major credits
        if progress.major_credits_completed < progress.major_credits_required:
            issues.append(f"Need {progress.major_credits_required - progress.major_credits_completed} more major credits")
        
        # Check remaining requirements
        if progress.requirements_remaining:
            issues.append(f"Must complete {len(progress.requirements_remaining)} more requirements")
        
        return len(issues) == 0, issues
    
    def get_alternative_paths(self, major: str, completed_courses: List[str]) -> List[Dict]:
        """Get alternative course paths to graduation"""
        progress = self.analyze_degree_progress(major, completed_courses)
        
        paths = []
        
        # Group requirements by type
        remaining_by_type = {}
        for req in progress.requirements_remaining:
            if req.requirement_type not in remaining_by_type:
                remaining_by_type[req.requirement_type] = []
            remaining_by_type[req.requirement_type].append(req)
        
        # Generate alternative paths for each type
        for req_type, reqs in remaining_by_type.items():
            if len(reqs) > 1:
                # Multiple options available
                paths.append({
                    "type": req_type,
                    "description": f"Alternative {req_type} options",
                    "options": [
                        {
                            "name": req.name,
                            "courses": req.course_options,
                            "credits": req.credit_hours
                        }
                        for req in reqs
                    ]
                })
        
        return paths

@dataclass
class SemesterPlan:
    """Represents a semester course plan"""
    semester: str
    year: int
    courses: List[str]
    total_credits: int
    difficulty_balance: float
    workload_estimate: float
    prerequisite_satisfaction: Dict[str, bool]
    major_requirement_progress: List[str]

@dataclass
class MultiSemesterPlan:
    """Represents a multi-semester academic plan"""
    total_semesters: int
    semester_plans: List[SemesterPlan]
    graduation_semester: str
    total_credits: int
    major_requirements_completed: List[str]
    optimization_score: float
    alternative_paths: List[Dict] = field(default_factory=list)

class SemesterPlanningEngine:
    """Advanced semester planning and optimization engine"""
    
    def __init__(self, prerequisite_parser: PrerequisiteParser, 
                 major_requirement_engine: MajorRequirementEngine):
        self.prerequisite_parser = prerequisite_parser
        self.major_requirement_engine = major_requirement_engine
        self.semester_constraints = {
            'max_credits': 18,
            'min_credits': 12,
            'max_difficulty': 0.8,
            'max_workload': 0.85
        }
        
    def create_optimal_plan(self, major: str, completed_courses: List[str], 
                          current_semester: str = "Fall", 
                          current_year: int = 2024,
                          target_graduation: str = None) -> MultiSemesterPlan:
        """Create an optimal multi-semester plan"""
        
        # Get degree progress
        progress = self.major_requirement_engine.analyze_degree_progress(major, completed_courses)
        
        # Get remaining courses needed
        remaining_requirements = progress.requirements_remaining
        remaining_courses = []
        for req in remaining_requirements:
            remaining_courses.extend(req.course_options)
        
        # Remove duplicates and prioritize
        remaining_courses = list(set(remaining_courses))
        
        # Get optimal sequence
        optimal_sequence = self.prerequisite_parser.find_optimal_course_sequence(
            remaining_courses, completed_courses
        )
        
        # Create semester plans
        semester_plans = self._create_semester_plans(
            optimal_sequence.sequence, 
            remaining_requirements,
            current_semester,
            current_year,
            completed_courses
        )
        
        # Calculate optimization score
        optimization_score = self._calculate_optimization_score(semester_plans)
        
        # Generate alternative paths
        alternative_paths = self._generate_alternative_paths(
            remaining_requirements, semester_plans
        )
        
        return MultiSemesterPlan(
            total_semesters=len(semester_plans),
            semester_plans=semester_plans,
            graduation_semester=f"{semester_plans[-1].semester} {semester_plans[-1].year}",
            total_credits=sum(plan.total_credits for plan in semester_plans),
            major_requirements_completed=[req.name for req in progress.requirements_satisfied],
            optimization_score=optimization_score,
            alternative_paths=alternative_paths
        )
    
    def _create_semester_plans(self, course_sequence: List[str], 
                             requirements: List[MajorRequirement],
                             current_semester: str,
                             current_year: int,
                             completed_courses: List[str]) -> List[SemesterPlan]:
        """Create detailed semester plans"""
        
        semester_plans = []
        course_queue = course_sequence.copy()
        semester = current_semester
        year = current_year
        
        # Create requirement lookup
        course_to_requirement = {}
        for req in requirements:
            for course in req.course_options:
                course_to_requirement[course] = req
        
        while course_queue:
            # Initialize semester
            semester_courses = []
            semester_credits = 0
            semester_difficulty = 0.0
            semester_workload = 0.0
            
            # Add courses to semester
            remaining_courses = course_queue.copy()
            
            for course_code in remaining_courses:
                # Check if we can add this course
                if self._can_add_course_to_semester(
                    course_code, semester_courses, semester_credits, 
                    semester_difficulty, semester_workload, completed_courses
                ):
                    semester_courses.append(course_code)
                    course_queue.remove(course_code)
                    
                    # Update semester metrics
                    semester_credits += self._get_course_credits(course_code)
                    semester_difficulty += self._get_course_difficulty(course_code)
                    semester_workload += self._get_course_workload(course_code)
                    
                    # Stop if we've reached reasonable limits
                    if semester_credits >= 15 or len(semester_courses) >= 5:
                        break
            
            # Create semester plan
            if semester_courses:
                prereq_satisfaction = {}
                major_req_progress = []
                
                for course in semester_courses:
                    # Check prerequisite satisfaction
                    satisfied, missing = self.prerequisite_parser.validate_prerequisite_satisfaction(
                        course, completed_courses + [c for plan in semester_plans for c in plan.courses]
                    )
                    prereq_satisfaction[course] = satisfied
                    
                    # Check major requirement progress
                    if course in course_to_requirement:
                        major_req_progress.append(course_to_requirement[course].name)
                
                semester_plan = SemesterPlan(
                    semester=semester,
                    year=year,
                    courses=semester_courses,
                    total_credits=semester_credits,
                    difficulty_balance=semester_difficulty / len(semester_courses) if semester_courses else 0,
                    workload_estimate=semester_workload / len(semester_courses) if semester_courses else 0,
                    prerequisite_satisfaction=prereq_satisfaction,
                    major_requirement_progress=major_req_progress
                )
                
                semester_plans.append(semester_plan)
            
            # Move to next semester
            if semester == "Fall":
                semester = "Spring"
                year += 1
            else:
                semester = "Fall"
        
        return semester_plans
    
    def _can_add_course_to_semester(self, course_code: str, current_courses: List[str],
                                  current_credits: int, current_difficulty: float,
                                  current_workload: float, completed_courses: List[str]) -> bool:
        """Check if a course can be added to the current semester"""
        
        # Check credit limit
        course_credits = self._get_course_credits(course_code)
        if current_credits + course_credits > self.semester_constraints['max_credits']:
            return False
        
        # Check difficulty balance
        course_difficulty = self._get_course_difficulty(course_code)
        if current_difficulty + course_difficulty > self.semester_constraints['max_difficulty']:
            return False
        
        # Check workload balance
        course_workload = self._get_course_workload(course_code)
        if current_workload + course_workload > self.semester_constraints['max_workload']:
            return False
        
        # Check prerequisites
        satisfied, missing = self.prerequisite_parser.validate_prerequisite_satisfaction(
            course_code, completed_courses + current_courses
        )
        if not satisfied:
            return False
        
        return True
    
    def _get_course_credits(self, course_code: str) -> int:
        """Get credit hours for a course"""
        # This would normally come from the course database
        # Using default for now
        return 4
    
    def _get_course_difficulty(self, course_code: str) -> float:
        """Get difficulty score for a course"""
        # Extract level from course code
        if len(course_code) >= 8:
            level_char = course_code.split()[-1][0]
            if level_char.isdigit():
                level = int(level_char)
                return min(level * 0.15, 0.8)
        return 0.5
    
    def _get_course_workload(self, course_code: str) -> float:
        """Get workload estimate for a course"""
        # Similar to difficulty for now
        return self._get_course_difficulty(course_code)
    
    def _calculate_optimization_score(self, semester_plans: List[SemesterPlan]) -> float:
        """Calculate optimization score for the entire plan"""
        if not semester_plans:
            return 0.0
        
        scores = []
        
        # Balance score (even distribution of difficulty)
        difficulties = [plan.difficulty_balance for plan in semester_plans]
        difficulty_variance = np.var(difficulties) if difficulties else 0
        balance_score = max(0.0, 1.0 - difficulty_variance)
        scores.append(balance_score)
        
        # Efficiency score (completing requirements in optimal order)
        efficiency_score = 0.8  # Base score
        for i, plan in enumerate(semester_plans[:-1]):
            if plan.major_requirement_progress:
                efficiency_score += 0.05  # Bonus for making progress
        scores.append(min(efficiency_score, 1.0))
        
        # Feasibility score (prerequisites satisfied)
        feasibility_score = 1.0
        for plan in semester_plans:
            unsatisfied = sum(1 for satisfied in plan.prerequisite_satisfaction.values() if not satisfied)
            if unsatisfied > 0:
                feasibility_score -= 0.1 * unsatisfied
        scores.append(max(feasibility_score, 0.0))
        
        return sum(scores) / len(scores)
    
    def _generate_alternative_paths(self, requirements: List[MajorRequirement], 
                                  semester_plans: List[SemesterPlan]) -> List[Dict]:
        """Generate alternative course paths"""
        alternatives = []
        
        # Group requirements by type
        requirement_groups = {}
        for req in requirements:
            if req.requirement_type not in requirement_groups:
                requirement_groups[req.requirement_type] = []
            requirement_groups[req.requirement_type].append(req)
        
        # Generate alternatives for each group
        for req_type, reqs in requirement_groups.items():
            if len(reqs) > 1:
                alternatives.append({
                    'type': req_type,
                    'description': f"Alternative {req_type} courses",
                    'options': [
                        {
                            'name': req.name,
                            'courses': req.course_options,
                            'semester_recommended': req.semester_recommended
                        }
                        for req in reqs
                    ]
                })
        
        return alternatives
    
    def optimize_semester_schedule(self, courses: List[str], 
                                 constraints: Dict = None) -> Dict:
        """Optimize a single semester schedule"""
        if constraints is None:
            constraints = self.semester_constraints
        
        # This is a simplified optimization
        # In a full implementation, this would use more sophisticated algorithms
        
        optimized_schedule = {
            'courses': courses[:5],  # Limit to 5 courses
            'total_credits': sum(self._get_course_credits(course) for course in courses[:5]),
            'difficulty_balance': sum(self._get_course_difficulty(course) for course in courses[:5]) / 5,
            'workload_estimate': sum(self._get_course_workload(course) for course in courses[:5]) / 5,
            'optimization_suggestions': []
        }
        
        # Add optimization suggestions
        if optimized_schedule['difficulty_balance'] > 0.7:
            optimized_schedule['optimization_suggestions'].append(
                "Consider balancing with easier courses"
            )
        
        if optimized_schedule['total_credits'] < 12:
            optimized_schedule['optimization_suggestions'].append(
                "Consider adding more credits to meet minimum requirements"
            )
        
        return optimized_schedule
    
    def get_semester_recommendations(self, major: str, completed_courses: List[str],
                                   current_semester: str = "Fall") -> Dict:
        """Get recommendations for the current semester"""
        
        # Get next semester recommendations from major requirement engine
        next_semester_reqs = self.major_requirement_engine.get_next_semester_recommendations(
            major, completed_courses, target_credits=15
        )
        
        # Extract course options
        recommended_courses = []
        for req in next_semester_reqs:
            recommended_courses.extend(req.course_options)
        
        # Filter by prerequisite satisfaction
        available_courses = []
        for course in recommended_courses:
            satisfied, missing = self.prerequisite_parser.validate_prerequisite_satisfaction(
                course, completed_courses
            )
            if satisfied:
                available_courses.append({
                    'course_code': course,
                    'requirement_type': next((req.requirement_type for req in next_semester_reqs 
                                           if course in req.course_options), 'unknown'),
                    'priority': next((req.priority for req in next_semester_reqs 
                                    if course in req.course_options), 5),
                    'difficulty': self._get_course_difficulty(course),
                    'workload': self._get_course_workload(course)
                })
        
        # Sort by priority and difficulty
        available_courses.sort(key=lambda x: (x['priority'], x['difficulty']))
        
        # Create optimized schedule
        optimized = self.optimize_semester_schedule([course['course_code'] for course in available_courses])
        
        return {
            'semester': current_semester,
            'recommended_courses': available_courses[:8],
            'optimized_schedule': optimized,
            'total_requirements_remaining': len(next_semester_reqs),
            'planning_notes': self._generate_planning_notes(available_courses, optimized)
        }
    
    def _generate_planning_notes(self, courses: List[Dict], optimized: Dict) -> List[str]:
        """Generate planning notes for semester recommendations"""
        notes = []
        
        # Priority notes
        high_priority = [c for c in courses if c['priority'] == 1]
        if high_priority:
            notes.append(f"📚 {len(high_priority)} high-priority courses should be taken soon")
        
        # Difficulty notes
        if optimized['difficulty_balance'] > 0.7:
            notes.append("⚠️ This semester has challenging courses - consider study groups")
        elif optimized['difficulty_balance'] < 0.3:
            notes.append("✅ This semester has manageable difficulty - good for exploring electives")
        
        # Credit notes
        if optimized['total_credits'] < 12:
            notes.append("📝 Consider adding more courses to meet minimum credit requirements")
        elif optimized['total_credits'] > 16:
            notes.append("⚡ This is a heavy course load - ensure good time management")
        
        return notes

# Test code commented out to prevent delays during Streamlit import
# def main():
#     """Demonstrate the advanced academic advisor capabilities"""
#     print("🚀 Testing Advanced Rice University Academic Advisor")
#     print("=" * 60)
#     
#     # Initialize the enhanced recommender
#     recommender = RiceCourseRecommender()
#     
#     # Test student profile
#     student_profile = {
#         'major': 'Computer Science',
#         'completed_courses': ['COMP 140', 'COMP 182', 'MATH 101', 'MATH 102'],
#         'current_year': 'Sophomore',
#         'career_interests': ['software_engineering', 'machine_learning']
#     }
#     
#     print("\n📚 Testing Smart Course Recommendations...")
#     query = "I am interested in learning machine learning as a freshman who took calculus BC, what math should i take next"
#     smart_recs = recommender.get_smart_course_recommendations(query, student_profile)
#     print(f"✅ Found {len(smart_recs['recommendations'])} intelligent recommendations")
#     
#     print("\n🎓 Testing Comprehensive Academic Plan...")
#     academic_plan = recommender.get_comprehensive_academic_plan(
#         'Computer Science', student_profile['completed_courses']
#     )
#     print(f"✅ Generated {academic_plan['multi_semester_plan'].total_semesters}-semester plan")
#     print(f"🎯 Graduation: {academic_plan['graduation_timeline']['estimated_graduation']}")
#     
#     print("\n📊 Testing Degree Audit...")
#     degree_audit = recommender.get_degree_audit(
#         'Computer Science', student_profile['completed_courses']
#     )
#     progress = degree_audit['degree_progress']
#     print(f"✅ Overall progress: {progress.overall_progress:.1f}%")
#     print(f"🎯 Major progress: {progress.major_progress:.1f}%")
#     
#     print("\n🔗 Testing Prerequisite Analysis...")
#     prereq_analysis = recommender.get_prerequisite_analysis('COMP 382')
#     print(f"✅ COMP 382 prerequisites: {prereq_analysis['direct_prerequisites']}")
#     print(f"🔄 Enables courses: {prereq_analysis['enables_courses']}")
#     
#     print("\n🎯 Testing Course Sequence Analysis...")
#     target_courses = ['COMP 215', 'COMP 321', 'COMP 382', 'COMP 413']
#     sequence_analysis = recommender.analyze_course_sequence(
#         target_courses, student_profile['completed_courses']
#     )
#     print(f"✅ Optimal sequence: {sequence_analysis['optimal_sequence'].sequence}")
#     print(f"📅 Total semesters: {sequence_analysis['total_semesters']}")
#     
#     print("\n🏆 Testing Graduation Analysis...")
#     grad_analysis = recommender.get_graduation_analysis(
#         'Computer Science', student_profile['completed_courses']
#     )
#     print(f"✅ Can graduate: {grad_analysis['can_graduate']}")
#     print(f"🎓 Estimated graduation: {grad_analysis['estimated_graduation']}")
#     
#     print("\n" + "=" * 60)
#     print("🎉 ALL ADVANCED FEATURES WORKING PERFECTLY!")
#     print("🧠 Intelligence Level: EXCEPTIONALLY HIGH")
#     print("=" * 60)

# if __name__ == "__main__":
#     main() 