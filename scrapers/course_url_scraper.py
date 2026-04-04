import json
import re
import os
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from collections import OrderedDict

def examine_json_structure():
    """
    Examine the structure of rice_organized_data.json to understand how to access courses
    """
    # Get the script directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_file = os.path.join(project_root, 'data', 'organized', 'rice_organized_data.json')
    
    print("Examining rice_organized_data.json structure...")
    
    # Load the data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Top-level keys: {list(data.keys())}")
    
    # Check if departments exists and examine its structure
    if 'departments' in data:
        departments = data['departments']
        dept_names = list(departments.keys())
        print(f"Number of departments: {len(dept_names)}")
        print(f"First 5 departments: {dept_names[:5]}")
        
        # Look at the structure of the first department
        if dept_names:
            first_dept = dept_names[0]
            dept_data = departments[first_dept]
            print(f"\nStructure of '{first_dept}' department:")
            print(f"Type: {type(dept_data)}")
            
            if isinstance(dept_data, dict):
                print(f"Keys in {first_dept}: {list(dept_data.keys())}")
                
                # Look at the courses within this department
                if 'courses' in dept_data:
                    courses = dept_data['courses']
                    print(f"\nCourses section type: {type(courses)}")
                    print(f"Number of courses: {len(courses) if isinstance(courses, list) else 'N/A'}")
                    
                    if isinstance(courses, list) and courses:
                        first_course = courses[0]
                        print(f"First course type: {type(first_course)}")
                        if isinstance(first_course, dict):
                            print(f"Course fields: {list(first_course.keys())}")
                            print(f"Sample course data: {first_course}")
                    elif isinstance(courses, dict):
                        course_keys = list(courses.keys())[:3]
                        print(f"First 3 course keys: {course_keys}")
                        if course_keys:
                            first_course = courses[course_keys[0]]
                            print(f"First course type: {type(first_course)}")
                            if isinstance(first_course, dict):
                                print(f"Course fields: {list(first_course.keys())}")
                                print(f"Sample course data: {first_course}")

