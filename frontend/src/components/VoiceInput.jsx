/**
 * VoiceInput — text input and optional mic (stream chunks to WS).
 * MVP: text input only; mic sends recorded blob when done (backend does full chunk handling).
 */
import { useState, useRef } from "react";

export default function VoiceInput({ onText, onAudioChunk, disabled }) {
  const [text, setText] = useState("");
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const t = text.trim();
    if (t && onText) {
      onText(t);
      setText("");
    }
  };

  const startMic = () => {
    if (!navigator.mediaDevices?.getUserMedia || !onAudioChunk) return;
    chunksRef.current = [];
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      const rec = new MediaRecorder(stream);
      mediaRecorderRef.current = rec;
      rec.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      rec.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size && onAudioChunk) onAudioChunk(blob);
      };
      rec.start(500);
      setRecording(true);
    }).catch(() => setRecording(false));
  };

  const stopMic = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);
  };

  return (
    <div className="panel">
      <h3>Your turn</h3>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          className="input-text"
          placeholder="Type your answer or question..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
        />
        <div className="controls" style={{ marginTop: "0.5rem" }}>
          <button type="submit" className="btn primary" disabled={disabled || !text.trim()}>
            Send
          </button>
          {onAudioChunk && (
            <button
              type="button"
              className={`btn ${recording ? "primary" : ""}`}
              disabled={disabled}
              onClick={recording ? stopMic : startMic}
            >
              {recording ? "Stop mic" : "Voice input"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
