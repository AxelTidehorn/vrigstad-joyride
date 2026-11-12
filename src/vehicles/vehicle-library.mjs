/**
 * Standalone low-poly vehicle models for Vrigstad Joyride.
 * Front is -Z, +Y is up. Geometry is cached by model and paint.
 * Deliberately independent of the game simulation.
 */
export const VEHICLES = Object.freeze({
  volvo240: {name:"Volvo 240",paint:"#c7bda4"},
  saab900: {name:"Saab 900 Classic (experimental)",paint:"#a4acb2"},
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
 // Closed quadrilateral hull (faces are directed; geometry is rendered double-sided).
 hull(zFront,zRear,halfW,yFloor,yShoulder,topFront,topRear,paint) {
  this.quad([-halfW,yFloor,zFront],[halfW,yFloor,zFront],[halfW,yShoulder,zFront],[-halfW,yShoulder,zFront],paint);
  this.quad([halfW,yFloor,zRear],[-halfW,yFloor,zRear],[-halfW,yShoulder,zRear],[halfW,yShoulder,zRear],paint);
  this.quad([-halfW,yFloor,zFront],[-halfW,yFloor,zRear],[halfW,yFloor,zRear],[halfW,yFloor,zFront],COLORS.black);
  this.quad([-halfW,yShoulder,zFront],[halfW,yShoulder,zFront],[halfW,yShoulder,zRear],[-halfW,yShoulder,zRear],COLORS.black);
  this.quad([-halfW,yShoulder,zFront],[-halfW,yShoulder,zRear],[-halfW,topRear,zRear],[-halfW,topFront,zFront],paint);
  this.quad([halfW,yShoulder,zRear],[halfW,yShoulder,zFront],[halfW,topFront,zFront],[halfW,topRear,zRear],paint);
 }
 lineOnSide(x,y1,z1,y2,z2,color,width=.016){
  this.quad([x,y1,z1-width],[x,y1,z1+width],[x,y2,z2+width],[x,y2,z2-width],color)
 }
 wheel(x,y,z,r,w,rim){
  const s=Math.sign(x),N=18,inner=x-s*w/2,outer=x+s*w/2;
  const ring=(at,rad)=>Array.from({length:N},(_,i)=>[at,y+rad*Math.sin(i*2*Math.PI/N),z+rad*Math.cos(i*2*Math.PI/N)]);
  const A=ring(inner,r),B=ring(outer,r);
  for(let i=0;i<N;i++)this.quad(A[i],A[(i+1)%N],B[(i+1)%N],B[i],COLORS.tyre);
  this.poly(B,COLORS.tyre);this.poly(ring(outer+s*.01,r*.51),rim);
  this.poly(ring(outer+s*.018,r*.22),COLORS.silver);
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
 // Interior skin closes the see-through sill and wheelhouse voids without
 // covering the exterior wheel-arch cut-outs or window glass.
 G.hull(-2.345,2.345,.745,.325,.885,.933,.986,paint);
 G.box(0,.47,0,1.59,.18,4.55,paint);
 // Close each exposed hood-to-grille and trunk-to-tail interface.
 G.quad([-.785,.900,-2.355],[.785,.900,-2.355],[.785,.955,-2.345],[-.785,.955,-2.345],paint);
 G.quad([-.785,.985,2.345],[.785,.985,2.345],[.785,1.001,2.295],[-.785,1.001,2.295],paint);
 // Seal the bottom of both end skirts above bumpers.
 G.quad([-.80,.355,-2.35],[.80,.355,-2.35],[.80,.65,-2.35],[-.80,.65,-2.35],paint);
 G.quad([.80,.355,2.35],[-.80,.355,2.35],[-.80,.65,2.35],[.80,.65,2.35],paint);
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
  G.wheel(s*.84,fy+.055,fr,.357,.29,COLORS.silver);
  G.wheel(s*.84,fy+.055,rr,.357,.29,COLORS.silver);
 }
 // Front and rear windscreens follow the roof planes.
 G.quad([-.756,1.055,-.98],[.756,1.055,-.98],[.67,1.41,-.60],[-.67,1.41,-.60],COLORS.black);
 G.quad([-.72,1.075,-.94],[.72,1.075,-.94],[.635,1.39,-.61],[-.635,1.39,-.61],COLORS.glass);
 G.quad([.67,1.41,1.13],[-.67,1.41,1.13],[-.756,1.055,1.55],[.756,1.055,1.55],COLORS.black);
 G.quad([.635,1.39,1.14],[-.635,1.39,1.14],[-.72,1.075,1.51],[.72,1.075,1.51],COLORS.glass);
 // Roof-to-window rebates and C-pillar close the apparent holes at the ends.
 for(const s of [-1,1]){
  G.quad([s*.756,1.055,-.98],[s*.67,1.41,-.60],[s*.635,1.39,-.61],[s*.72,1.075,-.94],paint);
  G.quad([s*.67,1.41,1.13],[s*.756,1.055,1.55],[s*.72,1.075,1.51],[s*.635,1.39,1.14],paint);
  // Inner body backstop under glazing, instead of seeing through to the ground.
  G.quad([s*.705,1.005,-.96],[s*.705,1.005,1.54],[s*.68,1.36,1.10],[s*.68,1.36,-.58],COLORS.black);
 }
 G.box(0,1.415,.265,1.33,.04,1.73,paint);
 // Close the actual rear body panel; previously only lamps, plate and bumper existed here.
 // The panel sits beneath the trim so the license plate cannot reveal open space.
 G.quad([-.785,.565,2.359],[.785,.565,2.359],[.785,.984,2.359],[-.785,.984,2.359],paint);
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
const SAAB_COLORS={glass:'#263d4a',glass2:'#334b57',black:'#172126',rubber:'#222729',gray:'#929c9e',silver:'#b8c0be',lamp:'#d9dfd8',amber:'#d79955',rear:'#ab3532'};
// Experimental 900 silhouette, retained for evaluation rather than approved production shape.
function saab(G,paint){const col=paint,topY=z=>z<-.94?.842+(z+2.31)*.158/1.37:z<2?.999:.999-(z-2)*.08/.31;
 const fa=-1.265,ra=1.252,r=.404;const zs=[-2.31,-2.22,-1.88,-.94,-.60,0,.6,1.22,1.86,2.1,2.31];for(let c of [fa,ra])for(let i=0;i<=18;i++)zs.push(c-r+2*r*i/18);zs.sort((a,b)=>a-b);const pts=zs.filter((x,i)=>!i||x-zs[i-1]>.002);
 const low=z=>{let y=.328;for(let c of [fa,ra]){const d=Math.abs(z-c);if(d<r)y=Math.max(y,.365+Math.sqrt(r*r-d*d))}return y};
 for(let sd of [-1,1]){let x=sd*.8;for(let i=0;i<pts.length-1;i++){let z=pts[i],zz=pts[i+1];G.quad([x,low(z),z],[x,low(zz),zz],[x,topY(zz),zz],[x,topY(z),z],col,sd>0?.95:1)}
 // sill only under door area
 G.quad([sd*.807,.338,-.8],[sd*.807,.338,.83],[sd*.809,.390,.83],[sd*.809,.390,-.8],'#343d40');
 // shoulder belt and door seam on the proper side
 G.quad([sd*.809,.724,-2.10],[sd*.809,.724,2.18],[sd*.811,.739,2.18],[sd*.811,.739,-2.10],'#30383b');
 G.quad([sd*.812,.436,-.80],[sd*.812,.436,.82],[sd*.812,.449,.82],[sd*.812,.449,-.80],SAAB_COLORS.rubber);
 G.lineOnSide(sd*.817,.966,.46,.445,.46,'#384247',.008);
 G.quad([sd*.816,.948,.18],[sd*.816,.948,.33],[sd*.816,.968,.33],[sd*.816,.968,.18],SAAB_COLORS.black);
 // glass wrapped dark seal + inset colored glass; front A-post rising to roof
 G.quad([sd*.805,.992,-.915],[sd*.805,.992,.435],[sd*.649,1.420,.395],[sd*.648,1.420,-.465],SAAB_COLORS.black);
 G.quad([sd*.814,1.016,-.875],[sd*.814,1.016,.375],[sd*.653,1.387,.36],[sd*.655,1.387,-.433],SAAB_COLORS.glass);
 // rear quarter glass: lower edge stretches far back, upper follows roof, rear edge steep diagonal
 G.poly([[sd*.806,.990,.445],[sd*.806,.990,1.730],[sd*.718,1.096,1.780],[sd*.641,1.419,.840],[sd*.642,1.419,.425]],SAAB_COLORS.black);
 G.poly([[sd*.814,1.012,.488],[sd*.814,1.012,1.662],[sd*.729,1.109,1.694],[sd*.653,1.390,.808],[sd*.653,1.390,.481]],SAAB_COLORS.glass);
 // C-pillar follows hatch roof line and sits *behind* quarter window; broad enough to register silhouette
 G.poly([[sd*.644,1.429,.800],[sd*.645,1.429,.919],[sd*.743,1.072,1.97],[sd*.739,1.071,1.77]],col);
 // framing and door division
 G.quad([sd*.811,.985,.398],[sd*.811,.985,.443],[sd*.659,1.418,.437],[sd*.659,1.418,.395],col);
 // tiny mirror
 G.box(sd*.84,1.065,-.78,.1,.13,.14,'#30383a');
 }
 // Inner shell behind wheel openings and side panels. Inset prevents Z-fighting.
 G.hull(-2.295,2.295,.726,.31,.80,.835,.92,col);
 // Opaque sail backing keeps the rear glass/hatch from showing through the car.
 for(const sd of [-1,1]){
  G.quad([sd*.73,.986,.82],[sd*.73,.986,2.14],[sd*.62,1.425,.862],[sd*.62,1.425,.82],col);
 }
 // hood inclined gently from deep windscreen base toward slant nose
 G.quad([-.75,.845,-2.31],[.75,.845,-2.31],[.75,.999,-.94],[-.75,.999,-.94],col,1.07);
 // bumper-to-front face wedge (increasing front projection toward lower y)
 const nz=y=>-2.21-(.94-y)*.33;
 G.quad([-.75,.615,nz(.615)],[.75,.615,nz(.615)],[.75,.928,nz(.928)],[-.75,.928,nz(.928)],col,.93);
 function nosePatch(x1,x2,y1,y2,c){let e=-.020;G.quad([x1,y1,nz(y1)+e],[x2,y1,nz(y1)+e],[x2,y2,nz(y2)+e],[x1,y2,nz(y2)+e],c)}
 nosePatch(-.33,.33,.720,.894,SAAB_COLORS.black);for(let sd of [-1,1]){nosePatch(sd*.535-.19,sd*.535+.19,.721,.904,SAAB_COLORS.lamp);nosePatch(sd*.76-.048,sd*.76+.048,.721,.904,SAAB_COLORS.amber)}
 for(let k=-2;k<=2;k++)nosePatch(k*.12-.007,k*.12+.007,.735,.883,'#66767b');
 // Nose closure reaches below headlight panel, which formerly had no lower face.
 G.quad([-.75,.34,-2.34],[.75,.34,-2.34],[.75,.615,nz(.615)],[-.75,.615,nz(.615)],col);
 G.box(0,.508,-2.39,1.69,.14,.16,SAAB_COLORS.rubber);
 // windscreen lower and upper points
 G.quad([-.738,1.000,-.94],[.738,1.000,-.94],[.631,1.429,-.49],[-.631,1.429,-.49],SAAB_COLORS.black);
 G.quad([-.710,1.022,-.912],[.710,1.022,-.912],[.607,1.394,-.468],[-.607,1.394,-.468],SAAB_COLORS.glass2);
 // roof + continuous long sloping hatch; more sweep than v2
 G.quad([-.636,1.440,-.49],[.636,1.440,-.49],[.643,1.440,.862],[-.643,1.440,.862],col,1.13);
 G.quad([-.644,1.437,.862],[.644,1.437,.862],[.752,.985,2.125],[-.752,.985,2.125],col,.96);
 // Outer sail panels close the space between hatch slope and beltline.
 // They also keep the long hatch visible in exact side profile (top face is edge-on).
 for(const sd of [-1,1]) { const zA=.86,zB=2.126,rail=z=>1.44-(z-zA)*(.454/(zB-zA)); const outerX=z=>sd*(.611+(z-zA)*(.135/(zB-zA)));
   for(let j=0;j<10;j++){const a=zA+(zB-zA)*j/10,b=zA+(zB-zA)*(j+1)/10;
     G.quad([sd*.774,.992,a],[sd*.774,.992,b],[outerX(b),rail(b),b],[outerX(a),rail(a),a],col,.96);
   }
 }
 G.quad([-.635,1.431,.915],[.635,1.431,.915],[.729,1.008,2.028],[-.729,1.008,2.028],SAAB_COLORS.black);
 G.quad([-.610,1.413,.947],[.610,1.413,.947],[.702,1.031,1.989],[-.702,1.031,1.989],SAAB_COLORS.glass2);
 G.quad([-.754,.989,2.12],[.754,.989,2.12],[.76,.931,2.31],[-.76,.931,2.31],col);
 G.quad([-.754,.93,2.33],[.754,.93,2.33],[.754,.612,2.34],[-.754,.612,2.34],col,.94);
 // Full-width tail closure and the lower section behind the number plate.
 G.quad([-.754,.34,2.345],[.754,.34,2.345],[.754,.615,2.345],[-.754,.615,2.345],col);
 // The short side returns tie the sloping tail panel to the side skins.
 for(const sd of [-1,1])G.quad([sd*.80,.61,2.30],[sd*.754,.612,2.34],[sd*.754,.93,2.33],[sd*.80,.92,2.30],col);
 for(let sd of [-1,1]){let xx=sd*.63;G.box(xx,.797,2.352,.27,.21,.035,SAAB_COLORS.rear);G.box(xx,.853,2.379,.27,.045,.014,SAAB_COLORS.amber)}
 G.box(0,.770,2.36,.45,.11,.015,'#919b9d');G.box(0,.51,2.43,1.67,.13,.15,SAAB_COLORS.rubber);
 for(let sd of [-1,1]){G.wheel(sd*.779,.40,fa,.354,.265,'#aab4b8');G.wheel(sd*.779,.40,ra,.354,.265,'#aab4b8')}
}

function tractor(G,id){
 const jd=id==="johnDeere6M",body=jd?"#3e8831":"#2375b5";
 const roof=jd?"#408633":"#236eac",rim=jd?"#e5bc23":"#c2c5bd";
 const nose=jd?-2.15:-2.24, frontY=jd?1.36:1.30, topY=jd?1.80:1.74;
 // Continuous inner frame and engine block close the open underside.
 G.box(0,.98,.22,1.35,.4,3.24,"#343c3b");
 G.box(0,1.16,-1.34,1.18,.48,1.70,body);
 G.quad([-.62,.90,nose],[.62,.90,nose],[.62,frontY,nose],[-.62,frontY,nose],body);
 // Cab floor and rear bulkhead provide the depth missing from window-only surfaces.
 G.box(0,1.44,.49,1.40,.11,1.78,"#303b3b");
 G.quad([-.69,1.43,1.36],[.69,1.43,1.36],[.69,2.53,1.17],[-.69,2.53,1.17],COLORS.black);
 G.box(0,1.14,1.30,1.32,.34,.78,"#3b4140");
 G.quad([-.62,frontY,nose],[.62,frontY,nose],[.72,topY,-.46],[-.72,topY,-.46],body);
 for(const s of [-1,1]){
  G.quad([s*.62,1.05,nose],[s*.72,1.12,-.46],[s*.72,topY,-.46],[s*.62,frontY,nose],body);
  G.quad([s*.69,1.46,-1.89],[s*.70,1.46,-.72],[s*.70,1.58,-.72],[s*.69,1.58,-1.89],COLORS.black);
  // Cab sheet metal at window bottom (only the glass remains transparent-looking).
  G.quad([s*.755,1.40,-.50],[s*.755,1.40,1.38],[s*.70,1.57,1.34],[s*.70,1.57,-.43],body);
  G.box(s*.78,1.13,.46,.14,.50,.22,COLORS.black);
  const ba=jd?-.44:-.5,ta=jd?-.16:-.18,tb=jd?1.13:1.17,bb=jd?1.33:1.37;
  G.quad([s*.77,1.44,ba],[s*.77,1.44,bb],[s*.70,2.53,tb],[s*.70,2.53,ta],COLORS.black);
  G.quad([s*.779,1.53,ba+.08],[s*.779,1.53,.41],[s*.707,2.46,.40],[s*.707,2.46,ta+.07],COLORS.glass);
  G.quad([s*.779,1.53,.47],[s*.779,1.53,bb-.08],[s*.707,2.46,tb-.07],[s*.707,2.46,.47],COLORS.glass);
  G.quad([s*.79,1.44,.422],[s*.79,1.44,.50],[s*.71,2.55,.50],[s*.71,2.55,.422],roof);
  G.quad([s*.79,1.55,.79],[s*1.14,1.56,.84],[s*1.17,1.46,1.79],[s*.79,1.47,1.80],body);
  G.wheel(s*.89,.60,-1.28,.555,.35,rim);
  G.wheel(s*.96,.87,1.18,.835,.43,rim);
  G.box(s*.92,2.18,-.34,.19,.16,.23,COLORS.black);
 }
 G.quad([-.76,1.44,-.48],[.76,1.44,-.48],[.70,2.54,-.18],[-.70,2.54,-.18],COLORS.glass);
 G.quad([.70,2.54,1.17],[-.70,2.54,1.17],[-.76,1.44,1.36],[.76,1.44,1.36],COLORS.glass);
 // Upper roof seals and front cab header.
 G.box(0,2.65,.49,1.64,.20,1.60,roof);
 G.quad([-.70,2.53,-.18],[.70,2.53,-.18],[.70,2.55,-.31],[-.70,2.55,-.31],roof);
 G.quad([.70,2.53,1.17],[-.70,2.53,1.17],[-.70,2.55,1.28],[.70,2.55,1.28],roof);
 G.box(0,1.22,nose-.025,1.12,.22,.05,COLORS.black);
 for(const s of [-1,1])G.box(s*.42,1.46,nose-.03,.2,.09,.06,COLORS.lamp);
 G.box(0,1.15,1.89,1.15,.38,.24,COLORS.black);
 G.box(jd?.52:-.55,2.89,.60,.14,.20,.14,COLORS.amber);
 G.box(-.54,1.90,-.53,.10,.70,.11,COLORS.black);
}
const cache=new WeakMap();
export function buildVehicleGeometryData(id,options={}){
 if(!(id in VEHICLES))throw new RangeError("Unknown model: "+id);
 const G=new Builder();if(id==="volvo240")volvo(G,options.paint||VEHICLES[id].paint);
 else if(id==="saab900")saab(G,options.paint||VEHICLES[id].paint);
 else tractor(G,id);
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
