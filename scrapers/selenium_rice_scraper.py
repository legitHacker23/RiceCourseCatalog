#!/usr/bin/env python3
"""
Simple and Reliable Rice University Program Scraper using Selenium

This approach is much cleaner because:
- Actually renders the page like a browser
- Follows real links instead of constructing URLs
- Handles JavaScript and dynamic content
- Less prone to URL construction errors
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
import json
import logging
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Program:
    department: str
    program_name: str
    program_type: str
    program_url: str
    department_overview_url: str  # New field for department overview
    outcomes_url: str
    requirements_url: str
    has_outcomes: bool
    has_requirements: bool
    # Content fields
    overview_content: str = ""
    outcomes_content: str = ""
    requirements_content: str = ""

class SeleniumRiceScraper:
    def __init__(self, headless: bool = True, interactive: bool = True):
        self.setup_driver(headless)
        self.base_url = "https://ga.rice.edu"
        self.start_url = "https://ga.rice.edu/programs-study/departments-programs/"
        self.programs: List[Program] = []
        self.interactive = interactive
        
    def setup_driver(self, headless: bool):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def get_department_links(self) -> List[Dict[str, str]]:
        """Get all department links from the main page"""
        logger.info(f"Loading main page: {self.start_url}")
        self.driver.get(self.start_url)
        
        # Find all department links
        department_links = []
        
        # Try to find the specific navigation section that contains departments
        # Look for the "Departments and Programs" section in the navigation
        try:
            # Find the navigation menu that contains department links
            nav_sections = self.driver.find_elements(By.CSS_SELECTOR, "nav, .navigation, .menu, ul")
            
            for nav in nav_sections:
                links = nav.find_elements(By.TAG_NAME, "a")
                
                for link in links:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    # Skip UI elements and navigation
                    if not text or len(text) < 3:
                        continue
                        
                    # Skip common UI elements
                    ui_elements_to_skip = [
                        'print options', 'opens modal', 'skip to content', 'az index', 
                        'catalog home', 'rice university', 'search catalog', 'toggle menu',
                        'home', 'about', 'policies', 'programs', 'courses', 'archive',
                        'academic calendar', 'undergraduate students', 'graduate students',
                        'non-traditional students', 'faculty', 'administration and faculty',
                        'important notices', 'back to top', 'send page to printer',
                        'download page', 'cancel', 'print this page', 'print', 'modal'
                    ]
                    
                    text_lower = text.lower()
                    if any(ui_element in text_lower for ui_element in ui_elements_to_skip):
                        continue
                    
                    # Only include links that look like actual departments
                    if (href and 
                        "/programs-study/departments-programs/" in href and 
                        href != self.start_url and
                        href.count('/') >= 5 and  # Should have at least school/department structure
                        # Make sure it's not a UI element URL
                        not any(ui_word in href.lower() for ui_word in ['print', 'modal', 'button', 'menu', 'navigation'])):
                        
                        department_links.append({
                            "name": text,
                            "url": href
                        })
        
        except Exception as e:
            logger.error(f"Error finding department navigation: {e}")
            # Fallback to original method but with better filtering
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                href = link.get_attribute("href")
                text = link.text.strip()
                
                # Skip UI elements
                if not text or len(text) < 3:
                    continue
                    
                text_lower = text.lower()
                if any(ui_element in text_lower for ui_element in ['print options', 'opens modal', 'print', 'modal', 'button']):
                    continue
                
                if (href and 
                    "/programs-study/departments-programs/" in href and 
                    href != self.start_url and
                    href.count('/') >= 5 and
                    not any(ui_word in href.lower() for ui_word in ['print', 'modal', 'button'])):
                    
                    department_links.append({
                        "name": text,
                        "url": href
                    })
        
        # Remove duplicates
        seen = set()
        unique_departments = []
        for dept in department_links:
            if dept["url"] not in seen:
                seen.add(dept["url"])
                unique_departments.append(dept)
        
        logger.info(f"Found {len(unique_departments)} departments")
        return unique_departments
    
    def get_program_links_from_department(self, dept_url: str) -> List[Dict[str, str]]:
        """Get all program links from a department page"""
        try:
            self.driver.get(dept_url)
            time.sleep(1)  # Let page load
            
            program_links = []
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            # Look for program patterns in URLs - all degree types found in logs
            # Expanded to catch more complex URL structures
            degree_patterns = [
                '-ba/', '-bs/', '-bscs/', '-bsee/', '-bsce/', '-bsme/', '-bsmsne/', 
                '-bsbe/', '-bsche/', '-bmus/', '-barch/', '-basc/',
                '-ma/', '-ms/', '-meng/', '-mmus/', '-march/', '-mfa/', '-med/',
                '-phd/', '-dma/', '-jd/', '-md/', '-mba/', '-mpp/',
                # More flexible patterns to catch complex URLs
                '-ba-', '-bs-', '-bscs-', '-bsee-', '-bsce-', '-bsme-', '-bsmsne-',
                '-bsbe-', '-bsche-', '-bmus-', '-barch-', '-basc-',
                '-ma-', '-ms-', '-meng-', '-mmus-', '-march-', '-mfa-', '-med-',
                '-phd-', '-dma-', '-jd-', '-md-', '-mba-', '-mpp-'
            ]
            
            for link in links:
                href = link.get_attribute("href")
                text = link.text.strip()
                
                if href:
                    # Check if URL contains any degree type pattern (not just ends with)
                    program_type = "Unknown"
                    for pattern in degree_patterns:
                        if pattern in href.lower():  # FIXED: Changed from endswith() to in
                            program_type = pattern.strip('-/').upper()
                            
                            # Extract program name from URL if link text is empty or generic
                            if not text or text.lower() in ['program', 'degree', 'major', 'minor'] or text == program_type:
                                # Extract from URL path
                                url_parts = href.split('/')
                                if len(url_parts) >= 2:
                                    # Get the last meaningful part of the URL
                                    url_name = url_parts[-2] if url_parts[-1] == '' else url_parts[-1]
                                    
                                    # Remove the degree suffix from the URL
                                    degree_suffix = pattern.strip('-/')
                                    if url_name.endswith(f'-{degree_suffix}'):
                                        clean_name = url_name[:-len(f'-{degree_suffix}')]
                                    else:
                                        clean_name = url_name
                                    
                                    # Convert dashes to spaces and title case
                                    clean_name = clean_name.replace('-', ' ').title()
                                    
                                    # Use the cleaned name if it's meaningful
                                    if clean_name and len(clean_name) > 2:
                                        program_name = clean_name
                                    else:
                                        program_name = program_type  # Just use the degree type
                                else:
                                    program_name = program_type  # Just use the degree type
                            else:
                                program_name = text
                            
                            program_links.append({
                                "name": program_name,
                                "url": href,
                                "type": program_type
                            })
                            break
            
            # Remove duplicates
            seen = set()
            unique_programs = []
            for prog in program_links:
                if prog["url"] not in seen:
                    seen.add(prog["url"])
                    unique_programs.append(prog)
            
            return unique_programs
            
        except Exception as e:
            logger.error(f"Error processing department {dept_url}: {e}")
            return []
    
    def check_program_sections(self, program_url: str) -> Dict[str, str]:
        """Check if program has outcomes and requirements sections"""
        try:
            self.driver.get(program_url)
            time.sleep(1)
            
            # Check for outcomes section
            outcomes_url = program_url.rstrip('/') + '/#outcomestext'
            requirements_url = program_url.rstrip('/') + '/#requirementstext'
            
            # Try to find outcomes and requirements sections on the page
            page_source = self.driver.page_source.lower()
            has_outcomes = 'outcomes' in page_source or 'learning outcomes' in page_source
            has_requirements = 'requirements' in page_source or 'degree requirements' in page_source
            
            return {
                "outcomes_url": outcomes_url if has_outcomes else None,
                "requirements_url": requirements_url if has_requirements else None,
                "has_outcomes": has_outcomes,
                "has_requirements": has_requirements
            }
            
        except Exception as e:
            logger.error(f"Error checking sections for {program_url}: {e}")
            return {
                "outcomes_url": None,
                "requirements_url": None,
                "has_outcomes": False,
                "has_requirements": False
            }
    
    def extract_overview_content(self, dept_overview_url: str) -> str:
        """Extract overview content from the department page overview section"""
        try:
            self.driver.get(dept_overview_url)
            time.sleep(2)  # Let page load
            
            overview_content = ""
            
            # Strategy 1: Target the specific Rice page structure with #textcontainer
            try:
                # Find the main content container (this is the key element from your HTML)
                text_container = self.driver.find_element(By.ID, "textcontainer")
                
                # Extract all paragraphs from the text container
                paragraphs = text_container.find_elements(By.TAG_NAME, "p")
                
                # Collect overview paragraphs (skip contact info)
                overview_paragraphs = []
                for p in paragraphs:
                    text = p.text.strip()
                    if not text:
                        continue
                    
                    # Skip contact info paragraphs (they contain email, phone, building info)
                    if any(skip in text.lower() for skip in [
                        '@rice.edu', '713-', 'building', 'mailto:', 'https://',
                        'phone', 'fax', 'office', 'room', 'hall'
                    ]):
                        continue
                    
                    # Skip very short paragraphs (likely navigation or UI elements)
                    if len(text) < 50:
                        continue
                    
                    # Skip paragraphs that look like degree requirements or program info
                    if any(skip in text.lower() for skip in [
                        'bachelor of arts degree with a major in',
                        'bachelor of science degree with a major in',
                        'master of arts degree',
                        'master of science degree',
                        'phd degree',
                        'degree requirements',
                        'course requirements',
                        'total credit hours required'
                    ]):
                        continue
                    
                    # This is likely overview content
                    overview_paragraphs.append(text)
                
                # Combine all overview paragraphs
                if overview_paragraphs:
                    overview_content = ' '.join(overview_paragraphs)
                else:
                    overview_content = ""
                
            except NoSuchElementException:
                # Strategy 2: Fallback - look for paragraphs with substantial content
                try:
                    paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
                    
                    substantial_paragraphs = []
                    for p in paragraphs:
                        text = p.text.strip()
                        if not text:
                            continue
                        
                        # Look for substantial paragraphs (long enough to be overview content)
                        if (len(text) > 150 and 
                            not any(skip in text.lower() for skip in [
                                'email', 'phone', 'fax', 'office', 'room', 'hall', 'building',
                                'rice university', 'catalog', 'programs', 'courses',
                                'bachelor', 'master', 'phd', 'degree', 'requirements',
                                'faculty', 'professor', 'associate professor', 'assistant professor',
                                'print options', 'send page to printer', 'download page'
                            ])):
                            
                            substantial_paragraphs.append(text)
                    
                    # Use the first substantial paragraph as overview
                    if substantial_paragraphs:
                        overview_content = substantial_paragraphs[0]
                    else:
                        overview_content = ""
                        
                except Exception as e:
                    overview_content = ""
            
            # Clean up the content
            overview_content = self.clean_content(overview_content)
            
            return overview_content
            
        except Exception as e:
            logger.error(f"Error accessing overview page {dept_overview_url}: {e}")
            return ""
    
    def extract_outcomes_content(self, outcomes_url: str) -> str:
        """Extract outcomes content from the outcomes section"""
        try:
            self.driver.get(outcomes_url)
            time.sleep(2)  # Let page load
            
            outcomes_content = ""
            
            # Strategy 1: Target the specific Rice outcomes structure with #outcomestextcontainer
            try:
                # Find the main outcomes container (this is the key element from your HTML)
                outcomes_container = self.driver.find_element(By.ID, "outcomestextcontainer")
                
                # Extract all content from the outcomes container
                outcomes_content = outcomes_container.text.strip()
                
                # If we got content, clean it up
                if outcomes_content:
                    # Keep all content including header and introductory text
                    # Just clean up excessive whitespace
                    outcomes_content = ' '.join(outcomes_content.split())
                
            except NoSuchElementException:
                # Strategy 2: Try the old ID approach
                try:
                    outcomes_element = self.driver.find_element(By.ID, "outcomestext")
                    outcomes_content = outcomes_element.text.strip()
                except NoSuchElementException:
                    # Strategy 3: Search for outcomes content in page text
                    try:
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if "outcomes" in page_text.lower():
                            outcomes_content = self.extract_section_around_keyword(page_text, "outcomes")
                        else:
                            outcomes_content = ""
                    except Exception as e:
                        outcomes_content = ""
            
            # Clean up the content
            outcomes_content = self.clean_content(outcomes_content)
            
            return outcomes_content
            
        except Exception as e:
            logger.error(f"Error accessing outcomes page {outcomes_url}: {e}")
            return ""
    
    def extract_requirements_content(self, requirements_url: str) -> str:
        """Extract requirements content from the requirements section"""
        try:
            self.driver.get(requirements_url)
            time.sleep(2)  # Let page load
            
            requirements_content = ""
            
            # Strategy 1: Target the specific Rice requirements structure with #requirementstextcontainer
            try:
                # Find the main requirements container (this is the key element from your HTML)
                requirements_container = self.driver.find_element(By.ID, "requirementstextcontainer")
                
                # Extract all content from the requirements container
                requirements_content = requirements_container.text.strip()
                
                # If we got content, clean it up
                if requirements_content:
                    # Keep all content including header and course lists
                    # Just clean up excessive whitespace
                    requirements_content = ' '.join(requirements_content.split())
                
            except NoSuchElementException:
                # Strategy 2: Try the old ID approach
                try:
                    requirements_element = self.driver.find_element(By.ID, "requirementstext")
                    requirements_content = requirements_element.text.strip()
                except NoSuchElementException:
                    # Strategy 3: Search for requirements content in page text
                    try:
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if "requirements" in page_text.lower():
                            requirements_content = self.extract_section_around_keyword(page_text, "requirements")
                        else:
                            requirements_content = ""
                    except Exception as e:
                        requirements_content = ""
            
            # Clean up the content
            requirements_content = self.clean_content(requirements_content)
            
            return requirements_content
            
        except Exception as e:
            logger.error(f"Error accessing requirements page {requirements_url}: {e}")
            return ""
    
    def extract_section_around_keyword(self, text: str, keyword: str) -> str:
        """Extract content around a specific keyword"""
        try:
            # Find the keyword in the text
            keyword_index = text.lower().find(keyword.lower())
            if keyword_index != -1:
                # Extract content around the keyword (1000 chars before and after)
                start = max(0, keyword_index - 1000)
                end = min(len(text), keyword_index + 2000)
                return text[start:end].strip()
            return ""
        except:
            return ""
    
    def clean_content(self, content: str) -> str:
        """Clean and format the extracted content"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = ' '.join(content.split())
        
        # Remove common navigation text
        unwanted_phrases = [
            "skip to content", "az index", "catalog home", "rice university",
            "search catalog", "toggle menu", "home", "about", "policies",
            "programs", "courses", "archive", "print options", "opens modal"
        ]
        
        for phrase in unwanted_phrases:
            content = content.replace(phrase, "")
        
        # Clean up again after removing phrases
        content = ' '.join(content.split())
        
        return content
    
    def scrape_all_programs(self) -> List[Program]:
        """Main scraping method"""
        logger.info("Starting comprehensive scrape...")
        
        # Get all departments
        departments = self.get_department_links()
        
        total_programs = 0
        
        for i, dept in enumerate(departments, 1):
            logger.info(f"Processing department {i}/{len(departments)}: {dept['name']}")
            
            # Get programs from this department
            programs = self.get_program_links_from_department(dept["url"])
            
            if not programs:
                logger.info(f"  No programs found automatically - skipping department")
                if self.interactive:
                    print(f"\n🔍 NO PROGRAMS FOUND in {dept['name']}")
                    print(f"Department URL: {dept['url']}")
                    manual_input = input("Enter program URL to add (or press Enter to skip department): ").strip()
                else:
                    manual_input = None
                    
                if manual_input:
                    # Parse the URL to extract program info
                    program_name = manual_input.split('/')[-2] if manual_input.endswith('/') else manual_input.split('/')[-1]
                    degree_type = "UNKNOWN"
                    for pattern in ['-ba/', '-bs/', '-bscs/', '-bsee/', '-bsce/', '-bsme/', '-bsmsne/', '-bsbe/', '-bsche/', '-bmus/', '-barch/', '-basc/', '-ma/', '-ms/', '-meng/', '-mmus/', '-march/', '-mfa/', '-med/', '-phd/', '-dma/', '-jd/', '-md/', '-mba/', '-mpp/']:
                        if pattern in manual_input.lower():
                            degree_type = pattern.strip('-/').upper()
                            break
                    
                    programs = [{
                        "name": program_name,
                        "url": manual_input,
                        "type": degree_type
                    }]
                    logger.info(f"  Added manual program: {program_name} ({degree_type})")
            
            for program in programs:
                # Skip graduate programs (PhD, Masters, etc.)
                graduate_programs = ['PHD', 'MA', 'MS', 'MENG', 'MMUS', 'MARCH', 'MFA', 'MED', 'DMA', 'JD', 'MD', 'MBA', 'MPP']
                if program['type'] in graduate_programs:
                    continue
                
                logger.info(f"  Found program: {program['name']} ({program['type']})")
                
                # Test if URL is accessible
                try:
                    self.driver.get(program["url"])
                    time.sleep(0.5)
                    accessible = "404" not in self.driver.title.lower()
                    if accessible:
                        logger.info(f"    ✅ Accessible")
                    else:
                        logger.info(f"    ❌ 404 Error")
                        # Ask user for correct URL
                        if self.interactive:
                            print(f"\n🔍 URL NOT FOUND: {program['url']}")
                            print(f"Program: {program['name']} ({program['type']})")
                            print(f"Department: {dept['name']}")
                            user_url = input("Enter correct URL (or press Enter to skip): ").strip()
                        else:
                            user_url = None
                        if user_url:
                            program["url"] = user_url
                            # Test the user-provided URL
                            try:
                                self.driver.get(user_url)
                                time.sleep(0.5)
                                accessible = "404" not in self.driver.title.lower()
                                if accessible:
                                    logger.info(f"    ✅ User URL works!")
                                else:
                                    logger.info(f"    ❌ User URL also 404")
                            except:
                                accessible = False
                                logger.info(f"    ❌ Error with user URL")
                        else:
                            logger.info(f"    ⏭️ Skipping this program")
                except:
                    accessible = False
                    logger.info(f"    ❌ Error accessing")
                    # Ask user for correct URL
                    if self.interactive:
                        print(f"\n🔍 URL ERROR: {program['url']}")
                        print(f"Program: {program['name']} ({program['type']})")
                        print(f"Department: {dept['name']}")
                        user_url = input("Enter correct URL (or press Enter to skip): ").strip()
                    else:
                        user_url = None
                    if user_url:
                        program["url"] = user_url
                        # Test the user-provided URL
                        try:
                            self.driver.get(user_url)
                            time.sleep(0.5)
                            accessible = "404" not in self.driver.title.lower()
                            if accessible:
                                logger.info(f"    ✅ User URL works!")
                            else:
                                accessible = False
                                logger.info(f"    ❌ User URL also has issues")
                        except:
                            accessible = False
                            logger.info(f"    ❌ Error with user URL")
                    else:
                        logger.info(f"    ⏭️ Skipping this program")
                
                # Check program sections only if accessible
                if accessible:
                    sections = self.check_program_sections(program["url"])
                else:
                    sections = {
                        "outcomes_url": None,
                        "requirements_url": None,
                        "has_outcomes": False,
                        "has_requirements": False
                    }
                
                # Create department overview URL from program URL
                # From: https://ga.rice.edu/programs-study/departments-programs/architecture/architecture/architecture-ba/
                # To:   https://ga.rice.edu/programs-study/departments-programs/architecture/architecture/#text
                program_url_parts = program["url"].split('/')
                dept_overview_url = None
                if len(program_url_parts) >= 7:
                    # Remove the last part (program name) and add #text
                    dept_overview_url = '/'.join(program_url_parts[:-2]) + '/#text'
                
                # Create program object
                program_obj = Program(
                    department=dept["name"],
                    program_name=program["name"],
                    program_type=program["type"],
                    program_url=program["url"],
                    department_overview_url=dept_overview_url,
                    outcomes_url=program["url"].rstrip('/') + '/#outcomestext' if accessible else None,  # FIXED: Added #outcomestext
                    requirements_url=program["url"].rstrip('/') + '/#requirementstext' if accessible else None,
                    has_outcomes=sections["has_outcomes"],
                    has_requirements=sections["has_requirements"]
                )
                
                # Extract content immediately after creating the program object
                if accessible:
                    logger.info(f"    📄 Extracting content for {program['name']}...")
                    
                    # Extract overview content
                    if dept_overview_url:
                        overview_content = self.extract_overview_content(dept_overview_url)
                        program_obj.overview_content = overview_content
                    
                    # Extract outcomes content
                    if sections["has_outcomes"]:
                        outcomes_content = self.extract_outcomes_content(program_obj.outcomes_url)
                        program_obj.outcomes_content = outcomes_content
                    
                    # Extract requirements content
                    if sections["has_requirements"]:
                        requirements_content = self.extract_requirements_content(program_obj.requirements_url)
                        program_obj.requirements_content = requirements_content
                    
                    # Log summary of content extraction
                    overview_chars = len(program_obj.overview_content)
                    outcomes_chars = len(program_obj.outcomes_content)
                    requirements_chars = len(program_obj.requirements_content)
                    logger.info(f"    ✅ Extracted content: Overview({overview_chars}), Outcomes({outcomes_chars}), Requirements({requirements_chars})")
                    
                    # Small delay between content extractions
                    time.sleep(1)
                
                self.programs.append(program_obj)
                total_programs += 1
            
            # Small delay between departments
            time.sleep(0.5)
        
        logger.info(f"Scraping complete! Found {total_programs} programs")
        return self.programs
    
    def save_results(self, filename: str = None):
        """Save results to JSON file"""
        if filename is None:
            filename = f"selenium_rice_programs_with_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "scrape_date": datetime.now().isoformat(),
            "scraper_type": "selenium_with_content",
            "total_programs": len(self.programs),
            "programs": [asdict(program) for program in self.programs]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {filename}")
        return filename
    
    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "="*70)
        print("🎓 SELENIUM RICE UNIVERSITY SCRAPER RESULTS")
        print("="*70)
        print(f"Total Programs Found: {len(self.programs)}")
        
        # By department
        dept_counts = {}
        for prog in self.programs:
            dept = prog.department
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        print(f"\nTop 10 Departments by Program Count:")
        for dept, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {dept}: {count} programs")
        
        # By program type
        type_counts = {}
        for prog in self.programs:
            ptype = prog.program_type
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
        
        print(f"\nBy Program Type:")
        for ptype, count in sorted(type_counts.items()):
            print(f"  {ptype}: {count} programs")
        
        # Content availability
        accessible = sum(1 for p in self.programs if p.outcomes_url is not None)
        with_outcomes = sum(1 for p in self.programs if p.has_outcomes)
        with_requirements = sum(1 for p in self.programs if p.has_requirements)
        
        # Content extraction results
        with_overview_content = sum(1 for p in self.programs if p.overview_content)
        with_outcomes_content = sum(1 for p in self.programs if p.outcomes_content)
        with_requirements_content = sum(1 for p in self.programs if p.requirements_content)
        
        print(f"\nContent Availability:")
        print(f"  Accessible Programs: {accessible}/{len(self.programs)} ({accessible/len(self.programs)*100:.1f}%)")
        print(f"  Programs with Outcomes: {with_outcomes}")
        print(f"  Programs with Requirements: {with_requirements}")
        
        print(f"\nContent Extraction Results:")
        print(f"  Programs with Overview Content: {with_overview_content}/{len(self.programs)} ({with_overview_content/len(self.programs)*100:.1f}%)")
        print(f"  Programs with Outcomes Content: {with_outcomes_content}/{len(self.programs)} ({with_outcomes_content/len(self.programs)*100:.1f}%)")
        print(f"  Programs with Requirements Content: {with_requirements_content}/{len(self.programs)} ({with_requirements_content/len(self.programs)*100:.1f}%)")
        
        print("\nSample Programs:")
        for i, prog in enumerate(self.programs[:3]):
            print(f"{i+1}. {prog.department} - {prog.program_name} ({prog.program_type})")
            print(f"   URL: {prog.program_url}")
            print(f"   Outcomes: {'✓' if prog.has_outcomes else '✗'} ({len(prog.outcomes_content)} chars)")
            print(f"   Requirements: {'✓' if prog.has_requirements else '✗'} ({len(prog.requirements_content)} chars)")
            print(f"   Overview: {'✓' if prog.overview_content else '✗'} ({len(prog.overview_content)} chars)")
            print()
        
        print("="*70)
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

def main():
    """Main execution"""
    print("🎓 Rice University Program Scraper")
    print("=" * 50)
    
    # Interactive mode for better user control
    scraper = SeleniumRiceScraper(headless=False, interactive=True)
    
    try:
        # Run the scraper
        programs = scraper.scrape_all_programs()
        
        # Save results
        filename = scraper.save_results()
        
        # Print summary
        scraper.print_summary()
        
        print(f"\n✅ Scraping complete! Results saved to: {filename}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 