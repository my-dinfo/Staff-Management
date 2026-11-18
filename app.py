import os, io, sqlite3, secrets, shutil, json, time
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, abort
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("STAFF_DB_PATH", os.path.join(ROOT, "data", "staff.db"))
BACKUP_DIR = os.environ.get("STAFF_BACKUP_DIR", os.path.join(ROOT, "backups"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

app = Flask(__name__)
_secret = os.environ.get("SECRET_KEY", "").strip()
if not _secret:
    # Persist a random key for a single-machine office installation. In production,
    # always provide SECRET_KEY through the hosting provider's secret environment.
    secret_file = os.path.join(ROOT, ".secret_key")
    try:
        if os.path.isfile(secret_file):
            _secret = open(secret_file, encoding="utf-8").read().strip()
        else:
            _secret = secrets.token_urlsafe(48)
            with open(secret_file, "w", encoding="utf-8") as f:
                f.write(_secret)
            try: os.chmod(secret_file, 0o600)
            except OSError: pass
    except OSError:
        _secret = secrets.token_urlsafe(48)
app.secret_key = _secret

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,
)

oauth = OAuth(app)
google = None
if os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"):
    google = oauth.register(
        name="google", client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

DEPARTMENTS = ["စီမံရေးရာ", "ဘဏ္ဍာရေး", "နည်းပညာ", "လူ့စွမ်းအားအရင်းအမြစ်", "လုပ်ငန်းဆောင်ရွက်ရေး", "လုံခြုံရေး", "အခြား"]
STATUSES = ["တာဝန်ထမ်းဆောင်ဆဲ", "ခွင့်ယူ", "အလုပ်မှထွက်"]
ROLES = ["admin", "user"]
EMPLOYEE_FIELDS = ["employee_code", "full_name", "department", "position", "phone", "email", "hire_date", "status", "address", "date_of_birth", "gender", "emergency_contact", "notes"]
FIELD_LABELS = {
    "employee_code":"ဝန်ထမ်းအမှတ်", "full_name":"အမည်", "department":"ဌာန", "position":"ရာထူး",
    "phone":"ဖုန်း", "email":"အီးမေးလ်", "hire_date":"ခန့်အပ်သည့်ရက်", "status":"အခြေအနေ",
    "address":"နေရပ်လိပ်စာ", "date_of_birth":"မွေးသက္ကရာဇ်", "gender":"လိင်", "emergency_contact":"အရေးပေါ်ဆက်သွယ်ရန်", "notes":"မှတ်ချက်"
}
FIELD_LABELS_EN = {
    "employee_code":"Employee ID", "full_name":"Full Name", "department":"Department", "position":"Position",
    "phone":"Phone", "email":"Email", "hire_date":"Appointment Date", "status":"Employment Status",
    "address":"Address", "date_of_birth":"Date of Birth", "gender":"Gender", "emergency_contact":"Emergency Contact", "notes":"Notes"
}
DEPARTMENTS_EN = {"စီမံရေးရာ":"Administration", "ဘဏ္ဍာရေး":"Finance", "နည်းပညာ":"Technology", "လူ့စွမ်းအားအရင်းအမြစ်":"Human Resources", "လုပ်ငန်းဆောင်ရွက်ရေး":"Operations", "လုံခြုံရေး":"Security", "အခြား":"Other"}
STATUSES_EN = {"တာဝန်ထမ်းဆောင်ဆဲ":"Active", "ခွင့်ယူ":"On leave", "အလုပ်မှထွက်":"Resigned"}

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=20000")
    return conn

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','user')),
          is_active INTEGER NOT NULL DEFAULT 1, approved INTEGER NOT NULL DEFAULT 1,
          auth_provider TEXT NOT NULL DEFAULT 'local', google_sub TEXT UNIQUE, email TEXT DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS employees (
          id INTEGER PRIMARY KEY AUTOINCREMENT, employee_code TEXT UNIQUE NOT NULL,
          full_name TEXT NOT NULL, department TEXT NOT NULL, position TEXT NOT NULL,
          phone TEXT DEFAULT '', email TEXT DEFAULT '', hire_date TEXT DEFAULT '',
          status TEXT NOT NULL DEFAULT 'တာဝန်ထမ်းဆောင်ဆဲ', address TEXT DEFAULT '',
          date_of_birth TEXT DEFAULT '', gender TEXT DEFAULT '', emergency_contact TEXT DEFAULT '',
          notes TEXT DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS employment_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id INTEGER NOT NULL,
          effective_date TEXT NOT NULL, event_type TEXT NOT NULL, department TEXT DEFAULT '',
          position TEXT DEFAULT '', details TEXT DEFAULT '', created_by INTEGER,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE,
          FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS audit_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT NOT NULL,
          target_type TEXT DEFAULT '', target_id TEXT DEFAULT '', details TEXT DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS login_attempts (
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL,
          remote_addr TEXT NOT NULL, success INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # Safe schema upgrades for existing DBs from the previous prototype.
        user_cols = {r["name"] for r in c.execute("PRAGMA table_info(users)").fetchall()}
        for col, typ in [("approved","INTEGER NOT NULL DEFAULT 1"),("auth_provider","TEXT NOT NULL DEFAULT 'local'"),("google_sub","TEXT"),("email","TEXT DEFAULT ''")]:
            if col not in user_cols:
                c.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
        cols = {r["name"] for r in c.execute("PRAGMA table_info(employees)").fetchall()}
        for col, typ in [("address","TEXT DEFAULT ''"),("date_of_birth","TEXT DEFAULT ''"),("gender","TEXT DEFAULT ''"),("emergency_contact","TEXT DEFAULT ''")]:
            if col not in cols:
                c.execute(f"ALTER TABLE employees ADD COLUMN {col} {typ}")

def log_action(action, target_type="", target_id="", details=""):
    with connect() as c:
        c.execute("INSERT INTO audit_log(user_id, action, target_type, target_id, details) VALUES(?,?,?,?,?)",
                  (session.get("user_id"), action, target_type, str(target_id), details[:500]))

def current_user():
    if not session.get("user_id"):
        return None
    with connect() as c:
        return c.execute("SELECT id, username, role, is_active, approved, auth_provider, email FROM users WHERE id=?", (session["user_id"],)).fetchone()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        u = current_user()
        if not u or not u["is_active"]:
            session.clear()
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user()["role"] != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapped

def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]

@app.context_processor
def inject_globals():
    return {"csrf_token": csrf_token, "departments": DEPARTMENTS, "statuses": STATUSES,
            "field_labels": FIELD_LABELS, "current_user": current_user()}

@app.before_request
def approval_gate():
    allowed = {"login", "signup", "google_login", "google_callback", "pending", "static", "setup"}
    if request.endpoint in allowed or request.endpoint is None:
        return None
    u = current_user()
    if u and (not u["is_active"] or not u["approved"]):
        session.clear()
        return redirect(url_for("pending"))

@app.before_request
def csrf_protect():
    if request.method == "POST":
        sent = request.form.get("_csrf", "")
        expected = session.get("_csrf", "")
        if not sent or not expected or not secrets.compare_digest(sent, expected):
            abort(400, "CSRF token မမှန်ပါ။ စာမျက်နှာကို refresh လုပ်ပြီး ထပ်ကြိုးစားပါ။")

@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; form-action 'self'; frame-ancestors 'none'; base-uri 'self'")
    if request.is_secure or app.config.get("SESSION_COOKIE_SECURE"):
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


def login_rate_limited(username, remote_addr):
    # Five failed attempts per username+IP in a rolling 15-minute window.
    with connect() as c:
        count = c.execute("""SELECT COUNT(*) FROM login_attempts
          WHERE username=? AND remote_addr=? AND success=0
          AND created_at >= datetime('now','-15 minutes')""", (username, remote_addr)).fetchone()[0]
    return count >= 5


def record_login_attempt(username, remote_addr, success):
    with connect() as c:
        c.execute("INSERT INTO login_attempts(username,remote_addr,success) VALUES(?,?,?)",
                  (username[:128], remote_addr[:64], int(success)))
        c.execute("DELETE FROM login_attempts WHERE created_at < datetime('now','-7 days')")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user(): return redirect(url_for("index"))
    if request.method == "POST":
        username=request.form.get("username","").strip()[:128]
        email=request.form.get("email","").strip().lower()[:254]
        password=request.form.get("password",""); confirm=request.form.get("confirm","")
        if len(username)<4 or len(password)<12 or password!=confirm or not email or "@" not in email:
            flash("Username၊ Email နှင့် Password (အနည်းဆုံး ၁၂ လုံး) ကို မှန်ကန်စွာ ဖြည့်ပါ။", "error")
        else:
            try:
                with connect() as c:
                    c.execute("INSERT INTO users(username,password_hash,role,is_active,approved,auth_provider,email) VALUES(?,?, 'user',1,0,'local',?)",(username,generate_password_hash(password),email))
                log_action("signup_pending","user",username,email)
                return redirect(url_for("pending"))
            except sqlite3.IntegrityError: flash("ဤ Username ကို အသုံးပြုပြီးဖြစ်ပါသည်။", "error")
    return render_template("signup.html", google_enabled=bool(google))

@app.route("/pending")
def pending(): return render_template("pending.html")

@app.route("/auth/google")
def google_login():
    if not google: abort(503, "Google Sign-In ကို Admin က မသတ်မှတ်ရသေးပါ။")
    return google.authorize_redirect(url_for("google_callback", _external=True))

@app.route("/auth/google/callback")
def google_callback():
    if not google: abort(503)
    token=google.authorize_access_token()
    info=token.get("userinfo") or google.parse_id_token(token)
    if not info or not info.get("sub") or not info.get("email_verified"):
        flash("Google အကောင့် အတည်ပြုမှု မအောင်မြင်ပါ။", "error"); return redirect(url_for("login"))
    sub=str(info["sub"]); email=str(info.get("email","")).lower()[:254]
    with connect() as c:
        user=c.execute("SELECT * FROM users WHERE google_sub=?",(sub,)).fetchone()
        if not user:
            base=(email.split("@")[0] or "googleuser")[:110]; username=base; suffix=1
            while c.execute("SELECT 1 FROM users WHERE username=?",(username,)).fetchone():
                suffix+=1; username=f"{base}{suffix}"
            cur=c.execute("INSERT INTO users(username,password_hash,role,is_active,approved,auth_provider,google_sub,email) VALUES(?,?, 'user',1,0,'google',?,?)",(username,generate_password_hash(secrets.token_urlsafe(32)),sub,email))
            user=c.execute("SELECT * FROM users WHERE id=?",(cur.lastrowid,)).fetchone()
            log_action("google_signup_pending","user",username,email)
    if user and user["is_active"] and user["approved"]:
        session.clear(); session["user_id"]=user["id"]; session["_csrf"]=secrets.token_urlsafe(32)
        log_action("google_login","user",user["id"],email); return redirect(url_for("index"))
    session.clear(); return redirect(url_for("pending"))

@app.route("/setup", methods=["GET","POST"])
def setup():
    with connect() as c:
        count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count:
        return redirect(url_for("login"))
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        confirm = request.form.get("confirm","")
        if len(username) < 4:
            flash("အသုံးပြုသူအမည် အနည်းဆုံး ၄ လုံး ဖြစ်ရပါမည်။", "error")
        elif len(password) < 12:
            flash("စကားဝှက် အနည်းဆုံး ၁၂ လုံး အသုံးပြုပါ။", "error")
        elif password != confirm:
            flash("စကားဝှက်နှစ်ခု မတူပါ။", "error")
        else:
            with connect() as c:
                c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                          (username, generate_password_hash(password), "admin"))
            log_action("initial_admin_created","user",username)
            flash("Admin အကောင့် ဖန်တီးပြီးပါပြီ။ Login ဝင်နိုင်ပါပြီ။","success")
            return redirect(url_for("login"))
    return render_template("setup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()[:128]
        password = request.form.get("password", "")
        remote_addr = request.remote_addr or "unknown"
        if login_rate_limited(username, remote_addr):
            flash("Login ကြိုးစားမှုများလွန်းပါသည်။ ၁၅ မိနစ်ခန့်စောင့်ပြီး ထပ်ကြိုးစားပါ။", "error")
            return render_template("login.html", google_enabled=bool(google)), 429
        with connect() as c:
            user = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        valid = bool(user and user["is_active"] and check_password_hash(user["password_hash"], password))
        record_login_attempt(username, remote_addr, valid)
        if valid:
            session.clear()
            session["user_id"] = user["id"]
            session["_csrf"] = secrets.token_urlsafe(32)
            log_action("login", "user", user["id"])
            next_url = request.args.get("next", "")
            # Prevent open redirects: only allow local absolute paths.
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("index")
            return redirect(next_url)
        flash("အသုံးပြုသူအမည် သို့မဟုတ် စကားဝှက် မမှန်ပါ။", "error")
    return render_template("login.html", google_enabled=bool(google))

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    log_action("logout","user",session.get("user_id"))
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    q = request.args.get("q","").strip()
    department = request.args.get("department","").strip()
    status = request.args.get("status","").strip()
    sql = "SELECT * FROM employees WHERE 1=1"; params=[]
    if q:
        like=f"%{q}%"; sql += " AND (employee_code LIKE ? OR full_name LIKE ? OR department LIKE ? OR position LIKE ? OR phone LIKE ? OR email LIKE ?)"
        params += [like]*6
    if department: sql += " AND department=?"; params.append(department)
    if status: sql += " AND status=?"; params.append(status)
    sql += " ORDER BY full_name COLLATE NOCASE"
    with connect() as c:
        employees=c.execute(sql,params).fetchall()
        stats = {
            "total": c.execute("SELECT COUNT(*) FROM employees").fetchone()[0],
            "active": c.execute("SELECT COUNT(*) FROM employees WHERE status=?",(STATUSES[0],)).fetchone()[0],
            "leave": c.execute("SELECT COUNT(*) FROM employees WHERE status=?",(STATUSES[1],)).fetchone()[0],
            "departments": c.execute("SELECT COUNT(DISTINCT department) FROM employees").fetchone()[0]
        }
        dept_rows = c.execute("SELECT department, COUNT(*) AS total, SUM(CASE WHEN status=? THEN 1 ELSE 0 END) AS active FROM employees GROUP BY department ORDER BY department",(STATUSES[0],)).fetchall()
    return render_template("index.html", employees=employees, stats=stats, dept_rows=dept_rows, q=q, department=department, status=status)

def form_data():
    return {f: request.form.get(f,"").strip() for f in EMPLOYEE_FIELDS}

def validate_employee(d):
    if not d["employee_code"] or not d["full_name"] or not d["position"]:
        return "ဝန်ထမ်းအမှတ်၊ အမည်နှင့် ရာထူးတို့ကို ဖြည့်ပါ။"
    if d["department"] not in DEPARTMENTS: return "ဌာနကို မှန်ကန်စွာ ရွေးချယ်ပါ။"
    if d["status"] not in STATUSES: return "အခြေအနေကို မှန်ကန်စွာ ရွေးချယ်ပါ။"
    if d["email"] and ("@" not in d["email"] or len(d["email"]) > 254): return "အီးမေးလ်လိပ်စာကို စစ်ဆေးပါ။"
    return None

@app.route("/employee/new", methods=["GET","POST"])
@admin_required
def create_employee():
    d = {f:"" for f in EMPLOYEE_FIELDS}; d.update(department=DEPARTMENTS[0],status=STATUSES[0])
    if request.method=="POST":
        d=form_data(); err=validate_employee(d)
        if err: flash(err,"error")
        else:
            try:
                with connect() as c:
                    cur=c.execute("""INSERT INTO employees(employee_code,full_name,department,position,phone,email,hire_date,status,address,date_of_birth,gender,emergency_contact,notes)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", tuple(d[f] for f in EMPLOYEE_FIELDS))
                    eid=cur.lastrowid
                    c.execute("""INSERT INTO employment_history(employee_id,effective_date,event_type,department,position,details,created_by)
                    VALUES(?,?,?,?,?,?,?)""",(eid,d["hire_date"] or date.today().isoformat(),"ခန့်အပ်ခြင်း",d["department"],d["position"],"ပထမဆုံး မှတ်တမ်း",session["user_id"]))
                log_action("employee_created","employee",eid,d["employee_code"])
                flash("ဝန်ထမ်းစာရင်း သိမ်းဆည်းပြီးပါပြီ။","success")
                return redirect(url_for("employee_detail",employee_id=eid))
            except sqlite3.IntegrityError: flash("ဤဝန်ထမ်းအမှတ် ရှိပြီးဖြစ်ပါသည်။","error")
    return render_template("employee_form.html", employee=d, mode="new")

@app.route("/employee/<int:employee_id>")
@login_required
def employee_detail(employee_id):
    with connect() as c:
        e=c.execute("SELECT * FROM employees WHERE id=?",(employee_id,)).fetchone()
        history=c.execute("SELECT h.*,u.username FROM employment_history h LEFT JOIN users u ON u.id=h.created_by WHERE employee_id=? ORDER BY effective_date DESC,h.id DESC",(employee_id,)).fetchall()
    if not e: abort(404)
    return render_template("employee_detail.html", employee=e, history=history)

@app.route("/employee/<int:employee_id>/edit", methods=["GET","POST"])
@admin_required
def edit_employee(employee_id):
    with connect() as c: row=c.execute("SELECT * FROM employees WHERE id=?",(employee_id,)).fetchone()
    if not row: abort(404)
    old=dict(row)
    if request.method=="POST":
        d=form_data(); err=validate_employee(d)
        if err: flash(err,"error")
        else:
            try:
                with connect() as c:
                    c.execute("""UPDATE employees SET employee_code=?,full_name=?,department=?,position=?,phone=?,email=?,hire_date=?,status=?,address=?,date_of_birth=?,gender=?,emergency_contact=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                              tuple(d[f] for f in EMPLOYEE_FIELDS)+(employee_id,))
                    if old["department"]!=d["department"] or old["position"]!=d["position"] or old["status"]!=d["status"]:
                        evt="ဌာန/ရာထူး/အခြေအနေ ပြောင်းလဲခြင်း"
                        details=f"ယခင်: {old['department']} / {old['position']} / {old['status']} → အသစ်: {d['department']} / {d['position']} / {d['status']}"
                        c.execute("""INSERT INTO employment_history(employee_id,effective_date,event_type,department,position,details,created_by) VALUES(?,?,?,?,?,?,?)""",
                                  (employee_id,date.today().isoformat(),evt,d["department"],d["position"],details,session["user_id"]))
                log_action("employee_updated","employee",employee_id,d["employee_code"])
                flash("အချက်အလက် ပြင်ဆင်ပြီးပါပြီ။","success")
                return redirect(url_for("employee_detail",employee_id=employee_id))
            except sqlite3.IntegrityError: flash("ဤဝန်ထမ်းအမှတ်ကို အခြားသူ အသုံးပြုထားပါသည်။","error")
    else: d=old
    return render_template("employee_form.html", employee=d, mode="edit")

@app.route("/employee/<int:employee_id>/history", methods=["POST"])
@admin_required
def add_history(employee_id):
    with connect() as c:
        e=c.execute("SELECT id FROM employees WHERE id=?",(employee_id,)).fetchone()
    if not e: abort(404)
    effective=request.form.get("effective_date","").strip()
    event=request.form.get("event_type","").strip()
    if not effective or not event:
        flash("ရက်စွဲနှင့် မှတ်တမ်းအမျိုးအစား ဖြည့်ပါ။","error")
    else:
        with connect() as c:
            c.execute("""INSERT INTO employment_history(employee_id,effective_date,event_type,department,position,details,created_by)
            VALUES(?,?,?,?,?,?,?)""",(employee_id,effective,event,request.form.get("department","").strip(),request.form.get("position","").strip(),request.form.get("details","").strip(),session["user_id"]))
        log_action("employment_history_added","employee",employee_id,event)
        flash("အလုပ်အကိုင်မှတ်တမ်း ထည့်သွင်းပြီးပါပြီ။","success")
    return redirect(url_for("employee_detail",employee_id=employee_id))

@app.route("/employee/<int:employee_id>/delete", methods=["POST"])
@admin_required
def delete_employee(employee_id):
    with connect() as c:
        e=c.execute("SELECT employee_code FROM employees WHERE id=?",(employee_id,)).fetchone()
        if e: c.execute("DELETE FROM employees WHERE id=?",(employee_id,))
    if e: log_action("employee_deleted","employee",employee_id,e["employee_code"])
    flash("ဝန်ထမ်းမှတ်တမ်း ဖယ်ရှားပြီးပါပြီ။","success")
    return redirect(url_for("index"))

def filtered_employee_rows():
    q=request.args.get("q","").strip(); department=request.args.get("department","").strip(); status=request.args.get("status","").strip()
    sql="SELECT employee_code,full_name,department,position,phone,email,hire_date,status,address,date_of_birth,gender,emergency_contact,notes FROM employees WHERE 1=1"; p=[]
    if q:
        like=f"%{q}%"; sql+=" AND (employee_code LIKE ? OR full_name LIKE ? OR department LIKE ? OR position LIKE ? OR phone LIKE ? OR email LIKE ?)"; p += [like]*6
    if department and department in DEPARTMENTS: sql+=" AND department=?"; p.append(department)
    if status: sql+=" AND status=?"; p.append(status)
    sql+=" ORDER BY department,full_name COLLATE NOCASE"
    with connect() as c: return c.execute(sql,p).fetchall()

@app.route("/reports")
@login_required
def reports():
    selected_department = request.args.get("department", "").strip()
    if selected_department and selected_department not in DEPARTMENTS:
        selected_department = ""
    with connect() as c:
        rows=c.execute("""SELECT department, COUNT(*) total,
          SUM(CASE WHEN status=? THEN 1 ELSE 0 END) active,
          SUM(CASE WHEN status=? THEN 1 ELSE 0 END) on_leave,
          SUM(CASE WHEN status=? THEN 1 ELSE 0 END) resigned
          FROM employees """ + ("WHERE department=? " if selected_department else "") + "GROUP BY department ORDER BY department", ((STATUSES[0],STATUSES[1],STATUSES[2],selected_department) if selected_department else (STATUSES[0],STATUSES[1],STATUSES[2]))).fetchall()
    return render_template("reports.html", rows=rows, total=sum(r["total"] for r in rows), selected_department=selected_department)

@app.route("/export.xlsx")
@login_required
def export_excel():
    rows=filtered_employee_rows()
    lang = request.args.get("lang", "both").lower()
    if lang not in ("my", "en", "both"): lang = "both"
    wb=Workbook(); ws=wb.active; ws.title="Staff Report" if lang == "en" else "ဝန်ထမ်းစာရင်း"
    headers = [FIELD_LABELS[f] if lang == "my" else FIELD_LABELS_EN[f] if lang == "en" else FIELD_LABELS[f] + " / " + FIELD_LABELS_EN[f] for f in EMPLOYEE_FIELDS]
    title_text = "Staff Management - Employee Report" if lang == "en" else "ဝန်ထမ်းအင်အား စီမံခန့်ခွဲမှု - ဝန်ထမ်းစာရင်း" if lang == "my" else "ဝန်ထမ်းအင်အား စီမံခန့်ခွဲမှု / Staff Management - Employee Report"
    ws.append([title_text])
    ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=len(headers))
    ws["A1"].font=Font(bold=True,size=15,color="FFFFFF"); ws["A1"].fill=PatternFill("solid",fgColor="17365D")
    ws["A1"].alignment=Alignment(horizontal="center")
    ws.append(headers)
    for cell in ws[2]:
        cell.font=Font(bold=True,color="FFFFFF"); cell.fill=PatternFill("solid",fgColor="2F75B5"); cell.alignment=Alignment(horizontal="center",wrap_text=True)
    for r in rows:
        values = [r[f] for f in EMPLOYEE_FIELDS]
        if lang == "en":
            values[2] = DEPARTMENTS_EN.get(values[2], values[2])
            values[7] = STATUSES_EN.get(values[7], values[7])
        ws.append(values)
    widths=[18,25,25,22,18,28,18,24,32,18,14,25,35]
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
    for row in ws.iter_rows(min_row=3):
        for cell in row: cell.alignment=Alignment(vertical="top",wrap_text=True)
    ws.freeze_panes="A3"; ws.auto_filter.ref=f"A2:{get_column_letter(len(headers))}{max(2,ws.max_row)}"
    out=io.BytesIO(); wb.save(out); out.seek(0)
    log_action("excel_export","report","employees",f"{len(rows)} records")
    return send_file(out,as_attachment=True,download_name=f"staff_report_{datetime.now():%Y%m%d_%H%M}.xlsx",mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/export.pdf")
@login_required
def export_pdf():
    rows = filtered_employee_rows()
    lang = request.args.get("lang", "both").lower()
    if lang not in ("my", "en", "both"): lang = "both"
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=8*mm, leftMargin=8*mm, topMargin=10*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    font_regular = os.environ.get("MYANMAR_FONT_PATH", os.path.join(ROOT, "static", "fonts", "NotoSansMyanmar-Regular.ttf"))
    font_bold = os.path.join(os.path.dirname(font_regular), "NotoSansMyanmar-Bold.ttf")
    font_name = "Helvetica"
    if lang in ("my", "both") and os.path.isfile(font_regular):
        try:
            pdfmetrics.registerFont(TTFont("MyanmarReport", font_regular))
            if os.path.isfile(font_bold): pdfmetrics.registerFont(TTFont("MyanmarReport-Bold", font_bold))
            font_name = "MyanmarReport"
        except Exception:
            font_name = "Helvetica"
    title_text = "Staff Management - Employee Report" if lang == "en" else "ဝန်ထမ်းအင်အား စီမံခန့်ခွဲမှု - ဝန်ထမ်းစာရင်း" if lang == "my" else "ဝန်ထမ်းအင်အား စီမံခန့်ခွဲမှု / Staff Management - Employee Report"
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], fontName=font_name, fontSize=13, leading=17)
    body_style = ParagraphStyle("ReportBody", parent=styles["Normal"], fontName=font_name, fontSize=7, leading=9)
    title = Paragraph(title_text, title_style)
    note_text = ("ထုတ်ယူချိန်: " if lang != "en" else "Generated: ") + datetime.now().strftime("%Y-%m-%d %H:%M") + (" | စာရင်း: " if lang != "en" else " | Records: ") + str(len(rows))
    headers_my = ["ဝန်ထမ်းအမှတ်", "အမည်", "ဌာန", "ရာထူး", "ဖုန်း", "ခန့်အပ်သည့်ရက်", "အခြေအနေ"]
    headers_en = ["Employee ID", "Full Name", "Department", "Position", "Phone", "Appointment Date", "Status"]
    if lang == "my": headers = headers_my
    elif lang == "en": headers = headers_en
    else: headers = [a + " / " + b for a, b in zip(headers_my, headers_en)]
    data = [[Paragraph(str(h), body_style) for h in headers]]
    for r in rows:
        dept = DEPARTMENTS_EN.get(r["department"], r["department"]) if lang == "en" else r["department"]
        status = STATUSES_EN.get(r["status"], r["status"]) if lang == "en" else r["status"]
        vals = [r["employee_code"], r["full_name"], dept, r["position"], r["phone"], r["hire_date"], status]
        data.append([Paragraph(str(v or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), body_style) for v in vals])
    widths = [24*mm, 37*mm, 34*mm, 32*mm, 25*mm, 28*mm, 34*mm]
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365d")), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,-1),font_name), ("FONTSIZE",(0,0),(-1,-1),7),
        ("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#d5deea")), ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f4f7fb")]),
        ("LEFTPADDING",(0,0),(-1,-1),4), ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4)
    ]))
    note_style = ParagraphStyle("ReportNote", parent=styles["Normal"], fontName=font_name, fontSize=8)
    doc.build([title, Spacer(1, 3*mm), Paragraph(note_text, note_style), Spacer(1, 4*mm), table])
    buf.seek(0)
    log_action("pdf_export", "report", "employees", f"{len(rows)} records; language={lang}")
    return send_file(buf, as_attachment=True, download_name=f"staff_report_{lang}_{datetime.now():%Y%m%d_%H%M}.pdf", mimetype="application/pdf")

