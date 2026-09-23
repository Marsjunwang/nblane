var Zg=Object.defineProperty;var $g=(n,e,t)=>e in n?Zg(n,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):n[e]=t;var Ie=(n,e,t)=>$g(n,typeof e!="symbol"?e+"":e,t);import{u as Jg,a as Qg,j as pe,T as e_,n as Jf,G as t_,r as st,b as n_,c as i_,L as r_,g as s_,d as a_,e as o_,f as l_,h as Qf}from"./index-SHEMlMcn.js";function c_(n){return`${n.getFullYear()}-${String(n.getMonth()+1).padStart(2,"0")}`}function u_(n,e=new Date){const t=c_(e);let i=0,r=0,s=0;for(const o of n)!o.date||!String(o.date).startsWith(t)||(o.kind==="goal.added"?i+=1:o.kind==="goal.completed"?r+=1:o.kind==="north_star.rewritten"&&(s+=1));const a=[];return i>0&&a.push(`本月新立目标 ${i}`),r>0&&a.push(`新镌 ${r} 星`),s>0&&a.push("北极星已重刻"),a.join("，")}function h_(n,e){return e?n.endsWith("。」")?`${n.slice(0,-2)}，${e}。」`:n.endsWith("」")?`${n.slice(0,-1)}，${e}」`:`${n} ${e}`:n}function f_({habit:n}){return pe.jsxs(t_,{gap:5,wrap:"nowrap",children:[(n.week??[]).map(e=>pe.jsx("span",{title:e.date,style:{display:"inline-block",width:9,height:9,borderRadius:"50%",background:e.done?"#dcae55":"transparent",border:`1px solid ${e.done?"#dcae55":"rgba(232, 226, 210, 0.55)"}`,opacity:e.future?.4:1}},e.date)),pe.jsxs("span",{style:{marginLeft:6,fontSize:11,opacity:.75},children:["连续 ",n.streak??0," 天"]})]})}function d_({profile:n}){var o,l;const e=Jg(n),t=Qg(n),i=((o=e.data)==null?void 0:o.board.habits)??[],r=((l=e.data)==null?void 0:l.board.today)??"";if(i.length===0)return null;const s=c=>(c.week??[]).some(u=>u.done&&!u.future&&u.date===r),a=c=>{t.mutate({habit:c.id,date:"",summary:"",note:""},{onSuccess:()=>{Jf.show({color:"green",title:"已打卡",message:`${c.title||c.id} 今日打卡成功。`})},onError:u=>{Jf.show({color:"red",title:"打卡失败",message:u instanceof Error?u.message:String(u)})}})};return pe.jsxs("div",{className:"starmap-habit-seal","data-starmap-ui":!0,"data-testid":"habit-seal",children:[pe.jsx("span",{className:"starmap-habit-seal-label",children:"日课"}),i.map(c=>{const u=s(c);return pe.jsx(e_,{label:pe.jsx(f_,{habit:c}),withArrow:!0,position:"top",children:pe.jsxs("button",{type:"button",className:"starmap-habit-seal-item","data-testid":`habit-seal-${c.id}`,"data-done":u?"true":"false",disabled:t.isPending,onClick:()=>a(c),"aria-label":`日课打卡 ${c.title||c.id}`,children:[c.title||c.id,pe.jsx("span",{className:`starmap-habit-seal-dot${u?" done":""}`,children:u?"●":"○"})]})},c.id)})]})}const p_=[{value:"active",label:"进行中"},{value:"paused",label:"暂停"},{value:"completed",label:"已镌刻"}];function m_({selection:n,snapshot:e,profile:t,onSaved:i}){const r=n.kind==="north"||n.kind==="goal",[s,a]=st.useState(n.kind==="north"&&!e.north.is_set),[o,l]=st.useState(!1),c=n_(t),u=i_(t),f=n.kind==="goal"?e.goals.find(B=>B.id===n.id):void 0,[h,d]=st.useState(e.north.full),[m,g]=st.useState(e.north.brief),[p,_]=st.useState(e.north.visibility==="public"?"public":"private"),[v,S]=st.useState((f==null?void 0:f.title)??""),[y,M]=st.useState((f==null?void 0:f.summary)??""),[T,w]=st.useState((f==null?void 0:f.start)??""),[b,x]=st.useState((f==null?void 0:f.target)??""),[A,P]=st.useState((f==null?void 0:f.status)??"active");st.useEffect(()=>{d(e.north.full),g(e.north.brief),_(e.north.visibility==="public"?"public":"private")},[e.north.full,e.north.brief,e.north.visibility]),st.useEffect(()=>{S((f==null?void 0:f.title)??""),M((f==null?void 0:f.summary)??""),w((f==null?void 0:f.start)??""),x((f==null?void 0:f.target)??""),P((f==null?void 0:f.status)??"active")},[f==null?void 0:f.id,f==null?void 0:f.title,f==null?void 0:f.summary,f==null?void 0:f.start,f==null?void 0:f.target,f==null?void 0:f.status]);const R=c.isPending||u.isPending,L=c.error??u.error,I=B=>{l(!0),window.setTimeout(()=>{l(!1),a(!1),i(B)},950)},N=()=>{c.mutate({full:h.trim(),brief:m.trim(),visibility:p},{onSuccess:B=>{const q=B.north_star;I({...n,title:"北极星",rows:[["类型","北极星"],["铭文",(q==null?void 0:q.full)||"—"],["简称",(q==null?void 0:q.brief)||"—"],["可见性",(q==null?void 0:q.visibility)==="public"?"可公开":"仅本地"]]})}})},O=()=>{f&&u.mutate({goalId:f.id,body:{title:v.trim(),summary:y.trim(),start:T,target:b,status:A}},{onSuccess:B=>{const q=B.goal;I({...n,title:q.title||f.title,rows:[["状态",s_(q.status??"active")],["起始",q.start||"—"],["目标",q.target||"—"],["铭文",q.summary||"—"]]})}})};return pe.jsxs(pe.Fragment,{children:[o&&pe.jsx("div",{className:"starmap-seal","aria-hidden":"true","data-testid":"starmap-seal",children:"印"}),!s&&pe.jsxs(pe.Fragment,{children:[pe.jsx("h3",{children:n.title}),pe.jsx("dl",{children:n.rows.map(([B,q])=>pe.jsxs("div",{children:[pe.jsx("dt",{children:B}),pe.jsx("dd",{children:q})]},B))}),pe.jsxs("div",{className:"starmap-detail-actions",children:[r&&pe.jsx("button",{type:"button",className:"starmap-recarve","data-testid":"starmap-recarve",onClick:()=>a(!0),children:"重刻"}),pe.jsx(g_,{kind:n.kind,profile:t})]})]}),s&&n.kind==="north"&&pe.jsxs("div",{className:"starmap-edit","data-testid":"starmap-edit-north",children:[pe.jsx("h3",{children:"重刻 · 北极星铭文"}),pe.jsxs("label",{children:[pe.jsx("span",{children:"全文"}),pe.jsx("textarea",{value:h,onChange:B=>d(B.target.value),rows:4,placeholder:"写下你的北极星…","data-testid":"edit-north-full"})]}),pe.jsxs("label",{children:[pe.jsx("span",{children:"简称(图面与列表展示)"}),pe.jsx("input",{value:m,onChange:B=>g(B.target.value),placeholder:"一句话简称","data-testid":"edit-north-brief"})]}),pe.jsxs("div",{className:"starmap-edit-field",children:[pe.jsx("span",{children:"可见性"}),pe.jsxs("div",{className:"starmap-vis-toggle",role:"group","aria-label":"可见性",children:[pe.jsx("button",{type:"button",className:p==="public"?"on":"",onClick:()=>_("public"),"data-testid":"edit-north-public",children:"可公开"}),pe.jsx("button",{type:"button",className:p==="private"?"on":"",onClick:()=>_("private"),"data-testid":"edit-north-private",children:"仅本地"})]}),pe.jsx("p",{className:"starmap-edit-hint",children:"助手始终可见全文;此开关只影响公开产物。"})]}),pe.jsx(ed,{saving:R,error:L,saveDisabled:!h.trim()&&!m.trim(),onSave:N,onCancel:()=>a(!1)})]}),s&&n.kind==="goal"&&f&&pe.jsxs("div",{className:"starmap-edit","data-testid":"starmap-edit-goal",children:[pe.jsx("h3",{children:"重刻 · 恒星铭文"}),pe.jsxs("label",{children:[pe.jsx("span",{children:"标题"}),pe.jsx("input",{value:v,onChange:B=>S(B.target.value),"data-testid":"edit-goal-title"})]}),pe.jsxs("label",{children:[pe.jsx("span",{children:"摘要"}),pe.jsx("textarea",{value:y,onChange:B=>M(B.target.value),rows:3,"data-testid":"edit-goal-summary"})]}),pe.jsxs("label",{children:[pe.jsx("span",{children:"起始日期"}),pe.jsx("input",{type:"date",value:T,onChange:B=>w(B.target.value),"data-testid":"edit-goal-start"})]}),pe.jsxs("label",{children:[pe.jsx("span",{children:"目标日期"}),pe.jsx("input",{type:"date",value:b,onChange:B=>x(B.target.value),"data-testid":"edit-goal-target"})]}),pe.jsxs("label",{children:[pe.jsx("span",{children:"状态"}),pe.jsx("select",{value:A,onChange:B=>P(B.target.value),"data-testid":"edit-goal-status",children:p_.map(B=>pe.jsx("option",{value:B.value,children:B.label},B.value))})]}),pe.jsx(ed,{saving:R,error:L,saveDisabled:!v.trim(),onSave:O,onCancel:()=>a(!1)})]})]})}function ed({saving:n,error:e,saveDisabled:t,onSave:i,onCancel:r}){return pe.jsxs(pe.Fragment,{children:[e&&pe.jsx("p",{className:"starmap-edit-error",role:"alert",children:e.message}),pe.jsxs("div",{className:"starmap-edit-actions",children:[pe.jsx("button",{type:"button",className:"starmap-save",disabled:n||t,onClick:i,"data-testid":"starmap-save",children:n?"落印中…":"落印"}),pe.jsx("button",{type:"button",className:"starmap-cancel",disabled:n,onClick:r,children:"收起刻刀"})]})]})}function g_({kind:n,profile:e}){const t=`/p/${encodeURIComponent(e)}`,i=n==="goal"?{to:`${t}/projects`,label:"前往项目泳道 →"}:n==="planet"?{to:`${t}/projects`,label:"前往项目 →"}:n==="guest"?{to:`${t}/evidence`,label:"前往证据 →"}:n==="skill"?{to:`${t}/skill-tree`,label:"前往技能树 →"}:null;return i?pe.jsx(r_,{className:"starmap-detail-link",to:i.to,children:i.label}):null}const bm=[{key:"active",title:"进行中",match:n=>n.status==="active"},{key:"paused",title:"暂停",match:n=>n.status==="paused"},{key:"carved",title:"已镌刻",match:n=>n.status==="completed"}];function __(n){const e=[{id:"north"}];for(const t of bm)for(const i of n.goals.filter(t.match))e.push({id:i.id,goal:i});return e}function v_(n,e,t){return n<=0?-1:(((e<0?0:e)+t)%n+n)%n}const td="nblane-starmap-catalog-hint-seen";function x_({open:n,snapshot:e,profile:t,selection:i,onFocus:r}){const[s,a]=st.useState(!1),[o,l]=st.useState(""),[c,u]=st.useState("north"),[f,h]=st.useState(!1),d=st.useRef(null),m=a_(t),g=st.useMemo(()=>__(e),[e]),p=e.north.is_set?e.north.brief||e.north.full||"北极星":"虚位 · 点击立星",_=v=>{u(v),r(v)};return st.useEffect(()=>{if(!n||!i)return;const v=i.kind==="north"?"north":i.kind==="goal"?i.id:null;v&&g.some(S=>S.id===v)&&u(v)},[n,i,g]),st.useEffect(()=>{var v,S,y;!n||!c||(y=(S=(v=d.current)==null?void 0:v.querySelector(`[data-catalog-id="${CSS.escape(c)}"]`))==null?void 0:S.scrollIntoView)==null||y.call(S,{block:"nearest"})},[n,c]),st.useEffect(()=>{if(!n||s)return;const v=S=>{const y=S.target;if(y&&/^(INPUT|TEXTAREA|SELECT)$/.test(y.tagName))return;const M=S.key==="ArrowDown"||S.key==="j"?1:S.key==="ArrowUp"||S.key==="k"?-1:0;if(M!==0){S.preventDefault();const T=g.findIndex(b=>b.id===c),w=g[v_(g.length,T,M)];w&&u(w.id)}else S.key==="Enter"&&(S.preventDefault(),c&&g.some(T=>T.id===c)&&r(c))};return window.addEventListener("keydown",v),()=>window.removeEventListener("keydown",v)},[n,s,g,c,r]),st.useEffect(()=>{if(!n)return;try{if(sessionStorage.getItem(td))return;sessionStorage.setItem(td,"1")}catch{}h(!0);const v=window.setTimeout(()=>h(!1),2600);return()=>window.clearTimeout(v)},[n]),pe.jsx("div",{className:`starmap-catalog${n?" open":""}`,ref:d,"data-starmap-ui":!0,"data-testid":"starmap-catalog","aria-hidden":!n,children:n&&pe.jsxs(pe.Fragment,{children:[pe.jsx("h3",{children:"星表"}),f&&pe.jsxs("p",{className:"starmap-catalog-hintbar","data-testid":"catalog-hintbar",children:[pe.jsx("kbd",{children:"↑"}),pe.jsx("kbd",{children:"↓"})," 移动 · ",pe.jsx("kbd",{children:"Enter"})," 开卡 · ",pe.jsx("kbd",{children:"Esc"})," 回纯图"]}),pe.jsxs("div",{className:"starmap-catalog-section","data-testid":"catalog-north",children:[pe.jsx("h4",{children:"北极星"}),pe.jsx(nd,{id:"north",active:c==="north",className:e.north.is_set?"":" vacant",title:p,sub:e.north.visibility==="public"?"可公开":"仅本地",onFocus:_})]}),bm.map(v=>{const S=e.goals.filter(v.match);return pe.jsxs("div",{className:"starmap-catalog-section","data-testid":`catalog-${v.key}`,children:[pe.jsxs("h4",{children:[v.title,S.length>0&&pe.jsx("span",{className:"sec-count",children:S.length})]}),S.length===0&&v.key==="active"&&pe.jsx("p",{className:"starmap-catalog-empty",children:"恒星虚位 — 自下方新增目标。"}),S.map(y=>pe.jsx(nd,{id:y.id,active:c===y.id,className:y.status==="completed"?" carved":"",title:y.title,sub:y.target||"",onFocus:_},y.id))]},v.key)}),!s&&pe.jsx("button",{type:"button",className:"starmap-catalog-add",onClick:()=>{l(""),a(!0)},"data-testid":"catalog-add-goal",children:"＋ 新增目标"}),s&&pe.jsx(y_,{saving:m.isPending,error:m.error,onCancel:()=>a(!1),onSubmit:v=>m.mutate(v,{onSuccess:S=>{a(!1),l(`「${S.goal.title||S.goal.id}」已入星表`)}})}),o&&pe.jsx("p",{className:"starmap-catalog-note",children:o})]})})}function nd({id:n,active:e,className:t,title:i,sub:r,onFocus:s}){return pe.jsxs("button",{type:"button",className:`starmap-catalog-row${e?" active":""}${t}`,onClick:()=>s(n),"data-catalog-id":n,"data-testid":`catalog-row-${n}`,children:[pe.jsx("span",{className:"row-title",children:i}),pe.jsx("span",{className:"row-sub",children:r}),pe.jsx("kbd",{className:"row-kbd",children:"Enter"})]})}function y_({saving:n,error:e,onSubmit:t,onCancel:i}){const[r,s]=st.useState(""),[a,o]=st.useState(""),[l,c]=st.useState("");return pe.jsxs("div",{className:"starmap-edit starmap-catalog-form","data-testid":"catalog-goal-form",children:[pe.jsxs("label",{children:[pe.jsx("span",{children:"标题"}),pe.jsx("input",{value:r,onChange:u=>s(u.target.value),placeholder:"新恒星之名","data-testid":"create-goal-title"})]}),pe.jsxs("label",{children:[pe.jsx("span",{children:"摘要"}),pe.jsx("textarea",{value:a,onChange:u=>o(u.target.value),rows:2,"data-testid":"create-goal-summary"})]}),pe.jsxs("label",{children:[pe.jsx("span",{children:"目标日期"}),pe.jsx("input",{type:"date",value:l,onChange:u=>c(u.target.value),"data-testid":"create-goal-target"})]}),e&&pe.jsx("p",{className:"starmap-edit-error",role:"alert",children:e.message}),pe.jsxs("div",{className:"starmap-edit-actions",children:[pe.jsx("button",{type:"button",className:"starmap-save",disabled:n||!r.trim(),onClick:()=>t({title:r.trim(),summary:a.trim(),target:l}),"data-testid":"create-goal-save",children:n?"镌刻中…":"落印"}),pe.jsx("button",{type:"button",className:"starmap-cancel",disabled:n,onClick:i,children:"收起刻刀"})]})]})}/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */const Ka="184",Us={ROTATE:0,DOLLY:1,PAN:2},Rs={ROTATE:0,PAN:1,DOLLY_PAN:2,DOLLY_ROTATE:3},b_=0,id=1,S_=2,Yo=1,M_=2,wa=3,ji=0,an=1,Rn=2,Tn=0,Hr=1,ol=2,rd=3,sd=4,T_=5,Br=100,E_=101,w_=102,A_=103,R_=104,C_=200,P_=201,D_=202,U_=203,Eu=204,wu=205,L_=206,I_=207,F_=208,N_=209,O_=210,B_=211,k_=212,z_=213,G_=214,Au=0,ll=1,Ru=2,Bs=3,Cu=4,Pu=5,Du=6,Uu=7,Sm=0,H_=1,V_=2,Di=0,Mm=1,Tm=2,Em=3,wm=4,Am=5,Rm=6,Cm=7,Pm=300,Zr=301,ks=302,ac=303,oc=304,Ul=306,Lu=1e3,Vi=1001,Iu=1002,un=1003,W_=1004,oo=1005,Gt=1006,lc=1007,zr=1008,Yt=1009,Dm=1010,Um=1011,ka=1012,jh=1013,Ui=1014,hi=1015,Yi=1016,Yh=1017,qh=1018,zs=1020,Lm=35902,Im=35899,Fm=1021,Nm=1022,fi=1023,qi=1026,fr=1027,Om=1028,Kh=1029,$r=1030,Zh=1031,$h=1033,qo=33776,Ko=33777,Zo=33778,$o=33779,Fu=35840,Nu=35841,Ou=35842,Bu=35843,ku=36196,zu=37492,Gu=37496,Hu=37488,Vu=37489,cl=37490,Wu=37491,Xu=37808,ju=37809,Yu=37810,qu=37811,Ku=37812,Zu=37813,$u=37814,Ju=37815,Qu=37816,eh=37817,th=37818,nh=37819,ih=37820,rh=37821,sh=36492,ah=36494,oh=36495,lh=36283,ch=36284,ul=36285,uh=36286,Za=3200,X_=3201,ad=0,j_=1,Ti="",Et="srgb",Gs="srgb-linear",hl="linear",bt="srgb",ls=7680,od=519,Y_=512,q_=513,K_=514,Jh=515,Z_=516,$_=517,Qh=518,J_=519,hh=35044,ld="300 es",Ri=2e3,fl=2001;function Q_(n){for(let e=n.length-1;e>=0;--e)if(n[e]>=65535)return!0;return!1}function dl(n){return document.createElementNS("http://www.w3.org/1999/xhtml",n)}function ev(){const n=dl("canvas");return n.style.display="block",n}const cd={};function pl(...n){const e="THREE."+n.shift();console.log(e,...n)}function Bm(n){const e=n[0];if(typeof e=="string"&&e.startsWith("TSL:")){const t=n[1];t&&t.isStackTrace?n[0]+=" "+t.getLocation():n[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return n}function Je(...n){n=Bm(n);const e="THREE."+n.shift();{const t=n[0];t&&t.isStackTrace?console.warn(t.getError(e)):console.warn(e,...n)}}function pt(...n){n=Bm(n);const e="THREE."+n.shift();{const t=n[0];t&&t.isStackTrace?console.error(t.getError(e)):console.error(e,...n)}}function fh(...n){const e=n.join(" ");e in cd||(cd[e]=!0,Je(...n))}function tv(n,e,t){return new Promise(function(i,r){function s(){switch(n.clientWaitSync(e,n.SYNC_FLUSH_COMMANDS_BIT,0)){case n.WAIT_FAILED:r();break;case n.TIMEOUT_EXPIRED:setTimeout(s,t);break;default:i()}}setTimeout(s,t)})}const nv={[Au]:ll,[Ru]:Du,[Cu]:Uu,[Bs]:Pu,[ll]:Au,[Du]:Ru,[Uu]:Cu,[Pu]:Bs};class pi{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});const i=this._listeners;i[e]===void 0&&(i[e]=[]),i[e].indexOf(t)===-1&&i[e].push(t)}hasEventListener(e,t){const i=this._listeners;return i===void 0?!1:i[e]!==void 0&&i[e].indexOf(t)!==-1}removeEventListener(e,t){const i=this._listeners;if(i===void 0)return;const r=i[e];if(r!==void 0){const s=r.indexOf(t);s!==-1&&r.splice(s,1)}}dispatchEvent(e){const t=this._listeners;if(t===void 0)return;const i=t[e.type];if(i!==void 0){e.target=this;const r=i.slice(0);for(let s=0,a=r.length;s<a;s++)r[s].call(this,e);e.target=null}}}const dn=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Jo=Math.PI/180,dh=180/Math.PI;function _r(){const n=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,i=Math.random()*4294967295|0;return(dn[n&255]+dn[n>>8&255]+dn[n>>16&255]+dn[n>>24&255]+"-"+dn[e&255]+dn[e>>8&255]+"-"+dn[e>>16&15|64]+dn[e>>24&255]+"-"+dn[t&63|128]+dn[t>>8&255]+"-"+dn[t>>16&255]+dn[t>>24&255]+dn[i&255]+dn[i>>8&255]+dn[i>>16&255]+dn[i>>24&255]).toLowerCase()}function lt(n,e,t){return Math.max(e,Math.min(t,n))}function iv(n,e){return(n%e+e)%e}function cc(n,e,t){return(1-t)*n+t*e}function Ei(n,e){switch(e.constructor){case Float32Array:return n;case Uint32Array:return n/4294967295;case Uint16Array:return n/65535;case Uint8Array:return n/255;case Int32Array:return Math.max(n/2147483647,-1);case Int16Array:return Math.max(n/32767,-1);case Int8Array:return Math.max(n/127,-1);default:throw new Error("Invalid component type.")}}function St(n,e){switch(e.constructor){case Float32Array:return n;case Uint32Array:return Math.round(n*4294967295);case Uint16Array:return Math.round(n*65535);case Uint8Array:return Math.round(n*255);case Int32Array:return Math.round(n*2147483647);case Int16Array:return Math.round(n*32767);case Int8Array:return Math.round(n*127);default:throw new Error("Invalid component type.")}}const rv={DEG2RAD:Jo},Nf=class Nf{constructor(e=0,t=0){this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const t=this.x,i=this.y,r=e.elements;return this.x=r[0]*t+r[3]*i+r[6],this.y=r[1]*t+r[4]*i+r[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=lt(this.x,e.x,t.x),this.y=lt(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=lt(this.x,e,t),this.y=lt(this.y,e,t),this}clampLength(e,t){const i=this.length();return this.divideScalar(i||1).multiplyScalar(lt(i,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const i=this.dot(e)/t;return Math.acos(lt(i,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,i=this.y-e.y;return t*t+i*i}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,i){return this.x=e.x+(t.x-e.x)*i,this.y=e.y+(t.y-e.y)*i,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){const i=Math.cos(t),r=Math.sin(t),s=this.x-e.x,a=this.y-e.y;return this.x=s*i-a*r+e.x,this.y=s*r+a*i+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};Nf.prototype.isVector2=!0;let Xe=Nf;class br{constructor(e=0,t=0,i=0,r=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=i,this._w=r}static slerpFlat(e,t,i,r,s,a,o){let l=i[r+0],c=i[r+1],u=i[r+2],f=i[r+3],h=s[a+0],d=s[a+1],m=s[a+2],g=s[a+3];if(f!==g||l!==h||c!==d||u!==m){let p=l*h+c*d+u*m+f*g;p<0&&(h=-h,d=-d,m=-m,g=-g,p=-p);let _=1-o;if(p<.9995){const v=Math.acos(p),S=Math.sin(v);_=Math.sin(_*v)/S,o=Math.sin(o*v)/S,l=l*_+h*o,c=c*_+d*o,u=u*_+m*o,f=f*_+g*o}else{l=l*_+h*o,c=c*_+d*o,u=u*_+m*o,f=f*_+g*o;const v=1/Math.sqrt(l*l+c*c+u*u+f*f);l*=v,c*=v,u*=v,f*=v}}e[t]=l,e[t+1]=c,e[t+2]=u,e[t+3]=f}static multiplyQuaternionsFlat(e,t,i,r,s,a){const o=i[r],l=i[r+1],c=i[r+2],u=i[r+3],f=s[a],h=s[a+1],d=s[a+2],m=s[a+3];return e[t]=o*m+u*f+l*d-c*h,e[t+1]=l*m+u*h+c*f-o*d,e[t+2]=c*m+u*d+o*h-l*f,e[t+3]=u*m-o*f-l*h-c*d,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,i,r){return this._x=e,this._y=t,this._z=i,this._w=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){const i=e._x,r=e._y,s=e._z,a=e._order,o=Math.cos,l=Math.sin,c=o(i/2),u=o(r/2),f=o(s/2),h=l(i/2),d=l(r/2),m=l(s/2);switch(a){case"XYZ":this._x=h*u*f+c*d*m,this._y=c*d*f-h*u*m,this._z=c*u*m+h*d*f,this._w=c*u*f-h*d*m;break;case"YXZ":this._x=h*u*f+c*d*m,this._y=c*d*f-h*u*m,this._z=c*u*m-h*d*f,this._w=c*u*f+h*d*m;break;case"ZXY":this._x=h*u*f-c*d*m,this._y=c*d*f+h*u*m,this._z=c*u*m+h*d*f,this._w=c*u*f-h*d*m;break;case"ZYX":this._x=h*u*f-c*d*m,this._y=c*d*f+h*u*m,this._z=c*u*m-h*d*f,this._w=c*u*f+h*d*m;break;case"YZX":this._x=h*u*f+c*d*m,this._y=c*d*f+h*u*m,this._z=c*u*m-h*d*f,this._w=c*u*f-h*d*m;break;case"XZY":this._x=h*u*f-c*d*m,this._y=c*d*f-h*u*m,this._z=c*u*m+h*d*f,this._w=c*u*f+h*d*m;break;default:Je("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){const i=t/2,r=Math.sin(i);return this._x=e.x*r,this._y=e.y*r,this._z=e.z*r,this._w=Math.cos(i),this._onChangeCallback(),this}setFromRotationMatrix(e){const t=e.elements,i=t[0],r=t[4],s=t[8],a=t[1],o=t[5],l=t[9],c=t[2],u=t[6],f=t[10],h=i+o+f;if(h>0){const d=.5/Math.sqrt(h+1);this._w=.25/d,this._x=(u-l)*d,this._y=(s-c)*d,this._z=(a-r)*d}else if(i>o&&i>f){const d=2*Math.sqrt(1+i-o-f);this._w=(u-l)/d,this._x=.25*d,this._y=(r+a)/d,this._z=(s+c)/d}else if(o>f){const d=2*Math.sqrt(1+o-i-f);this._w=(s-c)/d,this._x=(r+a)/d,this._y=.25*d,this._z=(l+u)/d}else{const d=2*Math.sqrt(1+f-i-o);this._w=(a-r)/d,this._x=(s+c)/d,this._y=(l+u)/d,this._z=.25*d}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let i=e.dot(t)+1;return i<1e-8?(i=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=i):(this._x=0,this._y=-e.z,this._z=e.y,this._w=i)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=i),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(lt(this.dot(e),-1,1)))}rotateTowards(e,t){const i=this.angleTo(e);if(i===0)return this;const r=Math.min(1,t/i);return this.slerp(e,r),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){const i=e._x,r=e._y,s=e._z,a=e._w,o=t._x,l=t._y,c=t._z,u=t._w;return this._x=i*u+a*o+r*c-s*l,this._y=r*u+a*l+s*o-i*c,this._z=s*u+a*c+i*l-r*o,this._w=a*u-i*o-r*l-s*c,this._onChangeCallback(),this}slerp(e,t){let i=e._x,r=e._y,s=e._z,a=e._w,o=this.dot(e);o<0&&(i=-i,r=-r,s=-s,a=-a,o=-o);let l=1-t;if(o<.9995){const c=Math.acos(o),u=Math.sin(c);l=Math.sin(l*c)/u,t=Math.sin(t*c)/u,this._x=this._x*l+i*t,this._y=this._y*l+r*t,this._z=this._z*l+s*t,this._w=this._w*l+a*t,this._onChangeCallback()}else this._x=this._x*l+i*t,this._y=this._y*l+r*t,this._z=this._z*l+s*t,this._w=this._w*l+a*t,this.normalize();return this}slerpQuaternions(e,t,i){return this.copy(e).slerp(t,i)}random(){const e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),i=Math.random(),r=Math.sqrt(1-i),s=Math.sqrt(i);return this.set(r*Math.sin(e),r*Math.cos(e),s*Math.sin(t),s*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}const Of=class Of{constructor(e=0,t=0,i=0){this.x=e,this.y=t,this.z=i}set(e,t,i){return i===void 0&&(i=this.z),this.x=e,this.y=t,this.z=i,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(ud.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(ud.setFromAxisAngle(e,t))}applyMatrix3(e){const t=this.x,i=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[3]*i+s[6]*r,this.y=s[1]*t+s[4]*i+s[7]*r,this.z=s[2]*t+s[5]*i+s[8]*r,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const t=this.x,i=this.y,r=this.z,s=e.elements,a=1/(s[3]*t+s[7]*i+s[11]*r+s[15]);return this.x=(s[0]*t+s[4]*i+s[8]*r+s[12])*a,this.y=(s[1]*t+s[5]*i+s[9]*r+s[13])*a,this.z=(s[2]*t+s[6]*i+s[10]*r+s[14])*a,this}applyQuaternion(e){const t=this.x,i=this.y,r=this.z,s=e.x,a=e.y,o=e.z,l=e.w,c=2*(a*r-o*i),u=2*(o*t-s*r),f=2*(s*i-a*t);return this.x=t+l*c+a*f-o*u,this.y=i+l*u+o*c-s*f,this.z=r+l*f+s*u-a*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const t=this.x,i=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[4]*i+s[8]*r,this.y=s[1]*t+s[5]*i+s[9]*r,this.z=s[2]*t+s[6]*i+s[10]*r,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=lt(this.x,e.x,t.x),this.y=lt(this.y,e.y,t.y),this.z=lt(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=lt(this.x,e,t),this.y=lt(this.y,e,t),this.z=lt(this.z,e,t),this}clampLength(e,t){const i=this.length();return this.divideScalar(i||1).multiplyScalar(lt(i,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,i){return this.x=e.x+(t.x-e.x)*i,this.y=e.y+(t.y-e.y)*i,this.z=e.z+(t.z-e.z)*i,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){const i=e.x,r=e.y,s=e.z,a=t.x,o=t.y,l=t.z;return this.x=r*l-s*o,this.y=s*a-i*l,this.z=i*o-r*a,this}projectOnVector(e){const t=e.lengthSq();if(t===0)return this.set(0,0,0);const i=e.dot(this)/t;return this.copy(e).multiplyScalar(i)}projectOnPlane(e){return uc.copy(this).projectOnVector(e),this.sub(uc)}reflect(e){return this.sub(uc.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const i=this.dot(e)/t;return Math.acos(lt(i,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,i=this.y-e.y,r=this.z-e.z;return t*t+i*i+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,i){const r=Math.sin(t)*e;return this.x=r*Math.sin(i),this.y=Math.cos(t)*e,this.z=r*Math.cos(i),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,i){return this.x=e*Math.sin(t),this.y=i,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){const t=this.setFromMatrixColumn(e,0).length(),i=this.setFromMatrixColumn(e,1).length(),r=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=i,this.z=r,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,t=Math.random()*2-1,i=Math.sqrt(1-t*t);return this.x=i*Math.cos(e),this.y=t,this.z=i*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};Of.prototype.isVector3=!0;let $=Of;const uc=new $,ud=new br,Bf=class Bf{constructor(e,t,i,r,s,a,o,l,c){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,i,r,s,a,o,l,c)}set(e,t,i,r,s,a,o,l,c){const u=this.elements;return u[0]=e,u[1]=r,u[2]=o,u[3]=t,u[4]=s,u[5]=l,u[6]=i,u[7]=a,u[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const t=this.elements,i=e.elements;return t[0]=i[0],t[1]=i[1],t[2]=i[2],t[3]=i[3],t[4]=i[4],t[5]=i[5],t[6]=i[6],t[7]=i[7],t[8]=i[8],this}extractBasis(e,t,i){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),i.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const i=e.elements,r=t.elements,s=this.elements,a=i[0],o=i[3],l=i[6],c=i[1],u=i[4],f=i[7],h=i[2],d=i[5],m=i[8],g=r[0],p=r[3],_=r[6],v=r[1],S=r[4],y=r[7],M=r[2],T=r[5],w=r[8];return s[0]=a*g+o*v+l*M,s[3]=a*p+o*S+l*T,s[6]=a*_+o*y+l*w,s[1]=c*g+u*v+f*M,s[4]=c*p+u*S+f*T,s[7]=c*_+u*y+f*w,s[2]=h*g+d*v+m*M,s[5]=h*p+d*S+m*T,s[8]=h*_+d*y+m*w,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){const e=this.elements,t=e[0],i=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8];return t*a*u-t*o*c-i*s*u+i*o*l+r*s*c-r*a*l}invert(){const e=this.elements,t=e[0],i=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8],f=u*a-o*c,h=o*l-u*s,d=c*s-a*l,m=t*f+i*h+r*d;if(m===0)return this.set(0,0,0,0,0,0,0,0,0);const g=1/m;return e[0]=f*g,e[1]=(r*c-u*i)*g,e[2]=(o*i-r*a)*g,e[3]=h*g,e[4]=(u*t-r*l)*g,e[5]=(r*s-o*t)*g,e[6]=d*g,e[7]=(i*l-c*t)*g,e[8]=(a*t-i*s)*g,this}transpose(){let e;const t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,i,r,s,a,o){const l=Math.cos(s),c=Math.sin(s);return this.set(i*l,i*c,-i*(l*a+c*o)+a+e,-r*c,r*l,-r*(-c*a+l*o)+o+t,0,0,1),this}scale(e,t){return this.premultiply(hc.makeScale(e,t)),this}rotate(e){return this.premultiply(hc.makeRotation(-e)),this}translate(e,t){return this.premultiply(hc.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){const t=Math.cos(e),i=Math.sin(e);return this.set(t,-i,0,i,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){const t=this.elements,i=e.elements;for(let r=0;r<9;r++)if(t[r]!==i[r])return!1;return!0}fromArray(e,t=0){for(let i=0;i<9;i++)this.elements[i]=e[i+t];return this}toArray(e=[],t=0){const i=this.elements;return e[t]=i[0],e[t+1]=i[1],e[t+2]=i[2],e[t+3]=i[3],e[t+4]=i[4],e[t+5]=i[5],e[t+6]=i[6],e[t+7]=i[7],e[t+8]=i[8],e}clone(){return new this.constructor().fromArray(this.elements)}};Bf.prototype.isMatrix3=!0;let it=Bf;const hc=new it,hd=new it().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),fd=new it().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function sv(){const n={enabled:!0,workingColorSpace:Gs,spaces:{},convert:function(r,s,a){return this.enabled===!1||s===a||!s||!a||(this.spaces[s].transfer===bt&&(r.r=Wi(r.r),r.g=Wi(r.g),r.b=Wi(r.b)),this.spaces[s].primaries!==this.spaces[a].primaries&&(r.applyMatrix3(this.spaces[s].toXYZ),r.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===bt&&(r.r=Ls(r.r),r.g=Ls(r.g),r.b=Ls(r.b))),r},workingToColorSpace:function(r,s){return this.convert(r,this.workingColorSpace,s)},colorSpaceToWorking:function(r,s){return this.convert(r,s,this.workingColorSpace)},getPrimaries:function(r){return this.spaces[r].primaries},getTransfer:function(r){return r===Ti?hl:this.spaces[r].transfer},getToneMappingMode:function(r){return this.spaces[r].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(r,s=this.workingColorSpace){return r.fromArray(this.spaces[s].luminanceCoefficients)},define:function(r){Object.assign(this.spaces,r)},_getMatrix:function(r,s,a){return r.copy(this.spaces[s].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(r){return this.spaces[r].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(r=this.workingColorSpace){return this.spaces[r].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(r,s){return fh("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),n.workingToColorSpace(r,s)},toWorkingColorSpace:function(r,s){return fh("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),n.colorSpaceToWorking(r,s)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],i=[.3127,.329];return n.define({[Gs]:{primaries:e,whitePoint:i,transfer:hl,toXYZ:hd,fromXYZ:fd,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:Et},outputColorSpaceConfig:{drawingBufferColorSpace:Et}},[Et]:{primaries:e,whitePoint:i,transfer:bt,toXYZ:hd,fromXYZ:fd,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:Et}}}),n}const ft=sv();function Wi(n){return n<.04045?n*.0773993808:Math.pow(n*.9478672986+.0521327014,2.4)}function Ls(n){return n<.0031308?n*12.92:1.055*Math.pow(n,.41666)-.055}let cs;class av{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let i;if(e instanceof HTMLCanvasElement)i=e;else{cs===void 0&&(cs=dl("canvas")),cs.width=e.width,cs.height=e.height;const r=cs.getContext("2d");e instanceof ImageData?r.putImageData(e,0,0):r.drawImage(e,0,0,e.width,e.height),i=cs}return i.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const t=dl("canvas");t.width=e.width,t.height=e.height;const i=t.getContext("2d");i.drawImage(e,0,0,e.width,e.height);const r=i.getImageData(0,0,e.width,e.height),s=r.data;for(let a=0;a<s.length;a++)s[a]=Wi(s[a]/255)*255;return i.putImageData(r,0,0),t}else if(e.data){const t=e.data.slice(0);for(let i=0;i<t.length;i++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[i]=Math.floor(Wi(t[i]/255)*255):t[i]=Wi(t[i]);return{data:t,width:e.width,height:e.height}}else return Je("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let ov=0;class ef{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:ov++}),this.uuid=_r(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){const t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):typeof VideoFrame<"u"&&t instanceof VideoFrame?e.set(t.displayWidth,t.displayHeight,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const i={uuid:this.uuid,url:""},r=this.data;if(r!==null){let s;if(Array.isArray(r)){s=[];for(let a=0,o=r.length;a<o;a++)r[a].isDataTexture?s.push(fc(r[a].image)):s.push(fc(r[a]))}else s=fc(r);i.url=s}return t||(e.images[this.uuid]=i),i}}function fc(n){return typeof HTMLImageElement<"u"&&n instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&n instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&n instanceof ImageBitmap?av.getDataURL(n):n.data?{data:Array.from(n.data),width:n.width,height:n.height,type:n.data.constructor.name}:(Je("Texture: Unable to serialize Texture."),{})}let lv=0;const dc=new $;class $t extends pi{constructor(e=$t.DEFAULT_IMAGE,t=$t.DEFAULT_MAPPING,i=Vi,r=Vi,s=Gt,a=zr,o=fi,l=Yt,c=$t.DEFAULT_ANISOTROPY,u=Ti){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:lv++}),this.uuid=_r(),this.name="",this.source=new ef(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=i,this.wrapT=r,this.magFilter=s,this.minFilter=a,this.anisotropy=c,this.format=o,this.internalFormat=null,this.type=l,this.offset=new Xe(0,0),this.repeat=new Xe(1,1),this.center=new Xe(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new it,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=u,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(dc).x}get height(){return this.source.getSize(dc).y}get depth(){return this.source.getSize(dc).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(const t in e){const i=e[t];if(i===void 0){Je(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}const r=this[t];if(r===void 0){Je(`Texture.setValues(): property '${t}' does not exist.`);continue}r&&i&&r.isVector2&&i.isVector2||r&&i&&r.isVector3&&i.isVector3||r&&i&&r.isMatrix3&&i.isMatrix3?r.copy(i):this[t]=i}}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const i={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(i.userData=this.userData),t||(e.textures[this.uuid]=i),i}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==Pm)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Lu:e.x=e.x-Math.floor(e.x);break;case Vi:e.x=e.x<0?0:1;break;case Iu:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Lu:e.y=e.y-Math.floor(e.y);break;case Vi:e.y=e.y<0?0:1;break;case Iu:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}$t.DEFAULT_IMAGE=null;$t.DEFAULT_MAPPING=Pm;$t.DEFAULT_ANISOTROPY=1;const kf=class kf{constructor(e=0,t=0,i=0,r=1){this.x=e,this.y=t,this.z=i,this.w=r}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,i,r){return this.x=e,this.y=t,this.z=i,this.w=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const t=this.x,i=this.y,r=this.z,s=this.w,a=e.elements;return this.x=a[0]*t+a[4]*i+a[8]*r+a[12]*s,this.y=a[1]*t+a[5]*i+a[9]*r+a[13]*s,this.z=a[2]*t+a[6]*i+a[10]*r+a[14]*s,this.w=a[3]*t+a[7]*i+a[11]*r+a[15]*s,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,i,r,s;const l=e.elements,c=l[0],u=l[4],f=l[8],h=l[1],d=l[5],m=l[9],g=l[2],p=l[6],_=l[10];if(Math.abs(u-h)<.01&&Math.abs(f-g)<.01&&Math.abs(m-p)<.01){if(Math.abs(u+h)<.1&&Math.abs(f+g)<.1&&Math.abs(m+p)<.1&&Math.abs(c+d+_-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;const S=(c+1)/2,y=(d+1)/2,M=(_+1)/2,T=(u+h)/4,w=(f+g)/4,b=(m+p)/4;return S>y&&S>M?S<.01?(i=0,r=.707106781,s=.707106781):(i=Math.sqrt(S),r=T/i,s=w/i):y>M?y<.01?(i=.707106781,r=0,s=.707106781):(r=Math.sqrt(y),i=T/r,s=b/r):M<.01?(i=.707106781,r=.707106781,s=0):(s=Math.sqrt(M),i=w/s,r=b/s),this.set(i,r,s,t),this}let v=Math.sqrt((p-m)*(p-m)+(f-g)*(f-g)+(h-u)*(h-u));return Math.abs(v)<.001&&(v=1),this.x=(p-m)/v,this.y=(f-g)/v,this.z=(h-u)/v,this.w=Math.acos((c+d+_-1)/2),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=lt(this.x,e.x,t.x),this.y=lt(this.y,e.y,t.y),this.z=lt(this.z,e.z,t.z),this.w=lt(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=lt(this.x,e,t),this.y=lt(this.y,e,t),this.z=lt(this.z,e,t),this.w=lt(this.w,e,t),this}clampLength(e,t){const i=this.length();return this.divideScalar(i||1).multiplyScalar(lt(i,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,i){return this.x=e.x+(t.x-e.x)*i,this.y=e.y+(t.y-e.y)*i,this.z=e.z+(t.z-e.z)*i,this.w=e.w+(t.w-e.w)*i,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};kf.prototype.isVector4=!0;let Ut=kf;class cv extends pi{constructor(e=1,t=1,i={}){super(),i=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:Gt,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},i),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=i.depth,this.scissor=new Ut(0,0,e,t),this.scissorTest=!1,this.viewport=new Ut(0,0,e,t),this.textures=[];const r={width:e,height:t,depth:i.depth},s=new $t(r),a=i.count;for(let o=0;o<a;o++)this.textures[o]=s.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(i),this.depthBuffer=i.depthBuffer,this.stencilBuffer=i.stencilBuffer,this.resolveDepthBuffer=i.resolveDepthBuffer,this.resolveStencilBuffer=i.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=i.depthTexture,this.samples=i.samples,this.multiview=i.multiview}_setTextureOptions(e={}){const t={minFilter:Gt,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let i=0;i<this.textures.length;i++)this.textures[i].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,i=1){if(this.width!==e||this.height!==t||this.depth!==i){this.width=e,this.height=t,this.depth=i;for(let r=0,s=this.textures.length;r<s;r++)this.textures[r].image.width=e,this.textures[r].image.height=t,this.textures[r].image.depth=i,this.textures[r].isData3DTexture!==!0&&(this.textures[r].isArrayTexture=this.textures[r].image.depth>1);this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,i=e.textures.length;t<i;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;const r=Object.assign({},e.textures[t].image);this.textures[t].source=new ef(r)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this.multiview=e.multiview,this}dispose(){this.dispatchEvent({type:"dispose"})}}class Jt extends cv{constructor(e=1,t=1,i={}){super(e,t,i),this.isWebGLRenderTarget=!0}}class km extends $t{constructor(e=null,t=1,i=1,r=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:i,depth:r},this.magFilter=un,this.minFilter=un,this.wrapR=Vi,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class uv extends $t{constructor(e=null,t=1,i=1,r=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:i,depth:r},this.magFilter=un,this.minFilter=un,this.wrapR=Vi,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}const Dl=class Dl{constructor(e,t,i,r,s,a,o,l,c,u,f,h,d,m,g,p){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,i,r,s,a,o,l,c,u,f,h,d,m,g,p)}set(e,t,i,r,s,a,o,l,c,u,f,h,d,m,g,p){const _=this.elements;return _[0]=e,_[4]=t,_[8]=i,_[12]=r,_[1]=s,_[5]=a,_[9]=o,_[13]=l,_[2]=c,_[6]=u,_[10]=f,_[14]=h,_[3]=d,_[7]=m,_[11]=g,_[15]=p,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new Dl().fromArray(this.elements)}copy(e){const t=this.elements,i=e.elements;return t[0]=i[0],t[1]=i[1],t[2]=i[2],t[3]=i[3],t[4]=i[4],t[5]=i[5],t[6]=i[6],t[7]=i[7],t[8]=i[8],t[9]=i[9],t[10]=i[10],t[11]=i[11],t[12]=i[12],t[13]=i[13],t[14]=i[14],t[15]=i[15],this}copyPosition(e){const t=this.elements,i=e.elements;return t[12]=i[12],t[13]=i[13],t[14]=i[14],this}setFromMatrix3(e){const t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,i){return this.determinant()===0?(e.set(1,0,0),t.set(0,1,0),i.set(0,0,1),this):(e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),i.setFromMatrixColumn(this,2),this)}makeBasis(e,t,i){return this.set(e.x,t.x,i.x,0,e.y,t.y,i.y,0,e.z,t.z,i.z,0,0,0,0,1),this}extractRotation(e){if(e.determinant()===0)return this.identity();const t=this.elements,i=e.elements,r=1/us.setFromMatrixColumn(e,0).length(),s=1/us.setFromMatrixColumn(e,1).length(),a=1/us.setFromMatrixColumn(e,2).length();return t[0]=i[0]*r,t[1]=i[1]*r,t[2]=i[2]*r,t[3]=0,t[4]=i[4]*s,t[5]=i[5]*s,t[6]=i[6]*s,t[7]=0,t[8]=i[8]*a,t[9]=i[9]*a,t[10]=i[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){const t=this.elements,i=e.x,r=e.y,s=e.z,a=Math.cos(i),o=Math.sin(i),l=Math.cos(r),c=Math.sin(r),u=Math.cos(s),f=Math.sin(s);if(e.order==="XYZ"){const h=a*u,d=a*f,m=o*u,g=o*f;t[0]=l*u,t[4]=-l*f,t[8]=c,t[1]=d+m*c,t[5]=h-g*c,t[9]=-o*l,t[2]=g-h*c,t[6]=m+d*c,t[10]=a*l}else if(e.order==="YXZ"){const h=l*u,d=l*f,m=c*u,g=c*f;t[0]=h+g*o,t[4]=m*o-d,t[8]=a*c,t[1]=a*f,t[5]=a*u,t[9]=-o,t[2]=d*o-m,t[6]=g+h*o,t[10]=a*l}else if(e.order==="ZXY"){const h=l*u,d=l*f,m=c*u,g=c*f;t[0]=h-g*o,t[4]=-a*f,t[8]=m+d*o,t[1]=d+m*o,t[5]=a*u,t[9]=g-h*o,t[2]=-a*c,t[6]=o,t[10]=a*l}else if(e.order==="ZYX"){const h=a*u,d=a*f,m=o*u,g=o*f;t[0]=l*u,t[4]=m*c-d,t[8]=h*c+g,t[1]=l*f,t[5]=g*c+h,t[9]=d*c-m,t[2]=-c,t[6]=o*l,t[10]=a*l}else if(e.order==="YZX"){const h=a*l,d=a*c,m=o*l,g=o*c;t[0]=l*u,t[4]=g-h*f,t[8]=m*f+d,t[1]=f,t[5]=a*u,t[9]=-o*u,t[2]=-c*u,t[6]=d*f+m,t[10]=h-g*f}else if(e.order==="XZY"){const h=a*l,d=a*c,m=o*l,g=o*c;t[0]=l*u,t[4]=-f,t[8]=c*u,t[1]=h*f+g,t[5]=a*u,t[9]=d*f-m,t[2]=m*f-d,t[6]=o*u,t[10]=g*f+h}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(hv,e,fv)}lookAt(e,t,i){const r=this.elements;return Bn.subVectors(e,t),Bn.lengthSq()===0&&(Bn.z=1),Bn.normalize(),nr.crossVectors(i,Bn),nr.lengthSq()===0&&(Math.abs(i.z)===1?Bn.x+=1e-4:Bn.z+=1e-4,Bn.normalize(),nr.crossVectors(i,Bn)),nr.normalize(),lo.crossVectors(Bn,nr),r[0]=nr.x,r[4]=lo.x,r[8]=Bn.x,r[1]=nr.y,r[5]=lo.y,r[9]=Bn.y,r[2]=nr.z,r[6]=lo.z,r[10]=Bn.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const i=e.elements,r=t.elements,s=this.elements,a=i[0],o=i[4],l=i[8],c=i[12],u=i[1],f=i[5],h=i[9],d=i[13],m=i[2],g=i[6],p=i[10],_=i[14],v=i[3],S=i[7],y=i[11],M=i[15],T=r[0],w=r[4],b=r[8],x=r[12],A=r[1],P=r[5],R=r[9],L=r[13],I=r[2],N=r[6],O=r[10],B=r[14],q=r[3],F=r[7],k=r[11],U=r[15];return s[0]=a*T+o*A+l*I+c*q,s[4]=a*w+o*P+l*N+c*F,s[8]=a*b+o*R+l*O+c*k,s[12]=a*x+o*L+l*B+c*U,s[1]=u*T+f*A+h*I+d*q,s[5]=u*w+f*P+h*N+d*F,s[9]=u*b+f*R+h*O+d*k,s[13]=u*x+f*L+h*B+d*U,s[2]=m*T+g*A+p*I+_*q,s[6]=m*w+g*P+p*N+_*F,s[10]=m*b+g*R+p*O+_*k,s[14]=m*x+g*L+p*B+_*U,s[3]=v*T+S*A+y*I+M*q,s[7]=v*w+S*P+y*N+M*F,s[11]=v*b+S*R+y*O+M*k,s[15]=v*x+S*L+y*B+M*U,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){const e=this.elements,t=e[0],i=e[4],r=e[8],s=e[12],a=e[1],o=e[5],l=e[9],c=e[13],u=e[2],f=e[6],h=e[10],d=e[14],m=e[3],g=e[7],p=e[11],_=e[15],v=l*d-c*h,S=o*d-c*f,y=o*h-l*f,M=a*d-c*u,T=a*h-l*u,w=a*f-o*u;return t*(g*v-p*S+_*y)-i*(m*v-p*M+_*T)+r*(m*S-g*M+_*w)-s*(m*y-g*T+p*w)}transpose(){const e=this.elements;let t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,i){const r=this.elements;return e.isVector3?(r[12]=e.x,r[13]=e.y,r[14]=e.z):(r[12]=e,r[13]=t,r[14]=i),this}invert(){const e=this.elements,t=e[0],i=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8],f=e[9],h=e[10],d=e[11],m=e[12],g=e[13],p=e[14],_=e[15],v=t*o-i*a,S=t*l-r*a,y=t*c-s*a,M=i*l-r*o,T=i*c-s*o,w=r*c-s*l,b=u*g-f*m,x=u*p-h*m,A=u*_-d*m,P=f*p-h*g,R=f*_-d*g,L=h*_-d*p,I=v*L-S*R+y*P+M*A-T*x+w*b;if(I===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const N=1/I;return e[0]=(o*L-l*R+c*P)*N,e[1]=(r*R-i*L-s*P)*N,e[2]=(g*w-p*T+_*M)*N,e[3]=(h*T-f*w-d*M)*N,e[4]=(l*A-a*L-c*x)*N,e[5]=(t*L-r*A+s*x)*N,e[6]=(p*y-m*w-_*S)*N,e[7]=(u*w-h*y+d*S)*N,e[8]=(a*R-o*A+c*b)*N,e[9]=(i*A-t*R-s*b)*N,e[10]=(m*T-g*y+_*v)*N,e[11]=(f*y-u*T-d*v)*N,e[12]=(o*x-a*P-l*b)*N,e[13]=(t*P-i*x+r*b)*N,e[14]=(g*S-m*M-p*v)*N,e[15]=(u*M-f*S+h*v)*N,this}scale(e){const t=this.elements,i=e.x,r=e.y,s=e.z;return t[0]*=i,t[4]*=r,t[8]*=s,t[1]*=i,t[5]*=r,t[9]*=s,t[2]*=i,t[6]*=r,t[10]*=s,t[3]*=i,t[7]*=r,t[11]*=s,this}getMaxScaleOnAxis(){const e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],i=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],r=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,i,r))}makeTranslation(e,t,i){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,i,0,0,0,1),this}makeRotationX(e){const t=Math.cos(e),i=Math.sin(e);return this.set(1,0,0,0,0,t,-i,0,0,i,t,0,0,0,0,1),this}makeRotationY(e){const t=Math.cos(e),i=Math.sin(e);return this.set(t,0,i,0,0,1,0,0,-i,0,t,0,0,0,0,1),this}makeRotationZ(e){const t=Math.cos(e),i=Math.sin(e);return this.set(t,-i,0,0,i,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){const i=Math.cos(t),r=Math.sin(t),s=1-i,a=e.x,o=e.y,l=e.z,c=s*a,u=s*o;return this.set(c*a+i,c*o-r*l,c*l+r*o,0,c*o+r*l,u*o+i,u*l-r*a,0,c*l-r*o,u*l+r*a,s*l*l+i,0,0,0,0,1),this}makeScale(e,t,i){return this.set(e,0,0,0,0,t,0,0,0,0,i,0,0,0,0,1),this}makeShear(e,t,i,r,s,a){return this.set(1,i,s,0,e,1,a,0,t,r,1,0,0,0,0,1),this}compose(e,t,i){const r=this.elements,s=t._x,a=t._y,o=t._z,l=t._w,c=s+s,u=a+a,f=o+o,h=s*c,d=s*u,m=s*f,g=a*u,p=a*f,_=o*f,v=l*c,S=l*u,y=l*f,M=i.x,T=i.y,w=i.z;return r[0]=(1-(g+_))*M,r[1]=(d+y)*M,r[2]=(m-S)*M,r[3]=0,r[4]=(d-y)*T,r[5]=(1-(h+_))*T,r[6]=(p+v)*T,r[7]=0,r[8]=(m+S)*w,r[9]=(p-v)*w,r[10]=(1-(h+g))*w,r[11]=0,r[12]=e.x,r[13]=e.y,r[14]=e.z,r[15]=1,this}decompose(e,t,i){const r=this.elements;e.x=r[12],e.y=r[13],e.z=r[14];const s=this.determinant();if(s===0)return i.set(1,1,1),t.identity(),this;let a=us.set(r[0],r[1],r[2]).length();const o=us.set(r[4],r[5],r[6]).length(),l=us.set(r[8],r[9],r[10]).length();s<0&&(a=-a),oi.copy(this);const c=1/a,u=1/o,f=1/l;return oi.elements[0]*=c,oi.elements[1]*=c,oi.elements[2]*=c,oi.elements[4]*=u,oi.elements[5]*=u,oi.elements[6]*=u,oi.elements[8]*=f,oi.elements[9]*=f,oi.elements[10]*=f,t.setFromRotationMatrix(oi),i.x=a,i.y=o,i.z=l,this}makePerspective(e,t,i,r,s,a,o=Ri,l=!1){const c=this.elements,u=2*s/(t-e),f=2*s/(i-r),h=(t+e)/(t-e),d=(i+r)/(i-r);let m,g;if(l)m=s/(a-s),g=a*s/(a-s);else if(o===Ri)m=-(a+s)/(a-s),g=-2*a*s/(a-s);else if(o===fl)m=-a/(a-s),g=-a*s/(a-s);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return c[0]=u,c[4]=0,c[8]=h,c[12]=0,c[1]=0,c[5]=f,c[9]=d,c[13]=0,c[2]=0,c[6]=0,c[10]=m,c[14]=g,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,i,r,s,a,o=Ri,l=!1){const c=this.elements,u=2/(t-e),f=2/(i-r),h=-(t+e)/(t-e),d=-(i+r)/(i-r);let m,g;if(l)m=1/(a-s),g=a/(a-s);else if(o===Ri)m=-2/(a-s),g=-(a+s)/(a-s);else if(o===fl)m=-1/(a-s),g=-s/(a-s);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return c[0]=u,c[4]=0,c[8]=0,c[12]=h,c[1]=0,c[5]=f,c[9]=0,c[13]=d,c[2]=0,c[6]=0,c[10]=m,c[14]=g,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){const t=this.elements,i=e.elements;for(let r=0;r<16;r++)if(t[r]!==i[r])return!1;return!0}fromArray(e,t=0){for(let i=0;i<16;i++)this.elements[i]=e[i+t];return this}toArray(e=[],t=0){const i=this.elements;return e[t]=i[0],e[t+1]=i[1],e[t+2]=i[2],e[t+3]=i[3],e[t+4]=i[4],e[t+5]=i[5],e[t+6]=i[6],e[t+7]=i[7],e[t+8]=i[8],e[t+9]=i[9],e[t+10]=i[10],e[t+11]=i[11],e[t+12]=i[12],e[t+13]=i[13],e[t+14]=i[14],e[t+15]=i[15],e}};Dl.prototype.isMatrix4=!0;let zt=Dl;const us=new $,oi=new zt,hv=new $(0,0,0),fv=new $(1,1,1),nr=new $,lo=new $,Bn=new $,dd=new zt,pd=new br;class Jr{constructor(e=0,t=0,i=0,r=Jr.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=i,this._order=r}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,i,r=this._order){return this._x=e,this._y=t,this._z=i,this._order=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,i=!0){const r=e.elements,s=r[0],a=r[4],o=r[8],l=r[1],c=r[5],u=r[9],f=r[2],h=r[6],d=r[10];switch(t){case"XYZ":this._y=Math.asin(lt(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-u,d),this._z=Math.atan2(-a,s)):(this._x=Math.atan2(h,c),this._z=0);break;case"YXZ":this._x=Math.asin(-lt(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(o,d),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-f,s),this._z=0);break;case"ZXY":this._x=Math.asin(lt(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(-f,d),this._z=Math.atan2(-a,c)):(this._y=0,this._z=Math.atan2(l,s));break;case"ZYX":this._y=Math.asin(-lt(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(h,d),this._z=Math.atan2(l,s)):(this._x=0,this._z=Math.atan2(-a,c));break;case"YZX":this._z=Math.asin(lt(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-u,c),this._y=Math.atan2(-f,s)):(this._x=0,this._y=Math.atan2(o,d));break;case"XZY":this._z=Math.asin(-lt(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(h,c),this._y=Math.atan2(o,s)):(this._x=Math.atan2(-u,d),this._y=0);break;default:Je("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,i===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,i){return dd.makeRotationFromQuaternion(e),this.setFromRotationMatrix(dd,t,i)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return pd.setFromEuler(this),this.setFromQuaternion(pd,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}Jr.DEFAULT_ORDER="XYZ";class zm{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let dv=0;const md=new $,hs=new br,Ni=new zt,co=new $,fa=new $,pv=new $,mv=new br,gd=new $(1,0,0),_d=new $(0,1,0),vd=new $(0,0,1),xd={type:"added"},gv={type:"removed"},fs={type:"childadded",child:null},pc={type:"childremoved",child:null};class _n extends pi{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:dv++}),this.uuid=_r(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=_n.DEFAULT_UP.clone();const e=new $,t=new Jr,i=new br,r=new $(1,1,1);function s(){i.setFromEuler(t,!1)}function a(){t.setFromQuaternion(i,void 0,!1)}t._onChange(s),i._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:i},scale:{configurable:!0,enumerable:!0,value:r},modelViewMatrix:{value:new zt},normalMatrix:{value:new it}}),this.matrix=new zt,this.matrixWorld=new zt,this.matrixAutoUpdate=_n.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=_n.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new zm,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return hs.setFromAxisAngle(e,t),this.quaternion.multiply(hs),this}rotateOnWorldAxis(e,t){return hs.setFromAxisAngle(e,t),this.quaternion.premultiply(hs),this}rotateX(e){return this.rotateOnAxis(gd,e)}rotateY(e){return this.rotateOnAxis(_d,e)}rotateZ(e){return this.rotateOnAxis(vd,e)}translateOnAxis(e,t){return md.copy(e).applyQuaternion(this.quaternion),this.position.add(md.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(gd,e)}translateY(e){return this.translateOnAxis(_d,e)}translateZ(e){return this.translateOnAxis(vd,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(Ni.copy(this.matrixWorld).invert())}lookAt(e,t,i){e.isVector3?co.copy(e):co.set(e,t,i);const r=this.parent;this.updateWorldMatrix(!0,!1),fa.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?Ni.lookAt(fa,co,this.up):Ni.lookAt(co,fa,this.up),this.quaternion.setFromRotationMatrix(Ni),r&&(Ni.extractRotation(r.matrixWorld),hs.setFromRotationMatrix(Ni),this.quaternion.premultiply(hs.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(pt("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(xd),fs.child=e,this.dispatchEvent(fs),fs.child=null):pt("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let i=0;i<arguments.length;i++)this.remove(arguments[i]);return this}const t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(gv),pc.child=e,this.dispatchEvent(pc),pc.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),Ni.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),Ni.multiply(e.parent.matrixWorld)),e.applyMatrix4(Ni),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(xd),fs.child=e,this.dispatchEvent(fs),fs.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let i=0,r=this.children.length;i<r;i++){const a=this.children[i].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,i=[]){this[e]===t&&i.push(this);const r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].getObjectsByProperty(e,t,i);return i}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(fa,e,pv),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(fa,mv,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}traverse(e){e(this);const t=this.children;for(let i=0,r=t.length;i<r;i++)t[i].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const t=this.children;for(let i=0,r=t.length;i<r;i++)t[i].traverseVisible(e)}traverseAncestors(e){const t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);const e=this.pivot;if(e!==null){const t=e.x,i=e.y,r=e.z,s=this.matrix.elements;s[12]+=t-s[0]*t-s[4]*i-s[8]*r,s[13]+=i-s[1]*t-s[5]*i-s[9]*r,s[14]+=r-s[2]*t-s[6]*i-s[10]*r}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const t=this.children;for(let i=0,r=t.length;i<r;i++)t[i].updateMatrixWorld(e)}updateWorldMatrix(e,t){const i=this.parent;if(e===!0&&i!==null&&i.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),t===!0){const r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].updateWorldMatrix(!1,!0)}}toJSON(e){const t=e===void 0||typeof e=="string",i={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},i.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});const r={};r.uuid=this.uuid,r.type=this.type,this.name!==""&&(r.name=this.name),this.castShadow===!0&&(r.castShadow=!0),this.receiveShadow===!0&&(r.receiveShadow=!0),this.visible===!1&&(r.visible=!1),this.frustumCulled===!1&&(r.frustumCulled=!1),this.renderOrder!==0&&(r.renderOrder=this.renderOrder),this.static!==!1&&(r.static=this.static),Object.keys(this.userData).length>0&&(r.userData=this.userData),r.layers=this.layers.mask,r.matrix=this.matrix.toArray(),r.up=this.up.toArray(),this.pivot!==null&&(r.pivot=this.pivot.toArray()),this.matrixAutoUpdate===!1&&(r.matrixAutoUpdate=!1),this.morphTargetDictionary!==void 0&&(r.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(r.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(r.type="InstancedMesh",r.count=this.count,r.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(r.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(r.type="BatchedMesh",r.perObjectFrustumCulled=this.perObjectFrustumCulled,r.sortObjects=this.sortObjects,r.drawRanges=this._drawRanges,r.reservedRanges=this._reservedRanges,r.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),r.instanceInfo=this._instanceInfo.map(o=>({...o})),r.availableInstanceIds=this._availableInstanceIds.slice(),r.availableGeometryIds=this._availableGeometryIds.slice(),r.nextIndexStart=this._nextIndexStart,r.nextVertexStart=this._nextVertexStart,r.geometryCount=this._geometryCount,r.maxInstanceCount=this._maxInstanceCount,r.maxVertexCount=this._maxVertexCount,r.maxIndexCount=this._maxIndexCount,r.geometryInitialized=this._geometryInitialized,r.matricesTexture=this._matricesTexture.toJSON(e),r.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(r.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(r.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(r.boundingBox=this.boundingBox.toJSON()));function s(o,l){return o[l.uuid]===void 0&&(o[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?r.background=this.background.toJSON():this.background.isTexture&&(r.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(r.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){r.geometry=s(e.geometries,this.geometry);const o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){const l=o.shapes;if(Array.isArray(l))for(let c=0,u=l.length;c<u;c++){const f=l[c];s(e.shapes,f)}else s(e.shapes,l)}}if(this.isSkinnedMesh&&(r.bindMode=this.bindMode,r.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(s(e.skeletons,this.skeleton),r.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const o=[];for(let l=0,c=this.material.length;l<c;l++)o.push(s(e.materials,this.material[l]));r.material=o}else r.material=s(e.materials,this.material);if(this.children.length>0){r.children=[];for(let o=0;o<this.children.length;o++)r.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){r.animations=[];for(let o=0;o<this.animations.length;o++){const l=this.animations[o];r.animations.push(s(e.animations,l))}}if(t){const o=a(e.geometries),l=a(e.materials),c=a(e.textures),u=a(e.images),f=a(e.shapes),h=a(e.skeletons),d=a(e.animations),m=a(e.nodes);o.length>0&&(i.geometries=o),l.length>0&&(i.materials=l),c.length>0&&(i.textures=c),u.length>0&&(i.images=u),f.length>0&&(i.shapes=f),h.length>0&&(i.skeletons=h),d.length>0&&(i.animations=d),m.length>0&&(i.nodes=m)}return i.object=r,i;function a(o){const l=[];for(const c in o){const u=o[c];delete u.metadata,l.push(u)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let i=0;i<e.children.length;i++){const r=e.children[i];this.add(r.clone())}return this}}_n.DEFAULT_UP=new $(0,1,0);_n.DEFAULT_MATRIX_AUTO_UPDATE=!0;_n.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;class Cs extends _n{constructor(){super(),this.isGroup=!0,this.type="Group"}}const _v={type:"move"};class mc{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new Cs,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new Cs,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new $,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new $),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new Cs,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new $,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new $,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const t=this._hand;if(t)for(const i of e.hand.values())this._getHandJoint(t,i)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,i){let r=null,s=null,a=null;const o=this._targetRay,l=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){a=!0;for(const g of e.hand.values()){const p=t.getJointPose(g,i),_=this._getHandJoint(c,g);p!==null&&(_.matrix.fromArray(p.transform.matrix),_.matrix.decompose(_.position,_.rotation,_.scale),_.matrixWorldNeedsUpdate=!0,_.jointRadius=p.radius),_.visible=p!==null}const u=c.joints["index-finger-tip"],f=c.joints["thumb-tip"],h=u.position.distanceTo(f.position),d=.02,m=.005;c.inputState.pinching&&h>d+m?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&h<=d-m&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(s=t.getPose(e.gripSpace,i),s!==null&&(l.matrix.fromArray(s.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,s.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(s.linearVelocity)):l.hasLinearVelocity=!1,s.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(s.angularVelocity)):l.hasAngularVelocity=!1,l.eventsEnabled&&l.dispatchEvent({type:"gripUpdated",data:e,target:this})));o!==null&&(r=t.getPose(e.targetRaySpace,i),r===null&&s!==null&&(r=s),r!==null&&(o.matrix.fromArray(r.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,r.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(r.linearVelocity)):o.hasLinearVelocity=!1,r.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(r.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(_v)))}return o!==null&&(o.visible=r!==null),l!==null&&(l.visible=s!==null),c!==null&&(c.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){const i=new Cs;i.matrixAutoUpdate=!1,i.visible=!1,e.joints[t.jointName]=i,e.add(i)}return e.joints[t.jointName]}}const Gm={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},ir={h:0,s:0,l:0},uo={h:0,s:0,l:0};function gc(n,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?n+(e-n)*6*t:t<1/2?e:t<2/3?n+(e-n)*6*(2/3-t):n}class ut{constructor(e,t,i){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,i)}set(e,t,i){if(t===void 0&&i===void 0){const r=e;r&&r.isColor?this.copy(r):typeof r=="number"?this.setHex(r):typeof r=="string"&&this.setStyle(r)}else this.setRGB(e,t,i);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=Et){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,ft.colorSpaceToWorking(this,t),this}setRGB(e,t,i,r=ft.workingColorSpace){return this.r=e,this.g=t,this.b=i,ft.colorSpaceToWorking(this,r),this}setHSL(e,t,i,r=ft.workingColorSpace){if(e=iv(e,1),t=lt(t,0,1),i=lt(i,0,1),t===0)this.r=this.g=this.b=i;else{const s=i<=.5?i*(1+t):i+t-i*t,a=2*i-s;this.r=gc(a,s,e+1/3),this.g=gc(a,s,e),this.b=gc(a,s,e-1/3)}return ft.colorSpaceToWorking(this,r),this}setStyle(e,t=Et){function i(s){s!==void 0&&parseFloat(s)<1&&Je("Color: Alpha component of "+e+" will be ignored.")}let r;if(r=/^(\w+)\(([^\)]*)\)/.exec(e)){let s;const a=r[1],o=r[2];switch(a){case"rgb":case"rgba":if(s=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return i(s[4]),this.setRGB(Math.min(255,parseInt(s[1],10))/255,Math.min(255,parseInt(s[2],10))/255,Math.min(255,parseInt(s[3],10))/255,t);if(s=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return i(s[4]),this.setRGB(Math.min(100,parseInt(s[1],10))/100,Math.min(100,parseInt(s[2],10))/100,Math.min(100,parseInt(s[3],10))/100,t);break;case"hsl":case"hsla":if(s=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return i(s[4]),this.setHSL(parseFloat(s[1])/360,parseFloat(s[2])/100,parseFloat(s[3])/100,t);break;default:Je("Color: Unknown color model "+e)}}else if(r=/^\#([A-Fa-f\d]+)$/.exec(e)){const s=r[1],a=s.length;if(a===3)return this.setRGB(parseInt(s.charAt(0),16)/15,parseInt(s.charAt(1),16)/15,parseInt(s.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(s,16),t);Je("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=Et){const i=Gm[e.toLowerCase()];return i!==void 0?this.setHex(i,t):Je("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Wi(e.r),this.g=Wi(e.g),this.b=Wi(e.b),this}copyLinearToSRGB(e){return this.r=Ls(e.r),this.g=Ls(e.g),this.b=Ls(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=Et){return ft.workingToColorSpace(pn.copy(this),e),Math.round(lt(pn.r*255,0,255))*65536+Math.round(lt(pn.g*255,0,255))*256+Math.round(lt(pn.b*255,0,255))}getHexString(e=Et){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=ft.workingColorSpace){ft.workingToColorSpace(pn.copy(this),t);const i=pn.r,r=pn.g,s=pn.b,a=Math.max(i,r,s),o=Math.min(i,r,s);let l,c;const u=(o+a)/2;if(o===a)l=0,c=0;else{const f=a-o;switch(c=u<=.5?f/(a+o):f/(2-a-o),a){case i:l=(r-s)/f+(r<s?6:0);break;case r:l=(s-i)/f+2;break;case s:l=(i-r)/f+4;break}l/=6}return e.h=l,e.s=c,e.l=u,e}getRGB(e,t=ft.workingColorSpace){return ft.workingToColorSpace(pn.copy(this),t),e.r=pn.r,e.g=pn.g,e.b=pn.b,e}getStyle(e=Et){ft.workingToColorSpace(pn.copy(this),e);const t=pn.r,i=pn.g,r=pn.b;return e!==Et?`color(${e} ${t.toFixed(3)} ${i.toFixed(3)} ${r.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(i*255)},${Math.round(r*255)})`}offsetHSL(e,t,i){return this.getHSL(ir),this.setHSL(ir.h+e,ir.s+t,ir.l+i)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,i){return this.r=e.r+(t.r-e.r)*i,this.g=e.g+(t.g-e.g)*i,this.b=e.b+(t.b-e.b)*i,this}lerpHSL(e,t){this.getHSL(ir),e.getHSL(uo);const i=cc(ir.h,uo.h,t),r=cc(ir.s,uo.s,t),s=cc(ir.l,uo.l,t);return this.setHSL(i,r,s),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const t=this.r,i=this.g,r=this.b,s=e.elements;return this.r=s[0]*t+s[3]*i+s[6]*r,this.g=s[1]*t+s[4]*i+s[7]*r,this.b=s[2]*t+s[5]*i+s[8]*r,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const pn=new ut;ut.NAMES=Gm;class ph extends _n{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new Jr,this.environmentIntensity=1,this.environmentRotation=new Jr,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(t.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(t.object.backgroundIntensity=this.backgroundIntensity),t.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(t.object.environmentIntensity=this.environmentIntensity),t.object.environmentRotation=this.environmentRotation.toArray(),t}}const li=new $,Oi=new $,_c=new $,Bi=new $,ds=new $,ps=new $,yd=new $,vc=new $,xc=new $,yc=new $,bc=new Ut,Sc=new Ut,Mc=new Ut;class Qn{constructor(e=new $,t=new $,i=new $){this.a=e,this.b=t,this.c=i}static getNormal(e,t,i,r){r.subVectors(i,t),li.subVectors(e,t),r.cross(li);const s=r.lengthSq();return s>0?r.multiplyScalar(1/Math.sqrt(s)):r.set(0,0,0)}static getBarycoord(e,t,i,r,s){li.subVectors(r,t),Oi.subVectors(i,t),_c.subVectors(e,t);const a=li.dot(li),o=li.dot(Oi),l=li.dot(_c),c=Oi.dot(Oi),u=Oi.dot(_c),f=a*c-o*o;if(f===0)return s.set(0,0,0),null;const h=1/f,d=(c*l-o*u)*h,m=(a*u-o*l)*h;return s.set(1-d-m,m,d)}static containsPoint(e,t,i,r){return this.getBarycoord(e,t,i,r,Bi)===null?!1:Bi.x>=0&&Bi.y>=0&&Bi.x+Bi.y<=1}static getInterpolation(e,t,i,r,s,a,o,l){return this.getBarycoord(e,t,i,r,Bi)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(s,Bi.x),l.addScaledVector(a,Bi.y),l.addScaledVector(o,Bi.z),l)}static getInterpolatedAttribute(e,t,i,r,s,a){return bc.setScalar(0),Sc.setScalar(0),Mc.setScalar(0),bc.fromBufferAttribute(e,t),Sc.fromBufferAttribute(e,i),Mc.fromBufferAttribute(e,r),a.setScalar(0),a.addScaledVector(bc,s.x),a.addScaledVector(Sc,s.y),a.addScaledVector(Mc,s.z),a}static isFrontFacing(e,t,i,r){return li.subVectors(i,t),Oi.subVectors(e,t),li.cross(Oi).dot(r)<0}set(e,t,i){return this.a.copy(e),this.b.copy(t),this.c.copy(i),this}setFromPointsAndIndices(e,t,i,r){return this.a.copy(e[t]),this.b.copy(e[i]),this.c.copy(e[r]),this}setFromAttributeAndIndices(e,t,i,r){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,i),this.c.fromBufferAttribute(e,r),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return li.subVectors(this.c,this.b),Oi.subVectors(this.a,this.b),li.cross(Oi).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return Qn.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return Qn.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,i,r,s){return Qn.getInterpolation(e,this.a,this.b,this.c,t,i,r,s)}containsPoint(e){return Qn.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return Qn.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){const i=this.a,r=this.b,s=this.c;let a,o;ds.subVectors(r,i),ps.subVectors(s,i),vc.subVectors(e,i);const l=ds.dot(vc),c=ps.dot(vc);if(l<=0&&c<=0)return t.copy(i);xc.subVectors(e,r);const u=ds.dot(xc),f=ps.dot(xc);if(u>=0&&f<=u)return t.copy(r);const h=l*f-u*c;if(h<=0&&l>=0&&u<=0)return a=l/(l-u),t.copy(i).addScaledVector(ds,a);yc.subVectors(e,s);const d=ds.dot(yc),m=ps.dot(yc);if(m>=0&&d<=m)return t.copy(s);const g=d*c-l*m;if(g<=0&&c>=0&&m<=0)return o=c/(c-m),t.copy(i).addScaledVector(ps,o);const p=u*m-d*f;if(p<=0&&f-u>=0&&d-m>=0)return yd.subVectors(s,r),o=(f-u)/(f-u+(d-m)),t.copy(r).addScaledVector(yd,o);const _=1/(p+g+h);return a=g*_,o=h*_,t.copy(i).addScaledVector(ds,a).addScaledVector(ps,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}class Ks{constructor(e=new $(1/0,1/0,1/0),t=new $(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,i=e.length;t<i;t+=3)this.expandByPoint(ci.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,i=e.count;t<i;t++)this.expandByPoint(ci.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,i=e.length;t<i;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){const i=ci.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(i),this.max.copy(e).add(i),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);const i=e.geometry;if(i!==void 0){const s=i.getAttribute("position");if(t===!0&&s!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=s.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,ci):ci.fromBufferAttribute(s,a),ci.applyMatrix4(e.matrixWorld),this.expandByPoint(ci);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),ho.copy(e.boundingBox)):(i.boundingBox===null&&i.computeBoundingBox(),ho.copy(i.boundingBox)),ho.applyMatrix4(e.matrixWorld),this.union(ho)}const r=e.children;for(let s=0,a=r.length;s<a;s++)this.expandByObject(r[s],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,ci),ci.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,i;return e.normal.x>0?(t=e.normal.x*this.min.x,i=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,i=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,i+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,i+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,i+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,i+=e.normal.z*this.min.z),t<=-e.constant&&i>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(da),fo.subVectors(this.max,da),ms.subVectors(e.a,da),gs.subVectors(e.b,da),_s.subVectors(e.c,da),rr.subVectors(gs,ms),sr.subVectors(_s,gs),Cr.subVectors(ms,_s);let t=[0,-rr.z,rr.y,0,-sr.z,sr.y,0,-Cr.z,Cr.y,rr.z,0,-rr.x,sr.z,0,-sr.x,Cr.z,0,-Cr.x,-rr.y,rr.x,0,-sr.y,sr.x,0,-Cr.y,Cr.x,0];return!Tc(t,ms,gs,_s,fo)||(t=[1,0,0,0,1,0,0,0,1],!Tc(t,ms,gs,_s,fo))?!1:(po.crossVectors(rr,sr),t=[po.x,po.y,po.z],Tc(t,ms,gs,_s,fo))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,ci).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(ci).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(ki[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),ki[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),ki[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),ki[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),ki[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),ki[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),ki[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),ki[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(ki),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}const ki=[new $,new $,new $,new $,new $,new $,new $,new $],ci=new $,ho=new Ks,ms=new $,gs=new $,_s=new $,rr=new $,sr=new $,Cr=new $,da=new $,fo=new $,po=new $,Pr=new $;function Tc(n,e,t,i,r){for(let s=0,a=n.length-3;s<=a;s+=3){Pr.fromArray(n,s);const o=r.x*Math.abs(Pr.x)+r.y*Math.abs(Pr.y)+r.z*Math.abs(Pr.z),l=e.dot(Pr),c=t.dot(Pr),u=i.dot(Pr);if(Math.max(-Math.max(l,c,u),Math.min(l,c,u))>o)return!1}return!0}const Xt=new $,mo=new Xe;let vv=0;class Nt extends pi{constructor(e,t,i=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:vv++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=i,this.usage=hh,this.updateRanges=[],this.gpuType=hi,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,i){e*=this.itemSize,i*=t.itemSize;for(let r=0,s=this.itemSize;r<s;r++)this.array[e+r]=t.array[i+r];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,i=this.count;t<i;t++)mo.fromBufferAttribute(this,t),mo.applyMatrix3(e),this.setXY(t,mo.x,mo.y);else if(this.itemSize===3)for(let t=0,i=this.count;t<i;t++)Xt.fromBufferAttribute(this,t),Xt.applyMatrix3(e),this.setXYZ(t,Xt.x,Xt.y,Xt.z);return this}applyMatrix4(e){for(let t=0,i=this.count;t<i;t++)Xt.fromBufferAttribute(this,t),Xt.applyMatrix4(e),this.setXYZ(t,Xt.x,Xt.y,Xt.z);return this}applyNormalMatrix(e){for(let t=0,i=this.count;t<i;t++)Xt.fromBufferAttribute(this,t),Xt.applyNormalMatrix(e),this.setXYZ(t,Xt.x,Xt.y,Xt.z);return this}transformDirection(e){for(let t=0,i=this.count;t<i;t++)Xt.fromBufferAttribute(this,t),Xt.transformDirection(e),this.setXYZ(t,Xt.x,Xt.y,Xt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let i=this.array[e*this.itemSize+t];return this.normalized&&(i=Ei(i,this.array)),i}setComponent(e,t,i){return this.normalized&&(i=St(i,this.array)),this.array[e*this.itemSize+t]=i,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=Ei(t,this.array)),t}setX(e,t){return this.normalized&&(t=St(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=Ei(t,this.array)),t}setY(e,t){return this.normalized&&(t=St(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=Ei(t,this.array)),t}setZ(e,t){return this.normalized&&(t=St(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=Ei(t,this.array)),t}setW(e,t){return this.normalized&&(t=St(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,i){return e*=this.itemSize,this.normalized&&(t=St(t,this.array),i=St(i,this.array)),this.array[e+0]=t,this.array[e+1]=i,this}setXYZ(e,t,i,r){return e*=this.itemSize,this.normalized&&(t=St(t,this.array),i=St(i,this.array),r=St(r,this.array)),this.array[e+0]=t,this.array[e+1]=i,this.array[e+2]=r,this}setXYZW(e,t,i,r,s){return e*=this.itemSize,this.normalized&&(t=St(t,this.array),i=St(i,this.array),r=St(r,this.array),s=St(s,this.array)),this.array[e+0]=t,this.array[e+1]=i,this.array[e+2]=r,this.array[e+3]=s,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==hh&&(e.usage=this.usage),e}dispose(){this.dispatchEvent({type:"dispose"})}}class Hm extends Nt{constructor(e,t,i){super(new Uint16Array(e),t,i)}}class Vm extends Nt{constructor(e,t,i){super(new Uint32Array(e),t,i)}}class di extends Nt{constructor(e,t,i){super(new Float32Array(e),t,i)}}const xv=new Ks,pa=new $,Ec=new $;class Zs{constructor(e=new $,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){const i=this.center;t!==void 0?i.copy(t):xv.setFromPoints(e).getCenter(i);let r=0;for(let s=0,a=e.length;s<a;s++)r=Math.max(r,i.distanceToSquared(e[s]));return this.radius=Math.sqrt(r),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){const i=this.center.distanceToSquared(e);return t.copy(e),i>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;pa.subVectors(e,this.center);const t=pa.lengthSq();if(t>this.radius*this.radius){const i=Math.sqrt(t),r=(i-this.radius)*.5;this.center.addScaledVector(pa,r/i),this.radius+=r}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Ec.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(pa.copy(e.center).add(Ec)),this.expandByPoint(pa.copy(e.center).sub(Ec))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}let yv=0;const $n=new zt,wc=new _n,vs=new $,kn=new Ks,ma=new Ks,rn=new $;class Dt extends pi{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:yv++}),this.uuid=_r(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(Q_(e)?Vm:Hm)(e,1):this.index=e,this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,i=0){this.groups.push({start:e,count:t,materialIndex:i})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){const t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);const i=this.attributes.normal;if(i!==void 0){const s=new it().getNormalMatrix(e);i.applyNormalMatrix(s),i.needsUpdate=!0}const r=this.attributes.tangent;return r!==void 0&&(r.transformDirection(e),r.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return $n.makeRotationFromQuaternion(e),this.applyMatrix4($n),this}rotateX(e){return $n.makeRotationX(e),this.applyMatrix4($n),this}rotateY(e){return $n.makeRotationY(e),this.applyMatrix4($n),this}rotateZ(e){return $n.makeRotationZ(e),this.applyMatrix4($n),this}translate(e,t,i){return $n.makeTranslation(e,t,i),this.applyMatrix4($n),this}scale(e,t,i){return $n.makeScale(e,t,i),this.applyMatrix4($n),this}lookAt(e){return wc.lookAt(e),wc.updateMatrix(),this.applyMatrix4(wc.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(vs).negate(),this.translate(vs.x,vs.y,vs.z),this}setFromPoints(e){const t=this.getAttribute("position");if(t===void 0){const i=[];for(let r=0,s=e.length;r<s;r++){const a=e[r];i.push(a.x,a.y,a.z||0)}this.setAttribute("position",new di(i,3))}else{const i=Math.min(e.length,t.count);for(let r=0;r<i;r++){const s=e[r];t.setXYZ(r,s.x,s.y,s.z||0)}e.length>t.count&&Je("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new Ks);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){pt("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new $(-1/0,-1/0,-1/0),new $(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let i=0,r=t.length;i<r;i++){const s=t[i];kn.setFromBufferAttribute(s),this.morphTargetsRelative?(rn.addVectors(this.boundingBox.min,kn.min),this.boundingBox.expandByPoint(rn),rn.addVectors(this.boundingBox.max,kn.max),this.boundingBox.expandByPoint(rn)):(this.boundingBox.expandByPoint(kn.min),this.boundingBox.expandByPoint(kn.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&pt('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Zs);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){pt("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new $,1/0);return}if(e){const i=this.boundingSphere.center;if(kn.setFromBufferAttribute(e),t)for(let s=0,a=t.length;s<a;s++){const o=t[s];ma.setFromBufferAttribute(o),this.morphTargetsRelative?(rn.addVectors(kn.min,ma.min),kn.expandByPoint(rn),rn.addVectors(kn.max,ma.max),kn.expandByPoint(rn)):(kn.expandByPoint(ma.min),kn.expandByPoint(ma.max))}kn.getCenter(i);let r=0;for(let s=0,a=e.count;s<a;s++)rn.fromBufferAttribute(e,s),r=Math.max(r,i.distanceToSquared(rn));if(t)for(let s=0,a=t.length;s<a;s++){const o=t[s],l=this.morphTargetsRelative;for(let c=0,u=o.count;c<u;c++)rn.fromBufferAttribute(o,c),l&&(vs.fromBufferAttribute(e,c),rn.add(vs)),r=Math.max(r,i.distanceToSquared(rn))}this.boundingSphere.radius=Math.sqrt(r),isNaN(this.boundingSphere.radius)&&pt('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){pt("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const i=t.position,r=t.normal,s=t.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new Nt(new Float32Array(4*i.count),4));const a=this.getAttribute("tangent"),o=[],l=[];for(let b=0;b<i.count;b++)o[b]=new $,l[b]=new $;const c=new $,u=new $,f=new $,h=new Xe,d=new Xe,m=new Xe,g=new $,p=new $;function _(b,x,A){c.fromBufferAttribute(i,b),u.fromBufferAttribute(i,x),f.fromBufferAttribute(i,A),h.fromBufferAttribute(s,b),d.fromBufferAttribute(s,x),m.fromBufferAttribute(s,A),u.sub(c),f.sub(c),d.sub(h),m.sub(h);const P=1/(d.x*m.y-m.x*d.y);isFinite(P)&&(g.copy(u).multiplyScalar(m.y).addScaledVector(f,-d.y).multiplyScalar(P),p.copy(f).multiplyScalar(d.x).addScaledVector(u,-m.x).multiplyScalar(P),o[b].add(g),o[x].add(g),o[A].add(g),l[b].add(p),l[x].add(p),l[A].add(p))}let v=this.groups;v.length===0&&(v=[{start:0,count:e.count}]);for(let b=0,x=v.length;b<x;++b){const A=v[b],P=A.start,R=A.count;for(let L=P,I=P+R;L<I;L+=3)_(e.getX(L+0),e.getX(L+1),e.getX(L+2))}const S=new $,y=new $,M=new $,T=new $;function w(b){M.fromBufferAttribute(r,b),T.copy(M);const x=o[b];S.copy(x),S.sub(M.multiplyScalar(M.dot(x))).normalize(),y.crossVectors(T,x);const P=y.dot(l[b])<0?-1:1;a.setXYZW(b,S.x,S.y,S.z,P)}for(let b=0,x=v.length;b<x;++b){const A=v[b],P=A.start,R=A.count;for(let L=P,I=P+R;L<I;L+=3)w(e.getX(L+0)),w(e.getX(L+1)),w(e.getX(L+2))}}computeVertexNormals(){const e=this.index,t=this.getAttribute("position");if(t!==void 0){let i=this.getAttribute("normal");if(i===void 0)i=new Nt(new Float32Array(t.count*3),3),this.setAttribute("normal",i);else for(let h=0,d=i.count;h<d;h++)i.setXYZ(h,0,0,0);const r=new $,s=new $,a=new $,o=new $,l=new $,c=new $,u=new $,f=new $;if(e)for(let h=0,d=e.count;h<d;h+=3){const m=e.getX(h+0),g=e.getX(h+1),p=e.getX(h+2);r.fromBufferAttribute(t,m),s.fromBufferAttribute(t,g),a.fromBufferAttribute(t,p),u.subVectors(a,s),f.subVectors(r,s),u.cross(f),o.fromBufferAttribute(i,m),l.fromBufferAttribute(i,g),c.fromBufferAttribute(i,p),o.add(u),l.add(u),c.add(u),i.setXYZ(m,o.x,o.y,o.z),i.setXYZ(g,l.x,l.y,l.z),i.setXYZ(p,c.x,c.y,c.z)}else for(let h=0,d=t.count;h<d;h+=3)r.fromBufferAttribute(t,h+0),s.fromBufferAttribute(t,h+1),a.fromBufferAttribute(t,h+2),u.subVectors(a,s),f.subVectors(r,s),u.cross(f),i.setXYZ(h+0,u.x,u.y,u.z),i.setXYZ(h+1,u.x,u.y,u.z),i.setXYZ(h+2,u.x,u.y,u.z);this.normalizeNormals(),i.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let t=0,i=e.count;t<i;t++)rn.fromBufferAttribute(e,t),rn.normalize(),e.setXYZ(t,rn.x,rn.y,rn.z)}toNonIndexed(){function e(o,l){const c=o.array,u=o.itemSize,f=o.normalized,h=new c.constructor(l.length*u);let d=0,m=0;for(let g=0,p=l.length;g<p;g++){o.isInterleavedBufferAttribute?d=l[g]*o.data.stride+o.offset:d=l[g]*u;for(let _=0;_<u;_++)h[m++]=c[d++]}return new Nt(h,u,f)}if(this.index===null)return Je("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const t=new Dt,i=this.index.array,r=this.attributes;for(const o in r){const l=r[o],c=e(l,i);t.setAttribute(o,c)}const s=this.morphAttributes;for(const o in s){const l=[],c=s[o];for(let u=0,f=c.length;u<f;u++){const h=c[u],d=e(h,i);l.push(d)}t.morphAttributes[o]=l}t.morphTargetsRelative=this.morphTargetsRelative;const a=this.groups;for(let o=0,l=a.length;o<l;o++){const c=a[o];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){const e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){const l=this.parameters;for(const c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};const t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});const i=this.attributes;for(const l in i){const c=i[l];e.data.attributes[l]=c.toJSON(e.data)}const r={};let s=!1;for(const l in this.morphAttributes){const c=this.morphAttributes[l],u=[];for(let f=0,h=c.length;f<h;f++){const d=c[f];u.push(d.toJSON(e.data))}u.length>0&&(r[l]=u,s=!0)}s&&(e.data.morphAttributes=r,e.data.morphTargetsRelative=this.morphTargetsRelative);const a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));const o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const t={};this.name=e.name;const i=e.index;i!==null&&this.setIndex(i.clone());const r=e.attributes;for(const c in r){const u=r[c];this.setAttribute(c,u.clone(t))}const s=e.morphAttributes;for(const c in s){const u=[],f=s[c];for(let h=0,d=f.length;h<d;h++)u.push(f[h].clone(t));this.morphAttributes[c]=u}this.morphTargetsRelative=e.morphTargetsRelative;const a=e.groups;for(let c=0,u=a.length;c<u;c++){const f=a[c];this.addGroup(f.start,f.count,f.materialIndex)}const o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());const l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}}class bv{constructor(e,t){this.isInterleavedBuffer=!0,this.array=e,this.stride=t,this.count=e!==void 0?e.length/t:0,this.usage=hh,this.updateRanges=[],this.version=0,this.uuid=_r()}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.array=new e.array.constructor(e.array),this.count=e.count,this.stride=e.stride,this.usage=e.usage,this}copyAt(e,t,i){e*=this.stride,i*=t.stride;for(let r=0,s=this.stride;r<s;r++)this.array[e+r]=t.array[i+r];return this}set(e,t=0){return this.array.set(e,t),this}clone(e){e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=_r()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer);const t=new this.array.constructor(e.arrayBuffers[this.array.buffer._uuid]),i=new this.constructor(t,this.stride);return i.setUsage(this.usage),i}onUpload(e){return this.onUploadCallback=e,this}toJSON(e){return e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=_r()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer))),{uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride}}}const bn=new $;class ml{constructor(e,t,i,r=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=e,this.itemSize=t,this.offset=i,this.normalized=r}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(e){this.data.needsUpdate=e}applyMatrix4(e){for(let t=0,i=this.data.count;t<i;t++)bn.fromBufferAttribute(this,t),bn.applyMatrix4(e),this.setXYZ(t,bn.x,bn.y,bn.z);return this}applyNormalMatrix(e){for(let t=0,i=this.count;t<i;t++)bn.fromBufferAttribute(this,t),bn.applyNormalMatrix(e),this.setXYZ(t,bn.x,bn.y,bn.z);return this}transformDirection(e){for(let t=0,i=this.count;t<i;t++)bn.fromBufferAttribute(this,t),bn.transformDirection(e),this.setXYZ(t,bn.x,bn.y,bn.z);return this}getComponent(e,t){let i=this.array[e*this.data.stride+this.offset+t];return this.normalized&&(i=Ei(i,this.array)),i}setComponent(e,t,i){return this.normalized&&(i=St(i,this.array)),this.data.array[e*this.data.stride+this.offset+t]=i,this}setX(e,t){return this.normalized&&(t=St(t,this.array)),this.data.array[e*this.data.stride+this.offset]=t,this}setY(e,t){return this.normalized&&(t=St(t,this.array)),this.data.array[e*this.data.stride+this.offset+1]=t,this}setZ(e,t){return this.normalized&&(t=St(t,this.array)),this.data.array[e*this.data.stride+this.offset+2]=t,this}setW(e,t){return this.normalized&&(t=St(t,this.array)),this.data.array[e*this.data.stride+this.offset+3]=t,this}getX(e){let t=this.data.array[e*this.data.stride+this.offset];return this.normalized&&(t=Ei(t,this.array)),t}getY(e){let t=this.data.array[e*this.data.stride+this.offset+1];return this.normalized&&(t=Ei(t,this.array)),t}getZ(e){let t=this.data.array[e*this.data.stride+this.offset+2];return this.normalized&&(t=Ei(t,this.array)),t}getW(e){let t=this.data.array[e*this.data.stride+this.offset+3];return this.normalized&&(t=Ei(t,this.array)),t}setXY(e,t,i){return e=e*this.data.stride+this.offset,this.normalized&&(t=St(t,this.array),i=St(i,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=i,this}setXYZ(e,t,i,r){return e=e*this.data.stride+this.offset,this.normalized&&(t=St(t,this.array),i=St(i,this.array),r=St(r,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=i,this.data.array[e+2]=r,this}setXYZW(e,t,i,r,s){return e=e*this.data.stride+this.offset,this.normalized&&(t=St(t,this.array),i=St(i,this.array),r=St(r,this.array),s=St(s,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=i,this.data.array[e+2]=r,this.data.array[e+3]=s,this}clone(e){if(e===void 0){pl("InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");const t=[];for(let i=0;i<this.count;i++){const r=i*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return new Nt(new this.array.constructor(t),this.itemSize,this.normalized)}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.clone(e)),new ml(e.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}toJSON(e){if(e===void 0){pl("InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");const t=[];for(let i=0;i<this.count;i++){const r=i*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:t,normalized:this.normalized}}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.toJSON(e)),{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}}let Sv=0;class $i extends pi{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Sv++}),this.uuid=_r(),this.name="",this.type="Material",this.blending=Hr,this.side=ji,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Eu,this.blendDst=wu,this.blendEquation=Br,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new ut(0,0,0),this.blendAlpha=0,this.depthFunc=Bs,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=od,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=ls,this.stencilZFail=ls,this.stencilZPass=ls,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const t in e){const i=e[t];if(i===void 0){Je(`Material: parameter '${t}' has value of undefined.`);continue}const r=this[t];if(r===void 0){Je(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}r&&r.isColor?r.set(i):r&&r.isVector3&&i&&i.isVector3?r.copy(i):this[t]=i}}toJSON(e){const t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});const i={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};i.uuid=this.uuid,i.type=this.type,this.name!==""&&(i.name=this.name),this.color&&this.color.isColor&&(i.color=this.color.getHex()),this.roughness!==void 0&&(i.roughness=this.roughness),this.metalness!==void 0&&(i.metalness=this.metalness),this.sheen!==void 0&&(i.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(i.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(i.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(i.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(i.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(i.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(i.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(i.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(i.shininess=this.shininess),this.clearcoat!==void 0&&(i.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(i.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(i.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(i.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(i.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,i.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(i.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(i.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(i.dispersion=this.dispersion),this.iridescence!==void 0&&(i.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(i.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(i.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(i.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(i.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(i.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(i.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(i.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(i.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(i.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(i.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(i.lightMap=this.lightMap.toJSON(e).uuid,i.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(i.aoMap=this.aoMap.toJSON(e).uuid,i.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(i.bumpMap=this.bumpMap.toJSON(e).uuid,i.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(i.normalMap=this.normalMap.toJSON(e).uuid,i.normalMapType=this.normalMapType,i.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(i.displacementMap=this.displacementMap.toJSON(e).uuid,i.displacementScale=this.displacementScale,i.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(i.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(i.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(i.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(i.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(i.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(i.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(i.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(i.combine=this.combine)),this.envMapRotation!==void 0&&(i.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(i.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(i.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(i.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(i.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(i.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(i.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(i.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(i.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(i.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(i.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(i.size=this.size),this.shadowSide!==null&&(i.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(i.sizeAttenuation=this.sizeAttenuation),this.blending!==Hr&&(i.blending=this.blending),this.side!==ji&&(i.side=this.side),this.vertexColors===!0&&(i.vertexColors=!0),this.opacity<1&&(i.opacity=this.opacity),this.transparent===!0&&(i.transparent=!0),this.blendSrc!==Eu&&(i.blendSrc=this.blendSrc),this.blendDst!==wu&&(i.blendDst=this.blendDst),this.blendEquation!==Br&&(i.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(i.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(i.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(i.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(i.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(i.blendAlpha=this.blendAlpha),this.depthFunc!==Bs&&(i.depthFunc=this.depthFunc),this.depthTest===!1&&(i.depthTest=this.depthTest),this.depthWrite===!1&&(i.depthWrite=this.depthWrite),this.colorWrite===!1&&(i.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(i.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==od&&(i.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(i.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(i.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==ls&&(i.stencilFail=this.stencilFail),this.stencilZFail!==ls&&(i.stencilZFail=this.stencilZFail),this.stencilZPass!==ls&&(i.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(i.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(i.rotation=this.rotation),this.polygonOffset===!0&&(i.polygonOffset=!0),this.polygonOffsetFactor!==0&&(i.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(i.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(i.linewidth=this.linewidth),this.dashSize!==void 0&&(i.dashSize=this.dashSize),this.gapSize!==void 0&&(i.gapSize=this.gapSize),this.scale!==void 0&&(i.scale=this.scale),this.dithering===!0&&(i.dithering=!0),this.alphaTest>0&&(i.alphaTest=this.alphaTest),this.alphaHash===!0&&(i.alphaHash=!0),this.alphaToCoverage===!0&&(i.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(i.premultipliedAlpha=!0),this.forceSinglePass===!0&&(i.forceSinglePass=!0),this.allowOverride===!1&&(i.allowOverride=!1),this.wireframe===!0&&(i.wireframe=!0),this.wireframeLinewidth>1&&(i.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(i.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(i.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(i.flatShading=!0),this.visible===!1&&(i.visible=!1),this.toneMapped===!1&&(i.toneMapped=!1),this.fog===!1&&(i.fog=!1),Object.keys(this.userData).length>0&&(i.userData=this.userData);function r(s){const a=[];for(const o in s){const l=s[o];delete l.metadata,a.push(l)}return a}if(t){const s=r(e.textures),a=r(e.images);s.length>0&&(i.textures=s),a.length>0&&(i.images=a)}return i}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const t=e.clippingPlanes;let i=null;if(t!==null){const r=t.length;i=new Array(r);for(let s=0;s!==r;++s)i[s]=t[s].clone()}return this.clippingPlanes=i,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}}class Aa extends $i{constructor(e){super(),this.isSpriteMaterial=!0,this.type="SpriteMaterial",this.color=new ut(16777215),this.map=null,this.alphaMap=null,this.rotation=0,this.sizeAttenuation=!0,this.transparent=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.rotation=e.rotation,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}let xs;const ga=new $,ys=new $,bs=new $,Ss=new Xe,_a=new Xe,Wm=new zt,go=new $,va=new $,_o=new $,bd=new Xe,Ac=new Xe,Sd=new Xe;class vo extends _n{constructor(e=new Aa){if(super(),this.isSprite=!0,this.type="Sprite",xs===void 0){xs=new Dt;const t=new Float32Array([-.5,-.5,0,0,0,.5,-.5,0,1,0,.5,.5,0,1,1,-.5,.5,0,0,1]),i=new bv(t,5);xs.setIndex([0,1,2,0,2,3]),xs.setAttribute("position",new ml(i,3,0,!1)),xs.setAttribute("uv",new ml(i,2,3,!1))}this.geometry=xs,this.material=e,this.center=new Xe(.5,.5),this.count=1}raycast(e,t){e.camera===null&&pt('Sprite: "Raycaster.camera" needs to be set in order to raycast against sprites.'),ys.setFromMatrixScale(this.matrixWorld),Wm.copy(e.camera.matrixWorld),this.modelViewMatrix.multiplyMatrices(e.camera.matrixWorldInverse,this.matrixWorld),bs.setFromMatrixPosition(this.modelViewMatrix),e.camera.isPerspectiveCamera&&this.material.sizeAttenuation===!1&&ys.multiplyScalar(-bs.z);const i=this.material.rotation;let r,s;i!==0&&(s=Math.cos(i),r=Math.sin(i));const a=this.center;xo(go.set(-.5,-.5,0),bs,a,ys,r,s),xo(va.set(.5,-.5,0),bs,a,ys,r,s),xo(_o.set(.5,.5,0),bs,a,ys,r,s),bd.set(0,0),Ac.set(1,0),Sd.set(1,1);let o=e.ray.intersectTriangle(go,va,_o,!1,ga);if(o===null&&(xo(va.set(-.5,.5,0),bs,a,ys,r,s),Ac.set(0,1),o=e.ray.intersectTriangle(go,_o,va,!1,ga),o===null))return;const l=e.ray.origin.distanceTo(ga);l<e.near||l>e.far||t.push({distance:l,point:ga.clone(),uv:Qn.getInterpolation(ga,go,va,_o,bd,Ac,Sd,new Xe),face:null,object:this})}copy(e,t){return super.copy(e,t),e.center!==void 0&&this.center.copy(e.center),this.material=e.material,this}}function xo(n,e,t,i,r,s){Ss.subVectors(n,t).addScalar(.5).multiply(i),r!==void 0?(_a.x=s*Ss.x-r*Ss.y,_a.y=r*Ss.x+s*Ss.y):_a.copy(Ss),n.copy(e),n.x+=_a.x,n.y+=_a.y,n.applyMatrix4(Wm)}const zi=new $,Rc=new $,yo=new $,ar=new $,Cc=new $,bo=new $,Pc=new $;class Ll{constructor(e=new $,t=new $(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,zi)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);const i=t.dot(this.direction);return i<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,i)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const t=zi.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(zi.copy(this.origin).addScaledVector(this.direction,t),zi.distanceToSquared(e))}distanceSqToSegment(e,t,i,r){Rc.copy(e).add(t).multiplyScalar(.5),yo.copy(t).sub(e).normalize(),ar.copy(this.origin).sub(Rc);const s=e.distanceTo(t)*.5,a=-this.direction.dot(yo),o=ar.dot(this.direction),l=-ar.dot(yo),c=ar.lengthSq(),u=Math.abs(1-a*a);let f,h,d,m;if(u>0)if(f=a*l-o,h=a*o-l,m=s*u,f>=0)if(h>=-m)if(h<=m){const g=1/u;f*=g,h*=g,d=f*(f+a*h+2*o)+h*(a*f+h+2*l)+c}else h=s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;else h=-s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;else h<=-m?(f=Math.max(0,-(-a*s+o)),h=f>0?-s:Math.min(Math.max(-s,-l),s),d=-f*f+h*(h+2*l)+c):h<=m?(f=0,h=Math.min(Math.max(-s,-l),s),d=h*(h+2*l)+c):(f=Math.max(0,-(a*s+o)),h=f>0?s:Math.min(Math.max(-s,-l),s),d=-f*f+h*(h+2*l)+c);else h=a>0?-s:s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;return i&&i.copy(this.origin).addScaledVector(this.direction,f),r&&r.copy(Rc).addScaledVector(yo,h),d}intersectSphere(e,t){zi.subVectors(e.center,this.origin);const i=zi.dot(this.direction),r=zi.dot(zi)-i*i,s=e.radius*e.radius;if(r>s)return null;const a=Math.sqrt(s-r),o=i-a,l=i+a;return l<0?null:o<0?this.at(l,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;const i=-(this.origin.dot(e.normal)+e.constant)/t;return i>=0?i:null}intersectPlane(e,t){const i=this.distanceToPlane(e);return i===null?null:this.at(i,t)}intersectsPlane(e){const t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let i,r,s,a,o,l;const c=1/this.direction.x,u=1/this.direction.y,f=1/this.direction.z,h=this.origin;return c>=0?(i=(e.min.x-h.x)*c,r=(e.max.x-h.x)*c):(i=(e.max.x-h.x)*c,r=(e.min.x-h.x)*c),u>=0?(s=(e.min.y-h.y)*u,a=(e.max.y-h.y)*u):(s=(e.max.y-h.y)*u,a=(e.min.y-h.y)*u),i>a||s>r||((s>i||isNaN(i))&&(i=s),(a<r||isNaN(r))&&(r=a),f>=0?(o=(e.min.z-h.z)*f,l=(e.max.z-h.z)*f):(o=(e.max.z-h.z)*f,l=(e.min.z-h.z)*f),i>l||o>r)||((o>i||i!==i)&&(i=o),(l<r||r!==r)&&(r=l),r<0)?null:this.at(i>=0?i:r,t)}intersectsBox(e){return this.intersectBox(e,zi)!==null}intersectTriangle(e,t,i,r,s){Cc.subVectors(t,e),bo.subVectors(i,e),Pc.crossVectors(Cc,bo);let a=this.direction.dot(Pc),o;if(a>0){if(r)return null;o=1}else if(a<0)o=-1,a=-a;else return null;ar.subVectors(this.origin,e);const l=o*this.direction.dot(bo.crossVectors(ar,bo));if(l<0)return null;const c=o*this.direction.dot(Cc.cross(ar));if(c<0||l+c>a)return null;const u=-o*ar.dot(Pc);return u<0?null:this.at(u/a,s)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class tf extends $i{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new ut(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Jr,this.combine=Sm,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const Md=new zt,Dr=new Ll,So=new Zs,Td=new $,Mo=new $,To=new $,Eo=new $,Dc=new $,wo=new $,Ed=new $,Ao=new $;class jn extends _n{constructor(e=new Dt,t=new tf){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const t=this.geometry.morphAttributes,i=Object.keys(t);if(i.length>0){const r=t[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){const o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}getVertexPosition(e,t){const i=this.geometry,r=i.attributes.position,s=i.morphAttributes.position,a=i.morphTargetsRelative;t.fromBufferAttribute(r,e);const o=this.morphTargetInfluences;if(s&&o){wo.set(0,0,0);for(let l=0,c=s.length;l<c;l++){const u=o[l],f=s[l];u!==0&&(Dc.fromBufferAttribute(f,e),a?wo.addScaledVector(Dc,u):wo.addScaledVector(Dc.sub(t),u))}t.add(wo)}return t}raycast(e,t){const i=this.geometry,r=this.material,s=this.matrixWorld;r!==void 0&&(i.boundingSphere===null&&i.computeBoundingSphere(),So.copy(i.boundingSphere),So.applyMatrix4(s),Dr.copy(e.ray).recast(e.near),!(So.containsPoint(Dr.origin)===!1&&(Dr.intersectSphere(So,Td)===null||Dr.origin.distanceToSquared(Td)>(e.far-e.near)**2))&&(Md.copy(s).invert(),Dr.copy(e.ray).applyMatrix4(Md),!(i.boundingBox!==null&&Dr.intersectsBox(i.boundingBox)===!1)&&this._computeIntersections(e,t,Dr)))}_computeIntersections(e,t,i){let r;const s=this.geometry,a=this.material,o=s.index,l=s.attributes.position,c=s.attributes.uv,u=s.attributes.uv1,f=s.attributes.normal,h=s.groups,d=s.drawRange;if(o!==null)if(Array.isArray(a))for(let m=0,g=h.length;m<g;m++){const p=h[m],_=a[p.materialIndex],v=Math.max(p.start,d.start),S=Math.min(o.count,Math.min(p.start+p.count,d.start+d.count));for(let y=v,M=S;y<M;y+=3){const T=o.getX(y),w=o.getX(y+1),b=o.getX(y+2);r=Ro(this,_,e,i,c,u,f,T,w,b),r&&(r.faceIndex=Math.floor(y/3),r.face.materialIndex=p.materialIndex,t.push(r))}}else{const m=Math.max(0,d.start),g=Math.min(o.count,d.start+d.count);for(let p=m,_=g;p<_;p+=3){const v=o.getX(p),S=o.getX(p+1),y=o.getX(p+2);r=Ro(this,a,e,i,c,u,f,v,S,y),r&&(r.faceIndex=Math.floor(p/3),t.push(r))}}else if(l!==void 0)if(Array.isArray(a))for(let m=0,g=h.length;m<g;m++){const p=h[m],_=a[p.materialIndex],v=Math.max(p.start,d.start),S=Math.min(l.count,Math.min(p.start+p.count,d.start+d.count));for(let y=v,M=S;y<M;y+=3){const T=y,w=y+1,b=y+2;r=Ro(this,_,e,i,c,u,f,T,w,b),r&&(r.faceIndex=Math.floor(y/3),r.face.materialIndex=p.materialIndex,t.push(r))}}else{const m=Math.max(0,d.start),g=Math.min(l.count,d.start+d.count);for(let p=m,_=g;p<_;p+=3){const v=p,S=p+1,y=p+2;r=Ro(this,a,e,i,c,u,f,v,S,y),r&&(r.faceIndex=Math.floor(p/3),t.push(r))}}}}function Mv(n,e,t,i,r,s,a,o){let l;if(e.side===an?l=i.intersectTriangle(a,s,r,!0,o):l=i.intersectTriangle(r,s,a,e.side===ji,o),l===null)return null;Ao.copy(o),Ao.applyMatrix4(n.matrixWorld);const c=t.ray.origin.distanceTo(Ao);return c<t.near||c>t.far?null:{distance:c,point:Ao.clone(),object:n}}function Ro(n,e,t,i,r,s,a,o,l,c){n.getVertexPosition(o,Mo),n.getVertexPosition(l,To),n.getVertexPosition(c,Eo);const u=Mv(n,e,t,i,Mo,To,Eo,Ed);if(u){const f=new $;Qn.getBarycoord(Ed,Mo,To,Eo,f),r&&(u.uv=Qn.getInterpolatedAttribute(r,o,l,c,f,new Xe)),s&&(u.uv1=Qn.getInterpolatedAttribute(s,o,l,c,f,new Xe)),a&&(u.normal=Qn.getInterpolatedAttribute(a,o,l,c,f,new $),u.normal.dot(i.direction)>0&&u.normal.multiplyScalar(-1));const h={a:o,b:l,c,normal:new $,materialIndex:0};Qn.getNormal(Mo,To,Eo,h.normal),u.face=h,u.barycoord=f}return u}class Tv extends $t{constructor(e=null,t=1,i=1,r,s,a,o,l,c=un,u=un,f,h){super(null,a,o,l,c,u,r,s,f,h),this.isDataTexture=!0,this.image={data:e,width:t,height:i},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class Ev extends Nt{constructor(e,t,i,r=1){super(e,t,i),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=r}copy(e){return super.copy(e),this.meshPerAttribute=e.meshPerAttribute,this}toJSON(){const e=super.toJSON();return e.meshPerAttribute=this.meshPerAttribute,e.isInstancedBufferAttribute=!0,e}}const Uc=new $,wv=new $,Av=new it;class ur{constructor(e=new $(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,i,r){return this.normal.set(e,t,i),this.constant=r,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,i){const r=Uc.subVectors(i,t).cross(wv.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(r,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t,i=!0){const r=e.delta(Uc),s=this.normal.dot(r);if(s===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;const a=-(e.start.dot(this.normal)+this.constant)/s;return i===!0&&(a<0||a>1)?null:t.copy(e.start).addScaledVector(r,a)}intersectsLine(e){const t=this.distanceToPoint(e.start),i=this.distanceToPoint(e.end);return t<0&&i>0||i<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){const i=t||Av.getNormalMatrix(e),r=this.coplanarPoint(Uc).applyMatrix4(e),s=this.normal.applyMatrix3(i).normalize();return this.constant=-r.dot(s),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}}const Ur=new Zs,Rv=new Xe(.5,.5),Co=new $;class Xm{constructor(e=new ur,t=new ur,i=new ur,r=new ur,s=new ur,a=new ur){this.planes=[e,t,i,r,s,a]}set(e,t,i,r,s,a){const o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(i),o[3].copy(r),o[4].copy(s),o[5].copy(a),this}copy(e){const t=this.planes;for(let i=0;i<6;i++)t[i].copy(e.planes[i]);return this}setFromProjectionMatrix(e,t=Ri,i=!1){const r=this.planes,s=e.elements,a=s[0],o=s[1],l=s[2],c=s[3],u=s[4],f=s[5],h=s[6],d=s[7],m=s[8],g=s[9],p=s[10],_=s[11],v=s[12],S=s[13],y=s[14],M=s[15];if(r[0].setComponents(c-a,d-u,_-m,M-v).normalize(),r[1].setComponents(c+a,d+u,_+m,M+v).normalize(),r[2].setComponents(c+o,d+f,_+g,M+S).normalize(),r[3].setComponents(c-o,d-f,_-g,M-S).normalize(),i)r[4].setComponents(l,h,p,y).normalize(),r[5].setComponents(c-l,d-h,_-p,M-y).normalize();else if(r[4].setComponents(c-l,d-h,_-p,M-y).normalize(),t===Ri)r[5].setComponents(c+l,d+h,_+p,M+y).normalize();else if(t===fl)r[5].setComponents(l,h,p,y).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Ur.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),Ur.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Ur)}intersectsSprite(e){Ur.center.set(0,0,0);const t=Rv.distanceTo(e.center);return Ur.radius=.7071067811865476+t,Ur.applyMatrix4(e.matrixWorld),this.intersectsSphere(Ur)}intersectsSphere(e){const t=this.planes,i=e.center,r=-e.radius;for(let s=0;s<6;s++)if(t[s].distanceToPoint(i)<r)return!1;return!0}intersectsBox(e){const t=this.planes;for(let i=0;i<6;i++){const r=t[i];if(Co.x=r.normal.x>0?e.max.x:e.min.x,Co.y=r.normal.y>0?e.max.y:e.min.y,Co.z=r.normal.z>0?e.max.z:e.min.z,r.distanceToPoint(Co)<0)return!1}return!0}containsPoint(e){const t=this.planes;for(let i=0;i<6;i++)if(t[i].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class mh extends $i{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new ut(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}}const gl=new $,_l=new $,wd=new zt,xa=new Ll,Po=new Zs,Lc=new $,Ad=new $;class nf extends _n{constructor(e=new Dt,t=new mh){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,i=[0];for(let r=1,s=t.count;r<s;r++)gl.fromBufferAttribute(t,r-1),_l.fromBufferAttribute(t,r),i[r]=i[r-1],i[r]+=gl.distanceTo(_l);e.setAttribute("lineDistance",new di(i,1))}else Je("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(e,t){const i=this.geometry,r=this.matrixWorld,s=e.params.Line.threshold,a=i.drawRange;if(i.boundingSphere===null&&i.computeBoundingSphere(),Po.copy(i.boundingSphere),Po.applyMatrix4(r),Po.radius+=s,e.ray.intersectsSphere(Po)===!1)return;wd.copy(r).invert(),xa.copy(e.ray).applyMatrix4(wd);const o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=this.isLineSegments?2:1,u=i.index,h=i.attributes.position;if(u!==null){const d=Math.max(0,a.start),m=Math.min(u.count,a.start+a.count);for(let g=d,p=m-1;g<p;g+=c){const _=u.getX(g),v=u.getX(g+1),S=Do(this,e,xa,l,_,v,g);S&&t.push(S)}if(this.isLineLoop){const g=u.getX(m-1),p=u.getX(d),_=Do(this,e,xa,l,g,p,m-1);_&&t.push(_)}}else{const d=Math.max(0,a.start),m=Math.min(h.count,a.start+a.count);for(let g=d,p=m-1;g<p;g+=c){const _=Do(this,e,xa,l,g,g+1,g);_&&t.push(_)}if(this.isLineLoop){const g=Do(this,e,xa,l,m-1,d,m-1);g&&t.push(g)}}}updateMorphTargets(){const t=this.geometry.morphAttributes,i=Object.keys(t);if(i.length>0){const r=t[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){const o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}}function Do(n,e,t,i,r,s,a){const o=n.geometry.attributes.position;if(gl.fromBufferAttribute(o,r),_l.fromBufferAttribute(o,s),t.distanceSqToSegment(gl,_l,Lc,Ad)>i)return;Lc.applyMatrix4(n.matrixWorld);const c=e.ray.origin.distanceTo(Lc);if(!(c<e.near||c>e.far))return{distance:c,point:Ad.clone().applyMatrix4(n.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:n}}const Rd=new $,Cd=new $;class or extends nf{constructor(e,t){super(e,t),this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,i=[];for(let r=0,s=t.count;r<s;r+=2)Rd.fromBufferAttribute(t,r),Cd.fromBufferAttribute(t,r+1),i[r]=r===0?0:i[r-1],i[r+1]=i[r]+Rd.distanceTo(Cd);e.setAttribute("lineDistance",new di(i,1))}else Je("LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}}class Pd extends nf{constructor(e,t){super(e,t),this.isLineLoop=!0,this.type="LineLoop"}}class Cv extends $i{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new ut(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}const Dd=new zt,gh=new Ll,Uo=new Zs,Lo=new $;class Pv extends _n{constructor(e=new Dt,t=new Cv){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}raycast(e,t){const i=this.geometry,r=this.matrixWorld,s=e.params.Points.threshold,a=i.drawRange;if(i.boundingSphere===null&&i.computeBoundingSphere(),Uo.copy(i.boundingSphere),Uo.applyMatrix4(r),Uo.radius+=s,e.ray.intersectsSphere(Uo)===!1)return;Dd.copy(r).invert(),gh.copy(e.ray).applyMatrix4(Dd);const o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=i.index,f=i.attributes.position;if(c!==null){const h=Math.max(0,a.start),d=Math.min(c.count,a.start+a.count);for(let m=h,g=d;m<g;m++){const p=c.getX(m);Lo.fromBufferAttribute(f,p),Ud(Lo,p,l,r,e,t,this)}}else{const h=Math.max(0,a.start),d=Math.min(f.count,a.start+a.count);for(let m=h,g=d;m<g;m++)Lo.fromBufferAttribute(f,m),Ud(Lo,m,l,r,e,t,this)}}updateMorphTargets(){const t=this.geometry.morphAttributes,i=Object.keys(t);if(i.length>0){const r=t[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){const o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}}function Ud(n,e,t,i,r,s,a){const o=gh.distanceSqToPoint(n);if(o<t){const l=new $;gh.closestPointToPoint(n,l),l.applyMatrix4(i);const c=r.ray.origin.distanceTo(l);if(c<r.near||c>r.far)return;s.push({distance:c,distanceToRay:Math.sqrt(o),point:l,index:e,face:null,faceIndex:null,barycoord:null,object:a})}}class jm extends $t{constructor(e=[],t=Zr,i,r,s,a,o,l,c,u){super(e,t,i,r,s,a,o,l,c,u),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class Dv extends $t{constructor(e,t,i,r,s,a,o,l,c){super(e,t,i,r,s,a,o,l,c),this.isCanvasTexture=!0,this.needsUpdate=!0}}class Xi extends $t{constructor(e,t,i=Ui,r,s,a,o=un,l=un,c,u=qi,f=1){if(u!==qi&&u!==fr)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");const h={width:e,height:t,depth:f};super(h,r,s,a,o,l,u,i,c),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new ef(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){const t=super.toJSON(e);return this.compareFunction!==null&&(t.compareFunction=this.compareFunction),t}}class Uv extends Xi{constructor(e,t=Ui,i=Zr,r,s,a=un,o=un,l,c=qi){const u={width:e,height:e,depth:1},f=[u,u,u,u,u,u];super(e,e,t,i,r,s,a,o,l,c),this.image=f,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}}class Ym extends $t{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class $a extends Dt{constructor(e=1,t=1,i=1,r=1,s=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:i,widthSegments:r,heightSegments:s,depthSegments:a};const o=this;r=Math.floor(r),s=Math.floor(s),a=Math.floor(a);const l=[],c=[],u=[],f=[];let h=0,d=0;m("z","y","x",-1,-1,i,t,e,a,s,0),m("z","y","x",1,-1,i,t,-e,a,s,1),m("x","z","y",1,1,e,i,t,r,a,2),m("x","z","y",1,-1,e,i,-t,r,a,3),m("x","y","z",1,-1,e,t,i,r,s,4),m("x","y","z",-1,-1,e,t,-i,r,s,5),this.setIndex(l),this.setAttribute("position",new di(c,3)),this.setAttribute("normal",new di(u,3)),this.setAttribute("uv",new di(f,2));function m(g,p,_,v,S,y,M,T,w,b,x){const A=y/w,P=M/b,R=y/2,L=M/2,I=T/2,N=w+1,O=b+1;let B=0,q=0;const F=new $;for(let k=0;k<O;k++){const U=k*P-L;for(let z=0;z<N;z++){const K=z*A-R;F[g]=K*v,F[p]=U*S,F[_]=I,c.push(F.x,F.y,F.z),F[g]=0,F[p]=0,F[_]=T>0?1:-1,u.push(F.x,F.y,F.z),f.push(z/w),f.push(1-k/b),B+=1}}for(let k=0;k<b;k++)for(let U=0;U<w;U++){const z=h+U+N*k,K=h+U+N*(k+1),Z=h+(U+1)+N*(k+1),X=h+(U+1)+N*k;l.push(z,K,X),l.push(K,Z,X),q+=6}o.addGroup(d,q,x),d+=q,h+=B}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new $a(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}class Qr extends Dt{constructor(e=1,t=1,i=1,r=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:i,heightSegments:r};const s=e/2,a=t/2,o=Math.floor(i),l=Math.floor(r),c=o+1,u=l+1,f=e/o,h=t/l,d=[],m=[],g=[],p=[];for(let _=0;_<u;_++){const v=_*h-a;for(let S=0;S<c;S++){const y=S*f-s;m.push(y,-v,0),g.push(0,0,1),p.push(S/o),p.push(1-_/l)}}for(let _=0;_<l;_++)for(let v=0;v<o;v++){const S=v+c*_,y=v+c*(_+1),M=v+1+c*(_+1),T=v+1+c*_;d.push(S,y,T),d.push(y,M,T)}this.setIndex(d),this.setAttribute("position",new di(m,3)),this.setAttribute("normal",new di(g,3)),this.setAttribute("uv",new di(p,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Qr(e.width,e.height,e.widthSegments,e.heightSegments)}}function Hs(n){const e={};for(const t in n){e[t]={};for(const i in n[t]){const r=n[t][i];if(Ld(r))r.isRenderTargetTexture?(Je("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][i]=null):e[t][i]=r.clone();else if(Array.isArray(r))if(Ld(r[0])){const s=[];for(let a=0,o=r.length;a<o;a++)s[a]=r[a].clone();e[t][i]=s}else e[t][i]=r.slice();else e[t][i]=r}}return e}function Sn(n){const e={};for(let t=0;t<n.length;t++){const i=Hs(n[t]);for(const r in i)e[r]=i[r]}return e}function Ld(n){return n&&(n.isColor||n.isMatrix3||n.isMatrix4||n.isVector2||n.isVector3||n.isVector4||n.isTexture||n.isQuaternion)}function Lv(n){const e=[];for(let t=0;t<n.length;t++)e.push(n[t].clone());return e}function qm(n){const e=n.getRenderTarget();return e===null?n.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:ft.workingColorSpace}const Km={clone:Hs,merge:Sn};var Iv=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Fv=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class on extends $i{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=Iv,this.fragmentShader=Fv,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Hs(e.uniforms),this.uniformsGroups=Lv(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){const t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(const r in this.uniforms){const a=this.uniforms[r].value;a&&a.isTexture?t.uniforms[r]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[r]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[r]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[r]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[r]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[r]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[r]={type:"m4",value:a.toArray()}:t.uniforms[r]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;const i={};for(const r in this.extensions)this.extensions[r]===!0&&(i[r]=!0);return Object.keys(i).length>0&&(t.extensions=i),t}}class Nv extends on{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}}class Zm extends $i{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=Za,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class $m extends $i{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}const Io=new $,Fo=new br,xi=new $;class Jm extends _n{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new zt,this.projectionMatrix=new zt,this.projectionMatrixInverse=new zt,this.coordinateSystem=Ri,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(Io,Fo,xi),xi.x===1&&xi.y===1&&xi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Io,Fo,xi.set(1,1,1)).invert()}updateWorldMatrix(e,t){super.updateWorldMatrix(e,t),this.matrixWorld.decompose(Io,Fo,xi),xi.x===1&&xi.y===1&&xi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Io,Fo,xi.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}}const lr=new $,Id=new Xe,Fd=new Xe;class Gn extends Jm{constructor(e=50,t=1,i=.1,r=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=i,this.far=r,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const t=.5*this.getFilmHeight()/e;this.fov=dh*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(Jo*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return dh*2*Math.atan(Math.tan(Jo*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,i){lr.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(lr.x,lr.y).multiplyScalar(-e/lr.z),lr.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),i.set(lr.x,lr.y).multiplyScalar(-e/lr.z)}getViewSize(e,t){return this.getViewBounds(e,Id,Fd),t.subVectors(Fd,Id)}setViewOffset(e,t,i,r,s,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=i,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let t=e*Math.tan(Jo*.5*this.fov)/this.zoom,i=2*t,r=this.aspect*i,s=-.5*r;const a=this.view;if(this.view!==null&&this.view.enabled){const l=a.fullWidth,c=a.fullHeight;s+=a.offsetX*r/l,t-=a.offsetY*i/c,r*=a.width/l,i*=a.height/c}const o=this.filmOffset;o!==0&&(s+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(s,s+r,t,t-i,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}}class rf extends Jm{constructor(e=-1,t=1,i=1,r=-1,s=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=i,this.bottom=r,this.near=s,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,i,r,s,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=i,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),i=(this.right+this.left)/2,r=(this.top+this.bottom)/2;let s=i-e,a=i+e,o=r+t,l=r-t;if(this.view!==null&&this.view.enabled){const c=(this.right-this.left)/this.view.fullWidth/this.zoom,u=(this.top-this.bottom)/this.view.fullHeight/this.zoom;s+=c*this.view.offsetX,a=s+c*this.view.width,o-=u*this.view.offsetY,l=o-u*this.view.height}this.projectionMatrix.makeOrthographic(s,a,o,l,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}}class Ov extends Dt{constructor(){super(),this.isInstancedBufferGeometry=!0,this.type="InstancedBufferGeometry",this.instanceCount=1/0}copy(e){return super.copy(e),this.instanceCount=e.instanceCount,this}toJSON(){const e=super.toJSON();return e.instanceCount=this.instanceCount,e.isInstancedBufferGeometry=!0,e}}const Ms=-90,Ts=1;class Bv extends _n{constructor(e,t,i){super(),this.type="CubeCamera",this.renderTarget=i,this.coordinateSystem=null,this.activeMipmapLevel=0;const r=new Gn(Ms,Ts,e,t);r.layers=this.layers,this.add(r);const s=new Gn(Ms,Ts,e,t);s.layers=this.layers,this.add(s);const a=new Gn(Ms,Ts,e,t);a.layers=this.layers,this.add(a);const o=new Gn(Ms,Ts,e,t);o.layers=this.layers,this.add(o);const l=new Gn(Ms,Ts,e,t);l.layers=this.layers,this.add(l);const c=new Gn(Ms,Ts,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){const e=this.coordinateSystem,t=this.children.concat(),[i,r,s,a,o,l]=t;for(const c of t)this.remove(c);if(e===Ri)i.up.set(0,1,0),i.lookAt(1,0,0),r.up.set(0,1,0),r.lookAt(-1,0,0),s.up.set(0,0,-1),s.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===fl)i.up.set(0,-1,0),i.lookAt(-1,0,0),r.up.set(0,-1,0),r.lookAt(1,0,0),s.up.set(0,0,1),s.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const c of t)this.add(c),c.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();const{renderTarget:i,activeMipmapLevel:r}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[s,a,o,l,c,u]=this.children,f=e.getRenderTarget(),h=e.getActiveCubeFace(),d=e.getActiveMipmapLevel(),m=e.xr.enabled;e.xr.enabled=!1;const g=i.texture.generateMipmaps;i.texture.generateMipmaps=!1;let p=!1;e.isWebGLRenderer===!0?p=e.state.buffers.depth.getReversed():p=e.reversedDepthBuffer,e.setRenderTarget(i,0,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,s),e.setRenderTarget(i,1,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,a),e.setRenderTarget(i,2,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,o),e.setRenderTarget(i,3,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,l),e.setRenderTarget(i,4,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,c),i.texture.generateMipmaps=g,e.setRenderTarget(i,5,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,u),e.setRenderTarget(f,h,d),e.xr.enabled=m,i.texture.needsPMREMUpdate=!0}}class kv extends Gn{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}class vt{constructor(e){this.value=e}clone(){return new vt(this.value.clone===void 0?this.value:this.value.clone())}}class zv{constructor(e=!0){this.autoStart=e,this.startTime=0,this.oldTime=0,this.elapsedTime=0,this.running=!1,Je("Clock: This module has been deprecated. Please use THREE.Timer instead.")}start(){this.startTime=performance.now(),this.oldTime=this.startTime,this.elapsedTime=0,this.running=!0}stop(){this.getElapsedTime(),this.running=!1,this.autoStart=!1}getElapsedTime(){return this.getDelta(),this.elapsedTime}getDelta(){let e=0;if(this.autoStart&&!this.running)return this.start(),0;if(this.running){const t=performance.now();e=(t-this.oldTime)/1e3,this.oldTime=t,this.elapsedTime+=e}return e}}class Nd{constructor(e=1,t=0,i=0){this.radius=e,this.phi=t,this.theta=i}set(e,t,i){return this.radius=e,this.phi=t,this.theta=i,this}copy(e){return this.radius=e.radius,this.phi=e.phi,this.theta=e.theta,this}makeSafe(){return this.phi=lt(this.phi,1e-6,Math.PI-1e-6),this}setFromVector3(e){return this.setFromCartesianCoords(e.x,e.y,e.z)}setFromCartesianCoords(e,t,i){return this.radius=Math.sqrt(e*e+t*t+i*i),this.radius===0?(this.theta=0,this.phi=0):(this.theta=Math.atan2(e,i),this.phi=Math.acos(lt(t/this.radius,-1,1))),this}clone(){return new this.constructor().copy(this)}}const zf=class zf{constructor(e,t,i,r){this.elements=[1,0,0,1],e!==void 0&&this.set(e,t,i,r)}identity(){return this.set(1,0,0,1),this}fromArray(e,t=0){for(let i=0;i<4;i++)this.elements[i]=e[i+t];return this}set(e,t,i,r){const s=this.elements;return s[0]=e,s[2]=t,s[1]=i,s[3]=r,this}};zf.prototype.isMatrix2=!0;let Od=zf;class Gv extends pi{constructor(e,t=null){super(),this.object=e,this.domElement=t,this.enabled=!0,this.state=-1,this.keys={},this.mouseButtons={LEFT:null,MIDDLE:null,RIGHT:null},this.touches={ONE:null,TWO:null}}connect(e){if(e===void 0){Je("Controls: connect() now requires an element.");return}this.domElement!==null&&this.disconnect(),this.domElement=e}disconnect(){}dispose(){}update(){}}function Bd(n,e,t,i){const r=Hv(i);switch(t){case Fm:return n*e;case Om:return n*e/r.components*r.byteLength;case Kh:return n*e/r.components*r.byteLength;case $r:return n*e*2/r.components*r.byteLength;case Zh:return n*e*2/r.components*r.byteLength;case Nm:return n*e*3/r.components*r.byteLength;case fi:return n*e*4/r.components*r.byteLength;case $h:return n*e*4/r.components*r.byteLength;case qo:case Ko:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*8;case Zo:case $o:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case Nu:case Bu:return Math.max(n,16)*Math.max(e,8)/4;case Fu:case Ou:return Math.max(n,8)*Math.max(e,8)/2;case ku:case zu:case Hu:case Vu:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*8;case Gu:case cl:case Wu:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case Xu:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case ju:return Math.floor((n+4)/5)*Math.floor((e+3)/4)*16;case Yu:return Math.floor((n+4)/5)*Math.floor((e+4)/5)*16;case qu:return Math.floor((n+5)/6)*Math.floor((e+4)/5)*16;case Ku:return Math.floor((n+5)/6)*Math.floor((e+5)/6)*16;case Zu:return Math.floor((n+7)/8)*Math.floor((e+4)/5)*16;case $u:return Math.floor((n+7)/8)*Math.floor((e+5)/6)*16;case Ju:return Math.floor((n+7)/8)*Math.floor((e+7)/8)*16;case Qu:return Math.floor((n+9)/10)*Math.floor((e+4)/5)*16;case eh:return Math.floor((n+9)/10)*Math.floor((e+5)/6)*16;case th:return Math.floor((n+9)/10)*Math.floor((e+7)/8)*16;case nh:return Math.floor((n+9)/10)*Math.floor((e+9)/10)*16;case ih:return Math.floor((n+11)/12)*Math.floor((e+9)/10)*16;case rh:return Math.floor((n+11)/12)*Math.floor((e+11)/12)*16;case sh:case ah:case oh:return Math.ceil(n/4)*Math.ceil(e/4)*16;case lh:case ch:return Math.ceil(n/4)*Math.ceil(e/4)*8;case ul:case uh:return Math.ceil(n/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function Hv(n){switch(n){case Yt:case Dm:return{byteLength:1,components:1};case ka:case Um:case Yi:return{byteLength:2,components:1};case Yh:case qh:return{byteLength:2,components:4};case Ui:case jh:case hi:return{byteLength:4,components:1};case Lm:case Im:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${n}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:Ka}}));typeof window<"u"&&(window.__THREE__?Je("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=Ka);/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */function Qm(){let n=null,e=!1,t=null,i=null;function r(s,a){t(s,a),i=n.requestAnimationFrame(r)}return{start:function(){e!==!0&&t!==null&&n!==null&&(i=n.requestAnimationFrame(r),e=!0)},stop:function(){n!==null&&n.cancelAnimationFrame(i),e=!1},setAnimationLoop:function(s){t=s},setContext:function(s){n=s}}}function Vv(n){const e=new WeakMap;function t(o,l){const c=o.array,u=o.usage,f=c.byteLength,h=n.createBuffer();n.bindBuffer(l,h),n.bufferData(l,c,u),o.onUploadCallback();let d;if(c instanceof Float32Array)d=n.FLOAT;else if(typeof Float16Array<"u"&&c instanceof Float16Array)d=n.HALF_FLOAT;else if(c instanceof Uint16Array)o.isFloat16BufferAttribute?d=n.HALF_FLOAT:d=n.UNSIGNED_SHORT;else if(c instanceof Int16Array)d=n.SHORT;else if(c instanceof Uint32Array)d=n.UNSIGNED_INT;else if(c instanceof Int32Array)d=n.INT;else if(c instanceof Int8Array)d=n.BYTE;else if(c instanceof Uint8Array)d=n.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)d=n.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:h,type:d,bytesPerElement:c.BYTES_PER_ELEMENT,version:o.version,size:f}}function i(o,l,c){const u=l.array,f=l.updateRanges;if(n.bindBuffer(c,o),f.length===0)n.bufferSubData(c,0,u);else{f.sort((d,m)=>d.start-m.start);let h=0;for(let d=1;d<f.length;d++){const m=f[h],g=f[d];g.start<=m.start+m.count+1?m.count=Math.max(m.count,g.start+g.count-m.start):(++h,f[h]=g)}f.length=h+1;for(let d=0,m=f.length;d<m;d++){const g=f[d];n.bufferSubData(c,g.start*u.BYTES_PER_ELEMENT,u,g.start,g.count)}l.clearUpdateRanges()}l.onUploadCallback()}function r(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function s(o){o.isInterleavedBufferAttribute&&(o=o.data);const l=e.get(o);l&&(n.deleteBuffer(l.buffer),e.delete(o))}function a(o,l){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){const u=e.get(o);(!u||u.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}const c=e.get(o);if(c===void 0)e.set(o,t(o,l));else if(c.version<o.version){if(c.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");i(c.buffer,o,l),c.version=o.version}}return{get:r,remove:s,update:a}}var Wv=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,Xv=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,jv=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,Yv=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,qv=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,Kv=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,Zv=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,$v=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,Jv=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec4 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 );
	}
#endif`,Qv=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,ex=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,tx=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,nx=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,ix=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,rx=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,sx=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,ax=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,ox=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,lx=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,cx=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,ux=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,hx=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,fx=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec4( 1.0 );
#endif
#ifdef USE_COLOR_ALPHA
	vColor *= color;
#elif defined( USE_COLOR )
	vColor.rgb *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.rgb *= instanceColor.rgb;
#endif
#ifdef USE_BATCHING_COLOR
	vColor *= getBatchingColor( getIndirectIndex( gl_DrawID ) );
#endif`,dx=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
vec3 inverseTransformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( vec4( dir, 0.0 ) * matrix ).xyz );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,px=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,mx=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
	#ifdef FLIP_SIDED
		transformedTangent = - transformedTangent;
	#endif
#endif`,gx=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,_x=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,vx=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,xx=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,yx="gl_FragColor = linearToOutputTexel( gl_FragColor );",bx=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,Sx=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * reflectVec );
		#ifdef ENVMAP_BLENDING_MULTIPLY
			outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_MIX )
			outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_ADD )
			outgoingLight += envColor.xyz * specularStrength * reflectivity;
		#endif
	#endif
#endif`,Mx=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,Tx=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,Ex=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,wx=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,Ax=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,Rx=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,Cx=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,Px=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,Dx=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,Ux=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,Lx=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,Ix=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,Fx=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif
#include <lightprobes_pars_fragment>`,Nx=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, pow4( roughness ) ) );
			reflectVec = inverseTransformDirection( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
#endif`,Ox=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,Bx=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,kx=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,zx=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,Gx=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.diffuseContribution = diffuseColor.rgb * ( 1.0 - metalnessFactor );
material.metalness = metalnessFactor;
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor;
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = vec3( 0.04 );
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.0001, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,Hx=`uniform sampler2D dfgLUT;
struct PhysicalMaterial {
	vec3 diffuseColor;
	vec3 diffuseContribution;
	vec3 specularColor;
	vec3 specularColorBlended;
	float roughness;
	float metalness;
	float specularF90;
	float dispersion;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
		vec3 iridescenceFresnelDielectric;
		vec3 iridescenceFresnelMetallic;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		return 0.5 / max( gv + gl, EPSILON );
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColorBlended;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transpose( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float rInv = 1.0 / ( roughness + 0.1 );
	float a = -1.9362 + 1.0678 * roughness + 0.4573 * r2 - 0.8469 * rInv;
	float b = -0.6014 + 0.5538 * roughness - 0.4670 * r2 - 0.1255 * rInv;
	float DG = exp( a * dotNV + b );
	return saturate( DG );
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
vec3 BRDF_GGX_Multiscatter( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 singleScatter = BRDF_GGX( lightDir, viewDir, normal, material );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 dfgV = texture2D( dfgLUT, vec2( material.roughness, dotNV ) ).rg;
	vec2 dfgL = texture2D( dfgLUT, vec2( material.roughness, dotNL ) ).rg;
	vec3 FssEss_V = material.specularColorBlended * dfgV.x + material.specularF90 * dfgV.y;
	vec3 FssEss_L = material.specularColorBlended * dfgL.x + material.specularF90 * dfgL.y;
	float Ess_V = dfgV.x + dfgV.y;
	float Ess_L = dfgL.x + dfgL.y;
	float Ems_V = 1.0 - Ess_V;
	float Ems_L = 1.0 - Ess_L;
	vec3 Favg = material.specularColorBlended + ( 1.0 - material.specularColorBlended ) * 0.047619;
	vec3 Fms = FssEss_V * FssEss_L * Favg / ( 1.0 - Ems_V * Ems_L * Favg + EPSILON );
	float compensationFactor = Ems_V * Ems_L;
	vec3 multiScatter = Fms * compensationFactor;
	return singleScatter + multiScatter;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColorBlended * t2.x + ( material.specularF90 - material.specularColorBlended ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseContribution * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
		#ifdef USE_CLEARCOAT
			vec3 Ncc = geometryClearcoatNormal;
			vec2 uvClearcoat = LTC_Uv( Ncc, viewDir, material.clearcoatRoughness );
			vec4 t1Clearcoat = texture2D( ltc_1, uvClearcoat );
			vec4 t2Clearcoat = texture2D( ltc_2, uvClearcoat );
			mat3 mInvClearcoat = mat3(
				vec3( t1Clearcoat.x, 0, t1Clearcoat.y ),
				vec3(             0, 1,             0 ),
				vec3( t1Clearcoat.z, 0, t1Clearcoat.w )
			);
			vec3 fresnelClearcoat = material.clearcoatF0 * t2Clearcoat.x + ( material.clearcoatF90 - material.clearcoatF0 ) * t2Clearcoat.y;
			clearcoatSpecularDirect += lightColor * fresnelClearcoat * LTC_Evaluate( Ncc, viewDir, position, mInvClearcoat, rectCoords );
		#endif
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
 
 		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
 
 		float sheenAlbedoV = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
 		float sheenAlbedoL = IBLSheenBRDF( geometryNormal, directLight.direction, material.sheenRoughness );
 
 		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * max( sheenAlbedoV, sheenAlbedoL );
 
 		irradiance *= sheenEnergyComp;
 
 	#endif
	reflectedLight.directSpecular += irradiance * BRDF_GGX_Multiscatter( directLight.direction, geometryViewDir, geometryNormal, material );
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 diffuse = irradiance * BRDF_Lambert( material.diffuseContribution );
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		diffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectDiffuse += diffuse;
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness ) * RECIPROCAL_PI;
 	#endif
	vec3 singleScatteringDielectric = vec3( 0.0 );
	vec3 multiScatteringDielectric = vec3( 0.0 );
	vec3 singleScatteringMetallic = vec3( 0.0 );
	vec3 multiScatteringMetallic = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnelDielectric, material.roughness, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.diffuseColor, material.specularF90, material.iridescence, material.iridescenceFresnelMetallic, material.roughness, singleScatteringMetallic, multiScatteringMetallic );
	#else
		computeMultiscattering( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.roughness, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscattering( geometryNormal, geometryViewDir, material.diffuseColor, material.specularF90, material.roughness, singleScatteringMetallic, multiScatteringMetallic );
	#endif
	vec3 singleScattering = mix( singleScatteringDielectric, singleScatteringMetallic, material.metalness );
	vec3 multiScattering = mix( multiScatteringDielectric, multiScatteringMetallic, material.metalness );
	vec3 totalScatteringDielectric = singleScatteringDielectric + multiScatteringDielectric;
	vec3 diffuse = material.diffuseContribution * ( 1.0 - totalScatteringDielectric );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	vec3 indirectSpecular = radiance * singleScattering;
	indirectSpecular += multiScattering * cosineWeightedIrradiance;
	vec3 indirectDiffuse = diffuse * cosineWeightedIrradiance;
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		indirectSpecular *= sheenEnergyComp;
		indirectDiffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectSpecular += indirectSpecular;
	reflectedLight.indirectDiffuse += indirectDiffuse;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,Vx=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnelDielectric = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceFresnelMetallic = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.diffuseColor );
		material.iridescenceFresnel = mix( material.iridescenceFresnelDielectric, material.iridescenceFresnelMetallic, material.metalness );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS ) && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
	#ifdef USE_LIGHT_PROBES_GRID
		vec3 probeWorldPos = ( ( vec4( geometryPosition, 1.0 ) - viewMatrix[ 3 ] ) * viewMatrix ).xyz;
		vec3 probeWorldNormal = inverseTransformDirection( geometryNormal, viewMatrix );
		irradiance += getLightProbeGridIrradiance( probeWorldPos, probeWorldNormal );
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,Wx=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( ENVMAP_TYPE_CUBE_UV )
		#if defined( STANDARD ) || defined( LAMBERT ) || defined( PHONG )
			iblIrradiance += getIBLIrradiance( geometryNormal );
		#endif
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		radiance += getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,Xx=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,jx=`#ifdef USE_LIGHT_PROBES_GRID
uniform highp sampler3D probesSH;
uniform vec3 probesMin;
uniform vec3 probesMax;
uniform vec3 probesResolution;
vec3 getLightProbeGridIrradiance( vec3 worldPos, vec3 worldNormal ) {
	vec3 res = probesResolution;
	vec3 gridRange = probesMax - probesMin;
	vec3 resMinusOne = res - 1.0;
	vec3 probeSpacing = gridRange / resMinusOne;
	vec3 samplePos = worldPos + worldNormal * probeSpacing * 0.5;
	vec3 uvw = clamp( ( samplePos - probesMin ) / gridRange, 0.0, 1.0 );
	uvw = uvw * resMinusOne / res + 0.5 / res;
	float nz          = res.z;
	float paddedSlices = nz + 2.0;
	float atlasDepth  = 7.0 * paddedSlices;
	float uvZBase     = uvw.z * nz + 1.0;
	vec4 s0 = texture( probesSH, vec3( uvw.xy, ( uvZBase                       ) / atlasDepth ) );
	vec4 s1 = texture( probesSH, vec3( uvw.xy, ( uvZBase +       paddedSlices   ) / atlasDepth ) );
	vec4 s2 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 2.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s3 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 3.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s4 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 4.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s5 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 5.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s6 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 6.0 * paddedSlices   ) / atlasDepth ) );
	vec3 c0 = s0.xyz;
	vec3 c1 = vec3( s0.w, s1.xy );
	vec3 c2 = vec3( s1.zw, s2.x );
	vec3 c3 = s2.yzw;
	vec3 c4 = s3.xyz;
	vec3 c5 = vec3( s3.w, s4.xy );
	vec3 c6 = vec3( s4.zw, s5.x );
	vec3 c7 = s5.yzw;
	vec3 c8 = s6.xyz;
	float x = worldNormal.x, y = worldNormal.y, z = worldNormal.z;
	vec3 result = c0 * 0.886227;
	result += c1 * 2.0 * 0.511664 * y;
	result += c2 * 2.0 * 0.511664 * z;
	result += c3 * 2.0 * 0.511664 * x;
	result += c4 * 2.0 * 0.429043 * x * y;
	result += c5 * 2.0 * 0.429043 * y * z;
	result += c6 * ( 0.743125 * z * z - 0.247708 );
	result += c7 * 2.0 * 0.429043 * x * z;
	result += c8 * 0.429043 * ( x * x - y * y );
	return max( result, vec3( 0.0 ) );
}
#endif`,Yx=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,qx=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Kx=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Zx=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,$x=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,Jx=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,Qx=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,e1=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,t1=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,n1=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,i1=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,r1=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,s1=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,a1=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,o1=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,l1=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,c1=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#if defined( USE_PACKED_NORMALMAP )
		mapN = vec3( mapN.xy, sqrt( saturate( 1.0 - dot( mapN.xy, mapN.xy ) ) ) );
	#endif
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,u1=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,h1=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,f1=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,d1=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,p1=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,m1=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,g1=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,_1=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,v1=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,x1=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	#ifdef USE_REVERSED_DEPTH_BUFFER
	
		return depth * ( far - near ) - far;
	#else
		return depth * ( near - far ) - near;
	#endif
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	
	#ifdef USE_REVERSED_DEPTH_BUFFER
		return ( near * far ) / ( ( near - far ) * depth - near );
	#else
		return ( near * far ) / ( ( far - near ) * depth - far );
	#endif
}`,y1=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,b1=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,S1=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,M1=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,T1=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,E1=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,w1=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#else
			uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#endif
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#else
			uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#endif
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform samplerCubeShadow pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#elif defined( SHADOWMAP_TYPE_BASIC )
			uniform samplerCube pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#endif
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float interleavedGradientNoise( vec2 position ) {
			return fract( 52.9829189 * fract( dot( position, vec2( 0.06711056, 0.00583715 ) ) ) );
		}
		vec2 vogelDiskSample( int sampleIndex, int samplesCount, float phi ) {
			const float goldenAngle = 2.399963229728653;
			float r = sqrt( ( float( sampleIndex ) + 0.5 ) / float( samplesCount ) );
			float theta = float( sampleIndex ) * goldenAngle + phi;
			return vec2( cos( theta ), sin( theta ) ) * r;
		}
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float getShadow( sampler2DShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
				float radius = shadowRadius * texelSize.x;
				float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
				shadow = (
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 0, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 1, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 2, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 3, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 4, 5, phi ) * radius, shadowCoord.z ) )
				) * 0.2;
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#elif defined( SHADOWMAP_TYPE_VSM )
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 distribution = texture2D( shadowMap, shadowCoord.xy ).rg;
				float mean = distribution.x;
				float variance = distribution.y * distribution.y;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					float hard_shadow = step( mean, shadowCoord.z );
				#else
					float hard_shadow = step( shadowCoord.z, mean );
				#endif
				
				if ( hard_shadow == 1.0 ) {
					shadow = 1.0;
				} else {
					variance = max( variance, 0.0000001 );
					float d = shadowCoord.z - mean;
					float p_max = variance / ( variance + d * d );
					p_max = clamp( ( p_max - 0.3 ) / 0.65, 0.0, 1.0 );
					shadow = max( hard_shadow, p_max );
				}
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#else
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				float depth = texture2D( shadowMap, shadowCoord.xy ).r;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					shadow = step( depth, shadowCoord.z );
				#else
					shadow = step( shadowCoord.z, depth );
				#endif
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#if defined( SHADOWMAP_TYPE_PCF )
	float getPointShadow( samplerCubeShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			#ifdef USE_REVERSED_DEPTH_BUFFER
				float dp = ( shadowCameraNear * ( shadowCameraFar - viewSpaceZ ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp -= shadowBias;
			#else
				float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp += shadowBias;
			#endif
			float texelSize = shadowRadius / shadowMapSize.x;
			vec3 absDir = abs( bd3D );
			vec3 tangent = absDir.x > absDir.z ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 );
			tangent = normalize( cross( bd3D, tangent ) );
			vec3 bitangent = cross( bd3D, tangent );
			float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
			vec2 sample0 = vogelDiskSample( 0, 5, phi );
			vec2 sample1 = vogelDiskSample( 1, 5, phi );
			vec2 sample2 = vogelDiskSample( 2, 5, phi );
			vec2 sample3 = vogelDiskSample( 3, 5, phi );
			vec2 sample4 = vogelDiskSample( 4, 5, phi );
			shadow = (
				texture( shadowMap, vec4( bd3D + ( tangent * sample0.x + bitangent * sample0.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample1.x + bitangent * sample1.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample2.x + bitangent * sample2.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample3.x + bitangent * sample3.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample4.x + bitangent * sample4.y ) * texelSize, dp ) )
			) * 0.2;
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#elif defined( SHADOWMAP_TYPE_BASIC )
	float getPointShadow( samplerCube shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			float depth = textureCube( shadowMap, bd3D ).r;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				depth = 1.0 - depth;
			#endif
			shadow = step( dp, depth );
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#endif
	#endif
#endif`,A1=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,R1=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	#ifdef HAS_NORMAL
		vec3 shadowWorldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
	#else
		vec3 shadowWorldNormal = vec3( 0.0 );
	#endif
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,C1=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0 && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,P1=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,D1=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,U1=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,L1=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,I1=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,F1=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,N1=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,O1=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,B1=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = inverseTransformDirection( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseContribution, material.specularColorBlended, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,k1=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,z1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,G1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,H1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,V1=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;const W1=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,X1=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,j1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,Y1=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vWorldDirection );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,q1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,K1=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Z1=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,$1=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,J1=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,Q1=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main () {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = vec4( dist, 0.0, 0.0, 1.0 );
}`,ey=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,ty=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,ny=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,iy=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,ry=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,sy=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,ay=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,oy=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,ly=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,cy=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,uy=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,hy=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( normalize( normal ) * 0.5 + 0.5, diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,fy=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,dy=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,py=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,my=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
 
		outgoingLight = outgoingLight + sheenSpecularDirect + sheenSpecularIndirect;
 
 	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,gy=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,_y=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,vy=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,xy=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,yy=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,by=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Sy=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,My=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,rt={alphahash_fragment:Wv,alphahash_pars_fragment:Xv,alphamap_fragment:jv,alphamap_pars_fragment:Yv,alphatest_fragment:qv,alphatest_pars_fragment:Kv,aomap_fragment:Zv,aomap_pars_fragment:$v,batching_pars_vertex:Jv,batching_vertex:Qv,begin_vertex:ex,beginnormal_vertex:tx,bsdfs:nx,iridescence_fragment:ix,bumpmap_pars_fragment:rx,clipping_planes_fragment:sx,clipping_planes_pars_fragment:ax,clipping_planes_pars_vertex:ox,clipping_planes_vertex:lx,color_fragment:cx,color_pars_fragment:ux,color_pars_vertex:hx,color_vertex:fx,common:dx,cube_uv_reflection_fragment:px,defaultnormal_vertex:mx,displacementmap_pars_vertex:gx,displacementmap_vertex:_x,emissivemap_fragment:vx,emissivemap_pars_fragment:xx,colorspace_fragment:yx,colorspace_pars_fragment:bx,envmap_fragment:Sx,envmap_common_pars_fragment:Mx,envmap_pars_fragment:Tx,envmap_pars_vertex:Ex,envmap_physical_pars_fragment:Nx,envmap_vertex:wx,fog_vertex:Ax,fog_pars_vertex:Rx,fog_fragment:Cx,fog_pars_fragment:Px,gradientmap_pars_fragment:Dx,lightmap_pars_fragment:Ux,lights_lambert_fragment:Lx,lights_lambert_pars_fragment:Ix,lights_pars_begin:Fx,lights_toon_fragment:Ox,lights_toon_pars_fragment:Bx,lights_phong_fragment:kx,lights_phong_pars_fragment:zx,lights_physical_fragment:Gx,lights_physical_pars_fragment:Hx,lights_fragment_begin:Vx,lights_fragment_maps:Wx,lights_fragment_end:Xx,lightprobes_pars_fragment:jx,logdepthbuf_fragment:Yx,logdepthbuf_pars_fragment:qx,logdepthbuf_pars_vertex:Kx,logdepthbuf_vertex:Zx,map_fragment:$x,map_pars_fragment:Jx,map_particle_fragment:Qx,map_particle_pars_fragment:e1,metalnessmap_fragment:t1,metalnessmap_pars_fragment:n1,morphinstance_vertex:i1,morphcolor_vertex:r1,morphnormal_vertex:s1,morphtarget_pars_vertex:a1,morphtarget_vertex:o1,normal_fragment_begin:l1,normal_fragment_maps:c1,normal_pars_fragment:u1,normal_pars_vertex:h1,normal_vertex:f1,normalmap_pars_fragment:d1,clearcoat_normal_fragment_begin:p1,clearcoat_normal_fragment_maps:m1,clearcoat_pars_fragment:g1,iridescence_pars_fragment:_1,opaque_fragment:v1,packing:x1,premultiplied_alpha_fragment:y1,project_vertex:b1,dithering_fragment:S1,dithering_pars_fragment:M1,roughnessmap_fragment:T1,roughnessmap_pars_fragment:E1,shadowmap_pars_fragment:w1,shadowmap_pars_vertex:A1,shadowmap_vertex:R1,shadowmask_pars_fragment:C1,skinbase_vertex:P1,skinning_pars_vertex:D1,skinning_vertex:U1,skinnormal_vertex:L1,specularmap_fragment:I1,specularmap_pars_fragment:F1,tonemapping_fragment:N1,tonemapping_pars_fragment:O1,transmission_fragment:B1,transmission_pars_fragment:k1,uv_pars_fragment:z1,uv_pars_vertex:G1,uv_vertex:H1,worldpos_vertex:V1,background_vert:W1,background_frag:X1,backgroundCube_vert:j1,backgroundCube_frag:Y1,cube_vert:q1,cube_frag:K1,depth_vert:Z1,depth_frag:$1,distance_vert:J1,distance_frag:Q1,equirect_vert:ey,equirect_frag:ty,linedashed_vert:ny,linedashed_frag:iy,meshbasic_vert:ry,meshbasic_frag:sy,meshlambert_vert:ay,meshlambert_frag:oy,meshmatcap_vert:ly,meshmatcap_frag:cy,meshnormal_vert:uy,meshnormal_frag:hy,meshphong_vert:fy,meshphong_frag:dy,meshphysical_vert:py,meshphysical_frag:my,meshtoon_vert:gy,meshtoon_frag:_y,points_vert:vy,points_frag:xy,shadow_vert:yy,shadow_frag:by,sprite_vert:Sy,sprite_frag:My},Ge={common:{diffuse:{value:new ut(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new it},alphaMap:{value:null},alphaMapTransform:{value:new it},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new it}},envmap:{envMap:{value:null},envMapRotation:{value:new it},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new it}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new it}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new it},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new it},normalScale:{value:new Xe(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new it},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new it}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new it}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new it}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new ut(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new $},probesMax:{value:new $},probesResolution:{value:new $}},points:{diffuse:{value:new ut(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new it},alphaTest:{value:0},uvTransform:{value:new it}},sprite:{diffuse:{value:new ut(16777215)},opacity:{value:1},center:{value:new Xe(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new it},alphaMap:{value:null},alphaMapTransform:{value:new it},alphaTest:{value:0}}},Mi={basic:{uniforms:Sn([Ge.common,Ge.specularmap,Ge.envmap,Ge.aomap,Ge.lightmap,Ge.fog]),vertexShader:rt.meshbasic_vert,fragmentShader:rt.meshbasic_frag},lambert:{uniforms:Sn([Ge.common,Ge.specularmap,Ge.envmap,Ge.aomap,Ge.lightmap,Ge.emissivemap,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.fog,Ge.lights,{emissive:{value:new ut(0)},envMapIntensity:{value:1}}]),vertexShader:rt.meshlambert_vert,fragmentShader:rt.meshlambert_frag},phong:{uniforms:Sn([Ge.common,Ge.specularmap,Ge.envmap,Ge.aomap,Ge.lightmap,Ge.emissivemap,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.fog,Ge.lights,{emissive:{value:new ut(0)},specular:{value:new ut(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:rt.meshphong_vert,fragmentShader:rt.meshphong_frag},standard:{uniforms:Sn([Ge.common,Ge.envmap,Ge.aomap,Ge.lightmap,Ge.emissivemap,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.roughnessmap,Ge.metalnessmap,Ge.fog,Ge.lights,{emissive:{value:new ut(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:rt.meshphysical_vert,fragmentShader:rt.meshphysical_frag},toon:{uniforms:Sn([Ge.common,Ge.aomap,Ge.lightmap,Ge.emissivemap,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.gradientmap,Ge.fog,Ge.lights,{emissive:{value:new ut(0)}}]),vertexShader:rt.meshtoon_vert,fragmentShader:rt.meshtoon_frag},matcap:{uniforms:Sn([Ge.common,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.fog,{matcap:{value:null}}]),vertexShader:rt.meshmatcap_vert,fragmentShader:rt.meshmatcap_frag},points:{uniforms:Sn([Ge.points,Ge.fog]),vertexShader:rt.points_vert,fragmentShader:rt.points_frag},dashed:{uniforms:Sn([Ge.common,Ge.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:rt.linedashed_vert,fragmentShader:rt.linedashed_frag},depth:{uniforms:Sn([Ge.common,Ge.displacementmap]),vertexShader:rt.depth_vert,fragmentShader:rt.depth_frag},normal:{uniforms:Sn([Ge.common,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,{opacity:{value:1}}]),vertexShader:rt.meshnormal_vert,fragmentShader:rt.meshnormal_frag},sprite:{uniforms:Sn([Ge.sprite,Ge.fog]),vertexShader:rt.sprite_vert,fragmentShader:rt.sprite_frag},background:{uniforms:{uvTransform:{value:new it},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:rt.background_vert,fragmentShader:rt.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new it}},vertexShader:rt.backgroundCube_vert,fragmentShader:rt.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:rt.cube_vert,fragmentShader:rt.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:rt.equirect_vert,fragmentShader:rt.equirect_frag},distance:{uniforms:Sn([Ge.common,Ge.displacementmap,{referencePosition:{value:new $},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:rt.distance_vert,fragmentShader:rt.distance_frag},shadow:{uniforms:Sn([Ge.lights,Ge.fog,{color:{value:new ut(0)},opacity:{value:1}}]),vertexShader:rt.shadow_vert,fragmentShader:rt.shadow_frag}};Mi.physical={uniforms:Sn([Mi.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new it},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new it},clearcoatNormalScale:{value:new Xe(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new it},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new it},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new it},sheen:{value:0},sheenColor:{value:new ut(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new it},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new it},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new it},transmissionSamplerSize:{value:new Xe},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new it},attenuationDistance:{value:0},attenuationColor:{value:new ut(0)},specularColor:{value:new ut(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new it},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new it},anisotropyVector:{value:new Xe},anisotropyMap:{value:null},anisotropyMapTransform:{value:new it}}]),vertexShader:rt.meshphysical_vert,fragmentShader:rt.meshphysical_frag};const No={r:0,b:0,g:0},Ty=new zt,e0=new it;e0.set(-1,0,0,0,1,0,0,0,1);function Ey(n,e,t,i,r,s){const a=new ut(0);let o=r===!0?0:1,l,c,u=null,f=0,h=null;function d(v){let S=v.isScene===!0?v.background:null;if(S&&S.isTexture){const y=v.backgroundBlurriness>0;S=e.get(S,y)}return S}function m(v){let S=!1;const y=d(v);y===null?p(a,o):y&&y.isColor&&(p(y,1),S=!0);const M=n.xr.getEnvironmentBlendMode();M==="additive"?t.buffers.color.setClear(0,0,0,1,s):M==="alpha-blend"&&t.buffers.color.setClear(0,0,0,0,s),(n.autoClear||S)&&(t.buffers.depth.setTest(!0),t.buffers.depth.setMask(!0),t.buffers.color.setMask(!0),n.clear(n.autoClearColor,n.autoClearDepth,n.autoClearStencil))}function g(v,S){const y=d(S);y&&(y.isCubeTexture||y.mapping===Ul)?(c===void 0&&(c=new jn(new $a(1,1,1),new on({name:"BackgroundCubeMaterial",uniforms:Hs(Mi.backgroundCube.uniforms),vertexShader:Mi.backgroundCube.vertexShader,fragmentShader:Mi.backgroundCube.fragmentShader,side:an,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),c.geometry.deleteAttribute("uv"),c.onBeforeRender=function(M,T,w){this.matrixWorld.copyPosition(w.matrixWorld)},Object.defineProperty(c.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),i.update(c)),c.material.uniforms.envMap.value=y,c.material.uniforms.backgroundBlurriness.value=S.backgroundBlurriness,c.material.uniforms.backgroundIntensity.value=S.backgroundIntensity,c.material.uniforms.backgroundRotation.value.setFromMatrix4(Ty.makeRotationFromEuler(S.backgroundRotation)).transpose(),y.isCubeTexture&&y.isRenderTargetTexture===!1&&c.material.uniforms.backgroundRotation.value.premultiply(e0),c.material.toneMapped=ft.getTransfer(y.colorSpace)!==bt,(u!==y||f!==y.version||h!==n.toneMapping)&&(c.material.needsUpdate=!0,u=y,f=y.version,h=n.toneMapping),c.layers.enableAll(),v.unshift(c,c.geometry,c.material,0,0,null)):y&&y.isTexture&&(l===void 0&&(l=new jn(new Qr(2,2),new on({name:"BackgroundMaterial",uniforms:Hs(Mi.background.uniforms),vertexShader:Mi.background.vertexShader,fragmentShader:Mi.background.fragmentShader,side:ji,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),i.update(l)),l.material.uniforms.t2D.value=y,l.material.uniforms.backgroundIntensity.value=S.backgroundIntensity,l.material.toneMapped=ft.getTransfer(y.colorSpace)!==bt,y.matrixAutoUpdate===!0&&y.updateMatrix(),l.material.uniforms.uvTransform.value.copy(y.matrix),(u!==y||f!==y.version||h!==n.toneMapping)&&(l.material.needsUpdate=!0,u=y,f=y.version,h=n.toneMapping),l.layers.enableAll(),v.unshift(l,l.geometry,l.material,0,0,null))}function p(v,S){v.getRGB(No,qm(n)),t.buffers.color.setClear(No.r,No.g,No.b,S,s)}function _(){c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return a},setClearColor:function(v,S=1){a.set(v),o=S,p(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(v){o=v,p(a,o)},render:m,addToRenderList:g,dispose:_}}function wy(n,e){const t=n.getParameter(n.MAX_VERTEX_ATTRIBS),i={},r=h(null);let s=r,a=!1;function o(P,R,L,I,N){let O=!1;const B=f(P,I,L,R);s!==B&&(s=B,c(s.object)),O=d(P,I,L,N),O&&m(P,I,L,N),N!==null&&e.update(N,n.ELEMENT_ARRAY_BUFFER),(O||a)&&(a=!1,y(P,R,L,I),N!==null&&n.bindBuffer(n.ELEMENT_ARRAY_BUFFER,e.get(N).buffer))}function l(){return n.createVertexArray()}function c(P){return n.bindVertexArray(P)}function u(P){return n.deleteVertexArray(P)}function f(P,R,L,I){const N=I.wireframe===!0;let O=i[R.id];O===void 0&&(O={},i[R.id]=O);const B=P.isInstancedMesh===!0?P.id:0;let q=O[B];q===void 0&&(q={},O[B]=q);let F=q[L.id];F===void 0&&(F={},q[L.id]=F);let k=F[N];return k===void 0&&(k=h(l()),F[N]=k),k}function h(P){const R=[],L=[],I=[];for(let N=0;N<t;N++)R[N]=0,L[N]=0,I[N]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:R,enabledAttributes:L,attributeDivisors:I,object:P,attributes:{},index:null}}function d(P,R,L,I){const N=s.attributes,O=R.attributes;let B=0;const q=L.getAttributes();for(const F in q)if(q[F].location>=0){const U=N[F];let z=O[F];if(z===void 0&&(F==="instanceMatrix"&&P.instanceMatrix&&(z=P.instanceMatrix),F==="instanceColor"&&P.instanceColor&&(z=P.instanceColor)),U===void 0||U.attribute!==z||z&&U.data!==z.data)return!0;B++}return s.attributesNum!==B||s.index!==I}function m(P,R,L,I){const N={},O=R.attributes;let B=0;const q=L.getAttributes();for(const F in q)if(q[F].location>=0){let U=O[F];U===void 0&&(F==="instanceMatrix"&&P.instanceMatrix&&(U=P.instanceMatrix),F==="instanceColor"&&P.instanceColor&&(U=P.instanceColor));const z={};z.attribute=U,U&&U.data&&(z.data=U.data),N[F]=z,B++}s.attributes=N,s.attributesNum=B,s.index=I}function g(){const P=s.newAttributes;for(let R=0,L=P.length;R<L;R++)P[R]=0}function p(P){_(P,0)}function _(P,R){const L=s.newAttributes,I=s.enabledAttributes,N=s.attributeDivisors;L[P]=1,I[P]===0&&(n.enableVertexAttribArray(P),I[P]=1),N[P]!==R&&(n.vertexAttribDivisor(P,R),N[P]=R)}function v(){const P=s.newAttributes,R=s.enabledAttributes;for(let L=0,I=R.length;L<I;L++)R[L]!==P[L]&&(n.disableVertexAttribArray(L),R[L]=0)}function S(P,R,L,I,N,O,B){B===!0?n.vertexAttribIPointer(P,R,L,N,O):n.vertexAttribPointer(P,R,L,I,N,O)}function y(P,R,L,I){g();const N=I.attributes,O=L.getAttributes(),B=R.defaultAttributeValues;for(const q in O){const F=O[q];if(F.location>=0){let k=N[q];if(k===void 0&&(q==="instanceMatrix"&&P.instanceMatrix&&(k=P.instanceMatrix),q==="instanceColor"&&P.instanceColor&&(k=P.instanceColor)),k!==void 0){const U=k.normalized,z=k.itemSize,K=e.get(k);if(K===void 0)continue;const Z=K.buffer,X=K.type,H=K.bytesPerElement,V=X===n.INT||X===n.UNSIGNED_INT||k.gpuType===jh;if(k.isInterleavedBufferAttribute){const j=k.data,le=j.stride,ge=k.offset;if(j.isInstancedInterleavedBuffer){for(let oe=0;oe<F.locationSize;oe++)_(F.location+oe,j.meshPerAttribute);P.isInstancedMesh!==!0&&I._maxInstanceCount===void 0&&(I._maxInstanceCount=j.meshPerAttribute*j.count)}else for(let oe=0;oe<F.locationSize;oe++)p(F.location+oe);n.bindBuffer(n.ARRAY_BUFFER,Z);for(let oe=0;oe<F.locationSize;oe++)S(F.location+oe,z/F.locationSize,X,U,le*H,(ge+z/F.locationSize*oe)*H,V)}else{if(k.isInstancedBufferAttribute){for(let j=0;j<F.locationSize;j++)_(F.location+j,k.meshPerAttribute);P.isInstancedMesh!==!0&&I._maxInstanceCount===void 0&&(I._maxInstanceCount=k.meshPerAttribute*k.count)}else for(let j=0;j<F.locationSize;j++)p(F.location+j);n.bindBuffer(n.ARRAY_BUFFER,Z);for(let j=0;j<F.locationSize;j++)S(F.location+j,z/F.locationSize,X,U,z*H,z/F.locationSize*j*H,V)}}else if(B!==void 0){const U=B[q];if(U!==void 0)switch(U.length){case 2:n.vertexAttrib2fv(F.location,U);break;case 3:n.vertexAttrib3fv(F.location,U);break;case 4:n.vertexAttrib4fv(F.location,U);break;default:n.vertexAttrib1fv(F.location,U)}}}}v()}function M(){x();for(const P in i){const R=i[P];for(const L in R){const I=R[L];for(const N in I){const O=I[N];for(const B in O)u(O[B].object),delete O[B];delete I[N]}}delete i[P]}}function T(P){if(i[P.id]===void 0)return;const R=i[P.id];for(const L in R){const I=R[L];for(const N in I){const O=I[N];for(const B in O)u(O[B].object),delete O[B];delete I[N]}}delete i[P.id]}function w(P){for(const R in i){const L=i[R];for(const I in L){const N=L[I];if(N[P.id]===void 0)continue;const O=N[P.id];for(const B in O)u(O[B].object),delete O[B];delete N[P.id]}}}function b(P){for(const R in i){const L=i[R],I=P.isInstancedMesh===!0?P.id:0,N=L[I];if(N!==void 0){for(const O in N){const B=N[O];for(const q in B)u(B[q].object),delete B[q];delete N[O]}delete L[I],Object.keys(L).length===0&&delete i[R]}}}function x(){A(),a=!0,s!==r&&(s=r,c(s.object))}function A(){r.geometry=null,r.program=null,r.wireframe=!1}return{setup:o,reset:x,resetDefaultState:A,dispose:M,releaseStatesOfGeometry:T,releaseStatesOfObject:b,releaseStatesOfProgram:w,initAttributes:g,enableAttribute:p,disableUnusedAttributes:v}}function Ay(n,e,t){let i;function r(l){i=l}function s(l,c){n.drawArrays(i,l,c),t.update(c,i,1)}function a(l,c,u){u!==0&&(n.drawArraysInstanced(i,l,c,u),t.update(c,i,u))}function o(l,c,u){if(u===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(i,l,0,c,0,u);let h=0;for(let d=0;d<u;d++)h+=c[d];t.update(h,i,1)}this.setMode=r,this.render=s,this.renderInstances=a,this.renderMultiDraw=o}function Ry(n,e,t,i){let r;function s(){if(r!==void 0)return r;if(e.has("EXT_texture_filter_anisotropic")===!0){const w=e.get("EXT_texture_filter_anisotropic");r=n.getParameter(w.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else r=0;return r}function a(w){return!(w!==fi&&i.convert(w)!==n.getParameter(n.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(w){const b=w===Yi&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(w!==Yt&&i.convert(w)!==n.getParameter(n.IMPLEMENTATION_COLOR_READ_TYPE)&&w!==hi&&!b)}function l(w){if(w==="highp"){if(n.getShaderPrecisionFormat(n.VERTEX_SHADER,n.HIGH_FLOAT).precision>0&&n.getShaderPrecisionFormat(n.FRAGMENT_SHADER,n.HIGH_FLOAT).precision>0)return"highp";w="mediump"}return w==="mediump"&&n.getShaderPrecisionFormat(n.VERTEX_SHADER,n.MEDIUM_FLOAT).precision>0&&n.getShaderPrecisionFormat(n.FRAGMENT_SHADER,n.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=t.precision!==void 0?t.precision:"highp";const u=l(c);u!==c&&(Je("WebGLRenderer:",c,"not supported, using",u,"instead."),c=u);const f=t.logarithmicDepthBuffer===!0,h=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control");t.reversedDepthBuffer===!0&&h===!1&&Je("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");const d=n.getParameter(n.MAX_TEXTURE_IMAGE_UNITS),m=n.getParameter(n.MAX_VERTEX_TEXTURE_IMAGE_UNITS),g=n.getParameter(n.MAX_TEXTURE_SIZE),p=n.getParameter(n.MAX_CUBE_MAP_TEXTURE_SIZE),_=n.getParameter(n.MAX_VERTEX_ATTRIBS),v=n.getParameter(n.MAX_VERTEX_UNIFORM_VECTORS),S=n.getParameter(n.MAX_VARYING_VECTORS),y=n.getParameter(n.MAX_FRAGMENT_UNIFORM_VECTORS),M=n.getParameter(n.MAX_SAMPLES),T=n.getParameter(n.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:s,getMaxPrecision:l,textureFormatReadable:a,textureTypeReadable:o,precision:c,logarithmicDepthBuffer:f,reversedDepthBuffer:h,maxTextures:d,maxVertexTextures:m,maxTextureSize:g,maxCubemapSize:p,maxAttributes:_,maxVertexUniforms:v,maxVaryings:S,maxFragmentUniforms:y,maxSamples:M,samples:T}}function Cy(n){const e=this;let t=null,i=0,r=!1,s=!1;const a=new ur,o=new it,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(f,h){const d=f.length!==0||h||i!==0||r;return r=h,i=f.length,d},this.beginShadows=function(){s=!0,u(null)},this.endShadows=function(){s=!1},this.setGlobalState=function(f,h){t=u(f,h,0)},this.setState=function(f,h,d){const m=f.clippingPlanes,g=f.clipIntersection,p=f.clipShadows,_=n.get(f);if(!r||m===null||m.length===0||s&&!p)s?u(null):c();else{const v=s?0:i,S=v*4;let y=_.clippingState||null;l.value=y,y=u(m,h,S,d);for(let M=0;M!==S;++M)y[M]=t[M];_.clippingState=y,this.numIntersection=g?this.numPlanes:0,this.numPlanes+=v}};function c(){l.value!==t&&(l.value=t,l.needsUpdate=i>0),e.numPlanes=i,e.numIntersection=0}function u(f,h,d,m){const g=f!==null?f.length:0;let p=null;if(g!==0){if(p=l.value,m!==!0||p===null){const _=d+g*4,v=h.matrixWorldInverse;o.getNormalMatrix(v),(p===null||p.length<_)&&(p=new Float32Array(_));for(let S=0,y=d;S!==g;++S,y+=4)a.copy(f[S]).applyMatrix4(v,o),a.normal.toArray(p,y),p[y+3]=a.constant}l.value=p,l.needsUpdate=!0}return e.numPlanes=g,e.numIntersection=0,p}}const dr=4,kd=[.125,.215,.35,.446,.526,.582],kr=20,Py=256,ya=new rf,zd=new ut;let Ic=null,Fc=0,Nc=0,Oc=!1;const Dy=new $;class Gd{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._sigmas=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,i=.1,r=100,s={}){const{size:a=256,position:o=Dy}=s;Ic=this._renderer.getRenderTarget(),Fc=this._renderer.getActiveCubeFace(),Nc=this._renderer.getActiveMipmapLevel(),Oc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);const l=this._allocateTargets();return l.depthBuffer=!0,this._sceneToCubeUV(e,i,r,l,o),t>0&&this._blur(l,0,0,t),this._applyPMREM(l),this._cleanup(l),l}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=Wd(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=Vd(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(Ic,Fc,Nc),this._renderer.xr.enabled=Oc,e.scissorTest=!1,Es(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===Zr||e.mapping===ks?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),Ic=this._renderer.getRenderTarget(),Fc=this._renderer.getActiveCubeFace(),Nc=this._renderer.getActiveMipmapLevel(),Oc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const i=t||this._allocateTargets();return this._textureToCubeUV(e,i),this._applyPMREM(i),this._cleanup(i),i}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,i={magFilter:Gt,minFilter:Gt,generateMipmaps:!1,type:Yi,format:fi,colorSpace:Gs,depthBuffer:!1},r=Hd(e,t,i);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=Hd(e,t,i);const{_lodMax:s}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods,sigmas:this._sigmas}=Uy(s)),this._blurMaterial=Iy(s,e,t),this._ggxMaterial=Ly(s,e,t)}return r}_compileMaterial(e){const t=new jn(new Dt,e);this._renderer.compile(t,ya)}_sceneToCubeUV(e,t,i,r,s){const l=new Gn(90,1,t,i),c=[1,-1,1,1,1,1],u=[1,1,1,-1,-1,-1],f=this._renderer,h=f.autoClear,d=f.toneMapping;f.getClearColor(zd),f.toneMapping=Di,f.autoClear=!1,f.state.buffers.depth.getReversed()&&(f.setRenderTarget(r),f.clearDepth(),f.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new jn(new $a,new tf({name:"PMREM.Background",side:an,depthWrite:!1,depthTest:!1})));const g=this._backgroundBox,p=g.material;let _=!1;const v=e.background;v?v.isColor&&(p.color.copy(v),e.background=null,_=!0):(p.color.copy(zd),_=!0);for(let S=0;S<6;S++){const y=S%3;y===0?(l.up.set(0,c[S],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x+u[S],s.y,s.z)):y===1?(l.up.set(0,0,c[S]),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y+u[S],s.z)):(l.up.set(0,c[S],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y,s.z+u[S]));const M=this._cubeSize;Es(r,y*M,S>2?M:0,M,M),f.setRenderTarget(r),_&&f.render(g,l),f.render(e,l)}f.toneMapping=d,f.autoClear=h,e.background=v}_textureToCubeUV(e,t){const i=this._renderer,r=e.mapping===Zr||e.mapping===ks;r?(this._cubemapMaterial===null&&(this._cubemapMaterial=Wd()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=Vd());const s=r?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=s;const o=s.uniforms;o.envMap.value=e;const l=this._cubeSize;Es(t,0,0,3*l,2*l),i.setRenderTarget(t),i.render(a,ya)}_applyPMREM(e){const t=this._renderer,i=t.autoClear;t.autoClear=!1;const r=this._lodMeshes.length;for(let s=1;s<r;s++)this._applyGGXFilter(e,s-1,s);t.autoClear=i}_applyGGXFilter(e,t,i){const r=this._renderer,s=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[i];o.material=a;const l=a.uniforms,c=i/(this._lodMeshes.length-1),u=t/(this._lodMeshes.length-1),f=Math.sqrt(c*c-u*u),h=0+c*1.25,d=f*h,{_lodMax:m}=this,g=this._sizeLods[i],p=3*g*(i>m-dr?i-m+dr:0),_=4*(this._cubeSize-g);l.envMap.value=e.texture,l.roughness.value=d,l.mipInt.value=m-t,Es(s,p,_,3*g,2*g),r.setRenderTarget(s),r.render(o,ya),l.envMap.value=s.texture,l.roughness.value=0,l.mipInt.value=m-i,Es(e,p,_,3*g,2*g),r.setRenderTarget(e),r.render(o,ya)}_blur(e,t,i,r,s){const a=this._pingPongRenderTarget;this._halfBlur(e,a,t,i,r,"latitudinal",s),this._halfBlur(a,e,i,i,r,"longitudinal",s)}_halfBlur(e,t,i,r,s,a,o){const l=this._renderer,c=this._blurMaterial;a!=="latitudinal"&&a!=="longitudinal"&&pt("blur direction must be either latitudinal or longitudinal!");const u=3,f=this._lodMeshes[r];f.material=c;const h=c.uniforms,d=this._sizeLods[i]-1,m=isFinite(s)?Math.PI/(2*d):2*Math.PI/(2*kr-1),g=s/m,p=isFinite(s)?1+Math.floor(u*g):kr;p>kr&&Je(`sigmaRadians, ${s}, is too large and will clip, as it requested ${p} samples when the maximum is set to ${kr}`);const _=[];let v=0;for(let w=0;w<kr;++w){const b=w/g,x=Math.exp(-b*b/2);_.push(x),w===0?v+=x:w<p&&(v+=2*x)}for(let w=0;w<_.length;w++)_[w]=_[w]/v;h.envMap.value=e.texture,h.samples.value=p,h.weights.value=_,h.latitudinal.value=a==="latitudinal",o&&(h.poleAxis.value=o);const{_lodMax:S}=this;h.dTheta.value=m,h.mipInt.value=S-i;const y=this._sizeLods[r],M=3*y*(r>S-dr?r-S+dr:0),T=4*(this._cubeSize-y);Es(t,M,T,3*y,2*y),l.setRenderTarget(t),l.render(f,ya)}}function Uy(n){const e=[],t=[],i=[];let r=n;const s=n-dr+1+kd.length;for(let a=0;a<s;a++){const o=Math.pow(2,r);e.push(o);let l=1/o;a>n-dr?l=kd[a-n+dr-1]:a===0&&(l=0),t.push(l);const c=1/(o-2),u=-c,f=1+c,h=[u,u,f,u,f,f,u,u,f,f,u,f],d=6,m=6,g=3,p=2,_=1,v=new Float32Array(g*m*d),S=new Float32Array(p*m*d),y=new Float32Array(_*m*d);for(let T=0;T<d;T++){const w=T%3*2/3-1,b=T>2?0:-1,x=[w,b,0,w+2/3,b,0,w+2/3,b+1,0,w,b,0,w+2/3,b+1,0,w,b+1,0];v.set(x,g*m*T),S.set(h,p*m*T);const A=[T,T,T,T,T,T];y.set(A,_*m*T)}const M=new Dt;M.setAttribute("position",new Nt(v,g)),M.setAttribute("uv",new Nt(S,p)),M.setAttribute("faceIndex",new Nt(y,_)),i.push(new jn(M,null)),r>dr&&r--}return{lodMeshes:i,sizeLods:e,sigmas:t}}function Hd(n,e,t){const i=new Jt(n,e,t);return i.texture.mapping=Ul,i.texture.name="PMREM.cubeUv",i.scissorTest=!0,i}function Es(n,e,t,i,r){n.viewport.set(e,t,i,r),n.scissor.set(e,t,i,r)}function Ly(n,e,t){return new on({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:Py,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${n}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:Il(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float roughness;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359

			// Van der Corput radical inverse
			float radicalInverse_VdC(uint bits) {
				bits = (bits << 16u) | (bits >> 16u);
				bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
				bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
				bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
				bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);
				return float(bits) * 2.3283064365386963e-10; // / 0x100000000
			}

			// Hammersley sequence
			vec2 hammersley(uint i, uint N) {
				return vec2(float(i) / float(N), radicalInverse_VdC(i));
			}

			// GGX VNDF importance sampling (Eric Heitz 2018)
			// "Sampling the GGX Distribution of Visible Normals"
			// https://jcgt.org/published/0007/04/01/
			vec3 importanceSampleGGX_VNDF(vec2 Xi, vec3 V, float roughness) {
				float alpha = roughness * roughness;

				// Section 4.1: Orthonormal basis
				vec3 T1 = vec3(1.0, 0.0, 0.0);
				vec3 T2 = cross(V, T1);

				// Section 4.2: Parameterization of projected area
				float r = sqrt(Xi.x);
				float phi = 2.0 * PI * Xi.y;
				float t1 = r * cos(phi);
				float t2 = r * sin(phi);
				float s = 0.5 * (1.0 + V.z);
				t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;

				// Section 4.3: Reprojection onto hemisphere
				vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0.0, 1.0 - t1 * t1 - t2 * t2)) * V;

				// Section 3.4: Transform back to ellipsoid configuration
				return normalize(vec3(alpha * Nh.x, alpha * Nh.y, max(0.0, Nh.z)));
			}

			void main() {
				vec3 N = normalize(vOutputDirection);
				vec3 V = N; // Assume view direction equals normal for pre-filtering

				vec3 prefilteredColor = vec3(0.0);
				float totalWeight = 0.0;

				// For very low roughness, just sample the environment directly
				if (roughness < 0.001) {
					gl_FragColor = vec4(bilinearCubeUV(envMap, N, mipInt), 1.0);
					return;
				}

				// Tangent space basis for VNDF sampling
				vec3 up = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
				vec3 tangent = normalize(cross(up, N));
				vec3 bitangent = cross(N, tangent);

				for(uint i = 0u; i < uint(GGX_SAMPLES); i++) {
					vec2 Xi = hammersley(i, uint(GGX_SAMPLES));

					// For PMREM, V = N, so in tangent space V is always (0, 0, 1)
					vec3 H_tangent = importanceSampleGGX_VNDF(Xi, vec3(0.0, 0.0, 1.0), roughness);

					// Transform H back to world space
					vec3 H = normalize(tangent * H_tangent.x + bitangent * H_tangent.y + N * H_tangent.z);
					vec3 L = normalize(2.0 * dot(V, H) * H - V);

					float NdotL = max(dot(N, L), 0.0);

					if(NdotL > 0.0) {
						// Sample environment at fixed mip level
						// VNDF importance sampling handles the distribution filtering
						vec3 sampleColor = bilinearCubeUV(envMap, L, mipInt);

						// Weight by NdotL for the split-sum approximation
						// VNDF PDF naturally accounts for the visible microfacet distribution
						prefilteredColor += sampleColor * NdotL;
						totalWeight += NdotL;
					}
				}

				if (totalWeight > 0.0) {
					prefilteredColor = prefilteredColor / totalWeight;
				}

				gl_FragColor = vec4(prefilteredColor, 1.0);
			}
		`,blending:Tn,depthTest:!1,depthWrite:!1})}function Iy(n,e,t){const i=new Float32Array(kr),r=new $(0,1,0);return new on({name:"SphericalGaussianBlur",defines:{n:kr,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${n}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:i},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:r}},vertexShader:Il(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,blending:Tn,depthTest:!1,depthWrite:!1})}function Vd(){return new on({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Il(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:Tn,depthTest:!1,depthWrite:!1})}function Wd(){return new on({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Il(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Tn,depthTest:!1,depthWrite:!1})}function Il(){return`

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`}class t0 extends Jt{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;const i={width:e,height:e,depth:1},r=[i,i,i,i,i,i];this.texture=new jm(r),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;const i={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},r=new $a(5,5,5),s=new on({name:"CubemapFromEquirect",uniforms:Hs(i.uniforms),vertexShader:i.vertexShader,fragmentShader:i.fragmentShader,side:an,blending:Tn});s.uniforms.tEquirect.value=t;const a=new jn(r,s),o=t.minFilter;return t.minFilter===zr&&(t.minFilter=Gt),new Bv(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,i=!0,r=!0){const s=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,i,r);e.setRenderTarget(s)}}function Fy(n){let e=new WeakMap,t=new WeakMap,i=null;function r(h,d=!1){return h==null?null:d?a(h):s(h)}function s(h){if(h&&h.isTexture){const d=h.mapping;if(d===ac||d===oc)if(e.has(h)){const m=e.get(h).texture;return o(m,h.mapping)}else{const m=h.image;if(m&&m.height>0){const g=new t0(m.height);return g.fromEquirectangularTexture(n,h),e.set(h,g),h.addEventListener("dispose",c),o(g.texture,h.mapping)}else return null}}return h}function a(h){if(h&&h.isTexture){const d=h.mapping,m=d===ac||d===oc,g=d===Zr||d===ks;if(m||g){let p=t.get(h);const _=p!==void 0?p.texture.pmremVersion:0;if(h.isRenderTargetTexture&&h.pmremVersion!==_)return i===null&&(i=new Gd(n)),p=m?i.fromEquirectangular(h,p):i.fromCubemap(h,p),p.texture.pmremVersion=h.pmremVersion,t.set(h,p),p.texture;if(p!==void 0)return p.texture;{const v=h.image;return m&&v&&v.height>0||g&&v&&l(v)?(i===null&&(i=new Gd(n)),p=m?i.fromEquirectangular(h):i.fromCubemap(h),p.texture.pmremVersion=h.pmremVersion,t.set(h,p),h.addEventListener("dispose",u),p.texture):null}}}return h}function o(h,d){return d===ac?h.mapping=Zr:d===oc&&(h.mapping=ks),h}function l(h){let d=0;const m=6;for(let g=0;g<m;g++)h[g]!==void 0&&d++;return d===m}function c(h){const d=h.target;d.removeEventListener("dispose",c);const m=e.get(d);m!==void 0&&(e.delete(d),m.dispose())}function u(h){const d=h.target;d.removeEventListener("dispose",u);const m=t.get(d);m!==void 0&&(t.delete(d),m.dispose())}function f(){e=new WeakMap,t=new WeakMap,i!==null&&(i.dispose(),i=null)}return{get:r,dispose:f}}function Ny(n){const e={};function t(i){if(e[i]!==void 0)return e[i];const r=n.getExtension(i);return e[i]=r,r}return{has:function(i){return t(i)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(i){const r=t(i);return r===null&&fh("WebGLRenderer: "+i+" extension not supported."),r}}}function Oy(n,e,t,i){const r={},s=new WeakMap;function a(f){const h=f.target;h.index!==null&&e.remove(h.index);for(const m in h.attributes)e.remove(h.attributes[m]);h.removeEventListener("dispose",a),delete r[h.id];const d=s.get(h);d&&(e.remove(d),s.delete(h)),i.releaseStatesOfGeometry(h),h.isInstancedBufferGeometry===!0&&delete h._maxInstanceCount,t.memory.geometries--}function o(f,h){return r[h.id]===!0||(h.addEventListener("dispose",a),r[h.id]=!0,t.memory.geometries++),h}function l(f){const h=f.attributes;for(const d in h)e.update(h[d],n.ARRAY_BUFFER)}function c(f){const h=[],d=f.index,m=f.attributes.position;let g=0;if(m===void 0)return;if(d!==null){const v=d.array;g=d.version;for(let S=0,y=v.length;S<y;S+=3){const M=v[S+0],T=v[S+1],w=v[S+2];h.push(M,T,T,w,w,M)}}else{const v=m.array;g=m.version;for(let S=0,y=v.length/3-1;S<y;S+=3){const M=S+0,T=S+1,w=S+2;h.push(M,T,T,w,w,M)}}const p=new(m.count>=65535?Vm:Hm)(h,1);p.version=g;const _=s.get(f);_&&e.remove(_),s.set(f,p)}function u(f){const h=s.get(f);if(h){const d=f.index;d!==null&&h.version<d.version&&c(f)}else c(f);return s.get(f)}return{get:o,update:l,getWireframeAttribute:u}}function By(n,e,t){let i;function r(f){i=f}let s,a;function o(f){s=f.type,a=f.bytesPerElement}function l(f,h){n.drawElements(i,h,s,f*a),t.update(h,i,1)}function c(f,h,d){d!==0&&(n.drawElementsInstanced(i,h,s,f*a,d),t.update(h,i,d))}function u(f,h,d){if(d===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(i,h,0,s,f,0,d);let g=0;for(let p=0;p<d;p++)g+=h[p];t.update(g,i,1)}this.setMode=r,this.setIndex=o,this.render=l,this.renderInstances=c,this.renderMultiDraw=u}function ky(n){const e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function i(s,a,o){switch(t.calls++,a){case n.TRIANGLES:t.triangles+=o*(s/3);break;case n.LINES:t.lines+=o*(s/2);break;case n.LINE_STRIP:t.lines+=o*(s-1);break;case n.LINE_LOOP:t.lines+=o*s;break;case n.POINTS:t.points+=o*s;break;default:pt("WebGLInfo: Unknown draw mode:",a);break}}function r(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:r,update:i}}function zy(n,e,t){const i=new WeakMap,r=new Ut;function s(a,o,l){const c=a.morphTargetInfluences,u=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,f=u!==void 0?u.length:0;let h=i.get(o);if(h===void 0||h.count!==f){let x=function(){w.dispose(),i.delete(o),o.removeEventListener("dispose",x)};h!==void 0&&h.texture.dispose();const d=o.morphAttributes.position!==void 0,m=o.morphAttributes.normal!==void 0,g=o.morphAttributes.color!==void 0,p=o.morphAttributes.position||[],_=o.morphAttributes.normal||[],v=o.morphAttributes.color||[];let S=0;d===!0&&(S=1),m===!0&&(S=2),g===!0&&(S=3);let y=o.attributes.position.count*S,M=1;y>e.maxTextureSize&&(M=Math.ceil(y/e.maxTextureSize),y=e.maxTextureSize);const T=new Float32Array(y*M*4*f),w=new km(T,y,M,f);w.type=hi,w.needsUpdate=!0;const b=S*4;for(let A=0;A<f;A++){const P=p[A],R=_[A],L=v[A],I=y*M*4*A;for(let N=0;N<P.count;N++){const O=N*b;d===!0&&(r.fromBufferAttribute(P,N),T[I+O+0]=r.x,T[I+O+1]=r.y,T[I+O+2]=r.z,T[I+O+3]=0),m===!0&&(r.fromBufferAttribute(R,N),T[I+O+4]=r.x,T[I+O+5]=r.y,T[I+O+6]=r.z,T[I+O+7]=0),g===!0&&(r.fromBufferAttribute(L,N),T[I+O+8]=r.x,T[I+O+9]=r.y,T[I+O+10]=r.z,T[I+O+11]=L.itemSize===4?r.w:1)}}h={count:f,texture:w,size:new Xe(y,M)},i.set(o,h),o.addEventListener("dispose",x)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)l.getUniforms().setValue(n,"morphTexture",a.morphTexture,t);else{let d=0;for(let g=0;g<c.length;g++)d+=c[g];const m=o.morphTargetsRelative?1:1-d;l.getUniforms().setValue(n,"morphTargetBaseInfluence",m),l.getUniforms().setValue(n,"morphTargetInfluences",c)}l.getUniforms().setValue(n,"morphTargetsTexture",h.texture,t),l.getUniforms().setValue(n,"morphTargetsTextureSize",h.size)}return{update:s}}function Gy(n,e,t,i,r){let s=new WeakMap;function a(c){const u=r.render.frame,f=c.geometry,h=e.get(c,f);if(s.get(h)!==u&&(e.update(h),s.set(h,u)),c.isInstancedMesh&&(c.hasEventListener("dispose",l)===!1&&c.addEventListener("dispose",l),s.get(c)!==u&&(t.update(c.instanceMatrix,n.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,n.ARRAY_BUFFER),s.set(c,u))),c.isSkinnedMesh){const d=c.skeleton;s.get(d)!==u&&(d.update(),s.set(d,u))}return h}function o(){s=new WeakMap}function l(c){const u=c.target;u.removeEventListener("dispose",l),i.releaseStatesOfObject(u),t.remove(u.instanceMatrix),u.instanceColor!==null&&t.remove(u.instanceColor)}return{update:a,dispose:o}}const Hy={[Mm]:"LINEAR_TONE_MAPPING",[Tm]:"REINHARD_TONE_MAPPING",[Em]:"CINEON_TONE_MAPPING",[wm]:"ACES_FILMIC_TONE_MAPPING",[Rm]:"AGX_TONE_MAPPING",[Cm]:"NEUTRAL_TONE_MAPPING",[Am]:"CUSTOM_TONE_MAPPING"};function Vy(n,e,t,i,r){const s=new Jt(e,t,{type:n,depthBuffer:i,stencilBuffer:r,depthTexture:i?new Xi(e,t):void 0}),a=new Jt(e,t,{type:Yi,depthBuffer:!1,stencilBuffer:!1}),o=new Dt;o.setAttribute("position",new di([-1,3,0,-1,-1,0,3,-1,0],3)),o.setAttribute("uv",new di([0,2,0,0,2,0],2));const l=new Nv({uniforms:{tDiffuse:{value:null}},vertexShader:`
			precision highp float;

			uniform mat4 modelViewMatrix;
			uniform mat4 projectionMatrix;

			attribute vec3 position;
			attribute vec2 uv;

			varying vec2 vUv;

			void main() {
				vUv = uv;
				gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
			}`,fragmentShader:`
			precision highp float;

			uniform sampler2D tDiffuse;

			varying vec2 vUv;

			#include <tonemapping_pars_fragment>
			#include <colorspace_pars_fragment>

			void main() {
				gl_FragColor = texture2D( tDiffuse, vUv );

				#ifdef LINEAR_TONE_MAPPING
					gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );
				#elif defined( REINHARD_TONE_MAPPING )
					gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );
				#elif defined( CINEON_TONE_MAPPING )
					gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );
				#elif defined( ACES_FILMIC_TONE_MAPPING )
					gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );
				#elif defined( AGX_TONE_MAPPING )
					gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );
				#elif defined( NEUTRAL_TONE_MAPPING )
					gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );
				#elif defined( CUSTOM_TONE_MAPPING )
					gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );
				#endif

				#ifdef SRGB_TRANSFER
					gl_FragColor = sRGBTransferOETF( gl_FragColor );
				#endif
			}`,depthTest:!1,depthWrite:!1}),c=new jn(o,l),u=new rf(-1,1,1,-1,0,1);let f=null,h=null,d=!1,m,g=null,p=[],_=!1;this.setSize=function(v,S){s.setSize(v,S),a.setSize(v,S);for(let y=0;y<p.length;y++){const M=p[y];M.setSize&&M.setSize(v,S)}},this.setEffects=function(v){p=v,_=p.length>0&&p[0].isRenderPass===!0;const S=s.width,y=s.height;for(let M=0;M<p.length;M++){const T=p[M];T.setSize&&T.setSize(S,y)}},this.begin=function(v,S){if(d||v.toneMapping===Di&&p.length===0)return!1;if(g=S,S!==null){const y=S.width,M=S.height;(s.width!==y||s.height!==M)&&this.setSize(y,M)}return _===!1&&v.setRenderTarget(s),m=v.toneMapping,v.toneMapping=Di,!0},this.hasRenderPass=function(){return _},this.end=function(v,S){v.toneMapping=m,d=!0;let y=s,M=a;for(let T=0;T<p.length;T++){const w=p[T];if(w.enabled!==!1&&(w.render(v,M,y,S),w.needsSwap!==!1)){const b=y;y=M,M=b}}if(f!==v.outputColorSpace||h!==v.toneMapping){f=v.outputColorSpace,h=v.toneMapping,l.defines={},ft.getTransfer(f)===bt&&(l.defines.SRGB_TRANSFER="");const T=Hy[h];T&&(l.defines[T]=""),l.needsUpdate=!0}l.uniforms.tDiffuse.value=y.texture,v.setRenderTarget(g),v.render(c,u),g=null,d=!1},this.isCompositing=function(){return d},this.dispose=function(){s.depthTexture&&s.depthTexture.dispose(),s.dispose(),a.dispose(),o.dispose(),l.dispose()}}const n0=new $t,_h=new Xi(1,1),i0=new km,r0=new uv,s0=new jm,Xd=[],jd=[],Yd=new Float32Array(16),qd=new Float32Array(9),Kd=new Float32Array(4);function $s(n,e,t){const i=n[0];if(i<=0||i>0)return n;const r=e*t;let s=Xd[r];if(s===void 0&&(s=new Float32Array(r),Xd[r]=s),e!==0){i.toArray(s,0);for(let a=1,o=0;a!==e;++a)o+=t,n[a].toArray(s,o)}return s}function Qt(n,e){if(n.length!==e.length)return!1;for(let t=0,i=n.length;t<i;t++)if(n[t]!==e[t])return!1;return!0}function en(n,e){for(let t=0,i=e.length;t<i;t++)n[t]=e[t]}function Fl(n,e){let t=jd[e];t===void 0&&(t=new Int32Array(e),jd[e]=t);for(let i=0;i!==e;++i)t[i]=n.allocateTextureUnit();return t}function Wy(n,e){const t=this.cache;t[0]!==e&&(n.uniform1f(this.addr,e),t[0]=e)}function Xy(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Qt(t,e))return;n.uniform2fv(this.addr,e),en(t,e)}}function jy(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(n.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(Qt(t,e))return;n.uniform3fv(this.addr,e),en(t,e)}}function Yy(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Qt(t,e))return;n.uniform4fv(this.addr,e),en(t,e)}}function qy(n,e){const t=this.cache,i=e.elements;if(i===void 0){if(Qt(t,e))return;n.uniformMatrix2fv(this.addr,!1,e),en(t,e)}else{if(Qt(t,i))return;Kd.set(i),n.uniformMatrix2fv(this.addr,!1,Kd),en(t,i)}}function Ky(n,e){const t=this.cache,i=e.elements;if(i===void 0){if(Qt(t,e))return;n.uniformMatrix3fv(this.addr,!1,e),en(t,e)}else{if(Qt(t,i))return;qd.set(i),n.uniformMatrix3fv(this.addr,!1,qd),en(t,i)}}function Zy(n,e){const t=this.cache,i=e.elements;if(i===void 0){if(Qt(t,e))return;n.uniformMatrix4fv(this.addr,!1,e),en(t,e)}else{if(Qt(t,i))return;Yd.set(i),n.uniformMatrix4fv(this.addr,!1,Yd),en(t,i)}}function $y(n,e){const t=this.cache;t[0]!==e&&(n.uniform1i(this.addr,e),t[0]=e)}function Jy(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Qt(t,e))return;n.uniform2iv(this.addr,e),en(t,e)}}function Qy(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Qt(t,e))return;n.uniform3iv(this.addr,e),en(t,e)}}function eb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Qt(t,e))return;n.uniform4iv(this.addr,e),en(t,e)}}function tb(n,e){const t=this.cache;t[0]!==e&&(n.uniform1ui(this.addr,e),t[0]=e)}function nb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Qt(t,e))return;n.uniform2uiv(this.addr,e),en(t,e)}}function ib(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Qt(t,e))return;n.uniform3uiv(this.addr,e),en(t,e)}}function rb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Qt(t,e))return;n.uniform4uiv(this.addr,e),en(t,e)}}function sb(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r);let s;this.type===n.SAMPLER_2D_SHADOW?(_h.compareFunction=t.isReversedDepthBuffer()?Qh:Jh,s=_h):s=n0,t.setTexture2D(e||s,r)}function ab(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r),t.setTexture3D(e||r0,r)}function ob(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r),t.setTextureCube(e||s0,r)}function lb(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r),t.setTexture2DArray(e||i0,r)}function cb(n){switch(n){case 5126:return Wy;case 35664:return Xy;case 35665:return jy;case 35666:return Yy;case 35674:return qy;case 35675:return Ky;case 35676:return Zy;case 5124:case 35670:return $y;case 35667:case 35671:return Jy;case 35668:case 35672:return Qy;case 35669:case 35673:return eb;case 5125:return tb;case 36294:return nb;case 36295:return ib;case 36296:return rb;case 35678:case 36198:case 36298:case 36306:case 35682:return sb;case 35679:case 36299:case 36307:return ab;case 35680:case 36300:case 36308:case 36293:return ob;case 36289:case 36303:case 36311:case 36292:return lb}}function ub(n,e){n.uniform1fv(this.addr,e)}function hb(n,e){const t=$s(e,this.size,2);n.uniform2fv(this.addr,t)}function fb(n,e){const t=$s(e,this.size,3);n.uniform3fv(this.addr,t)}function db(n,e){const t=$s(e,this.size,4);n.uniform4fv(this.addr,t)}function pb(n,e){const t=$s(e,this.size,4);n.uniformMatrix2fv(this.addr,!1,t)}function mb(n,e){const t=$s(e,this.size,9);n.uniformMatrix3fv(this.addr,!1,t)}function gb(n,e){const t=$s(e,this.size,16);n.uniformMatrix4fv(this.addr,!1,t)}function _b(n,e){n.uniform1iv(this.addr,e)}function vb(n,e){n.uniform2iv(this.addr,e)}function xb(n,e){n.uniform3iv(this.addr,e)}function yb(n,e){n.uniform4iv(this.addr,e)}function bb(n,e){n.uniform1uiv(this.addr,e)}function Sb(n,e){n.uniform2uiv(this.addr,e)}function Mb(n,e){n.uniform3uiv(this.addr,e)}function Tb(n,e){n.uniform4uiv(this.addr,e)}function Eb(n,e,t){const i=this.cache,r=e.length,s=Fl(t,r);Qt(i,s)||(n.uniform1iv(this.addr,s),en(i,s));let a;this.type===n.SAMPLER_2D_SHADOW?a=_h:a=n0;for(let o=0;o!==r;++o)t.setTexture2D(e[o]||a,s[o])}function wb(n,e,t){const i=this.cache,r=e.length,s=Fl(t,r);Qt(i,s)||(n.uniform1iv(this.addr,s),en(i,s));for(let a=0;a!==r;++a)t.setTexture3D(e[a]||r0,s[a])}function Ab(n,e,t){const i=this.cache,r=e.length,s=Fl(t,r);Qt(i,s)||(n.uniform1iv(this.addr,s),en(i,s));for(let a=0;a!==r;++a)t.setTextureCube(e[a]||s0,s[a])}function Rb(n,e,t){const i=this.cache,r=e.length,s=Fl(t,r);Qt(i,s)||(n.uniform1iv(this.addr,s),en(i,s));for(let a=0;a!==r;++a)t.setTexture2DArray(e[a]||i0,s[a])}function Cb(n){switch(n){case 5126:return ub;case 35664:return hb;case 35665:return fb;case 35666:return db;case 35674:return pb;case 35675:return mb;case 35676:return gb;case 5124:case 35670:return _b;case 35667:case 35671:return vb;case 35668:case 35672:return xb;case 35669:case 35673:return yb;case 5125:return bb;case 36294:return Sb;case 36295:return Mb;case 36296:return Tb;case 35678:case 36198:case 36298:case 36306:case 35682:return Eb;case 35679:case 36299:case 36307:return wb;case 35680:case 36300:case 36308:case 36293:return Ab;case 36289:case 36303:case 36311:case 36292:return Rb}}class Pb{constructor(e,t,i){this.id=e,this.addr=i,this.cache=[],this.type=t.type,this.setValue=cb(t.type)}}class Db{constructor(e,t,i){this.id=e,this.addr=i,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=Cb(t.type)}}class Ub{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,i){const r=this.seq;for(let s=0,a=r.length;s!==a;++s){const o=r[s];o.setValue(e,t[o.id],i)}}}const Bc=/(\w+)(\])?(\[|\.)?/g;function Zd(n,e){n.seq.push(e),n.map[e.id]=e}function Lb(n,e,t){const i=n.name,r=i.length;for(Bc.lastIndex=0;;){const s=Bc.exec(i),a=Bc.lastIndex;let o=s[1];const l=s[2]==="]",c=s[3];if(l&&(o=o|0),c===void 0||c==="["&&a+2===r){Zd(t,c===void 0?new Pb(o,n,e):new Db(o,n,e));break}else{let f=t.map[o];f===void 0&&(f=new Ub(o),Zd(t,f)),t=f}}}class Qo{constructor(e,t){this.seq=[],this.map={};const i=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let a=0;a<i;++a){const o=e.getActiveUniform(t,a),l=e.getUniformLocation(t,o.name);Lb(o,l,this)}const r=[],s=[];for(const a of this.seq)a.type===e.SAMPLER_2D_SHADOW||a.type===e.SAMPLER_CUBE_SHADOW||a.type===e.SAMPLER_2D_ARRAY_SHADOW?r.push(a):s.push(a);r.length>0&&(this.seq=r.concat(s))}setValue(e,t,i,r){const s=this.map[t];s!==void 0&&s.setValue(e,i,r)}setOptional(e,t,i){const r=t[i];r!==void 0&&this.setValue(e,i,r)}static upload(e,t,i,r){for(let s=0,a=t.length;s!==a;++s){const o=t[s],l=i[o.id];l.needsUpdate!==!1&&o.setValue(e,l.value,r)}}static seqWithValue(e,t){const i=[];for(let r=0,s=e.length;r!==s;++r){const a=e[r];a.id in t&&i.push(a)}return i}}function $d(n,e,t){const i=n.createShader(e);return n.shaderSource(i,t),n.compileShader(i),i}const Ib=37297;let Fb=0;function Nb(n,e){const t=n.split(`
`),i=[],r=Math.max(e-6,0),s=Math.min(e+6,t.length);for(let a=r;a<s;a++){const o=a+1;i.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return i.join(`
`)}const Jd=new it;function Ob(n){ft._getMatrix(Jd,ft.workingColorSpace,n);const e=`mat3( ${Jd.elements.map(t=>t.toFixed(4))} )`;switch(ft.getTransfer(n)){case hl:return[e,"LinearTransferOETF"];case bt:return[e,"sRGBTransferOETF"];default:return Je("WebGLProgram: Unsupported color space: ",n),[e,"LinearTransferOETF"]}}function Qd(n,e,t){const i=n.getShaderParameter(e,n.COMPILE_STATUS),s=(n.getShaderInfoLog(e)||"").trim();if(i&&s==="")return"";const a=/ERROR: 0:(\d+)/.exec(s);if(a){const o=parseInt(a[1]);return t.toUpperCase()+`

`+s+`

`+Nb(n.getShaderSource(e),o)}else return s}function Bb(n,e){const t=Ob(e);return[`vec4 ${n}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}const kb={[Mm]:"Linear",[Tm]:"Reinhard",[Em]:"Cineon",[wm]:"ACESFilmic",[Rm]:"AgX",[Cm]:"Neutral",[Am]:"Custom"};function zb(n,e){const t=kb[e];return t===void 0?(Je("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+n+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+n+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}const Oo=new $;function Gb(){ft.getLuminanceCoefficients(Oo);const n=Oo.x.toFixed(4),e=Oo.y.toFixed(4),t=Oo.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${n}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function Hb(n){return[n.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",n.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Ra).join(`
`)}function Vb(n){const e=[];for(const t in n){const i=n[t];i!==!1&&e.push("#define "+t+" "+i)}return e.join(`
`)}function Wb(n,e){const t={},i=n.getProgramParameter(e,n.ACTIVE_ATTRIBUTES);for(let r=0;r<i;r++){const s=n.getActiveAttrib(e,r),a=s.name;let o=1;s.type===n.FLOAT_MAT2&&(o=2),s.type===n.FLOAT_MAT3&&(o=3),s.type===n.FLOAT_MAT4&&(o=4),t[a]={type:s.type,location:n.getAttribLocation(e,a),locationSize:o}}return t}function Ra(n){return n!==""}function ep(n,e){const t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return n.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function tp(n,e){return n.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const Xb=/^[ \t]*#include +<([\w\d./]+)>/gm;function vh(n){return n.replace(Xb,Yb)}const jb=new Map;function Yb(n,e){let t=rt[e];if(t===void 0){const i=jb.get(e);if(i!==void 0)t=rt[i],Je('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,i);else throw new Error("Can not resolve #include <"+e+">")}return vh(t)}const qb=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function np(n){return n.replace(qb,Kb)}function Kb(n,e,t,i){let r="";for(let s=parseInt(e);s<parseInt(t);s++)r+=i.replace(/\[\s*i\s*\]/g,"[ "+s+" ]").replace(/UNROLLED_LOOP_INDEX/g,s);return r}function ip(n){let e=`precision ${n.precision} float;
	precision ${n.precision} int;
	precision ${n.precision} sampler2D;
	precision ${n.precision} samplerCube;
	precision ${n.precision} sampler3D;
	precision ${n.precision} sampler2DArray;
	precision ${n.precision} sampler2DShadow;
	precision ${n.precision} samplerCubeShadow;
	precision ${n.precision} sampler2DArrayShadow;
	precision ${n.precision} isampler2D;
	precision ${n.precision} isampler3D;
	precision ${n.precision} isamplerCube;
	precision ${n.precision} isampler2DArray;
	precision ${n.precision} usampler2D;
	precision ${n.precision} usampler3D;
	precision ${n.precision} usamplerCube;
	precision ${n.precision} usampler2DArray;
	`;return n.precision==="highp"?e+=`
#define HIGH_PRECISION`:n.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:n.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}const Zb={[Yo]:"SHADOWMAP_TYPE_PCF",[wa]:"SHADOWMAP_TYPE_VSM"};function $b(n){return Zb[n.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}const Jb={[Zr]:"ENVMAP_TYPE_CUBE",[ks]:"ENVMAP_TYPE_CUBE",[Ul]:"ENVMAP_TYPE_CUBE_UV"};function Qb(n){return n.envMap===!1?"ENVMAP_TYPE_CUBE":Jb[n.envMapMode]||"ENVMAP_TYPE_CUBE"}const eS={[ks]:"ENVMAP_MODE_REFRACTION"};function tS(n){return n.envMap===!1?"ENVMAP_MODE_REFLECTION":eS[n.envMapMode]||"ENVMAP_MODE_REFLECTION"}const nS={[Sm]:"ENVMAP_BLENDING_MULTIPLY",[H_]:"ENVMAP_BLENDING_MIX",[V_]:"ENVMAP_BLENDING_ADD"};function iS(n){return n.envMap===!1?"ENVMAP_BLENDING_NONE":nS[n.combine]||"ENVMAP_BLENDING_NONE"}function rS(n){const e=n.envMapCubeUVHeight;if(e===null)return null;const t=Math.log2(e)-2,i=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:i,maxMip:t}}function sS(n,e,t,i){const r=n.getContext(),s=t.defines;let a=t.vertexShader,o=t.fragmentShader;const l=$b(t),c=Qb(t),u=tS(t),f=iS(t),h=rS(t),d=Hb(t),m=Vb(s),g=r.createProgram();let p,_,v=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(p=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m].filter(Ra).join(`
`),p.length>0&&(p+=`
`),_=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m].filter(Ra).join(`
`),_.length>0&&(_+=`
`)):(p=[ip(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+u:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexNormals?"#define HAS_NORMAL":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Ra).join(`
`),_=[ip(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+c:"",t.envMap?"#define "+u:"",t.envMap?"#define "+f:"",h?"#define CUBEUV_TEXEL_WIDTH "+h.texelWidth:"",h?"#define CUBEUV_TEXEL_HEIGHT "+h.texelHeight:"",h?"#define CUBEUV_MAX_MIP "+h.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor?"#define USE_COLOR":"",t.vertexAlphas||t.batchingColor?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==Di?"#define TONE_MAPPING":"",t.toneMapping!==Di?rt.tonemapping_pars_fragment:"",t.toneMapping!==Di?zb("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",rt.colorspace_pars_fragment,Bb("linearToOutputTexel",t.outputColorSpace),Gb(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter(Ra).join(`
`)),a=vh(a),a=ep(a,t),a=tp(a,t),o=vh(o),o=ep(o,t),o=tp(o,t),a=np(a),o=np(o),t.isRawShaderMaterial!==!0&&(v=`#version 300 es
`,p=[d,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+p,_=["#define varying in",t.glslVersion===ld?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===ld?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+_);const S=v+p+a,y=v+_+o,M=$d(r,r.VERTEX_SHADER,S),T=$d(r,r.FRAGMENT_SHADER,y);r.attachShader(g,M),r.attachShader(g,T),t.index0AttributeName!==void 0?r.bindAttribLocation(g,0,t.index0AttributeName):t.morphTargets===!0&&r.bindAttribLocation(g,0,"position"),r.linkProgram(g);function w(P){if(n.debug.checkShaderErrors){const R=r.getProgramInfoLog(g)||"",L=r.getShaderInfoLog(M)||"",I=r.getShaderInfoLog(T)||"",N=R.trim(),O=L.trim(),B=I.trim();let q=!0,F=!0;if(r.getProgramParameter(g,r.LINK_STATUS)===!1)if(q=!1,typeof n.debug.onShaderError=="function")n.debug.onShaderError(r,g,M,T);else{const k=Qd(r,M,"vertex"),U=Qd(r,T,"fragment");pt("THREE.WebGLProgram: Shader Error "+r.getError()+" - VALIDATE_STATUS "+r.getProgramParameter(g,r.VALIDATE_STATUS)+`

Material Name: `+P.name+`
Material Type: `+P.type+`

Program Info Log: `+N+`
`+k+`
`+U)}else N!==""?Je("WebGLProgram: Program Info Log:",N):(O===""||B==="")&&(F=!1);F&&(P.diagnostics={runnable:q,programLog:N,vertexShader:{log:O,prefix:p},fragmentShader:{log:B,prefix:_}})}r.deleteShader(M),r.deleteShader(T),b=new Qo(r,g),x=Wb(r,g)}let b;this.getUniforms=function(){return b===void 0&&w(this),b};let x;this.getAttributes=function(){return x===void 0&&w(this),x};let A=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return A===!1&&(A=r.getProgramParameter(g,Ib)),A},this.destroy=function(){i.releaseStatesOfProgram(this),r.deleteProgram(g),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=Fb++,this.cacheKey=e,this.usedTimes=1,this.program=g,this.vertexShader=M,this.fragmentShader=T,this}let aS=0;class oS{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){const t=e.vertexShader,i=e.fragmentShader,r=this._getShaderStage(t),s=this._getShaderStage(i),a=this._getShaderCacheForMaterial(e);return a.has(r)===!1&&(a.add(r),r.usedTimes++),a.has(s)===!1&&(a.add(s),s.usedTimes++),this}remove(e){const t=this.materialCache.get(e);for(const i of t)i.usedTimes--,i.usedTimes===0&&this.shaderCache.delete(i.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const t=this.materialCache;let i=t.get(e);return i===void 0&&(i=new Set,t.set(e,i)),i}_getShaderStage(e){const t=this.shaderCache;let i=t.get(e);return i===void 0&&(i=new lS(e),t.set(e,i)),i}}class lS{constructor(e){this.id=aS++,this.code=e,this.usedTimes=0}}function cS(n){return n===$r||n===cl||n===ul}function uS(n,e,t,i,r,s){const a=new zm,o=new oS,l=new Set,c=[],u=new Map,f=i.logarithmicDepthBuffer;let h=i.precision;const d={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function m(b){return l.add(b),b===0?"uv":`uv${b}`}function g(b,x,A,P,R,L){const I=P.fog,N=R.geometry,O=b.isMeshStandardMaterial||b.isMeshLambertMaterial||b.isMeshPhongMaterial?P.environment:null,B=b.isMeshStandardMaterial||b.isMeshLambertMaterial&&!b.envMap||b.isMeshPhongMaterial&&!b.envMap,q=e.get(b.envMap||O,B),F=q&&q.mapping===Ul?q.image.height:null,k=d[b.type];b.precision!==null&&(h=i.getMaxPrecision(b.precision),h!==b.precision&&Je("WebGLProgram.getParameters:",b.precision,"not supported, using",h,"instead."));const U=N.morphAttributes.position||N.morphAttributes.normal||N.morphAttributes.color,z=U!==void 0?U.length:0;let K=0;N.morphAttributes.position!==void 0&&(K=1),N.morphAttributes.normal!==void 0&&(K=2),N.morphAttributes.color!==void 0&&(K=3);let Z,X,H,V;if(k){const Ze=Mi[k];Z=Ze.vertexShader,X=Ze.fragmentShader}else Z=b.vertexShader,X=b.fragmentShader,o.update(b),H=o.getVertexShaderID(b),V=o.getFragmentShaderID(b);const j=n.getRenderTarget(),le=n.state.buffers.depth.getReversed(),ge=R.isInstancedMesh===!0,oe=R.isBatchedMesh===!0,te=!!b.map,xe=!!b.matcap,Ae=!!q,Te=!!b.aoMap,ye=!!b.lightMap,Ue=!!b.bumpMap,me=!!b.normalMap,ke=!!b.displacementMap,G=!!b.emissiveMap,fe=!!b.metalnessMap,Fe=!!b.roughnessMap,we=b.anisotropy>0,he=b.clearcoat>0,Re=b.dispersion>0,D=b.iridescence>0,E=b.sheen>0,W=b.transmission>0,Q=we&&!!b.anisotropyMap,ue=he&&!!b.clearcoatMap,ve=he&&!!b.clearcoatNormalMap,Me=he&&!!b.clearcoatRoughnessMap,ee=D&&!!b.iridescenceMap,se=D&&!!b.iridescenceThicknessMap,de=E&&!!b.sheenColorMap,De=E&&!!b.sheenRoughnessMap,be=!!b.specularMap,Ee=!!b.specularColorMap,He=!!b.specularIntensityMap,Le=W&&!!b.transmissionMap,Ye=W&&!!b.thicknessMap,Y=!!b.gradientMap,_e=!!b.alphaMap,re=b.alphaTest>0,Pe=!!b.alphaHash,Se=!!b.extensions;let ce=Di;b.toneMapped&&(j===null||j.isXRRenderTarget===!0)&&(ce=n.toneMapping);const Ne={shaderID:k,shaderType:b.type,shaderName:b.name,vertexShader:Z,fragmentShader:X,defines:b.defines,customVertexShaderID:H,customFragmentShaderID:V,isRawShaderMaterial:b.isRawShaderMaterial===!0,glslVersion:b.glslVersion,precision:h,batching:oe,batchingColor:oe&&R._colorsTexture!==null,instancing:ge,instancingColor:ge&&R.instanceColor!==null,instancingMorph:ge&&R.morphTexture!==null,outputColorSpace:j===null?n.outputColorSpace:j.isXRRenderTarget===!0?j.texture.colorSpace:ft.workingColorSpace,alphaToCoverage:!!b.alphaToCoverage,map:te,matcap:xe,envMap:Ae,envMapMode:Ae&&q.mapping,envMapCubeUVHeight:F,aoMap:Te,lightMap:ye,bumpMap:Ue,normalMap:me,displacementMap:ke,emissiveMap:G,normalMapObjectSpace:me&&b.normalMapType===j_,normalMapTangentSpace:me&&b.normalMapType===ad,packedNormalMap:me&&b.normalMapType===ad&&cS(b.normalMap.format),metalnessMap:fe,roughnessMap:Fe,anisotropy:we,anisotropyMap:Q,clearcoat:he,clearcoatMap:ue,clearcoatNormalMap:ve,clearcoatRoughnessMap:Me,dispersion:Re,iridescence:D,iridescenceMap:ee,iridescenceThicknessMap:se,sheen:E,sheenColorMap:de,sheenRoughnessMap:De,specularMap:be,specularColorMap:Ee,specularIntensityMap:He,transmission:W,transmissionMap:Le,thicknessMap:Ye,gradientMap:Y,opaque:b.transparent===!1&&b.blending===Hr&&b.alphaToCoverage===!1,alphaMap:_e,alphaTest:re,alphaHash:Pe,combine:b.combine,mapUv:te&&m(b.map.channel),aoMapUv:Te&&m(b.aoMap.channel),lightMapUv:ye&&m(b.lightMap.channel),bumpMapUv:Ue&&m(b.bumpMap.channel),normalMapUv:me&&m(b.normalMap.channel),displacementMapUv:ke&&m(b.displacementMap.channel),emissiveMapUv:G&&m(b.emissiveMap.channel),metalnessMapUv:fe&&m(b.metalnessMap.channel),roughnessMapUv:Fe&&m(b.roughnessMap.channel),anisotropyMapUv:Q&&m(b.anisotropyMap.channel),clearcoatMapUv:ue&&m(b.clearcoatMap.channel),clearcoatNormalMapUv:ve&&m(b.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:Me&&m(b.clearcoatRoughnessMap.channel),iridescenceMapUv:ee&&m(b.iridescenceMap.channel),iridescenceThicknessMapUv:se&&m(b.iridescenceThicknessMap.channel),sheenColorMapUv:de&&m(b.sheenColorMap.channel),sheenRoughnessMapUv:De&&m(b.sheenRoughnessMap.channel),specularMapUv:be&&m(b.specularMap.channel),specularColorMapUv:Ee&&m(b.specularColorMap.channel),specularIntensityMapUv:He&&m(b.specularIntensityMap.channel),transmissionMapUv:Le&&m(b.transmissionMap.channel),thicknessMapUv:Ye&&m(b.thicknessMap.channel),alphaMapUv:_e&&m(b.alphaMap.channel),vertexTangents:!!N.attributes.tangent&&(me||we),vertexNormals:!!N.attributes.normal,vertexColors:b.vertexColors,vertexAlphas:b.vertexColors===!0&&!!N.attributes.color&&N.attributes.color.itemSize===4,pointsUvs:R.isPoints===!0&&!!N.attributes.uv&&(te||_e),fog:!!I,useFog:b.fog===!0,fogExp2:!!I&&I.isFogExp2,flatShading:b.wireframe===!1&&(b.flatShading===!0||N.attributes.normal===void 0&&me===!1&&(b.isMeshLambertMaterial||b.isMeshPhongMaterial||b.isMeshStandardMaterial||b.isMeshPhysicalMaterial)),sizeAttenuation:b.sizeAttenuation===!0,logarithmicDepthBuffer:f,reversedDepthBuffer:le,skinning:R.isSkinnedMesh===!0,morphTargets:N.morphAttributes.position!==void 0,morphNormals:N.morphAttributes.normal!==void 0,morphColors:N.morphAttributes.color!==void 0,morphTargetsCount:z,morphTextureStride:K,numDirLights:x.directional.length,numPointLights:x.point.length,numSpotLights:x.spot.length,numSpotLightMaps:x.spotLightMap.length,numRectAreaLights:x.rectArea.length,numHemiLights:x.hemi.length,numDirLightShadows:x.directionalShadowMap.length,numPointLightShadows:x.pointShadowMap.length,numSpotLightShadows:x.spotShadowMap.length,numSpotLightShadowsWithMaps:x.numSpotLightShadowsWithMaps,numLightProbes:x.numLightProbes,numLightProbeGrids:L.length,numClippingPlanes:s.numPlanes,numClipIntersection:s.numIntersection,dithering:b.dithering,shadowMapEnabled:n.shadowMap.enabled&&A.length>0,shadowMapType:n.shadowMap.type,toneMapping:ce,decodeVideoTexture:te&&b.map.isVideoTexture===!0&&ft.getTransfer(b.map.colorSpace)===bt,decodeVideoTextureEmissive:G&&b.emissiveMap.isVideoTexture===!0&&ft.getTransfer(b.emissiveMap.colorSpace)===bt,premultipliedAlpha:b.premultipliedAlpha,doubleSided:b.side===Rn,flipSided:b.side===an,useDepthPacking:b.depthPacking>=0,depthPacking:b.depthPacking||0,index0AttributeName:b.index0AttributeName,extensionClipCullDistance:Se&&b.extensions.clipCullDistance===!0&&t.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(Se&&b.extensions.multiDraw===!0||oe)&&t.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:t.has("KHR_parallel_shader_compile"),customProgramCacheKey:b.customProgramCacheKey()};return Ne.vertexUv1s=l.has(1),Ne.vertexUv2s=l.has(2),Ne.vertexUv3s=l.has(3),l.clear(),Ne}function p(b){const x=[];if(b.shaderID?x.push(b.shaderID):(x.push(b.customVertexShaderID),x.push(b.customFragmentShaderID)),b.defines!==void 0)for(const A in b.defines)x.push(A),x.push(b.defines[A]);return b.isRawShaderMaterial===!1&&(_(x,b),v(x,b),x.push(n.outputColorSpace)),x.push(b.customProgramCacheKey),x.join()}function _(b,x){b.push(x.precision),b.push(x.outputColorSpace),b.push(x.envMapMode),b.push(x.envMapCubeUVHeight),b.push(x.mapUv),b.push(x.alphaMapUv),b.push(x.lightMapUv),b.push(x.aoMapUv),b.push(x.bumpMapUv),b.push(x.normalMapUv),b.push(x.displacementMapUv),b.push(x.emissiveMapUv),b.push(x.metalnessMapUv),b.push(x.roughnessMapUv),b.push(x.anisotropyMapUv),b.push(x.clearcoatMapUv),b.push(x.clearcoatNormalMapUv),b.push(x.clearcoatRoughnessMapUv),b.push(x.iridescenceMapUv),b.push(x.iridescenceThicknessMapUv),b.push(x.sheenColorMapUv),b.push(x.sheenRoughnessMapUv),b.push(x.specularMapUv),b.push(x.specularColorMapUv),b.push(x.specularIntensityMapUv),b.push(x.transmissionMapUv),b.push(x.thicknessMapUv),b.push(x.combine),b.push(x.fogExp2),b.push(x.sizeAttenuation),b.push(x.morphTargetsCount),b.push(x.morphAttributeCount),b.push(x.numDirLights),b.push(x.numPointLights),b.push(x.numSpotLights),b.push(x.numSpotLightMaps),b.push(x.numHemiLights),b.push(x.numRectAreaLights),b.push(x.numDirLightShadows),b.push(x.numPointLightShadows),b.push(x.numSpotLightShadows),b.push(x.numSpotLightShadowsWithMaps),b.push(x.numLightProbes),b.push(x.shadowMapType),b.push(x.toneMapping),b.push(x.numClippingPlanes),b.push(x.numClipIntersection),b.push(x.depthPacking)}function v(b,x){a.disableAll(),x.instancing&&a.enable(0),x.instancingColor&&a.enable(1),x.instancingMorph&&a.enable(2),x.matcap&&a.enable(3),x.envMap&&a.enable(4),x.normalMapObjectSpace&&a.enable(5),x.normalMapTangentSpace&&a.enable(6),x.clearcoat&&a.enable(7),x.iridescence&&a.enable(8),x.alphaTest&&a.enable(9),x.vertexColors&&a.enable(10),x.vertexAlphas&&a.enable(11),x.vertexUv1s&&a.enable(12),x.vertexUv2s&&a.enable(13),x.vertexUv3s&&a.enable(14),x.vertexTangents&&a.enable(15),x.anisotropy&&a.enable(16),x.alphaHash&&a.enable(17),x.batching&&a.enable(18),x.dispersion&&a.enable(19),x.batchingColor&&a.enable(20),x.gradientMap&&a.enable(21),x.packedNormalMap&&a.enable(22),x.vertexNormals&&a.enable(23),b.push(a.mask),a.disableAll(),x.fog&&a.enable(0),x.useFog&&a.enable(1),x.flatShading&&a.enable(2),x.logarithmicDepthBuffer&&a.enable(3),x.reversedDepthBuffer&&a.enable(4),x.skinning&&a.enable(5),x.morphTargets&&a.enable(6),x.morphNormals&&a.enable(7),x.morphColors&&a.enable(8),x.premultipliedAlpha&&a.enable(9),x.shadowMapEnabled&&a.enable(10),x.doubleSided&&a.enable(11),x.flipSided&&a.enable(12),x.useDepthPacking&&a.enable(13),x.dithering&&a.enable(14),x.transmission&&a.enable(15),x.sheen&&a.enable(16),x.opaque&&a.enable(17),x.pointsUvs&&a.enable(18),x.decodeVideoTexture&&a.enable(19),x.decodeVideoTextureEmissive&&a.enable(20),x.alphaToCoverage&&a.enable(21),x.numLightProbeGrids>0&&a.enable(22),b.push(a.mask)}function S(b){const x=d[b.type];let A;if(x){const P=Mi[x];A=Km.clone(P.uniforms)}else A=b.uniforms;return A}function y(b,x){let A=u.get(x);return A!==void 0?++A.usedTimes:(A=new sS(n,x,b,r),c.push(A),u.set(x,A)),A}function M(b){if(--b.usedTimes===0){const x=c.indexOf(b);c[x]=c[c.length-1],c.pop(),u.delete(b.cacheKey),b.destroy()}}function T(b){o.remove(b)}function w(){o.dispose()}return{getParameters:g,getProgramCacheKey:p,getUniforms:S,acquireProgram:y,releaseProgram:M,releaseShaderCache:T,programs:c,dispose:w}}function hS(){let n=new WeakMap;function e(a){return n.has(a)}function t(a){let o=n.get(a);return o===void 0&&(o={},n.set(a,o)),o}function i(a){n.delete(a)}function r(a,o,l){n.get(a)[o]=l}function s(){n=new WeakMap}return{has:e,get:t,remove:i,update:r,dispose:s}}function fS(n,e){return n.groupOrder!==e.groupOrder?n.groupOrder-e.groupOrder:n.renderOrder!==e.renderOrder?n.renderOrder-e.renderOrder:n.material.id!==e.material.id?n.material.id-e.material.id:n.materialVariant!==e.materialVariant?n.materialVariant-e.materialVariant:n.z!==e.z?n.z-e.z:n.id-e.id}function rp(n,e){return n.groupOrder!==e.groupOrder?n.groupOrder-e.groupOrder:n.renderOrder!==e.renderOrder?n.renderOrder-e.renderOrder:n.z!==e.z?e.z-n.z:n.id-e.id}function sp(){const n=[];let e=0;const t=[],i=[],r=[];function s(){e=0,t.length=0,i.length=0,r.length=0}function a(h){let d=0;return h.isInstancedMesh&&(d+=2),h.isSkinnedMesh&&(d+=1),d}function o(h,d,m,g,p,_){let v=n[e];return v===void 0?(v={id:h.id,object:h,geometry:d,material:m,materialVariant:a(h),groupOrder:g,renderOrder:h.renderOrder,z:p,group:_},n[e]=v):(v.id=h.id,v.object=h,v.geometry=d,v.material=m,v.materialVariant=a(h),v.groupOrder=g,v.renderOrder=h.renderOrder,v.z=p,v.group=_),e++,v}function l(h,d,m,g,p,_){const v=o(h,d,m,g,p,_);m.transmission>0?i.push(v):m.transparent===!0?r.push(v):t.push(v)}function c(h,d,m,g,p,_){const v=o(h,d,m,g,p,_);m.transmission>0?i.unshift(v):m.transparent===!0?r.unshift(v):t.unshift(v)}function u(h,d){t.length>1&&t.sort(h||fS),i.length>1&&i.sort(d||rp),r.length>1&&r.sort(d||rp)}function f(){for(let h=e,d=n.length;h<d;h++){const m=n[h];if(m.id===null)break;m.id=null,m.object=null,m.geometry=null,m.material=null,m.group=null}}return{opaque:t,transmissive:i,transparent:r,init:s,push:l,unshift:c,finish:f,sort:u}}function dS(){let n=new WeakMap;function e(i,r){const s=n.get(i);let a;return s===void 0?(a=new sp,n.set(i,[a])):r>=s.length?(a=new sp,s.push(a)):a=s[r],a}function t(){n=new WeakMap}return{get:e,dispose:t}}function pS(){const n={};return{get:function(e){if(n[e.id]!==void 0)return n[e.id];let t;switch(e.type){case"DirectionalLight":t={direction:new $,color:new ut};break;case"SpotLight":t={position:new $,direction:new $,color:new ut,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new $,color:new ut,distance:0,decay:0};break;case"HemisphereLight":t={direction:new $,skyColor:new ut,groundColor:new ut};break;case"RectAreaLight":t={color:new ut,position:new $,halfWidth:new $,halfHeight:new $};break}return n[e.id]=t,t}}}function mS(){const n={};return{get:function(e){if(n[e.id]!==void 0)return n[e.id];let t;switch(e.type){case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe,shadowCameraNear:1,shadowCameraFar:1e3};break}return n[e.id]=t,t}}}let gS=0;function _S(n,e){return(e.castShadow?2:0)-(n.castShadow?2:0)+(e.map?1:0)-(n.map?1:0)}function vS(n){const e=new pS,t=mS(),i={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)i.probe.push(new $);const r=new $,s=new zt,a=new zt;function o(c){let u=0,f=0,h=0;for(let x=0;x<9;x++)i.probe[x].set(0,0,0);let d=0,m=0,g=0,p=0,_=0,v=0,S=0,y=0,M=0,T=0,w=0;c.sort(_S);for(let x=0,A=c.length;x<A;x++){const P=c[x],R=P.color,L=P.intensity,I=P.distance;let N=null;if(P.shadow&&P.shadow.map&&(P.shadow.map.texture.format===$r?N=P.shadow.map.texture:N=P.shadow.map.depthTexture||P.shadow.map.texture),P.isAmbientLight)u+=R.r*L,f+=R.g*L,h+=R.b*L;else if(P.isLightProbe){for(let O=0;O<9;O++)i.probe[O].addScaledVector(P.sh.coefficients[O],L);w++}else if(P.isDirectionalLight){const O=e.get(P);if(O.color.copy(P.color).multiplyScalar(P.intensity),P.castShadow){const B=P.shadow,q=t.get(P);q.shadowIntensity=B.intensity,q.shadowBias=B.bias,q.shadowNormalBias=B.normalBias,q.shadowRadius=B.radius,q.shadowMapSize=B.mapSize,i.directionalShadow[d]=q,i.directionalShadowMap[d]=N,i.directionalShadowMatrix[d]=P.shadow.matrix,v++}i.directional[d]=O,d++}else if(P.isSpotLight){const O=e.get(P);O.position.setFromMatrixPosition(P.matrixWorld),O.color.copy(R).multiplyScalar(L),O.distance=I,O.coneCos=Math.cos(P.angle),O.penumbraCos=Math.cos(P.angle*(1-P.penumbra)),O.decay=P.decay,i.spot[g]=O;const B=P.shadow;if(P.map&&(i.spotLightMap[M]=P.map,M++,B.updateMatrices(P),P.castShadow&&T++),i.spotLightMatrix[g]=B.matrix,P.castShadow){const q=t.get(P);q.shadowIntensity=B.intensity,q.shadowBias=B.bias,q.shadowNormalBias=B.normalBias,q.shadowRadius=B.radius,q.shadowMapSize=B.mapSize,i.spotShadow[g]=q,i.spotShadowMap[g]=N,y++}g++}else if(P.isRectAreaLight){const O=e.get(P);O.color.copy(R).multiplyScalar(L),O.halfWidth.set(P.width*.5,0,0),O.halfHeight.set(0,P.height*.5,0),i.rectArea[p]=O,p++}else if(P.isPointLight){const O=e.get(P);if(O.color.copy(P.color).multiplyScalar(P.intensity),O.distance=P.distance,O.decay=P.decay,P.castShadow){const B=P.shadow,q=t.get(P);q.shadowIntensity=B.intensity,q.shadowBias=B.bias,q.shadowNormalBias=B.normalBias,q.shadowRadius=B.radius,q.shadowMapSize=B.mapSize,q.shadowCameraNear=B.camera.near,q.shadowCameraFar=B.camera.far,i.pointShadow[m]=q,i.pointShadowMap[m]=N,i.pointShadowMatrix[m]=P.shadow.matrix,S++}i.point[m]=O,m++}else if(P.isHemisphereLight){const O=e.get(P);O.skyColor.copy(P.color).multiplyScalar(L),O.groundColor.copy(P.groundColor).multiplyScalar(L),i.hemi[_]=O,_++}}p>0&&(n.has("OES_texture_float_linear")===!0?(i.rectAreaLTC1=Ge.LTC_FLOAT_1,i.rectAreaLTC2=Ge.LTC_FLOAT_2):(i.rectAreaLTC1=Ge.LTC_HALF_1,i.rectAreaLTC2=Ge.LTC_HALF_2)),i.ambient[0]=u,i.ambient[1]=f,i.ambient[2]=h;const b=i.hash;(b.directionalLength!==d||b.pointLength!==m||b.spotLength!==g||b.rectAreaLength!==p||b.hemiLength!==_||b.numDirectionalShadows!==v||b.numPointShadows!==S||b.numSpotShadows!==y||b.numSpotMaps!==M||b.numLightProbes!==w)&&(i.directional.length=d,i.spot.length=g,i.rectArea.length=p,i.point.length=m,i.hemi.length=_,i.directionalShadow.length=v,i.directionalShadowMap.length=v,i.pointShadow.length=S,i.pointShadowMap.length=S,i.spotShadow.length=y,i.spotShadowMap.length=y,i.directionalShadowMatrix.length=v,i.pointShadowMatrix.length=S,i.spotLightMatrix.length=y+M-T,i.spotLightMap.length=M,i.numSpotLightShadowsWithMaps=T,i.numLightProbes=w,b.directionalLength=d,b.pointLength=m,b.spotLength=g,b.rectAreaLength=p,b.hemiLength=_,b.numDirectionalShadows=v,b.numPointShadows=S,b.numSpotShadows=y,b.numSpotMaps=M,b.numLightProbes=w,i.version=gS++)}function l(c,u){let f=0,h=0,d=0,m=0,g=0;const p=u.matrixWorldInverse;for(let _=0,v=c.length;_<v;_++){const S=c[_];if(S.isDirectionalLight){const y=i.directional[f];y.direction.setFromMatrixPosition(S.matrixWorld),r.setFromMatrixPosition(S.target.matrixWorld),y.direction.sub(r),y.direction.transformDirection(p),f++}else if(S.isSpotLight){const y=i.spot[d];y.position.setFromMatrixPosition(S.matrixWorld),y.position.applyMatrix4(p),y.direction.setFromMatrixPosition(S.matrixWorld),r.setFromMatrixPosition(S.target.matrixWorld),y.direction.sub(r),y.direction.transformDirection(p),d++}else if(S.isRectAreaLight){const y=i.rectArea[m];y.position.setFromMatrixPosition(S.matrixWorld),y.position.applyMatrix4(p),a.identity(),s.copy(S.matrixWorld),s.premultiply(p),a.extractRotation(s),y.halfWidth.set(S.width*.5,0,0),y.halfHeight.set(0,S.height*.5,0),y.halfWidth.applyMatrix4(a),y.halfHeight.applyMatrix4(a),m++}else if(S.isPointLight){const y=i.point[h];y.position.setFromMatrixPosition(S.matrixWorld),y.position.applyMatrix4(p),h++}else if(S.isHemisphereLight){const y=i.hemi[g];y.direction.setFromMatrixPosition(S.matrixWorld),y.direction.transformDirection(p),g++}}}return{setup:o,setupView:l,state:i}}function ap(n){const e=new vS(n),t=[],i=[],r=[];function s(h){f.camera=h,t.length=0,i.length=0,r.length=0}function a(h){t.push(h)}function o(h){i.push(h)}function l(h){r.push(h)}function c(){e.setup(t)}function u(h){e.setupView(t,h)}const f={lightsArray:t,shadowsArray:i,lightProbeGridArray:r,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:s,state:f,setupLights:c,setupLightsView:u,pushLight:a,pushShadow:o,pushLightProbeGrid:l}}function xS(n){let e=new WeakMap;function t(r,s=0){const a=e.get(r);let o;return a===void 0?(o=new ap(n),e.set(r,[o])):s>=a.length?(o=new ap(n),a.push(o)):o=a[s],o}function i(){e=new WeakMap}return{get:t,dispose:i}}const yS=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,bS=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ).rg;
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ).r;
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( max( 0.0, squared_mean - mean * mean ) );
	gl_FragColor = vec4( mean, std_dev, 0.0, 1.0 );
}`,SS=[new $(1,0,0),new $(-1,0,0),new $(0,1,0),new $(0,-1,0),new $(0,0,1),new $(0,0,-1)],MS=[new $(0,-1,0),new $(0,-1,0),new $(0,0,1),new $(0,0,-1),new $(0,-1,0),new $(0,-1,0)],op=new zt,ba=new $,kc=new $;function TS(n,e,t){let i=new Xm;const r=new Xe,s=new Xe,a=new Ut,o=new Zm,l=new $m,c={},u=t.maxTextureSize,f={[ji]:an,[an]:ji,[Rn]:Rn},h=new on({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Xe},radius:{value:4}},vertexShader:yS,fragmentShader:bS}),d=h.clone();d.defines.HORIZONTAL_PASS=1;const m=new Dt;m.setAttribute("position",new Nt(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const g=new jn(m,h),p=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Yo;let _=this.type;this.render=function(T,w,b){if(p.enabled===!1||p.autoUpdate===!1&&p.needsUpdate===!1||T.length===0)return;this.type===M_&&(Je("WebGLShadowMap: PCFSoftShadowMap has been deprecated. Using PCFShadowMap instead."),this.type=Yo);const x=n.getRenderTarget(),A=n.getActiveCubeFace(),P=n.getActiveMipmapLevel(),R=n.state;R.setBlending(Tn),R.buffers.depth.getReversed()===!0?R.buffers.color.setClear(0,0,0,0):R.buffers.color.setClear(1,1,1,1),R.buffers.depth.setTest(!0),R.setScissorTest(!1);const L=_!==this.type;L&&w.traverse(function(I){I.material&&(Array.isArray(I.material)?I.material.forEach(N=>N.needsUpdate=!0):I.material.needsUpdate=!0)});for(let I=0,N=T.length;I<N;I++){const O=T[I],B=O.shadow;if(B===void 0){Je("WebGLShadowMap:",O,"has no shadow.");continue}if(B.autoUpdate===!1&&B.needsUpdate===!1)continue;r.copy(B.mapSize);const q=B.getFrameExtents();r.multiply(q),s.copy(B.mapSize),(r.x>u||r.y>u)&&(r.x>u&&(s.x=Math.floor(u/q.x),r.x=s.x*q.x,B.mapSize.x=s.x),r.y>u&&(s.y=Math.floor(u/q.y),r.y=s.y*q.y,B.mapSize.y=s.y));const F=n.state.buffers.depth.getReversed();if(B.camera._reversedDepth=F,B.map===null||L===!0){if(B.map!==null&&(B.map.depthTexture!==null&&(B.map.depthTexture.dispose(),B.map.depthTexture=null),B.map.dispose()),this.type===wa){if(O.isPointLight){Je("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}B.map=new Jt(r.x,r.y,{format:$r,type:Yi,minFilter:Gt,magFilter:Gt,generateMipmaps:!1}),B.map.texture.name=O.name+".shadowMap",B.map.depthTexture=new Xi(r.x,r.y,hi),B.map.depthTexture.name=O.name+".shadowMapDepth",B.map.depthTexture.format=qi,B.map.depthTexture.compareFunction=null,B.map.depthTexture.minFilter=un,B.map.depthTexture.magFilter=un}else O.isPointLight?(B.map=new t0(r.x),B.map.depthTexture=new Uv(r.x,Ui)):(B.map=new Jt(r.x,r.y),B.map.depthTexture=new Xi(r.x,r.y,Ui)),B.map.depthTexture.name=O.name+".shadowMap",B.map.depthTexture.format=qi,this.type===Yo?(B.map.depthTexture.compareFunction=F?Qh:Jh,B.map.depthTexture.minFilter=Gt,B.map.depthTexture.magFilter=Gt):(B.map.depthTexture.compareFunction=null,B.map.depthTexture.minFilter=un,B.map.depthTexture.magFilter=un);B.camera.updateProjectionMatrix()}const k=B.map.isWebGLCubeRenderTarget?6:1;for(let U=0;U<k;U++){if(B.map.isWebGLCubeRenderTarget)n.setRenderTarget(B.map,U),n.clear();else{U===0&&(n.setRenderTarget(B.map),n.clear());const z=B.getViewport(U);a.set(s.x*z.x,s.y*z.y,s.x*z.z,s.y*z.w),R.viewport(a)}if(O.isPointLight){const z=B.camera,K=B.matrix,Z=O.distance||z.far;Z!==z.far&&(z.far=Z,z.updateProjectionMatrix()),ba.setFromMatrixPosition(O.matrixWorld),z.position.copy(ba),kc.copy(z.position),kc.add(SS[U]),z.up.copy(MS[U]),z.lookAt(kc),z.updateMatrixWorld(),K.makeTranslation(-ba.x,-ba.y,-ba.z),op.multiplyMatrices(z.projectionMatrix,z.matrixWorldInverse),B._frustum.setFromProjectionMatrix(op,z.coordinateSystem,z.reversedDepth)}else B.updateMatrices(O);i=B.getFrustum(),y(w,b,B.camera,O,this.type)}B.isPointLightShadow!==!0&&this.type===wa&&v(B,b),B.needsUpdate=!1}_=this.type,p.needsUpdate=!1,n.setRenderTarget(x,A,P)};function v(T,w){const b=e.update(g);h.defines.VSM_SAMPLES!==T.blurSamples&&(h.defines.VSM_SAMPLES=T.blurSamples,d.defines.VSM_SAMPLES=T.blurSamples,h.needsUpdate=!0,d.needsUpdate=!0),T.mapPass===null&&(T.mapPass=new Jt(r.x,r.y,{format:$r,type:Yi})),h.uniforms.shadow_pass.value=T.map.depthTexture,h.uniforms.resolution.value=T.mapSize,h.uniforms.radius.value=T.radius,n.setRenderTarget(T.mapPass),n.clear(),n.renderBufferDirect(w,null,b,h,g,null),d.uniforms.shadow_pass.value=T.mapPass.texture,d.uniforms.resolution.value=T.mapSize,d.uniforms.radius.value=T.radius,n.setRenderTarget(T.map),n.clear(),n.renderBufferDirect(w,null,b,d,g,null)}function S(T,w,b,x){let A=null;const P=b.isPointLight===!0?T.customDistanceMaterial:T.customDepthMaterial;if(P!==void 0)A=P;else if(A=b.isPointLight===!0?l:o,n.localClippingEnabled&&w.clipShadows===!0&&Array.isArray(w.clippingPlanes)&&w.clippingPlanes.length!==0||w.displacementMap&&w.displacementScale!==0||w.alphaMap&&w.alphaTest>0||w.map&&w.alphaTest>0||w.alphaToCoverage===!0){const R=A.uuid,L=w.uuid;let I=c[R];I===void 0&&(I={},c[R]=I);let N=I[L];N===void 0&&(N=A.clone(),I[L]=N,w.addEventListener("dispose",M)),A=N}if(A.visible=w.visible,A.wireframe=w.wireframe,x===wa?A.side=w.shadowSide!==null?w.shadowSide:w.side:A.side=w.shadowSide!==null?w.shadowSide:f[w.side],A.alphaMap=w.alphaMap,A.alphaTest=w.alphaToCoverage===!0?.5:w.alphaTest,A.map=w.map,A.clipShadows=w.clipShadows,A.clippingPlanes=w.clippingPlanes,A.clipIntersection=w.clipIntersection,A.displacementMap=w.displacementMap,A.displacementScale=w.displacementScale,A.displacementBias=w.displacementBias,A.wireframeLinewidth=w.wireframeLinewidth,A.linewidth=w.linewidth,b.isPointLight===!0&&A.isMeshDistanceMaterial===!0){const R=n.properties.get(A);R.light=b}return A}function y(T,w,b,x,A){if(T.visible===!1)return;if(T.layers.test(w.layers)&&(T.isMesh||T.isLine||T.isPoints)&&(T.castShadow||T.receiveShadow&&A===wa)&&(!T.frustumCulled||i.intersectsObject(T))){T.modelViewMatrix.multiplyMatrices(b.matrixWorldInverse,T.matrixWorld);const L=e.update(T),I=T.material;if(Array.isArray(I)){const N=L.groups;for(let O=0,B=N.length;O<B;O++){const q=N[O],F=I[q.materialIndex];if(F&&F.visible){const k=S(T,F,x,A);T.onBeforeShadow(n,T,w,b,L,k,q),n.renderBufferDirect(b,null,L,k,T,q),T.onAfterShadow(n,T,w,b,L,k,q)}}}else if(I.visible){const N=S(T,I,x,A);T.onBeforeShadow(n,T,w,b,L,N,null),n.renderBufferDirect(b,null,L,N,T,null),T.onAfterShadow(n,T,w,b,L,N,null)}}const R=T.children;for(let L=0,I=R.length;L<I;L++)y(R[L],w,b,x,A)}function M(T){T.target.removeEventListener("dispose",M);for(const b in c){const x=c[b],A=T.target.uuid;A in x&&(x[A].dispose(),delete x[A])}}}function ES(n,e){function t(){let Y=!1;const _e=new Ut;let re=null;const Pe=new Ut(0,0,0,0);return{setMask:function(Se){re!==Se&&!Y&&(n.colorMask(Se,Se,Se,Se),re=Se)},setLocked:function(Se){Y=Se},setClear:function(Se,ce,Ne,Ze,ot){ot===!0&&(Se*=Ze,ce*=Ze,Ne*=Ze),_e.set(Se,ce,Ne,Ze),Pe.equals(_e)===!1&&(n.clearColor(Se,ce,Ne,Ze),Pe.copy(_e))},reset:function(){Y=!1,re=null,Pe.set(-1,0,0,0)}}}function i(){let Y=!1,_e=!1,re=null,Pe=null,Se=null;return{setReversed:function(ce){if(_e!==ce){const Ne=e.get("EXT_clip_control");ce?Ne.clipControlEXT(Ne.LOWER_LEFT_EXT,Ne.ZERO_TO_ONE_EXT):Ne.clipControlEXT(Ne.LOWER_LEFT_EXT,Ne.NEGATIVE_ONE_TO_ONE_EXT),_e=ce;const Ze=Se;Se=null,this.setClear(Ze)}},getReversed:function(){return _e},setTest:function(ce){ce?j(n.DEPTH_TEST):le(n.DEPTH_TEST)},setMask:function(ce){re!==ce&&!Y&&(n.depthMask(ce),re=ce)},setFunc:function(ce){if(_e&&(ce=nv[ce]),Pe!==ce){switch(ce){case Au:n.depthFunc(n.NEVER);break;case ll:n.depthFunc(n.ALWAYS);break;case Ru:n.depthFunc(n.LESS);break;case Bs:n.depthFunc(n.LEQUAL);break;case Cu:n.depthFunc(n.EQUAL);break;case Pu:n.depthFunc(n.GEQUAL);break;case Du:n.depthFunc(n.GREATER);break;case Uu:n.depthFunc(n.NOTEQUAL);break;default:n.depthFunc(n.LEQUAL)}Pe=ce}},setLocked:function(ce){Y=ce},setClear:function(ce){Se!==ce&&(Se=ce,_e&&(ce=1-ce),n.clearDepth(ce))},reset:function(){Y=!1,re=null,Pe=null,Se=null,_e=!1}}}function r(){let Y=!1,_e=null,re=null,Pe=null,Se=null,ce=null,Ne=null,Ze=null,ot=null;return{setTest:function(et){Y||(et?j(n.STENCIL_TEST):le(n.STENCIL_TEST))},setMask:function(et){_e!==et&&!Y&&(n.stencilMask(et),_e=et)},setFunc:function(et,Vt,Kt){(re!==et||Pe!==Vt||Se!==Kt)&&(n.stencilFunc(et,Vt,Kt),re=et,Pe=Vt,Se=Kt)},setOp:function(et,Vt,Kt){(ce!==et||Ne!==Vt||Ze!==Kt)&&(n.stencilOp(et,Vt,Kt),ce=et,Ne=Vt,Ze=Kt)},setLocked:function(et){Y=et},setClear:function(et){ot!==et&&(n.clearStencil(et),ot=et)},reset:function(){Y=!1,_e=null,re=null,Pe=null,Se=null,ce=null,Ne=null,Ze=null,ot=null}}}const s=new t,a=new i,o=new r,l=new WeakMap,c=new WeakMap;let u={},f={},h={},d=new WeakMap,m=[],g=null,p=!1,_=null,v=null,S=null,y=null,M=null,T=null,w=null,b=new ut(0,0,0),x=0,A=!1,P=null,R=null,L=null,I=null,N=null;const O=n.getParameter(n.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let B=!1,q=0;const F=n.getParameter(n.VERSION);F.indexOf("WebGL")!==-1?(q=parseFloat(/^WebGL (\d)/.exec(F)[1]),B=q>=1):F.indexOf("OpenGL ES")!==-1&&(q=parseFloat(/^OpenGL ES (\d)/.exec(F)[1]),B=q>=2);let k=null,U={};const z=n.getParameter(n.SCISSOR_BOX),K=n.getParameter(n.VIEWPORT),Z=new Ut().fromArray(z),X=new Ut().fromArray(K);function H(Y,_e,re,Pe){const Se=new Uint8Array(4),ce=n.createTexture();n.bindTexture(Y,ce),n.texParameteri(Y,n.TEXTURE_MIN_FILTER,n.NEAREST),n.texParameteri(Y,n.TEXTURE_MAG_FILTER,n.NEAREST);for(let Ne=0;Ne<re;Ne++)Y===n.TEXTURE_3D||Y===n.TEXTURE_2D_ARRAY?n.texImage3D(_e,0,n.RGBA,1,1,Pe,0,n.RGBA,n.UNSIGNED_BYTE,Se):n.texImage2D(_e+Ne,0,n.RGBA,1,1,0,n.RGBA,n.UNSIGNED_BYTE,Se);return ce}const V={};V[n.TEXTURE_2D]=H(n.TEXTURE_2D,n.TEXTURE_2D,1),V[n.TEXTURE_CUBE_MAP]=H(n.TEXTURE_CUBE_MAP,n.TEXTURE_CUBE_MAP_POSITIVE_X,6),V[n.TEXTURE_2D_ARRAY]=H(n.TEXTURE_2D_ARRAY,n.TEXTURE_2D_ARRAY,1,1),V[n.TEXTURE_3D]=H(n.TEXTURE_3D,n.TEXTURE_3D,1,1),s.setClear(0,0,0,1),a.setClear(1),o.setClear(0),j(n.DEPTH_TEST),a.setFunc(Bs),Ue(!1),me(id),j(n.CULL_FACE),Te(Tn);function j(Y){u[Y]!==!0&&(n.enable(Y),u[Y]=!0)}function le(Y){u[Y]!==!1&&(n.disable(Y),u[Y]=!1)}function ge(Y,_e){return h[Y]!==_e?(n.bindFramebuffer(Y,_e),h[Y]=_e,Y===n.DRAW_FRAMEBUFFER&&(h[n.FRAMEBUFFER]=_e),Y===n.FRAMEBUFFER&&(h[n.DRAW_FRAMEBUFFER]=_e),!0):!1}function oe(Y,_e){let re=m,Pe=!1;if(Y){re=d.get(_e),re===void 0&&(re=[],d.set(_e,re));const Se=Y.textures;if(re.length!==Se.length||re[0]!==n.COLOR_ATTACHMENT0){for(let ce=0,Ne=Se.length;ce<Ne;ce++)re[ce]=n.COLOR_ATTACHMENT0+ce;re.length=Se.length,Pe=!0}}else re[0]!==n.BACK&&(re[0]=n.BACK,Pe=!0);Pe&&n.drawBuffers(re)}function te(Y){return g!==Y?(n.useProgram(Y),g=Y,!0):!1}const xe={[Br]:n.FUNC_ADD,[E_]:n.FUNC_SUBTRACT,[w_]:n.FUNC_REVERSE_SUBTRACT};xe[A_]=n.MIN,xe[R_]=n.MAX;const Ae={[C_]:n.ZERO,[P_]:n.ONE,[D_]:n.SRC_COLOR,[Eu]:n.SRC_ALPHA,[O_]:n.SRC_ALPHA_SATURATE,[F_]:n.DST_COLOR,[L_]:n.DST_ALPHA,[U_]:n.ONE_MINUS_SRC_COLOR,[wu]:n.ONE_MINUS_SRC_ALPHA,[N_]:n.ONE_MINUS_DST_COLOR,[I_]:n.ONE_MINUS_DST_ALPHA,[B_]:n.CONSTANT_COLOR,[k_]:n.ONE_MINUS_CONSTANT_COLOR,[z_]:n.CONSTANT_ALPHA,[G_]:n.ONE_MINUS_CONSTANT_ALPHA};function Te(Y,_e,re,Pe,Se,ce,Ne,Ze,ot,et){if(Y===Tn){p===!0&&(le(n.BLEND),p=!1);return}if(p===!1&&(j(n.BLEND),p=!0),Y!==T_){if(Y!==_||et!==A){if((v!==Br||M!==Br)&&(n.blendEquation(n.FUNC_ADD),v=Br,M=Br),et)switch(Y){case Hr:n.blendFuncSeparate(n.ONE,n.ONE_MINUS_SRC_ALPHA,n.ONE,n.ONE_MINUS_SRC_ALPHA);break;case ol:n.blendFunc(n.ONE,n.ONE);break;case rd:n.blendFuncSeparate(n.ZERO,n.ONE_MINUS_SRC_COLOR,n.ZERO,n.ONE);break;case sd:n.blendFuncSeparate(n.DST_COLOR,n.ONE_MINUS_SRC_ALPHA,n.ZERO,n.ONE);break;default:pt("WebGLState: Invalid blending: ",Y);break}else switch(Y){case Hr:n.blendFuncSeparate(n.SRC_ALPHA,n.ONE_MINUS_SRC_ALPHA,n.ONE,n.ONE_MINUS_SRC_ALPHA);break;case ol:n.blendFuncSeparate(n.SRC_ALPHA,n.ONE,n.ONE,n.ONE);break;case rd:pt("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case sd:pt("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:pt("WebGLState: Invalid blending: ",Y);break}S=null,y=null,T=null,w=null,b.set(0,0,0),x=0,_=Y,A=et}return}Se=Se||_e,ce=ce||re,Ne=Ne||Pe,(_e!==v||Se!==M)&&(n.blendEquationSeparate(xe[_e],xe[Se]),v=_e,M=Se),(re!==S||Pe!==y||ce!==T||Ne!==w)&&(n.blendFuncSeparate(Ae[re],Ae[Pe],Ae[ce],Ae[Ne]),S=re,y=Pe,T=ce,w=Ne),(Ze.equals(b)===!1||ot!==x)&&(n.blendColor(Ze.r,Ze.g,Ze.b,ot),b.copy(Ze),x=ot),_=Y,A=!1}function ye(Y,_e){Y.side===Rn?le(n.CULL_FACE):j(n.CULL_FACE);let re=Y.side===an;_e&&(re=!re),Ue(re),Y.blending===Hr&&Y.transparent===!1?Te(Tn):Te(Y.blending,Y.blendEquation,Y.blendSrc,Y.blendDst,Y.blendEquationAlpha,Y.blendSrcAlpha,Y.blendDstAlpha,Y.blendColor,Y.blendAlpha,Y.premultipliedAlpha),a.setFunc(Y.depthFunc),a.setTest(Y.depthTest),a.setMask(Y.depthWrite),s.setMask(Y.colorWrite);const Pe=Y.stencilWrite;o.setTest(Pe),Pe&&(o.setMask(Y.stencilWriteMask),o.setFunc(Y.stencilFunc,Y.stencilRef,Y.stencilFuncMask),o.setOp(Y.stencilFail,Y.stencilZFail,Y.stencilZPass)),G(Y.polygonOffset,Y.polygonOffsetFactor,Y.polygonOffsetUnits),Y.alphaToCoverage===!0?j(n.SAMPLE_ALPHA_TO_COVERAGE):le(n.SAMPLE_ALPHA_TO_COVERAGE)}function Ue(Y){P!==Y&&(Y?n.frontFace(n.CW):n.frontFace(n.CCW),P=Y)}function me(Y){Y!==b_?(j(n.CULL_FACE),Y!==R&&(Y===id?n.cullFace(n.BACK):Y===S_?n.cullFace(n.FRONT):n.cullFace(n.FRONT_AND_BACK))):le(n.CULL_FACE),R=Y}function ke(Y){Y!==L&&(B&&n.lineWidth(Y),L=Y)}function G(Y,_e,re){Y?(j(n.POLYGON_OFFSET_FILL),(I!==_e||N!==re)&&(I=_e,N=re,a.getReversed()&&(_e=-_e),n.polygonOffset(_e,re))):le(n.POLYGON_OFFSET_FILL)}function fe(Y){Y?j(n.SCISSOR_TEST):le(n.SCISSOR_TEST)}function Fe(Y){Y===void 0&&(Y=n.TEXTURE0+O-1),k!==Y&&(n.activeTexture(Y),k=Y)}function we(Y,_e,re){re===void 0&&(k===null?re=n.TEXTURE0+O-1:re=k);let Pe=U[re];Pe===void 0&&(Pe={type:void 0,texture:void 0},U[re]=Pe),(Pe.type!==Y||Pe.texture!==_e)&&(k!==re&&(n.activeTexture(re),k=re),n.bindTexture(Y,_e||V[Y]),Pe.type=Y,Pe.texture=_e)}function he(){const Y=U[k];Y!==void 0&&Y.type!==void 0&&(n.bindTexture(Y.type,null),Y.type=void 0,Y.texture=void 0)}function Re(){try{n.compressedTexImage2D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function D(){try{n.compressedTexImage3D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function E(){try{n.texSubImage2D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function W(){try{n.texSubImage3D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function Q(){try{n.compressedTexSubImage2D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function ue(){try{n.compressedTexSubImage3D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function ve(){try{n.texStorage2D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function Me(){try{n.texStorage3D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function ee(){try{n.texImage2D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function se(){try{n.texImage3D(...arguments)}catch(Y){pt("WebGLState:",Y)}}function de(Y){return f[Y]!==void 0?f[Y]:n.getParameter(Y)}function De(Y,_e){f[Y]!==_e&&(n.pixelStorei(Y,_e),f[Y]=_e)}function be(Y){Z.equals(Y)===!1&&(n.scissor(Y.x,Y.y,Y.z,Y.w),Z.copy(Y))}function Ee(Y){X.equals(Y)===!1&&(n.viewport(Y.x,Y.y,Y.z,Y.w),X.copy(Y))}function He(Y,_e){let re=c.get(_e);re===void 0&&(re=new WeakMap,c.set(_e,re));let Pe=re.get(Y);Pe===void 0&&(Pe=n.getUniformBlockIndex(_e,Y.name),re.set(Y,Pe))}function Le(Y,_e){const Pe=c.get(_e).get(Y);l.get(_e)!==Pe&&(n.uniformBlockBinding(_e,Pe,Y.__bindingPointIndex),l.set(_e,Pe))}function Ye(){n.disable(n.BLEND),n.disable(n.CULL_FACE),n.disable(n.DEPTH_TEST),n.disable(n.POLYGON_OFFSET_FILL),n.disable(n.SCISSOR_TEST),n.disable(n.STENCIL_TEST),n.disable(n.SAMPLE_ALPHA_TO_COVERAGE),n.blendEquation(n.FUNC_ADD),n.blendFunc(n.ONE,n.ZERO),n.blendFuncSeparate(n.ONE,n.ZERO,n.ONE,n.ZERO),n.blendColor(0,0,0,0),n.colorMask(!0,!0,!0,!0),n.clearColor(0,0,0,0),n.depthMask(!0),n.depthFunc(n.LESS),a.setReversed(!1),n.clearDepth(1),n.stencilMask(4294967295),n.stencilFunc(n.ALWAYS,0,4294967295),n.stencilOp(n.KEEP,n.KEEP,n.KEEP),n.clearStencil(0),n.cullFace(n.BACK),n.frontFace(n.CCW),n.polygonOffset(0,0),n.activeTexture(n.TEXTURE0),n.bindFramebuffer(n.FRAMEBUFFER,null),n.bindFramebuffer(n.DRAW_FRAMEBUFFER,null),n.bindFramebuffer(n.READ_FRAMEBUFFER,null),n.useProgram(null),n.lineWidth(1),n.scissor(0,0,n.canvas.width,n.canvas.height),n.viewport(0,0,n.canvas.width,n.canvas.height),n.pixelStorei(n.PACK_ALIGNMENT,4),n.pixelStorei(n.UNPACK_ALIGNMENT,4),n.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,!1),n.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),n.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,n.BROWSER_DEFAULT_WEBGL),n.pixelStorei(n.PACK_ROW_LENGTH,0),n.pixelStorei(n.PACK_SKIP_PIXELS,0),n.pixelStorei(n.PACK_SKIP_ROWS,0),n.pixelStorei(n.UNPACK_ROW_LENGTH,0),n.pixelStorei(n.UNPACK_IMAGE_HEIGHT,0),n.pixelStorei(n.UNPACK_SKIP_PIXELS,0),n.pixelStorei(n.UNPACK_SKIP_ROWS,0),n.pixelStorei(n.UNPACK_SKIP_IMAGES,0),u={},f={},k=null,U={},h={},d=new WeakMap,m=[],g=null,p=!1,_=null,v=null,S=null,y=null,M=null,T=null,w=null,b=new ut(0,0,0),x=0,A=!1,P=null,R=null,L=null,I=null,N=null,Z.set(0,0,n.canvas.width,n.canvas.height),X.set(0,0,n.canvas.width,n.canvas.height),s.reset(),a.reset(),o.reset()}return{buffers:{color:s,depth:a,stencil:o},enable:j,disable:le,bindFramebuffer:ge,drawBuffers:oe,useProgram:te,setBlending:Te,setMaterial:ye,setFlipSided:Ue,setCullFace:me,setLineWidth:ke,setPolygonOffset:G,setScissorTest:fe,activeTexture:Fe,bindTexture:we,unbindTexture:he,compressedTexImage2D:Re,compressedTexImage3D:D,texImage2D:ee,texImage3D:se,pixelStorei:De,getParameter:de,updateUBOMapping:He,uniformBlockBinding:Le,texStorage2D:ve,texStorage3D:Me,texSubImage2D:E,texSubImage3D:W,compressedTexSubImage2D:Q,compressedTexSubImage3D:ue,scissor:be,viewport:Ee,reset:Ye}}function wS(n,e,t,i,r,s,a){const o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new Xe,u=new WeakMap,f=new Set;let h;const d=new WeakMap;let m=!1;try{m=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function g(D,E){return m?new OffscreenCanvas(D,E):dl("canvas")}function p(D,E,W){let Q=1;const ue=Re(D);if((ue.width>W||ue.height>W)&&(Q=W/Math.max(ue.width,ue.height)),Q<1)if(typeof HTMLImageElement<"u"&&D instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&D instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&D instanceof ImageBitmap||typeof VideoFrame<"u"&&D instanceof VideoFrame){const ve=Math.floor(Q*ue.width),Me=Math.floor(Q*ue.height);h===void 0&&(h=g(ve,Me));const ee=E?g(ve,Me):h;return ee.width=ve,ee.height=Me,ee.getContext("2d").drawImage(D,0,0,ve,Me),Je("WebGLRenderer: Texture has been resized from ("+ue.width+"x"+ue.height+") to ("+ve+"x"+Me+")."),ee}else return"data"in D&&Je("WebGLRenderer: Image in DataTexture is too big ("+ue.width+"x"+ue.height+")."),D;return D}function _(D){return D.generateMipmaps}function v(D){n.generateMipmap(D)}function S(D){return D.isWebGLCubeRenderTarget?n.TEXTURE_CUBE_MAP:D.isWebGL3DRenderTarget?n.TEXTURE_3D:D.isWebGLArrayRenderTarget||D.isCompressedArrayTexture?n.TEXTURE_2D_ARRAY:n.TEXTURE_2D}function y(D,E,W,Q,ue,ve=!1){if(D!==null){if(n[D]!==void 0)return n[D];Je("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+D+"'")}let Me;Q&&(Me=e.get("EXT_texture_norm16"),Me||Je("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let ee=E;if(E===n.RED&&(W===n.FLOAT&&(ee=n.R32F),W===n.HALF_FLOAT&&(ee=n.R16F),W===n.UNSIGNED_BYTE&&(ee=n.R8),W===n.UNSIGNED_SHORT&&Me&&(ee=Me.R16_EXT),W===n.SHORT&&Me&&(ee=Me.R16_SNORM_EXT)),E===n.RED_INTEGER&&(W===n.UNSIGNED_BYTE&&(ee=n.R8UI),W===n.UNSIGNED_SHORT&&(ee=n.R16UI),W===n.UNSIGNED_INT&&(ee=n.R32UI),W===n.BYTE&&(ee=n.R8I),W===n.SHORT&&(ee=n.R16I),W===n.INT&&(ee=n.R32I)),E===n.RG&&(W===n.FLOAT&&(ee=n.RG32F),W===n.HALF_FLOAT&&(ee=n.RG16F),W===n.UNSIGNED_BYTE&&(ee=n.RG8),W===n.UNSIGNED_SHORT&&Me&&(ee=Me.RG16_EXT),W===n.SHORT&&Me&&(ee=Me.RG16_SNORM_EXT)),E===n.RG_INTEGER&&(W===n.UNSIGNED_BYTE&&(ee=n.RG8UI),W===n.UNSIGNED_SHORT&&(ee=n.RG16UI),W===n.UNSIGNED_INT&&(ee=n.RG32UI),W===n.BYTE&&(ee=n.RG8I),W===n.SHORT&&(ee=n.RG16I),W===n.INT&&(ee=n.RG32I)),E===n.RGB_INTEGER&&(W===n.UNSIGNED_BYTE&&(ee=n.RGB8UI),W===n.UNSIGNED_SHORT&&(ee=n.RGB16UI),W===n.UNSIGNED_INT&&(ee=n.RGB32UI),W===n.BYTE&&(ee=n.RGB8I),W===n.SHORT&&(ee=n.RGB16I),W===n.INT&&(ee=n.RGB32I)),E===n.RGBA_INTEGER&&(W===n.UNSIGNED_BYTE&&(ee=n.RGBA8UI),W===n.UNSIGNED_SHORT&&(ee=n.RGBA16UI),W===n.UNSIGNED_INT&&(ee=n.RGBA32UI),W===n.BYTE&&(ee=n.RGBA8I),W===n.SHORT&&(ee=n.RGBA16I),W===n.INT&&(ee=n.RGBA32I)),E===n.RGB&&(W===n.UNSIGNED_SHORT&&Me&&(ee=Me.RGB16_EXT),W===n.SHORT&&Me&&(ee=Me.RGB16_SNORM_EXT),W===n.UNSIGNED_INT_5_9_9_9_REV&&(ee=n.RGB9_E5),W===n.UNSIGNED_INT_10F_11F_11F_REV&&(ee=n.R11F_G11F_B10F)),E===n.RGBA){const se=ve?hl:ft.getTransfer(ue);W===n.FLOAT&&(ee=n.RGBA32F),W===n.HALF_FLOAT&&(ee=n.RGBA16F),W===n.UNSIGNED_BYTE&&(ee=se===bt?n.SRGB8_ALPHA8:n.RGBA8),W===n.UNSIGNED_SHORT&&Me&&(ee=Me.RGBA16_EXT),W===n.SHORT&&Me&&(ee=Me.RGBA16_SNORM_EXT),W===n.UNSIGNED_SHORT_4_4_4_4&&(ee=n.RGBA4),W===n.UNSIGNED_SHORT_5_5_5_1&&(ee=n.RGB5_A1)}return(ee===n.R16F||ee===n.R32F||ee===n.RG16F||ee===n.RG32F||ee===n.RGBA16F||ee===n.RGBA32F)&&e.get("EXT_color_buffer_float"),ee}function M(D,E){let W;return D?E===null||E===Ui||E===zs?W=n.DEPTH24_STENCIL8:E===hi?W=n.DEPTH32F_STENCIL8:E===ka&&(W=n.DEPTH24_STENCIL8,Je("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):E===null||E===Ui||E===zs?W=n.DEPTH_COMPONENT24:E===hi?W=n.DEPTH_COMPONENT32F:E===ka&&(W=n.DEPTH_COMPONENT16),W}function T(D,E){return _(D)===!0||D.isFramebufferTexture&&D.minFilter!==un&&D.minFilter!==Gt?Math.log2(Math.max(E.width,E.height))+1:D.mipmaps!==void 0&&D.mipmaps.length>0?D.mipmaps.length:D.isCompressedTexture&&Array.isArray(D.image)?E.mipmaps.length:1}function w(D){const E=D.target;E.removeEventListener("dispose",w),x(E),E.isVideoTexture&&u.delete(E),E.isHTMLTexture&&f.delete(E)}function b(D){const E=D.target;E.removeEventListener("dispose",b),P(E)}function x(D){const E=i.get(D);if(E.__webglInit===void 0)return;const W=D.source,Q=d.get(W);if(Q){const ue=Q[E.__cacheKey];ue.usedTimes--,ue.usedTimes===0&&A(D),Object.keys(Q).length===0&&d.delete(W)}i.remove(D)}function A(D){const E=i.get(D);n.deleteTexture(E.__webglTexture);const W=D.source,Q=d.get(W);delete Q[E.__cacheKey],a.memory.textures--}function P(D){const E=i.get(D);if(D.depthTexture&&(D.depthTexture.dispose(),i.remove(D.depthTexture)),D.isWebGLCubeRenderTarget)for(let Q=0;Q<6;Q++){if(Array.isArray(E.__webglFramebuffer[Q]))for(let ue=0;ue<E.__webglFramebuffer[Q].length;ue++)n.deleteFramebuffer(E.__webglFramebuffer[Q][ue]);else n.deleteFramebuffer(E.__webglFramebuffer[Q]);E.__webglDepthbuffer&&n.deleteRenderbuffer(E.__webglDepthbuffer[Q])}else{if(Array.isArray(E.__webglFramebuffer))for(let Q=0;Q<E.__webglFramebuffer.length;Q++)n.deleteFramebuffer(E.__webglFramebuffer[Q]);else n.deleteFramebuffer(E.__webglFramebuffer);if(E.__webglDepthbuffer&&n.deleteRenderbuffer(E.__webglDepthbuffer),E.__webglMultisampledFramebuffer&&n.deleteFramebuffer(E.__webglMultisampledFramebuffer),E.__webglColorRenderbuffer)for(let Q=0;Q<E.__webglColorRenderbuffer.length;Q++)E.__webglColorRenderbuffer[Q]&&n.deleteRenderbuffer(E.__webglColorRenderbuffer[Q]);E.__webglDepthRenderbuffer&&n.deleteRenderbuffer(E.__webglDepthRenderbuffer)}const W=D.textures;for(let Q=0,ue=W.length;Q<ue;Q++){const ve=i.get(W[Q]);ve.__webglTexture&&(n.deleteTexture(ve.__webglTexture),a.memory.textures--),i.remove(W[Q])}i.remove(D)}let R=0;function L(){R=0}function I(){return R}function N(D){R=D}function O(){const D=R;return D>=r.maxTextures&&Je("WebGLTextures: Trying to use "+D+" texture units while this GPU supports only "+r.maxTextures),R+=1,D}function B(D){const E=[];return E.push(D.wrapS),E.push(D.wrapT),E.push(D.wrapR||0),E.push(D.magFilter),E.push(D.minFilter),E.push(D.anisotropy),E.push(D.internalFormat),E.push(D.format),E.push(D.type),E.push(D.generateMipmaps),E.push(D.premultiplyAlpha),E.push(D.flipY),E.push(D.unpackAlignment),E.push(D.colorSpace),E.join()}function q(D,E){const W=i.get(D);if(D.isVideoTexture&&we(D),D.isRenderTargetTexture===!1&&D.isExternalTexture!==!0&&D.version>0&&W.__version!==D.version){const Q=D.image;if(Q===null)Je("WebGLRenderer: Texture marked for update but no image data found.");else if(Q.complete===!1)Je("WebGLRenderer: Texture marked for update but image is incomplete");else{le(W,D,E);return}}else D.isExternalTexture&&(W.__webglTexture=D.sourceTexture?D.sourceTexture:null);t.bindTexture(n.TEXTURE_2D,W.__webglTexture,n.TEXTURE0+E)}function F(D,E){const W=i.get(D);if(D.isRenderTargetTexture===!1&&D.version>0&&W.__version!==D.version){le(W,D,E);return}else D.isExternalTexture&&(W.__webglTexture=D.sourceTexture?D.sourceTexture:null);t.bindTexture(n.TEXTURE_2D_ARRAY,W.__webglTexture,n.TEXTURE0+E)}function k(D,E){const W=i.get(D);if(D.isRenderTargetTexture===!1&&D.version>0&&W.__version!==D.version){le(W,D,E);return}t.bindTexture(n.TEXTURE_3D,W.__webglTexture,n.TEXTURE0+E)}function U(D,E){const W=i.get(D);if(D.isCubeDepthTexture!==!0&&D.version>0&&W.__version!==D.version){ge(W,D,E);return}t.bindTexture(n.TEXTURE_CUBE_MAP,W.__webglTexture,n.TEXTURE0+E)}const z={[Lu]:n.REPEAT,[Vi]:n.CLAMP_TO_EDGE,[Iu]:n.MIRRORED_REPEAT},K={[un]:n.NEAREST,[W_]:n.NEAREST_MIPMAP_NEAREST,[oo]:n.NEAREST_MIPMAP_LINEAR,[Gt]:n.LINEAR,[lc]:n.LINEAR_MIPMAP_NEAREST,[zr]:n.LINEAR_MIPMAP_LINEAR},Z={[Y_]:n.NEVER,[J_]:n.ALWAYS,[q_]:n.LESS,[Jh]:n.LEQUAL,[K_]:n.EQUAL,[Qh]:n.GEQUAL,[Z_]:n.GREATER,[$_]:n.NOTEQUAL};function X(D,E){if(E.type===hi&&e.has("OES_texture_float_linear")===!1&&(E.magFilter===Gt||E.magFilter===lc||E.magFilter===oo||E.magFilter===zr||E.minFilter===Gt||E.minFilter===lc||E.minFilter===oo||E.minFilter===zr)&&Je("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),n.texParameteri(D,n.TEXTURE_WRAP_S,z[E.wrapS]),n.texParameteri(D,n.TEXTURE_WRAP_T,z[E.wrapT]),(D===n.TEXTURE_3D||D===n.TEXTURE_2D_ARRAY)&&n.texParameteri(D,n.TEXTURE_WRAP_R,z[E.wrapR]),n.texParameteri(D,n.TEXTURE_MAG_FILTER,K[E.magFilter]),n.texParameteri(D,n.TEXTURE_MIN_FILTER,K[E.minFilter]),E.compareFunction&&(n.texParameteri(D,n.TEXTURE_COMPARE_MODE,n.COMPARE_REF_TO_TEXTURE),n.texParameteri(D,n.TEXTURE_COMPARE_FUNC,Z[E.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(E.magFilter===un||E.minFilter!==oo&&E.minFilter!==zr||E.type===hi&&e.has("OES_texture_float_linear")===!1)return;if(E.anisotropy>1||i.get(E).__currentAnisotropy){const W=e.get("EXT_texture_filter_anisotropic");n.texParameterf(D,W.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(E.anisotropy,r.getMaxAnisotropy())),i.get(E).__currentAnisotropy=E.anisotropy}}}function H(D,E){let W=!1;D.__webglInit===void 0&&(D.__webglInit=!0,E.addEventListener("dispose",w));const Q=E.source;let ue=d.get(Q);ue===void 0&&(ue={},d.set(Q,ue));const ve=B(E);if(ve!==D.__cacheKey){ue[ve]===void 0&&(ue[ve]={texture:n.createTexture(),usedTimes:0},a.memory.textures++,W=!0),ue[ve].usedTimes++;const Me=ue[D.__cacheKey];Me!==void 0&&(ue[D.__cacheKey].usedTimes--,Me.usedTimes===0&&A(E)),D.__cacheKey=ve,D.__webglTexture=ue[ve].texture}return W}function V(D,E,W){return Math.floor(Math.floor(D/W)/E)}function j(D,E,W,Q){const ve=D.updateRanges;if(ve.length===0)t.texSubImage2D(n.TEXTURE_2D,0,0,0,E.width,E.height,W,Q,E.data);else{ve.sort((De,be)=>De.start-be.start);let Me=0;for(let De=1;De<ve.length;De++){const be=ve[Me],Ee=ve[De],He=be.start+be.count,Le=V(Ee.start,E.width,4),Ye=V(be.start,E.width,4);Ee.start<=He+1&&Le===Ye&&V(Ee.start+Ee.count-1,E.width,4)===Le?be.count=Math.max(be.count,Ee.start+Ee.count-be.start):(++Me,ve[Me]=Ee)}ve.length=Me+1;const ee=t.getParameter(n.UNPACK_ROW_LENGTH),se=t.getParameter(n.UNPACK_SKIP_PIXELS),de=t.getParameter(n.UNPACK_SKIP_ROWS);t.pixelStorei(n.UNPACK_ROW_LENGTH,E.width);for(let De=0,be=ve.length;De<be;De++){const Ee=ve[De],He=Math.floor(Ee.start/4),Le=Math.ceil(Ee.count/4),Ye=He%E.width,Y=Math.floor(He/E.width),_e=Le,re=1;t.pixelStorei(n.UNPACK_SKIP_PIXELS,Ye),t.pixelStorei(n.UNPACK_SKIP_ROWS,Y),t.texSubImage2D(n.TEXTURE_2D,0,Ye,Y,_e,re,W,Q,E.data)}D.clearUpdateRanges(),t.pixelStorei(n.UNPACK_ROW_LENGTH,ee),t.pixelStorei(n.UNPACK_SKIP_PIXELS,se),t.pixelStorei(n.UNPACK_SKIP_ROWS,de)}}function le(D,E,W){let Q=n.TEXTURE_2D;(E.isDataArrayTexture||E.isCompressedArrayTexture)&&(Q=n.TEXTURE_2D_ARRAY),E.isData3DTexture&&(Q=n.TEXTURE_3D);const ue=H(D,E),ve=E.source;t.bindTexture(Q,D.__webglTexture,n.TEXTURE0+W);const Me=i.get(ve);if(ve.version!==Me.__version||ue===!0){if(t.activeTexture(n.TEXTURE0+W),(typeof ImageBitmap<"u"&&E.image instanceof ImageBitmap)===!1){const re=ft.getPrimaries(ft.workingColorSpace),Pe=E.colorSpace===Ti?null:ft.getPrimaries(E.colorSpace),Se=E.colorSpace===Ti||re===Pe?n.NONE:n.BROWSER_DEFAULT_WEBGL;t.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,E.flipY),t.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,E.premultiplyAlpha),t.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,Se)}t.pixelStorei(n.UNPACK_ALIGNMENT,E.unpackAlignment);let se=p(E.image,!1,r.maxTextureSize);se=he(E,se);const de=s.convert(E.format,E.colorSpace),De=s.convert(E.type);let be=y(E.internalFormat,de,De,E.normalized,E.colorSpace,E.isVideoTexture);X(Q,E);let Ee;const He=E.mipmaps,Le=E.isVideoTexture!==!0,Ye=Me.__version===void 0||ue===!0,Y=ve.dataReady,_e=T(E,se);if(E.isDepthTexture)be=M(E.format===fr,E.type),Ye&&(Le?t.texStorage2D(n.TEXTURE_2D,1,be,se.width,se.height):t.texImage2D(n.TEXTURE_2D,0,be,se.width,se.height,0,de,De,null));else if(E.isDataTexture)if(He.length>0){Le&&Ye&&t.texStorage2D(n.TEXTURE_2D,_e,be,He[0].width,He[0].height);for(let re=0,Pe=He.length;re<Pe;re++)Ee=He[re],Le?Y&&t.texSubImage2D(n.TEXTURE_2D,re,0,0,Ee.width,Ee.height,de,De,Ee.data):t.texImage2D(n.TEXTURE_2D,re,be,Ee.width,Ee.height,0,de,De,Ee.data);E.generateMipmaps=!1}else Le?(Ye&&t.texStorage2D(n.TEXTURE_2D,_e,be,se.width,se.height),Y&&j(E,se,de,De)):t.texImage2D(n.TEXTURE_2D,0,be,se.width,se.height,0,de,De,se.data);else if(E.isCompressedTexture)if(E.isCompressedArrayTexture){Le&&Ye&&t.texStorage3D(n.TEXTURE_2D_ARRAY,_e,be,He[0].width,He[0].height,se.depth);for(let re=0,Pe=He.length;re<Pe;re++)if(Ee=He[re],E.format!==fi)if(de!==null)if(Le){if(Y)if(E.layerUpdates.size>0){const Se=Bd(Ee.width,Ee.height,E.format,E.type);for(const ce of E.layerUpdates){const Ne=Ee.data.subarray(ce*Se/Ee.data.BYTES_PER_ELEMENT,(ce+1)*Se/Ee.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(n.TEXTURE_2D_ARRAY,re,0,0,ce,Ee.width,Ee.height,1,de,Ne)}E.clearLayerUpdates()}else t.compressedTexSubImage3D(n.TEXTURE_2D_ARRAY,re,0,0,0,Ee.width,Ee.height,se.depth,de,Ee.data)}else t.compressedTexImage3D(n.TEXTURE_2D_ARRAY,re,be,Ee.width,Ee.height,se.depth,0,Ee.data,0,0);else Je("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else Le?Y&&t.texSubImage3D(n.TEXTURE_2D_ARRAY,re,0,0,0,Ee.width,Ee.height,se.depth,de,De,Ee.data):t.texImage3D(n.TEXTURE_2D_ARRAY,re,be,Ee.width,Ee.height,se.depth,0,de,De,Ee.data)}else{Le&&Ye&&t.texStorage2D(n.TEXTURE_2D,_e,be,He[0].width,He[0].height);for(let re=0,Pe=He.length;re<Pe;re++)Ee=He[re],E.format!==fi?de!==null?Le?Y&&t.compressedTexSubImage2D(n.TEXTURE_2D,re,0,0,Ee.width,Ee.height,de,Ee.data):t.compressedTexImage2D(n.TEXTURE_2D,re,be,Ee.width,Ee.height,0,Ee.data):Je("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):Le?Y&&t.texSubImage2D(n.TEXTURE_2D,re,0,0,Ee.width,Ee.height,de,De,Ee.data):t.texImage2D(n.TEXTURE_2D,re,be,Ee.width,Ee.height,0,de,De,Ee.data)}else if(E.isDataArrayTexture)if(Le){if(Ye&&t.texStorage3D(n.TEXTURE_2D_ARRAY,_e,be,se.width,se.height,se.depth),Y)if(E.layerUpdates.size>0){const re=Bd(se.width,se.height,E.format,E.type);for(const Pe of E.layerUpdates){const Se=se.data.subarray(Pe*re/se.data.BYTES_PER_ELEMENT,(Pe+1)*re/se.data.BYTES_PER_ELEMENT);t.texSubImage3D(n.TEXTURE_2D_ARRAY,0,0,0,Pe,se.width,se.height,1,de,De,Se)}E.clearLayerUpdates()}else t.texSubImage3D(n.TEXTURE_2D_ARRAY,0,0,0,0,se.width,se.height,se.depth,de,De,se.data)}else t.texImage3D(n.TEXTURE_2D_ARRAY,0,be,se.width,se.height,se.depth,0,de,De,se.data);else if(E.isData3DTexture)Le?(Ye&&t.texStorage3D(n.TEXTURE_3D,_e,be,se.width,se.height,se.depth),Y&&t.texSubImage3D(n.TEXTURE_3D,0,0,0,0,se.width,se.height,se.depth,de,De,se.data)):t.texImage3D(n.TEXTURE_3D,0,be,se.width,se.height,se.depth,0,de,De,se.data);else if(E.isFramebufferTexture){if(Ye)if(Le)t.texStorage2D(n.TEXTURE_2D,_e,be,se.width,se.height);else{let re=se.width,Pe=se.height;for(let Se=0;Se<_e;Se++)t.texImage2D(n.TEXTURE_2D,Se,be,re,Pe,0,de,De,null),re>>=1,Pe>>=1}}else if(E.isHTMLTexture){if("texElementImage2D"in n){const re=n.canvas;if(re.hasAttribute("layoutsubtree")||re.setAttribute("layoutsubtree","true"),se.parentNode!==re){re.appendChild(se),f.add(E),re.onpaint=Ze=>{const ot=Ze.changedElements;for(const et of f)ot.includes(et.image)&&(et.needsUpdate=!0)},re.requestPaint();return}const Pe=0,Se=n.RGBA,ce=n.RGBA,Ne=n.UNSIGNED_BYTE;n.texElementImage2D(n.TEXTURE_2D,Pe,Se,ce,Ne,se),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_MIN_FILTER,n.LINEAR),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_WRAP_S,n.CLAMP_TO_EDGE),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_WRAP_T,n.CLAMP_TO_EDGE)}}else if(He.length>0){if(Le&&Ye){const re=Re(He[0]);t.texStorage2D(n.TEXTURE_2D,_e,be,re.width,re.height)}for(let re=0,Pe=He.length;re<Pe;re++)Ee=He[re],Le?Y&&t.texSubImage2D(n.TEXTURE_2D,re,0,0,de,De,Ee):t.texImage2D(n.TEXTURE_2D,re,be,de,De,Ee);E.generateMipmaps=!1}else if(Le){if(Ye){const re=Re(se);t.texStorage2D(n.TEXTURE_2D,_e,be,re.width,re.height)}Y&&t.texSubImage2D(n.TEXTURE_2D,0,0,0,de,De,se)}else t.texImage2D(n.TEXTURE_2D,0,be,de,De,se);_(E)&&v(Q),Me.__version=ve.version,E.onUpdate&&E.onUpdate(E)}D.__version=E.version}function ge(D,E,W){if(E.image.length!==6)return;const Q=H(D,E),ue=E.source;t.bindTexture(n.TEXTURE_CUBE_MAP,D.__webglTexture,n.TEXTURE0+W);const ve=i.get(ue);if(ue.version!==ve.__version||Q===!0){t.activeTexture(n.TEXTURE0+W);const Me=ft.getPrimaries(ft.workingColorSpace),ee=E.colorSpace===Ti?null:ft.getPrimaries(E.colorSpace),se=E.colorSpace===Ti||Me===ee?n.NONE:n.BROWSER_DEFAULT_WEBGL;t.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,E.flipY),t.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,E.premultiplyAlpha),t.pixelStorei(n.UNPACK_ALIGNMENT,E.unpackAlignment),t.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,se);const de=E.isCompressedTexture||E.image[0].isCompressedTexture,De=E.image[0]&&E.image[0].isDataTexture,be=[];for(let ce=0;ce<6;ce++)!de&&!De?be[ce]=p(E.image[ce],!0,r.maxCubemapSize):be[ce]=De?E.image[ce].image:E.image[ce],be[ce]=he(E,be[ce]);const Ee=be[0],He=s.convert(E.format,E.colorSpace),Le=s.convert(E.type),Ye=y(E.internalFormat,He,Le,E.normalized,E.colorSpace),Y=E.isVideoTexture!==!0,_e=ve.__version===void 0||Q===!0,re=ue.dataReady;let Pe=T(E,Ee);X(n.TEXTURE_CUBE_MAP,E);let Se;if(de){Y&&_e&&t.texStorage2D(n.TEXTURE_CUBE_MAP,Pe,Ye,Ee.width,Ee.height);for(let ce=0;ce<6;ce++){Se=be[ce].mipmaps;for(let Ne=0;Ne<Se.length;Ne++){const Ze=Se[Ne];E.format!==fi?He!==null?Y?re&&t.compressedTexSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,Ne,0,0,Ze.width,Ze.height,He,Ze.data):t.compressedTexImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,Ne,Ye,Ze.width,Ze.height,0,Ze.data):Je("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):Y?re&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,Ne,0,0,Ze.width,Ze.height,He,Le,Ze.data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,Ne,Ye,Ze.width,Ze.height,0,He,Le,Ze.data)}}}else{if(Se=E.mipmaps,Y&&_e){Se.length>0&&Pe++;const ce=Re(be[0]);t.texStorage2D(n.TEXTURE_CUBE_MAP,Pe,Ye,ce.width,ce.height)}for(let ce=0;ce<6;ce++)if(De){Y?re&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,0,0,0,be[ce].width,be[ce].height,He,Le,be[ce].data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,0,Ye,be[ce].width,be[ce].height,0,He,Le,be[ce].data);for(let Ne=0;Ne<Se.length;Ne++){const ot=Se[Ne].image[ce].image;Y?re&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,Ne+1,0,0,ot.width,ot.height,He,Le,ot.data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,Ne+1,Ye,ot.width,ot.height,0,He,Le,ot.data)}}else{Y?re&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,0,0,0,He,Le,be[ce]):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,0,Ye,He,Le,be[ce]);for(let Ne=0;Ne<Se.length;Ne++){const Ze=Se[Ne];Y?re&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,Ne+1,0,0,He,Le,Ze.image[ce]):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ce,Ne+1,Ye,He,Le,Ze.image[ce])}}}_(E)&&v(n.TEXTURE_CUBE_MAP),ve.__version=ue.version,E.onUpdate&&E.onUpdate(E)}D.__version=E.version}function oe(D,E,W,Q,ue,ve){const Me=s.convert(W.format,W.colorSpace),ee=s.convert(W.type),se=y(W.internalFormat,Me,ee,W.normalized,W.colorSpace),de=i.get(E),De=i.get(W);if(De.__renderTarget=E,!de.__hasExternalTextures){const be=Math.max(1,E.width>>ve),Ee=Math.max(1,E.height>>ve);ue===n.TEXTURE_3D||ue===n.TEXTURE_2D_ARRAY?t.texImage3D(ue,ve,se,be,Ee,E.depth,0,Me,ee,null):t.texImage2D(ue,ve,se,be,Ee,0,Me,ee,null)}t.bindFramebuffer(n.FRAMEBUFFER,D),Fe(E)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,Q,ue,De.__webglTexture,0,fe(E)):(ue===n.TEXTURE_2D||ue>=n.TEXTURE_CUBE_MAP_POSITIVE_X&&ue<=n.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&n.framebufferTexture2D(n.FRAMEBUFFER,Q,ue,De.__webglTexture,ve),t.bindFramebuffer(n.FRAMEBUFFER,null)}function te(D,E,W){if(n.bindRenderbuffer(n.RENDERBUFFER,D),E.depthBuffer){const Q=E.depthTexture,ue=Q&&Q.isDepthTexture?Q.type:null,ve=M(E.stencilBuffer,ue),Me=E.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;Fe(E)?o.renderbufferStorageMultisampleEXT(n.RENDERBUFFER,fe(E),ve,E.width,E.height):W?n.renderbufferStorageMultisample(n.RENDERBUFFER,fe(E),ve,E.width,E.height):n.renderbufferStorage(n.RENDERBUFFER,ve,E.width,E.height),n.framebufferRenderbuffer(n.FRAMEBUFFER,Me,n.RENDERBUFFER,D)}else{const Q=E.textures;for(let ue=0;ue<Q.length;ue++){const ve=Q[ue],Me=s.convert(ve.format,ve.colorSpace),ee=s.convert(ve.type),se=y(ve.internalFormat,Me,ee,ve.normalized,ve.colorSpace);Fe(E)?o.renderbufferStorageMultisampleEXT(n.RENDERBUFFER,fe(E),se,E.width,E.height):W?n.renderbufferStorageMultisample(n.RENDERBUFFER,fe(E),se,E.width,E.height):n.renderbufferStorage(n.RENDERBUFFER,se,E.width,E.height)}}n.bindRenderbuffer(n.RENDERBUFFER,null)}function xe(D,E,W){const Q=E.isWebGLCubeRenderTarget===!0;if(t.bindFramebuffer(n.FRAMEBUFFER,D),!(E.depthTexture&&E.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");const ue=i.get(E.depthTexture);if(ue.__renderTarget=E,(!ue.__webglTexture||E.depthTexture.image.width!==E.width||E.depthTexture.image.height!==E.height)&&(E.depthTexture.image.width=E.width,E.depthTexture.image.height=E.height,E.depthTexture.needsUpdate=!0),Q){if(ue.__webglInit===void 0&&(ue.__webglInit=!0,E.depthTexture.addEventListener("dispose",w)),ue.__webglTexture===void 0){ue.__webglTexture=n.createTexture(),t.bindTexture(n.TEXTURE_CUBE_MAP,ue.__webglTexture),X(n.TEXTURE_CUBE_MAP,E.depthTexture);const de=s.convert(E.depthTexture.format),De=s.convert(E.depthTexture.type);let be;E.depthTexture.format===qi?be=n.DEPTH_COMPONENT24:E.depthTexture.format===fr&&(be=n.DEPTH24_STENCIL8);for(let Ee=0;Ee<6;Ee++)n.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+Ee,0,be,E.width,E.height,0,de,De,null)}}else q(E.depthTexture,0);const ve=ue.__webglTexture,Me=fe(E),ee=Q?n.TEXTURE_CUBE_MAP_POSITIVE_X+W:n.TEXTURE_2D,se=E.depthTexture.format===fr?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;if(E.depthTexture.format===qi)Fe(E)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,se,ee,ve,0,Me):n.framebufferTexture2D(n.FRAMEBUFFER,se,ee,ve,0);else if(E.depthTexture.format===fr)Fe(E)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,se,ee,ve,0,Me):n.framebufferTexture2D(n.FRAMEBUFFER,se,ee,ve,0);else throw new Error("Unknown depthTexture format")}function Ae(D){const E=i.get(D),W=D.isWebGLCubeRenderTarget===!0;if(E.__boundDepthTexture!==D.depthTexture){const Q=D.depthTexture;if(E.__depthDisposeCallback&&E.__depthDisposeCallback(),Q){const ue=()=>{delete E.__boundDepthTexture,delete E.__depthDisposeCallback,Q.removeEventListener("dispose",ue)};Q.addEventListener("dispose",ue),E.__depthDisposeCallback=ue}E.__boundDepthTexture=Q}if(D.depthTexture&&!E.__autoAllocateDepthBuffer)if(W)for(let Q=0;Q<6;Q++)xe(E.__webglFramebuffer[Q],D,Q);else{const Q=D.texture.mipmaps;Q&&Q.length>0?xe(E.__webglFramebuffer[0],D,0):xe(E.__webglFramebuffer,D,0)}else if(W){E.__webglDepthbuffer=[];for(let Q=0;Q<6;Q++)if(t.bindFramebuffer(n.FRAMEBUFFER,E.__webglFramebuffer[Q]),E.__webglDepthbuffer[Q]===void 0)E.__webglDepthbuffer[Q]=n.createRenderbuffer(),te(E.__webglDepthbuffer[Q],D,!1);else{const ue=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,ve=E.__webglDepthbuffer[Q];n.bindRenderbuffer(n.RENDERBUFFER,ve),n.framebufferRenderbuffer(n.FRAMEBUFFER,ue,n.RENDERBUFFER,ve)}}else{const Q=D.texture.mipmaps;if(Q&&Q.length>0?t.bindFramebuffer(n.FRAMEBUFFER,E.__webglFramebuffer[0]):t.bindFramebuffer(n.FRAMEBUFFER,E.__webglFramebuffer),E.__webglDepthbuffer===void 0)E.__webglDepthbuffer=n.createRenderbuffer(),te(E.__webglDepthbuffer,D,!1);else{const ue=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,ve=E.__webglDepthbuffer;n.bindRenderbuffer(n.RENDERBUFFER,ve),n.framebufferRenderbuffer(n.FRAMEBUFFER,ue,n.RENDERBUFFER,ve)}}t.bindFramebuffer(n.FRAMEBUFFER,null)}function Te(D,E,W){const Q=i.get(D);E!==void 0&&oe(Q.__webglFramebuffer,D,D.texture,n.COLOR_ATTACHMENT0,n.TEXTURE_2D,0),W!==void 0&&Ae(D)}function ye(D){const E=D.texture,W=i.get(D),Q=i.get(E);D.addEventListener("dispose",b);const ue=D.textures,ve=D.isWebGLCubeRenderTarget===!0,Me=ue.length>1;if(Me||(Q.__webglTexture===void 0&&(Q.__webglTexture=n.createTexture()),Q.__version=E.version,a.memory.textures++),ve){W.__webglFramebuffer=[];for(let ee=0;ee<6;ee++)if(E.mipmaps&&E.mipmaps.length>0){W.__webglFramebuffer[ee]=[];for(let se=0;se<E.mipmaps.length;se++)W.__webglFramebuffer[ee][se]=n.createFramebuffer()}else W.__webglFramebuffer[ee]=n.createFramebuffer()}else{if(E.mipmaps&&E.mipmaps.length>0){W.__webglFramebuffer=[];for(let ee=0;ee<E.mipmaps.length;ee++)W.__webglFramebuffer[ee]=n.createFramebuffer()}else W.__webglFramebuffer=n.createFramebuffer();if(Me)for(let ee=0,se=ue.length;ee<se;ee++){const de=i.get(ue[ee]);de.__webglTexture===void 0&&(de.__webglTexture=n.createTexture(),a.memory.textures++)}if(D.samples>0&&Fe(D)===!1){W.__webglMultisampledFramebuffer=n.createFramebuffer(),W.__webglColorRenderbuffer=[],t.bindFramebuffer(n.FRAMEBUFFER,W.__webglMultisampledFramebuffer);for(let ee=0;ee<ue.length;ee++){const se=ue[ee];W.__webglColorRenderbuffer[ee]=n.createRenderbuffer(),n.bindRenderbuffer(n.RENDERBUFFER,W.__webglColorRenderbuffer[ee]);const de=s.convert(se.format,se.colorSpace),De=s.convert(se.type),be=y(se.internalFormat,de,De,se.normalized,se.colorSpace,D.isXRRenderTarget===!0),Ee=fe(D);n.renderbufferStorageMultisample(n.RENDERBUFFER,Ee,be,D.width,D.height),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+ee,n.RENDERBUFFER,W.__webglColorRenderbuffer[ee])}n.bindRenderbuffer(n.RENDERBUFFER,null),D.depthBuffer&&(W.__webglDepthRenderbuffer=n.createRenderbuffer(),te(W.__webglDepthRenderbuffer,D,!0)),t.bindFramebuffer(n.FRAMEBUFFER,null)}}if(ve){t.bindTexture(n.TEXTURE_CUBE_MAP,Q.__webglTexture),X(n.TEXTURE_CUBE_MAP,E);for(let ee=0;ee<6;ee++)if(E.mipmaps&&E.mipmaps.length>0)for(let se=0;se<E.mipmaps.length;se++)oe(W.__webglFramebuffer[ee][se],D,E,n.COLOR_ATTACHMENT0,n.TEXTURE_CUBE_MAP_POSITIVE_X+ee,se);else oe(W.__webglFramebuffer[ee],D,E,n.COLOR_ATTACHMENT0,n.TEXTURE_CUBE_MAP_POSITIVE_X+ee,0);_(E)&&v(n.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Me){for(let ee=0,se=ue.length;ee<se;ee++){const de=ue[ee],De=i.get(de);let be=n.TEXTURE_2D;(D.isWebGL3DRenderTarget||D.isWebGLArrayRenderTarget)&&(be=D.isWebGL3DRenderTarget?n.TEXTURE_3D:n.TEXTURE_2D_ARRAY),t.bindTexture(be,De.__webglTexture),X(be,de),oe(W.__webglFramebuffer,D,de,n.COLOR_ATTACHMENT0+ee,be,0),_(de)&&v(be)}t.unbindTexture()}else{let ee=n.TEXTURE_2D;if((D.isWebGL3DRenderTarget||D.isWebGLArrayRenderTarget)&&(ee=D.isWebGL3DRenderTarget?n.TEXTURE_3D:n.TEXTURE_2D_ARRAY),t.bindTexture(ee,Q.__webglTexture),X(ee,E),E.mipmaps&&E.mipmaps.length>0)for(let se=0;se<E.mipmaps.length;se++)oe(W.__webglFramebuffer[se],D,E,n.COLOR_ATTACHMENT0,ee,se);else oe(W.__webglFramebuffer,D,E,n.COLOR_ATTACHMENT0,ee,0);_(E)&&v(ee),t.unbindTexture()}D.depthBuffer&&Ae(D)}function Ue(D){const E=D.textures;for(let W=0,Q=E.length;W<Q;W++){const ue=E[W];if(_(ue)){const ve=S(D),Me=i.get(ue).__webglTexture;t.bindTexture(ve,Me),v(ve),t.unbindTexture()}}}const me=[],ke=[];function G(D){if(D.samples>0){if(Fe(D)===!1){const E=D.textures,W=D.width,Q=D.height;let ue=n.COLOR_BUFFER_BIT;const ve=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,Me=i.get(D),ee=E.length>1;if(ee)for(let de=0;de<E.length;de++)t.bindFramebuffer(n.FRAMEBUFFER,Me.__webglMultisampledFramebuffer),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+de,n.RENDERBUFFER,null),t.bindFramebuffer(n.FRAMEBUFFER,Me.__webglFramebuffer),n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0+de,n.TEXTURE_2D,null,0);t.bindFramebuffer(n.READ_FRAMEBUFFER,Me.__webglMultisampledFramebuffer);const se=D.texture.mipmaps;se&&se.length>0?t.bindFramebuffer(n.DRAW_FRAMEBUFFER,Me.__webglFramebuffer[0]):t.bindFramebuffer(n.DRAW_FRAMEBUFFER,Me.__webglFramebuffer);for(let de=0;de<E.length;de++){if(D.resolveDepthBuffer&&(D.depthBuffer&&(ue|=n.DEPTH_BUFFER_BIT),D.stencilBuffer&&D.resolveStencilBuffer&&(ue|=n.STENCIL_BUFFER_BIT)),ee){n.framebufferRenderbuffer(n.READ_FRAMEBUFFER,n.COLOR_ATTACHMENT0,n.RENDERBUFFER,Me.__webglColorRenderbuffer[de]);const De=i.get(E[de]).__webglTexture;n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0,n.TEXTURE_2D,De,0)}n.blitFramebuffer(0,0,W,Q,0,0,W,Q,ue,n.NEAREST),l===!0&&(me.length=0,ke.length=0,me.push(n.COLOR_ATTACHMENT0+de),D.depthBuffer&&D.resolveDepthBuffer===!1&&(me.push(ve),ke.push(ve),n.invalidateFramebuffer(n.DRAW_FRAMEBUFFER,ke)),n.invalidateFramebuffer(n.READ_FRAMEBUFFER,me))}if(t.bindFramebuffer(n.READ_FRAMEBUFFER,null),t.bindFramebuffer(n.DRAW_FRAMEBUFFER,null),ee)for(let de=0;de<E.length;de++){t.bindFramebuffer(n.FRAMEBUFFER,Me.__webglMultisampledFramebuffer),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+de,n.RENDERBUFFER,Me.__webglColorRenderbuffer[de]);const De=i.get(E[de]).__webglTexture;t.bindFramebuffer(n.FRAMEBUFFER,Me.__webglFramebuffer),n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0+de,n.TEXTURE_2D,De,0)}t.bindFramebuffer(n.DRAW_FRAMEBUFFER,Me.__webglMultisampledFramebuffer)}else if(D.depthBuffer&&D.resolveDepthBuffer===!1&&l){const E=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;n.invalidateFramebuffer(n.DRAW_FRAMEBUFFER,[E])}}}function fe(D){return Math.min(r.maxSamples,D.samples)}function Fe(D){const E=i.get(D);return D.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&E.__useRenderToTexture!==!1}function we(D){const E=a.render.frame;u.get(D)!==E&&(u.set(D,E),D.update())}function he(D,E){const W=D.colorSpace,Q=D.format,ue=D.type;return D.isCompressedTexture===!0||D.isVideoTexture===!0||W!==Gs&&W!==Ti&&(ft.getTransfer(W)===bt?(Q!==fi||ue!==Yt)&&Je("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):pt("WebGLTextures: Unsupported texture color space:",W)),E}function Re(D){return typeof HTMLImageElement<"u"&&D instanceof HTMLImageElement?(c.width=D.naturalWidth||D.width,c.height=D.naturalHeight||D.height):typeof VideoFrame<"u"&&D instanceof VideoFrame?(c.width=D.displayWidth,c.height=D.displayHeight):(c.width=D.width,c.height=D.height),c}this.allocateTextureUnit=O,this.resetTextureUnits=L,this.getTextureUnits=I,this.setTextureUnits=N,this.setTexture2D=q,this.setTexture2DArray=F,this.setTexture3D=k,this.setTextureCube=U,this.rebindTextures=Te,this.setupRenderTarget=ye,this.updateRenderTargetMipmap=Ue,this.updateMultisampleRenderTarget=G,this.setupDepthRenderbuffer=Ae,this.setupFrameBufferTexture=oe,this.useMultisampledRTT=Fe,this.isReversedDepthBuffer=function(){return t.buffers.depth.getReversed()}}function AS(n,e){function t(i,r=Ti){let s;const a=ft.getTransfer(r);if(i===Yt)return n.UNSIGNED_BYTE;if(i===Yh)return n.UNSIGNED_SHORT_4_4_4_4;if(i===qh)return n.UNSIGNED_SHORT_5_5_5_1;if(i===Lm)return n.UNSIGNED_INT_5_9_9_9_REV;if(i===Im)return n.UNSIGNED_INT_10F_11F_11F_REV;if(i===Dm)return n.BYTE;if(i===Um)return n.SHORT;if(i===ka)return n.UNSIGNED_SHORT;if(i===jh)return n.INT;if(i===Ui)return n.UNSIGNED_INT;if(i===hi)return n.FLOAT;if(i===Yi)return n.HALF_FLOAT;if(i===Fm)return n.ALPHA;if(i===Nm)return n.RGB;if(i===fi)return n.RGBA;if(i===qi)return n.DEPTH_COMPONENT;if(i===fr)return n.DEPTH_STENCIL;if(i===Om)return n.RED;if(i===Kh)return n.RED_INTEGER;if(i===$r)return n.RG;if(i===Zh)return n.RG_INTEGER;if(i===$h)return n.RGBA_INTEGER;if(i===qo||i===Ko||i===Zo||i===$o)if(a===bt)if(s=e.get("WEBGL_compressed_texture_s3tc_srgb"),s!==null){if(i===qo)return s.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(i===Ko)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(i===Zo)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(i===$o)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(s=e.get("WEBGL_compressed_texture_s3tc"),s!==null){if(i===qo)return s.COMPRESSED_RGB_S3TC_DXT1_EXT;if(i===Ko)return s.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(i===Zo)return s.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(i===$o)return s.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(i===Fu||i===Nu||i===Ou||i===Bu)if(s=e.get("WEBGL_compressed_texture_pvrtc"),s!==null){if(i===Fu)return s.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(i===Nu)return s.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(i===Ou)return s.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(i===Bu)return s.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(i===ku||i===zu||i===Gu||i===Hu||i===Vu||i===cl||i===Wu)if(s=e.get("WEBGL_compressed_texture_etc"),s!==null){if(i===ku||i===zu)return a===bt?s.COMPRESSED_SRGB8_ETC2:s.COMPRESSED_RGB8_ETC2;if(i===Gu)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:s.COMPRESSED_RGBA8_ETC2_EAC;if(i===Hu)return s.COMPRESSED_R11_EAC;if(i===Vu)return s.COMPRESSED_SIGNED_R11_EAC;if(i===cl)return s.COMPRESSED_RG11_EAC;if(i===Wu)return s.COMPRESSED_SIGNED_RG11_EAC}else return null;if(i===Xu||i===ju||i===Yu||i===qu||i===Ku||i===Zu||i===$u||i===Ju||i===Qu||i===eh||i===th||i===nh||i===ih||i===rh)if(s=e.get("WEBGL_compressed_texture_astc"),s!==null){if(i===Xu)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:s.COMPRESSED_RGBA_ASTC_4x4_KHR;if(i===ju)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:s.COMPRESSED_RGBA_ASTC_5x4_KHR;if(i===Yu)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:s.COMPRESSED_RGBA_ASTC_5x5_KHR;if(i===qu)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:s.COMPRESSED_RGBA_ASTC_6x5_KHR;if(i===Ku)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:s.COMPRESSED_RGBA_ASTC_6x6_KHR;if(i===Zu)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:s.COMPRESSED_RGBA_ASTC_8x5_KHR;if(i===$u)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:s.COMPRESSED_RGBA_ASTC_8x6_KHR;if(i===Ju)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:s.COMPRESSED_RGBA_ASTC_8x8_KHR;if(i===Qu)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:s.COMPRESSED_RGBA_ASTC_10x5_KHR;if(i===eh)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:s.COMPRESSED_RGBA_ASTC_10x6_KHR;if(i===th)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:s.COMPRESSED_RGBA_ASTC_10x8_KHR;if(i===nh)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:s.COMPRESSED_RGBA_ASTC_10x10_KHR;if(i===ih)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:s.COMPRESSED_RGBA_ASTC_12x10_KHR;if(i===rh)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:s.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(i===sh||i===ah||i===oh)if(s=e.get("EXT_texture_compression_bptc"),s!==null){if(i===sh)return a===bt?s.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:s.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(i===ah)return s.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(i===oh)return s.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(i===lh||i===ch||i===ul||i===uh)if(s=e.get("EXT_texture_compression_rgtc"),s!==null){if(i===lh)return s.COMPRESSED_RED_RGTC1_EXT;if(i===ch)return s.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(i===ul)return s.COMPRESSED_RED_GREEN_RGTC2_EXT;if(i===uh)return s.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return i===zs?n.UNSIGNED_INT_24_8:n[i]!==void 0?n[i]:null}return{convert:t}}const RS=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,CS=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`;class PS{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){const i=new Ym(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=i}}getMesh(e){if(this.texture!==null&&this.mesh===null){const t=e.cameras[0].viewport,i=new on({vertexShader:RS,fragmentShader:CS,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new jn(new Qr(20,20),i)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class DS extends pi{constructor(e,t){super();const i=this;let r=null,s=1,a=null,o="local-floor",l=1,c=null,u=null,f=null,h=null,d=null,m=null;const g=typeof XRWebGLBinding<"u",p=new PS,_={},v=t.getContextAttributes();let S=null,y=null;const M=[],T=[],w=new Xe;let b=null;const x=new Gn;x.viewport=new Ut;const A=new Gn;A.viewport=new Ut;const P=[x,A],R=new kv;let L=null,I=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(H){let V=M[H];return V===void 0&&(V=new mc,M[H]=V),V.getTargetRaySpace()},this.getControllerGrip=function(H){let V=M[H];return V===void 0&&(V=new mc,M[H]=V),V.getGripSpace()},this.getHand=function(H){let V=M[H];return V===void 0&&(V=new mc,M[H]=V),V.getHandSpace()};function N(H){const V=T.indexOf(H.inputSource);if(V===-1)return;const j=M[V];j!==void 0&&(j.update(H.inputSource,H.frame,c||a),j.dispatchEvent({type:H.type,data:H.inputSource}))}function O(){r.removeEventListener("select",N),r.removeEventListener("selectstart",N),r.removeEventListener("selectend",N),r.removeEventListener("squeeze",N),r.removeEventListener("squeezestart",N),r.removeEventListener("squeezeend",N),r.removeEventListener("end",O),r.removeEventListener("inputsourceschange",B);for(let H=0;H<M.length;H++){const V=T[H];V!==null&&(T[H]=null,M[H].disconnect(V))}L=null,I=null,p.reset();for(const H in _)delete _[H];e.setRenderTarget(S),d=null,h=null,f=null,r=null,y=null,X.stop(),i.isPresenting=!1,e.setPixelRatio(b),e.setSize(w.width,w.height,!1),i.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(H){s=H,i.isPresenting===!0&&Je("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(H){o=H,i.isPresenting===!0&&Je("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||a},this.setReferenceSpace=function(H){c=H},this.getBaseLayer=function(){return h!==null?h:d},this.getBinding=function(){return f===null&&g&&(f=new XRWebGLBinding(r,t)),f},this.getFrame=function(){return m},this.getSession=function(){return r},this.setSession=async function(H){if(r=H,r!==null){if(S=e.getRenderTarget(),r.addEventListener("select",N),r.addEventListener("selectstart",N),r.addEventListener("selectend",N),r.addEventListener("squeeze",N),r.addEventListener("squeezestart",N),r.addEventListener("squeezeend",N),r.addEventListener("end",O),r.addEventListener("inputsourceschange",B),v.xrCompatible!==!0&&await t.makeXRCompatible(),b=e.getPixelRatio(),e.getSize(w),g&&"createProjectionLayer"in XRWebGLBinding.prototype){let j=null,le=null,ge=null;v.depth&&(ge=v.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,j=v.stencil?fr:qi,le=v.stencil?zs:Ui);const oe={colorFormat:t.RGBA8,depthFormat:ge,scaleFactor:s};f=this.getBinding(),h=f.createProjectionLayer(oe),r.updateRenderState({layers:[h]}),e.setPixelRatio(1),e.setSize(h.textureWidth,h.textureHeight,!1),y=new Jt(h.textureWidth,h.textureHeight,{format:fi,type:Yt,depthTexture:new Xi(h.textureWidth,h.textureHeight,le,void 0,void 0,void 0,void 0,void 0,void 0,j),stencilBuffer:v.stencil,colorSpace:e.outputColorSpace,samples:v.antialias?4:0,resolveDepthBuffer:h.ignoreDepthValues===!1,resolveStencilBuffer:h.ignoreDepthValues===!1})}else{const j={antialias:v.antialias,alpha:!0,depth:v.depth,stencil:v.stencil,framebufferScaleFactor:s};d=new XRWebGLLayer(r,t,j),r.updateRenderState({baseLayer:d}),e.setPixelRatio(1),e.setSize(d.framebufferWidth,d.framebufferHeight,!1),y=new Jt(d.framebufferWidth,d.framebufferHeight,{format:fi,type:Yt,colorSpace:e.outputColorSpace,stencilBuffer:v.stencil,resolveDepthBuffer:d.ignoreDepthValues===!1,resolveStencilBuffer:d.ignoreDepthValues===!1})}y.isXRRenderTarget=!0,this.setFoveation(l),c=null,a=await r.requestReferenceSpace(o),X.setContext(r),X.start(),i.isPresenting=!0,i.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(r!==null)return r.environmentBlendMode},this.getDepthTexture=function(){return p.getDepthTexture()};function B(H){for(let V=0;V<H.removed.length;V++){const j=H.removed[V],le=T.indexOf(j);le>=0&&(T[le]=null,M[le].disconnect(j))}for(let V=0;V<H.added.length;V++){const j=H.added[V];let le=T.indexOf(j);if(le===-1){for(let oe=0;oe<M.length;oe++)if(oe>=T.length){T.push(j),le=oe;break}else if(T[oe]===null){T[oe]=j,le=oe;break}if(le===-1)break}const ge=M[le];ge&&ge.connect(j)}}const q=new $,F=new $;function k(H,V,j){q.setFromMatrixPosition(V.matrixWorld),F.setFromMatrixPosition(j.matrixWorld);const le=q.distanceTo(F),ge=V.projectionMatrix.elements,oe=j.projectionMatrix.elements,te=ge[14]/(ge[10]-1),xe=ge[14]/(ge[10]+1),Ae=(ge[9]+1)/ge[5],Te=(ge[9]-1)/ge[5],ye=(ge[8]-1)/ge[0],Ue=(oe[8]+1)/oe[0],me=te*ye,ke=te*Ue,G=le/(-ye+Ue),fe=G*-ye;if(V.matrixWorld.decompose(H.position,H.quaternion,H.scale),H.translateX(fe),H.translateZ(G),H.matrixWorld.compose(H.position,H.quaternion,H.scale),H.matrixWorldInverse.copy(H.matrixWorld).invert(),ge[10]===-1)H.projectionMatrix.copy(V.projectionMatrix),H.projectionMatrixInverse.copy(V.projectionMatrixInverse);else{const Fe=te+G,we=xe+G,he=me-fe,Re=ke+(le-fe),D=Ae*xe/we*Fe,E=Te*xe/we*Fe;H.projectionMatrix.makePerspective(he,Re,D,E,Fe,we),H.projectionMatrixInverse.copy(H.projectionMatrix).invert()}}function U(H,V){V===null?H.matrixWorld.copy(H.matrix):H.matrixWorld.multiplyMatrices(V.matrixWorld,H.matrix),H.matrixWorldInverse.copy(H.matrixWorld).invert()}this.updateCamera=function(H){if(r===null)return;let V=H.near,j=H.far;p.texture!==null&&(p.depthNear>0&&(V=p.depthNear),p.depthFar>0&&(j=p.depthFar)),R.near=A.near=x.near=V,R.far=A.far=x.far=j,(L!==R.near||I!==R.far)&&(r.updateRenderState({depthNear:R.near,depthFar:R.far}),L=R.near,I=R.far),R.layers.mask=H.layers.mask|6,x.layers.mask=R.layers.mask&-5,A.layers.mask=R.layers.mask&-3;const le=H.parent,ge=R.cameras;U(R,le);for(let oe=0;oe<ge.length;oe++)U(ge[oe],le);ge.length===2?k(R,x,A):R.projectionMatrix.copy(x.projectionMatrix),z(H,R,le)};function z(H,V,j){j===null?H.matrix.copy(V.matrixWorld):(H.matrix.copy(j.matrixWorld),H.matrix.invert(),H.matrix.multiply(V.matrixWorld)),H.matrix.decompose(H.position,H.quaternion,H.scale),H.updateMatrixWorld(!0),H.projectionMatrix.copy(V.projectionMatrix),H.projectionMatrixInverse.copy(V.projectionMatrixInverse),H.isPerspectiveCamera&&(H.fov=dh*2*Math.atan(1/H.projectionMatrix.elements[5]),H.zoom=1)}this.getCamera=function(){return R},this.getFoveation=function(){if(!(h===null&&d===null))return l},this.setFoveation=function(H){l=H,h!==null&&(h.fixedFoveation=H),d!==null&&d.fixedFoveation!==void 0&&(d.fixedFoveation=H)},this.hasDepthSensing=function(){return p.texture!==null},this.getDepthSensingMesh=function(){return p.getMesh(R)},this.getCameraTexture=function(H){return _[H]};let K=null;function Z(H,V){if(u=V.getViewerPose(c||a),m=V,u!==null){const j=u.views;d!==null&&(e.setRenderTargetFramebuffer(y,d.framebuffer),e.setRenderTarget(y));let le=!1;j.length!==R.cameras.length&&(R.cameras.length=0,le=!0);for(let xe=0;xe<j.length;xe++){const Ae=j[xe];let Te=null;if(d!==null)Te=d.getViewport(Ae);else{const Ue=f.getViewSubImage(h,Ae);Te=Ue.viewport,xe===0&&(e.setRenderTargetTextures(y,Ue.colorTexture,Ue.depthStencilTexture),e.setRenderTarget(y))}let ye=P[xe];ye===void 0&&(ye=new Gn,ye.layers.enable(xe),ye.viewport=new Ut,P[xe]=ye),ye.matrix.fromArray(Ae.transform.matrix),ye.matrix.decompose(ye.position,ye.quaternion,ye.scale),ye.projectionMatrix.fromArray(Ae.projectionMatrix),ye.projectionMatrixInverse.copy(ye.projectionMatrix).invert(),ye.viewport.set(Te.x,Te.y,Te.width,Te.height),xe===0&&(R.matrix.copy(ye.matrix),R.matrix.decompose(R.position,R.quaternion,R.scale)),le===!0&&R.cameras.push(ye)}const ge=r.enabledFeatures;if(ge&&ge.includes("depth-sensing")&&r.depthUsage=="gpu-optimized"&&g){f=i.getBinding();const xe=f.getDepthInformation(j[0]);xe&&xe.isValid&&xe.texture&&p.init(xe,r.renderState)}if(ge&&ge.includes("camera-access")&&g){e.state.unbindTexture(),f=i.getBinding();for(let xe=0;xe<j.length;xe++){const Ae=j[xe].camera;if(Ae){let Te=_[Ae];Te||(Te=new Ym,_[Ae]=Te);const ye=f.getCameraImage(Ae);Te.sourceTexture=ye}}}}for(let j=0;j<M.length;j++){const le=T[j],ge=M[j];le!==null&&ge!==void 0&&ge.update(le,V,c||a)}K&&K(H,V),V.detectedPlanes&&i.dispatchEvent({type:"planesdetected",data:V}),m=null}const X=new Qm;X.setAnimationLoop(Z),this.setAnimationLoop=function(H){K=H},this.dispose=function(){}}}const US=new zt,a0=new it;a0.set(-1,0,0,0,1,0,0,0,1);function LS(n,e){function t(p,_){p.matrixAutoUpdate===!0&&p.updateMatrix(),_.value.copy(p.matrix)}function i(p,_){_.color.getRGB(p.fogColor.value,qm(n)),_.isFog?(p.fogNear.value=_.near,p.fogFar.value=_.far):_.isFogExp2&&(p.fogDensity.value=_.density)}function r(p,_,v,S,y){_.isNodeMaterial?_.uniformsNeedUpdate=!1:_.isMeshBasicMaterial?s(p,_):_.isMeshLambertMaterial?(s(p,_),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)):_.isMeshToonMaterial?(s(p,_),f(p,_)):_.isMeshPhongMaterial?(s(p,_),u(p,_),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)):_.isMeshStandardMaterial?(s(p,_),h(p,_),_.isMeshPhysicalMaterial&&d(p,_,y)):_.isMeshMatcapMaterial?(s(p,_),m(p,_)):_.isMeshDepthMaterial?s(p,_):_.isMeshDistanceMaterial?(s(p,_),g(p,_)):_.isMeshNormalMaterial?s(p,_):_.isLineBasicMaterial?(a(p,_),_.isLineDashedMaterial&&o(p,_)):_.isPointsMaterial?l(p,_,v,S):_.isSpriteMaterial?c(p,_):_.isShadowMaterial?(p.color.value.copy(_.color),p.opacity.value=_.opacity):_.isShaderMaterial&&(_.uniformsNeedUpdate=!1)}function s(p,_){p.opacity.value=_.opacity,_.color&&p.diffuse.value.copy(_.color),_.emissive&&p.emissive.value.copy(_.emissive).multiplyScalar(_.emissiveIntensity),_.map&&(p.map.value=_.map,t(_.map,p.mapTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.bumpMap&&(p.bumpMap.value=_.bumpMap,t(_.bumpMap,p.bumpMapTransform),p.bumpScale.value=_.bumpScale,_.side===an&&(p.bumpScale.value*=-1)),_.normalMap&&(p.normalMap.value=_.normalMap,t(_.normalMap,p.normalMapTransform),p.normalScale.value.copy(_.normalScale),_.side===an&&p.normalScale.value.negate()),_.displacementMap&&(p.displacementMap.value=_.displacementMap,t(_.displacementMap,p.displacementMapTransform),p.displacementScale.value=_.displacementScale,p.displacementBias.value=_.displacementBias),_.emissiveMap&&(p.emissiveMap.value=_.emissiveMap,t(_.emissiveMap,p.emissiveMapTransform)),_.specularMap&&(p.specularMap.value=_.specularMap,t(_.specularMap,p.specularMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest);const v=e.get(_),S=v.envMap,y=v.envMapRotation;S&&(p.envMap.value=S,p.envMapRotation.value.setFromMatrix4(US.makeRotationFromEuler(y)).transpose(),S.isCubeTexture&&S.isRenderTargetTexture===!1&&p.envMapRotation.value.premultiply(a0),p.reflectivity.value=_.reflectivity,p.ior.value=_.ior,p.refractionRatio.value=_.refractionRatio),_.lightMap&&(p.lightMap.value=_.lightMap,p.lightMapIntensity.value=_.lightMapIntensity,t(_.lightMap,p.lightMapTransform)),_.aoMap&&(p.aoMap.value=_.aoMap,p.aoMapIntensity.value=_.aoMapIntensity,t(_.aoMap,p.aoMapTransform))}function a(p,_){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,_.map&&(p.map.value=_.map,t(_.map,p.mapTransform))}function o(p,_){p.dashSize.value=_.dashSize,p.totalSize.value=_.dashSize+_.gapSize,p.scale.value=_.scale}function l(p,_,v,S){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,p.size.value=_.size*v,p.scale.value=S*.5,_.map&&(p.map.value=_.map,t(_.map,p.uvTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest)}function c(p,_){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,p.rotation.value=_.rotation,_.map&&(p.map.value=_.map,t(_.map,p.mapTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest)}function u(p,_){p.specular.value.copy(_.specular),p.shininess.value=Math.max(_.shininess,1e-4)}function f(p,_){_.gradientMap&&(p.gradientMap.value=_.gradientMap)}function h(p,_){p.metalness.value=_.metalness,_.metalnessMap&&(p.metalnessMap.value=_.metalnessMap,t(_.metalnessMap,p.metalnessMapTransform)),p.roughness.value=_.roughness,_.roughnessMap&&(p.roughnessMap.value=_.roughnessMap,t(_.roughnessMap,p.roughnessMapTransform)),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)}function d(p,_,v){p.ior.value=_.ior,_.sheen>0&&(p.sheenColor.value.copy(_.sheenColor).multiplyScalar(_.sheen),p.sheenRoughness.value=_.sheenRoughness,_.sheenColorMap&&(p.sheenColorMap.value=_.sheenColorMap,t(_.sheenColorMap,p.sheenColorMapTransform)),_.sheenRoughnessMap&&(p.sheenRoughnessMap.value=_.sheenRoughnessMap,t(_.sheenRoughnessMap,p.sheenRoughnessMapTransform))),_.clearcoat>0&&(p.clearcoat.value=_.clearcoat,p.clearcoatRoughness.value=_.clearcoatRoughness,_.clearcoatMap&&(p.clearcoatMap.value=_.clearcoatMap,t(_.clearcoatMap,p.clearcoatMapTransform)),_.clearcoatRoughnessMap&&(p.clearcoatRoughnessMap.value=_.clearcoatRoughnessMap,t(_.clearcoatRoughnessMap,p.clearcoatRoughnessMapTransform)),_.clearcoatNormalMap&&(p.clearcoatNormalMap.value=_.clearcoatNormalMap,t(_.clearcoatNormalMap,p.clearcoatNormalMapTransform),p.clearcoatNormalScale.value.copy(_.clearcoatNormalScale),_.side===an&&p.clearcoatNormalScale.value.negate())),_.dispersion>0&&(p.dispersion.value=_.dispersion),_.iridescence>0&&(p.iridescence.value=_.iridescence,p.iridescenceIOR.value=_.iridescenceIOR,p.iridescenceThicknessMinimum.value=_.iridescenceThicknessRange[0],p.iridescenceThicknessMaximum.value=_.iridescenceThicknessRange[1],_.iridescenceMap&&(p.iridescenceMap.value=_.iridescenceMap,t(_.iridescenceMap,p.iridescenceMapTransform)),_.iridescenceThicknessMap&&(p.iridescenceThicknessMap.value=_.iridescenceThicknessMap,t(_.iridescenceThicknessMap,p.iridescenceThicknessMapTransform))),_.transmission>0&&(p.transmission.value=_.transmission,p.transmissionSamplerMap.value=v.texture,p.transmissionSamplerSize.value.set(v.width,v.height),_.transmissionMap&&(p.transmissionMap.value=_.transmissionMap,t(_.transmissionMap,p.transmissionMapTransform)),p.thickness.value=_.thickness,_.thicknessMap&&(p.thicknessMap.value=_.thicknessMap,t(_.thicknessMap,p.thicknessMapTransform)),p.attenuationDistance.value=_.attenuationDistance,p.attenuationColor.value.copy(_.attenuationColor)),_.anisotropy>0&&(p.anisotropyVector.value.set(_.anisotropy*Math.cos(_.anisotropyRotation),_.anisotropy*Math.sin(_.anisotropyRotation)),_.anisotropyMap&&(p.anisotropyMap.value=_.anisotropyMap,t(_.anisotropyMap,p.anisotropyMapTransform))),p.specularIntensity.value=_.specularIntensity,p.specularColor.value.copy(_.specularColor),_.specularColorMap&&(p.specularColorMap.value=_.specularColorMap,t(_.specularColorMap,p.specularColorMapTransform)),_.specularIntensityMap&&(p.specularIntensityMap.value=_.specularIntensityMap,t(_.specularIntensityMap,p.specularIntensityMapTransform))}function m(p,_){_.matcap&&(p.matcap.value=_.matcap)}function g(p,_){const v=e.get(_).light;p.referencePosition.value.setFromMatrixPosition(v.matrixWorld),p.nearDistance.value=v.shadow.camera.near,p.farDistance.value=v.shadow.camera.far}return{refreshFogUniforms:i,refreshMaterialUniforms:r}}function IS(n,e,t,i){let r={},s={},a=[];const o=n.getParameter(n.MAX_UNIFORM_BUFFER_BINDINGS);function l(v,S){const y=S.program;i.uniformBlockBinding(v,y)}function c(v,S){let y=r[v.id];y===void 0&&(m(v),y=u(v),r[v.id]=y,v.addEventListener("dispose",p));const M=S.program;i.updateUBOMapping(v,M);const T=e.render.frame;s[v.id]!==T&&(h(v),s[v.id]=T)}function u(v){const S=f();v.__bindingPointIndex=S;const y=n.createBuffer(),M=v.__size,T=v.usage;return n.bindBuffer(n.UNIFORM_BUFFER,y),n.bufferData(n.UNIFORM_BUFFER,M,T),n.bindBuffer(n.UNIFORM_BUFFER,null),n.bindBufferBase(n.UNIFORM_BUFFER,S,y),y}function f(){for(let v=0;v<o;v++)if(a.indexOf(v)===-1)return a.push(v),v;return pt("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function h(v){const S=r[v.id],y=v.uniforms,M=v.__cache;n.bindBuffer(n.UNIFORM_BUFFER,S);for(let T=0,w=y.length;T<w;T++){const b=Array.isArray(y[T])?y[T]:[y[T]];for(let x=0,A=b.length;x<A;x++){const P=b[x];if(d(P,T,x,M)===!0){const R=P.__offset,L=Array.isArray(P.value)?P.value:[P.value];let I=0;for(let N=0;N<L.length;N++){const O=L[N],B=g(O);typeof O=="number"||typeof O=="boolean"?(P.__data[0]=O,n.bufferSubData(n.UNIFORM_BUFFER,R+I,P.__data)):O.isMatrix3?(P.__data[0]=O.elements[0],P.__data[1]=O.elements[1],P.__data[2]=O.elements[2],P.__data[3]=0,P.__data[4]=O.elements[3],P.__data[5]=O.elements[4],P.__data[6]=O.elements[5],P.__data[7]=0,P.__data[8]=O.elements[6],P.__data[9]=O.elements[7],P.__data[10]=O.elements[8],P.__data[11]=0):ArrayBuffer.isView(O)?P.__data.set(new O.constructor(O.buffer,O.byteOffset,P.__data.length)):(O.toArray(P.__data,I),I+=B.storage/Float32Array.BYTES_PER_ELEMENT)}n.bufferSubData(n.UNIFORM_BUFFER,R,P.__data)}}}n.bindBuffer(n.UNIFORM_BUFFER,null)}function d(v,S,y,M){const T=v.value,w=S+"_"+y;if(M[w]===void 0)return typeof T=="number"||typeof T=="boolean"?M[w]=T:ArrayBuffer.isView(T)?M[w]=T.slice():M[w]=T.clone(),!0;{const b=M[w];if(typeof T=="number"||typeof T=="boolean"){if(b!==T)return M[w]=T,!0}else{if(ArrayBuffer.isView(T))return!0;if(b.equals(T)===!1)return b.copy(T),!0}}return!1}function m(v){const S=v.uniforms;let y=0;const M=16;for(let w=0,b=S.length;w<b;w++){const x=Array.isArray(S[w])?S[w]:[S[w]];for(let A=0,P=x.length;A<P;A++){const R=x[A],L=Array.isArray(R.value)?R.value:[R.value];for(let I=0,N=L.length;I<N;I++){const O=L[I],B=g(O),q=y%M,F=q%B.boundary,k=q+F;y+=F,k!==0&&M-k<B.storage&&(y+=M-k),R.__data=new Float32Array(B.storage/Float32Array.BYTES_PER_ELEMENT),R.__offset=y,y+=B.storage}}}const T=y%M;return T>0&&(y+=M-T),v.__size=y,v.__cache={},this}function g(v){const S={boundary:0,storage:0};return typeof v=="number"||typeof v=="boolean"?(S.boundary=4,S.storage=4):v.isVector2?(S.boundary=8,S.storage=8):v.isVector3||v.isColor?(S.boundary=16,S.storage=12):v.isVector4?(S.boundary=16,S.storage=16):v.isMatrix3?(S.boundary=48,S.storage=48):v.isMatrix4?(S.boundary=64,S.storage=64):v.isTexture?Je("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(v)?(S.boundary=16,S.storage=v.byteLength):Je("WebGLRenderer: Unsupported uniform value type.",v),S}function p(v){const S=v.target;S.removeEventListener("dispose",p);const y=a.indexOf(S.__bindingPointIndex);a.splice(y,1),n.deleteBuffer(r[S.id]),delete r[S.id],delete s[S.id]}function _(){for(const v in r)n.deleteBuffer(r[v]);a=[],r={},s={}}return{bind:l,update:c,dispose:_}}const FS=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]);let yi=null;function NS(){return yi===null&&(yi=new Tv(FS,16,16,$r,Yi),yi.name="DFG_LUT",yi.minFilter=Gt,yi.magFilter=Gt,yi.wrapS=Vi,yi.wrapT=Vi,yi.generateMipmaps=!1,yi.needsUpdate=!0),yi}class OS{constructor(e={}){const{canvas:t=ev(),context:i=null,depth:r=!0,stencil:s=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:u="default",failIfMajorPerformanceCaveat:f=!1,reversedDepthBuffer:h=!1,outputBufferType:d=Yt}=e;this.isWebGLRenderer=!0;let m;if(i!==null){if(typeof WebGLRenderingContext<"u"&&i instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");m=i.getContextAttributes().alpha}else m=a;const g=d,p=new Set([$h,Zh,Kh]),_=new Set([Yt,Ui,ka,zs,Yh,qh]),v=new Uint32Array(4),S=new Int32Array(4),y=new $;let M=null,T=null;const w=[],b=[];let x=null;this.domElement=t,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=Di,this.toneMappingExposure=1,this.transmissionResolutionScale=1;const A=this;let P=!1,R=null;this._outputColorSpace=Et;let L=0,I=0,N=null,O=-1,B=null;const q=new Ut,F=new Ut;let k=null;const U=new ut(0);let z=0,K=t.width,Z=t.height,X=1,H=null,V=null;const j=new Ut(0,0,K,Z),le=new Ut(0,0,K,Z);let ge=!1;const oe=new Xm;let te=!1,xe=!1;const Ae=new zt,Te=new $,ye=new Ut,Ue={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let me=!1;function ke(){return N===null?X:1}let G=i;function fe(C,J){return t.getContext(C,J)}try{const C={alpha:!0,depth:r,stencil:s,antialias:o,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:u,failIfMajorPerformanceCaveat:f};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${Ka}`),t.addEventListener("webglcontextlost",ce,!1),t.addEventListener("webglcontextrestored",Ne,!1),t.addEventListener("webglcontextcreationerror",Ze,!1),G===null){const J="webgl2";if(G=fe(J,C),G===null)throw fe(J)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(C){throw pt("WebGLRenderer: "+C.message),C}let Fe,we,he,Re,D,E,W,Q,ue,ve,Me,ee,se,de,De,be,Ee,He,Le,Ye,Y,_e,re;function Pe(){Fe=new Ny(G),Fe.init(),Y=new AS(G,Fe),we=new Ry(G,Fe,e,Y),he=new ES(G,Fe),we.reversedDepthBuffer&&h&&he.buffers.depth.setReversed(!0),Re=new ky(G),D=new hS,E=new wS(G,Fe,he,D,we,Y,Re),W=new Fy(A),Q=new Vv(G),_e=new wy(G,Q),ue=new Oy(G,Q,Re,_e),ve=new Gy(G,ue,Q,_e,Re),He=new zy(G,we,E),De=new Cy(D),Me=new uS(A,W,Fe,we,_e,De),ee=new LS(A,D),se=new dS,de=new xS(Fe),Ee=new Ey(A,W,he,ve,m,l),be=new TS(A,ve,we),re=new IS(G,Re,we,he),Le=new Ay(G,Fe,Re),Ye=new By(G,Fe,Re),Re.programs=Me.programs,A.capabilities=we,A.extensions=Fe,A.properties=D,A.renderLists=se,A.shadowMap=be,A.state=he,A.info=Re}Pe(),g!==Yt&&(x=new Vy(g,t.width,t.height,r,s));const Se=new DS(A,G);this.xr=Se,this.getContext=function(){return G},this.getContextAttributes=function(){return G.getContextAttributes()},this.forceContextLoss=function(){const C=Fe.get("WEBGL_lose_context");C&&C.loseContext()},this.forceContextRestore=function(){const C=Fe.get("WEBGL_lose_context");C&&C.restoreContext()},this.getPixelRatio=function(){return X},this.setPixelRatio=function(C){C!==void 0&&(X=C,this.setSize(K,Z,!1))},this.getSize=function(C){return C.set(K,Z)},this.setSize=function(C,J,ae=!0){if(Se.isPresenting){Je("WebGLRenderer: Can't change size while VR device is presenting.");return}K=C,Z=J,t.width=Math.floor(C*X),t.height=Math.floor(J*X),ae===!0&&(t.style.width=C+"px",t.style.height=J+"px"),x!==null&&x.setSize(t.width,t.height),this.setViewport(0,0,C,J)},this.getDrawingBufferSize=function(C){return C.set(K*X,Z*X).floor()},this.setDrawingBufferSize=function(C,J,ae){K=C,Z=J,X=ae,t.width=Math.floor(C*ae),t.height=Math.floor(J*ae),this.setViewport(0,0,C,J)},this.setEffects=function(C){if(g===Yt){pt("THREE.WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(C){for(let J=0;J<C.length;J++)if(C[J].isOutputPass===!0){Je("THREE.WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}x.setEffects(C||[])},this.getCurrentViewport=function(C){return C.copy(q)},this.getViewport=function(C){return C.copy(j)},this.setViewport=function(C,J,ae,ne){C.isVector4?j.set(C.x,C.y,C.z,C.w):j.set(C,J,ae,ne),he.viewport(q.copy(j).multiplyScalar(X).round())},this.getScissor=function(C){return C.copy(le)},this.setScissor=function(C,J,ae,ne){C.isVector4?le.set(C.x,C.y,C.z,C.w):le.set(C,J,ae,ne),he.scissor(F.copy(le).multiplyScalar(X).round())},this.getScissorTest=function(){return ge},this.setScissorTest=function(C){he.setScissorTest(ge=C)},this.setOpaqueSort=function(C){H=C},this.setTransparentSort=function(C){V=C},this.getClearColor=function(C){return C.copy(Ee.getClearColor())},this.setClearColor=function(){Ee.setClearColor(...arguments)},this.getClearAlpha=function(){return Ee.getClearAlpha()},this.setClearAlpha=function(){Ee.setClearAlpha(...arguments)},this.clear=function(C=!0,J=!0,ae=!0){let ne=0;if(C){let ie=!1;if(N!==null){const Be=N.texture.format;ie=p.has(Be)}if(ie){const Be=N.texture.type,Ve=_.has(Be),Oe=Ee.getClearColor(),je=Ee.getClearAlpha(),qe=Oe.r,tt=Oe.g,nt=Oe.b;Ve?(v[0]=qe,v[1]=tt,v[2]=nt,v[3]=je,G.clearBufferuiv(G.COLOR,0,v)):(S[0]=qe,S[1]=tt,S[2]=nt,S[3]=je,G.clearBufferiv(G.COLOR,0,S))}else ne|=G.COLOR_BUFFER_BIT}J&&(ne|=G.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),ae&&(ne|=G.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),ne!==0&&G.clear(ne)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(C){C.setRenderer(this),R=C},this.dispose=function(){t.removeEventListener("webglcontextlost",ce,!1),t.removeEventListener("webglcontextrestored",Ne,!1),t.removeEventListener("webglcontextcreationerror",Ze,!1),Ee.dispose(),se.dispose(),de.dispose(),D.dispose(),W.dispose(),ve.dispose(),_e.dispose(),re.dispose(),Me.dispose(),Se.dispose(),Se.removeEventListener("sessionstart",_i),Se.removeEventListener("sessionend",Kn),Ft.stop()};function ce(C){C.preventDefault(),pl("WebGLRenderer: Context Lost."),P=!0}function Ne(){pl("WebGLRenderer: Context Restored."),P=!1;const C=Re.autoReset,J=be.enabled,ae=be.autoUpdate,ne=be.needsUpdate,ie=be.type;Pe(),Re.autoReset=C,be.enabled=J,be.autoUpdate=ae,be.needsUpdate=ne,be.type=ie}function Ze(C){pt("WebGLRenderer: A WebGL context could not be created. Reason: ",C.statusMessage)}function ot(C){const J=C.target;J.removeEventListener("dispose",ot),et(J)}function et(C){Vt(C),D.remove(C)}function Vt(C){const J=D.get(C).programs;J!==void 0&&(J.forEach(function(ae){Me.releaseProgram(ae)}),C.isShaderMaterial&&Me.releaseShaderCache(C))}this.renderBufferDirect=function(C,J,ae,ne,ie,Be){J===null&&(J=Ue);const Ve=ie.isMesh&&ie.matrixWorld.determinant()<0,Oe=as(C,J,ae,ne,ie);he.setMaterial(ne,Ve);let je=ae.index,qe=1;if(ne.wireframe===!0){if(je=ue.getWireframeAttribute(ae),je===void 0)return;qe=2}const tt=ae.drawRange,nt=ae.attributes.position;let Ke=tt.start*qe,ht=(tt.start+tt.count)*qe;Be!==null&&(Ke=Math.max(Ke,Be.start*qe),ht=Math.min(ht,(Be.start+Be.count)*qe)),je!==null?(Ke=Math.max(Ke,0),ht=Math.min(ht,je.count)):nt!=null&&(Ke=Math.max(Ke,0),ht=Math.min(ht,nt.count));const Pt=ht-Ke;if(Pt<0||Pt===1/0)return;_e.setup(ie,ne,Oe,ae,je);let Ct,_t=Le;if(je!==null&&(Ct=Q.get(je),_t=Ye,_t.setIndex(Ct)),ie.isMesh)ne.wireframe===!0?(he.setLineWidth(ne.wireframeLinewidth*ke()),_t.setMode(G.LINES)):_t.setMode(G.TRIANGLES);else if(ie.isLine){let wt=ne.linewidth;wt===void 0&&(wt=1),he.setLineWidth(wt*ke()),ie.isLineSegments?_t.setMode(G.LINES):ie.isLineLoop?_t.setMode(G.LINE_LOOP):_t.setMode(G.LINE_STRIP)}else ie.isPoints?_t.setMode(G.POINTS):ie.isSprite&&_t.setMode(G.TRIANGLES);if(ie.isBatchedMesh)if(Fe.get("WEBGL_multi_draw"))_t.renderMultiDraw(ie._multiDrawStarts,ie._multiDrawCounts,ie._multiDrawCount);else{const wt=ie._multiDrawStarts,We=ie._multiDrawCounts,nn=ie._multiDrawCount,at=je?Q.get(je).bytesPerElement:1,xn=D.get(ne).currentProgram.getUniforms();for(let yn=0;yn<nn;yn++)xn.setValue(G,"_gl_DrawID",yn),_t.render(wt[yn]/at,We[yn])}else if(ie.isInstancedMesh)_t.renderInstances(Ke,Pt,ie.count);else if(ae.isInstancedBufferGeometry){const wt=ae._maxInstanceCount!==void 0?ae._maxInstanceCount:1/0,We=Math.min(ae.instanceCount,wt);_t.renderInstances(Ke,Pt,We)}else _t.render(Ke,Pt)};function Kt(C,J,ae){C.transparent===!0&&C.side===Rn&&C.forceSinglePass===!1?(C.side=an,C.needsUpdate=!0,Ii(C,J,ae),C.side=ji,C.needsUpdate=!0,Ii(C,J,ae),C.side=Rn):Ii(C,J,ae)}this.compile=function(C,J,ae=null){ae===null&&(ae=C),T=de.get(ae),T.init(J),b.push(T),ae.traverseVisible(function(ie){ie.isLight&&ie.layers.test(J.layers)&&(T.pushLight(ie),ie.castShadow&&T.pushShadow(ie))}),C!==ae&&C.traverseVisible(function(ie){ie.isLight&&ie.layers.test(J.layers)&&(T.pushLight(ie),ie.castShadow&&T.pushShadow(ie))}),T.setupLights();const ne=new Set;return C.traverse(function(ie){if(!(ie.isMesh||ie.isPoints||ie.isLine||ie.isSprite))return;const Be=ie.material;if(Be)if(Array.isArray(Be))for(let Ve=0;Ve<Be.length;Ve++){const Oe=Be[Ve];Kt(Oe,ae,ie),ne.add(Oe)}else Kt(Be,ae,ie),ne.add(Be)}),T=b.pop(),ne},this.compileAsync=function(C,J,ae=null){const ne=this.compile(C,J,ae);return new Promise(ie=>{function Be(){if(ne.forEach(function(Ve){D.get(Ve).currentProgram.isReady()&&ne.delete(Ve)}),ne.size===0){ie(C);return}setTimeout(Be,10)}Fe.get("KHR_parallel_shader_compile")!==null?Be():setTimeout(Be,10)})};let Fn=null;function gi(C){Fn&&Fn(C)}function _i(){Ft.stop()}function Kn(){Ft.start()}const Ft=new Qm;Ft.setAnimationLoop(gi),typeof self<"u"&&Ft.setContext(self),this.setAnimationLoop=function(C){Fn=C,Se.setAnimationLoop(C),C===null?Ft.stop():Ft.start()},Se.addEventListener("sessionstart",_i),Se.addEventListener("sessionend",Kn),this.render=function(C,J){if(J!==void 0&&J.isCamera!==!0){pt("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(P===!0)return;R!==null&&R.renderStart(C,J);const ae=Se.enabled===!0&&Se.isPresenting===!0,ne=x!==null&&(N===null||ae)&&x.begin(A,N);if(C.matrixWorldAutoUpdate===!0&&C.updateMatrixWorld(),J.parent===null&&J.matrixWorldAutoUpdate===!0&&J.updateMatrixWorld(),Se.enabled===!0&&Se.isPresenting===!0&&(x===null||x.isCompositing()===!1)&&(Se.cameraAutoUpdate===!0&&Se.updateCamera(J),J=Se.getCamera()),C.isScene===!0&&C.onBeforeRender(A,C,J,N),T=de.get(C,b.length),T.init(J),T.state.textureUnits=E.getTextureUnits(),b.push(T),Ae.multiplyMatrices(J.projectionMatrix,J.matrixWorldInverse),oe.setFromProjectionMatrix(Ae,Ri,J.reversedDepth),xe=this.localClippingEnabled,te=De.init(this.clippingPlanes,xe),M=se.get(C,w.length),M.init(),w.push(M),Se.enabled===!0&&Se.isPresenting===!0){const Ve=A.xr.getDepthSensingMesh();Ve!==null&&ni(Ve,J,-1/0,A.sortObjects)}ni(C,J,0,A.sortObjects),M.finish(),A.sortObjects===!0&&M.sort(H,V),me=Se.enabled===!1||Se.isPresenting===!1||Se.hasDepthSensing()===!1,me&&Ee.addToRenderList(M,C),this.info.render.frame++,te===!0&&De.beginShadows();const ie=T.state.shadowsArray;if(be.render(ie,C,J),te===!0&&De.endShadows(),this.info.autoReset===!0&&this.info.reset(),(ne&&x.hasRenderPass())===!1){const Ve=M.opaque,Oe=M.transmissive;if(T.setupLights(),J.isArrayCamera){const je=J.cameras;if(Oe.length>0)for(let qe=0,tt=je.length;qe<tt;qe++){const nt=je[qe];is(Ve,Oe,C,nt)}me&&Ee.render(C);for(let qe=0,tt=je.length;qe<tt;qe++){const nt=je[qe];na(M,C,nt,nt.viewport)}}else Oe.length>0&&is(Ve,Oe,C,J),me&&Ee.render(C),na(M,C,J)}N!==null&&I===0&&(E.updateMultisampleRenderTarget(N),E.updateRenderTargetMipmap(N)),ne&&x.end(A),C.isScene===!0&&C.onAfterRender(A,C,J),_e.resetDefaultState(),O=-1,B=null,b.pop(),b.length>0?(T=b[b.length-1],E.setTextureUnits(T.state.textureUnits),te===!0&&De.setGlobalState(A.clippingPlanes,T.state.camera)):T=null,w.pop(),w.length>0?M=w[w.length-1]:M=null,R!==null&&R.renderEnd()};function ni(C,J,ae,ne){if(C.visible===!1)return;if(C.layers.test(J.layers)){if(C.isGroup)ae=C.renderOrder;else if(C.isLOD)C.autoUpdate===!0&&C.update(J);else if(C.isLightProbeGrid)T.pushLightProbeGrid(C);else if(C.isLight)T.pushLight(C),C.castShadow&&T.pushShadow(C);else if(C.isSprite){if(!C.frustumCulled||oe.intersectsSprite(C)){ne&&ye.setFromMatrixPosition(C.matrixWorld).applyMatrix4(Ae);const Ve=ve.update(C),Oe=C.material;Oe.visible&&M.push(C,Ve,Oe,ae,ye.z,null)}}else if((C.isMesh||C.isLine||C.isPoints)&&(!C.frustumCulled||oe.intersectsObject(C))){const Ve=ve.update(C),Oe=C.material;if(ne&&(C.boundingSphere!==void 0?(C.boundingSphere===null&&C.computeBoundingSphere(),ye.copy(C.boundingSphere.center)):(Ve.boundingSphere===null&&Ve.computeBoundingSphere(),ye.copy(Ve.boundingSphere.center)),ye.applyMatrix4(C.matrixWorld).applyMatrix4(Ae)),Array.isArray(Oe)){const je=Ve.groups;for(let qe=0,tt=je.length;qe<tt;qe++){const nt=je[qe],Ke=Oe[nt.materialIndex];Ke&&Ke.visible&&M.push(C,Ve,Ke,ae,ye.z,nt)}}else Oe.visible&&M.push(C,Ve,Oe,ae,ye.z,null)}}const Be=C.children;for(let Ve=0,Oe=Be.length;Ve<Oe;Ve++)ni(Be[Ve],J,ae,ne)}function na(C,J,ae,ne){const{opaque:ie,transmissive:Be,transparent:Ve}=C;T.setupLightsView(ae),te===!0&&De.setGlobalState(A.clippingPlanes,ae),ne&&he.viewport(q.copy(ne)),ie.length>0&&rs(ie,J,ae),Be.length>0&&rs(Be,J,ae),Ve.length>0&&rs(Ve,J,ae),he.buffers.depth.setTest(!0),he.buffers.depth.setMask(!0),he.buffers.color.setMask(!0),he.setPolygonOffset(!1)}function is(C,J,ae,ne){if((ae.isScene===!0?ae.overrideMaterial:null)!==null)return;if(T.state.transmissionRenderTarget[ne.id]===void 0){const Ke=Fe.has("EXT_color_buffer_half_float")||Fe.has("EXT_color_buffer_float");T.state.transmissionRenderTarget[ne.id]=new Jt(1,1,{generateMipmaps:!0,type:Ke?Yi:Yt,minFilter:zr,samples:Math.max(4,we.samples),stencilBuffer:s,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:ft.workingColorSpace})}const Be=T.state.transmissionRenderTarget[ne.id],Ve=ne.viewport||q;Be.setSize(Ve.z*A.transmissionResolutionScale,Ve.w*A.transmissionResolutionScale);const Oe=A.getRenderTarget(),je=A.getActiveCubeFace(),qe=A.getActiveMipmapLevel();A.setRenderTarget(Be),A.getClearColor(U),z=A.getClearAlpha(),z<1&&A.setClearColor(16777215,.5),A.clear(),me&&Ee.render(ae);const tt=A.toneMapping;A.toneMapping=Di;const nt=ne.viewport;if(ne.viewport!==void 0&&(ne.viewport=void 0),T.setupLightsView(ne),te===!0&&De.setGlobalState(A.clippingPlanes,ne),rs(C,ae,ne),E.updateMultisampleRenderTarget(Be),E.updateRenderTargetMipmap(Be),Fe.has("WEBGL_multisampled_render_to_texture")===!1){let Ke=!1;for(let ht=0,Pt=J.length;ht<Pt;ht++){const Ct=J[ht],{object:_t,geometry:wt,material:We,group:nn}=Ct;if(We.side===Rn&&_t.layers.test(ne.layers)){const at=We.side;We.side=an,We.needsUpdate=!0,ia(_t,ae,ne,wt,We,nn),We.side=at,We.needsUpdate=!0,Ke=!0}}Ke===!0&&(E.updateMultisampleRenderTarget(Be),E.updateRenderTargetMipmap(Be))}A.setRenderTarget(Oe,je,qe),A.setClearColor(U,z),nt!==void 0&&(ne.viewport=nt),A.toneMapping=tt}function rs(C,J,ae){const ne=J.isScene===!0?J.overrideMaterial:null;for(let ie=0,Be=C.length;ie<Be;ie++){const Ve=C[ie],{object:Oe,geometry:je,group:qe}=Ve;let tt=Ve.material;tt.allowOverride===!0&&ne!==null&&(tt=ne),Oe.layers.test(ae.layers)&&ia(Oe,J,ae,je,tt,qe)}}function ia(C,J,ae,ne,ie,Be){C.onBeforeRender(A,J,ae,ne,ie,Be),C.modelViewMatrix.multiplyMatrices(ae.matrixWorldInverse,C.matrixWorld),C.normalMatrix.getNormalMatrix(C.modelViewMatrix),ie.onBeforeRender(A,J,ae,ne,C,Be),ie.transparent===!0&&ie.side===Rn&&ie.forceSinglePass===!1?(ie.side=an,ie.needsUpdate=!0,A.renderBufferDirect(ae,J,ne,ie,C,Be),ie.side=ji,ie.needsUpdate=!0,A.renderBufferDirect(ae,J,ne,ie,C,Be),ie.side=Rn):A.renderBufferDirect(ae,J,ne,ie,C,Be),C.onAfterRender(A,J,ae,ne,ie,Be)}function Ii(C,J,ae){J.isScene!==!0&&(J=Ue);const ne=D.get(C),ie=T.state.lights,Be=T.state.shadowsArray,Ve=ie.state.version,Oe=Me.getParameters(C,ie.state,Be,J,ae,T.state.lightProbeGridArray),je=Me.getProgramCacheKey(Oe);let qe=ne.programs;ne.environment=C.isMeshStandardMaterial||C.isMeshLambertMaterial||C.isMeshPhongMaterial?J.environment:null,ne.fog=J.fog;const tt=C.isMeshStandardMaterial||C.isMeshLambertMaterial&&!C.envMap||C.isMeshPhongMaterial&&!C.envMap;ne.envMap=W.get(C.envMap||ne.environment,tt),ne.envMapRotation=ne.environment!==null&&C.envMap===null?J.environmentRotation:C.envMapRotation,qe===void 0&&(C.addEventListener("dispose",ot),qe=new Map,ne.programs=qe);let nt=qe.get(je);if(nt!==void 0){if(ne.currentProgram===nt&&ne.lightsStateVersion===Ve)return no(C,Oe),nt}else Oe.uniforms=Me.getUniforms(C),R!==null&&C.isNodeMaterial&&R.build(C,ae,Oe),C.onBeforeCompile(Oe,A),nt=Me.acquireProgram(Oe,je),qe.set(je,nt),ne.uniforms=Oe.uniforms;const Ke=ne.uniforms;return(!C.isShaderMaterial&&!C.isRawShaderMaterial||C.clipping===!0)&&(Ke.clippingPlanes=De.uniform),no(C,Oe),ne.needsLights=sa(C),ne.lightsStateVersion=Ve,ne.needsLights&&(Ke.ambientLightColor.value=ie.state.ambient,Ke.lightProbe.value=ie.state.probe,Ke.directionalLights.value=ie.state.directional,Ke.directionalLightShadows.value=ie.state.directionalShadow,Ke.spotLights.value=ie.state.spot,Ke.spotLightShadows.value=ie.state.spotShadow,Ke.rectAreaLights.value=ie.state.rectArea,Ke.ltc_1.value=ie.state.rectAreaLTC1,Ke.ltc_2.value=ie.state.rectAreaLTC2,Ke.pointLights.value=ie.state.point,Ke.pointLightShadows.value=ie.state.pointShadow,Ke.hemisphereLights.value=ie.state.hemi,Ke.directionalShadowMatrix.value=ie.state.directionalShadowMatrix,Ke.spotLightMatrix.value=ie.state.spotLightMatrix,Ke.spotLightMap.value=ie.state.spotLightMap,Ke.pointShadowMatrix.value=ie.state.pointShadowMatrix),ne.lightProbeGrid=T.state.lightProbeGridArray.length>0,ne.currentProgram=nt,ne.uniformsList=null,nt}function ss(C){if(C.uniformsList===null){const J=C.currentProgram.getUniforms();C.uniformsList=Qo.seqWithValue(J.seq,C.uniforms)}return C.uniformsList}function no(C,J){const ae=D.get(C);ae.outputColorSpace=J.outputColorSpace,ae.batching=J.batching,ae.batchingColor=J.batchingColor,ae.instancing=J.instancing,ae.instancingColor=J.instancingColor,ae.instancingMorph=J.instancingMorph,ae.skinning=J.skinning,ae.morphTargets=J.morphTargets,ae.morphNormals=J.morphNormals,ae.morphColors=J.morphColors,ae.morphTargetsCount=J.morphTargetsCount,ae.numClippingPlanes=J.numClippingPlanes,ae.numIntersection=J.numClipIntersection,ae.vertexAlphas=J.vertexAlphas,ae.vertexTangents=J.vertexTangents,ae.toneMapping=J.toneMapping}function io(C,J){if(C.length===0)return null;if(C.length===1)return C[0].texture!==null?C[0]:null;y.setFromMatrixPosition(J.matrixWorld);for(let ae=0,ne=C.length;ae<ne;ae++){const ie=C[ae];if(ie.texture!==null&&ie.boundingBox.containsPoint(y))return ie}return null}function as(C,J,ae,ne,ie){J.isScene!==!0&&(J=Ue),E.resetTextureUnits();const Be=J.fog,Ve=ne.isMeshStandardMaterial||ne.isMeshLambertMaterial||ne.isMeshPhongMaterial?J.environment:null,Oe=N===null?A.outputColorSpace:N.isXRRenderTarget===!0?N.texture.colorSpace:ft.workingColorSpace,je=ne.isMeshStandardMaterial||ne.isMeshLambertMaterial&&!ne.envMap||ne.isMeshPhongMaterial&&!ne.envMap,qe=W.get(ne.envMap||Ve,je),tt=ne.vertexColors===!0&&!!ae.attributes.color&&ae.attributes.color.itemSize===4,nt=!!ae.attributes.tangent&&(!!ne.normalMap||ne.anisotropy>0),Ke=!!ae.morphAttributes.position,ht=!!ae.morphAttributes.normal,Pt=!!ae.morphAttributes.color;let Ct=Di;ne.toneMapped&&(N===null||N.isXRRenderTarget===!0)&&(Ct=A.toneMapping);const _t=ae.morphAttributes.position||ae.morphAttributes.normal||ae.morphAttributes.color,wt=_t!==void 0?_t.length:0,We=D.get(ne),nn=T.state.lights;if(te===!0&&(xe===!0||C!==B)){const mt=C===B&&ne.id===O;De.setState(ne,C,mt)}let at=!1;ne.version===We.__version?(We.needsLights&&We.lightsStateVersion!==nn.state.version||We.outputColorSpace!==Oe||ie.isBatchedMesh&&We.batching===!1||!ie.isBatchedMesh&&We.batching===!0||ie.isBatchedMesh&&We.batchingColor===!0&&ie.colorTexture===null||ie.isBatchedMesh&&We.batchingColor===!1&&ie.colorTexture!==null||ie.isInstancedMesh&&We.instancing===!1||!ie.isInstancedMesh&&We.instancing===!0||ie.isSkinnedMesh&&We.skinning===!1||!ie.isSkinnedMesh&&We.skinning===!0||ie.isInstancedMesh&&We.instancingColor===!0&&ie.instanceColor===null||ie.isInstancedMesh&&We.instancingColor===!1&&ie.instanceColor!==null||ie.isInstancedMesh&&We.instancingMorph===!0&&ie.morphTexture===null||ie.isInstancedMesh&&We.instancingMorph===!1&&ie.morphTexture!==null||We.envMap!==qe||ne.fog===!0&&We.fog!==Be||We.numClippingPlanes!==void 0&&(We.numClippingPlanes!==De.numPlanes||We.numIntersection!==De.numIntersection)||We.vertexAlphas!==tt||We.vertexTangents!==nt||We.morphTargets!==Ke||We.morphNormals!==ht||We.morphColors!==Pt||We.toneMapping!==Ct||We.morphTargetsCount!==wt||!!We.lightProbeGrid!=T.state.lightProbeGridArray.length>0)&&(at=!0):(at=!0,We.__version=ne.version);let xn=We.currentProgram;at===!0&&(xn=Ii(ne,J,ie),R&&ne.isNodeMaterial&&R.onUpdateProgram(ne,xn,We));let yn=!1,Nn=!1,vi=!1;const xt=xn.getUniforms(),Lt=We.uniforms;if(he.useProgram(xn.program)&&(yn=!0,Nn=!0,vi=!0),ne.id!==O&&(O=ne.id,Nn=!0),We.needsLights){const mt=io(T.state.lightProbeGridArray,ie);We.lightProbeGrid!==mt&&(We.lightProbeGrid=mt,Nn=!0)}if(yn||B!==C){he.buffers.depth.getReversed()&&C.reversedDepth!==!0&&(C._reversedDepth=!0,C.updateProjectionMatrix()),xt.setValue(G,"projectionMatrix",C.projectionMatrix),xt.setValue(G,"viewMatrix",C.matrixWorldInverse);const ii=xt.map.cameraPosition;ii!==void 0&&ii.setValue(G,Te.setFromMatrixPosition(C.matrixWorld)),we.logarithmicDepthBuffer&&xt.setValue(G,"logDepthBufFC",2/(Math.log(C.far+1)/Math.LN2)),(ne.isMeshPhongMaterial||ne.isMeshToonMaterial||ne.isMeshLambertMaterial||ne.isMeshBasicMaterial||ne.isMeshStandardMaterial||ne.isShaderMaterial)&&xt.setValue(G,"isOrthographic",C.isOrthographicCamera===!0),B!==C&&(B=C,Nn=!0,vi=!0)}if(We.needsLights&&(nn.state.directionalShadowMap.length>0&&xt.setValue(G,"directionalShadowMap",nn.state.directionalShadowMap,E),nn.state.spotShadowMap.length>0&&xt.setValue(G,"spotShadowMap",nn.state.spotShadowMap,E),nn.state.pointShadowMap.length>0&&xt.setValue(G,"pointShadowMap",nn.state.pointShadowMap,E)),ie.isSkinnedMesh){xt.setOptional(G,ie,"bindMatrix"),xt.setOptional(G,ie,"bindMatrixInverse");const mt=ie.skeleton;mt&&(mt.boneTexture===null&&mt.computeBoneTexture(),xt.setValue(G,"boneTexture",mt.boneTexture,E))}ie.isBatchedMesh&&(xt.setOptional(G,ie,"batchingTexture"),xt.setValue(G,"batchingTexture",ie._matricesTexture,E),xt.setOptional(G,ie,"batchingIdTexture"),xt.setValue(G,"batchingIdTexture",ie._indirectTexture,E),xt.setOptional(G,ie,"batchingColorTexture"),ie._colorsTexture!==null&&xt.setValue(G,"batchingColorTexture",ie._colorsTexture,E));const Zn=ae.morphAttributes;if((Zn.position!==void 0||Zn.normal!==void 0||Zn.color!==void 0)&&He.update(ie,ae,xn),(Nn||We.receiveShadow!==ie.receiveShadow)&&(We.receiveShadow=ie.receiveShadow,xt.setValue(G,"receiveShadow",ie.receiveShadow)),(ne.isMeshStandardMaterial||ne.isMeshLambertMaterial||ne.isMeshPhongMaterial)&&ne.envMap===null&&J.environment!==null&&(Lt.envMapIntensity.value=J.environmentIntensity),Lt.dfgLUT!==void 0&&(Lt.dfgLUT.value=NS()),Nn){if(xt.setValue(G,"toneMappingExposure",A.toneMappingExposure),We.needsLights&&ra(Lt,vi),Be&&ne.fog===!0&&ee.refreshFogUniforms(Lt,Be),ee.refreshMaterialUniforms(Lt,ne,X,Z,T.state.transmissionRenderTarget[C.id]),We.needsLights&&We.lightProbeGrid){const mt=We.lightProbeGrid;Lt.probesSH.value=mt.texture,Lt.probesMin.value.copy(mt.boundingBox.min),Lt.probesMax.value.copy(mt.boundingBox.max),Lt.probesResolution.value.copy(mt.resolution)}Qo.upload(G,ss(We),Lt,E)}if(ne.isShaderMaterial&&ne.uniformsNeedUpdate===!0&&(Qo.upload(G,ss(We),Lt,E),ne.uniformsNeedUpdate=!1),ne.isSpriteMaterial&&xt.setValue(G,"center",ie.center),xt.setValue(G,"modelViewMatrix",ie.modelViewMatrix),xt.setValue(G,"normalMatrix",ie.normalMatrix),xt.setValue(G,"modelMatrix",ie.matrixWorld),ne.uniformsGroups!==void 0){const mt=ne.uniformsGroups;for(let ii=0,ri=mt.length;ii<ri;ii++){const Fi=mt[ii];re.update(Fi,xn),re.bind(Fi,xn)}}return xn}function ra(C,J){C.ambientLightColor.needsUpdate=J,C.lightProbe.needsUpdate=J,C.directionalLights.needsUpdate=J,C.directionalLightShadows.needsUpdate=J,C.pointLights.needsUpdate=J,C.pointLightShadows.needsUpdate=J,C.spotLights.needsUpdate=J,C.spotLightShadows.needsUpdate=J,C.rectAreaLights.needsUpdate=J,C.hemisphereLights.needsUpdate=J}function sa(C){return C.isMeshLambertMaterial||C.isMeshToonMaterial||C.isMeshPhongMaterial||C.isMeshStandardMaterial||C.isShadowMaterial||C.isShaderMaterial&&C.lights===!0}this.getActiveCubeFace=function(){return L},this.getActiveMipmapLevel=function(){return I},this.getRenderTarget=function(){return N},this.setRenderTargetTextures=function(C,J,ae){const ne=D.get(C);ne.__autoAllocateDepthBuffer=C.resolveDepthBuffer===!1,ne.__autoAllocateDepthBuffer===!1&&(ne.__useRenderToTexture=!1),D.get(C.texture).__webglTexture=J,D.get(C.depthTexture).__webglTexture=ne.__autoAllocateDepthBuffer?void 0:ae,ne.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(C,J){const ae=D.get(C);ae.__webglFramebuffer=J,ae.__useDefaultFramebuffer=J===void 0};const $e=G.createFramebuffer();this.setRenderTarget=function(C,J=0,ae=0){N=C,L=J,I=ae;let ne=null,ie=!1,Be=!1;if(C){const Oe=D.get(C);if(Oe.__useDefaultFramebuffer!==void 0){he.bindFramebuffer(G.FRAMEBUFFER,Oe.__webglFramebuffer),q.copy(C.viewport),F.copy(C.scissor),k=C.scissorTest,he.viewport(q),he.scissor(F),he.setScissorTest(k),O=-1;return}else if(Oe.__webglFramebuffer===void 0)E.setupRenderTarget(C);else if(Oe.__hasExternalTextures)E.rebindTextures(C,D.get(C.texture).__webglTexture,D.get(C.depthTexture).__webglTexture);else if(C.depthBuffer){const tt=C.depthTexture;if(Oe.__boundDepthTexture!==tt){if(tt!==null&&D.has(tt)&&(C.width!==tt.image.width||C.height!==tt.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");E.setupDepthRenderbuffer(C)}}const je=C.texture;(je.isData3DTexture||je.isDataArrayTexture||je.isCompressedArrayTexture)&&(Be=!0);const qe=D.get(C).__webglFramebuffer;C.isWebGLCubeRenderTarget?(Array.isArray(qe[J])?ne=qe[J][ae]:ne=qe[J],ie=!0):C.samples>0&&E.useMultisampledRTT(C)===!1?ne=D.get(C).__webglMultisampledFramebuffer:Array.isArray(qe)?ne=qe[ae]:ne=qe,q.copy(C.viewport),F.copy(C.scissor),k=C.scissorTest}else q.copy(j).multiplyScalar(X).floor(),F.copy(le).multiplyScalar(X).floor(),k=ge;if(ae!==0&&(ne=$e),he.bindFramebuffer(G.FRAMEBUFFER,ne)&&he.drawBuffers(C,ne),he.viewport(q),he.scissor(F),he.setScissorTest(k),ie){const Oe=D.get(C.texture);G.framebufferTexture2D(G.FRAMEBUFFER,G.COLOR_ATTACHMENT0,G.TEXTURE_CUBE_MAP_POSITIVE_X+J,Oe.__webglTexture,ae)}else if(Be){const Oe=J;for(let je=0;je<C.textures.length;je++){const qe=D.get(C.textures[je]);G.framebufferTextureLayer(G.FRAMEBUFFER,G.COLOR_ATTACHMENT0+je,qe.__webglTexture,ae,Oe)}}else if(C!==null&&ae!==0){const Oe=D.get(C.texture);G.framebufferTexture2D(G.FRAMEBUFFER,G.COLOR_ATTACHMENT0,G.TEXTURE_2D,Oe.__webglTexture,ae)}O=-1},this.readRenderTargetPixels=function(C,J,ae,ne,ie,Be,Ve,Oe=0){if(!(C&&C.isWebGLRenderTarget)){pt("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let je=D.get(C).__webglFramebuffer;if(C.isWebGLCubeRenderTarget&&Ve!==void 0&&(je=je[Ve]),je){he.bindFramebuffer(G.FRAMEBUFFER,je);try{const qe=C.textures[Oe],tt=qe.format,nt=qe.type;if(C.textures.length>1&&G.readBuffer(G.COLOR_ATTACHMENT0+Oe),!we.textureFormatReadable(tt)){pt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!we.textureTypeReadable(nt)){pt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}J>=0&&J<=C.width-ne&&ae>=0&&ae<=C.height-ie&&G.readPixels(J,ae,ne,ie,Y.convert(tt),Y.convert(nt),Be)}finally{const qe=N!==null?D.get(N).__webglFramebuffer:null;he.bindFramebuffer(G.FRAMEBUFFER,qe)}}},this.readRenderTargetPixelsAsync=async function(C,J,ae,ne,ie,Be,Ve,Oe=0){if(!(C&&C.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let je=D.get(C).__webglFramebuffer;if(C.isWebGLCubeRenderTarget&&Ve!==void 0&&(je=je[Ve]),je)if(J>=0&&J<=C.width-ne&&ae>=0&&ae<=C.height-ie){he.bindFramebuffer(G.FRAMEBUFFER,je);const qe=C.textures[Oe],tt=qe.format,nt=qe.type;if(C.textures.length>1&&G.readBuffer(G.COLOR_ATTACHMENT0+Oe),!we.textureFormatReadable(tt))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!we.textureTypeReadable(nt))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");const Ke=G.createBuffer();G.bindBuffer(G.PIXEL_PACK_BUFFER,Ke),G.bufferData(G.PIXEL_PACK_BUFFER,Be.byteLength,G.STREAM_READ),G.readPixels(J,ae,ne,ie,Y.convert(tt),Y.convert(nt),0);const ht=N!==null?D.get(N).__webglFramebuffer:null;he.bindFramebuffer(G.FRAMEBUFFER,ht);const Pt=G.fenceSync(G.SYNC_GPU_COMMANDS_COMPLETE,0);return G.flush(),await tv(G,Pt,4),G.bindBuffer(G.PIXEL_PACK_BUFFER,Ke),G.getBufferSubData(G.PIXEL_PACK_BUFFER,0,Be),G.deleteBuffer(Ke),G.deleteSync(Pt),Be}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(C,J=null,ae=0){const ne=Math.pow(2,-ae),ie=Math.floor(C.image.width*ne),Be=Math.floor(C.image.height*ne),Ve=J!==null?J.x:0,Oe=J!==null?J.y:0;E.setTexture2D(C,0),G.copyTexSubImage2D(G.TEXTURE_2D,ae,0,0,Ve,Oe,ie,Be),he.unbindTexture()};const Rr=G.createFramebuffer(),$l=G.createFramebuffer();this.copyTextureToTexture=function(C,J,ae=null,ne=null,ie=0,Be=0){let Ve,Oe,je,qe,tt,nt,Ke,ht,Pt;const Ct=C.isCompressedTexture?C.mipmaps[Be]:C.image;if(ae!==null)Ve=ae.max.x-ae.min.x,Oe=ae.max.y-ae.min.y,je=ae.isBox3?ae.max.z-ae.min.z:1,qe=ae.min.x,tt=ae.min.y,nt=ae.isBox3?ae.min.z:0;else{const Lt=Math.pow(2,-ie);Ve=Math.floor(Ct.width*Lt),Oe=Math.floor(Ct.height*Lt),C.isDataArrayTexture?je=Ct.depth:C.isData3DTexture?je=Math.floor(Ct.depth*Lt):je=1,qe=0,tt=0,nt=0}ne!==null?(Ke=ne.x,ht=ne.y,Pt=ne.z):(Ke=0,ht=0,Pt=0);const _t=Y.convert(J.format),wt=Y.convert(J.type);let We;J.isData3DTexture?(E.setTexture3D(J,0),We=G.TEXTURE_3D):J.isDataArrayTexture||J.isCompressedArrayTexture?(E.setTexture2DArray(J,0),We=G.TEXTURE_2D_ARRAY):(E.setTexture2D(J,0),We=G.TEXTURE_2D),he.activeTexture(G.TEXTURE0),he.pixelStorei(G.UNPACK_FLIP_Y_WEBGL,J.flipY),he.pixelStorei(G.UNPACK_PREMULTIPLY_ALPHA_WEBGL,J.premultiplyAlpha),he.pixelStorei(G.UNPACK_ALIGNMENT,J.unpackAlignment);const nn=he.getParameter(G.UNPACK_ROW_LENGTH),at=he.getParameter(G.UNPACK_IMAGE_HEIGHT),xn=he.getParameter(G.UNPACK_SKIP_PIXELS),yn=he.getParameter(G.UNPACK_SKIP_ROWS),Nn=he.getParameter(G.UNPACK_SKIP_IMAGES);he.pixelStorei(G.UNPACK_ROW_LENGTH,Ct.width),he.pixelStorei(G.UNPACK_IMAGE_HEIGHT,Ct.height),he.pixelStorei(G.UNPACK_SKIP_PIXELS,qe),he.pixelStorei(G.UNPACK_SKIP_ROWS,tt),he.pixelStorei(G.UNPACK_SKIP_IMAGES,nt);const vi=C.isDataArrayTexture||C.isData3DTexture,xt=J.isDataArrayTexture||J.isData3DTexture;if(C.isDepthTexture){const Lt=D.get(C),Zn=D.get(J),mt=D.get(Lt.__renderTarget),ii=D.get(Zn.__renderTarget);he.bindFramebuffer(G.READ_FRAMEBUFFER,mt.__webglFramebuffer),he.bindFramebuffer(G.DRAW_FRAMEBUFFER,ii.__webglFramebuffer);for(let ri=0;ri<je;ri++)vi&&(G.framebufferTextureLayer(G.READ_FRAMEBUFFER,G.COLOR_ATTACHMENT0,D.get(C).__webglTexture,ie,nt+ri),G.framebufferTextureLayer(G.DRAW_FRAMEBUFFER,G.COLOR_ATTACHMENT0,D.get(J).__webglTexture,Be,Pt+ri)),G.blitFramebuffer(qe,tt,Ve,Oe,Ke,ht,Ve,Oe,G.DEPTH_BUFFER_BIT,G.NEAREST);he.bindFramebuffer(G.READ_FRAMEBUFFER,null),he.bindFramebuffer(G.DRAW_FRAMEBUFFER,null)}else if(ie!==0||C.isRenderTargetTexture||D.has(C)){const Lt=D.get(C),Zn=D.get(J);he.bindFramebuffer(G.READ_FRAMEBUFFER,Rr),he.bindFramebuffer(G.DRAW_FRAMEBUFFER,$l);for(let mt=0;mt<je;mt++)vi?G.framebufferTextureLayer(G.READ_FRAMEBUFFER,G.COLOR_ATTACHMENT0,Lt.__webglTexture,ie,nt+mt):G.framebufferTexture2D(G.READ_FRAMEBUFFER,G.COLOR_ATTACHMENT0,G.TEXTURE_2D,Lt.__webglTexture,ie),xt?G.framebufferTextureLayer(G.DRAW_FRAMEBUFFER,G.COLOR_ATTACHMENT0,Zn.__webglTexture,Be,Pt+mt):G.framebufferTexture2D(G.DRAW_FRAMEBUFFER,G.COLOR_ATTACHMENT0,G.TEXTURE_2D,Zn.__webglTexture,Be),ie!==0?G.blitFramebuffer(qe,tt,Ve,Oe,Ke,ht,Ve,Oe,G.COLOR_BUFFER_BIT,G.NEAREST):xt?G.copyTexSubImage3D(We,Be,Ke,ht,Pt+mt,qe,tt,Ve,Oe):G.copyTexSubImage2D(We,Be,Ke,ht,qe,tt,Ve,Oe);he.bindFramebuffer(G.READ_FRAMEBUFFER,null),he.bindFramebuffer(G.DRAW_FRAMEBUFFER,null)}else xt?C.isDataTexture||C.isData3DTexture?G.texSubImage3D(We,Be,Ke,ht,Pt,Ve,Oe,je,_t,wt,Ct.data):J.isCompressedArrayTexture?G.compressedTexSubImage3D(We,Be,Ke,ht,Pt,Ve,Oe,je,_t,Ct.data):G.texSubImage3D(We,Be,Ke,ht,Pt,Ve,Oe,je,_t,wt,Ct):C.isDataTexture?G.texSubImage2D(G.TEXTURE_2D,Be,Ke,ht,Ve,Oe,_t,wt,Ct.data):C.isCompressedTexture?G.compressedTexSubImage2D(G.TEXTURE_2D,Be,Ke,ht,Ct.width,Ct.height,_t,Ct.data):G.texSubImage2D(G.TEXTURE_2D,Be,Ke,ht,Ve,Oe,_t,wt,Ct);he.pixelStorei(G.UNPACK_ROW_LENGTH,nn),he.pixelStorei(G.UNPACK_IMAGE_HEIGHT,at),he.pixelStorei(G.UNPACK_SKIP_PIXELS,xn),he.pixelStorei(G.UNPACK_SKIP_ROWS,yn),he.pixelStorei(G.UNPACK_SKIP_IMAGES,Nn),Be===0&&J.generateMipmaps&&G.generateMipmap(We),he.unbindTexture()},this.initRenderTarget=function(C){D.get(C).__webglFramebuffer===void 0&&E.setupRenderTarget(C)},this.initTexture=function(C){C.isCubeTexture?E.setTextureCube(C,0):C.isData3DTexture?E.setTexture3D(C,0):C.isDataArrayTexture||C.isCompressedArrayTexture?E.setTexture2DArray(C,0):E.setTexture2D(C,0),he.unbindTexture()},this.resetState=function(){L=0,I=0,N=null,he.reset(),_e.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Ri}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const t=this.getContext();t.drawingBufferColorSpace=ft._getDrawingBufferColorSpace(e),t.unpackColorSpace=ft._getUnpackColorSpace()}}function BS(){var n=Object.create(null);function e(r,s){var a=r.id,o=r.name,l=r.dependencies;l===void 0&&(l=[]);var c=r.init;c===void 0&&(c=function(){});var u=r.getTransferables;if(u===void 0&&(u=null),!n[a])try{l=l.map(function(h){return h&&h.isWorkerModule&&(e(h,function(d){if(d instanceof Error)throw d}),h=n[h.id].value),h}),c=i("<"+o+">.init",c),u&&(u=i("<"+o+">.getTransferables",u));var f=null;typeof c=="function"?f=c.apply(void 0,l):console.error("worker module init function failed to rehydrate"),n[a]={id:a,value:f,getTransferables:u},s(f)}catch(h){h&&h.noLog||console.error(h),s(h)}}function t(r,s){var a,o=r.id,l=r.args;(!n[o]||typeof n[o].value!="function")&&s(new Error("Worker module "+o+": not found or its 'init' did not return a function"));try{var c=(a=n[o]).value.apply(a,l);c&&typeof c.then=="function"?c.then(u,function(f){return s(f instanceof Error?f:new Error(""+f))}):u(c)}catch(f){s(f)}function u(f){try{var h=n[o].getTransferables&&n[o].getTransferables(f);(!h||!Array.isArray(h)||!h.length)&&(h=void 0),s(f,h)}catch(d){console.error(d),s(d)}}}function i(r,s){var a=void 0;self.troikaDefine=function(l){return a=l};var o=URL.createObjectURL(new Blob(["/** "+r.replace(/\*/g,"")+` **/

troikaDefine(
`+s+`
)`],{type:"application/javascript"}));try{importScripts(o)}catch(l){console.error(l)}return URL.revokeObjectURL(o),delete self.troikaDefine,a}self.addEventListener("message",function(r){var s=r.data,a=s.messageId,o=s.action,l=s.data;try{o==="registerModule"&&e(l,function(c){c instanceof Error?postMessage({messageId:a,success:!1,error:c.message}):postMessage({messageId:a,success:!0,result:{isCallable:typeof c=="function"}})}),o==="callModule"&&t(l,function(c,u){c instanceof Error?postMessage({messageId:a,success:!1,error:c.message}):postMessage({messageId:a,success:!0,result:c},u||void 0)})}catch(c){postMessage({messageId:a,success:!1,error:c.stack})}})}function kS(n){var e=function(){for(var t=[],i=arguments.length;i--;)t[i]=arguments[i];return e._getInitResult().then(function(r){if(typeof r=="function")return r.apply(void 0,t);throw new Error("Worker module function was called but `init` did not return a callable function")})};return e._getInitResult=function(){var t=n.dependencies,i=n.init;t=Array.isArray(t)?t.map(function(s){return s&&(s=s.onMainThread||s,s._getInitResult&&(s=s._getInitResult())),s}):[];var r=Promise.all(t).then(function(s){return i.apply(null,s)});return e._getInitResult=function(){return r},r},e}var o0=function(){var n=!1;if(typeof window<"u"&&typeof window.document<"u")try{var e=new Worker(URL.createObjectURL(new Blob([""],{type:"application/javascript"})));e.terminate(),n=!0}catch(t){console.log("Troika createWorkerModule: web workers not allowed; falling back to main thread execution. Cause: ["+t.message+"]")}return o0=function(){return n},n},zS=0,GS=0,zc=!1,La=Object.create(null),Ia=Object.create(null),xh=Object.create(null);function Js(n){if((!n||typeof n.init!="function")&&!zc)throw new Error("requires `options.init` function");var e=n.dependencies,t=n.init,i=n.getTransferables,r=n.workerId,s=kS(n);r==null&&(r="#default");var a="workerModule"+ ++zS,o=n.name||a,l=null;e=e&&e.map(function(u){return typeof u=="function"&&!u.workerModuleData&&(zc=!0,u=Js({workerId:r,name:"<"+o+"> function dependency: "+u.name,init:`function(){return (
`+el(u)+`
)}`}),zc=!1),u&&u.workerModuleData&&(u=u.workerModuleData),u});function c(){for(var u=[],f=arguments.length;f--;)u[f]=arguments[f];if(!o0())return s.apply(void 0,u);if(!l){l=lp(r,"registerModule",c.workerModuleData);var h=function(){l=null,Ia[r].delete(h)};(Ia[r]||(Ia[r]=new Set)).add(h)}return l.then(function(d){var m=d.isCallable;if(m)return lp(r,"callModule",{id:a,args:u});throw new Error("Worker module function was called but `init` did not return a callable function")})}return c.workerModuleData={isWorkerModule:!0,id:a,name:o,dependencies:e,init:el(t),getTransferables:i&&el(i)},c.onMainThread=s,c}function HS(n){Ia[n]&&Ia[n].forEach(function(e){e()}),La[n]&&(La[n].terminate(),delete La[n])}function el(n){var e=n.toString();return!/^function/.test(e)&&/^\w+\s*\(/.test(e)&&(e="function "+e),e}function VS(n){var e=La[n];if(!e){var t=el(BS);e=La[n]=new Worker(URL.createObjectURL(new Blob(["/** Worker Module Bootstrap: "+n.replace(/\*/g,"")+` **/

;(`+t+")()"],{type:"application/javascript"}))),e.onmessage=function(i){var r=i.data,s=r.messageId,a=xh[s];if(!a)throw new Error("WorkerModule response with empty or unknown messageId");delete xh[s],a(r)}}return e}function lp(n,e,t){return new Promise(function(i,r){var s=++GS;xh[s]=function(a){a.success?i(a.result):r(new Error("Error in worker "+e+" call: "+a.error))},VS(n).postMessage({messageId:s,action:e,data:t})})}function l0(){var n=(function(e){function t(F,k,U,z,K,Z,X,H){var V=1-X;H.x=V*V*F+2*V*X*U+X*X*K,H.y=V*V*k+2*V*X*z+X*X*Z}function i(F,k,U,z,K,Z,X,H,V,j){var le=1-V;j.x=le*le*le*F+3*le*le*V*U+3*le*V*V*K+V*V*V*X,j.y=le*le*le*k+3*le*le*V*z+3*le*V*V*Z+V*V*V*H}function r(F,k){for(var U=/([MLQCZ])([^MLQCZ]*)/g,z,K,Z,X,H;z=U.exec(F);){var V=z[2].replace(/^\s*|\s*$/g,"").split(/[,\s]+/).map(function(j){return parseFloat(j)});switch(z[1]){case"M":X=K=V[0],H=Z=V[1];break;case"L":(V[0]!==X||V[1]!==H)&&k("L",X,H,X=V[0],H=V[1]);break;case"Q":{k("Q",X,H,X=V[2],H=V[3],V[0],V[1]);break}case"C":{k("C",X,H,X=V[4],H=V[5],V[0],V[1],V[2],V[3]);break}case"Z":(X!==K||H!==Z)&&k("L",X,H,K,Z);break}}}function s(F,k,U){U===void 0&&(U=16);var z={x:0,y:0};r(F,function(K,Z,X,H,V,j,le,ge,oe){switch(K){case"L":k(Z,X,H,V);break;case"Q":{for(var te=Z,xe=X,Ae=1;Ae<U;Ae++)t(Z,X,j,le,H,V,Ae/(U-1),z),k(te,xe,z.x,z.y),te=z.x,xe=z.y;break}case"C":{for(var Te=Z,ye=X,Ue=1;Ue<U;Ue++)i(Z,X,j,le,ge,oe,H,V,Ue/(U-1),z),k(Te,ye,z.x,z.y),Te=z.x,ye=z.y;break}}})}var a="precision highp float;attribute vec2 aUV;varying vec2 vUV;void main(){vUV=aUV;gl_Position=vec4(mix(vec2(-1.0),vec2(1.0),aUV),0.0,1.0);}",o="precision highp float;uniform sampler2D tex;varying vec2 vUV;void main(){gl_FragColor=texture2D(tex,vUV);}",l=new WeakMap,c={premultipliedAlpha:!1,preserveDrawingBuffer:!0,antialias:!1,depth:!1};function u(F,k){var U=F.getContext?F.getContext("webgl",c):F,z=l.get(U);if(!z){let le=function(Te){var ye=Z[Te];if(!ye&&(ye=Z[Te]=U.getExtension(Te),!ye))throw new Error(Te+" not supported");return ye},ge=function(Te,ye){var Ue=U.createShader(ye);return U.shaderSource(Ue,Te),U.compileShader(Ue),Ue},oe=function(Te,ye,Ue,me){if(!X[Te]){var ke={},G={},fe=U.createProgram();U.attachShader(fe,ge(ye,U.VERTEX_SHADER)),U.attachShader(fe,ge(Ue,U.FRAGMENT_SHADER)),U.linkProgram(fe),X[Te]={program:fe,transaction:function(we){U.useProgram(fe),we({setUniform:function(Re,D){for(var E=[],W=arguments.length-2;W-- >0;)E[W]=arguments[W+2];var Q=G[D]||(G[D]=U.getUniformLocation(fe,D));U["uniform"+Re].apply(U,[Q].concat(E))},setAttribute:function(Re,D,E,W,Q){var ue=ke[Re];ue||(ue=ke[Re]={buf:U.createBuffer(),loc:U.getAttribLocation(fe,Re),data:null}),U.bindBuffer(U.ARRAY_BUFFER,ue.buf),U.vertexAttribPointer(ue.loc,D,U.FLOAT,!1,0,0),U.enableVertexAttribArray(ue.loc),K?U.vertexAttribDivisor(ue.loc,W):le("ANGLE_instanced_arrays").vertexAttribDivisorANGLE(ue.loc,W),Q!==ue.data&&(U.bufferData(U.ARRAY_BUFFER,Q,E),ue.data=Q)}})}}}X[Te].transaction(me)},te=function(Te,ye){V++;try{U.activeTexture(U.TEXTURE0+V);var Ue=H[Te];Ue||(Ue=H[Te]=U.createTexture(),U.bindTexture(U.TEXTURE_2D,Ue),U.texParameteri(U.TEXTURE_2D,U.TEXTURE_MIN_FILTER,U.NEAREST),U.texParameteri(U.TEXTURE_2D,U.TEXTURE_MAG_FILTER,U.NEAREST)),U.bindTexture(U.TEXTURE_2D,Ue),ye(Ue,V)}finally{V--}},xe=function(Te,ye,Ue){var me=U.createFramebuffer();j.push(me),U.bindFramebuffer(U.FRAMEBUFFER,me),U.activeTexture(U.TEXTURE0+ye),U.bindTexture(U.TEXTURE_2D,Te),U.framebufferTexture2D(U.FRAMEBUFFER,U.COLOR_ATTACHMENT0,U.TEXTURE_2D,Te,0);try{Ue(me)}finally{U.deleteFramebuffer(me),U.bindFramebuffer(U.FRAMEBUFFER,j[--j.length-1]||null)}},Ae=function(){Z={},X={},H={},V=-1,j.length=0};var K=typeof WebGL2RenderingContext<"u"&&U instanceof WebGL2RenderingContext,Z={},X={},H={},V=-1,j=[];U.canvas.addEventListener("webglcontextlost",function(Te){Ae(),Te.preventDefault()},!1),l.set(U,z={gl:U,isWebGL2:K,getExtension:le,withProgram:oe,withTexture:te,withTextureFramebuffer:xe,handleContextLoss:Ae})}k(z)}function f(F,k,U,z,K,Z,X,H){X===void 0&&(X=15),H===void 0&&(H=null),u(F,function(V){var j=V.gl,le=V.withProgram,ge=V.withTexture;ge("copy",function(oe,te){j.texImage2D(j.TEXTURE_2D,0,j.RGBA,K,Z,0,j.RGBA,j.UNSIGNED_BYTE,k),le("copy",a,o,function(xe){var Ae=xe.setUniform,Te=xe.setAttribute;Te("aUV",2,j.STATIC_DRAW,0,new Float32Array([0,0,2,0,0,2])),Ae("1i","image",te),j.bindFramebuffer(j.FRAMEBUFFER,H||null),j.disable(j.BLEND),j.colorMask(X&8,X&4,X&2,X&1),j.viewport(U,z,K,Z),j.scissor(U,z,K,Z),j.drawArrays(j.TRIANGLES,0,3)})})})}function h(F,k,U){var z=F.width,K=F.height;u(F,function(Z){var X=Z.gl,H=new Uint8Array(z*K*4);X.readPixels(0,0,z,K,X.RGBA,X.UNSIGNED_BYTE,H),F.width=k,F.height=U,f(X,H,0,0,z,K)})}var d=Object.freeze({__proto__:null,withWebGLContext:u,renderImageData:f,resizeWebGLCanvasWithoutClearing:h});function m(F,k,U,z,K,Z){Z===void 0&&(Z=1);var X=new Uint8Array(F*k),H=z[2]-z[0],V=z[3]-z[1],j=[];s(U,function(Te,ye,Ue,me){j.push({x1:Te,y1:ye,x2:Ue,y2:me,minX:Math.min(Te,Ue),minY:Math.min(ye,me),maxX:Math.max(Te,Ue),maxY:Math.max(ye,me)})}),j.sort(function(Te,ye){return Te.maxX-ye.maxX});for(var le=0;le<F;le++)for(var ge=0;ge<k;ge++){var oe=xe(z[0]+H*(le+.5)/F,z[1]+V*(ge+.5)/k),te=Math.pow(1-Math.abs(oe)/K,Z)/2;oe<0&&(te=1-te),te=Math.max(0,Math.min(255,Math.round(te*255))),X[ge*F+le]=te}return X;function xe(Te,ye){for(var Ue=1/0,me=1/0,ke=j.length;ke--;){var G=j[ke];if(G.maxX+me<=Te)break;if(Te+me>G.minX&&ye-me<G.maxY&&ye+me>G.minY){var fe=_(Te,ye,G.x1,G.y1,G.x2,G.y2);fe<Ue&&(Ue=fe,me=Math.sqrt(Ue))}}return Ae(Te,ye)&&(me=-me),me}function Ae(Te,ye){for(var Ue=0,me=j.length;me--;){var ke=j[me];if(ke.maxX<=Te)break;var G=ke.y1>ye!=ke.y2>ye&&Te<(ke.x2-ke.x1)*(ye-ke.y1)/(ke.y2-ke.y1)+ke.x1;G&&(Ue+=ke.y1<ke.y2?1:-1)}return Ue!==0}}function g(F,k,U,z,K,Z,X,H,V,j){Z===void 0&&(Z=1),H===void 0&&(H=0),V===void 0&&(V=0),j===void 0&&(j=0),p(F,k,U,z,K,Z,X,null,H,V,j)}function p(F,k,U,z,K,Z,X,H,V,j,le){Z===void 0&&(Z=1),V===void 0&&(V=0),j===void 0&&(j=0),le===void 0&&(le=0);for(var ge=m(F,k,U,z,K,Z),oe=new Uint8Array(ge.length*4),te=0;te<ge.length;te++)oe[te*4+le]=ge[te];f(X,oe,V,j,F,k,1<<3-le,H)}function _(F,k,U,z,K,Z){var X=K-U,H=Z-z,V=X*X+H*H,j=V?Math.max(0,Math.min(1,((F-U)*X+(k-z)*H)/V)):0,le=F-(U+j*X),ge=k-(z+j*H);return le*le+ge*ge}var v=Object.freeze({__proto__:null,generate:m,generateIntoCanvas:g,generateIntoFramebuffer:p}),S="precision highp float;uniform vec4 uGlyphBounds;attribute vec2 aUV;attribute vec4 aLineSegment;varying vec4 vLineSegment;varying vec2 vGlyphXY;void main(){vLineSegment=aLineSegment;vGlyphXY=mix(uGlyphBounds.xy,uGlyphBounds.zw,aUV);gl_Position=vec4(mix(vec2(-1.0),vec2(1.0),aUV),0.0,1.0);}",y="precision highp float;uniform vec4 uGlyphBounds;uniform float uMaxDistance;uniform float uExponent;varying vec4 vLineSegment;varying vec2 vGlyphXY;float absDistToSegment(vec2 point,vec2 lineA,vec2 lineB){vec2 lineDir=lineB-lineA;float lenSq=dot(lineDir,lineDir);float t=lenSq==0.0 ? 0.0 : clamp(dot(point-lineA,lineDir)/lenSq,0.0,1.0);vec2 linePt=lineA+t*lineDir;return distance(point,linePt);}void main(){vec4 seg=vLineSegment;vec2 p=vGlyphXY;float dist=absDistToSegment(p,seg.xy,seg.zw);float val=pow(1.0-clamp(dist/uMaxDistance,0.0,1.0),uExponent)*0.5;bool crossing=(seg.y>p.y!=seg.w>p.y)&&(p.x<(seg.z-seg.x)*(p.y-seg.y)/(seg.w-seg.y)+seg.x);bool crossingUp=crossing&&vLineSegment.y<vLineSegment.w;gl_FragColor=vec4(crossingUp ? 1.0/255.0 : 0.0,crossing&&!crossingUp ? 1.0/255.0 : 0.0,0.0,val);}",M="precision highp float;uniform sampler2D tex;varying vec2 vUV;void main(){vec4 color=texture2D(tex,vUV);bool inside=color.r!=color.g;float val=inside ? 1.0-color.a : color.a;gl_FragColor=vec4(val);}",T=new Float32Array([0,0,2,0,0,2]),w=null,b=!1,x={},A=new WeakMap;function P(F){if(!b&&!N(F))throw new Error("WebGL generation not supported")}function R(F,k,U,z,K,Z,X){if(Z===void 0&&(Z=1),X===void 0&&(X=null),!X&&(X=w,!X)){var H=typeof OffscreenCanvas=="function"?new OffscreenCanvas(1,1):typeof document<"u"?document.createElement("canvas"):null;if(!H)throw new Error("OffscreenCanvas or DOM canvas not supported");X=w=H.getContext("webgl",{depth:!1})}P(X);var V=new Uint8Array(F*k*4);u(X,function(oe){var te=oe.gl,xe=oe.withTexture,Ae=oe.withTextureFramebuffer;xe("readable",function(Te,ye){te.texImage2D(te.TEXTURE_2D,0,te.RGBA,F,k,0,te.RGBA,te.UNSIGNED_BYTE,null),Ae(Te,ye,function(Ue){I(F,k,U,z,K,Z,te,Ue,0,0,0),te.readPixels(0,0,F,k,te.RGBA,te.UNSIGNED_BYTE,V)})})});for(var j=new Uint8Array(F*k),le=0,ge=0;le<V.length;le+=4)j[ge++]=V[le];return j}function L(F,k,U,z,K,Z,X,H,V,j){Z===void 0&&(Z=1),H===void 0&&(H=0),V===void 0&&(V=0),j===void 0&&(j=0),I(F,k,U,z,K,Z,X,null,H,V,j)}function I(F,k,U,z,K,Z,X,H,V,j,le){Z===void 0&&(Z=1),V===void 0&&(V=0),j===void 0&&(j=0),le===void 0&&(le=0),P(X);var ge=[];s(U,function(oe,te,xe,Ae){ge.push(oe,te,xe,Ae)}),ge=new Float32Array(ge),u(X,function(oe){var te=oe.gl,xe=oe.isWebGL2,Ae=oe.getExtension,Te=oe.withProgram,ye=oe.withTexture,Ue=oe.withTextureFramebuffer,me=oe.handleContextLoss;if(ye("rawDistances",function(ke,G){(F!==ke._lastWidth||k!==ke._lastHeight)&&te.texImage2D(te.TEXTURE_2D,0,te.RGBA,ke._lastWidth=F,ke._lastHeight=k,0,te.RGBA,te.UNSIGNED_BYTE,null),Te("main",S,y,function(fe){var Fe=fe.setAttribute,we=fe.setUniform,he=!xe&&Ae("ANGLE_instanced_arrays"),Re=!xe&&Ae("EXT_blend_minmax");Fe("aUV",2,te.STATIC_DRAW,0,T),Fe("aLineSegment",4,te.DYNAMIC_DRAW,1,ge),we.apply(void 0,["4f","uGlyphBounds"].concat(z)),we("1f","uMaxDistance",K),we("1f","uExponent",Z),Ue(ke,G,function(D){te.enable(te.BLEND),te.colorMask(!0,!0,!0,!0),te.viewport(0,0,F,k),te.scissor(0,0,F,k),te.blendFunc(te.ONE,te.ONE),te.blendEquationSeparate(te.FUNC_ADD,xe?te.MAX:Re.MAX_EXT),te.clear(te.COLOR_BUFFER_BIT),xe?te.drawArraysInstanced(te.TRIANGLES,0,3,ge.length/4):he.drawArraysInstancedANGLE(te.TRIANGLES,0,3,ge.length/4)})}),Te("post",a,M,function(fe){fe.setAttribute("aUV",2,te.STATIC_DRAW,0,T),fe.setUniform("1i","tex",G),te.bindFramebuffer(te.FRAMEBUFFER,H),te.disable(te.BLEND),te.colorMask(le===0,le===1,le===2,le===3),te.viewport(V,j,F,k),te.scissor(V,j,F,k),te.drawArrays(te.TRIANGLES,0,3)})}),te.isContextLost())throw me(),new Error("webgl context lost")})}function N(F){var k=!F||F===w?x:F.canvas||F,U=A.get(k);if(U===void 0){b=!0;var z=null;try{var K=[97,106,97,61,99,137,118,80,80,118,137,99,61,97,106,97],Z=R(4,4,"M8,8L16,8L24,24L16,24Z",[0,0,32,32],24,1,F);U=Z&&K.length===Z.length&&Z.every(function(X,H){return X===K[H]}),U||(z="bad trial run results",console.info(K,Z))}catch(X){U=!1,z=X.message}z&&console.warn("WebGL SDF generation not supported:",z),b=!1,A.set(k,U)}return U}var O=Object.freeze({__proto__:null,generate:R,generateIntoCanvas:L,generateIntoFramebuffer:I,isSupported:N});function B(F,k,U,z,K,Z){K===void 0&&(K=Math.max(z[2]-z[0],z[3]-z[1])/2),Z===void 0&&(Z=1);try{return R.apply(O,arguments)}catch(X){return console.info("WebGL SDF generation failed, falling back to JS",X),m.apply(v,arguments)}}function q(F,k,U,z,K,Z,X,H,V,j){K===void 0&&(K=Math.max(z[2]-z[0],z[3]-z[1])/2),Z===void 0&&(Z=1),H===void 0&&(H=0),V===void 0&&(V=0),j===void 0&&(j=0);try{return L.apply(O,arguments)}catch(le){return console.info("WebGL SDF generation failed, falling back to JS",le),g.apply(v,arguments)}}return e.forEachPathCommand=r,e.generate=B,e.generateIntoCanvas=q,e.javascript=v,e.pathToLineSegments=s,e.webgl=O,e.webglUtils=d,Object.defineProperty(e,"__esModule",{value:!0}),e})({});return n}function WS(){var n=(function(e){var t={R:"13k,1a,2,3,3,2+1j,ch+16,a+1,5+2,2+n,5,a,4,6+16,4+3,h+1b,4mo,179q,2+9,2+11,2i9+7y,2+68,4,3+4,5+13,4+3,2+4k,3+29,8+cf,1t+7z,w+17,3+3m,1t+3z,16o1+5r,8+30,8+mc,29+1r,29+4v,75+73",EN:"1c+9,3d+1,6,187+9,513,4+5,7+9,sf+j,175h+9,qw+q,161f+1d,4xt+a,25i+9",ES:"17,2,6dp+1,f+1,av,16vr,mx+1,4o,2",ET:"z+2,3h+3,b+1,ym,3e+1,2o,p4+1,8,6u,7c,g6,1wc,1n9+4,30+1b,2n,6d,qhx+1,h0m,a+1,49+2,63+1,4+1,6bb+3,12jj",AN:"16o+5,2j+9,2+1,35,ed,1ff2+9,87+u",CS:"18,2+1,b,2u,12k,55v,l,17v0,2,3,53,2+1,b",B:"a,3,f+2,2v,690",S:"9,2,k",WS:"c,k,4f4,1vk+a,u,1j,335",ON:"x+1,4+4,h+5,r+5,r+3,z,5+3,2+1,2+1,5,2+2,3+4,o,w,ci+1,8+d,3+d,6+8,2+g,39+1,9,6+1,2,33,b8,3+1,3c+1,7+1,5r,b,7h+3,sa+5,2,3i+6,jg+3,ur+9,2v,ij+1,9g+9,7+a,8m,4+1,49+x,14u,2+2,c+2,e+2,e+2,e+1,i+n,e+e,2+p,u+2,e+2,36+1,2+3,2+1,b,2+2,6+5,2,2,2,h+1,5+4,6+3,3+f,16+2,5+3l,3+81,1y+p,2+40,q+a,m+13,2r+ch,2+9e,75+hf,3+v,2+2w,6e+5,f+6,75+2a,1a+p,2+2g,d+5x,r+b,6+3,4+o,g,6+1,6+2,2k+1,4,2j,5h+z,1m+1,1e+f,t+2,1f+e,d+3,4o+3,2s+1,w,535+1r,h3l+1i,93+2,2s,b+1,3l+x,2v,4g+3,21+3,kz+1,g5v+1,5a,j+9,n+v,2,3,2+8,2+1,3+2,2,3,46+1,4+4,h+5,r+5,r+a,3h+2,4+6,b+4,78,1r+24,4+c,4,1hb,ey+6,103+j,16j+c,1ux+7,5+g,fsh,jdq+1t,4,57+2e,p1,1m,1m,1m,1m,4kt+1,7j+17,5+2r,d+e,3+e,2+e,2+10,m+4,w,1n+5,1q,4z+5,4b+rb,9+c,4+c,4+37,d+2g,8+b,l+b,5+1j,9+9,7+13,9+t,3+1,27+3c,2+29,2+3q,d+d,3+4,4+2,6+6,a+o,8+6,a+2,e+6,16+42,2+1i",BN:"0+8,6+d,2s+5,2+p,e,4m9,1kt+2,2b+5,5+5,17q9+v,7k,6p+8,6+1,119d+3,440+7,96s+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+75,6p+2rz,1ben+1,1ekf+1,1ekf+1",NSM:"lc+33,7o+6,7c+18,2,2+1,2+1,2,21+a,1d+k,h,2u+6,3+5,3+1,2+3,10,v+q,2k+a,1n+8,a,p+3,2+8,2+2,2+4,18+2,3c+e,2+v,1k,2,5+7,5,4+6,b+1,u,1n,5+3,9,l+1,r,3+1,1m,5+1,5+1,3+2,4,v+1,4,c+1,1m,5+4,2+1,5,l+1,n+5,2,1n,3,2+3,9,8+1,c+1,v,1q,d,1f,4,1m+2,6+2,2+3,8+1,c+1,u,1n,g+1,l+1,t+1,1m+1,5+3,9,l+1,u,21,8+2,2,2j,3+6,d+7,2r,3+8,c+5,23+1,s,2,2,1k+d,2+4,2+1,6+a,2+z,a,2v+3,2+5,2+1,3+1,q+1,5+2,h+3,e,3+1,7,g,jk+2,qb+2,u+2,u+1,v+1,1t+1,2+6,9,3+a,a,1a+2,3c+1,z,3b+2,5+1,a,7+2,64+1,3,1n,2+6,2,2,3+7,7+9,3,1d+g,1s+3,1d,2+4,2,6,15+8,d+1,x+3,3+1,2+2,1l,2+1,4,2+2,1n+7,3+1,49+2,2+c,2+6,5,7,4+1,5j+1l,2+4,k1+w,2db+2,3y,2p+v,ff+3,30+1,n9x+3,2+9,x+1,29+1,7l,4,5,q+1,6,48+1,r+h,e,13+7,q+a,1b+2,1d,3+3,3+1,14,1w+5,3+1,3+1,d,9,1c,1g,2+2,3+1,6+1,2,17+1,9,6n,3,5,fn5,ki+f,h+f,r2,6b,46+4,1af+2,2+1,6+3,15+2,5,4m+1,fy+3,as+1,4a+a,4x,1j+e,1l+2,1e+3,3+1,1y+2,11+4,2+7,1r,d+1,1h+8,b+3,3,2o+2,3,2+1,7,4h,4+7,m+1,1m+1,4,12+6,4+4,5g+7,3+2,2,o,2d+5,2,5+1,2+1,6n+3,7+1,2+1,s+1,2e+7,3,2+1,2z,2,3+5,2,2u+2,3+3,2+4,78+8,2+1,75+1,2,5,41+3,3+1,5,x+5,3+1,15+5,3+3,9,a+5,3+2,1b+c,2+1,bb+6,2+5,2d+l,3+6,2+1,2+1,3f+5,4,2+1,2+6,2,21+1,4,2,9o+1,f0c+4,1o+6,t5,1s+3,2a,f5l+1,43t+2,i+7,3+6,v+3,45+2,1j0+1i,5+1d,9,f,n+4,2+e,11t+6,2+g,3+6,2+1,2+4,7a+6,c6+3,15t+6,32+6,gzhy+6n",AL:"16w,3,2,e+1b,z+2,2+2s,g+1,8+1,b+m,2+t,s+2i,c+e,4h+f,1d+1e,1bwe+dp,3+3z,x+c,2+1,35+3y,2rm+z,5+7,b+5,dt+l,c+u,17nl+27,1t+27,4x+6n,3+d",LRO:"6ct",RLO:"6cu",LRE:"6cq",RLE:"6cr",PDF:"6cs",LRI:"6ee",RLI:"6ef",FSI:"6eg",PDI:"6eh"},i={},r={};i.L=1,r[1]="L",Object.keys(t).forEach(function(me,ke){i[me]=1<<ke+1,r[i[me]]=me}),Object.freeze(i);var s=i.LRI|i.RLI|i.FSI,a=i.L|i.R|i.AL,o=i.B|i.S|i.WS|i.ON|i.FSI|i.LRI|i.RLI|i.PDI,l=i.BN|i.RLE|i.LRE|i.RLO|i.LRO|i.PDF,c=i.S|i.WS|i.B|s|i.PDI|l,u=null;function f(){if(!u){u=new Map;var me=0;for(var ke in t)if(t.hasOwnProperty(ke))for(var G=t[ke],fe="",Fe=void 0,we=!1,he=0,Re=0;Re<=G.length+1;Re+=1){var D=G[Re];if(D!==","&&Re!==G.length)D==="+"?(we=!0,he=me=he+parseInt(fe,36),fe=""):fe+=D;else{we?Fe=me+parseInt(fe,36):(he=me=he+parseInt(fe,36),Fe=me),we=!1,fe="",he=Fe;for(var E=me;E<Fe+1;E+=1)u.set(E,i[ke])}}}}function h(me){return f(),u.get(me.codePointAt(0))||i.L}function d(me){return r[h(me)]}var m={pairs:"14>1,1e>2,u>2,2wt>1,1>1,1ge>1,1wp>1,1j>1,f>1,hm>1,1>1,u>1,u6>1,1>1,+5,28>1,w>1,1>1,+3,b8>1,1>1,+3,1>3,-1>-1,3>1,1>1,+2,1s>1,1>1,x>1,th>1,1>1,+2,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,4q>1,1e>2,u>2,2>1,+1",canonical:"6f1>-6dx,6dy>-6dx,6ec>-6ed,6ee>-6ed,6ww>2jj,-2ji>2jj,14r4>-1e7l,1e7m>-1e7l,1e7m>-1e5c,1e5d>-1e5b,1e5c>-14qx,14qy>-14qx,14vn>-1ecg,1ech>-1ecg,1edu>-1ecg,1eci>-1ecg,1eda>-1ecg,1eci>-1ecg,1eci>-168q,168r>-168q,168s>-14ye,14yf>-14ye"};function g(me,ke){var G=36,fe=0,Fe=new Map,we=ke&&new Map,he;return me.split(",").forEach(function Re(D){if(D.indexOf("+")!==-1)for(var E=+D;E--;)Re(he);else{he=D;var W=D.split(">"),Q=W[0],ue=W[1];Q=String.fromCodePoint(fe+=parseInt(Q,G)),ue=String.fromCodePoint(fe+=parseInt(ue,G)),Fe.set(Q,ue),ke&&we.set(ue,Q)}}),{map:Fe,reverseMap:we}}var p,_,v;function S(){if(!p){var me=g(m.pairs,!0),ke=me.map,G=me.reverseMap;p=ke,_=G,v=g(m.canonical,!1).map}}function y(me){return S(),p.get(me)||null}function M(me){return S(),_.get(me)||null}function T(me){return S(),v.get(me)||null}var w=i.L,b=i.R,x=i.EN,A=i.ES,P=i.ET,R=i.AN,L=i.CS,I=i.B,N=i.S,O=i.ON,B=i.BN,q=i.NSM,F=i.AL,k=i.LRO,U=i.RLO,z=i.LRE,K=i.RLE,Z=i.PDF,X=i.LRI,H=i.RLI,V=i.FSI,j=i.PDI;function le(me,ke){for(var G=125,fe=new Uint32Array(me.length),Fe=0;Fe<me.length;Fe++)fe[Fe]=h(me[Fe]);var we=new Map;function he(En,ai){var wn=fe[En];fe[En]=ai,we.set(wn,we.get(wn)-1),wn&o&&we.set(o,we.get(o)-1),we.set(ai,(we.get(ai)||0)+1),ai&o&&we.set(o,(we.get(o)||0)+1)}for(var Re=new Uint8Array(me.length),D=new Map,E=[],W=null,Q=0;Q<me.length;Q++)W||E.push(W={start:Q,end:me.length-1,level:ke==="rtl"?1:ke==="ltr"?0:Zf(Q,!1)}),fe[Q]&I&&(W.end=Q,W=null);for(var ue=K|z|U|k|s|j|Z|I,ve=function(En){return En+(En&1?1:2)},Me=function(En){return En+(En&1?2:1)},ee=0;ee<E.length;ee++){W=E[ee];var se=[{_level:W.level,_override:0,_isolate:0}],de=void 0,De=0,be=0,Ee=0;we.clear();for(var He=W.start;He<=W.end;He++){var Le=fe[He];if(de=se[se.length-1],we.set(Le,(we.get(Le)||0)+1),Le&o&&we.set(o,(we.get(o)||0)+1),Le&ue)if(Le&(K|z)){Re[He]=de._level;var Ye=(Le===K?Me:ve)(de._level);Ye<=G&&!De&&!be?se.push({_level:Ye,_override:0,_isolate:0}):De||be++}else if(Le&(U|k)){Re[He]=de._level;var Y=(Le===U?Me:ve)(de._level);Y<=G&&!De&&!be?se.push({_level:Y,_override:Le&U?b:w,_isolate:0}):De||be++}else if(Le&s){Le&V&&(Le=Zf(He+1,!0)===1?H:X),Re[He]=de._level,de._override&&he(He,de._override);var _e=(Le===H?Me:ve)(de._level);_e<=G&&De===0&&be===0?(Ee++,se.push({_level:_e,_override:0,_isolate:1,_isolInitIndex:He})):De++}else if(Le&j){if(De>0)De--;else if(Ee>0){for(be=0;!se[se.length-1]._isolate;)se.pop();var re=se[se.length-1]._isolInitIndex;re!=null&&(D.set(re,He),D.set(He,re)),se.pop(),Ee--}de=se[se.length-1],Re[He]=de._level,de._override&&he(He,de._override)}else Le&Z?(De===0&&(be>0?be--:!de._isolate&&se.length>1&&(se.pop(),de=se[se.length-1])),Re[He]=de._level):Le&I&&(Re[He]=W.level);else Re[He]=de._level,de._override&&Le!==B&&he(He,de._override)}for(var Pe=[],Se=null,ce=W.start;ce<=W.end;ce++){var Ne=fe[ce];if(!(Ne&l)){var Ze=Re[ce],ot=Ne&s,et=Ne===j;Se&&Ze===Se._level?(Se._end=ce,Se._endsWithIsolInit=ot):Pe.push(Se={_start:ce,_end:ce,_level:Ze,_startsWithPDI:et,_endsWithIsolInit:ot})}}for(var Vt=[],Kt=0;Kt<Pe.length;Kt++){var Fn=Pe[Kt];if(!Fn._startsWithPDI||Fn._startsWithPDI&&!D.has(Fn._start)){for(var gi=[Se=Fn],_i=void 0;Se&&Se._endsWithIsolInit&&(_i=D.get(Se._end))!=null;)for(var Kn=Kt+1;Kn<Pe.length;Kn++)if(Pe[Kn]._start===_i){gi.push(Se=Pe[Kn]);break}for(var Ft=[],ni=0;ni<gi.length;ni++)for(var na=gi[ni],is=na._start;is<=na._end;is++)Ft.push(is);for(var rs=Re[Ft[0]],ia=W.level,Ii=Ft[0]-1;Ii>=0;Ii--)if(!(fe[Ii]&l)){ia=Re[Ii];break}var ss=Ft[Ft.length-1],no=Re[ss],io=W.level;if(!(fe[ss]&s)){for(var as=ss+1;as<=W.end;as++)if(!(fe[as]&l)){io=Re[as];break}}Vt.push({_seqIndices:Ft,_sosType:Math.max(ia,rs)%2?b:w,_eosType:Math.max(io,no)%2?b:w})}}for(var ra=0;ra<Vt.length;ra++){var sa=Vt[ra],$e=sa._seqIndices,Rr=sa._sosType,$l=sa._eosType,C=Re[$e[0]]&1?b:w;if(we.get(q))for(var J=0;J<$e.length;J++){var ae=$e[J];if(fe[ae]&q){for(var ne=Rr,ie=J-1;ie>=0;ie--)if(!(fe[$e[ie]]&l)){ne=fe[$e[ie]];break}he(ae,ne&(s|j)?O:ne)}}if(we.get(x))for(var Be=0;Be<$e.length;Be++){var Ve=$e[Be];if(fe[Ve]&x)for(var Oe=Be-1;Oe>=-1;Oe--){var je=Oe===-1?Rr:fe[$e[Oe]];if(je&a){je===F&&he(Ve,R);break}}}if(we.get(F))for(var qe=0;qe<$e.length;qe++){var tt=$e[qe];fe[tt]&F&&he(tt,b)}if(we.get(A)||we.get(L))for(var nt=1;nt<$e.length-1;nt++){var Ke=$e[nt];if(fe[Ke]&(A|L)){for(var ht=0,Pt=0,Ct=nt-1;Ct>=0&&(ht=fe[$e[Ct]],!!(ht&l));Ct--);for(var _t=nt+1;_t<$e.length&&(Pt=fe[$e[_t]],!!(Pt&l));_t++);ht===Pt&&(fe[Ke]===A?ht===x:ht&(x|R))&&he(Ke,ht)}}if(we.get(x))for(var wt=0;wt<$e.length;wt++){var We=$e[wt];if(fe[We]&x){for(var nn=wt-1;nn>=0&&fe[$e[nn]]&(P|l);nn--)he($e[nn],x);for(wt++;wt<$e.length&&fe[$e[wt]]&(P|l|x);wt++)fe[$e[wt]]!==x&&he($e[wt],x)}}if(we.get(P)||we.get(A)||we.get(L))for(var at=0;at<$e.length;at++){var xn=$e[at];if(fe[xn]&(P|A|L)){he(xn,O);for(var yn=at-1;yn>=0&&fe[$e[yn]]&l;yn--)he($e[yn],O);for(var Nn=at+1;Nn<$e.length&&fe[$e[Nn]]&l;Nn++)he($e[Nn],O)}}if(we.get(x))for(var vi=0,xt=Rr;vi<$e.length;vi++){var Lt=$e[vi],Zn=fe[Lt];Zn&x?xt===w&&he(Lt,w):Zn&a&&(xt=Zn)}if(we.get(o)){var mt=b|x|R,ii=mt|w,ri=[];{for(var Fi=[],os=0;os<$e.length;os++)if(fe[$e[os]]&o){var aa=me[$e[os]],Gf=void 0;if(y(aa)!==null)if(Fi.length<63)Fi.push({char:aa,seqIndex:os});else break;else if((Gf=M(aa))!==null)for(var oa=Fi.length-1;oa>=0;oa--){var Jl=Fi[oa].char;if(Jl===Gf||Jl===M(T(aa))||y(T(Jl))===aa){ri.push([Fi[oa].seqIndex,os]),Fi.length=oa;break}}}ri.sort(function(En,ai){return En[0]-ai[0]})}for(var Ql=0;Ql<ri.length;Ql++){for(var Hf=ri[Ql],ro=Hf[0],ec=Hf[1],Vf=!1,si=0,tc=ro+1;tc<ec;tc++){var Wf=$e[tc];if(fe[Wf]&ii){Vf=!0;var Xf=fe[Wf]&mt?b:w;if(Xf===C){si=Xf;break}}}if(Vf&&!si){si=Rr;for(var nc=ro-1;nc>=0;nc--){var jf=$e[nc];if(fe[jf]&ii){var Yf=fe[jf]&mt?b:w;Yf!==C?si=Yf:si=C;break}}}if(si){if(fe[$e[ro]]=fe[$e[ec]]=si,si!==C){for(var la=ro+1;la<$e.length;la++)if(!(fe[$e[la]]&l)){h(me[$e[la]])&q&&(fe[$e[la]]=si);break}}if(si!==C){for(var ca=ec+1;ca<$e.length;ca++)if(!(fe[$e[ca]]&l)){h(me[$e[ca]])&q&&(fe[$e[ca]]=si);break}}}}for(var er=0;er<$e.length;er++)if(fe[$e[er]]&o){for(var qf=er,ic=er,rc=Rr,ua=er-1;ua>=0;ua--)if(fe[$e[ua]]&l)qf=ua;else{rc=fe[$e[ua]]&mt?b:w;break}for(var Kf=$l,ha=er+1;ha<$e.length;ha++)if(fe[$e[ha]]&(o|l))ic=ha;else{Kf=fe[$e[ha]]&mt?b:w;break}for(var sc=qf;sc<=ic;sc++)fe[$e[sc]]=rc===Kf?rc:C;er=ic}}}for(var On=W.start;On<=W.end;On++){var qg=Re[On],so=fe[On];if(qg&1?so&(w|x|R)&&Re[On]++:so&b?Re[On]++:so&(R|x)&&(Re[On]+=2),so&l&&(Re[On]=On===0?W.level:Re[On-1]),On===W.end||h(me[On])&(N|I))for(var ao=On;ao>=0&&h(me[ao])&c;ao--)Re[ao]=W.level}}return{levels:Re,paragraphs:E};function Zf(En,ai){for(var wn=En;wn<me.length;wn++){var tr=fe[wn];if(tr&(b|F))return 1;if(tr&(I|w)||ai&&tr===j)return 0;if(tr&s){var $f=Kg(wn);wn=$f===-1?me.length:$f}}return 0}function Kg(En){for(var ai=1,wn=En+1;wn<me.length;wn++){var tr=fe[wn];if(tr&I)break;if(tr&j){if(--ai===0)return wn}else tr&s&&ai++}return-1}}var ge="14>1,j>2,t>2,u>2,1a>g,2v3>1,1>1,1ge>1,1wd>1,b>1,1j>1,f>1,ai>3,-2>3,+1,8>1k0,-1jq>1y7,-1y6>1hf,-1he>1h6,-1h5>1ha,-1h8>1qi,-1pu>1,6>3u,-3s>7,6>1,1>1,f>1,1>1,+2,3>1,1>1,+13,4>1,1>1,6>1eo,-1ee>1,3>1mg,-1me>1mk,-1mj>1mi,-1mg>1mi,-1md>1,1>1,+2,1>10k,-103>1,1>1,4>1,5>1,1>1,+10,3>1,1>8,-7>8,+1,-6>7,+1,a>1,1>1,u>1,u6>1,1>1,+5,26>1,1>1,2>1,2>2,8>1,7>1,4>1,1>1,+5,b8>1,1>1,+3,1>3,-2>1,2>1,1>1,+2,c>1,3>1,1>1,+2,h>1,3>1,a>1,1>1,2>1,3>1,1>1,d>1,f>1,3>1,1a>1,1>1,6>1,7>1,13>1,k>1,1>1,+19,4>1,1>1,+2,2>1,1>1,+18,m>1,a>1,1>1,lk>1,1>1,4>1,2>1,f>1,3>1,1>1,+3,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,6>1,4j>1,j>2,t>2,u>2,2>1,+1",oe;function te(){if(!oe){var me=g(ge,!0),ke=me.map,G=me.reverseMap;G.forEach(function(fe,Fe){ke.set(Fe,fe)}),oe=ke}}function xe(me){return te(),oe.get(me)||null}function Ae(me,ke,G,fe){var Fe=me.length;G=Math.max(0,G==null?0:+G),fe=Math.min(Fe-1,fe==null?Fe-1:+fe);for(var we=new Map,he=G;he<=fe;he++)if(ke[he]&1){var Re=xe(me[he]);Re!==null&&we.set(he,Re)}return we}function Te(me,ke,G,fe){var Fe=me.length;G=Math.max(0,G==null?0:+G),fe=Math.min(Fe-1,fe==null?Fe-1:+fe);var we=[];return ke.paragraphs.forEach(function(he){var Re=Math.max(G,he.start),D=Math.min(fe,he.end);if(Re<D){for(var E=ke.levels.slice(Re,D+1),W=D;W>=Re&&h(me[W])&c;W--)E[W]=he.level;for(var Q=he.level,ue=1/0,ve=0;ve<E.length;ve++){var Me=E[ve];Me>Q&&(Q=Me),Me<ue&&(ue=Me|1)}for(var ee=Q;ee>=ue;ee--)for(var se=0;se<E.length;se++)if(E[se]>=ee){for(var de=se;se+1<E.length&&E[se+1]>=ee;)se++;se>de&&we.push([de+Re,se+Re])}}}),we}function ye(me,ke,G,fe){var Fe=Ue(me,ke,G,fe),we=[].concat(me);return Fe.forEach(function(he,Re){we[Re]=(ke.levels[he]&1?xe(me[he]):null)||me[he]}),we.join("")}function Ue(me,ke,G,fe){for(var Fe=Te(me,ke,G,fe),we=[],he=0;he<me.length;he++)we[he]=he;return Fe.forEach(function(Re){for(var D=Re[0],E=Re[1],W=we.slice(D,E+1),Q=W.length;Q--;)we[E-Q]=W[Q]}),we}return e.closingToOpeningBracket=M,e.getBidiCharType=h,e.getBidiCharTypeName=d,e.getCanonicalBracket=T,e.getEmbeddingLevels=le,e.getMirroredCharacter=xe,e.getMirroredCharactersMap=Ae,e.getReorderSegments=Te,e.getReorderedIndices=Ue,e.getReorderedString=ye,e.openingToClosingBracket=y,Object.defineProperty(e,"__esModule",{value:!0}),e})({});return n}const c0=/\bvoid\s+main\s*\(\s*\)\s*{/g;function yh(n){const e=/^[ \t]*#include +<([\w\d./]+)>/gm;function t(i,r){let s=rt[r];return s?yh(s):i}return n.replace(e,t)}const cn=[];for(let n=0;n<256;n++)cn[n]=(n<16?"0":"")+n.toString(16);function XS(){const n=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,i=Math.random()*4294967295|0;return(cn[n&255]+cn[n>>8&255]+cn[n>>16&255]+cn[n>>24&255]+"-"+cn[e&255]+cn[e>>8&255]+"-"+cn[e>>16&15|64]+cn[e>>24&255]+"-"+cn[t&63|128]+cn[t>>8&255]+"-"+cn[t>>16&255]+cn[t>>24&255]+cn[i&255]+cn[i>>8&255]+cn[i>>16&255]+cn[i>>24&255]).toUpperCase()}const Lr=Object.assign||function(){let n=arguments[0];for(let e=1,t=arguments.length;e<t;e++){let i=arguments[e];if(i)for(let r in i)Object.prototype.hasOwnProperty.call(i,r)&&(n[r]=i[r])}return n},jS=Date.now(),cp=new WeakMap,up=new Map;let YS=1e10;function bh(n,e){const t=$S(e);let i=cp.get(n);if(i||cp.set(n,i=Object.create(null)),i[t])return new i[t];const r=`_onBeforeCompile${t}`,s=function(c,u){n.onBeforeCompile.call(this,c,u);const f=this.customProgramCacheKey()+"|"+c.vertexShader+"|"+c.fragmentShader;let h=up[f];if(!h){const d=qS(this,c,e,t);h=up[f]=d}c.vertexShader=h.vertexShader,c.fragmentShader=h.fragmentShader,Lr(c.uniforms,this.uniforms),e.timeUniform&&(c.uniforms[e.timeUniform]={get value(){return Date.now()-jS}}),this[r]&&this[r](c)},a=function(){return o(e.chained?n:n.clone())},o=function(c){const u=Object.create(c,l);return Object.defineProperty(u,"baseMaterial",{value:n}),Object.defineProperty(u,"id",{value:YS++}),u.uuid=XS(),u.uniforms=Lr({},c.uniforms,e.uniforms),u.defines=Lr({},c.defines,e.defines),u.defines[`TROIKA_DERIVED_MATERIAL_${t}`]="",u.extensions=Lr({},c.extensions,e.extensions),u._listeners=void 0,u},l={constructor:{value:a},isDerivedMaterial:{value:!0},type:{get:()=>n.type,set:c=>{n.type=c}},isDerivedFrom:{writable:!0,configurable:!0,value:function(c){const u=this.baseMaterial;return c===u||u.isDerivedMaterial&&u.isDerivedFrom(c)||!1}},customProgramCacheKey:{writable:!0,configurable:!0,value:function(){return n.customProgramCacheKey()+"|"+t}},onBeforeCompile:{get(){return s},set(c){this[r]=c}},copy:{writable:!0,configurable:!0,value:function(c){return n.copy.call(this,c),!n.isShaderMaterial&&!n.isDerivedMaterial&&(Lr(this.extensions,c.extensions),Lr(this.defines,c.defines),Lr(this.uniforms,Km.clone(c.uniforms))),this}},clone:{writable:!0,configurable:!0,value:function(){const c=new n.constructor;return o(c).copy(this)}},getDepthMaterial:{writable:!0,configurable:!0,value:function(){let c=this._depthMaterial;return c||(c=this._depthMaterial=bh(n.isDerivedMaterial?n.getDepthMaterial():new Zm({depthPacking:X_}),e),c.defines.IS_DEPTH_MATERIAL="",c.uniforms=this.uniforms),c}},getDistanceMaterial:{writable:!0,configurable:!0,value:function(){let c=this._distanceMaterial;return c||(c=this._distanceMaterial=bh(n.isDerivedMaterial?n.getDistanceMaterial():new $m,e),c.defines.IS_DISTANCE_MATERIAL="",c.uniforms=this.uniforms),c}},dispose:{writable:!0,configurable:!0,value(){const{_depthMaterial:c,_distanceMaterial:u}=this;c&&c.dispose(),u&&u.dispose(),n.dispose.call(this)}}};return i[t]=a,new a}function qS(n,{vertexShader:e,fragmentShader:t},i,r){let{vertexDefs:s,vertexMainIntro:a,vertexMainOutro:o,vertexTransform:l,fragmentDefs:c,fragmentMainIntro:u,fragmentMainOutro:f,fragmentColorTransform:h,customRewriter:d,timeUniform:m}=i;if(s=s||"",a=a||"",o=o||"",c=c||"",u=u||"",f=f||"",(l||d)&&(e=yh(e)),(h||d)&&(t=t.replace(/^[ \t]*#include <((?:tonemapping|encodings|colorspace|fog|premultiplied_alpha|dithering)_fragment)>/gm,`
//!BEGIN_POST_CHUNK $1
$&
//!END_POST_CHUNK
`),t=yh(t)),d){let g=d({vertexShader:e,fragmentShader:t});e=g.vertexShader,t=g.fragmentShader}if(h){let g=[];t=t.replace(/^\/\/!BEGIN_POST_CHUNK[^]+?^\/\/!END_POST_CHUNK/gm,p=>(g.push(p),"")),f=`${h}
${g.join(`
`)}
${f}`}if(m){const g=`
uniform float ${m};
`;s=g+s,c=g+c}return l&&(e=`vec3 troika_position_${r};
vec3 troika_normal_${r};
vec2 troika_uv_${r};
${e}
`,s=`${s}
void troikaVertexTransform${r}() {
  vec3 position = troika_position_${r};
  vec3 normal = troika_normal_${r};
  vec2 uv = troika_uv_${r};
  ${l}
  troika_position_${r} = position;
  troika_normal_${r} = normal;
  troika_uv_${r} = uv;
}
`,a=`
troika_position_${r} = vec3(position);
troika_normal_${r} = vec3(normal);
troika_uv_${r} = vec2(uv);
troikaVertexTransform${r}();
${a}
`,e=e.replace(/\b(position|normal|uv)\b/g,(g,p,_,v)=>/\battribute\s+vec[23]\s+$/.test(v.substr(0,_))?p:`troika_${p}_${r}`),n.map&&n.map.channel>0||(e=e.replace(/\bMAP_UV\b/g,`troika_uv_${r}`))),e=hp(e,r,s,a,o),t=hp(t,r,c,u,f),{vertexShader:e,fragmentShader:t}}function hp(n,e,t,i,r){return(i||r||t)&&(n=n.replace(c0,`
${t}
void troikaOrigMain${e}() {`),n+=`
void main() {
  ${i}
  troikaOrigMain${e}();
  ${r}
}`),n}function KS(n,e){return n==="uniforms"?void 0:typeof e=="function"?e.toString():e}let ZS=0;const fp=new Map;function $S(n){const e=JSON.stringify(n,KS);let t=fp.get(e);return t==null&&fp.set(e,t=++ZS),t}/*!
Custom build of Typr.ts (https://github.com/fredli74/Typr.ts) for use in Troika text rendering.
Original MIT license applies: https://github.com/fredli74/Typr.ts/blob/master/LICENSE
*/function JS(){return typeof window>"u"&&(self.window=self),(function(n){var e={parse:function(r){var s=e._bin,a=new Uint8Array(r);if(s.readASCII(a,0,4)=="ttcf"){var o=4;s.readUshort(a,o),o+=2,s.readUshort(a,o),o+=2;var l=s.readUint(a,o);o+=4;for(var c=[],u=0;u<l;u++){var f=s.readUint(a,o);o+=4,c.push(e._readFont(a,f))}return c}return[e._readFont(a,0)]},_readFont:function(r,s){var a=e._bin,o=s;a.readFixed(r,s),s+=4;var l=a.readUshort(r,s);s+=2,a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2;for(var c=["cmap","head","hhea","maxp","hmtx","name","OS/2","post","loca","glyf","kern","CFF ","GDEF","GPOS","GSUB","SVG "],u={_data:r,_offset:o},f={},h=0;h<l;h++){var d=a.readASCII(r,s,4);s+=4,a.readUint(r,s),s+=4;var m=a.readUint(r,s);s+=4;var g=a.readUint(r,s);s+=4,f[d]={offset:m,length:g}}for(h=0;h<c.length;h++){var p=c[h];f[p]&&(u[p.trim()]=e[p.trim()].parse(r,f[p].offset,f[p].length,u))}return u},_tabOffset:function(r,s,a){for(var o=e._bin,l=o.readUshort(r,a+4),c=a+12,u=0;u<l;u++){var f=o.readASCII(r,c,4);c+=4,o.readUint(r,c),c+=4;var h=o.readUint(r,c);if(c+=4,o.readUint(r,c),c+=4,f==s)return h}return 0}};e._bin={readFixed:function(r,s){return(r[s]<<8|r[s+1])+(r[s+2]<<8|r[s+3])/65540},readF2dot14:function(r,s){return e._bin.readShort(r,s)/16384},readInt:function(r,s){return e._bin._view(r).getInt32(s)},readInt8:function(r,s){return e._bin._view(r).getInt8(s)},readShort:function(r,s){return e._bin._view(r).getInt16(s)},readUshort:function(r,s){return e._bin._view(r).getUint16(s)},readUshorts:function(r,s,a){for(var o=[],l=0;l<a;l++)o.push(e._bin.readUshort(r,s+2*l));return o},readUint:function(r,s){return e._bin._view(r).getUint32(s)},readUint64:function(r,s){return 4294967296*e._bin.readUint(r,s)+e._bin.readUint(r,s+4)},readASCII:function(r,s,a){for(var o="",l=0;l<a;l++)o+=String.fromCharCode(r[s+l]);return o},readUnicode:function(r,s,a){for(var o="",l=0;l<a;l++){var c=r[s++]<<8|r[s++];o+=String.fromCharCode(c)}return o},_tdec:typeof window<"u"&&window.TextDecoder?new window.TextDecoder:null,readUTF8:function(r,s,a){var o=e._bin._tdec;return o&&s==0&&a==r.length?o.decode(r):e._bin.readASCII(r,s,a)},readBytes:function(r,s,a){for(var o=[],l=0;l<a;l++)o.push(r[s+l]);return o},readASCIIArray:function(r,s,a){for(var o=[],l=0;l<a;l++)o.push(String.fromCharCode(r[s+l]));return o},_view:function(r){return r._dataView||(r._dataView=r.buffer?new DataView(r.buffer,r.byteOffset,r.byteLength):new DataView(new Uint8Array(r).buffer))}},e._lctf={},e._lctf.parse=function(r,s,a,o,l){var c=e._bin,u={},f=s;c.readFixed(r,s),s+=4;var h=c.readUshort(r,s);s+=2;var d=c.readUshort(r,s);s+=2;var m=c.readUshort(r,s);return s+=2,u.scriptList=e._lctf.readScriptList(r,f+h),u.featureList=e._lctf.readFeatureList(r,f+d),u.lookupList=e._lctf.readLookupList(r,f+m,l),u},e._lctf.readLookupList=function(r,s,a){var o=e._bin,l=s,c=[],u=o.readUshort(r,s);s+=2;for(var f=0;f<u;f++){var h=o.readUshort(r,s);s+=2;var d=e._lctf.readLookupTable(r,l+h,a);c.push(d)}return c},e._lctf.readLookupTable=function(r,s,a){var o=e._bin,l=s,c={tabs:[]};c.ltype=o.readUshort(r,s),s+=2,c.flag=o.readUshort(r,s),s+=2;var u=o.readUshort(r,s);s+=2;for(var f=c.ltype,h=0;h<u;h++){var d=o.readUshort(r,s);s+=2;var m=a(r,f,l+d,c);c.tabs.push(m)}return c},e._lctf.numOfOnes=function(r){for(var s=0,a=0;a<32;a++)(r>>>a&1)!=0&&s++;return s},e._lctf.readClassDef=function(r,s){var a=e._bin,o=[],l=a.readUshort(r,s);if(s+=2,l==1){var c=a.readUshort(r,s);s+=2;var u=a.readUshort(r,s);s+=2;for(var f=0;f<u;f++)o.push(c+f),o.push(c+f),o.push(a.readUshort(r,s)),s+=2}if(l==2){var h=a.readUshort(r,s);for(s+=2,f=0;f<h;f++)o.push(a.readUshort(r,s)),s+=2,o.push(a.readUshort(r,s)),s+=2,o.push(a.readUshort(r,s)),s+=2}return o},e._lctf.getInterval=function(r,s){for(var a=0;a<r.length;a+=3){var o=r[a],l=r[a+1];if(r[a+2],o<=s&&s<=l)return a}return-1},e._lctf.readCoverage=function(r,s){var a=e._bin,o={};o.fmt=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);return s+=2,o.fmt==1&&(o.tab=a.readUshorts(r,s,l)),o.fmt==2&&(o.tab=a.readUshorts(r,s,3*l)),o},e._lctf.coverageIndex=function(r,s){var a=r.tab;if(r.fmt==1)return a.indexOf(s);if(r.fmt==2){var o=e._lctf.getInterval(a,s);if(o!=-1)return a[o+2]+(s-a[o])}return-1},e._lctf.readFeatureList=function(r,s){var a=e._bin,o=s,l=[],c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readASCII(r,s,4);s+=4;var h=a.readUshort(r,s);s+=2;var d=e._lctf.readFeatureTable(r,o+h);d.tag=f.trim(),l.push(d)}return l},e._lctf.readFeatureTable=function(r,s){var a=e._bin,o=s,l={},c=a.readUshort(r,s);s+=2,c>0&&(l.featureParams=o+c);var u=a.readUshort(r,s);s+=2,l.tab=[];for(var f=0;f<u;f++)l.tab.push(a.readUshort(r,s+2*f));return l},e._lctf.readScriptList=function(r,s){var a=e._bin,o=s,l={},c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readASCII(r,s,4);s+=4;var h=a.readUshort(r,s);s+=2,l[f.trim()]=e._lctf.readScriptTable(r,o+h)}return l},e._lctf.readScriptTable=function(r,s){var a=e._bin,o=s,l={},c=a.readUshort(r,s);s+=2,c>0&&(l.default=e._lctf.readLangSysTable(r,o+c));var u=a.readUshort(r,s);s+=2;for(var f=0;f<u;f++){var h=a.readASCII(r,s,4);s+=4;var d=a.readUshort(r,s);s+=2,l[h.trim()]=e._lctf.readLangSysTable(r,o+d)}return l},e._lctf.readLangSysTable=function(r,s){var a=e._bin,o={};a.readUshort(r,s),s+=2,o.reqFeature=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);return s+=2,o.features=a.readUshorts(r,s,l),o},e.CFF={},e.CFF.parse=function(r,s,a){var o=e._bin;(r=new Uint8Array(r.buffer,s,a))[s=0],r[++s],r[++s],r[++s],s++;var l=[];s=e.CFF.readIndex(r,s,l);for(var c=[],u=0;u<l.length-1;u++)c.push(o.readASCII(r,s+l[u],l[u+1]-l[u]));s+=l[l.length-1];var f=[];s=e.CFF.readIndex(r,s,f);var h=[];for(u=0;u<f.length-1;u++)h.push(e.CFF.readDict(r,s+f[u],s+f[u+1]));s+=f[f.length-1];var d=h[0],m=[];s=e.CFF.readIndex(r,s,m);var g=[];for(u=0;u<m.length-1;u++)g.push(o.readASCII(r,s+m[u],m[u+1]-m[u]));if(s+=m[m.length-1],e.CFF.readSubrs(r,s,d),d.CharStrings){s=d.CharStrings,m=[],s=e.CFF.readIndex(r,s,m);var p=[];for(u=0;u<m.length-1;u++)p.push(o.readBytes(r,s+m[u],m[u+1]-m[u]));d.CharStrings=p}if(d.ROS){s=d.FDArray;var _=[];for(s=e.CFF.readIndex(r,s,_),d.FDArray=[],u=0;u<_.length-1;u++){var v=e.CFF.readDict(r,s+_[u],s+_[u+1]);e.CFF._readFDict(r,v,g),d.FDArray.push(v)}s+=_[_.length-1],s=d.FDSelect,d.FDSelect=[];var S=r[s];if(s++,S!=3)throw S;var y=o.readUshort(r,s);for(s+=2,u=0;u<y+1;u++)d.FDSelect.push(o.readUshort(r,s),r[s+2]),s+=3}return d.Encoding&&(d.Encoding=e.CFF.readEncoding(r,d.Encoding,d.CharStrings.length)),d.charset&&(d.charset=e.CFF.readCharset(r,d.charset,d.CharStrings.length)),e.CFF._readFDict(r,d,g),d},e.CFF._readFDict=function(r,s,a){var o;for(var l in s.Private&&(o=s.Private[1],s.Private=e.CFF.readDict(r,o,o+s.Private[0]),s.Private.Subrs&&e.CFF.readSubrs(r,o+s.Private.Subrs,s.Private)),s)["FamilyName","FontName","FullName","Notice","version","Copyright"].indexOf(l)!=-1&&(s[l]=a[s[l]-426+35])},e.CFF.readSubrs=function(r,s,a){var o=e._bin,l=[];s=e.CFF.readIndex(r,s,l);var c,u=l.length;c=u<1240?107:u<33900?1131:32768,a.Bias=c,a.Subrs=[];for(var f=0;f<l.length-1;f++)a.Subrs.push(o.readBytes(r,s+l[f],l[f+1]-l[f]))},e.CFF.tableSE=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,0,111,112,113,114,0,115,116,117,118,119,120,121,122,0,123,0,124,125,126,127,128,129,130,131,0,132,133,0,134,135,136,137,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,138,0,139,0,0,0,0,140,141,142,143,0,0,0,0,0,144,0,0,0,145,0,0,146,147,148,149,0,0,0,0],e.CFF.glyphByUnicode=function(r,s){for(var a=0;a<r.charset.length;a++)if(r.charset[a]==s)return a;return-1},e.CFF.glyphBySE=function(r,s){return s<0||s>255?-1:e.CFF.glyphByUnicode(r,e.CFF.tableSE[s])},e.CFF.readEncoding=function(r,s,a){e._bin;var o=[".notdef"],l=r[s];if(s++,l!=0)throw"error: unknown encoding format: "+l;var c=r[s];s++;for(var u=0;u<c;u++)o.push(r[s+u]);return o},e.CFF.readCharset=function(r,s,a){var o=e._bin,l=[".notdef"],c=r[s];if(s++,c==0)for(var u=0;u<a;u++){var f=o.readUshort(r,s);s+=2,l.push(f)}else{if(c!=1&&c!=2)throw"error: format: "+c;for(;l.length<a;){f=o.readUshort(r,s),s+=2;var h=0;for(c==1?(h=r[s],s++):(h=o.readUshort(r,s),s+=2),u=0;u<=h;u++)l.push(f),f++}}return l},e.CFF.readIndex=function(r,s,a){var o=e._bin,l=o.readUshort(r,s)+1,c=r[s+=2];if(s++,c==1)for(var u=0;u<l;u++)a.push(r[s+u]);else if(c==2)for(u=0;u<l;u++)a.push(o.readUshort(r,s+2*u));else if(c==3)for(u=0;u<l;u++)a.push(16777215&o.readUint(r,s+3*u-1));else if(l!=1)throw"unsupported offset size: "+c+", count: "+l;return(s+=l*c)-1},e.CFF.getCharString=function(r,s,a){var o=e._bin,l=r[s],c=r[s+1];r[s+2],r[s+3],r[s+4];var u=1,f=null,h=null;l<=20&&(f=l,u=1),l==12&&(f=100*l+c,u=2),21<=l&&l<=27&&(f=l,u=1),l==28&&(h=o.readShort(r,s+1),u=3),29<=l&&l<=31&&(f=l,u=1),32<=l&&l<=246&&(h=l-139,u=1),247<=l&&l<=250&&(h=256*(l-247)+c+108,u=2),251<=l&&l<=254&&(h=256*-(l-251)-c-108,u=2),l==255&&(h=o.readInt(r,s+1)/65535,u=5),a.val=h??"o"+f,a.size=u},e.CFF.readCharString=function(r,s,a){for(var o=s+a,l=e._bin,c=[];s<o;){var u=r[s],f=r[s+1];r[s+2],r[s+3],r[s+4];var h=1,d=null,m=null;u<=20&&(d=u,h=1),u==12&&(d=100*u+f,h=2),u!=19&&u!=20||(d=u,h=2),21<=u&&u<=27&&(d=u,h=1),u==28&&(m=l.readShort(r,s+1),h=3),29<=u&&u<=31&&(d=u,h=1),32<=u&&u<=246&&(m=u-139,h=1),247<=u&&u<=250&&(m=256*(u-247)+f+108,h=2),251<=u&&u<=254&&(m=256*-(u-251)-f-108,h=2),u==255&&(m=l.readInt(r,s+1)/65535,h=5),c.push(m??"o"+d),s+=h}return c},e.CFF.readDict=function(r,s,a){for(var o=e._bin,l={},c=[];s<a;){var u=r[s],f=r[s+1];r[s+2],r[s+3],r[s+4];var h=1,d=null,m=null;if(u==28&&(m=o.readShort(r,s+1),h=3),u==29&&(m=o.readInt(r,s+1),h=5),32<=u&&u<=246&&(m=u-139,h=1),247<=u&&u<=250&&(m=256*(u-247)+f+108,h=2),251<=u&&u<=254&&(m=256*-(u-251)-f-108,h=2),u==255)throw m=o.readInt(r,s+1)/65535,h=5,"unknown number";if(u==30){var g=[];for(h=1;;){var p=r[s+h];h++;var _=p>>4,v=15&p;if(_!=15&&g.push(_),v!=15&&g.push(v),v==15)break}for(var S="",y=[0,1,2,3,4,5,6,7,8,9,".","e","e-","reserved","-","endOfNumber"],M=0;M<g.length;M++)S+=y[g[M]];m=parseFloat(S)}u<=21&&(d=["version","Notice","FullName","FamilyName","Weight","FontBBox","BlueValues","OtherBlues","FamilyBlues","FamilyOtherBlues","StdHW","StdVW","escape","UniqueID","XUID","charset","Encoding","CharStrings","Private","Subrs","defaultWidthX","nominalWidthX"][u],h=1,u==12&&(d=["Copyright","isFixedPitch","ItalicAngle","UnderlinePosition","UnderlineThickness","PaintType","CharstringType","FontMatrix","StrokeWidth","BlueScale","BlueShift","BlueFuzz","StemSnapH","StemSnapV","ForceBold",0,0,"LanguageGroup","ExpansionFactor","initialRandomSeed","SyntheticBase","PostScript","BaseFontName","BaseFontBlend",0,0,0,0,0,0,"ROS","CIDFontVersion","CIDFontRevision","CIDFontType","CIDCount","UIDBase","FDArray","FDSelect","FontName"][f],h=2)),d!=null?(l[d]=c.length==1?c[0]:c,c=[]):c.push(m),s+=h}return l},e.cmap={},e.cmap.parse=function(r,s,a){r=new Uint8Array(r.buffer,s,a),s=0;var o=e._bin,l={};o.readUshort(r,s),s+=2;var c=o.readUshort(r,s);s+=2;var u=[];l.tables=[];for(var f=0;f<c;f++){var h=o.readUshort(r,s);s+=2;var d=o.readUshort(r,s);s+=2;var m=o.readUint(r,s);s+=4;var g="p"+h+"e"+d,p=u.indexOf(m);if(p==-1){var _;p=l.tables.length,u.push(m);var v=o.readUshort(r,m);v==0?_=e.cmap.parse0(r,m):v==4?_=e.cmap.parse4(r,m):v==6?_=e.cmap.parse6(r,m):v==12?_=e.cmap.parse12(r,m):console.debug("unknown format: "+v,h,d,m),l.tables.push(_)}if(l[g]!=null)throw"multiple tables for one platform+encoding";l[g]=p}return l},e.cmap.parse0=function(r,s){var a=e._bin,o={};o.format=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);s+=2,a.readUshort(r,s),s+=2,o.map=[];for(var c=0;c<l-6;c++)o.map.push(r[s+c]);return o},e.cmap.parse4=function(r,s){var a=e._bin,o=s,l={};l.format=a.readUshort(r,s),s+=2;var c=a.readUshort(r,s);s+=2,a.readUshort(r,s),s+=2;var u=a.readUshort(r,s);s+=2;var f=u/2;l.searchRange=a.readUshort(r,s),s+=2,l.entrySelector=a.readUshort(r,s),s+=2,l.rangeShift=a.readUshort(r,s),s+=2,l.endCount=a.readUshorts(r,s,f),s+=2*f,s+=2,l.startCount=a.readUshorts(r,s,f),s+=2*f,l.idDelta=[];for(var h=0;h<f;h++)l.idDelta.push(a.readShort(r,s)),s+=2;for(l.idRangeOffset=a.readUshorts(r,s,f),s+=2*f,l.glyphIdArray=[];s<o+c;)l.glyphIdArray.push(a.readUshort(r,s)),s+=2;return l},e.cmap.parse6=function(r,s){var a=e._bin,o={};o.format=a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2,o.firstCode=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);s+=2,o.glyphIdArray=[];for(var c=0;c<l;c++)o.glyphIdArray.push(a.readUshort(r,s)),s+=2;return o},e.cmap.parse12=function(r,s){var a=e._bin,o={};o.format=a.readUshort(r,s),s+=2,s+=2,a.readUint(r,s),s+=4,a.readUint(r,s),s+=4;var l=a.readUint(r,s);s+=4,o.groups=[];for(var c=0;c<l;c++){var u=s+12*c,f=a.readUint(r,u+0),h=a.readUint(r,u+4),d=a.readUint(r,u+8);o.groups.push([f,h,d])}return o},e.glyf={},e.glyf.parse=function(r,s,a,o){for(var l=[],c=0;c<o.maxp.numGlyphs;c++)l.push(null);return l},e.glyf._parseGlyf=function(r,s){var a=e._bin,o=r._data,l=e._tabOffset(o,"glyf",r._offset)+r.loca[s];if(r.loca[s]==r.loca[s+1])return null;var c={};if(c.noc=a.readShort(o,l),l+=2,c.xMin=a.readShort(o,l),l+=2,c.yMin=a.readShort(o,l),l+=2,c.xMax=a.readShort(o,l),l+=2,c.yMax=a.readShort(o,l),l+=2,c.xMin>=c.xMax||c.yMin>=c.yMax)return null;if(c.noc>0){c.endPts=[];for(var u=0;u<c.noc;u++)c.endPts.push(a.readUshort(o,l)),l+=2;var f=a.readUshort(o,l);if(l+=2,o.length-l<f)return null;c.instructions=a.readBytes(o,l,f),l+=f;var h=c.endPts[c.noc-1]+1;for(c.flags=[],u=0;u<h;u++){var d=o[l];if(l++,c.flags.push(d),(8&d)!=0){var m=o[l];l++;for(var g=0;g<m;g++)c.flags.push(d),u++}}for(c.xs=[],u=0;u<h;u++){var p=(2&c.flags[u])!=0,_=(16&c.flags[u])!=0;p?(c.xs.push(_?o[l]:-o[l]),l++):_?c.xs.push(0):(c.xs.push(a.readShort(o,l)),l+=2)}for(c.ys=[],u=0;u<h;u++)p=(4&c.flags[u])!=0,_=(32&c.flags[u])!=0,p?(c.ys.push(_?o[l]:-o[l]),l++):_?c.ys.push(0):(c.ys.push(a.readShort(o,l)),l+=2);var v=0,S=0;for(u=0;u<h;u++)v+=c.xs[u],S+=c.ys[u],c.xs[u]=v,c.ys[u]=S}else{var y;c.parts=[];do{y=a.readUshort(o,l),l+=2;var M={m:{a:1,b:0,c:0,d:1,tx:0,ty:0},p1:-1,p2:-1};if(c.parts.push(M),M.glyphIndex=a.readUshort(o,l),l+=2,1&y){var T=a.readShort(o,l);l+=2;var w=a.readShort(o,l);l+=2}else T=a.readInt8(o,l),l++,w=a.readInt8(o,l),l++;2&y?(M.m.tx=T,M.m.ty=w):(M.p1=T,M.p2=w),8&y?(M.m.a=M.m.d=a.readF2dot14(o,l),l+=2):64&y?(M.m.a=a.readF2dot14(o,l),l+=2,M.m.d=a.readF2dot14(o,l),l+=2):128&y&&(M.m.a=a.readF2dot14(o,l),l+=2,M.m.b=a.readF2dot14(o,l),l+=2,M.m.c=a.readF2dot14(o,l),l+=2,M.m.d=a.readF2dot14(o,l),l+=2)}while(32&y);if(256&y){var b=a.readUshort(o,l);for(l+=2,c.instr=[],u=0;u<b;u++)c.instr.push(o[l]),l++}}return c},e.GDEF={},e.GDEF.parse=function(r,s,a,o){var l=s;s+=4;var c=e._bin.readUshort(r,s);return{glyphClassDef:c===0?null:e._lctf.readClassDef(r,l+c)}},e.GPOS={},e.GPOS.parse=function(r,s,a,o){return e._lctf.parse(r,s,a,o,e.GPOS.subt)},e.GPOS.subt=function(r,s,a,o){var l=e._bin,c=a,u={};if(u.fmt=l.readUshort(r,a),a+=2,s==1||s==2||s==3||s==7||s==8&&u.fmt<=2){var f=l.readUshort(r,a);a+=2,u.coverage=e._lctf.readCoverage(r,f+c)}if(s==1&&u.fmt==1){var h=l.readUshort(r,a);a+=2,h!=0&&(u.pos=e.GPOS.readValueRecord(r,a,h))}else if(s==2&&u.fmt>=1&&u.fmt<=2){h=l.readUshort(r,a),a+=2;var d=l.readUshort(r,a);a+=2;var m=e._lctf.numOfOnes(h),g=e._lctf.numOfOnes(d);if(u.fmt==1){u.pairsets=[];var p=l.readUshort(r,a);a+=2;for(var _=0;_<p;_++){var v=c+l.readUshort(r,a);a+=2;var S=l.readUshort(r,v);v+=2;for(var y=[],M=0;M<S;M++){var T=l.readUshort(r,v);v+=2,h!=0&&(R=e.GPOS.readValueRecord(r,v,h),v+=2*m),d!=0&&(L=e.GPOS.readValueRecord(r,v,d),v+=2*g),y.push({gid2:T,val1:R,val2:L})}u.pairsets.push(y)}}if(u.fmt==2){var w=l.readUshort(r,a);a+=2;var b=l.readUshort(r,a);a+=2;var x=l.readUshort(r,a);a+=2;var A=l.readUshort(r,a);for(a+=2,u.classDef1=e._lctf.readClassDef(r,c+w),u.classDef2=e._lctf.readClassDef(r,c+b),u.matrix=[],_=0;_<x;_++){var P=[];for(M=0;M<A;M++){var R=null,L=null;h!=0&&(R=e.GPOS.readValueRecord(r,a,h),a+=2*m),d!=0&&(L=e.GPOS.readValueRecord(r,a,d),a+=2*g),P.push({val1:R,val2:L})}u.matrix.push(P)}}}else if(s==4&&u.fmt==1)u.markCoverage=e._lctf.readCoverage(r,l.readUshort(r,a)+c),u.baseCoverage=e._lctf.readCoverage(r,l.readUshort(r,a+2)+c),u.markClassCount=l.readUshort(r,a+4),u.markArray=e.GPOS.readMarkArray(r,l.readUshort(r,a+6)+c),u.baseArray=e.GPOS.readBaseArray(r,l.readUshort(r,a+8)+c,u.markClassCount);else if(s==6&&u.fmt==1)u.mark1Coverage=e._lctf.readCoverage(r,l.readUshort(r,a)+c),u.mark2Coverage=e._lctf.readCoverage(r,l.readUshort(r,a+2)+c),u.markClassCount=l.readUshort(r,a+4),u.mark1Array=e.GPOS.readMarkArray(r,l.readUshort(r,a+6)+c),u.mark2Array=e.GPOS.readBaseArray(r,l.readUshort(r,a+8)+c,u.markClassCount);else{if(s==9&&u.fmt==1){var I=l.readUshort(r,a);a+=2;var N=l.readUint(r,a);if(a+=4,o.ltype==9)o.ltype=I;else if(o.ltype!=I)throw"invalid extension substitution";return e.GPOS.subt(r,o.ltype,c+N)}console.debug("unsupported GPOS table LookupType",s,"format",u.fmt)}return u},e.GPOS.readValueRecord=function(r,s,a){var o=e._bin,l=[];return l.push(1&a?o.readShort(r,s):0),s+=1&a?2:0,l.push(2&a?o.readShort(r,s):0),s+=2&a?2:0,l.push(4&a?o.readShort(r,s):0),s+=4&a?2:0,l.push(8&a?o.readShort(r,s):0),s+=8&a?2:0,l},e.GPOS.readBaseArray=function(r,s,a){var o=e._bin,l=[],c=s,u=o.readUshort(r,s);s+=2;for(var f=0;f<u;f++){for(var h=[],d=0;d<a;d++)h.push(e.GPOS.readAnchorRecord(r,c+o.readUshort(r,s))),s+=2;l.push(h)}return l},e.GPOS.readMarkArray=function(r,s){var a=e._bin,o=[],l=s,c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=e.GPOS.readAnchorRecord(r,a.readUshort(r,s+2)+l);f.markClass=a.readUshort(r,s),o.push(f),s+=4}return o},e.GPOS.readAnchorRecord=function(r,s){var a=e._bin,o={};return o.fmt=a.readUshort(r,s),o.x=a.readShort(r,s+2),o.y=a.readShort(r,s+4),o},e.GSUB={},e.GSUB.parse=function(r,s,a,o){return e._lctf.parse(r,s,a,o,e.GSUB.subt)},e.GSUB.subt=function(r,s,a,o){var l=e._bin,c=a,u={};if(u.fmt=l.readUshort(r,a),a+=2,s!=1&&s!=2&&s!=4&&s!=5&&s!=6)return null;if(s==1||s==2||s==4||s==5&&u.fmt<=2||s==6&&u.fmt<=2){var f=l.readUshort(r,a);a+=2,u.coverage=e._lctf.readCoverage(r,c+f)}if(s==1&&u.fmt>=1&&u.fmt<=2){if(u.fmt==1)u.delta=l.readShort(r,a),a+=2;else if(u.fmt==2){var h=l.readUshort(r,a);a+=2,u.newg=l.readUshorts(r,a,h),a+=2*u.newg.length}}else if(s==2&&u.fmt==1){h=l.readUshort(r,a),a+=2,u.seqs=[];for(var d=0;d<h;d++){var m=l.readUshort(r,a)+c;a+=2;var g=l.readUshort(r,m);u.seqs.push(l.readUshorts(r,m+2,g))}}else if(s==4)for(u.vals=[],h=l.readUshort(r,a),a+=2,d=0;d<h;d++){var p=l.readUshort(r,a);a+=2,u.vals.push(e.GSUB.readLigatureSet(r,c+p))}else if(s==5&&u.fmt==2){if(u.fmt==2){var _=l.readUshort(r,a);a+=2,u.cDef=e._lctf.readClassDef(r,c+_),u.scset=[];var v=l.readUshort(r,a);for(a+=2,d=0;d<v;d++){var S=l.readUshort(r,a);a+=2,u.scset.push(S==0?null:e.GSUB.readSubClassSet(r,c+S))}}}else if(s==6&&u.fmt==3){if(u.fmt==3){for(d=0;d<3;d++){h=l.readUshort(r,a),a+=2;for(var y=[],M=0;M<h;M++)y.push(e._lctf.readCoverage(r,c+l.readUshort(r,a+2*M)));a+=2*h,d==0&&(u.backCvg=y),d==1&&(u.inptCvg=y),d==2&&(u.ahedCvg=y)}h=l.readUshort(r,a),a+=2,u.lookupRec=e.GSUB.readSubstLookupRecords(r,a,h)}}else{if(s==7&&u.fmt==1){var T=l.readUshort(r,a);a+=2;var w=l.readUint(r,a);if(a+=4,o.ltype==9)o.ltype=T;else if(o.ltype!=T)throw"invalid extension substitution";return e.GSUB.subt(r,o.ltype,c+w)}console.debug("unsupported GSUB table LookupType",s,"format",u.fmt)}return u},e.GSUB.readSubClassSet=function(r,s){var a=e._bin.readUshort,o=s,l=[],c=a(r,s);s+=2;for(var u=0;u<c;u++){var f=a(r,s);s+=2,l.push(e.GSUB.readSubClassRule(r,o+f))}return l},e.GSUB.readSubClassRule=function(r,s){var a=e._bin.readUshort,o={},l=a(r,s),c=a(r,s+=2);s+=2,o.input=[];for(var u=0;u<l-1;u++)o.input.push(a(r,s)),s+=2;return o.substLookupRecords=e.GSUB.readSubstLookupRecords(r,s,c),o},e.GSUB.readSubstLookupRecords=function(r,s,a){for(var o=e._bin.readUshort,l=[],c=0;c<a;c++)l.push(o(r,s),o(r,s+2)),s+=4;return l},e.GSUB.readChainSubClassSet=function(r,s){var a=e._bin,o=s,l=[],c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readUshort(r,s);s+=2,l.push(e.GSUB.readChainSubClassRule(r,o+f))}return l},e.GSUB.readChainSubClassRule=function(r,s){for(var a=e._bin,o={},l=["backtrack","input","lookahead"],c=0;c<l.length;c++){var u=a.readUshort(r,s);s+=2,c==1&&u--,o[l[c]]=a.readUshorts(r,s,u),s+=2*o[l[c]].length}return u=a.readUshort(r,s),s+=2,o.subst=a.readUshorts(r,s,2*u),s+=2*o.subst.length,o},e.GSUB.readLigatureSet=function(r,s){var a=e._bin,o=s,l=[],c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readUshort(r,s);s+=2,l.push(e.GSUB.readLigature(r,o+f))}return l},e.GSUB.readLigature=function(r,s){var a=e._bin,o={chain:[]};o.nglyph=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);s+=2;for(var c=0;c<l-1;c++)o.chain.push(a.readUshort(r,s)),s+=2;return o},e.head={},e.head.parse=function(r,s,a){var o=e._bin,l={};return o.readFixed(r,s),s+=4,l.fontRevision=o.readFixed(r,s),s+=4,o.readUint(r,s),s+=4,o.readUint(r,s),s+=4,l.flags=o.readUshort(r,s),s+=2,l.unitsPerEm=o.readUshort(r,s),s+=2,l.created=o.readUint64(r,s),s+=8,l.modified=o.readUint64(r,s),s+=8,l.xMin=o.readShort(r,s),s+=2,l.yMin=o.readShort(r,s),s+=2,l.xMax=o.readShort(r,s),s+=2,l.yMax=o.readShort(r,s),s+=2,l.macStyle=o.readUshort(r,s),s+=2,l.lowestRecPPEM=o.readUshort(r,s),s+=2,l.fontDirectionHint=o.readShort(r,s),s+=2,l.indexToLocFormat=o.readShort(r,s),s+=2,l.glyphDataFormat=o.readShort(r,s),s+=2,l},e.hhea={},e.hhea.parse=function(r,s,a){var o=e._bin,l={};return o.readFixed(r,s),s+=4,l.ascender=o.readShort(r,s),s+=2,l.descender=o.readShort(r,s),s+=2,l.lineGap=o.readShort(r,s),s+=2,l.advanceWidthMax=o.readUshort(r,s),s+=2,l.minLeftSideBearing=o.readShort(r,s),s+=2,l.minRightSideBearing=o.readShort(r,s),s+=2,l.xMaxExtent=o.readShort(r,s),s+=2,l.caretSlopeRise=o.readShort(r,s),s+=2,l.caretSlopeRun=o.readShort(r,s),s+=2,l.caretOffset=o.readShort(r,s),s+=2,s+=8,l.metricDataFormat=o.readShort(r,s),s+=2,l.numberOfHMetrics=o.readUshort(r,s),s+=2,l},e.hmtx={},e.hmtx.parse=function(r,s,a,o){for(var l=e._bin,c={aWidth:[],lsBearing:[]},u=0,f=0,h=0;h<o.maxp.numGlyphs;h++)h<o.hhea.numberOfHMetrics&&(u=l.readUshort(r,s),s+=2,f=l.readShort(r,s),s+=2),c.aWidth.push(u),c.lsBearing.push(f);return c},e.kern={},e.kern.parse=function(r,s,a,o){var l=e._bin,c=l.readUshort(r,s);if(s+=2,c==1)return e.kern.parseV1(r,s-2,a,o);var u=l.readUshort(r,s);s+=2;for(var f={glyph1:[],rval:[]},h=0;h<u;h++){s+=2,a=l.readUshort(r,s),s+=2;var d=l.readUshort(r,s);s+=2;var m=d>>>8;if((m&=15)!=0)throw"unknown kern table format: "+m;s=e.kern.readFormat0(r,s,f)}return f},e.kern.parseV1=function(r,s,a,o){var l=e._bin;l.readFixed(r,s),s+=4;var c=l.readUint(r,s);s+=4;for(var u={glyph1:[],rval:[]},f=0;f<c;f++){l.readUint(r,s),s+=4;var h=l.readUshort(r,s);s+=2,l.readUshort(r,s),s+=2;var d=h>>>8;if((d&=15)!=0)throw"unknown kern table format: "+d;s=e.kern.readFormat0(r,s,u)}return u},e.kern.readFormat0=function(r,s,a){var o=e._bin,l=-1,c=o.readUshort(r,s);s+=2,o.readUshort(r,s),s+=2,o.readUshort(r,s),s+=2,o.readUshort(r,s),s+=2;for(var u=0;u<c;u++){var f=o.readUshort(r,s);s+=2;var h=o.readUshort(r,s);s+=2;var d=o.readShort(r,s);s+=2,f!=l&&(a.glyph1.push(f),a.rval.push({glyph2:[],vals:[]}));var m=a.rval[a.rval.length-1];m.glyph2.push(h),m.vals.push(d),l=f}return s},e.loca={},e.loca.parse=function(r,s,a,o){var l=e._bin,c=[],u=o.head.indexToLocFormat,f=o.maxp.numGlyphs+1;if(u==0)for(var h=0;h<f;h++)c.push(l.readUshort(r,s+(h<<1))<<1);if(u==1)for(h=0;h<f;h++)c.push(l.readUint(r,s+(h<<2)));return c},e.maxp={},e.maxp.parse=function(r,s,a){var o=e._bin,l={},c=o.readUint(r,s);return s+=4,l.numGlyphs=o.readUshort(r,s),s+=2,c==65536&&(l.maxPoints=o.readUshort(r,s),s+=2,l.maxContours=o.readUshort(r,s),s+=2,l.maxCompositePoints=o.readUshort(r,s),s+=2,l.maxCompositeContours=o.readUshort(r,s),s+=2,l.maxZones=o.readUshort(r,s),s+=2,l.maxTwilightPoints=o.readUshort(r,s),s+=2,l.maxStorage=o.readUshort(r,s),s+=2,l.maxFunctionDefs=o.readUshort(r,s),s+=2,l.maxInstructionDefs=o.readUshort(r,s),s+=2,l.maxStackElements=o.readUshort(r,s),s+=2,l.maxSizeOfInstructions=o.readUshort(r,s),s+=2,l.maxComponentElements=o.readUshort(r,s),s+=2,l.maxComponentDepth=o.readUshort(r,s),s+=2),l},e.name={},e.name.parse=function(r,s,a){var o=e._bin,l={};o.readUshort(r,s),s+=2;var c=o.readUshort(r,s);s+=2,o.readUshort(r,s);for(var u,f=["copyright","fontFamily","fontSubfamily","ID","fullName","version","postScriptName","trademark","manufacturer","designer","description","urlVendor","urlDesigner","licence","licenceURL","---","typoFamilyName","typoSubfamilyName","compatibleFull","sampleText","postScriptCID","wwsFamilyName","wwsSubfamilyName","lightPalette","darkPalette"],h=s+=2,d=0;d<c;d++){var m=o.readUshort(r,s);s+=2;var g=o.readUshort(r,s);s+=2;var p=o.readUshort(r,s);s+=2;var _=o.readUshort(r,s);s+=2;var v=o.readUshort(r,s);s+=2;var S=o.readUshort(r,s);s+=2;var y,M=f[_],T=h+12*c+S;if(m==0)y=o.readUnicode(r,T,v/2);else if(m==3&&g==0)y=o.readUnicode(r,T,v/2);else if(g==0)y=o.readASCII(r,T,v);else if(g==1)y=o.readUnicode(r,T,v/2);else if(g==3)y=o.readUnicode(r,T,v/2);else{if(m!=1)throw"unknown encoding "+g+", platformID: "+m;y=o.readASCII(r,T,v),console.debug("reading unknown MAC encoding "+g+" as ASCII")}var w="p"+m+","+p.toString(16);l[w]==null&&(l[w]={}),l[w][M!==void 0?M:_]=y,l[w]._lang=p}for(var b in l)if(l[b].postScriptName!=null&&l[b]._lang==1033)return l[b];for(var b in l)if(l[b].postScriptName!=null&&l[b]._lang==0)return l[b];for(var b in l)if(l[b].postScriptName!=null&&l[b]._lang==3084)return l[b];for(var b in l)if(l[b].postScriptName!=null)return l[b];for(var b in l){u=b;break}return console.debug("returning name table with languageID "+l[u]._lang),l[u]},e["OS/2"]={},e["OS/2"].parse=function(r,s,a){var o=e._bin.readUshort(r,s);s+=2;var l={};if(o==0)e["OS/2"].version0(r,s,l);else if(o==1)e["OS/2"].version1(r,s,l);else if(o==2||o==3||o==4)e["OS/2"].version2(r,s,l);else{if(o!=5)throw"unknown OS/2 table version: "+o;e["OS/2"].version5(r,s,l)}return l},e["OS/2"].version0=function(r,s,a){var o=e._bin;return a.xAvgCharWidth=o.readShort(r,s),s+=2,a.usWeightClass=o.readUshort(r,s),s+=2,a.usWidthClass=o.readUshort(r,s),s+=2,a.fsType=o.readUshort(r,s),s+=2,a.ySubscriptXSize=o.readShort(r,s),s+=2,a.ySubscriptYSize=o.readShort(r,s),s+=2,a.ySubscriptXOffset=o.readShort(r,s),s+=2,a.ySubscriptYOffset=o.readShort(r,s),s+=2,a.ySuperscriptXSize=o.readShort(r,s),s+=2,a.ySuperscriptYSize=o.readShort(r,s),s+=2,a.ySuperscriptXOffset=o.readShort(r,s),s+=2,a.ySuperscriptYOffset=o.readShort(r,s),s+=2,a.yStrikeoutSize=o.readShort(r,s),s+=2,a.yStrikeoutPosition=o.readShort(r,s),s+=2,a.sFamilyClass=o.readShort(r,s),s+=2,a.panose=o.readBytes(r,s,10),s+=10,a.ulUnicodeRange1=o.readUint(r,s),s+=4,a.ulUnicodeRange2=o.readUint(r,s),s+=4,a.ulUnicodeRange3=o.readUint(r,s),s+=4,a.ulUnicodeRange4=o.readUint(r,s),s+=4,a.achVendID=[o.readInt8(r,s),o.readInt8(r,s+1),o.readInt8(r,s+2),o.readInt8(r,s+3)],s+=4,a.fsSelection=o.readUshort(r,s),s+=2,a.usFirstCharIndex=o.readUshort(r,s),s+=2,a.usLastCharIndex=o.readUshort(r,s),s+=2,a.sTypoAscender=o.readShort(r,s),s+=2,a.sTypoDescender=o.readShort(r,s),s+=2,a.sTypoLineGap=o.readShort(r,s),s+=2,a.usWinAscent=o.readUshort(r,s),s+=2,a.usWinDescent=o.readUshort(r,s),s+=2},e["OS/2"].version1=function(r,s,a){var o=e._bin;return s=e["OS/2"].version0(r,s,a),a.ulCodePageRange1=o.readUint(r,s),s+=4,a.ulCodePageRange2=o.readUint(r,s),s+=4},e["OS/2"].version2=function(r,s,a){var o=e._bin;return s=e["OS/2"].version1(r,s,a),a.sxHeight=o.readShort(r,s),s+=2,a.sCapHeight=o.readShort(r,s),s+=2,a.usDefault=o.readUshort(r,s),s+=2,a.usBreak=o.readUshort(r,s),s+=2,a.usMaxContext=o.readUshort(r,s),s+=2},e["OS/2"].version5=function(r,s,a){var o=e._bin;return s=e["OS/2"].version2(r,s,a),a.usLowerOpticalPointSize=o.readUshort(r,s),s+=2,a.usUpperOpticalPointSize=o.readUshort(r,s),s+=2},e.post={},e.post.parse=function(r,s,a){var o=e._bin,l={};return l.version=o.readFixed(r,s),s+=4,l.italicAngle=o.readFixed(r,s),s+=4,l.underlinePosition=o.readShort(r,s),s+=2,l.underlineThickness=o.readShort(r,s),s+=2,l},e==null&&(e={}),e.U==null&&(e.U={}),e.U.codeToGlyph=function(r,s){var a=r.cmap,o=-1;if(a.p0e4!=null?o=a.p0e4:a.p3e1!=null?o=a.p3e1:a.p1e0!=null?o=a.p1e0:a.p0e3!=null&&(o=a.p0e3),o==-1)throw"no familiar platform and encoding!";var l=a.tables[o];if(l.format==0)return s>=l.map.length?0:l.map[s];if(l.format==4){for(var c=-1,u=0;u<l.endCount.length;u++)if(s<=l.endCount[u]){c=u;break}return c==-1||l.startCount[c]>s?0:65535&(l.idRangeOffset[c]!=0?l.glyphIdArray[s-l.startCount[c]+(l.idRangeOffset[c]>>1)-(l.idRangeOffset.length-c)]:s+l.idDelta[c])}if(l.format==12){if(s>l.groups[l.groups.length-1][1])return 0;for(u=0;u<l.groups.length;u++){var f=l.groups[u];if(f[0]<=s&&s<=f[1])return f[2]+(s-f[0])}return 0}throw"unknown cmap table format "+l.format},e.U.glyphToPath=function(r,s){var a={cmds:[],crds:[]};if(r.SVG&&r.SVG.entries[s]){var o=r.SVG.entries[s];return o==null?a:(typeof o=="string"&&(o=e.SVG.toPath(o),r.SVG.entries[s]=o),o)}if(r.CFF){var l={x:0,y:0,stack:[],nStems:0,haveWidth:!1,width:r.CFF.Private?r.CFF.Private.defaultWidthX:0,open:!1},c=r.CFF,u=r.CFF.Private;if(c.ROS){for(var f=0;c.FDSelect[f+2]<=s;)f+=2;u=c.FDArray[c.FDSelect[f+1]].Private}e.U._drawCFF(r.CFF.CharStrings[s],l,c,u,a)}else r.glyf&&e.U._drawGlyf(s,r,a);return a},e.U._drawGlyf=function(r,s,a){var o=s.glyf[r];o==null&&(o=s.glyf[r]=e.glyf._parseGlyf(s,r)),o!=null&&(o.noc>-1?e.U._simpleGlyph(o,a):e.U._compoGlyph(o,s,a))},e.U._simpleGlyph=function(r,s){for(var a=0;a<r.noc;a++){for(var o=a==0?0:r.endPts[a-1]+1,l=r.endPts[a],c=o;c<=l;c++){var u=c==o?l:c-1,f=c==l?o:c+1,h=1&r.flags[c],d=1&r.flags[u],m=1&r.flags[f],g=r.xs[c],p=r.ys[c];if(c==o)if(h){if(!d){e.U.P.moveTo(s,g,p);continue}e.U.P.moveTo(s,r.xs[u],r.ys[u])}else d?e.U.P.moveTo(s,r.xs[u],r.ys[u]):e.U.P.moveTo(s,(r.xs[u]+g)/2,(r.ys[u]+p)/2);h?d&&e.U.P.lineTo(s,g,p):m?e.U.P.qcurveTo(s,g,p,r.xs[f],r.ys[f]):e.U.P.qcurveTo(s,g,p,(g+r.xs[f])/2,(p+r.ys[f])/2)}e.U.P.closePath(s)}},e.U._compoGlyph=function(r,s,a){for(var o=0;o<r.parts.length;o++){var l={cmds:[],crds:[]},c=r.parts[o];e.U._drawGlyf(c.glyphIndex,s,l);for(var u=c.m,f=0;f<l.crds.length;f+=2){var h=l.crds[f],d=l.crds[f+1];a.crds.push(h*u.a+d*u.b+u.tx),a.crds.push(h*u.c+d*u.d+u.ty)}for(f=0;f<l.cmds.length;f++)a.cmds.push(l.cmds[f])}},e.U._getGlyphClass=function(r,s){var a=e._lctf.getInterval(s,r);return a==-1?0:s[a+2]},e.U._applySubs=function(r,s,a,o){for(var l=r.length-s-1,c=0;c<a.tabs.length;c++)if(a.tabs[c]!=null){var u,f=a.tabs[c];if(!f.coverage||(u=e._lctf.coverageIndex(f.coverage,r[s]))!=-1){if(a.ltype==1)r[s],f.fmt==1?r[s]=r[s]+f.delta:r[s]=f.newg[u];else if(a.ltype==4)for(var h=f.vals[u],d=0;d<h.length;d++){var m=h[d],g=m.chain.length;if(!(g>l)){for(var p=!0,_=0,v=0;v<g;v++){for(;r[s+_+(1+v)]==-1;)_++;m.chain[v]!=r[s+_+(1+v)]&&(p=!1)}if(p){for(r[s]=m.nglyph,v=0;v<g+_;v++)r[s+v+1]=-1;break}}}else if(a.ltype==5&&f.fmt==2)for(var S=e._lctf.getInterval(f.cDef,r[s]),y=f.cDef[S+2],M=f.scset[y],T=0;T<M.length;T++){var w=M[T],b=w.input;if(!(b.length>l)){for(p=!0,v=0;v<b.length;v++){var x=e._lctf.getInterval(f.cDef,r[s+1+v]);if(S==-1&&f.cDef[x+2]!=b[v]){p=!1;break}}if(p){var A=w.substLookupRecords;for(d=0;d<A.length;d+=2)A[d],A[d+1]}}}else if(a.ltype==6&&f.fmt==3){if(!e.U._glsCovered(r,f.backCvg,s-f.backCvg.length)||!e.U._glsCovered(r,f.inptCvg,s)||!e.U._glsCovered(r,f.ahedCvg,s+f.inptCvg.length))continue;var P=f.lookupRec;for(T=0;T<P.length;T+=2){S=P[T];var R=o[P[T+1]];e.U._applySubs(r,s+S,R,o)}}}}},e.U._glsCovered=function(r,s,a){for(var o=0;o<s.length;o++)if(e._lctf.coverageIndex(s[o],r[a+o])==-1)return!1;return!0},e.U.glyphsToPath=function(r,s,a){for(var o={cmds:[],crds:[]},l=0,c=0;c<s.length;c++){var u=s[c];if(u!=-1){for(var f=c<s.length-1&&s[c+1]!=-1?s[c+1]:0,h=e.U.glyphToPath(r,u),d=0;d<h.crds.length;d+=2)o.crds.push(h.crds[d]+l),o.crds.push(h.crds[d+1]);for(a&&o.cmds.push(a),d=0;d<h.cmds.length;d++)o.cmds.push(h.cmds[d]);a&&o.cmds.push("X"),l+=r.hmtx.aWidth[u],c<s.length-1&&(l+=e.U.getPairAdjustment(r,u,f))}}return o},e.U.P={},e.U.P.moveTo=function(r,s,a){r.cmds.push("M"),r.crds.push(s,a)},e.U.P.lineTo=function(r,s,a){r.cmds.push("L"),r.crds.push(s,a)},e.U.P.curveTo=function(r,s,a,o,l,c,u){r.cmds.push("C"),r.crds.push(s,a,o,l,c,u)},e.U.P.qcurveTo=function(r,s,a,o,l){r.cmds.push("Q"),r.crds.push(s,a,o,l)},e.U.P.closePath=function(r){r.cmds.push("Z")},e.U._drawCFF=function(r,s,a,o,l){for(var c=s.stack,u=s.nStems,f=s.haveWidth,h=s.width,d=s.open,m=0,g=s.x,p=s.y,_=0,v=0,S=0,y=0,M=0,T=0,w=0,b=0,x=0,A=0,P={val:0,size:0};m<r.length;){e.CFF.getCharString(r,m,P);var R=P.val;if(m+=P.size,R=="o1"||R=="o18")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0;else if(R=="o3"||R=="o23")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0;else if(R=="o4")c.length>1&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),d&&e.U.P.closePath(l),p+=c.pop(),e.U.P.moveTo(l,g,p),d=!0;else if(R=="o5")for(;c.length>0;)g+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,g,p);else if(R=="o6"||R=="o7")for(var L=c.length,I=R=="o6",N=0;N<L;N++){var O=c.shift();I?g+=O:p+=O,I=!I,e.U.P.lineTo(l,g,p)}else if(R=="o8"||R=="o24"){L=c.length;for(var B=0;B+6<=L;)_=g+c.shift(),v=p+c.shift(),S=_+c.shift(),y=v+c.shift(),g=S+c.shift(),p=y+c.shift(),e.U.P.curveTo(l,_,v,S,y,g,p),B+=6;R=="o24"&&(g+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,g,p))}else{if(R=="o11")break;if(R=="o1234"||R=="o1235"||R=="o1236"||R=="o1237")R=="o1234"&&(v=p,S=(_=g+c.shift())+c.shift(),A=y=v+c.shift(),T=y,b=p,g=(w=(M=(x=S+c.shift())+c.shift())+c.shift())+c.shift(),e.U.P.curveTo(l,_,v,S,y,x,A),e.U.P.curveTo(l,M,T,w,b,g,p)),R=="o1235"&&(_=g+c.shift(),v=p+c.shift(),S=_+c.shift(),y=v+c.shift(),x=S+c.shift(),A=y+c.shift(),M=x+c.shift(),T=A+c.shift(),w=M+c.shift(),b=T+c.shift(),g=w+c.shift(),p=b+c.shift(),c.shift(),e.U.P.curveTo(l,_,v,S,y,x,A),e.U.P.curveTo(l,M,T,w,b,g,p)),R=="o1236"&&(_=g+c.shift(),v=p+c.shift(),S=_+c.shift(),A=y=v+c.shift(),T=y,w=(M=(x=S+c.shift())+c.shift())+c.shift(),b=T+c.shift(),g=w+c.shift(),e.U.P.curveTo(l,_,v,S,y,x,A),e.U.P.curveTo(l,M,T,w,b,g,p)),R=="o1237"&&(_=g+c.shift(),v=p+c.shift(),S=_+c.shift(),y=v+c.shift(),x=S+c.shift(),A=y+c.shift(),M=x+c.shift(),T=A+c.shift(),w=M+c.shift(),b=T+c.shift(),Math.abs(w-g)>Math.abs(b-p)?g=w+c.shift():p=b+c.shift(),e.U.P.curveTo(l,_,v,S,y,x,A),e.U.P.curveTo(l,M,T,w,b,g,p));else if(R=="o14"){if(c.length>0&&!f&&(h=c.shift()+a.nominalWidthX,f=!0),c.length==4){var q=c.shift(),F=c.shift(),k=c.shift(),U=c.shift(),z=e.CFF.glyphBySE(a,k),K=e.CFF.glyphBySE(a,U);e.U._drawCFF(a.CharStrings[z],s,a,o,l),s.x=q,s.y=F,e.U._drawCFF(a.CharStrings[K],s,a,o,l)}d&&(e.U.P.closePath(l),d=!1)}else if(R=="o19"||R=="o20")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0,m+=u+7>>3;else if(R=="o21")c.length>2&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),p+=c.pop(),g+=c.pop(),d&&e.U.P.closePath(l),e.U.P.moveTo(l,g,p),d=!0;else if(R=="o22")c.length>1&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),g+=c.pop(),d&&e.U.P.closePath(l),e.U.P.moveTo(l,g,p),d=!0;else if(R=="o25"){for(;c.length>6;)g+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,g,p);_=g+c.shift(),v=p+c.shift(),S=_+c.shift(),y=v+c.shift(),g=S+c.shift(),p=y+c.shift(),e.U.P.curveTo(l,_,v,S,y,g,p)}else if(R=="o26")for(c.length%2&&(g+=c.shift());c.length>0;)_=g,v=p+c.shift(),g=S=_+c.shift(),p=(y=v+c.shift())+c.shift(),e.U.P.curveTo(l,_,v,S,y,g,p);else if(R=="o27")for(c.length%2&&(p+=c.shift());c.length>0;)v=p,S=(_=g+c.shift())+c.shift(),y=v+c.shift(),g=S+c.shift(),p=y,e.U.P.curveTo(l,_,v,S,y,g,p);else if(R=="o10"||R=="o29"){var Z=R=="o10"?o:a;if(c.length==0)console.debug("error: empty stack");else{var X=c.pop(),H=Z.Subrs[X+Z.Bias];s.x=g,s.y=p,s.nStems=u,s.haveWidth=f,s.width=h,s.open=d,e.U._drawCFF(H,s,a,o,l),g=s.x,p=s.y,u=s.nStems,f=s.haveWidth,h=s.width,d=s.open}}else if(R=="o30"||R=="o31"){var V=c.length,j=(B=0,R=="o31");for(B+=V-(L=-3&V);B<L;)j?(v=p,S=(_=g+c.shift())+c.shift(),p=(y=v+c.shift())+c.shift(),L-B==5?(g=S+c.shift(),B++):g=S,j=!1):(_=g,v=p+c.shift(),S=_+c.shift(),y=v+c.shift(),g=S+c.shift(),L-B==5?(p=y+c.shift(),B++):p=y,j=!0),e.U.P.curveTo(l,_,v,S,y,g,p),B+=4}else{if((R+"").charAt(0)=="o")throw console.debug("Unknown operation: "+R,r),R;c.push(R)}}}s.x=g,s.y=p,s.nStems=u,s.haveWidth=f,s.width=h,s.open=d};var t=e,i={Typr:t};return n.Typr=t,n.default=i,Object.defineProperty(n,"__esModule",{value:!0}),n})({}).Typr}/*!
Custom bundle of woff2otf (https://github.com/arty-name/woff2otf) with fflate
(https://github.com/101arrowz/fflate) for use in Troika text rendering. 
Original licenses apply: 
- fflate: https://github.com/101arrowz/fflate/blob/master/LICENSE (MIT)
- woff2otf.js: https://github.com/arty-name/woff2otf/blob/master/woff2otf.js (Apache2)
*/function QS(){return(function(n){var e=Uint8Array,t=Uint16Array,i=Uint32Array,r=new e([0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0,0,0,0]),s=new e([0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,0,0]),a=new e([16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]),o=function(R,L){for(var I=new t(31),N=0;N<31;++N)I[N]=L+=1<<R[N-1];var O=new i(I[30]);for(N=1;N<30;++N)for(var B=I[N];B<I[N+1];++B)O[B]=B-I[N]<<5|N;return[I,O]},l=o(r,2),c=l[0],u=l[1];c[28]=258,u[258]=28;for(var f=o(s,0)[0],h=new t(32768),d=0;d<32768;++d){var m=(43690&d)>>>1|(21845&d)<<1;m=(61680&(m=(52428&m)>>>2|(13107&m)<<2))>>>4|(3855&m)<<4,h[d]=((65280&m)>>>8|(255&m)<<8)>>>1}var g=function(R,L,I){for(var N=R.length,O=0,B=new t(L);O<N;++O)++B[R[O]-1];var q,F=new t(L);for(O=0;O<L;++O)F[O]=F[O-1]+B[O-1]<<1;{q=new t(1<<L);var k=15-L;for(O=0;O<N;++O)if(R[O])for(var U=O<<4|R[O],z=L-R[O],K=F[R[O]-1]++<<z,Z=K|(1<<z)-1;K<=Z;++K)q[h[K]>>>k]=U}return q},p=new e(288);for(d=0;d<144;++d)p[d]=8;for(d=144;d<256;++d)p[d]=9;for(d=256;d<280;++d)p[d]=7;for(d=280;d<288;++d)p[d]=8;var _=new e(32);for(d=0;d<32;++d)_[d]=5;var v=g(p,9),S=g(_,5),y=function(R){for(var L=R[0],I=1;I<R.length;++I)R[I]>L&&(L=R[I]);return L},M=function(R,L,I){var N=L/8|0;return(R[N]|R[N+1]<<8)>>(7&L)&I},T=function(R,L){var I=L/8|0;return(R[I]|R[I+1]<<8|R[I+2]<<16)>>(7&L)},w=["unexpected EOF","invalid block type","invalid length/literal","invalid distance","stream finished","no stream handler",,"no callback","invalid UTF-8 data","extra field too long","date not in range 1980-2099","filename too long","stream finishing","invalid zip data"],b=function(R,L,I){var N=new Error(L||w[R]);if(N.code=R,Error.captureStackTrace&&Error.captureStackTrace(N,b),!I)throw N;return N},x=function(R,L,I){var N=R.length;if(!N||I&&!I.l&&N<5)return L||new e(0);var O=!L||I,B=!I||I.i;I||(I={}),L||(L=new e(3*N));var q,F=function(de){var De=L.length;if(de>De){var be=new e(Math.max(2*De,de));be.set(L),L=be}},k=I.f||0,U=I.p||0,z=I.b||0,K=I.l,Z=I.d,X=I.m,H=I.n,V=8*N;do{if(!K){I.f=k=M(R,U,1);var j=M(R,U+1,3);if(U+=3,!j){var le=R[(G=((q=U)/8|0)+(7&q&&1)+4)-4]|R[G-3]<<8,ge=G+le;if(ge>N){B&&b(0);break}O&&F(z+le),L.set(R.subarray(G,ge),z),I.b=z+=le,I.p=U=8*ge;continue}if(j==1)K=v,Z=S,X=9,H=5;else if(j==2){var oe=M(R,U,31)+257,te=M(R,U+10,15)+4,xe=oe+M(R,U+5,31)+1;U+=14;for(var Ae=new e(xe),Te=new e(19),ye=0;ye<te;++ye)Te[a[ye]]=M(R,U+3*ye,7);U+=3*te;var Ue=y(Te),me=(1<<Ue)-1,ke=g(Te,Ue);for(ye=0;ye<xe;){var G,fe=ke[M(R,U,me)];if(U+=15&fe,(G=fe>>>4)<16)Ae[ye++]=G;else{var Fe=0,we=0;for(G==16?(we=3+M(R,U,3),U+=2,Fe=Ae[ye-1]):G==17?(we=3+M(R,U,7),U+=3):G==18&&(we=11+M(R,U,127),U+=7);we--;)Ae[ye++]=Fe}}var he=Ae.subarray(0,oe),Re=Ae.subarray(oe);X=y(he),H=y(Re),K=g(he,X),Z=g(Re,H)}else b(1);if(U>V){B&&b(0);break}}O&&F(z+131072);for(var D=(1<<X)-1,E=(1<<H)-1,W=U;;W=U){var Q=(Fe=K[T(R,U)&D])>>>4;if((U+=15&Fe)>V){B&&b(0);break}if(Fe||b(2),Q<256)L[z++]=Q;else{if(Q==256){W=U,K=null;break}var ue=Q-254;if(Q>264){var ve=r[ye=Q-257];ue=M(R,U,(1<<ve)-1)+c[ye],U+=ve}var Me=Z[T(R,U)&E],ee=Me>>>4;if(Me||b(3),U+=15&Me,Re=f[ee],ee>3&&(ve=s[ee],Re+=T(R,U)&(1<<ve)-1,U+=ve),U>V){B&&b(0);break}O&&F(z+131072);for(var se=z+ue;z<se;z+=4)L[z]=L[z-Re],L[z+1]=L[z+1-Re],L[z+2]=L[z+2-Re],L[z+3]=L[z+3-Re];z=se}}I.l=K,I.p=W,I.b=z,K&&(k=1,I.m=X,I.d=Z,I.n=H)}while(!k);return z==L.length?L:(function(de,De,be){(be==null||be>de.length)&&(be=de.length);var Ee=new(de instanceof t?t:de instanceof i?i:e)(be-De);return Ee.set(de.subarray(De,be)),Ee})(L,0,z)},A=new e(0),P=typeof TextDecoder<"u"&&new TextDecoder;try{P.decode(A,{stream:!0})}catch{}return n.convert_streams=function(R){var L=new DataView(R),I=0;function N(){var oe=L.getUint16(I);return I+=2,oe}function O(){var oe=L.getUint32(I);return I+=4,oe}function B(oe){le.setUint16(ge,oe),ge+=2}function q(oe){le.setUint32(ge,oe),ge+=4}for(var F={signature:O(),flavor:O(),length:O(),numTables:N(),reserved:N(),totalSfntSize:O(),majorVersion:N(),minorVersion:N(),metaOffset:O(),metaLength:O(),metaOrigLength:O(),privOffset:O(),privLength:O()},k=0;Math.pow(2,k)<=F.numTables;)k++;k--;for(var U=16*Math.pow(2,k),z=16*F.numTables-U,K=12,Z=[],X=0;X<F.numTables;X++)Z.push({tag:O(),offset:O(),compLength:O(),origLength:O(),origChecksum:O()}),K+=16;var H,V=new Uint8Array(12+16*Z.length+Z.reduce((function(oe,te){return oe+te.origLength+4}),0)),j=V.buffer,le=new DataView(j),ge=0;return q(F.flavor),B(F.numTables),B(U),B(k),B(z),Z.forEach((function(oe){q(oe.tag),q(oe.origChecksum),q(K),q(oe.origLength),oe.outOffset=K,(K+=oe.origLength)%4!=0&&(K+=4-K%4)})),Z.forEach((function(oe){var te,xe=R.slice(oe.offset,oe.offset+oe.compLength);if(oe.compLength!=oe.origLength){var Ae=new Uint8Array(oe.origLength);te=new Uint8Array(xe,2),x(te,Ae)}else Ae=new Uint8Array(xe);V.set(Ae,oe.outOffset);var Te=0;(K=oe.outOffset+oe.origLength)%4!=0&&(Te=4-K%4),V.set(new Uint8Array(Te).buffer,oe.outOffset+oe.origLength),H=K+Te})),j.slice(0,H)},Object.defineProperty(n,"__esModule",{value:!0}),n})({}).convert_streams}function eM(n,e){const t={M:2,L:2,Q:4,C:6,Z:0},i={C:"18g,ca,368,1kz",D:"17k,6,2,2+4,5+c,2+6,2+1,10+1,9+f,j+11,2+1,a,2,2+1,15+2,3,j+2,6+3,2+8,2,2,2+1,w+a,4+e,3+3,2,3+2,3+5,23+w,2f+4,3,2+9,2,b,2+3,3,1k+9,6+1,3+1,2+2,2+d,30g,p+y,1,1+1g,f+x,2,sd2+1d,jf3+4,f+3,2+4,2+2,b+3,42,2,4+2,2+1,2,3,t+1,9f+w,2,el+2,2+g,d+2,2l,2+1,5,3+1,2+1,2,3,6,16wm+1v",R:"17m+3,2,2,6+3,m,15+2,2+2,h+h,13,3+8,2,2,3+1,2,p+1,x,5+4,5,a,2,2,3,u,c+2,g+1,5,2+1,4+1,5j,6+1,2,b,2+2,f,2+1,1s+2,2,3+1,7,1ez0,2,2+1,4+4,b,4,3,b,42,2+2,4,3,2+1,2,o+3,ae,ep,x,2o+2,3+1,3,5+1,6",L:"x9u,jff,a,fd,jv",T:"4t,gj+33,7o+4,1+1,7c+18,2,2+1,2+1,2,21+a,2,1b+k,h,2u+6,3+5,3+1,2+3,y,2,v+q,2k+a,1n+8,a,p+3,2+8,2+2,2+4,18+2,3c+e,2+v,1k,2,5+7,5,4+6,b+1,u,1n,5+3,9,l+1,r,3+1,1m,5+1,5+1,3+2,4,v+1,4,c+1,1m,5+4,2+1,5,l+1,n+5,2,1n,3,2+3,9,8+1,c+1,v,1q,d,1f,4,1m+2,6+2,2+3,8+1,c+1,u,1n,3,7,6+1,l+1,t+1,1m+1,5+3,9,l+1,u,21,8+2,2,2j,3+6,d+7,2r,3+8,c+5,23+1,s,2,2,1k+d,2+4,2+1,6+a,2+z,a,2v+3,2+5,2+1,3+1,q+1,5+2,h+3,e,3+1,7,g,jk+2,qb+2,u+2,u+1,v+1,1t+1,2+6,9,3+a,a,1a+2,3c+1,z,3b+2,5+1,a,7+2,64+1,3,1n,2+6,2,2,3+7,7+9,3,1d+d,1,1+1,1s+3,1d,2+4,2,6,15+8,d+1,x+3,3+1,2+2,1l,2+1,4,2+2,1n+7,3+1,49+2,2+c,2+6,5,7,4+1,5j+1l,2+4,ek,3+1,r+4,1e+4,6+5,2p+c,1+3,1,1+2,1+b,2db+2,3y,2p+v,ff+3,30+1,n9x,1+2,2+9,x+1,29+1,7l,4,5,q+1,6,48+1,r+h,e,13+7,q+a,1b+2,1d,3+3,3+1,14,1w+5,3+1,3+1,d,9,1c,1g,2+2,3+1,6+1,2,17+1,9,6n,3,5,fn5,ki+f,h+f,5s,6y+2,ea,6b,46+4,1af+2,2+1,6+3,15+2,5,4m+1,fy+3,as+1,4a+a,4x,1j+e,1l+2,1e+3,3+1,1y+2,11+4,2+7,1r,d+1,1h+8,b+3,3,2o+2,3,2+1,7,4h,4+7,m+1,1m+1,4,12+6,4+4,5g+7,3+2,2,o,2d+5,2,5+1,2+1,6n+3,7+1,2+1,s+1,2e+7,3,2+1,2z,2,3+5,2,2u+2,3+3,2+4,78+8,2+1,75+1,2,5,41+3,3+1,5,x+9,15+5,3+3,9,a+5,3+2,1b+c,2+1,bb+6,2+5,2,2b+l,3+6,2+1,2+1,3f+5,4,2+1,2+6,2,21+1,4,2,9o+1,470+8,at4+4,1o+6,t5,1s+3,2a,f5l+1,2+3,43o+2,a+7,1+7,3+6,v+3,45+2,1j0+1i,5+1d,9,f,n+4,2+e,11t+6,2+g,3+6,2+1,2+4,7a+6,c6+3,15t+6,32+6,1,gzau,v+2n,3l+6n"},r=1,s=2,a=4,o=8,l=16,c=32;let u;function f(w){if(!u){const b={R:s,L:r,D:a,C:l,U:c,T:o};u=new Map;for(let x in i){let A=0;i[x].split(",").forEach(P=>{let[R,L]=P.split("+");R=parseInt(R,36),L=L?parseInt(L,36):0,u.set(A+=R,b[x]);for(let I=L;I--;)u.set(++A,b[x])})}}return u.get(w)||c}const h=1,d=2,m=3,g=4,p=[null,"isol","init","fina","medi"];function _(w){const b=new Uint8Array(w.length);let x=c,A=h,P=-1;for(let R=0;R<w.length;R++){const L=w.codePointAt(R);let I=f(L)|0,N=h;I&o||(x&(r|a|l)?I&(s|a|l)?(N=m,(A===h||A===m)&&b[P]++):I&(r|c)&&(A===d||A===g)&&b[P]--:x&(s|c)&&(A===d||A===g)&&b[P]--,A=b[R]=N,x=I,P=R,L>65535&&R++)}return b}function v(w,b){const x=[];for(let P=0;P<b.length;P++){const R=b.codePointAt(P);R>65535&&P++,x.push(n.U.codeToGlyph(w,R))}const A=w.GSUB;if(A){const{lookupList:P,featureList:R}=A;let L;const I=/^(rlig|liga|mset|isol|init|fina|medi|half|pres|blws|ccmp)$/,N=[];R.forEach(O=>{if(I.test(O.tag))for(let B=0;B<O.tab.length;B++){if(N[O.tab[B]])continue;N[O.tab[B]]=!0;const q=P[O.tab[B]],F=/^(isol|init|fina|medi)$/.test(O.tag);F&&!L&&(L=_(b));for(let k=0;k<x.length;k++)(!L||!F||p[L[k]]===O.tag)&&n.U._applySubs(x,k,q,P)}})}return x}function S(w,b){const x=new Int16Array(b.length*3);let A=0;for(;A<b.length;A++){const I=b[A];if(I===-1)continue;x[A*3+2]=w.hmtx.aWidth[I];const N=w.GPOS;if(N){const O=N.lookupList;for(let B=0;B<O.length;B++){const q=O[B];for(let F=0;F<q.tabs.length;F++){const k=q.tabs[F];if(q.ltype===1){if(n._lctf.coverageIndex(k.coverage,I)!==-1&&k.pos){L(k.pos,A);break}}else if(q.ltype===2){let U=null,z=P();if(z!==-1){const K=n._lctf.coverageIndex(k.coverage,b[z]);if(K!==-1){if(k.fmt===1){const Z=k.pairsets[K];for(let X=0;X<Z.length;X++)Z[X].gid2===I&&(U=Z[X])}else if(k.fmt===2){const Z=n.U._getGlyphClass(b[z],k.classDef1),X=n.U._getGlyphClass(I,k.classDef2);U=k.matrix[Z][X]}if(U){U.val1&&L(U.val1,z),U.val2&&L(U.val2,A);break}}}}else if(q.ltype===4){const U=n._lctf.coverageIndex(k.markCoverage,I);if(U!==-1){const z=P(R),K=z===-1?-1:n._lctf.coverageIndex(k.baseCoverage,b[z]);if(K!==-1){const Z=k.markArray[U],X=k.baseArray[K][Z.markClass];x[A*3]=X.x-Z.x+x[z*3]-x[z*3+2],x[A*3+1]=X.y-Z.y+x[z*3+1];break}}}else if(q.ltype===6){const U=n._lctf.coverageIndex(k.mark1Coverage,I);if(U!==-1){const z=P();if(z!==-1){const K=b[z];if(y(w,K)===3){const Z=n._lctf.coverageIndex(k.mark2Coverage,K);if(Z!==-1){const X=k.mark1Array[U],H=k.mark2Array[Z][X.markClass];x[A*3]=H.x-X.x+x[z*3]-x[z*3+2],x[A*3+1]=H.y-X.y+x[z*3+1];break}}}}}}}}else if(w.kern&&!w.cff){const O=P();if(O!==-1){const B=w.kern.glyph1.indexOf(b[O]);if(B!==-1){const q=w.kern.rval[B].glyph2.indexOf(I);q!==-1&&(x[O*3+2]+=w.kern.rval[B].vals[q])}}}}return x;function P(I){for(let N=A-1;N>=0;N--)if(b[N]!==-1&&(!I||I(b[N])))return N;return-1}function R(I){return y(w,I)===1}function L(I,N){for(let O=0;O<3;O++)x[N*3+O]+=I[O]||0}}function y(w,b){const x=w.GDEF&&w.GDEF.glyphClassDef;return x?n.U._getGlyphClass(b,x):0}function M(...w){for(let b=0;b<w.length;b++)if(typeof w[b]=="number")return w[b]}function T(w){const b=Object.create(null),x=w["OS/2"],A=w.hhea,P=w.head.unitsPerEm,R=M(x&&x.sTypoAscender,A&&A.ascender,P),L={unitsPerEm:P,ascender:R,descender:M(x&&x.sTypoDescender,A&&A.descender,0),capHeight:M(x&&x.sCapHeight,R),xHeight:M(x&&x.sxHeight,R),lineGap:M(x&&x.sTypoLineGap,A&&A.lineGap),supportsCodePoint(I){return n.U.codeToGlyph(w,I)>0},forEachGlyph(I,N,O,B){let q=0;const F=1/L.unitsPerEm*N,k=v(w,I);let U=0;const z=S(w,k);return k.forEach((K,Z)=>{if(K!==-1){let X=b[K];if(!X){const{cmds:H,crds:V}=n.U.glyphToPath(w,K);let j="",le=0;for(let Ae=0,Te=H.length;Ae<Te;Ae++){const ye=t[H[Ae]];j+=H[Ae];for(let Ue=1;Ue<=ye;Ue++)j+=(Ue>1?",":"")+V[le++]}let ge,oe,te,xe;if(V.length){ge=oe=1/0,te=xe=-1/0;for(let Ae=0,Te=V.length;Ae<Te;Ae+=2){let ye=V[Ae],Ue=V[Ae+1];ye<ge&&(ge=ye),Ue<oe&&(oe=Ue),ye>te&&(te=ye),Ue>xe&&(xe=Ue)}}else ge=te=oe=xe=0;X=b[K]={index:K,advanceWidth:w.hmtx.aWidth[K],xMin:ge,yMin:oe,xMax:te,yMax:xe,path:j}}B.call(null,X,q+z[Z*3]*F,z[Z*3+1]*F,U),q+=z[Z*3+2]*F,O&&(q+=O*N)}U+=I.codePointAt(U)>65535?2:1}),q}};return L}return function(b){const x=new Uint8Array(b,0,4),A=n._bin.readASCII(x,0,4);if(A==="wOFF")b=e(b);else if(A==="wOF2")throw new Error("woff2 fonts not supported");return T(n.parse(b)[0])}}const tM=Js({name:"Typr Font Parser",dependencies:[JS,QS,eM],init(n,e,t){const i=n(),r=e();return t(i,r)}});/*!
Custom bundle of @unicode-font-resolver/client v1.0.2 (https://github.com/lojjic/unicode-font-resolver)
for use in Troika text rendering. 
Original MIT license applies
*/function nM(){return(function(n){var e=function(){this.buckets=new Map};e.prototype.add=function(S){var y=S>>5;this.buckets.set(y,(this.buckets.get(y)||0)|1<<(31&S))},e.prototype.has=function(S){var y=this.buckets.get(S>>5);return y!==void 0&&(y&1<<(31&S))!=0},e.prototype.serialize=function(){var S=[];return this.buckets.forEach((function(y,M){S.push((+M).toString(36)+":"+y.toString(36))})),S.join(",")},e.prototype.deserialize=function(S){var y=this;this.buckets.clear(),S.split(",").forEach((function(M){var T=M.split(":");y.buckets.set(parseInt(T[0],36),parseInt(T[1],36))}))};var t=Math.pow(2,8),i=t-1,r=~i;function s(S){var y=(function(T){return T&r})(S).toString(16),M=(function(T){return(T&r)+t-1})(S).toString(16);return"codepoint-index/plane"+(S>>16)+"/"+y+"-"+M+".json"}function a(S,y){var M=S&i,T=y.codePointAt(M/6|0);return((T=(T||48)-48)&1<<M%6)!=0}function o(S,y){var M;(M=S,M.replace(/U\+/gi,"").replace(/^,+|,+$/g,"").split(/,+/).map((function(T){return T.split("-").map((function(w){return parseInt(w.trim(),16)}))}))).forEach((function(T){var w=T[0],b=T[1];b===void 0&&(b=w),y(w,b)}))}function l(S,y){o(S,(function(M,T){for(var w=M;w<=T;w++)y(w)}))}var c={},u={},f=new WeakMap,h="https://cdn.jsdelivr.net/gh/lojjic/unicode-font-resolver@v1.0.1/packages/data";function d(S){var y=f.get(S);return y||(y=new e,l(S.ranges,(function(M){return y.add(M)})),f.set(S,y)),y}var m,g=new Map;function p(S,y,M){return S[y]?y:S[M]?M:(function(T){for(var w in T)return w})(S)}function _(S,y){var M=y;if(!S.includes(M)){M=1/0;for(var T=0;T<S.length;T++)Math.abs(S[T]-y)<Math.abs(M-y)&&(M=S[T])}return M}function v(S){return m||(m=new Set,l("9-D,20,85,A0,1680,2000-200A,2028-202F,205F,3000",(function(y){m.add(y)}))),m.has(S)}return n.CodePointSet=e,n.clearCache=function(){c={},u={}},n.getFontsForString=function(S,y){y===void 0&&(y={});var M,T=y.lang;T===void 0&&(T=new RegExp("\\p{Script=Hangul}","u").test(M=S)?"ko":new RegExp("\\p{Script=Hiragana}|\\p{Script=Katakana}","u").test(M)?"ja":"en");var w=y.category;w===void 0&&(w="sans-serif");var b=y.style;b===void 0&&(b="normal");var x=y.weight;x===void 0&&(x=400);var A=(y.dataUrl||h).replace(/\/$/g,""),P=new Map,R=new Uint8Array(S.length),L={},I={},N=new Array(S.length),O=new Map,B=!1;function q(U){var z=g.get(U);return z||(z=fetch(A+"/"+U).then((function(K){if(!K.ok)throw new Error(K.statusText);return K.json().then((function(Z){if(!Array.isArray(Z)||Z[0]!==1)throw new Error("Incorrect schema version; need 1, got "+Z[0]);return Z[1]}))})).catch((function(K){if(A!==h)return B||(console.error('unicode-font-resolver: Failed loading from dataUrl "'+A+'", trying default CDN. '+K.message),B=!0),A=h,g.delete(U),q(U);throw K})),g.set(U,z)),z}for(var F=function(U){var z=S.codePointAt(U),K=s(z);N[U]=K,c[K]||O.has(K)||O.set(K,q(K).then((function(Z){c[K]=Z}))),z>65535&&(U++,k=U)},k=0;k<S.length;k++)F(k);return Promise.all(O.values()).then((function(){O.clear();for(var U=function(K){var Z=S.codePointAt(K),X=null,H=c[N[K]],V=void 0;for(var j in H){var le=I[j];if(le===void 0&&(le=I[j]=new RegExp(j).test(T||"en")),le){for(var ge in V=j,H[j])if(a(Z,H[j][ge])){X=ge;break}break}}if(!X){e:for(var oe in H)if(oe!==V){for(var te in H[oe])if(a(Z,H[oe][te])){X=te;break e}}}X||(console.debug("No font coverage for U+"+Z.toString(16)),X="latin"),N[K]=X,u[X]||O.has(X)||O.set(X,q("font-meta/"+X+".json").then((function(xe){u[X]=xe}))),Z>65535&&(K++,z=K)},z=0;z<S.length;z++)U(z);return Promise.all(O.values())})).then((function(){for(var U,z=null,K=0;K<S.length;K++){var Z=S.codePointAt(K);if(z&&(v(Z)||d(z).has(Z)))R[K]=R[K-1];else{z=u[N[K]];var X=L[z.id];if(!X){var H=z.typeforms,V=p(H,w,"sans-serif"),j=p(H[V],b,"normal"),le=_((U=H[V])===null||U===void 0?void 0:U[j],x);X=L[z.id]=A+"/font-files/"+z.id+"/"+V+"."+j+"."+le+".woff"}var ge=P.get(X);ge==null&&(ge=P.size,P.set(X,ge)),R[K]=ge}Z>65535&&(K++,R[K]=R[K-1])}return{fontUrls:Array.from(P.keys()),chars:R}}))},Object.defineProperty(n,"__esModule",{value:!0}),n})({})}function iM(n,e){const t=Object.create(null),i=Object.create(null);function r(a,o){const l=c=>{console.error(`Failure loading font ${a}`,c)};try{const c=new XMLHttpRequest;c.open("get",a,!0),c.responseType="arraybuffer",c.onload=function(){if(c.status>=400)l(new Error(c.statusText));else if(c.status>0)try{const u=n(c.response);u.src=a,o(u)}catch(u){l(u)}},c.onerror=l,c.send()}catch(c){l(c)}}function s(a,o){let l=t[a];l?o(l):i[a]?i[a].push(o):(i[a]=[o],r(a,c=>{c.src=a,t[a]=c,i[a].forEach(u=>u(c)),delete i[a]}))}return function(a,o,{lang:l,fonts:c=[],style:u="normal",weight:f="normal",unicodeFontsURL:h}={}){const d=new Uint8Array(a.length),m=[];a.length||v();const g=new Map,p=[];if(u!=="italic"&&(u="normal"),typeof f!="number"&&(f=f==="bold"?700:400),c&&!Array.isArray(c)&&(c=[c]),c=c.slice().filter(y=>!y.lang||y.lang.test(l)).reverse(),c.length){let w=0;(function b(x=0){for(let A=x,P=a.length;A<P;A++){const R=a.codePointAt(A);if(w===1&&m[d[A-1]].supportsCodePoint(R)||A>0&&/\s/.test(a[A]))d[A]=d[A-1],w===2&&(p[p.length-1][1]=A);else for(let L=d[A],I=c.length;L<=I;L++)if(L===I){const N=w===2?p[p.length-1]:p[p.length]=[A,A];N[1]=A,w=2}else{d[A]=L;const{src:N,unicodeRange:O}=c[L];if(!O||S(R,O)){const B=t[N];if(!B){s(N,()=>{b(A)});return}if(B.supportsCodePoint(R)){let q=g.get(B);typeof q!="number"&&(q=m.length,m.push(B),g.set(B,q)),d[A]=q,w=1;break}}}R>65535&&A+1<P&&(d[A+1]=d[A],A++,w===2&&(p[p.length-1][1]=A))}_()})()}else p.push([0,a.length-1]),_();function _(){if(p.length){const y=p.map(M=>a.substring(M[0],M[1]+1)).join(`
`);e.getFontsForString(y,{lang:l||void 0,style:u,weight:f,dataUrl:h}).then(({fontUrls:M,chars:T})=>{const w=m.length;let b=0;p.forEach(A=>{for(let P=0,R=A[1]-A[0];P<=R;P++)d[A[0]+P]=T[b++]+w;b++});let x=0;M.forEach((A,P)=>{s(A,R=>{m[P+w]=R,++x===M.length&&v()})})})}else v()}function v(){o({chars:d,fonts:m})}function S(y,M){for(let T=0;T<M.length;T++){const[w,b=w]=M[T];if(w<=y&&y<=b)return!0}return!1}}}const rM=Js({name:"FontResolver",dependencies:[iM,tM,nM],init(n,e,t){return n(e,t())}});function sM(n,e){const i=/[\u00AD\u034F\u061C\u115F-\u1160\u17B4-\u17B5\u180B-\u180E\u200B-\u200F\u202A-\u202E\u2060-\u206F\u3164\uFE00-\uFE0F\uFEFF\uFFA0\uFFF0-\uFFF8]/,r="[^\\S\\u00A0]",s=new RegExp(`${r}|[\\-\\u007C\\u00AD\\u2010\\u2012-\\u2014\\u2027\\u2056\\u2E17\\u2E40]`);function a({text:m,lang:g,fonts:p,style:_,weight:v,preResolvedFonts:S,unicodeFontsURL:y},M){const T=({chars:w,fonts:b})=>{let x,A;const P=[];for(let R=0;R<w.length;R++)w[R]!==A?(A=w[R],P.push(x={start:R,end:R,fontObj:b[w[R]]})):x.end=R;M(P)};S?T(S):n(m,T,{lang:g,fonts:p,style:_,weight:v,unicodeFontsURL:y})}function o({text:m="",font:g,lang:p,sdfGlyphSize:_=64,fontSize:v=400,fontWeight:S=1,fontStyle:y="normal",letterSpacing:M=0,lineHeight:T="normal",maxWidth:w=1/0,direction:b,textAlign:x="left",textIndent:A=0,whiteSpace:P="normal",overflowWrap:R="normal",anchorX:L=0,anchorY:I=0,metricsOnly:N=!1,unicodeFontsURL:O,preResolvedFonts:B=null,includeCaretPositions:q=!1,chunkedBoundsSize:F=8192,colorRanges:k=null},U){const z=f(),K={fontLoad:0,typesetting:0};m.indexOf("\r")>-1&&(console.info("Typesetter: got text with \\r chars; normalizing to \\n"),m=m.replace(/\r\n/g,`
`).replace(/\r/g,`
`)),v=+v,M=+M,w=+w,T=T||"normal",A=+A,a({text:m,lang:p,style:y,weight:S,fonts:typeof g=="string"?[{src:g}]:g,unicodeFontsURL:O,preResolvedFonts:B},Z=>{K.fontLoad=f()-z;const X=isFinite(w);let H=null,V=null,j=null,le=null,ge=null,oe=null,te=null,xe=null,Ae=0,Te=0,ye=P!=="nowrap";const Ue=new Map,me=f();let ke=A,G=0,fe=new h;const Fe=[fe];Z.forEach(E=>{const{fontObj:W}=E,{ascender:Q,descender:ue,unitsPerEm:ve,lineGap:Me,capHeight:ee,xHeight:se}=W;let de=Ue.get(W);if(!de){const Le=v/ve,Ye=T==="normal"?(Q-ue+Me)*Le:T*v,Y=(Ye-(Q-ue)*Le)/2,_e=Math.min(Ye,(Q-ue)*Le),re=(Q+ue)/2*Le+_e/2;de={index:Ue.size,src:W.src,fontObj:W,fontSizeMult:Le,unitsPerEm:ve,ascender:Q*Le,descender:ue*Le,capHeight:ee*Le,xHeight:se*Le,lineHeight:Ye,baseline:-Y-Q*Le,caretTop:re,caretBottom:re-_e},Ue.set(W,de)}const{fontSizeMult:De}=de,be=m.slice(E.start,E.end+1);let Ee,He;W.forEachGlyph(be,v,M,(Le,Ye,Y,_e)=>{Ye+=G,_e+=E.start,Ee=Ye,He=Le;const re=m.charAt(_e),Pe=Le.advanceWidth*De,Se=fe.count;let ce;if("isEmpty"in Le||(Le.isWhitespace=!!re&&new RegExp(r).test(re),Le.canBreakAfter=!!re&&s.test(re),Le.isEmpty=Le.xMin===Le.xMax||Le.yMin===Le.yMax||i.test(re)),!Le.isWhitespace&&!Le.isEmpty&&Te++,ye&&X&&!Le.isWhitespace&&Ye+Pe+ke>w&&Se){if(fe.glyphAt(Se-1).glyphObj.canBreakAfter)ce=new h,ke=-Ye;else for(let Ze=Se;Ze--;)if(Ze===0&&R==="break-word"){ce=new h,ke=-Ye;break}else if(fe.glyphAt(Ze).glyphObj.canBreakAfter){ce=fe.splitAt(Ze+1);const ot=ce.glyphAt(0).x;ke-=ot;for(let et=ce.count;et--;)ce.glyphAt(et).x-=ot;break}ce&&(fe.isSoftWrapped=!0,fe=ce,Fe.push(fe),Ae=w)}let Ne=fe.glyphAt(fe.count);Ne.glyphObj=Le,Ne.x=Ye+ke,Ne.y=Y,Ne.width=Pe,Ne.charIndex=_e,Ne.fontData=de,re===`
`&&(fe=new h,Fe.push(fe),ke=-(Ye+Pe+M*v)+A)}),G=Ee+He.advanceWidth*De+M*v});let we=0;Fe.forEach(E=>{let W=!0;for(let Q=E.count;Q--;){const ue=E.glyphAt(Q);W&&!ue.glyphObj.isWhitespace&&(E.width=ue.x+ue.width,E.width>Ae&&(Ae=E.width),W=!1);let{lineHeight:ve,capHeight:Me,xHeight:ee,baseline:se}=ue.fontData;ve>E.lineHeight&&(E.lineHeight=ve);const de=se-E.baseline;de<0&&(E.baseline+=de,E.cap+=de,E.ex+=de),E.cap=Math.max(E.cap,E.baseline+Me),E.ex=Math.max(E.ex,E.baseline+ee)}E.baseline-=we,E.cap-=we,E.ex-=we,we+=E.lineHeight});let he=0,Re=0;if(L&&(typeof L=="number"?he=-L:typeof L=="string"&&(he=-Ae*(L==="left"?0:L==="center"?.5:L==="right"?1:c(L)))),I&&(typeof I=="number"?Re=-I:typeof I=="string"&&(Re=I==="top"?0:I==="top-baseline"?-Fe[0].baseline:I==="top-cap"?-Fe[0].cap:I==="top-ex"?-Fe[0].ex:I==="middle"?we/2:I==="bottom"?we:I==="bottom-baseline"?-Fe[Fe.length-1].baseline:c(I)*we)),!N){const E=e.getEmbeddingLevels(m,b);H=new Uint16Array(Te),V=new Uint8Array(Te),j=new Float32Array(Te*2),le={},te=[1/0,1/0,-1/0,-1/0],xe=[],q&&(oe=new Float32Array(m.length*4)),k&&(ge=new Uint8Array(Te*3));let W=0,Q=-1,ue=-1,ve,Me;if(Fe.forEach((ee,se)=>{let{count:de,width:De}=ee;if(de>0){let be=0;for(let _e=de;_e--&&ee.glyphAt(_e).glyphObj.isWhitespace;)be++;let Ee=0,He=0;if(x==="center")Ee=(Ae-De)/2;else if(x==="right")Ee=Ae-De;else if(x==="justify"&&ee.isSoftWrapped){let _e=0;for(let re=de-be;re--;)ee.glyphAt(re).glyphObj.isWhitespace&&_e++;He=(Ae-De)/_e}if(He||Ee){let _e=0;for(let re=0;re<de;re++){let Pe=ee.glyphAt(re);const Se=Pe.glyphObj;Pe.x+=Ee+_e,He!==0&&Se.isWhitespace&&re<de-be&&(_e+=He,Pe.width+=He)}}const Le=e.getReorderSegments(m,E,ee.glyphAt(0).charIndex,ee.glyphAt(ee.count-1).charIndex);for(let _e=0;_e<Le.length;_e++){const[re,Pe]=Le[_e];let Se=1/0,ce=-1/0;for(let Ne=0;Ne<de;Ne++)if(ee.glyphAt(Ne).charIndex>=re){let Ze=Ne,ot=Ne;for(;ot<de;ot++){let et=ee.glyphAt(ot);if(et.charIndex>Pe)break;ot<de-be&&(Se=Math.min(Se,et.x),ce=Math.max(ce,et.x+et.width))}for(let et=Ze;et<ot;et++){const Vt=ee.glyphAt(et);Vt.x=ce-(Vt.x+Vt.width-Se)}break}}let Ye;const Y=_e=>Ye=_e;for(let _e=0;_e<de;_e++){const re=ee.glyphAt(_e);Ye=re.glyphObj;const Pe=Ye.index,Se=E.levels[re.charIndex]&1;if(Se){const ce=e.getMirroredCharacter(m[re.charIndex]);ce&&re.fontData.fontObj.forEachGlyph(ce,0,0,Y)}if(q){const{charIndex:ce,fontData:Ne}=re,Ze=re.x+he,ot=re.x+re.width+he;oe[ce*4]=Se?ot:Ze,oe[ce*4+1]=Se?Ze:ot,oe[ce*4+2]=ee.baseline+Ne.caretBottom+Re,oe[ce*4+3]=ee.baseline+Ne.caretTop+Re;const et=ce-Q;et>1&&u(oe,Q,et),Q=ce}if(k){const{charIndex:ce}=re;for(;ce>ue;)ue++,k.hasOwnProperty(ue)&&(Me=k[ue])}if(!Ye.isWhitespace&&!Ye.isEmpty){const ce=W++,{fontSizeMult:Ne,src:Ze,index:ot}=re.fontData,et=le[Ze]||(le[Ze]={});et[Pe]||(et[Pe]={path:Ye.path,pathBounds:[Ye.xMin,Ye.yMin,Ye.xMax,Ye.yMax]});const Vt=re.x+he,Kt=re.y+ee.baseline+Re;j[ce*2]=Vt,j[ce*2+1]=Kt;const Fn=Vt+Ye.xMin*Ne,gi=Kt+Ye.yMin*Ne,_i=Vt+Ye.xMax*Ne,Kn=Kt+Ye.yMax*Ne;Fn<te[0]&&(te[0]=Fn),gi<te[1]&&(te[1]=gi),_i>te[2]&&(te[2]=_i),Kn>te[3]&&(te[3]=Kn),ce%F===0&&(ve={start:ce,end:ce,rect:[1/0,1/0,-1/0,-1/0]},xe.push(ve)),ve.end++;const Ft=ve.rect;if(Fn<Ft[0]&&(Ft[0]=Fn),gi<Ft[1]&&(Ft[1]=gi),_i>Ft[2]&&(Ft[2]=_i),Kn>Ft[3]&&(Ft[3]=Kn),H[ce]=Pe,V[ce]=ot,k){const ni=ce*3;ge[ni]=Me>>16&255,ge[ni+1]=Me>>8&255,ge[ni+2]=Me&255}}}}}),oe){const ee=m.length-Q;ee>1&&u(oe,Q,ee)}}const D=[];Ue.forEach(({index:E,src:W,unitsPerEm:Q,ascender:ue,descender:ve,lineHeight:Me,capHeight:ee,xHeight:se})=>{D[E]={src:W,unitsPerEm:Q,ascender:ue,descender:ve,lineHeight:Me,capHeight:ee,xHeight:se}}),K.typesetting=f()-me,U({glyphIds:H,glyphFontIndices:V,glyphPositions:j,glyphData:le,fontData:D,caretPositions:oe,glyphColors:ge,chunkedBounds:xe,fontSize:v,topBaseline:Re+Fe[0].baseline,blockBounds:[he,Re-we,he+Ae,Re],visibleBounds:te,timings:K})})}function l(m,g){o({...m,metricsOnly:!0},p=>{const[_,v,S,y]=p.blockBounds;g({width:S-_,height:y-v})})}function c(m){let g=m.match(/^([\d.]+)%$/),p=g?parseFloat(g[1]):NaN;return isNaN(p)?0:p/100}function u(m,g,p){const _=m[g*4],v=m[g*4+1],S=m[g*4+2],y=m[g*4+3],M=(v-_)/p;for(let T=0;T<p;T++){const w=(g+T)*4;m[w]=_+M*T,m[w+1]=_+M*(T+1),m[w+2]=S,m[w+3]=y}}function f(){return(self.performance||Date).now()}function h(){this.data=[]}const d=["glyphObj","x","y","width","charIndex","fontData"];return h.prototype={width:0,lineHeight:0,baseline:0,cap:0,ex:0,isSoftWrapped:!1,get count(){return Math.ceil(this.data.length/d.length)},glyphAt(m){let g=h.flyweight;return g.data=this.data,g.index=m,g},splitAt(m){let g=new h;return g.data=this.data.splice(m*d.length),g}},h.flyweight=d.reduce((m,g,p,_)=>(Object.defineProperty(m,g,{get(){return this.data[this.index*d.length+p]},set(v){this.data[this.index*d.length+p]=v}}),m),{data:null,index:0}),{typeset:o,measure:l}}const Vr=()=>(self.performance||Date).now(),Nl=l0();let dp;function aM(n,e,t,i,r,s,a,o,l,c,u=!0){return u?lM(n,e,t,i,r,s,a,o,l,c).then(null,f=>(dp||(console.warn("WebGL SDF generation failed, falling back to JS",f),dp=!0),mp(n,e,t,i,r,s,a,o,l,c))):mp(n,e,t,i,r,s,a,o,l,c)}const tl=[],oM=5;let Sh=0;function u0(){const n=Vr();for(;tl.length&&Vr()-n<oM;)tl.shift()();Sh=tl.length?setTimeout(u0,0):0}const lM=(...n)=>new Promise((e,t)=>{tl.push(()=>{const i=Vr();try{Nl.webgl.generateIntoCanvas(...n),e({timing:Vr()-i})}catch(r){t(r)}}),Sh||(Sh=setTimeout(u0,0))}),cM=4,uM=2e3,pp={};let hM=0;function mp(n,e,t,i,r,s,a,o,l,c){const u="TroikaTextSDFGenerator_JS_"+hM++%cM;let f=pp[u];return f||(f=pp[u]={workerModule:Js({name:u,workerId:u,dependencies:[l0,Vr],init(h,d){const m=h().javascript.generate;return function(...g){const p=d();return{textureData:m(...g),timing:d()-p}}},getTransferables(h){return[h.textureData.buffer]}}),requests:0,idleTimer:null}),f.requests++,clearTimeout(f.idleTimer),f.workerModule(n,e,t,i,r,s).then(({textureData:h,timing:d})=>{const m=Vr(),g=new Uint8Array(h.length*4);for(let p=0;p<h.length;p++)g[p*4+c]=h[p];return Nl.webglUtils.renderImageData(a,g,o,l,n,e,1<<3-c),d+=Vr()-m,--f.requests===0&&(f.idleTimer=setTimeout(()=>{HS(u)},uM)),{timing:d}})}function fM(n){n._warm||(Nl.webgl.isSupported(n),n._warm=!0)}const dM=Nl.webglUtils.resizeWebGLCanvasWithoutClearing,Ca={unicodeFontsURL:null,sdfGlyphSize:64,sdfMargin:1/16,sdfExponent:9,textureWidth:2048},pM=new ut;function ws(){return(self.performance||Date).now()}const gp=Object.create(null);function mM(n,e){n=_M({},n);const t=ws(),i=[];if(n.font&&i.push({label:"user",src:vM(n.font)}),n.font=i,n.text=""+n.text,n.sdfGlyphSize=n.sdfGlyphSize||Ca.sdfGlyphSize,n.unicodeFontsURL=n.unicodeFontsURL||Ca.unicodeFontsURL,n.colorRanges!=null){let h={};for(let d in n.colorRanges)if(n.colorRanges.hasOwnProperty(d)){let m=n.colorRanges[d];typeof m!="number"&&(m=pM.set(m).getHex()),h[d]=m}n.colorRanges=h}Object.freeze(n);const{textureWidth:r,sdfExponent:s}=Ca,{sdfGlyphSize:a}=n,o=r/a*4;let l=gp[a];if(!l){const h=document.createElement("canvas");h.width=r,h.height=a*256/o,l=gp[a]={glyphCount:0,sdfGlyphSize:a,sdfCanvas:h,sdfTexture:new $t(h,void 0,void 0,void 0,Gt,Gt),contextLost:!1,glyphsByFont:new Map},l.sdfTexture.generateMipmaps=!1,gM(l)}const{sdfTexture:c,sdfCanvas:u}=l;d0(n).then(h=>{const{glyphIds:d,glyphFontIndices:m,fontData:g,glyphPositions:p,fontSize:_,timings:v}=h,S=[],y=new Float32Array(d.length*4);let M=0,T=0;const w=ws(),b=g.map(L=>{let I=l.glyphsByFont.get(L.src);return I||l.glyphsByFont.set(L.src,I=new Map),I});d.forEach((L,I)=>{const N=m[I],{src:O,unitsPerEm:B}=g[N];let q=b[N].get(L);if(!q){const{path:K,pathBounds:Z}=h.glyphData[O][L],X=Math.max(Z[2]-Z[0],Z[3]-Z[1])/a*(Ca.sdfMargin*a+.5),H=l.glyphCount++,V=[Z[0]-X,Z[1]-X,Z[2]+X,Z[3]+X];b[N].set(L,q={path:K,atlasIndex:H,sdfViewBox:V}),S.push(q)}const{sdfViewBox:F}=q,k=p[T++],U=p[T++],z=_/B;y[M++]=k+F[0]*z,y[M++]=U+F[1]*z,y[M++]=k+F[2]*z,y[M++]=U+F[3]*z,d[I]=q.atlasIndex}),v.quads=(v.quads||0)+(ws()-w);const x=ws();v.sdf={};const A=u.height,P=Math.ceil(l.glyphCount/o),R=Math.pow(2,Math.ceil(Math.log2(P*a)));R>A&&(console.info(`Increasing SDF texture size ${A}->${R}`),dM(u,r,R),c.dispose()),Promise.all(S.map(L=>h0(L,l,n.gpuAccelerateSDF).then(({timing:I})=>{v.sdf[L.atlasIndex]=I}))).then(()=>{S.length&&!l.contextLost&&(f0(l),c.needsUpdate=!0),v.sdfTotal=ws()-x,v.total=ws()-t,e(Object.freeze({parameters:n,sdfTexture:c,sdfGlyphSize:a,sdfExponent:s,glyphBounds:y,glyphAtlasIndices:d,glyphColors:h.glyphColors,caretPositions:h.caretPositions,chunkedBounds:h.chunkedBounds,ascender:h.ascender,descender:h.descender,lineHeight:h.lineHeight,capHeight:h.capHeight,xHeight:h.xHeight,topBaseline:h.topBaseline,blockBounds:h.blockBounds,visibleBounds:h.visibleBounds,timings:h.timings}))})}),Promise.resolve().then(()=>{l.contextLost||fM(u)})}function h0({path:n,atlasIndex:e,sdfViewBox:t},{sdfGlyphSize:i,sdfCanvas:r,contextLost:s},a){if(s)return Promise.resolve({timing:-1});const{textureWidth:o,sdfExponent:l}=Ca,c=Math.max(t[2]-t[0],t[3]-t[1]),u=Math.floor(e/4),f=u%(o/i)*i,h=Math.floor(u/(o/i))*i,d=e%4;return aM(i,i,n,t,c,l,r,f,h,d,a)}function gM(n){const e=n.sdfCanvas;e.addEventListener("webglcontextlost",t=>{console.log("Context Lost",t),t.preventDefault(),n.contextLost=!0}),e.addEventListener("webglcontextrestored",t=>{console.log("Context Restored",t),n.contextLost=!1;const i=[];n.glyphsByFont.forEach(r=>{r.forEach(s=>{i.push(h0(s,n,!0))})}),Promise.all(i).then(()=>{f0(n),n.sdfTexture.needsUpdate=!0})})}function _M(n,e){for(let t in e)e.hasOwnProperty(t)&&(n[t]=e[t]);return n}let Bo;function vM(n){return Bo||(Bo=typeof document>"u"?{}:document.createElement("a")),Bo.href=n,Bo.href}function f0(n){if(typeof createImageBitmap!="function"){console.info("Safari<15: applying SDF canvas workaround");const{sdfCanvas:e,sdfTexture:t}=n,{width:i,height:r}=e,s=n.sdfCanvas.getContext("webgl");let a=t.image.data;(!a||a.length!==i*r*4)&&(a=new Uint8Array(i*r*4),t.image={width:i,height:r,data:a},t.flipY=!1,t.isDataTexture=!0),s.readPixels(0,0,i,r,s.RGBA,s.UNSIGNED_BYTE,a)}}const xM=Js({name:"Typesetter",dependencies:[sM,rM,WS],init(n,e,t){return n(e,t())}}),d0=Js({name:"Typesetter",dependencies:[xM],init(n){return function(e){return new Promise(t=>{n.typeset(e,t)})}},getTransferables(n){const e=[];for(let t in n)n[t]&&n[t].buffer&&e.push(n[t].buffer);return e}});d0.onMainThread;const _p={};function yM(n){let e=_p[n];return e||(e=_p[n]=new Qr(1,1,n,n).translate(.5,.5,0)),e}const bM="aTroikaGlyphBounds",vp="aTroikaGlyphIndex",SM="aTroikaGlyphColor";class MM extends Ov{constructor(){super(),this.detail=1,this.curveRadius=0,this.groups=[{start:0,count:1/0,materialIndex:0},{start:0,count:1/0,materialIndex:1}],this.boundingSphere=new Zs,this.boundingBox=new Ks}computeBoundingSphere(){}computeBoundingBox(){}set detail(e){if(e!==this._detail){this._detail=e,(typeof e!="number"||e<1)&&(e=1);let t=yM(e);["position","normal","uv"].forEach(i=>{this.attributes[i]=t.attributes[i].clone()}),this.setIndex(t.getIndex().clone())}}get detail(){return this._detail}set curveRadius(e){e!==this._curveRadius&&(this._curveRadius=e,this._updateBounds())}get curveRadius(){return this._curveRadius}updateGlyphs(e,t,i,r,s){this.updateAttributeData(bM,e,4),this.updateAttributeData(vp,t,1),this.updateAttributeData(SM,s,3),this._blockBounds=i,this._chunkedBounds=r,this.instanceCount=t.length,this._updateBounds()}_updateBounds(){const e=this._blockBounds;if(e){const{curveRadius:t,boundingBox:i}=this;if(t){const{PI:r,floor:s,min:a,max:o,sin:l,cos:c}=Math,u=r/2,f=r*2,h=Math.abs(t),d=e[0]/h,m=e[2]/h,g=s((d+u)/f)!==s((m+u)/f)?-h:a(l(d)*h,l(m)*h),p=s((d-u)/f)!==s((m-u)/f)?h:o(l(d)*h,l(m)*h),_=s((d+r)/f)!==s((m+r)/f)?h*2:o(h-c(d)*h,h-c(m)*h);i.min.set(g,e[1],t<0?-_:0),i.max.set(p,e[3],t<0?0:_)}else i.min.set(e[0],e[1],0),i.max.set(e[2],e[3],0);i.getBoundingSphere(this.boundingSphere)}}applyClipRect(e){let t=this.getAttribute(vp).count,i=this._chunkedBounds;if(i)for(let r=i.length;r--;){t=i[r].end;let s=i[r].rect;if(s[1]<e.w&&s[3]>e.y&&s[0]<e.z&&s[2]>e.x)break}this.instanceCount=t}updateAttributeData(e,t,i){const r=this.getAttribute(e);t?r&&r.array.length===t.length?(r.array.set(t),r.needsUpdate=!0):(this.setAttribute(e,new Ev(t,i)),delete this._maxInstanceCount,this.dispose()):r&&this.deleteAttribute(e)}}const TM=`
uniform vec2 uTroikaSDFTextureSize;
uniform float uTroikaSDFGlyphSize;
uniform vec4 uTroikaTotalBounds;
uniform vec4 uTroikaClipRect;
uniform mat3 uTroikaOrient;
uniform bool uTroikaUseGlyphColors;
uniform float uTroikaEdgeOffset;
uniform float uTroikaBlurRadius;
uniform vec2 uTroikaPositionOffset;
uniform float uTroikaCurveRadius;
attribute vec4 aTroikaGlyphBounds;
attribute float aTroikaGlyphIndex;
attribute vec3 aTroikaGlyphColor;
varying vec2 vTroikaGlyphUV;
varying vec4 vTroikaTextureUVBounds;
varying float vTroikaTextureChannel;
varying vec3 vTroikaGlyphColor;
varying vec2 vTroikaGlyphDimensions;
`,EM=`
vec4 bounds = aTroikaGlyphBounds;
bounds.xz += uTroikaPositionOffset.x;
bounds.yw -= uTroikaPositionOffset.y;

vec4 outlineBounds = vec4(
  bounds.xy - uTroikaEdgeOffset - uTroikaBlurRadius,
  bounds.zw + uTroikaEdgeOffset + uTroikaBlurRadius
);
vec4 clippedBounds = vec4(
  clamp(outlineBounds.xy, uTroikaClipRect.xy, uTroikaClipRect.zw),
  clamp(outlineBounds.zw, uTroikaClipRect.xy, uTroikaClipRect.zw)
);

vec2 clippedXY = (mix(clippedBounds.xy, clippedBounds.zw, position.xy) - bounds.xy) / (bounds.zw - bounds.xy);

position.xy = mix(bounds.xy, bounds.zw, clippedXY);

uv = (position.xy - uTroikaTotalBounds.xy) / (uTroikaTotalBounds.zw - uTroikaTotalBounds.xy);

float rad = uTroikaCurveRadius;
if (rad != 0.0) {
  float angle = position.x / rad;
  position.xz = vec2(sin(angle) * rad, rad - cos(angle) * rad);
  normal.xz = vec2(sin(angle), cos(angle));
}
  
position = uTroikaOrient * position;
normal = uTroikaOrient * normal;

vTroikaGlyphUV = clippedXY.xy;
vTroikaGlyphDimensions = vec2(bounds[2] - bounds[0], bounds[3] - bounds[1]);


float txCols = uTroikaSDFTextureSize.x / uTroikaSDFGlyphSize;
vec2 txUvPerSquare = uTroikaSDFGlyphSize / uTroikaSDFTextureSize;
vec2 txStartUV = txUvPerSquare * vec2(
  mod(floor(aTroikaGlyphIndex / 4.0), txCols),
  floor(floor(aTroikaGlyphIndex / 4.0) / txCols)
);
vTroikaTextureUVBounds = vec4(txStartUV, vec2(txStartUV) + txUvPerSquare);
vTroikaTextureChannel = mod(aTroikaGlyphIndex, 4.0);
`,wM=`
uniform sampler2D uTroikaSDFTexture;
uniform vec2 uTroikaSDFTextureSize;
uniform float uTroikaSDFGlyphSize;
uniform float uTroikaSDFExponent;
uniform float uTroikaEdgeOffset;
uniform float uTroikaFillOpacity;
uniform float uTroikaBlurRadius;
uniform vec3 uTroikaStrokeColor;
uniform float uTroikaStrokeWidth;
uniform float uTroikaStrokeOpacity;
uniform bool uTroikaSDFDebug;
varying vec2 vTroikaGlyphUV;
varying vec4 vTroikaTextureUVBounds;
varying float vTroikaTextureChannel;
varying vec2 vTroikaGlyphDimensions;

float troikaSdfValueToSignedDistance(float alpha) {
  // Inverse of exponential encoding in webgl-sdf-generator
  
  float maxDimension = max(vTroikaGlyphDimensions.x, vTroikaGlyphDimensions.y);
  float absDist = (1.0 - pow(2.0 * (alpha > 0.5 ? 1.0 - alpha : alpha), 1.0 / uTroikaSDFExponent)) * maxDimension;
  float signedDist = absDist * (alpha > 0.5 ? -1.0 : 1.0);
  return signedDist;
}

float troikaGlyphUvToSdfValue(vec2 glyphUV) {
  vec2 textureUV = mix(vTroikaTextureUVBounds.xy, vTroikaTextureUVBounds.zw, glyphUV);
  vec4 rgba = texture2D(uTroikaSDFTexture, textureUV);
  float ch = floor(vTroikaTextureChannel + 0.5); //NOTE: can't use round() in WebGL1
  return ch == 0.0 ? rgba.r : ch == 1.0 ? rgba.g : ch == 2.0 ? rgba.b : rgba.a;
}

float troikaGlyphUvToDistance(vec2 uv) {
  return troikaSdfValueToSignedDistance(troikaGlyphUvToSdfValue(uv));
}

float troikaGetAADist() {
  
  #if defined(GL_OES_standard_derivatives) || __VERSION__ >= 300
  return length(fwidth(vTroikaGlyphUV * vTroikaGlyphDimensions)) * 0.5;
  #else
  return vTroikaGlyphDimensions.x / 64.0;
  #endif
}

float troikaGetFragDistValue() {
  vec2 clampedGlyphUV = clamp(vTroikaGlyphUV, 0.5 / uTroikaSDFGlyphSize, 1.0 - 0.5 / uTroikaSDFGlyphSize);
  float distance = troikaGlyphUvToDistance(clampedGlyphUV);
 
  // Extrapolate distance when outside bounds:
  distance += clampedGlyphUV == vTroikaGlyphUV ? 0.0 : 
    length((vTroikaGlyphUV - clampedGlyphUV) * vTroikaGlyphDimensions);

  

  return distance;
}

float troikaGetEdgeAlpha(float distance, float distanceOffset, float aaDist) {
  #if defined(IS_DEPTH_MATERIAL) || defined(IS_DISTANCE_MATERIAL)
  float alpha = step(-distanceOffset, -distance);
  #else

  float alpha = smoothstep(
    distanceOffset + aaDist,
    distanceOffset - aaDist,
    distance
  );
  #endif

  return alpha;
}
`,AM=`
float aaDist = troikaGetAADist();
float fragDistance = troikaGetFragDistValue();
float edgeAlpha = uTroikaSDFDebug ?
  troikaGlyphUvToSdfValue(vTroikaGlyphUV) :
  troikaGetEdgeAlpha(fragDistance, uTroikaEdgeOffset, max(aaDist, uTroikaBlurRadius));

#if !defined(IS_DEPTH_MATERIAL) && !defined(IS_DISTANCE_MATERIAL)
vec4 fillRGBA = gl_FragColor;
fillRGBA.a *= uTroikaFillOpacity;
vec4 strokeRGBA = uTroikaStrokeWidth == 0.0 ? fillRGBA : vec4(uTroikaStrokeColor, uTroikaStrokeOpacity);
if (fillRGBA.a == 0.0) fillRGBA.rgb = strokeRGBA.rgb;
gl_FragColor = mix(fillRGBA, strokeRGBA, smoothstep(
  -uTroikaStrokeWidth - aaDist,
  -uTroikaStrokeWidth + aaDist,
  fragDistance
));
gl_FragColor.a *= edgeAlpha;
#endif

if (edgeAlpha == 0.0) {
  discard;
}
`;function RM(n){const e=bh(n,{chained:!0,extensions:{derivatives:!0},uniforms:{uTroikaSDFTexture:{value:null},uTroikaSDFTextureSize:{value:new Xe},uTroikaSDFGlyphSize:{value:0},uTroikaSDFExponent:{value:0},uTroikaTotalBounds:{value:new Ut(0,0,0,0)},uTroikaClipRect:{value:new Ut(0,0,0,0)},uTroikaEdgeOffset:{value:0},uTroikaFillOpacity:{value:1},uTroikaPositionOffset:{value:new Xe},uTroikaCurveRadius:{value:0},uTroikaBlurRadius:{value:0},uTroikaStrokeWidth:{value:0},uTroikaStrokeColor:{value:new ut},uTroikaStrokeOpacity:{value:1},uTroikaOrient:{value:new it},uTroikaUseGlyphColors:{value:!0},uTroikaSDFDebug:{value:!1}},vertexDefs:TM,vertexTransform:EM,fragmentDefs:wM,fragmentColorTransform:AM,customRewriter({vertexShader:t,fragmentShader:i}){let r=/\buniform\s+vec3\s+diffuse\b/;return r.test(i)&&(i=i.replace(r,"varying vec3 vTroikaGlyphColor").replace(/\bdiffuse\b/g,"vTroikaGlyphColor"),r.test(t)||(t=t.replace(c0,`uniform vec3 diffuse;
$&
vTroikaGlyphColor = uTroikaUseGlyphColors ? aTroikaGlyphColor / 255.0 : diffuse;
`))),{vertexShader:t,fragmentShader:i}}});return e.transparent=!0,e.forceSinglePass=!0,Object.defineProperties(e,{isTroikaTextMaterial:{value:!0},shadowSide:{get(){return this.side},set(){}}}),e}const sf=new tf({color:16777215,side:Rn,transparent:!0}),xp=8421504,yp=new zt,ko=new $,Gc=new $,Sa=[],CM=new $,Hc="+x+y";function bp(n){return Array.isArray(n)?n[0]:n}let p0=()=>{const n=new jn(new Qr(1,1),sf);return p0=()=>n,n},m0=()=>{const n=new jn(new Qr(1,1,32,1),sf);return m0=()=>n,n};const PM={type:"syncstart"},DM={type:"synccomplete"},g0=["font","fontSize","fontStyle","fontWeight","lang","letterSpacing","lineHeight","maxWidth","overflowWrap","text","direction","textAlign","textIndent","whiteSpace","anchorX","anchorY","colorRanges","sdfGlyphSize"],UM=g0.concat("material","color","depthOffset","clipRect","curveRadius","orientation","glyphGeometryDetail");class Mh extends jn{constructor(){const e=new MM;super(e,null),this.text="",this.anchorX=0,this.anchorY=0,this.curveRadius=0,this.direction="auto",this.font=null,this.unicodeFontsURL=null,this.fontSize=.1,this.fontWeight="normal",this.fontStyle="normal",this.lang=null,this.letterSpacing=0,this.lineHeight="normal",this.maxWidth=1/0,this.overflowWrap="normal",this.textAlign="left",this.textIndent=0,this.whiteSpace="normal",this.material=null,this.color=null,this.colorRanges=null,this.outlineWidth=0,this.outlineColor=0,this.outlineOpacity=1,this.outlineBlur=0,this.outlineOffsetX=0,this.outlineOffsetY=0,this.strokeWidth=0,this.strokeColor=xp,this.strokeOpacity=1,this.fillOpacity=1,this.depthOffset=0,this.clipRect=null,this.orientation=Hc,this.glyphGeometryDetail=1,this.sdfGlyphSize=null,this.gpuAccelerateSDF=!0,this.debugSDF=!1}sync(e){this._needsSync&&(this._needsSync=!1,this._isSyncing?(this._queuedSyncs||(this._queuedSyncs=[])).push(e):(this._isSyncing=!0,this.dispatchEvent(PM),mM({text:this.text,font:this.font,lang:this.lang,fontSize:this.fontSize||.1,fontWeight:this.fontWeight||"normal",fontStyle:this.fontStyle||"normal",letterSpacing:this.letterSpacing||0,lineHeight:this.lineHeight||"normal",maxWidth:this.maxWidth,direction:this.direction||"auto",textAlign:this.textAlign,textIndent:this.textIndent,whiteSpace:this.whiteSpace,overflowWrap:this.overflowWrap,anchorX:this.anchorX,anchorY:this.anchorY,colorRanges:this.colorRanges,includeCaretPositions:!0,sdfGlyphSize:this.sdfGlyphSize,gpuAccelerateSDF:this.gpuAccelerateSDF,unicodeFontsURL:this.unicodeFontsURL},t=>{this._isSyncing=!1,this._textRenderInfo=t,this.geometry.updateGlyphs(t.glyphBounds,t.glyphAtlasIndices,t.blockBounds,t.chunkedBounds,t.glyphColors);const i=this._queuedSyncs;i&&(this._queuedSyncs=null,this._needsSync=!0,this.sync(()=>{i.forEach(r=>r&&r())})),this.dispatchEvent(DM),e&&e()})))}onBeforeRender(e,t,i,r,s,a){this.sync(),s.isTroikaTextMaterial&&this._prepareForRender(s)}dispose(){this.geometry.dispose()}get textRenderInfo(){return this._textRenderInfo||null}createDerivedMaterial(e){return RM(e)}get material(){let e=this._derivedMaterial;const t=this._baseMaterial||this._defaultMaterial||(this._defaultMaterial=sf.clone());if((!e||!e.isDerivedFrom(t))&&(e=this._derivedMaterial=this.createDerivedMaterial(t),t.addEventListener("dispose",function i(){t.removeEventListener("dispose",i),e.dispose()})),this.hasOutline()){let i=e._outlineMtl;return i||(i=e._outlineMtl=Object.create(e,{id:{value:e.id+.1}}),i.isTextOutlineMaterial=!0,i.depthWrite=!1,i.map=null,e.addEventListener("dispose",function r(){e.removeEventListener("dispose",r),i.dispose()})),[i,e]}else return e}set material(e){e&&e.isTroikaTextMaterial?(this._derivedMaterial=e,this._baseMaterial=e.baseMaterial):this._baseMaterial=e}hasOutline(){return!!(this.outlineWidth||this.outlineBlur||this.outlineOffsetX||this.outlineOffsetY)}get glyphGeometryDetail(){return this.geometry.detail}set glyphGeometryDetail(e){this.geometry.detail=e}get curveRadius(){return this.geometry.curveRadius}set curveRadius(e){this.geometry.curveRadius=e}get customDepthMaterial(){return bp(this.material).getDepthMaterial()}set customDepthMaterial(e){}get customDistanceMaterial(){return bp(this.material).getDistanceMaterial()}set customDistanceMaterial(e){}_prepareForRender(e){const t=e.isTextOutlineMaterial,i=e.uniforms,r=this.textRenderInfo;if(r){const{sdfTexture:o,blockBounds:l}=r;i.uTroikaSDFTexture.value=o,i.uTroikaSDFTextureSize.value.set(o.image.width,o.image.height),i.uTroikaSDFGlyphSize.value=r.sdfGlyphSize,i.uTroikaSDFExponent.value=r.sdfExponent,i.uTroikaTotalBounds.value.fromArray(l),i.uTroikaUseGlyphColors.value=!t&&!!r.glyphColors;let c=0,u=0,f=0,h,d,m,g=0,p=0;if(t){let{outlineWidth:v,outlineOffsetX:S,outlineOffsetY:y,outlineBlur:M,outlineOpacity:T}=this;c=this._parsePercent(v)||0,u=Math.max(0,this._parsePercent(M)||0),h=T,g=this._parsePercent(S)||0,p=this._parsePercent(y)||0}else f=Math.max(0,this._parsePercent(this.strokeWidth)||0),f&&(m=this.strokeColor,i.uTroikaStrokeColor.value.set(m??xp),d=this.strokeOpacity,d==null&&(d=1)),h=this.fillOpacity;i.uTroikaEdgeOffset.value=c,i.uTroikaPositionOffset.value.set(g,p),i.uTroikaBlurRadius.value=u,i.uTroikaStrokeWidth.value=f,i.uTroikaStrokeOpacity.value=d,i.uTroikaFillOpacity.value=h??1,i.uTroikaCurveRadius.value=this.curveRadius||0;let _=this.clipRect;if(_&&Array.isArray(_)&&_.length===4)i.uTroikaClipRect.value.fromArray(_);else{const v=(this.fontSize||.1)*100;i.uTroikaClipRect.value.set(l[0]-v,l[1]-v,l[2]+v,l[3]+v)}this.geometry.applyClipRect(i.uTroikaClipRect.value)}i.uTroikaSDFDebug.value=!!this.debugSDF,e.polygonOffset=!!this.depthOffset,e.polygonOffsetFactor=e.polygonOffsetUnits=this.depthOffset||0;const s=t?this.outlineColor||0:this.color;if(s==null)delete e.color;else{const o=e.hasOwnProperty("color")?e.color:e.color=new ut;(s!==o._input||typeof s=="object")&&o.set(o._input=s)}let a=this.orientation||Hc;if(a!==e._orientation){let o=i.uTroikaOrient.value;a=a.replace(/[^-+xyz]/g,"");let l=a!==Hc&&a.match(/^([-+])([xyz])([-+])([xyz])$/);if(l){let[,c,u,f,h]=l;ko.set(0,0,0)[u]=c==="-"?1:-1,Gc.set(0,0,0)[h]=f==="-"?-1:1,yp.lookAt(CM,ko.cross(Gc),Gc),o.setFromMatrix4(yp)}else o.identity();e._orientation=a}}_parsePercent(e){if(typeof e=="string"){let t=e.match(/^(-?[\d.]+)%$/),i=t?parseFloat(t[1]):NaN;e=(isNaN(i)?0:i/100)*this.fontSize}return e}localPositionToTextCoords(e,t=new Xe){t.copy(e);const i=this.curveRadius;return i&&(t.x=Math.atan2(e.x,Math.abs(i)-Math.abs(e.z))*Math.abs(i)),t}worldPositionToTextCoords(e,t=new Xe){return ko.copy(e),this.localPositionToTextCoords(this.worldToLocal(ko),t)}raycast(e,t){const{textRenderInfo:i,curveRadius:r}=this;if(i){const s=i.blockBounds,a=r?m0():p0(),o=a.geometry,{position:l,uv:c}=o.attributes;for(let u=0;u<c.count;u++){let f=s[0]+c.getX(u)*(s[2]-s[0]);const h=s[1]+c.getY(u)*(s[3]-s[1]);let d=0;r&&(d=r-Math.cos(f/r)*r,f=Math.sin(f/r)*r),l.setXYZ(u,f,h,d)}o.boundingSphere=this.geometry.boundingSphere,o.boundingBox=this.geometry.boundingBox,a.matrixWorld=this.matrixWorld,a.material.side=this.material.side,Sa.length=0,a.raycast(e,Sa);for(let u=0;u<Sa.length;u++)Sa[u].object=this,t.push(Sa[u])}}copy(e){const t=this.geometry;return super.copy(e),this.geometry=t,UM.forEach(i=>{this[i]=e[i]}),this}clone(){return new this.constructor().copy(this)}}g0.forEach(n=>{const e="_private_"+n;Object.defineProperty(Mh.prototype,n,{get(){return this[e]},set(t){t!==this[e]&&(this[e]=t,this._needsSync=!0)}})});new ut;const Sp={type:"change"},af={type:"start"},_0={type:"end"},zo=new Ll,Mp=new ur,LM=Math.cos(70*rv.DEG2RAD),Zt=new $,An=2*Math.PI,Tt={NONE:-1,ROTATE:0,DOLLY:1,PAN:2,TOUCH_ROTATE:3,TOUCH_PAN:4,TOUCH_DOLLY_PAN:5,TOUCH_DOLLY_ROTATE:6},Vc=1e-6;class IM extends Gv{constructor(e,t=null){super(e,t),this.state=Tt.NONE,this.target=new $,this.cursor=new $,this.minDistance=0,this.maxDistance=1/0,this.minZoom=0,this.maxZoom=1/0,this.minTargetRadius=0,this.maxTargetRadius=1/0,this.minPolarAngle=0,this.maxPolarAngle=Math.PI,this.minAzimuthAngle=-1/0,this.maxAzimuthAngle=1/0,this.enableDamping=!1,this.dampingFactor=.05,this.enableZoom=!0,this.zoomSpeed=1,this.enableRotate=!0,this.rotateSpeed=1,this.keyRotateSpeed=1,this.enablePan=!0,this.panSpeed=1,this.screenSpacePanning=!0,this.keyPanSpeed=7,this.zoomToCursor=!1,this.autoRotate=!1,this.autoRotateSpeed=2,this.keys={LEFT:"ArrowLeft",UP:"ArrowUp",RIGHT:"ArrowRight",BOTTOM:"ArrowDown"},this.mouseButtons={LEFT:Us.ROTATE,MIDDLE:Us.DOLLY,RIGHT:Us.PAN},this.touches={ONE:Rs.ROTATE,TWO:Rs.DOLLY_PAN},this.target0=this.target.clone(),this.position0=this.object.position.clone(),this.zoom0=this.object.zoom,this._cursorStyle="auto",this._domElementKeyEvents=null,this._lastPosition=new $,this._lastQuaternion=new br,this._lastTargetPosition=new $,this._quat=new br().setFromUnitVectors(e.up,new $(0,1,0)),this._quatInverse=this._quat.clone().invert(),this._spherical=new Nd,this._sphericalDelta=new Nd,this._scale=1,this._panOffset=new $,this._rotateStart=new Xe,this._rotateEnd=new Xe,this._rotateDelta=new Xe,this._panStart=new Xe,this._panEnd=new Xe,this._panDelta=new Xe,this._dollyStart=new Xe,this._dollyEnd=new Xe,this._dollyDelta=new Xe,this._dollyDirection=new $,this._mouse=new Xe,this._performCursorZoom=!1,this._pointers=[],this._pointerPositions={},this._controlActive=!1,this._onPointerMove=NM.bind(this),this._onPointerDown=FM.bind(this),this._onPointerUp=OM.bind(this),this._onContextMenu=WM.bind(this),this._onMouseWheel=zM.bind(this),this._onKeyDown=GM.bind(this),this._onTouchStart=HM.bind(this),this._onTouchMove=VM.bind(this),this._onMouseDown=BM.bind(this),this._onMouseMove=kM.bind(this),this._interceptControlDown=XM.bind(this),this._interceptControlUp=jM.bind(this),this.domElement!==null&&this.connect(this.domElement),this.update()}set cursorStyle(e){this._cursorStyle=e,e==="grab"?this.domElement.style.cursor="grab":this.domElement.style.cursor="auto"}get cursorStyle(){return this._cursorStyle}connect(e){super.connect(e),this.domElement.addEventListener("pointerdown",this._onPointerDown),this.domElement.addEventListener("pointercancel",this._onPointerUp),this.domElement.addEventListener("contextmenu",this._onContextMenu),this.domElement.addEventListener("wheel",this._onMouseWheel,{passive:!1}),this.domElement.getRootNode().addEventListener("keydown",this._interceptControlDown,{passive:!0,capture:!0}),this.domElement.style.touchAction="none"}disconnect(){this.domElement.removeEventListener("pointerdown",this._onPointerDown),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.domElement.removeEventListener("pointercancel",this._onPointerUp),this.domElement.removeEventListener("wheel",this._onMouseWheel),this.domElement.removeEventListener("contextmenu",this._onContextMenu),this.stopListenToKeyEvents(),this.domElement.getRootNode().removeEventListener("keydown",this._interceptControlDown,{capture:!0}),this.domElement.style.touchAction=""}dispose(){this.disconnect()}getPolarAngle(){return this._spherical.phi}getAzimuthalAngle(){return this._spherical.theta}getDistance(){return this.object.position.distanceTo(this.target)}listenToKeyEvents(e){e.addEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=e}stopListenToKeyEvents(){this._domElementKeyEvents!==null&&(this._domElementKeyEvents.removeEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=null)}saveState(){this.target0.copy(this.target),this.position0.copy(this.object.position),this.zoom0=this.object.zoom}reset(){this.target.copy(this.target0),this.object.position.copy(this.position0),this.object.zoom=this.zoom0,this.object.updateProjectionMatrix(),this.dispatchEvent(Sp),this.update(),this.state=Tt.NONE}pan(e,t){this._pan(e,t),this.update()}dollyIn(e){this._dollyIn(e),this.update()}dollyOut(e){this._dollyOut(e),this.update()}rotateLeft(e){this._rotateLeft(e),this.update()}rotateUp(e){this._rotateUp(e),this.update()}update(e=null){const t=this.object.position;Zt.copy(t).sub(this.target),Zt.applyQuaternion(this._quat),this._spherical.setFromVector3(Zt),this.autoRotate&&this.state===Tt.NONE&&this._rotateLeft(this._getAutoRotationAngle(e)),this.enableDamping?(this._spherical.theta+=this._sphericalDelta.theta*this.dampingFactor,this._spherical.phi+=this._sphericalDelta.phi*this.dampingFactor):(this._spherical.theta+=this._sphericalDelta.theta,this._spherical.phi+=this._sphericalDelta.phi);let i=this.minAzimuthAngle,r=this.maxAzimuthAngle;isFinite(i)&&isFinite(r)&&(i<-Math.PI?i+=An:i>Math.PI&&(i-=An),r<-Math.PI?r+=An:r>Math.PI&&(r-=An),i<=r?this._spherical.theta=Math.max(i,Math.min(r,this._spherical.theta)):this._spherical.theta=this._spherical.theta>(i+r)/2?Math.max(i,this._spherical.theta):Math.min(r,this._spherical.theta)),this._spherical.phi=Math.max(this.minPolarAngle,Math.min(this.maxPolarAngle,this._spherical.phi)),this._spherical.makeSafe(),this.enableDamping===!0?this.target.addScaledVector(this._panOffset,this.dampingFactor):this.target.add(this._panOffset),this.target.sub(this.cursor),this.target.clampLength(this.minTargetRadius,this.maxTargetRadius),this.target.add(this.cursor);let s=!1;if(this.zoomToCursor&&this._performCursorZoom||this.object.isOrthographicCamera)this._spherical.radius=this._clampDistance(this._spherical.radius);else{const a=this._spherical.radius;this._spherical.radius=this._clampDistance(this._spherical.radius*this._scale),s=a!=this._spherical.radius}if(Zt.setFromSpherical(this._spherical),Zt.applyQuaternion(this._quatInverse),t.copy(this.target).add(Zt),this.object.lookAt(this.target),this.enableDamping===!0?(this._sphericalDelta.theta*=1-this.dampingFactor,this._sphericalDelta.phi*=1-this.dampingFactor,this._panOffset.multiplyScalar(1-this.dampingFactor)):(this._sphericalDelta.set(0,0,0),this._panOffset.set(0,0,0)),this.zoomToCursor&&this._performCursorZoom){let a=null;if(this.object.isPerspectiveCamera){const o=Zt.length();a=this._clampDistance(o*this._scale);const l=o-a;this.object.position.addScaledVector(this._dollyDirection,l),this.object.updateMatrixWorld(),s=!!l}else if(this.object.isOrthographicCamera){const o=new $(this._mouse.x,this._mouse.y,0);o.unproject(this.object);const l=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),this.object.updateProjectionMatrix(),s=l!==this.object.zoom;const c=new $(this._mouse.x,this._mouse.y,0);c.unproject(this.object),this.object.position.sub(c).add(o),this.object.updateMatrixWorld(),a=Zt.length()}else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - zoom to cursor disabled."),this.zoomToCursor=!1;a!==null&&(this.screenSpacePanning?this.target.set(0,0,-1).transformDirection(this.object.matrix).multiplyScalar(a).add(this.object.position):(zo.origin.copy(this.object.position),zo.direction.set(0,0,-1).transformDirection(this.object.matrix),Math.abs(this.object.up.dot(zo.direction))<LM?this.object.lookAt(this.target):(Mp.setFromNormalAndCoplanarPoint(this.object.up,this.target),zo.intersectPlane(Mp,this.target))))}else if(this.object.isOrthographicCamera){const a=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),a!==this.object.zoom&&(this.object.updateProjectionMatrix(),s=!0)}return this._scale=1,this._performCursorZoom=!1,s||this._lastPosition.distanceToSquared(this.object.position)>Vc||8*(1-this._lastQuaternion.dot(this.object.quaternion))>Vc||this._lastTargetPosition.distanceToSquared(this.target)>Vc?(this.dispatchEvent(Sp),this._lastPosition.copy(this.object.position),this._lastQuaternion.copy(this.object.quaternion),this._lastTargetPosition.copy(this.target),!0):!1}_getAutoRotationAngle(e){return e!==null?An/60*this.autoRotateSpeed*e:An/60/60*this.autoRotateSpeed}_getZoomScale(e){const t=Math.abs(e*.01);return Math.pow(.95,this.zoomSpeed*t)}_rotateLeft(e){this._sphericalDelta.theta-=e}_rotateUp(e){this._sphericalDelta.phi-=e}_panLeft(e,t){Zt.setFromMatrixColumn(t,0),Zt.multiplyScalar(-e),this._panOffset.add(Zt)}_panUp(e,t){this.screenSpacePanning===!0?Zt.setFromMatrixColumn(t,1):(Zt.setFromMatrixColumn(t,0),Zt.crossVectors(this.object.up,Zt)),Zt.multiplyScalar(e),this._panOffset.add(Zt)}_pan(e,t){const i=this.domElement;if(this.object.isPerspectiveCamera){const r=this.object.position;Zt.copy(r).sub(this.target);let s=Zt.length();s*=Math.tan(this.object.fov/2*Math.PI/180),this._panLeft(2*e*s/i.clientHeight,this.object.matrix),this._panUp(2*t*s/i.clientHeight,this.object.matrix)}else this.object.isOrthographicCamera?(this._panLeft(e*(this.object.right-this.object.left)/this.object.zoom/i.clientWidth,this.object.matrix),this._panUp(t*(this.object.top-this.object.bottom)/this.object.zoom/i.clientHeight,this.object.matrix)):(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled."),this.enablePan=!1)}_dollyOut(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale/=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_dollyIn(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale*=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_updateZoomParameters(e,t){if(!this.zoomToCursor)return;this._performCursorZoom=!0;const i=this.domElement.getBoundingClientRect(),r=e-i.left,s=t-i.top,a=i.width,o=i.height;this._mouse.x=r/a*2-1,this._mouse.y=-(s/o)*2+1,this._dollyDirection.set(this._mouse.x,this._mouse.y,1).unproject(this.object).sub(this.object.position).normalize()}_clampDistance(e){return Math.max(this.minDistance,Math.min(this.maxDistance,e))}_handleMouseDownRotate(e){this._rotateStart.set(e.clientX,e.clientY)}_handleMouseDownDolly(e){this._updateZoomParameters(e.clientX,e.clientX),this._dollyStart.set(e.clientX,e.clientY)}_handleMouseDownPan(e){this._panStart.set(e.clientX,e.clientY)}_handleMouseMoveRotate(e){this._rotateEnd.set(e.clientX,e.clientY),this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(An*this._rotateDelta.x/t.clientHeight),this._rotateUp(An*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd),this.update()}_handleMouseMoveDolly(e){this._dollyEnd.set(e.clientX,e.clientY),this._dollyDelta.subVectors(this._dollyEnd,this._dollyStart),this._dollyDelta.y>0?this._dollyOut(this._getZoomScale(this._dollyDelta.y)):this._dollyDelta.y<0&&this._dollyIn(this._getZoomScale(this._dollyDelta.y)),this._dollyStart.copy(this._dollyEnd),this.update()}_handleMouseMovePan(e){this._panEnd.set(e.clientX,e.clientY),this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd),this.update()}_handleMouseWheel(e){this._updateZoomParameters(e.clientX,e.clientY),e.deltaY<0?this._dollyIn(this._getZoomScale(e.deltaY)):e.deltaY>0&&this._dollyOut(this._getZoomScale(e.deltaY)),this.update()}_handleKeyDown(e){let t=!1;switch(e.code){case this.keys.UP:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(An*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,this.keyPanSpeed),t=!0;break;case this.keys.BOTTOM:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(-An*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,-this.keyPanSpeed),t=!0;break;case this.keys.LEFT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(An*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(this.keyPanSpeed,0),t=!0;break;case this.keys.RIGHT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(-An*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(-this.keyPanSpeed,0),t=!0;break}t&&(e.preventDefault(),this.update())}_handleTouchStartRotate(e){if(this._pointers.length===1)this._rotateStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),i=.5*(e.pageX+t.x),r=.5*(e.pageY+t.y);this._rotateStart.set(i,r)}}_handleTouchStartPan(e){if(this._pointers.length===1)this._panStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),i=.5*(e.pageX+t.x),r=.5*(e.pageY+t.y);this._panStart.set(i,r)}}_handleTouchStartDolly(e){const t=this._getSecondPointerPosition(e),i=e.pageX-t.x,r=e.pageY-t.y,s=Math.sqrt(i*i+r*r);this._dollyStart.set(0,s)}_handleTouchStartDollyPan(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enablePan&&this._handleTouchStartPan(e)}_handleTouchStartDollyRotate(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enableRotate&&this._handleTouchStartRotate(e)}_handleTouchMoveRotate(e){if(this._pointers.length==1)this._rotateEnd.set(e.pageX,e.pageY);else{const i=this._getSecondPointerPosition(e),r=.5*(e.pageX+i.x),s=.5*(e.pageY+i.y);this._rotateEnd.set(r,s)}this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(An*this._rotateDelta.x/t.clientHeight),this._rotateUp(An*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd)}_handleTouchMovePan(e){if(this._pointers.length===1)this._panEnd.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),i=.5*(e.pageX+t.x),r=.5*(e.pageY+t.y);this._panEnd.set(i,r)}this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd)}_handleTouchMoveDolly(e){const t=this._getSecondPointerPosition(e),i=e.pageX-t.x,r=e.pageY-t.y,s=Math.sqrt(i*i+r*r);this._dollyEnd.set(0,s),this._dollyDelta.set(0,Math.pow(this._dollyEnd.y/this._dollyStart.y,this.zoomSpeed)),this._dollyOut(this._dollyDelta.y),this._dollyStart.copy(this._dollyEnd);const a=(e.pageX+t.x)*.5,o=(e.pageY+t.y)*.5;this._updateZoomParameters(a,o)}_handleTouchMoveDollyPan(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enablePan&&this._handleTouchMovePan(e)}_handleTouchMoveDollyRotate(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enableRotate&&this._handleTouchMoveRotate(e)}_addPointer(e){this._pointers.push(e.pointerId)}_removePointer(e){delete this._pointerPositions[e.pointerId];for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId){this._pointers.splice(t,1);return}}_isTrackingPointer(e){for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId)return!0;return!1}_trackPointer(e){let t=this._pointerPositions[e.pointerId];t===void 0&&(t=new Xe,this._pointerPositions[e.pointerId]=t),t.set(e.pageX,e.pageY)}_getSecondPointerPosition(e){const t=e.pointerId===this._pointers[0]?this._pointers[1]:this._pointers[0];return this._pointerPositions[t]}_customWheelEvent(e){const t=e.deltaMode,i={clientX:e.clientX,clientY:e.clientY,deltaY:e.deltaY};switch(t){case 1:i.deltaY*=16;break;case 2:i.deltaY*=100;break}return e.ctrlKey&&!this._controlActive&&(i.deltaY*=10),i}}function FM(n){this.enabled!==!1&&(this._pointers.length===0&&(this.domElement.setPointerCapture(n.pointerId),this.domElement.ownerDocument.addEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.addEventListener("pointerup",this._onPointerUp)),!this._isTrackingPointer(n)&&(this._addPointer(n),n.pointerType==="touch"?this._onTouchStart(n):this._onMouseDown(n),this._cursorStyle==="grab"&&(this.domElement.style.cursor="grabbing")))}function NM(n){this.enabled!==!1&&(n.pointerType==="touch"?this._onTouchMove(n):this._onMouseMove(n))}function OM(n){switch(this._removePointer(n),this._pointers.length){case 0:this.domElement.releasePointerCapture(n.pointerId),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.dispatchEvent(_0),this.state=Tt.NONE,this._cursorStyle==="grab"&&(this.domElement.style.cursor="grab");break;case 1:const e=this._pointers[0],t=this._pointerPositions[e];this._onTouchStart({pointerId:e,pageX:t.x,pageY:t.y});break}}function BM(n){let e;switch(n.button){case 0:e=this.mouseButtons.LEFT;break;case 1:e=this.mouseButtons.MIDDLE;break;case 2:e=this.mouseButtons.RIGHT;break;default:e=-1}switch(e){case Us.DOLLY:if(this.enableZoom===!1)return;this._handleMouseDownDolly(n),this.state=Tt.DOLLY;break;case Us.ROTATE:if(n.ctrlKey||n.metaKey||n.shiftKey){if(this.enablePan===!1)return;this._handleMouseDownPan(n),this.state=Tt.PAN}else{if(this.enableRotate===!1)return;this._handleMouseDownRotate(n),this.state=Tt.ROTATE}break;case Us.PAN:if(n.ctrlKey||n.metaKey||n.shiftKey){if(this.enableRotate===!1)return;this._handleMouseDownRotate(n),this.state=Tt.ROTATE}else{if(this.enablePan===!1)return;this._handleMouseDownPan(n),this.state=Tt.PAN}break;default:this.state=Tt.NONE}this.state!==Tt.NONE&&this.dispatchEvent(af)}function kM(n){switch(this.state){case Tt.ROTATE:if(this.enableRotate===!1)return;this._handleMouseMoveRotate(n);break;case Tt.DOLLY:if(this.enableZoom===!1)return;this._handleMouseMoveDolly(n);break;case Tt.PAN:if(this.enablePan===!1)return;this._handleMouseMovePan(n);break}}function zM(n){this.enabled===!1||this.enableZoom===!1||this.state!==Tt.NONE||(n.preventDefault(),this.dispatchEvent(af),this._handleMouseWheel(this._customWheelEvent(n)),this.dispatchEvent(_0))}function GM(n){this.enabled!==!1&&this._handleKeyDown(n)}function HM(n){switch(this._trackPointer(n),this._pointers.length){case 1:switch(this.touches.ONE){case Rs.ROTATE:if(this.enableRotate===!1)return;this._handleTouchStartRotate(n),this.state=Tt.TOUCH_ROTATE;break;case Rs.PAN:if(this.enablePan===!1)return;this._handleTouchStartPan(n),this.state=Tt.TOUCH_PAN;break;default:this.state=Tt.NONE}break;case 2:switch(this.touches.TWO){case Rs.DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchStartDollyPan(n),this.state=Tt.TOUCH_DOLLY_PAN;break;case Rs.DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchStartDollyRotate(n),this.state=Tt.TOUCH_DOLLY_ROTATE;break;default:this.state=Tt.NONE}break;default:this.state=Tt.NONE}this.state!==Tt.NONE&&this.dispatchEvent(af)}function VM(n){switch(this._trackPointer(n),this.state){case Tt.TOUCH_ROTATE:if(this.enableRotate===!1)return;this._handleTouchMoveRotate(n),this.update();break;case Tt.TOUCH_PAN:if(this.enablePan===!1)return;this._handleTouchMovePan(n),this.update();break;case Tt.TOUCH_DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchMoveDollyPan(n),this.update();break;case Tt.TOUCH_DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchMoveDollyRotate(n),this.update();break;default:this.state=Tt.NONE}}function WM(n){this.enabled!==!1&&n.preventDefault()}function XM(n){n.key==="Control"&&(this._controlActive=!0,this.domElement.getRootNode().addEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function jM(n){n.key==="Control"&&(this._controlActive=!1,this.domElement.getRootNode().removeEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function Gi(n){if(n===void 0)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return n}function v0(n,e){n.prototype=Object.create(e.prototype),n.prototype.constructor=n,n.__proto__=e}/*!
 * GSAP 3.15.0
 * https://gsap.com
 *
 * @license Copyright 2008-2026, GreenSock. All rights reserved.
 * Subject to the terms at https://gsap.com/standard-license
 * @author: Jack Doyle, jack@greensock.com
*/var Xn={autoSleep:120,force3D:"auto",nullTargetWarn:1,units:{lineHeight:""}},za={duration:.5,overwrite:!1,delay:0},of,hn,It,ei=1e8,Rt=1/ei,Th=Math.PI*2,YM=Th/4,qM=0,x0=Math.sqrt,KM=Math.cos,ZM=Math.sin,ln=function(e){return typeof e=="string"},Ht=function(e){return typeof e=="function"},Ki=function(e){return typeof e=="number"},lf=function(e){return typeof e>"u"},Li=function(e){return typeof e=="object"},Pn=function(e){return e!==!1},cf=function(){return typeof window<"u"},Go=function(e){return Ht(e)||ln(e)},y0=typeof ArrayBuffer=="function"&&ArrayBuffer.isView||function(){},vn=Array.isArray,$M=/random\([^)]+\)/g,JM=/,\s*/g,Tp=/(?:-?\.?\d|\.)+/gi,b0=/[-+=.]*\d+[.e\-+]*\d*[e\-+]*\d*/g,Ps=/[-+=.]*\d+[.e-]*\d*[a-z%]*/g,Wc=/[-+=.]*\d+\.?\d*(?:e-|e\+)?\d*/gi,S0=/[+-]=-?[.\d]+/,QM=/[^,'"\[\]\s]+/gi,e2=/^[+\-=e\s\d]*\d+[.\d]*([a-z]*|%)\s*$/i,Bt,Si,Eh,uf,Yn={},vl={},M0,T0=function(e){return(vl=Vs(e,Yn))&&In},hf=function(e,t){return console.warn("Invalid property",e,"set to",t,"Missing plugin? gsap.registerPlugin()")},Ga=function(e,t){return!t&&console.warn(e)},E0=function(e,t){return e&&(Yn[e]=t)&&vl&&(vl[e]=t)||Yn},Ha=function(){return 0},t2={suppressEvents:!0,isStart:!0,kill:!1},nl={suppressEvents:!0,kill:!1},n2={suppressEvents:!0},ff={},vr=[],wh={},w0,zn={},Xc={},Ep=30,il=[],df="",pf=function(e){var t=e[0],i,r;if(Li(t)||Ht(t)||(e=[e]),!(i=(t._gsap||{}).harness)){for(r=il.length;r--&&!il[r].targetTest(t););i=il[r]}for(r=e.length;r--;)e[r]&&(e[r]._gsap||(e[r]._gsap=new q0(e[r],i)))||e.splice(r,1);return e},Wr=function(e){return e._gsap||pf(ti(e))[0]._gsap},A0=function(e,t,i){return(i=e[t])&&Ht(i)?e[t]():lf(i)&&e.getAttribute&&e.getAttribute(t)||i},Dn=function(e,t){return(e=e.split(",")).forEach(t)||e},Wt=function(e){return Math.round(e*1e5)/1e5||0},Ot=function(e){return Math.round(e*1e7)/1e7||0},Is=function(e,t){var i=t.charAt(0),r=parseFloat(t.substr(2));return e=parseFloat(e),i==="+"?e+r:i==="-"?e-r:i==="*"?e*r:e/r},i2=function(e,t){for(var i=t.length,r=0;e.indexOf(t[r])<0&&++r<i;);return r<i},xl=function(){var e=vr.length,t=vr.slice(0),i,r;for(wh={},vr.length=0,i=0;i<e;i++)r=t[i],r&&r._lazy&&(r.render(r._lazy[0],r._lazy[1],!0)._lazy=0)},mf=function(e){return!!(e._initted||e._startAt||e.add)},R0=function(e,t,i,r){vr.length&&!hn&&xl(),e.render(t,i,!!(hn&&t<0&&mf(e))),vr.length&&!hn&&xl()},C0=function(e){var t=parseFloat(e);return(t||t===0)&&(e+"").match(QM).length<2?t:ln(e)?e.trim():e},P0=function(e){return e},qn=function(e,t){for(var i in t)i in e||(e[i]=t[i]);return e},r2=function(e){return function(t,i){for(var r in i)r in t||r==="duration"&&e||r==="ease"||(t[r]=i[r])}},Vs=function(e,t){for(var i in t)e[i]=t[i];return e},wp=function n(e,t){for(var i in t)i!=="__proto__"&&i!=="constructor"&&i!=="prototype"&&(e[i]=Li(t[i])?n(e[i]||(e[i]={}),t[i]):t[i]);return e},yl=function(e,t){var i={},r;for(r in e)r in t||(i[r]=e[r]);return i},Fa=function(e){var t=e.parent||Bt,i=e.keyframes?r2(vn(e.keyframes)):qn;if(Pn(e.inherit))for(;t;)i(e,t.vars.defaults),t=t.parent||t._dp;return e},s2=function(e,t){for(var i=e.length,r=i===t.length;r&&i--&&e[i]===t[i];);return i<0},D0=function(e,t,i,r,s){var a=e[r],o;if(s)for(o=t[s];a&&a[s]>o;)a=a._prev;return a?(t._next=a._next,a._next=t):(t._next=e[i],e[i]=t),t._next?t._next._prev=t:e[r]=t,t._prev=a,t.parent=t._dp=e,t},Ol=function(e,t,i,r){i===void 0&&(i="_first"),r===void 0&&(r="_last");var s=t._prev,a=t._next;s?s._next=a:e[i]===t&&(e[i]=a),a?a._prev=s:e[r]===t&&(e[r]=s),t._next=t._prev=t.parent=null},Sr=function(e,t){e.parent&&(!t||e.parent.autoRemoveChildren)&&e.parent.remove&&e.parent.remove(e),e._act=0},Xr=function(e,t){if(e&&(!t||t._end>e._dur||t._start<0))for(var i=e;i;)i._dirty=1,i=i.parent;return e},a2=function(e){for(var t=e.parent;t&&t.parent;)t._dirty=1,t.totalDuration(),t=t.parent;return e},Ah=function(e,t,i,r){return e._startAt&&(hn?e._startAt.revert(nl):e.vars.immediateRender&&!e.vars.autoRevert||e._startAt.render(t,!0,r))},o2=function n(e){return!e||e._ts&&n(e.parent)},Ap=function(e){return e._repeat?Ws(e._tTime,e=e.duration()+e._rDelay)*e:0},Ws=function(e,t){var i=Math.floor(e=Ot(e/t));return e&&i===e?i-1:i},bl=function(e,t){return(e-t._start)*t._ts+(t._ts>=0?0:t._dirty?t.totalDuration():t._tDur)},Bl=function(e){return e._end=Ot(e._start+(e._tDur/Math.abs(e._ts||e._rts||Rt)||0))},kl=function(e,t){var i=e._dp;return i&&i.smoothChildTiming&&e._ts&&(e._start=Ot(i._time-(e._ts>0?t/e._ts:((e._dirty?e.totalDuration():e._tDur)-t)/-e._ts)),Bl(e),i._dirty||Xr(i,e)),e},U0=function(e,t){var i;if((t._time||!t._dur&&t._initted||t._start<e._time&&(t._dur||!t.add))&&(i=bl(e.rawTime(),t),(!t._dur||Ja(0,t.totalDuration(),i)-t._tTime>Rt)&&t.render(i,!0)),Xr(e,t)._dp&&e._initted&&e._time>=e._dur&&e._ts){if(e._dur<e.duration())for(i=e;i._dp;)i.rawTime()>=0&&i.totalTime(i._tTime),i=i._dp;e._zTime=-Rt}},wi=function(e,t,i,r){return t.parent&&Sr(t),t._start=Ot((Ki(i)?i:i||e!==Bt?Jn(e,i,t):e._time)+t._delay),t._end=Ot(t._start+(t.totalDuration()/Math.abs(t.timeScale())||0)),D0(e,t,"_first","_last",e._sort?"_start":0),Rh(t)||(e._recent=t),r||U0(e,t),e._ts<0&&kl(e,e._tTime),e},L0=function(e,t){return(Yn.ScrollTrigger||hf("scrollTrigger",t))&&Yn.ScrollTrigger.create(t,e)},I0=function(e,t,i,r,s){if(_f(e,t,s),!e._initted)return 1;if(!i&&e._pt&&!hn&&(e._dur&&e.vars.lazy!==!1||!e._dur&&e.vars.lazy)&&w0!==Hn.frame)return vr.push(e),e._lazy=[s,r],1},l2=function n(e){var t=e.parent;return t&&t._ts&&t._initted&&!t._lock&&(t.rawTime()<0||n(t))},Rh=function(e){var t=e.data;return t==="isFromStart"||t==="isStart"},c2=function(e,t,i,r){var s=e.ratio,a=t<0||!t&&(!e._start&&l2(e)&&!(!e._initted&&Rh(e))||(e._ts<0||e._dp._ts<0)&&!Rh(e))?0:1,o=e._rDelay,l=0,c,u,f;if(o&&e._repeat&&(l=Ja(0,e._tDur,t),u=Ws(l,o),e._yoyo&&u&1&&(a=1-a),u!==Ws(e._tTime,o)&&(s=1-a,e.vars.repeatRefresh&&e._initted&&e.invalidate())),a!==s||hn||r||e._zTime===Rt||!t&&e._zTime){if(!e._initted&&I0(e,t,r,i,l))return;for(f=e._zTime,e._zTime=t||(i?Rt:0),i||(i=t&&!f),e.ratio=a,e._from&&(a=1-a),e._time=0,e._tTime=l,c=e._pt;c;)c.r(a,c.d),c=c._next;t<0&&Ah(e,t,i,!0),e._onUpdate&&!i&&Vn(e,"onUpdate"),l&&e._repeat&&!i&&e.parent&&Vn(e,"onRepeat"),(t>=e._tDur||t<0)&&e.ratio===a&&(a&&Sr(e,1),!i&&!hn&&(Vn(e,a?"onComplete":"onReverseComplete",!0),e._prom&&e._prom()))}else e._zTime||(e._zTime=t)},u2=function(e,t,i){var r;if(i>t)for(r=e._first;r&&r._start<=i;){if(r.data==="isPause"&&r._start>t)return r;r=r._next}else for(r=e._last;r&&r._start>=i;){if(r.data==="isPause"&&r._start<t)return r;r=r._prev}},Xs=function(e,t,i,r){var s=e._repeat,a=Ot(t)||0,o=e._tTime/e._tDur;return o&&!r&&(e._time*=a/e._dur),e._dur=a,e._tDur=s?s<0?1e10:Ot(a*(s+1)+e._rDelay*s):a,o>0&&!r&&kl(e,e._tTime=e._tDur*o),e.parent&&Bl(e),i||Xr(e.parent,e),e},Rp=function(e){return e instanceof Cn?Xr(e):Xs(e,e._dur)},h2={_start:0,endTime:Ha,totalDuration:Ha},Jn=function n(e,t,i){var r=e.labels,s=e._recent||h2,a=e.duration()>=ei?s.endTime(!1):e._dur,o,l,c;return ln(t)&&(isNaN(t)||t in r)?(l=t.charAt(0),c=t.substr(-1)==="%",o=t.indexOf("="),l==="<"||l===">"?(o>=0&&(t=t.replace(/=/,"")),(l==="<"?s._start:s.endTime(s._repeat>=0))+(parseFloat(t.substr(1))||0)*(c?(o<0?s:i).totalDuration()/100:1)):o<0?(t in r||(r[t]=a),r[t]):(l=parseFloat(t.charAt(o-1)+t.substr(o+1)),c&&i&&(l=l/100*(vn(i)?i[0]:i).totalDuration()),o>1?n(e,t.substr(0,o-1),i)+l:a+l)):t==null?a:+t},Na=function(e,t,i){var r=Ki(t[1]),s=(r?2:1)+(e<2?0:1),a=t[s],o,l;if(r&&(a.duration=t[1]),a.parent=i,e){for(o=a,l=i;l&&!("immediateRender"in o);)o=l.vars.defaults||{},l=Pn(l.vars.inherit)&&l.parent;a.immediateRender=Pn(o.immediateRender),e<2?a.runBackwards=1:a.startAt=t[s-1]}return new jt(t[0],a,t[s+1])},Ar=function(e,t){return e||e===0?t(e):t},Ja=function(e,t,i){return i<e?e:i>t?t:i},gn=function(e,t){return!ln(e)||!(t=e2.exec(e))?"":t[1]},f2=function(e,t,i){return Ar(i,function(r){return Ja(e,t,r)})},Ch=[].slice,F0=function(e,t){return e&&Li(e)&&"length"in e&&(!t&&!e.length||e.length-1 in e&&Li(e[0]))&&!e.nodeType&&e!==Si},d2=function(e,t,i){return i===void 0&&(i=[]),e.forEach(function(r){var s;return ln(r)&&!t||F0(r,1)?(s=i).push.apply(s,ti(r)):i.push(r)})||i},ti=function(e,t,i){return It&&!t&&It.selector?It.selector(e):ln(e)&&!i&&(Eh||!js())?Ch.call((t||uf).querySelectorAll(e),0):vn(e)?d2(e,i):F0(e)?Ch.call(e,0):e?[e]:[]},Ph=function(e){return e=ti(e)[0]||Ga("Invalid scope")||{},function(t){var i=e.current||e.nativeElement||e;return ti(t,i.querySelectorAll?i:i===e?Ga("Invalid scope")||uf.createElement("div"):e)}},N0=function(e){return e.sort(function(){return .5-Math.random()})},O0=function(e){if(Ht(e))return e;var t=Li(e)?e:{each:e},i=jr(t.ease),r=t.from||0,s=parseFloat(t.base)||0,a={},o=r>0&&r<1,l=isNaN(r)||o,c=t.axis,u=r,f=r;return ln(r)?u=f={center:.5,edges:.5,end:1}[r]||0:!o&&l&&(u=r[0],f=r[1]),function(h,d,m){var g=(m||t).length,p=a[g],_,v,S,y,M,T,w,b,x;if(!p){if(x=t.grid==="auto"?0:(t.grid||[1,ei])[1],!x){for(w=-ei;w<(w=m[x++].getBoundingClientRect().left)&&x<g;);x<g&&x--}for(p=a[g]=[],_=l?Math.min(x,g)*u-.5:r%x,v=x===ei?0:l?g*f/x-.5:r/x|0,w=0,b=ei,T=0;T<g;T++)S=T%x-_,y=v-(T/x|0),p[T]=M=c?Math.abs(c==="y"?y:S):x0(S*S+y*y),M>w&&(w=M),M<b&&(b=M);r==="random"&&N0(p),p.max=w-b,p.min=b,p.v=g=(parseFloat(t.amount)||parseFloat(t.each)*(x>g?g-1:c?c==="y"?g/x:x:Math.max(x,g/x))||0)*(r==="edges"?-1:1),p.b=g<0?s-g:s,p.u=gn(t.amount||t.each)||0,i=i&&g<0?w2(i):i}return g=(p[h]-p.min)/p.max||0,Ot(p.b+(i?i(g):g)*p.v)+p.u}},Dh=function(e){var t=Math.pow(10,((e+"").split(".")[1]||"").length);return function(i){var r=Ot(Math.round(parseFloat(i)/e)*e*t);return(r-r%1)/t+(Ki(i)?0:gn(i))}},B0=function(e,t){var i=vn(e),r,s;return!i&&Li(e)&&(r=i=e.radius||ei,e.values?(e=ti(e.values),(s=!Ki(e[0]))&&(r*=r)):e=Dh(e.increment)),Ar(t,i?Ht(e)?function(a){return s=e(a),Math.abs(s-a)<=r?s:a}:function(a){for(var o=parseFloat(s?a.x:a),l=parseFloat(s?a.y:0),c=ei,u=0,f=e.length,h,d;f--;)s?(h=e[f].x-o,d=e[f].y-l,h=h*h+d*d):h=Math.abs(e[f]-o),h<c&&(c=h,u=f);return u=!r||c<=r?e[u]:a,s||u===a||Ki(a)?u:u+gn(a)}:Dh(e))},k0=function(e,t,i,r){return Ar(vn(e)?!t:i===!0?!!(i=0):!r,function(){return vn(e)?e[~~(Math.random()*e.length)]:(i=i||1e-5)&&(r=i<1?Math.pow(10,(i+"").length-2):1)&&Math.floor(Math.round((e-i/2+Math.random()*(t-e+i*.99))/i)*i*r)/r})},p2=function(){for(var e=arguments.length,t=new Array(e),i=0;i<e;i++)t[i]=arguments[i];return function(r){return t.reduce(function(s,a){return a(s)},r)}},m2=function(e,t){return function(i){return e(parseFloat(i))+(t||gn(i))}},g2=function(e,t,i){return G0(e,t,0,1,i)},z0=function(e,t,i){return Ar(i,function(r){return e[~~t(r)]})},_2=function n(e,t,i){var r=t-e;return vn(e)?z0(e,n(0,e.length),t):Ar(i,function(s){return(r+(s-e)%r)%r+e})},v2=function n(e,t,i){var r=t-e,s=r*2;return vn(e)?z0(e,n(0,e.length-1),t):Ar(i,function(a){return a=(s+(a-e)%s)%s||0,e+(a>r?s-a:a)})},Va=function(e){return e.replace($M,function(t){var i=t.indexOf("[")+1,r=t.substring(i||7,i?t.indexOf("]"):t.length-1).split(JM);return k0(i?r:+r[0],i?0:+r[1],+r[2]||1e-5)})},G0=function(e,t,i,r,s){var a=t-e,o=r-i;return Ar(s,function(l){return i+((l-e)/a*o||0)})},x2=function n(e,t,i,r){var s=isNaN(e+t)?0:function(d){return(1-d)*e+d*t};if(!s){var a=ln(e),o={},l,c,u,f,h;if(i===!0&&(r=1)&&(i=null),a)e={p:e},t={p:t};else if(vn(e)&&!vn(t)){for(u=[],f=e.length,h=f-2,c=1;c<f;c++)u.push(n(e[c-1],e[c]));f--,s=function(m){m*=f;var g=Math.min(h,~~m);return u[g](m-g)},i=t}else r||(e=Vs(vn(e)?[]:{},e));if(!u){for(l in t)gf.call(o,e,l,"get",t[l]);s=function(m){return yf(m,o)||(a?e.p:e)}}}return Ar(i,s)},Cp=function(e,t,i){var r=e.labels,s=ei,a,o,l;for(a in r)o=r[a]-t,o<0==!!i&&o&&s>(o=Math.abs(o))&&(l=a,s=o);return l},Vn=function(e,t,i){var r=e.vars,s=r[t],a=It,o=e._ctx,l,c,u;if(s)return l=r[t+"Params"],c=r.callbackScope||e,i&&vr.length&&xl(),o&&(It=o),u=l?s.apply(c,l):s.call(c),It=a,u},Pa=function(e){return Sr(e),e.scrollTrigger&&e.scrollTrigger.kill(!!hn),e.progress()<1&&Vn(e,"onInterrupt"),e},Ds,H0=[],V0=function(e){if(e)if(e=!e.name&&e.default||e,cf()||e.headless){var t=e.name,i=Ht(e),r=t&&!i&&e.init?function(){this._props=[]}:e,s={init:Ha,render:yf,add:gf,kill:N2,modifier:F2,rawVars:0},a={targetTest:0,get:0,getSetter:xf,aliases:{},register:0};if(js(),e!==r){if(zn[t])return;qn(r,qn(yl(e,s),a)),Vs(r.prototype,Vs(s,yl(e,a))),zn[r.prop=t]=r,e.targetTest&&(il.push(r),ff[t]=1),t=(t==="css"?"CSS":t.charAt(0).toUpperCase()+t.substr(1))+"Plugin"}E0(t,r),e.register&&e.register(In,r,Un)}else H0.push(e)},At=255,Da={aqua:[0,At,At],lime:[0,At,0],silver:[192,192,192],black:[0,0,0],maroon:[128,0,0],teal:[0,128,128],blue:[0,0,At],navy:[0,0,128],white:[At,At,At],olive:[128,128,0],yellow:[At,At,0],orange:[At,165,0],gray:[128,128,128],purple:[128,0,128],green:[0,128,0],red:[At,0,0],pink:[At,192,203],cyan:[0,At,At],transparent:[At,At,At,0]},jc=function(e,t,i){return e+=e<0?1:e>1?-1:0,(e*6<1?t+(i-t)*e*6:e<.5?i:e*3<2?t+(i-t)*(2/3-e)*6:t)*At+.5|0},W0=function(e,t,i){var r=e?Ki(e)?[e>>16,e>>8&At,e&At]:0:Da.black,s,a,o,l,c,u,f,h,d,m;if(!r){if(e.substr(-1)===","&&(e=e.substr(0,e.length-1)),Da[e])r=Da[e];else if(e.charAt(0)==="#"){if(e.length<6&&(s=e.charAt(1),a=e.charAt(2),o=e.charAt(3),e="#"+s+s+a+a+o+o+(e.length===5?e.charAt(4)+e.charAt(4):"")),e.length===9)return r=parseInt(e.substr(1,6),16),[r>>16,r>>8&At,r&At,parseInt(e.substr(7),16)/255];e=parseInt(e.substr(1),16),r=[e>>16,e>>8&At,e&At]}else if(e.substr(0,3)==="hsl"){if(r=m=e.match(Tp),!t)l=+r[0]%360/360,c=+r[1]/100,u=+r[2]/100,a=u<=.5?u*(c+1):u+c-u*c,s=u*2-a,r.length>3&&(r[3]*=1),r[0]=jc(l+1/3,s,a),r[1]=jc(l,s,a),r[2]=jc(l-1/3,s,a);else if(~e.indexOf("="))return r=e.match(b0),i&&r.length<4&&(r[3]=1),r}else r=e.match(Tp)||Da.transparent;r=r.map(Number)}return t&&!m&&(s=r[0]/At,a=r[1]/At,o=r[2]/At,f=Math.max(s,a,o),h=Math.min(s,a,o),u=(f+h)/2,f===h?l=c=0:(d=f-h,c=u>.5?d/(2-f-h):d/(f+h),l=f===s?(a-o)/d+(a<o?6:0):f===a?(o-s)/d+2:(s-a)/d+4,l*=60),r[0]=~~(l+.5),r[1]=~~(c*100+.5),r[2]=~~(u*100+.5)),i&&r.length<4&&(r[3]=1),r},X0=function(e){var t=[],i=[],r=-1;return e.split(xr).forEach(function(s){var a=s.match(Ps)||[];t.push.apply(t,a),i.push(r+=a.length+1)}),t.c=i,t},Pp=function(e,t,i){var r="",s=(e+r).match(xr),a=t?"hsla(":"rgba(",o=0,l,c,u,f;if(!s)return e;if(s=s.map(function(h){return(h=W0(h,t,1))&&a+(t?h[0]+","+h[1]+"%,"+h[2]+"%,"+h[3]:h.join(","))+")"}),i&&(u=X0(e),l=i.c,l.join(r)!==u.c.join(r)))for(c=e.replace(xr,"1").split(Ps),f=c.length-1;o<f;o++)r+=c[o]+(~l.indexOf(o)?s.shift()||a+"0,0,0,0)":(u.length?u:s.length?s:i).shift());if(!c)for(c=e.split(xr),f=c.length-1;o<f;o++)r+=c[o]+s[o];return r+c[f]},xr=(function(){var n="(?:\\b(?:(?:rgb|rgba|hsl|hsla)\\(.+?\\))|\\B#(?:[0-9a-f]{3,4}){1,2}\\b",e;for(e in Da)n+="|"+e+"\\b";return new RegExp(n+")","gi")})(),y2=/hsl[a]?\(/,j0=function(e){var t=e.join(" "),i;if(xr.lastIndex=0,xr.test(t))return i=y2.test(t),e[1]=Pp(e[1],i),e[0]=Pp(e[0],i,X0(e[1])),!0},Wa,Hn=(function(){var n=Date.now,e=500,t=33,i=n(),r=i,s=1e3/240,a=s,o=[],l,c,u,f,h,d,m=function g(p){var _=n()-r,v=p===!0,S,y,M,T;if((_>e||_<0)&&(i+=_-t),r+=_,M=r-i,S=M-a,(S>0||v)&&(T=++f.frame,h=M-f.time*1e3,f.time=M=M/1e3,a+=S+(S>=s?4:s-S),y=1),v||(l=c(g)),y)for(d=0;d<o.length;d++)o[d](M,h,T,p)};return f={time:0,frame:0,tick:function(){m(!0)},deltaRatio:function(p){return h/(1e3/(p||60))},wake:function(){M0&&(!Eh&&cf()&&(Si=Eh=window,uf=Si.document||{},Yn.gsap=In,(Si.gsapVersions||(Si.gsapVersions=[])).push(In.version),T0(vl||Si.GreenSockGlobals||!Si.gsap&&Si||{}),H0.forEach(V0)),u=typeof requestAnimationFrame<"u"&&requestAnimationFrame,l&&f.sleep(),c=u||function(p){return setTimeout(p,a-f.time*1e3+1|0)},Wa=1,m(2))},sleep:function(){(u?cancelAnimationFrame:clearTimeout)(l),Wa=0,c=Ha},lagSmoothing:function(p,_){e=p||1/0,t=Math.min(_||33,e)},fps:function(p){s=1e3/(p||240),a=f.time*1e3+s},add:function(p,_,v){var S=_?function(y,M,T,w){p(y,M,T,w),f.remove(S)}:p;return f.remove(p),o[v?"unshift":"push"](S),js(),S},remove:function(p,_){~(_=o.indexOf(p))&&o.splice(_,1)&&d>=_&&d--},_listeners:o},f})(),js=function(){return!Wa&&Hn.wake()},dt={},b2=/^[\d.\-M][\d.\-,\s]/,S2=/["']/g,M2=function(e){for(var t={},i=e.substr(1,e.length-3).split(":"),r=i[0],s=1,a=i.length,o,l,c;s<a;s++)l=i[s],o=s!==a-1?l.lastIndexOf(","):l.length,c=l.substr(0,o),t[r]=isNaN(c)?c.replace(S2,"").trim():+c,r=l.substr(o+1).trim();return t},T2=function(e){var t=e.indexOf("(")+1,i=e.indexOf(")"),r=e.indexOf("(",t);return e.substring(t,~r&&r<i?e.indexOf(")",i+1):i)},E2=function(e){var t=(e+"").split("("),i=dt[t[0]];return i&&t.length>1&&i.config?i.config.apply(null,~e.indexOf("{")?[M2(t[1])]:T2(e).split(",").map(C0)):dt._CE&&b2.test(e)?dt._CE("",e):i},w2=function(e){return function(t){return 1-e(1-t)}},jr=function(e,t){return e&&(Ht(e)?e:dt[e]||E2(e))||t},es=function(e,t,i,r){i===void 0&&(i=function(l){return 1-t(1-l)}),r===void 0&&(r=function(l){return l<.5?t(l*2)/2:1-t((1-l)*2)/2});var s={easeIn:t,easeOut:i,easeInOut:r},a;return Dn(e,function(o){dt[o]=Yn[o]=s,dt[a=o.toLowerCase()]=i;for(var l in s)dt[a+(l==="easeIn"?".in":l==="easeOut"?".out":".inOut")]=dt[o+"."+l]=s[l]}),s},Y0=function(e){return function(t){return t<.5?(1-e(1-t*2))/2:.5+e((t-.5)*2)/2}},Yc=function n(e,t,i){var r=t>=1?t:1,s=(i||(e?.3:.45))/(t<1?t:1),a=s/Th*(Math.asin(1/r)||0),o=function(u){return u===1?1:r*Math.pow(2,-10*u)*ZM((u-a)*s)+1},l=e==="out"?o:e==="in"?function(c){return 1-o(1-c)}:Y0(o);return s=Th/s,l.config=function(c,u){return n(e,c,u)},l},qc=function n(e,t){t===void 0&&(t=1.70158);var i=function(a){return a?--a*a*((t+1)*a+t)+1:0},r=e==="out"?i:e==="in"?function(s){return 1-i(1-s)}:Y0(i);return r.config=function(s){return n(e,s)},r};Dn("Linear,Quad,Cubic,Quart,Quint,Strong",function(n,e){var t=e<5?e+1:e;es(n+",Power"+(t-1),e?function(i){return Math.pow(i,t)}:function(i){return i},function(i){return 1-Math.pow(1-i,t)},function(i){return i<.5?Math.pow(i*2,t)/2:1-Math.pow((1-i)*2,t)/2})});dt.Linear.easeNone=dt.none=dt.Linear.easeIn;es("Elastic",Yc("in"),Yc("out"),Yc());(function(n,e){var t=1/e,i=2*t,r=2.5*t,s=function(o){return o<t?n*o*o:o<i?n*Math.pow(o-1.5/e,2)+.75:o<r?n*(o-=2.25/e)*o+.9375:n*Math.pow(o-2.625/e,2)+.984375};es("Bounce",function(a){return 1-s(1-a)},s)})(7.5625,2.75);es("Expo",function(n){return Math.pow(2,10*(n-1))*n+n*n*n*n*n*n*(1-n)});es("Circ",function(n){return-(x0(1-n*n)-1)});es("Sine",function(n){return n===1?1:-KM(n*YM)+1});es("Back",qc("in"),qc("out"),qc());dt.SteppedEase=dt.steps=Yn.SteppedEase={config:function(e,t){e===void 0&&(e=1);var i=1/e,r=e+(t?0:1),s=t?1:0,a=1-Rt;return function(o){return((r*Ja(0,a,o)|0)+s)*i}}};za.ease=dt["quad.out"];Dn("onComplete,onUpdate,onStart,onRepeat,onReverseComplete,onInterrupt",function(n){return df+=n+","+n+"Params,"});var q0=function(e,t){this.id=qM++,e._gsap=this,this.target=e,this.harness=t,this.get=t?t.get:A0,this.set=t?t.getSetter:xf},Xa=(function(){function n(t){this.vars=t,this._delay=+t.delay||0,(this._repeat=t.repeat===1/0?-2:t.repeat||0)&&(this._rDelay=t.repeatDelay||0,this._yoyo=!!t.yoyo||!!t.yoyoEase),this._ts=1,Xs(this,+t.duration,1,1),this.data=t.data,It&&(this._ctx=It,It.data.push(this)),Wa||Hn.wake()}var e=n.prototype;return e.delay=function(i){return i||i===0?(this.parent&&this.parent.smoothChildTiming&&this.startTime(this._start+i-this._delay),this._delay=i,this):this._delay},e.duration=function(i){return arguments.length?this.totalDuration(this._repeat>0?i+(i+this._rDelay)*this._repeat:i):this.totalDuration()&&this._dur},e.totalDuration=function(i){return arguments.length?(this._dirty=0,Xs(this,this._repeat<0?i:(i-this._repeat*this._rDelay)/(this._repeat+1))):this._tDur},e.totalTime=function(i,r){if(js(),!arguments.length)return this._tTime;var s=this._dp;if(s&&s.smoothChildTiming&&this._ts){for(kl(this,i),!s._dp||s.parent||U0(s,this);s&&s.parent;)s.parent._time!==s._start+(s._ts>=0?s._tTime/s._ts:(s.totalDuration()-s._tTime)/-s._ts)&&s.totalTime(s._tTime,!0),s=s.parent;!this.parent&&this._dp.autoRemoveChildren&&(this._ts>0&&i<this._tDur||this._ts<0&&i>0||!this._tDur&&!i)&&wi(this._dp,this,this._start-this._delay)}return(this._tTime!==i||!this._dur&&!r||this._initted&&Math.abs(this._zTime)===Rt||!this._initted&&this._dur&&i||!i&&!this._initted&&(this.add||this._ptLookup))&&(this._ts||(this._pTime=i),R0(this,i,r)),this},e.time=function(i,r){return arguments.length?this.totalTime(Math.min(this.totalDuration(),i+Ap(this))%(this._dur+this._rDelay)||(i?this._dur:0),r):this._time},e.totalProgress=function(i,r){return arguments.length?this.totalTime(this.totalDuration()*i,r):this.totalDuration()?Math.min(1,this._tTime/this._tDur):this.rawTime()>=0&&this._initted?1:0},e.progress=function(i,r){return arguments.length?this.totalTime(this.duration()*(this._yoyo&&!(this.iteration()&1)?1-i:i)+Ap(this),r):this.duration()?Math.min(1,this._time/this._dur):this.rawTime()>0?1:0},e.iteration=function(i,r){var s=this.duration()+this._rDelay;return arguments.length?this.totalTime(this._time+(i-1)*s,r):this._repeat?Ws(this._tTime,s)+1:1},e.timeScale=function(i,r){if(!arguments.length)return this._rts===-Rt?0:this._rts;if(this._rts===i)return this;var s=this.parent&&this._ts?bl(this.parent._time,this):this._tTime;return this._rts=+i||0,this._ts=this._ps||i===-Rt?0:this._rts,this.totalTime(Ja(-Math.abs(this._delay),this.totalDuration(),s),r!==!1),Bl(this),a2(this)},e.paused=function(i){return arguments.length?(this._ps!==i&&(this._ps=i,i?(this._pTime=this._tTime||Math.max(-this._delay,this.rawTime()),this._ts=this._act=0):(js(),this._ts=this._rts,this.totalTime(this.parent&&!this.parent.smoothChildTiming?this.rawTime():this._tTime||this._pTime,this.progress()===1&&Math.abs(this._zTime)!==Rt&&(this._tTime-=Rt)))),this):this._ps},e.startTime=function(i){if(arguments.length){this._start=Ot(i);var r=this.parent||this._dp;return r&&(r._sort||!this.parent)&&wi(r,this,this._start-this._delay),this}return this._start},e.endTime=function(i){return this._start+(Pn(i)?this.totalDuration():this.duration())/Math.abs(this._ts||1)},e.rawTime=function(i){var r=this.parent||this._dp;return r?i&&(!this._ts||this._repeat&&this._time&&this.totalProgress()<1)?this._tTime%(this._dur+this._rDelay):this._ts?bl(r.rawTime(i),this):this._tTime:this._tTime},e.revert=function(i){i===void 0&&(i=n2);var r=hn;return hn=i,mf(this)&&(this.timeline&&this.timeline.revert(i),this.totalTime(-.01,i.suppressEvents)),this.data!=="nested"&&i.kill!==!1&&this.kill(),hn=r,this},e.globalTime=function(i){for(var r=this,s=arguments.length?i:r.rawTime();r;)s=r._start+s/(Math.abs(r._ts)||1),r=r._dp;return!this.parent&&this._sat?this._sat.globalTime(i):s},e.repeat=function(i){return arguments.length?(this._repeat=i===1/0?-2:i,Rp(this)):this._repeat===-2?1/0:this._repeat},e.repeatDelay=function(i){if(arguments.length){var r=this._time;return this._rDelay=i,Rp(this),r?this.time(r):this}return this._rDelay},e.yoyo=function(i){return arguments.length?(this._yoyo=i,this):this._yoyo},e.seek=function(i,r){return this.totalTime(Jn(this,i),Pn(r))},e.restart=function(i,r){return this.play().totalTime(i?-this._delay:0,Pn(r)),this._dur||(this._zTime=-Rt),this},e.play=function(i,r){return i!=null&&this.seek(i,r),this.reversed(!1).paused(!1)},e.reverse=function(i,r){return i!=null&&this.seek(i||this.totalDuration(),r),this.reversed(!0).paused(!1)},e.pause=function(i,r){return i!=null&&this.seek(i,r),this.paused(!0)},e.resume=function(){return this.paused(!1)},e.reversed=function(i){return arguments.length?(!!i!==this.reversed()&&this.timeScale(-this._rts||(i?-Rt:0)),this):this._rts<0},e.invalidate=function(){return this._initted=this._act=0,this._zTime=-Rt,this},e.isActive=function(){var i=this.parent||this._dp,r=this._start,s;return!!(!i||this._ts&&this._initted&&i.isActive()&&(s=i.rawTime(!0))>=r&&s<this.endTime(!0)-Rt)},e.eventCallback=function(i,r,s){var a=this.vars;return arguments.length>1?(r?(a[i]=r,s&&(a[i+"Params"]=s),i==="onUpdate"&&(this._onUpdate=r)):delete a[i],this):a[i]},e.then=function(i){var r=this,s=r._prom;return new Promise(function(a){var o=Ht(i)?i:P0,l=function(){var u=r.then;r.then=null,s&&s(),Ht(o)&&(o=o(r))&&(o.then||o===r)&&(r.then=u),a(o),r.then=u};r._initted&&r.totalProgress()===1&&r._ts>=0||!r._tTime&&r._ts<0?l():r._prom=l})},e.kill=function(){Pa(this)},n})();qn(Xa.prototype,{_time:0,_start:0,_end:0,_tTime:0,_tDur:0,_dirty:0,_repeat:0,_yoyo:!1,parent:null,_initted:!1,_rDelay:0,_ts:1,_dp:0,ratio:0,_zTime:-Rt,_prom:0,_ps:!1,_rts:1});var Cn=(function(n){v0(e,n);function e(i,r){var s;return i===void 0&&(i={}),s=n.call(this,i)||this,s.labels={},s.smoothChildTiming=!!i.smoothChildTiming,s.autoRemoveChildren=!!i.autoRemoveChildren,s._sort=Pn(i.sortChildren),Bt&&wi(i.parent||Bt,Gi(s),r),i.reversed&&s.reverse(),i.paused&&s.paused(!0),i.scrollTrigger&&L0(Gi(s),i.scrollTrigger),s}var t=e.prototype;return t.to=function(r,s,a){return Na(0,arguments,this),this},t.from=function(r,s,a){return Na(1,arguments,this),this},t.fromTo=function(r,s,a,o){return Na(2,arguments,this),this},t.set=function(r,s,a){return s.duration=0,s.parent=this,Fa(s).repeatDelay||(s.repeat=0),s.immediateRender=!!s.immediateRender,new jt(r,s,Jn(this,a),1),this},t.call=function(r,s,a){return wi(this,jt.delayedCall(0,r,s),a)},t.staggerTo=function(r,s,a,o,l,c,u){return a.duration=s,a.stagger=a.stagger||o,a.onComplete=c,a.onCompleteParams=u,a.parent=this,new jt(r,a,Jn(this,l)),this},t.staggerFrom=function(r,s,a,o,l,c,u){return a.runBackwards=1,Fa(a).immediateRender=Pn(a.immediateRender),this.staggerTo(r,s,a,o,l,c,u)},t.staggerFromTo=function(r,s,a,o,l,c,u,f){return o.startAt=a,Fa(o).immediateRender=Pn(o.immediateRender),this.staggerTo(r,s,o,l,c,u,f)},t.render=function(r,s,a){var o=this._time,l=this._dirty?this.totalDuration():this._tDur,c=this._dur,u=r<=0?0:Ot(r),f=this._zTime<0!=r<0&&(this._initted||!c),h,d,m,g,p,_,v,S,y,M,T,w;if(this!==Bt&&u>l&&r>=0&&(u=l),u!==this._tTime||a||f){if(o!==this._time&&c&&(u+=this._time-o,r+=this._time-o),h=u,y=this._start,S=this._ts,_=!S,f&&(c||(o=this._zTime),(r||!s)&&(this._zTime=r)),this._repeat){if(T=this._yoyo,p=c+this._rDelay,this._repeat<-1&&r<0)return this.totalTime(p*100+r,s,a);if(h=Ot(u%p),u===l?(g=this._repeat,h=c):(M=Ot(u/p),g=~~M,g&&g===M&&(h=c,g--),h>c&&(h=c)),M=Ws(this._tTime,p),!o&&this._tTime&&M!==g&&this._tTime-M*p-this._dur<=0&&(M=g),T&&g&1&&(h=c-h,w=1),g!==M&&!this._lock){var b=T&&M&1,x=b===(T&&g&1);if(g<M&&(b=!b),o=b?0:u%c?c:u,this._lock=1,this.render(o||(w?0:Ot(g*p)),s,!c)._lock=0,this._tTime=u,!s&&this.parent&&Vn(this,"onRepeat"),this.vars.repeatRefresh&&!w&&(this.invalidate()._lock=1,M=g),o&&o!==this._time||_!==!this._ts||this.vars.onRepeat&&!this.parent&&!this._act)return this;if(c=this._dur,l=this._tDur,x&&(this._lock=2,o=b?c:-1e-4,this.render(o,!0),this.vars.repeatRefresh&&!w&&this.invalidate()),this._lock=0,!this._ts&&!_)return this}}if(this._hasPause&&!this._forcing&&this._lock<2&&(v=u2(this,Ot(o),Ot(h)),v&&(u-=h-(h=v._start))),this._tTime=u,this._time=h,this._act=!!S,this._initted||(this._onUpdate=this.vars.onUpdate,this._initted=1,this._zTime=r,o=0),!o&&u&&c&&!s&&!M&&(Vn(this,"onStart"),this._tTime!==u))return this;if(h>=o&&r>=0)for(d=this._first;d;){if(m=d._next,(d._act||h>=d._start)&&d._ts&&v!==d){if(d.parent!==this)return this.render(r,s,a);if(d.render(d._ts>0?(h-d._start)*d._ts:(d._dirty?d.totalDuration():d._tDur)+(h-d._start)*d._ts,s,a),h!==this._time||!this._ts&&!_){v=0,m&&(u+=this._zTime=-Rt);break}}d=m}else{d=this._last;for(var A=r<0?r:h;d;){if(m=d._prev,(d._act||A<=d._end)&&d._ts&&v!==d){if(d.parent!==this)return this.render(r,s,a);if(d.render(d._ts>0?(A-d._start)*d._ts:(d._dirty?d.totalDuration():d._tDur)+(A-d._start)*d._ts,s,a||hn&&mf(d)),h!==this._time||!this._ts&&!_){v=0,m&&(u+=this._zTime=A?-Rt:Rt);break}}d=m}}if(v&&!s&&(this.pause(),v.render(h>=o?0:-Rt)._zTime=h>=o?1:-1,this._ts))return this._start=y,Bl(this),this.render(r,s,a);this._onUpdate&&!s&&Vn(this,"onUpdate",!0),(u===l&&this._tTime>=this.totalDuration()||!u&&o)&&(y===this._start||Math.abs(S)!==Math.abs(this._ts))&&(this._lock||((r||!c)&&(u===l&&this._ts>0||!u&&this._ts<0)&&Sr(this,1),!s&&!(r<0&&!o)&&(u||o||!l)&&(Vn(this,u===l&&r>=0?"onComplete":"onReverseComplete",!0),this._prom&&!(u<l&&this.timeScale()>0)&&this._prom())))}return this},t.add=function(r,s){var a=this;if(Ki(s)||(s=Jn(this,s,r)),!(r instanceof Xa)){if(vn(r))return r.forEach(function(o){return a.add(o,s)}),this;if(ln(r))return this.addLabel(r,s);if(Ht(r))r=jt.delayedCall(0,r);else return this}return this!==r?wi(this,r,s):this},t.getChildren=function(r,s,a,o){r===void 0&&(r=!0),s===void 0&&(s=!0),a===void 0&&(a=!0),o===void 0&&(o=-ei);for(var l=[],c=this._first;c;)c._start>=o&&(c instanceof jt?s&&l.push(c):(a&&l.push(c),r&&l.push.apply(l,c.getChildren(!0,s,a)))),c=c._next;return l},t.getById=function(r){for(var s=this.getChildren(1,1,1),a=s.length;a--;)if(s[a].vars.id===r)return s[a]},t.remove=function(r){return ln(r)?this.removeLabel(r):Ht(r)?this.killTweensOf(r):(r.parent===this&&Ol(this,r),r===this._recent&&(this._recent=this._last),Xr(this))},t.totalTime=function(r,s){return arguments.length?(this._forcing=1,!this._dp&&this._ts&&(this._start=Ot(Hn.time-(this._ts>0?r/this._ts:(this.totalDuration()-r)/-this._ts))),n.prototype.totalTime.call(this,r,s),this._forcing=0,this):this._tTime},t.addLabel=function(r,s){return this.labels[r]=Jn(this,s),this},t.removeLabel=function(r){return delete this.labels[r],this},t.addPause=function(r,s,a){var o=jt.delayedCall(0,s||Ha,a);return o.data="isPause",this._hasPause=1,wi(this,o,Jn(this,r))},t.removePause=function(r){var s=this._first;for(r=Jn(this,r);s;)s._start===r&&s.data==="isPause"&&Sr(s),s=s._next},t.killTweensOf=function(r,s,a){for(var o=this.getTweensOf(r,a),l=o.length;l--;)pr!==o[l]&&o[l].kill(r,s);return this},t.getTweensOf=function(r,s){for(var a=[],o=ti(r),l=this._first,c=Ki(s),u;l;)l instanceof jt?i2(l._targets,o)&&(c?(!pr||l._initted&&l._ts)&&l.globalTime(0)<=s&&l.globalTime(l.totalDuration())>s:!s||l.isActive())&&a.push(l):(u=l.getTweensOf(o,s)).length&&a.push.apply(a,u),l=l._next;return a},t.tweenTo=function(r,s){s=s||{};var a=this,o=Jn(a,r),l=s,c=l.startAt,u=l.onStart,f=l.onStartParams,h=l.immediateRender,d,m=jt.to(a,qn({ease:s.ease||"none",lazy:!1,immediateRender:!1,time:o,overwrite:"auto",duration:s.duration||Math.abs((o-(c&&"time"in c?c.time:a._time))/a.timeScale())||Rt,onStart:function(){if(a.pause(),!d){var p=s.duration||Math.abs((o-(c&&"time"in c?c.time:a._time))/a.timeScale());m._dur!==p&&Xs(m,p,0,1).render(m._time,!0,!0),d=1}u&&u.apply(m,f||[])}},s));return h?m.render(0):m},t.tweenFromTo=function(r,s,a){return this.tweenTo(s,qn({startAt:{time:Jn(this,r)}},a))},t.recent=function(){return this._recent},t.nextLabel=function(r){return r===void 0&&(r=this._time),Cp(this,Jn(this,r))},t.previousLabel=function(r){return r===void 0&&(r=this._time),Cp(this,Jn(this,r),1)},t.currentLabel=function(r){return arguments.length?this.seek(r,!0):this.previousLabel(this._time+Rt)},t.shiftChildren=function(r,s,a){a===void 0&&(a=0);var o=this._first,l=this.labels,c;for(r=Ot(r);o;)o._start>=a&&(o._start+=r,o._end+=r),o=o._next;if(s)for(c in l)l[c]>=a&&(l[c]+=r);return Xr(this)},t.invalidate=function(r){var s=this._first;for(this._lock=0;s;)s.invalidate(r),s=s._next;return n.prototype.invalidate.call(this,r)},t.clear=function(r){r===void 0&&(r=!0);for(var s=this._first,a;s;)a=s._next,this.remove(s),s=a;return this._dp&&(this._time=this._tTime=this._pTime=0),r&&(this.labels={}),Xr(this)},t.totalDuration=function(r){var s=0,a=this,o=a._last,l=ei,c,u,f;if(arguments.length)return a.timeScale((a._repeat<0?a.duration():a.totalDuration())/(a.reversed()?-r:r));if(a._dirty){for(f=a.parent;o;)c=o._prev,o._dirty&&o.totalDuration(),u=o._start,u>l&&a._sort&&o._ts&&!a._lock?(a._lock=1,wi(a,o,u-o._delay,1)._lock=0):l=u,u<0&&o._ts&&(s-=u,(!f&&!a._dp||f&&f.smoothChildTiming)&&(a._start+=Ot(u/a._ts),a._time-=u,a._tTime-=u),a.shiftChildren(-u,!1,-1/0),l=0),o._end>s&&o._ts&&(s=o._end),o=c;Xs(a,a===Bt&&a._time>s?a._time:s,1,1),a._dirty=0}return a._tDur},e.updateRoot=function(r){if(Bt._ts&&(R0(Bt,bl(r,Bt)),w0=Hn.frame),Hn.frame>=Ep){Ep+=Xn.autoSleep||120;var s=Bt._first;if((!s||!s._ts)&&Xn.autoSleep&&Hn._listeners.length<2){for(;s&&!s._ts;)s=s._next;s||Hn.sleep()}}},e})(Xa);qn(Cn.prototype,{_lock:0,_hasPause:0,_forcing:0});var A2=function(e,t,i,r,s,a,o){var l=new Un(this._pt,e,t,0,1,eg,null,s),c=0,u=0,f,h,d,m,g,p,_,v;for(l.b=i,l.e=r,i+="",r+="",(_=~r.indexOf("random("))&&(r=Va(r)),a&&(v=[i,r],a(v,e,t),i=v[0],r=v[1]),h=i.match(Wc)||[];f=Wc.exec(r);)m=f[0],g=r.substring(c,f.index),d?d=(d+1)%5:g.substr(-5)==="rgba("&&(d=1),m!==h[u++]&&(p=parseFloat(h[u-1])||0,l._pt={_next:l._pt,p:g||u===1?g:",",s:p,c:m.charAt(1)==="="?Is(p,m)-p:parseFloat(m)-p,m:d&&d<4?Math.round:0},c=Wc.lastIndex);return l.c=c<r.length?r.substring(c,r.length):"",l.fp=o,(S0.test(r)||_)&&(l.e=0),this._pt=l,l},gf=function(e,t,i,r,s,a,o,l,c,u){Ht(r)&&(r=r(s||0,e,a));var f=e[t],h=i!=="get"?i:Ht(f)?c?e[t.indexOf("set")||!Ht(e["get"+t.substr(3)])?t:"get"+t.substr(3)](c):e[t]():f,d=Ht(f)?c?U2:J0:vf,m;if(ln(r)&&(~r.indexOf("random(")&&(r=Va(r)),r.charAt(1)==="="&&(m=Is(h,r)+(gn(h)||0),(m||m===0)&&(r=m))),!u||h!==r||Uh)return!isNaN(h*r)&&r!==""?(m=new Un(this._pt,e,t,+h||0,r-(h||0),typeof f=="boolean"?I2:Q0,0,d),c&&(m.fp=c),o&&m.modifier(o,this,e),this._pt=m):(!f&&!(t in e)&&hf(t,r),A2.call(this,e,t,h,r,d,l||Xn.stringFilter,c))},R2=function(e,t,i,r,s){if(Ht(e)&&(e=Oa(e,s,t,i,r)),!Li(e)||e.style&&e.nodeType||vn(e)||y0(e))return ln(e)?Oa(e,s,t,i,r):e;var a={},o;for(o in e)a[o]=Oa(e[o],s,t,i,r);return a},K0=function(e,t,i,r,s,a){var o,l,c,u;if(zn[e]&&(o=new zn[e]).init(s,o.rawVars?t[e]:R2(t[e],r,s,a,i),i,r,a)!==!1&&(i._pt=l=new Un(i._pt,s,e,0,1,o.render,o,0,o.priority),i!==Ds))for(c=i._ptLookup[i._targets.indexOf(s)],u=o._props.length;u--;)c[o._props[u]]=l;return o},pr,Uh,_f=function n(e,t,i){var r=e.vars,s=r.ease,a=r.startAt,o=r.immediateRender,l=r.lazy,c=r.onUpdate,u=r.runBackwards,f=r.yoyoEase,h=r.keyframes,d=r.autoRevert,m=e._dur,g=e._startAt,p=e._targets,_=e.parent,v=_&&_.data==="nested"?_.vars.targets:p,S=e._overwrite==="auto"&&!of,y=e.timeline,M=r.easeReverse||f,T,w,b,x,A,P,R,L,I,N,O,B,q;if(y&&(!h||!s)&&(s="none"),e._ease=jr(s,za.ease),e._rEase=M&&(jr(M)||e._ease),e._from=!y&&!!r.runBackwards,e._from&&(e.ratio=1),!y||h&&!r.stagger){if(L=p[0]?Wr(p[0]).harness:0,B=L&&r[L.prop],T=yl(r,ff),g&&(g._zTime<0&&g.progress(1),t<0&&u&&o&&!d?g.render(-1,!0):g.revert(u&&m?nl:t2),g._lazy=0),a){if(Sr(e._startAt=jt.set(p,qn({data:"isStart",overwrite:!1,parent:_,immediateRender:!0,lazy:!g&&Pn(l),startAt:null,delay:0,onUpdate:c&&function(){return Vn(e,"onUpdate")},stagger:0},a))),e._startAt._dp=0,e._startAt._sat=e,t<0&&(hn||!o&&!d)&&e._startAt.revert(nl),o&&m&&t<=0&&i<=0){t&&(e._zTime=t);return}}else if(u&&m&&!g){if(t&&(o=!1),b=qn({overwrite:!1,data:"isFromStart",lazy:o&&!g&&Pn(l),immediateRender:o,stagger:0,parent:_},T),B&&(b[L.prop]=B),Sr(e._startAt=jt.set(p,b)),e._startAt._dp=0,e._startAt._sat=e,t<0&&(hn?e._startAt.revert(nl):e._startAt.render(-1,!0)),e._zTime=t,!o)n(e._startAt,Rt,Rt);else if(!t)return}for(e._pt=e._ptCache=0,l=m&&Pn(l)||l&&!m,w=0;w<p.length;w++){if(A=p[w],R=A._gsap||pf(p)[w]._gsap,e._ptLookup[w]=N={},wh[R.id]&&vr.length&&xl(),O=v===p?w:v.indexOf(A),L&&(I=new L).init(A,B||T,e,O,v)!==!1&&(e._pt=x=new Un(e._pt,A,I.name,0,1,I.render,I,0,I.priority),I._props.forEach(function(F){N[F]=x}),I.priority&&(P=1)),!L||B)for(b in T)zn[b]&&(I=K0(b,T,e,O,A,v))?I.priority&&(P=1):N[b]=x=gf.call(e,A,b,"get",T[b],O,v,0,r.stringFilter);e._op&&e._op[w]&&e.kill(A,e._op[w]),S&&e._pt&&(pr=e,Bt.killTweensOf(A,N,e.globalTime(t)),q=!e.parent,pr=0),e._pt&&l&&(wh[R.id]=1)}P&&tg(e),e._onInit&&e._onInit(e)}e._onUpdate=c,e._initted=(!e._op||e._pt)&&!q,h&&t<=0&&y.render(ei,!0,!0)},C2=function(e,t,i,r,s,a,o,l){var c=(e._pt&&e._ptCache||(e._ptCache={}))[t],u,f,h,d;if(!c)for(c=e._ptCache[t]=[],h=e._ptLookup,d=e._targets.length;d--;){if(u=h[d][t],u&&u.d&&u.d._pt)for(u=u.d._pt;u&&u.p!==t&&u.fp!==t;)u=u._next;if(!u)return Uh=1,e.vars[t]="+=0",_f(e,o),Uh=0,l?Ga(t+" not eligible for reset. Try splitting into individual properties"):1;c.push(u)}for(d=c.length;d--;)f=c[d],u=f._pt||f,u.s=(r||r===0)&&!s?r:u.s+(r||0)+a*u.c,u.c=i-u.s,f.e&&(f.e=Wt(i)+gn(f.e)),f.b&&(f.b=u.s+gn(f.b))},P2=function(e,t){var i=e[0]?Wr(e[0]).harness:0,r=i&&i.aliases,s,a,o,l;if(!r)return t;s=Vs({},t);for(a in r)if(a in s)for(l=r[a].split(","),o=l.length;o--;)s[l[o]]=s[a];return s},D2=function(e,t,i,r){var s=t.ease||r||"power1.inOut",a,o;if(vn(t))o=i[e]||(i[e]=[]),t.forEach(function(l,c){return o.push({t:c/(t.length-1)*100,v:l,e:s})});else for(a in t)o=i[a]||(i[a]=[]),a==="ease"||o.push({t:parseFloat(e),v:t[a],e:s})},Oa=function(e,t,i,r,s){return Ht(e)?e.call(t,i,r,s):ln(e)&&~e.indexOf("random(")?Va(e):e},Z0=df+"repeat,repeatDelay,yoyo,repeatRefresh,yoyoEase,easeReverse,autoRevert",$0={};Dn(Z0+",id,stagger,delay,duration,paused,scrollTrigger",function(n){return $0[n]=1});var jt=(function(n){v0(e,n);function e(i,r,s,a){var o;typeof r=="number"&&(s.duration=r,r=s,s=null),o=n.call(this,a?r:Fa(r))||this;var l=o.vars,c=l.duration,u=l.delay,f=l.immediateRender,h=l.stagger,d=l.overwrite,m=l.keyframes,g=l.defaults,p=l.scrollTrigger,_=r.parent||Bt,v=(vn(i)||y0(i)?Ki(i[0]):"length"in r)?[i]:ti(i),S,y,M,T,w,b,x,A;if(o._targets=v.length?pf(v):Ga("GSAP target "+i+" not found. https://gsap.com",!Xn.nullTargetWarn)||[],o._ptLookup=[],o._overwrite=d,m||h||Go(c)||Go(u)){r=o.vars;var P=r.easeReverse||r.yoyoEase;if(S=o.timeline=new Cn({data:"nested",defaults:g||{},targets:_&&_.data==="nested"?_.vars.targets:v}),S.kill(),S.parent=S._dp=Gi(o),S._start=0,h||Go(c)||Go(u)){if(T=v.length,x=h&&O0(h),Li(h))for(w in h)~Z0.indexOf(w)&&(A||(A={}),A[w]=h[w]);for(y=0;y<T;y++)M=yl(r,$0),M.stagger=0,P&&(M.easeReverse=P),A&&Vs(M,A),b=v[y],M.duration=+Oa(c,Gi(o),y,b,v),M.delay=(+Oa(u,Gi(o),y,b,v)||0)-o._delay,!h&&T===1&&M.delay&&(o._delay=u=M.delay,o._start+=u,M.delay=0),S.to(b,M,x?x(y,b,v):0),S._ease=dt.none;S.duration()?c=u=0:o.timeline=0}else if(m){Fa(qn(S.vars.defaults,{ease:"none"})),S._ease=jr(m.ease||r.ease||"none");var R=0,L,I,N;if(vn(m))m.forEach(function(O){return S.to(v,O,">")}),S.duration();else{M={};for(w in m)w==="ease"||w==="easeEach"||D2(w,m[w],M,m.easeEach);for(w in M)for(L=M[w].sort(function(O,B){return O.t-B.t}),R=0,y=0;y<L.length;y++)I=L[y],N={ease:I.e,duration:(I.t-(y?L[y-1].t:0))/100*c},N[w]=I.v,S.to(v,N,R),R+=N.duration;S.duration()<c&&S.to({},{duration:c-S.duration()})}}c||o.duration(c=S.duration())}else o.timeline=0;return d===!0&&!of&&(pr=Gi(o),Bt.killTweensOf(v),pr=0),wi(_,Gi(o),s),r.reversed&&o.reverse(),r.paused&&o.paused(!0),(f||!c&&!m&&o._start===Ot(_._time)&&Pn(f)&&o2(Gi(o))&&_.data!=="nested")&&(o._tTime=-Rt,o.render(Math.max(0,-u)||0)),p&&L0(Gi(o),p),o}var t=e.prototype;return t.render=function(r,s,a){var o=this._time,l=this._tDur,c=this._dur,u=r<0,f=r>l-Rt&&!u?l:r<Rt?0:r,h,d,m,g,p,_,v,S;if(!c)c2(this,r,s,a);else if(f!==this._tTime||!r||a||!this._initted&&this._tTime||this._startAt&&this._zTime<0!==u||this._lazy){if(h=f,S=this.timeline,this._repeat){if(g=c+this._rDelay,this._repeat<-1&&u)return this.totalTime(g*100+r,s,a);if(h=Ot(f%g),f===l?(m=this._repeat,h=c):(p=Ot(f/g),m=~~p,m&&m===p?(h=c,m--):h>c&&(h=c)),_=this._yoyo&&m&1,_&&(h=c-h),p=Ws(this._tTime,g),h===o&&!a&&this._initted&&m===p)return this._tTime=f,this;m!==p&&this.vars.repeatRefresh&&!_&&!this._lock&&h!==g&&this._initted&&(this._lock=a=1,this.render(Ot(g*m),!0).invalidate()._lock=0)}if(!this._initted){if(I0(this,u?r:h,a,s,f))return this._tTime=0,this;if(o!==this._time&&!(a&&this.vars.repeatRefresh&&m!==p))return this;if(c!==this._dur)return this.render(r,s,a)}if(this._rEase){var y=h<o;if(y!==this._inv){var M=y?o:c-o;this._inv=y,this._from&&(this.ratio=1-this.ratio),this._invRatio=this.ratio,this._invTime=o,this._invRecip=M?(y?-1:1)/M:0,this._invScale=y?-this.ratio:1-this.ratio,this._invEase=y?this._rEase:this._ease}this.ratio=v=this._invRatio+this._invScale*this._invEase((h-this._invTime)*this._invRecip)}else this.ratio=v=this._ease(h/c);if(this._from&&(this.ratio=v=1-v),this._tTime=f,this._time=h,!this._act&&this._ts&&(this._act=1,this._lazy=0),!o&&f&&!s&&!p&&(Vn(this,"onStart"),this._tTime!==f))return this;for(d=this._pt;d;)d.r(v,d.d),d=d._next;S&&S.render(r<0?r:S._dur*S._ease(h/this._dur),s,a)||this._startAt&&(this._zTime=r),this._onUpdate&&!s&&(u&&Ah(this,r,s,a),Vn(this,"onUpdate")),this._repeat&&m!==p&&this.vars.onRepeat&&!s&&this.parent&&Vn(this,"onRepeat"),(f===this._tDur||!f)&&this._tTime===f&&(u&&!this._onUpdate&&Ah(this,r,!0,!0),(r||!c)&&(f===this._tDur&&this._ts>0||!f&&this._ts<0)&&Sr(this,1),!s&&!(u&&!o)&&(f||o||_)&&(Vn(this,f===l?"onComplete":"onReverseComplete",!0),this._prom&&!(f<l&&this.timeScale()>0)&&this._prom()))}return this},t.targets=function(){return this._targets},t.invalidate=function(r){return(!r||!this.vars.runBackwards)&&(this._startAt=0),this._pt=this._op=this._onUpdate=this._lazy=this.ratio=0,this._ptLookup=[],this.timeline&&this.timeline.invalidate(r),n.prototype.invalidate.call(this,r)},t.resetTo=function(r,s,a,o,l){Wa||Hn.wake(),this._ts||this.play();var c=Math.min(this._dur,(this._dp._time-this._start)*this._ts),u;return this._initted||_f(this,c),u=this._ease(c/this._dur),C2(this,r,s,a,o,u,c,l)?this.resetTo(r,s,a,o,1):(kl(this,0),this.parent||D0(this._dp,this,"_first","_last",this._dp._sort?"_start":0),this.render(0))},t.kill=function(r,s){if(s===void 0&&(s="all"),!r&&(!s||s==="all"))return this._lazy=this._pt=0,this.parent?Pa(this):this.scrollTrigger&&this.scrollTrigger.kill(!!hn),this;if(this.timeline){var a=this.timeline.totalDuration();return this.timeline.killTweensOf(r,s,pr&&pr.vars.overwrite!==!0)._first||Pa(this),this.parent&&a!==this.timeline.totalDuration()&&Xs(this,this._dur*this.timeline._tDur/a,0,1),this}var o=this._targets,l=r?ti(r):o,c=this._ptLookup,u=this._pt,f,h,d,m,g,p,_;if((!s||s==="all")&&s2(o,l))return s==="all"&&(this._pt=0),Pa(this);for(f=this._op=this._op||[],s!=="all"&&(ln(s)&&(g={},Dn(s,function(v){return g[v]=1}),s=g),s=P2(o,s)),_=o.length;_--;)if(~l.indexOf(o[_])){h=c[_],s==="all"?(f[_]=s,m=h,d={}):(d=f[_]=f[_]||{},m=s);for(g in m)p=h&&h[g],p&&((!("kill"in p.d)||p.d.kill(g)===!0)&&Ol(this,p,"_pt"),delete h[g]),d!=="all"&&(d[g]=1)}return this._initted&&!this._pt&&u&&Pa(this),this},e.to=function(r,s){return new e(r,s,arguments[2])},e.from=function(r,s){return Na(1,arguments)},e.delayedCall=function(r,s,a,o){return new e(s,0,{immediateRender:!1,lazy:!1,overwrite:!1,delay:r,onComplete:s,onReverseComplete:s,onCompleteParams:a,onReverseCompleteParams:a,callbackScope:o})},e.fromTo=function(r,s,a){return Na(2,arguments)},e.set=function(r,s){return s.duration=0,s.repeatDelay||(s.repeat=0),new e(r,s)},e.killTweensOf=function(r,s,a){return Bt.killTweensOf(r,s,a)},e})(Xa);qn(jt.prototype,{_targets:[],_lazy:0,_startAt:0,_op:0,_onInit:0});Dn("staggerTo,staggerFrom,staggerFromTo",function(n){jt[n]=function(){var e=new Cn,t=Ch.call(arguments,0);return t.splice(n==="staggerFromTo"?5:4,0,0),e[n].apply(e,t)}});var vf=function(e,t,i){return e[t]=i},J0=function(e,t,i){return e[t](i)},U2=function(e,t,i,r){return e[t](r.fp,i)},L2=function(e,t,i){return e.setAttribute(t,i)},xf=function(e,t){return Ht(e[t])?J0:lf(e[t])&&e.setAttribute?L2:vf},Q0=function(e,t){return t.set(t.t,t.p,Math.round((t.s+t.c*e)*1e6)/1e6,t)},I2=function(e,t){return t.set(t.t,t.p,!!(t.s+t.c*e),t)},eg=function(e,t){var i=t._pt,r="";if(!e&&t.b)r=t.b;else if(e===1&&t.e)r=t.e;else{for(;i;)r=i.p+(i.m?i.m(i.s+i.c*e):Math.round((i.s+i.c*e)*1e4)/1e4)+r,i=i._next;r+=t.c}t.set(t.t,t.p,r,t)},yf=function(e,t){for(var i=t._pt;i;)i.r(e,i.d),i=i._next},F2=function(e,t,i,r){for(var s=this._pt,a;s;)a=s._next,s.p===r&&s.modifier(e,t,i),s=a},N2=function(e){for(var t=this._pt,i,r;t;)r=t._next,t.p===e&&!t.op||t.op===e?Ol(this,t,"_pt"):t.dep||(i=1),t=r;return!i},O2=function(e,t,i,r){r.mSet(e,t,r.m.call(r.tween,i,r.mt),r)},tg=function(e){for(var t=e._pt,i,r,s,a;t;){for(i=t._next,r=s;r&&r.pr>t.pr;)r=r._next;(t._prev=r?r._prev:a)?t._prev._next=t:s=t,(t._next=r)?r._prev=t:a=t,t=i}e._pt=s},Un=(function(){function n(t,i,r,s,a,o,l,c,u){this.t=i,this.s=s,this.c=a,this.p=r,this.r=o||Q0,this.d=l||this,this.set=c||vf,this.pr=u||0,this._next=t,t&&(t._prev=this)}var e=n.prototype;return e.modifier=function(i,r,s){this.mSet=this.mSet||this.set,this.set=O2,this.m=i,this.mt=s,this.tween=r},n})();Dn(df+"parent,duration,ease,delay,overwrite,runBackwards,startAt,yoyo,immediateRender,repeat,repeatDelay,data,paused,reversed,lazy,callbackScope,stringFilter,id,yoyoEase,stagger,inherit,repeatRefresh,keyframes,autoRevert,scrollTrigger,easeReverse",function(n){return ff[n]=1});Yn.TweenMax=Yn.TweenLite=jt;Yn.TimelineLite=Yn.TimelineMax=Cn;Bt=new Cn({sortChildren:!1,defaults:za,autoRemoveChildren:!0,id:"root",smoothChildTiming:!0});Xn.stringFilter=j0;var Yr=[],rl={},B2=[],Dp=0,k2=0,Kc=function(e){return(rl[e]||B2).map(function(t){return t()})},Lh=function(){var e=Date.now(),t=[];e-Dp>2&&(Kc("matchMediaInit"),Yr.forEach(function(i){var r=i.queries,s=i.conditions,a,o,l,c;for(o in r)a=Si.matchMedia(r[o]).matches,a&&(l=1),a!==s[o]&&(s[o]=a,c=1);c&&(i.revert(),l&&t.push(i))}),Kc("matchMediaRevert"),t.forEach(function(i){return i.onMatch(i,function(r){return i.add(null,r)})}),Dp=e,Kc("matchMedia"))},ng=(function(){function n(t,i){this.selector=i&&Ph(i),this.data=[],this._r=[],this.isReverted=!1,this.id=k2++,t&&this.add(t)}var e=n.prototype;return e.add=function(i,r,s){Ht(i)&&(s=r,r=i,i=Ht);var a=this,o=function(){var c=It,u=a.selector,f;return c&&c!==a&&c.data.push(a),s&&(a.selector=Ph(s)),It=a,f=r.apply(a,arguments),Ht(f)&&a._r.push(f),It=c,a.selector=u,a.isReverted=!1,f};return a.last=o,i===Ht?o(a,function(l){return a.add(null,l)}):i?a[i]=o:o},e.ignore=function(i){var r=It;It=null,i(this),It=r},e.getTweens=function(){var i=[];return this.data.forEach(function(r){return r instanceof n?i.push.apply(i,r.getTweens()):r instanceof jt&&!(r.parent&&r.parent.data==="nested")&&i.push(r)}),i},e.clear=function(){this._r.length=this.data.length=0},e.kill=function(i,r){var s=this;if(i?(function(){for(var o=s.getTweens(),l=s.data.length,c;l--;)c=s.data[l],c.data==="isFlip"&&(c.revert(),c.getChildren(!0,!0,!1).forEach(function(u){return o.splice(o.indexOf(u),1)}));for(o.map(function(u){return{g:u._dur||u._delay||u._sat&&!u._sat.vars.immediateRender?u.globalTime(0):-1/0,t:u}}).sort(function(u,f){return f.g-u.g||-1/0}).forEach(function(u){return u.t.revert(i)}),l=s.data.length;l--;)c=s.data[l],c instanceof Cn?c.data!=="nested"&&(c.scrollTrigger&&c.scrollTrigger.revert(),c.kill()):!(c instanceof jt)&&c.revert&&c.revert(i);s._r.forEach(function(u){return u(i,s)}),s.isReverted=!0})():this.data.forEach(function(o){return o.kill&&o.kill()}),this.clear(),r)for(var a=Yr.length;a--;)Yr[a].id===this.id&&Yr.splice(a,1)},e.revert=function(i){this.kill(i||{})},n})(),z2=(function(){function n(t){this.contexts=[],this.scope=t,It&&It.data.push(this)}var e=n.prototype;return e.add=function(i,r,s){Li(i)||(i={matches:i});var a=new ng(0,s||this.scope),o=a.conditions={},l,c,u;It&&!a.selector&&(a.selector=It.selector),this.contexts.push(a),r=a.add("onMatch",r),a.queries=i;for(c in i)c==="all"?u=1:(l=Si.matchMedia(i[c]),l&&(Yr.indexOf(a)<0&&Yr.push(a),(o[c]=l.matches)&&(u=1),l.addListener?l.addListener(Lh):l.addEventListener("change",Lh)));return u&&r(a,function(f){return a.add(null,f)}),this},e.revert=function(i){this.kill(i||{})},e.kill=function(i){this.contexts.forEach(function(r){return r.kill(i,!0)})},n})(),Sl={registerPlugin:function(){for(var e=arguments.length,t=new Array(e),i=0;i<e;i++)t[i]=arguments[i];t.forEach(function(r){return V0(r)})},timeline:function(e){return new Cn(e)},getTweensOf:function(e,t){return Bt.getTweensOf(e,t)},getProperty:function(e,t,i,r){ln(e)&&(e=ti(e)[0]);var s=Wr(e||{}).get,a=i?P0:C0;return i==="native"&&(i=""),e&&(t?a((zn[t]&&zn[t].get||s)(e,t,i,r)):function(o,l,c){return a((zn[o]&&zn[o].get||s)(e,o,l,c))})},quickSetter:function(e,t,i){if(e=ti(e),e.length>1){var r=e.map(function(u){return In.quickSetter(u,t,i)}),s=r.length;return function(u){for(var f=s;f--;)r[f](u)}}e=e[0]||{};var a=zn[t],o=Wr(e),l=o.harness&&(o.harness.aliases||{})[t]||t,c=a?function(u){var f=new a;Ds._pt=0,f.init(e,i?u+i:u,Ds,0,[e]),f.render(1,f),Ds._pt&&yf(1,Ds)}:o.set(e,l);return a?c:function(u){return c(e,l,i?u+i:u,o,1)}},quickTo:function(e,t,i){var r,s=In.to(e,qn((r={},r[t]="+=0.1",r.paused=!0,r.stagger=0,r),i||{})),a=function(l,c,u){return s.resetTo(t,l,c,u)};return a.tween=s,a},isTweening:function(e){return Bt.getTweensOf(e,!0).length>0},defaults:function(e){return e&&e.ease&&(e.ease=jr(e.ease,za.ease)),wp(za,e||{})},config:function(e){return wp(Xn,e||{})},registerEffect:function(e){var t=e.name,i=e.effect,r=e.plugins,s=e.defaults,a=e.extendTimeline;(r||"").split(",").forEach(function(o){return o&&!zn[o]&&!Yn[o]&&Ga(t+" effect requires "+o+" plugin.")}),Xc[t]=function(o,l,c){return i(ti(o),qn(l||{},s),c)},a&&(Cn.prototype[t]=function(o,l,c){return this.add(Xc[t](o,Li(l)?l:(c=l)&&{},this),c)})},registerEase:function(e,t){dt[e]=jr(t)},parseEase:function(e,t){return arguments.length?jr(e,t):dt},getById:function(e){return Bt.getById(e)},exportRoot:function(e,t){e===void 0&&(e={});var i=new Cn(e),r,s;for(i.smoothChildTiming=Pn(e.smoothChildTiming),Bt.remove(i),i._dp=0,i._time=i._tTime=Bt._time,r=Bt._first;r;)s=r._next,(t||!(!r._dur&&r instanceof jt&&r.vars.onComplete===r._targets[0]))&&wi(i,r,r._start-r._delay),r=s;return wi(Bt,i,0),i},context:function(e,t){return e?new ng(e,t):It},matchMedia:function(e){return new z2(e)},matchMediaRefresh:function(){return Yr.forEach(function(e){var t=e.conditions,i,r;for(r in t)t[r]&&(t[r]=!1,i=1);i&&e.revert()})||Lh()},addEventListener:function(e,t){var i=rl[e]||(rl[e]=[]);~i.indexOf(t)||i.push(t)},removeEventListener:function(e,t){var i=rl[e],r=i&&i.indexOf(t);r>=0&&i.splice(r,1)},utils:{wrap:_2,wrapYoyo:v2,distribute:O0,random:k0,snap:B0,normalize:g2,getUnit:gn,clamp:f2,splitColor:W0,toArray:ti,selector:Ph,mapRange:G0,pipe:p2,unitize:m2,interpolate:x2,shuffle:N0},install:T0,effects:Xc,ticker:Hn,updateRoot:Cn.updateRoot,plugins:zn,globalTimeline:Bt,core:{PropTween:Un,globals:E0,Tween:jt,Timeline:Cn,Animation:Xa,getCache:Wr,_removeLinkedListItem:Ol,reverting:function(){return hn},context:function(e){return e&&It&&(It.data.push(e),e._ctx=It),It},suppressOverwrites:function(e){return of=e}}};Dn("to,from,fromTo,delayedCall,set,killTweensOf",function(n){return Sl[n]=jt[n]});Hn.add(Cn.updateRoot);Ds=Sl.to({},{duration:0});var G2=function(e,t){for(var i=e._pt;i&&i.p!==t&&i.op!==t&&i.fp!==t;)i=i._next;return i},H2=function(e,t){var i=e._targets,r,s,a;for(r in t)for(s=i.length;s--;)a=e._ptLookup[s][r],a&&(a=a.d)&&(a._pt&&(a=G2(a,r)),a&&a.modifier&&a.modifier(t[r],e,i[s],r))},Zc=function(e,t){return{name:e,headless:1,rawVars:1,init:function(r,s,a){a._onInit=function(o){var l,c;if(ln(s)&&(l={},Dn(s,function(u){return l[u]=1}),s=l),t){l={};for(c in s)l[c]=t(s[c]);s=l}H2(o,s)}}}},In=Sl.registerPlugin({name:"attr",init:function(e,t,i,r,s){var a,o,l;this.tween=i;for(a in t)l=e.getAttribute(a)||"",o=this.add(e,"setAttribute",(l||0)+"",t[a],r,s,0,0,a),o.op=a,o.b=l,this._props.push(a)},render:function(e,t){for(var i=t._pt;i;)hn?i.set(i.t,i.p,i.b,i):i.r(e,i.d),i=i._next}},{name:"endArray",headless:1,init:function(e,t){for(var i=t.length;i--;)this.add(e,i,e[i]||0,t[i],0,0,0,0,0,1)}},Zc("roundProps",Dh),Zc("modifiers"),Zc("snap",B0))||Sl;jt.version=Cn.version=In.version="3.15.0";M0=1;cf()&&js();dt.Power0;dt.Power1;dt.Power2;dt.Power3;dt.Power4;dt.Linear;dt.Quad;dt.Cubic;dt.Quart;dt.Quint;dt.Strong;dt.Elastic;dt.Back;dt.SteppedEase;dt.Bounce;dt.Sine;dt.Expo;dt.Circ;/*!
 * CSSPlugin 3.15.0
 * https://gsap.com
 *
 * Copyright 2008-2026, GreenSock. All rights reserved.
 * Subject to the terms at https://gsap.com/standard-license
 * @author: Jack Doyle, jack@greensock.com
*/var Up,mr,Fs,bf,Gr,Lp,Sf,V2=function(){return typeof window<"u"},Zi={},Or=180/Math.PI,Ns=Math.PI/180,As=Math.atan2,Ip=1e8,Mf=/([A-Z])/g,W2=/(left|right|width|margin|padding|x)/i,X2=/[\s,\(]\S/,Ci={autoAlpha:"opacity,visibility",scale:"scaleX,scaleY",alpha:"opacity"},Ih=function(e,t){return t.set(t.t,t.p,Math.round((t.s+t.c*e)*1e4)/1e4+t.u,t)},j2=function(e,t){return t.set(t.t,t.p,e===1?t.e:Math.round((t.s+t.c*e)*1e4)/1e4+t.u,t)},Y2=function(e,t){return t.set(t.t,t.p,e?Math.round((t.s+t.c*e)*1e4)/1e4+t.u:t.b,t)},q2=function(e,t){return t.set(t.t,t.p,e===1?t.e:e?Math.round((t.s+t.c*e)*1e4)/1e4+t.u:t.b,t)},K2=function(e,t){var i=t.s+t.c*e;t.set(t.t,t.p,~~(i+(i<0?-.5:.5))+t.u,t)},ig=function(e,t){return t.set(t.t,t.p,e?t.e:t.b,t)},rg=function(e,t){return t.set(t.t,t.p,e!==1?t.b:t.e,t)},Z2=function(e,t,i){return e.style[t]=i},$2=function(e,t,i){return e.style.setProperty(t,i)},J2=function(e,t,i){return e._gsap[t]=i},Q2=function(e,t,i){return e._gsap.scaleX=e._gsap.scaleY=i},eT=function(e,t,i,r,s){var a=e._gsap;a.scaleX=a.scaleY=i,a.renderTransform(s,a)},tT=function(e,t,i,r,s){var a=e._gsap;a[t]=i,a.renderTransform(s,a)},kt="transform",Ln=kt+"Origin",nT=function n(e,t){var i=this,r=this.target,s=r.style,a=r._gsap;if(e in Zi&&s){if(this.tfm=this.tfm||{},e!=="transform")e=Ci[e]||e,~e.indexOf(",")?e.split(",").forEach(function(o){return i.tfm[o]=Hi(r,o)}):this.tfm[e]=a.x?a[e]:Hi(r,e),e===Ln&&(this.tfm.zOrigin=a.zOrigin);else return Ci.transform.split(",").forEach(function(o){return n.call(i,o,t)});if(this.props.indexOf(kt)>=0)return;a.svg&&(this.svgo=r.getAttribute("data-svg-origin"),this.props.push(Ln,t,"")),e=kt}(s||t)&&this.props.push(e,t,s[e])},sg=function(e){e.translate&&(e.removeProperty("translate"),e.removeProperty("scale"),e.removeProperty("rotate"))},iT=function(){var e=this.props,t=this.target,i=t.style,r=t._gsap,s,a;for(s=0;s<e.length;s+=3)e[s+1]?e[s+1]===2?t[e[s]](e[s+2]):t[e[s]]=e[s+2]:e[s+2]?i[e[s]]=e[s+2]:i.removeProperty(e[s].substr(0,2)==="--"?e[s]:e[s].replace(Mf,"-$1").toLowerCase());if(this.tfm){for(a in this.tfm)r[a]=this.tfm[a];r.svg&&(r.renderTransform(),t.setAttribute("data-svg-origin",this.svgo||"")),s=Sf(),(!s||!s.isStart)&&!i[kt]&&(sg(i),r.zOrigin&&i[Ln]&&(i[Ln]+=" "+r.zOrigin+"px",r.zOrigin=0,r.renderTransform()),r.uncache=1)}},ag=function(e,t){var i={target:e,props:[],revert:iT,save:nT};return e._gsap||In.core.getCache(e),t&&e.style&&e.nodeType&&t.split(",").forEach(function(r){return i.save(r)}),i},og,Fh=function(e,t){var i=mr.createElementNS?mr.createElementNS((t||"http://www.w3.org/1999/xhtml").replace(/^https/,"http"),e):mr.createElement(e);return i&&i.style?i:mr.createElement(e)},Wn=function n(e,t,i){var r=getComputedStyle(e);return r[t]||r.getPropertyValue(t.replace(Mf,"-$1").toLowerCase())||r.getPropertyValue(t)||!i&&n(e,Ys(t)||t,1)||""},Fp="O,Moz,ms,Ms,Webkit".split(","),Ys=function(e,t,i){var r=t||Gr,s=r.style,a=5;if(e in s&&!i)return e;for(e=e.charAt(0).toUpperCase()+e.substr(1);a--&&!(Fp[a]+e in s););return a<0?null:(a===3?"ms":a>=0?Fp[a]:"")+e},Nh=function(){V2()&&window.document&&(Up=window,mr=Up.document,Fs=mr.documentElement,Gr=Fh("div")||{style:{}},Fh("div"),kt=Ys(kt),Ln=kt+"Origin",Gr.style.cssText="border-width:0;line-height:0;position:absolute;padding:0",og=!!Ys("perspective"),Sf=In.core.reverting,bf=1)},Np=function(e){var t=e.ownerSVGElement,i=Fh("svg",t&&t.getAttribute("xmlns")||"http://www.w3.org/2000/svg"),r=e.cloneNode(!0),s;r.style.display="block",i.appendChild(r),Fs.appendChild(i);try{s=r.getBBox()}catch{}return i.removeChild(r),Fs.removeChild(i),s},Op=function(e,t){for(var i=t.length;i--;)if(e.hasAttribute(t[i]))return e.getAttribute(t[i])},lg=function(e){var t,i;try{t=e.getBBox()}catch{t=Np(e),i=1}return t&&(t.width||t.height)||i||(t=Np(e)),t&&!t.width&&!t.x&&!t.y?{x:+Op(e,["x","cx","x1"])||0,y:+Op(e,["y","cy","y1"])||0,width:0,height:0}:t},cg=function(e){return!!(e.getCTM&&(!e.parentNode||e.ownerSVGElement)&&lg(e))},Mr=function(e,t){if(t){var i=e.style,r;t in Zi&&t!==Ln&&(t=kt),i.removeProperty?(r=t.substr(0,2),(r==="ms"||t.substr(0,6)==="webkit")&&(t="-"+t),i.removeProperty(r==="--"?t:t.replace(Mf,"-$1").toLowerCase())):i.removeAttribute(t)}},gr=function(e,t,i,r,s,a){var o=new Un(e._pt,t,i,0,1,a?rg:ig);return e._pt=o,o.b=r,o.e=s,e._props.push(i),o},Bp={deg:1,rad:1,turn:1},rT={grid:1,flex:1},Tr=function n(e,t,i,r){var s=parseFloat(i)||0,a=(i+"").trim().substr((s+"").length)||"px",o=Gr.style,l=W2.test(t),c=e.tagName.toLowerCase()==="svg",u=(c?"client":"offset")+(l?"Width":"Height"),f=100,h=r==="px",d=r==="%",m,g,p,_;if(r===a||!s||Bp[r]||Bp[a])return s;if(a!=="px"&&!h&&(s=n(e,t,i,"px")),_=e.getCTM&&cg(e),(d||a==="%")&&(Zi[t]||~t.indexOf("adius")))return m=_?e.getBBox()[l?"width":"height"]:e[u],Wt(d?s/m*f:s/100*m);if(o[l?"width":"height"]=f+(h?a:r),g=r!=="rem"&&~t.indexOf("adius")||r==="em"&&e.appendChild&&!c?e:e.parentNode,_&&(g=(e.ownerSVGElement||{}).parentNode),(!g||g===mr||!g.appendChild)&&(g=mr.body),p=g._gsap,p&&d&&p.width&&l&&p.time===Hn.time&&!p.uncache)return Wt(s/p.width*f);if(d&&(t==="height"||t==="width")){var v=e.style[t];e.style[t]=f+r,m=e[u],v?e.style[t]=v:Mr(e,t)}else(d||a==="%")&&!rT[Wn(g,"display")]&&(o.position=Wn(e,"position")),g===e&&(o.position="static"),g.appendChild(Gr),m=Gr[u],g.removeChild(Gr),o.position="absolute";return l&&d&&(p=Wr(g),p.time=Hn.time,p.width=g[u]),Wt(h?m*s/f:m&&s?f/m*s:0)},Hi=function(e,t,i,r){var s;return bf||Nh(),t in Ci&&t!=="transform"&&(t=Ci[t],~t.indexOf(",")&&(t=t.split(",")[0])),Zi[t]&&t!=="transform"?(s=Ya(e,r),s=t!=="transformOrigin"?s[t]:s.svg?s.origin:Tl(Wn(e,Ln))+" "+s.zOrigin+"px"):(s=e.style[t],(!s||s==="auto"||r||~(s+"").indexOf("calc("))&&(s=Ml[t]&&Ml[t](e,t,i)||Wn(e,t)||A0(e,t)||(t==="opacity"?1:0))),i&&!~(s+"").trim().indexOf(" ")?Tr(e,t,s,i)+i:s},sT=function(e,t,i,r){if(!i||i==="none"){var s=Ys(t,e,1),a=s&&Wn(e,s,1);a&&a!==i?(t=s,i=a):t==="borderColor"&&(i=Wn(e,"borderTopColor"))}var o=new Un(this._pt,e.style,t,0,1,eg),l=0,c=0,u,f,h,d,m,g,p,_,v,S,y,M;if(o.b=i,o.e=r,i+="",r+="",r.substring(0,6)==="var(--"&&(r=Wn(e,r.substring(4,r.indexOf(")")))),r==="auto"&&(g=e.style[t],e.style[t]=r,r=Wn(e,t)||r,g?e.style[t]=g:Mr(e,t)),u=[i,r],j0(u),i=u[0],r=u[1],h=i.match(Ps)||[],M=r.match(Ps)||[],M.length){for(;f=Ps.exec(r);)p=f[0],v=r.substring(l,f.index),m?m=(m+1)%5:(v.substr(-5)==="rgba("||v.substr(-5)==="hsla(")&&(m=1),p!==(g=h[c++]||"")&&(d=parseFloat(g)||0,y=g.substr((d+"").length),p.charAt(1)==="="&&(p=Is(d,p)+y),_=parseFloat(p),S=p.substr((_+"").length),l=Ps.lastIndex-S.length,S||(S=S||Xn.units[t]||y,l===r.length&&(r+=S,o.e+=S)),y!==S&&(d=Tr(e,t,g,S)||0),o._pt={_next:o._pt,p:v||c===1?v:",",s:d,c:_-d,m:m&&m<4||t==="zIndex"?Math.round:0});o.c=l<r.length?r.substring(l,r.length):""}else o.r=t==="display"&&r==="none"?rg:ig;return S0.test(r)&&(o.e=0),this._pt=o,o},kp={top:"0%",bottom:"100%",left:"0%",right:"100%",center:"50%"},aT=function(e){var t=e.split(" "),i=t[0],r=t[1]||"50%";return(i==="top"||i==="bottom"||r==="left"||r==="right")&&(e=i,i=r,r=e),t[0]=kp[i]||i,t[1]=kp[r]||r,t.join(" ")},oT=function(e,t){if(t.tween&&t.tween._time===t.tween._dur){var i=t.t,r=i.style,s=t.u,a=i._gsap,o,l,c;if(s==="all"||s===!0)r.cssText="",l=1;else for(s=s.split(","),c=s.length;--c>-1;)o=s[c],Zi[o]&&(l=1,o=o==="transformOrigin"?Ln:kt),Mr(i,o);l&&(Mr(i,kt),a&&(a.svg&&i.removeAttribute("transform"),r.scale=r.rotate=r.translate="none",Ya(i,1),a.uncache=1,sg(r)))}},Ml={clearProps:function(e,t,i,r,s){if(s.data!=="isFromStart"){var a=e._pt=new Un(e._pt,t,i,0,0,oT);return a.u=r,a.pr=-10,a.tween=s,e._props.push(i),1}}},ja=[1,0,0,1,0,0],ug={},hg=function(e){return e==="matrix(1, 0, 0, 1, 0, 0)"||e==="none"||!e},zp=function(e){var t=Wn(e,kt);return hg(t)?ja:t.substr(7).match(b0).map(Wt)},Tf=function(e,t){var i=e._gsap||Wr(e),r=e.style,s=zp(e),a,o,l,c;return i.svg&&e.getAttribute("transform")?(l=e.transform.baseVal.consolidate().matrix,s=[l.a,l.b,l.c,l.d,l.e,l.f],s.join(",")==="1,0,0,1,0,0"?ja:s):(s===ja&&!e.offsetParent&&e!==Fs&&!i.svg&&(l=r.display,r.display="block",a=e.parentNode,(!a||!e.offsetParent&&!e.getBoundingClientRect().width)&&(c=1,o=e.nextElementSibling,Fs.appendChild(e)),s=zp(e),l?r.display=l:Mr(e,"display"),c&&(o?a.insertBefore(e,o):a?a.appendChild(e):Fs.removeChild(e))),t&&s.length>6?[s[0],s[1],s[4],s[5],s[12],s[13]]:s)},Oh=function(e,t,i,r,s,a){var o=e._gsap,l=s||Tf(e,!0),c=o.xOrigin||0,u=o.yOrigin||0,f=o.xOffset||0,h=o.yOffset||0,d=l[0],m=l[1],g=l[2],p=l[3],_=l[4],v=l[5],S=t.split(" "),y=parseFloat(S[0])||0,M=parseFloat(S[1])||0,T,w,b,x;i?l!==ja&&(w=d*p-m*g)&&(b=y*(p/w)+M*(-g/w)+(g*v-p*_)/w,x=y*(-m/w)+M*(d/w)-(d*v-m*_)/w,y=b,M=x):(T=lg(e),y=T.x+(~S[0].indexOf("%")?y/100*T.width:y),M=T.y+(~(S[1]||S[0]).indexOf("%")?M/100*T.height:M)),r||r!==!1&&o.smooth?(_=y-c,v=M-u,o.xOffset=f+(_*d+v*g)-_,o.yOffset=h+(_*m+v*p)-v):o.xOffset=o.yOffset=0,o.xOrigin=y,o.yOrigin=M,o.smooth=!!r,o.origin=t,o.originIsAbsolute=!!i,e.style[Ln]="0px 0px",a&&(gr(a,o,"xOrigin",c,y),gr(a,o,"yOrigin",u,M),gr(a,o,"xOffset",f,o.xOffset),gr(a,o,"yOffset",h,o.yOffset)),e.setAttribute("data-svg-origin",y+" "+M)},Ya=function(e,t){var i=e._gsap||new q0(e);if("x"in i&&!t&&!i.uncache)return i;var r=e.style,s=i.scaleX<0,a="px",o="deg",l=getComputedStyle(e),c=Wn(e,Ln)||"0",u,f,h,d,m,g,p,_,v,S,y,M,T,w,b,x,A,P,R,L,I,N,O,B,q,F,k,U,z,K,Z,X;return u=f=h=g=p=_=v=S=y=0,d=m=1,i.svg=!!(e.getCTM&&cg(e)),l.translate&&((l.translate!=="none"||l.scale!=="none"||l.rotate!=="none")&&(r[kt]=(l.translate!=="none"?"translate3d("+(l.translate+" 0 0").split(" ").slice(0,3).join(", ")+") ":"")+(l.rotate!=="none"?"rotate("+l.rotate+") ":"")+(l.scale!=="none"?"scale("+l.scale.split(" ").join(",")+") ":"")+(l[kt]!=="none"?l[kt]:"")),r.scale=r.rotate=r.translate="none"),w=Tf(e,i.svg),i.svg&&(i.uncache?(q=e.getBBox(),c=i.xOrigin-q.x+"px "+(i.yOrigin-q.y)+"px",B=""):B=!t&&e.getAttribute("data-svg-origin"),Oh(e,B||c,!!B||i.originIsAbsolute,i.smooth!==!1,w)),M=i.xOrigin||0,T=i.yOrigin||0,w!==ja&&(P=w[0],R=w[1],L=w[2],I=w[3],u=N=w[4],f=O=w[5],w.length===6?(d=Math.sqrt(P*P+R*R),m=Math.sqrt(I*I+L*L),g=P||R?As(R,P)*Or:0,v=L||I?As(L,I)*Or+g:0,v&&(m*=Math.abs(Math.cos(v*Ns))),i.svg&&(u-=M-(M*P+T*L),f-=T-(M*R+T*I))):(X=w[6],K=w[7],k=w[8],U=w[9],z=w[10],Z=w[11],u=w[12],f=w[13],h=w[14],b=As(X,z),p=b*Or,b&&(x=Math.cos(-b),A=Math.sin(-b),B=N*x+k*A,q=O*x+U*A,F=X*x+z*A,k=N*-A+k*x,U=O*-A+U*x,z=X*-A+z*x,Z=K*-A+Z*x,N=B,O=q,X=F),b=As(-L,z),_=b*Or,b&&(x=Math.cos(-b),A=Math.sin(-b),B=P*x-k*A,q=R*x-U*A,F=L*x-z*A,Z=I*A+Z*x,P=B,R=q,L=F),b=As(R,P),g=b*Or,b&&(x=Math.cos(b),A=Math.sin(b),B=P*x+R*A,q=N*x+O*A,R=R*x-P*A,O=O*x-N*A,P=B,N=q),p&&Math.abs(p)+Math.abs(g)>359.9&&(p=g=0,_=180-_),d=Wt(Math.sqrt(P*P+R*R+L*L)),m=Wt(Math.sqrt(O*O+X*X)),b=As(N,O),v=Math.abs(b)>2e-4?b*Or:0,y=Z?1/(Z<0?-Z:Z):0),i.svg&&(B=e.getAttribute("transform"),i.forceCSS=e.setAttribute("transform","")||!hg(Wn(e,kt)),B&&e.setAttribute("transform",B))),Math.abs(v)>90&&Math.abs(v)<270&&(s?(d*=-1,v+=g<=0?180:-180,g+=g<=0?180:-180):(m*=-1,v+=v<=0?180:-180)),t=t||i.uncache,i.x=u-((i.xPercent=u&&(!t&&i.xPercent||(Math.round(e.offsetWidth/2)===Math.round(-u)?-50:0)))?e.offsetWidth*i.xPercent/100:0)+a,i.y=f-((i.yPercent=f&&(!t&&i.yPercent||(Math.round(e.offsetHeight/2)===Math.round(-f)?-50:0)))?e.offsetHeight*i.yPercent/100:0)+a,i.z=h+a,i.scaleX=Wt(d),i.scaleY=Wt(m),i.rotation=Wt(g)+o,i.rotationX=Wt(p)+o,i.rotationY=Wt(_)+o,i.skewX=v+o,i.skewY=S+o,i.transformPerspective=y+a,(i.zOrigin=parseFloat(c.split(" ")[2])||!t&&i.zOrigin||0)&&(r[Ln]=Tl(c)),i.xOffset=i.yOffset=0,i.force3D=Xn.force3D,i.renderTransform=i.svg?cT:og?fg:lT,i.uncache=0,i},Tl=function(e){return(e=e.split(" "))[0]+" "+e[1]},$c=function(e,t,i){var r=gn(t);return Wt(parseFloat(t)+parseFloat(Tr(e,"x",i+"px",r)))+r},lT=function(e,t){t.z="0px",t.rotationY=t.rotationX="0deg",t.force3D=0,fg(e,t)},Ir="0deg",Ma="0px",Fr=") ",fg=function(e,t){var i=t||this,r=i.xPercent,s=i.yPercent,a=i.x,o=i.y,l=i.z,c=i.rotation,u=i.rotationY,f=i.rotationX,h=i.skewX,d=i.skewY,m=i.scaleX,g=i.scaleY,p=i.transformPerspective,_=i.force3D,v=i.target,S=i.zOrigin,y="",M=_==="auto"&&e&&e!==1||_===!0;if(S&&(f!==Ir||u!==Ir)){var T=parseFloat(u)*Ns,w=Math.sin(T),b=Math.cos(T),x;T=parseFloat(f)*Ns,x=Math.cos(T),a=$c(v,a,w*x*-S),o=$c(v,o,-Math.sin(T)*-S),l=$c(v,l,b*x*-S+S)}p!==Ma&&(y+="perspective("+p+Fr),(r||s)&&(y+="translate("+r+"%, "+s+"%) "),(M||a!==Ma||o!==Ma||l!==Ma)&&(y+=l!==Ma||M?"translate3d("+a+", "+o+", "+l+") ":"translate("+a+", "+o+Fr),c!==Ir&&(y+="rotate("+c+Fr),u!==Ir&&(y+="rotateY("+u+Fr),f!==Ir&&(y+="rotateX("+f+Fr),(h!==Ir||d!==Ir)&&(y+="skew("+h+", "+d+Fr),(m!==1||g!==1)&&(y+="scale("+m+", "+g+Fr),v.style[kt]=y||"translate(0, 0)"},cT=function(e,t){var i=t||this,r=i.xPercent,s=i.yPercent,a=i.x,o=i.y,l=i.rotation,c=i.skewX,u=i.skewY,f=i.scaleX,h=i.scaleY,d=i.target,m=i.xOrigin,g=i.yOrigin,p=i.xOffset,_=i.yOffset,v=i.forceCSS,S=parseFloat(a),y=parseFloat(o),M,T,w,b,x;l=parseFloat(l),c=parseFloat(c),u=parseFloat(u),u&&(u=parseFloat(u),c+=u,l+=u),l||c?(l*=Ns,c*=Ns,M=Math.cos(l)*f,T=Math.sin(l)*f,w=Math.sin(l-c)*-h,b=Math.cos(l-c)*h,c&&(u*=Ns,x=Math.tan(c-u),x=Math.sqrt(1+x*x),w*=x,b*=x,u&&(x=Math.tan(u),x=Math.sqrt(1+x*x),M*=x,T*=x)),M=Wt(M),T=Wt(T),w=Wt(w),b=Wt(b)):(M=f,b=h,T=w=0),(S&&!~(a+"").indexOf("px")||y&&!~(o+"").indexOf("px"))&&(S=Tr(d,"x",a,"px"),y=Tr(d,"y",o,"px")),(m||g||p||_)&&(S=Wt(S+m-(m*M+g*w)+p),y=Wt(y+g-(m*T+g*b)+_)),(r||s)&&(x=d.getBBox(),S=Wt(S+r/100*x.width),y=Wt(y+s/100*x.height)),x="matrix("+M+","+T+","+w+","+b+","+S+","+y+")",d.setAttribute("transform",x),v&&(d.style[kt]=x)},uT=function(e,t,i,r,s){var a=360,o=ln(s),l=parseFloat(s)*(o&&~s.indexOf("rad")?Or:1),c=l-r,u=r+c+"deg",f,h;return o&&(f=s.split("_")[1],f==="short"&&(c%=a,c!==c%(a/2)&&(c+=c<0?a:-a)),f==="cw"&&c<0?c=(c+a*Ip)%a-~~(c/a)*a:f==="ccw"&&c>0&&(c=(c-a*Ip)%a-~~(c/a)*a)),e._pt=h=new Un(e._pt,t,i,r,c,j2),h.e=u,h.u="deg",e._props.push(i),h},Gp=function(e,t){for(var i in t)e[i]=t[i];return e},hT=function(e,t,i){var r=Gp({},i._gsap),s="perspective,force3D,transformOrigin,svgOrigin",a=i.style,o,l,c,u,f,h,d,m;r.svg?(c=i.getAttribute("transform"),i.setAttribute("transform",""),a[kt]=t,o=Ya(i,1),Mr(i,kt),i.setAttribute("transform",c)):(c=getComputedStyle(i)[kt],a[kt]=t,o=Ya(i,1),a[kt]=c);for(l in Zi)c=r[l],u=o[l],c!==u&&s.indexOf(l)<0&&(d=gn(c),m=gn(u),f=d!==m?Tr(i,l,c,m):parseFloat(c),h=parseFloat(u),e._pt=new Un(e._pt,o,l,f,h-f,Ih),e._pt.u=m||0,e._props.push(l));Gp(o,r)};Dn("padding,margin,Width,Radius",function(n,e){var t="Top",i="Right",r="Bottom",s="Left",a=(e<3?[t,i,r,s]:[t+s,t+i,r+i,r+s]).map(function(o){return e<2?n+o:"border"+o+n});Ml[e>1?"border"+n:n]=function(o,l,c,u,f){var h,d;if(arguments.length<4)return h=a.map(function(m){return Hi(o,m,c)}),d=h.join(" "),d.split(h[0]).length===5?h[0]:d;h=(u+"").split(" "),d={},a.forEach(function(m,g){return d[m]=h[g]=h[g]||h[(g-1)/2|0]}),o.init(l,d,f)}});var dg={name:"css",register:Nh,targetTest:function(e){return e.style&&e.nodeType},init:function(e,t,i,r,s){var a=this._props,o=e.style,l=i.vars.startAt,c,u,f,h,d,m,g,p,_,v,S,y,M,T,w,b,x;bf||Nh(),this.styles=this.styles||ag(e),b=this.styles.props,this.tween=i;for(g in t)if(g!=="autoRound"&&(u=t[g],!(zn[g]&&K0(g,t,i,r,e,s)))){if(d=typeof u,m=Ml[g],d==="function"&&(u=u.call(i,r,e,s),d=typeof u),d==="string"&&~u.indexOf("random(")&&(u=Va(u)),m)m(this,e,g,u,i)&&(w=1);else if(g.substr(0,2)==="--")c=(getComputedStyle(e).getPropertyValue(g)+"").trim(),u+="",xr.lastIndex=0,xr.test(c)||(p=gn(c),_=gn(u),_?p!==_&&(c=Tr(e,g,c,_)+_):p&&(u+=p)),this.add(o,"setProperty",c,u,r,s,0,0,g),a.push(g),b.push(g,0,o[g]);else if(d!=="undefined"){if(l&&g in l?(c=typeof l[g]=="function"?l[g].call(i,r,e,s):l[g],ln(c)&&~c.indexOf("random(")&&(c=Va(c)),gn(c+"")||c==="auto"||(c+=Xn.units[g]||gn(Hi(e,g))||""),(c+"").charAt(1)==="="&&(c=Hi(e,g))):c=Hi(e,g),h=parseFloat(c),v=d==="string"&&u.charAt(1)==="="&&u.substr(0,2),v&&(u=u.substr(2)),f=parseFloat(u),g in Ci&&(g==="autoAlpha"&&(h===1&&Hi(e,"visibility")==="hidden"&&f&&(h=0),b.push("visibility",0,o.visibility),gr(this,o,"visibility",h?"inherit":"hidden",f?"inherit":"hidden",!f)),g!=="scale"&&g!=="transform"&&(g=Ci[g],~g.indexOf(",")&&(g=g.split(",")[0]))),S=g in Zi,S){if(this.styles.save(g),x=u,d==="string"&&u.substring(0,6)==="var(--"){if(u=Wn(e,u.substring(4,u.indexOf(")"))),u.substring(0,5)==="calc("){var A=e.style.perspective;e.style.perspective=u,u=Wn(e,"perspective"),A?e.style.perspective=A:Mr(e,"perspective")}f=parseFloat(u)}if(y||(M=e._gsap,M.renderTransform&&!t.parseTransform||Ya(e,t.parseTransform),T=t.smoothOrigin!==!1&&M.smooth,y=this._pt=new Un(this._pt,o,kt,0,1,M.renderTransform,M,0,-1),y.dep=1),g==="scale")this._pt=new Un(this._pt,M,"scaleY",M.scaleY,(v?Is(M.scaleY,v+f):f)-M.scaleY||0,Ih),this._pt.u=0,a.push("scaleY",g),g+="X";else if(g==="transformOrigin"){b.push(Ln,0,o[Ln]),u=aT(u),M.svg?Oh(e,u,0,T,0,this):(_=parseFloat(u.split(" ")[2])||0,_!==M.zOrigin&&gr(this,M,"zOrigin",M.zOrigin,_),gr(this,o,g,Tl(c),Tl(u)));continue}else if(g==="svgOrigin"){Oh(e,u,1,T,0,this);continue}else if(g in ug){uT(this,M,g,h,v?Is(h,v+u):u);continue}else if(g==="smoothOrigin"){gr(this,M,"smooth",M.smooth,u);continue}else if(g==="force3D"){M[g]=u;continue}else if(g==="transform"){hT(this,u,e);continue}}else g in o||(g=Ys(g)||g);if(S||(f||f===0)&&(h||h===0)&&!X2.test(u)&&g in o)p=(c+"").substr((h+"").length),f||(f=0),_=gn(u)||(g in Xn.units?Xn.units[g]:p),p!==_&&(h=Tr(e,g,c,_)),this._pt=new Un(this._pt,S?M:o,g,h,(v?Is(h,v+f):f)-h,!S&&(_==="px"||g==="zIndex")&&t.autoRound!==!1?K2:Ih),this._pt.u=_||0,S&&x!==u?(this._pt.b=c,this._pt.e=x,this._pt.r=q2):p!==_&&_!=="%"&&(this._pt.b=c,this._pt.r=Y2);else if(g in o)sT.call(this,e,g,c,v?v+u:u);else if(g in e)this.add(e,g,c||e[g],v?v+u:u,r,s);else if(g!=="parseTransform"){hf(g,u);continue}S||(g in o?b.push(g,0,o[g]):typeof e[g]=="function"?b.push(g,2,e[g]()):b.push(g,1,c||e[g])),a.push(g)}}w&&tg(this)},render:function(e,t){if(t.tween._time||!Sf())for(var i=t._pt;i;)i.r(e,i.d),i=i._next;else t.styles.revert()},get:Hi,aliases:Ci,getSetter:function(e,t,i){var r=Ci[t];return r&&r.indexOf(",")<0&&(t=r),t in Zi&&t!==Ln&&(e._gsap.x||Hi(e,"x"))?i&&Lp===i?t==="scale"?Q2:J2:(Lp=i||{})&&(t==="scale"?eT:tT):e.style&&!lf(e.style[t])?Z2:~t.indexOf("-")?$2:xf(e,t)},core:{_removeProperty:Mr,_getMatrix:Tf}};In.utils.checkPrefix=Ys;In.core.getStyleSaver=ag;(function(n,e,t,i){var r=Dn(n+","+e+","+t,function(s){Zi[s]=1});Dn(e,function(s){Xn.units[s]="deg",ug[s]=1}),Ci[r[13]]=n+","+e,Dn(i,function(s){var a=s.split(":");Ci[a[1]]=r[a[0]]})})("x,y,z,scale,scaleX,scaleY,xPercent,yPercent","rotation,rotationX,rotationY,skewX,skewY","transform,transformOrigin,svgOrigin,force3D,smoothOrigin,transformPerspective","0:translateX,1:translateY,2:translateZ,8:rotate,8:rotationZ,8:rotateZ,9:rotateX,10:rotateY");Dn("x,y,z,top,right,bottom,left,width,height,fontSize,padding,margin,perspective",function(n){Xn.units[n]="px"});In.registerPlugin(dg);var sl=In.registerPlugin(dg)||In;sl.core.Tween;/**
 * postprocessing v6.39.5 build Wed Sep 09 2026
 * https://github.com/pmndrs/postprocessing
 * Copyright 2015-2026 Raoul van Rüschen
 * @license Zlib
 */var fT=(()=>{const n=new Float32Array([-1,-1,0,3,-1,0,-1,3,0]),e=new Float32Array([0,0,2,0,0,2]),t=new Dt;return t.setAttribute("position",new Nt(n,3)),t.setAttribute("uv",new Nt(e,2)),t})(),mi=class Bh{static get fullscreenGeometry(){return fT}constructor(e="Pass",t=new ph,i=new rf){this.name=e,this.renderer=null,this.scene=t,this.camera=i,this.screen=null,this.rtt=!0,this.needsSwap=!0,this.needsDepthBlit=!1,this.needsDepthTexture=!1,this.enabled=!0}get renderToScreen(){return!this.rtt}set renderToScreen(e){if(this.rtt===e){const t=this.fullscreenMaterial;t!==null&&(t.needsUpdate=!0),this.rtt=!e}}set mainScene(e){}set mainCamera(e){}setRenderer(e){this.renderer=e}isEnabled(){return this.enabled}setEnabled(e){this.enabled=e}get fullscreenMaterial(){return this.screen!==null?this.screen.material:null}set fullscreenMaterial(e){let t=this.screen;t!==null?t.material=e:(t=new jn(Bh.fullscreenGeometry,e),t.frustumCulled=!1,this.scene===null&&(this.scene=new ph),this.scene.add(t),this.screen=t)}getFullscreenMaterial(){return this.fullscreenMaterial}setFullscreenMaterial(e){this.fullscreenMaterial=e}getDepthTexture(){return null}setDepthTexture(e,t=Za){}render(e,t,i,r,s){throw new Error("Render method not implemented!")}setSize(e,t){}initialize(e,t,i){}dispose(){for(const e of Object.keys(this)){const t=this[e];(t instanceof Jt||t instanceof $i||t instanceof $t||t instanceof Bh)&&this[e].dispose()}this.fullscreenMaterial!==null&&this.fullscreenMaterial.dispose()}},dT=class extends mi{constructor(){super("ClearMaskPass",null,null),this.needsSwap=!1}render(n,e,t,i,r){const s=n.state.buffers.stencil;s.setLocked(!1),s.setTest(!1)}},pT=`#ifdef COLOR_WRITE
#include <common>
#include <dithering_pars_fragment>
#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
#endif
#ifdef DEPTH_WRITE
#include <packing>
#ifdef GL_FRAGMENT_PRECISION_HIGH
uniform highp sampler2D depthBuffer;
#else
uniform mediump sampler2D depthBuffer;
#endif
float readDepth(const in vec2 uv){
#if DEPTH_PACKING == 3201
return unpackRGBAToDepth(texture2D(depthBuffer,uv));
#else
return texture2D(depthBuffer,uv).r;
#endif
}
#endif
#ifdef USE_WEIGHTS
uniform vec4 channelWeights;
#endif
uniform float opacity;varying vec2 vUv;void main(){
#ifdef COLOR_WRITE
vec4 texel=texture2D(inputBuffer,vUv);
#ifdef USE_WEIGHTS
texel*=channelWeights;
#endif
gl_FragColor=opacity*texel;
#ifdef COLOR_SPACE_CONVERSION
#include <colorspace_fragment>
#endif
#include <dithering_fragment>
#else
gl_FragColor=vec4(0.0);
#endif
#ifdef DEPTH_WRITE
gl_FragDepth=readDepth(vUv);
#endif
}`,pg="varying vec2 vUv;void main(){vUv=position.xy*0.5+0.5;gl_Position=vec4(position.xy,1.0,1.0);}",mg=class extends on{constructor(){super({name:"CopyMaterial",defines:{COLOR_SPACE_CONVERSION:"1",DEPTH_PACKING:"0",COLOR_WRITE:"1"},uniforms:{inputBuffer:new vt(null),depthBuffer:new vt(null),channelWeights:new vt(null),opacity:new vt(1)},blending:Tn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:pT,vertexShader:pg}),this.depthFunc=ll}get inputBuffer(){return this.uniforms.inputBuffer.value}set inputBuffer(n){const e=n!==null;this.colorWrite!==e&&(e?this.defines.COLOR_WRITE=!0:delete this.defines.COLOR_WRITE,this.colorWrite=e,this.needsUpdate=!0),this.uniforms.inputBuffer.value=n}get depthBuffer(){return this.uniforms.depthBuffer.value}set depthBuffer(n){const e=n!==null;this.depthWrite!==e&&(e?this.defines.DEPTH_WRITE=!0:delete this.defines.DEPTH_WRITE,this.depthTest=e,this.depthWrite=e,this.needsUpdate=!0),this.uniforms.depthBuffer.value=n}set depthPacking(n){this.defines.DEPTH_PACKING=n.toFixed(0),this.needsUpdate=!0}get colorSpaceConversion(){return this.defines.COLOR_SPACE_CONVERSION!==void 0}set colorSpaceConversion(n){this.colorSpaceConversion!==n&&(n?this.defines.COLOR_SPACE_CONVERSION=!0:delete this.defines.COLOR_SPACE_CONVERSION,this.needsUpdate=!0)}get channelWeights(){return this.uniforms.channelWeights.value}set channelWeights(n){n!==null?(this.defines.USE_WEIGHTS="1",this.uniforms.channelWeights.value=n):delete this.defines.USE_WEIGHTS,this.needsUpdate=!0}setInputBuffer(n){this.uniforms.inputBuffer.value=n}getOpacity(n){return this.uniforms.opacity.value}setOpacity(n){this.uniforms.opacity.value=n}},mT=class extends mi{constructor(n,e=!0){super("CopyPass"),this.fullscreenMaterial=new mg,this.needsSwap=!1,this.renderTarget=n,n===void 0&&(this.renderTarget=new Jt(1,1,{minFilter:Gt,magFilter:Gt,stencilBuffer:!1,depthBuffer:!1}),this.renderTarget.texture.name="CopyPass.Target"),this.autoResize=e}get resize(){return this.autoResize}set resize(n){this.autoResize=n}get texture(){return this.renderTarget.texture}getTexture(){return this.renderTarget.texture}setAutoResizeEnabled(n){this.autoResize=n}render(n,e,t,i,r){this.fullscreenMaterial.inputBuffer=e.texture,n.setRenderTarget(this.renderToScreen?null:this.renderTarget),n.render(this.scene,this.camera)}setSize(n,e){this.autoResize&&this.renderTarget.setSize(n,e)}initialize(n,e,t){t!==void 0&&(this.renderTarget.texture.type=t,t!==Yt?this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1":n!==null&&n.outputColorSpace===Et&&(this.renderTarget.texture.colorSpace=Et))}},Hp=new ut,gg=class extends mi{constructor(n=!0,e=!0,t=!1){super("ClearPass",null,null),this.needsSwap=!1,this.color=n,this.depth=e,this.stencil=t,this.overrideClearColor=null,this.overrideClearAlpha=-1}setClearFlags(n,e,t){this.color=n,this.depth=e,this.stencil=t}getOverrideClearColor(){return this.overrideClearColor}setOverrideClearColor(n){this.overrideClearColor=n}getOverrideClearAlpha(){return this.overrideClearAlpha}setOverrideClearAlpha(n){this.overrideClearAlpha=n}render(n,e,t,i,r){const s=this.overrideClearColor,a=this.overrideClearAlpha,o=n.getClearAlpha(),l=s!==null,c=a>=0;l?(n.getClearColor(Hp),n.setClearColor(s,c?a:o)):c&&n.setClearAlpha(a),n.setRenderTarget(this.renderToScreen?null:e),n.clear(this.color,this.depth,this.stencil),l?n.setClearColor(Hp,o):c&&n.setClearAlpha(o)}},gT=class extends mi{constructor(n,e){super("MaskPass",n,e),this.needsSwap=!1,this.clearPass=new gg(!1,!1,!0),this.inverse=!1}set mainScene(n){this.scene=n}set mainCamera(n){this.camera=n}get inverted(){return this.inverse}set inverted(n){this.inverse=n}get clear(){return this.clearPass.enabled}set clear(n){this.clearPass.enabled=n}getClearPass(){return this.clearPass}isInverted(){return this.inverted}setInverted(n){this.inverted=n}render(n,e,t,i,r){const s=n.getContext(),a=n.state.buffers,o=this.scene,l=this.camera,c=this.clearPass,u=this.inverted?0:1,f=1-u;a.color.setMask(!1),a.depth.setMask(!1),a.color.setLocked(!0),a.depth.setLocked(!0),a.stencil.setTest(!0),a.stencil.setOp(s.REPLACE,s.REPLACE,s.REPLACE),a.stencil.setFunc(s.ALWAYS,u,4294967295),a.stencil.setClear(f),a.stencil.setLocked(!0),this.clearPass.enabled&&(this.renderToScreen?c.render(n,null):(c.render(n,e),c.render(n,t))),this.renderToScreen?(n.setRenderTarget(null),n.render(o,l)):(n.setRenderTarget(e),n.render(o,l),n.setRenderTarget(t),n.render(o,l)),a.color.setLocked(!1),a.depth.setLocked(!1),a.stencil.setLocked(!1),a.stencil.setFunc(s.EQUAL,1,4294967295),a.stencil.setOp(s.KEEP,s.KEEP,s.KEEP),a.stencil.setLocked(!0)}};function _T(n,e){const t=n.getContext();if(e<=0||typeof t.renderbufferStorageMultisample!="function")return 0;const i=t.getParameter(t.MAX_SAMPLES),r=Math.min(e,i);if(r<=0)return 0;const s=t.getParameter(t.RENDERBUFFER_BINDING),a=t.createRenderbuffer();try{return t.bindRenderbuffer(t.RENDERBUFFER,a),t.renderbufferStorageMultisample(t.RENDERBUFFER,r,t.RGBA8,1,1),r}catch{return 0}finally{t.bindRenderbuffer(t.RENDERBUFFER,s),t.deleteRenderbuffer(a)}}var Jc=1/1e3,vT=1e3,xT=class{constructor(){this.startTime=performance.now(),this.previousTime=0,this.currentTime=0,this._delta=0,this._elapsed=0,this._fixedDelta=1e3/60,this.timescale=1,this.useFixedDelta=!1,this._autoReset=!1}get autoReset(){return this._autoReset}set autoReset(n){typeof document<"u"&&document.hidden!==void 0&&(n?document.addEventListener("visibilitychange",this):document.removeEventListener("visibilitychange",this),this._autoReset=n)}get delta(){return this._delta*Jc}get fixedDelta(){return this._fixedDelta*Jc}set fixedDelta(n){this._fixedDelta=n*vT}get elapsed(){return this._elapsed*Jc}update(n){this.useFixedDelta?this._delta=this.fixedDelta:(this.previousTime=this.currentTime,this.currentTime=(n!==void 0?n:performance.now())-this.startTime,this._delta=this.currentTime-this.previousTime),this._delta*=this.timescale,this._elapsed+=this._delta}reset(){this._delta=0,this._elapsed=0,this.currentTime=performance.now()-this.startTime}getDelta(){return this.delta}getElapsed(){return this.elapsed}handleEvent(n){document.hidden||(this.currentTime=performance.now()-this.startTime)}dispose(){this.autoReset=!1}},yT=class{constructor(n=null,{depthBuffer:e=!0,stencilBuffer:t=!1,multisampling:i=0,frameBufferType:r=Yt}={}){this.renderer=null,this.inputBuffer=this.createBuffer(e,t,r,i),this.outputBuffer=this.inputBuffer.clone(),this.copyPass=new mT,this.depthRenderTarget=null,this.passes=[],this.timer=new xT,this.autoRenderToScreen=!0,this.setRenderer(n)}get stableDepthTexture(){return this.depthRenderTarget===null?null:this.depthRenderTarget.depthTexture}get multisampling(){return this.inputBuffer.samples}set multisampling(n){const e=this.renderer===null?n:_T(this.renderer,n);this.multisampling!==e&&(this.inputBuffer.samples=e,this.outputBuffer.samples=e,this.inputBuffer.dispose(),this.outputBuffer.dispose())}getTimer(){return this.timer}getRenderer(){return this.renderer}setRenderer(n){if(this.renderer=n,n!==null){const e=n.getSize(new Xe),t=n.getContext().getContextAttributes().alpha,i=this.inputBuffer.texture.type;i===Yt&&n.outputColorSpace===Et&&(this.inputBuffer.texture.colorSpace=Et,this.outputBuffer.texture.colorSpace=Et,this.inputBuffer.dispose(),this.outputBuffer.dispose());const r=this.multisampling;this.multisampling=r,n.autoClear=!1,this.setSize(e.width,e.height);for(const s of this.passes)s.initialize(n,t,i)}}replaceRenderer(n,e=!0){const t=this.renderer,i=t.domElement.parentNode;return this.setRenderer(n),e&&i!==null&&(i.removeChild(t.domElement),i.appendChild(n.domElement)),t}createDepthTexture(){const n=new Xi;n.name="EffectComposer.InputDepth",this.inputBuffer.stencilBuffer?(n.format=fr,n.type=zs):n.type=hi;const e=new Xi;e.format=n.format,e.type=n.type,e.name="EffectComposer.OutputDepth";const t=new Xi;t.format=n.format,t.type=n.type,t.name="EffectComposer.StableDepth",this.inputBuffer.depthTexture=n,this.outputBuffer.depthTexture=e,this.inputBuffer.dispose(),this.outputBuffer.dispose();const{width:i,height:r}=this.inputBuffer;this.depthRenderTarget=new Jt(i,r,{depthBuffer:!0,stencilBuffer:this.inputBuffer.stencilBuffer,depthTexture:t})}blitDepthBuffer(n){const e=this.renderer,t=this.depthRenderTarget,i=e.properties,r=e.getContext();e.setRenderTarget(t);const s=i.get(n).__webglFramebuffer,a=i.get(t).__webglFramebuffer,o=n.stencilBuffer?r.DEPTH_BUFFER_BIT|r.STENCIL_BUFFER_BIT:r.DEPTH_BUFFER_BIT;r.bindFramebuffer(r.READ_FRAMEBUFFER,s),r.bindFramebuffer(r.DRAW_FRAMEBUFFER,a),r.blitFramebuffer(0,0,n.width,n.height,0,0,t.width,t.height,o,r.NEAREST),r.bindFramebuffer(r.READ_FRAMEBUFFER,null),r.bindFramebuffer(r.DRAW_FRAMEBUFFER,null),e.setRenderTarget(null)}deleteDepthTexture(){const n=this.stableDepthTexture;for(const e of this.passes)e.getDepthTexture()===n&&e.setDepthTexture(null);this.depthRenderTarget!==null&&(this.depthRenderTarget.dispose(),this.depthRenderTarget=null),this.inputBuffer.depthTexture!==null&&(this.inputBuffer.depthTexture.dispose(),this.inputBuffer.depthTexture=null),this.outputBuffer.depthTexture!==null&&(this.outputBuffer.depthTexture.dispose(),this.outputBuffer.depthTexture=null)}createBuffer(n,e,t,i){const r=this.renderer,s=r===null?new Xe:r.getDrawingBufferSize(new Xe),a=new Jt(s.width,s.height,{minFilter:Gt,magFilter:Gt,samples:i,stencilBuffer:e,depthBuffer:n,type:t});return t===Yt&&r!==null&&r.outputColorSpace===Et&&(a.texture.colorSpace=Et),a.texture.name="EffectComposer.Buffer",a.texture.generateMipmaps=!1,a}setMainScene(n){for(const e of this.passes)e.mainScene=n}setMainCamera(n){for(const e of this.passes)e.mainCamera=n}addPass(n,e){const t=this.passes,i=this.renderer,r=i.getDrawingBufferSize(new Xe),s=i.getContext().getContextAttributes().alpha,a=this.inputBuffer.texture.type;if(n.renderer=i,n.setSize(r.width,r.height),n.initialize(i,s,a),this.autoRenderToScreen&&(t.length>0&&(t[t.length-1].renderToScreen=!1),n.renderToScreen&&(this.autoRenderToScreen=!1)),e!==void 0?t.splice(e,0,n):t.push(n),this.autoRenderToScreen&&(t[t.length-1].renderToScreen=!0),n.needsDepthTexture||this.depthRenderTarget!==null)if(this.depthRenderTarget===null){this.createDepthTexture();for(const o of t)o.setDepthTexture(this.stableDepthTexture)}else n.setDepthTexture(this.stableDepthTexture)}removePass(n){const e=this.passes,t=e.indexOf(n);if(t!==-1&&e.splice(t,1).length>0){const s=this.stableDepthTexture;if(s!==null){const a=(l,c)=>l||c.needsDepthTexture;e.reduce(a,!1)||(n.getDepthTexture()===s&&n.setDepthTexture(null),this.deleteDepthTexture())}this.autoRenderToScreen&&t===e.length&&(n.renderToScreen=!1,e.length>0&&(e[e.length-1].renderToScreen=!0))}}removeAllPasses(){const n=this.passes;this.deleteDepthTexture(),n.length>0&&(this.autoRenderToScreen&&(n[n.length-1].renderToScreen=!1),this.passes=[])}render(n){const e=this.renderer,t=this.copyPass;let i=this.inputBuffer,r=this.outputBuffer,s,a=!1;n===void 0&&(this.timer.update(),n=this.timer.getDelta());for(const o of this.passes)if(o.enabled){if(o.render(e,i,r,n,a),o.needsDepthBlit&&this.depthRenderTarget!==null&&this.blitDepthBuffer(i),o.needsSwap){if(a){t.renderToScreen=o.renderToScreen;const l=e.getContext(),c=e.state.buffers.stencil;c.setFunc(l.NOTEQUAL,1,4294967295),t.render(e,i,r,n,a),c.setFunc(l.EQUAL,1,4294967295)}s=i,i=r,r=s}o instanceof gT?a=!0:o instanceof dT&&(a=!1)}}setSize(n,e,t){const i=this.renderer,r=i.getSize(new Xe);(n===void 0||e===void 0)&&(n=r.width,e=r.height),(r.width!==n||r.height!==e)&&i.setSize(n,e,t);const s=i.getDrawingBufferSize(new Xe);this.inputBuffer.setSize(s.width,s.height),this.outputBuffer.setSize(s.width,s.height),this.depthRenderTarget!==null&&this.depthRenderTarget.setSize(s.width,s.height);for(const a of this.passes)a.setSize(s.width,s.height)}reset(){this.dispose(),this.autoRenderToScreen=!0}dispose(){for(const n of this.passes)n.dispose();this.deleteDepthTexture(),this.inputBuffer.dispose(),this.outputBuffer.dispose(),this.copyPass.dispose(),this.timer.dispose(),this.passes=[],mi.fullscreenGeometry.dispose()}},qr={NONE:0,DEPTH:1,CONVOLUTION:2},gt={FRAGMENT_HEAD:"FRAGMENT_HEAD",FRAGMENT_MAIN_UV:"FRAGMENT_MAIN_UV",FRAGMENT_MAIN_IMAGE:"FRAGMENT_MAIN_IMAGE",VERTEX_HEAD:"VERTEX_HEAD",VERTEX_MAIN_SUPPORT:"VERTEX_MAIN_SUPPORT"},bT=class{constructor(){this.shaderParts=new Map([[gt.FRAGMENT_HEAD,null],[gt.FRAGMENT_MAIN_UV,null],[gt.FRAGMENT_MAIN_IMAGE,null],[gt.VERTEX_HEAD,null],[gt.VERTEX_MAIN_SUPPORT,null]]),this.defines=new Map,this.uniforms=new Map,this.blendModes=new Map,this.extensions=new Set,this.attributes=qr.NONE,this.varyings=new Set,this.uvTransformation=!1,this.readDepth=!1,this.colorSpace=Gs}},Qc=!1,Vp=class{constructor(n=null){this.originalMaterials=new Map,this.material=null,this.materials=null,this.materialsBackSide=null,this.materialsDoubleSide=null,this.materialsFlatShaded=null,this.materialsFlatShadedBackSide=null,this.materialsFlatShadedDoubleSide=null,this.setMaterial(n),this.meshCount=0,this.replaceMaterial=e=>{if(e.isMesh){let t;if(e.material.flatShading)switch(e.material.side){case Rn:t=this.materialsFlatShadedDoubleSide;break;case an:t=this.materialsFlatShadedBackSide;break;default:t=this.materialsFlatShaded;break}else switch(e.material.side){case Rn:t=this.materialsDoubleSide;break;case an:t=this.materialsBackSide;break;default:t=this.materials;break}this.originalMaterials.set(e,e.material),e.isSkinnedMesh?e.material=t[2]:e.isInstancedMesh?e.material=t[1]:e.material=t[0],++this.meshCount}}}cloneMaterial(n){if(!(n instanceof on))return n.clone();const e=n.uniforms,t=new Map;for(const r in e){const s=e[r].value;s.isRenderTargetTexture&&(e[r].value=null,t.set(r,s))}const i=n.clone();for(const r of t)e[r[0]].value=r[1],i.uniforms[r[0]].value=r[1];return i}setMaterial(n){if(this.disposeMaterials(),this.material=n,n!==null){const e=this.materials=[this.cloneMaterial(n),this.cloneMaterial(n),this.cloneMaterial(n)];for(const t of e)t.uniforms=Object.assign({},n.uniforms),t.side=ji;e[2].skinning=!0,this.materialsBackSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.side=an,i}),this.materialsDoubleSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.side=Rn,i}),this.materialsFlatShaded=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.flatShading=!0,i}),this.materialsFlatShadedBackSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.flatShading=!0,i.side=an,i}),this.materialsFlatShadedDoubleSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.flatShading=!0,i.side=Rn,i})}}render(n,e,t){const i=n.shadowMap.enabled;if(n.shadowMap.enabled=!1,Qc){const r=this.originalMaterials;this.meshCount=0,e.traverse(this.replaceMaterial),n.render(e,t);for(const s of r)s[0].material=s[1];this.meshCount!==r.size&&r.clear()}else{const r=e.overrideMaterial;e.overrideMaterial=this.material,n.render(e,t),e.overrideMaterial=r}n.shadowMap.enabled=i}disposeMaterials(){if(this.material!==null){const n=this.materials.concat(this.materialsBackSide).concat(this.materialsDoubleSide).concat(this.materialsFlatShaded).concat(this.materialsFlatShadedBackSide).concat(this.materialsFlatShadedDoubleSide);for(const e of n)e.dispose()}}dispose(){this.originalMaterials.clear(),this.disposeMaterials()}static get workaroundEnabled(){return Qc}static set workaroundEnabled(n){Qc=n}},cr=-1,Pi=class extends pi{constructor(n=null,e=cr,t=cr,i=1){super(),n!==null&&this.addEventListener("change",()=>n.setSize(this.baseSize.width,this.baseSize.height)),this.baseSize=new Xe(1,1),this.preferredSize=new Xe(e,t),this.target=this.preferredSize,this.s=i,this.effectiveSize=new Xe,this.addEventListener("change",()=>this.updateEffectiveSize()),this.updateEffectiveSize()}updateEffectiveSize(){const n=this.baseSize,e=this.preferredSize,t=this.effectiveSize,i=this.scale;e.width!==cr?t.width=e.width:e.height!==cr?t.width=Math.round(e.height*(n.width/Math.max(n.height,1))):t.width=Math.round(n.width*i),e.height!==cr?t.height=e.height:e.width!==cr?t.height=Math.round(e.width/Math.max(n.width/Math.max(n.height,1),1)):t.height=Math.round(n.height*i)}get width(){return this.effectiveSize.width}set width(n){this.preferredWidth=n}get height(){return this.effectiveSize.height}set height(n){this.preferredHeight=n}getWidth(){return this.width}getHeight(){return this.height}get scale(){return this.s}set scale(n){this.s!==n&&(this.s=n,this.preferredSize.setScalar(cr),this.dispatchEvent({type:"change"}))}getScale(){return this.scale}setScale(n){this.scale=n}get baseWidth(){return this.baseSize.width}set baseWidth(n){this.baseSize.width!==n&&(this.baseSize.width=n,this.dispatchEvent({type:"change"}))}getBaseWidth(){return this.baseWidth}setBaseWidth(n){this.baseWidth=n}get baseHeight(){return this.baseSize.height}set baseHeight(n){this.baseSize.height!==n&&(this.baseSize.height=n,this.dispatchEvent({type:"change"}))}getBaseHeight(){return this.baseHeight}setBaseHeight(n){this.baseHeight=n}setBaseSize(n,e){(this.baseSize.width!==n||this.baseSize.height!==e)&&(this.baseSize.set(n,e),this.dispatchEvent({type:"change"}))}get preferredWidth(){return this.preferredSize.width}set preferredWidth(n){this.preferredSize.width!==n&&(this.preferredSize.width=n,this.dispatchEvent({type:"change"}))}getPreferredWidth(){return this.preferredWidth}setPreferredWidth(n){this.preferredWidth=n}get preferredHeight(){return this.preferredSize.height}set preferredHeight(n){this.preferredSize.height!==n&&(this.preferredSize.height=n,this.dispatchEvent({type:"change"}))}getPreferredHeight(){return this.preferredHeight}setPreferredHeight(n){this.preferredHeight=n}setPreferredSize(n,e){(this.preferredSize.width!==n||this.preferredSize.height!==e)&&(this.preferredSize.set(n,e),this.dispatchEvent({type:"change"}))}copy(n){this.s=n.scale,this.baseSize.set(n.baseWidth,n.baseHeight),this.preferredSize.set(n.preferredWidth,n.preferredHeight),this.dispatchEvent({type:"change"})}static get AUTO_SIZE(){return cr}},ct={ADD:0,ALPHA:1,AVERAGE:2,COLOR:3,COLOR_BURN:4,COLOR_DODGE:5,DARKEN:6,DIFFERENCE:7,DIVIDE:8,DST:9,EXCLUSION:10,HARD_LIGHT:11,HARD_MIX:12,HUE:13,INVERT:14,INVERT_RGB:15,LIGHTEN:16,LINEAR_BURN:17,LINEAR_DODGE:18,LINEAR_LIGHT:19,LUMINOSITY:20,MULTIPLY:21,NEGATION:22,NORMAL:23,OVERLAY:24,PIN_LIGHT:25,REFLECT:26,SATURATION:27,SCREEN:28,SOFT_LIGHT:29,SRC:30,SUBTRACT:31,VIVID_LIGHT:32},ST="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",MT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return mix(dst,src,src.a*opacity);}",TT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=(dst.rgb+src.rgb)*0.5;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",ET="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(b.xy,a.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",wT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=dst.rgb,b=src.rgb;vec3 c=mix(step(0.0,b)*(1.0-min(vec3(1.0),(1.0-a)/max(b,1e-9))),vec3(1.0),step(1.0,a));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",AT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=dst.rgb,b=src.rgb;vec3 c=step(0.0,a)*mix(min(vec3(1.0),a/max(1.0-b,1e-9)),vec3(1.0),step(1.0,b));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",RT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=min(dst.rgb,src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",CT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=abs(dst.rgb-src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",PT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb/max(src.rgb,1e-9);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",DT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb-2.0*dst.rgb*src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",UT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=min(dst.rgb,1.0);vec3 b=min(src.rgb,1.0);vec3 c=mix(2.0*a*b,1.0-2.0*(1.0-a)*(1.0-b),step(0.5,b));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",LT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=step(1.0,dst.rgb+src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",IT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(b.x,a.yz));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",FT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(1.0-src.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",NT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=src.rgb*max(1.0-dst.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",OT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(dst.rgb,src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",BT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=clamp(src.rgb+dst.rgb-1.0,0.0,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",kT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=min(dst.rgb+src.rgb,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",zT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=clamp(2.0*src.rgb+dst.rgb-1.0,0.0,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",GT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(a.xy,b.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",HT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb*src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",VT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(1.0-abs(1.0-dst.rgb-src.rgb),0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",WT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return mix(dst,src,opacity);}",XT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=2.0*src.rgb*dst.rgb;vec3 b=1.0-2.0*(1.0-src.rgb)*(1.0-dst.rgb);vec3 c=mix(a,b,step(0.5,dst.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",jT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 src2=2.0*src.rgb;vec3 c=mix(mix(src2,dst.rgb,step(0.5*dst.rgb,src.rgb)),max(src2-1.0,vec3(0.0)),step(dst.rgb,src2-1.0));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",YT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=min(dst.rgb*dst.rgb/max(1.0-src.rgb,1e-9),1.0);vec3 c=mix(a,src.rgb,step(1.0,src.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",qT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(a.x,b.y,a.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",KT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb-min(dst.rgb*src.rgb,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",ZT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 src2=2.0*src.rgb;vec3 d=dst.rgb+(src2-1.0);vec3 w=step(0.5,src.rgb);vec3 a=dst.rgb-(1.0-src2)*dst.rgb*(1.0-dst.rgb);vec3 b=mix(d*(sqrt(dst.rgb)-dst.rgb),d*dst.rgb*((16.0*dst.rgb-12.0)*dst.rgb+3.0),w*(1.0-step(0.25,dst.rgb)));vec3 c=mix(a,b,w);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",$T="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return src;}",JT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(dst.rgb-src.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",QT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=mix(max(1.0-min((1.0-dst.rgb)/(2.0*src.rgb),1.0),0.0),min(dst.rgb/(2.0*(1.0-src.rgb)),1.0),step(0.5,src.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",eE=new Map([[ct.ADD,ST],[ct.ALPHA,MT],[ct.AVERAGE,TT],[ct.COLOR,ET],[ct.COLOR_BURN,wT],[ct.COLOR_DODGE,AT],[ct.DARKEN,RT],[ct.DIFFERENCE,CT],[ct.DIVIDE,PT],[ct.DST,null],[ct.EXCLUSION,DT],[ct.HARD_LIGHT,UT],[ct.HARD_MIX,LT],[ct.HUE,IT],[ct.INVERT,FT],[ct.INVERT_RGB,NT],[ct.LIGHTEN,OT],[ct.LINEAR_BURN,BT],[ct.LINEAR_DODGE,kT],[ct.LINEAR_LIGHT,zT],[ct.LUMINOSITY,GT],[ct.MULTIPLY,HT],[ct.NEGATION,VT],[ct.NORMAL,WT],[ct.OVERLAY,XT],[ct.PIN_LIGHT,jT],[ct.REFLECT,YT],[ct.SATURATION,qT],[ct.SCREEN,KT],[ct.SOFT_LIGHT,ZT],[ct.SRC,$T],[ct.SUBTRACT,JT],[ct.VIVID_LIGHT,QT]]),tE=class extends pi{constructor(n,e=1){super(),this._blendFunction=n,this.opacity=new vt(e)}getOpacity(){return this.opacity.value}setOpacity(n){this.opacity.value=n}get blendFunction(){return this._blendFunction}set blendFunction(n){this._blendFunction=n,this.dispatchEvent({type:"change"})}getBlendFunction(){return this.blendFunction}setBlendFunction(n){this.blendFunction=n}getShaderCode(){return eE.get(this.blendFunction)}},nE=class extends pi{constructor(n,e,{attributes:t=qr.NONE,blendFunction:i=ct.NORMAL,defines:r=new Map,uniforms:s=new Map,extensions:a=null,vertexShader:o=null}={}){super(),this.name=n,this.renderer=null,this.attributes=t,this.fragmentShader=e,this.vertexShader=o,this.defines=r,this.uniforms=s,this.extensions=a,this.blendMode=new tE(i),this.blendMode.addEventListener("change",l=>this.setChanged()),this._inputColorSpace=Gs,this._outputColorSpace=Ti}get inputColorSpace(){return this._inputColorSpace}set inputColorSpace(n){this._inputColorSpace=n,this.setChanged()}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(n){this._outputColorSpace=n,this.setChanged()}set mainScene(n){}set mainCamera(n){}getName(){return this.name}setRenderer(n){this.renderer=n}getDefines(){return this.defines}getUniforms(){return this.uniforms}getExtensions(){return this.extensions}getBlendMode(){return this.blendMode}getAttributes(){return this.attributes}setAttributes(n){this.attributes=n,this.setChanged()}getFragmentShader(){return this.fragmentShader}setFragmentShader(n){this.fragmentShader=n,this.setChanged()}getVertexShader(){return this.vertexShader}setVertexShader(n){this.vertexShader=n,this.setChanged()}setChanged(){this.dispatchEvent({type:"change"})}setDepthTexture(n,e=Za){}update(n,e,t){}setSize(n,e){}initialize(n,e,t){}dispose(){for(const n of Object.keys(this)){const e=this[n];(e instanceof Jt||e instanceof $i||e instanceof $t||e instanceof mi)&&this[n].dispose()}}},Ef={MEDIUM:2,LARGE:3},iE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;void main(){vec4 sum=texture2D(inputBuffer,vUv0);sum+=texture2D(inputBuffer,vUv1);sum+=texture2D(inputBuffer,vUv2);sum+=texture2D(inputBuffer,vUv3);gl_FragColor=sum*0.25;
#include <colorspace_fragment>
}`,rE="uniform vec4 texelSize;uniform float kernel;uniform float scale;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;void main(){vec2 uv=position.xy*0.5+0.5;vec2 dUv=(texelSize.xy*vec2(kernel)+texelSize.zw)*scale;vUv0=vec2(uv.x-dUv.x,uv.y+dUv.y);vUv1=vec2(uv.x+dUv.x,uv.y+dUv.y);vUv2=vec2(uv.x+dUv.x,uv.y-dUv.y);vUv3=vec2(uv.x-dUv.x,uv.y-dUv.y);gl_Position=vec4(position.xy,1.0,1.0);}",sE=[new Float32Array([0,0]),new Float32Array([0,1,1]),new Float32Array([0,1,1,2]),new Float32Array([0,1,2,2,3]),new Float32Array([0,1,2,3,4,4,5]),new Float32Array([0,1,2,3,4,5,7,8,9,10])],aE=class extends on{constructor(n=new Ut){super({name:"KawaseBlurMaterial",uniforms:{inputBuffer:new vt(null),texelSize:new vt(new Ut),scale:new vt(1),kernel:new vt(0)},blending:Tn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:iE,vertexShader:rE}),this.setTexelSize(n.x,n.y),this.kernelSize=Ef.MEDIUM}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.inputBuffer=n}get kernelSequence(){return sE[this.kernelSize]}get scale(){return this.uniforms.scale.value}set scale(n){this.uniforms.scale.value=n}getScale(){return this.uniforms.scale.value}setScale(n){this.uniforms.scale.value=n}getKernel(){return null}get kernel(){return this.uniforms.kernel.value}set kernel(n){this.uniforms.kernel.value=n}setKernel(n){this.kernel=n}setTexelSize(n,e){this.uniforms.texelSize.value.set(n,e,n*.5,e*.5)}setSize(n,e){const t=1/n,i=1/e;this.uniforms.texelSize.value.set(t,i,t*.5,i*.5)}},oE=class extends mi{constructor({kernelSize:n=Ef.MEDIUM,resolutionScale:e=.5,width:t=Pi.AUTO_SIZE,height:i=Pi.AUTO_SIZE,resolutionX:r=t,resolutionY:s=i}={}){super("KawaseBlurPass"),this.renderTargetA=new Jt(1,1,{depthBuffer:!1}),this.renderTargetA.texture.name="Blur.Target.A",this.renderTargetB=this.renderTargetA.clone(),this.renderTargetB.texture.name="Blur.Target.B";const a=this.resolution=new Pi(this,r,s,e);a.addEventListener("change",o=>this.setSize(a.baseWidth,a.baseHeight)),this._blurMaterial=new aE,this._blurMaterial.kernelSize=n,this.copyMaterial=new mg}getResolution(){return this.resolution}get blurMaterial(){return this._blurMaterial}set blurMaterial(n){this._blurMaterial=n}get dithering(){return this.copyMaterial.dithering}set dithering(n){this.copyMaterial.dithering=n}get kernelSize(){return this.blurMaterial.kernelSize}set kernelSize(n){this.blurMaterial.kernelSize=n}get width(){return this.resolution.width}set width(n){this.resolution.preferredWidth=n}get height(){return this.resolution.height}set height(n){this.resolution.preferredHeight=n}get scale(){return this.blurMaterial.scale}set scale(n){this.blurMaterial.scale=n}getScale(){return this.blurMaterial.scale}setScale(n){this.blurMaterial.scale=n}getKernelSize(){return this.kernelSize}setKernelSize(n){this.kernelSize=n}getResolutionScale(){return this.resolution.scale}setResolutionScale(n){this.resolution.scale=n}render(n,e,t,i,r){const s=this.scene,a=this.camera,o=this.renderTargetA,l=this.renderTargetB,c=this.blurMaterial,u=c.kernelSequence;let f=e;this.fullscreenMaterial=c;for(let h=0,d=u.length;h<d;++h){const m=(h&1)===0?o:l;c.kernel=u[h],c.inputBuffer=f.texture,n.setRenderTarget(m),n.render(s,a),f=m}this.fullscreenMaterial=this.copyMaterial,this.copyMaterial.inputBuffer=f.texture,n.setRenderTarget(this.renderToScreen?null:t),n.render(s,a)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e);const i=t.width,r=t.height;this.renderTargetA.setSize(i,r),this.renderTargetB.setSize(i,r),this.blurMaterial.setSize(n,e)}initialize(n,e,t){t!==void 0&&(this.renderTargetA.texture.type=t,this.renderTargetB.texture.type=t,t!==Yt?(this.blurMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1",this.copyMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1"):n!==null&&n.outputColorSpace===Et&&(this.renderTargetA.texture.colorSpace=Et,this.renderTargetB.texture.colorSpace=Et))}static get AUTO_SIZE(){return Pi.AUTO_SIZE}},lE=`#include <common>
#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
#ifdef RANGE
uniform vec2 range;
#elif defined(THRESHOLD)
uniform float threshold;uniform float smoothing;
#endif
varying vec2 vUv;void main(){vec4 texel=texture2D(inputBuffer,vUv);float l=luminance(texel.rgb);float mask=1.0;
#ifdef RANGE
float low=step(range.x,l);float high=step(l,range.y);mask=low*high;
#elif defined(THRESHOLD)
mask=smoothstep(threshold,threshold+smoothing,l);
#endif
#ifdef COLOR
gl_FragColor=texel*mask;
#else
gl_FragColor=vec4(l*mask);
#endif
}`,cE=class extends on{constructor(n=!1,e=null){super({name:"LuminanceMaterial",defines:{THREE_REVISION:Ka.replace(/\D+/g,"")},uniforms:{inputBuffer:new vt(null),threshold:new vt(0),smoothing:new vt(1),range:new vt(null)},blending:Tn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:lE,vertexShader:pg}),this.colorOutput=n,this.luminanceRange=e}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.uniforms.inputBuffer.value=n}get threshold(){return this.uniforms.threshold.value}set threshold(n){this.smoothing>0||n>0?this.defines.THRESHOLD="1":delete this.defines.THRESHOLD,this.uniforms.threshold.value=n}getThreshold(){return this.threshold}setThreshold(n){this.threshold=n}get smoothing(){return this.uniforms.smoothing.value}set smoothing(n){this.threshold>0||n>0?this.defines.THRESHOLD="1":delete this.defines.THRESHOLD,this.uniforms.smoothing.value=n}getSmoothingFactor(){return this.smoothing}setSmoothingFactor(n){this.smoothing=n}get useThreshold(){return this.threshold>0||this.smoothing>0}set useThreshold(n){}get colorOutput(){return this.defines.COLOR!==void 0}set colorOutput(n){n?this.defines.COLOR="1":delete this.defines.COLOR,this.needsUpdate=!0}isColorOutputEnabled(n){return this.colorOutput}setColorOutputEnabled(n){this.colorOutput=n}get useRange(){return this.luminanceRange!==null}set useRange(n){this.luminanceRange=null}get luminanceRange(){return this.uniforms.range.value}set luminanceRange(n){n!==null?this.defines.RANGE="1":delete this.defines.RANGE,this.uniforms.range.value=n,this.needsUpdate=!0}getLuminanceRange(){return this.luminanceRange}setLuminanceRange(n){this.luminanceRange=n}},uE=class extends mi{constructor({renderTarget:n,luminanceRange:e,colorOutput:t,resolutionScale:i=1,width:r=Pi.AUTO_SIZE,height:s=Pi.AUTO_SIZE,resolutionX:a=r,resolutionY:o=s}={}){super("LuminancePass"),this.fullscreenMaterial=new cE(t,e),this.needsSwap=!1,this.renderTarget=n,this.renderTarget===void 0&&(this.renderTarget=new Jt(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="LuminancePass.Target");const l=this.resolution=new Pi(this,a,o,i);l.addEventListener("change",c=>this.setSize(l.baseWidth,l.baseHeight))}get texture(){return this.renderTarget.texture}getTexture(){return this.renderTarget.texture}getResolution(){return this.resolution}render(n,e,t,i,r){const s=this.fullscreenMaterial;s.inputBuffer=e.texture,n.setRenderTarget(this.renderToScreen?null:this.renderTarget),n.render(this.scene,this.camera)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e),this.renderTarget.setSize(t.width,t.height)}initialize(n,e,t){t!==void 0&&t!==Yt&&(this.renderTarget.texture.type=t,this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1")}},hE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
#define WEIGHT_INNER 0.125
#define WEIGHT_OUTER 0.05556
varying vec2 vUv;varying vec2 vUv00;varying vec2 vUv01;varying vec2 vUv02;varying vec2 vUv03;varying vec2 vUv04;varying vec2 vUv05;varying vec2 vUv06;varying vec2 vUv07;varying vec2 vUv08;varying vec2 vUv09;varying vec2 vUv10;varying vec2 vUv11;float clampToBorder(const in vec2 uv){return float(uv.s>=0.0&&uv.s<=1.0&&uv.t>=0.0&&uv.t<=1.0);}void main(){vec4 c=vec4(0.0);vec4 w=WEIGHT_INNER*vec4(clampToBorder(vUv00),clampToBorder(vUv01),clampToBorder(vUv02),clampToBorder(vUv03));c+=w.x*texture2D(inputBuffer,vUv00);c+=w.y*texture2D(inputBuffer,vUv01);c+=w.z*texture2D(inputBuffer,vUv02);c+=w.w*texture2D(inputBuffer,vUv03);w=WEIGHT_OUTER*vec4(clampToBorder(vUv04),clampToBorder(vUv05),clampToBorder(vUv06),clampToBorder(vUv07));c+=w.x*texture2D(inputBuffer,vUv04);c+=w.y*texture2D(inputBuffer,vUv05);c+=w.z*texture2D(inputBuffer,vUv06);c+=w.w*texture2D(inputBuffer,vUv07);w=WEIGHT_OUTER*vec4(clampToBorder(vUv08),clampToBorder(vUv09),clampToBorder(vUv10),clampToBorder(vUv11));c+=w.x*texture2D(inputBuffer,vUv08);c+=w.y*texture2D(inputBuffer,vUv09);c+=w.z*texture2D(inputBuffer,vUv10);c+=w.w*texture2D(inputBuffer,vUv11);c+=WEIGHT_OUTER*texture2D(inputBuffer,vUv);gl_FragColor=c;
#include <colorspace_fragment>
}`,fE="uniform vec2 texelSize;varying vec2 vUv;varying vec2 vUv00;varying vec2 vUv01;varying vec2 vUv02;varying vec2 vUv03;varying vec2 vUv04;varying vec2 vUv05;varying vec2 vUv06;varying vec2 vUv07;varying vec2 vUv08;varying vec2 vUv09;varying vec2 vUv10;varying vec2 vUv11;void main(){vUv=position.xy*0.5+0.5;vUv00=vUv+texelSize*vec2(-1.0,1.0);vUv01=vUv+texelSize*vec2(1.0,1.0);vUv02=vUv+texelSize*vec2(-1.0,-1.0);vUv03=vUv+texelSize*vec2(1.0,-1.0);vUv04=vUv+texelSize*vec2(-2.0,2.0);vUv05=vUv+texelSize*vec2(0.0,2.0);vUv06=vUv+texelSize*vec2(2.0,2.0);vUv07=vUv+texelSize*vec2(-2.0,0.0);vUv08=vUv+texelSize*vec2(2.0,0.0);vUv09=vUv+texelSize*vec2(-2.0,-2.0);vUv10=vUv+texelSize*vec2(0.0,-2.0);vUv11=vUv+texelSize*vec2(2.0,-2.0);gl_Position=vec4(position.xy,1.0,1.0);}",dE=class extends on{constructor(){super({name:"DownsamplingMaterial",uniforms:{inputBuffer:new vt(null),texelSize:new vt(new Xe)},blending:Tn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:hE,vertexShader:fE})}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setSize(n,e){this.uniforms.texelSize.value.set(1/n,1/e)}},pE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;uniform mediump sampler2D supportBuffer;
#else
uniform lowp sampler2D inputBuffer;uniform lowp sampler2D supportBuffer;
#endif
uniform float radius;varying vec2 vUv;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;varying vec2 vUv4;varying vec2 vUv5;varying vec2 vUv6;varying vec2 vUv7;void main(){vec4 c=vec4(0.0);c+=texture2D(inputBuffer,vUv0)*0.0625;c+=texture2D(inputBuffer,vUv1)*0.125;c+=texture2D(inputBuffer,vUv2)*0.0625;c+=texture2D(inputBuffer,vUv3)*0.125;c+=texture2D(inputBuffer,vUv)*0.25;c+=texture2D(inputBuffer,vUv4)*0.125;c+=texture2D(inputBuffer,vUv5)*0.0625;c+=texture2D(inputBuffer,vUv6)*0.125;c+=texture2D(inputBuffer,vUv7)*0.0625;vec4 baseColor=texture2D(supportBuffer,vUv);gl_FragColor=mix(baseColor,c,radius);
#include <colorspace_fragment>
}`,mE="uniform vec2 texelSize;varying vec2 vUv;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;varying vec2 vUv4;varying vec2 vUv5;varying vec2 vUv6;varying vec2 vUv7;void main(){vUv=position.xy*0.5+0.5;vUv0=vUv+texelSize*vec2(-1.0,1.0);vUv1=vUv+texelSize*vec2(0.0,1.0);vUv2=vUv+texelSize*vec2(1.0,1.0);vUv3=vUv+texelSize*vec2(-1.0,0.0);vUv4=vUv+texelSize*vec2(1.0,0.0);vUv5=vUv+texelSize*vec2(-1.0,-1.0);vUv6=vUv+texelSize*vec2(0.0,-1.0);vUv7=vUv+texelSize*vec2(1.0,-1.0);gl_Position=vec4(position.xy,1.0,1.0);}",gE=class extends on{constructor(){super({name:"UpsamplingMaterial",uniforms:{inputBuffer:new vt(null),supportBuffer:new vt(null),texelSize:new vt(new Xe),radius:new vt(.85)},blending:Tn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:pE,vertexShader:mE})}set inputBuffer(n){this.uniforms.inputBuffer.value=n}set supportBuffer(n){this.uniforms.supportBuffer.value=n}get radius(){return this.uniforms.radius.value}set radius(n){this.uniforms.radius.value=n}setSize(n,e){this.uniforms.texelSize.value.set(1/n,1/e)}},_E=class extends mi{constructor(){super("MipmapBlurPass"),this.needsSwap=!1,this.renderTarget=new Jt(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="Upsampling.Mipmap0",this.downsamplingMipmaps=[],this.upsamplingMipmaps=[],this.downsamplingMaterial=new dE,this.upsamplingMaterial=new gE,this.resolution=new Xe}get texture(){return this.renderTarget.texture}get levels(){return this.downsamplingMipmaps.length}set levels(n){if(this.levels!==n){const e=this.renderTarget;this.dispose(),this.downsamplingMipmaps=[],this.upsamplingMipmaps=[];for(let t=0;t<n;++t){const i=e.clone();i.texture.name="Downsampling.Mipmap"+t,this.downsamplingMipmaps.push(i)}this.upsamplingMipmaps.push(e);for(let t=1,i=n-1;t<i;++t){const r=e.clone();r.texture.name="Upsampling.Mipmap"+t,this.upsamplingMipmaps.push(r)}this.setSize(this.resolution.x,this.resolution.y)}}get radius(){return this.upsamplingMaterial.radius}set radius(n){this.upsamplingMaterial.radius=n}render(n,e,t,i,r){const{scene:s,camera:a}=this,{downsamplingMaterial:o,upsamplingMaterial:l}=this,{downsamplingMipmaps:c,upsamplingMipmaps:u}=this;let f=e;this.fullscreenMaterial=o;for(let h=0,d=c.length;h<d;++h){const m=c[h];o.setSize(f.width,f.height),o.inputBuffer=f.texture,n.setRenderTarget(m),n.render(s,a),f=m}this.fullscreenMaterial=l;for(let h=u.length-1;h>=0;--h){const d=u[h];l.setSize(f.width,f.height),l.inputBuffer=f.texture,l.supportBuffer=c[h].texture,n.setRenderTarget(d),n.render(s,a),f=d}}setSize(n,e){const t=this.resolution;t.set(n,e);let i=t.width,r=t.height;for(let s=0,a=this.downsamplingMipmaps.length;s<a;++s)i=Math.round(i*.5),r=Math.round(r*.5),this.downsamplingMipmaps[s].setSize(i,r),s<this.upsamplingMipmaps.length&&this.upsamplingMipmaps[s].setSize(i,r)}initialize(n,e,t){if(t!==void 0){const i=this.downsamplingMipmaps.concat(this.upsamplingMipmaps);for(const r of i)r.texture.type=t;if(t!==Yt)this.downsamplingMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1",this.upsamplingMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1";else if(n!==null&&n.outputColorSpace===Et)for(const r of i)r.texture.colorSpace=Et}}dispose(){super.dispose();for(const n of this.downsamplingMipmaps.concat(this.upsamplingMipmaps))n.dispose()}},vE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D map;
#else
uniform lowp sampler2D map;
#endif
uniform float intensity;void mainImage(const in vec4 inputColor,const in vec2 uv,out vec4 outputColor){outputColor=texture2D(map,uv)*intensity;}`,xE=class extends nE{constructor({blendFunction:n=ct.SCREEN,luminanceThreshold:e=1,luminanceSmoothing:t=.03,mipmapBlur:i=!0,intensity:r=1,radius:s=.85,levels:a=8,kernelSize:o=Ef.LARGE,resolutionScale:l=.5,width:c=Pi.AUTO_SIZE,height:u=Pi.AUTO_SIZE,resolutionX:f=c,resolutionY:h=u}={}){super("BloomEffect",vE,{blendFunction:n,uniforms:new Map([["map",new vt(null)],["intensity",new vt(r)]])}),this.renderTarget=new Jt(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="Bloom.Target",this.blurPass=new oE({kernelSize:o}),this.luminancePass=new uE({colorOutput:!0}),this.luminanceMaterial.threshold=e,this.luminanceMaterial.smoothing=t,this.mipmapBlurPass=new _E,this.mipmapBlurPass.enabled=i,this.mipmapBlurPass.radius=s,this.mipmapBlurPass.levels=a,this.uniforms.get("map").value=i?this.mipmapBlurPass.texture:this.renderTarget.texture;const d=this.resolution=new Pi(this,f,h,l);d.addEventListener("change",m=>this.setSize(d.baseWidth,d.baseHeight))}get texture(){return this.mipmapBlurPass.enabled?this.mipmapBlurPass.texture:this.renderTarget.texture}getTexture(){return this.texture}getResolution(){return this.resolution}getBlurPass(){return this.blurPass}getLuminancePass(){return this.luminancePass}get luminanceMaterial(){return this.luminancePass.fullscreenMaterial}getLuminanceMaterial(){return this.luminancePass.fullscreenMaterial}get width(){return this.resolution.width}set width(n){this.resolution.preferredWidth=n}get height(){return this.resolution.height}set height(n){this.resolution.preferredHeight=n}get dithering(){return this.blurPass.dithering}set dithering(n){this.blurPass.dithering=n}get kernelSize(){return this.blurPass.kernelSize}set kernelSize(n){this.blurPass.kernelSize=n}get distinction(){return console.warn(this.name,"distinction was removed"),1}set distinction(n){console.warn(this.name,"distinction was removed")}get intensity(){return this.uniforms.get("intensity").value}set intensity(n){this.uniforms.get("intensity").value=n}getIntensity(){return this.intensity}setIntensity(n){this.intensity=n}getResolutionScale(){return this.resolution.scale}setResolutionScale(n){this.resolution.scale=n}update(n,e,t){const i=this.renderTarget,r=this.luminancePass;r.enabled?(r.render(n,e),this.mipmapBlurPass.enabled?this.mipmapBlurPass.render(n,r.renderTarget):this.blurPass.render(n,r.renderTarget,i)):this.mipmapBlurPass.enabled?this.mipmapBlurPass.render(n,e):this.blurPass.render(n,e,i)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e),this.renderTarget.setSize(t.width,t.height),this.blurPass.resolution.copy(t),this.luminancePass.setSize(n,e),this.mipmapBlurPass.setSize(n,e)}initialize(n,e,t){this.blurPass.initialize(n,e,t),this.luminancePass.initialize(n,e,t),this.mipmapBlurPass.initialize(n,e,t),t!==void 0&&(this.renderTarget.texture.type=t,n!==null&&n.outputColorSpace===Et&&(this.renderTarget.texture.colorSpace=Et))}},yE=class extends mi{constructor(n,e,t=null){super("RenderPass",n,e),this.needsSwap=!1,this.needsDepthBlit=!0,this.clearPass=new gg,this.overrideMaterialManager=t===null?null:new Vp(t),this.ignoreBackground=!1,this.skipShadowMapUpdate=!1,this.selection=null}set mainScene(n){this.scene=n}set mainCamera(n){this.camera=n}get renderToScreen(){return super.renderToScreen}set renderToScreen(n){super.renderToScreen=n,this.clearPass.renderToScreen=n}get overrideMaterial(){const n=this.overrideMaterialManager;return n!==null?n.material:null}set overrideMaterial(n){const e=this.overrideMaterialManager;n!==null?e!==null?e.setMaterial(n):this.overrideMaterialManager=new Vp(n):e!==null&&(e.dispose(),this.overrideMaterialManager=null)}getOverrideMaterial(){return this.overrideMaterial}setOverrideMaterial(n){this.overrideMaterial=n}get clear(){return this.clearPass.enabled}set clear(n){this.clearPass.enabled=n}getSelection(){return this.selection}setSelection(n){this.selection=n}isBackgroundDisabled(){return this.ignoreBackground}setBackgroundDisabled(n){this.ignoreBackground=n}isShadowMapDisabled(){return this.skipShadowMapUpdate}setShadowMapDisabled(n){this.skipShadowMapUpdate=n}getClearPass(){return this.clearPass}render(n,e,t,i,r){const s=this.scene,a=this.camera,o=this.selection,l=a.layers.mask,c=s.background,u=n.shadowMap.autoUpdate,f=this.renderToScreen?null:e;o!==null&&a.layers.set(o.getLayer()),this.skipShadowMapUpdate&&(n.shadowMap.autoUpdate=!1),(this.ignoreBackground||this.clearPass.overrideClearColor!==null)&&(s.background=null),this.clearPass.enabled&&this.clearPass.render(n,e),n.setRenderTarget(f),this.overrideMaterialManager!==null?this.overrideMaterialManager.render(n,s,a):n.render(s,a),a.layers.mask=l,s.background=c,n.shadowMap.autoUpdate=u}},bE=`#include <common>
#include <packing>
#include <dithering_pars_fragment>
#define packFloatToRGBA(v) packDepthToRGBA(v)
#define unpackRGBAToFloat(v) unpackRGBAToDepth(v)
#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
#if DEPTH_PACKING == 3201
uniform lowp sampler2D depthBuffer;
#elif defined(GL_FRAGMENT_PRECISION_HIGH)
uniform highp sampler2D depthBuffer;
#else
uniform mediump sampler2D depthBuffer;
#endif
uniform vec2 resolution;uniform vec2 texelSize;uniform float cameraNear;uniform float cameraFar;uniform float aspect;uniform float time;varying vec2 vUv;vec4 sRGBToLinear(const in vec4 value){return vec4(mix(pow(value.rgb*0.9478672986+vec3(0.0521327014),vec3(2.4)),value.rgb*0.0773993808,vec3(lessThanEqual(value.rgb,vec3(0.04045)))),value.a);}float readDepth(const in vec2 uv){
#if DEPTH_PACKING == 3201
float depth=unpackRGBAToDepth(texture2D(depthBuffer,uv));
#else
float depth=texture2D(depthBuffer,uv).r;
#endif
#if defined(USE_LOGARITHMIC_DEPTH_BUFFER) || defined(LOG_DEPTH)
float d=pow(2.0,depth*log2(cameraFar+1.0))-1.0;float a=cameraFar/(cameraFar-cameraNear);float b=cameraFar*cameraNear/(cameraNear-cameraFar);depth=a+b/d;
#elif defined(USE_REVERSED_DEPTH_BUFFER)
depth=1.0-depth;
#endif
return depth;}float getViewZ(const in float depth){
#ifdef PERSPECTIVE_CAMERA
return perspectiveDepthToViewZ(depth,cameraNear,cameraFar);
#else
return orthographicDepthToViewZ(depth,cameraNear,cameraFar);
#endif
}vec3 RGBToHCV(const in vec3 RGB){vec4 P=mix(vec4(RGB.bg,-1.0,2.0/3.0),vec4(RGB.gb,0.0,-1.0/3.0),step(RGB.b,RGB.g));vec4 Q=mix(vec4(P.xyw,RGB.r),vec4(RGB.r,P.yzx),step(P.x,RGB.r));float C=Q.x-min(Q.w,Q.y);float H=abs((Q.w-Q.y)/(6.0*C+EPSILON)+Q.z);return vec3(H,C,Q.x);}vec3 RGBToHSL(const in vec3 RGB){vec3 HCV=RGBToHCV(RGB);float L=HCV.z-HCV.y*0.5;float S=HCV.y/(1.0-abs(L*2.0-1.0)+EPSILON);return vec3(HCV.x,S,L);}vec3 HueToRGB(const in float H){float R=abs(H*6.0-3.0)-1.0;float G=2.0-abs(H*6.0-2.0);float B=2.0-abs(H*6.0-4.0);return clamp(vec3(R,G,B),0.0,1.0);}vec3 HSLToRGB(const in vec3 HSL){vec3 RGB=HueToRGB(HSL.x);float C=(1.0-abs(2.0*HSL.z-1.0))*HSL.y;return(RGB-0.5)*C+HSL.z;}FRAGMENT_HEAD void main(){FRAGMENT_MAIN_UV vec4 color0=texture2D(inputBuffer,UV);vec4 color1=vec4(0.0);FRAGMENT_MAIN_IMAGE color0.a=clamp(color0.a,0.0,1.0);gl_FragColor=color0;
#ifdef ENCODE_OUTPUT
#include <colorspace_fragment>
#endif
#include <dithering_fragment>
}`,SE="uniform vec2 resolution;uniform vec2 texelSize;uniform float cameraNear;uniform float cameraFar;uniform float aspect;uniform float time;varying vec2 vUv;VERTEX_HEAD void main(){vUv=position.xy*0.5+0.5;VERTEX_MAIN_SUPPORT gl_Position=vec4(position.xy,1.0,1.0);}",ME=class extends on{constructor(n,e,t,i,r=!1){super({name:"EffectMaterial",defines:{THREE_REVISION:Ka.replace(/\D+/g,""),DEPTH_PACKING:"0",ENCODE_OUTPUT:"1"},uniforms:{inputBuffer:new vt(null),depthBuffer:new vt(null),resolution:new vt(new Xe),texelSize:new vt(new Xe),cameraNear:new vt(.3),cameraFar:new vt(1e3),aspect:new vt(1),time:new vt(0)},blending:Tn,toneMapped:!1,depthWrite:!1,depthTest:!1,dithering:r}),n&&this.setShaderParts(n),e&&this.setDefines(e),t&&this.setUniforms(t),this.copyCameraSettings(i)}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.uniforms.inputBuffer.value=n}get depthBuffer(){return this.uniforms.depthBuffer.value}set depthBuffer(n){this.uniforms.depthBuffer.value=n}get depthPacking(){return Number(this.defines.DEPTH_PACKING)}set depthPacking(n){this.defines.DEPTH_PACKING=n.toFixed(0),this.needsUpdate=!0}setDepthBuffer(n,e=Za){this.depthBuffer=n,this.depthPacking=e}setShaderData(n){this.setShaderParts(n.shaderParts),this.setDefines(n.defines),this.setUniforms(n.uniforms),this.setExtensions(n.extensions)}setShaderParts(n){return this.fragmentShader=bE.replace(gt.FRAGMENT_HEAD,n.get(gt.FRAGMENT_HEAD)||"").replace(gt.FRAGMENT_MAIN_UV,n.get(gt.FRAGMENT_MAIN_UV)||"").replace(gt.FRAGMENT_MAIN_IMAGE,n.get(gt.FRAGMENT_MAIN_IMAGE)||""),this.vertexShader=SE.replace(gt.VERTEX_HEAD,n.get(gt.VERTEX_HEAD)||"").replace(gt.VERTEX_MAIN_SUPPORT,n.get(gt.VERTEX_MAIN_SUPPORT)||""),this.needsUpdate=!0,this}setDefines(n){for(const e of n.entries())this.defines[e[0]]=e[1];return this.needsUpdate=!0,this}setUniforms(n){for(const e of n.entries())this.uniforms[e[0]]=e[1];return this}setExtensions(n){this.extensions={};for(const e of n)this.extensions[e]=!0;return this}get encodeOutput(){return this.defines.ENCODE_OUTPUT!==void 0}set encodeOutput(n){this.encodeOutput!==n&&(n?this.defines.ENCODE_OUTPUT="1":delete this.defines.ENCODE_OUTPUT,this.needsUpdate=!0)}isOutputEncodingEnabled(n){return this.encodeOutput}setOutputEncodingEnabled(n){this.encodeOutput=n}get time(){return this.uniforms.time.value}set time(n){this.uniforms.time.value=n}setDeltaTime(n){this.uniforms.time.value+=n}adoptCameraSettings(n){this.copyCameraSettings(n)}copyCameraSettings(n){n&&(this.uniforms.cameraNear.value=n.near,this.uniforms.cameraFar.value=n.far,n instanceof Gn?this.defines.PERSPECTIVE_CAMERA="1":delete this.defines.PERSPECTIVE_CAMERA,this.needsUpdate=!0)}setSize(n,e){const t=this.uniforms;t.resolution.value.set(n,e),t.texelSize.value.set(1/n,1/e),t.aspect.value=n/e}static get Section(){return gt}};function Wp(n,e,t){for(const i of e){const r="$1"+n+i.charAt(0).toUpperCase()+i.slice(1),s=new RegExp("([^\\.])(\\b"+i+"\\b)","g");for(const a of t.entries())a[1]!==null&&t.set(a[0],a[1].replace(s,r))}}function TE(n,e,t){let i=e.getFragmentShader(),r=e.getVertexShader();const s=i!==void 0&&/mainImage/.test(i),a=i!==void 0&&/mainUv/.test(i);if(t.attributes|=e.getAttributes(),i===void 0)throw new Error(`Missing fragment shader (${e.name})`);if(a&&(t.attributes&qr.CONVOLUTION)!==0)throw new Error(`Effects that transform UVs are incompatible with convolution effects (${e.name})`);if(!s&&!a)throw new Error(`Could not find mainImage or mainUv function (${e.name})`);{const o=/\w+\s+(\w+)\([\w\s,]*\)\s*{/g,l=t.shaderParts;let c=l.get(gt.FRAGMENT_HEAD)||"",u=l.get(gt.FRAGMENT_MAIN_UV)||"",f=l.get(gt.FRAGMENT_MAIN_IMAGE)||"",h=l.get(gt.VERTEX_HEAD)||"",d=l.get(gt.VERTEX_MAIN_SUPPORT)||"";const m=new Set,g=new Set;if(a&&(u+=`	${n}MainUv(UV);
`,t.uvTransformation=!0),r!==null&&/mainSupport/.test(r)){const v=/mainSupport *\([\w\s]*?uv\s*?\)/.test(r);d+=`	${n}MainSupport(`,d+=v?`vUv);
`:`);
`;for(const S of r.matchAll(/(?:varying\s+\w+\s+([\S\s]*?);)/g))for(const y of S[1].split(/\s*,\s*/))t.varyings.add(y),m.add(y),g.add(y);for(const S of r.matchAll(o))g.add(S[1])}for(const v of i.matchAll(o))g.add(v[1]);for(const v of e.defines.keys())g.add(v.replace(/\([\w\s,]*\)/g,""));for(const v of e.uniforms.keys())g.add(v);g.delete("while"),g.delete("for"),g.delete("if"),e.uniforms.forEach((v,S)=>t.uniforms.set(n+S.charAt(0).toUpperCase()+S.slice(1),v)),e.defines.forEach((v,S)=>t.defines.set(n+S.charAt(0).toUpperCase()+S.slice(1),v));const p=new Map([["fragment",i],["vertex",r]]);Wp(n,g,t.defines),Wp(n,g,p),i=p.get("fragment"),r=p.get("vertex");const _=e.blendMode;if(t.blendModes.set(_.blendFunction,_),s){e.inputColorSpace!==null&&e.inputColorSpace!==t.colorSpace&&(f+=e.inputColorSpace===Et?`color0 = sRGBTransferOETF(color0);
	`:`color0 = sRGBToLinear(color0);
	`),e.outputColorSpace!==Ti?t.colorSpace=e.outputColorSpace:e.inputColorSpace!==null&&(t.colorSpace=e.inputColorSpace);const v=/MainImage *\([\w\s,]*?depth[\w\s,]*?\)/;f+=`${n}MainImage(color0, UV, `,(t.attributes&qr.DEPTH)!==0&&v.test(i)&&(f+="depth, ",t.readDepth=!0),f+=`color1);
	`;const S=n+"BlendOpacity";t.uniforms.set(S,_.opacity),f+=`color0 = blend${_.blendFunction}(color0, color1, ${S});

	`,c+=`uniform float ${S};

`}if(c+=i+`
`,r!==null&&(h+=r+`
`),l.set(gt.FRAGMENT_HEAD,c),l.set(gt.FRAGMENT_MAIN_UV,u),l.set(gt.FRAGMENT_MAIN_IMAGE,f),l.set(gt.VERTEX_HEAD,h),l.set(gt.VERTEX_MAIN_SUPPORT,d),e.extensions!==null)for(const v of e.extensions)t.extensions.add(v)}}var EE=class extends mi{constructor(n,...e){super("EffectPass"),this.fullscreenMaterial=new ME(null,null,null,n),this.listener=t=>this.handleEvent(t),this.effects=[],this.setEffects(e),this.skipRendering=!1,this.minTime=1,this.maxTime=Number.POSITIVE_INFINITY,this.timeScale=1}set mainScene(n){for(const e of this.effects)e.mainScene=n}set mainCamera(n){this.fullscreenMaterial.copyCameraSettings(n);for(const e of this.effects)e.mainCamera=n}get encodeOutput(){return this.fullscreenMaterial.encodeOutput}set encodeOutput(n){this.fullscreenMaterial.encodeOutput=n}get dithering(){return this.fullscreenMaterial.dithering}set dithering(n){const e=this.fullscreenMaterial;e.dithering=n,e.needsUpdate=!0}setEffects(n){for(const e of this.effects)e.removeEventListener("change",this.listener);this.effects=n.sort((e,t)=>t.attributes-e.attributes);for(const e of this.effects)e.addEventListener("change",this.listener)}updateMaterial(){const n=new bT;let e=0;for(const a of this.effects)if(a.blendMode.blendFunction===ct.DST)n.attributes|=a.getAttributes()&qr.DEPTH;else{if((n.attributes&a.getAttributes()&qr.CONVOLUTION)!==0)throw new Error(`Convolution effects cannot be merged (${a.name})`);TE("e"+e++,a,n)}let t=n.shaderParts.get(gt.FRAGMENT_HEAD),i=n.shaderParts.get(gt.FRAGMENT_MAIN_IMAGE),r=n.shaderParts.get(gt.FRAGMENT_MAIN_UV);const s=/\bblend\b/g;for(const a of n.blendModes.values())t+=a.getShaderCode().replace(s,`blend${a.blendFunction}`)+`
`;(n.attributes&qr.DEPTH)!==0?(n.readDepth&&(i=`float depth = readDepth(UV);

	`+i),this.needsDepthTexture=this.getDepthTexture()===null):this.needsDepthTexture=!1,n.colorSpace===Et&&(i+=`color0 = sRGBToLinear(color0);
	`),n.uvTransformation?(r=`vec2 transformedUv = vUv;
`+r,n.defines.set("UV","transformedUv")):n.defines.set("UV","vUv"),n.shaderParts.set(gt.FRAGMENT_HEAD,t),n.shaderParts.set(gt.FRAGMENT_MAIN_IMAGE,i),n.shaderParts.set(gt.FRAGMENT_MAIN_UV,r);for(const[a,o]of n.shaderParts)o!==null&&n.shaderParts.set(a,o.trim().replace(/^#/,`
#`));this.skipRendering=e===0,this.needsSwap=!this.skipRendering,this.fullscreenMaterial.setShaderData(n)}recompile(){this.updateMaterial()}getDepthTexture(){return this.fullscreenMaterial.depthBuffer}setDepthTexture(n,e=Za){this.fullscreenMaterial.depthBuffer=n,this.fullscreenMaterial.depthPacking=e;for(const t of this.effects)t.setDepthTexture(n,e)}render(n,e,t,i,r){for(const s of this.effects)s.update(n,e,i);if(!this.skipRendering||this.renderToScreen){const s=this.fullscreenMaterial;s.inputBuffer=e.texture,s.time+=i*this.timeScale,n.setRenderTarget(this.renderToScreen?null:t),n.render(this.scene,this.camera)}}setSize(n,e){this.fullscreenMaterial.setSize(n,e);for(const t of this.effects)t.setSize(n,e)}initialize(n,e,t){this.renderer=n;for(const i of this.effects)i.initialize(n,e,t);this.updateMaterial(),t!==void 0&&t!==Yt&&(this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1")}dispose(){super.dispose();for(const n of this.effects)n.removeEventListener("change",this.listener),n.dispose()}handleEvent(n){switch(n.type){case"change":this.recompile();break}}};const _g=(n,e)=>{if(typeof n=="number"){if(e===3)return{mode:"rgb",r:(n>>8&15|n>>4&240)/255,g:(n>>4&15|n&240)/255,b:(n&15|n<<4&240)/255};if(e===4)return{mode:"rgb",r:(n>>12&15|n>>8&240)/255,g:(n>>8&15|n>>4&240)/255,b:(n>>4&15|n&240)/255,alpha:(n&15|n<<4&240)/255};if(e===6)return{mode:"rgb",r:(n>>16&255)/255,g:(n>>8&255)/255,b:(n&255)/255};if(e===8)return{mode:"rgb",r:(n>>24&255)/255,g:(n>>16&255)/255,b:(n>>8&255)/255,alpha:(n&255)/255}}},wE={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},AE=n=>_g(wE[n.toLowerCase()],6),RE=/^#?([0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{4}|[0-9a-f]{3})$/i,CE=n=>{let e;return(e=n.match(RE))?_g(parseInt(e[1],16),e[1].length):void 0},yr="([+-]?\\d*\\.?\\d+(?:[eE][+-]?\\d+)?)",Ba=`${yr}%`,wf=`(?:${yr}%|${yr})`,PE=`(?:${yr}(deg|grad|rad|turn)|${yr})`,qs="\\s*,\\s*",DE=new RegExp(`^rgba?\\(\\s*${yr}${qs}${yr}${qs}${yr}\\s*(?:,\\s*${wf}\\s*)?\\)$`),UE=new RegExp(`^rgba?\\(\\s*${Ba}${qs}${Ba}${qs}${Ba}\\s*(?:,\\s*${wf}\\s*)?\\)$`),LE=n=>{let e={mode:"rgb"},t;if(t=n.match(DE))t[1]!==void 0&&(e.r=t[1]/255),t[2]!==void 0&&(e.g=t[2]/255),t[3]!==void 0&&(e.b=t[3]/255);else if(t=n.match(UE))t[1]!==void 0&&(e.r=t[1]/100),t[2]!==void 0&&(e.g=t[2]/100),t[3]!==void 0&&(e.b=t[3]/100);else return;return t[4]!==void 0?e.alpha=Math.max(0,Math.min(1,t[4]/100)):t[5]!==void 0&&(e.alpha=Math.max(0,Math.min(1,+t[5]))),e},IE=(n,e)=>n===void 0?void 0:typeof n!="object"?VE(n):n.mode!==void 0?n:e?{...n,mode:e}:void 0,Af=(n="rgb")=>e=>(e=IE(e,n))!==void 0?e.mode===n?e:Ai[e.mode][n]?Ai[e.mode][n](e):n==="rgb"?Ai[e.mode].rgb(e):Ai.rgb[n](Ai[e.mode].rgb(e)):void 0,Ai={},vg={},El=[],xg={},FE=n=>n,yt=n=>(Ai[n.mode]={...Ai[n.mode],...n.toMode},Object.keys(n.fromMode||{}).forEach(e=>{Ai[e]||(Ai[e]={}),Ai[e][n.mode]=n.fromMode[e]}),n.ranges||(n.ranges={}),n.difference||(n.difference={}),n.channels.forEach(e=>{if(n.ranges[e]===void 0&&(n.ranges[e]=[0,1]),!n.interpolate[e])throw new Error(`Missing interpolator for: ${e}`);typeof n.interpolate[e]=="function"&&(n.interpolate[e]={use:n.interpolate[e]}),n.interpolate[e].fixup||(n.interpolate[e].fixup=FE)}),vg[n.mode]=n,(n.parse||[]).forEach(e=>{NE(e,n.mode)}),Af(n.mode)),yg=n=>vg[n],NE=(n,e)=>{if(typeof n=="string"){if(!e)throw new Error("'mode' required when 'parser' is a string");xg[n]=e}else typeof n=="function"&&El.indexOf(n)<0&&El.push(n)},kh=/[^\x00-\x7F]|[a-zA-Z_]/,OE=/[^\x00-\x7F]|[-\w]/,Ce={Function:"function",Ident:"ident",Number:"number",Percentage:"percentage",ParenClose:")",None:"none",Hue:"hue",Alpha:"alpha"};let Qe=0;function Ho(n){let e=n[Qe],t=n[Qe+1];return e==="-"||e==="+"?/\d/.test(t)||t==="."&&/\d/.test(n[Qe+2]):e==="."?/\d/.test(t):/\d/.test(e)}function zh(n){if(Qe>=n.length)return!1;let e=n[Qe];if(kh.test(e))return!0;if(e==="-"){if(n.length-Qe<2)return!1;let t=n[Qe+1];return!!(t==="-"||kh.test(t))}return!1}const BE={deg:1,rad:180/Math.PI,grad:9/10,turn:360};function Ta(n){let e="";if((n[Qe]==="-"||n[Qe]==="+")&&(e+=n[Qe++]),e+=Vo(n),n[Qe]==="."&&/\d/.test(n[Qe+1])&&(e+=n[Qe++]+Vo(n)),(n[Qe]==="e"||n[Qe]==="E")&&((n[Qe+1]==="-"||n[Qe+1]==="+")&&/\d/.test(n[Qe+2])?e+=n[Qe++]+n[Qe++]+Vo(n):/\d/.test(n[Qe+1])&&(e+=n[Qe++]+Vo(n))),zh(n)){let t=wl(n);return t==="deg"||t==="rad"||t==="turn"||t==="grad"?{type:Ce.Hue,value:e*BE[t]}:void 0}return n[Qe]==="%"?(Qe++,{type:Ce.Percentage,value:+e}):{type:Ce.Number,value:+e}}function Vo(n){let e="";for(;/\d/.test(n[Qe]);)e+=n[Qe++];return e}function wl(n){let e="";for(;Qe<n.length&&OE.test(n[Qe]);)e+=n[Qe++];return e}function kE(n){let e=wl(n);return n[Qe]==="("?(Qe++,{type:Ce.Function,value:e}):e==="none"?{type:Ce.None,value:void 0}:{type:Ce.Ident,value:e}}function zE(n=""){let e=n.trim(),t=[],i;for(Qe=0;Qe<e.length;){if(i=e[Qe++],i===`
`||i==="	"||i===" "){for(;Qe<e.length&&(e[Qe]===`
`||e[Qe]==="	"||e[Qe]===" ");)Qe++;continue}if(i===",")return;if(i===")"){t.push({type:Ce.ParenClose});continue}if(i==="+"){if(Qe--,Ho(e)){t.push(Ta(e));continue}return}if(i==="-"){if(Qe--,Ho(e)){t.push(Ta(e));continue}if(zh(e)){t.push({type:Ce.Ident,value:wl(e)});continue}return}if(i==="."){if(Qe--,Ho(e)){t.push(Ta(e));continue}return}if(i==="/"){for(;Qe<e.length&&(e[Qe]===`
`||e[Qe]==="	"||e[Qe]===" ");)Qe++;let r;if(Ho(e)&&(r=Ta(e),r.type!==Ce.Hue)){t.push({type:Ce.Alpha,value:r});continue}if(zh(e)&&wl(e)==="none"){t.push({type:Ce.Alpha,value:{type:Ce.None,value:void 0}});continue}return}if(/\d/.test(i)){Qe--,t.push(Ta(e));continue}if(kh.test(i)){Qe--,t.push(kE(e));continue}return}return t}function GE(n){n._i=0;let e=n[n._i++];if(!e||e.type!==Ce.Function||e.value!=="color"||(e=n[n._i++],e.type!==Ce.Ident))return;const t=xg[e.value];if(!t)return;const i={mode:t},r=bg(n,!1);if(!r)return;const s=yg(t).channels;for(let a=0,o,l;a<s.length;a++)o=r[a],l=s[a],o.type!==Ce.None&&(i[l]=o.type===Ce.Number?o.value:o.value/100,l==="alpha"&&(i[l]=Math.max(0,Math.min(1,i[l]))));return i}function bg(n,e){const t=[];let i;for(;n._i<n.length;){if(i=n[n._i++],i.type===Ce.None||i.type===Ce.Number||i.type===Ce.Alpha||i.type===Ce.Percentage||e&&i.type===Ce.Hue){t.push(i);continue}if(i.type===Ce.ParenClose){if(n._i<n.length)return;continue}return}if(!(t.length<3||t.length>4)){if(t.length===4){if(t[3].type!==Ce.Alpha)return;t[3]=t[3].value}return t.length===3&&t.push({type:Ce.None,value:void 0}),t.every(r=>r.type!==Ce.Alpha)?t:void 0}}function HE(n,e){n._i=0;let t=n[n._i++];if(!t||t.type!==Ce.Function)return;let i=bg(n,e);if(i)return i.unshift(t.value),i}const VE=n=>{if(typeof n!="string")return;const e=zE(n),t=e?HE(e,!0):void 0;let i,r=0,s=El.length;for(;r<s;)if((i=El[r++](n,t))!==void 0)return i;return e?GE(e):void 0};function WE(n,e){if(!e||e[0]!=="rgb"&&e[0]!=="rgba")return;const t={mode:"rgb"},[,i,r,s,a]=e;if(!(i.type===Ce.Hue||r.type===Ce.Hue||s.type===Ce.Hue))return i.type!==Ce.None&&(t.r=i.type===Ce.Number?i.value/255:i.value/100),r.type!==Ce.None&&(t.g=r.type===Ce.Number?r.value/255:r.value/100),s.type!==Ce.None&&(t.b=s.type===Ce.Number?s.value/255:s.value/100),a.type!==Ce.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ce.Number?a.value:a.value/100))),t}const XE=n=>n==="transparent"?{mode:"rgb",r:0,g:0,b:0,alpha:0}:void 0,jE=(n,e,t)=>n+t*(e-n),YE=n=>{let e=[];for(let t=0;t<n.length-1;t++){let i=n[t],r=n[t+1];i===void 0&&r===void 0?e.push(void 0):i!==void 0&&r!==void 0?e.push([i,r]):e.push(i!==void 0?[i,i]:[r,r])}return e},qE=n=>e=>{let t=YE(e);return i=>{let r=i*t.length,s=i>=1?t.length-1:Math.max(Math.floor(r),0),a=t[s];return a===void 0?void 0:n(a[0],a[1],r-s)}},ze=qE(jE),tn=n=>{let e=!1,t=n.map(i=>i!==void 0?(e=!0,i):1);return e?t:n},Qs={mode:"rgb",channels:["r","g","b","alpha"],parse:[WE,CE,LE,AE,XE,"srgb"],serialize:"srgb",interpolate:{r:ze,g:ze,b:ze,alpha:{use:ze,fixup:tn}},gamut:!0,white:{r:1,g:1,b:1},black:{r:0,g:0,b:0}},eu=(n=0)=>Math.pow(Math.abs(n),563/256)*Math.sign(n),Xp=n=>{let e=eu(n.r),t=eu(n.g),i=eu(n.b),r={mode:"xyz65",x:.5766690429101305*e+.1855582379065463*t+.1882286462349947*i,y:.297344975250536*e+.6273635662554661*t+.0752914584939979*i,z:.0270313613864123*e+.0706888525358272*t+.9913375368376386*i};return n.alpha!==void 0&&(r.alpha=n.alpha),r},tu=n=>Math.pow(Math.abs(n),256/563)*Math.sign(n),jp=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"a98",r:tu(n*2.0415879038107465-e*.5650069742788597-.3447313507783297*t),g:tu(n*-.9692436362808798+e*1.8759675015077206+.0415550574071756*t),b:tu(n*.0134442806320312-e*.1183623922310184+1.0151749943912058*t)};return i!==void 0&&(r.alpha=i),r},nu=(n=0)=>{const e=Math.abs(n);return e<=.04045?n/12.92:(Math.sign(n)||1)*Math.pow((e+.055)/1.055,2.4)},ea=({r:n,g:e,b:t,alpha:i})=>{let r={mode:"lrgb",r:nu(n),g:nu(e),b:nu(t)};return i!==void 0&&(r.alpha=i),r},ts=n=>{let{r:e,g:t,b:i,alpha:r}=ea(n),s={mode:"xyz65",x:.4123907992659593*e+.357584339383878*t+.1804807884018343*i,y:.2126390058715102*e+.715168678767756*t+.0721923153607337*i,z:.0193308187155918*e+.119194779794626*t+.9505321522496607*i};return r!==void 0&&(s.alpha=r),s},iu=(n=0)=>{const e=Math.abs(n);return e>.0031308?(Math.sign(n)||1)*(1.055*Math.pow(e,1/2.4)-.055):n*12.92},ta=({r:n,g:e,b:t,alpha:i},r="rgb")=>{let s={mode:r,r:iu(n),g:iu(e),b:iu(t)};return i!==void 0&&(s.alpha=i),s},ns=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=ta({r:n*3.2409699419045226-e*1.537383177570094-.4986107602930034*t,g:n*-.9692436362808796+e*1.8759675015077204+.0415550574071756*t,b:n*.0556300796969936-e*.2039769588889765+1.0569715142428784*t});return i!==void 0&&(r.alpha=i),r},KE={...Qs,mode:"a98",parse:["a98-rgb"],serialize:"a98-rgb",fromMode:{rgb:n=>jp(ts(n)),xyz65:jp},toMode:{rgb:n=>ns(Xp(n)),xyz65:Xp}},fn=n=>(n=n%360)<0?n+360:n,ZE=(n,e)=>n.map((t,i,r)=>{if(t===void 0)return t;let s=fn(t);return i===0||n[i-1]===void 0?s:e(s-fn(r[i-1]))}).reduce((t,i)=>!t.length||i===void 0||t[t.length-1]===void 0?(t.push(i),t):(t.push(i+t[t.length-1]),t),[]),Ji=n=>ZE(n,e=>Math.abs(e)<=180?e:e-360*Math.sign(e)),sn=[-.14861,1.78277,-.29227,-.90649,1.97294,0],$E=Math.PI/180,JE=180/Math.PI;let Yp=sn[3]*sn[4],qp=sn[1]*sn[4],Kp=sn[1]*sn[2]-sn[0]*sn[3];const QE=({r:n,g:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(Kp*t+n*Yp-e*qp)/(Kp+Yp-qp),s=t-r,a=(sn[4]*(e-r)-sn[2]*s)/sn[3],o={mode:"cubehelix",l:r,s:r===0||r===1?void 0:Math.sqrt(s*s+a*a)/(sn[4]*r*(1-r))};return o.s&&(o.h=Math.atan2(a,s)*JE-120),i!==void 0&&(o.alpha=i),o},e3=({h:n,s:e,l:t,alpha:i})=>{let r={mode:"rgb"};n=(n===void 0?0:n+120)*$E,t===void 0&&(t=0);let s=e===void 0?0:e*t*(1-t),a=Math.cos(n),o=Math.sin(n);return r.r=t+s*(sn[0]*a+sn[1]*o),r.g=t+s*(sn[2]*a+sn[3]*o),r.b=t+s*(sn[4]*a+sn[5]*o),i!==void 0&&(r.alpha=i),r},zl=(n,e)=>{if(n.h===void 0||e.h===void 0||!n.s||!e.s)return 0;let t=fn(n.h),i=fn(e.h),r=Math.sin((i-t+360)/2*Math.PI/180);return 2*Math.sqrt(n.s*e.s)*r},t3=(n,e)=>{if(n.h===void 0||e.h===void 0)return 0;let t=fn(n.h),i=fn(e.h);return Math.abs(i-t)>180?t-(i-360*Math.sign(i-t)):i-t},Gl=(n,e)=>{if(n.h===void 0||e.h===void 0||!n.c||!e.c)return 0;let t=fn(n.h),i=fn(e.h),r=Math.sin((i-t+360)/2*Math.PI/180);return 2*Math.sqrt(n.c*e.c)*r},Qi=n=>{let e=n.reduce((i,r)=>{if(r!==void 0){let s=r*Math.PI/180;i.sin+=Math.sin(s),i.cos+=Math.cos(s)}return i},{sin:0,cos:0}),t=Math.atan2(e.sin,e.cos)*180/Math.PI;return t<0?360+t:t},n3={mode:"cubehelix",channels:["h","s","l","alpha"],parse:["--cubehelix"],serialize:"--cubehelix",ranges:{h:[0,360],s:[0,4.614],l:[0,1]},fromMode:{rgb:QE},toMode:{rgb:e3},interpolate:{h:{use:ze,fixup:Ji},s:ze,l:ze,alpha:{use:ze,fixup:tn}},difference:{h:zl},average:{h:Qi}},Er=({l:n,a:e,b:t,alpha:i},r="lch")=>{e===void 0&&(e=0),t===void 0&&(t=0);let s=Math.sqrt(e*e+t*t),a={mode:r,l:n,c:s};return s&&(a.h=fn(Math.atan2(t,e)*180/Math.PI)),i!==void 0&&(a.alpha=i),a},wr=({l:n,c:e,h:t,alpha:i},r="lab")=>{t===void 0&&(t=0);let s={mode:r,l:n,a:e?e*Math.cos(t/180*Math.PI):0,b:e?e*Math.sin(t/180*Math.PI):0};return i!==void 0&&(s.alpha=i),s},Sg=Math.pow(29,3)/Math.pow(3,3),Mg=Math.pow(6,3)/Math.pow(29,3),qt={X:.3457/.3585,Y:1,Z:(1-.3457-.3585)/.3585},Os={X:.3127/.329,Y:1,Z:(1-.3127-.329)/.329};let ru=n=>Math.pow(n,3)>Mg?Math.pow(n,3):(116*n-16)/Sg;const Tg=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(n+16)/116,s=e/500+r,a=r-t/200,o={mode:"xyz65",x:ru(s)*Os.X,y:ru(r)*Os.Y,z:ru(a)*Os.Z};return i!==void 0&&(o.alpha=i),o},Hl=n=>ns(Tg(n)),su=n=>n>Mg?Math.cbrt(n):(Sg*n+16)/116,Eg=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=su(n/Os.X),s=su(e/Os.Y),a=su(t/Os.Z),o={mode:"lab65",l:116*s-16,a:500*(r-s),b:200*(s-a)};return i!==void 0&&(o.alpha=i),o},Vl=n=>{let e=Eg(ts(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},Al=1,wg=1,qa=26/180*Math.PI,Rl=Math.cos(qa),Cl=Math.sin(qa),Ag=100/Math.log(139/100),Gh=({l:n,c:e,h:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"lab65",l:(Math.exp(n*Al/Ag)-1)/.0039},s=(Math.exp(.0435*e*wg*Al)-1)/.075,a=s*Math.cos(t/180*Math.PI-qa),o=s*Math.sin(t/180*Math.PI-qa);return r.a=a*Rl-o/.83*Cl,r.b=a*Cl+o/.83*Rl,i!==void 0&&(r.alpha=i),r},Hh=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=e*Rl+t*Cl,s=.83*(t*Rl-e*Cl),a=Math.sqrt(r*r+s*s),o={mode:"dlch",l:Ag/Al*Math.log(1+.0039*n),c:Math.log(1+.075*a)/(.0435*wg*Al)};return o.c&&(o.h=fn((Math.atan2(s,r)+qa)/Math.PI*180)),i!==void 0&&(o.alpha=i),o},Zp=n=>Gh(Er(n,"dlch")),$p=n=>wr(Hh(n),"dlab"),i3={mode:"dlab",parse:["--din99o-lab"],serialize:"--din99o-lab",toMode:{lab65:Zp,rgb:n=>Hl(Zp(n))},fromMode:{lab65:$p,rgb:n=>$p(Vl(n))},channels:["l","a","b","alpha"],ranges:{l:[0,100],a:[-40.09,45.501],b:[-40.469,44.344]},interpolate:{l:ze,a:ze,b:ze,alpha:{use:ze,fixup:tn}}},r3={mode:"dlch",parse:["--din99o-lch"],serialize:"--din99o-lch",toMode:{lab65:Gh,dlab:n=>wr(n,"dlab"),rgb:n=>Hl(Gh(n))},fromMode:{lab65:Hh,dlab:n=>Er(n,"dlch"),rgb:n=>Hh(Vl(n))},channels:["l","c","h","alpha"],ranges:{l:[0,100],c:[0,51.484],h:[0,360]},interpolate:{l:ze,c:ze,h:{use:ze,fixup:Ji},alpha:{use:ze,fixup:tn}},difference:{h:Gl},average:{h:Qi}};function s3({h:n,s:e,i:t,alpha:i}){n=fn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.abs(n/60%2-1),s;switch(Math.floor(n/60)){case 0:s={r:t*(1+e*(3/(2-r)-1)),g:t*(1+e*(3*(1-r)/(2-r)-1)),b:t*(1-e)};break;case 1:s={r:t*(1+e*(3*(1-r)/(2-r)-1)),g:t*(1+e*(3/(2-r)-1)),b:t*(1-e)};break;case 2:s={r:t*(1-e),g:t*(1+e*(3/(2-r)-1)),b:t*(1+e*(3*(1-r)/(2-r)-1))};break;case 3:s={r:t*(1-e),g:t*(1+e*(3*(1-r)/(2-r)-1)),b:t*(1+e*(3/(2-r)-1))};break;case 4:s={r:t*(1+e*(3*(1-r)/(2-r)-1)),g:t*(1-e),b:t*(1+e*(3/(2-r)-1))};break;case 5:s={r:t*(1+e*(3/(2-r)-1)),g:t*(1-e),b:t*(1+e*(3*(1-r)/(2-r)-1))};break;default:s={r:t*(1-e),g:t*(1-e),b:t*(1-e)}}return s.mode="rgb",i!==void 0&&(s.alpha=i),s}function a3({r:n,g:e,b:t,alpha:i}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsi",s:n+e+t===0?0:1-3*s/(n+e+t),i:(n+e+t)/3};return r-s!==0&&(a.h=(r===n?(e-t)/(r-s)+(e<t)*6:r===e?(t-n)/(r-s)+2:(n-e)/(r-s)+4)*60),i!==void 0&&(a.alpha=i),a}const o3={mode:"hsi",toMode:{rgb:s3},parse:["--hsi"],serialize:"--hsi",fromMode:{rgb:a3},channels:["h","s","i","alpha"],ranges:{h:[0,360]},gamut:"rgb",interpolate:{h:{use:ze,fixup:Ji},s:ze,i:ze,alpha:{use:ze,fixup:tn}},difference:{h:zl},average:{h:Qi}};function l3({h:n,s:e,l:t,alpha:i}){n=fn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let r=t+e*(t<.5?t:1-t),s=r-(r-t)*2*Math.abs(n/60%2-1),a;switch(Math.floor(n/60)){case 0:a={r,g:s,b:2*t-r};break;case 1:a={r:s,g:r,b:2*t-r};break;case 2:a={r:2*t-r,g:r,b:s};break;case 3:a={r:2*t-r,g:s,b:r};break;case 4:a={r:s,g:2*t-r,b:r};break;case 5:a={r,g:2*t-r,b:s};break;default:a={r:2*t-r,g:2*t-r,b:2*t-r}}return a.mode="rgb",i!==void 0&&(a.alpha=i),a}function c3({r:n,g:e,b:t,alpha:i}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsl",s:r===s?0:(r-s)/(1-Math.abs(r+s-1)),l:.5*(r+s)};return r-s!==0&&(a.h=(r===n?(e-t)/(r-s)+(e<t)*6:r===e?(t-n)/(r-s)+2:(n-e)/(r-s)+4)*60),i!==void 0&&(a.alpha=i),a}const u3=(n,e)=>{switch(e){case"deg":return+n;case"rad":return n/Math.PI*180;case"grad":return n/10*9;case"turn":return n*360}},h3=new RegExp(`^hsla?\\(\\s*${PE}${qs}${Ba}${qs}${Ba}\\s*(?:,\\s*${wf}\\s*)?\\)$`),f3=n=>{let e=n.match(h3);if(!e)return;let t={mode:"hsl"};return e[3]!==void 0?t.h=+e[3]:e[1]!==void 0&&e[2]!==void 0&&(t.h=u3(e[1],e[2])),e[4]!==void 0&&(t.s=Math.min(Math.max(0,e[4]/100),1)),e[5]!==void 0&&(t.l=Math.min(Math.max(0,e[5]/100),1)),e[6]!==void 0?t.alpha=Math.max(0,Math.min(1,e[6]/100)):e[7]!==void 0&&(t.alpha=Math.max(0,Math.min(1,+e[7]))),t};function d3(n,e){if(!e||e[0]!=="hsl"&&e[0]!=="hsla")return;const t={mode:"hsl"},[,i,r,s,a]=e;if(i.type!==Ce.None){if(i.type===Ce.Percentage)return;t.h=i.value}if(r.type!==Ce.None){if(r.type===Ce.Hue)return;t.s=r.value/100}if(s.type!==Ce.None){if(s.type===Ce.Hue)return;t.l=s.value/100}return a.type!==Ce.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ce.Number?a.value:a.value/100))),t}const Rg={mode:"hsl",toMode:{rgb:l3},fromMode:{rgb:c3},channels:["h","s","l","alpha"],ranges:{h:[0,360]},gamut:"rgb",parse:[d3,f3],serialize:n=>`hsl(${n.h!==void 0?n.h:"none"} ${n.s!==void 0?n.s*100+"%":"none"} ${n.l!==void 0?n.l*100+"%":"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:ze,fixup:Ji},s:ze,l:ze,alpha:{use:ze,fixup:tn}},difference:{h:zl},average:{h:Qi}};function Cg({h:n,s:e,v:t,alpha:i}){n=fn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.abs(n/60%2-1),s;switch(Math.floor(n/60)){case 0:s={r:t,g:t*(1-e*r),b:t*(1-e)};break;case 1:s={r:t*(1-e*r),g:t,b:t*(1-e)};break;case 2:s={r:t*(1-e),g:t,b:t*(1-e*r)};break;case 3:s={r:t*(1-e),g:t*(1-e*r),b:t};break;case 4:s={r:t*(1-e*r),g:t*(1-e),b:t};break;case 5:s={r:t,g:t*(1-e),b:t*(1-e*r)};break;default:s={r:t*(1-e),g:t*(1-e),b:t*(1-e)}}return s.mode="rgb",i!==void 0&&(s.alpha=i),s}function Pg({r:n,g:e,b:t,alpha:i}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsv",s:r===0?0:1-s/r,v:r};return r-s!==0&&(a.h=(r===n?(e-t)/(r-s)+(e<t)*6:r===e?(t-n)/(r-s)+2:(n-e)/(r-s)+4)*60),i!==void 0&&(a.alpha=i),a}const Dg={mode:"hsv",toMode:{rgb:Cg},parse:["--hsv"],serialize:"--hsv",fromMode:{rgb:Pg},channels:["h","s","v","alpha"],ranges:{h:[0,360]},gamut:"rgb",interpolate:{h:{use:ze,fixup:Ji},s:ze,v:ze,alpha:{use:ze,fixup:tn}},difference:{h:zl},average:{h:Qi}};function p3({h:n,w:e,b:t,alpha:i}){if(e===void 0&&(e=0),t===void 0&&(t=0),e+t>1){let r=e+t;e/=r,t/=r}return Cg({h:n,s:t===1?1:1-e/(1-t),v:1-t,alpha:i})}function m3(n){let e=Pg(n);if(e===void 0)return;let t=e.s!==void 0?e.s:0,i=e.v!==void 0?e.v:0,r={mode:"hwb",w:(1-t)*i,b:1-i};return e.h!==void 0&&(r.h=e.h),e.alpha!==void 0&&(r.alpha=e.alpha),r}function g3(n,e){if(!e||e[0]!=="hwb")return;const t={mode:"hwb"},[,i,r,s,a]=e;if(i.type!==Ce.None){if(i.type===Ce.Percentage)return;t.h=i.value}if(r.type!==Ce.None){if(r.type===Ce.Hue)return;t.w=r.value/100}if(s.type!==Ce.None){if(s.type===Ce.Hue)return;t.b=s.value/100}return a.type!==Ce.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ce.Number?a.value:a.value/100))),t}const _3={mode:"hwb",toMode:{rgb:p3},fromMode:{rgb:m3},channels:["h","w","b","alpha"],ranges:{h:[0,360]},gamut:"rgb",parse:[g3],serialize:n=>`hwb(${n.h!==void 0?n.h:"none"} ${n.w!==void 0?n.w*100+"%":"none"} ${n.b!==void 0?n.b*100+"%":"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:ze,fixup:Ji},w:ze,b:ze,alpha:{use:ze,fixup:tn}},difference:{h:t3},average:{h:Qi}},Ug=203,Wl=.1593017578125,Lg=78.84375,Xl=.8359375,jl=18.8515625,Yl=18.6875;function au(n){if(n<0)return 0;const e=Math.pow(n,1/Lg);return 1e4*Math.pow(Math.max(0,e-Xl)/(jl-Yl*e),1/Wl)}function ou(n){if(n<0)return 0;const e=Math.pow(n/1e4,Wl);return Math.pow((Xl+jl*e)/(1+Yl*e),Lg)}const lu=n=>Math.max(n/Ug,0),Jp=({i:n,t:e,p:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r=au(n+.008609037037932761*e+.11102962500302593*t),s=au(n-.00860903703793275*e-.11102962500302599*t),a=au(n+.5600313357106791*e-.32062717498731885*t),o={mode:"xyz65",x:lu(2.070152218389422*r-1.3263473389671556*s+.2066510476294051*a),y:lu(.3647385209748074*r+.680566024947227*s-.0453045459220346*a),z:lu(-.049747207535812*r-.0492609666966138*s+1.1880659249923042*a)};return i!==void 0&&(o.alpha=i),o},cu=(n=0)=>Math.max(n*Ug,0),Qp=({x:n,y:e,z:t,alpha:i})=>{const r=cu(n),s=cu(e),a=cu(t),o=ou(.3592832590121217*r+.6976051147779502*s-.0358915932320289*a),l=ou(-.1920808463704995*r+1.1004767970374323*s+.0753748658519118*a),c=ou(.0070797844607477*r+.0748396662186366*s+.8433265453898765*a),u=.5*o+.5*l,f=1.61376953125*o-3.323486328125*l+1.709716796875*c,h=4.378173828125*o-4.24560546875*l-.132568359375*c,d={mode:"itp",i:u,t:f,p:h};return i!==void 0&&(d.alpha=i),d},v3={mode:"itp",channels:["i","t","p","alpha"],parse:["--ictcp"],serialize:"--ictcp",toMode:{xyz65:Jp,rgb:n=>ns(Jp(n))},fromMode:{xyz65:Qp,rgb:n=>Qp(ts(n))},ranges:{i:[0,.581],t:[-.369,.272],p:[-.164,.331]},interpolate:{i:ze,t:ze,p:ze,alpha:{use:ze,fixup:tn}}},x3=134.03437499999998,y3=16295499532821565e-27,uu=n=>{if(n<0)return 0;let e=Math.pow(n/1e4,Wl);return Math.pow((Xl+jl*e)/(1+Yl*e),x3)},hu=(n=0)=>Math.max(n*203,0),Ig=({x:n,y:e,z:t,alpha:i})=>{n=hu(n),e=hu(e),t=hu(t);let r=1.15*n-.15*t,s=.66*e+.34*n,a=uu(.41478972*r+.579999*s+.014648*t),o=uu(-.20151*r+1.120649*s+.0531008*t),l=uu(-.0166008*r+.2648*s+.6684799*t),c=(a+o)/2,u={mode:"jab",j:.44*c/(1-.56*c)-y3,a:3.524*a-4.066708*o+.542708*l,b:.199076*a+1.096799*o-1.295875*l};return i!==void 0&&(u.alpha=i),u},b3=134.03437499999998,em=16295499532821565e-27,fu=n=>{if(n<0)return 0;let e=Math.pow(n,1/b3);return 1e4*Math.pow((Xl-e)/(Yl*e-jl),1/Wl)},du=n=>n/203,Fg=({j:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(n+em)/(.44+.56*(n+em)),s=fu(r+.13860504*e+.058047316*t),a=fu(r-.13860504*e-.058047316*t),o=fu(r-.096019242*e-.8118919*t),l={mode:"xyz65",x:du(1.661373024652174*s-.914523081304348*a+.23136208173913045*o),y:du(-.3250758611844533*s+1.571847026732543*a-.21825383453227928*o),z:du(-.090982811*s-.31272829*a+1.5227666*o)};return i!==void 0&&(l.alpha=i),l},Ng=n=>{let e=Ig(ts(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},Og=n=>ns(Fg(n)),S3={mode:"jab",channels:["j","a","b","alpha"],parse:["--jzazbz"],serialize:"--jzazbz",fromMode:{rgb:Ng,xyz65:Ig},toMode:{rgb:Og,xyz65:Fg},ranges:{j:[0,.222],a:[-.109,.129],b:[-.185,.134]},interpolate:{j:ze,a:ze,b:ze,alpha:{use:ze,fixup:tn}}},tm=({j:n,a:e,b:t,alpha:i})=>{e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.sqrt(e*e+t*t),s={mode:"jch",j:n,c:r};return r&&(s.h=fn(Math.atan2(t,e)*180/Math.PI)),i!==void 0&&(s.alpha=i),s},nm=({j:n,c:e,h:t,alpha:i})=>{t===void 0&&(t=0);let r={mode:"jab",j:n,a:e?e*Math.cos(t/180*Math.PI):0,b:e?e*Math.sin(t/180*Math.PI):0};return i!==void 0&&(r.alpha=i),r},M3={mode:"jch",parse:["--jzczhz"],serialize:"--jzczhz",toMode:{jab:nm,rgb:n=>Og(nm(n))},fromMode:{rgb:n=>tm(Ng(n)),jab:tm},channels:["j","c","h","alpha"],ranges:{j:[0,.221],c:[0,.19],h:[0,360]},interpolate:{h:{use:ze,fixup:Ji},c:ze,j:ze,alpha:{use:ze,fixup:tn}},difference:{h:Gl},average:{h:Qi}},ql=Math.pow(29,3)/Math.pow(3,3),Rf=Math.pow(6,3)/Math.pow(29,3);let pu=n=>Math.pow(n,3)>Rf?Math.pow(n,3):(116*n-16)/ql;const Cf=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(n+16)/116,s=e/500+r,a=r-t/200,o={mode:"xyz50",x:pu(s)*qt.X,y:pu(r)*qt.Y,z:pu(a)*qt.Z};return i!==void 0&&(o.alpha=i),o},Qa=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=ta({r:n*3.1341359569958707-e*1.6173863321612538-.4906619460083532*t,g:n*-.978795502912089+e*1.916254567259524+.03344273116131949*t,b:n*.07195537988411677-e*.2289768264158322+1.405386058324125*t});return i!==void 0&&(r.alpha=i),r},Bg=n=>Qa(Cf(n)),eo=n=>{let{r:e,g:t,b:i,alpha:r}=ea(n),s={mode:"xyz50",x:.436065742824811*e+.3851514688337912*t+.14307845442264197*i,y:.22249319175623702*e+.7168870538238823*t+.06061979053616537*i,z:.013923904500943465*e+.09708128566574634*t+.7140993584005155*i};return r!==void 0&&(s.alpha=r),s},mu=n=>n>Rf?Math.cbrt(n):(ql*n+16)/116,Pf=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=mu(n/qt.X),s=mu(e/qt.Y),a=mu(t/qt.Z),o={mode:"lab",l:116*s-16,a:500*(r-s),b:200*(s-a)};return i!==void 0&&(o.alpha=i),o},kg=n=>{let e=Pf(eo(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e};function T3(n,e){if(!e||e[0]!=="lab")return;const t={mode:"lab"},[,i,r,s,a]=e;if(!(i.type===Ce.Hue||r.type===Ce.Hue||s.type===Ce.Hue))return i.type!==Ce.None&&(t.l=Math.min(Math.max(0,i.value),100)),r.type!==Ce.None&&(t.a=r.type===Ce.Number?r.value:r.value*125/100),s.type!==Ce.None&&(t.b=s.type===Ce.Number?s.value:s.value*125/100),a.type!==Ce.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ce.Number?a.value:a.value/100))),t}const Df={mode:"lab",toMode:{xyz50:Cf,rgb:Bg},fromMode:{xyz50:Pf,rgb:kg},channels:["l","a","b","alpha"],ranges:{l:[0,100],a:[-125,125],b:[-125,125]},parse:[T3],serialize:n=>`lab(${n.l!==void 0?n.l:"none"} ${n.a!==void 0?n.a:"none"} ${n.b!==void 0?n.b:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{l:ze,a:ze,b:ze,alpha:{use:ze,fixup:tn}}},E3={...Df,mode:"lab65",parse:["--lab-d65"],serialize:"--lab-d65",toMode:{xyz65:Tg,rgb:Hl},fromMode:{xyz65:Eg,rgb:Vl},ranges:{l:[0,100],a:[-125,125],b:[-125,125]}};function w3(n,e){if(!e||e[0]!=="lch")return;const t={mode:"lch"},[,i,r,s,a]=e;if(i.type!==Ce.None){if(i.type===Ce.Hue)return;t.l=Math.min(Math.max(0,i.value),100)}if(r.type!==Ce.None&&(t.c=Math.max(0,r.type===Ce.Number?r.value:r.value*150/100)),s.type!==Ce.None){if(s.type===Ce.Percentage)return;t.h=s.value}return a.type!==Ce.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ce.Number?a.value:a.value/100))),t}const Uf={mode:"lch",toMode:{lab:wr,rgb:n=>Bg(wr(n))},fromMode:{rgb:n=>Er(kg(n)),lab:Er},channels:["l","c","h","alpha"],ranges:{l:[0,100],c:[0,150],h:[0,360]},parse:[w3],serialize:n=>`lch(${n.l!==void 0?n.l:"none"} ${n.c!==void 0?n.c:"none"} ${n.h!==void 0?n.h:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:ze,fixup:Ji},c:ze,l:ze,alpha:{use:ze,fixup:tn}},difference:{h:Gl},average:{h:Qi}},A3={...Uf,mode:"lch65",parse:["--lch-d65"],serialize:"--lch-d65",toMode:{lab65:n=>wr(n,"lab65"),rgb:n=>Hl(wr(n,"lab65"))},fromMode:{rgb:n=>Er(Vl(n),"lch65"),lab65:n=>Er(n,"lch65")},ranges:{l:[0,100],c:[0,150],h:[0,360]}},zg=({l:n,u:e,v:t,alpha:i})=>{e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.sqrt(e*e+t*t),s={mode:"lchuv",l:n,c:r};return r&&(s.h=fn(Math.atan2(t,e)*180/Math.PI)),i!==void 0&&(s.alpha=i),s},Gg=({l:n,c:e,h:t,alpha:i})=>{t===void 0&&(t=0);let r={mode:"luv",l:n,u:e?e*Math.cos(t/180*Math.PI):0,v:e?e*Math.sin(t/180*Math.PI):0};return i!==void 0&&(r.alpha=i),r},Hg=(n,e,t)=>4*n/(n+15*e+3*t),Vg=(n,e,t)=>9*e/(n+15*e+3*t),R3=Hg(qt.X,qt.Y,qt.Z),C3=Vg(qt.X,qt.Y,qt.Z),P3=n=>n<=Rf?ql*n:116*Math.cbrt(n)-16,Vh=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=P3(e/qt.Y),s=Hg(n,e,t),a=Vg(n,e,t);!isFinite(s)||!isFinite(a)?r=s=a=0:(s=13*r*(s-R3),a=13*r*(a-C3));let o={mode:"luv",l:r,u:s,v:a};return i!==void 0&&(o.alpha=i),o},D3=(n,e,t)=>4*n/(n+15*e+3*t),U3=(n,e,t)=>9*e/(n+15*e+3*t),L3=D3(qt.X,qt.Y,qt.Z),I3=U3(qt.X,qt.Y,qt.Z),Wh=({l:n,u:e,v:t,alpha:i})=>{if(n===void 0&&(n=0),n===0)return{mode:"xyz50",x:0,y:0,z:0};e===void 0&&(e=0),t===void 0&&(t=0);let r=e/(13*n)+L3,s=t/(13*n)+I3,a=qt.Y*(n<=8?n/ql:Math.pow((n+16)/116,3)),o=a*(9*r)/(4*s),l=a*(12-3*r-20*s)/(4*s),c={mode:"xyz50",x:o,y:a,z:l};return i!==void 0&&(c.alpha=i),c},F3=n=>zg(Vh(eo(n))),N3=n=>Qa(Wh(Gg(n))),O3={mode:"lchuv",toMode:{luv:Gg,rgb:N3},fromMode:{rgb:F3,luv:zg},channels:["l","c","h","alpha"],parse:["--lchuv"],serialize:"--lchuv",ranges:{l:[0,100],c:[0,176.956],h:[0,360]},interpolate:{h:{use:ze,fixup:Ji},c:ze,l:ze,alpha:{use:ze,fixup:tn}},difference:{h:Gl},average:{h:Qi}},B3={...Qs,mode:"lrgb",toMode:{rgb:ta},fromMode:{rgb:ea},parse:["srgb-linear"],serialize:"srgb-linear"},k3={mode:"luv",toMode:{xyz50:Wh,rgb:n=>Qa(Wh(n))},fromMode:{xyz50:Vh,rgb:n=>Vh(eo(n))},channels:["l","u","v","alpha"],parse:["--luv"],serialize:"--luv",ranges:{l:[0,100],u:[-84.936,175.042],v:[-125.882,87.243]},interpolate:{l:ze,u:ze,v:ze,alpha:{use:ze,fixup:tn}}},Wg=({r:n,g:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.cbrt(.412221469470763*n+.5363325372617348*e+.0514459932675022*t),s=Math.cbrt(.2119034958178252*n+.6806995506452344*e+.1073969535369406*t),a=Math.cbrt(.0883024591900564*n+.2817188391361215*e+.6299787016738222*t),o={mode:"oklab",l:.210454268309314*r+.7936177747023054*s-.0040720430116193*a,a:1.9779985324311684*r-2.42859224204858*s+.450593709617411*a,b:.0259040424655478*r+.7827717124575296*s-.8086757549230774*a};return i!==void 0&&(o.alpha=i),o},Kl=n=>{let e=Wg(ea(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},to=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.pow(n+.3963377773761749*e+.2158037573099136*t,3),s=Math.pow(n-.1055613458156586*e-.0638541728258133*t,3),a=Math.pow(n-.0894841775298119*e-1.2914855480194092*t,3),o={mode:"lrgb",r:4.076741636075957*r-3.3077115392580616*s+.2309699031821044*a,g:-1.2684379732850317*r+2.6097573492876887*s-.3413193760026573*a,b:-.0041960761386756*r-.7034186179359362*s+1.7076146940746117*a};return i!==void 0&&(o.alpha=i),o},Zl=n=>ta(to(n));function Xh(n){const i=1.170873786407767;return .5*(i*n-.206+Math.sqrt((i*n-.206)*(i*n-.206)+4*.03*i*n))}function Pl(n){return(n*n+.206*n)/(1.170873786407767*(n+.03))}function z3(n,e){let t,i,r,s,a,o,l,c;-1.88170328*n-.80936493*e>1?(t=1.19086277,i=1.76576728,r=.59662641,s=.75515197,a=.56771245,o=4.0767416621,l=-3.3077115913,c=.2309699292):1.81444104*n-1.19445276*e>1?(t=.73956515,i=-.45954404,r=.08285427,s=.1254107,a=.14503204,o=-1.2684380046,l=2.6097574011,c=-.3413193965):(t=1.35733652,i=-.00915799,r=-1.1513021,s=-.50559606,a=.00692167,o=-.0041960863,l=-.7034186147,c=1.707614701);let u=t+i*n+r*e+s*n*n+a*n*e,f=.3963377774*n+.2158037573*e,h=-.1055613458*n-.0638541728*e,d=-.0894841775*n-1.291485548*e;{let m=1+u*f,g=1+u*h,p=1+u*d,_=m*m*m,v=g*g*g,S=p*p*p,y=3*f*m*m,M=3*h*g*g,T=3*d*p*p,w=6*f*f*m,b=6*h*h*g,x=6*d*d*p,A=o*_+l*v+c*S,P=o*y+l*M+c*T,R=o*w+l*b+c*x;u=u-A*P/(P*P-.5*A*R)}return u}function Lf(n,e){let t=z3(n,e),i=to({l:1,a:t*n,b:t*e}),r=Math.cbrt(1/Math.max(i.r,i.g,i.b)),s=r*t;return[r,s]}function G3(n,e,t,i,r,s=null){s||(s=Lf(n,e));let a;if((t-r)*s[1]-(s[0]-r)*i<=0)a=s[1]*r/(i*s[0]+s[1]*(r-t));else{a=s[1]*(r-1)/(i*(s[0]-1)+s[1]*(r-t));{let o=t-r,l=i,c=.3963377774*n+.2158037573*e,u=-.1055613458*n-.0638541728*e,f=-.0894841775*n-1.291485548*e,h=o+l*c,d=o+l*u,m=o+l*f;{let g=r*(1-a)+a*t,p=a*i,_=g+p*c,v=g+p*u,S=g+p*f,y=_*_*_,M=v*v*v,T=S*S*S,w=3*h*_*_,b=3*d*v*v,x=3*m*S*S,A=6*h*h*_,P=6*d*d*v,R=6*m*m*S,L=4.0767416621*y-3.3077115913*M+.2309699292*T-1,I=4.0767416621*w-3.3077115913*b+.2309699292*x,N=4.0767416621*A-3.3077115913*P+.2309699292*R,O=I/(I*I-.5*L*N),B=-L*O,q=-1.2684380046*y+2.6097574011*M-.3413193965*T-1,F=-1.2684380046*w+2.6097574011*b-.3413193965*x,k=-1.2684380046*A+2.6097574011*P-.3413193965*R,U=F/(F*F-.5*q*k),z=-q*U,K=-.0041960863*y-.7034186147*M+1.707614701*T-1,Z=-.0041960863*w-.7034186147*b+1.707614701*x,X=-.0041960863*A-.7034186147*P+1.707614701*R,H=Z/(Z*Z-.5*K*X),V=-K*H;B=O>=0?B:1e6,z=U>=0?z:1e6,V=H>=0?V:1e6,a+=Math.min(B,Math.min(z,V))}}}return a}function If(n,e,t=null){t||(t=Lf(n,e));let i=t[0],r=t[1];return[r/i,r/(1-i)]}function Xg(n,e,t){let i=Lf(e,t),r=G3(e,t,n,1,n,i),s=If(e,t,i),a=.11516993+1/(7.4477897+4.1590124*t+e*(-2.19557347+1.75198401*t+e*(-2.13704948-10.02301043*t+e*(-4.24894561+5.38770819*t+4.69891013*e)))),o=.11239642+1/(1.6132032-.68124379*t+e*(.40370612+.90148123*t+e*(-.27087943+.6122399*t+e*(.00299215-.45399568*t-.14661872*e)))),l=r/Math.min(n*s[0],(1-n)*s[1]),c=n*a,u=(1-n)*o,f=.9*l*Math.sqrt(Math.sqrt(1/(1/(c*c*c*c)+1/(u*u*u*u))));return c=n*.4,u=(1-n)*.8,[Math.sqrt(1/(1/(c*c)+1/(u*u))),f,r]}function im(n){const e=n.l!==void 0?n.l:0,t=n.a!==void 0?n.a:0,i=n.b!==void 0?n.b:0,r={mode:"okhsl",l:Xh(e)};n.alpha!==void 0&&(r.alpha=n.alpha);let s=Math.sqrt(t*t+i*i);if(!s)return r.s=0,r;let[a,o,l]=Xg(e,t/s,i/s),c;if(s<o){let u=0,f=.8*a,h=1-f/o;c=(s-u)/(f+h*(s-u))*.8}else{let u=o,f=.2*o*o*1.25*1.25/a,h=1-f/(l-o);c=.8+.2*((s-u)/(f+h*(s-u)))}return c&&(r.s=c,r.h=fn(Math.atan2(i,t)*180/Math.PI)),r}function rm(n){let e=n.h!==void 0?n.h:0,t=n.s!==void 0?n.s:0,i=n.l!==void 0?n.l:0;const r={mode:"oklab",l:Pl(i)};if(n.alpha!==void 0&&(r.alpha=n.alpha),!t||i===1)return r.a=r.b=0,r;let s=Math.cos(e/180*Math.PI),a=Math.sin(e/180*Math.PI),[o,l,c]=Xg(r.l,s,a),u,f,h,d;t<.8?(u=1.25*t,f=0,h=.8*o,d=1-h/l):(u=5*(t-.8),f=l,h=.2*l*l*1.25*1.25/o,d=1-h/(c-l));let m=f+u*h/(1-d*u);return r.a=m*s,r.b=m*a,r}const H3={...Rg,mode:"okhsl",channels:["h","s","l","alpha"],parse:["--okhsl"],serialize:"--okhsl",fromMode:{oklab:im,rgb:n=>im(Kl(n))},toMode:{oklab:rm,rgb:n=>Zl(rm(n))}};function sm(n){let e=n.l!==void 0?n.l:0,t=n.a!==void 0?n.a:0,i=n.b!==void 0?n.b:0,r=Math.sqrt(t*t+i*i),s=r?t/r:1,a=r?i/r:1,[o,l]=If(s,a),c=.5,u=1-c/o,f=l/(r+e*l),h=f*e,d=f*r,m=Pl(h),g=d*m/h,p=to({l:m,a:s*g,b:a*g}),_=Math.cbrt(1/Math.max(p.r,p.g,p.b,0));e=e/_,r=r/_*Xh(e)/e,e=Xh(e);const v={mode:"okhsv",s:r?(c+l)*d/(l*c+l*u*d):0,v:e?e/h:0};return v.s&&(v.h=fn(Math.atan2(i,t)*180/Math.PI)),n.alpha!==void 0&&(v.alpha=n.alpha),v}function am(n){const e={mode:"oklab"};n.alpha!==void 0&&(e.alpha=n.alpha);const t=n.h!==void 0?n.h:0,i=n.s!==void 0?n.s:0,r=n.v!==void 0?n.v:0,s=Math.cos(t/180*Math.PI),a=Math.sin(t/180*Math.PI),[o,l]=If(s,a),c=.5,u=1-c/o,f=1-i*c/(c+l-l*u*i),h=i*l*c/(c+l-l*u*i),d=Pl(f),m=h*d/f,g=to({l:d,a:s*m,b:a*m}),p=Math.cbrt(1/Math.max(g.r,g.g,g.b,0)),_=Pl(r*f),v=h*_/f;return e.l=_*p,e.a=v*s*p,e.b=v*a*p,e}const V3={...Dg,mode:"okhsv",channels:["h","s","v","alpha"],parse:["--okhsv"],serialize:"--okhsv",fromMode:{oklab:sm,rgb:n=>sm(Kl(n))},toMode:{oklab:am,rgb:n=>Zl(am(n))}};function W3(n,e){if(!e||e[0]!=="oklab")return;const t={mode:"oklab"},[,i,r,s,a]=e;if(!(i.type===Ce.Hue||r.type===Ce.Hue||s.type===Ce.Hue))return i.type!==Ce.None&&(t.l=Math.min(Math.max(0,i.type===Ce.Number?i.value:i.value/100),1)),r.type!==Ce.None&&(t.a=r.type===Ce.Number?r.value:r.value*.4/100),s.type!==Ce.None&&(t.b=s.type===Ce.Number?s.value:s.value*.4/100),a.type!==Ce.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ce.Number?a.value:a.value/100))),t}const X3={...Df,mode:"oklab",toMode:{lrgb:to,rgb:Zl},fromMode:{lrgb:Wg,rgb:Kl},ranges:{l:[0,1],a:[-.4,.4],b:[-.4,.4]},parse:[W3],serialize:n=>`oklab(${n.l!==void 0?n.l:"none"} ${n.a!==void 0?n.a:"none"} ${n.b!==void 0?n.b:"none"}${n.alpha<1?` / ${n.alpha}`:""})`};function j3(n,e){if(!e||e[0]!=="oklch")return;const t={mode:"oklch"},[,i,r,s,a]=e;if(i.type!==Ce.None){if(i.type===Ce.Hue)return;t.l=Math.min(Math.max(0,i.type===Ce.Number?i.value:i.value/100),1)}if(r.type!==Ce.None&&(t.c=Math.max(0,r.type===Ce.Number?r.value:r.value*.4/100)),s.type!==Ce.None){if(s.type===Ce.Percentage)return;t.h=s.value}return a.type!==Ce.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ce.Number?a.value:a.value/100))),t}const Y3={...Uf,mode:"oklch",toMode:{oklab:n=>wr(n,"oklab"),rgb:n=>Zl(wr(n,"oklab"))},fromMode:{rgb:n=>Er(Kl(n),"oklch"),oklab:n=>Er(n,"oklch")},parse:[j3],serialize:n=>`oklch(${n.l!==void 0?n.l:"none"} ${n.c!==void 0?n.c:"none"} ${n.h!==void 0?n.h:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,ranges:{l:[0,1],c:[0,.4],h:[0,360]}},om=n=>{let{r:e,g:t,b:i,alpha:r}=ea(n),s={mode:"xyz65",x:.486570948648216*e+.265667693169093*t+.1982172852343625*i,y:.2289745640697487*e+.6917385218365062*t+.079286914093745*i,z:0*e+.0451133818589026*t+1.043944368900976*i};return r!==void 0&&(s.alpha=r),s},lm=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=ta({r:n*2.4934969119414263-e*.9313836179191242-.402710784450717*t,g:n*-.8294889695615749+e*1.7626640603183465+.0236246858419436*t,b:n*.0358458302437845-e*.0761723892680418+.9568845240076871*t},"p3");return i!==void 0&&(r.alpha=i),r},q3={...Qs,mode:"p3",parse:["display-p3"],serialize:"display-p3",fromMode:{rgb:n=>lm(ts(n)),xyz65:lm},toMode:{rgb:n=>ns(om(n)),xyz65:om}},gu=n=>{let e=Math.abs(n);return e>=1/512?Math.sign(n)*Math.pow(e,1/1.8):16*n},cm=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"prophoto",r:gu(n*1.3457868816471585-e*.2555720873797946-.0511018649755453*t),g:gu(n*-.5446307051249019+e*1.5082477428451466+.0205274474364214*t),b:gu(n*0+e*0+1.2119675456389452*t)};return i!==void 0&&(r.alpha=i),r},_u=(n=0)=>{let e=Math.abs(n);return e>=16/512?Math.sign(n)*Math.pow(e,1.8):n/16},um=n=>{let e=_u(n.r),t=_u(n.g),i=_u(n.b),r={mode:"xyz50",x:.7977666449006423*e+.1351812974005331*t+.0313477341283922*i,y:.2880748288194013*e+.7118352342418731*t+899369387256e-16*i,z:0*e+0*t+.8251046025104602*i};return n.alpha!==void 0&&(r.alpha=n.alpha),r},K3={...Qs,mode:"prophoto",parse:["prophoto-rgb"],serialize:"prophoto-rgb",fromMode:{xyz50:cm,rgb:n=>cm(eo(n))},toMode:{xyz50:um,rgb:n=>Qa(um(n))}},hm=1.09929682680944,Z3=.018053968510807,vu=n=>{const e=Math.abs(n);return e>Z3?(Math.sign(n)||1)*(hm*Math.pow(e,.45)-(hm-1)):4.5*n},fm=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"rec2020",r:vu(n*1.7166511879712683-e*.3556707837763925-.2533662813736599*t),g:vu(n*-.6666843518324893+e*1.6164812366349395+.0157685458139111*t),b:vu(n*.0176398574453108-e*.0427706132578085+.9421031212354739*t)};return i!==void 0&&(r.alpha=i),r},dm=1.09929682680944,$3=.018053968510807,xu=(n=0)=>{let e=Math.abs(n);return e<$3*4.5?n/4.5:(Math.sign(n)||1)*Math.pow((e+dm-1)/dm,1/.45)},pm=n=>{let e=xu(n.r),t=xu(n.g),i=xu(n.b),r={mode:"xyz65",x:.6369580483012911*e+.1446169035862083*t+.1688809751641721*i,y:.262700212011267*e+.6779980715188708*t+.059301716469862*i,z:0*e+.0280726930490874*t+1.0609850577107909*i};return n.alpha!==void 0&&(r.alpha=n.alpha),r},J3={...Qs,mode:"rec2020",fromMode:{xyz65:fm,rgb:n=>fm(ts(n))},toMode:{xyz65:pm,rgb:n=>ns(pm(n))},parse:["rec2020"],serialize:"rec2020"},Kr=.0037930732552754493,jg=Math.cbrt(Kr),yu=n=>Math.cbrt(n)-jg,Q3=n=>{const{r:e,g:t,b:i,alpha:r}=ea(n),s=yu(.3*e+.622*t+.078*i+Kr),a=yu(.23*e+.692*t+.078*i+Kr),o=yu(.2434226892454782*e+.2047674442449682*t+.5518098665095535*i+Kr),l={mode:"xyb",x:(s-a)/2,y:(s+a)/2,b:o-(s+a)/2};return r!==void 0&&(l.alpha=r),l},bu=n=>Math.pow(n+jg,3),ew=({x:n,y:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r=bu(n+e)-Kr,s=bu(e-n)-Kr,a=bu(t+e)-Kr,o=ta({r:11.031566904639861*r-9.866943908131562*s-.16462299650829934*a,g:-3.2541473810744237*r+4.418770377582723*s-.16462299650829934*a,b:-3.6588512867136815*r+2.7129230459360922*s+1.9459282407775895*a});return i!==void 0&&(o.alpha=i),o},tw={mode:"xyb",channels:["x","y","b","alpha"],parse:["--xyb"],serialize:"--xyb",toMode:{rgb:ew},fromMode:{rgb:Q3},ranges:{x:[-.0154,.0281],y:[0,.8453],b:[-.2778,.388]},interpolate:{x:ze,y:ze,b:ze,alpha:{use:ze,fixup:tn}}},nw={mode:"xyz50",parse:["xyz-d50"],serialize:"xyz-d50",toMode:{rgb:Qa,lab:Pf},fromMode:{rgb:eo,lab:Cf},channels:["x","y","z","alpha"],ranges:{x:[0,.964],y:[0,.999],z:[0,.825]},interpolate:{x:ze,y:ze,z:ze,alpha:{use:ze,fixup:tn}}},iw=n=>{let{x:e,y:t,z:i,alpha:r}=n;e===void 0&&(e=0),t===void 0&&(t=0),i===void 0&&(i=0);let s={mode:"xyz50",x:1.0479298208405488*e+.0229467933410191*t-.0501922295431356*i,y:.0296278156881593*e+.990434484573249*t-.0170738250293851*i,z:-.0092430581525912*e+.0150551448965779*t+.7518742899580008*i};return r!==void 0&&(s.alpha=r),s},rw=n=>{let{x:e,y:t,z:i,alpha:r}=n;e===void 0&&(e=0),t===void 0&&(t=0),i===void 0&&(i=0);let s={mode:"xyz65",x:.9554734527042182*e-.0230985368742614*t+.0632593086610217*i,y:-.0283697069632081*e+1.0099954580058226*t+.021041398966943*i,z:.0123140016883199*e-.0205076964334779*t+1.3303659366080753*i};return r!==void 0&&(s.alpha=r),s},sw={mode:"xyz65",toMode:{rgb:ns,xyz50:iw},fromMode:{rgb:ts,xyz50:rw},ranges:{x:[0,.95],y:[0,1],z:[0,1.088]},channels:["x","y","z","alpha"],parse:["xyz","xyz-d65"],serialize:"xyz-d65",interpolate:{x:ze,y:ze,z:ze,alpha:{use:ze,fixup:tn}}},aw=({r:n,g:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r={mode:"yiq",y:.29889531*n+.58662247*e+.11448223*t,i:.59597799*n-.2741761*e-.32180189*t,q:.21147017*n-.52261711*e+.31114694*t};return i!==void 0&&(r.alpha=i),r},ow=({y:n,i:e,q:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r={mode:"rgb",r:n+.95608445*e+.6208885*t,g:n-.27137664*e-.6486059*t,b:n-1.10561724*e+1.70250126*t};return i!==void 0&&(r.alpha=i),r},lw={mode:"yiq",toMode:{rgb:ow},fromMode:{rgb:aw},channels:["y","i","q","alpha"],parse:["--yiq"],serialize:"--yiq",ranges:{i:[-.595,.595],q:[-.522,.522]},interpolate:{y:ze,i:ze,q:ze,alpha:{use:ze,fixup:tn}}},cw=n=>{n[0]===void 0&&(n[0]=0),n[n.length-1]===void 0&&(n[n.length-1]=1);let e=1,t,i,r,s;for(;e<n.length;){if(n[e]===void 0){for(i=e,r=n[e-1],t=e;n[t]===void 0;)t++;for(s=(n[t]-r)/(t-e+1);e<t;)n[e]=r+(e+1-i)*s,e++}else n[e]<n[e-1]&&(n[e]=n[e-1]);e++}return n},uw=(n=.5)=>e=>n<=0?1:n>=1?0:Math.pow(e,Math.log(.5)/Math.log(n)),Wo=n=>typeof n=="function",Nr=n=>n&&typeof n=="object",mm=n=>typeof n=="number",hw=(n,e="rgb",t,i)=>{let r=yg(e),s=Af(e),a=[],o=[],l={};n.forEach(h=>{Array.isArray(h)?(a.push(s(h[0])),o.push(h[1])):mm(h)||Wo(h)?l[o.length]=h:(a.push(s(h)),o.push(void 0))}),cw(o);let c=r.channels.reduce((h,d)=>{let m;return Nr(t)&&Nr(t[d])&&t[d].fixup?m=t[d].fixup:Nr(r.interpolate[d])&&r.interpolate[d].fixup?m=r.interpolate[d].fixup:m=g=>g,h[d]=m(a.map(g=>g[d])),h},{}),u=r.channels.reduce((h,d)=>{let m;return Wo(t)?m=t:Nr(t)&&Wo(t[d])?m=t[d]:Nr(t)&&Nr(t[d])&&t[d].use?m=t[d].use:Wo(r.interpolate[d])?m=r.interpolate[d]:Nr(r.interpolate[d])&&(m=r.interpolate[d].use),h[d]=m(c[d]),h},{}),f=a.length-1;return h=>{if(h=Math.min(Math.max(0,h),1),h<=o[0])return a[0];if(h>o[f])return a[f];let d=0;for(;o[d]<h;)d++;let m=o[d-1],g=o[d]-m,p=(h-m)/g,_=l[d]||l[0];_!==void 0&&(mm(_)&&(_=uw((_-m)/g)),p=_(p));let v=(d-1+p)/f;return r.channels.reduce((S,y)=>{let M=u[y](v);return M!==void 0&&(S[y]=M),S},{mode:e})}},fw=(n,e="rgb",t)=>hw(n,e,t);yt(KE);yt(n3);yt(i3);yt(r3);yt(o3);yt(Rg);yt(Dg);yt(_3);yt(v3);yt(S3);yt(M3);yt(Df);yt(E3);yt(Uf);yt(A3);yt(O3);yt(B3);yt(k3);yt(H3);yt(V3);yt(X3);yt(Y3);yt(q3);yt(K3);yt(J3);yt(Qs);yt(tw);yt(nw);yt(sw);yt(lw);function ui(n){let e=n>>>0;return()=>{e|=0,e=e+1831565813|0;let t=Math.imul(e^e>>>15,1|e);return t=t+Math.imul(t^t>>>7,61|t)^t,((t^t>>>14)>>>0)/4294967296}}const dw=[{id:"beidou",name_zh:"北斗",lore:"天枢·北斗之首，主枢机；七星斟酌元气，运乎中央，临制四方",stars:[{x:-.6456,y:.4576,mag:1.81,name:"天枢"},{x:-.7715,y:.1074,mag:2.34,name:"天璇"},{x:-.3043,y:-.1753,mag:2.41,name:"天玑"},{x:-.08,y:.0366,mag:3.32,name:"天权"},{x:.2846,y:-.0219,mag:1.76,name:"玉衡"},{x:.5838,y:-.0447,mag:2.23,name:"开阳"},{x:.9331,y:-.3597,mag:1.85,name:"摇光"}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6]]},{id:"beiji",name_zh:"北极",lore:"北极五星，紫微中枢，帝星所居——北辰居其所而众星共之",stars:[{x:.4553,y:-.5791,mag:3},{x:.141,y:-.3243,mag:2.07},{x:-.053,y:-.1338,mag:4.25},{x:-.1729,y:.1083,mag:4.8},{x:-.3703,y:.9289,mag:5.38}],lines:[[0,1],[1,2],[2,3],[3,4]]},{id:"gouchen",name_zh:"勾陈",lore:"勾陈六星，天皇大帝之御座，主后宫，亦掌兵革",stars:[{x:.572,y:.2057,mag:4.7},{x:.3764,y:.489,mag:4.24},{x:.0615,y:.418,mag:1.97},{x:-.04,y:.0144,mag:4.35},{x:-.2588,y:-.4241,mag:4.21},{x:-.7112,y:-.703,mag:4.29}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5]]},{id:"ziwei_zuoyuan",name_zh:"紫微左垣",lore:"紫微东藩，左垣八星，如臣卫帝庭之左",stars:[{x:-.6802,y:-.3579,mag:3.29},{x:-.5188,y:-.4593,mag:4.01},{x:-.3731,y:-.3887,mag:2.73},{x:-.1488,y:-.2772,mag:3.17},{x:.1973,y:-.0506,mag:4.82},{x:.3691,y:.1925,mag:5.18},{x:.5624,y:.5353,mag:4.41},{x:.5921,y:.8058,mag:5.42}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7]]},{id:"ziwei_youyuan",name_zh:"紫微右垣",lore:"紫微西藩，右垣七星，如臣卫帝庭之右",stars:[{x:.9449,y:.203,mag:3.67},{x:.5853,y:-3e-4,mag:3.85},{x:.4498,y:-.1479,mag:3.82},{x:.1037,y:-.2654,mag:4.54},{x:-.393,y:-.1982,mag:5.11},{x:-.7644,y:.0323,mag:4.26},{x:-.9264,y:.3765,mag:4.74}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6]]},{id:"huagai",name_zh:"华盖",lore:"华盖七星，覆于帝座之上，主遮护銮驾",stars:[{x:-.0126,y:.128,mag:5.82},{x:.1535,y:.9881,mag:5.28},{x:-.3751,y:.597,mag:5.87},{x:-.5879,y:-.3058,mag:5.32},{x:-.1661,y:-.5295,mag:4.72},{x:.307,y:-.5517,mag:5.57},{x:.681,y:-.3262,mag:4.97}],lines:[[0,1],[0,2],[0,3],[0,4],[0,5],[0,6]]},{id:"wenchang",name_zh:"文昌",lore:"文昌六星，司禄主文，掌天下文运科名",stars:[{x:.4513,y:.8924,mag:3.78},{x:.5423,y:.002,mag:4.55},{x:.0387,y:-.4454,mag:3.17},{x:-.6297,y:-.4344,mag:4.46},{x:-.4025,y:-.0145,mag:4.8}],lines:[[0,1],[1,2],[2,3],[3,4]]},{id:"santai",name_zh:"三台",lore:"三台六星，上下两阶，天子陟降之梯，主德政升降",stars:[{x:-.8426,y:.5181,mag:3.12},{x:-.8074,y:.4499,mag:3.57},{x:-.0157,y:.0855,mag:3.45},{x:.0452,y:-.0028,mag:3.06},{x:.8033,y:-.4744,mag:3.49},{x:.8172,y:-.5763,mag:3.79}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5]]},{id:"wudi_neizuo",name_zh:"五帝内座",lore:"五帝内座五星，五方天帝之便座，承帝居于紫微",stars:[{x:.0387,y:-.0175,mag:5.49},{x:-.8678,y:-.4969,mag:5.27},{x:-.1558,y:.5448,mag:5.8},{x:.2515,y:-.4707,mag:5.44},{x:.7334,y:.4402,mag:5.1}],lines:[[0,1],[0,2],[0,3],[0,4]]},{id:"taiwei_zuoyuan",name_zh:"太微左垣",lore:"太微东藩，左垣五星，列卿大夫之位",stars:[{x:-.5895,y:-.524,mag:3.89},{x:-.1576,y:-.5858,mag:2.74},{x:.1166,y:-.203,mag:3.39},{x:.2419,y:.3914,mag:2.85},{x:.3886,y:.9214,mag:4.32}],lines:[[0,1],[1,2],[2,3],[3,4]]},{id:"taiwei_youyuan",name_zh:"太微右垣",lore:"太微西藩，右垣五星，列将相之班",stars:[{x:.5787,y:-.8155,mag:3.59},{x:-.0877,y:-.4314,mag:4.05},{x:-.0255,y:-.0301,mag:4},{x:-.2334,y:.408,mag:3.33},{x:-.2322,y:.869,mag:2.56}],lines:[[0,1],[1,2],[2,3],[3,4]]},{id:"wudizuo",name_zh:"五帝座",lore:"太微之中，五帝座五星，天子临朝听政之正位",stars:[{x:-.0986,y:-.0128,mag:2.14},{x:-.0792,y:.7029,mag:6.05},{x:-.5008,y:-.1439,mag:6.51},{x:.5836,y:.4493,mag:5.53},{x:.095,y:-.9955,mag:6.37}],lines:[[0,1],[0,2],[0,3],[0,4]]},{id:"tianshi_zuoyuan",name_zh:"天市左垣",lore:"天市东藩，十一星以诸侯为名，主四方商贾之事",stars:[{x:-.3742,y:.5321,mag:3.12},{x:-.2501,y:.5673,mag:4.41},{x:-.1289,y:.6184,mag:3.42},{x:.0299,y:.6533,mag:3.84},{x:.3792,y:.4119,mag:5.43},{x:.4972,y:.1634,mag:2.99},{x:.4329,y:-.1618,mag:4.62},{x:.1464,y:-.4012,mag:3.23},{x:-.0391,y:-.6417,mag:3.32},{x:-.2253,y:-.8579,mag:3.54},{x:-.4681,y:-.8837,mag:2.43}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10]]},{id:"tianshi_youyuan",name_zh:"天市右垣",lore:"天市西藩，十一星以都邑为号，主市井度量之制",stars:[{x:.2745,y:.6377,mag:2.78},{x:.182,y:.5196,mag:3.74},{x:.0256,y:.4156,mag:5},{x:-.1068,y:.35,mag:3.85},{x:-.2244,y:.3403,mag:3.65},{x:-.3602,y:.1113,mag:3.8},{x:-.2522,y:-.0849,mag:2.63},{x:-.1762,y:-.1775,mag:3.71},{x:.1023,y:-.5699,mag:2.73},{x:.1504,y:-.6193,mag:3.23},{x:.385,y:-.9229,mag:2.54}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10]]},{id:"jiao",name_zh:"角宿",lore:"东方苍龙之首，角二星为天门，主万物生发",stars:[{x:-.2177,y:-.976,mag:.98},{x:.2177,y:.976,mag:3.38}],lines:[[0,1]]},{id:"kang",name_zh:"亢宿",lore:"苍龙之颈，亢四星，主朝廷礼乐，亦司疾疫",stars:[{x:-.2463,y:-.3728,mag:4.18},{x:-.1236,y:.3179,mag:4.07},{x:.3693,y:.9293,mag:4.81},{x:6e-4,y:-.8744,mag:4.52}],lines:[[0,1],[1,2],[0,3]]},{id:"xin",name_zh:"心宿",lore:"苍龙之心，心三星为天王明堂，心宿二即大火，观之以授时",stars:[{x:-.7951,y:.5347,mag:2.9},{x:.0663,y:.1501,mag:1.06},{x:.7288,y:-.6848,mag:2.82}],lines:[[0,1],[1,2]]},{id:"dou",name_zh:"斗宿",lore:"北方玄武之首，南斗六星，主爵禄寿命之权衡",stars:[{x:-.8231,y:.5679,mag:3.84},{x:-.4305,y:.0908,mag:2.82},{x:.0174,y:-.0783,mag:3.17},{x:.259,y:-.003,mag:2.05},{x:.5468,y:-.1665,mag:3.32},{x:.4303,y:-.4109,mag:2.6}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5]]},{id:"kui",name_zh:"奎宿",lore:"西方白虎之库，奎十六星如破鞋，主文章武库",stars:[{x:-.0516,y:-.5016,mag:4.4},{x:-.2394,y:-.4275,mag:4.08},{x:-.1846,y:-.1406,mag:5.55},{x:-.388,y:-2e-4,mag:4.34},{x:-.3683,y:.1285,mag:3.27},{x:-.4004,y:.3699,mag:4.34},{x:-.1616,y:.9869,mag:4.53},{x:-.0518,y:.7626,mag:3.86},{x:.1675,y:.5204,mag:2.07},{x:.111,y:.2309,mag:6.28},{x:.2121,y:.0585,mag:4.51},{x:.3882,y:-.0482,mag:5.23},{x:.363,y:-.1725,mag:4.74},{x:.2634,y:-.4004,mag:4.67},{x:.2272,y:-.7012,mag:4.66},{x:.1132,y:-.6655,mag:5.33}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10],[10,11],[11,12],[12,13],[13,14],[14,15],[15,0]]},{id:"bi",name_zh:"毕宿",lore:"白虎之网，毕八星，主边兵弋猎，毕宿五为虎视",stars:[{x:.1127,y:.4028,mag:3.53},{x:.0087,y:.226,mag:4.3},{x:-.077,y:.1719,mag:3.77},{x:-.1842,y:-.0971,mag:3.65},{x:.3609,y:.0288,mag:.87},{x:.1132,y:-.0504,mag:3.84},{x:.0378,y:-.099,mag:4.48},{x:-.8479,y:-.5301,mag:3.41},{x:.4757,y:-.0529,mag:4.67}],lines:[[0,1],[1,2],[2,3],[4,5],[5,6],[6,3],[3,7],[4,8]]},{id:"shen",name_zh:"参宿",lore:"白虎之躯，参宿七星，中三星为腰带，主斩刈权衡",stars:[{x:.4907,y:.8713,mag:.45},{x:.1222,y:-.0875,mag:1.74},{x:.0069,y:-.0122,mag:1.69},{x:-.1,y:.0795,mag:2.25},{x:-.5438,y:-.7306,mag:.18},{x:-.2754,y:.7598,mag:1.64},{x:.2993,y:-.8803,mag:2.07}],lines:[[0,1],[1,2],[2,3],[3,4],[3,5],[1,6]]},{id:"liu",name_zh:"柳宿",lore:"南方朱雀之喙，柳八星，主草木庖厨",stars:[{x:-.1153,y:.1717,mag:4.35},{x:-.3232,y:-.2171,mag:4.3},{x:-.5015,y:-.2258,mag:4.45},{x:-.5436,y:.1519,mag:4.14},{x:-.1808,y:.2646,mag:3.38},{x:.1609,y:.189,mag:3.11},{x:.5821,y:.0544,mag:4.99},{x:.9214,y:-.3887,mag:3.89}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7]]}],pw={asterisms:dw},Mt=100,Ff=Mt/400,Ua=.3*Mt,hr=.54*Mt,mw=.95*Mt,Su=Mt+22*Ff,Xo=Mt+52*Ff,Mu=Mt+37*Ff,gw=-160,mn=15262418,gm=14462549,_w=15781247,al=[-145,-72,-2,52,160],_m=[-108,-37,25,106,-170],vm=["天枢","天璇","天玑","天权","玉衡","开阳","摇光"],vw=[...al,200,262],Mn={blueWhite:[.78,.86,1],moonWhite:[.949,.929,.878],warmGold:[.98,.8,.45],softOrange:[.93,.66,.44]},xw=new Map(pw.asterisms.map(n=>[n.id,n])),Yg={系统:{id:"dou",name:"斗宿"},学习力:{id:"kui",name:"奎宿"},基础:{id:"huagai",name:"华盖"},操作:{id:"shen",name:"参宿"},感知:{id:"bi",name:"毕宿"},研究:{id:"wenchang",name:"文昌"},中间件:{id:"kang",name:"亢宿"},影响力:{id:"liu",name:"柳宿"},导航:{id:"yi",name:"翼宿"},战略:{id:"fang",name:"房宿"},运动:{id:"ji",name:"箕宿"},控制:{id:"zhen",name:"轸宿"},领导力:{id:"xuanyuan",name:"轩辕"},仿真:{id:"xu",name:"虚宿"}};function yw(n){var e;return((e=Yg[n])==null?void 0:e.name)??n}const xm=[{slots:[[0,4,1.15],[-.5,-1.5,.68],[-4,-6,.62],[-8,-8.5,.78],[-11.2,-7.2,.58],[3,-5.5,.62],[6.8,-7.8,.72]],links:[[0,1],[1,2],[2,3],[3,4],[1,5],[5,6]]},{slots:[[-11.8,2.8,.62],[-6,.5,.72],[-.5,-1,.92],[5,-.5,.68],[10.8,1.8,.6]],links:[[0,1],[1,2],[2,3],[3,4]]},{slots:[[-8.8,-1.8,.62],[-4.5,2,.7],[0,3.5,.9],[4.5,2,.7],[8.8,-1.8,.62]],links:[[0,1],[1,2],[2,3],[3,4]]},{slots:[[-2,-1.2,.85],[2.2,-.8,.65],[0,2,.6]],links:[[0,1],[1,2],[2,0]]},{slots:[[-9.2,-2.5,.62],[-4,2.2,.72],[1,-2.2,.82],[6,2.5,.65],[10.2,-.8,.6]],links:[[0,1],[1,2],[2,3],[3,4]]}],bw=[[-40,18,.72,1],[-78,11.5,.6,0],[-112,15.5,.68,0],[-148,12.5,.58,0],[168,19,.78,1],[142,11.5,.58,0],[116,17,.65,0],[88,11,.58,0],[58,15,.72,1],[34,21,.6,0],[-32,24,.62,0],[-95,22.5,.65,1]],Sw=[[0,1],[1,2],[2,3],[5,6],[6,7],[8,9]];function bi(n,e){const t=e*Math.PI/180;return[n*Math.cos(t),n*Math.sin(t)]}function Mw(n){return n=n%360,n>180&&(n-=360),n<-180&&(n+=360),n}function Tw(n){const e=ui(20260921),t=n.categories.reduce((F,k)=>F+k.count,0)||1,i=[];let r=gw;for(const F of n.categories){const k=F.count/t*360;i.push({id:F.id,name:F.name,asterism:yw(F.name),start:r,width:k,count:F.count,figRadius:0}),r+=k}const s=F=>i.find(k=>k.id===F),a=[.961,.918,.824],o={plan:[],deep:[],size:[],opacity:[],core:[],ring:[],legacyRing:[],color:[],deepColor:[],filler:[],deepOpScale:[],deepSizeScale:[]},l=(F,k,U,z,K,Z,X,H,V,j,le,ge,oe,te,xe=Mn.moonWhite)=>{o.plan.push(F,k,0),o.deep.push(U,z,K),o.size.push(Z),o.opacity.push(X),o.core.push(ge),o.ring.push(oe),o.legacyRing.push(te),o.color.push(V[0],V[1],V[2]),o.deepColor.push(xe[0],xe[1],xe[2]),o.filler.push(H?1:0),o.deepOpScale.push(j),o.deepSizeScale.push(le)},c=()=>[(e()*2-1)*250,(e()*2-1)*140,40-e()*180],u=new Map;for(const F of n.skills)u.has(F.category)||u.set(F.category,[]),u.get(F.category).push(F);for(const F of n.skills){if(F.lit||F.status==="learning")continue;const k=s(F.category);if(!k)continue;const U=k.start+1.5+e()*(k.width-3),z=Mt*(.34+.58*Math.sqrt(e())),[K,Z]=bi(z,U),[X,H,V]=c();l(K,Z,X,H,V,.62+e()*.2,.34+e()*.08,!1,a,.6,.55,0,1,e()<.3?1:0)}const f=1800;for(const F of i){const k=Math.round(F.count/t*f);for(let U=0;U<k;U++){let z,K;if(e()<.15){if(z=e()*360,K=Ua*(.52+.46*e()),Math.abs(Mw(z))<25)continue}else z=F.start+1.3+e()*(F.width-2.6),K=Mt*(.33+.61*Math.sqrt(e()));const[Z,X]=bi(K,z),[H,V,j]=c(),le=[1,.88,.69],ge=[.74,.81,1],oe=e(),te=oe>.975?le:oe>.95?ge:a,xe=Math.pow(e(),8),Ae=xe>.42,Te=Math.min(1.15,.15+Math.pow(e(),1.8)*.55+xe*.75),ye=.35+Math.pow(e(),2)*.35+xe*.6,Ue=Ae?Mn.blueWhite:oe>.92?Mn.softOrange:oe>.88?Mn.warmGold:Mn.moonWhite;l(Z,X,H,V,j,Ae?.62:.34+e()*.22,Ae?.38:.1+e()*.12,!0,te,Te,ye,1,0,e()<.18?1:0,Ue)}}const h={plan:[],deep:[],size:[],opacity:[],core:[],ring:[],color:[],links:[],skills:[]},d={plan:[],deep:[],size:[],opacity:[],color:[]},m=[],g=new Map;n.evidence.forEach(F=>F.skill_ids.forEach(k=>g.set(k,(g.get(k)||0)+1)));let p=0;n.categories.forEach((F,k)=>{const U=s(F.id);if(!U)return;const z=Yg[F.name],K=z?xw.get(z.id):void 0,Z=(u.get(F.id)||[]).filter(te=>te.lit||te.status==="learning");if(!Z.length&&!z)return;const X=U.start+U.width/2,[H,V]=bi(Mt*.72,X),j=ui(500+k);let le,ge;if(K){const te=U.width*Math.PI/180*(Mt*.72),xe=Math.min(11,Math.max(6,te*.24)),Ae=(X-90)*Math.PI/180,Te=Math.cos(Ae),ye=Math.sin(Ae);le=K.stars.map(Ue=>{const me=Ue.mag??5,ke=.55+Math.min(3,Math.max(0,5.6-me))*.11;return[(Ue.x*Te-Ue.y*ye)*xe,(Ue.x*ye+Ue.y*Te)*xe,ke]}),ge=K.lines}else{const te=xm[k%xm.length];le=te.slots.map(xe=>[xe[0],xe[1],xe[2]]),ge=te.links}for(;le.length<Z.length;){const te=le[le.length-1];le.push([te[0]+4.5,te[1]+(j()-.5)*3,.58])}U.figRadius=le.reduce((te,xe)=>Math.max(te,Math.hypot(xe[0],xe[1])),0);for(const[te,xe]of ge)te>=le.length||xe>=le.length||m.push(H+le[te][0],V+le[te][1],0,H+le[xe][0],V+le[xe][1],0);const oe=p;Z.forEach((te,xe)=>{const[Ae,Te,ye]=le[xe],Ue=K?0:(j()-.5)*1.6,me=K?0:(j()-.5)*1.6,ke=H+Ae+Ue,G=V+Te+me,[fe,Fe,we]=c();h.plan.push(ke,G,0),h.deep.push(fe,Fe,we),h.size.push(ye*(te.lit?1.15:.9)),h.opacity.push(te.lit?.95:.55),h.core.push(1),h.ring.push(te.lit?1:0),h.color.push(.961,.918,.824),h.skills.push({id:te.id,label:te.label,category:te.category,status:te.status,evidenceCount:g.get(te.id)||0}),p+=1});for(let te=Z.length;te<le.length;te++){const[xe,Ae,Te]=le[te],[ye,Ue,me]=c();d.plan.push(H+xe,V+Ae,0),d.deep.push(ye,Ue,me),d.size.push(Math.max(.42,Te*.75)),d.opacity.push(.16),d.color.push(Mn.moonWhite[0],Mn.moonWhite[1],Mn.moonWhite[2])}if(Z.length>=3)for(const[te,xe]of ge)te<Z.length&&xe<Z.length&&h.links.push(oe+te,oe+xe)});const _=n.goals.filter(F=>F.status!=="completed"),v=n.goals.filter(F=>F.status==="completed"),y=[..._.slice(0,al.length).map((F,k)=>({g:F,angle:al[k],seat:k})),...v.slice(0,_m.length).map((F,k)=>({g:F,angle:_m[k],seat:-1}))].map(({g:F,angle:k,seat:U},z)=>{const[K,Z]=bi(hr,k),X=ui(900+z);return{id:F.id,title:F.title,status:F.status||"active",angle:k,seatName:U>=0?vm[U]:void 0,plan:[K,Z,0],deep:[K+(X()-.5)*10,Z+(X()-.5)*6,(X()-.5)*24]}}),M=vw.map((F,k)=>{var U;return{name:vm[k],angle:F,goalIndex:k<al.length&&((U=y[k])!=null&&U.seatName)?k:null}}),T={plan:[],size:[],gold:[],links:Sw};for(const[F,k,U,z]of bw){const[K,Z]=bi(k,F);T.plan.push(K,Z,0),T.size.push(U),T.gold.push(z)}const w=new Map(n.skills.map(F=>[F.id,F.category])),b=new Map(y.map((F,k)=>[F.id,k])),x=new Map(y.map(F=>[F.id,F.angle])),A=[-13,9,-6,15],P=new Map;let R=0;const L=[];n.projects.forEach(F=>{const k=(F.goal_ids||[]).find(V=>x.has(V));let U,z,K=-1;if(k!==void 0){K=b.get(k)??-1;const V=P.get(k)||0;P.set(k,V+1),U=x.get(k)+A[V%A.length],z=hr+(V%2===0?-10:10)}else U=-170+R*42,R+=1,z=hr+24;const[Z,X]=bi(z,U),H=ui(3e3+L.length);L.push({id:F.id,title:F.title,status:F.status,progress:F.progress,taskCount:F.task_count,goalIndex:K,plan:[Z,X,0],deep:[Z+(H()-.5)*8,X+(H()-.5)*8,(H()-.5)*10]})});const I={plan:[],deep:[],size:[],opacity:[]};L.forEach((F,k)=>{const U=ui(3100+k);for(let z=0;z<Math.min(F.taskCount,5);z++){const K=U()*360,Z=3.8+U()*2.4,[X,H]=bi(Z,K);I.plan.push(F.plan[0]+X,F.plan[1]+H,0),I.deep.push(F.deep[0]+X*1.3,F.deep[1]+H*1.3,F.deep[2]+(U()-.5)*4),I.size.push(.42),I.opacity.push(F.status==="active"?.55:.3)}});const N={weak:4,unrated:4,medium:6.5,strong:9,high_trust:12},O=[];n.evidence.filter(F=>F.flying).forEach((F,k)=>{const U=ui(3200+k),z=U()*360,K=Mt*(.42+.42*U()),[Z,X]=bi(K,z);O.push({id:F.id,title:F.title,date:F.date,strength:F.strength,review:F.review_status,plan:[Z,X,0],deep:[(U()*2-1)*230,(U()*2-1)*120,30-U()*150],tailDir:z+90+(U()-.5)*30,tailLen:N[F.strength]||5})});const B={plan:[],deep:[],size:[],opacity:[]};n.evidence.filter(F=>!F.flying).forEach((F,k)=>{const U=ui(3300+k);let z,K;const Z=F.project_refs.length&&L.find(X=>X.id===F.project_refs[0]);if(Z){const[X,H]=bi(5.5+U()*4,U()*360);z=Z.plan[0]+X,K=Z.plan[1]+H}else{const X=F.skill_ids.length?w.get(F.skill_ids[0]):void 0,H=X&&s(X)||i[Math.floor(U()*i.length)];if(!H)return;const V=H.start+2+U()*(H.width-4),j=Mt*(.45+.43*Math.sqrt(U()));[z,K]=bi(j,V)}B.plan.push(z,K,0),B.deep.push((U()*2-1)*240,(U()*2-1)*130,40-U()*170),B.size.push(.5),B.opacity.push(.4)});const q={plan:[],deep:[],size:[],opacity:[],trailPlan:[],trailDeep:[]};{const F=[-1.15*Mt,-.35*Mt],k=[-.42*Mt,.28*Mt],U=[.42*Mt,-.58*Mt],z=[1.15*Mt,.04*Mt],K=n.evidence.length;n.evidence.forEach((Z,X)=>{const H=ui(3400+X),V=K<=1?0:X/(K-1),j=1-V,le=j*j*j*F[0]+3*j*j*V*k[0]+3*j*V*V*U[0]+V*V*V*z[0],ge=j*j*j*F[1]+3*j*j*V*k[1]+3*j*V*V*U[1]+V*V*V*z[1];let oe=3*j*j*(k[0]-F[0])+6*j*V*(U[0]-k[0])+3*V*V*(z[0]-U[0]),te=3*j*j*(k[1]-F[1])+6*j*V*(U[1]-k[1])+3*V*V*(z[1]-U[1]);const xe=Math.hypot(oe,te)||1;oe/=xe,te/=xe;const Ae=le+(H()-.5)*10,Te=ge+(H()-.5)*10,ye=le*1.9+(H()-.5)*20,Ue=ge*1.9+(H()-.5)*16,me=30-V*130+(H()-.5)*20;q.plan.push(Ae,Te,0),q.deep.push(ye,Ue,me),q.trailPlan.push(Ae,Te,0,Ae-oe*2.6,Te-te*2.6,0),q.trailDeep.push(ye,Ue,me,ye-oe*4.9,Ue-te*4.9,me-2.2),q.size.push(.75),q.opacity.push(Z.review_status==="needs_review"?.38:.2)})}return{sectors:i,dim:o,lit:h,goals:y,seats:M,court:T,planets:L,moons:I,guests:O,seated:B,dust:q,etched:d,shapeLinesPlan:m}}const Ew="/assets/NotoSerifSC-subset-Cx3VUXg0.ttf",Ea="/assets/IMing-subset-Kpo8eYZB.ttf",jo="/assets/LXGWWenKai-subset-D9yc30St.ttf",ww="/assets/IMFellEnglish-subset-DL3qchp1.ttf",Tu=(n,e)=>Math.min(1,Math.max(0,(n-e)/.4));function ym(n,e){const t={plan:[],deep:[],size:[],opacity:[],core:[],ring:[],color:[],deepColor:[],filler:[],deepOpScale:[],deepSizeScale:[]};for(let i=0;i<n.filler.length;i++)n.filler[i]===1===e&&(t.plan.push(n.plan[i*3],n.plan[i*3+1],n.plan[i*3+2]),t.deep.push(n.deep[i*3],n.deep[i*3+1],n.deep[i*3+2]),t.size.push(n.size[i]),t.opacity.push(n.opacity[i]),t.core.push(n.core[i]),t.ring.push(n.ring[i]),t.color.push(n.color[i*3],n.color[i*3+1],n.color[i*3+2]),t.deepColor.push(n.deepColor[i*3],n.deepColor[i*3+1],n.deepColor[i*3+2]),t.filler.push(n.filler[i]),t.deepOpScale.push(n.deepOpScale[i]),t.deepSizeScale.push(n.deepSizeScale[i]));return t}class Aw{constructor(e,t,i,r={}){Ie(this,"root");Ie(this,"heart");Ie(this,"snapshot");Ie(this,"opts");Ie(this,"L");Ie(this,"renderer");Ie(this,"composer");Ie(this,"bloom");Ie(this,"fxPass");Ie(this,"scene",new ph);Ie(this,"camera");Ie(this,"chart",new Cs);Ie(this,"canvas");Ie(this,"bgStone");Ie(this,"bgDeep");Ie(this,"bgDusk");Ie(this,"vignette");Ie(this,"tooltip");Ie(this,"fadeMats",[]);Ie(this,"labelObjs",[]);Ie(this,"morphables",[]);Ie(this,"reveal");Ie(this,"dimPts");Ie(this,"dimBgPts");Ie(this,"bgLayer",new Cs);Ie(this,"litPts");Ie(this,"goalPts");Ie(this,"northPts");Ie(this,"northVacant");Ie(this,"planetPts");Ie(this,"guestPts");Ie(this,"planetInnerPts");Ie(this,"moonPts");Ie(this,"guestTails");Ie(this,"glows",[]);Ie(this,"guestGlows",[]);Ie(this,"nebulae",[]);Ie(this,"dustRiver",[]);Ie(this,"tiered",[]);Ie(this,"colored",[]);Ie(this,"goalLabelGroups",[]);Ie(this,"selRing");Ie(this,"controls",null);Ie(this,"state",{t:0,density:1,bloom:1,w1:0,w2:.3,w3:.6,duskPos:.45,duskAmt:1,ch1:0,ch2:0,ch3:0});Ie(this,"tween",null);Ie(this,"hoverIdx",-1);Ie(this,"selectedIdx",-1);Ie(this,"hoverables",[]);Ie(this,"clickables",[]);Ie(this,"focusTween",null);Ie(this,"focusToken",0);Ie(this,"dragging",!1);Ie(this,"dragLastX",0);Ie(this,"dragLastT",0);Ie(this,"dragDist",0);Ie(this,"spinVel",0);Ie(this,"spinFactor",1);Ie(this,"lastPointerActive",-1e9);Ie(this,"clock",new zv);Ie(this,"rafId",0);Ie(this,"disposed",!1);Ie(this,"resizeObserver",null);Ie(this,"labelsPending",0);Ie(this,"segPending",0);Ie(this,"reducedMotion");Ie(this,"coarsePointer");Ie(this,"softGL");Ie(this,"camPlan",{pos:new $(0,4,346),look:new $(0,0,0)});Ie(this,"camDeep",{pos:new $(0,72,232),look:new $(0,-4,0)});Ie(this,"goalPeriods");Ie(this,"planetPeriods");Ie(this,"guestPeriods");Ie(this,"goalPhase");Ie(this,"planetPhase");Ie(this,"guestPhase");Ie(this,"goalDeepBase");Ie(this,"planetDeepBase");Ie(this,"guestDeepBase");Ie(this,"moonDeepBase");Ie(this,"moonPlanet",[]);Ie(this,"tailOffsets",[]);Ie(this,"guestBaseOpacity");Ie(this,"onPointerMoveWindow",e=>this.onPointerMove(e));Ie(this,"onPointerActive",()=>{this.lastPointerActive=performance.now()});Ie(this,"onClickWindow",e=>this.onClick(e));Ie(this,"onKeydown",e=>{e.key==="Escape"&&this.closeDetail()});Ie(this,"onWheel",(()=>{let e=0;return t=>{e+=t.deltaY,Math.abs(e)>260&&(this.goTo(e<0?1:0),e=0)}})());var b;this.root=e,this.heart=t,this.snapshot=i,this.opts=r,this.L=Tw(i),this.northVacant=!(((b=i.north)==null?void 0:b.is_set)??i.north_star.trim().length>0),this.reducedMotion=matchMedia("(prefers-reduced-motion: reduce)").matches,this.coarsePointer=matchMedia("(pointer: coarse)").matches,this.reveal=r.reveal??!1,this.state.t=r.initialState==="deepspace"?1:0;const s=x=>{const A=document.createElement("div");return A.className=x,this.root.appendChild(A),A};this.bgStone=s("starmap-bg"),this.bgDusk=s("starmap-bg"),this.bgDeep=s("starmap-bg"),this.vignette=s("starmap-vignette"),this.canvas=document.createElement("canvas"),this.canvas.className="starmap-canvas",this.heart.appendChild(this.canvas),this.tooltip=s("starmap-tooltip"),this.tooltip.style.display="none",this.renderer=new OS({canvas:this.canvas,antialias:!0,alpha:!0}),this.renderer.setClearColor(0,0),this.renderer.setPixelRatio(Math.min(window.devicePixelRatio,2)),this.camera=new Gn(45,1,1,2e3),this.fitPlanCamera(),this.scene.add(this.chart),this.chart.add(this.bgLayer),this.bakeBackgrounds(),this.buildLinework();const a=ym(this.L.dim,!1),o=ym(this.L.dim,!0);this.dimPts=this.makePoints(a),this.dimBgPts=this.makePoints(o,this.bgLayer);for(const x of[this.dimPts,this.dimBgPts])x.userData.filler=x===this.dimBgPts?o.filler:a.filler,x.userData.baseOpacity=new Float32Array(x.geometry.attributes.aOpacity.array),x.userData.baseSize=new Float32Array(x.geometry.attributes.aSize.array),x.userData.baseRing=new Float32Array(x.geometry.attributes.aRing.array);this.dimPts.userData.deepOpScale=new Float32Array(a.deepOpScale),this.dimPts.userData.deepSizeScale=new Float32Array(a.deepSizeScale),this.dimBgPts.userData.deepOpScale=new Float32Array(o.deepOpScale),this.dimBgPts.userData.deepSizeScale=new Float32Array(o.deepSizeScale),this.litPts=this.makePoints({plan:this.L.lit.plan,deep:this.L.lit.deep,size:this.L.lit.size,opacity:this.L.lit.opacity,core:this.L.lit.core,ring:this.L.lit.ring,color:this.L.lit.color});const l=[.949,.929,.878];this.goalPts=this.makePoints({plan:this.L.goals.flatMap(x=>x.plan),deep:this.L.goals.flatMap(x=>x.deep),size:this.L.goals.map(x=>x.status==="completed"?2.2:2.6),opacity:this.L.goals.map(x=>x.status==="completed"?.3:x.status==="paused"?.55:1),core:this.L.goals.map(x=>x.status==="completed"?0:1),ring:this.L.goals.map(()=>1),color:this.L.goals.flatMap(x=>x.status==="completed"?l:[.91,.72,.36]),deepColor:this.L.goals.flatMap(x=>x.status==="completed"?[...Mn.moonWhite]:[.95,.76,.34])}),this.addTier(this.goalPts,1.18,1);const c=this.makePoints({plan:this.L.court.plan,deep:this.L.court.plan.map((x,A)=>A%3===2?x||0:x*1.6),size:this.L.court.size,opacity:this.L.court.gold.map(x=>x?1:.85),core:this.L.court.gold.map(()=>1),ring:this.L.court.gold.map(()=>0),color:this.L.court.gold.flatMap(x=>x?[.91,.72,.36]:[.961,.918,.824])});this.northPts=this.makePoints(this.northVacant?{plan:[0,0,0],deep:[0,0,0],size:[4.4],opacity:[.3],core:[0],ring:[1],color:l}:{plan:[0,0,0],deep:[0,0,0],size:[4.4],opacity:[1],core:[1],ring:[0],color:[.98,.85,.55],deepColor:[...Mn.warmGold]}),this.northVacant||this.addTier(this.northPts,1.35,1),this.planetPts=this.makePoints({plan:this.L.planets.flatMap(x=>x.plan),deep:this.L.planets.flatMap(x=>x.deep),size:this.L.planets.map(()=>3),opacity:this.L.planets.map(x=>x.status==="active"?.9:.35),core:this.L.planets.map(()=>.4),ring:this.L.planets.map(()=>1),color:this.L.planets.flatMap(()=>[.961,.918,.824]),deepColor:this.L.planets.flatMap(()=>[...Mn.softOrange])}),this.addTier(this.planetPts,.95,1),this.moonPts=this.makePoints({plan:this.L.moons.plan,deep:this.L.moons.deep,size:this.L.moons.size,opacity:this.L.moons.opacity,core:this.L.moons.size.map(()=>1),ring:this.L.moons.size.map(()=>0),color:this.L.moons.size.flatMap(()=>[.961,.918,.824]),deepColor:this.L.moons.size.flatMap(()=>[...Mn.moonWhite])}),this.addTier(this.moonPts,.9,1);const u=this.makePoints({plan:this.L.seated.plan,deep:this.L.seated.deep,size:this.L.seated.size,opacity:this.L.seated.opacity,core:this.L.seated.size.map(()=>1),ring:this.L.seated.size.map(()=>0),color:this.L.seated.size.flatMap(()=>[.961,.918,.824]),deepColor:this.L.seated.size.flatMap(()=>[...Mn.moonWhite])});this.addTier(u,.9,1),this.guestPts=this.makePoints({plan:this.L.guests.flatMap(x=>x.plan),deep:this.L.guests.flatMap(x=>x.deep),size:this.L.guests.map(()=>1.15),opacity:this.L.guests.map(()=>.95),core:this.L.guests.map(()=>1),ring:this.L.guests.map(()=>0),color:this.L.guests.flatMap(()=>[1,.95,.85]),deepColor:this.L.guests.flatMap(()=>[...Mn.blueWhite])}),this.addTier(this.guestPts,.95,null);const f=this.makePoints({plan:this.L.dust.plan,deep:this.L.dust.deep,size:this.L.dust.size,opacity:this.L.dust.opacity,core:this.L.dust.size.map(()=>1),ring:this.L.dust.size.map(()=>0),color:this.L.dust.size.flatMap(()=>[.961,.918,.824]),deepColor:this.L.dust.size.flatMap(()=>[.88,.9,.94])});this.addTier(f,.8,1);const h=this.makePoints({plan:this.L.etched.plan,deep:this.L.etched.deep,size:this.L.etched.size,opacity:this.L.etched.opacity,core:this.L.etched.size.map(()=>0),ring:this.L.etched.size.map(()=>1),color:this.L.etched.color,deepColor:this.L.etched.color.slice()});this.addTier(h,.9,.22);const d=(()=>{const x=new Dt;x.setAttribute("position",new Nt(new Float32Array(this.L.dust.trailPlan),3));const A=new or(x,this.lineMat(mn,.26,.22,3));this.chart.add(A);const P=A;return P.userData.plan=new Float32Array(this.L.dust.trailPlan),P.userData.deep=new Float32Array(this.L.dust.trailDeep),P})();if(this.planetInnerPts=this.makePoints({plan:this.L.planets.flatMap(x=>x.plan),deep:this.L.planets.flatMap(x=>x.deep),size:this.L.planets.map(()=>2),opacity:this.L.planets.map(x=>x.status==="active"?.9:.35),core:this.L.planets.map(()=>0),ring:this.L.planets.map(()=>1),color:this.L.planets.flatMap(()=>[.961,.918,.824]),deepColor:this.L.planets.flatMap(()=>[...Mn.softOrange])}),this.addTier(this.planetInnerPts,.95,1),this.L.shapeLinesPlan.length){const x=new Dt;x.setAttribute("position",new Nt(new Float32Array(this.L.shapeLinesPlan),3)),this.chart.add(new or(x,this.lineMat(mn,.14,.05,2)))}{const x=[];for(const A of this.L.planets){if(A.goalIndex<0)continue;const P=this.L.goals[A.goalIndex];x.push(new $(A.plan[0],A.plan[1],0)),x.push(new $(P.plan[0],P.plan[1],0))}this.chart.add(new or(new Dt().setFromPoints(x),this.lineMat(mn,.22,0,1)))}{const x=[];for(const A of this.L.planets){if(A.progress===null||A.progress===void 0||A.progress<=0)continue;const P=32,R=4.6;for(let L=0;L<P;L++){const I=Math.PI/2-L/P*A.progress*Math.PI*2,N=Math.PI/2-(L+1)/P*A.progress*Math.PI*2;x.push(new $(A.plan[0]+R*Math.cos(I),A.plan[1]+R*Math.sin(I),0)),x.push(new $(A.plan[0]+R*Math.cos(N),A.plan[1]+R*Math.sin(N),0))}}x.length&&this.chart.add(new or(new Dt().setFromPoints(x),this.lineMat(gm,.55,0,2)))}this.guestTails=(()=>{const x=[],A=[];for(const L of this.L.guests){const I=L.tailDir*Math.PI/180,N=Math.cos(I),O=Math.sin(I),B=-O,q=N,F=5;for(let k=0;k<F;k++)for(const U of[k/F,(k+1)/F]){const z=Math.sin(U*2.5)*1.1;x.push(L.plan[0]-N*L.tailLen*U+B*z,L.plan[1]-O*L.tailLen*U+q*z,0),A.push(L.deep[0]-N*L.tailLen*1.3*U+B*z,L.deep[1]-O*L.tailLen*1.3*U+q*z,L.deep[2])}}const P=new Dt;P.setAttribute("position",new Nt(new Float32Array(x),3));const R=new or(P,this.lineMat(mn,.55,.4,3));return this.chart.add(R),R})();{const x=this.guestTails;x.userData.plan=new Float32Array(x.geometry.attributes.position.array),x.userData.deep=new Float32Array(this.L.guests.flatMap(A=>{const P=A.tailDir*Math.PI/180,R=Math.cos(P),L=Math.sin(P),I=-L,N=R,O=[],B=5;for(let q=0;q<B;q++)for(const F of[q/B,(q+1)/B]){const k=Math.sin(F*2.5)*1.1;O.push(A.deep[0]-R*A.tailLen*1.3*F+I*k,A.deep[1]-L*A.tailLen*1.3*F+N*k,A.deep[2])}return O}))}const m=this.makeGlowTexture(),g=(x,A,P,R)=>{const L=new Aa({map:m,color:P,transparent:!0,opacity:0,blending:ol,depthWrite:!1}),I=new vo(L);return I.scale.set(A,A,1),this.chart.add(I),this.glows.push({spr:I,mat:L,getPos:x,maxOpacity:R}),I};g(()=>[0,0,0],20,16767370,this.northVacant?0:.8),g(()=>[0,0,0],40,9873628,this.northVacant?0:.1),this.L.goals.forEach((x,A)=>g(()=>{const P=this.goalPts.geometry.attributes.position.array;return[P[A*3],P[A*3+1],P[A*3+2]]},9,16764280,x.status==="completed"?0:x.status==="paused"?.12:.35)),this.guestGlows=this.L.guests.map((x,A)=>{const P=new Aa({map:m,color:14543103,transparent:!0,opacity:0,blending:ol,depthWrite:!1}),R=new vo(P);return R.scale.set(5.5,5.5,1),this.chart.add(R),{spr:R,mat:P,idx:A,breathe:x.review==="needs_review"}});{const x=this.L.dust.deep.length/3;if(x>0){const A=ui(7700),P=Math.max(6,Math.min(26,Math.round(x*.6))),R=Math.min(1,x/24);for(let L=0;L<P;L++){const I=P<=1?0:L/(P-1),N=Math.min(x-1,Math.floor(I*x)),O=new Aa({map:m,color:9410989,transparent:!0,opacity:0,depthWrite:!1}),B=new vo(O),q=30+A()*26;B.scale.set(q,q,1),B.position.set(this.L.dust.deep[N*3],this.L.dust.deep[N*3+1],this.L.dust.deep[N*3+2]-4),B.visible=!1,B.renderOrder=-1,this.chart.add(B),this.dustRiver.push({spr:B,mat:O,base:.06*R*(.7+A()*.6)})}}}for(const[x,A,P,R,L,I]of[[150,70,-120,260,8017464,.13],[-170,-60,-100,300,6119536,.1],[0,120,-140,200,4608634,.085]]){const N=new Aa({map:m,color:L,transparent:!0,opacity:0,depthWrite:!1}),O=new vo(N);O.position.set(x,A,P),O.scale.set(R,R,1),O.visible=!1,this.scene.add(O),this.nebulae.push({mat:N,op:I,spr:O})}this.buildLabels();const p=this.renderer.getContext(),_=p.getExtension("WEBGL_debug_renderer_info"),v=_?String(p.getParameter(_.UNMASKED_RENDERER_WEBGL)):"";this.softGL=/swiftshader|llvmpipe|software/i.test(v),this.composer=new yT(this.renderer),this.composer.addPass(new yE(this.scene,this.camera)),this.bloom=new xE({luminanceThreshold:.65,intensity:0,mipmapBlur:!0}),this.fxPass=new EE(this.camera,this.bloom),this.composer.addPass(this.fxPass),this.composer.setSize(this.heart.clientWidth||1600,this.heart.clientHeight||900),this.morphables=[this.dimPts,this.dimBgPts,this.litPts,this.goalPts,c,this.northPts,this.planetPts,this.planetInnerPts,this.moonPts,u,this.guestPts,f,h,this.guestTails,d];for(const x of[this.goalPts,this.planetPts,this.planetInnerPts,this.moonPts,this.guestPts,this.guestTails])x.userData.orbitManaged=!0;const S=this.L.seats.filter(x=>x.goalIndex===null);if(S.length){const x=S.flatMap(P=>{const R=P.angle*Math.PI/180;return[hr*Math.cos(R),hr*Math.sin(R),0]}),A=this.makePoints({plan:x,deep:x.slice(),size:S.map(()=>2),opacity:S.map(()=>.16),core:S.map(()=>0),ring:S.map(()=>1),color:S.flatMap(()=>[.961,.918,.824])});this.morphables.push(A)}this.goalPeriods=this.L.goals.map((x,A)=>150+A*36),this.planetPeriods=this.L.planets.map((x,A)=>100+A*14),this.guestPeriods=this.L.guests.map((x,A)=>26+A*6.5),this.goalPhase=this.L.goals.map(()=>0),this.planetPhase=this.L.planets.map(()=>0),this.guestPhase=this.L.guests.map(()=>0),this.guestDeepBase=this.L.guests.map(x=>x.deep.slice()),this.planetDeepBase=this.L.planets.map(x=>x.deep.slice()),this.goalDeepBase=this.L.goals.map(x=>x.deep.slice()),this.L.planets.forEach((x,A)=>{for(let P=0;P<Math.min(x.taskCount,5);P++)this.moonPlanet.push(A)}),this.moonDeepBase=[];for(let x=0;x<this.L.moons.deep.length;x+=3)this.moonDeepBase.push(this.L.moons.deep.slice(x,x+3));const y=this.guestTails;this.L.guests.forEach((x,A)=>{const P=[];for(let R=0;R<10;R++){const L=(A*10+R)*3;P.push([y.userData.deep[L]-x.deep[0],y.userData.deep[L+1]-x.deep[1],y.userData.deep[L+2]-x.deep[2]])}this.tailOffsets.push(P)});const M=(x,A)=>{const P=x.geometry.attributes.position.array;return[P[A*3],P[A*3+1],P[A*3+2]]};this.hoverables=[{title:"北极星",info:this.northVacant?"虚位 · 点击立星":i.north_star.split(/[，。]/)[0],pos:()=>[0,0,0]},...this.L.goals.map((x,A)=>({title:x.title,info:x.status==="completed"?"刻痕星 · 已镌刻":x.status==="paused"?"目标恒星 · 暂停":"目标恒星",pos:()=>M(this.goalPts,A)})),...this.L.planets.map((x,A)=>({title:x.title,info:`${x.status==="active"?"行星 · 在轨":"行星 · 归档"} · 任务 ${x.taskCount}`+(x.progress!==null&&x.progress!==void 0?` · 进度 ${Math.round(x.progress*100)}%`:""),pos:()=>M(this.planetPts,A)})),...this.L.guests.map((x,A)=>({title:x.title,info:`客星 · ${x.date} · ${x.strength}${x.review==="needs_review"?" · 待评审":""}`,pos:()=>M(this.guestPts,A)}))],this.clickables=[{kind:"north",id:"north",idx:-1,title:"北极星",pos:()=>[0,0,0]},...this.L.goals.map((x,A)=>({kind:"goal",id:x.id,idx:A,title:x.title,pos:()=>M(this.goalPts,A)})),...this.L.planets.map((x,A)=>({kind:"planet",id:x.id,idx:A,title:x.title,pos:()=>M(this.planetPts,A)})),...this.L.guests.map((x,A)=>({kind:"guest",id:x.id,idx:A,title:x.title,pos:()=>M(this.guestPts,A)})),...this.L.lit.skills.map((x,A)=>({kind:"skill",id:x.id,idx:A,title:x.label,pos:()=>M(this.litPts,A)}))],this.selRing=new Pd(new Dt().setFromPoints(this.circlePoints(3.2,48)),new mh({color:_w,transparent:!0,opacity:.8,depthWrite:!1})),this.selRing.visible=!1,this.chart.add(this.selRing);const T=new ResizeObserver(()=>this.onResize());T.observe(this.heart),this.resizeObserver=T,window.addEventListener("pointermove",this.onPointerMoveWindow,{passive:!0}),window.addEventListener("pointermove",this.onPointerActive,{passive:!0}),window.addEventListener("click",this.onClickWindow),window.addEventListener("keydown",this.onKeydown),window.addEventListener("wheel",this.onWheel,{passive:!0}),this.canvas.addEventListener("pointerdown",x=>{var A;this.focusToken+=1,(A=this.focusTween)==null||A.kill(),this.focusTween=null,!(this.coarsePointer||this.state.t>=.5)&&(this.dragging=!0,this.dragLastX=x.clientX,this.dragLastT=performance.now(),this.dragDist=0,this.spinVel=0,this.canvas.setPointerCapture(x.pointerId))}),this.canvas.addEventListener("pointermove",x=>{if(!this.dragging)return;const A=performance.now(),P=x.clientX-this.dragLastX,R=Math.max((A-this.dragLastT)/1e3,.008);this.dragLastX=x.clientX,this.dragLastT=A,this.dragDist+=Math.abs(P);const L=P*.004;this.chart.rotation.z+=L,this.spinVel=this.spinVel*.75+L/R*.25});const w=()=>{this.dragging=!1};this.canvas.addEventListener("pointerup",w),this.canvas.addEventListener("pointercancel",w),this.coarsePointer&&(this.controls=new IM(this.camera,this.canvas),this.controls.enableRotate=!1,this.controls.enableDamping=!0,this.controls.dampingFactor=.08,this.controls.enableZoom=!0,this.controls.zoomSpeed=.9,this.controls.enablePan=!0,this.controls.panSpeed=.8),this.guestBaseOpacity=new Float32Array(this.guestPts.geometry.attributes.aOpacity.array),this.onResize(),this.applyMorph(),r.initialState==="deepspace"&&this.goTo(1,!0),this.loop()}goTo(e,t=!1){var i;if(this.tween&&this.tween.kill(),this.focusToken+=1,(i=this.focusTween)==null||i.kill(),this.focusTween=null,this.closeDetail(),t||this.reducedMotion){this.state.t=e,this.applyMorph();return}this.tween=sl.to(this.state,{t:e,duration:2.4,ease:"power2.inOut",onUpdate:()=>this.applyMorph()})}focusStar(e){var s;const t=this.clickables.findIndex(a=>a.id===e);if(t<0||this.disposed)return!1;this.lastPointerActive=performance.now();const i=++this.focusToken;(s=this.focusTween)==null||s.kill(),this.focusTween=null;const r=()=>{i!==this.focusToken||this.disposed||this.runFocus(t,i)};return this.state.t>.5?(this.tween&&this.tween.kill(),this.closeDetail(),this.reducedMotion?(this.state.t=0,this.applyMorph(),r(),!0):(this.tween=sl.to(this.state,{t:0,duration:2.4,ease:"power2.inOut",onUpdate:()=>this.applyMorph(),onComplete:r}),!0)):(r(),!0)}runFocus(e,t){const i=this.clickables[e],r=()=>{t===this.focusToken&&!this.disposed&&this.openDetail(e)},s=i.pos();if(Math.hypot(s[0],s[1])<1){r();return}let l=90-(Math.atan2(s[1],s[0])*180/Math.PI+this.chart.rotation.z*180/Math.PI);l=(l+540)%360-180;const c=this.chart.rotation.z+l*Math.PI/180;if(this.reducedMotion){this.chart.rotation.z=c,r();return}this.focusTween=sl.to(this.chart.rotation,{z:c,duration:1.1,ease:"power2.inOut",onComplete:r})}toggle(){this.goTo(this.state.t>.5?0:1)}setReveal(e){if(!(e===this.reveal||this.disposed)){this.reveal=e;for(const{t}of this.labelObjs)this.chart.remove(t),t.dispose();this.labelObjs=[],this.goalLabelGroups=[],this.buildLabels(),this.applyMorph()}}deselect(){this.closeDetail()}dispose(){var e,t,i;this.disposed=!0,(e=this.resizeObserver)==null||e.disconnect(),cancelAnimationFrame(this.rafId),this.tween&&this.tween.kill(),(t=this.focusTween)==null||t.kill(),window.removeEventListener("pointermove",this.onPointerMoveWindow),window.removeEventListener("pointermove",this.onPointerActive),window.removeEventListener("click",this.onClickWindow),window.removeEventListener("keydown",this.onKeydown),window.removeEventListener("wheel",this.onWheel),(i=this.controls)==null||i.dispose(),this.scene.traverse(r=>{const s=r;s.geometry&&s.geometry.dispose();const a=s.material;Array.isArray(a)?a.forEach(o=>o.dispose()):a==null||a.dispose()}),this.composer.dispose(),this.renderer.dispose();for(const r of[this.bgStone,this.bgDeep,this.bgDusk,this.vignette,this.tooltip])r.remove();this.canvas.remove()}fitPlanCamera(){const e=this.heart.clientWidth||1600,t=this.heart.clientHeight||900,i=Math.tan(this.camera.fov*Math.PI/360);this.camPlan.pos.z=(Xo+16)/(i*Math.min(1,e/t))}bakeBackgrounds(){const e=Af("rgb"),t=(a,o,l)=>{const c=e(fw([a,o],"oklch")(l));return[Math.round(c.r*255),Math.round(c.g*255),Math.round(c.b*255)]},i=t("#1c2c4e","#10172c",.4),r=t("#182642","#0d1322",.4),s=a=>{const c=document.createElement("canvas");c.width=1024,c.height=640;const u=c.getContext("2d"),f=a==="stone",h=a==="dusk",d=f?[37,64,94]:h?i:[36,44,62],m=f?[29,52,80]:h?r:[26,31,46],g=u.createLinearGradient(0,0,0,640);g.addColorStop(0,`rgb(${d.join(",")})`),g.addColorStop(1,`rgb(${m.join(",")})`),u.fillStyle=g,u.fillRect(0,0,1024,640);const p=ui(f?41:h?43:42);for(let y=0;y<9;y++){const M=p()*1024,T=p()*640,w=120+p()*260,b=p()>.5,x=(f?.05:h?.04:.035)*(.7+p()*.6),A=u.createRadialGradient(M,T,0,M,T,w);A.addColorStop(0,b?`rgba(70,98,132,${x})`:`rgba(10,20,36,${x})`),A.addColorStop(1,"rgba(0,0,0,0)"),u.fillStyle=A,u.fillRect(M-w,T-w,w*2,w*2)}if(h){const y=u.createRadialGradient(512,396.8,0,512,396.8,348.16);y.addColorStop(0,"rgba(196,138,64,0.13)"),y.addColorStop(.55,"rgba(150,100,52,0.05)"),y.addColorStop(1,"rgba(150,100,52,0)"),u.fillStyle=y,u.fillRect(0,0,1024,640)}const _=u.getImageData(0,0,1024,640),v=f?.028:h?.04:.05,S=f?.045:h?.032:.02;for(let y=0;y<640;y++){const M=y/640;for(let T=0;T<1024;T++){const w=T/1024,b=Math.exp(-Math.pow((w*.82+M*.57-.78)*5,2))*v,x=(p()-.5)*S,A=(y*1024+T)*4,P=(b+x)*255;_.data[A]=Math.max(0,Math.min(255,_.data[A]+P*.9)),_.data[A+1]=Math.max(0,Math.min(255,_.data[A+1]+P*.88)),_.data[A+2]=Math.max(0,Math.min(255,_.data[A+2]+P*.82))}}return u.putImageData(_,0,0),c};this.bgStone.style.backgroundImage=`url(${s("stone").toDataURL("image/png")})`,this.bgDusk.style.backgroundImage=`url(${s("dusk").toDataURL("image/png")})`,this.bgDusk.style.opacity="0",this.bgDeep.style.backgroundImage=`url(${s("deep").toDataURL("image/png")})`,this.bgDeep.style.opacity="0"}applyBackground(e,t){e<=t?(this.bgDusk.style.opacity=String(e/t),this.bgDeep.style.opacity="0"):(this.bgDusk.style.opacity="1",this.bgDeep.style.opacity=String((e-t)/(1-t)))}lineMat(e,t,i,r=1){const s=new mh({color:e,transparent:!0,opacity:t,depthWrite:!1});return this.fadeMats.push({mat:s,plan:t,deep:i,ch:r}),s}circlePoints(e,t=160){const i=[];for(let r=0;r<=t;r++){const s=r/t*Math.PI*2;i.push(new $(e*Math.cos(s),e*Math.sin(s),0))}return i}buildLinework(){const e=this.L,t=this.lineMat(mn,.42,.2,2),i=this.lineMat(mn,.55,0,1),r=this.lineMat(mn,.18,0,1),s=this.lineMat(mn,.08,0,1),a=this.lineMat(mn,.5,0,2),o=this.lineMat(mn,.52,.15,2),l=this.lineMat(mn,.35,0,2),c=(d,m,g=!1)=>{const p=new Dt().setFromPoints(d),_=g?new Pd(p,m):new nf(p,m);return this.chart.add(_),_},u=ui(53),f=(d,m,g,p)=>{const _=[];for(let v=0;v<=4;v++){const S=d+(m-d)*v/4,M=(g+(v>0&&v<4?(u()-.5)*1.4:0))*Math.PI/180;_.push(new $(S*Math.cos(M),S*Math.sin(M),0))}c(_,p)};for(const[d,m]of[[hr,t],[mw,t],[Mt,i],[Su,a],[Xo,a]])c(this.circlePoints(d),m,!0);{const d=[];for(let m=18;m<=342;m+=2){const g=m*Math.PI/180;d.push(new $(Ua*Math.cos(g),Ua*Math.sin(g),0))}c(d,t)}{const d=[];for(let g=0;g<360;g+=6){const p=g*Math.PI/180,_=Mt+(g%30===0?3.25:1.5);d.push(new $(Mt*Math.cos(p),Mt*Math.sin(p),0)),d.push(new $(_*Math.cos(p),_*Math.sin(p),0))}const m=new Dt().setFromPoints(d);this.chart.add(new or(m,i))}const h=d=>(d=d%360,d>180&&(d-=360),d<-180&&(d+=360),d);for(const d of e.sectors){Math.abs(h(d.start))>=12&&f(Ua,Mt,d.start,r);const m=Math.max(1,Math.round(d.count/6)),g=[];for(let _=1;_<m;_++)g.push(_/m+(u()-.5)*.5/m);g.sort();for(const _ of g){const v=d.start+d.width*_;Math.abs(h(v))>=12&&f(Ua,Mt,v,s)}const p=d.start*Math.PI/180;c([new $(Su*Math.cos(p),Su*Math.sin(p),0),new $(Xo*Math.cos(p),Xo*Math.sin(p),0)],a)}{const d=[],m=e.lit.plan;for(let p=0;p<e.lit.links.length;p+=2){const _=e.lit.links[p]*3,v=e.lit.links[p+1]*3;d.push(new $(m[_],m[_+1],0)),d.push(new $(m[v],m[v+1],0))}const g=new Dt().setFromPoints(d);this.chart.add(new or(g,o))}{const d=[],m=e.court.plan;for(const[p,_]of e.court.links)d.push(new $(m[p*3],m[p*3+1],0)),d.push(new $(m[_*3],m[_*3+1],0));const g=new Dt().setFromPoints(d);this.chart.add(new or(g,l))}c(this.circlePoints(4.2,64),this.lineMat(mn,.55,0,2),!0)}makePoints(e,t){const{plan:i,deep:r,size:s,opacity:a,core:o,ring:l,color:c}=e,u=new Dt;u.setAttribute("position",new Nt(new Float32Array(i),3)),u.setAttribute("aSize",new Nt(new Float32Array(s),1)),u.setAttribute("aOpacity",new Nt(new Float32Array(a),1)),u.setAttribute("aCore",new Nt(new Float32Array(o),1)),u.setAttribute("aRing",new Nt(new Float32Array(l),1)),u.setAttribute("aColor",new Nt(new Float32Array(c),3));const f=new on({transparent:!0,depthWrite:!1,blending:Hr,uniforms:{uScale:{value:1},uGlobal:{value:1}},vertexShader:`
        attribute float aSize;
        attribute float aOpacity;
        attribute float aCore;
        attribute float aRing;
        attribute vec3 aColor;
        varying float vOpacity;
        varying float vCore;
        varying float vRing;
        varying vec3 vColor;
        uniform float uScale;
        uniform float uGlobal;
        void main() {
          vOpacity = aOpacity;
          vCore = aCore;
          vRing = aRing;
          vColor = aColor;
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = aSize * uGlobal * uScale / -mv.z;
          gl_Position = projectionMatrix * mv;
        }
      `,fragmentShader:`
        varying float vOpacity;
        varying float vCore;
        varying float vRing;
        varying vec3 vColor;
        void main() {
          vec2 uv = gl_PointCoord - 0.5;
          float d = length(uv) * 2.0;
          float core = (1.0 - smoothstep(0.40, 0.62, d)) * vCore;
          float ring = smoothstep(0.58, 0.70, d) * (1.0 - smoothstep(0.80, 0.92, d)) * vRing;
          float a = max(core, ring) * vOpacity;
          if (a < 0.004) discard;
          gl_FragColor = vec4(pow(vColor, vec3(2.2)), a); // linear pipeline
        }
      `}),h=new Pv(u,f);return h.userData.plan=new Float32Array(i),h.userData.deep=new Float32Array(r),e.deepColor&&this.colored.push({pts:h,plan:new Float32Array(c),deep:new Float32Array(e.deepColor)}),(t??this.chart).add(h),h}addTier(e,t,i){this.tiered.push({pts:e,baseSize:new Float32Array(e.geometry.attributes.aSize.array),baseOp:i===null?null:new Float32Array(e.geometry.attributes.aOpacity.array),ds:t,dop:i??1})}makeGlowTexture(){const e=document.createElement("canvas");e.width=e.height=128;const t=e.getContext("2d"),i=t.createRadialGradient(64,64,0,64,64,64);return i.addColorStop(0,"rgba(255,255,255,1)"),i.addColorStop(.25,"rgba(255,255,255,0.35)"),i.addColorStop(1,"rgba(255,255,255,0)"),t.fillStyle=i,t.fillRect(0,0,128,128),new Dv(e)}addLabel(e,t={}){const{size:i=3.4,color:r=mn,font:s=Ew,pos:a=[0,0,0],deepPos:o=null,rotZ:l=0,anchorX:c="center",fade:u="band"}=t,f=new Mh;return f.text=e,f.font=s,f.fontSize=i,f.color=r,f.anchorX=c,f.anchorY="middle",f.position.set(a[0],a[1],a[2]??0),f.rotation.z=l,f.material.transparent=!0,f.outlineWidth="5%",f.outlineColor=726566,f.outlineOpacity=.85,this.chart.add(f),this.labelObjs.push({t:f,fade:u,planPos:a.slice(),deepPos:o?o.slice():null}),f}addSegmentedLabel(e,t){const{size:i=3.6,color:r=15652502,pos:s,align:a="left",fade:o="goal",goalIdx:l=-1}=t,c=e.split(/([A-Za-z0-9.]+)/).filter(Boolean),u={goalIdx:l,segs:[],base:[],anchor:s.slice()},f=c.map(d=>{const m=/^[A-Za-z0-9.]+$/.test(d),g=new Mh;return g.text=d,g.font=m?ww:Ea,g.fontSize=i,g.color=r,g.anchorX="left",g.anchorY="middle",g.material.transparent=!0,g.outlineWidth="5%",g.outlineColor=726566,g.outlineOpacity=.85,this.chart.add(g),this.labelObjs.push({t:g,fade:o,planPos:s.slice(),deepPos:null}),u.segs.push(g),g});l>=0&&this.goalLabelGroups.push(u),this.segPending+=f.length;let h=f.length;f.forEach(d=>d.sync(()=>{if(this.segPending-=1,h-=1,h===0){const m=f.map(_=>{const v=_.textRenderInfo&&_.textRenderInfo.blockBounds;return v?Math.max(.1,v[2]-v[0]):_.text.length*i*.6}),g=m.reduce((_,v)=>_+v,0)+.4*(f.length-1);let p=s[0]-(a==="right"?g:a==="center"?g/2:0);f.forEach((_,v)=>{_.position.set(p,s[1],0),p+=m[v]+.4}),u.base=f.map(_=>[_.position.x,_.position.y])}}))}followGoal(e,t){this.goalLabelGroups.push({goalIdx:e,segs:t,base:t.map(i=>[i.position.x,i.position.y]),anchor:[]})}buildLabels(){const e=this.L;for(const t of e.sectors){const i=t.start+t.width/2,r=Array.from(this.reveal?t.name:t.asterism),s=this.reveal?gm:mn,a=3.2*1.25/Mu*(180/Math.PI),o=i-a*(r.length-1)/2;if(r.forEach((l,c)=>{const u=(o+c*a)*Math.PI/180;this.addLabel(l,{size:3.2,color:s,font:Ea,fade:"band",pos:[Mu*Math.cos(u),Mu*Math.sin(u),0],rotZ:u+Math.PI/2})}),!this.reveal&&t.asterism!==t.name&&t.figRadius>0){const l=i*Math.PI/180,c=Mt*.72+t.figRadius+3.5;this.addLabel(t.asterism,{size:2.2,color:11907232,font:Ea,fade:"band",pos:[c*Math.cos(l),c*Math.sin(l),0],rotZ:l+Math.PI/2})}}e.goals.forEach((t,i)=>{const r=Math.cos(t.angle*Math.PI/180),s=r>.35?"left":r<-.35?"right":"center",a=hr+8,o=t.angle*Math.PI/180,l=a*Math.cos(o)+(s==="left"?1:s==="right"?-1:0),c=a*Math.sin(o);if(t.status==="completed"){this.addSegmentedLabel(t.title,{size:3.6,color:10130038,align:s,goalIdx:i,pos:[l,c,0]});return}if(!this.reveal){const u=this.addLabel(t.seatName??t.title,{size:3.8,color:15652502,font:Ea,fade:"goal",pos:[l,c,0]});this.followGoal(i,[u]);return}this.addSegmentedLabel(t.title,{size:3.6,color:15652502,align:s,goalIdx:i,pos:[l,c,0]})});for(const t of e.seats){if(t.goalIndex!==null)continue;const i=t.angle*Math.PI/180,r=hr+8;this.addLabel(`${t.name}·虚位`,{size:2.8,color:9274994,font:Ea,fade:"goal",pos:[r*Math.cos(i),r*Math.sin(i),0]})}if(this.northVacant)this.addLabel("虚位",{size:3.8,color:mn,font:jo,anchorX:"left",pos:[6.5,.4,0],deepPos:[10.5,-10.6,0],fade:"north"});else if(!this.reveal)this.addLabel("北极星",{size:3.8,color:mn,font:jo,anchorX:"left",pos:[6.5,.4,0],deepPos:[10.5,-10.6,0],fade:"north"});else{const t=this.snapshot.north_star.split(/[，。]/)[0],i=t.indexOf("成为"),r=i>0?[t.slice(0,i+2),t.slice(i+2)]:[t,""];this.addLabel(r[0],{size:3.8,color:15652502,font:jo,anchorX:"left",pos:[6.5,3.4,0],deepPos:[10.5,-8.5,0],fade:"north"}),r[1]&&this.addLabel(r[1],{size:3.8,color:15652502,font:jo,anchorX:"left",pos:[6.5,-2.6,0],deepPos:[10.5,-13.6,0],fade:"north"})}this.labelsPending=this.labelObjs.length;for(const{t}of this.labelObjs)t.sync(()=>{this.labelsPending-=1})}applyMorph(){var c,u;const e=this.state.t,t=Tu(e,this.state.w1),i=Tu(e,this.state.w2),r=Tu(e,this.state.w3);this.state.ch1=t,this.state.ch2=i,this.state.ch3=r;for(const f of this.morphables){if(f.userData.orbitManaged)continue;const h=f.geometry.attributes.position,d=f.userData.plan,m=f.userData.deep,g=h.array;for(let p=0;p<g.length;p++)g[p]=d[p]+(m[p]-d[p])*i;h.needsUpdate=!0}this.chart.rotation.x=-1.05*i,this.camera.position.lerpVectors(this.camPlan.pos,this.camDeep.pos,i),this.camera.lookAt(new $().lerpVectors(this.camPlan.look,this.camDeep.look,i));for(const{mat:f,plan:h,deep:d,ch:m}of this.fadeMats){const g=m===1?t:m===3?r:i;f.opacity=h+(d-h)*g}for(const{t:f,fade:h,planPos:d,deepPos:m}of this.labelObjs)h==="band"?(f.material.opacity=1-i,f.visible=i<.98):h==="north"&&m&&(f.material.opacity=1-.25*i,f.position.set(d[0]+(m[0]-d[0])*i,d[1]+(m[1]-d[1])*i,0));for(const f of this.glows){f.mat.opacity=f.maxOpacity*r,f.spr.visible=f.mat.opacity>.004;const h=f.getPos();f.spr.position.set(h[0],h[1],h[2])}for(const f of this.nebulae)f.mat.opacity=f.op*r,f.spr.visible=f.mat.opacity>.004;const s=Math.exp(-Math.pow((i-this.state.duskPos)/.13,2))*this.state.duskAmt,a=this.glows[0];if(s>.01){a.mat.opacity=Math.min(1,Math.max(a.mat.opacity,a.maxOpacity*s*.6)),a.spr.visible=!0;const f=20*(1+.55*s);a.spr.scale.set(f,f,1)}else a.spr.scale.set(20,20,1);for(const f of[this.dimPts,this.dimBgPts]){const h=f.geometry.attributes.aOpacity,d=f.geometry.attributes.aSize,m=f.geometry.attributes.aRing,g=f.userData.baseOpacity,p=f.userData.baseSize,_=f.userData.baseRing,v=f.userData.deepOpScale,S=f.userData.deepSizeScale,y=f.userData.filler;for(let M=0;M<h.array.length;M++){const T=y[M]?this.state.density:1;h.array[M]=g[M]*T*(1+(v[M]-1)*r),d.array[M]=p[M]*(1+(S[M]-1)*r),m.array[M]=_[M]*(1-.55*r)}h.needsUpdate=!0,d.needsUpdate=!0,m.needsUpdate=!0}for(const f of this.tiered){const h=f.pts.geometry.attributes.aSize,d=h.array,m=1+(f.ds-1)*r;for(let g=0;g<d.length;g++)d[g]=f.baseSize[g]*m;if(h.needsUpdate=!0,f.baseOp){const g=f.pts.geometry.attributes.aOpacity,p=g.array,_=1+(f.dop-1)*r;for(let v=0;v<p.length;v++)p[v]=f.baseOp[v]*_;g.needsUpdate=!0}}for(const f of this.colored){const h=f.pts.geometry.attributes.aColor,d=h.array;for(let m=0;m<d.length;m++)d[m]=f.plan[m]+(f.deep[m]-f.plan[m])*i;h.needsUpdate=!0}for(const f of this.dustRiver)f.mat.opacity=f.base*r,f.spr.visible=f.mat.opacity>.004;this.applyBackground(i,this.state.duskPos),this.fxPass.enabled=!this.softGL&&r>.02,this.bloom.intensity=.7*r*this.state.bloom,this.vignette.style.opacity=String(.55+.45*i);const o=String(1-i),l=this.opts.domRefs;l!=null&&l.cartouche&&(l.cartouche.style.opacity=o),l!=null&&l.briefing&&(l.briefing.style.opacity=o),l!=null&&l.toggle&&(l.toggle.textContent=e>.5?"图":"境"),(u=(c=this.opts).onMorph)==null||u.call(c,e)}screenOf(e){const t=new $(e[0],e[1],e[2]??0);this.chart.localToWorld(t),t.project(this.camera);const i=this.heart.getBoundingClientRect();return[i.left+(t.x*.5+.5)*i.width,i.top+(-t.y*.5+.5)*i.height]}onPointerMove(e){this.hoverIdx=-1;let t=26;this.hoverables.forEach((i,r)=>{const[s,a]=this.screenOf(i.pos()),o=Math.hypot(s-e.clientX,a-e.clientY);o<t&&(t=o,this.hoverIdx=r)})}updateTooltip(){const e=this.tooltip;if(this.hoverIdx<0||!this.hoverables[this.hoverIdx]){e.style.display="none";return}const t=this.hoverables[this.hoverIdx],[i,r]=this.screenOf(t.pos());e.innerHTML='<div class="tt-title"></div><div class="tt-info"></div>',e.querySelector(".tt-title").textContent=t.title,e.querySelector(".tt-info").textContent=t.info,e.style.display="block";const s=e.offsetWidth;e.style.left=Math.min(window.innerWidth-s-12,i+16)+"px",e.style.top=Math.max(10,r-44)+"px"}detailRows(e){var a,o;const t=this.snapshot;if(e.kind==="north"){const l=t.north;return this.northVacant?[["类型","北极星 · 虚位"],["铭文","（尚未立星 — 点「重刻」写下北极星）"]]:[["类型","北极星"],["铭文",l.full||t.north_star],["简称",l.brief||"—"],["可见性",l.visibility==="public"?"可公开":"仅本地"]]}if(e.kind==="goal"){const l=t.goals.find(f=>f.id===e.id)??{status:((a=this.L.goals[e.idx])==null?void 0:a.status)??"active",start:"",target:"",summary:""},c=l.status==="completed"?"已镌刻":l.status==="paused"?"已暂停":"进行中",u=(o=this.L.goals[e.idx])==null?void 0:o.seatName;return[["状态",c],...u?[["星位",u]]:[],["起始",l.start||"—"],["目标",l.target||"—"],["铭文",l.summary||"—"]]}if(e.kind==="planet"){const l=t.projects[e.idx],c=this.L.planets[e.idx].goalIndex;return[["状态",l.status==="active"?"在轨":"归档"],["所属目标",c>=0?this.L.goals[c].title:"（自由轨道）"],["任务",`${l.task_count} 项`],["进度",l.progress===null||l.progress===void 0?"—":`${Math.round(l.progress*100)}%`],["时间范围",l.time_range||"—"]]}if(e.kind==="guest"){const l=t.evidence.find(c=>c.id===this.L.guests[e.idx].id)??this.L.guests[e.idx];return[["类型","type"in l?l.type:"—"],["强度",l.strength||"—"],["日期",l.date||"—"],["评审","review_status"in l&&l.review_status==="needs_review"?"待评审":"已入座"],["摘要","summary"in l&&l.summary?l.summary:"—"]]}const i=this.L.lit.skills[e.idx],r=t.evidence.filter(l=>l.skill_ids.includes(i.id)).slice(0,3).map(l=>l.title),s=[["类别",i.category],["状态",i.status],["关联证据",`${i.evidenceCount} 条`]];return r.forEach((l,c)=>s.push([c===0?"入座证据":"",`· ${l}`])),s}openDetail(e){var i,r;this.selectedIdx=e;const t=this.clickables[e];(r=(i=this.opts).onSelect)==null||r.call(i,{kind:t.kind,id:t.id,title:t.title,rows:this.detailRows(t)})}closeDetail(){var e,t;this.selectedIdx<0||(this.selectedIdx=-1,this.selRing.visible=!1,(t=(e=this.opts).onSelect)==null||t.call(e,null))}onClick(e){if(this.dragDist>6){this.dragDist=0;return}const t=e.target;if(!t.isConnected||t.closest("[data-starmap-ui]"))return;let i=-1,r=26;this.clickables.forEach((s,a)=>{const[o,l]=this.screenOf(s.pos()),c=Math.hypot(o-e.clientX,l-e.clientY);c<r&&(r=c,i=a)}),i>=0?this.openDetail(i):this.closeDetail()}updatePointScale(){const t=this.renderer.domElement.height/(2*Math.tan(this.camera.fov*Math.PI/360));for(const i of this.morphables){const r=i;r.isPoints&&(r.material.uniforms.uScale.value=t)}}onResize(){const e=this.heart.clientWidth||1,t=this.heart.clientHeight||1;this.renderer.setSize(e,t),this.composer.setSize(e,t),this.camera.aspect=e/t,this.camera.updateProjectionMatrix(),this.fitPlanCamera(),this.controls&&(this.controls.minDistance=this.camPlan.pos.z*.65,this.controls.maxDistance=this.camPlan.pos.z*1.6),this.updatePointScale(),this.applyMorph()}loop(){if(this.disposed)return;this.rafId=requestAnimationFrame(()=>this.loop());const e=Math.min(this.clock.getDelta(),.1),t=this.clock.elapsedTime,{ch2:i,ch3:r}=this.state,s=this.L,a=performance.now(),l=this.dragging||this.hoverIdx>=0||this.selectedIdx>=0||a-this.lastPointerActive<3e3||this.reducedMotion?0:1;this.spinFactor+=(l-this.spinFactor)*Math.min(1,e/.8);const c=Math.PI*2/3600;this.chart.rotation.z+=e*c*this.spinFactor*(1+2.5*Math.sin(i*Math.PI)),!this.dragging&&Math.abs(this.spinVel)>1e-4&&(this.chart.rotation.z+=this.spinVel*e,this.spinVel*=Math.exp(-e/1.2)),this.bgLayer.rotation.z=-.7*i*this.chart.rotation.z;const u=(h,d,m)=>[h*Math.cos(m)-d*Math.sin(m),h*Math.sin(m)+d*Math.cos(m)];{const h=this.goalPts.geometry.attributes.position,d=s.goals.map((y,M)=>{const T=this.goalDeepBase[M];this.goalPhase[M]+=e*(2*Math.PI/this.goalPeriods[M])*r;const[w,b]=u(T[0],T[1],this.goalPhase[M]);return[y.plan[0]+(T[0]-y.plan[0])*i+(w-T[0]),y.plan[1]+(T[1]-y.plan[1])*i+(b-T[1]),y.plan[2]+(T[2]-y.plan[2])*i]});d.forEach((y,M)=>h.setXYZ(M,y[0],y[1],y[2])),h.needsUpdate=!0;for(const y of this.goalLabelGroups){if(!y.base.length)continue;const M=d[y.goalIdx],T=s.goals[y.goalIdx].plan,w=this.goalDeepBase[y.goalIdx],b=T[0]+(w[0]-T[0])*i,x=T[1]+(w[1]-T[1])*i,A=M[0]-b,P=M[1]-x;y.segs.forEach((R,L)=>R.position.set(y.base[L][0]+A,y.base[L][1]+P,0))}const m=this.planetPts.geometry.attributes.position,g=this.planetInnerPts.geometry.attributes.position,p=this.moonPts.geometry.attributes.position,_=s.planets.map((y,M)=>{const T=this.planetDeepBase[M];this.planetPhase[M]+=e*(2*Math.PI/this.planetPeriods[M])*r;const w=y.goalIndex,b=w>=0?this.goalDeepBase[w]:[0,0,0],x=w>=0?d[w]:[0,0,0],[A,P]=u(T[0]-b[0],T[1]-b[1],this.planetPhase[M]),R=y.plan[0]+(T[0]-y.plan[0])*i,L=y.plan[1]+(T[1]-y.plan[1])*i;return[R+(x[0]-b[0])+(A-(T[0]-b[0])),L+(x[1]-b[1])+(P-(T[1]-b[1])),y.plan[2]+(T[2]-y.plan[2])*i]});_.forEach((y,M)=>{m.setXYZ(M,y[0],y[1],y[2]),g.setXYZ(M,y[0],y[1],y[2])}),m.needsUpdate=!0,g.needsUpdate=!0,this.moonDeepBase.forEach((y,M)=>{const T=this.moonPlanet[M];T!==void 0&&p.setXYZ(M,y[0]+(_[T][0]-this.planetDeepBase[T][0]),y[1]+(_[T][1]-this.planetDeepBase[T][1]),y[2])}),p.needsUpdate=!0;const v=this.guestPts.geometry.attributes.position,S=this.guestTails.geometry.attributes.position;s.guests.forEach((y,M)=>{const T=this.guestDeepBase[M];this.guestPhase[M]+=e*(2*Math.PI/this.guestPeriods[M])*r;const w=4*r,b=y.plan[0]+(T[0]-y.plan[0])*i+w*Math.cos(this.guestPhase[M]+M*1.3),x=y.plan[1]+(T[1]-y.plan[1])*i+w*Math.sin(this.guestPhase[M]+M*1.3),A=y.plan[2]+(T[2]-y.plan[2])*i;v.setXYZ(M,b,x,A),this.guestGlows[M].spr.position.set(b,x,A),this.tailOffsets[M].forEach((R,L)=>S.setXYZ(M*10+L,b+R[0]*i,x+R[1]*i,A+R[2]*i))}),v.needsUpdate=!0,S.needsUpdate=!0}const f=h=>h<.25?.5-.5*Math.cos(h/.25*Math.PI):h<.45?1:.5+.5*Math.cos((h-.45)/.55*Math.PI);if(this.reducedMotion)for(const h of this.guestGlows)h.mat.opacity=(.34+.3*r)*.925,h.spr.visible=h.mat.opacity>.004;else for(const h of this.guestGlows){const d=.34+.3*r,m=h.breathe?f((t/11+h.idx*.31)%1):.4;h.mat.opacity=d*(.85+.15*m),h.spr.visible=h.mat.opacity>.004;const g=5.5*(1+.4*r);h.spr.scale.set(g,g,1)}{const h=this.guestPts.geometry.attributes.aOpacity;let d=!1;for(let m=0;m<h.array.length;m++)h.array[m]!==this.guestBaseOpacity[m]&&(h.array[m]=this.guestBaseOpacity[m],d=!0);d&&(h.needsUpdate=!0)}if(this.updateTooltip(),this.northVacant){const h=this.northPts.geometry.attributes.aOpacity;h.array[0]=this.reducedMotion?.3:.28+.14*Math.sin(t*.9),h.needsUpdate=!0}if(this.selectedIdx>=0){const h=this.clickables[this.selectedIdx].pos();this.selRing.visible=!0,this.selRing.position.set(h[0],h[1],h[2]??0);const d=this.reducedMotion?1:1+.04*Math.sin(t*3);this.selRing.scale.set(d,d,1)}if(this.controls){this.controls.enabled=this.state.t<.5,this.controls.update();const h=this.controls.target,d=Math.max(-70,Math.min(70,h.x)),m=Math.max(-70,Math.min(70,h.y));(d!==h.x||m!==h.y)&&(this.camera.position.x+=d-h.x,this.camera.position.y+=m-h.y,h.x=d,h.y=m,h.z=0)}this.fxPass.enabled?this.composer.render():this.renderer.render(this.scene,this.camera)}}const Rw="/assets/title-v2-b-ibfvihIe.svg";function Dw({snapshot:n}){const{name:e=""}=o_(),t=st.useRef(null),i=st.useRef(null),r=st.useRef(null),s=st.useRef(null),a=st.useRef(null),o=st.useRef(null),l=st.useRef(null),[c,u]=st.useState(null),[f,h]=st.useState(!1),[d,m]=st.useState(!1),[g,p]=st.useState(()=>localStorage.getItem("nblane.starmap.reveal")==="1"),_=st.useRef(g);_.current=g;const v=l_(e);st.useEffect(()=>{const y=t.current,M=i.current;if(!y||!M)return;let T=null;try{T=new Aw(y,M,n,{onSelect:b=>{l.current=null,u(b)},domRefs:{cartouche:r.current,briefing:s.current,toggle:a.current},reveal:_.current})}catch{m(!0);return}o.current=T;const w=l.current;if(w&&performance.now()-w.at<6e3){if(!T.focusStar(w.id)){l.current=null;const b=n.goals.find(x=>x.id===w.id);b&&u({kind:"goal",id:b.id,title:b.title,rows:Qf(b)})}}else l.current=null;return()=>{T==null||T.dispose(),o.current=null}},[n]);const S=st.useMemo(()=>{var M;const y=`「${n.counts.evidence_needs_review} 条客星待评审，${n.counts.projects_active} 颗行星在轨。」`;return h_(y,u_(((M=v.data)==null?void 0:M.entries)??[]))},[n,v.data]);return st.useEffect(()=>{const y=M=>{var T;M.key==="Escape"&&(h(!1),u(null),l.current=null,(T=o.current)==null||T.deselect())};return window.addEventListener("keydown",y),()=>window.removeEventListener("keydown",y)},[]),pe.jsxs("div",{className:"starmap-root",ref:t,"data-testid":"starmap-root",children:[pe.jsxs("div",{className:"starmap-layout",children:[pe.jsx("div",{className:"starmap-mount-top",children:pe.jsx("img",{className:"starmap-cartouche",ref:r,src:Rw,alt:"成长星图"})}),pe.jsx("div",{className:"starmap-heart",ref:i,"data-testid":"starmap-heart"}),pe.jsx("div",{className:"starmap-mount-bottom",children:pe.jsx("div",{className:"starmap-briefing",ref:s,"data-testid":"starmap-briefing",children:S})})]}),!d&&pe.jsxs(pe.Fragment,{children:[pe.jsx("button",{type:"button",className:"starmap-toggle",ref:a,"data-starmap-ui":!0,"data-testid":"starmap-toggle","aria-label":"切换 境态/图态",title:"境态 ⇄ 图态",onClick:()=>{var y;return(y=o.current)==null?void 0:y.toggle()},children:"境"}),pe.jsxs("button",{type:"button",className:"starmap-reveal-toggle","data-starmap-ui":!0,"data-testid":"starmap-reveal-toggle","aria-pressed":g,"aria-label":"显真",title:g?"显真·朱文 — 点击钤回古名":"显真·白文 — 点击显现真名（已记住此偏好）",onClick:()=>{var M;const y=!g;p(y),localStorage.setItem("nblane.starmap.reveal",y?"1":"0"),(M=o.current)==null||M.setReveal(y)},children:[pe.jsx("span",{"aria-hidden":"true",children:"显"}),pe.jsx("span",{"aria-hidden":"true",children:"真"})]}),pe.jsx("button",{type:"button",className:"starmap-catalog-btn","data-starmap-ui":!0,"data-testid":"starmap-catalog-btn","aria-label":"星表","aria-expanded":f,onClick:()=>h(y=>!y),children:"＋"})]}),pe.jsx(d_,{profile:e}),pe.jsx(x_,{open:f,snapshot:n,profile:e,selection:c,onFocus:y=>{var w;if(((w=o.current)==null?void 0:w.focusStar(y))??!1){l.current={id:y,at:performance.now()};return}l.current=null;const T=n.goals.find(b=>b.id===y);T&&u({kind:"goal",id:T.id,title:T.title,rows:Qf(T)})}}),pe.jsx("div",{className:`starmap-detail${c?" open":""}`,"data-starmap-ui":!0,"data-testid":"starmap-detail",children:c&&pe.jsx(m_,{selection:c,snapshot:n,profile:e,onSaved:u},`${c.kind}:${c.id}`)}),d&&pe.jsxs("div",{className:"starmap-fallback","data-testid":"starmap-fallback",children:[pe.jsx("div",{className:"fb-title",children:"成长星图"}),pe.jsx("div",{className:"fb-line",children:n.north.is_set?n.north_star:"尚未设置北极星 — 北极星虚位以待。"}),pe.jsx("div",{className:"fb-line",children:S}),pe.jsx("div",{className:"fb-line",children:"此浏览器不支持 WebGL，以上为静态简报。"})]})]})}export{Dw as StarmapView};
