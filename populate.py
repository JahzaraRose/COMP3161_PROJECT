import mysql.connector
import random
from datetime import datetime, timedelta
from app.db import _db_config

conn = mysql.connector.connect(**_db_config())
cursor = conn.cursor()

print("Connected to database successfully!")

# ============================================================
# HELPER DATA
# ============================================================
first_names = [
    'James','Maria','John','Sarah','David','Emma','Michael','Lisa',
    'Robert','Anna','Chris','Sophia','Daniel','Olivia','Matthew',
    'Isabella','Andrew','Mia','Joshua','Ava'
]
last_names = [
    'Smith','Johnson','Williams','Brown','Jones','Garcia','Miller',
    'Davis','Wilson','Moore','Taylor','Anderson','Thomas','Jackson',
    'White','Harris','Martin','Thompson','Young','King'
]
majors = [
    'Computer Science','Mathematics','Physics','Chemistry','Biology',
    'Engineering','Business','Economics','Psychology','Literature'
]
departments = [
    'Computer Science','Mathematics','Physics','Chemistry','Biology',
    'Engineering','Business','Economics','Psychology','Literature'
]
course_prefixes = [
    'Introduction to','Advanced','Fundamentals of','Applied',
    'Principles of','Topics in','Special Topics in','Research in',
    'Seminar in','Theory of'
]
course_subjects = [
    'Computer Science','Mathematics','Physics','Chemistry','Biology',
    'Engineering','Business','Economics','Psychology','Data Science',
    'Networking','Databases','Algorithms','Statistics','Calculus',
    'Linear Algebra','Organic Chemistry','Mechanics','Microeconomics','Accounting'
]
reply_texts = [
    'Great question! I was wondering the same thing.',
    'I think the answer is in the lecture notes from week 3.',
    'Has anyone asked the lecturer about this?',
    'Thanks for bringing this up, very helpful.',
    'I found a useful resource online that explains this well.'
]
thread_titles = [
    'Question about the syllabus',
    'Help with assignment',
    'Study group formation',
    'Clarification on lecture material',
    'Exam preparation tips'
]
event_titles = [
    'Midterm Exam','Final Exam','Guest Lecture',
    'Lab Session','Project Presentation'
]
item_titles = [
    'Lecture Slides','Reading Material','Tutorial Video',
    'Assignment Brief','Reference Guide'
]
item_types = ['link', 'file', 'slide']
assign_types = ['Problem Set','Research Paper','Project','Lab Report','Case Study']

def random_date(days_back=365):
    return datetime.now() - timedelta(days=random.randint(0, days_back))

# ============================================================
# STEP 1: INSERT 5 ADMINS
# ============================================================
print("\n[1/13] Inserting admins...")
admin_user_ids = []
admin_ids = []

for i in range(1, 6):
    cursor.execute("""
        INSERT INTO user (username, password_hash, first_name, last_name, email, role)
        VALUES (%s, %s, %s, %s, %s, 'admin')
    """, (f'admin{i}', '$2b$12$adminhash', 'Admin', f'User{i}', f'admin{i}@school.edu'))
    uid = cursor.lastrowid
    admin_user_ids.append(uid)
    cursor.execute("INSERT INTO admin (user_id) VALUES (%s)", (uid,))
    admin_ids.append(cursor.lastrowid)

conn.commit()
print(f"  ✓ {len(admin_ids)} admins inserted")

# ============================================================
# STEP 2: INSERT 100 LECTURERS
# ============================================================
print("\n[2/13] Inserting lecturers...")
lecturer_ids = []

for i in range(1, 101):
    fname = first_names[i % len(first_names)]
    lname = last_names[i % len(last_names)]
    dept  = departments[i % len(departments)]
    cursor.execute("""
        INSERT INTO user (username, password_hash, first_name, last_name, email, role)
        VALUES (%s, %s, %s, %s, %s, 'lecturer')
    """, (f'lecturer{i}', '$2b$12$lecturerhash', fname, lname, f'lecturer{i}@school.edu'))
    uid = cursor.lastrowid
    cursor.execute("INSERT INTO lecturer (user_id, department) VALUES (%s, %s)", (uid, dept))
    lecturer_ids.append(cursor.lastrowid)

