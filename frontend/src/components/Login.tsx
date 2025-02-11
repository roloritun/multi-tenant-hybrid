import React, { useState } from 'react';
import { GoogleLogin } from 'react-google-login';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [isOtpSent, setIsOtpSent] = useState(false);

  const handleGoogleSuccess = async (response: any) => {
    try {
      const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: response.tokenId }),
      });
      
      const data = await res.json();
      // Store token in localStorage or state management solution
      localStorage.setItem('token', data.access_token);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleOtpRequest = async () => {
    try {
      await fetch('/api/auth/otp/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      setIsOtpSent(true);
    } catch (error) {
      console.error('OTP request failed:', error);
    }
  };

  const handleOtpVerify = async () => {
    try {
      const res = await fetch('/api/auth/otp/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, otp }),
      });
      
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
    } catch (error) {
      console.error('OTP verification failed:', error);
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      
      <GoogleLogin
        clientId="your-google-client-id"
        buttonText="Login with Google"
        onSuccess={handleGoogleSuccess}
        onFailure={(error) => console.error('Google login failed:', error)}
      />

      <div className="otp-section">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        
        {!isOtpSent ? (
          <button onClick={handleOtpRequest}>Send OTP</button>
        ) : (
          <>
            <input
              type="text"
              placeholder="Enter OTP"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
            />
            <button onClick={handleOtpVerify}>Verify OTP</button>
          </>
        )}
      </div>
    </div>
  );
};

export default Login; 