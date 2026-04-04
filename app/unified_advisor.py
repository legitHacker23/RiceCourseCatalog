#!/usr/bin/env python3
"""
Unified Advisor - Central Intelligence Orchestrator
=================================================

Orchestrates all 3 intelligence levels and connects to existing systems:
- Routes queries to optimal intelligence level
- Connects to existing Phase 1, 2, and 3 systems
- Provides unified interface for all features
"""

import time
import logging
from typing import Dict, List, Optional, Any
from app.intelligence_router import IntelligenceRouter, IntelligenceLevel, QueryAnalysis
from app.response_formatter import UnifiedResponse, ResponseFormatter

# Import existing systems
try:
    from app.course_recommender import RiceCourseRecommender
    COURSE_RECOMMENDER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Course recommender not available: {e}")
    COURSE_RECOMMENDER_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedAdvisor:
    """
    🎯 Unified Academic Advisor
    
    Central orchestrator that:
    - Analyzes queries and routes to optimal intelligence level
    - Connects to existing Phase 1, 2, and 3 systems
    - Provides consistent, unified responses
    - Tracks performance and learns from usage
    """
    
    def __init__(self):
        """Initialize the unified advisor with all intelligence systems"""
        
        logger.info("🚀 Initializing Unified Academic Advisor...")
        
        # Core components
        self.intelligence_router = IntelligenceRouter()
        self.response_formatter = ResponseFormatter()
        
        # Initialize existing systems
        self.course_recommender = None
        self._initialize_existing_systems()
        
        # Performance tracking
        self.performance_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_response_time': 0.0,
            'intelligence_level_usage': {
                'basic': 0,
                'enhanced': 0,
                'expert': 0
            },
            'user_satisfaction': {
                'total_ratings': 0,
                'average_rating': 0.0
            }
        }
        
        # Response cache for performance
        self.response_cache = {}
        self.cache_enabled = True
        self.cache_max_size = 1000
        
        logger.info("✅ Unified Academic Advisor initialized successfully!")
        
    def _initialize_existing_systems(self):
        """Initialize connections to existing recommendation systems"""
        
        if COURSE_RECOMMENDER_AVAILABLE:
            try:
                # Initialize course recommender with Fall 2025 data
                fall2025_course_file = "data/raw/rice_courses_202610_with_instructors.json"
                self.course_recommender = RiceCourseRecommender(course_file=fall2025_course_file, enable_ml=True)
                logger.info("✅ Course recommender system connected with Fall 2025 data")
            except Exception as e:
                logger.error(f"❌ Failed to initialize course recommender with Fall 2025 data: {e}")
                # Fallback to default data
                try:
                    self.course_recommender = RiceCourseRecommender(enable_ml=True)
                    logger.info("✅ Course recommender system connected with default data")
                except Exception as e2:
                    logger.error(f"❌ Failed to initialize course recommender: {e2}")
                    self.course_recommender = None
        else:
            logger.warning("⚠️ Course recommender not available - some features will be limited")
    
    def process_query(self, query: str, user_profile: Dict) -> UnifiedResponse:
        """
        🎯 Process user query with optimal intelligence level
        
        Args:
            query: User's query string
            user_profile: User profile dictionary
            
        Returns:
            UnifiedResponse with recommendations and analysis
        """
        
        start_time = time.time()
        self.performance_stats['total_queries'] += 1
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query, user_profile)
            if self.cache_enabled and cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                cached_response.cache_hit = True
                cached_response.processing_time = time.time() - start_time
                logger.info(f"💨 Cache hit for query: {query[:50]}...")
                return cached_response
            
            # Analyze query to determine intelligence level
            logger.info(f"🔍 Processing query: {query[:50]}...")
            analysis = self.intelligence_router.analyze_query(query, user_profile)
            intelligence_level = self.intelligence_router.determine_intelligence_level(analysis)
            
            # Route to appropriate intelligence level
            if intelligence_level == IntelligenceLevel.EXPERT:
                response_data = self._process_expert_level(query, user_profile, analysis)
            elif intelligence_level == IntelligenceLevel.ENHANCED:
                response_data = self._process_enhanced_level(query, user_profile, analysis)
            else:
                response_data = self._process_basic_level(query, user_profile, analysis)
            
            # Create unified response
            processing_time = time.time() - start_time
            response = self._create_unified_response(
                response_data, intelligence_level, analysis, processing_time
            )
            
            # Cache the response
            if self.cache_enabled:
                self._cache_response(cache_key, response)
            
            # Update performance stats
            self.performance_stats['successful_queries'] += 1
            self.performance_stats['intelligence_level_usage'][intelligence_level.value] += 1
            self._update_average_response_time(processing_time)
            
            logger.info(f"✅ Query processed successfully in {processing_time:.2f}s using {intelligence_level.value} intelligence")
            return response
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            self.performance_stats['failed_queries'] += 1
            
            # Return error response
            return self._create_error_response(query, user_profile, str(e), time.time() - start_time)
    
    def _process_basic_level(self, query: str, user_profile: Dict, analysis: QueryAnalysis) -> Dict:
        """Process with basic intelligence (Phase 1)"""
        
        logger.info("🔵 Processing with Basic Intelligence (Phase 1)")
        
        if not self.course_recommender:
            return self._create_fallback_response("Course recommender not available")
        
        try:
            # Use existing course recommender for basic recommendations
            recommendations = self.course_recommender.get_recommendations_by_interest(
                query, num_recommendations=8
            )
            
            # Enhance recommendations with basic analysis
            enhanced_recommendations = self._enhance_basic_recommendations(
                recommendations, analysis
            )
            
            return {
                'recommendations': enhanced_recommendations,
                'confidence': 0.75,
                'reasoning': [
                    "Fast recommendations based on course content similarity",
                    "Prerequisite requirements verified",
                    "Department relevance considered",
                    f"Analyzed {len(recommendations)} courses for relevance"
                ],
                'total_courses_analyzed': len(self.course_recommender.courses_df) if self.course_recommender else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Basic processing failed: {e}")
            return self._create_fallback_response(f"Basic processing error: {e}")
    
    def _process_enhanced_level(self, query: str, user_profile: Dict, analysis: QueryAnalysis) -> Dict:
        """Process with ML enhancement (Phase 2)"""
        
        logger.info("🟡 Processing with Enhanced Intelligence (Phase 2)")
        
        if not self.course_recommender:
            return self._create_fallback_response("Course recommender not available")
        
        try:
            # Use ML-enhanced recommendations
            recommendations = self.course_recommender.get_ml_enhanced_recommendations(
                query, student_profile=user_profile, num_recommendations=8
            )
            
            # Extract ML insights
            ml_insights = self._extract_ml_insights(user_profile, analysis)
            
            return {
                'recommendations': recommendations,
                'confidence': 0.85,
                'reasoning': [
                    "ML-enhanced recommendations based on student success prediction",
                    "Personalized for your academic profile and goals",
                    "Success probabilities calculated for each course",
                    "Course sequence optimized for your progression"
                ],
                'ml_insights': ml_insights,
                'total_courses_analyzed': len(self.course_recommender.courses_df) if self.course_recommender else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced processing failed: {e}")
            # Fallback to basic processing
            logger.info("🔄 Falling back to basic processing")
            return self._process_basic_level(query, user_profile, analysis)
    
    def _process_expert_level(self, query: str, user_profile: Dict, analysis: QueryAnalysis) -> Dict:
        """Process with GPT validation (Phase 3)"""
        
        logger.info("🟢 Processing with Expert Intelligence (Phase 3)")
        
        if not self.course_recommender:
            return self._create_fallback_response("Course recommender not available")
        
        try:
            # Use GPT-validated recommendations
            gpt_result = self.course_recommender.get_gpt_validated_recommendations(
                query, student_profile=user_profile, num_recommendations=8
            )
            
            return {
                'recommendations': gpt_result.get('enhanced_recommendations', []),
                'confidence': 0.95,
                'reasoning': [
                    "GPT-4 validated recommendations with expert analysis",
                    "System learned from GPT feedback for continuous improvement",
                    "Optimized for accuracy and career relevance",
                    "Expert-level analysis of course sequence and timing"
                ],
                'gpt_analysis': gpt_result.get('gpt_analysis', 'Expert analysis completed'),
                'ml_insights': gpt_result.get('learning_insights', []),
                'total_courses_analyzed': len(self.course_recommender.courses_df) if self.course_recommender else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Expert processing failed: {e}")
            # Fallback to enhanced processing
            logger.info("🔄 Falling back to enhanced processing")
            return self._process_enhanced_level(query, user_profile, analysis)
    
    def _enhance_basic_recommendations(self, recommendations: List[Dict], analysis: QueryAnalysis) -> List[Dict]:
        """Enhance basic recommendations with additional analysis"""
        
        enhanced = []
        for rec in recommendations:
            # Add reasoning based on query analysis
            reasoning = self._generate_course_reasoning(rec, analysis)
            rec['reasoning'] = reasoning
            
            # Add relevance indicators
            if 'similarity_score' in rec:
                rec['relevance_level'] = self._calculate_relevance_level(rec['similarity_score'])
            
            enhanced.append(rec)
        
        return enhanced
    
    def _extract_ml_insights(self, user_profile: Dict, analysis: QueryAnalysis) -> List[str]:
        """Extract ML insights from user profile and analysis"""
        
        insights = []
        
        # Profile-based insights
        if user_profile.get('gpa'):
            gpa = user_profile['gpa']
            if gpa >= 3.5:
                insights.append(f"Your GPA ({gpa:.1f}) suggests you can handle challenging courses")
            elif gpa >= 3.0:
                insights.append(f"Your GPA ({gpa:.1f}) indicates solid academic foundation")
            else:
                insights.append(f"Consider foundational courses to build strong academic base")
        
        # Completed courses insights
        completed_courses = user_profile.get('completed_courses', [])
        if completed_courses:
            insights.append(f"Based on your {len(completed_courses)} completed courses, you're ready for intermediate-level work")
        
        # Career goal insights
        career_goals = user_profile.get('career_goals', [])
        if career_goals:
            insights.append(f"Recommendations optimized for your career goals: {', '.join(career_goals)}")
        
        # Query complexity insights
        if analysis.complexity_score > 0.7:
            insights.append("Your complex query suggests you're ready for advanced planning")
        
        return insights
    
    def _generate_course_reasoning(self, course: Dict, analysis: QueryAnalysis) -> str:
        """Generate reasoning for why a course is recommended"""
        
        course_code = course.get('course_code', 'Course')
        
        # Base reasoning on similarity score
        similarity = course.get('similarity_score', 0.5)
        if similarity > 0.8:
            return f"Excellent match for '{analysis.intent}' with high content relevance"
        elif similarity > 0.6:
            return f"Good match for your interests with solid foundational content"
        else:
            return f"Relevant course that provides important background knowledge"
    
    def _calculate_relevance_level(self, similarity_score: float) -> str:
        """Calculate relevance level from similarity score"""
        
        if similarity_score > 0.8:
            return "Highly Relevant"
        elif similarity_score > 0.6:
            return "Relevant"
        elif similarity_score > 0.4:
            return "Moderately Relevant"
        else:
            return "Basic Relevance"
    
    def _create_unified_response(self, response_data: Dict, intelligence_level: IntelligenceLevel, 
                               analysis: QueryAnalysis, processing_time: float) -> UnifiedResponse:
        """Create unified response from processing results"""
        
        # Generate quick actions based on intelligence level and analysis
        quick_actions = self._generate_quick_actions(intelligence_level, analysis)
        
        # Generate follow-up suggestions
        follow_up_suggestions = self._generate_follow_up_suggestions(intelligence_level, analysis)
        
        return UnifiedResponse(
            recommendations=response_data.get('recommendations', []),
            intelligence_level=intelligence_level,
            confidence=response_data.get('confidence', 0.5),
            reasoning=response_data.get('reasoning', []),
            query_analysis=analysis,
            processing_time=processing_time,
            ml_insights=response_data.get('ml_insights'),
            gpt_analysis=response_data.get('gpt_analysis'),
            quick_actions=quick_actions,
            follow_up_suggestions=follow_up_suggestions,
            total_courses_analyzed=response_data.get('total_courses_analyzed', 0)
        )
    
    def _generate_quick_actions(self, intelligence_level: IntelligenceLevel, analysis: QueryAnalysis) -> List[str]:
        """Generate contextual quick actions"""
        
        actions = []
        
        # Intent-based actions
        if analysis.intent == 'course_recommendation':
            actions.extend([
                "📅 Plan full semester with these courses",
                "🔍 Find similar courses",
                "📊 View course statistics"
            ])
        elif analysis.intent == 'academic_planning':
            actions.extend([
                "🎓 Create graduation timeline",
                "💼 Analyze career preparation",
                "📈 Track academic progress"
            ])
        elif analysis.intent == 'career_guidance':
            actions.extend([
                "🏢 Research target companies",
                "📊 Analyze skill requirements",
                "🎯 Create career roadmap"
            ])
        
        # Intelligence level upgrade actions
        if intelligence_level == IntelligenceLevel.BASIC:
            actions.append("🟡 Get ML-enhanced recommendations")
        if intelligence_level in [IntelligenceLevel.BASIC, IntelligenceLevel.ENHANCED]:
            actions.append("🟢 Request GPT expert analysis")
        
        return actions
    
    def _generate_follow_up_suggestions(self, intelligence_level: IntelligenceLevel, analysis: QueryAnalysis) -> List[str]:
        """Generate follow-up suggestions"""
        
        suggestions = []
        
        # Profile completeness suggestions
        if analysis.user_profile_completeness < 0.5:
            suggestions.append("Complete your profile for more personalized recommendations")
        
        # Intelligence level suggestions
        if intelligence_level == IntelligenceLevel.BASIC:
            suggestions.append("Add more profile details for ML-enhanced recommendations")
        
        if intelligence_level in [IntelligenceLevel.BASIC, IntelligenceLevel.ENHANCED]:
            suggestions.append("Try asking for 'expert analysis' for GPT-validated recommendations")
        
        # Query-specific suggestions
        if analysis.complexity_score < 0.3:
            suggestions.append("Try asking more specific questions for better recommendations")
        
        suggestions.extend([
            "Ask about specific courses for detailed analysis",
            "Request semester-by-semester planning",
            "Explore career-focused course sequences"
        ])
        
        return suggestions
    
    def _create_fallback_response(self, error_message: str) -> Dict:
        """Create fallback response when systems are unavailable"""
        
        return {
            'recommendations': [],
            'confidence': 0.0,
            'reasoning': [
                f"System temporarily unavailable: {error_message}",
                "Please try again later or contact support"
            ],
            'total_courses_analyzed': 0
        }
    
    def _create_error_response(self, query: str, user_profile: Dict, error: str, processing_time: float) -> UnifiedResponse:
        """Create error response when processing fails"""
        
        # Create basic analysis for error response
        error_analysis = QueryAnalysis(
            complexity_score=0.0,
            user_profile_completeness=0.0,
            needs_personalization=False,
            needs_expert_validation=False,
            keywords=[],
            intent='error',
            confidence=0.0,
            reasoning=[f"Processing failed: {error}"]
        )
        
        return UnifiedResponse(
            recommendations=[],
            intelligence_level=IntelligenceLevel.BASIC,
            confidence=0.0,
            reasoning=[
                f"❌ Processing failed: {error}",
                "Please try rephrasing your query or contact support",
                "The system is designed to handle various query types"
            ],
            query_analysis=error_analysis,
            processing_time=processing_time,
            follow_up_suggestions=[
                "Try a simpler query",
                "Check your internet connection",
                "Contact support if the problem persists"
            ]
        )
    
    def _generate_cache_key(self, query: str, user_profile: Dict) -> str:
        """Generate cache key for query and profile"""
        
        # Create simplified profile for caching
        cache_profile = {
            'major': user_profile.get('major', ''),
            'current_year': user_profile.get('current_year', ''),
            'completed_courses_count': len(user_profile.get('completed_courses', [])),
            'career_goals': sorted(user_profile.get('career_goals', []))
        }
        
        return f"{query.lower().strip()}|{str(cache_profile)}"
    
    def _cache_response(self, cache_key: str, response: UnifiedResponse):
        """Cache response for future use"""
        
        # Manage cache size
        if len(self.response_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
        
        self.response_cache[cache_key] = response
    
    def _update_average_response_time(self, processing_time: float):
        """Update average response time statistics"""
        
        total_queries = self.performance_stats['total_queries']
        current_avg = self.performance_stats['avg_response_time']
        
        self.performance_stats['avg_response_time'] = (
            (current_avg * (total_queries - 1) + processing_time) / total_queries
        )
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        
        stats = self.performance_stats.copy()
        
        # Add derived metrics
        total_queries = stats['total_queries']
        if total_queries > 0:
            stats['success_rate'] = (stats['successful_queries'] / total_queries) * 100
            stats['failure_rate'] = (stats['failed_queries'] / total_queries) * 100
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        # Add router and formatter stats
        stats['router_stats'] = self.intelligence_router.get_stats()
        stats['formatter_stats'] = self.response_formatter.get_formatting_stats()
        
        # Add cache stats
        stats['cache_stats'] = {
            'cache_size': len(self.response_cache),
            'cache_enabled': self.cache_enabled,
            'cache_max_size': self.cache_max_size
        }
        
        return stats
    
    def clear_cache(self):
        """Clear response cache"""
        self.response_cache.clear()
        logger.info("🧹 Response cache cleared")
    
    def reset_stats(self):
        """Reset all performance statistics"""
        self.performance_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_response_time': 0.0,
            'intelligence_level_usage': {
                'basic': 0,
                'enhanced': 0,
                'expert': 0
            },
            'user_satisfaction': {
                'total_ratings': 0,
                'average_rating': 0.0
            }
        }
        self.intelligence_router.reset_stats()
        self.response_formatter.reset_stats()
        logger.info("📊 All statistics reset")

# Test the unified advisor
if __name__ == "__main__":
    print("🎯 Testing Unified Advisor...")
    
    # Create test advisor
    advisor = UnifiedAdvisor()
    
    # Test queries with different complexity levels
    test_queries = [
        {
            'query': "Find machine learning courses",
            'profile': {'major': 'Computer Science'},
            'expected_level': 'basic'
        },
        {
            'query': "Recommend ML courses for my CS sophomore profile",
            'profile': {
                'major': 'Computer Science',
                'current_year': 'sophomore',
                'completed_courses': ['COMP 140', 'COMP 182'],
                'gpa': 3.5
            },
            'expected_level': 'enhanced'
        },
        {
            'query': "Create optimal graduation strategy for Google career",
            'profile': {
                'major': 'Computer Science',
                'current_year': 'freshman',
                'career_goals': ['software_engineering']
            },
            'expected_level': 'expert'
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{test['query']}'")
        
        try:
            response = advisor.process_query(test['query'], test['profile'])
            print(f"   Intelligence Level: {response.intelligence_level.value}")
            print(f"   Confidence: {response.confidence:.2f}")
            print(f"   Recommendations: {len(response.recommendations)}")
            print(f"   Processing Time: {response.processing_time:.3f}s")
            print(f"   Expected Level: {test['expected_level']}")
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    # Show performance statistics
    print(f"\n📊 Performance Statistics:")
    stats = advisor.get_performance_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for subkey, subvalue in value.items():
                print(f"     {subkey}: {subvalue}")
        else:
            print(f"   {key}: {value}")
    
    print("\n🎉 Unified Advisor test complete!") 