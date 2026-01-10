/**
 * Tests for RegisterForm component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RegisterForm } from "../RegisterForm";
import { AuthProvider } from "../../../contexts/AuthContext";
import { BrowserRouter } from "react-router-dom";

// Mock Firebase
vi.mock("../../../config/firebase", () => ({
  registerWithEmail: vi.fn(),
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

describe("RegisterForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders email, password, and confirm password fields", () => {
    renderWithProviders(<RegisterForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
  });

  it("renders create account button", () => {
    renderWithProviders(<RegisterForm />);

    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
  });

  it("shows password requirements", () => {
    renderWithProviders(<RegisterForm />);

    expect(screen.getByText(/at least 6 characters/i)).toBeInTheDocument();
    expect(screen.getByText(/contains a number/i)).toBeInTheDocument();
    expect(screen.getByText(/contains a letter/i)).toBeInTheDocument();
  });

  it("shows error when email is empty", async () => {
    renderWithProviders(<RegisterForm />);

    const submitButton = screen.getByRole("button", { name: /create account/i });
    await userEvent.click(submitButton);

    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
  });

  it("shows error when password is too short", async () => {
    renderWithProviders(<RegisterForm />);

    const emailInput = screen.getByLabelText(/email/i);
    await userEvent.type(emailInput, "test@example.com");

    const passwordInput = screen.getByLabelText(/^password$/i);
    await userEvent.type(passwordInput, "12345");

    const confirmInput = screen.getByLabelText(/confirm password/i);
    await userEvent.type(confirmInput, "12345");

    const submitButton = screen.getByRole("button", { name: /create account/i });
    await userEvent.click(submitButton);

    expect(screen.getByText(/at least 6 characters/i)).toBeInTheDocument();
  });

  it("shows error when passwords do not match", async () => {
    renderWithProviders(<RegisterForm />);

    const emailInput = screen.getByLabelText(/email/i);
    await userEvent.type(emailInput, "test@example.com");

    const passwordInput = screen.getByLabelText(/^password$/i);
    await userEvent.type(passwordInput, "password123");

    const confirmInput = screen.getByLabelText(/confirm password/i);
    await userEvent.type(confirmInput, "differentpassword");

    const submitButton = screen.getByRole("button", { name: /create account/i });
    await userEvent.click(submitButton);

    expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
  });

  it("updates password requirement indicators as user types", async () => {
    renderWithProviders(<RegisterForm />);

    const passwordInput = screen.getByLabelText(/^password$/i);

    // Initially, requirements should not be met (red text)
    const lengthReq = screen.getByText(/at least 6 characters/i);
    expect(lengthReq.closest("li")).toHaveClass("text-red-400");

    // Type a valid password
    await userEvent.type(passwordInput, "pass123");

    // All requirements should now be met (green text)
    await waitFor(() => {
      expect(screen.getByText(/at least 6 characters/i).closest("li")).toHaveClass("text-green-500");
      expect(screen.getByText(/contains a number/i).closest("li")).toHaveClass("text-green-500");
      expect(screen.getByText(/contains a letter/i).closest("li")).toHaveClass("text-green-500");
    });
  });

  it("renders switch to login link when callback provided", () => {
    const onSwitchToLogin = vi.fn();
    renderWithProviders(<RegisterForm onSwitchToLogin={onSwitchToLogin} />);

    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  it("calls onSwitchToLogin when link is clicked", async () => {
    const onSwitchToLogin = vi.fn();
    renderWithProviders(<RegisterForm onSwitchToLogin={onSwitchToLogin} />);

    const loginLink = screen.getByText(/sign in/i);
    await userEvent.click(loginLink);

    expect(onSwitchToLogin).toHaveBeenCalled();
  });
});
