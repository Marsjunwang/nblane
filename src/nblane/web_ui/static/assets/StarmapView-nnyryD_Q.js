var Xg=Object.defineProperty;var jg=(n,e,t)=>e in n?Xg(n,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):n[e]=t;var ye=(n,e,t)=>jg(n,typeof e!="symbol"?e+"":e,t);import{r as et,u as Yg,j as me,L as qg,a as $f,b as Kg,c as Zg,d as $g,T as Jg,n as ha,e as Qg,f as e_,g as Er,I as Fn,G as ac,h as Jf,R as fa,B as ao,i as t_,k as ss,l as oc,m as oo,o as lc,p as n_,q as i_,s as lo,t as r_,v as s_,w as Qf,x as a_}from"./index-COnM2rF0.js";function o_(n){return`${n.getFullYear()}-${String(n.getMonth()+1).padStart(2,"0")}`}function l_(n,e=new Date){const t=o_(e);let i=0,r=0,s=0;for(const o of n)!o.date||!String(o.date).startsWith(t)||(o.kind==="goal.added"?i+=1:o.kind==="goal.completed"?r+=1:o.kind==="north_star.rewritten"&&(s+=1));const a=[];return i>0&&a.push(`本月新立目标 ${i}`),r>0&&a.push(`新镌 ${r} 星`),s>0&&a.push("北极星已重刻"),a.join("，")}function c_(n,e){return e?n.endsWith("。」")?`${n.slice(0,-2)}，${e}。」`:n.endsWith("」")?`${n.slice(0,-1)}，${e}」`:`${n} ${e}`:n}function u_(n){var t;const e=(t=n==null?void 0:n.anchors)==null?void 0:t.gap;return((e==null?void 0:e.closure)??[]).filter(i=>i.is_gap)}function gm(n){return n.slice(0,6).reverse().map(e=>e===1)}function h_({lines:n,size:e=44,animated:t=!1}){const i=gm(n),r=e,s=e*.72,a=s/6;return me.jsx("div",{className:`hexagram-symbol${t?" casting":""}`,style:{width:r,height:s},"data-testid":"hexagram-symbol","aria-hidden":"true",children:i.map((o,l)=>me.jsx("div",{className:`hex-yao${o?" solid":" broken"}`,style:{height:a*.52,top:l*a+a*.24},children:!o&&me.jsx("span",{className:"hex-yao-gap"})},l))})}function f_({phase:n,lines:e,reduced:t}){const i=et.useRef(null),r=et.useRef({phase:n,lines:e});return r.current={phase:n,lines:e},et.useEffect(()=>{const s=i.current;if(!s)return;const a=s.parentElement,o=a.clientWidth,l=a.clientHeight,c=Math.min(window.devicePixelRatio,2);s.width=o*c,s.height=l*c;const u=s.getContext("2d");u.scale(c,c);const f=o*.3,h=l*.48,d=Math.min(96,o*.16),g=d*.72/6,m=T=>h-d*.36+T*g+g/2,p=(()=>{let T=20260924;return()=>(T=T*1664525+1013904223>>>0,T/2**32)})(),_=[];for(let T=0;T<130;T++){const S=Math.floor(p()*6),E=p()<.45,b=E?(p()<.5?-1:1)*(.12+p()*.06):0,x=f+(p()-.5)*d*(E?.76:.96)+b*d,A=m(S)+(p()-.5)*g*.5,C=p()*Math.PI*2,R=(.25+p()*.45)*Math.min(o,l)*.5;_.push({sx:o/2+Math.cos(C)*R*1.25,sy:l/2+Math.sin(C)*R,tx:x,ty:A,delay:p()*.45,size:.8+p()*1.2,gold:p()<.22,seed:p()*1e3})}let v=0;const M=performance.now(),y=T=>{v=requestAnimationFrame(y);const S=(T-M)/1e3,{phase:E,lines:b}=r.current;u.clearRect(0,0,o,l),u.globalCompositeOperation="lighter";const x=Math.min(1,S/1.6),A=E==="casting";for(const U of _){const I=Math.min(1,Math.max(0,(x-U.delay)/(1-U.delay||1))),F=I*I*(3-2*I),O=A&&!t?2.2:.6,j=Math.sin(S*1.7+U.seed)*O,G=Math.cos(S*1.3+U.seed*1.7)*O,W=U.sx+(U.tx-U.sx)*F+j*F,N=U.sy+(U.ty-U.sy)*F+G*F,k=.55+.45*Math.sin(S*2.1+U.seed*3);u.beginPath(),u.arc(W,N,U.size,0,Math.PI*2),u.fillStyle=U.gold?`rgba(240, 205, 127, ${.5*k*F})`:`rgba(232, 226, 210, ${.4*k*F})`,u.fill()}const R=E==="done"||E==="error"?gm(b):null,L=Math.floor(S/.12);for(let U=0;U<6;U++){const I=m(U),F=R?R[U]:(U*7+L)%3!==0,O=E==="gather"?Math.max(0,x-.55)*.6:A?.3+.25*Math.sin(S*4+U):.85;if(O<=.01)continue;u.fillStyle=`rgba(240, 205, 127, ${O})`;const j=Math.max(2,g*.34);if(F)u.fillRect(f-d/2,I-j/2,d,j);else{const G=d/2*.76;u.fillRect(f-d/2,I-j/2,G,j),u.fillRect(f+d/2-G,I-j/2,G,j)}}u.globalCompositeOperation="source-over"};return v=requestAnimationFrame(y),()=>cancelAnimationFrame(v)},[t]),me.jsx("canvas",{ref:i,className:"starmap-div-ritual-canvas"})}function d_({profile:n,open:e,onClose:t}){const i=et.useMemo(()=>typeof matchMedia<"u"&&matchMedia("(prefers-reduced-motion: reduce)").matches,[]),[r,s]=et.useState("gather"),[a,o]=et.useState("play"),[l,c]=et.useState(""),[u,f]=et.useState(null),[h,d]=et.useState(""),[g,m]=et.useState(!1),[p,_]=et.useState({state:"idle",count:0,error:""}),v=et.useRef(0),M=Yg(),y=async(x,A)=>{const C=++v.current;s("casting"),f(null),d(""),_({state:"idle",count:0,error:""});try{const R={mode:x,question:A},L=await $f(`/profiles/${encodeURIComponent(n)}/divination`,R);if(C!==v.current)return;f(L),s("done"),window.setTimeout(()=>m(!0),i?0:500)}catch(R){if(C!==v.current)return;d(R instanceof Error?R.message:String(R)),s("error"),window.setTimeout(()=>m(!0),i?0:500)}},T=async(x,A)=>{if(!(p.state==="working"||p.state==="done")){_({state:"working",count:0,error:""});try{for(const C of x)await $f(`/profiles/${encodeURIComponent(n)}/gap/intake`,{title:`学习 ${C.label||C.id}`,node_id:C.id,why:A,section:"Queue"});M.invalidateQueries({queryKey:["profiles",n,"kanban"]}),M.invalidateQueries({queryKey:["profiles",n,"projects-board"]}),_({state:"done",count:x.length,error:""})}catch(C){_({state:"error",count:0,error:C instanceof Error?C.message:String(C)})}}};if(et.useEffect(()=>{if(!e)return;s("gather"),f(null),d(""),m(!1),o("play"),c(""),y("play","");const x=window.setTimeout(()=>s(A=>A==="gather"?"casting":A),1650);return()=>window.clearTimeout(x)},[e]),!e)return null;const S=u==null?void 0:u.hexagram,E=(S==null?void 0:S.symbol_lines)??[1,1,1,1,1,1],b=u_(u);return me.jsxs("div",{className:`starmap-div-root${g?" docked":""}`,"data-starmap-ui":!0,"data-testid":"divination-root",children:[me.jsx("div",{className:"starmap-div-overlay",children:me.jsx(f_,{phase:r,lines:E,reduced:i})}),me.jsxs("div",{className:`starmap-div-card${g?" open":""}`,"data-testid":"divination-card",role:"dialog","aria-label":"占卜",children:[me.jsxs("div",{className:"div-card-head",children:[me.jsx(h_,{lines:E,size:44,animated:r==="casting"}),me.jsx("div",{className:"div-card-title",children:r==="casting"||r==="gather"?me.jsx("span",{className:"div-casting-label",children:"摇卦…"}):r==="error"?me.jsx("span",{className:"div-error-label",children:"占问未果"}):me.jsxs(me.Fragment,{children:[me.jsx("span",{className:"div-hx-name",children:S==null?void 0:S.name}),(u==null?void 0:u.source)==="rule"&&me.jsx("span",{className:"div-offline-note",children:"离线卦"})]})}),me.jsx("button",{type:"button",className:"div-close",onClick:t,"aria-label":"收起卦辞 (Esc)","data-testid":"divination-close",children:"×"})]}),r==="error"?me.jsx("p",{className:"div-error",role:"alert",children:h}):u&&me.jsxs(me.Fragment,{children:[me.jsx("p",{className:"div-judgment","data-testid":"divination-judgment",children:S==null?void 0:S.judgment}),me.jsx("p",{className:"div-reading","data-testid":"divination-reading",children:u.reading}),u.mode==="serious"&&b.length>0&&me.jsx("div",{className:"div-intake","data-testid":"divination-intake-zone",children:p.state==="done"?me.jsxs("p",{className:"div-intake-done","data-testid":"divination-intake-done",children:["已将 ",p.count," 处缺口化为看板任务(Queue)。",me.jsx(qg,{to:`/p/${encodeURIComponent(n)}/projects`,className:"div-intake-link","data-testid":"divination-intake-link",children:"去项目页看看 →"})]}):me.jsxs(me.Fragment,{children:[me.jsx("button",{type:"button",className:"div-cast-btn div-intake-btn",disabled:p.state==="working","data-testid":"divination-intake",onClick:()=>T(b,u.question),children:p.state==="working"?"化为任务…":`化为任务(${b.length} 处所缺)`}),p.state==="error"&&me.jsxs("p",{className:"div-error",role:"alert","data-testid":"divination-intake-error",children:["化为任务未果:",p.error]})]})})]}),me.jsxs("div",{className:"div-chips",role:"tablist",children:[me.jsx("button",{type:"button",role:"tab","aria-selected":a==="play",className:`div-chip${a==="play"?" active":""}`,"data-testid":"divination-mode-play",onClick:()=>{o("play"),y("play","")},children:"戏占"}),me.jsx("button",{type:"button",role:"tab","aria-selected":a==="serious",className:`div-chip${a==="serious"?" active":""}`,"data-testid":"divination-mode-serious",onClick:()=>o("serious"),children:"正占"})]}),a==="serious"&&me.jsxs("div",{className:"div-question",children:[me.jsx("textarea",{value:l,onChange:x=>c(x.target.value),rows:2,placeholder:"所问何事?(接真实差距分析)","data-testid":"divination-question"}),me.jsx("button",{type:"button",className:"div-cast-btn",disabled:!l.trim(),"data-testid":"divination-cast",onClick:()=>y("serious",l.trim()),children:"起卦"})]})]})]})}function p_(n){const e=`${n.id} ${n.title}`.toLowerCase();return/exercise|锻炼|健身/.test(e)?"炼":/learning|学习/.test(e)?"学":/康复|复健|recovery/.test(e)?"复":/read|读书|阅读/.test(e)?"读":/run|跑步/.test(e)?"跑":/meditat|冥想|静坐/.test(e)?"坐":/sleep|睡眠|作息/.test(e)?"息":Array.from(n.title||n.id)[0]??"课"}function ed(n,e){const t=(n.recent_days??[]).find(r=>r.date===e),i=((t==null?void 0:t.checkin_ids)??[]).filter(r=>r.length>0);return i.length>0?i[i.length-1]:""}function m_({habit:n,streak:e,done:t,today:i}){return me.jsxs("div",{style:{maxWidth:240},children:[me.jsx("div",{style:{fontSize:14,marginBottom:6},children:n.title||n.id}),me.jsx("div",{style:{display:"flex",gap:5,alignItems:"center",marginBottom:6},children:(n.week??[]).map(r=>{const s=r.date===i&&!r.future;return me.jsx("span",{title:r.date,"data-testid":`seal-slip-dot-${n.id}-${r.date}`,"data-done":r.done?"true":"false","data-today":s?"true":"false",style:{display:"inline-block",width:9,height:9,borderRadius:"50%",boxSizing:"border-box",background:r.done?"#dcae55":"transparent",border:`1px solid ${r.done?"#dcae55":"rgba(242, 237, 224, 0.35)"}`,boxShadow:s?"0 0 0 1.5px #dcae55":void 0,opacity:r.future?.4:1}},r.date)})}),me.jsxs("div",{style:{fontSize:12,opacity:.8},children:["连续 ",e," 天"]}),me.jsx("div",{style:{fontSize:11,opacity:.6,marginTop:6},children:t?"右键/长按 = 销印(撤销今日最近一次打卡)":"点击印面 = 今日打卡"})]})}function g_({profile:n}){var y,T;const e=Kg(n),t=Zg(n),i=$g(n),r=((y=e.data)==null?void 0:y.board.habits)??[],s=((T=e.data)==null?void 0:T.board.today)??"",[a,o]=et.useState(null),[l,c]=et.useState(null),[u,f]=et.useState(null),h=et.useRef(null),d=et.useRef(!1),g=et.useRef(typeof matchMedia<"u"&&matchMedia("(pointer: coarse)").matches),m=r.find(S=>S.id===u)??null;if(et.useEffect(()=>{if(!u)return;const S=E=>{E.key==="Escape"&&f(null)};return window.addEventListener("keydown",S),()=>window.removeEventListener("keydown",S)},[u]),r.length===0)return null;const p=S=>(S.week??[]).some(E=>E.done&&!E.future&&E.date===s),_=S=>{if(p(S)){if(!ed(S,s)){ha.show({color:"yellow",title:"销印",message:`${S.title||S.id} 今日打卡记录缺少 id,暂不可销印(可在项目页日课栏热力图核实)。`});return}c(null),f(S.id)}},v=()=>{if(!m)return;const S=m,E=ed(S,s);if(!E){f(null);return}i.mutate({checkinId:E},{onSuccess:()=>{ha.show({color:"green",title:"已销印",message:`${S.title||S.id} 今日最近一次打卡已删除。`})},onError:b=>{ha.show({color:"red",title:"销印失败",message:b instanceof Error?b.message:String(b)})},onSettled:()=>f(null)})},M=S=>{t.mutate({habit:S.id,date:"",summary:"",note:""},{onSuccess:()=>{ha.show({color:"green",title:"已打卡",message:`${S.title||S.id} 今日打卡成功。`})},onError:E=>{ha.show({color:"red",title:"打卡失败",message:E instanceof Error?E.message:String(E)})}})};return me.jsxs("div",{className:"starmap-habit-seal","data-starmap-ui":!0,"data-testid":"habit-seal",children:[m&&me.jsxs("div",{className:"starmap-habit-unseal",role:"alertdialog","aria-label":"销印确认","data-testid":`seal-unseal-${m.id}`,children:[me.jsxs("span",{className:"starmap-habit-unseal-text",children:["销印「",m.title||m.id,"」今日最近一次打卡?"]}),me.jsx("button",{type:"button",className:"starmap-habit-unseal-btn danger",disabled:i.isPending,onClick:v,"data-testid":`seal-unseal-yes-${m.id}`,children:"销印"}),me.jsx("button",{type:"button",className:"starmap-habit-unseal-btn",onClick:()=>f(null),"data-testid":`seal-unseal-no-${m.id}`,children:"取消"})]}),me.jsxs("span",{className:"starmap-habit-seal-caption","aria-hidden":"true",children:[me.jsx("span",{children:"日"}),me.jsx("span",{children:"课"})]}),r.map(S=>{const E=p(S),b=S.id;return me.jsx(Jg,{label:me.jsx(m_,{habit:S,streak:S.streak??0,done:E,today:s}),withArrow:!0,position:"top",disabled:m!==null,opened:g.current?l===b:void 0,events:{hover:!g.current,focus:!0,touch:!1},children:me.jsx("button",{type:"button",className:`starmap-habit-stamp${a===b?" stamping":""}`,"data-testid":`habit-seal-${b}`,"data-done":E?"true":"false",disabled:t.isPending||i.isPending,"aria-label":`日课打卡 ${S.title||S.id}`,"aria-pressed":E,onClick:()=>{if(d.current){d.current=!1;return}o(b),window.setTimeout(()=>o(null),380),M(S)},onContextMenu:x=>{x.preventDefault(),_(S)},onPointerDown:()=>{g.current&&(h.current=setTimeout(()=>{d.current=!0,p(S)?_(S):c(b)},550))},onPointerUp:()=>{h.current&&clearTimeout(h.current)},onPointerLeave:()=>{h.current&&clearTimeout(h.current),l===b&&c(null)},children:p_(S)})},b)})]})}const _m=[{key:"active",title:"进行中",match:n=>n.status==="active"},{key:"paused",title:"暂停",match:n=>n.status==="paused"},{key:"carved",title:"已镌刻",match:n=>n.status==="completed"}];function __(n){const e=[{id:"north"}];for(const t of _m)for(const i of n.goals.filter(t.match))e.push({id:i.id,goal:i});return e}function v_(n,e,t){return n<=0?-1:(((e<0?0:e)+t)%n+n)%n}const td="nblane-starmap-catalog-hint-seen";function x_({open:n,snapshot:e,profile:t,selection:i,onFocus:r}){const[s,a]=et.useState(!1),[o,l]=et.useState(""),[c,u]=et.useState("north"),[f,h]=et.useState(!1),d=et.useRef(null),g=Qg(t),m=et.useMemo(()=>__(e),[e]),p=e.north.is_set?e.north.brief||e.north.full||"北极星":"虚位 · 点击立星",_=v=>{u(v),r(v)};return et.useEffect(()=>{if(!n||!i)return;const v=i.kind==="north"?"north":i.kind==="goal"?i.id:null;v&&m.some(M=>M.id===v)&&u(v)},[n,i,m]),et.useEffect(()=>{var v,M,y;!n||!c||(y=(M=(v=d.current)==null?void 0:v.querySelector(`[data-catalog-id="${CSS.escape(c)}"]`))==null?void 0:M.scrollIntoView)==null||y.call(M,{block:"nearest"})},[n,c]),et.useEffect(()=>{if(!n||s)return;const v=M=>{const y=M.target;if(y&&/^(INPUT|TEXTAREA|SELECT)$/.test(y.tagName))return;const T=M.key==="ArrowDown"||M.key==="j"?1:M.key==="ArrowUp"||M.key==="k"?-1:0;if(T!==0){M.preventDefault();const S=m.findIndex(b=>b.id===c),E=m[v_(m.length,S,T)];E&&u(E.id)}else M.key==="Enter"&&(M.preventDefault(),c&&m.some(S=>S.id===c)&&r(c))};return window.addEventListener("keydown",v),()=>window.removeEventListener("keydown",v)},[n,s,m,c,r]),et.useEffect(()=>{if(!n)return;try{if(sessionStorage.getItem(td))return;sessionStorage.setItem(td,"1")}catch{}h(!0);const v=window.setTimeout(()=>h(!1),2600);return()=>window.clearTimeout(v)},[n]),me.jsx("div",{className:`starmap-catalog${n?" open":""}`,ref:d,"data-starmap-ui":!0,"data-testid":"starmap-catalog","aria-hidden":!n,children:n&&me.jsxs(me.Fragment,{children:[me.jsx("h3",{children:"星表"}),f&&me.jsxs("p",{className:"starmap-catalog-hintbar","data-testid":"catalog-hintbar",children:[me.jsx("kbd",{children:"↑"}),me.jsx("kbd",{children:"↓"})," 移动 · ",me.jsx("kbd",{children:"Enter"})," 开卡 · ",me.jsx("kbd",{children:"Esc"})," 回纯图"]}),me.jsxs("div",{className:"starmap-catalog-section","data-testid":"catalog-north",children:[me.jsx("h4",{children:"北极星"}),me.jsx(nd,{id:"north",active:c==="north",className:e.north.is_set?"":" vacant",title:p,sub:e.north.visibility==="public"?"可公开":"仅本地",onFocus:_})]}),_m.map(v=>{const M=e.goals.filter(v.match);return me.jsxs("div",{className:"starmap-catalog-section","data-testid":`catalog-${v.key}`,children:[me.jsxs("h4",{children:[v.title,M.length>0&&me.jsx("span",{className:"sec-count",children:M.length})]}),M.length===0&&v.key==="active"&&me.jsx("p",{className:"starmap-catalog-empty",children:"恒星虚位 — 自下方新增目标。"}),M.map(y=>me.jsx(nd,{id:y.id,active:c===y.id,className:y.status==="completed"?" carved":"",title:y.title,sub:y.target||"",onFocus:_},y.id))]},v.key)}),!s&&me.jsx("button",{type:"button",className:"starmap-catalog-add",onClick:()=>{l(""),a(!0)},"data-testid":"catalog-add-goal",children:"＋ 新增目标"}),s&&me.jsx(b_,{saving:g.isPending,error:g.error,onCancel:()=>a(!1),onSubmit:v=>g.mutate(v,{onSuccess:M=>{a(!1),l(`「${M.goal.title||M.goal.id}」已入星表`)}})}),o&&me.jsx("p",{className:"starmap-catalog-note",children:o})]})})}function nd({id:n,active:e,className:t,title:i,sub:r,onFocus:s}){return me.jsxs("button",{type:"button",className:`starmap-catalog-row${e?" active":""}${t}`,onClick:()=>s(n),"data-catalog-id":n,"data-testid":`catalog-row-${n}`,children:[me.jsx("span",{className:"row-title",children:i}),me.jsx("span",{className:"row-sub",children:r}),me.jsx("kbd",{className:"row-kbd",children:"Enter"})]})}function b_({saving:n,error:e,onSubmit:t,onCancel:i}){const[r,s]=et.useState(""),[a,o]=et.useState(""),[l,c]=et.useState("");return me.jsxs("div",{className:"starmap-edit starmap-catalog-form","data-testid":"catalog-goal-form",children:[me.jsxs("label",{children:[me.jsx("span",{children:"标题"}),me.jsx("input",{value:r,onChange:u=>s(u.target.value),placeholder:"新恒星之名","data-testid":"create-goal-title"})]}),me.jsxs("label",{children:[me.jsx("span",{children:"摘要"}),me.jsx("textarea",{value:a,onChange:u=>o(u.target.value),rows:2,"data-testid":"create-goal-summary"})]}),me.jsxs("label",{children:[me.jsx("span",{children:"目标日期"}),me.jsx("input",{type:"date",value:l,onChange:u=>c(u.target.value),"data-testid":"create-goal-target"})]}),e&&me.jsx("p",{className:"starmap-edit-error",role:"alert",children:e.message}),me.jsxs("div",{className:"starmap-edit-actions",children:[me.jsx("button",{type:"button",className:"starmap-save",disabled:n||!r.trim(),onClick:()=>t({title:r.trim(),summary:a.trim(),target:l}),"data-testid":"create-goal-save",children:n?"镌刻中…":"落印"}),me.jsx("button",{type:"button",className:"starmap-cancel",disabled:n,onClick:i,children:"收起刻刀"})]})]})}/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */const qa="184",Ds={ROTATE:0,DOLLY:1,PAN:2},As={ROTATE:0,PAN:1,DOLLY_PAN:2,DOLLY_ROTATE:3},M_=0,id=1,S_=2,Yo=1,y_=2,wa=3,Hi=0,sn=1,En=2,Mn=0,kr=1,al=2,rd=3,sd=4,T_=5,Fr=100,E_=101,w_=102,A_=103,R_=104,C_=200,P_=201,D_=202,U_=203,Au=204,Ru=205,L_=206,I_=207,F_=208,N_=209,O_=210,B_=211,k_=212,z_=213,G_=214,Cu=0,ol=1,Pu=2,Os=3,Du=4,Uu=5,Lu=6,Iu=7,vm=0,H_=1,V_=2,Ai=0,xm=1,bm=2,Mm=3,Sm=4,ym=5,Tm=6,Em=7,wm=300,Yr=301,Bs=302,cc=303,uc=304,Ul=306,Fu=1e3,ki=1001,Nu=1002,cn=1003,W_=1004,co=1005,zt=1006,hc=1007,Or=1008,jt=1009,Am=1010,Rm=1011,Ba=1012,Yh=1013,Ri=1014,li=1015,Vi=1016,qh=1017,Kh=1018,ks=1020,Cm=35902,Pm=35899,Dm=1021,Um=1022,ci=1023,Wi=1026,lr=1027,Lm=1028,Zh=1029,qr=1030,$h=1031,Jh=1033,qo=33776,Ko=33777,Zo=33778,$o=33779,Ou=35840,Bu=35841,ku=35842,zu=35843,Gu=36196,Hu=37492,Vu=37496,Wu=37488,Xu=37489,ll=37490,ju=37491,Yu=37808,qu=37809,Ku=37810,Zu=37811,$u=37812,Ju=37813,Qu=37814,eh=37815,th=37816,nh=37817,ih=37818,rh=37819,sh=37820,ah=37821,oh=36492,lh=36494,ch=36495,uh=36283,hh=36284,cl=36285,fh=36286,Ka=3200,X_=3201,ad=0,j_=1,bi="",Tt="srgb",zs="srgb-linear",ul="linear",Mt="srgb",as=7680,od=519,Y_=512,q_=513,K_=514,Qh=515,Z_=516,$_=517,ef=518,J_=519,dh=35044,ld="300 es",Ti=2e3,hl=2001;function Q_(n){for(let e=n.length-1;e>=0;--e)if(n[e]>=65535)return!0;return!1}function fl(n){return document.createElementNS("http://www.w3.org/1999/xhtml",n)}function ev(){const n=fl("canvas");return n.style.display="block",n}const cd={};function dl(...n){const e="THREE."+n.shift();console.log(e,...n)}function Im(n){const e=n[0];if(typeof e=="string"&&e.startsWith("TSL:")){const t=n[1];t&&t.isStackTrace?n[0]+=" "+t.getLocation():n[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return n}function Je(...n){n=Im(n);const e="THREE."+n.shift();{const t=n[0];t&&t.isStackTrace?console.warn(t.getError(e)):console.warn(e,...n)}}function pt(...n){n=Im(n);const e="THREE."+n.shift();{const t=n[0];t&&t.isStackTrace?console.error(t.getError(e)):console.error(e,...n)}}function ph(...n){const e=n.join(" ");e in cd||(cd[e]=!0,Je(...n))}function tv(n,e,t){return new Promise(function(i,r){function s(){switch(n.clientWaitSync(e,n.SYNC_FLUSH_COMMANDS_BIT,0)){case n.WAIT_FAILED:r();break;case n.TIMEOUT_EXPIRED:setTimeout(s,t);break;default:i()}}setTimeout(s,t)})}const nv={[Cu]:ol,[Pu]:Lu,[Du]:Iu,[Os]:Uu,[ol]:Cu,[Lu]:Pu,[Iu]:Du,[Uu]:Os};class hi{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});const i=this._listeners;i[e]===void 0&&(i[e]=[]),i[e].indexOf(t)===-1&&i[e].push(t)}hasEventListener(e,t){const i=this._listeners;return i===void 0?!1:i[e]!==void 0&&i[e].indexOf(t)!==-1}removeEventListener(e,t){const i=this._listeners;if(i===void 0)return;const r=i[e];if(r!==void 0){const s=r.indexOf(t);s!==-1&&r.splice(s,1)}}dispatchEvent(e){const t=this._listeners;if(t===void 0)return;const i=t[e.type];if(i!==void 0){e.target=this;const r=i.slice(0);for(let s=0,a=r.length;s<a;s++)r[s].call(this,e);e.target=null}}}const fn=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Jo=Math.PI/180,mh=180/Math.PI;function dr(){const n=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,i=Math.random()*4294967295|0;return(fn[n&255]+fn[n>>8&255]+fn[n>>16&255]+fn[n>>24&255]+"-"+fn[e&255]+fn[e>>8&255]+"-"+fn[e>>16&15|64]+fn[e>>24&255]+"-"+fn[t&63|128]+fn[t>>8&255]+"-"+fn[t>>16&255]+fn[t>>24&255]+fn[i&255]+fn[i>>8&255]+fn[i>>16&255]+fn[i>>24&255]).toLowerCase()}function lt(n,e,t){return Math.max(e,Math.min(t,n))}function iv(n,e){return(n%e+e)%e}function fc(n,e,t){return(1-t)*n+t*e}function Mi(n,e){switch(e.constructor){case Float32Array:return n;case Uint32Array:return n/4294967295;case Uint16Array:return n/65535;case Uint8Array:return n/255;case Int32Array:return Math.max(n/2147483647,-1);case Int16Array:return Math.max(n/32767,-1);case Int8Array:return Math.max(n/127,-1);default:throw new Error("Invalid component type.")}}function St(n,e){switch(e.constructor){case Float32Array:return n;case Uint32Array:return Math.round(n*4294967295);case Uint16Array:return Math.round(n*65535);case Uint8Array:return Math.round(n*255);case Int32Array:return Math.round(n*2147483647);case Int16Array:return Math.round(n*32767);case Int8Array:return Math.round(n*127);default:throw new Error("Invalid component type.")}}const rv={DEG2RAD:Jo},Ff=class Ff{constructor(e=0,t=0){this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const t=this.x,i=this.y,r=e.elements;return this.x=r[0]*t+r[3]*i+r[6],this.y=r[1]*t+r[4]*i+r[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=lt(this.x,e.x,t.x),this.y=lt(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=lt(this.x,e,t),this.y=lt(this.y,e,t),this}clampLength(e,t){const i=this.length();return this.divideScalar(i||1).multiplyScalar(lt(i,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const i=this.dot(e)/t;return Math.acos(lt(i,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,i=this.y-e.y;return t*t+i*i}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,i){return this.x=e.x+(t.x-e.x)*i,this.y=e.y+(t.y-e.y)*i,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){const i=Math.cos(t),r=Math.sin(t),s=this.x-e.x,a=this.y-e.y;return this.x=s*i-a*r+e.x,this.y=s*r+a*i+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};Ff.prototype.isVector2=!0;let Xe=Ff;class _r{constructor(e=0,t=0,i=0,r=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=i,this._w=r}static slerpFlat(e,t,i,r,s,a,o){let l=i[r+0],c=i[r+1],u=i[r+2],f=i[r+3],h=s[a+0],d=s[a+1],g=s[a+2],m=s[a+3];if(f!==m||l!==h||c!==d||u!==g){let p=l*h+c*d+u*g+f*m;p<0&&(h=-h,d=-d,g=-g,m=-m,p=-p);let _=1-o;if(p<.9995){const v=Math.acos(p),M=Math.sin(v);_=Math.sin(_*v)/M,o=Math.sin(o*v)/M,l=l*_+h*o,c=c*_+d*o,u=u*_+g*o,f=f*_+m*o}else{l=l*_+h*o,c=c*_+d*o,u=u*_+g*o,f=f*_+m*o;const v=1/Math.sqrt(l*l+c*c+u*u+f*f);l*=v,c*=v,u*=v,f*=v}}e[t]=l,e[t+1]=c,e[t+2]=u,e[t+3]=f}static multiplyQuaternionsFlat(e,t,i,r,s,a){const o=i[r],l=i[r+1],c=i[r+2],u=i[r+3],f=s[a],h=s[a+1],d=s[a+2],g=s[a+3];return e[t]=o*g+u*f+l*d-c*h,e[t+1]=l*g+u*h+c*f-o*d,e[t+2]=c*g+u*d+o*h-l*f,e[t+3]=u*g-o*f-l*h-c*d,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,i,r){return this._x=e,this._y=t,this._z=i,this._w=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){const i=e._x,r=e._y,s=e._z,a=e._order,o=Math.cos,l=Math.sin,c=o(i/2),u=o(r/2),f=o(s/2),h=l(i/2),d=l(r/2),g=l(s/2);switch(a){case"XYZ":this._x=h*u*f+c*d*g,this._y=c*d*f-h*u*g,this._z=c*u*g+h*d*f,this._w=c*u*f-h*d*g;break;case"YXZ":this._x=h*u*f+c*d*g,this._y=c*d*f-h*u*g,this._z=c*u*g-h*d*f,this._w=c*u*f+h*d*g;break;case"ZXY":this._x=h*u*f-c*d*g,this._y=c*d*f+h*u*g,this._z=c*u*g+h*d*f,this._w=c*u*f-h*d*g;break;case"ZYX":this._x=h*u*f-c*d*g,this._y=c*d*f+h*u*g,this._z=c*u*g-h*d*f,this._w=c*u*f+h*d*g;break;case"YZX":this._x=h*u*f+c*d*g,this._y=c*d*f+h*u*g,this._z=c*u*g-h*d*f,this._w=c*u*f-h*d*g;break;case"XZY":this._x=h*u*f-c*d*g,this._y=c*d*f-h*u*g,this._z=c*u*g+h*d*f,this._w=c*u*f+h*d*g;break;default:Je("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){const i=t/2,r=Math.sin(i);return this._x=e.x*r,this._y=e.y*r,this._z=e.z*r,this._w=Math.cos(i),this._onChangeCallback(),this}setFromRotationMatrix(e){const t=e.elements,i=t[0],r=t[4],s=t[8],a=t[1],o=t[5],l=t[9],c=t[2],u=t[6],f=t[10],h=i+o+f;if(h>0){const d=.5/Math.sqrt(h+1);this._w=.25/d,this._x=(u-l)*d,this._y=(s-c)*d,this._z=(a-r)*d}else if(i>o&&i>f){const d=2*Math.sqrt(1+i-o-f);this._w=(u-l)/d,this._x=.25*d,this._y=(r+a)/d,this._z=(s+c)/d}else if(o>f){const d=2*Math.sqrt(1+o-i-f);this._w=(s-c)/d,this._x=(r+a)/d,this._y=.25*d,this._z=(l+u)/d}else{const d=2*Math.sqrt(1+f-i-o);this._w=(a-r)/d,this._x=(s+c)/d,this._y=(l+u)/d,this._z=.25*d}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let i=e.dot(t)+1;return i<1e-8?(i=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=i):(this._x=0,this._y=-e.z,this._z=e.y,this._w=i)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=i),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(lt(this.dot(e),-1,1)))}rotateTowards(e,t){const i=this.angleTo(e);if(i===0)return this;const r=Math.min(1,t/i);return this.slerp(e,r),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){const i=e._x,r=e._y,s=e._z,a=e._w,o=t._x,l=t._y,c=t._z,u=t._w;return this._x=i*u+a*o+r*c-s*l,this._y=r*u+a*l+s*o-i*c,this._z=s*u+a*c+i*l-r*o,this._w=a*u-i*o-r*l-s*c,this._onChangeCallback(),this}slerp(e,t){let i=e._x,r=e._y,s=e._z,a=e._w,o=this.dot(e);o<0&&(i=-i,r=-r,s=-s,a=-a,o=-o);let l=1-t;if(o<.9995){const c=Math.acos(o),u=Math.sin(c);l=Math.sin(l*c)/u,t=Math.sin(t*c)/u,this._x=this._x*l+i*t,this._y=this._y*l+r*t,this._z=this._z*l+s*t,this._w=this._w*l+a*t,this._onChangeCallback()}else this._x=this._x*l+i*t,this._y=this._y*l+r*t,this._z=this._z*l+s*t,this._w=this._w*l+a*t,this.normalize();return this}slerpQuaternions(e,t,i){return this.copy(e).slerp(t,i)}random(){const e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),i=Math.random(),r=Math.sqrt(1-i),s=Math.sqrt(i);return this.set(r*Math.sin(e),r*Math.cos(e),s*Math.sin(t),s*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}const Nf=class Nf{constructor(e=0,t=0,i=0){this.x=e,this.y=t,this.z=i}set(e,t,i){return i===void 0&&(i=this.z),this.x=e,this.y=t,this.z=i,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(ud.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(ud.setFromAxisAngle(e,t))}applyMatrix3(e){const t=this.x,i=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[3]*i+s[6]*r,this.y=s[1]*t+s[4]*i+s[7]*r,this.z=s[2]*t+s[5]*i+s[8]*r,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const t=this.x,i=this.y,r=this.z,s=e.elements,a=1/(s[3]*t+s[7]*i+s[11]*r+s[15]);return this.x=(s[0]*t+s[4]*i+s[8]*r+s[12])*a,this.y=(s[1]*t+s[5]*i+s[9]*r+s[13])*a,this.z=(s[2]*t+s[6]*i+s[10]*r+s[14])*a,this}applyQuaternion(e){const t=this.x,i=this.y,r=this.z,s=e.x,a=e.y,o=e.z,l=e.w,c=2*(a*r-o*i),u=2*(o*t-s*r),f=2*(s*i-a*t);return this.x=t+l*c+a*f-o*u,this.y=i+l*u+o*c-s*f,this.z=r+l*f+s*u-a*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const t=this.x,i=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[4]*i+s[8]*r,this.y=s[1]*t+s[5]*i+s[9]*r,this.z=s[2]*t+s[6]*i+s[10]*r,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=lt(this.x,e.x,t.x),this.y=lt(this.y,e.y,t.y),this.z=lt(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=lt(this.x,e,t),this.y=lt(this.y,e,t),this.z=lt(this.z,e,t),this}clampLength(e,t){const i=this.length();return this.divideScalar(i||1).multiplyScalar(lt(i,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,i){return this.x=e.x+(t.x-e.x)*i,this.y=e.y+(t.y-e.y)*i,this.z=e.z+(t.z-e.z)*i,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){const i=e.x,r=e.y,s=e.z,a=t.x,o=t.y,l=t.z;return this.x=r*l-s*o,this.y=s*a-i*l,this.z=i*o-r*a,this}projectOnVector(e){const t=e.lengthSq();if(t===0)return this.set(0,0,0);const i=e.dot(this)/t;return this.copy(e).multiplyScalar(i)}projectOnPlane(e){return dc.copy(this).projectOnVector(e),this.sub(dc)}reflect(e){return this.sub(dc.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const i=this.dot(e)/t;return Math.acos(lt(i,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,i=this.y-e.y,r=this.z-e.z;return t*t+i*i+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,i){const r=Math.sin(t)*e;return this.x=r*Math.sin(i),this.y=Math.cos(t)*e,this.z=r*Math.cos(i),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,i){return this.x=e*Math.sin(t),this.y=i,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){const t=this.setFromMatrixColumn(e,0).length(),i=this.setFromMatrixColumn(e,1).length(),r=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=i,this.z=r,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,t=Math.random()*2-1,i=Math.sqrt(1-t*t);return this.x=i*Math.cos(e),this.y=t,this.z=i*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};Nf.prototype.isVector3=!0;let X=Nf;const dc=new X,ud=new _r,Of=class Of{constructor(e,t,i,r,s,a,o,l,c){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,i,r,s,a,o,l,c)}set(e,t,i,r,s,a,o,l,c){const u=this.elements;return u[0]=e,u[1]=r,u[2]=o,u[3]=t,u[4]=s,u[5]=l,u[6]=i,u[7]=a,u[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const t=this.elements,i=e.elements;return t[0]=i[0],t[1]=i[1],t[2]=i[2],t[3]=i[3],t[4]=i[4],t[5]=i[5],t[6]=i[6],t[7]=i[7],t[8]=i[8],this}extractBasis(e,t,i){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),i.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const i=e.elements,r=t.elements,s=this.elements,a=i[0],o=i[3],l=i[6],c=i[1],u=i[4],f=i[7],h=i[2],d=i[5],g=i[8],m=r[0],p=r[3],_=r[6],v=r[1],M=r[4],y=r[7],T=r[2],S=r[5],E=r[8];return s[0]=a*m+o*v+l*T,s[3]=a*p+o*M+l*S,s[6]=a*_+o*y+l*E,s[1]=c*m+u*v+f*T,s[4]=c*p+u*M+f*S,s[7]=c*_+u*y+f*E,s[2]=h*m+d*v+g*T,s[5]=h*p+d*M+g*S,s[8]=h*_+d*y+g*E,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){const e=this.elements,t=e[0],i=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8];return t*a*u-t*o*c-i*s*u+i*o*l+r*s*c-r*a*l}invert(){const e=this.elements,t=e[0],i=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8],f=u*a-o*c,h=o*l-u*s,d=c*s-a*l,g=t*f+i*h+r*d;if(g===0)return this.set(0,0,0,0,0,0,0,0,0);const m=1/g;return e[0]=f*m,e[1]=(r*c-u*i)*m,e[2]=(o*i-r*a)*m,e[3]=h*m,e[4]=(u*t-r*l)*m,e[5]=(r*s-o*t)*m,e[6]=d*m,e[7]=(i*l-c*t)*m,e[8]=(a*t-i*s)*m,this}transpose(){let e;const t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,i,r,s,a,o){const l=Math.cos(s),c=Math.sin(s);return this.set(i*l,i*c,-i*(l*a+c*o)+a+e,-r*c,r*l,-r*(-c*a+l*o)+o+t,0,0,1),this}scale(e,t){return this.premultiply(pc.makeScale(e,t)),this}rotate(e){return this.premultiply(pc.makeRotation(-e)),this}translate(e,t){return this.premultiply(pc.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){const t=Math.cos(e),i=Math.sin(e);return this.set(t,-i,0,i,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){const t=this.elements,i=e.elements;for(let r=0;r<9;r++)if(t[r]!==i[r])return!1;return!0}fromArray(e,t=0){for(let i=0;i<9;i++)this.elements[i]=e[i+t];return this}toArray(e=[],t=0){const i=this.elements;return e[t]=i[0],e[t+1]=i[1],e[t+2]=i[2],e[t+3]=i[3],e[t+4]=i[4],e[t+5]=i[5],e[t+6]=i[6],e[t+7]=i[7],e[t+8]=i[8],e}clone(){return new this.constructor().fromArray(this.elements)}};Of.prototype.isMatrix3=!0;let rt=Of;const pc=new rt,hd=new rt().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),fd=new rt().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function sv(){const n={enabled:!0,workingColorSpace:zs,spaces:{},convert:function(r,s,a){return this.enabled===!1||s===a||!s||!a||(this.spaces[s].transfer===Mt&&(r.r=zi(r.r),r.g=zi(r.g),r.b=zi(r.b)),this.spaces[s].primaries!==this.spaces[a].primaries&&(r.applyMatrix3(this.spaces[s].toXYZ),r.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===Mt&&(r.r=Us(r.r),r.g=Us(r.g),r.b=Us(r.b))),r},workingToColorSpace:function(r,s){return this.convert(r,this.workingColorSpace,s)},colorSpaceToWorking:function(r,s){return this.convert(r,s,this.workingColorSpace)},getPrimaries:function(r){return this.spaces[r].primaries},getTransfer:function(r){return r===bi?ul:this.spaces[r].transfer},getToneMappingMode:function(r){return this.spaces[r].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(r,s=this.workingColorSpace){return r.fromArray(this.spaces[s].luminanceCoefficients)},define:function(r){Object.assign(this.spaces,r)},_getMatrix:function(r,s,a){return r.copy(this.spaces[s].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(r){return this.spaces[r].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(r=this.workingColorSpace){return this.spaces[r].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(r,s){return ph("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),n.workingToColorSpace(r,s)},toWorkingColorSpace:function(r,s){return ph("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),n.colorSpaceToWorking(r,s)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],i=[.3127,.329];return n.define({[zs]:{primaries:e,whitePoint:i,transfer:ul,toXYZ:hd,fromXYZ:fd,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:Tt},outputColorSpaceConfig:{drawingBufferColorSpace:Tt}},[Tt]:{primaries:e,whitePoint:i,transfer:Mt,toXYZ:hd,fromXYZ:fd,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:Tt}}}),n}const ft=sv();function zi(n){return n<.04045?n*.0773993808:Math.pow(n*.9478672986+.0521327014,2.4)}function Us(n){return n<.0031308?n*12.92:1.055*Math.pow(n,.41666)-.055}let os;class av{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let i;if(e instanceof HTMLCanvasElement)i=e;else{os===void 0&&(os=fl("canvas")),os.width=e.width,os.height=e.height;const r=os.getContext("2d");e instanceof ImageData?r.putImageData(e,0,0):r.drawImage(e,0,0,e.width,e.height),i=os}return i.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const t=fl("canvas");t.width=e.width,t.height=e.height;const i=t.getContext("2d");i.drawImage(e,0,0,e.width,e.height);const r=i.getImageData(0,0,e.width,e.height),s=r.data;for(let a=0;a<s.length;a++)s[a]=zi(s[a]/255)*255;return i.putImageData(r,0,0),t}else if(e.data){const t=e.data.slice(0);for(let i=0;i<t.length;i++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[i]=Math.floor(zi(t[i]/255)*255):t[i]=zi(t[i]);return{data:t,width:e.width,height:e.height}}else return Je("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let ov=0;class tf{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:ov++}),this.uuid=dr(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){const t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):typeof VideoFrame<"u"&&t instanceof VideoFrame?e.set(t.displayWidth,t.displayHeight,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const i={uuid:this.uuid,url:""},r=this.data;if(r!==null){let s;if(Array.isArray(r)){s=[];for(let a=0,o=r.length;a<o;a++)r[a].isDataTexture?s.push(mc(r[a].image)):s.push(mc(r[a]))}else s=mc(r);i.url=s}return t||(e.images[this.uuid]=i),i}}function mc(n){return typeof HTMLImageElement<"u"&&n instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&n instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&n instanceof ImageBitmap?av.getDataURL(n):n.data?{data:Array.from(n.data),width:n.width,height:n.height,type:n.data.constructor.name}:(Je("Texture: Unable to serialize Texture."),{})}let lv=0;const gc=new X;class Zt extends hi{constructor(e=Zt.DEFAULT_IMAGE,t=Zt.DEFAULT_MAPPING,i=ki,r=ki,s=zt,a=Or,o=ci,l=jt,c=Zt.DEFAULT_ANISOTROPY,u=bi){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:lv++}),this.uuid=dr(),this.name="",this.source=new tf(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=i,this.wrapT=r,this.magFilter=s,this.minFilter=a,this.anisotropy=c,this.format=o,this.internalFormat=null,this.type=l,this.offset=new Xe(0,0),this.repeat=new Xe(1,1),this.center=new Xe(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new rt,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=u,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(gc).x}get height(){return this.source.getSize(gc).y}get depth(){return this.source.getSize(gc).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(const t in e){const i=e[t];if(i===void 0){Je(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}const r=this[t];if(r===void 0){Je(`Texture.setValues(): property '${t}' does not exist.`);continue}r&&i&&r.isVector2&&i.isVector2||r&&i&&r.isVector3&&i.isVector3||r&&i&&r.isMatrix3&&i.isMatrix3?r.copy(i):this[t]=i}}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const i={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(i.userData=this.userData),t||(e.textures[this.uuid]=i),i}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==wm)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Fu:e.x=e.x-Math.floor(e.x);break;case ki:e.x=e.x<0?0:1;break;case Nu:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Fu:e.y=e.y-Math.floor(e.y);break;case ki:e.y=e.y<0?0:1;break;case Nu:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}Zt.DEFAULT_IMAGE=null;Zt.DEFAULT_MAPPING=wm;Zt.DEFAULT_ANISOTROPY=1;const Bf=class Bf{constructor(e=0,t=0,i=0,r=1){this.x=e,this.y=t,this.z=i,this.w=r}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,i,r){return this.x=e,this.y=t,this.z=i,this.w=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const t=this.x,i=this.y,r=this.z,s=this.w,a=e.elements;return this.x=a[0]*t+a[4]*i+a[8]*r+a[12]*s,this.y=a[1]*t+a[5]*i+a[9]*r+a[13]*s,this.z=a[2]*t+a[6]*i+a[10]*r+a[14]*s,this.w=a[3]*t+a[7]*i+a[11]*r+a[15]*s,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,i,r,s;const l=e.elements,c=l[0],u=l[4],f=l[8],h=l[1],d=l[5],g=l[9],m=l[2],p=l[6],_=l[10];if(Math.abs(u-h)<.01&&Math.abs(f-m)<.01&&Math.abs(g-p)<.01){if(Math.abs(u+h)<.1&&Math.abs(f+m)<.1&&Math.abs(g+p)<.1&&Math.abs(c+d+_-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;const M=(c+1)/2,y=(d+1)/2,T=(_+1)/2,S=(u+h)/4,E=(f+m)/4,b=(g+p)/4;return M>y&&M>T?M<.01?(i=0,r=.707106781,s=.707106781):(i=Math.sqrt(M),r=S/i,s=E/i):y>T?y<.01?(i=.707106781,r=0,s=.707106781):(r=Math.sqrt(y),i=S/r,s=b/r):T<.01?(i=.707106781,r=.707106781,s=0):(s=Math.sqrt(T),i=E/s,r=b/s),this.set(i,r,s,t),this}let v=Math.sqrt((p-g)*(p-g)+(f-m)*(f-m)+(h-u)*(h-u));return Math.abs(v)<.001&&(v=1),this.x=(p-g)/v,this.y=(f-m)/v,this.z=(h-u)/v,this.w=Math.acos((c+d+_-1)/2),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=lt(this.x,e.x,t.x),this.y=lt(this.y,e.y,t.y),this.z=lt(this.z,e.z,t.z),this.w=lt(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=lt(this.x,e,t),this.y=lt(this.y,e,t),this.z=lt(this.z,e,t),this.w=lt(this.w,e,t),this}clampLength(e,t){const i=this.length();return this.divideScalar(i||1).multiplyScalar(lt(i,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,i){return this.x=e.x+(t.x-e.x)*i,this.y=e.y+(t.y-e.y)*i,this.z=e.z+(t.z-e.z)*i,this.w=e.w+(t.w-e.w)*i,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};Bf.prototype.isVector4=!0;let Dt=Bf;class cv extends hi{constructor(e=1,t=1,i={}){super(),i=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:zt,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},i),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=i.depth,this.scissor=new Dt(0,0,e,t),this.scissorTest=!1,this.viewport=new Dt(0,0,e,t),this.textures=[];const r={width:e,height:t,depth:i.depth},s=new Zt(r),a=i.count;for(let o=0;o<a;o++)this.textures[o]=s.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(i),this.depthBuffer=i.depthBuffer,this.stencilBuffer=i.stencilBuffer,this.resolveDepthBuffer=i.resolveDepthBuffer,this.resolveStencilBuffer=i.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=i.depthTexture,this.samples=i.samples,this.multiview=i.multiview}_setTextureOptions(e={}){const t={minFilter:zt,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let i=0;i<this.textures.length;i++)this.textures[i].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,i=1){if(this.width!==e||this.height!==t||this.depth!==i){this.width=e,this.height=t,this.depth=i;for(let r=0,s=this.textures.length;r<s;r++)this.textures[r].image.width=e,this.textures[r].image.height=t,this.textures[r].image.depth=i,this.textures[r].isData3DTexture!==!0&&(this.textures[r].isArrayTexture=this.textures[r].image.depth>1);this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,i=e.textures.length;t<i;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;const r=Object.assign({},e.textures[t].image);this.textures[t].source=new tf(r)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this.multiview=e.multiview,this}dispose(){this.dispatchEvent({type:"dispose"})}}class $t extends cv{constructor(e=1,t=1,i={}){super(e,t,i),this.isWebGLRenderTarget=!0}}class Fm extends Zt{constructor(e=null,t=1,i=1,r=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:i,depth:r},this.magFilter=cn,this.minFilter=cn,this.wrapR=ki,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class uv extends Zt{constructor(e=null,t=1,i=1,r=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:i,depth:r},this.magFilter=cn,this.minFilter=cn,this.wrapR=ki,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}const Dl=class Dl{constructor(e,t,i,r,s,a,o,l,c,u,f,h,d,g,m,p){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,i,r,s,a,o,l,c,u,f,h,d,g,m,p)}set(e,t,i,r,s,a,o,l,c,u,f,h,d,g,m,p){const _=this.elements;return _[0]=e,_[4]=t,_[8]=i,_[12]=r,_[1]=s,_[5]=a,_[9]=o,_[13]=l,_[2]=c,_[6]=u,_[10]=f,_[14]=h,_[3]=d,_[7]=g,_[11]=m,_[15]=p,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new Dl().fromArray(this.elements)}copy(e){const t=this.elements,i=e.elements;return t[0]=i[0],t[1]=i[1],t[2]=i[2],t[3]=i[3],t[4]=i[4],t[5]=i[5],t[6]=i[6],t[7]=i[7],t[8]=i[8],t[9]=i[9],t[10]=i[10],t[11]=i[11],t[12]=i[12],t[13]=i[13],t[14]=i[14],t[15]=i[15],this}copyPosition(e){const t=this.elements,i=e.elements;return t[12]=i[12],t[13]=i[13],t[14]=i[14],this}setFromMatrix3(e){const t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,i){return this.determinant()===0?(e.set(1,0,0),t.set(0,1,0),i.set(0,0,1),this):(e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),i.setFromMatrixColumn(this,2),this)}makeBasis(e,t,i){return this.set(e.x,t.x,i.x,0,e.y,t.y,i.y,0,e.z,t.z,i.z,0,0,0,0,1),this}extractRotation(e){if(e.determinant()===0)return this.identity();const t=this.elements,i=e.elements,r=1/ls.setFromMatrixColumn(e,0).length(),s=1/ls.setFromMatrixColumn(e,1).length(),a=1/ls.setFromMatrixColumn(e,2).length();return t[0]=i[0]*r,t[1]=i[1]*r,t[2]=i[2]*r,t[3]=0,t[4]=i[4]*s,t[5]=i[5]*s,t[6]=i[6]*s,t[7]=0,t[8]=i[8]*a,t[9]=i[9]*a,t[10]=i[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){const t=this.elements,i=e.x,r=e.y,s=e.z,a=Math.cos(i),o=Math.sin(i),l=Math.cos(r),c=Math.sin(r),u=Math.cos(s),f=Math.sin(s);if(e.order==="XYZ"){const h=a*u,d=a*f,g=o*u,m=o*f;t[0]=l*u,t[4]=-l*f,t[8]=c,t[1]=d+g*c,t[5]=h-m*c,t[9]=-o*l,t[2]=m-h*c,t[6]=g+d*c,t[10]=a*l}else if(e.order==="YXZ"){const h=l*u,d=l*f,g=c*u,m=c*f;t[0]=h+m*o,t[4]=g*o-d,t[8]=a*c,t[1]=a*f,t[5]=a*u,t[9]=-o,t[2]=d*o-g,t[6]=m+h*o,t[10]=a*l}else if(e.order==="ZXY"){const h=l*u,d=l*f,g=c*u,m=c*f;t[0]=h-m*o,t[4]=-a*f,t[8]=g+d*o,t[1]=d+g*o,t[5]=a*u,t[9]=m-h*o,t[2]=-a*c,t[6]=o,t[10]=a*l}else if(e.order==="ZYX"){const h=a*u,d=a*f,g=o*u,m=o*f;t[0]=l*u,t[4]=g*c-d,t[8]=h*c+m,t[1]=l*f,t[5]=m*c+h,t[9]=d*c-g,t[2]=-c,t[6]=o*l,t[10]=a*l}else if(e.order==="YZX"){const h=a*l,d=a*c,g=o*l,m=o*c;t[0]=l*u,t[4]=m-h*f,t[8]=g*f+d,t[1]=f,t[5]=a*u,t[9]=-o*u,t[2]=-c*u,t[6]=d*f+g,t[10]=h-m*f}else if(e.order==="XZY"){const h=a*l,d=a*c,g=o*l,m=o*c;t[0]=l*u,t[4]=-f,t[8]=c*u,t[1]=h*f+m,t[5]=a*u,t[9]=d*f-g,t[2]=g*f-d,t[6]=o*u,t[10]=m*f+h}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(hv,e,fv)}lookAt(e,t,i){const r=this.elements;return Nn.subVectors(e,t),Nn.lengthSq()===0&&(Nn.z=1),Nn.normalize(),Ji.crossVectors(i,Nn),Ji.lengthSq()===0&&(Math.abs(i.z)===1?Nn.x+=1e-4:Nn.z+=1e-4,Nn.normalize(),Ji.crossVectors(i,Nn)),Ji.normalize(),uo.crossVectors(Nn,Ji),r[0]=Ji.x,r[4]=uo.x,r[8]=Nn.x,r[1]=Ji.y,r[5]=uo.y,r[9]=Nn.y,r[2]=Ji.z,r[6]=uo.z,r[10]=Nn.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const i=e.elements,r=t.elements,s=this.elements,a=i[0],o=i[4],l=i[8],c=i[12],u=i[1],f=i[5],h=i[9],d=i[13],g=i[2],m=i[6],p=i[10],_=i[14],v=i[3],M=i[7],y=i[11],T=i[15],S=r[0],E=r[4],b=r[8],x=r[12],A=r[1],C=r[5],R=r[9],L=r[13],U=r[2],I=r[6],F=r[10],O=r[14],j=r[3],G=r[7],W=r[11],N=r[15];return s[0]=a*S+o*A+l*U+c*j,s[4]=a*E+o*C+l*I+c*G,s[8]=a*b+o*R+l*F+c*W,s[12]=a*x+o*L+l*O+c*N,s[1]=u*S+f*A+h*U+d*j,s[5]=u*E+f*C+h*I+d*G,s[9]=u*b+f*R+h*F+d*W,s[13]=u*x+f*L+h*O+d*N,s[2]=g*S+m*A+p*U+_*j,s[6]=g*E+m*C+p*I+_*G,s[10]=g*b+m*R+p*F+_*W,s[14]=g*x+m*L+p*O+_*N,s[3]=v*S+M*A+y*U+T*j,s[7]=v*E+M*C+y*I+T*G,s[11]=v*b+M*R+y*F+T*W,s[15]=v*x+M*L+y*O+T*N,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){const e=this.elements,t=e[0],i=e[4],r=e[8],s=e[12],a=e[1],o=e[5],l=e[9],c=e[13],u=e[2],f=e[6],h=e[10],d=e[14],g=e[3],m=e[7],p=e[11],_=e[15],v=l*d-c*h,M=o*d-c*f,y=o*h-l*f,T=a*d-c*u,S=a*h-l*u,E=a*f-o*u;return t*(m*v-p*M+_*y)-i*(g*v-p*T+_*S)+r*(g*M-m*T+_*E)-s*(g*y-m*S+p*E)}transpose(){const e=this.elements;let t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,i){const r=this.elements;return e.isVector3?(r[12]=e.x,r[13]=e.y,r[14]=e.z):(r[12]=e,r[13]=t,r[14]=i),this}invert(){const e=this.elements,t=e[0],i=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8],f=e[9],h=e[10],d=e[11],g=e[12],m=e[13],p=e[14],_=e[15],v=t*o-i*a,M=t*l-r*a,y=t*c-s*a,T=i*l-r*o,S=i*c-s*o,E=r*c-s*l,b=u*m-f*g,x=u*p-h*g,A=u*_-d*g,C=f*p-h*m,R=f*_-d*m,L=h*_-d*p,U=v*L-M*R+y*C+T*A-S*x+E*b;if(U===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const I=1/U;return e[0]=(o*L-l*R+c*C)*I,e[1]=(r*R-i*L-s*C)*I,e[2]=(m*E-p*S+_*T)*I,e[3]=(h*S-f*E-d*T)*I,e[4]=(l*A-a*L-c*x)*I,e[5]=(t*L-r*A+s*x)*I,e[6]=(p*y-g*E-_*M)*I,e[7]=(u*E-h*y+d*M)*I,e[8]=(a*R-o*A+c*b)*I,e[9]=(i*A-t*R-s*b)*I,e[10]=(g*S-m*y+_*v)*I,e[11]=(f*y-u*S-d*v)*I,e[12]=(o*x-a*C-l*b)*I,e[13]=(t*C-i*x+r*b)*I,e[14]=(m*M-g*T-p*v)*I,e[15]=(u*T-f*M+h*v)*I,this}scale(e){const t=this.elements,i=e.x,r=e.y,s=e.z;return t[0]*=i,t[4]*=r,t[8]*=s,t[1]*=i,t[5]*=r,t[9]*=s,t[2]*=i,t[6]*=r,t[10]*=s,t[3]*=i,t[7]*=r,t[11]*=s,this}getMaxScaleOnAxis(){const e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],i=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],r=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,i,r))}makeTranslation(e,t,i){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,i,0,0,0,1),this}makeRotationX(e){const t=Math.cos(e),i=Math.sin(e);return this.set(1,0,0,0,0,t,-i,0,0,i,t,0,0,0,0,1),this}makeRotationY(e){const t=Math.cos(e),i=Math.sin(e);return this.set(t,0,i,0,0,1,0,0,-i,0,t,0,0,0,0,1),this}makeRotationZ(e){const t=Math.cos(e),i=Math.sin(e);return this.set(t,-i,0,0,i,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){const i=Math.cos(t),r=Math.sin(t),s=1-i,a=e.x,o=e.y,l=e.z,c=s*a,u=s*o;return this.set(c*a+i,c*o-r*l,c*l+r*o,0,c*o+r*l,u*o+i,u*l-r*a,0,c*l-r*o,u*l+r*a,s*l*l+i,0,0,0,0,1),this}makeScale(e,t,i){return this.set(e,0,0,0,0,t,0,0,0,0,i,0,0,0,0,1),this}makeShear(e,t,i,r,s,a){return this.set(1,i,s,0,e,1,a,0,t,r,1,0,0,0,0,1),this}compose(e,t,i){const r=this.elements,s=t._x,a=t._y,o=t._z,l=t._w,c=s+s,u=a+a,f=o+o,h=s*c,d=s*u,g=s*f,m=a*u,p=a*f,_=o*f,v=l*c,M=l*u,y=l*f,T=i.x,S=i.y,E=i.z;return r[0]=(1-(m+_))*T,r[1]=(d+y)*T,r[2]=(g-M)*T,r[3]=0,r[4]=(d-y)*S,r[5]=(1-(h+_))*S,r[6]=(p+v)*S,r[7]=0,r[8]=(g+M)*E,r[9]=(p-v)*E,r[10]=(1-(h+m))*E,r[11]=0,r[12]=e.x,r[13]=e.y,r[14]=e.z,r[15]=1,this}decompose(e,t,i){const r=this.elements;e.x=r[12],e.y=r[13],e.z=r[14];const s=this.determinant();if(s===0)return i.set(1,1,1),t.identity(),this;let a=ls.set(r[0],r[1],r[2]).length();const o=ls.set(r[4],r[5],r[6]).length(),l=ls.set(r[8],r[9],r[10]).length();s<0&&(a=-a),si.copy(this);const c=1/a,u=1/o,f=1/l;return si.elements[0]*=c,si.elements[1]*=c,si.elements[2]*=c,si.elements[4]*=u,si.elements[5]*=u,si.elements[6]*=u,si.elements[8]*=f,si.elements[9]*=f,si.elements[10]*=f,t.setFromRotationMatrix(si),i.x=a,i.y=o,i.z=l,this}makePerspective(e,t,i,r,s,a,o=Ti,l=!1){const c=this.elements,u=2*s/(t-e),f=2*s/(i-r),h=(t+e)/(t-e),d=(i+r)/(i-r);let g,m;if(l)g=s/(a-s),m=a*s/(a-s);else if(o===Ti)g=-(a+s)/(a-s),m=-2*a*s/(a-s);else if(o===hl)g=-a/(a-s),m=-a*s/(a-s);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return c[0]=u,c[4]=0,c[8]=h,c[12]=0,c[1]=0,c[5]=f,c[9]=d,c[13]=0,c[2]=0,c[6]=0,c[10]=g,c[14]=m,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,i,r,s,a,o=Ti,l=!1){const c=this.elements,u=2/(t-e),f=2/(i-r),h=-(t+e)/(t-e),d=-(i+r)/(i-r);let g,m;if(l)g=1/(a-s),m=a/(a-s);else if(o===Ti)g=-2/(a-s),m=-(a+s)/(a-s);else if(o===hl)g=-1/(a-s),m=-s/(a-s);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return c[0]=u,c[4]=0,c[8]=0,c[12]=h,c[1]=0,c[5]=f,c[9]=0,c[13]=d,c[2]=0,c[6]=0,c[10]=g,c[14]=m,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){const t=this.elements,i=e.elements;for(let r=0;r<16;r++)if(t[r]!==i[r])return!1;return!0}fromArray(e,t=0){for(let i=0;i<16;i++)this.elements[i]=e[i+t];return this}toArray(e=[],t=0){const i=this.elements;return e[t]=i[0],e[t+1]=i[1],e[t+2]=i[2],e[t+3]=i[3],e[t+4]=i[4],e[t+5]=i[5],e[t+6]=i[6],e[t+7]=i[7],e[t+8]=i[8],e[t+9]=i[9],e[t+10]=i[10],e[t+11]=i[11],e[t+12]=i[12],e[t+13]=i[13],e[t+14]=i[14],e[t+15]=i[15],e}};Dl.prototype.isMatrix4=!0;let kt=Dl;const ls=new X,si=new kt,hv=new X(0,0,0),fv=new X(1,1,1),Ji=new X,uo=new X,Nn=new X,dd=new kt,pd=new _r;class Kr{constructor(e=0,t=0,i=0,r=Kr.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=i,this._order=r}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,i,r=this._order){return this._x=e,this._y=t,this._z=i,this._order=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,i=!0){const r=e.elements,s=r[0],a=r[4],o=r[8],l=r[1],c=r[5],u=r[9],f=r[2],h=r[6],d=r[10];switch(t){case"XYZ":this._y=Math.asin(lt(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-u,d),this._z=Math.atan2(-a,s)):(this._x=Math.atan2(h,c),this._z=0);break;case"YXZ":this._x=Math.asin(-lt(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(o,d),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-f,s),this._z=0);break;case"ZXY":this._x=Math.asin(lt(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(-f,d),this._z=Math.atan2(-a,c)):(this._y=0,this._z=Math.atan2(l,s));break;case"ZYX":this._y=Math.asin(-lt(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(h,d),this._z=Math.atan2(l,s)):(this._x=0,this._z=Math.atan2(-a,c));break;case"YZX":this._z=Math.asin(lt(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-u,c),this._y=Math.atan2(-f,s)):(this._x=0,this._y=Math.atan2(o,d));break;case"XZY":this._z=Math.asin(-lt(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(h,c),this._y=Math.atan2(o,s)):(this._x=Math.atan2(-u,d),this._y=0);break;default:Je("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,i===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,i){return dd.makeRotationFromQuaternion(e),this.setFromRotationMatrix(dd,t,i)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return pd.setFromEuler(this),this.setFromQuaternion(pd,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}Kr.DEFAULT_ORDER="XYZ";class Nm{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let dv=0;const md=new X,cs=new _r,Ui=new kt,ho=new X,da=new X,pv=new X,mv=new _r,gd=new X(1,0,0),_d=new X(0,1,0),vd=new X(0,0,1),xd={type:"added"},gv={type:"removed"},us={type:"childadded",child:null},_c={type:"childremoved",child:null};class mn extends hi{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:dv++}),this.uuid=dr(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=mn.DEFAULT_UP.clone();const e=new X,t=new Kr,i=new _r,r=new X(1,1,1);function s(){i.setFromEuler(t,!1)}function a(){t.setFromQuaternion(i,void 0,!1)}t._onChange(s),i._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:i},scale:{configurable:!0,enumerable:!0,value:r},modelViewMatrix:{value:new kt},normalMatrix:{value:new rt}}),this.matrix=new kt,this.matrixWorld=new kt,this.matrixAutoUpdate=mn.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=mn.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Nm,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return cs.setFromAxisAngle(e,t),this.quaternion.multiply(cs),this}rotateOnWorldAxis(e,t){return cs.setFromAxisAngle(e,t),this.quaternion.premultiply(cs),this}rotateX(e){return this.rotateOnAxis(gd,e)}rotateY(e){return this.rotateOnAxis(_d,e)}rotateZ(e){return this.rotateOnAxis(vd,e)}translateOnAxis(e,t){return md.copy(e).applyQuaternion(this.quaternion),this.position.add(md.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(gd,e)}translateY(e){return this.translateOnAxis(_d,e)}translateZ(e){return this.translateOnAxis(vd,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(Ui.copy(this.matrixWorld).invert())}lookAt(e,t,i){e.isVector3?ho.copy(e):ho.set(e,t,i);const r=this.parent;this.updateWorldMatrix(!0,!1),da.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?Ui.lookAt(da,ho,this.up):Ui.lookAt(ho,da,this.up),this.quaternion.setFromRotationMatrix(Ui),r&&(Ui.extractRotation(r.matrixWorld),cs.setFromRotationMatrix(Ui),this.quaternion.premultiply(cs.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(pt("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(xd),us.child=e,this.dispatchEvent(us),us.child=null):pt("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let i=0;i<arguments.length;i++)this.remove(arguments[i]);return this}const t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(gv),_c.child=e,this.dispatchEvent(_c),_c.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),Ui.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),Ui.multiply(e.parent.matrixWorld)),e.applyMatrix4(Ui),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(xd),us.child=e,this.dispatchEvent(us),us.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let i=0,r=this.children.length;i<r;i++){const a=this.children[i].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,i=[]){this[e]===t&&i.push(this);const r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].getObjectsByProperty(e,t,i);return i}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(da,e,pv),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(da,mv,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}traverse(e){e(this);const t=this.children;for(let i=0,r=t.length;i<r;i++)t[i].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const t=this.children;for(let i=0,r=t.length;i<r;i++)t[i].traverseVisible(e)}traverseAncestors(e){const t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);const e=this.pivot;if(e!==null){const t=e.x,i=e.y,r=e.z,s=this.matrix.elements;s[12]+=t-s[0]*t-s[4]*i-s[8]*r,s[13]+=i-s[1]*t-s[5]*i-s[9]*r,s[14]+=r-s[2]*t-s[6]*i-s[10]*r}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const t=this.children;for(let i=0,r=t.length;i<r;i++)t[i].updateMatrixWorld(e)}updateWorldMatrix(e,t){const i=this.parent;if(e===!0&&i!==null&&i.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),t===!0){const r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].updateWorldMatrix(!1,!0)}}toJSON(e){const t=e===void 0||typeof e=="string",i={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},i.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});const r={};r.uuid=this.uuid,r.type=this.type,this.name!==""&&(r.name=this.name),this.castShadow===!0&&(r.castShadow=!0),this.receiveShadow===!0&&(r.receiveShadow=!0),this.visible===!1&&(r.visible=!1),this.frustumCulled===!1&&(r.frustumCulled=!1),this.renderOrder!==0&&(r.renderOrder=this.renderOrder),this.static!==!1&&(r.static=this.static),Object.keys(this.userData).length>0&&(r.userData=this.userData),r.layers=this.layers.mask,r.matrix=this.matrix.toArray(),r.up=this.up.toArray(),this.pivot!==null&&(r.pivot=this.pivot.toArray()),this.matrixAutoUpdate===!1&&(r.matrixAutoUpdate=!1),this.morphTargetDictionary!==void 0&&(r.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(r.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(r.type="InstancedMesh",r.count=this.count,r.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(r.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(r.type="BatchedMesh",r.perObjectFrustumCulled=this.perObjectFrustumCulled,r.sortObjects=this.sortObjects,r.drawRanges=this._drawRanges,r.reservedRanges=this._reservedRanges,r.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),r.instanceInfo=this._instanceInfo.map(o=>({...o})),r.availableInstanceIds=this._availableInstanceIds.slice(),r.availableGeometryIds=this._availableGeometryIds.slice(),r.nextIndexStart=this._nextIndexStart,r.nextVertexStart=this._nextVertexStart,r.geometryCount=this._geometryCount,r.maxInstanceCount=this._maxInstanceCount,r.maxVertexCount=this._maxVertexCount,r.maxIndexCount=this._maxIndexCount,r.geometryInitialized=this._geometryInitialized,r.matricesTexture=this._matricesTexture.toJSON(e),r.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(r.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(r.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(r.boundingBox=this.boundingBox.toJSON()));function s(o,l){return o[l.uuid]===void 0&&(o[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?r.background=this.background.toJSON():this.background.isTexture&&(r.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(r.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){r.geometry=s(e.geometries,this.geometry);const o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){const l=o.shapes;if(Array.isArray(l))for(let c=0,u=l.length;c<u;c++){const f=l[c];s(e.shapes,f)}else s(e.shapes,l)}}if(this.isSkinnedMesh&&(r.bindMode=this.bindMode,r.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(s(e.skeletons,this.skeleton),r.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const o=[];for(let l=0,c=this.material.length;l<c;l++)o.push(s(e.materials,this.material[l]));r.material=o}else r.material=s(e.materials,this.material);if(this.children.length>0){r.children=[];for(let o=0;o<this.children.length;o++)r.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){r.animations=[];for(let o=0;o<this.animations.length;o++){const l=this.animations[o];r.animations.push(s(e.animations,l))}}if(t){const o=a(e.geometries),l=a(e.materials),c=a(e.textures),u=a(e.images),f=a(e.shapes),h=a(e.skeletons),d=a(e.animations),g=a(e.nodes);o.length>0&&(i.geometries=o),l.length>0&&(i.materials=l),c.length>0&&(i.textures=c),u.length>0&&(i.images=u),f.length>0&&(i.shapes=f),h.length>0&&(i.skeletons=h),d.length>0&&(i.animations=d),g.length>0&&(i.nodes=g)}return i.object=r,i;function a(o){const l=[];for(const c in o){const u=o[c];delete u.metadata,l.push(u)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let i=0;i<e.children.length;i++){const r=e.children[i];this.add(r.clone())}return this}}mn.DEFAULT_UP=new X(0,1,0);mn.DEFAULT_MATRIX_AUTO_UPDATE=!0;mn.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;class Rs extends mn{constructor(){super(),this.isGroup=!0,this.type="Group"}}const _v={type:"move"};class vc{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new Rs,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new Rs,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new X,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new X),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new Rs,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new X,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new X,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const t=this._hand;if(t)for(const i of e.hand.values())this._getHandJoint(t,i)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,i){let r=null,s=null,a=null;const o=this._targetRay,l=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){a=!0;for(const m of e.hand.values()){const p=t.getJointPose(m,i),_=this._getHandJoint(c,m);p!==null&&(_.matrix.fromArray(p.transform.matrix),_.matrix.decompose(_.position,_.rotation,_.scale),_.matrixWorldNeedsUpdate=!0,_.jointRadius=p.radius),_.visible=p!==null}const u=c.joints["index-finger-tip"],f=c.joints["thumb-tip"],h=u.position.distanceTo(f.position),d=.02,g=.005;c.inputState.pinching&&h>d+g?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&h<=d-g&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(s=t.getPose(e.gripSpace,i),s!==null&&(l.matrix.fromArray(s.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,s.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(s.linearVelocity)):l.hasLinearVelocity=!1,s.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(s.angularVelocity)):l.hasAngularVelocity=!1,l.eventsEnabled&&l.dispatchEvent({type:"gripUpdated",data:e,target:this})));o!==null&&(r=t.getPose(e.targetRaySpace,i),r===null&&s!==null&&(r=s),r!==null&&(o.matrix.fromArray(r.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,r.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(r.linearVelocity)):o.hasLinearVelocity=!1,r.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(r.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(_v)))}return o!==null&&(o.visible=r!==null),l!==null&&(l.visible=s!==null),c!==null&&(c.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){const i=new Rs;i.matrixAutoUpdate=!1,i.visible=!1,e.joints[t.jointName]=i,e.add(i)}return e.joints[t.jointName]}}const Om={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},Qi={h:0,s:0,l:0},fo={h:0,s:0,l:0};function xc(n,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?n+(e-n)*6*t:t<1/2?e:t<2/3?n+(e-n)*6*(2/3-t):n}class ut{constructor(e,t,i){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,i)}set(e,t,i){if(t===void 0&&i===void 0){const r=e;r&&r.isColor?this.copy(r):typeof r=="number"?this.setHex(r):typeof r=="string"&&this.setStyle(r)}else this.setRGB(e,t,i);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=Tt){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,ft.colorSpaceToWorking(this,t),this}setRGB(e,t,i,r=ft.workingColorSpace){return this.r=e,this.g=t,this.b=i,ft.colorSpaceToWorking(this,r),this}setHSL(e,t,i,r=ft.workingColorSpace){if(e=iv(e,1),t=lt(t,0,1),i=lt(i,0,1),t===0)this.r=this.g=this.b=i;else{const s=i<=.5?i*(1+t):i+t-i*t,a=2*i-s;this.r=xc(a,s,e+1/3),this.g=xc(a,s,e),this.b=xc(a,s,e-1/3)}return ft.colorSpaceToWorking(this,r),this}setStyle(e,t=Tt){function i(s){s!==void 0&&parseFloat(s)<1&&Je("Color: Alpha component of "+e+" will be ignored.")}let r;if(r=/^(\w+)\(([^\)]*)\)/.exec(e)){let s;const a=r[1],o=r[2];switch(a){case"rgb":case"rgba":if(s=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return i(s[4]),this.setRGB(Math.min(255,parseInt(s[1],10))/255,Math.min(255,parseInt(s[2],10))/255,Math.min(255,parseInt(s[3],10))/255,t);if(s=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return i(s[4]),this.setRGB(Math.min(100,parseInt(s[1],10))/100,Math.min(100,parseInt(s[2],10))/100,Math.min(100,parseInt(s[3],10))/100,t);break;case"hsl":case"hsla":if(s=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return i(s[4]),this.setHSL(parseFloat(s[1])/360,parseFloat(s[2])/100,parseFloat(s[3])/100,t);break;default:Je("Color: Unknown color model "+e)}}else if(r=/^\#([A-Fa-f\d]+)$/.exec(e)){const s=r[1],a=s.length;if(a===3)return this.setRGB(parseInt(s.charAt(0),16)/15,parseInt(s.charAt(1),16)/15,parseInt(s.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(s,16),t);Je("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=Tt){const i=Om[e.toLowerCase()];return i!==void 0?this.setHex(i,t):Je("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=zi(e.r),this.g=zi(e.g),this.b=zi(e.b),this}copyLinearToSRGB(e){return this.r=Us(e.r),this.g=Us(e.g),this.b=Us(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=Tt){return ft.workingToColorSpace(dn.copy(this),e),Math.round(lt(dn.r*255,0,255))*65536+Math.round(lt(dn.g*255,0,255))*256+Math.round(lt(dn.b*255,0,255))}getHexString(e=Tt){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=ft.workingColorSpace){ft.workingToColorSpace(dn.copy(this),t);const i=dn.r,r=dn.g,s=dn.b,a=Math.max(i,r,s),o=Math.min(i,r,s);let l,c;const u=(o+a)/2;if(o===a)l=0,c=0;else{const f=a-o;switch(c=u<=.5?f/(a+o):f/(2-a-o),a){case i:l=(r-s)/f+(r<s?6:0);break;case r:l=(s-i)/f+2;break;case s:l=(i-r)/f+4;break}l/=6}return e.h=l,e.s=c,e.l=u,e}getRGB(e,t=ft.workingColorSpace){return ft.workingToColorSpace(dn.copy(this),t),e.r=dn.r,e.g=dn.g,e.b=dn.b,e}getStyle(e=Tt){ft.workingToColorSpace(dn.copy(this),e);const t=dn.r,i=dn.g,r=dn.b;return e!==Tt?`color(${e} ${t.toFixed(3)} ${i.toFixed(3)} ${r.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(i*255)},${Math.round(r*255)})`}offsetHSL(e,t,i){return this.getHSL(Qi),this.setHSL(Qi.h+e,Qi.s+t,Qi.l+i)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,i){return this.r=e.r+(t.r-e.r)*i,this.g=e.g+(t.g-e.g)*i,this.b=e.b+(t.b-e.b)*i,this}lerpHSL(e,t){this.getHSL(Qi),e.getHSL(fo);const i=fc(Qi.h,fo.h,t),r=fc(Qi.s,fo.s,t),s=fc(Qi.l,fo.l,t);return this.setHSL(i,r,s),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const t=this.r,i=this.g,r=this.b,s=e.elements;return this.r=s[0]*t+s[3]*i+s[6]*r,this.g=s[1]*t+s[4]*i+s[7]*r,this.b=s[2]*t+s[5]*i+s[8]*r,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const dn=new ut;ut.NAMES=Om;class gh extends mn{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new Kr,this.environmentIntensity=1,this.environmentRotation=new Kr,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(t.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(t.object.backgroundIntensity=this.backgroundIntensity),t.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(t.object.environmentIntensity=this.environmentIntensity),t.object.environmentRotation=this.environmentRotation.toArray(),t}}const ai=new X,Li=new X,bc=new X,Ii=new X,hs=new X,fs=new X,bd=new X,Mc=new X,Sc=new X,yc=new X,Tc=new Dt,Ec=new Dt,wc=new Dt;class $n{constructor(e=new X,t=new X,i=new X){this.a=e,this.b=t,this.c=i}static getNormal(e,t,i,r){r.subVectors(i,t),ai.subVectors(e,t),r.cross(ai);const s=r.lengthSq();return s>0?r.multiplyScalar(1/Math.sqrt(s)):r.set(0,0,0)}static getBarycoord(e,t,i,r,s){ai.subVectors(r,t),Li.subVectors(i,t),bc.subVectors(e,t);const a=ai.dot(ai),o=ai.dot(Li),l=ai.dot(bc),c=Li.dot(Li),u=Li.dot(bc),f=a*c-o*o;if(f===0)return s.set(0,0,0),null;const h=1/f,d=(c*l-o*u)*h,g=(a*u-o*l)*h;return s.set(1-d-g,g,d)}static containsPoint(e,t,i,r){return this.getBarycoord(e,t,i,r,Ii)===null?!1:Ii.x>=0&&Ii.y>=0&&Ii.x+Ii.y<=1}static getInterpolation(e,t,i,r,s,a,o,l){return this.getBarycoord(e,t,i,r,Ii)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(s,Ii.x),l.addScaledVector(a,Ii.y),l.addScaledVector(o,Ii.z),l)}static getInterpolatedAttribute(e,t,i,r,s,a){return Tc.setScalar(0),Ec.setScalar(0),wc.setScalar(0),Tc.fromBufferAttribute(e,t),Ec.fromBufferAttribute(e,i),wc.fromBufferAttribute(e,r),a.setScalar(0),a.addScaledVector(Tc,s.x),a.addScaledVector(Ec,s.y),a.addScaledVector(wc,s.z),a}static isFrontFacing(e,t,i,r){return ai.subVectors(i,t),Li.subVectors(e,t),ai.cross(Li).dot(r)<0}set(e,t,i){return this.a.copy(e),this.b.copy(t),this.c.copy(i),this}setFromPointsAndIndices(e,t,i,r){return this.a.copy(e[t]),this.b.copy(e[i]),this.c.copy(e[r]),this}setFromAttributeAndIndices(e,t,i,r){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,i),this.c.fromBufferAttribute(e,r),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return ai.subVectors(this.c,this.b),Li.subVectors(this.a,this.b),ai.cross(Li).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return $n.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return $n.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,i,r,s){return $n.getInterpolation(e,this.a,this.b,this.c,t,i,r,s)}containsPoint(e){return $n.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return $n.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){const i=this.a,r=this.b,s=this.c;let a,o;hs.subVectors(r,i),fs.subVectors(s,i),Mc.subVectors(e,i);const l=hs.dot(Mc),c=fs.dot(Mc);if(l<=0&&c<=0)return t.copy(i);Sc.subVectors(e,r);const u=hs.dot(Sc),f=fs.dot(Sc);if(u>=0&&f<=u)return t.copy(r);const h=l*f-u*c;if(h<=0&&l>=0&&u<=0)return a=l/(l-u),t.copy(i).addScaledVector(hs,a);yc.subVectors(e,s);const d=hs.dot(yc),g=fs.dot(yc);if(g>=0&&d<=g)return t.copy(s);const m=d*c-l*g;if(m<=0&&c>=0&&g<=0)return o=c/(c-g),t.copy(i).addScaledVector(fs,o);const p=u*g-d*f;if(p<=0&&f-u>=0&&d-g>=0)return bd.subVectors(s,r),o=(f-u)/(f-u+(d-g)),t.copy(r).addScaledVector(bd,o);const _=1/(p+m+h);return a=m*_,o=h*_,t.copy(i).addScaledVector(hs,a).addScaledVector(fs,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}class qs{constructor(e=new X(1/0,1/0,1/0),t=new X(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,i=e.length;t<i;t+=3)this.expandByPoint(oi.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,i=e.count;t<i;t++)this.expandByPoint(oi.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,i=e.length;t<i;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){const i=oi.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(i),this.max.copy(e).add(i),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);const i=e.geometry;if(i!==void 0){const s=i.getAttribute("position");if(t===!0&&s!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=s.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,oi):oi.fromBufferAttribute(s,a),oi.applyMatrix4(e.matrixWorld),this.expandByPoint(oi);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),po.copy(e.boundingBox)):(i.boundingBox===null&&i.computeBoundingBox(),po.copy(i.boundingBox)),po.applyMatrix4(e.matrixWorld),this.union(po)}const r=e.children;for(let s=0,a=r.length;s<a;s++)this.expandByObject(r[s],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,oi),oi.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,i;return e.normal.x>0?(t=e.normal.x*this.min.x,i=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,i=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,i+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,i+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,i+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,i+=e.normal.z*this.min.z),t<=-e.constant&&i>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(pa),mo.subVectors(this.max,pa),ds.subVectors(e.a,pa),ps.subVectors(e.b,pa),ms.subVectors(e.c,pa),er.subVectors(ps,ds),tr.subVectors(ms,ps),wr.subVectors(ds,ms);let t=[0,-er.z,er.y,0,-tr.z,tr.y,0,-wr.z,wr.y,er.z,0,-er.x,tr.z,0,-tr.x,wr.z,0,-wr.x,-er.y,er.x,0,-tr.y,tr.x,0,-wr.y,wr.x,0];return!Ac(t,ds,ps,ms,mo)||(t=[1,0,0,0,1,0,0,0,1],!Ac(t,ds,ps,ms,mo))?!1:(go.crossVectors(er,tr),t=[go.x,go.y,go.z],Ac(t,ds,ps,ms,mo))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,oi).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(oi).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(Fi[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),Fi[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),Fi[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),Fi[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),Fi[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),Fi[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),Fi[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),Fi[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(Fi),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}const Fi=[new X,new X,new X,new X,new X,new X,new X,new X],oi=new X,po=new qs,ds=new X,ps=new X,ms=new X,er=new X,tr=new X,wr=new X,pa=new X,mo=new X,go=new X,Ar=new X;function Ac(n,e,t,i,r){for(let s=0,a=n.length-3;s<=a;s+=3){Ar.fromArray(n,s);const o=r.x*Math.abs(Ar.x)+r.y*Math.abs(Ar.y)+r.z*Math.abs(Ar.z),l=e.dot(Ar),c=t.dot(Ar),u=i.dot(Ar);if(Math.max(-Math.max(l,c,u),Math.min(l,c,u))>o)return!1}return!0}const Wt=new X,_o=new Xe;let vv=0;class Ft extends hi{constructor(e,t,i=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:vv++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=i,this.usage=dh,this.updateRanges=[],this.gpuType=li,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,i){e*=this.itemSize,i*=t.itemSize;for(let r=0,s=this.itemSize;r<s;r++)this.array[e+r]=t.array[i+r];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,i=this.count;t<i;t++)_o.fromBufferAttribute(this,t),_o.applyMatrix3(e),this.setXY(t,_o.x,_o.y);else if(this.itemSize===3)for(let t=0,i=this.count;t<i;t++)Wt.fromBufferAttribute(this,t),Wt.applyMatrix3(e),this.setXYZ(t,Wt.x,Wt.y,Wt.z);return this}applyMatrix4(e){for(let t=0,i=this.count;t<i;t++)Wt.fromBufferAttribute(this,t),Wt.applyMatrix4(e),this.setXYZ(t,Wt.x,Wt.y,Wt.z);return this}applyNormalMatrix(e){for(let t=0,i=this.count;t<i;t++)Wt.fromBufferAttribute(this,t),Wt.applyNormalMatrix(e),this.setXYZ(t,Wt.x,Wt.y,Wt.z);return this}transformDirection(e){for(let t=0,i=this.count;t<i;t++)Wt.fromBufferAttribute(this,t),Wt.transformDirection(e),this.setXYZ(t,Wt.x,Wt.y,Wt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let i=this.array[e*this.itemSize+t];return this.normalized&&(i=Mi(i,this.array)),i}setComponent(e,t,i){return this.normalized&&(i=St(i,this.array)),this.array[e*this.itemSize+t]=i,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=Mi(t,this.array)),t}setX(e,t){return this.normalized&&(t=St(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=Mi(t,this.array)),t}setY(e,t){return this.normalized&&(t=St(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=Mi(t,this.array)),t}setZ(e,t){return this.normalized&&(t=St(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=Mi(t,this.array)),t}setW(e,t){return this.normalized&&(t=St(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,i){return e*=this.itemSize,this.normalized&&(t=St(t,this.array),i=St(i,this.array)),this.array[e+0]=t,this.array[e+1]=i,this}setXYZ(e,t,i,r){return e*=this.itemSize,this.normalized&&(t=St(t,this.array),i=St(i,this.array),r=St(r,this.array)),this.array[e+0]=t,this.array[e+1]=i,this.array[e+2]=r,this}setXYZW(e,t,i,r,s){return e*=this.itemSize,this.normalized&&(t=St(t,this.array),i=St(i,this.array),r=St(r,this.array),s=St(s,this.array)),this.array[e+0]=t,this.array[e+1]=i,this.array[e+2]=r,this.array[e+3]=s,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==dh&&(e.usage=this.usage),e}dispose(){this.dispatchEvent({type:"dispose"})}}class Bm extends Ft{constructor(e,t,i){super(new Uint16Array(e),t,i)}}class km extends Ft{constructor(e,t,i){super(new Uint32Array(e),t,i)}}class ui extends Ft{constructor(e,t,i){super(new Float32Array(e),t,i)}}const xv=new qs,ma=new X,Rc=new X;class Ks{constructor(e=new X,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){const i=this.center;t!==void 0?i.copy(t):xv.setFromPoints(e).getCenter(i);let r=0;for(let s=0,a=e.length;s<a;s++)r=Math.max(r,i.distanceToSquared(e[s]));return this.radius=Math.sqrt(r),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){const i=this.center.distanceToSquared(e);return t.copy(e),i>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;ma.subVectors(e,this.center);const t=ma.lengthSq();if(t>this.radius*this.radius){const i=Math.sqrt(t),r=(i-this.radius)*.5;this.center.addScaledVector(ma,r/i),this.radius+=r}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Rc.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(ma.copy(e.center).add(Rc)),this.expandByPoint(ma.copy(e.center).sub(Rc))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}let bv=0;const Kn=new kt,Cc=new mn,gs=new X,On=new qs,ga=new qs,nn=new X;class At extends hi{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:bv++}),this.uuid=dr(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(Q_(e)?km:Bm)(e,1):this.index=e,this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,i=0){this.groups.push({start:e,count:t,materialIndex:i})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){const t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);const i=this.attributes.normal;if(i!==void 0){const s=new rt().getNormalMatrix(e);i.applyNormalMatrix(s),i.needsUpdate=!0}const r=this.attributes.tangent;return r!==void 0&&(r.transformDirection(e),r.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return Kn.makeRotationFromQuaternion(e),this.applyMatrix4(Kn),this}rotateX(e){return Kn.makeRotationX(e),this.applyMatrix4(Kn),this}rotateY(e){return Kn.makeRotationY(e),this.applyMatrix4(Kn),this}rotateZ(e){return Kn.makeRotationZ(e),this.applyMatrix4(Kn),this}translate(e,t,i){return Kn.makeTranslation(e,t,i),this.applyMatrix4(Kn),this}scale(e,t,i){return Kn.makeScale(e,t,i),this.applyMatrix4(Kn),this}lookAt(e){return Cc.lookAt(e),Cc.updateMatrix(),this.applyMatrix4(Cc.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(gs).negate(),this.translate(gs.x,gs.y,gs.z),this}setFromPoints(e){const t=this.getAttribute("position");if(t===void 0){const i=[];for(let r=0,s=e.length;r<s;r++){const a=e[r];i.push(a.x,a.y,a.z||0)}this.setAttribute("position",new ui(i,3))}else{const i=Math.min(e.length,t.count);for(let r=0;r<i;r++){const s=e[r];t.setXYZ(r,s.x,s.y,s.z||0)}e.length>t.count&&Je("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new qs);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){pt("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new X(-1/0,-1/0,-1/0),new X(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let i=0,r=t.length;i<r;i++){const s=t[i];On.setFromBufferAttribute(s),this.morphTargetsRelative?(nn.addVectors(this.boundingBox.min,On.min),this.boundingBox.expandByPoint(nn),nn.addVectors(this.boundingBox.max,On.max),this.boundingBox.expandByPoint(nn)):(this.boundingBox.expandByPoint(On.min),this.boundingBox.expandByPoint(On.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&pt('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Ks);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){pt("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new X,1/0);return}if(e){const i=this.boundingSphere.center;if(On.setFromBufferAttribute(e),t)for(let s=0,a=t.length;s<a;s++){const o=t[s];ga.setFromBufferAttribute(o),this.morphTargetsRelative?(nn.addVectors(On.min,ga.min),On.expandByPoint(nn),nn.addVectors(On.max,ga.max),On.expandByPoint(nn)):(On.expandByPoint(ga.min),On.expandByPoint(ga.max))}On.getCenter(i);let r=0;for(let s=0,a=e.count;s<a;s++)nn.fromBufferAttribute(e,s),r=Math.max(r,i.distanceToSquared(nn));if(t)for(let s=0,a=t.length;s<a;s++){const o=t[s],l=this.morphTargetsRelative;for(let c=0,u=o.count;c<u;c++)nn.fromBufferAttribute(o,c),l&&(gs.fromBufferAttribute(e,c),nn.add(gs)),r=Math.max(r,i.distanceToSquared(nn))}this.boundingSphere.radius=Math.sqrt(r),isNaN(this.boundingSphere.radius)&&pt('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){pt("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const i=t.position,r=t.normal,s=t.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new Ft(new Float32Array(4*i.count),4));const a=this.getAttribute("tangent"),o=[],l=[];for(let b=0;b<i.count;b++)o[b]=new X,l[b]=new X;const c=new X,u=new X,f=new X,h=new Xe,d=new Xe,g=new Xe,m=new X,p=new X;function _(b,x,A){c.fromBufferAttribute(i,b),u.fromBufferAttribute(i,x),f.fromBufferAttribute(i,A),h.fromBufferAttribute(s,b),d.fromBufferAttribute(s,x),g.fromBufferAttribute(s,A),u.sub(c),f.sub(c),d.sub(h),g.sub(h);const C=1/(d.x*g.y-g.x*d.y);isFinite(C)&&(m.copy(u).multiplyScalar(g.y).addScaledVector(f,-d.y).multiplyScalar(C),p.copy(f).multiplyScalar(d.x).addScaledVector(u,-g.x).multiplyScalar(C),o[b].add(m),o[x].add(m),o[A].add(m),l[b].add(p),l[x].add(p),l[A].add(p))}let v=this.groups;v.length===0&&(v=[{start:0,count:e.count}]);for(let b=0,x=v.length;b<x;++b){const A=v[b],C=A.start,R=A.count;for(let L=C,U=C+R;L<U;L+=3)_(e.getX(L+0),e.getX(L+1),e.getX(L+2))}const M=new X,y=new X,T=new X,S=new X;function E(b){T.fromBufferAttribute(r,b),S.copy(T);const x=o[b];M.copy(x),M.sub(T.multiplyScalar(T.dot(x))).normalize(),y.crossVectors(S,x);const C=y.dot(l[b])<0?-1:1;a.setXYZW(b,M.x,M.y,M.z,C)}for(let b=0,x=v.length;b<x;++b){const A=v[b],C=A.start,R=A.count;for(let L=C,U=C+R;L<U;L+=3)E(e.getX(L+0)),E(e.getX(L+1)),E(e.getX(L+2))}}computeVertexNormals(){const e=this.index,t=this.getAttribute("position");if(t!==void 0){let i=this.getAttribute("normal");if(i===void 0)i=new Ft(new Float32Array(t.count*3),3),this.setAttribute("normal",i);else for(let h=0,d=i.count;h<d;h++)i.setXYZ(h,0,0,0);const r=new X,s=new X,a=new X,o=new X,l=new X,c=new X,u=new X,f=new X;if(e)for(let h=0,d=e.count;h<d;h+=3){const g=e.getX(h+0),m=e.getX(h+1),p=e.getX(h+2);r.fromBufferAttribute(t,g),s.fromBufferAttribute(t,m),a.fromBufferAttribute(t,p),u.subVectors(a,s),f.subVectors(r,s),u.cross(f),o.fromBufferAttribute(i,g),l.fromBufferAttribute(i,m),c.fromBufferAttribute(i,p),o.add(u),l.add(u),c.add(u),i.setXYZ(g,o.x,o.y,o.z),i.setXYZ(m,l.x,l.y,l.z),i.setXYZ(p,c.x,c.y,c.z)}else for(let h=0,d=t.count;h<d;h+=3)r.fromBufferAttribute(t,h+0),s.fromBufferAttribute(t,h+1),a.fromBufferAttribute(t,h+2),u.subVectors(a,s),f.subVectors(r,s),u.cross(f),i.setXYZ(h+0,u.x,u.y,u.z),i.setXYZ(h+1,u.x,u.y,u.z),i.setXYZ(h+2,u.x,u.y,u.z);this.normalizeNormals(),i.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let t=0,i=e.count;t<i;t++)nn.fromBufferAttribute(e,t),nn.normalize(),e.setXYZ(t,nn.x,nn.y,nn.z)}toNonIndexed(){function e(o,l){const c=o.array,u=o.itemSize,f=o.normalized,h=new c.constructor(l.length*u);let d=0,g=0;for(let m=0,p=l.length;m<p;m++){o.isInterleavedBufferAttribute?d=l[m]*o.data.stride+o.offset:d=l[m]*u;for(let _=0;_<u;_++)h[g++]=c[d++]}return new Ft(h,u,f)}if(this.index===null)return Je("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const t=new At,i=this.index.array,r=this.attributes;for(const o in r){const l=r[o],c=e(l,i);t.setAttribute(o,c)}const s=this.morphAttributes;for(const o in s){const l=[],c=s[o];for(let u=0,f=c.length;u<f;u++){const h=c[u],d=e(h,i);l.push(d)}t.morphAttributes[o]=l}t.morphTargetsRelative=this.morphTargetsRelative;const a=this.groups;for(let o=0,l=a.length;o<l;o++){const c=a[o];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){const e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){const l=this.parameters;for(const c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};const t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});const i=this.attributes;for(const l in i){const c=i[l];e.data.attributes[l]=c.toJSON(e.data)}const r={};let s=!1;for(const l in this.morphAttributes){const c=this.morphAttributes[l],u=[];for(let f=0,h=c.length;f<h;f++){const d=c[f];u.push(d.toJSON(e.data))}u.length>0&&(r[l]=u,s=!0)}s&&(e.data.morphAttributes=r,e.data.morphTargetsRelative=this.morphTargetsRelative);const a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));const o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const t={};this.name=e.name;const i=e.index;i!==null&&this.setIndex(i.clone());const r=e.attributes;for(const c in r){const u=r[c];this.setAttribute(c,u.clone(t))}const s=e.morphAttributes;for(const c in s){const u=[],f=s[c];for(let h=0,d=f.length;h<d;h++)u.push(f[h].clone(t));this.morphAttributes[c]=u}this.morphTargetsRelative=e.morphTargetsRelative;const a=e.groups;for(let c=0,u=a.length;c<u;c++){const f=a[c];this.addGroup(f.start,f.count,f.materialIndex)}const o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());const l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}}class Mv{constructor(e,t){this.isInterleavedBuffer=!0,this.array=e,this.stride=t,this.count=e!==void 0?e.length/t:0,this.usage=dh,this.updateRanges=[],this.version=0,this.uuid=dr()}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.array=new e.array.constructor(e.array),this.count=e.count,this.stride=e.stride,this.usage=e.usage,this}copyAt(e,t,i){e*=this.stride,i*=t.stride;for(let r=0,s=this.stride;r<s;r++)this.array[e+r]=t.array[i+r];return this}set(e,t=0){return this.array.set(e,t),this}clone(e){e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=dr()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer);const t=new this.array.constructor(e.arrayBuffers[this.array.buffer._uuid]),i=new this.constructor(t,this.stride);return i.setUsage(this.usage),i}onUpload(e){return this.onUploadCallback=e,this}toJSON(e){return e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=dr()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer))),{uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride}}}const xn=new X;class pl{constructor(e,t,i,r=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=e,this.itemSize=t,this.offset=i,this.normalized=r}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(e){this.data.needsUpdate=e}applyMatrix4(e){for(let t=0,i=this.data.count;t<i;t++)xn.fromBufferAttribute(this,t),xn.applyMatrix4(e),this.setXYZ(t,xn.x,xn.y,xn.z);return this}applyNormalMatrix(e){for(let t=0,i=this.count;t<i;t++)xn.fromBufferAttribute(this,t),xn.applyNormalMatrix(e),this.setXYZ(t,xn.x,xn.y,xn.z);return this}transformDirection(e){for(let t=0,i=this.count;t<i;t++)xn.fromBufferAttribute(this,t),xn.transformDirection(e),this.setXYZ(t,xn.x,xn.y,xn.z);return this}getComponent(e,t){let i=this.array[e*this.data.stride+this.offset+t];return this.normalized&&(i=Mi(i,this.array)),i}setComponent(e,t,i){return this.normalized&&(i=St(i,this.array)),this.data.array[e*this.data.stride+this.offset+t]=i,this}setX(e,t){return this.normalized&&(t=St(t,this.array)),this.data.array[e*this.data.stride+this.offset]=t,this}setY(e,t){return this.normalized&&(t=St(t,this.array)),this.data.array[e*this.data.stride+this.offset+1]=t,this}setZ(e,t){return this.normalized&&(t=St(t,this.array)),this.data.array[e*this.data.stride+this.offset+2]=t,this}setW(e,t){return this.normalized&&(t=St(t,this.array)),this.data.array[e*this.data.stride+this.offset+3]=t,this}getX(e){let t=this.data.array[e*this.data.stride+this.offset];return this.normalized&&(t=Mi(t,this.array)),t}getY(e){let t=this.data.array[e*this.data.stride+this.offset+1];return this.normalized&&(t=Mi(t,this.array)),t}getZ(e){let t=this.data.array[e*this.data.stride+this.offset+2];return this.normalized&&(t=Mi(t,this.array)),t}getW(e){let t=this.data.array[e*this.data.stride+this.offset+3];return this.normalized&&(t=Mi(t,this.array)),t}setXY(e,t,i){return e=e*this.data.stride+this.offset,this.normalized&&(t=St(t,this.array),i=St(i,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=i,this}setXYZ(e,t,i,r){return e=e*this.data.stride+this.offset,this.normalized&&(t=St(t,this.array),i=St(i,this.array),r=St(r,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=i,this.data.array[e+2]=r,this}setXYZW(e,t,i,r,s){return e=e*this.data.stride+this.offset,this.normalized&&(t=St(t,this.array),i=St(i,this.array),r=St(r,this.array),s=St(s,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=i,this.data.array[e+2]=r,this.data.array[e+3]=s,this}clone(e){if(e===void 0){dl("InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");const t=[];for(let i=0;i<this.count;i++){const r=i*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return new Ft(new this.array.constructor(t),this.itemSize,this.normalized)}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.clone(e)),new pl(e.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}toJSON(e){if(e===void 0){dl("InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");const t=[];for(let i=0;i<this.count;i++){const r=i*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:t,normalized:this.normalized}}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.toJSON(e)),{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}}let Sv=0;class Yi extends hi{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Sv++}),this.uuid=dr(),this.name="",this.type="Material",this.blending=kr,this.side=Hi,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Au,this.blendDst=Ru,this.blendEquation=Fr,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new ut(0,0,0),this.blendAlpha=0,this.depthFunc=Os,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=od,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=as,this.stencilZFail=as,this.stencilZPass=as,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const t in e){const i=e[t];if(i===void 0){Je(`Material: parameter '${t}' has value of undefined.`);continue}const r=this[t];if(r===void 0){Je(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}r&&r.isColor?r.set(i):r&&r.isVector3&&i&&i.isVector3?r.copy(i):this[t]=i}}toJSON(e){const t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});const i={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};i.uuid=this.uuid,i.type=this.type,this.name!==""&&(i.name=this.name),this.color&&this.color.isColor&&(i.color=this.color.getHex()),this.roughness!==void 0&&(i.roughness=this.roughness),this.metalness!==void 0&&(i.metalness=this.metalness),this.sheen!==void 0&&(i.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(i.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(i.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(i.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(i.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(i.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(i.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(i.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(i.shininess=this.shininess),this.clearcoat!==void 0&&(i.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(i.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(i.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(i.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(i.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,i.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(i.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(i.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(i.dispersion=this.dispersion),this.iridescence!==void 0&&(i.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(i.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(i.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(i.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(i.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(i.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(i.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(i.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(i.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(i.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(i.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(i.lightMap=this.lightMap.toJSON(e).uuid,i.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(i.aoMap=this.aoMap.toJSON(e).uuid,i.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(i.bumpMap=this.bumpMap.toJSON(e).uuid,i.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(i.normalMap=this.normalMap.toJSON(e).uuid,i.normalMapType=this.normalMapType,i.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(i.displacementMap=this.displacementMap.toJSON(e).uuid,i.displacementScale=this.displacementScale,i.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(i.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(i.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(i.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(i.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(i.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(i.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(i.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(i.combine=this.combine)),this.envMapRotation!==void 0&&(i.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(i.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(i.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(i.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(i.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(i.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(i.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(i.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(i.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(i.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(i.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(i.size=this.size),this.shadowSide!==null&&(i.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(i.sizeAttenuation=this.sizeAttenuation),this.blending!==kr&&(i.blending=this.blending),this.side!==Hi&&(i.side=this.side),this.vertexColors===!0&&(i.vertexColors=!0),this.opacity<1&&(i.opacity=this.opacity),this.transparent===!0&&(i.transparent=!0),this.blendSrc!==Au&&(i.blendSrc=this.blendSrc),this.blendDst!==Ru&&(i.blendDst=this.blendDst),this.blendEquation!==Fr&&(i.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(i.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(i.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(i.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(i.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(i.blendAlpha=this.blendAlpha),this.depthFunc!==Os&&(i.depthFunc=this.depthFunc),this.depthTest===!1&&(i.depthTest=this.depthTest),this.depthWrite===!1&&(i.depthWrite=this.depthWrite),this.colorWrite===!1&&(i.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(i.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==od&&(i.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(i.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(i.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==as&&(i.stencilFail=this.stencilFail),this.stencilZFail!==as&&(i.stencilZFail=this.stencilZFail),this.stencilZPass!==as&&(i.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(i.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(i.rotation=this.rotation),this.polygonOffset===!0&&(i.polygonOffset=!0),this.polygonOffsetFactor!==0&&(i.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(i.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(i.linewidth=this.linewidth),this.dashSize!==void 0&&(i.dashSize=this.dashSize),this.gapSize!==void 0&&(i.gapSize=this.gapSize),this.scale!==void 0&&(i.scale=this.scale),this.dithering===!0&&(i.dithering=!0),this.alphaTest>0&&(i.alphaTest=this.alphaTest),this.alphaHash===!0&&(i.alphaHash=!0),this.alphaToCoverage===!0&&(i.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(i.premultipliedAlpha=!0),this.forceSinglePass===!0&&(i.forceSinglePass=!0),this.allowOverride===!1&&(i.allowOverride=!1),this.wireframe===!0&&(i.wireframe=!0),this.wireframeLinewidth>1&&(i.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(i.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(i.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(i.flatShading=!0),this.visible===!1&&(i.visible=!1),this.toneMapped===!1&&(i.toneMapped=!1),this.fog===!1&&(i.fog=!1),Object.keys(this.userData).length>0&&(i.userData=this.userData);function r(s){const a=[];for(const o in s){const l=s[o];delete l.metadata,a.push(l)}return a}if(t){const s=r(e.textures),a=r(e.images);s.length>0&&(i.textures=s),a.length>0&&(i.images=a)}return i}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const t=e.clippingPlanes;let i=null;if(t!==null){const r=t.length;i=new Array(r);for(let s=0;s!==r;++s)i[s]=t[s].clone()}return this.clippingPlanes=i,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}}class Aa extends Yi{constructor(e){super(),this.isSpriteMaterial=!0,this.type="SpriteMaterial",this.color=new ut(16777215),this.map=null,this.alphaMap=null,this.rotation=0,this.sizeAttenuation=!0,this.transparent=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.rotation=e.rotation,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}let _s;const _a=new X,vs=new X,xs=new X,bs=new Xe,va=new Xe,zm=new kt,vo=new X,xa=new X,xo=new X,Md=new Xe,Pc=new Xe,Sd=new Xe;class bo extends mn{constructor(e=new Aa){if(super(),this.isSprite=!0,this.type="Sprite",_s===void 0){_s=new At;const t=new Float32Array([-.5,-.5,0,0,0,.5,-.5,0,1,0,.5,.5,0,1,1,-.5,.5,0,0,1]),i=new Mv(t,5);_s.setIndex([0,1,2,0,2,3]),_s.setAttribute("position",new pl(i,3,0,!1)),_s.setAttribute("uv",new pl(i,2,3,!1))}this.geometry=_s,this.material=e,this.center=new Xe(.5,.5),this.count=1}raycast(e,t){e.camera===null&&pt('Sprite: "Raycaster.camera" needs to be set in order to raycast against sprites.'),vs.setFromMatrixScale(this.matrixWorld),zm.copy(e.camera.matrixWorld),this.modelViewMatrix.multiplyMatrices(e.camera.matrixWorldInverse,this.matrixWorld),xs.setFromMatrixPosition(this.modelViewMatrix),e.camera.isPerspectiveCamera&&this.material.sizeAttenuation===!1&&vs.multiplyScalar(-xs.z);const i=this.material.rotation;let r,s;i!==0&&(s=Math.cos(i),r=Math.sin(i));const a=this.center;Mo(vo.set(-.5,-.5,0),xs,a,vs,r,s),Mo(xa.set(.5,-.5,0),xs,a,vs,r,s),Mo(xo.set(.5,.5,0),xs,a,vs,r,s),Md.set(0,0),Pc.set(1,0),Sd.set(1,1);let o=e.ray.intersectTriangle(vo,xa,xo,!1,_a);if(o===null&&(Mo(xa.set(-.5,.5,0),xs,a,vs,r,s),Pc.set(0,1),o=e.ray.intersectTriangle(vo,xo,xa,!1,_a),o===null))return;const l=e.ray.origin.distanceTo(_a);l<e.near||l>e.far||t.push({distance:l,point:_a.clone(),uv:$n.getInterpolation(_a,vo,xa,xo,Md,Pc,Sd,new Xe),face:null,object:this})}copy(e,t){return super.copy(e,t),e.center!==void 0&&this.center.copy(e.center),this.material=e.material,this}}function Mo(n,e,t,i,r,s){bs.subVectors(n,t).addScalar(.5).multiply(i),r!==void 0?(va.x=s*bs.x-r*bs.y,va.y=r*bs.x+s*bs.y):va.copy(bs),n.copy(e),n.x+=va.x,n.y+=va.y,n.applyMatrix4(zm)}const Ni=new X,Dc=new X,So=new X,nr=new X,Uc=new X,yo=new X,Lc=new X;class Ll{constructor(e=new X,t=new X(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,Ni)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);const i=t.dot(this.direction);return i<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,i)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const t=Ni.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(Ni.copy(this.origin).addScaledVector(this.direction,t),Ni.distanceToSquared(e))}distanceSqToSegment(e,t,i,r){Dc.copy(e).add(t).multiplyScalar(.5),So.copy(t).sub(e).normalize(),nr.copy(this.origin).sub(Dc);const s=e.distanceTo(t)*.5,a=-this.direction.dot(So),o=nr.dot(this.direction),l=-nr.dot(So),c=nr.lengthSq(),u=Math.abs(1-a*a);let f,h,d,g;if(u>0)if(f=a*l-o,h=a*o-l,g=s*u,f>=0)if(h>=-g)if(h<=g){const m=1/u;f*=m,h*=m,d=f*(f+a*h+2*o)+h*(a*f+h+2*l)+c}else h=s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;else h=-s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;else h<=-g?(f=Math.max(0,-(-a*s+o)),h=f>0?-s:Math.min(Math.max(-s,-l),s),d=-f*f+h*(h+2*l)+c):h<=g?(f=0,h=Math.min(Math.max(-s,-l),s),d=h*(h+2*l)+c):(f=Math.max(0,-(a*s+o)),h=f>0?s:Math.min(Math.max(-s,-l),s),d=-f*f+h*(h+2*l)+c);else h=a>0?-s:s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;return i&&i.copy(this.origin).addScaledVector(this.direction,f),r&&r.copy(Dc).addScaledVector(So,h),d}intersectSphere(e,t){Ni.subVectors(e.center,this.origin);const i=Ni.dot(this.direction),r=Ni.dot(Ni)-i*i,s=e.radius*e.radius;if(r>s)return null;const a=Math.sqrt(s-r),o=i-a,l=i+a;return l<0?null:o<0?this.at(l,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;const i=-(this.origin.dot(e.normal)+e.constant)/t;return i>=0?i:null}intersectPlane(e,t){const i=this.distanceToPlane(e);return i===null?null:this.at(i,t)}intersectsPlane(e){const t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let i,r,s,a,o,l;const c=1/this.direction.x,u=1/this.direction.y,f=1/this.direction.z,h=this.origin;return c>=0?(i=(e.min.x-h.x)*c,r=(e.max.x-h.x)*c):(i=(e.max.x-h.x)*c,r=(e.min.x-h.x)*c),u>=0?(s=(e.min.y-h.y)*u,a=(e.max.y-h.y)*u):(s=(e.max.y-h.y)*u,a=(e.min.y-h.y)*u),i>a||s>r||((s>i||isNaN(i))&&(i=s),(a<r||isNaN(r))&&(r=a),f>=0?(o=(e.min.z-h.z)*f,l=(e.max.z-h.z)*f):(o=(e.max.z-h.z)*f,l=(e.min.z-h.z)*f),i>l||o>r)||((o>i||i!==i)&&(i=o),(l<r||r!==r)&&(r=l),r<0)?null:this.at(i>=0?i:r,t)}intersectsBox(e){return this.intersectBox(e,Ni)!==null}intersectTriangle(e,t,i,r,s){Uc.subVectors(t,e),yo.subVectors(i,e),Lc.crossVectors(Uc,yo);let a=this.direction.dot(Lc),o;if(a>0){if(r)return null;o=1}else if(a<0)o=-1,a=-a;else return null;nr.subVectors(this.origin,e);const l=o*this.direction.dot(yo.crossVectors(nr,yo));if(l<0)return null;const c=o*this.direction.dot(Uc.cross(nr));if(c<0||l+c>a)return null;const u=-o*nr.dot(Lc);return u<0?null:this.at(u/a,s)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class nf extends Yi{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new ut(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Kr,this.combine=vm,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const yd=new kt,Rr=new Ll,To=new Ks,Td=new X,Eo=new X,wo=new X,Ao=new X,Ic=new X,Ro=new X,Ed=new X,Co=new X;class Wn extends mn{constructor(e=new At,t=new nf){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const t=this.geometry.morphAttributes,i=Object.keys(t);if(i.length>0){const r=t[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){const o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}getVertexPosition(e,t){const i=this.geometry,r=i.attributes.position,s=i.morphAttributes.position,a=i.morphTargetsRelative;t.fromBufferAttribute(r,e);const o=this.morphTargetInfluences;if(s&&o){Ro.set(0,0,0);for(let l=0,c=s.length;l<c;l++){const u=o[l],f=s[l];u!==0&&(Ic.fromBufferAttribute(f,e),a?Ro.addScaledVector(Ic,u):Ro.addScaledVector(Ic.sub(t),u))}t.add(Ro)}return t}raycast(e,t){const i=this.geometry,r=this.material,s=this.matrixWorld;r!==void 0&&(i.boundingSphere===null&&i.computeBoundingSphere(),To.copy(i.boundingSphere),To.applyMatrix4(s),Rr.copy(e.ray).recast(e.near),!(To.containsPoint(Rr.origin)===!1&&(Rr.intersectSphere(To,Td)===null||Rr.origin.distanceToSquared(Td)>(e.far-e.near)**2))&&(yd.copy(s).invert(),Rr.copy(e.ray).applyMatrix4(yd),!(i.boundingBox!==null&&Rr.intersectsBox(i.boundingBox)===!1)&&this._computeIntersections(e,t,Rr)))}_computeIntersections(e,t,i){let r;const s=this.geometry,a=this.material,o=s.index,l=s.attributes.position,c=s.attributes.uv,u=s.attributes.uv1,f=s.attributes.normal,h=s.groups,d=s.drawRange;if(o!==null)if(Array.isArray(a))for(let g=0,m=h.length;g<m;g++){const p=h[g],_=a[p.materialIndex],v=Math.max(p.start,d.start),M=Math.min(o.count,Math.min(p.start+p.count,d.start+d.count));for(let y=v,T=M;y<T;y+=3){const S=o.getX(y),E=o.getX(y+1),b=o.getX(y+2);r=Po(this,_,e,i,c,u,f,S,E,b),r&&(r.faceIndex=Math.floor(y/3),r.face.materialIndex=p.materialIndex,t.push(r))}}else{const g=Math.max(0,d.start),m=Math.min(o.count,d.start+d.count);for(let p=g,_=m;p<_;p+=3){const v=o.getX(p),M=o.getX(p+1),y=o.getX(p+2);r=Po(this,a,e,i,c,u,f,v,M,y),r&&(r.faceIndex=Math.floor(p/3),t.push(r))}}else if(l!==void 0)if(Array.isArray(a))for(let g=0,m=h.length;g<m;g++){const p=h[g],_=a[p.materialIndex],v=Math.max(p.start,d.start),M=Math.min(l.count,Math.min(p.start+p.count,d.start+d.count));for(let y=v,T=M;y<T;y+=3){const S=y,E=y+1,b=y+2;r=Po(this,_,e,i,c,u,f,S,E,b),r&&(r.faceIndex=Math.floor(y/3),r.face.materialIndex=p.materialIndex,t.push(r))}}else{const g=Math.max(0,d.start),m=Math.min(l.count,d.start+d.count);for(let p=g,_=m;p<_;p+=3){const v=p,M=p+1,y=p+2;r=Po(this,a,e,i,c,u,f,v,M,y),r&&(r.faceIndex=Math.floor(p/3),t.push(r))}}}}function yv(n,e,t,i,r,s,a,o){let l;if(e.side===sn?l=i.intersectTriangle(a,s,r,!0,o):l=i.intersectTriangle(r,s,a,e.side===Hi,o),l===null)return null;Co.copy(o),Co.applyMatrix4(n.matrixWorld);const c=t.ray.origin.distanceTo(Co);return c<t.near||c>t.far?null:{distance:c,point:Co.clone(),object:n}}function Po(n,e,t,i,r,s,a,o,l,c){n.getVertexPosition(o,Eo),n.getVertexPosition(l,wo),n.getVertexPosition(c,Ao);const u=yv(n,e,t,i,Eo,wo,Ao,Ed);if(u){const f=new X;$n.getBarycoord(Ed,Eo,wo,Ao,f),r&&(u.uv=$n.getInterpolatedAttribute(r,o,l,c,f,new Xe)),s&&(u.uv1=$n.getInterpolatedAttribute(s,o,l,c,f,new Xe)),a&&(u.normal=$n.getInterpolatedAttribute(a,o,l,c,f,new X),u.normal.dot(i.direction)>0&&u.normal.multiplyScalar(-1));const h={a:o,b:l,c,normal:new X,materialIndex:0};$n.getNormal(Eo,wo,Ao,h.normal),u.face=h,u.barycoord=f}return u}class Tv extends Zt{constructor(e=null,t=1,i=1,r,s,a,o,l,c=cn,u=cn,f,h){super(null,a,o,l,c,u,r,s,f,h),this.isDataTexture=!0,this.image={data:e,width:t,height:i},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class Ev extends Ft{constructor(e,t,i,r=1){super(e,t,i),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=r}copy(e){return super.copy(e),this.meshPerAttribute=e.meshPerAttribute,this}toJSON(){const e=super.toJSON();return e.meshPerAttribute=this.meshPerAttribute,e.isInstancedBufferAttribute=!0,e}}const Fc=new X,wv=new X,Av=new rt;class or{constructor(e=new X(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,i,r){return this.normal.set(e,t,i),this.constant=r,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,i){const r=Fc.subVectors(i,t).cross(wv.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(r,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t,i=!0){const r=e.delta(Fc),s=this.normal.dot(r);if(s===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;const a=-(e.start.dot(this.normal)+this.constant)/s;return i===!0&&(a<0||a>1)?null:t.copy(e.start).addScaledVector(r,a)}intersectsLine(e){const t=this.distanceToPoint(e.start),i=this.distanceToPoint(e.end);return t<0&&i>0||i<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){const i=t||Av.getNormalMatrix(e),r=this.coplanarPoint(Fc).applyMatrix4(e),s=this.normal.applyMatrix3(i).normalize();return this.constant=-r.dot(s),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}}const Cr=new Ks,Rv=new Xe(.5,.5),Do=new X;class Gm{constructor(e=new or,t=new or,i=new or,r=new or,s=new or,a=new or){this.planes=[e,t,i,r,s,a]}set(e,t,i,r,s,a){const o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(i),o[3].copy(r),o[4].copy(s),o[5].copy(a),this}copy(e){const t=this.planes;for(let i=0;i<6;i++)t[i].copy(e.planes[i]);return this}setFromProjectionMatrix(e,t=Ti,i=!1){const r=this.planes,s=e.elements,a=s[0],o=s[1],l=s[2],c=s[3],u=s[4],f=s[5],h=s[6],d=s[7],g=s[8],m=s[9],p=s[10],_=s[11],v=s[12],M=s[13],y=s[14],T=s[15];if(r[0].setComponents(c-a,d-u,_-g,T-v).normalize(),r[1].setComponents(c+a,d+u,_+g,T+v).normalize(),r[2].setComponents(c+o,d+f,_+m,T+M).normalize(),r[3].setComponents(c-o,d-f,_-m,T-M).normalize(),i)r[4].setComponents(l,h,p,y).normalize(),r[5].setComponents(c-l,d-h,_-p,T-y).normalize();else if(r[4].setComponents(c-l,d-h,_-p,T-y).normalize(),t===Ti)r[5].setComponents(c+l,d+h,_+p,T+y).normalize();else if(t===hl)r[5].setComponents(l,h,p,y).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Cr.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),Cr.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Cr)}intersectsSprite(e){Cr.center.set(0,0,0);const t=Rv.distanceTo(e.center);return Cr.radius=.7071067811865476+t,Cr.applyMatrix4(e.matrixWorld),this.intersectsSphere(Cr)}intersectsSphere(e){const t=this.planes,i=e.center,r=-e.radius;for(let s=0;s<6;s++)if(t[s].distanceToPoint(i)<r)return!1;return!0}intersectsBox(e){const t=this.planes;for(let i=0;i<6;i++){const r=t[i];if(Do.x=r.normal.x>0?e.max.x:e.min.x,Do.y=r.normal.y>0?e.max.y:e.min.y,Do.z=r.normal.z>0?e.max.z:e.min.z,r.distanceToPoint(Do)<0)return!1}return!0}containsPoint(e){const t=this.planes;for(let i=0;i<6;i++)if(t[i].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class ws extends Yi{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new ut(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}}const ml=new X,gl=new X,wd=new kt,ba=new Ll,Uo=new Ks,Nc=new X,Ad=new X;class _l extends mn{constructor(e=new At,t=new ws){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,i=[0];for(let r=1,s=t.count;r<s;r++)ml.fromBufferAttribute(t,r-1),gl.fromBufferAttribute(t,r),i[r]=i[r-1],i[r]+=ml.distanceTo(gl);e.setAttribute("lineDistance",new ui(i,1))}else Je("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(e,t){const i=this.geometry,r=this.matrixWorld,s=e.params.Line.threshold,a=i.drawRange;if(i.boundingSphere===null&&i.computeBoundingSphere(),Uo.copy(i.boundingSphere),Uo.applyMatrix4(r),Uo.radius+=s,e.ray.intersectsSphere(Uo)===!1)return;wd.copy(r).invert(),ba.copy(e.ray).applyMatrix4(wd);const o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=this.isLineSegments?2:1,u=i.index,h=i.attributes.position;if(u!==null){const d=Math.max(0,a.start),g=Math.min(u.count,a.start+a.count);for(let m=d,p=g-1;m<p;m+=c){const _=u.getX(m),v=u.getX(m+1),M=Lo(this,e,ba,l,_,v,m);M&&t.push(M)}if(this.isLineLoop){const m=u.getX(g-1),p=u.getX(d),_=Lo(this,e,ba,l,m,p,g-1);_&&t.push(_)}}else{const d=Math.max(0,a.start),g=Math.min(h.count,a.start+a.count);for(let m=d,p=g-1;m<p;m+=c){const _=Lo(this,e,ba,l,m,m+1,m);_&&t.push(_)}if(this.isLineLoop){const m=Lo(this,e,ba,l,g-1,d,g-1);m&&t.push(m)}}}updateMorphTargets(){const t=this.geometry.morphAttributes,i=Object.keys(t);if(i.length>0){const r=t[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){const o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}}function Lo(n,e,t,i,r,s,a){const o=n.geometry.attributes.position;if(ml.fromBufferAttribute(o,r),gl.fromBufferAttribute(o,s),t.distanceSqToSegment(ml,gl,Nc,Ad)>i)return;Nc.applyMatrix4(n.matrixWorld);const c=e.ray.origin.distanceTo(Nc);if(!(c<e.near||c>e.far))return{distance:c,point:Ad.clone().applyMatrix4(n.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:n}}const Rd=new X,Cd=new X;class ir extends _l{constructor(e,t){super(e,t),this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,i=[];for(let r=0,s=t.count;r<s;r+=2)Rd.fromBufferAttribute(t,r),Cd.fromBufferAttribute(t,r+1),i[r]=r===0?0:i[r-1],i[r+1]=i[r]+Rd.distanceTo(Cd);e.setAttribute("lineDistance",new ui(i,1))}else Je("LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}}class Oc extends _l{constructor(e,t){super(e,t),this.isLineLoop=!0,this.type="LineLoop"}}class Cv extends Yi{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new ut(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}const Pd=new kt,_h=new Ll,Io=new Ks,Fo=new X;class Pv extends mn{constructor(e=new At,t=new Cv){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}raycast(e,t){const i=this.geometry,r=this.matrixWorld,s=e.params.Points.threshold,a=i.drawRange;if(i.boundingSphere===null&&i.computeBoundingSphere(),Io.copy(i.boundingSphere),Io.applyMatrix4(r),Io.radius+=s,e.ray.intersectsSphere(Io)===!1)return;Pd.copy(r).invert(),_h.copy(e.ray).applyMatrix4(Pd);const o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=i.index,f=i.attributes.position;if(c!==null){const h=Math.max(0,a.start),d=Math.min(c.count,a.start+a.count);for(let g=h,m=d;g<m;g++){const p=c.getX(g);Fo.fromBufferAttribute(f,p),Dd(Fo,p,l,r,e,t,this)}}else{const h=Math.max(0,a.start),d=Math.min(f.count,a.start+a.count);for(let g=h,m=d;g<m;g++)Fo.fromBufferAttribute(f,g),Dd(Fo,g,l,r,e,t,this)}}updateMorphTargets(){const t=this.geometry.morphAttributes,i=Object.keys(t);if(i.length>0){const r=t[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){const o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}}function Dd(n,e,t,i,r,s,a){const o=_h.distanceSqToPoint(n);if(o<t){const l=new X;_h.closestPointToPoint(n,l),l.applyMatrix4(i);const c=r.ray.origin.distanceTo(l);if(c<r.near||c>r.far)return;s.push({distance:c,distanceToRay:Math.sqrt(o),point:l,index:e,face:null,faceIndex:null,barycoord:null,object:a})}}class Hm extends Zt{constructor(e=[],t=Yr,i,r,s,a,o,l,c,u){super(e,t,i,r,s,a,o,l,c,u),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class Dv extends Zt{constructor(e,t,i,r,s,a,o,l,c){super(e,t,i,r,s,a,o,l,c),this.isCanvasTexture=!0,this.needsUpdate=!0}}class Gi extends Zt{constructor(e,t,i=Ri,r,s,a,o=cn,l=cn,c,u=Wi,f=1){if(u!==Wi&&u!==lr)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");const h={width:e,height:t,depth:f};super(h,r,s,a,o,l,u,i,c),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new tf(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){const t=super.toJSON(e);return this.compareFunction!==null&&(t.compareFunction=this.compareFunction),t}}class Uv extends Gi{constructor(e,t=Ri,i=Yr,r,s,a=cn,o=cn,l,c=Wi){const u={width:e,height:e,depth:1},f=[u,u,u,u,u,u];super(e,e,t,i,r,s,a,o,l,c),this.image=f,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}}class Vm extends Zt{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class Za extends At{constructor(e=1,t=1,i=1,r=1,s=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:i,widthSegments:r,heightSegments:s,depthSegments:a};const o=this;r=Math.floor(r),s=Math.floor(s),a=Math.floor(a);const l=[],c=[],u=[],f=[];let h=0,d=0;g("z","y","x",-1,-1,i,t,e,a,s,0),g("z","y","x",1,-1,i,t,-e,a,s,1),g("x","z","y",1,1,e,i,t,r,a,2),g("x","z","y",1,-1,e,i,-t,r,a,3),g("x","y","z",1,-1,e,t,i,r,s,4),g("x","y","z",-1,-1,e,t,-i,r,s,5),this.setIndex(l),this.setAttribute("position",new ui(c,3)),this.setAttribute("normal",new ui(u,3)),this.setAttribute("uv",new ui(f,2));function g(m,p,_,v,M,y,T,S,E,b,x){const A=y/E,C=T/b,R=y/2,L=T/2,U=S/2,I=E+1,F=b+1;let O=0,j=0;const G=new X;for(let W=0;W<F;W++){const N=W*C-L;for(let k=0;k<I;k++){const J=k*A-R;G[m]=J*v,G[p]=N*M,G[_]=U,c.push(G.x,G.y,G.z),G[m]=0,G[p]=0,G[_]=S>0?1:-1,u.push(G.x,G.y,G.z),f.push(k/E),f.push(1-W/b),O+=1}}for(let W=0;W<b;W++)for(let N=0;N<E;N++){const k=h+N+I*W,J=h+N+I*(W+1),Q=h+(N+1)+I*(W+1),K=h+(N+1)+I*W;l.push(k,J,K),l.push(J,Q,K),j+=6}o.addGroup(d,j,x),d+=j,h+=O}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Za(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}class Zr extends At{constructor(e=1,t=1,i=1,r=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:i,heightSegments:r};const s=e/2,a=t/2,o=Math.floor(i),l=Math.floor(r),c=o+1,u=l+1,f=e/o,h=t/l,d=[],g=[],m=[],p=[];for(let _=0;_<u;_++){const v=_*h-a;for(let M=0;M<c;M++){const y=M*f-s;g.push(y,-v,0),m.push(0,0,1),p.push(M/o),p.push(1-_/l)}}for(let _=0;_<l;_++)for(let v=0;v<o;v++){const M=v+c*_,y=v+c*(_+1),T=v+1+c*(_+1),S=v+1+c*_;d.push(M,y,S),d.push(y,T,S)}this.setIndex(d),this.setAttribute("position",new ui(g,3)),this.setAttribute("normal",new ui(m,3)),this.setAttribute("uv",new ui(p,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Zr(e.width,e.height,e.widthSegments,e.heightSegments)}}function Gs(n){const e={};for(const t in n){e[t]={};for(const i in n[t]){const r=n[t][i];if(Ud(r))r.isRenderTargetTexture?(Je("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][i]=null):e[t][i]=r.clone();else if(Array.isArray(r))if(Ud(r[0])){const s=[];for(let a=0,o=r.length;a<o;a++)s[a]=r[a].clone();e[t][i]=s}else e[t][i]=r.slice();else e[t][i]=r}}return e}function bn(n){const e={};for(let t=0;t<n.length;t++){const i=Gs(n[t]);for(const r in i)e[r]=i[r]}return e}function Ud(n){return n&&(n.isColor||n.isMatrix3||n.isMatrix4||n.isVector2||n.isVector3||n.isVector4||n.isTexture||n.isQuaternion)}function Lv(n){const e=[];for(let t=0;t<n.length;t++)e.push(n[t].clone());return e}function Wm(n){const e=n.getRenderTarget();return e===null?n.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:ft.workingColorSpace}const Xm={clone:Gs,merge:bn};var Iv=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Fv=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class an extends Yi{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=Iv,this.fragmentShader=Fv,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Gs(e.uniforms),this.uniformsGroups=Lv(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){const t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(const r in this.uniforms){const a=this.uniforms[r].value;a&&a.isTexture?t.uniforms[r]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[r]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[r]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[r]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[r]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[r]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[r]={type:"m4",value:a.toArray()}:t.uniforms[r]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;const i={};for(const r in this.extensions)this.extensions[r]===!0&&(i[r]=!0);return Object.keys(i).length>0&&(t.extensions=i),t}}class Nv extends an{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}}class jm extends Yi{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=Ka,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class Ym extends Yi{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}const No=new X,Oo=new _r,gi=new X;class qm extends mn{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new kt,this.projectionMatrix=new kt,this.projectionMatrixInverse=new kt,this.coordinateSystem=Ti,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(No,Oo,gi),gi.x===1&&gi.y===1&&gi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(No,Oo,gi.set(1,1,1)).invert()}updateWorldMatrix(e,t){super.updateWorldMatrix(e,t),this.matrixWorld.decompose(No,Oo,gi),gi.x===1&&gi.y===1&&gi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(No,Oo,gi.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}}const rr=new X,Ld=new Xe,Id=new Xe;class kn extends qm{constructor(e=50,t=1,i=.1,r=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=i,this.far=r,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const t=.5*this.getFilmHeight()/e;this.fov=mh*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(Jo*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return mh*2*Math.atan(Math.tan(Jo*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,i){rr.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(rr.x,rr.y).multiplyScalar(-e/rr.z),rr.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),i.set(rr.x,rr.y).multiplyScalar(-e/rr.z)}getViewSize(e,t){return this.getViewBounds(e,Ld,Id),t.subVectors(Id,Ld)}setViewOffset(e,t,i,r,s,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=i,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let t=e*Math.tan(Jo*.5*this.fov)/this.zoom,i=2*t,r=this.aspect*i,s=-.5*r;const a=this.view;if(this.view!==null&&this.view.enabled){const l=a.fullWidth,c=a.fullHeight;s+=a.offsetX*r/l,t-=a.offsetY*i/c,r*=a.width/l,i*=a.height/c}const o=this.filmOffset;o!==0&&(s+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(s,s+r,t,t-i,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}}class rf extends qm{constructor(e=-1,t=1,i=1,r=-1,s=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=i,this.bottom=r,this.near=s,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,i,r,s,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=i,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),i=(this.right+this.left)/2,r=(this.top+this.bottom)/2;let s=i-e,a=i+e,o=r+t,l=r-t;if(this.view!==null&&this.view.enabled){const c=(this.right-this.left)/this.view.fullWidth/this.zoom,u=(this.top-this.bottom)/this.view.fullHeight/this.zoom;s+=c*this.view.offsetX,a=s+c*this.view.width,o-=u*this.view.offsetY,l=o-u*this.view.height}this.projectionMatrix.makeOrthographic(s,a,o,l,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}}class Ov extends At{constructor(){super(),this.isInstancedBufferGeometry=!0,this.type="InstancedBufferGeometry",this.instanceCount=1/0}copy(e){return super.copy(e),this.instanceCount=e.instanceCount,this}toJSON(){const e=super.toJSON();return e.instanceCount=this.instanceCount,e.isInstancedBufferGeometry=!0,e}}const Ms=-90,Ss=1;class Bv extends mn{constructor(e,t,i){super(),this.type="CubeCamera",this.renderTarget=i,this.coordinateSystem=null,this.activeMipmapLevel=0;const r=new kn(Ms,Ss,e,t);r.layers=this.layers,this.add(r);const s=new kn(Ms,Ss,e,t);s.layers=this.layers,this.add(s);const a=new kn(Ms,Ss,e,t);a.layers=this.layers,this.add(a);const o=new kn(Ms,Ss,e,t);o.layers=this.layers,this.add(o);const l=new kn(Ms,Ss,e,t);l.layers=this.layers,this.add(l);const c=new kn(Ms,Ss,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){const e=this.coordinateSystem,t=this.children.concat(),[i,r,s,a,o,l]=t;for(const c of t)this.remove(c);if(e===Ti)i.up.set(0,1,0),i.lookAt(1,0,0),r.up.set(0,1,0),r.lookAt(-1,0,0),s.up.set(0,0,-1),s.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===hl)i.up.set(0,-1,0),i.lookAt(-1,0,0),r.up.set(0,-1,0),r.lookAt(1,0,0),s.up.set(0,0,1),s.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const c of t)this.add(c),c.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();const{renderTarget:i,activeMipmapLevel:r}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[s,a,o,l,c,u]=this.children,f=e.getRenderTarget(),h=e.getActiveCubeFace(),d=e.getActiveMipmapLevel(),g=e.xr.enabled;e.xr.enabled=!1;const m=i.texture.generateMipmaps;i.texture.generateMipmaps=!1;let p=!1;e.isWebGLRenderer===!0?p=e.state.buffers.depth.getReversed():p=e.reversedDepthBuffer,e.setRenderTarget(i,0,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,s),e.setRenderTarget(i,1,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,a),e.setRenderTarget(i,2,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,o),e.setRenderTarget(i,3,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,l),e.setRenderTarget(i,4,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,c),i.texture.generateMipmaps=m,e.setRenderTarget(i,5,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,u),e.setRenderTarget(f,h,d),e.xr.enabled=g,i.texture.needsPMREMUpdate=!0}}class kv extends kn{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}class vt{constructor(e){this.value=e}clone(){return new vt(this.value.clone===void 0?this.value:this.value.clone())}}class zv{constructor(e=!0){this.autoStart=e,this.startTime=0,this.oldTime=0,this.elapsedTime=0,this.running=!1,Je("Clock: This module has been deprecated. Please use THREE.Timer instead.")}start(){this.startTime=performance.now(),this.oldTime=this.startTime,this.elapsedTime=0,this.running=!0}stop(){this.getElapsedTime(),this.running=!1,this.autoStart=!1}getElapsedTime(){return this.getDelta(),this.elapsedTime}getDelta(){let e=0;if(this.autoStart&&!this.running)return this.start(),0;if(this.running){const t=performance.now();e=(t-this.oldTime)/1e3,this.oldTime=t,this.elapsedTime+=e}return e}}class Fd{constructor(e=1,t=0,i=0){this.radius=e,this.phi=t,this.theta=i}set(e,t,i){return this.radius=e,this.phi=t,this.theta=i,this}copy(e){return this.radius=e.radius,this.phi=e.phi,this.theta=e.theta,this}makeSafe(){return this.phi=lt(this.phi,1e-6,Math.PI-1e-6),this}setFromVector3(e){return this.setFromCartesianCoords(e.x,e.y,e.z)}setFromCartesianCoords(e,t,i){return this.radius=Math.sqrt(e*e+t*t+i*i),this.radius===0?(this.theta=0,this.phi=0):(this.theta=Math.atan2(e,i),this.phi=Math.acos(lt(t/this.radius,-1,1))),this}clone(){return new this.constructor().copy(this)}}const kf=class kf{constructor(e,t,i,r){this.elements=[1,0,0,1],e!==void 0&&this.set(e,t,i,r)}identity(){return this.set(1,0,0,1),this}fromArray(e,t=0){for(let i=0;i<4;i++)this.elements[i]=e[i+t];return this}set(e,t,i,r){const s=this.elements;return s[0]=e,s[2]=t,s[1]=i,s[3]=r,this}};kf.prototype.isMatrix2=!0;let Nd=kf;class Gv extends hi{constructor(e,t=null){super(),this.object=e,this.domElement=t,this.enabled=!0,this.state=-1,this.keys={},this.mouseButtons={LEFT:null,MIDDLE:null,RIGHT:null},this.touches={ONE:null,TWO:null}}connect(e){if(e===void 0){Je("Controls: connect() now requires an element.");return}this.domElement!==null&&this.disconnect(),this.domElement=e}disconnect(){}dispose(){}update(){}}function Od(n,e,t,i){const r=Hv(i);switch(t){case Dm:return n*e;case Lm:return n*e/r.components*r.byteLength;case Zh:return n*e/r.components*r.byteLength;case qr:return n*e*2/r.components*r.byteLength;case $h:return n*e*2/r.components*r.byteLength;case Um:return n*e*3/r.components*r.byteLength;case ci:return n*e*4/r.components*r.byteLength;case Jh:return n*e*4/r.components*r.byteLength;case qo:case Ko:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*8;case Zo:case $o:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case Bu:case zu:return Math.max(n,16)*Math.max(e,8)/4;case Ou:case ku:return Math.max(n,8)*Math.max(e,8)/2;case Gu:case Hu:case Wu:case Xu:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*8;case Vu:case ll:case ju:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case Yu:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case qu:return Math.floor((n+4)/5)*Math.floor((e+3)/4)*16;case Ku:return Math.floor((n+4)/5)*Math.floor((e+4)/5)*16;case Zu:return Math.floor((n+5)/6)*Math.floor((e+4)/5)*16;case $u:return Math.floor((n+5)/6)*Math.floor((e+5)/6)*16;case Ju:return Math.floor((n+7)/8)*Math.floor((e+4)/5)*16;case Qu:return Math.floor((n+7)/8)*Math.floor((e+5)/6)*16;case eh:return Math.floor((n+7)/8)*Math.floor((e+7)/8)*16;case th:return Math.floor((n+9)/10)*Math.floor((e+4)/5)*16;case nh:return Math.floor((n+9)/10)*Math.floor((e+5)/6)*16;case ih:return Math.floor((n+9)/10)*Math.floor((e+7)/8)*16;case rh:return Math.floor((n+9)/10)*Math.floor((e+9)/10)*16;case sh:return Math.floor((n+11)/12)*Math.floor((e+9)/10)*16;case ah:return Math.floor((n+11)/12)*Math.floor((e+11)/12)*16;case oh:case lh:case ch:return Math.ceil(n/4)*Math.ceil(e/4)*16;case uh:case hh:return Math.ceil(n/4)*Math.ceil(e/4)*8;case cl:case fh:return Math.ceil(n/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function Hv(n){switch(n){case jt:case Am:return{byteLength:1,components:1};case Ba:case Rm:case Vi:return{byteLength:2,components:1};case qh:case Kh:return{byteLength:2,components:4};case Ri:case Yh:case li:return{byteLength:4,components:1};case Cm:case Pm:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${n}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:qa}}));typeof window<"u"&&(window.__THREE__?Je("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=qa);/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */function Km(){let n=null,e=!1,t=null,i=null;function r(s,a){t(s,a),i=n.requestAnimationFrame(r)}return{start:function(){e!==!0&&t!==null&&n!==null&&(i=n.requestAnimationFrame(r),e=!0)},stop:function(){n!==null&&n.cancelAnimationFrame(i),e=!1},setAnimationLoop:function(s){t=s},setContext:function(s){n=s}}}function Vv(n){const e=new WeakMap;function t(o,l){const c=o.array,u=o.usage,f=c.byteLength,h=n.createBuffer();n.bindBuffer(l,h),n.bufferData(l,c,u),o.onUploadCallback();let d;if(c instanceof Float32Array)d=n.FLOAT;else if(typeof Float16Array<"u"&&c instanceof Float16Array)d=n.HALF_FLOAT;else if(c instanceof Uint16Array)o.isFloat16BufferAttribute?d=n.HALF_FLOAT:d=n.UNSIGNED_SHORT;else if(c instanceof Int16Array)d=n.SHORT;else if(c instanceof Uint32Array)d=n.UNSIGNED_INT;else if(c instanceof Int32Array)d=n.INT;else if(c instanceof Int8Array)d=n.BYTE;else if(c instanceof Uint8Array)d=n.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)d=n.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:h,type:d,bytesPerElement:c.BYTES_PER_ELEMENT,version:o.version,size:f}}function i(o,l,c){const u=l.array,f=l.updateRanges;if(n.bindBuffer(c,o),f.length===0)n.bufferSubData(c,0,u);else{f.sort((d,g)=>d.start-g.start);let h=0;for(let d=1;d<f.length;d++){const g=f[h],m=f[d];m.start<=g.start+g.count+1?g.count=Math.max(g.count,m.start+m.count-g.start):(++h,f[h]=m)}f.length=h+1;for(let d=0,g=f.length;d<g;d++){const m=f[d];n.bufferSubData(c,m.start*u.BYTES_PER_ELEMENT,u,m.start,m.count)}l.clearUpdateRanges()}l.onUploadCallback()}function r(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function s(o){o.isInterleavedBufferAttribute&&(o=o.data);const l=e.get(o);l&&(n.deleteBuffer(l.buffer),e.delete(o))}function a(o,l){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){const u=e.get(o);(!u||u.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}const c=e.get(o);if(c===void 0)e.set(o,t(o,l));else if(c.version<o.version){if(c.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");i(c.buffer,o,l),c.version=o.version}}return{get:r,remove:s,update:a}}var Wv=`#ifdef USE_ALPHAHASH
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
#endif`,bx="gl_FragColor = linearToOutputTexel( gl_FragColor );",Mx=`vec4 LinearTransferOETF( in vec4 value ) {
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
#endif`,yx=`#ifdef USE_ENVMAP
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
}`,b1=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,M1=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,S1=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,y1=`#ifdef DITHERING
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
}`,eb=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,tb=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,nb=`uniform float scale;
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
}`,ib=`uniform vec3 diffuse;
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
}`,rb=`#include <common>
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
}`,sb=`uniform vec3 diffuse;
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
}`,ab=`#define LAMBERT
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
}`,ob=`#define LAMBERT
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
}`,lb=`#define MATCAP
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
}`,cb=`#define MATCAP
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
}`,ub=`#define NORMAL
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
}`,hb=`#define NORMAL
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
}`,fb=`#define PHONG
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
}`,db=`#define PHONG
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
}`,pb=`#define STANDARD
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
}`,mb=`#define STANDARD
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
}`,gb=`#define TOON
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
}`,_b=`#define TOON
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
}`,vb=`uniform float size;
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
}`,xb=`uniform vec3 diffuse;
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
}`,bb=`#include <common>
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
}`,Mb=`uniform vec3 color;
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
}`,Sb=`uniform float rotation;
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
}`,yb=`uniform vec3 diffuse;
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
}`,st={alphahash_fragment:Wv,alphahash_pars_fragment:Xv,alphamap_fragment:jv,alphamap_pars_fragment:Yv,alphatest_fragment:qv,alphatest_pars_fragment:Kv,aomap_fragment:Zv,aomap_pars_fragment:$v,batching_pars_vertex:Jv,batching_vertex:Qv,begin_vertex:ex,beginnormal_vertex:tx,bsdfs:nx,iridescence_fragment:ix,bumpmap_pars_fragment:rx,clipping_planes_fragment:sx,clipping_planes_pars_fragment:ax,clipping_planes_pars_vertex:ox,clipping_planes_vertex:lx,color_fragment:cx,color_pars_fragment:ux,color_pars_vertex:hx,color_vertex:fx,common:dx,cube_uv_reflection_fragment:px,defaultnormal_vertex:mx,displacementmap_pars_vertex:gx,displacementmap_vertex:_x,emissivemap_fragment:vx,emissivemap_pars_fragment:xx,colorspace_fragment:bx,colorspace_pars_fragment:Mx,envmap_fragment:Sx,envmap_common_pars_fragment:yx,envmap_pars_fragment:Tx,envmap_pars_vertex:Ex,envmap_physical_pars_fragment:Nx,envmap_vertex:wx,fog_vertex:Ax,fog_pars_vertex:Rx,fog_fragment:Cx,fog_pars_fragment:Px,gradientmap_pars_fragment:Dx,lightmap_pars_fragment:Ux,lights_lambert_fragment:Lx,lights_lambert_pars_fragment:Ix,lights_pars_begin:Fx,lights_toon_fragment:Ox,lights_toon_pars_fragment:Bx,lights_phong_fragment:kx,lights_phong_pars_fragment:zx,lights_physical_fragment:Gx,lights_physical_pars_fragment:Hx,lights_fragment_begin:Vx,lights_fragment_maps:Wx,lights_fragment_end:Xx,lightprobes_pars_fragment:jx,logdepthbuf_fragment:Yx,logdepthbuf_pars_fragment:qx,logdepthbuf_pars_vertex:Kx,logdepthbuf_vertex:Zx,map_fragment:$x,map_pars_fragment:Jx,map_particle_fragment:Qx,map_particle_pars_fragment:e1,metalnessmap_fragment:t1,metalnessmap_pars_fragment:n1,morphinstance_vertex:i1,morphcolor_vertex:r1,morphnormal_vertex:s1,morphtarget_pars_vertex:a1,morphtarget_vertex:o1,normal_fragment_begin:l1,normal_fragment_maps:c1,normal_pars_fragment:u1,normal_pars_vertex:h1,normal_vertex:f1,normalmap_pars_fragment:d1,clearcoat_normal_fragment_begin:p1,clearcoat_normal_fragment_maps:m1,clearcoat_pars_fragment:g1,iridescence_pars_fragment:_1,opaque_fragment:v1,packing:x1,premultiplied_alpha_fragment:b1,project_vertex:M1,dithering_fragment:S1,dithering_pars_fragment:y1,roughnessmap_fragment:T1,roughnessmap_pars_fragment:E1,shadowmap_pars_fragment:w1,shadowmap_pars_vertex:A1,shadowmap_vertex:R1,shadowmask_pars_fragment:C1,skinbase_vertex:P1,skinning_pars_vertex:D1,skinning_vertex:U1,skinnormal_vertex:L1,specularmap_fragment:I1,specularmap_pars_fragment:F1,tonemapping_fragment:N1,tonemapping_pars_fragment:O1,transmission_fragment:B1,transmission_pars_fragment:k1,uv_pars_fragment:z1,uv_pars_vertex:G1,uv_vertex:H1,worldpos_vertex:V1,background_vert:W1,background_frag:X1,backgroundCube_vert:j1,backgroundCube_frag:Y1,cube_vert:q1,cube_frag:K1,depth_vert:Z1,depth_frag:$1,distance_vert:J1,distance_frag:Q1,equirect_vert:eb,equirect_frag:tb,linedashed_vert:nb,linedashed_frag:ib,meshbasic_vert:rb,meshbasic_frag:sb,meshlambert_vert:ab,meshlambert_frag:ob,meshmatcap_vert:lb,meshmatcap_frag:cb,meshnormal_vert:ub,meshnormal_frag:hb,meshphong_vert:fb,meshphong_frag:db,meshphysical_vert:pb,meshphysical_frag:mb,meshtoon_vert:gb,meshtoon_frag:_b,points_vert:vb,points_frag:xb,shadow_vert:bb,shadow_frag:Mb,sprite_vert:Sb,sprite_frag:yb},ke={common:{diffuse:{value:new ut(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new rt},alphaMap:{value:null},alphaMapTransform:{value:new rt},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new rt}},envmap:{envMap:{value:null},envMapRotation:{value:new rt},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new rt}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new rt}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new rt},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new rt},normalScale:{value:new Xe(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new rt},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new rt}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new rt}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new rt}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new ut(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new X},probesMax:{value:new X},probesResolution:{value:new X}},points:{diffuse:{value:new ut(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new rt},alphaTest:{value:0},uvTransform:{value:new rt}},sprite:{diffuse:{value:new ut(16777215)},opacity:{value:1},center:{value:new Xe(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new rt},alphaMap:{value:null},alphaMapTransform:{value:new rt},alphaTest:{value:0}}},xi={basic:{uniforms:bn([ke.common,ke.specularmap,ke.envmap,ke.aomap,ke.lightmap,ke.fog]),vertexShader:st.meshbasic_vert,fragmentShader:st.meshbasic_frag},lambert:{uniforms:bn([ke.common,ke.specularmap,ke.envmap,ke.aomap,ke.lightmap,ke.emissivemap,ke.bumpmap,ke.normalmap,ke.displacementmap,ke.fog,ke.lights,{emissive:{value:new ut(0)},envMapIntensity:{value:1}}]),vertexShader:st.meshlambert_vert,fragmentShader:st.meshlambert_frag},phong:{uniforms:bn([ke.common,ke.specularmap,ke.envmap,ke.aomap,ke.lightmap,ke.emissivemap,ke.bumpmap,ke.normalmap,ke.displacementmap,ke.fog,ke.lights,{emissive:{value:new ut(0)},specular:{value:new ut(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:st.meshphong_vert,fragmentShader:st.meshphong_frag},standard:{uniforms:bn([ke.common,ke.envmap,ke.aomap,ke.lightmap,ke.emissivemap,ke.bumpmap,ke.normalmap,ke.displacementmap,ke.roughnessmap,ke.metalnessmap,ke.fog,ke.lights,{emissive:{value:new ut(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:st.meshphysical_vert,fragmentShader:st.meshphysical_frag},toon:{uniforms:bn([ke.common,ke.aomap,ke.lightmap,ke.emissivemap,ke.bumpmap,ke.normalmap,ke.displacementmap,ke.gradientmap,ke.fog,ke.lights,{emissive:{value:new ut(0)}}]),vertexShader:st.meshtoon_vert,fragmentShader:st.meshtoon_frag},matcap:{uniforms:bn([ke.common,ke.bumpmap,ke.normalmap,ke.displacementmap,ke.fog,{matcap:{value:null}}]),vertexShader:st.meshmatcap_vert,fragmentShader:st.meshmatcap_frag},points:{uniforms:bn([ke.points,ke.fog]),vertexShader:st.points_vert,fragmentShader:st.points_frag},dashed:{uniforms:bn([ke.common,ke.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:st.linedashed_vert,fragmentShader:st.linedashed_frag},depth:{uniforms:bn([ke.common,ke.displacementmap]),vertexShader:st.depth_vert,fragmentShader:st.depth_frag},normal:{uniforms:bn([ke.common,ke.bumpmap,ke.normalmap,ke.displacementmap,{opacity:{value:1}}]),vertexShader:st.meshnormal_vert,fragmentShader:st.meshnormal_frag},sprite:{uniforms:bn([ke.sprite,ke.fog]),vertexShader:st.sprite_vert,fragmentShader:st.sprite_frag},background:{uniforms:{uvTransform:{value:new rt},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:st.background_vert,fragmentShader:st.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new rt}},vertexShader:st.backgroundCube_vert,fragmentShader:st.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:st.cube_vert,fragmentShader:st.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:st.equirect_vert,fragmentShader:st.equirect_frag},distance:{uniforms:bn([ke.common,ke.displacementmap,{referencePosition:{value:new X},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:st.distance_vert,fragmentShader:st.distance_frag},shadow:{uniforms:bn([ke.lights,ke.fog,{color:{value:new ut(0)},opacity:{value:1}}]),vertexShader:st.shadow_vert,fragmentShader:st.shadow_frag}};xi.physical={uniforms:bn([xi.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new rt},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new rt},clearcoatNormalScale:{value:new Xe(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new rt},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new rt},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new rt},sheen:{value:0},sheenColor:{value:new ut(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new rt},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new rt},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new rt},transmissionSamplerSize:{value:new Xe},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new rt},attenuationDistance:{value:0},attenuationColor:{value:new ut(0)},specularColor:{value:new ut(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new rt},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new rt},anisotropyVector:{value:new Xe},anisotropyMap:{value:null},anisotropyMapTransform:{value:new rt}}]),vertexShader:st.meshphysical_vert,fragmentShader:st.meshphysical_frag};const Bo={r:0,b:0,g:0},Tb=new kt,Zm=new rt;Zm.set(-1,0,0,0,1,0,0,0,1);function Eb(n,e,t,i,r,s){const a=new ut(0);let o=r===!0?0:1,l,c,u=null,f=0,h=null;function d(v){let M=v.isScene===!0?v.background:null;if(M&&M.isTexture){const y=v.backgroundBlurriness>0;M=e.get(M,y)}return M}function g(v){let M=!1;const y=d(v);y===null?p(a,o):y&&y.isColor&&(p(y,1),M=!0);const T=n.xr.getEnvironmentBlendMode();T==="additive"?t.buffers.color.setClear(0,0,0,1,s):T==="alpha-blend"&&t.buffers.color.setClear(0,0,0,0,s),(n.autoClear||M)&&(t.buffers.depth.setTest(!0),t.buffers.depth.setMask(!0),t.buffers.color.setMask(!0),n.clear(n.autoClearColor,n.autoClearDepth,n.autoClearStencil))}function m(v,M){const y=d(M);y&&(y.isCubeTexture||y.mapping===Ul)?(c===void 0&&(c=new Wn(new Za(1,1,1),new an({name:"BackgroundCubeMaterial",uniforms:Gs(xi.backgroundCube.uniforms),vertexShader:xi.backgroundCube.vertexShader,fragmentShader:xi.backgroundCube.fragmentShader,side:sn,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),c.geometry.deleteAttribute("uv"),c.onBeforeRender=function(T,S,E){this.matrixWorld.copyPosition(E.matrixWorld)},Object.defineProperty(c.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),i.update(c)),c.material.uniforms.envMap.value=y,c.material.uniforms.backgroundBlurriness.value=M.backgroundBlurriness,c.material.uniforms.backgroundIntensity.value=M.backgroundIntensity,c.material.uniforms.backgroundRotation.value.setFromMatrix4(Tb.makeRotationFromEuler(M.backgroundRotation)).transpose(),y.isCubeTexture&&y.isRenderTargetTexture===!1&&c.material.uniforms.backgroundRotation.value.premultiply(Zm),c.material.toneMapped=ft.getTransfer(y.colorSpace)!==Mt,(u!==y||f!==y.version||h!==n.toneMapping)&&(c.material.needsUpdate=!0,u=y,f=y.version,h=n.toneMapping),c.layers.enableAll(),v.unshift(c,c.geometry,c.material,0,0,null)):y&&y.isTexture&&(l===void 0&&(l=new Wn(new Zr(2,2),new an({name:"BackgroundMaterial",uniforms:Gs(xi.background.uniforms),vertexShader:xi.background.vertexShader,fragmentShader:xi.background.fragmentShader,side:Hi,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),i.update(l)),l.material.uniforms.t2D.value=y,l.material.uniforms.backgroundIntensity.value=M.backgroundIntensity,l.material.toneMapped=ft.getTransfer(y.colorSpace)!==Mt,y.matrixAutoUpdate===!0&&y.updateMatrix(),l.material.uniforms.uvTransform.value.copy(y.matrix),(u!==y||f!==y.version||h!==n.toneMapping)&&(l.material.needsUpdate=!0,u=y,f=y.version,h=n.toneMapping),l.layers.enableAll(),v.unshift(l,l.geometry,l.material,0,0,null))}function p(v,M){v.getRGB(Bo,Wm(n)),t.buffers.color.setClear(Bo.r,Bo.g,Bo.b,M,s)}function _(){c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return a},setClearColor:function(v,M=1){a.set(v),o=M,p(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(v){o=v,p(a,o)},render:g,addToRenderList:m,dispose:_}}function wb(n,e){const t=n.getParameter(n.MAX_VERTEX_ATTRIBS),i={},r=h(null);let s=r,a=!1;function o(C,R,L,U,I){let F=!1;const O=f(C,U,L,R);s!==O&&(s=O,c(s.object)),F=d(C,U,L,I),F&&g(C,U,L,I),I!==null&&e.update(I,n.ELEMENT_ARRAY_BUFFER),(F||a)&&(a=!1,y(C,R,L,U),I!==null&&n.bindBuffer(n.ELEMENT_ARRAY_BUFFER,e.get(I).buffer))}function l(){return n.createVertexArray()}function c(C){return n.bindVertexArray(C)}function u(C){return n.deleteVertexArray(C)}function f(C,R,L,U){const I=U.wireframe===!0;let F=i[R.id];F===void 0&&(F={},i[R.id]=F);const O=C.isInstancedMesh===!0?C.id:0;let j=F[O];j===void 0&&(j={},F[O]=j);let G=j[L.id];G===void 0&&(G={},j[L.id]=G);let W=G[I];return W===void 0&&(W=h(l()),G[I]=W),W}function h(C){const R=[],L=[],U=[];for(let I=0;I<t;I++)R[I]=0,L[I]=0,U[I]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:R,enabledAttributes:L,attributeDivisors:U,object:C,attributes:{},index:null}}function d(C,R,L,U){const I=s.attributes,F=R.attributes;let O=0;const j=L.getAttributes();for(const G in j)if(j[G].location>=0){const N=I[G];let k=F[G];if(k===void 0&&(G==="instanceMatrix"&&C.instanceMatrix&&(k=C.instanceMatrix),G==="instanceColor"&&C.instanceColor&&(k=C.instanceColor)),N===void 0||N.attribute!==k||k&&N.data!==k.data)return!0;O++}return s.attributesNum!==O||s.index!==U}function g(C,R,L,U){const I={},F=R.attributes;let O=0;const j=L.getAttributes();for(const G in j)if(j[G].location>=0){let N=F[G];N===void 0&&(G==="instanceMatrix"&&C.instanceMatrix&&(N=C.instanceMatrix),G==="instanceColor"&&C.instanceColor&&(N=C.instanceColor));const k={};k.attribute=N,N&&N.data&&(k.data=N.data),I[G]=k,O++}s.attributes=I,s.attributesNum=O,s.index=U}function m(){const C=s.newAttributes;for(let R=0,L=C.length;R<L;R++)C[R]=0}function p(C){_(C,0)}function _(C,R){const L=s.newAttributes,U=s.enabledAttributes,I=s.attributeDivisors;L[C]=1,U[C]===0&&(n.enableVertexAttribArray(C),U[C]=1),I[C]!==R&&(n.vertexAttribDivisor(C,R),I[C]=R)}function v(){const C=s.newAttributes,R=s.enabledAttributes;for(let L=0,U=R.length;L<U;L++)R[L]!==C[L]&&(n.disableVertexAttribArray(L),R[L]=0)}function M(C,R,L,U,I,F,O){O===!0?n.vertexAttribIPointer(C,R,L,I,F):n.vertexAttribPointer(C,R,L,U,I,F)}function y(C,R,L,U){m();const I=U.attributes,F=L.getAttributes(),O=R.defaultAttributeValues;for(const j in F){const G=F[j];if(G.location>=0){let W=I[j];if(W===void 0&&(j==="instanceMatrix"&&C.instanceMatrix&&(W=C.instanceMatrix),j==="instanceColor"&&C.instanceColor&&(W=C.instanceColor)),W!==void 0){const N=W.normalized,k=W.itemSize,J=e.get(W);if(J===void 0)continue;const Q=J.buffer,K=J.type,H=J.bytesPerElement,Y=K===n.INT||K===n.UNSIGNED_INT||W.gpuType===Yh;if(W.isInterleavedBufferAttribute){const Z=W.data,fe=Z.stride,Me=W.offset;if(Z.isInstancedInterleavedBuffer){for(let ce=0;ce<G.locationSize;ce++)_(G.location+ce,Z.meshPerAttribute);C.isInstancedMesh!==!0&&U._maxInstanceCount===void 0&&(U._maxInstanceCount=Z.meshPerAttribute*Z.count)}else for(let ce=0;ce<G.locationSize;ce++)p(G.location+ce);n.bindBuffer(n.ARRAY_BUFFER,Q);for(let ce=0;ce<G.locationSize;ce++)M(G.location+ce,k/G.locationSize,K,N,fe*H,(Me+k/G.locationSize*ce)*H,Y)}else{if(W.isInstancedBufferAttribute){for(let Z=0;Z<G.locationSize;Z++)_(G.location+Z,W.meshPerAttribute);C.isInstancedMesh!==!0&&U._maxInstanceCount===void 0&&(U._maxInstanceCount=W.meshPerAttribute*W.count)}else for(let Z=0;Z<G.locationSize;Z++)p(G.location+Z);n.bindBuffer(n.ARRAY_BUFFER,Q);for(let Z=0;Z<G.locationSize;Z++)M(G.location+Z,k/G.locationSize,K,N,k*H,k/G.locationSize*Z*H,Y)}}else if(O!==void 0){const N=O[j];if(N!==void 0)switch(N.length){case 2:n.vertexAttrib2fv(G.location,N);break;case 3:n.vertexAttrib3fv(G.location,N);break;case 4:n.vertexAttrib4fv(G.location,N);break;default:n.vertexAttrib1fv(G.location,N)}}}}v()}function T(){x();for(const C in i){const R=i[C];for(const L in R){const U=R[L];for(const I in U){const F=U[I];for(const O in F)u(F[O].object),delete F[O];delete U[I]}}delete i[C]}}function S(C){if(i[C.id]===void 0)return;const R=i[C.id];for(const L in R){const U=R[L];for(const I in U){const F=U[I];for(const O in F)u(F[O].object),delete F[O];delete U[I]}}delete i[C.id]}function E(C){for(const R in i){const L=i[R];for(const U in L){const I=L[U];if(I[C.id]===void 0)continue;const F=I[C.id];for(const O in F)u(F[O].object),delete F[O];delete I[C.id]}}}function b(C){for(const R in i){const L=i[R],U=C.isInstancedMesh===!0?C.id:0,I=L[U];if(I!==void 0){for(const F in I){const O=I[F];for(const j in O)u(O[j].object),delete O[j];delete I[F]}delete L[U],Object.keys(L).length===0&&delete i[R]}}}function x(){A(),a=!0,s!==r&&(s=r,c(s.object))}function A(){r.geometry=null,r.program=null,r.wireframe=!1}return{setup:o,reset:x,resetDefaultState:A,dispose:T,releaseStatesOfGeometry:S,releaseStatesOfObject:b,releaseStatesOfProgram:E,initAttributes:m,enableAttribute:p,disableUnusedAttributes:v}}function Ab(n,e,t){let i;function r(l){i=l}function s(l,c){n.drawArrays(i,l,c),t.update(c,i,1)}function a(l,c,u){u!==0&&(n.drawArraysInstanced(i,l,c,u),t.update(c,i,u))}function o(l,c,u){if(u===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(i,l,0,c,0,u);let h=0;for(let d=0;d<u;d++)h+=c[d];t.update(h,i,1)}this.setMode=r,this.render=s,this.renderInstances=a,this.renderMultiDraw=o}function Rb(n,e,t,i){let r;function s(){if(r!==void 0)return r;if(e.has("EXT_texture_filter_anisotropic")===!0){const E=e.get("EXT_texture_filter_anisotropic");r=n.getParameter(E.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else r=0;return r}function a(E){return!(E!==ci&&i.convert(E)!==n.getParameter(n.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(E){const b=E===Vi&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(E!==jt&&i.convert(E)!==n.getParameter(n.IMPLEMENTATION_COLOR_READ_TYPE)&&E!==li&&!b)}function l(E){if(E==="highp"){if(n.getShaderPrecisionFormat(n.VERTEX_SHADER,n.HIGH_FLOAT).precision>0&&n.getShaderPrecisionFormat(n.FRAGMENT_SHADER,n.HIGH_FLOAT).precision>0)return"highp";E="mediump"}return E==="mediump"&&n.getShaderPrecisionFormat(n.VERTEX_SHADER,n.MEDIUM_FLOAT).precision>0&&n.getShaderPrecisionFormat(n.FRAGMENT_SHADER,n.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=t.precision!==void 0?t.precision:"highp";const u=l(c);u!==c&&(Je("WebGLRenderer:",c,"not supported, using",u,"instead."),c=u);const f=t.logarithmicDepthBuffer===!0,h=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control");t.reversedDepthBuffer===!0&&h===!1&&Je("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");const d=n.getParameter(n.MAX_TEXTURE_IMAGE_UNITS),g=n.getParameter(n.MAX_VERTEX_TEXTURE_IMAGE_UNITS),m=n.getParameter(n.MAX_TEXTURE_SIZE),p=n.getParameter(n.MAX_CUBE_MAP_TEXTURE_SIZE),_=n.getParameter(n.MAX_VERTEX_ATTRIBS),v=n.getParameter(n.MAX_VERTEX_UNIFORM_VECTORS),M=n.getParameter(n.MAX_VARYING_VECTORS),y=n.getParameter(n.MAX_FRAGMENT_UNIFORM_VECTORS),T=n.getParameter(n.MAX_SAMPLES),S=n.getParameter(n.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:s,getMaxPrecision:l,textureFormatReadable:a,textureTypeReadable:o,precision:c,logarithmicDepthBuffer:f,reversedDepthBuffer:h,maxTextures:d,maxVertexTextures:g,maxTextureSize:m,maxCubemapSize:p,maxAttributes:_,maxVertexUniforms:v,maxVaryings:M,maxFragmentUniforms:y,maxSamples:T,samples:S}}function Cb(n){const e=this;let t=null,i=0,r=!1,s=!1;const a=new or,o=new rt,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(f,h){const d=f.length!==0||h||i!==0||r;return r=h,i=f.length,d},this.beginShadows=function(){s=!0,u(null)},this.endShadows=function(){s=!1},this.setGlobalState=function(f,h){t=u(f,h,0)},this.setState=function(f,h,d){const g=f.clippingPlanes,m=f.clipIntersection,p=f.clipShadows,_=n.get(f);if(!r||g===null||g.length===0||s&&!p)s?u(null):c();else{const v=s?0:i,M=v*4;let y=_.clippingState||null;l.value=y,y=u(g,h,M,d);for(let T=0;T!==M;++T)y[T]=t[T];_.clippingState=y,this.numIntersection=m?this.numPlanes:0,this.numPlanes+=v}};function c(){l.value!==t&&(l.value=t,l.needsUpdate=i>0),e.numPlanes=i,e.numIntersection=0}function u(f,h,d,g){const m=f!==null?f.length:0;let p=null;if(m!==0){if(p=l.value,g!==!0||p===null){const _=d+m*4,v=h.matrixWorldInverse;o.getNormalMatrix(v),(p===null||p.length<_)&&(p=new Float32Array(_));for(let M=0,y=d;M!==m;++M,y+=4)a.copy(f[M]).applyMatrix4(v,o),a.normal.toArray(p,y),p[y+3]=a.constant}l.value=p,l.needsUpdate=!0}return e.numPlanes=m,e.numIntersection=0,p}}const cr=4,Bd=[.125,.215,.35,.446,.526,.582],Nr=20,Pb=256,Ma=new rf,kd=new ut;let Bc=null,kc=0,zc=0,Gc=!1;const Db=new X;class zd{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._sigmas=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,i=.1,r=100,s={}){const{size:a=256,position:o=Db}=s;Bc=this._renderer.getRenderTarget(),kc=this._renderer.getActiveCubeFace(),zc=this._renderer.getActiveMipmapLevel(),Gc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);const l=this._allocateTargets();return l.depthBuffer=!0,this._sceneToCubeUV(e,i,r,l,o),t>0&&this._blur(l,0,0,t),this._applyPMREM(l),this._cleanup(l),l}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=Vd(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=Hd(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(Bc,kc,zc),this._renderer.xr.enabled=Gc,e.scissorTest=!1,ys(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===Yr||e.mapping===Bs?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),Bc=this._renderer.getRenderTarget(),kc=this._renderer.getActiveCubeFace(),zc=this._renderer.getActiveMipmapLevel(),Gc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const i=t||this._allocateTargets();return this._textureToCubeUV(e,i),this._applyPMREM(i),this._cleanup(i),i}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,i={magFilter:zt,minFilter:zt,generateMipmaps:!1,type:Vi,format:ci,colorSpace:zs,depthBuffer:!1},r=Gd(e,t,i);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=Gd(e,t,i);const{_lodMax:s}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods,sigmas:this._sigmas}=Ub(s)),this._blurMaterial=Ib(s,e,t),this._ggxMaterial=Lb(s,e,t)}return r}_compileMaterial(e){const t=new Wn(new At,e);this._renderer.compile(t,Ma)}_sceneToCubeUV(e,t,i,r,s){const l=new kn(90,1,t,i),c=[1,-1,1,1,1,1],u=[1,1,1,-1,-1,-1],f=this._renderer,h=f.autoClear,d=f.toneMapping;f.getClearColor(kd),f.toneMapping=Ai,f.autoClear=!1,f.state.buffers.depth.getReversed()&&(f.setRenderTarget(r),f.clearDepth(),f.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new Wn(new Za,new nf({name:"PMREM.Background",side:sn,depthWrite:!1,depthTest:!1})));const m=this._backgroundBox,p=m.material;let _=!1;const v=e.background;v?v.isColor&&(p.color.copy(v),e.background=null,_=!0):(p.color.copy(kd),_=!0);for(let M=0;M<6;M++){const y=M%3;y===0?(l.up.set(0,c[M],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x+u[M],s.y,s.z)):y===1?(l.up.set(0,0,c[M]),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y+u[M],s.z)):(l.up.set(0,c[M],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y,s.z+u[M]));const T=this._cubeSize;ys(r,y*T,M>2?T:0,T,T),f.setRenderTarget(r),_&&f.render(m,l),f.render(e,l)}f.toneMapping=d,f.autoClear=h,e.background=v}_textureToCubeUV(e,t){const i=this._renderer,r=e.mapping===Yr||e.mapping===Bs;r?(this._cubemapMaterial===null&&(this._cubemapMaterial=Vd()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=Hd());const s=r?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=s;const o=s.uniforms;o.envMap.value=e;const l=this._cubeSize;ys(t,0,0,3*l,2*l),i.setRenderTarget(t),i.render(a,Ma)}_applyPMREM(e){const t=this._renderer,i=t.autoClear;t.autoClear=!1;const r=this._lodMeshes.length;for(let s=1;s<r;s++)this._applyGGXFilter(e,s-1,s);t.autoClear=i}_applyGGXFilter(e,t,i){const r=this._renderer,s=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[i];o.material=a;const l=a.uniforms,c=i/(this._lodMeshes.length-1),u=t/(this._lodMeshes.length-1),f=Math.sqrt(c*c-u*u),h=0+c*1.25,d=f*h,{_lodMax:g}=this,m=this._sizeLods[i],p=3*m*(i>g-cr?i-g+cr:0),_=4*(this._cubeSize-m);l.envMap.value=e.texture,l.roughness.value=d,l.mipInt.value=g-t,ys(s,p,_,3*m,2*m),r.setRenderTarget(s),r.render(o,Ma),l.envMap.value=s.texture,l.roughness.value=0,l.mipInt.value=g-i,ys(e,p,_,3*m,2*m),r.setRenderTarget(e),r.render(o,Ma)}_blur(e,t,i,r,s){const a=this._pingPongRenderTarget;this._halfBlur(e,a,t,i,r,"latitudinal",s),this._halfBlur(a,e,i,i,r,"longitudinal",s)}_halfBlur(e,t,i,r,s,a,o){const l=this._renderer,c=this._blurMaterial;a!=="latitudinal"&&a!=="longitudinal"&&pt("blur direction must be either latitudinal or longitudinal!");const u=3,f=this._lodMeshes[r];f.material=c;const h=c.uniforms,d=this._sizeLods[i]-1,g=isFinite(s)?Math.PI/(2*d):2*Math.PI/(2*Nr-1),m=s/g,p=isFinite(s)?1+Math.floor(u*m):Nr;p>Nr&&Je(`sigmaRadians, ${s}, is too large and will clip, as it requested ${p} samples when the maximum is set to ${Nr}`);const _=[];let v=0;for(let E=0;E<Nr;++E){const b=E/m,x=Math.exp(-b*b/2);_.push(x),E===0?v+=x:E<p&&(v+=2*x)}for(let E=0;E<_.length;E++)_[E]=_[E]/v;h.envMap.value=e.texture,h.samples.value=p,h.weights.value=_,h.latitudinal.value=a==="latitudinal",o&&(h.poleAxis.value=o);const{_lodMax:M}=this;h.dTheta.value=g,h.mipInt.value=M-i;const y=this._sizeLods[r],T=3*y*(r>M-cr?r-M+cr:0),S=4*(this._cubeSize-y);ys(t,T,S,3*y,2*y),l.setRenderTarget(t),l.render(f,Ma)}}function Ub(n){const e=[],t=[],i=[];let r=n;const s=n-cr+1+Bd.length;for(let a=0;a<s;a++){const o=Math.pow(2,r);e.push(o);let l=1/o;a>n-cr?l=Bd[a-n+cr-1]:a===0&&(l=0),t.push(l);const c=1/(o-2),u=-c,f=1+c,h=[u,u,f,u,f,f,u,u,f,f,u,f],d=6,g=6,m=3,p=2,_=1,v=new Float32Array(m*g*d),M=new Float32Array(p*g*d),y=new Float32Array(_*g*d);for(let S=0;S<d;S++){const E=S%3*2/3-1,b=S>2?0:-1,x=[E,b,0,E+2/3,b,0,E+2/3,b+1,0,E,b,0,E+2/3,b+1,0,E,b+1,0];v.set(x,m*g*S),M.set(h,p*g*S);const A=[S,S,S,S,S,S];y.set(A,_*g*S)}const T=new At;T.setAttribute("position",new Ft(v,m)),T.setAttribute("uv",new Ft(M,p)),T.setAttribute("faceIndex",new Ft(y,_)),i.push(new Wn(T,null)),r>cr&&r--}return{lodMeshes:i,sizeLods:e,sigmas:t}}function Gd(n,e,t){const i=new $t(n,e,t);return i.texture.mapping=Ul,i.texture.name="PMREM.cubeUv",i.scissorTest=!0,i}function ys(n,e,t,i,r){n.viewport.set(e,t,i,r),n.scissor.set(e,t,i,r)}function Lb(n,e,t){return new an({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:Pb,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${n}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:Il(),fragmentShader:`

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
		`,blending:Mn,depthTest:!1,depthWrite:!1})}function Ib(n,e,t){const i=new Float32Array(Nr),r=new X(0,1,0);return new an({name:"SphericalGaussianBlur",defines:{n:Nr,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${n}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:i},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:r}},vertexShader:Il(),fragmentShader:`

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
		`,blending:Mn,depthTest:!1,depthWrite:!1})}function Hd(){return new an({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Il(),fragmentShader:`

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
		`,blending:Mn,depthTest:!1,depthWrite:!1})}function Vd(){return new an({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Il(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Mn,depthTest:!1,depthWrite:!1})}function Il(){return`

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
	`}class $m extends $t{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;const i={width:e,height:e,depth:1},r=[i,i,i,i,i,i];this.texture=new Hm(r),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;const i={uniforms:{tEquirect:{value:null}},vertexShader:`

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
			`},r=new Za(5,5,5),s=new an({name:"CubemapFromEquirect",uniforms:Gs(i.uniforms),vertexShader:i.vertexShader,fragmentShader:i.fragmentShader,side:sn,blending:Mn});s.uniforms.tEquirect.value=t;const a=new Wn(r,s),o=t.minFilter;return t.minFilter===Or&&(t.minFilter=zt),new Bv(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,i=!0,r=!0){const s=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,i,r);e.setRenderTarget(s)}}function Fb(n){let e=new WeakMap,t=new WeakMap,i=null;function r(h,d=!1){return h==null?null:d?a(h):s(h)}function s(h){if(h&&h.isTexture){const d=h.mapping;if(d===cc||d===uc)if(e.has(h)){const g=e.get(h).texture;return o(g,h.mapping)}else{const g=h.image;if(g&&g.height>0){const m=new $m(g.height);return m.fromEquirectangularTexture(n,h),e.set(h,m),h.addEventListener("dispose",c),o(m.texture,h.mapping)}else return null}}return h}function a(h){if(h&&h.isTexture){const d=h.mapping,g=d===cc||d===uc,m=d===Yr||d===Bs;if(g||m){let p=t.get(h);const _=p!==void 0?p.texture.pmremVersion:0;if(h.isRenderTargetTexture&&h.pmremVersion!==_)return i===null&&(i=new zd(n)),p=g?i.fromEquirectangular(h,p):i.fromCubemap(h,p),p.texture.pmremVersion=h.pmremVersion,t.set(h,p),p.texture;if(p!==void 0)return p.texture;{const v=h.image;return g&&v&&v.height>0||m&&v&&l(v)?(i===null&&(i=new zd(n)),p=g?i.fromEquirectangular(h):i.fromCubemap(h),p.texture.pmremVersion=h.pmremVersion,t.set(h,p),h.addEventListener("dispose",u),p.texture):null}}}return h}function o(h,d){return d===cc?h.mapping=Yr:d===uc&&(h.mapping=Bs),h}function l(h){let d=0;const g=6;for(let m=0;m<g;m++)h[m]!==void 0&&d++;return d===g}function c(h){const d=h.target;d.removeEventListener("dispose",c);const g=e.get(d);g!==void 0&&(e.delete(d),g.dispose())}function u(h){const d=h.target;d.removeEventListener("dispose",u);const g=t.get(d);g!==void 0&&(t.delete(d),g.dispose())}function f(){e=new WeakMap,t=new WeakMap,i!==null&&(i.dispose(),i=null)}return{get:r,dispose:f}}function Nb(n){const e={};function t(i){if(e[i]!==void 0)return e[i];const r=n.getExtension(i);return e[i]=r,r}return{has:function(i){return t(i)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(i){const r=t(i);return r===null&&ph("WebGLRenderer: "+i+" extension not supported."),r}}}function Ob(n,e,t,i){const r={},s=new WeakMap;function a(f){const h=f.target;h.index!==null&&e.remove(h.index);for(const g in h.attributes)e.remove(h.attributes[g]);h.removeEventListener("dispose",a),delete r[h.id];const d=s.get(h);d&&(e.remove(d),s.delete(h)),i.releaseStatesOfGeometry(h),h.isInstancedBufferGeometry===!0&&delete h._maxInstanceCount,t.memory.geometries--}function o(f,h){return r[h.id]===!0||(h.addEventListener("dispose",a),r[h.id]=!0,t.memory.geometries++),h}function l(f){const h=f.attributes;for(const d in h)e.update(h[d],n.ARRAY_BUFFER)}function c(f){const h=[],d=f.index,g=f.attributes.position;let m=0;if(g===void 0)return;if(d!==null){const v=d.array;m=d.version;for(let M=0,y=v.length;M<y;M+=3){const T=v[M+0],S=v[M+1],E=v[M+2];h.push(T,S,S,E,E,T)}}else{const v=g.array;m=g.version;for(let M=0,y=v.length/3-1;M<y;M+=3){const T=M+0,S=M+1,E=M+2;h.push(T,S,S,E,E,T)}}const p=new(g.count>=65535?km:Bm)(h,1);p.version=m;const _=s.get(f);_&&e.remove(_),s.set(f,p)}function u(f){const h=s.get(f);if(h){const d=f.index;d!==null&&h.version<d.version&&c(f)}else c(f);return s.get(f)}return{get:o,update:l,getWireframeAttribute:u}}function Bb(n,e,t){let i;function r(f){i=f}let s,a;function o(f){s=f.type,a=f.bytesPerElement}function l(f,h){n.drawElements(i,h,s,f*a),t.update(h,i,1)}function c(f,h,d){d!==0&&(n.drawElementsInstanced(i,h,s,f*a,d),t.update(h,i,d))}function u(f,h,d){if(d===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(i,h,0,s,f,0,d);let m=0;for(let p=0;p<d;p++)m+=h[p];t.update(m,i,1)}this.setMode=r,this.setIndex=o,this.render=l,this.renderInstances=c,this.renderMultiDraw=u}function kb(n){const e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function i(s,a,o){switch(t.calls++,a){case n.TRIANGLES:t.triangles+=o*(s/3);break;case n.LINES:t.lines+=o*(s/2);break;case n.LINE_STRIP:t.lines+=o*(s-1);break;case n.LINE_LOOP:t.lines+=o*s;break;case n.POINTS:t.points+=o*s;break;default:pt("WebGLInfo: Unknown draw mode:",a);break}}function r(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:r,update:i}}function zb(n,e,t){const i=new WeakMap,r=new Dt;function s(a,o,l){const c=a.morphTargetInfluences,u=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,f=u!==void 0?u.length:0;let h=i.get(o);if(h===void 0||h.count!==f){let x=function(){E.dispose(),i.delete(o),o.removeEventListener("dispose",x)};h!==void 0&&h.texture.dispose();const d=o.morphAttributes.position!==void 0,g=o.morphAttributes.normal!==void 0,m=o.morphAttributes.color!==void 0,p=o.morphAttributes.position||[],_=o.morphAttributes.normal||[],v=o.morphAttributes.color||[];let M=0;d===!0&&(M=1),g===!0&&(M=2),m===!0&&(M=3);let y=o.attributes.position.count*M,T=1;y>e.maxTextureSize&&(T=Math.ceil(y/e.maxTextureSize),y=e.maxTextureSize);const S=new Float32Array(y*T*4*f),E=new Fm(S,y,T,f);E.type=li,E.needsUpdate=!0;const b=M*4;for(let A=0;A<f;A++){const C=p[A],R=_[A],L=v[A],U=y*T*4*A;for(let I=0;I<C.count;I++){const F=I*b;d===!0&&(r.fromBufferAttribute(C,I),S[U+F+0]=r.x,S[U+F+1]=r.y,S[U+F+2]=r.z,S[U+F+3]=0),g===!0&&(r.fromBufferAttribute(R,I),S[U+F+4]=r.x,S[U+F+5]=r.y,S[U+F+6]=r.z,S[U+F+7]=0),m===!0&&(r.fromBufferAttribute(L,I),S[U+F+8]=r.x,S[U+F+9]=r.y,S[U+F+10]=r.z,S[U+F+11]=L.itemSize===4?r.w:1)}}h={count:f,texture:E,size:new Xe(y,T)},i.set(o,h),o.addEventListener("dispose",x)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)l.getUniforms().setValue(n,"morphTexture",a.morphTexture,t);else{let d=0;for(let m=0;m<c.length;m++)d+=c[m];const g=o.morphTargetsRelative?1:1-d;l.getUniforms().setValue(n,"morphTargetBaseInfluence",g),l.getUniforms().setValue(n,"morphTargetInfluences",c)}l.getUniforms().setValue(n,"morphTargetsTexture",h.texture,t),l.getUniforms().setValue(n,"morphTargetsTextureSize",h.size)}return{update:s}}function Gb(n,e,t,i,r){let s=new WeakMap;function a(c){const u=r.render.frame,f=c.geometry,h=e.get(c,f);if(s.get(h)!==u&&(e.update(h),s.set(h,u)),c.isInstancedMesh&&(c.hasEventListener("dispose",l)===!1&&c.addEventListener("dispose",l),s.get(c)!==u&&(t.update(c.instanceMatrix,n.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,n.ARRAY_BUFFER),s.set(c,u))),c.isSkinnedMesh){const d=c.skeleton;s.get(d)!==u&&(d.update(),s.set(d,u))}return h}function o(){s=new WeakMap}function l(c){const u=c.target;u.removeEventListener("dispose",l),i.releaseStatesOfObject(u),t.remove(u.instanceMatrix),u.instanceColor!==null&&t.remove(u.instanceColor)}return{update:a,dispose:o}}const Hb={[xm]:"LINEAR_TONE_MAPPING",[bm]:"REINHARD_TONE_MAPPING",[Mm]:"CINEON_TONE_MAPPING",[Sm]:"ACES_FILMIC_TONE_MAPPING",[Tm]:"AGX_TONE_MAPPING",[Em]:"NEUTRAL_TONE_MAPPING",[ym]:"CUSTOM_TONE_MAPPING"};function Vb(n,e,t,i,r){const s=new $t(e,t,{type:n,depthBuffer:i,stencilBuffer:r,depthTexture:i?new Gi(e,t):void 0}),a=new $t(e,t,{type:Vi,depthBuffer:!1,stencilBuffer:!1}),o=new At;o.setAttribute("position",new ui([-1,3,0,-1,-1,0,3,-1,0],3)),o.setAttribute("uv",new ui([0,2,0,0,2,0],2));const l=new Nv({uniforms:{tDiffuse:{value:null}},vertexShader:`
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
			}`,depthTest:!1,depthWrite:!1}),c=new Wn(o,l),u=new rf(-1,1,1,-1,0,1);let f=null,h=null,d=!1,g,m=null,p=[],_=!1;this.setSize=function(v,M){s.setSize(v,M),a.setSize(v,M);for(let y=0;y<p.length;y++){const T=p[y];T.setSize&&T.setSize(v,M)}},this.setEffects=function(v){p=v,_=p.length>0&&p[0].isRenderPass===!0;const M=s.width,y=s.height;for(let T=0;T<p.length;T++){const S=p[T];S.setSize&&S.setSize(M,y)}},this.begin=function(v,M){if(d||v.toneMapping===Ai&&p.length===0)return!1;if(m=M,M!==null){const y=M.width,T=M.height;(s.width!==y||s.height!==T)&&this.setSize(y,T)}return _===!1&&v.setRenderTarget(s),g=v.toneMapping,v.toneMapping=Ai,!0},this.hasRenderPass=function(){return _},this.end=function(v,M){v.toneMapping=g,d=!0;let y=s,T=a;for(let S=0;S<p.length;S++){const E=p[S];if(E.enabled!==!1&&(E.render(v,T,y,M),E.needsSwap!==!1)){const b=y;y=T,T=b}}if(f!==v.outputColorSpace||h!==v.toneMapping){f=v.outputColorSpace,h=v.toneMapping,l.defines={},ft.getTransfer(f)===Mt&&(l.defines.SRGB_TRANSFER="");const S=Hb[h];S&&(l.defines[S]=""),l.needsUpdate=!0}l.uniforms.tDiffuse.value=y.texture,v.setRenderTarget(m),v.render(c,u),m=null,d=!1},this.isCompositing=function(){return d},this.dispose=function(){s.depthTexture&&s.depthTexture.dispose(),s.dispose(),a.dispose(),o.dispose(),l.dispose()}}const Jm=new Zt,vh=new Gi(1,1),Qm=new Fm,e0=new uv,t0=new Hm,Wd=[],Xd=[],jd=new Float32Array(16),Yd=new Float32Array(9),qd=new Float32Array(4);function Zs(n,e,t){const i=n[0];if(i<=0||i>0)return n;const r=e*t;let s=Wd[r];if(s===void 0&&(s=new Float32Array(r),Wd[r]=s),e!==0){i.toArray(s,0);for(let a=1,o=0;a!==e;++a)o+=t,n[a].toArray(s,o)}return s}function Jt(n,e){if(n.length!==e.length)return!1;for(let t=0,i=n.length;t<i;t++)if(n[t]!==e[t])return!1;return!0}function Qt(n,e){for(let t=0,i=e.length;t<i;t++)n[t]=e[t]}function Fl(n,e){let t=Xd[e];t===void 0&&(t=new Int32Array(e),Xd[e]=t);for(let i=0;i!==e;++i)t[i]=n.allocateTextureUnit();return t}function Wb(n,e){const t=this.cache;t[0]!==e&&(n.uniform1f(this.addr,e),t[0]=e)}function Xb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Jt(t,e))return;n.uniform2fv(this.addr,e),Qt(t,e)}}function jb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(n.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(Jt(t,e))return;n.uniform3fv(this.addr,e),Qt(t,e)}}function Yb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Jt(t,e))return;n.uniform4fv(this.addr,e),Qt(t,e)}}function qb(n,e){const t=this.cache,i=e.elements;if(i===void 0){if(Jt(t,e))return;n.uniformMatrix2fv(this.addr,!1,e),Qt(t,e)}else{if(Jt(t,i))return;qd.set(i),n.uniformMatrix2fv(this.addr,!1,qd),Qt(t,i)}}function Kb(n,e){const t=this.cache,i=e.elements;if(i===void 0){if(Jt(t,e))return;n.uniformMatrix3fv(this.addr,!1,e),Qt(t,e)}else{if(Jt(t,i))return;Yd.set(i),n.uniformMatrix3fv(this.addr,!1,Yd),Qt(t,i)}}function Zb(n,e){const t=this.cache,i=e.elements;if(i===void 0){if(Jt(t,e))return;n.uniformMatrix4fv(this.addr,!1,e),Qt(t,e)}else{if(Jt(t,i))return;jd.set(i),n.uniformMatrix4fv(this.addr,!1,jd),Qt(t,i)}}function $b(n,e){const t=this.cache;t[0]!==e&&(n.uniform1i(this.addr,e),t[0]=e)}function Jb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Jt(t,e))return;n.uniform2iv(this.addr,e),Qt(t,e)}}function Qb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Jt(t,e))return;n.uniform3iv(this.addr,e),Qt(t,e)}}function eM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Jt(t,e))return;n.uniform4iv(this.addr,e),Qt(t,e)}}function tM(n,e){const t=this.cache;t[0]!==e&&(n.uniform1ui(this.addr,e),t[0]=e)}function nM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Jt(t,e))return;n.uniform2uiv(this.addr,e),Qt(t,e)}}function iM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Jt(t,e))return;n.uniform3uiv(this.addr,e),Qt(t,e)}}function rM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Jt(t,e))return;n.uniform4uiv(this.addr,e),Qt(t,e)}}function sM(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r);let s;this.type===n.SAMPLER_2D_SHADOW?(vh.compareFunction=t.isReversedDepthBuffer()?ef:Qh,s=vh):s=Jm,t.setTexture2D(e||s,r)}function aM(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r),t.setTexture3D(e||e0,r)}function oM(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r),t.setTextureCube(e||t0,r)}function lM(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r),t.setTexture2DArray(e||Qm,r)}function cM(n){switch(n){case 5126:return Wb;case 35664:return Xb;case 35665:return jb;case 35666:return Yb;case 35674:return qb;case 35675:return Kb;case 35676:return Zb;case 5124:case 35670:return $b;case 35667:case 35671:return Jb;case 35668:case 35672:return Qb;case 35669:case 35673:return eM;case 5125:return tM;case 36294:return nM;case 36295:return iM;case 36296:return rM;case 35678:case 36198:case 36298:case 36306:case 35682:return sM;case 35679:case 36299:case 36307:return aM;case 35680:case 36300:case 36308:case 36293:return oM;case 36289:case 36303:case 36311:case 36292:return lM}}function uM(n,e){n.uniform1fv(this.addr,e)}function hM(n,e){const t=Zs(e,this.size,2);n.uniform2fv(this.addr,t)}function fM(n,e){const t=Zs(e,this.size,3);n.uniform3fv(this.addr,t)}function dM(n,e){const t=Zs(e,this.size,4);n.uniform4fv(this.addr,t)}function pM(n,e){const t=Zs(e,this.size,4);n.uniformMatrix2fv(this.addr,!1,t)}function mM(n,e){const t=Zs(e,this.size,9);n.uniformMatrix3fv(this.addr,!1,t)}function gM(n,e){const t=Zs(e,this.size,16);n.uniformMatrix4fv(this.addr,!1,t)}function _M(n,e){n.uniform1iv(this.addr,e)}function vM(n,e){n.uniform2iv(this.addr,e)}function xM(n,e){n.uniform3iv(this.addr,e)}function bM(n,e){n.uniform4iv(this.addr,e)}function MM(n,e){n.uniform1uiv(this.addr,e)}function SM(n,e){n.uniform2uiv(this.addr,e)}function yM(n,e){n.uniform3uiv(this.addr,e)}function TM(n,e){n.uniform4uiv(this.addr,e)}function EM(n,e,t){const i=this.cache,r=e.length,s=Fl(t,r);Jt(i,s)||(n.uniform1iv(this.addr,s),Qt(i,s));let a;this.type===n.SAMPLER_2D_SHADOW?a=vh:a=Jm;for(let o=0;o!==r;++o)t.setTexture2D(e[o]||a,s[o])}function wM(n,e,t){const i=this.cache,r=e.length,s=Fl(t,r);Jt(i,s)||(n.uniform1iv(this.addr,s),Qt(i,s));for(let a=0;a!==r;++a)t.setTexture3D(e[a]||e0,s[a])}function AM(n,e,t){const i=this.cache,r=e.length,s=Fl(t,r);Jt(i,s)||(n.uniform1iv(this.addr,s),Qt(i,s));for(let a=0;a!==r;++a)t.setTextureCube(e[a]||t0,s[a])}function RM(n,e,t){const i=this.cache,r=e.length,s=Fl(t,r);Jt(i,s)||(n.uniform1iv(this.addr,s),Qt(i,s));for(let a=0;a!==r;++a)t.setTexture2DArray(e[a]||Qm,s[a])}function CM(n){switch(n){case 5126:return uM;case 35664:return hM;case 35665:return fM;case 35666:return dM;case 35674:return pM;case 35675:return mM;case 35676:return gM;case 5124:case 35670:return _M;case 35667:case 35671:return vM;case 35668:case 35672:return xM;case 35669:case 35673:return bM;case 5125:return MM;case 36294:return SM;case 36295:return yM;case 36296:return TM;case 35678:case 36198:case 36298:case 36306:case 35682:return EM;case 35679:case 36299:case 36307:return wM;case 35680:case 36300:case 36308:case 36293:return AM;case 36289:case 36303:case 36311:case 36292:return RM}}class PM{constructor(e,t,i){this.id=e,this.addr=i,this.cache=[],this.type=t.type,this.setValue=cM(t.type)}}class DM{constructor(e,t,i){this.id=e,this.addr=i,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=CM(t.type)}}class UM{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,i){const r=this.seq;for(let s=0,a=r.length;s!==a;++s){const o=r[s];o.setValue(e,t[o.id],i)}}}const Hc=/(\w+)(\])?(\[|\.)?/g;function Kd(n,e){n.seq.push(e),n.map[e.id]=e}function LM(n,e,t){const i=n.name,r=i.length;for(Hc.lastIndex=0;;){const s=Hc.exec(i),a=Hc.lastIndex;let o=s[1];const l=s[2]==="]",c=s[3];if(l&&(o=o|0),c===void 0||c==="["&&a+2===r){Kd(t,c===void 0?new PM(o,n,e):new DM(o,n,e));break}else{let f=t.map[o];f===void 0&&(f=new UM(o),Kd(t,f)),t=f}}}class Qo{constructor(e,t){this.seq=[],this.map={};const i=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let a=0;a<i;++a){const o=e.getActiveUniform(t,a),l=e.getUniformLocation(t,o.name);LM(o,l,this)}const r=[],s=[];for(const a of this.seq)a.type===e.SAMPLER_2D_SHADOW||a.type===e.SAMPLER_CUBE_SHADOW||a.type===e.SAMPLER_2D_ARRAY_SHADOW?r.push(a):s.push(a);r.length>0&&(this.seq=r.concat(s))}setValue(e,t,i,r){const s=this.map[t];s!==void 0&&s.setValue(e,i,r)}setOptional(e,t,i){const r=t[i];r!==void 0&&this.setValue(e,i,r)}static upload(e,t,i,r){for(let s=0,a=t.length;s!==a;++s){const o=t[s],l=i[o.id];l.needsUpdate!==!1&&o.setValue(e,l.value,r)}}static seqWithValue(e,t){const i=[];for(let r=0,s=e.length;r!==s;++r){const a=e[r];a.id in t&&i.push(a)}return i}}function Zd(n,e,t){const i=n.createShader(e);return n.shaderSource(i,t),n.compileShader(i),i}const IM=37297;let FM=0;function NM(n,e){const t=n.split(`
`),i=[],r=Math.max(e-6,0),s=Math.min(e+6,t.length);for(let a=r;a<s;a++){const o=a+1;i.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return i.join(`
`)}const $d=new rt;function OM(n){ft._getMatrix($d,ft.workingColorSpace,n);const e=`mat3( ${$d.elements.map(t=>t.toFixed(4))} )`;switch(ft.getTransfer(n)){case ul:return[e,"LinearTransferOETF"];case Mt:return[e,"sRGBTransferOETF"];default:return Je("WebGLProgram: Unsupported color space: ",n),[e,"LinearTransferOETF"]}}function Jd(n,e,t){const i=n.getShaderParameter(e,n.COMPILE_STATUS),s=(n.getShaderInfoLog(e)||"").trim();if(i&&s==="")return"";const a=/ERROR: 0:(\d+)/.exec(s);if(a){const o=parseInt(a[1]);return t.toUpperCase()+`

`+s+`

`+NM(n.getShaderSource(e),o)}else return s}function BM(n,e){const t=OM(e);return[`vec4 ${n}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}const kM={[xm]:"Linear",[bm]:"Reinhard",[Mm]:"Cineon",[Sm]:"ACESFilmic",[Tm]:"AgX",[Em]:"Neutral",[ym]:"Custom"};function zM(n,e){const t=kM[e];return t===void 0?(Je("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+n+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+n+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}const ko=new X;function GM(){ft.getLuminanceCoefficients(ko);const n=ko.x.toFixed(4),e=ko.y.toFixed(4),t=ko.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${n}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function HM(n){return[n.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",n.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Ra).join(`
`)}function VM(n){const e=[];for(const t in n){const i=n[t];i!==!1&&e.push("#define "+t+" "+i)}return e.join(`
`)}function WM(n,e){const t={},i=n.getProgramParameter(e,n.ACTIVE_ATTRIBUTES);for(let r=0;r<i;r++){const s=n.getActiveAttrib(e,r),a=s.name;let o=1;s.type===n.FLOAT_MAT2&&(o=2),s.type===n.FLOAT_MAT3&&(o=3),s.type===n.FLOAT_MAT4&&(o=4),t[a]={type:s.type,location:n.getAttribLocation(e,a),locationSize:o}}return t}function Ra(n){return n!==""}function Qd(n,e){const t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return n.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function ep(n,e){return n.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const XM=/^[ \t]*#include +<([\w\d./]+)>/gm;function xh(n){return n.replace(XM,YM)}const jM=new Map;function YM(n,e){let t=st[e];if(t===void 0){const i=jM.get(e);if(i!==void 0)t=st[i],Je('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,i);else throw new Error("Can not resolve #include <"+e+">")}return xh(t)}const qM=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function tp(n){return n.replace(qM,KM)}function KM(n,e,t,i){let r="";for(let s=parseInt(e);s<parseInt(t);s++)r+=i.replace(/\[\s*i\s*\]/g,"[ "+s+" ]").replace(/UNROLLED_LOOP_INDEX/g,s);return r}function np(n){let e=`precision ${n.precision} float;
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
#define LOW_PRECISION`),e}const ZM={[Yo]:"SHADOWMAP_TYPE_PCF",[wa]:"SHADOWMAP_TYPE_VSM"};function $M(n){return ZM[n.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}const JM={[Yr]:"ENVMAP_TYPE_CUBE",[Bs]:"ENVMAP_TYPE_CUBE",[Ul]:"ENVMAP_TYPE_CUBE_UV"};function QM(n){return n.envMap===!1?"ENVMAP_TYPE_CUBE":JM[n.envMapMode]||"ENVMAP_TYPE_CUBE"}const eS={[Bs]:"ENVMAP_MODE_REFRACTION"};function tS(n){return n.envMap===!1?"ENVMAP_MODE_REFLECTION":eS[n.envMapMode]||"ENVMAP_MODE_REFLECTION"}const nS={[vm]:"ENVMAP_BLENDING_MULTIPLY",[H_]:"ENVMAP_BLENDING_MIX",[V_]:"ENVMAP_BLENDING_ADD"};function iS(n){return n.envMap===!1?"ENVMAP_BLENDING_NONE":nS[n.combine]||"ENVMAP_BLENDING_NONE"}function rS(n){const e=n.envMapCubeUVHeight;if(e===null)return null;const t=Math.log2(e)-2,i=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:i,maxMip:t}}function sS(n,e,t,i){const r=n.getContext(),s=t.defines;let a=t.vertexShader,o=t.fragmentShader;const l=$M(t),c=QM(t),u=tS(t),f=iS(t),h=rS(t),d=HM(t),g=VM(s),m=r.createProgram();let p,_,v=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(p=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter(Ra).join(`
`),p.length>0&&(p+=`
`),_=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter(Ra).join(`
`),_.length>0&&(_+=`
`)):(p=[np(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+u:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexNormals?"#define HAS_NORMAL":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Ra).join(`
`),_=[np(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+c:"",t.envMap?"#define "+u:"",t.envMap?"#define "+f:"",h?"#define CUBEUV_TEXEL_WIDTH "+h.texelWidth:"",h?"#define CUBEUV_TEXEL_HEIGHT "+h.texelHeight:"",h?"#define CUBEUV_MAX_MIP "+h.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor?"#define USE_COLOR":"",t.vertexAlphas||t.batchingColor?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==Ai?"#define TONE_MAPPING":"",t.toneMapping!==Ai?st.tonemapping_pars_fragment:"",t.toneMapping!==Ai?zM("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",st.colorspace_pars_fragment,BM("linearToOutputTexel",t.outputColorSpace),GM(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter(Ra).join(`
`)),a=xh(a),a=Qd(a,t),a=ep(a,t),o=xh(o),o=Qd(o,t),o=ep(o,t),a=tp(a),o=tp(o),t.isRawShaderMaterial!==!0&&(v=`#version 300 es
`,p=[d,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+p,_=["#define varying in",t.glslVersion===ld?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===ld?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+_);const M=v+p+a,y=v+_+o,T=Zd(r,r.VERTEX_SHADER,M),S=Zd(r,r.FRAGMENT_SHADER,y);r.attachShader(m,T),r.attachShader(m,S),t.index0AttributeName!==void 0?r.bindAttribLocation(m,0,t.index0AttributeName):t.morphTargets===!0&&r.bindAttribLocation(m,0,"position"),r.linkProgram(m);function E(C){if(n.debug.checkShaderErrors){const R=r.getProgramInfoLog(m)||"",L=r.getShaderInfoLog(T)||"",U=r.getShaderInfoLog(S)||"",I=R.trim(),F=L.trim(),O=U.trim();let j=!0,G=!0;if(r.getProgramParameter(m,r.LINK_STATUS)===!1)if(j=!1,typeof n.debug.onShaderError=="function")n.debug.onShaderError(r,m,T,S);else{const W=Jd(r,T,"vertex"),N=Jd(r,S,"fragment");pt("THREE.WebGLProgram: Shader Error "+r.getError()+" - VALIDATE_STATUS "+r.getProgramParameter(m,r.VALIDATE_STATUS)+`

Material Name: `+C.name+`
Material Type: `+C.type+`

Program Info Log: `+I+`
`+W+`
`+N)}else I!==""?Je("WebGLProgram: Program Info Log:",I):(F===""||O==="")&&(G=!1);G&&(C.diagnostics={runnable:j,programLog:I,vertexShader:{log:F,prefix:p},fragmentShader:{log:O,prefix:_}})}r.deleteShader(T),r.deleteShader(S),b=new Qo(r,m),x=WM(r,m)}let b;this.getUniforms=function(){return b===void 0&&E(this),b};let x;this.getAttributes=function(){return x===void 0&&E(this),x};let A=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return A===!1&&(A=r.getProgramParameter(m,IM)),A},this.destroy=function(){i.releaseStatesOfProgram(this),r.deleteProgram(m),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=FM++,this.cacheKey=e,this.usedTimes=1,this.program=m,this.vertexShader=T,this.fragmentShader=S,this}let aS=0;class oS{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){const t=e.vertexShader,i=e.fragmentShader,r=this._getShaderStage(t),s=this._getShaderStage(i),a=this._getShaderCacheForMaterial(e);return a.has(r)===!1&&(a.add(r),r.usedTimes++),a.has(s)===!1&&(a.add(s),s.usedTimes++),this}remove(e){const t=this.materialCache.get(e);for(const i of t)i.usedTimes--,i.usedTimes===0&&this.shaderCache.delete(i.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const t=this.materialCache;let i=t.get(e);return i===void 0&&(i=new Set,t.set(e,i)),i}_getShaderStage(e){const t=this.shaderCache;let i=t.get(e);return i===void 0&&(i=new lS(e),t.set(e,i)),i}}class lS{constructor(e){this.id=aS++,this.code=e,this.usedTimes=0}}function cS(n){return n===qr||n===ll||n===cl}function uS(n,e,t,i,r,s){const a=new Nm,o=new oS,l=new Set,c=[],u=new Map,f=i.logarithmicDepthBuffer;let h=i.precision;const d={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function g(b){return l.add(b),b===0?"uv":`uv${b}`}function m(b,x,A,C,R,L){const U=C.fog,I=R.geometry,F=b.isMeshStandardMaterial||b.isMeshLambertMaterial||b.isMeshPhongMaterial?C.environment:null,O=b.isMeshStandardMaterial||b.isMeshLambertMaterial&&!b.envMap||b.isMeshPhongMaterial&&!b.envMap,j=e.get(b.envMap||F,O),G=j&&j.mapping===Ul?j.image.height:null,W=d[b.type];b.precision!==null&&(h=i.getMaxPrecision(b.precision),h!==b.precision&&Je("WebGLProgram.getParameters:",b.precision,"not supported, using",h,"instead."));const N=I.morphAttributes.position||I.morphAttributes.normal||I.morphAttributes.color,k=N!==void 0?N.length:0;let J=0;I.morphAttributes.position!==void 0&&(J=1),I.morphAttributes.normal!==void 0&&(J=2),I.morphAttributes.color!==void 0&&(J=3);let Q,K,H,Y;if(W){const Ze=xi[W];Q=Ze.vertexShader,K=Ze.fragmentShader}else Q=b.vertexShader,K=b.fragmentShader,o.update(b),H=o.getVertexShaderID(b),Y=o.getFragmentShaderID(b);const Z=n.getRenderTarget(),fe=n.state.buffers.depth.getReversed(),Me=R.isInstancedMesh===!0,ce=R.isBatchedMesh===!0,de=!!b.map,Ne=!!b.matcap,Oe=!!j,Ce=!!b.aoMap,Te=!!b.lightMap,Ge=!!b.bumpMap,_e=!!b.normalMap,ze=!!b.displacementMap,B=!!b.emissiveMap,ue=!!b.metalnessMap,Le=!!b.roughnessMap,Ee=b.anisotropy>0,le=b.clearcoat>0,we=b.dispersion>0,D=b.iridescence>0,w=b.sheen>0,z=b.transmission>0,$=Ee&&!!b.anisotropyMap,oe=le&&!!b.clearcoatMap,ge=le&&!!b.clearcoatNormalMap,be=le&&!!b.clearcoatRoughnessMap,ee=D&&!!b.iridescenceMap,re=D&&!!b.iridescenceThicknessMap,he=w&&!!b.sheenColorMap,Pe=w&&!!b.sheenRoughnessMap,ve=!!b.specularMap,Se=!!b.specularColorMap,He=!!b.specularIntensityMap,De=z&&!!b.transmissionMap,Ye=z&&!!b.thicknessMap,V=!!b.gradientMap,pe=!!b.alphaMap,ie=b.alphaTest>0,Re=!!b.alphaHash,xe=!!b.extensions;let ae=Ai;b.toneMapped&&(Z===null||Z.isXRRenderTarget===!0)&&(ae=n.toneMapping);const Ue={shaderID:W,shaderType:b.type,shaderName:b.name,vertexShader:Q,fragmentShader:K,defines:b.defines,customVertexShaderID:H,customFragmentShaderID:Y,isRawShaderMaterial:b.isRawShaderMaterial===!0,glslVersion:b.glslVersion,precision:h,batching:ce,batchingColor:ce&&R._colorsTexture!==null,instancing:Me,instancingColor:Me&&R.instanceColor!==null,instancingMorph:Me&&R.morphTexture!==null,outputColorSpace:Z===null?n.outputColorSpace:Z.isXRRenderTarget===!0?Z.texture.colorSpace:ft.workingColorSpace,alphaToCoverage:!!b.alphaToCoverage,map:de,matcap:Ne,envMap:Oe,envMapMode:Oe&&j.mapping,envMapCubeUVHeight:G,aoMap:Ce,lightMap:Te,bumpMap:Ge,normalMap:_e,displacementMap:ze,emissiveMap:B,normalMapObjectSpace:_e&&b.normalMapType===j_,normalMapTangentSpace:_e&&b.normalMapType===ad,packedNormalMap:_e&&b.normalMapType===ad&&cS(b.normalMap.format),metalnessMap:ue,roughnessMap:Le,anisotropy:Ee,anisotropyMap:$,clearcoat:le,clearcoatMap:oe,clearcoatNormalMap:ge,clearcoatRoughnessMap:be,dispersion:we,iridescence:D,iridescenceMap:ee,iridescenceThicknessMap:re,sheen:w,sheenColorMap:he,sheenRoughnessMap:Pe,specularMap:ve,specularColorMap:Se,specularIntensityMap:He,transmission:z,transmissionMap:De,thicknessMap:Ye,gradientMap:V,opaque:b.transparent===!1&&b.blending===kr&&b.alphaToCoverage===!1,alphaMap:pe,alphaTest:ie,alphaHash:Re,combine:b.combine,mapUv:de&&g(b.map.channel),aoMapUv:Ce&&g(b.aoMap.channel),lightMapUv:Te&&g(b.lightMap.channel),bumpMapUv:Ge&&g(b.bumpMap.channel),normalMapUv:_e&&g(b.normalMap.channel),displacementMapUv:ze&&g(b.displacementMap.channel),emissiveMapUv:B&&g(b.emissiveMap.channel),metalnessMapUv:ue&&g(b.metalnessMap.channel),roughnessMapUv:Le&&g(b.roughnessMap.channel),anisotropyMapUv:$&&g(b.anisotropyMap.channel),clearcoatMapUv:oe&&g(b.clearcoatMap.channel),clearcoatNormalMapUv:ge&&g(b.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:be&&g(b.clearcoatRoughnessMap.channel),iridescenceMapUv:ee&&g(b.iridescenceMap.channel),iridescenceThicknessMapUv:re&&g(b.iridescenceThicknessMap.channel),sheenColorMapUv:he&&g(b.sheenColorMap.channel),sheenRoughnessMapUv:Pe&&g(b.sheenRoughnessMap.channel),specularMapUv:ve&&g(b.specularMap.channel),specularColorMapUv:Se&&g(b.specularColorMap.channel),specularIntensityMapUv:He&&g(b.specularIntensityMap.channel),transmissionMapUv:De&&g(b.transmissionMap.channel),thicknessMapUv:Ye&&g(b.thicknessMap.channel),alphaMapUv:pe&&g(b.alphaMap.channel),vertexTangents:!!I.attributes.tangent&&(_e||Ee),vertexNormals:!!I.attributes.normal,vertexColors:b.vertexColors,vertexAlphas:b.vertexColors===!0&&!!I.attributes.color&&I.attributes.color.itemSize===4,pointsUvs:R.isPoints===!0&&!!I.attributes.uv&&(de||pe),fog:!!U,useFog:b.fog===!0,fogExp2:!!U&&U.isFogExp2,flatShading:b.wireframe===!1&&(b.flatShading===!0||I.attributes.normal===void 0&&_e===!1&&(b.isMeshLambertMaterial||b.isMeshPhongMaterial||b.isMeshStandardMaterial||b.isMeshPhysicalMaterial)),sizeAttenuation:b.sizeAttenuation===!0,logarithmicDepthBuffer:f,reversedDepthBuffer:fe,skinning:R.isSkinnedMesh===!0,morphTargets:I.morphAttributes.position!==void 0,morphNormals:I.morphAttributes.normal!==void 0,morphColors:I.morphAttributes.color!==void 0,morphTargetsCount:k,morphTextureStride:J,numDirLights:x.directional.length,numPointLights:x.point.length,numSpotLights:x.spot.length,numSpotLightMaps:x.spotLightMap.length,numRectAreaLights:x.rectArea.length,numHemiLights:x.hemi.length,numDirLightShadows:x.directionalShadowMap.length,numPointLightShadows:x.pointShadowMap.length,numSpotLightShadows:x.spotShadowMap.length,numSpotLightShadowsWithMaps:x.numSpotLightShadowsWithMaps,numLightProbes:x.numLightProbes,numLightProbeGrids:L.length,numClippingPlanes:s.numPlanes,numClipIntersection:s.numIntersection,dithering:b.dithering,shadowMapEnabled:n.shadowMap.enabled&&A.length>0,shadowMapType:n.shadowMap.type,toneMapping:ae,decodeVideoTexture:de&&b.map.isVideoTexture===!0&&ft.getTransfer(b.map.colorSpace)===Mt,decodeVideoTextureEmissive:B&&b.emissiveMap.isVideoTexture===!0&&ft.getTransfer(b.emissiveMap.colorSpace)===Mt,premultipliedAlpha:b.premultipliedAlpha,doubleSided:b.side===En,flipSided:b.side===sn,useDepthPacking:b.depthPacking>=0,depthPacking:b.depthPacking||0,index0AttributeName:b.index0AttributeName,extensionClipCullDistance:xe&&b.extensions.clipCullDistance===!0&&t.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(xe&&b.extensions.multiDraw===!0||ce)&&t.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:t.has("KHR_parallel_shader_compile"),customProgramCacheKey:b.customProgramCacheKey()};return Ue.vertexUv1s=l.has(1),Ue.vertexUv2s=l.has(2),Ue.vertexUv3s=l.has(3),l.clear(),Ue}function p(b){const x=[];if(b.shaderID?x.push(b.shaderID):(x.push(b.customVertexShaderID),x.push(b.customFragmentShaderID)),b.defines!==void 0)for(const A in b.defines)x.push(A),x.push(b.defines[A]);return b.isRawShaderMaterial===!1&&(_(x,b),v(x,b),x.push(n.outputColorSpace)),x.push(b.customProgramCacheKey),x.join()}function _(b,x){b.push(x.precision),b.push(x.outputColorSpace),b.push(x.envMapMode),b.push(x.envMapCubeUVHeight),b.push(x.mapUv),b.push(x.alphaMapUv),b.push(x.lightMapUv),b.push(x.aoMapUv),b.push(x.bumpMapUv),b.push(x.normalMapUv),b.push(x.displacementMapUv),b.push(x.emissiveMapUv),b.push(x.metalnessMapUv),b.push(x.roughnessMapUv),b.push(x.anisotropyMapUv),b.push(x.clearcoatMapUv),b.push(x.clearcoatNormalMapUv),b.push(x.clearcoatRoughnessMapUv),b.push(x.iridescenceMapUv),b.push(x.iridescenceThicknessMapUv),b.push(x.sheenColorMapUv),b.push(x.sheenRoughnessMapUv),b.push(x.specularMapUv),b.push(x.specularColorMapUv),b.push(x.specularIntensityMapUv),b.push(x.transmissionMapUv),b.push(x.thicknessMapUv),b.push(x.combine),b.push(x.fogExp2),b.push(x.sizeAttenuation),b.push(x.morphTargetsCount),b.push(x.morphAttributeCount),b.push(x.numDirLights),b.push(x.numPointLights),b.push(x.numSpotLights),b.push(x.numSpotLightMaps),b.push(x.numHemiLights),b.push(x.numRectAreaLights),b.push(x.numDirLightShadows),b.push(x.numPointLightShadows),b.push(x.numSpotLightShadows),b.push(x.numSpotLightShadowsWithMaps),b.push(x.numLightProbes),b.push(x.shadowMapType),b.push(x.toneMapping),b.push(x.numClippingPlanes),b.push(x.numClipIntersection),b.push(x.depthPacking)}function v(b,x){a.disableAll(),x.instancing&&a.enable(0),x.instancingColor&&a.enable(1),x.instancingMorph&&a.enable(2),x.matcap&&a.enable(3),x.envMap&&a.enable(4),x.normalMapObjectSpace&&a.enable(5),x.normalMapTangentSpace&&a.enable(6),x.clearcoat&&a.enable(7),x.iridescence&&a.enable(8),x.alphaTest&&a.enable(9),x.vertexColors&&a.enable(10),x.vertexAlphas&&a.enable(11),x.vertexUv1s&&a.enable(12),x.vertexUv2s&&a.enable(13),x.vertexUv3s&&a.enable(14),x.vertexTangents&&a.enable(15),x.anisotropy&&a.enable(16),x.alphaHash&&a.enable(17),x.batching&&a.enable(18),x.dispersion&&a.enable(19),x.batchingColor&&a.enable(20),x.gradientMap&&a.enable(21),x.packedNormalMap&&a.enable(22),x.vertexNormals&&a.enable(23),b.push(a.mask),a.disableAll(),x.fog&&a.enable(0),x.useFog&&a.enable(1),x.flatShading&&a.enable(2),x.logarithmicDepthBuffer&&a.enable(3),x.reversedDepthBuffer&&a.enable(4),x.skinning&&a.enable(5),x.morphTargets&&a.enable(6),x.morphNormals&&a.enable(7),x.morphColors&&a.enable(8),x.premultipliedAlpha&&a.enable(9),x.shadowMapEnabled&&a.enable(10),x.doubleSided&&a.enable(11),x.flipSided&&a.enable(12),x.useDepthPacking&&a.enable(13),x.dithering&&a.enable(14),x.transmission&&a.enable(15),x.sheen&&a.enable(16),x.opaque&&a.enable(17),x.pointsUvs&&a.enable(18),x.decodeVideoTexture&&a.enable(19),x.decodeVideoTextureEmissive&&a.enable(20),x.alphaToCoverage&&a.enable(21),x.numLightProbeGrids>0&&a.enable(22),b.push(a.mask)}function M(b){const x=d[b.type];let A;if(x){const C=xi[x];A=Xm.clone(C.uniforms)}else A=b.uniforms;return A}function y(b,x){let A=u.get(x);return A!==void 0?++A.usedTimes:(A=new sS(n,x,b,r),c.push(A),u.set(x,A)),A}function T(b){if(--b.usedTimes===0){const x=c.indexOf(b);c[x]=c[c.length-1],c.pop(),u.delete(b.cacheKey),b.destroy()}}function S(b){o.remove(b)}function E(){o.dispose()}return{getParameters:m,getProgramCacheKey:p,getUniforms:M,acquireProgram:y,releaseProgram:T,releaseShaderCache:S,programs:c,dispose:E}}function hS(){let n=new WeakMap;function e(a){return n.has(a)}function t(a){let o=n.get(a);return o===void 0&&(o={},n.set(a,o)),o}function i(a){n.delete(a)}function r(a,o,l){n.get(a)[o]=l}function s(){n=new WeakMap}return{has:e,get:t,remove:i,update:r,dispose:s}}function fS(n,e){return n.groupOrder!==e.groupOrder?n.groupOrder-e.groupOrder:n.renderOrder!==e.renderOrder?n.renderOrder-e.renderOrder:n.material.id!==e.material.id?n.material.id-e.material.id:n.materialVariant!==e.materialVariant?n.materialVariant-e.materialVariant:n.z!==e.z?n.z-e.z:n.id-e.id}function ip(n,e){return n.groupOrder!==e.groupOrder?n.groupOrder-e.groupOrder:n.renderOrder!==e.renderOrder?n.renderOrder-e.renderOrder:n.z!==e.z?e.z-n.z:n.id-e.id}function rp(){const n=[];let e=0;const t=[],i=[],r=[];function s(){e=0,t.length=0,i.length=0,r.length=0}function a(h){let d=0;return h.isInstancedMesh&&(d+=2),h.isSkinnedMesh&&(d+=1),d}function o(h,d,g,m,p,_){let v=n[e];return v===void 0?(v={id:h.id,object:h,geometry:d,material:g,materialVariant:a(h),groupOrder:m,renderOrder:h.renderOrder,z:p,group:_},n[e]=v):(v.id=h.id,v.object=h,v.geometry=d,v.material=g,v.materialVariant=a(h),v.groupOrder=m,v.renderOrder=h.renderOrder,v.z=p,v.group=_),e++,v}function l(h,d,g,m,p,_){const v=o(h,d,g,m,p,_);g.transmission>0?i.push(v):g.transparent===!0?r.push(v):t.push(v)}function c(h,d,g,m,p,_){const v=o(h,d,g,m,p,_);g.transmission>0?i.unshift(v):g.transparent===!0?r.unshift(v):t.unshift(v)}function u(h,d){t.length>1&&t.sort(h||fS),i.length>1&&i.sort(d||ip),r.length>1&&r.sort(d||ip)}function f(){for(let h=e,d=n.length;h<d;h++){const g=n[h];if(g.id===null)break;g.id=null,g.object=null,g.geometry=null,g.material=null,g.group=null}}return{opaque:t,transmissive:i,transparent:r,init:s,push:l,unshift:c,finish:f,sort:u}}function dS(){let n=new WeakMap;function e(i,r){const s=n.get(i);let a;return s===void 0?(a=new rp,n.set(i,[a])):r>=s.length?(a=new rp,s.push(a)):a=s[r],a}function t(){n=new WeakMap}return{get:e,dispose:t}}function pS(){const n={};return{get:function(e){if(n[e.id]!==void 0)return n[e.id];let t;switch(e.type){case"DirectionalLight":t={direction:new X,color:new ut};break;case"SpotLight":t={position:new X,direction:new X,color:new ut,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new X,color:new ut,distance:0,decay:0};break;case"HemisphereLight":t={direction:new X,skyColor:new ut,groundColor:new ut};break;case"RectAreaLight":t={color:new ut,position:new X,halfWidth:new X,halfHeight:new X};break}return n[e.id]=t,t}}}function mS(){const n={};return{get:function(e){if(n[e.id]!==void 0)return n[e.id];let t;switch(e.type){case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe,shadowCameraNear:1,shadowCameraFar:1e3};break}return n[e.id]=t,t}}}let gS=0;function _S(n,e){return(e.castShadow?2:0)-(n.castShadow?2:0)+(e.map?1:0)-(n.map?1:0)}function vS(n){const e=new pS,t=mS(),i={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)i.probe.push(new X);const r=new X,s=new kt,a=new kt;function o(c){let u=0,f=0,h=0;for(let x=0;x<9;x++)i.probe[x].set(0,0,0);let d=0,g=0,m=0,p=0,_=0,v=0,M=0,y=0,T=0,S=0,E=0;c.sort(_S);for(let x=0,A=c.length;x<A;x++){const C=c[x],R=C.color,L=C.intensity,U=C.distance;let I=null;if(C.shadow&&C.shadow.map&&(C.shadow.map.texture.format===qr?I=C.shadow.map.texture:I=C.shadow.map.depthTexture||C.shadow.map.texture),C.isAmbientLight)u+=R.r*L,f+=R.g*L,h+=R.b*L;else if(C.isLightProbe){for(let F=0;F<9;F++)i.probe[F].addScaledVector(C.sh.coefficients[F],L);E++}else if(C.isDirectionalLight){const F=e.get(C);if(F.color.copy(C.color).multiplyScalar(C.intensity),C.castShadow){const O=C.shadow,j=t.get(C);j.shadowIntensity=O.intensity,j.shadowBias=O.bias,j.shadowNormalBias=O.normalBias,j.shadowRadius=O.radius,j.shadowMapSize=O.mapSize,i.directionalShadow[d]=j,i.directionalShadowMap[d]=I,i.directionalShadowMatrix[d]=C.shadow.matrix,v++}i.directional[d]=F,d++}else if(C.isSpotLight){const F=e.get(C);F.position.setFromMatrixPosition(C.matrixWorld),F.color.copy(R).multiplyScalar(L),F.distance=U,F.coneCos=Math.cos(C.angle),F.penumbraCos=Math.cos(C.angle*(1-C.penumbra)),F.decay=C.decay,i.spot[m]=F;const O=C.shadow;if(C.map&&(i.spotLightMap[T]=C.map,T++,O.updateMatrices(C),C.castShadow&&S++),i.spotLightMatrix[m]=O.matrix,C.castShadow){const j=t.get(C);j.shadowIntensity=O.intensity,j.shadowBias=O.bias,j.shadowNormalBias=O.normalBias,j.shadowRadius=O.radius,j.shadowMapSize=O.mapSize,i.spotShadow[m]=j,i.spotShadowMap[m]=I,y++}m++}else if(C.isRectAreaLight){const F=e.get(C);F.color.copy(R).multiplyScalar(L),F.halfWidth.set(C.width*.5,0,0),F.halfHeight.set(0,C.height*.5,0),i.rectArea[p]=F,p++}else if(C.isPointLight){const F=e.get(C);if(F.color.copy(C.color).multiplyScalar(C.intensity),F.distance=C.distance,F.decay=C.decay,C.castShadow){const O=C.shadow,j=t.get(C);j.shadowIntensity=O.intensity,j.shadowBias=O.bias,j.shadowNormalBias=O.normalBias,j.shadowRadius=O.radius,j.shadowMapSize=O.mapSize,j.shadowCameraNear=O.camera.near,j.shadowCameraFar=O.camera.far,i.pointShadow[g]=j,i.pointShadowMap[g]=I,i.pointShadowMatrix[g]=C.shadow.matrix,M++}i.point[g]=F,g++}else if(C.isHemisphereLight){const F=e.get(C);F.skyColor.copy(C.color).multiplyScalar(L),F.groundColor.copy(C.groundColor).multiplyScalar(L),i.hemi[_]=F,_++}}p>0&&(n.has("OES_texture_float_linear")===!0?(i.rectAreaLTC1=ke.LTC_FLOAT_1,i.rectAreaLTC2=ke.LTC_FLOAT_2):(i.rectAreaLTC1=ke.LTC_HALF_1,i.rectAreaLTC2=ke.LTC_HALF_2)),i.ambient[0]=u,i.ambient[1]=f,i.ambient[2]=h;const b=i.hash;(b.directionalLength!==d||b.pointLength!==g||b.spotLength!==m||b.rectAreaLength!==p||b.hemiLength!==_||b.numDirectionalShadows!==v||b.numPointShadows!==M||b.numSpotShadows!==y||b.numSpotMaps!==T||b.numLightProbes!==E)&&(i.directional.length=d,i.spot.length=m,i.rectArea.length=p,i.point.length=g,i.hemi.length=_,i.directionalShadow.length=v,i.directionalShadowMap.length=v,i.pointShadow.length=M,i.pointShadowMap.length=M,i.spotShadow.length=y,i.spotShadowMap.length=y,i.directionalShadowMatrix.length=v,i.pointShadowMatrix.length=M,i.spotLightMatrix.length=y+T-S,i.spotLightMap.length=T,i.numSpotLightShadowsWithMaps=S,i.numLightProbes=E,b.directionalLength=d,b.pointLength=g,b.spotLength=m,b.rectAreaLength=p,b.hemiLength=_,b.numDirectionalShadows=v,b.numPointShadows=M,b.numSpotShadows=y,b.numSpotMaps=T,b.numLightProbes=E,i.version=gS++)}function l(c,u){let f=0,h=0,d=0,g=0,m=0;const p=u.matrixWorldInverse;for(let _=0,v=c.length;_<v;_++){const M=c[_];if(M.isDirectionalLight){const y=i.directional[f];y.direction.setFromMatrixPosition(M.matrixWorld),r.setFromMatrixPosition(M.target.matrixWorld),y.direction.sub(r),y.direction.transformDirection(p),f++}else if(M.isSpotLight){const y=i.spot[d];y.position.setFromMatrixPosition(M.matrixWorld),y.position.applyMatrix4(p),y.direction.setFromMatrixPosition(M.matrixWorld),r.setFromMatrixPosition(M.target.matrixWorld),y.direction.sub(r),y.direction.transformDirection(p),d++}else if(M.isRectAreaLight){const y=i.rectArea[g];y.position.setFromMatrixPosition(M.matrixWorld),y.position.applyMatrix4(p),a.identity(),s.copy(M.matrixWorld),s.premultiply(p),a.extractRotation(s),y.halfWidth.set(M.width*.5,0,0),y.halfHeight.set(0,M.height*.5,0),y.halfWidth.applyMatrix4(a),y.halfHeight.applyMatrix4(a),g++}else if(M.isPointLight){const y=i.point[h];y.position.setFromMatrixPosition(M.matrixWorld),y.position.applyMatrix4(p),h++}else if(M.isHemisphereLight){const y=i.hemi[m];y.direction.setFromMatrixPosition(M.matrixWorld),y.direction.transformDirection(p),m++}}}return{setup:o,setupView:l,state:i}}function sp(n){const e=new vS(n),t=[],i=[],r=[];function s(h){f.camera=h,t.length=0,i.length=0,r.length=0}function a(h){t.push(h)}function o(h){i.push(h)}function l(h){r.push(h)}function c(){e.setup(t)}function u(h){e.setupView(t,h)}const f={lightsArray:t,shadowsArray:i,lightProbeGridArray:r,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:s,state:f,setupLights:c,setupLightsView:u,pushLight:a,pushShadow:o,pushLightProbeGrid:l}}function xS(n){let e=new WeakMap;function t(r,s=0){const a=e.get(r);let o;return a===void 0?(o=new sp(n),e.set(r,[o])):s>=a.length?(o=new sp(n),a.push(o)):o=a[s],o}function i(){e=new WeakMap}return{get:t,dispose:i}}const bS=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,MS=`uniform sampler2D shadow_pass;
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
}`,SS=[new X(1,0,0),new X(-1,0,0),new X(0,1,0),new X(0,-1,0),new X(0,0,1),new X(0,0,-1)],yS=[new X(0,-1,0),new X(0,-1,0),new X(0,0,1),new X(0,0,-1),new X(0,-1,0),new X(0,-1,0)],ap=new kt,Sa=new X,Vc=new X;function TS(n,e,t){let i=new Gm;const r=new Xe,s=new Xe,a=new Dt,o=new jm,l=new Ym,c={},u=t.maxTextureSize,f={[Hi]:sn,[sn]:Hi,[En]:En},h=new an({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Xe},radius:{value:4}},vertexShader:bS,fragmentShader:MS}),d=h.clone();d.defines.HORIZONTAL_PASS=1;const g=new At;g.setAttribute("position",new Ft(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const m=new Wn(g,h),p=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Yo;let _=this.type;this.render=function(S,E,b){if(p.enabled===!1||p.autoUpdate===!1&&p.needsUpdate===!1||S.length===0)return;this.type===y_&&(Je("WebGLShadowMap: PCFSoftShadowMap has been deprecated. Using PCFShadowMap instead."),this.type=Yo);const x=n.getRenderTarget(),A=n.getActiveCubeFace(),C=n.getActiveMipmapLevel(),R=n.state;R.setBlending(Mn),R.buffers.depth.getReversed()===!0?R.buffers.color.setClear(0,0,0,0):R.buffers.color.setClear(1,1,1,1),R.buffers.depth.setTest(!0),R.setScissorTest(!1);const L=_!==this.type;L&&E.traverse(function(U){U.material&&(Array.isArray(U.material)?U.material.forEach(I=>I.needsUpdate=!0):U.material.needsUpdate=!0)});for(let U=0,I=S.length;U<I;U++){const F=S[U],O=F.shadow;if(O===void 0){Je("WebGLShadowMap:",F,"has no shadow.");continue}if(O.autoUpdate===!1&&O.needsUpdate===!1)continue;r.copy(O.mapSize);const j=O.getFrameExtents();r.multiply(j),s.copy(O.mapSize),(r.x>u||r.y>u)&&(r.x>u&&(s.x=Math.floor(u/j.x),r.x=s.x*j.x,O.mapSize.x=s.x),r.y>u&&(s.y=Math.floor(u/j.y),r.y=s.y*j.y,O.mapSize.y=s.y));const G=n.state.buffers.depth.getReversed();if(O.camera._reversedDepth=G,O.map===null||L===!0){if(O.map!==null&&(O.map.depthTexture!==null&&(O.map.depthTexture.dispose(),O.map.depthTexture=null),O.map.dispose()),this.type===wa){if(F.isPointLight){Je("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}O.map=new $t(r.x,r.y,{format:qr,type:Vi,minFilter:zt,magFilter:zt,generateMipmaps:!1}),O.map.texture.name=F.name+".shadowMap",O.map.depthTexture=new Gi(r.x,r.y,li),O.map.depthTexture.name=F.name+".shadowMapDepth",O.map.depthTexture.format=Wi,O.map.depthTexture.compareFunction=null,O.map.depthTexture.minFilter=cn,O.map.depthTexture.magFilter=cn}else F.isPointLight?(O.map=new $m(r.x),O.map.depthTexture=new Uv(r.x,Ri)):(O.map=new $t(r.x,r.y),O.map.depthTexture=new Gi(r.x,r.y,Ri)),O.map.depthTexture.name=F.name+".shadowMap",O.map.depthTexture.format=Wi,this.type===Yo?(O.map.depthTexture.compareFunction=G?ef:Qh,O.map.depthTexture.minFilter=zt,O.map.depthTexture.magFilter=zt):(O.map.depthTexture.compareFunction=null,O.map.depthTexture.minFilter=cn,O.map.depthTexture.magFilter=cn);O.camera.updateProjectionMatrix()}const W=O.map.isWebGLCubeRenderTarget?6:1;for(let N=0;N<W;N++){if(O.map.isWebGLCubeRenderTarget)n.setRenderTarget(O.map,N),n.clear();else{N===0&&(n.setRenderTarget(O.map),n.clear());const k=O.getViewport(N);a.set(s.x*k.x,s.y*k.y,s.x*k.z,s.y*k.w),R.viewport(a)}if(F.isPointLight){const k=O.camera,J=O.matrix,Q=F.distance||k.far;Q!==k.far&&(k.far=Q,k.updateProjectionMatrix()),Sa.setFromMatrixPosition(F.matrixWorld),k.position.copy(Sa),Vc.copy(k.position),Vc.add(SS[N]),k.up.copy(yS[N]),k.lookAt(Vc),k.updateMatrixWorld(),J.makeTranslation(-Sa.x,-Sa.y,-Sa.z),ap.multiplyMatrices(k.projectionMatrix,k.matrixWorldInverse),O._frustum.setFromProjectionMatrix(ap,k.coordinateSystem,k.reversedDepth)}else O.updateMatrices(F);i=O.getFrustum(),y(E,b,O.camera,F,this.type)}O.isPointLightShadow!==!0&&this.type===wa&&v(O,b),O.needsUpdate=!1}_=this.type,p.needsUpdate=!1,n.setRenderTarget(x,A,C)};function v(S,E){const b=e.update(m);h.defines.VSM_SAMPLES!==S.blurSamples&&(h.defines.VSM_SAMPLES=S.blurSamples,d.defines.VSM_SAMPLES=S.blurSamples,h.needsUpdate=!0,d.needsUpdate=!0),S.mapPass===null&&(S.mapPass=new $t(r.x,r.y,{format:qr,type:Vi})),h.uniforms.shadow_pass.value=S.map.depthTexture,h.uniforms.resolution.value=S.mapSize,h.uniforms.radius.value=S.radius,n.setRenderTarget(S.mapPass),n.clear(),n.renderBufferDirect(E,null,b,h,m,null),d.uniforms.shadow_pass.value=S.mapPass.texture,d.uniforms.resolution.value=S.mapSize,d.uniforms.radius.value=S.radius,n.setRenderTarget(S.map),n.clear(),n.renderBufferDirect(E,null,b,d,m,null)}function M(S,E,b,x){let A=null;const C=b.isPointLight===!0?S.customDistanceMaterial:S.customDepthMaterial;if(C!==void 0)A=C;else if(A=b.isPointLight===!0?l:o,n.localClippingEnabled&&E.clipShadows===!0&&Array.isArray(E.clippingPlanes)&&E.clippingPlanes.length!==0||E.displacementMap&&E.displacementScale!==0||E.alphaMap&&E.alphaTest>0||E.map&&E.alphaTest>0||E.alphaToCoverage===!0){const R=A.uuid,L=E.uuid;let U=c[R];U===void 0&&(U={},c[R]=U);let I=U[L];I===void 0&&(I=A.clone(),U[L]=I,E.addEventListener("dispose",T)),A=I}if(A.visible=E.visible,A.wireframe=E.wireframe,x===wa?A.side=E.shadowSide!==null?E.shadowSide:E.side:A.side=E.shadowSide!==null?E.shadowSide:f[E.side],A.alphaMap=E.alphaMap,A.alphaTest=E.alphaToCoverage===!0?.5:E.alphaTest,A.map=E.map,A.clipShadows=E.clipShadows,A.clippingPlanes=E.clippingPlanes,A.clipIntersection=E.clipIntersection,A.displacementMap=E.displacementMap,A.displacementScale=E.displacementScale,A.displacementBias=E.displacementBias,A.wireframeLinewidth=E.wireframeLinewidth,A.linewidth=E.linewidth,b.isPointLight===!0&&A.isMeshDistanceMaterial===!0){const R=n.properties.get(A);R.light=b}return A}function y(S,E,b,x,A){if(S.visible===!1)return;if(S.layers.test(E.layers)&&(S.isMesh||S.isLine||S.isPoints)&&(S.castShadow||S.receiveShadow&&A===wa)&&(!S.frustumCulled||i.intersectsObject(S))){S.modelViewMatrix.multiplyMatrices(b.matrixWorldInverse,S.matrixWorld);const L=e.update(S),U=S.material;if(Array.isArray(U)){const I=L.groups;for(let F=0,O=I.length;F<O;F++){const j=I[F],G=U[j.materialIndex];if(G&&G.visible){const W=M(S,G,x,A);S.onBeforeShadow(n,S,E,b,L,W,j),n.renderBufferDirect(b,null,L,W,S,j),S.onAfterShadow(n,S,E,b,L,W,j)}}}else if(U.visible){const I=M(S,U,x,A);S.onBeforeShadow(n,S,E,b,L,I,null),n.renderBufferDirect(b,null,L,I,S,null),S.onAfterShadow(n,S,E,b,L,I,null)}}const R=S.children;for(let L=0,U=R.length;L<U;L++)y(R[L],E,b,x,A)}function T(S){S.target.removeEventListener("dispose",T);for(const b in c){const x=c[b],A=S.target.uuid;A in x&&(x[A].dispose(),delete x[A])}}}function ES(n,e){function t(){let V=!1;const pe=new Dt;let ie=null;const Re=new Dt(0,0,0,0);return{setMask:function(xe){ie!==xe&&!V&&(n.colorMask(xe,xe,xe,xe),ie=xe)},setLocked:function(xe){V=xe},setClear:function(xe,ae,Ue,Ze,ot){ot===!0&&(xe*=Ze,ae*=Ze,Ue*=Ze),pe.set(xe,ae,Ue,Ze),Re.equals(pe)===!1&&(n.clearColor(xe,ae,Ue,Ze),Re.copy(pe))},reset:function(){V=!1,ie=null,Re.set(-1,0,0,0)}}}function i(){let V=!1,pe=!1,ie=null,Re=null,xe=null;return{setReversed:function(ae){if(pe!==ae){const Ue=e.get("EXT_clip_control");ae?Ue.clipControlEXT(Ue.LOWER_LEFT_EXT,Ue.ZERO_TO_ONE_EXT):Ue.clipControlEXT(Ue.LOWER_LEFT_EXT,Ue.NEGATIVE_ONE_TO_ONE_EXT),pe=ae;const Ze=xe;xe=null,this.setClear(Ze)}},getReversed:function(){return pe},setTest:function(ae){ae?Z(n.DEPTH_TEST):fe(n.DEPTH_TEST)},setMask:function(ae){ie!==ae&&!V&&(n.depthMask(ae),ie=ae)},setFunc:function(ae){if(pe&&(ae=nv[ae]),Re!==ae){switch(ae){case Cu:n.depthFunc(n.NEVER);break;case ol:n.depthFunc(n.ALWAYS);break;case Pu:n.depthFunc(n.LESS);break;case Os:n.depthFunc(n.LEQUAL);break;case Du:n.depthFunc(n.EQUAL);break;case Uu:n.depthFunc(n.GEQUAL);break;case Lu:n.depthFunc(n.GREATER);break;case Iu:n.depthFunc(n.NOTEQUAL);break;default:n.depthFunc(n.LEQUAL)}Re=ae}},setLocked:function(ae){V=ae},setClear:function(ae){xe!==ae&&(xe=ae,pe&&(ae=1-ae),n.clearDepth(ae))},reset:function(){V=!1,ie=null,Re=null,xe=null,pe=!1}}}function r(){let V=!1,pe=null,ie=null,Re=null,xe=null,ae=null,Ue=null,Ze=null,ot=null;return{setTest:function(tt){V||(tt?Z(n.STENCIL_TEST):fe(n.STENCIL_TEST))},setMask:function(tt){pe!==tt&&!V&&(n.stencilMask(tt),pe=tt)},setFunc:function(tt,Ht,qt){(ie!==tt||Re!==Ht||xe!==qt)&&(n.stencilFunc(tt,Ht,qt),ie=tt,Re=Ht,xe=qt)},setOp:function(tt,Ht,qt){(ae!==tt||Ue!==Ht||Ze!==qt)&&(n.stencilOp(tt,Ht,qt),ae=tt,Ue=Ht,Ze=qt)},setLocked:function(tt){V=tt},setClear:function(tt){ot!==tt&&(n.clearStencil(tt),ot=tt)},reset:function(){V=!1,pe=null,ie=null,Re=null,xe=null,ae=null,Ue=null,Ze=null,ot=null}}}const s=new t,a=new i,o=new r,l=new WeakMap,c=new WeakMap;let u={},f={},h={},d=new WeakMap,g=[],m=null,p=!1,_=null,v=null,M=null,y=null,T=null,S=null,E=null,b=new ut(0,0,0),x=0,A=!1,C=null,R=null,L=null,U=null,I=null;const F=n.getParameter(n.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let O=!1,j=0;const G=n.getParameter(n.VERSION);G.indexOf("WebGL")!==-1?(j=parseFloat(/^WebGL (\d)/.exec(G)[1]),O=j>=1):G.indexOf("OpenGL ES")!==-1&&(j=parseFloat(/^OpenGL ES (\d)/.exec(G)[1]),O=j>=2);let W=null,N={};const k=n.getParameter(n.SCISSOR_BOX),J=n.getParameter(n.VIEWPORT),Q=new Dt().fromArray(k),K=new Dt().fromArray(J);function H(V,pe,ie,Re){const xe=new Uint8Array(4),ae=n.createTexture();n.bindTexture(V,ae),n.texParameteri(V,n.TEXTURE_MIN_FILTER,n.NEAREST),n.texParameteri(V,n.TEXTURE_MAG_FILTER,n.NEAREST);for(let Ue=0;Ue<ie;Ue++)V===n.TEXTURE_3D||V===n.TEXTURE_2D_ARRAY?n.texImage3D(pe,0,n.RGBA,1,1,Re,0,n.RGBA,n.UNSIGNED_BYTE,xe):n.texImage2D(pe+Ue,0,n.RGBA,1,1,0,n.RGBA,n.UNSIGNED_BYTE,xe);return ae}const Y={};Y[n.TEXTURE_2D]=H(n.TEXTURE_2D,n.TEXTURE_2D,1),Y[n.TEXTURE_CUBE_MAP]=H(n.TEXTURE_CUBE_MAP,n.TEXTURE_CUBE_MAP_POSITIVE_X,6),Y[n.TEXTURE_2D_ARRAY]=H(n.TEXTURE_2D_ARRAY,n.TEXTURE_2D_ARRAY,1,1),Y[n.TEXTURE_3D]=H(n.TEXTURE_3D,n.TEXTURE_3D,1,1),s.setClear(0,0,0,1),a.setClear(1),o.setClear(0),Z(n.DEPTH_TEST),a.setFunc(Os),Ge(!1),_e(id),Z(n.CULL_FACE),Ce(Mn);function Z(V){u[V]!==!0&&(n.enable(V),u[V]=!0)}function fe(V){u[V]!==!1&&(n.disable(V),u[V]=!1)}function Me(V,pe){return h[V]!==pe?(n.bindFramebuffer(V,pe),h[V]=pe,V===n.DRAW_FRAMEBUFFER&&(h[n.FRAMEBUFFER]=pe),V===n.FRAMEBUFFER&&(h[n.DRAW_FRAMEBUFFER]=pe),!0):!1}function ce(V,pe){let ie=g,Re=!1;if(V){ie=d.get(pe),ie===void 0&&(ie=[],d.set(pe,ie));const xe=V.textures;if(ie.length!==xe.length||ie[0]!==n.COLOR_ATTACHMENT0){for(let ae=0,Ue=xe.length;ae<Ue;ae++)ie[ae]=n.COLOR_ATTACHMENT0+ae;ie.length=xe.length,Re=!0}}else ie[0]!==n.BACK&&(ie[0]=n.BACK,Re=!0);Re&&n.drawBuffers(ie)}function de(V){return m!==V?(n.useProgram(V),m=V,!0):!1}const Ne={[Fr]:n.FUNC_ADD,[E_]:n.FUNC_SUBTRACT,[w_]:n.FUNC_REVERSE_SUBTRACT};Ne[A_]=n.MIN,Ne[R_]=n.MAX;const Oe={[C_]:n.ZERO,[P_]:n.ONE,[D_]:n.SRC_COLOR,[Au]:n.SRC_ALPHA,[O_]:n.SRC_ALPHA_SATURATE,[F_]:n.DST_COLOR,[L_]:n.DST_ALPHA,[U_]:n.ONE_MINUS_SRC_COLOR,[Ru]:n.ONE_MINUS_SRC_ALPHA,[N_]:n.ONE_MINUS_DST_COLOR,[I_]:n.ONE_MINUS_DST_ALPHA,[B_]:n.CONSTANT_COLOR,[k_]:n.ONE_MINUS_CONSTANT_COLOR,[z_]:n.CONSTANT_ALPHA,[G_]:n.ONE_MINUS_CONSTANT_ALPHA};function Ce(V,pe,ie,Re,xe,ae,Ue,Ze,ot,tt){if(V===Mn){p===!0&&(fe(n.BLEND),p=!1);return}if(p===!1&&(Z(n.BLEND),p=!0),V!==T_){if(V!==_||tt!==A){if((v!==Fr||T!==Fr)&&(n.blendEquation(n.FUNC_ADD),v=Fr,T=Fr),tt)switch(V){case kr:n.blendFuncSeparate(n.ONE,n.ONE_MINUS_SRC_ALPHA,n.ONE,n.ONE_MINUS_SRC_ALPHA);break;case al:n.blendFunc(n.ONE,n.ONE);break;case rd:n.blendFuncSeparate(n.ZERO,n.ONE_MINUS_SRC_COLOR,n.ZERO,n.ONE);break;case sd:n.blendFuncSeparate(n.DST_COLOR,n.ONE_MINUS_SRC_ALPHA,n.ZERO,n.ONE);break;default:pt("WebGLState: Invalid blending: ",V);break}else switch(V){case kr:n.blendFuncSeparate(n.SRC_ALPHA,n.ONE_MINUS_SRC_ALPHA,n.ONE,n.ONE_MINUS_SRC_ALPHA);break;case al:n.blendFuncSeparate(n.SRC_ALPHA,n.ONE,n.ONE,n.ONE);break;case rd:pt("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case sd:pt("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:pt("WebGLState: Invalid blending: ",V);break}M=null,y=null,S=null,E=null,b.set(0,0,0),x=0,_=V,A=tt}return}xe=xe||pe,ae=ae||ie,Ue=Ue||Re,(pe!==v||xe!==T)&&(n.blendEquationSeparate(Ne[pe],Ne[xe]),v=pe,T=xe),(ie!==M||Re!==y||ae!==S||Ue!==E)&&(n.blendFuncSeparate(Oe[ie],Oe[Re],Oe[ae],Oe[Ue]),M=ie,y=Re,S=ae,E=Ue),(Ze.equals(b)===!1||ot!==x)&&(n.blendColor(Ze.r,Ze.g,Ze.b,ot),b.copy(Ze),x=ot),_=V,A=!1}function Te(V,pe){V.side===En?fe(n.CULL_FACE):Z(n.CULL_FACE);let ie=V.side===sn;pe&&(ie=!ie),Ge(ie),V.blending===kr&&V.transparent===!1?Ce(Mn):Ce(V.blending,V.blendEquation,V.blendSrc,V.blendDst,V.blendEquationAlpha,V.blendSrcAlpha,V.blendDstAlpha,V.blendColor,V.blendAlpha,V.premultipliedAlpha),a.setFunc(V.depthFunc),a.setTest(V.depthTest),a.setMask(V.depthWrite),s.setMask(V.colorWrite);const Re=V.stencilWrite;o.setTest(Re),Re&&(o.setMask(V.stencilWriteMask),o.setFunc(V.stencilFunc,V.stencilRef,V.stencilFuncMask),o.setOp(V.stencilFail,V.stencilZFail,V.stencilZPass)),B(V.polygonOffset,V.polygonOffsetFactor,V.polygonOffsetUnits),V.alphaToCoverage===!0?Z(n.SAMPLE_ALPHA_TO_COVERAGE):fe(n.SAMPLE_ALPHA_TO_COVERAGE)}function Ge(V){C!==V&&(V?n.frontFace(n.CW):n.frontFace(n.CCW),C=V)}function _e(V){V!==M_?(Z(n.CULL_FACE),V!==R&&(V===id?n.cullFace(n.BACK):V===S_?n.cullFace(n.FRONT):n.cullFace(n.FRONT_AND_BACK))):fe(n.CULL_FACE),R=V}function ze(V){V!==L&&(O&&n.lineWidth(V),L=V)}function B(V,pe,ie){V?(Z(n.POLYGON_OFFSET_FILL),(U!==pe||I!==ie)&&(U=pe,I=ie,a.getReversed()&&(pe=-pe),n.polygonOffset(pe,ie))):fe(n.POLYGON_OFFSET_FILL)}function ue(V){V?Z(n.SCISSOR_TEST):fe(n.SCISSOR_TEST)}function Le(V){V===void 0&&(V=n.TEXTURE0+F-1),W!==V&&(n.activeTexture(V),W=V)}function Ee(V,pe,ie){ie===void 0&&(W===null?ie=n.TEXTURE0+F-1:ie=W);let Re=N[ie];Re===void 0&&(Re={type:void 0,texture:void 0},N[ie]=Re),(Re.type!==V||Re.texture!==pe)&&(W!==ie&&(n.activeTexture(ie),W=ie),n.bindTexture(V,pe||Y[V]),Re.type=V,Re.texture=pe)}function le(){const V=N[W];V!==void 0&&V.type!==void 0&&(n.bindTexture(V.type,null),V.type=void 0,V.texture=void 0)}function we(){try{n.compressedTexImage2D(...arguments)}catch(V){pt("WebGLState:",V)}}function D(){try{n.compressedTexImage3D(...arguments)}catch(V){pt("WebGLState:",V)}}function w(){try{n.texSubImage2D(...arguments)}catch(V){pt("WebGLState:",V)}}function z(){try{n.texSubImage3D(...arguments)}catch(V){pt("WebGLState:",V)}}function $(){try{n.compressedTexSubImage2D(...arguments)}catch(V){pt("WebGLState:",V)}}function oe(){try{n.compressedTexSubImage3D(...arguments)}catch(V){pt("WebGLState:",V)}}function ge(){try{n.texStorage2D(...arguments)}catch(V){pt("WebGLState:",V)}}function be(){try{n.texStorage3D(...arguments)}catch(V){pt("WebGLState:",V)}}function ee(){try{n.texImage2D(...arguments)}catch(V){pt("WebGLState:",V)}}function re(){try{n.texImage3D(...arguments)}catch(V){pt("WebGLState:",V)}}function he(V){return f[V]!==void 0?f[V]:n.getParameter(V)}function Pe(V,pe){f[V]!==pe&&(n.pixelStorei(V,pe),f[V]=pe)}function ve(V){Q.equals(V)===!1&&(n.scissor(V.x,V.y,V.z,V.w),Q.copy(V))}function Se(V){K.equals(V)===!1&&(n.viewport(V.x,V.y,V.z,V.w),K.copy(V))}function He(V,pe){let ie=c.get(pe);ie===void 0&&(ie=new WeakMap,c.set(pe,ie));let Re=ie.get(V);Re===void 0&&(Re=n.getUniformBlockIndex(pe,V.name),ie.set(V,Re))}function De(V,pe){const Re=c.get(pe).get(V);l.get(pe)!==Re&&(n.uniformBlockBinding(pe,Re,V.__bindingPointIndex),l.set(pe,Re))}function Ye(){n.disable(n.BLEND),n.disable(n.CULL_FACE),n.disable(n.DEPTH_TEST),n.disable(n.POLYGON_OFFSET_FILL),n.disable(n.SCISSOR_TEST),n.disable(n.STENCIL_TEST),n.disable(n.SAMPLE_ALPHA_TO_COVERAGE),n.blendEquation(n.FUNC_ADD),n.blendFunc(n.ONE,n.ZERO),n.blendFuncSeparate(n.ONE,n.ZERO,n.ONE,n.ZERO),n.blendColor(0,0,0,0),n.colorMask(!0,!0,!0,!0),n.clearColor(0,0,0,0),n.depthMask(!0),n.depthFunc(n.LESS),a.setReversed(!1),n.clearDepth(1),n.stencilMask(4294967295),n.stencilFunc(n.ALWAYS,0,4294967295),n.stencilOp(n.KEEP,n.KEEP,n.KEEP),n.clearStencil(0),n.cullFace(n.BACK),n.frontFace(n.CCW),n.polygonOffset(0,0),n.activeTexture(n.TEXTURE0),n.bindFramebuffer(n.FRAMEBUFFER,null),n.bindFramebuffer(n.DRAW_FRAMEBUFFER,null),n.bindFramebuffer(n.READ_FRAMEBUFFER,null),n.useProgram(null),n.lineWidth(1),n.scissor(0,0,n.canvas.width,n.canvas.height),n.viewport(0,0,n.canvas.width,n.canvas.height),n.pixelStorei(n.PACK_ALIGNMENT,4),n.pixelStorei(n.UNPACK_ALIGNMENT,4),n.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,!1),n.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),n.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,n.BROWSER_DEFAULT_WEBGL),n.pixelStorei(n.PACK_ROW_LENGTH,0),n.pixelStorei(n.PACK_SKIP_PIXELS,0),n.pixelStorei(n.PACK_SKIP_ROWS,0),n.pixelStorei(n.UNPACK_ROW_LENGTH,0),n.pixelStorei(n.UNPACK_IMAGE_HEIGHT,0),n.pixelStorei(n.UNPACK_SKIP_PIXELS,0),n.pixelStorei(n.UNPACK_SKIP_ROWS,0),n.pixelStorei(n.UNPACK_SKIP_IMAGES,0),u={},f={},W=null,N={},h={},d=new WeakMap,g=[],m=null,p=!1,_=null,v=null,M=null,y=null,T=null,S=null,E=null,b=new ut(0,0,0),x=0,A=!1,C=null,R=null,L=null,U=null,I=null,Q.set(0,0,n.canvas.width,n.canvas.height),K.set(0,0,n.canvas.width,n.canvas.height),s.reset(),a.reset(),o.reset()}return{buffers:{color:s,depth:a,stencil:o},enable:Z,disable:fe,bindFramebuffer:Me,drawBuffers:ce,useProgram:de,setBlending:Ce,setMaterial:Te,setFlipSided:Ge,setCullFace:_e,setLineWidth:ze,setPolygonOffset:B,setScissorTest:ue,activeTexture:Le,bindTexture:Ee,unbindTexture:le,compressedTexImage2D:we,compressedTexImage3D:D,texImage2D:ee,texImage3D:re,pixelStorei:Pe,getParameter:he,updateUBOMapping:He,uniformBlockBinding:De,texStorage2D:ge,texStorage3D:be,texSubImage2D:w,texSubImage3D:z,compressedTexSubImage2D:$,compressedTexSubImage3D:oe,scissor:ve,viewport:Se,reset:Ye}}function wS(n,e,t,i,r,s,a){const o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new Xe,u=new WeakMap,f=new Set;let h;const d=new WeakMap;let g=!1;try{g=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function m(D,w){return g?new OffscreenCanvas(D,w):fl("canvas")}function p(D,w,z){let $=1;const oe=we(D);if((oe.width>z||oe.height>z)&&($=z/Math.max(oe.width,oe.height)),$<1)if(typeof HTMLImageElement<"u"&&D instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&D instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&D instanceof ImageBitmap||typeof VideoFrame<"u"&&D instanceof VideoFrame){const ge=Math.floor($*oe.width),be=Math.floor($*oe.height);h===void 0&&(h=m(ge,be));const ee=w?m(ge,be):h;return ee.width=ge,ee.height=be,ee.getContext("2d").drawImage(D,0,0,ge,be),Je("WebGLRenderer: Texture has been resized from ("+oe.width+"x"+oe.height+") to ("+ge+"x"+be+")."),ee}else return"data"in D&&Je("WebGLRenderer: Image in DataTexture is too big ("+oe.width+"x"+oe.height+")."),D;return D}function _(D){return D.generateMipmaps}function v(D){n.generateMipmap(D)}function M(D){return D.isWebGLCubeRenderTarget?n.TEXTURE_CUBE_MAP:D.isWebGL3DRenderTarget?n.TEXTURE_3D:D.isWebGLArrayRenderTarget||D.isCompressedArrayTexture?n.TEXTURE_2D_ARRAY:n.TEXTURE_2D}function y(D,w,z,$,oe,ge=!1){if(D!==null){if(n[D]!==void 0)return n[D];Je("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+D+"'")}let be;$&&(be=e.get("EXT_texture_norm16"),be||Je("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let ee=w;if(w===n.RED&&(z===n.FLOAT&&(ee=n.R32F),z===n.HALF_FLOAT&&(ee=n.R16F),z===n.UNSIGNED_BYTE&&(ee=n.R8),z===n.UNSIGNED_SHORT&&be&&(ee=be.R16_EXT),z===n.SHORT&&be&&(ee=be.R16_SNORM_EXT)),w===n.RED_INTEGER&&(z===n.UNSIGNED_BYTE&&(ee=n.R8UI),z===n.UNSIGNED_SHORT&&(ee=n.R16UI),z===n.UNSIGNED_INT&&(ee=n.R32UI),z===n.BYTE&&(ee=n.R8I),z===n.SHORT&&(ee=n.R16I),z===n.INT&&(ee=n.R32I)),w===n.RG&&(z===n.FLOAT&&(ee=n.RG32F),z===n.HALF_FLOAT&&(ee=n.RG16F),z===n.UNSIGNED_BYTE&&(ee=n.RG8),z===n.UNSIGNED_SHORT&&be&&(ee=be.RG16_EXT),z===n.SHORT&&be&&(ee=be.RG16_SNORM_EXT)),w===n.RG_INTEGER&&(z===n.UNSIGNED_BYTE&&(ee=n.RG8UI),z===n.UNSIGNED_SHORT&&(ee=n.RG16UI),z===n.UNSIGNED_INT&&(ee=n.RG32UI),z===n.BYTE&&(ee=n.RG8I),z===n.SHORT&&(ee=n.RG16I),z===n.INT&&(ee=n.RG32I)),w===n.RGB_INTEGER&&(z===n.UNSIGNED_BYTE&&(ee=n.RGB8UI),z===n.UNSIGNED_SHORT&&(ee=n.RGB16UI),z===n.UNSIGNED_INT&&(ee=n.RGB32UI),z===n.BYTE&&(ee=n.RGB8I),z===n.SHORT&&(ee=n.RGB16I),z===n.INT&&(ee=n.RGB32I)),w===n.RGBA_INTEGER&&(z===n.UNSIGNED_BYTE&&(ee=n.RGBA8UI),z===n.UNSIGNED_SHORT&&(ee=n.RGBA16UI),z===n.UNSIGNED_INT&&(ee=n.RGBA32UI),z===n.BYTE&&(ee=n.RGBA8I),z===n.SHORT&&(ee=n.RGBA16I),z===n.INT&&(ee=n.RGBA32I)),w===n.RGB&&(z===n.UNSIGNED_SHORT&&be&&(ee=be.RGB16_EXT),z===n.SHORT&&be&&(ee=be.RGB16_SNORM_EXT),z===n.UNSIGNED_INT_5_9_9_9_REV&&(ee=n.RGB9_E5),z===n.UNSIGNED_INT_10F_11F_11F_REV&&(ee=n.R11F_G11F_B10F)),w===n.RGBA){const re=ge?ul:ft.getTransfer(oe);z===n.FLOAT&&(ee=n.RGBA32F),z===n.HALF_FLOAT&&(ee=n.RGBA16F),z===n.UNSIGNED_BYTE&&(ee=re===Mt?n.SRGB8_ALPHA8:n.RGBA8),z===n.UNSIGNED_SHORT&&be&&(ee=be.RGBA16_EXT),z===n.SHORT&&be&&(ee=be.RGBA16_SNORM_EXT),z===n.UNSIGNED_SHORT_4_4_4_4&&(ee=n.RGBA4),z===n.UNSIGNED_SHORT_5_5_5_1&&(ee=n.RGB5_A1)}return(ee===n.R16F||ee===n.R32F||ee===n.RG16F||ee===n.RG32F||ee===n.RGBA16F||ee===n.RGBA32F)&&e.get("EXT_color_buffer_float"),ee}function T(D,w){let z;return D?w===null||w===Ri||w===ks?z=n.DEPTH24_STENCIL8:w===li?z=n.DEPTH32F_STENCIL8:w===Ba&&(z=n.DEPTH24_STENCIL8,Je("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):w===null||w===Ri||w===ks?z=n.DEPTH_COMPONENT24:w===li?z=n.DEPTH_COMPONENT32F:w===Ba&&(z=n.DEPTH_COMPONENT16),z}function S(D,w){return _(D)===!0||D.isFramebufferTexture&&D.minFilter!==cn&&D.minFilter!==zt?Math.log2(Math.max(w.width,w.height))+1:D.mipmaps!==void 0&&D.mipmaps.length>0?D.mipmaps.length:D.isCompressedTexture&&Array.isArray(D.image)?w.mipmaps.length:1}function E(D){const w=D.target;w.removeEventListener("dispose",E),x(w),w.isVideoTexture&&u.delete(w),w.isHTMLTexture&&f.delete(w)}function b(D){const w=D.target;w.removeEventListener("dispose",b),C(w)}function x(D){const w=i.get(D);if(w.__webglInit===void 0)return;const z=D.source,$=d.get(z);if($){const oe=$[w.__cacheKey];oe.usedTimes--,oe.usedTimes===0&&A(D),Object.keys($).length===0&&d.delete(z)}i.remove(D)}function A(D){const w=i.get(D);n.deleteTexture(w.__webglTexture);const z=D.source,$=d.get(z);delete $[w.__cacheKey],a.memory.textures--}function C(D){const w=i.get(D);if(D.depthTexture&&(D.depthTexture.dispose(),i.remove(D.depthTexture)),D.isWebGLCubeRenderTarget)for(let $=0;$<6;$++){if(Array.isArray(w.__webglFramebuffer[$]))for(let oe=0;oe<w.__webglFramebuffer[$].length;oe++)n.deleteFramebuffer(w.__webglFramebuffer[$][oe]);else n.deleteFramebuffer(w.__webglFramebuffer[$]);w.__webglDepthbuffer&&n.deleteRenderbuffer(w.__webglDepthbuffer[$])}else{if(Array.isArray(w.__webglFramebuffer))for(let $=0;$<w.__webglFramebuffer.length;$++)n.deleteFramebuffer(w.__webglFramebuffer[$]);else n.deleteFramebuffer(w.__webglFramebuffer);if(w.__webglDepthbuffer&&n.deleteRenderbuffer(w.__webglDepthbuffer),w.__webglMultisampledFramebuffer&&n.deleteFramebuffer(w.__webglMultisampledFramebuffer),w.__webglColorRenderbuffer)for(let $=0;$<w.__webglColorRenderbuffer.length;$++)w.__webglColorRenderbuffer[$]&&n.deleteRenderbuffer(w.__webglColorRenderbuffer[$]);w.__webglDepthRenderbuffer&&n.deleteRenderbuffer(w.__webglDepthRenderbuffer)}const z=D.textures;for(let $=0,oe=z.length;$<oe;$++){const ge=i.get(z[$]);ge.__webglTexture&&(n.deleteTexture(ge.__webglTexture),a.memory.textures--),i.remove(z[$])}i.remove(D)}let R=0;function L(){R=0}function U(){return R}function I(D){R=D}function F(){const D=R;return D>=r.maxTextures&&Je("WebGLTextures: Trying to use "+D+" texture units while this GPU supports only "+r.maxTextures),R+=1,D}function O(D){const w=[];return w.push(D.wrapS),w.push(D.wrapT),w.push(D.wrapR||0),w.push(D.magFilter),w.push(D.minFilter),w.push(D.anisotropy),w.push(D.internalFormat),w.push(D.format),w.push(D.type),w.push(D.generateMipmaps),w.push(D.premultiplyAlpha),w.push(D.flipY),w.push(D.unpackAlignment),w.push(D.colorSpace),w.join()}function j(D,w){const z=i.get(D);if(D.isVideoTexture&&Ee(D),D.isRenderTargetTexture===!1&&D.isExternalTexture!==!0&&D.version>0&&z.__version!==D.version){const $=D.image;if($===null)Je("WebGLRenderer: Texture marked for update but no image data found.");else if($.complete===!1)Je("WebGLRenderer: Texture marked for update but image is incomplete");else{fe(z,D,w);return}}else D.isExternalTexture&&(z.__webglTexture=D.sourceTexture?D.sourceTexture:null);t.bindTexture(n.TEXTURE_2D,z.__webglTexture,n.TEXTURE0+w)}function G(D,w){const z=i.get(D);if(D.isRenderTargetTexture===!1&&D.version>0&&z.__version!==D.version){fe(z,D,w);return}else D.isExternalTexture&&(z.__webglTexture=D.sourceTexture?D.sourceTexture:null);t.bindTexture(n.TEXTURE_2D_ARRAY,z.__webglTexture,n.TEXTURE0+w)}function W(D,w){const z=i.get(D);if(D.isRenderTargetTexture===!1&&D.version>0&&z.__version!==D.version){fe(z,D,w);return}t.bindTexture(n.TEXTURE_3D,z.__webglTexture,n.TEXTURE0+w)}function N(D,w){const z=i.get(D);if(D.isCubeDepthTexture!==!0&&D.version>0&&z.__version!==D.version){Me(z,D,w);return}t.bindTexture(n.TEXTURE_CUBE_MAP,z.__webglTexture,n.TEXTURE0+w)}const k={[Fu]:n.REPEAT,[ki]:n.CLAMP_TO_EDGE,[Nu]:n.MIRRORED_REPEAT},J={[cn]:n.NEAREST,[W_]:n.NEAREST_MIPMAP_NEAREST,[co]:n.NEAREST_MIPMAP_LINEAR,[zt]:n.LINEAR,[hc]:n.LINEAR_MIPMAP_NEAREST,[Or]:n.LINEAR_MIPMAP_LINEAR},Q={[Y_]:n.NEVER,[J_]:n.ALWAYS,[q_]:n.LESS,[Qh]:n.LEQUAL,[K_]:n.EQUAL,[ef]:n.GEQUAL,[Z_]:n.GREATER,[$_]:n.NOTEQUAL};function K(D,w){if(w.type===li&&e.has("OES_texture_float_linear")===!1&&(w.magFilter===zt||w.magFilter===hc||w.magFilter===co||w.magFilter===Or||w.minFilter===zt||w.minFilter===hc||w.minFilter===co||w.minFilter===Or)&&Je("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),n.texParameteri(D,n.TEXTURE_WRAP_S,k[w.wrapS]),n.texParameteri(D,n.TEXTURE_WRAP_T,k[w.wrapT]),(D===n.TEXTURE_3D||D===n.TEXTURE_2D_ARRAY)&&n.texParameteri(D,n.TEXTURE_WRAP_R,k[w.wrapR]),n.texParameteri(D,n.TEXTURE_MAG_FILTER,J[w.magFilter]),n.texParameteri(D,n.TEXTURE_MIN_FILTER,J[w.minFilter]),w.compareFunction&&(n.texParameteri(D,n.TEXTURE_COMPARE_MODE,n.COMPARE_REF_TO_TEXTURE),n.texParameteri(D,n.TEXTURE_COMPARE_FUNC,Q[w.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(w.magFilter===cn||w.minFilter!==co&&w.minFilter!==Or||w.type===li&&e.has("OES_texture_float_linear")===!1)return;if(w.anisotropy>1||i.get(w).__currentAnisotropy){const z=e.get("EXT_texture_filter_anisotropic");n.texParameterf(D,z.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(w.anisotropy,r.getMaxAnisotropy())),i.get(w).__currentAnisotropy=w.anisotropy}}}function H(D,w){let z=!1;D.__webglInit===void 0&&(D.__webglInit=!0,w.addEventListener("dispose",E));const $=w.source;let oe=d.get($);oe===void 0&&(oe={},d.set($,oe));const ge=O(w);if(ge!==D.__cacheKey){oe[ge]===void 0&&(oe[ge]={texture:n.createTexture(),usedTimes:0},a.memory.textures++,z=!0),oe[ge].usedTimes++;const be=oe[D.__cacheKey];be!==void 0&&(oe[D.__cacheKey].usedTimes--,be.usedTimes===0&&A(w)),D.__cacheKey=ge,D.__webglTexture=oe[ge].texture}return z}function Y(D,w,z){return Math.floor(Math.floor(D/z)/w)}function Z(D,w,z,$){const ge=D.updateRanges;if(ge.length===0)t.texSubImage2D(n.TEXTURE_2D,0,0,0,w.width,w.height,z,$,w.data);else{ge.sort((Pe,ve)=>Pe.start-ve.start);let be=0;for(let Pe=1;Pe<ge.length;Pe++){const ve=ge[be],Se=ge[Pe],He=ve.start+ve.count,De=Y(Se.start,w.width,4),Ye=Y(ve.start,w.width,4);Se.start<=He+1&&De===Ye&&Y(Se.start+Se.count-1,w.width,4)===De?ve.count=Math.max(ve.count,Se.start+Se.count-ve.start):(++be,ge[be]=Se)}ge.length=be+1;const ee=t.getParameter(n.UNPACK_ROW_LENGTH),re=t.getParameter(n.UNPACK_SKIP_PIXELS),he=t.getParameter(n.UNPACK_SKIP_ROWS);t.pixelStorei(n.UNPACK_ROW_LENGTH,w.width);for(let Pe=0,ve=ge.length;Pe<ve;Pe++){const Se=ge[Pe],He=Math.floor(Se.start/4),De=Math.ceil(Se.count/4),Ye=He%w.width,V=Math.floor(He/w.width),pe=De,ie=1;t.pixelStorei(n.UNPACK_SKIP_PIXELS,Ye),t.pixelStorei(n.UNPACK_SKIP_ROWS,V),t.texSubImage2D(n.TEXTURE_2D,0,Ye,V,pe,ie,z,$,w.data)}D.clearUpdateRanges(),t.pixelStorei(n.UNPACK_ROW_LENGTH,ee),t.pixelStorei(n.UNPACK_SKIP_PIXELS,re),t.pixelStorei(n.UNPACK_SKIP_ROWS,he)}}function fe(D,w,z){let $=n.TEXTURE_2D;(w.isDataArrayTexture||w.isCompressedArrayTexture)&&($=n.TEXTURE_2D_ARRAY),w.isData3DTexture&&($=n.TEXTURE_3D);const oe=H(D,w),ge=w.source;t.bindTexture($,D.__webglTexture,n.TEXTURE0+z);const be=i.get(ge);if(ge.version!==be.__version||oe===!0){if(t.activeTexture(n.TEXTURE0+z),(typeof ImageBitmap<"u"&&w.image instanceof ImageBitmap)===!1){const ie=ft.getPrimaries(ft.workingColorSpace),Re=w.colorSpace===bi?null:ft.getPrimaries(w.colorSpace),xe=w.colorSpace===bi||ie===Re?n.NONE:n.BROWSER_DEFAULT_WEBGL;t.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,w.flipY),t.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,w.premultiplyAlpha),t.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,xe)}t.pixelStorei(n.UNPACK_ALIGNMENT,w.unpackAlignment);let re=p(w.image,!1,r.maxTextureSize);re=le(w,re);const he=s.convert(w.format,w.colorSpace),Pe=s.convert(w.type);let ve=y(w.internalFormat,he,Pe,w.normalized,w.colorSpace,w.isVideoTexture);K($,w);let Se;const He=w.mipmaps,De=w.isVideoTexture!==!0,Ye=be.__version===void 0||oe===!0,V=ge.dataReady,pe=S(w,re);if(w.isDepthTexture)ve=T(w.format===lr,w.type),Ye&&(De?t.texStorage2D(n.TEXTURE_2D,1,ve,re.width,re.height):t.texImage2D(n.TEXTURE_2D,0,ve,re.width,re.height,0,he,Pe,null));else if(w.isDataTexture)if(He.length>0){De&&Ye&&t.texStorage2D(n.TEXTURE_2D,pe,ve,He[0].width,He[0].height);for(let ie=0,Re=He.length;ie<Re;ie++)Se=He[ie],De?V&&t.texSubImage2D(n.TEXTURE_2D,ie,0,0,Se.width,Se.height,he,Pe,Se.data):t.texImage2D(n.TEXTURE_2D,ie,ve,Se.width,Se.height,0,he,Pe,Se.data);w.generateMipmaps=!1}else De?(Ye&&t.texStorage2D(n.TEXTURE_2D,pe,ve,re.width,re.height),V&&Z(w,re,he,Pe)):t.texImage2D(n.TEXTURE_2D,0,ve,re.width,re.height,0,he,Pe,re.data);else if(w.isCompressedTexture)if(w.isCompressedArrayTexture){De&&Ye&&t.texStorage3D(n.TEXTURE_2D_ARRAY,pe,ve,He[0].width,He[0].height,re.depth);for(let ie=0,Re=He.length;ie<Re;ie++)if(Se=He[ie],w.format!==ci)if(he!==null)if(De){if(V)if(w.layerUpdates.size>0){const xe=Od(Se.width,Se.height,w.format,w.type);for(const ae of w.layerUpdates){const Ue=Se.data.subarray(ae*xe/Se.data.BYTES_PER_ELEMENT,(ae+1)*xe/Se.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(n.TEXTURE_2D_ARRAY,ie,0,0,ae,Se.width,Se.height,1,he,Ue)}w.clearLayerUpdates()}else t.compressedTexSubImage3D(n.TEXTURE_2D_ARRAY,ie,0,0,0,Se.width,Se.height,re.depth,he,Se.data)}else t.compressedTexImage3D(n.TEXTURE_2D_ARRAY,ie,ve,Se.width,Se.height,re.depth,0,Se.data,0,0);else Je("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else De?V&&t.texSubImage3D(n.TEXTURE_2D_ARRAY,ie,0,0,0,Se.width,Se.height,re.depth,he,Pe,Se.data):t.texImage3D(n.TEXTURE_2D_ARRAY,ie,ve,Se.width,Se.height,re.depth,0,he,Pe,Se.data)}else{De&&Ye&&t.texStorage2D(n.TEXTURE_2D,pe,ve,He[0].width,He[0].height);for(let ie=0,Re=He.length;ie<Re;ie++)Se=He[ie],w.format!==ci?he!==null?De?V&&t.compressedTexSubImage2D(n.TEXTURE_2D,ie,0,0,Se.width,Se.height,he,Se.data):t.compressedTexImage2D(n.TEXTURE_2D,ie,ve,Se.width,Se.height,0,Se.data):Je("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):De?V&&t.texSubImage2D(n.TEXTURE_2D,ie,0,0,Se.width,Se.height,he,Pe,Se.data):t.texImage2D(n.TEXTURE_2D,ie,ve,Se.width,Se.height,0,he,Pe,Se.data)}else if(w.isDataArrayTexture)if(De){if(Ye&&t.texStorage3D(n.TEXTURE_2D_ARRAY,pe,ve,re.width,re.height,re.depth),V)if(w.layerUpdates.size>0){const ie=Od(re.width,re.height,w.format,w.type);for(const Re of w.layerUpdates){const xe=re.data.subarray(Re*ie/re.data.BYTES_PER_ELEMENT,(Re+1)*ie/re.data.BYTES_PER_ELEMENT);t.texSubImage3D(n.TEXTURE_2D_ARRAY,0,0,0,Re,re.width,re.height,1,he,Pe,xe)}w.clearLayerUpdates()}else t.texSubImage3D(n.TEXTURE_2D_ARRAY,0,0,0,0,re.width,re.height,re.depth,he,Pe,re.data)}else t.texImage3D(n.TEXTURE_2D_ARRAY,0,ve,re.width,re.height,re.depth,0,he,Pe,re.data);else if(w.isData3DTexture)De?(Ye&&t.texStorage3D(n.TEXTURE_3D,pe,ve,re.width,re.height,re.depth),V&&t.texSubImage3D(n.TEXTURE_3D,0,0,0,0,re.width,re.height,re.depth,he,Pe,re.data)):t.texImage3D(n.TEXTURE_3D,0,ve,re.width,re.height,re.depth,0,he,Pe,re.data);else if(w.isFramebufferTexture){if(Ye)if(De)t.texStorage2D(n.TEXTURE_2D,pe,ve,re.width,re.height);else{let ie=re.width,Re=re.height;for(let xe=0;xe<pe;xe++)t.texImage2D(n.TEXTURE_2D,xe,ve,ie,Re,0,he,Pe,null),ie>>=1,Re>>=1}}else if(w.isHTMLTexture){if("texElementImage2D"in n){const ie=n.canvas;if(ie.hasAttribute("layoutsubtree")||ie.setAttribute("layoutsubtree","true"),re.parentNode!==ie){ie.appendChild(re),f.add(w),ie.onpaint=Ze=>{const ot=Ze.changedElements;for(const tt of f)ot.includes(tt.image)&&(tt.needsUpdate=!0)},ie.requestPaint();return}const Re=0,xe=n.RGBA,ae=n.RGBA,Ue=n.UNSIGNED_BYTE;n.texElementImage2D(n.TEXTURE_2D,Re,xe,ae,Ue,re),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_MIN_FILTER,n.LINEAR),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_WRAP_S,n.CLAMP_TO_EDGE),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_WRAP_T,n.CLAMP_TO_EDGE)}}else if(He.length>0){if(De&&Ye){const ie=we(He[0]);t.texStorage2D(n.TEXTURE_2D,pe,ve,ie.width,ie.height)}for(let ie=0,Re=He.length;ie<Re;ie++)Se=He[ie],De?V&&t.texSubImage2D(n.TEXTURE_2D,ie,0,0,he,Pe,Se):t.texImage2D(n.TEXTURE_2D,ie,ve,he,Pe,Se);w.generateMipmaps=!1}else if(De){if(Ye){const ie=we(re);t.texStorage2D(n.TEXTURE_2D,pe,ve,ie.width,ie.height)}V&&t.texSubImage2D(n.TEXTURE_2D,0,0,0,he,Pe,re)}else t.texImage2D(n.TEXTURE_2D,0,ve,he,Pe,re);_(w)&&v($),be.__version=ge.version,w.onUpdate&&w.onUpdate(w)}D.__version=w.version}function Me(D,w,z){if(w.image.length!==6)return;const $=H(D,w),oe=w.source;t.bindTexture(n.TEXTURE_CUBE_MAP,D.__webglTexture,n.TEXTURE0+z);const ge=i.get(oe);if(oe.version!==ge.__version||$===!0){t.activeTexture(n.TEXTURE0+z);const be=ft.getPrimaries(ft.workingColorSpace),ee=w.colorSpace===bi?null:ft.getPrimaries(w.colorSpace),re=w.colorSpace===bi||be===ee?n.NONE:n.BROWSER_DEFAULT_WEBGL;t.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,w.flipY),t.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,w.premultiplyAlpha),t.pixelStorei(n.UNPACK_ALIGNMENT,w.unpackAlignment),t.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,re);const he=w.isCompressedTexture||w.image[0].isCompressedTexture,Pe=w.image[0]&&w.image[0].isDataTexture,ve=[];for(let ae=0;ae<6;ae++)!he&&!Pe?ve[ae]=p(w.image[ae],!0,r.maxCubemapSize):ve[ae]=Pe?w.image[ae].image:w.image[ae],ve[ae]=le(w,ve[ae]);const Se=ve[0],He=s.convert(w.format,w.colorSpace),De=s.convert(w.type),Ye=y(w.internalFormat,He,De,w.normalized,w.colorSpace),V=w.isVideoTexture!==!0,pe=ge.__version===void 0||$===!0,ie=oe.dataReady;let Re=S(w,Se);K(n.TEXTURE_CUBE_MAP,w);let xe;if(he){V&&pe&&t.texStorage2D(n.TEXTURE_CUBE_MAP,Re,Ye,Se.width,Se.height);for(let ae=0;ae<6;ae++){xe=ve[ae].mipmaps;for(let Ue=0;Ue<xe.length;Ue++){const Ze=xe[Ue];w.format!==ci?He!==null?V?ie&&t.compressedTexSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Ue,0,0,Ze.width,Ze.height,He,Ze.data):t.compressedTexImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Ue,Ye,Ze.width,Ze.height,0,Ze.data):Je("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):V?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Ue,0,0,Ze.width,Ze.height,He,De,Ze.data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Ue,Ye,Ze.width,Ze.height,0,He,De,Ze.data)}}}else{if(xe=w.mipmaps,V&&pe){xe.length>0&&Re++;const ae=we(ve[0]);t.texStorage2D(n.TEXTURE_CUBE_MAP,Re,Ye,ae.width,ae.height)}for(let ae=0;ae<6;ae++)if(Pe){V?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,0,0,0,ve[ae].width,ve[ae].height,He,De,ve[ae].data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,0,Ye,ve[ae].width,ve[ae].height,0,He,De,ve[ae].data);for(let Ue=0;Ue<xe.length;Ue++){const ot=xe[Ue].image[ae].image;V?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Ue+1,0,0,ot.width,ot.height,He,De,ot.data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Ue+1,Ye,ot.width,ot.height,0,He,De,ot.data)}}else{V?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,0,0,0,He,De,ve[ae]):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,0,Ye,He,De,ve[ae]);for(let Ue=0;Ue<xe.length;Ue++){const Ze=xe[Ue];V?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Ue+1,0,0,He,De,Ze.image[ae]):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Ue+1,Ye,He,De,Ze.image[ae])}}}_(w)&&v(n.TEXTURE_CUBE_MAP),ge.__version=oe.version,w.onUpdate&&w.onUpdate(w)}D.__version=w.version}function ce(D,w,z,$,oe,ge){const be=s.convert(z.format,z.colorSpace),ee=s.convert(z.type),re=y(z.internalFormat,be,ee,z.normalized,z.colorSpace),he=i.get(w),Pe=i.get(z);if(Pe.__renderTarget=w,!he.__hasExternalTextures){const ve=Math.max(1,w.width>>ge),Se=Math.max(1,w.height>>ge);oe===n.TEXTURE_3D||oe===n.TEXTURE_2D_ARRAY?t.texImage3D(oe,ge,re,ve,Se,w.depth,0,be,ee,null):t.texImage2D(oe,ge,re,ve,Se,0,be,ee,null)}t.bindFramebuffer(n.FRAMEBUFFER,D),Le(w)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,$,oe,Pe.__webglTexture,0,ue(w)):(oe===n.TEXTURE_2D||oe>=n.TEXTURE_CUBE_MAP_POSITIVE_X&&oe<=n.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&n.framebufferTexture2D(n.FRAMEBUFFER,$,oe,Pe.__webglTexture,ge),t.bindFramebuffer(n.FRAMEBUFFER,null)}function de(D,w,z){if(n.bindRenderbuffer(n.RENDERBUFFER,D),w.depthBuffer){const $=w.depthTexture,oe=$&&$.isDepthTexture?$.type:null,ge=T(w.stencilBuffer,oe),be=w.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;Le(w)?o.renderbufferStorageMultisampleEXT(n.RENDERBUFFER,ue(w),ge,w.width,w.height):z?n.renderbufferStorageMultisample(n.RENDERBUFFER,ue(w),ge,w.width,w.height):n.renderbufferStorage(n.RENDERBUFFER,ge,w.width,w.height),n.framebufferRenderbuffer(n.FRAMEBUFFER,be,n.RENDERBUFFER,D)}else{const $=w.textures;for(let oe=0;oe<$.length;oe++){const ge=$[oe],be=s.convert(ge.format,ge.colorSpace),ee=s.convert(ge.type),re=y(ge.internalFormat,be,ee,ge.normalized,ge.colorSpace);Le(w)?o.renderbufferStorageMultisampleEXT(n.RENDERBUFFER,ue(w),re,w.width,w.height):z?n.renderbufferStorageMultisample(n.RENDERBUFFER,ue(w),re,w.width,w.height):n.renderbufferStorage(n.RENDERBUFFER,re,w.width,w.height)}}n.bindRenderbuffer(n.RENDERBUFFER,null)}function Ne(D,w,z){const $=w.isWebGLCubeRenderTarget===!0;if(t.bindFramebuffer(n.FRAMEBUFFER,D),!(w.depthTexture&&w.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");const oe=i.get(w.depthTexture);if(oe.__renderTarget=w,(!oe.__webglTexture||w.depthTexture.image.width!==w.width||w.depthTexture.image.height!==w.height)&&(w.depthTexture.image.width=w.width,w.depthTexture.image.height=w.height,w.depthTexture.needsUpdate=!0),$){if(oe.__webglInit===void 0&&(oe.__webglInit=!0,w.depthTexture.addEventListener("dispose",E)),oe.__webglTexture===void 0){oe.__webglTexture=n.createTexture(),t.bindTexture(n.TEXTURE_CUBE_MAP,oe.__webglTexture),K(n.TEXTURE_CUBE_MAP,w.depthTexture);const he=s.convert(w.depthTexture.format),Pe=s.convert(w.depthTexture.type);let ve;w.depthTexture.format===Wi?ve=n.DEPTH_COMPONENT24:w.depthTexture.format===lr&&(ve=n.DEPTH24_STENCIL8);for(let Se=0;Se<6;Se++)n.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+Se,0,ve,w.width,w.height,0,he,Pe,null)}}else j(w.depthTexture,0);const ge=oe.__webglTexture,be=ue(w),ee=$?n.TEXTURE_CUBE_MAP_POSITIVE_X+z:n.TEXTURE_2D,re=w.depthTexture.format===lr?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;if(w.depthTexture.format===Wi)Le(w)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,re,ee,ge,0,be):n.framebufferTexture2D(n.FRAMEBUFFER,re,ee,ge,0);else if(w.depthTexture.format===lr)Le(w)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,re,ee,ge,0,be):n.framebufferTexture2D(n.FRAMEBUFFER,re,ee,ge,0);else throw new Error("Unknown depthTexture format")}function Oe(D){const w=i.get(D),z=D.isWebGLCubeRenderTarget===!0;if(w.__boundDepthTexture!==D.depthTexture){const $=D.depthTexture;if(w.__depthDisposeCallback&&w.__depthDisposeCallback(),$){const oe=()=>{delete w.__boundDepthTexture,delete w.__depthDisposeCallback,$.removeEventListener("dispose",oe)};$.addEventListener("dispose",oe),w.__depthDisposeCallback=oe}w.__boundDepthTexture=$}if(D.depthTexture&&!w.__autoAllocateDepthBuffer)if(z)for(let $=0;$<6;$++)Ne(w.__webglFramebuffer[$],D,$);else{const $=D.texture.mipmaps;$&&$.length>0?Ne(w.__webglFramebuffer[0],D,0):Ne(w.__webglFramebuffer,D,0)}else if(z){w.__webglDepthbuffer=[];for(let $=0;$<6;$++)if(t.bindFramebuffer(n.FRAMEBUFFER,w.__webglFramebuffer[$]),w.__webglDepthbuffer[$]===void 0)w.__webglDepthbuffer[$]=n.createRenderbuffer(),de(w.__webglDepthbuffer[$],D,!1);else{const oe=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,ge=w.__webglDepthbuffer[$];n.bindRenderbuffer(n.RENDERBUFFER,ge),n.framebufferRenderbuffer(n.FRAMEBUFFER,oe,n.RENDERBUFFER,ge)}}else{const $=D.texture.mipmaps;if($&&$.length>0?t.bindFramebuffer(n.FRAMEBUFFER,w.__webglFramebuffer[0]):t.bindFramebuffer(n.FRAMEBUFFER,w.__webglFramebuffer),w.__webglDepthbuffer===void 0)w.__webglDepthbuffer=n.createRenderbuffer(),de(w.__webglDepthbuffer,D,!1);else{const oe=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,ge=w.__webglDepthbuffer;n.bindRenderbuffer(n.RENDERBUFFER,ge),n.framebufferRenderbuffer(n.FRAMEBUFFER,oe,n.RENDERBUFFER,ge)}}t.bindFramebuffer(n.FRAMEBUFFER,null)}function Ce(D,w,z){const $=i.get(D);w!==void 0&&ce($.__webglFramebuffer,D,D.texture,n.COLOR_ATTACHMENT0,n.TEXTURE_2D,0),z!==void 0&&Oe(D)}function Te(D){const w=D.texture,z=i.get(D),$=i.get(w);D.addEventListener("dispose",b);const oe=D.textures,ge=D.isWebGLCubeRenderTarget===!0,be=oe.length>1;if(be||($.__webglTexture===void 0&&($.__webglTexture=n.createTexture()),$.__version=w.version,a.memory.textures++),ge){z.__webglFramebuffer=[];for(let ee=0;ee<6;ee++)if(w.mipmaps&&w.mipmaps.length>0){z.__webglFramebuffer[ee]=[];for(let re=0;re<w.mipmaps.length;re++)z.__webglFramebuffer[ee][re]=n.createFramebuffer()}else z.__webglFramebuffer[ee]=n.createFramebuffer()}else{if(w.mipmaps&&w.mipmaps.length>0){z.__webglFramebuffer=[];for(let ee=0;ee<w.mipmaps.length;ee++)z.__webglFramebuffer[ee]=n.createFramebuffer()}else z.__webglFramebuffer=n.createFramebuffer();if(be)for(let ee=0,re=oe.length;ee<re;ee++){const he=i.get(oe[ee]);he.__webglTexture===void 0&&(he.__webglTexture=n.createTexture(),a.memory.textures++)}if(D.samples>0&&Le(D)===!1){z.__webglMultisampledFramebuffer=n.createFramebuffer(),z.__webglColorRenderbuffer=[],t.bindFramebuffer(n.FRAMEBUFFER,z.__webglMultisampledFramebuffer);for(let ee=0;ee<oe.length;ee++){const re=oe[ee];z.__webglColorRenderbuffer[ee]=n.createRenderbuffer(),n.bindRenderbuffer(n.RENDERBUFFER,z.__webglColorRenderbuffer[ee]);const he=s.convert(re.format,re.colorSpace),Pe=s.convert(re.type),ve=y(re.internalFormat,he,Pe,re.normalized,re.colorSpace,D.isXRRenderTarget===!0),Se=ue(D);n.renderbufferStorageMultisample(n.RENDERBUFFER,Se,ve,D.width,D.height),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+ee,n.RENDERBUFFER,z.__webglColorRenderbuffer[ee])}n.bindRenderbuffer(n.RENDERBUFFER,null),D.depthBuffer&&(z.__webglDepthRenderbuffer=n.createRenderbuffer(),de(z.__webglDepthRenderbuffer,D,!0)),t.bindFramebuffer(n.FRAMEBUFFER,null)}}if(ge){t.bindTexture(n.TEXTURE_CUBE_MAP,$.__webglTexture),K(n.TEXTURE_CUBE_MAP,w);for(let ee=0;ee<6;ee++)if(w.mipmaps&&w.mipmaps.length>0)for(let re=0;re<w.mipmaps.length;re++)ce(z.__webglFramebuffer[ee][re],D,w,n.COLOR_ATTACHMENT0,n.TEXTURE_CUBE_MAP_POSITIVE_X+ee,re);else ce(z.__webglFramebuffer[ee],D,w,n.COLOR_ATTACHMENT0,n.TEXTURE_CUBE_MAP_POSITIVE_X+ee,0);_(w)&&v(n.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(be){for(let ee=0,re=oe.length;ee<re;ee++){const he=oe[ee],Pe=i.get(he);let ve=n.TEXTURE_2D;(D.isWebGL3DRenderTarget||D.isWebGLArrayRenderTarget)&&(ve=D.isWebGL3DRenderTarget?n.TEXTURE_3D:n.TEXTURE_2D_ARRAY),t.bindTexture(ve,Pe.__webglTexture),K(ve,he),ce(z.__webglFramebuffer,D,he,n.COLOR_ATTACHMENT0+ee,ve,0),_(he)&&v(ve)}t.unbindTexture()}else{let ee=n.TEXTURE_2D;if((D.isWebGL3DRenderTarget||D.isWebGLArrayRenderTarget)&&(ee=D.isWebGL3DRenderTarget?n.TEXTURE_3D:n.TEXTURE_2D_ARRAY),t.bindTexture(ee,$.__webglTexture),K(ee,w),w.mipmaps&&w.mipmaps.length>0)for(let re=0;re<w.mipmaps.length;re++)ce(z.__webglFramebuffer[re],D,w,n.COLOR_ATTACHMENT0,ee,re);else ce(z.__webglFramebuffer,D,w,n.COLOR_ATTACHMENT0,ee,0);_(w)&&v(ee),t.unbindTexture()}D.depthBuffer&&Oe(D)}function Ge(D){const w=D.textures;for(let z=0,$=w.length;z<$;z++){const oe=w[z];if(_(oe)){const ge=M(D),be=i.get(oe).__webglTexture;t.bindTexture(ge,be),v(ge),t.unbindTexture()}}}const _e=[],ze=[];function B(D){if(D.samples>0){if(Le(D)===!1){const w=D.textures,z=D.width,$=D.height;let oe=n.COLOR_BUFFER_BIT;const ge=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,be=i.get(D),ee=w.length>1;if(ee)for(let he=0;he<w.length;he++)t.bindFramebuffer(n.FRAMEBUFFER,be.__webglMultisampledFramebuffer),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+he,n.RENDERBUFFER,null),t.bindFramebuffer(n.FRAMEBUFFER,be.__webglFramebuffer),n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0+he,n.TEXTURE_2D,null,0);t.bindFramebuffer(n.READ_FRAMEBUFFER,be.__webglMultisampledFramebuffer);const re=D.texture.mipmaps;re&&re.length>0?t.bindFramebuffer(n.DRAW_FRAMEBUFFER,be.__webglFramebuffer[0]):t.bindFramebuffer(n.DRAW_FRAMEBUFFER,be.__webglFramebuffer);for(let he=0;he<w.length;he++){if(D.resolveDepthBuffer&&(D.depthBuffer&&(oe|=n.DEPTH_BUFFER_BIT),D.stencilBuffer&&D.resolveStencilBuffer&&(oe|=n.STENCIL_BUFFER_BIT)),ee){n.framebufferRenderbuffer(n.READ_FRAMEBUFFER,n.COLOR_ATTACHMENT0,n.RENDERBUFFER,be.__webglColorRenderbuffer[he]);const Pe=i.get(w[he]).__webglTexture;n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0,n.TEXTURE_2D,Pe,0)}n.blitFramebuffer(0,0,z,$,0,0,z,$,oe,n.NEAREST),l===!0&&(_e.length=0,ze.length=0,_e.push(n.COLOR_ATTACHMENT0+he),D.depthBuffer&&D.resolveDepthBuffer===!1&&(_e.push(ge),ze.push(ge),n.invalidateFramebuffer(n.DRAW_FRAMEBUFFER,ze)),n.invalidateFramebuffer(n.READ_FRAMEBUFFER,_e))}if(t.bindFramebuffer(n.READ_FRAMEBUFFER,null),t.bindFramebuffer(n.DRAW_FRAMEBUFFER,null),ee)for(let he=0;he<w.length;he++){t.bindFramebuffer(n.FRAMEBUFFER,be.__webglMultisampledFramebuffer),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+he,n.RENDERBUFFER,be.__webglColorRenderbuffer[he]);const Pe=i.get(w[he]).__webglTexture;t.bindFramebuffer(n.FRAMEBUFFER,be.__webglFramebuffer),n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0+he,n.TEXTURE_2D,Pe,0)}t.bindFramebuffer(n.DRAW_FRAMEBUFFER,be.__webglMultisampledFramebuffer)}else if(D.depthBuffer&&D.resolveDepthBuffer===!1&&l){const w=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;n.invalidateFramebuffer(n.DRAW_FRAMEBUFFER,[w])}}}function ue(D){return Math.min(r.maxSamples,D.samples)}function Le(D){const w=i.get(D);return D.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&w.__useRenderToTexture!==!1}function Ee(D){const w=a.render.frame;u.get(D)!==w&&(u.set(D,w),D.update())}function le(D,w){const z=D.colorSpace,$=D.format,oe=D.type;return D.isCompressedTexture===!0||D.isVideoTexture===!0||z!==zs&&z!==bi&&(ft.getTransfer(z)===Mt?($!==ci||oe!==jt)&&Je("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):pt("WebGLTextures: Unsupported texture color space:",z)),w}function we(D){return typeof HTMLImageElement<"u"&&D instanceof HTMLImageElement?(c.width=D.naturalWidth||D.width,c.height=D.naturalHeight||D.height):typeof VideoFrame<"u"&&D instanceof VideoFrame?(c.width=D.displayWidth,c.height=D.displayHeight):(c.width=D.width,c.height=D.height),c}this.allocateTextureUnit=F,this.resetTextureUnits=L,this.getTextureUnits=U,this.setTextureUnits=I,this.setTexture2D=j,this.setTexture2DArray=G,this.setTexture3D=W,this.setTextureCube=N,this.rebindTextures=Ce,this.setupRenderTarget=Te,this.updateRenderTargetMipmap=Ge,this.updateMultisampleRenderTarget=B,this.setupDepthRenderbuffer=Oe,this.setupFrameBufferTexture=ce,this.useMultisampledRTT=Le,this.isReversedDepthBuffer=function(){return t.buffers.depth.getReversed()}}function AS(n,e){function t(i,r=bi){let s;const a=ft.getTransfer(r);if(i===jt)return n.UNSIGNED_BYTE;if(i===qh)return n.UNSIGNED_SHORT_4_4_4_4;if(i===Kh)return n.UNSIGNED_SHORT_5_5_5_1;if(i===Cm)return n.UNSIGNED_INT_5_9_9_9_REV;if(i===Pm)return n.UNSIGNED_INT_10F_11F_11F_REV;if(i===Am)return n.BYTE;if(i===Rm)return n.SHORT;if(i===Ba)return n.UNSIGNED_SHORT;if(i===Yh)return n.INT;if(i===Ri)return n.UNSIGNED_INT;if(i===li)return n.FLOAT;if(i===Vi)return n.HALF_FLOAT;if(i===Dm)return n.ALPHA;if(i===Um)return n.RGB;if(i===ci)return n.RGBA;if(i===Wi)return n.DEPTH_COMPONENT;if(i===lr)return n.DEPTH_STENCIL;if(i===Lm)return n.RED;if(i===Zh)return n.RED_INTEGER;if(i===qr)return n.RG;if(i===$h)return n.RG_INTEGER;if(i===Jh)return n.RGBA_INTEGER;if(i===qo||i===Ko||i===Zo||i===$o)if(a===Mt)if(s=e.get("WEBGL_compressed_texture_s3tc_srgb"),s!==null){if(i===qo)return s.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(i===Ko)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(i===Zo)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(i===$o)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(s=e.get("WEBGL_compressed_texture_s3tc"),s!==null){if(i===qo)return s.COMPRESSED_RGB_S3TC_DXT1_EXT;if(i===Ko)return s.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(i===Zo)return s.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(i===$o)return s.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(i===Ou||i===Bu||i===ku||i===zu)if(s=e.get("WEBGL_compressed_texture_pvrtc"),s!==null){if(i===Ou)return s.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(i===Bu)return s.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(i===ku)return s.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(i===zu)return s.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(i===Gu||i===Hu||i===Vu||i===Wu||i===Xu||i===ll||i===ju)if(s=e.get("WEBGL_compressed_texture_etc"),s!==null){if(i===Gu||i===Hu)return a===Mt?s.COMPRESSED_SRGB8_ETC2:s.COMPRESSED_RGB8_ETC2;if(i===Vu)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:s.COMPRESSED_RGBA8_ETC2_EAC;if(i===Wu)return s.COMPRESSED_R11_EAC;if(i===Xu)return s.COMPRESSED_SIGNED_R11_EAC;if(i===ll)return s.COMPRESSED_RG11_EAC;if(i===ju)return s.COMPRESSED_SIGNED_RG11_EAC}else return null;if(i===Yu||i===qu||i===Ku||i===Zu||i===$u||i===Ju||i===Qu||i===eh||i===th||i===nh||i===ih||i===rh||i===sh||i===ah)if(s=e.get("WEBGL_compressed_texture_astc"),s!==null){if(i===Yu)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:s.COMPRESSED_RGBA_ASTC_4x4_KHR;if(i===qu)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:s.COMPRESSED_RGBA_ASTC_5x4_KHR;if(i===Ku)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:s.COMPRESSED_RGBA_ASTC_5x5_KHR;if(i===Zu)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:s.COMPRESSED_RGBA_ASTC_6x5_KHR;if(i===$u)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:s.COMPRESSED_RGBA_ASTC_6x6_KHR;if(i===Ju)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:s.COMPRESSED_RGBA_ASTC_8x5_KHR;if(i===Qu)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:s.COMPRESSED_RGBA_ASTC_8x6_KHR;if(i===eh)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:s.COMPRESSED_RGBA_ASTC_8x8_KHR;if(i===th)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:s.COMPRESSED_RGBA_ASTC_10x5_KHR;if(i===nh)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:s.COMPRESSED_RGBA_ASTC_10x6_KHR;if(i===ih)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:s.COMPRESSED_RGBA_ASTC_10x8_KHR;if(i===rh)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:s.COMPRESSED_RGBA_ASTC_10x10_KHR;if(i===sh)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:s.COMPRESSED_RGBA_ASTC_12x10_KHR;if(i===ah)return a===Mt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:s.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(i===oh||i===lh||i===ch)if(s=e.get("EXT_texture_compression_bptc"),s!==null){if(i===oh)return a===Mt?s.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:s.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(i===lh)return s.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(i===ch)return s.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(i===uh||i===hh||i===cl||i===fh)if(s=e.get("EXT_texture_compression_rgtc"),s!==null){if(i===uh)return s.COMPRESSED_RED_RGTC1_EXT;if(i===hh)return s.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(i===cl)return s.COMPRESSED_RED_GREEN_RGTC2_EXT;if(i===fh)return s.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return i===ks?n.UNSIGNED_INT_24_8:n[i]!==void 0?n[i]:null}return{convert:t}}const RS=`
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

}`;class PS{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){const i=new Vm(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=i}}getMesh(e){if(this.texture!==null&&this.mesh===null){const t=e.cameras[0].viewport,i=new an({vertexShader:RS,fragmentShader:CS,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new Wn(new Zr(20,20),i)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class DS extends hi{constructor(e,t){super();const i=this;let r=null,s=1,a=null,o="local-floor",l=1,c=null,u=null,f=null,h=null,d=null,g=null;const m=typeof XRWebGLBinding<"u",p=new PS,_={},v=t.getContextAttributes();let M=null,y=null;const T=[],S=[],E=new Xe;let b=null;const x=new kn;x.viewport=new Dt;const A=new kn;A.viewport=new Dt;const C=[x,A],R=new kv;let L=null,U=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(H){let Y=T[H];return Y===void 0&&(Y=new vc,T[H]=Y),Y.getTargetRaySpace()},this.getControllerGrip=function(H){let Y=T[H];return Y===void 0&&(Y=new vc,T[H]=Y),Y.getGripSpace()},this.getHand=function(H){let Y=T[H];return Y===void 0&&(Y=new vc,T[H]=Y),Y.getHandSpace()};function I(H){const Y=S.indexOf(H.inputSource);if(Y===-1)return;const Z=T[Y];Z!==void 0&&(Z.update(H.inputSource,H.frame,c||a),Z.dispatchEvent({type:H.type,data:H.inputSource}))}function F(){r.removeEventListener("select",I),r.removeEventListener("selectstart",I),r.removeEventListener("selectend",I),r.removeEventListener("squeeze",I),r.removeEventListener("squeezestart",I),r.removeEventListener("squeezeend",I),r.removeEventListener("end",F),r.removeEventListener("inputsourceschange",O);for(let H=0;H<T.length;H++){const Y=S[H];Y!==null&&(S[H]=null,T[H].disconnect(Y))}L=null,U=null,p.reset();for(const H in _)delete _[H];e.setRenderTarget(M),d=null,h=null,f=null,r=null,y=null,K.stop(),i.isPresenting=!1,e.setPixelRatio(b),e.setSize(E.width,E.height,!1),i.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(H){s=H,i.isPresenting===!0&&Je("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(H){o=H,i.isPresenting===!0&&Je("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||a},this.setReferenceSpace=function(H){c=H},this.getBaseLayer=function(){return h!==null?h:d},this.getBinding=function(){return f===null&&m&&(f=new XRWebGLBinding(r,t)),f},this.getFrame=function(){return g},this.getSession=function(){return r},this.setSession=async function(H){if(r=H,r!==null){if(M=e.getRenderTarget(),r.addEventListener("select",I),r.addEventListener("selectstart",I),r.addEventListener("selectend",I),r.addEventListener("squeeze",I),r.addEventListener("squeezestart",I),r.addEventListener("squeezeend",I),r.addEventListener("end",F),r.addEventListener("inputsourceschange",O),v.xrCompatible!==!0&&await t.makeXRCompatible(),b=e.getPixelRatio(),e.getSize(E),m&&"createProjectionLayer"in XRWebGLBinding.prototype){let Z=null,fe=null,Me=null;v.depth&&(Me=v.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,Z=v.stencil?lr:Wi,fe=v.stencil?ks:Ri);const ce={colorFormat:t.RGBA8,depthFormat:Me,scaleFactor:s};f=this.getBinding(),h=f.createProjectionLayer(ce),r.updateRenderState({layers:[h]}),e.setPixelRatio(1),e.setSize(h.textureWidth,h.textureHeight,!1),y=new $t(h.textureWidth,h.textureHeight,{format:ci,type:jt,depthTexture:new Gi(h.textureWidth,h.textureHeight,fe,void 0,void 0,void 0,void 0,void 0,void 0,Z),stencilBuffer:v.stencil,colorSpace:e.outputColorSpace,samples:v.antialias?4:0,resolveDepthBuffer:h.ignoreDepthValues===!1,resolveStencilBuffer:h.ignoreDepthValues===!1})}else{const Z={antialias:v.antialias,alpha:!0,depth:v.depth,stencil:v.stencil,framebufferScaleFactor:s};d=new XRWebGLLayer(r,t,Z),r.updateRenderState({baseLayer:d}),e.setPixelRatio(1),e.setSize(d.framebufferWidth,d.framebufferHeight,!1),y=new $t(d.framebufferWidth,d.framebufferHeight,{format:ci,type:jt,colorSpace:e.outputColorSpace,stencilBuffer:v.stencil,resolveDepthBuffer:d.ignoreDepthValues===!1,resolveStencilBuffer:d.ignoreDepthValues===!1})}y.isXRRenderTarget=!0,this.setFoveation(l),c=null,a=await r.requestReferenceSpace(o),K.setContext(r),K.start(),i.isPresenting=!0,i.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(r!==null)return r.environmentBlendMode},this.getDepthTexture=function(){return p.getDepthTexture()};function O(H){for(let Y=0;Y<H.removed.length;Y++){const Z=H.removed[Y],fe=S.indexOf(Z);fe>=0&&(S[fe]=null,T[fe].disconnect(Z))}for(let Y=0;Y<H.added.length;Y++){const Z=H.added[Y];let fe=S.indexOf(Z);if(fe===-1){for(let ce=0;ce<T.length;ce++)if(ce>=S.length){S.push(Z),fe=ce;break}else if(S[ce]===null){S[ce]=Z,fe=ce;break}if(fe===-1)break}const Me=T[fe];Me&&Me.connect(Z)}}const j=new X,G=new X;function W(H,Y,Z){j.setFromMatrixPosition(Y.matrixWorld),G.setFromMatrixPosition(Z.matrixWorld);const fe=j.distanceTo(G),Me=Y.projectionMatrix.elements,ce=Z.projectionMatrix.elements,de=Me[14]/(Me[10]-1),Ne=Me[14]/(Me[10]+1),Oe=(Me[9]+1)/Me[5],Ce=(Me[9]-1)/Me[5],Te=(Me[8]-1)/Me[0],Ge=(ce[8]+1)/ce[0],_e=de*Te,ze=de*Ge,B=fe/(-Te+Ge),ue=B*-Te;if(Y.matrixWorld.decompose(H.position,H.quaternion,H.scale),H.translateX(ue),H.translateZ(B),H.matrixWorld.compose(H.position,H.quaternion,H.scale),H.matrixWorldInverse.copy(H.matrixWorld).invert(),Me[10]===-1)H.projectionMatrix.copy(Y.projectionMatrix),H.projectionMatrixInverse.copy(Y.projectionMatrixInverse);else{const Le=de+B,Ee=Ne+B,le=_e-ue,we=ze+(fe-ue),D=Oe*Ne/Ee*Le,w=Ce*Ne/Ee*Le;H.projectionMatrix.makePerspective(le,we,D,w,Le,Ee),H.projectionMatrixInverse.copy(H.projectionMatrix).invert()}}function N(H,Y){Y===null?H.matrixWorld.copy(H.matrix):H.matrixWorld.multiplyMatrices(Y.matrixWorld,H.matrix),H.matrixWorldInverse.copy(H.matrixWorld).invert()}this.updateCamera=function(H){if(r===null)return;let Y=H.near,Z=H.far;p.texture!==null&&(p.depthNear>0&&(Y=p.depthNear),p.depthFar>0&&(Z=p.depthFar)),R.near=A.near=x.near=Y,R.far=A.far=x.far=Z,(L!==R.near||U!==R.far)&&(r.updateRenderState({depthNear:R.near,depthFar:R.far}),L=R.near,U=R.far),R.layers.mask=H.layers.mask|6,x.layers.mask=R.layers.mask&-5,A.layers.mask=R.layers.mask&-3;const fe=H.parent,Me=R.cameras;N(R,fe);for(let ce=0;ce<Me.length;ce++)N(Me[ce],fe);Me.length===2?W(R,x,A):R.projectionMatrix.copy(x.projectionMatrix),k(H,R,fe)};function k(H,Y,Z){Z===null?H.matrix.copy(Y.matrixWorld):(H.matrix.copy(Z.matrixWorld),H.matrix.invert(),H.matrix.multiply(Y.matrixWorld)),H.matrix.decompose(H.position,H.quaternion,H.scale),H.updateMatrixWorld(!0),H.projectionMatrix.copy(Y.projectionMatrix),H.projectionMatrixInverse.copy(Y.projectionMatrixInverse),H.isPerspectiveCamera&&(H.fov=mh*2*Math.atan(1/H.projectionMatrix.elements[5]),H.zoom=1)}this.getCamera=function(){return R},this.getFoveation=function(){if(!(h===null&&d===null))return l},this.setFoveation=function(H){l=H,h!==null&&(h.fixedFoveation=H),d!==null&&d.fixedFoveation!==void 0&&(d.fixedFoveation=H)},this.hasDepthSensing=function(){return p.texture!==null},this.getDepthSensingMesh=function(){return p.getMesh(R)},this.getCameraTexture=function(H){return _[H]};let J=null;function Q(H,Y){if(u=Y.getViewerPose(c||a),g=Y,u!==null){const Z=u.views;d!==null&&(e.setRenderTargetFramebuffer(y,d.framebuffer),e.setRenderTarget(y));let fe=!1;Z.length!==R.cameras.length&&(R.cameras.length=0,fe=!0);for(let Ne=0;Ne<Z.length;Ne++){const Oe=Z[Ne];let Ce=null;if(d!==null)Ce=d.getViewport(Oe);else{const Ge=f.getViewSubImage(h,Oe);Ce=Ge.viewport,Ne===0&&(e.setRenderTargetTextures(y,Ge.colorTexture,Ge.depthStencilTexture),e.setRenderTarget(y))}let Te=C[Ne];Te===void 0&&(Te=new kn,Te.layers.enable(Ne),Te.viewport=new Dt,C[Ne]=Te),Te.matrix.fromArray(Oe.transform.matrix),Te.matrix.decompose(Te.position,Te.quaternion,Te.scale),Te.projectionMatrix.fromArray(Oe.projectionMatrix),Te.projectionMatrixInverse.copy(Te.projectionMatrix).invert(),Te.viewport.set(Ce.x,Ce.y,Ce.width,Ce.height),Ne===0&&(R.matrix.copy(Te.matrix),R.matrix.decompose(R.position,R.quaternion,R.scale)),fe===!0&&R.cameras.push(Te)}const Me=r.enabledFeatures;if(Me&&Me.includes("depth-sensing")&&r.depthUsage=="gpu-optimized"&&m){f=i.getBinding();const Ne=f.getDepthInformation(Z[0]);Ne&&Ne.isValid&&Ne.texture&&p.init(Ne,r.renderState)}if(Me&&Me.includes("camera-access")&&m){e.state.unbindTexture(),f=i.getBinding();for(let Ne=0;Ne<Z.length;Ne++){const Oe=Z[Ne].camera;if(Oe){let Ce=_[Oe];Ce||(Ce=new Vm,_[Oe]=Ce);const Te=f.getCameraImage(Oe);Ce.sourceTexture=Te}}}}for(let Z=0;Z<T.length;Z++){const fe=S[Z],Me=T[Z];fe!==null&&Me!==void 0&&Me.update(fe,Y,c||a)}J&&J(H,Y),Y.detectedPlanes&&i.dispatchEvent({type:"planesdetected",data:Y}),g=null}const K=new Km;K.setAnimationLoop(Q),this.setAnimationLoop=function(H){J=H},this.dispose=function(){}}}const US=new kt,n0=new rt;n0.set(-1,0,0,0,1,0,0,0,1);function LS(n,e){function t(p,_){p.matrixAutoUpdate===!0&&p.updateMatrix(),_.value.copy(p.matrix)}function i(p,_){_.color.getRGB(p.fogColor.value,Wm(n)),_.isFog?(p.fogNear.value=_.near,p.fogFar.value=_.far):_.isFogExp2&&(p.fogDensity.value=_.density)}function r(p,_,v,M,y){_.isNodeMaterial?_.uniformsNeedUpdate=!1:_.isMeshBasicMaterial?s(p,_):_.isMeshLambertMaterial?(s(p,_),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)):_.isMeshToonMaterial?(s(p,_),f(p,_)):_.isMeshPhongMaterial?(s(p,_),u(p,_),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)):_.isMeshStandardMaterial?(s(p,_),h(p,_),_.isMeshPhysicalMaterial&&d(p,_,y)):_.isMeshMatcapMaterial?(s(p,_),g(p,_)):_.isMeshDepthMaterial?s(p,_):_.isMeshDistanceMaterial?(s(p,_),m(p,_)):_.isMeshNormalMaterial?s(p,_):_.isLineBasicMaterial?(a(p,_),_.isLineDashedMaterial&&o(p,_)):_.isPointsMaterial?l(p,_,v,M):_.isSpriteMaterial?c(p,_):_.isShadowMaterial?(p.color.value.copy(_.color),p.opacity.value=_.opacity):_.isShaderMaterial&&(_.uniformsNeedUpdate=!1)}function s(p,_){p.opacity.value=_.opacity,_.color&&p.diffuse.value.copy(_.color),_.emissive&&p.emissive.value.copy(_.emissive).multiplyScalar(_.emissiveIntensity),_.map&&(p.map.value=_.map,t(_.map,p.mapTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.bumpMap&&(p.bumpMap.value=_.bumpMap,t(_.bumpMap,p.bumpMapTransform),p.bumpScale.value=_.bumpScale,_.side===sn&&(p.bumpScale.value*=-1)),_.normalMap&&(p.normalMap.value=_.normalMap,t(_.normalMap,p.normalMapTransform),p.normalScale.value.copy(_.normalScale),_.side===sn&&p.normalScale.value.negate()),_.displacementMap&&(p.displacementMap.value=_.displacementMap,t(_.displacementMap,p.displacementMapTransform),p.displacementScale.value=_.displacementScale,p.displacementBias.value=_.displacementBias),_.emissiveMap&&(p.emissiveMap.value=_.emissiveMap,t(_.emissiveMap,p.emissiveMapTransform)),_.specularMap&&(p.specularMap.value=_.specularMap,t(_.specularMap,p.specularMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest);const v=e.get(_),M=v.envMap,y=v.envMapRotation;M&&(p.envMap.value=M,p.envMapRotation.value.setFromMatrix4(US.makeRotationFromEuler(y)).transpose(),M.isCubeTexture&&M.isRenderTargetTexture===!1&&p.envMapRotation.value.premultiply(n0),p.reflectivity.value=_.reflectivity,p.ior.value=_.ior,p.refractionRatio.value=_.refractionRatio),_.lightMap&&(p.lightMap.value=_.lightMap,p.lightMapIntensity.value=_.lightMapIntensity,t(_.lightMap,p.lightMapTransform)),_.aoMap&&(p.aoMap.value=_.aoMap,p.aoMapIntensity.value=_.aoMapIntensity,t(_.aoMap,p.aoMapTransform))}function a(p,_){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,_.map&&(p.map.value=_.map,t(_.map,p.mapTransform))}function o(p,_){p.dashSize.value=_.dashSize,p.totalSize.value=_.dashSize+_.gapSize,p.scale.value=_.scale}function l(p,_,v,M){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,p.size.value=_.size*v,p.scale.value=M*.5,_.map&&(p.map.value=_.map,t(_.map,p.uvTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest)}function c(p,_){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,p.rotation.value=_.rotation,_.map&&(p.map.value=_.map,t(_.map,p.mapTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest)}function u(p,_){p.specular.value.copy(_.specular),p.shininess.value=Math.max(_.shininess,1e-4)}function f(p,_){_.gradientMap&&(p.gradientMap.value=_.gradientMap)}function h(p,_){p.metalness.value=_.metalness,_.metalnessMap&&(p.metalnessMap.value=_.metalnessMap,t(_.metalnessMap,p.metalnessMapTransform)),p.roughness.value=_.roughness,_.roughnessMap&&(p.roughnessMap.value=_.roughnessMap,t(_.roughnessMap,p.roughnessMapTransform)),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)}function d(p,_,v){p.ior.value=_.ior,_.sheen>0&&(p.sheenColor.value.copy(_.sheenColor).multiplyScalar(_.sheen),p.sheenRoughness.value=_.sheenRoughness,_.sheenColorMap&&(p.sheenColorMap.value=_.sheenColorMap,t(_.sheenColorMap,p.sheenColorMapTransform)),_.sheenRoughnessMap&&(p.sheenRoughnessMap.value=_.sheenRoughnessMap,t(_.sheenRoughnessMap,p.sheenRoughnessMapTransform))),_.clearcoat>0&&(p.clearcoat.value=_.clearcoat,p.clearcoatRoughness.value=_.clearcoatRoughness,_.clearcoatMap&&(p.clearcoatMap.value=_.clearcoatMap,t(_.clearcoatMap,p.clearcoatMapTransform)),_.clearcoatRoughnessMap&&(p.clearcoatRoughnessMap.value=_.clearcoatRoughnessMap,t(_.clearcoatRoughnessMap,p.clearcoatRoughnessMapTransform)),_.clearcoatNormalMap&&(p.clearcoatNormalMap.value=_.clearcoatNormalMap,t(_.clearcoatNormalMap,p.clearcoatNormalMapTransform),p.clearcoatNormalScale.value.copy(_.clearcoatNormalScale),_.side===sn&&p.clearcoatNormalScale.value.negate())),_.dispersion>0&&(p.dispersion.value=_.dispersion),_.iridescence>0&&(p.iridescence.value=_.iridescence,p.iridescenceIOR.value=_.iridescenceIOR,p.iridescenceThicknessMinimum.value=_.iridescenceThicknessRange[0],p.iridescenceThicknessMaximum.value=_.iridescenceThicknessRange[1],_.iridescenceMap&&(p.iridescenceMap.value=_.iridescenceMap,t(_.iridescenceMap,p.iridescenceMapTransform)),_.iridescenceThicknessMap&&(p.iridescenceThicknessMap.value=_.iridescenceThicknessMap,t(_.iridescenceThicknessMap,p.iridescenceThicknessMapTransform))),_.transmission>0&&(p.transmission.value=_.transmission,p.transmissionSamplerMap.value=v.texture,p.transmissionSamplerSize.value.set(v.width,v.height),_.transmissionMap&&(p.transmissionMap.value=_.transmissionMap,t(_.transmissionMap,p.transmissionMapTransform)),p.thickness.value=_.thickness,_.thicknessMap&&(p.thicknessMap.value=_.thicknessMap,t(_.thicknessMap,p.thicknessMapTransform)),p.attenuationDistance.value=_.attenuationDistance,p.attenuationColor.value.copy(_.attenuationColor)),_.anisotropy>0&&(p.anisotropyVector.value.set(_.anisotropy*Math.cos(_.anisotropyRotation),_.anisotropy*Math.sin(_.anisotropyRotation)),_.anisotropyMap&&(p.anisotropyMap.value=_.anisotropyMap,t(_.anisotropyMap,p.anisotropyMapTransform))),p.specularIntensity.value=_.specularIntensity,p.specularColor.value.copy(_.specularColor),_.specularColorMap&&(p.specularColorMap.value=_.specularColorMap,t(_.specularColorMap,p.specularColorMapTransform)),_.specularIntensityMap&&(p.specularIntensityMap.value=_.specularIntensityMap,t(_.specularIntensityMap,p.specularIntensityMapTransform))}function g(p,_){_.matcap&&(p.matcap.value=_.matcap)}function m(p,_){const v=e.get(_).light;p.referencePosition.value.setFromMatrixPosition(v.matrixWorld),p.nearDistance.value=v.shadow.camera.near,p.farDistance.value=v.shadow.camera.far}return{refreshFogUniforms:i,refreshMaterialUniforms:r}}function IS(n,e,t,i){let r={},s={},a=[];const o=n.getParameter(n.MAX_UNIFORM_BUFFER_BINDINGS);function l(v,M){const y=M.program;i.uniformBlockBinding(v,y)}function c(v,M){let y=r[v.id];y===void 0&&(g(v),y=u(v),r[v.id]=y,v.addEventListener("dispose",p));const T=M.program;i.updateUBOMapping(v,T);const S=e.render.frame;s[v.id]!==S&&(h(v),s[v.id]=S)}function u(v){const M=f();v.__bindingPointIndex=M;const y=n.createBuffer(),T=v.__size,S=v.usage;return n.bindBuffer(n.UNIFORM_BUFFER,y),n.bufferData(n.UNIFORM_BUFFER,T,S),n.bindBuffer(n.UNIFORM_BUFFER,null),n.bindBufferBase(n.UNIFORM_BUFFER,M,y),y}function f(){for(let v=0;v<o;v++)if(a.indexOf(v)===-1)return a.push(v),v;return pt("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function h(v){const M=r[v.id],y=v.uniforms,T=v.__cache;n.bindBuffer(n.UNIFORM_BUFFER,M);for(let S=0,E=y.length;S<E;S++){const b=Array.isArray(y[S])?y[S]:[y[S]];for(let x=0,A=b.length;x<A;x++){const C=b[x];if(d(C,S,x,T)===!0){const R=C.__offset,L=Array.isArray(C.value)?C.value:[C.value];let U=0;for(let I=0;I<L.length;I++){const F=L[I],O=m(F);typeof F=="number"||typeof F=="boolean"?(C.__data[0]=F,n.bufferSubData(n.UNIFORM_BUFFER,R+U,C.__data)):F.isMatrix3?(C.__data[0]=F.elements[0],C.__data[1]=F.elements[1],C.__data[2]=F.elements[2],C.__data[3]=0,C.__data[4]=F.elements[3],C.__data[5]=F.elements[4],C.__data[6]=F.elements[5],C.__data[7]=0,C.__data[8]=F.elements[6],C.__data[9]=F.elements[7],C.__data[10]=F.elements[8],C.__data[11]=0):ArrayBuffer.isView(F)?C.__data.set(new F.constructor(F.buffer,F.byteOffset,C.__data.length)):(F.toArray(C.__data,U),U+=O.storage/Float32Array.BYTES_PER_ELEMENT)}n.bufferSubData(n.UNIFORM_BUFFER,R,C.__data)}}}n.bindBuffer(n.UNIFORM_BUFFER,null)}function d(v,M,y,T){const S=v.value,E=M+"_"+y;if(T[E]===void 0)return typeof S=="number"||typeof S=="boolean"?T[E]=S:ArrayBuffer.isView(S)?T[E]=S.slice():T[E]=S.clone(),!0;{const b=T[E];if(typeof S=="number"||typeof S=="boolean"){if(b!==S)return T[E]=S,!0}else{if(ArrayBuffer.isView(S))return!0;if(b.equals(S)===!1)return b.copy(S),!0}}return!1}function g(v){const M=v.uniforms;let y=0;const T=16;for(let E=0,b=M.length;E<b;E++){const x=Array.isArray(M[E])?M[E]:[M[E]];for(let A=0,C=x.length;A<C;A++){const R=x[A],L=Array.isArray(R.value)?R.value:[R.value];for(let U=0,I=L.length;U<I;U++){const F=L[U],O=m(F),j=y%T,G=j%O.boundary,W=j+G;y+=G,W!==0&&T-W<O.storage&&(y+=T-W),R.__data=new Float32Array(O.storage/Float32Array.BYTES_PER_ELEMENT),R.__offset=y,y+=O.storage}}}const S=y%T;return S>0&&(y+=T-S),v.__size=y,v.__cache={},this}function m(v){const M={boundary:0,storage:0};return typeof v=="number"||typeof v=="boolean"?(M.boundary=4,M.storage=4):v.isVector2?(M.boundary=8,M.storage=8):v.isVector3||v.isColor?(M.boundary=16,M.storage=12):v.isVector4?(M.boundary=16,M.storage=16):v.isMatrix3?(M.boundary=48,M.storage=48):v.isMatrix4?(M.boundary=64,M.storage=64):v.isTexture?Je("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(v)?(M.boundary=16,M.storage=v.byteLength):Je("WebGLRenderer: Unsupported uniform value type.",v),M}function p(v){const M=v.target;M.removeEventListener("dispose",p);const y=a.indexOf(M.__bindingPointIndex);a.splice(y,1),n.deleteBuffer(r[M.id]),delete r[M.id],delete s[M.id]}function _(){for(const v in r)n.deleteBuffer(r[v]);a=[],r={},s={}}return{bind:l,update:c,dispose:_}}const FS=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]);let _i=null;function NS(){return _i===null&&(_i=new Tv(FS,16,16,qr,Vi),_i.name="DFG_LUT",_i.minFilter=zt,_i.magFilter=zt,_i.wrapS=ki,_i.wrapT=ki,_i.generateMipmaps=!1,_i.needsUpdate=!0),_i}class OS{constructor(e={}){const{canvas:t=ev(),context:i=null,depth:r=!0,stencil:s=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:u="default",failIfMajorPerformanceCaveat:f=!1,reversedDepthBuffer:h=!1,outputBufferType:d=jt}=e;this.isWebGLRenderer=!0;let g;if(i!==null){if(typeof WebGLRenderingContext<"u"&&i instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");g=i.getContextAttributes().alpha}else g=a;const m=d,p=new Set([Jh,$h,Zh]),_=new Set([jt,Ri,Ba,ks,qh,Kh]),v=new Uint32Array(4),M=new Int32Array(4),y=new X;let T=null,S=null;const E=[],b=[];let x=null;this.domElement=t,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=Ai,this.toneMappingExposure=1,this.transmissionResolutionScale=1;const A=this;let C=!1,R=null;this._outputColorSpace=Tt;let L=0,U=0,I=null,F=-1,O=null;const j=new Dt,G=new Dt;let W=null;const N=new ut(0);let k=0,J=t.width,Q=t.height,K=1,H=null,Y=null;const Z=new Dt(0,0,J,Q),fe=new Dt(0,0,J,Q);let Me=!1;const ce=new Gm;let de=!1,Ne=!1;const Oe=new kt,Ce=new X,Te=new Dt,Ge={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let _e=!1;function ze(){return I===null?K:1}let B=i;function ue(P,q){return t.getContext(P,q)}try{const P={alpha:!0,depth:r,stencil:s,antialias:o,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:u,failIfMajorPerformanceCaveat:f};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${qa}`),t.addEventListener("webglcontextlost",ae,!1),t.addEventListener("webglcontextrestored",Ue,!1),t.addEventListener("webglcontextcreationerror",Ze,!1),B===null){const q="webgl2";if(B=ue(q,P),B===null)throw ue(q)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(P){throw pt("WebGLRenderer: "+P.message),P}let Le,Ee,le,we,D,w,z,$,oe,ge,be,ee,re,he,Pe,ve,Se,He,De,Ye,V,pe,ie;function Re(){Le=new Nb(B),Le.init(),V=new AS(B,Le),Ee=new Rb(B,Le,e,V),le=new ES(B,Le),Ee.reversedDepthBuffer&&h&&le.buffers.depth.setReversed(!0),we=new kb(B),D=new hS,w=new wS(B,Le,le,D,Ee,V,we),z=new Fb(A),$=new Vv(B),pe=new wb(B,$),oe=new Ob(B,$,we,pe),ge=new Gb(B,oe,$,pe,we),He=new zb(B,Ee,w),Pe=new Cb(D),be=new uS(A,z,Le,Ee,pe,Pe),ee=new LS(A,D),re=new dS,he=new xS(Le),Se=new Eb(A,z,le,ge,g,l),ve=new TS(A,ge,Ee),ie=new IS(B,we,Ee,le),De=new Ab(B,Le,we),Ye=new Bb(B,Le,we),we.programs=be.programs,A.capabilities=Ee,A.extensions=Le,A.properties=D,A.renderLists=re,A.shadowMap=ve,A.state=le,A.info=we}Re(),m!==jt&&(x=new Vb(m,t.width,t.height,r,s));const xe=new DS(A,B);this.xr=xe,this.getContext=function(){return B},this.getContextAttributes=function(){return B.getContextAttributes()},this.forceContextLoss=function(){const P=Le.get("WEBGL_lose_context");P&&P.loseContext()},this.forceContextRestore=function(){const P=Le.get("WEBGL_lose_context");P&&P.restoreContext()},this.getPixelRatio=function(){return K},this.setPixelRatio=function(P){P!==void 0&&(K=P,this.setSize(J,Q,!1))},this.getSize=function(P){return P.set(J,Q)},this.setSize=function(P,q,se=!0){if(xe.isPresenting){Je("WebGLRenderer: Can't change size while VR device is presenting.");return}J=P,Q=q,t.width=Math.floor(P*K),t.height=Math.floor(q*K),se===!0&&(t.style.width=P+"px",t.style.height=q+"px"),x!==null&&x.setSize(t.width,t.height),this.setViewport(0,0,P,q)},this.getDrawingBufferSize=function(P){return P.set(J*K,Q*K).floor()},this.setDrawingBufferSize=function(P,q,se){J=P,Q=q,K=se,t.width=Math.floor(P*se),t.height=Math.floor(q*se),this.setViewport(0,0,P,q)},this.setEffects=function(P){if(m===jt){pt("THREE.WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(P){for(let q=0;q<P.length;q++)if(P[q].isOutputPass===!0){Je("THREE.WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}x.setEffects(P||[])},this.getCurrentViewport=function(P){return P.copy(j)},this.getViewport=function(P){return P.copy(Z)},this.setViewport=function(P,q,se,te){P.isVector4?Z.set(P.x,P.y,P.z,P.w):Z.set(P,q,se,te),le.viewport(j.copy(Z).multiplyScalar(K).round())},this.getScissor=function(P){return P.copy(fe)},this.setScissor=function(P,q,se,te){P.isVector4?fe.set(P.x,P.y,P.z,P.w):fe.set(P,q,se,te),le.scissor(G.copy(fe).multiplyScalar(K).round())},this.getScissorTest=function(){return Me},this.setScissorTest=function(P){le.setScissorTest(Me=P)},this.setOpaqueSort=function(P){H=P},this.setTransparentSort=function(P){Y=P},this.getClearColor=function(P){return P.copy(Se.getClearColor())},this.setClearColor=function(){Se.setClearColor(...arguments)},this.getClearAlpha=function(){return Se.getClearAlpha()},this.setClearAlpha=function(){Se.setClearAlpha(...arguments)},this.clear=function(P=!0,q=!0,se=!0){let te=0;if(P){let ne=!1;if(I!==null){const Fe=I.texture.format;ne=p.has(Fe)}if(ne){const Fe=I.texture.type,Ve=_.has(Fe),Ie=Se.getClearColor(),je=Se.getClearAlpha(),qe=Ie.r,nt=Ie.g,it=Ie.b;Ve?(v[0]=qe,v[1]=nt,v[2]=it,v[3]=je,B.clearBufferuiv(B.COLOR,0,v)):(M[0]=qe,M[1]=nt,M[2]=it,M[3]=je,B.clearBufferiv(B.COLOR,0,M))}else te|=B.COLOR_BUFFER_BIT}q&&(te|=B.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),se&&(te|=B.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),te!==0&&B.clear(te)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(P){P.setRenderer(this),R=P},this.dispose=function(){t.removeEventListener("webglcontextlost",ae,!1),t.removeEventListener("webglcontextrestored",Ue,!1),t.removeEventListener("webglcontextcreationerror",Ze,!1),Se.dispose(),re.dispose(),he.dispose(),D.dispose(),z.dispose(),ge.dispose(),pe.dispose(),ie.dispose(),be.dispose(),xe.dispose(),xe.removeEventListener("sessionstart",pi),xe.removeEventListener("sessionend",Yn),It.stop()};function ae(P){P.preventDefault(),dl("WebGLRenderer: Context Lost."),C=!0}function Ue(){dl("WebGLRenderer: Context Restored."),C=!1;const P=we.autoReset,q=ve.enabled,se=ve.autoUpdate,te=ve.needsUpdate,ne=ve.type;Re(),we.autoReset=P,ve.enabled=q,ve.autoUpdate=se,ve.needsUpdate=te,ve.type=ne}function Ze(P){pt("WebGLRenderer: A WebGL context could not be created. Reason: ",P.statusMessage)}function ot(P){const q=P.target;q.removeEventListener("dispose",ot),tt(q)}function tt(P){Ht(P),D.remove(P)}function Ht(P){const q=D.get(P).programs;q!==void 0&&(q.forEach(function(se){be.releaseProgram(se)}),P.isShaderMaterial&&be.releaseShaderCache(P))}this.renderBufferDirect=function(P,q,se,te,ne,Fe){q===null&&(q=Ge);const Ve=ne.isMesh&&ne.matrixWorld.determinant()<0,Ie=is(P,q,se,te,ne);le.setMaterial(te,Ve);let je=se.index,qe=1;if(te.wireframe===!0){if(je=oe.getWireframeAttribute(se),je===void 0)return;qe=2}const nt=se.drawRange,it=se.attributes.position;let Ke=nt.start*qe,ht=(nt.start+nt.count)*qe;Fe!==null&&(Ke=Math.max(Ke,Fe.start*qe),ht=Math.min(ht,(Fe.start+Fe.count)*qe)),je!==null?(Ke=Math.max(Ke,0),ht=Math.min(ht,je.count)):it!=null&&(Ke=Math.max(Ke,0),ht=Math.min(ht,it.count));const Pt=ht-Ke;if(Pt<0||Pt===1/0)return;pe.setup(ne,te,Ie,se,je);let Ct,_t=De;if(je!==null&&(Ct=$.get(je),_t=Ye,_t.setIndex(Ct)),ne.isMesh)te.wireframe===!0?(le.setLineWidth(te.wireframeLinewidth*ze()),_t.setMode(B.LINES)):_t.setMode(B.TRIANGLES);else if(ne.isLine){let Et=te.linewidth;Et===void 0&&(Et=1),le.setLineWidth(Et*ze()),ne.isLineSegments?_t.setMode(B.LINES):ne.isLineLoop?_t.setMode(B.LINE_LOOP):_t.setMode(B.LINE_STRIP)}else ne.isPoints?_t.setMode(B.POINTS):ne.isSprite&&_t.setMode(B.TRIANGLES);if(ne.isBatchedMesh)if(Le.get("WEBGL_multi_draw"))_t.renderMultiDraw(ne._multiDrawStarts,ne._multiDrawCounts,ne._multiDrawCount);else{const Et=ne._multiDrawStarts,We=ne._multiDrawCounts,tn=ne._multiDrawCount,at=je?$.get(je).bytesPerElement:1,_n=D.get(te).currentProgram.getUniforms();for(let vn=0;vn<tn;vn++)_n.setValue(B,"_gl_DrawID",vn),_t.render(Et[vn]/at,We[vn])}else if(ne.isInstancedMesh)_t.renderInstances(Ke,Pt,ne.count);else if(se.isInstancedBufferGeometry){const Et=se._maxInstanceCount!==void 0?se._maxInstanceCount:1/0,We=Math.min(se.instanceCount,Et);_t.renderInstances(Ke,Pt,We)}else _t.render(Ke,Pt)};function qt(P,q,se){P.transparent===!0&&P.side===En&&P.forceSinglePass===!1?(P.side=sn,P.needsUpdate=!0,Pi(P,q,se),P.side=Hi,P.needsUpdate=!0,Pi(P,q,se),P.side=En):Pi(P,q,se)}this.compile=function(P,q,se=null){se===null&&(se=P),S=he.get(se),S.init(q),b.push(S),se.traverseVisible(function(ne){ne.isLight&&ne.layers.test(q.layers)&&(S.pushLight(ne),ne.castShadow&&S.pushShadow(ne))}),P!==se&&P.traverseVisible(function(ne){ne.isLight&&ne.layers.test(q.layers)&&(S.pushLight(ne),ne.castShadow&&S.pushShadow(ne))}),S.setupLights();const te=new Set;return P.traverse(function(ne){if(!(ne.isMesh||ne.isPoints||ne.isLine||ne.isSprite))return;const Fe=ne.material;if(Fe)if(Array.isArray(Fe))for(let Ve=0;Ve<Fe.length;Ve++){const Ie=Fe[Ve];qt(Ie,se,ne),te.add(Ie)}else qt(Fe,se,ne),te.add(Fe)}),S=b.pop(),te},this.compileAsync=function(P,q,se=null){const te=this.compile(P,q,se);return new Promise(ne=>{function Fe(){if(te.forEach(function(Ve){D.get(Ve).currentProgram.isReady()&&te.delete(Ve)}),te.size===0){ne(P);return}setTimeout(Fe,10)}Le.get("KHR_parallel_shader_compile")!==null?Fe():setTimeout(Fe,10)})};let Un=null;function di(P){Un&&Un(P)}function pi(){It.stop()}function Yn(){It.start()}const It=new Km;It.setAnimationLoop(di),typeof self<"u"&&It.setContext(self),this.setAnimationLoop=function(P){Un=P,xe.setAnimationLoop(P),P===null?It.stop():It.start()},xe.addEventListener("sessionstart",pi),xe.addEventListener("sessionend",Yn),this.render=function(P,q){if(q!==void 0&&q.isCamera!==!0){pt("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(C===!0)return;R!==null&&R.renderStart(P,q);const se=xe.enabled===!0&&xe.isPresenting===!0,te=x!==null&&(I===null||se)&&x.begin(A,I);if(P.matrixWorldAutoUpdate===!0&&P.updateMatrixWorld(),q.parent===null&&q.matrixWorldAutoUpdate===!0&&q.updateMatrixWorld(),xe.enabled===!0&&xe.isPresenting===!0&&(x===null||x.isCompositing()===!1)&&(xe.cameraAutoUpdate===!0&&xe.updateCamera(q),q=xe.getCamera()),P.isScene===!0&&P.onBeforeRender(A,P,q,I),S=he.get(P,b.length),S.init(q),S.state.textureUnits=w.getTextureUnits(),b.push(S),Oe.multiplyMatrices(q.projectionMatrix,q.matrixWorldInverse),ce.setFromProjectionMatrix(Oe,Ti,q.reversedDepth),Ne=this.localClippingEnabled,de=Pe.init(this.clippingPlanes,Ne),T=re.get(P,E.length),T.init(),E.push(T),xe.enabled===!0&&xe.isPresenting===!0){const Ve=A.xr.getDepthSensingMesh();Ve!==null&&ei(Ve,q,-1/0,A.sortObjects)}ei(P,q,0,A.sortObjects),T.finish(),A.sortObjects===!0&&T.sort(H,Y),_e=xe.enabled===!1||xe.isPresenting===!1||xe.hasDepthSensing()===!1,_e&&Se.addToRenderList(T,P),this.info.render.frame++,de===!0&&Pe.beginShadows();const ne=S.state.shadowsArray;if(ve.render(ne,P,q),de===!0&&Pe.endShadows(),this.info.autoReset===!0&&this.info.reset(),(te&&x.hasRenderPass())===!1){const Ve=T.opaque,Ie=T.transmissive;if(S.setupLights(),q.isArrayCamera){const je=q.cameras;if(Ie.length>0)for(let qe=0,nt=je.length;qe<nt;qe++){const it=je[qe];es(Ve,Ie,P,it)}_e&&Se.render(P);for(let qe=0,nt=je.length;qe<nt;qe++){const it=je[qe];ta(T,P,it,it.viewport)}}else Ie.length>0&&es(Ve,Ie,P,q),_e&&Se.render(P),ta(T,P,q)}I!==null&&U===0&&(w.updateMultisampleRenderTarget(I),w.updateRenderTargetMipmap(I)),te&&x.end(A),P.isScene===!0&&P.onAfterRender(A,P,q),pe.resetDefaultState(),F=-1,O=null,b.pop(),b.length>0?(S=b[b.length-1],w.setTextureUnits(S.state.textureUnits),de===!0&&Pe.setGlobalState(A.clippingPlanes,S.state.camera)):S=null,E.pop(),E.length>0?T=E[E.length-1]:T=null,R!==null&&R.renderEnd()};function ei(P,q,se,te){if(P.visible===!1)return;if(P.layers.test(q.layers)){if(P.isGroup)se=P.renderOrder;else if(P.isLOD)P.autoUpdate===!0&&P.update(q);else if(P.isLightProbeGrid)S.pushLightProbeGrid(P);else if(P.isLight)S.pushLight(P),P.castShadow&&S.pushShadow(P);else if(P.isSprite){if(!P.frustumCulled||ce.intersectsSprite(P)){te&&Te.setFromMatrixPosition(P.matrixWorld).applyMatrix4(Oe);const Ve=ge.update(P),Ie=P.material;Ie.visible&&T.push(P,Ve,Ie,se,Te.z,null)}}else if((P.isMesh||P.isLine||P.isPoints)&&(!P.frustumCulled||ce.intersectsObject(P))){const Ve=ge.update(P),Ie=P.material;if(te&&(P.boundingSphere!==void 0?(P.boundingSphere===null&&P.computeBoundingSphere(),Te.copy(P.boundingSphere.center)):(Ve.boundingSphere===null&&Ve.computeBoundingSphere(),Te.copy(Ve.boundingSphere.center)),Te.applyMatrix4(P.matrixWorld).applyMatrix4(Oe)),Array.isArray(Ie)){const je=Ve.groups;for(let qe=0,nt=je.length;qe<nt;qe++){const it=je[qe],Ke=Ie[it.materialIndex];Ke&&Ke.visible&&T.push(P,Ve,Ke,se,Te.z,it)}}else Ie.visible&&T.push(P,Ve,Ie,se,Te.z,null)}}const Fe=P.children;for(let Ve=0,Ie=Fe.length;Ve<Ie;Ve++)ei(Fe[Ve],q,se,te)}function ta(P,q,se,te){const{opaque:ne,transmissive:Fe,transparent:Ve}=P;S.setupLightsView(se),de===!0&&Pe.setGlobalState(A.clippingPlanes,se),te&&le.viewport(j.copy(te)),ne.length>0&&ts(ne,q,se),Fe.length>0&&ts(Fe,q,se),Ve.length>0&&ts(Ve,q,se),le.buffers.depth.setTest(!0),le.buffers.depth.setMask(!0),le.buffers.color.setMask(!0),le.setPolygonOffset(!1)}function es(P,q,se,te){if((se.isScene===!0?se.overrideMaterial:null)!==null)return;if(S.state.transmissionRenderTarget[te.id]===void 0){const Ke=Le.has("EXT_color_buffer_half_float")||Le.has("EXT_color_buffer_float");S.state.transmissionRenderTarget[te.id]=new $t(1,1,{generateMipmaps:!0,type:Ke?Vi:jt,minFilter:Or,samples:Math.max(4,Ee.samples),stencilBuffer:s,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:ft.workingColorSpace})}const Fe=S.state.transmissionRenderTarget[te.id],Ve=te.viewport||j;Fe.setSize(Ve.z*A.transmissionResolutionScale,Ve.w*A.transmissionResolutionScale);const Ie=A.getRenderTarget(),je=A.getActiveCubeFace(),qe=A.getActiveMipmapLevel();A.setRenderTarget(Fe),A.getClearColor(N),k=A.getClearAlpha(),k<1&&A.setClearColor(16777215,.5),A.clear(),_e&&Se.render(se);const nt=A.toneMapping;A.toneMapping=Ai;const it=te.viewport;if(te.viewport!==void 0&&(te.viewport=void 0),S.setupLightsView(te),de===!0&&Pe.setGlobalState(A.clippingPlanes,te),ts(P,se,te),w.updateMultisampleRenderTarget(Fe),w.updateRenderTargetMipmap(Fe),Le.has("WEBGL_multisampled_render_to_texture")===!1){let Ke=!1;for(let ht=0,Pt=q.length;ht<Pt;ht++){const Ct=q[ht],{object:_t,geometry:Et,material:We,group:tn}=Ct;if(We.side===En&&_t.layers.test(te.layers)){const at=We.side;We.side=sn,We.needsUpdate=!0,na(_t,se,te,Et,We,tn),We.side=at,We.needsUpdate=!0,Ke=!0}}Ke===!0&&(w.updateMultisampleRenderTarget(Fe),w.updateRenderTargetMipmap(Fe))}A.setRenderTarget(Ie,je,qe),A.setClearColor(N,k),it!==void 0&&(te.viewport=it),A.toneMapping=nt}function ts(P,q,se){const te=q.isScene===!0?q.overrideMaterial:null;for(let ne=0,Fe=P.length;ne<Fe;ne++){const Ve=P[ne],{object:Ie,geometry:je,group:qe}=Ve;let nt=Ve.material;nt.allowOverride===!0&&te!==null&&(nt=te),Ie.layers.test(se.layers)&&na(Ie,q,se,je,nt,qe)}}function na(P,q,se,te,ne,Fe){P.onBeforeRender(A,q,se,te,ne,Fe),P.modelViewMatrix.multiplyMatrices(se.matrixWorldInverse,P.matrixWorld),P.normalMatrix.getNormalMatrix(P.modelViewMatrix),ne.onBeforeRender(A,q,se,te,P,Fe),ne.transparent===!0&&ne.side===En&&ne.forceSinglePass===!1?(ne.side=sn,ne.needsUpdate=!0,A.renderBufferDirect(se,q,te,ne,P,Fe),ne.side=Hi,ne.needsUpdate=!0,A.renderBufferDirect(se,q,te,ne,P,Fe),ne.side=En):A.renderBufferDirect(se,q,te,ne,P,Fe),P.onAfterRender(A,q,se,te,ne,Fe)}function Pi(P,q,se){q.isScene!==!0&&(q=Ge);const te=D.get(P),ne=S.state.lights,Fe=S.state.shadowsArray,Ve=ne.state.version,Ie=be.getParameters(P,ne.state,Fe,q,se,S.state.lightProbeGridArray),je=be.getProgramCacheKey(Ie);let qe=te.programs;te.environment=P.isMeshStandardMaterial||P.isMeshLambertMaterial||P.isMeshPhongMaterial?q.environment:null,te.fog=q.fog;const nt=P.isMeshStandardMaterial||P.isMeshLambertMaterial&&!P.envMap||P.isMeshPhongMaterial&&!P.envMap;te.envMap=z.get(P.envMap||te.environment,nt),te.envMapRotation=te.environment!==null&&P.envMap===null?q.environmentRotation:P.envMapRotation,qe===void 0&&(P.addEventListener("dispose",ot),qe=new Map,te.programs=qe);let it=qe.get(je);if(it!==void 0){if(te.currentProgram===it&&te.lightsStateVersion===Ve)return to(P,Ie),it}else Ie.uniforms=be.getUniforms(P),R!==null&&P.isNodeMaterial&&R.build(P,se,Ie),P.onBeforeCompile(Ie,A),it=be.acquireProgram(Ie,je),qe.set(je,it),te.uniforms=Ie.uniforms;const Ke=te.uniforms;return(!P.isShaderMaterial&&!P.isRawShaderMaterial||P.clipping===!0)&&(Ke.clippingPlanes=Pe.uniform),to(P,Ie),te.needsLights=ra(P),te.lightsStateVersion=Ve,te.needsLights&&(Ke.ambientLightColor.value=ne.state.ambient,Ke.lightProbe.value=ne.state.probe,Ke.directionalLights.value=ne.state.directional,Ke.directionalLightShadows.value=ne.state.directionalShadow,Ke.spotLights.value=ne.state.spot,Ke.spotLightShadows.value=ne.state.spotShadow,Ke.rectAreaLights.value=ne.state.rectArea,Ke.ltc_1.value=ne.state.rectAreaLTC1,Ke.ltc_2.value=ne.state.rectAreaLTC2,Ke.pointLights.value=ne.state.point,Ke.pointLightShadows.value=ne.state.pointShadow,Ke.hemisphereLights.value=ne.state.hemi,Ke.directionalShadowMatrix.value=ne.state.directionalShadowMatrix,Ke.spotLightMatrix.value=ne.state.spotLightMatrix,Ke.spotLightMap.value=ne.state.spotLightMap,Ke.pointShadowMatrix.value=ne.state.pointShadowMatrix),te.lightProbeGrid=S.state.lightProbeGridArray.length>0,te.currentProgram=it,te.uniformsList=null,it}function ns(P){if(P.uniformsList===null){const q=P.currentProgram.getUniforms();P.uniformsList=Qo.seqWithValue(q.seq,P.uniforms)}return P.uniformsList}function to(P,q){const se=D.get(P);se.outputColorSpace=q.outputColorSpace,se.batching=q.batching,se.batchingColor=q.batchingColor,se.instancing=q.instancing,se.instancingColor=q.instancingColor,se.instancingMorph=q.instancingMorph,se.skinning=q.skinning,se.morphTargets=q.morphTargets,se.morphNormals=q.morphNormals,se.morphColors=q.morphColors,se.morphTargetsCount=q.morphTargetsCount,se.numClippingPlanes=q.numClippingPlanes,se.numIntersection=q.numClipIntersection,se.vertexAlphas=q.vertexAlphas,se.vertexTangents=q.vertexTangents,se.toneMapping=q.toneMapping}function no(P,q){if(P.length===0)return null;if(P.length===1)return P[0].texture!==null?P[0]:null;y.setFromMatrixPosition(q.matrixWorld);for(let se=0,te=P.length;se<te;se++){const ne=P[se];if(ne.texture!==null&&ne.boundingBox.containsPoint(y))return ne}return null}function is(P,q,se,te,ne){q.isScene!==!0&&(q=Ge),w.resetTextureUnits();const Fe=q.fog,Ve=te.isMeshStandardMaterial||te.isMeshLambertMaterial||te.isMeshPhongMaterial?q.environment:null,Ie=I===null?A.outputColorSpace:I.isXRRenderTarget===!0?I.texture.colorSpace:ft.workingColorSpace,je=te.isMeshStandardMaterial||te.isMeshLambertMaterial&&!te.envMap||te.isMeshPhongMaterial&&!te.envMap,qe=z.get(te.envMap||Ve,je),nt=te.vertexColors===!0&&!!se.attributes.color&&se.attributes.color.itemSize===4,it=!!se.attributes.tangent&&(!!te.normalMap||te.anisotropy>0),Ke=!!se.morphAttributes.position,ht=!!se.morphAttributes.normal,Pt=!!se.morphAttributes.color;let Ct=Ai;te.toneMapped&&(I===null||I.isXRRenderTarget===!0)&&(Ct=A.toneMapping);const _t=se.morphAttributes.position||se.morphAttributes.normal||se.morphAttributes.color,Et=_t!==void 0?_t.length:0,We=D.get(te),tn=S.state.lights;if(de===!0&&(Ne===!0||P!==O)){const mt=P===O&&te.id===F;Pe.setState(te,P,mt)}let at=!1;te.version===We.__version?(We.needsLights&&We.lightsStateVersion!==tn.state.version||We.outputColorSpace!==Ie||ne.isBatchedMesh&&We.batching===!1||!ne.isBatchedMesh&&We.batching===!0||ne.isBatchedMesh&&We.batchingColor===!0&&ne.colorTexture===null||ne.isBatchedMesh&&We.batchingColor===!1&&ne.colorTexture!==null||ne.isInstancedMesh&&We.instancing===!1||!ne.isInstancedMesh&&We.instancing===!0||ne.isSkinnedMesh&&We.skinning===!1||!ne.isSkinnedMesh&&We.skinning===!0||ne.isInstancedMesh&&We.instancingColor===!0&&ne.instanceColor===null||ne.isInstancedMesh&&We.instancingColor===!1&&ne.instanceColor!==null||ne.isInstancedMesh&&We.instancingMorph===!0&&ne.morphTexture===null||ne.isInstancedMesh&&We.instancingMorph===!1&&ne.morphTexture!==null||We.envMap!==qe||te.fog===!0&&We.fog!==Fe||We.numClippingPlanes!==void 0&&(We.numClippingPlanes!==Pe.numPlanes||We.numIntersection!==Pe.numIntersection)||We.vertexAlphas!==nt||We.vertexTangents!==it||We.morphTargets!==Ke||We.morphNormals!==ht||We.morphColors!==Pt||We.toneMapping!==Ct||We.morphTargetsCount!==Et||!!We.lightProbeGrid!=S.state.lightProbeGridArray.length>0)&&(at=!0):(at=!0,We.__version=te.version);let _n=We.currentProgram;at===!0&&(_n=Pi(te,q,ne),R&&te.isNodeMaterial&&R.onUpdateProgram(te,_n,We));let vn=!1,Ln=!1,mi=!1;const xt=_n.getUniforms(),Ut=We.uniforms;if(le.useProgram(_n.program)&&(vn=!0,Ln=!0,mi=!0),te.id!==F&&(F=te.id,Ln=!0),We.needsLights){const mt=no(S.state.lightProbeGridArray,ne);We.lightProbeGrid!==mt&&(We.lightProbeGrid=mt,Ln=!0)}if(vn||O!==P){le.buffers.depth.getReversed()&&P.reversedDepth!==!0&&(P._reversedDepth=!0,P.updateProjectionMatrix()),xt.setValue(B,"projectionMatrix",P.projectionMatrix),xt.setValue(B,"viewMatrix",P.matrixWorldInverse);const ti=xt.map.cameraPosition;ti!==void 0&&ti.setValue(B,Ce.setFromMatrixPosition(P.matrixWorld)),Ee.logarithmicDepthBuffer&&xt.setValue(B,"logDepthBufFC",2/(Math.log(P.far+1)/Math.LN2)),(te.isMeshPhongMaterial||te.isMeshToonMaterial||te.isMeshLambertMaterial||te.isMeshBasicMaterial||te.isMeshStandardMaterial||te.isShaderMaterial)&&xt.setValue(B,"isOrthographic",P.isOrthographicCamera===!0),O!==P&&(O=P,Ln=!0,mi=!0)}if(We.needsLights&&(tn.state.directionalShadowMap.length>0&&xt.setValue(B,"directionalShadowMap",tn.state.directionalShadowMap,w),tn.state.spotShadowMap.length>0&&xt.setValue(B,"spotShadowMap",tn.state.spotShadowMap,w),tn.state.pointShadowMap.length>0&&xt.setValue(B,"pointShadowMap",tn.state.pointShadowMap,w)),ne.isSkinnedMesh){xt.setOptional(B,ne,"bindMatrix"),xt.setOptional(B,ne,"bindMatrixInverse");const mt=ne.skeleton;mt&&(mt.boneTexture===null&&mt.computeBoneTexture(),xt.setValue(B,"boneTexture",mt.boneTexture,w))}ne.isBatchedMesh&&(xt.setOptional(B,ne,"batchingTexture"),xt.setValue(B,"batchingTexture",ne._matricesTexture,w),xt.setOptional(B,ne,"batchingIdTexture"),xt.setValue(B,"batchingIdTexture",ne._indirectTexture,w),xt.setOptional(B,ne,"batchingColorTexture"),ne._colorsTexture!==null&&xt.setValue(B,"batchingColorTexture",ne._colorsTexture,w));const qn=se.morphAttributes;if((qn.position!==void 0||qn.normal!==void 0||qn.color!==void 0)&&He.update(ne,se,_n),(Ln||We.receiveShadow!==ne.receiveShadow)&&(We.receiveShadow=ne.receiveShadow,xt.setValue(B,"receiveShadow",ne.receiveShadow)),(te.isMeshStandardMaterial||te.isMeshLambertMaterial||te.isMeshPhongMaterial)&&te.envMap===null&&q.environment!==null&&(Ut.envMapIntensity.value=q.environmentIntensity),Ut.dfgLUT!==void 0&&(Ut.dfgLUT.value=NS()),Ln){if(xt.setValue(B,"toneMappingExposure",A.toneMappingExposure),We.needsLights&&ia(Ut,mi),Fe&&te.fog===!0&&ee.refreshFogUniforms(Ut,Fe),ee.refreshMaterialUniforms(Ut,te,K,Q,S.state.transmissionRenderTarget[P.id]),We.needsLights&&We.lightProbeGrid){const mt=We.lightProbeGrid;Ut.probesSH.value=mt.texture,Ut.probesMin.value.copy(mt.boundingBox.min),Ut.probesMax.value.copy(mt.boundingBox.max),Ut.probesResolution.value.copy(mt.resolution)}Qo.upload(B,ns(We),Ut,w)}if(te.isShaderMaterial&&te.uniformsNeedUpdate===!0&&(Qo.upload(B,ns(We),Ut,w),te.uniformsNeedUpdate=!1),te.isSpriteMaterial&&xt.setValue(B,"center",ne.center),xt.setValue(B,"modelViewMatrix",ne.modelViewMatrix),xt.setValue(B,"normalMatrix",ne.normalMatrix),xt.setValue(B,"modelMatrix",ne.matrixWorld),te.uniformsGroups!==void 0){const mt=te.uniformsGroups;for(let ti=0,ni=mt.length;ti<ni;ti++){const Di=mt[ti];ie.update(Di,_n),ie.bind(Di,_n)}}return _n}function ia(P,q){P.ambientLightColor.needsUpdate=q,P.lightProbe.needsUpdate=q,P.directionalLights.needsUpdate=q,P.directionalLightShadows.needsUpdate=q,P.pointLights.needsUpdate=q,P.pointLightShadows.needsUpdate=q,P.spotLights.needsUpdate=q,P.spotLightShadows.needsUpdate=q,P.rectAreaLights.needsUpdate=q,P.hemisphereLights.needsUpdate=q}function ra(P){return P.isMeshLambertMaterial||P.isMeshToonMaterial||P.isMeshPhongMaterial||P.isMeshStandardMaterial||P.isShadowMaterial||P.isShaderMaterial&&P.lights===!0}this.getActiveCubeFace=function(){return L},this.getActiveMipmapLevel=function(){return U},this.getRenderTarget=function(){return I},this.setRenderTargetTextures=function(P,q,se){const te=D.get(P);te.__autoAllocateDepthBuffer=P.resolveDepthBuffer===!1,te.__autoAllocateDepthBuffer===!1&&(te.__useRenderToTexture=!1),D.get(P.texture).__webglTexture=q,D.get(P.depthTexture).__webglTexture=te.__autoAllocateDepthBuffer?void 0:se,te.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(P,q){const se=D.get(P);se.__webglFramebuffer=q,se.__useDefaultFramebuffer=q===void 0};const $e=B.createFramebuffer();this.setRenderTarget=function(P,q=0,se=0){I=P,L=q,U=se;let te=null,ne=!1,Fe=!1;if(P){const Ie=D.get(P);if(Ie.__useDefaultFramebuffer!==void 0){le.bindFramebuffer(B.FRAMEBUFFER,Ie.__webglFramebuffer),j.copy(P.viewport),G.copy(P.scissor),W=P.scissorTest,le.viewport(j),le.scissor(G),le.setScissorTest(W),F=-1;return}else if(Ie.__webglFramebuffer===void 0)w.setupRenderTarget(P);else if(Ie.__hasExternalTextures)w.rebindTextures(P,D.get(P.texture).__webglTexture,D.get(P.depthTexture).__webglTexture);else if(P.depthBuffer){const nt=P.depthTexture;if(Ie.__boundDepthTexture!==nt){if(nt!==null&&D.has(nt)&&(P.width!==nt.image.width||P.height!==nt.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");w.setupDepthRenderbuffer(P)}}const je=P.texture;(je.isData3DTexture||je.isDataArrayTexture||je.isCompressedArrayTexture)&&(Fe=!0);const qe=D.get(P).__webglFramebuffer;P.isWebGLCubeRenderTarget?(Array.isArray(qe[q])?te=qe[q][se]:te=qe[q],ne=!0):P.samples>0&&w.useMultisampledRTT(P)===!1?te=D.get(P).__webglMultisampledFramebuffer:Array.isArray(qe)?te=qe[se]:te=qe,j.copy(P.viewport),G.copy(P.scissor),W=P.scissorTest}else j.copy(Z).multiplyScalar(K).floor(),G.copy(fe).multiplyScalar(K).floor(),W=Me;if(se!==0&&(te=$e),le.bindFramebuffer(B.FRAMEBUFFER,te)&&le.drawBuffers(P,te),le.viewport(j),le.scissor(G),le.setScissorTest(W),ne){const Ie=D.get(P.texture);B.framebufferTexture2D(B.FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_CUBE_MAP_POSITIVE_X+q,Ie.__webglTexture,se)}else if(Fe){const Ie=q;for(let je=0;je<P.textures.length;je++){const qe=D.get(P.textures[je]);B.framebufferTextureLayer(B.FRAMEBUFFER,B.COLOR_ATTACHMENT0+je,qe.__webglTexture,se,Ie)}}else if(P!==null&&se!==0){const Ie=D.get(P.texture);B.framebufferTexture2D(B.FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_2D,Ie.__webglTexture,se)}F=-1},this.readRenderTargetPixels=function(P,q,se,te,ne,Fe,Ve,Ie=0){if(!(P&&P.isWebGLRenderTarget)){pt("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let je=D.get(P).__webglFramebuffer;if(P.isWebGLCubeRenderTarget&&Ve!==void 0&&(je=je[Ve]),je){le.bindFramebuffer(B.FRAMEBUFFER,je);try{const qe=P.textures[Ie],nt=qe.format,it=qe.type;if(P.textures.length>1&&B.readBuffer(B.COLOR_ATTACHMENT0+Ie),!Ee.textureFormatReadable(nt)){pt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!Ee.textureTypeReadable(it)){pt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}q>=0&&q<=P.width-te&&se>=0&&se<=P.height-ne&&B.readPixels(q,se,te,ne,V.convert(nt),V.convert(it),Fe)}finally{const qe=I!==null?D.get(I).__webglFramebuffer:null;le.bindFramebuffer(B.FRAMEBUFFER,qe)}}},this.readRenderTargetPixelsAsync=async function(P,q,se,te,ne,Fe,Ve,Ie=0){if(!(P&&P.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let je=D.get(P).__webglFramebuffer;if(P.isWebGLCubeRenderTarget&&Ve!==void 0&&(je=je[Ve]),je)if(q>=0&&q<=P.width-te&&se>=0&&se<=P.height-ne){le.bindFramebuffer(B.FRAMEBUFFER,je);const qe=P.textures[Ie],nt=qe.format,it=qe.type;if(P.textures.length>1&&B.readBuffer(B.COLOR_ATTACHMENT0+Ie),!Ee.textureFormatReadable(nt))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!Ee.textureTypeReadable(it))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");const Ke=B.createBuffer();B.bindBuffer(B.PIXEL_PACK_BUFFER,Ke),B.bufferData(B.PIXEL_PACK_BUFFER,Fe.byteLength,B.STREAM_READ),B.readPixels(q,se,te,ne,V.convert(nt),V.convert(it),0);const ht=I!==null?D.get(I).__webglFramebuffer:null;le.bindFramebuffer(B.FRAMEBUFFER,ht);const Pt=B.fenceSync(B.SYNC_GPU_COMMANDS_COMPLETE,0);return B.flush(),await tv(B,Pt,4),B.bindBuffer(B.PIXEL_PACK_BUFFER,Ke),B.getBufferSubData(B.PIXEL_PACK_BUFFER,0,Fe),B.deleteBuffer(Ke),B.deleteSync(Pt),Fe}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(P,q=null,se=0){const te=Math.pow(2,-se),ne=Math.floor(P.image.width*te),Fe=Math.floor(P.image.height*te),Ve=q!==null?q.x:0,Ie=q!==null?q.y:0;w.setTexture2D(P,0),B.copyTexSubImage2D(B.TEXTURE_2D,se,0,0,Ve,Ie,ne,Fe),le.unbindTexture()};const Tr=B.createFramebuffer(),$l=B.createFramebuffer();this.copyTextureToTexture=function(P,q,se=null,te=null,ne=0,Fe=0){let Ve,Ie,je,qe,nt,it,Ke,ht,Pt;const Ct=P.isCompressedTexture?P.mipmaps[Fe]:P.image;if(se!==null)Ve=se.max.x-se.min.x,Ie=se.max.y-se.min.y,je=se.isBox3?se.max.z-se.min.z:1,qe=se.min.x,nt=se.min.y,it=se.isBox3?se.min.z:0;else{const Ut=Math.pow(2,-ne);Ve=Math.floor(Ct.width*Ut),Ie=Math.floor(Ct.height*Ut),P.isDataArrayTexture?je=Ct.depth:P.isData3DTexture?je=Math.floor(Ct.depth*Ut):je=1,qe=0,nt=0,it=0}te!==null?(Ke=te.x,ht=te.y,Pt=te.z):(Ke=0,ht=0,Pt=0);const _t=V.convert(q.format),Et=V.convert(q.type);let We;q.isData3DTexture?(w.setTexture3D(q,0),We=B.TEXTURE_3D):q.isDataArrayTexture||q.isCompressedArrayTexture?(w.setTexture2DArray(q,0),We=B.TEXTURE_2D_ARRAY):(w.setTexture2D(q,0),We=B.TEXTURE_2D),le.activeTexture(B.TEXTURE0),le.pixelStorei(B.UNPACK_FLIP_Y_WEBGL,q.flipY),le.pixelStorei(B.UNPACK_PREMULTIPLY_ALPHA_WEBGL,q.premultiplyAlpha),le.pixelStorei(B.UNPACK_ALIGNMENT,q.unpackAlignment);const tn=le.getParameter(B.UNPACK_ROW_LENGTH),at=le.getParameter(B.UNPACK_IMAGE_HEIGHT),_n=le.getParameter(B.UNPACK_SKIP_PIXELS),vn=le.getParameter(B.UNPACK_SKIP_ROWS),Ln=le.getParameter(B.UNPACK_SKIP_IMAGES);le.pixelStorei(B.UNPACK_ROW_LENGTH,Ct.width),le.pixelStorei(B.UNPACK_IMAGE_HEIGHT,Ct.height),le.pixelStorei(B.UNPACK_SKIP_PIXELS,qe),le.pixelStorei(B.UNPACK_SKIP_ROWS,nt),le.pixelStorei(B.UNPACK_SKIP_IMAGES,it);const mi=P.isDataArrayTexture||P.isData3DTexture,xt=q.isDataArrayTexture||q.isData3DTexture;if(P.isDepthTexture){const Ut=D.get(P),qn=D.get(q),mt=D.get(Ut.__renderTarget),ti=D.get(qn.__renderTarget);le.bindFramebuffer(B.READ_FRAMEBUFFER,mt.__webglFramebuffer),le.bindFramebuffer(B.DRAW_FRAMEBUFFER,ti.__webglFramebuffer);for(let ni=0;ni<je;ni++)mi&&(B.framebufferTextureLayer(B.READ_FRAMEBUFFER,B.COLOR_ATTACHMENT0,D.get(P).__webglTexture,ne,it+ni),B.framebufferTextureLayer(B.DRAW_FRAMEBUFFER,B.COLOR_ATTACHMENT0,D.get(q).__webglTexture,Fe,Pt+ni)),B.blitFramebuffer(qe,nt,Ve,Ie,Ke,ht,Ve,Ie,B.DEPTH_BUFFER_BIT,B.NEAREST);le.bindFramebuffer(B.READ_FRAMEBUFFER,null),le.bindFramebuffer(B.DRAW_FRAMEBUFFER,null)}else if(ne!==0||P.isRenderTargetTexture||D.has(P)){const Ut=D.get(P),qn=D.get(q);le.bindFramebuffer(B.READ_FRAMEBUFFER,Tr),le.bindFramebuffer(B.DRAW_FRAMEBUFFER,$l);for(let mt=0;mt<je;mt++)mi?B.framebufferTextureLayer(B.READ_FRAMEBUFFER,B.COLOR_ATTACHMENT0,Ut.__webglTexture,ne,it+mt):B.framebufferTexture2D(B.READ_FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_2D,Ut.__webglTexture,ne),xt?B.framebufferTextureLayer(B.DRAW_FRAMEBUFFER,B.COLOR_ATTACHMENT0,qn.__webglTexture,Fe,Pt+mt):B.framebufferTexture2D(B.DRAW_FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_2D,qn.__webglTexture,Fe),ne!==0?B.blitFramebuffer(qe,nt,Ve,Ie,Ke,ht,Ve,Ie,B.COLOR_BUFFER_BIT,B.NEAREST):xt?B.copyTexSubImage3D(We,Fe,Ke,ht,Pt+mt,qe,nt,Ve,Ie):B.copyTexSubImage2D(We,Fe,Ke,ht,qe,nt,Ve,Ie);le.bindFramebuffer(B.READ_FRAMEBUFFER,null),le.bindFramebuffer(B.DRAW_FRAMEBUFFER,null)}else xt?P.isDataTexture||P.isData3DTexture?B.texSubImage3D(We,Fe,Ke,ht,Pt,Ve,Ie,je,_t,Et,Ct.data):q.isCompressedArrayTexture?B.compressedTexSubImage3D(We,Fe,Ke,ht,Pt,Ve,Ie,je,_t,Ct.data):B.texSubImage3D(We,Fe,Ke,ht,Pt,Ve,Ie,je,_t,Et,Ct):P.isDataTexture?B.texSubImage2D(B.TEXTURE_2D,Fe,Ke,ht,Ve,Ie,_t,Et,Ct.data):P.isCompressedTexture?B.compressedTexSubImage2D(B.TEXTURE_2D,Fe,Ke,ht,Ct.width,Ct.height,_t,Ct.data):B.texSubImage2D(B.TEXTURE_2D,Fe,Ke,ht,Ve,Ie,_t,Et,Ct);le.pixelStorei(B.UNPACK_ROW_LENGTH,tn),le.pixelStorei(B.UNPACK_IMAGE_HEIGHT,at),le.pixelStorei(B.UNPACK_SKIP_PIXELS,_n),le.pixelStorei(B.UNPACK_SKIP_ROWS,vn),le.pixelStorei(B.UNPACK_SKIP_IMAGES,Ln),Fe===0&&q.generateMipmaps&&B.generateMipmap(We),le.unbindTexture()},this.initRenderTarget=function(P){D.get(P).__webglFramebuffer===void 0&&w.setupRenderTarget(P)},this.initTexture=function(P){P.isCubeTexture?w.setTextureCube(P,0):P.isData3DTexture?w.setTexture3D(P,0):P.isDataArrayTexture||P.isCompressedArrayTexture?w.setTexture2DArray(P,0):w.setTexture2D(P,0),le.unbindTexture()},this.resetState=function(){L=0,U=0,I=null,le.reset(),pe.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Ti}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const t=this.getContext();t.drawingBufferColorSpace=ft._getDrawingBufferColorSpace(e),t.unpackColorSpace=ft._getUnpackColorSpace()}}function BS(){var n=Object.create(null);function e(r,s){var a=r.id,o=r.name,l=r.dependencies;l===void 0&&(l=[]);var c=r.init;c===void 0&&(c=function(){});var u=r.getTransferables;if(u===void 0&&(u=null),!n[a])try{l=l.map(function(h){return h&&h.isWorkerModule&&(e(h,function(d){if(d instanceof Error)throw d}),h=n[h.id].value),h}),c=i("<"+o+">.init",c),u&&(u=i("<"+o+">.getTransferables",u));var f=null;typeof c=="function"?f=c.apply(void 0,l):console.error("worker module init function failed to rehydrate"),n[a]={id:a,value:f,getTransferables:u},s(f)}catch(h){h&&h.noLog||console.error(h),s(h)}}function t(r,s){var a,o=r.id,l=r.args;(!n[o]||typeof n[o].value!="function")&&s(new Error("Worker module "+o+": not found or its 'init' did not return a function"));try{var c=(a=n[o]).value.apply(a,l);c&&typeof c.then=="function"?c.then(u,function(f){return s(f instanceof Error?f:new Error(""+f))}):u(c)}catch(f){s(f)}function u(f){try{var h=n[o].getTransferables&&n[o].getTransferables(f);(!h||!Array.isArray(h)||!h.length)&&(h=void 0),s(f,h)}catch(d){console.error(d),s(d)}}}function i(r,s){var a=void 0;self.troikaDefine=function(l){return a=l};var o=URL.createObjectURL(new Blob(["/** "+r.replace(/\*/g,"")+` **/

troikaDefine(
`+s+`
)`],{type:"application/javascript"}));try{importScripts(o)}catch(l){console.error(l)}return URL.revokeObjectURL(o),delete self.troikaDefine,a}self.addEventListener("message",function(r){var s=r.data,a=s.messageId,o=s.action,l=s.data;try{o==="registerModule"&&e(l,function(c){c instanceof Error?postMessage({messageId:a,success:!1,error:c.message}):postMessage({messageId:a,success:!0,result:{isCallable:typeof c=="function"}})}),o==="callModule"&&t(l,function(c,u){c instanceof Error?postMessage({messageId:a,success:!1,error:c.message}):postMessage({messageId:a,success:!0,result:c},u||void 0)})}catch(c){postMessage({messageId:a,success:!1,error:c.stack})}})}function kS(n){var e=function(){for(var t=[],i=arguments.length;i--;)t[i]=arguments[i];return e._getInitResult().then(function(r){if(typeof r=="function")return r.apply(void 0,t);throw new Error("Worker module function was called but `init` did not return a callable function")})};return e._getInitResult=function(){var t=n.dependencies,i=n.init;t=Array.isArray(t)?t.map(function(s){return s&&(s=s.onMainThread||s,s._getInitResult&&(s=s._getInitResult())),s}):[];var r=Promise.all(t).then(function(s){return i.apply(null,s)});return e._getInitResult=function(){return r},r},e}var i0=function(){var n=!1;if(typeof window<"u"&&typeof window.document<"u")try{var e=new Worker(URL.createObjectURL(new Blob([""],{type:"application/javascript"})));e.terminate(),n=!0}catch(t){console.log("Troika createWorkerModule: web workers not allowed; falling back to main thread execution. Cause: ["+t.message+"]")}return i0=function(){return n},n},zS=0,GS=0,Wc=!1,Ua=Object.create(null),La=Object.create(null),bh=Object.create(null);function $s(n){if((!n||typeof n.init!="function")&&!Wc)throw new Error("requires `options.init` function");var e=n.dependencies,t=n.init,i=n.getTransferables,r=n.workerId,s=kS(n);r==null&&(r="#default");var a="workerModule"+ ++zS,o=n.name||a,l=null;e=e&&e.map(function(u){return typeof u=="function"&&!u.workerModuleData&&(Wc=!0,u=$s({workerId:r,name:"<"+o+"> function dependency: "+u.name,init:`function(){return (
`+el(u)+`
)}`}),Wc=!1),u&&u.workerModuleData&&(u=u.workerModuleData),u});function c(){for(var u=[],f=arguments.length;f--;)u[f]=arguments[f];if(!i0())return s.apply(void 0,u);if(!l){l=op(r,"registerModule",c.workerModuleData);var h=function(){l=null,La[r].delete(h)};(La[r]||(La[r]=new Set)).add(h)}return l.then(function(d){var g=d.isCallable;if(g)return op(r,"callModule",{id:a,args:u});throw new Error("Worker module function was called but `init` did not return a callable function")})}return c.workerModuleData={isWorkerModule:!0,id:a,name:o,dependencies:e,init:el(t),getTransferables:i&&el(i)},c.onMainThread=s,c}function HS(n){La[n]&&La[n].forEach(function(e){e()}),Ua[n]&&(Ua[n].terminate(),delete Ua[n])}function el(n){var e=n.toString();return!/^function/.test(e)&&/^\w+\s*\(/.test(e)&&(e="function "+e),e}function VS(n){var e=Ua[n];if(!e){var t=el(BS);e=Ua[n]=new Worker(URL.createObjectURL(new Blob(["/** Worker Module Bootstrap: "+n.replace(/\*/g,"")+` **/

;(`+t+")()"],{type:"application/javascript"}))),e.onmessage=function(i){var r=i.data,s=r.messageId,a=bh[s];if(!a)throw new Error("WorkerModule response with empty or unknown messageId");delete bh[s],a(r)}}return e}function op(n,e,t){return new Promise(function(i,r){var s=++GS;bh[s]=function(a){a.success?i(a.result):r(new Error("Error in worker "+e+" call: "+a.error))},VS(n).postMessage({messageId:s,action:e,data:t})})}function r0(){var n=(function(e){function t(G,W,N,k,J,Q,K,H){var Y=1-K;H.x=Y*Y*G+2*Y*K*N+K*K*J,H.y=Y*Y*W+2*Y*K*k+K*K*Q}function i(G,W,N,k,J,Q,K,H,Y,Z){var fe=1-Y;Z.x=fe*fe*fe*G+3*fe*fe*Y*N+3*fe*Y*Y*J+Y*Y*Y*K,Z.y=fe*fe*fe*W+3*fe*fe*Y*k+3*fe*Y*Y*Q+Y*Y*Y*H}function r(G,W){for(var N=/([MLQCZ])([^MLQCZ]*)/g,k,J,Q,K,H;k=N.exec(G);){var Y=k[2].replace(/^\s*|\s*$/g,"").split(/[,\s]+/).map(function(Z){return parseFloat(Z)});switch(k[1]){case"M":K=J=Y[0],H=Q=Y[1];break;case"L":(Y[0]!==K||Y[1]!==H)&&W("L",K,H,K=Y[0],H=Y[1]);break;case"Q":{W("Q",K,H,K=Y[2],H=Y[3],Y[0],Y[1]);break}case"C":{W("C",K,H,K=Y[4],H=Y[5],Y[0],Y[1],Y[2],Y[3]);break}case"Z":(K!==J||H!==Q)&&W("L",K,H,J,Q);break}}}function s(G,W,N){N===void 0&&(N=16);var k={x:0,y:0};r(G,function(J,Q,K,H,Y,Z,fe,Me,ce){switch(J){case"L":W(Q,K,H,Y);break;case"Q":{for(var de=Q,Ne=K,Oe=1;Oe<N;Oe++)t(Q,K,Z,fe,H,Y,Oe/(N-1),k),W(de,Ne,k.x,k.y),de=k.x,Ne=k.y;break}case"C":{for(var Ce=Q,Te=K,Ge=1;Ge<N;Ge++)i(Q,K,Z,fe,Me,ce,H,Y,Ge/(N-1),k),W(Ce,Te,k.x,k.y),Ce=k.x,Te=k.y;break}}})}var a="precision highp float;attribute vec2 aUV;varying vec2 vUV;void main(){vUV=aUV;gl_Position=vec4(mix(vec2(-1.0),vec2(1.0),aUV),0.0,1.0);}",o="precision highp float;uniform sampler2D tex;varying vec2 vUV;void main(){gl_FragColor=texture2D(tex,vUV);}",l=new WeakMap,c={premultipliedAlpha:!1,preserveDrawingBuffer:!0,antialias:!1,depth:!1};function u(G,W){var N=G.getContext?G.getContext("webgl",c):G,k=l.get(N);if(!k){let fe=function(Ce){var Te=Q[Ce];if(!Te&&(Te=Q[Ce]=N.getExtension(Ce),!Te))throw new Error(Ce+" not supported");return Te},Me=function(Ce,Te){var Ge=N.createShader(Te);return N.shaderSource(Ge,Ce),N.compileShader(Ge),Ge},ce=function(Ce,Te,Ge,_e){if(!K[Ce]){var ze={},B={},ue=N.createProgram();N.attachShader(ue,Me(Te,N.VERTEX_SHADER)),N.attachShader(ue,Me(Ge,N.FRAGMENT_SHADER)),N.linkProgram(ue),K[Ce]={program:ue,transaction:function(Ee){N.useProgram(ue),Ee({setUniform:function(we,D){for(var w=[],z=arguments.length-2;z-- >0;)w[z]=arguments[z+2];var $=B[D]||(B[D]=N.getUniformLocation(ue,D));N["uniform"+we].apply(N,[$].concat(w))},setAttribute:function(we,D,w,z,$){var oe=ze[we];oe||(oe=ze[we]={buf:N.createBuffer(),loc:N.getAttribLocation(ue,we),data:null}),N.bindBuffer(N.ARRAY_BUFFER,oe.buf),N.vertexAttribPointer(oe.loc,D,N.FLOAT,!1,0,0),N.enableVertexAttribArray(oe.loc),J?N.vertexAttribDivisor(oe.loc,z):fe("ANGLE_instanced_arrays").vertexAttribDivisorANGLE(oe.loc,z),$!==oe.data&&(N.bufferData(N.ARRAY_BUFFER,$,w),oe.data=$)}})}}}K[Ce].transaction(_e)},de=function(Ce,Te){Y++;try{N.activeTexture(N.TEXTURE0+Y);var Ge=H[Ce];Ge||(Ge=H[Ce]=N.createTexture(),N.bindTexture(N.TEXTURE_2D,Ge),N.texParameteri(N.TEXTURE_2D,N.TEXTURE_MIN_FILTER,N.NEAREST),N.texParameteri(N.TEXTURE_2D,N.TEXTURE_MAG_FILTER,N.NEAREST)),N.bindTexture(N.TEXTURE_2D,Ge),Te(Ge,Y)}finally{Y--}},Ne=function(Ce,Te,Ge){var _e=N.createFramebuffer();Z.push(_e),N.bindFramebuffer(N.FRAMEBUFFER,_e),N.activeTexture(N.TEXTURE0+Te),N.bindTexture(N.TEXTURE_2D,Ce),N.framebufferTexture2D(N.FRAMEBUFFER,N.COLOR_ATTACHMENT0,N.TEXTURE_2D,Ce,0);try{Ge(_e)}finally{N.deleteFramebuffer(_e),N.bindFramebuffer(N.FRAMEBUFFER,Z[--Z.length-1]||null)}},Oe=function(){Q={},K={},H={},Y=-1,Z.length=0};var J=typeof WebGL2RenderingContext<"u"&&N instanceof WebGL2RenderingContext,Q={},K={},H={},Y=-1,Z=[];N.canvas.addEventListener("webglcontextlost",function(Ce){Oe(),Ce.preventDefault()},!1),l.set(N,k={gl:N,isWebGL2:J,getExtension:fe,withProgram:ce,withTexture:de,withTextureFramebuffer:Ne,handleContextLoss:Oe})}W(k)}function f(G,W,N,k,J,Q,K,H){K===void 0&&(K=15),H===void 0&&(H=null),u(G,function(Y){var Z=Y.gl,fe=Y.withProgram,Me=Y.withTexture;Me("copy",function(ce,de){Z.texImage2D(Z.TEXTURE_2D,0,Z.RGBA,J,Q,0,Z.RGBA,Z.UNSIGNED_BYTE,W),fe("copy",a,o,function(Ne){var Oe=Ne.setUniform,Ce=Ne.setAttribute;Ce("aUV",2,Z.STATIC_DRAW,0,new Float32Array([0,0,2,0,0,2])),Oe("1i","image",de),Z.bindFramebuffer(Z.FRAMEBUFFER,H||null),Z.disable(Z.BLEND),Z.colorMask(K&8,K&4,K&2,K&1),Z.viewport(N,k,J,Q),Z.scissor(N,k,J,Q),Z.drawArrays(Z.TRIANGLES,0,3)})})})}function h(G,W,N){var k=G.width,J=G.height;u(G,function(Q){var K=Q.gl,H=new Uint8Array(k*J*4);K.readPixels(0,0,k,J,K.RGBA,K.UNSIGNED_BYTE,H),G.width=W,G.height=N,f(K,H,0,0,k,J)})}var d=Object.freeze({__proto__:null,withWebGLContext:u,renderImageData:f,resizeWebGLCanvasWithoutClearing:h});function g(G,W,N,k,J,Q){Q===void 0&&(Q=1);var K=new Uint8Array(G*W),H=k[2]-k[0],Y=k[3]-k[1],Z=[];s(N,function(Ce,Te,Ge,_e){Z.push({x1:Ce,y1:Te,x2:Ge,y2:_e,minX:Math.min(Ce,Ge),minY:Math.min(Te,_e),maxX:Math.max(Ce,Ge),maxY:Math.max(Te,_e)})}),Z.sort(function(Ce,Te){return Ce.maxX-Te.maxX});for(var fe=0;fe<G;fe++)for(var Me=0;Me<W;Me++){var ce=Ne(k[0]+H*(fe+.5)/G,k[1]+Y*(Me+.5)/W),de=Math.pow(1-Math.abs(ce)/J,Q)/2;ce<0&&(de=1-de),de=Math.max(0,Math.min(255,Math.round(de*255))),K[Me*G+fe]=de}return K;function Ne(Ce,Te){for(var Ge=1/0,_e=1/0,ze=Z.length;ze--;){var B=Z[ze];if(B.maxX+_e<=Ce)break;if(Ce+_e>B.minX&&Te-_e<B.maxY&&Te+_e>B.minY){var ue=_(Ce,Te,B.x1,B.y1,B.x2,B.y2);ue<Ge&&(Ge=ue,_e=Math.sqrt(Ge))}}return Oe(Ce,Te)&&(_e=-_e),_e}function Oe(Ce,Te){for(var Ge=0,_e=Z.length;_e--;){var ze=Z[_e];if(ze.maxX<=Ce)break;var B=ze.y1>Te!=ze.y2>Te&&Ce<(ze.x2-ze.x1)*(Te-ze.y1)/(ze.y2-ze.y1)+ze.x1;B&&(Ge+=ze.y1<ze.y2?1:-1)}return Ge!==0}}function m(G,W,N,k,J,Q,K,H,Y,Z){Q===void 0&&(Q=1),H===void 0&&(H=0),Y===void 0&&(Y=0),Z===void 0&&(Z=0),p(G,W,N,k,J,Q,K,null,H,Y,Z)}function p(G,W,N,k,J,Q,K,H,Y,Z,fe){Q===void 0&&(Q=1),Y===void 0&&(Y=0),Z===void 0&&(Z=0),fe===void 0&&(fe=0);for(var Me=g(G,W,N,k,J,Q),ce=new Uint8Array(Me.length*4),de=0;de<Me.length;de++)ce[de*4+fe]=Me[de];f(K,ce,Y,Z,G,W,1<<3-fe,H)}function _(G,W,N,k,J,Q){var K=J-N,H=Q-k,Y=K*K+H*H,Z=Y?Math.max(0,Math.min(1,((G-N)*K+(W-k)*H)/Y)):0,fe=G-(N+Z*K),Me=W-(k+Z*H);return fe*fe+Me*Me}var v=Object.freeze({__proto__:null,generate:g,generateIntoCanvas:m,generateIntoFramebuffer:p}),M="precision highp float;uniform vec4 uGlyphBounds;attribute vec2 aUV;attribute vec4 aLineSegment;varying vec4 vLineSegment;varying vec2 vGlyphXY;void main(){vLineSegment=aLineSegment;vGlyphXY=mix(uGlyphBounds.xy,uGlyphBounds.zw,aUV);gl_Position=vec4(mix(vec2(-1.0),vec2(1.0),aUV),0.0,1.0);}",y="precision highp float;uniform vec4 uGlyphBounds;uniform float uMaxDistance;uniform float uExponent;varying vec4 vLineSegment;varying vec2 vGlyphXY;float absDistToSegment(vec2 point,vec2 lineA,vec2 lineB){vec2 lineDir=lineB-lineA;float lenSq=dot(lineDir,lineDir);float t=lenSq==0.0 ? 0.0 : clamp(dot(point-lineA,lineDir)/lenSq,0.0,1.0);vec2 linePt=lineA+t*lineDir;return distance(point,linePt);}void main(){vec4 seg=vLineSegment;vec2 p=vGlyphXY;float dist=absDistToSegment(p,seg.xy,seg.zw);float val=pow(1.0-clamp(dist/uMaxDistance,0.0,1.0),uExponent)*0.5;bool crossing=(seg.y>p.y!=seg.w>p.y)&&(p.x<(seg.z-seg.x)*(p.y-seg.y)/(seg.w-seg.y)+seg.x);bool crossingUp=crossing&&vLineSegment.y<vLineSegment.w;gl_FragColor=vec4(crossingUp ? 1.0/255.0 : 0.0,crossing&&!crossingUp ? 1.0/255.0 : 0.0,0.0,val);}",T="precision highp float;uniform sampler2D tex;varying vec2 vUV;void main(){vec4 color=texture2D(tex,vUV);bool inside=color.r!=color.g;float val=inside ? 1.0-color.a : color.a;gl_FragColor=vec4(val);}",S=new Float32Array([0,0,2,0,0,2]),E=null,b=!1,x={},A=new WeakMap;function C(G){if(!b&&!I(G))throw new Error("WebGL generation not supported")}function R(G,W,N,k,J,Q,K){if(Q===void 0&&(Q=1),K===void 0&&(K=null),!K&&(K=E,!K)){var H=typeof OffscreenCanvas=="function"?new OffscreenCanvas(1,1):typeof document<"u"?document.createElement("canvas"):null;if(!H)throw new Error("OffscreenCanvas or DOM canvas not supported");K=E=H.getContext("webgl",{depth:!1})}C(K);var Y=new Uint8Array(G*W*4);u(K,function(ce){var de=ce.gl,Ne=ce.withTexture,Oe=ce.withTextureFramebuffer;Ne("readable",function(Ce,Te){de.texImage2D(de.TEXTURE_2D,0,de.RGBA,G,W,0,de.RGBA,de.UNSIGNED_BYTE,null),Oe(Ce,Te,function(Ge){U(G,W,N,k,J,Q,de,Ge,0,0,0),de.readPixels(0,0,G,W,de.RGBA,de.UNSIGNED_BYTE,Y)})})});for(var Z=new Uint8Array(G*W),fe=0,Me=0;fe<Y.length;fe+=4)Z[Me++]=Y[fe];return Z}function L(G,W,N,k,J,Q,K,H,Y,Z){Q===void 0&&(Q=1),H===void 0&&(H=0),Y===void 0&&(Y=0),Z===void 0&&(Z=0),U(G,W,N,k,J,Q,K,null,H,Y,Z)}function U(G,W,N,k,J,Q,K,H,Y,Z,fe){Q===void 0&&(Q=1),Y===void 0&&(Y=0),Z===void 0&&(Z=0),fe===void 0&&(fe=0),C(K);var Me=[];s(N,function(ce,de,Ne,Oe){Me.push(ce,de,Ne,Oe)}),Me=new Float32Array(Me),u(K,function(ce){var de=ce.gl,Ne=ce.isWebGL2,Oe=ce.getExtension,Ce=ce.withProgram,Te=ce.withTexture,Ge=ce.withTextureFramebuffer,_e=ce.handleContextLoss;if(Te("rawDistances",function(ze,B){(G!==ze._lastWidth||W!==ze._lastHeight)&&de.texImage2D(de.TEXTURE_2D,0,de.RGBA,ze._lastWidth=G,ze._lastHeight=W,0,de.RGBA,de.UNSIGNED_BYTE,null),Ce("main",M,y,function(ue){var Le=ue.setAttribute,Ee=ue.setUniform,le=!Ne&&Oe("ANGLE_instanced_arrays"),we=!Ne&&Oe("EXT_blend_minmax");Le("aUV",2,de.STATIC_DRAW,0,S),Le("aLineSegment",4,de.DYNAMIC_DRAW,1,Me),Ee.apply(void 0,["4f","uGlyphBounds"].concat(k)),Ee("1f","uMaxDistance",J),Ee("1f","uExponent",Q),Ge(ze,B,function(D){de.enable(de.BLEND),de.colorMask(!0,!0,!0,!0),de.viewport(0,0,G,W),de.scissor(0,0,G,W),de.blendFunc(de.ONE,de.ONE),de.blendEquationSeparate(de.FUNC_ADD,Ne?de.MAX:we.MAX_EXT),de.clear(de.COLOR_BUFFER_BIT),Ne?de.drawArraysInstanced(de.TRIANGLES,0,3,Me.length/4):le.drawArraysInstancedANGLE(de.TRIANGLES,0,3,Me.length/4)})}),Ce("post",a,T,function(ue){ue.setAttribute("aUV",2,de.STATIC_DRAW,0,S),ue.setUniform("1i","tex",B),de.bindFramebuffer(de.FRAMEBUFFER,H),de.disable(de.BLEND),de.colorMask(fe===0,fe===1,fe===2,fe===3),de.viewport(Y,Z,G,W),de.scissor(Y,Z,G,W),de.drawArrays(de.TRIANGLES,0,3)})}),de.isContextLost())throw _e(),new Error("webgl context lost")})}function I(G){var W=!G||G===E?x:G.canvas||G,N=A.get(W);if(N===void 0){b=!0;var k=null;try{var J=[97,106,97,61,99,137,118,80,80,118,137,99,61,97,106,97],Q=R(4,4,"M8,8L16,8L24,24L16,24Z",[0,0,32,32],24,1,G);N=Q&&J.length===Q.length&&Q.every(function(K,H){return K===J[H]}),N||(k="bad trial run results",console.info(J,Q))}catch(K){N=!1,k=K.message}k&&console.warn("WebGL SDF generation not supported:",k),b=!1,A.set(W,N)}return N}var F=Object.freeze({__proto__:null,generate:R,generateIntoCanvas:L,generateIntoFramebuffer:U,isSupported:I});function O(G,W,N,k,J,Q){J===void 0&&(J=Math.max(k[2]-k[0],k[3]-k[1])/2),Q===void 0&&(Q=1);try{return R.apply(F,arguments)}catch(K){return console.info("WebGL SDF generation failed, falling back to JS",K),g.apply(v,arguments)}}function j(G,W,N,k,J,Q,K,H,Y,Z){J===void 0&&(J=Math.max(k[2]-k[0],k[3]-k[1])/2),Q===void 0&&(Q=1),H===void 0&&(H=0),Y===void 0&&(Y=0),Z===void 0&&(Z=0);try{return L.apply(F,arguments)}catch(fe){return console.info("WebGL SDF generation failed, falling back to JS",fe),m.apply(v,arguments)}}return e.forEachPathCommand=r,e.generate=O,e.generateIntoCanvas=j,e.javascript=v,e.pathToLineSegments=s,e.webgl=F,e.webglUtils=d,Object.defineProperty(e,"__esModule",{value:!0}),e})({});return n}function WS(){var n=(function(e){var t={R:"13k,1a,2,3,3,2+1j,ch+16,a+1,5+2,2+n,5,a,4,6+16,4+3,h+1b,4mo,179q,2+9,2+11,2i9+7y,2+68,4,3+4,5+13,4+3,2+4k,3+29,8+cf,1t+7z,w+17,3+3m,1t+3z,16o1+5r,8+30,8+mc,29+1r,29+4v,75+73",EN:"1c+9,3d+1,6,187+9,513,4+5,7+9,sf+j,175h+9,qw+q,161f+1d,4xt+a,25i+9",ES:"17,2,6dp+1,f+1,av,16vr,mx+1,4o,2",ET:"z+2,3h+3,b+1,ym,3e+1,2o,p4+1,8,6u,7c,g6,1wc,1n9+4,30+1b,2n,6d,qhx+1,h0m,a+1,49+2,63+1,4+1,6bb+3,12jj",AN:"16o+5,2j+9,2+1,35,ed,1ff2+9,87+u",CS:"18,2+1,b,2u,12k,55v,l,17v0,2,3,53,2+1,b",B:"a,3,f+2,2v,690",S:"9,2,k",WS:"c,k,4f4,1vk+a,u,1j,335",ON:"x+1,4+4,h+5,r+5,r+3,z,5+3,2+1,2+1,5,2+2,3+4,o,w,ci+1,8+d,3+d,6+8,2+g,39+1,9,6+1,2,33,b8,3+1,3c+1,7+1,5r,b,7h+3,sa+5,2,3i+6,jg+3,ur+9,2v,ij+1,9g+9,7+a,8m,4+1,49+x,14u,2+2,c+2,e+2,e+2,e+1,i+n,e+e,2+p,u+2,e+2,36+1,2+3,2+1,b,2+2,6+5,2,2,2,h+1,5+4,6+3,3+f,16+2,5+3l,3+81,1y+p,2+40,q+a,m+13,2r+ch,2+9e,75+hf,3+v,2+2w,6e+5,f+6,75+2a,1a+p,2+2g,d+5x,r+b,6+3,4+o,g,6+1,6+2,2k+1,4,2j,5h+z,1m+1,1e+f,t+2,1f+e,d+3,4o+3,2s+1,w,535+1r,h3l+1i,93+2,2s,b+1,3l+x,2v,4g+3,21+3,kz+1,g5v+1,5a,j+9,n+v,2,3,2+8,2+1,3+2,2,3,46+1,4+4,h+5,r+5,r+a,3h+2,4+6,b+4,78,1r+24,4+c,4,1hb,ey+6,103+j,16j+c,1ux+7,5+g,fsh,jdq+1t,4,57+2e,p1,1m,1m,1m,1m,4kt+1,7j+17,5+2r,d+e,3+e,2+e,2+10,m+4,w,1n+5,1q,4z+5,4b+rb,9+c,4+c,4+37,d+2g,8+b,l+b,5+1j,9+9,7+13,9+t,3+1,27+3c,2+29,2+3q,d+d,3+4,4+2,6+6,a+o,8+6,a+2,e+6,16+42,2+1i",BN:"0+8,6+d,2s+5,2+p,e,4m9,1kt+2,2b+5,5+5,17q9+v,7k,6p+8,6+1,119d+3,440+7,96s+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+75,6p+2rz,1ben+1,1ekf+1,1ekf+1",NSM:"lc+33,7o+6,7c+18,2,2+1,2+1,2,21+a,1d+k,h,2u+6,3+5,3+1,2+3,10,v+q,2k+a,1n+8,a,p+3,2+8,2+2,2+4,18+2,3c+e,2+v,1k,2,5+7,5,4+6,b+1,u,1n,5+3,9,l+1,r,3+1,1m,5+1,5+1,3+2,4,v+1,4,c+1,1m,5+4,2+1,5,l+1,n+5,2,1n,3,2+3,9,8+1,c+1,v,1q,d,1f,4,1m+2,6+2,2+3,8+1,c+1,u,1n,g+1,l+1,t+1,1m+1,5+3,9,l+1,u,21,8+2,2,2j,3+6,d+7,2r,3+8,c+5,23+1,s,2,2,1k+d,2+4,2+1,6+a,2+z,a,2v+3,2+5,2+1,3+1,q+1,5+2,h+3,e,3+1,7,g,jk+2,qb+2,u+2,u+1,v+1,1t+1,2+6,9,3+a,a,1a+2,3c+1,z,3b+2,5+1,a,7+2,64+1,3,1n,2+6,2,2,3+7,7+9,3,1d+g,1s+3,1d,2+4,2,6,15+8,d+1,x+3,3+1,2+2,1l,2+1,4,2+2,1n+7,3+1,49+2,2+c,2+6,5,7,4+1,5j+1l,2+4,k1+w,2db+2,3y,2p+v,ff+3,30+1,n9x+3,2+9,x+1,29+1,7l,4,5,q+1,6,48+1,r+h,e,13+7,q+a,1b+2,1d,3+3,3+1,14,1w+5,3+1,3+1,d,9,1c,1g,2+2,3+1,6+1,2,17+1,9,6n,3,5,fn5,ki+f,h+f,r2,6b,46+4,1af+2,2+1,6+3,15+2,5,4m+1,fy+3,as+1,4a+a,4x,1j+e,1l+2,1e+3,3+1,1y+2,11+4,2+7,1r,d+1,1h+8,b+3,3,2o+2,3,2+1,7,4h,4+7,m+1,1m+1,4,12+6,4+4,5g+7,3+2,2,o,2d+5,2,5+1,2+1,6n+3,7+1,2+1,s+1,2e+7,3,2+1,2z,2,3+5,2,2u+2,3+3,2+4,78+8,2+1,75+1,2,5,41+3,3+1,5,x+5,3+1,15+5,3+3,9,a+5,3+2,1b+c,2+1,bb+6,2+5,2d+l,3+6,2+1,2+1,3f+5,4,2+1,2+6,2,21+1,4,2,9o+1,f0c+4,1o+6,t5,1s+3,2a,f5l+1,43t+2,i+7,3+6,v+3,45+2,1j0+1i,5+1d,9,f,n+4,2+e,11t+6,2+g,3+6,2+1,2+4,7a+6,c6+3,15t+6,32+6,gzhy+6n",AL:"16w,3,2,e+1b,z+2,2+2s,g+1,8+1,b+m,2+t,s+2i,c+e,4h+f,1d+1e,1bwe+dp,3+3z,x+c,2+1,35+3y,2rm+z,5+7,b+5,dt+l,c+u,17nl+27,1t+27,4x+6n,3+d",LRO:"6ct",RLO:"6cu",LRE:"6cq",RLE:"6cr",PDF:"6cs",LRI:"6ee",RLI:"6ef",FSI:"6eg",PDI:"6eh"},i={},r={};i.L=1,r[1]="L",Object.keys(t).forEach(function(_e,ze){i[_e]=1<<ze+1,r[i[_e]]=_e}),Object.freeze(i);var s=i.LRI|i.RLI|i.FSI,a=i.L|i.R|i.AL,o=i.B|i.S|i.WS|i.ON|i.FSI|i.LRI|i.RLI|i.PDI,l=i.BN|i.RLE|i.LRE|i.RLO|i.LRO|i.PDF,c=i.S|i.WS|i.B|s|i.PDI|l,u=null;function f(){if(!u){u=new Map;var _e=0;for(var ze in t)if(t.hasOwnProperty(ze))for(var B=t[ze],ue="",Le=void 0,Ee=!1,le=0,we=0;we<=B.length+1;we+=1){var D=B[we];if(D!==","&&we!==B.length)D==="+"?(Ee=!0,le=_e=le+parseInt(ue,36),ue=""):ue+=D;else{Ee?Le=_e+parseInt(ue,36):(le=_e=le+parseInt(ue,36),Le=_e),Ee=!1,ue="",le=Le;for(var w=_e;w<Le+1;w+=1)u.set(w,i[ze])}}}}function h(_e){return f(),u.get(_e.codePointAt(0))||i.L}function d(_e){return r[h(_e)]}var g={pairs:"14>1,1e>2,u>2,2wt>1,1>1,1ge>1,1wp>1,1j>1,f>1,hm>1,1>1,u>1,u6>1,1>1,+5,28>1,w>1,1>1,+3,b8>1,1>1,+3,1>3,-1>-1,3>1,1>1,+2,1s>1,1>1,x>1,th>1,1>1,+2,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,4q>1,1e>2,u>2,2>1,+1",canonical:"6f1>-6dx,6dy>-6dx,6ec>-6ed,6ee>-6ed,6ww>2jj,-2ji>2jj,14r4>-1e7l,1e7m>-1e7l,1e7m>-1e5c,1e5d>-1e5b,1e5c>-14qx,14qy>-14qx,14vn>-1ecg,1ech>-1ecg,1edu>-1ecg,1eci>-1ecg,1eda>-1ecg,1eci>-1ecg,1eci>-168q,168r>-168q,168s>-14ye,14yf>-14ye"};function m(_e,ze){var B=36,ue=0,Le=new Map,Ee=ze&&new Map,le;return _e.split(",").forEach(function we(D){if(D.indexOf("+")!==-1)for(var w=+D;w--;)we(le);else{le=D;var z=D.split(">"),$=z[0],oe=z[1];$=String.fromCodePoint(ue+=parseInt($,B)),oe=String.fromCodePoint(ue+=parseInt(oe,B)),Le.set($,oe),ze&&Ee.set(oe,$)}}),{map:Le,reverseMap:Ee}}var p,_,v;function M(){if(!p){var _e=m(g.pairs,!0),ze=_e.map,B=_e.reverseMap;p=ze,_=B,v=m(g.canonical,!1).map}}function y(_e){return M(),p.get(_e)||null}function T(_e){return M(),_.get(_e)||null}function S(_e){return M(),v.get(_e)||null}var E=i.L,b=i.R,x=i.EN,A=i.ES,C=i.ET,R=i.AN,L=i.CS,U=i.B,I=i.S,F=i.ON,O=i.BN,j=i.NSM,G=i.AL,W=i.LRO,N=i.RLO,k=i.LRE,J=i.RLE,Q=i.PDF,K=i.LRI,H=i.RLI,Y=i.FSI,Z=i.PDI;function fe(_e,ze){for(var B=125,ue=new Uint32Array(_e.length),Le=0;Le<_e.length;Le++)ue[Le]=h(_e[Le]);var Ee=new Map;function le(Sn,ri){var yn=ue[Sn];ue[Sn]=ri,Ee.set(yn,Ee.get(yn)-1),yn&o&&Ee.set(o,Ee.get(o)-1),Ee.set(ri,(Ee.get(ri)||0)+1),ri&o&&Ee.set(o,(Ee.get(o)||0)+1)}for(var we=new Uint8Array(_e.length),D=new Map,w=[],z=null,$=0;$<_e.length;$++)z||w.push(z={start:$,end:_e.length-1,level:ze==="rtl"?1:ze==="ltr"?0:Kf($,!1)}),ue[$]&U&&(z.end=$,z=null);for(var oe=J|k|N|W|s|Z|Q|U,ge=function(Sn){return Sn+(Sn&1?1:2)},be=function(Sn){return Sn+(Sn&1?2:1)},ee=0;ee<w.length;ee++){z=w[ee];var re=[{_level:z.level,_override:0,_isolate:0}],he=void 0,Pe=0,ve=0,Se=0;Ee.clear();for(var He=z.start;He<=z.end;He++){var De=ue[He];if(he=re[re.length-1],Ee.set(De,(Ee.get(De)||0)+1),De&o&&Ee.set(o,(Ee.get(o)||0)+1),De&oe)if(De&(J|k)){we[He]=he._level;var Ye=(De===J?be:ge)(he._level);Ye<=B&&!Pe&&!ve?re.push({_level:Ye,_override:0,_isolate:0}):Pe||ve++}else if(De&(N|W)){we[He]=he._level;var V=(De===N?be:ge)(he._level);V<=B&&!Pe&&!ve?re.push({_level:V,_override:De&N?b:E,_isolate:0}):Pe||ve++}else if(De&s){De&Y&&(De=Kf(He+1,!0)===1?H:K),we[He]=he._level,he._override&&le(He,he._override);var pe=(De===H?be:ge)(he._level);pe<=B&&Pe===0&&ve===0?(Se++,re.push({_level:pe,_override:0,_isolate:1,_isolInitIndex:He})):Pe++}else if(De&Z){if(Pe>0)Pe--;else if(Se>0){for(ve=0;!re[re.length-1]._isolate;)re.pop();var ie=re[re.length-1]._isolInitIndex;ie!=null&&(D.set(ie,He),D.set(He,ie)),re.pop(),Se--}he=re[re.length-1],we[He]=he._level,he._override&&le(He,he._override)}else De&Q?(Pe===0&&(ve>0?ve--:!he._isolate&&re.length>1&&(re.pop(),he=re[re.length-1])),we[He]=he._level):De&U&&(we[He]=z.level);else we[He]=he._level,he._override&&De!==O&&le(He,he._override)}for(var Re=[],xe=null,ae=z.start;ae<=z.end;ae++){var Ue=ue[ae];if(!(Ue&l)){var Ze=we[ae],ot=Ue&s,tt=Ue===Z;xe&&Ze===xe._level?(xe._end=ae,xe._endsWithIsolInit=ot):Re.push(xe={_start:ae,_end:ae,_level:Ze,_startsWithPDI:tt,_endsWithIsolInit:ot})}}for(var Ht=[],qt=0;qt<Re.length;qt++){var Un=Re[qt];if(!Un._startsWithPDI||Un._startsWithPDI&&!D.has(Un._start)){for(var di=[xe=Un],pi=void 0;xe&&xe._endsWithIsolInit&&(pi=D.get(xe._end))!=null;)for(var Yn=qt+1;Yn<Re.length;Yn++)if(Re[Yn]._start===pi){di.push(xe=Re[Yn]);break}for(var It=[],ei=0;ei<di.length;ei++)for(var ta=di[ei],es=ta._start;es<=ta._end;es++)It.push(es);for(var ts=we[It[0]],na=z.level,Pi=It[0]-1;Pi>=0;Pi--)if(!(ue[Pi]&l)){na=we[Pi];break}var ns=It[It.length-1],to=we[ns],no=z.level;if(!(ue[ns]&s)){for(var is=ns+1;is<=z.end;is++)if(!(ue[is]&l)){no=we[is];break}}Ht.push({_seqIndices:It,_sosType:Math.max(na,ts)%2?b:E,_eosType:Math.max(no,to)%2?b:E})}}for(var ia=0;ia<Ht.length;ia++){var ra=Ht[ia],$e=ra._seqIndices,Tr=ra._sosType,$l=ra._eosType,P=we[$e[0]]&1?b:E;if(Ee.get(j))for(var q=0;q<$e.length;q++){var se=$e[q];if(ue[se]&j){for(var te=Tr,ne=q-1;ne>=0;ne--)if(!(ue[$e[ne]]&l)){te=ue[$e[ne]];break}le(se,te&(s|Z)?F:te)}}if(Ee.get(x))for(var Fe=0;Fe<$e.length;Fe++){var Ve=$e[Fe];if(ue[Ve]&x)for(var Ie=Fe-1;Ie>=-1;Ie--){var je=Ie===-1?Tr:ue[$e[Ie]];if(je&a){je===G&&le(Ve,R);break}}}if(Ee.get(G))for(var qe=0;qe<$e.length;qe++){var nt=$e[qe];ue[nt]&G&&le(nt,b)}if(Ee.get(A)||Ee.get(L))for(var it=1;it<$e.length-1;it++){var Ke=$e[it];if(ue[Ke]&(A|L)){for(var ht=0,Pt=0,Ct=it-1;Ct>=0&&(ht=ue[$e[Ct]],!!(ht&l));Ct--);for(var _t=it+1;_t<$e.length&&(Pt=ue[$e[_t]],!!(Pt&l));_t++);ht===Pt&&(ue[Ke]===A?ht===x:ht&(x|R))&&le(Ke,ht)}}if(Ee.get(x))for(var Et=0;Et<$e.length;Et++){var We=$e[Et];if(ue[We]&x){for(var tn=Et-1;tn>=0&&ue[$e[tn]]&(C|l);tn--)le($e[tn],x);for(Et++;Et<$e.length&&ue[$e[Et]]&(C|l|x);Et++)ue[$e[Et]]!==x&&le($e[Et],x)}}if(Ee.get(C)||Ee.get(A)||Ee.get(L))for(var at=0;at<$e.length;at++){var _n=$e[at];if(ue[_n]&(C|A|L)){le(_n,F);for(var vn=at-1;vn>=0&&ue[$e[vn]]&l;vn--)le($e[vn],F);for(var Ln=at+1;Ln<$e.length&&ue[$e[Ln]]&l;Ln++)le($e[Ln],F)}}if(Ee.get(x))for(var mi=0,xt=Tr;mi<$e.length;mi++){var Ut=$e[mi],qn=ue[Ut];qn&x?xt===E&&le(Ut,E):qn&a&&(xt=qn)}if(Ee.get(o)){var mt=b|x|R,ti=mt|E,ni=[];{for(var Di=[],rs=0;rs<$e.length;rs++)if(ue[$e[rs]]&o){var sa=_e[$e[rs]],zf=void 0;if(y(sa)!==null)if(Di.length<63)Di.push({char:sa,seqIndex:rs});else break;else if((zf=T(sa))!==null)for(var aa=Di.length-1;aa>=0;aa--){var Jl=Di[aa].char;if(Jl===zf||Jl===T(S(sa))||y(S(Jl))===sa){ni.push([Di[aa].seqIndex,rs]),Di.length=aa;break}}}ni.sort(function(Sn,ri){return Sn[0]-ri[0]})}for(var Ql=0;Ql<ni.length;Ql++){for(var Gf=ni[Ql],io=Gf[0],ec=Gf[1],Hf=!1,ii=0,tc=io+1;tc<ec;tc++){var Vf=$e[tc];if(ue[Vf]&ti){Hf=!0;var Wf=ue[Vf]&mt?b:E;if(Wf===P){ii=Wf;break}}}if(Hf&&!ii){ii=Tr;for(var nc=io-1;nc>=0;nc--){var Xf=$e[nc];if(ue[Xf]&ti){var jf=ue[Xf]&mt?b:E;jf!==P?ii=jf:ii=P;break}}}if(ii){if(ue[$e[io]]=ue[$e[ec]]=ii,ii!==P){for(var oa=io+1;oa<$e.length;oa++)if(!(ue[$e[oa]]&l)){h(_e[$e[oa]])&j&&(ue[$e[oa]]=ii);break}}if(ii!==P){for(var la=ec+1;la<$e.length;la++)if(!(ue[$e[la]]&l)){h(_e[$e[la]])&j&&(ue[$e[la]]=ii);break}}}}for(var Zi=0;Zi<$e.length;Zi++)if(ue[$e[Zi]]&o){for(var Yf=Zi,ic=Zi,rc=Tr,ca=Zi-1;ca>=0;ca--)if(ue[$e[ca]]&l)Yf=ca;else{rc=ue[$e[ca]]&mt?b:E;break}for(var qf=$l,ua=Zi+1;ua<$e.length;ua++)if(ue[$e[ua]]&(o|l))ic=ua;else{qf=ue[$e[ua]]&mt?b:E;break}for(var sc=Yf;sc<=ic;sc++)ue[$e[sc]]=rc===qf?rc:P;Zi=ic}}}for(var In=z.start;In<=z.end;In++){var Vg=we[In],ro=ue[In];if(Vg&1?ro&(E|x|R)&&we[In]++:ro&b?we[In]++:ro&(R|x)&&(we[In]+=2),ro&l&&(we[In]=In===0?z.level:we[In-1]),In===z.end||h(_e[In])&(I|U))for(var so=In;so>=0&&h(_e[so])&c;so--)we[so]=z.level}}return{levels:we,paragraphs:w};function Kf(Sn,ri){for(var yn=Sn;yn<_e.length;yn++){var $i=ue[yn];if($i&(b|G))return 1;if($i&(U|E)||ri&&$i===Z)return 0;if($i&s){var Zf=Wg(yn);yn=Zf===-1?_e.length:Zf}}return 0}function Wg(Sn){for(var ri=1,yn=Sn+1;yn<_e.length;yn++){var $i=ue[yn];if($i&U)break;if($i&Z){if(--ri===0)return yn}else $i&s&&ri++}return-1}}var Me="14>1,j>2,t>2,u>2,1a>g,2v3>1,1>1,1ge>1,1wd>1,b>1,1j>1,f>1,ai>3,-2>3,+1,8>1k0,-1jq>1y7,-1y6>1hf,-1he>1h6,-1h5>1ha,-1h8>1qi,-1pu>1,6>3u,-3s>7,6>1,1>1,f>1,1>1,+2,3>1,1>1,+13,4>1,1>1,6>1eo,-1ee>1,3>1mg,-1me>1mk,-1mj>1mi,-1mg>1mi,-1md>1,1>1,+2,1>10k,-103>1,1>1,4>1,5>1,1>1,+10,3>1,1>8,-7>8,+1,-6>7,+1,a>1,1>1,u>1,u6>1,1>1,+5,26>1,1>1,2>1,2>2,8>1,7>1,4>1,1>1,+5,b8>1,1>1,+3,1>3,-2>1,2>1,1>1,+2,c>1,3>1,1>1,+2,h>1,3>1,a>1,1>1,2>1,3>1,1>1,d>1,f>1,3>1,1a>1,1>1,6>1,7>1,13>1,k>1,1>1,+19,4>1,1>1,+2,2>1,1>1,+18,m>1,a>1,1>1,lk>1,1>1,4>1,2>1,f>1,3>1,1>1,+3,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,6>1,4j>1,j>2,t>2,u>2,2>1,+1",ce;function de(){if(!ce){var _e=m(Me,!0),ze=_e.map,B=_e.reverseMap;B.forEach(function(ue,Le){ze.set(Le,ue)}),ce=ze}}function Ne(_e){return de(),ce.get(_e)||null}function Oe(_e,ze,B,ue){var Le=_e.length;B=Math.max(0,B==null?0:+B),ue=Math.min(Le-1,ue==null?Le-1:+ue);for(var Ee=new Map,le=B;le<=ue;le++)if(ze[le]&1){var we=Ne(_e[le]);we!==null&&Ee.set(le,we)}return Ee}function Ce(_e,ze,B,ue){var Le=_e.length;B=Math.max(0,B==null?0:+B),ue=Math.min(Le-1,ue==null?Le-1:+ue);var Ee=[];return ze.paragraphs.forEach(function(le){var we=Math.max(B,le.start),D=Math.min(ue,le.end);if(we<D){for(var w=ze.levels.slice(we,D+1),z=D;z>=we&&h(_e[z])&c;z--)w[z]=le.level;for(var $=le.level,oe=1/0,ge=0;ge<w.length;ge++){var be=w[ge];be>$&&($=be),be<oe&&(oe=be|1)}for(var ee=$;ee>=oe;ee--)for(var re=0;re<w.length;re++)if(w[re]>=ee){for(var he=re;re+1<w.length&&w[re+1]>=ee;)re++;re>he&&Ee.push([he+we,re+we])}}}),Ee}function Te(_e,ze,B,ue){var Le=Ge(_e,ze,B,ue),Ee=[].concat(_e);return Le.forEach(function(le,we){Ee[we]=(ze.levels[le]&1?Ne(_e[le]):null)||_e[le]}),Ee.join("")}function Ge(_e,ze,B,ue){for(var Le=Ce(_e,ze,B,ue),Ee=[],le=0;le<_e.length;le++)Ee[le]=le;return Le.forEach(function(we){for(var D=we[0],w=we[1],z=Ee.slice(D,w+1),$=z.length;$--;)Ee[w-$]=z[$]}),Ee}return e.closingToOpeningBracket=T,e.getBidiCharType=h,e.getBidiCharTypeName=d,e.getCanonicalBracket=S,e.getEmbeddingLevels=fe,e.getMirroredCharacter=Ne,e.getMirroredCharactersMap=Oe,e.getReorderSegments=Ce,e.getReorderedIndices=Ge,e.getReorderedString=Te,e.openingToClosingBracket=y,Object.defineProperty(e,"__esModule",{value:!0}),e})({});return n}const s0=/\bvoid\s+main\s*\(\s*\)\s*{/g;function Mh(n){const e=/^[ \t]*#include +<([\w\d./]+)>/gm;function t(i,r){let s=st[r];return s?Mh(s):i}return n.replace(e,t)}const ln=[];for(let n=0;n<256;n++)ln[n]=(n<16?"0":"")+n.toString(16);function XS(){const n=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,i=Math.random()*4294967295|0;return(ln[n&255]+ln[n>>8&255]+ln[n>>16&255]+ln[n>>24&255]+"-"+ln[e&255]+ln[e>>8&255]+"-"+ln[e>>16&15|64]+ln[e>>24&255]+"-"+ln[t&63|128]+ln[t>>8&255]+"-"+ln[t>>16&255]+ln[t>>24&255]+ln[i&255]+ln[i>>8&255]+ln[i>>16&255]+ln[i>>24&255]).toUpperCase()}const Pr=Object.assign||function(){let n=arguments[0];for(let e=1,t=arguments.length;e<t;e++){let i=arguments[e];if(i)for(let r in i)Object.prototype.hasOwnProperty.call(i,r)&&(n[r]=i[r])}return n},jS=Date.now(),lp=new WeakMap,cp=new Map;let YS=1e10;function Sh(n,e){const t=$S(e);let i=lp.get(n);if(i||lp.set(n,i=Object.create(null)),i[t])return new i[t];const r=`_onBeforeCompile${t}`,s=function(c,u){n.onBeforeCompile.call(this,c,u);const f=this.customProgramCacheKey()+"|"+c.vertexShader+"|"+c.fragmentShader;let h=cp[f];if(!h){const d=qS(this,c,e,t);h=cp[f]=d}c.vertexShader=h.vertexShader,c.fragmentShader=h.fragmentShader,Pr(c.uniforms,this.uniforms),e.timeUniform&&(c.uniforms[e.timeUniform]={get value(){return Date.now()-jS}}),this[r]&&this[r](c)},a=function(){return o(e.chained?n:n.clone())},o=function(c){const u=Object.create(c,l);return Object.defineProperty(u,"baseMaterial",{value:n}),Object.defineProperty(u,"id",{value:YS++}),u.uuid=XS(),u.uniforms=Pr({},c.uniforms,e.uniforms),u.defines=Pr({},c.defines,e.defines),u.defines[`TROIKA_DERIVED_MATERIAL_${t}`]="",u.extensions=Pr({},c.extensions,e.extensions),u._listeners=void 0,u},l={constructor:{value:a},isDerivedMaterial:{value:!0},type:{get:()=>n.type,set:c=>{n.type=c}},isDerivedFrom:{writable:!0,configurable:!0,value:function(c){const u=this.baseMaterial;return c===u||u.isDerivedMaterial&&u.isDerivedFrom(c)||!1}},customProgramCacheKey:{writable:!0,configurable:!0,value:function(){return n.customProgramCacheKey()+"|"+t}},onBeforeCompile:{get(){return s},set(c){this[r]=c}},copy:{writable:!0,configurable:!0,value:function(c){return n.copy.call(this,c),!n.isShaderMaterial&&!n.isDerivedMaterial&&(Pr(this.extensions,c.extensions),Pr(this.defines,c.defines),Pr(this.uniforms,Xm.clone(c.uniforms))),this}},clone:{writable:!0,configurable:!0,value:function(){const c=new n.constructor;return o(c).copy(this)}},getDepthMaterial:{writable:!0,configurable:!0,value:function(){let c=this._depthMaterial;return c||(c=this._depthMaterial=Sh(n.isDerivedMaterial?n.getDepthMaterial():new jm({depthPacking:X_}),e),c.defines.IS_DEPTH_MATERIAL="",c.uniforms=this.uniforms),c}},getDistanceMaterial:{writable:!0,configurable:!0,value:function(){let c=this._distanceMaterial;return c||(c=this._distanceMaterial=Sh(n.isDerivedMaterial?n.getDistanceMaterial():new Ym,e),c.defines.IS_DISTANCE_MATERIAL="",c.uniforms=this.uniforms),c}},dispose:{writable:!0,configurable:!0,value(){const{_depthMaterial:c,_distanceMaterial:u}=this;c&&c.dispose(),u&&u.dispose(),n.dispose.call(this)}}};return i[t]=a,new a}function qS(n,{vertexShader:e,fragmentShader:t},i,r){let{vertexDefs:s,vertexMainIntro:a,vertexMainOutro:o,vertexTransform:l,fragmentDefs:c,fragmentMainIntro:u,fragmentMainOutro:f,fragmentColorTransform:h,customRewriter:d,timeUniform:g}=i;if(s=s||"",a=a||"",o=o||"",c=c||"",u=u||"",f=f||"",(l||d)&&(e=Mh(e)),(h||d)&&(t=t.replace(/^[ \t]*#include <((?:tonemapping|encodings|colorspace|fog|premultiplied_alpha|dithering)_fragment)>/gm,`
//!BEGIN_POST_CHUNK $1
$&
//!END_POST_CHUNK
`),t=Mh(t)),d){let m=d({vertexShader:e,fragmentShader:t});e=m.vertexShader,t=m.fragmentShader}if(h){let m=[];t=t.replace(/^\/\/!BEGIN_POST_CHUNK[^]+?^\/\/!END_POST_CHUNK/gm,p=>(m.push(p),"")),f=`${h}
${m.join(`
`)}
${f}`}if(g){const m=`
uniform float ${g};
`;s=m+s,c=m+c}return l&&(e=`vec3 troika_position_${r};
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
`,e=e.replace(/\b(position|normal|uv)\b/g,(m,p,_,v)=>/\battribute\s+vec[23]\s+$/.test(v.substr(0,_))?p:`troika_${p}_${r}`),n.map&&n.map.channel>0||(e=e.replace(/\bMAP_UV\b/g,`troika_uv_${r}`))),e=up(e,r,s,a,o),t=up(t,r,c,u,f),{vertexShader:e,fragmentShader:t}}function up(n,e,t,i,r){return(i||r||t)&&(n=n.replace(s0,`
${t}
void troikaOrigMain${e}() {`),n+=`
void main() {
  ${i}
  troikaOrigMain${e}();
  ${r}
}`),n}function KS(n,e){return n==="uniforms"?void 0:typeof e=="function"?e.toString():e}let ZS=0;const hp=new Map;function $S(n){const e=JSON.stringify(n,KS);let t=hp.get(e);return t==null&&hp.set(e,t=++ZS),t}/*!
Custom build of Typr.ts (https://github.com/fredli74/Typr.ts) for use in Troika text rendering.
Original MIT license applies: https://github.com/fredli74/Typr.ts/blob/master/LICENSE
*/function JS(){return typeof window>"u"&&(self.window=self),(function(n){var e={parse:function(r){var s=e._bin,a=new Uint8Array(r);if(s.readASCII(a,0,4)=="ttcf"){var o=4;s.readUshort(a,o),o+=2,s.readUshort(a,o),o+=2;var l=s.readUint(a,o);o+=4;for(var c=[],u=0;u<l;u++){var f=s.readUint(a,o);o+=4,c.push(e._readFont(a,f))}return c}return[e._readFont(a,0)]},_readFont:function(r,s){var a=e._bin,o=s;a.readFixed(r,s),s+=4;var l=a.readUshort(r,s);s+=2,a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2;for(var c=["cmap","head","hhea","maxp","hmtx","name","OS/2","post","loca","glyf","kern","CFF ","GDEF","GPOS","GSUB","SVG "],u={_data:r,_offset:o},f={},h=0;h<l;h++){var d=a.readASCII(r,s,4);s+=4,a.readUint(r,s),s+=4;var g=a.readUint(r,s);s+=4;var m=a.readUint(r,s);s+=4,f[d]={offset:g,length:m}}for(h=0;h<c.length;h++){var p=c[h];f[p]&&(u[p.trim()]=e[p.trim()].parse(r,f[p].offset,f[p].length,u))}return u},_tabOffset:function(r,s,a){for(var o=e._bin,l=o.readUshort(r,a+4),c=a+12,u=0;u<l;u++){var f=o.readASCII(r,c,4);c+=4,o.readUint(r,c),c+=4;var h=o.readUint(r,c);if(c+=4,o.readUint(r,c),c+=4,f==s)return h}return 0}};e._bin={readFixed:function(r,s){return(r[s]<<8|r[s+1])+(r[s+2]<<8|r[s+3])/65540},readF2dot14:function(r,s){return e._bin.readShort(r,s)/16384},readInt:function(r,s){return e._bin._view(r).getInt32(s)},readInt8:function(r,s){return e._bin._view(r).getInt8(s)},readShort:function(r,s){return e._bin._view(r).getInt16(s)},readUshort:function(r,s){return e._bin._view(r).getUint16(s)},readUshorts:function(r,s,a){for(var o=[],l=0;l<a;l++)o.push(e._bin.readUshort(r,s+2*l));return o},readUint:function(r,s){return e._bin._view(r).getUint32(s)},readUint64:function(r,s){return 4294967296*e._bin.readUint(r,s)+e._bin.readUint(r,s+4)},readASCII:function(r,s,a){for(var o="",l=0;l<a;l++)o+=String.fromCharCode(r[s+l]);return o},readUnicode:function(r,s,a){for(var o="",l=0;l<a;l++){var c=r[s++]<<8|r[s++];o+=String.fromCharCode(c)}return o},_tdec:typeof window<"u"&&window.TextDecoder?new window.TextDecoder:null,readUTF8:function(r,s,a){var o=e._bin._tdec;return o&&s==0&&a==r.length?o.decode(r):e._bin.readASCII(r,s,a)},readBytes:function(r,s,a){for(var o=[],l=0;l<a;l++)o.push(r[s+l]);return o},readASCIIArray:function(r,s,a){for(var o=[],l=0;l<a;l++)o.push(String.fromCharCode(r[s+l]));return o},_view:function(r){return r._dataView||(r._dataView=r.buffer?new DataView(r.buffer,r.byteOffset,r.byteLength):new DataView(new Uint8Array(r).buffer))}},e._lctf={},e._lctf.parse=function(r,s,a,o,l){var c=e._bin,u={},f=s;c.readFixed(r,s),s+=4;var h=c.readUshort(r,s);s+=2;var d=c.readUshort(r,s);s+=2;var g=c.readUshort(r,s);return s+=2,u.scriptList=e._lctf.readScriptList(r,f+h),u.featureList=e._lctf.readFeatureList(r,f+d),u.lookupList=e._lctf.readLookupList(r,f+g,l),u},e._lctf.readLookupList=function(r,s,a){var o=e._bin,l=s,c=[],u=o.readUshort(r,s);s+=2;for(var f=0;f<u;f++){var h=o.readUshort(r,s);s+=2;var d=e._lctf.readLookupTable(r,l+h,a);c.push(d)}return c},e._lctf.readLookupTable=function(r,s,a){var o=e._bin,l=s,c={tabs:[]};c.ltype=o.readUshort(r,s),s+=2,c.flag=o.readUshort(r,s),s+=2;var u=o.readUshort(r,s);s+=2;for(var f=c.ltype,h=0;h<u;h++){var d=o.readUshort(r,s);s+=2;var g=a(r,f,l+d,c);c.tabs.push(g)}return c},e._lctf.numOfOnes=function(r){for(var s=0,a=0;a<32;a++)(r>>>a&1)!=0&&s++;return s},e._lctf.readClassDef=function(r,s){var a=e._bin,o=[],l=a.readUshort(r,s);if(s+=2,l==1){var c=a.readUshort(r,s);s+=2;var u=a.readUshort(r,s);s+=2;for(var f=0;f<u;f++)o.push(c+f),o.push(c+f),o.push(a.readUshort(r,s)),s+=2}if(l==2){var h=a.readUshort(r,s);for(s+=2,f=0;f<h;f++)o.push(a.readUshort(r,s)),s+=2,o.push(a.readUshort(r,s)),s+=2,o.push(a.readUshort(r,s)),s+=2}return o},e._lctf.getInterval=function(r,s){for(var a=0;a<r.length;a+=3){var o=r[a],l=r[a+1];if(r[a+2],o<=s&&s<=l)return a}return-1},e._lctf.readCoverage=function(r,s){var a=e._bin,o={};o.fmt=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);return s+=2,o.fmt==1&&(o.tab=a.readUshorts(r,s,l)),o.fmt==2&&(o.tab=a.readUshorts(r,s,3*l)),o},e._lctf.coverageIndex=function(r,s){var a=r.tab;if(r.fmt==1)return a.indexOf(s);if(r.fmt==2){var o=e._lctf.getInterval(a,s);if(o!=-1)return a[o+2]+(s-a[o])}return-1},e._lctf.readFeatureList=function(r,s){var a=e._bin,o=s,l=[],c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readASCII(r,s,4);s+=4;var h=a.readUshort(r,s);s+=2;var d=e._lctf.readFeatureTable(r,o+h);d.tag=f.trim(),l.push(d)}return l},e._lctf.readFeatureTable=function(r,s){var a=e._bin,o=s,l={},c=a.readUshort(r,s);s+=2,c>0&&(l.featureParams=o+c);var u=a.readUshort(r,s);s+=2,l.tab=[];for(var f=0;f<u;f++)l.tab.push(a.readUshort(r,s+2*f));return l},e._lctf.readScriptList=function(r,s){var a=e._bin,o=s,l={},c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readASCII(r,s,4);s+=4;var h=a.readUshort(r,s);s+=2,l[f.trim()]=e._lctf.readScriptTable(r,o+h)}return l},e._lctf.readScriptTable=function(r,s){var a=e._bin,o=s,l={},c=a.readUshort(r,s);s+=2,c>0&&(l.default=e._lctf.readLangSysTable(r,o+c));var u=a.readUshort(r,s);s+=2;for(var f=0;f<u;f++){var h=a.readASCII(r,s,4);s+=4;var d=a.readUshort(r,s);s+=2,l[h.trim()]=e._lctf.readLangSysTable(r,o+d)}return l},e._lctf.readLangSysTable=function(r,s){var a=e._bin,o={};a.readUshort(r,s),s+=2,o.reqFeature=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);return s+=2,o.features=a.readUshorts(r,s,l),o},e.CFF={},e.CFF.parse=function(r,s,a){var o=e._bin;(r=new Uint8Array(r.buffer,s,a))[s=0],r[++s],r[++s],r[++s],s++;var l=[];s=e.CFF.readIndex(r,s,l);for(var c=[],u=0;u<l.length-1;u++)c.push(o.readASCII(r,s+l[u],l[u+1]-l[u]));s+=l[l.length-1];var f=[];s=e.CFF.readIndex(r,s,f);var h=[];for(u=0;u<f.length-1;u++)h.push(e.CFF.readDict(r,s+f[u],s+f[u+1]));s+=f[f.length-1];var d=h[0],g=[];s=e.CFF.readIndex(r,s,g);var m=[];for(u=0;u<g.length-1;u++)m.push(o.readASCII(r,s+g[u],g[u+1]-g[u]));if(s+=g[g.length-1],e.CFF.readSubrs(r,s,d),d.CharStrings){s=d.CharStrings,g=[],s=e.CFF.readIndex(r,s,g);var p=[];for(u=0;u<g.length-1;u++)p.push(o.readBytes(r,s+g[u],g[u+1]-g[u]));d.CharStrings=p}if(d.ROS){s=d.FDArray;var _=[];for(s=e.CFF.readIndex(r,s,_),d.FDArray=[],u=0;u<_.length-1;u++){var v=e.CFF.readDict(r,s+_[u],s+_[u+1]);e.CFF._readFDict(r,v,m),d.FDArray.push(v)}s+=_[_.length-1],s=d.FDSelect,d.FDSelect=[];var M=r[s];if(s++,M!=3)throw M;var y=o.readUshort(r,s);for(s+=2,u=0;u<y+1;u++)d.FDSelect.push(o.readUshort(r,s),r[s+2]),s+=3}return d.Encoding&&(d.Encoding=e.CFF.readEncoding(r,d.Encoding,d.CharStrings.length)),d.charset&&(d.charset=e.CFF.readCharset(r,d.charset,d.CharStrings.length)),e.CFF._readFDict(r,d,m),d},e.CFF._readFDict=function(r,s,a){var o;for(var l in s.Private&&(o=s.Private[1],s.Private=e.CFF.readDict(r,o,o+s.Private[0]),s.Private.Subrs&&e.CFF.readSubrs(r,o+s.Private.Subrs,s.Private)),s)["FamilyName","FontName","FullName","Notice","version","Copyright"].indexOf(l)!=-1&&(s[l]=a[s[l]-426+35])},e.CFF.readSubrs=function(r,s,a){var o=e._bin,l=[];s=e.CFF.readIndex(r,s,l);var c,u=l.length;c=u<1240?107:u<33900?1131:32768,a.Bias=c,a.Subrs=[];for(var f=0;f<l.length-1;f++)a.Subrs.push(o.readBytes(r,s+l[f],l[f+1]-l[f]))},e.CFF.tableSE=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,0,111,112,113,114,0,115,116,117,118,119,120,121,122,0,123,0,124,125,126,127,128,129,130,131,0,132,133,0,134,135,136,137,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,138,0,139,0,0,0,0,140,141,142,143,0,0,0,0,0,144,0,0,0,145,0,0,146,147,148,149,0,0,0,0],e.CFF.glyphByUnicode=function(r,s){for(var a=0;a<r.charset.length;a++)if(r.charset[a]==s)return a;return-1},e.CFF.glyphBySE=function(r,s){return s<0||s>255?-1:e.CFF.glyphByUnicode(r,e.CFF.tableSE[s])},e.CFF.readEncoding=function(r,s,a){e._bin;var o=[".notdef"],l=r[s];if(s++,l!=0)throw"error: unknown encoding format: "+l;var c=r[s];s++;for(var u=0;u<c;u++)o.push(r[s+u]);return o},e.CFF.readCharset=function(r,s,a){var o=e._bin,l=[".notdef"],c=r[s];if(s++,c==0)for(var u=0;u<a;u++){var f=o.readUshort(r,s);s+=2,l.push(f)}else{if(c!=1&&c!=2)throw"error: format: "+c;for(;l.length<a;){f=o.readUshort(r,s),s+=2;var h=0;for(c==1?(h=r[s],s++):(h=o.readUshort(r,s),s+=2),u=0;u<=h;u++)l.push(f),f++}}return l},e.CFF.readIndex=function(r,s,a){var o=e._bin,l=o.readUshort(r,s)+1,c=r[s+=2];if(s++,c==1)for(var u=0;u<l;u++)a.push(r[s+u]);else if(c==2)for(u=0;u<l;u++)a.push(o.readUshort(r,s+2*u));else if(c==3)for(u=0;u<l;u++)a.push(16777215&o.readUint(r,s+3*u-1));else if(l!=1)throw"unsupported offset size: "+c+", count: "+l;return(s+=l*c)-1},e.CFF.getCharString=function(r,s,a){var o=e._bin,l=r[s],c=r[s+1];r[s+2],r[s+3],r[s+4];var u=1,f=null,h=null;l<=20&&(f=l,u=1),l==12&&(f=100*l+c,u=2),21<=l&&l<=27&&(f=l,u=1),l==28&&(h=o.readShort(r,s+1),u=3),29<=l&&l<=31&&(f=l,u=1),32<=l&&l<=246&&(h=l-139,u=1),247<=l&&l<=250&&(h=256*(l-247)+c+108,u=2),251<=l&&l<=254&&(h=256*-(l-251)-c-108,u=2),l==255&&(h=o.readInt(r,s+1)/65535,u=5),a.val=h??"o"+f,a.size=u},e.CFF.readCharString=function(r,s,a){for(var o=s+a,l=e._bin,c=[];s<o;){var u=r[s],f=r[s+1];r[s+2],r[s+3],r[s+4];var h=1,d=null,g=null;u<=20&&(d=u,h=1),u==12&&(d=100*u+f,h=2),u!=19&&u!=20||(d=u,h=2),21<=u&&u<=27&&(d=u,h=1),u==28&&(g=l.readShort(r,s+1),h=3),29<=u&&u<=31&&(d=u,h=1),32<=u&&u<=246&&(g=u-139,h=1),247<=u&&u<=250&&(g=256*(u-247)+f+108,h=2),251<=u&&u<=254&&(g=256*-(u-251)-f-108,h=2),u==255&&(g=l.readInt(r,s+1)/65535,h=5),c.push(g??"o"+d),s+=h}return c},e.CFF.readDict=function(r,s,a){for(var o=e._bin,l={},c=[];s<a;){var u=r[s],f=r[s+1];r[s+2],r[s+3],r[s+4];var h=1,d=null,g=null;if(u==28&&(g=o.readShort(r,s+1),h=3),u==29&&(g=o.readInt(r,s+1),h=5),32<=u&&u<=246&&(g=u-139,h=1),247<=u&&u<=250&&(g=256*(u-247)+f+108,h=2),251<=u&&u<=254&&(g=256*-(u-251)-f-108,h=2),u==255)throw g=o.readInt(r,s+1)/65535,h=5,"unknown number";if(u==30){var m=[];for(h=1;;){var p=r[s+h];h++;var _=p>>4,v=15&p;if(_!=15&&m.push(_),v!=15&&m.push(v),v==15)break}for(var M="",y=[0,1,2,3,4,5,6,7,8,9,".","e","e-","reserved","-","endOfNumber"],T=0;T<m.length;T++)M+=y[m[T]];g=parseFloat(M)}u<=21&&(d=["version","Notice","FullName","FamilyName","Weight","FontBBox","BlueValues","OtherBlues","FamilyBlues","FamilyOtherBlues","StdHW","StdVW","escape","UniqueID","XUID","charset","Encoding","CharStrings","Private","Subrs","defaultWidthX","nominalWidthX"][u],h=1,u==12&&(d=["Copyright","isFixedPitch","ItalicAngle","UnderlinePosition","UnderlineThickness","PaintType","CharstringType","FontMatrix","StrokeWidth","BlueScale","BlueShift","BlueFuzz","StemSnapH","StemSnapV","ForceBold",0,0,"LanguageGroup","ExpansionFactor","initialRandomSeed","SyntheticBase","PostScript","BaseFontName","BaseFontBlend",0,0,0,0,0,0,"ROS","CIDFontVersion","CIDFontRevision","CIDFontType","CIDCount","UIDBase","FDArray","FDSelect","FontName"][f],h=2)),d!=null?(l[d]=c.length==1?c[0]:c,c=[]):c.push(g),s+=h}return l},e.cmap={},e.cmap.parse=function(r,s,a){r=new Uint8Array(r.buffer,s,a),s=0;var o=e._bin,l={};o.readUshort(r,s),s+=2;var c=o.readUshort(r,s);s+=2;var u=[];l.tables=[];for(var f=0;f<c;f++){var h=o.readUshort(r,s);s+=2;var d=o.readUshort(r,s);s+=2;var g=o.readUint(r,s);s+=4;var m="p"+h+"e"+d,p=u.indexOf(g);if(p==-1){var _;p=l.tables.length,u.push(g);var v=o.readUshort(r,g);v==0?_=e.cmap.parse0(r,g):v==4?_=e.cmap.parse4(r,g):v==6?_=e.cmap.parse6(r,g):v==12?_=e.cmap.parse12(r,g):console.debug("unknown format: "+v,h,d,g),l.tables.push(_)}if(l[m]!=null)throw"multiple tables for one platform+encoding";l[m]=p}return l},e.cmap.parse0=function(r,s){var a=e._bin,o={};o.format=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);s+=2,a.readUshort(r,s),s+=2,o.map=[];for(var c=0;c<l-6;c++)o.map.push(r[s+c]);return o},e.cmap.parse4=function(r,s){var a=e._bin,o=s,l={};l.format=a.readUshort(r,s),s+=2;var c=a.readUshort(r,s);s+=2,a.readUshort(r,s),s+=2;var u=a.readUshort(r,s);s+=2;var f=u/2;l.searchRange=a.readUshort(r,s),s+=2,l.entrySelector=a.readUshort(r,s),s+=2,l.rangeShift=a.readUshort(r,s),s+=2,l.endCount=a.readUshorts(r,s,f),s+=2*f,s+=2,l.startCount=a.readUshorts(r,s,f),s+=2*f,l.idDelta=[];for(var h=0;h<f;h++)l.idDelta.push(a.readShort(r,s)),s+=2;for(l.idRangeOffset=a.readUshorts(r,s,f),s+=2*f,l.glyphIdArray=[];s<o+c;)l.glyphIdArray.push(a.readUshort(r,s)),s+=2;return l},e.cmap.parse6=function(r,s){var a=e._bin,o={};o.format=a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2,o.firstCode=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);s+=2,o.glyphIdArray=[];for(var c=0;c<l;c++)o.glyphIdArray.push(a.readUshort(r,s)),s+=2;return o},e.cmap.parse12=function(r,s){var a=e._bin,o={};o.format=a.readUshort(r,s),s+=2,s+=2,a.readUint(r,s),s+=4,a.readUint(r,s),s+=4;var l=a.readUint(r,s);s+=4,o.groups=[];for(var c=0;c<l;c++){var u=s+12*c,f=a.readUint(r,u+0),h=a.readUint(r,u+4),d=a.readUint(r,u+8);o.groups.push([f,h,d])}return o},e.glyf={},e.glyf.parse=function(r,s,a,o){for(var l=[],c=0;c<o.maxp.numGlyphs;c++)l.push(null);return l},e.glyf._parseGlyf=function(r,s){var a=e._bin,o=r._data,l=e._tabOffset(o,"glyf",r._offset)+r.loca[s];if(r.loca[s]==r.loca[s+1])return null;var c={};if(c.noc=a.readShort(o,l),l+=2,c.xMin=a.readShort(o,l),l+=2,c.yMin=a.readShort(o,l),l+=2,c.xMax=a.readShort(o,l),l+=2,c.yMax=a.readShort(o,l),l+=2,c.xMin>=c.xMax||c.yMin>=c.yMax)return null;if(c.noc>0){c.endPts=[];for(var u=0;u<c.noc;u++)c.endPts.push(a.readUshort(o,l)),l+=2;var f=a.readUshort(o,l);if(l+=2,o.length-l<f)return null;c.instructions=a.readBytes(o,l,f),l+=f;var h=c.endPts[c.noc-1]+1;for(c.flags=[],u=0;u<h;u++){var d=o[l];if(l++,c.flags.push(d),(8&d)!=0){var g=o[l];l++;for(var m=0;m<g;m++)c.flags.push(d),u++}}for(c.xs=[],u=0;u<h;u++){var p=(2&c.flags[u])!=0,_=(16&c.flags[u])!=0;p?(c.xs.push(_?o[l]:-o[l]),l++):_?c.xs.push(0):(c.xs.push(a.readShort(o,l)),l+=2)}for(c.ys=[],u=0;u<h;u++)p=(4&c.flags[u])!=0,_=(32&c.flags[u])!=0,p?(c.ys.push(_?o[l]:-o[l]),l++):_?c.ys.push(0):(c.ys.push(a.readShort(o,l)),l+=2);var v=0,M=0;for(u=0;u<h;u++)v+=c.xs[u],M+=c.ys[u],c.xs[u]=v,c.ys[u]=M}else{var y;c.parts=[];do{y=a.readUshort(o,l),l+=2;var T={m:{a:1,b:0,c:0,d:1,tx:0,ty:0},p1:-1,p2:-1};if(c.parts.push(T),T.glyphIndex=a.readUshort(o,l),l+=2,1&y){var S=a.readShort(o,l);l+=2;var E=a.readShort(o,l);l+=2}else S=a.readInt8(o,l),l++,E=a.readInt8(o,l),l++;2&y?(T.m.tx=S,T.m.ty=E):(T.p1=S,T.p2=E),8&y?(T.m.a=T.m.d=a.readF2dot14(o,l),l+=2):64&y?(T.m.a=a.readF2dot14(o,l),l+=2,T.m.d=a.readF2dot14(o,l),l+=2):128&y&&(T.m.a=a.readF2dot14(o,l),l+=2,T.m.b=a.readF2dot14(o,l),l+=2,T.m.c=a.readF2dot14(o,l),l+=2,T.m.d=a.readF2dot14(o,l),l+=2)}while(32&y);if(256&y){var b=a.readUshort(o,l);for(l+=2,c.instr=[],u=0;u<b;u++)c.instr.push(o[l]),l++}}return c},e.GDEF={},e.GDEF.parse=function(r,s,a,o){var l=s;s+=4;var c=e._bin.readUshort(r,s);return{glyphClassDef:c===0?null:e._lctf.readClassDef(r,l+c)}},e.GPOS={},e.GPOS.parse=function(r,s,a,o){return e._lctf.parse(r,s,a,o,e.GPOS.subt)},e.GPOS.subt=function(r,s,a,o){var l=e._bin,c=a,u={};if(u.fmt=l.readUshort(r,a),a+=2,s==1||s==2||s==3||s==7||s==8&&u.fmt<=2){var f=l.readUshort(r,a);a+=2,u.coverage=e._lctf.readCoverage(r,f+c)}if(s==1&&u.fmt==1){var h=l.readUshort(r,a);a+=2,h!=0&&(u.pos=e.GPOS.readValueRecord(r,a,h))}else if(s==2&&u.fmt>=1&&u.fmt<=2){h=l.readUshort(r,a),a+=2;var d=l.readUshort(r,a);a+=2;var g=e._lctf.numOfOnes(h),m=e._lctf.numOfOnes(d);if(u.fmt==1){u.pairsets=[];var p=l.readUshort(r,a);a+=2;for(var _=0;_<p;_++){var v=c+l.readUshort(r,a);a+=2;var M=l.readUshort(r,v);v+=2;for(var y=[],T=0;T<M;T++){var S=l.readUshort(r,v);v+=2,h!=0&&(R=e.GPOS.readValueRecord(r,v,h),v+=2*g),d!=0&&(L=e.GPOS.readValueRecord(r,v,d),v+=2*m),y.push({gid2:S,val1:R,val2:L})}u.pairsets.push(y)}}if(u.fmt==2){var E=l.readUshort(r,a);a+=2;var b=l.readUshort(r,a);a+=2;var x=l.readUshort(r,a);a+=2;var A=l.readUshort(r,a);for(a+=2,u.classDef1=e._lctf.readClassDef(r,c+E),u.classDef2=e._lctf.readClassDef(r,c+b),u.matrix=[],_=0;_<x;_++){var C=[];for(T=0;T<A;T++){var R=null,L=null;h!=0&&(R=e.GPOS.readValueRecord(r,a,h),a+=2*g),d!=0&&(L=e.GPOS.readValueRecord(r,a,d),a+=2*m),C.push({val1:R,val2:L})}u.matrix.push(C)}}}else if(s==4&&u.fmt==1)u.markCoverage=e._lctf.readCoverage(r,l.readUshort(r,a)+c),u.baseCoverage=e._lctf.readCoverage(r,l.readUshort(r,a+2)+c),u.markClassCount=l.readUshort(r,a+4),u.markArray=e.GPOS.readMarkArray(r,l.readUshort(r,a+6)+c),u.baseArray=e.GPOS.readBaseArray(r,l.readUshort(r,a+8)+c,u.markClassCount);else if(s==6&&u.fmt==1)u.mark1Coverage=e._lctf.readCoverage(r,l.readUshort(r,a)+c),u.mark2Coverage=e._lctf.readCoverage(r,l.readUshort(r,a+2)+c),u.markClassCount=l.readUshort(r,a+4),u.mark1Array=e.GPOS.readMarkArray(r,l.readUshort(r,a+6)+c),u.mark2Array=e.GPOS.readBaseArray(r,l.readUshort(r,a+8)+c,u.markClassCount);else{if(s==9&&u.fmt==1){var U=l.readUshort(r,a);a+=2;var I=l.readUint(r,a);if(a+=4,o.ltype==9)o.ltype=U;else if(o.ltype!=U)throw"invalid extension substitution";return e.GPOS.subt(r,o.ltype,c+I)}console.debug("unsupported GPOS table LookupType",s,"format",u.fmt)}return u},e.GPOS.readValueRecord=function(r,s,a){var o=e._bin,l=[];return l.push(1&a?o.readShort(r,s):0),s+=1&a?2:0,l.push(2&a?o.readShort(r,s):0),s+=2&a?2:0,l.push(4&a?o.readShort(r,s):0),s+=4&a?2:0,l.push(8&a?o.readShort(r,s):0),s+=8&a?2:0,l},e.GPOS.readBaseArray=function(r,s,a){var o=e._bin,l=[],c=s,u=o.readUshort(r,s);s+=2;for(var f=0;f<u;f++){for(var h=[],d=0;d<a;d++)h.push(e.GPOS.readAnchorRecord(r,c+o.readUshort(r,s))),s+=2;l.push(h)}return l},e.GPOS.readMarkArray=function(r,s){var a=e._bin,o=[],l=s,c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=e.GPOS.readAnchorRecord(r,a.readUshort(r,s+2)+l);f.markClass=a.readUshort(r,s),o.push(f),s+=4}return o},e.GPOS.readAnchorRecord=function(r,s){var a=e._bin,o={};return o.fmt=a.readUshort(r,s),o.x=a.readShort(r,s+2),o.y=a.readShort(r,s+4),o},e.GSUB={},e.GSUB.parse=function(r,s,a,o){return e._lctf.parse(r,s,a,o,e.GSUB.subt)},e.GSUB.subt=function(r,s,a,o){var l=e._bin,c=a,u={};if(u.fmt=l.readUshort(r,a),a+=2,s!=1&&s!=2&&s!=4&&s!=5&&s!=6)return null;if(s==1||s==2||s==4||s==5&&u.fmt<=2||s==6&&u.fmt<=2){var f=l.readUshort(r,a);a+=2,u.coverage=e._lctf.readCoverage(r,c+f)}if(s==1&&u.fmt>=1&&u.fmt<=2){if(u.fmt==1)u.delta=l.readShort(r,a),a+=2;else if(u.fmt==2){var h=l.readUshort(r,a);a+=2,u.newg=l.readUshorts(r,a,h),a+=2*u.newg.length}}else if(s==2&&u.fmt==1){h=l.readUshort(r,a),a+=2,u.seqs=[];for(var d=0;d<h;d++){var g=l.readUshort(r,a)+c;a+=2;var m=l.readUshort(r,g);u.seqs.push(l.readUshorts(r,g+2,m))}}else if(s==4)for(u.vals=[],h=l.readUshort(r,a),a+=2,d=0;d<h;d++){var p=l.readUshort(r,a);a+=2,u.vals.push(e.GSUB.readLigatureSet(r,c+p))}else if(s==5&&u.fmt==2){if(u.fmt==2){var _=l.readUshort(r,a);a+=2,u.cDef=e._lctf.readClassDef(r,c+_),u.scset=[];var v=l.readUshort(r,a);for(a+=2,d=0;d<v;d++){var M=l.readUshort(r,a);a+=2,u.scset.push(M==0?null:e.GSUB.readSubClassSet(r,c+M))}}}else if(s==6&&u.fmt==3){if(u.fmt==3){for(d=0;d<3;d++){h=l.readUshort(r,a),a+=2;for(var y=[],T=0;T<h;T++)y.push(e._lctf.readCoverage(r,c+l.readUshort(r,a+2*T)));a+=2*h,d==0&&(u.backCvg=y),d==1&&(u.inptCvg=y),d==2&&(u.ahedCvg=y)}h=l.readUshort(r,a),a+=2,u.lookupRec=e.GSUB.readSubstLookupRecords(r,a,h)}}else{if(s==7&&u.fmt==1){var S=l.readUshort(r,a);a+=2;var E=l.readUint(r,a);if(a+=4,o.ltype==9)o.ltype=S;else if(o.ltype!=S)throw"invalid extension substitution";return e.GSUB.subt(r,o.ltype,c+E)}console.debug("unsupported GSUB table LookupType",s,"format",u.fmt)}return u},e.GSUB.readSubClassSet=function(r,s){var a=e._bin.readUshort,o=s,l=[],c=a(r,s);s+=2;for(var u=0;u<c;u++){var f=a(r,s);s+=2,l.push(e.GSUB.readSubClassRule(r,o+f))}return l},e.GSUB.readSubClassRule=function(r,s){var a=e._bin.readUshort,o={},l=a(r,s),c=a(r,s+=2);s+=2,o.input=[];for(var u=0;u<l-1;u++)o.input.push(a(r,s)),s+=2;return o.substLookupRecords=e.GSUB.readSubstLookupRecords(r,s,c),o},e.GSUB.readSubstLookupRecords=function(r,s,a){for(var o=e._bin.readUshort,l=[],c=0;c<a;c++)l.push(o(r,s),o(r,s+2)),s+=4;return l},e.GSUB.readChainSubClassSet=function(r,s){var a=e._bin,o=s,l=[],c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readUshort(r,s);s+=2,l.push(e.GSUB.readChainSubClassRule(r,o+f))}return l},e.GSUB.readChainSubClassRule=function(r,s){for(var a=e._bin,o={},l=["backtrack","input","lookahead"],c=0;c<l.length;c++){var u=a.readUshort(r,s);s+=2,c==1&&u--,o[l[c]]=a.readUshorts(r,s,u),s+=2*o[l[c]].length}return u=a.readUshort(r,s),s+=2,o.subst=a.readUshorts(r,s,2*u),s+=2*o.subst.length,o},e.GSUB.readLigatureSet=function(r,s){var a=e._bin,o=s,l=[],c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readUshort(r,s);s+=2,l.push(e.GSUB.readLigature(r,o+f))}return l},e.GSUB.readLigature=function(r,s){var a=e._bin,o={chain:[]};o.nglyph=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);s+=2;for(var c=0;c<l-1;c++)o.chain.push(a.readUshort(r,s)),s+=2;return o},e.head={},e.head.parse=function(r,s,a){var o=e._bin,l={};return o.readFixed(r,s),s+=4,l.fontRevision=o.readFixed(r,s),s+=4,o.readUint(r,s),s+=4,o.readUint(r,s),s+=4,l.flags=o.readUshort(r,s),s+=2,l.unitsPerEm=o.readUshort(r,s),s+=2,l.created=o.readUint64(r,s),s+=8,l.modified=o.readUint64(r,s),s+=8,l.xMin=o.readShort(r,s),s+=2,l.yMin=o.readShort(r,s),s+=2,l.xMax=o.readShort(r,s),s+=2,l.yMax=o.readShort(r,s),s+=2,l.macStyle=o.readUshort(r,s),s+=2,l.lowestRecPPEM=o.readUshort(r,s),s+=2,l.fontDirectionHint=o.readShort(r,s),s+=2,l.indexToLocFormat=o.readShort(r,s),s+=2,l.glyphDataFormat=o.readShort(r,s),s+=2,l},e.hhea={},e.hhea.parse=function(r,s,a){var o=e._bin,l={};return o.readFixed(r,s),s+=4,l.ascender=o.readShort(r,s),s+=2,l.descender=o.readShort(r,s),s+=2,l.lineGap=o.readShort(r,s),s+=2,l.advanceWidthMax=o.readUshort(r,s),s+=2,l.minLeftSideBearing=o.readShort(r,s),s+=2,l.minRightSideBearing=o.readShort(r,s),s+=2,l.xMaxExtent=o.readShort(r,s),s+=2,l.caretSlopeRise=o.readShort(r,s),s+=2,l.caretSlopeRun=o.readShort(r,s),s+=2,l.caretOffset=o.readShort(r,s),s+=2,s+=8,l.metricDataFormat=o.readShort(r,s),s+=2,l.numberOfHMetrics=o.readUshort(r,s),s+=2,l},e.hmtx={},e.hmtx.parse=function(r,s,a,o){for(var l=e._bin,c={aWidth:[],lsBearing:[]},u=0,f=0,h=0;h<o.maxp.numGlyphs;h++)h<o.hhea.numberOfHMetrics&&(u=l.readUshort(r,s),s+=2,f=l.readShort(r,s),s+=2),c.aWidth.push(u),c.lsBearing.push(f);return c},e.kern={},e.kern.parse=function(r,s,a,o){var l=e._bin,c=l.readUshort(r,s);if(s+=2,c==1)return e.kern.parseV1(r,s-2,a,o);var u=l.readUshort(r,s);s+=2;for(var f={glyph1:[],rval:[]},h=0;h<u;h++){s+=2,a=l.readUshort(r,s),s+=2;var d=l.readUshort(r,s);s+=2;var g=d>>>8;if((g&=15)!=0)throw"unknown kern table format: "+g;s=e.kern.readFormat0(r,s,f)}return f},e.kern.parseV1=function(r,s,a,o){var l=e._bin;l.readFixed(r,s),s+=4;var c=l.readUint(r,s);s+=4;for(var u={glyph1:[],rval:[]},f=0;f<c;f++){l.readUint(r,s),s+=4;var h=l.readUshort(r,s);s+=2,l.readUshort(r,s),s+=2;var d=h>>>8;if((d&=15)!=0)throw"unknown kern table format: "+d;s=e.kern.readFormat0(r,s,u)}return u},e.kern.readFormat0=function(r,s,a){var o=e._bin,l=-1,c=o.readUshort(r,s);s+=2,o.readUshort(r,s),s+=2,o.readUshort(r,s),s+=2,o.readUshort(r,s),s+=2;for(var u=0;u<c;u++){var f=o.readUshort(r,s);s+=2;var h=o.readUshort(r,s);s+=2;var d=o.readShort(r,s);s+=2,f!=l&&(a.glyph1.push(f),a.rval.push({glyph2:[],vals:[]}));var g=a.rval[a.rval.length-1];g.glyph2.push(h),g.vals.push(d),l=f}return s},e.loca={},e.loca.parse=function(r,s,a,o){var l=e._bin,c=[],u=o.head.indexToLocFormat,f=o.maxp.numGlyphs+1;if(u==0)for(var h=0;h<f;h++)c.push(l.readUshort(r,s+(h<<1))<<1);if(u==1)for(h=0;h<f;h++)c.push(l.readUint(r,s+(h<<2)));return c},e.maxp={},e.maxp.parse=function(r,s,a){var o=e._bin,l={},c=o.readUint(r,s);return s+=4,l.numGlyphs=o.readUshort(r,s),s+=2,c==65536&&(l.maxPoints=o.readUshort(r,s),s+=2,l.maxContours=o.readUshort(r,s),s+=2,l.maxCompositePoints=o.readUshort(r,s),s+=2,l.maxCompositeContours=o.readUshort(r,s),s+=2,l.maxZones=o.readUshort(r,s),s+=2,l.maxTwilightPoints=o.readUshort(r,s),s+=2,l.maxStorage=o.readUshort(r,s),s+=2,l.maxFunctionDefs=o.readUshort(r,s),s+=2,l.maxInstructionDefs=o.readUshort(r,s),s+=2,l.maxStackElements=o.readUshort(r,s),s+=2,l.maxSizeOfInstructions=o.readUshort(r,s),s+=2,l.maxComponentElements=o.readUshort(r,s),s+=2,l.maxComponentDepth=o.readUshort(r,s),s+=2),l},e.name={},e.name.parse=function(r,s,a){var o=e._bin,l={};o.readUshort(r,s),s+=2;var c=o.readUshort(r,s);s+=2,o.readUshort(r,s);for(var u,f=["copyright","fontFamily","fontSubfamily","ID","fullName","version","postScriptName","trademark","manufacturer","designer","description","urlVendor","urlDesigner","licence","licenceURL","---","typoFamilyName","typoSubfamilyName","compatibleFull","sampleText","postScriptCID","wwsFamilyName","wwsSubfamilyName","lightPalette","darkPalette"],h=s+=2,d=0;d<c;d++){var g=o.readUshort(r,s);s+=2;var m=o.readUshort(r,s);s+=2;var p=o.readUshort(r,s);s+=2;var _=o.readUshort(r,s);s+=2;var v=o.readUshort(r,s);s+=2;var M=o.readUshort(r,s);s+=2;var y,T=f[_],S=h+12*c+M;if(g==0)y=o.readUnicode(r,S,v/2);else if(g==3&&m==0)y=o.readUnicode(r,S,v/2);else if(m==0)y=o.readASCII(r,S,v);else if(m==1)y=o.readUnicode(r,S,v/2);else if(m==3)y=o.readUnicode(r,S,v/2);else{if(g!=1)throw"unknown encoding "+m+", platformID: "+g;y=o.readASCII(r,S,v),console.debug("reading unknown MAC encoding "+m+" as ASCII")}var E="p"+g+","+p.toString(16);l[E]==null&&(l[E]={}),l[E][T!==void 0?T:_]=y,l[E]._lang=p}for(var b in l)if(l[b].postScriptName!=null&&l[b]._lang==1033)return l[b];for(var b in l)if(l[b].postScriptName!=null&&l[b]._lang==0)return l[b];for(var b in l)if(l[b].postScriptName!=null&&l[b]._lang==3084)return l[b];for(var b in l)if(l[b].postScriptName!=null)return l[b];for(var b in l){u=b;break}return console.debug("returning name table with languageID "+l[u]._lang),l[u]},e["OS/2"]={},e["OS/2"].parse=function(r,s,a){var o=e._bin.readUshort(r,s);s+=2;var l={};if(o==0)e["OS/2"].version0(r,s,l);else if(o==1)e["OS/2"].version1(r,s,l);else if(o==2||o==3||o==4)e["OS/2"].version2(r,s,l);else{if(o!=5)throw"unknown OS/2 table version: "+o;e["OS/2"].version5(r,s,l)}return l},e["OS/2"].version0=function(r,s,a){var o=e._bin;return a.xAvgCharWidth=o.readShort(r,s),s+=2,a.usWeightClass=o.readUshort(r,s),s+=2,a.usWidthClass=o.readUshort(r,s),s+=2,a.fsType=o.readUshort(r,s),s+=2,a.ySubscriptXSize=o.readShort(r,s),s+=2,a.ySubscriptYSize=o.readShort(r,s),s+=2,a.ySubscriptXOffset=o.readShort(r,s),s+=2,a.ySubscriptYOffset=o.readShort(r,s),s+=2,a.ySuperscriptXSize=o.readShort(r,s),s+=2,a.ySuperscriptYSize=o.readShort(r,s),s+=2,a.ySuperscriptXOffset=o.readShort(r,s),s+=2,a.ySuperscriptYOffset=o.readShort(r,s),s+=2,a.yStrikeoutSize=o.readShort(r,s),s+=2,a.yStrikeoutPosition=o.readShort(r,s),s+=2,a.sFamilyClass=o.readShort(r,s),s+=2,a.panose=o.readBytes(r,s,10),s+=10,a.ulUnicodeRange1=o.readUint(r,s),s+=4,a.ulUnicodeRange2=o.readUint(r,s),s+=4,a.ulUnicodeRange3=o.readUint(r,s),s+=4,a.ulUnicodeRange4=o.readUint(r,s),s+=4,a.achVendID=[o.readInt8(r,s),o.readInt8(r,s+1),o.readInt8(r,s+2),o.readInt8(r,s+3)],s+=4,a.fsSelection=o.readUshort(r,s),s+=2,a.usFirstCharIndex=o.readUshort(r,s),s+=2,a.usLastCharIndex=o.readUshort(r,s),s+=2,a.sTypoAscender=o.readShort(r,s),s+=2,a.sTypoDescender=o.readShort(r,s),s+=2,a.sTypoLineGap=o.readShort(r,s),s+=2,a.usWinAscent=o.readUshort(r,s),s+=2,a.usWinDescent=o.readUshort(r,s),s+=2},e["OS/2"].version1=function(r,s,a){var o=e._bin;return s=e["OS/2"].version0(r,s,a),a.ulCodePageRange1=o.readUint(r,s),s+=4,a.ulCodePageRange2=o.readUint(r,s),s+=4},e["OS/2"].version2=function(r,s,a){var o=e._bin;return s=e["OS/2"].version1(r,s,a),a.sxHeight=o.readShort(r,s),s+=2,a.sCapHeight=o.readShort(r,s),s+=2,a.usDefault=o.readUshort(r,s),s+=2,a.usBreak=o.readUshort(r,s),s+=2,a.usMaxContext=o.readUshort(r,s),s+=2},e["OS/2"].version5=function(r,s,a){var o=e._bin;return s=e["OS/2"].version2(r,s,a),a.usLowerOpticalPointSize=o.readUshort(r,s),s+=2,a.usUpperOpticalPointSize=o.readUshort(r,s),s+=2},e.post={},e.post.parse=function(r,s,a){var o=e._bin,l={};return l.version=o.readFixed(r,s),s+=4,l.italicAngle=o.readFixed(r,s),s+=4,l.underlinePosition=o.readShort(r,s),s+=2,l.underlineThickness=o.readShort(r,s),s+=2,l},e==null&&(e={}),e.U==null&&(e.U={}),e.U.codeToGlyph=function(r,s){var a=r.cmap,o=-1;if(a.p0e4!=null?o=a.p0e4:a.p3e1!=null?o=a.p3e1:a.p1e0!=null?o=a.p1e0:a.p0e3!=null&&(o=a.p0e3),o==-1)throw"no familiar platform and encoding!";var l=a.tables[o];if(l.format==0)return s>=l.map.length?0:l.map[s];if(l.format==4){for(var c=-1,u=0;u<l.endCount.length;u++)if(s<=l.endCount[u]){c=u;break}return c==-1||l.startCount[c]>s?0:65535&(l.idRangeOffset[c]!=0?l.glyphIdArray[s-l.startCount[c]+(l.idRangeOffset[c]>>1)-(l.idRangeOffset.length-c)]:s+l.idDelta[c])}if(l.format==12){if(s>l.groups[l.groups.length-1][1])return 0;for(u=0;u<l.groups.length;u++){var f=l.groups[u];if(f[0]<=s&&s<=f[1])return f[2]+(s-f[0])}return 0}throw"unknown cmap table format "+l.format},e.U.glyphToPath=function(r,s){var a={cmds:[],crds:[]};if(r.SVG&&r.SVG.entries[s]){var o=r.SVG.entries[s];return o==null?a:(typeof o=="string"&&(o=e.SVG.toPath(o),r.SVG.entries[s]=o),o)}if(r.CFF){var l={x:0,y:0,stack:[],nStems:0,haveWidth:!1,width:r.CFF.Private?r.CFF.Private.defaultWidthX:0,open:!1},c=r.CFF,u=r.CFF.Private;if(c.ROS){for(var f=0;c.FDSelect[f+2]<=s;)f+=2;u=c.FDArray[c.FDSelect[f+1]].Private}e.U._drawCFF(r.CFF.CharStrings[s],l,c,u,a)}else r.glyf&&e.U._drawGlyf(s,r,a);return a},e.U._drawGlyf=function(r,s,a){var o=s.glyf[r];o==null&&(o=s.glyf[r]=e.glyf._parseGlyf(s,r)),o!=null&&(o.noc>-1?e.U._simpleGlyph(o,a):e.U._compoGlyph(o,s,a))},e.U._simpleGlyph=function(r,s){for(var a=0;a<r.noc;a++){for(var o=a==0?0:r.endPts[a-1]+1,l=r.endPts[a],c=o;c<=l;c++){var u=c==o?l:c-1,f=c==l?o:c+1,h=1&r.flags[c],d=1&r.flags[u],g=1&r.flags[f],m=r.xs[c],p=r.ys[c];if(c==o)if(h){if(!d){e.U.P.moveTo(s,m,p);continue}e.U.P.moveTo(s,r.xs[u],r.ys[u])}else d?e.U.P.moveTo(s,r.xs[u],r.ys[u]):e.U.P.moveTo(s,(r.xs[u]+m)/2,(r.ys[u]+p)/2);h?d&&e.U.P.lineTo(s,m,p):g?e.U.P.qcurveTo(s,m,p,r.xs[f],r.ys[f]):e.U.P.qcurveTo(s,m,p,(m+r.xs[f])/2,(p+r.ys[f])/2)}e.U.P.closePath(s)}},e.U._compoGlyph=function(r,s,a){for(var o=0;o<r.parts.length;o++){var l={cmds:[],crds:[]},c=r.parts[o];e.U._drawGlyf(c.glyphIndex,s,l);for(var u=c.m,f=0;f<l.crds.length;f+=2){var h=l.crds[f],d=l.crds[f+1];a.crds.push(h*u.a+d*u.b+u.tx),a.crds.push(h*u.c+d*u.d+u.ty)}for(f=0;f<l.cmds.length;f++)a.cmds.push(l.cmds[f])}},e.U._getGlyphClass=function(r,s){var a=e._lctf.getInterval(s,r);return a==-1?0:s[a+2]},e.U._applySubs=function(r,s,a,o){for(var l=r.length-s-1,c=0;c<a.tabs.length;c++)if(a.tabs[c]!=null){var u,f=a.tabs[c];if(!f.coverage||(u=e._lctf.coverageIndex(f.coverage,r[s]))!=-1){if(a.ltype==1)r[s],f.fmt==1?r[s]=r[s]+f.delta:r[s]=f.newg[u];else if(a.ltype==4)for(var h=f.vals[u],d=0;d<h.length;d++){var g=h[d],m=g.chain.length;if(!(m>l)){for(var p=!0,_=0,v=0;v<m;v++){for(;r[s+_+(1+v)]==-1;)_++;g.chain[v]!=r[s+_+(1+v)]&&(p=!1)}if(p){for(r[s]=g.nglyph,v=0;v<m+_;v++)r[s+v+1]=-1;break}}}else if(a.ltype==5&&f.fmt==2)for(var M=e._lctf.getInterval(f.cDef,r[s]),y=f.cDef[M+2],T=f.scset[y],S=0;S<T.length;S++){var E=T[S],b=E.input;if(!(b.length>l)){for(p=!0,v=0;v<b.length;v++){var x=e._lctf.getInterval(f.cDef,r[s+1+v]);if(M==-1&&f.cDef[x+2]!=b[v]){p=!1;break}}if(p){var A=E.substLookupRecords;for(d=0;d<A.length;d+=2)A[d],A[d+1]}}}else if(a.ltype==6&&f.fmt==3){if(!e.U._glsCovered(r,f.backCvg,s-f.backCvg.length)||!e.U._glsCovered(r,f.inptCvg,s)||!e.U._glsCovered(r,f.ahedCvg,s+f.inptCvg.length))continue;var C=f.lookupRec;for(S=0;S<C.length;S+=2){M=C[S];var R=o[C[S+1]];e.U._applySubs(r,s+M,R,o)}}}}},e.U._glsCovered=function(r,s,a){for(var o=0;o<s.length;o++)if(e._lctf.coverageIndex(s[o],r[a+o])==-1)return!1;return!0},e.U.glyphsToPath=function(r,s,a){for(var o={cmds:[],crds:[]},l=0,c=0;c<s.length;c++){var u=s[c];if(u!=-1){for(var f=c<s.length-1&&s[c+1]!=-1?s[c+1]:0,h=e.U.glyphToPath(r,u),d=0;d<h.crds.length;d+=2)o.crds.push(h.crds[d]+l),o.crds.push(h.crds[d+1]);for(a&&o.cmds.push(a),d=0;d<h.cmds.length;d++)o.cmds.push(h.cmds[d]);a&&o.cmds.push("X"),l+=r.hmtx.aWidth[u],c<s.length-1&&(l+=e.U.getPairAdjustment(r,u,f))}}return o},e.U.P={},e.U.P.moveTo=function(r,s,a){r.cmds.push("M"),r.crds.push(s,a)},e.U.P.lineTo=function(r,s,a){r.cmds.push("L"),r.crds.push(s,a)},e.U.P.curveTo=function(r,s,a,o,l,c,u){r.cmds.push("C"),r.crds.push(s,a,o,l,c,u)},e.U.P.qcurveTo=function(r,s,a,o,l){r.cmds.push("Q"),r.crds.push(s,a,o,l)},e.U.P.closePath=function(r){r.cmds.push("Z")},e.U._drawCFF=function(r,s,a,o,l){for(var c=s.stack,u=s.nStems,f=s.haveWidth,h=s.width,d=s.open,g=0,m=s.x,p=s.y,_=0,v=0,M=0,y=0,T=0,S=0,E=0,b=0,x=0,A=0,C={val:0,size:0};g<r.length;){e.CFF.getCharString(r,g,C);var R=C.val;if(g+=C.size,R=="o1"||R=="o18")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0;else if(R=="o3"||R=="o23")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0;else if(R=="o4")c.length>1&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),d&&e.U.P.closePath(l),p+=c.pop(),e.U.P.moveTo(l,m,p),d=!0;else if(R=="o5")for(;c.length>0;)m+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,m,p);else if(R=="o6"||R=="o7")for(var L=c.length,U=R=="o6",I=0;I<L;I++){var F=c.shift();U?m+=F:p+=F,U=!U,e.U.P.lineTo(l,m,p)}else if(R=="o8"||R=="o24"){L=c.length;for(var O=0;O+6<=L;)_=m+c.shift(),v=p+c.shift(),M=_+c.shift(),y=v+c.shift(),m=M+c.shift(),p=y+c.shift(),e.U.P.curveTo(l,_,v,M,y,m,p),O+=6;R=="o24"&&(m+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,m,p))}else{if(R=="o11")break;if(R=="o1234"||R=="o1235"||R=="o1236"||R=="o1237")R=="o1234"&&(v=p,M=(_=m+c.shift())+c.shift(),A=y=v+c.shift(),S=y,b=p,m=(E=(T=(x=M+c.shift())+c.shift())+c.shift())+c.shift(),e.U.P.curveTo(l,_,v,M,y,x,A),e.U.P.curveTo(l,T,S,E,b,m,p)),R=="o1235"&&(_=m+c.shift(),v=p+c.shift(),M=_+c.shift(),y=v+c.shift(),x=M+c.shift(),A=y+c.shift(),T=x+c.shift(),S=A+c.shift(),E=T+c.shift(),b=S+c.shift(),m=E+c.shift(),p=b+c.shift(),c.shift(),e.U.P.curveTo(l,_,v,M,y,x,A),e.U.P.curveTo(l,T,S,E,b,m,p)),R=="o1236"&&(_=m+c.shift(),v=p+c.shift(),M=_+c.shift(),A=y=v+c.shift(),S=y,E=(T=(x=M+c.shift())+c.shift())+c.shift(),b=S+c.shift(),m=E+c.shift(),e.U.P.curveTo(l,_,v,M,y,x,A),e.U.P.curveTo(l,T,S,E,b,m,p)),R=="o1237"&&(_=m+c.shift(),v=p+c.shift(),M=_+c.shift(),y=v+c.shift(),x=M+c.shift(),A=y+c.shift(),T=x+c.shift(),S=A+c.shift(),E=T+c.shift(),b=S+c.shift(),Math.abs(E-m)>Math.abs(b-p)?m=E+c.shift():p=b+c.shift(),e.U.P.curveTo(l,_,v,M,y,x,A),e.U.P.curveTo(l,T,S,E,b,m,p));else if(R=="o14"){if(c.length>0&&!f&&(h=c.shift()+a.nominalWidthX,f=!0),c.length==4){var j=c.shift(),G=c.shift(),W=c.shift(),N=c.shift(),k=e.CFF.glyphBySE(a,W),J=e.CFF.glyphBySE(a,N);e.U._drawCFF(a.CharStrings[k],s,a,o,l),s.x=j,s.y=G,e.U._drawCFF(a.CharStrings[J],s,a,o,l)}d&&(e.U.P.closePath(l),d=!1)}else if(R=="o19"||R=="o20")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0,g+=u+7>>3;else if(R=="o21")c.length>2&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),p+=c.pop(),m+=c.pop(),d&&e.U.P.closePath(l),e.U.P.moveTo(l,m,p),d=!0;else if(R=="o22")c.length>1&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),m+=c.pop(),d&&e.U.P.closePath(l),e.U.P.moveTo(l,m,p),d=!0;else if(R=="o25"){for(;c.length>6;)m+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,m,p);_=m+c.shift(),v=p+c.shift(),M=_+c.shift(),y=v+c.shift(),m=M+c.shift(),p=y+c.shift(),e.U.P.curveTo(l,_,v,M,y,m,p)}else if(R=="o26")for(c.length%2&&(m+=c.shift());c.length>0;)_=m,v=p+c.shift(),m=M=_+c.shift(),p=(y=v+c.shift())+c.shift(),e.U.P.curveTo(l,_,v,M,y,m,p);else if(R=="o27")for(c.length%2&&(p+=c.shift());c.length>0;)v=p,M=(_=m+c.shift())+c.shift(),y=v+c.shift(),m=M+c.shift(),p=y,e.U.P.curveTo(l,_,v,M,y,m,p);else if(R=="o10"||R=="o29"){var Q=R=="o10"?o:a;if(c.length==0)console.debug("error: empty stack");else{var K=c.pop(),H=Q.Subrs[K+Q.Bias];s.x=m,s.y=p,s.nStems=u,s.haveWidth=f,s.width=h,s.open=d,e.U._drawCFF(H,s,a,o,l),m=s.x,p=s.y,u=s.nStems,f=s.haveWidth,h=s.width,d=s.open}}else if(R=="o30"||R=="o31"){var Y=c.length,Z=(O=0,R=="o31");for(O+=Y-(L=-3&Y);O<L;)Z?(v=p,M=(_=m+c.shift())+c.shift(),p=(y=v+c.shift())+c.shift(),L-O==5?(m=M+c.shift(),O++):m=M,Z=!1):(_=m,v=p+c.shift(),M=_+c.shift(),y=v+c.shift(),m=M+c.shift(),L-O==5?(p=y+c.shift(),O++):p=y,Z=!0),e.U.P.curveTo(l,_,v,M,y,m,p),O+=4}else{if((R+"").charAt(0)=="o")throw console.debug("Unknown operation: "+R,r),R;c.push(R)}}}s.x=m,s.y=p,s.nStems=u,s.haveWidth=f,s.width=h,s.open=d};var t=e,i={Typr:t};return n.Typr=t,n.default=i,Object.defineProperty(n,"__esModule",{value:!0}),n})({}).Typr}/*!
Custom bundle of woff2otf (https://github.com/arty-name/woff2otf) with fflate
(https://github.com/101arrowz/fflate) for use in Troika text rendering. 
Original licenses apply: 
- fflate: https://github.com/101arrowz/fflate/blob/master/LICENSE (MIT)
- woff2otf.js: https://github.com/arty-name/woff2otf/blob/master/woff2otf.js (Apache2)
*/function QS(){return(function(n){var e=Uint8Array,t=Uint16Array,i=Uint32Array,r=new e([0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0,0,0,0]),s=new e([0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,0,0]),a=new e([16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]),o=function(R,L){for(var U=new t(31),I=0;I<31;++I)U[I]=L+=1<<R[I-1];var F=new i(U[30]);for(I=1;I<30;++I)for(var O=U[I];O<U[I+1];++O)F[O]=O-U[I]<<5|I;return[U,F]},l=o(r,2),c=l[0],u=l[1];c[28]=258,u[258]=28;for(var f=o(s,0)[0],h=new t(32768),d=0;d<32768;++d){var g=(43690&d)>>>1|(21845&d)<<1;g=(61680&(g=(52428&g)>>>2|(13107&g)<<2))>>>4|(3855&g)<<4,h[d]=((65280&g)>>>8|(255&g)<<8)>>>1}var m=function(R,L,U){for(var I=R.length,F=0,O=new t(L);F<I;++F)++O[R[F]-1];var j,G=new t(L);for(F=0;F<L;++F)G[F]=G[F-1]+O[F-1]<<1;{j=new t(1<<L);var W=15-L;for(F=0;F<I;++F)if(R[F])for(var N=F<<4|R[F],k=L-R[F],J=G[R[F]-1]++<<k,Q=J|(1<<k)-1;J<=Q;++J)j[h[J]>>>W]=N}return j},p=new e(288);for(d=0;d<144;++d)p[d]=8;for(d=144;d<256;++d)p[d]=9;for(d=256;d<280;++d)p[d]=7;for(d=280;d<288;++d)p[d]=8;var _=new e(32);for(d=0;d<32;++d)_[d]=5;var v=m(p,9),M=m(_,5),y=function(R){for(var L=R[0],U=1;U<R.length;++U)R[U]>L&&(L=R[U]);return L},T=function(R,L,U){var I=L/8|0;return(R[I]|R[I+1]<<8)>>(7&L)&U},S=function(R,L){var U=L/8|0;return(R[U]|R[U+1]<<8|R[U+2]<<16)>>(7&L)},E=["unexpected EOF","invalid block type","invalid length/literal","invalid distance","stream finished","no stream handler",,"no callback","invalid UTF-8 data","extra field too long","date not in range 1980-2099","filename too long","stream finishing","invalid zip data"],b=function(R,L,U){var I=new Error(L||E[R]);if(I.code=R,Error.captureStackTrace&&Error.captureStackTrace(I,b),!U)throw I;return I},x=function(R,L,U){var I=R.length;if(!I||U&&!U.l&&I<5)return L||new e(0);var F=!L||U,O=!U||U.i;U||(U={}),L||(L=new e(3*I));var j,G=function(he){var Pe=L.length;if(he>Pe){var ve=new e(Math.max(2*Pe,he));ve.set(L),L=ve}},W=U.f||0,N=U.p||0,k=U.b||0,J=U.l,Q=U.d,K=U.m,H=U.n,Y=8*I;do{if(!J){U.f=W=T(R,N,1);var Z=T(R,N+1,3);if(N+=3,!Z){var fe=R[(B=((j=N)/8|0)+(7&j&&1)+4)-4]|R[B-3]<<8,Me=B+fe;if(Me>I){O&&b(0);break}F&&G(k+fe),L.set(R.subarray(B,Me),k),U.b=k+=fe,U.p=N=8*Me;continue}if(Z==1)J=v,Q=M,K=9,H=5;else if(Z==2){var ce=T(R,N,31)+257,de=T(R,N+10,15)+4,Ne=ce+T(R,N+5,31)+1;N+=14;for(var Oe=new e(Ne),Ce=new e(19),Te=0;Te<de;++Te)Ce[a[Te]]=T(R,N+3*Te,7);N+=3*de;var Ge=y(Ce),_e=(1<<Ge)-1,ze=m(Ce,Ge);for(Te=0;Te<Ne;){var B,ue=ze[T(R,N,_e)];if(N+=15&ue,(B=ue>>>4)<16)Oe[Te++]=B;else{var Le=0,Ee=0;for(B==16?(Ee=3+T(R,N,3),N+=2,Le=Oe[Te-1]):B==17?(Ee=3+T(R,N,7),N+=3):B==18&&(Ee=11+T(R,N,127),N+=7);Ee--;)Oe[Te++]=Le}}var le=Oe.subarray(0,ce),we=Oe.subarray(ce);K=y(le),H=y(we),J=m(le,K),Q=m(we,H)}else b(1);if(N>Y){O&&b(0);break}}F&&G(k+131072);for(var D=(1<<K)-1,w=(1<<H)-1,z=N;;z=N){var $=(Le=J[S(R,N)&D])>>>4;if((N+=15&Le)>Y){O&&b(0);break}if(Le||b(2),$<256)L[k++]=$;else{if($==256){z=N,J=null;break}var oe=$-254;if($>264){var ge=r[Te=$-257];oe=T(R,N,(1<<ge)-1)+c[Te],N+=ge}var be=Q[S(R,N)&w],ee=be>>>4;if(be||b(3),N+=15&be,we=f[ee],ee>3&&(ge=s[ee],we+=S(R,N)&(1<<ge)-1,N+=ge),N>Y){O&&b(0);break}F&&G(k+131072);for(var re=k+oe;k<re;k+=4)L[k]=L[k-we],L[k+1]=L[k+1-we],L[k+2]=L[k+2-we],L[k+3]=L[k+3-we];k=re}}U.l=J,U.p=z,U.b=k,J&&(W=1,U.m=K,U.d=Q,U.n=H)}while(!W);return k==L.length?L:(function(he,Pe,ve){(ve==null||ve>he.length)&&(ve=he.length);var Se=new(he instanceof t?t:he instanceof i?i:e)(ve-Pe);return Se.set(he.subarray(Pe,ve)),Se})(L,0,k)},A=new e(0),C=typeof TextDecoder<"u"&&new TextDecoder;try{C.decode(A,{stream:!0})}catch{}return n.convert_streams=function(R){var L=new DataView(R),U=0;function I(){var ce=L.getUint16(U);return U+=2,ce}function F(){var ce=L.getUint32(U);return U+=4,ce}function O(ce){fe.setUint16(Me,ce),Me+=2}function j(ce){fe.setUint32(Me,ce),Me+=4}for(var G={signature:F(),flavor:F(),length:F(),numTables:I(),reserved:I(),totalSfntSize:F(),majorVersion:I(),minorVersion:I(),metaOffset:F(),metaLength:F(),metaOrigLength:F(),privOffset:F(),privLength:F()},W=0;Math.pow(2,W)<=G.numTables;)W++;W--;for(var N=16*Math.pow(2,W),k=16*G.numTables-N,J=12,Q=[],K=0;K<G.numTables;K++)Q.push({tag:F(),offset:F(),compLength:F(),origLength:F(),origChecksum:F()}),J+=16;var H,Y=new Uint8Array(12+16*Q.length+Q.reduce((function(ce,de){return ce+de.origLength+4}),0)),Z=Y.buffer,fe=new DataView(Z),Me=0;return j(G.flavor),O(G.numTables),O(N),O(W),O(k),Q.forEach((function(ce){j(ce.tag),j(ce.origChecksum),j(J),j(ce.origLength),ce.outOffset=J,(J+=ce.origLength)%4!=0&&(J+=4-J%4)})),Q.forEach((function(ce){var de,Ne=R.slice(ce.offset,ce.offset+ce.compLength);if(ce.compLength!=ce.origLength){var Oe=new Uint8Array(ce.origLength);de=new Uint8Array(Ne,2),x(de,Oe)}else Oe=new Uint8Array(Ne);Y.set(Oe,ce.outOffset);var Ce=0;(J=ce.outOffset+ce.origLength)%4!=0&&(Ce=4-J%4),Y.set(new Uint8Array(Ce).buffer,ce.outOffset+ce.origLength),H=J+Ce})),Z.slice(0,H)},Object.defineProperty(n,"__esModule",{value:!0}),n})({}).convert_streams}function ey(n,e){const t={M:2,L:2,Q:4,C:6,Z:0},i={C:"18g,ca,368,1kz",D:"17k,6,2,2+4,5+c,2+6,2+1,10+1,9+f,j+11,2+1,a,2,2+1,15+2,3,j+2,6+3,2+8,2,2,2+1,w+a,4+e,3+3,2,3+2,3+5,23+w,2f+4,3,2+9,2,b,2+3,3,1k+9,6+1,3+1,2+2,2+d,30g,p+y,1,1+1g,f+x,2,sd2+1d,jf3+4,f+3,2+4,2+2,b+3,42,2,4+2,2+1,2,3,t+1,9f+w,2,el+2,2+g,d+2,2l,2+1,5,3+1,2+1,2,3,6,16wm+1v",R:"17m+3,2,2,6+3,m,15+2,2+2,h+h,13,3+8,2,2,3+1,2,p+1,x,5+4,5,a,2,2,3,u,c+2,g+1,5,2+1,4+1,5j,6+1,2,b,2+2,f,2+1,1s+2,2,3+1,7,1ez0,2,2+1,4+4,b,4,3,b,42,2+2,4,3,2+1,2,o+3,ae,ep,x,2o+2,3+1,3,5+1,6",L:"x9u,jff,a,fd,jv",T:"4t,gj+33,7o+4,1+1,7c+18,2,2+1,2+1,2,21+a,2,1b+k,h,2u+6,3+5,3+1,2+3,y,2,v+q,2k+a,1n+8,a,p+3,2+8,2+2,2+4,18+2,3c+e,2+v,1k,2,5+7,5,4+6,b+1,u,1n,5+3,9,l+1,r,3+1,1m,5+1,5+1,3+2,4,v+1,4,c+1,1m,5+4,2+1,5,l+1,n+5,2,1n,3,2+3,9,8+1,c+1,v,1q,d,1f,4,1m+2,6+2,2+3,8+1,c+1,u,1n,3,7,6+1,l+1,t+1,1m+1,5+3,9,l+1,u,21,8+2,2,2j,3+6,d+7,2r,3+8,c+5,23+1,s,2,2,1k+d,2+4,2+1,6+a,2+z,a,2v+3,2+5,2+1,3+1,q+1,5+2,h+3,e,3+1,7,g,jk+2,qb+2,u+2,u+1,v+1,1t+1,2+6,9,3+a,a,1a+2,3c+1,z,3b+2,5+1,a,7+2,64+1,3,1n,2+6,2,2,3+7,7+9,3,1d+d,1,1+1,1s+3,1d,2+4,2,6,15+8,d+1,x+3,3+1,2+2,1l,2+1,4,2+2,1n+7,3+1,49+2,2+c,2+6,5,7,4+1,5j+1l,2+4,ek,3+1,r+4,1e+4,6+5,2p+c,1+3,1,1+2,1+b,2db+2,3y,2p+v,ff+3,30+1,n9x,1+2,2+9,x+1,29+1,7l,4,5,q+1,6,48+1,r+h,e,13+7,q+a,1b+2,1d,3+3,3+1,14,1w+5,3+1,3+1,d,9,1c,1g,2+2,3+1,6+1,2,17+1,9,6n,3,5,fn5,ki+f,h+f,5s,6y+2,ea,6b,46+4,1af+2,2+1,6+3,15+2,5,4m+1,fy+3,as+1,4a+a,4x,1j+e,1l+2,1e+3,3+1,1y+2,11+4,2+7,1r,d+1,1h+8,b+3,3,2o+2,3,2+1,7,4h,4+7,m+1,1m+1,4,12+6,4+4,5g+7,3+2,2,o,2d+5,2,5+1,2+1,6n+3,7+1,2+1,s+1,2e+7,3,2+1,2z,2,3+5,2,2u+2,3+3,2+4,78+8,2+1,75+1,2,5,41+3,3+1,5,x+9,15+5,3+3,9,a+5,3+2,1b+c,2+1,bb+6,2+5,2,2b+l,3+6,2+1,2+1,3f+5,4,2+1,2+6,2,21+1,4,2,9o+1,470+8,at4+4,1o+6,t5,1s+3,2a,f5l+1,2+3,43o+2,a+7,1+7,3+6,v+3,45+2,1j0+1i,5+1d,9,f,n+4,2+e,11t+6,2+g,3+6,2+1,2+4,7a+6,c6+3,15t+6,32+6,1,gzau,v+2n,3l+6n"},r=1,s=2,a=4,o=8,l=16,c=32;let u;function f(E){if(!u){const b={R:s,L:r,D:a,C:l,U:c,T:o};u=new Map;for(let x in i){let A=0;i[x].split(",").forEach(C=>{let[R,L]=C.split("+");R=parseInt(R,36),L=L?parseInt(L,36):0,u.set(A+=R,b[x]);for(let U=L;U--;)u.set(++A,b[x])})}}return u.get(E)||c}const h=1,d=2,g=3,m=4,p=[null,"isol","init","fina","medi"];function _(E){const b=new Uint8Array(E.length);let x=c,A=h,C=-1;for(let R=0;R<E.length;R++){const L=E.codePointAt(R);let U=f(L)|0,I=h;U&o||(x&(r|a|l)?U&(s|a|l)?(I=g,(A===h||A===g)&&b[C]++):U&(r|c)&&(A===d||A===m)&&b[C]--:x&(s|c)&&(A===d||A===m)&&b[C]--,A=b[R]=I,x=U,C=R,L>65535&&R++)}return b}function v(E,b){const x=[];for(let C=0;C<b.length;C++){const R=b.codePointAt(C);R>65535&&C++,x.push(n.U.codeToGlyph(E,R))}const A=E.GSUB;if(A){const{lookupList:C,featureList:R}=A;let L;const U=/^(rlig|liga|mset|isol|init|fina|medi|half|pres|blws|ccmp)$/,I=[];R.forEach(F=>{if(U.test(F.tag))for(let O=0;O<F.tab.length;O++){if(I[F.tab[O]])continue;I[F.tab[O]]=!0;const j=C[F.tab[O]],G=/^(isol|init|fina|medi)$/.test(F.tag);G&&!L&&(L=_(b));for(let W=0;W<x.length;W++)(!L||!G||p[L[W]]===F.tag)&&n.U._applySubs(x,W,j,C)}})}return x}function M(E,b){const x=new Int16Array(b.length*3);let A=0;for(;A<b.length;A++){const U=b[A];if(U===-1)continue;x[A*3+2]=E.hmtx.aWidth[U];const I=E.GPOS;if(I){const F=I.lookupList;for(let O=0;O<F.length;O++){const j=F[O];for(let G=0;G<j.tabs.length;G++){const W=j.tabs[G];if(j.ltype===1){if(n._lctf.coverageIndex(W.coverage,U)!==-1&&W.pos){L(W.pos,A);break}}else if(j.ltype===2){let N=null,k=C();if(k!==-1){const J=n._lctf.coverageIndex(W.coverage,b[k]);if(J!==-1){if(W.fmt===1){const Q=W.pairsets[J];for(let K=0;K<Q.length;K++)Q[K].gid2===U&&(N=Q[K])}else if(W.fmt===2){const Q=n.U._getGlyphClass(b[k],W.classDef1),K=n.U._getGlyphClass(U,W.classDef2);N=W.matrix[Q][K]}if(N){N.val1&&L(N.val1,k),N.val2&&L(N.val2,A);break}}}}else if(j.ltype===4){const N=n._lctf.coverageIndex(W.markCoverage,U);if(N!==-1){const k=C(R),J=k===-1?-1:n._lctf.coverageIndex(W.baseCoverage,b[k]);if(J!==-1){const Q=W.markArray[N],K=W.baseArray[J][Q.markClass];x[A*3]=K.x-Q.x+x[k*3]-x[k*3+2],x[A*3+1]=K.y-Q.y+x[k*3+1];break}}}else if(j.ltype===6){const N=n._lctf.coverageIndex(W.mark1Coverage,U);if(N!==-1){const k=C();if(k!==-1){const J=b[k];if(y(E,J)===3){const Q=n._lctf.coverageIndex(W.mark2Coverage,J);if(Q!==-1){const K=W.mark1Array[N],H=W.mark2Array[Q][K.markClass];x[A*3]=H.x-K.x+x[k*3]-x[k*3+2],x[A*3+1]=H.y-K.y+x[k*3+1];break}}}}}}}}else if(E.kern&&!E.cff){const F=C();if(F!==-1){const O=E.kern.glyph1.indexOf(b[F]);if(O!==-1){const j=E.kern.rval[O].glyph2.indexOf(U);j!==-1&&(x[F*3+2]+=E.kern.rval[O].vals[j])}}}}return x;function C(U){for(let I=A-1;I>=0;I--)if(b[I]!==-1&&(!U||U(b[I])))return I;return-1}function R(U){return y(E,U)===1}function L(U,I){for(let F=0;F<3;F++)x[I*3+F]+=U[F]||0}}function y(E,b){const x=E.GDEF&&E.GDEF.glyphClassDef;return x?n.U._getGlyphClass(b,x):0}function T(...E){for(let b=0;b<E.length;b++)if(typeof E[b]=="number")return E[b]}function S(E){const b=Object.create(null),x=E["OS/2"],A=E.hhea,C=E.head.unitsPerEm,R=T(x&&x.sTypoAscender,A&&A.ascender,C),L={unitsPerEm:C,ascender:R,descender:T(x&&x.sTypoDescender,A&&A.descender,0),capHeight:T(x&&x.sCapHeight,R),xHeight:T(x&&x.sxHeight,R),lineGap:T(x&&x.sTypoLineGap,A&&A.lineGap),supportsCodePoint(U){return n.U.codeToGlyph(E,U)>0},forEachGlyph(U,I,F,O){let j=0;const G=1/L.unitsPerEm*I,W=v(E,U);let N=0;const k=M(E,W);return W.forEach((J,Q)=>{if(J!==-1){let K=b[J];if(!K){const{cmds:H,crds:Y}=n.U.glyphToPath(E,J);let Z="",fe=0;for(let Oe=0,Ce=H.length;Oe<Ce;Oe++){const Te=t[H[Oe]];Z+=H[Oe];for(let Ge=1;Ge<=Te;Ge++)Z+=(Ge>1?",":"")+Y[fe++]}let Me,ce,de,Ne;if(Y.length){Me=ce=1/0,de=Ne=-1/0;for(let Oe=0,Ce=Y.length;Oe<Ce;Oe+=2){let Te=Y[Oe],Ge=Y[Oe+1];Te<Me&&(Me=Te),Ge<ce&&(ce=Ge),Te>de&&(de=Te),Ge>Ne&&(Ne=Ge)}}else Me=de=ce=Ne=0;K=b[J]={index:J,advanceWidth:E.hmtx.aWidth[J],xMin:Me,yMin:ce,xMax:de,yMax:Ne,path:Z}}O.call(null,K,j+k[Q*3]*G,k[Q*3+1]*G,N),j+=k[Q*3+2]*G,F&&(j+=F*I)}N+=U.codePointAt(N)>65535?2:1}),j}};return L}return function(b){const x=new Uint8Array(b,0,4),A=n._bin.readASCII(x,0,4);if(A==="wOFF")b=e(b);else if(A==="wOF2")throw new Error("woff2 fonts not supported");return S(n.parse(b)[0])}}const ty=$s({name:"Typr Font Parser",dependencies:[JS,QS,ey],init(n,e,t){const i=n(),r=e();return t(i,r)}});/*!
Custom bundle of @unicode-font-resolver/client v1.0.2 (https://github.com/lojjic/unicode-font-resolver)
for use in Troika text rendering. 
Original MIT license applies
*/function ny(){return(function(n){var e=function(){this.buckets=new Map};e.prototype.add=function(M){var y=M>>5;this.buckets.set(y,(this.buckets.get(y)||0)|1<<(31&M))},e.prototype.has=function(M){var y=this.buckets.get(M>>5);return y!==void 0&&(y&1<<(31&M))!=0},e.prototype.serialize=function(){var M=[];return this.buckets.forEach((function(y,T){M.push((+T).toString(36)+":"+y.toString(36))})),M.join(",")},e.prototype.deserialize=function(M){var y=this;this.buckets.clear(),M.split(",").forEach((function(T){var S=T.split(":");y.buckets.set(parseInt(S[0],36),parseInt(S[1],36))}))};var t=Math.pow(2,8),i=t-1,r=~i;function s(M){var y=(function(S){return S&r})(M).toString(16),T=(function(S){return(S&r)+t-1})(M).toString(16);return"codepoint-index/plane"+(M>>16)+"/"+y+"-"+T+".json"}function a(M,y){var T=M&i,S=y.codePointAt(T/6|0);return((S=(S||48)-48)&1<<T%6)!=0}function o(M,y){var T;(T=M,T.replace(/U\+/gi,"").replace(/^,+|,+$/g,"").split(/,+/).map((function(S){return S.split("-").map((function(E){return parseInt(E.trim(),16)}))}))).forEach((function(S){var E=S[0],b=S[1];b===void 0&&(b=E),y(E,b)}))}function l(M,y){o(M,(function(T,S){for(var E=T;E<=S;E++)y(E)}))}var c={},u={},f=new WeakMap,h="https://cdn.jsdelivr.net/gh/lojjic/unicode-font-resolver@v1.0.1/packages/data";function d(M){var y=f.get(M);return y||(y=new e,l(M.ranges,(function(T){return y.add(T)})),f.set(M,y)),y}var g,m=new Map;function p(M,y,T){return M[y]?y:M[T]?T:(function(S){for(var E in S)return E})(M)}function _(M,y){var T=y;if(!M.includes(T)){T=1/0;for(var S=0;S<M.length;S++)Math.abs(M[S]-y)<Math.abs(T-y)&&(T=M[S])}return T}function v(M){return g||(g=new Set,l("9-D,20,85,A0,1680,2000-200A,2028-202F,205F,3000",(function(y){g.add(y)}))),g.has(M)}return n.CodePointSet=e,n.clearCache=function(){c={},u={}},n.getFontsForString=function(M,y){y===void 0&&(y={});var T,S=y.lang;S===void 0&&(S=new RegExp("\\p{Script=Hangul}","u").test(T=M)?"ko":new RegExp("\\p{Script=Hiragana}|\\p{Script=Katakana}","u").test(T)?"ja":"en");var E=y.category;E===void 0&&(E="sans-serif");var b=y.style;b===void 0&&(b="normal");var x=y.weight;x===void 0&&(x=400);var A=(y.dataUrl||h).replace(/\/$/g,""),C=new Map,R=new Uint8Array(M.length),L={},U={},I=new Array(M.length),F=new Map,O=!1;function j(N){var k=m.get(N);return k||(k=fetch(A+"/"+N).then((function(J){if(!J.ok)throw new Error(J.statusText);return J.json().then((function(Q){if(!Array.isArray(Q)||Q[0]!==1)throw new Error("Incorrect schema version; need 1, got "+Q[0]);return Q[1]}))})).catch((function(J){if(A!==h)return O||(console.error('unicode-font-resolver: Failed loading from dataUrl "'+A+'", trying default CDN. '+J.message),O=!0),A=h,m.delete(N),j(N);throw J})),m.set(N,k)),k}for(var G=function(N){var k=M.codePointAt(N),J=s(k);I[N]=J,c[J]||F.has(J)||F.set(J,j(J).then((function(Q){c[J]=Q}))),k>65535&&(N++,W=N)},W=0;W<M.length;W++)G(W);return Promise.all(F.values()).then((function(){F.clear();for(var N=function(J){var Q=M.codePointAt(J),K=null,H=c[I[J]],Y=void 0;for(var Z in H){var fe=U[Z];if(fe===void 0&&(fe=U[Z]=new RegExp(Z).test(S||"en")),fe){for(var Me in Y=Z,H[Z])if(a(Q,H[Z][Me])){K=Me;break}break}}if(!K){e:for(var ce in H)if(ce!==Y){for(var de in H[ce])if(a(Q,H[ce][de])){K=de;break e}}}K||(console.debug("No font coverage for U+"+Q.toString(16)),K="latin"),I[J]=K,u[K]||F.has(K)||F.set(K,j("font-meta/"+K+".json").then((function(Ne){u[K]=Ne}))),Q>65535&&(J++,k=J)},k=0;k<M.length;k++)N(k);return Promise.all(F.values())})).then((function(){for(var N,k=null,J=0;J<M.length;J++){var Q=M.codePointAt(J);if(k&&(v(Q)||d(k).has(Q)))R[J]=R[J-1];else{k=u[I[J]];var K=L[k.id];if(!K){var H=k.typeforms,Y=p(H,E,"sans-serif"),Z=p(H[Y],b,"normal"),fe=_((N=H[Y])===null||N===void 0?void 0:N[Z],x);K=L[k.id]=A+"/font-files/"+k.id+"/"+Y+"."+Z+"."+fe+".woff"}var Me=C.get(K);Me==null&&(Me=C.size,C.set(K,Me)),R[J]=Me}Q>65535&&(J++,R[J]=R[J-1])}return{fontUrls:Array.from(C.keys()),chars:R}}))},Object.defineProperty(n,"__esModule",{value:!0}),n})({})}function iy(n,e){const t=Object.create(null),i=Object.create(null);function r(a,o){const l=c=>{console.error(`Failure loading font ${a}`,c)};try{const c=new XMLHttpRequest;c.open("get",a,!0),c.responseType="arraybuffer",c.onload=function(){if(c.status>=400)l(new Error(c.statusText));else if(c.status>0)try{const u=n(c.response);u.src=a,o(u)}catch(u){l(u)}},c.onerror=l,c.send()}catch(c){l(c)}}function s(a,o){let l=t[a];l?o(l):i[a]?i[a].push(o):(i[a]=[o],r(a,c=>{c.src=a,t[a]=c,i[a].forEach(u=>u(c)),delete i[a]}))}return function(a,o,{lang:l,fonts:c=[],style:u="normal",weight:f="normal",unicodeFontsURL:h}={}){const d=new Uint8Array(a.length),g=[];a.length||v();const m=new Map,p=[];if(u!=="italic"&&(u="normal"),typeof f!="number"&&(f=f==="bold"?700:400),c&&!Array.isArray(c)&&(c=[c]),c=c.slice().filter(y=>!y.lang||y.lang.test(l)).reverse(),c.length){let E=0;(function b(x=0){for(let A=x,C=a.length;A<C;A++){const R=a.codePointAt(A);if(E===1&&g[d[A-1]].supportsCodePoint(R)||A>0&&/\s/.test(a[A]))d[A]=d[A-1],E===2&&(p[p.length-1][1]=A);else for(let L=d[A],U=c.length;L<=U;L++)if(L===U){const I=E===2?p[p.length-1]:p[p.length]=[A,A];I[1]=A,E=2}else{d[A]=L;const{src:I,unicodeRange:F}=c[L];if(!F||M(R,F)){const O=t[I];if(!O){s(I,()=>{b(A)});return}if(O.supportsCodePoint(R)){let j=m.get(O);typeof j!="number"&&(j=g.length,g.push(O),m.set(O,j)),d[A]=j,E=1;break}}}R>65535&&A+1<C&&(d[A+1]=d[A],A++,E===2&&(p[p.length-1][1]=A))}_()})()}else p.push([0,a.length-1]),_();function _(){if(p.length){const y=p.map(T=>a.substring(T[0],T[1]+1)).join(`
`);e.getFontsForString(y,{lang:l||void 0,style:u,weight:f,dataUrl:h}).then(({fontUrls:T,chars:S})=>{const E=g.length;let b=0;p.forEach(A=>{for(let C=0,R=A[1]-A[0];C<=R;C++)d[A[0]+C]=S[b++]+E;b++});let x=0;T.forEach((A,C)=>{s(A,R=>{g[C+E]=R,++x===T.length&&v()})})})}else v()}function v(){o({chars:d,fonts:g})}function M(y,T){for(let S=0;S<T.length;S++){const[E,b=E]=T[S];if(E<=y&&y<=b)return!0}return!1}}}const ry=$s({name:"FontResolver",dependencies:[iy,ty,ny],init(n,e,t){return n(e,t())}});function sy(n,e){const i=/[\u00AD\u034F\u061C\u115F-\u1160\u17B4-\u17B5\u180B-\u180E\u200B-\u200F\u202A-\u202E\u2060-\u206F\u3164\uFE00-\uFE0F\uFEFF\uFFA0\uFFF0-\uFFF8]/,r="[^\\S\\u00A0]",s=new RegExp(`${r}|[\\-\\u007C\\u00AD\\u2010\\u2012-\\u2014\\u2027\\u2056\\u2E17\\u2E40]`);function a({text:g,lang:m,fonts:p,style:_,weight:v,preResolvedFonts:M,unicodeFontsURL:y},T){const S=({chars:E,fonts:b})=>{let x,A;const C=[];for(let R=0;R<E.length;R++)E[R]!==A?(A=E[R],C.push(x={start:R,end:R,fontObj:b[E[R]]})):x.end=R;T(C)};M?S(M):n(g,S,{lang:m,fonts:p,style:_,weight:v,unicodeFontsURL:y})}function o({text:g="",font:m,lang:p,sdfGlyphSize:_=64,fontSize:v=400,fontWeight:M=1,fontStyle:y="normal",letterSpacing:T=0,lineHeight:S="normal",maxWidth:E=1/0,direction:b,textAlign:x="left",textIndent:A=0,whiteSpace:C="normal",overflowWrap:R="normal",anchorX:L=0,anchorY:U=0,metricsOnly:I=!1,unicodeFontsURL:F,preResolvedFonts:O=null,includeCaretPositions:j=!1,chunkedBoundsSize:G=8192,colorRanges:W=null},N){const k=f(),J={fontLoad:0,typesetting:0};g.indexOf("\r")>-1&&(console.info("Typesetter: got text with \\r chars; normalizing to \\n"),g=g.replace(/\r\n/g,`
`).replace(/\r/g,`
`)),v=+v,T=+T,E=+E,S=S||"normal",A=+A,a({text:g,lang:p,style:y,weight:M,fonts:typeof m=="string"?[{src:m}]:m,unicodeFontsURL:F,preResolvedFonts:O},Q=>{J.fontLoad=f()-k;const K=isFinite(E);let H=null,Y=null,Z=null,fe=null,Me=null,ce=null,de=null,Ne=null,Oe=0,Ce=0,Te=C!=="nowrap";const Ge=new Map,_e=f();let ze=A,B=0,ue=new h;const Le=[ue];Q.forEach(w=>{const{fontObj:z}=w,{ascender:$,descender:oe,unitsPerEm:ge,lineGap:be,capHeight:ee,xHeight:re}=z;let he=Ge.get(z);if(!he){const De=v/ge,Ye=S==="normal"?($-oe+be)*De:S*v,V=(Ye-($-oe)*De)/2,pe=Math.min(Ye,($-oe)*De),ie=($+oe)/2*De+pe/2;he={index:Ge.size,src:z.src,fontObj:z,fontSizeMult:De,unitsPerEm:ge,ascender:$*De,descender:oe*De,capHeight:ee*De,xHeight:re*De,lineHeight:Ye,baseline:-V-$*De,caretTop:ie,caretBottom:ie-pe},Ge.set(z,he)}const{fontSizeMult:Pe}=he,ve=g.slice(w.start,w.end+1);let Se,He;z.forEachGlyph(ve,v,T,(De,Ye,V,pe)=>{Ye+=B,pe+=w.start,Se=Ye,He=De;const ie=g.charAt(pe),Re=De.advanceWidth*Pe,xe=ue.count;let ae;if("isEmpty"in De||(De.isWhitespace=!!ie&&new RegExp(r).test(ie),De.canBreakAfter=!!ie&&s.test(ie),De.isEmpty=De.xMin===De.xMax||De.yMin===De.yMax||i.test(ie)),!De.isWhitespace&&!De.isEmpty&&Ce++,Te&&K&&!De.isWhitespace&&Ye+Re+ze>E&&xe){if(ue.glyphAt(xe-1).glyphObj.canBreakAfter)ae=new h,ze=-Ye;else for(let Ze=xe;Ze--;)if(Ze===0&&R==="break-word"){ae=new h,ze=-Ye;break}else if(ue.glyphAt(Ze).glyphObj.canBreakAfter){ae=ue.splitAt(Ze+1);const ot=ae.glyphAt(0).x;ze-=ot;for(let tt=ae.count;tt--;)ae.glyphAt(tt).x-=ot;break}ae&&(ue.isSoftWrapped=!0,ue=ae,Le.push(ue),Oe=E)}let Ue=ue.glyphAt(ue.count);Ue.glyphObj=De,Ue.x=Ye+ze,Ue.y=V,Ue.width=Re,Ue.charIndex=pe,Ue.fontData=he,ie===`
`&&(ue=new h,Le.push(ue),ze=-(Ye+Re+T*v)+A)}),B=Se+He.advanceWidth*Pe+T*v});let Ee=0;Le.forEach(w=>{let z=!0;for(let $=w.count;$--;){const oe=w.glyphAt($);z&&!oe.glyphObj.isWhitespace&&(w.width=oe.x+oe.width,w.width>Oe&&(Oe=w.width),z=!1);let{lineHeight:ge,capHeight:be,xHeight:ee,baseline:re}=oe.fontData;ge>w.lineHeight&&(w.lineHeight=ge);const he=re-w.baseline;he<0&&(w.baseline+=he,w.cap+=he,w.ex+=he),w.cap=Math.max(w.cap,w.baseline+be),w.ex=Math.max(w.ex,w.baseline+ee)}w.baseline-=Ee,w.cap-=Ee,w.ex-=Ee,Ee+=w.lineHeight});let le=0,we=0;if(L&&(typeof L=="number"?le=-L:typeof L=="string"&&(le=-Oe*(L==="left"?0:L==="center"?.5:L==="right"?1:c(L)))),U&&(typeof U=="number"?we=-U:typeof U=="string"&&(we=U==="top"?0:U==="top-baseline"?-Le[0].baseline:U==="top-cap"?-Le[0].cap:U==="top-ex"?-Le[0].ex:U==="middle"?Ee/2:U==="bottom"?Ee:U==="bottom-baseline"?-Le[Le.length-1].baseline:c(U)*Ee)),!I){const w=e.getEmbeddingLevels(g,b);H=new Uint16Array(Ce),Y=new Uint8Array(Ce),Z=new Float32Array(Ce*2),fe={},de=[1/0,1/0,-1/0,-1/0],Ne=[],j&&(ce=new Float32Array(g.length*4)),W&&(Me=new Uint8Array(Ce*3));let z=0,$=-1,oe=-1,ge,be;if(Le.forEach((ee,re)=>{let{count:he,width:Pe}=ee;if(he>0){let ve=0;for(let pe=he;pe--&&ee.glyphAt(pe).glyphObj.isWhitespace;)ve++;let Se=0,He=0;if(x==="center")Se=(Oe-Pe)/2;else if(x==="right")Se=Oe-Pe;else if(x==="justify"&&ee.isSoftWrapped){let pe=0;for(let ie=he-ve;ie--;)ee.glyphAt(ie).glyphObj.isWhitespace&&pe++;He=(Oe-Pe)/pe}if(He||Se){let pe=0;for(let ie=0;ie<he;ie++){let Re=ee.glyphAt(ie);const xe=Re.glyphObj;Re.x+=Se+pe,He!==0&&xe.isWhitespace&&ie<he-ve&&(pe+=He,Re.width+=He)}}const De=e.getReorderSegments(g,w,ee.glyphAt(0).charIndex,ee.glyphAt(ee.count-1).charIndex);for(let pe=0;pe<De.length;pe++){const[ie,Re]=De[pe];let xe=1/0,ae=-1/0;for(let Ue=0;Ue<he;Ue++)if(ee.glyphAt(Ue).charIndex>=ie){let Ze=Ue,ot=Ue;for(;ot<he;ot++){let tt=ee.glyphAt(ot);if(tt.charIndex>Re)break;ot<he-ve&&(xe=Math.min(xe,tt.x),ae=Math.max(ae,tt.x+tt.width))}for(let tt=Ze;tt<ot;tt++){const Ht=ee.glyphAt(tt);Ht.x=ae-(Ht.x+Ht.width-xe)}break}}let Ye;const V=pe=>Ye=pe;for(let pe=0;pe<he;pe++){const ie=ee.glyphAt(pe);Ye=ie.glyphObj;const Re=Ye.index,xe=w.levels[ie.charIndex]&1;if(xe){const ae=e.getMirroredCharacter(g[ie.charIndex]);ae&&ie.fontData.fontObj.forEachGlyph(ae,0,0,V)}if(j){const{charIndex:ae,fontData:Ue}=ie,Ze=ie.x+le,ot=ie.x+ie.width+le;ce[ae*4]=xe?ot:Ze,ce[ae*4+1]=xe?Ze:ot,ce[ae*4+2]=ee.baseline+Ue.caretBottom+we,ce[ae*4+3]=ee.baseline+Ue.caretTop+we;const tt=ae-$;tt>1&&u(ce,$,tt),$=ae}if(W){const{charIndex:ae}=ie;for(;ae>oe;)oe++,W.hasOwnProperty(oe)&&(be=W[oe])}if(!Ye.isWhitespace&&!Ye.isEmpty){const ae=z++,{fontSizeMult:Ue,src:Ze,index:ot}=ie.fontData,tt=fe[Ze]||(fe[Ze]={});tt[Re]||(tt[Re]={path:Ye.path,pathBounds:[Ye.xMin,Ye.yMin,Ye.xMax,Ye.yMax]});const Ht=ie.x+le,qt=ie.y+ee.baseline+we;Z[ae*2]=Ht,Z[ae*2+1]=qt;const Un=Ht+Ye.xMin*Ue,di=qt+Ye.yMin*Ue,pi=Ht+Ye.xMax*Ue,Yn=qt+Ye.yMax*Ue;Un<de[0]&&(de[0]=Un),di<de[1]&&(de[1]=di),pi>de[2]&&(de[2]=pi),Yn>de[3]&&(de[3]=Yn),ae%G===0&&(ge={start:ae,end:ae,rect:[1/0,1/0,-1/0,-1/0]},Ne.push(ge)),ge.end++;const It=ge.rect;if(Un<It[0]&&(It[0]=Un),di<It[1]&&(It[1]=di),pi>It[2]&&(It[2]=pi),Yn>It[3]&&(It[3]=Yn),H[ae]=Re,Y[ae]=ot,W){const ei=ae*3;Me[ei]=be>>16&255,Me[ei+1]=be>>8&255,Me[ei+2]=be&255}}}}}),ce){const ee=g.length-$;ee>1&&u(ce,$,ee)}}const D=[];Ge.forEach(({index:w,src:z,unitsPerEm:$,ascender:oe,descender:ge,lineHeight:be,capHeight:ee,xHeight:re})=>{D[w]={src:z,unitsPerEm:$,ascender:oe,descender:ge,lineHeight:be,capHeight:ee,xHeight:re}}),J.typesetting=f()-_e,N({glyphIds:H,glyphFontIndices:Y,glyphPositions:Z,glyphData:fe,fontData:D,caretPositions:ce,glyphColors:Me,chunkedBounds:Ne,fontSize:v,topBaseline:we+Le[0].baseline,blockBounds:[le,we-Ee,le+Oe,we],visibleBounds:de,timings:J})})}function l(g,m){o({...g,metricsOnly:!0},p=>{const[_,v,M,y]=p.blockBounds;m({width:M-_,height:y-v})})}function c(g){let m=g.match(/^([\d.]+)%$/),p=m?parseFloat(m[1]):NaN;return isNaN(p)?0:p/100}function u(g,m,p){const _=g[m*4],v=g[m*4+1],M=g[m*4+2],y=g[m*4+3],T=(v-_)/p;for(let S=0;S<p;S++){const E=(m+S)*4;g[E]=_+T*S,g[E+1]=_+T*(S+1),g[E+2]=M,g[E+3]=y}}function f(){return(self.performance||Date).now()}function h(){this.data=[]}const d=["glyphObj","x","y","width","charIndex","fontData"];return h.prototype={width:0,lineHeight:0,baseline:0,cap:0,ex:0,isSoftWrapped:!1,get count(){return Math.ceil(this.data.length/d.length)},glyphAt(g){let m=h.flyweight;return m.data=this.data,m.index=g,m},splitAt(g){let m=new h;return m.data=this.data.splice(g*d.length),m}},h.flyweight=d.reduce((g,m,p,_)=>(Object.defineProperty(g,m,{get(){return this.data[this.index*d.length+p]},set(v){this.data[this.index*d.length+p]=v}}),g),{data:null,index:0}),{typeset:o,measure:l}}const zr=()=>(self.performance||Date).now(),Nl=r0();let fp;function ay(n,e,t,i,r,s,a,o,l,c,u=!0){return u?ly(n,e,t,i,r,s,a,o,l,c).then(null,f=>(fp||(console.warn("WebGL SDF generation failed, falling back to JS",f),fp=!0),pp(n,e,t,i,r,s,a,o,l,c))):pp(n,e,t,i,r,s,a,o,l,c)}const tl=[],oy=5;let yh=0;function a0(){const n=zr();for(;tl.length&&zr()-n<oy;)tl.shift()();yh=tl.length?setTimeout(a0,0):0}const ly=(...n)=>new Promise((e,t)=>{tl.push(()=>{const i=zr();try{Nl.webgl.generateIntoCanvas(...n),e({timing:zr()-i})}catch(r){t(r)}}),yh||(yh=setTimeout(a0,0))}),cy=4,uy=2e3,dp={};let hy=0;function pp(n,e,t,i,r,s,a,o,l,c){const u="TroikaTextSDFGenerator_JS_"+hy++%cy;let f=dp[u];return f||(f=dp[u]={workerModule:$s({name:u,workerId:u,dependencies:[r0,zr],init(h,d){const g=h().javascript.generate;return function(...m){const p=d();return{textureData:g(...m),timing:d()-p}}},getTransferables(h){return[h.textureData.buffer]}}),requests:0,idleTimer:null}),f.requests++,clearTimeout(f.idleTimer),f.workerModule(n,e,t,i,r,s).then(({textureData:h,timing:d})=>{const g=zr(),m=new Uint8Array(h.length*4);for(let p=0;p<h.length;p++)m[p*4+c]=h[p];return Nl.webglUtils.renderImageData(a,m,o,l,n,e,1<<3-c),d+=zr()-g,--f.requests===0&&(f.idleTimer=setTimeout(()=>{HS(u)},uy)),{timing:d}})}function fy(n){n._warm||(Nl.webgl.isSupported(n),n._warm=!0)}const dy=Nl.webglUtils.resizeWebGLCanvasWithoutClearing,Ca={unicodeFontsURL:null,sdfGlyphSize:64,sdfMargin:1/16,sdfExponent:9,textureWidth:2048},py=new ut;function Ts(){return(self.performance||Date).now()}const mp=Object.create(null);function my(n,e){n=_y({},n);const t=Ts(),i=[];if(n.font&&i.push({label:"user",src:vy(n.font)}),n.font=i,n.text=""+n.text,n.sdfGlyphSize=n.sdfGlyphSize||Ca.sdfGlyphSize,n.unicodeFontsURL=n.unicodeFontsURL||Ca.unicodeFontsURL,n.colorRanges!=null){let h={};for(let d in n.colorRanges)if(n.colorRanges.hasOwnProperty(d)){let g=n.colorRanges[d];typeof g!="number"&&(g=py.set(g).getHex()),h[d]=g}n.colorRanges=h}Object.freeze(n);const{textureWidth:r,sdfExponent:s}=Ca,{sdfGlyphSize:a}=n,o=r/a*4;let l=mp[a];if(!l){const h=document.createElement("canvas");h.width=r,h.height=a*256/o,l=mp[a]={glyphCount:0,sdfGlyphSize:a,sdfCanvas:h,sdfTexture:new Zt(h,void 0,void 0,void 0,zt,zt),contextLost:!1,glyphsByFont:new Map},l.sdfTexture.generateMipmaps=!1,gy(l)}const{sdfTexture:c,sdfCanvas:u}=l;c0(n).then(h=>{const{glyphIds:d,glyphFontIndices:g,fontData:m,glyphPositions:p,fontSize:_,timings:v}=h,M=[],y=new Float32Array(d.length*4);let T=0,S=0;const E=Ts(),b=m.map(L=>{let U=l.glyphsByFont.get(L.src);return U||l.glyphsByFont.set(L.src,U=new Map),U});d.forEach((L,U)=>{const I=g[U],{src:F,unitsPerEm:O}=m[I];let j=b[I].get(L);if(!j){const{path:J,pathBounds:Q}=h.glyphData[F][L],K=Math.max(Q[2]-Q[0],Q[3]-Q[1])/a*(Ca.sdfMargin*a+.5),H=l.glyphCount++,Y=[Q[0]-K,Q[1]-K,Q[2]+K,Q[3]+K];b[I].set(L,j={path:J,atlasIndex:H,sdfViewBox:Y}),M.push(j)}const{sdfViewBox:G}=j,W=p[S++],N=p[S++],k=_/O;y[T++]=W+G[0]*k,y[T++]=N+G[1]*k,y[T++]=W+G[2]*k,y[T++]=N+G[3]*k,d[U]=j.atlasIndex}),v.quads=(v.quads||0)+(Ts()-E);const x=Ts();v.sdf={};const A=u.height,C=Math.ceil(l.glyphCount/o),R=Math.pow(2,Math.ceil(Math.log2(C*a)));R>A&&(console.info(`Increasing SDF texture size ${A}->${R}`),dy(u,r,R),c.dispose()),Promise.all(M.map(L=>o0(L,l,n.gpuAccelerateSDF).then(({timing:U})=>{v.sdf[L.atlasIndex]=U}))).then(()=>{M.length&&!l.contextLost&&(l0(l),c.needsUpdate=!0),v.sdfTotal=Ts()-x,v.total=Ts()-t,e(Object.freeze({parameters:n,sdfTexture:c,sdfGlyphSize:a,sdfExponent:s,glyphBounds:y,glyphAtlasIndices:d,glyphColors:h.glyphColors,caretPositions:h.caretPositions,chunkedBounds:h.chunkedBounds,ascender:h.ascender,descender:h.descender,lineHeight:h.lineHeight,capHeight:h.capHeight,xHeight:h.xHeight,topBaseline:h.topBaseline,blockBounds:h.blockBounds,visibleBounds:h.visibleBounds,timings:h.timings}))})}),Promise.resolve().then(()=>{l.contextLost||fy(u)})}function o0({path:n,atlasIndex:e,sdfViewBox:t},{sdfGlyphSize:i,sdfCanvas:r,contextLost:s},a){if(s)return Promise.resolve({timing:-1});const{textureWidth:o,sdfExponent:l}=Ca,c=Math.max(t[2]-t[0],t[3]-t[1]),u=Math.floor(e/4),f=u%(o/i)*i,h=Math.floor(u/(o/i))*i,d=e%4;return ay(i,i,n,t,c,l,r,f,h,d,a)}function gy(n){const e=n.sdfCanvas;e.addEventListener("webglcontextlost",t=>{console.log("Context Lost",t),t.preventDefault(),n.contextLost=!0}),e.addEventListener("webglcontextrestored",t=>{console.log("Context Restored",t),n.contextLost=!1;const i=[];n.glyphsByFont.forEach(r=>{r.forEach(s=>{i.push(o0(s,n,!0))})}),Promise.all(i).then(()=>{l0(n),n.sdfTexture.needsUpdate=!0})})}function _y(n,e){for(let t in e)e.hasOwnProperty(t)&&(n[t]=e[t]);return n}let zo;function vy(n){return zo||(zo=typeof document>"u"?{}:document.createElement("a")),zo.href=n,zo.href}function l0(n){if(typeof createImageBitmap!="function"){console.info("Safari<15: applying SDF canvas workaround");const{sdfCanvas:e,sdfTexture:t}=n,{width:i,height:r}=e,s=n.sdfCanvas.getContext("webgl");let a=t.image.data;(!a||a.length!==i*r*4)&&(a=new Uint8Array(i*r*4),t.image={width:i,height:r,data:a},t.flipY=!1,t.isDataTexture=!0),s.readPixels(0,0,i,r,s.RGBA,s.UNSIGNED_BYTE,a)}}const xy=$s({name:"Typesetter",dependencies:[sy,ry,WS],init(n,e,t){return n(e,t())}}),c0=$s({name:"Typesetter",dependencies:[xy],init(n){return function(e){return new Promise(t=>{n.typeset(e,t)})}},getTransferables(n){const e=[];for(let t in n)n[t]&&n[t].buffer&&e.push(n[t].buffer);return e}});c0.onMainThread;const gp={};function by(n){let e=gp[n];return e||(e=gp[n]=new Zr(1,1,n,n).translate(.5,.5,0)),e}const My="aTroikaGlyphBounds",_p="aTroikaGlyphIndex",Sy="aTroikaGlyphColor";class yy extends Ov{constructor(){super(),this.detail=1,this.curveRadius=0,this.groups=[{start:0,count:1/0,materialIndex:0},{start:0,count:1/0,materialIndex:1}],this.boundingSphere=new Ks,this.boundingBox=new qs}computeBoundingSphere(){}computeBoundingBox(){}set detail(e){if(e!==this._detail){this._detail=e,(typeof e!="number"||e<1)&&(e=1);let t=by(e);["position","normal","uv"].forEach(i=>{this.attributes[i]=t.attributes[i].clone()}),this.setIndex(t.getIndex().clone())}}get detail(){return this._detail}set curveRadius(e){e!==this._curveRadius&&(this._curveRadius=e,this._updateBounds())}get curveRadius(){return this._curveRadius}updateGlyphs(e,t,i,r,s){this.updateAttributeData(My,e,4),this.updateAttributeData(_p,t,1),this.updateAttributeData(Sy,s,3),this._blockBounds=i,this._chunkedBounds=r,this.instanceCount=t.length,this._updateBounds()}_updateBounds(){const e=this._blockBounds;if(e){const{curveRadius:t,boundingBox:i}=this;if(t){const{PI:r,floor:s,min:a,max:o,sin:l,cos:c}=Math,u=r/2,f=r*2,h=Math.abs(t),d=e[0]/h,g=e[2]/h,m=s((d+u)/f)!==s((g+u)/f)?-h:a(l(d)*h,l(g)*h),p=s((d-u)/f)!==s((g-u)/f)?h:o(l(d)*h,l(g)*h),_=s((d+r)/f)!==s((g+r)/f)?h*2:o(h-c(d)*h,h-c(g)*h);i.min.set(m,e[1],t<0?-_:0),i.max.set(p,e[3],t<0?0:_)}else i.min.set(e[0],e[1],0),i.max.set(e[2],e[3],0);i.getBoundingSphere(this.boundingSphere)}}applyClipRect(e){let t=this.getAttribute(_p).count,i=this._chunkedBounds;if(i)for(let r=i.length;r--;){t=i[r].end;let s=i[r].rect;if(s[1]<e.w&&s[3]>e.y&&s[0]<e.z&&s[2]>e.x)break}this.instanceCount=t}updateAttributeData(e,t,i){const r=this.getAttribute(e);t?r&&r.array.length===t.length?(r.array.set(t),r.needsUpdate=!0):(this.setAttribute(e,new Ev(t,i)),delete this._maxInstanceCount,this.dispose()):r&&this.deleteAttribute(e)}}const Ty=`
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
`,Ey=`
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
`,wy=`
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
`,Ay=`
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
`;function Ry(n){const e=Sh(n,{chained:!0,extensions:{derivatives:!0},uniforms:{uTroikaSDFTexture:{value:null},uTroikaSDFTextureSize:{value:new Xe},uTroikaSDFGlyphSize:{value:0},uTroikaSDFExponent:{value:0},uTroikaTotalBounds:{value:new Dt(0,0,0,0)},uTroikaClipRect:{value:new Dt(0,0,0,0)},uTroikaEdgeOffset:{value:0},uTroikaFillOpacity:{value:1},uTroikaPositionOffset:{value:new Xe},uTroikaCurveRadius:{value:0},uTroikaBlurRadius:{value:0},uTroikaStrokeWidth:{value:0},uTroikaStrokeColor:{value:new ut},uTroikaStrokeOpacity:{value:1},uTroikaOrient:{value:new rt},uTroikaUseGlyphColors:{value:!0},uTroikaSDFDebug:{value:!1}},vertexDefs:Ty,vertexTransform:Ey,fragmentDefs:wy,fragmentColorTransform:Ay,customRewriter({vertexShader:t,fragmentShader:i}){let r=/\buniform\s+vec3\s+diffuse\b/;return r.test(i)&&(i=i.replace(r,"varying vec3 vTroikaGlyphColor").replace(/\bdiffuse\b/g,"vTroikaGlyphColor"),r.test(t)||(t=t.replace(s0,`uniform vec3 diffuse;
$&
vTroikaGlyphColor = uTroikaUseGlyphColors ? aTroikaGlyphColor / 255.0 : diffuse;
`))),{vertexShader:t,fragmentShader:i}}});return e.transparent=!0,e.forceSinglePass=!0,Object.defineProperties(e,{isTroikaTextMaterial:{value:!0},shadowSide:{get(){return this.side},set(){}}}),e}const sf=new nf({color:16777215,side:En,transparent:!0}),vp=8421504,xp=new kt,Go=new X,Xc=new X,ya=[],Cy=new X,jc="+x+y";function bp(n){return Array.isArray(n)?n[0]:n}let u0=()=>{const n=new Wn(new Zr(1,1),sf);return u0=()=>n,n},h0=()=>{const n=new Wn(new Zr(1,1,32,1),sf);return h0=()=>n,n};const Py={type:"syncstart"},Dy={type:"synccomplete"},f0=["font","fontSize","fontStyle","fontWeight","lang","letterSpacing","lineHeight","maxWidth","overflowWrap","text","direction","textAlign","textIndent","whiteSpace","anchorX","anchorY","colorRanges","sdfGlyphSize"],Uy=f0.concat("material","color","depthOffset","clipRect","curveRadius","orientation","glyphGeometryDetail");class Th extends Wn{constructor(){const e=new yy;super(e,null),this.text="",this.anchorX=0,this.anchorY=0,this.curveRadius=0,this.direction="auto",this.font=null,this.unicodeFontsURL=null,this.fontSize=.1,this.fontWeight="normal",this.fontStyle="normal",this.lang=null,this.letterSpacing=0,this.lineHeight="normal",this.maxWidth=1/0,this.overflowWrap="normal",this.textAlign="left",this.textIndent=0,this.whiteSpace="normal",this.material=null,this.color=null,this.colorRanges=null,this.outlineWidth=0,this.outlineColor=0,this.outlineOpacity=1,this.outlineBlur=0,this.outlineOffsetX=0,this.outlineOffsetY=0,this.strokeWidth=0,this.strokeColor=vp,this.strokeOpacity=1,this.fillOpacity=1,this.depthOffset=0,this.clipRect=null,this.orientation=jc,this.glyphGeometryDetail=1,this.sdfGlyphSize=null,this.gpuAccelerateSDF=!0,this.debugSDF=!1}sync(e){this._needsSync&&(this._needsSync=!1,this._isSyncing?(this._queuedSyncs||(this._queuedSyncs=[])).push(e):(this._isSyncing=!0,this.dispatchEvent(Py),my({text:this.text,font:this.font,lang:this.lang,fontSize:this.fontSize||.1,fontWeight:this.fontWeight||"normal",fontStyle:this.fontStyle||"normal",letterSpacing:this.letterSpacing||0,lineHeight:this.lineHeight||"normal",maxWidth:this.maxWidth,direction:this.direction||"auto",textAlign:this.textAlign,textIndent:this.textIndent,whiteSpace:this.whiteSpace,overflowWrap:this.overflowWrap,anchorX:this.anchorX,anchorY:this.anchorY,colorRanges:this.colorRanges,includeCaretPositions:!0,sdfGlyphSize:this.sdfGlyphSize,gpuAccelerateSDF:this.gpuAccelerateSDF,unicodeFontsURL:this.unicodeFontsURL},t=>{this._isSyncing=!1,this._textRenderInfo=t,this.geometry.updateGlyphs(t.glyphBounds,t.glyphAtlasIndices,t.blockBounds,t.chunkedBounds,t.glyphColors);const i=this._queuedSyncs;i&&(this._queuedSyncs=null,this._needsSync=!0,this.sync(()=>{i.forEach(r=>r&&r())})),this.dispatchEvent(Dy),e&&e()})))}onBeforeRender(e,t,i,r,s,a){this.sync(),s.isTroikaTextMaterial&&this._prepareForRender(s)}dispose(){this.geometry.dispose()}get textRenderInfo(){return this._textRenderInfo||null}createDerivedMaterial(e){return Ry(e)}get material(){let e=this._derivedMaterial;const t=this._baseMaterial||this._defaultMaterial||(this._defaultMaterial=sf.clone());if((!e||!e.isDerivedFrom(t))&&(e=this._derivedMaterial=this.createDerivedMaterial(t),t.addEventListener("dispose",function i(){t.removeEventListener("dispose",i),e.dispose()})),this.hasOutline()){let i=e._outlineMtl;return i||(i=e._outlineMtl=Object.create(e,{id:{value:e.id+.1}}),i.isTextOutlineMaterial=!0,i.depthWrite=!1,i.map=null,e.addEventListener("dispose",function r(){e.removeEventListener("dispose",r),i.dispose()})),[i,e]}else return e}set material(e){e&&e.isTroikaTextMaterial?(this._derivedMaterial=e,this._baseMaterial=e.baseMaterial):this._baseMaterial=e}hasOutline(){return!!(this.outlineWidth||this.outlineBlur||this.outlineOffsetX||this.outlineOffsetY)}get glyphGeometryDetail(){return this.geometry.detail}set glyphGeometryDetail(e){this.geometry.detail=e}get curveRadius(){return this.geometry.curveRadius}set curveRadius(e){this.geometry.curveRadius=e}get customDepthMaterial(){return bp(this.material).getDepthMaterial()}set customDepthMaterial(e){}get customDistanceMaterial(){return bp(this.material).getDistanceMaterial()}set customDistanceMaterial(e){}_prepareForRender(e){const t=e.isTextOutlineMaterial,i=e.uniforms,r=this.textRenderInfo;if(r){const{sdfTexture:o,blockBounds:l}=r;i.uTroikaSDFTexture.value=o,i.uTroikaSDFTextureSize.value.set(o.image.width,o.image.height),i.uTroikaSDFGlyphSize.value=r.sdfGlyphSize,i.uTroikaSDFExponent.value=r.sdfExponent,i.uTroikaTotalBounds.value.fromArray(l),i.uTroikaUseGlyphColors.value=!t&&!!r.glyphColors;let c=0,u=0,f=0,h,d,g,m=0,p=0;if(t){let{outlineWidth:v,outlineOffsetX:M,outlineOffsetY:y,outlineBlur:T,outlineOpacity:S}=this;c=this._parsePercent(v)||0,u=Math.max(0,this._parsePercent(T)||0),h=S,m=this._parsePercent(M)||0,p=this._parsePercent(y)||0}else f=Math.max(0,this._parsePercent(this.strokeWidth)||0),f&&(g=this.strokeColor,i.uTroikaStrokeColor.value.set(g??vp),d=this.strokeOpacity,d==null&&(d=1)),h=this.fillOpacity;i.uTroikaEdgeOffset.value=c,i.uTroikaPositionOffset.value.set(m,p),i.uTroikaBlurRadius.value=u,i.uTroikaStrokeWidth.value=f,i.uTroikaStrokeOpacity.value=d,i.uTroikaFillOpacity.value=h??1,i.uTroikaCurveRadius.value=this.curveRadius||0;let _=this.clipRect;if(_&&Array.isArray(_)&&_.length===4)i.uTroikaClipRect.value.fromArray(_);else{const v=(this.fontSize||.1)*100;i.uTroikaClipRect.value.set(l[0]-v,l[1]-v,l[2]+v,l[3]+v)}this.geometry.applyClipRect(i.uTroikaClipRect.value)}i.uTroikaSDFDebug.value=!!this.debugSDF,e.polygonOffset=!!this.depthOffset,e.polygonOffsetFactor=e.polygonOffsetUnits=this.depthOffset||0;const s=t?this.outlineColor||0:this.color;if(s==null)delete e.color;else{const o=e.hasOwnProperty("color")?e.color:e.color=new ut;(s!==o._input||typeof s=="object")&&o.set(o._input=s)}let a=this.orientation||jc;if(a!==e._orientation){let o=i.uTroikaOrient.value;a=a.replace(/[^-+xyz]/g,"");let l=a!==jc&&a.match(/^([-+])([xyz])([-+])([xyz])$/);if(l){let[,c,u,f,h]=l;Go.set(0,0,0)[u]=c==="-"?1:-1,Xc.set(0,0,0)[h]=f==="-"?-1:1,xp.lookAt(Cy,Go.cross(Xc),Xc),o.setFromMatrix4(xp)}else o.identity();e._orientation=a}}_parsePercent(e){if(typeof e=="string"){let t=e.match(/^(-?[\d.]+)%$/),i=t?parseFloat(t[1]):NaN;e=(isNaN(i)?0:i/100)*this.fontSize}return e}localPositionToTextCoords(e,t=new Xe){t.copy(e);const i=this.curveRadius;return i&&(t.x=Math.atan2(e.x,Math.abs(i)-Math.abs(e.z))*Math.abs(i)),t}worldPositionToTextCoords(e,t=new Xe){return Go.copy(e),this.localPositionToTextCoords(this.worldToLocal(Go),t)}raycast(e,t){const{textRenderInfo:i,curveRadius:r}=this;if(i){const s=i.blockBounds,a=r?h0():u0(),o=a.geometry,{position:l,uv:c}=o.attributes;for(let u=0;u<c.count;u++){let f=s[0]+c.getX(u)*(s[2]-s[0]);const h=s[1]+c.getY(u)*(s[3]-s[1]);let d=0;r&&(d=r-Math.cos(f/r)*r,f=Math.sin(f/r)*r),l.setXYZ(u,f,h,d)}o.boundingSphere=this.geometry.boundingSphere,o.boundingBox=this.geometry.boundingBox,a.matrixWorld=this.matrixWorld,a.material.side=this.material.side,ya.length=0,a.raycast(e,ya);for(let u=0;u<ya.length;u++)ya[u].object=this,t.push(ya[u])}}copy(e){const t=this.geometry;return super.copy(e),this.geometry=t,Uy.forEach(i=>{this[i]=e[i]}),this}clone(){return new this.constructor().copy(this)}}f0.forEach(n=>{const e="_private_"+n;Object.defineProperty(Th.prototype,n,{get(){return this[e]},set(t){t!==this[e]&&(this[e]=t,this._needsSync=!0)}})});new ut;const Mp={type:"change"},af={type:"start"},d0={type:"end"},Ho=new Ll,Sp=new or,Ly=Math.cos(70*rv.DEG2RAD),Kt=new X,Tn=2*Math.PI,yt={NONE:-1,ROTATE:0,DOLLY:1,PAN:2,TOUCH_ROTATE:3,TOUCH_PAN:4,TOUCH_DOLLY_PAN:5,TOUCH_DOLLY_ROTATE:6},Yc=1e-6;class Iy extends Gv{constructor(e,t=null){super(e,t),this.state=yt.NONE,this.target=new X,this.cursor=new X,this.minDistance=0,this.maxDistance=1/0,this.minZoom=0,this.maxZoom=1/0,this.minTargetRadius=0,this.maxTargetRadius=1/0,this.minPolarAngle=0,this.maxPolarAngle=Math.PI,this.minAzimuthAngle=-1/0,this.maxAzimuthAngle=1/0,this.enableDamping=!1,this.dampingFactor=.05,this.enableZoom=!0,this.zoomSpeed=1,this.enableRotate=!0,this.rotateSpeed=1,this.keyRotateSpeed=1,this.enablePan=!0,this.panSpeed=1,this.screenSpacePanning=!0,this.keyPanSpeed=7,this.zoomToCursor=!1,this.autoRotate=!1,this.autoRotateSpeed=2,this.keys={LEFT:"ArrowLeft",UP:"ArrowUp",RIGHT:"ArrowRight",BOTTOM:"ArrowDown"},this.mouseButtons={LEFT:Ds.ROTATE,MIDDLE:Ds.DOLLY,RIGHT:Ds.PAN},this.touches={ONE:As.ROTATE,TWO:As.DOLLY_PAN},this.target0=this.target.clone(),this.position0=this.object.position.clone(),this.zoom0=this.object.zoom,this._cursorStyle="auto",this._domElementKeyEvents=null,this._lastPosition=new X,this._lastQuaternion=new _r,this._lastTargetPosition=new X,this._quat=new _r().setFromUnitVectors(e.up,new X(0,1,0)),this._quatInverse=this._quat.clone().invert(),this._spherical=new Fd,this._sphericalDelta=new Fd,this._scale=1,this._panOffset=new X,this._rotateStart=new Xe,this._rotateEnd=new Xe,this._rotateDelta=new Xe,this._panStart=new Xe,this._panEnd=new Xe,this._panDelta=new Xe,this._dollyStart=new Xe,this._dollyEnd=new Xe,this._dollyDelta=new Xe,this._dollyDirection=new X,this._mouse=new Xe,this._performCursorZoom=!1,this._pointers=[],this._pointerPositions={},this._controlActive=!1,this._onPointerMove=Ny.bind(this),this._onPointerDown=Fy.bind(this),this._onPointerUp=Oy.bind(this),this._onContextMenu=Wy.bind(this),this._onMouseWheel=zy.bind(this),this._onKeyDown=Gy.bind(this),this._onTouchStart=Hy.bind(this),this._onTouchMove=Vy.bind(this),this._onMouseDown=By.bind(this),this._onMouseMove=ky.bind(this),this._interceptControlDown=Xy.bind(this),this._interceptControlUp=jy.bind(this),this.domElement!==null&&this.connect(this.domElement),this.update()}set cursorStyle(e){this._cursorStyle=e,e==="grab"?this.domElement.style.cursor="grab":this.domElement.style.cursor="auto"}get cursorStyle(){return this._cursorStyle}connect(e){super.connect(e),this.domElement.addEventListener("pointerdown",this._onPointerDown),this.domElement.addEventListener("pointercancel",this._onPointerUp),this.domElement.addEventListener("contextmenu",this._onContextMenu),this.domElement.addEventListener("wheel",this._onMouseWheel,{passive:!1}),this.domElement.getRootNode().addEventListener("keydown",this._interceptControlDown,{passive:!0,capture:!0}),this.domElement.style.touchAction="none"}disconnect(){this.domElement.removeEventListener("pointerdown",this._onPointerDown),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.domElement.removeEventListener("pointercancel",this._onPointerUp),this.domElement.removeEventListener("wheel",this._onMouseWheel),this.domElement.removeEventListener("contextmenu",this._onContextMenu),this.stopListenToKeyEvents(),this.domElement.getRootNode().removeEventListener("keydown",this._interceptControlDown,{capture:!0}),this.domElement.style.touchAction=""}dispose(){this.disconnect()}getPolarAngle(){return this._spherical.phi}getAzimuthalAngle(){return this._spherical.theta}getDistance(){return this.object.position.distanceTo(this.target)}listenToKeyEvents(e){e.addEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=e}stopListenToKeyEvents(){this._domElementKeyEvents!==null&&(this._domElementKeyEvents.removeEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=null)}saveState(){this.target0.copy(this.target),this.position0.copy(this.object.position),this.zoom0=this.object.zoom}reset(){this.target.copy(this.target0),this.object.position.copy(this.position0),this.object.zoom=this.zoom0,this.object.updateProjectionMatrix(),this.dispatchEvent(Mp),this.update(),this.state=yt.NONE}pan(e,t){this._pan(e,t),this.update()}dollyIn(e){this._dollyIn(e),this.update()}dollyOut(e){this._dollyOut(e),this.update()}rotateLeft(e){this._rotateLeft(e),this.update()}rotateUp(e){this._rotateUp(e),this.update()}update(e=null){const t=this.object.position;Kt.copy(t).sub(this.target),Kt.applyQuaternion(this._quat),this._spherical.setFromVector3(Kt),this.autoRotate&&this.state===yt.NONE&&this._rotateLeft(this._getAutoRotationAngle(e)),this.enableDamping?(this._spherical.theta+=this._sphericalDelta.theta*this.dampingFactor,this._spherical.phi+=this._sphericalDelta.phi*this.dampingFactor):(this._spherical.theta+=this._sphericalDelta.theta,this._spherical.phi+=this._sphericalDelta.phi);let i=this.minAzimuthAngle,r=this.maxAzimuthAngle;isFinite(i)&&isFinite(r)&&(i<-Math.PI?i+=Tn:i>Math.PI&&(i-=Tn),r<-Math.PI?r+=Tn:r>Math.PI&&(r-=Tn),i<=r?this._spherical.theta=Math.max(i,Math.min(r,this._spherical.theta)):this._spherical.theta=this._spherical.theta>(i+r)/2?Math.max(i,this._spherical.theta):Math.min(r,this._spherical.theta)),this._spherical.phi=Math.max(this.minPolarAngle,Math.min(this.maxPolarAngle,this._spherical.phi)),this._spherical.makeSafe(),this.enableDamping===!0?this.target.addScaledVector(this._panOffset,this.dampingFactor):this.target.add(this._panOffset),this.target.sub(this.cursor),this.target.clampLength(this.minTargetRadius,this.maxTargetRadius),this.target.add(this.cursor);let s=!1;if(this.zoomToCursor&&this._performCursorZoom||this.object.isOrthographicCamera)this._spherical.radius=this._clampDistance(this._spherical.radius);else{const a=this._spherical.radius;this._spherical.radius=this._clampDistance(this._spherical.radius*this._scale),s=a!=this._spherical.radius}if(Kt.setFromSpherical(this._spherical),Kt.applyQuaternion(this._quatInverse),t.copy(this.target).add(Kt),this.object.lookAt(this.target),this.enableDamping===!0?(this._sphericalDelta.theta*=1-this.dampingFactor,this._sphericalDelta.phi*=1-this.dampingFactor,this._panOffset.multiplyScalar(1-this.dampingFactor)):(this._sphericalDelta.set(0,0,0),this._panOffset.set(0,0,0)),this.zoomToCursor&&this._performCursorZoom){let a=null;if(this.object.isPerspectiveCamera){const o=Kt.length();a=this._clampDistance(o*this._scale);const l=o-a;this.object.position.addScaledVector(this._dollyDirection,l),this.object.updateMatrixWorld(),s=!!l}else if(this.object.isOrthographicCamera){const o=new X(this._mouse.x,this._mouse.y,0);o.unproject(this.object);const l=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),this.object.updateProjectionMatrix(),s=l!==this.object.zoom;const c=new X(this._mouse.x,this._mouse.y,0);c.unproject(this.object),this.object.position.sub(c).add(o),this.object.updateMatrixWorld(),a=Kt.length()}else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - zoom to cursor disabled."),this.zoomToCursor=!1;a!==null&&(this.screenSpacePanning?this.target.set(0,0,-1).transformDirection(this.object.matrix).multiplyScalar(a).add(this.object.position):(Ho.origin.copy(this.object.position),Ho.direction.set(0,0,-1).transformDirection(this.object.matrix),Math.abs(this.object.up.dot(Ho.direction))<Ly?this.object.lookAt(this.target):(Sp.setFromNormalAndCoplanarPoint(this.object.up,this.target),Ho.intersectPlane(Sp,this.target))))}else if(this.object.isOrthographicCamera){const a=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),a!==this.object.zoom&&(this.object.updateProjectionMatrix(),s=!0)}return this._scale=1,this._performCursorZoom=!1,s||this._lastPosition.distanceToSquared(this.object.position)>Yc||8*(1-this._lastQuaternion.dot(this.object.quaternion))>Yc||this._lastTargetPosition.distanceToSquared(this.target)>Yc?(this.dispatchEvent(Mp),this._lastPosition.copy(this.object.position),this._lastQuaternion.copy(this.object.quaternion),this._lastTargetPosition.copy(this.target),!0):!1}_getAutoRotationAngle(e){return e!==null?Tn/60*this.autoRotateSpeed*e:Tn/60/60*this.autoRotateSpeed}_getZoomScale(e){const t=Math.abs(e*.01);return Math.pow(.95,this.zoomSpeed*t)}_rotateLeft(e){this._sphericalDelta.theta-=e}_rotateUp(e){this._sphericalDelta.phi-=e}_panLeft(e,t){Kt.setFromMatrixColumn(t,0),Kt.multiplyScalar(-e),this._panOffset.add(Kt)}_panUp(e,t){this.screenSpacePanning===!0?Kt.setFromMatrixColumn(t,1):(Kt.setFromMatrixColumn(t,0),Kt.crossVectors(this.object.up,Kt)),Kt.multiplyScalar(e),this._panOffset.add(Kt)}_pan(e,t){const i=this.domElement;if(this.object.isPerspectiveCamera){const r=this.object.position;Kt.copy(r).sub(this.target);let s=Kt.length();s*=Math.tan(this.object.fov/2*Math.PI/180),this._panLeft(2*e*s/i.clientHeight,this.object.matrix),this._panUp(2*t*s/i.clientHeight,this.object.matrix)}else this.object.isOrthographicCamera?(this._panLeft(e*(this.object.right-this.object.left)/this.object.zoom/i.clientWidth,this.object.matrix),this._panUp(t*(this.object.top-this.object.bottom)/this.object.zoom/i.clientHeight,this.object.matrix)):(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled."),this.enablePan=!1)}_dollyOut(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale/=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_dollyIn(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale*=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_updateZoomParameters(e,t){if(!this.zoomToCursor)return;this._performCursorZoom=!0;const i=this.domElement.getBoundingClientRect(),r=e-i.left,s=t-i.top,a=i.width,o=i.height;this._mouse.x=r/a*2-1,this._mouse.y=-(s/o)*2+1,this._dollyDirection.set(this._mouse.x,this._mouse.y,1).unproject(this.object).sub(this.object.position).normalize()}_clampDistance(e){return Math.max(this.minDistance,Math.min(this.maxDistance,e))}_handleMouseDownRotate(e){this._rotateStart.set(e.clientX,e.clientY)}_handleMouseDownDolly(e){this._updateZoomParameters(e.clientX,e.clientX),this._dollyStart.set(e.clientX,e.clientY)}_handleMouseDownPan(e){this._panStart.set(e.clientX,e.clientY)}_handleMouseMoveRotate(e){this._rotateEnd.set(e.clientX,e.clientY),this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(Tn*this._rotateDelta.x/t.clientHeight),this._rotateUp(Tn*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd),this.update()}_handleMouseMoveDolly(e){this._dollyEnd.set(e.clientX,e.clientY),this._dollyDelta.subVectors(this._dollyEnd,this._dollyStart),this._dollyDelta.y>0?this._dollyOut(this._getZoomScale(this._dollyDelta.y)):this._dollyDelta.y<0&&this._dollyIn(this._getZoomScale(this._dollyDelta.y)),this._dollyStart.copy(this._dollyEnd),this.update()}_handleMouseMovePan(e){this._panEnd.set(e.clientX,e.clientY),this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd),this.update()}_handleMouseWheel(e){this._updateZoomParameters(e.clientX,e.clientY),e.deltaY<0?this._dollyIn(this._getZoomScale(e.deltaY)):e.deltaY>0&&this._dollyOut(this._getZoomScale(e.deltaY)),this.update()}_handleKeyDown(e){let t=!1;switch(e.code){case this.keys.UP:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(Tn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,this.keyPanSpeed),t=!0;break;case this.keys.BOTTOM:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(-Tn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,-this.keyPanSpeed),t=!0;break;case this.keys.LEFT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(Tn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(this.keyPanSpeed,0),t=!0;break;case this.keys.RIGHT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(-Tn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(-this.keyPanSpeed,0),t=!0;break}t&&(e.preventDefault(),this.update())}_handleTouchStartRotate(e){if(this._pointers.length===1)this._rotateStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),i=.5*(e.pageX+t.x),r=.5*(e.pageY+t.y);this._rotateStart.set(i,r)}}_handleTouchStartPan(e){if(this._pointers.length===1)this._panStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),i=.5*(e.pageX+t.x),r=.5*(e.pageY+t.y);this._panStart.set(i,r)}}_handleTouchStartDolly(e){const t=this._getSecondPointerPosition(e),i=e.pageX-t.x,r=e.pageY-t.y,s=Math.sqrt(i*i+r*r);this._dollyStart.set(0,s)}_handleTouchStartDollyPan(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enablePan&&this._handleTouchStartPan(e)}_handleTouchStartDollyRotate(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enableRotate&&this._handleTouchStartRotate(e)}_handleTouchMoveRotate(e){if(this._pointers.length==1)this._rotateEnd.set(e.pageX,e.pageY);else{const i=this._getSecondPointerPosition(e),r=.5*(e.pageX+i.x),s=.5*(e.pageY+i.y);this._rotateEnd.set(r,s)}this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(Tn*this._rotateDelta.x/t.clientHeight),this._rotateUp(Tn*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd)}_handleTouchMovePan(e){if(this._pointers.length===1)this._panEnd.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),i=.5*(e.pageX+t.x),r=.5*(e.pageY+t.y);this._panEnd.set(i,r)}this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd)}_handleTouchMoveDolly(e){const t=this._getSecondPointerPosition(e),i=e.pageX-t.x,r=e.pageY-t.y,s=Math.sqrt(i*i+r*r);this._dollyEnd.set(0,s),this._dollyDelta.set(0,Math.pow(this._dollyEnd.y/this._dollyStart.y,this.zoomSpeed)),this._dollyOut(this._dollyDelta.y),this._dollyStart.copy(this._dollyEnd);const a=(e.pageX+t.x)*.5,o=(e.pageY+t.y)*.5;this._updateZoomParameters(a,o)}_handleTouchMoveDollyPan(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enablePan&&this._handleTouchMovePan(e)}_handleTouchMoveDollyRotate(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enableRotate&&this._handleTouchMoveRotate(e)}_addPointer(e){this._pointers.push(e.pointerId)}_removePointer(e){delete this._pointerPositions[e.pointerId];for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId){this._pointers.splice(t,1);return}}_isTrackingPointer(e){for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId)return!0;return!1}_trackPointer(e){let t=this._pointerPositions[e.pointerId];t===void 0&&(t=new Xe,this._pointerPositions[e.pointerId]=t),t.set(e.pageX,e.pageY)}_getSecondPointerPosition(e){const t=e.pointerId===this._pointers[0]?this._pointers[1]:this._pointers[0];return this._pointerPositions[t]}_customWheelEvent(e){const t=e.deltaMode,i={clientX:e.clientX,clientY:e.clientY,deltaY:e.deltaY};switch(t){case 1:i.deltaY*=16;break;case 2:i.deltaY*=100;break}return e.ctrlKey&&!this._controlActive&&(i.deltaY*=10),i}}function Fy(n){this.enabled!==!1&&(this._pointers.length===0&&(this.domElement.setPointerCapture(n.pointerId),this.domElement.ownerDocument.addEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.addEventListener("pointerup",this._onPointerUp)),!this._isTrackingPointer(n)&&(this._addPointer(n),n.pointerType==="touch"?this._onTouchStart(n):this._onMouseDown(n),this._cursorStyle==="grab"&&(this.domElement.style.cursor="grabbing")))}function Ny(n){this.enabled!==!1&&(n.pointerType==="touch"?this._onTouchMove(n):this._onMouseMove(n))}function Oy(n){switch(this._removePointer(n),this._pointers.length){case 0:this.domElement.releasePointerCapture(n.pointerId),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.dispatchEvent(d0),this.state=yt.NONE,this._cursorStyle==="grab"&&(this.domElement.style.cursor="grab");break;case 1:const e=this._pointers[0],t=this._pointerPositions[e];this._onTouchStart({pointerId:e,pageX:t.x,pageY:t.y});break}}function By(n){let e;switch(n.button){case 0:e=this.mouseButtons.LEFT;break;case 1:e=this.mouseButtons.MIDDLE;break;case 2:e=this.mouseButtons.RIGHT;break;default:e=-1}switch(e){case Ds.DOLLY:if(this.enableZoom===!1)return;this._handleMouseDownDolly(n),this.state=yt.DOLLY;break;case Ds.ROTATE:if(n.ctrlKey||n.metaKey||n.shiftKey){if(this.enablePan===!1)return;this._handleMouseDownPan(n),this.state=yt.PAN}else{if(this.enableRotate===!1)return;this._handleMouseDownRotate(n),this.state=yt.ROTATE}break;case Ds.PAN:if(n.ctrlKey||n.metaKey||n.shiftKey){if(this.enableRotate===!1)return;this._handleMouseDownRotate(n),this.state=yt.ROTATE}else{if(this.enablePan===!1)return;this._handleMouseDownPan(n),this.state=yt.PAN}break;default:this.state=yt.NONE}this.state!==yt.NONE&&this.dispatchEvent(af)}function ky(n){switch(this.state){case yt.ROTATE:if(this.enableRotate===!1)return;this._handleMouseMoveRotate(n);break;case yt.DOLLY:if(this.enableZoom===!1)return;this._handleMouseMoveDolly(n);break;case yt.PAN:if(this.enablePan===!1)return;this._handleMouseMovePan(n);break}}function zy(n){this.enabled===!1||this.enableZoom===!1||this.state!==yt.NONE||(n.preventDefault(),this.dispatchEvent(af),this._handleMouseWheel(this._customWheelEvent(n)),this.dispatchEvent(d0))}function Gy(n){this.enabled!==!1&&this._handleKeyDown(n)}function Hy(n){switch(this._trackPointer(n),this._pointers.length){case 1:switch(this.touches.ONE){case As.ROTATE:if(this.enableRotate===!1)return;this._handleTouchStartRotate(n),this.state=yt.TOUCH_ROTATE;break;case As.PAN:if(this.enablePan===!1)return;this._handleTouchStartPan(n),this.state=yt.TOUCH_PAN;break;default:this.state=yt.NONE}break;case 2:switch(this.touches.TWO){case As.DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchStartDollyPan(n),this.state=yt.TOUCH_DOLLY_PAN;break;case As.DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchStartDollyRotate(n),this.state=yt.TOUCH_DOLLY_ROTATE;break;default:this.state=yt.NONE}break;default:this.state=yt.NONE}this.state!==yt.NONE&&this.dispatchEvent(af)}function Vy(n){switch(this._trackPointer(n),this.state){case yt.TOUCH_ROTATE:if(this.enableRotate===!1)return;this._handleTouchMoveRotate(n),this.update();break;case yt.TOUCH_PAN:if(this.enablePan===!1)return;this._handleTouchMovePan(n),this.update();break;case yt.TOUCH_DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchMoveDollyPan(n),this.update();break;case yt.TOUCH_DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchMoveDollyRotate(n),this.update();break;default:this.state=yt.NONE}}function Wy(n){this.enabled!==!1&&n.preventDefault()}function Xy(n){n.key==="Control"&&(this._controlActive=!0,this.domElement.getRootNode().addEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function jy(n){n.key==="Control"&&(this._controlActive=!1,this.domElement.getRootNode().removeEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function Oi(n){if(n===void 0)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return n}function p0(n,e){n.prototype=Object.create(e.prototype),n.prototype.constructor=n,n.__proto__=e}/*!
 * GSAP 3.15.0
 * https://gsap.com
 *
 * @license Copyright 2008-2026, GreenSock. All rights reserved.
 * Subject to the terms at https://gsap.com/standard-license
 * @author: Jack Doyle, jack@greensock.com
*/var Vn={autoSleep:120,force3D:"auto",nullTargetWarn:1,units:{lineHeight:""}},ka={duration:.5,overwrite:!1,delay:0},of,un,Lt,Jn=1e8,Rt=1/Jn,Eh=Math.PI*2,Yy=Eh/4,qy=0,m0=Math.sqrt,Ky=Math.cos,Zy=Math.sin,on=function(e){return typeof e=="string"},Gt=function(e){return typeof e=="function"},Xi=function(e){return typeof e=="number"},lf=function(e){return typeof e>"u"},Ci=function(e){return typeof e=="object"},An=function(e){return e!==!1},cf=function(){return typeof window<"u"},Vo=function(e){return Gt(e)||on(e)},g0=typeof ArrayBuffer=="function"&&ArrayBuffer.isView||function(){},gn=Array.isArray,$y=/random\([^)]+\)/g,Jy=/,\s*/g,yp=/(?:-?\.?\d|\.)+/gi,_0=/[-+=.]*\d+[.e\-+]*\d*[e\-+]*\d*/g,Cs=/[-+=.]*\d+[.e-]*\d*[a-z%]*/g,qc=/[-+=.]*\d+\.?\d*(?:e-|e\+)?\d*/gi,v0=/[+-]=-?[.\d]+/,Qy=/[^,'"\[\]\s]+/gi,eT=/^[+\-=e\s\d]*\d+[.\d]*([a-z]*|%)\s*$/i,Ot,vi,wh,uf,Xn={},vl={},x0,b0=function(e){return(vl=Hs(e,Xn))&&Dn},hf=function(e,t){return console.warn("Invalid property",e,"set to",t,"Missing plugin? gsap.registerPlugin()")},za=function(e,t){return!t&&console.warn(e)},M0=function(e,t){return e&&(Xn[e]=t)&&vl&&(vl[e]=t)||Xn},Ga=function(){return 0},tT={suppressEvents:!0,isStart:!0,kill:!1},nl={suppressEvents:!0,kill:!1},nT={suppressEvents:!0},ff={},pr=[],Ah={},S0,Bn={},Kc={},Tp=30,il=[],df="",pf=function(e){var t=e[0],i,r;if(Ci(t)||Gt(t)||(e=[e]),!(i=(t._gsap||{}).harness)){for(r=il.length;r--&&!il[r].targetTest(t););i=il[r]}for(r=e.length;r--;)e[r]&&(e[r]._gsap||(e[r]._gsap=new W0(e[r],i)))||e.splice(r,1);return e},Gr=function(e){return e._gsap||pf(Qn(e))[0]._gsap},y0=function(e,t,i){return(i=e[t])&&Gt(i)?e[t]():lf(i)&&e.getAttribute&&e.getAttribute(t)||i},Rn=function(e,t){return(e=e.split(",")).forEach(t)||e},Vt=function(e){return Math.round(e*1e5)/1e5||0},Nt=function(e){return Math.round(e*1e7)/1e7||0},Ls=function(e,t){var i=t.charAt(0),r=parseFloat(t.substr(2));return e=parseFloat(e),i==="+"?e+r:i==="-"?e-r:i==="*"?e*r:e/r},iT=function(e,t){for(var i=t.length,r=0;e.indexOf(t[r])<0&&++r<i;);return r<i},xl=function(){var e=pr.length,t=pr.slice(0),i,r;for(Ah={},pr.length=0,i=0;i<e;i++)r=t[i],r&&r._lazy&&(r.render(r._lazy[0],r._lazy[1],!0)._lazy=0)},mf=function(e){return!!(e._initted||e._startAt||e.add)},T0=function(e,t,i,r){pr.length&&!un&&xl(),e.render(t,i,!!(un&&t<0&&mf(e))),pr.length&&!un&&xl()},E0=function(e){var t=parseFloat(e);return(t||t===0)&&(e+"").match(Qy).length<2?t:on(e)?e.trim():e},w0=function(e){return e},jn=function(e,t){for(var i in t)i in e||(e[i]=t[i]);return e},rT=function(e){return function(t,i){for(var r in i)r in t||r==="duration"&&e||r==="ease"||(t[r]=i[r])}},Hs=function(e,t){for(var i in t)e[i]=t[i];return e},Ep=function n(e,t){for(var i in t)i!=="__proto__"&&i!=="constructor"&&i!=="prototype"&&(e[i]=Ci(t[i])?n(e[i]||(e[i]={}),t[i]):t[i]);return e},bl=function(e,t){var i={},r;for(r in e)r in t||(i[r]=e[r]);return i},Ia=function(e){var t=e.parent||Ot,i=e.keyframes?rT(gn(e.keyframes)):jn;if(An(e.inherit))for(;t;)i(e,t.vars.defaults),t=t.parent||t._dp;return e},sT=function(e,t){for(var i=e.length,r=i===t.length;r&&i--&&e[i]===t[i];);return i<0},A0=function(e,t,i,r,s){var a=e[r],o;if(s)for(o=t[s];a&&a[s]>o;)a=a._prev;return a?(t._next=a._next,a._next=t):(t._next=e[i],e[i]=t),t._next?t._next._prev=t:e[r]=t,t._prev=a,t.parent=t._dp=e,t},Ol=function(e,t,i,r){i===void 0&&(i="_first"),r===void 0&&(r="_last");var s=t._prev,a=t._next;s?s._next=a:e[i]===t&&(e[i]=a),a?a._prev=s:e[r]===t&&(e[r]=s),t._next=t._prev=t.parent=null},vr=function(e,t){e.parent&&(!t||e.parent.autoRemoveChildren)&&e.parent.remove&&e.parent.remove(e),e._act=0},Hr=function(e,t){if(e&&(!t||t._end>e._dur||t._start<0))for(var i=e;i;)i._dirty=1,i=i.parent;return e},aT=function(e){for(var t=e.parent;t&&t.parent;)t._dirty=1,t.totalDuration(),t=t.parent;return e},Rh=function(e,t,i,r){return e._startAt&&(un?e._startAt.revert(nl):e.vars.immediateRender&&!e.vars.autoRevert||e._startAt.render(t,!0,r))},oT=function n(e){return!e||e._ts&&n(e.parent)},wp=function(e){return e._repeat?Vs(e._tTime,e=e.duration()+e._rDelay)*e:0},Vs=function(e,t){var i=Math.floor(e=Nt(e/t));return e&&i===e?i-1:i},Ml=function(e,t){return(e-t._start)*t._ts+(t._ts>=0?0:t._dirty?t.totalDuration():t._tDur)},Bl=function(e){return e._end=Nt(e._start+(e._tDur/Math.abs(e._ts||e._rts||Rt)||0))},kl=function(e,t){var i=e._dp;return i&&i.smoothChildTiming&&e._ts&&(e._start=Nt(i._time-(e._ts>0?t/e._ts:((e._dirty?e.totalDuration():e._tDur)-t)/-e._ts)),Bl(e),i._dirty||Hr(i,e)),e},R0=function(e,t){var i;if((t._time||!t._dur&&t._initted||t._start<e._time&&(t._dur||!t.add))&&(i=Ml(e.rawTime(),t),(!t._dur||$a(0,t.totalDuration(),i)-t._tTime>Rt)&&t.render(i,!0)),Hr(e,t)._dp&&e._initted&&e._time>=e._dur&&e._ts){if(e._dur<e.duration())for(i=e;i._dp;)i.rawTime()>=0&&i.totalTime(i._tTime),i=i._dp;e._zTime=-Rt}},Si=function(e,t,i,r){return t.parent&&vr(t),t._start=Nt((Xi(i)?i:i||e!==Ot?Zn(e,i,t):e._time)+t._delay),t._end=Nt(t._start+(t.totalDuration()/Math.abs(t.timeScale())||0)),A0(e,t,"_first","_last",e._sort?"_start":0),Ch(t)||(e._recent=t),r||R0(e,t),e._ts<0&&kl(e,e._tTime),e},C0=function(e,t){return(Xn.ScrollTrigger||hf("scrollTrigger",t))&&Xn.ScrollTrigger.create(t,e)},P0=function(e,t,i,r,s){if(_f(e,t,s),!e._initted)return 1;if(!i&&e._pt&&!un&&(e._dur&&e.vars.lazy!==!1||!e._dur&&e.vars.lazy)&&S0!==zn.frame)return pr.push(e),e._lazy=[s,r],1},lT=function n(e){var t=e.parent;return t&&t._ts&&t._initted&&!t._lock&&(t.rawTime()<0||n(t))},Ch=function(e){var t=e.data;return t==="isFromStart"||t==="isStart"},cT=function(e,t,i,r){var s=e.ratio,a=t<0||!t&&(!e._start&&lT(e)&&!(!e._initted&&Ch(e))||(e._ts<0||e._dp._ts<0)&&!Ch(e))?0:1,o=e._rDelay,l=0,c,u,f;if(o&&e._repeat&&(l=$a(0,e._tDur,t),u=Vs(l,o),e._yoyo&&u&1&&(a=1-a),u!==Vs(e._tTime,o)&&(s=1-a,e.vars.repeatRefresh&&e._initted&&e.invalidate())),a!==s||un||r||e._zTime===Rt||!t&&e._zTime){if(!e._initted&&P0(e,t,r,i,l))return;for(f=e._zTime,e._zTime=t||(i?Rt:0),i||(i=t&&!f),e.ratio=a,e._from&&(a=1-a),e._time=0,e._tTime=l,c=e._pt;c;)c.r(a,c.d),c=c._next;t<0&&Rh(e,t,i,!0),e._onUpdate&&!i&&Gn(e,"onUpdate"),l&&e._repeat&&!i&&e.parent&&Gn(e,"onRepeat"),(t>=e._tDur||t<0)&&e.ratio===a&&(a&&vr(e,1),!i&&!un&&(Gn(e,a?"onComplete":"onReverseComplete",!0),e._prom&&e._prom()))}else e._zTime||(e._zTime=t)},uT=function(e,t,i){var r;if(i>t)for(r=e._first;r&&r._start<=i;){if(r.data==="isPause"&&r._start>t)return r;r=r._next}else for(r=e._last;r&&r._start>=i;){if(r.data==="isPause"&&r._start<t)return r;r=r._prev}},Ws=function(e,t,i,r){var s=e._repeat,a=Nt(t)||0,o=e._tTime/e._tDur;return o&&!r&&(e._time*=a/e._dur),e._dur=a,e._tDur=s?s<0?1e10:Nt(a*(s+1)+e._rDelay*s):a,o>0&&!r&&kl(e,e._tTime=e._tDur*o),e.parent&&Bl(e),i||Hr(e.parent,e),e},Ap=function(e){return e instanceof wn?Hr(e):Ws(e,e._dur)},hT={_start:0,endTime:Ga,totalDuration:Ga},Zn=function n(e,t,i){var r=e.labels,s=e._recent||hT,a=e.duration()>=Jn?s.endTime(!1):e._dur,o,l,c;return on(t)&&(isNaN(t)||t in r)?(l=t.charAt(0),c=t.substr(-1)==="%",o=t.indexOf("="),l==="<"||l===">"?(o>=0&&(t=t.replace(/=/,"")),(l==="<"?s._start:s.endTime(s._repeat>=0))+(parseFloat(t.substr(1))||0)*(c?(o<0?s:i).totalDuration()/100:1)):o<0?(t in r||(r[t]=a),r[t]):(l=parseFloat(t.charAt(o-1)+t.substr(o+1)),c&&i&&(l=l/100*(gn(i)?i[0]:i).totalDuration()),o>1?n(e,t.substr(0,o-1),i)+l:a+l)):t==null?a:+t},Fa=function(e,t,i){var r=Xi(t[1]),s=(r?2:1)+(e<2?0:1),a=t[s],o,l;if(r&&(a.duration=t[1]),a.parent=i,e){for(o=a,l=i;l&&!("immediateRender"in o);)o=l.vars.defaults||{},l=An(l.vars.inherit)&&l.parent;a.immediateRender=An(o.immediateRender),e<2?a.runBackwards=1:a.startAt=t[s-1]}return new Xt(t[0],a,t[s+1])},yr=function(e,t){return e||e===0?t(e):t},$a=function(e,t,i){return i<e?e:i>t?t:i},pn=function(e,t){return!on(e)||!(t=eT.exec(e))?"":t[1]},fT=function(e,t,i){return yr(i,function(r){return $a(e,t,r)})},Ph=[].slice,D0=function(e,t){return e&&Ci(e)&&"length"in e&&(!t&&!e.length||e.length-1 in e&&Ci(e[0]))&&!e.nodeType&&e!==vi},dT=function(e,t,i){return i===void 0&&(i=[]),e.forEach(function(r){var s;return on(r)&&!t||D0(r,1)?(s=i).push.apply(s,Qn(r)):i.push(r)})||i},Qn=function(e,t,i){return Lt&&!t&&Lt.selector?Lt.selector(e):on(e)&&!i&&(wh||!Xs())?Ph.call((t||uf).querySelectorAll(e),0):gn(e)?dT(e,i):D0(e)?Ph.call(e,0):e?[e]:[]},Dh=function(e){return e=Qn(e)[0]||za("Invalid scope")||{},function(t){var i=e.current||e.nativeElement||e;return Qn(t,i.querySelectorAll?i:i===e?za("Invalid scope")||uf.createElement("div"):e)}},U0=function(e){return e.sort(function(){return .5-Math.random()})},L0=function(e){if(Gt(e))return e;var t=Ci(e)?e:{each:e},i=Vr(t.ease),r=t.from||0,s=parseFloat(t.base)||0,a={},o=r>0&&r<1,l=isNaN(r)||o,c=t.axis,u=r,f=r;return on(r)?u=f={center:.5,edges:.5,end:1}[r]||0:!o&&l&&(u=r[0],f=r[1]),function(h,d,g){var m=(g||t).length,p=a[m],_,v,M,y,T,S,E,b,x;if(!p){if(x=t.grid==="auto"?0:(t.grid||[1,Jn])[1],!x){for(E=-Jn;E<(E=g[x++].getBoundingClientRect().left)&&x<m;);x<m&&x--}for(p=a[m]=[],_=l?Math.min(x,m)*u-.5:r%x,v=x===Jn?0:l?m*f/x-.5:r/x|0,E=0,b=Jn,S=0;S<m;S++)M=S%x-_,y=v-(S/x|0),p[S]=T=c?Math.abs(c==="y"?y:M):m0(M*M+y*y),T>E&&(E=T),T<b&&(b=T);r==="random"&&U0(p),p.max=E-b,p.min=b,p.v=m=(parseFloat(t.amount)||parseFloat(t.each)*(x>m?m-1:c?c==="y"?m/x:x:Math.max(x,m/x))||0)*(r==="edges"?-1:1),p.b=m<0?s-m:s,p.u=pn(t.amount||t.each)||0,i=i&&m<0?wT(i):i}return m=(p[h]-p.min)/p.max||0,Nt(p.b+(i?i(m):m)*p.v)+p.u}},Uh=function(e){var t=Math.pow(10,((e+"").split(".")[1]||"").length);return function(i){var r=Nt(Math.round(parseFloat(i)/e)*e*t);return(r-r%1)/t+(Xi(i)?0:pn(i))}},I0=function(e,t){var i=gn(e),r,s;return!i&&Ci(e)&&(r=i=e.radius||Jn,e.values?(e=Qn(e.values),(s=!Xi(e[0]))&&(r*=r)):e=Uh(e.increment)),yr(t,i?Gt(e)?function(a){return s=e(a),Math.abs(s-a)<=r?s:a}:function(a){for(var o=parseFloat(s?a.x:a),l=parseFloat(s?a.y:0),c=Jn,u=0,f=e.length,h,d;f--;)s?(h=e[f].x-o,d=e[f].y-l,h=h*h+d*d):h=Math.abs(e[f]-o),h<c&&(c=h,u=f);return u=!r||c<=r?e[u]:a,s||u===a||Xi(a)?u:u+pn(a)}:Uh(e))},F0=function(e,t,i,r){return yr(gn(e)?!t:i===!0?!!(i=0):!r,function(){return gn(e)?e[~~(Math.random()*e.length)]:(i=i||1e-5)&&(r=i<1?Math.pow(10,(i+"").length-2):1)&&Math.floor(Math.round((e-i/2+Math.random()*(t-e+i*.99))/i)*i*r)/r})},pT=function(){for(var e=arguments.length,t=new Array(e),i=0;i<e;i++)t[i]=arguments[i];return function(r){return t.reduce(function(s,a){return a(s)},r)}},mT=function(e,t){return function(i){return e(parseFloat(i))+(t||pn(i))}},gT=function(e,t,i){return O0(e,t,0,1,i)},N0=function(e,t,i){return yr(i,function(r){return e[~~t(r)]})},_T=function n(e,t,i){var r=t-e;return gn(e)?N0(e,n(0,e.length),t):yr(i,function(s){return(r+(s-e)%r)%r+e})},vT=function n(e,t,i){var r=t-e,s=r*2;return gn(e)?N0(e,n(0,e.length-1),t):yr(i,function(a){return a=(s+(a-e)%s)%s||0,e+(a>r?s-a:a)})},Ha=function(e){return e.replace($y,function(t){var i=t.indexOf("[")+1,r=t.substring(i||7,i?t.indexOf("]"):t.length-1).split(Jy);return F0(i?r:+r[0],i?0:+r[1],+r[2]||1e-5)})},O0=function(e,t,i,r,s){var a=t-e,o=r-i;return yr(s,function(l){return i+((l-e)/a*o||0)})},xT=function n(e,t,i,r){var s=isNaN(e+t)?0:function(d){return(1-d)*e+d*t};if(!s){var a=on(e),o={},l,c,u,f,h;if(i===!0&&(r=1)&&(i=null),a)e={p:e},t={p:t};else if(gn(e)&&!gn(t)){for(u=[],f=e.length,h=f-2,c=1;c<f;c++)u.push(n(e[c-1],e[c]));f--,s=function(g){g*=f;var m=Math.min(h,~~g);return u[m](g-m)},i=t}else r||(e=Hs(gn(e)?[]:{},e));if(!u){for(l in t)gf.call(o,e,l,"get",t[l]);s=function(g){return bf(g,o)||(a?e.p:e)}}}return yr(i,s)},Rp=function(e,t,i){var r=e.labels,s=Jn,a,o,l;for(a in r)o=r[a]-t,o<0==!!i&&o&&s>(o=Math.abs(o))&&(l=a,s=o);return l},Gn=function(e,t,i){var r=e.vars,s=r[t],a=Lt,o=e._ctx,l,c,u;if(s)return l=r[t+"Params"],c=r.callbackScope||e,i&&pr.length&&xl(),o&&(Lt=o),u=l?s.apply(c,l):s.call(c),Lt=a,u},Pa=function(e){return vr(e),e.scrollTrigger&&e.scrollTrigger.kill(!!un),e.progress()<1&&Gn(e,"onInterrupt"),e},Ps,B0=[],k0=function(e){if(e)if(e=!e.name&&e.default||e,cf()||e.headless){var t=e.name,i=Gt(e),r=t&&!i&&e.init?function(){this._props=[]}:e,s={init:Ga,render:bf,add:gf,kill:NT,modifier:FT,rawVars:0},a={targetTest:0,get:0,getSetter:xf,aliases:{},register:0};if(Xs(),e!==r){if(Bn[t])return;jn(r,jn(bl(e,s),a)),Hs(r.prototype,Hs(s,bl(e,a))),Bn[r.prop=t]=r,e.targetTest&&(il.push(r),ff[t]=1),t=(t==="css"?"CSS":t.charAt(0).toUpperCase()+t.substr(1))+"Plugin"}M0(t,r),e.register&&e.register(Dn,r,Cn)}else B0.push(e)},wt=255,Da={aqua:[0,wt,wt],lime:[0,wt,0],silver:[192,192,192],black:[0,0,0],maroon:[128,0,0],teal:[0,128,128],blue:[0,0,wt],navy:[0,0,128],white:[wt,wt,wt],olive:[128,128,0],yellow:[wt,wt,0],orange:[wt,165,0],gray:[128,128,128],purple:[128,0,128],green:[0,128,0],red:[wt,0,0],pink:[wt,192,203],cyan:[0,wt,wt],transparent:[wt,wt,wt,0]},Zc=function(e,t,i){return e+=e<0?1:e>1?-1:0,(e*6<1?t+(i-t)*e*6:e<.5?i:e*3<2?t+(i-t)*(2/3-e)*6:t)*wt+.5|0},z0=function(e,t,i){var r=e?Xi(e)?[e>>16,e>>8&wt,e&wt]:0:Da.black,s,a,o,l,c,u,f,h,d,g;if(!r){if(e.substr(-1)===","&&(e=e.substr(0,e.length-1)),Da[e])r=Da[e];else if(e.charAt(0)==="#"){if(e.length<6&&(s=e.charAt(1),a=e.charAt(2),o=e.charAt(3),e="#"+s+s+a+a+o+o+(e.length===5?e.charAt(4)+e.charAt(4):"")),e.length===9)return r=parseInt(e.substr(1,6),16),[r>>16,r>>8&wt,r&wt,parseInt(e.substr(7),16)/255];e=parseInt(e.substr(1),16),r=[e>>16,e>>8&wt,e&wt]}else if(e.substr(0,3)==="hsl"){if(r=g=e.match(yp),!t)l=+r[0]%360/360,c=+r[1]/100,u=+r[2]/100,a=u<=.5?u*(c+1):u+c-u*c,s=u*2-a,r.length>3&&(r[3]*=1),r[0]=Zc(l+1/3,s,a),r[1]=Zc(l,s,a),r[2]=Zc(l-1/3,s,a);else if(~e.indexOf("="))return r=e.match(_0),i&&r.length<4&&(r[3]=1),r}else r=e.match(yp)||Da.transparent;r=r.map(Number)}return t&&!g&&(s=r[0]/wt,a=r[1]/wt,o=r[2]/wt,f=Math.max(s,a,o),h=Math.min(s,a,o),u=(f+h)/2,f===h?l=c=0:(d=f-h,c=u>.5?d/(2-f-h):d/(f+h),l=f===s?(a-o)/d+(a<o?6:0):f===a?(o-s)/d+2:(s-a)/d+4,l*=60),r[0]=~~(l+.5),r[1]=~~(c*100+.5),r[2]=~~(u*100+.5)),i&&r.length<4&&(r[3]=1),r},G0=function(e){var t=[],i=[],r=-1;return e.split(mr).forEach(function(s){var a=s.match(Cs)||[];t.push.apply(t,a),i.push(r+=a.length+1)}),t.c=i,t},Cp=function(e,t,i){var r="",s=(e+r).match(mr),a=t?"hsla(":"rgba(",o=0,l,c,u,f;if(!s)return e;if(s=s.map(function(h){return(h=z0(h,t,1))&&a+(t?h[0]+","+h[1]+"%,"+h[2]+"%,"+h[3]:h.join(","))+")"}),i&&(u=G0(e),l=i.c,l.join(r)!==u.c.join(r)))for(c=e.replace(mr,"1").split(Cs),f=c.length-1;o<f;o++)r+=c[o]+(~l.indexOf(o)?s.shift()||a+"0,0,0,0)":(u.length?u:s.length?s:i).shift());if(!c)for(c=e.split(mr),f=c.length-1;o<f;o++)r+=c[o]+s[o];return r+c[f]},mr=(function(){var n="(?:\\b(?:(?:rgb|rgba|hsl|hsla)\\(.+?\\))|\\B#(?:[0-9a-f]{3,4}){1,2}\\b",e;for(e in Da)n+="|"+e+"\\b";return new RegExp(n+")","gi")})(),bT=/hsl[a]?\(/,H0=function(e){var t=e.join(" "),i;if(mr.lastIndex=0,mr.test(t))return i=bT.test(t),e[1]=Cp(e[1],i),e[0]=Cp(e[0],i,G0(e[1])),!0},Va,zn=(function(){var n=Date.now,e=500,t=33,i=n(),r=i,s=1e3/240,a=s,o=[],l,c,u,f,h,d,g=function m(p){var _=n()-r,v=p===!0,M,y,T,S;if((_>e||_<0)&&(i+=_-t),r+=_,T=r-i,M=T-a,(M>0||v)&&(S=++f.frame,h=T-f.time*1e3,f.time=T=T/1e3,a+=M+(M>=s?4:s-M),y=1),v||(l=c(m)),y)for(d=0;d<o.length;d++)o[d](T,h,S,p)};return f={time:0,frame:0,tick:function(){g(!0)},deltaRatio:function(p){return h/(1e3/(p||60))},wake:function(){x0&&(!wh&&cf()&&(vi=wh=window,uf=vi.document||{},Xn.gsap=Dn,(vi.gsapVersions||(vi.gsapVersions=[])).push(Dn.version),b0(vl||vi.GreenSockGlobals||!vi.gsap&&vi||{}),B0.forEach(k0)),u=typeof requestAnimationFrame<"u"&&requestAnimationFrame,l&&f.sleep(),c=u||function(p){return setTimeout(p,a-f.time*1e3+1|0)},Va=1,g(2))},sleep:function(){(u?cancelAnimationFrame:clearTimeout)(l),Va=0,c=Ga},lagSmoothing:function(p,_){e=p||1/0,t=Math.min(_||33,e)},fps:function(p){s=1e3/(p||240),a=f.time*1e3+s},add:function(p,_,v){var M=_?function(y,T,S,E){p(y,T,S,E),f.remove(M)}:p;return f.remove(p),o[v?"unshift":"push"](M),Xs(),M},remove:function(p,_){~(_=o.indexOf(p))&&o.splice(_,1)&&d>=_&&d--},_listeners:o},f})(),Xs=function(){return!Va&&zn.wake()},dt={},MT=/^[\d.\-M][\d.\-,\s]/,ST=/["']/g,yT=function(e){for(var t={},i=e.substr(1,e.length-3).split(":"),r=i[0],s=1,a=i.length,o,l,c;s<a;s++)l=i[s],o=s!==a-1?l.lastIndexOf(","):l.length,c=l.substr(0,o),t[r]=isNaN(c)?c.replace(ST,"").trim():+c,r=l.substr(o+1).trim();return t},TT=function(e){var t=e.indexOf("(")+1,i=e.indexOf(")"),r=e.indexOf("(",t);return e.substring(t,~r&&r<i?e.indexOf(")",i+1):i)},ET=function(e){var t=(e+"").split("("),i=dt[t[0]];return i&&t.length>1&&i.config?i.config.apply(null,~e.indexOf("{")?[yT(t[1])]:TT(e).split(",").map(E0)):dt._CE&&MT.test(e)?dt._CE("",e):i},wT=function(e){return function(t){return 1-e(1-t)}},Vr=function(e,t){return e&&(Gt(e)?e:dt[e]||ET(e))||t},$r=function(e,t,i,r){i===void 0&&(i=function(l){return 1-t(1-l)}),r===void 0&&(r=function(l){return l<.5?t(l*2)/2:1-t((1-l)*2)/2});var s={easeIn:t,easeOut:i,easeInOut:r},a;return Rn(e,function(o){dt[o]=Xn[o]=s,dt[a=o.toLowerCase()]=i;for(var l in s)dt[a+(l==="easeIn"?".in":l==="easeOut"?".out":".inOut")]=dt[o+"."+l]=s[l]}),s},V0=function(e){return function(t){return t<.5?(1-e(1-t*2))/2:.5+e((t-.5)*2)/2}},$c=function n(e,t,i){var r=t>=1?t:1,s=(i||(e?.3:.45))/(t<1?t:1),a=s/Eh*(Math.asin(1/r)||0),o=function(u){return u===1?1:r*Math.pow(2,-10*u)*Zy((u-a)*s)+1},l=e==="out"?o:e==="in"?function(c){return 1-o(1-c)}:V0(o);return s=Eh/s,l.config=function(c,u){return n(e,c,u)},l},Jc=function n(e,t){t===void 0&&(t=1.70158);var i=function(a){return a?--a*a*((t+1)*a+t)+1:0},r=e==="out"?i:e==="in"?function(s){return 1-i(1-s)}:V0(i);return r.config=function(s){return n(e,s)},r};Rn("Linear,Quad,Cubic,Quart,Quint,Strong",function(n,e){var t=e<5?e+1:e;$r(n+",Power"+(t-1),e?function(i){return Math.pow(i,t)}:function(i){return i},function(i){return 1-Math.pow(1-i,t)},function(i){return i<.5?Math.pow(i*2,t)/2:1-Math.pow((1-i)*2,t)/2})});dt.Linear.easeNone=dt.none=dt.Linear.easeIn;$r("Elastic",$c("in"),$c("out"),$c());(function(n,e){var t=1/e,i=2*t,r=2.5*t,s=function(o){return o<t?n*o*o:o<i?n*Math.pow(o-1.5/e,2)+.75:o<r?n*(o-=2.25/e)*o+.9375:n*Math.pow(o-2.625/e,2)+.984375};$r("Bounce",function(a){return 1-s(1-a)},s)})(7.5625,2.75);$r("Expo",function(n){return Math.pow(2,10*(n-1))*n+n*n*n*n*n*n*(1-n)});$r("Circ",function(n){return-(m0(1-n*n)-1)});$r("Sine",function(n){return n===1?1:-Ky(n*Yy)+1});$r("Back",Jc("in"),Jc("out"),Jc());dt.SteppedEase=dt.steps=Xn.SteppedEase={config:function(e,t){e===void 0&&(e=1);var i=1/e,r=e+(t?0:1),s=t?1:0,a=1-Rt;return function(o){return((r*$a(0,a,o)|0)+s)*i}}};ka.ease=dt["quad.out"];Rn("onComplete,onUpdate,onStart,onRepeat,onReverseComplete,onInterrupt",function(n){return df+=n+","+n+"Params,"});var W0=function(e,t){this.id=qy++,e._gsap=this,this.target=e,this.harness=t,this.get=t?t.get:y0,this.set=t?t.getSetter:xf},Wa=(function(){function n(t){this.vars=t,this._delay=+t.delay||0,(this._repeat=t.repeat===1/0?-2:t.repeat||0)&&(this._rDelay=t.repeatDelay||0,this._yoyo=!!t.yoyo||!!t.yoyoEase),this._ts=1,Ws(this,+t.duration,1,1),this.data=t.data,Lt&&(this._ctx=Lt,Lt.data.push(this)),Va||zn.wake()}var e=n.prototype;return e.delay=function(i){return i||i===0?(this.parent&&this.parent.smoothChildTiming&&this.startTime(this._start+i-this._delay),this._delay=i,this):this._delay},e.duration=function(i){return arguments.length?this.totalDuration(this._repeat>0?i+(i+this._rDelay)*this._repeat:i):this.totalDuration()&&this._dur},e.totalDuration=function(i){return arguments.length?(this._dirty=0,Ws(this,this._repeat<0?i:(i-this._repeat*this._rDelay)/(this._repeat+1))):this._tDur},e.totalTime=function(i,r){if(Xs(),!arguments.length)return this._tTime;var s=this._dp;if(s&&s.smoothChildTiming&&this._ts){for(kl(this,i),!s._dp||s.parent||R0(s,this);s&&s.parent;)s.parent._time!==s._start+(s._ts>=0?s._tTime/s._ts:(s.totalDuration()-s._tTime)/-s._ts)&&s.totalTime(s._tTime,!0),s=s.parent;!this.parent&&this._dp.autoRemoveChildren&&(this._ts>0&&i<this._tDur||this._ts<0&&i>0||!this._tDur&&!i)&&Si(this._dp,this,this._start-this._delay)}return(this._tTime!==i||!this._dur&&!r||this._initted&&Math.abs(this._zTime)===Rt||!this._initted&&this._dur&&i||!i&&!this._initted&&(this.add||this._ptLookup))&&(this._ts||(this._pTime=i),T0(this,i,r)),this},e.time=function(i,r){return arguments.length?this.totalTime(Math.min(this.totalDuration(),i+wp(this))%(this._dur+this._rDelay)||(i?this._dur:0),r):this._time},e.totalProgress=function(i,r){return arguments.length?this.totalTime(this.totalDuration()*i,r):this.totalDuration()?Math.min(1,this._tTime/this._tDur):this.rawTime()>=0&&this._initted?1:0},e.progress=function(i,r){return arguments.length?this.totalTime(this.duration()*(this._yoyo&&!(this.iteration()&1)?1-i:i)+wp(this),r):this.duration()?Math.min(1,this._time/this._dur):this.rawTime()>0?1:0},e.iteration=function(i,r){var s=this.duration()+this._rDelay;return arguments.length?this.totalTime(this._time+(i-1)*s,r):this._repeat?Vs(this._tTime,s)+1:1},e.timeScale=function(i,r){if(!arguments.length)return this._rts===-Rt?0:this._rts;if(this._rts===i)return this;var s=this.parent&&this._ts?Ml(this.parent._time,this):this._tTime;return this._rts=+i||0,this._ts=this._ps||i===-Rt?0:this._rts,this.totalTime($a(-Math.abs(this._delay),this.totalDuration(),s),r!==!1),Bl(this),aT(this)},e.paused=function(i){return arguments.length?(this._ps!==i&&(this._ps=i,i?(this._pTime=this._tTime||Math.max(-this._delay,this.rawTime()),this._ts=this._act=0):(Xs(),this._ts=this._rts,this.totalTime(this.parent&&!this.parent.smoothChildTiming?this.rawTime():this._tTime||this._pTime,this.progress()===1&&Math.abs(this._zTime)!==Rt&&(this._tTime-=Rt)))),this):this._ps},e.startTime=function(i){if(arguments.length){this._start=Nt(i);var r=this.parent||this._dp;return r&&(r._sort||!this.parent)&&Si(r,this,this._start-this._delay),this}return this._start},e.endTime=function(i){return this._start+(An(i)?this.totalDuration():this.duration())/Math.abs(this._ts||1)},e.rawTime=function(i){var r=this.parent||this._dp;return r?i&&(!this._ts||this._repeat&&this._time&&this.totalProgress()<1)?this._tTime%(this._dur+this._rDelay):this._ts?Ml(r.rawTime(i),this):this._tTime:this._tTime},e.revert=function(i){i===void 0&&(i=nT);var r=un;return un=i,mf(this)&&(this.timeline&&this.timeline.revert(i),this.totalTime(-.01,i.suppressEvents)),this.data!=="nested"&&i.kill!==!1&&this.kill(),un=r,this},e.globalTime=function(i){for(var r=this,s=arguments.length?i:r.rawTime();r;)s=r._start+s/(Math.abs(r._ts)||1),r=r._dp;return!this.parent&&this._sat?this._sat.globalTime(i):s},e.repeat=function(i){return arguments.length?(this._repeat=i===1/0?-2:i,Ap(this)):this._repeat===-2?1/0:this._repeat},e.repeatDelay=function(i){if(arguments.length){var r=this._time;return this._rDelay=i,Ap(this),r?this.time(r):this}return this._rDelay},e.yoyo=function(i){return arguments.length?(this._yoyo=i,this):this._yoyo},e.seek=function(i,r){return this.totalTime(Zn(this,i),An(r))},e.restart=function(i,r){return this.play().totalTime(i?-this._delay:0,An(r)),this._dur||(this._zTime=-Rt),this},e.play=function(i,r){return i!=null&&this.seek(i,r),this.reversed(!1).paused(!1)},e.reverse=function(i,r){return i!=null&&this.seek(i||this.totalDuration(),r),this.reversed(!0).paused(!1)},e.pause=function(i,r){return i!=null&&this.seek(i,r),this.paused(!0)},e.resume=function(){return this.paused(!1)},e.reversed=function(i){return arguments.length?(!!i!==this.reversed()&&this.timeScale(-this._rts||(i?-Rt:0)),this):this._rts<0},e.invalidate=function(){return this._initted=this._act=0,this._zTime=-Rt,this},e.isActive=function(){var i=this.parent||this._dp,r=this._start,s;return!!(!i||this._ts&&this._initted&&i.isActive()&&(s=i.rawTime(!0))>=r&&s<this.endTime(!0)-Rt)},e.eventCallback=function(i,r,s){var a=this.vars;return arguments.length>1?(r?(a[i]=r,s&&(a[i+"Params"]=s),i==="onUpdate"&&(this._onUpdate=r)):delete a[i],this):a[i]},e.then=function(i){var r=this,s=r._prom;return new Promise(function(a){var o=Gt(i)?i:w0,l=function(){var u=r.then;r.then=null,s&&s(),Gt(o)&&(o=o(r))&&(o.then||o===r)&&(r.then=u),a(o),r.then=u};r._initted&&r.totalProgress()===1&&r._ts>=0||!r._tTime&&r._ts<0?l():r._prom=l})},e.kill=function(){Pa(this)},n})();jn(Wa.prototype,{_time:0,_start:0,_end:0,_tTime:0,_tDur:0,_dirty:0,_repeat:0,_yoyo:!1,parent:null,_initted:!1,_rDelay:0,_ts:1,_dp:0,ratio:0,_zTime:-Rt,_prom:0,_ps:!1,_rts:1});var wn=(function(n){p0(e,n);function e(i,r){var s;return i===void 0&&(i={}),s=n.call(this,i)||this,s.labels={},s.smoothChildTiming=!!i.smoothChildTiming,s.autoRemoveChildren=!!i.autoRemoveChildren,s._sort=An(i.sortChildren),Ot&&Si(i.parent||Ot,Oi(s),r),i.reversed&&s.reverse(),i.paused&&s.paused(!0),i.scrollTrigger&&C0(Oi(s),i.scrollTrigger),s}var t=e.prototype;return t.to=function(r,s,a){return Fa(0,arguments,this),this},t.from=function(r,s,a){return Fa(1,arguments,this),this},t.fromTo=function(r,s,a,o){return Fa(2,arguments,this),this},t.set=function(r,s,a){return s.duration=0,s.parent=this,Ia(s).repeatDelay||(s.repeat=0),s.immediateRender=!!s.immediateRender,new Xt(r,s,Zn(this,a),1),this},t.call=function(r,s,a){return Si(this,Xt.delayedCall(0,r,s),a)},t.staggerTo=function(r,s,a,o,l,c,u){return a.duration=s,a.stagger=a.stagger||o,a.onComplete=c,a.onCompleteParams=u,a.parent=this,new Xt(r,a,Zn(this,l)),this},t.staggerFrom=function(r,s,a,o,l,c,u){return a.runBackwards=1,Ia(a).immediateRender=An(a.immediateRender),this.staggerTo(r,s,a,o,l,c,u)},t.staggerFromTo=function(r,s,a,o,l,c,u,f){return o.startAt=a,Ia(o).immediateRender=An(o.immediateRender),this.staggerTo(r,s,o,l,c,u,f)},t.render=function(r,s,a){var o=this._time,l=this._dirty?this.totalDuration():this._tDur,c=this._dur,u=r<=0?0:Nt(r),f=this._zTime<0!=r<0&&(this._initted||!c),h,d,g,m,p,_,v,M,y,T,S,E;if(this!==Ot&&u>l&&r>=0&&(u=l),u!==this._tTime||a||f){if(o!==this._time&&c&&(u+=this._time-o,r+=this._time-o),h=u,y=this._start,M=this._ts,_=!M,f&&(c||(o=this._zTime),(r||!s)&&(this._zTime=r)),this._repeat){if(S=this._yoyo,p=c+this._rDelay,this._repeat<-1&&r<0)return this.totalTime(p*100+r,s,a);if(h=Nt(u%p),u===l?(m=this._repeat,h=c):(T=Nt(u/p),m=~~T,m&&m===T&&(h=c,m--),h>c&&(h=c)),T=Vs(this._tTime,p),!o&&this._tTime&&T!==m&&this._tTime-T*p-this._dur<=0&&(T=m),S&&m&1&&(h=c-h,E=1),m!==T&&!this._lock){var b=S&&T&1,x=b===(S&&m&1);if(m<T&&(b=!b),o=b?0:u%c?c:u,this._lock=1,this.render(o||(E?0:Nt(m*p)),s,!c)._lock=0,this._tTime=u,!s&&this.parent&&Gn(this,"onRepeat"),this.vars.repeatRefresh&&!E&&(this.invalidate()._lock=1,T=m),o&&o!==this._time||_!==!this._ts||this.vars.onRepeat&&!this.parent&&!this._act)return this;if(c=this._dur,l=this._tDur,x&&(this._lock=2,o=b?c:-1e-4,this.render(o,!0),this.vars.repeatRefresh&&!E&&this.invalidate()),this._lock=0,!this._ts&&!_)return this}}if(this._hasPause&&!this._forcing&&this._lock<2&&(v=uT(this,Nt(o),Nt(h)),v&&(u-=h-(h=v._start))),this._tTime=u,this._time=h,this._act=!!M,this._initted||(this._onUpdate=this.vars.onUpdate,this._initted=1,this._zTime=r,o=0),!o&&u&&c&&!s&&!T&&(Gn(this,"onStart"),this._tTime!==u))return this;if(h>=o&&r>=0)for(d=this._first;d;){if(g=d._next,(d._act||h>=d._start)&&d._ts&&v!==d){if(d.parent!==this)return this.render(r,s,a);if(d.render(d._ts>0?(h-d._start)*d._ts:(d._dirty?d.totalDuration():d._tDur)+(h-d._start)*d._ts,s,a),h!==this._time||!this._ts&&!_){v=0,g&&(u+=this._zTime=-Rt);break}}d=g}else{d=this._last;for(var A=r<0?r:h;d;){if(g=d._prev,(d._act||A<=d._end)&&d._ts&&v!==d){if(d.parent!==this)return this.render(r,s,a);if(d.render(d._ts>0?(A-d._start)*d._ts:(d._dirty?d.totalDuration():d._tDur)+(A-d._start)*d._ts,s,a||un&&mf(d)),h!==this._time||!this._ts&&!_){v=0,g&&(u+=this._zTime=A?-Rt:Rt);break}}d=g}}if(v&&!s&&(this.pause(),v.render(h>=o?0:-Rt)._zTime=h>=o?1:-1,this._ts))return this._start=y,Bl(this),this.render(r,s,a);this._onUpdate&&!s&&Gn(this,"onUpdate",!0),(u===l&&this._tTime>=this.totalDuration()||!u&&o)&&(y===this._start||Math.abs(M)!==Math.abs(this._ts))&&(this._lock||((r||!c)&&(u===l&&this._ts>0||!u&&this._ts<0)&&vr(this,1),!s&&!(r<0&&!o)&&(u||o||!l)&&(Gn(this,u===l&&r>=0?"onComplete":"onReverseComplete",!0),this._prom&&!(u<l&&this.timeScale()>0)&&this._prom())))}return this},t.add=function(r,s){var a=this;if(Xi(s)||(s=Zn(this,s,r)),!(r instanceof Wa)){if(gn(r))return r.forEach(function(o){return a.add(o,s)}),this;if(on(r))return this.addLabel(r,s);if(Gt(r))r=Xt.delayedCall(0,r);else return this}return this!==r?Si(this,r,s):this},t.getChildren=function(r,s,a,o){r===void 0&&(r=!0),s===void 0&&(s=!0),a===void 0&&(a=!0),o===void 0&&(o=-Jn);for(var l=[],c=this._first;c;)c._start>=o&&(c instanceof Xt?s&&l.push(c):(a&&l.push(c),r&&l.push.apply(l,c.getChildren(!0,s,a)))),c=c._next;return l},t.getById=function(r){for(var s=this.getChildren(1,1,1),a=s.length;a--;)if(s[a].vars.id===r)return s[a]},t.remove=function(r){return on(r)?this.removeLabel(r):Gt(r)?this.killTweensOf(r):(r.parent===this&&Ol(this,r),r===this._recent&&(this._recent=this._last),Hr(this))},t.totalTime=function(r,s){return arguments.length?(this._forcing=1,!this._dp&&this._ts&&(this._start=Nt(zn.time-(this._ts>0?r/this._ts:(this.totalDuration()-r)/-this._ts))),n.prototype.totalTime.call(this,r,s),this._forcing=0,this):this._tTime},t.addLabel=function(r,s){return this.labels[r]=Zn(this,s),this},t.removeLabel=function(r){return delete this.labels[r],this},t.addPause=function(r,s,a){var o=Xt.delayedCall(0,s||Ga,a);return o.data="isPause",this._hasPause=1,Si(this,o,Zn(this,r))},t.removePause=function(r){var s=this._first;for(r=Zn(this,r);s;)s._start===r&&s.data==="isPause"&&vr(s),s=s._next},t.killTweensOf=function(r,s,a){for(var o=this.getTweensOf(r,a),l=o.length;l--;)ur!==o[l]&&o[l].kill(r,s);return this},t.getTweensOf=function(r,s){for(var a=[],o=Qn(r),l=this._first,c=Xi(s),u;l;)l instanceof Xt?iT(l._targets,o)&&(c?(!ur||l._initted&&l._ts)&&l.globalTime(0)<=s&&l.globalTime(l.totalDuration())>s:!s||l.isActive())&&a.push(l):(u=l.getTweensOf(o,s)).length&&a.push.apply(a,u),l=l._next;return a},t.tweenTo=function(r,s){s=s||{};var a=this,o=Zn(a,r),l=s,c=l.startAt,u=l.onStart,f=l.onStartParams,h=l.immediateRender,d,g=Xt.to(a,jn({ease:s.ease||"none",lazy:!1,immediateRender:!1,time:o,overwrite:"auto",duration:s.duration||Math.abs((o-(c&&"time"in c?c.time:a._time))/a.timeScale())||Rt,onStart:function(){if(a.pause(),!d){var p=s.duration||Math.abs((o-(c&&"time"in c?c.time:a._time))/a.timeScale());g._dur!==p&&Ws(g,p,0,1).render(g._time,!0,!0),d=1}u&&u.apply(g,f||[])}},s));return h?g.render(0):g},t.tweenFromTo=function(r,s,a){return this.tweenTo(s,jn({startAt:{time:Zn(this,r)}},a))},t.recent=function(){return this._recent},t.nextLabel=function(r){return r===void 0&&(r=this._time),Rp(this,Zn(this,r))},t.previousLabel=function(r){return r===void 0&&(r=this._time),Rp(this,Zn(this,r),1)},t.currentLabel=function(r){return arguments.length?this.seek(r,!0):this.previousLabel(this._time+Rt)},t.shiftChildren=function(r,s,a){a===void 0&&(a=0);var o=this._first,l=this.labels,c;for(r=Nt(r);o;)o._start>=a&&(o._start+=r,o._end+=r),o=o._next;if(s)for(c in l)l[c]>=a&&(l[c]+=r);return Hr(this)},t.invalidate=function(r){var s=this._first;for(this._lock=0;s;)s.invalidate(r),s=s._next;return n.prototype.invalidate.call(this,r)},t.clear=function(r){r===void 0&&(r=!0);for(var s=this._first,a;s;)a=s._next,this.remove(s),s=a;return this._dp&&(this._time=this._tTime=this._pTime=0),r&&(this.labels={}),Hr(this)},t.totalDuration=function(r){var s=0,a=this,o=a._last,l=Jn,c,u,f;if(arguments.length)return a.timeScale((a._repeat<0?a.duration():a.totalDuration())/(a.reversed()?-r:r));if(a._dirty){for(f=a.parent;o;)c=o._prev,o._dirty&&o.totalDuration(),u=o._start,u>l&&a._sort&&o._ts&&!a._lock?(a._lock=1,Si(a,o,u-o._delay,1)._lock=0):l=u,u<0&&o._ts&&(s-=u,(!f&&!a._dp||f&&f.smoothChildTiming)&&(a._start+=Nt(u/a._ts),a._time-=u,a._tTime-=u),a.shiftChildren(-u,!1,-1/0),l=0),o._end>s&&o._ts&&(s=o._end),o=c;Ws(a,a===Ot&&a._time>s?a._time:s,1,1),a._dirty=0}return a._tDur},e.updateRoot=function(r){if(Ot._ts&&(T0(Ot,Ml(r,Ot)),S0=zn.frame),zn.frame>=Tp){Tp+=Vn.autoSleep||120;var s=Ot._first;if((!s||!s._ts)&&Vn.autoSleep&&zn._listeners.length<2){for(;s&&!s._ts;)s=s._next;s||zn.sleep()}}},e})(Wa);jn(wn.prototype,{_lock:0,_hasPause:0,_forcing:0});var AT=function(e,t,i,r,s,a,o){var l=new Cn(this._pt,e,t,0,1,Z0,null,s),c=0,u=0,f,h,d,g,m,p,_,v;for(l.b=i,l.e=r,i+="",r+="",(_=~r.indexOf("random("))&&(r=Ha(r)),a&&(v=[i,r],a(v,e,t),i=v[0],r=v[1]),h=i.match(qc)||[];f=qc.exec(r);)g=f[0],m=r.substring(c,f.index),d?d=(d+1)%5:m.substr(-5)==="rgba("&&(d=1),g!==h[u++]&&(p=parseFloat(h[u-1])||0,l._pt={_next:l._pt,p:m||u===1?m:",",s:p,c:g.charAt(1)==="="?Ls(p,g)-p:parseFloat(g)-p,m:d&&d<4?Math.round:0},c=qc.lastIndex);return l.c=c<r.length?r.substring(c,r.length):"",l.fp=o,(v0.test(r)||_)&&(l.e=0),this._pt=l,l},gf=function(e,t,i,r,s,a,o,l,c,u){Gt(r)&&(r=r(s||0,e,a));var f=e[t],h=i!=="get"?i:Gt(f)?c?e[t.indexOf("set")||!Gt(e["get"+t.substr(3)])?t:"get"+t.substr(3)](c):e[t]():f,d=Gt(f)?c?UT:q0:vf,g;if(on(r)&&(~r.indexOf("random(")&&(r=Ha(r)),r.charAt(1)==="="&&(g=Ls(h,r)+(pn(h)||0),(g||g===0)&&(r=g))),!u||h!==r||Lh)return!isNaN(h*r)&&r!==""?(g=new Cn(this._pt,e,t,+h||0,r-(h||0),typeof f=="boolean"?IT:K0,0,d),c&&(g.fp=c),o&&g.modifier(o,this,e),this._pt=g):(!f&&!(t in e)&&hf(t,r),AT.call(this,e,t,h,r,d,l||Vn.stringFilter,c))},RT=function(e,t,i,r,s){if(Gt(e)&&(e=Na(e,s,t,i,r)),!Ci(e)||e.style&&e.nodeType||gn(e)||g0(e))return on(e)?Na(e,s,t,i,r):e;var a={},o;for(o in e)a[o]=Na(e[o],s,t,i,r);return a},X0=function(e,t,i,r,s,a){var o,l,c,u;if(Bn[e]&&(o=new Bn[e]).init(s,o.rawVars?t[e]:RT(t[e],r,s,a,i),i,r,a)!==!1&&(i._pt=l=new Cn(i._pt,s,e,0,1,o.render,o,0,o.priority),i!==Ps))for(c=i._ptLookup[i._targets.indexOf(s)],u=o._props.length;u--;)c[o._props[u]]=l;return o},ur,Lh,_f=function n(e,t,i){var r=e.vars,s=r.ease,a=r.startAt,o=r.immediateRender,l=r.lazy,c=r.onUpdate,u=r.runBackwards,f=r.yoyoEase,h=r.keyframes,d=r.autoRevert,g=e._dur,m=e._startAt,p=e._targets,_=e.parent,v=_&&_.data==="nested"?_.vars.targets:p,M=e._overwrite==="auto"&&!of,y=e.timeline,T=r.easeReverse||f,S,E,b,x,A,C,R,L,U,I,F,O,j;if(y&&(!h||!s)&&(s="none"),e._ease=Vr(s,ka.ease),e._rEase=T&&(Vr(T)||e._ease),e._from=!y&&!!r.runBackwards,e._from&&(e.ratio=1),!y||h&&!r.stagger){if(L=p[0]?Gr(p[0]).harness:0,O=L&&r[L.prop],S=bl(r,ff),m&&(m._zTime<0&&m.progress(1),t<0&&u&&o&&!d?m.render(-1,!0):m.revert(u&&g?nl:tT),m._lazy=0),a){if(vr(e._startAt=Xt.set(p,jn({data:"isStart",overwrite:!1,parent:_,immediateRender:!0,lazy:!m&&An(l),startAt:null,delay:0,onUpdate:c&&function(){return Gn(e,"onUpdate")},stagger:0},a))),e._startAt._dp=0,e._startAt._sat=e,t<0&&(un||!o&&!d)&&e._startAt.revert(nl),o&&g&&t<=0&&i<=0){t&&(e._zTime=t);return}}else if(u&&g&&!m){if(t&&(o=!1),b=jn({overwrite:!1,data:"isFromStart",lazy:o&&!m&&An(l),immediateRender:o,stagger:0,parent:_},S),O&&(b[L.prop]=O),vr(e._startAt=Xt.set(p,b)),e._startAt._dp=0,e._startAt._sat=e,t<0&&(un?e._startAt.revert(nl):e._startAt.render(-1,!0)),e._zTime=t,!o)n(e._startAt,Rt,Rt);else if(!t)return}for(e._pt=e._ptCache=0,l=g&&An(l)||l&&!g,E=0;E<p.length;E++){if(A=p[E],R=A._gsap||pf(p)[E]._gsap,e._ptLookup[E]=I={},Ah[R.id]&&pr.length&&xl(),F=v===p?E:v.indexOf(A),L&&(U=new L).init(A,O||S,e,F,v)!==!1&&(e._pt=x=new Cn(e._pt,A,U.name,0,1,U.render,U,0,U.priority),U._props.forEach(function(G){I[G]=x}),U.priority&&(C=1)),!L||O)for(b in S)Bn[b]&&(U=X0(b,S,e,F,A,v))?U.priority&&(C=1):I[b]=x=gf.call(e,A,b,"get",S[b],F,v,0,r.stringFilter);e._op&&e._op[E]&&e.kill(A,e._op[E]),M&&e._pt&&(ur=e,Ot.killTweensOf(A,I,e.globalTime(t)),j=!e.parent,ur=0),e._pt&&l&&(Ah[R.id]=1)}C&&$0(e),e._onInit&&e._onInit(e)}e._onUpdate=c,e._initted=(!e._op||e._pt)&&!j,h&&t<=0&&y.render(Jn,!0,!0)},CT=function(e,t,i,r,s,a,o,l){var c=(e._pt&&e._ptCache||(e._ptCache={}))[t],u,f,h,d;if(!c)for(c=e._ptCache[t]=[],h=e._ptLookup,d=e._targets.length;d--;){if(u=h[d][t],u&&u.d&&u.d._pt)for(u=u.d._pt;u&&u.p!==t&&u.fp!==t;)u=u._next;if(!u)return Lh=1,e.vars[t]="+=0",_f(e,o),Lh=0,l?za(t+" not eligible for reset. Try splitting into individual properties"):1;c.push(u)}for(d=c.length;d--;)f=c[d],u=f._pt||f,u.s=(r||r===0)&&!s?r:u.s+(r||0)+a*u.c,u.c=i-u.s,f.e&&(f.e=Vt(i)+pn(f.e)),f.b&&(f.b=u.s+pn(f.b))},PT=function(e,t){var i=e[0]?Gr(e[0]).harness:0,r=i&&i.aliases,s,a,o,l;if(!r)return t;s=Hs({},t);for(a in r)if(a in s)for(l=r[a].split(","),o=l.length;o--;)s[l[o]]=s[a];return s},DT=function(e,t,i,r){var s=t.ease||r||"power1.inOut",a,o;if(gn(t))o=i[e]||(i[e]=[]),t.forEach(function(l,c){return o.push({t:c/(t.length-1)*100,v:l,e:s})});else for(a in t)o=i[a]||(i[a]=[]),a==="ease"||o.push({t:parseFloat(e),v:t[a],e:s})},Na=function(e,t,i,r,s){return Gt(e)?e.call(t,i,r,s):on(e)&&~e.indexOf("random(")?Ha(e):e},j0=df+"repeat,repeatDelay,yoyo,repeatRefresh,yoyoEase,easeReverse,autoRevert",Y0={};Rn(j0+",id,stagger,delay,duration,paused,scrollTrigger",function(n){return Y0[n]=1});var Xt=(function(n){p0(e,n);function e(i,r,s,a){var o;typeof r=="number"&&(s.duration=r,r=s,s=null),o=n.call(this,a?r:Ia(r))||this;var l=o.vars,c=l.duration,u=l.delay,f=l.immediateRender,h=l.stagger,d=l.overwrite,g=l.keyframes,m=l.defaults,p=l.scrollTrigger,_=r.parent||Ot,v=(gn(i)||g0(i)?Xi(i[0]):"length"in r)?[i]:Qn(i),M,y,T,S,E,b,x,A;if(o._targets=v.length?pf(v):za("GSAP target "+i+" not found. https://gsap.com",!Vn.nullTargetWarn)||[],o._ptLookup=[],o._overwrite=d,g||h||Vo(c)||Vo(u)){r=o.vars;var C=r.easeReverse||r.yoyoEase;if(M=o.timeline=new wn({data:"nested",defaults:m||{},targets:_&&_.data==="nested"?_.vars.targets:v}),M.kill(),M.parent=M._dp=Oi(o),M._start=0,h||Vo(c)||Vo(u)){if(S=v.length,x=h&&L0(h),Ci(h))for(E in h)~j0.indexOf(E)&&(A||(A={}),A[E]=h[E]);for(y=0;y<S;y++)T=bl(r,Y0),T.stagger=0,C&&(T.easeReverse=C),A&&Hs(T,A),b=v[y],T.duration=+Na(c,Oi(o),y,b,v),T.delay=(+Na(u,Oi(o),y,b,v)||0)-o._delay,!h&&S===1&&T.delay&&(o._delay=u=T.delay,o._start+=u,T.delay=0),M.to(b,T,x?x(y,b,v):0),M._ease=dt.none;M.duration()?c=u=0:o.timeline=0}else if(g){Ia(jn(M.vars.defaults,{ease:"none"})),M._ease=Vr(g.ease||r.ease||"none");var R=0,L,U,I;if(gn(g))g.forEach(function(F){return M.to(v,F,">")}),M.duration();else{T={};for(E in g)E==="ease"||E==="easeEach"||DT(E,g[E],T,g.easeEach);for(E in T)for(L=T[E].sort(function(F,O){return F.t-O.t}),R=0,y=0;y<L.length;y++)U=L[y],I={ease:U.e,duration:(U.t-(y?L[y-1].t:0))/100*c},I[E]=U.v,M.to(v,I,R),R+=I.duration;M.duration()<c&&M.to({},{duration:c-M.duration()})}}c||o.duration(c=M.duration())}else o.timeline=0;return d===!0&&!of&&(ur=Oi(o),Ot.killTweensOf(v),ur=0),Si(_,Oi(o),s),r.reversed&&o.reverse(),r.paused&&o.paused(!0),(f||!c&&!g&&o._start===Nt(_._time)&&An(f)&&oT(Oi(o))&&_.data!=="nested")&&(o._tTime=-Rt,o.render(Math.max(0,-u)||0)),p&&C0(Oi(o),p),o}var t=e.prototype;return t.render=function(r,s,a){var o=this._time,l=this._tDur,c=this._dur,u=r<0,f=r>l-Rt&&!u?l:r<Rt?0:r,h,d,g,m,p,_,v,M;if(!c)cT(this,r,s,a);else if(f!==this._tTime||!r||a||!this._initted&&this._tTime||this._startAt&&this._zTime<0!==u||this._lazy){if(h=f,M=this.timeline,this._repeat){if(m=c+this._rDelay,this._repeat<-1&&u)return this.totalTime(m*100+r,s,a);if(h=Nt(f%m),f===l?(g=this._repeat,h=c):(p=Nt(f/m),g=~~p,g&&g===p?(h=c,g--):h>c&&(h=c)),_=this._yoyo&&g&1,_&&(h=c-h),p=Vs(this._tTime,m),h===o&&!a&&this._initted&&g===p)return this._tTime=f,this;g!==p&&this.vars.repeatRefresh&&!_&&!this._lock&&h!==m&&this._initted&&(this._lock=a=1,this.render(Nt(m*g),!0).invalidate()._lock=0)}if(!this._initted){if(P0(this,u?r:h,a,s,f))return this._tTime=0,this;if(o!==this._time&&!(a&&this.vars.repeatRefresh&&g!==p))return this;if(c!==this._dur)return this.render(r,s,a)}if(this._rEase){var y=h<o;if(y!==this._inv){var T=y?o:c-o;this._inv=y,this._from&&(this.ratio=1-this.ratio),this._invRatio=this.ratio,this._invTime=o,this._invRecip=T?(y?-1:1)/T:0,this._invScale=y?-this.ratio:1-this.ratio,this._invEase=y?this._rEase:this._ease}this.ratio=v=this._invRatio+this._invScale*this._invEase((h-this._invTime)*this._invRecip)}else this.ratio=v=this._ease(h/c);if(this._from&&(this.ratio=v=1-v),this._tTime=f,this._time=h,!this._act&&this._ts&&(this._act=1,this._lazy=0),!o&&f&&!s&&!p&&(Gn(this,"onStart"),this._tTime!==f))return this;for(d=this._pt;d;)d.r(v,d.d),d=d._next;M&&M.render(r<0?r:M._dur*M._ease(h/this._dur),s,a)||this._startAt&&(this._zTime=r),this._onUpdate&&!s&&(u&&Rh(this,r,s,a),Gn(this,"onUpdate")),this._repeat&&g!==p&&this.vars.onRepeat&&!s&&this.parent&&Gn(this,"onRepeat"),(f===this._tDur||!f)&&this._tTime===f&&(u&&!this._onUpdate&&Rh(this,r,!0,!0),(r||!c)&&(f===this._tDur&&this._ts>0||!f&&this._ts<0)&&vr(this,1),!s&&!(u&&!o)&&(f||o||_)&&(Gn(this,f===l?"onComplete":"onReverseComplete",!0),this._prom&&!(f<l&&this.timeScale()>0)&&this._prom()))}return this},t.targets=function(){return this._targets},t.invalidate=function(r){return(!r||!this.vars.runBackwards)&&(this._startAt=0),this._pt=this._op=this._onUpdate=this._lazy=this.ratio=0,this._ptLookup=[],this.timeline&&this.timeline.invalidate(r),n.prototype.invalidate.call(this,r)},t.resetTo=function(r,s,a,o,l){Va||zn.wake(),this._ts||this.play();var c=Math.min(this._dur,(this._dp._time-this._start)*this._ts),u;return this._initted||_f(this,c),u=this._ease(c/this._dur),CT(this,r,s,a,o,u,c,l)?this.resetTo(r,s,a,o,1):(kl(this,0),this.parent||A0(this._dp,this,"_first","_last",this._dp._sort?"_start":0),this.render(0))},t.kill=function(r,s){if(s===void 0&&(s="all"),!r&&(!s||s==="all"))return this._lazy=this._pt=0,this.parent?Pa(this):this.scrollTrigger&&this.scrollTrigger.kill(!!un),this;if(this.timeline){var a=this.timeline.totalDuration();return this.timeline.killTweensOf(r,s,ur&&ur.vars.overwrite!==!0)._first||Pa(this),this.parent&&a!==this.timeline.totalDuration()&&Ws(this,this._dur*this.timeline._tDur/a,0,1),this}var o=this._targets,l=r?Qn(r):o,c=this._ptLookup,u=this._pt,f,h,d,g,m,p,_;if((!s||s==="all")&&sT(o,l))return s==="all"&&(this._pt=0),Pa(this);for(f=this._op=this._op||[],s!=="all"&&(on(s)&&(m={},Rn(s,function(v){return m[v]=1}),s=m),s=PT(o,s)),_=o.length;_--;)if(~l.indexOf(o[_])){h=c[_],s==="all"?(f[_]=s,g=h,d={}):(d=f[_]=f[_]||{},g=s);for(m in g)p=h&&h[m],p&&((!("kill"in p.d)||p.d.kill(m)===!0)&&Ol(this,p,"_pt"),delete h[m]),d!=="all"&&(d[m]=1)}return this._initted&&!this._pt&&u&&Pa(this),this},e.to=function(r,s){return new e(r,s,arguments[2])},e.from=function(r,s){return Fa(1,arguments)},e.delayedCall=function(r,s,a,o){return new e(s,0,{immediateRender:!1,lazy:!1,overwrite:!1,delay:r,onComplete:s,onReverseComplete:s,onCompleteParams:a,onReverseCompleteParams:a,callbackScope:o})},e.fromTo=function(r,s,a){return Fa(2,arguments)},e.set=function(r,s){return s.duration=0,s.repeatDelay||(s.repeat=0),new e(r,s)},e.killTweensOf=function(r,s,a){return Ot.killTweensOf(r,s,a)},e})(Wa);jn(Xt.prototype,{_targets:[],_lazy:0,_startAt:0,_op:0,_onInit:0});Rn("staggerTo,staggerFrom,staggerFromTo",function(n){Xt[n]=function(){var e=new wn,t=Ph.call(arguments,0);return t.splice(n==="staggerFromTo"?5:4,0,0),e[n].apply(e,t)}});var vf=function(e,t,i){return e[t]=i},q0=function(e,t,i){return e[t](i)},UT=function(e,t,i,r){return e[t](r.fp,i)},LT=function(e,t,i){return e.setAttribute(t,i)},xf=function(e,t){return Gt(e[t])?q0:lf(e[t])&&e.setAttribute?LT:vf},K0=function(e,t){return t.set(t.t,t.p,Math.round((t.s+t.c*e)*1e6)/1e6,t)},IT=function(e,t){return t.set(t.t,t.p,!!(t.s+t.c*e),t)},Z0=function(e,t){var i=t._pt,r="";if(!e&&t.b)r=t.b;else if(e===1&&t.e)r=t.e;else{for(;i;)r=i.p+(i.m?i.m(i.s+i.c*e):Math.round((i.s+i.c*e)*1e4)/1e4)+r,i=i._next;r+=t.c}t.set(t.t,t.p,r,t)},bf=function(e,t){for(var i=t._pt;i;)i.r(e,i.d),i=i._next},FT=function(e,t,i,r){for(var s=this._pt,a;s;)a=s._next,s.p===r&&s.modifier(e,t,i),s=a},NT=function(e){for(var t=this._pt,i,r;t;)r=t._next,t.p===e&&!t.op||t.op===e?Ol(this,t,"_pt"):t.dep||(i=1),t=r;return!i},OT=function(e,t,i,r){r.mSet(e,t,r.m.call(r.tween,i,r.mt),r)},$0=function(e){for(var t=e._pt,i,r,s,a;t;){for(i=t._next,r=s;r&&r.pr>t.pr;)r=r._next;(t._prev=r?r._prev:a)?t._prev._next=t:s=t,(t._next=r)?r._prev=t:a=t,t=i}e._pt=s},Cn=(function(){function n(t,i,r,s,a,o,l,c,u){this.t=i,this.s=s,this.c=a,this.p=r,this.r=o||K0,this.d=l||this,this.set=c||vf,this.pr=u||0,this._next=t,t&&(t._prev=this)}var e=n.prototype;return e.modifier=function(i,r,s){this.mSet=this.mSet||this.set,this.set=OT,this.m=i,this.mt=s,this.tween=r},n})();Rn(df+"parent,duration,ease,delay,overwrite,runBackwards,startAt,yoyo,immediateRender,repeat,repeatDelay,data,paused,reversed,lazy,callbackScope,stringFilter,id,yoyoEase,stagger,inherit,repeatRefresh,keyframes,autoRevert,scrollTrigger,easeReverse",function(n){return ff[n]=1});Xn.TweenMax=Xn.TweenLite=Xt;Xn.TimelineLite=Xn.TimelineMax=wn;Ot=new wn({sortChildren:!1,defaults:ka,autoRemoveChildren:!0,id:"root",smoothChildTiming:!0});Vn.stringFilter=H0;var Wr=[],rl={},BT=[],Pp=0,kT=0,Qc=function(e){return(rl[e]||BT).map(function(t){return t()})},Ih=function(){var e=Date.now(),t=[];e-Pp>2&&(Qc("matchMediaInit"),Wr.forEach(function(i){var r=i.queries,s=i.conditions,a,o,l,c;for(o in r)a=vi.matchMedia(r[o]).matches,a&&(l=1),a!==s[o]&&(s[o]=a,c=1);c&&(i.revert(),l&&t.push(i))}),Qc("matchMediaRevert"),t.forEach(function(i){return i.onMatch(i,function(r){return i.add(null,r)})}),Pp=e,Qc("matchMedia"))},J0=(function(){function n(t,i){this.selector=i&&Dh(i),this.data=[],this._r=[],this.isReverted=!1,this.id=kT++,t&&this.add(t)}var e=n.prototype;return e.add=function(i,r,s){Gt(i)&&(s=r,r=i,i=Gt);var a=this,o=function(){var c=Lt,u=a.selector,f;return c&&c!==a&&c.data.push(a),s&&(a.selector=Dh(s)),Lt=a,f=r.apply(a,arguments),Gt(f)&&a._r.push(f),Lt=c,a.selector=u,a.isReverted=!1,f};return a.last=o,i===Gt?o(a,function(l){return a.add(null,l)}):i?a[i]=o:o},e.ignore=function(i){var r=Lt;Lt=null,i(this),Lt=r},e.getTweens=function(){var i=[];return this.data.forEach(function(r){return r instanceof n?i.push.apply(i,r.getTweens()):r instanceof Xt&&!(r.parent&&r.parent.data==="nested")&&i.push(r)}),i},e.clear=function(){this._r.length=this.data.length=0},e.kill=function(i,r){var s=this;if(i?(function(){for(var o=s.getTweens(),l=s.data.length,c;l--;)c=s.data[l],c.data==="isFlip"&&(c.revert(),c.getChildren(!0,!0,!1).forEach(function(u){return o.splice(o.indexOf(u),1)}));for(o.map(function(u){return{g:u._dur||u._delay||u._sat&&!u._sat.vars.immediateRender?u.globalTime(0):-1/0,t:u}}).sort(function(u,f){return f.g-u.g||-1/0}).forEach(function(u){return u.t.revert(i)}),l=s.data.length;l--;)c=s.data[l],c instanceof wn?c.data!=="nested"&&(c.scrollTrigger&&c.scrollTrigger.revert(),c.kill()):!(c instanceof Xt)&&c.revert&&c.revert(i);s._r.forEach(function(u){return u(i,s)}),s.isReverted=!0})():this.data.forEach(function(o){return o.kill&&o.kill()}),this.clear(),r)for(var a=Wr.length;a--;)Wr[a].id===this.id&&Wr.splice(a,1)},e.revert=function(i){this.kill(i||{})},n})(),zT=(function(){function n(t){this.contexts=[],this.scope=t,Lt&&Lt.data.push(this)}var e=n.prototype;return e.add=function(i,r,s){Ci(i)||(i={matches:i});var a=new J0(0,s||this.scope),o=a.conditions={},l,c,u;Lt&&!a.selector&&(a.selector=Lt.selector),this.contexts.push(a),r=a.add("onMatch",r),a.queries=i;for(c in i)c==="all"?u=1:(l=vi.matchMedia(i[c]),l&&(Wr.indexOf(a)<0&&Wr.push(a),(o[c]=l.matches)&&(u=1),l.addListener?l.addListener(Ih):l.addEventListener("change",Ih)));return u&&r(a,function(f){return a.add(null,f)}),this},e.revert=function(i){this.kill(i||{})},e.kill=function(i){this.contexts.forEach(function(r){return r.kill(i,!0)})},n})(),Sl={registerPlugin:function(){for(var e=arguments.length,t=new Array(e),i=0;i<e;i++)t[i]=arguments[i];t.forEach(function(r){return k0(r)})},timeline:function(e){return new wn(e)},getTweensOf:function(e,t){return Ot.getTweensOf(e,t)},getProperty:function(e,t,i,r){on(e)&&(e=Qn(e)[0]);var s=Gr(e||{}).get,a=i?w0:E0;return i==="native"&&(i=""),e&&(t?a((Bn[t]&&Bn[t].get||s)(e,t,i,r)):function(o,l,c){return a((Bn[o]&&Bn[o].get||s)(e,o,l,c))})},quickSetter:function(e,t,i){if(e=Qn(e),e.length>1){var r=e.map(function(u){return Dn.quickSetter(u,t,i)}),s=r.length;return function(u){for(var f=s;f--;)r[f](u)}}e=e[0]||{};var a=Bn[t],o=Gr(e),l=o.harness&&(o.harness.aliases||{})[t]||t,c=a?function(u){var f=new a;Ps._pt=0,f.init(e,i?u+i:u,Ps,0,[e]),f.render(1,f),Ps._pt&&bf(1,Ps)}:o.set(e,l);return a?c:function(u){return c(e,l,i?u+i:u,o,1)}},quickTo:function(e,t,i){var r,s=Dn.to(e,jn((r={},r[t]="+=0.1",r.paused=!0,r.stagger=0,r),i||{})),a=function(l,c,u){return s.resetTo(t,l,c,u)};return a.tween=s,a},isTweening:function(e){return Ot.getTweensOf(e,!0).length>0},defaults:function(e){return e&&e.ease&&(e.ease=Vr(e.ease,ka.ease)),Ep(ka,e||{})},config:function(e){return Ep(Vn,e||{})},registerEffect:function(e){var t=e.name,i=e.effect,r=e.plugins,s=e.defaults,a=e.extendTimeline;(r||"").split(",").forEach(function(o){return o&&!Bn[o]&&!Xn[o]&&za(t+" effect requires "+o+" plugin.")}),Kc[t]=function(o,l,c){return i(Qn(o),jn(l||{},s),c)},a&&(wn.prototype[t]=function(o,l,c){return this.add(Kc[t](o,Ci(l)?l:(c=l)&&{},this),c)})},registerEase:function(e,t){dt[e]=Vr(t)},parseEase:function(e,t){return arguments.length?Vr(e,t):dt},getById:function(e){return Ot.getById(e)},exportRoot:function(e,t){e===void 0&&(e={});var i=new wn(e),r,s;for(i.smoothChildTiming=An(e.smoothChildTiming),Ot.remove(i),i._dp=0,i._time=i._tTime=Ot._time,r=Ot._first;r;)s=r._next,(t||!(!r._dur&&r instanceof Xt&&r.vars.onComplete===r._targets[0]))&&Si(i,r,r._start-r._delay),r=s;return Si(Ot,i,0),i},context:function(e,t){return e?new J0(e,t):Lt},matchMedia:function(e){return new zT(e)},matchMediaRefresh:function(){return Wr.forEach(function(e){var t=e.conditions,i,r;for(r in t)t[r]&&(t[r]=!1,i=1);i&&e.revert()})||Ih()},addEventListener:function(e,t){var i=rl[e]||(rl[e]=[]);~i.indexOf(t)||i.push(t)},removeEventListener:function(e,t){var i=rl[e],r=i&&i.indexOf(t);r>=0&&i.splice(r,1)},utils:{wrap:_T,wrapYoyo:vT,distribute:L0,random:F0,snap:I0,normalize:gT,getUnit:pn,clamp:fT,splitColor:z0,toArray:Qn,selector:Dh,mapRange:O0,pipe:pT,unitize:mT,interpolate:xT,shuffle:U0},install:b0,effects:Kc,ticker:zn,updateRoot:wn.updateRoot,plugins:Bn,globalTimeline:Ot,core:{PropTween:Cn,globals:M0,Tween:Xt,Timeline:wn,Animation:Wa,getCache:Gr,_removeLinkedListItem:Ol,reverting:function(){return un},context:function(e){return e&&Lt&&(Lt.data.push(e),e._ctx=Lt),Lt},suppressOverwrites:function(e){return of=e}}};Rn("to,from,fromTo,delayedCall,set,killTweensOf",function(n){return Sl[n]=Xt[n]});zn.add(wn.updateRoot);Ps=Sl.to({},{duration:0});var GT=function(e,t){for(var i=e._pt;i&&i.p!==t&&i.op!==t&&i.fp!==t;)i=i._next;return i},HT=function(e,t){var i=e._targets,r,s,a;for(r in t)for(s=i.length;s--;)a=e._ptLookup[s][r],a&&(a=a.d)&&(a._pt&&(a=GT(a,r)),a&&a.modifier&&a.modifier(t[r],e,i[s],r))},eu=function(e,t){return{name:e,headless:1,rawVars:1,init:function(r,s,a){a._onInit=function(o){var l,c;if(on(s)&&(l={},Rn(s,function(u){return l[u]=1}),s=l),t){l={};for(c in s)l[c]=t(s[c]);s=l}HT(o,s)}}}},Dn=Sl.registerPlugin({name:"attr",init:function(e,t,i,r,s){var a,o,l;this.tween=i;for(a in t)l=e.getAttribute(a)||"",o=this.add(e,"setAttribute",(l||0)+"",t[a],r,s,0,0,a),o.op=a,o.b=l,this._props.push(a)},render:function(e,t){for(var i=t._pt;i;)un?i.set(i.t,i.p,i.b,i):i.r(e,i.d),i=i._next}},{name:"endArray",headless:1,init:function(e,t){for(var i=t.length;i--;)this.add(e,i,e[i]||0,t[i],0,0,0,0,0,1)}},eu("roundProps",Uh),eu("modifiers"),eu("snap",I0))||Sl;Xt.version=wn.version=Dn.version="3.15.0";x0=1;cf()&&Xs();dt.Power0;dt.Power1;dt.Power2;dt.Power3;dt.Power4;dt.Linear;dt.Quad;dt.Cubic;dt.Quart;dt.Quint;dt.Strong;dt.Elastic;dt.Back;dt.SteppedEase;dt.Bounce;dt.Sine;dt.Expo;dt.Circ;/*!
 * CSSPlugin 3.15.0
 * https://gsap.com
 *
 * Copyright 2008-2026, GreenSock. All rights reserved.
 * Subject to the terms at https://gsap.com/standard-license
 * @author: Jack Doyle, jack@greensock.com
*/var Dp,hr,Is,Mf,Br,Up,Sf,VT=function(){return typeof window<"u"},ji={},Ir=180/Math.PI,Fs=Math.PI/180,Es=Math.atan2,Lp=1e8,yf=/([A-Z])/g,WT=/(left|right|width|margin|padding|x)/i,XT=/[\s,\(]\S/,Ei={autoAlpha:"opacity,visibility",scale:"scaleX,scaleY",alpha:"opacity"},Fh=function(e,t){return t.set(t.t,t.p,Math.round((t.s+t.c*e)*1e4)/1e4+t.u,t)},jT=function(e,t){return t.set(t.t,t.p,e===1?t.e:Math.round((t.s+t.c*e)*1e4)/1e4+t.u,t)},YT=function(e,t){return t.set(t.t,t.p,e?Math.round((t.s+t.c*e)*1e4)/1e4+t.u:t.b,t)},qT=function(e,t){return t.set(t.t,t.p,e===1?t.e:e?Math.round((t.s+t.c*e)*1e4)/1e4+t.u:t.b,t)},KT=function(e,t){var i=t.s+t.c*e;t.set(t.t,t.p,~~(i+(i<0?-.5:.5))+t.u,t)},Q0=function(e,t){return t.set(t.t,t.p,e?t.e:t.b,t)},eg=function(e,t){return t.set(t.t,t.p,e!==1?t.b:t.e,t)},ZT=function(e,t,i){return e.style[t]=i},$T=function(e,t,i){return e.style.setProperty(t,i)},JT=function(e,t,i){return e._gsap[t]=i},QT=function(e,t,i){return e._gsap.scaleX=e._gsap.scaleY=i},eE=function(e,t,i,r,s){var a=e._gsap;a.scaleX=a.scaleY=i,a.renderTransform(s,a)},tE=function(e,t,i,r,s){var a=e._gsap;a[t]=i,a.renderTransform(s,a)},Bt="transform",Pn=Bt+"Origin",nE=function n(e,t){var i=this,r=this.target,s=r.style,a=r._gsap;if(e in ji&&s){if(this.tfm=this.tfm||{},e!=="transform")e=Ei[e]||e,~e.indexOf(",")?e.split(",").forEach(function(o){return i.tfm[o]=Bi(r,o)}):this.tfm[e]=a.x?a[e]:Bi(r,e),e===Pn&&(this.tfm.zOrigin=a.zOrigin);else return Ei.transform.split(",").forEach(function(o){return n.call(i,o,t)});if(this.props.indexOf(Bt)>=0)return;a.svg&&(this.svgo=r.getAttribute("data-svg-origin"),this.props.push(Pn,t,"")),e=Bt}(s||t)&&this.props.push(e,t,s[e])},tg=function(e){e.translate&&(e.removeProperty("translate"),e.removeProperty("scale"),e.removeProperty("rotate"))},iE=function(){var e=this.props,t=this.target,i=t.style,r=t._gsap,s,a;for(s=0;s<e.length;s+=3)e[s+1]?e[s+1]===2?t[e[s]](e[s+2]):t[e[s]]=e[s+2]:e[s+2]?i[e[s]]=e[s+2]:i.removeProperty(e[s].substr(0,2)==="--"?e[s]:e[s].replace(yf,"-$1").toLowerCase());if(this.tfm){for(a in this.tfm)r[a]=this.tfm[a];r.svg&&(r.renderTransform(),t.setAttribute("data-svg-origin",this.svgo||"")),s=Sf(),(!s||!s.isStart)&&!i[Bt]&&(tg(i),r.zOrigin&&i[Pn]&&(i[Pn]+=" "+r.zOrigin+"px",r.zOrigin=0,r.renderTransform()),r.uncache=1)}},ng=function(e,t){var i={target:e,props:[],revert:iE,save:nE};return e._gsap||Dn.core.getCache(e),t&&e.style&&e.nodeType&&t.split(",").forEach(function(r){return i.save(r)}),i},ig,Nh=function(e,t){var i=hr.createElementNS?hr.createElementNS((t||"http://www.w3.org/1999/xhtml").replace(/^https/,"http"),e):hr.createElement(e);return i&&i.style?i:hr.createElement(e)},Hn=function n(e,t,i){var r=getComputedStyle(e);return r[t]||r.getPropertyValue(t.replace(yf,"-$1").toLowerCase())||r.getPropertyValue(t)||!i&&n(e,js(t)||t,1)||""},Ip="O,Moz,ms,Ms,Webkit".split(","),js=function(e,t,i){var r=t||Br,s=r.style,a=5;if(e in s&&!i)return e;for(e=e.charAt(0).toUpperCase()+e.substr(1);a--&&!(Ip[a]+e in s););return a<0?null:(a===3?"ms":a>=0?Ip[a]:"")+e},Oh=function(){VT()&&window.document&&(Dp=window,hr=Dp.document,Is=hr.documentElement,Br=Nh("div")||{style:{}},Nh("div"),Bt=js(Bt),Pn=Bt+"Origin",Br.style.cssText="border-width:0;line-height:0;position:absolute;padding:0",ig=!!js("perspective"),Sf=Dn.core.reverting,Mf=1)},Fp=function(e){var t=e.ownerSVGElement,i=Nh("svg",t&&t.getAttribute("xmlns")||"http://www.w3.org/2000/svg"),r=e.cloneNode(!0),s;r.style.display="block",i.appendChild(r),Is.appendChild(i);try{s=r.getBBox()}catch{}return i.removeChild(r),Is.removeChild(i),s},Np=function(e,t){for(var i=t.length;i--;)if(e.hasAttribute(t[i]))return e.getAttribute(t[i])},rg=function(e){var t,i;try{t=e.getBBox()}catch{t=Fp(e),i=1}return t&&(t.width||t.height)||i||(t=Fp(e)),t&&!t.width&&!t.x&&!t.y?{x:+Np(e,["x","cx","x1"])||0,y:+Np(e,["y","cy","y1"])||0,width:0,height:0}:t},sg=function(e){return!!(e.getCTM&&(!e.parentNode||e.ownerSVGElement)&&rg(e))},xr=function(e,t){if(t){var i=e.style,r;t in ji&&t!==Pn&&(t=Bt),i.removeProperty?(r=t.substr(0,2),(r==="ms"||t.substr(0,6)==="webkit")&&(t="-"+t),i.removeProperty(r==="--"?t:t.replace(yf,"-$1").toLowerCase())):i.removeAttribute(t)}},fr=function(e,t,i,r,s,a){var o=new Cn(e._pt,t,i,0,1,a?eg:Q0);return e._pt=o,o.b=r,o.e=s,e._props.push(i),o},Op={deg:1,rad:1,turn:1},rE={grid:1,flex:1},br=function n(e,t,i,r){var s=parseFloat(i)||0,a=(i+"").trim().substr((s+"").length)||"px",o=Br.style,l=WT.test(t),c=e.tagName.toLowerCase()==="svg",u=(c?"client":"offset")+(l?"Width":"Height"),f=100,h=r==="px",d=r==="%",g,m,p,_;if(r===a||!s||Op[r]||Op[a])return s;if(a!=="px"&&!h&&(s=n(e,t,i,"px")),_=e.getCTM&&sg(e),(d||a==="%")&&(ji[t]||~t.indexOf("adius")))return g=_?e.getBBox()[l?"width":"height"]:e[u],Vt(d?s/g*f:s/100*g);if(o[l?"width":"height"]=f+(h?a:r),m=r!=="rem"&&~t.indexOf("adius")||r==="em"&&e.appendChild&&!c?e:e.parentNode,_&&(m=(e.ownerSVGElement||{}).parentNode),(!m||m===hr||!m.appendChild)&&(m=hr.body),p=m._gsap,p&&d&&p.width&&l&&p.time===zn.time&&!p.uncache)return Vt(s/p.width*f);if(d&&(t==="height"||t==="width")){var v=e.style[t];e.style[t]=f+r,g=e[u],v?e.style[t]=v:xr(e,t)}else(d||a==="%")&&!rE[Hn(m,"display")]&&(o.position=Hn(e,"position")),m===e&&(o.position="static"),m.appendChild(Br),g=Br[u],m.removeChild(Br),o.position="absolute";return l&&d&&(p=Gr(m),p.time=zn.time,p.width=m[u]),Vt(h?g*s/f:g&&s?f/g*s:0)},Bi=function(e,t,i,r){var s;return Mf||Oh(),t in Ei&&t!=="transform"&&(t=Ei[t],~t.indexOf(",")&&(t=t.split(",")[0])),ji[t]&&t!=="transform"?(s=ja(e,r),s=t!=="transformOrigin"?s[t]:s.svg?s.origin:Tl(Hn(e,Pn))+" "+s.zOrigin+"px"):(s=e.style[t],(!s||s==="auto"||r||~(s+"").indexOf("calc("))&&(s=yl[t]&&yl[t](e,t,i)||Hn(e,t)||y0(e,t)||(t==="opacity"?1:0))),i&&!~(s+"").trim().indexOf(" ")?br(e,t,s,i)+i:s},sE=function(e,t,i,r){if(!i||i==="none"){var s=js(t,e,1),a=s&&Hn(e,s,1);a&&a!==i?(t=s,i=a):t==="borderColor"&&(i=Hn(e,"borderTopColor"))}var o=new Cn(this._pt,e.style,t,0,1,Z0),l=0,c=0,u,f,h,d,g,m,p,_,v,M,y,T;if(o.b=i,o.e=r,i+="",r+="",r.substring(0,6)==="var(--"&&(r=Hn(e,r.substring(4,r.indexOf(")")))),r==="auto"&&(m=e.style[t],e.style[t]=r,r=Hn(e,t)||r,m?e.style[t]=m:xr(e,t)),u=[i,r],H0(u),i=u[0],r=u[1],h=i.match(Cs)||[],T=r.match(Cs)||[],T.length){for(;f=Cs.exec(r);)p=f[0],v=r.substring(l,f.index),g?g=(g+1)%5:(v.substr(-5)==="rgba("||v.substr(-5)==="hsla(")&&(g=1),p!==(m=h[c++]||"")&&(d=parseFloat(m)||0,y=m.substr((d+"").length),p.charAt(1)==="="&&(p=Ls(d,p)+y),_=parseFloat(p),M=p.substr((_+"").length),l=Cs.lastIndex-M.length,M||(M=M||Vn.units[t]||y,l===r.length&&(r+=M,o.e+=M)),y!==M&&(d=br(e,t,m,M)||0),o._pt={_next:o._pt,p:v||c===1?v:",",s:d,c:_-d,m:g&&g<4||t==="zIndex"?Math.round:0});o.c=l<r.length?r.substring(l,r.length):""}else o.r=t==="display"&&r==="none"?eg:Q0;return v0.test(r)&&(o.e=0),this._pt=o,o},Bp={top:"0%",bottom:"100%",left:"0%",right:"100%",center:"50%"},aE=function(e){var t=e.split(" "),i=t[0],r=t[1]||"50%";return(i==="top"||i==="bottom"||r==="left"||r==="right")&&(e=i,i=r,r=e),t[0]=Bp[i]||i,t[1]=Bp[r]||r,t.join(" ")},oE=function(e,t){if(t.tween&&t.tween._time===t.tween._dur){var i=t.t,r=i.style,s=t.u,a=i._gsap,o,l,c;if(s==="all"||s===!0)r.cssText="",l=1;else for(s=s.split(","),c=s.length;--c>-1;)o=s[c],ji[o]&&(l=1,o=o==="transformOrigin"?Pn:Bt),xr(i,o);l&&(xr(i,Bt),a&&(a.svg&&i.removeAttribute("transform"),r.scale=r.rotate=r.translate="none",ja(i,1),a.uncache=1,tg(r)))}},yl={clearProps:function(e,t,i,r,s){if(s.data!=="isFromStart"){var a=e._pt=new Cn(e._pt,t,i,0,0,oE);return a.u=r,a.pr=-10,a.tween=s,e._props.push(i),1}}},Xa=[1,0,0,1,0,0],ag={},og=function(e){return e==="matrix(1, 0, 0, 1, 0, 0)"||e==="none"||!e},kp=function(e){var t=Hn(e,Bt);return og(t)?Xa:t.substr(7).match(_0).map(Vt)},Tf=function(e,t){var i=e._gsap||Gr(e),r=e.style,s=kp(e),a,o,l,c;return i.svg&&e.getAttribute("transform")?(l=e.transform.baseVal.consolidate().matrix,s=[l.a,l.b,l.c,l.d,l.e,l.f],s.join(",")==="1,0,0,1,0,0"?Xa:s):(s===Xa&&!e.offsetParent&&e!==Is&&!i.svg&&(l=r.display,r.display="block",a=e.parentNode,(!a||!e.offsetParent&&!e.getBoundingClientRect().width)&&(c=1,o=e.nextElementSibling,Is.appendChild(e)),s=kp(e),l?r.display=l:xr(e,"display"),c&&(o?a.insertBefore(e,o):a?a.appendChild(e):Is.removeChild(e))),t&&s.length>6?[s[0],s[1],s[4],s[5],s[12],s[13]]:s)},Bh=function(e,t,i,r,s,a){var o=e._gsap,l=s||Tf(e,!0),c=o.xOrigin||0,u=o.yOrigin||0,f=o.xOffset||0,h=o.yOffset||0,d=l[0],g=l[1],m=l[2],p=l[3],_=l[4],v=l[5],M=t.split(" "),y=parseFloat(M[0])||0,T=parseFloat(M[1])||0,S,E,b,x;i?l!==Xa&&(E=d*p-g*m)&&(b=y*(p/E)+T*(-m/E)+(m*v-p*_)/E,x=y*(-g/E)+T*(d/E)-(d*v-g*_)/E,y=b,T=x):(S=rg(e),y=S.x+(~M[0].indexOf("%")?y/100*S.width:y),T=S.y+(~(M[1]||M[0]).indexOf("%")?T/100*S.height:T)),r||r!==!1&&o.smooth?(_=y-c,v=T-u,o.xOffset=f+(_*d+v*m)-_,o.yOffset=h+(_*g+v*p)-v):o.xOffset=o.yOffset=0,o.xOrigin=y,o.yOrigin=T,o.smooth=!!r,o.origin=t,o.originIsAbsolute=!!i,e.style[Pn]="0px 0px",a&&(fr(a,o,"xOrigin",c,y),fr(a,o,"yOrigin",u,T),fr(a,o,"xOffset",f,o.xOffset),fr(a,o,"yOffset",h,o.yOffset)),e.setAttribute("data-svg-origin",y+" "+T)},ja=function(e,t){var i=e._gsap||new W0(e);if("x"in i&&!t&&!i.uncache)return i;var r=e.style,s=i.scaleX<0,a="px",o="deg",l=getComputedStyle(e),c=Hn(e,Pn)||"0",u,f,h,d,g,m,p,_,v,M,y,T,S,E,b,x,A,C,R,L,U,I,F,O,j,G,W,N,k,J,Q,K;return u=f=h=m=p=_=v=M=y=0,d=g=1,i.svg=!!(e.getCTM&&sg(e)),l.translate&&((l.translate!=="none"||l.scale!=="none"||l.rotate!=="none")&&(r[Bt]=(l.translate!=="none"?"translate3d("+(l.translate+" 0 0").split(" ").slice(0,3).join(", ")+") ":"")+(l.rotate!=="none"?"rotate("+l.rotate+") ":"")+(l.scale!=="none"?"scale("+l.scale.split(" ").join(",")+") ":"")+(l[Bt]!=="none"?l[Bt]:"")),r.scale=r.rotate=r.translate="none"),E=Tf(e,i.svg),i.svg&&(i.uncache?(j=e.getBBox(),c=i.xOrigin-j.x+"px "+(i.yOrigin-j.y)+"px",O=""):O=!t&&e.getAttribute("data-svg-origin"),Bh(e,O||c,!!O||i.originIsAbsolute,i.smooth!==!1,E)),T=i.xOrigin||0,S=i.yOrigin||0,E!==Xa&&(C=E[0],R=E[1],L=E[2],U=E[3],u=I=E[4],f=F=E[5],E.length===6?(d=Math.sqrt(C*C+R*R),g=Math.sqrt(U*U+L*L),m=C||R?Es(R,C)*Ir:0,v=L||U?Es(L,U)*Ir+m:0,v&&(g*=Math.abs(Math.cos(v*Fs))),i.svg&&(u-=T-(T*C+S*L),f-=S-(T*R+S*U))):(K=E[6],J=E[7],W=E[8],N=E[9],k=E[10],Q=E[11],u=E[12],f=E[13],h=E[14],b=Es(K,k),p=b*Ir,b&&(x=Math.cos(-b),A=Math.sin(-b),O=I*x+W*A,j=F*x+N*A,G=K*x+k*A,W=I*-A+W*x,N=F*-A+N*x,k=K*-A+k*x,Q=J*-A+Q*x,I=O,F=j,K=G),b=Es(-L,k),_=b*Ir,b&&(x=Math.cos(-b),A=Math.sin(-b),O=C*x-W*A,j=R*x-N*A,G=L*x-k*A,Q=U*A+Q*x,C=O,R=j,L=G),b=Es(R,C),m=b*Ir,b&&(x=Math.cos(b),A=Math.sin(b),O=C*x+R*A,j=I*x+F*A,R=R*x-C*A,F=F*x-I*A,C=O,I=j),p&&Math.abs(p)+Math.abs(m)>359.9&&(p=m=0,_=180-_),d=Vt(Math.sqrt(C*C+R*R+L*L)),g=Vt(Math.sqrt(F*F+K*K)),b=Es(I,F),v=Math.abs(b)>2e-4?b*Ir:0,y=Q?1/(Q<0?-Q:Q):0),i.svg&&(O=e.getAttribute("transform"),i.forceCSS=e.setAttribute("transform","")||!og(Hn(e,Bt)),O&&e.setAttribute("transform",O))),Math.abs(v)>90&&Math.abs(v)<270&&(s?(d*=-1,v+=m<=0?180:-180,m+=m<=0?180:-180):(g*=-1,v+=v<=0?180:-180)),t=t||i.uncache,i.x=u-((i.xPercent=u&&(!t&&i.xPercent||(Math.round(e.offsetWidth/2)===Math.round(-u)?-50:0)))?e.offsetWidth*i.xPercent/100:0)+a,i.y=f-((i.yPercent=f&&(!t&&i.yPercent||(Math.round(e.offsetHeight/2)===Math.round(-f)?-50:0)))?e.offsetHeight*i.yPercent/100:0)+a,i.z=h+a,i.scaleX=Vt(d),i.scaleY=Vt(g),i.rotation=Vt(m)+o,i.rotationX=Vt(p)+o,i.rotationY=Vt(_)+o,i.skewX=v+o,i.skewY=M+o,i.transformPerspective=y+a,(i.zOrigin=parseFloat(c.split(" ")[2])||!t&&i.zOrigin||0)&&(r[Pn]=Tl(c)),i.xOffset=i.yOffset=0,i.force3D=Vn.force3D,i.renderTransform=i.svg?cE:ig?lg:lE,i.uncache=0,i},Tl=function(e){return(e=e.split(" "))[0]+" "+e[1]},tu=function(e,t,i){var r=pn(t);return Vt(parseFloat(t)+parseFloat(br(e,"x",i+"px",r)))+r},lE=function(e,t){t.z="0px",t.rotationY=t.rotationX="0deg",t.force3D=0,lg(e,t)},Dr="0deg",Ta="0px",Ur=") ",lg=function(e,t){var i=t||this,r=i.xPercent,s=i.yPercent,a=i.x,o=i.y,l=i.z,c=i.rotation,u=i.rotationY,f=i.rotationX,h=i.skewX,d=i.skewY,g=i.scaleX,m=i.scaleY,p=i.transformPerspective,_=i.force3D,v=i.target,M=i.zOrigin,y="",T=_==="auto"&&e&&e!==1||_===!0;if(M&&(f!==Dr||u!==Dr)){var S=parseFloat(u)*Fs,E=Math.sin(S),b=Math.cos(S),x;S=parseFloat(f)*Fs,x=Math.cos(S),a=tu(v,a,E*x*-M),o=tu(v,o,-Math.sin(S)*-M),l=tu(v,l,b*x*-M+M)}p!==Ta&&(y+="perspective("+p+Ur),(r||s)&&(y+="translate("+r+"%, "+s+"%) "),(T||a!==Ta||o!==Ta||l!==Ta)&&(y+=l!==Ta||T?"translate3d("+a+", "+o+", "+l+") ":"translate("+a+", "+o+Ur),c!==Dr&&(y+="rotate("+c+Ur),u!==Dr&&(y+="rotateY("+u+Ur),f!==Dr&&(y+="rotateX("+f+Ur),(h!==Dr||d!==Dr)&&(y+="skew("+h+", "+d+Ur),(g!==1||m!==1)&&(y+="scale("+g+", "+m+Ur),v.style[Bt]=y||"translate(0, 0)"},cE=function(e,t){var i=t||this,r=i.xPercent,s=i.yPercent,a=i.x,o=i.y,l=i.rotation,c=i.skewX,u=i.skewY,f=i.scaleX,h=i.scaleY,d=i.target,g=i.xOrigin,m=i.yOrigin,p=i.xOffset,_=i.yOffset,v=i.forceCSS,M=parseFloat(a),y=parseFloat(o),T,S,E,b,x;l=parseFloat(l),c=parseFloat(c),u=parseFloat(u),u&&(u=parseFloat(u),c+=u,l+=u),l||c?(l*=Fs,c*=Fs,T=Math.cos(l)*f,S=Math.sin(l)*f,E=Math.sin(l-c)*-h,b=Math.cos(l-c)*h,c&&(u*=Fs,x=Math.tan(c-u),x=Math.sqrt(1+x*x),E*=x,b*=x,u&&(x=Math.tan(u),x=Math.sqrt(1+x*x),T*=x,S*=x)),T=Vt(T),S=Vt(S),E=Vt(E),b=Vt(b)):(T=f,b=h,S=E=0),(M&&!~(a+"").indexOf("px")||y&&!~(o+"").indexOf("px"))&&(M=br(d,"x",a,"px"),y=br(d,"y",o,"px")),(g||m||p||_)&&(M=Vt(M+g-(g*T+m*E)+p),y=Vt(y+m-(g*S+m*b)+_)),(r||s)&&(x=d.getBBox(),M=Vt(M+r/100*x.width),y=Vt(y+s/100*x.height)),x="matrix("+T+","+S+","+E+","+b+","+M+","+y+")",d.setAttribute("transform",x),v&&(d.style[Bt]=x)},uE=function(e,t,i,r,s){var a=360,o=on(s),l=parseFloat(s)*(o&&~s.indexOf("rad")?Ir:1),c=l-r,u=r+c+"deg",f,h;return o&&(f=s.split("_")[1],f==="short"&&(c%=a,c!==c%(a/2)&&(c+=c<0?a:-a)),f==="cw"&&c<0?c=(c+a*Lp)%a-~~(c/a)*a:f==="ccw"&&c>0&&(c=(c-a*Lp)%a-~~(c/a)*a)),e._pt=h=new Cn(e._pt,t,i,r,c,jT),h.e=u,h.u="deg",e._props.push(i),h},zp=function(e,t){for(var i in t)e[i]=t[i];return e},hE=function(e,t,i){var r=zp({},i._gsap),s="perspective,force3D,transformOrigin,svgOrigin",a=i.style,o,l,c,u,f,h,d,g;r.svg?(c=i.getAttribute("transform"),i.setAttribute("transform",""),a[Bt]=t,o=ja(i,1),xr(i,Bt),i.setAttribute("transform",c)):(c=getComputedStyle(i)[Bt],a[Bt]=t,o=ja(i,1),a[Bt]=c);for(l in ji)c=r[l],u=o[l],c!==u&&s.indexOf(l)<0&&(d=pn(c),g=pn(u),f=d!==g?br(i,l,c,g):parseFloat(c),h=parseFloat(u),e._pt=new Cn(e._pt,o,l,f,h-f,Fh),e._pt.u=g||0,e._props.push(l));zp(o,r)};Rn("padding,margin,Width,Radius",function(n,e){var t="Top",i="Right",r="Bottom",s="Left",a=(e<3?[t,i,r,s]:[t+s,t+i,r+i,r+s]).map(function(o){return e<2?n+o:"border"+o+n});yl[e>1?"border"+n:n]=function(o,l,c,u,f){var h,d;if(arguments.length<4)return h=a.map(function(g){return Bi(o,g,c)}),d=h.join(" "),d.split(h[0]).length===5?h[0]:d;h=(u+"").split(" "),d={},a.forEach(function(g,m){return d[g]=h[m]=h[m]||h[(m-1)/2|0]}),o.init(l,d,f)}});var cg={name:"css",register:Oh,targetTest:function(e){return e.style&&e.nodeType},init:function(e,t,i,r,s){var a=this._props,o=e.style,l=i.vars.startAt,c,u,f,h,d,g,m,p,_,v,M,y,T,S,E,b,x;Mf||Oh(),this.styles=this.styles||ng(e),b=this.styles.props,this.tween=i;for(m in t)if(m!=="autoRound"&&(u=t[m],!(Bn[m]&&X0(m,t,i,r,e,s)))){if(d=typeof u,g=yl[m],d==="function"&&(u=u.call(i,r,e,s),d=typeof u),d==="string"&&~u.indexOf("random(")&&(u=Ha(u)),g)g(this,e,m,u,i)&&(E=1);else if(m.substr(0,2)==="--")c=(getComputedStyle(e).getPropertyValue(m)+"").trim(),u+="",mr.lastIndex=0,mr.test(c)||(p=pn(c),_=pn(u),_?p!==_&&(c=br(e,m,c,_)+_):p&&(u+=p)),this.add(o,"setProperty",c,u,r,s,0,0,m),a.push(m),b.push(m,0,o[m]);else if(d!=="undefined"){if(l&&m in l?(c=typeof l[m]=="function"?l[m].call(i,r,e,s):l[m],on(c)&&~c.indexOf("random(")&&(c=Ha(c)),pn(c+"")||c==="auto"||(c+=Vn.units[m]||pn(Bi(e,m))||""),(c+"").charAt(1)==="="&&(c=Bi(e,m))):c=Bi(e,m),h=parseFloat(c),v=d==="string"&&u.charAt(1)==="="&&u.substr(0,2),v&&(u=u.substr(2)),f=parseFloat(u),m in Ei&&(m==="autoAlpha"&&(h===1&&Bi(e,"visibility")==="hidden"&&f&&(h=0),b.push("visibility",0,o.visibility),fr(this,o,"visibility",h?"inherit":"hidden",f?"inherit":"hidden",!f)),m!=="scale"&&m!=="transform"&&(m=Ei[m],~m.indexOf(",")&&(m=m.split(",")[0]))),M=m in ji,M){if(this.styles.save(m),x=u,d==="string"&&u.substring(0,6)==="var(--"){if(u=Hn(e,u.substring(4,u.indexOf(")"))),u.substring(0,5)==="calc("){var A=e.style.perspective;e.style.perspective=u,u=Hn(e,"perspective"),A?e.style.perspective=A:xr(e,"perspective")}f=parseFloat(u)}if(y||(T=e._gsap,T.renderTransform&&!t.parseTransform||ja(e,t.parseTransform),S=t.smoothOrigin!==!1&&T.smooth,y=this._pt=new Cn(this._pt,o,Bt,0,1,T.renderTransform,T,0,-1),y.dep=1),m==="scale")this._pt=new Cn(this._pt,T,"scaleY",T.scaleY,(v?Ls(T.scaleY,v+f):f)-T.scaleY||0,Fh),this._pt.u=0,a.push("scaleY",m),m+="X";else if(m==="transformOrigin"){b.push(Pn,0,o[Pn]),u=aE(u),T.svg?Bh(e,u,0,S,0,this):(_=parseFloat(u.split(" ")[2])||0,_!==T.zOrigin&&fr(this,T,"zOrigin",T.zOrigin,_),fr(this,o,m,Tl(c),Tl(u)));continue}else if(m==="svgOrigin"){Bh(e,u,1,S,0,this);continue}else if(m in ag){uE(this,T,m,h,v?Ls(h,v+u):u);continue}else if(m==="smoothOrigin"){fr(this,T,"smooth",T.smooth,u);continue}else if(m==="force3D"){T[m]=u;continue}else if(m==="transform"){hE(this,u,e);continue}}else m in o||(m=js(m)||m);if(M||(f||f===0)&&(h||h===0)&&!XT.test(u)&&m in o)p=(c+"").substr((h+"").length),f||(f=0),_=pn(u)||(m in Vn.units?Vn.units[m]:p),p!==_&&(h=br(e,m,c,_)),this._pt=new Cn(this._pt,M?T:o,m,h,(v?Ls(h,v+f):f)-h,!M&&(_==="px"||m==="zIndex")&&t.autoRound!==!1?KT:Fh),this._pt.u=_||0,M&&x!==u?(this._pt.b=c,this._pt.e=x,this._pt.r=qT):p!==_&&_!=="%"&&(this._pt.b=c,this._pt.r=YT);else if(m in o)sE.call(this,e,m,c,v?v+u:u);else if(m in e)this.add(e,m,c||e[m],v?v+u:u,r,s);else if(m!=="parseTransform"){hf(m,u);continue}M||(m in o?b.push(m,0,o[m]):typeof e[m]=="function"?b.push(m,2,e[m]()):b.push(m,1,c||e[m])),a.push(m)}}E&&$0(this)},render:function(e,t){if(t.tween._time||!Sf())for(var i=t._pt;i;)i.r(e,i.d),i=i._next;else t.styles.revert()},get:Bi,aliases:Ei,getSetter:function(e,t,i){var r=Ei[t];return r&&r.indexOf(",")<0&&(t=r),t in ji&&t!==Pn&&(e._gsap.x||Bi(e,"x"))?i&&Up===i?t==="scale"?QT:JT:(Up=i||{})&&(t==="scale"?eE:tE):e.style&&!lf(e.style[t])?ZT:~t.indexOf("-")?$T:xf(e,t)},core:{_removeProperty:xr,_getMatrix:Tf}};Dn.utils.checkPrefix=js;Dn.core.getStyleSaver=ng;(function(n,e,t,i){var r=Rn(n+","+e+","+t,function(s){ji[s]=1});Rn(e,function(s){Vn.units[s]="deg",ag[s]=1}),Ei[r[13]]=n+","+e,Rn(i,function(s){var a=s.split(":");Ei[a[1]]=r[a[0]]})})("x,y,z,scale,scaleX,scaleY,xPercent,yPercent","rotation,rotationX,rotationY,skewX,skewY","transform,transformOrigin,svgOrigin,force3D,smoothOrigin,transformPerspective","0:translateX,1:translateY,2:translateZ,8:rotate,8:rotationZ,8:rotateZ,9:rotateX,10:rotateY");Rn("x,y,z,top,right,bottom,left,width,height,fontSize,padding,margin,perspective",function(n){Vn.units[n]="px"});Dn.registerPlugin(cg);var sl=Dn.registerPlugin(cg)||Dn;sl.core.Tween;/**
 * postprocessing v6.39.5 build Wed Sep 09 2026
 * https://github.com/pmndrs/postprocessing
 * Copyright 2015-2026 Raoul van Rüschen
 * @license Zlib
 */var fE=(()=>{const n=new Float32Array([-1,-1,0,3,-1,0,-1,3,0]),e=new Float32Array([0,0,2,0,0,2]),t=new At;return t.setAttribute("position",new Ft(n,3)),t.setAttribute("uv",new Ft(e,2)),t})(),fi=class kh{static get fullscreenGeometry(){return fE}constructor(e="Pass",t=new gh,i=new rf){this.name=e,this.renderer=null,this.scene=t,this.camera=i,this.screen=null,this.rtt=!0,this.needsSwap=!0,this.needsDepthBlit=!1,this.needsDepthTexture=!1,this.enabled=!0}get renderToScreen(){return!this.rtt}set renderToScreen(e){if(this.rtt===e){const t=this.fullscreenMaterial;t!==null&&(t.needsUpdate=!0),this.rtt=!e}}set mainScene(e){}set mainCamera(e){}setRenderer(e){this.renderer=e}isEnabled(){return this.enabled}setEnabled(e){this.enabled=e}get fullscreenMaterial(){return this.screen!==null?this.screen.material:null}set fullscreenMaterial(e){let t=this.screen;t!==null?t.material=e:(t=new Wn(kh.fullscreenGeometry,e),t.frustumCulled=!1,this.scene===null&&(this.scene=new gh),this.scene.add(t),this.screen=t)}getFullscreenMaterial(){return this.fullscreenMaterial}setFullscreenMaterial(e){this.fullscreenMaterial=e}getDepthTexture(){return null}setDepthTexture(e,t=Ka){}render(e,t,i,r,s){throw new Error("Render method not implemented!")}setSize(e,t){}initialize(e,t,i){}dispose(){for(const e of Object.keys(this)){const t=this[e];(t instanceof $t||t instanceof Yi||t instanceof Zt||t instanceof kh)&&this[e].dispose()}this.fullscreenMaterial!==null&&this.fullscreenMaterial.dispose()}},dE=class extends fi{constructor(){super("ClearMaskPass",null,null),this.needsSwap=!1}render(n,e,t,i,r){const s=n.state.buffers.stencil;s.setLocked(!1),s.setTest(!1)}},pE=`#ifdef COLOR_WRITE
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
}`,ug="varying vec2 vUv;void main(){vUv=position.xy*0.5+0.5;gl_Position=vec4(position.xy,1.0,1.0);}",hg=class extends an{constructor(){super({name:"CopyMaterial",defines:{COLOR_SPACE_CONVERSION:"1",DEPTH_PACKING:"0",COLOR_WRITE:"1"},uniforms:{inputBuffer:new vt(null),depthBuffer:new vt(null),channelWeights:new vt(null),opacity:new vt(1)},blending:Mn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:pE,vertexShader:ug}),this.depthFunc=ol}get inputBuffer(){return this.uniforms.inputBuffer.value}set inputBuffer(n){const e=n!==null;this.colorWrite!==e&&(e?this.defines.COLOR_WRITE=!0:delete this.defines.COLOR_WRITE,this.colorWrite=e,this.needsUpdate=!0),this.uniforms.inputBuffer.value=n}get depthBuffer(){return this.uniforms.depthBuffer.value}set depthBuffer(n){const e=n!==null;this.depthWrite!==e&&(e?this.defines.DEPTH_WRITE=!0:delete this.defines.DEPTH_WRITE,this.depthTest=e,this.depthWrite=e,this.needsUpdate=!0),this.uniforms.depthBuffer.value=n}set depthPacking(n){this.defines.DEPTH_PACKING=n.toFixed(0),this.needsUpdate=!0}get colorSpaceConversion(){return this.defines.COLOR_SPACE_CONVERSION!==void 0}set colorSpaceConversion(n){this.colorSpaceConversion!==n&&(n?this.defines.COLOR_SPACE_CONVERSION=!0:delete this.defines.COLOR_SPACE_CONVERSION,this.needsUpdate=!0)}get channelWeights(){return this.uniforms.channelWeights.value}set channelWeights(n){n!==null?(this.defines.USE_WEIGHTS="1",this.uniforms.channelWeights.value=n):delete this.defines.USE_WEIGHTS,this.needsUpdate=!0}setInputBuffer(n){this.uniforms.inputBuffer.value=n}getOpacity(n){return this.uniforms.opacity.value}setOpacity(n){this.uniforms.opacity.value=n}},mE=class extends fi{constructor(n,e=!0){super("CopyPass"),this.fullscreenMaterial=new hg,this.needsSwap=!1,this.renderTarget=n,n===void 0&&(this.renderTarget=new $t(1,1,{minFilter:zt,magFilter:zt,stencilBuffer:!1,depthBuffer:!1}),this.renderTarget.texture.name="CopyPass.Target"),this.autoResize=e}get resize(){return this.autoResize}set resize(n){this.autoResize=n}get texture(){return this.renderTarget.texture}getTexture(){return this.renderTarget.texture}setAutoResizeEnabled(n){this.autoResize=n}render(n,e,t,i,r){this.fullscreenMaterial.inputBuffer=e.texture,n.setRenderTarget(this.renderToScreen?null:this.renderTarget),n.render(this.scene,this.camera)}setSize(n,e){this.autoResize&&this.renderTarget.setSize(n,e)}initialize(n,e,t){t!==void 0&&(this.renderTarget.texture.type=t,t!==jt?this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1":n!==null&&n.outputColorSpace===Tt&&(this.renderTarget.texture.colorSpace=Tt))}},Gp=new ut,fg=class extends fi{constructor(n=!0,e=!0,t=!1){super("ClearPass",null,null),this.needsSwap=!1,this.color=n,this.depth=e,this.stencil=t,this.overrideClearColor=null,this.overrideClearAlpha=-1}setClearFlags(n,e,t){this.color=n,this.depth=e,this.stencil=t}getOverrideClearColor(){return this.overrideClearColor}setOverrideClearColor(n){this.overrideClearColor=n}getOverrideClearAlpha(){return this.overrideClearAlpha}setOverrideClearAlpha(n){this.overrideClearAlpha=n}render(n,e,t,i,r){const s=this.overrideClearColor,a=this.overrideClearAlpha,o=n.getClearAlpha(),l=s!==null,c=a>=0;l?(n.getClearColor(Gp),n.setClearColor(s,c?a:o)):c&&n.setClearAlpha(a),n.setRenderTarget(this.renderToScreen?null:e),n.clear(this.color,this.depth,this.stencil),l?n.setClearColor(Gp,o):c&&n.setClearAlpha(o)}},gE=class extends fi{constructor(n,e){super("MaskPass",n,e),this.needsSwap=!1,this.clearPass=new fg(!1,!1,!0),this.inverse=!1}set mainScene(n){this.scene=n}set mainCamera(n){this.camera=n}get inverted(){return this.inverse}set inverted(n){this.inverse=n}get clear(){return this.clearPass.enabled}set clear(n){this.clearPass.enabled=n}getClearPass(){return this.clearPass}isInverted(){return this.inverted}setInverted(n){this.inverted=n}render(n,e,t,i,r){const s=n.getContext(),a=n.state.buffers,o=this.scene,l=this.camera,c=this.clearPass,u=this.inverted?0:1,f=1-u;a.color.setMask(!1),a.depth.setMask(!1),a.color.setLocked(!0),a.depth.setLocked(!0),a.stencil.setTest(!0),a.stencil.setOp(s.REPLACE,s.REPLACE,s.REPLACE),a.stencil.setFunc(s.ALWAYS,u,4294967295),a.stencil.setClear(f),a.stencil.setLocked(!0),this.clearPass.enabled&&(this.renderToScreen?c.render(n,null):(c.render(n,e),c.render(n,t))),this.renderToScreen?(n.setRenderTarget(null),n.render(o,l)):(n.setRenderTarget(e),n.render(o,l),n.setRenderTarget(t),n.render(o,l)),a.color.setLocked(!1),a.depth.setLocked(!1),a.stencil.setLocked(!1),a.stencil.setFunc(s.EQUAL,1,4294967295),a.stencil.setOp(s.KEEP,s.KEEP,s.KEEP),a.stencil.setLocked(!0)}};function _E(n,e){const t=n.getContext();if(e<=0||typeof t.renderbufferStorageMultisample!="function")return 0;const i=t.getParameter(t.MAX_SAMPLES),r=Math.min(e,i);if(r<=0)return 0;const s=t.getParameter(t.RENDERBUFFER_BINDING),a=t.createRenderbuffer();try{return t.bindRenderbuffer(t.RENDERBUFFER,a),t.renderbufferStorageMultisample(t.RENDERBUFFER,r,t.RGBA8,1,1),r}catch{return 0}finally{t.bindRenderbuffer(t.RENDERBUFFER,s),t.deleteRenderbuffer(a)}}var nu=1/1e3,vE=1e3,xE=class{constructor(){this.startTime=performance.now(),this.previousTime=0,this.currentTime=0,this._delta=0,this._elapsed=0,this._fixedDelta=1e3/60,this.timescale=1,this.useFixedDelta=!1,this._autoReset=!1}get autoReset(){return this._autoReset}set autoReset(n){typeof document<"u"&&document.hidden!==void 0&&(n?document.addEventListener("visibilitychange",this):document.removeEventListener("visibilitychange",this),this._autoReset=n)}get delta(){return this._delta*nu}get fixedDelta(){return this._fixedDelta*nu}set fixedDelta(n){this._fixedDelta=n*vE}get elapsed(){return this._elapsed*nu}update(n){this.useFixedDelta?this._delta=this.fixedDelta:(this.previousTime=this.currentTime,this.currentTime=(n!==void 0?n:performance.now())-this.startTime,this._delta=this.currentTime-this.previousTime),this._delta*=this.timescale,this._elapsed+=this._delta}reset(){this._delta=0,this._elapsed=0,this.currentTime=performance.now()-this.startTime}getDelta(){return this.delta}getElapsed(){return this.elapsed}handleEvent(n){document.hidden||(this.currentTime=performance.now()-this.startTime)}dispose(){this.autoReset=!1}},bE=class{constructor(n=null,{depthBuffer:e=!0,stencilBuffer:t=!1,multisampling:i=0,frameBufferType:r=jt}={}){this.renderer=null,this.inputBuffer=this.createBuffer(e,t,r,i),this.outputBuffer=this.inputBuffer.clone(),this.copyPass=new mE,this.depthRenderTarget=null,this.passes=[],this.timer=new xE,this.autoRenderToScreen=!0,this.setRenderer(n)}get stableDepthTexture(){return this.depthRenderTarget===null?null:this.depthRenderTarget.depthTexture}get multisampling(){return this.inputBuffer.samples}set multisampling(n){const e=this.renderer===null?n:_E(this.renderer,n);this.multisampling!==e&&(this.inputBuffer.samples=e,this.outputBuffer.samples=e,this.inputBuffer.dispose(),this.outputBuffer.dispose())}getTimer(){return this.timer}getRenderer(){return this.renderer}setRenderer(n){if(this.renderer=n,n!==null){const e=n.getSize(new Xe),t=n.getContext().getContextAttributes().alpha,i=this.inputBuffer.texture.type;i===jt&&n.outputColorSpace===Tt&&(this.inputBuffer.texture.colorSpace=Tt,this.outputBuffer.texture.colorSpace=Tt,this.inputBuffer.dispose(),this.outputBuffer.dispose());const r=this.multisampling;this.multisampling=r,n.autoClear=!1,this.setSize(e.width,e.height);for(const s of this.passes)s.initialize(n,t,i)}}replaceRenderer(n,e=!0){const t=this.renderer,i=t.domElement.parentNode;return this.setRenderer(n),e&&i!==null&&(i.removeChild(t.domElement),i.appendChild(n.domElement)),t}createDepthTexture(){const n=new Gi;n.name="EffectComposer.InputDepth",this.inputBuffer.stencilBuffer?(n.format=lr,n.type=ks):n.type=li;const e=new Gi;e.format=n.format,e.type=n.type,e.name="EffectComposer.OutputDepth";const t=new Gi;t.format=n.format,t.type=n.type,t.name="EffectComposer.StableDepth",this.inputBuffer.depthTexture=n,this.outputBuffer.depthTexture=e,this.inputBuffer.dispose(),this.outputBuffer.dispose();const{width:i,height:r}=this.inputBuffer;this.depthRenderTarget=new $t(i,r,{depthBuffer:!0,stencilBuffer:this.inputBuffer.stencilBuffer,depthTexture:t})}blitDepthBuffer(n){const e=this.renderer,t=this.depthRenderTarget,i=e.properties,r=e.getContext();e.setRenderTarget(t);const s=i.get(n).__webglFramebuffer,a=i.get(t).__webglFramebuffer,o=n.stencilBuffer?r.DEPTH_BUFFER_BIT|r.STENCIL_BUFFER_BIT:r.DEPTH_BUFFER_BIT;r.bindFramebuffer(r.READ_FRAMEBUFFER,s),r.bindFramebuffer(r.DRAW_FRAMEBUFFER,a),r.blitFramebuffer(0,0,n.width,n.height,0,0,t.width,t.height,o,r.NEAREST),r.bindFramebuffer(r.READ_FRAMEBUFFER,null),r.bindFramebuffer(r.DRAW_FRAMEBUFFER,null),e.setRenderTarget(null)}deleteDepthTexture(){const n=this.stableDepthTexture;for(const e of this.passes)e.getDepthTexture()===n&&e.setDepthTexture(null);this.depthRenderTarget!==null&&(this.depthRenderTarget.dispose(),this.depthRenderTarget=null),this.inputBuffer.depthTexture!==null&&(this.inputBuffer.depthTexture.dispose(),this.inputBuffer.depthTexture=null),this.outputBuffer.depthTexture!==null&&(this.outputBuffer.depthTexture.dispose(),this.outputBuffer.depthTexture=null)}createBuffer(n,e,t,i){const r=this.renderer,s=r===null?new Xe:r.getDrawingBufferSize(new Xe),a=new $t(s.width,s.height,{minFilter:zt,magFilter:zt,samples:i,stencilBuffer:e,depthBuffer:n,type:t});return t===jt&&r!==null&&r.outputColorSpace===Tt&&(a.texture.colorSpace=Tt),a.texture.name="EffectComposer.Buffer",a.texture.generateMipmaps=!1,a}setMainScene(n){for(const e of this.passes)e.mainScene=n}setMainCamera(n){for(const e of this.passes)e.mainCamera=n}addPass(n,e){const t=this.passes,i=this.renderer,r=i.getDrawingBufferSize(new Xe),s=i.getContext().getContextAttributes().alpha,a=this.inputBuffer.texture.type;if(n.renderer=i,n.setSize(r.width,r.height),n.initialize(i,s,a),this.autoRenderToScreen&&(t.length>0&&(t[t.length-1].renderToScreen=!1),n.renderToScreen&&(this.autoRenderToScreen=!1)),e!==void 0?t.splice(e,0,n):t.push(n),this.autoRenderToScreen&&(t[t.length-1].renderToScreen=!0),n.needsDepthTexture||this.depthRenderTarget!==null)if(this.depthRenderTarget===null){this.createDepthTexture();for(const o of t)o.setDepthTexture(this.stableDepthTexture)}else n.setDepthTexture(this.stableDepthTexture)}removePass(n){const e=this.passes,t=e.indexOf(n);if(t!==-1&&e.splice(t,1).length>0){const s=this.stableDepthTexture;if(s!==null){const a=(l,c)=>l||c.needsDepthTexture;e.reduce(a,!1)||(n.getDepthTexture()===s&&n.setDepthTexture(null),this.deleteDepthTexture())}this.autoRenderToScreen&&t===e.length&&(n.renderToScreen=!1,e.length>0&&(e[e.length-1].renderToScreen=!0))}}removeAllPasses(){const n=this.passes;this.deleteDepthTexture(),n.length>0&&(this.autoRenderToScreen&&(n[n.length-1].renderToScreen=!1),this.passes=[])}render(n){const e=this.renderer,t=this.copyPass;let i=this.inputBuffer,r=this.outputBuffer,s,a=!1;n===void 0&&(this.timer.update(),n=this.timer.getDelta());for(const o of this.passes)if(o.enabled){if(o.render(e,i,r,n,a),o.needsDepthBlit&&this.depthRenderTarget!==null&&this.blitDepthBuffer(i),o.needsSwap){if(a){t.renderToScreen=o.renderToScreen;const l=e.getContext(),c=e.state.buffers.stencil;c.setFunc(l.NOTEQUAL,1,4294967295),t.render(e,i,r,n,a),c.setFunc(l.EQUAL,1,4294967295)}s=i,i=r,r=s}o instanceof gE?a=!0:o instanceof dE&&(a=!1)}}setSize(n,e,t){const i=this.renderer,r=i.getSize(new Xe);(n===void 0||e===void 0)&&(n=r.width,e=r.height),(r.width!==n||r.height!==e)&&i.setSize(n,e,t);const s=i.getDrawingBufferSize(new Xe);this.inputBuffer.setSize(s.width,s.height),this.outputBuffer.setSize(s.width,s.height),this.depthRenderTarget!==null&&this.depthRenderTarget.setSize(s.width,s.height);for(const a of this.passes)a.setSize(s.width,s.height)}reset(){this.dispose(),this.autoRenderToScreen=!0}dispose(){for(const n of this.passes)n.dispose();this.deleteDepthTexture(),this.inputBuffer.dispose(),this.outputBuffer.dispose(),this.copyPass.dispose(),this.timer.dispose(),this.passes=[],fi.fullscreenGeometry.dispose()}},Xr={NONE:0,DEPTH:1,CONVOLUTION:2},gt={FRAGMENT_HEAD:"FRAGMENT_HEAD",FRAGMENT_MAIN_UV:"FRAGMENT_MAIN_UV",FRAGMENT_MAIN_IMAGE:"FRAGMENT_MAIN_IMAGE",VERTEX_HEAD:"VERTEX_HEAD",VERTEX_MAIN_SUPPORT:"VERTEX_MAIN_SUPPORT"},ME=class{constructor(){this.shaderParts=new Map([[gt.FRAGMENT_HEAD,null],[gt.FRAGMENT_MAIN_UV,null],[gt.FRAGMENT_MAIN_IMAGE,null],[gt.VERTEX_HEAD,null],[gt.VERTEX_MAIN_SUPPORT,null]]),this.defines=new Map,this.uniforms=new Map,this.blendModes=new Map,this.extensions=new Set,this.attributes=Xr.NONE,this.varyings=new Set,this.uvTransformation=!1,this.readDepth=!1,this.colorSpace=zs}},iu=!1,Hp=class{constructor(n=null){this.originalMaterials=new Map,this.material=null,this.materials=null,this.materialsBackSide=null,this.materialsDoubleSide=null,this.materialsFlatShaded=null,this.materialsFlatShadedBackSide=null,this.materialsFlatShadedDoubleSide=null,this.setMaterial(n),this.meshCount=0,this.replaceMaterial=e=>{if(e.isMesh){let t;if(e.material.flatShading)switch(e.material.side){case En:t=this.materialsFlatShadedDoubleSide;break;case sn:t=this.materialsFlatShadedBackSide;break;default:t=this.materialsFlatShaded;break}else switch(e.material.side){case En:t=this.materialsDoubleSide;break;case sn:t=this.materialsBackSide;break;default:t=this.materials;break}this.originalMaterials.set(e,e.material),e.isSkinnedMesh?e.material=t[2]:e.isInstancedMesh?e.material=t[1]:e.material=t[0],++this.meshCount}}}cloneMaterial(n){if(!(n instanceof an))return n.clone();const e=n.uniforms,t=new Map;for(const r in e){const s=e[r].value;s.isRenderTargetTexture&&(e[r].value=null,t.set(r,s))}const i=n.clone();for(const r of t)e[r[0]].value=r[1],i.uniforms[r[0]].value=r[1];return i}setMaterial(n){if(this.disposeMaterials(),this.material=n,n!==null){const e=this.materials=[this.cloneMaterial(n),this.cloneMaterial(n),this.cloneMaterial(n)];for(const t of e)t.uniforms=Object.assign({},n.uniforms),t.side=Hi;e[2].skinning=!0,this.materialsBackSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.side=sn,i}),this.materialsDoubleSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.side=En,i}),this.materialsFlatShaded=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.flatShading=!0,i}),this.materialsFlatShadedBackSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.flatShading=!0,i.side=sn,i}),this.materialsFlatShadedDoubleSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.flatShading=!0,i.side=En,i})}}render(n,e,t){const i=n.shadowMap.enabled;if(n.shadowMap.enabled=!1,iu){const r=this.originalMaterials;this.meshCount=0,e.traverse(this.replaceMaterial),n.render(e,t);for(const s of r)s[0].material=s[1];this.meshCount!==r.size&&r.clear()}else{const r=e.overrideMaterial;e.overrideMaterial=this.material,n.render(e,t),e.overrideMaterial=r}n.shadowMap.enabled=i}disposeMaterials(){if(this.material!==null){const n=this.materials.concat(this.materialsBackSide).concat(this.materialsDoubleSide).concat(this.materialsFlatShaded).concat(this.materialsFlatShadedBackSide).concat(this.materialsFlatShadedDoubleSide);for(const e of n)e.dispose()}}dispose(){this.originalMaterials.clear(),this.disposeMaterials()}static get workaroundEnabled(){return iu}static set workaroundEnabled(n){iu=n}},sr=-1,wi=class extends hi{constructor(n=null,e=sr,t=sr,i=1){super(),n!==null&&this.addEventListener("change",()=>n.setSize(this.baseSize.width,this.baseSize.height)),this.baseSize=new Xe(1,1),this.preferredSize=new Xe(e,t),this.target=this.preferredSize,this.s=i,this.effectiveSize=new Xe,this.addEventListener("change",()=>this.updateEffectiveSize()),this.updateEffectiveSize()}updateEffectiveSize(){const n=this.baseSize,e=this.preferredSize,t=this.effectiveSize,i=this.scale;e.width!==sr?t.width=e.width:e.height!==sr?t.width=Math.round(e.height*(n.width/Math.max(n.height,1))):t.width=Math.round(n.width*i),e.height!==sr?t.height=e.height:e.width!==sr?t.height=Math.round(e.width/Math.max(n.width/Math.max(n.height,1),1)):t.height=Math.round(n.height*i)}get width(){return this.effectiveSize.width}set width(n){this.preferredWidth=n}get height(){return this.effectiveSize.height}set height(n){this.preferredHeight=n}getWidth(){return this.width}getHeight(){return this.height}get scale(){return this.s}set scale(n){this.s!==n&&(this.s=n,this.preferredSize.setScalar(sr),this.dispatchEvent({type:"change"}))}getScale(){return this.scale}setScale(n){this.scale=n}get baseWidth(){return this.baseSize.width}set baseWidth(n){this.baseSize.width!==n&&(this.baseSize.width=n,this.dispatchEvent({type:"change"}))}getBaseWidth(){return this.baseWidth}setBaseWidth(n){this.baseWidth=n}get baseHeight(){return this.baseSize.height}set baseHeight(n){this.baseSize.height!==n&&(this.baseSize.height=n,this.dispatchEvent({type:"change"}))}getBaseHeight(){return this.baseHeight}setBaseHeight(n){this.baseHeight=n}setBaseSize(n,e){(this.baseSize.width!==n||this.baseSize.height!==e)&&(this.baseSize.set(n,e),this.dispatchEvent({type:"change"}))}get preferredWidth(){return this.preferredSize.width}set preferredWidth(n){this.preferredSize.width!==n&&(this.preferredSize.width=n,this.dispatchEvent({type:"change"}))}getPreferredWidth(){return this.preferredWidth}setPreferredWidth(n){this.preferredWidth=n}get preferredHeight(){return this.preferredSize.height}set preferredHeight(n){this.preferredSize.height!==n&&(this.preferredSize.height=n,this.dispatchEvent({type:"change"}))}getPreferredHeight(){return this.preferredHeight}setPreferredHeight(n){this.preferredHeight=n}setPreferredSize(n,e){(this.preferredSize.width!==n||this.preferredSize.height!==e)&&(this.preferredSize.set(n,e),this.dispatchEvent({type:"change"}))}copy(n){this.s=n.scale,this.baseSize.set(n.baseWidth,n.baseHeight),this.preferredSize.set(n.preferredWidth,n.preferredHeight),this.dispatchEvent({type:"change"})}static get AUTO_SIZE(){return sr}},ct={ADD:0,ALPHA:1,AVERAGE:2,COLOR:3,COLOR_BURN:4,COLOR_DODGE:5,DARKEN:6,DIFFERENCE:7,DIVIDE:8,DST:9,EXCLUSION:10,HARD_LIGHT:11,HARD_MIX:12,HUE:13,INVERT:14,INVERT_RGB:15,LIGHTEN:16,LINEAR_BURN:17,LINEAR_DODGE:18,LINEAR_LIGHT:19,LUMINOSITY:20,MULTIPLY:21,NEGATION:22,NORMAL:23,OVERLAY:24,PIN_LIGHT:25,REFLECT:26,SATURATION:27,SCREEN:28,SOFT_LIGHT:29,SRC:30,SUBTRACT:31,VIVID_LIGHT:32},SE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",yE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return mix(dst,src,src.a*opacity);}",TE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=(dst.rgb+src.rgb)*0.5;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",EE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(b.xy,a.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",wE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=dst.rgb,b=src.rgb;vec3 c=mix(step(0.0,b)*(1.0-min(vec3(1.0),(1.0-a)/max(b,1e-9))),vec3(1.0),step(1.0,a));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",AE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=dst.rgb,b=src.rgb;vec3 c=step(0.0,a)*mix(min(vec3(1.0),a/max(1.0-b,1e-9)),vec3(1.0),step(1.0,b));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",RE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=min(dst.rgb,src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",CE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=abs(dst.rgb-src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",PE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb/max(src.rgb,1e-9);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",DE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb-2.0*dst.rgb*src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",UE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=min(dst.rgb,1.0);vec3 b=min(src.rgb,1.0);vec3 c=mix(2.0*a*b,1.0-2.0*(1.0-a)*(1.0-b),step(0.5,b));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",LE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=step(1.0,dst.rgb+src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",IE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(b.x,a.yz));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",FE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(1.0-src.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",NE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=src.rgb*max(1.0-dst.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",OE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(dst.rgb,src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",BE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=clamp(src.rgb+dst.rgb-1.0,0.0,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",kE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=min(dst.rgb+src.rgb,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",zE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=clamp(2.0*src.rgb+dst.rgb-1.0,0.0,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",GE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(a.xy,b.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",HE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb*src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",VE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(1.0-abs(1.0-dst.rgb-src.rgb),0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",WE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return mix(dst,src,opacity);}",XE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=2.0*src.rgb*dst.rgb;vec3 b=1.0-2.0*(1.0-src.rgb)*(1.0-dst.rgb);vec3 c=mix(a,b,step(0.5,dst.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",jE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 src2=2.0*src.rgb;vec3 c=mix(mix(src2,dst.rgb,step(0.5*dst.rgb,src.rgb)),max(src2-1.0,vec3(0.0)),step(dst.rgb,src2-1.0));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",YE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=min(dst.rgb*dst.rgb/max(1.0-src.rgb,1e-9),1.0);vec3 c=mix(a,src.rgb,step(1.0,src.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",qE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(a.x,b.y,a.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",KE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb-min(dst.rgb*src.rgb,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",ZE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 src2=2.0*src.rgb;vec3 d=dst.rgb+(src2-1.0);vec3 w=step(0.5,src.rgb);vec3 a=dst.rgb-(1.0-src2)*dst.rgb*(1.0-dst.rgb);vec3 b=mix(d*(sqrt(dst.rgb)-dst.rgb),d*dst.rgb*((16.0*dst.rgb-12.0)*dst.rgb+3.0),w*(1.0-step(0.25,dst.rgb)));vec3 c=mix(a,b,w);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",$E="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return src;}",JE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(dst.rgb-src.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",QE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=mix(max(1.0-min((1.0-dst.rgb)/(2.0*src.rgb),1.0),0.0),min(dst.rgb/(2.0*(1.0-src.rgb)),1.0),step(0.5,src.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",e2=new Map([[ct.ADD,SE],[ct.ALPHA,yE],[ct.AVERAGE,TE],[ct.COLOR,EE],[ct.COLOR_BURN,wE],[ct.COLOR_DODGE,AE],[ct.DARKEN,RE],[ct.DIFFERENCE,CE],[ct.DIVIDE,PE],[ct.DST,null],[ct.EXCLUSION,DE],[ct.HARD_LIGHT,UE],[ct.HARD_MIX,LE],[ct.HUE,IE],[ct.INVERT,FE],[ct.INVERT_RGB,NE],[ct.LIGHTEN,OE],[ct.LINEAR_BURN,BE],[ct.LINEAR_DODGE,kE],[ct.LINEAR_LIGHT,zE],[ct.LUMINOSITY,GE],[ct.MULTIPLY,HE],[ct.NEGATION,VE],[ct.NORMAL,WE],[ct.OVERLAY,XE],[ct.PIN_LIGHT,jE],[ct.REFLECT,YE],[ct.SATURATION,qE],[ct.SCREEN,KE],[ct.SOFT_LIGHT,ZE],[ct.SRC,$E],[ct.SUBTRACT,JE],[ct.VIVID_LIGHT,QE]]),t2=class extends hi{constructor(n,e=1){super(),this._blendFunction=n,this.opacity=new vt(e)}getOpacity(){return this.opacity.value}setOpacity(n){this.opacity.value=n}get blendFunction(){return this._blendFunction}set blendFunction(n){this._blendFunction=n,this.dispatchEvent({type:"change"})}getBlendFunction(){return this.blendFunction}setBlendFunction(n){this.blendFunction=n}getShaderCode(){return e2.get(this.blendFunction)}},n2=class extends hi{constructor(n,e,{attributes:t=Xr.NONE,blendFunction:i=ct.NORMAL,defines:r=new Map,uniforms:s=new Map,extensions:a=null,vertexShader:o=null}={}){super(),this.name=n,this.renderer=null,this.attributes=t,this.fragmentShader=e,this.vertexShader=o,this.defines=r,this.uniforms=s,this.extensions=a,this.blendMode=new t2(i),this.blendMode.addEventListener("change",l=>this.setChanged()),this._inputColorSpace=zs,this._outputColorSpace=bi}get inputColorSpace(){return this._inputColorSpace}set inputColorSpace(n){this._inputColorSpace=n,this.setChanged()}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(n){this._outputColorSpace=n,this.setChanged()}set mainScene(n){}set mainCamera(n){}getName(){return this.name}setRenderer(n){this.renderer=n}getDefines(){return this.defines}getUniforms(){return this.uniforms}getExtensions(){return this.extensions}getBlendMode(){return this.blendMode}getAttributes(){return this.attributes}setAttributes(n){this.attributes=n,this.setChanged()}getFragmentShader(){return this.fragmentShader}setFragmentShader(n){this.fragmentShader=n,this.setChanged()}getVertexShader(){return this.vertexShader}setVertexShader(n){this.vertexShader=n,this.setChanged()}setChanged(){this.dispatchEvent({type:"change"})}setDepthTexture(n,e=Ka){}update(n,e,t){}setSize(n,e){}initialize(n,e,t){}dispose(){for(const n of Object.keys(this)){const e=this[n];(e instanceof $t||e instanceof Yi||e instanceof Zt||e instanceof fi)&&this[n].dispose()}}},Ef={MEDIUM:2,LARGE:3},i2=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;void main(){vec4 sum=texture2D(inputBuffer,vUv0);sum+=texture2D(inputBuffer,vUv1);sum+=texture2D(inputBuffer,vUv2);sum+=texture2D(inputBuffer,vUv3);gl_FragColor=sum*0.25;
#include <colorspace_fragment>
}`,r2="uniform vec4 texelSize;uniform float kernel;uniform float scale;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;void main(){vec2 uv=position.xy*0.5+0.5;vec2 dUv=(texelSize.xy*vec2(kernel)+texelSize.zw)*scale;vUv0=vec2(uv.x-dUv.x,uv.y+dUv.y);vUv1=vec2(uv.x+dUv.x,uv.y+dUv.y);vUv2=vec2(uv.x+dUv.x,uv.y-dUv.y);vUv3=vec2(uv.x-dUv.x,uv.y-dUv.y);gl_Position=vec4(position.xy,1.0,1.0);}",s2=[new Float32Array([0,0]),new Float32Array([0,1,1]),new Float32Array([0,1,1,2]),new Float32Array([0,1,2,2,3]),new Float32Array([0,1,2,3,4,4,5]),new Float32Array([0,1,2,3,4,5,7,8,9,10])],a2=class extends an{constructor(n=new Dt){super({name:"KawaseBlurMaterial",uniforms:{inputBuffer:new vt(null),texelSize:new vt(new Dt),scale:new vt(1),kernel:new vt(0)},blending:Mn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:i2,vertexShader:r2}),this.setTexelSize(n.x,n.y),this.kernelSize=Ef.MEDIUM}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.inputBuffer=n}get kernelSequence(){return s2[this.kernelSize]}get scale(){return this.uniforms.scale.value}set scale(n){this.uniforms.scale.value=n}getScale(){return this.uniforms.scale.value}setScale(n){this.uniforms.scale.value=n}getKernel(){return null}get kernel(){return this.uniforms.kernel.value}set kernel(n){this.uniforms.kernel.value=n}setKernel(n){this.kernel=n}setTexelSize(n,e){this.uniforms.texelSize.value.set(n,e,n*.5,e*.5)}setSize(n,e){const t=1/n,i=1/e;this.uniforms.texelSize.value.set(t,i,t*.5,i*.5)}},o2=class extends fi{constructor({kernelSize:n=Ef.MEDIUM,resolutionScale:e=.5,width:t=wi.AUTO_SIZE,height:i=wi.AUTO_SIZE,resolutionX:r=t,resolutionY:s=i}={}){super("KawaseBlurPass"),this.renderTargetA=new $t(1,1,{depthBuffer:!1}),this.renderTargetA.texture.name="Blur.Target.A",this.renderTargetB=this.renderTargetA.clone(),this.renderTargetB.texture.name="Blur.Target.B";const a=this.resolution=new wi(this,r,s,e);a.addEventListener("change",o=>this.setSize(a.baseWidth,a.baseHeight)),this._blurMaterial=new a2,this._blurMaterial.kernelSize=n,this.copyMaterial=new hg}getResolution(){return this.resolution}get blurMaterial(){return this._blurMaterial}set blurMaterial(n){this._blurMaterial=n}get dithering(){return this.copyMaterial.dithering}set dithering(n){this.copyMaterial.dithering=n}get kernelSize(){return this.blurMaterial.kernelSize}set kernelSize(n){this.blurMaterial.kernelSize=n}get width(){return this.resolution.width}set width(n){this.resolution.preferredWidth=n}get height(){return this.resolution.height}set height(n){this.resolution.preferredHeight=n}get scale(){return this.blurMaterial.scale}set scale(n){this.blurMaterial.scale=n}getScale(){return this.blurMaterial.scale}setScale(n){this.blurMaterial.scale=n}getKernelSize(){return this.kernelSize}setKernelSize(n){this.kernelSize=n}getResolutionScale(){return this.resolution.scale}setResolutionScale(n){this.resolution.scale=n}render(n,e,t,i,r){const s=this.scene,a=this.camera,o=this.renderTargetA,l=this.renderTargetB,c=this.blurMaterial,u=c.kernelSequence;let f=e;this.fullscreenMaterial=c;for(let h=0,d=u.length;h<d;++h){const g=(h&1)===0?o:l;c.kernel=u[h],c.inputBuffer=f.texture,n.setRenderTarget(g),n.render(s,a),f=g}this.fullscreenMaterial=this.copyMaterial,this.copyMaterial.inputBuffer=f.texture,n.setRenderTarget(this.renderToScreen?null:t),n.render(s,a)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e);const i=t.width,r=t.height;this.renderTargetA.setSize(i,r),this.renderTargetB.setSize(i,r),this.blurMaterial.setSize(n,e)}initialize(n,e,t){t!==void 0&&(this.renderTargetA.texture.type=t,this.renderTargetB.texture.type=t,t!==jt?(this.blurMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1",this.copyMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1"):n!==null&&n.outputColorSpace===Tt&&(this.renderTargetA.texture.colorSpace=Tt,this.renderTargetB.texture.colorSpace=Tt))}static get AUTO_SIZE(){return wi.AUTO_SIZE}},l2=`#include <common>
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
}`,c2=class extends an{constructor(n=!1,e=null){super({name:"LuminanceMaterial",defines:{THREE_REVISION:qa.replace(/\D+/g,"")},uniforms:{inputBuffer:new vt(null),threshold:new vt(0),smoothing:new vt(1),range:new vt(null)},blending:Mn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:l2,vertexShader:ug}),this.colorOutput=n,this.luminanceRange=e}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.uniforms.inputBuffer.value=n}get threshold(){return this.uniforms.threshold.value}set threshold(n){this.smoothing>0||n>0?this.defines.THRESHOLD="1":delete this.defines.THRESHOLD,this.uniforms.threshold.value=n}getThreshold(){return this.threshold}setThreshold(n){this.threshold=n}get smoothing(){return this.uniforms.smoothing.value}set smoothing(n){this.threshold>0||n>0?this.defines.THRESHOLD="1":delete this.defines.THRESHOLD,this.uniforms.smoothing.value=n}getSmoothingFactor(){return this.smoothing}setSmoothingFactor(n){this.smoothing=n}get useThreshold(){return this.threshold>0||this.smoothing>0}set useThreshold(n){}get colorOutput(){return this.defines.COLOR!==void 0}set colorOutput(n){n?this.defines.COLOR="1":delete this.defines.COLOR,this.needsUpdate=!0}isColorOutputEnabled(n){return this.colorOutput}setColorOutputEnabled(n){this.colorOutput=n}get useRange(){return this.luminanceRange!==null}set useRange(n){this.luminanceRange=null}get luminanceRange(){return this.uniforms.range.value}set luminanceRange(n){n!==null?this.defines.RANGE="1":delete this.defines.RANGE,this.uniforms.range.value=n,this.needsUpdate=!0}getLuminanceRange(){return this.luminanceRange}setLuminanceRange(n){this.luminanceRange=n}},u2=class extends fi{constructor({renderTarget:n,luminanceRange:e,colorOutput:t,resolutionScale:i=1,width:r=wi.AUTO_SIZE,height:s=wi.AUTO_SIZE,resolutionX:a=r,resolutionY:o=s}={}){super("LuminancePass"),this.fullscreenMaterial=new c2(t,e),this.needsSwap=!1,this.renderTarget=n,this.renderTarget===void 0&&(this.renderTarget=new $t(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="LuminancePass.Target");const l=this.resolution=new wi(this,a,o,i);l.addEventListener("change",c=>this.setSize(l.baseWidth,l.baseHeight))}get texture(){return this.renderTarget.texture}getTexture(){return this.renderTarget.texture}getResolution(){return this.resolution}render(n,e,t,i,r){const s=this.fullscreenMaterial;s.inputBuffer=e.texture,n.setRenderTarget(this.renderToScreen?null:this.renderTarget),n.render(this.scene,this.camera)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e),this.renderTarget.setSize(t.width,t.height)}initialize(n,e,t){t!==void 0&&t!==jt&&(this.renderTarget.texture.type=t,this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1")}},h2=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
#define WEIGHT_INNER 0.125
#define WEIGHT_OUTER 0.05556
varying vec2 vUv;varying vec2 vUv00;varying vec2 vUv01;varying vec2 vUv02;varying vec2 vUv03;varying vec2 vUv04;varying vec2 vUv05;varying vec2 vUv06;varying vec2 vUv07;varying vec2 vUv08;varying vec2 vUv09;varying vec2 vUv10;varying vec2 vUv11;float clampToBorder(const in vec2 uv){return float(uv.s>=0.0&&uv.s<=1.0&&uv.t>=0.0&&uv.t<=1.0);}void main(){vec4 c=vec4(0.0);vec4 w=WEIGHT_INNER*vec4(clampToBorder(vUv00),clampToBorder(vUv01),clampToBorder(vUv02),clampToBorder(vUv03));c+=w.x*texture2D(inputBuffer,vUv00);c+=w.y*texture2D(inputBuffer,vUv01);c+=w.z*texture2D(inputBuffer,vUv02);c+=w.w*texture2D(inputBuffer,vUv03);w=WEIGHT_OUTER*vec4(clampToBorder(vUv04),clampToBorder(vUv05),clampToBorder(vUv06),clampToBorder(vUv07));c+=w.x*texture2D(inputBuffer,vUv04);c+=w.y*texture2D(inputBuffer,vUv05);c+=w.z*texture2D(inputBuffer,vUv06);c+=w.w*texture2D(inputBuffer,vUv07);w=WEIGHT_OUTER*vec4(clampToBorder(vUv08),clampToBorder(vUv09),clampToBorder(vUv10),clampToBorder(vUv11));c+=w.x*texture2D(inputBuffer,vUv08);c+=w.y*texture2D(inputBuffer,vUv09);c+=w.z*texture2D(inputBuffer,vUv10);c+=w.w*texture2D(inputBuffer,vUv11);c+=WEIGHT_OUTER*texture2D(inputBuffer,vUv);gl_FragColor=c;
#include <colorspace_fragment>
}`,f2="uniform vec2 texelSize;varying vec2 vUv;varying vec2 vUv00;varying vec2 vUv01;varying vec2 vUv02;varying vec2 vUv03;varying vec2 vUv04;varying vec2 vUv05;varying vec2 vUv06;varying vec2 vUv07;varying vec2 vUv08;varying vec2 vUv09;varying vec2 vUv10;varying vec2 vUv11;void main(){vUv=position.xy*0.5+0.5;vUv00=vUv+texelSize*vec2(-1.0,1.0);vUv01=vUv+texelSize*vec2(1.0,1.0);vUv02=vUv+texelSize*vec2(-1.0,-1.0);vUv03=vUv+texelSize*vec2(1.0,-1.0);vUv04=vUv+texelSize*vec2(-2.0,2.0);vUv05=vUv+texelSize*vec2(0.0,2.0);vUv06=vUv+texelSize*vec2(2.0,2.0);vUv07=vUv+texelSize*vec2(-2.0,0.0);vUv08=vUv+texelSize*vec2(2.0,0.0);vUv09=vUv+texelSize*vec2(-2.0,-2.0);vUv10=vUv+texelSize*vec2(0.0,-2.0);vUv11=vUv+texelSize*vec2(2.0,-2.0);gl_Position=vec4(position.xy,1.0,1.0);}",d2=class extends an{constructor(){super({name:"DownsamplingMaterial",uniforms:{inputBuffer:new vt(null),texelSize:new vt(new Xe)},blending:Mn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:h2,vertexShader:f2})}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setSize(n,e){this.uniforms.texelSize.value.set(1/n,1/e)}},p2=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;uniform mediump sampler2D supportBuffer;
#else
uniform lowp sampler2D inputBuffer;uniform lowp sampler2D supportBuffer;
#endif
uniform float radius;varying vec2 vUv;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;varying vec2 vUv4;varying vec2 vUv5;varying vec2 vUv6;varying vec2 vUv7;void main(){vec4 c=vec4(0.0);c+=texture2D(inputBuffer,vUv0)*0.0625;c+=texture2D(inputBuffer,vUv1)*0.125;c+=texture2D(inputBuffer,vUv2)*0.0625;c+=texture2D(inputBuffer,vUv3)*0.125;c+=texture2D(inputBuffer,vUv)*0.25;c+=texture2D(inputBuffer,vUv4)*0.125;c+=texture2D(inputBuffer,vUv5)*0.0625;c+=texture2D(inputBuffer,vUv6)*0.125;c+=texture2D(inputBuffer,vUv7)*0.0625;vec4 baseColor=texture2D(supportBuffer,vUv);gl_FragColor=mix(baseColor,c,radius);
#include <colorspace_fragment>
}`,m2="uniform vec2 texelSize;varying vec2 vUv;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;varying vec2 vUv4;varying vec2 vUv5;varying vec2 vUv6;varying vec2 vUv7;void main(){vUv=position.xy*0.5+0.5;vUv0=vUv+texelSize*vec2(-1.0,1.0);vUv1=vUv+texelSize*vec2(0.0,1.0);vUv2=vUv+texelSize*vec2(1.0,1.0);vUv3=vUv+texelSize*vec2(-1.0,0.0);vUv4=vUv+texelSize*vec2(1.0,0.0);vUv5=vUv+texelSize*vec2(-1.0,-1.0);vUv6=vUv+texelSize*vec2(0.0,-1.0);vUv7=vUv+texelSize*vec2(1.0,-1.0);gl_Position=vec4(position.xy,1.0,1.0);}",g2=class extends an{constructor(){super({name:"UpsamplingMaterial",uniforms:{inputBuffer:new vt(null),supportBuffer:new vt(null),texelSize:new vt(new Xe),radius:new vt(.85)},blending:Mn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:p2,vertexShader:m2})}set inputBuffer(n){this.uniforms.inputBuffer.value=n}set supportBuffer(n){this.uniforms.supportBuffer.value=n}get radius(){return this.uniforms.radius.value}set radius(n){this.uniforms.radius.value=n}setSize(n,e){this.uniforms.texelSize.value.set(1/n,1/e)}},_2=class extends fi{constructor(){super("MipmapBlurPass"),this.needsSwap=!1,this.renderTarget=new $t(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="Upsampling.Mipmap0",this.downsamplingMipmaps=[],this.upsamplingMipmaps=[],this.downsamplingMaterial=new d2,this.upsamplingMaterial=new g2,this.resolution=new Xe}get texture(){return this.renderTarget.texture}get levels(){return this.downsamplingMipmaps.length}set levels(n){if(this.levels!==n){const e=this.renderTarget;this.dispose(),this.downsamplingMipmaps=[],this.upsamplingMipmaps=[];for(let t=0;t<n;++t){const i=e.clone();i.texture.name="Downsampling.Mipmap"+t,this.downsamplingMipmaps.push(i)}this.upsamplingMipmaps.push(e);for(let t=1,i=n-1;t<i;++t){const r=e.clone();r.texture.name="Upsampling.Mipmap"+t,this.upsamplingMipmaps.push(r)}this.setSize(this.resolution.x,this.resolution.y)}}get radius(){return this.upsamplingMaterial.radius}set radius(n){this.upsamplingMaterial.radius=n}render(n,e,t,i,r){const{scene:s,camera:a}=this,{downsamplingMaterial:o,upsamplingMaterial:l}=this,{downsamplingMipmaps:c,upsamplingMipmaps:u}=this;let f=e;this.fullscreenMaterial=o;for(let h=0,d=c.length;h<d;++h){const g=c[h];o.setSize(f.width,f.height),o.inputBuffer=f.texture,n.setRenderTarget(g),n.render(s,a),f=g}this.fullscreenMaterial=l;for(let h=u.length-1;h>=0;--h){const d=u[h];l.setSize(f.width,f.height),l.inputBuffer=f.texture,l.supportBuffer=c[h].texture,n.setRenderTarget(d),n.render(s,a),f=d}}setSize(n,e){const t=this.resolution;t.set(n,e);let i=t.width,r=t.height;for(let s=0,a=this.downsamplingMipmaps.length;s<a;++s)i=Math.round(i*.5),r=Math.round(r*.5),this.downsamplingMipmaps[s].setSize(i,r),s<this.upsamplingMipmaps.length&&this.upsamplingMipmaps[s].setSize(i,r)}initialize(n,e,t){if(t!==void 0){const i=this.downsamplingMipmaps.concat(this.upsamplingMipmaps);for(const r of i)r.texture.type=t;if(t!==jt)this.downsamplingMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1",this.upsamplingMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1";else if(n!==null&&n.outputColorSpace===Tt)for(const r of i)r.texture.colorSpace=Tt}}dispose(){super.dispose();for(const n of this.downsamplingMipmaps.concat(this.upsamplingMipmaps))n.dispose()}},v2=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D map;
#else
uniform lowp sampler2D map;
#endif
uniform float intensity;void mainImage(const in vec4 inputColor,const in vec2 uv,out vec4 outputColor){outputColor=texture2D(map,uv)*intensity;}`,x2=class extends n2{constructor({blendFunction:n=ct.SCREEN,luminanceThreshold:e=1,luminanceSmoothing:t=.03,mipmapBlur:i=!0,intensity:r=1,radius:s=.85,levels:a=8,kernelSize:o=Ef.LARGE,resolutionScale:l=.5,width:c=wi.AUTO_SIZE,height:u=wi.AUTO_SIZE,resolutionX:f=c,resolutionY:h=u}={}){super("BloomEffect",v2,{blendFunction:n,uniforms:new Map([["map",new vt(null)],["intensity",new vt(r)]])}),this.renderTarget=new $t(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="Bloom.Target",this.blurPass=new o2({kernelSize:o}),this.luminancePass=new u2({colorOutput:!0}),this.luminanceMaterial.threshold=e,this.luminanceMaterial.smoothing=t,this.mipmapBlurPass=new _2,this.mipmapBlurPass.enabled=i,this.mipmapBlurPass.radius=s,this.mipmapBlurPass.levels=a,this.uniforms.get("map").value=i?this.mipmapBlurPass.texture:this.renderTarget.texture;const d=this.resolution=new wi(this,f,h,l);d.addEventListener("change",g=>this.setSize(d.baseWidth,d.baseHeight))}get texture(){return this.mipmapBlurPass.enabled?this.mipmapBlurPass.texture:this.renderTarget.texture}getTexture(){return this.texture}getResolution(){return this.resolution}getBlurPass(){return this.blurPass}getLuminancePass(){return this.luminancePass}get luminanceMaterial(){return this.luminancePass.fullscreenMaterial}getLuminanceMaterial(){return this.luminancePass.fullscreenMaterial}get width(){return this.resolution.width}set width(n){this.resolution.preferredWidth=n}get height(){return this.resolution.height}set height(n){this.resolution.preferredHeight=n}get dithering(){return this.blurPass.dithering}set dithering(n){this.blurPass.dithering=n}get kernelSize(){return this.blurPass.kernelSize}set kernelSize(n){this.blurPass.kernelSize=n}get distinction(){return console.warn(this.name,"distinction was removed"),1}set distinction(n){console.warn(this.name,"distinction was removed")}get intensity(){return this.uniforms.get("intensity").value}set intensity(n){this.uniforms.get("intensity").value=n}getIntensity(){return this.intensity}setIntensity(n){this.intensity=n}getResolutionScale(){return this.resolution.scale}setResolutionScale(n){this.resolution.scale=n}update(n,e,t){const i=this.renderTarget,r=this.luminancePass;r.enabled?(r.render(n,e),this.mipmapBlurPass.enabled?this.mipmapBlurPass.render(n,r.renderTarget):this.blurPass.render(n,r.renderTarget,i)):this.mipmapBlurPass.enabled?this.mipmapBlurPass.render(n,e):this.blurPass.render(n,e,i)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e),this.renderTarget.setSize(t.width,t.height),this.blurPass.resolution.copy(t),this.luminancePass.setSize(n,e),this.mipmapBlurPass.setSize(n,e)}initialize(n,e,t){this.blurPass.initialize(n,e,t),this.luminancePass.initialize(n,e,t),this.mipmapBlurPass.initialize(n,e,t),t!==void 0&&(this.renderTarget.texture.type=t,n!==null&&n.outputColorSpace===Tt&&(this.renderTarget.texture.colorSpace=Tt))}},b2=class extends fi{constructor(n,e,t=null){super("RenderPass",n,e),this.needsSwap=!1,this.needsDepthBlit=!0,this.clearPass=new fg,this.overrideMaterialManager=t===null?null:new Hp(t),this.ignoreBackground=!1,this.skipShadowMapUpdate=!1,this.selection=null}set mainScene(n){this.scene=n}set mainCamera(n){this.camera=n}get renderToScreen(){return super.renderToScreen}set renderToScreen(n){super.renderToScreen=n,this.clearPass.renderToScreen=n}get overrideMaterial(){const n=this.overrideMaterialManager;return n!==null?n.material:null}set overrideMaterial(n){const e=this.overrideMaterialManager;n!==null?e!==null?e.setMaterial(n):this.overrideMaterialManager=new Hp(n):e!==null&&(e.dispose(),this.overrideMaterialManager=null)}getOverrideMaterial(){return this.overrideMaterial}setOverrideMaterial(n){this.overrideMaterial=n}get clear(){return this.clearPass.enabled}set clear(n){this.clearPass.enabled=n}getSelection(){return this.selection}setSelection(n){this.selection=n}isBackgroundDisabled(){return this.ignoreBackground}setBackgroundDisabled(n){this.ignoreBackground=n}isShadowMapDisabled(){return this.skipShadowMapUpdate}setShadowMapDisabled(n){this.skipShadowMapUpdate=n}getClearPass(){return this.clearPass}render(n,e,t,i,r){const s=this.scene,a=this.camera,o=this.selection,l=a.layers.mask,c=s.background,u=n.shadowMap.autoUpdate,f=this.renderToScreen?null:e;o!==null&&a.layers.set(o.getLayer()),this.skipShadowMapUpdate&&(n.shadowMap.autoUpdate=!1),(this.ignoreBackground||this.clearPass.overrideClearColor!==null)&&(s.background=null),this.clearPass.enabled&&this.clearPass.render(n,e),n.setRenderTarget(f),this.overrideMaterialManager!==null?this.overrideMaterialManager.render(n,s,a):n.render(s,a),a.layers.mask=l,s.background=c,n.shadowMap.autoUpdate=u}},M2=`#include <common>
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
}`,S2="uniform vec2 resolution;uniform vec2 texelSize;uniform float cameraNear;uniform float cameraFar;uniform float aspect;uniform float time;varying vec2 vUv;VERTEX_HEAD void main(){vUv=position.xy*0.5+0.5;VERTEX_MAIN_SUPPORT gl_Position=vec4(position.xy,1.0,1.0);}",y2=class extends an{constructor(n,e,t,i,r=!1){super({name:"EffectMaterial",defines:{THREE_REVISION:qa.replace(/\D+/g,""),DEPTH_PACKING:"0",ENCODE_OUTPUT:"1"},uniforms:{inputBuffer:new vt(null),depthBuffer:new vt(null),resolution:new vt(new Xe),texelSize:new vt(new Xe),cameraNear:new vt(.3),cameraFar:new vt(1e3),aspect:new vt(1),time:new vt(0)},blending:Mn,toneMapped:!1,depthWrite:!1,depthTest:!1,dithering:r}),n&&this.setShaderParts(n),e&&this.setDefines(e),t&&this.setUniforms(t),this.copyCameraSettings(i)}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.uniforms.inputBuffer.value=n}get depthBuffer(){return this.uniforms.depthBuffer.value}set depthBuffer(n){this.uniforms.depthBuffer.value=n}get depthPacking(){return Number(this.defines.DEPTH_PACKING)}set depthPacking(n){this.defines.DEPTH_PACKING=n.toFixed(0),this.needsUpdate=!0}setDepthBuffer(n,e=Ka){this.depthBuffer=n,this.depthPacking=e}setShaderData(n){this.setShaderParts(n.shaderParts),this.setDefines(n.defines),this.setUniforms(n.uniforms),this.setExtensions(n.extensions)}setShaderParts(n){return this.fragmentShader=M2.replace(gt.FRAGMENT_HEAD,n.get(gt.FRAGMENT_HEAD)||"").replace(gt.FRAGMENT_MAIN_UV,n.get(gt.FRAGMENT_MAIN_UV)||"").replace(gt.FRAGMENT_MAIN_IMAGE,n.get(gt.FRAGMENT_MAIN_IMAGE)||""),this.vertexShader=S2.replace(gt.VERTEX_HEAD,n.get(gt.VERTEX_HEAD)||"").replace(gt.VERTEX_MAIN_SUPPORT,n.get(gt.VERTEX_MAIN_SUPPORT)||""),this.needsUpdate=!0,this}setDefines(n){for(const e of n.entries())this.defines[e[0]]=e[1];return this.needsUpdate=!0,this}setUniforms(n){for(const e of n.entries())this.uniforms[e[0]]=e[1];return this}setExtensions(n){this.extensions={};for(const e of n)this.extensions[e]=!0;return this}get encodeOutput(){return this.defines.ENCODE_OUTPUT!==void 0}set encodeOutput(n){this.encodeOutput!==n&&(n?this.defines.ENCODE_OUTPUT="1":delete this.defines.ENCODE_OUTPUT,this.needsUpdate=!0)}isOutputEncodingEnabled(n){return this.encodeOutput}setOutputEncodingEnabled(n){this.encodeOutput=n}get time(){return this.uniforms.time.value}set time(n){this.uniforms.time.value=n}setDeltaTime(n){this.uniforms.time.value+=n}adoptCameraSettings(n){this.copyCameraSettings(n)}copyCameraSettings(n){n&&(this.uniforms.cameraNear.value=n.near,this.uniforms.cameraFar.value=n.far,n instanceof kn?this.defines.PERSPECTIVE_CAMERA="1":delete this.defines.PERSPECTIVE_CAMERA,this.needsUpdate=!0)}setSize(n,e){const t=this.uniforms;t.resolution.value.set(n,e),t.texelSize.value.set(1/n,1/e),t.aspect.value=n/e}static get Section(){return gt}};function Vp(n,e,t){for(const i of e){const r="$1"+n+i.charAt(0).toUpperCase()+i.slice(1),s=new RegExp("([^\\.])(\\b"+i+"\\b)","g");for(const a of t.entries())a[1]!==null&&t.set(a[0],a[1].replace(s,r))}}function T2(n,e,t){let i=e.getFragmentShader(),r=e.getVertexShader();const s=i!==void 0&&/mainImage/.test(i),a=i!==void 0&&/mainUv/.test(i);if(t.attributes|=e.getAttributes(),i===void 0)throw new Error(`Missing fragment shader (${e.name})`);if(a&&(t.attributes&Xr.CONVOLUTION)!==0)throw new Error(`Effects that transform UVs are incompatible with convolution effects (${e.name})`);if(!s&&!a)throw new Error(`Could not find mainImage or mainUv function (${e.name})`);{const o=/\w+\s+(\w+)\([\w\s,]*\)\s*{/g,l=t.shaderParts;let c=l.get(gt.FRAGMENT_HEAD)||"",u=l.get(gt.FRAGMENT_MAIN_UV)||"",f=l.get(gt.FRAGMENT_MAIN_IMAGE)||"",h=l.get(gt.VERTEX_HEAD)||"",d=l.get(gt.VERTEX_MAIN_SUPPORT)||"";const g=new Set,m=new Set;if(a&&(u+=`	${n}MainUv(UV);
`,t.uvTransformation=!0),r!==null&&/mainSupport/.test(r)){const v=/mainSupport *\([\w\s]*?uv\s*?\)/.test(r);d+=`	${n}MainSupport(`,d+=v?`vUv);
`:`);
`;for(const M of r.matchAll(/(?:varying\s+\w+\s+([\S\s]*?);)/g))for(const y of M[1].split(/\s*,\s*/))t.varyings.add(y),g.add(y),m.add(y);for(const M of r.matchAll(o))m.add(M[1])}for(const v of i.matchAll(o))m.add(v[1]);for(const v of e.defines.keys())m.add(v.replace(/\([\w\s,]*\)/g,""));for(const v of e.uniforms.keys())m.add(v);m.delete("while"),m.delete("for"),m.delete("if"),e.uniforms.forEach((v,M)=>t.uniforms.set(n+M.charAt(0).toUpperCase()+M.slice(1),v)),e.defines.forEach((v,M)=>t.defines.set(n+M.charAt(0).toUpperCase()+M.slice(1),v));const p=new Map([["fragment",i],["vertex",r]]);Vp(n,m,t.defines),Vp(n,m,p),i=p.get("fragment"),r=p.get("vertex");const _=e.blendMode;if(t.blendModes.set(_.blendFunction,_),s){e.inputColorSpace!==null&&e.inputColorSpace!==t.colorSpace&&(f+=e.inputColorSpace===Tt?`color0 = sRGBTransferOETF(color0);
	`:`color0 = sRGBToLinear(color0);
	`),e.outputColorSpace!==bi?t.colorSpace=e.outputColorSpace:e.inputColorSpace!==null&&(t.colorSpace=e.inputColorSpace);const v=/MainImage *\([\w\s,]*?depth[\w\s,]*?\)/;f+=`${n}MainImage(color0, UV, `,(t.attributes&Xr.DEPTH)!==0&&v.test(i)&&(f+="depth, ",t.readDepth=!0),f+=`color1);
	`;const M=n+"BlendOpacity";t.uniforms.set(M,_.opacity),f+=`color0 = blend${_.blendFunction}(color0, color1, ${M});

	`,c+=`uniform float ${M};

`}if(c+=i+`
`,r!==null&&(h+=r+`
`),l.set(gt.FRAGMENT_HEAD,c),l.set(gt.FRAGMENT_MAIN_UV,u),l.set(gt.FRAGMENT_MAIN_IMAGE,f),l.set(gt.VERTEX_HEAD,h),l.set(gt.VERTEX_MAIN_SUPPORT,d),e.extensions!==null)for(const v of e.extensions)t.extensions.add(v)}}var E2=class extends fi{constructor(n,...e){super("EffectPass"),this.fullscreenMaterial=new y2(null,null,null,n),this.listener=t=>this.handleEvent(t),this.effects=[],this.setEffects(e),this.skipRendering=!1,this.minTime=1,this.maxTime=Number.POSITIVE_INFINITY,this.timeScale=1}set mainScene(n){for(const e of this.effects)e.mainScene=n}set mainCamera(n){this.fullscreenMaterial.copyCameraSettings(n);for(const e of this.effects)e.mainCamera=n}get encodeOutput(){return this.fullscreenMaterial.encodeOutput}set encodeOutput(n){this.fullscreenMaterial.encodeOutput=n}get dithering(){return this.fullscreenMaterial.dithering}set dithering(n){const e=this.fullscreenMaterial;e.dithering=n,e.needsUpdate=!0}setEffects(n){for(const e of this.effects)e.removeEventListener("change",this.listener);this.effects=n.sort((e,t)=>t.attributes-e.attributes);for(const e of this.effects)e.addEventListener("change",this.listener)}updateMaterial(){const n=new ME;let e=0;for(const a of this.effects)if(a.blendMode.blendFunction===ct.DST)n.attributes|=a.getAttributes()&Xr.DEPTH;else{if((n.attributes&a.getAttributes()&Xr.CONVOLUTION)!==0)throw new Error(`Convolution effects cannot be merged (${a.name})`);T2("e"+e++,a,n)}let t=n.shaderParts.get(gt.FRAGMENT_HEAD),i=n.shaderParts.get(gt.FRAGMENT_MAIN_IMAGE),r=n.shaderParts.get(gt.FRAGMENT_MAIN_UV);const s=/\bblend\b/g;for(const a of n.blendModes.values())t+=a.getShaderCode().replace(s,`blend${a.blendFunction}`)+`
`;(n.attributes&Xr.DEPTH)!==0?(n.readDepth&&(i=`float depth = readDepth(UV);

	`+i),this.needsDepthTexture=this.getDepthTexture()===null):this.needsDepthTexture=!1,n.colorSpace===Tt&&(i+=`color0 = sRGBToLinear(color0);
	`),n.uvTransformation?(r=`vec2 transformedUv = vUv;
`+r,n.defines.set("UV","transformedUv")):n.defines.set("UV","vUv"),n.shaderParts.set(gt.FRAGMENT_HEAD,t),n.shaderParts.set(gt.FRAGMENT_MAIN_IMAGE,i),n.shaderParts.set(gt.FRAGMENT_MAIN_UV,r);for(const[a,o]of n.shaderParts)o!==null&&n.shaderParts.set(a,o.trim().replace(/^#/,`
#`));this.skipRendering=e===0,this.needsSwap=!this.skipRendering,this.fullscreenMaterial.setShaderData(n)}recompile(){this.updateMaterial()}getDepthTexture(){return this.fullscreenMaterial.depthBuffer}setDepthTexture(n,e=Ka){this.fullscreenMaterial.depthBuffer=n,this.fullscreenMaterial.depthPacking=e;for(const t of this.effects)t.setDepthTexture(n,e)}render(n,e,t,i,r){for(const s of this.effects)s.update(n,e,i);if(!this.skipRendering||this.renderToScreen){const s=this.fullscreenMaterial;s.inputBuffer=e.texture,s.time+=i*this.timeScale,n.setRenderTarget(this.renderToScreen?null:t),n.render(this.scene,this.camera)}}setSize(n,e){this.fullscreenMaterial.setSize(n,e);for(const t of this.effects)t.setSize(n,e)}initialize(n,e,t){this.renderer=n;for(const i of this.effects)i.initialize(n,e,t);this.updateMaterial(),t!==void 0&&t!==jt&&(this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1")}dispose(){super.dispose();for(const n of this.effects)n.removeEventListener("change",this.listener),n.dispose()}handleEvent(n){switch(n.type){case"change":this.recompile();break}}};const dg=(n,e)=>{if(typeof n=="number"){if(e===3)return{mode:"rgb",r:(n>>8&15|n>>4&240)/255,g:(n>>4&15|n&240)/255,b:(n&15|n<<4&240)/255};if(e===4)return{mode:"rgb",r:(n>>12&15|n>>8&240)/255,g:(n>>8&15|n>>4&240)/255,b:(n>>4&15|n&240)/255,alpha:(n&15|n<<4&240)/255};if(e===6)return{mode:"rgb",r:(n>>16&255)/255,g:(n>>8&255)/255,b:(n&255)/255};if(e===8)return{mode:"rgb",r:(n>>24&255)/255,g:(n>>16&255)/255,b:(n>>8&255)/255,alpha:(n&255)/255}}},w2={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},A2=n=>dg(w2[n.toLowerCase()],6),R2=/^#?([0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{4}|[0-9a-f]{3})$/i,C2=n=>{let e;return(e=n.match(R2))?dg(parseInt(e[1],16),e[1].length):void 0},gr="([+-]?\\d*\\.?\\d+(?:[eE][+-]?\\d+)?)",Oa=`${gr}%`,wf=`(?:${gr}%|${gr})`,P2=`(?:${gr}(deg|grad|rad|turn)|${gr})`,Ys="\\s*,\\s*",D2=new RegExp(`^rgba?\\(\\s*${gr}${Ys}${gr}${Ys}${gr}\\s*(?:,\\s*${wf}\\s*)?\\)$`),U2=new RegExp(`^rgba?\\(\\s*${Oa}${Ys}${Oa}${Ys}${Oa}\\s*(?:,\\s*${wf}\\s*)?\\)$`),L2=n=>{let e={mode:"rgb"},t;if(t=n.match(D2))t[1]!==void 0&&(e.r=t[1]/255),t[2]!==void 0&&(e.g=t[2]/255),t[3]!==void 0&&(e.b=t[3]/255);else if(t=n.match(U2))t[1]!==void 0&&(e.r=t[1]/100),t[2]!==void 0&&(e.g=t[2]/100),t[3]!==void 0&&(e.b=t[3]/100);else return;return t[4]!==void 0?e.alpha=Math.max(0,Math.min(1,t[4]/100)):t[5]!==void 0&&(e.alpha=Math.max(0,Math.min(1,+t[5]))),e},I2=(n,e)=>n===void 0?void 0:typeof n!="object"?V2(n):n.mode!==void 0?n:e?{...n,mode:e}:void 0,Af=(n="rgb")=>e=>(e=I2(e,n))!==void 0?e.mode===n?e:yi[e.mode][n]?yi[e.mode][n](e):n==="rgb"?yi[e.mode].rgb(e):yi.rgb[n](yi[e.mode].rgb(e)):void 0,yi={},pg={},El=[],mg={},F2=n=>n,bt=n=>(yi[n.mode]={...yi[n.mode],...n.toMode},Object.keys(n.fromMode||{}).forEach(e=>{yi[e]||(yi[e]={}),yi[e][n.mode]=n.fromMode[e]}),n.ranges||(n.ranges={}),n.difference||(n.difference={}),n.channels.forEach(e=>{if(n.ranges[e]===void 0&&(n.ranges[e]=[0,1]),!n.interpolate[e])throw new Error(`Missing interpolator for: ${e}`);typeof n.interpolate[e]=="function"&&(n.interpolate[e]={use:n.interpolate[e]}),n.interpolate[e].fixup||(n.interpolate[e].fixup=F2)}),pg[n.mode]=n,(n.parse||[]).forEach(e=>{N2(e,n.mode)}),Af(n.mode)),gg=n=>pg[n],N2=(n,e)=>{if(typeof n=="string"){if(!e)throw new Error("'mode' required when 'parser' is a string");mg[n]=e}else typeof n=="function"&&El.indexOf(n)<0&&El.push(n)},zh=/[^\x00-\x7F]|[a-zA-Z_]/,O2=/[^\x00-\x7F]|[-\w]/,Ae={Function:"function",Ident:"ident",Number:"number",Percentage:"percentage",ParenClose:")",None:"none",Hue:"hue",Alpha:"alpha"};let Qe=0;function Wo(n){let e=n[Qe],t=n[Qe+1];return e==="-"||e==="+"?/\d/.test(t)||t==="."&&/\d/.test(n[Qe+2]):e==="."?/\d/.test(t):/\d/.test(e)}function Gh(n){if(Qe>=n.length)return!1;let e=n[Qe];if(zh.test(e))return!0;if(e==="-"){if(n.length-Qe<2)return!1;let t=n[Qe+1];return!!(t==="-"||zh.test(t))}return!1}const B2={deg:1,rad:180/Math.PI,grad:9/10,turn:360};function Ea(n){let e="";if((n[Qe]==="-"||n[Qe]==="+")&&(e+=n[Qe++]),e+=Xo(n),n[Qe]==="."&&/\d/.test(n[Qe+1])&&(e+=n[Qe++]+Xo(n)),(n[Qe]==="e"||n[Qe]==="E")&&((n[Qe+1]==="-"||n[Qe+1]==="+")&&/\d/.test(n[Qe+2])?e+=n[Qe++]+n[Qe++]+Xo(n):/\d/.test(n[Qe+1])&&(e+=n[Qe++]+Xo(n))),Gh(n)){let t=wl(n);return t==="deg"||t==="rad"||t==="turn"||t==="grad"?{type:Ae.Hue,value:e*B2[t]}:void 0}return n[Qe]==="%"?(Qe++,{type:Ae.Percentage,value:+e}):{type:Ae.Number,value:+e}}function Xo(n){let e="";for(;/\d/.test(n[Qe]);)e+=n[Qe++];return e}function wl(n){let e="";for(;Qe<n.length&&O2.test(n[Qe]);)e+=n[Qe++];return e}function k2(n){let e=wl(n);return n[Qe]==="("?(Qe++,{type:Ae.Function,value:e}):e==="none"?{type:Ae.None,value:void 0}:{type:Ae.Ident,value:e}}function z2(n=""){let e=n.trim(),t=[],i;for(Qe=0;Qe<e.length;){if(i=e[Qe++],i===`
`||i==="	"||i===" "){for(;Qe<e.length&&(e[Qe]===`
`||e[Qe]==="	"||e[Qe]===" ");)Qe++;continue}if(i===",")return;if(i===")"){t.push({type:Ae.ParenClose});continue}if(i==="+"){if(Qe--,Wo(e)){t.push(Ea(e));continue}return}if(i==="-"){if(Qe--,Wo(e)){t.push(Ea(e));continue}if(Gh(e)){t.push({type:Ae.Ident,value:wl(e)});continue}return}if(i==="."){if(Qe--,Wo(e)){t.push(Ea(e));continue}return}if(i==="/"){for(;Qe<e.length&&(e[Qe]===`
`||e[Qe]==="	"||e[Qe]===" ");)Qe++;let r;if(Wo(e)&&(r=Ea(e),r.type!==Ae.Hue)){t.push({type:Ae.Alpha,value:r});continue}if(Gh(e)&&wl(e)==="none"){t.push({type:Ae.Alpha,value:{type:Ae.None,value:void 0}});continue}return}if(/\d/.test(i)){Qe--,t.push(Ea(e));continue}if(zh.test(i)){Qe--,t.push(k2(e));continue}return}return t}function G2(n){n._i=0;let e=n[n._i++];if(!e||e.type!==Ae.Function||e.value!=="color"||(e=n[n._i++],e.type!==Ae.Ident))return;const t=mg[e.value];if(!t)return;const i={mode:t},r=_g(n,!1);if(!r)return;const s=gg(t).channels;for(let a=0,o,l;a<s.length;a++)o=r[a],l=s[a],o.type!==Ae.None&&(i[l]=o.type===Ae.Number?o.value:o.value/100,l==="alpha"&&(i[l]=Math.max(0,Math.min(1,i[l]))));return i}function _g(n,e){const t=[];let i;for(;n._i<n.length;){if(i=n[n._i++],i.type===Ae.None||i.type===Ae.Number||i.type===Ae.Alpha||i.type===Ae.Percentage||e&&i.type===Ae.Hue){t.push(i);continue}if(i.type===Ae.ParenClose){if(n._i<n.length)return;continue}return}if(!(t.length<3||t.length>4)){if(t.length===4){if(t[3].type!==Ae.Alpha)return;t[3]=t[3].value}return t.length===3&&t.push({type:Ae.None,value:void 0}),t.every(r=>r.type!==Ae.Alpha)?t:void 0}}function H2(n,e){n._i=0;let t=n[n._i++];if(!t||t.type!==Ae.Function)return;let i=_g(n,e);if(i)return i.unshift(t.value),i}const V2=n=>{if(typeof n!="string")return;const e=z2(n),t=e?H2(e,!0):void 0;let i,r=0,s=El.length;for(;r<s;)if((i=El[r++](n,t))!==void 0)return i;return e?G2(e):void 0};function W2(n,e){if(!e||e[0]!=="rgb"&&e[0]!=="rgba")return;const t={mode:"rgb"},[,i,r,s,a]=e;if(!(i.type===Ae.Hue||r.type===Ae.Hue||s.type===Ae.Hue))return i.type!==Ae.None&&(t.r=i.type===Ae.Number?i.value/255:i.value/100),r.type!==Ae.None&&(t.g=r.type===Ae.Number?r.value/255:r.value/100),s.type!==Ae.None&&(t.b=s.type===Ae.Number?s.value/255:s.value/100),a.type!==Ae.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ae.Number?a.value:a.value/100))),t}const X2=n=>n==="transparent"?{mode:"rgb",r:0,g:0,b:0,alpha:0}:void 0,j2=(n,e,t)=>n+t*(e-n),Y2=n=>{let e=[];for(let t=0;t<n.length-1;t++){let i=n[t],r=n[t+1];i===void 0&&r===void 0?e.push(void 0):i!==void 0&&r!==void 0?e.push([i,r]):e.push(i!==void 0?[i,i]:[r,r])}return e},q2=n=>e=>{let t=Y2(e);return i=>{let r=i*t.length,s=i>=1?t.length-1:Math.max(Math.floor(r),0),a=t[s];return a===void 0?void 0:n(a[0],a[1],r-s)}},Be=q2(j2),en=n=>{let e=!1,t=n.map(i=>i!==void 0?(e=!0,i):1);return e?t:n},Js={mode:"rgb",channels:["r","g","b","alpha"],parse:[W2,C2,L2,A2,X2,"srgb"],serialize:"srgb",interpolate:{r:Be,g:Be,b:Be,alpha:{use:Be,fixup:en}},gamut:!0,white:{r:1,g:1,b:1},black:{r:0,g:0,b:0}},ru=(n=0)=>Math.pow(Math.abs(n),563/256)*Math.sign(n),Wp=n=>{let e=ru(n.r),t=ru(n.g),i=ru(n.b),r={mode:"xyz65",x:.5766690429101305*e+.1855582379065463*t+.1882286462349947*i,y:.297344975250536*e+.6273635662554661*t+.0752914584939979*i,z:.0270313613864123*e+.0706888525358272*t+.9913375368376386*i};return n.alpha!==void 0&&(r.alpha=n.alpha),r},su=n=>Math.pow(Math.abs(n),256/563)*Math.sign(n),Xp=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"a98",r:su(n*2.0415879038107465-e*.5650069742788597-.3447313507783297*t),g:su(n*-.9692436362808798+e*1.8759675015077206+.0415550574071756*t),b:su(n*.0134442806320312-e*.1183623922310184+1.0151749943912058*t)};return i!==void 0&&(r.alpha=i),r},au=(n=0)=>{const e=Math.abs(n);return e<=.04045?n/12.92:(Math.sign(n)||1)*Math.pow((e+.055)/1.055,2.4)},Qs=({r:n,g:e,b:t,alpha:i})=>{let r={mode:"lrgb",r:au(n),g:au(e),b:au(t)};return i!==void 0&&(r.alpha=i),r},Jr=n=>{let{r:e,g:t,b:i,alpha:r}=Qs(n),s={mode:"xyz65",x:.4123907992659593*e+.357584339383878*t+.1804807884018343*i,y:.2126390058715102*e+.715168678767756*t+.0721923153607337*i,z:.0193308187155918*e+.119194779794626*t+.9505321522496607*i};return r!==void 0&&(s.alpha=r),s},ou=(n=0)=>{const e=Math.abs(n);return e>.0031308?(Math.sign(n)||1)*(1.055*Math.pow(e,1/2.4)-.055):n*12.92},ea=({r:n,g:e,b:t,alpha:i},r="rgb")=>{let s={mode:r,r:ou(n),g:ou(e),b:ou(t)};return i!==void 0&&(s.alpha=i),s},Qr=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=ea({r:n*3.2409699419045226-e*1.537383177570094-.4986107602930034*t,g:n*-.9692436362808796+e*1.8759675015077204+.0415550574071756*t,b:n*.0556300796969936-e*.2039769588889765+1.0569715142428784*t});return i!==void 0&&(r.alpha=i),r},K2={...Js,mode:"a98",parse:["a98-rgb"],serialize:"a98-rgb",fromMode:{rgb:n=>Xp(Jr(n)),xyz65:Xp},toMode:{rgb:n=>Qr(Wp(n)),xyz65:Wp}},hn=n=>(n=n%360)<0?n+360:n,Z2=(n,e)=>n.map((t,i,r)=>{if(t===void 0)return t;let s=hn(t);return i===0||n[i-1]===void 0?s:e(s-hn(r[i-1]))}).reduce((t,i)=>!t.length||i===void 0||t[t.length-1]===void 0?(t.push(i),t):(t.push(i+t[t.length-1]),t),[]),qi=n=>Z2(n,e=>Math.abs(e)<=180?e:e-360*Math.sign(e)),rn=[-.14861,1.78277,-.29227,-.90649,1.97294,0],$2=Math.PI/180,J2=180/Math.PI;let jp=rn[3]*rn[4],Yp=rn[1]*rn[4],qp=rn[1]*rn[2]-rn[0]*rn[3];const Q2=({r:n,g:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(qp*t+n*jp-e*Yp)/(qp+jp-Yp),s=t-r,a=(rn[4]*(e-r)-rn[2]*s)/rn[3],o={mode:"cubehelix",l:r,s:r===0||r===1?void 0:Math.sqrt(s*s+a*a)/(rn[4]*r*(1-r))};return o.s&&(o.h=Math.atan2(a,s)*J2-120),i!==void 0&&(o.alpha=i),o},ew=({h:n,s:e,l:t,alpha:i})=>{let r={mode:"rgb"};n=(n===void 0?0:n+120)*$2,t===void 0&&(t=0);let s=e===void 0?0:e*t*(1-t),a=Math.cos(n),o=Math.sin(n);return r.r=t+s*(rn[0]*a+rn[1]*o),r.g=t+s*(rn[2]*a+rn[3]*o),r.b=t+s*(rn[4]*a+rn[5]*o),i!==void 0&&(r.alpha=i),r},zl=(n,e)=>{if(n.h===void 0||e.h===void 0||!n.s||!e.s)return 0;let t=hn(n.h),i=hn(e.h),r=Math.sin((i-t+360)/2*Math.PI/180);return 2*Math.sqrt(n.s*e.s)*r},tw=(n,e)=>{if(n.h===void 0||e.h===void 0)return 0;let t=hn(n.h),i=hn(e.h);return Math.abs(i-t)>180?t-(i-360*Math.sign(i-t)):i-t},Gl=(n,e)=>{if(n.h===void 0||e.h===void 0||!n.c||!e.c)return 0;let t=hn(n.h),i=hn(e.h),r=Math.sin((i-t+360)/2*Math.PI/180);return 2*Math.sqrt(n.c*e.c)*r},Ki=n=>{let e=n.reduce((i,r)=>{if(r!==void 0){let s=r*Math.PI/180;i.sin+=Math.sin(s),i.cos+=Math.cos(s)}return i},{sin:0,cos:0}),t=Math.atan2(e.sin,e.cos)*180/Math.PI;return t<0?360+t:t},nw={mode:"cubehelix",channels:["h","s","l","alpha"],parse:["--cubehelix"],serialize:"--cubehelix",ranges:{h:[0,360],s:[0,4.614],l:[0,1]},fromMode:{rgb:Q2},toMode:{rgb:ew},interpolate:{h:{use:Be,fixup:qi},s:Be,l:Be,alpha:{use:Be,fixup:en}},difference:{h:zl},average:{h:Ki}},Mr=({l:n,a:e,b:t,alpha:i},r="lch")=>{e===void 0&&(e=0),t===void 0&&(t=0);let s=Math.sqrt(e*e+t*t),a={mode:r,l:n,c:s};return s&&(a.h=hn(Math.atan2(t,e)*180/Math.PI)),i!==void 0&&(a.alpha=i),a},Sr=({l:n,c:e,h:t,alpha:i},r="lab")=>{t===void 0&&(t=0);let s={mode:r,l:n,a:e?e*Math.cos(t/180*Math.PI):0,b:e?e*Math.sin(t/180*Math.PI):0};return i!==void 0&&(s.alpha=i),s},vg=Math.pow(29,3)/Math.pow(3,3),xg=Math.pow(6,3)/Math.pow(29,3),Yt={X:.3457/.3585,Y:1,Z:(1-.3457-.3585)/.3585},Ns={X:.3127/.329,Y:1,Z:(1-.3127-.329)/.329};let lu=n=>Math.pow(n,3)>xg?Math.pow(n,3):(116*n-16)/vg;const bg=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(n+16)/116,s=e/500+r,a=r-t/200,o={mode:"xyz65",x:lu(s)*Ns.X,y:lu(r)*Ns.Y,z:lu(a)*Ns.Z};return i!==void 0&&(o.alpha=i),o},Hl=n=>Qr(bg(n)),cu=n=>n>xg?Math.cbrt(n):(vg*n+16)/116,Mg=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=cu(n/Ns.X),s=cu(e/Ns.Y),a=cu(t/Ns.Z),o={mode:"lab65",l:116*s-16,a:500*(r-s),b:200*(s-a)};return i!==void 0&&(o.alpha=i),o},Vl=n=>{let e=Mg(Jr(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},Al=1,Sg=1,Ya=26/180*Math.PI,Rl=Math.cos(Ya),Cl=Math.sin(Ya),yg=100/Math.log(139/100),Hh=({l:n,c:e,h:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"lab65",l:(Math.exp(n*Al/yg)-1)/.0039},s=(Math.exp(.0435*e*Sg*Al)-1)/.075,a=s*Math.cos(t/180*Math.PI-Ya),o=s*Math.sin(t/180*Math.PI-Ya);return r.a=a*Rl-o/.83*Cl,r.b=a*Cl+o/.83*Rl,i!==void 0&&(r.alpha=i),r},Vh=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=e*Rl+t*Cl,s=.83*(t*Rl-e*Cl),a=Math.sqrt(r*r+s*s),o={mode:"dlch",l:yg/Al*Math.log(1+.0039*n),c:Math.log(1+.075*a)/(.0435*Sg*Al)};return o.c&&(o.h=hn((Math.atan2(s,r)+Ya)/Math.PI*180)),i!==void 0&&(o.alpha=i),o},Kp=n=>Hh(Mr(n,"dlch")),Zp=n=>Sr(Vh(n),"dlab"),iw={mode:"dlab",parse:["--din99o-lab"],serialize:"--din99o-lab",toMode:{lab65:Kp,rgb:n=>Hl(Kp(n))},fromMode:{lab65:Zp,rgb:n=>Zp(Vl(n))},channels:["l","a","b","alpha"],ranges:{l:[0,100],a:[-40.09,45.501],b:[-40.469,44.344]},interpolate:{l:Be,a:Be,b:Be,alpha:{use:Be,fixup:en}}},rw={mode:"dlch",parse:["--din99o-lch"],serialize:"--din99o-lch",toMode:{lab65:Hh,dlab:n=>Sr(n,"dlab"),rgb:n=>Hl(Hh(n))},fromMode:{lab65:Vh,dlab:n=>Mr(n,"dlch"),rgb:n=>Vh(Vl(n))},channels:["l","c","h","alpha"],ranges:{l:[0,100],c:[0,51.484],h:[0,360]},interpolate:{l:Be,c:Be,h:{use:Be,fixup:qi},alpha:{use:Be,fixup:en}},difference:{h:Gl},average:{h:Ki}};function sw({h:n,s:e,i:t,alpha:i}){n=hn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.abs(n/60%2-1),s;switch(Math.floor(n/60)){case 0:s={r:t*(1+e*(3/(2-r)-1)),g:t*(1+e*(3*(1-r)/(2-r)-1)),b:t*(1-e)};break;case 1:s={r:t*(1+e*(3*(1-r)/(2-r)-1)),g:t*(1+e*(3/(2-r)-1)),b:t*(1-e)};break;case 2:s={r:t*(1-e),g:t*(1+e*(3/(2-r)-1)),b:t*(1+e*(3*(1-r)/(2-r)-1))};break;case 3:s={r:t*(1-e),g:t*(1+e*(3*(1-r)/(2-r)-1)),b:t*(1+e*(3/(2-r)-1))};break;case 4:s={r:t*(1+e*(3*(1-r)/(2-r)-1)),g:t*(1-e),b:t*(1+e*(3/(2-r)-1))};break;case 5:s={r:t*(1+e*(3/(2-r)-1)),g:t*(1-e),b:t*(1+e*(3*(1-r)/(2-r)-1))};break;default:s={r:t*(1-e),g:t*(1-e),b:t*(1-e)}}return s.mode="rgb",i!==void 0&&(s.alpha=i),s}function aw({r:n,g:e,b:t,alpha:i}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsi",s:n+e+t===0?0:1-3*s/(n+e+t),i:(n+e+t)/3};return r-s!==0&&(a.h=(r===n?(e-t)/(r-s)+(e<t)*6:r===e?(t-n)/(r-s)+2:(n-e)/(r-s)+4)*60),i!==void 0&&(a.alpha=i),a}const ow={mode:"hsi",toMode:{rgb:sw},parse:["--hsi"],serialize:"--hsi",fromMode:{rgb:aw},channels:["h","s","i","alpha"],ranges:{h:[0,360]},gamut:"rgb",interpolate:{h:{use:Be,fixup:qi},s:Be,i:Be,alpha:{use:Be,fixup:en}},difference:{h:zl},average:{h:Ki}};function lw({h:n,s:e,l:t,alpha:i}){n=hn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let r=t+e*(t<.5?t:1-t),s=r-(r-t)*2*Math.abs(n/60%2-1),a;switch(Math.floor(n/60)){case 0:a={r,g:s,b:2*t-r};break;case 1:a={r:s,g:r,b:2*t-r};break;case 2:a={r:2*t-r,g:r,b:s};break;case 3:a={r:2*t-r,g:s,b:r};break;case 4:a={r:s,g:2*t-r,b:r};break;case 5:a={r,g:2*t-r,b:s};break;default:a={r:2*t-r,g:2*t-r,b:2*t-r}}return a.mode="rgb",i!==void 0&&(a.alpha=i),a}function cw({r:n,g:e,b:t,alpha:i}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsl",s:r===s?0:(r-s)/(1-Math.abs(r+s-1)),l:.5*(r+s)};return r-s!==0&&(a.h=(r===n?(e-t)/(r-s)+(e<t)*6:r===e?(t-n)/(r-s)+2:(n-e)/(r-s)+4)*60),i!==void 0&&(a.alpha=i),a}const uw=(n,e)=>{switch(e){case"deg":return+n;case"rad":return n/Math.PI*180;case"grad":return n/10*9;case"turn":return n*360}},hw=new RegExp(`^hsla?\\(\\s*${P2}${Ys}${Oa}${Ys}${Oa}\\s*(?:,\\s*${wf}\\s*)?\\)$`),fw=n=>{let e=n.match(hw);if(!e)return;let t={mode:"hsl"};return e[3]!==void 0?t.h=+e[3]:e[1]!==void 0&&e[2]!==void 0&&(t.h=uw(e[1],e[2])),e[4]!==void 0&&(t.s=Math.min(Math.max(0,e[4]/100),1)),e[5]!==void 0&&(t.l=Math.min(Math.max(0,e[5]/100),1)),e[6]!==void 0?t.alpha=Math.max(0,Math.min(1,e[6]/100)):e[7]!==void 0&&(t.alpha=Math.max(0,Math.min(1,+e[7]))),t};function dw(n,e){if(!e||e[0]!=="hsl"&&e[0]!=="hsla")return;const t={mode:"hsl"},[,i,r,s,a]=e;if(i.type!==Ae.None){if(i.type===Ae.Percentage)return;t.h=i.value}if(r.type!==Ae.None){if(r.type===Ae.Hue)return;t.s=r.value/100}if(s.type!==Ae.None){if(s.type===Ae.Hue)return;t.l=s.value/100}return a.type!==Ae.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ae.Number?a.value:a.value/100))),t}const Tg={mode:"hsl",toMode:{rgb:lw},fromMode:{rgb:cw},channels:["h","s","l","alpha"],ranges:{h:[0,360]},gamut:"rgb",parse:[dw,fw],serialize:n=>`hsl(${n.h!==void 0?n.h:"none"} ${n.s!==void 0?n.s*100+"%":"none"} ${n.l!==void 0?n.l*100+"%":"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:Be,fixup:qi},s:Be,l:Be,alpha:{use:Be,fixup:en}},difference:{h:zl},average:{h:Ki}};function Eg({h:n,s:e,v:t,alpha:i}){n=hn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.abs(n/60%2-1),s;switch(Math.floor(n/60)){case 0:s={r:t,g:t*(1-e*r),b:t*(1-e)};break;case 1:s={r:t*(1-e*r),g:t,b:t*(1-e)};break;case 2:s={r:t*(1-e),g:t,b:t*(1-e*r)};break;case 3:s={r:t*(1-e),g:t*(1-e*r),b:t};break;case 4:s={r:t*(1-e*r),g:t*(1-e),b:t};break;case 5:s={r:t,g:t*(1-e),b:t*(1-e*r)};break;default:s={r:t*(1-e),g:t*(1-e),b:t*(1-e)}}return s.mode="rgb",i!==void 0&&(s.alpha=i),s}function wg({r:n,g:e,b:t,alpha:i}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsv",s:r===0?0:1-s/r,v:r};return r-s!==0&&(a.h=(r===n?(e-t)/(r-s)+(e<t)*6:r===e?(t-n)/(r-s)+2:(n-e)/(r-s)+4)*60),i!==void 0&&(a.alpha=i),a}const Ag={mode:"hsv",toMode:{rgb:Eg},parse:["--hsv"],serialize:"--hsv",fromMode:{rgb:wg},channels:["h","s","v","alpha"],ranges:{h:[0,360]},gamut:"rgb",interpolate:{h:{use:Be,fixup:qi},s:Be,v:Be,alpha:{use:Be,fixup:en}},difference:{h:zl},average:{h:Ki}};function pw({h:n,w:e,b:t,alpha:i}){if(e===void 0&&(e=0),t===void 0&&(t=0),e+t>1){let r=e+t;e/=r,t/=r}return Eg({h:n,s:t===1?1:1-e/(1-t),v:1-t,alpha:i})}function mw(n){let e=wg(n);if(e===void 0)return;let t=e.s!==void 0?e.s:0,i=e.v!==void 0?e.v:0,r={mode:"hwb",w:(1-t)*i,b:1-i};return e.h!==void 0&&(r.h=e.h),e.alpha!==void 0&&(r.alpha=e.alpha),r}function gw(n,e){if(!e||e[0]!=="hwb")return;const t={mode:"hwb"},[,i,r,s,a]=e;if(i.type!==Ae.None){if(i.type===Ae.Percentage)return;t.h=i.value}if(r.type!==Ae.None){if(r.type===Ae.Hue)return;t.w=r.value/100}if(s.type!==Ae.None){if(s.type===Ae.Hue)return;t.b=s.value/100}return a.type!==Ae.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ae.Number?a.value:a.value/100))),t}const _w={mode:"hwb",toMode:{rgb:pw},fromMode:{rgb:mw},channels:["h","w","b","alpha"],ranges:{h:[0,360]},gamut:"rgb",parse:[gw],serialize:n=>`hwb(${n.h!==void 0?n.h:"none"} ${n.w!==void 0?n.w*100+"%":"none"} ${n.b!==void 0?n.b*100+"%":"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:Be,fixup:qi},w:Be,b:Be,alpha:{use:Be,fixup:en}},difference:{h:tw},average:{h:Ki}},Rg=203,Wl=.1593017578125,Cg=78.84375,Xl=.8359375,jl=18.8515625,Yl=18.6875;function uu(n){if(n<0)return 0;const e=Math.pow(n,1/Cg);return 1e4*Math.pow(Math.max(0,e-Xl)/(jl-Yl*e),1/Wl)}function hu(n){if(n<0)return 0;const e=Math.pow(n/1e4,Wl);return Math.pow((Xl+jl*e)/(1+Yl*e),Cg)}const fu=n=>Math.max(n/Rg,0),$p=({i:n,t:e,p:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r=uu(n+.008609037037932761*e+.11102962500302593*t),s=uu(n-.00860903703793275*e-.11102962500302599*t),a=uu(n+.5600313357106791*e-.32062717498731885*t),o={mode:"xyz65",x:fu(2.070152218389422*r-1.3263473389671556*s+.2066510476294051*a),y:fu(.3647385209748074*r+.680566024947227*s-.0453045459220346*a),z:fu(-.049747207535812*r-.0492609666966138*s+1.1880659249923042*a)};return i!==void 0&&(o.alpha=i),o},du=(n=0)=>Math.max(n*Rg,0),Jp=({x:n,y:e,z:t,alpha:i})=>{const r=du(n),s=du(e),a=du(t),o=hu(.3592832590121217*r+.6976051147779502*s-.0358915932320289*a),l=hu(-.1920808463704995*r+1.1004767970374323*s+.0753748658519118*a),c=hu(.0070797844607477*r+.0748396662186366*s+.8433265453898765*a),u=.5*o+.5*l,f=1.61376953125*o-3.323486328125*l+1.709716796875*c,h=4.378173828125*o-4.24560546875*l-.132568359375*c,d={mode:"itp",i:u,t:f,p:h};return i!==void 0&&(d.alpha=i),d},vw={mode:"itp",channels:["i","t","p","alpha"],parse:["--ictcp"],serialize:"--ictcp",toMode:{xyz65:$p,rgb:n=>Qr($p(n))},fromMode:{xyz65:Jp,rgb:n=>Jp(Jr(n))},ranges:{i:[0,.581],t:[-.369,.272],p:[-.164,.331]},interpolate:{i:Be,t:Be,p:Be,alpha:{use:Be,fixup:en}}},xw=134.03437499999998,bw=16295499532821565e-27,pu=n=>{if(n<0)return 0;let e=Math.pow(n/1e4,Wl);return Math.pow((Xl+jl*e)/(1+Yl*e),xw)},mu=(n=0)=>Math.max(n*203,0),Pg=({x:n,y:e,z:t,alpha:i})=>{n=mu(n),e=mu(e),t=mu(t);let r=1.15*n-.15*t,s=.66*e+.34*n,a=pu(.41478972*r+.579999*s+.014648*t),o=pu(-.20151*r+1.120649*s+.0531008*t),l=pu(-.0166008*r+.2648*s+.6684799*t),c=(a+o)/2,u={mode:"jab",j:.44*c/(1-.56*c)-bw,a:3.524*a-4.066708*o+.542708*l,b:.199076*a+1.096799*o-1.295875*l};return i!==void 0&&(u.alpha=i),u},Mw=134.03437499999998,Qp=16295499532821565e-27,gu=n=>{if(n<0)return 0;let e=Math.pow(n,1/Mw);return 1e4*Math.pow((Xl-e)/(Yl*e-jl),1/Wl)},_u=n=>n/203,Dg=({j:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(n+Qp)/(.44+.56*(n+Qp)),s=gu(r+.13860504*e+.058047316*t),a=gu(r-.13860504*e-.058047316*t),o=gu(r-.096019242*e-.8118919*t),l={mode:"xyz65",x:_u(1.661373024652174*s-.914523081304348*a+.23136208173913045*o),y:_u(-.3250758611844533*s+1.571847026732543*a-.21825383453227928*o),z:_u(-.090982811*s-.31272829*a+1.5227666*o)};return i!==void 0&&(l.alpha=i),l},Ug=n=>{let e=Pg(Jr(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},Lg=n=>Qr(Dg(n)),Sw={mode:"jab",channels:["j","a","b","alpha"],parse:["--jzazbz"],serialize:"--jzazbz",fromMode:{rgb:Ug,xyz65:Pg},toMode:{rgb:Lg,xyz65:Dg},ranges:{j:[0,.222],a:[-.109,.129],b:[-.185,.134]},interpolate:{j:Be,a:Be,b:Be,alpha:{use:Be,fixup:en}}},em=({j:n,a:e,b:t,alpha:i})=>{e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.sqrt(e*e+t*t),s={mode:"jch",j:n,c:r};return r&&(s.h=hn(Math.atan2(t,e)*180/Math.PI)),i!==void 0&&(s.alpha=i),s},tm=({j:n,c:e,h:t,alpha:i})=>{t===void 0&&(t=0);let r={mode:"jab",j:n,a:e?e*Math.cos(t/180*Math.PI):0,b:e?e*Math.sin(t/180*Math.PI):0};return i!==void 0&&(r.alpha=i),r},yw={mode:"jch",parse:["--jzczhz"],serialize:"--jzczhz",toMode:{jab:tm,rgb:n=>Lg(tm(n))},fromMode:{rgb:n=>em(Ug(n)),jab:em},channels:["j","c","h","alpha"],ranges:{j:[0,.221],c:[0,.19],h:[0,360]},interpolate:{h:{use:Be,fixup:qi},c:Be,j:Be,alpha:{use:Be,fixup:en}},difference:{h:Gl},average:{h:Ki}},ql=Math.pow(29,3)/Math.pow(3,3),Rf=Math.pow(6,3)/Math.pow(29,3);let vu=n=>Math.pow(n,3)>Rf?Math.pow(n,3):(116*n-16)/ql;const Cf=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(n+16)/116,s=e/500+r,a=r-t/200,o={mode:"xyz50",x:vu(s)*Yt.X,y:vu(r)*Yt.Y,z:vu(a)*Yt.Z};return i!==void 0&&(o.alpha=i),o},Ja=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=ea({r:n*3.1341359569958707-e*1.6173863321612538-.4906619460083532*t,g:n*-.978795502912089+e*1.916254567259524+.03344273116131949*t,b:n*.07195537988411677-e*.2289768264158322+1.405386058324125*t});return i!==void 0&&(r.alpha=i),r},Ig=n=>Ja(Cf(n)),Qa=n=>{let{r:e,g:t,b:i,alpha:r}=Qs(n),s={mode:"xyz50",x:.436065742824811*e+.3851514688337912*t+.14307845442264197*i,y:.22249319175623702*e+.7168870538238823*t+.06061979053616537*i,z:.013923904500943465*e+.09708128566574634*t+.7140993584005155*i};return r!==void 0&&(s.alpha=r),s},xu=n=>n>Rf?Math.cbrt(n):(ql*n+16)/116,Pf=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=xu(n/Yt.X),s=xu(e/Yt.Y),a=xu(t/Yt.Z),o={mode:"lab",l:116*s-16,a:500*(r-s),b:200*(s-a)};return i!==void 0&&(o.alpha=i),o},Fg=n=>{let e=Pf(Qa(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e};function Tw(n,e){if(!e||e[0]!=="lab")return;const t={mode:"lab"},[,i,r,s,a]=e;if(!(i.type===Ae.Hue||r.type===Ae.Hue||s.type===Ae.Hue))return i.type!==Ae.None&&(t.l=Math.min(Math.max(0,i.value),100)),r.type!==Ae.None&&(t.a=r.type===Ae.Number?r.value:r.value*125/100),s.type!==Ae.None&&(t.b=s.type===Ae.Number?s.value:s.value*125/100),a.type!==Ae.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ae.Number?a.value:a.value/100))),t}const Df={mode:"lab",toMode:{xyz50:Cf,rgb:Ig},fromMode:{xyz50:Pf,rgb:Fg},channels:["l","a","b","alpha"],ranges:{l:[0,100],a:[-125,125],b:[-125,125]},parse:[Tw],serialize:n=>`lab(${n.l!==void 0?n.l:"none"} ${n.a!==void 0?n.a:"none"} ${n.b!==void 0?n.b:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{l:Be,a:Be,b:Be,alpha:{use:Be,fixup:en}}},Ew={...Df,mode:"lab65",parse:["--lab-d65"],serialize:"--lab-d65",toMode:{xyz65:bg,rgb:Hl},fromMode:{xyz65:Mg,rgb:Vl},ranges:{l:[0,100],a:[-125,125],b:[-125,125]}};function ww(n,e){if(!e||e[0]!=="lch")return;const t={mode:"lch"},[,i,r,s,a]=e;if(i.type!==Ae.None){if(i.type===Ae.Hue)return;t.l=Math.min(Math.max(0,i.value),100)}if(r.type!==Ae.None&&(t.c=Math.max(0,r.type===Ae.Number?r.value:r.value*150/100)),s.type!==Ae.None){if(s.type===Ae.Percentage)return;t.h=s.value}return a.type!==Ae.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ae.Number?a.value:a.value/100))),t}const Uf={mode:"lch",toMode:{lab:Sr,rgb:n=>Ig(Sr(n))},fromMode:{rgb:n=>Mr(Fg(n)),lab:Mr},channels:["l","c","h","alpha"],ranges:{l:[0,100],c:[0,150],h:[0,360]},parse:[ww],serialize:n=>`lch(${n.l!==void 0?n.l:"none"} ${n.c!==void 0?n.c:"none"} ${n.h!==void 0?n.h:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:Be,fixup:qi},c:Be,l:Be,alpha:{use:Be,fixup:en}},difference:{h:Gl},average:{h:Ki}},Aw={...Uf,mode:"lch65",parse:["--lch-d65"],serialize:"--lch-d65",toMode:{lab65:n=>Sr(n,"lab65"),rgb:n=>Hl(Sr(n,"lab65"))},fromMode:{rgb:n=>Mr(Vl(n),"lch65"),lab65:n=>Mr(n,"lch65")},ranges:{l:[0,100],c:[0,150],h:[0,360]}},Ng=({l:n,u:e,v:t,alpha:i})=>{e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.sqrt(e*e+t*t),s={mode:"lchuv",l:n,c:r};return r&&(s.h=hn(Math.atan2(t,e)*180/Math.PI)),i!==void 0&&(s.alpha=i),s},Og=({l:n,c:e,h:t,alpha:i})=>{t===void 0&&(t=0);let r={mode:"luv",l:n,u:e?e*Math.cos(t/180*Math.PI):0,v:e?e*Math.sin(t/180*Math.PI):0};return i!==void 0&&(r.alpha=i),r},Bg=(n,e,t)=>4*n/(n+15*e+3*t),kg=(n,e,t)=>9*e/(n+15*e+3*t),Rw=Bg(Yt.X,Yt.Y,Yt.Z),Cw=kg(Yt.X,Yt.Y,Yt.Z),Pw=n=>n<=Rf?ql*n:116*Math.cbrt(n)-16,Wh=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Pw(e/Yt.Y),s=Bg(n,e,t),a=kg(n,e,t);!isFinite(s)||!isFinite(a)?r=s=a=0:(s=13*r*(s-Rw),a=13*r*(a-Cw));let o={mode:"luv",l:r,u:s,v:a};return i!==void 0&&(o.alpha=i),o},Dw=(n,e,t)=>4*n/(n+15*e+3*t),Uw=(n,e,t)=>9*e/(n+15*e+3*t),Lw=Dw(Yt.X,Yt.Y,Yt.Z),Iw=Uw(Yt.X,Yt.Y,Yt.Z),Xh=({l:n,u:e,v:t,alpha:i})=>{if(n===void 0&&(n=0),n===0)return{mode:"xyz50",x:0,y:0,z:0};e===void 0&&(e=0),t===void 0&&(t=0);let r=e/(13*n)+Lw,s=t/(13*n)+Iw,a=Yt.Y*(n<=8?n/ql:Math.pow((n+16)/116,3)),o=a*(9*r)/(4*s),l=a*(12-3*r-20*s)/(4*s),c={mode:"xyz50",x:o,y:a,z:l};return i!==void 0&&(c.alpha=i),c},Fw=n=>Ng(Wh(Qa(n))),Nw=n=>Ja(Xh(Og(n))),Ow={mode:"lchuv",toMode:{luv:Og,rgb:Nw},fromMode:{rgb:Fw,luv:Ng},channels:["l","c","h","alpha"],parse:["--lchuv"],serialize:"--lchuv",ranges:{l:[0,100],c:[0,176.956],h:[0,360]},interpolate:{h:{use:Be,fixup:qi},c:Be,l:Be,alpha:{use:Be,fixup:en}},difference:{h:Gl},average:{h:Ki}},Bw={...Js,mode:"lrgb",toMode:{rgb:ea},fromMode:{rgb:Qs},parse:["srgb-linear"],serialize:"srgb-linear"},kw={mode:"luv",toMode:{xyz50:Xh,rgb:n=>Ja(Xh(n))},fromMode:{xyz50:Wh,rgb:n=>Wh(Qa(n))},channels:["l","u","v","alpha"],parse:["--luv"],serialize:"--luv",ranges:{l:[0,100],u:[-84.936,175.042],v:[-125.882,87.243]},interpolate:{l:Be,u:Be,v:Be,alpha:{use:Be,fixup:en}}},zg=({r:n,g:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.cbrt(.412221469470763*n+.5363325372617348*e+.0514459932675022*t),s=Math.cbrt(.2119034958178252*n+.6806995506452344*e+.1073969535369406*t),a=Math.cbrt(.0883024591900564*n+.2817188391361215*e+.6299787016738222*t),o={mode:"oklab",l:.210454268309314*r+.7936177747023054*s-.0040720430116193*a,a:1.9779985324311684*r-2.42859224204858*s+.450593709617411*a,b:.0259040424655478*r+.7827717124575296*s-.8086757549230774*a};return i!==void 0&&(o.alpha=i),o},Kl=n=>{let e=zg(Qs(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},eo=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.pow(n+.3963377773761749*e+.2158037573099136*t,3),s=Math.pow(n-.1055613458156586*e-.0638541728258133*t,3),a=Math.pow(n-.0894841775298119*e-1.2914855480194092*t,3),o={mode:"lrgb",r:4.076741636075957*r-3.3077115392580616*s+.2309699031821044*a,g:-1.2684379732850317*r+2.6097573492876887*s-.3413193760026573*a,b:-.0041960761386756*r-.7034186179359362*s+1.7076146940746117*a};return i!==void 0&&(o.alpha=i),o},Zl=n=>ea(eo(n));function jh(n){const i=1.170873786407767;return .5*(i*n-.206+Math.sqrt((i*n-.206)*(i*n-.206)+4*.03*i*n))}function Pl(n){return(n*n+.206*n)/(1.170873786407767*(n+.03))}function zw(n,e){let t,i,r,s,a,o,l,c;-1.88170328*n-.80936493*e>1?(t=1.19086277,i=1.76576728,r=.59662641,s=.75515197,a=.56771245,o=4.0767416621,l=-3.3077115913,c=.2309699292):1.81444104*n-1.19445276*e>1?(t=.73956515,i=-.45954404,r=.08285427,s=.1254107,a=.14503204,o=-1.2684380046,l=2.6097574011,c=-.3413193965):(t=1.35733652,i=-.00915799,r=-1.1513021,s=-.50559606,a=.00692167,o=-.0041960863,l=-.7034186147,c=1.707614701);let u=t+i*n+r*e+s*n*n+a*n*e,f=.3963377774*n+.2158037573*e,h=-.1055613458*n-.0638541728*e,d=-.0894841775*n-1.291485548*e;{let g=1+u*f,m=1+u*h,p=1+u*d,_=g*g*g,v=m*m*m,M=p*p*p,y=3*f*g*g,T=3*h*m*m,S=3*d*p*p,E=6*f*f*g,b=6*h*h*m,x=6*d*d*p,A=o*_+l*v+c*M,C=o*y+l*T+c*S,R=o*E+l*b+c*x;u=u-A*C/(C*C-.5*A*R)}return u}function Lf(n,e){let t=zw(n,e),i=eo({l:1,a:t*n,b:t*e}),r=Math.cbrt(1/Math.max(i.r,i.g,i.b)),s=r*t;return[r,s]}function Gw(n,e,t,i,r,s=null){s||(s=Lf(n,e));let a;if((t-r)*s[1]-(s[0]-r)*i<=0)a=s[1]*r/(i*s[0]+s[1]*(r-t));else{a=s[1]*(r-1)/(i*(s[0]-1)+s[1]*(r-t));{let o=t-r,l=i,c=.3963377774*n+.2158037573*e,u=-.1055613458*n-.0638541728*e,f=-.0894841775*n-1.291485548*e,h=o+l*c,d=o+l*u,g=o+l*f;{let m=r*(1-a)+a*t,p=a*i,_=m+p*c,v=m+p*u,M=m+p*f,y=_*_*_,T=v*v*v,S=M*M*M,E=3*h*_*_,b=3*d*v*v,x=3*g*M*M,A=6*h*h*_,C=6*d*d*v,R=6*g*g*M,L=4.0767416621*y-3.3077115913*T+.2309699292*S-1,U=4.0767416621*E-3.3077115913*b+.2309699292*x,I=4.0767416621*A-3.3077115913*C+.2309699292*R,F=U/(U*U-.5*L*I),O=-L*F,j=-1.2684380046*y+2.6097574011*T-.3413193965*S-1,G=-1.2684380046*E+2.6097574011*b-.3413193965*x,W=-1.2684380046*A+2.6097574011*C-.3413193965*R,N=G/(G*G-.5*j*W),k=-j*N,J=-.0041960863*y-.7034186147*T+1.707614701*S-1,Q=-.0041960863*E-.7034186147*b+1.707614701*x,K=-.0041960863*A-.7034186147*C+1.707614701*R,H=Q/(Q*Q-.5*J*K),Y=-J*H;O=F>=0?O:1e6,k=N>=0?k:1e6,Y=H>=0?Y:1e6,a+=Math.min(O,Math.min(k,Y))}}}return a}function If(n,e,t=null){t||(t=Lf(n,e));let i=t[0],r=t[1];return[r/i,r/(1-i)]}function Gg(n,e,t){let i=Lf(e,t),r=Gw(e,t,n,1,n,i),s=If(e,t,i),a=.11516993+1/(7.4477897+4.1590124*t+e*(-2.19557347+1.75198401*t+e*(-2.13704948-10.02301043*t+e*(-4.24894561+5.38770819*t+4.69891013*e)))),o=.11239642+1/(1.6132032-.68124379*t+e*(.40370612+.90148123*t+e*(-.27087943+.6122399*t+e*(.00299215-.45399568*t-.14661872*e)))),l=r/Math.min(n*s[0],(1-n)*s[1]),c=n*a,u=(1-n)*o,f=.9*l*Math.sqrt(Math.sqrt(1/(1/(c*c*c*c)+1/(u*u*u*u))));return c=n*.4,u=(1-n)*.8,[Math.sqrt(1/(1/(c*c)+1/(u*u))),f,r]}function nm(n){const e=n.l!==void 0?n.l:0,t=n.a!==void 0?n.a:0,i=n.b!==void 0?n.b:0,r={mode:"okhsl",l:jh(e)};n.alpha!==void 0&&(r.alpha=n.alpha);let s=Math.sqrt(t*t+i*i);if(!s)return r.s=0,r;let[a,o,l]=Gg(e,t/s,i/s),c;if(s<o){let u=0,f=.8*a,h=1-f/o;c=(s-u)/(f+h*(s-u))*.8}else{let u=o,f=.2*o*o*1.25*1.25/a,h=1-f/(l-o);c=.8+.2*((s-u)/(f+h*(s-u)))}return c&&(r.s=c,r.h=hn(Math.atan2(i,t)*180/Math.PI)),r}function im(n){let e=n.h!==void 0?n.h:0,t=n.s!==void 0?n.s:0,i=n.l!==void 0?n.l:0;const r={mode:"oklab",l:Pl(i)};if(n.alpha!==void 0&&(r.alpha=n.alpha),!t||i===1)return r.a=r.b=0,r;let s=Math.cos(e/180*Math.PI),a=Math.sin(e/180*Math.PI),[o,l,c]=Gg(r.l,s,a),u,f,h,d;t<.8?(u=1.25*t,f=0,h=.8*o,d=1-h/l):(u=5*(t-.8),f=l,h=.2*l*l*1.25*1.25/o,d=1-h/(c-l));let g=f+u*h/(1-d*u);return r.a=g*s,r.b=g*a,r}const Hw={...Tg,mode:"okhsl",channels:["h","s","l","alpha"],parse:["--okhsl"],serialize:"--okhsl",fromMode:{oklab:nm,rgb:n=>nm(Kl(n))},toMode:{oklab:im,rgb:n=>Zl(im(n))}};function rm(n){let e=n.l!==void 0?n.l:0,t=n.a!==void 0?n.a:0,i=n.b!==void 0?n.b:0,r=Math.sqrt(t*t+i*i),s=r?t/r:1,a=r?i/r:1,[o,l]=If(s,a),c=.5,u=1-c/o,f=l/(r+e*l),h=f*e,d=f*r,g=Pl(h),m=d*g/h,p=eo({l:g,a:s*m,b:a*m}),_=Math.cbrt(1/Math.max(p.r,p.g,p.b,0));e=e/_,r=r/_*jh(e)/e,e=jh(e);const v={mode:"okhsv",s:r?(c+l)*d/(l*c+l*u*d):0,v:e?e/h:0};return v.s&&(v.h=hn(Math.atan2(i,t)*180/Math.PI)),n.alpha!==void 0&&(v.alpha=n.alpha),v}function sm(n){const e={mode:"oklab"};n.alpha!==void 0&&(e.alpha=n.alpha);const t=n.h!==void 0?n.h:0,i=n.s!==void 0?n.s:0,r=n.v!==void 0?n.v:0,s=Math.cos(t/180*Math.PI),a=Math.sin(t/180*Math.PI),[o,l]=If(s,a),c=.5,u=1-c/o,f=1-i*c/(c+l-l*u*i),h=i*l*c/(c+l-l*u*i),d=Pl(f),g=h*d/f,m=eo({l:d,a:s*g,b:a*g}),p=Math.cbrt(1/Math.max(m.r,m.g,m.b,0)),_=Pl(r*f),v=h*_/f;return e.l=_*p,e.a=v*s*p,e.b=v*a*p,e}const Vw={...Ag,mode:"okhsv",channels:["h","s","v","alpha"],parse:["--okhsv"],serialize:"--okhsv",fromMode:{oklab:rm,rgb:n=>rm(Kl(n))},toMode:{oklab:sm,rgb:n=>Zl(sm(n))}};function Ww(n,e){if(!e||e[0]!=="oklab")return;const t={mode:"oklab"},[,i,r,s,a]=e;if(!(i.type===Ae.Hue||r.type===Ae.Hue||s.type===Ae.Hue))return i.type!==Ae.None&&(t.l=Math.min(Math.max(0,i.type===Ae.Number?i.value:i.value/100),1)),r.type!==Ae.None&&(t.a=r.type===Ae.Number?r.value:r.value*.4/100),s.type!==Ae.None&&(t.b=s.type===Ae.Number?s.value:s.value*.4/100),a.type!==Ae.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ae.Number?a.value:a.value/100))),t}const Xw={...Df,mode:"oklab",toMode:{lrgb:eo,rgb:Zl},fromMode:{lrgb:zg,rgb:Kl},ranges:{l:[0,1],a:[-.4,.4],b:[-.4,.4]},parse:[Ww],serialize:n=>`oklab(${n.l!==void 0?n.l:"none"} ${n.a!==void 0?n.a:"none"} ${n.b!==void 0?n.b:"none"}${n.alpha<1?` / ${n.alpha}`:""})`};function jw(n,e){if(!e||e[0]!=="oklch")return;const t={mode:"oklch"},[,i,r,s,a]=e;if(i.type!==Ae.None){if(i.type===Ae.Hue)return;t.l=Math.min(Math.max(0,i.type===Ae.Number?i.value:i.value/100),1)}if(r.type!==Ae.None&&(t.c=Math.max(0,r.type===Ae.Number?r.value:r.value*.4/100)),s.type!==Ae.None){if(s.type===Ae.Percentage)return;t.h=s.value}return a.type!==Ae.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ae.Number?a.value:a.value/100))),t}const Yw={...Uf,mode:"oklch",toMode:{oklab:n=>Sr(n,"oklab"),rgb:n=>Zl(Sr(n,"oklab"))},fromMode:{rgb:n=>Mr(Kl(n),"oklch"),oklab:n=>Mr(n,"oklch")},parse:[jw],serialize:n=>`oklch(${n.l!==void 0?n.l:"none"} ${n.c!==void 0?n.c:"none"} ${n.h!==void 0?n.h:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,ranges:{l:[0,1],c:[0,.4],h:[0,360]}},am=n=>{let{r:e,g:t,b:i,alpha:r}=Qs(n),s={mode:"xyz65",x:.486570948648216*e+.265667693169093*t+.1982172852343625*i,y:.2289745640697487*e+.6917385218365062*t+.079286914093745*i,z:0*e+.0451133818589026*t+1.043944368900976*i};return r!==void 0&&(s.alpha=r),s},om=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=ea({r:n*2.4934969119414263-e*.9313836179191242-.402710784450717*t,g:n*-.8294889695615749+e*1.7626640603183465+.0236246858419436*t,b:n*.0358458302437845-e*.0761723892680418+.9568845240076871*t},"p3");return i!==void 0&&(r.alpha=i),r},qw={...Js,mode:"p3",parse:["display-p3"],serialize:"display-p3",fromMode:{rgb:n=>om(Jr(n)),xyz65:om},toMode:{rgb:n=>Qr(am(n)),xyz65:am}},bu=n=>{let e=Math.abs(n);return e>=1/512?Math.sign(n)*Math.pow(e,1/1.8):16*n},lm=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"prophoto",r:bu(n*1.3457868816471585-e*.2555720873797946-.0511018649755453*t),g:bu(n*-.5446307051249019+e*1.5082477428451466+.0205274474364214*t),b:bu(n*0+e*0+1.2119675456389452*t)};return i!==void 0&&(r.alpha=i),r},Mu=(n=0)=>{let e=Math.abs(n);return e>=16/512?Math.sign(n)*Math.pow(e,1.8):n/16},cm=n=>{let e=Mu(n.r),t=Mu(n.g),i=Mu(n.b),r={mode:"xyz50",x:.7977666449006423*e+.1351812974005331*t+.0313477341283922*i,y:.2880748288194013*e+.7118352342418731*t+899369387256e-16*i,z:0*e+0*t+.8251046025104602*i};return n.alpha!==void 0&&(r.alpha=n.alpha),r},Kw={...Js,mode:"prophoto",parse:["prophoto-rgb"],serialize:"prophoto-rgb",fromMode:{xyz50:lm,rgb:n=>lm(Qa(n))},toMode:{xyz50:cm,rgb:n=>Ja(cm(n))}},um=1.09929682680944,Zw=.018053968510807,Su=n=>{const e=Math.abs(n);return e>Zw?(Math.sign(n)||1)*(um*Math.pow(e,.45)-(um-1)):4.5*n},hm=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"rec2020",r:Su(n*1.7166511879712683-e*.3556707837763925-.2533662813736599*t),g:Su(n*-.6666843518324893+e*1.6164812366349395+.0157685458139111*t),b:Su(n*.0176398574453108-e*.0427706132578085+.9421031212354739*t)};return i!==void 0&&(r.alpha=i),r},fm=1.09929682680944,$w=.018053968510807,yu=(n=0)=>{let e=Math.abs(n);return e<$w*4.5?n/4.5:(Math.sign(n)||1)*Math.pow((e+fm-1)/fm,1/.45)},dm=n=>{let e=yu(n.r),t=yu(n.g),i=yu(n.b),r={mode:"xyz65",x:.6369580483012911*e+.1446169035862083*t+.1688809751641721*i,y:.262700212011267*e+.6779980715188708*t+.059301716469862*i,z:0*e+.0280726930490874*t+1.0609850577107909*i};return n.alpha!==void 0&&(r.alpha=n.alpha),r},Jw={...Js,mode:"rec2020",fromMode:{xyz65:hm,rgb:n=>hm(Jr(n))},toMode:{xyz65:dm,rgb:n=>Qr(dm(n))},parse:["rec2020"],serialize:"rec2020"},jr=.0037930732552754493,Hg=Math.cbrt(jr),Tu=n=>Math.cbrt(n)-Hg,Qw=n=>{const{r:e,g:t,b:i,alpha:r}=Qs(n),s=Tu(.3*e+.622*t+.078*i+jr),a=Tu(.23*e+.692*t+.078*i+jr),o=Tu(.2434226892454782*e+.2047674442449682*t+.5518098665095535*i+jr),l={mode:"xyb",x:(s-a)/2,y:(s+a)/2,b:o-(s+a)/2};return r!==void 0&&(l.alpha=r),l},Eu=n=>Math.pow(n+Hg,3),eA=({x:n,y:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r=Eu(n+e)-jr,s=Eu(e-n)-jr,a=Eu(t+e)-jr,o=ea({r:11.031566904639861*r-9.866943908131562*s-.16462299650829934*a,g:-3.2541473810744237*r+4.418770377582723*s-.16462299650829934*a,b:-3.6588512867136815*r+2.7129230459360922*s+1.9459282407775895*a});return i!==void 0&&(o.alpha=i),o},tA={mode:"xyb",channels:["x","y","b","alpha"],parse:["--xyb"],serialize:"--xyb",toMode:{rgb:eA},fromMode:{rgb:Qw},ranges:{x:[-.0154,.0281],y:[0,.8453],b:[-.2778,.388]},interpolate:{x:Be,y:Be,b:Be,alpha:{use:Be,fixup:en}}},nA={mode:"xyz50",parse:["xyz-d50"],serialize:"xyz-d50",toMode:{rgb:Ja,lab:Pf},fromMode:{rgb:Qa,lab:Cf},channels:["x","y","z","alpha"],ranges:{x:[0,.964],y:[0,.999],z:[0,.825]},interpolate:{x:Be,y:Be,z:Be,alpha:{use:Be,fixup:en}}},iA=n=>{let{x:e,y:t,z:i,alpha:r}=n;e===void 0&&(e=0),t===void 0&&(t=0),i===void 0&&(i=0);let s={mode:"xyz50",x:1.0479298208405488*e+.0229467933410191*t-.0501922295431356*i,y:.0296278156881593*e+.990434484573249*t-.0170738250293851*i,z:-.0092430581525912*e+.0150551448965779*t+.7518742899580008*i};return r!==void 0&&(s.alpha=r),s},rA=n=>{let{x:e,y:t,z:i,alpha:r}=n;e===void 0&&(e=0),t===void 0&&(t=0),i===void 0&&(i=0);let s={mode:"xyz65",x:.9554734527042182*e-.0230985368742614*t+.0632593086610217*i,y:-.0283697069632081*e+1.0099954580058226*t+.021041398966943*i,z:.0123140016883199*e-.0205076964334779*t+1.3303659366080753*i};return r!==void 0&&(s.alpha=r),s},sA={mode:"xyz65",toMode:{rgb:Qr,xyz50:iA},fromMode:{rgb:Jr,xyz50:rA},ranges:{x:[0,.95],y:[0,1],z:[0,1.088]},channels:["x","y","z","alpha"],parse:["xyz","xyz-d65"],serialize:"xyz-d65",interpolate:{x:Be,y:Be,z:Be,alpha:{use:Be,fixup:en}}},aA=({r:n,g:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r={mode:"yiq",y:.29889531*n+.58662247*e+.11448223*t,i:.59597799*n-.2741761*e-.32180189*t,q:.21147017*n-.52261711*e+.31114694*t};return i!==void 0&&(r.alpha=i),r},oA=({y:n,i:e,q:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r={mode:"rgb",r:n+.95608445*e+.6208885*t,g:n-.27137664*e-.6486059*t,b:n-1.10561724*e+1.70250126*t};return i!==void 0&&(r.alpha=i),r},lA={mode:"yiq",toMode:{rgb:oA},fromMode:{rgb:aA},channels:["y","i","q","alpha"],parse:["--yiq"],serialize:"--yiq",ranges:{i:[-.595,.595],q:[-.522,.522]},interpolate:{y:Be,i:Be,q:Be,alpha:{use:Be,fixup:en}}},cA=n=>{n[0]===void 0&&(n[0]=0),n[n.length-1]===void 0&&(n[n.length-1]=1);let e=1,t,i,r,s;for(;e<n.length;){if(n[e]===void 0){for(i=e,r=n[e-1],t=e;n[t]===void 0;)t++;for(s=(n[t]-r)/(t-e+1);e<t;)n[e]=r+(e+1-i)*s,e++}else n[e]<n[e-1]&&(n[e]=n[e-1]);e++}return n},uA=(n=.5)=>e=>n<=0?1:n>=1?0:Math.pow(e,Math.log(.5)/Math.log(n)),jo=n=>typeof n=="function",Lr=n=>n&&typeof n=="object",pm=n=>typeof n=="number",hA=(n,e="rgb",t,i)=>{let r=gg(e),s=Af(e),a=[],o=[],l={};n.forEach(h=>{Array.isArray(h)?(a.push(s(h[0])),o.push(h[1])):pm(h)||jo(h)?l[o.length]=h:(a.push(s(h)),o.push(void 0))}),cA(o);let c=r.channels.reduce((h,d)=>{let g;return Lr(t)&&Lr(t[d])&&t[d].fixup?g=t[d].fixup:Lr(r.interpolate[d])&&r.interpolate[d].fixup?g=r.interpolate[d].fixup:g=m=>m,h[d]=g(a.map(m=>m[d])),h},{}),u=r.channels.reduce((h,d)=>{let g;return jo(t)?g=t:Lr(t)&&jo(t[d])?g=t[d]:Lr(t)&&Lr(t[d])&&t[d].use?g=t[d].use:jo(r.interpolate[d])?g=r.interpolate[d]:Lr(r.interpolate[d])&&(g=r.interpolate[d].use),h[d]=g(c[d]),h},{}),f=a.length-1;return h=>{if(h=Math.min(Math.max(0,h),1),h<=o[0])return a[0];if(h>o[f])return a[f];let d=0;for(;o[d]<h;)d++;let g=o[d-1],m=o[d]-g,p=(h-g)/m,_=l[d]||l[0];_!==void 0&&(pm(_)&&(_=uA((_-g)/m)),p=_(p));let v=(d-1+p)/f;return r.channels.reduce((M,y)=>{let T=u[y](v);return T!==void 0&&(M[y]=T),M},{mode:e})}},fA=(n,e="rgb",t)=>hA(n,e,t);bt(K2);bt(nw);bt(iw);bt(rw);bt(ow);bt(Tg);bt(Ag);bt(_w);bt(vw);bt(Sw);bt(yw);bt(Df);bt(Ew);bt(Uf);bt(Aw);bt(Ow);bt(Bw);bt(kw);bt(Hw);bt(Vw);bt(Xw);bt(Yw);bt(qw);bt(Kw);bt(Jw);bt(Js);bt(tA);bt(nA);bt(sA);bt(lA);const dA="/assets/NotoSerifSC-subset-Cx3VUXg0.ttf",ar="/assets/IMing-subset-Kpo8eYZB.ttf",pA="/assets/IMFellEnglish-subset-DL3qchp1.ttf",wu=(n,e)=>Math.min(1,Math.max(0,(n-e)/.4));function mm(n,e){const t={plan:[],deep:[],size:[],opacity:[],core:[],ring:[],color:[],deepColor:[],filler:[],deepOpScale:[],deepSizeScale:[]};for(let i=0;i<n.filler.length;i++)n.filler[i]===1===e&&(t.plan.push(n.plan[i*3],n.plan[i*3+1],n.plan[i*3+2]),t.deep.push(n.deep[i*3],n.deep[i*3+1],n.deep[i*3+2]),t.size.push(n.size[i]),t.opacity.push(n.opacity[i]),t.core.push(n.core[i]),t.ring.push(n.ring[i]),t.color.push(n.color[i*3],n.color[i*3+1],n.color[i*3+2]),t.deepColor.push(n.deepColor[i*3],n.deepColor[i*3+1],n.deepColor[i*3+2]),t.filler.push(n.filler[i]),t.deepOpScale.push(n.deepOpScale[i]),t.deepSizeScale.push(n.deepSizeScale[i]));return t}class mA{constructor(e,t,i,r={}){ye(this,"root");ye(this,"heart");ye(this,"snapshot");ye(this,"opts");ye(this,"L");ye(this,"renderer");ye(this,"composer");ye(this,"bloom");ye(this,"fxPass");ye(this,"scene",new gh);ye(this,"camera");ye(this,"chart",new Rs);ye(this,"canvas");ye(this,"bgStone");ye(this,"bgDeep");ye(this,"bgDusk");ye(this,"vignette");ye(this,"tooltip");ye(this,"fadeMats",[]);ye(this,"fadeFns",[]);ye(this,"shapeLines",null);ye(this,"asterLinks",null);ye(this,"orbitRings",[]);ye(this,"planetTrails",[]);ye(this,"trailTimer",0);ye(this,"coreLerp",[]);ye(this,"labelObjs",[]);ye(this,"morphables",[]);ye(this,"reveal");ye(this,"dimPts");ye(this,"dimBgPts");ye(this,"bgLayer",new Rs);ye(this,"litPts");ye(this,"goalPts");ye(this,"northPts");ye(this,"northVacant");ye(this,"planetPts");ye(this,"guestPts");ye(this,"planetInnerPts");ye(this,"moonPts");ye(this,"guestTails");ye(this,"glows",[]);ye(this,"guestGlows",[]);ye(this,"nebulae",[]);ye(this,"dustRiver",[]);ye(this,"tiered",[]);ye(this,"colored",[]);ye(this,"goalLabelGroups",[]);ye(this,"selRing");ye(this,"controls",null);ye(this,"state",{t:0,density:1,bloom:1,w1:0,w2:.3,w3:.6,duskPos:.45,duskAmt:1,ch1:0,ch2:0,ch3:0});ye(this,"tween",null);ye(this,"hoverIdx",-1);ye(this,"selectedIdx",-1);ye(this,"hoverables",[]);ye(this,"clickables",[]);ye(this,"focusTween",null);ye(this,"focusToken",0);ye(this,"dragging",!1);ye(this,"dragLastX",0);ye(this,"dragLastT",0);ye(this,"dragDist",0);ye(this,"spinVel",0);ye(this,"spinFactor",1);ye(this,"lastPointerActive",-1e9);ye(this,"clock",new zv);ye(this,"rafId",0);ye(this,"disposed",!1);ye(this,"resizeObserver",null);ye(this,"labelsPending",0);ye(this,"segPending",0);ye(this,"labelGrpSeq",0);ye(this,"collisionTick",0);ye(this,"reducedMotion");ye(this,"coarsePointer");ye(this,"softGL");ye(this,"camPlan",{pos:new X(0,4,346),look:new X(0,0,0)});ye(this,"camDeep",{pos:new X(0,72,232),look:new X(0,-4,0)});ye(this,"goalPeriods");ye(this,"planetPeriods");ye(this,"guestPeriods");ye(this,"goalPhase");ye(this,"planetPhase");ye(this,"guestPhase");ye(this,"goalDeepBase");ye(this,"planetDeepBase");ye(this,"guestDeepBase");ye(this,"moonDeepBase");ye(this,"moonPlanet",[]);ye(this,"tailOffsets",[]);ye(this,"guestBaseOpacity");ye(this,"onPointerMoveWindow",e=>this.onPointerMove(e));ye(this,"onPointerActive",()=>{this.lastPointerActive=performance.now()});ye(this,"onClickWindow",e=>this.onClick(e));ye(this,"onKeydown",e=>{e.key==="Escape"&&this.closeDetail()});ye(this,"onWheel",(()=>{let e=0;return t=>{e+=t.deltaY,Math.abs(e)>260&&(this.goTo(e<0?1:0),e=0)}})());var b;this.root=e,this.heart=t,this.snapshot=i,this.opts=r,this.L=e_(i),this.northVacant=!(((b=i.north)==null?void 0:b.is_set)??i.north_star.trim().length>0),this.reducedMotion=matchMedia("(prefers-reduced-motion: reduce)").matches,this.coarsePointer=matchMedia("(pointer: coarse)").matches,this.reveal=r.reveal??!1,this.state.t=r.initialState==="deepspace"?1:0;const s=x=>{const A=document.createElement("div");return A.className=x,this.root.appendChild(A),A};this.bgStone=s("starmap-bg"),this.bgDusk=s("starmap-bg"),this.bgDeep=s("starmap-bg"),this.vignette=s("starmap-vignette"),this.canvas=document.createElement("canvas"),this.canvas.className="starmap-canvas",this.heart.appendChild(this.canvas),this.tooltip=s("starmap-tooltip"),this.tooltip.style.display="none",this.renderer=new OS({canvas:this.canvas,antialias:!0,alpha:!0}),this.renderer.setClearColor(0,0),this.renderer.setPixelRatio(Math.min(window.devicePixelRatio,2)),this.camera=new kn(45,1,1,2e3),this.fitPlanCamera(),this.scene.add(this.chart),this.chart.add(this.bgLayer),this.bakeBackgrounds(),this.buildLinework();const a=mm(this.L.dim,!1),o=mm(this.L.dim,!0);this.dimPts=this.makePoints(a),this.dimBgPts=this.makePoints(o,this.bgLayer);for(const x of[this.dimPts,this.dimBgPts])x.userData.filler=x===this.dimBgPts?o.filler:a.filler,x.userData.baseOpacity=new Float32Array(x.geometry.attributes.aOpacity.array),x.userData.baseSize=new Float32Array(x.geometry.attributes.aSize.array),x.userData.baseRing=new Float32Array(x.geometry.attributes.aRing.array);this.dimPts.userData.deepOpScale=new Float32Array(a.deepOpScale),this.dimPts.userData.deepSizeScale=new Float32Array(a.deepSizeScale),this.dimBgPts.userData.deepOpScale=new Float32Array(o.deepOpScale),this.dimBgPts.userData.deepSizeScale=new Float32Array(o.deepSizeScale),this.litPts=this.makePoints({plan:this.L.lit.plan,deep:this.L.lit.deep,size:this.L.lit.size,opacity:this.L.lit.opacity,core:this.L.lit.core,ring:this.L.lit.ring,color:this.L.lit.color,deepColor:this.L.lit.deepColor}),this.addTier(this.litPts,1.15,1);const l=[.949,.929,.878];this.goalPts=this.makePoints({plan:this.L.goals.flatMap(x=>x.plan),deep:this.L.goals.flatMap(x=>x.deep),size:this.L.goals.map(x=>x.status==="completed"?2.2:2.6),opacity:this.L.goals.map(x=>x.status==="completed"?.3:x.status==="paused"?.55:1),core:this.L.goals.map(x=>x.status==="completed"?0:1),ring:this.L.goals.map(()=>1),color:this.L.goals.flatMap(x=>x.status==="completed"?l:[.91,.72,.36]),deepColor:this.L.goals.flatMap(x=>x.status==="completed"?[...Er.moonWhite]:[.95,.76,.34])}),this.addTier(this.goalPts,1.18,1);const c=this.makePoints({plan:this.L.court.plan,deep:this.L.court.plan.map((x,A)=>A%3===2?x||0:x*1.6),size:this.L.court.size,opacity:this.L.court.gold.map(x=>x?1:.85),core:this.L.court.gold.map(()=>1),ring:this.L.court.gold.map(()=>0),color:this.L.court.gold.flatMap(x=>x?[.91,.72,.36]:[.961,.918,.824])});this.northPts=this.makePoints(this.northVacant?{plan:[0,0,0],deep:[0,0,0],size:[4.4],opacity:[.3],core:[0],ring:[1],color:l}:{plan:[0,0,0],deep:[0,0,0],size:[4.4],opacity:[1],core:[1],ring:[0],color:[.98,.85,.55],deepColor:[...Er.warmGold]}),this.northVacant||this.addTier(this.northPts,1.35,1),this.planetPts=this.makePoints({plan:this.L.planets.flatMap(x=>x.plan),deep:this.L.planets.flatMap(x=>x.deep),size:this.L.planets.map(()=>3),opacity:this.L.planets.map(x=>x.status==="active"?.9:.35),core:this.L.planets.map(()=>.4),ring:this.L.planets.map(()=>1),color:this.L.planets.flatMap(()=>[.961,.918,.824]),deepColor:this.L.planets.flatMap(()=>[...Er.softOrange])}),this.addTier(this.planetPts,.6,.85),this.moonPts=this.makePoints({plan:this.L.moons.plan,deep:this.L.moons.deep,size:this.L.moons.size,opacity:this.L.moons.opacity,core:this.L.moons.size.map(()=>1),ring:this.L.moons.size.map(()=>0),color:this.L.moons.size.flatMap(()=>[.961,.918,.824]),deepColor:this.L.moons.size.flatMap(()=>[...Er.moonWhite])}),this.addTier(this.moonPts,.9,1);const u=this.makePoints({plan:this.L.seated.plan,deep:this.L.seated.deep,size:this.L.seated.size,opacity:this.L.seated.opacity,core:this.L.seated.size.map(()=>1),ring:this.L.seated.size.map(()=>0),color:this.L.seated.size.flatMap(()=>[.961,.918,.824]),deepColor:this.L.seated.size.flatMap(()=>[...Er.moonWhite])});this.addTier(u,.9,1),this.guestPts=this.makePoints({plan:this.L.guests.flatMap(x=>x.plan),deep:this.L.guests.flatMap(x=>x.deep),size:this.L.guests.map(()=>1.15),opacity:this.L.guests.map(()=>.95),core:this.L.guests.map(()=>1),ring:this.L.guests.map(()=>0),color:this.L.guests.flatMap(()=>[1,.95,.85]),deepColor:this.L.guests.flatMap(()=>[...Er.blueWhite])}),this.addTier(this.guestPts,.95,null);const f=this.makePoints({plan:this.L.dust.plan,deep:this.L.dust.deep,size:this.L.dust.size,opacity:this.L.dust.opacity,core:this.L.dust.size.map(()=>1),ring:this.L.dust.size.map(()=>0),color:this.L.dust.size.flatMap(()=>[.961,.918,.824]),deepColor:this.L.dust.size.flatMap(()=>[.88,.9,.94])});this.addTier(f,.8,1);const h=this.makePoints({plan:this.L.etched.plan,deep:this.L.etched.deep,size:this.L.etched.size,opacity:this.L.etched.opacity,core:this.L.etched.size.map(()=>0),ring:this.L.etched.size.map(()=>1),color:this.L.etched.color,deepColor:this.L.etched.deepColor.slice(),deepCore:this.L.etched.size.map(()=>.85)});this.addTier(h,1.05,1.8);const d=(()=>{const x=new At;x.setAttribute("position",new Ft(new Float32Array(this.L.dust.trailPlan),3));const A=new ir(x,this.lineMat(Fn,.26,.22,3));this.chart.add(A);const C=A;return C.userData.plan=new Float32Array(this.L.dust.trailPlan),C.userData.deep=new Float32Array(this.L.dust.trailDeep),C})();if(this.planetInnerPts=this.makePoints({plan:this.L.planets.flatMap(x=>x.plan),deep:this.L.planets.flatMap(x=>x.deep),size:this.L.planets.map(()=>2),opacity:this.L.planets.map(x=>x.status==="active"?.9:.35),core:this.L.planets.map(()=>0),ring:this.L.planets.map(()=>1),color:this.L.planets.flatMap(()=>[.961,.918,.824]),deepColor:this.L.planets.flatMap(()=>[...Er.softOrange])}),this.addTier(this.planetInnerPts,.6,.85),this.L.shapeLinesPlan.length){const x=new At;x.setAttribute("position",new Ft(new Float32Array(this.L.shapeLinesPlan),3));const A=new ws({color:Fn,transparent:!0,opacity:.14,depthWrite:!1}),C=new ir(x,A);this.chart.add(C),this.shapeLines=C,this.shapeLines.userData.plan=new Float32Array(this.L.shapeLinesPlan),this.shapeLines.userData.deep=new Float32Array(this.L.shapeLinesDeep),this.fadeFns.push({mat:A,fn:(R,L,U)=>.14*(1-R)+.05*U})}{const x=lo(6600);for(const A of this.L.planets){if(A.goalIndex<0)continue;const C=this.L.goals[A.goalIndex],R=Math.hypot(A.deep[0]-C.deep[0],A.deep[1]-C.deep[1]),L=new ws({color:ac,transparent:!0,opacity:0,depthWrite:!1}),U=new Oc(new At().setFromPoints(this.circlePoints(R,72)),L);this.chart.add(U);const I=new ws({color:Jf,transparent:!0,opacity:0,depthWrite:!1}),F=[];for(let j=0;j<=10;j++){const G=j/10*(Math.PI*2)*.045;F.push(new X(R*Math.cos(G),R*Math.sin(G),0))}const O=new _l(new At().setFromPoints(F),I);U.add(O),this.orbitRings.push({ring:U,ringMat:L,flow:O,flowMat:I,goalIdx:A.goalIndex,phase:x()*Math.PI*2,shimmer:x()*Math.PI*2})}}{const x=[];for(const A of this.L.planets){if(A.goalIndex<0)continue;const C=this.L.goals[A.goalIndex];x.push(new X(A.plan[0],A.plan[1],0)),x.push(new X(C.plan[0],C.plan[1],0))}this.chart.add(new ir(new At().setFromPoints(x),this.lineMat(Fn,.22,0,1)))}{const x=[];for(const A of this.L.planets){if(A.progress===null||A.progress===void 0||A.progress<=0)continue;const C=32,R=4.6;for(let L=0;L<C;L++){const U=Math.PI/2-L/C*A.progress*Math.PI*2,I=Math.PI/2-(L+1)/C*A.progress*Math.PI*2;x.push(new X(A.plan[0]+R*Math.cos(U),A.plan[1]+R*Math.sin(U),0)),x.push(new X(A.plan[0]+R*Math.cos(I),A.plan[1]+R*Math.sin(I),0))}}x.length&&this.chart.add(new ir(new At().setFromPoints(x),this.lineMat(ac,.55,0,1)))}this.guestTails=(()=>{const x=[],A=[];for(const L of this.L.guests){const U=L.tailDir*Math.PI/180,I=Math.cos(U),F=Math.sin(U),O=-F,j=I,G=5;for(let W=0;W<G;W++)for(const N of[W/G,(W+1)/G]){const k=Math.sin(N*2.5)*1.1;x.push(L.plan[0]-I*L.tailLen*N+O*k,L.plan[1]-F*L.tailLen*N+j*k,0),A.push(L.deep[0]-I*L.tailLen*1.3*N+O*k,L.deep[1]-F*L.tailLen*1.3*N+j*k,L.deep[2])}}const C=new At;C.setAttribute("position",new Ft(new Float32Array(x),3));const R=new ir(C,this.lineMat(Fn,.55,.4,3));return this.chart.add(R),R})();{const x=this.guestTails;x.userData.plan=new Float32Array(x.geometry.attributes.position.array),x.userData.deep=new Float32Array(this.L.guests.flatMap(A=>{const C=A.tailDir*Math.PI/180,R=Math.cos(C),L=Math.sin(C),U=-L,I=R,F=[],O=5;for(let j=0;j<O;j++)for(const G of[j/O,(j+1)/O]){const W=Math.sin(G*2.5)*1.1;F.push(A.deep[0]-R*A.tailLen*1.3*G+U*W,A.deep[1]-L*A.tailLen*1.3*G+I*W,A.deep[2])}return F}))}const g=this.makeGlowTexture(),m=(x,A,C,R)=>{const L=new Aa({map:g,color:C,transparent:!0,opacity:0,blending:al,depthWrite:!1}),U=new bo(L);return U.scale.set(A,A,1),this.chart.add(U),this.glows.push({spr:U,mat:L,getPos:x,maxOpacity:R}),U};m(()=>[0,0,0],20,16767370,this.northVacant?0:.8),m(()=>[0,0,0],40,9873628,this.northVacant?0:.1),this.L.goals.forEach((x,A)=>m(()=>{const C=this.goalPts.geometry.attributes.position.array;return[C[A*3],C[A*3+1],C[A*3+2]]},9,16764280,x.status==="completed"?0:x.status==="paused"?.12:.35)),this.guestGlows=this.L.guests.map((x,A)=>{const C=new Aa({map:g,color:14543103,transparent:!0,opacity:0,blending:al,depthWrite:!1}),R=new bo(C);return R.scale.set(5.5,5.5,1),this.chart.add(R),{spr:R,mat:C,idx:A,breathe:x.review==="needs_review"}});{const x=this.L.dust.deep.length/3;if(x>0){const A=lo(7700),C=Math.max(6,Math.min(26,Math.round(x*.6))),R=Math.min(1,x/24);for(let L=0;L<C;L++){const U=C<=1?0:L/(C-1),I=Math.min(x-1,Math.floor(U*x)),F=new Aa({map:g,color:9410989,transparent:!0,opacity:0,depthWrite:!1}),O=new bo(F),j=30+A()*26;O.scale.set(j,j,1),O.position.set(this.L.dust.deep[I*3],this.L.dust.deep[I*3+1],this.L.dust.deep[I*3+2]-4),O.visible=!1,O.renderOrder=-1,this.chart.add(O);const G=Math.hypot(this.L.dust.deep[I*3],this.L.dust.deep[I*3+1]),W=Math.min(1.15,Math.max(.3,1.25-G/240));this.dustRiver.push({spr:O,mat:F,base:.06*R*W*(.7+A()*.6)})}}}for(const[x,A,C,R,L,U]of[[150,70,-120,260,8017464,.13],[-170,-60,-100,300,6119536,.1],[0,120,-140,200,4608634,.085]]){const I=new Aa({map:g,color:L,transparent:!0,opacity:0,depthWrite:!1}),F=new bo(I);F.position.set(x,A,C),F.scale.set(R,R,1),F.visible=!1,this.scene.add(F),this.nebulae.push({mat:I,op:U,spr:F})}this.buildLabels();const p=this.renderer.getContext(),_=p.getExtension("WEBGL_debug_renderer_info"),v=_?String(p.getParameter(_.UNMASKED_RENDERER_WEBGL)):"";this.softGL=/swiftshader|llvmpipe|software/i.test(v),this.composer=new bE(this.renderer),this.composer.addPass(new b2(this.scene,this.camera)),this.bloom=new x2({luminanceThreshold:.65,intensity:0,mipmapBlur:!0}),this.fxPass=new E2(this.camera,this.bloom),this.composer.addPass(this.fxPass),this.composer.setSize(this.heart.clientWidth||1600,this.heart.clientHeight||900),this.morphables=[this.dimPts,this.dimBgPts,this.litPts,this.goalPts,c,this.northPts,this.planetPts,this.planetInnerPts,this.moonPts,u,this.guestPts,f,h,this.guestTails,d],this.shapeLines&&this.morphables.push(this.shapeLines),this.asterLinks&&this.morphables.push(this.asterLinks);for(const x of[this.goalPts,this.planetPts,this.planetInnerPts,this.moonPts,this.guestPts,this.guestTails])x.userData.orbitManaged=!0;const M=this.L.seats.filter(x=>x.goalIndex===null);if(M.length){const x=M.flatMap(C=>{const R=C.angle*Math.PI/180;return[fa*Math.cos(R),fa*Math.sin(R),0]}),A=this.makePoints({plan:x,deep:x.slice(),size:M.map(()=>2),opacity:M.map(()=>.16),core:M.map(()=>0),ring:M.map(()=>1),color:M.flatMap(()=>[.961,.918,.824])});this.morphables.push(A)}this.goalPeriods=this.L.goals.map((x,A)=>150+A*36),this.planetPeriods=this.L.planets.map((x,A)=>100+A*14),this.guestPeriods=this.L.guests.map((x,A)=>26+A*6.5),this.goalPhase=this.L.goals.map(()=>0),this.planetPhase=this.L.planets.map(()=>0),this.guestPhase=this.L.guests.map(()=>0),this.guestDeepBase=this.L.guests.map(x=>x.deep.slice()),this.planetDeepBase=this.L.planets.map(x=>x.deep.slice()),this.goalDeepBase=this.L.goals.map(x=>x.deep.slice()),this.L.planets.forEach((x,A)=>{for(let C=0;C<Math.min(x.taskCount,5);C++)this.moonPlanet.push(A)}),this.moonDeepBase=[];for(let x=0;x<this.L.moons.deep.length;x+=3)this.moonDeepBase.push(this.L.moons.deep.slice(x,x+3));const y=this.guestTails;this.L.guests.forEach((x,A)=>{const C=[];for(let R=0;R<10;R++){const L=(A*10+R)*3;C.push([y.userData.deep[L]-x.deep[0],y.userData.deep[L+1]-x.deep[1],y.userData.deep[L+2]-x.deep[2]])}this.tailOffsets.push(C)});const T=(x,A)=>{const C=x.geometry.attributes.position.array;return[C[A*3],C[A*3+1],C[A*3+2]]};this.hoverables=[{title:"北极星",info:this.northVacant?"虚位 · 点击立星":i.north_star.split(/[，。]/)[0],pos:()=>[0,0,0]},...this.L.goals.map((x,A)=>({title:x.title,info:x.status==="completed"?"刻痕星 · 已镌刻":x.status==="paused"?"目标恒星 · 暂停":"目标恒星",pos:()=>T(this.goalPts,A)})),...this.L.planets.map((x,A)=>({title:x.title,info:`${x.status==="active"?"行星 · 在轨":"行星 · 归档"} · 任务 ${x.taskCount}`+(x.progress!==null&&x.progress!==void 0?` · 进度 ${Math.round(x.progress*100)}%`:""),pos:()=>T(this.planetPts,A)})),...this.L.guests.map((x,A)=>({title:x.title,info:`客星 · ${x.date} · ${x.strength}${x.review==="needs_review"?" · 待评审":""}`,pos:()=>T(this.guestPts,A)}))],this.clickables=[{kind:"north",id:"north",idx:-1,title:"北极星",pos:()=>[0,0,0]},...this.L.goals.map((x,A)=>({kind:"goal",id:x.id,idx:A,title:x.title,pos:()=>T(this.goalPts,A)})),...this.L.planets.map((x,A)=>({kind:"planet",id:x.id,idx:A,title:x.title,pos:()=>T(this.planetPts,A)})),...this.L.guests.map((x,A)=>({kind:"guest",id:x.id,idx:A,title:x.title,pos:()=>T(this.guestPts,A)})),...this.L.lit.skills.map((x,A)=>({kind:"skill",id:x.id,idx:A,title:x.label,pos:()=>T(this.litPts,A)}))],this.selRing=new Oc(new At().setFromPoints(this.circlePoints(3.2,48)),new ws({color:Jf,transparent:!0,opacity:.8,depthWrite:!1})),this.selRing.visible=!1,this.chart.add(this.selRing);const S=new ResizeObserver(()=>this.onResize());S.observe(this.heart),this.resizeObserver=S,window.addEventListener("pointermove",this.onPointerMoveWindow,{passive:!0}),window.addEventListener("pointermove",this.onPointerActive,{passive:!0}),window.addEventListener("click",this.onClickWindow),window.addEventListener("keydown",this.onKeydown),window.addEventListener("wheel",this.onWheel,{passive:!0}),this.canvas.addEventListener("pointerdown",x=>{var A;this.focusToken+=1,(A=this.focusTween)==null||A.kill(),this.focusTween=null,!(this.coarsePointer||this.state.t>=.5)&&(this.dragging=!0,this.dragLastX=x.clientX,this.dragLastT=performance.now(),this.dragDist=0,this.spinVel=0,this.canvas.setPointerCapture(x.pointerId))}),this.canvas.addEventListener("pointermove",x=>{if(!this.dragging)return;const A=performance.now(),C=x.clientX-this.dragLastX,R=Math.max((A-this.dragLastT)/1e3,.008);this.dragLastX=x.clientX,this.dragLastT=A,this.dragDist+=Math.abs(C);const L=C*.004;this.chart.rotation.z+=L,this.spinVel=this.spinVel*.75+L/R*.25});const E=()=>{this.dragging=!1};this.canvas.addEventListener("pointerup",E),this.canvas.addEventListener("pointercancel",E),this.coarsePointer&&(this.controls=new Iy(this.camera,this.canvas),this.controls.enableRotate=!1,this.controls.enableDamping=!0,this.controls.dampingFactor=.08,this.controls.enableZoom=!0,this.controls.zoomSpeed=.9,this.controls.enablePan=!0,this.controls.panSpeed=.8),this.guestBaseOpacity=new Float32Array(this.guestPts.geometry.attributes.aOpacity.array),this.onResize(),this.applyMorph(),r.initialState==="deepspace"&&this.goTo(1,!0),this.loop()}goalRadials(){const e=this.goalPts.geometry.attributes.position.array;return this.L.goals.map((t,i)=>({id:t.id,seatName:t.seatName,r:Math.hypot(e[i*3],e[i*3+1])}))}planetRadials(){const e=this.planetPts.geometry.attributes.position.array;return this.L.planets.map((t,i)=>({id:t.id,r:Math.hypot(e[i*3],e[i*3+1])}))}goTo(e,t=!1){var i;if(this.tween&&this.tween.kill(),this.focusToken+=1,(i=this.focusTween)==null||i.kill(),this.focusTween=null,this.closeDetail(),t||this.reducedMotion){this.state.t=e,this.applyMorph();return}this.tween=sl.to(this.state,{t:e,duration:2.4,ease:"power2.inOut",onUpdate:()=>this.applyMorph()})}focusStar(e){var s;const t=this.clickables.findIndex(a=>a.id===e);if(t<0||this.disposed)return!1;this.lastPointerActive=performance.now();const i=++this.focusToken;(s=this.focusTween)==null||s.kill(),this.focusTween=null;const r=()=>{i!==this.focusToken||this.disposed||this.runFocus(t,i)};return this.state.t>.5?(this.tween&&this.tween.kill(),this.closeDetail(),this.reducedMotion?(this.state.t=0,this.applyMorph(),r(),!0):(this.tween=sl.to(this.state,{t:0,duration:2.4,ease:"power2.inOut",onUpdate:()=>this.applyMorph(),onComplete:r}),!0)):(r(),!0)}runFocus(e,t){const i=this.clickables[e],r=()=>{t===this.focusToken&&!this.disposed&&this.openDetail(e)},s=i.pos();if(Math.hypot(s[0],s[1])<1){r();return}let l=90-(Math.atan2(s[1],s[0])*180/Math.PI+this.chart.rotation.z*180/Math.PI);l=(l+540)%360-180;const c=this.chart.rotation.z+l*Math.PI/180;if(this.reducedMotion){this.chart.rotation.z=c,r();return}this.focusTween=sl.to(this.chart.rotation,{z:c,duration:1.1,ease:"power2.inOut",onComplete:r})}toggle(){this.goTo(this.state.t>.5?0:1)}setReveal(e){if(!(e===this.reveal||this.disposed)){this.reveal=e;for(const{t}of this.labelObjs)this.chart.remove(t),t.dispose();this.labelObjs=[],this.goalLabelGroups=[],this.buildLabels(),this.applyMorph()}}deselect(){this.closeDetail()}dispose(){var e,t,i;this.disposed=!0,(e=this.resizeObserver)==null||e.disconnect(),cancelAnimationFrame(this.rafId),this.tween&&this.tween.kill(),(t=this.focusTween)==null||t.kill(),window.removeEventListener("pointermove",this.onPointerMoveWindow),window.removeEventListener("pointermove",this.onPointerActive),window.removeEventListener("click",this.onClickWindow),window.removeEventListener("keydown",this.onKeydown),window.removeEventListener("wheel",this.onWheel),(i=this.controls)==null||i.dispose(),this.scene.traverse(r=>{const s=r;s.geometry&&s.geometry.dispose();const a=s.material;Array.isArray(a)?a.forEach(o=>o.dispose()):a==null||a.dispose()}),this.composer.dispose(),this.renderer.dispose();for(const r of[this.bgStone,this.bgDeep,this.bgDusk,this.vignette,this.tooltip])r.remove();this.canvas.remove()}fitPlanCamera(){const e=this.heart.clientWidth||1600,t=this.heart.clientHeight||900,i=Math.tan(this.camera.fov*Math.PI/360);this.camPlan.pos.z=(ao+16)/(i*Math.min(1,e/t))}bakeBackgrounds(){const e=Af("rgb"),t=(a,o,l)=>{const c=e(fA([a,o],"oklch")(l));return[Math.round(c.r*255),Math.round(c.g*255),Math.round(c.b*255)]},i=t("#1c2c4e","#10172c",.4),r=t("#182642","#0d1322",.4),s=a=>{const c=document.createElement("canvas");c.width=1024,c.height=640;const u=c.getContext("2d"),f=a==="stone",h=a==="dusk",d=f?[37,64,94]:h?i:[36,44,62],g=f?[29,52,80]:h?r:[26,31,46],m=u.createLinearGradient(0,0,0,640);m.addColorStop(0,`rgb(${d.join(",")})`),m.addColorStop(1,`rgb(${g.join(",")})`),u.fillStyle=m,u.fillRect(0,0,1024,640);const p=lo(f?41:h?43:42);for(let y=0;y<9;y++){const T=p()*1024,S=p()*640,E=120+p()*260,b=p()>.5,x=(f?.05:h?.04:.035)*(.7+p()*.6),A=u.createRadialGradient(T,S,0,T,S,E);A.addColorStop(0,b?`rgba(70,98,132,${x})`:`rgba(10,20,36,${x})`),A.addColorStop(1,"rgba(0,0,0,0)"),u.fillStyle=A,u.fillRect(T-E,S-E,E*2,E*2)}if(h){const y=u.createRadialGradient(512,396.8,0,512,396.8,348.16);y.addColorStop(0,"rgba(196,138,64,0.13)"),y.addColorStop(.55,"rgba(150,100,52,0.05)"),y.addColorStop(1,"rgba(150,100,52,0)"),u.fillStyle=y,u.fillRect(0,0,1024,640)}const _=u.getImageData(0,0,1024,640),v=f?.028:h?.04:.05,M=f?.045:h?.032:.02;for(let y=0;y<640;y++){const T=y/640;for(let S=0;S<1024;S++){const E=S/1024,b=Math.exp(-Math.pow((E*.82+T*.57-.78)*5,2))*v,x=(p()-.5)*M,A=(y*1024+S)*4,C=(b+x)*255;_.data[A]=Math.max(0,Math.min(255,_.data[A]+C*.9)),_.data[A+1]=Math.max(0,Math.min(255,_.data[A+1]+C*.88)),_.data[A+2]=Math.max(0,Math.min(255,_.data[A+2]+C*.82))}}return u.putImageData(_,0,0),c};this.bgStone.style.backgroundImage=`url(${s("stone").toDataURL("image/png")})`,this.bgDusk.style.backgroundImage=`url(${s("dusk").toDataURL("image/png")})`,this.bgDusk.style.opacity="0",this.bgDeep.style.backgroundImage=`url(${s("deep").toDataURL("image/png")})`,this.bgDeep.style.opacity="0"}applyBackground(e,t){e<=t?(this.bgDusk.style.opacity=String(e/t),this.bgDeep.style.opacity="0"):(this.bgDusk.style.opacity="1",this.bgDeep.style.opacity=String((e-t)/(1-t)))}lineMat(e,t,i,r=1){const s=new ws({color:e,transparent:!0,opacity:t,depthWrite:!1});return this.fadeMats.push({mat:s,plan:t,deep:i,ch:r}),s}circlePoints(e,t=160){const i=[];for(let r=0;r<=t;r++){const s=r/t*Math.PI*2;i.push(new X(e*Math.cos(s),e*Math.sin(s),0))}return i}buildLinework(){const e=this.L,t=this.lineMat(Fn,.42,0,1),i=this.lineMat(Fn,.55,0,1),r=this.lineMat(Fn,.18,0,1),s=this.lineMat(Fn,.08,0,1),a=this.lineMat(Fn,.5,0,1),o=this.lineMat(Fn,.52,.12,2),l=this.lineMat(Fn,.35,0,1),c=(d,g,m=!1)=>{const p=new At().setFromPoints(d),_=m?new Oc(p,g):new _l(p,g);return this.chart.add(_),_},u=lo(53),f=(d,g,m,p)=>{const _=[];for(let v=0;v<=4;v++){const M=d+(g-d)*v/4,T=(m+(v>0&&v<4?(u()-.5)*1.4:0))*Math.PI/180;_.push(new X(M*Math.cos(T),M*Math.sin(T),0))}c(_,p)};for(const[d,g]of[[fa,t],[t_,t],[ss,i],[oc,a],[ao,a]])c(this.circlePoints(d),g,!0);{const d=[];for(let g=18;g<=342;g+=2){const m=g*Math.PI/180;d.push(new X(oo*Math.cos(m),oo*Math.sin(m),0))}c(d,t)}{const d=[];for(let m=0;m<360;m+=6){const p=m*Math.PI/180,_=ss+(m%30===0?3.25:1.5);d.push(new X(ss*Math.cos(p),ss*Math.sin(p),0)),d.push(new X(_*Math.cos(p),_*Math.sin(p),0))}const g=new At().setFromPoints(d);this.chart.add(new ir(g,i))}const h=d=>(d=d%360,d>180&&(d-=360),d<-180&&(d+=360),d);for(const d of e.sectors){Math.abs(h(d.start))>=12&&f(oo,ss,d.start,r);const g=Math.max(1,Math.round(d.count/6)),m=[];for(let _=1;_<g;_++)m.push(_/g+(u()-.5)*.5/g);m.sort();for(const _ of m){const v=d.start+d.width*_;Math.abs(h(v))>=12&&f(oo,ss,v,s)}const p=d.start*Math.PI/180;c([new X(oc*Math.cos(p),oc*Math.sin(p),0),new X(ao*Math.cos(p),ao*Math.sin(p),0)],a)}{const d=[],g=[],m=e.lit.plan,p=e.lit.deep;for(let M=0;M<e.lit.links.length;M+=2){const y=e.lit.links[M]*3,T=e.lit.links[M+1]*3;d.push(new X(m[y],m[y+1],0)),d.push(new X(m[T],m[T+1],0)),g.push(p[y],p[y+1],p[y+2],p[T],p[T+1],p[T+2])}const _=new At().setFromPoints(d),v=new ir(_,o);this.chart.add(v),this.asterLinks=v,this.asterLinks.userData.plan=new Float32Array(d.flatMap(M=>[M.x,M.y,M.z])),this.asterLinks.userData.deep=new Float32Array(g)}{const d=[],g=e.court.plan;for(const[p,_]of e.court.links)d.push(new X(g[p*3],g[p*3+1],0)),d.push(new X(g[_*3],g[_*3+1],0));const m=new At().setFromPoints(d);this.chart.add(new ir(m,l))}c(this.circlePoints(4.2,64),this.lineMat(Fn,.55,0,1),!0)}makePoints(e,t){const{plan:i,deep:r,size:s,opacity:a,core:o,ring:l,color:c}=e,u=new At;u.setAttribute("position",new Ft(new Float32Array(i),3)),u.setAttribute("aSize",new Ft(new Float32Array(s),1)),u.setAttribute("aOpacity",new Ft(new Float32Array(a),1)),u.setAttribute("aCore",new Ft(new Float32Array(o),1)),u.setAttribute("aRing",new Ft(new Float32Array(l),1)),u.setAttribute("aColor",new Ft(new Float32Array(c),3));const f=new an({transparent:!0,depthWrite:!1,blending:kr,uniforms:{uScale:{value:1},uGlobal:{value:1}},vertexShader:`
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
      `}),h=new Pv(u,f);return h.userData.plan=new Float32Array(i),h.userData.deep=new Float32Array(r),e.deepColor&&this.colored.push({pts:h,plan:new Float32Array(c),deep:new Float32Array(e.deepColor)}),e.deepCore&&this.coreLerp.push({pts:h,plan:new Float32Array(o),deep:new Float32Array(e.deepCore)}),(t??this.chart).add(h),h}addTier(e,t,i){this.tiered.push({pts:e,baseSize:new Float32Array(e.geometry.attributes.aSize.array),baseOp:i===null?null:new Float32Array(e.geometry.attributes.aOpacity.array),ds:t,dop:i??1})}makeGlowTexture(){const e=document.createElement("canvas");e.width=e.height=128;const t=e.getContext("2d"),i=t.createRadialGradient(64,64,0,64,64,64);return i.addColorStop(0,"rgba(255,255,255,1)"),i.addColorStop(.25,"rgba(255,255,255,0.35)"),i.addColorStop(1,"rgba(255,255,255,0)"),t.fillStyle=i,t.fillRect(0,0,128,128),new Dv(e)}addLabel(e,t={}){const{size:i=3.4,color:r=Fn,font:s=dA,pos:a=[0,0,0],deepPos:o=null,rotZ:l=0,anchorX:c="center",fade:u="band",prio:f=2}=t,h=new Th;return h.text=e,h.font=s,h.fontSize=i,h.color=r,h.anchorX=c,h.anchorY="middle",h.position.set(a[0],a[1],a[2]??0),h.rotation.z=l,h.material.transparent=!0,h.outlineWidth="5%",h.outlineColor=726566,h.outlineOpacity=.85,this.chart.add(h),this.labelObjs.push({t:h,fade:u,planPos:a.slice(),deepPos:o?o.slice():null,rotZ:l,prio:f,grpId:this.labelGrpSeq++,ca:1,caTarget:1}),h}addSegmentedLabel(e,t){const{size:i=3.6,color:r=15652502,pos:s,align:a="left",fade:o="goal",goalIdx:l=-1,prio:c=1}=t,u=this.labelGrpSeq++,f=e.split(/([A-Za-z0-9.]+)/).filter(Boolean),h={goalIdx:l,segs:[],base:[],anchor:s.slice()},d=f.map(m=>{const p=/^[A-Za-z0-9.]+$/.test(m),_=new Th;return _.text=m,_.font=p?pA:ar,_.fontSize=i,_.color=r,_.anchorX="left",_.anchorY="middle",_.material.transparent=!0,_.outlineWidth="5%",_.outlineColor=726566,_.outlineOpacity=.85,this.chart.add(_),this.labelObjs.push({t:_,fade:o,planPos:s.slice(),deepPos:null,rotZ:0,prio:c,grpId:u,ca:1,caTarget:1}),h.segs.push(_),_});l>=0&&this.goalLabelGroups.push(h),this.segPending+=d.length;let g=d.length;d.forEach(m=>m.sync(()=>{if(this.segPending-=1,g-=1,g===0){const p=d.map(M=>{const y=M.textRenderInfo&&M.textRenderInfo.blockBounds;return y?Math.max(.1,y[2]-y[0]):M.text.length*i*.6}),_=p.reduce((M,y)=>M+y,0)+.4*(d.length-1);let v=s[0]-(a==="right"?_:a==="center"?_/2:0);d.forEach((M,y)=>{M.position.set(v,s[1],0),v+=p[y]+.4}),h.base=d.map(M=>[M.position.x,M.position.y])}}))}followGoal(e,t){this.goalLabelGroups.push({goalIdx:e,segs:t,base:t.map(i=>[i.position.x,i.position.y]),anchor:[]})}buildLabels(){const e=this.L;for(const t of e.sectors){const i=t.start+t.width/2,r=Array.from(this.reveal?t.name:t.asterism),s=this.reveal?ac:11907232,a=3.2*1.25/lc*(180/Math.PI),o=i-a*(r.length-1)/2;r.forEach((l,c)=>{const u=(o+c*a)*Math.PI/180;this.addLabel(l,{size:3.2,color:s,font:ar,fade:"band",pos:[lc*Math.cos(u),lc*Math.sin(u),0],rotZ:u+Math.PI/2})})}e.goals.forEach((t,i)=>{const r=Math.cos(t.angle*Math.PI/180),s=r>.35?"left":r<-.35?"right":"center",a=fa+8,o=t.angle*Math.PI/180,l=a*Math.cos(o)+(s==="left"?1:s==="right"?-1:0),c=a*Math.sin(o);if(t.status==="completed"){this.addSegmentedLabel(t.title,{size:3.6,color:10130038,align:s,goalIdx:i,pos:[l,c,0]});return}if(!this.reveal){const u=this.addLabel(t.seatName??t.title,{size:3.8,color:15652502,font:ar,fade:"goal",pos:[l,c,0]});this.followGoal(i,[u]);return}this.addSegmentedLabel(t.title,{size:3.6,color:15652502,align:s,goalIdx:i,pos:[l,c,0]})});for(const t of e.seats){if(t.goalIndex!==null)continue;const i=t.angle*Math.PI/180,r=fa+8;this.addLabel(`${t.name}·虚位`,{size:2.8,color:9274994,font:ar,fade:"goal",pos:[r*Math.cos(i),r*Math.sin(i),0]})}if(this.northVacant)this.addLabel("虚位",{size:3.8,color:9274994,font:ar,anchorX:"left",pos:[6.5,.4,0],deepPos:[10.5,-10.6,0],fade:"north",prio:0});else if(!this.reveal)this.addLabel("北极星",{size:3.8,color:15652502,font:ar,anchorX:"left",pos:[6.5,.4,0],deepPos:[10.5,-10.6,0],fade:"north",prio:0});else{const t=this.snapshot.north_star.split(/[，。]/)[0],i=t.indexOf("成为"),r=i>0?[t.slice(0,i+2),t.slice(i+2)]:[t,""];this.addLabel(r[0],{size:3.8,color:15652502,font:ar,anchorX:"left",pos:[6.5,3.4,0],deepPos:[10.5,-8.5,0],fade:"north",prio:0}),r[1]&&this.addLabel(r[1],{size:3.8,color:15652502,font:ar,anchorX:"left",pos:[6.5,-2.6,0],deepPos:[10.5,-13.6,0],fade:"north",prio:0})}this.labelsPending=this.labelObjs.length;for(const{t}of this.labelObjs)t.sync(()=>{this.labelsPending-=1})}applyMorph(){var c,u;const e=this.state.t,t=wu(e,this.state.w1),i=wu(e,this.state.w2),r=wu(e,this.state.w3);this.state.ch1=t,this.state.ch2=i,this.state.ch3=r;for(const f of this.morphables){if(f.userData.orbitManaged)continue;const h=f.geometry.attributes.position,d=f.userData.plan,g=f.userData.deep,m=h.array;for(let p=0;p<m.length;p++)m[p]=d[p]+(g[p]-d[p])*i;h.needsUpdate=!0}this.chart.rotation.x=-1.05*i,this.camera.position.lerpVectors(this.camPlan.pos,this.camDeep.pos,i),this.camera.lookAt(new X().lerpVectors(this.camPlan.look,this.camDeep.look,i));for(const{mat:f,plan:h,deep:d,ch:g}of this.fadeMats){const m=g===1?t:g===3?r:i;f.opacity=h+(d-h)*m}for(const{mat:f,fn:h}of this.fadeFns)f.opacity=h(t,i,r);for(const{t:f,fade:h,planPos:d,deepPos:g}of this.labelObjs)h==="band"?(f.material.opacity=1-i,f.visible=i<.98):h==="north"&&g&&(f.material.opacity=1-.25*i,f.position.set(d[0]+(g[0]-d[0])*i,d[1]+(g[1]-d[1])*i,0));for(const f of this.glows){f.mat.opacity=f.maxOpacity*r,f.spr.visible=f.mat.opacity>.004;const h=f.getPos();f.spr.position.set(h[0],h[1],h[2])}for(const f of this.nebulae)f.mat.opacity=f.op*r,f.spr.visible=f.mat.opacity>.004;const s=Math.exp(-Math.pow((i-this.state.duskPos)/.13,2))*this.state.duskAmt,a=this.glows[0];if(s>.01){a.mat.opacity=Math.min(1,Math.max(a.mat.opacity,a.maxOpacity*s*.6)),a.spr.visible=!0;const f=20*(1+.55*s);a.spr.scale.set(f,f,1)}else a.spr.scale.set(20,20,1);for(const f of[this.dimPts,this.dimBgPts]){const h=f.geometry.attributes.aOpacity,d=f.geometry.attributes.aSize,g=f.geometry.attributes.aRing,m=f.userData.baseOpacity,p=f.userData.baseSize,_=f.userData.baseRing,v=f.userData.deepOpScale,M=f.userData.deepSizeScale,y=f.userData.filler;for(let T=0;T<h.array.length;T++){const S=y[T]?this.state.density:1;h.array[T]=m[T]*S*(1+(v[T]-1)*r),d.array[T]=p[T]*(1+(M[T]-1)*r),g.array[T]=_[T]*(1-.55*r)}h.needsUpdate=!0,d.needsUpdate=!0,g.needsUpdate=!0}for(const f of this.tiered){const h=f.pts.geometry.attributes.aSize,d=h.array,g=1+(f.ds-1)*r;for(let m=0;m<d.length;m++)d[m]=f.baseSize[m]*g;if(h.needsUpdate=!0,f.baseOp){const m=f.pts.geometry.attributes.aOpacity,p=m.array,_=1+(f.dop-1)*r;for(let v=0;v<p.length;v++)p[v]=f.baseOp[v]*_;m.needsUpdate=!0}}for(const f of this.colored){const h=f.pts.geometry.attributes.aColor,d=h.array;for(let g=0;g<d.length;g++)d[g]=f.plan[g]+(f.deep[g]-f.plan[g])*i;h.needsUpdate=!0}for(const f of this.coreLerp){const h=f.pts.geometry.attributes.aCore,d=h.array;for(let g=0;g<d.length;g++)d[g]=f.plan[g]+(f.deep[g]-f.plan[g])*i;h.needsUpdate=!0}for(const f of this.dustRiver)f.mat.opacity=f.base*r,f.spr.visible=f.mat.opacity>.004;this.applyBackground(i,this.state.duskPos),this.fxPass.enabled=!this.softGL&&r>.02,this.bloom.intensity=.7*r*this.state.bloom,this.vignette.style.opacity=String(.55+.45*i);const o=String(1-i),l=this.opts.domRefs;l!=null&&l.cartouche&&(l.cartouche.style.opacity=o),l!=null&&l.briefing&&(l.briefing.style.opacity=o),l!=null&&l.toggle&&(l.toggle.textContent=e>.5?"图":"境"),(u=(c=this.opts).onMorph)==null||u.call(c,e)}screenOf(e){const t=new X(e[0],e[1],e[2]??0);this.chart.localToWorld(t),t.project(this.camera);const i=this.heart.getBoundingClientRect();return[i.left+(t.x*.5+.5)*i.width,i.top+(-t.y*.5+.5)*i.height]}onPointerMove(e){this.hoverIdx=-1;let t=26;this.hoverables.forEach((i,r)=>{const[s,a]=this.screenOf(i.pos()),o=Math.hypot(s-e.clientX,a-e.clientY);o<t&&(t=o,this.hoverIdx=r)})}updateTooltip(){const e=this.tooltip;if(this.hoverIdx<0||!this.hoverables[this.hoverIdx]){e.style.display="none";return}const t=this.hoverables[this.hoverIdx],[i,r]=this.screenOf(t.pos());e.innerHTML='<div class="tt-title"></div><div class="tt-info"></div>',e.querySelector(".tt-title").textContent=t.title,e.querySelector(".tt-info").textContent=t.info,e.style.display="block";const s=e.offsetWidth;e.style.left=Math.min(window.innerWidth-s-12,i+16)+"px",e.style.top=Math.max(10,r-44)+"px"}detailRows(e){var a,o;const t=this.snapshot;if(e.kind==="north"){const l=t.north;return this.northVacant?[["类型","北极星 · 虚位"],["铭文","（尚未立星 — 点「重刻」写下北极星）"]]:[["类型","北极星"],["铭文",l.full||t.north_star],["简称",l.brief||"—"],["可见性",l.visibility==="public"?"可公开":"仅本地"]]}if(e.kind==="goal"){const l=t.goals.find(f=>f.id===e.id)??{status:((a=this.L.goals[e.idx])==null?void 0:a.status)??"active",start:"",target:"",summary:""},c=l.status==="completed"?"已镌刻":l.status==="paused"?"已暂停":"进行中",u=(o=this.L.goals[e.idx])==null?void 0:o.seatName;return[["状态",c],...u?[["星位",u]]:[],["起始",l.start||"—"],["目标",l.target||"—"],["铭文",l.summary||"—"]]}if(e.kind==="planet"){const l=t.projects[e.idx],c=this.L.planets[e.idx].goalIndex;return[["状态",l.status==="active"?"在轨":"归档"],["所属目标",c>=0?this.L.goals[c].title:"（自由轨道）"],["任务",`${l.task_count} 项`],["进度",l.progress===null||l.progress===void 0?"—":`${Math.round(l.progress*100)}%`],["时间范围",l.time_range||"—"]]}if(e.kind==="guest"){const l=t.evidence.find(c=>c.id===this.L.guests[e.idx].id)??this.L.guests[e.idx];return[["类型","type"in l?l.type:"—"],["强度",l.strength||"—"],["日期",l.date||"—"],["评审","review_status"in l&&l.review_status==="needs_review"?"待评审":"已入座"],["摘要","summary"in l&&l.summary?l.summary:"—"]]}const i=this.L.lit.skills[e.idx],r=t.evidence.filter(l=>l.skill_ids.includes(i.id)).slice(0,3).map(l=>l.title),s=[["类别",i.category],["状态",i.status],["关联证据",`${i.evidenceCount} 条`]];return r.forEach((l,c)=>s.push([c===0?"入座证据":"",`· ${l}`])),s}openDetail(e){var i,r;this.selectedIdx=e;const t=this.clickables[e];(r=(i=this.opts).onSelect)==null||r.call(i,{kind:t.kind,id:t.id,title:t.title,rows:this.detailRows(t)})}closeDetail(){var e,t;this.selectedIdx<0||(this.selectedIdx=-1,this.selRing.visible=!1,(t=(e=this.opts).onSelect)==null||t.call(e,null))}onClick(e){if(this.dragDist>6){this.dragDist=0;return}const t=e.target;if(!t.isConnected||t.closest("[data-starmap-ui]"))return;let i=-1,r=26;this.clickables.forEach((s,a)=>{const[o,l]=this.screenOf(s.pos()),c=Math.hypot(o-e.clientX,l-e.clientY);c<r&&(r=c,i=a)}),i>=0?this.openDetail(i):this.closeDetail()}updatePointScale(){const t=this.renderer.domElement.height/(2*Math.tan(this.camera.fov*Math.PI/360));for(const i of this.morphables){const r=i;r.isPoints&&(r.material.uniforms.uScale.value=t)}}onResize(){const e=this.heart.clientWidth||1,t=this.heart.clientHeight||1;this.renderer.setSize(e,t),this.composer.setSize(e,t),this.camera.aspect=e/t,this.camera.updateProjectionMatrix(),this.fitPlanCamera(),this.controls&&(this.controls.minDistance=this.camPlan.pos.z*.65,this.controls.maxDistance=this.camPlan.pos.z*1.6),this.updatePointScale(),this.applyMorph()}loop(){if(this.disposed)return;this.rafId=requestAnimationFrame(()=>this.loop());const e=Math.min(this.clock.getDelta(),.1),t=this.clock.elapsedTime,{ch2:i,ch3:r}=this.state,s=this.L,a=performance.now(),l=this.dragging||this.hoverIdx>=0||this.selectedIdx>=0||a-this.lastPointerActive<3e3||this.reducedMotion?0:1;this.spinFactor+=(l-this.spinFactor)*Math.min(1,e/.8);const c=Math.PI*2/3600;this.chart.rotation.z+=e*c*this.spinFactor*(1+2.5*Math.sin(i*Math.PI)),!this.dragging&&Math.abs(this.spinVel)>1e-4&&(this.chart.rotation.z+=this.spinVel*e,this.spinVel*=Math.exp(-e/1.2)),this.bgLayer.rotation.z=-.7*i*this.chart.rotation.z;{const h=this.goalPts.geometry.attributes.position,d=s.goals.map((T,S)=>{const E=this.goalDeepBase[S];return this.goalPhase[S]+=e*(2*Math.PI/this.goalPeriods[S])*r,n_(T.plan,E,this.goalPhase[S],i,r)});d.forEach((T,S)=>h.setXYZ(S,T[0],T[1],T[2])),h.needsUpdate=!0;const g=1+.9*i;for(const T of this.goalLabelGroups){if(!T.base.length)continue;const S=d[T.goalIdx],E=s.goals[T.goalIdx].plan;T.segs.forEach((b,x)=>b.position.set(S[0]+(T.base[x][0]-E[0])*g,S[1]+(T.base[x][1]-E[1])*g,0))}const m=this.planetPts.geometry.attributes.position,p=this.planetInnerPts.geometry.attributes.position,_=this.moonPts.geometry.attributes.position,v=s.planets.map((T,S)=>{const E=this.planetDeepBase[S];this.planetPhase[S]+=e*(2*Math.PI/this.planetPeriods[S])*r;const b=T.goalIndex,x=b>=0?this.goalDeepBase[b]:[0,0,0],A=b>=0?d[b]:[0,0,0],C=b>=0?s.goals[b].plan:[0,0,0],R=b>=0?[C[0]+(x[0]-C[0])*i,C[1]+(x[1]-C[1])*i]:[0,0];return i_(T.plan,E,x,R,A,this.planetPhase[S],i,r)});v.forEach((T,S)=>{m.setXYZ(S,T[0],T[1],T[2]),p.setXYZ(S,T[0],T[1],T[2])}),m.needsUpdate=!0,p.needsUpdate=!0,this.moonDeepBase.forEach((T,S)=>{const E=this.moonPlanet[S];E!==void 0&&_.setXYZ(S,T[0]+(v[E][0]-this.planetDeepBase[E][0]),T[1]+(v[E][1]-this.planetDeepBase[E][1]),T[2])}),_.needsUpdate=!0;for(const T of this.orbitRings){const S=d[T.goalIdx];T.ring.position.set(S[0],S[1],S[2]);const E=this.reducedMotion?1:.92+.08*Math.sin(t*.5+T.shimmer);T.ringMat.opacity=.22*r*E,T.ring.visible=T.ringMat.opacity>.004,this.reducedMotion?(T.flowMat.opacity=0,T.flow.visible=!1):(T.phase+=e*(2*Math.PI/46),T.flow.rotation.z=T.phase,T.flowMat.opacity=.5*r*E,T.flow.visible=T.flowMat.opacity>.004)}const M=this.guestPts.geometry.attributes.position,y=this.guestTails.geometry.attributes.position;s.guests.forEach((T,S)=>{const E=this.guestDeepBase[S];this.guestPhase[S]+=e*(2*Math.PI/this.guestPeriods[S])*r;const b=4*r,x=T.plan[0]+(E[0]-T.plan[0])*i+b*Math.cos(this.guestPhase[S]+S*1.3),A=T.plan[1]+(E[1]-T.plan[1])*i+b*Math.sin(this.guestPhase[S]+S*1.3),C=T.plan[2]+(E[2]-T.plan[2])*i;M.setXYZ(S,x,A,C),this.guestGlows[S].spr.position.set(x,A,C),this.tailOffsets[S].forEach((L,U)=>y.setXYZ(S*10+U,x+L[0]*i,A+L[1]*i,C+L[2]*i))}),M.needsUpdate=!0,y.needsUpdate=!0}for(const h of this.labelObjs)h.fade!=="band"&&(h.t.rotation.z=h.rotZ-this.chart.rotation.z*i);this.collisionTick+=1;const u=i>.6;if(u&&this.collisionTick%12===0){const d=this.labelObjs.filter(m=>m.fade!=="band"&&m.t.visible&&m.t.textRenderInfo).map(m=>{const[p,_]=this.screenOf([m.t.position.x,m.t.position.y,0]),v=m.t.textRenderInfo.blockBounds,M=Math.max(.5,v[2]-v[0]),y=Math.max(.5,v[3]-v[1]),[T]=this.screenOf([m.t.position.x+1,m.t.position.y,0]),S=Math.abs(T-p)||1,E=M*S,b=y*S,x=m.t.anchorX==="left"?0:m.t.anchorX==="right"?-E:-E/2;return{r:m,x0:p+x,y0:_-b/2,x1:p+x+E,y1:_+b/2}}),g=new Set;for(let m=0;m<d.length;m++)for(let p=m+1;p<d.length;p++){const _=d[m],v=d[p];_.r.grpId===v.r.grpId||!(Math.min(_.x1,v.x1)-Math.max(_.x0,v.x0)>1&&Math.min(_.y1,v.y1)-Math.max(_.y0,v.y0)>1)||g.add(_.r.prio===v.r.prio?Math.max(_.r.grpId,v.r.grpId):_.r.prio>v.r.prio?_.r.grpId:v.r.grpId)}for(const m of this.labelObjs)m.caTarget=g.has(m.grpId)?0:1}else if(!u)for(const h of this.labelObjs)h.caTarget=1;for(const h of this.labelObjs){if(h.fade==="band")continue;h.ca+=(h.caTarget-h.ca)*Math.min(1,e/.35);const d=h.fade==="north"?1-.25*i:1;h.t.material.opacity=d*h.ca}const f=h=>h<.25?.5-.5*Math.cos(h/.25*Math.PI):h<.45?1:.5+.5*Math.cos((h-.45)/.55*Math.PI);if(this.reducedMotion)for(const h of this.guestGlows)h.mat.opacity=(.34+.3*r)*.925,h.spr.visible=h.mat.opacity>.004;else for(const h of this.guestGlows){const d=.34+.3*r,g=h.breathe?f((t/11+h.idx*.31)%1):.4;h.mat.opacity=d*(.85+.15*g),h.spr.visible=h.mat.opacity>.004;const m=5.5*(1+.4*r);h.spr.scale.set(m,m,1)}{const h=this.guestPts.geometry.attributes.aOpacity;let d=!1;for(let g=0;g<h.array.length;g++)h.array[g]!==this.guestBaseOpacity[g]&&(h.array[g]=this.guestBaseOpacity[g],d=!0);d&&(h.needsUpdate=!0)}if(this.updateTooltip(),this.northVacant){const h=this.northPts.geometry.attributes.aOpacity;h.array[0]=this.reducedMotion?.3:.28+.14*Math.sin(t*.9),h.needsUpdate=!0}if(this.selectedIdx>=0){const h=this.clickables[this.selectedIdx].pos();this.selRing.visible=!0,this.selRing.position.set(h[0],h[1],h[2]??0);const d=this.reducedMotion?1:1+.04*Math.sin(t*3);this.selRing.scale.set(d,d,1)}if(this.controls){this.controls.enabled=this.state.t<.5,this.controls.update();const h=this.controls.target,d=Math.max(-70,Math.min(70,h.x)),g=Math.max(-70,Math.min(70,h.y));(d!==h.x||g!==h.y)&&(this.camera.position.x+=d-h.x,this.camera.position.y+=g-h.y,h.x=d,h.y=g,h.z=0)}this.fxPass.enabled?this.composer.render():this.renderer.render(this.scene,this.camera)}}const gA="/assets/title-v2-b-ibfvihIe.svg";function xA({snapshot:n}){const{name:e=""}=r_(),t=et.useRef(null),i=et.useRef(null),r=et.useRef(null),s=et.useRef(null),a=et.useRef(null),o=et.useRef(null),l=et.useRef(null),[c,u]=et.useState(null),[f,h]=et.useState(!1),[d,g]=et.useState(!1),[m,p]=et.useState(!1),[_,v]=et.useState(()=>localStorage.getItem("nblane.starmap.reveal")==="1"),M=et.useRef(_);M.current=_;const y=s_(e);et.useEffect(()=>{const S=t.current,E=i.current;if(!S||!E)return;let b=null;try{b=new mA(S,E,n,{onSelect:A=>{l.current=null,u(A)},domRefs:{cartouche:r.current,briefing:s.current,toggle:a.current},reveal:M.current})}catch{p(!0);return}o.current=b,window.__starmapProbe=b;const x=l.current;if(x&&performance.now()-x.at<6e3){if(!b.focusStar(x.id)){l.current=null;const A=n.goals.find(C=>C.id===x.id);A&&u({kind:"goal",id:A.id,title:A.title,rows:Qf(A)})}}else l.current=null;return()=>{window.__starmapProbe=void 0,b==null||b.dispose(),o.current=null}},[n]);const T=et.useMemo(()=>{var E;const S=`「${n.counts.evidence_needs_review} 条客星待评审，${n.counts.projects_active} 颗行星在轨。」`;return c_(S,l_(((E=y.data)==null?void 0:E.entries)??[]))},[n,y.data]);return et.useEffect(()=>{const S=E=>{var b;E.key==="Escape"&&(h(!1),g(!1),u(null),l.current=null,(b=o.current)==null||b.deselect())};return window.addEventListener("keydown",S),()=>window.removeEventListener("keydown",S)},[]),me.jsxs("div",{className:`starmap-root${d?" divining":""}`,ref:t,"data-testid":"starmap-root",children:[me.jsxs("div",{className:"starmap-layout",children:[me.jsx("div",{className:"starmap-mount-top",children:me.jsx("img",{className:"starmap-cartouche",ref:r,src:gA,alt:"成长星图"})}),me.jsx("div",{className:"starmap-heart",ref:i,"data-testid":"starmap-heart"}),me.jsx("div",{className:"starmap-mount-bottom",children:me.jsx("div",{className:"starmap-briefing",ref:s,"data-testid":"starmap-briefing",children:T})})]}),!m&&me.jsxs(me.Fragment,{children:[me.jsx("button",{type:"button",className:"starmap-div-btn","data-starmap-ui":!0,"data-testid":"starmap-div-btn","aria-label":"占卜","aria-pressed":d,title:"占卜 — 星尘聚卦",onClick:()=>g(S=>!S),children:"卜"}),me.jsx("button",{type:"button",className:"starmap-toggle",ref:a,"data-starmap-ui":!0,"data-testid":"starmap-toggle","aria-label":"切换 境态/图态",title:"境态 ⇄ 图态",onClick:()=>{var S;return(S=o.current)==null?void 0:S.toggle()},children:"境"}),me.jsx("button",{type:"button",className:"starmap-reveal-toggle","data-starmap-ui":!0,"data-testid":"starmap-reveal-toggle","aria-pressed":_,"aria-label":"显真",title:_?"真·朱文 — 点击钤回古名":"真·白文 — 点击显现真名（已记住此偏好）",onClick:()=>{var E;const S=!_;v(S),localStorage.setItem("nblane.starmap.reveal",S?"1":"0"),(E=o.current)==null||E.setReveal(S)},children:"真"}),me.jsx("button",{type:"button",className:"starmap-catalog-btn","data-starmap-ui":!0,"data-testid":"starmap-catalog-btn","aria-label":"星表","aria-expanded":f,onClick:()=>h(S=>!S),children:"＋"})]}),me.jsx(g_,{profile:e}),me.jsx(d_,{profile:e,open:d,onClose:()=>g(!1)}),me.jsx(x_,{open:f,snapshot:n,profile:e,selection:c,onFocus:S=>{var x;if(((x=o.current)==null?void 0:x.focusStar(S))??!1){l.current={id:S,at:performance.now()};return}l.current=null;const b=n.goals.find(A=>A.id===S);b&&u({kind:"goal",id:b.id,title:b.title,rows:Qf(b)})}}),me.jsx("div",{className:`starmap-detail${c?" open":""}`,"data-starmap-ui":!0,"data-testid":"starmap-detail",children:c&&me.jsx(a_,{selection:c,snapshot:n,profile:e,onSaved:u},`${c.kind}:${c.id}`)}),m&&me.jsxs("div",{className:"starmap-fallback","data-testid":"starmap-fallback",children:[me.jsx("div",{className:"fb-title",children:"成长星图"}),me.jsx("div",{className:"fb-line",children:n.north.is_set?n.north_star:"尚未设置北极星 — 北极星虚位以待。"}),me.jsx("div",{className:"fb-line",children:T}),me.jsx("div",{className:"fb-line",children:"此浏览器不支持 WebGL，以上为静态简报。"})]})]})}export{xA as StarmapView};
