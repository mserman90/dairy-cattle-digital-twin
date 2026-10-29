// Comprehensive runtime verification of all UI header buttons and modules in Node environment
const fs = require('fs');
const vm = require('vm');

// Create mock DOM elements
const mockElements = {};
function getMockElement(id) {
  if (!mockElements[id]) {
    mockElements[id] = {
      id: id,
      classList: {
        classes: new Set(),
        add(c) { this.classes.add(c); },
        remove(c) { this.classes.delete(c); },
        contains(c) { return this.classes.has(c); },
        toggle(c) { if (this.contains(c)) this.remove(c); else this.add(c); }
      },
      textContent: '',
      innerHTML: '',
      style: {},
      setAttribute(k, v) { this[k] = v; },
      getAttribute(k) { return this[k]; },
      dataset: {},
      value: '',
      appendChild: () => {},
      removeChild: () => {},
      addEventListener: () => {}
    };
  }
  return mockElements[id];
}

global.document = {
  getElementById: (id) => getMockElement(id),
  querySelectorAll: (selector) => [],
  querySelector: (selector) => null,
  addEventListener: (event, cb) => {},
  createElement: (tag) => ({
    tagName: tag.toUpperCase(),
    style: {},
    classList: { add() {}, remove() {} },
    appendChild() {},
    removeChild() {},
    setAttribute() {},
    addEventListener() {}
  }),
  body: { appendChild() {}, removeChild() {} }
};

global.window = {
  addEventListener: (event, cb) => {},
  setInterval: () => {},
  clearInterval: () => {},
  alert: (msg) => {}
};
global.alert = (msg) => {};

const storageMap = new Map();
global.localStorage = {
  getItem: (k) => storageMap.has(k) ? storageMap.get(k) : null,
  setItem: (k, v) => storageMap.set(k, String(v)),
  removeItem: (k) => storageMap.delete(k),
  clear: () => storageMap.clear()
};
global.window.localStorage = global.localStorage;

global.fetch = () => Promise.reject(new Error("Simulating Offline/GitHub Pages static mode"));
global.navigator = { clipboard: { writeText: () => Promise.resolve() } };
global.URL = { createObjectURL: () => 'blob:mock', revokeObjectURL: () => {} };
global.Blob = function(parts, opts) { this.parts = parts; this.opts = opts; };

// Load and evaluate app.js
const code = fs.readFileSync('app.js', 'utf8');
vm.runInThisContext(code);

console.log("=== VERIFYING HEADER ACTION BUTTONS & CLIENT FALLBACKS ===");

// 1. toggleEdgeConnection()
console.log("Testing 1. toggleEdgeConnection()...");
toggleEdgeConnection();
console.log("  Edge dot classes:", Array.from(getMockElement("edgeDot").classList.classes));
console.log("  Edge status text:", getMockElement("edgeStatusLabel").textContent);

// 2. togglePlayPause()
console.log("Testing 2. togglePlayPause()...");
togglePlayPause();
console.log("  Play text:", getMockElement("playText").textContent);
togglePlayPause();
console.log("  Play text after toggle back:", getMockElement("playText").textContent);

// 3. advanceStep()
console.log("Testing 3. advanceStep()...");
advanceStep();
console.log("  Step advanced, clientSimState tick:", clientSimState.simulation_tick);