conn.commit()
print(f"  ✓ {len(lecturer_ids)} lecturers inserted")

# ============================================================
# STEP 3: INSERT 100,000 STUDENTS (batch inserts)
# ============================================================
print("\n[3/13] Inserting 100,000 students in batches...")

BATCH_SIZE = 1000
student_ids = []

user_batch = []
for i in range(1, 100001):
    fname = first_names[i % len(first_names)]
    lname = last_names[i % len(last_names)]
    user_batch.append((
        f'student{i}',
        '$2b$12$studenthash',
        fname,
        lname,
        f'student{i}@school.edu',
        'student'
    ))

# Insert users in batches
for batch_start in range(0, len(user_batch), BATCH_SIZE):
    batch = user_batch[batch_start:batch_start + BATCH_SIZE]
    cursor.executemany("""
        INSERT INTO user (username, password_hash, first_name, last_name, email, role)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, batch)
    conn.commit()
    if (batch_start // BATCH_SIZE + 1) % 10 == 0:
        print(f"  Users: {batch_start + BATCH_SIZE} / 100000")

# Get all student user_ids
cursor.execute("SELECT user_id FROM user WHERE role = 'student' ORDER BY user_id")
student_user_ids = [row[0] for row in cursor.fetchall()]

# Insert student records in batches
major_list   = [majors[i % len(majors)] for i in range(len(student_user_ids))]
year_list    = [(i % 4) + 1 for i in range(len(student_user_ids))]
student_batch = [(student_user_ids[i], major_list[i], year_list[i]) for i in range(len(student_user_ids))]

for batch_start in range(0, len(student_batch), BATCH_SIZE):
    batch = student_batch[batch_start:batch_start + BATCH_SIZE]
    cursor.executemany("""
        INSERT INTO student (user_id, major, year_level)
        VALUES (%s, %s, %s)
    """, batch)
    conn.commit()
    if (batch_start // BATCH_SIZE + 1) % 10 == 0:
        print(f"  Students: {batch_start + BATCH_SIZE} / 100000")

# Fetch all student_ids
cursor.execute("SELECT student_id FROM student ORDER BY student_id")
student_ids = [row[0] for row in cursor.fetchall()]
print(f"  ✓ {len(student_ids)} students inserted")

# ============================================================
# STEP 4: INSERT 200 COURSES
# ============================================================
print("\n[4/13] Inserting 200 courses...")
course_ids = []
lecturer_course_plan = (
    lecturer_ids[:20] * 3 +
    lecturer_ids[20:80] * 2 +
    lecturer_ids[80:100]
)

for i in range(1, 201):
    prefix  = course_prefixes[i % len(course_prefixes)]
    subject = course_subjects[i % len(course_subjects)]
    lec_id  = lecturer_course_plan[i - 1]
    adm_id  = admin_ids[i % len(admin_ids)]
    cursor.execute("""
        INSERT INTO course (course_code, course_name, description, lecturer_id, created_by)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        f'CRS{i:04d}',
        f'{prefix} {subject}',
        'This course covers essential topics in the subject area.',
        lec_id,
        adm_id
    ))
    course_ids.append(cursor.lastrowid)

conn.commit()
print(f"  ✓ {len(course_ids)} courses inserted")

# ============================================================
# STEP 5: ENROLL STUDENTS (3-6 courses each, min 10 per course)
# ============================================================
print("\n[5/13] Enrolling students...")

enrollment_set = set()
enrollment_batch = []

# Enroll ALL students in 3-6 courses (no one exceeds 6)
student_course_counts = {sid: 0 for sid in student_ids}

for sid in student_ids:
    num_courses = random.randint(3, 6)
    chosen = random.sample(course_ids, num_courses)
    for cid in chosen:
        key = (sid, cid)
        if key not in enrollment_set:
            enrollment_set.add(key)
            enrollment_batch.append((sid, cid, random_date(365)))
            student_course_counts[sid] += 1

