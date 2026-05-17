from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.db import get_db

forums_bp = Blueprint("forums", __name__)


# ============================================================
# GET /api/courses/<course_id>/forums
# ============================================================
@forums_bp.route("/courses/<int:course_id>/forums", methods=["GET"])
@jwt_required()
def get_forums(course_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT forum_id, forum_title, created_at
            FROM discussion_forum
            WHERE course_id = %s
            ORDER BY created_at DESC
        """, (course_id,))
        forums = cursor.fetchall()
        for f in forums:
            f["created_at"] = str(f["created_at"])
        return jsonify(forums), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/courses/<course_id>/forums  (lecturer or admin)
# ============================================================
@forums_bp.route("/courses/<int:course_id>/forums", methods=["POST"])
@jwt_required()
def create_forum(course_id):
    claims  = get_jwt()
    user_id = claims["sub"]
    role    = claims.get("role")

    if role not in ("lecturer", "admin"):
        return jsonify({"error": "Only lecturers or admins can create forums"}), 403

    data = request.get_json()
    if "forum_title" not in data:
        return jsonify({"error": "forum_title required"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO discussion_forum (course_id, created_by, forum_title)
            VALUES (%s, %s, %s)
        """, (course_id, user_id, data["forum_title"]))
        conn.commit()
        return jsonify({"message": "Forum created", "forum_id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/forums/<forum_id>/threads
# ============================================================
@forums_bp.route("/forums/<int:forum_id>/threads", methods=["GET"])
@jwt_required()
def get_threads(forum_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT dt.thread_id, dt.thread_title, dt.starting_post, dt.created_at,
                   u.first_name, u.last_name
            FROM discussion_thread dt
            JOIN user u ON dt.user_id = u.user_id
            WHERE dt.forum_id = %s
            ORDER BY dt.created_at DESC
        """, (forum_id,))
        threads = cursor.fetchall()
        for t in threads:
            t["created_at"] = str(t["created_at"])
        return jsonify(threads), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/forums/<forum_id>/threads
# ============================================================
@forums_bp.route("/forums/<int:forum_id>/threads", methods=["POST"])
@jwt_required()
def create_thread(forum_id):
    claims  = get_jwt()
    user_id = claims["sub"]

    data = request.get_json()
    required = ["thread_title", "starting_post"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO discussion_thread (forum_id, user_id, thread_title, starting_post)
            VALUES (%s, %s, %s, %s)
        """, (forum_id, user_id, data["thread_title"], data["starting_post"]))
        conn.commit()
        return jsonify({"message": "Thread created", "thread_id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/threads/<thread_id>/replies
# ============================================================
@forums_bp.route("/threads/<int:thread_id>/replies", methods=["GET"])
@jwt_required()
def get_replies(thread_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT r.reply_id, r.parent_reply_id, r.reply_text, r.created_at,
                   u.first_name, u.last_name
            FROM reply r
            JOIN user u ON r.user_id = u.user_id
            WHERE r.thread_id = %s
            ORDER BY r.created_at ASC
        """, (thread_id,))
        replies = cursor.fetchall()
        for r in replies:
            r["created_at"] = str(r["created_at"])
        return jsonify(replies), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/threads/<thread_id>/replies
# ============================================================
@forums_bp.route("/threads/<int:thread_id>/replies", methods=["POST"])
@jwt_required()
def create_reply(thread_id):
    claims  = get_jwt()
    user_id = claims["sub"]

    data = request.get_json()
    if "reply_text" not in data:
        return jsonify({"error": "reply_text required"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO reply (thread_id, user_id, parent_reply_id, reply_text)
            VALUES (%s, %s, %s, %s)
        """, (
            thread_id,
            user_id,
            data.get("parent_reply_id"),  # NULL = top level, ID = nested
            data["reply_text"]
        ))
        conn.commit()
        return jsonify({"message": "Reply posted", "reply_id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()