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
      <header className="sticky top-0 z-10 bg-brand shadow-sm">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-6">
          <Link to="/" className="flex items-center gap-3">
            <img src={logo} alt="OnlyToes" className="h-8 w-8" />
            {}
            {}
          </Link>

          <nav className="ml-auto flex items-center gap-5">
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