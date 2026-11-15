import{c as s}from"./index-ywOpk92k.js";/**
 * @license @tabler/icons-react v3.46.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const i=[["path",{d:"M12 5l0 14",key:"svg-0"}],["path",{d:"M18 13l-6 6",key:"svg-1"}],["path",{d:"M6 13l6 6",key:"svg-2"}]],h=s("outline","arrow-down","ArrowDown",i);/**
 * @license @tabler/icons-react v3.46.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */const c=[["path",{d:"M12 5l0 14",key:"svg-0"}],["path",{d:"M18 11l-6 -6",key:"svg-1"}],["path",{d:"M6 11l6 -6",key:"svg-2"}]],m=s("outline","arrow-up","ArrowUp",c),p={experiences:{org:"company",role:"role",orgLabel:"单位",roleLabel:"职位"},projects:{org:"name",role:"role",orgLabel:"项目",roleLabel:"角色"},outputs:{org:"title",role:"role",orgLabel:"成果",roleLabel:"说明"},education:{org:"school",role:"degree",orgLabel:"学校",roleLabel:"专业 / 学位"}},u={summary:"个人概要",skills:"专业技能",experiences:"工作经历",projects:"项目经历",outputs:"成果",education:"教育经历",honors:"荣誉与其他"};function f(e){const{org:t,role:o}=p[e];return{[t]:"",[o]:"",start:"",end:"",summary:"",bullets:[],groups:[]}}function b(e,t){var o;return((o=e.section_titles)==null?void 0:o[t])||u[t]||t}function L(e,t,o){const n=t+o;if(n<0||n>=e.length)return e;const r=e.slice(),[a]=r.splice(t,1);return r.splice(n,0,a),r}function $(e){return e.split(`
`)}function y(e){return(e??[]).join(`
`)}function I(e,t){return{...e,...t,profile:e.profile,visibility:e.visibility,basics:{...t.basics,photo:t.basics.photo||e.basics.photo}}}function _(e){return[e.experiences.length?`经历 ${e.experiences.length} 段`:"",e.projects.length?`项目 ${e.projects.length} 个`:"",e.education.length?`教育 ${e.education.length} 段`:"",e.skill_groups.length||e.skills.length?`技能 ${e.skill_groups.length+e.skills.length} 项`:"",e.honors.length?`荣誉 ${e.honors.length} 条`:""].filter(Boolean).join(" · ")||"只有基本信息"}function l(e){return`/p/${encodeURIComponent(e)}/career`}function k(e){return`${l(e)}/resume`}function v(e,t){return`${l(e)}/jobs/${encodeURIComponent(t)}`}function w(e){return e.trim().replace(/[^a-zA-Z0-9一-鿿_-]+/g,"-").replace(/^-+|-+$/g,"").slice(0,80)}export{m as I,p as R,h as a,v as b,k as c,w as d,l as e,y as f,f as g,I as h,$ as l,L as m,_ as r,b as s};
