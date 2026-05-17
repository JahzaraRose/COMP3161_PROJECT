from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.db import get_db

enrollments_bp = Blueprint("enrollments", __name__)


# ============================================================
# POST /api/courses/<course_id>/enroll  (student only)
# ============================================================
@enrollments_bp.route("/courses/<int:course_id>/enroll", methods=["POST"])
@jwt_required()
def enroll_in_course(course_id):
    claims  = get_jwt()
    user_id = claims["sub"]

    if claims.get("role") != "student":
        return jsonify({"error": "Only students can enroll in courses"}), 403

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get student_id
        cursor.execute("SELECT student_id FROM student WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({"error": "Student record not found"}), 404

        student_id = student["student_id"]

        # Check max 6 courses
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM enrollment WHERE student_id = %s
        """, (student_id,))
        count = cursor.fetchone()["cnt"]
        if count >= 6:
            return jsonify({"error": "Student already enrolled in maximum 6 courses"}), 400

        # Check course exists
        cursor.execute("SELECT course_id FROM course WHERE course_id = %s", (course_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Course not found"}), 404

        cursor.execute("""
            INSERT INTO enrollment (student_id, course_id) VALUES (%s, %s)
        """, (student_id, course_id))
        conn.commit()
        return jsonify({"message": "Enrolled successfully"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/courses/<course_id>/assign-lecturer  (admin only)
# ============================================================
@enrollments_bp.route("/courses/<int:course_id>/assign-lecturer", methods=["POST"])
@jwt_required()
def assign_lecturer(course_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Only admins can assign lecturers"}), 403

    data = request.get_json()
    if "lecturer_id" not in data:
        return jsonify({"error": "lecturer_id required"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check lecturer teaches max 5 courses
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM course WHERE lecturer_id = %s
        """, (data["lecturer_id"],))
        count = cursor.fetchone()["cnt"]
        if count >= 5:
            return jsonify({"error": "Lecturer already teaching maximum 5 courses"}), 400

        cursor.execute("""
            UPDATE course SET lecturer_id = %s WHERE course_id = %s
        """, (data["lecturer_id"], course_id))
        conn.commit()
        return jsonify({"message": "Lecturer assigned successfully"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()