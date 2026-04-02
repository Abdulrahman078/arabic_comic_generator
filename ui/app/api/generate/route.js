import { spawn } from "child_process";
import path from "path";
import fs from "fs";

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
      },
    });

    const stdout = [];
    const stderr = [];
    let stderrBuffer = "";

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        function emitLog(line) {
          const trimmed = line.trim();
          if (trimmed) {
            controller.enqueue(encoder.encode(JSON.stringify({ t: "log", m: trimmed }) + "\n"));
          }
        }

        proc.stdout.on("data", (chunk) => stdout.push(chunk));
        proc.stderr.on("data", (chunk) => {
          stderr.push(chunk);
          stderrBuffer += chunk.toString("utf-8");
          const lines = stderrBuffer.split("\n");
          stderrBuffer = lines.pop() || "";
          lines.forEach(emitLog);
        });

        const TIMEOUT_MS = 5 * 60 * 1000;
        const timeoutId = setTimeout(() => {
          if (!proc.killed) proc.kill("SIGTERM");
        }, TIMEOUT_MS);

        proc.on("close", (code) => {
          clearTimeout(timeoutId);
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
          controller.enqueue(encoder.encode(JSON.stringify({ t: "done", ...data }) + "\n"));
          controller.close();
        });
        proc.on("error", (err) => {
          clearTimeout(timeoutId);
          controller.enqueue(
            encoder.encode(
              JSON.stringify({
                t: "done",
                success: false,
                error: err.message || "Process failed",
                logs: [],
              }) + "\n"
            )
          );
          controller.close();
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
