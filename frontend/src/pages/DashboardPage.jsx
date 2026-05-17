import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function DashboardPage() {
  const { user }              = useAuth();
  const [courses, setCourses] = useState([]);
  const [events, setEvents]   = useState([]);
  const [average, setAverage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        if (user.role === "student") {
          const [c, e, avg] = await Promise.all([
            api.getStudentCourses(user.subtype_id),
            api.getStudentEvents(user.subtype_id),
            api.getStudentAverage(user.subtype_id),
          ]);
          setCourses(c);
          setEvents(e.slice(0, 5));
          setAverage(avg.average_percentage);

        } else if (user.role === "lecturer") {
          const c = await api.getLecturerCourses(user.subtype_id);
          setCourses(c);

        } else if (user.role === "admin") {
          const c = await api.getCourses();
          setCourses(c.slice(0, 6));
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  if (loading) return <div className="loading">Loading dashboard...</div>;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Welcome back, {user.username}</h1>
        <span className={`role-badge role-${user.role}`}>{user.role}</span>
      </div>

      {/* Student — grade average banner */}
      {user.role === "student" && average !== null && (
        <div className="stat-banner">
          <div className="stat-item">
            <span className="stat-value">{average ?? "N/A"}%</span>
            <span className="stat-label">Overall Average</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{courses.length}</span>
            <span className="stat-label">Enrolled Courses</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{events.length}</span>
            <span className="stat-label">Upcoming Events</span>
          </div>
        </div>
      )}

      {/* Admin stat banner */}
      {user.role === "admin" && (
        <div className="stat-banner">
          <div className="stat-item">
            <span className="stat-value">{courses.length}+</span>
            <span className="stat-label">Total Courses</span>
          </div>
          <Link to="/reports" className="stat-item clickable">
            <span className="stat-value">5</span>
            <span className="stat-label">Reports Available</span>
          </Link>
        </div>
      )}

      {/* My / all courses */}
      <section>
        <div className="section-header">
          <h2>
            {user.role === "student"  && "My Courses"}
            {user.role === "lecturer" && "My Courses"}
            {user.role === "admin"    && "Recent Courses"}
          </h2>
          <Link to="/courses" className="btn btn-outline btn-sm">View All</Link>
        </div>

        {courses.length === 0 ? (
          <div className="empty-state">
            <p>No courses yet.</p>
            {user.role === "student" && (
              <Link to="/courses" className="btn btn-primary btn-sm">Browse Courses</Link>
            )}
          </div>
        ) : (
          <div className="course-grid">
            {courses.map((c) => (
              <Link to={`/courses/${c.course_id}`} key={c.course_id} className="course-card">
                <div className="course-card-code">{c.course_code}</div>
                <div className="course-card-name">{c.course_name}</div>
                {c.first_name && (
                  <div className="course-card-lecturer">
                    {c.first_name} {c.last_name}
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Upcoming events (student only) */}
      {user.role === "student" && events.length > 0 && (
        <section>
          <h2>Upcoming Events</h2>
          <div className="event-list">
            {events.map((e) => (
              <div key={e.event_id} className="event-item">
                <div className="event-date">{e.event_date}</div>
                <div className="event-info">
                  <span className="event-title">{e.event_title}</span>
                  <span className="event-course">{e.course_code} — {e.course_name}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
