-- ============================================================
-- MySQL Backup Schema for Learning Platform
-- ============================================================
-- HYBRID DATABASE ARCHITECTURE:
-- - MongoDB: Primary database (SOURCE OF TRUTH)
-- - MySQL: Backup database (READ-ONLY)
--
-- IMPORTANT: This schema is for BACKUP/AUDITING purposes only.
-- MongoDB is always the authoritative source.
-- MySQL data should NEVER be written back to MongoDB.
-- ============================================================

CREATE DATABASE IF NOT EXISTS learning_platform_backup
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE learning_platform_backup;

-- ============================================================
-- Session Reports Backup Table
-- ============================================================
-- Stores backup of session reports from MongoDB
-- The 'full_document' column contains the complete MongoDB document as JSON
-- Flattened columns enable SQL queries without parsing JSON
CREATE TABLE IF NOT EXISTS session_reports_backup (
    -- Auto-increment primary key for MySQL
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- MongoDB Reference - Links back to source document
    -- This is the MongoDB _id and must be UNIQUE to prevent duplicates
    mongo_id VARCHAR(24) UNIQUE NOT NULL,
    
    -- ==========================================
    -- Flattened Fields for SQL Queries
    -- ==========================================
    -- These fields are extracted from the MongoDB document
    -- to enable efficient SQL queries without JSON parsing
    
    session_id VARCHAR(24) NOT NULL,
    session_title VARCHAR(255),
    course_name VARCHAR(255),
    course_code VARCHAR(50),
    instructor_id VARCHAR(24),
    instructor_name VARCHAR(255),
    session_date DATE,
    session_status VARCHAR(50),
    
    -- Aggregated Metrics (useful for reporting dashboards)
    total_participants INT DEFAULT 0,
    total_questions_asked INT DEFAULT 0,
    average_quiz_score DECIMAL(5,2),
    
    -- Engagement Summary (flattened from nested object)
    highly_engaged_count INT DEFAULT 0,
    moderately_engaged_count INT DEFAULT 0,
    at_risk_count INT DEFAULT 0,
    
    -- ==========================================
    -- Complete MongoDB Document as JSON
    -- ==========================================
    -- This column stores the ENTIRE MongoDB document
    -- Use JSON functions for complex queries:
    -- Example: JSON_EXTRACT(full_document, '$.students[0].studentName')
    full_document JSON,
    
    -- ==========================================
    -- Metadata
    -- ==========================================
    report_type VARCHAR(50) DEFAULT 'master',
    generated_at DATETIME,
    backed_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- ==========================================
    -- Indexes for Common Queries
    -- ==========================================
    INDEX idx_session_id (session_id),
    INDEX idx_instructor_id (instructor_id),
    INDEX idx_session_date (session_date),
    INDEX idx_course_code (course_code),
    INDEX idx_backed_up_at (backed_up_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='READ-ONLY backup of session reports from MongoDB. Source of truth is MongoDB.';

-- ============================================================
-- Courses Backup Table
-- ============================================================
-- Stores backup of courses from MongoDB
CREATE TABLE IF NOT EXISTS courses_backup (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- MongoDB Reference
    mongo_id VARCHAR(24) UNIQUE NOT NULL,
    
    -- Course Information
    course_code VARCHAR(50),
    course_name VARCHAR(255),
    description TEXT,
    
    -- Instructor Details
    instructor_id VARCHAR(24),
    instructor_name VARCHAR(255),
    
    -- Academic Details
    semester VARCHAR(50),
    year INT,
    credits INT,
    
    -- Status and Enrollment
    status VARCHAR(50) DEFAULT 'active',
    enrolled_count INT DEFAULT 0,
    
    -- Metadata
    created_at DATETIME,
    backed_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_course_code (course_code),
    INDEX idx_instructor_id (instructor_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='READ-ONLY backup of courses from MongoDB. Source of truth is MongoDB.';

-- ============================================================
-- Student Participation Backup Table
-- ============================================================
-- Stores individual student participation records
-- Each row represents one student's participation in one session
CREATE TABLE IF NOT EXISTS student_participation_backup (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- References to parent report and session
    report_mongo_id VARCHAR(24) NOT NULL,
    session_id VARCHAR(24) NOT NULL,
    student_id VARCHAR(50) NOT NULL,
    
    -- Student Information
    student_name VARCHAR(255),
    student_email VARCHAR(255),
    
    -- Attendance Data
    joined_at DATETIME,
    left_at DATETIME,
    attendance_duration_minutes INT,
    
    -- Quiz Performance
    total_questions INT DEFAULT 0,
    correct_answers INT DEFAULT 0,
    incorrect_answers INT DEFAULT 0,
    quiz_score DECIMAL(5,2),
    average_response_time DECIMAL(8,2),
    
    -- Connection Quality
    connection_quality VARCHAR(50),
    
    -- Metadata
    backed_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate entries
    UNIQUE KEY uk_report_student (report_mongo_id, student_id),
    
    -- Indexes
    INDEX idx_student_id (student_id),
    INDEX idx_session_id (session_id),
    INDEX idx_student_email (student_email),
    INDEX idx_joined_at (joined_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='READ-ONLY backup of student participation data. Source of truth is MongoDB.';

-- ============================================================
-- Example Queries for Auditing/Reporting
-- ============================================================

-- Get all sessions for an instructor
-- SELECT session_id, session_title, session_date, total_participants
-- FROM session_reports_backup
-- WHERE instructor_id = '6923dd13eb13d1ef693bdbc7'
-- ORDER BY session_date DESC;

-- Get engagement statistics per course
-- SELECT 
--     course_name,
--     COUNT(*) as total_sessions,
--     SUM(total_participants) as total_students,
--     AVG(average_quiz_score) as avg_score
-- FROM session_reports_backup
-- GROUP BY course_name;

-- Find at-risk students (participated but low scores)
-- SELECT 
--     sp.student_name,
--     sp.student_email,
--     COUNT(sp.id) as sessions_attended,
--     AVG(sp.quiz_score) as avg_score
-- FROM student_participation_backup sp
-- WHERE sp.quiz_score < 50
-- GROUP BY sp.student_id, sp.student_name, sp.student_email
-- HAVING COUNT(sp.id) >= 3;

