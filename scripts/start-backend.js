const path = require("node:path");
const { spawn } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const port = Number.parseInt(process.env.BACKEND_PORT || "8002", 10);
const reloadEnabled = ["1", "true", "yes", "on"].includes(
  (process.env.BACKEND_RELOAD || "false").toLowerCase(),
);

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  console.error(`Invalid BACKEND_PORT: ${process.env.BACKEND_PORT}`);
  process.exit(1);
}

const python = process.platform === "win32"
  ? path.join(root, "backend", "venv", "Scripts", "python.exe")
  : path.join(root, "backend", "venv", "bin", "python");
const args = [
  "-m", "uvicorn",
  "main:app",
  "--port", String(port),
  "--app-dir", "backend",
];
if (reloadEnabled) args.push("--reload");

const child = spawn(python, args, {
  cwd: root,
  stdio: "inherit",
  windowsHide: false,
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.once(signal, () => child.kill(signal));
}

child.once("error", (error) => {
  console.error(`Failed to start backend: ${error.message}`);
  process.exitCode = 1;
});
child.once("exit", (code) => {
  process.exitCode = code ?? 1;
});
