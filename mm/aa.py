from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
import re

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Configuration
UPLOAD_FOLDER = 'uploads'
USER_DATA_FILE = 'users.txt'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xlsx', 'csv', 'ppt', 'pptx', 'mp4', 'avi', 'zip', 'rar'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Gemini AI
genai.configure(api_key='AIzaSyCEiqlCAi8xNchk9Gn-VBJ0o_JvN8MMQoE')
model = genai.GenerativeModel('gemini-2.0-flash')

# Data storage
USER_DATA = {}
SUPERUSER_DATA = {"varshith": "1234"}
COURSES = ["Python", "Java", "C", "C++"]

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_folder(username):
    path = os.path.join(app.config['UPLOAD_FOLDER'], username)
    os.makedirs(path, exist_ok=True)
    return path

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

# Authentication routes
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
    session.clear()
    return redirect(url_for("login"))

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

        return render_template("welcome.html",
                               username=username,
                               files=uploaded_files,
                               superuser_files=superuser_files)
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

# python course landing
@app.route("/courses/python")
def python_course():
    return render_template("python/index.html")

# dynamic module route (serves templates/python/<module>.html)
@app.route("/courses/python/<module>")
def python_module(module):
    # sanitize module name if you want; here we just attempt to render the template
    try:
        return render_template(f"python/{module}.html")
    except Exception:
        # optional: render a 404 template or a generic "module not found" page
        return render_template("404.html"), 404

@app.route("/java")
def java_course():
    return render_template("java/Eduvalt - Master Java Programming.html")

@app.route("/courses/cpp")
def cpp_course():
    return render_template("cpp_course.html")

@app.route("/courses/c")
def c_course():
    return render_template("c_course.html")


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

# Superuser routes
@app.route("/superuser_dashboard")
def superuser_dashboard():
    if "username" in session and session.get("is_superuser"):
        users = list(USER_DATA.keys())
        user_files = {user: os.listdir(get_user_folder(user)) for user in users}
        return render_template("superuser_dashboard.html", users=users, user_files=user_files)
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

# Chat functionality
@app.route('/chat', methods=['POST'])
def chat():
    # Check if user is logged in
    if "username" not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_message = request.json['message']
        username = session['username']
        is_superuser = session.get('is_superuser', False)
        
        # Create context-aware prompt based on user profile
        context = f"""You are an AI assistant for an educational platform. The user is {username}.
        
Available courses: {', '.join(COURSES)}
User type: {'Superuser' if is_superuser else 'Student'}

Please respond to the user's message in a helpful, educational tone. You can:
- Help with programming concepts in {', '.join(COURSES)}
- Explain course materials and assignments
- Provide coding examples and debugging help
- Answer questions about the platform features
- Assist with file management and uploads

User: {user_message}

Guidelines:
- Use **bold** for emphasis and important terms
- Use *italics* for technical concepts
- Format code blocks with markdown ```language\\ncode\\n```
- Be encouraging and supportive for learning
- If asked about courses, mention the available ones: {', '.join(COURSES)}
- Keep responses concise but informative
"""
        
        response = model.generate_content(context)
        formatted_response = format_response(response)
        return jsonify({'response': formatted_response})
        
    except Exception as e:
        print(f"Chat error: {str(e)}")  # Log the error
        return jsonify({'response': 'Sorry, I encountered an error. Please try again or contact support if the issue persists.'}), 500

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)