import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

class RiceCourseScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome driver options"""
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.scraped_crns = set()
        self.all_courses = []
        self.subject_codes = []  # Will be populated by scraping
    
    def scrape_subject_codes(self):
        """Scrape all available subject codes from the main course catalog page"""
        print("Scraping subject codes from Rice University catalog...")
        
        try:
            # Navigate to the main course catalog page
            self.driver.get("https://courses.rice.edu/courses/!SWKSCAT.cat")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for subject dropdown or links
            subject_elements = []
            
            # Try different selectors for subject codes
            selectors = [
                "select[name='p_subj_cd'] option",  # Subject dropdown
                "select[name='p_subj'] option",     # Alternative subject dropdown
                "a[href*='p_subj_cd=']",           # Subject links
                "option[value*='']"                 # Any option values
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"Found subject elements using selector: {selector}")
                        subject_elements = elements
                        break
                except:
                    continue
            
            # If no dropdown found, look for any pattern that might contain subject codes
            if not subject_elements:
                # Try to find subject codes in the page source
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Look for select elements
                selects = soup.find_all('select')
                for select in selects:
                    if 'subj' in str(select).lower():
                        options = select.find_all('option')
                        subject_elements = [opt.get('value') for opt in options if opt.get('value')]
                        break
            
            # Extract subject codes
            subject_codes = set()
            
            if subject_elements:
                for element in subject_elements:
                    try:
                        # If it's a Selenium element
                        if hasattr(element, 'get_attribute'):
                            value = element.get_attribute('value')
                            text = element.text.strip()
                        else:
                            # If it's a string from BeautifulSoup
                            value = element
                            text = element
                        
                        # Extract subject code (usually 3-4 letter codes)
                        if value and len(value) >= 3:
                            # Check if it's a valid subject code pattern
                            code_match = re.match(r'^[A-Z]{3,4}$', value.strip())
                            if code_match:
                                subject_codes.add(value.strip())
                        
                        # Also check text content for subject codes
                        if text:
                            code_match = re.search(r'^([A-Z]{3,4})', text.strip())
                            if code_match:
                                subject_codes.add(code_match.group(1))
                                
                    except Exception as e:
                        continue
            
            # Remove empty strings and common non-subject values
            subject_codes = {code for code in subject_codes if code and code not in ['', 'ALL', 'NONE']}
            
            # If we still don't have codes, try a different approach
            if not subject_codes:
                print("Trying alternative method to find subject codes...")
                
                # Look for any 3-4 letter uppercase codes in the page
                page_text = self.driver.page_source
                potential_codes = re.findall(r'\b([A-Z]{3,4})\b', page_text)
                
                # Filter to likely subject codes (common patterns)
                common_subjects = {'MATH', 'COMP', 'ENGL', 'HIST', 'CHEM', 'PHYS', 'BIOS', 'ECON', 'PSYC'}
                subject_codes = {code for code in potential_codes if code in common_subjects}
                
                # If still empty, use a minimal fallback
                if not subject_codes:
                    subject_codes = {'COMP', 'MATH', 'ENGL', 'HIST', 'CHEM', 'PHYS'}
                    print("Using fallback subject codes")
            
            self.subject_codes = sorted(list(subject_codes))
            
            print(f"Found {len(self.subject_codes)} subject codes:")
            for code in self.subject_codes:
                print(f"  - {code}")
            
            return self.subject_codes
            
        except Exception as e:
            print(f"Error scraping subject codes: {e}")
            # Fallback to common codes
            self.subject_codes = ['COMP', 'MATH', 'ENGL', 'HIST', 'CHEM', 'PHYS', 'BIOS', 'ECON']
            print("Using fallback subject codes")
            return self.subject_codes
    
    def get_subject_url(self, subject_code):
        """Generate URL for a specific subject code"""
        base_url = "https://courses.rice.edu/courses/!SWKSCAT.cat"
        params = (
            f"?p_action=QUERY&p_term=202610&p_ptrm=&p_crn=&p_onebar=&p_mode=AND"
            f"&p_subj_cd={subject_code}&p_subj={subject_code}&p_dept=&p_school=&p_spon_coll="
            f"&p_df=&p_insm=&p_submit=&as_fid=2df9dbce71ec05a423a3f872976292367909ccdd"
        )
        return base_url + params
    
    def parse_course_info(self, course_element):
        """Parse course information from a course element"""
        try:
            # Get the HTML content
            html_content = course_element.get_attribute('innerHTML')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all text content and links
            text_content = course_element.text.strip()
            links = course_element.find_elements(By.TAG_NAME, "a")
            
            # Extract CRN (usually first number)
            crn_match = re.search(r'\b(\d{5})\b', text_content)
            if not crn_match:
                return None
            crn = crn_match.group(1)
            
            # Skip if already scraped
            if crn in self.scraped_crns:
                return None
            
            # Extract course code (pattern like "COMP 140")
            course_code_match = re.search(r'([A-Z]{4})\s+(\d{3})', text_content)
            if not course_code_match:
                return None
            
            subject_code = course_code_match.group(1)
            course_number = course_code_match.group(2)
            course_code = f"{subject_code} {course_number}"
            
            # Extract section (pattern like "001" or "002")
            section_match = re.search(r'\b(\d{3})\b', text_content.split(course_number)[1])
            section = section_match.group(1) if section_match else "001"
            
            # Extract title (usually after course code and section)
            title_pattern = rf'{course_code}\s+{section}\s+([A-Z][A-Z\s&,\-\(\)0-9:]+?)(?=\s+[A-Z][a-z]|\s+\d|\s+TBA|\s+STAFF|\s*$)'
            title_match = re.search(title_pattern, text_content)
            title = title_match.group(1).strip() if title_match else "Unknown Title"
            
            # Find and click the CRN link to get detailed course info
            course_url = ""
            distribution_group = ""
            
            for link in links:
                href = link.get_attribute('href')
                if href and 'COURSE' in href:
                    course_url = href
                    try:
                        # Click on the link to go to course detail page
                        link.click()
                        
                        # Wait for the detail page to load
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        
                        # Get the detail page content
                        detail_text = self.driver.page_source
                        detail_soup = BeautifulSoup(detail_text, 'html.parser')
                        
                        # Extract title from the detail page - look for course-specific content
                        page_text = detail_soup.get_text()
                        
                        # Look for course title patterns in the page text
                        title_patterns = [
                            rf'{course_code}\s+{section}\s+([^\n\r]+?)(?=\s+\d|\s+Credit|\s+Instructor|\s+Meeting|$)',
                            rf'{subject_code}\s+{course_number}\s+([^\n\r]+?)(?=\s+\d|\s+Credit|\s+Instructor|\s+Meeting|$)',
                            r'Course Title[:\s]+([^\n\r]+?)(?=\s+\d|\s+Credit|\s+Instructor|\s+Meeting|$)',
                            r'Title[:\s]+([^\n\r]+?)(?=\s+\d|\s+Credit|\s+Instructor|\s+Meeting|$)'
                        ]
                        
                        for pattern in title_patterns:
                            title_match = re.search(pattern, page_text, re.IGNORECASE)
                            if title_match:
                                potential_title = title_match.group(1).strip()
                                # Clean up the title
                                potential_title = re.sub(r'\s+', ' ', potential_title)
                                # Filter out common page headers
                                if (len(potential_title) > 5 and 
                                    not potential_title.isupper() and
                                    'course schedule' not in potential_title.lower() and
                                    'catalog' not in potential_title.lower() and
                                    'rice university' not in potential_title.lower()):
                                    title = potential_title
                                    break
                        
                        # Extract distribution group
                        dist_patterns = [
                            r'Group\s+([IVX]+)',
                            r'Distribution\s+Group\s+([IVX]+)',
                            r'([IVX]+)\s+Group'
                        ]
                        
                        for pattern in dist_patterns:
                            dist_match = re.search(pattern, detail_text, re.IGNORECASE)
                            if dist_match:
                                distribution_group = dist_match.group(1)
                                break
                        
                        # Go back to the search results page
                        self.driver.back()
                        
                        # Wait for the search results page to load again
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        
                        break
                        
                    except Exception as e:
                        print(f"Error getting course details for CRN {crn}: {e}")
                        # Go back if we're on the wrong page
                        if "COURSE" in self.driver.current_url:
                            self.driver.back()
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.TAG_NAME, "body"))
                            )
                        continue
            
            # Extract instructors (names with capital letters)
            instructor_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*(?:,\s*[A-Z][a-z]+)*)'
            instructors = []
            for match in re.finditer(instructor_pattern, text_content):
                name = match.group(1).strip()
                # Filter out common non-instructor words
                if name not in ['TBA', 'STAFF', 'No', 'Final', 'Exam', 'Full', 'Term', 'Group'] and len(name) > 2:
                    instructors.append(name)
            
            # Clean up instructor list (remove duplicates and common false positives)
            instructors = list(set(instructors))
            instructors = [name for name in instructors if not re.match(r'^[A-Z]{2,4}$', name)]
            
            # Extract meeting time
            time_pattern = r'(\d{1,2}:\d{2}[AP]M\s*-\s*\d{1,2}:\d{2}[AP]M\s+[MTWRFSU]+(?:\s+No\s+Final\s+Exam)?|TBA)'
            time_match = re.search(time_pattern, text_content)
            meeting_time = time_match.group(1) if time_match else "TBA"
            
            # Extract credits
            credits_match = re.search(r'(\d+)\s*credit', text_content.lower())
            credits = credits_match.group(1) if credits_match else "3"
            
            course_info = {
                "crn": crn,
                "subject_code": subject_code,
                "course_number": course_number,
                "section": section,
                "course_code": course_code,
                "title": title,
                "instructors": instructors,
                "meeting_time": meeting_time,
                "credits": credits,
                "part_of_term": "Full Term",  # Default value
                "course_url": course_url,
                "distribution_group": distribution_group
            }
            
            return course_info
            
        except Exception as e:
            print(f"Error parsing course: {e}")
            return None
    
    def scrape_subject(self, subject_code):
        """Scrape all courses for a specific subject code"""
        url = self.get_subject_url(subject_code)
        print(f"Scraping subject: {subject_code}")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Find all course elements (they're usually in table rows or specific divs)
            course_elements = self.driver.find_elements(By.XPATH, "//tr[contains(@class, 'row')]")
            
            # If no elements found with class 'row', try other selectors
            if not course_elements:
                course_elements = self.driver.find_elements(By.XPATH, "//tr[td]")
            
            if not course_elements:
                course_elements = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'CRN')]")
            
            course_count = 0
            for element in course_elements:
                course_info = self.parse_course_info(element)
                if course_info:
                    self.scraped_crns.add(course_info["crn"])
                    self.all_courses.append(course_info)
                    course_count += 1
                    print(f"Scraped: {course_info}")
            
            print(f"Found {course_count} courses for {subject_code}")
            time.sleep(1)  # Be respectful to the server
            
        except TimeoutException:
            print(f"Timeout while loading {subject_code}")
        except Exception as e:
            print(f"Error scraping {subject_code}: {e}")
    
    def scrape_all_courses(self):
        """Scrape all courses for all subject codes"""
        print("Starting Rice University course scraping...")
        
        # First, scrape all available subject codes
        self.scrape_subject_codes()
        
        if not self.subject_codes:
            print("No subject codes found. Exiting.")
            return
        
        print(f"Will scrape {len(self.subject_codes)} subjects")
        
        for i, subject_code in enumerate(self.subject_codes):
            print(f"\n--- Progress: {i+1}/{len(self.subject_codes)} ---")
            self.scrape_subject(subject_code)
        
        print(f"\nScraping complete!")
        print(f"Total courses scraped: {len(self.all_courses)}")
        print(f"Unique CRNs: {len(self.scraped_crns)}")
        
        # Print all subject codes that were scraped
        print(f"\nSubject codes scraped: {', '.join(self.subject_codes)}")
    
    def save_to_json(self, filename="rice_courses.json"):
        """Save all scraped courses to a JSON file"""
        import os
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_courses, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
    
    def close(self):
        """Close the browser driver"""
        self.driver.quit()

def main():
    # Create scraper instance
    scraper = RiceCourseScraper(headless=False)  # Set to True for headless mode
    
    try:
        # Scrape all courses
        scraper.scrape_all_courses()
        
        # Save to JSON file
        scraper.save_to_json("/Users/kacemettahali/Desktop/RiceCatalog/data/raw/rice_courses_202610.json")
        
        # Print summary
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        print(f"Total courses scraped: {len(scraper.all_courses)}")
        print(f"Unique CRNs: {len(scraper.scraped_crns)}")
        
        # Show sample of scraped data
        if scraper.all_courses:
            print("\nSample course data:")
            print(json.dumps(scraper.all_courses[0], indent=2))
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()