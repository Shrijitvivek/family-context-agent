import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ChatPage from "./pages/ChatPage";
import TimelinePage from "./pages/TimelinePage";
import ExpensesPage from "./pages/ExpensesPage";
import DocumentsPage from "./pages/DocumentsPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <BrowserRouter>
      <nav style={{ display: "flex", gap: "1rem", padding: "1rem" }}>
        <Link to="/">Home</Link>
        <Link to="/chat">Chat</Link>
        <Link to="/timeline">Timeline</Link>
        <Link to="/expenses">Expenses</Link>
        <Link to="/documents">Documents</Link>
      </nav>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/timeline" element={<TimelinePage />} />
        <Route path="/expenses" element={<ExpensesPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}