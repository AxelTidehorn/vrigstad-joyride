/**
 * Standalone low-poly vehicle models for Vrigstad Joyride.
 * Front is -Z, +Y is up. Geometry is cached by model and paint.
 * Deliberately independent of the game simulation.
 */
export const VEHICLES = Object.freeze({
  volvo240: {name:"Volvo 240",paint:"#c7bda4"},
  saab900: {name:"Saab 900 Classic (experimental)",paint:"#a4acb2"},
  saab95Estate: {name:"Saab 9-5 SportCombi (2002–2005)",paint:"#a4afb8"},
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

// 2002–2005 9-5 five-door estate: measured dimensions in metres from Saab WIS.
// X is lateral, Y is up, -Z is forward. Independent from the classic 900.
function saab95Estate(G, paint) {
 const C = {rubber:'#20272b',seal:'#171f22',glass:'#304651',rearGlass:'#263b48',
  chrome:'#a9b4b5',light:'#dbe3df',amber:'#dca257',red:'#a72a35',
  deepRed:'#681e27',bumper:'#33383a',plate:'#d9d9cc',rim:'#b8bfc0',shadow:'#505c60'};
 const front=-2.414, rear=2.414, axles=[-1.398,1.305],wheelR=.349,archR=.416,cy=.362;
 const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
 const width=z=>.849+.046*Math.max(0,1-Math.pow(Math.abs(z)/2.48,2));
 const belt=z=>1.006+(z>1.96?-.042*(z-1.96)/.454:0);
 const bx=(z,y)=>width(z)-.045*Math.max(0,y-.82)/.25-.075*Math.pow(Math.max(0,.82-y)/.54,2);
 const archY=z=>{
  let y=.296;
  for(const a of axles){const d=Math.abs(z-a);if(d<archR)y=Math.max(y,cy+Math.sqrt(archR*archR-d*d));}
  return y;
 };
 const side=(s,z,y,offset=0)=>[s*(bx(z,y)+offset),y,z];
 // Panels are a continuous strip mesh, tessellated along length, with real holes over the tyres.
 const stops=[front,-2.37,-2.28,-2.14,-1.95,-1.81,-1.67,-1.45,-1.23,-1.00,-.92,-.70,-.45,-.14,.18,.46,.77,1.07,1.33,1.62,1.89,2.10,2.26,2.37,rear];
 for(const z of axles)for(let k=0;k<=30;k++)stops.push(z-archR+2*archR*k/30);
 const zz=[...new Set(stops.map(v=>v.toFixed(5)))].map(Number).sort((a,b)=>a-b);
 for(const s of [-1,1])for(let i=1;i<zz.length;i++){
  const a=zz[i-1], b=zz[i],ya=archY(a),yb=archY(b);
  if(b-a<.00005)continue;
  G.quad(side(s,a,ya),side(s,b,yb),side(s,b,.793),side(s,a,.793),paint);
  G.quad(side(s,a,.793),side(s,b,.793),side(s,b,.917),side(s,a,.917),paint);
  G.quad(side(s,a,.917),side(s,b,.917),side(s,b,belt(b)),side(s,a,belt(a)),paint);
 }
 // Recessed, dark wheelhouse backing and floor, kept inboard from visible bodywork.
 G.box(0,.334,0,1.32,.11,4.70,C.rubber);
 for(const z of axles)for(const s of [-1,1]){
  const N=24;
  for(let j=0;j<N;j++){
   const a=-Math.PI/2+Math.PI*j/N,b=-Math.PI/2+Math.PI*(j+1)/N;
   const at=t=>[s*.736,cy+archR*Math.cos(t),z+archR*Math.sin(t)];
   const bt=t=>[s*.752,cy+archR*Math.cos(t),z+archR*Math.sin(t)];
   G.quad(at(a),at(b),bt(b),bt(a),C.rubber);
  }
 }
 // Wide yet subtly crowned hood; front corner retreat gives the 9-5 its rounded nose.
 const hoodZ=[front,-2.36,-2.20,-2.04,-1.81,-1.54,-1.24,-.98];
 const hoodY=z=>.936+(.994-.936)*clamp((z-front)/(-.98-front),0,1);
 const uv=[-1,-.86,-.69,-.48,-.25,0,.25,.48,.69,.86,1];
 const hoodPoint=(u,z)=>[u*(bx(z,.98)-.030),hoodY(z)+.031*(1-u*u),z+.022*u*u];
 for(let i=1;i<hoodZ.length;i++)for(let j=1;j<uv.length;j++)
  G.quad(hoodPoint(uv[j-1],hoodZ[i-1]),hoodPoint(uv[j],hoodZ[i-1]),
         hoodPoint(uv[j],hoodZ[i]),hoodPoint(uv[j-1],hoodZ[i]),paint);
 // Lower lip closes the front body volume at multiple cross sections.
 const nose=(u,y,dz=0)=>{
  const x=u*(.807+.033*(y-.42));
  return [x,y,front + .190*u*u + .077*(y-.48) + dz];
 };
 const ys=[.31,.39,.49,.57,.69,.79,.88,.935];
 for(let i=1;i<ys.length;i++)for(let j=1;j<uv.length;j++)
  G.quad(nose(uv[j-1],ys[i-1]),nose(uv[j],ys[i-1]),nose(uv[j],ys[i]),nose(uv[j-1],ys[i]),paint);
 // Rounded boot/tailgate and rear bumper, gently recessed towards the corners.
 const back=(u,y,dz=0)=>[u*(.813+.014*y),y,rear-.160*u*u-.057*(y-.49)+dz];
 for(let i=1;i<ys.length;i++)for(let j=1;j<uv.length;j++)
  G.quad(back(uv[j-1],ys[i-1]),back(uv[j],ys[i-1]),back(uv[j],ys[i]),back(uv[j-1],ys[i]),paint);
 for(let j=1;j<uv.length;j++)
  G.quad(back(uv[j-1],.88),back(uv[j],.88),back(uv[j],.989),back(uv[j-1],.989),paint);
 // Windscreen and rear hatch are *inlaid*: seal ring and glass occupy disjoint regions.
 // Geometry is not drawn on top of glass, avoiding co-planar surfaces entirely.
 const framed=(outer,inner,glass)=>{
  for(let i=0;i<4;i++)G.quad(outer[i],outer[(i+1)%4],inner[(i+1)%4],inner[i],C.seal);
  G.quad(inner[0],inner[1],inner[2],inner[3],glass);
 };
 const roofX=z=>.694-.042*clamp((z-1.5)/.55,0,1);
 const roofY=z=>1.474-.015*clamp((z-.20)/1.73,0,1)-.020*Math.pow(clamp((z-1.70)/.30,0,1),2);
 // Sloping front glass, no separate black sheet underneath the glass.
 framed([[-.806,1.012,-.981],[.806,1.012,-.981],[.680,1.472,-.492],[-.680,1.472,-.492]],
        [[-.774,1.034,-.951],[.774,1.034,-.951],[.649,1.447,-.501],[-.649,1.447,-.501]],C.glass);
 // Long continuous curved roof (not the flat shoebox top from v0.1).
 const roofZ=[-.492,-.30,.02,.35,.72,1.10,1.42,1.69,1.90];
 const rp=(u,z)=>[u*roofX(z),roofY(z)+.018*(1-u*u),z];
 for(let i=1;i<roofZ.length;i++)for(let j=1;j<uv.length;j++)
  G.quad(rp(uv[j-1],roofZ[i-1]),rp(uv[j],roofZ[i-1]),rp(uv[j],roofZ[i]),rp(uv[j-1],roofZ[i]),paint);
 // SportCombi hatch: slopes aft below the trailing roof edge, with a broad glazed area.
 framed([[-.661,1.441,1.92],[.661,1.441,1.92],[.793,.992,2.361],[-.793,.992,2.361]],
        [[-.626,1.411,1.954],[.626,1.411,1.954],[.755,1.029,2.344],[-.755,1.029,2.344]],C.rearGlass);
 // Side glazing as a set of truly separated window openings. Side panels stop at the belt;
 // painted A/B/C/D posts use strips between frames rather than coplanar overprints.
 const windowX=(s,z,y)=>[s*(bx(z,1.01)-.145*clamp((y-1.01)/.47,0,1)),y,z];
 const putPanel=(s,q,color)=>G.poly(q.map(([z,y])=>windowX(s,z,y)),color);
 const sideWindow=(s,q,glass)=>{
  // Four corners: lower front, lower rear, upper rear, upper front.
  const inner=q.map(([z,y],i)=>{
   const next=q[(i+1)%4], prev=q[(i+3)%4];
   return [z*.895+(next[0]+prev[0])*.0525,y*.895+(next[1]+prev[1])*.0525];
  });
  const a=q.map(([z,y])=>windowX(s,z,y));
  const b=inner.map(([z,y])=>windowX(s,z,y));
  framed(a,b,glass);
 };
 for(const s of [-1,1]){
  // A- and B-pillars, an appreciable C-pillar and a swept rear D-pillar.
  putPanel(s,[[-1.000,1.014],[-.550,1.474],[-.545,1.444],[-.862,1.022],[-.875,1.014]],paint);
  putPanel(s,[[.120,1.014],[.100,1.472],[.213,1.473],[.233,1.014]],paint);
  putPanel(s,[[1.176,1.014],[1.177,1.467],[1.301,1.466],[1.315,1.014]],paint);
  putPanel(s,[[1.912,1.427],[2.363,.980],[2.225,.979],[1.817,1.456]],paint);
  sideWindow(s,[[-.857,1.022],[.120,1.022],[.100,1.444],[-.541,1.443]],C.glass);
  sideWindow(s,[[.232,1.022],[1.175,1.022],[1.175,1.438],[.215,1.445]],C.glass);
  sideWindow(s,[[1.314,1.022],[2.165,1.022],[1.801,1.425],[1.308,1.435]],C.glass);
  // Continuous upper belt; door gaps are narrow, recessed, never same-plane overlays.
  for(let i=1;i<zz.length;i++){
   const a=zz[i-1],b=zz[i];
   G.quad(side(s,a,.756,.008),side(s,b,.756,.008),side(s,b,.786,.008),side(s,a,.786,.008),C.rubber);
  }
  for(const z of [.225,1.311]){
   G.quad(side(s,z-.008,.403,.009),side(s,z+.008,.403,.009),
          side(s,z+.008,1.005,.009),side(s,z-.008,1.005,.009),C.rubber);
  }
  // Painted and black trim mirrors, low roof rails, narrow handle recesses.
  G.box(s*.911,1.036,-.957,.110,.104,.16,paint);
  G.box(s*.976,1.036,-.953,.034,.050,.13,C.rubber);
  for(const z of [-.24,.71])G.box(s*.883,.945,z,.022,.040,.140,C.rubber);
  G.box(s*.617,1.501,.75,.038,.031,2.25,C.rubber);
  G.box(s*.615,1.492,-.27,.045,.032,.110,C.rubber);
  G.box(s*.616,1.494,1.78,.045,.032,.110,C.rubber);
 }
 // 2002 facelift: organic wrap-around lamps and the three swept Saab grille ports.
 // Grille is formed from trapezoidal rings rather than broad black rectangles.
 const decal=(u1,u2,y1,y2,color,advance=.012)=>
  G.quad(nose(u1,y1,-advance),nose(u2,y1,-advance),nose(u2,y2,-advance),nose(u1,y2,-advance),color);
 const grill=(outline)=>{
  const cx=outline.reduce((a,p)=>a+p[0],0)/outline.length;
  const cy0=outline.reduce((a,p)=>a+p[1],0)/outline.length;
  const inner=outline.map(([u,y])=>[cx+(u-cx)*.78,cy0+(y-cy0)*.77]);
  for(let i=0;i<outline.length;i++){
   const a=outline[i],b=outline[(i+1)%outline.length];
   const c=inner[(i+1)%inner.length],d=inner[i];
   G.quad(nose(...a,-.018),nose(...b,-.018),nose(...c,-.018),nose(...d,-.018),C.chrome);
  }
  G.poly(inner.map(p=>nose(...p,-.032)),C.seal);
 };
 grill([[-.263,.709],[.263,.709],[.225,.880],[-.225,.880]]);
 for(const s of [-1,1]){
  grill([[s*.310,.733],[s*.498,.734],[s*.458,.868],[s*.288,.865]]);
  // Curved outer corner and gently swept top edge are distinctive to pre-2006 9-5.
  const rim=[[.500,.728],[.657,.716],[.944,.750],[.955,.822],[.910,.929],[.702,.943],[.512,.904]]
    .map(([u,y])=>nose(s*u,y,-.018));
  const glazing=[[.521,.747],[.661,.738],[.919,.772],[.930,.822],[.892,.911],[.702,.923],[.532,.883]]
    .map(([u,y])=>nose(s*u,y,-.035));
  for(let i=0;i<rim.length;i++)G.quad(rim[i],rim[(i+1)%rim.length],glazing[(i+1)%rim.length],glazing[i],C.chrome);
  G.poly(glazing,C.light);
  decal(s*.829,s*.943,.769,.819,C.amber,.047);
 }
 // Recessed upper bumper strip, front air intake and plate.
 decal(-.955,.955,.540,.574,C.rubber,.027);
 decal(-.470,.470,.375,.426,C.rubber,.031);
 for(const s of [-1,1])decal(s*.715,s*.888,.381,.444,C.shadow,.028);
 // Head-on convex rear lamps. Side wrap portions sit on adjacent body planes.
 for(const s of [-1,1]){
  const x=s*.704;
  G.quad(back(s*.68,.681,.022),back(s*.92,.681,.022),
         back(s*.92,1.078,.022),back(s*.68,1.078,.022),C.red);
  G.quad(back(s*.708,.857,.033),back(s*.902,.857,.033),
         back(s*.902,.934,.033),back(s*.708,.934,.033),C.light);
  G.quad([s*.856,.734,2.266],[s*.873,.734,2.180],
         [s*.860,1.052,2.180],[s*.847,1.052,2.281],C.red);
 }
 G.quad(back(-.290,.604,-.024),back(.290,.604,-.024),back(.290,.718,-.024),back(-.290,.718,-.024),C.plate);
 G.quad(back(-.986,.500,.016),back(.986,.500,.016),back(.986,.584,.016),back(-.986,.584,.016),C.rubber);
 G.box(0,1.045,2.364,.510,.015,.026,C.rubber);
 G.box(0,1.444,1.905,1.27,.032,.090,paint);
 // Proper five-spoke wheels: tyre sidewall, recessed dark wheel well, silver spokes.
 for(const s of [-1,1])for(const z of axles){
  const N=32,x=s*.755,outer=s*.869,inner=s*.716;
  const circle=(u,r,k)=>[u,cy+r*Math.cos(k*2*Math.PI/N),z+r*Math.sin(k*2*Math.PI/N)];
  for(let k=0;k<N;k++){
   G.quad(circle(inner,wheelR,k),circle(inner,wheelR,k+1),
          circle(outer,wheelR,k+1),circle(outer,wheelR,k),C.rubber);
   G.quad(circle(outer,wheelR,k),circle(outer,wheelR,k+1),
          circle(outer+s*.009,.255,k+1),circle(outer+s*.009,.255,k),C.rubber);
   G.quad(circle(outer+s*.009,.255,k),circle(outer+s*.009,.255,k+1),
          circle(outer+s*.014,.206,k+1),circle(outer+s*.014,.206,k),C.shadow);
  }
  // Hub and spokes are outside the recessed wheel face, no duplicate/coplanar circles.
  const face=outer+s*.023;
  const p=(r,a)=>[face,cy+r*Math.cos(a),z+r*Math.sin(a)];
  for(let k=0;k<5;k++){
   const a=(k+.16)*2*Math.PI/5;
   G.quad(p(.064,a-.22),p(.210,a-.155),p(.210,a+.155),p(.064,a+.22),C.rim);
  }
  G.poly(Array.from({length:16},(_,k)=>p(.066,k*2*Math.PI/16)),C.chrome);
 }
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
 else if(id==="saab95Estate")saab95Estate(G,options.paint||VEHICLES[id].paint);
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
