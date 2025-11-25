// src/pages/sessions/SessionCreate.tsx

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

import { SessionForm, SessionFormData } from "../../components/sessions/SessionForm";
import { Card } from "../../components/ui/Card";
import { ArrowLeftIcon } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { toast } from "sonner";

export const SessionCreate = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  // ✅ use the SAME variable you already use everywhere else
  const API_BASE = import.meta.env.VITE_API_URL;   // e.g. https://learningapp-production.up.railway.app

  const isInstructor = user?.role === "instructor" || user?.role === "admin";

  if (!isInstructor) {
    return (
      <div className="py-6">
        <Card className="p-6">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600 mb-4">Only instructors can create sessions.</p>
            <Button variant="primary" onClick={() => navigate("/dashboard/sessions")}>
              Go to Sessions
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const handleSubmit = async (data: SessionFormData) => {
    setIsLoading(true);
  
    try {
      const payload = {
        title: data.title,
        course: data.course,
        courseCode: data.courseCode,
        date: data.date,                    // "2025-11-25"
        time: data.startTime,               // use startTime ONLY (backend expects 1 time)
        durationMinutes: Number(data.duration),
        timezone: "Asia/Colombo"
      };
  
      console.log("📤 Sending session create payload:", payload);
  
      const res = await fetch(`${API_BASE}/api/sessions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`
        },
        body: JSON.stringify(payload)
      });
  
      const result = await res.json();
  
      if (!res.ok) {
        console.error("❌ Backend error:", result);
        toast.error(result.detail || "Failed to create session");
        return;
      }
  
      console.log("✅ Backend created session:", result);
      toast.success("Session created successfully!");
      navigate("/dashboard/sessions");
  
    } catch (err) {
      console.error("❌ Error creating session:", err);
      toast.error("Failed to create session");
    } finally {
      setIsLoading(false);
    }
  };
  

  return (
    <div className="py-6">
      <div className="mb-6">
        <Button
          variant="outline"
          leftIcon={<ArrowLeftIcon className="h-4 w-4" />}
          onClick={() => navigate("/dashboard/sessions")}
          className="mb-4"
        >
          Back to Sessions
        </Button>

        <h1 className="text-2xl font-semibold text-gray-900">Create New Session</h1>
        <p className="mt-1 text-sm text-gray-500">
          Fill in the details below to create a new learning session
        </p>
      </div>

      <SessionForm
        onSubmit={handleSubmit}
        onCancel={() => navigate("/dashboard/sessions")}
        isLoading={isLoading}
      />
    </div>
  );
};
