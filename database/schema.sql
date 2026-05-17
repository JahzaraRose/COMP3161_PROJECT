-- ============================================================
-- DATABASE SCHEMA
-- ============================================================

CREATE DATABASE IF NOT EXISTS comp3161_project;
USE comp3161_project;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS reply;
DROP TABLE IF EXISTS discussion_thread;
DROP TABLE IF EXISTS discussion_forum;
DROP TABLE IF EXISTS submission;
DROP TABLE IF EXISTS assignment;
DROP TABLE IF EXISTS calendar_event;
DROP TABLE IF EXISTS section_item;
DROP TABLE IF EXISTS section;
DROP TABLE IF EXISTS enrollment;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS lecturer;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS user;

-- ============================================================
-- 1. USER
-- ============================================================
CREATE TABLE user (
    user_id       INT          AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    role          ENUM('admin', 'lecturer', 'student') NOT NULL
);

-- ============================================================
-- 2. STUDENT (ISA subtype of User)
-- ============================================================
CREATE TABLE student (
    student_id INT          AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL UNIQUE,
    major      VARCHAR(100),
    year_level INT          CHECK (year_level BETWEEN 1 AND 6),
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- ============================================================
-- 3. LECTURER (ISA subtype of User)
-- ============================================================
CREATE TABLE lecturer (
    lecturer_id INT          AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL UNIQUE,
    department  VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- ============================================================
-- 4. ADMIN (ISA subtype of User)
-- ============================================================
CREATE TABLE admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id  INT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- ============================================================
-- 5. COURSE
-- ============================================================
CREATE TABLE course (
    course_id   INT          AUTO_INCREMENT PRIMARY KEY,
    lecturer_id INT,
    created_by  INT          NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    course_code VARCHAR(20)  NOT NULL UNIQUE,
    description TEXT,
    FOREIGN KEY (lecturer_id) REFERENCES lecturer(lecturer_id) ON DELETE SET NULL,
    FOREIGN KEY (created_by)  REFERENCES admin(admin_id)       ON DELETE RESTRICT
);

-- ============================================================
-- 6. ENROLLMENT
-- ============================================================
CREATE TABLE enrollment (
    enrollment_id INT      AUTO_INCREMENT PRIMARY KEY,
    student_id    INT      NOT NULL,
    course_id     INT      NOT NULL,
    enrollment_at DATETIME NOT NULL DEFAULT NOW(),
    UNIQUE KEY uq_enrollment (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES course(course_id)   ON DELETE CASCADE
);

-- ============================================================
-- 7. SECTION
-- ============================================================
CREATE TABLE section (
    section_id    INT          AUTO_INCREMENT PRIMARY KEY,
    course_id     INT          NOT NULL,
    section_title VARCHAR(150) NOT NULL,
    section_order INT          NOT NULL DEFAULT 1,
    FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE
);

-- ============================================================
-- 8. SECTION_ITEM
-- ============================================================
CREATE TABLE section_item (
    item_id     INT          AUTO_INCREMENT PRIMARY KEY,
    section_id  INT          NOT NULL,
    uploaded_by INT,
    item_title  VARCHAR(150) NOT NULL,
    item_type   ENUM('link', 'file', 'slide') NOT NULL,
    item_url    VARCHAR(500),
    FOREIGN KEY (section_id)  REFERENCES section(section_id)   ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES lecturer(lecturer_id) ON DELETE SET NULL
);

-- ============================================================
-- 9. ASSIGNMENT
-- ============================================================
CREATE TABLE assignment (
    assignment_id    INT          AUTO_INCREMENT PRIMARY KEY,
    course_id        INT          NOT NULL,
    created_by       INT          NOT NULL,
    assignment_title VARCHAR(200) NOT NULL,
    description      TEXT,
    due_date         DATE,
    max_grade        DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    FOREIGN KEY (course_id)  REFERENCES course(course_id)      ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES lecturer(lecturer_id)  ON DELETE RESTRICT
);

-- ============================================================
-- 10. SUBMISSION
-- ============================================================
CREATE TABLE submission (
    submission_id   INT          AUTO_INCREMENT PRIMARY KEY,
    assignment_id   INT          NOT NULL,
    student_id      INT          NOT NULL,
    submission_text TEXT,
    submitted_at    DATETIME     NOT NULL DEFAULT NOW(),
    grade           DECIMAL(5,2) CHECK (grade >= 0),
    UNIQUE KEY uq_submission (assignment_id, student_id),
    FOREIGN KEY (assignment_id) REFERENCES assignment(assignment_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id)    REFERENCES student(student_id)       ON DELETE CASCADE
);

-- ============================================================
-- 11. CALENDAR_EVENT
-- ============================================================
CREATE TABLE calendar_event (
    event_id          INT          AUTO_INCREMENT PRIMARY KEY,
    course_id         INT          NOT NULL,
    created_by        INT          NOT NULL,
    event_title       VARCHAR(200) NOT NULL,
    event_description TEXT,
    event_date        DATE         NOT NULL,
    start_time        TIME,
    end_time          TIME,
    FOREIGN KEY (course_id)  REFERENCES course(course_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES user(user_id)     ON DELETE RESTRICT
);

-- ============================================================
-- 12. DISCUSSION_FORUM
-- ============================================================
CREATE TABLE discussion_forum (
    forum_id    INT          AUTO_INCREMENT PRIMARY KEY,
    course_id   INT          NOT NULL,
    created_by  INT,
    forum_title VARCHAR(200) NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT NOW(),
    FOREIGN KEY (course_id)  REFERENCES course(course_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES user(user_id)     ON DELETE SET NULL
);

-- ============================================================
-- 13. DISCUSSION_THREAD
-- ============================================================
CREATE TABLE discussion_thread (
    thread_id     INT          AUTO_INCREMENT PRIMARY KEY,
    forum_id      INT          NOT NULL,
    user_id       INT          NOT NULL,
    thread_title  VARCHAR(200) NOT NULL,
    starting_post TEXT         NOT NULL,
    created_at    DATETIME     NOT NULL DEFAULT NOW(),
    FOREIGN KEY (forum_id) REFERENCES discussion_forum(forum_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)  REFERENCES user(user_id)              ON DELETE CASCADE
);

-- ============================================================
-- 14. REPLY
--     parent_reply_id NULL  = top-level reply
--     parent_reply_id SET   = nested reply (Reddit-style)
-- ============================================================
CREATE TABLE reply (
    reply_id        INT      AUTO_INCREMENT PRIMARY KEY,
    thread_id       INT      NOT NULL,
    user_id         INT      NOT NULL,
    parent_reply_id INT      DEFAULT NULL,
    reply_text      TEXT     NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT NOW(),
    FOREIGN KEY (thread_id)       REFERENCES discussion_thread(thread_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)         REFERENCES user(user_id)                ON DELETE CASCADE,
    FOREIGN KEY (parent_reply_id) REFERENCES reply(reply_id)              ON DELETE CASCADE
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_enrollment_student  ON enrollment(student_id);
CREATE INDEX idx_enrollment_course   ON enrollment(course_id);
CREATE INDEX idx_course_lecturer     ON course(lecturer_id);
CREATE INDEX idx_course_created_by   ON course(created_by);
CREATE INDEX idx_section_course      ON section(course_id);
CREATE INDEX idx_section_item        ON section_item(section_id);
CREATE INDEX idx_section_item_upby   ON section_item(uploaded_by);
CREATE INDEX idx_assignment_course   ON assignment(course_id);
CREATE INDEX idx_assignment_created  ON assignment(created_by);
CREATE INDEX idx_submission_assign   ON submission(assignment_id);
CREATE INDEX idx_submission_student  ON submission(student_id);
CREATE INDEX idx_cal_event_course    ON calendar_event(course_id);
CREATE INDEX idx_cal_event_date      ON calendar_event(event_date);
-- Compound index: speeds up student-events query (WHERE e.student_id=? AND ce.event_date=?)
CREATE INDEX idx_cal_event_date_course ON calendar_event(event_date, course_id);
-- Compound index: speeds up submission average calculation per student
CREATE INDEX idx_submission_student_grade ON submission(student_id, grade);
CREATE INDEX idx_forum_course        ON discussion_forum(course_id);
CREATE INDEX idx_forum_created_by    ON discussion_forum(created_by);
CREATE INDEX idx_thread_forum        ON discussion_thread(forum_id);
CREATE INDEX idx_reply_thread        ON reply(thread_id);
CREATE INDEX idx_reply_parent        ON reply(parent_reply_id);

-- ============================================================
-- VIEWS (5 required reports)
-- ============================================================

-- Report 1: Courses with 50 or more students
CREATE OR REPLACE VIEW view_courses_50_plus AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
    COUNT(e.student_id) AS student_count
FROM course c
JOIN enrollment e ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_code, c.course_name
HAVING COUNT(e.student_id) >= 50;

-- Report 2: Students enrolled in 5 or more courses
CREATE OR REPLACE VIEW view_students_5_plus_courses AS
SELECT
    s.student_id,
    u.first_name,
    u.last_name,
    u.email,
    COUNT(e.course_id) AS course_count
FROM student s
JOIN user       u ON s.user_id    = u.user_id
JOIN enrollment e ON s.student_id = e.student_id
GROUP BY s.student_id, u.first_name, u.last_name, u.email
HAVING COUNT(e.course_id) >= 5;

-- Report 3: Lecturers teaching 3 or more courses
CREATE OR REPLACE VIEW view_lecturers_3_plus_courses AS
SELECT
    l.lecturer_id,
    u.first_name,
    u.last_name,
    u.email,
    COUNT(c.course_id) AS course_count
FROM lecturer l
JOIN user   u ON l.user_id     = u.user_id
JOIN course c ON l.lecturer_id = c.lecturer_id
GROUP BY l.lecturer_id, u.first_name, u.last_name, u.email
HAVING COUNT(c.course_id) >= 3;

-- Report 4: Top 10 most enrolled courses
CREATE OR REPLACE VIEW view_top_10_enrolled_courses AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
    COUNT(e.student_id) AS student_count
FROM course c
JOIN enrollment e ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_code, c.course_name
ORDER BY student_count DESC
LIMIT 10;

-- Report 5: Top 10 students by overall grade average
CREATE OR REPLACE VIEW view_top_10_students_avg AS
SELECT
    s.student_id,
    u.first_name,
    u.last_name,
    u.email,
    ROUND(
        AVG((sub.grade / a.max_grade) * 100)
    , 2) AS average_percentage
FROM student s
JOIN user        u   ON s.user_id         = u.user_id
JOIN submission  sub ON s.student_id      = sub.student_id
JOIN assignment  a   ON sub.assignment_id = a.assignment_id
WHERE sub.grade IS NOT NULL
GROUP BY s.student_id, u.first_name, u.last_name, u.email
ORDER BY average_percentage DESC
LIMIT 10;
