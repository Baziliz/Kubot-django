import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axiosInstance from "../utils/axiosInstance";
import { toast } from "react-toastify";

const ResetPassword = () => {
  const navigate = useNavigate();
  const { uid, token } = useParams();
  const [newPasswords, setNewPasswords] = useState({
    password: "",
    confirm_password: "",
  });

  const handleChange = (e) => {
    setNewPasswords({ ...newPasswords, [e.target.name]: e.target.value });
  };

  const validatePassword = (password) => {
    const passwordRegex =
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$/;
    return passwordRegex.test(password);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { password, confirm_password } = newPasswords;

    // ตรวจสอบความซับซ้อนของรหัสผ่าน
    if (!validatePassword(password)) {
      toast.error(
        "Password must be at least 8 characters long, and include uppercase, lowercase, number, and special character."
      );
      return;
    }

    // ตรวจสอบการยืนยันรหัสผ่าน
    if (password !== confirm_password) {
      toast.error("Passwords do not match.");
      return;
    }

    const data = {
      password,
      confirm_password,
      uidb64: uid,
      token: token,
    };

    try {
      const response = await axiosInstance.patch(
        "/auth/set-new-password/",
        data
      );
      const result = response.data;

      if (response.status === 200) {
        toast.success(result.message);
        navigate("/login");
      }
    } catch (err) {
      toast.error("Failed to reset password. Please try again.");
      console.error(err);
    }
  };

  return (
    <div>
      <div className="form-container">
        <div className="wrapper" style={{ width: "100%" }}>
          <form action="" onSubmit={handleSubmit}>
            <div className="form-group">
              <h4>Set New Password</h4>
              <input
                placeholder="New Password"
                type="password"
                className="email-form"
                name="password"
                value={newPasswords.password}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <input
                placeholder="Confirm New Password"
                type="password"
                className="email-form"
                name="confirm_password"
                value={newPasswords.confirm_password}
                onChange={handleChange}
              />
            </div>
            <button type="submit" className="vbtn">
              Set New Password
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
