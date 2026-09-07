import os
import random
import string
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("UPAY_SECRET_KEY", "dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'upay.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"

STARTING_BALANCE = 5000.00  # every new user starts with fake demo money

NETWORKS = ["MTN", "Airtel", "Glo", "9mobile"]
BILLERS = ["Electricity (EKEDC)", "DSTV Subscription", "Internet (Spectranet)", "Water Bill"]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    pin_hash = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Float, default=STARTING_BALANCE)
    account_number = db.Column(db.String(12), unique=True, nullable=False)
    avatar_color = db.Column(db.String(7), default="#1a2f6b")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def set_pin(self, raw_pin):
        self.pin_hash = generate_password_hash(raw_pin)

    def check_pin(self, raw_pin):
        return check_password_hash(self.pin_hash, raw_pin)

    def initials(self):
        parts = self.full_name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.full_name[:2].upper()


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # whose history this entry is on
    counterparty_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    tx_type = db.Column(db.String(20), nullable=False)  # deposit, transfer_out, transfer_in, airtime, bill
    amount = db.Column(db.Float, nullable=False)
    balance_after = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default="success")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", foreign_keys=[user_id])
    counterparty = db.relationship("User", foreign_keys=[counterparty_id])

    def to_dict(self):
        return {
            "id": self.id,
            "reference": self.reference,
            "tx_type": self.tx_type,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "description": self.description,
            "status": self.status,
            "timestamp": self.timestamp.strftime("%d %b %Y, %H:%M"),
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gen_reference():
    return "UPAY" + "".join(random.choices(string.digits, k=10))


def gen_account_number():
    while True:
        acct = "".join(random.choices(string.digits, k=10))
        if not User.query.filter_by(account_number=acct).first():
            return acct


def record_transaction(user, tx_type, amount, description, counterparty=None, status="success"):
    tx = Transaction(
        reference=gen_reference(),
        user_id=user.id,
        counterparty_id=counterparty.id if counterparty else None,
        tx_type=tx_type,
        amount=amount,
        balance_after=user.balance,
        description=description,
        status=status,
    )
    db.session.add(tx)
    return tx


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        pin = request.form.get("pin", "").strip()

        error = None
        if not all([full_name, username, phone, password, pin]):
            error = "Please fill in all fields."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif not (pin.isdigit() and len(pin) == 4):
            error = "Transaction PIN must be exactly 4 digits."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."
        elif User.query.filter_by(phone=phone).first():
            error = "That phone number is already registered."

        if error:
            flash(error, "error")
        else:
            colors = ["#1a2f6b", "#0f9d58", "#c2185b", "#f57c00", "#00838f", "#5e35b1"]
            user = User(
                full_name=full_name,
                username=username,
                phone=phone,
                account_number=gen_account_number(),
                avatar_color=colors[User.query.count() % len(colors)],
                balance=STARTING_BALANCE,
            )
            user.set_password(password)
            user.set_pin(pin)
            db.session.add(user)
            db.session.flush()  # get user.id before commit
            record_transaction(
                user, "deposit", STARTING_BALANCE,
                "Welcome bonus — simulated starting balance"
            )
            db.session.commit()
            login_user(user)
            flash("Account created! You've been credited a demo starting balance.", "success")
            return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard & wallet routes
# ---------------------------------------------------------------------------

@app.route("/")
@login_required
def dashboard():
    recent_tx = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.timestamp.desc())
        .limit(6)
        .all()
    )
    return render_template("dashboard.html", recent_tx=recent_tx)


@app.route("/fund", methods=["GET", "POST"])
@login_required
def fund():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            amount = 0

        if amount <= 0:
            flash("Enter a valid amount.", "error")
        elif amount > 500000:
            flash("Simulated funding is capped at ₦500,000 per transaction.", "error")
        else:
            current_user.balance += amount
            record_transaction(
                current_user, "deposit", amount,
                "Wallet funding (simulated card/bank transfer)"
            )
            db.session.commit()
            flash(f"₦{amount:,.2f} added to your wallet.", "success")
            return redirect(url_for("dashboard"))

    return render_template("fund.html")


