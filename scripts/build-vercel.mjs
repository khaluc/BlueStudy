// Publish frontend assets only; never copy credentials or learner data.
import {cp, mkdir, readFile, writeFile} from 'node:fs/promises';
await mkdir('dist/app', {recursive:true});
await cp('apps/web', 'dist/app', {recursive:true});
const index=await readFile('dist/app/index.html','utf8');
await writeFile('dist/app/index.html',index.replace('<head>', '<head>\n<script>window.BLUESTUDY_STATIC = true;</script>'));
console.log('Built public frontend preview; backend features are not connected.');
