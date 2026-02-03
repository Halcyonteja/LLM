/**
 * useWebSocket — connect to backend WS, send JSON, receive messages.
 * Backend runs at ws://127.0.0.1:8765/ws by default.
 */
import { useState, useEffect, useRef, useCallback } from "react";

const WS_URL = "ws://127.0.0.1:8765/ws";

export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setError(null);
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      reconnectTimeoutRef.current = setTimeout(connect, 2000);
    };
    ws.onerror = (e) => setError("WebSocket error");
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        setLastMessage(msg);
      } catch {
        setLastMessage({ type: "raw", data: e.data });
      }
    };
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  const send = useCallback((msg) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    const s = typeof msg === "string" ? msg : JSON.stringify(msg);
    wsRef.current.send(s);
  }, []);

  const sendAudio = useCallback((blobOrArrayBuffer) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    if (blobOrArrayBuffer instanceof Blob) {
      blobOrArrayBuffer.arrayBuffer().then((buf) => wsRef.current.send(buf));
    } else {
      wsRef.current.send(blobOrArrayBuffer);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connected,
    lastMessage,
    error,
    send,
    sendAudio,
    connect,
    disconnect,
  };
}
