import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../utils/axiosInstance";
import { toast } from "react-toastify";
import Cookies from "js-cookie";

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const jwt_access = Cookies.get("access");
  const refresh = Cookies.get("refresh");
  const userCookie = Cookies.get("user");

  useEffect(() => {
    // Check for missing access and user cookies, and redirect to login if not found
    if (!jwt_access || !userCookie) {
      navigate("/login");
      return;
    }

    // Fetch data if access token exists
    if (jwt_access) {
      getSomeData();
    }
  }, [jwt_access, userCookie, navigate]);

  const getSomeData = async () => {
    try {
      const resp = await axiosInstance.get("/auth/profile/");
      console.log("API response data:", resp.data); // ตรวจสอบข้อมูลจาก API อย่างละเอียด

      if (resp.status === 200) {
        setUser(resp.data);
        console.log("User data set in state:", resp.data); // ตรวจสอบข้อมูลหลังการตั้งค่าใน state
      }
    } catch (error) {
      console.error("Error fetching user data:", error);
    }
  };

  const handleLogout = async () => {
    try {
      const res = await axiosInstance.post("/auth/logout/", {
        refresh_token: refresh,
      });
      if (res.status === 200) {
        Cookies.remove("access");
        Cookies.remove("refresh");
        Cookies.remove("user");
        setUser(null);
        navigate("/login");
        toast.success("Logout successful");
      }
    } catch (error) {
      console.error(error);
      toast.error("Logout failed. Please try again.");
    }
  };

  return (
    <div>
      <header>
        <h5 className="logo"></h5>
        <nav className="navigation">
          {jwt_access ? (
            <>
              <button
                onClick={() => navigate("/connections")}
                className="connections-btn"
              >
                Connections
              </button>
              {user && user.role === "teacher" ? (
                <button
                  onClick={() => navigate("/teacher-dashboard")}
                  className="dashboard-btn"
                >
                  Teacher Dashboard
                </button>
              ) : null}
              <button onClick={handleLogout} className="logout-btn">
                Logout
              </button>
            </>
          ) : (
            <button onClick={() => navigate("/login")} className="login-btn">
              Login
            </button>
          )}
        </nav>
      </header>
      <section id="hero">
        <div className="container">
          <h1>
            The only Discord app
            <br />
            you'll ever need! <br></br>
            <p>KuBot is the easiest way to organize your studies.</p>
            <a
              href="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot"
              target="_blank"
              rel="noopener noreferrer"
            >
              <button className="hover">Add to discord</button>
            </a>
          </h1>
          <img src="/favicon.png" alt="" />
        </div>
      </section>
    </div>
  );
};

export default Profile;
