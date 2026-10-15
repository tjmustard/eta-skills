/* EXAMPLE of the page-side shim that capture.mjs expects. It is NOT portable:
   every identifier below that is not on `window` (qManual, qLocked, playing,
   Voice, SCENES, idx, showScene, elapsed, clock, tick, fade) is a global of the
   ORIGINAL page this was written for. Rewrite the body for your page; keep the
   contract:

     window.__setup()  -> {total, scenes, durs}
         stop the live animation loop and any auto quality scaling, silence
         audio, build window.__starts (scene start times, seconds), and
         replace requestAnimationFrame so nothing renders on its own.
     window.__seek(t, fps)
         put the page into the exact state for film time t (seconds) and
         render ONE frame synchronously. Same t must give the same picture.
         Drive the page's clock with a fixed step 1/fps, not wall time.

   The cut handling below fades to black over 0.22 s at every scene boundary;
   check_cuts.py relies on the page doing something visible at each cut. */
window.__setup=function(){
  qManual=true; qLocked=true; playing=false;          // no auto quality demotion
  if(window.Voice){ Voice.on=false; try{Voice.stop();}catch(e){} }

  window.__starts=[]; let a=0;
  for(const s of SCENES){ window.__starts.push(a); a+=s.dur; }
  window.__total=a;

  // `fade` is a top-level const in the page script: a bare identifier, not
  // a property of window, and the element carries no id
  const fadeEl=(typeof fade!=='undefined')?fade:null;
  if(fadeEl) fadeEl.style.transition='none';

  window.__seek=function(gt,fps){
    let i=0;
    while(i<SCENES.length-1 && gt>=window.__starts[i]+SCENES[i].dur) i++;
    if(i!==idx){ idx=i; showScene(i); }
    elapsed=Math.min(Math.max(gt-window.__starts[i],0),SCENES[i].dur);
    clock.elapsedTime=gt;                              // scene time t
    clock.getDelta=()=>1/(fps||30);                    // fixed step
    // short dip to black across every cut
    const d=SCENES[i].dur, e=elapsed, F=0.22;
    let op=0;
    if(i>0 && e<F) op=1-e/F;
    else if(i<SCENES.length-1 && e>d-F) op=1-(d-e)/F;
    if(fadeEl) fadeEl.style.opacity=String(op);
    tick();                                            // renders exactly once
  };

  window.requestAnimationFrame=()=>0;                  // stop the live loop
  return {total:a, scenes:SCENES.length, durs:SCENES.map(s=>s.dur)};
};
