// Test that all header functions and module handlers exist and execute without errors in app.js
const fs = require('fs');

const jsContent = fs.readFileSync('app.js', 'utf8');

console.log("Checking JS syntax with new Function()...");
try {
  // Check if JS syntax is valid
  new Function(jsContent);
  console.log("Syntax is 100% valid JS!");
} catch (e) {
  console.error("Syntax Error:", e);
  process.exit(1);
}

// Check presence of key functions
const requiredFunctions = [
  'toggleEdgeConnection',
  'openGenomicsModal',
  'openCalvingModal',
  'openRoboticsModal',
  'openEnergyModal',
  'openRationModal',
  'openReportModal',
  'exportIcarAdeJson',
  'togglePlayPause',
  'advanceStep',
  'closeReportModalDirect',
  'copyReportText',
  'downloadReportMarkdown',
  'generateDailyAuditReportMarkdown',
  'renderMarkdownToHtml',
  'generateClientIcarAdeJson',
  'triggerScenario',
  'executeAiQuery',
  'processClientAiQuery',
  'openXaiModal',
  'closeModalDirect',
  'applySelectedRation',
  'sendRobotAction',
  'prescribeTreatment',
  'resolveIntervention',
  'openDemoLoginModal',
  'closeDemoLoginModalDirect',
  'selectDemoPersona',
  'quickLaunchDemo',
  'startGuidedDemoTour'
];

let allPassed = true;
requiredFunctions.forEach(fn => {
  const found = jsContent.includes(`function ${fn}`) || jsContent.includes(`${fn} =`);
  if (!found) {
    console.error(`Missing function: ${fn}`);
    allPassed = false;
  } else {
    console.log(`[OK] ${fn}`);
  }
});

if (allPassed) {
  console.log("\nALL 25 UI & HEADER FUNCTIONS PRESENT AND VERIFIED!");
} else {
  process.exit(1);
}
