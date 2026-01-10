/**
 * Forgot Password Form Component
 *
 * Allows users to request a password reset email via Firebase.
 * Vault Elegance design system styling.
 */

import { useState } from "react";
import { resetPassword } from "../../config/firebase";

interface ForgotPasswordFormProps {
  onBack: () => void;
}

export function ForgotPasswordForm({ onBack }: ForgotPasswordFormProps) {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await resetPassword(email);
      setSuccess(true);
    } catch (err) {
      const firebaseError = err as { code?: string; message?: string };

      // Map Firebase error codes to user-friendly messages
      switch (firebaseError.code) {
        case "auth/user-not-found":
          // Don't reveal if email exists for security
          setSuccess(true);
          break;
        case "auth/invalid-email":
          setError("Invalid email address");
          break;
        case "auth/too-many-requests":
          setError("Too many requests. Please try again later.");
          break;
        default:
          // Still show success to not reveal email existence
          setSuccess(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="space-y-6">
        {/* Success Icon */}
        <div className="flex justify-center">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
        </div>

        {/* Success Message */}
        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold text-stone-900">
            Check your email
          </h3>
          <p className="text-sm text-stone-600">
            If an account exists for <strong>{email}</strong>, you will receive
            a password reset link shortly.
          </p>
        </div>

        {/* Back to Login Button */}
        <button
          type="button"
          onClick={onBack}
          className="w-full py-3 px-4 bg-stone-100 text-stone-700 rounded-lg font-medium
                   hover:bg-stone-200 transition-colors"
        >
          Back to Sign In
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h3 className="text-lg font-semibold text-stone-900">
          Reset your password
        </h3>
        <p className="text-sm text-stone-600">
          Enter your email address and we'll send you a link to reset your
          password.
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div
          className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2"
          role="alert"
        >
          <svg
            className="w-4 h-4 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          {error}
        </div>
      )}

      {/* Email Input */}
      <div className="space-y-2">
        <label
          htmlFor="reset-email"
          className="block text-sm font-medium text-stone-700"
        >
          Email
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg
              className="h-5 w-5 text-stone-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          <input
            id="reset-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            className="w-full pl-10 pr-4 py-3 border border-stone-300 rounded-lg
                     focus:ring-2 focus:ring-[#8B7355] focus:border-transparent
                     placeholder:text-stone-400 text-stone-900"
          />
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !email}
        className="w-full py-3 px-4 bg-[#8B7355] text-white rounded-lg font-medium
                 hover:bg-[#6B5A45] disabled:opacity-50 disabled:cursor-not-allowed
                 transition-colors flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <svg
              className="animate-spin h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Sending...
          </>
        ) : (
          "Send Reset Link"
        )}
      </button>

      {/* Back Link */}
      <button
        type="button"
        onClick={onBack}
        className="w-full text-center text-sm text-[#8B7355] hover:text-[#6B5A45]
                 transition-colors"
      >
        Back to Sign In
      </button>
    </form>
  );
}
