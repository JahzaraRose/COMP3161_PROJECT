from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.authz import (
    can_access_assignment,
    can_access_course,
    can_access_student_records,
    can_access_submission,
    duplicate_key_error,
    forbidden,
    get_claim_int,
    safe_error,
)
from app.db import get_db

assignments_bp = Blueprint("assignments", __name__)


# ============================================================
# POST /api/courses/<course_id>/assignments  (lecturer only)
# ============================================================
@assignments_bp.route("/courses/<int:course_id>/assignments", methods=["POST"])
@jwt_required()
def create_assignment(course_id):
    claims  = get_jwt()

    if claims.get("role") != "lecturer":
        return jsonify({"error": "Only lecturers can create assignments"}), 403

    data = request.get_json()
    if "assignment_title" not in data:
        return jsonify({"error": "assignment_title required"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        lecturer_id = get_claim_int(claims, "subtype_id")
        if lecturer_id is None:
            return jsonify({"error": "Lecturer not found"}), 404
        if not can_access_course(cursor, claims, course_id):
            return forbidden()

        cursor.execute("""
            INSERT INTO assignment (course_id, created_by, assignment_title, description, due_date, max_grade)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            course_id,
            lecturer_id,
            data["assignment_title"],
            data.get("description"),
            data.get("due_date"),
            data.get("max_grade", 100.00)
        ))
        conn.commit()
        return jsonify({"message": "Assignment created", "assignment_id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return safe_error(e)
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/courses/<course_id>/assignments
# ============================================================
@assignments_bp.route("/courses/<int:course_id>/assignments", methods=["GET"])
@jwt_required()
def get_course_assignments(course_id):
    claims = get_jwt()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_course(cursor, claims, course_id):
            return forbidden()

        cursor.execute("""
            SELECT a.assignment_id, a.assignment_title, a.description,
                   a.due_date, a.max_grade,
                   u.first_name, u.last_name
            FROM assignment a
            JOIN lecturer l ON a.created_by  = l.lecturer_id
            JOIN user u     ON l.user_id     = u.user_id
            WHERE a.course_id = %s
            ORDER BY a.due_date
        """, (course_id,))
        assignments = cursor.fetchall()
        for a in assignments:
            if a["due_date"]:
                a["due_date"] = str(a["due_date"])
        return jsonify(assignments), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/assignments/<assignment_id>/submit  (student only)
# Includes enrollment check before allowing submission
# ============================================================
@assignments_bp.route("/assignments/<int:assignment_id>/submit", methods=["POST"])
@jwt_required()
def submit_assignment(assignment_id):
    claims  = get_jwt()

    if claims.get("role") != "student":
        return jsonify({"error": "Only students can submit assignments"}), 403

    data = request.get_json()

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        student_id = get_claim_int(claims, "subtype_id")
        if student_id is None:
            return jsonify({"error": "Student not found"}), 404

        # Get course_id for this assignment
        cursor.execute("SELECT course_id FROM assignment WHERE assignment_id = %s", (assignment_id,))
        assignment = cursor.fetchone()
        if not assignment:
            return jsonify({"error": "Assignment not found"}), 404

        # Check student is enrolled in the course
        cursor.execute("""
            SELECT enrollment_id FROM enrollment
            WHERE student_id = %s AND course_id = %s
        """, (student_id, assignment["course_id"]))
        enrollment = cursor.fetchone()
        if not enrollment:
            return jsonify({"error": "You are not enrolled in this course"}), 403

        cursor.execute("""
            INSERT INTO submission (assignment_id, student_id, submission_text)
            VALUES (%s, %s, %s)
        """, (assignment_id, student_id, data.get("submission_text")))
        conn.commit()
        return jsonify({"message": "Assignment submitted", "submission_id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        duplicate_response = duplicate_key_error(e, {
            "uq_submission": "Assignment already submitted",
        })
        if duplicate_response:
            return duplicate_response
        return safe_error(e)
    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/submissions/<submission_id>/grade  (lecturer only)
# ============================================================
@assignments_bp.route("/submissions/<int:submission_id>/grade", methods=["POST"])
@jwt_required()
def grade_submission(submission_id):
    claims = get_jwt()
    if claims.get("role") not in ("lecturer", "admin"):
        return jsonify({"error": "Only lecturers or admins can grade submissions"}), 403

    data = request.get_json()
    if "grade" not in data:
        return jsonify({"error": "grade required"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_submission(cursor, claims, submission_id):
            return forbidden()

        cursor.execute("""
            UPDATE submission SET grade = %s WHERE submission_id = %s
        """, (data["grade"], submission_id))
        conn.commit()
        return jsonify({"message": "Grade submitted successfully"}), 200
    except Exception as e:
        conn.rollback()
        return safe_error(e)
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/assignments/<assignment_id>/submissions  (lecturer only)
# ============================================================
@assignments_bp.route("/assignments/<int:assignment_id>/submissions", methods=["GET"])
@jwt_required()
def get_submissions(assignment_id):
    claims = get_jwt()
    if claims.get("role") not in ("lecturer", "admin"):
        return jsonify({"error": "Only lecturers or admins can view submissions"}), 403

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_assignment(cursor, claims, assignment_id):
            return forbidden()

        cursor.execute("""
            SELECT sub.submission_id, sub.submission_text, sub.submitted_at,
                   sub.grade, s.student_id, u.first_name, u.last_name, u.email
            FROM submission sub
            JOIN student s ON sub.student_id = s.student_id
            JOIN user u    ON s.user_id      = u.user_id
            WHERE sub.assignment_id = %s
            ORDER BY u.last_name, u.first_name
        """, (assignment_id,))
        submissions = cursor.fetchall()
        for s in submissions:
            s["submitted_at"] = str(s["submitted_at"])
        return jsonify(submissions), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/students/<student_id>/submissions  (get a student's grades)
# ============================================================
@assignments_bp.route("/students/<int:student_id>/submissions", methods=["GET"])
@jwt_required()
def get_student_submissions(student_id):
    claims = get_jwt()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_student_records(cursor, claims, student_id):
            return forbidden()

        params = [student_id]
        course_scope = ""
        lecturer_id = get_claim_int(claims, "subtype_id")
        if claims.get("role") == "lecturer":
            course_scope = " AND c.lecturer_id = %s"
            params.append(lecturer_id)

        cursor.execute(f"""
            SELECT sub.submission_id, sub.assignment_id, a.assignment_title,
                   sub.submission_text, sub.submitted_at,
                   sub.grade, a.max_grade,
                   ROUND((sub.grade / a.max_grade) * 100, 2) AS percentage
            FROM submission sub
            JOIN assignment a ON sub.assignment_id = a.assignment_id
            JOIN course c ON a.course_id = c.course_id
            WHERE sub.student_id = %s
            {course_scope}
            ORDER BY sub.submitted_at DESC
        """, tuple(params))
        submissions = cursor.fetchall()
        for s in submissions:
            s["submitted_at"] = str(s["submitted_at"])
        return jsonify(submissions), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/students/<student_id>/average
# ============================================================
@assignments_bp.route("/students/<int:student_id>/average", methods=["GET"])
@jwt_required()
def get_student_average(student_id):
    claims = get_jwt()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_student_records(cursor, claims, student_id):
            return forbidden()

        params = [student_id]
        course_scope = ""
        lecturer_id = get_claim_int(claims, "subtype_id")
        if claims.get("role") == "lecturer":
            course_scope = " AND c.lecturer_id = %s"
            params.append(lecturer_id)

        cursor.execute(f"""
            SELECT ROUND(AVG((sub.grade / a.max_grade) * 100), 2) AS average_percentage
            FROM submission sub
            JOIN assignment a ON sub.assignment_id = a.assignment_id
            JOIN course c ON a.course_id = c.course_id
            WHERE sub.student_id = %s AND sub.grade IS NOT NULL
            {course_scope}
        """, tuple(params))
        result = cursor.fetchone()
        return jsonify(result), 200
    finally:
        cursor.close()
        conn.close()
