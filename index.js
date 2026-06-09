const { execSync, spawn } = require("child_process");

console.log("🤖 Panel Rename Bot - Starting...");

function run(cmd) {
  try { execSync(cmd, { stdio: "inherit" }); return true; }
  catch (e) { return false; }
}

function checkPython() {
  try { execSync("python3 --version 2>&1"); return "python3"; } catch {}
  try { execSync("python --version 2>&1"); return "python"; } catch {}
  return null;
}

function installDeps(py) {
  console.log("📦 Install pip dulu...");
  run(`${py} -m ensurepip --upgrade`) ||
  run(`curl -sS https://bootstrap.pypa.io/get-pip.py | ${py}`) ||
  run(`wget -qO- https://bootstrap.pypa.io/get-pip.py | ${py}`);

  console.log("📦 Install dependencies...");
  run(`${py} -m pip install -r requirements.txt --quiet`) ||
  run(`${py} -m pip install -r requirements.txt --quiet --break-system-packages`) ||
  run(`${py} -m pip install python-telegram-bot==21.6 aiohttp==3.9.5 aiofiles==23.2.1 python-dotenv==1.0.1 --quiet --break-system-packages`);

  console.log("✅ Dependencies siap!");
}

function runBot(py) {
  console.log("🚀 Menjalankan bot...");
  const bot = spawn(py, ["bot.py"], { stdio: "inherit", env: process.env });

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
if (!py) { console.error("❌ Python tidak ditemukan!"); process.exit(1); }
console.log("✅ Python:", py);

installDeps(py);
runBot(py);
