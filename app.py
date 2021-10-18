import os
from datetime import datetime
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_recipes")
def get_recipes():
    recipes = list(mongo.db.recipes.find())
    return render_template("recipes.html", recipes=recipes)


@app.route("/register.html", methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists!")
            return redirect(url_for("register"))

        existing_email = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        if existing_email:
            flash("Email already used!")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "email": request.form.get("email").lower()
            }
        mongo.db.users.insert_one(register)

         # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful")
        return render_template("register.html", username=session["user"])
        #Change to my recipes page when created

    return render_template("register.html")


@app.route("/login.html", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                flash("Welcome, {}".format(request.form.get("username")))
                session["user"] = request.form.get("username").lower()

                return redirect(url_for("login",
                                username=session["user"],
                                redirect_to="login"))
                                # change login to my recipes page when created
            else:
                flash("Username and/or Password Incorrect")
        else:
            flash("Username and/or Password Incorrect")

    return render_template("login.html")


@app.route("/my_recipes/<username>", methods=['POST', 'GET'])
def my_recipes(username):

    if session.get('user'):
        username = session.get('user')

        return render_template("my_recipes.html", username=session["user"])


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():

    if not session.get("user"):
        return redirect(url_for("login"))

    if request.method == "POST":
        recipe = {
             "name": request.form.get("name"),
             "diets": request.form.getlist("diets"),
             "allergens": request.form.getlist("allergens"),
             "serves": request.form.get("serves"),
             "prep_time": request.form.get("prep_time"),
             "cook_time": request.form.get("cook_time"),
             "description": request.form.get("description"),
             "ingredients": request.form.get("ingredients"),
             "steps": request.form.get("steps"),
             "img_url": request.form.get("img_url"),
             "created_by": session["user"],
             "date_created": datetime.now()
            }

        mongo.db.recipes.insert_one(recipe)
        flash("Recipe successfully posted!")
        return redirect(url_for("my_recipes", username=session['user']))

    diets = mongo.db.diets.find().sort("diet_name", 1)
    allergens = mongo.db.allergens.find().sort("allergen_name", 1)
    return render_template(
        "add_recipe.html", allergens=allergens, diets=diets)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
