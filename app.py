from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify, make_response
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
import re
from functools import wraps
import json
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Configuration
UPLOAD_FOLDER = 'uploads'
USER_DATA_FILE = 'users.txt'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xlsx', 'csv', 'ppt', 'pptx', 'mp4', 'avi', 'zip', 'rar'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Gemini AI
genai.configure(api_key='AIzaSyBU_eVtXDDT6OB8hRO_RYOuv_qwQVAa-mk')
model = genai.GenerativeModel('gemini-2.0-flash')

# Data storage
USER_DATA = {}
SUPERUSER_DATA = {"varshith": "1234"}
COURSES = ["Python", "Java", "C", "C++"]
USER_COURSES = {}
USER_COURSES_FILE = 'user_courses.txt'
PROGRESS_FILE = 'student_progress.json'
AI_ANALYTICS_FILE = 'ai_analytics.json'
TIMETABLE_FILE = 'student_timetables.json'
USER_TIMETABLE_FILE = 'user_custom_timetables.json'  # NEW: For user-editable timetables

# Days and time slots
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_SLOTS = ["09:00 AM", "10:30 AM", "12:00 PM", "01:30 PM", "03:00 PM", "04:30 PM"]

# Utility functions
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    username, password = line.strip().split(',')
                    USER_DATA[username] = password

def save_user_data():
    with open(USER_DATA_FILE, 'w') as f:
        for username, password in USER_DATA.items():
            f.write(f"{username},{password}\n")

def load_user_courses():
    """Load user course assignments from file"""
    global USER_COURSES
    USER_COURSES = {}
    if os.path.exists(USER_COURSES_FILE):
        with open(USER_COURSES_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        username = parts[0]
                        course = parts[1]
                        if username not in USER_COURSES:
                            USER_COURSES[username] = []
                        USER_COURSES[username].append(course)

def save_user_courses():
    """Save user course assignments to file"""
    with open(USER_COURSES_FILE, 'w') as f:
        for username, courses in USER_COURSES.items():
            for course in courses:
                f.write(f"{username},{course}\n")

# ==================== PROGRESS TRACKING FUNCTIONS ====================
def load_student_progress():
    """Load student progress from JSON file"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_student_progress(progress_data):
    """Save student progress to JSON file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress_data, f, indent=4)

def get_student_progress(username):
    """Get progress for a specific student"""
    progress_data = load_student_progress()
    if username not in progress_data:
        # Initialize progress for all assigned courses
        progress_data[username] = {}
        for course in USER_COURSES.get(username, []):
            progress_data[username][course] = {
                "percentage": 0,
                "modules_completed": 0,
                "total_modules": 5,  # Assume 5 modules per course
                "last_updated": datetime.now().isoformat()
            }
        save_student_progress(progress_data)
    return progress_data.get(username, {})

def update_course_progress(username, course, percentage, modules_completed=None):
    """Update progress for a specific course"""
    progress_data = load_student_progress()
    if username not in progress_data:
        progress_data[username] = {}
    
    if course not in progress_data[username]:
        progress_data[username][course] = {
            "percentage": 0,
            "modules_completed": 0,
            "total_modules": 5,
            "last_updated": datetime.now().isoformat()
        }
    
    progress_data[username][course]["percentage"] = percentage
    if modules_completed is not None:
        progress_data[username][course]["modules_completed"] = modules_completed
    progress_data[username][course]["last_updated"] = datetime.now().isoformat()
    
    save_student_progress(progress_data)