def check_url_coverage():
    """
    Check how many courses currently have course_url fields in rice_organized_data.json
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_file = os.path.join(project_root, 'data', 'organized', 'rice_organized_data.json')
    
    print("🔍 Checking URL coverage in rice_organized_data.json...")
    
    # Load the data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    departments = data.get('departments', {})
    
    total_courses = 0
    courses_with_urls = 0
    courses_without_urls = 0
    empty_urls = 0
    invalid_urls = 0
    missing_examples = []
    
    for dept_code, dept_data in departments.items():
        courses = dept_data.get('courses', [])
        
        for course in courses:
            total_courses += 1
            
            # Check if course_url field exists
            if 'course_url' not in course:
                courses_without_urls += 1
                if len(missing_examples) < 5:
                    missing_examples.append({
                        'course_code': course.get('course_code', 'Unknown'),
                        'department': dept_code,
                        'issue': 'Missing course_url field'
                    })
                continue
            
            course_url = course.get('course_url', '')
            
            # Check if URL is empty
            if not course_url or course_url.strip() == '':
                empty_urls += 1
                if len(missing_examples) < 5:
                    missing_examples.append({
                        'course_code': course.get('course_code', 'Unknown'),
                        'department': dept_code,
                        'issue': 'Empty course_url value'
                    })
                continue
            
            # Check if URL looks valid
            if not course_url.startswith('https://courses.rice.edu/'):
                invalid_urls += 1
                if len(missing_examples) < 5:
                    missing_examples.append({
                        'course_code': course.get('course_code', 'Unknown'),
                        'department': dept_code,
                        'issue': f'Invalid URL: {course_url}'
                    })
                continue
            
            courses_with_urls += 1
    
    # Calculate statistics
    missing_count = courses_without_urls + empty_urls + invalid_urls
    coverage_percent = (courses_with_urls / total_courses * 100) if total_courses > 0 else 0
    
    # Report results
    print(f"\n📊 URL Coverage Analysis:")
    print(f"Total courses: {total_courses}")
    print(f"Courses with valid URLs: {courses_with_urls}")
    print(f"Missing course_url field: {courses_without_urls}")
    print(f"Empty URLs: {empty_urls}")
    print(f"Invalid URLs: {invalid_urls}")
    print(f"Total missing URLs: {missing_count}")
    print(f"Coverage: {coverage_percent:.1f}%")
    
    if missing_examples:
        print(f"\n❌ Examples of missing URLs:")
        for example in missing_examples:
            print(f"  - {example['course_code']} ({example['department']}): {example['issue']}")
    
    return {
        'total_courses': total_courses,
        'courses_with_urls': courses_with_urls,
        'missing_count': missing_count,
        'coverage_percent': coverage_percent
    }

def add_urls_to_all_courses():
    """
    Add course_url field to ALL courses in rice_organized_data.json
    Inserts URL after the description field, or at the end if no description
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_file = os.path.join(project_root, 'data', 'organized', 'rice_organized_data.json')
    backup_file = os.path.join(project_root, 'data', 'organized', 'rice_organized_data_backup.json')
    
    print("🔧 Adding URLs to ALL courses in rice_organized_data.json...")
    
    # Create backup
    print("Creating backup of original file...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Backup created: {backup_file}")
    
    departments = data.get('departments', {})
    
    total_courses = 0
    urls_added = 0
    urls_updated = 0
    urls_skipped = 0
    
    print("Processing departments...")
    
    for dept_code, dept_data in departments.items():
        courses = dept_data.get('courses', [])
        print(f"  Processing {dept_code} ({len(courses)} courses)...")
        
        for course in courses:
            total_courses += 1
            
            course_number = course.get('course_number', '')
            department = course.get('department', dept_code)
            
            # Skip if missing essential data
            if not course_number or not department:
                urls_skipped += 1
                continue
            
            # Generate the URL
            new_url = f"https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=CATALIST&p_acyr_code=2026&p_crse_numb={course_number}&p_subj={department}"
            
            # Check if URL already exists
            if 'course_url' in course:
                existing_url = course.get('course_url', '')
                if existing_url and existing_url.strip():
                    # URL exists and is not empty - update it
                    course['course_url'] = new_url
                    urls_updated += 1
                else:
                    # URL field exists but is empty - add URL
                    course['course_url'] = new_url
                    urls_added += 1
            else:
                # Create ordered dict to insert URL after description
                ordered_course = OrderedDict()
                
                # Copy fields in order, inserting course_url after description
                for key, value in course.items():
                    ordered_course[key] = value
                    if key == 'description':
                        ordered_course['course_url'] = new_url
                
                # If no description field was found, add URL at the end
                if 'course_url' not in ordered_course:
                    ordered_course['course_url'] = new_url
                
                # Replace the course with the ordered version
                course.clear()
                course.update(ordered_course)
                urls_added += 1
        
        # Progress update for large departments
        if total_courses % 1000 == 0:
            print(f"    Processed {total_courses} courses so far...")
    
    print(f"\n📊 URL Addition Summary:")
    print(f"Total courses processed: {total_courses}")
    print(f"URLs added: {urls_added}")
    print(f"URLs updated: {urls_updated}")
    print(f"Courses skipped (missing data): {urls_skipped}")
    print(f"Total URLs now present: {urls_added + urls_updated}")
    
    # Save the updated data
    print(f"\nSaving updated data to {input_file}...")
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("✅ Successfully added URLs to all courses!")
    print(f"📁 Original file backed up to: {backup_file}")
    
    # Run coverage check again
    print(f"\n🔍 Verifying URL coverage after update...")
    check_url_coverage()

def validate_course_url(course_data, timeout=10):
    """
    Validate a single course URL
    Returns (course_code, url, status, success, response_time, error_message)
    """
    course_code = course_data.get('course_code', 'Unknown')
    url = course_data.get('course_url', '')
    
    if not url:
        return (course_code, url, 'No URL', False, 0, 'Missing URL')
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        response_time = time.time() - start_time
        
        # Check if the response is successful
        if response.status_code == 200:
            # Check if the content contains course information
            content = response.text.lower()
            course_number = course_data.get('course_number', '')
            department = course_data.get('department', '')
            
            # Basic content validation
            has_course_info = (
                'course' in content or 
                'credit' in content or 
                course_number in content.lower() or
                department.lower() in content
            )
            
            if has_course_info:
                return (course_code, url, response.status_code, True, response_time, 'Success')
            else:
                return (course_code, url, response.status_code, False, response_time, 'No course content found')
        else:
            return (course_code, url, response.status_code, False, response_time, f'HTTP {response.status_code}')
            
    except requests.exceptions.Timeout:
        return (course_code, url, 'Timeout', False, timeout, 'Request timeout')
    except requests.exceptions.ConnectionError:
        return (course_code, url, 'Connection Error', False, 0, 'Connection failed')
    except requests.exceptions.RequestException as e:
        return (course_code, url, 'Request Error', False, 0, str(e))
    except Exception as e:
        return (course_code, url, 'Unknown Error', False, 0, str(e))

