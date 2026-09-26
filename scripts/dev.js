const http = require("node:http");
const net = require("node:net");
const path = require("node:path");
const { execFileSync, spawn } = require("node:child_process");

const root = path.resolve(__dirname, "..");

function isListening(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "127.0.0.1", port });
    const finish = (value) => {
      socket.removeAllListeners();
      socket.destroy();
      resolve(value);
    };
    socket.setTimeout(500);
    socket.once("connect", () => finish(true));
    socket.once("timeout", () => finish(false));
    socket.once("error", () => finish(false));
  });
}

function httpMatches(url, predicate, timeout = 1500) {
  return new Promise((resolve) => {
    const request = http.get(url, { timeout }, (response) => {
      let body = "";
      response.setEncoding("utf8");
      response.on("data", (chunk) => {
        if (body.length < 65536) body += chunk;
      });
      response.on("end", () => resolve(response.statusCode === 200 && predicate(body, response)));
    });
    request.once("timeout", () => {
      request.destroy();
      resolve(false);
    });
    request.once("error", () => resolve(false));
  });
}

function windowsOwner(port) {
  if (process.platform !== "win32") return "";
  const command = [
    `$connection = Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1`,
    "if ($connection) {",
    "  $process = Get-CimInstance Win32_Process -Filter \"ProcessId=$($connection.OwningProcess)\"",
    "  Write-Output \"PID $($connection.OwningProcess) ($($process.Name)): $($process.CommandLine)\"",
    "}",
  ].join("; ");
  try {
    return execFileSync("powershell.exe", ["-NoProfile", "-Command", command], {
      encoding: "utf8",
      windowsHide: true,
    }).trim();
  } catch {
    return "";
  }
}

async function preflight() {
  const frontendBusy = await isListening(3000);
  const backendBusy = await isListening(8001);
  const ollamaBusy = await isListening(11434);
  const reuseFrontend = frontendBusy && await httpMatches(
    "http://127.0.0.1:3000",
    (body) => body.includes("Wissen") && body.includes("__next"),
  );
  const reuseBackend = backendBusy && await httpMatches(
    "http://127.0.0.1:8001/api/health",
    (body) => {
      try {
        const result = JSON.parse(body);
        return result.status === "healthy" && result.knowledge_base && result.ollama;
      } catch {
        return false;
      }
    },
    6000,
  );
  const reuseOllama = ollamaBusy && await httpMatches(
    "http://127.0.0.1:11434/api/version",
    (body) => {
      try {
        return Boolean(JSON.parse(body).version);
      } catch {
        return false;
      }
    },
  );

  const conflicts = [];
  if (frontendBusy && !reuseFrontend) conflicts.push({ port: 3000, service: "frontend", owner: windowsOwner(3000) });
  if (backendBusy && !reuseBackend) conflicts.push({ port: 8001, service: "backend", owner: windowsOwner(8001) });

  if (conflicts.length) {
    console.error("\nStartup preflight failed. Required application ports are already in use:\n");
    for (const conflict of conflicts) {
      console.error(`  - ${conflict.service}: http://127.0.0.1:${conflict.port}`);
      if (conflict.owner) console.error(`    ${conflict.owner}`);
    }
    console.error("\nStop the stale process, or keep using the already-running application. No services were started.\n");
    process.exitCode = 1;
    return null;
  }

  if (ollamaBusy && !reuseOllama) {
    console.error("\nStartup preflight failed: port 11434 is occupied by a service that is not Ollama.");
    const owner = windowsOwner(11434);
    if (owner) console.error(`  ${owner}`);
    console.error("No services were started.\n");
    process.exitCode = 1;
    return null;
  }

  return { reuseFrontend, reuseBackend, reuseOllama };
}

async function main() {
  const result = await preflight();
  if (!result) return;

  const reused = [
    result.reuseOllama && "Ollama",
    result.reuseBackend && "backend",
    result.reuseFrontend && "frontend",
  ].filter(Boolean);
  console.log(reused.length
    ? `Startup preflight passed. Reusing healthy services: ${reused.join(", ")}.`
    : "Startup preflight passed. Ollama, backend, and frontend ports are available.");

  if (process.argv.includes("--check")) return;

  const services = [
    !result.reuseOllama && { name: "OLLAMA", color: "green.bold", command: "npm run dev:ollama" },
    !result.reuseBackend && { name: "BACKEND", color: "blue.bold", command: "npm run dev:backend" },
    !result.reuseFrontend && { name: "FRONTEND", color: "magenta.bold", command: "npm run dev:frontend" },
  ].filter(Boolean);
  if (!services.length) {
    console.log("All development services are already running. Nothing new was started.");
    return;
  }

  const commands = services.map((service) => service.command);
  const names = services.map((service) => service.name).join(",");
  const colors = services.map((service) => service.color).join(",");
  const concurrentlyCli = path.join(root, "node_modules", "concurrently", "dist", "bin", "concurrently.js");
  const child = spawn(process.execPath, [concurrentlyCli, "-k", "-p", "[{name}]", "-n", names, "-c", colors, ...commands], {
    cwd: root,
    stdio: "inherit",
    windowsHide: false,
  });

  child.once("error", (error) => {
    console.error(`Failed to start development services: ${error.message}`);
    process.exitCode = 1;
  });
  child.once("exit", (code) => {
    process.exitCode = code ?? 1;
  });
}

main().catch((error) => {
  console.error(`Startup failed: ${error.stack || error.message}`);
  process.exitCode = 1;
});
