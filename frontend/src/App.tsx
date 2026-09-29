/**
 * App
 *
 * Defines the main routing structure of the Family Context frontend.
 *
 * Responsibilities:
 * - Configure client-side routes for the application.
 * - Provide the shared AppShell around all main pages.
 * - Keep navigation and page layout separate from individual pages.
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import HomePage from "./pages/HomePage";
import ChatPage from "./pages/ChatPage";
import TimelinePage from "./pages/TimelinePage";
import ExpensesPage from "./pages/ExpensesPage";
import DocumentsPage from "./pages/DocumentsPage";
import DemoPage from "./pages/DemoPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/expenses" element={<ExpensesPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/demo" element={<DemoPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}