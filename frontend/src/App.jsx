/**
 * Local AI Tutor — main app. 
 * Updated to handle streaming tokens for slow CPUs (i3 optimization).
 */
import { useState, useEffect, useRef } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import Avatar from "./components/Avatar";
import VoiceInput from "./components/VoiceInput";
import TeachingPanel from "./components/TeachingPanel";

export default function App() {
  const { connected, lastMessage, error, send, sendAudio } = useWebSocket();
  const [avatarState, setAvatarState] = useState("idle");
  const [assistantText, setAssistantText] = useState("");
  const [concepts, setConcepts] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  
  const audioCtxRef = useRef(null);
  const lastIdRef = useRef(0);

  // Process inbound WS messages
  useEffect(() => {
    if (!lastMessage) return;
    const id = ++lastIdRef.current;
    const type = lastMessage.type;

    // 1. Handle Streaming Tokens (i3 Optimization)
    if (type === "token") {
      // Append the new token to existing text immediately
      setAssistantText((prev) => prev + (lastMessage.text || ""));
      // Ensure avatar looks active while streaming
      setAvatarState("talking");
    } 
    
    // 2. Handle Avatar State changes from backend
    else if (type === "avatar") {
      setAvatarState(lastMessage.state || "idle");
    } 
    
    // 3. Handle Full Text (Fallback or final updates)
    else if (type === "assistant_text") {
      setAssistantText(lastMessage.text || "");
    } 
    
    // 4. Initialization
    else if (type === "ready") {
      setSessionId(lastMessage.session_id || null);
      if (Array.isArray(lastMessage.example_concepts)) {
        setConcepts(lastMessage.example_concepts);
      }
    } 
    
    // 5. Audio Playback
    else if (type === "tts_chunk") {
      const b64 = lastMessage.data;
      if (!b64) return;
      try {
        const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
        playWav(bytes, id);
      } catch (err) {
        console.error("Audio decode error:", err);
      }
    } 
    
    else if (type === "error") {
      console.error("Backend error:", lastMessage.message);
    }
  }, [lastMessage]);

  const playWav = (bytes, playId) => {
    // Stop if a newer request has already started
    if (playId !== lastIdRef.current) return;

    const ctx = audioCtxRef.current || new (window.AudioContext || window.webkitAudioContext)();
    audioCtxRef.current = ctx;

    ctx.decodeAudioData(bytes.buffer).then((buf) => {
      const src = ctx.createBufferSource();
      src.buffer = buf;
      src.connect(ctx.destination);
      
      // Update avatar state while audio plays
      setAvatarState("talking");
      src.onended = () => setAvatarState("idle");
      
      src.start(0);
    }).catch((err) => console.error("Playback error:", err));
  };

  const handleStartConcept = (concept) => {
    setAssistantText(""); // Clear UI for new explanation
    send({ type: "start_concept", concept });
  };

  const handleUserText = (text) => {
    setAssistantText(""); // Clear UI for new reply
    send({ type: "user_text", text });
  };

  const handleAudioChunk = (blobOrBuf) => {
    setAssistantText(""); // Clear UI while waiting for STT
    if (blobOrBuf instanceof Blob || blobOrBuf instanceof ArrayBuffer) {
      sendAudio(blobOrBuf);
    } else if (blobOrBuf && typeof blobOrBuf === "object" && blobOrBuf.byteLength != null) {
      sendAudio(blobOrBuf);
    }
  };

  useEffect(() => {
    if (connected) send({ type: "start_session" });
  }, [connected, send]);

  return (
    <div className="tutor-layout">
      <header style={{ textAlign: 'center', padding: '1rem' }}>
        <h1>Local AI Tutor</h1>
        <p className={`status ${connected ? "online" : "offline"}`}>
          {connected ? "● Connected" : "○ Disconnected"}
          {error && <span className="error"> — {error}</span>}
        </p>
      </header>

      <main style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
        <div className="avatar-container" style={{ background: '#f0f0f0', borderRadius: '50%', padding: '20px' }}>
          <Avatar state={avatarState} />
        </div>

        <TeachingPanel
          assistantText={assistantText}
          concepts={concepts}
          onStartConcept={handleStartConcept}
          disabled={!connected}
        />

        <VoiceInput
          onText={handleUserText}
          onAudioChunk={handleAudioChunk}
          disabled={!connected}
        />
      </main>
    </div>
  );
}