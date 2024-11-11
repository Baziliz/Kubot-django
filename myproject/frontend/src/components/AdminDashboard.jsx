import React, { useState } from "react";
import axiosInstance from "../utils/axiosInstance";
import { toast } from "react-toastify";

const AdminDashboard = () => {
  const [formData, setFormData] = useState({
    email: "",
    first_name: "",
    last_name: "",
    password: "",
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axiosInstance.post(
        "/auth/admin/create-teacher/",
        formData
      );
      if (res.status === 201) {
        toast.success("Teacher account created successfully!");
        setFormData({ email: "", first_name: "", last_name: "", password: "" });
      }
    } catch (error) {
      toast.error("Failed to create teacher account.");
      console.error(error);
    }
  };

  return (
    <div className="form-container">
      <div style={{ width: "30%" }} name="wrapper">
      <form onSubmit={handleSubmit}>
      <h4>Create Teacher Account</h4>
      <div className="form-group">
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={formData.email}
          onChange={handleChange}
          required
        />
      </div>
      <div className="form-group">
        <input
          type="text"
          name="first_name"
          placeholder="First Name"
          value={formData.first_name}
          onChange={handleChange}
          required
        />
        </div>
        <div className="form-group">
        <input
          type="text"
          name="last_name"
          placeholder="Last Name"
          value={formData.last_name}
          onChange={handleChange}
          required
        />
        </div>
        <div className="form-group">
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          required
        />
        </div>
        <button type="submit" className="vbtn">Create Teacher</button>
      </form>
      </div>
    </div>
  );
};

export default AdminDashboard;
