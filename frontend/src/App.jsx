import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import CoursesPage from "./pages/CoursesPage";
import CourseDetailPage from "./pages/CourseDetailPage";
import ForumDetailPage from "./pages/ForumDetailPage";
import ReportsPage from "./pages/ReportsPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard"       element={<DashboardPage />} />
          <Route path="/courses"         element={<CoursesPage />} />
          <Route path="/courses/:id"     element={<CourseDetailPage />} />
          <Route path="/forums/:id"      element={<ForumDetailPage />} />
          <Route path="/reports"         element={<ReportsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  );
}
