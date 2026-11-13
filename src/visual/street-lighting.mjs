// Pure placement and schedule; never consumes the gameplay RNG.
export function streetlightLevel(hour) {
  const h=((hour%24)+24)%24;
  const smooth=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t)};
  return h>=19?1:h<5?1:h<5.25?1-smooth((h-5)*4):0;
}
export function placeStreetlights(roads,widths,height,blocked) {
  const sites=[];
  for(const r of roads){
    if(r.c>2)continue;
    let remaining=18,side=1;
    for(let i=1;i<r.p.length;i++){
      const a=r.p[i-1],b=r.p[i],dx=b[0]-a[0],dz=b[1]-a[1],len=Math.hypot(dx,dz);
      if(!len)continue;
      for(let d=remaining;d<len;d+=52){
        const offset=widths[r.c]/2+2.5,x=a[0]+dx*d/len-dz/len*offset*side,z=a[1]+dz*d/len+dx/len*offset*side;
        side=-side;
        if(Math.abs(x)>1090||Math.abs(z)>1090||blocked(x,z))continue;
        // Reject slopes and all nearby road corridors (including footpaths).
        if(Math.abs(height(x+2,z)-height(x-2,z))>1||Math.abs(height(x,z+2)-height(x,z-2))>1)continue;
        if(sites.some(p=>(p[0]-x)**2+(p[1]-z)**2<36**2))continue;
        let overlaps=false;
        for(const road of roads){for(let k=1;k<road.p.length;k++){
          const c=road.p[k-1],e=road.p[k],vx=e[0]-c[0],vz=e[1]-c[1],l=vx*vx+vz*vz;
          const t=l?Math.max(0,Math.min(1,((x-c[0])*vx+(z-c[1])*vz)/l)):0;
          if(Math.hypot(x-c[0]-vx*t,z-c[1]-vz*t)<widths[road.c]/2+1.1){overlaps=true;break}
        }if(overlaps)break}
        if(!overlaps)sites.push([x,z]);
      }
      remaining=((remaining-len)%52+52)%52;
    }
  }
  return sites;
}
export function createStreetLighting(THREE,{scene,camera,roads,widths,height,blocked,coarse}) {
  const positions=placeStreetlights(roads,widths,height,blocked);
  const pole=new THREE.InstancedMesh(new THREE.CylinderGeometry(.07,.10,5.3,8),new THREE.MeshLambertMaterial({color:0x616766}),positions.length);
  const bulbMat=new THREE.MeshLambertMaterial({color:0xb7aa82,emissive:0xff8e24,emissiveIntensity:0});
  const bulbs=new THREE.InstancedMesh(new THREE.BoxGeometry(.85,.12,.32),bulbMat,positions.length);
  const matrix=new THREE.Matrix4();
  const cv=document.createElement('canvas');cv.width=cv.height=64;
  const ctx=cv.getContext('2d'),g=ctx.createRadialGradient(32,32,0,32,32,32);
  g.addColorStop(0,'rgba(255,207,125,.65)');g.addColorStop(.18,'rgba(255,162,47,.24)');g.addColorStop(1,'rgba(255,125,20,0)');ctx.fillStyle=g;ctx.fillRect(0,0,64,64);
  const haloMat=new THREE.SpriteMaterial({map:new THREE.CanvasTexture(cv),color:0xffb258,transparent:true,depthTest:true,depthWrite:false,opacity:0});
  const halos=[];
  positions.forEach(([x,z],i)=>{
    const y=height(x,z);matrix.makeTranslation(x,y+2.65,z);pole.setMatrixAt(i,matrix);
    matrix.makeTranslation(x+.35,y+5.25,z);bulbs.setMatrixAt(i,matrix);
    const sprite=new THREE.Sprite(haloMat);sprite.position.set(x+.35,y+5.25,z);sprite.scale.set(3.4,3.4,1);scene.add(sprite);halos.push(sprite);
  });
  scene.add(pole,bulbs);
  // Fixed pool: no shader light-count changes while driving, no shadow maps.
  const pool=Array.from({length:coarse?2:4},()=>{const light=new THREE.PointLight(0xff9b32,0,26,2);scene.add(light);return light});
  const selected=new Int32Array(pool.length);let mode='auto',level=0,active=0;
  function update(dt,hour){
    const target=mode==='on'?1:mode==='off'?0:streetlightLevel(hour);
    level+=(target-level)*(dt===0?1:1-Math.exp(-dt*4));
    bulbMat.emissiveIntensity=level*1.8;haloMat.opacity=level;
    for(let k=0;k<pool.length;k++){
      let best=-1,distance=85*85;
      for(let i=0;i<positions.length;i++){
        let used=false;for(let j=0;j<k;j++)if(selected[j]===i)used=true;
        if(used)continue;
        const p=positions[i],d=(p[0]-camera.position.x)**2+(p[1]-camera.position.z)**2;
        if(d<distance){distance=d;best=i}
      }
      selected[k]=best;const light=pool[k];
      light.intensity=best<0?0:level*3.8;
      if(best>=0){const p=positions[best];light.position.set(p[0]+.35,height(p[0],p[1])+4.9,p[1])}
    }
    active=0;for(const light of pool)if(light.intensity>.01)active++;
    for(let i=0;i<halos.length;i++){const p=positions[i];halos[i].visible=level>.005&&(p[0]-camera.position.x)**2+(p[1]-camera.position.z)**2<180**2}
  }
  return {update,setMode(value){mode=value},getMode:()=>mode,stats:()=>({count:positions.length,budget:pool.length,active,level}),positions};
}
