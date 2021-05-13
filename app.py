import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
if os.path.exists("env.py"):
    import env


# flask app object
app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


# mongo obj flask app connection
mongo = PyMongo(app, ssl=True,ssl_cert_reqs='CERT_NONE')


@app.route("/")
@app.route("/index")
def index():
    # fill the name, title and description dinamically to each page by page header on base template    
    section = { "view": "Portuglish"  ,
                "title": "The Survival Glossary for Brazilians Abroad"}    
    # get only active posts
    posts = list(mongo.db.posts.find({"active": "1"}).sort('created', -1))
    return render_template("index.html", posts=posts, section=section)


@app.route("/about")
def about():
    section = { "view": "About"  ,
                "title": "The Survival Glossary for Brazilians Abroad"}    
    return render_template("about.html", section=section)


@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    section = { "view": "New Post"  ,
                "title": "The Survival Glossary for Brazilians Abroad"}    
    if request.method == "POST":
        active = "1" if request.form.get("active") == "on" else "0"        
        post = {
            "category": request.form.get("category"),
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "active": active,
            "created": datetime.now().strftime("%d %B, %Y"),
            "like": 0,
            "dislike": 0,
            "email_creator": session["email"]
        }
        mongo.db.posts.insert_one(post)
        flash("Post Successfully Added", category='success')
        return redirect(url_for("index"))

    categories = mongo.db.categories.find().sort("name", 1)
    return render_template("create_post.html", categories=categories, section=section) 


@app.route("/delete_post/<_id>")
def delete_post(_id):
    mongo.db.posts.remove({"_id": ObjectId(_id)})
    flash("Post Successfully Deleted")
    return redirect(url_for("profile"))


@app.route("/register", methods=["GET", "POST"])
def register():
    section = { "view": "Be a collaborator"  ,
                "title": "The Survival Glossary for Brazilians Abroad"}         
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        if existing_user:
            flash("There is another user already registered under this e-Mail", category='danger')
            return redirect(url_for("register"))

        register = {
            "name": request.form.get("name"),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("name").lower()
        session["email"] = request.form.get("email").lower()                
        flash("Registration Successful!", category='success')
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html", section=section)


@app.route("/login", methods=["GET", "POST"])
def login():
    section = { "view": "Portuglish"  ,
                "title": "The Survival Glossary for Brazilians Abroad"}        
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = existing_user["name"]
                        session["email"] = existing_user["email"]                        
                        flash("Welcome, {}".format(
                             existing_user["name"]), category='success')
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password", category='danger')
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html", section=section)


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    section = { "view": "Colaborator Profile"  ,
                "title": "Manage here your posts"}       
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"email": session["email"]})["name"]

    
    if session["user"]:
        # get only all colaborator posts (active/inactive)
        posts = list(mongo.db.posts.find({"email_creator": session["email"]}).sort('created', -1))
        return render_template("profile.html", posts=posts, username=username, section=section)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been signed out", category='success')
    session.pop("user")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)