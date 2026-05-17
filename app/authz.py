from flask import jsonify
import os
import re


def forbidden(message="Forbidden"):
    return jsonify({"error": message}), 403


def safe_error(error, status=400):
    debug = os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    is_database_error = (
        getattr(error, "errno", None) is not None
        or getattr(error, "sqlstate", None) is not None
        or error.__class__.__module__.startswith("mysql.connector")
    )
    message = str(error) if debug and not is_database_error else "Request failed"
    return jsonify({"error": message}), status


def duplicate_key_error(error, messages, default_message="Duplicate resource"):
    if getattr(error, "errno", None) != 1062:
        return None

    error_text = str(error).lower()
    key_match = re.search(r"for key ['`]([^'`]+)['`]", error_text)
    key_name = key_match.group(1) if key_match else error_text

    for key, message in messages.items():
        if key.lower() in key_name:
            return jsonify({"error": message}), 409

    return jsonify({"error": default_message}), 409


def get_claim_int(claims, name):
    value = claims.get(name)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def can_access_student_records(cursor, claims, student_id):
    role = claims.get("role")
    subtype_id = get_claim_int(claims, "subtype_id")

    if role == "admin":
        return True

    if role == "student":
        return subtype_id == student_id

    if role == "lecturer" and subtype_id is not None:
        cursor.execute("""
            SELECT 1
            FROM enrollment e
            JOIN course c ON e.course_id = c.course_id
            WHERE e.student_id = %s AND c.lecturer_id = %s
            LIMIT 1
        """, (student_id, subtype_id))
        return cursor.fetchone() is not None

    return False


def can_access_course(cursor, claims, course_id):
    role = claims.get("role")
    subtype_id = get_claim_int(claims, "subtype_id")

    if role == "admin":
        return True

    if subtype_id is None:
        return False

    if role == "lecturer":
        cursor.execute("""
            SELECT 1 FROM course
            WHERE course_id = %s AND lecturer_id = %s
            LIMIT 1
        """, (course_id, subtype_id))
        return cursor.fetchone() is not None

    if role == "student":
        cursor.execute("""
            SELECT 1 FROM enrollment
            WHERE course_id = %s AND student_id = %s
            LIMIT 1
        """, (course_id, subtype_id))
        return cursor.fetchone() is not None

    return False


def can_access_forum(cursor, claims, forum_id):
    cursor.execute("""
        SELECT course_id FROM discussion_forum
        WHERE forum_id = %s
    """, (forum_id,))
    forum = cursor.fetchone()
    if not forum:
        return False
    return can_access_course(cursor, claims, forum["course_id"])


def can_access_thread(cursor, claims, thread_id):
    cursor.execute("""
        SELECT df.course_id
        FROM discussion_thread dt
        JOIN discussion_forum df ON dt.forum_id = df.forum_id
        WHERE dt.thread_id = %s
    """, (thread_id,))
    thread = cursor.fetchone()
    if not thread:
        return False
    return can_access_course(cursor, claims, thread["course_id"])


def can_manage_section(cursor, claims, section_id):
    if claims.get("role") != "lecturer":
        return False

    cursor.execute("""
        SELECT course_id FROM section
        WHERE section_id = %s
    """, (section_id,))
    section = cursor.fetchone()
    if not section:
        return False
    return can_access_course(cursor, claims, section["course_id"])


def parent_reply_matches_thread(cursor, parent_reply_id, thread_id):
    if parent_reply_id is None:
        return True

    cursor.execute("""
        SELECT 1 FROM reply
        WHERE reply_id = %s AND thread_id = %s
        LIMIT 1
    """, (parent_reply_id, thread_id))
    return cursor.fetchone() is not None


def can_access_assignment(cursor, claims, assignment_id):
    role = claims.get("role")
    subtype_id = get_claim_int(claims, "subtype_id")

    if role == "admin":
        return True

    if subtype_id is None:
        return False

    if role == "lecturer":
        cursor.execute("""
            SELECT 1
            FROM assignment a
            JOIN course c ON a.course_id = c.course_id
            WHERE a.assignment_id = %s AND c.lecturer_id = %s
            LIMIT 1
        """, (assignment_id, subtype_id))
        return cursor.fetchone() is not None

    if role == "student":
        cursor.execute("""
            SELECT 1
            FROM assignment a
            JOIN enrollment e ON a.course_id = e.course_id
            WHERE a.assignment_id = %s AND e.student_id = %s
            LIMIT 1
        """, (assignment_id, subtype_id))
        return cursor.fetchone() is not None

    return False


def can_access_submission(cursor, claims, submission_id):
    role = claims.get("role")
    subtype_id = get_claim_int(claims, "subtype_id")

    if role == "admin":
        return True

    if subtype_id is None:
        return False

    if role == "student":
        cursor.execute("""
            SELECT 1 FROM submission
            WHERE submission_id = %s AND student_id = %s
            LIMIT 1
        """, (submission_id, subtype_id))
        return cursor.fetchone() is not None

    if role == "lecturer":
        cursor.execute("""
            SELECT 1
            FROM submission sub
            JOIN assignment a ON sub.assignment_id = a.assignment_id
            JOIN course c ON a.course_id = c.course_id
            WHERE sub.submission_id = %s AND c.lecturer_id = %s
            LIMIT 1
        """, (submission_id, subtype_id))
        return cursor.fetchone() is not None

    return False
