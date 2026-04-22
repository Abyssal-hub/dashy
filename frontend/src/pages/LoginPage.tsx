import { LoginForm } from "@/components/auth/LoginForm";

export function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent-purple/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-pink/5 rounded-full blur-3xl" />

      <LoginForm />
    </div>
  );
}
