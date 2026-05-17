from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.authz import can_access_course, can_manage_section, forbidden, get_claim_int, safe_error
from app.db import get_db

content_bp = Blueprint("content", __name__)


# ============================================================
# GET /api/courses/<course_id>/content
# ============================================================
@content_bp.route("/courses/<int:course_id>/content", methods=["GET"])
@jwt_required()
def get_course_content(course_id):
    claims = get_jwt()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_course(cursor, claims, course_id):
            return forbidden()

        cursor.execute("""
            SELECT s.section_id, s.section_title, s.section_order,
                   si.item_id, si.item_title, si.item_type, si.item_url
            FROM section s
            LEFT JOIN section_item si ON s.section_id = si.section_id
            WHERE s.course_id = %s
            ORDER BY s.section_order, si.item_id
        """, (course_id,))
        rows = cursor.fetchall()

        # Group items under their sections
        sections = {}
        for row in rows:
            sid = row["section_id"]
            if sid not in sections:
                sections[sid] = {
                    "section_id":    sid,
                    "section_title": row["section_title"],
                    "section_order": row["section_order"],
                    "items":         []
                }
            if row["item_id"]:
                sections[sid]["items"].append({
                    "item_id":    row["item_id"],
                    "item_title": row["item_title"],
                    "item_type":  row["item_type"],
                    "item_url":   row["item_url"]
                })

        return jsonify(list(sections.values())), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/courses/<course_id>/sections  (lecturer only)
# ============================================================
@content_bp.route("/courses/<int:course_id>/sections", methods=["POST"])
@jwt_required()
def create_section(course_id):
    claims = get_jwt()
    if claims.get("role") != "lecturer":
        return jsonify({"error": "Only lecturers can add sections"}), 403

    data = request.get_json()
    if "section_title" not in data:
        return jsonify({"error": "section_title required"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_course(cursor, claims, course_id):
            return forbidden()

        cursor.execute("""
            INSERT INTO section (course_id, section_title, section_order)
            VALUES (%s, %s, %s)
        """, (course_id, data["section_title"], data.get("section_order", 1)))
        conn.commit()
        return jsonify({"message": "Section created", "section_id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return safe_error(e)
    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/sections/<section_id>/items  (lecturer only)
# ============================================================
@content_bp.route("/sections/<int:section_id>/items", methods=["POST"])
@jwt_required()
def add_section_item(section_id):
    claims  = get_jwt()

    if claims.get("role") != "lecturer":
        return jsonify({"error": "Only lecturers can add content"}), 403

    data = request.get_json()
    required = ["item_title", "item_type"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    if data["item_type"] not in ("link", "file", "slide"):
        return jsonify({"error": "item_type must be link, file or slide"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        lecturer_id = get_claim_int(claims, "subtype_id")
        if lecturer_id is None:
            return jsonify({"error": "Lecturer record not found"}), 404
        if not can_manage_section(cursor, claims, section_id):
            return forbidden()

        cursor.execute("""
            INSERT INTO section_item (section_id, uploaded_by, item_title, item_type, item_url)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            section_id,
            lecturer_id,
            data["item_title"],
            data["item_type"],
            data.get("item_url")
        ))
        conn.commit()
        return jsonify({"message": "Item added", "item_id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return safe_error(e)
    finally:
        cursor.close()
        conn.close()
