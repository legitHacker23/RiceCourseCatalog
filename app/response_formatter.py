#!/usr/bin/env python3
"""
Response Formatter - Unified Response System
===========================================

Standardizes responses across all 3 intelligence levels:
- Consistent formatting for all phases
- Rich display with intelligence indicators
- Interactive elements and follow-up suggestions
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from app.intelligence_router import IntelligenceLevel, QueryAnalysis
import json

@dataclass
class UnifiedResponse:
    """Standardized response format for all intelligence levels"""
    
    # Core response data
    recommendations: List[Dict]
    intelligence_level: IntelligenceLevel
    confidence: float
    reasoning: List[str]
    
    # Query metadata
    query_analysis: QueryAnalysis
    processing_time: float
    
    # Intelligence-specific enhancements
    ml_insights: Optional[List[str]] = None
    gpt_analysis: Optional[str] = None
    success_predictions: Optional[Dict] = None
    
    # Interactive elements
    quick_actions: List[str] = None
    follow_up_suggestions: List[str] = None
    
    # Performance metadata
    cache_hit: bool = False
    total_courses_analyzed: int = 0
    
    def __post_init__(self):
        if self.quick_actions is None:
            self.quick_actions = []
        if self.follow_up_suggestions is None:
            self.follow_up_suggestions = []

class ResponseFormatter:
    """
    🎨 Unified Response Formatter
    
    Creates consistent, beautiful responses for all intelligence levels
    """
    
    def __init__(self):
        self.intelligence_labels = {
            IntelligenceLevel.BASIC: {
                'icon': '🔵',
                'name': 'Basic',
                'description': 'Fast, reliable recommendations',
                'color': '#1976d2'
            },
            IntelligenceLevel.ENHANCED: {
                'icon': '🟡',
                'name': 'Enhanced',
                'description': 'ML-powered personalization',
                'color': '#f57c00'
            },
            IntelligenceLevel.EXPERT: {
                'icon': '🟢',
                'name': 'Expert',
                'description': 'GPT-validated analysis',
                'color': '#388e3c'
            }
        }
        
        self.formatting_stats = {
            'total_responses': 0,
            'basic_responses': 0,
            'enhanced_responses': 0,
            'expert_responses': 0
        }
    
    def format_for_display(self, response: UnifiedResponse) -> str:
        """
        🎨 Format response for beautiful Streamlit display
        
        Args:
            response: UnifiedResponse object
            
        Returns:
            Formatted markdown string
        """
        
        self.formatting_stats['total_responses'] += 1
        
        if response.intelligence_level == IntelligenceLevel.BASIC:
            self.formatting_stats['basic_responses'] += 1
        elif response.intelligence_level == IntelligenceLevel.ENHANCED:
            self.formatting_stats['enhanced_responses'] += 1
        elif response.intelligence_level == IntelligenceLevel.EXPERT:
            self.formatting_stats['expert_responses'] += 1
        
        # Build formatted response
        formatted = self._build_header(response)
        formatted += self._build_recommendations(response)
        formatted += self._build_insights(response)
        formatted += self._build_ml_analysis(response)
        formatted += self._build_gpt_analysis(response)
        formatted += self._build_follow_up(response)
        formatted += self._build_performance_info(response)
        
        return formatted
    
    def _build_header(self, response: UnifiedResponse) -> str:
        """Build response header with intelligence level indicator"""
        
        level_info = self.intelligence_labels[response.intelligence_level]
        
        header = f"""
## 🎓 **Rice Academic Advisor**

**Query:** {response.query_analysis.intent.replace('_', ' ').title()}  
**Intelligence Level:** {level_info['icon']} {level_info['name']} - {level_info['description']}  
**Confidence:** {response.confidence:.0%}  
**Processing Time:** {response.processing_time:.2f}s  
{"**Cache Hit:** ✅ (Instant response)" if response.cache_hit else ""}

