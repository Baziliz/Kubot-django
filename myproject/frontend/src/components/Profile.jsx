import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import axiosInstance from "../utils/axiosInstance";
import { toast } from "react-toastify";
import Cookies from "js-cookie";

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null); // จัดการข้อมูลผู้ใช้ใน State
  const jwt_access = Cookies.get("access");
  const refresh = Cookies.get("refresh");
  const [discordProfile, setDiscordProfile] = useState(null);

  const connectDiscord = () => {
    const token = Cookies.get("access"); // ดึง JWT token จาก Cookies

    if (!token) {
      console.error("JWT token missing.");
      return;
    }

    const oauthURL = `https://discord.com/api/oauth2/authorize?client_id=1292933694511775847&redirect_uri=http://localhost:8000/api/v1/auth/discord/callback/&response_type=code&scope=identify%20email`;

    // ส่ง JWT Token ไปกับ redirect URL
    window.location.href = `${oauthURL}&state=${token}`;
  };

  // ฟังก์ชันดึงข้อมูลโปรไฟล์ Discord
  const getDiscordProfile = async () => {
    try {
      const response = await axiosInstance.get("/auth/discord/profile/");
      console.log(response.data); // ตรวจสอบข้อมูลใน console

      if (response.status === 200) {
        setDiscordProfile(response.data); // บันทึกข้อมูลลงใน state
      }
    } catch (error) {
      console.error("No connected Discord account found:", error);
      toast.error("No connected Discord account found");
    }
  };

  useEffect(() => {
    getDiscordProfile(); // ดึงข้อมูลเมื่อหน้าโหลด
  }, []);
  // เช็คว่ามี user และ jwt_access หรือไม่ (และป้องกันการวนลูป)
  useEffect(() => {
    const storedUser = Cookies.get("user");
    if (!jwt_access || !storedUser) {
      navigate("/login");
    } else {
      setUser(JSON.parse(storedUser)); // ตั้งค่า user เมื่อมีข้อมูลจาก cookies
    }
  }, []); // [] ทำให้ useEffect นี้ทำงานแค่ครั้งเดียวตอน mount

  // แยกการเช็ค Discord Auth Code ออกมาใน useEffect อีกตัว
  useEffect(() => {
    checkDiscordAuthCode(); // เรียกเช็คว่ามี Discord authorization code หรือไม่

    // เช็คว่ามีการเชื่อมต่อกับ Discord สำเร็จหรือไม่จาก URL
    const params = new URLSearchParams(window.location.search);
    if (params.get("discord_connected") === "true") {
      toast.success("Successfully connected to Discord!");
    }
  }, []); // [] ทำให้ฟังก์ชันนี้ทำงานแค่ครั้งเดียวเช่นกัน

  const checkDiscordAuthCode = () => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    if (code) {
      fetchDiscordData(code); // ถ้าเจอ code ให้ส่งไป backend
    }
  };

  const handleDiscordLogout = async () => {
    try {
      const response = await axiosInstance.post("/auth/discord/logout/");
      if (response.status === 200) {
        setDiscordProfile(null); // ล้างข้อมูลโปรไฟล์จาก state
        toast.success("Logged out from Discord successfully.");
      }
    } catch (error) {
      console.error("Error logging out from Discord:", error);
      toast.error("Logout from Discord failed. Please try again.");
    }
  };

  const getSomeData = async () => {
    try {
      const resp = await axiosInstance.get("/auth/profile/");
      if (resp.status === 200) {
        console.log(resp.data);
      }
    } catch (error) {
      console.error(error);
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
        navigate("/login");
        toast.success("Logout successful");
      }
    } catch (error) {
      console.error(error);
      toast.error("Logout failed. Please try again.");
    }
  };

  // ฟังก์ชันสำหรับเชื่อมต่อ Discord
  const handleDiscordConnect = () => {
    const token = Cookies.get("access"); // ดึง JWT token จาก Cookies

    if (!token) {
      toast.error("JWT token not found. Please log in.");
      return;
    }

    const discordAuthURL = `https://discord.com/api/oauth2/authorize?client_id=1292933694511775847&redirect_uri=http://localhost:8000/api/v1/auth/discord/callback/&response_type=code&scope=identify%20email`;

    // ส่ง JWT Token ไปกับ redirect URL
    window.location.href = `${discordAuthURL}&state=${token}`;
  };

  // ฟังก์ชันที่เรียก backend เพื่อเชื่อมต่อกับ Discord
  const fetchDiscordData = async (code) => {
    const accessToken = Cookies.get("access"); // รับ JWT Token

    if (!accessToken) {
      toast.error("Access token not found");
      return;
    }

    try {
      const response = await axios.post(
        "http://localhost:8000/api/v1/auth/discord/connect/",
        { code },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      if (response.status === 200) {
        toast.success("Successfully connected to Discord!");
      }
    } catch (error) {
      console.error("Error connecting to Discord:", error);
      toast.error("Discord connection failed. Please try again.");
    }
  };

  return (
    <div>
      <header>
        <h5 className="logo"></h5>
        <nav className="navigation">
          <button onClick={handleDiscordConnect} className="logindiscord-btn">
            Link with Discord
          </button>
          <a href="/link-myku">
            <button className="loginmyku-btn">Link with Nontri account</button>
          </a>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
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
            >
              {" "}
              <button className="hover">Add to discord</button>
            </a>
          </h1>
          <img src="/favicon.png" alt="" />
        </div>
      </section>
      <div className="form-container">
        <div className="wrapper profile-card">
          <h4>Your Discord Profile</h4>
          {discordProfile ? (
            <div className="profile-content">
              <img
                className="profile-avatar"
                src={discordProfile.avatar_url}
                alt="Discord Avatar"
              />
              <p>
                <strong>
                  Username: {discordProfile.discord_username || "N/A"}
                </strong>{" "}
                <br></br>
              </p>
              <div className="navigations">
                <p>
                  <button onClick={handleDiscordLogout} className="logout-btn">
                    Logout
                  </button>
                </p>
              </div>
            </div>
          ) : (
            <p>Not connected to Discord yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
