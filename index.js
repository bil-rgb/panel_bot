const { execSync, spawn } = require("child_process");

console.log("🤖 Panel Rename Bot - Starting...");

function run(cmd, opts = {}) {
  try {
    execSync(cmd, { stdio: "inherit", ...opts });
    return true;
  } catch (e) {
    return false;
  }
}

function checkPython() {
  try { execSync("python3 --version 2>&1"); return "python3"; } catch {}
  try { execSync("python --version 2>&1"); return "python"; } catch {}
  return null;
}

function setupVenv(py) {
  console.log("🔧 Membuat virtual environment...");
  run(`${py} -m venv /home/container/venv`);

  const venvPip = "/home/container/venv/bin/pip";

  console.log("📦 Install dependencies di venv...");
  run(`${venvPip} install --upgrade pip --quiet`);
  run(`${venvPip} install python-telegram-bot==21.6 aiohttp==3.9.5 aiofiles==23.2.1 python-dotenv==1.0.1 --quiet`);

  console.log("✅ Venv siap!");
  return "/home/container/venv/bin/python";
}

function runBot(py) {
  console.log("🚀 Menjalankan bot dengan:", py);
  const bot = spawn(py, ["bot.py"], {
    stdio: "inherit",
    env: process.env
  });

  bot.on("close", (code) => {
    console.log(`Bot berhenti (kode: ${code}), restart 5 detik...`);
    setTimeout(() => runBot(py), 5000);
  });

  bot.on("error", (err) => {
    console.error("❌ Error:", err.message);
    setTimeout(() => runBot(py), 5000);
  });
}

const py = checkPython();
if (!py) {
  console.error("❌ Python tidak ditemukan!");
  process.exit(1);
}
console.log("✅ Python ditemukan:", py);

const venvPy = setupVenv(py);
runBot(venvPy);
