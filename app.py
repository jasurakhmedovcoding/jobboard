from flask import Flask, render_template, request, redirect, url_for, session, jsonify,flash
from database import get_db, init_db
import bcrypt
from auth import login_required, role_required

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-later'

init_db()

# ─── HOME ────────────────────────────────────────────────
@app.route('/')
def home():
    db = get_db()
    jobs = db.execute('''
        SELECT jobs.*, users.username as poster
        FROM jobs
        JOIN users ON jobs.user_id = users.id
        ORDER BY posted_at DESC
    ''').fetchall()
    db.close()
    return render_template('index.html', jobs=jobs)

# ─── REGISTER ────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        password = request.form['password']
        role     = request.form['role']

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                (username, email, hashed, role)
            )
            db.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return render_template('register.html', error='Username or email already exists')
        finally:
            db.close()

    return render_template('register.html')

# ─── LOGIN ───────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']

        db   = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Wrong email or password')

    return render_template('login.html')

# ─── LOGOUT ──────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ─── POST A JOB ──────────────────────────────────────────
@app.route('/jobs/new', methods=['GET', 'POST'])
def new_job():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session['role'] != 'employer':
        return redirect(url_for('home'))

    if request.method == 'POST':
        db = get_db()
        db.execute('''
            INSERT INTO jobs (user_id, title, company, location, salary, category, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            request.form['title'],
            request.form['company'],
            request.form['location'],
            request.form['salary'],
            request.form['category'],
            request.form['description']
        ))
        db.commit()
        db.close()
        return redirect(url_for('home'))

    return render_template('new_job.html')

# ─── JOB DETAIL ──────────────────────────────────────────
@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    db  = get_db()
    job = db.execute('''
        SELECT jobs.*, users.username as poster
        FROM jobs JOIN users ON jobs.user_id = users.id
        WHERE jobs.id = ?
    ''', (job_id,)).fetchone()
    db.close()

    if not job:
        return 'Job not found', 404

    return render_template('job_detail.html', job=job)

# ─── APPLY ───────────────────────────────────────────────
@app.route('/jobs/<int:job_id>/apply', methods=['POST'])
def apply(job_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    db.execute(
        'INSERT INTO applications (job_id, user_id, cover_letter) VALUES (?, ?, ?)',
        (job_id, session['user_id'], request.form.get('cover_letter', ''))
    )
    db.commit()
    db.close()
    return redirect(url_for('job_detail', job_id=job_id))

# ─── SEARCH ──────────────────────────────────────────────
@app.route('/search')
@app.route('/search')
def search():
    query    = request.args.get('q', '')
    category = request.args.get('category', '')
    remote   = request.args.get('remote', '')

    sql    = 'SELECT * FROM jobs WHERE 1=1'
    params = []

    if query:
        sql += ' AND (title LIKE ? OR company LIKE ? OR description LIKE ?)'
        params += [f'%{query}%', f'%{query}%', f'%{query}%']

    if category:
        sql += ' AND category = ?'
        params.append(category)

    if remote:
        sql += ' AND location LIKE ?'
        params.append('%remote%')

    db   = get_db()
    jobs = db.execute(sql, params).fetchall()
    db.close()

    return render_template('index.html', jobs=jobs, query=query, remote=remote)


@app.route('/jobs/new', methods=['GET', 'POST'])
@role_required('employer')
def new_job():
    if request.method == 'POST':
        db = get_db()
        db.execute('''
            INSERT INTO jobs (user_id, title, company, location, salary, category, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            request.form['title'],
            request.form['company'],
            request.form['location'],
            request.form['salary'],
            request.form['category'],
            request.form['description']
        ))
        db.commit()
        db.close()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('new_job.html')

@app.route('/jobs/<int:job_id>/apply', methods=['POST'])
@login_required
def apply(job_id):
    db = get_db()
    db.execute(
        'INSERT INTO applications (job_id, user_id, cover_letter) VALUES (?, ?, ?)',
        (job_id, session['user_id'], request.form.get('cover_letter', ''))
    )
    db.commit()
    db.close()
    flash('Application submitted!', 'success')
    return redirect(url_for('job_detail', job_id=job_id))

if __name__ == '__main__':
    app.run(debug=True)