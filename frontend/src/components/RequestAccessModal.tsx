import React, { useState } from 'react';

interface RequestAccessModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RequestAccessModal: React.FC<RequestAccessModalProps> = ({ isOpen, onClose }) => {
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setSubmitted(true);
  };

  const handleReset = () => {
    setSubmitted(false);
    setEmail('');
    setCompany('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Dark backdrop */}
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-sm transition-opacity"
        onClick={handleReset}
      />

      {/* Modal dialog: floating on black void, 24px border-radius, clean subtle outline */}
      <div className="relative z-10 w-full max-w-[500px] bg-black border border-white/[0.08] rounded-[24px] p-8 md:p-12 shadow-none">
        {/* Close button */}
        <button
          onClick={handleReset}
          className="absolute top-6 right-6 text-[#9a9a9a] hover:text-white p-2 border-none bg-transparent cursor-pointer"
          aria-label="Close"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        {submitted ? (
          <div className="text-center py-6">
            <div className="w-12 h-12 mx-auto mb-6 flex items-center justify-center">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <polygon points="12,2 22,20 2,20" fill="#8052ff" />
              </svg>
            </div>
            <h3 className="text-white text-[27px] font-normal tracking-[-0.48px] mb-3">
              Request Received.
            </h3>
            <p className="text-[#bdbdbd] font-[200] text-[16px] leading-[1.6] mb-8">
              We are onboarding enterprise clusters in controlled cohorts. Your access credentials will be delivered to <span className="text-white font-normal">{email}</span>.
            </p>
            <button
              onClick={handleReset}
              className="btn-primary-pill"
            >
              Close
            </button>
          </div>
        ) : (
          <div>
            <span className="section-label">
              EARLY ACCESS
            </span>
            <h3 className="text-white text-[27px] sm:text-[32px] font-normal tracking-[-0.48px] mb-3">
              Join the Dala Network.
            </h3>
            <p className="text-[#bdbdbd] font-[200] text-[16px] leading-[1.6] mb-8">
              Connect your company's dispersed knowledge into an autonomous, distributed intelligence layer.
            </p>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-[#9a9a9a] text-[12px] uppercase font-semibold tracking-wider mb-2">
                  Work Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full bg-white/[0.04] text-white font-[200] text-[16px] rounded-[16px] px-4 py-3.5 border border-white/[0.08] focus:border-[#8052ff] focus:outline-none transition-colors"
                />
              </div>

              <div>
                <label className="block text-[#9a9a9a] text-[12px] uppercase font-semibold tracking-wider mb-2">
                  Company Name
                </label>
                <input
                  type="text"
                  required
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="Acme Corp"
                  className="w-full bg-white/[0.04] text-white font-[200] text-[16px] rounded-[16px] px-4 py-3.5 border border-white/[0.08] focus:border-[#8052ff] focus:outline-none transition-colors"
                />
              </div>

              <div className="pt-4">
                <button
                  type="submit"
                  className="btn-primary-pill w-full justify-center"
                >
                  Submit Request
                </button>
              </div>

              <p className="text-[#9a9a9a] text-[12px] font-[200] text-center pt-2">
                100% private. Zero telemetry leaves your secure perimeter.
              </p>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
