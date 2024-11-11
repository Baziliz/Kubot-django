import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../utils/axiosInstance";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css"; // Import toastify CSS

const TeacherDashboard = () => {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [announcements, setAnnouncements] = useState([]);
  const [newAnnouncement, setNewAnnouncement] = useState({
    event_type: "",
    title: "",
    description: "",
    start_date: "",
    end_date: "",
    start_time: "",
    end_time: "",
  });
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const editFormRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCourses();
    fetchAnnouncements();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await axiosInstance.get("/auth/teacher/courses/");
      setCourses(response.data);
    } catch (error) {
      console.error("Error fetching courses:", error);
    }
  };

  const fetchAnnouncements = async () => {
    try {
      const response = await axiosInstance.get("/auth/event/list/");
      const fetchedAnnouncements = response.data;

      // Map announcements to include course names
      const updatedAnnouncements = fetchedAnnouncements.map((announcement) => {
        const course = courses.find((c) => c.id === announcement.course);
        return {
          ...announcement,
          course_name: course ? course.subject_name : "N/A",
        };
      });

      setAnnouncements(updatedAnnouncements);
    } catch (error) {
      console.error("Error fetching announcements:", error);
    }
  };

  const handleCourseSelect = (e) => {
    const courseId = e.target.value;
    setSelectedCourse(courseId);
  };

  const handleAnnouncementSubmit = async (e) => {
    e.preventDefault();

    // Validate type and selected course
    if (!selectedCourse) {
      toast.error(
        "Please select a course before creating or updating an announcement."
      );
      return;
    }
    if (!newAnnouncement.event_type) {
      toast.error("Please select an event type.");
      return;
    }

    // Validate start and end dates/times (allowing current date and future dates)
    const now = new Date();
    const startDateTime = new Date(
      `${newAnnouncement.start_date}T${newAnnouncement.start_time}`
    );
    const endDateTime = new Date(
      `${newAnnouncement.end_date}T${newAnnouncement.end_time}`
    );

    if (startDateTime < now.setSeconds(now.getSeconds() - 1)) {
      toast.error("Start date and time must be today or in the future.");
      return;
    }

    if (endDateTime <= startDateTime) {
      toast.error("End date/time must be after the start date/time.");
      return;
    }

    try {
      if (isEditing) {
        await axiosInstance.put(`/auth/event/update/${editingId}/`, {
          ...newAnnouncement,
          course: selectedCourse,
        });
        setIsEditing(false);
        setEditingId(null);
        toast.success("Announcement updated successfully.");
      } else {
        await axiosInstance.post("/auth/event/create/", {
          ...newAnnouncement,
          course: selectedCourse,
        });
        toast.success("Announcement created successfully.");
      }
      setNewAnnouncement({
        event_type: "",
        title: "",
        description: "",
        start_date: "",
        end_date: "",
        start_time: "",
        end_time: "",
      });
      fetchAnnouncements();
    } catch (error) {
      console.error("Error creating/updating announcement:", error);
      toast.error("Failed to create or update the announcement.");
    }
  };

  const handleEdit = (announcement) => {
    setIsEditing(true);
    setEditingId(announcement.id);
    setSelectedCourse(announcement.course);
    setNewAnnouncement({
      event_type: announcement.event_type,
      title: announcement.title,
      description: announcement.description,
      start_date: announcement.start_date,
      end_date: announcement.end_date,
      start_time: announcement.start_time,
      end_time: announcement.end_time,
    });

    // Scroll to the edit form when an announcement is selected for editing
    editFormRef.current.scrollIntoView({ behavior: "smooth" });
  };

  const handleDelete = async (id) => {
    try {
      await axiosInstance.delete(`/auth/event/delete/${id}/`);
      fetchAnnouncements();
      toast.success("Announcement deleted successfully.");
    } catch (error) {
      console.error("Error deleting announcement:", error);
      toast.error("Failed to delete the announcement.");
    }
  };

  return (
    <div>
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
      <ToastContainer /> {/* Add ToastContainer for notifications */}
      <h2>Teacher Dashboard</h2>
      <h4>Select Course for Announcement</h4>
      <select
        style={{
          fontSize: "1em",
          color: "#2c2c2c",
          textAlign: "center",
          fontFamily: "'Poppins', sans-serif",
          fontWeight: 800,
          fontStyle: "normal",
          marginLeft: "90vh",
        }}
        onChange={handleCourseSelect}
        value={selectedCourse}
      >
        <option value="">Select a course</option>
        {courses.map((course) => (
          <option key={course.id} value={course.id}>
            {course.subject_name}
          </option>
        ))}
      </select>
      <form onSubmit={handleAnnouncementSubmit}>
        <h4 ref={editFormRef}>
          {isEditing ? "Edit Announcement" : "Create Announcement"}
        </h4>
        <label>
          Type:&nbsp;&nbsp;
          <select
            value={newAnnouncement.event_type}
            onChange={(e) =>
              setNewAnnouncement({
                ...newAnnouncement,
                event_type: e.target.value,
              })
            }
          >
            <option value="">Select type</option>
            <option value="makeup_class">แจ้งการเรียน</option>
            <option value="assignment">กำหนดส่งงาน</option>
          </select>
        </label>
        <div className="form-group">
          <input
            type="text"
            placeholder="Title"
            value={newAnnouncement.title}
            onChange={(e) =>
              setNewAnnouncement({ ...newAnnouncement, title: e.target.value })
            }
            required
          />
        </div>
        <div className="form-group">
          <textarea
            placeholder="Description"
            value={newAnnouncement.description}
            onChange={(e) =>
              setNewAnnouncement({
                ...newAnnouncement,
                description: e.target.value,
              })
            }
            required
          ></textarea>
        </div>
        <input
          type="date"
          placeholder="Start Date"
          value={newAnnouncement.start_date}
          onChange={(e) =>
            setNewAnnouncement({
              ...newAnnouncement,
              start_date: e.target.value,
            })
          }
          required
        />
        <input
          type="time"
          placeholder="Start Time"
          value={newAnnouncement.start_time}
          onChange={(e) =>
            setNewAnnouncement({
              ...newAnnouncement,
              start_time: e.target.value,
            })
          }
          required
        />

        <input
          type="date"
          placeholder="End Date"
          value={newAnnouncement.end_date}
          onChange={(e) =>
            setNewAnnouncement({ ...newAnnouncement, end_date: e.target.value })
          }
          required
        />
        <div className="form-group">
          <input
            type="time"
            placeholder="End Time"
            value={newAnnouncement.end_time}
            onChange={(e) =>
              setNewAnnouncement({
                ...newAnnouncement,
                end_time: e.target.value,
              })
            }
            required
          />
        </div>
        <button type="submit" className="vbtn">
          {isEditing ? "Update Announcement" : "Create Announcement"}
        </button>
      </form>
      <br />
      <h2>Existing Announcements</h2>
      <ul>
        {announcements.map((announcement) => (
          <div
            key={announcement.id}
            style={{
              border: "1px solid #ccc",
              borderRadius: "8px",
              padding: "16px",
              marginBottom: "16px",
              backgroundColor: "#f9f9f9",
              justifyContent: "center",
              padding: "22px",
              marginTop: "10px",
              marginBottom: "1rem",
              marginRight: "auto",
              marginLeft: "auto",
              maxWidth: "600px",
              width: "80%",
              border: "2px, solid , rgba(255, 255, 255, 0.5)",
              backgroundColor: "rgba(255, 255, 255, 0.5)",
              borderRadius: "20px",
              boxShadow: "0 , 0, 30px, rgba(0, 0, 0, 0.3)",
            }}
          >
            <h4>{announcement.title}</h4>
            <p>
              <strong>Type:</strong> {announcement.event_type}
            </p>
            <p>
              <strong>Course:</strong> {announcement.course_name || "N/A"}
            </p>
            <p>
              <strong>Description:</strong> {announcement.description}
            </p>
            <p>
              <strong>Date:</strong> {announcement.start_date} -{" "}
              {announcement.end_date}
            </p>
            <p>
              <strong>Time:</strong> {announcement.start_time} -{" "}
              {announcement.end_time}
            </p>
            <button onClick={() => handleEdit(announcement)}>Edit</button>&nbsp;
            <button onClick={() => handleDelete(announcement.id)}>
              Delete
            </button>
          </div>
        ))}
      </ul>
    </div>
  );
};

export default TeacherDashboard;
