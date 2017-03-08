import os
import random
import re
from flask import Flask, render_template, redirect, url_for, request
from flask_httpauth import HTTPBasicAuth
import mysql.connector as mariadb

from config import db_host, db_user, db_password, db_name, users

app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

@app.route('/')
def main():
    try:
        mariadb_connection = get_db_connection()
        cursor = mariadb_connection.cursor(buffered=True)
        cursor.execute('SELECT id FROM comments_07_03 WHERE sentiment IS NULL ORDER BY RAND() LIMIT 1')
        rows = cursor.fetchall()
        if cursor.rowcount == 0:
            return render_template('alldone.html')
        else:
            # commentid = random.choice(rows)[0]
            commentid = rows[0][0]
            return redirect(url_for('getcomment', commentid=commentid))
    finally:
        mariadb_connection.close()


@app.route('/comments/<commentid>')
def getcomment(commentid):
    # open database connection
    mariadb_connection = get_db_connection()

    # get post info from the database
    cursor = mariadb_connection.cursor(buffered=True)
    cursor.execute(
        'SELECT comment_text FROM comments_07_03 WHERE id = "' + str(commentid) + '"')
    if cursor.rowcount == 0 or cursor.rowcount > 1:
        raise ValueError

    text = cursor.fetchall()[0][0]
    comment = {'text': text, 'id': commentid}
    mariadb_connection.close()

    return render_template('index.html', comment=comment)


@app.route('/save', methods=["POST"])
@auth.login_required
def save():
    mariadb_connection = get_db_connection()
    cursor = mariadb_connection.cursor(buffered=True)
    if request.form['sentiment'] == 'spam':
        stmt = "UPDATE comments_07_03 SET spam = %s WHERE id = %s"
        cursor.execute(stmt, ("1", request.form['id']))
    else:
        stmt = "UPDATE comments_07_03 SET sentiment = %s WHERE id = %s"
        cursor.execute(stmt, (request.form['sentiment'], request.form['id']))

    mariadb_connection.commit()
    mariadb_connection.close()
    return main()


def get_db_connection():
    return mariadb.connect(host=db_host, user=db_user, password=db_password,
                           database=db_name)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)  # NOSONAR
