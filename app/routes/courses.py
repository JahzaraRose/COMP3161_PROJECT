from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.db import get_db
from app.cache import cache_get, cache_set, cache_delete

courses_bp = Blueprint("courses", __name__)


# ============================================================
# POST /api/courses  (admin only)
# ============================================================
@courses_bp.route("/courses", methods=["POST"])
@jwt_required()
def create_course():
    claims  = get_jwt()
    user_id = claims["sub"]   # fix: use claims["sub"] not get_jwt()["sub"]

    if claims.get("role") != "admin":
        return jsonify({"error": "Only admins can create courses"}), 403

    data = request.get_json()
    required = ["course_name", "course_code"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT admin_id FROM admin WHERE user_id = %s", (user_id,))
        admin = cursor.fetchone()
        if not admin:
            return jsonify({"error": "Admin record not found"}), 404

        # Fix: enforce max-5 courses per lecturer when lecturer_id is set at creation time
        if data.get("lecturer_id"):
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM course WHERE lecturer_id = %s
            """, (data["lecturer_id"],))
            if cursor.fetchone()["cnt"] >= 5:
                return jsonify({"error": "Lecturer already teaching maximum 5 courses"}), 400

        cursor.execute("""
            INSERT INTO course (course_name, course_code, description, lecturer_id, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data["course_name"],
            data["course_code"],
            data.get("description"),
            data.get("lecturer_id"),
            admin["admin_id"]
        ))
        conn.commit()
        cache_delete("courses:all")  # invalidate list cache after creation
        return jsonify({"message": "Course created", "course_id": cursor.lastrowid}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/courses  (all courses)
# ============================================================
@courses_bp.route("/courses", methods=["GET"])
@jwt_required()
def get_all_courses():
    cached = cache_get("courses:all")
    if cached is not None:
        return jsonify(cached), 200

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.course_id, c.course_code, c.course_name, c.description,
                   l.lecturer_id, u.first_name, u.last_name
            FROM course c
            LEFT JOIN lecturer l ON c.lecturer_id = l.lecturer_id
            LEFT JOIN user u     ON l.user_id     = u.user_id
            ORDER BY c.course_code
        """)
        courses = cursor.fetchall()
        cache_set("courses:all", courses, ttl=120)
        return jsonify(courses), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/courses/student/<student_id>
# ============================================================
@courses_bp.route("/courses/student/<int:student_id>", methods=["GET"])
@jwt_required()
def get_courses_by_student(student_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.course_id, c.course_code, c.course_name, c.description,
                   e.enrollment_at
            FROM course c
            JOIN enrollment e ON c.course_id = e.course_id
            WHERE e.student_id = %s
            ORDER BY c.course_code
        """, (student_id,))
        courses = cursor.fetchall()
        for c in courses:
            c["enrollment_at"] = str(c["enrollment_at"])
        return jsonify(courses), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/courses/lecturer/<lecturer_id>
# ============================================================
@courses_bp.route("/courses/lecturer/<int:lecturer_id>", methods=["GET"])
@jwt_required()
def get_courses_by_lecturer(lecturer_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.course_id, c.course_code, c.course_name, c.description
            FROM course c
            WHERE c.lecturer_id = %s
            ORDER BY c.course_code
        """, (lecturer_id,))
        courses = cursor.fetchall()
        return jsonify(courses), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/courses/<course_id>/members
# Now includes lecturer as a member too
# ============================================================
@courses_bp.route("/courses/<int:course_id>/members", methods=["GET"])
@jwt_required()
def get_course_members(course_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get enrolled students
        cursor.execute("""
            SELECT s.student_id, u.first_name, u.last_name, u.email,
                   s.major, s.year_level, e.enrollment_at,
                   'student' AS member_role
            FROM enrollment e
            JOIN student s ON e.student_id = s.student_id
            JOIN user u    ON s.user_id    = u.user_id
            WHERE e.course_id = %s
            ORDER BY u.last_name, u.first_name
        """, (course_id,))
        students = cursor.fetchall()
        for s in students:
            s["enrollment_at"] = str(s["enrollment_at"])

        # Get assigned lecturer
        cursor.execute("""
            SELECT l.lecturer_id, u.first_name, u.last_name, u.email,
                   l.department, 'lecturer' AS member_role
            FROM course c
            JOIN lecturer l ON c.lecturer_id = l.lecturer_id
            JOIN user u     ON l.user_id     = u.user_id
            WHERE c.course_id = %s
        """, (course_id,))
        lecturer = cursor.fetchone()

        members = []
        if lecturer:
            members.append(lecturer)
        members.extend(students)

        return jsonify(members), 200
    finally:
        cursor.close()
        conn.close()