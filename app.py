from flask import Flask, render_template, request, redirect, session, send_file, url_for
from flask_session import Session
import os
import sqlite3
from xhtml2pdf import pisa

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

DB_PATH = 'resumes.db'
ADMIN_USER = 'admin'
ADMIN_PASS = 'admin123'

# ------------------ INIT DB ------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, email TEXT, skills TEXT, ai_skills TEXT,
                    experience TEXT, education TEXT, user TEXT, template TEXT
                )''')
    conn.commit()
    conn.close()

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return render_template('popup.html', message="You're already logged in!")
    if request.method == 'POST':
        session['user'] = request.form['email']
        return redirect('/')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return render_template('popup.html', message="You're already logged in!")
    if request.method == 'POST':
        session['user'] = request.form['email']
        return redirect('/')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/set_theme', methods=['POST'])
def set_theme():
    session['theme'] = request.form['theme']
    return redirect(request.referrer or '/')
@app.route('/select-template')
def select_template():
    templates = [
        {"name": "Classic", "image": "https://via.placeholder.com/250x320?text=Classic", "slug": "classic"},
        {"name": "Modern", "image": "https://via.placeholder.com/250x320?text=Modern", "slug": "modern"},
        {"name": "Essential", "image": "https://via.placeholder.com/250x320?text=Essential", "slug": "essential"},
        {"name": "Confetti", "image": "https://via.placeholder.com/250x320?text=Confetti", "slug": "confetti"},
    ]
    return render_template("select_template.html", templates=templates)

@app.route('/choose-template')
def choose_template():
    templates = [
        {
            "name": "Classic",
            "image": "https://i.imgur.com/JP52fdG.png"
        },
        {
            "name": "Modern",
            "image": "https://i.imgur.com/k7J9FZP.png"
        },
        {
            "name": "Creative",
            "image": "https://i.imgur.com/MKxQ7tU.png"
        }
    ]
    return render_template('select_template.html', templates=templates)


@app.route('/select-template/<template_name>')
def use_template(template_name):
    # Store the selected template name in session
    session['selected_template'] = template_name
    return redirect('/create')


@app.route('/create/<template>', methods=['GET', 'POST'])
def create_with_template(template):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        skills = request.form['skills']
        experience = request.form['experience']
        education = request.form['education']

        ai_skills = ''
        if "python" in skills.lower():
            ai_skills += "Data Structures, OOP, Flask\n"
        if "html" in skills.lower():
            ai_skills += "CSS, JS, Responsive Design\n"
        if "sql" in skills.lower():
            ai_skills += "DBMS, Joins, Normalization\n"

        user = session.get('user', 'guest')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO resumes (name, email, skills, ai_skills, experience, education, user, template) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (name, email, skills, ai_skills, experience, education, user, template))
        conn.commit()
        conn.close()

        return render_template('preview.html', name=name, email=email, skills=skills,
                               ai_skills=ai_skills, experience=experience, education=education, template=template)

    return render_template('create_resume.html', template=template)

@app.route('/download', methods=['POST'])
def download():
    name = request.form['name']
    email = request.form['email']
    skills = request.form['skills']
    ai_skills = request.form['ai_skills']
    experience = request.form['experience']
    education = request.form['education']
    template = request.form.get('template', 'classic')

    html = render_template('pdf_template.html', name=name, email=email, skills=skills,
                           ai_skills=ai_skills, experience=experience,
                           education=education, template=template)

    pdf_path = "resume.pdf"
    with open(pdf_path, "w+b") as result_file:
        pisa.CreatePDF(html, dest=result_file)

    return send_file(pdf_path, as_attachment=True)

@app.route('/optimize', methods=['GET', 'POST'])
def optimize_resume():
    if request.method == 'POST':
        skills = request.form['skills']
        experience = request.form['experience']

        suggestions = []
        if "web" in experience.lower() or "html" in skills.lower():
            suggestions += ["Add JavaScript projects", "Learn React or Vue.js"]
        if "python" in skills.lower():
            suggestions += ["Build a data analysis project using Pandas", "Practice LeetCode problems"]
        if "sql" in skills.lower():
            suggestions += ["Include DBMS coursework", "Try designing a normalized schema"]
        if not skills.strip():
            suggestions += ["Add technical skills (e.g. Python, HTML, SQL)"]
        if not experience.strip():
            suggestions += ["Mention internships, personal or academic projects"]

        return render_template('optimize_result.html', skills=skills,
                               experience=experience, suggestions=suggestions)

    return render_template('optimize.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USER and password == ADMIN_PASS:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM resumes")
            resumes = c.fetchall()
            conn.close()
            return render_template('admin.html', resumes=resumes)
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

if __name__ == '__main__':
    init_db()
    import os

    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

