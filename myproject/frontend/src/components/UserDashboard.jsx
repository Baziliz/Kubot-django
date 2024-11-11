import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../utils/axiosInstance";
import Cookies from "js-cookie";
import { toast } from "react-toastify";

const UserDashboard = () => {
  const [studentProfile, setStudentProfile] = useState(null);
  const [scheduleData, setScheduleData] = useState([]);
  const [groupCourseData, setGroupCourseData] = useState([]);
  const [gradesData, setGradesData] = useState([]);
  const [studentEducationData, setStudentEducationData] = useState(null);
  const [gpaxData, setGpaxData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});

  const [yearTermOptions, setYearTermOptions] = useState([]);
  const [selectedYearTerm, setSelectedYearTerm] = useState(null);

  const navigate = useNavigate();
  const accessToken = Cookies.get("access");

  useEffect(() => {
    if (!accessToken) {
      toast.error("You are not logged in. Please log in first.");
      navigate("/login");
      return;
    }
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setIsLoading(true);
      const res = await axiosInstance.get("/auth/myku-data/");
      if (res.status === 200) {
        const data = res.data;

        // กำหนดค่า studentProfile ให้มีข้อมูลล่าสุดจากฐานข้อมูล
        setStudentProfile(data.student_profile || null);

        // โหลดข้อมูลอื่นๆ
        setScheduleData(data.schedule_data || []);
        setGroupCourseData(data.group_course_data || []);
        setGradesData(data.grades_data || []);
        setStudentEducationData(data.student_education_data || null);
        setGpaxData(data.gpax_data || null);

        // สร้างตัวเลือกปีและภาคเรียนจากข้อมูลเกรด
        setYearTermOptions(
          Object.keys(data.grades_data).sort((a, b) => {
            const [yearA, termA] = a
              .match(/(\d+)\/(\d)/)
              .slice(1, 3)
              .map(Number);
            const [yearB, termB] = b
              .match(/(\d+)\/(\d)/)
              .slice(1, 3)
              .map(Number);
            if (yearA !== yearB) return yearB - yearA;
            return termB - termA;
          })
        );
      } else {
        toast.error("Failed to load data.");
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Unable to retrieve data.");
    } finally {
      setIsLoading(false);
    }
  };

  const semesterNames = { 0: "ฤดูร้อน", 1: "ภาคต้น", 2: "ภาคปลาย" };

  const handleYearTermChange = (e) => {
    setSelectedYearTerm(e.target.value);
  };

  useEffect(() => {
    if (studentProfile) {
      setEditData(studentProfile); // ตั้งค่าเริ่มต้นให้ editData จาก studentProfile
    }
  }, [studentProfile]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleSaveField = async (key) => {
    try {
      const updatedField = { [key]: editData[key] };
      const res = await axiosInstance.put(
        "/auth/update-profile/",
        updatedField,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
        }
      );

      if (res.status === 200) {
        toast.success("Updated successfully!");

        await fetchAllData();

        setIsEditing(false);
      }
    } catch (error) {
      toast.error("Failed to update field. Please try again with full e-mail.");
    }
  };

  const handleCancelEdit = (key) => {
    setIsEditing((prev) => ({ ...prev, [key]: false }));
    setEditData(studentProfile);
  };

  return (
    <div>
      <header>
        <h5 className="logo"></h5>
        <nav className="navigation">
          <button
            onClick={() => navigate("/connections")}
            className="connections-btn"
          >
            Connections
          </button>
          <button
            onClick={() => navigate("/profile")}
            className="connections-btn"
          >
            Home
          </button>
        </nav>
      </header>

      {isLoading ? (
        <div className="text-center">
          <p>Loading...</p>
        </div>
      ) : (
        <div className="row gx-5 gy-4">
          {studentProfile && (
            <div className="col-lg-6 col-md-8 mx-auto">
              <div className="profile-cards shadow-sm text-center p-4">
                <h4 className="card-title mb-4">Personal Information</h4>

                <p>
                  <strong>ชื่อ-นามสกุล (TH) :</strong> {studentProfile.name_th}
                </p>
                <p>
                  <strong>ชื่อ-นามสกุล (EN) :</strong> {studentProfile.name_en}
                </p>
                <p>
                  <strong>รหัสนิสิต :</strong> {studentProfile.std_code}
                </p>
                <p>
                  <strong>เบอร์โทร :</strong>

                  {isEditing.phone ? (
                    <>
                      <input
                        type="text"
                        name="phone"
                        value={editData.phone || ""}
                        onChange={handleInputChange}
                        className="form-control"
                        style={{
                          flex: 1,
                          marginLeft: "10px",
                          marginRight: "10px",
                        }}
                      />
                      <button
                        onClick={() => handleSaveField("phone")}
                        className="btn btn-success me-2"
                      >
                        Save
                      </button>
                      &nbsp;&nbsp;
                      <button
                        onClick={() => handleCancelEdit("phone")}
                        className="btn btn-secondary"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <span style={{ flex: 1, marginLeft: "10px" }}>
                        {studentProfile.phone || "ยังไม่เพิ่ม"}
                      </span>
                      &nbsp;&nbsp;
                      <button
                        onClick={() =>
                          setIsEditing((prev) => ({ ...prev, phone: true }))
                        }
                        className="btn btn-link"
                      >
                        Edit
                      </button>
                    </>
                  )}
                </p>
                <p>
                  <strong>KU Email :</strong>
                  {isEditing.ku_email ? (
                    <>
                      <input
                        type="email"
                        name="ku_email"
                        value={editData.ku_email || ""}
                        onChange={handleInputChange}
                        className="form-control"
                        style={{
                          flex: 1,
                          marginLeft: "10px",
                          marginRight: "10px",
                        }}
                      />
                      <button
                        onClick={() => handleSaveField("ku_email")}
                        className="btn btn-success me-2"
                      >
                        Save
                      </button>
                      &nbsp;&nbsp;
                      <button
                        onClick={() => handleCancelEdit("ku_email")}
                        className="btn btn-secondary"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <span style={{ flex: 1, marginLeft: "10px" }}>
                        {studentProfile.ku_email || "ยังไม่เพิ่ม"}
                      </span>
                      &nbsp;&nbsp;
                      <button
                        onClick={() =>
                          setIsEditing((prev) => ({
                            ...prev,
                            ku_email: true,
                          }))
                        }
                        className="btn btn-link"
                      >
                        Edit
                      </button>
                    </>
                  )}
                </p>

                {studentEducationData && (
                  <>
                    <h4>Educational Information</h4>
                    <p>
                      <strong>สถานภาพ :</strong> {studentEducationData.status}
                    </p>
                    <p>
                      <strong>ชื่อปริญญา :</strong>{" "}
                      {studentEducationData.degree_name}
                    </p>
                    <p>
                      <strong>คณะ :</strong>{" "}
                      {studentEducationData.faculty_name_th}
                    </p>
                    <p>
                      <strong>สาขา :</strong>{" "}
                      {studentEducationData.major_name_th}
                    </p>
                  </>
                )}

                {gpaxData && (
                  <div className="card shadow-sm text-center p-4">
                    <h4>
                      Grade Result <br />
                      <strong>หน่วยกิตสะสม&nbsp;: &nbsp;</strong>{" "}
                      {gpaxData.total_credit}&nbsp;&nbsp;&nbsp;&nbsp;
                      <strong>เกรดเฉลี่ยสะสม&nbsp;: &nbsp;</strong>{" "}
                      {gpaxData.gpax}
                    </h4>
                  </div>
                )}

                <div className="form-group">
                  <select
                    id="yearTermSelect"
                    value={selectedYearTerm || ""}
                    onChange={handleYearTermChange}
                    className="form-control"
                  >
                    <option value="">เลือกปีและภาคการศึกษา</option>
                    {yearTermOptions.map((yearTerm) => (
                      <option key={yearTerm} value={yearTerm}>
                        {`${
                          semesterNames[parseInt(yearTerm.split("/")[1], 10)]
                        } ${yearTerm.split("/")[0]}`}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedYearTerm && gradesData[selectedYearTerm] && (
                  <div className="semester-card mb-4 p-3 shadow-sm">
                    <div className="d-flex justify-content-between align-items-center">
                      <h5>{`${
                        semesterNames[
                          parseInt(selectedYearTerm.split("/")[1], 10)
                        ]
                      } ${selectedYearTerm.split("/")[0]}`}</h5>
                      <p>
                        <strong>
                          หน่วยกิตรวม&nbsp;:{" "}
                          {gradesData[selectedYearTerm].total_credits || "N/A"}{" "}
                          &nbsp;|&nbsp; GPA&nbsp;:{" "}
                          {gradesData[selectedYearTerm].gpa || "N/A"}
                        </strong>
                      </p>
                    </div>

                    <div className="course-list mt-3">
                      {gradesData[selectedYearTerm].courses.map(
                        (course, cIdx) => (
                          <div
                            key={cIdx}
                            className="d-flex justify-content-between align-items-center course-item mb-2 p-2"
                          >
                            <div className="d-flex flex-column">
                              <p>
                                <strong>{course.subject_code} : </strong>
                                {course.subject_name_th} <br />
                                {course.subject_name_en || "N/A"} <br />
                                <strong>หน่วยกิต :</strong> {course.credit}{" "}
                                &nbsp;
                                <strong>เกรด :</strong> {course.grade}
                              </p>
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

                {scheduleData.length > 0 && (
                  <>
                    <h4>Schedule</h4>
                    {scheduleData.map((schedule, index) => (
                      <div key={index}>
                        {/* <h5>
                          ปีการศึกษา :&nbsp;{schedule.academic_year},
                          ภาคการศึกษา :&nbsp; {schedule.semester}
                        </h5> */}

                        {/* Display all groupCourseData */}
                        {groupCourseData.map((course, idx) => (
                          <div key={idx}>
                            <p>
                              <strong>วิชา :</strong> {course.subject_name}
                            </p>
                            <p>
                              <strong>อาจารย์ :</strong> {course.teacher_name}
                            </p>
                            <p>
                              <strong>วัน :</strong> {course.day_w}
                            </p>
                            <p>
                              <strong>เวลา :</strong> {course.time_from} -{" "}
                              {course.time_to}
                            </p>
                            <p>
                              <strong>ห้อง :</strong> {course.room_name_th}
                            </p>
                            <hr />
                          </div>
                        ))}
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UserDashboard;
