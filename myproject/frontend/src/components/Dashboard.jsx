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
  const [isLoading, setIsLoading] = useState(true);

  const navigate = useNavigate();
  const accessToken = Cookies.get("access");

  useEffect(() => {
    if (!accessToken) {
      toast.error("You are not logged in. Please log in first.");
      navigate("/login");
      return;
    }

    fetchAllData(); // โหลดข้อมูลทั้งหมดเมื่อ Component Mount
  }, []);

  const fetchAllData = async () => {
    try {
      setIsLoading(true);
      const res = await axiosInstance.get("/auth/myku-data/");

      if (res.status === 200) {
        const data = res.data;

        // ตั้งค่าข้อมูลนักศึกษา
        if (data.student_data?.results?.stdPersonalModel) {
          setStudentData(data.student_data.results.stdPersonalModel);
        }

        // ตั้งค่าตารางเรียน
        setSchedule(data.results?.schedule_data?.results || []);

        // ตั้งค่าประกาศ
        setAnnouncements(data.results?.announce_data?.results || []);

        // ตั้งค่าเกรด
        setGrades(data.results?.grades_data?.results || []);

        // ตั้งค่ากลุ่มวิชา
        setGroupCourse(data.results?.group_course_data?.results || []);

        // ตั้งค่าข้อมูลการศึกษา
        setStudentEducation(data.results?.student_education_data?.results);

        // ตั้งค่า GPAX
        const gpaxData = data.results?.gpax_data?.results || [];
        if (gpaxData.length > 0) setGpax(gpaxData[0]);
      } else {
        toast.error("Failed to load data.");
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Unable to retrieve data. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    Cookies.remove("access");
    Cookies.remove("refresh");
    Cookies.remove("user");
    toast.success("Logout successful.");
    navigate("/login");
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
                    <br></br>
                  </p>
                  <p>
                    <strong>ชื่อ-นามสกุล (EN):</strong> {studentData.nameEn}
                    <br></br>
                  </p>
                  <p>
                    <strong>เพศ:</strong> {studentData.genderTh}
                    <br></br>
                  </p>
                  <p>
                    <strong>เบอร์โทรศัพท์ติดต่อ:</strong> {studentData.phone}
                    <br></br>
                  </p>
                  <p>
                    <strong>Email:</strong> {studentData.email}
                    <br></br>
                  </p>
                  {studentEducation && studentEducation.education ? (
                    <>
                      <h4>Educational information</h4>
                      {studentEducation.education.map((edu, index) => (
                        <div key={index}>
                          <p>
                            <strong>ระดับการศึกษา:</strong> {edu.edulevelNameTh}
                            <br></br>
                          </p>
                          <p>
                            <strong>สถานภาพนิสิต:</strong> {edu.statusNameTh}
                            <br></br>
                          </p>
                          <p>
                            <strong>ชื่อปริญญา:</strong> {edu.degreeNameTh}
                            <br></br>
                          </p>
                          <p>
                            <strong>คณะ:</strong> {edu.facultyNameTh}
                            <br></br>
                          </p>
                          <p>
                            <strong>ภาควิชา:</strong> {edu.departmentNameTh}
                            <br></br>
                          </p>
                          <p>
                            <strong>สาขา:</strong> {edu.majorNameTh}
                            <br></br>
                          </p>
                          <p>
                            <strong>อาจารย์ที่ปรึกษา:</strong> {edu.teacherName}
                            <br></br>
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
                                  <br></br>
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
