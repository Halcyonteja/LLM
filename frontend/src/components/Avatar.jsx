/**
 * Avatar — 2D canvas: idle / listening / talking with simple lip sync.
 * State comes from backend (idle | listening | talking).
 */
import { useEffect, useRef } from "react";

const W = 240;
const H = 200;

export default function Avatar({ state = "idle" }) {
  const canvasRef = useRef(null);
  const frameRef = useRef(0);
  const mouthRef = useRef(0);
  const phaseRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let raf = 0;

    const draw = () => {
      const t = phaseRef.current;
      const mouth = mouthRef.current;

      ctx.fillStyle = "#1a1b26";
      ctx.fillRect(0, 0, W, H);

      // Head circle
      ctx.fillStyle = "#24283b";
      ctx.beginPath();
      ctx.arc(W / 2, H / 2 - 10, 70, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#414868";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Eyes
      const eyeY = H / 2 - 40;
      const eyeOff = 25;
      const blink = state === "idle" ? (Math.sin(t * 2) > 0.98 ? 0.3 : 1) : 1;
      ctx.fillStyle = "#c0caf5";
      ctx.beginPath();
      ctx.ellipse(W / 2 - eyeOff, eyeY, 8, 10 * blink, 0, 0, Math.PI * 2);
      ctx.ellipse(W / 2 + eyeOff, eyeY, 8, 10 * blink, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#1a1b26";
      ctx.beginPath();
      ctx.arc(W / 2 - eyeOff, eyeY, 4, 0, Math.PI * 2);
      ctx.arc(W / 2 + eyeOff, eyeY, 4, 0, Math.PI * 2);
      ctx.fill();

      // Mouth: lip sync when talking; slight open when listening
      const mouthOpen = state === "talking" ? 0.3 + mouth * 0.25 : state === "listening" ? 0.1 : 0.05;
      ctx.strokeStyle = "#c0caf5";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.ellipse(W / 2, H / 2 + 25, 20, 8 * mouthOpen, 0, 0, Math.PI * 2);
      ctx.stroke();

      phaseRef.current += 0.02;
      if (state === "talking") {
        mouthRef.current = 0.5 + 0.5 * Math.sin(t * 8);
      } else {
        mouthRef.current *= 0.9;
      }
      raf = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(raf);
  }, [state]);

  return (
    <canvas
      ref={canvasRef}
      width={W}
      height={H}
      style={{ display: "block", borderRadius: 8 }}
      aria-label={`Avatar ${state}`}
    />
  );
}
