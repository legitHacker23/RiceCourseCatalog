import React, { useState, useEffect } from 'react';
import config from './config';
import './CourseCatalog.css';

// Function to truncate text
const truncateText = (text, maxLength = 120) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
};

// Function to clean Fall 2025 course titles
const cleanCourseTitle = (title) => {
  if (!title) return '';
  
  // Remove everything from "Department:" onwards
  const cleanTitle = title.split('Department:')[0].trim();
  return cleanTitle;
};

const CourseCatalog = ({ onNavigateToTab }) => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({});
  const [departments, setDepartments] = useState([]);
  const [departmentStats, setDepartmentStats] = useState({});
  const [selectedDepartments, setSelectedDepartments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  const [courseLevel, setCourseLevel] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCourses, setTotalCourses] = useState(0);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [courseSection, setCourseSection] = useState('fall2025'); // 'fall2025' or 'all'
  
  // Modal state
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [shareMessage, setShareMessage] = useState('');
  const [sharedCourse, setSharedCourse] = useState(null); // Add this line
  // Add this new state for modal share status
  const [modalShareCopied, setModalShareCopied] = useState(false);

  const [searchInput, setSearchInput] = useState('');
  const [previousPage, setPreviousPage] = useState(1);

  useEffect(() => {
    fetchStats();
    fetchDepartments();
  }, [courseSection]);

  useEffect(() => {
    fetchCourses();
  }, [searchQuery, selectedDepartments, courseLevel, currentPage, courseSection]);

  useEffect(() => {
    setCurrentPage(1);
  }, [courseSection]);

  useEffect(() => {
    setSelectedDepartments([]);
    setCourseLevel('');
  }, [courseSection]);

  useEffect(() => {
    if (showModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    // Clean up in case the component unmounts while modal is open
    return () => {
      document.body.style.overflow = '';
    };
  }, [showModal]);

  const fetchStats = async () => {
    try {
      const endpoint = courseSection === 'fall2025' ? '/api/fall2025/stats' : '/api/catalog/stats';
      const response = await fetch(`${config.BACKEND_URL}${endpoint}`);
      const data = await response.json();
      setStats(data);
      // Extract department statistics
      if (data.department_stats) {
        setDepartmentStats(data.department_stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await fetch(`${config.BACKEND_URL}/api/departments`);
      const data = await response.json();
      setDepartments(data.departments || []);
    } catch (error) {
      console.error('Error fetching departments:', error);
    }
  };

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        search: searchQuery,
        page: currentPage,
        per_page: 20,
        ...(courseLevel && { course_level: courseLevel }),
        ...(courseSection === 'all' && { course_type: 'all' })
      });

      // Add each department as a separate parameter for OR logic
      selectedDepartments.forEach(dept => {
        params.append('departments', dept);
      });

      const endpoint = courseSection === 'fall2025' ? '/api/fall2025/search' : '/api/catalog/search';
      const response = await fetch(`${config.BACKEND_URL}${endpoint}?${params}`);
      const data = await response.json();

      if (data.error) {
        setError(data.error);
      } else {
        setCourses(data.courses || []);
        setTotalPages(data.total_pages || 1);
        setTotalCourses(data.total || 0);
        setError(null);
      }
    } catch (error) {
      setError('Failed to fetch courses. Please try again.');
      console.error('Error fetching courses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDepartmentToggle = (dept) => {
    setSelectedDepartments(prev => 
      prev.includes(dept) 
        ? prev.filter(d => d !== dept)
        : [...prev, dept]
    );
    setCurrentPage(1);
  };

  const handleClearAll = () => {
    setSearchQuery('');
    setSelectedDepartments([]);
    setCourseLevel('');
    setCurrentPage(1);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const formatCourseCode = (courseCode) => {
    if (!courseCode) return '';
    return courseCode.replace(/([A-Z]+)\s*(\d+)/, '$1 $2');
  };

  const getSectionTitle = () => {
    return courseSection === 'fall2025' ? 'Fall 2025 Courses' : 'All Courses';
  };

  const getSectionDescription = () => {
    return courseSection === 'fall2025' 
      ? 'Browse and search through all available courses for Fall 2025 semester'
      : 'Browse and search through all Rice University courses';
  };

  // Generate course URL based on Rice catalog pattern
  const generateCourseUrl = (courseCode) => {
    if (!courseCode) return '';
    const formattedCode = courseCode.replace(/\s+/g, '%20');
    return `https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=COURSE&p_term=202420&p_crn=${formattedCode}`;
  };

  // Handle view details - Added console.log for debugging
  const handleViewDetails = (course) => {
    setSelectedCourse(course);
    setShowModal(true);
  };

  // Handle share functionality
  const handleShare = async (course) => {
    // Use the same URL as the "View on Rice Catalog" button
    const courseUrl = course.course_url;
    const department = course.department || course.subject_code || '';
    const instructors = Array.isArray(course.instructors) ? course.instructors.join(', ') : (course.instructors || '');
    let shareText = `${course.course_code} - ${cleanCourseTitle(course.title)}`;
    if (department) {
      shareText += `\nDepartment: ${department}`;
    }
    if (instructors) {
      shareText += `\nInstructor: ${instructors}`;
    }
    shareText += `\n\nView on Rice Catalog: ${courseUrl}`;
    
    try {
      // Always copy to clipboard instead of using native share
      await navigator.clipboard.writeText(shareText);
      setShareMessage('✅ Copied!');
      setSharedCourse(course.course_code);
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      setShareMessage('❌ Failed');
      setSharedCourse(course.course_code);
    }
    
    // Clear message after 3 seconds
    setTimeout(() => {
      setShareMessage('');
      setSharedCourse(null);
    }, 3000);
  };

  const handleCourseLink = async (course) => {
    // Use the same URL as the "View on Rice Catalog" button
    const courseUrl = course.course_url
    
    try {
      // Always copy to clipboard instead of using native share
      await navigator.clipboard.writeText(courseUrl);
      setShareMessage('✅ Copied!');
      setSharedCourse(course.course_code);
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      setShareMessage('❌ Failed');
      setSharedCourse(course.course_code);
    }
    
    // Clear message after 3 seconds
    setTimeout(() => {
      setShareMessage('');
      setSharedCourse(null);
    }, 3000);
  };

  const handleEstherTutorial = (course) => {
    // Navigate to the evaluations tab
    if (onNavigateToTab) {
      onNavigateToTab('evaluations');
      // Scroll to top of the page after navigation
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }, 100);
    }
  };

  // Close modal
  const closeModal = () => {
    setShowModal(false);
    setSelectedCourse(null);
  };

  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscKey = (event) => {
      if (event.key === 'Escape' && showModal) {
        closeModal();
      }
    };

    document.addEventListener('keydown', handleEscKey);
    return () => document.removeEventListener('keydown', handleEscKey);
  }, [showModal]);

  const handleSearchInputChange = (e) => {
    const value = e.target.value;
    if (searchQuery === "" && value !== "") {
      setPreviousPage(currentPage);
      setCurrentPage(1);
    }
    if (value === "") {
      setCurrentPage(previousPage);
    }
    setSearchQuery(value);
  };

  return (
    <div className="course-catalog">
      {/* Animated Background Elements */}
      <div className="animated-blob blob-1"></div>
      <div className="animated-blob blob-2"></div>
      <div className="animated-dots">
        {[...Array(20)].map((_, i) => (
          <div key={i} className="dot" style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 20}s`,
            animationDuration: `${15 + Math.random() * 10}s`
          }}></div>
        ))}
      </div>

      <div className="catalog-container">
        {/* Hero Section */}
        <div className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">
              <span className="gradient-text">Rice Course Catalog</span>
            </h1>
            <p className="hero-subtitle">{getSectionDescription()}</p>
            
            {/* Section Selector */}
            <div className="section-selector">
              <button 
                className={`section-btn ${courseSection === 'fall2025' ? 'active' : ''}`}
                onClick={() => setCourseSection('fall2025')}
              >
                🍂 Fall 2025 Courses
              </button>
              <button 
                className={`section-btn ${courseSection === 'all' ? 'active' : ''}`}
                onClick={() => setCourseSection('all')}
              >
                📚 All Courses
              </button>
            </div>

            {/* Stats */}
            <div className="hero-stats">
              <div className="stat-item">
                <span className="stat-number">{stats.total_courses || 0}</span>
                <span className="stat-label">Total Courses</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">{stats.total_departments || 0}</span>
                <span className="stat-label">Departments</span>
              </div>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="search-filters">
          <div className="search-bar">
            <input
              type="text"
              placeholder="Search courses, departments, or keywords..."
              value={searchQuery}
              onChange={handleSearchInputChange}
              className="search-input"
            />
            <button className="clear-btn" onClick={handleClearAll}>
              Clear All
            </button>
          </div>

          <div className="filters-container">
            <div className="filter-group">
              <label>Course Level:</label>
              <select
                value={courseLevel}
                onChange={(e) => setCourseLevel(e.target.value)}
                className="level-select"
              >
                <option value="">All Levels</option>
                <option value="100">100 Level</option>
                <option value="200">200 Level</option>
                <option value="300">300 Level</option>
                <option value="400">400 Level</option>
                <option value="500">500+ Level</option>
              </select>
            </div>
            <div className="view-toggle">
              <button
                className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
              >
                Grid
              </button>
              <button
                className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => setViewMode('list')}
              >
                List
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="catalog-main">
          {/* Filters Sidebar */}
          <div className="filters-sidebar">
            <div className="filter-section">
              <label>Departments</label>
              <div className="department-filters">
                {departments.map(dept => (
                  <label key={dept} className={`checkbox-label${selectedDepartments.includes(dept) ? ' selected' : ''}`}>
                    <input
                      type="checkbox"
                      checked={selectedDepartments.includes(dept)}
                      onChange={() => handleDepartmentToggle(dept)}
                    />
                    <span className="checkbox-custom"></span>
                    <span className="department-name">{dept}</span>
                    <span className="course-count">
                      ({departmentStats[dept] !== undefined ? departmentStats[dept] : 0})
                    </span>
                  </label>
                ))}
              </div>
              {selectedDepartments.length > 0 && (
                <button
                  className="clear-departments-btn"
                  onClick={handleClearAll}
                  style={{ position: 'absolute', left: 0, bottom: 0, margin: '1rem' }}
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Courses Grid */}
          <div className="courses-container">
            {loading ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Loading courses...</p>
              </div>
            ) : error ? (
              <div className="error-container">
                <p>{error}</p>
                <button onClick={fetchCourses} className="try-again-btn">
                  Try Again
                </button>
              </div>
            ) : (
              <>
                <div className={`courses-grid ${viewMode === 'list' ? 'list-view' : ''}`}>
                  {courses.map((course, index) => (
                    <div key={`${course.course_code}-${index}`} className="course-card">
                      <div className="course-header">
                        <h3 className="course-code">{formatCourseCode(course.course_code)}</h3>
                      </div>
                      <h4 className="course-title">{cleanCourseTitle(course.title)}</h4>
                      {course.description && (
                        <p className="course-description">{truncateText(course.description, 120)}</p>
                      )}
                      {course.instructors && (
                        <div className="course-instructor">
                          <strong>Instructor:</strong> {Array.isArray(course.instructors) ? course.instructors.join(', ') : course.instructors}
                        </div>
                      )}
                      {course.meeting_time && (
                        <div className="course-time">
                          <strong>Time:</strong> {course.meeting_time}
                        </div>
                      )}
                      {course.prerequisites && (
                        <div className="course-prerequisites">
                          <strong>Prerequisites:</strong> {truncateText(course.prerequisites, 80)}
                        </div>
                      )}
                      <div className="course-actions">
                        <button 
                          className="view-details-btn"
                          onClick={() => {
                            handleViewDetails(course);
                          }}
                          style={{ pointerEvents: 'auto', zIndex: 999 }}
                        >
                          View Details
                        </button>
                        <button 
                          className="share-btn"
                          onClick={() => {
                            handleCourseLink(course);
                          }}
                          style={{ pointerEvents: 'auto', zIndex: 999 }}
                        >
                          {sharedCourse === course.course_code && shareMessage ? shareMessage : 'Course Link'}
                        </button>
                        <button 
                          className="esther-btn"
                          onClick={() => {
                            handleEstherTutorial(course);
                          }}
                          style={{ pointerEvents: 'auto', zIndex: 999 }}
                        >
                          Course Evaluations
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="pagination">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="pagination-btn"
                    >
                      Previous
                    </button>
                    
                    {[...Array(totalPages)].map((_, i) => {
                      const page = i + 1;
                      if (
                        page === 1 ||
                        page === totalPages ||
                        (page >= currentPage - 2 && page <= currentPage + 2)
                      ) {
                        return (
                          <button
                            key={page}
                            onClick={() => handlePageChange(page)}
                            className={`pagination-btn ${currentPage === page ? 'active' : ''}`}
                          >
                            {page}
                          </button>
                        );
                      } else if (
                        page === currentPage - 3 ||
                        page === currentPage + 3
                      ) {
                        return <span key={page} className="pagination-ellipsis">...</span>;
                      }
                      return null;
                    })}
                    
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="pagination-btn"
                    >
                      Next
                    </button>
                  </div>
                )}

                {/* Results Summary */}
                <div className="results-summary">
                  Showing {courses.length} of {totalCourses} courses
                  {selectedDepartments.length > 0 && (
                    <span> in {selectedDepartments.join(', ')}</span>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Course Details Modal */}
      {showModal && selectedCourse && (
        <div className="course-modal-overlay active" onClick={closeModal}>
          <div className="course-modal" onClick={(e) => e.stopPropagation()}>
            
            {/* Header */}
            <div className="modal-header">
              <div>
                <div className="modal-course-code">
                  <span className="code">{selectedCourse.course_code}</span>
                  <span className="level-badge">
                    {selectedCourse.course_number ? `Level ${Math.floor(selectedCourse.course_number / 100)}00` : 'Course'}
                  </span>
                </div>
                <h3 className="modal-course-title">{cleanCourseTitle(selectedCourse.title)}</h3>
              </div>
              <button onClick={closeModal} className="modal-close-btn">×</button>
            </div>

            {/* Course Details */}
            <div className="modal-content">
              
              {/* Course Meta Information */}
              <div className="modal-meta">
                {selectedCourse.course_type && (
                  <div className="meta-item">
                    <div className="meta-icon">🏷️</div>
                    <div className="meta-label">Type</div>
                    <div className="meta-value">{selectedCourse.course_type}</div>
                  </div>
                )}

                {(selectedCourse.subject_code || selectedCourse.department) && (
                  <div className="meta-item">
                    <div className="meta-icon">🏛️</div>
                    <div className="meta-label">Department</div>
                    <div className="meta-value">{selectedCourse.subject_code || selectedCourse.department}</div>
                  </div>
                )}

                {selectedCourse.course_number && (
                  <div className="meta-item">
                    <div className="meta-icon">🔢</div>
                    <div className="meta-label">COURSE Number</div>
                    <div className="meta-value">{selectedCourse.course_number}</div>
                  </div>
                )}
              </div>

              {/* Fall 2025 Specific Info */}
              {(selectedCourse.instructors || selectedCourse.meeting_time || selectedCourse.crn) && (
                <div className="modal-schedule-info">
                  <h3>🍂 Fall 2025 Schedule Info</h3>
                  
                  {selectedCourse.instructors && (
                    <div className="schedule-item">
                      <strong>Instructor(s):</strong>
                      <div>{Array.isArray(selectedCourse.instructors) ? selectedCourse.instructors.join(', ') : selectedCourse.instructors}</div>
                    </div>
                  )}

                  {selectedCourse.meeting_time && (
                    <div className="schedule-item">
                      <strong>Meeting Time:</strong>
                      <div>{selectedCourse.meeting_time}</div>
                    </div>
                  )}

                  {selectedCourse.crn && (
                    <div className="schedule-item">
                      <strong>CRN:</strong>
                      <div>{selectedCourse.crn}</div>
                    </div>
                  )}

                  {selectedCourse.section && (
                    <div className="schedule-item">
                      <strong>Section:</strong>
                      <div>{selectedCourse.section}</div>
                    </div>
                  )}

                  {selectedCourse.part_of_term && (
                    <div className="schedule-item">
                      <strong>Term:</strong>
                      <div>{selectedCourse.part_of_term}</div>
                    </div>
                  )}

                  <div className="schedule-item">
                    <strong>Distribution Group:</strong>
                    <div>{selectedCourse.distribution_group || 'None'}</div>
                  </div>
                </div>
              )}

              {/* Description */}
              {selectedCourse.description && (
                <div className="modal-section">
                  <h3>📋 Description</h3>
                  <p>{selectedCourse.description}</p>
                </div>
              )}

              {/* Prerequisites */}
              {selectedCourse.prerequisites && (
                <div className="modal-section">
                  <h3>⚠️ Prerequisites</h3>
                  <p>{selectedCourse.prerequisites}</p>
                </div>
              )}

              {/* Actions */}
              <div className="modal-actions">
                {selectedCourse.course_url && (
                  <a 
                    href={selectedCourse.course_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="share-btn"
                  >
                    🔗 View on Rice Catalog
                  </a>
                )}
                <button 
                  onClick={async () => {
                    await handleShare(selectedCourse);
                    setModalShareCopied(true);
                    setTimeout(() => setModalShareCopied(false), 1000);
                  }}
                  className="share-btn"
                >
                  {modalShareCopied ? 'Copied!' : 'Share'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CourseCatalog;