import axios from "axios";
import { jwtDecode } from "jwt-decode"; // นำเข้า jwtDecode แบบ named import
import dayjs from "dayjs";
import Cookies from "js-cookie";

const baseUrl = "http://localhost:8000/api/v1";
const axiosInstance = axios.create({
  baseURL: baseUrl,
  "Content-type": "application/json",
});

axiosInstance.interceptors.request.use(async (req) => {
  let token = Cookies.get("access");
  let refresh_token = Cookies.get("refresh");

  if (token) {
    req.headers.Authorization = `Bearer ${token}`;
    const user = jwtDecode(token); // ใช้ jwtDecode ที่นำเข้าแบบ named import
    const isExpired = dayjs.unix(user.exp).diff(dayjs()) < 1;

    if (isExpired) {
      try {
        // ใช้ refresh token เพื่อดึง access token ใหม่
        const res = await axios.post(`${baseUrl}/auth/token/refresh/`, {
          refresh: refresh_token,
        });

        if (res.status === 200) {
          // เก็บ access token ใหม่ใน cookies และอัพเดท header
          Cookies.set("access", res.data.access);
          token = res.data.access; // อัพเดท token ใหม่
          req.headers.Authorization = `Bearer ${token}`;
        } else {
          // ถ้า refresh token ไม่ถูกต้องให้ทำการ logout
          const logoutRes = await axios.post(`${baseUrl}/auth/logout/`, {
            refresh_token: refresh_token,
          });
          if (logoutRes.status === 200) {
            Cookies.remove("access");
            Cookies.remove("refresh");
            Cookies.remove("user");
          }
        }
      } catch (error) {
        console.error("Error refreshing token", error);
      }
    }
  }

  return req;
});

export default axiosInstance;
