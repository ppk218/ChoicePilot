import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const PaymentError = ({ onClose }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleRetry = () => {
    if (onClose) {
      onClose();
    } else {
      navigate('/');
    }
  };

  const getErrorDetails = () => {
    const params = new URLSearchParams(location.search);
    return {
      error: params.get('error'),
      errorDescription: params.get('error_description'),
      paymentId: params.get('payment_id')
    };
  };

  const details = getErrorDetails();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4 text-center">
        {/* Error Icon */}
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>

        {/* Error Message */}
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Failed</h2>
        <p className="text-gray-600 mb-6">
          We encountered an issue processing your payment. Don't worry, no charges have been made to your account.
        </p>

        {/* Error Details */}
        {(details.error || details.errorDescription) && (
          <div className="bg-red-50 rounded-lg p-4 mb-6 text-left">
            <h3 className="font-semibold text-red-900 mb-3">Error Details</h3>
            <div className="space-y-2 text-sm">
              {details.error && (
                <div className="flex justify-between">
                  <span className="text-red-600">Error Code:</span>
                  <span className="font-medium">{details.error}</span>
                </div>
              )}
              {details.errorDescription && (
                <div>
                  <span className="text-red-600">Description:</span>
                  <p className="text-red-800 mt-1">{details.errorDescription}</p>
                </div>
              )}
              {details.paymentId && (
                <div className="flex justify-between">
                  <span className="text-red-600">Reference:</span>
                  <span className="font-mono text-xs">{details.paymentId}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Common Issues */}
        <div className="bg-yellow-50 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-yellow-900 mb-2">Common Issues</h3>
          <ul className="text-sm text-yellow-800 space-y-1 text-left">
            <li>• Insufficient funds in your account</li>
            <li>• Credit card expired or blocked</li>
            <li>• Incorrect billing information</li>
            <li>• Bank declined the transaction</li>
            <li>• Network connection issues</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleRetry}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium"
          >
            Try Again
          </button>
          
          <button
            onClick={() => window.history.back()}
            className="w-full bg-gray-100 text-gray-800 py-3 px-6 rounded-lg hover:bg-gray-200 transition-colors duration-200 font-medium"
          >
            Go Back
          </button>
        </div>

        {/* Support Section */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h4 className="font-semibold text-gray-900 mb-2">Need Help?</h4>
          <p className="text-sm text-gray-600 mb-3">
            If you continue to experience issues, please contact our support team.
          </p>
          <div className="space-y-2">
            <a
              href="mailto:support@choicepilot.ai"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              support@choicepilot.ai
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentError;