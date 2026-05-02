import { useRef, useState, useEffect, useCallback } from 'react';
import { Camera, ShieldCheck, RefreshCw } from 'lucide-react';

interface FaceAuthModalProps {
  mode: 'register' | 'verify';
  onSuccess: () => void;
  onCancel: () => void;
}

export function FaceAuthModal({ mode, onSuccess, onCancel }: FaceAuthModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);   // use ref, not state, to avoid stale closure
  const [cameraReady, setCameraReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Start camera on mount, stop on unmount — using ref so cleanup always sees the stream
  useEffect(() => {
    let cancelled = false;

    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } } })
      .then((s) => {
        if (cancelled) {
          s.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = s;
        if (videoRef.current) {
          videoRef.current.srcObject = s;
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError('Camera access denied or unavailable. Please allow camera access and try again.');
          console.error('Camera error:', err);
        }
      });

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, []);

  const handleRetry = useCallback(() => {
    setError(null);
    setLoading(false);
  }, []);

  const captureAndSend = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) return;

    // Guard: video must be playing and have valid dimensions
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      setError('Camera is not ready yet. Please wait a moment and try again.');
      return;
    }

    setLoading(true);
    setError(null);

    // Capture frame to canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setError('Could not access canvas context.');
      setLoading(false);
      return;
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const base64Image = canvas.toDataURL('image/jpeg', 0.92);

    const endpoint = mode === 'register' ? '/api/face-auth/register' : '/api/face-auth/verify';

    try {
      const res = await fetch(`http://localhost:8765${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: base64Image }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Request failed');
      }

      if (mode === 'verify' && !data.verified) {
        throw new Error('Face does not match the registered owner. Please try again.');
      }

      // Success — stop camera before calling onSuccess so the indicator turns off
      setSuccess(true);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      setTimeout(() => onSuccess(), 600); // brief flash of success state
    } catch (err: any) {
      setError(err.message || 'An error occurred. Please try again.');
      setLoading(false);
    }
  }, [mode, onSuccess]);

  const isRegister = mode === 'register';
  const btnLabel = loading
    ? 'Processing...'
    : success
    ? isRegister ? '✓ Registered!' : '✓ Verified!'
    : isRegister ? 'Capture & Register' : 'Verify & Run';

  return (
    <div className="hitl-overlay" style={{ zIndex: 9999 }}>
      <div className="hitl-modal" style={{ maxWidth: '420px', textAlign: 'center' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', marginBottom: '8px' }}>
          {isRegister ? <Camera size={22} color="#38bdf8" /> : <ShieldCheck size={22} color="#38bdf8" />}
          <h3 style={{ margin: 0 }}>
            {isRegister ? 'Register Master Face' : 'Face Verification Required'}
          </h3>
        </div>
        <p style={{ opacity: 0.7, marginBottom: '16px', fontSize: '0.875rem' }}>
          {isRegister
            ? 'Position your face in the frame and click Capture.'
            : 'Please verify your identity to run this workflow.'}
        </p>

        {/* Camera / Error area */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            background: '#000',
            borderRadius: '10px',
            overflow: 'hidden',
            aspectRatio: '4/3',
            marginBottom: '16px',
            border: success ? '2px solid #10b981' : error ? '2px solid #ef4444' : '2px solid transparent',
            transition: 'border-color 0.3s',
          }}
        >
          {/* Video always mounted so the stream attaches immediately */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            onCanPlay={() => setCameraReady(true)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              display: error ? 'none' : 'block',
              transform: 'scaleX(-1)', // mirror so it feels natural
            }}
          />

          {/* Overlay: camera-not-ready spinner */}
          {!cameraReady && !error && (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              color: '#64748b', fontSize: '0.85rem', flexDirection: 'column', gap: '8px',
            }}>
              <Camera size={32} opacity={0.4} />
              <span>Starting camera…</span>
            </div>
          )}

          {/* Overlay: face guide oval */}
          {cameraReady && !error && !success && (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex',
              alignItems: 'center', justifyContent: 'center', pointerEvents: 'none',
            }}>
              <div style={{
                width: '45%', aspectRatio: '3/4',
                borderRadius: '50%',
                border: '2px dashed rgba(56, 189, 248, 0.6)',
                boxShadow: '0 0 0 2000px rgba(0,0,0,0.25)',
              }} />
            </div>
          )}

          {/* Success flash */}
          {success && (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              background: 'rgba(16,185,129,0.25)', color: '#10b981', fontSize: '1.1rem', fontWeight: 600, gap: '8px',
            }}>
              <ShieldCheck size={28} /> {isRegister ? 'Face Registered!' : 'Identity Confirmed!'}
            </div>
          )}

          {/* Error display */}
          {error && (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              height: '100%', padding: '24px', color: '#ef4444', fontSize: '0.875rem',
              background: 'rgba(239,68,68,0.08)',
            }}>
              {error}
            </div>
          )}

          {/* Hidden canvas for capture */}
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>

        {/* Actions */}
        <div className="hitl-actions" style={{ justifyContent: 'center', gap: '12px' }}>
          <button className="secondary-btn" onClick={onCancel} disabled={loading || success}>
            Cancel
          </button>

          {error ? (
            <button className="primary-btn" onClick={handleRetry} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <RefreshCw size={16} /> Try Again
            </button>
          ) : (
            <button
              className="primary-btn"
              onClick={captureAndSend}
              disabled={loading || success || !cameraReady}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              {isRegister ? <Camera size={16} /> : <ShieldCheck size={16} />}
              {btnLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
