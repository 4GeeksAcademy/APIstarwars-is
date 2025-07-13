"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, Blueprint
from flask_migrate import Migrate
from flasgger import Swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity

app = Flask(__name__)
app.url_map.strict_slashes = False

# Swagger UI
Swagger(app)

# Database config
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT config
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-key")
jwt = JWTManager(app)

# Initialize extensions
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Create blueprint for api routes
api = Blueprint('api', __name__)

# --- API ENDPOINTS ---

# Hello world test
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():
    return jsonify({"msg": "Hello, this is your GET /user response"}), 200

# Example register user (not required, since you add users via admin)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400
    user = User(email=email, password=password, is_active=True)
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201

# Login endpoint to get JWT token
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email, password=password).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify({"token": access_token}), 200

# GET /people - list all people
@api.route('/people', methods=['GET'])
def get_people():
    people = People.query.all()
    return jsonify([p.serialize() for p in people]), 200

# GET /people/<int:id> - get one person
@api.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = People.query.get(people_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404
    return jsonify(person.serialize()), 200

# GET /planets - list all planets
@api.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    return jsonify([p.serialize() for p in planets]), 200

# GET /planets/<int:id> - get one planet
@api.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

# GET /users - list all users
@api.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.serialize() for u in users]), 200

# GET /users/favorites - list current user's favorites
@api.route('/users/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    current_user_id = get_jwt_identity()
    favorites = Favorite.query.filter_by(user_id=current_user_id).all()
    return jsonify([f.serialize() for f in favorites]), 200

# POST /favorite/planet/<int:planet_id> - add favorite planet
@api.route('/favorite/planet/<int:planet_id>', methods=['POST'])
@jwt_required()
def add_favorite_planet(planet_id):
    current_user_id = get_jwt_identity()
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404
    exists = Favorite.query.filter_by(user_id=current_user_id, planet_id=planet_id).first()
    if exists:
        return jsonify({"msg": "Planet already in favorites"}), 400
    fav = Favorite(user_id=current_user_id, planet_id=planet_id)
    db.session.add(fav)
    db.session.commit()
    favorites = Favorite.query.filter_by(user_id=current_user_id).all()
    return jsonify([f.serialize() for f in favorites]), 200

# POST /favorite/people/<int:people_id> - add favorite person
@api.route('/favorite/people/<int:people_id>', methods=['POST'])
@jwt_required()
def add_favorite_person(people_id):
    current_user_id = get_jwt_identity()
    person = People.query.get(people_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404
    exists = Favorite.query.filter_by(user_id=current_user_id, people_id=people_id).first()
    if exists:
        return jsonify({"msg": "Person already in favorites"}), 400
    fav = Favorite(user_id=current_user_id, people_id=people_id)
    db.session.add(fav)
    db.session.commit()
    favorites = Favorite.query.filter_by(user_id=current_user_id).all()
    return jsonify([f.serialize() for f in favorites]), 200

# DELETE /favorite/planet/<int:planet_id> - remove favorite planet
@api.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite_planet(planet_id):
    current_user_id = get_jwt_identity()
    fav = Favorite.query.filter_by(user_id=current_user_id, planet_id=planet_id).first()
    if not fav:
        return jsonify({"error": "Favorite planet not found"}), 404
    db.session.delete(fav)
    db.session.commit()
    favorites = Favorite.query.filter_by(user_id=current_user_id).all()
    return jsonify([f.serialize() for f in favorites]), 200

# DELETE /favorite/people/<int:people_id> - remove favorite person
@api.route('/favorite/people/<int:people_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite_person(people_id):
    current_user_id = get_jwt_identity()
    fav = Favorite.query.filter_by(user_id=current_user_id, people_id=people_id).first()
    if not fav:
        return jsonify({"error": "Favorite person not found"}), 404
    db.session.delete(fav)
    db.session.commit()
    favorites = Favorite.query.filter_by(user_id=current_user_id).all()
    return jsonify([f.serialize() for f in favorites]), 200

# Register blueprint
app.register_blueprint(api, url_prefix='/api')

# Error handler
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    with app.app_context():
     db.create_all()
    app.run(host='0.0.0.0', port=PORT, debug=False)
