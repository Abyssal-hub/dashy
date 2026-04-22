import { LayoutDashboard, Settings, LogOut, BarChart3, Calendar, FileText, Bitcoin } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";

interface SidebarProps {
  activeItem?: string;
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "portfolio", label: "Portfolio", icon: BarChart3 },
  { id: "calendar", label: "Calendar", icon: Calendar },
  { id: "logs", label: "Logs", icon: FileText },
  { id: "crypto", label: "Crypto", icon: Bitcoin },
];

export function Sidebar({ activeItem = "dashboard" }: SidebarProps) {
  const logout = useAuthStore((s) => s.logout);

  return (
    <aside className="w-64 h-screen bg-dark-900 border-r border-dark-700 flex flex-col">
      {/* Brand */}
      <div className="p-6 border-b border-dark-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl brand-gradient flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold brand-text">Dashy</h1>
            <p className="text-xs text-gray-500">Monitoring Dashboard</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeItem === item.id;
          return (
            <a
              key={item.id}
              href={`#${item.id}`}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all",
                isActive
                  ? "bg-accent-violet/10 text-accent-purple border border-accent-purple/20"
                  : "text-gray-400 hover:bg-dark-700 hover:text-gray-200"
              )}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </a>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="p-4 border-t border-dark-700 space-y-1">
        <a
          href="#settings"
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-dark-700 hover:text-gray-200 transition-all"
        >
          <Settings className="w-4 h-4" />
          Settings
        </a>
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-dark-700 hover:text-status-critical transition-all"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
