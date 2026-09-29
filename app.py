import os
import sqlite3
import random
from functools import wraps
from flask import Flask, request, redirect, url_for, session, render_template_string, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --------------------------------------------------
# CONFIGURAÇÃO
# --------------------------------------------------

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "gugabet-v3-secret-change-this-key"
)

DATABASE = "gugabet.db"


# --------------------------------------------------
# BANCO DE DADOS
# --------------------------------------------------

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
            balance REAL DEFAULT 1000
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            team TEXT NOT NULL,
            amount REAL NOT NULL,
            odds REAL NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# --------------------------------------------------
# ESTILO
# --------------------------------------------------

BASE_HTML = """
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
    font-family: Arial, Helvetica, sans-serif;
    background:
        radial-gradient(circle at top, #172554 0%, #07111f 45%, #020617 100%);
    color: white;
    min-height: 100vh;
}

.navbar {
    background: rgba(2,6,23,.85);
    border-bottom: 1px solid rgba(255,255,255,.08);
    padding: 18px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 25px;
    font-weight: 800;
}

.logo span {
    color: #22c55e;
}

.navbar a {
    color: white;
    text-decoration: none;
    margin-left: 20px;
}

.container {
    max-width: 1100px;
    margin: 35px auto;
    padding: 0 20px;
}

.card {
    background: rgba(15,23,42,.88);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 25px;
    margin-bottom: 20px;
    box-shadow: 0 15px 40px rgba(0,0,0,.25);
}

.hero {
    text-align: center;
    padding: 45px 20px;
}

.hero h1 {
    font-size: 42px;
    margin: 0 0 10px;
}

.hero p {
    color: #cbd5e1;
}

.balance {
    font-size: 30px;
    color: #22c55e;
    font-weight: bold;
}

input {
    width: 100%;
    padding: 13px;
    margin: 8px 0 15px;
    border-radius: 10px;
    border: 1px solid #334155;
    background: #020617;
    color: white;
}

button {
    width: 100%;
    padding: 13px;
    border: none;
    border-radius: 10px;
    background: #22c55e;
    color: #04120a;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    background: #16a34a;
}

.match {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    padding: 20px;
    border-radius: 14px;
    background: #0f172a;
    margin-bottom: 15px;
}

.team {
    font-size: 19px;
    font-weight: bold;
}

.odds {
    color: #22c55e;
    font-weight: bold;
}

.small {
    color: #94a3b8;
    font-size: 14px;
}

.error {
    background: #7f1d1d;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 15px;
}

.success {
    background: #14532d;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 15px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #334155;
}

@media(max-width:700px) {

    .match {
        flex-direction: column;
        align-items: stretch;
    }

    .hero h1 {
        font-size: 32px;
    }

}

</style>
</head>

<body>

<div class="navbar">

    <div class="logo">
        🎯 Guga<span>Bet</span> V3
    </div>

    <div>

    {% if session.get("user_id") %}
        <a href="{{ url_for('dashboard') }}">Dashboard</a>
        <a href="{{ url_for('logout') }}">Sair</a>
    {% else %}
        <a href="{{ url_for('login') }}">Login</a>
        <a href="{{ url_for('register') }}">Criar conta</a>
    {% endif %}

    </div>

</div>

<div class="container">

{% with messages = get_flashed_messages(with_categories=true) %}

    {% for category, message in messages %}

        <div class="{{ category }}">
            {{ message }}
        </div>

    {% endfor %}

{% endwith %}

{{ content|safe }}

</div>

</body>
</html>
"""


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():

    content = """
    <div class="card hero">

        <h1>🎯 GugaBet V3</h1>

        <p>
            Simulador esportivo com créditos virtuais.
        </p>

        <br>

        <a href="/register">
            <button>Criar minha conta</button>
        </a>

        <br><br>

        <a href="/login">
            <button style="background:#334155;color:white;">
                Entrar
            </button>
        </a>

        <br><br>

        <div class="small">
            ⚠️ Projeto demonstrativo.
            Não utiliza dinheiro real.
        </div>

    </div>
    """

    return render_template_string(
        BASE_HTML,
        content=content
    )


