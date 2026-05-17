import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

const TABS = ["Content", "Assignments", "Forums", "Calendar", "Members"];

export default function CourseDetailPage() {
  const { id }       = useParams();
  const { user }     = useAuth();
  const courseId     = parseInt(id);

  const [tab, setTab]         = useState("Content");
  const [loading, setLoading] = useState(true);
  const [msg, setMsg]         = useState("");

  // Data per tab
  const [content,     setContent]     = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [forums,      setForums]      = useState([]);
  const [events,      setEvents]      = useState([]);
  const [members,     setMembers]     = useState([]);

  // Create forms (lecturer)
  const [newSection,    setNewSection]    = useState({ section_title: "", section_order: 1 });
  const [newAssignment, setNewAssignment] = useState({ assignment_title: "", description: "", due_date: "" });
  const [newForum,      setNewForum]      = useState({ forum_title: "" });
  const [newEvent,      setNewEvent]      = useState({ event_title: "", event_date: "", start_time: "", end_time: "" });

  // Submissions panel (lecturer)
  const [viewSubmissions, setViewSubmissions] = useState(null);
  const [submissions,     setSubmissions]     = useState([]);
  const [gradeInput,      setGradeInput]      = useState({});

  // Submit assignment (student)
  const [submitText, setSubmitText] = useState({});

  useEffect(() => {
    const load = async () => {
      try {
        const [c, a, f, e, m] = await Promise.all([
          api.getCourseContent(courseId),
          api.getCourseAssignments(courseId),
          api.getForums(courseId),
          api.getCourseEvents(courseId),
          api.getCourseMembers(courseId),
        ]);
        setContent(c);
        setAssignments(a);
        setForums(f);
        setEvents(e);
        setMembers(m);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [courseId]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(""), 3000); };

  // --- Content tab actions ---
  const handleAddSection = async (e) => {
    e.preventDefault();
    try {
      await api.createSection(courseId, newSection);
      setContent(await api.getCourseContent(courseId));
      setNewSection({ section_title: "", section_order: 1 });
      flash("Section created.");
    } catch (err) { flash(err.message); }
  };

  const handleAddItem = async (sectionId, itemData) => {
    try {
      await api.addSectionItem(sectionId, itemData);
      setContent(await api.getCourseContent(courseId));
      flash("Item added.");
    } catch (err) { flash(err.message); }
  };

  // --- Assignment tab actions ---
  const handleCreateAssignment = async (e) => {
    e.preventDefault();
    try {
      await api.createAssignment(courseId, newAssignment);
      setAssignments(await api.getCourseAssignments(courseId));
      setNewAssignment({ assignment_title: "", description: "", due_date: "" });
      flash("Assignment created.");
    } catch (err) { flash(err.message); }
  };

  const handleSubmitAssignment = async (assignmentId) => {
    try {
      await api.submitAssignment(assignmentId, { submission_text: submitText[assignmentId] || "" });
      flash("Submitted successfully!");
    } catch (err) { flash(err.message); }
  };

  const handleViewSubmissions = async (assignmentId) => {
    setViewSubmissions(assignmentId);
    const subs = await api.getSubmissions(assignmentId);
    setSubmissions(subs);
  };

  const handleGrade = async (submissionId) => {
    try {
      await api.gradeSubmission(submissionId, { grade: parseFloat(gradeInput[submissionId]) });
      const subs = await api.getSubmissions(viewSubmissions);
      setSubmissions(subs);
      flash("Grade submitted.");
    } catch (err) { flash(err.message); }
  };

  // --- Forum tab actions ---
  const handleCreateForum = async (e) => {
    e.preventDefault();
    try {
      await api.createForum(courseId, newForum);
      setForums(await api.getForums(courseId));
      setNewForum({ forum_title: "" });
      flash("Forum created.");
    } catch (err) { flash(err.message); }
  };

  // --- Calendar tab actions ---
  const handleCreateEvent = async (e) => {
    e.preventDefault();
    try {
      await api.createEvent(courseId, newEvent);
      setEvents(await api.getCourseEvents(courseId));
      setNewEvent({ event_title: "", event_date: "", start_time: "", end_time: "" });
      flash("Event created.");
    } catch (err) { flash(err.message); }
  };

  if (loading) return <div className="loading">Loading course...</div>;

  const isLecturer = user.role === "lecturer";
  const isAdmin    = user.role === "admin";

  return (
    <div className="page">
      <div className="page-header">
        <Link to="/courses" className="back-link">← Courses</Link>
        <h1>Course #{courseId}</h1>
      </div>

      {msg && <div className="alert alert-info">{msg}</div>}

      {/* Tabs */}
      <div className="tabs">
        {TABS.map((t) => (
          <button key={t} className={`tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {/* ══════════════ CONTENT TAB ══════════════ */}
      {tab === "Content" && (
        <div className="tab-content">
          {isLecturer && (
            <div className="card mb-4">
              <h3>Add Section</h3>
              <form onSubmit={handleAddSection} className="inline-form">
                <input placeholder="Section title" value={newSection.section_title}
                  onChange={(e) => setNewSection({ ...newSection, section_title: e.target.value })} required />
                <input type="number" placeholder="Order" value={newSection.section_order} style={{ width: 80 }}
                  onChange={(e) => setNewSection({ ...newSection, section_order: e.target.value })} />
                <button type="submit" className="btn btn-primary btn-sm">Add Section</button>
              </form>
            </div>
          )}

          {content.length === 0 ? (
            <div className="empty-state">No content yet.</div>
          ) : (
            content.map((section) => (
              <div key={section.section_id} className="section-block">
                <h3 className="section-title">
                  {section.section_order}. {section.section_title}
                </h3>
                <div className="item-list">
                  {section.items.map((item) => (
                    <a key={item.item_id} href={item.item_url || "#"} target="_blank"
                      rel="noreferrer" className="item-row">
                      <span className={`item-type item-type-${item.item_type}`}>{item.item_type}</span>
                      <span>{item.item_title}</span>
                    </a>
                  ))}
                  {section.items.length === 0 && <p className="muted">No items yet.</p>}
                </div>

                {isLecturer && (
                  <AddItemForm sectionId={section.section_id} onAdd={handleAddItem} />
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* ══════════════ ASSIGNMENTS TAB ══════════════ */}
      {tab === "Assignments" && (
        <div className="tab-content">
          {isLecturer && (
            <div className="card mb-4">
              <h3>Create Assignment</h3>
              <form onSubmit={handleCreateAssignment}>
                <div className="form-group">
                  <label>Title</label>
                  <input value={newAssignment.assignment_title}
                    onChange={(e) => setNewAssignment({ ...newAssignment, assignment_title: e.target.value })}
                    required />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea value={newAssignment.description} rows={2}
                    onChange={(e) => setNewAssignment({ ...newAssignment, description: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Due Date</label>
                  <input type="date" value={newAssignment.due_date}
                    onChange={(e) => setNewAssignment({ ...newAssignment, due_date: e.target.value })} />
                </div>
                <button type="submit" className="btn btn-primary btn-sm">Create</button>
              </form>
            </div>
          )}

          {assignments.length === 0 ? (
            <div className="empty-state">No assignments yet.</div>
          ) : (
            assignments.map((a) => (
              <div key={a.assignment_id} className="card mb-2">
                <div className="assignment-header">
                  <h3>{a.assignment_title}</h3>
                  {a.due_date && <span className="due-date">Due: {a.due_date}</span>}
                </div>
                {a.description && <p className="muted">{a.description}</p>}

                {user.role === "student" && (
                  <div className="submit-area">
                    <textarea placeholder="Your submission text..."
                      value={submitText[a.assignment_id] || ""}
                      onChange={(e) => setSubmitText({ ...submitText, [a.assignment_id]: e.target.value })}
                      rows={2} />
                    <button className="btn btn-primary btn-sm"
                      onClick={() => handleSubmitAssignment(a.assignment_id)}>
                      Submit
                    </button>
                  </div>
                )}

                {isLecturer && (
                  <button className="btn btn-outline btn-sm"
                    onClick={() => handleViewSubmissions(a.assignment_id)}>
                    View Submissions
                  </button>
                )}

                {/* Submissions panel */}
                {viewSubmissions === a.assignment_id && (
                  <div className="submissions-panel">
                    <h4>Submissions ({submissions.length})</h4>
                    {submissions.length === 0 ? (
                      <p className="muted">No submissions yet.</p>
                    ) : (
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Student</th>
                            <th>Submitted</th>
                            <th>Grade / 100</th>
                            <th>Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {submissions.map((s) => (
                            <tr key={s.submission_id}>
                              <td>{s.first_name} {s.last_name}</td>
                              <td>{s.submitted_at?.slice(0, 10)}</td>
                              <td>{s.grade ?? "—"}</td>
                              <td>
                                <input type="number" min="0" max="100" style={{ width: 70 }}
                                  value={gradeInput[s.submission_id] || ""}
                                  onChange={(e) => setGradeInput({ ...gradeInput, [s.submission_id]: e.target.value })} />
                                <button className="btn btn-primary btn-sm ml-1"
                                  onClick={() => handleGrade(s.submission_id)}>Save</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* ══════════════ FORUMS TAB ══════════════ */}
      {tab === "Forums" && (
        <div className="tab-content">
          {(isLecturer || isAdmin) && (
            <div className="card mb-4">
              <h3>Create Forum</h3>
              <form onSubmit={handleCreateForum} className="inline-form">
                <input placeholder="Forum title" value={newForum.forum_title}
                  onChange={(e) => setNewForum({ forum_title: e.target.value })} required />
                <button type="submit" className="btn btn-primary btn-sm">Create</button>
              </form>
            </div>
          )}

          {forums.length === 0 ? (
            <div className="empty-state">No forums yet.</div>
          ) : (
            forums.map((f) => (
              <Link key={f.forum_id} to={`/forums/${f.forum_id}`} className="forum-row">
                <span className="forum-title">{f.forum_title}</span>
                <span className="forum-date muted">{f.created_at?.slice(0, 10)}</span>
              </Link>
            ))
          )}
        </div>
      )}

      {/* ══════════════ CALENDAR TAB ══════════════ */}
      {tab === "Calendar" && (
        <div className="tab-content">
          {(isLecturer || isAdmin) && (
            <div className="card mb-4">
              <h3>Create Event</h3>
              <form onSubmit={handleCreateEvent}>
                <div className="form-row">
                  <div className="form-group">
                    <label>Title</label>
                    <input value={newEvent.event_title}
                      onChange={(e) => setNewEvent({ ...newEvent, event_title: e.target.value })} required />
                  </div>
                  <div className="form-group">
                    <label>Date</label>
                    <input type="date" value={newEvent.event_date}
                      onChange={(e) => setNewEvent({ ...newEvent, event_date: e.target.value })} required />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Start Time</label>
                    <input type="time" value={newEvent.start_time}
                      onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>End Time</label>
                    <input type="time" value={newEvent.end_time}
                      onChange={(e) => setNewEvent({ ...newEvent, end_time: e.target.value })} />
                  </div>
                </div>
                <button type="submit" className="btn btn-primary btn-sm">Add Event</button>
              </form>
            </div>
          )}

          {events.length === 0 ? (
            <div className="empty-state">No events scheduled.</div>
          ) : (
            <div className="event-list">
              {events.map((e) => (
                <div key={e.event_id} className="event-item">
                  <div className="event-date">{e.event_date}</div>
                  <div className="event-info">
                    <span className="event-title">{e.event_title}</span>
                    {e.start_time && (
                      <span className="muted">{e.start_time} — {e.end_time}</span>
                    )}
                    {e.event_description && <p className="muted">{e.event_description}</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ══════════════ MEMBERS TAB ══════════════ */}
      {tab === "Members" && (
        <div className="tab-content">
          <p className="muted mb-2">{members.length} member(s)</p>
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {members.map((m, i) => (
                <tr key={i}>
                  <td>{m.first_name} {m.last_name}</td>
                  <td>{m.email}</td>
                  <td>
                    <span className={`role-badge role-${m.member_role}`}>{m.member_role}</span>
                  </td>
                  <td className="muted">
                    {m.member_role === "student" && m.major && `${m.major}, Year ${m.year_level}`}
                    {m.member_role === "lecturer" && m.department}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// Sub-component: add item to a section
function AddItemForm({ sectionId, onAdd }) {
  const [form, setForm]     = useState({ item_title: "", item_type: "link", item_url: "" });
  const [open, setOpen]     = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await onAdd(sectionId, form);
    setForm({ item_title: "", item_type: "link", item_url: "" });
    setOpen(false);
  };

  if (!open) {
    return (
      <button className="btn btn-outline btn-xs mt-1" onClick={() => setOpen(true)}>
        + Add Item
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="add-item-form">
      <input placeholder="Title" value={form.item_title}
        onChange={(e) => setForm({ ...form, item_title: e.target.value })} required />
      <select value={form.item_type} onChange={(e) => setForm({ ...form, item_type: e.target.value })}>
        <option value="link">Link</option>
        <option value="file">File</option>
        <option value="slide">Slide</option>
      </select>
      <input placeholder="URL" value={form.item_url}
        onChange={(e) => setForm({ ...form, item_url: e.target.value })} />
      <button type="submit" className="btn btn-primary btn-xs">Add</button>
      <button type="button" className="btn btn-outline btn-xs" onClick={() => setOpen(false)}>Cancel</button>
    </form>
  );
}
