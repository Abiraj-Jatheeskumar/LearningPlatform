"""
Real-time Live Learning System with Flask-SocketIO
Each student receives a different question when instructor triggers
🎯 SESSION-BASED ROOMS: Only joined students receive quizzes
"""
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import os
import eventlet

# Monkey patch for eventlet
eventlet.monkey_patch()

# Load environment variables
load_dotenv()

# Import database and models
from database import init_db, get_db
from models import ParticipantModel, QuestionModel, ResponseModel
from routes.live import live_bp

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/live_learning')
init_db(mongo_uri)

# Register blueprints
app.register_blueprint(live_bp)

# Socket ID to Student ID mapping
socket_to_student = {}

# 🎯 Session room tracking: {session_id: {student_id: {socket_id, name, status, ...}}}
session_participants = {}


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Real-time Live Learning System',
        'version': '2.0.0',
        'features': ['Session-based quiz delivery', 'Only joined students receive quizzes'],
        'endpoints': {
            'student': '/student',
            'instructor': '/instructor',
            'api': '/api/live'
        }
    })


@app.route('/student')
def student_page():
    """Student page"""
    return render_template('student.html')


@app.route('/instructor')
def instructor_page():
    """Instructor page"""
    return render_template('instructor.html')


@app.route('/health')
def health():
    """Health check"""
    try:
        db = get_db()
        db.client.admin.command('ping')
        db_status = 'connected'
    except:
        db_status = 'disconnected'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'socketio': 'active',
        'active_sessions': list(session_participants.keys()),
        'total_participants': sum(len(p) for p in session_participants.values())
    })


# =========================================================
# Socket.IO Event Handlers
# =========================================================

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print(f"🔌 Client connected: {request.sid}")
    emit('connected', {'socket_id': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected - Remove from all session rooms"""
    print(f"🔌 Client disconnected: {request.sid}")
    
    student_id = socket_to_student.get(request.sid)
    if student_id:
        # Remove from old participant model
        ParticipantModel.remove_participant(request.sid)
        del socket_to_student[request.sid]
        
        # 🎯 Remove from all session rooms
        for session_id in list(session_participants.keys()):
            if student_id in session_participants[session_id]:
                session_participants[session_id][student_id]['status'] = 'left'
                session_participants[session_id][student_id]['leftAt'] = datetime.utcnow().isoformat()
                
                # Leave the Socket.IO room
                leave_room(f"session_{session_id}")
                
                # Notify instructor
                emit('student_left', {
                    'student_id': student_id,
                    'session_id': session_id,
                    'name': session_participants[session_id][student_id].get('name', student_id)
                }, room=f"instructor_{session_id}")
                
                print(f"   👋 Removed from session: {session_id}")
        
        print(f"   Removed student: {student_id}")


# =========================================================
# 🎯 SESSION-BASED JOIN (NEW - Students must join to receive quizzes)
# =========================================================

@socketio.on('join_session')
def handle_join_session(data):
    """
    🎯 Student joins a SESSION ROOM
    Only students in this room will receive quiz questions for this session
    Data: { session_id, student_id, name, email }
    """
    try:
        session_id = data.get('session_id') or data.get('sessionId')
        student_id = data.get('student_id') or data.get('studentId')
        name = data.get('name') or data.get('studentName', f'Student {student_id}')
        email = data.get('email') or data.get('studentEmail')
        
        if not session_id or not student_id:
            emit('error', {'message': 'session_id and student_id required'})
            return
        
        # Initialize session room if not exists
        if session_id not in session_participants:
            session_participants[session_id] = {}
        
        # Add participant to session
        session_participants[session_id][student_id] = {
            'socket_id': request.sid,
            'name': name,
            'email': email,
            'status': 'joined',
            'joinedAt': datetime.utcnow().isoformat()
        }
        
        # Store mapping
        socket_to_student[request.sid] = student_id
        
        # 🎯 Join the session-specific Socket.IO room
        join_room(f"session_{session_id}")
        
        # Also join instructor room for updates
        join_room(f"instructor_{session_id}")
        
        participant_count = len([p for p in session_participants[session_id].values() if p['status'] == 'joined'])
        
        print(f"✅ Student joined SESSION: {name} ({student_id}) in session {session_id}")
        print(f"   Socket: {request.sid}")
        print(f"   Room: session_{session_id} (now has {participant_count} students)")
        
        # Confirm to student
        emit('session_joined', {
            'success': True,
            'session_id': session_id,
            'student_id': student_id,
            'socket_id': request.sid,
            'participant_count': participant_count,
            'message': 'You will receive quiz questions when instructor triggers them'
        })
        
        # Notify instructor
        emit('student_joined_session', {
            'student_id': student_id,
            'name': name,
            'session_id': session_id,
            'participant_count': participant_count
        }, room=f"instructor_{session_id}")
        
    except Exception as e:
        print(f"❌ Error in join_session: {e}")
        emit('error', {'message': str(e)})


@socketio.on('leave_session')
def handle_leave_session(data):
    """Student leaves a session room"""
    try:
        session_id = data.get('session_id') or data.get('sessionId')
        student_id = data.get('student_id') or data.get('studentId')
        
        if session_id and student_id and session_id in session_participants:
            if student_id in session_participants[session_id]:
                session_participants[session_id][student_id]['status'] = 'left'
                session_participants[session_id][student_id]['leftAt'] = datetime.utcnow().isoformat()
                
                leave_room(f"session_{session_id}")
                
                emit('session_left', {'success': True, 'session_id': session_id})
                print(f"👋 Student {student_id} left session {session_id}")
                
    except Exception as e:
        print(f"❌ Error in leave_session: {e}")


# =========================================================
# 🎯 TRIGGER QUIZ TO SESSION ONLY (NEW)
# =========================================================

@socketio.on('trigger_quiz_to_session')
def handle_trigger_quiz_to_session(data):
    """
    🎯 Instructor triggers quiz to ONLY students who joined this session
    Data: { session_id, question_id, question, options, time_limit }
    """
    try:
        session_id = data.get('session_id') or data.get('sessionId')
        
        if not session_id:
            emit('error', {'message': 'session_id required'})
            return
        
        print(f"\n🚀 Triggering quiz to SESSION: {session_id}")
        
        # Get only JOINED participants in this session
        if session_id not in session_participants:
            emit('error', {'message': f'No participants in session {session_id}'})
            return
        
        active_participants = [
            {**info, 'student_id': sid}
            for sid, info in session_participants[session_id].items()
            if info.get('status') == 'joined'
        ]
        
        if not active_participants:
            emit('error', {'message': 'No active participants in session'})
            return
        
        print(f"   Found {len(active_participants)} active students in session")
        
        # Prepare quiz data
        quiz_data = {
            'type': 'quiz',
            'session_id': session_id,
            'question_id': data.get('question_id') or data.get('questionId'),
            'question': data.get('question'),
            'options': data.get('options'),
            'time_limit': data.get('time_limit') or data.get('timeLimit', 30),
            'triggered_at': datetime.utcnow().isoformat()
        }
        
        # 🎯 EMIT ONLY TO SESSION ROOM - Not to all clients!
        socketio.emit('NEW_QUESTION', quiz_data, room=f"session_{session_id}")
        
        print(f"✅ Quiz sent to room session_{session_id}")
        
        # Notify instructor
        emit('quiz_sent_to_session', {
            'success': True,
            'session_id': session_id,
            'sent_to': len(active_participants),
            'participants': [{'student_id': p['student_id'], 'name': p['name']} for p in active_participants]
        })
        
    except Exception as e:
        print(f"❌ Error triggering quiz to session: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': str(e)})


# =========================================================
# Legacy handlers (kept for backward compatibility)
# =========================================================

@socketio.on('join_student')
def handle_join_student(data):
    """
    Legacy: Student joins the system (old method)
    Data: { student_id, meeting_id, name }
    """
    try:
        student_id = data.get('student_id')
        meeting_id = data.get('meeting_id')
        name = data.get('name', f'Student {student_id}')
        
        if not student_id or not meeting_id:
            emit('error', {'message': 'student_id and meeting_id required'})
            return
        
        # Add to participants collection
        participant = ParticipantModel.add_participant(
            student_id=student_id,
            meeting_id=meeting_id,
            socket_id=request.sid,
            name=name
        )
        
        # Store mapping
        socket_to_student[request.sid] = student_id
        
        # Join rooms
        join_room(request.sid)
        join_room(f"meeting_{meeting_id}")
        join_room(f"instructor_{meeting_id}")
        
        # 🎯 Also join as session (treat meeting_id as session_id for compatibility)
        if meeting_id not in session_participants:
            session_participants[meeting_id] = {}
        
        session_participants[meeting_id][student_id] = {
            'socket_id': request.sid,
            'name': name,
            'status': 'joined',
            'joinedAt': datetime.utcnow().isoformat()
        }
        join_room(f"session_{meeting_id}")
        
        print(f"✅ Student joined: {name} ({student_id}) in meeting {meeting_id}")
        
        emit('joined', {
            'success': True,
            'student_id': student_id,
            'meeting_id': meeting_id,
            'socket_id': request.sid
        })
        
        # Notify instructor
        emit('student_joined', {
            'student_id': student_id,
            'name': name,
            'meeting_id': meeting_id
        }, room=f"instructor_{meeting_id}")
        
    except Exception as e:
        print(f"❌ Error in join_student: {e}")
        emit('error', {'message': str(e)})


@socketio.on('join_instructor')
def handle_join_instructor(data):
    """Instructor joins the system"""
    try:
        instructor_id = data.get('instructor_id')
        meeting_id = data.get('meeting_id') or data.get('session_id') or data.get('sessionId')
        
        if not instructor_id or not meeting_id:
            emit('error', {'message': 'instructor_id and meeting_id/session_id required'})
            return
        
        # Join instructor room
        join_room(f"instructor_{meeting_id}")
        
        print(f"✅ Instructor joined: {instructor_id} for meeting/session {meeting_id}")
        
        # Get current participants
        participant_count = 0
        if meeting_id in session_participants:
            participant_count = len([p for p in session_participants[meeting_id].values() if p['status'] == 'joined'])
        
        emit('instructor_joined', {
            'success': True,
            'instructor_id': instructor_id,
            'meeting_id': meeting_id,
            'participant_count': participant_count
        })
        
    except Exception as e:
        print(f"❌ Error in join_instructor: {e}")
        emit('error', {'message': str(e)})


@socketio.on('trigger_questions')
def handle_trigger_questions(data):
    """
    Legacy: Instructor triggers questions (now uses session rooms)
    Data: { meeting_id }
    """
    try:
        meeting_id = data.get('meeting_id') or data.get('session_id') or data.get('sessionId')
        
        if not meeting_id:
            emit('error', {'message': 'meeting_id/session_id required'})
            return
        
        print(f"\n🚀 Triggering questions for meeting/session: {meeting_id}")
        
        # 🎯 Get participants from session room
        if meeting_id in session_participants:
            active_participants = [
                {**info, 'student_id': sid}
                for sid, info in session_participants[meeting_id].items()
                if info.get('status') == 'joined'
            ]
        else:
            # Fallback to old participant model
            active_participants = ParticipantModel.get_participants_by_meeting(meeting_id)
        
        if not active_participants:
            emit('error', {'message': 'No participants found'})
            return
        
        num_students = len(active_participants)
        print(f"   Found {num_students} students")
        
        # Get random questions
        questions = QuestionModel.get_random_questions(num_students)
        
        if len(questions) < num_students:
            emit('error', {
                'message': f'Not enough questions. Need {num_students}, have {len(questions)}'
            })
            return
        
        # Assign and send different question to each student
        from models import StudentQuestionModel
        
        assignments = []
        for i, participant in enumerate(active_participants):
            question = questions[i]
            student_id = participant.get('student_id')
            socket_id = participant.get('socket_id')
            
            # Save assignment
            StudentQuestionModel.assign_question(
                student_id=student_id,
                question_id=question['_id'],
                meeting_id=meeting_id
            )
            
            # Send question to this specific student
            question_data = {
                'type': 'quiz',
                'question_id': question['_id'],
                'question': question['question'],
                'options': question['options'],
                'sent_time': str(datetime.utcnow())
            }
            
            # Emit to specific student's socket
            if socket_id:
                socketio.emit('NEW_QUESTION', question_data, room=socket_id)
            
            print(f"   ✅ Sent Q#{i+1} to {participant.get('name', student_id)}")
            
            assignments.append({
                'student_id': student_id,
                'student_name': participant.get('name', student_id),
                'question_id': question['_id']
            })
        
        print(f"\n✅ All questions sent to {num_students} students!\n")
        
        # Notify instructor
        emit('questions_sent', {
            'success': True,
            'count': num_students,
            'assignments': assignments
        }, room=f"instructor_{meeting_id}")
        
    except Exception as e:
        print(f"❌ Error triggering questions: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': str(e)})


@socketio.on('submit_answer_ws')
def handle_submit_answer_ws(data):
    """Student submits answer via WebSocket"""
    try:
        student_id = data.get('student_id')
        question_id = data.get('question_id')
        answer = data.get('answer')
        response_time = data.get('response_time')
        
        if not all([student_id, question_id, answer is not None]):
            emit('error', {'message': 'Missing required fields'})
            return
        
        # Get question
        question = QuestionModel.get_question_by_id(question_id)
        
        if not question:
            emit('error', {'message': 'Question not found'})
            return
        
        # Check correctness
        correct_answer = question.get('correct')
        is_correct = (answer == correct_answer)
        
        # Save response
        response = ResponseModel.save_response(
            student_id=student_id,
            question_id=question_id,
            answer=answer,
            correct=is_correct,
            response_time=response_time
        )
        
        print(f"✅ Answer: Student {student_id} -> {'✓ Correct' if is_correct else '✗ Wrong'}")
        
        # Send result back to student
        emit('answer_result', {
            'correct': is_correct,
            'correct_answer': correct_answer,
            'your_answer': answer
        })
        
        # Get updated stats
        stats = ResponseModel.get_stats_by_question(question_id)
        
        # Get participant info
        participant = ParticipantModel.get_participant_by_socket(request.sid)
        meeting_id = participant.get('meeting_id') if participant else None
        
        # Send update to instructor
        if meeting_id:
            emit('ANSWER_UPDATE', {
                'student_id': student_id,
                'student_name': participant.get('name', student_id),
                'question_id': question_id,
                'answer': answer,
                'correct': is_correct,
                'stats': stats,
                'timestamp': str(datetime.utcnow())
            }, room=f"instructor_{meeting_id}")
        
    except Exception as e:
        print(f"❌ Error submitting answer: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': str(e)})


# =========================================================
# REST API for session participants
# =========================================================

@app.route('/api/session/<session_id>/participants')
def get_session_participants(session_id):
    """Get all active participants in a session"""
    if session_id not in session_participants:
        return jsonify({'participants': [], 'count': 0})
    
    active = [
        {'student_id': sid, 'name': info.get('name'), 'status': info.get('status')}
        for sid, info in session_participants[session_id].items()
        if info.get('status') == 'joined'
    ]
    
    return jsonify({'participants': active, 'count': len(active)})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    
    print("\n" + "="*60)
    print("🚀 Real-time Live Learning System Starting...")
    print("="*60)
    print(f"   Port: {port}")
    print(f"   Student UI: http://localhost:{port}/student")
    print(f"   Instructor UI: http://localhost:{port}/instructor")
    print(f"   WebSocket: Active (Socket.IO)")
    print(f"   🎯 Session-based quiz delivery: ENABLED")
    print("="*60 + "\n")
    
    # Run with eventlet
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
