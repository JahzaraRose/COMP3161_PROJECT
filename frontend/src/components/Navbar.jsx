import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isActive = (path) => pathname.startsWith(path) ? "active" : "";

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/dashboard">UniLearn</Link>
      </div>

      <div className="nav-links">
        <Link to="/dashboard" className={isActive("/dashboard")}>Dashboard</Link>
        <Link to="/courses"   className={isActive("/courses")}>Courses</Link>
        {user?.role === "admin" && (
          <Link to="/reports" className={isActive("/reports")}>Reports</Link>
        )}
      </div>

      <div className="nav-user">
        <span className={`role-badge role-${user?.role}`}>{user?.role}</span>
        <span className="nav-username">{user?.username}</span>
        <button className="btn-logout" onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  );
}
