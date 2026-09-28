import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import {fileURLToPath} from "node:url";
const here=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(here,"..");const src=path.join(root,"src");const dist=path.join(root,"dist");
fs.rmSync(dist,{recursive:true,force:true});fs.mkdirSync(dist,{recursive:true});
const modules={};
function addCjs(id,file){modules[id]=fs.readFileSync(file,"utf8")}
addCjs("react",path.join(root,"node_modules/react/cjs/react.production.js"));addCjs("scheduler",path.join(root,"node_modules/scheduler/cjs/scheduler.production.js"));addCjs("react-dom",path.join(root,"node_modules/react-dom/cjs/react-dom.production.js"));addCjs("react-dom/client",path.join(root,"node_modules/react-dom/cjs/react-dom-client.production.js"));
const seen=new Set();
function normalize(from,spec){if(!spec.startsWith("."))return spec;let p=path.resolve(path.dirname(from),spec);if(!path.extname(p))p+=".js";return "./"+path.relative(src,p).replaceAll(path.sep,"/")}
function transform(file){const id="./"+path.relative(src,file).replaceAll(path.sep,"/");if(seen.has(id))return;seen.add(id);let code=fs.readFileSync(file,"utf8");const deps=[];
code=code.replace(/import\s+([A-Za-z_$][\w$]*)\s+from\s+["']([^"']+)["'];?/g,(m,name,spec)=>{const dep=normalize(file,spec);deps.push([spec,dep]);return `const ${name}=require(${JSON.stringify(dep)}).default ?? require(${JSON.stringify(dep)});`});
code=code.replace(/import\s+\{([^}]+)\}\s+from\s+["']([^"']+)["'];?/g,(m,names,spec)=>{const dep=normalize(file,spec);deps.push([spec,dep]);return `const {${names}}=require(${JSON.stringify(dep)});`});
code=code.replace(/import\s+["']([^"']+)["'];?/g,(m,spec)=>{if(spec.endsWith('.css'))return '';const dep=normalize(file,spec);deps.push([spec,dep]);return `require(${JSON.stringify(dep)});`});
const exports=[];let defaultName=null;
code=code.replace(/export\s+default\s+function\s+([A-Za-z_$][\w$]*)/g,(m,n)=>{defaultName=n;return `function ${n}`});
code=code.replace(/export\s+function\s+([A-Za-z_$][\w$]*)/g,(m,n)=>{exports.push(n);return `function ${n}`});
code=code.replace(/export\s+class\s+([A-Za-z_$][\w$]*)/g,(m,n)=>{exports.push(n);return `class ${n}`});
code=code.replace(/export\s+const\s+([A-Za-z_$][\w$]*)/g,(m,n)=>{exports.push(n);return `const ${n}`});
code=code.replace(/export\s+default\s+([A-Za-z_$][\w$]*);?/g,(m,n)=>{defaultName=n;return ''});
code=code.replace(/import\.meta\.env\.VITE_API_URL/g,JSON.stringify(process.env.VITE_API_URL||"/api/v1"));
if(exports.length)code+=`\n${exports.map(n=>`exports.${n}=${n};`).join("\n")}`;if(defaultName)code+=`\nexports.default=${defaultName};`;
modules[id]=code;for(const [orig,dep] of deps){if(orig.startsWith('.'))transform(path.resolve(path.dirname(file),orig.endsWith('.js')?orig:orig+'.js'))}}
transform(path.join(src,"main.jsx"));
const bundle=`(()=>{const modules={${Object.entries(modules).map(([id,code])=>`${JSON.stringify(id)}:(module,exports,require)=>{\n${code}\n}`).join(',')}};const cache={};function require(id){if(cache[id])return cache[id].exports;if(!modules[id])throw new Error('Module not found: '+id);const module={exports:{}};cache[id]=module;modules[id](module,module.exports,require);return module.exports;}require('./main.jsx');})();`;
fs.writeFileSync(path.join(dist,"app.js"),bundle);fs.copyFileSync(path.join(src,"styles.css"),path.join(dist,"styles.css"));
const html=`<!doctype html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><meta name="theme-color" content="#2f2435"/><meta name="description" content="AI-powered growth automation control center"/><title>AI Growth Operations OS</title><link rel="stylesheet" href="/styles.css"/></head><body><div id="root"></div><script src="/app.js" defer></script></body></html>`;fs.writeFileSync(path.join(dist,"index.html"),html);console.log(`Built production bundle: ${path.relative(process.cwd(),dist)} (${Math.round(fs.statSync(path.join(dist,'app.js')).size/1024)} KB JS)`);
