import json
import os
from collections import OrderedDict

def add_course_urls_to_organized_data():
    """
    Add/overwrite course_url fields in rice_organized_data.json using URLs from rice_simplified_catalog.json
    Inserts the course_url field after the description field in each course.
    """
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    organized_file = os.path.join(project_root, 'data', 'organized', 'rice_organized_data.json')
    simplified_file = os.path.join(project_root, 'data', 'raw', 'rice_simplified_catalog.json')  # Updated path
    backup_file = os.path.join(project_root, 'data', 'organized', 'rice_organized_data_backup.json')
    
    # Check if files exist
    if not os.path.exists(organized_file):
        print(f"❌ Error: {organized_file} not found")
        return
    
    if not os.path.exists(simplified_file):
        print(f"❌ Error: {simplified_file} not found")
        print("Please check that rice_simplified_catalog.json is in the data/raw/ folder")
        return
    
    print("📚 Loading course data files...")
    print(f"📁 Looking for simplified catalog at: {simplified_file}")
    
    # Load simplified catalog (course_code -> course_url mapping)
    with open(simplified_file, 'r', encoding='utf-8') as f:
        simplified_courses = json.load(f)
    
    # Create mapping from course_code to course_url
    url_mapping = {}
    for course in simplified_courses:
        course_code = course.get('course_code')
        course_url = course.get('course_url')
        if course_code and course_url:
            url_mapping[course_code] = course_url
    
    print(f"✅ Loaded {len(url_mapping)} course URLs from simplified catalog")
    
    # Load organized data
    with open(organized_file, 'r', encoding='utf-8') as f:
        organized_data = json.load(f)
    
    print("✅ Loaded organized course data")
    
    # Create backup before modifying
    print("💾 Creating backup of original file...")
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(organized_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Backup saved to: {backup_file}")
    
    # Process departments and add/overwrite course URLs
    departments = organized_data.get('departments', {})
    total_courses = 0
    updated_courses = 0
    overwritten_courses = 0
    missing_urls = 0
    
    print("\n🔄 Processing departments and adding/overwriting course URLs...")
    
    for dept_name, dept_data in departments.items():
        if 'courses' not in dept_data:
            continue
            
        courses = dept_data['courses']
        dept_updated = 0
        dept_overwritten = 0
        
        for i, course in enumerate(courses):
            total_courses += 1
            course_code = course.get('course_code')
            
            if not course_code:
                continue
            
            # Check if course_url already exists (for counting overwritten)
            had_existing_url = 'course_url' in course
            
            # Get URL from mapping
            if course_code in url_mapping:
                course_url = url_mapping[course_code]
                
                # Create new ordered course object with course_url after description
                new_course = OrderedDict()
                
                for key, value in course.items():
                    # Skip existing course_url to avoid duplicates
                    if key == 'course_url':
                        continue
                        
                    new_course[key] = value
                    # Insert course_url after description
                    if key == 'description':
                        new_course['course_url'] = course_url
                
                # If no description field exists, add course_url at the end
                if 'description' not in course:
                    new_course['course_url'] = course_url
                
                # Replace the course in the list
                courses[i] = dict(new_course)
                updated_courses += 1
                dept_updated += 1
                
                if had_existing_url:
                    overwritten_courses += 1
                    dept_overwritten += 1
            else:
                missing_urls += 1
        
        if dept_updated > 0:
            overwrite_msg = f" ({dept_overwritten} overwritten)" if dept_overwritten > 0 else ""
            print(f"  📂 {dept_name}: Updated {dept_updated} courses{overwrite_msg}")
    
    print(f"\n📊 Processing Summary:")
    print(f"  Total courses processed: {total_courses}")
    print(f"  Courses updated with URLs: {updated_courses}")
    print(f"  Existing URLs overwritten: {overwritten_courses}")
    print(f"  Courses missing URLs: {missing_urls}")
    print(f"  Success rate: {(updated_courses/total_courses*100):.1f}%")
    
    # Save updated organized data
    print(f"\n💾 Saving updated data to {organized_file}...")
    with open(organized_file, 'w', encoding='utf-8') as f:
        json.dump(organized_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Successfully added/overwritten course URLs in organized data!")
    
    # Verification: Sample a few courses to show the result
    print("\n🔍 Sample verification (first 3 courses with URLs):")
    sample_count = 0
    for dept_name, dept_data in departments.items():
        if sample_count >= 3:
            break
        courses = dept_data.get('courses', [])
        for course in courses:
            if 'course_url' in course and sample_count < 3:
                print(f"  📚 {course.get('course_code', 'N/A')}: {course.get('title', 'N/A')}")
                print(f"      URL: {course.get('course_url', 'N/A')}")
                sample_count += 1
                if sample_count >= 3:
                    break
    
    # Show courses that didn't get URLs (for debugging)
    if missing_urls > 0:
        print(f"\n⚠️ Courses without URLs (first 5):")
        missing_count = 0
        for dept_name, dept_data in departments.items():
            if missing_count >= 5:
                break
            courses = dept_data.get('courses', [])
            for course in courses:
                if 'course_url' not in course and course.get('course_code') and missing_count < 5:
                    print(f"  ❌ {course.get('course_code', 'N/A')}: {course.get('title', 'N/A')}")
                    missing_count += 1
                    if missing_count >= 5:
                        break

def verify_course_url_addition():
    """
    Verify that course URLs were added correctly
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    organized_file = os.path.join(project_root, 'data', 'organized', 'rice_organized_data.json')
    
    if not os.path.exists(organized_file):
        print("❌ Organized data file not found")
        return
    
    print("🔍 Verifying course URL addition...")
    
    with open(organized_file, 'r', encoding='utf-8') as f:
        organized_data = json.load(f)
    
    departments = organized_data.get('departments', {})
    total_courses = 0
    courses_with_urls = 0
    
    for dept_name, dept_data in departments.items():
        courses = dept_data.get('courses', [])
        for course in courses:
            total_courses += 1
            if 'course_url' in course:
                courses_with_urls += 1
    
    print(f"📊 Verification Results:")
    print(f"  Total courses: {total_courses}")
    print(f"  Courses with URLs: {courses_with_urls}")
    print(f"  Coverage: {(courses_with_urls/total_courses*100):.1f}%")
    
    # Check field order (ensure course_url comes after description)
    print(f"\n🔍 Checking field order for a sample course:")
    for dept_name, dept_data in departments.items():
        courses = dept_data.get('courses', [])
        for course in courses:
            if 'course_url' in course:
                fields = list(course.keys())
                print(f"  📚 Sample course ({course.get('course_code', 'N/A')}) field order:")
                for i, field in enumerate(fields):
                    marker = " 👈" if field == 'course_url' else ""
                    print(f"    {i+1}. {field}{marker}")
                return  # Just show one example

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_course_url_addition()
    else:
        add_course_urls_to_organized_data()
        print("\n" + "="*60)
        print("To verify the changes, run:")
        print("python scrapers/add_course_urls.py verify")
