import axiosInstance from "../utils/axiosInstance";
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "react-toastify";
import Cookies from "js-cookie";

const LinkMyku = () => {
  const [mykuData, setMykuData] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleOnChange = (e) => {
    setMykuData({ ...mykuData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { username, password } = mykuData;

    if (!username || !password) {
      setError("Username and password are required.");
      toast.error("Please fill in both username and password.");
      return;
    }

    setIsLoading(true); // เริ่มการโหลด

    try {
      const accessToken = Cookies.get("access");
      if (!accessToken) {
        throw new Error("Session expired. Please log in again.");
      }

      // ส่งคำขอเชื่อมต่อ MyKU
      const res = await axiosInstance.post("/auth/myku-login/", mykuData, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (res.status === 200) {
        toast.success("MyKU connection successful!");
        navigate("/dashboard");
      }
    } catch (error) {
      console.error(
        "Error:",
        error.response ? error.response.data : error.message
      );

      if (error.response && error.response.status === 401) {
        toast.error("Session expired. Please log in again.");
        Cookies.remove("access");
        Cookies.remove("refresh");
        navigate("/login");
      } else {
        setError("Failed to connect MyKU. Please try again.");
        toast.error("MyKU connection failed.");
      }
    } finally {
      setIsLoading(false); // หยุดการโหลด
    }
  };

  return (
    <div className="form-container">
      <div style={{ width: "30%" }} className="wrapper">
        <form onSubmit={handleSubmit}>
          <h4>Link MyKU Account</h4>
          {isLoading && <p>Loading...</p>}

          <div className="form-group">
            <input
              type="text"
              name="username"
              value={mykuData.username}
              onChange={handleOnChange}
              placeholder="MyKU Username"
              required
            />
          </div>

          <div className="form-group">
            <input
              type="password"
              name="password"
              value={mykuData.password}
              onChange={handleOnChange}
              placeholder="MyKU Password"
              required
            />
          </div>

          {error && <p className="error-text">{error}</p>}

          <input type="submit" value="Link Account" className="submitButton" />

          <p className="pass-link">
            Sign in with email account <Link to="/login">Login here</Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default LinkMyku;
