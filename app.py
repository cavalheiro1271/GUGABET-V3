import os
import sqlite3
import random
from functools import wraps

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    render_template_string,
    flash
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "gugabet-v3-development-key"
)

DATABASE = "gugabet.db"


# =========================================================
# BANCO DE DADOS
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            credits INTEGER DEFAULT 1000,
            is_admin INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sport TEXT NOT NULL,
            event TEXT NOT NULL,
            selection TEXT NOT NULL,
            odds REAL NOT NULL,
            stake INTEGER NOT NULL,
            result TEXT DEFAULT 'pending',
            payout INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Cria usuário administrador inicial
    admin = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:
        conn.execute(
            """
            INSERT INTO users
            (username, password, credits, is_admin)
            VALUES (?, ?, ?, ?)
            """,
            (
                "admin",
                generate_password_hash("admin123"),
                10000,
                1
            )
        )

    conn.commit()
    conn.close()


init_db()


# =========================================================
# AUTENTICAÇÃO
# =========================================================

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        conn.close()

        if not user or not user["is_admin"]:
            return "Acesso negado.", 403

        return view(*args, **kwargs)

    return wrapped


# =========================================================
# HTML BASE
# =========================================================

BASE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>GugaBet V3</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #08111f;
    color: white;
}

nav {
    background: #0d1b2f;
    padding: 18px 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #20334f;
}

.logo {
    font-size: 24px;
    font-weight: bold;
    color: #32e875;
}

nav a {
    color: white;
    text-decoration: none;
    margin-left: 18px;
}

.container {
    max-width: 1000px;
    margin: 35px auto;
    padding: 20px;
}

.card {
    background: #10233d;
    padding: 25px;
    border-radius: 16px;
    margin-bottom: 20px;
    border: 1px solid #203b60;
}

h1, h2, h3 {
    margin-top: 0;
}

button,
.btn {
    background: #32e875;
    color: #06120b;
    border: none;
    padding: 12px 18px;
    border-radius: 9px;
    font-weight: bold;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
}

input, select {
    width: 100%;
    padding: 12px;
    margin: 8px 0 15px;
    border-radius: 8px;
    border: 1px solid #345276;
    background: #09182b;
    color: white;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 18px;
}

.credit {
    font-size: 28px;
    color: #32e875;
    font-weight: bold;
}

