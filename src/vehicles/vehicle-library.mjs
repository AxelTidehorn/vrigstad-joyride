/**
 * Standalone low-poly vehicle models for Vrigstad Joyride.
 * Front is -Z, +Y is up. Geometry is cached by model and paint.
 * Deliberately independent of the game simulation.
 */
export const VEHICLES = Object.freeze({
  volvo240: {name:"Volvo 240",paint:"#c7bda4"},
  newHollandT6: {name:"New Holland T6",paint:"#2375b5"},
  johnDeere6M: {name:"John Deere 6M",paint:"#3e8831"}
});
const COLORS={tyre:"#202426",glass:"#263c47",black:"#1a2224",silver:"#b1b8b6",rear:"#ac3432",amber:"#d99b48",lamp:"#dce0d8"};
const rgb=h=>{const x=h.replace("#","");return [0,2,4].map(i=>parseInt(x.slice(i,i+2),16)/255)};
class Builder{
 constructor(){this.position=[];this.normal=[];this.color=[]}
 tri(a,b,c,color){
  let u=b.map((v,i)=>v-a[i]),v=c.map((x,i)=>x-a[i]);
  let n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
  const len=Math.hypot(...n);if(len<1e-8)return;n=n.map(x=>x/len);
  for(const p of [a,b,c]){this.position.push(...p);this.normal.push(...n);this.color.push(...rgb(color))}
 }
 quad(a,b,c,d,color){this.tri(a,b,c,color);this.tri(a,c,d,color)}
 poly(pts,color){for(let i=1;i<pts.length-1;i++)this.tri(pts[0],pts[i],pts[i+1],color)}
 box(x,y,z,w,h,l,color){
  const a=x-w/2,b=x+w/2,c=y-h/2,d=y+h/2,e=z-l/2,f=z+l/2;
  this.quad([a,c,e],[b,c,e],[b,d,e],[a,d,e],color);
  this.quad([b,c,f],[a,c,f],[a,d,f],[b,d,f],color);
  this.quad([a,c,f],[a,c,e],[a,d,e],[a,d,f],color);
  this.quad([b,c,e],[b,c,f],[b,d,f],[b,d,e],color);
  this.quad([a,d,e],[b,d,e],[b,d,f],[a,d,f],color);
  this.quad([a,c,f],[b,c,f],[b,c,e],[a,c,e],color);
 }
 lineOnSide(x,y1,z1,y2,z2,color,width=.016){
  this.quad([x,y1,z1-width],[x,y1,z1+width],[x,y2,z2+width],[x,y2,z2-width],color)
 }
 wheel(x,y,z,r,w,rim){
  const s=Math.sign(x),N=18,inner=x-s*w/2,outer=x+s*w/2;
  const ring=(at,rad)=>Array.from({length:N},(_,i)=>[at,y+rad*Math.sin(i*2*Math.PI/N),z+rad*Math.cos(i*2*Math.PI/N)]);
  const A=ring(inner,r),B=ring(outer,r);
  for(let i=0;i<N;i++)this.quad(A[i],A[(i+1)%N],B[(i+1)%N],B[i],COLORS.tyre);
  this.poly(B,COLORS.tyre);this.poly(ring(outer+s*.01,r*.64),rim);
  this.poly(ring(outer+s*.018,r*.28),COLORS.silver);
 }
}
function volvo(G,paint){
 const front=-2.35,rear=2.35,fy=.36,fr=-1.43,rr=1.22;
 // Continuous wheel-arch-aware side panels, rather than intersecting boxes.
 const zs=[front,-2.18,-1.91,-.98,-.58,.25,1.13,1.55,1.9,2.18,rear];
 for(const zc of [fr,rr])for(let i=0;i<=16;i++)zs.push(zc-.415+i*.83/16);
 zs.sort((a,b)=>a-b);
 const top=z=>z<-.98?.94+(z+2.35)*.067:z>1.55?1.03-(z-1.55)*.052:1.032;
 const bot=z=>{let h=.355;for(const c of [fr,rr]){const dx=Math.abs(z-c);if(dx<.415)h=Math.max(h,fy+Math.sqrt(.415*.415-dx*dx))}return h};
 for(const s of [-1,1])for(let i=1;i<zs.length;i++){
  const a=zs[i-1],b=zs[i];if(b-a<.0001)continue;
  G.quad([s*.81,bot(a),a],[s*.81,bot(b),b],[s*.845,.905,b],[s*.845,.905,a],paint);
  G.quad([s*.845,.905,a],[s*.845,.905,b],[s*.785,top(b),b],[s*.785,top(a),a],paint);
 }
 const deck=(z1,z2)=>{G.quad([-.785,top(z1),z1],[.785,top(z1),z1],[.785,top(z2),z2],[-.785,top(z2),z2],paint)};
 deck(front,-.98);deck(1.55,rear);
 G.box(0,.47,0,1.59,.18,4.55,paint);
 for(const s of [-1,1]){
  const a=s*.756,b=s*.67;
  // Two tall rectangular door windows with a narrow central pillar.
  G.quad([a,1.055,-.93],[a,1.055,.255],[b,1.395,.255],[b,1.395,-.59],COLORS.black);
  G.quad([a,1.082,-.87],[a,1.082,.19],[b,1.37,.19],[b,1.37,-.53],COLORS.glass);
  G.quad([a,1.055,.30],[a,1.055,1.48],[b,1.395,1.12],[b,1.395,.30],COLORS.black);
  G.quad([a,1.082,.35],[a,1.082,1.40],[b,1.37,1.05],[b,1.37,.35],COLORS.glass);
  G.quad([s*.77,1.02,.245],[s*.77,1.02,.31],[s*.68,1.43,.31],[s*.68,1.43,.245],paint);
  G.lineOnSide(s*.855,.86,-2.17,.86,2.17,COLORS.black,.014);
  for(const z of [-.20,.88])G.box(s*.86,.96,z,.022,.022,.18,COLORS.black);
  for(const z of [-.75,.27,1.43])G.lineOnSide(s*.853,.46,z,.85,z,COLORS.black,.006);
  G.wheel(s*.84,fy,fr,.357,.29,COLORS.silver);
  G.wheel(s*.84,fy,rr,.357,.29,COLORS.silver);
 }
 // Front and rear windscreens follow the roof planes.
 G.quad([-.756,1.055,-.98],[.756,1.055,-.98],[.67,1.41,-.60],[-.67,1.41,-.60],COLORS.black);
 G.quad([-.72,1.075,-.94],[.72,1.075,-.94],[.635,1.39,-.61],[-.635,1.39,-.61],COLORS.glass);
 G.quad([.67,1.41,1.13],[-.67,1.41,1.13],[-.756,1.055,1.55],[.756,1.055,1.55],COLORS.black);
 G.quad([.635,1.39,1.14],[-.635,1.39,1.14],[-.72,1.075,1.51],[.72,1.075,1.51],COLORS.glass);
 G.box(0,1.415,.265,1.33,.04,1.73,paint);
 // 1986-90 front treatment and rear lighting.
 G.box(0,.78,-2.361,1.51,.32,.045,COLORS.black);
 G.box(0,.78,-2.393,.62,.25,.02,COLORS.black);
 for(const s of [-1,1]){
  G.box(s*.53,.80,-2.40,.39,.225,.025,COLORS.lamp);
  G.box(s*.75,.80,-2.405,.075,.225,.03,COLORS.amber);
  G.box(s*.65,.80,2.386,.27,.32,.03,COLORS.rear);
 }
 for(let i=-2;i<=2;i++)G.box(i*.10,.78,-2.414,.012,.23,.02,"#899295");
 G.box(0,.55,-2.46,1.83,.15,.25,COLORS.tyre);
 G.box(0,.55,2.46,1.83,.15,.25,COLORS.tyre);
 G.box(0,.75,2.397,.45,.11,.03,COLORS.silver);
}
function tractor(G,id){
 const jd=id==="johnDeere6M",body=jd?"#3e8831":"#2375b5";
 const roof=jd?"#408633":"#236eac",rim=jd?"#e5bc23":"#c2c5bd";
 const nose=jd?-2.15:-2.24, frontY=jd?1.36:1.30, topY=jd?1.80:1.74;
 G.box(0,.98,.22,1.35,.4,3.24,"#343c3b");
 G.box(0,1.14,1.30,1.32,.34,.78,"#3b4140");
 G.quad([-.62,frontY,nose],[.62,frontY,nose],[.72,topY,-.46],[-.72,topY,-.46],body);
 for(const s of [-1,1]){
  G.quad([s*.62,1.05,nose],[s*.72,1.12,-.46],[s*.72,topY,-.46],[s*.62,frontY,nose],body);
  G.quad([s*.69,1.46,-1.89],[s*.70,1.46,-.72],[s*.70,1.58,-.72],[s*.69,1.58,-1.89],COLORS.black);
  G.box(s*.78,1.13,.46,.14,.50,.22,COLORS.black);
  const ba=jd?-.44:-.5,ta=jd?-.16:-.18,tb=jd?1.13:1.17,bb=jd?1.33:1.37;
  G.quad([s*.77,1.44,ba],[s*.77,1.44,bb],[s*.70,2.53,tb],[s*.70,2.53,ta],COLORS.black);
  G.quad([s*.779,1.53,ba+.08],[s*.779,1.53,.41],[s*.707,2.46,.40],[s*.707,2.46,ta+.07],COLORS.glass);
  G.quad([s*.779,1.53,.47],[s*.779,1.53,bb-.08],[s*.707,2.46,tb-.07],[s*.707,2.46,.47],COLORS.glass);
  G.quad([s*.79,1.44,.422],[s*.79,1.44,.50],[s*.71,2.55,.50],[s*.71,2.55,.422],roof);
  G.quad([s*.79,1.55,.79],[s*1.14,1.56,.84],[s*1.17,1.46,1.79],[s*.79,1.47,1.80],body);
  G.wheel(s*.89,.56,-1.28,.555,.35,rim);
  G.wheel(s*.96,.82,1.18,.835,.43,rim);
  G.box(s*.92,2.18,-.34,.19,.16,.23,COLORS.black);
 }
 G.quad([-.76,1.44,-.48],[.76,1.44,-.48],[.70,2.54,-.18],[-.70,2.54,-.18],COLORS.glass);
 G.quad([.70,2.54,1.17],[-.70,2.54,1.17],[-.76,1.44,1.36],[.76,1.44,1.36],COLORS.glass);
 G.box(0,2.65,.49,1.64,.20,1.60,roof);
 G.box(0,1.22,nose-.025,1.12,.22,.05,COLORS.black);
 for(const s of [-1,1])G.box(s*.42,1.46,nose-.03,.2,.09,.06,COLORS.lamp);
 G.box(0,1.15,1.89,1.15,.38,.24,COLORS.black);
 G.box(jd?.52:-.55,2.89,.60,.14,.20,.14,COLORS.amber);
 G.box(-.54,1.90,-.53,.10,.70,.11,COLORS.black);
}
const cache=new WeakMap();
export function buildVehicleGeometryData(id,options={}){
 if(!(id in VEHICLES))throw new RangeError("Unknown model: "+id);
 const G=new Builder();if(id==="volvo240")volvo(G,options.paint||VEHICLES[id].paint);else tractor(G,id);
 return {positions:G.position,normals:G.normal,colors:G.color};
}
export function createVehicleGeometry(THREE,id,options={}){
 if(!(id in VEHICLES))throw new RangeError("Unknown model: "+id);
 let c=cache.get(THREE);if(!c){c=new Map();cache.set(THREE,c)}
 const paint=options.paint||VEHICLES[id].paint,key=id+":"+paint;
 if(c.has(key))return c.get(key);
 const data=buildVehicleGeometryData(id,{paint}),geo=new THREE.BufferGeometry();
 geo.setAttribute("position",new THREE.Float32BufferAttribute(data.positions,3));
 geo.setAttribute("normal",new THREE.Float32BufferAttribute(data.normals,3));
 geo.setAttribute("color",new THREE.Float32BufferAttribute(data.colors,3));
 geo.computeBoundingSphere();c.set(key,geo);return geo;
}
export function disposeVehicleGeometries(THREE){
 const c=cache.get(THREE);if(c){for(const geo of c.values())geo.dispose();c.clear()}
}
