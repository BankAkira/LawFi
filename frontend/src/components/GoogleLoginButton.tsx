"use client";

import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function GoogleLoginButton() {
  const { googleLogin } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");

  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  if (!clientId) return null; // Don't render if not configured

  return (
    <div>
      {error && (
        <p className="text-red-500 text-sm mb-2 text-center">{error}</p>
      )}
      <GoogleLogin
        onSuccess={async (response) => {
          if (!response.credential) {
            setError("ไม่ได้รับข้อมูลจาก Google");
            return;
          }
          try {
            await googleLogin(response.credential);
            router.push("/");
          } catch (err) {
            setError(
              err instanceof Error
                ? err.message
                : "ไม่สามารถเข้าสู่ระบบด้วย Google ได้"
            );
          }
        }}
        onError={() => setError("เกิดข้อผิดพลาดจาก Google")}
        text="signin_with"
        width="100%"
      />
    </div>
  );
}
