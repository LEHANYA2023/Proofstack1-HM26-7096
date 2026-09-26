from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@bp.post("/register")
def register():
    body = request.get_json(force=True) or {}
    email = body.get("email", "").strip().lower()
    if not email or not body.get("password"):
        return jsonify({"error": "Email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
    role = body.get("role", "student")
    if role not in {"student", "expert", "recruiter", "institution"}:
        return jsonify({"error": "Invalid role"}), 400
    user = User(name=body.get("name", "New User"), email=email, password_hash=generate_password_hash(body["password"]), role=role, skills=body.get("skills", ""), track=body.get("track", "technical"))
    db.session.add(user); db.session.commit()
    return jsonify({"token": create_access_token(identity=user.id), "user": user.to_dict()}), 201

@bp.post("/login")
def login():
    body = request.get_json(force=True) or {}
    user = User.query.filter_by(email=body.get("email", "").strip().lower()).first()
    if not user or not check_password_hash(user.password_hash, body.get("password", "")):
        return jsonify({"error": "Invalid email or password"}), 401
    requested_role = body.get("role")
    if requested_role and user.role != requested_role:
        return jsonify({"error": f"This account belongs to the {user.role} portal."}), 403
    return jsonify({"token": create_access_token(identity=user.id), "user": user.to_dict()})

@bp.get("/me")
@jwt_required()
def me():
    return jsonify(User.query.get_or_404(get_jwt_identity()).to_dict())

@bp.put("/profile")
@jwt_required()
def update_profile():
    user = User.query.get_or_404(get_jwt_identity())
    body = request.get_json(force=True) or {}
    for field in ["name", "skills", "track", "headline", "bio", "resume_url", "github_profile_url", "portfolio_url", "availability"]:
        if field in body:
            setattr(user, field, body[field] or "")
    db.session.commit()
    return jsonify(user.to_dict())
