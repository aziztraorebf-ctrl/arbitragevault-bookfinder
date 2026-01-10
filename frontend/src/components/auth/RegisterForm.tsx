/**
 * Registration form component with Vault Elegance styling.
 */

import { useState } from "react";
import { Mail, Lock, Eye, EyeOff, UserPlus, AlertCircle, Check } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";

interface RegisterFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

// Password strength requirements
const PASSWORD_REQUIREMENTS = [
  { label: "At least 6 characters", check: (p: string) => p.length >= 6 },
  { label: "Contains a number", check: (p: string) => /\d/.test(p) },
  { label: "Contains a letter", check: (p: string) => /[a-zA-Z]/.test(p) },
];

export function RegisterForm({ onSuccess, onSwitchToLogin }: RegisterFormProps) {
  const { register, isLoading, error, clearError } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    // Validation
    if (!email.trim()) {
      setLocalError("Email is required");
      return;
    }
    if (!password) {
      setLocalError("Password is required");
      return;
    }
    if (password.length < 6) {
      setLocalError("Password must be at least 6 characters");
      return;
    }
    if (password !== confirmPassword) {
      setLocalError("Passwords do not match");
      return;
    }

    try {
      await register(email.trim(), password);
      onSuccess?.();
    } catch {
      // Error is handled by AuthContext
    }
  };

  const displayError = localError || error;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Error Alert */}
      {displayError && (
        <div className="flex items-center gap-3 p-4 rounded-vault-sm bg-red-500/10 border border-red-500/20">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-400">{displayError}</p>
        </div>
      )}

      {/* Email Field */}
      <div className="space-y-2">
        <label htmlFor="register-email" className="block text-sm font-medium text-vault-text">
          Email
        </label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
          <input
            id="register-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            className="
              w-full pl-11 pr-4 py-3
              bg-vault-bg border border-vault-border rounded-vault-sm
              text-vault-text placeholder:text-vault-text-muted
              focus:outline-none focus:ring-2 focus:ring-vault-accent/50 focus:border-vault-accent
              transition-all duration-200
            "
          />
        </div>
      </div>

      {/* Password Field */}
      <div className="space-y-2">
        <label htmlFor="register-password" className="block text-sm font-medium text-vault-text">
          Password
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
          <input
            id="register-password"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Create a password"
            autoComplete="new-password"
            className="
              w-full pl-11 pr-12 py-3
              bg-vault-bg border border-vault-border rounded-vault-sm
              text-vault-text placeholder:text-vault-text-muted
              focus:outline-none focus:ring-2 focus:ring-vault-accent/50 focus:border-vault-accent
              transition-all duration-200
            "
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-vault-text-muted hover:text-vault-text transition-colors"
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>

        {/* Password Requirements */}
        {password && (
          <div className="space-y-1 mt-2">
            {PASSWORD_REQUIREMENTS.map((req, index) => {
              const met = req.check(password);
              return (
                <div
                  key={index}
                  className={`flex items-center gap-2 text-xs ${
                    met ? "text-green-400" : "text-vault-text-muted"
                  }`}
                >
                  <Check className={`w-3.5 h-3.5 ${met ? "opacity-100" : "opacity-30"}`} />
                  <span>{req.label}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Confirm Password Field */}
      <div className="space-y-2">
        <label htmlFor="confirm-password" className="block text-sm font-medium text-vault-text">
          Confirm Password
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
          <input
            id="confirm-password"
            type={showPassword ? "text" : "password"}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm your password"
            autoComplete="new-password"
            className={`
              w-full pl-11 pr-4 py-3
              bg-vault-bg border rounded-vault-sm
              text-vault-text placeholder:text-vault-text-muted
              focus:outline-none focus:ring-2 focus:ring-vault-accent/50 focus:border-vault-accent
              transition-all duration-200
              ${
                confirmPassword && password !== confirmPassword
                  ? "border-red-500/50"
                  : "border-vault-border"
              }
            `}
          />
        </div>
        {confirmPassword && password !== confirmPassword && (
          <p className="text-xs text-red-400">Passwords do not match</p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="
          w-full flex items-center justify-center gap-2
          py-3 px-4
          bg-vault-accent hover:bg-vault-accent-hover
          text-white font-medium
          rounded-vault-sm
          shadow-vault-sm hover:shadow-vault-md
          transition-all duration-200
          disabled:opacity-50 disabled:cursor-not-allowed
        "
      >
        {isLoading ? (
          <>
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            <span>Creating account...</span>
          </>
        ) : (
          <>
            <UserPlus className="w-5 h-5" />
            <span>Create Account</span>
          </>
        )}
      </button>

      {/* Switch to Login */}
      {onSwitchToLogin && (
        <p className="text-center text-sm text-vault-text-secondary">
          Already have an account?{" "}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-vault-accent hover:text-vault-accent-hover font-medium transition-colors"
          >
            Sign in
          </button>
        </p>
      )}
    </form>
  );
}
