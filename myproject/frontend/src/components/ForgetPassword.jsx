import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../utils/axiosInstance";
import { toast } from "react-toastify";
import Cookies from "js-cookie";

const ForgetPassword = () => {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    // Function to check for an existing cookie indicating user authentication status
    const checkCookie = () => {
      const userCookie = Cookies.get("user");
      const accessToken = Cookies.get("access");
      if (userCookie && accessToken) {
        // If cookies are present, automatically redirect the user
        const user = JSON.parse(userCookie);
        toast.info(`Welcome back, ${user.names}`);
        // Redirect based on role
        if (user.role === "admin") {
          navigate("/admin/create-teacher");
        } else {
          navigate("/profile");
        }
      }
    };
    checkCookie();
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (email) {
      const res = await axiosInstance.post("/auth/password-reset/", {
        email: email,
      });
      if (res.status === 200) {
        toast.success(
          "A link to reset your password has been sent to your email"
        );
        setMessage("Please check your email for the password reset link.");
      }
      console.log(res);
      setEmail("");
    }
  };

  return (
    <div>
      <div className="form-container">
        {message ? (
          <div>{message}</div>
        ) : (
          <form onSubmit={handleSubmit}>
            <h4>Reset Password</h4>
            <div className="form-group">
              <input
                placeholder="Enter your email address"
                type="text"
                className="email-form"
                name="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <button className="vbtn">Reset Password</button>
          </form>
        )}
      </div>
    </div>
  );
};

export default ForgetPassword;