@app.route("/admin/users")
@admin_required
def users():
    with connect() as c: rows=c.execute("SELECT id,username,role,is_active,approved,auth_provider,email,created_at FROM users ORDER BY approved,id").fetchall()
    return render_template("users.html", users=rows)

@app.route("/admin/users/new", methods=["POST"])
@admin_required
def create_user():
    username=request.form.get("username","").strip(); password=request.form.get("password",""); role="user"
    if len(username)<4 or len(password)<12:
        flash("Username အနည်းဆုံး ၄ လုံး၊ password အနည်းဆုံး ၁၂ လုံးနှင့် မှန်ကန်သော role လိုအပ်ပါသည်။","error")
    else:
        try:
            with connect() as c: c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",(username,generate_password_hash(password),role))
            log_action("user_created","user",username,role); flash("အသုံးပြုသူ အကောင့်ဖန်တီးပြီးပါပြီ။","success")
        except sqlite3.IntegrityError: flash("Username ရှိပြီးသားဖြစ်ပါသည်။","error")
    return redirect(url_for("users"))

@app.route("/admin/users/<int:user_id>/approve", methods=["POST"])
@admin_required
def approve_user(user_id):
    with connect() as c:
        u=c.execute("SELECT username FROM users WHERE id=?",(user_id,)).fetchone()
        if u: c.execute("UPDATE users SET approved=1,is_active=1 WHERE id=?",(user_id,))
    if u:
        log_action("user_approved","user",user_id,u["username"]); flash("အသုံးပြုသူကို ခွင့်ပြုပြီးပါပြီ။", "success")
    return redirect(url_for("users"))

