import os

from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from models import db

load_dotenv()


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # demo only
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///proofstack.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    JWTManager(app)

    # CORS: explicit, permissive-for-local-dev config. Using "*" as the
    # origins value together with supports_credentials=True is invalid per
    # the CORS spec (browsers reject it), which is what produces a CORS
    # error in the console even though the app "starts" fine. We instead
    # default to reflecting the request's own origin (covers 127.0.0.1 and
    # localhost on any port) unless FRONTEND_ORIGIN is explicitly set.
    frontend_origin = os.environ.get("FRONTEND_ORIGIN", "").strip()
    cors_origins = [o.strip() for o in frontend_origin.split(",") if o.strip()] or "*"
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    from routes import (
        auth, challenges, submissions, reviews, recruiter,
        dashboard, interview, institution, assessments, mentorship, chatbot,
        opportunities,
    )

    app.register_blueprint(auth.bp)
    app.register_blueprint(challenges.bp)
    app.register_blueprint(submissions.bp)
    app.register_blueprint(reviews.bp)
    app.register_blueprint(recruiter.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(interview.bp)
    app.register_blueprint(institution.bp)
    app.register_blueprint(assessments.bp)
    app.register_blueprint(mentorship.bp)
    app.register_blueprint(chatbot.bp)
    app.register_blueprint(opportunities.bp)

    with app.app_context():
        try:
            db.create_all()
        except Exception as exc:  # pragma: no cover - startup diagnostics
            print(f"[proofstack] WARNING: could not initialize the database: {exc}")
            print("[proofstack] Check DATABASE_URL / file permissions in .env")

    @app.get("/")
    def index():
        return send_from_directory(app.template_folder, "index.html")

    @app.get("/login/<role>")
    def role_login(role):
        return send_from_directory(app.template_folder, "login.html")

    @app.get("/student")
    def student_page():
        return send_from_directory(app.template_folder, "student.html")

    @app.get("/expert")
    def expert_page():
        return send_from_directory(app.template_folder, "expert.html")

    @app.get("/recruiter")
    def recruiter_page():
        return send_from_directory(app.template_folder, "recruiter.html")

    @app.get("/institution")
    def institution_page():
        return send_from_directory(app.template_folder, "institution.html")

    @app.get("/interview")
    def interview_page():
        return send_from_directory(app.template_folder, "interview.html")

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # host="0.0.0.0" means the server accepts connections addressed to
    # 127.0.0.1, localhost, or the machine's LAN IP -- avoids the classic
    # "works on 127.0.0.1 but not localhost" (or vice versa) mismatch.
    create_app().run(host="0.0.0.0", port=port, debug=True)
