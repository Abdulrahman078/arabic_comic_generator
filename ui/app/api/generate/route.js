import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import { PIPELINE_TIMEOUT_MS } from "../../../lib/timeouts.js";

/** Next.js / Vercel route max duration (seconds). Align with PIPELINE_TIMEOUT_MS when deploying. */
export const maxDuration = 1200;

function getPythonPath(projectRoot) {
  const isWin = process.platform === "win32";
  const venvPython = isWin
    ? path.join(projectRoot, ".venv", "Scripts", "python.exe")
    : path.join(projectRoot, ".venv", "bin", "python");
  if (fs.existsSync(venvPython)) return venvPython;
  return "python";
}

export async function POST(request) {
  try {
    const { prompt } = await request.json();
    if (!prompt || typeof prompt !== "string") {
      return Response.json(
        { success: false, error: "Prompt is required" },
        { status: 400 }
      );
    }

    const projectRoot = path.resolve(process.cwd(), "..");
    const pythonPath = getPythonPath(projectRoot);
    const proc = spawn(pythonPath, ["-m", "src.pipeline", "--json"], {
      cwd: projectRoot,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
      env: {
        ...process.env,
        COMIC_PROMPT_B64: Buffer.from(prompt, "utf-8").toString("base64"),
        PYTHONUNBUFFERED: "1",
        PYTHONIOENCODING: "utf-8",
      },
    });

    const stdout = [];
    const stderr = [];
    let stderrBuffer = "";

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        let finished = false;

        function safeEnqueue(bytes) {
          if (finished) return;
          try {
            controller.enqueue(bytes);
          } catch {
            finished = true;
          }
        }

        function emitLog(line) {
          if (finished) return;
          const trimmed = line.trim();
          if (trimmed) {
            safeEnqueue(
              encoder.encode(
                JSON.stringify({ t: "log", m: trimmed }) + "\n"
              )
            );
          }
        }

        function detachStdio() {
          try {
            proc.stderr?.removeAllListeners("data");
            proc.stdout?.removeAllListeners("data");
          } catch {
            /* ignore */
          }
        }

        function sendDone(payload) {
          if (finished) return;
          detachStdio();
          finished = true;
          try {
            controller.enqueue(
              encoder.encode(
                JSON.stringify({ t: "done", ...payload }) + "\n"
              )
            );
          } catch {
            /* stream may already be closing */
          }
          try {
            controller.close();
          } catch {
            /* ignore */
          }
        }

        proc.stdout.on("data", (chunk) => stdout.push(chunk));
        proc.stderr.on("data", (chunk) => {
          if (finished) return;
          stderr.push(chunk);
          stderrBuffer += chunk.toString("utf-8");
          const lines = stderrBuffer.split("\n");
          stderrBuffer = lines.pop() || "";
          lines.forEach(emitLog);
        });

        const timeoutId = setTimeout(() => {
          if (!proc.killed) proc.kill("SIGTERM");
        }, PIPELINE_TIMEOUT_MS);

        proc.on("close", (code) => {
          clearTimeout(timeoutId);
          if (finished) return;
          if (stderrBuffer.trim()) emitLog(stderrBuffer);
          const output = Buffer.concat(stdout).toString("utf-8");
          const errText = Buffer.concat(stderr).toString("utf-8");
          let data;
          try {
            data = JSON.parse(output);
          } catch {
            data = {
              success: false,
              error: errText || output || "Pipeline failed",
              logs: [],
            };
          }
          if (code !== 0 && data.success !== false) {
            data = { success: false, error: errText || "Pipeline failed", logs: [] };
          }
          sendDone(data);
        });

        proc.on("error", (err) => {
          clearTimeout(timeoutId);
          sendDone({
            success: false,
            error: err.message || "Process failed",
            logs: [],
          });
        });
      },
    });

    return new Response(stream, {
      headers: { "Content-Type": "application/x-ndjson" },
    });
  } catch (err) {
    return Response.json(
      { success: false, error: err.message || "Request failed", logs: [] },
      { status: 500 }
    );
  }
}
