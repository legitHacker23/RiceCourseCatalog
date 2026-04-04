#!/usr/bin/env python3
"""
Rice University Distribution Credit Course Scraper

Scrapes the Rice University course catalog to extract distribution credit courses
and their details including distribution groups, credit hours, and diversity indicators.
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
import time
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DistributionCourse:
    course_code: str
    course_title: str
    distribution_group: str
    analyzing_diversity: str
    credit_hours: str
    course_url: str
    subject_code: str
    course_number: str

class RiceDistributionScraper:
    def __init__(self):
        self.base_url = "https://courses.rice.edu"
        self.catalog_url = "https://courses.rice.edu/admweb/!SWKSCAT.cat?p_acyr_code=2025&p_action=CATASRCH&p_onebar=&p_mode=AND&p_subj_cd=&p_subj=&p_dept=&p_school=&p_df=All&p_submit="
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.courses: List[DistributionCourse] = []
        
    def get_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage with retries"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None
    
    def parse_course_code(self, course_code: str) -> tuple:
        """Parse course code into subject and number"""
        match = re.match(r'([A-Z]{2,4})\s+(\d{3}[A-Z]?)', course_code)
        if match:
            return match.group(1), match.group(2)
        return "", ""
    
    def extract_distribution_courses(self, soup: BeautifulSoup) -> List[DistributionCourse]:
        """Extract distribution courses from the catalog page"""
        courses = []
        
        # Find the main course table
        table = soup.find('table')
        if not table:
            logger.error("No course table found on page")
            return courses
        
        # Extract table rows (skip header)
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:  # Ensure we have all required columns
                try:
                    # Extract course link and code
                    course_link = cells[0].find('a')
                    if course_link:
                        course_code = course_link.get_text(strip=True)
                        course_url = self.base_url + course_link.get('href', '')
                    else:
                        course_code = cells[0].get_text(strip=True)
                        course_url = ""
                    
                    # Extract other course details
                    course_title = cells[1].get_text(strip=True)
                    distribution_group = cells[2].get_text(strip=True)
                    
                    # Handle analyzing diversity column (can be in different positions)
                    analyzing_diversity = ""
                    credit_hours = ""
                    
                    if len(cells) >= 5:
                        analyzing_diversity = cells[3].get_text(strip=True)
                        credit_hours = cells[4].get_text(strip=True)
                    else:
                        # Sometimes analyzing diversity is empty and credit hours are in position 3
                        potential_credits = cells[3].get_text(strip=True)
                        if re.match(r'\d+', potential_credits):
                            credit_hours = potential_credits
                        else:
                            analyzing_diversity = potential_credits
                    
                    # Parse subject and course number
                    subject_code, course_number = self.parse_course_code(course_code)
                    
                    # Create course object
                    course = DistributionCourse(
                        course_code=course_code,
                        course_title=course_title,
                        distribution_group=distribution_group,
                        analyzing_diversity=analyzing_diversity,
                        credit_hours=credit_hours,
                        course_url=course_url,
                        subject_code=subject_code,
                        course_number=course_number
                    )
                    
                    courses.append(course)
                    logger.info(f"Extracted: {course_code} - {course_title}")
                    
                except Exception as e:
                    logger.warning(f"Error parsing course row: {e}")
                    continue
        
        return courses
    
    def scrape_all_distribution_courses(self) -> List[DistributionCourse]:
        """Scrape all distribution courses from the catalog"""
        logger.info("🚀 Starting Rice University distribution course scraping...")
        logger.info(f"📖 Scraping: {self.catalog_url}")
        
        soup = self.get_page(self.catalog_url)
        if not soup:
            logger.error("Failed to fetch catalog page")
            return []
        
        courses = self.extract_distribution_courses(soup)
        self.courses = courses
        
        logger.info(f"✅ Successfully scraped {len(courses)} distribution courses")
        return courses
    
    def get_courses_by_distribution_group(self, group: str) -> List[DistributionCourse]:
        """Get courses filtered by distribution group"""
        return [course for course in self.courses if group.lower() in course.distribution_group.lower()]
    
    def get_courses_by_subject(self, subject: str) -> List[DistributionCourse]:
        """Get courses filtered by subject code"""
        return [course for course in self.courses if subject.upper() == course.subject_code.upper()]
    
    def get_analyzing_diversity_courses(self) -> List[DistributionCourse]:
        """Get courses that fulfill analyzing diversity requirement"""
        return [course for course in self.courses if 'analyzing diversity' in course.analyzing_diversity.lower()]
    
    def get_courses_by_credit_hours(self, credits: str) -> List[DistributionCourse]:
        """Get courses filtered by credit hours"""
        return [course for course in self.courses if credits in course.credit_hours]
    
    def analyze_distribution_breakdown(self) -> Dict[str, int]:
        """Analyze the breakdown of courses by distribution group"""
        breakdown = {}
        for course in self.courses:
            group = course.distribution_group
            breakdown[group] = breakdown.get(group, 0) + 1
        return breakdown
    
    def analyze_subject_breakdown(self) -> Dict[str, int]:
        """Analyze the breakdown of courses by subject"""
        breakdown = {}
        for course in self.courses:
            subject = course.subject_code
            breakdown[subject] = breakdown.get(subject, 0) + 1
        return breakdown
    
    def save_results(self, filename: str = "rice_distribution_courses.json") -> Dict:
        """Save scraped results to JSON file"""
        # Prepare data for JSON serialization
        courses_data = [asdict(course) for course in self.courses]
        
        # Generate analysis
        distribution_breakdown = self.analyze_distribution_breakdown()
        subject_breakdown = self.analyze_subject_breakdown()
        analyzing_diversity_count = len(self.get_analyzing_diversity_courses())
        
        output_data = {
            'metadata': {
                'scraping_timestamp': datetime.now().isoformat(),
                'total_courses': len(self.courses),
                'catalog_url': self.catalog_url,
                'scraper_version': 'rice_distribution_v1.0'
            },
            'analysis': {
                'distribution_breakdown': distribution_breakdown,
                'subject_breakdown': subject_breakdown,
                'analyzing_diversity_courses': analyzing_diversity_count,
                'total_subjects': len(subject_breakdown),
                'total_distribution_groups': len(distribution_breakdown)
            },
            'courses': courses_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Results saved to {filename}")
        return output_data
    
    def print_summary(self):
        """Print a summary of scraped courses"""
        print("\n" + "="*70)
        print("🎓 RICE UNIVERSITY DISTRIBUTION COURSES SUMMARY")
        print("="*70)
        
        print(f"Total Courses Scraped: {len(self.courses)}")
        
        # Distribution group breakdown
        dist_breakdown = self.analyze_distribution_breakdown()
        print(f"\n📊 Distribution Group Breakdown:")
        for group, count in sorted(dist_breakdown.items()):
            print(f"  {group}: {count} courses")
        
        # Subject breakdown (top 10)
        subject_breakdown = self.analyze_subject_breakdown()
        print(f"\n📚 Top 10 Subjects by Course Count:")
        for subject, count in sorted(subject_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {subject}: {count} courses")
        
        # Analyzing diversity courses
        diversity_courses = self.get_analyzing_diversity_courses()
        print(f"\n🌍 Analyzing Diversity Courses: {len(diversity_courses)}")
        
        # Sample courses from each distribution group
        print(f"\n📋 Sample Courses by Distribution Group:")
        for group in sorted(dist_breakdown.keys()):
            group_courses = self.get_courses_by_distribution_group(group)
            if group_courses:
                print(f"\n  {group}:")
                for course in group_courses[:3]:  # Show first 3 courses
                    print(f"    {course.course_code}: {course.course_title} ({course.credit_hours} credits)")
        
        print(f"\n✅ Data ready for academic planning and course selection!")

def main():
    """Main scraping function"""
    scraper = RiceDistributionScraper()
    
    try:
        # Scrape all distribution courses
        courses = scraper.scrape_all_distribution_courses()
        
        if not courses:
            print("❌ No courses found. Please check the URL and try again.")
            return
        
        # Save results
        output_data = scraper.save_results()
        
        # Print summary
        scraper.print_summary()
        
        # Additional analysis examples
        print("\n" + "="*70)
        print("🔍 ADDITIONAL ANALYSIS EXAMPLES")
        print("="*70)
        
        # Example: Get all Distribution Group I courses
        group_i_courses = scraper.get_courses_by_distribution_group("Group I")
        print(f"\nDistribution Group I courses: {len(group_i_courses)}")
        
        # Example: Get all COMP courses
        comp_courses = scraper.get_courses_by_subject("COMP")
        print(f"Computer Science courses: {len(comp_courses)}")
        
        # Example: Get all 3-credit courses
        three_credit_courses = scraper.get_courses_by_credit_hours("3")
        print(f"3-credit courses: {len(three_credit_courses)}")
        
        print("\n📁 Detailed data saved to: rice_distribution_courses.json")
        
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main() 