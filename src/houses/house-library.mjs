// Residential house catalogue for the playable Vrigstad map.
// Each archetype is built ONCE as a complete mesh and reused by InstancedMesh.
// GIS footprints are used for placement, not as a source for per-house modelling.
export const HOUSE_TYPES = {
  cottage: { length: 10.5, width: 8.0, wallHeight: 3.15, ridgeHeight: 5.65, roof: 'gable' },
  bungalow: { length: 13.0, width: 9.2, wallHeight: 3.28, ridgeHeight: 4.62, roof: 'hip' },
  villa80: { length: 12.0, width: 8.8, wallHeight: 3.75, ridgeHeight: 6.25, roof: 'gable' }
};

const PALETTES = {
  cottage: {
    red: { wall:'#843b30', groove:'#75352d', trim:'#e7e5db', roof:'#534840', foundation:'#6e6e65', door:'#425564' },
    yellow: { wall:'#b99550', groove:'#a88a47', trim:'#f0eee4', roof:'#8b5948', foundation:'#747269', door:'#566e71' },
    cream: { wall:'#d7d3c7', groove:'#c8c4b7', trim:'#f4f0e8', roof:'#5f5a58', foundation:'#71716e', door:'#59717b' }
  },
  bungalow: {
    mexi: { wall:'#c7c6ba', groove:'#b5b3a9', trim:'#ddd9ce', roof:'#5d5551', foundation:'#71716a', door:'#564a43' },
    brick: { wall:'#9e7865', groove:'#836858', trim:'#dedbd2', roof:'#4b4746', foundation:'#71716a', door:'#4c5957' },
    ochre: { wall:'#bda46b', groove:'#a68e61', trim:'#e7e3d7', roof:'#5d5551', foundation:'#74726d', door:'#4e625c' }
  },
  villa80: {
    red: { wall:'#934739', groove:'#7d4035', trim:'#ebe7dc', roof:'#4f4e4d', foundation:'#77746e', door:'#36575c' },
    green: { wall:'#70867d', groove:'#60756e', trim:'#eceae2', roof:'#4a4c4c', foundation:'#73736d', door:'#734d45' },
    cream: { wall:'#d7d3c7', groove:'#c6c1b7', trim:'#f2eee5', roof:'#8a6150', foundation:'#73716c', door:'#48606b' }
  }
};

export function houseSkin(type, wallHex, hash) {
  const red = wallHex === '#843b30' || wallHex === '#934739';
  const yellow = wallHex === '#b99550' || wallHex === '#c2a66a';
  const green = wallHex === '#70867d' || wallHex === '#778c80';
  if (type === 'cottage') return red ? 'red' : yellow ? 'yellow' : 'cream';
  if (type === 'bungalow') return red ? 'brick' : yellow ? 'ochre' : 'mexi';
  return red ? 'red' : green ? 'green' : (hash & 3) === 0 ? 'green' : 'cream';
}

export function footprintRect(p) {
  const n=p.length/2;
  if(n<4)return null;
  const pts=Array.from({length:n},(_,i)=>[p[i*2],p[i*2+1]]);
  let shoelace=0;
  for(let i=0;i<n;i++){
    const a=pts[i],b=pts[(i+1)%n];
    shoelace+=a[0]*b[1]-b[0]*a[1];
  }
  const area=Math.abs(shoelace)/2;
  let best=null;
  for(let i=0;i<n;i++){
    const a=pts[i],b=pts[(i+1)%n],dx=b[0]-a[0],dz=b[1]-a[1],edge=Math.hypot(dx,dz);
    if(edge<1)continue;
    let ux=dx/edge,uz=dz/edge,vx=-uz,vz=ux;
    let u0=Infinity,u1=-Infinity,v0=Infinity,v1=-Infinity;
    for(const q of pts){
      const u=q[0]*ux+q[1]*uz,v=q[0]*vx+q[1]*vz;
      u0=Math.min(u0,u);u1=Math.max(u1,u);v0=Math.min(v0,v);v1=Math.max(v1,v);
    }
    let length=u1-u0,width=v1-v0;
    const boxArea=length*width;
    if(boxArea<1)continue;
    if(width>length){
      // Swap axes, preserving a right-handed local XZ basis.
      const oldU=ux,oldZ=uz;
      ux=vx;uz=vz;vx=-oldU;vz=-oldZ;
      let nu0=Infinity,nu1=-Infinity,nv0=Infinity,nv1=-Infinity;
      for(const q of pts){const u=q[0]*ux+q[1]*uz,v=q[0]*vx+q[1]*vz;
        nu0=Math.min(nu0,u);nu1=Math.max(nu1,u);nv0=Math.min(nv0,v);nv1=Math.max(nv1,v);}
      u0=nu0;u1=nu1;v0=nv0;v1=nv1;
      length=u1-u0;width=v1-v0;
    }
    const fit=area/(length*width);
    if(!best||fit>best.fit+1e-6||(Math.abs(fit-best.fit)<=1e-6&&edge>best.edge)){
      const um=(u0+u1)/2,vm=(v0+v1)/2;
      best={cx:um*ux+vm*vx,cz:um*uz+vm*vz,length,width,ux,uz,fit,area,edge,yaw:-Math.atan2(uz,ux)};
    }
  }
  return best;
}