# --------------------------------------------------
# REGISTRO
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3:
            flash("O usuário precisa ter pelo menos 3 caracteres.", "error")
            return redirect(url_for("register"))

        if len(password) < 4:
            flash("A senha precisa ter pelo menos 4 caracteres.", "error")
            return redirect(url_for("register"))

        conn = get_db()

        try:

            conn.execute(
                """
                INSERT INTO users (username, password, balance)
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

            flash("Esse usuário já existe.", "error")

            return redirect(url_for("register"))

        conn.close()

        flash(
            "Conta criada! Você recebeu 1.000 créditos virtuais.",
            "success"
        )

        return redirect(url_for("login"))

    content = """
    <div class="card">

        <h2>🚀 Criar conta</h2>

        <form method="POST">

            <label>Usuário</label>

            <input
                type="text"
                name="username"
                placeholder="Digite seu usuário"
                required
            >

            <label>Senha</label>

            <input
                type="password"
                name="password"
                placeholder="Digite sua senha"
                required
            >

            <button type="submit">
                Criar conta
            </button>

        </form>

    </div>
    """

    return render_template_string(
        BASE_HTML,
        content=content
    )


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

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

        flash("Usuário ou senha incorretos.", "error")

    content = """
    <div class="card">

        <h2>🔐 Login</h2>

        <form method="POST">

            <label>Usuário</label>

            <input
                type="text"
                name="username"
                required
            >

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

    return render_template_string(
        BASE_HTML,
        content=content
    )


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

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

    matches = [
        ("Flamengo", "Palmeiras", 1.80, 2.10),
        ("Barcelona", "Real Madrid", 2.20, 1.75),
        ("Lakers", "Celtics", 1.90, 1.95),
        ("Chiefs", "49ers", 1.85, 2.00),
    ]

    matches_html = ""

    for i, match in enumerate(matches):

        home, away, odd_home, odd_away = match

        matches_html += f"""
        <div class="match">

            <div>
                <div class="team">{home}</div>
                <div class="small">vs</div>
                <div class="team">{away}</div>
            </div>

            <div>

                <form method="POST"
                      action="/bet"
                      style="margin-bottom:10px;">

                    <input type="hidden"
                           name="team"
                           value="{home}">

                    <input type="hidden"
                           name="odds"
                           value="{odd_home}">

                    <input type="number"
                           name="amount"
                           placeholder="Créditos"
                           min="1"
                           step="1"
                           required>

                    <button type="submit">
                        {home} — {odd_home}
                    </button>

                </form>

                <form method="POST"
                      action="/bet">

                    <input type="hidden"
                           name="team"
                           value="{away}">

                    <input type="hidden"
                           name="odds"
                           value="{odd_away}">

                    <input type="number"
                           name="amount"
                           placeholder="Créditos"
                           min="1"
                           step="1"
                           required>

                    <button type="submit"
                            style="background:#2563eb;color:white;">

                        {away} — {odd_away}

                    </button>

                </form>

            </div>

        </div>
        """

    history_html = ""

    for bet in bets:

        history_html += f"""
        <tr>
            <td>{bet["team"]}</td>
            <td>{bet["amount"]:.0f}</td>
            <td>{bet["odds"]:.2f}</td>
            <td>{bet["status"]}</td>
        </tr>
        """

    content = f"""

    <div class="card">

        <h2>👋 Olá, {user["username"]}</h2>

        <p class="small">
            Seu saldo virtual
        </p>

        <div class="balance">
            {user["balance"]:.2f} créditos
        </div>

    </div>

    <div class="card">

        <h2>🏆 Eventos disponíveis</h2>

        <p class="small">
            Escolha um resultado e utilize seus créditos virtuais.
        </p>

        {matches_html}

    </div>

    <div class="card">

        <h2>📊 Histórico</h2>

        <table>

            <tr>
                <th>Time</th>
                <th>Valor</th>
                <th>Cotação</th>
                <th>Status</th>
            </tr>

            {history_html}

        </table>

    </div>

    """

    return render_template_string(
        BASE_HTML,
        content=content
    )


# --------------------------------------------------
# CRIAR SIMULAÇÃO
# --------------------------------------------------

@app.route("/bet", methods=["POST"])
@login_required
def bet():

    team = request.form.get("team")
    odds = float(request.form.get("odds", 0))
    amount = float(request.form.get("amount", 0))

    if amount <= 0:
        flash("Digite um valor válido.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if amount > user["balance"]:

        conn.close()

        flash(
            "Você não possui créditos suficientes.",
            "error"
        )

        return redirect(url_for("dashboard"))

    # Simulação simples
    won = random.choice([True, False])

    if won:

        payout = amount * odds
        new_balance = user["balance"] - amount + payout

        status = "GANHOU"
        result = "WIN"

    else:

        new_balance = user["balance"] - amount

        status = "PERDEU"
        result = "LOSS"

    conn.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE id = ?
        """,
        (
            new_balance,
            session["user_id"]
        )
    )

    conn.execute(
        """
        INSERT INTO bets
        (user_id, team, amount, odds, status, result)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            team,
            amount,
            odds,
            status,
            result
        )
    )

    conn.commit()
    conn.close()

    if won:

        flash(
            f"🎉 Resultado: GANHOU! +{payout:.2f} créditos.",
            "success"
        )

    else:

        flash(
            f"Resultado: perdeu {amount:.2f} créditos.",
            "error"
        )

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# --------------------------------------------------
# STATUS
# --------------------------------------------------

@app.route("/status")
def status():

    return {
        "status": "online",
        "version": "GugaBet V3",
        "mode": "virtual_credits_only"
    }


# --------------------------------------------------
# INICIAR BANCO
# --------------------------------------------------

init_db()


# --------------------------------------------------
# RODAR LOCALMENTE
# --------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
