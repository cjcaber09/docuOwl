import { createBrowserRouter, Navigate } from "react-router"
import { AppLayout } from "@/layouts/AppLayout"
import { AuthLayout } from "@/layouts/AuthLayout"
import { RootLayout } from "@/layouts/RootLayout"
import { ChatPage } from "@/pages/ChatPage"
import { DocumentsPage } from "@/pages/DocumentsPage"
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage"
import { LoginPage } from "@/pages/LoginPage"
import { NotFoundPage } from "@/pages/NotFoundPage"
import { ResetPasswordPage } from "@/pages/ResetPasswordPage"
import { SignupPage } from "@/pages/SignupPage"

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: "/login", element: <LoginPage /> },
          { path: "/signup", element: <SignupPage /> },
          { path: "/forgot-password", element: <ForgotPasswordPage /> },
          { path: "/reset-password", element: <ResetPasswordPage /> },
        ],
      },
      {
        element: <AppLayout />,
        children: [
          { path: "/", element: <Navigate to="/chat" replace /> },
          { path: "/chat", element: <ChatPage /> },
          { path: "/chat/:conversationId", element: <ChatPage /> },
          { path: "/documents", element: <DocumentsPage /> },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
])
