import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function CoursesPage() {
  const { user }               = useAuth();
  const [courses, setCourses]  = useState([]);
  const [pagination, setPagination] = useState({ page: 1, per_page: 20, total: 0, total_pages: 1 });
  const [search, setSearch]    = useState("");
  const [loading, setLoading]  = useState(true);
  const [enrolling, setEnrolling] = useState(null);
  const [msg, setMsg]          = useState("");

  // For admin: create course form
  const [showCreate, setShowCreate] = useState(false);
  const [newCourse, setNewCourse]   = useState({ course_name: "", course_code: "", description: "" });
  const [creating, setCreating]     = useState(false);

  const loadCourses = async (page = 1) => {
    setLoading(true);
    try {
      const data = await api.getCoursesPage({ page, per_page: pagination.per_page });
      if (Array.isArray(data)) {
        setCourses(data);
        setPagination({ page: 1, per_page: data.length, total: data.length, total_pages: 1 });
      } else {
        setCourses(data.courses || []);
        setPagination(data.pagination || { page, per_page: 20, total: data.courses?.length || 0, total_pages: 1 });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses(1);
  }, []);

  const handleEnroll = async (courseId) => {
    setEnrolling(courseId);
    setMsg("");
    try {
      await api.enroll(courseId);
      setMsg("Enrolled successfully!");
    } catch (err) {
      setMsg(err.message);
    } finally {
      setEnrolling(null);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.createCourse(newCourse);
      await loadCourses(1);
      setShowCreate(false);
      setNewCourse({ course_name: "", course_code: "", description: "" });
    } catch (err) {
      setMsg(err.message);
    } finally {
      setCreating(false);
    }
  };

  const filtered = courses.filter(
    (c) =>
      c.course_name.toLowerCase().includes(search.toLowerCase()) ||
      c.course_code.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="loading">Loading courses...</div>;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Courses</h1>
        {user.role === "admin" && (
          <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
            {showCreate ? "Cancel" : "+ New Course"}
          </button>
        )}
      </div>

      {msg && <div className="alert alert-info">{msg}</div>}

      {/* Admin: create course form */}
      {showCreate && user.role === "admin" && (
        <div className="card mb-4">
          <h3>Create New Course</h3>
          <form onSubmit={handleCreate}>
            <div className="form-row">
              <div className="form-group">
                <label>Course Code</label>
                <input value={newCourse.course_code}
                  onChange={(e) => setNewCourse({ ...newCourse, course_code: e.target.value })}
                  placeholder="e.g. COMP3161" required />
              </div>
              <div className="form-group">
                <label>Course Name</label>
                <input value={newCourse.course_name}
                  onChange={(e) => setNewCourse({ ...newCourse, course_name: e.target.value })}
                  placeholder="e.g. Database Management" required />
              </div>
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea value={newCourse.description}
                onChange={(e) => setNewCourse({ ...newCourse, description: e.target.value })}
                rows={3} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? "Creating..." : "Create Course"}
            </button>
          </form>
        </div>
      )}

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search by course name or code..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="result-row">
        <p className="result-count">
          Showing {filtered.length} of {pagination.total || filtered.length} courses
          {search && " on this page"}
        </p>
        <div className="pagination-controls">
          <button
            className="btn btn-outline btn-sm"
            onClick={() => loadCourses(pagination.page - 1)}
            disabled={pagination.page <= 1}
          >
            Previous
          </button>
          <span className="pagination-status">
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => loadCourses(pagination.page + 1)}
            disabled={pagination.page >= pagination.total_pages}
          >
            Next
          </button>
        </div>
      </div>

      <div className="course-grid">
        {filtered.map((c) => (
          <div key={c.course_id} className="course-card">
            <div className="course-card-code">{c.course_code}</div>
            <div className="course-card-name">{c.course_name}</div>
            {c.first_name && (
              <div className="course-card-lecturer">
                {c.first_name} {c.last_name}
              </div>
            )}
            <div className="course-card-actions">
              <Link to={`/courses/${c.course_id}`} className="btn btn-outline btn-sm">
                View
              </Link>
              {user.role === "student" && (
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => handleEnroll(c.course_id)}
                  disabled={enrolling === c.course_id}
                >
                  {enrolling === c.course_id ? "..." : "Enroll"}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
