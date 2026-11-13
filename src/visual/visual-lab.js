// Optional DOM tooling; no renderer/UI dependencies in the solar calculations.
if(new URLSearchParams(location.search).get('dev')==='lighting') {
  const panel=document.createElement('details');panel.id='visual-lab';panel.open=true;
  panel.style.cssText='position:fixed;right:12px;top:100px;z-index:1000;width:min(290px,85vw);max-height:75vh;overflow:auto;background:#19232ef2;color:white;padding:12px;border:1px solid #8899aa;border-radius:8px;font:14px system-ui';
  panel.innerHTML=`<summary>Visual Lab</summary>
    <label>Time <output id="lab-clock"></output><input id="lab-time" aria-label="Time" type="range" min="0" max="24" step=".01"></label>
    <label>Date <input id="lab-date" aria-label="Solar date" type="date" min="2020-01-01" max="2035-12-31"></label>
    <div id="lab-presets"></div><label><input id="lab-cycle" type="checkbox"> Run day cycle</label>
    <label>Profile <select id="lab-film"><option value="off">Original / Neutral</option><option value="chrome">Classic Chrome</option><option value="negative">Classic Negative</option><option value="gold">Kodak Gold inspired</option></select></label>
    <label>Streetlights <select id="lab-street"><option value="auto">Auto</option><option value="on">On</option><option value="off">Off</option></select></label>
    <label>Cloud coverage <input id="lab-cloud" type="range" min="0" max="1" step=".01" value=".5"></label>
    <label>Sun glare <input id="lab-glare" type="range" min="0" max="3" step=".05" value="3"></label>
    <label>Mist / diffusion <input id="lab-mist" type="range" min="0" max="1.5" step=".01"></label>
    <button id="lab-reset" type="button">Reset</button>`;
  const style=document.createElement('style');style.textContent='#visual-lab label{display:block;margin:10px 0}#visual-lab input[type=range]{display:block;width:100%}#visual-lab button,#visual-lab select{font:inherit;margin:3px;padding:5px}#visual-lab summary{cursor:pointer;font-weight:bold}';document.head.append(style);document.body.append(panel);
  // Stop bubbled keyboard events reaching gameplay; keyup still releases keys.
  panel.addEventListener('keydown',e=>e.stopPropagation());
  panel.addEventListener('pointerdown',()=>{for(const k in keys)keys[k]=false;joy.x=joy.y=0});
  for(const type of ['pointerdown','pointermove','pointerup','wheel'])panel.addEventListener(type,e=>e.stopPropagation());
  const el=id=>panel.querySelector('#lab-'+id);
  const clock=()=>{el('date').value=daylight.getDate();const h=daylight.getHour(),m=Math.round(h*60)%1440;el('clock').value=String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');el('time').value=h;el('cycle').checked=daylight.getCycle()};
  const apply=()=>{daylight.update(0);streetLighting.update(0,daylight.getHour(),daylight.getSolarElevation());clock()};
  el('time').oninput=e=>{daylight.setHour(+e.target.value);apply()};
  el('date').value=daylight.getDate();
  el('date').onchange=e=>{daylight.setDate(e.target.value);apply()};
  for(const hour of [13,17,19,20.5,22]){const b=document.createElement('button');b.type='button';b.textContent=hour===20.5?'20:30':hour+':00';b.onclick=()=>{daylight.setHour(hour);apply()};el('presets').append(b)}
  el('cycle').onchange=e=>daylight.setCycle(e.target.checked);
  el('film').value=filmQuery==='off'?'off':filmPresetName;
  el('film').onchange=e=>setFilmPreset(e.target.value);
  el('street').onchange=e=>{streetLighting.setMode(e.target.value);apply()};
  el('cloud').oninput=e=>{daylight.setCoverage(+e.target.value);apply()};
  el('glare').oninput=e=>{daylight.setGlare(+e.target.value);apply()};
  el('mist').value=filmMistStrength;el('mist').oninput=e=>{filmFrameMaterial.uniforms.uMist.value=+e.target.value};
  el('reset').onclick=()=>{daylight.reset();streetLighting.setMode('auto');setFilmPreset(filmQuery==='off'?'off':filmPresetName);filmFrameMaterial.uniforms.uMist.value=filmMistStrength;el('film').value=filmQuery==='off'?'off':filmPresetName;el('street').value='auto';el('cloud').value=daylightStateForLab();el('date').value=daylight.getDate();el('glare').value=3;el('mist').value=filmMistStrength;apply()};
  function daylightStateForLab(){return daylight.getCoverage()}
  el('cloud').value=daylightStateForLab();clock();setInterval(clock,250);
}
