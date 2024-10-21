import axiosInstance from "../utils/axiosInstance";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import Cookies from "js-cookie";
import { Link } from "react-router-dom";

const LinkMyku = () => {
  const [mykuData, setMykuData] = useState({
    username: "",
    password: "",
  });
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleOnChange = (e) => {
    setMykuData({ ...mykuData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { username, password } = mykuData;
    if (!username || !password) {
      setError("Username and password are required information.");
      toast.error("Please fill in your complete username and password.");
    } else {
      setIsLoading(true);
      try {
        // ดึง JWT token จาก cookies หรือ localStorage
        const accessToken = Cookies.get("access");

        if (!accessToken) {
          throw new Error("User is not authenticated. Please login again.");
        }

        // ส่งคำขอไปยัง /myku-login/ พร้อม Authorization header
        const res = await axiosInstance.post("/auth/myku-login/", mykuData, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        const response = res.data;
        console.log(response);
        setIsLoading(false);

        if (res.status === 200) {
          toast.success("MyKU connection successful");
          navigate("/dashboard");
        }
      } catch (error) {
        setIsLoading(false);
        setError("MyKU connection failed");
        toast.error("MyKU connection failed. Please try again.");
        console.error(
          "Error:",
          error.response ? error.response.data : error.message
        );
      }
    }
  };

  return (
    <div>
      <div className="form-container">
        <div style={{ width: "30%" }} name="wrapper">
          <form onSubmit={handleSubmit}>
            {isLoading && <p>Loading...</p>}
            <div className="form-group">
              <h4>Link account MyKU</h4>
              <input
                type="text"
                name="username"
                value={mykuData.username}
                onChange={handleOnChange}
                placeholder="MyKU Username"
              />
            </div>
            <div className="form-group">
              <input
                type="password"
                name="password"
                value={mykuData.password}
                onChange={handleOnChange}
                placeholder="MyKU Password"
              />
            </div>
            <input type="submit" value="Login" className="submitButton" />
            <br />
            <p1 className="pass-link">
              Sign in with email account <Link to={"/Login"}>Login here</Link>
            </p1>
            <br />
          </form>
        </div>
      </div>
    </div>
  );
};

export default LinkMyku;
