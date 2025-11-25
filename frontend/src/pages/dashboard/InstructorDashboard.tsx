import { Link } from "react-router-dom";
import axios from "axios";

import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { BarChart3Icon, TargetIcon } from "lucide-react";



export const InstructorDashboard = () => {
  const { user } = useAuth();

  // ================================
  // ⭐ TRIGGER QUESTION FUNCTION
  // ================================
  const handleTriggerQuestion = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL;

      // TEMP MEETING ID (replace with real meeting later)
      const meetingId = "123456789";

      const res = await axios.post(
        `${apiUrl}/api/live/trigger/${meetingId}`
      );

      console.log("Trigger Response:", res.data);
      alert("🎯 Question sent to all students!");
    } catch (error) {
      console.error("Trigger Error:", error);
      alert("❌ Failed to send question");
    }
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Instructor Dashboard
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Welcome back, {user?.firstName}! Here's an overview of your teaching activities.
          </p>
        </div>

        {/* BUTTON GROUP */}
        <div className="flex gap-3">
          {/* ⭐ Trigger Question Button */}
          <Button
            variant="secondary"
            leftIcon={<TargetIcon className="h-4 w-4" />}
            onClick={handleTriggerQuestion}
          >
            Trigger Question
          </Button>

          <Link to="/dashboard/instructor/analytics">
            <Button variant="primary" leftIcon={<BarChart3Icon className="h-4 w-4" />}>
              View Analytics
            </Button>
          </Link>
        </div>
      </div>

      {/* ================= CARDS SECTION ================= */}
      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">

        {/* Active Courses */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5 flex items-center">
            <div className="flex-shrink-0 bg-indigo-500 rounded-md p-3"></div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Active Courses
                </dt>
                <dd>
                  <div className="text-lg font-medium text-gray-900">3</div>
                </dd>
              </dl>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <a className="text-sm font-medium text-indigo-700 hover:text-indigo-900" href="#">
              View all
            </a>
          </div>
        </div>

        {/* Upcoming Sessions */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5 flex items-center">
            <div className="flex-shrink-0 bg-green-500 rounded-md p-3"></div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Upcoming Sessions
                </dt>
                <dd>
                  <div className="text-lg font-medium text-gray-900">4</div>
                </dd>
              </dl>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <a className="text-sm font-medium text-indigo-700 hover:text-indigo-900" href="#">
              View all
            </a>
          </div>
        </div>

        {/* Total Students */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5 flex items-center">
            <div className="flex-shrink-0 bg-blue-500 rounded-md p-3"></div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Students
                </dt>
                <dd>
                  <div className="text-lg font-medium text-gray-900">124</div>
                </dd>
              </dl>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <a className="text-sm font-medium text-indigo-700 hover:text-indigo-900" href="#">
              View details
            </a>
          </div>
        </div>
      </div>

      {/* ================= UPCOMING SESSION LIST ================= */}
      <div className="mt-8">
        <h2 className="text-lg font-medium text-gray-900">Upcoming Sessions</h2>
        <div className="mt-2 bg-white shadow overflow-hidden sm:rounded-md">

          <ul className="divide-y divide-gray-200">

            <li className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-indigo-600 truncate">
                  Machine Learning: Neural Networks
                </p>
                <p className="px-2 inline-flex text-xs rounded-full bg-green-100 text-green-800">
                  Today, 2:00 PM
                </p>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                Machine Learning Fundamentals • 45 students
              </p>
            </li>

            <li className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-indigo-600 truncate">
                  Database Design: Normalization
                </p>
                <p className="px-2 inline-flex text-xs rounded-full bg-yellow-100 text-yellow-800">
                  Tomorrow, 10:00 AM
                </p>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                Database Systems • 38 students
              </p>
            </li>

          </ul>

        </div>
      </div>
    </div>
  );
};
