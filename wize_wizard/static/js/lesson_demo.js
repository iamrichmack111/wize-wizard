(() => {
  const root = document.querySelector('.browser-demo');
  if (!root) return;
  const visual = root.querySelector('.demo-visual');
  const message = root.querySelector('.demo-message');
  const play = root.querySelector('.demo-play');
  const reset = root.querySelector('.demo-reset');
  const kind = root.dataset.demo;
  let timer = null;
  const sequences = {
    why: [
      ['Need / Goal','I need to make money so that I can buy a car.'],
      ['WHY 1 → Wish','I need reliable transportation so that I can get to work.'],
      ['WHY 2 → Dream','I need to buy a house so that I can reduce rent.'],
      ['WHY 3 → Fantasy','I need financial freedom so that I can control my time.']
    ],
    pert: [['Best case','6 hours'],['Most likely','12 hours'],['Worst case','24 hours'],['Weighted planning view','Best + 4×Likely + Worst, divided by 6']],
    comms: [['Raw team','Everyone talks to everyone'],['Group the work','Put a supervisor inside each working group'],['Coordinate groups','Remainder people become coordination managers'],['Compare','Recalculate channels and span of control']],
    loop: [['Judgment','What decision are we making?'],['Logic','What must be true?'],['Computation','What does the model show?'],['Action','I need to ___ so that I can ___']],
    bcg: [['Relative position','Compare your share with the strongest rival'],['Experience','Ask whether repeated volume actually lowers unit cost'],['Cash','Ask whether position generates cash'],['Portfolio','Decide where scarce capital should go']],
    tree: [['Problem','Sales are declining'],['Branch 1','Market'],['Branch 2','Customer'],['Branch 3','Economics / Execution']],
    forces: [['Rivalry','Existing competitors'],['Entry','New entrants'],['Substitutes','Alternative ways to solve the job'],['Power','Suppliers + Buyers']],
    market: [['Step 1','Sort market shares'],['Four-Firm Concentration Ratio','Add the four largest shares'],['Herfindahl-Hirschman Index','Square every share, then add'],['Decision check','Concentration is not the same as profitability']],
    finance: [['Operating return','Return on Invested Capital'],['Financing hurdle','Weighted Average Cost of Capital'],['Compare','Return above cost → potential value creation'],['Do not stop','Check cash-flow assumptions and risk']],
    risk: [['One forecast','Hides the range'],['Add uncertainty','Define probabilities/distributions'],['Simulate','Repeat many possible outcomes'],['Read distribution','Inspect percentiles and failure probability']],
    flow: [['Find bottleneck','Identify the constraint'],['Use it well','Exploit the constraint'],['Align work','Subordinate other activities'],['Improve + repeat','Elevate, then find the next constraint']],
    integrated: [['Position','Market structure and rank'],['Economics','Price, synergies, return vs cost of capital'],['Response','Five Forces + competitor reaction'],['Risk + future','Monte Carlo + Three Horizons']]
  };
  const seq = sequences[kind] || sequences.loop;
  let i = 0;
  function draw() {
    const [title, body] = seq[i];
    message.innerHTML = `<b>${title}</b><span>${body}</span>`;
    visual.innerHTML = seq.map((x, idx) => `<div class="demo-node ${idx === i ? 'active' : idx < i ? 'done' : ''}"><b>${idx+1}</b><span>${x[0]}</span></div>`).join('<i>→</i>');
  }
  function stop(){ if(timer){ clearInterval(timer); timer=null; } play.textContent='▶ Play example'; }
  function start(){ stop(); play.textContent='⏸ Pause'; timer=setInterval(()=>{ i=(i+1)%seq.length; draw(); },1400); }
  play.addEventListener('click',()=> timer ? stop() : start());
  reset.addEventListener('click',()=>{ stop(); i=0; draw(); });
  draw();
})();
