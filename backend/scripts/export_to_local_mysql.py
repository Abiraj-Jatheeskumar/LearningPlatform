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
            "generated_at": str(report.get("generatedAt", "")),
            "full_document": json.dumps(report, default=str)
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
            full_document JSON,
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
    
    print("   ✅ Tables created")

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
    
    # Step 1: Connect to MongoDB and export
    try:
        db = connect_mongodb()
        reports = export_session_reports(db)
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        print("\n💡 Make sure MONGO_URI is set in your .env file or update the script")
        return
    
    if not reports:
        print("\n⚠️ No reports found in MongoDB")
        return
    
    # Step 2: Convert to CSV
    reports_csv = convert_reports_to_csv(reports)
    students_csv = convert_students_to_csv(reports)
    
    print("\n" + "=" * 60)
    print("CSV FILES CREATED:")
    print(f"  📄 {reports_csv}")
    print(f"  📄 {students_csv}")
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
        
        # Create tables
        create_mysql_tables(cursor)
        
        # Import CSVs
        import_csv_to_mysql(cursor, reports_csv, "session_reports_backup")
        import_csv_to_mysql(cursor, students_csv, "student_participation_backup")
        
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
    print("  Tables: session_reports_backup, student_participation_backup")
    print("=" * 60)

if __name__ == "__main__":
    main()

