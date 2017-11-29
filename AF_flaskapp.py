import os
import json
import urllib

from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify
from flask_script import Manager, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'comp205'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)


# class User(db.Model):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     name = db.Column(db.String(64), unique=True, nullable=False)
#     # password = db.Column(db.String(64), nullable=False)
#     # picture = db.Column()
#     # recipeList = db.Column(db.String(64))
#     # ingredientList = db.Column(db.String(64))
#     #recipe = db.relationship('Recipe', backref='user', lazy='dynamic')
#
#     def __repr__(self):
#         return '<User %r>' % self.user_name


class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(64), unique=True, nullable=False)
    ingredients = db.Column(db.ForeignKey('ingredients.name'),index=True)
    #prepTime = db.Column(db.TIME(timezone=True))
    #date = db.Column(db.DATE)
    source = db.Column(db.Integer)
    recipePic = db.Column(db.String(256))
    #author = db.Column(db.Integer, db.ForeignKey('users.id'))
    #desc = db.Column(db.String(128), unique=True, index=True)

    def __repr__(self):
        return '<Recipe %r>' % self.title


class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    #desc = db.Column(db.String(128), unique=True, index=True)
    #cost = db.Column(db.DECIMAL(5,2))
    isAllergen = db.Column(db.BOOLEAN)

    def __repr__(self):
        return '<Ingredient %r>' % self.name


class RecipeToIngredient(db.Model):
    __tablename__ = 'recipe_ingredient'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipeID = db.Column(db.ForeignKey('recipes.id'))
    ingredientID = db.Column(db.ForeignKey('ingredients.id'))

    def __repr__(self):
        return '<RecipeToIngredient %r>' % self.ingredient_name

def createDB():
    db.drop_all()
    db.create_all()

createDB()

'''
def searchRecipes():
    #list of all the recipes
    recipeList = Recipe.query.all
    q = request.args.get('q', "") #is this where the query goes?

    matches = list()
    for r in recipeList:
        if r.lower().startswith(q.lower()):
            matches.append(r)

    print(result=matches)
    return jsonify(result=matches)
'''

def jsonParser(indgredientQuery):
    # ALGORITHM
    # for loop that adds each recipe
    # loop again through the ingredients, inside the previous loop
    # check if the ingredient is already in the database and if its an allergen
    # commit recipe and each ingredient to the recipe and ingredient db lists

    url = "http://www.recipepuppy.com/api/?i=onions,garlic"
    r = urllib.request.urlopen(url)
    data = json.loads(r.read().decode(r.info().get_param('charset') or 'utf-8'))
    #print(data)

    #add Recipe data
    for item in data["results"]:
        recipePicture = item["thumbnail"]
        recipeIngredients = item["ingredients"]
        recipeSource = item["href"]
        recipeTitle = item["title"]
        currRecipe = Recipe(title = recipeTitle, ingredients = recipeIngredients,
                            source = recipeSource, recipePic = recipePicture
                            )
        #add the recipe
        db.session.add(currRecipe)

        #add Ingredients data
        allergenList = ["milk", "wheat", "mussels", "anchovies", "eggs", "gluten", "peanuts", "almonds", "soy", "fish", "shellfish"]
        dbIngredientList = [ingredient.name for ingredient in  Ingredient.query.all()]
        #print(dbIngredientList)
        recipeIngredients = recipeIngredients.split(", ")

        for i in recipeIngredients:
            if i in allergenList :
                currIngredient = Ingredient(name = i, isAllergen = True)
                if (i not in dbIngredientList):
                    # flash("That's already in our database!  Thanks")
                    #print("ingredientToAdd: ", i, "That's already in our database!  Thanks")
                    db.session.add(currIngredient)

            else:
                currIngredient = Ingredient(name = i, isAllergen = False)
                if (i not in dbIngredientList):
                    # flash("That's already in our database!  Thanks")
                    #print("ingredientToAdd: ", i, "That's already in our database!  Thanks")
                    db.session.add(currIngredient)

        #commit entries to db
        db.session.commit()



class NewIngredient(Form):
    newIngredient = StringField('New Ingredient', validators=[Required()])
    submit = SubmitField('Submit')

class SearchForm(Form):
    title = StringField('')
    include = StringField('')
    exclude = StringField('')
    exclude_allergens = SelectField(u'', choices=[(True, "Yes"), (False, "No")])
    meal_type = SelectField(u'', choices =[('breakfast', 'Breakfast'), ('lunch', 'Lunch'), ('dinner', 'Dinner')])
    submit = SubmitField('Search')

class NameForm(Form):
    name = StringField('New Recipe Name', validators=[Required()])
    mealType = SelectField('Meal Type', coerce=int, validators=[Required()])
    description = TextAreaField('Description')
    submit = SubmitField('Submit')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/')
def index():
    return redirect(url_for('recipe'))

@app.route('/listsrecipes')
def listsrecipes():
    filter = Recipe.query.all()
    filter = [user.title for user in filter]
    return render_template('listsrecipes.html', alist=filter)

@app.route('/specific/<aname>')
def specific(aname):
    info = Recipe.query.filter_by(name=aname).first()
    if info is not None:
        return render_template('specific.html', recipe=aname, mealType=info.genre.name, description=info.desc)
    else:
        return render_template('404.html'), 404

@app.route('/recipe', methods = ['GET', 'POST'])
def recipe():
    form = SearchForm()
    if form.validate_on_submit():
        title = form.title.data
        include = form.include.data
        exclude = form.exclude.data
        meal_type = form.meal_type.data
        exclude_allergens = form.exclude_allergens.data
        flash('include ='+include+'     exclude ='+exclude)


        #searchRecipes()


        return render_template('recipe.html', SearchForm = form)
    return render_template('recipe.html', SearchForm = form )

@app.route('/extendedrecipe')
def extendedrecipe():
    return render_template('extendedrecipe.html')

@app.route('/newi', methods=['GET', 'POST'])
def newi():
    myForm = NewIngredient()
    if myForm.validate_on_submit():
        brandNewIngredient = Ingredient(title = myForm.newIngredient.data)
        db.session.add(brandNewIngredient)
        flash('This ingredient has been added to the database!')
        return redirect(url_for('new'))
    return render_template('newi.html', thisForm = myForm)

@app.route('/new', methods=['GET', 'POST'])
def new():
    filter = Recipe.query.all()
    filter = [user.name for user in filter]
    form = NameForm()
    form.mealType.choices = [(g.id, g.name) for g in Ingredient.query.all()]
    if form.validate_on_submit():
        brandNewRecipe = Recipe(name = form.name.data, meal_type = form.mealType.data, desc = form.description.data)
        db.session.add(brandNewRecipe)
        flash('Your input has been added to the Recipe List!')
        return redirect(url_for('listsrecipes'))
    return render_template('new.html', form=form)

if __name__ == '__main__':

    jsonParser("onions")
    app.run()

    # app.run when uploading
    # manager.run when editing