@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            amount = 0
        note = request.form.get("note", "").strip()
        pin = request.form.get("pin", "").strip()

        recipient = User.query.filter(
            (User.username == identifier) |
            (User.phone == identifier) |
            (User.account_number == identifier)
        ).first()

        error = None
        if not recipient:
            error = "No UPay user found with that username, phone, or account number."
        elif recipient.id == current_user.id:
            error = "You can't send money to yourself."
        elif amount <= 0:
            error = "Enter a valid amount."
        elif amount > current_user.balance:
            error = "Insufficient balance."
        elif not current_user.check_pin(pin):
            error = "Incorrect transaction PIN."

        if error:
            flash(error, "error")
        else:
            current_user.balance -= amount
            recipient.balance += amount

            desc_out = f"Transfer to {recipient.full_name} (@{recipient.username})"
            desc_in = f"Transfer from {current_user.full_name} (@{current_user.username})"
            if note:
                desc_out += f" — {note}"
                desc_in += f" — {note}"

            record_transaction(current_user, "transfer_out", amount, desc_out, counterparty=recipient)
            record_transaction(recipient, "transfer_in", amount, desc_in, counterparty=current_user)
            db.session.commit()

            flash(f"₦{amount:,.2f} sent to {recipient.full_name}.", "success")
            return redirect(url_for("dashboard"))

    return render_template("transfer.html")


@app.route("/airtime", methods=["GET", "POST"])
@login_required
def airtime():
    if request.method == "POST":
        network = request.form.get("network", "")
        phone = request.form.get("phone", "").strip()
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            amount = 0
        pin = request.form.get("pin", "").strip()

        error = None
        if network not in NETWORKS:
            error = "Select a valid network."
        elif not phone:
            error = "Enter a phone number."
        elif amount <= 0:
            error = "Enter a valid amount."
        elif amount > current_user.balance:
            error = "Insufficient balance."
        elif not current_user.check_pin(pin):
            error = "Incorrect transaction PIN."

        if error:
            flash(error, "error")
        else:
            current_user.balance -= amount
            record_transaction(
                current_user, "airtime", amount,
                f"{network} airtime top-up for {phone} (simulated)"
            )
            db.session.commit()
            flash(f"₦{amount:,.2f} {network} airtime sent to {phone} (simulated).", "success")
            return redirect(url_for("dashboard"))

    return render_template("airtime.html", networks=NETWORKS)


@app.route("/bills", methods=["GET", "POST"])
@login_required
def bills():
    if request.method == "POST":
        biller = request.form.get("biller", "")
        account_ref = request.form.get("account_ref", "").strip()
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            amount = 0
        pin = request.form.get("pin", "").strip()

        error = None
        if biller not in BILLERS:
            error = "Select a valid biller."
        elif not account_ref:
            error = "Enter a meter/account/customer number."
        elif amount <= 0:
            error = "Enter a valid amount."
        elif amount > current_user.balance:
            error = "Insufficient balance."
        elif not current_user.check_pin(pin):
            error = "Incorrect transaction PIN."

        if error:
            flash(error, "error")
        else:
            current_user.balance -= amount
            record_transaction(
                current_user, "bill", amount,
                f"{biller} payment — ref {account_ref} (simulated)"
            )
            db.session.commit()
            flash(f"₦{amount:,.2f} paid to {biller} (simulated).", "success")
            return redirect(url_for("dashboard"))

    return render_template("bills.html", billers=BILLERS)


@app.route("/history")
@login_required
def history():
    tx_type = request.args.get("type", "all")
    query = Transaction.query.filter_by(user_id=current_user.id)
    if tx_type != "all":
        query = query.filter_by(tx_type=tx_type)
    transactions = query.order_by(Transaction.timestamp.desc()).all()
    return render_template("history.html", transactions=transactions, active_filter=tx_type)


@app.route("/receipt/<reference>")
@login_required
def receipt(reference):
    tx = Transaction.query.filter_by(reference=reference, user_id=current_user.id).first_or_404()
    return render_template("receipt.html", tx=tx)


@app.route("/api/balance")
@login_required
def api_balance():
    return jsonify({"balance": current_user.balance})


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        if full_name:
            current_user.full_name = full_name
            db.session.commit()
            flash("Profile updated.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html")


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5001)
