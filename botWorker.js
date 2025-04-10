// botWorker.js
importScripts("https://cdn.jsdelivr.net/pyodide/v0.23.1/full/pyodide.js");

let pyodideReady = false;
let pyodide = null;

async function initPyodide() {
  pyodide = await loadPyodide();
  // Adjust the path below if necessary:
  const engineCode = await (await fetch("Gobbet-engine/engine.py")).text();
  await pyodide.runPythonAsync(engineCode);
  pyodideReady = true;
  console.log("Pyodide and engine loaded in worker.");
}
initPyodide();

self.onmessage = async function(e) {
  const { state, timeLimit } = e.data;
  while (!pyodideReady) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  // Construct the Python code to run
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
