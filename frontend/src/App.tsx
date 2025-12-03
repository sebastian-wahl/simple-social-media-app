import { Link, Outlet, useLocation } from "react-router-dom";
import logo from "../pic/logo.png";

export default function App() {
  const loc = useLocation();
  const isActive = (path: string) =>
    loc.pathname === path || loc.pathname.startsWith(path)
      ? "text-white font-semibold"
      : "text-white/80 hover:text-white";

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-10 bg-brand shadow-md">
        <div className="mx-auto max-w-6xl px-6 py-4 md:py-5 flex items-center gap-6">
          <Link to="/" className="flex items-center gap-3">
            {/* größeres Logo */}
            <img
              src={logo}
              alt="OnlyToes"
              className="h-10 w-10 md:h-12 md:w-12"
            />
            {/* größerer Titeltext */}
            <span className="hidden sm:inline text-xl md:text-2xl font-bold text-white">
              HappyFeet
            </span>
          </Link>

          <nav className="ml-auto flex items-center gap-6 text-sm md:text-base">
            <Link to="/" className={isActive("/")}>
              Feed
            </Link>
            <Link to="/create" className={isActive("/create")}>
              Create Post
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1 mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t">
        <div className="mx-auto max-w-6xl px-4 py-3 text-sm text-gray-500">
          © {new Date().getFullYear()} OnlyToes — demo
        </div>
      </footer>
    </div>
  );
}