@app.route("/admin/users/<int:user_id>/reject", methods=["POST"])
@admin_required
def reject_user(user_id):
    if user_id==session.get("user_id"): abort(400)
    with connect() as c:
        u=c.execute("SELECT username FROM users WHERE id=?",(user_id,)).fetchone()
        if u: c.execute("UPDATE users SET approved=0,is_active=0 WHERE id=?",(user_id,))
    if u:
        log_action("user_access_revoked","user",user_id,u["username"]); flash("အသုံးပြုခွင့်ကို ရုပ်သိမ်းပြီးပါပြီ။", "success")
    return redirect(url_for("users"))

@app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    if user_id==session.get("user_id"):
        flash("ကိုယ့်အကောင့်ကိုယ် ပိတ်၍မရပါ။","error")
    else:
        with connect() as c:
            u=c.execute("SELECT is_active,username FROM users WHERE id=?",(user_id,)).fetchone()
            if u:
                c.execute("UPDATE users SET is_active=? WHERE id=?",(0 if u["is_active"] else 1,user_id))
                log_action("user_toggled","user",user_id,u["username"])
                flash("အကောင့်အခြေအနေ ပြောင်းလဲပြီးပါပြီ။","success")
    return redirect(url_for("users"))

@app.route("/admin/users/<int:user_id>/password", methods=["POST"])
@admin_required
def reset_password(user_id):
    password=request.form.get("password","")
    if len(password)<12: flash("Password အနည်းဆုံး ၁၂ လုံးဖြစ်ရပါမည်။","error")
    else:
        with connect() as c: c.execute("UPDATE users SET password_hash=? WHERE id=?",(generate_password_hash(password),user_id))
        log_action("password_reset","user",user_id)
        flash("Password ပြောင်းလဲပြီးပါပြီ။","success")
    return redirect(url_for("users"))

