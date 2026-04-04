#!/usr/bin/env python3
"""
Intelligence Router - Smart Query Routing System
===============================================

Automatically determines the optimal intelligence level for each query:
- 🔵 Basic: Fast recommendations (Phase 1)
- 🟡 Enhanced: ML-powered personalization (Phase 2)  
- 🟢 Expert: GPT-validated analysis (Phase 3)
"""

import re
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligenceLevel(Enum):
    """Three levels of intelligence processing"""
    BASIC = "basic"        # Phase 1: Fast, foundational recommendations
    ENHANCED = "enhanced"  # Phase 2: ML-powered personalization
    EXPERT = "expert"      # Phase 3: GPT-validated analysis

@dataclass
class QueryAnalysis:
    """Comprehensive analysis of user query"""
    complexity_score: float  # 0-1 scale
    user_profile_completeness: float  # 0-1 scale
    needs_personalization: bool
    needs_expert_validation: bool
    keywords: List[str]
    intent: str
    confidence: float
    reasoning: List[str]
    
    def __str__(self):
        return f"QueryAnalysis(complexity={self.complexity_score:.2f}, intent={self.intent}, confidence={self.confidence:.2f})"

class IntelligenceRouter:
    """
    🧠 Smart Intelligence Router
    
    Analyzes queries and routes them to the optimal intelligence level
    """
    
    def __init__(self):
        # Query complexity patterns
        self.complexity_patterns = {
            'simple': {
                'patterns': [
                    r'what is', r'find courses?', r'list courses?',
                    r'show me', r'search for', r'browse',
                    r'tell me about', r'explain', r'describe'
                ],
                'weight': 0.2
            },
            'medium': {
                'patterns': [
                    r'recommend', r'suggest', r'should I take',
                    r'plan', r'schedule', r'next semester',
                    r'help me choose', r'which course', r'prerequisites'
                ],
                'weight': 0.5
            },
            'complex': {
                'patterns': [
                    r'career', r'graduate', r'optimize', r'strategy',
                    r'job', r'company', r'best path', r'graduation plan',
                    r'roadmap', r'timeline', r'early graduation',
                    r'google', r'microsoft', r'meta', r'amazon'
                ],
                'weight': 0.8
            }
        }
        
        # Intent classification patterns
        self.intent_patterns = {
            'course_search': [
                r'find', r'search', r'browse', r'list', r'show'
            ],
            'course_recommendation': [
                r'recommend', r'suggest', r'should I', r'which course',
                r'what course', r'help me choose'
            ],
            'academic_planning': [
                r'plan', r'schedule', r'semester', r'timeline',
                r'graduation', r'roadmap', r'sequence'
            ],
            'career_guidance': [
                r'career', r'job', r'work', r'company', r'industry',
                r'prepare', r'skills', r'interview'
            ],
            'prerequisite_check': [
                r'prerequisite', r'prereq', r'requirement', r'can I take',
                r'eligible', r'ready for'
            ]
        }
        
        # Profile completeness weights
        self.profile_weights = {
            'major': 0.25,
            'current_year': 0.20,
            'completed_courses': 0.25,
            'gpa': 0.15,
            'career_goals': 0.15
        }
        
        # Query processing statistics
        self.query_stats = {
            'total_queries': 0,
            'basic_queries': 0,
            'enhanced_queries': 0,
            'expert_queries': 0,
            'avg_processing_time': 0.0
        }
        
        logger.info("🧠 Intelligence Router initialized successfully!")
    
    def analyze_query(self, query: str, user_profile: Dict) -> QueryAnalysis:
        """
        🔍 Comprehensive query analysis
        
        Args:
            query: User's query string
            user_profile: User profile dictionary
            
        Returns:
            QueryAnalysis object with full analysis
        """
        start_time = time.time()
        
        query_lower = query.lower().strip()
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(query_lower)
        
        # Check profile completeness
        profile_completeness = self._calculate_profile_completeness(user_profile)
        
        # Determine needs
        needs_personalization = self._needs_personalization(query_lower, profile_completeness)
        needs_expert_validation = self._needs_expert_validation(query_lower, complexity_score)
        
        # Extract keywords and intent
        keywords = self._extract_keywords(query_lower)
        intent = self._determine_intent(query_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(complexity_score, profile_completeness, intent)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(complexity_score, profile_completeness, intent, keywords)
        
        processing_time = time.time() - start_time
        self.query_stats['total_queries'] += 1
        self.query_stats['avg_processing_time'] = (
            (self.query_stats['avg_processing_time'] * (self.query_stats['total_queries'] - 1) + processing_time) 
            / self.query_stats['total_queries']
        )
        
        analysis = QueryAnalysis(
            complexity_score=complexity_score,
            user_profile_completeness=profile_completeness,
            needs_personalization=needs_personalization,
            needs_expert_validation=needs_expert_validation,
            keywords=keywords,
            intent=intent,
            confidence=confidence,
            reasoning=reasoning
        )
        
        logger.info(f"📊 Query analyzed: {analysis}")
        return analysis
    
    def determine_intelligence_level(self, analysis: QueryAnalysis) -> IntelligenceLevel:
        """
        🎯 Determine optimal intelligence level
        
        Args:
            analysis: QueryAnalysis object
            
        Returns:
            IntelligenceLevel enum
        """
        
        # ALWAYS use EXPERT level (GPT-4) for highest quality responses
        self.query_stats['expert_queries'] += 1
        logger.info(f"🟢 Routing to EXPERT level (FORCED - using GPT-4 for all queries)")
        return IntelligenceLevel.EXPERT
    
    def _calculate_complexity(self, query: str) -> float:
        """Calculate query complexity score (0-1)"""
        max_complexity = 0.0
        
        for level, data in self.complexity_patterns.items():
            for pattern in data['patterns']:
                if re.search(pattern, query):
                    max_complexity = max(max_complexity, data['weight'])
        
        # Boost complexity for multi-part queries
        if len(query.split()) > 10:
            max_complexity = min(1.0, max_complexity + 0.1)
        
        # Boost for question words indicating complexity
        complex_indicators = ['how', 'why', 'optimize', 'best', 'strategy', 'timeline']
        for indicator in complex_indicators:
            if indicator in query:
                max_complexity = min(1.0, max_complexity + 0.15)
        
        return max_complexity
    
    def _calculate_profile_completeness(self, profile: Dict) -> float:
        """Calculate how complete user profile is (0-1)"""
        if not profile:
            return 0.0
        
        completeness = 0.0
        
        for field, weight in self.profile_weights.items():
            if field in profile and profile[field]:
                if field == 'completed_courses':
                    # More completed courses = higher completeness
                    courses = profile[field]
                    if isinstance(courses, list) and len(courses) > 0:
                        completeness += weight * min(1.0, len(courses) / 10)
                elif field == 'career_goals':
                    # Career goals list
                    goals = profile[field]
                    if isinstance(goals, list) and len(goals) > 0:
                        completeness += weight
                    elif isinstance(goals, str) and goals.strip():
                        completeness += weight
                else:
                    completeness += weight
        
        return min(1.0, completeness)
    
    def _needs_personalization(self, query: str, profile_completeness: float) -> bool:
        """Determine if query would benefit from personalization"""
        
        # High profile completeness suggests personalization would help
        if profile_completeness > 0.3:
            return True
        
        # Personalization keywords
        personalization_keywords = [
            'for me', 'my profile', 'my background', 'my major',
            'recommend', 'suggest', 'should I', 'my career',
            'my goals', 'based on', 'given my'
        ]
        
        return any(keyword in query for keyword in personalization_keywords)
    
    def _needs_expert_validation(self, query: str, complexity_score: float) -> bool:
        """Determine if query needs expert GPT validation"""
        
        # High complexity suggests expert validation would help
        if complexity_score > 0.7:
            return True
        
        # Expert validation keywords
        expert_keywords = [
            'optimize', 'best strategy', 'expert advice', 'validation',
            'graduation plan', 'career strategy', 'company preparation',
            'advanced analysis', 'detailed plan', 'expert review'
        ]
        
        return any(keyword in query for keyword in expert_keywords)
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords from query"""
        keywords = []
        
        # Academic keywords
        academic_keywords = {
            'machine learning': ['machine learning', 'ml', 'artificial intelligence', 'ai'],
            'computer science': ['computer science', 'cs', 'programming', 'coding'],
            'mathematics': ['math', 'calculus', 'statistics', 'linear algebra'],
            'physics': ['physics', 'quantum', 'mechanics'],
            'engineering': ['engineering', 'design', 'systems'],
            'data science': ['data science', 'data analysis', 'statistics'],
            'web development': ['web', 'frontend', 'backend', 'html', 'javascript'],
            'algorithms': ['algorithms', 'data structures', 'complexity']
        }
        
        for category, terms in academic_keywords.items():
            if any(term in query for term in terms):
                keywords.append(category)
        
        # Career keywords
        career_keywords = {
            'software_engineering': ['software engineer', 'developer', 'programming'],
            'data_science': ['data scientist', 'analyst', 'machine learning'],
            'research': ['research', 'phd', 'graduate school'],
            'finance': ['finance', 'banking', 'trading'],
            'consulting': ['consulting', 'strategy', 'business']
        }
        
        for category, terms in career_keywords.items():
            if any(term in query for term in terms):
                keywords.append(category)
        
        return keywords
    
    def _determine_intent(self, query: str) -> str:
        """Determine primary intent of query"""
        
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query):
                    score += 1
            intent_scores[intent] = score
        
        # Return intent with highest score
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        else:
            return 'general_inquiry'
    
    def _calculate_confidence(self, complexity: float, profile_completeness: float, intent: str) -> float:
        """Calculate confidence in routing decision"""
        
        base_confidence = 0.7
        
        # Boost confidence for clear intent
        if intent in ['course_search', 'course_recommendation']:
            base_confidence += 0.1
        
        # Boost confidence for good profile
        if profile_completeness > 0.5:
            base_confidence += 0.1
        
        # Boost confidence for clear complexity
        if complexity < 0.3 or complexity > 0.7:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _generate_reasoning(self, complexity: float, profile_completeness: float, 
                          intent: str, keywords: List[str]) -> List[str]:
        """Generate reasoning for routing decision"""
        
        reasoning = []
        
        # Complexity reasoning
        if complexity > 0.7:
            reasoning.append(f"High complexity query ({complexity:.2f}) suggests expert analysis needed")
        elif complexity > 0.4:
            reasoning.append(f"Medium complexity query ({complexity:.2f}) benefits from enhanced processing")
        else:
            reasoning.append(f"Simple query ({complexity:.2f}) can be handled with basic processing")
        
        # Profile reasoning
        if profile_completeness > 0.5:
            reasoning.append(f"Complete profile ({profile_completeness:.2f}) enables personalization")
        elif profile_completeness > 0.3:
            reasoning.append(f"Partial profile ({profile_completeness:.2f}) allows some personalization")
        else:
            reasoning.append(f"Limited profile ({profile_completeness:.2f}) limits personalization")
        
        # Intent reasoning
        if intent == 'career_guidance':
            reasoning.append("Career guidance queries benefit from expert validation")
        elif intent == 'academic_planning':
            reasoning.append("Academic planning queries benefit from personalized recommendations")
        elif intent == 'course_search':
            reasoning.append("Course search queries can be handled efficiently with basic processing")
        
        # Keywords reasoning
        if keywords:
            reasoning.append(f"Keywords detected: {', '.join(keywords)}")
        
        return reasoning
    
    def get_stats(self) -> Dict:
        """Get routing statistics"""
        total = self.query_stats['total_queries']
        if total == 0:
            return self.query_stats
        
        return {
            **self.query_stats,
            'basic_percentage': (self.query_stats['basic_queries'] / total) * 100,
            'enhanced_percentage': (self.query_stats['enhanced_queries'] / total) * 100,
            'expert_percentage': (self.query_stats['expert_queries'] / total) * 100
        }
    
    def reset_stats(self):
        """Reset routing statistics"""
        self.query_stats = {
            'total_queries': 0,
            'basic_queries': 0,
            'enhanced_queries': 0,
            'expert_queries': 0,
            'avg_processing_time': 0.0
        }
        logger.info("📊 Router statistics reset")

# Test the router
if __name__ == "__main__":
    print("🧠 Testing Intelligence Router...")
    
    router = IntelligenceRouter()
    
    # Test queries
    test_cases = [
        {
            'query': "Find machine learning courses",
            'profile': {'major': 'Computer Science'},
            'expected': IntelligenceLevel.BASIC
        },
        {
            'query': "Recommend ML courses for my CS sophomore profile",
            'profile': {
                'major': 'Computer Science',
                'current_year': 'sophomore',
                'completed_courses': ['COMP 140', 'COMP 182'],
                'gpa': 3.5
            },
            'expected': IntelligenceLevel.ENHANCED
        },
        {
            'query': "Create an optimal graduation strategy to prepare for Google",
            'profile': {
                'major': 'Computer Science',
                'current_year': 'freshman',
                'career_goals': ['software_engineering']
            },
            'expected': IntelligenceLevel.EXPERT
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: '{test['query']}'")
        analysis = router.analyze_query(test['query'], test['profile'])
        level = router.determine_intelligence_level(analysis)
        
        print(f"   Intent: {analysis.intent}")
        print(f"   Complexity: {analysis.complexity_score:.2f}")
        print(f"   Profile: {analysis.user_profile_completeness:.2f}")
        print(f"   Level: {level.value}")
        print(f"   Expected: {test['expected'].value}")
        print(f"   ✅ Match: {level == test['expected']}")
    
    # Show statistics
    print(f"\n📊 Router Statistics:")
    stats = router.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n🎉 Intelligence Router test complete!") 