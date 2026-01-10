/**
 * Tests for LoginForm component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "../LoginForm";
import { AuthProvider } from "../../../contexts/AuthContext";
import { BrowserRouter } from "react-router-dom";

// Mock Firebase
vi.mock("../../../config/firebase", () => ({
  loginWithEmail: vi.fn(),
  getIdToken: vi.fn().mockResolvedValue("mock-token"),
  subscribeToAuthChanges: vi.fn((callback) => {
    callback(null);
    return () => {};
  }),
}));

// Mock auth service
vi.mock("../../../services/authService", () => ({
  syncUserWithBackend: vi.fn().mockResolvedValue({
    id: "test-id",
    email: "test@example.com",
    role: "sourcer",
  }),
}));

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>{ui}</AuthProvider>
    </BrowserRouter>
  );
};

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders email and password fields", () => {
    renderWithProviders(<LoginForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("renders sign in button", () => {
    renderWithProviders(<LoginForm />);

    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("shows error when email is empty", async () => {
    renderWithProviders(<LoginForm />);

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    await userEvent.click(submitButton);

    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
  });

  it("shows error when password is empty", async () => {
    renderWithProviders(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    await userEvent.type(emailInput, "test@example.com");

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    await userEvent.click(submitButton);

    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it("toggles password visibility", async () => {
    renderWithProviders(<LoginForm />);

    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toHaveAttribute("type", "password");

    // Find and click the visibility toggle button
    const toggleButton = screen.getByRole("button", { name: "" });
    await userEvent.click(toggleButton);

    expect(passwordInput).toHaveAttribute("type", "text");
  });

  it("renders forgot password link when callback provided", () => {
    const onForgotPassword = vi.fn();
    renderWithProviders(<LoginForm onForgotPassword={onForgotPassword} />);

    expect(screen.getByText(/forgot password/i)).toBeInTheDocument();
  });

  it("calls onForgotPassword when forgot password is clicked", async () => {
    const onForgotPassword = vi.fn();
    renderWithProviders(<LoginForm onForgotPassword={onForgotPassword} />);

    const forgotLink = screen.getByText(/forgot password/i);
    await userEvent.click(forgotLink);

    expect(onForgotPassword).toHaveBeenCalled();
  });

  it("renders switch to register link when callback provided", () => {
    const onSwitchToRegister = vi.fn();
    renderWithProviders(<LoginForm onSwitchToRegister={onSwitchToRegister} />);

    expect(screen.getByText(/create one/i)).toBeInTheDocument();
  });

  it("calls onSwitchToRegister when link is clicked", async () => {
    const onSwitchToRegister = vi.fn();
    renderWithProviders(<LoginForm onSwitchToRegister={onSwitchToRegister} />);

    const registerLink = screen.getByText(/create one/i);
    await userEvent.click(registerLink);

    expect(onSwitchToRegister).toHaveBeenCalled();
  });
});
