// Playable-night lighting for the r128 standalone game.
// Geometry/glow is cheap and instanced where possible. Real local lighting uses
// a fixed pool of unshadowed lights, not one costly light per window/car.
export function windowSites(buildings,hAt,roadDistance){
  const sites=[];
  for(let bi=0;bi<buildings.length;bi++){
    const b=buildings[bi],p=b.p;
    if(b.k!==0||!p||p.length<8)continue;
    // A deterministic subset of occupied houses; never consume gameplay RNG.
    const hash=((Math.imul(bi+1,1103515245)>>>0)%1000)/1000;
    if(hash>.43)continue;
    const n=p.length/2;
    let area=0;
    for(let i=0;i<n;i++){const j=(i+1)%n;area+=p[2*i]*p[2*j+1]-p[2*j]*p[2*i+1];}
    const side=area>=0?1:-1;
    let best=null;
    for(let i=0;i<n;i++){
      const j=(i+1)%n,ax=p[2*i],az=p[2*i+1],bx=p[2*j],bz=p[2*j+1];
      const dx=bx-ax,dz=bz-az,len=Math.hypot(dx,dz);
      if(len<6.5)continue;
      const nx=side*dz/len,nz=-side*dx/len;
      const cx=(ax+bx)*.5,cz=(az+bz)*.5;
      const d=roadDistance(cx+nx*2,cz+nz*2);
      if(!Number.isFinite(d)||d>12)continue;
      const score=d-len*.014;
      if(!best||score<best.score)best={ax,az,dx,dz,len,nx,nz,score};
    }
    if(!best)continue;
    const xs=best.len>10.5?[.26,.74]:[.57];
    for(const u of xs){
      const x=best.ax+best.dx*u+best.nx*.16,z=best.az+best.dz*u+best.nz*.16;
      const y=hAt(x,z)+1.64;
      if([x,y,z].every(Number.isFinite))sites.push({x,y,z,nx:best.nx,nz:best.nz,buildingIndex:bi});
    }
  }
  return sites;
}
export function createWindowLighting(THREE,{scene,camera,buildings,hAt,nearestRoad,coarse}){
  const sites=windowSites(buildings,hAt,(x,z)=>nearestRoad(x,z).d);
  const color=new THREE.Color(),position=new THREE.Vector3(),scale=new THREE.Vector3(1,1,1),
        normal=new THREE.Vector3(),front=new THREE.Vector3(0,0,1),quaternion=new THREE.Quaternion(),matrix=new THREE.Matrix4();
  const mat=new THREE.MeshBasicMaterial({color:0xffd3a0,transparent:true,opacity:0,depthWrite:false,
    side:THREE.DoubleSide,toneMapped:false});
  const quads=new THREE.InstancedMesh(new THREE.PlaneGeometry(.92,1.05),mat,sites.length);
  const shades=[0xffc47a,0xf6d9a3,0xffa95e,0xffe5b8];
  for(let i=0;i<sites.length;i++){
    const p=sites[i];
    position.set(p.x,p.y,p.z);normal.set(p.nx,0,p.nz);
    quaternion.setFromUnitVectors(front,normal);
    matrix.compose(position,quaternion,scale);quads.setMatrixAt(i,matrix);
    color.setHex(shades[(p.buildingIndex*7+i)%shades.length]);quads.setColorAt(i,color);
  }
  quads.instanceMatrix.needsUpdate=true;
  quads.frustumCulled=false;quads.visible=false;scene.add(quads);
  const pool=Array.from({length:coarse?0:1},()=>{
    const light=new THREE.PointLight(0xffbc7a,0,11,2);scene.add(light);return light;
  });
  function update(level){
    quads.visible=level>.03;mat.opacity=.86*level;
    for(const light of pool){
      let best=null,dist=32*32;
      for(const p of sites){
        const d=(p.x-camera.position.x)**2+(p.z-camera.position.z)**2;
        if(d<dist){dist=d;best=p}
      }
      light.visible=!!best&&level>.04;
      light.intensity=light.visible?level*.95:0;
      if(best)light.position.set(best.x+best.nx*.7,best.y,best.z+best.nz*.7);
    }
  }
  return {update,stats:()=>({windows:sites.length,active:quads.visible?sites.length:0,localLights:pool.length})};
}
export function createVehicleLighting(THREE,{scene,coarse}){
  const bulbMat=new THREE.MeshBasicMaterial({color:0xfff0ca,transparent:true,opacity:0,
    depthWrite:false,side:THREE.DoubleSide,toneMapped:false});
  const geometries=new Map(),lamps=new Map(),tails=new Map();
  const rearMat=new THREE.MeshBasicMaterial({color:0xff301c,transparent:true,opacity:.82,
    depthWrite:false,side:THREE.DoubleSide,toneMapped:false});
  const brakeMat=new THREE.MeshBasicMaterial({color:0xff7260,transparent:true,opacity:.95,
    depthWrite:false,side:THREE.DoubleSide,toneMapped:false});
  const cv=document.createElement('canvas');cv.width=cv.height=64;
  const ctx=cv.getContext('2d'),glow=ctx.createRadialGradient(32,32,2,32,32,31);
  glow.addColorStop(0,'rgba(255,105,72,.85)');
  glow.addColorStop(.27,'rgba(255,64,35,.30)');
  glow.addColorStop(1,'rgba(255,45,20,0)');
  ctx.fillStyle=glow;ctx.fillRect(0,0,64,64);
  const glowTexture=new THREE.CanvasTexture(cv);
  const tailHaloMat=new THREE.SpriteMaterial({map:glowTexture,color:0xff6550,
    transparent:true,opacity:.38,depthWrite:false,depthTest:true});
  function geometryFor(type){
    const tractor=type==='traktor'||type==='newHolland'||type==='johnDeere';
    const key=tractor?'tractor':type==='saab'?'saab':'car';
    if(geometries.has(key))return geometries.get(key);
    const z=tractor?-2.22:key==='saab'?-2.34:-2.46;
    const y=tractor?1.46:.78,x=tractor?.41:.64,w=tractor?.19:.24,h=.13;
    const pos=[];
    for(const side of [-1,1]){
      const cx=side*x,a=cx-w,b=cx+w,bottom=y-h,top=y+h;
      pos.push(a,bottom,z,b,bottom,z,b,top,z,a,bottom,z,b,top,z,a,top,z);
    }
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
    geo.computeVertexNormals();geometries.set(key,geo);return geo;
  }
  function tailGeometry(type){
    const tractor=type==='traktor'||type==='newHolland'||type==='johnDeere';
    const z=tractor?2.03:type==='saab'?2.30:2.39;
    const y=tractor?1.28:.84,x=tractor?.53:.64,w=tractor?.16:.21,h=.16;
    const pos=[];
    for(const side of [-1,1]){
      const a=side*x-w,b=side*x+w;
      pos.push(a,y-h,z,b,y-h,z,b,y+h,z,a,y-h,z,b,y+h,z,a,y+h,z);
    }
    const geo=new THREE.BufferGeometry();
    geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
    geo.computeVertexNormals();return {geo,x,y,z};
  }
  function attach(body,type,car){
    const mesh=new THREE.Mesh(geometryFor(type),bulbMat);body.add(mesh);lamps.set(car,mesh);
    const rear=tailGeometry(type);
    const rearMesh=new THREE.Mesh(rear.geo,rearMat),brakeMesh=new THREE.Mesh(rear.geo,brakeMat);
    brakeMesh.position.z=.012;brakeMesh.visible=false;
    body.add(rearMesh,brakeMesh);
    const halos=[];
    for(const side of [-1,1]){
      const sprite=new THREE.Sprite(tailHaloMat);
      sprite.position.set(side*rear.x,rear.y,rear.z+.045);
      sprite.scale.set(1.25,1.1,1);body.add(sprite);halos.push(sprite);
    }
    tails.set(car,{rearMesh,brakeMesh,halos});
  }
  const pool=Array.from({length:coarse?1:2},()=>{
    const lamp=new THREE.SpotLight(0xffe9c3,0,45,Math.PI/5,.65,1.5);
    lamp.castShadow=false;scene.add(lamp,lamp.target);return lamp;
  });
  function update(cars,playerCar,camera,level){
    // Attach lazily: compatible with both the original Mesh and the
    // suspension BodyRig introduced in the separate driving PR.
    for(const c of cars)if(!lamps.has(c)){
      const parent=c.bodyRig?c.bodyRig.children[0]:c.mesh;
      if(parent)attach(parent,c.type,c);
    }
    for(const [c,m] of lamps)if(!cars.includes(c)){
      if(m.parent)m.parent.remove(m);
      lamps.delete(c);
      const rear=tails.get(c);
      if(rear){
        for(const part of [rear.rearMesh,rear.brakeMesh,...rear.halos])
          if(part.parent)part.parent.remove(part);
        rear.rearMesh.geometry.dispose();
        tails.delete(c);
      }
    }
    bulbMat.opacity=level*.98;
    const lit=level>.03;
    for(const [c,m] of lamps)m.visible=lit&&['ai','player','police'].includes(c.mode);
    for(const [c,rear] of tails){
      const active=['ai','player','police'].includes(c.mode);
      const dist=(c.x-camera.position.x)**2+(c.z-camera.position.z)**2;
      const close=dist<190*190;
      rear.rearMesh.visible=active&&lit;
      rear.brakeMesh.visible=active&&lit&&!!c.braking;
      for(const halo of rear.halos){
        halo.visible=active&&lit&&close;
        if(halo.visible){
          const fade=Math.max(0,Math.min(1,(190-Math.sqrt(dist))/45));
          halo.scale.set(1.25*fade,1.1*fade,1);
        }
      }
    }
    tailHaloMat.opacity=level*.34;
    const active=cars.filter(c=>['player','police','ai'].includes(c.mode)
       &&(c.x-camera.position.x)**2+(c.z-camera.position.z)**2<135*135);
    active.sort((a,b)=>(a===playerCar?-1:b===playerCar?1:0)||
      ((a.x-camera.position.x)**2+(a.z-camera.position.z)**2
      -(b.x-camera.position.x)**2-(b.z-camera.position.z)**2));
    for(let i=0;i<pool.length;i++){
      const light=pool[i],c=active[i];
      light.visible=!!c&&level>.04;
      light.intensity=light.visible?level*5.2:0;
      if(!c)continue;
      const fx=Math.sin(c.h),fz=-Math.cos(c.h);
      const tractor=c.type==='newHolland'||c.type==='johnDeere'||c.type==='traktor';
      const height=tractor?1.46:.84,d=tractor?1.9:2.1;
      const y=c.mesh.position.y+height;
      light.position.set(c.x+fx*d,y,c.z+fz*d);
      light.target.position.set(c.x+fx*36,y-.65,c.z+fz*36);
    }
  }
  return {attach,update,stats:()=>({carFixtures:lamps.size,beamBudget:pool.length})};
}
