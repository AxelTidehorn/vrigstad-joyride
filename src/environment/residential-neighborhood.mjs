// Residential landscape layer for the real, playable Vrigstad map.
// Deliberately conservative: every feature is computed once and omitted
// rather than guessed when road/lot/terrain geometry cannot support it.
// Footprints, collisions, traffic, safehouses and land use are never changed.

export function createResidentialNeighborhood(THREE, scene, env) {
  const {sites, buildings, roads, roadWidths, hAt, inPoly, protectedCenters=[]} = env;
  const stats={candidates:sites.length,walks:0,drives:0,fences:0,hedges:0,walls:0,trees:0,skipped:0};
  const hash=(n,s=0)=>{let x=(n+Math.imul(s+1,0x9e3779b1))|0;
    x^=x>>>16;x=Math.imul(x,0x7feb352d);x^=x>>>15;
    x=Math.imul(x,0x846ca68b);return (x^x>>>16)>>>0;};
  const chance=(seed,n)=>hash(seed,n)/4294967295;
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  const len=(dx,dz)=>Math.hypot(dx,dz);
  const boxes=buildings.map((b,i)=>{
    let minX=Infinity,maxX=-Infinity,minZ=Infinity,maxZ=-Infinity;
    for(let j=0;j<b.p.length;j+=2){
      minX=Math.min(minX,b.p[j]);maxX=Math.max(maxX,b.p[j]);
      minZ=Math.min(minZ,b.p[j+1]);maxZ=Math.max(maxZ,b.p[j+1]);
    }
    return {i,p:b.p,minX,maxX,minZ,maxZ,cx:(minX+maxX)/2,cz:(minZ+maxZ)/2};
  });
  const sectors=new Map(),gridSize=45;
  function put(grid,cx,cz,item){const k=cx+','+cz;let v=grid.get(k);if(!v)grid.set(k,v=[]);v.push(item);}
  for(const b of boxes)for(let x=Math.floor((b.minX-3)/gridSize);x<=Math.floor((b.maxX+3)/gridSize);x++)
    for(let z=Math.floor((b.minZ-3)/gridSize);z<=Math.floor((b.maxZ+3)/gridSize);z++)put(sectors,x,z,b);
  function nearbyBuildings(x,z){return sectors.get(Math.floor(x/gridSize)+','+Math.floor(z/gridSize))||[];}
  function buildingBlocked(x,z,except=-1,margin=.50){
    for(const b of nearbyBuildings(x,z)){
      if(b.i===except||x<b.minX-margin||x>b.maxX+margin||z<b.minZ-margin||z>b.maxZ+margin)continue;
      if(inPoly(b.p,x,z))return true;
      for(let j=0;j<b.p.length;j+=2){
        const k=(j+2)%b.p.length,ax=b.p[j],az=b.p[j+1],dx=b.p[k]-ax,dz=b.p[k+1]-az;
        const t=clamp(((x-ax)*dx+(z-az)*dz)/(dx*dx+dz*dz||1),0,1);
        if(len(x-ax-dx*t,z-az-dz*t)<margin)return true;
      }
    }
    return false;
  }
  function blockedPolyline(points,except,clearance=.65){
    for(let i=1;i<points.length;i++){
      const a=points[i-1],b=points[i],dist=len(b.x-a.x,b.z-a.z),steps=Math.ceil(dist/1.0);
      for(let j=0;j<=steps;j++){
        if(i===1&&j<2)continue; // step starts just outside its own entry
        const t=j/steps,x=a.x+(b.x-a.x)*t,z=a.z+(b.z-a.z)*t;
        if(buildingBlocked(x,z,except,clearance))return true;
      }
    }
    return false;
  }
  const roadSegments=[];
  for(const r of roads){
    if(r.c>3)continue;
    for(let i=1;i<r.p.length;i++){
      const a=r.p[i-1],b=r.p[i],dx=b[0]-a[0],dz=b[1]-a[1],length=len(dx,dz);
      if(length<1.2)continue;
      roadSegments.push({x:a[0],z:a[1],dx,dz,L2:dx*dx+dz*dz,len:length,c:r.c,w:roadWidths[r.c]});
    }
  }
  const roadsGrid=new Map();
  for(const seg of roadSegments){
    const xmin=Math.min(seg.x,seg.x+seg.dx)-25,xmax=Math.max(seg.x,seg.x+seg.dx)+25;
    const zmin=Math.min(seg.z,seg.z+seg.dz)-25,zmax=Math.max(seg.z,seg.z+seg.dz)+25;
    for(let x=Math.floor(xmin/gridSize);x<=Math.floor(xmax/gridSize);x++)
      for(let z=Math.floor(zmin/gridSize);z<=Math.floor(zmax/gridSize);z++)put(roadsGrid,x,z,seg);
  }
  function roadNear(x,z){
    const arr=roadsGrid.get(Math.floor(x/gridSize)+','+Math.floor(z/gridSize))||[];
    let best=null;
    for(const seg of arr){
      const t=clamp(((x-seg.x)*seg.dx+(z-seg.z)*seg.dz)/seg.L2,0,1);
      const cx=seg.x+t*seg.dx,cz=seg.z+t*seg.dz,d=len(x-cx,z-cz)-seg.w/2;
      if(!best||d<best.d)best={seg,t,cx,cz,d};
    }
    return best;
  }
  const surface={p:[],c:[]};
  const surfaceColors={
    gravel:new THREE.Color('#8e887a'),
    stone:new THREE.Color('#a7a59d'),
    slabs:new THREE.Color('#989994'),
    asphalt:new THREE.Color('#585d5d'),
    concrete:new THREE.Color('#898987')
  };
  function strip(a,b,width,style,roadLift=0){
    const col=surfaceColors[style],dx=b.x-a.x,dz=b.z-a.z,dist=len(dx,dz);
    if(dist<.5)return;
    const nx=-dz/dist,nz=dx/dist,segments=Math.ceil(dist/.95);
    let prev=null;
    for(let i=0;i<=segments;i++){
      const t=i/segments,x=a.x+dx*t,z=a.z+dz*t;
      // Ramp to the raised road mesh only at the actual street connection.
      const r=roadLift*Math.max(0,1-(dist*(1-t)/1.8));
      const v0=[x+nx*width/2,hAt(x+nx*width/2,z+nz*width/2)+.055+r,z+nz*width/2];
      const v1=[x-nx*width/2,hAt(x-nx*width/2,z-nz*width/2)+.055+r,z-nz*width/2];
      if(prev){
        for(const q of [prev[0],prev[1],v1,prev[0],v1,v0]){
          surface.p.push(...q);surface.c.push(col.r,col.g,col.b);
        }
      }
      prev=[v0,v1];
    }
  }
  const boxesBatches=new Map();
  function box(kind,x,z,y,sx,sy,sz,yaw=0,color=null){
    const k=kind;
    if(!boxesBatches.has(k))boxesBatches.set(k,[]);
    boxesBatches.get(k).push({x,z,y,sx,sy,sz,yaw,color});
  }
  const hedgeBatches=[];
  const trees=[];
  const placedTreePositions=[];
  const treeKinds=['small','mature','apple','spruce'];
  function addTree(x,z,kind,seed,exclude){
    const h=kind==='mature'?7.2:kind==='spruce'?6.3:kind==='small'?4.8:3.7;
    if(buildingBlocked(x,z,exclude,2.3))return false;
    const rd=roadNear(x,z);
    if(rd&&rd.d<3.2)return false;
    if(protectedCenters.some(q=>len(x-q[0],z-q[1])<q[2]))return false;
    if(placedTreePositions.some(p=>len(x-p[0],z-p[1])<4.0))return false;
    const slope=Math.max(...[[1,0],[-1,0],[0,1],[0,-1]].map(([dx,dz])=>Math.abs(hAt(x,z)-hAt(x+dx*2,z+dz*2))));
    if(slope>1.0)return false;
    trees.push({x,z,y:hAt(x,z),h:h*(.90+.20*chance(seed,31)),kind,seed});
    placedTreePositions.push([x,z]);stats.trees++;
    return true;
  }
  const frontageOccupied=[];
  function overlappingFrontage(x,z,ux,uz,half){
    for(const f of frontageOccupied){
      const dx=x-f.x,dz=z-f.z,along=Math.abs(dx*ux+dz*uz);
      const normal=Math.abs(dx*(-uz)+dz*ux);
      if(normal<3.8&&along<(half+f.half-1.1))return true;
    }
    return false;
  }
  const sorted=sites.slice().sort((a,b)=>a.bi-b.bi);
  for(const site of sorted){
    const seed=hash(site.bi,Math.round(site.x*10));
    if(site.area<52||site.area>450||site.kind!==0||
      protectedCenters.some(q=>len(site.x-q[0],site.z-q[1])<q[2])||
      chance(seed,0)<.32){stats.skipped++;continue;}
    const near=roadNear(site.entryX,site.entryZ);
    if(!near||near.d<.35||near.d>21.0){stats.skipped++;continue;}
    const seg=near.seg,tanX=seg.dx/seg.len,tanZ=seg.dz/seg.len;
    const dirX=site.entryX-near.cx,dirZ=site.entryZ-near.cz,distToAxis=len(dirX,dirZ);
    if(distToAxis<seg.w/2+1.2)continue;
    const roadDirection=(near.cx-site.entryX)*site.normalX+(near.cz-site.entryZ)*site.normalZ;
    if(roadDirection<1.0)continue;
    const nx=dirX/distToAxis,nz=dirZ/distToAxis;
    const edge={x:near.cx+nx*(seg.w/2+.32),z:near.cz+nz*(seg.w/2+.32)};
    const entry={x:site.entryX,z:site.entryZ};
    if(len(entry.x-edge.x,entry.z-edge.z)<1||len(entry.x-edge.x,entry.z-edge.z)>19)continue;
    if(blockedPolyline([entry,edge],site.bi,.55)){stats.skipped++;continue;}
    const rise=Math.abs(hAt(entry.x,entry.z)-hAt(edge.x,edge.z));
    if(rise>2.4)continue;

    // The footpath determines the future opening, not the opposite way around.
    const style=['gravel','stone','slabs'][hash(seed,1)%3];
    strip(entry,edge,1.08,style,.25-seg.c*.03);
    stats.walks++;
    let drive=null;
    if(site.area>=85&&site.area<410&&chance(seed,2)>.55){
      // Estimate a usable side yard from the actual polygon, not a made-up lot.
      let min=Infinity,max=-Infinity;
      for(let j=0;j<site.poly.length;j+=2){
        const t=(site.poly[j]-site.x)*tanX+(site.poly[j+1]-site.z)*tanZ;
        min=Math.min(min,t);max=Math.max(max,t);
      }
      const left=hash(seed,3)%2===0;
      const offset=left?min-2.25:max+2.25;
      if(Math.abs(offset)<14.5&&Math.abs(offset)>3.0){
        const end={x:site.x+tanX*offset-nx*.8,z:site.z+tanZ*offset-nz*.8};
        const begin={x:edge.x+tanX*offset,z:edge.z+tanZ*offset};
        if(len(begin.x-end.x,begin.z-end.z)<22 &&
           !blockedPolyline([end,begin],site.bi,.90) &&
           !buildingBlocked(end.x,end.z,site.bi,1.7)){
          drive={begin,end,offset,width:2.7};
          strip(end,begin,drive.width,['gravel','asphalt','concrete'][hash(seed,4)%3],.25-seg.c*.03);
          stats.drives++;
        }
      }
    }

    // The fence/hard boundary is just beyond the roadway, parallel to it.
    // Openings are derived from the intersection with the real footpath and
    // side driveway. A blocked gap cannot be produced by this construction.
    if(chance(seed,5)>.30){
      const gapDepth=2.10,denom=(entry.x-edge.x)*nx+(entry.z-edge.z)*nz;
      if(denom>gapDepth+.3){
        const alpha=gapDepth/denom;
        const gateX=edge.x+(entry.x-edge.x)*alpha;
        const gateZ=edge.z+(entry.z-edge.z)*alpha;
        const half=7.2+chance(seed,6)*3.7;
        const ux=tanX,uz=tanZ;
        if(!overlappingFrontage(gateX,gateZ,ux,uz,half)){
          let style=hash(seed,7)%4; // hedge, white pickets, stone wall, rail
          const openings=[{a:-.78,b:.78}];
          if(drive){
            const gx=edge.x+tanX*drive.offset+nx*gapDepth;
            const gz=edge.z+tanZ*drive.offset+nz*gapDepth;
            const offset=(gx-gateX)*ux+(gz-gateZ)*uz;
            openings.push({a:offset-1.65,b:offset+1.65});
          }
          let included=0;
          for(let u=-half;u<half-0.3;u+=1.25){
            const center=u+.625;
            if(openings.some(o=>u<o.b+.12&&u+1.25>o.a-.12))continue;
            const x=gateX+ux*center,z=gateZ+uz*center,y=hAt(x,z);
            if(buildingBlocked(x,z,site.bi,.70))continue;
            const road=roadNear(x,z);
            if(road && road.d<.5)continue;
            if(style===0){
              const height=.85+.29*chance(seed,Math.round(u*11));
              hedgeBatches.push({x,z,y:y+height*.43,height,angle:-Math.atan2(uz,ux),
                color:hash(seed,Math.round(u*2))%2?'#4b6741':'#506b43'});
              stats.hedges++;
            }else if(style===2){
              box('stone',x,z,y+.36,1.23,.70,.48,-Math.atan2(uz,ux));stats.walls++;
            }else{
              const yaw=-Math.atan2(uz,ux),height=style===1?1.05:.86;
              box('fencepost',x-ux*.60,z-uz*.60,y+height/2,.12,height,.12,yaw);
              if(style===1){
                for(let k=0;k<5;k++)
                  box('picket',x+ux*(k-2)*.23,z+uz*(k-2)*.23,y+.53,.11,1.04,.07,yaw);
                box('fencerail',x,z,y+.31,1.19,.075,.075,yaw);
                box('fencerail',x,z,y+.79,1.19,.075,.075,yaw);
              }else{
                box('rail',x,z,y+.42,1.22,.095,.08,yaw);
                box('rail',x,z,y+.73,1.22,.095,.08,yaw);
              }
              stats.fences++;
            }
            included++;
          }
          if(included>2)frontageOccupied.push({x:gateX,z:gateZ,half});
        }
      }
    }

    // A sparse garden selection. Prefer back gardens, and leave many open.
    let backEdge=-Infinity;
    for(let j=0;j<site.poly.length;j+=2)
      backEdge=Math.max(backEdge,(site.poly[j]-site.x)*nx+(site.poly[j+1]-site.z)*nz);
    if(chance(seed,12)>.36){
      const back=backEdge+2.5+chance(seed,13)*3.3;
      const lateral=(chance(seed,14)-.5)*7.5;
      const tx=site.x+tanX*lateral+nx*back;
      const tz=site.z+tanZ*lateral+nz*back;
      const kind=treeKinds[hash(seed,15)%treeKinds.length];
      addTree(tx,tz,kind,seed,site.bi);
    }
    if(chance(seed,16)>.83){
      const back=backEdge+2.3+chance(seed,17)*2;
      const tx=site.x-tanX*(3.2+chance(seed,17)*3.2)+nx*back;
      const tz=site.z-tanZ*(3.2+chance(seed,17)*3.2)+nz*back;
      addTree(tx,tz,'small',hash(seed,18),site.bi);
    }
  }

  if(surface.p.length){
    const geom=new THREE.BufferGeometry();
    geom.setAttribute('position',new THREE.Float32BufferAttribute(surface.p,3));
    geom.setAttribute('color',new THREE.Float32BufferAttribute(surface.c,3));
    geom.computeVertexNormals();
    const mesh=new THREE.Mesh(geom,new THREE.MeshLambertMaterial({
      vertexColors:true,side:THREE.DoubleSide,polygonOffset:true,
      polygonOffsetFactor:-1,polygonOffsetUnits:-3
    }));
    mesh.receiveShadow=true;scene.add(mesh);
  }
  const dummy=new THREE.Object3D(),white=new THREE.Color();
  const materials={
    stone:'#77756d',fencepost:'#e4e3d9',picket:'#e5e5dc',
    fencerail:'#d7d7ca',rail:'#847868'
  };
  for(const [kind,arr] of boxesBatches){
    if(!arr.length)continue;
    const geom=new THREE.BoxGeometry(1,1,1);
    const mat=new THREE.MeshLambertMaterial({color:materials[kind]||'#77776f'});
    const batch=new THREE.InstancedMesh(geom,mat,arr.length);
    for(let i=0;i<arr.length;i++){
      const q=arr[i];
      dummy.position.set(q.x,q.y,q.z);
      dummy.rotation.set(0,q.yaw||0,0);
      dummy.scale.set(q.sx,q.sy,q.sz);
      dummy.updateMatrix();batch.setMatrixAt(i,dummy.matrix);
    }
    batch.instanceMatrix.needsUpdate=true;
    batch.frustumCulled=false;batch.receiveShadow=true;scene.add(batch);
  }
  if(hedgeBatches.length){
    const geom=new THREE.DodecahedronGeometry(1,1);
    const mat=new THREE.MeshLambertMaterial({color:0xffffff});
    const batch=new THREE.InstancedMesh(geom,mat,hedgeBatches.length);
    for(let i=0;i<hedgeBatches.length;i++){
      const q=hedgeBatches[i];
      dummy.position.set(q.x,q.y,q.z);dummy.rotation.set(0,q.angle,0);
      dummy.scale.set(.67,q.height/2,.48);dummy.updateMatrix();
      batch.setMatrixAt(i,dummy.matrix);batch.setColorAt(i,white.set(q.color));
    }
    batch.instanceMatrix.needsUpdate=true;batch.instanceColor.needsUpdate=true;
    batch.frustumCulled=false;batch.receiveShadow=true;scene.add(batch);
  }
  const treeParts=['small','mature','apple','spruce'];
  const leafGeom=new THREE.IcosahedronGeometry(1,2);
  const coneGeom=new THREE.ConeGeometry(1,1,11,1);
  const trunkGeom=new THREE.CylinderGeometry(.16,.23,1,8);
  const branchGeom=new THREE.CylinderGeometry(.07,.095,1,7);
  for(const kind of treeParts){
    const items=trees.filter(t=>t.kind===kind);if(!items.length)continue;
    const trunkMat=new THREE.MeshLambertMaterial({color:kind==='spruce'?0x706152:0x817569});
    const trunk=new THREE.InstancedMesh(trunkGeom,trunkMat,items.length);
    const branch=new THREE.InstancedMesh(branchGeom,trunkMat,kind==='spruce'?items.length:items.length*2);
    const leafMat=new THREE.MeshLambertMaterial({color:0xffffff,side:THREE.DoubleSide});
    const nCrown=kind==='spruce'?3:4;
    const leaves=new THREE.InstancedMesh(kind==='spruce'?coneGeom:leafGeom,leafMat,items.length*nCrown);
    const c0=kind==='mature'?'#466d47':kind==='apple'?'#698151':kind==='spruce'?'#345a45':'#628252';
    let bi=0;
    for(let i=0;i<items.length;i++){
      const t=items[i],h=t.h,stem=kind==='spruce'?.38:kind==='mature'?.37:kind==='apple'?.31:.36;
      dummy.position.set(t.x,t.y+stem*h/2,t.z);
      dummy.rotation.set(0,0,0);dummy.scale.set(1,h*stem,1);dummy.updateMatrix();
      trunk.setMatrixAt(i,dummy.matrix);
      for(let q=0;q<(kind==='spruce'?1:2);q++){
        const a=chance(t.seed,q+20)*Math.PI*2,rad=h*(kind==='mature'?.13:.09);
        dummy.position.set(t.x+Math.cos(a)*rad,t.y+h*(stem+.14),t.z+Math.sin(a)*rad);
        dummy.rotation.set(Math.cos(a)*.28,0,Math.sin(a)*.40);
        dummy.scale.set(.9,h*.32,.9);dummy.updateMatrix();branch.setMatrixAt(bi++,dummy.matrix);
      }
      for(let j=0;j<nCrown;j++){
        const angle=chance(t.seed,j+33)*6.2832;
        const radial=j===0?0:(.17+.06*chance(t.seed,j+40))*h;
        const y=kind==='spruce'?(.55+j*.13)*h:(.60+(j%2)*.14+.06*chance(t.seed,j+44))*h;
        dummy.position.set(t.x+Math.cos(angle)*radial,t.y+y,t.z+Math.sin(angle)*radial);
        dummy.rotation.set(.05*Math.sin(angle),angle,.05*Math.cos(angle));
        if(kind==='spruce')dummy.scale.set(h*(.25-j*.044),h*.34,h*(.25-j*.044));
        else dummy.scale.set(h*(kind==='mature'?.255:.22),h*.23,h*(kind==='mature'?.24:.20));
        dummy.updateMatrix();
        leaves.setMatrixAt(i*nCrown+j,dummy.matrix);
        white.set(c0).multiplyScalar(.82+chance(t.seed,j+61)*.33);
        leaves.setColorAt(i*nCrown+j,white);
      }
    }
    for(const batch of [trunk,branch,leaves]){
      batch.instanceMatrix.needsUpdate=true;batch.frustumCulled=false;
      batch.castShadow=true;batch.receiveShadow=true;scene.add(batch);
    }
    leaves.instanceColor.needsUpdate=true;
  }
  return stats;
}
