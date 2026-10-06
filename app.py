import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cims.db')

app = Flask(__name__)
app.secret_key = 'cims_shri_shivaji_science_college_secret_key_2026'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'principal', 'faculty')),
        status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT UNIQUE NOT NULL,
        icon TEXT DEFAULT 'bi-box-seam',
        description TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        department TEXT NOT NULL,
        physical_quantity INTEGER NOT NULL DEFAULT 0,
        reserved_quantity INTEGER NOT NULL DEFAULT 0,
        minimum_quantity INTEGER NOT NULL DEFAULT 5,
        unit TEXT NOT NULL DEFAULT 'Units',
        location TEXT DEFAULT 'Central Store / Dept Lab',
        description TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracking_code TEXT UNIQUE NOT NULL,
        requester_type TEXT NOT NULL CHECK(requester_type IN ('student', 'faculty')),
        requester_name TEXT NOT NULL,
        requester_email TEXT NOT NULL,
        requester_id_num TEXT,
        department TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        requested_quantity INTEGER NOT NULL,
        purpose TEXT NOT NULL,
        urgency TEXT DEFAULT 'Normal' CHECK(urgency IN ('Low', 'Normal', 'High', 'Critical')),
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'declined', 'completed', 'withdrawn')),
        rejection_reason TEXT,
        reviewed_by TEXT,
        reviewed_at TIMESTAMP,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES inventory_items (item_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        transaction_type TEXT NOT NULL CHECK(transaction_type IN ('stock_in', 'reservation', 'release', 'withdrawal', 'adjustment')),
        quantity INTEGER NOT NULL,
        performed_by TEXT NOT NULL,
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES inventory_items (item_id)
    )
    """)

    # Populate seed data if users table is empty
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    if cursor.fetchone()['cnt'] == 0:
        # Default users (password: admin123, principal123, faculty123)
        users = [
            ('Administrator', 'admin@shivajisc.org', 'Central Administration', generate_password_hash('admin123'), 'admin', 'active'),
            ('Dr. G. V. Korpe (Principal)', 'principal@shivajisc.org', 'Office of the Principal', generate_password_hash('principal123'), 'principal', 'active'),
            ('Prof. Yash Kale (HOD CS)', 'faculty@shivajisc.org', 'Computer Science & Data Analytics', generate_password_hash('faculty123'), 'faculty', 'active'),
            ('Dr. A. B. Deshmukh', 'chemistry.faculty@shivajisc.org', 'Chemistry', generate_password_hash('faculty123'), 'faculty', 'active'),
            ('Prof. S. R. Ujjainkar', 'physics.faculty@shivajisc.org', 'Physics', generate_password_hash('faculty123'), 'faculty', 'active')
        ]
        cursor.executemany("""
            INSERT INTO users (name, email, department, password_hash, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, users)

        # Seed categories
        categories = [
            ('Laboratory Equipment', 'bi-radioactive', 'Glassware, microscopes, chemicals, test tubes & sensor kits'),
            ('Computer Science & IT', 'bi-cpu', 'Desktop components, cables, networking gear, IoT kits & peripherals'),
            ('Stationery & Printing', 'bi-journal-bookmark', 'Registers, printer paper, toner cartridges, markers & markers'),
            ('Sports & Physical Edu', 'bi-trophy', 'Cricket sets, badminton rackets, footballs & sports accessories'),
            ('Classroom & AV Aids', 'bi-projector', 'Projectors, pointer pens, HDMI adapters, projection screens')
        ]
        cursor.executemany("""
            INSERT INTO categories (category_name, icon, description)
            VALUES (?, ?, ?)
        """, categories)

        # Seed items
        items = [
            ('Compound Optical Microscope (1000x)', 1, 'Microbiology & Botany', 18, 2, 5, 'Pieces', 'Biology Lab-2', 'High-magnification binocular optical microscope'),
            ('Digital Multimeter Fluke 101', 2, 'Physics', 25, 3, 6, 'Units', 'Electronics Lab A', 'Pocket digital multimeter for electronic circuits'),
            ('Arduino UNO R3 & Sensor Kit', 2, 'Computer Science & Data Analytics', 40, 5, 8, 'Kits', 'IoT Lab 304', 'Microcontroller development boards with breadboards & sensors'),
            ('Raspberry Pi 4 Model B (4GB)', 2, 'Computer Science & Data Analytics', 15, 0, 4, 'Units', 'Research Lab 102', 'Mini computing modules for practical data analytics'),
            ('Conical Flask 250ml (Borosil)', 1, 'Chemistry', 120, 10, 20, 'Pieces', 'Chemical Store Rm 12', 'Heat-resistant borosilicate laboratory flasks'),
            ('A4 Copier Paper (75 GSM Rim)', 3, 'Central Administration', 50, 4, 15, 'Reams', 'Store Room B', 'High quality multipurpose printing & exam paper'),
            ('Whiteboard Markers (Pack of 4)', 3, 'Central Administration', 60, 2, 12, 'Packs', 'Stationery Vault', 'Black, Blue, Red, Green dry-erase marker sets'),
            ('HDMI to VGA / Type-C Display Dongle', 5, 'Computer Science & Data Analytics', 12, 1, 3, 'Pieces', 'Smart Class Rm 3', 'Essential converters for seminars and AV projection'),
            ('Epson 4K Laser Projector Unit', 5, 'Seminar Hall', 6, 1, 2, 'Units', 'Auditorium AV Rack', 'Ceiling mount capable high brightness seminar projector'),
            ('Yonex Badminton Rackets (Carbon)', 4, 'Sports & Physical Edu', 16, 2, 4, 'Pairs', 'Gymkhana Locker 4', 'Professional badminton racquets for collegiate tournaments')
        ]
        cursor.executemany("""
            INSERT INTO inventory_items (item_name, category_id, department, physical_quantity, reserved_quantity, minimum_quantity, unit, location, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, items)

        # Seed sample requests
        sample_requests = [
            ('SSC-REQ-701', 'student', 'Athar Khan (Final Year B.Sc CS)', 'athar.cs@shivajisc.org', 'STU-2023-CS-042', 'Computer Science & Data Analytics', 3, 2, 'Final Year Capstone IoT Weather Station Project practical demonstration', 'High', 'approved', None, 'Dr. G. V. Korpe (Principal)', '2026-10-05 11:30:00', None),
            ('SSC-REQ-702', 'faculty', 'Dr. A. B. Deshmukh', 'chemistry.faculty@shivajisc.org', 'FAC-CHEM-108', 'Chemistry', 5, 10, 'Preparatory organic chemistry titration practicals for semester 5 batch', 'Normal', 'completed', None, 'Dr. G. V. Korpe (Principal)', '2026-10-04 10:15:00', '2026-10-05 14:00:00'),
            ('SSC-REQ-703', 'student', 'Shravani Ujjainkar', 'shravani.u@shivajisc.org', 'STU-2024-PHY-019', 'Physics', 2, 1, 'Measurement of circuit frequency characteristics in semester practical lab', 'Normal', 'pending', None, None, None, None),
            ('SSC-REQ-704', 'student', 'Gayatri Kathale', 'gayatri.k@shivajisc.org', 'STU-2023-DS-088', 'Computer Science & Data Analytics', 4, 3, 'Cluster edge computing setup for data science semester seminar', 'High', 'declined', 'Insufficient stock for non-lab individual issuance. Please use central research lab setup.', 'Dr. G. V. Korpe (Principal)', '2026-10-06 09:20:00', None)
        ]
        cursor.executemany("""
            INSERT INTO requests (tracking_code, requester_type, requester_name, requester_email, requester_id_num, department, item_id, requested_quantity, purpose, urgency, status, rejection_reason, reviewed_by, reviewed_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_requests)

        # Transactions
        transactions = [
            (3, 'stock_in', 40, 'Administrator', 'Initial stock induction for session 2025-2026'),
            (3, 'reservation', 2, 'Dr. G. V. Korpe (Principal)', 'Approved request SSC-REQ-701'),
            (5, 'stock_in', 120, 'Administrator', 'Central chemistry glassware replenishment'),
            (5, 'reservation', 10, 'Dr. G. V. Korpe (Principal)', 'Approved request SSC-REQ-702'),
            (5, 'withdrawal', 10, 'Prof. Yash Kale (HOD CS)', 'Physical collection confirmed for SSC-REQ-702')
        ]
        cursor.executemany("""
            INSERT INTO inventory_transactions (item_id, transaction_type, quantity, performed_by, remarks)
            VALUES (?, ?, ?, ?, ?)
        """, transactions)

    db.commit()
    db.close()

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in with your credentials to access this portal section.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in with your credentials.', 'warning')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Access restricted: You do not possess authorized privileges for that action.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- PUBLIC ROUTES ---
@app.route('/')
def home():
    db = get_db()
    # Stats for showcase
    stats = {}
    stats['total_items'] = db.execute("SELECT COUNT(*) FROM inventory_items").fetchone()[0]
    stats['total_categories'] = db.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    stats['total_requests'] = db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    stats['completed_requests'] = db.execute("SELECT COUNT(*) FROM requests WHERE status IN ('completed', 'withdrawn')").fetchone()[0]
    
    # Active categories with item count
    categories = db.execute("""
        SELECT c.*, COUNT(i.item_id) as item_count 
        FROM categories c 
        LEFT JOIN inventory_items i ON c.category_id = i.category_id 
        GROUP BY c.category_id
    """).fetchall()

    # Featured inventory items
    items = db.execute("""
        SELECT i.*, c.category_name, (i.physical_quantity - i.reserved_quantity) AS available_quantity
        FROM inventory_items i
        JOIN categories c ON i.category_id = c.category_id
        ORDER BY i.item_id DESC
        LIMIT 6
    """).fetchall()

    return render_template('home.html', stats=stats, categories=categories, items=items)

@app.route('/catalog')
def catalog():
    db = get_db()
    category_id = request.args.get('category_id', type=int)
    search_q = request.args.get('q', '').strip()
    dept = request.args.get('department', '').strip()

    sql = """
        SELECT i.*, c.category_name, (i.physical_quantity - i.reserved_quantity) AS available_quantity
        FROM inventory_items i
        JOIN categories c ON i.category_id = c.category_id
        WHERE 1=1
    """
    params = []

    if category_id:
        sql += " AND i.category_id = ?"
        params.append(category_id)
    if search_q:
        sql += " AND (i.item_name LIKE ? OR i.description LIKE ?)"
        params.append(f"%{search_q}%")
        params.append(f"%{search_q}%")
    if dept:
        sql += " AND i.department = ?"
        params.append(dept)

    sql += " ORDER BY i.item_name ASC"
    items = db.execute(sql, params).fetchall()
    categories = db.execute("SELECT * FROM categories ORDER BY category_name").fetchall()
    departments = [
        'Computer Science & Data Analytics',
        'Physics',
        'Chemistry',
        'Microbiology & Botany',
        'Zoology & Environmental Science',
        'Mathematics & Statistics',
        'Sports & Physical Edu',
        'Central Administration',
        'Seminar Hall & AV'
    ]

    return render_template('catalog.html', items=items, categories=categories, departments=departments, selected_cat=category_id, search_q=search_q, selected_dept=dept)

@app.route('/request-goods', methods=['GET', 'POST'])
def request_goods():
    db = get_db()
    if request.method == 'POST':
        requester_type = request.form.get('requester_type')
        requester_name = request.form.get('requester_name', '').strip()
        requester_email = request.form.get('requester_email', '').strip()
        requester_id_num = request.form.get('requester_id_num', '').strip()
        department = request.form.get('department')
        item_id = request.form.get('item_id', type=int)
        requested_quantity = request.form.get('requested_quantity', type=int)
        purpose = request.form.get('purpose', '').strip()
        urgency = request.form.get('urgency', 'Normal')

        # Validations
        if not (requester_name and requester_email and department and item_id and requested_quantity and purpose):
            flash('Please fill in all mandatory fields.', 'danger')
            return redirect(url_for('request_goods', item_id=item_id))

        if requested_quantity <= 0:
            flash('Requested quantity must be at least 1.', 'danger')
            return redirect(url_for('request_goods', item_id=item_id))

        item = db.execute("""
            SELECT *, (physical_quantity - reserved_quantity) AS available_quantity 
            FROM inventory_items WHERE item_id = ?
        """, (item_id,)).fetchone()

        if not item:
            flash('Selected product does not exist.', 'danger')
            return redirect(url_for('catalog'))

        # Generate unique tracking code
        timestamp_part = datetime.now().strftime('%m%d')
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM requests")
        next_num = cursor.fetchone()[0] + 101
        tracking_code = f"SSC-{timestamp_part}-{next_num}"

        cursor.execute("""
            INSERT INTO requests (tracking_code, requester_type, requester_name, requester_email, requester_id_num, department, item_id, requested_quantity, purpose, urgency, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (tracking_code, requester_type, requester_name, requester_email, requester_id_num, department, item_id, requested_quantity, purpose, urgency))
        db.commit()

        flash(f'Requisition submitted successfully! Your tracking code is {tracking_code}. You can monitor its progress anytime without logging in.', 'success')
        return redirect(url_for('track', code=tracking_code))

    # GET
    preselected_item_id = request.args.get('item_id', type=int)
    items = db.execute("""
        SELECT i.*, c.category_name, (i.physical_quantity - i.reserved_quantity) AS available_quantity
        FROM inventory_items i
        JOIN categories c ON i.category_id = c.category_id
        ORDER BY i.item_name ASC
    """).fetchall()
    departments = [
        'Computer Science & Data Analytics',
        'Physics',
        'Chemistry',
        'Microbiology & Botany',
        'Zoology & Environmental Science',
        'Mathematics & Statistics',
        'Sports & Physical Edu',
        'Central Administration',
        'Seminar Hall & AV'
    ]
    return render_template('request_goods.html', items=items, departments=departments, preselected_item_id=preselected_item_id)

@app.route('/track')
def track():
    code = request.args.get('code', '').strip().upper()
    req_data = None
    item_data = None
    if code:
        db = get_db()
        req_data = db.execute("""
            SELECT r.*, i.item_name, i.unit, i.physical_quantity, i.reserved_quantity, (i.physical_quantity - i.reserved_quantity) as available_quantity, c.category_name
            FROM requests r
            JOIN inventory_items i ON r.item_id = i.item_id
            JOIN categories c ON i.category_id = c.category_id
            WHERE UPPER(r.tracking_code) = ?
        """, (code,)).fetchone()
        if not req_data:
            flash(f'No request found with tracking code "{code}". Please verify your reference number.', 'warning')

    return render_template('track.html', code=code, req=req_data)

# --- AUTHENTICATION ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            if user['status'] != 'active':
                flash('Your account has been deactivated. Please contact the administrator.', 'danger')
                return render_template('login.html')

            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = user['role']
            session['department'] = user['department']
            flash(f'Welcome back, {user["name"]}! Successfully authenticated.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email credentials or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been securely signed out.', 'info')
    return redirect(url_for('login'))

# --- PORTAL / DASHBOARDS ---
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    role = session['role']

    # Common metrics
    total_items = db.execute("SELECT COUNT(*) FROM inventory_items").fetchone()[0]
    low_stock_items = db.execute("SELECT COUNT(*) FROM inventory_items WHERE (physical_quantity - reserved_quantity) <= minimum_quantity").fetchone()[0]
    pending_requests = db.execute("SELECT COUNT(*) FROM requests WHERE status = 'pending'").fetchone()[0]
    approved_requests = db.execute("SELECT COUNT(*) FROM requests WHERE status = 'approved'").fetchone()[0]
    completed_requests = db.execute("SELECT COUNT(*) FROM requests WHERE status IN ('completed', 'withdrawn')").fetchone()[0]
    declined_requests = db.execute("SELECT COUNT(*) FROM requests WHERE status = 'declined'").fetchone()[0]

    # Department filter or recents
    recent_requests = db.execute("""
        SELECT r.*, i.item_name, c.category_name, (i.physical_quantity - i.reserved_quantity) AS available_quantity
        FROM requests r
        JOIN inventory_items i ON r.item_id = i.item_id
        JOIN categories c ON i.category_id = c.category_id
        ORDER BY r.request_id DESC
        LIMIT 8
    """).fetchall()

    low_stock_list = db.execute("""
        SELECT i.*, c.category_name, (i.physical_quantity - i.reserved_quantity) AS available_quantity
        FROM inventory_items i
        JOIN categories c ON i.category_id = c.category_id
        WHERE (i.physical_quantity - i.reserved_quantity) <= i.minimum_quantity
        ORDER BY available_quantity ASC
        LIMIT 5
    """).fetchall()

    recent_transactions = db.execute("""
        SELECT t.*, i.item_name
        FROM inventory_transactions t
        JOIN inventory_items i ON t.item_id = i.item_id
        ORDER BY t.transaction_id DESC
        LIMIT 6
    """).fetchall()

    return render_template(
        'dashboard.html',
        total_items=total_items,
        low_stock_items=low_stock_items,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        completed_requests=completed_requests,
        declined_requests=declined_requests,
        recent_requests=recent_requests,
        low_stock_list=low_stock_list,
        recent_transactions=recent_transactions
    )

# --- REQUEST MANAGEMENT (Faculty / Principal / Admin) ---
@app.route('/requests')
@login_required
def manage_requests():
    db = get_db()
    status_filter = request.args.get('status', 'all')
    dept_filter = request.args.get('department', 'all')
    type_filter = request.args.get('type', 'all')
    search_q = request.args.get('q', '').strip()

    sql = """
        SELECT r.*, i.item_name, i.physical_quantity, i.reserved_quantity, 
               (i.physical_quantity - i.reserved_quantity) AS available_quantity,
               i.unit, c.category_name
        FROM requests r
        JOIN inventory_items i ON r.item_id = i.item_id
        JOIN categories c ON i.category_id = c.category_id
        WHERE 1=1
    """
    params = []

    if status_filter != 'all':
        sql += " AND r.status = ?"
        params.append(status_filter)
    if dept_filter != 'all':
        sql += " AND r.department = ?"
        params.append(dept_filter)
    if type_filter != 'all':
        sql += " AND r.requester_type = ?"
        params.append(type_filter)
    if search_q:
        sql += " AND (r.tracking_code LIKE ? OR r.requester_name LIKE ? OR i.item_name LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"])

    sql += " ORDER BY CASE r.status WHEN 'pending' THEN 1 WHEN 'approved' THEN 2 WHEN 'completed' THEN 3 ELSE 4 END, r.request_id DESC"
    requests_list = db.execute(sql, params).fetchall()

    departments = [
        'Computer Science & Data Analytics',
        'Physics',
        'Chemistry',
        'Microbiology & Botany',
        'Zoology & Environmental Science',
        'Mathematics & Statistics',
        'Sports & Physical Edu',
        'Central Administration',
        'Seminar Hall & AV'
    ]

    return render_template(
        'requests.html',
        requests_list=requests_list,
        status_filter=status_filter,
        dept_filter=dept_filter,
        type_filter=type_filter,
        search_q=search_q,
        departments=departments
    )

# Workflow Action: Approve Request (Principal or Authorized Faculty/Admin)
@app.route('/requests/<int:req_id>/approve', methods=['POST'])
@login_required
def approve_request(req_id):
    db = get_db()
    req = db.execute("SELECT * FROM requests WHERE request_id = ?", (req_id,)).fetchone()
    if not req:
        flash('Request not found.', 'danger')
        return redirect(url_for('manage_requests'))

    if req['status'] != 'pending':
        flash(f'Cannot approve request currently in "{req["status"]}" status.', 'warning')
        return redirect(url_for('manage_requests'))

    # Check stock availability
    item = db.execute("""
        SELECT *, (physical_quantity - reserved_quantity) as available_quantity 
        FROM inventory_items WHERE item_id = ?
    """, (req['item_id'],)).fetchone()

    if item['available_quantity'] < req['requested_quantity']:
        flash(f'Insufficient available stock! Available: {item["available_quantity"]} {item["unit"]}, Requested: {req["requested_quantity"]} {item["unit"]}. Stock reservation prevented.', 'danger')
        return redirect(url_for('manage_requests'))

    reviewer_title = f"{session['user_name']} ({session['role'].capitalize()})"
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Atomic stock reservation: increase reserved_quantity
    cursor = db.cursor()
    cursor.execute("""
        UPDATE inventory_items 
        SET reserved_quantity = reserved_quantity + ?
        WHERE item_id = ?
    """, (req['requested_quantity'], req['item_id']))

    # Update request state to 'approved'
    cursor.execute("""
        UPDATE requests
        SET status = 'approved',
            reviewed_by = ?,
            reviewed_at = ?,
            rejection_reason = NULL
        WHERE request_id = ?
    """, (reviewer_title, now_str, req_id))

    # Audit transaction
    cursor.execute("""
        INSERT INTO inventory_transactions (item_id, transaction_type, quantity, performed_by, remarks)
        VALUES (?, 'reservation', ?, ?, ?)
    """, (req['item_id'], req['requested_quantity'], reviewer_title, f"Reserved for approved requisition {req['tracking_code']} ({req['requester_name']})"))

    db.commit()
    flash(f'Requisition {req["tracking_code"]} has been APPROVED. Stock reserved safely.', 'success')
    return redirect(url_for('manage_requests'))

# Workflow Action: Decline Request (with mandatory justification)
@app.route('/requests/<int:req_id>/decline', methods=['POST'])
@login_required
def decline_request(req_id):
    db = get_db()
    reason = request.form.get('rejection_reason', '').strip()
    if not reason:
        flash('A mandatory justification/reason must be provided when declining a request.', 'danger')
        return redirect(url_for('manage_requests'))

    req = db.execute("SELECT * FROM requests WHERE request_id = ?", (req_id,)).fetchone()
    if not req:
        flash('Request not found.', 'danger')
        return redirect(url_for('manage_requests'))

    reviewer_title = f"{session['user_name']} ({session['role'].capitalize()})"
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = db.cursor()
    # If it was previously approved and now declined, release the reserved stock!
    if req['status'] == 'approved':
        cursor.execute("""
            UPDATE inventory_items 
            SET reserved_quantity = MAX(0, reserved_quantity - ?)
            WHERE item_id = ?
        """, (req['requested_quantity'], req['item_id']))

        cursor.execute("""
            INSERT INTO inventory_transactions (item_id, transaction_type, quantity, performed_by, remarks)
            VALUES (?, 'release', ?, ?, ?)
        """, (req['item_id'], req['requested_quantity'], reviewer_title, f"Released reservation due to revocation/decline of {req['tracking_code']}"))

    cursor.execute("""
        UPDATE requests
        SET status = 'declined',
            rejection_reason = ?,
            reviewed_by = ?,
            reviewed_at = ?
        WHERE request_id = ?
    """, (reason, reviewer_title, now_str, req_id))

    db.commit()
    flash(f'Requisition {req["tracking_code"]} has been DECLINED with provided remarks.', 'warning')
    return redirect(url_for('manage_requests'))

# Workflow Action: Complete / Withdraw (Physical goods handover)
@app.route('/requests/<int:req_id>/complete', methods=['POST'])
@login_required
def complete_request(req_id):
    db = get_db()
    req = db.execute("SELECT * FROM requests WHERE request_id = ?", (req_id,)).fetchone()
    if not req:
        flash('Request not found.', 'danger')
        return redirect(url_for('manage_requests'))

    if req['status'] != 'approved':
        flash('Only Approved requests can be marked as Completed/Withdrawn upon handover.', 'warning')
        return redirect(url_for('manage_requests'))

    actor_title = f"{session['user_name']} ({session['role'].capitalize()})"
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = db.cursor()
    # Atomic execution: physical stock decreases AND reserved stock decreases
    cursor.execute("""
        UPDATE inventory_items 
        SET physical_quantity = MAX(0, physical_quantity - ?),
            reserved_quantity = MAX(0, reserved_quantity - ?)
        WHERE item_id = ?
    """, (req['requested_quantity'], req['requested_quantity'], req['item_id']))

    cursor.execute("""
        UPDATE requests
        SET status = 'completed',
            completed_at = ?
        WHERE request_id = ?
    """, (now_str, req_id))

    cursor.execute("""
        INSERT INTO inventory_transactions (item_id, transaction_type, quantity, performed_by, remarks)
        VALUES (?, 'withdrawal', ?, ?, ?)
    """, (req['item_id'], req['requested_quantity'], actor_title, f"Physical handover fulfilled for request {req['tracking_code']} to {req['requester_name']}"))

    db.commit()
    flash(f'Requisition {req["tracking_code"]} completed. Inventory stock successfully deducted and recorded in audit log.', 'success')
    return redirect(url_for('manage_requests'))

# --- INVENTORY MANAGEMENT (Admin & Faculty view/manage) ---
@app.route('/inventory')
@login_required
def manage_inventory():
    db = get_db()
    search_q = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)

    sql = """
        SELECT i.*, c.category_name, (i.physical_quantity - i.reserved_quantity) AS available_quantity
        FROM inventory_items i
        JOIN categories c ON i.category_id = c.category_id
        WHERE 1=1
    """
    params = []
    if search_q:
        sql += " AND (i.item_name LIKE ? OR i.department LIKE ? OR i.location LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"])
    if category_id:
        sql += " AND i.category_id = ?"
        params.append(category_id)

    sql += " ORDER BY i.item_id DESC"
    items = db.execute(sql, params).fetchall()
    categories = db.execute("SELECT * FROM categories ORDER BY category_name").fetchall()

    departments = [
        'Computer Science & Data Analytics',
        'Physics',
        'Chemistry',
        'Microbiology & Botany',
        'Zoology & Environmental Science',
        'Mathematics & Statistics',
        'Sports & Physical Edu',
        'Central Administration',
        'Seminar Hall & AV'
    ]

    return render_template('inventory.html', items=items, categories=categories, departments=departments, search_q=search_q, selected_cat=category_id)

# Add New Item (Admin only or Faculty)
@app.route('/inventory/add', methods=['POST'])
@login_required
def add_item():
    if session['role'] not in ['admin', 'faculty']:
        flash('Only Administrators and Department Faculty are authorized to register stock items.', 'danger')
        return redirect(url_for('manage_inventory'))

    name = request.form.get('item_name', '').strip()
    category_id = request.form.get('category_id', type=int)
    department = request.form.get('department')
    physical_quantity = request.form.get('physical_quantity', type=int, default=0)
    minimum_quantity = request.form.get('minimum_quantity', type=int, default=5)
    unit = request.form.get('unit', 'Units').strip()
    location = request.form.get('location', 'Central Store').strip()
    description = request.form.get('description', '').strip()

    if not (name and category_id and department):
        flash('Item name, category, and department are mandatory.', 'danger')
        return redirect(url_for('manage_inventory'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO inventory_items (item_name, category_id, department, physical_quantity, reserved_quantity, minimum_quantity, unit, location, description)
        VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)
    """, (name, category_id, department, physical_quantity, minimum_quantity, unit, location, description))
    new_item_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO inventory_transactions (item_id, transaction_type, quantity, performed_by, remarks)
        VALUES (?, 'stock_in', ?, ?, ?)
    """, (new_item_id, physical_quantity, f"{session['user_name']} ({session['role']})", "Initial item registration"))

    db.commit()
    flash(f'New asset "{name}" successfully registered into inventory catalog.', 'success')
    return redirect(url_for('manage_inventory'))

# Replenish Stock / Stock-In
@app.route('/inventory/<int:item_id>/replenish', methods=['POST'])
@login_required
def replenish_stock(item_id):
    if session['role'] not in ['admin', 'faculty']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('manage_inventory'))

    added_qty = request.form.get('added_quantity', type=int)
    remarks = request.form.get('remarks', 'Stock replenishment').strip()

    if not added_qty or added_qty <= 0:
        flash('Please enter a valid positive quantity to add.', 'danger')
        return redirect(url_for('manage_inventory'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE inventory_items
        SET physical_quantity = physical_quantity + ?,
            last_updated = CURRENT_TIMESTAMP
        WHERE item_id = ?
    """, (added_qty, item_id))

    cursor.execute("""
        INSERT INTO inventory_transactions (item_id, transaction_type, quantity, performed_by, remarks)
        VALUES (?, 'stock_in', ?, ?, ?)
    """, (item_id, added_qty, f"{session['user_name']} ({session['role']})", remarks))

    db.commit()
    flash(f'Successfully replenished +{added_qty} units into stock.', 'success')
    return redirect(url_for('manage_inventory'))