.flash {
    background: #17395d;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

.small {
    color: #9eb0c7;
}

</style>
</head>

<body>

<nav>

<div class="logo">
🚀 GugaBet V3
</div>

<div>

<a href="{{ url_for('home') }}">Início</a>

{% if session.get('user_id') %}
<a href="{{ url_for('dashboard') }}">Minha Conta</a>
<a href="{{ url_for('logout') }}">Sair</a>
{% else %}
<a href="{{ url_for('login') }}">Entrar</a>
<a href="{{ url_for('register') }}">Criar conta</a>
{% endif %}

</div>

</nav>

<div class="container">

{% with messages = get_flashed_messages() %}
{% for message in messages %}
<div class="flash">{{ message }}</div>
{% endfor %}
{% endwith %}

{{ content|safe }}

</div>

</body>
</html>
"""


def render_page(content):
    return render_template_string(
        BASE,
        content=content
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    content = """
    <div class="card" style="text-align:center">

        <h1>🚀 GugaBet V3</h1>

        <p>
            Simulador esportivo com créditos virtuais.
        </p>

        <p class="small">
            Projeto experimental para entretenimento e desenvolvimento.
        </p>

        <br>

        <a class="btn" href="/register">
            Criar minha conta
        </a>

    </div>

    <div class="grid">

        <div class="card">
            <h3>🏆 Esportes</h3>
            <p>Eventos esportivos simulados.</p>
        </div>

        <div class="card">
            <h3>💰 Créditos</h3>
            <p>Comece com créditos virtuais.</p>
        </div>

        <div class="card">
            <h3>📊 Histórico</h3>
            <p>Acompanhe suas simulações.</p>
        </div>

    </div>
    """

    return render_page(content)


# =========================================================
# CADASTRO
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            flash("Preencha todos os campos.")
            return redirect(url_for("register"))

        conn = get_db()

        try:

            conn.execute(
                """
                INSERT INTO users
                (username, password, credits)
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    generate_password_hash(password),
                    1000
                )
            )

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            flash("Esse usuário já existe.")
            return redirect(url_for("register"))

        conn.close()

        flash("Conta criada! Agora faça login.")
        return redirect(url_for("login"))

    content = """
    <div class="card">

        <h2>📝 Criar conta</h2>

        <form method="POST">

            <label>Usuário</label>
            <input name="username" required>

            <label>Senha</label>
            <input
                type="password"
                name="password"
                required
            >

            <button type="submit">
                Criar conta
            </button>

        </form>

    </div>
    """

    return render_page(content)


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        flash("Usuário ou senha incorretos.")

    content = """
    <div class="card">

        <h2>🔐 Entrar</h2>

        <form method="POST">

            <label>Usuário</label>
            <input name="username" required>

            <label>Senha</label>
            <input
                type="password"
                name="password"
                required
            >

            <button type="submit">
                Entrar
            </button>

        </form>

    </div>
    """

    return render_page(content)


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    bets = conn.execute(
        """
        SELECT *
        FROM bets
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    content = f"""
    <div class="card">

        <h1>Olá, {user["username"]}! 👋</h1>

        <p>Seu saldo virtual:</p>

        <div class="credit">
            {user["credits"]:,} créditos
        </div>

    </div>

    <div class="card">

        <h2>🏆 Simulador esportivo</h2>

        <p>
            Escolha um evento para fazer uma simulação.
        </p>

        <div class="grid">

            <div class="card">

                <h3>⚽ Futebol</h3>

                <p>Brasil FC x USA FC</p>

                <a class="btn"
                   href="/bet/futebol">
                   Simular
                </a>

            </div>

            <div class="card">

                <h3>🏀 Basquete</h3>

                <p>Raleigh x Charlotte</p>

                <a class="btn"
                   href="/bet/basquete">
                   Simular
                </a>

            </div>

        </div>

    </div>

    <div class="card">

        <h2>📊 Histórico</h2>
    """

    if bets:

        for bet in bets:

            content += f"""
            <p>
            {bet["sport"]} —
            {bet["event"]} —
            {bet["selection"]} —
            {bet["stake"]} créditos
            </p>
            """

    else:

        content += """
        <p class="small">
            Nenhuma simulação ainda.
        </p>
        """

    content += "</div>"

    return render_page(content)


# =========================================================
# APOSTA VIRTUAL
# =========================================================

@app.route("/bet/<sport>", methods=["GET", "POST"])
@login_required
def bet(sport):

    if sport == "futebol":

        event = "Brasil FC x USA FC"

        selections = [
            ("Brasil FC", 1.80),
            ("Empate", 3.20),
            ("USA FC", 2.40)
        ]

    else:

        event = "Raleigh x Charlotte"

        selections = [
            ("Raleigh", 1.70),
            ("Charlotte", 2.10)
        ]

    if request.method == "POST":

        selection = request.form["selection"]
        stake = int(request.form["stake"])

        if stake <= 0:
            flash("Valor inválido.")
            return redirect(request.url)

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        if stake > user["credits"]:

            conn.close()

            flash("Créditos insuficientes.")
            return redirect(request.url)

        odds = dict(selections).get(
            selection,
            1.0
        )

        conn.execute(
            """
            UPDATE users
            SET credits = credits - ?
            WHERE id = ?
            """,
            (stake, session["user_id"])
        )

        conn.execute(
            """
            INSERT INTO bets
            (user_id, sport, event, selection, odds, stake)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                sport,
                event,
                selection,
                odds,
                stake
            )
        )

        conn.commit()

        conn.close()

        flash("Simulação registrada!")
        return redirect(url_for("dashboard"))

    options = ""

    for name, odds in selections:

        options += f"""
        <option value="{name}">
            {name} — odd {odds}
        </option>
        """

    content = f"""
    <div class="card">

        <h2>🏆 {event}</h2>

        <form method="POST">

            <label>Escolha</label>

            <select name="selection">
                {options}
            </select>

            <label>
                Créditos virtuais
            </label>

            <input
                type="number"
                name="stake"
                min="1"
                required
            >

            <button type="submit">
                Confirmar simulação
            </button>

        </form>

    </div>
    """

    return render_page(content)


# =========================================================
# ADMIN
# =========================================================

@app.route("/admin")
@admin_required
def admin():

    conn = get_db()

    users = conn.execute(
        "SELECT id, username, credits, is_admin FROM users"
    ).fetchall()

    bets = conn.execute(
        "SELECT * FROM bets ORDER BY id DESC LIMIT 20"
    ).fetchall()

    conn.close()

    content = """
    <div class="card">

        <h1>⚙️ Painel Administrativo</h1>

        <h2>Usuários</h2>
    """

    for user in users:

        content += f"""
        <p>
        #{user["id"]}
        — {user["username"]}
        — {user["credits"]:,} créditos
        </p>
        """

    content += """
        <h2>Últimas simulações</h2>
    """

    for bet_item in bets:

        content += f"""
        <p>
        {bet_item["username"] if "username" in bet_item.keys() else ""}
        {bet_item["sport"]}
        —
        {bet_item["selection"]}
        —
        {bet_item["stake"]} créditos
        </p>
        """

    content += "</div>"

    return render_page(content)


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
