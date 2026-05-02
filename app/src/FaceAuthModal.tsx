import React, { useRef, useState, useEffect } from 'react';

interface FaceAuthModalProps {
  mode: 'register' | 'verify';
  onSuccess: () => void;
  onCancel: () => void;
}

export function FaceAuthModal({ mode, onSuccess, onCancel }: FaceAuthModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Start camera
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(s => {
        setStream(s);
        if (videoRef.current) {
          videoRef.current.srcObject = s;
        }
      })
      .catch(err => {
        setError('Camera access denied or unavailable.');
        console.error(err);
      });

    return () => {
      // Stop camera on unmount
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  // Cleanup stream when component unmounts
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  const captureAndSend = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    setLoading(true);
    setError(null);
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const base64Image = canvas.toDataURL('image/jpeg', 0.8);
    
    try {
      const endpoint = mode === 'register' ? '/api/face-auth/register' : '/api/face-auth/verify';
      const res = await fetch(`http://localhost:8765${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: base64Image })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || 'Face verification failed');
      }
      
      if (mode === 'verify' && !data.verified) {
        throw new Error('Face does not match the registered owner.');
      }
      
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'An error occurred during facial verification.');
      setLoading(false);
    }
  };

  return (
    <div className="hitl-overlay" style={{ zIndex: 9999 }}>
      <div className="hitl-modal" style={{ maxWidth: '400px', textAlign: 'center' }}>
        <h3>{mode === 'register' ? 'Register Master Face' : 'Face Verification Required'}</h3>
        <p style={{ opacity: 0.8, marginBottom: '16px' }}>
          {mode === 'register' 
            ? 'Look directly at the camera to register yourself as the owner.'
            : 'Please verify your identity to run this workflow.'}
        </p>
        
        <div style={{ position: 'relative', width: '100%', background: '#000', borderRadius: '8px', overflow: 'hidden', aspectRatio: '4/3', marginBottom: '16px' }}>
          {error ? (
             <div style={{ color: 'var(--red)', padding: '20px', paddingTop: '100px' }}>{error}</div>
          ) : (
            <video 
              ref={videoRef} 
              autoPlay 
              playsInline 
              muted
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          )}
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>

        <div className="hitl-actions" style={{ justifyContent: 'center' }}>
          <button className="secondary-btn" onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          {!error && (
            <button className="primary-btn" onClick={captureAndSend} disabled={loading}>
              {loading ? 'Processing...' : (mode === 'register' ? 'Capture & Register' : 'Verify & Run')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