# Edit / Update Item
@app.route('/inventory/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_item(item_id):
    if session['role'] not in ['admin', 'faculty']:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('manage_inventory'))

    name = request.form.get('item_name', '').strip()
    min_qty = request.form.get('minimum_quantity', type=int, default=5)
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()

    db = get_db()
    db.execute("""
        UPDATE inventory_items
        SET item_name = ?, minimum_quantity = ?, location = ?, description = ?, last_updated = CURRENT_TIMESTAMP
        WHERE item_id = ?
    """, (name, min_qty, location, description, item_id))
    db.commit()

    flash('Item details updated.', 'success')
    return redirect(url_for('manage_inventory'))

# --- AUDIT TRAIL & LOGS ---
@app.route('/audit-logs')
@login_required
def audit_logs():
    db = get_db()
    transactions = db.execute("""
        SELECT t.*, i.item_name, c.category_name, i.unit
        FROM inventory_transactions t
        JOIN inventory_items i ON t.item_id = i.item_id
        JOIN categories c ON i.category_id = c.category_id
        ORDER BY t.transaction_id DESC
        LIMIT 100
    """).fetchall()

    return render_template('audit_logs.html', transactions=transactions)

# --- USERS MANAGEMENT (Admin only) ---
@app.route('/users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_users():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        department = request.form.get('department', '').strip()
        role = request.form.get('role', 'faculty')
        password = request.form.get('password', 'faculty123')

        if not (name and email and department and password):
            flash('All user fields are required.', 'danger')
            return redirect(url_for('manage_users'))

        try:
            db.execute("""
                INSERT INTO users (name, email, department, password_hash, role, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (name, email, department, generate_password_hash(password), role))
            db.commit()
            flash(f'Account created for {name} ({role.capitalize()}).', 'success')
        except sqlite3.IntegrityError:
            flash(f'Error: A user with email {email} already exists.', 'danger')

        return redirect(url_for('manage_users'))

    users = db.execute("SELECT * FROM users ORDER BY user_id ASC").fetchall()
    departments = [
        'Central Administration',
        'Office of the Principal',
        'Computer Science & Data Analytics',
        'Physics',
        'Chemistry',
        'Microbiology & Botany',
        'Zoology & Environmental Science',
        'Mathematics & Statistics',
        'Sports & Physical Edu'
    ]
    return render_template('users.html', users=users, departments=departments)

@app.route('/users/<int:u_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user_status(u_id):
    if u_id == session['user_id']:
        flash('You cannot deactivate your own administrative account.', 'warning')
        return redirect(url_for('manage_users'))

    db = get_db()
    u = db.execute("SELECT status FROM users WHERE user_id = ?", (u_id,)).fetchone()
    if u:
        new_status = 'inactive' if u['status'] == 'active' else 'active'
        db.execute("UPDATE users SET status = ? WHERE user_id = ?", (new_status, u_id))
        db.commit()
        flash(f'User status transitioned to {new_status}.', 'info')
    return redirect(url_for('manage_users'))

# Quick Live API Search for Frontend
@app.route('/api/search-items')
def api_search_items():
    query = request.args.get('q', '').strip()
    db = get_db()
    if query:
        items = db.execute("""
            SELECT i.item_id, i.item_name, i.department, i.unit,
                   (i.physical_quantity - i.reserved_quantity) AS available_quantity
            FROM inventory_items i
            WHERE i.item_name LIKE ? OR i.department LIKE ?
            LIMIT 10
        """, (f"%{query}%", f"%{query}%")).fetchall()
    else:
        items = db.execute("""
            SELECT i.item_id, i.item_name, i.department, i.unit,
                   (i.physical_quantity - i.reserved_quantity) AS available_quantity
            FROM inventory_items i
            LIMIT 10
        """).fetchall()

    return jsonify([dict(x) for x in items])

if __name__ == '__main__':
    init_db()
    print("Starting Shri Shivaji Science College Inventory Management Server on http://127.0.0.1:5000 ...")
    app.run(debug=True, host='127.0.0.1', port=5000)
