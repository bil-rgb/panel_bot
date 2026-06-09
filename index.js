const { execSync, spawn } = require("child_process");
const fs = require("fs");

console.log("🤖 Panel Rename Bot - Starting...");

// Cek apakah python3 tersedia
function checkPython() {
  try {
    const ver = execSync("python3 --version 2>&1").toString().trim();
    console.log("✅ Python ditemukan:", ver);
    return "python3";
  } catch {}
  try {
    const ver = execSync("python --version 2>&1").toString().trim();
    console.log("✅ Python ditemukan:", ver);
    return "python";
  } catch {}
  return null;
}

// Install pip packages
function installDeps(pythonCmd) {
  console.log("📦 Menginstall dependencies...");
  try {
    execSync(`${pythonCmd} -m pip install -r requirements.txt --quiet`, {
      stdio: "inherit",
    });
    console.log("✅ Dependencies terinstall!");
  } catch (e) {
    console.error("❌ Gagal install dependencies:", e.message);
    process.exit(1);
  }
}

// Jalankan bot
function runBot(pythonCmd) {
  console.log("🚀 Menjalankan bot...");

  const env = {
    ...process.env,
  };

  const bot = spawn(pythonCmd, ["bot.py"], {
    stdio: "inherit",
    env: env,
  });

  bot.on("close", (code) => {
    console.log(`Bot berhenti dengan kode: ${code}`);
    console.log("🔄 Restart dalam 5 detik...");
    setTimeout(() => runBot(pythonCmd), 5000);
  });

  bot.on("error", (err) => {
    console.error("❌ Error:", err.message);
    setTimeout(() => runBot(pythonCmd), 5000);
  });
}

// Main
const pythonCmd = checkPython();
if (!pythonCmd) {
  console.error("❌ Python tidak ditemukan di server ini!");
  process.exit(1);
}

installDeps(pythonCmd);
runBot(pythonCmd);
