import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, flash, redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# Wraps
def login_required(f):
    '''
    Allow page entry if user logged in
    '''
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user" in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for("login"))

    return wrap


def approval_required(f):
    '''
    Allow page entry if approved user
    '''
    @wraps(f)
    def wrap(*args, **kwargs):
        if mongo.db.hiveMembers.find_one(
                {"_id": ObjectId(session["user_id"]), "approvedMember": True}):
            return f(*args, **kwargs)
        else:
            flash("This page will become viewable once\
                your membership has been approved")
            return redirect(url_for("home"))

    return wrap


def no_demo(f):
    '''
    Allow page entry if not demo user
    '''
    @wraps(f)
    def wrap(*args, **kwargs):
        if mongo.db.hiveMembers.find_one(
                {"_id": ObjectId(session["user_id"]),
                 "password": {"$exists": True}}):
            return f(*args, **kwargs)
        else:
            flash("Not available in Demo version")
            return redirect(url_for("home"))

    return wrap


def queen_bee_required(f):
    '''
    Allow page entry if user is Queen Bee
    '''
    @wraps(f)
    def wrap(*args, **kwargs):
        if session["member_type"] == "Queen Bee":
            return f(*args, **kwargs)
        else:
            flash("This page is only accessible to Queen Bees")
            return redirect(url_for("home"))

    return wrap


# Functions
def set_session_variables(user, member_type):
    '''
    Set session variables
    '''
    session["user"] = user
    session["username"] = mongo.db.hiveMembers.find_one(
        {"email": session["user"]})["username"]
    session["user_id"] = str(mongo.db.hiveMembers.find_one(
        {"email": session["user"]})["_id"])
    session["hive"] = str(mongo.db.hiveMembers.find_one(
        {"email": session["user"]})["hive"])
    session["member_type"] = member_type
    return


def get_unapproved_members():
    '''
    List members waiting for membership approval
    '''
    unapproved_members = list(mongo.db.hiveMembers.find(
            {"hive": ObjectId(session["hive"]), "approvedMember": False}))
    return unapproved_members


def get_first_collections():
    '''
    List all first collections waiting for approval
    '''
    first_collections = list(mongo.db.firstCollection.find(
        {"hive": ObjectId(session["hive"])}))
    return first_collections


def get_unapproved_collections():
    '''
    List all public collections waiting for approval
    '''
    unapproved_collections = list(mongo.db.publicCollections.find(
        {"hive": ObjectId(session["hive"]), "approvedCollection": False}))
    return unapproved_collections


def create_unnested_list(collection):
    original_list = list(mongo.db[collection].find(
        {}, {"memberID": 1, "_id": 0}))
    unnested_list = list(
        [document["memberID"] for document in original_list])
    return unnested_list


def combine_dictionaries(dict1, dict2):
    '''
    Combine public and private dictionaries into one
    '''
    for item in dict1:
        if item not in dict2:
            dict2.append(item)
            dict2
            dict2
    return dict2


def pop_variables():
    '''
    Remove all session variables
    '''
    session.pop("user")
    session.pop("username")
    session.pop("user_id")
    session.pop("hive")
    session.pop("member_type")
    return


def check_existing_category(value):
    '''
    Check whether field/value already exists
    '''
    mongo.db.itemCategory.find_one(
                {"categoryName_lower": value})
    return


def check_existing_item(value1, value2):
    '''
    Check whether item already exists
    '''
    mongo.db.recyclableItems.find_one(
                {"typeOfWaste_lower": value1,
                 "categoryID": value2})
    return


def get_user_locations(user_id):
    '''
    Get list of users locations
    '''
    locations = list(mongo.db.collectionLocations.find(
        {"memberID": user_id}).sort("nickname"))
    return locations


def get_unapproved_public(user_id):
    '''
    Get list of unapproved public collections
    '''
    unapproved_public_collections = list(mongo.db.publicCollections.find(
            {"memberID": user_id}).sort("businessName"))
    return unapproved_public_collections


def awaiting_approval(user_id):
    '''
    Check whether user has first collection awaiting approval
    '''
    awaiting_approval = list(mongo.db.firstCollection.find_one(
            {"memberID": user_id}))
    return awaiting_approval


def add_new_category():
    '''
    Add new category and return its ID
    '''
    new_category = {
        "categoryName": request.form.get("newItemCategory"),
        "categoryName_lower": request.form.get(
            "newItemCategory").lower()
    }
    mongo.db.itemCategory.insert_one(new_category)
    category_id = mongo.db.itemCategory.find_one(
            {"categoryName_lower": request.form.get(
                "newItemCategory").lower()})["_id"]
    return category_id


def add_new_item_(category_id):
    '''
    Add new item and return its ID
    '''
    new_type_of_waste = {
        "typeOfWaste": request.form.get("newTypeOfWaste"),
        "typeOfWaste_lower": request.form.get(
            "newTypeOfWaste").lower(),
        "categoryID": category_id
    }
    mongo.db.recyclableItems.insert_one(new_type_of_waste)
    item_id = mongo.db.recyclableItems.find_one(
            {"typeOfWaste_lower": request.form.get(
                "newTypeOfWaste").lower()})["_id"]
    return item_id


def default_charity_scheme():
    '''
    Check charity scheme and replace with '-' if null
    '''
    charityScheme = request.form.get("charityScheme")
    if charityScheme == "":
        charityScheme = "-"
    return charityScheme


def new_private_collection(item_id, charityScheme, user_id):
    '''
    Add new collection details to db
    '''
    new_collection = {
        "itemID": item_id,
        "conditionNotes": request.form.get("conditionNotes"),
        "charityScheme": charityScheme,
        "memberID": user_id,
        "locationID": mongo.db.collectionLocations.find_one(
            {"nickname_lower": request.form.get("locationID").lower(),
                "memberID": user_id})["_id"],
        "dateAdded": datetime.now().strftime("%d %b %Y")
    }
    mongo.db.itemCollections.insert_one(new_collection)
    flash("New collection added")
    return