export function createHouseGeometry(THREE, type, skin, entrance) {
  const spec=HOUSE_TYPES[type],pal=PALETTES[type]?.[skin];
  if(!spec||!pal||!['+x','-x','+z','-z'].includes(entrance))throw Error('Unknown house type/skin/entry');
  const L=spec.length,W=spec.width,e=spec.wallHeight,r=spec.ridgeHeight;
  const positions=[],colors=[],c={};
  for(const [key,value] of Object.entries(pal))c[key]=new THREE.Color(value);
  c.glass=new THREE.Color('#304953');
  c.glassEdge=new THREE.Color('#203842');
  c.sill=new THREE.Color('#bcbab0');
  c.chimney=new THREE.Color('#8a6154');
  c.roofTrim=new THREE.Color('#77706a');
  c.knob=new THREE.Color('#c5b085');
  const push=(p,col)=>{positions.push(p[0],p[1],p[2]);colors.push(col.r,col.g,col.b);};
  const tri=(a,b,d,col)=>{push(a,col);push(b,col);push(d,col);};
  const quad=(a,b,d,f,col)=>{tri(a,b,d,col);tri(a,d,f,col);};
  function box(x0,y0,z0,x1,y1,z1,col){
    if(!(x1>x0&&y1>y0&&z1>z0))return;
    quad([x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],col);
    quad([x0,y0,z1],[x0,y1,z1],[x1,y1,z1],[x1,y0,z1],col);
    quad([x0,y0,z0],[x0,y1,z0],[x0,y1,z1],[x0,y0,z1],col);
    quad([x1,y0,z0],[x1,y0,z1],[x1,y1,z1],[x1,y1,z0],col);
    quad([x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1],col);
    quad([x0,y0,z0],[x0,y0,z1],[x1,y0,z1],[x1,y0,z0],col);
  }
  // Reusable complete shell: facade, cellar plinth and either gable or hip roof.
  box(-L/2,0,-W/2,L/2,e,W/2,c.wall);
  box(-L/2-.025,0,-W/2-.025,L/2+.025,.34,W/2+.025,c.foundation);
  const X=L/2+.35,Z=W/2+.42,roofE=e+.08;
  if(spec.roof==='gable'){
    for(const x of [-L/2,L/2])
      tri([x,e,-W/2],[x,r,0],[x,e,W/2],c.wall);
    quad([-X,roofE,-Z],[X,roofE,-Z],[X,r,0],[-X,r,0],c.roof);
    quad([-X,r,0],[X,r,0],[X,roofE,Z],[-X,roofE,Z],c.roof);
    box(-X,r-.06,-.105,X,r+.04,.105,c.roofTrim);
    for(const z of [-Z,Z])box(-X,roofE-.08,z-.055,X,roofE+.06,z+.055,c.roofTrim);
  } else {
    const hx=L/2-1.35;
    quad([-X,roofE,-Z],[X,roofE,-Z],[hx,r,0],[-hx,r,0],c.roof);
    quad([-hx,r,0],[hx,r,0],[X,roofE,Z],[-X,roofE,Z],c.roof);
    tri([X,roofE,-Z],[X,roofE,Z],[hx,r,0],c.roof);
    tri([-X,roofE,Z],[-X,roofE,-Z],[-hx,r,0],c.roof);
    box(-hx,r-.06,-.09,hx,r+.04,.09,c.roofTrim);
  }
  // A shallow soffit and fascia keep the eaves visually separate from the wall.
  for(const z of [-Z,Z])box(-X,roofE-.12,z-.07,X,roofE+.02,z+.07,c.roofTrim);
  // Add facade details to each of the four sides in fixed template coordinates.
  function panel(side,along,w,y0,y1,offset,col){
    if(y1<=y0||w<=0)return;
    const h=w/2;
    if(side.endsWith('z')){
      const z=(side[0]==='+'?1:-1)*(W/2+offset);
      quad([along-h,y0,z],[along+h,y0,z],[along+h,y1,z],[along-h,y1,z],col);
    }else{
      const x=(side[0]==='+'?1:-1)*(L/2+offset);
      quad([x,y0,along-h],[x,y0,along+h],[x,y1,along+h],[x,y1,along-h],col);
    }
  }
  function windowOn(side,along,y0=1.05,w=1.18,h=1.22){
    const y1=y0+h;
    panel(side,along,w+.19,y0-.105,y1+.105,.048,c.trim);
    panel(side,along,w,y0,y1,.065,c.glassEdge);
    panel(side,along,w-.12,y0+.06,y1-.06,.078,c.glass);
    panel(side,along,.065,y0+.045,y1-.045,.087,c.trim);
    panel(side,along,w-.07,y0+h*.50-.035,y0+h*.50+.035,.092,c.trim);
    panel(side,along,w+.28,y0-.15,y0-.075,.103,c.sill);
  }
  function doorOn(side){
    panel(side,0,1.16,.11,2.37,.052,c.trim);
    panel(side,0,.94,.17,2.25,.075,c.door);
    panel(side,.31,.07,1.08,1.17,.085,c.knob);
    if(side==='+z')box(-.74,0,W/2+.01,.74,.18,W/2+.68,c.foundation);
    else if(side==='-z')box(-.74,0,-W/2-.68,.74,.18,-W/2-.01,c.foundation);
    else if(side==='+x')box(L/2+.01,0,-.74,L/2+.68,.18,.74,c.foundation);
    else box(-L/2-.68,0,-.74,-L/2-.01,.18,.74,c.foundation);
  }
  for(const side of ['+z','-z','+x','-x']){
    const longWall=side.endsWith('z'),span=longWall?L:W;
    // Broad timber boards (25-27 cm); 70s brick gets horizontal mortar courses.
    if(type==='bungalow'){
      for(let y=.50;y<e-.18;y+=.31)panel(side,0,span-.08,y,y+.025,.025,c.groove);
    }else{
      for(let v=-span/2+.28;v<span/2-.16;v+=.27)
        panel(side,v,.012,.35,e-.03,.026,c.groove);
      // Corner boards are geometry on both sides of the corner, not extra world objects.
      panel(side,-span/2+.11,.19,.33,e+.04,.051,c.trim);
      panel(side,span/2-.11,.19,.33,e+.04,.051,c.trim);
    }
    if(longWall){
      const centers=type==='bungalow'?[-L*.32,0,L*.32]:[-L*.30,0,L*.30];
      for(const at of centers)if(!(side===entrance&&Math.abs(at)<.1))
        windowOn(side,at,type==='bungalow'?1.01:1.10,type==='bungalow'?1.53:1.16,1.23);
    }else if(side!==entrance){
      windowOn(side,0,1.08,1.24,1.24);
    }
    if(side===entrance)doorOn(side);
  }
  // Attic window distinguishes the 1½-storey Swedish villa from the bungalow.
  if(type==='villa80')for(const side of ['+x','-x']){
    panel(side,0,.97,e+.38,e+1.27,.048,c.trim);
    panel(side,0,.80,e+.46,e+1.20,.072,c.glass);
    panel(side,0,.055,e+.45,e+1.20,.086,c.trim);
  }
  if(type!=='bungalow')
    box(-L*.22-.27,e+1.35,-.30,-L*.22+.27,r+.85,.30,c.chimney);
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  geometry.computeVertexNormals();
  return geometry;
}
