import os
from datetime import datetime
from flask import Flask, flash, render_template, redirect, request, \
    session, url_for

from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, \
    check_password_hash
if os.path.exists('env.py'):
    import env

app = Flask(__name__)

app.config['MONGO_DBNAME'] = os.environ.get('MONGO_DBNAME')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.secret_key = os.environ.get('SECRET_KEY')

mongo = PyMongo(app)


@app.route('/')
@app.route('/get_recipes')
def get_recipes():
    recipes = list(mongo.db.recipes.find())
    return render_template('all_recipes.html', recipes=recipes)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return render_template("all_recipes.html", recipes=recipes)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        # check if username already exists in db

        existing_user = \
            mongo.db.users.find_one({'username': request.form.get('username'
                                    ).lower()})
        existing_email = \
            mongo.db.email.find_one({'email': request.form.get('email'
                                    ).lower()})

        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))

        if existing_email:
            flash('Email already used!')
            return redirect(url_for('register'))

        register = {'username': request.form.get('username').lower(),
                    'password': generate_password_hash(request.form.get('password'
                    )), 'email': request.form.get('email').lower()}
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie

        session['user'] = request.form.get('username').lower()
        flash('Registration Successful!')
        return redirect(url_for('my_recipes', username=session['user']))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        # check if username exists in db

        existing_user = \
            mongo.db.users.find_one({'username': request.form.get('username'
                                    ).lower()})

        if existing_user:

            # ensure hashed password matches user input

            if check_password_hash(existing_user['password'],
                                   request.form.get('password')):
                session['user'] = request.form.get('username').lower()
                flash('Welcome, {}'.format(request.form.get('username'
                      )))
                return redirect(url_for('my_recipes',
                                username=session['user']))
            else:

                # invalid password match

                flash('Incorrect Username and/or Password')
                return redirect(url_for('login'))
        else:

            # username doesn't exist

            flash('Incorrect Username and/or Password')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():

    # remove user from session cookie

    flash('You have been logged out')
    session.pop('user')
    return redirect(url_for('login'))


@app.route('/my_recipes/<username>', methods=['POST', 'GET'])
def my_recipes(username):

    if session.get('user'):
        username = session.get('user')
        my_recipes = list(mongo.db.recipes.find({'created_by': username}))

        return render_template('my_recipes.html',
                               username=session['user'],
                               my_recipes=my_recipes)


@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():

    if not session.get('user'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        recipe = {
            'name': request.form.get('name'),
            'diets': request.form.get('diet_name'),
            'allergens': request.form.getlist('allergen_name'),
            'serves': request.form.get('serves'),
            'prep_time': request.form.get('prep_time'),
            'cook_time': request.form.get('cook_time'),
            'description': request.form.get('description'),
            'ingredients': request.form.get('ingredients').split(">"),
            'steps': request.form.get('steps').split(">"),
            'img_url': request.form.get('img_url'),
            'created_by': session['user'],
            'date_created': datetime.now(),
            }

        mongo.db.recipes.insert_one(recipe)
        flash('Recipe successfully posted!')
        return redirect(url_for('my_recipes', username=session['user']))

    diets = mongo.db.diets.find().sort('diet_name', 1)
    allergens = mongo.db.allergens.find().sort('allergen_name', 1)
    return render_template('add_recipe.html', allergens=allergens,
                           diets=diets)


@app.route('/edit_recipe/<recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    if request.method == 'POST':

        submit = {
                'name': request.form.get('name'),
                'diets': request.form.get('diet_name'),
                'allergens': request.form.getlist('allergen_name'),
                'serves': request.form.get('serves'),
                'prep_time': request.form.get('prep_time'),
                'cook_time': request.form.get('cook_time'),
                'description': request.form.get('description'),
                'ingredients': request.form.get('ingredients').split(">"),
                'steps': request.form.get('steps').split(">"),
                'img_url': request.form.get('img_url'),
                'created_by': session['user'],
                'date_created': datetime.now(),
                    }
        mongo.db.recipes.update({'_id': ObjectId(recipe_id)}, submit)
        flash('Recipe updated!')
        return redirect(url_for('my_recipes', username=session['user']))

    recipe = mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})
    diets = mongo.db.diets.find().sort('diet_name', 1)
    allergens = mongo.db.allergens.find().sort('allergen_name', 1)
    return render_template('edit_recipe.html', recipe=recipe,
                           allergens=allergens, diets=diets)


@app.route('/delete_recipe/<recipe_id>')
def delete_recipe(recipe_id):
    recipe_owner = ("recipe.created_by")
    if (session["user"].lower() == recipe_owner.lower()
            or session["user"] == "admin"):
        mongo.db.recipes.remove({'_id': ObjectId(recipe_id)})
        flash('Recipe Successfully Deleted')
        return redirect(url_for('my_recipes', username=session['user']))

    else:
        flash('You Must Be The Recipe Owner Perform This Action')
        return redirect(url_for('get_recipes'))


@app.route("/view_recipe/<recipe_id>", methods=['POST', 'GET'])
def view_recipe(recipe_id):
    recipe = mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})
    return render_template("view_recipe.html", recipe=recipe)


@app.route("/get_diets")
def get_diets():
    diets = list(mongo.db.diets.find().sort("diet_name", 1))
    return render_template("diets.html", diets=diets)


@app.route("/add_diet", methods=["GET", "POST"])
def add_diet():
    if request.method == "POST":
        diet = {
            "diet_name": request.form.get("diet_name")
        }
        mongo.db.diets.insert_one(diet)
        flash("New diet Added")
        return redirect(url_for("get_diets"))

    return render_template("add_diet.html")


@app.route("/edit_diet/<diet_id>", methods=["GET", "POST"])
def edit_diet(diet_id):
    if request.method == "POST":
        submit = {
            "diet_name": request.form.get("diet_name")
        }
        mongo.db.diets.update({"_id": ObjectId(diet_id)}, submit)
        flash("Diet Successfully Updated")
        return redirect(url_for("get_diets"))

    diet_id = mongo.db.diets.find_one({"_id": ObjectId(diet_id)})
    return render_template("edit_diet.html", diet_id=diet_id)


@app.route("/delete_diet/<diet_id>")
def delete_diet(diet_id):
    mongo.db.diets.remove({"_id": ObjectId(diet_id)})
    flash("Diet Successfully Deleted")
    return redirect(url_for("get_diets"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404




if __name__ == '__main__':
    app.run(host=os.environ.get('IP'), port=int(os.environ.get('PORT'
            )), debug=False)
