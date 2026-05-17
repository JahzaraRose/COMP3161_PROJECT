-- ============================================================
-- COURSE MANAGEMENT SYSTEM - DATA POPULATION SCRIPT
-- MySQL Version
-- ============================================================

USE comp3161_project;

-- Turn off safe mode and foreign key checks for bulk inserts
SET SQL_SAFE_UPDATES = 0;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- STEP 1: INSERT 5 ADMIN USERS
-- ============================================================
DROP PROCEDURE IF EXISTS insert_admins;
DELIMITER //
CREATE PROCEDURE insert_admins()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 5 DO
        INSERT INTO user (username, password_hash, first_name, last_name, email, role)
        VALUES (
            CONCAT('admin', i),
            '$2b$12$adminhashplaceholder',
            'Admin',
            CONCAT('User', i),
            CONCAT('admin', i, '@school.edu'),
            'admin'
        );
        INSERT INTO admin (user_id) VALUES (LAST_INSERT_ID());
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL insert_admins();


-- ============================================================
-- STEP 2: INSERT 100 LECTURERS
-- ============================================================
DROP PROCEDURE IF EXISTS insert_lecturers;
DELIMITER //
CREATE PROCEDURE insert_lecturers()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE dept VARCHAR(100);
    WHILE i <= 100 DO
        SET dept = ELT((i % 10) + 1,
            'Computer Science', 'Mathematics', 'Physics', 'Chemistry',
            'Biology', 'Engineering', 'Business', 'Economics',
            'Psychology', 'Literature'
        );
        INSERT INTO user (username, password_hash, first_name, last_name, email, role)
        VALUES (
            CONCAT('lecturer', i),
            '$2b$12$lecturerhashplaceholder',
            ELT((i % 10) + 1, 'James','Maria','John','Sarah','David','Emma','Michael','Lisa','Robert','Anna'),
            CONCAT('Lecturer', i),
            CONCAT('lecturer', i, '@school.edu'),
            'lecturer'
        );
        INSERT INTO lecturer (user_id, department) VALUES (LAST_INSERT_ID(), dept);
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL insert_lecturers();


-- ============================================================
-- STEP 3: INSERT 100,000 STUDENTS
-- ============================================================
DROP PROCEDURE IF EXISTS insert_students;
DELIMITER //
CREATE PROCEDURE insert_students()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE fname VARCHAR(50);
    DECLARE lname VARCHAR(50);
    DECLARE maj VARCHAR(100);
    DECLARE yr INT;

    WHILE i <= 100000 DO
        SET fname = ELT((i % 20) + 1,
            'James','Maria','John','Sarah','David','Emma','Michael','Lisa','Robert','Anna',
            'Chris','Sophia','Daniel','Olivia','Matthew','Isabella','Andrew','Mia','Joshua','Ava'
        );
        SET lname = ELT((i % 20) + 1,
            'Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Wilson','Moore',
            'Taylor','Anderson','Thomas','Jackson','White','Harris','Martin','Thompson','Young','King'
        );
        SET maj = ELT((i % 10) + 1,
            'Computer Science','Mathematics','Physics','Chemistry','Biology',
            'Engineering','Business','Economics','Psychology','Literature'
        );
        SET yr = (i % 4) + 1;

        INSERT INTO user (username, password_hash, first_name, last_name, email, role)
        VALUES (
            CONCAT('student', i),
            '$2b$12$studenthashplaceholder',
            fname,
            lname,
            CONCAT('student', i, '@school.edu'),
            'student'
        );
        INSERT INTO student (user_id, major, year_level) VALUES (LAST_INSERT_ID(), maj, yr);
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL insert_students();


-- ============================================================
-- STEP 4: INSERT 200 COURSES
-- ============================================================
DROP PROCEDURE IF EXISTS insert_courses;
DELIMITER //
CREATE PROCEDURE insert_courses()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE lec_id INT;
    DECLARE adm_id INT;
    DECLARE cname VARCHAR(150);
    DECLARE prefix VARCHAR(50);
    DECLARE subject VARCHAR(50);

    WHILE i <= 200 DO
        SET prefix = ELT((i % 10) + 1,
            'Introduction to','Advanced','Fundamentals of','Applied',
            'Principles of','Topics in','Special Topics in','Research in',
            'Seminar in','Theory of'
        );
        SET subject = ELT((i % 20) + 1,
            'Computer Science','Mathematics','Physics','Chemistry',
            'Biology','Engineering','Business','Economics',
            'Psychology','Data Science','Networking','Databases',
            'Algorithms','Statistics','Calculus','Linear Algebra',
            'Organic Chemistry','Mechanics','Microeconomics','Accounting'
        );
        SET cname = CONCAT(prefix, ' ', subject);

        -- Assign lecturer round-robin (1 to 100, max 5 courses each = 500 slots)
        SELECT lecturer_id INTO lec_id
        FROM lecturer
        ORDER BY lecturer_id
        LIMIT 1 OFFSET ((i - 1) % 100);

        -- Assign admin round-robin
        SELECT admin_id INTO adm_id
        FROM admin
        ORDER BY admin_id
        LIMIT 1 OFFSET ((i - 1) % 5);

        INSERT INTO course (course_code, course_name, description, lecturer_id, created_by)
        VALUES (
            CONCAT('CRS', LPAD(i, 4, '0')),
            cname,
            'This course covers essential topics in the subject area.',
            lec_id,
            adm_id
        );
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL insert_courses();


