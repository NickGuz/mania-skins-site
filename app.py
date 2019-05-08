from flask import Flask, flash, render_template, request, send_from_directory
from flask_basicauth import BasicAuth
from helpers import alert_page, download_skin, sql_execute
import sqlite3

# create flask instance
app = Flask(__name__)

# set up config file
app.config.from_pyfile("config.cfg")

# set up basic security for admin panel
basic_auth = BasicAuth(app)


@app.route("/")
def index():
    """ The main skins page """

    skinData = sql_execute("SELECT Name, Link, Image FROM Skins WHERE Approved = 1", ())
    return render_template("main.html", skinData=skinData)


@app.route("/submit", methods=["GET", "POST"])
def submit():
    """ Submit a new skin page """

    # run this if user submits form for new skin
    if request.method == "POST":

        # ensure user enters a name
        if not request.form.get("skinName"):
            return alert_page("You must provide a skin name!")

        # ensure user enters a url
        elif not request.form.get("skinUrl"):
            return alert_page("You must provide a skin url!")
        
        # insert skin into db
        vals = (request.form.get("skinName"), request.form.get("skinUrl"))
        sql_execute("INSERT INTO Skins (Name, Link) VALUES (?, ?)", vals)

        return alert_page("Skin submitted! Please wait for it to be approved.")

    return render_template("submit.html")


@app.route("/admin", methods=["GET", "POST"])
@basic_auth.required
def admin():
    """ Admin panel page """
    if request.method == "GET":
        skinData = sql_execute("SELECT Name, Link FROM Skins WHERE Approved = 0", ())
        return render_template("admin.html", skinData=skinData)


@app.route("/approve")
def approve():
    name = request.args.get('name', 0, type=str)

    # download skin first
    t1 = (name,)
    skin_data = sql_execute("SELECT Link FROM Skins WHERE Name = ?", t1)
    img = download_skin(skin_data[0][0], name)

    # then set to new link in our directory
    t2 = (f"/skins/{name}.osk", img, name)
    sql_execute("UPDATE Skins SET Approved = 1, Link = ?, Image = ? WHERE Name = ?", t2)

    print("success")
    return "Nothing"


@app.route("/skins/<path:filename>")
def download_file(filename):
    return send_from_directory(app.config["DOWNLOAD_FOLDER"], filename, as_attachment=True, mimetype="application/octet-stream")