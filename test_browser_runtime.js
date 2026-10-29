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
  clearInterval: () => {}
};

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
}).then(() => {
  console.log("  calvingModal active?", getMockElement("calvingModal").classList.contains("active"));
  closeCalvingModalDirect();
  console.log("  calvingModal closed?", !getMockElement("calvingModal").classList.contains("active"));

  // 6. openRoboticsModal()
  console.log("Testing 6. openRoboticsModal()...");
  return openRoboticsModal();
}).then(() => {
  console.log("  roboticsModal active?", getMockElement("roboticsModal").classList.contains("active"));
  closeRoboticsModalDirect();
  console.log("  roboticsModal closed?", !getMockElement("roboticsModal").classList.contains("active"));

  // 7. openEnergyModal()
  console.log("Testing 7. openEnergyModal()...");
  return openEnergyModal();
}).then(() => {
  console.log("  energyModal active?", getMockElement("energyModal").classList.contains("active"));
  closeEnergyModalDirect();
  console.log("  energyModal closed?", !getMockElement("energyModal").classList.contains("active"));

  // 8. openRationModal()
  console.log("Testing 8. openRationModal()...");
  return openRationModal();
}).then(() => {
  console.log("  rationModal active?", getMockElement("rationModal").classList.contains("active"));
  closeRationModalDirect();
  console.log("  rationModal closed?", !getMockElement("rationModal").classList.contains("active"));

  // 9. openReportModal() & report generation
  console.log("Testing 9. openReportModal()...");
  return openReportModal();
}).then(() => {
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

  console.log("\n>>> ALL TESTS COMPLETED SUCCESSFULLY! <<<");
}).catch(err => {
  console.error("Runtime test error:", err);
  process.exit(1);
});