-- ============================================================
-- STEP 5: ENROLL STUDENTS IN COURSES
--   - Every student gets 3-6 courses
--   - Deterministic spread across 200 courses gives every course far more than 10 members
-- ============================================================
DROP PROCEDURE IF EXISTS insert_enrollments;
DELIMITER //
CREATE PROCEDURE insert_enrollments()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE j INT DEFAULT 1;
    DECLARE num_courses INT;
    DECLARE course_offset INT;
    DECLARE sid INT;
    DECLARE cid INT;

    WHILE i <= 100000 DO
        SELECT student_id INTO sid FROM student ORDER BY student_id LIMIT 1 OFFSET (i - 1);
        SET num_courses = 3 + (i % 4);  -- 3 to 6 courses
        SET j = 1;
        WHILE j <= num_courses DO
            SET course_offset = ((i * 7 + j * 13) % 200);
            SELECT course_id INTO cid FROM course ORDER BY course_id LIMIT 1 OFFSET course_offset;
            INSERT IGNORE INTO enrollment (student_id, course_id, enrollment_at)
            VALUES (sid, cid, NOW() - INTERVAL FLOOR(RAND() * 365) DAY);
            SET j = j + 1;
        END WHILE;
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL insert_enrollments();


-- ============================================================
-- STEP 6: INSERT SECTIONS (3 per course)
-- ============================================================
DROP PROCEDURE IF EXISTS insert_sections;
DELIMITER //
CREATE PROCEDURE insert_sections()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE cid INT;
    DECLARE sec_num INT;
    DECLARE sec_title VARCHAR(150);

    DECLARE cur CURSOR FOR SELECT course_id FROM course;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;
    course_loop: LOOP
        FETCH cur INTO cid;
        IF done THEN LEAVE course_loop; END IF;
        SET sec_num = 1;
        WHILE sec_num <= 3 DO
            SET sec_title = ELT(sec_num,
                'Introduction',
                'Core Concepts',
                'Advanced Topics'
            );
            INSERT INTO section (course_id, section_title, section_order)
            VALUES (cid, CONCAT('Section ', sec_num, ': ', sec_title), sec_num);
            SET sec_num = sec_num + 1;
        END WHILE;
    END LOOP;
    CLOSE cur;
END //
DELIMITER ;
CALL insert_sections();


-- ============================================================
-- STEP 7: INSERT SECTION ITEMS (2 per section)
-- ============================================================
DROP PROCEDURE IF EXISTS insert_section_items;
DELIMITER //
CREATE PROCEDURE insert_section_items()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE sid INT;
    DECLARE cid INT;
    DECLARE lec_id INT;
    DECLARE item_num INT;
    DECLARE itype VARCHAR(10);

    DECLARE cur CURSOR FOR SELECT s.section_id, s.course_id FROM section s;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;
    sec_loop: LOOP
        FETCH cur INTO sid, cid;
        IF done THEN LEAVE sec_loop; END IF;

        SELECT lecturer_id INTO lec_id FROM course WHERE course_id = cid;

        SET item_num = 1;
        WHILE item_num <= 2 DO
            SET itype = ELT((item_num % 3) + 1, 'file', 'link', 'slide');
            INSERT INTO section_item (section_id, uploaded_by, item_title, item_type, item_url)
            VALUES (
                sid,
                lec_id,
                CONCAT(ELT((item_num % 5) + 1,
                    'Lecture Slides','Reading Material','Tutorial Video',
                    'Assignment Brief','Reference Guide'
                ), ' - Section ', sid),
                itype,
                CONCAT('https://school.edu/content/', sid, '/', item_num)
            );
            SET item_num = item_num + 1;
        END WHILE;
    END LOOP;
    CLOSE cur;
END //
DELIMITER ;
CALL insert_section_items();


