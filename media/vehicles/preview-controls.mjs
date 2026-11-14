// Camera/gesture state is independent of WebGL, so touch transitions can be checked.
export const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
export const CAMERA_VIEWS = Object.freeze({
  three_quarter: {az:-Math.PI*.75, el:.30, ortho:false},
  side: {az:-Math.PI*.5, el:0, ortho:true},
  front: {az:Math.PI, el:0, ortho:true},
  rear: {az:0, el:0, ortho:true},
  top: {az:0, el:Math.PI*.5, ortho:true},
});
export function orbitState(){return {...CAMERA_VIEWS.three_quarter,zoom:1,pointers:new Map()};}
export function setFixedView(state,name){
  if(!Object.prototype.hasOwnProperty.call(CAMERA_VIEWS,name))return false;
  Object.assign(state,CAMERA_VIEWS[name],{zoom:1});
  state.pointers.clear();
  return true;
}
export function zoomBy(state,factor){
  if(Number.isFinite(factor)&&factor>0)state.zoom=clamp(state.zoom*factor,.45,2.8);
}
export function pointerDown(state,id,x,y){
  if(state.pointers.size>=2&&!state.pointers.has(id))return false;
  state.pointers.set(id,{x,y});return true;
}
const span = pointers => {
  const [a,b]=[...pointers.values()];return a&&b?Math.hypot(a.x-b.x,a.y-b.y):0;
};
export function pointerMove(state,id,x,y){
  const previous=state.pointers.get(id);if(!previous)return false;
  const before=span(state.pointers);
  state.pointers.set(id,{x,y});
  if(state.pointers.size===1){
    state.az-=(x-previous.x)*.007;
    state.el=clamp(state.el+(y-previous.y)*.007,-.12,Math.PI/2);
  }else{
    const after=span(state.pointers);
    if(before>8&&after>8)zoomBy(state,before/after);
  }
  return true;
}
export function pointerUp(state,id){state.pointers.delete(id);}
export function orthoHeight(horizontal,vertical,aspect){
  return Math.max(vertical,horizontal/Math.max(aspect,.05),.1)*1.16;
}
export function reviewRegion(width,height,panels){
  const x=width<600?12:Math.min(panels.headerRight+16,width*.48);
  const y=width<600?panels.headerBottom+16:panels.lookBottom+12;
  return {x,y,width:Math.max(100,width-x-12),height:Math.max(100,panels.controlsTop-y-16)};
}
export function frameReviewCamera(THREE,options){
  const {state,perspective,orthographic,target,corners,radius,width,height,region}=options;
  const camera=state.ortho?orthographic:perspective;
  const aspect=region.width/region.height;
  camera.aspect=aspect;
  const verticalFov=THREE.MathUtils.degToRad(38);
  const horizontalFov=2*Math.atan(Math.tan(verticalFov/2)*aspect);
  const distance=radius/Math.sin(Math.min(verticalFov,horizontalFov)/2)*1.10*state.zoom;
  camera.position.set(target.x+Math.sin(state.az)*distance*Math.cos(state.el),target.y+Math.sin(state.el)*distance,target.z+Math.cos(state.az)*distance*Math.cos(state.el));
  camera.up.set(0,1,0);
  if(state.el>Math.PI/2-.001)camera.up.set(0,0,-1);
  camera.lookAt(target);camera.updateMatrixWorld(true);
  if(state.ortho){
    let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
    for(const point of corners){
      const q=point.clone().applyMatrix4(camera.matrixWorldInverse);
      minX=Math.min(minX,q.x);maxX=Math.max(maxX,q.x);minY=Math.min(minY,q.y);maxY=Math.max(maxY,q.y);
    }
    const h=orthoHeight(maxX-minX,maxY-minY,aspect)*state.zoom;
    camera.left=-h*aspect/2;camera.right=h*aspect/2;camera.top=h/2;camera.bottom=-h/2;
  }
  camera.updateProjectionMatrix();
  // Render the same full-frame film pass, offsetting the camera's view into the
  // region beside/below the controls. Model geometry and scale remain untouched.
  camera.setViewOffset(region.width,region.height,-region.x,-region.y,width,height);
  return camera;
}
