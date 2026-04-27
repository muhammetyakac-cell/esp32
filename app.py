import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import Any

import requests
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY", "dev-secret-change-me")
app.config["DATABASE_PATH"] = os.getenv("DATABASE_PATH", "dzy_panel.db")


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    customer_name: str
    supabase_url: str
    supabase_anon_key: str
    is_admin: int


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        supabase_url TEXT,
        supabase_anon_key TEXT,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    with closing(sqlite3.connect(app.config["DATABASE_PATH"])) as conn:
        conn.executescript(schema)
        conn.commit()

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    db = get_db()
    existing_admin = db.execute(
        "SELECT id FROM users WHERE username = ?", (admin_username,)
    ).fetchone()
    if not existing_admin:
        db.execute(
            """
            INSERT INTO users(username, password_hash, customer_name, supabase_url, supabase_anon_key, is_admin)
            VALUES (?, ?, ?, '', '', 1)
            """,
            (admin_username, generate_password_hash(admin_password), "DZY Admin"),
        )
        db.commit()


def query_user_by_username(username: str) -> User | None:
    row = get_db().execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    if not row:
        return None
    return User(**dict(row))


def current_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return None
    return User(**dict(row))


def require_login() -> User | None:
    user = current_user()
    if not user:
        return None
    return user


def fetch_supabase_telemetry(user: User, limit: int = 50) -> tuple[list[dict[str, Any]], str | None]:
    if not user.supabase_url or not user.supabase_anon_key:
        return [], "Bu kullanıcı için Supabase bilgisi girilmemiş."

    endpoint = (
        f"{user.supabase_url.rstrip('/')}/rest/v1/telemetry"
        f"?select=*&order=created_at.desc&limit={limit}"
    )

    headers = {
        "apikey": user.supabase_anon_key,
        "Authorization": f"Bearer {user.supabase_anon_key}",
    }

    try:
        resp = requests.get(endpoint, headers=headers, timeout=10)
        if resp.status_code >= 400:
            return [], f"Supabase hatası: HTTP {resp.status_code}"
        data = resp.json()
        if not isinstance(data, list):
            return [], "Supabase yanıt formatı beklenenden farklı."
        return data, None
    except requests.RequestException as exc:
        return [], f"Supabase bağlantı hatası: {exc}"


@app.route("/")
def index():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user.is_admin:
        return redirect(url_for("admin_panel"))
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = query_user_by_username(username)
        if not user or not check_password_hash(user.password_hash, password):
            flash("Kullanıcı adı veya şifre yanlış.", "error")
            return render_template("login.html")

        session["user_id"] = user.id
        flash("Giriş başarılı.", "success")
        return redirect(url_for("admin_panel" if user.is_admin else "dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış yapıldı.", "success")
    return redirect(url_for("login"))


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    user = require_login()
    if not user:
        return redirect(url_for("login"))
    if not user.is_admin:
        flash("Bu sayfa sadece admin içindir.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        customer_name = request.form.get("customer_name", "").strip()
        supabase_url = request.form.get("supabase_url", "").strip()
        supabase_anon_key = request.form.get("supabase_anon_key", "").strip()

        if not username or not password or not customer_name:
            flash("username, password ve customer_name zorunlu.", "error")
            return redirect(url_for("admin_panel"))

        try:
            get_db().execute(
                """
                INSERT INTO users(username, password_hash, customer_name, supabase_url, supabase_anon_key, is_admin)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (
                    username,
                    generate_password_hash(password),
                    customer_name,
                    supabase_url,
                    supabase_anon_key,
                ),
            )
            get_db().commit()
            flash("Yeni kullanıcı oluşturuldu.", "success")
        except sqlite3.IntegrityError:
            flash("Bu kullanıcı adı zaten mevcut.", "error")

        return redirect(url_for("admin_panel"))

    users = get_db().execute(
        "SELECT id, username, customer_name, supabase_url, is_admin, created_at FROM users ORDER BY id DESC"
    ).fetchall()
    return render_template("admin.html", users=users, current_user=user)


@app.route("/dashboard")
def dashboard():
    user = require_login()
    if not user:
        return redirect(url_for("login"))

    telemetry, error = fetch_supabase_telemetry(user)
    return render_template(
        "dashboard.html",
        current_user=user,
        telemetry=telemetry,
        error=error,
    )


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
