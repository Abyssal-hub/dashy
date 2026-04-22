import { useAuthStore } from "@/stores/authStore";
import { login as loginApi } from "@/lib/api";
import type { User } from "@/types";

export function useAuth() {
  const { token, user, isAuthenticated, login: storeLogin, logout } = useAuthStore();

  const login = async (email: string, password: string) => {
    const data = await loginApi(email, password);
    const userObj: User = { id: "", email }; // We don't get user details from login; fetch separately if needed
    storeLogin(data.access_token, userObj);
    localStorage.setItem("refresh_token", data.refresh_token);
    return data;
  };

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
  };
}
