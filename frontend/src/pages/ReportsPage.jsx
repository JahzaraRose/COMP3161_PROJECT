import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { Navigate } from "react-router-dom";

const REPORTS = [
  { key: "courses50",    label: "Courses with 50+ Students",      fn: () => api.reportCourses50Plus()  },
  { key: "students5",    label: "Students in 5+ Courses",          fn: () => api.reportStudents5Plus()  },
  { key: "lecturers3",   label: "Lecturers Teaching 3+ Courses",   fn: () => api.reportLecturers3Plus() },
  { key: "top10courses", label: "Top 10 Most Enrolled Courses",    fn: () => api.reportTop10Courses()   },
  { key: "top10students",label: "Top 10 Students by Average",      fn: () => api.reportTop10Students()  },
];

export default function ReportsPage() {
  const { user }            = useAuth();
  const [active, setActive] = useState(null);
  const [data,   setData]   = useState([]);
  const [loading,setLoading]= useState(false);
  const [error,  setError]  = useState("");

  if (user.role !== "admin") return <Navigate to="/dashboard" replace />;

  const runReport = async (report) => {
    setActive(report.key);
    setLoading(true);
    setError("");
    try {
      const result = await report.fn();
      setData(result);
    } catch (err) {
      setError(err.message);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  const activeReport = REPORTS.find((r) => r.key === active);

  const renderTable = () => {
    if (data.length === 0) return <div className="empty-state">No data returned.</div>;
    const cols = Object.keys(data[0]);
    return (
      <table className="data-table">
        <thead>
          <tr>{cols.map((c) => <th key={c}>{c.replace(/_/g, " ")}</th>)}</tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              {cols.map((c) => <td key={c}>{row[c] ?? "—"}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Reports</h1>
        <span className="muted">Admin only · Results cached for 5 min</span>
      </div>

      <div className="report-grid">
        {REPORTS.map((r) => (
          <button key={r.key}
            className={`report-card ${active === r.key ? "active" : ""}`}
            onClick={() => runReport(r)}>
            {r.label}
          </button>
        ))}
      </div>

      {active && (
        <div className="report-result">
          <h2>{activeReport?.label}</h2>
          {loading && <div className="loading">Running report...</div>}
          {error   && <div className="alert alert-error">{error}</div>}
          {!loading && !error && renderTable()}
        </div>
      )}
    </div>
  );
}
