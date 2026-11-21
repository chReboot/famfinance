@app.route('/', methods=['GET', 'POST'])
def idx():

    if request.method == 'POST':

        f = request.files['file']

        df = pd.read_csv(
            f,
            sep=';',
            encoding='cp1252'
        )

        con = sqlite3.connect(DB)

        for _, r in df.iterrows():

            payee = str(
                r.get('Empfänger/Auftraggeber Name', '')
            )

            amount = str(
                r.get('Soll/Haben', '')
            )

            date = str(
                r.get('Buchungstag', '')
            )

            h = hashlib.sha256(
                f'{date}|{payee}|{amount}'.encode()
            ).hexdigest()

            try:
                con.execute(
                    'insert into transactions values(?,?,?,?,?)',
                    (
                        h,
                        date,
                        payee,
                        float(str(amount).replace(',', '.')),
                        cat(payee)
                    )
                )
            except:
                pass

        con.commit()
        con.close()

        return redirect('/')

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
        'index.html',
        bookings=stats[0],
        balance=stats[1],
        income=stats[2],
        expenses=stats[3]
    )