from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.authz import can_access_course, can_access_student_records, forbidden, get_claim_int, safe_error
from app.db import get_db

calendar_bp = Blueprint("calendar", __name__)


# ============================================================
# GET /api/courses/<course_id>/events
# ============================================================
@calendar_bp.route("/courses/<int:course_id>/events", methods=["GET"])
@jwt_required()
def get_course_events(course_id):
    claims = get_jwt()
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if not can_access_course(cursor, claims, course_id):
            return forbidden()

        cursor.execute("""
            SELECT event_id, event_title, event_description,
                   event_date, start_time, end_time, created_by
            FROM calendar_event
            WHERE course_id = %s
            ORDER BY event_date, start_time
        """, (course_id,))
        events = cursor.fetchall()
        # Convert time/date to string for JSON
        for e in events:
            e["event_date"]  = str(e["event_date"])
            e["start_time"]  = str(e["start_time"]) if e["start_time"] else None
            e["end_time"]    = str(e["end_time"])   if e["end_time"]   else None
        return jsonify(events), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/students/<student_id>/events?date=YYYY-MM-DD
# ============================================================
@calendar_bp.route("/students/<int:student_id>/events", methods=["GET"])
@jwt_required()
def get_student_events(student_id):
    claims = get_jwt()
    date = request.args.get("date")

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

        if date:
            params.append(date)
            cursor.execute("""
                SELECT ce.event_id, ce.event_title, ce.event_description,
                       ce.event_date, ce.start_time, ce.end_time,
                       c.course_name, c.course_code
                FROM calendar_event ce
                JOIN course c     ON ce.course_id  = c.course_id
                JOIN enrollment e ON c.course_id   = e.course_id
                WHERE e.student_id = %s
                """ + lecturer_scope + """
                  AND ce.event_date = %s
                ORDER BY ce.start_time
            """, tuple(params))
        else:
            cursor.execute("""
                SELECT ce.event_id, ce.event_title, ce.event_description,
                       ce.event_date, ce.start_time, ce.end_time,
                       c.course_name, c.course_code
                FROM calendar_event ce
                JOIN course c     ON ce.course_id = c.course_id
                JOIN enrollment e ON c.course_id  = e.course_id
                WHERE e.student_id = %s
                """ + lecturer_scope + """
                ORDER BY ce.event_date, ce.start_time
            """, tuple(params))

        events = cursor.fetchall()
        for e in events:
            e["event_date"] = str(e["event_date"])
            e["start_time"] = str(e["start_time"]) if e["start_time"] else None
            e["end_time"]   = str(e["end_time"])   if e["end_time"]   else None
        return jsonify(events), 200
    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/courses/<course_id>/events  (lecturer or admin)
# ============================================================
@calendar_bp.route("/courses/<int:course_id>/events", methods=["POST"])
@jwt_required()
def create_event(course_id):
    claims  = get_jwt()
    user_id = claims["sub"]
    role    = claims.get("role")

    if role not in ("lecturer", "admin"):
        return jsonify({"error": "Only lecturers or admins can create events"}), 403

    data = request.get_json()
    required = ["event_title", "event_date"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if role == "lecturer" and not can_access_course(cursor, claims, course_id):
            return forbidden()

        cursor.execute("""
            INSERT INTO calendar_event
            (course_id, created_by, event_title, event_description, event_date, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            course_id,
            user_id,
            data["event_title"],
            data.get("event_description"),
            data["event_date"],
            data.get("start_time"),
            data.get("end_time")
        ))
        conn.commit()
        return jsonify({"message": "Event created", "event_id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return safe_error(e)
    finally:
        cursor.close()
        conn.close()
