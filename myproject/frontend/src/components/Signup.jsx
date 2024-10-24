import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "react-toastify";

const OTP_EXPIRATION_TIME = 600; // 10 นาที (600 วินาที)

const Signup = () => {
  const navigate = useNavigate();
  const [formdata, setFormData] = useState({
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    password2: "",
  });

  const handleOnChange = (e) => {
    setFormData({ ...formdata, [e.target.name]: e.target.value });
  };

  const validatePassword = (password) => {
    const passwordRegex =
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$/;
    return passwordRegex.test(password);
  };

  const resendOtp = async (email) => {
    try {
      await axios.post("http://localhost:8000/api/v1/auth/resend-otp/", {
        email,
      });
      toast.success("OTP has been sent to your email.");
    } catch (err) {
      toast.error("Failed to send OTP. Please try again.");
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { email, first_name, last_name, password, password2 } = formdata;

    if (!email || !first_name || !last_name || !password || !password2) {
      toast.error("Please fill all the fields");
      return;
    }

    if (!validatePassword(password)) {
      toast.error(
        "Password must be at least 8 characters long, and include uppercase, lowercase, number, and special character."
      );
      return;
    }

    if (password !== password2) {
      toast.error("Passwords do not match");
      return;
    }

    try {
      const res = await axios.post(
        "http://localhost:8000/api/v1/auth/register/",
        formdata
      );
      if (res.status === 201) {
        toast.success("Registration successful. OTP sent to your email.");

        const now = Math.floor(Date.now() / 1000);
        localStorage.setItem("otpExpiration", now + OTP_EXPIRATION_TIME); // บันทึก OTP ใหม่
        localStorage.setItem("userData", JSON.stringify({ email })); // เก็บอีเมลใน LocalStorage

        navigate("/otp/verify", { state: { email } }); // ส่งไปหน้า Verify
      }
    } catch (err) {
      toast.error(
        "Registration failed or Email is already registered. Please try again."
      );
      console.error(err);
    }
  };

  const { email, first_name, last_name, password, password2 } = formdata;

  return (
    <div className="form-container">
      <div style={{ width: "30%" }} className="wrapper">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <h4>Sign Up</h4>
            <input
              placeholder="Email"
              type="text"
              name="email"
              value={email}
              onChange={handleOnChange}
              className="email-form"
            />
          </div>
          <div className="form-group">
            <input
              placeholder="First Name"
              type="text"
              name="first_name"
              value={first_name}
              onChange={handleOnChange}
              className="email-form"
            />
          </div>
          <div className="form-group">
            <input
              placeholder="Last Name"
              type="text"
              name="last_name"
              value={last_name}
              onChange={handleOnChange}
              className="email-form"
            />
          </div>
          <div className="form-group">
            <input
              placeholder="Password"
              type="password"
              name="password"
              value={password}
              onChange={handleOnChange}
              className="email-form"
            />
          </div>
          <div className="form-group">
            <input
              placeholder="Confirm Password"
              type="password"
              name="password2"
              value={password2}
              onChange={handleOnChange}
              className="email-form"
            />
          </div>
          <input type="submit" value="Register" className="submitButton" />
          <p className="pass-link">
            Already have an account? <Link to="/login">Login here</Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Signup;