# Top up any course that has fewer than 10 students
course_counts = {}
for sid, cid, _ in enrollment_batch:
    course_counts[cid] = course_counts.get(cid, 0) + 1

for cid in course_ids:
    while course_counts.get(cid, 0) < 10:
        for sid in student_ids:
            if student_course_counts[sid] < 6 and (sid, cid) not in enrollment_set:
                key = (sid, cid)
                enrollment_set.add(key)
                enrollment_batch.append((sid, cid, random_date(365)))
                student_course_counts[sid] += 1
                course_counts[cid] = course_counts.get(cid, 0) + 1
                break

    # Insert in batches
    if len(enrollment_batch) >= BATCH_SIZE:
        cursor.executemany("""
            INSERT IGNORE INTO enrollment (student_id, course_id, enrollment_at)
            VALUES (%s, %s, %s)
        """, enrollment_batch)
        conn.commit()
        enrollment_batch = []

# Insert remaining
if enrollment_batch:
    cursor.executemany("""
        INSERT IGNORE INTO enrollment (student_id, course_id, enrollment_at)
        VALUES (%s, %s, %s)
    """, enrollment_batch)
    conn.commit()

print(f"  ✓ {len(enrollment_set)} enrollments inserted")

# ============================================================
# STEP 6: INSERT SECTIONS (3 per course)
# ============================================================
print("\n[6/13] Inserting sections...")
section_titles = ['Introduction', 'Core Concepts', 'Advanced Topics']
section_ids_by_course = {}
section_batch = []

for cid in course_ids:
    section_ids_by_course[cid] = []
    for j, title in enumerate(section_titles, start=1):
        section_batch.append((cid, f'Section {j}: {title}', j))

cursor.executemany("""
    INSERT INTO section (course_id, section_title, section_order)
    VALUES (%s, %s, %s)
""", section_batch)
conn.commit()

cursor.execute("SELECT section_id, course_id FROM section ORDER BY section_id")
sections = cursor.fetchall()
section_ids = [row[0] for row in sections]
print(f"  ✓ {len(section_ids)} sections inserted")

# ============================================================
# STEP 7: INSERT SECTION ITEMS (2 per section)
# ============================================================
print("\n[7/13] Inserting section items...")

# Build a course -> lecturer map
cursor.execute("SELECT course_id, lecturer_id FROM course")
course_lecturer_map = {row[0]: row[1] for row in cursor.fetchall()}

# Build section -> course map
cursor.execute("SELECT section_id, course_id FROM section")
section_course_map = {row[0]: row[1] for row in cursor.fetchall()}

item_batch = []
for sec_id in section_ids:
    cid    = section_course_map[sec_id]
    lec_id = course_lecturer_map.get(cid)
    for j in range(1, 3):
        item_batch.append((
            sec_id,
            lec_id,
            f'{item_titles[(sec_id + j) % len(item_titles)]} - Section {sec_id}',
            item_types[j % len(item_types)],
            f'https://school.edu/content/{sec_id}/{j}'
        ))

cursor.executemany("""
    INSERT INTO section_item (section_id, uploaded_by, item_title, item_type, item_url)
    VALUES (%s, %s, %s, %s, %s)
""", item_batch)
conn.commit()
print(f"  ✓ {len(item_batch)} section items inserted")

# ============================================================
# STEP 8: INSERT ASSIGNMENTS (2 per course)
# ============================================================
print("\n[8/13] Inserting assignments...")
assignment_batch = []
assignment_ids_by_course = {}

for cid in course_ids:
    lec_id = course_lecturer_map.get(cid)
    if not lec_id:
        continue
    assignment_ids_by_course[cid] = []
    for j in range(1, 3):
        atype = assign_types[(cid + j) % len(assign_types)]
        assignment_batch.append((
            cid,
            lec_id,
            f'Assignment {j}: {atype}',
            'Complete all required tasks and submit before the due date.',
            (datetime.now() + timedelta(days=j * 30)).date(),
            100.00
        ))

