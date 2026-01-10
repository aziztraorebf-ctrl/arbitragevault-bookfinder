/**
 * Authentication page with Login/Register tabs.
 * Vault Elegance design.
 */

import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Vault, Sparkles } from "lucide-react";
import { LoginForm, RegisterForm } from "../components/auth";
import { useAuth } from "../contexts/AuthContext";

type AuthTab = "login" | "register";

export default function AuthPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, isLoading } = useAuth();

  // Get initial tab from URL or default to login
  const initialTab = (searchParams.get("tab") as AuthTab) || "login";
  const [activeTab, setActiveTab] = useState<AuthTab>(initialTab);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      const returnTo = searchParams.get("returnTo") || "/";
      navigate(returnTo, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, searchParams]);

  // Handle successful auth
  const handleAuthSuccess = () => {
    const returnTo = searchParams.get("returnTo") || "/";
    navigate(returnTo, { replace: true });
  };

  // Show loading while checking auth state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-vault-bg flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-vault-accent/30 border-t-vault-accent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-vault-bg flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-2/5 bg-gradient-to-br from-vault-card to-vault-bg p-12 flex-col justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-vault-accent rounded-vault-sm flex items-center justify-center">
            <Vault className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold text-vault-text">ArbitrageVault</span>
        </div>

        {/* Tagline */}
        <div className="space-y-6">
          <h1 className="text-4xl font-bold text-vault-text leading-tight">
            Discover Profitable
            <br />
            <span className="text-vault-accent">Book Niches</span>
          </h1>
          <p className="text-lg text-vault-text-secondary max-w-md">
            Analyze Amazon book markets, find hidden opportunities, and maximize your ROI
            with data-driven insights.
          </p>
          <div className="flex items-center gap-2 text-vault-text-muted">
            <Sparkles className="w-5 h-5 text-vault-accent" />
            <span className="text-sm">Powered by Keepa analytics</span>
          </div>
        </div>

        {/* Footer */}
        <p className="text-sm text-vault-text-muted">
          &copy; {new Date().getFullYear()} ArbitrageVault. All rights reserved.
        </p>
      </div>

      {/* Right side - Auth Form */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-10 h-10 bg-vault-accent rounded-vault-sm flex items-center justify-center">
              <Vault className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-vault-text">ArbitrageVault</span>
          </div>

          {/* Card */}
          <div className="bg-vault-card rounded-vault-md shadow-vault-md border border-vault-border p-8">
            {/* Tabs */}
            <div className="flex mb-8 bg-vault-bg rounded-vault-sm p-1">
              <button
                onClick={() => setActiveTab("login")}
                className={`
                  flex-1 py-2.5 px-4 text-sm font-medium rounded-vault-sm
                  transition-all duration-200
                  ${
                    activeTab === "login"
                      ? "bg-vault-card text-vault-text shadow-vault-sm"
                      : "text-vault-text-muted hover:text-vault-text"
                  }
                `}
              >
                Sign In
              </button>
              <button
                onClick={() => setActiveTab("register")}
                className={`
                  flex-1 py-2.5 px-4 text-sm font-medium rounded-vault-sm
                  transition-all duration-200
                  ${
                    activeTab === "register"
                      ? "bg-vault-card text-vault-text shadow-vault-sm"
                      : "text-vault-text-muted hover:text-vault-text"
                  }
                `}
              >
                Create Account
              </button>
            </div>

            {/* Form */}
            {activeTab === "login" ? (
              <LoginForm
                onSuccess={handleAuthSuccess}
                onSwitchToRegister={() => setActiveTab("register")}
              />
            ) : (
              <RegisterForm
                onSuccess={handleAuthSuccess}
                onSwitchToLogin={() => setActiveTab("login")}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
