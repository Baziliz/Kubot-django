import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../utils/axiosInstance";
import { toast } from "react-toastify";
import Cookies from "js-cookie";

const Connections = () => {
  const [activeTab, setActiveTab] = useState("nontri");
  const [discordProfile, setDiscordProfile] = useState(
    JSON.parse(localStorage.getItem("discordProfile")) || null
  );
  const [isLinkingKu, setIsLinkingKu] = useState(false);
  const [mykuData, setMykuData] = useState({ username: "", password: "" });
  const [studentProfile, setStudentProfile] = useState(
    JSON.parse(localStorage.getItem("studentProfile")) || null
  );
  const [role, setRole] = useState(null); // เพิ่มสถานะ role ของผู้ใช้
  const navigate = useNavigate();

  useEffect(() => {
    // ดึงข้อมูลผู้ใช้เพื่อเช็ค role
    const fetchUserRole = async () => {
      try {
        const response = await axiosInstance.get("/auth/user-profile/");
        setRole(response.data.role); // ตั้งค่า role จากข้อมูลที่ดึงมา
      } catch (error) {
        console.error("Failed to fetch user role:", error);
      }
    };

    fetchUserRole();
  }, []);

  const handleOnChange = (e) => {
    setMykuData({ ...mykuData, [e.target.name]: e.target.value });
  };

  const handleMykuSubmit = async (e) => {
    e.preventDefault();
    try {
      const accessToken = Cookies.get("access");
      if (!accessToken)
        throw new Error("Session expired. Please log in again.");

      const res = await axiosInstance.post("/auth/myku-login/", mykuData, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (res.status === 200) {
        toast.success("MyKU connection successful!");
        fetchStudentData();
        setIsLinkingKu(false);
      }
    } catch (error) {
      toast.error("Failed to connect MyKU. Please try again.");
    }
  };

  const fetchStudentData = async () => {
    if (role === "student") {
      try {
        const res = await axiosInstance.get("/auth/myku-data/");
        if (res.status === 200) {
          setStudentProfile(res.data.student_profile);
          console.log("Student profile data:", res.data.student_profile); // ตรวจสอบข้อมูลที่ดึงมา
        }
      } catch (error) {
        toast.error("Unable to fetch student data.");
        console.error("Error fetching student data:", error);
      }
    }
  };

  const handleKuLogout = async () => {
    try {
      await axiosInstance.post("/auth/disconnect-myku-data/");
      toast.success("Nontri account disconnected successfully.");
      setStudentProfile(null);
    } catch (error) {
      toast.error("Failed to disconnect your Nontri account.");
    }
  };

  const handleDiscordConnect = () => {
    const token = Cookies.get("access");
    const discordAuthURL = `https://discord.com/api/oauth2/authorize?client_id=1292933694511775847&redirect_uri=http://localhost:8000/api/v1/auth/discord/callback/&response_type=code&scope=identify%20email&state=${token}`;
    window.location.href = discordAuthURL;
  };

  const getDiscordProfile = async () => {
    try {
      const response = await axiosInstance.get("/auth/discord/profile/");
      if (response.status === 200) {
        setDiscordProfile(response.data);
      }
    } catch {
      setDiscordProfile(null);
      localStorage.removeItem("discordProfile");
    }
  };

  const handleDiscordLogout = async () => {
    try {
      const accessToken = Cookies.get("access");
      await axiosInstance.post(
        "/auth/discord/logout/",
        {},
        {
          headers: { Authorization: `Bearer ${accessToken}` },
        }
      );
      setDiscordProfile(null);
      localStorage.removeItem("discordProfile");
      toast.success("Disconnected from Discord.");
    } catch {
      toast.error("Failed to disconnect Discord.");
    }
  };

  useEffect(() => {
    if (!discordProfile) getDiscordProfile();
    if (role === "student" && !studentProfile && !isLinkingKu)
      fetchStudentData();
  }, [role]);

  useEffect(() => {
    const fetchUserRole = async () => {
      try {
        const response = await axiosInstance.get("/auth/user-profile/");
        console.log("User data fetched:", response.data); // Debug: พิมพ์ข้อมูล user
        setRole(response.data.role);
      } catch (error) {
        console.error("Failed to fetch user role:", error);
      }
    };

    fetchUserRole();
  }, []);

  return (
    <div className="form-container">
      <header>
        <h5 className="logo"></h5>
        <nav className="navigation">
          <button
            onClick={() => navigate("/profile")}
            className="connections-btn"
          >
            Home
          </button>
        </nav>
      </header>
      <div style={{ width: "30%" }} name="wrapper">
        <div className="tabs-vertical">
          {role === "student" && (
            <button
              className={`tab-btn ${activeTab === "nontri" ? "active" : ""}`}
              onClick={() => setActiveTab("nontri")}
            >
              Nontri
            </button>
          )}
          <button
            className={`tab-btn ${activeTab === "discord" ? "active" : ""}`}
            onClick={() => setActiveTab("discord")}
          >
            Discord
          </button>
        </div>
        <br />
        <div className="tab-content mt-4">
          {activeTab === "nontri" && role === "student" ? (
            <div>
              <h4>Nontri Account</h4>
              {studentProfile ? (
                <div>
                  <p>
                    <strong>ชื่อ-นามสกุล (TH):</strong> {studentProfile.name_th}
                  </p>
                  <p>
                    <strong>ชื่อ-นามสกุล (EN):</strong> {studentProfile.name_en}
                  </p>
                  <p>
                    <strong>รหัสนิสิต:</strong> {studentProfile.std_code}
                  </p>
                  <button
                    onClick={() => navigate("/user-dashboard")}
                    className="connections-btn"
                  >
                    Go to Dashboard
                  </button>
                  <button onClick={handleKuLogout} className="logout-btn">
                    Logout
                  </button>
                </div>
              ) : isLinkingKu ? (
                <form onSubmit={handleMykuSubmit} className="mt-4">
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
                  <input
                    type="submit"
                    value="Link Account"
                    className="submitButton"
                  />
                </form>
              ) : (
                <button
                  onClick={() => setIsLinkingKu(true)}
                  className="connections-btn"
                >
                  Link Nontri Account
                </button>
              )}
            </div>
          ) : (
            <div>
              <h4>Discord Profile</h4>
              {discordProfile ? (
                <div className="profile-content">
                  <img
                    src={discordProfile.avatar_url}
                    alt="Discord Avatar"
                    className="profile-avatar"
                  />
                  <p>
                    <strong>Username:</strong> {discordProfile.discord_username}
                  </p>
                  <button onClick={handleDiscordLogout} className="logout-btn">
                    Logout
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleDiscordConnect}
                  className="connection-button"
                >
                  Connect to Discord
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Connections;
