import io
import os
import re
import secrets
import string
import time
from collections import defaultdict
from datetime import datetime
from functools import wraps

import qrcode
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from flask_wtf.csrf import CSRFProtect

from config import Config
from models import Candidate, Election, SchoolClass, SchoolSettings, Vote, VotingCode, db

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
csrf = CSRFProtect(app)

# Store hashed admin password
_admin_pw_hash = generate_password_hash(app.config["ADMIN_PASSWORD"], method="pbkdf2:sha256")

# Rate limiting storage: {ip: [timestamps]}
_rate_limits: dict[str, list[float]] = defaultdict(list)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def check_rate_limit(ip: str) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    now = time.time()
    window = 60  # seconds
    max_requests = app.config["RATE_LIMIT_PER_MINUTE"]

    # Clean old entries
    _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < window]

    if len(_rate_limits[ip]) >= max_requests:
        return False

    _rate_limits[ip].append(now)
    return True


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


def generate_code(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def class_sort_key(name: str) -> tuple:
    """Sort class names naturally: 5a < 5b < 6a < 10d."""
    m = re.match(r"(\d+)(.*)", name.strip())
    if m:
        return (int(m.group(1)), m.group(2).lower())
    return (999, name.lower())


def get_school_settings() -> SchoolSettings:
    """Return the single SchoolSettings row, creating it if needed."""
    settings = SchoolSettings.query.first()
    if not settings:
        settings = SchoolSettings(school_name="")
        db.session.add(settings)
        db.session.commit()
    return settings


@app.context_processor
def inject_school_settings():
    """Make school_settings available in all templates."""
    return dict(school_settings=get_school_settings())


# ---------------------------------------------------------------------------
# Schüler-Bereich
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/enter-code", methods=["POST"])
def enter_code():
    code = request.form.get("code", "").strip()
    if not code:
        flash("Bitte gib einen Code ein.", "error")
        return redirect(url_for("index"))

    ip = request.remote_addr or "unknown"
    if not check_rate_limit(ip):
        flash("Zu viele Versuche. Bitte warte eine Minute.", "error")
        return redirect(url_for("index"))

    return redirect(url_for("vote", code=code))


@app.route("/vote/<code>")
def vote(code: str):
    ip = request.remote_addr or "unknown"
    if not check_rate_limit(ip):
        flash("Zu viele Versuche. Bitte warte eine Minute.", "error")
        return redirect(url_for("index"))

    voting_code = VotingCode.query.filter_by(code=code).first()
    if not voting_code:
        flash("Ungültiger Code.", "error")
        return redirect(url_for("index"))

    if voting_code.is_used:
        flash("Dieser Code wurde bereits verwendet.", "error")
        return redirect(url_for("index"))

    election = voting_code.election
    if not election.is_active:
        flash("Diese Wahl ist derzeit nicht aktiv.", "error")
        return redirect(url_for("index"))

    candidates = Candidate.query.filter_by(election_id=election.id).order_by(Candidate.name).all()

    return render_template(
        "vote.html",
        election=election,
        candidates=candidates,
        code=code,
    )


@app.route("/vote/<code>/submit", methods=["POST"])
def submit_vote(code: str):
    voting_code = VotingCode.query.filter_by(code=code).first()
    if not voting_code:
        flash("Ungültiger Code.", "error")
        return redirect(url_for("index"))

    if voting_code.is_used:
        flash("Dieser Code wurde bereits verwendet.", "error")
        return redirect(url_for("index"))

    election = voting_code.election
    if not election.is_active:
        flash("Diese Wahl ist derzeit nicht aktiv.", "error")
        return redirect(url_for("index"))

    selected_ids = request.form.getlist("candidates")
    if not selected_ids:
        flash("Bitte wähle mindestens einen Kandidaten.", "error")
        return redirect(url_for("vote", code=code))

    if len(selected_ids) > election.max_votes:
        flash(f"Du kannst maximal {election.max_votes} Kandidaten wählen.", "error")
        return redirect(url_for("vote", code=code))

    # Validate that all candidate IDs belong to this election
    valid_candidate_ids = {
        c.id for c in Candidate.query.filter_by(election_id=election.id).all()
    }
    for cid_str in selected_ids:
        try:
            cid = int(cid_str)
        except ValueError:
            abort(400)
        if cid not in valid_candidate_ids:
            abort(400)

    # Record votes (no link to voting code -> anonymous!)
    for cid_str in selected_ids:
        vote_record = Vote(election_id=election.id, candidate_id=int(cid_str))
        db.session.add(vote_record)

    # Mark code as used
    voting_code.is_used = True
    voting_code.used_at = datetime.utcnow()

    db.session.commit()

    return redirect(url_for("success"))


@app.route("/vote/success")
def success():
    return render_template("success.html")


# ---------------------------------------------------------------------------
# Admin-Bereich
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if check_password_hash(_admin_pw_hash, password):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Falsches Passwort.", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.route("/admin/")
@admin_required
def admin_dashboard():
    elections = Election.query.order_by(Election.year.desc(), Election.id.desc()).all()
    return render_template("admin/dashboard.html", elections=elections)


@app.route("/admin/school-settings", methods=["POST"])
@admin_required
def admin_school_settings():
    settings = get_school_settings()
    settings.school_name = request.form.get("school_name", "").strip()

    if "logo" in request.files:
        logo = request.files["logo"]
        if logo.filename and allowed_file(logo.filename):
            # Delete old logo
            if settings.logo_filename:
                old_path = os.path.join(app.config["UPLOAD_FOLDER"], settings.logo_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            filename = secure_filename(f"school_logo_{logo.filename}")
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            logo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            settings.logo_filename = filename

    db.session.commit()
    flash("Schuleinstellungen gespeichert.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/school-settings/delete-logo", methods=["POST"])
@admin_required
def admin_delete_logo():
    settings = get_school_settings()
    if settings.logo_filename:
        logo_path = os.path.join(app.config["UPLOAD_FOLDER"], settings.logo_filename)
        if os.path.exists(logo_path):
            os.remove(logo_path)
        settings.logo_filename = None
        db.session.commit()
    flash("Logo entfernt.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/election/new", methods=["POST"])
@admin_required
def admin_election_new():
    name = request.form.get("name", "").strip()
    year = request.form.get("year", "")
    max_votes = request.form.get("max_votes", "3")

    if not name or not year:
        flash("Name und Jahr sind Pflichtfelder.", "error")
        return redirect(url_for("admin_dashboard"))

    election = Election(
        name=name,
        year=int(year),
        max_votes=int(max_votes),
    )
    db.session.add(election)
    db.session.commit()
    flash("Wahl erstellt.", "success")
    return redirect(url_for("admin_election", election_id=election.id))


@app.route("/admin/election/<int:election_id>")
@admin_required
def admin_election(election_id: int):
    election = Election.query.get_or_404(election_id)
    candidates = Candidate.query.filter_by(election_id=election_id).order_by(Candidate.name).all()
    return render_template("admin/election.html", election=election, candidates=candidates)


@app.route("/admin/election/<int:election_id>/toggle", methods=["POST"])
@admin_required
def admin_election_toggle(election_id: int):
    election = Election.query.get_or_404(election_id)

    if not election.is_active:
        # Check if codes exist
        code_count = VotingCode.query.filter_by(election_id=election_id).count()
        if code_count == 0:
            flash("Wahl kann nicht aktiviert werden: Es wurden noch keine Codes generiert.", "error")
            return redirect(url_for("admin_election", election_id=election_id))
        # Deactivate all other elections first
        Election.query.update({"is_active": False})
        election.is_active = True
    else:
        election.is_active = False

    db.session.commit()
    status = "aktiviert" if election.is_active else "deaktiviert"
    flash(f"Wahl {status}.", "success")
    return redirect(url_for("admin_election", election_id=election_id))


@app.route("/admin/election/<int:election_id>/delete", methods=["POST"])
@admin_required
def admin_election_delete(election_id: int):
    election = Election.query.get_or_404(election_id)
    db.session.delete(election)
    db.session.commit()
    flash("Wahl gelöscht.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/election/<int:election_id>/candidate/add", methods=["POST"])
@admin_required
def admin_candidate_add(election_id: int):
    election = Election.query.get_or_404(election_id)

    name = request.form.get("name", "").strip()
    class_name = request.form.get("class_name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Name ist ein Pflichtfeld.", "error")
        return redirect(url_for("admin_election", election_id=election_id))

    photo_filename = None
    if "photo" in request.files:
        photo = request.files["photo"]
        if photo.filename and allowed_file(photo.filename):
            filename = secure_filename(f"{election_id}_{name}_{photo.filename}")
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            photo_filename = filename

    candidate = Candidate(
        election_id=election_id,
        name=name,
        class_name=class_name,
        description=description,
        photo_filename=photo_filename,
    )
    db.session.add(candidate)
    db.session.commit()
    flash(f"Kandidat '{name}' hinzugefügt.", "success")
    return redirect(url_for("admin_election", election_id=election_id))


@app.route("/admin/candidate/<int:candidate_id>/delete", methods=["POST"])
@admin_required
def admin_candidate_delete(candidate_id: int):
    candidate = Candidate.query.get_or_404(candidate_id)
    election_id = candidate.election_id

    # Delete photo if exists
    if candidate.photo_filename:
        photo_path = os.path.join(app.config["UPLOAD_FOLDER"], candidate.photo_filename)
        if os.path.exists(photo_path):
            os.remove(photo_path)

    db.session.delete(candidate)
    db.session.commit()
    flash("Kandidat gelöscht.", "success")
    return redirect(url_for("admin_election", election_id=election_id))


# ---------------------------------------------------------------------------
# Klassen
# ---------------------------------------------------------------------------

@app.route("/admin/election/<int:election_id>/class/add", methods=["POST"])
@admin_required
def admin_class_add(election_id: int):
    election = Election.query.get_or_404(election_id)

    name = request.form.get("name", "").strip()
    student_count = request.form.get("student_count", "")

    if not name or not student_count:
        flash("Klasse und Schülerzahl sind Pflichtfelder.", "error")
        return redirect(url_for("admin_codes", election_id=election_id))

    sc = SchoolClass(
        election_id=election_id,
        name=name,
        student_count=int(student_count),
    )
    db.session.add(sc)
    db.session.commit()
    flash(f"Klasse '{name}' hinzugefügt.", "success")
    return redirect(url_for("admin_codes", election_id=election_id, _anchor="add-class"))


@app.route("/admin/class/<int:class_id>/delete", methods=["POST"])
@admin_required
def admin_class_delete(class_id: int):
    sc = SchoolClass.query.get_or_404(class_id)
    election_id = sc.election_id
    db.session.delete(sc)
    db.session.commit()
    flash("Klasse gelöscht.", "success")
    return redirect(url_for("admin_codes", election_id=election_id))


@app.route("/admin/election/<int:election_id>/codes/generate-classes", methods=["POST"])
@admin_required
def admin_codes_generate_classes(election_id: int):
    election = Election.query.get_or_404(election_id)
    school_classes = SchoolClass.query.filter_by(election_id=election_id).all()

    total_generated = 0
    for sc in school_classes:
        existing = VotingCode.query.filter_by(election_id=election_id, class_name=sc.name).count()
        needed = sc.student_count - existing
        if needed <= 0:
            continue

        generated = 0
        attempts = 0
        while generated < needed and attempts < needed * 3:
            code = generate_code()
            attempts += 1
            if not VotingCode.query.filter_by(code=code).first():
                vc = VotingCode(election_id=election_id, code=code, class_name=sc.name)
                db.session.add(vc)
                generated += 1

        total_generated += generated

    db.session.commit()
    flash(f"{total_generated} Codes für Klassen generiert.", "success")
    return redirect(url_for("admin_codes", election_id=election_id))


# ---------------------------------------------------------------------------
# Codes
# ---------------------------------------------------------------------------

@app.route("/admin/election/<int:election_id>/codes")
@admin_required
def admin_codes(election_id: int):
    election = Election.query.get_or_404(election_id)
    codes = VotingCode.query.filter_by(election_id=election_id).order_by(VotingCode.id).all()
    used = sum(1 for c in codes if c.is_used)
    school_classes = SchoolClass.query.filter_by(election_id=election_id).all()
    school_classes.sort(key=lambda sc: class_sort_key(sc.name))

    # Count codes per class
    class_code_counts = {}
    for sc in school_classes:
        class_code_counts[sc.name] = VotingCode.query.filter_by(
            election_id=election_id, class_name=sc.name
        ).count()

    return render_template(
        "admin/codes.html",
        election=election,
        codes=codes,
        used=used,
        school_classes=school_classes,
        class_code_counts=class_code_counts,
    )


@app.route("/admin/election/<int:election_id>/codes/generate", methods=["POST"])
@admin_required
def admin_codes_generate(election_id: int):
    election = Election.query.get_or_404(election_id)
    count = int(request.form.get("count", 50))
    count = min(count, 2000)  # Safety limit

    generated = 0
    attempts = 0
    while generated < count and attempts < count * 3:
        code = generate_code()
        attempts += 1
        # Check uniqueness
        if not VotingCode.query.filter_by(code=code).first():
            vc = VotingCode(election_id=election_id, code=code)
            db.session.add(vc)
            generated += 1

    db.session.commit()
    flash(f"{generated} Codes generiert.", "success")
    return redirect(url_for("admin_codes", election_id=election_id))


@app.route("/admin/election/<int:election_id>/codes/pdf")
@admin_required
def admin_codes_pdf(election_id: int):
    election = Election.query.get_or_404(election_id)
    settings = get_school_settings()

    # Optional: filter by single class
    filter_class = request.args.get("class_name")
    if filter_class:
        codes = VotingCode.query.filter_by(
            election_id=election_id, is_used=False, class_name=filter_class
        ).all()
    else:
        codes = VotingCode.query.filter_by(election_id=election_id, is_used=False).all()

    if not codes:
        flash("Keine ungenutzten Codes vorhanden.", "error")
        return redirect(url_for("admin_codes", election_id=election_id))

    # Group codes by class_name, sorted naturally (codes without class at the end)
    from itertools import groupby

    def sort_key(vc):
        if vc.class_name:
            return (0, class_sort_key(vc.class_name))
        return (1, (999, ""))

    codes_sorted = sorted(codes, key=sort_key)
    grouped = []
    for key, group in groupby(codes_sorted, key=lambda vc: vc.class_name or ""):
        grouped.append((key, list(group)))

    base_url = app.config["BASE_URL"].rstrip("/")
    buf = io.BytesIO()
    pdf_title = f"{election.name} {election.year}"
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(pdf_title)
    c.setAuthor(settings.school_name or "")
    page_w, page_h = A4

    # Layout: 2 columns x 5 rows = 10 per page
    cols = 2
    rows = 5
    cards_per_page = cols * rows
    margin_x = 15 * mm
    margin_y = 15 * mm
    cell_w = (page_w - 2 * margin_x) / cols
    cell_h = (page_h - 2 * margin_y) / rows

    # Reserve space for text below QR code (3 lines + padding)
    text_area_h = 22 * mm
    top_pad = 3 * mm
    qr_size = min(cell_h - text_area_h - top_pad, cell_w - 10 * mm)

    from reportlab.lib.utils import ImageReader

    first_group = True
    for class_name, class_codes in grouped:
        # Page break between classes (not before the first group)
        if not first_group:
            c.showPage()
        first_group = False

        for idx, vc in enumerate(class_codes):
            pos_on_page = idx % cards_per_page
            if idx > 0 and pos_on_page == 0:
                c.showPage()

            col = pos_on_page % cols
            row = pos_on_page // cols

            x = margin_x + col * cell_w
            y = page_h - margin_y - (row + 1) * cell_h

            # Draw cut lines (dashed)
            c.setDash(3, 3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x, y, cell_w, cell_h)
            c.setDash()

            # Generate QR code
            vote_url = f"{base_url}/vote/{vc.code}"
            qr = qrcode.make(vote_url, box_size=10, border=1)
            qr_buf = io.BytesIO()
            qr.save(qr_buf, format="PNG")
            qr_buf.seek(0)

            qr_img = ImageReader(qr_buf)
            qr_x = x + (cell_w - qr_size) / 2
            qr_y = y + text_area_h
            c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

            # Text below QR code (Courier for clear 0/O distinction)
            c.setFillColorRGB(0, 0, 0)
            text_x = x + cell_w / 2

            c.setFont("Courier-Bold", 10)
            c.drawCentredString(text_x, y + 14 * mm, f"Code: {vc.code}")

            # Class name (if present)
            c.setFont("Helvetica", 7)
            if vc.class_name:
                c.drawCentredString(text_x, y + 9 * mm, f"Klasse {vc.class_name}")
            else:
                c.drawCentredString(text_x, y + 9 * mm, election.name)

            # School name
            if settings.school_name:
                c.setFont("Helvetica", 6)
                c.setFillColorRGB(0.4, 0.4, 0.4)
                c.drawCentredString(text_x, y + 4 * mm, settings.school_name)

    c.save()
    buf.seek(0)

    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"wahlcodes_{election.name}_{election.year}{'_' + filter_class if filter_class else ''}.pdf",
    )


# ---------------------------------------------------------------------------
# Ergebnisse
# ---------------------------------------------------------------------------

@app.route("/admin/election/<int:election_id>/results")
@admin_required
def admin_results(election_id: int):
    election = Election.query.get_or_404(election_id)
    return render_template("admin/results.html", election=election)


@app.route("/admin/election/<int:election_id>/present")
@admin_required
def admin_present(election_id: int):
    election = Election.query.get_or_404(election_id)
    return render_template("admin/present.html", election=election)


@app.route("/api/election/<int:election_id>/results")
@admin_required
def api_results(election_id: int):
    election = Election.query.get_or_404(election_id)
    candidates = Candidate.query.filter_by(election_id=election_id).all()

    results = []
    for c in candidates:
        count = Vote.query.filter_by(election_id=election_id, candidate_id=c.id).count()
        results.append({"name": c.name, "class_name": c.class_name, "votes": count})

    results.sort(key=lambda r: r["votes"], reverse=True)

    total_codes = VotingCode.query.filter_by(election_id=election_id).count()
    used_codes = VotingCode.query.filter_by(election_id=election_id, is_used=True).count()

    return jsonify({
        "results": results,
        "total_codes": total_codes,
        "used_codes": used_codes,
        "max_votes": election.max_votes,
    })


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

with app.app_context():
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.create_all()
    # Ensure school settings row exists
    get_school_settings()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