-- ============================================================
-- STEP 8: INSERT ASSIGNMENTS (2 per course)
-- ============================================================
DROP PROCEDURE IF EXISTS insert_assignments;
DELIMITER //
CREATE PROCEDURE insert_assignments()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE cid INT;
    DECLARE lec_id INT;
    DECLARE assign_num INT;

    DECLARE cur CURSOR FOR SELECT course_id, lecturer_id FROM course WHERE lecturer_id IS NOT NULL;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;
    course_loop: LOOP
        FETCH cur INTO cid, lec_id;
        IF done THEN LEAVE course_loop; END IF;

        SET assign_num = 1;
        WHILE assign_num <= 2 DO
            INSERT INTO assignment (course_id, created_by, assignment_title, description, due_date, max_grade)
            VALUES (
                cid,
                lec_id,
                CONCAT('Assignment ', assign_num, ': ',
                    ELT(((cid + assign_num) % 5) + 1,
                        'Problem Set','Research Paper','Project','Lab Report','Case Study'
                    )
                ),
                'Complete all required tasks and submit before the due date.',
                DATE_ADD(CURDATE(), INTERVAL (assign_num * 30) DAY),
                100.00
            );
            SET assign_num = assign_num + 1;
        END WHILE;
    END LOOP;
    CLOSE cur;
END //
DELIMITER ;
CALL insert_assignments();


-- ============================================================
-- STEP 9: INSERT SUBMISSIONS
--   Every enrolled student submits every assignment for
--   their courses, with a random grade between 50-100
-- ============================================================
INSERT IGNORE INTO submission (assignment_id, student_id, submission_text, submitted_at, grade)
SELECT
    a.assignment_id,
    e.student_id,
    CONCAT('Submission for assignment ', a.assignment_id, ' by student ', e.student_id),
    NOW() - INTERVAL FLOOR(RAND() * 20) DAY,
    ROUND(50 + (RAND() * 50), 2)
FROM enrollment e
JOIN assignment a ON a.course_id = e.course_id;


-- ============================================================
-- STEP 10: INSERT CALENDAR EVENTS (2 per course)
-- ============================================================
DROP PROCEDURE IF EXISTS insert_calendar_events;
DELIMITER //
CREATE PROCEDURE insert_calendar_events()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE cid INT;
    DECLARE uid INT;
    DECLARE ev_num INT;

    DECLARE cur CURSOR FOR
        SELECT c.course_id, u.user_id
        FROM course c
        JOIN lecturer l ON c.lecturer_id = l.lecturer_id
        JOIN user u ON l.user_id = u.user_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;
    course_loop: LOOP
        FETCH cur INTO cid, uid;
        IF done THEN LEAVE course_loop; END IF;

        SET ev_num = 1;
        WHILE ev_num <= 2 DO
            INSERT INTO calendar_event (course_id, created_by, event_title, event_description, event_date, start_time, end_time)
            VALUES (
                cid,
                uid,
                ELT(((cid + ev_num) % 5) + 1,
                    'Midterm Exam','Final Exam','Guest Lecture',
                    'Lab Session','Project Presentation'
                ),
                'Please attend this event. Bring all required materials.',
                DATE_ADD(CURDATE(), INTERVAL (ev_num * 45) DAY),
                '09:00:00',
                '11:00:00'
            );
            SET ev_num = ev_num + 1;
        END WHILE;
    END LOOP;
    CLOSE cur;
END //
DELIMITER ;
CALL insert_calendar_events();


-- ============================================================
-- STEP 11: INSERT DISCUSSION FORUMS (1 per course)
-- ============================================================
INSERT INTO discussion_forum (course_id, created_by, forum_title, created_at)
SELECT
    c.course_id,
    u.user_id,
    CONCAT('General Discussion - ', c.course_name),
    NOW() - INTERVAL FLOOR(RAND() * 180) DAY
FROM course c
JOIN lecturer l ON c.lecturer_id = l.lecturer_id
JOIN user u ON l.user_id = u.user_id;


-- ============================================================
-- STEP 12: INSERT DISCUSSION THREADS (2 per forum)
-- ============================================================
DROP PROCEDURE IF EXISTS insert_threads;
DELIMITER //
CREATE PROCEDURE insert_threads()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE fid INT;
    DECLARE uid INT;
    DECLARE thr_num INT;

    DECLARE cur CURSOR FOR SELECT forum_id FROM discussion_forum;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;
    forum_loop: LOOP
        FETCH cur INTO fid;
        IF done THEN LEAVE forum_loop; END IF;

        -- Pick a student user
        SELECT u.user_id INTO uid
        FROM user u
        WHERE u.role = 'student'
        ORDER BY u.user_id
        LIMIT 1 OFFSET (fid % 1000);

        SET thr_num = 1;
        WHILE thr_num <= 2 DO
            INSERT INTO discussion_thread (forum_id, user_id, thread_title, starting_post, created_at)
            VALUES (
                fid,
                uid,
                ELT(((fid + thr_num) % 5) + 1,
                    'Question about the syllabus',
                    'Help with assignment',
                    'Study group formation',
                    'Clarification on lecture material',
                    'Exam preparation tips'
                ),
                'Hi everyone, I wanted to start a discussion. Please share your thoughts.',
                NOW() - INTERVAL FLOOR(RAND() * 90) DAY
            );
            SET thr_num = thr_num + 1;
        END WHILE;
    END LOOP;
    CLOSE cur;