---
"""
        return header
    
    def _build_recommendations(self, response: UnifiedResponse) -> str:
        """Build recommendations section with compact expandable cards"""
        
        if not response.recommendations:
            return "❌ **No recommendations found for your query.**\n\n"
        
        # Group recommendations by priority
        grouped_recs = self._group_recommendations_by_priority(response.recommendations)
        
        recommendations = "\n## 📚 **Course Recommendations**\n\n"
        
        # Show only top 4-5 recommendations initially
        top_recs = response.recommendations[:5]
        
        for group_name, group_recs in grouped_recs.items():
            if not group_recs:
                continue
                
            # Add group header with icon
            group_icon = {
                'Must Take': '🎯',
                'Highly Recommended': '⭐',
                'Consider': '💡'
            }.get(group_name, '📚')
            
            recommendations += f"### {group_icon} **{group_name}**\n\n"
            
            # Show compact cards for this group
            for rec in group_recs:
                recommendations += self._build_compact_card(rec, response.intelligence_level)
            
            recommendations += "\n"
        
        # Add "Show More" indicator if there are additional recommendations
        if len(response.recommendations) > 5:
            additional_count = len(response.recommendations) - 5
            recommendations += f"\n*💫 {additional_count} more courses available - expand for full details*\n\n"
        
        return recommendations
    
    def _group_recommendations_by_priority(self, recommendations: List[Dict]) -> Dict[str, List[Dict]]:
        """Group recommendations by priority level"""
        
        grouped = {
            'Must Take': [],
            'Highly Recommended': [],
            'Consider': []
        }
        
        for rec in recommendations[:5]:  # Only group top 5
            score = rec.get('similarity_score', 0.5)
            success_prob = rec.get('success_probability', 0.5)
            
            # Priority logic
            if score >= 0.8 or success_prob >= 0.8:
                grouped['Must Take'].append(rec)
            elif score >= 0.6 or success_prob >= 0.6:
                grouped['Highly Recommended'].append(rec)
            else:
                grouped['Consider'].append(rec)
        
        return grouped
    
    def _build_compact_card(self, rec: Dict, intelligence_level: IntelligenceLevel) -> str:
        """Build a compact expandable card for a single recommendation"""
        
        course_code = str(rec.get('course_code', 'N/A'))
        title = str(rec.get('title', 'Course Title'))
        department = str(rec.get('department', 'N/A'))
        credit_hours = str(rec.get('credit_hours', 'N/A'))
        
        # Difficulty indicator
        difficulty_icon = self._get_difficulty_icon(rec)
        
        # Success probability indicator
        success_icon = self._get_success_icon(rec, intelligence_level)
        
        # Compact card header
        card = f"**{course_code}** - {title}\n"
        card += f"📍 {department} | 📊 {credit_hours} credits {difficulty_icon} {success_icon}\n"
        
        # Quick relevance score
        if 'similarity_score' in rec:
            score = rec['similarity_score']
            stars = '⭐' * min(5, int(score * 5))
            card += f"**Match:** {stars} ({score:.2f})\n"
        
        # Expandable details indicator
        card += "\n*Click to expand for full details in chat...*\n\n"
        
        # Brief description only
        if 'description' in rec and rec['description']:
            description = str(rec['description'])  # Convert to string to handle floats/NaN
            if description not in ['N/A', 'None', '', 'nan']:
                if len(description) > 100:
                    description = description[:100] + "..."
                card += f"📝 {description}\n\n"
        
        # Prerequisites (compact)
        if 'prerequisites' in rec and rec['prerequisites']:
            prereqs = str(rec['prerequisites'])  # Convert to string to handle floats/NaN
            if prereqs not in ['N/A', 'None', '', 'nan']:
                if len(prereqs) > 50:
                    prereqs = prereqs[:50] + "..."
                card += f"📋 **Prereqs:** {prereqs}\n\n"
        
        # Course-specific reasoning (brief)
        if 'reasoning' in rec:
            reasoning = str(rec['reasoning'])  # Convert to string to handle floats/NaN
            if reasoning not in ['N/A', 'None', '', 'nan']:
                if len(reasoning) > 80:
                    reasoning = reasoning[:80] + "..."
                card += f"💡 {reasoning}\n\n"
        
        # Add visual separator
        card += "---\n\n"
        
        return card
    
    def _get_difficulty_icon(self, rec: Dict) -> str:
        """Get difficulty indicator icon"""
        # Use course number or success probability to estimate difficulty
        course_code = str(rec.get('course_code', ''))
        if course_code and course_code not in ['N/A', 'None', '', 'nan']:
            # Extract course number
            import re
            match = re.search(r'(\d+)', course_code)
            if match:
                try:
                    course_num = int(match.group(1))
                    if course_num >= 500:
                        return "🔴"  # Hard (graduate level)
                    elif course_num >= 300:
                        return "🟡"  # Medium (upper level)
                    else:
                        return "🟢"  # Easy (lower level)
                except ValueError:
                    pass
        
        return "🟡"  # Default to medium
    
    def _get_success_icon(self, rec: Dict, intelligence_level: IntelligenceLevel) -> str:
        """Get success probability indicator"""
        if intelligence_level in [IntelligenceLevel.ENHANCED, IntelligenceLevel.EXPERT]:
            if 'success_probability' in rec:
                success_prob = rec['success_probability']
                if success_prob >= 0.8:
                    return "✅"  # High success
                elif success_prob >= 0.6:
                    return "⚠️"   # Medium success
                else:
                    return "❌"  # Low success
        
        return ""  # No success prediction available
    
    def _build_insights(self, response: UnifiedResponse) -> str:
        """Build smart insights section"""
        
        if not response.reasoning:
            return ""
        
        insights = "\n## 🎯 **Smart Insights**\n\n"
        
        for insight in response.reasoning:
            insights += f"• {insight}\n"
        
        # Add query analysis insights
        if response.query_analysis.keywords:
            insights += f"• **Keywords detected:** {', '.join(response.query_analysis.keywords)}\n"
        
        insights += "\n"
        return insights
    
    def _build_ml_analysis(self, response: UnifiedResponse) -> str:
        """Build ML analysis section (for Enhanced level)"""
        
        if response.intelligence_level != IntelligenceLevel.ENHANCED or not response.ml_insights:
            return ""
        
        ml_section = "\n## 🤖 **ML Analysis**\n\n"
        
        for insight in response.ml_insights:
            ml_section += f"• {insight}\n"
        
        # Add success predictions if available
        if response.success_predictions:
            ml_section += "\n**Success Predictions:**\n"
            for course, prediction in response.success_predictions.items():
                ml_section += f"• {course}: {prediction:.0%} success probability\n"
        
        ml_section += "\n"
        return ml_section
    
    def _build_gpt_analysis(self, response: UnifiedResponse) -> str:
        """Build GPT analysis section (for Expert level)"""
        
        if response.intelligence_level != IntelligenceLevel.EXPERT or not response.gpt_analysis:
            return ""
        
        gpt_section = "\n## 🧠 **GPT Expert Analysis**\n\n"
        gpt_section += f"{response.gpt_analysis}\n\n"
        
        return gpt_section
    
    def _build_follow_up(self, response: UnifiedResponse) -> str:
        """Build follow-up suggestions section"""
        
        follow_up = ""
        
        # Quick actions
        if response.quick_actions:
            follow_up += "\n## 🎯 **Quick Actions**\n\n"
            for action in response.quick_actions:
                follow_up += f"• {action}\n"
        
        # Follow-up suggestions
        if response.follow_up_suggestions:
            follow_up += "\n## 💫 **What's Next?**\n\n"
            for suggestion in response.follow_up_suggestions:
                follow_up += f"• {suggestion}\n"
        
        # Intelligence level upgrade suggestions
        if response.intelligence_level == IntelligenceLevel.BASIC:
            follow_up += "• **Want personalized recommendations?** Complete your profile for ML enhancement\n"
            follow_up += "• **Need expert validation?** Ask for GPT analysis of these recommendations\n"
        elif response.intelligence_level == IntelligenceLevel.ENHANCED:
            follow_up += "• **Want expert validation?** Click 'Get GPT Review' for expert analysis\n"
        
        if follow_up:
            follow_up += "\n"
        
        return follow_up
    
    def _build_performance_info(self, response: UnifiedResponse) -> str:
        """Build performance information section"""
        
        perf_info = "\n## 📊 **System Performance**\n\n"
        perf_info += f"• **Courses analyzed:** {response.total_courses_analyzed:,}\n"
        perf_info += f"• **Query complexity:** {response.query_analysis.complexity_score:.2f}/1.0\n"
        perf_info += f"• **Profile completeness:** {response.query_analysis.user_profile_completeness:.2f}/1.0\n"
        perf_info += f"• **Routing confidence:** {response.query_analysis.confidence:.0%}\n"
        
        return perf_info
    
    def format_for_json(self, response: UnifiedResponse) -> Dict:
        """Format response as JSON for API usage"""
        
        return {
            'recommendations': response.recommendations,
            'intelligence_level': response.intelligence_level.value,
            'confidence': response.confidence,
            'reasoning': response.reasoning,
            'query_analysis': {
                'complexity_score': response.query_analysis.complexity_score,
                'profile_completeness': response.query_analysis.user_profile_completeness,
                'intent': response.query_analysis.intent,
                'keywords': response.query_analysis.keywords
            },
            'processing_time': response.processing_time,
            'ml_insights': response.ml_insights,
            'gpt_analysis': response.gpt_analysis,
            'quick_actions': response.quick_actions,
            'follow_up_suggestions': response.follow_up_suggestions,
            'performance': {
                'cache_hit': response.cache_hit,
                'total_courses_analyzed': response.total_courses_analyzed
            }
        }
    
    def format_intelligence_indicator(self, level: IntelligenceLevel) -> str:
        """Format intelligence level indicator for UI"""
        
        level_info = self.intelligence_labels[level]
        
        return f"{level_info['icon']} **{level_info['name']}** - {level_info['description']}"
    
    def create_comparison_table(self, responses: List[UnifiedResponse]) -> str:
        """Create comparison table for multiple responses"""
        
        if not responses:
            return ""
        
        comparison = "\n## 📊 **Intelligence Level Comparison**\n\n"
        comparison += "| Level | Confidence | Processing Time | Recommendations |\n"
        comparison += "|-------|------------|-----------------|----------------|\n"
        
        for response in responses:
            level_info = self.intelligence_labels[response.intelligence_level]
            comparison += f"| {level_info['icon']} {level_info['name']} | "
            comparison += f"{response.confidence:.0%} | "
            comparison += f"{response.processing_time:.2f}s | "
            comparison += f"{len(response.recommendations)} |\n"
        
        return comparison
    
    def get_formatting_stats(self) -> Dict:
        """Get formatting statistics"""
        
        total = self.formatting_stats['total_responses']
        if total == 0:
            return self.formatting_stats
        
        return {
            **self.formatting_stats,
            'basic_percentage': (self.formatting_stats['basic_responses'] / total) * 100,
            'enhanced_percentage': (self.formatting_stats['enhanced_responses'] / total) * 100,
            'expert_percentage': (self.formatting_stats['expert_responses'] / total) * 100
        }
    
    def reset_stats(self):
        """Reset formatting statistics"""
        self.formatting_stats = {
            'total_responses': 0,
            'basic_responses': 0,
            'enhanced_responses': 0,
            'expert_responses': 0
        }

# Test the formatter
if __name__ == "__main__":
    print("🎨 Testing Response Formatter...")
    
    from intelligence_router import IntelligenceRouter, QueryAnalysis
    
    # Create test response
    test_analysis = QueryAnalysis(
        complexity_score=0.6,
        user_profile_completeness=0.8,
        needs_personalization=True,
        needs_expert_validation=False,
        keywords=['machine learning', 'computer science'],
        intent='course_recommendation',
        confidence=0.85,
        reasoning=['Medium complexity query benefits from enhanced processing']
    )
    
    test_recommendations = [
        {
            'course_code': 'COMP 382',
            'title': 'Reasoning for Complexity',
            'department': 'Computer Science',
            'credit_hours': '4',
            'similarity_score': 0.92,
            'success_probability': 0.87,
            'description': 'Introduction to machine learning algorithms and applications.',
            'prerequisites': 'COMP 182, MATH 212',
            'reasoning': 'Strong match for machine learning interests with solid prerequisites'
        },
        {
            'course_code': 'COMP 540',
            'title': 'Statistical Machine Learning',
            'department': 'Computer Science',
            'credit_hours': '3',
            'similarity_score': 0.88,
            'success_probability': 0.82,
            'description': 'Advanced statistical approaches to machine learning.',
            'prerequisites': 'COMP 382, STAT 310',
            'reasoning': 'Advanced ML course building on foundational knowledge'
        }
    ]
    
    test_response = UnifiedResponse(
        recommendations=test_recommendations,
        intelligence_level=IntelligenceLevel.ENHANCED,
        confidence=0.85,
        reasoning=[
            'ML-enhanced recommendations based on your profile',
            'Success probabilities calculated for each course',
            'Optimized for your computer science major'
        ],
        query_analysis=test_analysis,
        processing_time=0.45,
        ml_insights=[
            'Your profile suggests high success rate in advanced courses',
            'Consider taking STAT 310 before COMP 540 for better preparation'
        ],
        quick_actions=[
            '📅 Plan full semester with these courses',
            '🔍 Find similar ML courses',
            '🧠 Get GPT expert analysis'
        ],
        follow_up_suggestions=[
            'Complete prerequisite courses first',
            'Consider adding MATH 355 for stronger mathematical foundation'
        ],
        total_courses_analyzed=6358
    )
    
    # Test formatting
    formatter = ResponseFormatter()
    formatted_display = formatter.format_for_display(test_response)
    formatted_json = formatter.format_for_json(test_response)
    
    print("\n🎨 Formatted Display:")
    print(formatted_display)
    
    print("\n📊 JSON Format:")
    print(json.dumps(formatted_json, indent=2))
    
    print("\n📈 Formatter Statistics:")
    stats = formatter.get_formatting_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n🎉 Response Formatter test complete!") 