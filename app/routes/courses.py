from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.authz import can_access_course, can_access_student_records, duplicate_key_error, forbidden, get_claim_int, safe_error
from app.db import get_db
from app.cache import cache_delete

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
        duplicate_response = duplicate_key_error(e, {
            "course_code": "Course code already exists",
        })
        if duplicate_response:
            return duplicate_response
        return safe_error(e)
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/courses  (paginated courses)
# ============================================================
@courses_bp.route("/courses", methods=["GET"])
@jwt_required()
def get_all_courses():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except (TypeError, ValueError):
        return jsonify({"error": "page and per_page must be positive integers"}), 400

    if page < 1 or per_page < 1:
        return jsonify({"error": "page and per_page must be positive integers"}), 400

    offset = (page - 1) * per_page

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM course")
        total = cursor.fetchone()["total"]
        total_pages = (total + per_page - 1) // per_page

        cursor.execute("""
            SELECT c.course_id, c.course_code, c.course_name, c.description,
                   l.lecturer_id, u.first_name, u.last_name
            FROM course c
            LEFT JOIN lecturer l ON c.lecturer_id = l.lecturer_id
            LEFT JOIN user u     ON l.user_id     = u.user_id
            ORDER BY c.course_code
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        courses = cursor.fetchall()
        return jsonify({
            "courses": courses,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/courses/<course_id>  (single course)
# ============================================================
@courses_bp.route("/courses/<int:course_id>", methods=["GET"])
@jwt_required()
def get_course(course_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.course_id, c.course_code, c.course_name, c.description,
                   l.lecturer_id, l.department,
                   u.first_name AS lecturer_first_name,
                   u.last_name AS lecturer_last_name,
                   u.email AS lecturer_email
            FROM course c
            LEFT JOIN lecturer l ON c.lecturer_id = l.lecturer_id
            LEFT JOIN user u     ON l.user_id     = u.user_id
            WHERE c.course_id = %s
        """, (course_id,))
        course = cursor.fetchone()
        if not course:
            return jsonify({"error": "Course not found"}), 404
        return jsonify(course), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/courses/student/<student_id>
# ============================================================
@courses_bp.route("/courses/student/<int:student_id>", methods=["GET"])
@jwt_required()
def get_courses_by_student(student_id):
    claims = get_jwt()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_student_records(cursor, claims, student_id):
            return forbidden()

        params = [student_id]
        lecturer_scope = ""
        lecturer_id = get_claim_int(claims, "subtype_id")
        if claims.get("role") == "lecturer":
            lecturer_scope = " AND c.lecturer_id = %s"
            params.append(lecturer_id)

        cursor.execute(f"""
            SELECT c.course_id, c.course_code, c.course_name, c.description,
                   e.enrollment_at
            FROM course c
            JOIN enrollment e ON c.course_id = e.course_id
            WHERE e.student_id = %s
            {lecturer_scope}
            ORDER BY c.course_code
        """, tuple(params))
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
    claims = get_jwt()
    if claims.get("role") == "lecturer" and get_claim_int(claims, "subtype_id") != lecturer_id:
        return forbidden()
    if claims.get("role") not in ("lecturer", "admin"):
        return forbidden()

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
    claims = get_jwt()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_course(cursor, claims, course_id):
            return forbidden()

        student_filter = ""
        params = [course_id]
        if claims.get("role") == "student":
            student_filter = " AND s.student_id = %s"
            params.append(get_claim_int(claims, "subtype_id"))

        # Get enrolled students. Students only see their own student record.
        cursor.execute(f"""
            SELECT s.student_id, u.first_name, u.last_name, u.email,
                   s.major, s.year_level, e.enrollment_at,
                   'student' AS member_role
            FROM enrollment e
            JOIN student s ON e.student_id = s.student_id
            JOIN user u    ON s.user_id    = u.user_id
            WHERE e.course_id = %s
            {student_filter}
            ORDER BY u.last_name, u.first_name
        """, tuple(params))
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
