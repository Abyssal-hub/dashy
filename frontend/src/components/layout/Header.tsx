import { Bell, Search, Menu } from "lucide-react";
import { useUIStore } from "@/stores/uiStore";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface HeaderProps {
  title?: string;
  onSearch?: (query: string) => void;
}

export function Header({ title = "Dashboard", onSearch }: HeaderProps) {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const user = useAuthStore((s) => s.user);

  return (
    <header className="h-16 bg-dark-900/80 backdrop-blur-md border-b border-dark-700 flex items-center px-6 sticky top-0 z-40">
      <div className="flex items-center gap-4 flex-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className={cn("lg:hidden", sidebarOpen && "hidden")}
        >
          <Menu className="w-5 h-5 text-gray-400" />
        </Button>

        <h2 className="text-lg font-semibold text-white">{title}</h2>
      </div>

      <div className="flex items-center gap-4">
        {onSearch && (
          <div className="relative hidden md:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              placeholder="Search..."
              className="w-64 pl-10 bg-dark-800 border-dark-600"
              onChange={(e) => onSearch(e.target.value)}
            />
          </div>
        )}

        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5 text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-status-critical rounded-full" />
        </Button>

        <div className="flex items-center gap-3 pl-4 border-l border-dark-700">
          <div className="w-8 h-8 rounded-full bg-accent-violet/20 flex items-center justify-center">
            <span className="text-xs font-medium text-accent-purple">
              {user?.email?.[0]?.toUpperCase() || "U"}
            </span>
          </div>
          <span className="text-sm text-gray-300 hidden sm:block">
            {user?.email || "User"}
          </span>
        </div>
      </div>
    </header>
  );
}