END //
DELIMITER ;
CALL insert_threads();


-- ============================================================
-- STEP 13: INSERT REPLIES (3 top-level per thread)
-- ============================================================
DROP PROCEDURE IF EXISTS insert_replies;
DELIMITER //
CREATE PROCEDURE insert_replies()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE tid INT;
    DECLARE uid INT;
    DECLARE rep_num INT;

    DECLARE cur CURSOR FOR SELECT thread_id FROM discussion_thread;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;
    thread_loop: LOOP
        FETCH cur INTO tid;
        IF done THEN LEAVE thread_loop; END IF;

        SET rep_num = 1;
        WHILE rep_num <= 3 DO
            SELECT u.user_id INTO uid
            FROM user u
            WHERE u.role = 'student'
            ORDER BY u.user_id
            LIMIT 1 OFFSET ((tid + rep_num) % 1000);

            INSERT INTO reply (thread_id, user_id, parent_reply_id, reply_text, created_at)
            VALUES (
                tid,
                uid,
                NULL,
                ELT(((tid + rep_num) % 5) + 1,
                    'Great question! I was wondering the same thing.',
                    'I think the answer is in the lecture notes from week 3.',
                    'Has anyone asked the lecturer about this?',
                    'Thanks for bringing this up, very helpful.',
                    'I found a useful resource online that explains this well.'
                ),
                NOW() - INTERVAL FLOOR(RAND() * 60) DAY
            );
            SET rep_num = rep_num + 1;
        END WHILE;
    END LOOP;
    CLOSE cur;
END //
DELIMITER ;
CALL insert_replies();

-- Insert 1 nested reply per top-level reply
INSERT INTO reply (thread_id, user_id, parent_reply_id, reply_text, created_at)
SELECT
    r.thread_id,
    (SELECT user_id FROM user WHERE role = 'student' ORDER BY user_id LIMIT 1 OFFSET (r.reply_id % 1000)),
    r.reply_id,
    'Thanks for your reply! That really helps clarify things.',
    NOW() - INTERVAL FLOOR(RAND() * 30) DAY
FROM reply r
WHERE r.parent_reply_id IS NULL;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- VERIFICATION QUERIES
-- Run these to confirm all constraints are met
-- ============================================================

-- Total row counts
SELECT 'user'              AS tbl, COUNT(*) AS total FROM user
UNION ALL SELECT 'student',        COUNT(*) FROM student
UNION ALL SELECT 'lecturer',       COUNT(*) FROM lecturer
UNION ALL SELECT 'admin',          COUNT(*) FROM admin
UNION ALL SELECT 'course',         COUNT(*) FROM course
UNION ALL SELECT 'enrollment',     COUNT(*) FROM enrollment
UNION ALL SELECT 'section',        COUNT(*) FROM section
UNION ALL SELECT 'section_item',   COUNT(*) FROM section_item
UNION ALL SELECT 'assignment',     COUNT(*) FROM assignment
UNION ALL SELECT 'submission',     COUNT(*) FROM submission
UNION ALL SELECT 'calendar_event', COUNT(*) FROM calendar_event
UNION ALL SELECT 'discussion_forum',  COUNT(*) FROM discussion_forum
UNION ALL SELECT 'discussion_thread', COUNT(*) FROM discussion_thread
UNION ALL SELECT 'reply',          COUNT(*) FROM reply;

-- Should return NO rows (no student in more than 6 courses)
SELECT student_id, COUNT(*) AS course_count
FROM enrollment
GROUP BY student_id
HAVING COUNT(*) > 6;

-- Should return NO rows (all courses have at least 10 students)
SELECT course_id, COUNT(*) AS student_count
FROM enrollment
GROUP BY course_id
HAVING COUNT(*) < 10;

-- Should return NO rows (no lecturer teaches more than 5 courses)
SELECT lecturer_id, COUNT(*) AS course_count
FROM course
GROUP BY lecturer_id
HAVING COUNT(*) > 5;

-- Should return NO rows (all students in at least 3 courses)
SELECT student_id, COUNT(*) AS course_count
FROM enrollment
GROUP BY student_id
HAVING COUNT(*) < 3;
