from flask import Flask, render_template, request, redirect
import sqlite3
import hashlib
import pandas as pd
import os
import json

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


def categorize(payee):

    p = str(payee).upper()

    with open("rules.json", encoding="utf-8") as f:
        rules = json.load(f)

    for category, keywords in rules.items():

        for keyword in keywords:

            if keyword.upper() in p:
                return category

    return "Unkategorisiert"


@app.route("/", methods=["GET", "POST"])
def idx():

    if request.method == "POST":

        f = request.files.get("file")

        if not f:
            return redirect("/")

        if f.filename == "":
            return redirect("/")

        try:

            df = pd.read_csv(
                f,
                sep=";",
                encoding="cp1252"
            )

        except pd.errors.EmptyDataError:

            print("Leere CSV-Datei")
            return redirect("/")

        except Exception as ex:

            print(f"CSV Fehler: {ex}")
            return redirect("/")

        print(df.columns.tolist())
        print(f"Datensätze: {len(df)}")

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
                        categorize(payee)
                    )
                )

            except Exception:
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

@app.route("/rules")
def rules():

    with open("rules.json", encoding="utf-8") as f:
        rules = json.load(f)

    return render_template(
        "rules.html",
        rules=rules
    )

@app.route("/rules/add", methods=["POST"])
def rules_add():

    category = request.form.get("category", "").strip()
    keyword = request.form.get("keyword", "").strip().upper()

    if not category or not keyword:
        return redirect("/rules")

    with open("rules.json", "r", encoding="utf-8") as f:
        rules = json.load(f)

    if category not in rules:
        rules[category] = []

    if keyword not in rules[category]:
        rules[category].append(keyword)

    rules[category] = sorted(rules[category])

    with open("rules.json", "w", encoding="utf-8") as f:
        json.dump(
            rules,
            f,
            indent=2,
            ensure_ascii=False
        )

    return redirect("/rules")

@app.route("/transaction/update_category", methods=["POST"])
def update_category():

    tx_hash = request.form.get("hash")
    category = request.form.get("category")

    con = sqlite3.connect(DB)

    con.execute("""
        UPDATE transactions
        SET category = ?
        WHERE hash = ?
    """, (
        category,
        tx_hash
    ))

    con.commit()
    con.close()

    return redirect("/transactions")


@app.route("/transactions")
def transactions():

    con = sqlite3.connect(DB)

    rows = con.execute("""
        SELECT
            hash,
            date,
            payee,
            amount,
            category
        FROM transactions
        ORDER BY date DESC
    """).fetchall()

    con.close()

    with open("rules.json", encoding="utf-8") as f:
        rules = json.load(f)

    categories = sorted(rules.keys())

    if "Unkategorisiert" not in categories:
        categories.append("Unkategorisiert")
        
    return render_template(
        "transactions.html",
        transactions=rows,
        search="",
        categories=categories
    )


@app.route("/rules/delete")
def rules_delete():

    category = request.args.get("category")
    keyword = request.args.get("keyword")

    with open("rules.json", "r", encoding="utf-8") as f:
        rules = json.load(f)

    if category in rules:

        if keyword in rulesrules[category].remove(keyword)

            if len(rules[category]) == 0:
                del rules[category]

    with open("rules.json", "w", encoding="utf-8") as f:

        json.dump(
            rules,
            f,
            indent=2,
            ensure_ascii=False
        )

    return redirect("/rules")

@app.route("/rules/edit")
def rules_edit():

    category = request.args.get("category")
    keyword = request.args.get("keyword")

    return render_template(
        "rule_edit.html",
        category=category,
        keyword=keyword
    )

@app.route("/rules/update", methods=["POST"])
def rules_update():

    old_category = request.form["old_category"]
    old_keyword = request.form["old_keyword"]

    new_category = request.form["category"]
    new_keyword = request.form["keyword"].upper()

    with open("rules.json", encoding="utf-8") as f:
        rules = json.load(f)

    if old_category in rules:

        if old_keyword in rules[old_category]:

            rules[old_category].remove(old_keyword)

    if len(rules.get(old_category, [])) == 0:

        rules.pop(old_category, None)

    if new_category not in rules:

        rules[new_category] = []

    if new_keyword not in rules[new_category]:

        rules[new_category].append(new_keyword)

    with open("rules.json", "w", encoding
            f,
            indent=2,
            ensure_ascii=False
        )

    return redirect("/rules")

@app.route("/categories")
def categories():

    con = sqlite3.connect(DB)

    rows = con.execute("""
        SELECT
            category,
            COUNT(*),
            ROUND(SUM(amount), 2)
        FROM transactions
        GROUP BY category
        ORDER BY SUM(amount)
    """).fetchall()

    con.close()

    return render_template(
        "categories.html",
        categories=rows
    )


@app.route("/statistics")
def statistics():

    con = sqlite3.connect(DB)

    expense_rows = con.execute("""
        SELECT
            category,
            ROUND(ABS(SUM(amount)), 2)
        FROM transactions
        WHERE amount < 0
        GROUP BY category
        ORDER BY ABS(SUM(amount)) DESC
    """).fetchall()

    income_rows = con.execute("""
        SELECT
            category,
            ROUND(SUM(amount), 2)
        FROM transactions
        WHERE amount > 0
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """).fetchall()

    con.close()

    expense_labels = [r[0] for r in expense_rows]
    expense_values = [r[1] for r in expense_rows]

    income_labels = [r[0] for r in income_rows]
    income_values = [r[1] for r in income_rows]

    return render_template(
        "statistics.html",

        expense_labels=expense_labels,
        expense_values=expense_values,

        income_labels=income_labels,
        income_values=income_values
    )

@app.route("/recategorize")
def recategorize():

    con = sqlite3.connect(DB)

    rows = con.execute("""
        SELECT hash, payee
        FROM transactions
    """).fetchall()

    updated = 0

    for row in rows:

        tx_hash = row[0]
        payee = row[1]

        category = categorize(payee)

        con.execute("""
            UPDATE transactions
            SET category = ?
            WHERE hash = ?
        """, (
            category,
            tx_hash
        ))

        updated += 1

    con.commit()
    con.close()

    print(f"{updated} Buchungen neu kategorisiert")

    return redirect("/categories")

app.run(
    host="0.0.0.0",
    port=5000
)