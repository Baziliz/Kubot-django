import { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "./App.css";
import {
  Signup,
  Login,
  Profile,
  VerifyEmail,
  ForgetPassword,
  ResetPassword,
  LinkMyKU,
  Dashboard,
  ProtectedRoute,
} from "./components";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

function App() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <Router>
        <ToastContainer />
        <Routes>
          <Route path="/" element={<Profile />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/" element={<ProtectedRoute />}>
            <Route path="profile" element={<Profile />} />
            <Route path="/link-myku" element={<LinkMyKU />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Route>
          <Route path="/otp/verify" element={<VerifyEmail />} />
          <Route path="/forget_password" element={<ForgetPassword />} />
          <Route
            path="/password-reset-confirm/:uid/:token"
            element={<ResetPassword />}
          />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
