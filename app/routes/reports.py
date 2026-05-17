from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.db import get_db
from app.cache import cache_get, cache_set

reports_bp = Blueprint("reports", __name__)

REPORT_TTL = 300  # 5 minutes


def _admin_only():
    claims = get_jwt()
    return claims.get("role") == "admin"


# ============================================================
# GET /api/reports/courses-50-plus
# ============================================================
@reports_bp.route("/reports/courses-50-plus", methods=["GET"])
@jwt_required()
def courses_50_plus():
    if not _admin_only():
        return jsonify({"error": "Only admins can view reports"}), 403

    cached = cache_get("report:courses_50_plus")
    if cached is not None:
        return jsonify(cached), 200

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM view_courses_50_plus ORDER BY student_count DESC")
        data = cursor.fetchall()
        cache_set("report:courses_50_plus", data, REPORT_TTL)
        return jsonify(data), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/reports/students-5-plus-courses
# ============================================================
@reports_bp.route("/reports/students-5-plus-courses", methods=["GET"])
@jwt_required()
def students_5_plus():
    if not _admin_only():
        return jsonify({"error": "Only admins can view reports"}), 403

    cached = cache_get("report:students_5_plus")
    if cached is not None:
        return jsonify(cached), 200

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM view_students_5_plus_courses ORDER BY course_count DESC")
        data = cursor.fetchall()
        cache_set("report:students_5_plus", data, REPORT_TTL)
        return jsonify(data), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/reports/lecturers-3-plus-courses
# ============================================================
@reports_bp.route("/reports/lecturers-3-plus-courses", methods=["GET"])
@jwt_required()
def lecturers_3_plus():
    if not _admin_only():
        return jsonify({"error": "Only admins can view reports"}), 403

    cached = cache_get("report:lecturers_3_plus")
    if cached is not None:
        return jsonify(cached), 200

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM view_lecturers_3_plus_courses ORDER BY course_count DESC")
        data = cursor.fetchall()
        cache_set("report:lecturers_3_plus", data, REPORT_TTL)
        return jsonify(data), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/reports/top-10-enrolled-courses
# ============================================================
@reports_bp.route("/reports/top-10-enrolled-courses", methods=["GET"])
@jwt_required()
def top_10_courses():
    if not _admin_only():
        return jsonify({"error": "Only admins can view reports"}), 403

    cached = cache_get("report:top10_courses")
    if cached is not None:
        return jsonify(cached), 200

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.course_id, c.course_code, c.course_name,
                   COUNT(e.student_id) AS student_count
            FROM course c
            JOIN enrollment e ON c.course_id = e.course_id
            GROUP BY c.course_id, c.course_code, c.course_name
            ORDER BY student_count DESC
            LIMIT 10
        """)
        data = cursor.fetchall()
        cache_set("report:top10_courses", data, REPORT_TTL)
        return jsonify(data), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/reports/top-10-students
# ============================================================
@reports_bp.route("/reports/top-10-students", methods=["GET"])
@jwt_required()
def top_10_students():
    if not _admin_only():
        return jsonify({"error": "Only admins can view reports"}), 403

    cached = cache_get("report:top10_students")
    if cached is not None:
        return jsonify(cached), 200

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT s.student_id, u.first_name, u.last_name, u.email,
                   ROUND(AVG((sub.grade / a.max_grade) * 100), 2) AS average_percentage
            FROM student s
            JOIN user       u   ON s.user_id         = u.user_id
            JOIN submission sub ON s.student_id      = sub.student_id
            JOIN assignment a   ON sub.assignment_id = a.assignment_id
            WHERE sub.grade IS NOT NULL
            GROUP BY s.student_id, u.first_name, u.last_name, u.email
            ORDER BY average_percentage DESC
            LIMIT 10
        """)
        data = cursor.fetchall()
        cache_set("report:top10_students", data, REPORT_TTL)
        return jsonify(data), 200
    finally:
        cursor.close()
        conn.close()
