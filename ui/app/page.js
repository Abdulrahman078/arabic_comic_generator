"use client";

import { useState } from "react";
import { PIPELINE_TIMEOUT_MS } from "../lib/timeouts.js";
import Sidebar from "../components/Sidebar";
import MainContent from "../components/MainContent";

export default function Home() {
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const onGenerate = async (prompt) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setLogs([]);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), PIPELINE_TIMEOUT_MS);
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || res.statusText);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let logBuffer = [];
      let rafId = null;

      const flushLogs = () => {
        if (logBuffer.length === 0) return;
        const toAdd = logBuffer.splice(0);
        setLogs((prev) => [...prev, ...toAdd]);
      };

      const scheduleFlush = () => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
          rafId = null;
          flushLogs();
        });
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const obj = JSON.parse(line);
            if (obj.t === "log") {
              logBuffer.push(obj.m);
              scheduleFlush();
            } else if (obj.t === "done") {
              if (rafId) cancelAnimationFrame(rafId);
              flushLogs();
              if (obj.logs) setLogs(obj.logs);
              if (obj.success) {
                setResult({ pageBase64: obj.page_base64, script: obj.script });
              } else {
                setError(obj.error || "Unknown error");
              }
            }
          } catch (_) {}
        }
      }
      if (buffer.trim()) {
        try {
          const obj = JSON.parse(buffer);
          if (obj.t === "log") {
            logBuffer.push(obj.m);
            flushLogs();
          } else if (obj.t === "done") {
            if (rafId) cancelAnimationFrame(rafId);
            flushLogs();
            if (obj.logs) setLogs(obj.logs);
            if (obj.success) setResult({ pageBase64: obj.page_base64, script: obj.script });
            else setError(obj.error || "Unknown error");
          }
        } catch (_) {}
      }
    } catch (err) {
      setError(err.name === "AbortError" ? "انتهت المهلة - جرّب مرة أخرى" : err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-row-reverse h-screen bg-[#faf9f7] overflow-hidden">
      <main className="flex-1 min-w-0 min-h-0 overflow-auto">
        <MainContent
          onGenerate={onGenerate}
          loading={loading}
          result={result}
          error={error}
        />
      </main>
      <Sidebar logs={logs} />
    </div>
  );
}
