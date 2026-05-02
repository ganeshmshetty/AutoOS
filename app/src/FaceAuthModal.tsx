import { useRef, useState, useEffect, useCallback } from 'react';
import { Camera, ShieldCheck, RefreshCw, CheckCircle } from 'lucide-react';

interface FaceAuthModalProps {
  mode: 'register' | 'verify';
  onSuccess: () => void;
  onCancel: () => void;
}

type Step = 'camera' | 'preview' | 'sending' | 'success' | 'error';

export function FaceAuthModal({ mode, onSuccess, onCancel }: FaceAuthModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [step, setStep] = useState<Step>('camera');
  const [capturedImage, setCapturedImage] = useState<string | null>(null); // base64 data URL
  const [errorMsg, setErrorMsg] = useState('');

  const isRegister = mode === 'register';

  // ── Start camera on mount, stop on unmount ─────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    navigator.mediaDevices
      .getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      })
      .then((s) => {
        if (cancelled) { s.getTracks().forEach((t) => t.stop()); return; }
        streamRef.current = s;
        if (videoRef.current) videoRef.current.srcObject = s;
      })
      .catch((err) => {
        if (!cancelled) {
          setErrorMsg('Camera access denied or unavailable. Please allow camera permissions and try again.');
          setStep('error');
        }
        console.error('Camera error:', err);
      });

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, []);

  // ── Stop camera once we no longer need the live feed ───────────────────────
  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  // ── Step 1 → 2: take a still photo ────────────────────────────────────────
  const takePhoto = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    if (video.videoWidth === 0 || video.videoHeight === 0) {
      setErrorMsg('Camera is still loading — please wait a moment and try again.');
      setStep('error');
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Draw mirrored (same as the video preview)
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    setCapturedImage(dataUrl);
    setStep('preview');
    // Stop the live feed — we have the photo
    stopCamera();
  }, [stopCamera]);

  // ── Step 2 → camera: retake ────────────────────────────────────────────────
  const retake = useCallback(() => {
    setCapturedImage(null);
    setStep('camera');
    setCameraReady(false);
    // Restart camera
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } } })
      .then((s) => {
        streamRef.current = s;
        if (videoRef.current) videoRef.current.srcObject = s;
      })
      .catch(() => {
        setErrorMsg('Could not restart camera.');
        setStep('error');
      });
  }, []);

  // ── Step 2 → 3: send to backend ───────────────────────────────────────────
  const confirmAndSend = useCallback(async () => {
    if (!capturedImage) return;
    setStep('sending');

    const endpoint = isRegister ? '/api/face-auth/register' : '/api/face-auth/verify';
    try {
      const res = await fetch(`http://localhost:8765${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: capturedImage }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Request failed');
      }

      if (!isRegister && !data.verified) {
        throw new Error('Face does not match the registered owner. Please try again.');
      }

      setStep('success');
      setTimeout(() => onSuccess(), 900);
    } catch (err: any) {
      setErrorMsg(err.message || 'Something went wrong. Please try again.');
      setStep('error');
    }
  }, [capturedImage, isRegister, onSuccess]);

  // ── Retry from error ───────────────────────────────────────────────────────
  const retry = useCallback(() => {
    setErrorMsg('');
    setCapturedImage(null);
    setStep('camera');
    setCameraReady(false);
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } } })
      .then((s) => {
        streamRef.current = s;
        if (videoRef.current) videoRef.current.srcObject = s;
      })
      .catch(() => {
        setErrorMsg('Camera is not available.');
        setStep('error');
      });
  }, []);

  // ── Derived ────────────────────────────────────────────────────────────────
  const title = isRegister ? 'Register Your Face' : 'Face Verification';
  const subtitle =
    step === 'camera'
      ? isRegister
        ? 'Position your face in the oval, then click "Take Photo".'
        : 'Look at the camera and click "Take Photo" to verify your identity.'
      : step === 'preview'
      ? 'Happy with the shot? Click "Confirm" to proceed, or "Retake" to try again.'
      : step === 'sending'
      ? isRegister ? 'Saving your face…' : 'Verifying your identity…'
      : step === 'success'
      ? isRegister ? 'Face registered successfully!' : 'Identity confirmed!'
      : 'Something went wrong.';

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)',
      }}
    >
      <div
        style={{
          background: '#0f172a',
          border: '1px solid #1e293b',
          borderRadius: '16px',
          padding: '28px 24px',
          width: '420px',
          maxWidth: '95vw',
          boxShadow: '0 25px 60px rgba(0,0,0,0.6)',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        {/* ── Header ── */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '10px' }}>
            <div style={{
              background: 'rgba(56,189,248,0.1)', borderRadius: '50%',
              padding: '12px', display: 'inline-flex',
            }}>
              {isRegister ? <Camera size={28} color="#38bdf8" /> : <ShieldCheck size={28} color="#38bdf8" />}
            </div>
          </div>
          <h2 style={{ margin: 0, color: '#f1f5f9', fontSize: '1.2rem', fontWeight: 700 }}>{title}</h2>
          <p style={{ margin: '6px 0 0', color: '#64748b', fontSize: '0.875rem' }}>{subtitle}</p>
        </div>

        {/* ── Camera / Preview frame ── */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            aspectRatio: '4/3',
            borderRadius: '12px',
            overflow: 'hidden',
            background: '#000',
            border: `2px solid ${
              step === 'success' ? '#10b981' :
              step === 'error'   ? '#ef4444' :
              step === 'preview' ? '#38bdf8' : '#1e293b'
            }`,
            transition: 'border-color 0.3s',
          }}
        >
          {/* Live camera — always mounted, hidden when not in camera step */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            onCanPlay={() => setCameraReady(true)}
            style={{
              position: 'absolute', inset: 0,
              width: '100%', height: '100%', objectFit: 'cover',
              transform: 'scaleX(-1)', // mirror for natural selfie feel
              display: (step === 'camera') ? 'block' : 'none',
            }}
          />

          {/* Face oval guide */}
          {step === 'camera' && cameraReady && (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex',
              alignItems: 'center', justifyContent: 'center', pointerEvents: 'none',
            }}>
              <div style={{
                width: '44%', aspectRatio: '3/4', borderRadius: '50%',
                border: '2px dashed rgba(56,189,248,0.7)',
                boxShadow: '0 0 0 9999px rgba(0,0,0,0.3)',
              }} />
            </div>
          )}

          {/* Camera loading */}
          {step === 'camera' && !cameraReady && (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex',
              flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              color: '#475569', gap: '10px',
            }}>
              <Camera size={36} opacity={0.4} />
              <span style={{ fontSize: '0.85rem' }}>Starting camera…</span>
            </div>
          )}

          {/* Captured photo preview */}
          {step === 'preview' && capturedImage && (
            <img
              src={capturedImage}
              alt="Captured"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          )}

          {/* Sending overlay */}
          {step === 'sending' && capturedImage && (
            <>
              <img
                src={capturedImage}
                alt="Captured"
                style={{ width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(0.4)' }}
              />
              <div style={{
                position: 'absolute', inset: 0, display: 'flex',
                flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px',
              }}>
                <div style={{
                  width: '36px', height: '36px', borderRadius: '50%',
                  border: '3px solid rgba(56,189,248,0.2)', borderTopColor: '#38bdf8',
                  animation: 'spin 0.8s linear infinite',
                }} />
                <span style={{ color: '#38bdf8', fontSize: '0.9rem', fontWeight: 500 }}>
                  {isRegister ? 'Saving…' : 'Verifying…'}
                </span>
              </div>
            </>
          )}

          {/* Success overlay */}
          {step === 'success' && (
            <>
              {capturedImage && (
                <img
                  src={capturedImage}
                  alt="Captured"
                  style={{ width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(0.4)' }}
                />
              )}
              <div style={{
                position: 'absolute', inset: 0, display: 'flex',
                flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                gap: '10px', background: 'rgba(16,185,129,0.2)',
              }}>
                <CheckCircle size={48} color="#10b981" />
                <span style={{ color: '#10b981', fontWeight: 700, fontSize: '1rem' }}>
                  {isRegister ? 'Face Saved!' : 'Identity Confirmed!'}
                </span>
              </div>
            </>
          )}

          {/* Error display */}
          {step === 'error' && (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex',
              flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              padding: '24px', gap: '10px', background: 'rgba(239,68,68,0.08)',
              textAlign: 'center',
            }}>
              <span style={{ color: '#ef4444', fontSize: '0.875rem', lineHeight: 1.5 }}>{errorMsg}</span>
            </div>
          )}

          {/* Hidden canvas for capture */}
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>

        {/* ── Action buttons ── */}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
          {/* Cancel — always visible except during sending/success */}
          {step !== 'sending' && step !== 'success' && (
            <button
              onClick={onCancel}
              style={{
                padding: '10px 20px', borderRadius: '8px', border: '1px solid #1e293b',
                background: 'transparent', color: '#94a3b8', cursor: 'pointer',
                fontSize: '0.875rem', fontWeight: 500,
              }}
            >
              Cancel
            </button>
          )}

          {/* CAMERA step: Take Photo */}
          {step === 'camera' && (
            <button
              onClick={takePhoto}
              disabled={!cameraReady}
              style={{
                padding: '10px 24px', borderRadius: '8px', border: 'none',
                background: cameraReady ? 'linear-gradient(135deg, #38bdf8, #818cf8)' : '#1e293b',
                color: cameraReady ? '#fff' : '#475569',
                cursor: cameraReady ? 'pointer' : 'not-allowed',
                fontSize: '0.875rem', fontWeight: 600,
                display: 'flex', alignItems: 'center', gap: '8px',
                transition: 'all 0.2s',
              }}
            >
              <Camera size={16} />
              {cameraReady ? 'Take Photo' : 'Loading camera…'}
            </button>
          )}

          {/* PREVIEW step: Retake + Confirm */}
          {step === 'preview' && (
            <>
              <button
                onClick={retake}
                style={{
                  padding: '10px 20px', borderRadius: '8px', border: '1px solid #1e293b',
                  background: 'transparent', color: '#94a3b8', cursor: 'pointer',
                  fontSize: '0.875rem', fontWeight: 500,
                  display: 'flex', alignItems: 'center', gap: '6px',
                }}
              >
                <RefreshCw size={14} /> Retake
              </button>
              <button
                onClick={confirmAndSend}
                style={{
                  padding: '10px 24px', borderRadius: '8px', border: 'none',
                  background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
                  color: '#fff', cursor: 'pointer',
                  fontSize: '0.875rem', fontWeight: 600,
                  display: 'flex', alignItems: 'center', gap: '8px',
                }}
              >
                <CheckCircle size={16} />
                {isRegister ? 'Confirm & Save' : 'Confirm & Verify'}
              </button>
            </>
          )}

          {/* ERROR step: Try Again */}
          {step === 'error' && (
            <button
              onClick={retry}
              style={{
                padding: '10px 24px', borderRadius: '8px', border: 'none',
                background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
                color: '#fff', cursor: 'pointer',
                fontSize: '0.875rem', fontWeight: 600,
                display: 'flex', alignItems: 'center', gap: '8px',
              }}
            >
              <RefreshCw size={16} /> Try Again
            </button>
          )}
        </div>
      </div>

      {/* Spin animation */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
