// botWorker.pyw (rename as botWorker.js; it’s our worker script that loads Pyodide)

// Import Pyodide script (adjust URL as needed)
importScripts("https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.js");

let pyodideReady = false;
let pyodide = null;

// Load Pyodide and your engine code
async function initPyodide() {
  pyodide = await loadPyodide();
  // Now load your engine code from gobblet-engine/engine.py.
  // You can fetch it as text and then run it in Pyodide.
  const engineCode = await (await fetch("gobblet-engine/engine.py")).text();
  await pyodide.runPythonAsync(engineCode);
  pyodideReady = true;
}
initPyodide();

self.onmessage = async function(e) {
  const { state, timeLimit } = e.data;
  // Wait until Pyodide is ready
  while (!pyodideReady) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  // Prepare the Python command to run your iterative deepening function.
  // Assume your Python engine defines a function iterative_deepening(engine, time_limit)
  // and that you've also provided a way to convert the JSON state into your engine's state.
  // For example, you might have a function in your engine module like:
  //     get_best_move_from_json(json_state, time_limit)
  //
  // Here is an example command (adjust function names as needed):
  const command = `
import json
# Convert JSON state to a Python dictionary
state = json.loads("""${JSON.stringify(state)}""")
# Create an engine instance from the state; assume your engine module has a function for that.
engine = create_engine_from_state(state)
move = iterative_deepening(engine, ${timeLimit})
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
