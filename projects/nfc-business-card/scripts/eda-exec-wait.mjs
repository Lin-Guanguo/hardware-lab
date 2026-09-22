#!/usr/bin/env node
// Run an EasyEDA code file through the local bridge, waiting for a live window.
//
// The Run API Gateway extension reconnects on a roughly 16 s cycle and the
// bridge keeps stale registrations, so a request can land in a gap. This
// helper polls /eda-windows until a window is live, selects it, posts the code
// and retries a few times before giving up.
import fs from "node:fs";

const base = process.env.EDA_BRIDGE_BASE ?? "http://127.0.0.1:49620";
const codePath = process.argv[2];
const waitMs = Number(process.argv[3] ?? 120000);
if (!codePath) {
  console.error("usage: eda-exec-wait.mjs <code.js> [waitMs]");
  process.exit(2);
}
const code = fs.readFileSync(codePath, "utf8");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function liveWindow() {
  try {
    const res = await fetch(base + "/eda-windows");
    const json = await res.json();
    const live = (json.windows || []).filter((w) => w.connected !== false);
    if (!live.length) return null;
    const id = live.find((w) => w.windowId === json.activeWindowId)?.windowId ?? live[0].windowId;
    await fetch(base + "/eda-windows/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ windowId: id }),
    });
    return id;
  } catch {
    return null;
  }
}

async function execute() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  try {
    const res = await fetch(base + "/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
      signal: controller.signal,
    });
    return await res.text();
  } finally {
    clearTimeout(timer);
  }
}

const deadline = Date.now() + waitMs;
let attempt = 0;
while (Date.now() < deadline) {
  const wid = await liveWindow();
  if (wid) {
    attempt += 1;
    try {
      const text = await execute();
      if (text.includes('"success":true')) {
        console.log(text);
        process.exit(0);
      }
      console.error(`attempt ${attempt} on ${wid} failed: ${text.slice(0, 200)}`);
    } catch (error) {
      console.error(`attempt ${attempt} on ${wid} threw: ${String(error).slice(0, 120)}`);
    }
  } else {
    console.error(`no live window (attempt ${attempt})`);
  }
  await sleep(5000);
}
console.error("gave up waiting for a responsive EDA window");
process.exit(1);
