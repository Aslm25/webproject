from flask import Blueprint, request, jsonify
from src.models.user import db, User, Project, ProjectFile, Session as UserSession
from datetime import datetime, timedelta
import uuid

user_bp = Blueprint("user", __name__)

@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    if not username or not email or not password:
        return jsonify({"message": "Missing username, email, or password"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 409

    new_user = User(username=username, email=email, full_name=full_name)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials"}), 401

    # Generate a session token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)
    new_session = UserSession(user_id=user.id, token=token, expires_at=expires_at)
    db.session.add(new_session)

    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Login successful", "token": token, "user": {"username": user.username, "email": user.email, "full_name": user.full_name}}), 200

@user_bp.route("/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token missing"}), 401

    session = UserSession.query.filter_by(token=token).first()
    if session:
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": "Logged out successfully"}), 200
    return jsonify({"message": "Invalid token"}), 401

@user_bp.route("/profile", methods=["GET"])
def profile():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token missing"}), 401

    session = UserSession.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        return jsonify({"message": "Invalid or expired token"}), 401

    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({"username": user.username, "email": user.email, "full_name": user.full_name}), 200

@user_bp.route("/projects", methods=["POST"])
def create_project():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token missing"}), 401

    session = UserSession.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        return jsonify({"message": "Invalid or expired token"}), 401

    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    name = data.get("name")
    description = data.get("description")

    if not name:
        return jsonify({"message": "Project name is required"}), 400

    new_project = Project(user_id=user.id, name=name, description=description)
    db.session.add(new_project)
    db.session.commit()

    return jsonify({"message": "Project created successfully", "project_id": new_project.id}), 201

@user_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token missing"}), 401

    session = UserSession.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        return jsonify({"message": "Invalid or expired token"}), 401

    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({"message": "Project not found or unauthorized"}), 404

    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "files": []
    }
    for file in project.files:
        project_data["files"].append({
            "id": file.id,
            "filename": file.filename,
            "content": file.content,
            "language": file.language,
            "created_at": file.created_at.isoformat(),
            "updated_at": file.updated_at.isoformat()
        })

    return jsonify(project_data), 200

@user_bp.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token missing"}), 401

    session = UserSession.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        return jsonify({"message": "Invalid or expired token"}), 401

    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({"message": "Project not found or unauthorized"}), 404

    data = request.get_json()
    project.name = data.get("name", project.name)
    project.description = data.get("description", project.description)
    db.session.commit()

    return jsonify({"message": "Project updated successfully"}), 200

@user_bp.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token missing"}), 401

    session = UserSession.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        return jsonify({"message": "Invalid or expired token"}), 401

    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({"message": "Project not found or unauthorized"}), 404

    db.session.delete(project)
    db.session.commit()

    return jsonify({"message": "Project deleted successfully"}), 200

@user_bp.route("/projects/<int:project_id>/files", methods=["POST"])
def create_project_file(project_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token missing"}), 401

    session = UserSession.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        return jsonify({"message": "Invalid or expired token"}), 401

    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({"message": "Project not found or unauthorized"}), 404

    data = request.get_json()
    filename = data.get("filename")
    content = data.get("content", "")
    language = data.get("language", "plaintext")

    if not filename:
        return jsonify({"message": "Filename is required"}), 400

    new_file = ProjectFile(project_id=project.id, filename=filename, content=content, language=language)
    db.session.add(new_file)
    db.session.commit()

    return jsonify({"message": "File created successfully", "file_id": new_file.id}), 201

@user_bp.route("/projects/<int:project_id>/files/<int:file_id>", methods=["PUT"])
def update_project_file(project_id, file_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token missing"}), 401

    session = UserSession.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        return jsonify({"message": "Invalid or expired token"}), 401

    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({"message": "Project not found or unauthorized"}), 404

    file = ProjectFile.query.filter_by(id=file_id, project_id=project.id).first()
    if not file:
        return jsonify({"message": "File not found or unauthorized"}), 404

    data = request.get_json()
    file.filename = data.get("filename", file.filename)
    file.content = data.get("content", file.content)
    file.language = data.get("language", file.language)
    db.session.commit()

    return jsonify({"message": "File updated successfully"}), 200

@user_bp.route("/projects/<int:project_id>/files/<int:file_id>", methods=["DELETE"])
def delete_project_file(project_id, file_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token missing"}), 401

    session = UserSession.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        return jsonify({"message": "Invalid or expired token"}), 401

    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({"message": "Project not found or unauthorized"}), 404

    file = ProjectFile.query.filter_by(id=file_id, project_id=project.id).first()
    if not file:
        return jsonify({"message": "File not found or unauthorized"}), 404

    db.session.delete(file)
    db.session.commit()

    return jsonify({"message": "File deleted successfully"}), 200


