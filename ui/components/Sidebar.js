"use client";

import { useState, useRef, useEffect } from "react";

export default function Sidebar({ logs }) {
  const [open, setOpen] = useState(true);
  const [copied, setCopied] = useState(false);
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [logs]);

  const handleCopy = async () => {
    const text = logs.length > 0 ? logs.join("\n") : "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (_) {}
  };

  return (
    <aside
      className={`shrink-0 border-l border-[#e5e3e0] bg-white flex flex-col h-screen overflow-hidden transition-[width] duration-200 ease-out ${
        open ? "w-[440px]" : "w-14"
      }`}
    >
      <button
        onClick={() => setOpen(!open)}
        className="shrink-0 p-3 border-b border-[#e5e3e0] flex items-center justify-center gap-2 hover:bg-[#f9f9f9] text-[#6b6b6b] hover:text-[#1a1a1a]"
        aria-label={open ? "طي الشريط الجانبي" : "فتح الشريط الجانبي"}
      >
        <span className="text-lg font-medium">{open ? "‹" : "›"}</span>
        {open && <span className="text-xs">السجل</span>}
      </button>

      {open && (
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="p-4 border-b border-[#e5e3e0] shrink-0">
            <h3 className="text-sm font-semibold text-[#1a1a1a] mb-1">الإعدادات</h3>
            <p className="text-[12px] text-[#6b6b6b]">لا توجد إعدادات متاحة حاليًا.</p>
          </div>
          <div className="flex-1 flex flex-col min-h-0 p-4 overflow-hidden">
            <div className="flex items-center justify-between gap-2 mb-2 shrink-0">
              <h3 className="text-sm font-semibold text-[#1a1a1a]">السجل</h3>
              <button
                onClick={handleCopy}
                disabled={logs.length === 0}
                className="text-[11px] px-2 py-1 rounded border border-[#e5e3e0] hover:bg-[#f5f5f5] disabled:opacity-50 disabled:cursor-not-allowed text-[#6b6b6b]"
              >
                {copied ? "تم النسخ" : "نسخ"}
              </button>
            </div>
            <div className="flex-1 min-h-0 rounded-lg bg-[#1a1a1a] text-[#e5e5e5] p-3 font-mono text-[11px] leading-relaxed overflow-y-auto overflow-x-auto overscroll-contain">
              <pre className="whitespace-pre-wrap break-words m-0 min-w-0">
                {logs.length > 0 ? logs.join("\n") : "لم تبدأ أي عملية بعد."}
                <span ref={logEndRef} />
              </pre>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
