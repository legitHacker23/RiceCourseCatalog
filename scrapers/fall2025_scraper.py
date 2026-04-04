#!/usr/bin/env python3
"""
Fall 2025 Course Schedule Scraper
==================================

Scrapes the actual Fall 2025 course schedule from Rice University's course website.
Extracts course codes, numbers, instructors, meeting times, credits, and distribution groups.

Author: Rice Course Assistant Team
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
from typing import List, Dict, Optional

class Fall2025Scraper:
    """Scraper for Fall 2025 course schedule data."""
    
    def __init__(self):
        self.base_url = "https://courses.rice.edu/courses/!SWKSCAT.cat"
        self.fall2025_url = "https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=QUERY&p_term=202610&p_ptrm=&p_crn=&p_onebar=&p_mode=AND&p_subj_cd=&p_subj=&p_dept=&p_school=&p_spon_coll=&p_df=All&p_insm=&p_submit=&as_fid=2df9dbce71ec05a423a3f872976292367909ccdd"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_fall2025_courses(self) -> Dict:
        """Scrape all Fall 2025 courses from the Rice course schedule."""
        print("Starting Fall 2025 course schedule scraping...")
        
        try:
            # Get the main course schedule page
            response = self.session.get(self.fall2025_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the course table - try different selectors
            course_table = soup.find('table')
            if not course_table:
                # Try to find any table
                tables = soup.find_all('table')
                print(f"Found {len(tables)} tables on the page")
                if tables:
                    course_table = tables[0]  # Use the first table
                else:
                    print("No course table found")
                    return self._create_empty_dataset()
            
            courses = []
            rows = course_table.find_all('tr')[1:]  # Skip header row
            
            print(f"Found {len(rows)} course rows to process...")
            
            # Debug: Print first few rows to understand structure
            for i, row in enumerate(rows[:3]):
                print(f"\nRow {i+1} structure:")
                cells = row.find_all('td')
                print(f"Number of cells: {len(cells)}")
                for j, cell in enumerate(cells):
                    print(f"  Cell {j}: '{cell.text.strip()}'")
                    links = cell.find_all('a')
                    if links:
                        print(f"    Links: {[link.text.strip() for link in links]}")
            
            for i, row in enumerate(rows):
                if i % 50 == 0:
                    print(f"Processing course {i+1}/{len(rows)}...")
                
                course_data = self._parse_course_row(row)
                if course_data:
                    # Fetch distribution group from individual course page
                    distribution_group = self._get_distribution_group(course_data['crn'])
                    course_data['distribution_group'] = distribution_group
                    courses.append(course_data)
                
                # Be respectful with requests
                time.sleep(0.2)  # Increased delay since we're making more requests
            
            # Create the dataset
            dataset = self._create_dataset(courses)
            
            print(f"Successfully scraped {len(courses)} Fall 2025 courses")
            return dataset
            
        except Exception as e:
            print(f"Error scraping Fall 2025 courses: {e}")
            return self._create_empty_dataset()
    
    def _parse_course_row(self, row) -> Optional[Dict]:
        """Parse a single course row from the table."""
        try:
            cells = row.find_all('td')
            if len(cells) < 7:  # Need at least 7 cells for complete data
                return None
            
            # Extract CRN (Course Registration Number) - first column
            crn = cells[0].text.strip()
            
            # Extract course code and number - second column
            course_text = cells[1].text.strip()
            course_parts = course_text.split()
            if len(course_parts) < 2:
                return None
            
            subject_code = course_parts[0]
            course_number = course_parts[1]
            section = course_parts[2] if len(course_parts) > 2 else "001"
            
            # Extract title - fourth column
            title = cells[3].text.strip()
            
            # Extract instructor - fifth column
            instructor_text = cells[4].text.strip()
            instructors = [instructor_text] if instructor_text else []
            
            # Extract meeting time - sixth column
            meeting_time = cells[5].text.strip()
            
            # Extract credits - seventh column
            credits = cells[6].text.strip()
            
            # Extract part of term - third column
            part_of_term = cells[2].text.strip()
            
            return {
                'crn': crn,
                'subject_code': subject_code,
                'course_number': course_number,
                'section': section,
                'course_code': f"{subject_code} {course_number}",
                'title': title,
                'instructors': instructors,
                'meeting_time': meeting_time,
                'credits': credits,
                'part_of_term': part_of_term,
                'course_url': f"https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=COURSE&p_term=202610&p_crn={crn}"
            }
            
        except Exception as e:
            print(f"Error parsing course row: {e}")
            return None
    
    def _get_distribution_group(self, crn: str) -> Optional[str]:
        """Get distribution group from individual course page."""
        try:
            course_url = f"https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=COURSE&p_term=202610&p_crn={crn}"
            response = self.session.get(course_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for distribution group information
            # The text usually appears as "Distribution Group I", "Distribution Group II", etc.
            text_content = soup.get_text()
            
            # Search for distribution group pattern
            dist_group_match = re.search(r'Distribution Group\s+([I]+)', text_content)
            if dist_group_match:
                return dist_group_match.group(1)
            
            # Alternative search patterns
            dist_group_match = re.search(r'Distribution Group:\s*([I]+)', text_content)
            if dist_group_match:
                return dist_group_match.group(1)
            
            # Look for roman numerals after "Distribution"
            dist_group_match = re.search(r'Distribution[^A-Za-z]*([I]+)', text_content)
            if dist_group_match:
                return dist_group_match.group(1)
            
            return None
            
        except Exception as e:
            print(f"Error getting distribution group for CRN {crn}: {e}")
            return None
    
    def _parse_time_and_credits(self, time_credits_text: str) -> tuple:
        """Parse meeting time and credits from the combined text."""
        meeting_time = ""
        credits = ""
        
        try:
            # Split by common separators
            parts = re.split(r'\s+', time_credits_text.strip())
            
            # Find credits (usually at the end, numeric)
            for i, part in enumerate(parts):
                if part.isdigit() or (part.replace('.', '').isdigit() and '.' in part):
                    credits = part
                    # Everything before this is meeting time
                    meeting_time = ' '.join(parts[:i])
                    break
            
            # If no credits found, try to extract from common patterns
            if not credits:
                # Look for credit patterns like "3", "3 TO 6", etc.
                credit_match = re.search(r'(\d+(?:\s+TO\s+\d+)?)', time_credits_text)
                if credit_match:
                    credits = credit_match.group(1)
                    # Remove credits from meeting time
                    meeting_time = re.sub(r'\d+(?:\s+TO\s+\d+)?', '', time_credits_text).strip()
                else:
                    meeting_time = time_credits_text
            
            return meeting_time.strip(), credits.strip()
            
        except Exception as e:
            print(f"Error parsing time and credits: {e}")
            return time_credits_text.strip(), ""
    
    def _create_dataset(self, courses: List[Dict]) -> Dict:
        """Create the final dataset structure."""
        # Group courses by subject
        subjects = {}
        for course in courses:
            subject = course['subject_code']
            if subject not in subjects:
                subjects[subject] = []
            subjects[subject].append(course)
        
        # Calculate statistics
        total_courses = len(courses)
        total_subjects = len(subjects)
        
        # Count courses by subject
        subject_counts = {subject: len(courses_list) for subject, courses_list in subjects.items()}
        
        # Count courses by distribution group
        dist_group_counts = {}
        for course in courses:
            dist_group = course.get('distribution_group')
            if dist_group:
                if dist_group not in dist_group_counts:
                    dist_group_counts[dist_group] = 0
                dist_group_counts[dist_group] += 1
        
        return {
            'metadata': {
                'scraping_timestamp': datetime.now().isoformat(),
                'academic_year': '2025-2026',
                'semester': 'Fall 2025',
                'term_code': '202610',
                'source_url': self.fall2025_url,
                'total_courses': total_courses,
                'total_subjects': total_subjects,
                'scraper_version': 'fall2025_v1.1'
            },
            'statistics': {
                'total_courses': total_courses,
                'total_subjects': total_subjects,
                'subject_breakdown': subject_counts,
                'distribution_group_breakdown': dist_group_counts,
                'courses_with_instructors': len([c for c in courses if c['instructors']]),
                'courses_with_meeting_times': len([c for c in courses if c['meeting_time']]),
                'courses_with_credits': len([c for c in courses if c['credits']]),
                'courses_with_distribution_groups': len([c for c in courses if c.get('distribution_group')])
            },
            'courses': courses,
            'subjects': subjects
        }
    
    def _create_empty_dataset(self) -> Dict:
        """Create an empty dataset structure."""
        return {
            'metadata': {
                'scraping_timestamp': datetime.now().isoformat(),
                'academic_year': '2025-2026',
                'semester': 'Fall 2025',
                'term_code': '202610',
                'source_url': self.fall2025_url,
                'total_courses': 0,
                'total_subjects': 0,
                'scraper_version': 'fall2025_v1.1',
                'error': 'No courses found or scraping failed'
            },
            'statistics': {
                'total_courses': 0,
                'total_subjects': 0,
                'subject_breakdown': {},
                'distribution_group_breakdown': {},
                'courses_with_instructors': 0,
                'courses_with_meeting_times': 0,
                'courses_with_credits': 0,
                'courses_with_distribution_groups': 0
            },
            'courses': [],
            'subjects': {}
        }
    
    def save_dataset(self, dataset: Dict, filename: str = None) -> str:
        """Save the dataset to a JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fall2025_courses_{timestamp}.json"
        
        filepath = f"data/raw/{filename}"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(dataset, f, indent=2)
            
            print(f"Dataset saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error saving dataset: {e}")
            return ""

def main():
    """Main function to run the Fall 2025 scraper."""
    scraper = Fall2025Scraper()
    
    print("=" * 60)
    print("Fall 2025 Course Schedule Scraper")
    print("=" * 60)
    
    # Scrape the courses
    dataset = scraper.scrape_fall2025_courses()
    
    # Save the dataset
    if dataset['courses']:
        filepath = scraper.save_dataset(dataset)
        print(f"\nScraping completed successfully!")
        print(f"Total courses scraped: {dataset['metadata']['total_courses']}")
        print(f"Total subjects: {dataset['metadata']['total_subjects']}")
        print(f"Courses with distribution groups: {dataset['statistics']['courses_with_distribution_groups']}")
        print(f"Distribution group breakdown: {dataset['statistics']['distribution_group_breakdown']}")
        print(f"Dataset saved to: {filepath}")
    else:
        print("\nScraping failed - no courses found")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()