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
mongo = PyMongo(app, ssl=True, ssl_cert_reqs='CERT_NONE')


@app.route("/")
@app.route("/index")
def index():
    """
    Main view. It loads all active posts for browse and search
    """
    # fill the name, title and description dinamically to each page
    section = {
        "view": "Portuglish",
        "title": "The Survival Glossary for Brazilians Abroad"}
    # get only active posts
    posts = list(mongo.db.posts.find({"active": "1"}).sort('created', -1))
    return render_template("index.html", posts=posts, section=section)


@app.route("/search", methods=["GET", "POST"])
def search():
    """
    The search feature on the main view between the published and active posts
    """
    section = {
        "view": "Portuglish",
        "title": "The Survival Glossary for Brazilians Abroad"}
    query = request.form.get("query")
    if query == '':
        return redirect(url_for("index"))
    posts = list(mongo.db.posts.find(
                {"$text": {"$search": query}}).sort('created', -1))
    return render_template("index.html", posts=posts, section=section)


@app.route("/about")
def about():
    """
    Static view. It brings the project conception explanation.
    """
    section = {
        "view": "About",
        "title": "The Survival Glossary for Brazilians Abroad"}
    return render_template("about.html", section=section)


@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    """
    The feature that provides the form to create new Posts
    """
    username = session["user"]
    section = {
        "view": "New Post",
        "title": f"Hi, {username}! We can't wait for your ideas"}
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
    return render_template(
                            "create_post.html",
                            categories=categories,
                            section=section,
                            username=session["user"])


@app.route("/edit_post/<_id>", methods=["GET", "POST"])
def edit_post(_id):
    """
    The feature that provides the form to update some post
    """
    section = {
        "view": "Edit Post",
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
        mongo.db.posts.update({"_id": ObjectId(_id)}, post)
        flash("Task Successfully Updated", category='success')

    post = mongo.db.posts.find_one({"_id": ObjectId(_id)})
    categories = mongo.db.categories.find().sort("name", 1)
    return render_template(
                            "edit_post.html",
                            post=post,
                            categories=categories,
                            section=section,
                            username=session["user"])


@app.route("/delete_post/<_id>")
def delete_post(_id):
    """
    Feature to delete posts.
    """
    mongo.db.posts.remove({"_id": ObjectId(_id)})
    flash("Post Successfully Deleted", category='success')
    return redirect(url_for("profile", username=session["user"]))


@app.route("/like_post/<_id>")
def like_post(_id):
    """
    Feature to allow users to like posts, storing the positive
    votes in the DB
    """
    post = (mongo.db.posts.find_one({"_id": ObjectId(_id)}))
    likes_updated = (int(post['like']) + 1)
    mongo.db.posts.update({"_id": ObjectId(ObjectId(_id))},
                          {"$set": {"like": likes_updated}})
    return redirect(url_for("index"))


@app.route("/dislike_post/<_id>")
def dislike_post(_id):
    """
    Feature to allow users to dislike posts, storing the negative
    votes in the DB
    """
    post = (mongo.db.posts.find_one({"_id": ObjectId(_id)}))
    dislikes_updated = (int(post['dislike']) + 1)
    mongo.db.posts.update({"_id": ObjectId(ObjectId(_id))},
                          {"$set": {"dislike": dislikes_updated}})
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Form to allow new users to become a collaborator by registering themselves
    """
    section = {
        "view": "Be a collaborator",
        "title": "Help the Brazilian community to better express their ideas"}
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        if existing_user:
            flash(
                "There is another user already registered under this e-Mail",
                category='danger')
            return redirect(url_for("register"))

        register = {
            "name": request.form.get("name"),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("name")
        session["email"] = request.form.get("email").lower()
        flash("Registration Successful!", category='success')
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html", section=section)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Sign in feature, to allow collaborators access the posts manage section
    """
    section = {
        "view": "Sign In",
        "title": "Help the Brazilian community to better express their ideas"}
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
    """
    Feature to allow users to manage their posts, editing, deleting,
    publish and unpublish existent posts
    """
    section = {
        "view": "Welcome",
        "title": f"Hi, {username}! We can't wait for your ideas"}
    if session["user"]:
        # get only all colaborator posts (active/inactive)
        posts = list(mongo.db.posts.find(
                    {"email_creator": session["email"]}).sort('created', -1))
        return render_template(
                                "profile.html",
                                posts=posts,
                                username=session["user"],
                                section=section)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """
    User log out feature
    """
    # remove user from session cookie
    flash("You have been signed out", category='success')
    session.pop("user")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")), debug=False)