cursor.executemany("""
    INSERT INTO assignment (course_id, created_by, assignment_title, description, due_date, max_grade)
    VALUES (%s, %s, %s, %s, %s, %s)
""", assignment_batch)
conn.commit()

cursor.execute("SELECT assignment_id, course_id FROM assignment")
assignments = cursor.fetchall()
assignment_ids = [row[0] for row in assignments]
for aid, cid in assignments:
    if cid not in assignment_ids_by_course:
        assignment_ids_by_course[cid] = []
    assignment_ids_by_course[cid].append(aid)

print(f"  ✓ {len(assignment_ids)} assignments inserted")

# ============================================================
# STEP 9: INSERT SUBMISSIONS (batch)
# ============================================================
print("\n[9/13] Inserting submissions...")

cursor.execute("SELECT student_id, course_id FROM enrollment")
enrollments = cursor.fetchall()

submission_batch = []
submission_set = set()

for sid, cid in enrollments:
    for aid in assignment_ids_by_course.get(cid, []):
        key = (aid, sid)
        if key not in submission_set:
            submission_set.add(key)
            submission_batch.append((
                aid,
                sid,
                f'Submission for assignment {aid} by student {sid}.',
                random_date(20),
                round(random.uniform(50, 100), 2)
            ))

        if len(submission_batch) >= BATCH_SIZE:
            cursor.executemany("""
                INSERT IGNORE INTO submission
                (assignment_id, student_id, submission_text, submitted_at, grade)
                VALUES (%s, %s, %s, %s, %s)
            """, submission_batch)
            conn.commit()
            submission_batch = []

if submission_batch:
    cursor.executemany("""
        INSERT IGNORE INTO submission
        (assignment_id, student_id, submission_text, submitted_at, grade)
        VALUES (%s, %s, %s, %s, %s)
    """, submission_batch)
    conn.commit()

print(f"  ✓ {len(submission_set)} submissions inserted")

# ============================================================
# STEP 10: INSERT CALENDAR EVENTS (2 per course)
# ============================================================
print("\n[10/13] Inserting calendar events...")

cursor.execute("""
    SELECT c.course_id, u.user_id
    FROM course c
    JOIN lecturer l ON c.lecturer_id = l.lecturer_id
    JOIN user u ON l.user_id = u.user_id
""")
course_user_map = cursor.fetchall()

event_batch = []
for cid, uid in course_user_map:
    for j in range(1, 3):
        event_batch.append((
            cid,
            uid,
            event_titles[(cid + j) % len(event_titles)],
            'Please attend this event. Bring all required materials.',
            (datetime.now() + timedelta(days=j * 45)).date(),
            '09:00:00',
            '11:00:00'
        ))

