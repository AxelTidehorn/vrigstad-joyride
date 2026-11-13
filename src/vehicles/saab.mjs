// Closed body loft: one connected, outward-wound shell. -Z forward, metres.
// Panel colors live on faces; glass is opaque, so no interior/transparent sorting.
export function buildBodyData(paint='#c9bd9c') {
 const positions=[],colors=[],normals=[],vertices=[],faces=[],glassFaces=[],glassNormals=new Map();
 const rgb=h=>{const v=parseInt(h.slice(1),16);return [(v>>16&255)/255,(v>>8&255)/255,(v&255)/255].map(c=>c<=.04045?c/12.92:Math.pow((c+.055)/1.055,2.4))};
 const push=(a,b,c,color)=>{
  const p=vertices[a],q=vertices[b],r=vertices[c],u=q.map((v,i)=>v-p[i]),v=r.map((x,i)=>x-p[i]);
  let n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],len=Math.hypot(...n);if(len<1e-10)throw Error('Degenerate body face');n=n.map(x=>x/len);
  if(color==='#263c47'){
   glassFaces.push(faces.length);
   for(const index of [a,b,c]){if(!glassNormals.has(index))glassNormals.set(index,[0,0,0]);const sum=glassNormals.get(index);for(let k=0;k<3;k++)sum[k]+=n[k]*len}
  }
  faces.push([a,b,c]);for(const i of [a,b,c]){positions.push(...vertices[i]);normals.push(...n);colors.push(...rgb(color))}
 };
 // Each station: z, half width, belt height, roof half width, roof height.
 const stations=[[-2.3, 0.78, 0.76, 0.75, 0.84], [-1.0, 0.82, 0.91, 0.77, 1.0], [-0.8, 0.81, 0.93, 0.72, 1.22], [-0.48, 0.8, 0.95, 0.64, 1.43], [0.27, 0.8, 0.95, 0.64, 1.43], [0.33, 0.8, 0.95, 0.64, 1.43], [0.72, 0.8, 0.95, 0.64, 1.43], [1.12, 0.8, 0.95, 0.68, 1.3], [1.67, 0.79, 0.93, 0.72, 1.09], [2.3, 0.77, 0.86, 0.75, 0.94]];
 const axles=[-1.27,1.25],keys=stations.map(p=>p[0]);
 for(const z of axles)for(let i=0;i<=12;i++)keys.push(z-.39+i*.78/12);
 keys.sort((a,b)=>a-b);
 const rings=keys.filter((z,i)=>!i||z-keys[i-1]>1e-6).map(z=>{
  const i=Math.min(stations.length-2,Math.max(0,stations.findIndex(p=>p[0]>z)-1));
  const left=stations[i],right=stations[i+1],t=(z-left[0])/(right[0]-left[0]);
  // Last station is handled explicitly; all other samples interpolate the loft.
  if(z===stations.at(-1)[0])return [...stations.at(-1)];
  return [z,...left.slice(1).map((v,k)=>v+(right[k+1]-v)*t)];
 });
 for(const [z,w,b,r,h] of rings){
  let base=.34;for(const axle of axles){const d=Math.abs(z-axle);if(d<.39)base=Math.max(base,.33+Math.sqrt(Math.max(0,.39*.39-d*d)))}
  const wind=z>-1&&z<-.48?.07*Math.sin(Math.PI*(z+1)/.52):0;
  vertices.push([-w,base,z],[w,base,z],[w,b,z],[r,h,z],[0,h+.008,z-wind],[-r,h,z],[-w,b,z]);
 }
 const N=7;
 for(let i=0;i<rings.length-1;i++)for(let j=0;j<N;j++){
  const a=i*N+j,b=i*N+(j+1)%N,c=(i+1)*N+(j+1)%N,d=(i+1)*N+j;
  // Glass is a material region of the closed shell, never a floating panel.
  const color=(((j===2||j===5)&&rings[i][0]>=-1&&rings[i+1][0]<=1.67&&!(rings[i][0]>=.27&&rings[i+1][0]<=.33))||((j===3||j===4)&&((rings[i][0]>=-1&&rings[i+1][0]<=-.48)||(rings[i][0]>=.72&&rings[i+1][0]<=1.67))))?'#263c47':paint;
  push(a,b,c,color);push(a,c,d,color);
 }
 // End caps use a center vertex: shared ring edges give manifold closure.
 for(const end of [0,rings.length-1]){
  const center=vertices.length,z=rings[end][0];vertices.push([0,.65,z]);
  for(let j=0;j<N;j++){
   if(end===0)push(center,(j+1)%N,j,paint);
   else push(center,end*N+j,end*N+(j+1)%N,paint);
  }
 }
 // Smooth only connected glazing: hard paint/pillar edges remain flat.
 for(const sum of glassNormals.values()){const length=Math.hypot(...sum);for(let k=0;k<3;k++)sum[k]/=length}
 for(const face of glassFaces)for(let corner=0;corner<3;corner++){const n=glassNormals.get(faces[face][corner]);for(let k=0;k<3;k++)normals[face*9+corner*3+k]=n[k]}
 return {positions,normals,colors,vertices,faces};
}
const cache=new WeakMap();
export function createModelGeometry(THREE,paint){
 let byPaint=cache.get(THREE);if(!byPaint){byPaint=new Map();cache.set(THREE,byPaint)}
 if(byPaint.has(paint))return byPaint.get(paint);
 const data=buildBodyData(paint),body=new THREE.BufferGeometry();
 for(const [name,values] of [['position',data.positions],['normal',data.normals],['color',data.colors]])body.setAttribute(name,new THREE.Float32BufferAttribute(values,3));
 const parts=[body];
 const add=(geo,color)=>{const g=geo.index?geo.toNonIndexed():geo;const c=new THREE.Color(color).convertSRGBToLinear(),values=[];for(let i=0;i<g.attributes.position.count;i++)values.push(c.r,c.g,c.b);g.setAttribute('color',new THREE.Float32BufferAttribute(values,3));parts.push(g)};
 for(const x of [-.78,.78])for(const z of [-1.27, 1.25]){
  add(new THREE.CylinderGeometry(.33,.33,.25,16,1,false).rotateZ(Math.PI/2).translate(x,.33,z),'#202426');
  add(new THREE.CylinderGeometry(.17,.17,.26,12,1,false).rotateZ(Math.PI/2).translate(x,.33,z),'#aab4b8');
 }
 for(const x of [-.60,.60])for(const z of [-1.27,1.25])add(new THREE.BoxGeometry(.06,.40,.80).translate(x,.52,z),'#202426');
 for(const z of [-2.34,2.34])add(new THREE.BoxGeometry(1.76,.16,.16).translate(0,.49,z),'#202426');
 for(const x of [-.57,.57]){
  add(new THREE.BoxGeometry(.36,.17,.025).translate(x,.77,-2.315),'#e6dfb9');
  add(new THREE.BoxGeometry(.29,.17,.025).translate(x,.77,2.315),'#b33530');
 }
 add(new THREE.BoxGeometry(.57,.14,.025).translate(0,.77,-2.315),'#202426');
 // Pillar bands are faces of the body shell, not floating box overlays.
 const result=new THREE.BufferGeometry();
 for(const name of ['position','normal','color']){
  const values=[];for(const g of parts)values.push(...g.attributes[name].array);
  result.setAttribute(name,new THREE.Float32BufferAttribute(values,3));
 }
 result.computeBoundingBox();result.computeBoundingSphere();
 for(const g of parts)g.dispose();byPaint.set(paint,result);return result;
}
