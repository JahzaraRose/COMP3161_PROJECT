function getApiBase() {
  const raw = import.meta.env.VITE_API_BASE_URL || "/api";
  const base = raw.trim().replace(/\/+$/, "");

  if (base.startsWith("/") || /^https?:\/\//i.test(base)) {
    return base;
  }

  return `http://${base}`;
}

const BASE = getApiBase();

function getToken() {
  return localStorage.getItem("token");
}

async function req(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(BASE + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Could not connect to the API. Check VITE_API_BASE_URL and make sure the backend is running.");
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function queryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

export const api = {
  // Auth
  login:    (b) => req("POST", "/login", b),
  register: (b) => req("POST", "/register", b),

  // Courses
  getCoursesPage:      (params) => req("GET", `/courses${queryString(params)}`),
  getCourses:          async (params) => {
    const data = await req("GET", `/courses${queryString(params)}`);
    return Array.isArray(data) ? data : data.courses;
  },
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