def validate_course_urls(sample_size=50, max_workers=5):
    """
    Validate course URLs from the organized data
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_file = os.path.join(project_root, 'data', 'organized', 'rice_organized_data.json')
    
    print("Loading organized data...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract all courses from departments
    all_courses = []
    departments = data.get('departments', {})
    for dept_data in departments.values():
        courses = dept_data.get('courses', [])
        all_courses.extend(courses)
    
    # Filter courses that have URLs
    courses_with_urls = [course for course in all_courses if course.get('course_url')]
    
    total_courses = len(courses_with_urls)
    print(f"Found {total_courses} courses with URLs")
    
    if total_courses == 0:
        print("❌ No courses have URLs to validate. Run URL addition first.")
        return
    
    # Determine which courses to test
    if sample_size and sample_size < total_courses:
        # Random sample
        test_courses = random.sample(courses_with_urls, sample_size)
        print(f"Testing random sample of {len(test_courses)} courses...")
    else:
        # Test all courses
        test_courses = courses_with_urls
        print(f"Testing all {len(test_courses)} courses...")
    
    print("Starting URL validation...")
    print("This may take a while depending on the number of URLs...")
    
    # Track results
    results = []
    successful_urls = 0
    failed_urls = 0
    
    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_course = {
            executor.submit(validate_course_url, course): course 
            for course in test_courses
        }
        
        # Process completed requests
        for i, future in enumerate(as_completed(future_to_course)):
            course_code, url, status, success, response_time, error_msg = future.result()
            results.append({
                'course_code': course_code,
                'url': url,
                'status': status,
                'success': success,
                'response_time': response_time,
                'error_message': error_msg
            })
            
            if success:
                successful_urls += 1
            else:
                failed_urls += 1
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Tested {i + 1}/{len(test_courses)} URLs...")
            
            # Rate limiting - small delay between requests
            time.sleep(0.1)
    
    # Generate report
    print(f"\n{'='*60}")
    print("URL VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Total URLs tested: {len(test_courses)}")
    print(f"Successful: {successful_urls} ({successful_urls/len(test_courses)*100:.1f}%)")
    print(f"Failed: {failed_urls} ({failed_urls/len(test_courses)*100:.1f}%)")
    
    # Average response time for successful requests
    successful_times = [r['response_time'] for r in results if r['success']]
    if successful_times:
        avg_time = sum(successful_times) / len(successful_times)
        print(f"Average response time: {avg_time:.2f} seconds")
    
    # Show failed URLs
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        print(f"\nFailed URLs ({len(failed_results)}):")
        for result in failed_results[:10]:  # Show first 10 failures
            print(f"  {result['course_code']}: {result['error_message']}")
        
        if len(failed_results) > 10:
            print(f"  ... and {len(failed_results) - 10} more failures")
    
    # Show successful examples
    successful_results = [r for r in results if r['success']]
    if successful_results:
        print(f"\nSuccessful URLs (sample):")
        for result in successful_results[:5]:  # Show first 5 successes
            print(f"  ✅ {result['course_code']}: {result['response_time']:.2f}s")
    
    return successful_urls / len(test_courses) * 100  # Return success rate

def create_simplified_course_catalog():
    """
    Create a new simplified JSON file with course_code, title, department, course_number, and course_url
    """
    # Get the script directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_file = os.path.join(project_root, 'data', 'organized', 'rice_organized_data.json')
    output_file = os.path.join(project_root, 'data', 'organized', 'rice_simplified_catalog.json')
    
    print("Loading rice_organized_data.json...")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: Could not find {input_file}")
        return
    
    # Load the existing data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    simplified_courses = []
    total_courses = 0
    processed_courses = 0
    skipped_courses = 0
    
    print("Processing courses by department...")
    
    # Access the departments section
    if 'departments' not in data:
        print("❌ Error: No 'departments' key found in JSON")
        return
    
    departments = data['departments']
    
    for dept_name, dept_data in departments.items():
        if 'courses' not in dept_data:
            print(f"⚠️  No 'courses' key in {dept_name} department, skipping...")
            continue
            
        courses = dept_data['courses']
        print(f"Processing {dept_name} department ({len(courses) if isinstance(courses, (list, dict)) else '?'} courses)...")
        
        # Handle different possible structures for courses
        if isinstance(courses, list):
            # Courses are in a list
            for course_info in courses:
                total_courses += 1
                
                if isinstance(course_info, dict):
                    # Extract required fields
                    course_code = course_info.get('course_code', '')
                    title = course_info.get('title', '')
                    department = course_info.get('department', dept_name)
                    course_number = course_info.get('course_number', '')
                    
                    # Skip courses with missing essential data
                    if not course_code or not title or not department or not course_number:
                        skipped_courses += 1
                        continue
                    
                    # Use existing course_url if available, otherwise generate it
                    course_url = course_info.get('course_url')
                    if not course_url:
                        course_url = f"https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=CATALIST&p_acyr_code=2026&p_crse_numb={course_number}&p_subj={department}"
                    
                    # Create simplified course entry
                    simplified_course = {
                        "course_code": course_code,
                        "title": title,
                        "department": department,
                        "course_number": course_number,
                        "course_url": course_url
                    }
                    
                    simplified_courses.append(simplified_course)
                    processed_courses += 1
                    
        elif isinstance(courses, dict):
            # Courses are in a dictionary
            for course_key, course_info in courses.items():
                total_courses += 1
                
                if isinstance(course_info, dict):
                    # Extract required fields
                    course_code = course_info.get('course_code', '')
                    title = course_info.get('title', '')
                    department = course_info.get('department', dept_name)
                    course_number = course_info.get('course_number', '')
                    
                    # Skip courses with missing essential data
                    if not course_code or not title or not department or not course_number:
                        skipped_courses += 1
                        continue
                    
                    # Use existing course_url if available, otherwise generate it
                    course_url = course_info.get('course_url')
                    if not course_url:
                        course_url = f"https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=CATALIST&p_acyr_code=2026&p_crse_numb={course_number}&p_subj={department}"
                    
                    # Create simplified course entry
                    simplified_course = {
                        "course_code": course_code,
                        "title": title,
                        "department": department,
                        "course_number": course_number,
                        "course_url": course_url
                    }
                    
                    simplified_courses.append(simplified_course)
                    processed_courses += 1
        
        # Progress indicator for large departments
        if processed_courses % 500 == 0 and processed_courses > 0:
            print(f"  Processed {processed_courses} courses so far...")
    
    print(f"\nProcessing Summary:")
    print(f"  Total courses found: {total_courses}")
    print(f"  Successfully processed: {processed_courses}")
    print(f"  Skipped (missing data): {skipped_courses}")
    
    if processed_courses == 0:
        print("❌ No courses were processed. Check the JSON structure.")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save the simplified data to new file
    print(f"\nSaving simplified catalog to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(simplified_courses, f, indent=2, ensure_ascii=False)
    
    print("✅ Simplified course catalog successfully created!")
    
    # Show file size comparison
    original_size = os.path.getsize(input_file) / (1024 * 1024)  # MB
    new_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    
    print(f"\nFile Size Comparison:")
    print(f"  Original file: {original_size:.2f} MB")
    print(f"  Simplified file: {new_size:.2f} MB")
    print(f"  Size reduction: {((original_size - new_size) / original_size * 100):.1f}%")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            check_url_coverage()
        elif command == "add":
            add_urls_to_all_courses()
        elif command == "validate":
            sample_size = 50  # Default sample size
            if len(sys.argv) > 2:
                try:
                    sample_size = int(sys.argv[2])
                except ValueError:
                    if sys.argv[2].lower() == "all":
                        sample_size = None
                    else:
                        print("Invalid sample size. Use a number or 'all'.")
                        sys.exit(1)
            validate_course_urls(sample_size=sample_size)
        elif command == "examine":
            examine_json_structure()
        else:
            print("Usage:")
            print("  python course_url_scraper.py check              # Check URL coverage")
            print("  python course_url_scraper.py add                # Add URLs to all courses") 
            print("  python course_url_scraper.py validate [size]    # Validate URLs")
            print("  python course_url_scraper.py examine            # Examine structure")
    else:
        # Default: check coverage first
        print("=== Checking Current URL Coverage ===")
        result = check_url_coverage()
        
        if result['coverage_percent'] < 100:
            print(f"\n⚠️  Only {result['coverage_percent']:.1f}% of courses have URLs!")
            print("To add URLs to all courses, run: python scrapers/course_url_scraper.py add")
        else:
            print(f"\n✅ All courses have URLs! ({result['coverage_percent']:.1f}% coverage)")
            print("To validate URLs, run: python scrapers/course_url_scraper.py validate")
