document.addEventListener('DOMContentLoaded', () => {
  const diagPython = document.getElementById('diagPython');
  const diagSignals = document.getElementById('diagSignals');
  const diagAI = document.getElementById('diagAI');
  const diagPkgs = document.getElementById('diagPkgs');
  const btnTestSignals = document.getElementById('btnTestSignals');
  const signalsResultBox = document.getElementById('signalsResultBox');
  const btnTestAI = document.getElementById('btnTestAI');
  const promptInput = document.getElementById('promptInput');
  const aiResultBox = document.getElementById('aiResultBox');
  const specsContainer = document.getElementById('specsContainer');

  // 1. Fetch Health & Diagnostics
  async function loadHealth() {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      
      diagPython.textContent = 'Python ' + data.pythonVersion;
      diagSignals.innerHTML = data.signals.mockMode 
        ? '<span class="text-amber-400 font-semibold">Mock Mode (Offline)</span>' 
        : '<span class="text-emerald-400 font-semibold">Connected</span> <span class="text-slate-400 text-xs truncate">(' + data.signals.tenant + ')</span>';
      
      diagAI.innerHTML = '<span class="text-cyan-400 font-semibold">' + data.ai.model + '</span> <span class="text-slate-400 text-[11px]">(' + data.ai.provider + ')</span>';
      diagPkgs.textContent = data.installedPackages.length + ' Ready (' + data.installedPackages.slice(0, 4).join(', ') + '...)';
    } catch (err) {
      console.error(err);
      diagPython.textContent = 'Server starting...';
    }
  }

  // 2. Fetch OpenAPI Specs List
  async function loadSpecs() {
    try {
      const res = await fetch('/api/docs-list');
      const data = await res.json();
      specsContainer.innerHTML = '';
      
      (data.specs || []).forEach(spec => {
        const card = document.createElement('div');
        card.className = 'bg-slate-950 p-2.5 rounded-lg border border-slate-800 hover:border-brand-500 hover:bg-slate-900/80 transition cursor-pointer flex flex-col justify-between group';
        card.title = 'Click to view raw OpenAPI YAML specification';
        card.innerHTML = '<div class="flex items-center justify-between"><span class="text-[11px] font-bold text-white group-hover:text-brand-400 transition truncate">' + spec.name + '</span><span class="text-[9px] text-brand-500 font-mono opacity-0 group-hover:opacity-100 transition">↗</span></div>' +
          '<span class="text-[10px] text-slate-500 font-mono mt-1">' + spec.filename + '</span>' +
          '<span class="text-[9px] text-slate-600 mt-0.5">' + spec.sizeKb + ' KB</span>';
        card.addEventListener('click', () => {
          window.open('/api/docs/spec/' + spec.filename, '_blank');
        });
        specsContainer.appendChild(card);
      });
    } catch (err) {
      console.error(err);
      specsContainer.innerHTML = '<div class="text-xs text-rose-400 col-span-full">Failed to load specifications.</div>';
    }
  }

  // 3. Test Signals Connection
  btnTestSignals.addEventListener('click', async () => {
    btnTestSignals.disabled = true;
    btnTestSignals.textContent = 'Querying Signals...';
    signalsResultBox.innerHTML = '<span class="text-cyan-400">Sending GET /entities?filter[type]=experiment to Signals Notebook...</span>';

    try {
      const res = await fetch('/api/test-signals');
      const data = await res.json();
      
      if (data.status === 'success') {
        const exps = data.experiments || [];
        let html = '<div class="text-emerald-400 font-bold mb-2">Status: ' + (data.connection.status || 'OK').toUpperCase() + '</div>';
        html += '<div class="text-slate-400 mb-2">Retrieved ' + exps.length + ' experiment(s):</div>';
        html += '<ul class="space-y-1.5 pl-1">';
        exps.forEach(e => {
          html += '<li class="border-b border-slate-800 pb-1"><strong class="text-white">' + e.name + '</strong><br><span class="text-[10px] text-slate-500 font-mono">' + e.eid + '</span></li>';
        });
        html += '</ul>';
        signalsResultBox.innerHTML = html;
      } else {
        signalsResultBox.innerHTML = '<span class="text-rose-400">Error: ' + data.error + '</span>';
      }
    } catch (err) {
      signalsResultBox.innerHTML = '<span class="text-rose-400">Network error: ' + err.message + '</span>';
    } finally {
      btnTestSignals.disabled = false;
      btnTestSignals.textContent = 'Run Test Query';
    }
  });

  // 4. Test Gemini AI Synthesis
  btnTestAI.addEventListener('click', async () => {
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    btnTestAI.disabled = true;
    btnTestAI.textContent = 'Summarizing Portfolio...';
    aiResultBox.innerHTML = '<span class="text-cyan-400">Synthesizing Signals Notebook portfolio with Gemini 3.6 Flash...</span>';

    try {
      const res = await fetch('/api/test-ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, include_experiments: true })
      });
      const data = await res.json();
      
      if (data.status === 'success') {
        const r = data.result;
        let html = '<div class="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-2">';
        html += '<span class="text-[10px] bg-slate-800 text-cyan-300 font-mono px-2 py-0.5 rounded">' + r.source + '</span>';
        html += '</div>';
        html += '<div class="text-slate-200 whitespace-pre-wrap leading-relaxed">' + r.text + '</div>';
        aiResultBox.innerHTML = html;
      } else {
        aiResultBox.innerHTML = '<span class="text-rose-400">AI Error: ' + data.detail + '</span>';
      }
    } catch (err) {
      aiResultBox.innerHTML = '<span class="text-rose-400">Network error: ' + err.message + '</span>';
    } finally {
      btnTestAI.disabled = false;
      btnTestAI.textContent = '✨ Summarize Lab Data';
    }
  });

  loadHealth();
  loadSpecs();
});