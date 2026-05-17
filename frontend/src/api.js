const BASE = "/api";

function getToken() {
  return localStorage.getItem("token");
}

async function req(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(BASE + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

export const api = {
  // Auth
  login:    (b) => req("POST", "/login", b),
  register: (b) => req("POST", "/register", b),

  // Courses
  getCourses:          ()    => req("GET",  "/courses"),
  createCourse:        (b)   => req("POST", "/courses", b),
  getStudentCourses:   (sid) => req("GET",  `/courses/student/${sid}`),
  getLecturerCourses:  (lid) => req("GET",  `/courses/lecturer/${lid}`),
  getCourseMembers:    (cid) => req("GET",  `/courses/${cid}/members`),
  assignLecturer:      (cid, b) => req("POST", `/courses/${cid}/assign-lecturer`, b),

  // Enrollment
  enroll: (cid) => req("POST", `/courses/${cid}/enroll`),

  // Content
  getCourseContent: (cid) => req("GET",  `/courses/${cid}/content`),
  createSection:    (cid, b) => req("POST", `/courses/${cid}/sections`, b),
  addSectionItem:   (sid, b) => req("POST", `/sections/${sid}/items`, b),

  // Assignments
  getCourseAssignments:  (cid) => req("GET",  `/courses/${cid}/assignments`),
  createAssignment:      (cid, b) => req("POST", `/courses/${cid}/assignments`, b),
  submitAssignment:      (aid, b) => req("POST", `/assignments/${aid}/submit`, b),
  getSubmissions:        (aid) => req("GET",  `/assignments/${aid}/submissions`),
  gradeSubmission:       (sid, b) => req("POST", `/submissions/${sid}/grade`, b),
  getStudentSubmissions: (sid) => req("GET",  `/students/${sid}/submissions`),
  getStudentAverage:     (sid) => req("GET",  `/students/${sid}/average`),

  // Calendar
  getCourseEvents:  (cid) => req("GET",  `/courses/${cid}/events`),
  getStudentEvents: (sid, date) =>
    req("GET", `/students/${sid}/events${date ? `?date=${date}` : ""}`),
  createEvent: (cid, b) => req("POST", `/courses/${cid}/events`, b),

  // Forums
  getForums:    (cid) => req("GET",  `/courses/${cid}/forums`),
  createForum:  (cid, b) => req("POST", `/courses/${cid}/forums`, b),
  getThreads:   (fid) => req("GET",  `/forums/${fid}/threads`),
  createThread: (fid, b) => req("POST", `/forums/${fid}/threads`, b),
  getReplies:   (tid) => req("GET",  `/threads/${tid}/replies`),
  createReply:  (tid, b) => req("POST", `/threads/${tid}/replies`, b),

  // Reports (admin only)
  reportCourses50Plus:  () => req("GET", "/reports/courses-50-plus"),
  reportStudents5Plus:  () => req("GET", "/reports/students-5-plus-courses"),
  reportLecturers3Plus: () => req("GET", "/reports/lecturers-3-plus-courses"),
  reportTop10Courses:   () => req("GET", "/reports/top-10-enrolled-courses"),
  reportTop10Students:  () => req("GET", "/reports/top-10-students"),
};
