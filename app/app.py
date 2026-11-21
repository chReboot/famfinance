from flask import Flask, render_template, request, redirect
import sqlite3
import hashlib
import pandas as pd
import os

app = Flask(__name__)

DB = "/data/finance.db"

os.makedirs("/data", exist_ok=True)

con = sqlite3.connect(DB)
con.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    hash TEXT PRIMARY KEY,
    date TEXT,
    payee TEXT,
    amount REAL,
    category TEXT
)
""")
con.close()


def cat(payee):

    p = (payee or "").upper()

    if "REWE" in p or "EDEKA" in p:
        return "Lebensmittel"

    if "AMAZON" in p:
        return "Shopping"

    return "Unkategorisiert"


@app.route("/", methods=["GET", "POST"])
def idx():

    if request.method == "POST":

        f = request.files["file"]

        df = pd.read_csv(
            f,
            sep=";",
            encoding="cp1252"
        )

        con = sqlite3.connect(DB)

        for _, r in df.iterrows():

            payee = str(
                r.get("Empfänger/Auftraggeber Name", "")
            )

            amount = str(
                r.get("Soll/Haben", "0")
            )

            date = str(
                r.get("Buchungstag", "")
            )

            h = hashlib.sha256(
                f"{date}|{payee}|{amount}".encode()
            ).hexdigest()

            try:

                con.execute(
                    "INSERT INTO transactions VALUES (?,?,?,?,?)",
                    (
                        h,
                        date,
                        payee,
                        float(amount.replace(",", ".")),
                        cat(payee),
                    )
                )

            except:
                pass

        con.commit()
        con.close()

        return redirect("/")

    con = sqlite3.connect(DB)

    stats = con.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(amount),0),
            COALESCE(SUM(CASE WHEN amount > 0 THEN amount END),0),
            COALESCE(SUM(CASE WHEN amount < 0 THEN amount END),0)
        FROM transactions
    """).fetchone()

    con.close()

    return render_template(
        "index.html",
        bookings=stats[0],
        balance=stats[1],
        income=stats[2],
        expenses=stats[3]
    )


@app.route("/transactions")
def transactions():

    con = sqlite3.connect(DB)

    rows = con.execute("""
        SELECT
            date,
            payee,
            amount,
            category
        FROM transactions
        ORDER BY date DESC
    """).fetchall()

    con.close()

    return render_template(
        "transactions.html",
        transactions=rows,
        search=""
    )


app.run(
    host="0.0.0.0",
    port=5000
)