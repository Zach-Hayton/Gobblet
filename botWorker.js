// botWorker.js
importScripts("https://cdn.jsdelivr.net/pyodide/v0.23.1/full/pyodide.js");

let pyodideReady = false;
let pyodide = null;
let currentEngineFile = null;  // keep track of which engine is loaded

async function initPyodide() {
  pyodide = await loadPyodide();
  // Initially load the default engine.
  const engineCode = await (await fetch("Gobbet-engine/engine.py")).text();
  await pyodide.runPythonAsync(engineCode);
  currentEngineFile = "engine.py";
  pyodideReady = true;
  console.log("Pyodide and initial engine loaded in worker.");
}
initPyodide();

self.onmessage = async function(e) {
  const { state, timeLimit, engineFile } = e.data;
  while (!pyodideReady) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  // If a new engine file is requested, load it.
  if (engineFile && engineFile !== currentEngineFile) {
    try {
      const newEngineCode = await (await fetch("Gobbet-engine/" + engineFile)).text();
      await pyodide.runPythonAsync(newEngineCode);
      currentEngineFile = engineFile;
      console.log("Loaded new engine file:", engineFile);
    } catch(err) {
      self.postMessage({ error: "Failed to load engine file: " + err.toString() });
      return;
    }
  }
  
  // Construct the Python command.
  const command = `
import json
state = json.loads('${JSON.stringify(state)}')
engine = create_engine_from_state(state)
move = get_move(engine, ${timeLimit})
json.dumps(move)
`;
  try {
    let resultJson = await pyodide.runPythonAsync(command);
    const result = JSON.parse(resultJson);
    self.postMessage({ move: result });
  } catch (error) {
    self.postMessage({ error: error.toString() });
  }
};
