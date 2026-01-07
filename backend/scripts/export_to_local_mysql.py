"""
MongoDB → Local MySQL Export Script
====================================
This script:
1. Exports session reports from MongoDB
2. Converts JSON → CSV
3. Imports CSV into local MySQL

Usage:
    python export_to_local_mysql.py

Requirements:
    pip install pymongo pandas mysql-connector-python python-dotenv
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path

# Try to import required packages
try:
    from pymongo import MongoClient
    import pandas as pd
    import mysql.connector
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing package: {e}")
    print("Run: pip install pymongo pandas mysql-connector-python python-dotenv")
    exit(1)

# Load environment variables
load_dotenv()

# ============================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================

# MongoDB Connection (your Railway MongoDB)
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://your-mongodb-uri")
MONGO_DB = os.getenv("MONGO_DB_NAME", "learning_platform")

# Local MySQL Connection (your laptop)
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_local_mysql_password",  # ← UPDATE THIS
    "database": "learning_platform_backup"
}

# Output directory for CSV files
OUTPUT_DIR = Path("./exports")

# ============================================================
# STEP 1: EXPORT FROM MONGODB
# ============================================================

def connect_mongodb():
    """Connect to MongoDB"""
    print("🔗 Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    print(f"✅ Connected to MongoDB: {MONGO_DB}")
    return db

def export_session_reports(db):
    """Export session reports from MongoDB"""
    print("\n📊 Exporting session reports...")
    
    reports = list(db.session_reports.find({"reportType": "master"}))
    print(f"   Found {len(reports)} reports")
    
    return reports

def export_participants(db):
    """Export session participants from MongoDB"""
    print("\n👥 Exporting session participants...")
    
    participants = list(db.session_participants.find({}))
    print(f"   Found {len(participants)} participants")
    
    return participants


def export_users(db):
    """Export users from MongoDB"""
    print("\n👤 Exporting users...")
    
    users = list(db.users.find({}))
    print(f"   Found {len(users)} users")
    
    return users


def export_quiz_answers(db):
    """Export quiz answers from MongoDB"""
    print("\n📝 Exporting quiz answers...")
    
    answers = list(db.quiz_answers.find({}))
    print(f"   Found {len(answers)} quiz answers")
    
    return answers


def export_questions(db):
    """Export questions from MongoDB"""
    print("\n❓ Exporting questions...")
    
    questions = list(db.questions.find({}))
    print(f"   Found {len(questions)} questions")
    
    return questions

# ============================================================
# STEP 2: CONVERT JSON → CSV
# ============================================================

def convert_reports_to_csv(reports):
    """Convert session reports to CSV"""
    print("\n📄 Converting reports to CSV...")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Flatten report data for CSV
    csv_data = []
    for report in reports:
        row = {
            "mongo_id": str(report.get("_id", "")),
            "session_id": report.get("sessionId", ""),
            "session_title": report.get("sessionTitle", ""),
            "course_name": report.get("courseName", ""),
            "course_code": report.get("courseCode", ""),
            "instructor_id": report.get("instructorId", ""),
            "instructor_name": report.get("instructorName", ""),
            "session_date": report.get("sessionDate", ""),
            "session_status": report.get("sessionStatus", ""),
            "total_participants": report.get("totalParticipants", 0),
            "total_questions_asked": report.get("totalQuestionsAsked", 0),
            "average_quiz_score": report.get("averageQuizScore"),
            "highly_engaged_count": report.get("engagementSummary", {}).get("highly_engaged", 0),
            "moderately_engaged_count": report.get("engagementSummary", {}).get("moderately_engaged", 0),
            "at_risk_count": report.get("engagementSummary", {}).get("at_risk", 0),
            "report_type": report.get("reportType", "master"),
            "generated_at": str(report.get("generatedAt", ""))
        }
        csv_data.append(row)
    
    # Write to CSV
    csv_path = OUTPUT_DIR / "session_reports.csv"
    if csv_data:
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"   ✅ Saved: {csv_path}")
    
    return csv_path

def convert_students_to_csv(reports):
    """Extract student participation data from reports and convert to CSV"""
    print("\n📄 Converting student participation to CSV...")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    csv_data = []
    for report in reports:
        report_mongo_id = str(report.get("_id", ""))
        session_id = report.get("sessionId", "")
        
        for student in report.get("students", []):
            row = {
                "report_mongo_id": report_mongo_id,
                "session_id": session_id,
                "student_id": student.get("studentId", ""),
                "student_name": student.get("studentName", ""),
                "student_email": student.get("studentEmail", ""),
                "joined_at": str(student.get("joinedAt", "")),
                "left_at": str(student.get("leftAt", "")),
                "attendance_duration_minutes": student.get("attendanceDuration"),
                "total_questions": student.get("totalQuestions", 0),
                "correct_answers": student.get("correctAnswers", 0),
                "incorrect_answers": student.get("incorrectAnswers", 0),
                "quiz_score": student.get("quizScore"),
                "average_response_time": student.get("averageResponseTime"),
                "connection_quality": student.get("averageConnectionQuality", "")
            }
            csv_data.append(row)
    
    # Write to CSV
    csv_path = OUTPUT_DIR / "student_participation.csv"
    if csv_data:
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"   ✅ Saved: {csv_path}")
    else:
        print("   ⚠️ No student data found")
    
    return csv_path


def convert_users_to_csv(users):
    """Convert users to CSV"""
    print("\n📄 Converting users to CSV...")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    csv_data = []
    for user in users:
        row = {
            "mongo_id": str(user.get("_id", "")),
            "email": user.get("email", ""),
            "first_name": user.get("firstName", user.get("first_name", "")),
            "last_name": user.get("lastName", user.get("last_name", "")),
            "role": user.get("role", "student"),
            "created_at": str(user.get("createdAt", user.get("created_at", ""))),
            "last_login": str(user.get("lastLogin", user.get("last_login", ""))),
            "is_active": user.get("isActive", True)
        }
        csv_data.append(row)
    
    csv_path = OUTPUT_DIR / "users.csv"
    if csv_data:
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"   ✅ Saved: {csv_path}")
    
    return csv_path


def convert_quiz_answers_to_csv(answers):
    """Convert quiz answers to CSV"""
    print("\n📄 Converting quiz answers to CSV...")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    csv_data = []
    for answer in answers:
        network = answer.get("networkStrength", {})
        row = {
            "mongo_id": str(answer.get("_id", "")),
            "session_id": answer.get("sessionId", ""),
            "student_id": answer.get("studentId", ""),
            "question_id": answer.get("questionId", ""),
            "answer_index": answer.get("answerIndex"),
            "is_correct": answer.get("isCorrect"),
            "time_taken": answer.get("timeTaken"),
            "network_quality": network.get("quality") if isinstance(network, dict) else None,
            "answered_at": str(answer.get("timestamp", answer.get("answeredAt", "")))
        }
        csv_data.append(row)
    
    csv_path = OUTPUT_DIR / "quiz_answers.csv"
    if csv_data:
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"   ✅ Saved: {csv_path}")
    
    return csv_path


def convert_questions_to_csv(questions):
    """Convert questions to CSV"""
    print("\n📄 Converting questions to CSV...")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    csv_data = []
    for q in questions:
        row = {
            "mongo_id": str(q.get("_id", "")),
            "question_text": q.get("question", q.get("text", "")),
            "question_type": q.get("type", q.get("questionType", "multiple_choice")),
            "difficulty": q.get("difficulty", "medium"),
            "course_id": q.get("courseId", q.get("course_id", "")),
            "created_by": q.get("createdBy", q.get("created_by", "")),
            "correct_answer": q.get("correctAnswer", q.get("correct_answer")),
            "options": json.dumps(q.get("options", []), default=str),
            "tags": json.dumps(q.get("tags", []), default=str),
            "created_at": str(q.get("createdAt", q.get("created_at", "")))
        }
        csv_data.append(row)
    
    csv_path = OUTPUT_DIR / "questions.csv"
    if csv_data:
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"   ✅ Saved: {csv_path}")
    
    return csv_path

# ============================================================
# STEP 3: IMPORT CSV INTO LOCAL MYSQL
# ============================================================

def create_mysql_tables(cursor):
    """Create MySQL tables if they don't exist"""
    print("\n🗄️ Creating MySQL tables...")
    
    # Session Reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_reports_backup (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            mongo_id VARCHAR(24) UNIQUE NOT NULL,
            session_id VARCHAR(24) NOT NULL,
            session_title VARCHAR(255),
            course_name VARCHAR(255),
            course_code VARCHAR(50),
            instructor_id VARCHAR(24),
            instructor_name VARCHAR(255),
            session_date VARCHAR(50),
            session_status VARCHAR(50),
            total_participants INT DEFAULT 0,
            total_questions_asked INT DEFAULT 0,
            average_quiz_score DECIMAL(5,2),
            highly_engaged_count INT DEFAULT 0,
            moderately_engaged_count INT DEFAULT 0,
            at_risk_count INT DEFAULT 0,
            report_type VARCHAR(50) DEFAULT 'master',
            generated_at VARCHAR(50),
            backed_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session_id (session_id),
            INDEX idx_instructor_id (instructor_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Student Participation table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_participation_backup (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            report_mongo_id VARCHAR(24) NOT NULL,
            session_id VARCHAR(24) NOT NULL,
            student_id VARCHAR(50) NOT NULL,
            student_name VARCHAR(255),
            student_email VARCHAR(255),
            joined_at VARCHAR(50),
            left_at VARCHAR(50),
            attendance_duration_minutes INT,
            total_questions INT DEFAULT 0,
            correct_answers INT DEFAULT 0,
            incorrect_answers INT DEFAULT 0,
            quiz_score DECIMAL(5,2),
            average_response_time DECIMAL(8,2),
            connection_quality VARCHAR(50),
            backed_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_student_id (student_id),
            INDEX idx_session_id (session_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_backup (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            mongo_id VARCHAR(24) UNIQUE NOT NULL,
            email VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            role VARCHAR(50) DEFAULT 'student',
            created_at VARCHAR(50),
            last_login VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            backed_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_role (role)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Quiz Answers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_answers_backup (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            mongo_id VARCHAR(24) UNIQUE NOT NULL,
            session_id VARCHAR(50) NOT NULL,
            student_id VARCHAR(50) NOT NULL,
            question_id VARCHAR(50) NOT NULL,
            answer_index INT,
            is_correct BOOLEAN,
            time_taken DECIMAL(8,2),
            network_quality VARCHAR(50),
            answered_at VARCHAR(50),
            backed_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session_id (session_id),
            INDEX idx_student_id (student_id),
            INDEX idx_question_id (question_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # Questions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions_backup (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            mongo_id VARCHAR(24) UNIQUE NOT NULL,
            question_text TEXT,
            question_type VARCHAR(50),
            difficulty VARCHAR(50),
            course_id VARCHAR(24),
            created_by VARCHAR(24),
            correct_answer INT,
            options JSON,
            tags JSON,
            created_at VARCHAR(50),
            backed_up_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_course_id (course_id),
            INDEX idx_difficulty (difficulty)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    print("   ✅ All tables created (5 tables)")

def import_csv_to_mysql(cursor, csv_path, table_name):
    """Import CSV file into MySQL table"""
    print(f"\n📥 Importing {csv_path.name} into {table_name}...")
    
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print(f"   ⚠️ CSV is empty, skipping")
        return 0
    
    # Replace NaN with None
    df = df.where(pd.notnull(df), None)
    
    # Get column names
    columns = list(df.columns)
    placeholders = ", ".join(["%s"] * len(columns))
    column_names = ", ".join(columns)
    
    # Insert data
    inserted = 0
    for _, row in df.iterrows():
        try:
            values = tuple(row[col] for col in columns)
            cursor.execute(f"""
                INSERT IGNORE INTO {table_name} ({column_names})
                VALUES ({placeholders})
            """, values)
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"   ⚠️ Error inserting row: {e}")
    
    print(f"   ✅ Inserted {inserted} rows into {table_name}")
    return inserted

def connect_local_mysql():
    """Connect to local MySQL"""
    print("\n🔗 Connecting to local MySQL...")
    
    try:
        # First, try to create database if it doesn't exist
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"]
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        cursor.close()
        conn.close()
        
        # Now connect to the database
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print(f"✅ Connected to MySQL: {MYSQL_CONFIG['database']}")
        return conn
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return None

# ============================================================
# MAIN FUNCTION
# ============================================================

def main():
    print("=" * 60)
    print("MongoDB → Local MySQL Export Tool")
    print("=" * 60)
    
    # Step 1: Connect to MongoDB and export ALL collections
    try:
        db = connect_mongodb()
        reports = export_session_reports(db)
        users = export_users(db)
        quiz_answers = export_quiz_answers(db)
        questions = export_questions(db)
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        print("\n💡 Make sure MONGO_URI is set in your .env file or update the script")
        return
    
    # Step 2: Convert ALL to CSV
    print("\n" + "=" * 60)
    print("CONVERTING TO CSV...")
    print("=" * 60)
    
    reports_csv = convert_reports_to_csv(reports) if reports else None
    students_csv = convert_students_to_csv(reports) if reports else None
    users_csv = convert_users_to_csv(users) if users else None
    quiz_answers_csv = convert_quiz_answers_to_csv(quiz_answers) if quiz_answers else None
    questions_csv = convert_questions_to_csv(questions) if questions else None
    
    print("\n" + "=" * 60)
    print("CSV FILES CREATED:")
    if reports_csv: print(f"  📄 {reports_csv}")
    if students_csv: print(f"  📄 {students_csv}")
    if users_csv: print(f"  📄 {users_csv}")
    if quiz_answers_csv: print(f"  📄 {quiz_answers_csv}")
    if questions_csv: print(f"  📄 {questions_csv}")
    print("=" * 60)
    
    # Step 3: Import to local MySQL
    print("\n" + "=" * 60)
    print("IMPORTING TO LOCAL MYSQL...")
    print("=" * 60)
    
    conn = connect_local_mysql()
    if not conn:
        print("\n💡 Update MYSQL_CONFIG in the script with your local MySQL password")
        print("   Or import the CSV files manually using MySQL Workbench")
        return
    
    try:
        cursor = conn.cursor()
        
        # Create ALL tables
        create_mysql_tables(cursor)
        
        # Import ALL CSVs
        if reports_csv and reports_csv.exists():
            import_csv_to_mysql(cursor, reports_csv, "session_reports_backup")
        if students_csv and students_csv.exists():
            import_csv_to_mysql(cursor, students_csv, "student_participation_backup")
        if users_csv and users_csv.exists():
            import_csv_to_mysql(cursor, users_csv, "users_backup")
        if quiz_answers_csv and quiz_answers_csv.exists():
            import_csv_to_mysql(cursor, quiz_answers_csv, "quiz_answers_backup")
        if questions_csv and questions_csv.exists():
            import_csv_to_mysql(cursor, questions_csv, "questions_backup")
        
        conn.commit()
        print("\n✅ All data imported successfully!")
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    print("\n" + "=" * 60)
    print("DONE! Check your local MySQL database:")
    print(f"  Database: {MYSQL_CONFIG['database']}")
    print("  Tables:")
    print("    - session_reports_backup")
    print("    - student_participation_backup")
    print("    - users_backup")
    print("    - quiz_answers_backup")
    print("    - questions_backup")
    print("=" * 60)

if __name__ == "__main__":
    main()

