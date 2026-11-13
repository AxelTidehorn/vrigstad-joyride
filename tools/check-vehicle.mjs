import assert from 'node:assert/strict';
import {buildBodyData} from '../src/vehicles/saab.mjs';
const data=buildBodyData(),{positions,normals,colors,vertices,faces}=data;
assert.equal(positions.length,normals.length);assert.equal(colors.length,positions.length);
assert.ok(positions.every(Number.isFinite)&&normals.every(Number.isFinite));
const edges=new Map(),adj=new Map();let volume=0;
for(const [a,b,c] of faces){
 const A=vertices[a],B=vertices[b],C=vertices[c];
 volume+=(A[0]*(B[1]*C[2]-B[2]*C[1])+A[1]*(B[2]*C[0]-B[0]*C[2])+A[2]*(B[0]*C[1]-B[1]*C[0]))/6;
 for(const [i,j] of [[a,b],[b,c],[c,a]]){const key=[i,j].sort((a,b)=>a-b).join(',');if(!edges.has(key))edges.set(key,[]);edges.get(key).push([i,j]);if(!adj.has(i))adj.set(i,new Set());adj.get(i).add(j);adj.get(j)?.add(i)}
}
for(const edge of edges.values()){assert.equal(edge.length,2,'watertight manifold body');assert.equal(edge[0][0],edge[1][1],'opposite shared-edge winding')}
const seen=new Set(),stack=[0];while(stack.length){const v=stack.pop();if(seen.has(v))continue;seen.add(v);for(const w of adj.get(v)||[])stack.push(w)}
assert.equal(seen.size,vertices.length,'one connected body shell');assert.ok(volume>3&&volume<8,'outward winding and plausible volume');
for(let i=0;i<normals.length;i+=3)assert.ok(Math.abs(Math.hypot(...normals.slice(i,i+3))-1)<1e-6);
const extent=k=>Math.max(...vertices.map(v=>v[k]))-Math.min(...vertices.map(v=>v[k]));
assert.ok(extent(0)<1.9&&extent(0)>1.5);assert.ok(extent(2)>4.5&&extent(2)<4.9);assert.ok(extent(1)>1);
assert.ok(faces.length<600,'body polygon budget');assert.deepEqual(buildBodyData(),data,'deterministic');
console.log('saab: generated body manifold, connected, outward wound; bounds, normals and budgets passed',faces.length,volume);
