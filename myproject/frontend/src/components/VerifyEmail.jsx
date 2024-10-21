import axios from "axios";
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

const VerifyEmail = () => {
  const [otp, setOtp] = useState("");
  const [timer, setTimer] = useState(600); // 10 นาที = 600 วินาที
  const [cooldown, setCooldown] = useState(0); // คูลดาวน์ 5 นาที = 300 วินาที
  const navigate = useNavigate();

  // ลดเวลาของ OTP ทีละวินาที
  useEffect(() => {
    let otpInterval;
    if (timer > 0) {
      otpInterval = setInterval(() => setTimer((prev) => prev - 1), 1000);
    }
    return () => clearInterval(otpInterval);
  }, [timer]);

  // ลดเวลาของคูลดาวน์ทีละวินาที
  useEffect(() => {
    let cooldownInterval;
    if (cooldown > 0) {
      cooldownInterval = setInterval(
        () => setCooldown((prev) => prev - 1),
        1000
      );
    }
    return () => clearInterval(cooldownInterval);
  }, [cooldown]);

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs < 10 ? "0" : ""}${secs}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (otp) {
      try {
        const response = await axios.post(
          "http://localhost:8000/api/v1/auth/verify-email/",
          { otp }
        );
        if (response.status === 200) {
          toast.success(response.data.message);
          navigate("/login");
        }
      } catch (err) {
        toast.error("Invalid OTP. Please try again.");
      }
    }
  };

  const handleResendOtp = async () => {
    try {
      await axios.post("http://localhost:8000/api/v1/auth/resend-otp/");
      toast.success("OTP has been resent!");
      setTimer(600); // รีเซ็ตเวลาให้ OTP หมดอายุใน 10 นาที
      setCooldown(300); // เริ่มคูลดาวน์ 5 นาที
    } catch (err) {
      toast.error("Failed to resend OTP. Please try again.");
    }
  };

  return (
    <div>
      <div className="form-container">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <h4>Please enter your One-Time Password to verify your account</h4>
            <input
              placeholder="Enter your OTP code"
              type="text"
              className="email-form"
              name="otp"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
            />
          </div>
          <input type="submit" className="vbtn" value="Validate" />
          <button
            className="resend-button"
            onClick={handleResendOtp}
            disabled={cooldown > 0}
          >
            Resend One-Time Password
          </button>
          {cooldown > 0 && <p>Resend available in: {formatTime(cooldown)}</p>}
        <p>OTP will expire in: {formatTime(timer)} minutes</p>
        </form>
      </div>
    </div>
  );
};

export default VerifyEmail;
