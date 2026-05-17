import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api";

export default function RegisterPage() {
  const [form, setForm] = useState({
    username: "", password: "", first_name: "", last_name: "",
    email: "", role: "student", major: "", year_level: "", department: "",
  });
  const [error, setError]     = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate              = useNavigate();

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = {
        username:   form.username,
        password:   form.password,
        first_name: form.first_name,
        last_name:  form.last_name,
        email:      form.email,
        role:       form.role,
      };
      if (form.role === "student") {
        payload.major      = form.major;
        payload.year_level = parseInt(form.year_level) || undefined;
      } else if (form.role === "lecturer") {
        payload.department = form.department;
      }
      await api.register(payload);
      setSuccess("Account created! Redirecting to login...");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-wide">
        <div className="auth-header">
          <div className="auth-logo">U</div>
          <h1>UniLearn</h1>
          <p>Course Management System</p>
        </div>

        <form onSubmit={handleSubmit}>
          <h2>Create Account</h2>
          {error   && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <div className="form-row">
            <div className="form-group">
              <label>First Name</label>
              <input value={form.first_name} onChange={(e) => set("first_name", e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Last Name</label>
              <input value={form.last_name} onChange={(e) => set("last_name", e.target.value)} required />
            </div>
          </div>

          <div className="form-group">
            <label>Username</label>
            <input value={form.username} onChange={(e) => set("username", e.target.value)} required />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required />
          </div>

          <div className="form-group">
            <label>Role</label>
            <select value={form.role} onChange={(e) => set("role", e.target.value)}>
              <option value="student">Student</option>
              <option value="lecturer">Lecturer</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          {form.role === "student" && (
            <div className="form-row">
              <div className="form-group">
                <label>Major</label>
                <input value={form.major} onChange={(e) => set("major", e.target.value)} />
              </div>
              <div className="form-group">
                <label>Year Level (1–6)</label>
                <input type="number" min="1" max="6" value={form.year_level}
                  onChange={(e) => set("year_level", e.target.value)} />
              </div>
            </div>
          )}

          {form.role === "lecturer" && (
            <div className="form-group">
              <label>Department</label>
              <input value={form.department} onChange={(e) => set("department", e.target.value)} />
            </div>
          )}

          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? "Creating account..." : "Register"}
          </button>

          <p className="auth-link">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