cursor.executemany("""
    INSERT INTO calendar_event
    (course_id, created_by, event_title, event_description, event_date, start_time, end_time)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", event_batch)
conn.commit()
print(f"  ✓ {len(event_batch)} calendar events inserted")

# ============================================================
# STEP 11: INSERT DISCUSSION FORUMS (1 per course)
# ============================================================
print("\n[11/13] Inserting discussion forums...")

cursor.execute("SELECT c.course_id, c.course_name, u.user_id FROM course c JOIN lecturer l ON c.lecturer_id = l.lecturer_id JOIN user u ON l.user_id = u.user_id")
course_info = cursor.fetchall()

forum_batch = []
for cid, cname, uid in course_info:
    forum_batch.append((
        cid,
        uid,
        f'General Discussion - {cname}',
        random_date(180)
    ))

cursor.executemany("""
    INSERT INTO discussion_forum (course_id, created_by, forum_title, created_at)
    VALUES (%s, %s, %s, %s)
""", forum_batch)
conn.commit()

cursor.execute("SELECT forum_id FROM discussion_forum ORDER BY forum_id")
forum_ids = [row[0] for row in cursor.fetchall()]
print(f"  ✓ {len(forum_ids)} forums inserted")

# ============================================================
# STEP 12: INSERT DISCUSSION THREADS (2 per forum)
# ============================================================
print("\n[12/13] Inserting discussion threads...")
thread_batch = []

for fid in forum_ids:
    for j in range(1, 3):
        uid = student_user_ids[(fid + j) % len(student_user_ids)]
        thread_batch.append((
            fid,
            uid,
            thread_titles[(fid + j) % len(thread_titles)],
            'Hi everyone, I wanted to start a discussion. Please share your thoughts.',
            random_date(90)
        ))

cursor.executemany("""
    INSERT INTO discussion_thread (forum_id, user_id, thread_title, starting_post, created_at)
    VALUES (%s, %s, %s, %s, %s)
""", thread_batch)
conn.commit()

cursor.execute("SELECT thread_id FROM discussion_thread ORDER BY thread_id")
thread_ids = [row[0] for row in cursor.fetchall()]
print(f"  ✓ {len(thread_ids)} threads inserted")

# ============================================================
# STEP 13: INSERT REPLIES (3 per thread + nested replies)
# ============================================================
print("\n[13/13] Inserting replies...")
reply_batch = []

for tid in thread_ids:
    for j in range(1, 4):
        uid = student_user_ids[(tid + j) % len(student_user_ids)]
        reply_batch.append((
            tid,
            uid,
            None,
            reply_texts[(tid + j) % len(reply_texts)],
            random_date(60)
        ))

cursor.executemany("""
    INSERT INTO reply (thread_id, user_id, parent_reply_id, reply_text, created_at)
    VALUES (%s, %s, %s, %s, %s)
""", reply_batch)
conn.commit()

# Nested replies (1 per top-level reply)
cursor.execute("SELECT reply_id, thread_id FROM reply WHERE parent_reply_id IS NULL")
top_replies = cursor.fetchall()

nested_batch = []
for rid, tid in top_replies:
    uid = student_user_ids[(rid + 1) % len(student_user_ids)]
    nested_batch.append((
        tid,
        uid,
        rid,
        'Thanks for your reply! That really helps clarify things.',
        random_date(30)
    ))

    if len(nested_batch) >= BATCH_SIZE:
        cursor.executemany("""
            INSERT INTO reply (thread_id, user_id, parent_reply_id, reply_text, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, nested_batch)
        conn.commit()
        nested_batch = []

if nested_batch:
    cursor.executemany("""
        INSERT INTO reply (thread_id, user_id, parent_reply_id, reply_text, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, nested_batch)
    conn.commit()

nested_count = len(top_replies)
print(f"  ✓ {len(reply_batch) + nested_count} replies inserted")

# ============================================================
# VERIFICATION
# ============================================================
print("\n============ VERIFICATION ============")

checks = [
    ("Total users",    "SELECT COUNT(*) FROM user"),
    ("Total students", "SELECT COUNT(*) FROM student"),
    ("Total courses",  "SELECT COUNT(*) FROM course"),
    ("Total enrollments", "SELECT COUNT(*) FROM enrollment"),
    ("Students > 6 courses (should be 0)",
     "SELECT COUNT(*) FROM (SELECT student_id FROM enrollment GROUP BY student_id HAVING COUNT(*) > 6) t"),
    ("Courses < 10 students (should be 0)",
     "SELECT COUNT(*) FROM (SELECT course_id FROM enrollment GROUP BY course_id HAVING COUNT(*) < 10) t"),
    ("Lecturers > 5 courses (should be 0)",
     "SELECT COUNT(*) FROM (SELECT lecturer_id FROM course GROUP BY lecturer_id HAVING COUNT(*) > 5) t"),
    ("Students < 3 courses (should be 0)",
     "SELECT COUNT(*) FROM (SELECT student_id FROM enrollment GROUP BY student_id HAVING COUNT(*) < 3) t"),
]

for label, query in checks:
    cursor.execute(query)
    result = cursor.fetchone()[0]
    status = "✓" if "should be 0" not in label or result == 0 else "✗ PROBLEM"
    print(f"  {status} {label}: {result}")

cursor.close()
conn.close()
print("\nDone! Database fully populated.")
