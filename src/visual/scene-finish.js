// r128: retain upstream's ACES, sRGB output, material conversions and encoded fog.
// The target is RGBA8 (not a hardware sRGB texture). Its encoding tells r128's
// scene shaders to write sRGB, exactly like the canvas. Raw final sampling must
// NOT decode/encode or tone-map a second time. No automatic encoding chunks.
const sceneFinish=(()=>{
const q=new URLSearchParams(location.search).get('grain');
const parsed=Number(q),strength=q==='off'?0:q==='strong'?1.35:q==='subtle'||q===null?.62:Number.isFinite(parsed)?Math.max(0,Math.min(2,parsed)):.62;
const enabled=strength>0;
const uniforms={uStrength:{value:strength}};

if(!enabled)return {render:()=>renderer.render(scene,camera),resize(){},state:()=>({enabled:false,targets:0})};
const Target=renderer.capabilities.isWebGL2?THREE.WebGLMultisampleRenderTarget:THREE.WebGLRenderTarget;
const target=new Target(1,1,{minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter,depthBuffer:true,stencilBuffer:false});
target.texture.encoding=THREE.sRGBEncoding;target.texture.generateMipmaps=false;
if(target.isWebGLMultisampleRenderTarget)target.samples=coarse?2:4;
uniforms.uScene={value:target.texture};
const screen=new THREE.Scene(),view=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const material=new THREE.ShaderMaterial({depthTest:false,depthWrite:false,toneMapped:false,uniforms,
vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',
fragmentShader:`uniform sampler2D uScene;varying vec2 vUv;
uniform float uStrength;
float hash(vec2 pixel){vec3 p=fract(vec3(pixel.xyx)*vec3(.1031,.1030,.0973));p+=dot(p,p.yzx+33.33);return fract((p.x+p.y)*p.z);}
vec3 finishColor(vec3 c){
 float y=dot(c,vec3(.2126,.7152,.0722));
 float mid=smoothstep(.03,.30,y)*(1.-.62*smoothstep(.61,.97,y));
 float noise=.85*hash(floor(gl_FragCoord.xy))+.15*hash(floor(gl_FragCoord.xy*.57)+vec2(91.,17.))-.5;
 return clamp(c+vec3(noise*.023*uStrength*(.25+.75*mid)),0.,1.);
}
void main(){gl_FragColor=vec4(finishColor(texture2D(uScene,vUv).rgb),1.);}`});
screen.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),material));
const size=new THREE.Vector2();
return {
 render(){renderer.setRenderTarget(target);renderer.render(scene,camera);renderer.setRenderTarget(null);renderer.render(screen,view)},
 resize(){renderer.getDrawingBufferSize(size);target.setSize(Math.max(1,size.x),Math.max(1,size.y))},
 state:()=>({enabled:true,targets:1,setting:q,strength})
};
})();
