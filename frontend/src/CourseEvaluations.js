import React from 'react';
import './CourseEvaluations.css';

const CourseEvaluations = () => {
  return (
    <div className="evaluations-container">
      <div className="evaluations-header">
        <h2>📊 Course Evaluations</h2>
        <p>Access course evaluations and student feedback through ESTHER</p>
      </div>

      <div className="evaluations-content">
        <div className="esther-link-section">
          <div className="esther-card">
            <h3>🎯 Access Course Evaluations</h3>
            <p>Click the button below to go directly to ESTHER and view course evaluations:</p>
            <a 
              href="https://esther.rice.edu" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="esther-button"
            >
              🔗 Go to ESTHER
            </a>
            <div className="esther-instructions">
              <h4>How to find course evaluations in ESTHER:</h4>
              <ol>
                <li>Log in to ESTHER with your Rice credentials</li>
                <li>Navigate to "Students - General"</li>
                <li>Click on "Course Evaluations and Instructor Evaluations - View Results"</li>
                <li>Agree to the terms and select the semester and course you want to view</li>
                <li>Browse through student feedback and ratings</li>
              </ol>
            </div>
          </div>
        </div>

        <div className="video-section">
          <div className="video-container">
            <h3>📹 Video Tutorial</h3>
            <p>Watch this tutorial to learn how to access course evaluations:</p>
            <video 
              src="/videos/0725.mp4"
              controls
              width="100%"
              height="600"
              className="course-evaluations-video"
            >
              Your browser does not support the video tag.
            </video>
          </div>
        </div>

        <div className="evaluations-info">
          <div className="info-card">
            <h3>💡 Why Check Course Evaluations?</h3>
            <ul>
              <li><strong>Student Feedback:</strong> See what other students say about courses and professors</li>
              <li><strong>Course Difficulty:</strong> Understand the workload and challenge level</li>
              <li><strong>Teaching Style:</strong> Learn about professor teaching methods and expectations</li>
              <li><strong>Course Content:</strong> Get insights into what topics are covered</li>
              <li><strong>Grading:</strong> Understand how grades are distributed and what to expect</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseEvaluations; 