@app.route("/admin/backup", methods=["GET","POST"])
@admin_required
def backup():
    if request.method=="POST" and request.form.get("action")=="create":
        dest=os.path.join(BACKUP_DIR,"staff_backup_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".db")
        with connect() as src:
            with sqlite3.connect(dest) as dst: src.backup(dst)
        log_action("database_backup","backup",os.path.basename(dest))
        flash("Database backup ဖန်တီးပြီးပါပြီ။","success")
        return redirect(url_for("backup"))
    backups=[]
    for name in sorted(os.listdir(BACKUP_DIR),reverse=True):
        if name.endswith(".db") and name.startswith("staff_backup_"):
            p=os.path.join(BACKUP_DIR,name)
            backups.append({"name":name,"size":os.path.getsize(p),"modified":datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")})
    return render_template("backup.html",backups=backups)

@app.route("/admin/backup/download/<path:name>")
@admin_required
def download_backup(name):
    safe=secure_filename(name)
    if safe!=name or not name.startswith("staff_backup_") or not name.endswith(".db"): abort(404)
    path=os.path.join(BACKUP_DIR,name)
    if not os.path.isfile(path): abort(404)
    log_action("backup_download","backup",name)
    return send_file(path,as_attachment=True,download_name=name)

@app.route("/admin/backup/restore", methods=["POST"])
@admin_required
def restore_backup():
    f=request.files.get("backup_file")
    if not f or not f.filename.lower().endswith((".db",".sqlite",".sqlite3")):
        flash("မှန်ကန်သော SQLite backup ဖိုင် ရွေးချယ်ပါ။","error"); return redirect(url_for("backup"))
    temp=os.path.join(BACKUP_DIR,"restore_upload_"+secrets.token_hex(6)+".db")
    try:
        f.save(temp)
        with sqlite3.connect(temp) as test:
            ok=test.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
            tables={r[0] for r in test.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not ok or not {"users","employees","employment_history"}.issubset(tables):
            raise ValueError("Database structure မမှန်ပါ။")
        current=os.path.join(BACKUP_DIR,"pre_restore_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".db")
        with connect() as src:
            with sqlite3.connect(current) as dst: src.backup(dst)
        # Use SQLite backup API rather than replacing a live DB file.
        with sqlite3.connect(temp) as src, connect() as dst:
            src.backup(dst)
        log_action("database_restored","backup",f.filename)
        flash("Database restore ပြီးပါပြီ။ လုံခြုံရေးအတွက် ပြန်လည် login ဝင်ပါ။","success")
        session.clear()
        return redirect(url_for("login"))
    except Exception as ex:
        flash("Restore မအောင်မြင်ပါ။ Backup ဖိုင်၏ မှန်ကန်မှုကို စစ်ဆေးပါ။","error")
        app.logger.warning("Restore failed: %s", ex)
        return redirect(url_for("backup"))
    finally:
        if os.path.exists(temp): os.remove(temp)

@app.errorhandler(403)
def forbidden(e): return render_template("error.html",code=403,message="ဤလုပ်ဆောင်ချက်အတွက် Admin ခွင့်ပြုချက် လိုအပ်ပါသည်။"),403
@app.errorhandler(404)
def not_found(e): return render_template("error.html",code=404,message="တောင်းဆိုထားသော စာမျက်နှာကို မတွေ့ပါ။"),404
@app.errorhandler(400)
def bad_request(e): return render_template("error.html",code=400,message=getattr(e,"description","တောင်းဆိုမှု မမှန်ပါ။")),400

init_db()
if __name__=="__main__":
    app.run(host=os.environ.get("HOST","0.0.0.0"),port=int(os.environ.get("PORT","5000")),debug=False)