// 4. openGenomicsModal()
console.log("Testing 4. openGenomicsModal()...");
openGenomicsModal().then(() => {
  console.log("  genomicsModal active?", getMockElement("genomicsModal").classList.contains("active"));
  closeGenomicsModalDirect();
  console.log("  genomicsModal closed?", !getMockElement("genomicsModal").classList.contains("active"));

  // 5. openCalvingModal()
  console.log("Testing 5. openCalvingModal()...");
  return openCalvingModal();
}).then(async () => {
  console.log("  calvingModal active?", getMockElement("calvingModal").classList.contains("active"));
  closeCalvingModalDirect();
  console.log("  calvingModal closed?", !getMockElement("calvingModal").classList.contains("active"));

  // 6. openRoboticsModal()
  console.log("Testing 6. openRoboticsModal()...");
  return openRoboticsModal();
}).then(async () => {
  console.log("  roboticsModal active?", getMockElement("roboticsModal").classList.contains("active"));
  closeRoboticsModalDirect();
  console.log("  roboticsModal closed?", !getMockElement("roboticsModal").classList.contains("active"));

  // 7. openEnergyModal()
  console.log("Testing 7. openEnergyModal()...");
  return openEnergyModal();
}).then(async () => {
  console.log("  energyModal active?", getMockElement("energyModal").classList.contains("active"));
  closeEnergyModalDirect();
  console.log("  energyModal closed?", !getMockElement("energyModal").classList.contains("active"));

  // 8. openRationModal()
  console.log("Testing 8. openRationModal()...");
  return openRationModal();
}).then(async () => {
  console.log("  rationModal active?", getMockElement("rationModal").classList.contains("active"));
  closeRationModalDirect();
  console.log("  rationModal closed?", !getMockElement("rationModal").classList.contains("active"));

  // 9. openReportModal() & report generation
  console.log("Testing 9. openReportModal()...");
  return openReportModal();
}).then(async () => {
  console.log("  reportModal active?", getMockElement("reportModal").classList.contains("active"));
  const reportMd = generateDailyAuditReportMarkdown();
  console.log("  Generated Report length:", reportMd.length, "characters");
  console.log("  Generated Report includes # 📋 AGRITWIN?", reportMd.includes("# 📋 AGRITWIN"));
  const renderedHtml = renderMarkdownToHtml(reportMd);
  console.log("  Rendered HTML includes <table>?", renderedHtml.includes("<table>"));
  closeReportModalDirect();

  // 10. exportIcarAdeJson()
  console.log("Testing 10. exportIcarAdeJson()...");
  const ade = generateClientIcarAdeJson();
  console.log("  ICAR ADE Document ID:", ade.header.document_id);
  console.log("  ICAR ADE Records Count:", ade.records.length);
  console.log("  ICAR ADE Spec Version:", ade.header.specification_version);

  // 11. Scenarios
  console.log("Testing 11. Scenarios (dystocia, mastitis, reset)...");
  triggerScenario("dystocia");
  console.log("  Dystocia active scenario:", clientSimState.active_scenario);
  console.log("  Gate status:", clientSimState.sorting_gate.status);
  triggerScenario("reset");
  console.log("  Reset active scenario:", clientSimState.active_scenario);

  // 12. AI Danışman Client Fallback
  console.log("Testing 12. AI Danışman NLP queries...");
  const queries = [
    "doğumhane ve distosi durumu nedir?",
    "kolostrum brix ve fpt analizi",
    "genomik eşleştirme ve boğa önerisi",
    "robot filosu durumu",
    "biyogaz enerji üretimi ve chp",
    "finansal roi ve süt geliri"
  ];
  queries.forEach(q => {
    const ans = processClientAiQuery(q);
    console.log(`  AI Danışman query '${q}': answered (${ans.length} chars)`);
  });

  // 13. Animal XAI Detail Modal & Veterinary actions
  console.log("Testing 13. Animal XAI Modal & Veterinary Actions...");
  currentFarmState = clientSimState;
  openXaiModal("TR-34-102");
  console.log("  xaiModal active?", getMockElement("xaiModal").classList.contains("active"));
  prescribeTreatment();
  console.log("  Prescription executed, active treatments:", clientSimState.edge_gateway.active_treatments.length);
  closeModalDirect();
  console.log("  xaiModal closed?", !getMockElement("xaiModal").classList.contains("active"));

  // 14. Demo User Personas & Persona Switch
  console.log("Testing 14. Demo User Personas & Persona Switching...");
  openDemoLoginModal();
  console.log("  demoLoginModal active?", getMockElement("demoLoginModal").classList.contains("active"));
  selectDemoPersona("manager");
  console.log("  Active persona after switch to manager:", currentDemoPersona.name, `(${currentDemoPersona.role})`);
  const mgrAiAns = processClientAiQuery("finansal roi ve süt geliri");
  console.log("  AI answer greets manager?", mgrAiAns.includes("Selim Aksoy"));
  selectDemoPersona("energy");
  console.log("  Active persona after switch to energy:", currentDemoPersona.name);
  selectDemoPersona("vet");
  console.log("  Active persona reset to vet:", currentDemoPersona.name);
  closeDemoLoginModalDirect();
  console.log("  demoLoginModal closed?", !getMockElement("demoLoginModal").classList.contains("active"));

  // 15. Dynamic Mock Sensor Stream Oscillation
  console.log("Testing 15. Dynamic Mock Sensor Stream Oscillation...");
  const initialTick = clientSimState.simulation_tick;
  const initialPusherHeight = clientSimState.robotics.pusher.feed_height_sensor_cm;
  runClientTick();
  runClientTick();
  console.log("  Tick advanced from", initialTick, "to", clientSimState.simulation_tick);
  console.log("  Feed height sensor dynamically updated:", clientSimState.robotics.pusher.feed_height_sensor_cm, "cm");
  console.log("  Discovery manure tank fill pct:", clientSimState.robotics.collector.tank_fill_pct, "%");
  console.log("  Cow 1 rumen pH:", clientSimState.animals[0].rumen.telemetry.rumen_ph);
  console.log("  Cow 1 body temp:", clientSimState.animals[0].telemetry.body_temperature_c, "°C");

  // 16. Quick Launch Demo & Tour
  console.log("Testing 16. Quick Launch Demo & Guided Tour...");
  startGuidedDemoTour();
  console.log("  Tour launched, AI response updated?", getMockElement("aiChatResponse").innerHTML.includes("AgriTwin Rehberli Demo Turu"));
  quickLaunchDemo("ration");

  // 17. Farm Devices Fleet Modal & Actuators
  console.log("Testing 17. Farm Devices Fleet Modal & Actuator Actions...");
  openDevicesModal();
  console.log("  devicesModal active?", getMockElement("devicesModal").classList.contains("active"));
  filterDeviceCategory("ROBOTICS");
  sendDeviceAction("DEV-PUSHER-01", "ROTATE_AUGER");
  sendDeviceAction("DEV-AMS-01", "STEAM_CLEAN");
  sendDeviceAction("DEV-MISTING-SYS", "PULSE_MIST");
  closeDevicesModalDirect();
  console.log("  devicesModal closed?", !getMockElement("devicesModal").classList.contains("active"));

  // 18. Authentication Engine (User Registration & Login & Session)
  console.log("Testing 18. Authentication Engine (Register, Login, Session, Tabs)...");
  openAuthModal("login");
  console.log("  authModal active?", getMockElement("demoLoginModal").classList.contains("active"));
  switchAuthTab("register");
  switchAuthTab("demo");
  switchAuthTab("login");
  fillDemoCredentials("manager");
  console.log("  Login username filled:", getMockElement("loginUsername").value);
  await submitLoginForm();
  console.log("  Current logged-in user:", currentUser ? currentUser.full_name : "none");
  console.log("  Header user name updated:", getMockElement("demoUserName").textContent);
  await logoutUser();
  console.log("  User logged out, active name:", getMockElement("demoUserName").textContent);
  closeAuthModalDirect();
  console.log("  authModal closed?", !getMockElement("demoLoginModal").classList.contains("active"));

  console.log("\n>>> ALL TESTS COMPLETED SUCCESSFULLY! <<<");
}).catch(err => {
  console.error("Runtime test error:", err);
  process.exit(1);
});
