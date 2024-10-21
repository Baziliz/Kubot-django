import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../utils/axiosInstance";
import Cookies from "js-cookie";
import { toast } from "react-toastify";

const Dashboard = () => {
  const [studentData, setStudentData] = useState(null);
  const [schedule, setSchedule] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [grades, setGrades] = useState([]);
  const [groupCourse, setGroupCourse] = useState([]);
  const [studentEducation, setStudentEducation] = useState(null);
  const [gpax, setGpax] = useState(null);

  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const accessToken = Cookies.get("access");

  useEffect(() => {
    if (!accessToken) {
      toast.error("You are not logged in yet. Please log in first.");
      navigate("/login");
    } else {
      fetchStudentData();
    }
  }, []);

  const fetchStudentData = async () => {
    setIsLoading(true);
    try {
      const res = await axiosInstance.get("/auth/myku-data/", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      console.log("Response from /auth/myku-data/:", res);

      if (res.status === 200) {
        const data = res.data;
        console.log("Data received:", data);

        if (data && data.results) {
          const results = data.results;

          if (data.student_data && data.student_data.results) {
            setStudentData(data.student_data.results.stdPersonalModel);
            console.log(
              "Student Data set:",
              data.student_data.results.stdPersonalModel
            );
          }

          if (results.schedule_data && results.schedule_data.results) {
            setSchedule(results.schedule_data.results);
            console.log("Schedule Data set:", results.schedule_data.results);
          }

          if (results.announce_data && results.announce_data.results) {
            setAnnouncements(results.announce_data.results);
            console.log(
              "Announcements Data set:",
              results.announce_data.results
            );
          }

          if (results.grades_data && results.grades_data.results) {
            setGrades(results.grades_data.results);
            console.log("Grades Data set:", results.grades_data.results);
          }

          if (results.group_course_data && results.group_course_data.results) {
            setGroupCourse(results.group_course_data.results);
            console.log(
              "Group Course Data set:",
              results.group_course_data.results
            );
          }

          if (
            results.student_education_data &&
            results.student_education_data.results
          ) {
            setStudentEducation(results.student_education_data.results);
            console.log(
              "Student Education Data set:",
              results.student_education_data.results
            );
          }

          if (results.gpax_data && results.gpax_data.results.length > 0) {
            setGpax(results.gpax_data.results[0]);
            console.log("GPAX Data set:", results.gpax_data.results[0]);
          }
        } else {
          toast.error("Unable to retrieve student data.");
          console.log("Results not found in data.");
        }
      } else {
        toast.error("An error occurred while retrieving user data.");
        console.log("Failed to fetch data from server. Status:", res.status);
      }
    } catch (error) {
      console.error("Error fetching student data:", error);
      toast.error("Unable to retrieve user information. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // ฟังก์ชัน handleLogout
  const handleLogout = () => {
    // ลบ Token
    Cookies.remove("access");
    // นำผู้ใช้ไปยังหน้า Login
    navigate("/login");
    // แสดงข้อความแจ้งเตือน
    toast.success("Logout successful");
  };

  return (
    <div className="dashboard-container">
      <header className="d-flex justify-content-between align-items-center mb-4">
        <h4>Student Information</h4>
        <button onClick={handleLogout} className="btn btn-danger logout-btn">
          Logout
        </button>
      </header>

      {isLoading ? (
        <div className="text-center">
          <p>Loading...</p>
        </div>
      ) : (
        <div className="row gx-5 gy-4">
          {studentData && (
            <div className="col-lg-6 col-md-8 mx-auto">
              <div className="profile-cards shadow-sm text-center p-4">
                <h4 className="card-title mb-4">Personal Information</h4>
                <div className="personal-info">
                  <p>
                    <strong>ชื่อ-นามสกุล (TH):</strong> {studentData.nameTh}
                  </p>
                  <p>
                    <strong>ชื่อ-นามสกุล (EN):</strong> {studentData.nameEn}
                  </p>
                  <p>
                    <strong>เพศ:</strong> {studentData.genderTh}
                  </p>
                  <p>
                    <strong>เบอร์โทรศัพท์ติดต่อ:</strong> {studentData.phone}
                  </p>
                  <p>
                    <strong>Email:</strong> {studentData.email}
                  </p>
                  {studentEducation && studentEducation.education ? (
                    <>
                      <h4>Educational information</h4>
                      {studentEducation.education.map((edu, index) => (
                        <div key={index}>
                          <p>
                            <strong>ระดับการศึกษา:</strong> {edu.edulevelNameTh}
                          </p>
                          <p>
                            <strong>สถานภาพนิสิต:</strong> {edu.statusNameTh}
                          </p>
                          <p>
                            <strong>ชื่อปริญญา:</strong> {edu.degreeNameTh}
                          </p>
                          <p>
                            <strong>คณะ:</strong> {edu.facultyNameTh}
                          </p>
                          <p>
                            <strong>ภาควิชา:</strong> {edu.departmentNameTh}
                          </p>
                          <p>
                            <strong>สาขา:</strong> {edu.majorNameTh}
                          </p>
                          <p>
                            <strong>อาจารย์ที่ปรึกษา:</strong> {edu.teacherName}
                          </p>
                        </div>
                      ))}
                    </>
                  ) : (
                    <p>ไม่มีข้อมูลการศึกษาที่จะแสดง</p>
                  )}
                  {gpax && (
                    <div className="col-lg-6 col-md-8 mx-auto">
                      <div className="card shadow-sm text-center p-4">
                        <h4>
                          Grade result <br />
                          หน่วยกิตสะสม: &nbsp;&nbsp;{gpax.total_credit}{" "}
                          &nbsp;&nbsp;&nbsp;&nbsp; เกรดเฉลี่ยสะสม: &nbsp;&nbsp;
                          {gpax.gpax}
                        </h4>
                      </div>
                    </div>
                  )}
                  {grades.length > 0 && (
                    <div className="col-12">
                      <div className="card shadow-sm text-center p-4">
                        {grades.map((semester, index) => (
                          <div key={index} className="mb-3">
                            <h5>
                              ปีการศึกษา: {semester.academicYear}, GPA:{" "}
                              {semester.gpa}
                            </h5>
                            <ul className="list-unstyled">
                              {semester.grade.map((course, idx) => (
                                <p key={idx}>
                                  <strong>
                                    {course.subject_name_th} (
                                    {course.subject_code}):
                                  </strong>{" "}
                                  เกรด {course.grade}
                                </p>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {schedule.length > 0 ? (
                    <>
                      <h4>Schedule</h4>
                      <ul>
                        {schedule.map((item, index) => (
                          <p key={index}>
                            <strong>ปีการศึกษา:</strong> {item.academicYr},{" "}
                            <strong>ภาคการศึกษา:</strong> {item.semester}
                          </p>
                        ))}
                      </ul>
                    </>
                  ) : (
                    <p>ไม่มีตารางเรียนที่จะแสดง</p>
                  )}
                  {groupCourse.length > 0 ? (
                    <>
                      <h4>Subject</h4>
                      {groupCourse.map((group, index) => (
                        <div key={index}>
                          <h5>Period: {group.peroid_date}</h5>
                          <ul>
                            {group.course.map((course, idx) => (
                              <p key={idx}>
                                <strong>วิชา:</strong> {course.subject_name_th}{" "}
                                - <strong>อาจารย์:</strong>{" "}
                                {course.teacher_name}
                              </p>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </>
                  ) : (
                    <p>ไม่มีข้อมูลกลุ่มวิชาที่จะแสดง</p>
                  )}
                  {/* {announcements.length > 0 ? (
            <>
              <h2>ประกาศ</h2>
              <ul>
                {announcements.map((announce, index) => (
                  <li key={index}>
                    {announce.announce_message_th || "ไม่มีหัวข้อ"} - โดย{" "}
                    {announce.teachername}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p>ไม่มีประกาศที่จะแสดง</p>
          )} */}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