# ==================== AI ANALYTICS FUNCTIONS ====================
def load_ai_analytics():
    """Load AI analytics data"""
    if os.path.exists(AI_ANALYTICS_FILE):
        try:
            with open(AI_ANALYTICS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_ai_analytics(analytics_data):
    """Save AI analytics data"""
    with open(AI_ANALYTICS_FILE, 'w') as f:
        json.dump(analytics_data, f, indent=4)

def track_question(username, question):
    """Track student questions for AI analytics"""
    analytics_data = load_ai_analytics()
    
    if username not in analytics_data:
        analytics_data[username] = {
            "total_questions": 0,
            "topics": {},
            "weak_areas": [],
            "insights": ""
        }
    
    analytics_data[username]["total_questions"] += 1
    
    # Extract topics from question using keywords
    keywords = ["python", "java", "c", "c++", "loop", "function", "array", "oop", 
                "variable", "string", "list", "dictionary", "recursion", "sorting"]
    
    for keyword in keywords:
        if keyword.lower() in question.lower():
            if keyword not in analytics_data[username]["topics"]:
                analytics_data[username]["topics"][keyword] = 0
            analytics_data[username]["topics"][keyword] += 1
    
    # Generate insights if weak areas exist
    if analytics_data[username]["topics"]:
        max_topic = max(analytics_data[username]["topics"], 
                       key=analytics_data[username]["topics"].get)
        weak_areas = sorted(analytics_data[username]["topics"].items(), 
                           key=lambda x: x[1], reverse=True)[:3]
        analytics_data[username]["weak_areas"] = [topic[0] for topic in weak_areas]
    
    save_ai_analytics(analytics_data)

def get_ai_insights(username):
    """Generate AI insights for student"""
    analytics_data = load_ai_analytics()
    student_analytics = analytics_data.get(username, {})
    
    if not student_analytics.get("weak_areas"):
        return "Keep up the great learning journey! No specific areas need attention yet."
    
    weak_areas = student_analytics.get("weak_areas", [])
    total_questions = student_analytics.get("total_questions", 0)
    
    if weak_areas:
        main_weak = weak_areas[0]
        insight = f"📊 You've asked {total_questions} questions. Focus on: {main_weak.title()}. You're doing great!"
        return insight
    
    return "Your learning is on track! Keep exploring."

# ==================== TIMETABLE GENERATION FUNCTIONS ====================
HOURS = ["9:00 AM", "11:00 AM", "2:00 PM", "4:00 PM"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

def load_student_timetables():
    """Load student timetables"""
    if os.path.exists(TIMETABLE_FILE):
        try:
            with open(TIMETABLE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_student_timetables(timetables_data):
    """Save student timetables"""
    with open(TIMETABLE_FILE, 'w') as f:
        json.dump(timetables_data, f, indent=4)

def generate_timetable(username):
    """Generate automatic timetable based on assigned courses"""
    timetables = load_student_timetables()
    assigned_courses = USER_COURSES.get(username, [])
    
    if not assigned_courses:
        return {}
    
    # Create timetable
    timetable = {}
    course_index = 0
    used_slots = set()
    
    for day_idx, day in enumerate(DAYS):
        timetable[day] = []
        
        for hour_idx, hour in enumerate(HOURS):
            slot_key = f"{day}_{hour_idx}"
            
            # Get course (cycle through assigned courses)
            course = assigned_courses[course_index % len(assigned_courses)]
            
            # Avoid same course consecutively
            if timetable[day] and timetable[day][-1]["course"] == course:
                # Try next course
                course_index = (course_index + 1) % len(assigned_courses)
                course = assigned_courses[course_index % len(assigned_courses)]
            
            timetable[day].append({
                "time": hour,
                "course": course,
                "completed": False,
                "notes": ""
            })
            
            course_index += 1
    
    timetables[username] = {
        "timetable": timetable,
        "generated_date": datetime.now().isoformat(),
        "courses": assigned_courses
    }
    
    save_student_timetables(timetables)
    return timetable

def get_student_timetable(username):
    """Get or generate student timetable"""
    timetables = load_student_timetables()
    
    if username in timetables:
        return timetables[username].get("timetable", {})
    
    return generate_timetable(username)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_folder(username):
    path = os.path.join(app.config['UPLOAD_FOLDER'], username)
    os.makedirs(path, exist_ok=True)
    return path

# ==================== USER-EDITABLE TIMETABLE FUNCTIONS ====================
def load_user_timetables():
    """Load user-editable timetables"""
    if os.path.exists(USER_TIMETABLE_FILE):
        try:
            with open(USER_TIMETABLE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_timetables(timetables_data):
    """Save user-editable timetables"""
    with open(USER_TIMETABLE_FILE, 'w') as f:
        json.dump(timetables_data, f, indent=4)

def get_user_timetable_entries(username):
    """Get all timetable entries for a user"""
    timetables = load_user_timetables()
    return timetables.get(username, [])

def add_timetable_entry(username, day, course, time, notes=""):
    """Add a new timetable entry for user"""
    timetables = load_user_timetables()
    
    if username not in timetables:
        timetables[username] = []
    
    # Create unique ID based on timestamp
    entry_id = int(datetime.now().timestamp() * 1000)
    
    entry = {
        "id": entry_id,
        "day": day,
        "course": course,
        "time": time,
        "notes": notes,
        "created_at": datetime.now().isoformat()
    }
    
    timetables[username].append(entry)
    save_user_timetables(timetables)
    return entry

def update_timetable_entry(username, entry_id, day, course, time, notes=""):
    """Update an existing timetable entry"""
    timetables = load_user_timetables()
    
    if username not in timetables:
        return None
    
    for entry in timetables[username]:
        if entry["id"] == entry_id:
            entry["day"] = day
            entry["course"] = course
            entry["time"] = time
            entry["notes"] = notes
            entry["updated_at"] = datetime.now().isoformat()
            save_user_timetables(timetables)
            return entry
    
    return None

def delete_timetable_entry(username, entry_id):
    """Delete a timetable entry"""
    timetables = load_user_timetables()
    
    if username not in timetables:
        return False
    
    timetables[username] = [e for e in timetables[username] if e["id"] != entry_id]
    save_user_timetables(timetables)
    return True

def format_response(response):
    formatted_response = response.text
    formatted_response = re.sub(
        r'```(\w+)?\n(.*?)\n```',
        r'```\1\n\2\n```',
        formatted_response,
        flags=re.DOTALL
    )
    return formatted_response

# Load user data on startup
load_user_data()
load_user_courses()

# ==================== AUTHENTICATION MIDDLEWARE ====================
# List of routes that don't require authentication
PUBLIC_ROUTES = ['login', 'static']

@app.before_request
def check_authentication():
    """
    Global middleware to check if user is authenticated.
    Redirects to login if trying to access protected routes without session.
    """
    # Get the current route name (endpoint)
    endpoint = request.endpoint
    
    # Skip authentication check for public routes
    if endpoint in PUBLIC_ROUTES or endpoint is None:
        return None
    
    # Skip for static files
    if endpoint == 'static':
        return None
    
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return None

@app.after_request
def set_cache_headers(response):
    """
    Disable caching for protected pages to prevent accessing them via back button.
    This ensures users cannot view cached pages after logout.
    """
    # Check if this is a protected route (user is authenticated for it)
    endpoint = request.endpoint
    
    # Set cache control headers for all responses
    if endpoint not in PUBLIC_ROUTES and endpoint != 'static':
        # Disable caching for protected routes
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.cache_control.must_revalidate = True
        response.cache_control.max_age = 0
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

# ==================== AUTHENTICATION ROUTES ====================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USER_DATA and password == USER_DATA[username]:
            session["username"] = username
            session["is_superuser"] = False
            return redirect(url_for("welcome"))
        elif username in SUPERUSER_DATA and password == SUPERUSER_DATA[username]:
            session["username"] = username
            session["is_superuser"] = True
            return redirect(url_for("superuser_dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    """
    Logout route that securely clears the session and sets cache-control headers
    to prevent accessing protected pages via browser back button.
    """
    # Clear all session data
    session.clear()
    
    # Create response to login page
    response = make_response(redirect(url_for('login')))
    
    # Disable caching for this response
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    response.cache_control.max_age = 0
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Clear any cookies that might store session info
    response.delete_cookie('session')
    
    return response

# Main application routes
@app.route("/welcome")
def welcome():
    if "username" in session and not session.get("is_superuser"):
        username = session["username"]
        user_folder = get_user_folder(username)
        uploaded_files = os.listdir(user_folder)

        # Include superuser uploads in updates
        superuser_folder = get_user_folder("varshith")
        superuser_files = os.listdir(superuser_folder) if os.path.exists(superuser_folder) else []

        # Get assigned courses for this user
        assigned_courses = USER_COURSES.get(username, [])
        
        # Get student analytics data
        progress = get_student_progress(username)
        insights = get_ai_insights(username)
        timetable = get_student_timetable(username)
        
        # Initialize timetable if empty
        if not timetable:
            timetable = generate_timetable(username)

        return render_template("welcome.html",
                               username=username,
                               files=uploaded_files,
                               superuser_files=superuser_files,
                               assigned_courses=assigned_courses,
                               COURSES=assigned_courses,
                               progress=progress,
                               insights=insights,
                               timetable=timetable,
                               timetable_json=json.dumps(timetable))
    return redirect(url_for("login"))

@app.route("/courses", methods=["GET", "POST"])
def courses():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST" and session.get("is_superuser"):
        action = request.form.get("action")
        course_name = request.form.get("course_name", "").strip()
        if course_name:
            if action == "add" and course_name not in COURSES:
                COURSES.append(course_name)
            elif action == "delete" and course_name in COURSES:
                COURSES.remove(course_name)

    return render_template("courses.html", courses=COURSES, is_superuser=session.get("is_superuser"))

@app.route("/uploads", methods=["GET", "POST"])
def uploads():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    is_superuser = session.get("is_superuser")
    user_folder = get_user_folder(username)

    if request.method == "POST":
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(user_folder, filename))
            return redirect(url_for("uploads"))

    files = os.listdir(user_folder)
    dashboard_url = url_for('superuser_dashboard') if is_superuser else url_for("welcome")

    superuser_files = []
    if not is_superuser:
        superuser_folder = get_user_folder("varshith")
        superuser_files = os.listdir(superuser_folder) if os.path.exists(superuser_folder) else []

    return render_template("uploads.html", files=files, dashboard_url=dashboard_url, superuser_files=superuser_files)

@app.route("/delete_files", methods=["POST"])
def delete_files():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    is_superuser = session.get("is_superuser")
    target_user = request.form.get("target_user", username)

    if not is_superuser and username != target_user:
        return "Unauthorized", 403

    user_folder = get_user_folder(target_user)
    selected_files = request.form.getlist("selected_files")

    for file in selected_files:
        file_path = os.path.join(user_folder, file)
        if os.path.exists(file_path):
            os.remove(file_path)

    return redirect(url_for("uploads"))

@app.route("/serve_file/<username>/<filename>")
def serve_file(username, filename):
    if "username" not in session:
        return redirect(url_for("login"))

    file_folder = get_user_folder(username)
    file_path = os.path.join(file_folder, filename)
    if os.path.exists(file_path):
        return send_from_directory(file_folder, filename)
    return "File not found or unauthorized", 404

@app.route("/custom_timetable")
def custom_timetable():
    """User-editable custom timetable page"""
    if "username" not in session or session.get("is_superuser"):
        return redirect(url_for("login"))
    
    username = session["username"]
    return render_template("custom_timetable.html", username=username)

# Superuser routes
@app.route("/superuser_dashboard")
def superuser_dashboard():
    if "username" in session and session.get("is_superuser"):
        username = session["username"]
        superuser_folder = get_user_folder(username)
        
        # Get superuser's own uploaded files
        files = os.listdir(superuser_folder)
        
        # Get all users and their course assignments
        users = list(USER_DATA.keys())
        user_files = {user: os.listdir(get_user_folder(user)) for user in users}
        user_courses_map = {user: USER_COURSES.get(user, []) for user in users}
        
        return render_template("superuser_dashboard.html", 
                               username=username,
                               files=files,
                               users=users, 
                               user_files=user_files,
                               courses=COURSES,
                               user_courses=user_courses_map)
    return redirect(url_for("login"))

@app.route("/manage_users", methods=["POST"])
def manage_users():
    if "username" in session and session.get("is_superuser"):
        action = request.form.get("action")
        username = request.form.get("username")
        password = request.form.get("password")
        if action == "add" and username and password:
            USER_DATA[username] = password
            save_user_data()
        elif action == "delete" and username in USER_DATA:
            del USER_DATA[username]
            save_user_data()
    return redirect(url_for("superuser_dashboard"))

@app.route("/assign_course", methods=["POST"])
def assign_course():
    if "username" in session and session.get("is_superuser"):
        username = request.form.get("username")
        course = request.form.get("course")
        
        if username and course and username in USER_DATA and course in COURSES:
            if username not in USER_COURSES:
                USER_COURSES[username] = []
            
            # Prevent duplicate course assignments
            if course not in USER_COURSES[username]:
                USER_COURSES[username].append(course)
                save_user_courses()
    
    return redirect(url_for("superuser_dashboard"))

@app.route("/remove_course", methods=["POST"])
def remove_course():
    if "username" in session and session.get("is_superuser"):
        username = request.form.get("username")
        course = request.form.get("course")
        
        if username and course and username in USER_COURSES:
            if course in USER_COURSES[username]:
                USER_COURSES[username].remove(course)
                save_user_courses()
    
    return redirect(url_for("superuser_dashboard"))

# --- 📘 NEW COURSE ROUTES ---
@app.route("/python_course")
def python_course():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("python_course.html")

@app.route("/courses/python/<module>")
def python_module(module):
    if "username" not in session:
        return redirect(url_for("login"))
    try:
        return render_template(f"python_courses/{module}.html")
    except Exception:
        return render_template("404.html"), 404

@app.route("/java_course")
def java_course():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("java_course.html")

@app.route("/c_course")
def c_course():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("c_course.html")

@app.route("/cpp_course")
def cpp_course():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("cpp_course.html")

# Chat functionality
@app.route('/chat', methods=['POST'])
def chat():
    if "username" not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_message = request.json['message']
        username = session['username']
        is_superuser = session.get('is_superuser', False)
        
        # Track question for analytics
        if not is_superuser:
            track_question(username, user_message)
        
        context = f"""You are an AI assistant for an educational platform. The user is {username}.
        
Available courses: {', '.join(COURSES)}
User type: {'Superuser' if is_superuser else 'Student'}

Please respond in an educational tone about programming and course content.

User: {user_message}
"""
        response = model.generate_content(context)
        formatted_response = format_response(response)
        return jsonify({'response': formatted_response})
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({'response': 'Sorry, I encountered an error.'}), 500

# ==================== ANALYTICS & PROGRESS ROUTES ====================

@app.route('/api/student/progress')
def get_progress():
    """Get student progress data for dashboard"""
    if "username" not in session or session.get("is_superuser"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session["username"]
    progress = get_student_progress(username)
    
    return jsonify(progress)

@app.route('/api/student/update-progress', methods=['POST'])
def update_progress():
    """Update course progress"""
    if "username" not in session or session.get("is_superuser"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session["username"]
    data = request.json
    course = data.get('course')
    percentage = data.get('percentage', 0)
    modules = data.get('modules_completed')
    
    update_course_progress(username, course, percentage, modules)
    
    return jsonify({'status': 'success', 'message': 'Progress updated'})

@app.route('/api/student/ai-insights')
def get_ai_insights_api():
    """Get AI tutor insights"""
    if "username" not in session or session.get("is_superuser"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session["username"]
    insights = get_ai_insights(username)
    
    analytics_data = load_ai_analytics()
    student_data = analytics_data.get(username, {})
    
    return jsonify({
        'insights': insights,
        'total_questions': student_data.get('total_questions', 0),
        'weak_areas': student_data.get('weak_areas', []),
        'topics': student_data.get('topics', {})
    })

@app.route('/api/student/timetable')
def get_timetable_api():
    """Get student timetable"""
    if "username" not in session or session.get("is_superuser"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session["username"]
    timetable = get_student_timetable(username)
    
    return jsonify(timetable)

@app.route('/api/student/performance-data')
def get_performance_data():
    """Get performance data for charts"""
    if "username" not in session or session.get("is_superuser"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session["username"]
    progress = get_student_progress(username)
    assigned_courses = USER_COURSES.get(username, [])
    
    # Prepare chart data
    course_names = list(progress.keys())
    progress_percentages = [progress[course].get('percentage', 0) for course in course_names]
    
    # Create synthetic performance trend data
    trend_labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    trend_data = [
        [20, 30, 40, 50],  # Python
        [15, 25, 35, 40],  # Java
        [10, 20, 30, 35],  # C
        [10, 15, 25, 30]   # C++
    ]
    
    return jsonify({
        'courses': course_names,
        'progress': progress_percentages,
        'modules': [progress[c].get('modules_completed', 0) for c in course_names],
        'total_modules': [progress[c].get('total_modules', 5) for c in course_names],
        'trend_labels': trend_labels,
        'trend_data': trend_data[:len(course_names)]
    })

# ==================== USER-EDITABLE TIMETABLE API ROUTES ====================
@app.route('/api/student/custom-timetable', methods=['GET'])
def get_custom_timetable():
    """Get user's custom timetable entries"""
    if "username" not in session or session.get("is_superuser"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session["username"]
    entries = get_user_timetable_entries(username)
    
    return jsonify({
        'entries': entries,
        'available_courses': USER_COURSES.get(username, []),
        'days': DAYS,
        'time_slots': TIME_SLOTS
    })

@app.route('/api/student/custom-timetable', methods=['POST'])
def add_custom_timetable_entry():
    """Add a new timetable entry"""
    if "username" not in session or session.get("is_superuser"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        username = session["username"]
        
        day = data.get('day')
        course = data.get('course')
        time = data.get('time')
        notes = data.get('notes', '')
        
        # Validate input
        if not all([day, course, time]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if day not in DAYS:
            return jsonify({'error': 'Invalid day'}), 400
        
        if course not in USER_COURSES.get(username, []):
            return jsonify({'error': 'Course not assigned to user'}), 400
        
        if time not in TIME_SLOTS:
            return jsonify({'error': 'Invalid time slot'}), 400
        
        entry = add_timetable_entry(username, day, course, time, notes)
        return jsonify({'success': True, 'entry': entry}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/custom-timetable/<int:entry_id>', methods=['PUT'])
def update_custom_timetable_entry(entry_id):
    """Update a timetable entry"""
    if "username" not in session or session.get("is_superuser"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        username = session["username"]
        
        day = data.get('day')
        course = data.get('course')
        time = data.get('time')
        notes = data.get('notes', '')
        
        # Validate input
        if not all([day, course, time]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if day not in DAYS:
            return jsonify({'error': 'Invalid day'}), 400
        
        if course not in USER_COURSES.get(username, []):
            return jsonify({'error': 'Course not assigned to user'}), 400
        
        if time not in TIME_SLOTS:
            return jsonify({'error': 'Invalid time slot'}), 400
        
        entry = update_timetable_entry(username, entry_id, day, course, time, notes)
        
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        return jsonify({'success': True, 'entry': entry})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/custom-timetable/<int:entry_id>', methods=['DELETE'])
def delete_custom_timetable_entry(entry_id):
    """Delete a timetable entry"""
    if "username" not in session or session.get("is_superuser"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        username = session["username"]
        
        if delete_timetable_entry(username, entry_id):
            return jsonify({'success': True, 'message': 'Entry deleted'})
        else:
            return jsonify({'error': 'Entry not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
