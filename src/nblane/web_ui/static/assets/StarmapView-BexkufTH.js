var Jg=Object.defineProperty;var Qg=(n,e,t)=>e in n?Jg(n,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):n[e]=t;var Ce=(n,e,t)=>Qg(n,typeof e!="symbol"?e+"":e,t);import{r as Ze,j as ne,a as e_,u as t_,b as n_,c as i_,T as r_,n as pa,d as s_,e as a_,L as o_,g as l_,f as c_,h as u_,i as h_,k as ed}from"./index-DhpOXVAI.js";function f_(n){return`${n.getFullYear()}-${String(n.getMonth()+1).padStart(2,"0")}`}function d_(n,e=new Date){const t=f_(e);let i=0,r=0,s=0;for(const o of n)!o.date||!String(o.date).startsWith(t)||(o.kind==="goal.added"?i+=1:o.kind==="goal.completed"?r+=1:o.kind==="north_star.rewritten"&&(s+=1));const a=[];return i>0&&a.push(`本月新立目标 ${i}`),r>0&&a.push(`新镌 ${r} 星`),s>0&&a.push("北极星已重刻"),a.join("，")}function p_(n,e){return e?n.endsWith("。」")?`${n.slice(0,-2)}，${e}。」`:n.endsWith("」")?`${n.slice(0,-1)}，${e}」`:`${n} ${e}`:n}function Mm(n){return n.slice(0,6).reverse().map(e=>e===1)}function m_({lines:n,size:e=44,animated:t=!1}){const i=Mm(n),r=e,s=e*.72,a=s/6;return ne.jsx("div",{className:`hexagram-symbol${t?" casting":""}`,style:{width:r,height:s},"data-testid":"hexagram-symbol","aria-hidden":"true",children:i.map((o,l)=>ne.jsx("div",{className:`hex-yao${o?" solid":" broken"}`,style:{height:a*.52,top:l*a+a*.24},children:!o&&ne.jsx("span",{className:"hex-yao-gap"})},l))})}function g_({phase:n,lines:e,reduced:t}){const i=Ze.useRef(null),r=Ze.useRef({phase:n,lines:e});return r.current={phase:n,lines:e},Ze.useEffect(()=>{const s=i.current;if(!s)return;const a=s.parentElement,o=a.clientWidth,l=a.clientHeight,c=Math.min(window.devicePixelRatio,2);s.width=o*c,s.height=l*c;const u=s.getContext("2d");u.scale(c,c);const f=o*.3,h=l*.48,d=Math.min(96,o*.16),m=d*.72/6,g=E=>h-d*.36+E*m+m/2,p=(()=>{let E=20260924;return()=>(E=E*1664525+1013904223>>>0,E/2**32)})(),_=[];for(let E=0;E<130;E++){const M=Math.floor(p()*6),T=p()<.45,x=T?(p()<.5?-1:1)*(.12+p()*.06):0,y=f+(p()-.5)*d*(T?.76:.96)+x*d,w=g(M)+(p()-.5)*m*.5,C=p()*Math.PI*2,R=(.25+p()*.45)*Math.min(o,l)*.5;_.push({sx:o/2+Math.cos(C)*R*1.25,sy:l/2+Math.sin(C)*R,tx:y,ty:w,delay:p()*.45,size:.8+p()*1.2,gold:p()<.22,seed:p()*1e3})}let v=0;const b=performance.now(),S=E=>{v=requestAnimationFrame(S);const M=(E-b)/1e3,{phase:T,lines:x}=r.current;u.clearRect(0,0,o,l),u.globalCompositeOperation="lighter";const y=Math.min(1,M/1.6),w=T==="casting";for(const U of _){const I=Math.min(1,Math.max(0,(y-U.delay)/(1-U.delay||1))),F=I*I*(3-2*I),N=w&&!t?2.2:.6,Y=Math.sin(M*1.7+U.seed)*N,j=Math.cos(M*1.3+U.seed*1.7)*N,Z=U.sx+(U.tx-U.sx)*F+Y*F,O=U.sy+(U.ty-U.sy)*F+j*F,H=.55+.45*Math.sin(M*2.1+U.seed*3);u.beginPath(),u.arc(Z,O,U.size,0,Math.PI*2),u.fillStyle=U.gold?`rgba(240, 205, 127, ${.5*H*F})`:`rgba(232, 226, 210, ${.4*H*F})`,u.fill()}const R=T==="done"||T==="error"?Mm(x):null,L=Math.floor(M/.12);for(let U=0;U<6;U++){const I=g(U),F=R?R[U]:(U*7+L)%3!==0,N=T==="gather"?Math.max(0,y-.55)*.6:w?.3+.25*Math.sin(M*4+U):.85;if(N<=.01)continue;u.fillStyle=`rgba(240, 205, 127, ${N})`;const Y=Math.max(2,m*.34);if(F)u.fillRect(f-d/2,I-Y/2,d,Y);else{const j=d/2*.76;u.fillRect(f-d/2,I-Y/2,j,Y),u.fillRect(f+d/2-j,I-Y/2,j,Y)}}u.globalCompositeOperation="source-over"};return v=requestAnimationFrame(S),()=>cancelAnimationFrame(v)},[t]),ne.jsx("canvas",{ref:i,className:"starmap-div-ritual-canvas"})}function __({profile:n,open:e,onClose:t}){const i=Ze.useMemo(()=>typeof matchMedia<"u"&&matchMedia("(prefers-reduced-motion: reduce)").matches,[]),[r,s]=Ze.useState("gather"),[a,o]=Ze.useState("play"),[l,c]=Ze.useState(""),[u,f]=Ze.useState(null),[h,d]=Ze.useState(""),[m,g]=Ze.useState(!1),p=Ze.useRef(0),_=async(S,E)=>{const M=++p.current;s("casting"),f(null),d("");try{const T={mode:S,question:E},x=await e_(`/profiles/${encodeURIComponent(n)}/divination`,T);if(M!==p.current)return;f(x),s("done"),window.setTimeout(()=>g(!0),i?0:500)}catch(T){if(M!==p.current)return;d(T instanceof Error?T.message:String(T)),s("error"),window.setTimeout(()=>g(!0),i?0:500)}};if(Ze.useEffect(()=>{if(!e)return;s("gather"),f(null),d(""),g(!1),o("play"),c(""),_("play","");const S=window.setTimeout(()=>s(E=>E==="gather"?"casting":E),1650);return()=>window.clearTimeout(S)},[e]),!e)return null;const v=u==null?void 0:u.hexagram,b=(v==null?void 0:v.symbol_lines)??[1,1,1,1,1,1];return ne.jsxs("div",{className:`starmap-div-root${m?" docked":""}`,"data-starmap-ui":!0,"data-testid":"divination-root",children:[ne.jsx("div",{className:"starmap-div-overlay",children:ne.jsx(g_,{phase:r,lines:b,reduced:i})}),ne.jsxs("div",{className:`starmap-div-card${m?" open":""}`,"data-testid":"divination-card",role:"dialog","aria-label":"占卜",children:[ne.jsxs("div",{className:"div-card-head",children:[ne.jsx(m_,{lines:b,size:44,animated:r==="casting"}),ne.jsx("div",{className:"div-card-title",children:r==="casting"||r==="gather"?ne.jsx("span",{className:"div-casting-label",children:"摇卦…"}):r==="error"?ne.jsx("span",{className:"div-error-label",children:"占问未果"}):ne.jsxs(ne.Fragment,{children:[ne.jsx("span",{className:"div-hx-name",children:v==null?void 0:v.name}),(u==null?void 0:u.source)==="rule"&&ne.jsx("span",{className:"div-offline-note",children:"离线卦"})]})}),ne.jsx("button",{type:"button",className:"div-close",onClick:t,"aria-label":"收起卦辞 (Esc)","data-testid":"divination-close",children:"×"})]}),r==="error"?ne.jsx("p",{className:"div-error",role:"alert",children:h}):u&&ne.jsxs(ne.Fragment,{children:[ne.jsx("p",{className:"div-judgment","data-testid":"divination-judgment",children:v==null?void 0:v.judgment}),ne.jsx("p",{className:"div-reading","data-testid":"divination-reading",children:u.reading})]}),ne.jsxs("div",{className:"div-chips",role:"tablist",children:[ne.jsx("button",{type:"button",role:"tab","aria-selected":a==="play",className:`div-chip${a==="play"?" active":""}`,"data-testid":"divination-mode-play",onClick:()=>{o("play"),_("play","")},children:"戏占"}),ne.jsx("button",{type:"button",role:"tab","aria-selected":a==="serious",className:`div-chip${a==="serious"?" active":""}`,"data-testid":"divination-mode-serious",onClick:()=>o("serious"),children:"正占"})]}),a==="serious"&&ne.jsxs("div",{className:"div-question",children:[ne.jsx("textarea",{value:l,onChange:S=>c(S.target.value),rows:2,placeholder:"所问何事?(接真实差距分析)","data-testid":"divination-question"}),ne.jsx("button",{type:"button",className:"div-cast-btn",disabled:!l.trim(),"data-testid":"divination-cast",onClick:()=>_("serious",l.trim()),children:"起卦"})]})]})]})}function v_(n){const e=`${n.id} ${n.title}`.toLowerCase();return/exercise|锻炼|健身/.test(e)?"炼":/learning|学习/.test(e)?"学":/康复|复健|recovery/.test(e)?"复":/read|读书|阅读/.test(e)?"读":/run|跑步/.test(e)?"跑":/meditat|冥想|静坐/.test(e)?"坐":/sleep|睡眠|作息/.test(e)?"息":Array.from(n.title||n.id)[0]??"课"}function td(n,e){const t=(n.recent_days??[]).find(r=>r.date===e),i=((t==null?void 0:t.checkin_ids)??[]).filter(r=>r.length>0);return i.length>0?i[i.length-1]:""}function x_({habit:n,streak:e,done:t}){return ne.jsxs("div",{style:{maxWidth:240},children:[ne.jsx("div",{style:{fontSize:14,marginBottom:6},children:n.title||n.id}),ne.jsx("div",{style:{display:"flex",gap:5,alignItems:"center",marginBottom:6},children:(n.week??[]).map(i=>ne.jsx("span",{title:i.date,style:{display:"inline-block",width:9,height:9,borderRadius:"50%",background:i.done?"#dcae55":"transparent",border:`1px solid ${i.done?"#dcae55":"rgba(232, 226, 210, 0.55)"}`,opacity:i.future?.4:1}},i.date))}),ne.jsxs("div",{style:{fontSize:12,opacity:.8},children:["连续 ",e," 天"]}),ne.jsx("div",{style:{fontSize:11,opacity:.6,marginTop:6},children:t?"右键/长按 = 销印(撤销今日最近一次打卡)":"点击印面 = 今日打卡"})]})}function y_({profile:n}){var S,E;const e=t_(n),t=n_(n),i=i_(n),r=((S=e.data)==null?void 0:S.board.habits)??[],s=((E=e.data)==null?void 0:E.board.today)??"",[a,o]=Ze.useState(null),[l,c]=Ze.useState(null),[u,f]=Ze.useState(null),h=Ze.useRef(null),d=Ze.useRef(!1),m=Ze.useRef(typeof matchMedia<"u"&&matchMedia("(pointer: coarse)").matches),g=r.find(M=>M.id===u)??null;if(Ze.useEffect(()=>{if(!u)return;const M=T=>{T.key==="Escape"&&f(null)};return window.addEventListener("keydown",M),()=>window.removeEventListener("keydown",M)},[u]),r.length===0)return null;const p=M=>(M.week??[]).some(T=>T.done&&!T.future&&T.date===s),_=M=>{if(p(M)){if(!td(M,s)){pa.show({color:"yellow",title:"销印",message:`${M.title||M.id} 今日打卡记录缺少 id,暂不可销印(可在项目页日课栏热力图核实)。`});return}c(null),f(M.id)}},v=()=>{if(!g)return;const M=g,T=td(M,s);if(!T){f(null);return}i.mutate({checkinId:T},{onSuccess:()=>{pa.show({color:"green",title:"已销印",message:`${M.title||M.id} 今日最近一次打卡已删除。`})},onError:x=>{pa.show({color:"red",title:"销印失败",message:x instanceof Error?x.message:String(x)})},onSettled:()=>f(null)})},b=M=>{t.mutate({habit:M.id,date:"",summary:"",note:""},{onSuccess:()=>{pa.show({color:"green",title:"已打卡",message:`${M.title||M.id} 今日打卡成功。`})},onError:T=>{pa.show({color:"red",title:"打卡失败",message:T instanceof Error?T.message:String(T)})}})};return ne.jsxs("div",{className:"starmap-habit-seal","data-starmap-ui":!0,"data-testid":"habit-seal",children:[g&&ne.jsxs("div",{className:"starmap-habit-unseal",role:"alertdialog","aria-label":"销印确认","data-testid":`seal-unseal-${g.id}`,children:[ne.jsxs("span",{className:"starmap-habit-unseal-text",children:["销印「",g.title||g.id,"」今日最近一次打卡?"]}),ne.jsx("button",{type:"button",className:"starmap-habit-unseal-btn danger",disabled:i.isPending,onClick:v,"data-testid":`seal-unseal-yes-${g.id}`,children:"销印"}),ne.jsx("button",{type:"button",className:"starmap-habit-unseal-btn",onClick:()=>f(null),"data-testid":`seal-unseal-no-${g.id}`,children:"取消"})]}),ne.jsxs("span",{className:"starmap-habit-seal-caption","aria-hidden":"true",children:[ne.jsx("span",{children:"日"}),ne.jsx("span",{children:"课"})]}),r.map(M=>{const T=p(M),x=M.id;return ne.jsx(r_,{label:ne.jsx(x_,{habit:M,streak:M.streak??0,done:T}),withArrow:!0,position:"top",disabled:g!==null,opened:m.current?l===x:void 0,events:{hover:!m.current,focus:!0,touch:!1},children:ne.jsx("button",{type:"button",className:`starmap-habit-stamp${a===x?" stamping":""}`,"data-testid":`habit-seal-${x}`,"data-done":T?"true":"false",disabled:t.isPending||i.isPending,"aria-label":`日课打卡 ${M.title||M.id}`,"aria-pressed":T,onClick:()=>{if(d.current){d.current=!1;return}o(x),window.setTimeout(()=>o(null),380),b(M)},onContextMenu:y=>{y.preventDefault(),_(M)},onPointerDown:()=>{m.current&&(h.current=setTimeout(()=>{d.current=!0,p(M)?_(M):c(x)},550))},onPointerUp:()=>{h.current&&clearTimeout(h.current)},onPointerLeave:()=>{h.current&&clearTimeout(h.current),l===x&&c(null)},children:v_(M)})},x)})]})}const b_=[{value:"active",label:"进行中"},{value:"paused",label:"暂停"},{value:"completed",label:"已镌刻"}];function M_({selection:n,snapshot:e,profile:t,onSaved:i}){const r=n.kind==="north"||n.kind==="goal",[s,a]=Ze.useState(n.kind==="north"&&!e.north.is_set),[o,l]=Ze.useState(!1),c=s_(t),u=a_(t),f=n.kind==="goal"?e.goals.find(N=>N.id===n.id):void 0,[h,d]=Ze.useState(e.north.full),[m,g]=Ze.useState(e.north.brief),[p,_]=Ze.useState(e.north.visibility==="public"?"public":"private"),[v,b]=Ze.useState((f==null?void 0:f.title)??""),[S,E]=Ze.useState((f==null?void 0:f.summary)??""),[M,T]=Ze.useState((f==null?void 0:f.start)??""),[x,y]=Ze.useState((f==null?void 0:f.target)??""),[w,C]=Ze.useState((f==null?void 0:f.status)??"active");Ze.useEffect(()=>{d(e.north.full),g(e.north.brief),_(e.north.visibility==="public"?"public":"private")},[e.north.full,e.north.brief,e.north.visibility]),Ze.useEffect(()=>{b((f==null?void 0:f.title)??""),E((f==null?void 0:f.summary)??""),T((f==null?void 0:f.start)??""),y((f==null?void 0:f.target)??""),C((f==null?void 0:f.status)??"active")},[f==null?void 0:f.id,f==null?void 0:f.title,f==null?void 0:f.summary,f==null?void 0:f.start,f==null?void 0:f.target,f==null?void 0:f.status]);const R=c.isPending||u.isPending,L=c.error??u.error,U=N=>{l(!0),window.setTimeout(()=>{l(!1),a(!1),i(N)},950)},I=()=>{c.mutate({full:h.trim(),brief:m.trim(),visibility:p},{onSuccess:N=>{const Y=N.north_star;U({...n,title:"北极星",rows:[["类型","北极星"],["铭文",(Y==null?void 0:Y.full)||"—"],["简称",(Y==null?void 0:Y.brief)||"—"],["可见性",(Y==null?void 0:Y.visibility)==="public"?"可公开":"仅本地"]]})}})},F=()=>{f&&u.mutate({goalId:f.id,body:{title:v.trim(),summary:S.trim(),start:M,target:x,status:w}},{onSuccess:N=>{const Y=N.goal;U({...n,title:Y.title||f.title,rows:[["状态",l_(Y.status??"active")],["起始",Y.start||"—"],["目标",Y.target||"—"],["铭文",Y.summary||"—"]]})}})};return ne.jsxs(ne.Fragment,{children:[o&&ne.jsx("div",{className:"starmap-seal","aria-hidden":"true","data-testid":"starmap-seal",children:"印"}),!s&&ne.jsxs(ne.Fragment,{children:[ne.jsx("h3",{children:n.title}),ne.jsx("dl",{children:n.rows.map(([N,Y])=>ne.jsxs("div",{children:[ne.jsx("dt",{children:N}),ne.jsx("dd",{children:Y})]},N))}),ne.jsxs("div",{className:"starmap-detail-actions",children:[r&&ne.jsx("button",{type:"button",className:"starmap-recarve","data-testid":"starmap-recarve",onClick:()=>a(!0),children:"重刻"}),ne.jsx(S_,{kind:n.kind,profile:t})]})]}),s&&n.kind==="north"&&ne.jsxs("div",{className:"starmap-edit","data-testid":"starmap-edit-north",children:[ne.jsx("h3",{children:"重刻 · 北极星铭文"}),ne.jsxs("label",{children:[ne.jsx("span",{children:"全文"}),ne.jsx("textarea",{value:h,onChange:N=>d(N.target.value),rows:4,placeholder:"写下你的北极星…","data-testid":"edit-north-full"})]}),ne.jsxs("label",{children:[ne.jsx("span",{children:"简称(图面与列表展示)"}),ne.jsx("input",{value:m,onChange:N=>g(N.target.value),placeholder:"一句话简称","data-testid":"edit-north-brief"})]}),ne.jsxs("div",{className:"starmap-edit-field",children:[ne.jsx("span",{children:"可见性"}),ne.jsxs("div",{className:"starmap-vis-toggle",role:"group","aria-label":"可见性",children:[ne.jsx("button",{type:"button",className:p==="public"?"on":"",onClick:()=>_("public"),"data-testid":"edit-north-public",children:"可公开"}),ne.jsx("button",{type:"button",className:p==="private"?"on":"",onClick:()=>_("private"),"data-testid":"edit-north-private",children:"仅本地"})]}),ne.jsx("p",{className:"starmap-edit-hint",children:"助手始终可见全文;此开关只影响公开产物。"})]}),ne.jsx(nd,{saving:R,error:L,saveDisabled:!h.trim()&&!m.trim(),onSave:I,onCancel:()=>a(!1)})]}),s&&n.kind==="goal"&&f&&ne.jsxs("div",{className:"starmap-edit","data-testid":"starmap-edit-goal",children:[ne.jsx("h3",{children:"重刻 · 恒星铭文"}),ne.jsxs("label",{children:[ne.jsx("span",{children:"标题"}),ne.jsx("input",{value:v,onChange:N=>b(N.target.value),"data-testid":"edit-goal-title"})]}),ne.jsxs("label",{children:[ne.jsx("span",{children:"摘要"}),ne.jsx("textarea",{value:S,onChange:N=>E(N.target.value),rows:3,"data-testid":"edit-goal-summary"})]}),ne.jsxs("label",{children:[ne.jsx("span",{children:"起始日期"}),ne.jsx("input",{type:"date",value:M,onChange:N=>T(N.target.value),"data-testid":"edit-goal-start"})]}),ne.jsxs("label",{children:[ne.jsx("span",{children:"目标日期"}),ne.jsx("input",{type:"date",value:x,onChange:N=>y(N.target.value),"data-testid":"edit-goal-target"})]}),ne.jsxs("label",{children:[ne.jsx("span",{children:"状态"}),ne.jsx("select",{value:w,onChange:N=>C(N.target.value),"data-testid":"edit-goal-status",children:b_.map(N=>ne.jsx("option",{value:N.value,children:N.label},N.value))})]}),ne.jsx(nd,{saving:R,error:L,saveDisabled:!v.trim(),onSave:F,onCancel:()=>a(!1)})]})]})}function nd({saving:n,error:e,saveDisabled:t,onSave:i,onCancel:r}){return ne.jsxs(ne.Fragment,{children:[e&&ne.jsx("p",{className:"starmap-edit-error",role:"alert",children:e.message}),ne.jsxs("div",{className:"starmap-edit-actions",children:[ne.jsx("button",{type:"button",className:"starmap-save",disabled:n||t,onClick:i,"data-testid":"starmap-save",children:n?"落印中…":"落印"}),ne.jsx("button",{type:"button",className:"starmap-cancel",disabled:n,onClick:r,children:"收起刻刀"})]})]})}function S_({kind:n,profile:e}){const t=`/p/${encodeURIComponent(e)}`,i=n==="goal"?{to:`${t}/projects`,label:"前往项目泳道 →"}:n==="planet"?{to:`${t}/projects`,label:"前往项目 →"}:n==="guest"?{to:`${t}/evidence`,label:"前往证据 →"}:n==="skill"?{to:`${t}/skill-tree`,label:"前往技能树 →"}:null;return i?ne.jsx(o_,{className:"starmap-detail-link",to:i.to,children:i.label}):null}const Sm=[{key:"active",title:"进行中",match:n=>n.status==="active"},{key:"paused",title:"暂停",match:n=>n.status==="paused"},{key:"carved",title:"已镌刻",match:n=>n.status==="completed"}];function T_(n){const e=[{id:"north"}];for(const t of Sm)for(const i of n.goals.filter(t.match))e.push({id:i.id,goal:i});return e}function E_(n,e,t){return n<=0?-1:(((e<0?0:e)+t)%n+n)%n}const id="nblane-starmap-catalog-hint-seen";function w_({open:n,snapshot:e,profile:t,selection:i,onFocus:r}){const[s,a]=Ze.useState(!1),[o,l]=Ze.useState(""),[c,u]=Ze.useState("north"),[f,h]=Ze.useState(!1),d=Ze.useRef(null),m=c_(t),g=Ze.useMemo(()=>T_(e),[e]),p=e.north.is_set?e.north.brief||e.north.full||"北极星":"虚位 · 点击立星",_=v=>{u(v),r(v)};return Ze.useEffect(()=>{if(!n||!i)return;const v=i.kind==="north"?"north":i.kind==="goal"?i.id:null;v&&g.some(b=>b.id===v)&&u(v)},[n,i,g]),Ze.useEffect(()=>{var v,b,S;!n||!c||(S=(b=(v=d.current)==null?void 0:v.querySelector(`[data-catalog-id="${CSS.escape(c)}"]`))==null?void 0:b.scrollIntoView)==null||S.call(b,{block:"nearest"})},[n,c]),Ze.useEffect(()=>{if(!n||s)return;const v=b=>{const S=b.target;if(S&&/^(INPUT|TEXTAREA|SELECT)$/.test(S.tagName))return;const E=b.key==="ArrowDown"||b.key==="j"?1:b.key==="ArrowUp"||b.key==="k"?-1:0;if(E!==0){b.preventDefault();const M=g.findIndex(x=>x.id===c),T=g[E_(g.length,M,E)];T&&u(T.id)}else b.key==="Enter"&&(b.preventDefault(),c&&g.some(M=>M.id===c)&&r(c))};return window.addEventListener("keydown",v),()=>window.removeEventListener("keydown",v)},[n,s,g,c,r]),Ze.useEffect(()=>{if(!n)return;try{if(sessionStorage.getItem(id))return;sessionStorage.setItem(id,"1")}catch{}h(!0);const v=window.setTimeout(()=>h(!1),2600);return()=>window.clearTimeout(v)},[n]),ne.jsx("div",{className:`starmap-catalog${n?" open":""}`,ref:d,"data-starmap-ui":!0,"data-testid":"starmap-catalog","aria-hidden":!n,children:n&&ne.jsxs(ne.Fragment,{children:[ne.jsx("h3",{children:"星表"}),f&&ne.jsxs("p",{className:"starmap-catalog-hintbar","data-testid":"catalog-hintbar",children:[ne.jsx("kbd",{children:"↑"}),ne.jsx("kbd",{children:"↓"})," 移动 · ",ne.jsx("kbd",{children:"Enter"})," 开卡 · ",ne.jsx("kbd",{children:"Esc"})," 回纯图"]}),ne.jsxs("div",{className:"starmap-catalog-section","data-testid":"catalog-north",children:[ne.jsx("h4",{children:"北极星"}),ne.jsx(rd,{id:"north",active:c==="north",className:e.north.is_set?"":" vacant",title:p,sub:e.north.visibility==="public"?"可公开":"仅本地",onFocus:_})]}),Sm.map(v=>{const b=e.goals.filter(v.match);return ne.jsxs("div",{className:"starmap-catalog-section","data-testid":`catalog-${v.key}`,children:[ne.jsxs("h4",{children:[v.title,b.length>0&&ne.jsx("span",{className:"sec-count",children:b.length})]}),b.length===0&&v.key==="active"&&ne.jsx("p",{className:"starmap-catalog-empty",children:"恒星虚位 — 自下方新增目标。"}),b.map(S=>ne.jsx(rd,{id:S.id,active:c===S.id,className:S.status==="completed"?" carved":"",title:S.title,sub:S.target||"",onFocus:_},S.id))]},v.key)}),!s&&ne.jsx("button",{type:"button",className:"starmap-catalog-add",onClick:()=>{l(""),a(!0)},"data-testid":"catalog-add-goal",children:"＋ 新增目标"}),s&&ne.jsx(A_,{saving:m.isPending,error:m.error,onCancel:()=>a(!1),onSubmit:v=>m.mutate(v,{onSuccess:b=>{a(!1),l(`「${b.goal.title||b.goal.id}」已入星表`)}})}),o&&ne.jsx("p",{className:"starmap-catalog-note",children:o})]})})}function rd({id:n,active:e,className:t,title:i,sub:r,onFocus:s}){return ne.jsxs("button",{type:"button",className:`starmap-catalog-row${e?" active":""}${t}`,onClick:()=>s(n),"data-catalog-id":n,"data-testid":`catalog-row-${n}`,children:[ne.jsx("span",{className:"row-title",children:i}),ne.jsx("span",{className:"row-sub",children:r}),ne.jsx("kbd",{className:"row-kbd",children:"Enter"})]})}function A_({saving:n,error:e,onSubmit:t,onCancel:i}){const[r,s]=Ze.useState(""),[a,o]=Ze.useState(""),[l,c]=Ze.useState("");return ne.jsxs("div",{className:"starmap-edit starmap-catalog-form","data-testid":"catalog-goal-form",children:[ne.jsxs("label",{children:[ne.jsx("span",{children:"标题"}),ne.jsx("input",{value:r,onChange:u=>s(u.target.value),placeholder:"新恒星之名","data-testid":"create-goal-title"})]}),ne.jsxs("label",{children:[ne.jsx("span",{children:"摘要"}),ne.jsx("textarea",{value:a,onChange:u=>o(u.target.value),rows:2,"data-testid":"create-goal-summary"})]}),ne.jsxs("label",{children:[ne.jsx("span",{children:"目标日期"}),ne.jsx("input",{type:"date",value:l,onChange:u=>c(u.target.value),"data-testid":"create-goal-target"})]}),e&&ne.jsx("p",{className:"starmap-edit-error",role:"alert",children:e.message}),ne.jsxs("div",{className:"starmap-edit-actions",children:[ne.jsx("button",{type:"button",className:"starmap-save",disabled:n||!r.trim(),onClick:()=>t({title:r.trim(),summary:a.trim(),target:l}),"data-testid":"create-goal-save",children:n?"镌刻中…":"落印"}),ne.jsx("button",{type:"button",className:"starmap-cancel",disabled:n,onClick:i,children:"收起刻刀"})]})]})}/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */const Ja="184",Is={ROTATE:0,DOLLY:1,PAN:2},Ps={ROTATE:0,PAN:1,DOLLY_PAN:2,DOLLY_ROTATE:3},R_=0,sd=1,C_=2,Ko=1,P_=2,Ra=3,ji=0,on=1,An=2,Sn=0,Vr=1,ll=2,ad=3,od=4,D_=5,kr=100,U_=101,L_=102,I_=103,F_=104,N_=200,O_=201,B_=202,k_=203,Cu=204,Pu=205,z_=206,G_=207,H_=208,V_=209,W_=210,X_=211,j_=212,Y_=213,q_=214,Du=0,cl=1,Uu=2,zs=3,Lu=4,Iu=5,Fu=6,Nu=7,Tm=0,K_=1,Z_=2,Di=0,Em=1,wm=2,Am=3,Rm=4,Cm=5,Pm=6,Dm=7,Um=300,$r=301,Gs=302,lc=303,cc=304,Il=306,Ou=1e3,Vi=1001,Bu=1002,hn=1003,$_=1004,uo=1005,Gt=1006,uc=1007,Gr=1008,Yt=1009,Lm=1010,Im=1011,Ha=1012,Kh=1013,Ui=1014,fi=1015,Yi=1016,Zh=1017,$h=1018,Hs=1020,Fm=35902,Nm=35899,Om=1021,Bm=1022,di=1023,qi=1026,dr=1027,km=1028,Jh=1029,Jr=1030,Qh=1031,ef=1033,Zo=33776,$o=33777,Jo=33778,Qo=33779,ku=35840,zu=35841,Gu=35842,Hu=35843,Vu=36196,Wu=37492,Xu=37496,ju=37488,Yu=37489,ul=37490,qu=37491,Ku=37808,Zu=37809,$u=37810,Ju=37811,Qu=37812,eh=37813,th=37814,nh=37815,ih=37816,rh=37817,sh=37818,ah=37819,oh=37820,lh=37821,ch=36492,uh=36494,hh=36495,fh=36283,dh=36284,hl=36285,ph=36286,Qa=3200,J_=3201,ld=0,Q_=1,Ti="",Tt="srgb",Vs="srgb-linear",fl="linear",bt="srgb",cs=7680,cd=519,ev=512,tv=513,nv=514,tf=515,iv=516,rv=517,nf=518,sv=519,mh=35044,ud="300 es",Ri=2e3,dl=2001;function av(n){for(let e=n.length-1;e>=0;--e)if(n[e]>=65535)return!0;return!1}function pl(n){return document.createElementNS("http://www.w3.org/1999/xhtml",n)}function ov(){const n=pl("canvas");return n.style.display="block",n}const hd={};function ml(...n){const e="THREE."+n.shift();console.log(e,...n)}function zm(n){const e=n[0];if(typeof e=="string"&&e.startsWith("TSL:")){const t=n[1];t&&t.isStackTrace?n[0]+=" "+t.getLocation():n[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return n}function Qe(...n){n=zm(n);const e="THREE."+n.shift();{const t=n[0];t&&t.isStackTrace?console.warn(t.getError(e)):console.warn(e,...n)}}function pt(...n){n=zm(n);const e="THREE."+n.shift();{const t=n[0];t&&t.isStackTrace?console.error(t.getError(e)):console.error(e,...n)}}function gh(...n){const e=n.join(" ");e in hd||(hd[e]=!0,Qe(...n))}function lv(n,e,t){return new Promise(function(i,r){function s(){switch(n.clientWaitSync(e,n.SYNC_FLUSH_COMMANDS_BIT,0)){case n.WAIT_FAILED:r();break;case n.TIMEOUT_EXPIRED:setTimeout(s,t);break;default:i()}}setTimeout(s,t)})}const cv={[Du]:cl,[Uu]:Fu,[Lu]:Nu,[zs]:Iu,[cl]:Du,[Fu]:Uu,[Nu]:Lu,[Iu]:zs};class mi{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});const i=this._listeners;i[e]===void 0&&(i[e]=[]),i[e].indexOf(t)===-1&&i[e].push(t)}hasEventListener(e,t){const i=this._listeners;return i===void 0?!1:i[e]!==void 0&&i[e].indexOf(t)!==-1}removeEventListener(e,t){const i=this._listeners;if(i===void 0)return;const r=i[e];if(r!==void 0){const s=r.indexOf(t);s!==-1&&r.splice(s,1)}}dispatchEvent(e){const t=this._listeners;if(t===void 0)return;const i=t[e.type];if(i!==void 0){e.target=this;const r=i.slice(0);for(let s=0,a=r.length;s<a;s++)r[s].call(this,e);e.target=null}}}const pn=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],el=Math.PI/180,_h=180/Math.PI;function vr(){const n=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,i=Math.random()*4294967295|0;return(pn[n&255]+pn[n>>8&255]+pn[n>>16&255]+pn[n>>24&255]+"-"+pn[e&255]+pn[e>>8&255]+"-"+pn[e>>16&15|64]+pn[e>>24&255]+"-"+pn[t&63|128]+pn[t>>8&255]+"-"+pn[t>>16&255]+pn[t>>24&255]+pn[i&255]+pn[i>>8&255]+pn[i>>16&255]+pn[i>>24&255]).toLowerCase()}function lt(n,e,t){return Math.max(e,Math.min(t,n))}function uv(n,e){return(n%e+e)%e}function hc(n,e,t){return(1-t)*n+t*e}function Ei(n,e){switch(e.constructor){case Float32Array:return n;case Uint32Array:return n/4294967295;case Uint16Array:return n/65535;case Uint8Array:return n/255;case Int32Array:return Math.max(n/2147483647,-1);case Int16Array:return Math.max(n/32767,-1);case Int8Array:return Math.max(n/127,-1);default:throw new Error("Invalid component type.")}}function Mt(n,e){switch(e.constructor){case Float32Array:return n;case Uint32Array:return Math.round(n*4294967295);case Uint16Array:return Math.round(n*65535);case Uint8Array:return Math.round(n*255);case Int32Array:return Math.round(n*2147483647);case Int16Array:return Math.round(n*32767);case Int8Array:return Math.round(n*127);default:throw new Error("Invalid component type.")}}const hv={DEG2RAD:el},Bf=class Bf{constructor(e=0,t=0){this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const t=this.x,i=this.y,r=e.elements;return this.x=r[0]*t+r[3]*i+r[6],this.y=r[1]*t+r[4]*i+r[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=lt(this.x,e.x,t.x),this.y=lt(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=lt(this.x,e,t),this.y=lt(this.y,e,t),this}clampLength(e,t){const i=this.length();return this.divideScalar(i||1).multiplyScalar(lt(i,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const i=this.dot(e)/t;return Math.acos(lt(i,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,i=this.y-e.y;return t*t+i*i}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,i){return this.x=e.x+(t.x-e.x)*i,this.y=e.y+(t.y-e.y)*i,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){const i=Math.cos(t),r=Math.sin(t),s=this.x-e.x,a=this.y-e.y;return this.x=s*i-a*r+e.x,this.y=s*r+a*i+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};Bf.prototype.isVector2=!0;let Xe=Bf;class Mr{constructor(e=0,t=0,i=0,r=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=i,this._w=r}static slerpFlat(e,t,i,r,s,a,o){let l=i[r+0],c=i[r+1],u=i[r+2],f=i[r+3],h=s[a+0],d=s[a+1],m=s[a+2],g=s[a+3];if(f!==g||l!==h||c!==d||u!==m){let p=l*h+c*d+u*m+f*g;p<0&&(h=-h,d=-d,m=-m,g=-g,p=-p);let _=1-o;if(p<.9995){const v=Math.acos(p),b=Math.sin(v);_=Math.sin(_*v)/b,o=Math.sin(o*v)/b,l=l*_+h*o,c=c*_+d*o,u=u*_+m*o,f=f*_+g*o}else{l=l*_+h*o,c=c*_+d*o,u=u*_+m*o,f=f*_+g*o;const v=1/Math.sqrt(l*l+c*c+u*u+f*f);l*=v,c*=v,u*=v,f*=v}}e[t]=l,e[t+1]=c,e[t+2]=u,e[t+3]=f}static multiplyQuaternionsFlat(e,t,i,r,s,a){const o=i[r],l=i[r+1],c=i[r+2],u=i[r+3],f=s[a],h=s[a+1],d=s[a+2],m=s[a+3];return e[t]=o*m+u*f+l*d-c*h,e[t+1]=l*m+u*h+c*f-o*d,e[t+2]=c*m+u*d+o*h-l*f,e[t+3]=u*m-o*f-l*h-c*d,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,i,r){return this._x=e,this._y=t,this._z=i,this._w=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){const i=e._x,r=e._y,s=e._z,a=e._order,o=Math.cos,l=Math.sin,c=o(i/2),u=o(r/2),f=o(s/2),h=l(i/2),d=l(r/2),m=l(s/2);switch(a){case"XYZ":this._x=h*u*f+c*d*m,this._y=c*d*f-h*u*m,this._z=c*u*m+h*d*f,this._w=c*u*f-h*d*m;break;case"YXZ":this._x=h*u*f+c*d*m,this._y=c*d*f-h*u*m,this._z=c*u*m-h*d*f,this._w=c*u*f+h*d*m;break;case"ZXY":this._x=h*u*f-c*d*m,this._y=c*d*f+h*u*m,this._z=c*u*m+h*d*f,this._w=c*u*f-h*d*m;break;case"ZYX":this._x=h*u*f-c*d*m,this._y=c*d*f+h*u*m,this._z=c*u*m-h*d*f,this._w=c*u*f+h*d*m;break;case"YZX":this._x=h*u*f+c*d*m,this._y=c*d*f+h*u*m,this._z=c*u*m-h*d*f,this._w=c*u*f-h*d*m;break;case"XZY":this._x=h*u*f-c*d*m,this._y=c*d*f-h*u*m,this._z=c*u*m+h*d*f,this._w=c*u*f+h*d*m;break;default:Qe("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){const i=t/2,r=Math.sin(i);return this._x=e.x*r,this._y=e.y*r,this._z=e.z*r,this._w=Math.cos(i),this._onChangeCallback(),this}setFromRotationMatrix(e){const t=e.elements,i=t[0],r=t[4],s=t[8],a=t[1],o=t[5],l=t[9],c=t[2],u=t[6],f=t[10],h=i+o+f;if(h>0){const d=.5/Math.sqrt(h+1);this._w=.25/d,this._x=(u-l)*d,this._y=(s-c)*d,this._z=(a-r)*d}else if(i>o&&i>f){const d=2*Math.sqrt(1+i-o-f);this._w=(u-l)/d,this._x=.25*d,this._y=(r+a)/d,this._z=(s+c)/d}else if(o>f){const d=2*Math.sqrt(1+o-i-f);this._w=(s-c)/d,this._x=(r+a)/d,this._y=.25*d,this._z=(l+u)/d}else{const d=2*Math.sqrt(1+f-i-o);this._w=(a-r)/d,this._x=(s+c)/d,this._y=(l+u)/d,this._z=.25*d}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let i=e.dot(t)+1;return i<1e-8?(i=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=i):(this._x=0,this._y=-e.z,this._z=e.y,this._w=i)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=i),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(lt(this.dot(e),-1,1)))}rotateTowards(e,t){const i=this.angleTo(e);if(i===0)return this;const r=Math.min(1,t/i);return this.slerp(e,r),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){const i=e._x,r=e._y,s=e._z,a=e._w,o=t._x,l=t._y,c=t._z,u=t._w;return this._x=i*u+a*o+r*c-s*l,this._y=r*u+a*l+s*o-i*c,this._z=s*u+a*c+i*l-r*o,this._w=a*u-i*o-r*l-s*c,this._onChangeCallback(),this}slerp(e,t){let i=e._x,r=e._y,s=e._z,a=e._w,o=this.dot(e);o<0&&(i=-i,r=-r,s=-s,a=-a,o=-o);let l=1-t;if(o<.9995){const c=Math.acos(o),u=Math.sin(c);l=Math.sin(l*c)/u,t=Math.sin(t*c)/u,this._x=this._x*l+i*t,this._y=this._y*l+r*t,this._z=this._z*l+s*t,this._w=this._w*l+a*t,this._onChangeCallback()}else this._x=this._x*l+i*t,this._y=this._y*l+r*t,this._z=this._z*l+s*t,this._w=this._w*l+a*t,this.normalize();return this}slerpQuaternions(e,t,i){return this.copy(e).slerp(t,i)}random(){const e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),i=Math.random(),r=Math.sqrt(1-i),s=Math.sqrt(i);return this.set(r*Math.sin(e),r*Math.cos(e),s*Math.sin(t),s*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}const kf=class kf{constructor(e=0,t=0,i=0){this.x=e,this.y=t,this.z=i}set(e,t,i){return i===void 0&&(i=this.z),this.x=e,this.y=t,this.z=i,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(fd.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(fd.setFromAxisAngle(e,t))}applyMatrix3(e){const t=this.x,i=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[3]*i+s[6]*r,this.y=s[1]*t+s[4]*i+s[7]*r,this.z=s[2]*t+s[5]*i+s[8]*r,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const t=this.x,i=this.y,r=this.z,s=e.elements,a=1/(s[3]*t+s[7]*i+s[11]*r+s[15]);return this.x=(s[0]*t+s[4]*i+s[8]*r+s[12])*a,this.y=(s[1]*t+s[5]*i+s[9]*r+s[13])*a,this.z=(s[2]*t+s[6]*i+s[10]*r+s[14])*a,this}applyQuaternion(e){const t=this.x,i=this.y,r=this.z,s=e.x,a=e.y,o=e.z,l=e.w,c=2*(a*r-o*i),u=2*(o*t-s*r),f=2*(s*i-a*t);return this.x=t+l*c+a*f-o*u,this.y=i+l*u+o*c-s*f,this.z=r+l*f+s*u-a*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const t=this.x,i=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[4]*i+s[8]*r,this.y=s[1]*t+s[5]*i+s[9]*r,this.z=s[2]*t+s[6]*i+s[10]*r,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=lt(this.x,e.x,t.x),this.y=lt(this.y,e.y,t.y),this.z=lt(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=lt(this.x,e,t),this.y=lt(this.y,e,t),this.z=lt(this.z,e,t),this}clampLength(e,t){const i=this.length();return this.divideScalar(i||1).multiplyScalar(lt(i,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,i){return this.x=e.x+(t.x-e.x)*i,this.y=e.y+(t.y-e.y)*i,this.z=e.z+(t.z-e.z)*i,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){const i=e.x,r=e.y,s=e.z,a=t.x,o=t.y,l=t.z;return this.x=r*l-s*o,this.y=s*a-i*l,this.z=i*o-r*a,this}projectOnVector(e){const t=e.lengthSq();if(t===0)return this.set(0,0,0);const i=e.dot(this)/t;return this.copy(e).multiplyScalar(i)}projectOnPlane(e){return fc.copy(this).projectOnVector(e),this.sub(fc)}reflect(e){return this.sub(fc.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const i=this.dot(e)/t;return Math.acos(lt(i,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,i=this.y-e.y,r=this.z-e.z;return t*t+i*i+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,i){const r=Math.sin(t)*e;return this.x=r*Math.sin(i),this.y=Math.cos(t)*e,this.z=r*Math.cos(i),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,i){return this.x=e*Math.sin(t),this.y=i,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){const t=this.setFromMatrixColumn(e,0).length(),i=this.setFromMatrixColumn(e,1).length(),r=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=i,this.z=r,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,t=Math.random()*2-1,i=Math.sqrt(1-t*t);return this.x=i*Math.cos(e),this.y=t,this.z=i*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};kf.prototype.isVector3=!0;let $=kf;const fc=new $,fd=new Mr,zf=class zf{constructor(e,t,i,r,s,a,o,l,c){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,i,r,s,a,o,l,c)}set(e,t,i,r,s,a,o,l,c){const u=this.elements;return u[0]=e,u[1]=r,u[2]=o,u[3]=t,u[4]=s,u[5]=l,u[6]=i,u[7]=a,u[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const t=this.elements,i=e.elements;return t[0]=i[0],t[1]=i[1],t[2]=i[2],t[3]=i[3],t[4]=i[4],t[5]=i[5],t[6]=i[6],t[7]=i[7],t[8]=i[8],this}extractBasis(e,t,i){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),i.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const i=e.elements,r=t.elements,s=this.elements,a=i[0],o=i[3],l=i[6],c=i[1],u=i[4],f=i[7],h=i[2],d=i[5],m=i[8],g=r[0],p=r[3],_=r[6],v=r[1],b=r[4],S=r[7],E=r[2],M=r[5],T=r[8];return s[0]=a*g+o*v+l*E,s[3]=a*p+o*b+l*M,s[6]=a*_+o*S+l*T,s[1]=c*g+u*v+f*E,s[4]=c*p+u*b+f*M,s[7]=c*_+u*S+f*T,s[2]=h*g+d*v+m*E,s[5]=h*p+d*b+m*M,s[8]=h*_+d*S+m*T,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){const e=this.elements,t=e[0],i=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8];return t*a*u-t*o*c-i*s*u+i*o*l+r*s*c-r*a*l}invert(){const e=this.elements,t=e[0],i=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8],f=u*a-o*c,h=o*l-u*s,d=c*s-a*l,m=t*f+i*h+r*d;if(m===0)return this.set(0,0,0,0,0,0,0,0,0);const g=1/m;return e[0]=f*g,e[1]=(r*c-u*i)*g,e[2]=(o*i-r*a)*g,e[3]=h*g,e[4]=(u*t-r*l)*g,e[5]=(r*s-o*t)*g,e[6]=d*g,e[7]=(i*l-c*t)*g,e[8]=(a*t-i*s)*g,this}transpose(){let e;const t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,i,r,s,a,o){const l=Math.cos(s),c=Math.sin(s);return this.set(i*l,i*c,-i*(l*a+c*o)+a+e,-r*c,r*l,-r*(-c*a+l*o)+o+t,0,0,1),this}scale(e,t){return this.premultiply(dc.makeScale(e,t)),this}rotate(e){return this.premultiply(dc.makeRotation(-e)),this}translate(e,t){return this.premultiply(dc.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){const t=Math.cos(e),i=Math.sin(e);return this.set(t,-i,0,i,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){const t=this.elements,i=e.elements;for(let r=0;r<9;r++)if(t[r]!==i[r])return!1;return!0}fromArray(e,t=0){for(let i=0;i<9;i++)this.elements[i]=e[i+t];return this}toArray(e=[],t=0){const i=this.elements;return e[t]=i[0],e[t+1]=i[1],e[t+2]=i[2],e[t+3]=i[3],e[t+4]=i[4],e[t+5]=i[5],e[t+6]=i[6],e[t+7]=i[7],e[t+8]=i[8],e}clone(){return new this.constructor().fromArray(this.elements)}};zf.prototype.isMatrix3=!0;let rt=zf;const dc=new rt,dd=new rt().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),pd=new rt().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function fv(){const n={enabled:!0,workingColorSpace:Vs,spaces:{},convert:function(r,s,a){return this.enabled===!1||s===a||!s||!a||(this.spaces[s].transfer===bt&&(r.r=Wi(r.r),r.g=Wi(r.g),r.b=Wi(r.b)),this.spaces[s].primaries!==this.spaces[a].primaries&&(r.applyMatrix3(this.spaces[s].toXYZ),r.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===bt&&(r.r=Fs(r.r),r.g=Fs(r.g),r.b=Fs(r.b))),r},workingToColorSpace:function(r,s){return this.convert(r,this.workingColorSpace,s)},colorSpaceToWorking:function(r,s){return this.convert(r,s,this.workingColorSpace)},getPrimaries:function(r){return this.spaces[r].primaries},getTransfer:function(r){return r===Ti?fl:this.spaces[r].transfer},getToneMappingMode:function(r){return this.spaces[r].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(r,s=this.workingColorSpace){return r.fromArray(this.spaces[s].luminanceCoefficients)},define:function(r){Object.assign(this.spaces,r)},_getMatrix:function(r,s,a){return r.copy(this.spaces[s].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(r){return this.spaces[r].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(r=this.workingColorSpace){return this.spaces[r].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(r,s){return gh("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),n.workingToColorSpace(r,s)},toWorkingColorSpace:function(r,s){return gh("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),n.colorSpaceToWorking(r,s)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],i=[.3127,.329];return n.define({[Vs]:{primaries:e,whitePoint:i,transfer:fl,toXYZ:dd,fromXYZ:pd,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:Tt},outputColorSpaceConfig:{drawingBufferColorSpace:Tt}},[Tt]:{primaries:e,whitePoint:i,transfer:bt,toXYZ:dd,fromXYZ:pd,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:Tt}}}),n}const ft=fv();function Wi(n){return n<.04045?n*.0773993808:Math.pow(n*.9478672986+.0521327014,2.4)}function Fs(n){return n<.0031308?n*12.92:1.055*Math.pow(n,.41666)-.055}let us;class dv{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let i;if(e instanceof HTMLCanvasElement)i=e;else{us===void 0&&(us=pl("canvas")),us.width=e.width,us.height=e.height;const r=us.getContext("2d");e instanceof ImageData?r.putImageData(e,0,0):r.drawImage(e,0,0,e.width,e.height),i=us}return i.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const t=pl("canvas");t.width=e.width,t.height=e.height;const i=t.getContext("2d");i.drawImage(e,0,0,e.width,e.height);const r=i.getImageData(0,0,e.width,e.height),s=r.data;for(let a=0;a<s.length;a++)s[a]=Wi(s[a]/255)*255;return i.putImageData(r,0,0),t}else if(e.data){const t=e.data.slice(0);for(let i=0;i<t.length;i++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[i]=Math.floor(Wi(t[i]/255)*255):t[i]=Wi(t[i]);return{data:t,width:e.width,height:e.height}}else return Qe("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let pv=0;class rf{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:pv++}),this.uuid=vr(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){const t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):typeof VideoFrame<"u"&&t instanceof VideoFrame?e.set(t.displayWidth,t.displayHeight,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const i={uuid:this.uuid,url:""},r=this.data;if(r!==null){let s;if(Array.isArray(r)){s=[];for(let a=0,o=r.length;a<o;a++)r[a].isDataTexture?s.push(pc(r[a].image)):s.push(pc(r[a]))}else s=pc(r);i.url=s}return t||(e.images[this.uuid]=i),i}}function pc(n){return typeof HTMLImageElement<"u"&&n instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&n instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&n instanceof ImageBitmap?dv.getDataURL(n):n.data?{data:Array.from(n.data),width:n.width,height:n.height,type:n.data.constructor.name}:(Qe("Texture: Unable to serialize Texture."),{})}let mv=0;const mc=new $;class Jt extends mi{constructor(e=Jt.DEFAULT_IMAGE,t=Jt.DEFAULT_MAPPING,i=Vi,r=Vi,s=Gt,a=Gr,o=di,l=Yt,c=Jt.DEFAULT_ANISOTROPY,u=Ti){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:mv++}),this.uuid=vr(),this.name="",this.source=new rf(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=i,this.wrapT=r,this.magFilter=s,this.minFilter=a,this.anisotropy=c,this.format=o,this.internalFormat=null,this.type=l,this.offset=new Xe(0,0),this.repeat=new Xe(1,1),this.center=new Xe(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new rt,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=u,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(mc).x}get height(){return this.source.getSize(mc).y}get depth(){return this.source.getSize(mc).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(const t in e){const i=e[t];if(i===void 0){Qe(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}const r=this[t];if(r===void 0){Qe(`Texture.setValues(): property '${t}' does not exist.`);continue}r&&i&&r.isVector2&&i.isVector2||r&&i&&r.isVector3&&i.isVector3||r&&i&&r.isMatrix3&&i.isMatrix3?r.copy(i):this[t]=i}}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const i={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(i.userData=this.userData),t||(e.textures[this.uuid]=i),i}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==Um)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Ou:e.x=e.x-Math.floor(e.x);break;case Vi:e.x=e.x<0?0:1;break;case Bu:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Ou:e.y=e.y-Math.floor(e.y);break;case Vi:e.y=e.y<0?0:1;break;case Bu:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}Jt.DEFAULT_IMAGE=null;Jt.DEFAULT_MAPPING=Um;Jt.DEFAULT_ANISOTROPY=1;const Gf=class Gf{constructor(e=0,t=0,i=0,r=1){this.x=e,this.y=t,this.z=i,this.w=r}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,i,r){return this.x=e,this.y=t,this.z=i,this.w=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const t=this.x,i=this.y,r=this.z,s=this.w,a=e.elements;return this.x=a[0]*t+a[4]*i+a[8]*r+a[12]*s,this.y=a[1]*t+a[5]*i+a[9]*r+a[13]*s,this.z=a[2]*t+a[6]*i+a[10]*r+a[14]*s,this.w=a[3]*t+a[7]*i+a[11]*r+a[15]*s,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,i,r,s;const l=e.elements,c=l[0],u=l[4],f=l[8],h=l[1],d=l[5],m=l[9],g=l[2],p=l[6],_=l[10];if(Math.abs(u-h)<.01&&Math.abs(f-g)<.01&&Math.abs(m-p)<.01){if(Math.abs(u+h)<.1&&Math.abs(f+g)<.1&&Math.abs(m+p)<.1&&Math.abs(c+d+_-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;const b=(c+1)/2,S=(d+1)/2,E=(_+1)/2,M=(u+h)/4,T=(f+g)/4,x=(m+p)/4;return b>S&&b>E?b<.01?(i=0,r=.707106781,s=.707106781):(i=Math.sqrt(b),r=M/i,s=T/i):S>E?S<.01?(i=.707106781,r=0,s=.707106781):(r=Math.sqrt(S),i=M/r,s=x/r):E<.01?(i=.707106781,r=.707106781,s=0):(s=Math.sqrt(E),i=T/s,r=x/s),this.set(i,r,s,t),this}let v=Math.sqrt((p-m)*(p-m)+(f-g)*(f-g)+(h-u)*(h-u));return Math.abs(v)<.001&&(v=1),this.x=(p-m)/v,this.y=(f-g)/v,this.z=(h-u)/v,this.w=Math.acos((c+d+_-1)/2),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=lt(this.x,e.x,t.x),this.y=lt(this.y,e.y,t.y),this.z=lt(this.z,e.z,t.z),this.w=lt(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=lt(this.x,e,t),this.y=lt(this.y,e,t),this.z=lt(this.z,e,t),this.w=lt(this.w,e,t),this}clampLength(e,t){const i=this.length();return this.divideScalar(i||1).multiplyScalar(lt(i,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,i){return this.x=e.x+(t.x-e.x)*i,this.y=e.y+(t.y-e.y)*i,this.z=e.z+(t.z-e.z)*i,this.w=e.w+(t.w-e.w)*i,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};Gf.prototype.isVector4=!0;let Ut=Gf;class gv extends mi{constructor(e=1,t=1,i={}){super(),i=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:Gt,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},i),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=i.depth,this.scissor=new Ut(0,0,e,t),this.scissorTest=!1,this.viewport=new Ut(0,0,e,t),this.textures=[];const r={width:e,height:t,depth:i.depth},s=new Jt(r),a=i.count;for(let o=0;o<a;o++)this.textures[o]=s.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(i),this.depthBuffer=i.depthBuffer,this.stencilBuffer=i.stencilBuffer,this.resolveDepthBuffer=i.resolveDepthBuffer,this.resolveStencilBuffer=i.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=i.depthTexture,this.samples=i.samples,this.multiview=i.multiview}_setTextureOptions(e={}){const t={minFilter:Gt,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let i=0;i<this.textures.length;i++)this.textures[i].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,i=1){if(this.width!==e||this.height!==t||this.depth!==i){this.width=e,this.height=t,this.depth=i;for(let r=0,s=this.textures.length;r<s;r++)this.textures[r].image.width=e,this.textures[r].image.height=t,this.textures[r].image.depth=i,this.textures[r].isData3DTexture!==!0&&(this.textures[r].isArrayTexture=this.textures[r].image.depth>1);this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,i=e.textures.length;t<i;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;const r=Object.assign({},e.textures[t].image);this.textures[t].source=new rf(r)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this.multiview=e.multiview,this}dispose(){this.dispatchEvent({type:"dispose"})}}class Qt extends gv{constructor(e=1,t=1,i={}){super(e,t,i),this.isWebGLRenderTarget=!0}}class Gm extends Jt{constructor(e=null,t=1,i=1,r=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:i,depth:r},this.magFilter=hn,this.minFilter=hn,this.wrapR=Vi,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class _v extends Jt{constructor(e=null,t=1,i=1,r=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:i,depth:r},this.magFilter=hn,this.minFilter=hn,this.wrapR=Vi,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}const Ll=class Ll{constructor(e,t,i,r,s,a,o,l,c,u,f,h,d,m,g,p){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,i,r,s,a,o,l,c,u,f,h,d,m,g,p)}set(e,t,i,r,s,a,o,l,c,u,f,h,d,m,g,p){const _=this.elements;return _[0]=e,_[4]=t,_[8]=i,_[12]=r,_[1]=s,_[5]=a,_[9]=o,_[13]=l,_[2]=c,_[6]=u,_[10]=f,_[14]=h,_[3]=d,_[7]=m,_[11]=g,_[15]=p,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new Ll().fromArray(this.elements)}copy(e){const t=this.elements,i=e.elements;return t[0]=i[0],t[1]=i[1],t[2]=i[2],t[3]=i[3],t[4]=i[4],t[5]=i[5],t[6]=i[6],t[7]=i[7],t[8]=i[8],t[9]=i[9],t[10]=i[10],t[11]=i[11],t[12]=i[12],t[13]=i[13],t[14]=i[14],t[15]=i[15],this}copyPosition(e){const t=this.elements,i=e.elements;return t[12]=i[12],t[13]=i[13],t[14]=i[14],this}setFromMatrix3(e){const t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,i){return this.determinant()===0?(e.set(1,0,0),t.set(0,1,0),i.set(0,0,1),this):(e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),i.setFromMatrixColumn(this,2),this)}makeBasis(e,t,i){return this.set(e.x,t.x,i.x,0,e.y,t.y,i.y,0,e.z,t.z,i.z,0,0,0,0,1),this}extractRotation(e){if(e.determinant()===0)return this.identity();const t=this.elements,i=e.elements,r=1/hs.setFromMatrixColumn(e,0).length(),s=1/hs.setFromMatrixColumn(e,1).length(),a=1/hs.setFromMatrixColumn(e,2).length();return t[0]=i[0]*r,t[1]=i[1]*r,t[2]=i[2]*r,t[3]=0,t[4]=i[4]*s,t[5]=i[5]*s,t[6]=i[6]*s,t[7]=0,t[8]=i[8]*a,t[9]=i[9]*a,t[10]=i[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){const t=this.elements,i=e.x,r=e.y,s=e.z,a=Math.cos(i),o=Math.sin(i),l=Math.cos(r),c=Math.sin(r),u=Math.cos(s),f=Math.sin(s);if(e.order==="XYZ"){const h=a*u,d=a*f,m=o*u,g=o*f;t[0]=l*u,t[4]=-l*f,t[8]=c,t[1]=d+m*c,t[5]=h-g*c,t[9]=-o*l,t[2]=g-h*c,t[6]=m+d*c,t[10]=a*l}else if(e.order==="YXZ"){const h=l*u,d=l*f,m=c*u,g=c*f;t[0]=h+g*o,t[4]=m*o-d,t[8]=a*c,t[1]=a*f,t[5]=a*u,t[9]=-o,t[2]=d*o-m,t[6]=g+h*o,t[10]=a*l}else if(e.order==="ZXY"){const h=l*u,d=l*f,m=c*u,g=c*f;t[0]=h-g*o,t[4]=-a*f,t[8]=m+d*o,t[1]=d+m*o,t[5]=a*u,t[9]=g-h*o,t[2]=-a*c,t[6]=o,t[10]=a*l}else if(e.order==="ZYX"){const h=a*u,d=a*f,m=o*u,g=o*f;t[0]=l*u,t[4]=m*c-d,t[8]=h*c+g,t[1]=l*f,t[5]=g*c+h,t[9]=d*c-m,t[2]=-c,t[6]=o*l,t[10]=a*l}else if(e.order==="YZX"){const h=a*l,d=a*c,m=o*l,g=o*c;t[0]=l*u,t[4]=g-h*f,t[8]=m*f+d,t[1]=f,t[5]=a*u,t[9]=-o*u,t[2]=-c*u,t[6]=d*f+m,t[10]=h-g*f}else if(e.order==="XZY"){const h=a*l,d=a*c,m=o*l,g=o*c;t[0]=l*u,t[4]=-f,t[8]=c*u,t[1]=h*f+g,t[5]=a*u,t[9]=d*f-m,t[2]=m*f-d,t[6]=o*u,t[10]=g*f+h}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(vv,e,xv)}lookAt(e,t,i){const r=this.elements;return On.subVectors(e,t),On.lengthSq()===0&&(On.z=1),On.normalize(),nr.crossVectors(i,On),nr.lengthSq()===0&&(Math.abs(i.z)===1?On.x+=1e-4:On.z+=1e-4,On.normalize(),nr.crossVectors(i,On)),nr.normalize(),ho.crossVectors(On,nr),r[0]=nr.x,r[4]=ho.x,r[8]=On.x,r[1]=nr.y,r[5]=ho.y,r[9]=On.y,r[2]=nr.z,r[6]=ho.z,r[10]=On.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const i=e.elements,r=t.elements,s=this.elements,a=i[0],o=i[4],l=i[8],c=i[12],u=i[1],f=i[5],h=i[9],d=i[13],m=i[2],g=i[6],p=i[10],_=i[14],v=i[3],b=i[7],S=i[11],E=i[15],M=r[0],T=r[4],x=r[8],y=r[12],w=r[1],C=r[5],R=r[9],L=r[13],U=r[2],I=r[6],F=r[10],N=r[14],Y=r[3],j=r[7],Z=r[11],O=r[15];return s[0]=a*M+o*w+l*U+c*Y,s[4]=a*T+o*C+l*I+c*j,s[8]=a*x+o*R+l*F+c*Z,s[12]=a*y+o*L+l*N+c*O,s[1]=u*M+f*w+h*U+d*Y,s[5]=u*T+f*C+h*I+d*j,s[9]=u*x+f*R+h*F+d*Z,s[13]=u*y+f*L+h*N+d*O,s[2]=m*M+g*w+p*U+_*Y,s[6]=m*T+g*C+p*I+_*j,s[10]=m*x+g*R+p*F+_*Z,s[14]=m*y+g*L+p*N+_*O,s[3]=v*M+b*w+S*U+E*Y,s[7]=v*T+b*C+S*I+E*j,s[11]=v*x+b*R+S*F+E*Z,s[15]=v*y+b*L+S*N+E*O,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){const e=this.elements,t=e[0],i=e[4],r=e[8],s=e[12],a=e[1],o=e[5],l=e[9],c=e[13],u=e[2],f=e[6],h=e[10],d=e[14],m=e[3],g=e[7],p=e[11],_=e[15],v=l*d-c*h,b=o*d-c*f,S=o*h-l*f,E=a*d-c*u,M=a*h-l*u,T=a*f-o*u;return t*(g*v-p*b+_*S)-i*(m*v-p*E+_*M)+r*(m*b-g*E+_*T)-s*(m*S-g*M+p*T)}transpose(){const e=this.elements;let t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,i){const r=this.elements;return e.isVector3?(r[12]=e.x,r[13]=e.y,r[14]=e.z):(r[12]=e,r[13]=t,r[14]=i),this}invert(){const e=this.elements,t=e[0],i=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8],f=e[9],h=e[10],d=e[11],m=e[12],g=e[13],p=e[14],_=e[15],v=t*o-i*a,b=t*l-r*a,S=t*c-s*a,E=i*l-r*o,M=i*c-s*o,T=r*c-s*l,x=u*g-f*m,y=u*p-h*m,w=u*_-d*m,C=f*p-h*g,R=f*_-d*g,L=h*_-d*p,U=v*L-b*R+S*C+E*w-M*y+T*x;if(U===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const I=1/U;return e[0]=(o*L-l*R+c*C)*I,e[1]=(r*R-i*L-s*C)*I,e[2]=(g*T-p*M+_*E)*I,e[3]=(h*M-f*T-d*E)*I,e[4]=(l*w-a*L-c*y)*I,e[5]=(t*L-r*w+s*y)*I,e[6]=(p*S-m*T-_*b)*I,e[7]=(u*T-h*S+d*b)*I,e[8]=(a*R-o*w+c*x)*I,e[9]=(i*w-t*R-s*x)*I,e[10]=(m*M-g*S+_*v)*I,e[11]=(f*S-u*M-d*v)*I,e[12]=(o*y-a*C-l*x)*I,e[13]=(t*C-i*y+r*x)*I,e[14]=(g*b-m*E-p*v)*I,e[15]=(u*E-f*b+h*v)*I,this}scale(e){const t=this.elements,i=e.x,r=e.y,s=e.z;return t[0]*=i,t[4]*=r,t[8]*=s,t[1]*=i,t[5]*=r,t[9]*=s,t[2]*=i,t[6]*=r,t[10]*=s,t[3]*=i,t[7]*=r,t[11]*=s,this}getMaxScaleOnAxis(){const e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],i=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],r=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,i,r))}makeTranslation(e,t,i){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,i,0,0,0,1),this}makeRotationX(e){const t=Math.cos(e),i=Math.sin(e);return this.set(1,0,0,0,0,t,-i,0,0,i,t,0,0,0,0,1),this}makeRotationY(e){const t=Math.cos(e),i=Math.sin(e);return this.set(t,0,i,0,0,1,0,0,-i,0,t,0,0,0,0,1),this}makeRotationZ(e){const t=Math.cos(e),i=Math.sin(e);return this.set(t,-i,0,0,i,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){const i=Math.cos(t),r=Math.sin(t),s=1-i,a=e.x,o=e.y,l=e.z,c=s*a,u=s*o;return this.set(c*a+i,c*o-r*l,c*l+r*o,0,c*o+r*l,u*o+i,u*l-r*a,0,c*l-r*o,u*l+r*a,s*l*l+i,0,0,0,0,1),this}makeScale(e,t,i){return this.set(e,0,0,0,0,t,0,0,0,0,i,0,0,0,0,1),this}makeShear(e,t,i,r,s,a){return this.set(1,i,s,0,e,1,a,0,t,r,1,0,0,0,0,1),this}compose(e,t,i){const r=this.elements,s=t._x,a=t._y,o=t._z,l=t._w,c=s+s,u=a+a,f=o+o,h=s*c,d=s*u,m=s*f,g=a*u,p=a*f,_=o*f,v=l*c,b=l*u,S=l*f,E=i.x,M=i.y,T=i.z;return r[0]=(1-(g+_))*E,r[1]=(d+S)*E,r[2]=(m-b)*E,r[3]=0,r[4]=(d-S)*M,r[5]=(1-(h+_))*M,r[6]=(p+v)*M,r[7]=0,r[8]=(m+b)*T,r[9]=(p-v)*T,r[10]=(1-(h+g))*T,r[11]=0,r[12]=e.x,r[13]=e.y,r[14]=e.z,r[15]=1,this}decompose(e,t,i){const r=this.elements;e.x=r[12],e.y=r[13],e.z=r[14];const s=this.determinant();if(s===0)return i.set(1,1,1),t.identity(),this;let a=hs.set(r[0],r[1],r[2]).length();const o=hs.set(r[4],r[5],r[6]).length(),l=hs.set(r[8],r[9],r[10]).length();s<0&&(a=-a),ci.copy(this);const c=1/a,u=1/o,f=1/l;return ci.elements[0]*=c,ci.elements[1]*=c,ci.elements[2]*=c,ci.elements[4]*=u,ci.elements[5]*=u,ci.elements[6]*=u,ci.elements[8]*=f,ci.elements[9]*=f,ci.elements[10]*=f,t.setFromRotationMatrix(ci),i.x=a,i.y=o,i.z=l,this}makePerspective(e,t,i,r,s,a,o=Ri,l=!1){const c=this.elements,u=2*s/(t-e),f=2*s/(i-r),h=(t+e)/(t-e),d=(i+r)/(i-r);let m,g;if(l)m=s/(a-s),g=a*s/(a-s);else if(o===Ri)m=-(a+s)/(a-s),g=-2*a*s/(a-s);else if(o===dl)m=-a/(a-s),g=-a*s/(a-s);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return c[0]=u,c[4]=0,c[8]=h,c[12]=0,c[1]=0,c[5]=f,c[9]=d,c[13]=0,c[2]=0,c[6]=0,c[10]=m,c[14]=g,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,i,r,s,a,o=Ri,l=!1){const c=this.elements,u=2/(t-e),f=2/(i-r),h=-(t+e)/(t-e),d=-(i+r)/(i-r);let m,g;if(l)m=1/(a-s),g=a/(a-s);else if(o===Ri)m=-2/(a-s),g=-(a+s)/(a-s);else if(o===dl)m=-1/(a-s),g=-s/(a-s);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return c[0]=u,c[4]=0,c[8]=0,c[12]=h,c[1]=0,c[5]=f,c[9]=0,c[13]=d,c[2]=0,c[6]=0,c[10]=m,c[14]=g,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){const t=this.elements,i=e.elements;for(let r=0;r<16;r++)if(t[r]!==i[r])return!1;return!0}fromArray(e,t=0){for(let i=0;i<16;i++)this.elements[i]=e[i+t];return this}toArray(e=[],t=0){const i=this.elements;return e[t]=i[0],e[t+1]=i[1],e[t+2]=i[2],e[t+3]=i[3],e[t+4]=i[4],e[t+5]=i[5],e[t+6]=i[6],e[t+7]=i[7],e[t+8]=i[8],e[t+9]=i[9],e[t+10]=i[10],e[t+11]=i[11],e[t+12]=i[12],e[t+13]=i[13],e[t+14]=i[14],e[t+15]=i[15],e}};Ll.prototype.isMatrix4=!0;let zt=Ll;const hs=new $,ci=new zt,vv=new $(0,0,0),xv=new $(1,1,1),nr=new $,ho=new $,On=new $,md=new zt,gd=new Mr;class Qr{constructor(e=0,t=0,i=0,r=Qr.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=i,this._order=r}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,i,r=this._order){return this._x=e,this._y=t,this._z=i,this._order=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,i=!0){const r=e.elements,s=r[0],a=r[4],o=r[8],l=r[1],c=r[5],u=r[9],f=r[2],h=r[6],d=r[10];switch(t){case"XYZ":this._y=Math.asin(lt(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-u,d),this._z=Math.atan2(-a,s)):(this._x=Math.atan2(h,c),this._z=0);break;case"YXZ":this._x=Math.asin(-lt(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(o,d),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-f,s),this._z=0);break;case"ZXY":this._x=Math.asin(lt(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(-f,d),this._z=Math.atan2(-a,c)):(this._y=0,this._z=Math.atan2(l,s));break;case"ZYX":this._y=Math.asin(-lt(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(h,d),this._z=Math.atan2(l,s)):(this._x=0,this._z=Math.atan2(-a,c));break;case"YZX":this._z=Math.asin(lt(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-u,c),this._y=Math.atan2(-f,s)):(this._x=0,this._y=Math.atan2(o,d));break;case"XZY":this._z=Math.asin(-lt(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(h,c),this._y=Math.atan2(o,s)):(this._x=Math.atan2(-u,d),this._y=0);break;default:Qe("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,i===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,i){return md.makeRotationFromQuaternion(e),this.setFromRotationMatrix(md,t,i)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return gd.setFromEuler(this),this.setFromQuaternion(gd,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}Qr.DEFAULT_ORDER="XYZ";class Hm{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let yv=0;const _d=new $,fs=new Mr,Ni=new zt,fo=new $,ma=new $,bv=new $,Mv=new Mr,vd=new $(1,0,0),xd=new $(0,1,0),yd=new $(0,0,1),bd={type:"added"},Sv={type:"removed"},ds={type:"childadded",child:null},gc={type:"childremoved",child:null};class _n extends mi{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:yv++}),this.uuid=vr(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=_n.DEFAULT_UP.clone();const e=new $,t=new Qr,i=new Mr,r=new $(1,1,1);function s(){i.setFromEuler(t,!1)}function a(){t.setFromQuaternion(i,void 0,!1)}t._onChange(s),i._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:i},scale:{configurable:!0,enumerable:!0,value:r},modelViewMatrix:{value:new zt},normalMatrix:{value:new rt}}),this.matrix=new zt,this.matrixWorld=new zt,this.matrixAutoUpdate=_n.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=_n.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Hm,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return fs.setFromAxisAngle(e,t),this.quaternion.multiply(fs),this}rotateOnWorldAxis(e,t){return fs.setFromAxisAngle(e,t),this.quaternion.premultiply(fs),this}rotateX(e){return this.rotateOnAxis(vd,e)}rotateY(e){return this.rotateOnAxis(xd,e)}rotateZ(e){return this.rotateOnAxis(yd,e)}translateOnAxis(e,t){return _d.copy(e).applyQuaternion(this.quaternion),this.position.add(_d.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(vd,e)}translateY(e){return this.translateOnAxis(xd,e)}translateZ(e){return this.translateOnAxis(yd,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(Ni.copy(this.matrixWorld).invert())}lookAt(e,t,i){e.isVector3?fo.copy(e):fo.set(e,t,i);const r=this.parent;this.updateWorldMatrix(!0,!1),ma.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?Ni.lookAt(ma,fo,this.up):Ni.lookAt(fo,ma,this.up),this.quaternion.setFromRotationMatrix(Ni),r&&(Ni.extractRotation(r.matrixWorld),fs.setFromRotationMatrix(Ni),this.quaternion.premultiply(fs.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(pt("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(bd),ds.child=e,this.dispatchEvent(ds),ds.child=null):pt("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let i=0;i<arguments.length;i++)this.remove(arguments[i]);return this}const t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(Sv),gc.child=e,this.dispatchEvent(gc),gc.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),Ni.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),Ni.multiply(e.parent.matrixWorld)),e.applyMatrix4(Ni),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(bd),ds.child=e,this.dispatchEvent(ds),ds.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let i=0,r=this.children.length;i<r;i++){const a=this.children[i].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,i=[]){this[e]===t&&i.push(this);const r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].getObjectsByProperty(e,t,i);return i}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(ma,e,bv),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(ma,Mv,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}traverse(e){e(this);const t=this.children;for(let i=0,r=t.length;i<r;i++)t[i].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const t=this.children;for(let i=0,r=t.length;i<r;i++)t[i].traverseVisible(e)}traverseAncestors(e){const t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);const e=this.pivot;if(e!==null){const t=e.x,i=e.y,r=e.z,s=this.matrix.elements;s[12]+=t-s[0]*t-s[4]*i-s[8]*r,s[13]+=i-s[1]*t-s[5]*i-s[9]*r,s[14]+=r-s[2]*t-s[6]*i-s[10]*r}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const t=this.children;for(let i=0,r=t.length;i<r;i++)t[i].updateMatrixWorld(e)}updateWorldMatrix(e,t){const i=this.parent;if(e===!0&&i!==null&&i.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),t===!0){const r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].updateWorldMatrix(!1,!0)}}toJSON(e){const t=e===void 0||typeof e=="string",i={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},i.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});const r={};r.uuid=this.uuid,r.type=this.type,this.name!==""&&(r.name=this.name),this.castShadow===!0&&(r.castShadow=!0),this.receiveShadow===!0&&(r.receiveShadow=!0),this.visible===!1&&(r.visible=!1),this.frustumCulled===!1&&(r.frustumCulled=!1),this.renderOrder!==0&&(r.renderOrder=this.renderOrder),this.static!==!1&&(r.static=this.static),Object.keys(this.userData).length>0&&(r.userData=this.userData),r.layers=this.layers.mask,r.matrix=this.matrix.toArray(),r.up=this.up.toArray(),this.pivot!==null&&(r.pivot=this.pivot.toArray()),this.matrixAutoUpdate===!1&&(r.matrixAutoUpdate=!1),this.morphTargetDictionary!==void 0&&(r.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(r.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(r.type="InstancedMesh",r.count=this.count,r.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(r.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(r.type="BatchedMesh",r.perObjectFrustumCulled=this.perObjectFrustumCulled,r.sortObjects=this.sortObjects,r.drawRanges=this._drawRanges,r.reservedRanges=this._reservedRanges,r.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),r.instanceInfo=this._instanceInfo.map(o=>({...o})),r.availableInstanceIds=this._availableInstanceIds.slice(),r.availableGeometryIds=this._availableGeometryIds.slice(),r.nextIndexStart=this._nextIndexStart,r.nextVertexStart=this._nextVertexStart,r.geometryCount=this._geometryCount,r.maxInstanceCount=this._maxInstanceCount,r.maxVertexCount=this._maxVertexCount,r.maxIndexCount=this._maxIndexCount,r.geometryInitialized=this._geometryInitialized,r.matricesTexture=this._matricesTexture.toJSON(e),r.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(r.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(r.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(r.boundingBox=this.boundingBox.toJSON()));function s(o,l){return o[l.uuid]===void 0&&(o[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?r.background=this.background.toJSON():this.background.isTexture&&(r.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(r.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){r.geometry=s(e.geometries,this.geometry);const o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){const l=o.shapes;if(Array.isArray(l))for(let c=0,u=l.length;c<u;c++){const f=l[c];s(e.shapes,f)}else s(e.shapes,l)}}if(this.isSkinnedMesh&&(r.bindMode=this.bindMode,r.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(s(e.skeletons,this.skeleton),r.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const o=[];for(let l=0,c=this.material.length;l<c;l++)o.push(s(e.materials,this.material[l]));r.material=o}else r.material=s(e.materials,this.material);if(this.children.length>0){r.children=[];for(let o=0;o<this.children.length;o++)r.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){r.animations=[];for(let o=0;o<this.animations.length;o++){const l=this.animations[o];r.animations.push(s(e.animations,l))}}if(t){const o=a(e.geometries),l=a(e.materials),c=a(e.textures),u=a(e.images),f=a(e.shapes),h=a(e.skeletons),d=a(e.animations),m=a(e.nodes);o.length>0&&(i.geometries=o),l.length>0&&(i.materials=l),c.length>0&&(i.textures=c),u.length>0&&(i.images=u),f.length>0&&(i.shapes=f),h.length>0&&(i.skeletons=h),d.length>0&&(i.animations=d),m.length>0&&(i.nodes=m)}return i.object=r,i;function a(o){const l=[];for(const c in o){const u=o[c];delete u.metadata,l.push(u)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let i=0;i<e.children.length;i++){const r=e.children[i];this.add(r.clone())}return this}}_n.DEFAULT_UP=new $(0,1,0);_n.DEFAULT_MATRIX_AUTO_UPDATE=!0;_n.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;class Ds extends _n{constructor(){super(),this.isGroup=!0,this.type="Group"}}const Tv={type:"move"};class _c{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new Ds,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new Ds,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new $,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new $),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new Ds,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new $,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new $,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const t=this._hand;if(t)for(const i of e.hand.values())this._getHandJoint(t,i)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,i){let r=null,s=null,a=null;const o=this._targetRay,l=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){a=!0;for(const g of e.hand.values()){const p=t.getJointPose(g,i),_=this._getHandJoint(c,g);p!==null&&(_.matrix.fromArray(p.transform.matrix),_.matrix.decompose(_.position,_.rotation,_.scale),_.matrixWorldNeedsUpdate=!0,_.jointRadius=p.radius),_.visible=p!==null}const u=c.joints["index-finger-tip"],f=c.joints["thumb-tip"],h=u.position.distanceTo(f.position),d=.02,m=.005;c.inputState.pinching&&h>d+m?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&h<=d-m&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(s=t.getPose(e.gripSpace,i),s!==null&&(l.matrix.fromArray(s.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,s.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(s.linearVelocity)):l.hasLinearVelocity=!1,s.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(s.angularVelocity)):l.hasAngularVelocity=!1,l.eventsEnabled&&l.dispatchEvent({type:"gripUpdated",data:e,target:this})));o!==null&&(r=t.getPose(e.targetRaySpace,i),r===null&&s!==null&&(r=s),r!==null&&(o.matrix.fromArray(r.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,r.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(r.linearVelocity)):o.hasLinearVelocity=!1,r.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(r.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(Tv)))}return o!==null&&(o.visible=r!==null),l!==null&&(l.visible=s!==null),c!==null&&(c.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){const i=new Ds;i.matrixAutoUpdate=!1,i.visible=!1,e.joints[t.jointName]=i,e.add(i)}return e.joints[t.jointName]}}const Vm={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},ir={h:0,s:0,l:0},po={h:0,s:0,l:0};function vc(n,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?n+(e-n)*6*t:t<1/2?e:t<2/3?n+(e-n)*6*(2/3-t):n}class ut{constructor(e,t,i){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,i)}set(e,t,i){if(t===void 0&&i===void 0){const r=e;r&&r.isColor?this.copy(r):typeof r=="number"?this.setHex(r):typeof r=="string"&&this.setStyle(r)}else this.setRGB(e,t,i);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=Tt){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,ft.colorSpaceToWorking(this,t),this}setRGB(e,t,i,r=ft.workingColorSpace){return this.r=e,this.g=t,this.b=i,ft.colorSpaceToWorking(this,r),this}setHSL(e,t,i,r=ft.workingColorSpace){if(e=uv(e,1),t=lt(t,0,1),i=lt(i,0,1),t===0)this.r=this.g=this.b=i;else{const s=i<=.5?i*(1+t):i+t-i*t,a=2*i-s;this.r=vc(a,s,e+1/3),this.g=vc(a,s,e),this.b=vc(a,s,e-1/3)}return ft.colorSpaceToWorking(this,r),this}setStyle(e,t=Tt){function i(s){s!==void 0&&parseFloat(s)<1&&Qe("Color: Alpha component of "+e+" will be ignored.")}let r;if(r=/^(\w+)\(([^\)]*)\)/.exec(e)){let s;const a=r[1],o=r[2];switch(a){case"rgb":case"rgba":if(s=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return i(s[4]),this.setRGB(Math.min(255,parseInt(s[1],10))/255,Math.min(255,parseInt(s[2],10))/255,Math.min(255,parseInt(s[3],10))/255,t);if(s=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return i(s[4]),this.setRGB(Math.min(100,parseInt(s[1],10))/100,Math.min(100,parseInt(s[2],10))/100,Math.min(100,parseInt(s[3],10))/100,t);break;case"hsl":case"hsla":if(s=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return i(s[4]),this.setHSL(parseFloat(s[1])/360,parseFloat(s[2])/100,parseFloat(s[3])/100,t);break;default:Qe("Color: Unknown color model "+e)}}else if(r=/^\#([A-Fa-f\d]+)$/.exec(e)){const s=r[1],a=s.length;if(a===3)return this.setRGB(parseInt(s.charAt(0),16)/15,parseInt(s.charAt(1),16)/15,parseInt(s.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(s,16),t);Qe("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=Tt){const i=Vm[e.toLowerCase()];return i!==void 0?this.setHex(i,t):Qe("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Wi(e.r),this.g=Wi(e.g),this.b=Wi(e.b),this}copyLinearToSRGB(e){return this.r=Fs(e.r),this.g=Fs(e.g),this.b=Fs(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=Tt){return ft.workingToColorSpace(mn.copy(this),e),Math.round(lt(mn.r*255,0,255))*65536+Math.round(lt(mn.g*255,0,255))*256+Math.round(lt(mn.b*255,0,255))}getHexString(e=Tt){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=ft.workingColorSpace){ft.workingToColorSpace(mn.copy(this),t);const i=mn.r,r=mn.g,s=mn.b,a=Math.max(i,r,s),o=Math.min(i,r,s);let l,c;const u=(o+a)/2;if(o===a)l=0,c=0;else{const f=a-o;switch(c=u<=.5?f/(a+o):f/(2-a-o),a){case i:l=(r-s)/f+(r<s?6:0);break;case r:l=(s-i)/f+2;break;case s:l=(i-r)/f+4;break}l/=6}return e.h=l,e.s=c,e.l=u,e}getRGB(e,t=ft.workingColorSpace){return ft.workingToColorSpace(mn.copy(this),t),e.r=mn.r,e.g=mn.g,e.b=mn.b,e}getStyle(e=Tt){ft.workingToColorSpace(mn.copy(this),e);const t=mn.r,i=mn.g,r=mn.b;return e!==Tt?`color(${e} ${t.toFixed(3)} ${i.toFixed(3)} ${r.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(i*255)},${Math.round(r*255)})`}offsetHSL(e,t,i){return this.getHSL(ir),this.setHSL(ir.h+e,ir.s+t,ir.l+i)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,i){return this.r=e.r+(t.r-e.r)*i,this.g=e.g+(t.g-e.g)*i,this.b=e.b+(t.b-e.b)*i,this}lerpHSL(e,t){this.getHSL(ir),e.getHSL(po);const i=hc(ir.h,po.h,t),r=hc(ir.s,po.s,t),s=hc(ir.l,po.l,t);return this.setHSL(i,r,s),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const t=this.r,i=this.g,r=this.b,s=e.elements;return this.r=s[0]*t+s[3]*i+s[6]*r,this.g=s[1]*t+s[4]*i+s[7]*r,this.b=s[2]*t+s[5]*i+s[8]*r,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const mn=new ut;ut.NAMES=Vm;class vh extends _n{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new Qr,this.environmentIntensity=1,this.environmentRotation=new Qr,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(t.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(t.object.backgroundIntensity=this.backgroundIntensity),t.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(t.object.environmentIntensity=this.environmentIntensity),t.object.environmentRotation=this.environmentRotation.toArray(),t}}const ui=new $,Oi=new $,xc=new $,Bi=new $,ps=new $,ms=new $,Md=new $,yc=new $,bc=new $,Mc=new $,Sc=new Ut,Tc=new Ut,Ec=new Ut;class ti{constructor(e=new $,t=new $,i=new $){this.a=e,this.b=t,this.c=i}static getNormal(e,t,i,r){r.subVectors(i,t),ui.subVectors(e,t),r.cross(ui);const s=r.lengthSq();return s>0?r.multiplyScalar(1/Math.sqrt(s)):r.set(0,0,0)}static getBarycoord(e,t,i,r,s){ui.subVectors(r,t),Oi.subVectors(i,t),xc.subVectors(e,t);const a=ui.dot(ui),o=ui.dot(Oi),l=ui.dot(xc),c=Oi.dot(Oi),u=Oi.dot(xc),f=a*c-o*o;if(f===0)return s.set(0,0,0),null;const h=1/f,d=(c*l-o*u)*h,m=(a*u-o*l)*h;return s.set(1-d-m,m,d)}static containsPoint(e,t,i,r){return this.getBarycoord(e,t,i,r,Bi)===null?!1:Bi.x>=0&&Bi.y>=0&&Bi.x+Bi.y<=1}static getInterpolation(e,t,i,r,s,a,o,l){return this.getBarycoord(e,t,i,r,Bi)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(s,Bi.x),l.addScaledVector(a,Bi.y),l.addScaledVector(o,Bi.z),l)}static getInterpolatedAttribute(e,t,i,r,s,a){return Sc.setScalar(0),Tc.setScalar(0),Ec.setScalar(0),Sc.fromBufferAttribute(e,t),Tc.fromBufferAttribute(e,i),Ec.fromBufferAttribute(e,r),a.setScalar(0),a.addScaledVector(Sc,s.x),a.addScaledVector(Tc,s.y),a.addScaledVector(Ec,s.z),a}static isFrontFacing(e,t,i,r){return ui.subVectors(i,t),Oi.subVectors(e,t),ui.cross(Oi).dot(r)<0}set(e,t,i){return this.a.copy(e),this.b.copy(t),this.c.copy(i),this}setFromPointsAndIndices(e,t,i,r){return this.a.copy(e[t]),this.b.copy(e[i]),this.c.copy(e[r]),this}setFromAttributeAndIndices(e,t,i,r){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,i),this.c.fromBufferAttribute(e,r),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return ui.subVectors(this.c,this.b),Oi.subVectors(this.a,this.b),ui.cross(Oi).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return ti.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return ti.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,i,r,s){return ti.getInterpolation(e,this.a,this.b,this.c,t,i,r,s)}containsPoint(e){return ti.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return ti.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){const i=this.a,r=this.b,s=this.c;let a,o;ps.subVectors(r,i),ms.subVectors(s,i),yc.subVectors(e,i);const l=ps.dot(yc),c=ms.dot(yc);if(l<=0&&c<=0)return t.copy(i);bc.subVectors(e,r);const u=ps.dot(bc),f=ms.dot(bc);if(u>=0&&f<=u)return t.copy(r);const h=l*f-u*c;if(h<=0&&l>=0&&u<=0)return a=l/(l-u),t.copy(i).addScaledVector(ps,a);Mc.subVectors(e,s);const d=ps.dot(Mc),m=ms.dot(Mc);if(m>=0&&d<=m)return t.copy(s);const g=d*c-l*m;if(g<=0&&c>=0&&m<=0)return o=c/(c-m),t.copy(i).addScaledVector(ms,o);const p=u*m-d*f;if(p<=0&&f-u>=0&&d-m>=0)return Md.subVectors(s,r),o=(f-u)/(f-u+(d-m)),t.copy(r).addScaledVector(Md,o);const _=1/(p+g+h);return a=g*_,o=h*_,t.copy(i).addScaledVector(ps,a).addScaledVector(ms,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}class $s{constructor(e=new $(1/0,1/0,1/0),t=new $(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,i=e.length;t<i;t+=3)this.expandByPoint(hi.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,i=e.count;t<i;t++)this.expandByPoint(hi.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,i=e.length;t<i;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){const i=hi.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(i),this.max.copy(e).add(i),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);const i=e.geometry;if(i!==void 0){const s=i.getAttribute("position");if(t===!0&&s!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=s.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,hi):hi.fromBufferAttribute(s,a),hi.applyMatrix4(e.matrixWorld),this.expandByPoint(hi);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),mo.copy(e.boundingBox)):(i.boundingBox===null&&i.computeBoundingBox(),mo.copy(i.boundingBox)),mo.applyMatrix4(e.matrixWorld),this.union(mo)}const r=e.children;for(let s=0,a=r.length;s<a;s++)this.expandByObject(r[s],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,hi),hi.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,i;return e.normal.x>0?(t=e.normal.x*this.min.x,i=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,i=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,i+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,i+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,i+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,i+=e.normal.z*this.min.z),t<=-e.constant&&i>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(ga),go.subVectors(this.max,ga),gs.subVectors(e.a,ga),_s.subVectors(e.b,ga),vs.subVectors(e.c,ga),rr.subVectors(_s,gs),sr.subVectors(vs,_s),Pr.subVectors(gs,vs);let t=[0,-rr.z,rr.y,0,-sr.z,sr.y,0,-Pr.z,Pr.y,rr.z,0,-rr.x,sr.z,0,-sr.x,Pr.z,0,-Pr.x,-rr.y,rr.x,0,-sr.y,sr.x,0,-Pr.y,Pr.x,0];return!wc(t,gs,_s,vs,go)||(t=[1,0,0,0,1,0,0,0,1],!wc(t,gs,_s,vs,go))?!1:(_o.crossVectors(rr,sr),t=[_o.x,_o.y,_o.z],wc(t,gs,_s,vs,go))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,hi).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(hi).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(ki[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),ki[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),ki[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),ki[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),ki[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),ki[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),ki[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),ki[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(ki),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}const ki=[new $,new $,new $,new $,new $,new $,new $,new $],hi=new $,mo=new $s,gs=new $,_s=new $,vs=new $,rr=new $,sr=new $,Pr=new $,ga=new $,go=new $,_o=new $,Dr=new $;function wc(n,e,t,i,r){for(let s=0,a=n.length-3;s<=a;s+=3){Dr.fromArray(n,s);const o=r.x*Math.abs(Dr.x)+r.y*Math.abs(Dr.y)+r.z*Math.abs(Dr.z),l=e.dot(Dr),c=t.dot(Dr),u=i.dot(Dr);if(Math.max(-Math.max(l,c,u),Math.min(l,c,u))>o)return!1}return!0}const Xt=new $,vo=new Xe;let Ev=0;class Nt extends mi{constructor(e,t,i=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Ev++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=i,this.usage=mh,this.updateRanges=[],this.gpuType=fi,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,i){e*=this.itemSize,i*=t.itemSize;for(let r=0,s=this.itemSize;r<s;r++)this.array[e+r]=t.array[i+r];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,i=this.count;t<i;t++)vo.fromBufferAttribute(this,t),vo.applyMatrix3(e),this.setXY(t,vo.x,vo.y);else if(this.itemSize===3)for(let t=0,i=this.count;t<i;t++)Xt.fromBufferAttribute(this,t),Xt.applyMatrix3(e),this.setXYZ(t,Xt.x,Xt.y,Xt.z);return this}applyMatrix4(e){for(let t=0,i=this.count;t<i;t++)Xt.fromBufferAttribute(this,t),Xt.applyMatrix4(e),this.setXYZ(t,Xt.x,Xt.y,Xt.z);return this}applyNormalMatrix(e){for(let t=0,i=this.count;t<i;t++)Xt.fromBufferAttribute(this,t),Xt.applyNormalMatrix(e),this.setXYZ(t,Xt.x,Xt.y,Xt.z);return this}transformDirection(e){for(let t=0,i=this.count;t<i;t++)Xt.fromBufferAttribute(this,t),Xt.transformDirection(e),this.setXYZ(t,Xt.x,Xt.y,Xt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let i=this.array[e*this.itemSize+t];return this.normalized&&(i=Ei(i,this.array)),i}setComponent(e,t,i){return this.normalized&&(i=Mt(i,this.array)),this.array[e*this.itemSize+t]=i,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=Ei(t,this.array)),t}setX(e,t){return this.normalized&&(t=Mt(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=Ei(t,this.array)),t}setY(e,t){return this.normalized&&(t=Mt(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=Ei(t,this.array)),t}setZ(e,t){return this.normalized&&(t=Mt(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=Ei(t,this.array)),t}setW(e,t){return this.normalized&&(t=Mt(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,i){return e*=this.itemSize,this.normalized&&(t=Mt(t,this.array),i=Mt(i,this.array)),this.array[e+0]=t,this.array[e+1]=i,this}setXYZ(e,t,i,r){return e*=this.itemSize,this.normalized&&(t=Mt(t,this.array),i=Mt(i,this.array),r=Mt(r,this.array)),this.array[e+0]=t,this.array[e+1]=i,this.array[e+2]=r,this}setXYZW(e,t,i,r,s){return e*=this.itemSize,this.normalized&&(t=Mt(t,this.array),i=Mt(i,this.array),r=Mt(r,this.array),s=Mt(s,this.array)),this.array[e+0]=t,this.array[e+1]=i,this.array[e+2]=r,this.array[e+3]=s,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==mh&&(e.usage=this.usage),e}dispose(){this.dispatchEvent({type:"dispose"})}}class Wm extends Nt{constructor(e,t,i){super(new Uint16Array(e),t,i)}}class Xm extends Nt{constructor(e,t,i){super(new Uint32Array(e),t,i)}}class pi extends Nt{constructor(e,t,i){super(new Float32Array(e),t,i)}}const wv=new $s,_a=new $,Ac=new $;class Js{constructor(e=new $,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){const i=this.center;t!==void 0?i.copy(t):wv.setFromPoints(e).getCenter(i);let r=0;for(let s=0,a=e.length;s<a;s++)r=Math.max(r,i.distanceToSquared(e[s]));return this.radius=Math.sqrt(r),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){const i=this.center.distanceToSquared(e);return t.copy(e),i>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;_a.subVectors(e,this.center);const t=_a.lengthSq();if(t>this.radius*this.radius){const i=Math.sqrt(t),r=(i-this.radius)*.5;this.center.addScaledVector(_a,r/i),this.radius+=r}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Ac.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(_a.copy(e.center).add(Ac)),this.expandByPoint(_a.copy(e.center).sub(Ac))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}let Av=0;const Jn=new zt,Rc=new _n,xs=new $,Bn=new $s,va=new $s,sn=new $;class Rt extends mi{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:Av++}),this.uuid=vr(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(av(e)?Xm:Wm)(e,1):this.index=e,this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,i=0){this.groups.push({start:e,count:t,materialIndex:i})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){const t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);const i=this.attributes.normal;if(i!==void 0){const s=new rt().getNormalMatrix(e);i.applyNormalMatrix(s),i.needsUpdate=!0}const r=this.attributes.tangent;return r!==void 0&&(r.transformDirection(e),r.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return Jn.makeRotationFromQuaternion(e),this.applyMatrix4(Jn),this}rotateX(e){return Jn.makeRotationX(e),this.applyMatrix4(Jn),this}rotateY(e){return Jn.makeRotationY(e),this.applyMatrix4(Jn),this}rotateZ(e){return Jn.makeRotationZ(e),this.applyMatrix4(Jn),this}translate(e,t,i){return Jn.makeTranslation(e,t,i),this.applyMatrix4(Jn),this}scale(e,t,i){return Jn.makeScale(e,t,i),this.applyMatrix4(Jn),this}lookAt(e){return Rc.lookAt(e),Rc.updateMatrix(),this.applyMatrix4(Rc.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(xs).negate(),this.translate(xs.x,xs.y,xs.z),this}setFromPoints(e){const t=this.getAttribute("position");if(t===void 0){const i=[];for(let r=0,s=e.length;r<s;r++){const a=e[r];i.push(a.x,a.y,a.z||0)}this.setAttribute("position",new pi(i,3))}else{const i=Math.min(e.length,t.count);for(let r=0;r<i;r++){const s=e[r];t.setXYZ(r,s.x,s.y,s.z||0)}e.length>t.count&&Qe("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new $s);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){pt("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new $(-1/0,-1/0,-1/0),new $(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let i=0,r=t.length;i<r;i++){const s=t[i];Bn.setFromBufferAttribute(s),this.morphTargetsRelative?(sn.addVectors(this.boundingBox.min,Bn.min),this.boundingBox.expandByPoint(sn),sn.addVectors(this.boundingBox.max,Bn.max),this.boundingBox.expandByPoint(sn)):(this.boundingBox.expandByPoint(Bn.min),this.boundingBox.expandByPoint(Bn.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&pt('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Js);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){pt("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new $,1/0);return}if(e){const i=this.boundingSphere.center;if(Bn.setFromBufferAttribute(e),t)for(let s=0,a=t.length;s<a;s++){const o=t[s];va.setFromBufferAttribute(o),this.morphTargetsRelative?(sn.addVectors(Bn.min,va.min),Bn.expandByPoint(sn),sn.addVectors(Bn.max,va.max),Bn.expandByPoint(sn)):(Bn.expandByPoint(va.min),Bn.expandByPoint(va.max))}Bn.getCenter(i);let r=0;for(let s=0,a=e.count;s<a;s++)sn.fromBufferAttribute(e,s),r=Math.max(r,i.distanceToSquared(sn));if(t)for(let s=0,a=t.length;s<a;s++){const o=t[s],l=this.morphTargetsRelative;for(let c=0,u=o.count;c<u;c++)sn.fromBufferAttribute(o,c),l&&(xs.fromBufferAttribute(e,c),sn.add(xs)),r=Math.max(r,i.distanceToSquared(sn))}this.boundingSphere.radius=Math.sqrt(r),isNaN(this.boundingSphere.radius)&&pt('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){pt("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const i=t.position,r=t.normal,s=t.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new Nt(new Float32Array(4*i.count),4));const a=this.getAttribute("tangent"),o=[],l=[];for(let x=0;x<i.count;x++)o[x]=new $,l[x]=new $;const c=new $,u=new $,f=new $,h=new Xe,d=new Xe,m=new Xe,g=new $,p=new $;function _(x,y,w){c.fromBufferAttribute(i,x),u.fromBufferAttribute(i,y),f.fromBufferAttribute(i,w),h.fromBufferAttribute(s,x),d.fromBufferAttribute(s,y),m.fromBufferAttribute(s,w),u.sub(c),f.sub(c),d.sub(h),m.sub(h);const C=1/(d.x*m.y-m.x*d.y);isFinite(C)&&(g.copy(u).multiplyScalar(m.y).addScaledVector(f,-d.y).multiplyScalar(C),p.copy(f).multiplyScalar(d.x).addScaledVector(u,-m.x).multiplyScalar(C),o[x].add(g),o[y].add(g),o[w].add(g),l[x].add(p),l[y].add(p),l[w].add(p))}let v=this.groups;v.length===0&&(v=[{start:0,count:e.count}]);for(let x=0,y=v.length;x<y;++x){const w=v[x],C=w.start,R=w.count;for(let L=C,U=C+R;L<U;L+=3)_(e.getX(L+0),e.getX(L+1),e.getX(L+2))}const b=new $,S=new $,E=new $,M=new $;function T(x){E.fromBufferAttribute(r,x),M.copy(E);const y=o[x];b.copy(y),b.sub(E.multiplyScalar(E.dot(y))).normalize(),S.crossVectors(M,y);const C=S.dot(l[x])<0?-1:1;a.setXYZW(x,b.x,b.y,b.z,C)}for(let x=0,y=v.length;x<y;++x){const w=v[x],C=w.start,R=w.count;for(let L=C,U=C+R;L<U;L+=3)T(e.getX(L+0)),T(e.getX(L+1)),T(e.getX(L+2))}}computeVertexNormals(){const e=this.index,t=this.getAttribute("position");if(t!==void 0){let i=this.getAttribute("normal");if(i===void 0)i=new Nt(new Float32Array(t.count*3),3),this.setAttribute("normal",i);else for(let h=0,d=i.count;h<d;h++)i.setXYZ(h,0,0,0);const r=new $,s=new $,a=new $,o=new $,l=new $,c=new $,u=new $,f=new $;if(e)for(let h=0,d=e.count;h<d;h+=3){const m=e.getX(h+0),g=e.getX(h+1),p=e.getX(h+2);r.fromBufferAttribute(t,m),s.fromBufferAttribute(t,g),a.fromBufferAttribute(t,p),u.subVectors(a,s),f.subVectors(r,s),u.cross(f),o.fromBufferAttribute(i,m),l.fromBufferAttribute(i,g),c.fromBufferAttribute(i,p),o.add(u),l.add(u),c.add(u),i.setXYZ(m,o.x,o.y,o.z),i.setXYZ(g,l.x,l.y,l.z),i.setXYZ(p,c.x,c.y,c.z)}else for(let h=0,d=t.count;h<d;h+=3)r.fromBufferAttribute(t,h+0),s.fromBufferAttribute(t,h+1),a.fromBufferAttribute(t,h+2),u.subVectors(a,s),f.subVectors(r,s),u.cross(f),i.setXYZ(h+0,u.x,u.y,u.z),i.setXYZ(h+1,u.x,u.y,u.z),i.setXYZ(h+2,u.x,u.y,u.z);this.normalizeNormals(),i.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let t=0,i=e.count;t<i;t++)sn.fromBufferAttribute(e,t),sn.normalize(),e.setXYZ(t,sn.x,sn.y,sn.z)}toNonIndexed(){function e(o,l){const c=o.array,u=o.itemSize,f=o.normalized,h=new c.constructor(l.length*u);let d=0,m=0;for(let g=0,p=l.length;g<p;g++){o.isInterleavedBufferAttribute?d=l[g]*o.data.stride+o.offset:d=l[g]*u;for(let _=0;_<u;_++)h[m++]=c[d++]}return new Nt(h,u,f)}if(this.index===null)return Qe("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const t=new Rt,i=this.index.array,r=this.attributes;for(const o in r){const l=r[o],c=e(l,i);t.setAttribute(o,c)}const s=this.morphAttributes;for(const o in s){const l=[],c=s[o];for(let u=0,f=c.length;u<f;u++){const h=c[u],d=e(h,i);l.push(d)}t.morphAttributes[o]=l}t.morphTargetsRelative=this.morphTargetsRelative;const a=this.groups;for(let o=0,l=a.length;o<l;o++){const c=a[o];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){const e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){const l=this.parameters;for(const c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};const t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});const i=this.attributes;for(const l in i){const c=i[l];e.data.attributes[l]=c.toJSON(e.data)}const r={};let s=!1;for(const l in this.morphAttributes){const c=this.morphAttributes[l],u=[];for(let f=0,h=c.length;f<h;f++){const d=c[f];u.push(d.toJSON(e.data))}u.length>0&&(r[l]=u,s=!0)}s&&(e.data.morphAttributes=r,e.data.morphTargetsRelative=this.morphTargetsRelative);const a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));const o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const t={};this.name=e.name;const i=e.index;i!==null&&this.setIndex(i.clone());const r=e.attributes;for(const c in r){const u=r[c];this.setAttribute(c,u.clone(t))}const s=e.morphAttributes;for(const c in s){const u=[],f=s[c];for(let h=0,d=f.length;h<d;h++)u.push(f[h].clone(t));this.morphAttributes[c]=u}this.morphTargetsRelative=e.morphTargetsRelative;const a=e.groups;for(let c=0,u=a.length;c<u;c++){const f=a[c];this.addGroup(f.start,f.count,f.materialIndex)}const o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());const l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}}class Rv{constructor(e,t){this.isInterleavedBuffer=!0,this.array=e,this.stride=t,this.count=e!==void 0?e.length/t:0,this.usage=mh,this.updateRanges=[],this.version=0,this.uuid=vr()}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.array=new e.array.constructor(e.array),this.count=e.count,this.stride=e.stride,this.usage=e.usage,this}copyAt(e,t,i){e*=this.stride,i*=t.stride;for(let r=0,s=this.stride;r<s;r++)this.array[e+r]=t.array[i+r];return this}set(e,t=0){return this.array.set(e,t),this}clone(e){e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=vr()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer);const t=new this.array.constructor(e.arrayBuffers[this.array.buffer._uuid]),i=new this.constructor(t,this.stride);return i.setUsage(this.usage),i}onUpload(e){return this.onUploadCallback=e,this}toJSON(e){return e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=vr()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer))),{uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride}}}const bn=new $;class gl{constructor(e,t,i,r=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=e,this.itemSize=t,this.offset=i,this.normalized=r}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(e){this.data.needsUpdate=e}applyMatrix4(e){for(let t=0,i=this.data.count;t<i;t++)bn.fromBufferAttribute(this,t),bn.applyMatrix4(e),this.setXYZ(t,bn.x,bn.y,bn.z);return this}applyNormalMatrix(e){for(let t=0,i=this.count;t<i;t++)bn.fromBufferAttribute(this,t),bn.applyNormalMatrix(e),this.setXYZ(t,bn.x,bn.y,bn.z);return this}transformDirection(e){for(let t=0,i=this.count;t<i;t++)bn.fromBufferAttribute(this,t),bn.transformDirection(e),this.setXYZ(t,bn.x,bn.y,bn.z);return this}getComponent(e,t){let i=this.array[e*this.data.stride+this.offset+t];return this.normalized&&(i=Ei(i,this.array)),i}setComponent(e,t,i){return this.normalized&&(i=Mt(i,this.array)),this.data.array[e*this.data.stride+this.offset+t]=i,this}setX(e,t){return this.normalized&&(t=Mt(t,this.array)),this.data.array[e*this.data.stride+this.offset]=t,this}setY(e,t){return this.normalized&&(t=Mt(t,this.array)),this.data.array[e*this.data.stride+this.offset+1]=t,this}setZ(e,t){return this.normalized&&(t=Mt(t,this.array)),this.data.array[e*this.data.stride+this.offset+2]=t,this}setW(e,t){return this.normalized&&(t=Mt(t,this.array)),this.data.array[e*this.data.stride+this.offset+3]=t,this}getX(e){let t=this.data.array[e*this.data.stride+this.offset];return this.normalized&&(t=Ei(t,this.array)),t}getY(e){let t=this.data.array[e*this.data.stride+this.offset+1];return this.normalized&&(t=Ei(t,this.array)),t}getZ(e){let t=this.data.array[e*this.data.stride+this.offset+2];return this.normalized&&(t=Ei(t,this.array)),t}getW(e){let t=this.data.array[e*this.data.stride+this.offset+3];return this.normalized&&(t=Ei(t,this.array)),t}setXY(e,t,i){return e=e*this.data.stride+this.offset,this.normalized&&(t=Mt(t,this.array),i=Mt(i,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=i,this}setXYZ(e,t,i,r){return e=e*this.data.stride+this.offset,this.normalized&&(t=Mt(t,this.array),i=Mt(i,this.array),r=Mt(r,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=i,this.data.array[e+2]=r,this}setXYZW(e,t,i,r,s){return e=e*this.data.stride+this.offset,this.normalized&&(t=Mt(t,this.array),i=Mt(i,this.array),r=Mt(r,this.array),s=Mt(s,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=i,this.data.array[e+2]=r,this.data.array[e+3]=s,this}clone(e){if(e===void 0){ml("InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");const t=[];for(let i=0;i<this.count;i++){const r=i*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return new Nt(new this.array.constructor(t),this.itemSize,this.normalized)}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.clone(e)),new gl(e.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}toJSON(e){if(e===void 0){ml("InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");const t=[];for(let i=0;i<this.count;i++){const r=i*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:t,normalized:this.normalized}}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.toJSON(e)),{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}}let Cv=0;class $i extends mi{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Cv++}),this.uuid=vr(),this.name="",this.type="Material",this.blending=Vr,this.side=ji,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Cu,this.blendDst=Pu,this.blendEquation=kr,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new ut(0,0,0),this.blendAlpha=0,this.depthFunc=zs,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=cd,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=cs,this.stencilZFail=cs,this.stencilZPass=cs,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const t in e){const i=e[t];if(i===void 0){Qe(`Material: parameter '${t}' has value of undefined.`);continue}const r=this[t];if(r===void 0){Qe(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}r&&r.isColor?r.set(i):r&&r.isVector3&&i&&i.isVector3?r.copy(i):this[t]=i}}toJSON(e){const t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});const i={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};i.uuid=this.uuid,i.type=this.type,this.name!==""&&(i.name=this.name),this.color&&this.color.isColor&&(i.color=this.color.getHex()),this.roughness!==void 0&&(i.roughness=this.roughness),this.metalness!==void 0&&(i.metalness=this.metalness),this.sheen!==void 0&&(i.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(i.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(i.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(i.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(i.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(i.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(i.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(i.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(i.shininess=this.shininess),this.clearcoat!==void 0&&(i.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(i.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(i.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(i.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(i.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,i.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(i.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(i.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(i.dispersion=this.dispersion),this.iridescence!==void 0&&(i.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(i.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(i.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(i.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(i.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(i.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(i.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(i.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(i.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(i.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(i.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(i.lightMap=this.lightMap.toJSON(e).uuid,i.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(i.aoMap=this.aoMap.toJSON(e).uuid,i.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(i.bumpMap=this.bumpMap.toJSON(e).uuid,i.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(i.normalMap=this.normalMap.toJSON(e).uuid,i.normalMapType=this.normalMapType,i.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(i.displacementMap=this.displacementMap.toJSON(e).uuid,i.displacementScale=this.displacementScale,i.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(i.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(i.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(i.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(i.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(i.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(i.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(i.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(i.combine=this.combine)),this.envMapRotation!==void 0&&(i.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(i.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(i.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(i.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(i.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(i.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(i.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(i.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(i.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(i.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(i.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(i.size=this.size),this.shadowSide!==null&&(i.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(i.sizeAttenuation=this.sizeAttenuation),this.blending!==Vr&&(i.blending=this.blending),this.side!==ji&&(i.side=this.side),this.vertexColors===!0&&(i.vertexColors=!0),this.opacity<1&&(i.opacity=this.opacity),this.transparent===!0&&(i.transparent=!0),this.blendSrc!==Cu&&(i.blendSrc=this.blendSrc),this.blendDst!==Pu&&(i.blendDst=this.blendDst),this.blendEquation!==kr&&(i.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(i.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(i.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(i.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(i.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(i.blendAlpha=this.blendAlpha),this.depthFunc!==zs&&(i.depthFunc=this.depthFunc),this.depthTest===!1&&(i.depthTest=this.depthTest),this.depthWrite===!1&&(i.depthWrite=this.depthWrite),this.colorWrite===!1&&(i.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(i.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==cd&&(i.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(i.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(i.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==cs&&(i.stencilFail=this.stencilFail),this.stencilZFail!==cs&&(i.stencilZFail=this.stencilZFail),this.stencilZPass!==cs&&(i.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(i.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(i.rotation=this.rotation),this.polygonOffset===!0&&(i.polygonOffset=!0),this.polygonOffsetFactor!==0&&(i.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(i.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(i.linewidth=this.linewidth),this.dashSize!==void 0&&(i.dashSize=this.dashSize),this.gapSize!==void 0&&(i.gapSize=this.gapSize),this.scale!==void 0&&(i.scale=this.scale),this.dithering===!0&&(i.dithering=!0),this.alphaTest>0&&(i.alphaTest=this.alphaTest),this.alphaHash===!0&&(i.alphaHash=!0),this.alphaToCoverage===!0&&(i.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(i.premultipliedAlpha=!0),this.forceSinglePass===!0&&(i.forceSinglePass=!0),this.allowOverride===!1&&(i.allowOverride=!1),this.wireframe===!0&&(i.wireframe=!0),this.wireframeLinewidth>1&&(i.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(i.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(i.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(i.flatShading=!0),this.visible===!1&&(i.visible=!1),this.toneMapped===!1&&(i.toneMapped=!1),this.fog===!1&&(i.fog=!1),Object.keys(this.userData).length>0&&(i.userData=this.userData);function r(s){const a=[];for(const o in s){const l=s[o];delete l.metadata,a.push(l)}return a}if(t){const s=r(e.textures),a=r(e.images);s.length>0&&(i.textures=s),a.length>0&&(i.images=a)}return i}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const t=e.clippingPlanes;let i=null;if(t!==null){const r=t.length;i=new Array(r);for(let s=0;s!==r;++s)i[s]=t[s].clone()}return this.clippingPlanes=i,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}}class Ca extends $i{constructor(e){super(),this.isSpriteMaterial=!0,this.type="SpriteMaterial",this.color=new ut(16777215),this.map=null,this.alphaMap=null,this.rotation=0,this.sizeAttenuation=!0,this.transparent=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.rotation=e.rotation,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}let ys;const xa=new $,bs=new $,Ms=new $,Ss=new Xe,ya=new Xe,jm=new zt,xo=new $,ba=new $,yo=new $,Sd=new Xe,Cc=new Xe,Td=new Xe;class bo extends _n{constructor(e=new Ca){if(super(),this.isSprite=!0,this.type="Sprite",ys===void 0){ys=new Rt;const t=new Float32Array([-.5,-.5,0,0,0,.5,-.5,0,1,0,.5,.5,0,1,1,-.5,.5,0,0,1]),i=new Rv(t,5);ys.setIndex([0,1,2,0,2,3]),ys.setAttribute("position",new gl(i,3,0,!1)),ys.setAttribute("uv",new gl(i,2,3,!1))}this.geometry=ys,this.material=e,this.center=new Xe(.5,.5),this.count=1}raycast(e,t){e.camera===null&&pt('Sprite: "Raycaster.camera" needs to be set in order to raycast against sprites.'),bs.setFromMatrixScale(this.matrixWorld),jm.copy(e.camera.matrixWorld),this.modelViewMatrix.multiplyMatrices(e.camera.matrixWorldInverse,this.matrixWorld),Ms.setFromMatrixPosition(this.modelViewMatrix),e.camera.isPerspectiveCamera&&this.material.sizeAttenuation===!1&&bs.multiplyScalar(-Ms.z);const i=this.material.rotation;let r,s;i!==0&&(s=Math.cos(i),r=Math.sin(i));const a=this.center;Mo(xo.set(-.5,-.5,0),Ms,a,bs,r,s),Mo(ba.set(.5,-.5,0),Ms,a,bs,r,s),Mo(yo.set(.5,.5,0),Ms,a,bs,r,s),Sd.set(0,0),Cc.set(1,0),Td.set(1,1);let o=e.ray.intersectTriangle(xo,ba,yo,!1,xa);if(o===null&&(Mo(ba.set(-.5,.5,0),Ms,a,bs,r,s),Cc.set(0,1),o=e.ray.intersectTriangle(xo,yo,ba,!1,xa),o===null))return;const l=e.ray.origin.distanceTo(xa);l<e.near||l>e.far||t.push({distance:l,point:xa.clone(),uv:ti.getInterpolation(xa,xo,ba,yo,Sd,Cc,Td,new Xe),face:null,object:this})}copy(e,t){return super.copy(e,t),e.center!==void 0&&this.center.copy(e.center),this.material=e.material,this}}function Mo(n,e,t,i,r,s){Ss.subVectors(n,t).addScalar(.5).multiply(i),r!==void 0?(ya.x=s*Ss.x-r*Ss.y,ya.y=r*Ss.x+s*Ss.y):ya.copy(Ss),n.copy(e),n.x+=ya.x,n.y+=ya.y,n.applyMatrix4(jm)}const zi=new $,Pc=new $,So=new $,ar=new $,Dc=new $,To=new $,Uc=new $;class Fl{constructor(e=new $,t=new $(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,zi)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);const i=t.dot(this.direction);return i<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,i)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const t=zi.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(zi.copy(this.origin).addScaledVector(this.direction,t),zi.distanceToSquared(e))}distanceSqToSegment(e,t,i,r){Pc.copy(e).add(t).multiplyScalar(.5),So.copy(t).sub(e).normalize(),ar.copy(this.origin).sub(Pc);const s=e.distanceTo(t)*.5,a=-this.direction.dot(So),o=ar.dot(this.direction),l=-ar.dot(So),c=ar.lengthSq(),u=Math.abs(1-a*a);let f,h,d,m;if(u>0)if(f=a*l-o,h=a*o-l,m=s*u,f>=0)if(h>=-m)if(h<=m){const g=1/u;f*=g,h*=g,d=f*(f+a*h+2*o)+h*(a*f+h+2*l)+c}else h=s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;else h=-s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;else h<=-m?(f=Math.max(0,-(-a*s+o)),h=f>0?-s:Math.min(Math.max(-s,-l),s),d=-f*f+h*(h+2*l)+c):h<=m?(f=0,h=Math.min(Math.max(-s,-l),s),d=h*(h+2*l)+c):(f=Math.max(0,-(a*s+o)),h=f>0?s:Math.min(Math.max(-s,-l),s),d=-f*f+h*(h+2*l)+c);else h=a>0?-s:s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;return i&&i.copy(this.origin).addScaledVector(this.direction,f),r&&r.copy(Pc).addScaledVector(So,h),d}intersectSphere(e,t){zi.subVectors(e.center,this.origin);const i=zi.dot(this.direction),r=zi.dot(zi)-i*i,s=e.radius*e.radius;if(r>s)return null;const a=Math.sqrt(s-r),o=i-a,l=i+a;return l<0?null:o<0?this.at(l,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;const i=-(this.origin.dot(e.normal)+e.constant)/t;return i>=0?i:null}intersectPlane(e,t){const i=this.distanceToPlane(e);return i===null?null:this.at(i,t)}intersectsPlane(e){const t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let i,r,s,a,o,l;const c=1/this.direction.x,u=1/this.direction.y,f=1/this.direction.z,h=this.origin;return c>=0?(i=(e.min.x-h.x)*c,r=(e.max.x-h.x)*c):(i=(e.max.x-h.x)*c,r=(e.min.x-h.x)*c),u>=0?(s=(e.min.y-h.y)*u,a=(e.max.y-h.y)*u):(s=(e.max.y-h.y)*u,a=(e.min.y-h.y)*u),i>a||s>r||((s>i||isNaN(i))&&(i=s),(a<r||isNaN(r))&&(r=a),f>=0?(o=(e.min.z-h.z)*f,l=(e.max.z-h.z)*f):(o=(e.max.z-h.z)*f,l=(e.min.z-h.z)*f),i>l||o>r)||((o>i||i!==i)&&(i=o),(l<r||r!==r)&&(r=l),r<0)?null:this.at(i>=0?i:r,t)}intersectsBox(e){return this.intersectBox(e,zi)!==null}intersectTriangle(e,t,i,r,s){Dc.subVectors(t,e),To.subVectors(i,e),Uc.crossVectors(Dc,To);let a=this.direction.dot(Uc),o;if(a>0){if(r)return null;o=1}else if(a<0)o=-1,a=-a;else return null;ar.subVectors(this.origin,e);const l=o*this.direction.dot(To.crossVectors(ar,To));if(l<0)return null;const c=o*this.direction.dot(Dc.cross(ar));if(c<0||l+c>a)return null;const u=-o*ar.dot(Uc);return u<0?null:this.at(u/a,s)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class sf extends $i{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new ut(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Qr,this.combine=Tm,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const Ed=new zt,Ur=new Fl,Eo=new Js,wd=new $,wo=new $,Ao=new $,Ro=new $,Lc=new $,Co=new $,Ad=new $,Po=new $;class Yn extends _n{constructor(e=new Rt,t=new sf){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const t=this.geometry.morphAttributes,i=Object.keys(t);if(i.length>0){const r=t[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){const o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}getVertexPosition(e,t){const i=this.geometry,r=i.attributes.position,s=i.morphAttributes.position,a=i.morphTargetsRelative;t.fromBufferAttribute(r,e);const o=this.morphTargetInfluences;if(s&&o){Co.set(0,0,0);for(let l=0,c=s.length;l<c;l++){const u=o[l],f=s[l];u!==0&&(Lc.fromBufferAttribute(f,e),a?Co.addScaledVector(Lc,u):Co.addScaledVector(Lc.sub(t),u))}t.add(Co)}return t}raycast(e,t){const i=this.geometry,r=this.material,s=this.matrixWorld;r!==void 0&&(i.boundingSphere===null&&i.computeBoundingSphere(),Eo.copy(i.boundingSphere),Eo.applyMatrix4(s),Ur.copy(e.ray).recast(e.near),!(Eo.containsPoint(Ur.origin)===!1&&(Ur.intersectSphere(Eo,wd)===null||Ur.origin.distanceToSquared(wd)>(e.far-e.near)**2))&&(Ed.copy(s).invert(),Ur.copy(e.ray).applyMatrix4(Ed),!(i.boundingBox!==null&&Ur.intersectsBox(i.boundingBox)===!1)&&this._computeIntersections(e,t,Ur)))}_computeIntersections(e,t,i){let r;const s=this.geometry,a=this.material,o=s.index,l=s.attributes.position,c=s.attributes.uv,u=s.attributes.uv1,f=s.attributes.normal,h=s.groups,d=s.drawRange;if(o!==null)if(Array.isArray(a))for(let m=0,g=h.length;m<g;m++){const p=h[m],_=a[p.materialIndex],v=Math.max(p.start,d.start),b=Math.min(o.count,Math.min(p.start+p.count,d.start+d.count));for(let S=v,E=b;S<E;S+=3){const M=o.getX(S),T=o.getX(S+1),x=o.getX(S+2);r=Do(this,_,e,i,c,u,f,M,T,x),r&&(r.faceIndex=Math.floor(S/3),r.face.materialIndex=p.materialIndex,t.push(r))}}else{const m=Math.max(0,d.start),g=Math.min(o.count,d.start+d.count);for(let p=m,_=g;p<_;p+=3){const v=o.getX(p),b=o.getX(p+1),S=o.getX(p+2);r=Do(this,a,e,i,c,u,f,v,b,S),r&&(r.faceIndex=Math.floor(p/3),t.push(r))}}else if(l!==void 0)if(Array.isArray(a))for(let m=0,g=h.length;m<g;m++){const p=h[m],_=a[p.materialIndex],v=Math.max(p.start,d.start),b=Math.min(l.count,Math.min(p.start+p.count,d.start+d.count));for(let S=v,E=b;S<E;S+=3){const M=S,T=S+1,x=S+2;r=Do(this,_,e,i,c,u,f,M,T,x),r&&(r.faceIndex=Math.floor(S/3),r.face.materialIndex=p.materialIndex,t.push(r))}}else{const m=Math.max(0,d.start),g=Math.min(l.count,d.start+d.count);for(let p=m,_=g;p<_;p+=3){const v=p,b=p+1,S=p+2;r=Do(this,a,e,i,c,u,f,v,b,S),r&&(r.faceIndex=Math.floor(p/3),t.push(r))}}}}function Pv(n,e,t,i,r,s,a,o){let l;if(e.side===on?l=i.intersectTriangle(a,s,r,!0,o):l=i.intersectTriangle(r,s,a,e.side===ji,o),l===null)return null;Po.copy(o),Po.applyMatrix4(n.matrixWorld);const c=t.ray.origin.distanceTo(Po);return c<t.near||c>t.far?null:{distance:c,point:Po.clone(),object:n}}function Do(n,e,t,i,r,s,a,o,l,c){n.getVertexPosition(o,wo),n.getVertexPosition(l,Ao),n.getVertexPosition(c,Ro);const u=Pv(n,e,t,i,wo,Ao,Ro,Ad);if(u){const f=new $;ti.getBarycoord(Ad,wo,Ao,Ro,f),r&&(u.uv=ti.getInterpolatedAttribute(r,o,l,c,f,new Xe)),s&&(u.uv1=ti.getInterpolatedAttribute(s,o,l,c,f,new Xe)),a&&(u.normal=ti.getInterpolatedAttribute(a,o,l,c,f,new $),u.normal.dot(i.direction)>0&&u.normal.multiplyScalar(-1));const h={a:o,b:l,c,normal:new $,materialIndex:0};ti.getNormal(wo,Ao,Ro,h.normal),u.face=h,u.barycoord=f}return u}class Dv extends Jt{constructor(e=null,t=1,i=1,r,s,a,o,l,c=hn,u=hn,f,h){super(null,a,o,l,c,u,r,s,f,h),this.isDataTexture=!0,this.image={data:e,width:t,height:i},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class Uv extends Nt{constructor(e,t,i,r=1){super(e,t,i),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=r}copy(e){return super.copy(e),this.meshPerAttribute=e.meshPerAttribute,this}toJSON(){const e=super.toJSON();return e.meshPerAttribute=this.meshPerAttribute,e.isInstancedBufferAttribute=!0,e}}const Ic=new $,Lv=new $,Iv=new rt;class hr{constructor(e=new $(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,i,r){return this.normal.set(e,t,i),this.constant=r,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,i){const r=Ic.subVectors(i,t).cross(Lv.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(r,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t,i=!0){const r=e.delta(Ic),s=this.normal.dot(r);if(s===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;const a=-(e.start.dot(this.normal)+this.constant)/s;return i===!0&&(a<0||a>1)?null:t.copy(e.start).addScaledVector(r,a)}intersectsLine(e){const t=this.distanceToPoint(e.start),i=this.distanceToPoint(e.end);return t<0&&i>0||i<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){const i=t||Iv.getNormalMatrix(e),r=this.coplanarPoint(Ic).applyMatrix4(e),s=this.normal.applyMatrix3(i).normalize();return this.constant=-r.dot(s),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}}const Lr=new Js,Fv=new Xe(.5,.5),Uo=new $;class Ym{constructor(e=new hr,t=new hr,i=new hr,r=new hr,s=new hr,a=new hr){this.planes=[e,t,i,r,s,a]}set(e,t,i,r,s,a){const o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(i),o[3].copy(r),o[4].copy(s),o[5].copy(a),this}copy(e){const t=this.planes;for(let i=0;i<6;i++)t[i].copy(e.planes[i]);return this}setFromProjectionMatrix(e,t=Ri,i=!1){const r=this.planes,s=e.elements,a=s[0],o=s[1],l=s[2],c=s[3],u=s[4],f=s[5],h=s[6],d=s[7],m=s[8],g=s[9],p=s[10],_=s[11],v=s[12],b=s[13],S=s[14],E=s[15];if(r[0].setComponents(c-a,d-u,_-m,E-v).normalize(),r[1].setComponents(c+a,d+u,_+m,E+v).normalize(),r[2].setComponents(c+o,d+f,_+g,E+b).normalize(),r[3].setComponents(c-o,d-f,_-g,E-b).normalize(),i)r[4].setComponents(l,h,p,S).normalize(),r[5].setComponents(c-l,d-h,_-p,E-S).normalize();else if(r[4].setComponents(c-l,d-h,_-p,E-S).normalize(),t===Ri)r[5].setComponents(c+l,d+h,_+p,E+S).normalize();else if(t===dl)r[5].setComponents(l,h,p,S).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Lr.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),Lr.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Lr)}intersectsSprite(e){Lr.center.set(0,0,0);const t=Fv.distanceTo(e.center);return Lr.radius=.7071067811865476+t,Lr.applyMatrix4(e.matrixWorld),this.intersectsSphere(Lr)}intersectsSphere(e){const t=this.planes,i=e.center,r=-e.radius;for(let s=0;s<6;s++)if(t[s].distanceToPoint(i)<r)return!1;return!0}intersectsBox(e){const t=this.planes;for(let i=0;i<6;i++){const r=t[i];if(Uo.x=r.normal.x>0?e.max.x:e.min.x,Uo.y=r.normal.y>0?e.max.y:e.min.y,Uo.z=r.normal.z>0?e.max.z:e.min.z,r.distanceToPoint(Uo)<0)return!1}return!0}containsPoint(e){const t=this.planes;for(let i=0;i<6;i++)if(t[i].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class Cs extends $i{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new ut(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}}const _l=new $,vl=new $,Rd=new zt,Ma=new Fl,Lo=new Js,Fc=new $,Cd=new $;class xl extends _n{constructor(e=new Rt,t=new Cs){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,i=[0];for(let r=1,s=t.count;r<s;r++)_l.fromBufferAttribute(t,r-1),vl.fromBufferAttribute(t,r),i[r]=i[r-1],i[r]+=_l.distanceTo(vl);e.setAttribute("lineDistance",new pi(i,1))}else Qe("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(e,t){const i=this.geometry,r=this.matrixWorld,s=e.params.Line.threshold,a=i.drawRange;if(i.boundingSphere===null&&i.computeBoundingSphere(),Lo.copy(i.boundingSphere),Lo.applyMatrix4(r),Lo.radius+=s,e.ray.intersectsSphere(Lo)===!1)return;Rd.copy(r).invert(),Ma.copy(e.ray).applyMatrix4(Rd);const o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=this.isLineSegments?2:1,u=i.index,h=i.attributes.position;if(u!==null){const d=Math.max(0,a.start),m=Math.min(u.count,a.start+a.count);for(let g=d,p=m-1;g<p;g+=c){const _=u.getX(g),v=u.getX(g+1),b=Io(this,e,Ma,l,_,v,g);b&&t.push(b)}if(this.isLineLoop){const g=u.getX(m-1),p=u.getX(d),_=Io(this,e,Ma,l,g,p,m-1);_&&t.push(_)}}else{const d=Math.max(0,a.start),m=Math.min(h.count,a.start+a.count);for(let g=d,p=m-1;g<p;g+=c){const _=Io(this,e,Ma,l,g,g+1,g);_&&t.push(_)}if(this.isLineLoop){const g=Io(this,e,Ma,l,m-1,d,m-1);g&&t.push(g)}}}updateMorphTargets(){const t=this.geometry.morphAttributes,i=Object.keys(t);if(i.length>0){const r=t[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){const o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}}function Io(n,e,t,i,r,s,a){const o=n.geometry.attributes.position;if(_l.fromBufferAttribute(o,r),vl.fromBufferAttribute(o,s),t.distanceSqToSegment(_l,vl,Fc,Cd)>i)return;Fc.applyMatrix4(n.matrixWorld);const c=e.ray.origin.distanceTo(Fc);if(!(c<e.near||c>e.far))return{distance:c,point:Cd.clone().applyMatrix4(n.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:n}}const Pd=new $,Dd=new $;class or extends xl{constructor(e,t){super(e,t),this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,i=[];for(let r=0,s=t.count;r<s;r+=2)Pd.fromBufferAttribute(t,r),Dd.fromBufferAttribute(t,r+1),i[r]=r===0?0:i[r-1],i[r+1]=i[r]+Pd.distanceTo(Dd);e.setAttribute("lineDistance",new pi(i,1))}else Qe("LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}}class Nc extends xl{constructor(e,t){super(e,t),this.isLineLoop=!0,this.type="LineLoop"}}class Nv extends $i{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new ut(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}const Ud=new zt,xh=new Fl,Fo=new Js,No=new $;class Ov extends _n{constructor(e=new Rt,t=new Nv){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}raycast(e,t){const i=this.geometry,r=this.matrixWorld,s=e.params.Points.threshold,a=i.drawRange;if(i.boundingSphere===null&&i.computeBoundingSphere(),Fo.copy(i.boundingSphere),Fo.applyMatrix4(r),Fo.radius+=s,e.ray.intersectsSphere(Fo)===!1)return;Ud.copy(r).invert(),xh.copy(e.ray).applyMatrix4(Ud);const o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=i.index,f=i.attributes.position;if(c!==null){const h=Math.max(0,a.start),d=Math.min(c.count,a.start+a.count);for(let m=h,g=d;m<g;m++){const p=c.getX(m);No.fromBufferAttribute(f,p),Ld(No,p,l,r,e,t,this)}}else{const h=Math.max(0,a.start),d=Math.min(f.count,a.start+a.count);for(let m=h,g=d;m<g;m++)No.fromBufferAttribute(f,m),Ld(No,m,l,r,e,t,this)}}updateMorphTargets(){const t=this.geometry.morphAttributes,i=Object.keys(t);if(i.length>0){const r=t[i[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){const o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}}function Ld(n,e,t,i,r,s,a){const o=xh.distanceSqToPoint(n);if(o<t){const l=new $;xh.closestPointToPoint(n,l),l.applyMatrix4(i);const c=r.ray.origin.distanceTo(l);if(c<r.near||c>r.far)return;s.push({distance:c,distanceToRay:Math.sqrt(o),point:l,index:e,face:null,faceIndex:null,barycoord:null,object:a})}}class qm extends Jt{constructor(e=[],t=$r,i,r,s,a,o,l,c,u){super(e,t,i,r,s,a,o,l,c,u),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class Bv extends Jt{constructor(e,t,i,r,s,a,o,l,c){super(e,t,i,r,s,a,o,l,c),this.isCanvasTexture=!0,this.needsUpdate=!0}}class Xi extends Jt{constructor(e,t,i=Ui,r,s,a,o=hn,l=hn,c,u=qi,f=1){if(u!==qi&&u!==dr)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");const h={width:e,height:t,depth:f};super(h,r,s,a,o,l,u,i,c),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new rf(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){const t=super.toJSON(e);return this.compareFunction!==null&&(t.compareFunction=this.compareFunction),t}}class kv extends Xi{constructor(e,t=Ui,i=$r,r,s,a=hn,o=hn,l,c=qi){const u={width:e,height:e,depth:1},f=[u,u,u,u,u,u];super(e,e,t,i,r,s,a,o,l,c),this.image=f,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}}class Km extends Jt{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class eo extends Rt{constructor(e=1,t=1,i=1,r=1,s=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:i,widthSegments:r,heightSegments:s,depthSegments:a};const o=this;r=Math.floor(r),s=Math.floor(s),a=Math.floor(a);const l=[],c=[],u=[],f=[];let h=0,d=0;m("z","y","x",-1,-1,i,t,e,a,s,0),m("z","y","x",1,-1,i,t,-e,a,s,1),m("x","z","y",1,1,e,i,t,r,a,2),m("x","z","y",1,-1,e,i,-t,r,a,3),m("x","y","z",1,-1,e,t,i,r,s,4),m("x","y","z",-1,-1,e,t,-i,r,s,5),this.setIndex(l),this.setAttribute("position",new pi(c,3)),this.setAttribute("normal",new pi(u,3)),this.setAttribute("uv",new pi(f,2));function m(g,p,_,v,b,S,E,M,T,x,y){const w=S/T,C=E/x,R=S/2,L=E/2,U=M/2,I=T+1,F=x+1;let N=0,Y=0;const j=new $;for(let Z=0;Z<F;Z++){const O=Z*C-L;for(let H=0;H<I;H++){const B=H*w-R;j[g]=B*v,j[p]=O*b,j[_]=U,c.push(j.x,j.y,j.z),j[g]=0,j[p]=0,j[_]=M>0?1:-1,u.push(j.x,j.y,j.z),f.push(H/T),f.push(1-Z/x),N+=1}}for(let Z=0;Z<x;Z++)for(let O=0;O<T;O++){const H=h+O+I*Z,B=h+O+I*(Z+1),V=h+(O+1)+I*(Z+1),G=h+(O+1)+I*Z;l.push(H,B,G),l.push(B,V,G),Y+=6}o.addGroup(d,Y,y),d+=Y,h+=N}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new eo(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}class es extends Rt{constructor(e=1,t=1,i=1,r=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:i,heightSegments:r};const s=e/2,a=t/2,o=Math.floor(i),l=Math.floor(r),c=o+1,u=l+1,f=e/o,h=t/l,d=[],m=[],g=[],p=[];for(let _=0;_<u;_++){const v=_*h-a;for(let b=0;b<c;b++){const S=b*f-s;m.push(S,-v,0),g.push(0,0,1),p.push(b/o),p.push(1-_/l)}}for(let _=0;_<l;_++)for(let v=0;v<o;v++){const b=v+c*_,S=v+c*(_+1),E=v+1+c*(_+1),M=v+1+c*_;d.push(b,S,M),d.push(S,E,M)}this.setIndex(d),this.setAttribute("position",new pi(m,3)),this.setAttribute("normal",new pi(g,3)),this.setAttribute("uv",new pi(p,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new es(e.width,e.height,e.widthSegments,e.heightSegments)}}function Ws(n){const e={};for(const t in n){e[t]={};for(const i in n[t]){const r=n[t][i];if(Id(r))r.isRenderTargetTexture?(Qe("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][i]=null):e[t][i]=r.clone();else if(Array.isArray(r))if(Id(r[0])){const s=[];for(let a=0,o=r.length;a<o;a++)s[a]=r[a].clone();e[t][i]=s}else e[t][i]=r.slice();else e[t][i]=r}}return e}function Mn(n){const e={};for(let t=0;t<n.length;t++){const i=Ws(n[t]);for(const r in i)e[r]=i[r]}return e}function Id(n){return n&&(n.isColor||n.isMatrix3||n.isMatrix4||n.isVector2||n.isVector3||n.isVector4||n.isTexture||n.isQuaternion)}function zv(n){const e=[];for(let t=0;t<n.length;t++)e.push(n[t].clone());return e}function Zm(n){const e=n.getRenderTarget();return e===null?n.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:ft.workingColorSpace}const $m={clone:Ws,merge:Mn};var Gv=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Hv=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class ln extends $i{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=Gv,this.fragmentShader=Hv,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Ws(e.uniforms),this.uniformsGroups=zv(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){const t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(const r in this.uniforms){const a=this.uniforms[r].value;a&&a.isTexture?t.uniforms[r]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[r]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[r]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[r]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[r]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[r]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[r]={type:"m4",value:a.toArray()}:t.uniforms[r]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;const i={};for(const r in this.extensions)this.extensions[r]===!0&&(i[r]=!0);return Object.keys(i).length>0&&(t.extensions=i),t}}class Vv extends ln{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}}class Jm extends $i{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=Qa,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class Qm extends $i{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}const Oo=new $,Bo=new Mr,yi=new $;class e0 extends _n{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new zt,this.projectionMatrix=new zt,this.projectionMatrixInverse=new zt,this.coordinateSystem=Ri,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(Oo,Bo,yi),yi.x===1&&yi.y===1&&yi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Oo,Bo,yi.set(1,1,1)).invert()}updateWorldMatrix(e,t){super.updateWorldMatrix(e,t),this.matrixWorld.decompose(Oo,Bo,yi),yi.x===1&&yi.y===1&&yi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Oo,Bo,yi.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}}const lr=new $,Fd=new Xe,Nd=new Xe;class Hn extends e0{constructor(e=50,t=1,i=.1,r=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=i,this.far=r,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const t=.5*this.getFilmHeight()/e;this.fov=_h*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(el*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return _h*2*Math.atan(Math.tan(el*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,i){lr.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(lr.x,lr.y).multiplyScalar(-e/lr.z),lr.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),i.set(lr.x,lr.y).multiplyScalar(-e/lr.z)}getViewSize(e,t){return this.getViewBounds(e,Fd,Nd),t.subVectors(Nd,Fd)}setViewOffset(e,t,i,r,s,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=i,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let t=e*Math.tan(el*.5*this.fov)/this.zoom,i=2*t,r=this.aspect*i,s=-.5*r;const a=this.view;if(this.view!==null&&this.view.enabled){const l=a.fullWidth,c=a.fullHeight;s+=a.offsetX*r/l,t-=a.offsetY*i/c,r*=a.width/l,i*=a.height/c}const o=this.filmOffset;o!==0&&(s+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(s,s+r,t,t-i,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}}class af extends e0{constructor(e=-1,t=1,i=1,r=-1,s=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=i,this.bottom=r,this.near=s,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,i,r,s,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=i,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),i=(this.right+this.left)/2,r=(this.top+this.bottom)/2;let s=i-e,a=i+e,o=r+t,l=r-t;if(this.view!==null&&this.view.enabled){const c=(this.right-this.left)/this.view.fullWidth/this.zoom,u=(this.top-this.bottom)/this.view.fullHeight/this.zoom;s+=c*this.view.offsetX,a=s+c*this.view.width,o-=u*this.view.offsetY,l=o-u*this.view.height}this.projectionMatrix.makeOrthographic(s,a,o,l,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}}class Wv extends Rt{constructor(){super(),this.isInstancedBufferGeometry=!0,this.type="InstancedBufferGeometry",this.instanceCount=1/0}copy(e){return super.copy(e),this.instanceCount=e.instanceCount,this}toJSON(){const e=super.toJSON();return e.instanceCount=this.instanceCount,e.isInstancedBufferGeometry=!0,e}}const Ts=-90,Es=1;class Xv extends _n{constructor(e,t,i){super(),this.type="CubeCamera",this.renderTarget=i,this.coordinateSystem=null,this.activeMipmapLevel=0;const r=new Hn(Ts,Es,e,t);r.layers=this.layers,this.add(r);const s=new Hn(Ts,Es,e,t);s.layers=this.layers,this.add(s);const a=new Hn(Ts,Es,e,t);a.layers=this.layers,this.add(a);const o=new Hn(Ts,Es,e,t);o.layers=this.layers,this.add(o);const l=new Hn(Ts,Es,e,t);l.layers=this.layers,this.add(l);const c=new Hn(Ts,Es,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){const e=this.coordinateSystem,t=this.children.concat(),[i,r,s,a,o,l]=t;for(const c of t)this.remove(c);if(e===Ri)i.up.set(0,1,0),i.lookAt(1,0,0),r.up.set(0,1,0),r.lookAt(-1,0,0),s.up.set(0,0,-1),s.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===dl)i.up.set(0,-1,0),i.lookAt(-1,0,0),r.up.set(0,-1,0),r.lookAt(1,0,0),s.up.set(0,0,1),s.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const c of t)this.add(c),c.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();const{renderTarget:i,activeMipmapLevel:r}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[s,a,o,l,c,u]=this.children,f=e.getRenderTarget(),h=e.getActiveCubeFace(),d=e.getActiveMipmapLevel(),m=e.xr.enabled;e.xr.enabled=!1;const g=i.texture.generateMipmaps;i.texture.generateMipmaps=!1;let p=!1;e.isWebGLRenderer===!0?p=e.state.buffers.depth.getReversed():p=e.reversedDepthBuffer,e.setRenderTarget(i,0,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,s),e.setRenderTarget(i,1,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,a),e.setRenderTarget(i,2,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,o),e.setRenderTarget(i,3,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,l),e.setRenderTarget(i,4,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,c),i.texture.generateMipmaps=g,e.setRenderTarget(i,5,r),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,u),e.setRenderTarget(f,h,d),e.xr.enabled=m,i.texture.needsPMREMUpdate=!0}}class jv extends Hn{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}class vt{constructor(e){this.value=e}clone(){return new vt(this.value.clone===void 0?this.value:this.value.clone())}}class Yv{constructor(e=!0){this.autoStart=e,this.startTime=0,this.oldTime=0,this.elapsedTime=0,this.running=!1,Qe("Clock: This module has been deprecated. Please use THREE.Timer instead.")}start(){this.startTime=performance.now(),this.oldTime=this.startTime,this.elapsedTime=0,this.running=!0}stop(){this.getElapsedTime(),this.running=!1,this.autoStart=!1}getElapsedTime(){return this.getDelta(),this.elapsedTime}getDelta(){let e=0;if(this.autoStart&&!this.running)return this.start(),0;if(this.running){const t=performance.now();e=(t-this.oldTime)/1e3,this.oldTime=t,this.elapsedTime+=e}return e}}class Od{constructor(e=1,t=0,i=0){this.radius=e,this.phi=t,this.theta=i}set(e,t,i){return this.radius=e,this.phi=t,this.theta=i,this}copy(e){return this.radius=e.radius,this.phi=e.phi,this.theta=e.theta,this}makeSafe(){return this.phi=lt(this.phi,1e-6,Math.PI-1e-6),this}setFromVector3(e){return this.setFromCartesianCoords(e.x,e.y,e.z)}setFromCartesianCoords(e,t,i){return this.radius=Math.sqrt(e*e+t*t+i*i),this.radius===0?(this.theta=0,this.phi=0):(this.theta=Math.atan2(e,i),this.phi=Math.acos(lt(t/this.radius,-1,1))),this}clone(){return new this.constructor().copy(this)}}const Hf=class Hf{constructor(e,t,i,r){this.elements=[1,0,0,1],e!==void 0&&this.set(e,t,i,r)}identity(){return this.set(1,0,0,1),this}fromArray(e,t=0){for(let i=0;i<4;i++)this.elements[i]=e[i+t];return this}set(e,t,i,r){const s=this.elements;return s[0]=e,s[2]=t,s[1]=i,s[3]=r,this}};Hf.prototype.isMatrix2=!0;let Bd=Hf;class qv extends mi{constructor(e,t=null){super(),this.object=e,this.domElement=t,this.enabled=!0,this.state=-1,this.keys={},this.mouseButtons={LEFT:null,MIDDLE:null,RIGHT:null},this.touches={ONE:null,TWO:null}}connect(e){if(e===void 0){Qe("Controls: connect() now requires an element.");return}this.domElement!==null&&this.disconnect(),this.domElement=e}disconnect(){}dispose(){}update(){}}function kd(n,e,t,i){const r=Kv(i);switch(t){case Om:return n*e;case km:return n*e/r.components*r.byteLength;case Jh:return n*e/r.components*r.byteLength;case Jr:return n*e*2/r.components*r.byteLength;case Qh:return n*e*2/r.components*r.byteLength;case Bm:return n*e*3/r.components*r.byteLength;case di:return n*e*4/r.components*r.byteLength;case ef:return n*e*4/r.components*r.byteLength;case Zo:case $o:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*8;case Jo:case Qo:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case zu:case Hu:return Math.max(n,16)*Math.max(e,8)/4;case ku:case Gu:return Math.max(n,8)*Math.max(e,8)/2;case Vu:case Wu:case ju:case Yu:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*8;case Xu:case ul:case qu:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case Ku:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case Zu:return Math.floor((n+4)/5)*Math.floor((e+3)/4)*16;case $u:return Math.floor((n+4)/5)*Math.floor((e+4)/5)*16;case Ju:return Math.floor((n+5)/6)*Math.floor((e+4)/5)*16;case Qu:return Math.floor((n+5)/6)*Math.floor((e+5)/6)*16;case eh:return Math.floor((n+7)/8)*Math.floor((e+4)/5)*16;case th:return Math.floor((n+7)/8)*Math.floor((e+5)/6)*16;case nh:return Math.floor((n+7)/8)*Math.floor((e+7)/8)*16;case ih:return Math.floor((n+9)/10)*Math.floor((e+4)/5)*16;case rh:return Math.floor((n+9)/10)*Math.floor((e+5)/6)*16;case sh:return Math.floor((n+9)/10)*Math.floor((e+7)/8)*16;case ah:return Math.floor((n+9)/10)*Math.floor((e+9)/10)*16;case oh:return Math.floor((n+11)/12)*Math.floor((e+9)/10)*16;case lh:return Math.floor((n+11)/12)*Math.floor((e+11)/12)*16;case ch:case uh:case hh:return Math.ceil(n/4)*Math.ceil(e/4)*16;case fh:case dh:return Math.ceil(n/4)*Math.ceil(e/4)*8;case hl:case ph:return Math.ceil(n/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function Kv(n){switch(n){case Yt:case Lm:return{byteLength:1,components:1};case Ha:case Im:case Yi:return{byteLength:2,components:1};case Zh:case $h:return{byteLength:2,components:4};case Ui:case Kh:case fi:return{byteLength:4,components:1};case Fm:case Nm:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${n}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:Ja}}));typeof window<"u"&&(window.__THREE__?Qe("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=Ja);/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */function t0(){let n=null,e=!1,t=null,i=null;function r(s,a){t(s,a),i=n.requestAnimationFrame(r)}return{start:function(){e!==!0&&t!==null&&n!==null&&(i=n.requestAnimationFrame(r),e=!0)},stop:function(){n!==null&&n.cancelAnimationFrame(i),e=!1},setAnimationLoop:function(s){t=s},setContext:function(s){n=s}}}function Zv(n){const e=new WeakMap;function t(o,l){const c=o.array,u=o.usage,f=c.byteLength,h=n.createBuffer();n.bindBuffer(l,h),n.bufferData(l,c,u),o.onUploadCallback();let d;if(c instanceof Float32Array)d=n.FLOAT;else if(typeof Float16Array<"u"&&c instanceof Float16Array)d=n.HALF_FLOAT;else if(c instanceof Uint16Array)o.isFloat16BufferAttribute?d=n.HALF_FLOAT:d=n.UNSIGNED_SHORT;else if(c instanceof Int16Array)d=n.SHORT;else if(c instanceof Uint32Array)d=n.UNSIGNED_INT;else if(c instanceof Int32Array)d=n.INT;else if(c instanceof Int8Array)d=n.BYTE;else if(c instanceof Uint8Array)d=n.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)d=n.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:h,type:d,bytesPerElement:c.BYTES_PER_ELEMENT,version:o.version,size:f}}function i(o,l,c){const u=l.array,f=l.updateRanges;if(n.bindBuffer(c,o),f.length===0)n.bufferSubData(c,0,u);else{f.sort((d,m)=>d.start-m.start);let h=0;for(let d=1;d<f.length;d++){const m=f[h],g=f[d];g.start<=m.start+m.count+1?m.count=Math.max(m.count,g.start+g.count-m.start):(++h,f[h]=g)}f.length=h+1;for(let d=0,m=f.length;d<m;d++){const g=f[d];n.bufferSubData(c,g.start*u.BYTES_PER_ELEMENT,u,g.start,g.count)}l.clearUpdateRanges()}l.onUploadCallback()}function r(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function s(o){o.isInterleavedBufferAttribute&&(o=o.data);const l=e.get(o);l&&(n.deleteBuffer(l.buffer),e.delete(o))}function a(o,l){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){const u=e.get(o);(!u||u.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}const c=e.get(o);if(c===void 0)e.set(o,t(o,l));else if(c.version<o.version){if(c.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");i(c.buffer,o,l),c.version=o.version}}return{get:r,remove:s,update:a}}var $v=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,Jv=`#ifdef USE_ALPHAHASH
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
#endif`,Qv=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,ex=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,tx=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,nx=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,ix=`#ifdef USE_AOMAP
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
#endif`,rx=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,sx=`#ifdef USE_BATCHING
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
#endif`,ax=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,ox=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,lx=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,cx=`float G_BlinnPhong_Implicit( ) {
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
} // validated`,ux=`#ifdef USE_IRIDESCENCE
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
#endif`,hx=`#ifdef USE_BUMPMAP
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
#endif`,fx=`#if NUM_CLIPPING_PLANES > 0
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
#endif`,dx=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,px=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,mx=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,gx=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,_x=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,vx=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,xx=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
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
#endif`,yx=`#define PI 3.141592653589793
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
} // validated`,bx=`#ifdef ENVMAP_TYPE_CUBE_UV
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
#endif`,Mx=`vec3 transformedNormal = objectNormal;
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
#endif`,Sx=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,Tx=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,Ex=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,wx=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,Ax="gl_FragColor = linearToOutputTexel( gl_FragColor );",Rx=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,Cx=`#ifdef USE_ENVMAP
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
#endif`,Px=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,Dx=`#ifdef USE_ENVMAP
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
#endif`,Ux=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,Lx=`#ifdef USE_ENVMAP
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
#endif`,Ix=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,Fx=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,Nx=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,Ox=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,Bx=`#ifdef USE_GRADIENTMAP
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
}`,kx=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,zx=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,Gx=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,Hx=`uniform bool receiveShadow;
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
#include <lightprobes_pars_fragment>`,Vx=`#ifdef USE_ENVMAP
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
#endif`,Wx=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,Xx=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,jx=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,Yx=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,qx=`PhysicalMaterial material;
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
#endif`,Kx=`uniform sampler2D dfgLUT;
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
}`,Zx=`
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
#endif`,$x=`#if defined( RE_IndirectDiffuse )
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
#endif`,Jx=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,Qx=`#ifdef USE_LIGHT_PROBES_GRID
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
#endif`,e1=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,t1=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,n1=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,i1=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,r1=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,s1=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,a1=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
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
#endif`,o1=`#if defined( USE_POINTS_UV )
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
#endif`,l1=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,c1=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,u1=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,h1=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,f1=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,d1=`#ifdef USE_MORPHTARGETS
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
#endif`,p1=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,m1=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
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
vec3 nonPerturbedNormal = normal;`,g1=`#ifdef USE_NORMALMAP_OBJECTSPACE
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
#endif`,_1=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,v1=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,x1=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,y1=`#ifdef USE_NORMALMAP
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
#endif`,b1=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,M1=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,S1=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,T1=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,E1=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,w1=`vec3 packNormalToRGB( const in vec3 normal ) {
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
}`,A1=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,R1=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,C1=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,P1=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,D1=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,U1=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,L1=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,I1=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,F1=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
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
#endif`,N1=`float getShadowMask() {
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
}`,O1=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,B1=`#ifdef USE_SKINNING
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
#endif`,k1=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,z1=`#ifdef USE_SKINNING
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
#endif`,G1=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,H1=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,V1=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,W1=`#ifndef saturate
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
vec3 CustomToneMapping( vec3 color ) { return color; }`,X1=`#ifdef USE_TRANSMISSION
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
#endif`,j1=`#ifdef USE_TRANSMISSION
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
#endif`,Y1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,q1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,K1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,Z1=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;const $1=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,J1=`uniform sampler2D t2D;
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
}`,Q1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,ey=`#ifdef ENVMAP_TYPE_CUBE
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
}`,ty=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,ny=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,iy=`#include <common>
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
}`,ry=`#if DEPTH_PACKING == 3200
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
}`,sy=`#define DISTANCE
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
}`,ay=`#define DISTANCE
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
}`,oy=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,ly=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,cy=`uniform float scale;
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
}`,uy=`uniform vec3 diffuse;
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
}`,hy=`#include <common>
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
}`,fy=`uniform vec3 diffuse;
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
}`,dy=`#define LAMBERT
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
}`,py=`#define LAMBERT
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
}`,my=`#define MATCAP
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
}`,gy=`#define MATCAP
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
}`,_y=`#define NORMAL
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
}`,vy=`#define NORMAL
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
}`,xy=`#define PHONG
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
}`,yy=`#define PHONG
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
}`,by=`#define STANDARD
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
}`,My=`#define STANDARD
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
}`,Sy=`#define TOON
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
}`,Ty=`#define TOON
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
}`,Ey=`uniform float size;
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
}`,wy=`uniform vec3 diffuse;
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
}`,Ay=`#include <common>
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
}`,Ry=`uniform vec3 color;
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
}`,Cy=`uniform float rotation;
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
}`,Py=`uniform vec3 diffuse;
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
}`,st={alphahash_fragment:$v,alphahash_pars_fragment:Jv,alphamap_fragment:Qv,alphamap_pars_fragment:ex,alphatest_fragment:tx,alphatest_pars_fragment:nx,aomap_fragment:ix,aomap_pars_fragment:rx,batching_pars_vertex:sx,batching_vertex:ax,begin_vertex:ox,beginnormal_vertex:lx,bsdfs:cx,iridescence_fragment:ux,bumpmap_pars_fragment:hx,clipping_planes_fragment:fx,clipping_planes_pars_fragment:dx,clipping_planes_pars_vertex:px,clipping_planes_vertex:mx,color_fragment:gx,color_pars_fragment:_x,color_pars_vertex:vx,color_vertex:xx,common:yx,cube_uv_reflection_fragment:bx,defaultnormal_vertex:Mx,displacementmap_pars_vertex:Sx,displacementmap_vertex:Tx,emissivemap_fragment:Ex,emissivemap_pars_fragment:wx,colorspace_fragment:Ax,colorspace_pars_fragment:Rx,envmap_fragment:Cx,envmap_common_pars_fragment:Px,envmap_pars_fragment:Dx,envmap_pars_vertex:Ux,envmap_physical_pars_fragment:Vx,envmap_vertex:Lx,fog_vertex:Ix,fog_pars_vertex:Fx,fog_fragment:Nx,fog_pars_fragment:Ox,gradientmap_pars_fragment:Bx,lightmap_pars_fragment:kx,lights_lambert_fragment:zx,lights_lambert_pars_fragment:Gx,lights_pars_begin:Hx,lights_toon_fragment:Wx,lights_toon_pars_fragment:Xx,lights_phong_fragment:jx,lights_phong_pars_fragment:Yx,lights_physical_fragment:qx,lights_physical_pars_fragment:Kx,lights_fragment_begin:Zx,lights_fragment_maps:$x,lights_fragment_end:Jx,lightprobes_pars_fragment:Qx,logdepthbuf_fragment:e1,logdepthbuf_pars_fragment:t1,logdepthbuf_pars_vertex:n1,logdepthbuf_vertex:i1,map_fragment:r1,map_pars_fragment:s1,map_particle_fragment:a1,map_particle_pars_fragment:o1,metalnessmap_fragment:l1,metalnessmap_pars_fragment:c1,morphinstance_vertex:u1,morphcolor_vertex:h1,morphnormal_vertex:f1,morphtarget_pars_vertex:d1,morphtarget_vertex:p1,normal_fragment_begin:m1,normal_fragment_maps:g1,normal_pars_fragment:_1,normal_pars_vertex:v1,normal_vertex:x1,normalmap_pars_fragment:y1,clearcoat_normal_fragment_begin:b1,clearcoat_normal_fragment_maps:M1,clearcoat_pars_fragment:S1,iridescence_pars_fragment:T1,opaque_fragment:E1,packing:w1,premultiplied_alpha_fragment:A1,project_vertex:R1,dithering_fragment:C1,dithering_pars_fragment:P1,roughnessmap_fragment:D1,roughnessmap_pars_fragment:U1,shadowmap_pars_fragment:L1,shadowmap_pars_vertex:I1,shadowmap_vertex:F1,shadowmask_pars_fragment:N1,skinbase_vertex:O1,skinning_pars_vertex:B1,skinning_vertex:k1,skinnormal_vertex:z1,specularmap_fragment:G1,specularmap_pars_fragment:H1,tonemapping_fragment:V1,tonemapping_pars_fragment:W1,transmission_fragment:X1,transmission_pars_fragment:j1,uv_pars_fragment:Y1,uv_pars_vertex:q1,uv_vertex:K1,worldpos_vertex:Z1,background_vert:$1,background_frag:J1,backgroundCube_vert:Q1,backgroundCube_frag:ey,cube_vert:ty,cube_frag:ny,depth_vert:iy,depth_frag:ry,distance_vert:sy,distance_frag:ay,equirect_vert:oy,equirect_frag:ly,linedashed_vert:cy,linedashed_frag:uy,meshbasic_vert:hy,meshbasic_frag:fy,meshlambert_vert:dy,meshlambert_frag:py,meshmatcap_vert:my,meshmatcap_frag:gy,meshnormal_vert:_y,meshnormal_frag:vy,meshphong_vert:xy,meshphong_frag:yy,meshphysical_vert:by,meshphysical_frag:My,meshtoon_vert:Sy,meshtoon_frag:Ty,points_vert:Ey,points_frag:wy,shadow_vert:Ay,shadow_frag:Ry,sprite_vert:Cy,sprite_frag:Py},Ge={common:{diffuse:{value:new ut(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new rt},alphaMap:{value:null},alphaMapTransform:{value:new rt},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new rt}},envmap:{envMap:{value:null},envMapRotation:{value:new rt},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new rt}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new rt}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new rt},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new rt},normalScale:{value:new Xe(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new rt},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new rt}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new rt}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new rt}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new ut(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new $},probesMax:{value:new $},probesResolution:{value:new $}},points:{diffuse:{value:new ut(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new rt},alphaTest:{value:0},uvTransform:{value:new rt}},sprite:{diffuse:{value:new ut(16777215)},opacity:{value:1},center:{value:new Xe(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new rt},alphaMap:{value:null},alphaMapTransform:{value:new rt},alphaTest:{value:0}}},Si={basic:{uniforms:Mn([Ge.common,Ge.specularmap,Ge.envmap,Ge.aomap,Ge.lightmap,Ge.fog]),vertexShader:st.meshbasic_vert,fragmentShader:st.meshbasic_frag},lambert:{uniforms:Mn([Ge.common,Ge.specularmap,Ge.envmap,Ge.aomap,Ge.lightmap,Ge.emissivemap,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.fog,Ge.lights,{emissive:{value:new ut(0)},envMapIntensity:{value:1}}]),vertexShader:st.meshlambert_vert,fragmentShader:st.meshlambert_frag},phong:{uniforms:Mn([Ge.common,Ge.specularmap,Ge.envmap,Ge.aomap,Ge.lightmap,Ge.emissivemap,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.fog,Ge.lights,{emissive:{value:new ut(0)},specular:{value:new ut(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:st.meshphong_vert,fragmentShader:st.meshphong_frag},standard:{uniforms:Mn([Ge.common,Ge.envmap,Ge.aomap,Ge.lightmap,Ge.emissivemap,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.roughnessmap,Ge.metalnessmap,Ge.fog,Ge.lights,{emissive:{value:new ut(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:st.meshphysical_vert,fragmentShader:st.meshphysical_frag},toon:{uniforms:Mn([Ge.common,Ge.aomap,Ge.lightmap,Ge.emissivemap,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.gradientmap,Ge.fog,Ge.lights,{emissive:{value:new ut(0)}}]),vertexShader:st.meshtoon_vert,fragmentShader:st.meshtoon_frag},matcap:{uniforms:Mn([Ge.common,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,Ge.fog,{matcap:{value:null}}]),vertexShader:st.meshmatcap_vert,fragmentShader:st.meshmatcap_frag},points:{uniforms:Mn([Ge.points,Ge.fog]),vertexShader:st.points_vert,fragmentShader:st.points_frag},dashed:{uniforms:Mn([Ge.common,Ge.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:st.linedashed_vert,fragmentShader:st.linedashed_frag},depth:{uniforms:Mn([Ge.common,Ge.displacementmap]),vertexShader:st.depth_vert,fragmentShader:st.depth_frag},normal:{uniforms:Mn([Ge.common,Ge.bumpmap,Ge.normalmap,Ge.displacementmap,{opacity:{value:1}}]),vertexShader:st.meshnormal_vert,fragmentShader:st.meshnormal_frag},sprite:{uniforms:Mn([Ge.sprite,Ge.fog]),vertexShader:st.sprite_vert,fragmentShader:st.sprite_frag},background:{uniforms:{uvTransform:{value:new rt},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:st.background_vert,fragmentShader:st.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new rt}},vertexShader:st.backgroundCube_vert,fragmentShader:st.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:st.cube_vert,fragmentShader:st.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:st.equirect_vert,fragmentShader:st.equirect_frag},distance:{uniforms:Mn([Ge.common,Ge.displacementmap,{referencePosition:{value:new $},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:st.distance_vert,fragmentShader:st.distance_frag},shadow:{uniforms:Mn([Ge.lights,Ge.fog,{color:{value:new ut(0)},opacity:{value:1}}]),vertexShader:st.shadow_vert,fragmentShader:st.shadow_frag}};Si.physical={uniforms:Mn([Si.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new rt},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new rt},clearcoatNormalScale:{value:new Xe(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new rt},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new rt},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new rt},sheen:{value:0},sheenColor:{value:new ut(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new rt},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new rt},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new rt},transmissionSamplerSize:{value:new Xe},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new rt},attenuationDistance:{value:0},attenuationColor:{value:new ut(0)},specularColor:{value:new ut(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new rt},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new rt},anisotropyVector:{value:new Xe},anisotropyMap:{value:null},anisotropyMapTransform:{value:new rt}}]),vertexShader:st.meshphysical_vert,fragmentShader:st.meshphysical_frag};const ko={r:0,b:0,g:0},Dy=new zt,n0=new rt;n0.set(-1,0,0,0,1,0,0,0,1);function Uy(n,e,t,i,r,s){const a=new ut(0);let o=r===!0?0:1,l,c,u=null,f=0,h=null;function d(v){let b=v.isScene===!0?v.background:null;if(b&&b.isTexture){const S=v.backgroundBlurriness>0;b=e.get(b,S)}return b}function m(v){let b=!1;const S=d(v);S===null?p(a,o):S&&S.isColor&&(p(S,1),b=!0);const E=n.xr.getEnvironmentBlendMode();E==="additive"?t.buffers.color.setClear(0,0,0,1,s):E==="alpha-blend"&&t.buffers.color.setClear(0,0,0,0,s),(n.autoClear||b)&&(t.buffers.depth.setTest(!0),t.buffers.depth.setMask(!0),t.buffers.color.setMask(!0),n.clear(n.autoClearColor,n.autoClearDepth,n.autoClearStencil))}function g(v,b){const S=d(b);S&&(S.isCubeTexture||S.mapping===Il)?(c===void 0&&(c=new Yn(new eo(1,1,1),new ln({name:"BackgroundCubeMaterial",uniforms:Ws(Si.backgroundCube.uniforms),vertexShader:Si.backgroundCube.vertexShader,fragmentShader:Si.backgroundCube.fragmentShader,side:on,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),c.geometry.deleteAttribute("uv"),c.onBeforeRender=function(E,M,T){this.matrixWorld.copyPosition(T.matrixWorld)},Object.defineProperty(c.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),i.update(c)),c.material.uniforms.envMap.value=S,c.material.uniforms.backgroundBlurriness.value=b.backgroundBlurriness,c.material.uniforms.backgroundIntensity.value=b.backgroundIntensity,c.material.uniforms.backgroundRotation.value.setFromMatrix4(Dy.makeRotationFromEuler(b.backgroundRotation)).transpose(),S.isCubeTexture&&S.isRenderTargetTexture===!1&&c.material.uniforms.backgroundRotation.value.premultiply(n0),c.material.toneMapped=ft.getTransfer(S.colorSpace)!==bt,(u!==S||f!==S.version||h!==n.toneMapping)&&(c.material.needsUpdate=!0,u=S,f=S.version,h=n.toneMapping),c.layers.enableAll(),v.unshift(c,c.geometry,c.material,0,0,null)):S&&S.isTexture&&(l===void 0&&(l=new Yn(new es(2,2),new ln({name:"BackgroundMaterial",uniforms:Ws(Si.background.uniforms),vertexShader:Si.background.vertexShader,fragmentShader:Si.background.fragmentShader,side:ji,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),i.update(l)),l.material.uniforms.t2D.value=S,l.material.uniforms.backgroundIntensity.value=b.backgroundIntensity,l.material.toneMapped=ft.getTransfer(S.colorSpace)!==bt,S.matrixAutoUpdate===!0&&S.updateMatrix(),l.material.uniforms.uvTransform.value.copy(S.matrix),(u!==S||f!==S.version||h!==n.toneMapping)&&(l.material.needsUpdate=!0,u=S,f=S.version,h=n.toneMapping),l.layers.enableAll(),v.unshift(l,l.geometry,l.material,0,0,null))}function p(v,b){v.getRGB(ko,Zm(n)),t.buffers.color.setClear(ko.r,ko.g,ko.b,b,s)}function _(){c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return a},setClearColor:function(v,b=1){a.set(v),o=b,p(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(v){o=v,p(a,o)},render:m,addToRenderList:g,dispose:_}}function Ly(n,e){const t=n.getParameter(n.MAX_VERTEX_ATTRIBS),i={},r=h(null);let s=r,a=!1;function o(C,R,L,U,I){let F=!1;const N=f(C,U,L,R);s!==N&&(s=N,c(s.object)),F=d(C,U,L,I),F&&m(C,U,L,I),I!==null&&e.update(I,n.ELEMENT_ARRAY_BUFFER),(F||a)&&(a=!1,S(C,R,L,U),I!==null&&n.bindBuffer(n.ELEMENT_ARRAY_BUFFER,e.get(I).buffer))}function l(){return n.createVertexArray()}function c(C){return n.bindVertexArray(C)}function u(C){return n.deleteVertexArray(C)}function f(C,R,L,U){const I=U.wireframe===!0;let F=i[R.id];F===void 0&&(F={},i[R.id]=F);const N=C.isInstancedMesh===!0?C.id:0;let Y=F[N];Y===void 0&&(Y={},F[N]=Y);let j=Y[L.id];j===void 0&&(j={},Y[L.id]=j);let Z=j[I];return Z===void 0&&(Z=h(l()),j[I]=Z),Z}function h(C){const R=[],L=[],U=[];for(let I=0;I<t;I++)R[I]=0,L[I]=0,U[I]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:R,enabledAttributes:L,attributeDivisors:U,object:C,attributes:{},index:null}}function d(C,R,L,U){const I=s.attributes,F=R.attributes;let N=0;const Y=L.getAttributes();for(const j in Y)if(Y[j].location>=0){const O=I[j];let H=F[j];if(H===void 0&&(j==="instanceMatrix"&&C.instanceMatrix&&(H=C.instanceMatrix),j==="instanceColor"&&C.instanceColor&&(H=C.instanceColor)),O===void 0||O.attribute!==H||H&&O.data!==H.data)return!0;N++}return s.attributesNum!==N||s.index!==U}function m(C,R,L,U){const I={},F=R.attributes;let N=0;const Y=L.getAttributes();for(const j in Y)if(Y[j].location>=0){let O=F[j];O===void 0&&(j==="instanceMatrix"&&C.instanceMatrix&&(O=C.instanceMatrix),j==="instanceColor"&&C.instanceColor&&(O=C.instanceColor));const H={};H.attribute=O,O&&O.data&&(H.data=O.data),I[j]=H,N++}s.attributes=I,s.attributesNum=N,s.index=U}function g(){const C=s.newAttributes;for(let R=0,L=C.length;R<L;R++)C[R]=0}function p(C){_(C,0)}function _(C,R){const L=s.newAttributes,U=s.enabledAttributes,I=s.attributeDivisors;L[C]=1,U[C]===0&&(n.enableVertexAttribArray(C),U[C]=1),I[C]!==R&&(n.vertexAttribDivisor(C,R),I[C]=R)}function v(){const C=s.newAttributes,R=s.enabledAttributes;for(let L=0,U=R.length;L<U;L++)R[L]!==C[L]&&(n.disableVertexAttribArray(L),R[L]=0)}function b(C,R,L,U,I,F,N){N===!0?n.vertexAttribIPointer(C,R,L,I,F):n.vertexAttribPointer(C,R,L,U,I,F)}function S(C,R,L,U){g();const I=U.attributes,F=L.getAttributes(),N=R.defaultAttributeValues;for(const Y in F){const j=F[Y];if(j.location>=0){let Z=I[Y];if(Z===void 0&&(Y==="instanceMatrix"&&C.instanceMatrix&&(Z=C.instanceMatrix),Y==="instanceColor"&&C.instanceColor&&(Z=C.instanceColor)),Z!==void 0){const O=Z.normalized,H=Z.itemSize,B=e.get(Z);if(B===void 0)continue;const V=B.buffer,G=B.type,z=B.bytesPerElement,W=G===n.INT||G===n.UNSIGNED_INT||Z.gpuType===Kh;if(Z.isInterleavedBufferAttribute){const q=Z.data,ce=q.stride,me=Z.offset;if(q.isInstancedInterleavedBuffer){for(let Q=0;Q<j.locationSize;Q++)_(j.location+Q,q.meshPerAttribute);C.isInstancedMesh!==!0&&U._maxInstanceCount===void 0&&(U._maxInstanceCount=q.meshPerAttribute*q.count)}else for(let Q=0;Q<j.locationSize;Q++)p(j.location+Q);n.bindBuffer(n.ARRAY_BUFFER,V);for(let Q=0;Q<j.locationSize;Q++)b(j.location+Q,H/j.locationSize,G,O,ce*z,(me+H/j.locationSize*Q)*z,W)}else{if(Z.isInstancedBufferAttribute){for(let q=0;q<j.locationSize;q++)_(j.location+q,Z.meshPerAttribute);C.isInstancedMesh!==!0&&U._maxInstanceCount===void 0&&(U._maxInstanceCount=Z.meshPerAttribute*Z.count)}else for(let q=0;q<j.locationSize;q++)p(j.location+q);n.bindBuffer(n.ARRAY_BUFFER,V);for(let q=0;q<j.locationSize;q++)b(j.location+q,H/j.locationSize,G,O,H*z,H/j.locationSize*q*z,W)}}else if(N!==void 0){const O=N[Y];if(O!==void 0)switch(O.length){case 2:n.vertexAttrib2fv(j.location,O);break;case 3:n.vertexAttrib3fv(j.location,O);break;case 4:n.vertexAttrib4fv(j.location,O);break;default:n.vertexAttrib1fv(j.location,O)}}}}v()}function E(){y();for(const C in i){const R=i[C];for(const L in R){const U=R[L];for(const I in U){const F=U[I];for(const N in F)u(F[N].object),delete F[N];delete U[I]}}delete i[C]}}function M(C){if(i[C.id]===void 0)return;const R=i[C.id];for(const L in R){const U=R[L];for(const I in U){const F=U[I];for(const N in F)u(F[N].object),delete F[N];delete U[I]}}delete i[C.id]}function T(C){for(const R in i){const L=i[R];for(const U in L){const I=L[U];if(I[C.id]===void 0)continue;const F=I[C.id];for(const N in F)u(F[N].object),delete F[N];delete I[C.id]}}}function x(C){for(const R in i){const L=i[R],U=C.isInstancedMesh===!0?C.id:0,I=L[U];if(I!==void 0){for(const F in I){const N=I[F];for(const Y in N)u(N[Y].object),delete N[Y];delete I[F]}delete L[U],Object.keys(L).length===0&&delete i[R]}}}function y(){w(),a=!0,s!==r&&(s=r,c(s.object))}function w(){r.geometry=null,r.program=null,r.wireframe=!1}return{setup:o,reset:y,resetDefaultState:w,dispose:E,releaseStatesOfGeometry:M,releaseStatesOfObject:x,releaseStatesOfProgram:T,initAttributes:g,enableAttribute:p,disableUnusedAttributes:v}}function Iy(n,e,t){let i;function r(l){i=l}function s(l,c){n.drawArrays(i,l,c),t.update(c,i,1)}function a(l,c,u){u!==0&&(n.drawArraysInstanced(i,l,c,u),t.update(c,i,u))}function o(l,c,u){if(u===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(i,l,0,c,0,u);let h=0;for(let d=0;d<u;d++)h+=c[d];t.update(h,i,1)}this.setMode=r,this.render=s,this.renderInstances=a,this.renderMultiDraw=o}function Fy(n,e,t,i){let r;function s(){if(r!==void 0)return r;if(e.has("EXT_texture_filter_anisotropic")===!0){const T=e.get("EXT_texture_filter_anisotropic");r=n.getParameter(T.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else r=0;return r}function a(T){return!(T!==di&&i.convert(T)!==n.getParameter(n.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(T){const x=T===Yi&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(T!==Yt&&i.convert(T)!==n.getParameter(n.IMPLEMENTATION_COLOR_READ_TYPE)&&T!==fi&&!x)}function l(T){if(T==="highp"){if(n.getShaderPrecisionFormat(n.VERTEX_SHADER,n.HIGH_FLOAT).precision>0&&n.getShaderPrecisionFormat(n.FRAGMENT_SHADER,n.HIGH_FLOAT).precision>0)return"highp";T="mediump"}return T==="mediump"&&n.getShaderPrecisionFormat(n.VERTEX_SHADER,n.MEDIUM_FLOAT).precision>0&&n.getShaderPrecisionFormat(n.FRAGMENT_SHADER,n.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=t.precision!==void 0?t.precision:"highp";const u=l(c);u!==c&&(Qe("WebGLRenderer:",c,"not supported, using",u,"instead."),c=u);const f=t.logarithmicDepthBuffer===!0,h=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control");t.reversedDepthBuffer===!0&&h===!1&&Qe("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");const d=n.getParameter(n.MAX_TEXTURE_IMAGE_UNITS),m=n.getParameter(n.MAX_VERTEX_TEXTURE_IMAGE_UNITS),g=n.getParameter(n.MAX_TEXTURE_SIZE),p=n.getParameter(n.MAX_CUBE_MAP_TEXTURE_SIZE),_=n.getParameter(n.MAX_VERTEX_ATTRIBS),v=n.getParameter(n.MAX_VERTEX_UNIFORM_VECTORS),b=n.getParameter(n.MAX_VARYING_VECTORS),S=n.getParameter(n.MAX_FRAGMENT_UNIFORM_VECTORS),E=n.getParameter(n.MAX_SAMPLES),M=n.getParameter(n.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:s,getMaxPrecision:l,textureFormatReadable:a,textureTypeReadable:o,precision:c,logarithmicDepthBuffer:f,reversedDepthBuffer:h,maxTextures:d,maxVertexTextures:m,maxTextureSize:g,maxCubemapSize:p,maxAttributes:_,maxVertexUniforms:v,maxVaryings:b,maxFragmentUniforms:S,maxSamples:E,samples:M}}function Ny(n){const e=this;let t=null,i=0,r=!1,s=!1;const a=new hr,o=new rt,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(f,h){const d=f.length!==0||h||i!==0||r;return r=h,i=f.length,d},this.beginShadows=function(){s=!0,u(null)},this.endShadows=function(){s=!1},this.setGlobalState=function(f,h){t=u(f,h,0)},this.setState=function(f,h,d){const m=f.clippingPlanes,g=f.clipIntersection,p=f.clipShadows,_=n.get(f);if(!r||m===null||m.length===0||s&&!p)s?u(null):c();else{const v=s?0:i,b=v*4;let S=_.clippingState||null;l.value=S,S=u(m,h,b,d);for(let E=0;E!==b;++E)S[E]=t[E];_.clippingState=S,this.numIntersection=g?this.numPlanes:0,this.numPlanes+=v}};function c(){l.value!==t&&(l.value=t,l.needsUpdate=i>0),e.numPlanes=i,e.numIntersection=0}function u(f,h,d,m){const g=f!==null?f.length:0;let p=null;if(g!==0){if(p=l.value,m!==!0||p===null){const _=d+g*4,v=h.matrixWorldInverse;o.getNormalMatrix(v),(p===null||p.length<_)&&(p=new Float32Array(_));for(let b=0,S=d;b!==g;++b,S+=4)a.copy(f[b]).applyMatrix4(v,o),a.normal.toArray(p,S),p[S+3]=a.constant}l.value=p,l.needsUpdate=!0}return e.numPlanes=g,e.numIntersection=0,p}}const pr=4,zd=[.125,.215,.35,.446,.526,.582],zr=20,Oy=256,Sa=new af,Gd=new ut;let Oc=null,Bc=0,kc=0,zc=!1;const By=new $;class Hd{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._sigmas=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,i=.1,r=100,s={}){const{size:a=256,position:o=By}=s;Oc=this._renderer.getRenderTarget(),Bc=this._renderer.getActiveCubeFace(),kc=this._renderer.getActiveMipmapLevel(),zc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);const l=this._allocateTargets();return l.depthBuffer=!0,this._sceneToCubeUV(e,i,r,l,o),t>0&&this._blur(l,0,0,t),this._applyPMREM(l),this._cleanup(l),l}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=Xd(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=Wd(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(Oc,Bc,kc),this._renderer.xr.enabled=zc,e.scissorTest=!1,ws(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===$r||e.mapping===Gs?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),Oc=this._renderer.getRenderTarget(),Bc=this._renderer.getActiveCubeFace(),kc=this._renderer.getActiveMipmapLevel(),zc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const i=t||this._allocateTargets();return this._textureToCubeUV(e,i),this._applyPMREM(i),this._cleanup(i),i}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,i={magFilter:Gt,minFilter:Gt,generateMipmaps:!1,type:Yi,format:di,colorSpace:Vs,depthBuffer:!1},r=Vd(e,t,i);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=Vd(e,t,i);const{_lodMax:s}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods,sigmas:this._sigmas}=ky(s)),this._blurMaterial=Gy(s,e,t),this._ggxMaterial=zy(s,e,t)}return r}_compileMaterial(e){const t=new Yn(new Rt,e);this._renderer.compile(t,Sa)}_sceneToCubeUV(e,t,i,r,s){const l=new Hn(90,1,t,i),c=[1,-1,1,1,1,1],u=[1,1,1,-1,-1,-1],f=this._renderer,h=f.autoClear,d=f.toneMapping;f.getClearColor(Gd),f.toneMapping=Di,f.autoClear=!1,f.state.buffers.depth.getReversed()&&(f.setRenderTarget(r),f.clearDepth(),f.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new Yn(new eo,new sf({name:"PMREM.Background",side:on,depthWrite:!1,depthTest:!1})));const g=this._backgroundBox,p=g.material;let _=!1;const v=e.background;v?v.isColor&&(p.color.copy(v),e.background=null,_=!0):(p.color.copy(Gd),_=!0);for(let b=0;b<6;b++){const S=b%3;S===0?(l.up.set(0,c[b],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x+u[b],s.y,s.z)):S===1?(l.up.set(0,0,c[b]),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y+u[b],s.z)):(l.up.set(0,c[b],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y,s.z+u[b]));const E=this._cubeSize;ws(r,S*E,b>2?E:0,E,E),f.setRenderTarget(r),_&&f.render(g,l),f.render(e,l)}f.toneMapping=d,f.autoClear=h,e.background=v}_textureToCubeUV(e,t){const i=this._renderer,r=e.mapping===$r||e.mapping===Gs;r?(this._cubemapMaterial===null&&(this._cubemapMaterial=Xd()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=Wd());const s=r?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=s;const o=s.uniforms;o.envMap.value=e;const l=this._cubeSize;ws(t,0,0,3*l,2*l),i.setRenderTarget(t),i.render(a,Sa)}_applyPMREM(e){const t=this._renderer,i=t.autoClear;t.autoClear=!1;const r=this._lodMeshes.length;for(let s=1;s<r;s++)this._applyGGXFilter(e,s-1,s);t.autoClear=i}_applyGGXFilter(e,t,i){const r=this._renderer,s=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[i];o.material=a;const l=a.uniforms,c=i/(this._lodMeshes.length-1),u=t/(this._lodMeshes.length-1),f=Math.sqrt(c*c-u*u),h=0+c*1.25,d=f*h,{_lodMax:m}=this,g=this._sizeLods[i],p=3*g*(i>m-pr?i-m+pr:0),_=4*(this._cubeSize-g);l.envMap.value=e.texture,l.roughness.value=d,l.mipInt.value=m-t,ws(s,p,_,3*g,2*g),r.setRenderTarget(s),r.render(o,Sa),l.envMap.value=s.texture,l.roughness.value=0,l.mipInt.value=m-i,ws(e,p,_,3*g,2*g),r.setRenderTarget(e),r.render(o,Sa)}_blur(e,t,i,r,s){const a=this._pingPongRenderTarget;this._halfBlur(e,a,t,i,r,"latitudinal",s),this._halfBlur(a,e,i,i,r,"longitudinal",s)}_halfBlur(e,t,i,r,s,a,o){const l=this._renderer,c=this._blurMaterial;a!=="latitudinal"&&a!=="longitudinal"&&pt("blur direction must be either latitudinal or longitudinal!");const u=3,f=this._lodMeshes[r];f.material=c;const h=c.uniforms,d=this._sizeLods[i]-1,m=isFinite(s)?Math.PI/(2*d):2*Math.PI/(2*zr-1),g=s/m,p=isFinite(s)?1+Math.floor(u*g):zr;p>zr&&Qe(`sigmaRadians, ${s}, is too large and will clip, as it requested ${p} samples when the maximum is set to ${zr}`);const _=[];let v=0;for(let T=0;T<zr;++T){const x=T/g,y=Math.exp(-x*x/2);_.push(y),T===0?v+=y:T<p&&(v+=2*y)}for(let T=0;T<_.length;T++)_[T]=_[T]/v;h.envMap.value=e.texture,h.samples.value=p,h.weights.value=_,h.latitudinal.value=a==="latitudinal",o&&(h.poleAxis.value=o);const{_lodMax:b}=this;h.dTheta.value=m,h.mipInt.value=b-i;const S=this._sizeLods[r],E=3*S*(r>b-pr?r-b+pr:0),M=4*(this._cubeSize-S);ws(t,E,M,3*S,2*S),l.setRenderTarget(t),l.render(f,Sa)}}function ky(n){const e=[],t=[],i=[];let r=n;const s=n-pr+1+zd.length;for(let a=0;a<s;a++){const o=Math.pow(2,r);e.push(o);let l=1/o;a>n-pr?l=zd[a-n+pr-1]:a===0&&(l=0),t.push(l);const c=1/(o-2),u=-c,f=1+c,h=[u,u,f,u,f,f,u,u,f,f,u,f],d=6,m=6,g=3,p=2,_=1,v=new Float32Array(g*m*d),b=new Float32Array(p*m*d),S=new Float32Array(_*m*d);for(let M=0;M<d;M++){const T=M%3*2/3-1,x=M>2?0:-1,y=[T,x,0,T+2/3,x,0,T+2/3,x+1,0,T,x,0,T+2/3,x+1,0,T,x+1,0];v.set(y,g*m*M),b.set(h,p*m*M);const w=[M,M,M,M,M,M];S.set(w,_*m*M)}const E=new Rt;E.setAttribute("position",new Nt(v,g)),E.setAttribute("uv",new Nt(b,p)),E.setAttribute("faceIndex",new Nt(S,_)),i.push(new Yn(E,null)),r>pr&&r--}return{lodMeshes:i,sizeLods:e,sigmas:t}}function Vd(n,e,t){const i=new Qt(n,e,t);return i.texture.mapping=Il,i.texture.name="PMREM.cubeUv",i.scissorTest=!0,i}function ws(n,e,t,i,r){n.viewport.set(e,t,i,r),n.scissor.set(e,t,i,r)}function zy(n,e,t){return new ln({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:Oy,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${n}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:Nl(),fragmentShader:`

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
		`,blending:Sn,depthTest:!1,depthWrite:!1})}function Gy(n,e,t){const i=new Float32Array(zr),r=new $(0,1,0);return new ln({name:"SphericalGaussianBlur",defines:{n:zr,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${n}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:i},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:r}},vertexShader:Nl(),fragmentShader:`

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
		`,blending:Sn,depthTest:!1,depthWrite:!1})}function Wd(){return new ln({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Nl(),fragmentShader:`

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
		`,blending:Sn,depthTest:!1,depthWrite:!1})}function Xd(){return new ln({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Nl(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Sn,depthTest:!1,depthWrite:!1})}function Nl(){return`

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
	`}class i0 extends Qt{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;const i={width:e,height:e,depth:1},r=[i,i,i,i,i,i];this.texture=new qm(r),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;const i={uniforms:{tEquirect:{value:null}},vertexShader:`

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
			`},r=new eo(5,5,5),s=new ln({name:"CubemapFromEquirect",uniforms:Ws(i.uniforms),vertexShader:i.vertexShader,fragmentShader:i.fragmentShader,side:on,blending:Sn});s.uniforms.tEquirect.value=t;const a=new Yn(r,s),o=t.minFilter;return t.minFilter===Gr&&(t.minFilter=Gt),new Xv(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,i=!0,r=!0){const s=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,i,r);e.setRenderTarget(s)}}function Hy(n){let e=new WeakMap,t=new WeakMap,i=null;function r(h,d=!1){return h==null?null:d?a(h):s(h)}function s(h){if(h&&h.isTexture){const d=h.mapping;if(d===lc||d===cc)if(e.has(h)){const m=e.get(h).texture;return o(m,h.mapping)}else{const m=h.image;if(m&&m.height>0){const g=new i0(m.height);return g.fromEquirectangularTexture(n,h),e.set(h,g),h.addEventListener("dispose",c),o(g.texture,h.mapping)}else return null}}return h}function a(h){if(h&&h.isTexture){const d=h.mapping,m=d===lc||d===cc,g=d===$r||d===Gs;if(m||g){let p=t.get(h);const _=p!==void 0?p.texture.pmremVersion:0;if(h.isRenderTargetTexture&&h.pmremVersion!==_)return i===null&&(i=new Hd(n)),p=m?i.fromEquirectangular(h,p):i.fromCubemap(h,p),p.texture.pmremVersion=h.pmremVersion,t.set(h,p),p.texture;if(p!==void 0)return p.texture;{const v=h.image;return m&&v&&v.height>0||g&&v&&l(v)?(i===null&&(i=new Hd(n)),p=m?i.fromEquirectangular(h):i.fromCubemap(h),p.texture.pmremVersion=h.pmremVersion,t.set(h,p),h.addEventListener("dispose",u),p.texture):null}}}return h}function o(h,d){return d===lc?h.mapping=$r:d===cc&&(h.mapping=Gs),h}function l(h){let d=0;const m=6;for(let g=0;g<m;g++)h[g]!==void 0&&d++;return d===m}function c(h){const d=h.target;d.removeEventListener("dispose",c);const m=e.get(d);m!==void 0&&(e.delete(d),m.dispose())}function u(h){const d=h.target;d.removeEventListener("dispose",u);const m=t.get(d);m!==void 0&&(t.delete(d),m.dispose())}function f(){e=new WeakMap,t=new WeakMap,i!==null&&(i.dispose(),i=null)}return{get:r,dispose:f}}function Vy(n){const e={};function t(i){if(e[i]!==void 0)return e[i];const r=n.getExtension(i);return e[i]=r,r}return{has:function(i){return t(i)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(i){const r=t(i);return r===null&&gh("WebGLRenderer: "+i+" extension not supported."),r}}}function Wy(n,e,t,i){const r={},s=new WeakMap;function a(f){const h=f.target;h.index!==null&&e.remove(h.index);for(const m in h.attributes)e.remove(h.attributes[m]);h.removeEventListener("dispose",a),delete r[h.id];const d=s.get(h);d&&(e.remove(d),s.delete(h)),i.releaseStatesOfGeometry(h),h.isInstancedBufferGeometry===!0&&delete h._maxInstanceCount,t.memory.geometries--}function o(f,h){return r[h.id]===!0||(h.addEventListener("dispose",a),r[h.id]=!0,t.memory.geometries++),h}function l(f){const h=f.attributes;for(const d in h)e.update(h[d],n.ARRAY_BUFFER)}function c(f){const h=[],d=f.index,m=f.attributes.position;let g=0;if(m===void 0)return;if(d!==null){const v=d.array;g=d.version;for(let b=0,S=v.length;b<S;b+=3){const E=v[b+0],M=v[b+1],T=v[b+2];h.push(E,M,M,T,T,E)}}else{const v=m.array;g=m.version;for(let b=0,S=v.length/3-1;b<S;b+=3){const E=b+0,M=b+1,T=b+2;h.push(E,M,M,T,T,E)}}const p=new(m.count>=65535?Xm:Wm)(h,1);p.version=g;const _=s.get(f);_&&e.remove(_),s.set(f,p)}function u(f){const h=s.get(f);if(h){const d=f.index;d!==null&&h.version<d.version&&c(f)}else c(f);return s.get(f)}return{get:o,update:l,getWireframeAttribute:u}}function Xy(n,e,t){let i;function r(f){i=f}let s,a;function o(f){s=f.type,a=f.bytesPerElement}function l(f,h){n.drawElements(i,h,s,f*a),t.update(h,i,1)}function c(f,h,d){d!==0&&(n.drawElementsInstanced(i,h,s,f*a,d),t.update(h,i,d))}function u(f,h,d){if(d===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(i,h,0,s,f,0,d);let g=0;for(let p=0;p<d;p++)g+=h[p];t.update(g,i,1)}this.setMode=r,this.setIndex=o,this.render=l,this.renderInstances=c,this.renderMultiDraw=u}function jy(n){const e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function i(s,a,o){switch(t.calls++,a){case n.TRIANGLES:t.triangles+=o*(s/3);break;case n.LINES:t.lines+=o*(s/2);break;case n.LINE_STRIP:t.lines+=o*(s-1);break;case n.LINE_LOOP:t.lines+=o*s;break;case n.POINTS:t.points+=o*s;break;default:pt("WebGLInfo: Unknown draw mode:",a);break}}function r(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:r,update:i}}function Yy(n,e,t){const i=new WeakMap,r=new Ut;function s(a,o,l){const c=a.morphTargetInfluences,u=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,f=u!==void 0?u.length:0;let h=i.get(o);if(h===void 0||h.count!==f){let y=function(){T.dispose(),i.delete(o),o.removeEventListener("dispose",y)};h!==void 0&&h.texture.dispose();const d=o.morphAttributes.position!==void 0,m=o.morphAttributes.normal!==void 0,g=o.morphAttributes.color!==void 0,p=o.morphAttributes.position||[],_=o.morphAttributes.normal||[],v=o.morphAttributes.color||[];let b=0;d===!0&&(b=1),m===!0&&(b=2),g===!0&&(b=3);let S=o.attributes.position.count*b,E=1;S>e.maxTextureSize&&(E=Math.ceil(S/e.maxTextureSize),S=e.maxTextureSize);const M=new Float32Array(S*E*4*f),T=new Gm(M,S,E,f);T.type=fi,T.needsUpdate=!0;const x=b*4;for(let w=0;w<f;w++){const C=p[w],R=_[w],L=v[w],U=S*E*4*w;for(let I=0;I<C.count;I++){const F=I*x;d===!0&&(r.fromBufferAttribute(C,I),M[U+F+0]=r.x,M[U+F+1]=r.y,M[U+F+2]=r.z,M[U+F+3]=0),m===!0&&(r.fromBufferAttribute(R,I),M[U+F+4]=r.x,M[U+F+5]=r.y,M[U+F+6]=r.z,M[U+F+7]=0),g===!0&&(r.fromBufferAttribute(L,I),M[U+F+8]=r.x,M[U+F+9]=r.y,M[U+F+10]=r.z,M[U+F+11]=L.itemSize===4?r.w:1)}}h={count:f,texture:T,size:new Xe(S,E)},i.set(o,h),o.addEventListener("dispose",y)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)l.getUniforms().setValue(n,"morphTexture",a.morphTexture,t);else{let d=0;for(let g=0;g<c.length;g++)d+=c[g];const m=o.morphTargetsRelative?1:1-d;l.getUniforms().setValue(n,"morphTargetBaseInfluence",m),l.getUniforms().setValue(n,"morphTargetInfluences",c)}l.getUniforms().setValue(n,"morphTargetsTexture",h.texture,t),l.getUniforms().setValue(n,"morphTargetsTextureSize",h.size)}return{update:s}}function qy(n,e,t,i,r){let s=new WeakMap;function a(c){const u=r.render.frame,f=c.geometry,h=e.get(c,f);if(s.get(h)!==u&&(e.update(h),s.set(h,u)),c.isInstancedMesh&&(c.hasEventListener("dispose",l)===!1&&c.addEventListener("dispose",l),s.get(c)!==u&&(t.update(c.instanceMatrix,n.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,n.ARRAY_BUFFER),s.set(c,u))),c.isSkinnedMesh){const d=c.skeleton;s.get(d)!==u&&(d.update(),s.set(d,u))}return h}function o(){s=new WeakMap}function l(c){const u=c.target;u.removeEventListener("dispose",l),i.releaseStatesOfObject(u),t.remove(u.instanceMatrix),u.instanceColor!==null&&t.remove(u.instanceColor)}return{update:a,dispose:o}}const Ky={[Em]:"LINEAR_TONE_MAPPING",[wm]:"REINHARD_TONE_MAPPING",[Am]:"CINEON_TONE_MAPPING",[Rm]:"ACES_FILMIC_TONE_MAPPING",[Pm]:"AGX_TONE_MAPPING",[Dm]:"NEUTRAL_TONE_MAPPING",[Cm]:"CUSTOM_TONE_MAPPING"};function Zy(n,e,t,i,r){const s=new Qt(e,t,{type:n,depthBuffer:i,stencilBuffer:r,depthTexture:i?new Xi(e,t):void 0}),a=new Qt(e,t,{type:Yi,depthBuffer:!1,stencilBuffer:!1}),o=new Rt;o.setAttribute("position",new pi([-1,3,0,-1,-1,0,3,-1,0],3)),o.setAttribute("uv",new pi([0,2,0,0,2,0],2));const l=new Vv({uniforms:{tDiffuse:{value:null}},vertexShader:`
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
			}`,depthTest:!1,depthWrite:!1}),c=new Yn(o,l),u=new af(-1,1,1,-1,0,1);let f=null,h=null,d=!1,m,g=null,p=[],_=!1;this.setSize=function(v,b){s.setSize(v,b),a.setSize(v,b);for(let S=0;S<p.length;S++){const E=p[S];E.setSize&&E.setSize(v,b)}},this.setEffects=function(v){p=v,_=p.length>0&&p[0].isRenderPass===!0;const b=s.width,S=s.height;for(let E=0;E<p.length;E++){const M=p[E];M.setSize&&M.setSize(b,S)}},this.begin=function(v,b){if(d||v.toneMapping===Di&&p.length===0)return!1;if(g=b,b!==null){const S=b.width,E=b.height;(s.width!==S||s.height!==E)&&this.setSize(S,E)}return _===!1&&v.setRenderTarget(s),m=v.toneMapping,v.toneMapping=Di,!0},this.hasRenderPass=function(){return _},this.end=function(v,b){v.toneMapping=m,d=!0;let S=s,E=a;for(let M=0;M<p.length;M++){const T=p[M];if(T.enabled!==!1&&(T.render(v,E,S,b),T.needsSwap!==!1)){const x=S;S=E,E=x}}if(f!==v.outputColorSpace||h!==v.toneMapping){f=v.outputColorSpace,h=v.toneMapping,l.defines={},ft.getTransfer(f)===bt&&(l.defines.SRGB_TRANSFER="");const M=Ky[h];M&&(l.defines[M]=""),l.needsUpdate=!0}l.uniforms.tDiffuse.value=S.texture,v.setRenderTarget(g),v.render(c,u),g=null,d=!1},this.isCompositing=function(){return d},this.dispose=function(){s.depthTexture&&s.depthTexture.dispose(),s.dispose(),a.dispose(),o.dispose(),l.dispose()}}const r0=new Jt,yh=new Xi(1,1),s0=new Gm,a0=new _v,o0=new qm,jd=[],Yd=[],qd=new Float32Array(16),Kd=new Float32Array(9),Zd=new Float32Array(4);function Qs(n,e,t){const i=n[0];if(i<=0||i>0)return n;const r=e*t;let s=jd[r];if(s===void 0&&(s=new Float32Array(r),jd[r]=s),e!==0){i.toArray(s,0);for(let a=1,o=0;a!==e;++a)o+=t,n[a].toArray(s,o)}return s}function en(n,e){if(n.length!==e.length)return!1;for(let t=0,i=n.length;t<i;t++)if(n[t]!==e[t])return!1;return!0}function tn(n,e){for(let t=0,i=e.length;t<i;t++)n[t]=e[t]}function Ol(n,e){let t=Yd[e];t===void 0&&(t=new Int32Array(e),Yd[e]=t);for(let i=0;i!==e;++i)t[i]=n.allocateTextureUnit();return t}function $y(n,e){const t=this.cache;t[0]!==e&&(n.uniform1f(this.addr,e),t[0]=e)}function Jy(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(en(t,e))return;n.uniform2fv(this.addr,e),tn(t,e)}}function Qy(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(n.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(en(t,e))return;n.uniform3fv(this.addr,e),tn(t,e)}}function eb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(en(t,e))return;n.uniform4fv(this.addr,e),tn(t,e)}}function tb(n,e){const t=this.cache,i=e.elements;if(i===void 0){if(en(t,e))return;n.uniformMatrix2fv(this.addr,!1,e),tn(t,e)}else{if(en(t,i))return;Zd.set(i),n.uniformMatrix2fv(this.addr,!1,Zd),tn(t,i)}}function nb(n,e){const t=this.cache,i=e.elements;if(i===void 0){if(en(t,e))return;n.uniformMatrix3fv(this.addr,!1,e),tn(t,e)}else{if(en(t,i))return;Kd.set(i),n.uniformMatrix3fv(this.addr,!1,Kd),tn(t,i)}}function ib(n,e){const t=this.cache,i=e.elements;if(i===void 0){if(en(t,e))return;n.uniformMatrix4fv(this.addr,!1,e),tn(t,e)}else{if(en(t,i))return;qd.set(i),n.uniformMatrix4fv(this.addr,!1,qd),tn(t,i)}}function rb(n,e){const t=this.cache;t[0]!==e&&(n.uniform1i(this.addr,e),t[0]=e)}function sb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(en(t,e))return;n.uniform2iv(this.addr,e),tn(t,e)}}function ab(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(en(t,e))return;n.uniform3iv(this.addr,e),tn(t,e)}}function ob(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(en(t,e))return;n.uniform4iv(this.addr,e),tn(t,e)}}function lb(n,e){const t=this.cache;t[0]!==e&&(n.uniform1ui(this.addr,e),t[0]=e)}function cb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(en(t,e))return;n.uniform2uiv(this.addr,e),tn(t,e)}}function ub(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(en(t,e))return;n.uniform3uiv(this.addr,e),tn(t,e)}}function hb(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(en(t,e))return;n.uniform4uiv(this.addr,e),tn(t,e)}}function fb(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r);let s;this.type===n.SAMPLER_2D_SHADOW?(yh.compareFunction=t.isReversedDepthBuffer()?nf:tf,s=yh):s=r0,t.setTexture2D(e||s,r)}function db(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r),t.setTexture3D(e||a0,r)}function pb(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r),t.setTextureCube(e||o0,r)}function mb(n,e,t){const i=this.cache,r=t.allocateTextureUnit();i[0]!==r&&(n.uniform1i(this.addr,r),i[0]=r),t.setTexture2DArray(e||s0,r)}function gb(n){switch(n){case 5126:return $y;case 35664:return Jy;case 35665:return Qy;case 35666:return eb;case 35674:return tb;case 35675:return nb;case 35676:return ib;case 5124:case 35670:return rb;case 35667:case 35671:return sb;case 35668:case 35672:return ab;case 35669:case 35673:return ob;case 5125:return lb;case 36294:return cb;case 36295:return ub;case 36296:return hb;case 35678:case 36198:case 36298:case 36306:case 35682:return fb;case 35679:case 36299:case 36307:return db;case 35680:case 36300:case 36308:case 36293:return pb;case 36289:case 36303:case 36311:case 36292:return mb}}function _b(n,e){n.uniform1fv(this.addr,e)}function vb(n,e){const t=Qs(e,this.size,2);n.uniform2fv(this.addr,t)}function xb(n,e){const t=Qs(e,this.size,3);n.uniform3fv(this.addr,t)}function yb(n,e){const t=Qs(e,this.size,4);n.uniform4fv(this.addr,t)}function bb(n,e){const t=Qs(e,this.size,4);n.uniformMatrix2fv(this.addr,!1,t)}function Mb(n,e){const t=Qs(e,this.size,9);n.uniformMatrix3fv(this.addr,!1,t)}function Sb(n,e){const t=Qs(e,this.size,16);n.uniformMatrix4fv(this.addr,!1,t)}function Tb(n,e){n.uniform1iv(this.addr,e)}function Eb(n,e){n.uniform2iv(this.addr,e)}function wb(n,e){n.uniform3iv(this.addr,e)}function Ab(n,e){n.uniform4iv(this.addr,e)}function Rb(n,e){n.uniform1uiv(this.addr,e)}function Cb(n,e){n.uniform2uiv(this.addr,e)}function Pb(n,e){n.uniform3uiv(this.addr,e)}function Db(n,e){n.uniform4uiv(this.addr,e)}function Ub(n,e,t){const i=this.cache,r=e.length,s=Ol(t,r);en(i,s)||(n.uniform1iv(this.addr,s),tn(i,s));let a;this.type===n.SAMPLER_2D_SHADOW?a=yh:a=r0;for(let o=0;o!==r;++o)t.setTexture2D(e[o]||a,s[o])}function Lb(n,e,t){const i=this.cache,r=e.length,s=Ol(t,r);en(i,s)||(n.uniform1iv(this.addr,s),tn(i,s));for(let a=0;a!==r;++a)t.setTexture3D(e[a]||a0,s[a])}function Ib(n,e,t){const i=this.cache,r=e.length,s=Ol(t,r);en(i,s)||(n.uniform1iv(this.addr,s),tn(i,s));for(let a=0;a!==r;++a)t.setTextureCube(e[a]||o0,s[a])}function Fb(n,e,t){const i=this.cache,r=e.length,s=Ol(t,r);en(i,s)||(n.uniform1iv(this.addr,s),tn(i,s));for(let a=0;a!==r;++a)t.setTexture2DArray(e[a]||s0,s[a])}function Nb(n){switch(n){case 5126:return _b;case 35664:return vb;case 35665:return xb;case 35666:return yb;case 35674:return bb;case 35675:return Mb;case 35676:return Sb;case 5124:case 35670:return Tb;case 35667:case 35671:return Eb;case 35668:case 35672:return wb;case 35669:case 35673:return Ab;case 5125:return Rb;case 36294:return Cb;case 36295:return Pb;case 36296:return Db;case 35678:case 36198:case 36298:case 36306:case 35682:return Ub;case 35679:case 36299:case 36307:return Lb;case 35680:case 36300:case 36308:case 36293:return Ib;case 36289:case 36303:case 36311:case 36292:return Fb}}class Ob{constructor(e,t,i){this.id=e,this.addr=i,this.cache=[],this.type=t.type,this.setValue=gb(t.type)}}class Bb{constructor(e,t,i){this.id=e,this.addr=i,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=Nb(t.type)}}class kb{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,i){const r=this.seq;for(let s=0,a=r.length;s!==a;++s){const o=r[s];o.setValue(e,t[o.id],i)}}}const Gc=/(\w+)(\])?(\[|\.)?/g;function $d(n,e){n.seq.push(e),n.map[e.id]=e}function zb(n,e,t){const i=n.name,r=i.length;for(Gc.lastIndex=0;;){const s=Gc.exec(i),a=Gc.lastIndex;let o=s[1];const l=s[2]==="]",c=s[3];if(l&&(o=o|0),c===void 0||c==="["&&a+2===r){$d(t,c===void 0?new Ob(o,n,e):new Bb(o,n,e));break}else{let f=t.map[o];f===void 0&&(f=new kb(o),$d(t,f)),t=f}}}class tl{constructor(e,t){this.seq=[],this.map={};const i=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let a=0;a<i;++a){const o=e.getActiveUniform(t,a),l=e.getUniformLocation(t,o.name);zb(o,l,this)}const r=[],s=[];for(const a of this.seq)a.type===e.SAMPLER_2D_SHADOW||a.type===e.SAMPLER_CUBE_SHADOW||a.type===e.SAMPLER_2D_ARRAY_SHADOW?r.push(a):s.push(a);r.length>0&&(this.seq=r.concat(s))}setValue(e,t,i,r){const s=this.map[t];s!==void 0&&s.setValue(e,i,r)}setOptional(e,t,i){const r=t[i];r!==void 0&&this.setValue(e,i,r)}static upload(e,t,i,r){for(let s=0,a=t.length;s!==a;++s){const o=t[s],l=i[o.id];l.needsUpdate!==!1&&o.setValue(e,l.value,r)}}static seqWithValue(e,t){const i=[];for(let r=0,s=e.length;r!==s;++r){const a=e[r];a.id in t&&i.push(a)}return i}}function Jd(n,e,t){const i=n.createShader(e);return n.shaderSource(i,t),n.compileShader(i),i}const Gb=37297;let Hb=0;function Vb(n,e){const t=n.split(`
`),i=[],r=Math.max(e-6,0),s=Math.min(e+6,t.length);for(let a=r;a<s;a++){const o=a+1;i.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return i.join(`
`)}const Qd=new rt;function Wb(n){ft._getMatrix(Qd,ft.workingColorSpace,n);const e=`mat3( ${Qd.elements.map(t=>t.toFixed(4))} )`;switch(ft.getTransfer(n)){case fl:return[e,"LinearTransferOETF"];case bt:return[e,"sRGBTransferOETF"];default:return Qe("WebGLProgram: Unsupported color space: ",n),[e,"LinearTransferOETF"]}}function ep(n,e,t){const i=n.getShaderParameter(e,n.COMPILE_STATUS),s=(n.getShaderInfoLog(e)||"").trim();if(i&&s==="")return"";const a=/ERROR: 0:(\d+)/.exec(s);if(a){const o=parseInt(a[1]);return t.toUpperCase()+`

`+s+`

`+Vb(n.getShaderSource(e),o)}else return s}function Xb(n,e){const t=Wb(e);return[`vec4 ${n}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}const jb={[Em]:"Linear",[wm]:"Reinhard",[Am]:"Cineon",[Rm]:"ACESFilmic",[Pm]:"AgX",[Dm]:"Neutral",[Cm]:"Custom"};function Yb(n,e){const t=jb[e];return t===void 0?(Qe("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+n+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+n+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}const zo=new $;function qb(){ft.getLuminanceCoefficients(zo);const n=zo.x.toFixed(4),e=zo.y.toFixed(4),t=zo.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${n}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function Kb(n){return[n.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",n.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Pa).join(`
`)}function Zb(n){const e=[];for(const t in n){const i=n[t];i!==!1&&e.push("#define "+t+" "+i)}return e.join(`
`)}function $b(n,e){const t={},i=n.getProgramParameter(e,n.ACTIVE_ATTRIBUTES);for(let r=0;r<i;r++){const s=n.getActiveAttrib(e,r),a=s.name;let o=1;s.type===n.FLOAT_MAT2&&(o=2),s.type===n.FLOAT_MAT3&&(o=3),s.type===n.FLOAT_MAT4&&(o=4),t[a]={type:s.type,location:n.getAttribLocation(e,a),locationSize:o}}return t}function Pa(n){return n!==""}function tp(n,e){const t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return n.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function np(n,e){return n.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const Jb=/^[ \t]*#include +<([\w\d./]+)>/gm;function bh(n){return n.replace(Jb,eM)}const Qb=new Map;function eM(n,e){let t=st[e];if(t===void 0){const i=Qb.get(e);if(i!==void 0)t=st[i],Qe('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,i);else throw new Error("Can not resolve #include <"+e+">")}return bh(t)}const tM=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function ip(n){return n.replace(tM,nM)}function nM(n,e,t,i){let r="";for(let s=parseInt(e);s<parseInt(t);s++)r+=i.replace(/\[\s*i\s*\]/g,"[ "+s+" ]").replace(/UNROLLED_LOOP_INDEX/g,s);return r}function rp(n){let e=`precision ${n.precision} float;
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
#define LOW_PRECISION`),e}const iM={[Ko]:"SHADOWMAP_TYPE_PCF",[Ra]:"SHADOWMAP_TYPE_VSM"};function rM(n){return iM[n.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}const sM={[$r]:"ENVMAP_TYPE_CUBE",[Gs]:"ENVMAP_TYPE_CUBE",[Il]:"ENVMAP_TYPE_CUBE_UV"};function aM(n){return n.envMap===!1?"ENVMAP_TYPE_CUBE":sM[n.envMapMode]||"ENVMAP_TYPE_CUBE"}const oM={[Gs]:"ENVMAP_MODE_REFRACTION"};function lM(n){return n.envMap===!1?"ENVMAP_MODE_REFLECTION":oM[n.envMapMode]||"ENVMAP_MODE_REFLECTION"}const cM={[Tm]:"ENVMAP_BLENDING_MULTIPLY",[K_]:"ENVMAP_BLENDING_MIX",[Z_]:"ENVMAP_BLENDING_ADD"};function uM(n){return n.envMap===!1?"ENVMAP_BLENDING_NONE":cM[n.combine]||"ENVMAP_BLENDING_NONE"}function hM(n){const e=n.envMapCubeUVHeight;if(e===null)return null;const t=Math.log2(e)-2,i=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:i,maxMip:t}}function fM(n,e,t,i){const r=n.getContext(),s=t.defines;let a=t.vertexShader,o=t.fragmentShader;const l=rM(t),c=aM(t),u=lM(t),f=uM(t),h=hM(t),d=Kb(t),m=Zb(s),g=r.createProgram();let p,_,v=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(p=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m].filter(Pa).join(`
`),p.length>0&&(p+=`
`),_=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m].filter(Pa).join(`
`),_.length>0&&(_+=`
`)):(p=[rp(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+u:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexNormals?"#define HAS_NORMAL":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Pa).join(`
`),_=[rp(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+c:"",t.envMap?"#define "+u:"",t.envMap?"#define "+f:"",h?"#define CUBEUV_TEXEL_WIDTH "+h.texelWidth:"",h?"#define CUBEUV_TEXEL_HEIGHT "+h.texelHeight:"",h?"#define CUBEUV_MAX_MIP "+h.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor?"#define USE_COLOR":"",t.vertexAlphas||t.batchingColor?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==Di?"#define TONE_MAPPING":"",t.toneMapping!==Di?st.tonemapping_pars_fragment:"",t.toneMapping!==Di?Yb("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",st.colorspace_pars_fragment,Xb("linearToOutputTexel",t.outputColorSpace),qb(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter(Pa).join(`
`)),a=bh(a),a=tp(a,t),a=np(a,t),o=bh(o),o=tp(o,t),o=np(o,t),a=ip(a),o=ip(o),t.isRawShaderMaterial!==!0&&(v=`#version 300 es
`,p=[d,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+p,_=["#define varying in",t.glslVersion===ud?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===ud?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+_);const b=v+p+a,S=v+_+o,E=Jd(r,r.VERTEX_SHADER,b),M=Jd(r,r.FRAGMENT_SHADER,S);r.attachShader(g,E),r.attachShader(g,M),t.index0AttributeName!==void 0?r.bindAttribLocation(g,0,t.index0AttributeName):t.morphTargets===!0&&r.bindAttribLocation(g,0,"position"),r.linkProgram(g);function T(C){if(n.debug.checkShaderErrors){const R=r.getProgramInfoLog(g)||"",L=r.getShaderInfoLog(E)||"",U=r.getShaderInfoLog(M)||"",I=R.trim(),F=L.trim(),N=U.trim();let Y=!0,j=!0;if(r.getProgramParameter(g,r.LINK_STATUS)===!1)if(Y=!1,typeof n.debug.onShaderError=="function")n.debug.onShaderError(r,g,E,M);else{const Z=ep(r,E,"vertex"),O=ep(r,M,"fragment");pt("THREE.WebGLProgram: Shader Error "+r.getError()+" - VALIDATE_STATUS "+r.getProgramParameter(g,r.VALIDATE_STATUS)+`

Material Name: `+C.name+`
Material Type: `+C.type+`

Program Info Log: `+I+`
`+Z+`
`+O)}else I!==""?Qe("WebGLProgram: Program Info Log:",I):(F===""||N==="")&&(j=!1);j&&(C.diagnostics={runnable:Y,programLog:I,vertexShader:{log:F,prefix:p},fragmentShader:{log:N,prefix:_}})}r.deleteShader(E),r.deleteShader(M),x=new tl(r,g),y=$b(r,g)}let x;this.getUniforms=function(){return x===void 0&&T(this),x};let y;this.getAttributes=function(){return y===void 0&&T(this),y};let w=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return w===!1&&(w=r.getProgramParameter(g,Gb)),w},this.destroy=function(){i.releaseStatesOfProgram(this),r.deleteProgram(g),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=Hb++,this.cacheKey=e,this.usedTimes=1,this.program=g,this.vertexShader=E,this.fragmentShader=M,this}let dM=0;class pM{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){const t=e.vertexShader,i=e.fragmentShader,r=this._getShaderStage(t),s=this._getShaderStage(i),a=this._getShaderCacheForMaterial(e);return a.has(r)===!1&&(a.add(r),r.usedTimes++),a.has(s)===!1&&(a.add(s),s.usedTimes++),this}remove(e){const t=this.materialCache.get(e);for(const i of t)i.usedTimes--,i.usedTimes===0&&this.shaderCache.delete(i.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const t=this.materialCache;let i=t.get(e);return i===void 0&&(i=new Set,t.set(e,i)),i}_getShaderStage(e){const t=this.shaderCache;let i=t.get(e);return i===void 0&&(i=new mM(e),t.set(e,i)),i}}class mM{constructor(e){this.id=dM++,this.code=e,this.usedTimes=0}}function gM(n){return n===Jr||n===ul||n===hl}function _M(n,e,t,i,r,s){const a=new Hm,o=new pM,l=new Set,c=[],u=new Map,f=i.logarithmicDepthBuffer;let h=i.precision;const d={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function m(x){return l.add(x),x===0?"uv":`uv${x}`}function g(x,y,w,C,R,L){const U=C.fog,I=R.geometry,F=x.isMeshStandardMaterial||x.isMeshLambertMaterial||x.isMeshPhongMaterial?C.environment:null,N=x.isMeshStandardMaterial||x.isMeshLambertMaterial&&!x.envMap||x.isMeshPhongMaterial&&!x.envMap,Y=e.get(x.envMap||F,N),j=Y&&Y.mapping===Il?Y.image.height:null,Z=d[x.type];x.precision!==null&&(h=i.getMaxPrecision(x.precision),h!==x.precision&&Qe("WebGLProgram.getParameters:",x.precision,"not supported, using",h,"instead."));const O=I.morphAttributes.position||I.morphAttributes.normal||I.morphAttributes.color,H=O!==void 0?O.length:0;let B=0;I.morphAttributes.position!==void 0&&(B=1),I.morphAttributes.normal!==void 0&&(B=2),I.morphAttributes.color!==void 0&&(B=3);let V,G,z,W;if(Z){const $e=Si[Z];V=$e.vertexShader,G=$e.fragmentShader}else V=x.vertexShader,G=x.fragmentShader,o.update(x),z=o.getVertexShaderID(x),W=o.getFragmentShaderID(x);const q=n.getRenderTarget(),ce=n.state.buffers.depth.getReversed(),me=R.isInstancedMesh===!0,Q=R.isBatchedMesh===!0,ie=!!x.map,be=!!x.matcap,De=!!Y,ye=!!x.aoMap,_e=!!x.lightMap,Ne=!!x.bumpMap,ae=!!x.normalMap,Ee=!!x.displacementMap,k=!!x.emissiveMap,de=!!x.metalnessMap,Pe=!!x.roughnessMap,we=x.anisotropy>0,pe=x.clearcoat>0,Re=x.dispersion>0,D=x.iridescence>0,A=x.sheen>0,X=x.transmission>0,ee=we&&!!x.anisotropyMap,he=pe&&!!x.clearcoatMap,xe=pe&&!!x.clearcoatNormalMap,Te=pe&&!!x.clearcoatRoughnessMap,te=D&&!!x.iridescenceMap,le=D&&!!x.iridescenceThicknessMap,ge=A&&!!x.sheenColorMap,Ie=A&&!!x.sheenRoughnessMap,Me=!!x.specularMap,Ae=!!x.specularColorMap,He=!!x.specularIntensityMap,Fe=X&&!!x.transmissionMap,Ye=X&&!!x.thicknessMap,K=!!x.gradientMap,ve=!!x.alphaMap,oe=x.alphaTest>0,Le=!!x.alphaHash,Se=!!x.extensions;let fe=Di;x.toneMapped&&(q===null||q.isXRRenderTarget===!0)&&(fe=n.toneMapping);const Oe={shaderID:Z,shaderType:x.type,shaderName:x.name,vertexShader:V,fragmentShader:G,defines:x.defines,customVertexShaderID:z,customFragmentShaderID:W,isRawShaderMaterial:x.isRawShaderMaterial===!0,glslVersion:x.glslVersion,precision:h,batching:Q,batchingColor:Q&&R._colorsTexture!==null,instancing:me,instancingColor:me&&R.instanceColor!==null,instancingMorph:me&&R.morphTexture!==null,outputColorSpace:q===null?n.outputColorSpace:q.isXRRenderTarget===!0?q.texture.colorSpace:ft.workingColorSpace,alphaToCoverage:!!x.alphaToCoverage,map:ie,matcap:be,envMap:De,envMapMode:De&&Y.mapping,envMapCubeUVHeight:j,aoMap:ye,lightMap:_e,bumpMap:Ne,normalMap:ae,displacementMap:Ee,emissiveMap:k,normalMapObjectSpace:ae&&x.normalMapType===Q_,normalMapTangentSpace:ae&&x.normalMapType===ld,packedNormalMap:ae&&x.normalMapType===ld&&gM(x.normalMap.format),metalnessMap:de,roughnessMap:Pe,anisotropy:we,anisotropyMap:ee,clearcoat:pe,clearcoatMap:he,clearcoatNormalMap:xe,clearcoatRoughnessMap:Te,dispersion:Re,iridescence:D,iridescenceMap:te,iridescenceThicknessMap:le,sheen:A,sheenColorMap:ge,sheenRoughnessMap:Ie,specularMap:Me,specularColorMap:Ae,specularIntensityMap:He,transmission:X,transmissionMap:Fe,thicknessMap:Ye,gradientMap:K,opaque:x.transparent===!1&&x.blending===Vr&&x.alphaToCoverage===!1,alphaMap:ve,alphaTest:oe,alphaHash:Le,combine:x.combine,mapUv:ie&&m(x.map.channel),aoMapUv:ye&&m(x.aoMap.channel),lightMapUv:_e&&m(x.lightMap.channel),bumpMapUv:Ne&&m(x.bumpMap.channel),normalMapUv:ae&&m(x.normalMap.channel),displacementMapUv:Ee&&m(x.displacementMap.channel),emissiveMapUv:k&&m(x.emissiveMap.channel),metalnessMapUv:de&&m(x.metalnessMap.channel),roughnessMapUv:Pe&&m(x.roughnessMap.channel),anisotropyMapUv:ee&&m(x.anisotropyMap.channel),clearcoatMapUv:he&&m(x.clearcoatMap.channel),clearcoatNormalMapUv:xe&&m(x.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:Te&&m(x.clearcoatRoughnessMap.channel),iridescenceMapUv:te&&m(x.iridescenceMap.channel),iridescenceThicknessMapUv:le&&m(x.iridescenceThicknessMap.channel),sheenColorMapUv:ge&&m(x.sheenColorMap.channel),sheenRoughnessMapUv:Ie&&m(x.sheenRoughnessMap.channel),specularMapUv:Me&&m(x.specularMap.channel),specularColorMapUv:Ae&&m(x.specularColorMap.channel),specularIntensityMapUv:He&&m(x.specularIntensityMap.channel),transmissionMapUv:Fe&&m(x.transmissionMap.channel),thicknessMapUv:Ye&&m(x.thicknessMap.channel),alphaMapUv:ve&&m(x.alphaMap.channel),vertexTangents:!!I.attributes.tangent&&(ae||we),vertexNormals:!!I.attributes.normal,vertexColors:x.vertexColors,vertexAlphas:x.vertexColors===!0&&!!I.attributes.color&&I.attributes.color.itemSize===4,pointsUvs:R.isPoints===!0&&!!I.attributes.uv&&(ie||ve),fog:!!U,useFog:x.fog===!0,fogExp2:!!U&&U.isFogExp2,flatShading:x.wireframe===!1&&(x.flatShading===!0||I.attributes.normal===void 0&&ae===!1&&(x.isMeshLambertMaterial||x.isMeshPhongMaterial||x.isMeshStandardMaterial||x.isMeshPhysicalMaterial)),sizeAttenuation:x.sizeAttenuation===!0,logarithmicDepthBuffer:f,reversedDepthBuffer:ce,skinning:R.isSkinnedMesh===!0,morphTargets:I.morphAttributes.position!==void 0,morphNormals:I.morphAttributes.normal!==void 0,morphColors:I.morphAttributes.color!==void 0,morphTargetsCount:H,morphTextureStride:B,numDirLights:y.directional.length,numPointLights:y.point.length,numSpotLights:y.spot.length,numSpotLightMaps:y.spotLightMap.length,numRectAreaLights:y.rectArea.length,numHemiLights:y.hemi.length,numDirLightShadows:y.directionalShadowMap.length,numPointLightShadows:y.pointShadowMap.length,numSpotLightShadows:y.spotShadowMap.length,numSpotLightShadowsWithMaps:y.numSpotLightShadowsWithMaps,numLightProbes:y.numLightProbes,numLightProbeGrids:L.length,numClippingPlanes:s.numPlanes,numClipIntersection:s.numIntersection,dithering:x.dithering,shadowMapEnabled:n.shadowMap.enabled&&w.length>0,shadowMapType:n.shadowMap.type,toneMapping:fe,decodeVideoTexture:ie&&x.map.isVideoTexture===!0&&ft.getTransfer(x.map.colorSpace)===bt,decodeVideoTextureEmissive:k&&x.emissiveMap.isVideoTexture===!0&&ft.getTransfer(x.emissiveMap.colorSpace)===bt,premultipliedAlpha:x.premultipliedAlpha,doubleSided:x.side===An,flipSided:x.side===on,useDepthPacking:x.depthPacking>=0,depthPacking:x.depthPacking||0,index0AttributeName:x.index0AttributeName,extensionClipCullDistance:Se&&x.extensions.clipCullDistance===!0&&t.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(Se&&x.extensions.multiDraw===!0||Q)&&t.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:t.has("KHR_parallel_shader_compile"),customProgramCacheKey:x.customProgramCacheKey()};return Oe.vertexUv1s=l.has(1),Oe.vertexUv2s=l.has(2),Oe.vertexUv3s=l.has(3),l.clear(),Oe}function p(x){const y=[];if(x.shaderID?y.push(x.shaderID):(y.push(x.customVertexShaderID),y.push(x.customFragmentShaderID)),x.defines!==void 0)for(const w in x.defines)y.push(w),y.push(x.defines[w]);return x.isRawShaderMaterial===!1&&(_(y,x),v(y,x),y.push(n.outputColorSpace)),y.push(x.customProgramCacheKey),y.join()}function _(x,y){x.push(y.precision),x.push(y.outputColorSpace),x.push(y.envMapMode),x.push(y.envMapCubeUVHeight),x.push(y.mapUv),x.push(y.alphaMapUv),x.push(y.lightMapUv),x.push(y.aoMapUv),x.push(y.bumpMapUv),x.push(y.normalMapUv),x.push(y.displacementMapUv),x.push(y.emissiveMapUv),x.push(y.metalnessMapUv),x.push(y.roughnessMapUv),x.push(y.anisotropyMapUv),x.push(y.clearcoatMapUv),x.push(y.clearcoatNormalMapUv),x.push(y.clearcoatRoughnessMapUv),x.push(y.iridescenceMapUv),x.push(y.iridescenceThicknessMapUv),x.push(y.sheenColorMapUv),x.push(y.sheenRoughnessMapUv),x.push(y.specularMapUv),x.push(y.specularColorMapUv),x.push(y.specularIntensityMapUv),x.push(y.transmissionMapUv),x.push(y.thicknessMapUv),x.push(y.combine),x.push(y.fogExp2),x.push(y.sizeAttenuation),x.push(y.morphTargetsCount),x.push(y.morphAttributeCount),x.push(y.numDirLights),x.push(y.numPointLights),x.push(y.numSpotLights),x.push(y.numSpotLightMaps),x.push(y.numHemiLights),x.push(y.numRectAreaLights),x.push(y.numDirLightShadows),x.push(y.numPointLightShadows),x.push(y.numSpotLightShadows),x.push(y.numSpotLightShadowsWithMaps),x.push(y.numLightProbes),x.push(y.shadowMapType),x.push(y.toneMapping),x.push(y.numClippingPlanes),x.push(y.numClipIntersection),x.push(y.depthPacking)}function v(x,y){a.disableAll(),y.instancing&&a.enable(0),y.instancingColor&&a.enable(1),y.instancingMorph&&a.enable(2),y.matcap&&a.enable(3),y.envMap&&a.enable(4),y.normalMapObjectSpace&&a.enable(5),y.normalMapTangentSpace&&a.enable(6),y.clearcoat&&a.enable(7),y.iridescence&&a.enable(8),y.alphaTest&&a.enable(9),y.vertexColors&&a.enable(10),y.vertexAlphas&&a.enable(11),y.vertexUv1s&&a.enable(12),y.vertexUv2s&&a.enable(13),y.vertexUv3s&&a.enable(14),y.vertexTangents&&a.enable(15),y.anisotropy&&a.enable(16),y.alphaHash&&a.enable(17),y.batching&&a.enable(18),y.dispersion&&a.enable(19),y.batchingColor&&a.enable(20),y.gradientMap&&a.enable(21),y.packedNormalMap&&a.enable(22),y.vertexNormals&&a.enable(23),x.push(a.mask),a.disableAll(),y.fog&&a.enable(0),y.useFog&&a.enable(1),y.flatShading&&a.enable(2),y.logarithmicDepthBuffer&&a.enable(3),y.reversedDepthBuffer&&a.enable(4),y.skinning&&a.enable(5),y.morphTargets&&a.enable(6),y.morphNormals&&a.enable(7),y.morphColors&&a.enable(8),y.premultipliedAlpha&&a.enable(9),y.shadowMapEnabled&&a.enable(10),y.doubleSided&&a.enable(11),y.flipSided&&a.enable(12),y.useDepthPacking&&a.enable(13),y.dithering&&a.enable(14),y.transmission&&a.enable(15),y.sheen&&a.enable(16),y.opaque&&a.enable(17),y.pointsUvs&&a.enable(18),y.decodeVideoTexture&&a.enable(19),y.decodeVideoTextureEmissive&&a.enable(20),y.alphaToCoverage&&a.enable(21),y.numLightProbeGrids>0&&a.enable(22),x.push(a.mask)}function b(x){const y=d[x.type];let w;if(y){const C=Si[y];w=$m.clone(C.uniforms)}else w=x.uniforms;return w}function S(x,y){let w=u.get(y);return w!==void 0?++w.usedTimes:(w=new fM(n,y,x,r),c.push(w),u.set(y,w)),w}function E(x){if(--x.usedTimes===0){const y=c.indexOf(x);c[y]=c[c.length-1],c.pop(),u.delete(x.cacheKey),x.destroy()}}function M(x){o.remove(x)}function T(){o.dispose()}return{getParameters:g,getProgramCacheKey:p,getUniforms:b,acquireProgram:S,releaseProgram:E,releaseShaderCache:M,programs:c,dispose:T}}function vM(){let n=new WeakMap;function e(a){return n.has(a)}function t(a){let o=n.get(a);return o===void 0&&(o={},n.set(a,o)),o}function i(a){n.delete(a)}function r(a,o,l){n.get(a)[o]=l}function s(){n=new WeakMap}return{has:e,get:t,remove:i,update:r,dispose:s}}function xM(n,e){return n.groupOrder!==e.groupOrder?n.groupOrder-e.groupOrder:n.renderOrder!==e.renderOrder?n.renderOrder-e.renderOrder:n.material.id!==e.material.id?n.material.id-e.material.id:n.materialVariant!==e.materialVariant?n.materialVariant-e.materialVariant:n.z!==e.z?n.z-e.z:n.id-e.id}function sp(n,e){return n.groupOrder!==e.groupOrder?n.groupOrder-e.groupOrder:n.renderOrder!==e.renderOrder?n.renderOrder-e.renderOrder:n.z!==e.z?e.z-n.z:n.id-e.id}function ap(){const n=[];let e=0;const t=[],i=[],r=[];function s(){e=0,t.length=0,i.length=0,r.length=0}function a(h){let d=0;return h.isInstancedMesh&&(d+=2),h.isSkinnedMesh&&(d+=1),d}function o(h,d,m,g,p,_){let v=n[e];return v===void 0?(v={id:h.id,object:h,geometry:d,material:m,materialVariant:a(h),groupOrder:g,renderOrder:h.renderOrder,z:p,group:_},n[e]=v):(v.id=h.id,v.object=h,v.geometry=d,v.material=m,v.materialVariant=a(h),v.groupOrder=g,v.renderOrder=h.renderOrder,v.z=p,v.group=_),e++,v}function l(h,d,m,g,p,_){const v=o(h,d,m,g,p,_);m.transmission>0?i.push(v):m.transparent===!0?r.push(v):t.push(v)}function c(h,d,m,g,p,_){const v=o(h,d,m,g,p,_);m.transmission>0?i.unshift(v):m.transparent===!0?r.unshift(v):t.unshift(v)}function u(h,d){t.length>1&&t.sort(h||xM),i.length>1&&i.sort(d||sp),r.length>1&&r.sort(d||sp)}function f(){for(let h=e,d=n.length;h<d;h++){const m=n[h];if(m.id===null)break;m.id=null,m.object=null,m.geometry=null,m.material=null,m.group=null}}return{opaque:t,transmissive:i,transparent:r,init:s,push:l,unshift:c,finish:f,sort:u}}function yM(){let n=new WeakMap;function e(i,r){const s=n.get(i);let a;return s===void 0?(a=new ap,n.set(i,[a])):r>=s.length?(a=new ap,s.push(a)):a=s[r],a}function t(){n=new WeakMap}return{get:e,dispose:t}}function bM(){const n={};return{get:function(e){if(n[e.id]!==void 0)return n[e.id];let t;switch(e.type){case"DirectionalLight":t={direction:new $,color:new ut};break;case"SpotLight":t={position:new $,direction:new $,color:new ut,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new $,color:new ut,distance:0,decay:0};break;case"HemisphereLight":t={direction:new $,skyColor:new ut,groundColor:new ut};break;case"RectAreaLight":t={color:new ut,position:new $,halfWidth:new $,halfHeight:new $};break}return n[e.id]=t,t}}}function MM(){const n={};return{get:function(e){if(n[e.id]!==void 0)return n[e.id];let t;switch(e.type){case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Xe,shadowCameraNear:1,shadowCameraFar:1e3};break}return n[e.id]=t,t}}}let SM=0;function TM(n,e){return(e.castShadow?2:0)-(n.castShadow?2:0)+(e.map?1:0)-(n.map?1:0)}function EM(n){const e=new bM,t=MM(),i={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)i.probe.push(new $);const r=new $,s=new zt,a=new zt;function o(c){let u=0,f=0,h=0;for(let y=0;y<9;y++)i.probe[y].set(0,0,0);let d=0,m=0,g=0,p=0,_=0,v=0,b=0,S=0,E=0,M=0,T=0;c.sort(TM);for(let y=0,w=c.length;y<w;y++){const C=c[y],R=C.color,L=C.intensity,U=C.distance;let I=null;if(C.shadow&&C.shadow.map&&(C.shadow.map.texture.format===Jr?I=C.shadow.map.texture:I=C.shadow.map.depthTexture||C.shadow.map.texture),C.isAmbientLight)u+=R.r*L,f+=R.g*L,h+=R.b*L;else if(C.isLightProbe){for(let F=0;F<9;F++)i.probe[F].addScaledVector(C.sh.coefficients[F],L);T++}else if(C.isDirectionalLight){const F=e.get(C);if(F.color.copy(C.color).multiplyScalar(C.intensity),C.castShadow){const N=C.shadow,Y=t.get(C);Y.shadowIntensity=N.intensity,Y.shadowBias=N.bias,Y.shadowNormalBias=N.normalBias,Y.shadowRadius=N.radius,Y.shadowMapSize=N.mapSize,i.directionalShadow[d]=Y,i.directionalShadowMap[d]=I,i.directionalShadowMatrix[d]=C.shadow.matrix,v++}i.directional[d]=F,d++}else if(C.isSpotLight){const F=e.get(C);F.position.setFromMatrixPosition(C.matrixWorld),F.color.copy(R).multiplyScalar(L),F.distance=U,F.coneCos=Math.cos(C.angle),F.penumbraCos=Math.cos(C.angle*(1-C.penumbra)),F.decay=C.decay,i.spot[g]=F;const N=C.shadow;if(C.map&&(i.spotLightMap[E]=C.map,E++,N.updateMatrices(C),C.castShadow&&M++),i.spotLightMatrix[g]=N.matrix,C.castShadow){const Y=t.get(C);Y.shadowIntensity=N.intensity,Y.shadowBias=N.bias,Y.shadowNormalBias=N.normalBias,Y.shadowRadius=N.radius,Y.shadowMapSize=N.mapSize,i.spotShadow[g]=Y,i.spotShadowMap[g]=I,S++}g++}else if(C.isRectAreaLight){const F=e.get(C);F.color.copy(R).multiplyScalar(L),F.halfWidth.set(C.width*.5,0,0),F.halfHeight.set(0,C.height*.5,0),i.rectArea[p]=F,p++}else if(C.isPointLight){const F=e.get(C);if(F.color.copy(C.color).multiplyScalar(C.intensity),F.distance=C.distance,F.decay=C.decay,C.castShadow){const N=C.shadow,Y=t.get(C);Y.shadowIntensity=N.intensity,Y.shadowBias=N.bias,Y.shadowNormalBias=N.normalBias,Y.shadowRadius=N.radius,Y.shadowMapSize=N.mapSize,Y.shadowCameraNear=N.camera.near,Y.shadowCameraFar=N.camera.far,i.pointShadow[m]=Y,i.pointShadowMap[m]=I,i.pointShadowMatrix[m]=C.shadow.matrix,b++}i.point[m]=F,m++}else if(C.isHemisphereLight){const F=e.get(C);F.skyColor.copy(C.color).multiplyScalar(L),F.groundColor.copy(C.groundColor).multiplyScalar(L),i.hemi[_]=F,_++}}p>0&&(n.has("OES_texture_float_linear")===!0?(i.rectAreaLTC1=Ge.LTC_FLOAT_1,i.rectAreaLTC2=Ge.LTC_FLOAT_2):(i.rectAreaLTC1=Ge.LTC_HALF_1,i.rectAreaLTC2=Ge.LTC_HALF_2)),i.ambient[0]=u,i.ambient[1]=f,i.ambient[2]=h;const x=i.hash;(x.directionalLength!==d||x.pointLength!==m||x.spotLength!==g||x.rectAreaLength!==p||x.hemiLength!==_||x.numDirectionalShadows!==v||x.numPointShadows!==b||x.numSpotShadows!==S||x.numSpotMaps!==E||x.numLightProbes!==T)&&(i.directional.length=d,i.spot.length=g,i.rectArea.length=p,i.point.length=m,i.hemi.length=_,i.directionalShadow.length=v,i.directionalShadowMap.length=v,i.pointShadow.length=b,i.pointShadowMap.length=b,i.spotShadow.length=S,i.spotShadowMap.length=S,i.directionalShadowMatrix.length=v,i.pointShadowMatrix.length=b,i.spotLightMatrix.length=S+E-M,i.spotLightMap.length=E,i.numSpotLightShadowsWithMaps=M,i.numLightProbes=T,x.directionalLength=d,x.pointLength=m,x.spotLength=g,x.rectAreaLength=p,x.hemiLength=_,x.numDirectionalShadows=v,x.numPointShadows=b,x.numSpotShadows=S,x.numSpotMaps=E,x.numLightProbes=T,i.version=SM++)}function l(c,u){let f=0,h=0,d=0,m=0,g=0;const p=u.matrixWorldInverse;for(let _=0,v=c.length;_<v;_++){const b=c[_];if(b.isDirectionalLight){const S=i.directional[f];S.direction.setFromMatrixPosition(b.matrixWorld),r.setFromMatrixPosition(b.target.matrixWorld),S.direction.sub(r),S.direction.transformDirection(p),f++}else if(b.isSpotLight){const S=i.spot[d];S.position.setFromMatrixPosition(b.matrixWorld),S.position.applyMatrix4(p),S.direction.setFromMatrixPosition(b.matrixWorld),r.setFromMatrixPosition(b.target.matrixWorld),S.direction.sub(r),S.direction.transformDirection(p),d++}else if(b.isRectAreaLight){const S=i.rectArea[m];S.position.setFromMatrixPosition(b.matrixWorld),S.position.applyMatrix4(p),a.identity(),s.copy(b.matrixWorld),s.premultiply(p),a.extractRotation(s),S.halfWidth.set(b.width*.5,0,0),S.halfHeight.set(0,b.height*.5,0),S.halfWidth.applyMatrix4(a),S.halfHeight.applyMatrix4(a),m++}else if(b.isPointLight){const S=i.point[h];S.position.setFromMatrixPosition(b.matrixWorld),S.position.applyMatrix4(p),h++}else if(b.isHemisphereLight){const S=i.hemi[g];S.direction.setFromMatrixPosition(b.matrixWorld),S.direction.transformDirection(p),g++}}}return{setup:o,setupView:l,state:i}}function op(n){const e=new EM(n),t=[],i=[],r=[];function s(h){f.camera=h,t.length=0,i.length=0,r.length=0}function a(h){t.push(h)}function o(h){i.push(h)}function l(h){r.push(h)}function c(){e.setup(t)}function u(h){e.setupView(t,h)}const f={lightsArray:t,shadowsArray:i,lightProbeGridArray:r,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:s,state:f,setupLights:c,setupLightsView:u,pushLight:a,pushShadow:o,pushLightProbeGrid:l}}function wM(n){let e=new WeakMap;function t(r,s=0){const a=e.get(r);let o;return a===void 0?(o=new op(n),e.set(r,[o])):s>=a.length?(o=new op(n),a.push(o)):o=a[s],o}function i(){e=new WeakMap}return{get:t,dispose:i}}const AM=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,RM=`uniform sampler2D shadow_pass;
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
}`,CM=[new $(1,0,0),new $(-1,0,0),new $(0,1,0),new $(0,-1,0),new $(0,0,1),new $(0,0,-1)],PM=[new $(0,-1,0),new $(0,-1,0),new $(0,0,1),new $(0,0,-1),new $(0,-1,0),new $(0,-1,0)],lp=new zt,Ta=new $,Hc=new $;function DM(n,e,t){let i=new Ym;const r=new Xe,s=new Xe,a=new Ut,o=new Jm,l=new Qm,c={},u=t.maxTextureSize,f={[ji]:on,[on]:ji,[An]:An},h=new ln({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Xe},radius:{value:4}},vertexShader:AM,fragmentShader:RM}),d=h.clone();d.defines.HORIZONTAL_PASS=1;const m=new Rt;m.setAttribute("position",new Nt(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const g=new Yn(m,h),p=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Ko;let _=this.type;this.render=function(M,T,x){if(p.enabled===!1||p.autoUpdate===!1&&p.needsUpdate===!1||M.length===0)return;this.type===P_&&(Qe("WebGLShadowMap: PCFSoftShadowMap has been deprecated. Using PCFShadowMap instead."),this.type=Ko);const y=n.getRenderTarget(),w=n.getActiveCubeFace(),C=n.getActiveMipmapLevel(),R=n.state;R.setBlending(Sn),R.buffers.depth.getReversed()===!0?R.buffers.color.setClear(0,0,0,0):R.buffers.color.setClear(1,1,1,1),R.buffers.depth.setTest(!0),R.setScissorTest(!1);const L=_!==this.type;L&&T.traverse(function(U){U.material&&(Array.isArray(U.material)?U.material.forEach(I=>I.needsUpdate=!0):U.material.needsUpdate=!0)});for(let U=0,I=M.length;U<I;U++){const F=M[U],N=F.shadow;if(N===void 0){Qe("WebGLShadowMap:",F,"has no shadow.");continue}if(N.autoUpdate===!1&&N.needsUpdate===!1)continue;r.copy(N.mapSize);const Y=N.getFrameExtents();r.multiply(Y),s.copy(N.mapSize),(r.x>u||r.y>u)&&(r.x>u&&(s.x=Math.floor(u/Y.x),r.x=s.x*Y.x,N.mapSize.x=s.x),r.y>u&&(s.y=Math.floor(u/Y.y),r.y=s.y*Y.y,N.mapSize.y=s.y));const j=n.state.buffers.depth.getReversed();if(N.camera._reversedDepth=j,N.map===null||L===!0){if(N.map!==null&&(N.map.depthTexture!==null&&(N.map.depthTexture.dispose(),N.map.depthTexture=null),N.map.dispose()),this.type===Ra){if(F.isPointLight){Qe("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}N.map=new Qt(r.x,r.y,{format:Jr,type:Yi,minFilter:Gt,magFilter:Gt,generateMipmaps:!1}),N.map.texture.name=F.name+".shadowMap",N.map.depthTexture=new Xi(r.x,r.y,fi),N.map.depthTexture.name=F.name+".shadowMapDepth",N.map.depthTexture.format=qi,N.map.depthTexture.compareFunction=null,N.map.depthTexture.minFilter=hn,N.map.depthTexture.magFilter=hn}else F.isPointLight?(N.map=new i0(r.x),N.map.depthTexture=new kv(r.x,Ui)):(N.map=new Qt(r.x,r.y),N.map.depthTexture=new Xi(r.x,r.y,Ui)),N.map.depthTexture.name=F.name+".shadowMap",N.map.depthTexture.format=qi,this.type===Ko?(N.map.depthTexture.compareFunction=j?nf:tf,N.map.depthTexture.minFilter=Gt,N.map.depthTexture.magFilter=Gt):(N.map.depthTexture.compareFunction=null,N.map.depthTexture.minFilter=hn,N.map.depthTexture.magFilter=hn);N.camera.updateProjectionMatrix()}const Z=N.map.isWebGLCubeRenderTarget?6:1;for(let O=0;O<Z;O++){if(N.map.isWebGLCubeRenderTarget)n.setRenderTarget(N.map,O),n.clear();else{O===0&&(n.setRenderTarget(N.map),n.clear());const H=N.getViewport(O);a.set(s.x*H.x,s.y*H.y,s.x*H.z,s.y*H.w),R.viewport(a)}if(F.isPointLight){const H=N.camera,B=N.matrix,V=F.distance||H.far;V!==H.far&&(H.far=V,H.updateProjectionMatrix()),Ta.setFromMatrixPosition(F.matrixWorld),H.position.copy(Ta),Hc.copy(H.position),Hc.add(CM[O]),H.up.copy(PM[O]),H.lookAt(Hc),H.updateMatrixWorld(),B.makeTranslation(-Ta.x,-Ta.y,-Ta.z),lp.multiplyMatrices(H.projectionMatrix,H.matrixWorldInverse),N._frustum.setFromProjectionMatrix(lp,H.coordinateSystem,H.reversedDepth)}else N.updateMatrices(F);i=N.getFrustum(),S(T,x,N.camera,F,this.type)}N.isPointLightShadow!==!0&&this.type===Ra&&v(N,x),N.needsUpdate=!1}_=this.type,p.needsUpdate=!1,n.setRenderTarget(y,w,C)};function v(M,T){const x=e.update(g);h.defines.VSM_SAMPLES!==M.blurSamples&&(h.defines.VSM_SAMPLES=M.blurSamples,d.defines.VSM_SAMPLES=M.blurSamples,h.needsUpdate=!0,d.needsUpdate=!0),M.mapPass===null&&(M.mapPass=new Qt(r.x,r.y,{format:Jr,type:Yi})),h.uniforms.shadow_pass.value=M.map.depthTexture,h.uniforms.resolution.value=M.mapSize,h.uniforms.radius.value=M.radius,n.setRenderTarget(M.mapPass),n.clear(),n.renderBufferDirect(T,null,x,h,g,null),d.uniforms.shadow_pass.value=M.mapPass.texture,d.uniforms.resolution.value=M.mapSize,d.uniforms.radius.value=M.radius,n.setRenderTarget(M.map),n.clear(),n.renderBufferDirect(T,null,x,d,g,null)}function b(M,T,x,y){let w=null;const C=x.isPointLight===!0?M.customDistanceMaterial:M.customDepthMaterial;if(C!==void 0)w=C;else if(w=x.isPointLight===!0?l:o,n.localClippingEnabled&&T.clipShadows===!0&&Array.isArray(T.clippingPlanes)&&T.clippingPlanes.length!==0||T.displacementMap&&T.displacementScale!==0||T.alphaMap&&T.alphaTest>0||T.map&&T.alphaTest>0||T.alphaToCoverage===!0){const R=w.uuid,L=T.uuid;let U=c[R];U===void 0&&(U={},c[R]=U);let I=U[L];I===void 0&&(I=w.clone(),U[L]=I,T.addEventListener("dispose",E)),w=I}if(w.visible=T.visible,w.wireframe=T.wireframe,y===Ra?w.side=T.shadowSide!==null?T.shadowSide:T.side:w.side=T.shadowSide!==null?T.shadowSide:f[T.side],w.alphaMap=T.alphaMap,w.alphaTest=T.alphaToCoverage===!0?.5:T.alphaTest,w.map=T.map,w.clipShadows=T.clipShadows,w.clippingPlanes=T.clippingPlanes,w.clipIntersection=T.clipIntersection,w.displacementMap=T.displacementMap,w.displacementScale=T.displacementScale,w.displacementBias=T.displacementBias,w.wireframeLinewidth=T.wireframeLinewidth,w.linewidth=T.linewidth,x.isPointLight===!0&&w.isMeshDistanceMaterial===!0){const R=n.properties.get(w);R.light=x}return w}function S(M,T,x,y,w){if(M.visible===!1)return;if(M.layers.test(T.layers)&&(M.isMesh||M.isLine||M.isPoints)&&(M.castShadow||M.receiveShadow&&w===Ra)&&(!M.frustumCulled||i.intersectsObject(M))){M.modelViewMatrix.multiplyMatrices(x.matrixWorldInverse,M.matrixWorld);const L=e.update(M),U=M.material;if(Array.isArray(U)){const I=L.groups;for(let F=0,N=I.length;F<N;F++){const Y=I[F],j=U[Y.materialIndex];if(j&&j.visible){const Z=b(M,j,y,w);M.onBeforeShadow(n,M,T,x,L,Z,Y),n.renderBufferDirect(x,null,L,Z,M,Y),M.onAfterShadow(n,M,T,x,L,Z,Y)}}}else if(U.visible){const I=b(M,U,y,w);M.onBeforeShadow(n,M,T,x,L,I,null),n.renderBufferDirect(x,null,L,I,M,null),M.onAfterShadow(n,M,T,x,L,I,null)}}const R=M.children;for(let L=0,U=R.length;L<U;L++)S(R[L],T,x,y,w)}function E(M){M.target.removeEventListener("dispose",E);for(const x in c){const y=c[x],w=M.target.uuid;w in y&&(y[w].dispose(),delete y[w])}}}function UM(n,e){function t(){let K=!1;const ve=new Ut;let oe=null;const Le=new Ut(0,0,0,0);return{setMask:function(Se){oe!==Se&&!K&&(n.colorMask(Se,Se,Se,Se),oe=Se)},setLocked:function(Se){K=Se},setClear:function(Se,fe,Oe,$e,ot){ot===!0&&(Se*=$e,fe*=$e,Oe*=$e),ve.set(Se,fe,Oe,$e),Le.equals(ve)===!1&&(n.clearColor(Se,fe,Oe,$e),Le.copy(ve))},reset:function(){K=!1,oe=null,Le.set(-1,0,0,0)}}}function i(){let K=!1,ve=!1,oe=null,Le=null,Se=null;return{setReversed:function(fe){if(ve!==fe){const Oe=e.get("EXT_clip_control");fe?Oe.clipControlEXT(Oe.LOWER_LEFT_EXT,Oe.ZERO_TO_ONE_EXT):Oe.clipControlEXT(Oe.LOWER_LEFT_EXT,Oe.NEGATIVE_ONE_TO_ONE_EXT),ve=fe;const $e=Se;Se=null,this.setClear($e)}},getReversed:function(){return ve},setTest:function(fe){fe?q(n.DEPTH_TEST):ce(n.DEPTH_TEST)},setMask:function(fe){oe!==fe&&!K&&(n.depthMask(fe),oe=fe)},setFunc:function(fe){if(ve&&(fe=cv[fe]),Le!==fe){switch(fe){case Du:n.depthFunc(n.NEVER);break;case cl:n.depthFunc(n.ALWAYS);break;case Uu:n.depthFunc(n.LESS);break;case zs:n.depthFunc(n.LEQUAL);break;case Lu:n.depthFunc(n.EQUAL);break;case Iu:n.depthFunc(n.GEQUAL);break;case Fu:n.depthFunc(n.GREATER);break;case Nu:n.depthFunc(n.NOTEQUAL);break;default:n.depthFunc(n.LEQUAL)}Le=fe}},setLocked:function(fe){K=fe},setClear:function(fe){Se!==fe&&(Se=fe,ve&&(fe=1-fe),n.clearDepth(fe))},reset:function(){K=!1,oe=null,Le=null,Se=null,ve=!1}}}function r(){let K=!1,ve=null,oe=null,Le=null,Se=null,fe=null,Oe=null,$e=null,ot=null;return{setTest:function(tt){K||(tt?q(n.STENCIL_TEST):ce(n.STENCIL_TEST))},setMask:function(tt){ve!==tt&&!K&&(n.stencilMask(tt),ve=tt)},setFunc:function(tt,Vt,Kt){(oe!==tt||Le!==Vt||Se!==Kt)&&(n.stencilFunc(tt,Vt,Kt),oe=tt,Le=Vt,Se=Kt)},setOp:function(tt,Vt,Kt){(fe!==tt||Oe!==Vt||$e!==Kt)&&(n.stencilOp(tt,Vt,Kt),fe=tt,Oe=Vt,$e=Kt)},setLocked:function(tt){K=tt},setClear:function(tt){ot!==tt&&(n.clearStencil(tt),ot=tt)},reset:function(){K=!1,ve=null,oe=null,Le=null,Se=null,fe=null,Oe=null,$e=null,ot=null}}}const s=new t,a=new i,o=new r,l=new WeakMap,c=new WeakMap;let u={},f={},h={},d=new WeakMap,m=[],g=null,p=!1,_=null,v=null,b=null,S=null,E=null,M=null,T=null,x=new ut(0,0,0),y=0,w=!1,C=null,R=null,L=null,U=null,I=null;const F=n.getParameter(n.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let N=!1,Y=0;const j=n.getParameter(n.VERSION);j.indexOf("WebGL")!==-1?(Y=parseFloat(/^WebGL (\d)/.exec(j)[1]),N=Y>=1):j.indexOf("OpenGL ES")!==-1&&(Y=parseFloat(/^OpenGL ES (\d)/.exec(j)[1]),N=Y>=2);let Z=null,O={};const H=n.getParameter(n.SCISSOR_BOX),B=n.getParameter(n.VIEWPORT),V=new Ut().fromArray(H),G=new Ut().fromArray(B);function z(K,ve,oe,Le){const Se=new Uint8Array(4),fe=n.createTexture();n.bindTexture(K,fe),n.texParameteri(K,n.TEXTURE_MIN_FILTER,n.NEAREST),n.texParameteri(K,n.TEXTURE_MAG_FILTER,n.NEAREST);for(let Oe=0;Oe<oe;Oe++)K===n.TEXTURE_3D||K===n.TEXTURE_2D_ARRAY?n.texImage3D(ve,0,n.RGBA,1,1,Le,0,n.RGBA,n.UNSIGNED_BYTE,Se):n.texImage2D(ve+Oe,0,n.RGBA,1,1,0,n.RGBA,n.UNSIGNED_BYTE,Se);return fe}const W={};W[n.TEXTURE_2D]=z(n.TEXTURE_2D,n.TEXTURE_2D,1),W[n.TEXTURE_CUBE_MAP]=z(n.TEXTURE_CUBE_MAP,n.TEXTURE_CUBE_MAP_POSITIVE_X,6),W[n.TEXTURE_2D_ARRAY]=z(n.TEXTURE_2D_ARRAY,n.TEXTURE_2D_ARRAY,1,1),W[n.TEXTURE_3D]=z(n.TEXTURE_3D,n.TEXTURE_3D,1,1),s.setClear(0,0,0,1),a.setClear(1),o.setClear(0),q(n.DEPTH_TEST),a.setFunc(zs),Ne(!1),ae(sd),q(n.CULL_FACE),ye(Sn);function q(K){u[K]!==!0&&(n.enable(K),u[K]=!0)}function ce(K){u[K]!==!1&&(n.disable(K),u[K]=!1)}function me(K,ve){return h[K]!==ve?(n.bindFramebuffer(K,ve),h[K]=ve,K===n.DRAW_FRAMEBUFFER&&(h[n.FRAMEBUFFER]=ve),K===n.FRAMEBUFFER&&(h[n.DRAW_FRAMEBUFFER]=ve),!0):!1}function Q(K,ve){let oe=m,Le=!1;if(K){oe=d.get(ve),oe===void 0&&(oe=[],d.set(ve,oe));const Se=K.textures;if(oe.length!==Se.length||oe[0]!==n.COLOR_ATTACHMENT0){for(let fe=0,Oe=Se.length;fe<Oe;fe++)oe[fe]=n.COLOR_ATTACHMENT0+fe;oe.length=Se.length,Le=!0}}else oe[0]!==n.BACK&&(oe[0]=n.BACK,Le=!0);Le&&n.drawBuffers(oe)}function ie(K){return g!==K?(n.useProgram(K),g=K,!0):!1}const be={[kr]:n.FUNC_ADD,[U_]:n.FUNC_SUBTRACT,[L_]:n.FUNC_REVERSE_SUBTRACT};be[I_]=n.MIN,be[F_]=n.MAX;const De={[N_]:n.ZERO,[O_]:n.ONE,[B_]:n.SRC_COLOR,[Cu]:n.SRC_ALPHA,[W_]:n.SRC_ALPHA_SATURATE,[H_]:n.DST_COLOR,[z_]:n.DST_ALPHA,[k_]:n.ONE_MINUS_SRC_COLOR,[Pu]:n.ONE_MINUS_SRC_ALPHA,[V_]:n.ONE_MINUS_DST_COLOR,[G_]:n.ONE_MINUS_DST_ALPHA,[X_]:n.CONSTANT_COLOR,[j_]:n.ONE_MINUS_CONSTANT_COLOR,[Y_]:n.CONSTANT_ALPHA,[q_]:n.ONE_MINUS_CONSTANT_ALPHA};function ye(K,ve,oe,Le,Se,fe,Oe,$e,ot,tt){if(K===Sn){p===!0&&(ce(n.BLEND),p=!1);return}if(p===!1&&(q(n.BLEND),p=!0),K!==D_){if(K!==_||tt!==w){if((v!==kr||E!==kr)&&(n.blendEquation(n.FUNC_ADD),v=kr,E=kr),tt)switch(K){case Vr:n.blendFuncSeparate(n.ONE,n.ONE_MINUS_SRC_ALPHA,n.ONE,n.ONE_MINUS_SRC_ALPHA);break;case ll:n.blendFunc(n.ONE,n.ONE);break;case ad:n.blendFuncSeparate(n.ZERO,n.ONE_MINUS_SRC_COLOR,n.ZERO,n.ONE);break;case od:n.blendFuncSeparate(n.DST_COLOR,n.ONE_MINUS_SRC_ALPHA,n.ZERO,n.ONE);break;default:pt("WebGLState: Invalid blending: ",K);break}else switch(K){case Vr:n.blendFuncSeparate(n.SRC_ALPHA,n.ONE_MINUS_SRC_ALPHA,n.ONE,n.ONE_MINUS_SRC_ALPHA);break;case ll:n.blendFuncSeparate(n.SRC_ALPHA,n.ONE,n.ONE,n.ONE);break;case ad:pt("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case od:pt("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:pt("WebGLState: Invalid blending: ",K);break}b=null,S=null,M=null,T=null,x.set(0,0,0),y=0,_=K,w=tt}return}Se=Se||ve,fe=fe||oe,Oe=Oe||Le,(ve!==v||Se!==E)&&(n.blendEquationSeparate(be[ve],be[Se]),v=ve,E=Se),(oe!==b||Le!==S||fe!==M||Oe!==T)&&(n.blendFuncSeparate(De[oe],De[Le],De[fe],De[Oe]),b=oe,S=Le,M=fe,T=Oe),($e.equals(x)===!1||ot!==y)&&(n.blendColor($e.r,$e.g,$e.b,ot),x.copy($e),y=ot),_=K,w=!1}function _e(K,ve){K.side===An?ce(n.CULL_FACE):q(n.CULL_FACE);let oe=K.side===on;ve&&(oe=!oe),Ne(oe),K.blending===Vr&&K.transparent===!1?ye(Sn):ye(K.blending,K.blendEquation,K.blendSrc,K.blendDst,K.blendEquationAlpha,K.blendSrcAlpha,K.blendDstAlpha,K.blendColor,K.blendAlpha,K.premultipliedAlpha),a.setFunc(K.depthFunc),a.setTest(K.depthTest),a.setMask(K.depthWrite),s.setMask(K.colorWrite);const Le=K.stencilWrite;o.setTest(Le),Le&&(o.setMask(K.stencilWriteMask),o.setFunc(K.stencilFunc,K.stencilRef,K.stencilFuncMask),o.setOp(K.stencilFail,K.stencilZFail,K.stencilZPass)),k(K.polygonOffset,K.polygonOffsetFactor,K.polygonOffsetUnits),K.alphaToCoverage===!0?q(n.SAMPLE_ALPHA_TO_COVERAGE):ce(n.SAMPLE_ALPHA_TO_COVERAGE)}function Ne(K){C!==K&&(K?n.frontFace(n.CW):n.frontFace(n.CCW),C=K)}function ae(K){K!==R_?(q(n.CULL_FACE),K!==R&&(K===sd?n.cullFace(n.BACK):K===C_?n.cullFace(n.FRONT):n.cullFace(n.FRONT_AND_BACK))):ce(n.CULL_FACE),R=K}function Ee(K){K!==L&&(N&&n.lineWidth(K),L=K)}function k(K,ve,oe){K?(q(n.POLYGON_OFFSET_FILL),(U!==ve||I!==oe)&&(U=ve,I=oe,a.getReversed()&&(ve=-ve),n.polygonOffset(ve,oe))):ce(n.POLYGON_OFFSET_FILL)}function de(K){K?q(n.SCISSOR_TEST):ce(n.SCISSOR_TEST)}function Pe(K){K===void 0&&(K=n.TEXTURE0+F-1),Z!==K&&(n.activeTexture(K),Z=K)}function we(K,ve,oe){oe===void 0&&(Z===null?oe=n.TEXTURE0+F-1:oe=Z);let Le=O[oe];Le===void 0&&(Le={type:void 0,texture:void 0},O[oe]=Le),(Le.type!==K||Le.texture!==ve)&&(Z!==oe&&(n.activeTexture(oe),Z=oe),n.bindTexture(K,ve||W[K]),Le.type=K,Le.texture=ve)}function pe(){const K=O[Z];K!==void 0&&K.type!==void 0&&(n.bindTexture(K.type,null),K.type=void 0,K.texture=void 0)}function Re(){try{n.compressedTexImage2D(...arguments)}catch(K){pt("WebGLState:",K)}}function D(){try{n.compressedTexImage3D(...arguments)}catch(K){pt("WebGLState:",K)}}function A(){try{n.texSubImage2D(...arguments)}catch(K){pt("WebGLState:",K)}}function X(){try{n.texSubImage3D(...arguments)}catch(K){pt("WebGLState:",K)}}function ee(){try{n.compressedTexSubImage2D(...arguments)}catch(K){pt("WebGLState:",K)}}function he(){try{n.compressedTexSubImage3D(...arguments)}catch(K){pt("WebGLState:",K)}}function xe(){try{n.texStorage2D(...arguments)}catch(K){pt("WebGLState:",K)}}function Te(){try{n.texStorage3D(...arguments)}catch(K){pt("WebGLState:",K)}}function te(){try{n.texImage2D(...arguments)}catch(K){pt("WebGLState:",K)}}function le(){try{n.texImage3D(...arguments)}catch(K){pt("WebGLState:",K)}}function ge(K){return f[K]!==void 0?f[K]:n.getParameter(K)}function Ie(K,ve){f[K]!==ve&&(n.pixelStorei(K,ve),f[K]=ve)}function Me(K){V.equals(K)===!1&&(n.scissor(K.x,K.y,K.z,K.w),V.copy(K))}function Ae(K){G.equals(K)===!1&&(n.viewport(K.x,K.y,K.z,K.w),G.copy(K))}function He(K,ve){let oe=c.get(ve);oe===void 0&&(oe=new WeakMap,c.set(ve,oe));let Le=oe.get(K);Le===void 0&&(Le=n.getUniformBlockIndex(ve,K.name),oe.set(K,Le))}function Fe(K,ve){const Le=c.get(ve).get(K);l.get(ve)!==Le&&(n.uniformBlockBinding(ve,Le,K.__bindingPointIndex),l.set(ve,Le))}function Ye(){n.disable(n.BLEND),n.disable(n.CULL_FACE),n.disable(n.DEPTH_TEST),n.disable(n.POLYGON_OFFSET_FILL),n.disable(n.SCISSOR_TEST),n.disable(n.STENCIL_TEST),n.disable(n.SAMPLE_ALPHA_TO_COVERAGE),n.blendEquation(n.FUNC_ADD),n.blendFunc(n.ONE,n.ZERO),n.blendFuncSeparate(n.ONE,n.ZERO,n.ONE,n.ZERO),n.blendColor(0,0,0,0),n.colorMask(!0,!0,!0,!0),n.clearColor(0,0,0,0),n.depthMask(!0),n.depthFunc(n.LESS),a.setReversed(!1),n.clearDepth(1),n.stencilMask(4294967295),n.stencilFunc(n.ALWAYS,0,4294967295),n.stencilOp(n.KEEP,n.KEEP,n.KEEP),n.clearStencil(0),n.cullFace(n.BACK),n.frontFace(n.CCW),n.polygonOffset(0,0),n.activeTexture(n.TEXTURE0),n.bindFramebuffer(n.FRAMEBUFFER,null),n.bindFramebuffer(n.DRAW_FRAMEBUFFER,null),n.bindFramebuffer(n.READ_FRAMEBUFFER,null),n.useProgram(null),n.lineWidth(1),n.scissor(0,0,n.canvas.width,n.canvas.height),n.viewport(0,0,n.canvas.width,n.canvas.height),n.pixelStorei(n.PACK_ALIGNMENT,4),n.pixelStorei(n.UNPACK_ALIGNMENT,4),n.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,!1),n.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),n.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,n.BROWSER_DEFAULT_WEBGL),n.pixelStorei(n.PACK_ROW_LENGTH,0),n.pixelStorei(n.PACK_SKIP_PIXELS,0),n.pixelStorei(n.PACK_SKIP_ROWS,0),n.pixelStorei(n.UNPACK_ROW_LENGTH,0),n.pixelStorei(n.UNPACK_IMAGE_HEIGHT,0),n.pixelStorei(n.UNPACK_SKIP_PIXELS,0),n.pixelStorei(n.UNPACK_SKIP_ROWS,0),n.pixelStorei(n.UNPACK_SKIP_IMAGES,0),u={},f={},Z=null,O={},h={},d=new WeakMap,m=[],g=null,p=!1,_=null,v=null,b=null,S=null,E=null,M=null,T=null,x=new ut(0,0,0),y=0,w=!1,C=null,R=null,L=null,U=null,I=null,V.set(0,0,n.canvas.width,n.canvas.height),G.set(0,0,n.canvas.width,n.canvas.height),s.reset(),a.reset(),o.reset()}return{buffers:{color:s,depth:a,stencil:o},enable:q,disable:ce,bindFramebuffer:me,drawBuffers:Q,useProgram:ie,setBlending:ye,setMaterial:_e,setFlipSided:Ne,setCullFace:ae,setLineWidth:Ee,setPolygonOffset:k,setScissorTest:de,activeTexture:Pe,bindTexture:we,unbindTexture:pe,compressedTexImage2D:Re,compressedTexImage3D:D,texImage2D:te,texImage3D:le,pixelStorei:Ie,getParameter:ge,updateUBOMapping:He,uniformBlockBinding:Fe,texStorage2D:xe,texStorage3D:Te,texSubImage2D:A,texSubImage3D:X,compressedTexSubImage2D:ee,compressedTexSubImage3D:he,scissor:Me,viewport:Ae,reset:Ye}}function LM(n,e,t,i,r,s,a){const o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new Xe,u=new WeakMap,f=new Set;let h;const d=new WeakMap;let m=!1;try{m=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function g(D,A){return m?new OffscreenCanvas(D,A):pl("canvas")}function p(D,A,X){let ee=1;const he=Re(D);if((he.width>X||he.height>X)&&(ee=X/Math.max(he.width,he.height)),ee<1)if(typeof HTMLImageElement<"u"&&D instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&D instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&D instanceof ImageBitmap||typeof VideoFrame<"u"&&D instanceof VideoFrame){const xe=Math.floor(ee*he.width),Te=Math.floor(ee*he.height);h===void 0&&(h=g(xe,Te));const te=A?g(xe,Te):h;return te.width=xe,te.height=Te,te.getContext("2d").drawImage(D,0,0,xe,Te),Qe("WebGLRenderer: Texture has been resized from ("+he.width+"x"+he.height+") to ("+xe+"x"+Te+")."),te}else return"data"in D&&Qe("WebGLRenderer: Image in DataTexture is too big ("+he.width+"x"+he.height+")."),D;return D}function _(D){return D.generateMipmaps}function v(D){n.generateMipmap(D)}function b(D){return D.isWebGLCubeRenderTarget?n.TEXTURE_CUBE_MAP:D.isWebGL3DRenderTarget?n.TEXTURE_3D:D.isWebGLArrayRenderTarget||D.isCompressedArrayTexture?n.TEXTURE_2D_ARRAY:n.TEXTURE_2D}function S(D,A,X,ee,he,xe=!1){if(D!==null){if(n[D]!==void 0)return n[D];Qe("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+D+"'")}let Te;ee&&(Te=e.get("EXT_texture_norm16"),Te||Qe("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let te=A;if(A===n.RED&&(X===n.FLOAT&&(te=n.R32F),X===n.HALF_FLOAT&&(te=n.R16F),X===n.UNSIGNED_BYTE&&(te=n.R8),X===n.UNSIGNED_SHORT&&Te&&(te=Te.R16_EXT),X===n.SHORT&&Te&&(te=Te.R16_SNORM_EXT)),A===n.RED_INTEGER&&(X===n.UNSIGNED_BYTE&&(te=n.R8UI),X===n.UNSIGNED_SHORT&&(te=n.R16UI),X===n.UNSIGNED_INT&&(te=n.R32UI),X===n.BYTE&&(te=n.R8I),X===n.SHORT&&(te=n.R16I),X===n.INT&&(te=n.R32I)),A===n.RG&&(X===n.FLOAT&&(te=n.RG32F),X===n.HALF_FLOAT&&(te=n.RG16F),X===n.UNSIGNED_BYTE&&(te=n.RG8),X===n.UNSIGNED_SHORT&&Te&&(te=Te.RG16_EXT),X===n.SHORT&&Te&&(te=Te.RG16_SNORM_EXT)),A===n.RG_INTEGER&&(X===n.UNSIGNED_BYTE&&(te=n.RG8UI),X===n.UNSIGNED_SHORT&&(te=n.RG16UI),X===n.UNSIGNED_INT&&(te=n.RG32UI),X===n.BYTE&&(te=n.RG8I),X===n.SHORT&&(te=n.RG16I),X===n.INT&&(te=n.RG32I)),A===n.RGB_INTEGER&&(X===n.UNSIGNED_BYTE&&(te=n.RGB8UI),X===n.UNSIGNED_SHORT&&(te=n.RGB16UI),X===n.UNSIGNED_INT&&(te=n.RGB32UI),X===n.BYTE&&(te=n.RGB8I),X===n.SHORT&&(te=n.RGB16I),X===n.INT&&(te=n.RGB32I)),A===n.RGBA_INTEGER&&(X===n.UNSIGNED_BYTE&&(te=n.RGBA8UI),X===n.UNSIGNED_SHORT&&(te=n.RGBA16UI),X===n.UNSIGNED_INT&&(te=n.RGBA32UI),X===n.BYTE&&(te=n.RGBA8I),X===n.SHORT&&(te=n.RGBA16I),X===n.INT&&(te=n.RGBA32I)),A===n.RGB&&(X===n.UNSIGNED_SHORT&&Te&&(te=Te.RGB16_EXT),X===n.SHORT&&Te&&(te=Te.RGB16_SNORM_EXT),X===n.UNSIGNED_INT_5_9_9_9_REV&&(te=n.RGB9_E5),X===n.UNSIGNED_INT_10F_11F_11F_REV&&(te=n.R11F_G11F_B10F)),A===n.RGBA){const le=xe?fl:ft.getTransfer(he);X===n.FLOAT&&(te=n.RGBA32F),X===n.HALF_FLOAT&&(te=n.RGBA16F),X===n.UNSIGNED_BYTE&&(te=le===bt?n.SRGB8_ALPHA8:n.RGBA8),X===n.UNSIGNED_SHORT&&Te&&(te=Te.RGBA16_EXT),X===n.SHORT&&Te&&(te=Te.RGBA16_SNORM_EXT),X===n.UNSIGNED_SHORT_4_4_4_4&&(te=n.RGBA4),X===n.UNSIGNED_SHORT_5_5_5_1&&(te=n.RGB5_A1)}return(te===n.R16F||te===n.R32F||te===n.RG16F||te===n.RG32F||te===n.RGBA16F||te===n.RGBA32F)&&e.get("EXT_color_buffer_float"),te}function E(D,A){let X;return D?A===null||A===Ui||A===Hs?X=n.DEPTH24_STENCIL8:A===fi?X=n.DEPTH32F_STENCIL8:A===Ha&&(X=n.DEPTH24_STENCIL8,Qe("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):A===null||A===Ui||A===Hs?X=n.DEPTH_COMPONENT24:A===fi?X=n.DEPTH_COMPONENT32F:A===Ha&&(X=n.DEPTH_COMPONENT16),X}function M(D,A){return _(D)===!0||D.isFramebufferTexture&&D.minFilter!==hn&&D.minFilter!==Gt?Math.log2(Math.max(A.width,A.height))+1:D.mipmaps!==void 0&&D.mipmaps.length>0?D.mipmaps.length:D.isCompressedTexture&&Array.isArray(D.image)?A.mipmaps.length:1}function T(D){const A=D.target;A.removeEventListener("dispose",T),y(A),A.isVideoTexture&&u.delete(A),A.isHTMLTexture&&f.delete(A)}function x(D){const A=D.target;A.removeEventListener("dispose",x),C(A)}function y(D){const A=i.get(D);if(A.__webglInit===void 0)return;const X=D.source,ee=d.get(X);if(ee){const he=ee[A.__cacheKey];he.usedTimes--,he.usedTimes===0&&w(D),Object.keys(ee).length===0&&d.delete(X)}i.remove(D)}function w(D){const A=i.get(D);n.deleteTexture(A.__webglTexture);const X=D.source,ee=d.get(X);delete ee[A.__cacheKey],a.memory.textures--}function C(D){const A=i.get(D);if(D.depthTexture&&(D.depthTexture.dispose(),i.remove(D.depthTexture)),D.isWebGLCubeRenderTarget)for(let ee=0;ee<6;ee++){if(Array.isArray(A.__webglFramebuffer[ee]))for(let he=0;he<A.__webglFramebuffer[ee].length;he++)n.deleteFramebuffer(A.__webglFramebuffer[ee][he]);else n.deleteFramebuffer(A.__webglFramebuffer[ee]);A.__webglDepthbuffer&&n.deleteRenderbuffer(A.__webglDepthbuffer[ee])}else{if(Array.isArray(A.__webglFramebuffer))for(let ee=0;ee<A.__webglFramebuffer.length;ee++)n.deleteFramebuffer(A.__webglFramebuffer[ee]);else n.deleteFramebuffer(A.__webglFramebuffer);if(A.__webglDepthbuffer&&n.deleteRenderbuffer(A.__webglDepthbuffer),A.__webglMultisampledFramebuffer&&n.deleteFramebuffer(A.__webglMultisampledFramebuffer),A.__webglColorRenderbuffer)for(let ee=0;ee<A.__webglColorRenderbuffer.length;ee++)A.__webglColorRenderbuffer[ee]&&n.deleteRenderbuffer(A.__webglColorRenderbuffer[ee]);A.__webglDepthRenderbuffer&&n.deleteRenderbuffer(A.__webglDepthRenderbuffer)}const X=D.textures;for(let ee=0,he=X.length;ee<he;ee++){const xe=i.get(X[ee]);xe.__webglTexture&&(n.deleteTexture(xe.__webglTexture),a.memory.textures--),i.remove(X[ee])}i.remove(D)}let R=0;function L(){R=0}function U(){return R}function I(D){R=D}function F(){const D=R;return D>=r.maxTextures&&Qe("WebGLTextures: Trying to use "+D+" texture units while this GPU supports only "+r.maxTextures),R+=1,D}function N(D){const A=[];return A.push(D.wrapS),A.push(D.wrapT),A.push(D.wrapR||0),A.push(D.magFilter),A.push(D.minFilter),A.push(D.anisotropy),A.push(D.internalFormat),A.push(D.format),A.push(D.type),A.push(D.generateMipmaps),A.push(D.premultiplyAlpha),A.push(D.flipY),A.push(D.unpackAlignment),A.push(D.colorSpace),A.join()}function Y(D,A){const X=i.get(D);if(D.isVideoTexture&&we(D),D.isRenderTargetTexture===!1&&D.isExternalTexture!==!0&&D.version>0&&X.__version!==D.version){const ee=D.image;if(ee===null)Qe("WebGLRenderer: Texture marked for update but no image data found.");else if(ee.complete===!1)Qe("WebGLRenderer: Texture marked for update but image is incomplete");else{ce(X,D,A);return}}else D.isExternalTexture&&(X.__webglTexture=D.sourceTexture?D.sourceTexture:null);t.bindTexture(n.TEXTURE_2D,X.__webglTexture,n.TEXTURE0+A)}function j(D,A){const X=i.get(D);if(D.isRenderTargetTexture===!1&&D.version>0&&X.__version!==D.version){ce(X,D,A);return}else D.isExternalTexture&&(X.__webglTexture=D.sourceTexture?D.sourceTexture:null);t.bindTexture(n.TEXTURE_2D_ARRAY,X.__webglTexture,n.TEXTURE0+A)}function Z(D,A){const X=i.get(D);if(D.isRenderTargetTexture===!1&&D.version>0&&X.__version!==D.version){ce(X,D,A);return}t.bindTexture(n.TEXTURE_3D,X.__webglTexture,n.TEXTURE0+A)}function O(D,A){const X=i.get(D);if(D.isCubeDepthTexture!==!0&&D.version>0&&X.__version!==D.version){me(X,D,A);return}t.bindTexture(n.TEXTURE_CUBE_MAP,X.__webglTexture,n.TEXTURE0+A)}const H={[Ou]:n.REPEAT,[Vi]:n.CLAMP_TO_EDGE,[Bu]:n.MIRRORED_REPEAT},B={[hn]:n.NEAREST,[$_]:n.NEAREST_MIPMAP_NEAREST,[uo]:n.NEAREST_MIPMAP_LINEAR,[Gt]:n.LINEAR,[uc]:n.LINEAR_MIPMAP_NEAREST,[Gr]:n.LINEAR_MIPMAP_LINEAR},V={[ev]:n.NEVER,[sv]:n.ALWAYS,[tv]:n.LESS,[tf]:n.LEQUAL,[nv]:n.EQUAL,[nf]:n.GEQUAL,[iv]:n.GREATER,[rv]:n.NOTEQUAL};function G(D,A){if(A.type===fi&&e.has("OES_texture_float_linear")===!1&&(A.magFilter===Gt||A.magFilter===uc||A.magFilter===uo||A.magFilter===Gr||A.minFilter===Gt||A.minFilter===uc||A.minFilter===uo||A.minFilter===Gr)&&Qe("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),n.texParameteri(D,n.TEXTURE_WRAP_S,H[A.wrapS]),n.texParameteri(D,n.TEXTURE_WRAP_T,H[A.wrapT]),(D===n.TEXTURE_3D||D===n.TEXTURE_2D_ARRAY)&&n.texParameteri(D,n.TEXTURE_WRAP_R,H[A.wrapR]),n.texParameteri(D,n.TEXTURE_MAG_FILTER,B[A.magFilter]),n.texParameteri(D,n.TEXTURE_MIN_FILTER,B[A.minFilter]),A.compareFunction&&(n.texParameteri(D,n.TEXTURE_COMPARE_MODE,n.COMPARE_REF_TO_TEXTURE),n.texParameteri(D,n.TEXTURE_COMPARE_FUNC,V[A.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(A.magFilter===hn||A.minFilter!==uo&&A.minFilter!==Gr||A.type===fi&&e.has("OES_texture_float_linear")===!1)return;if(A.anisotropy>1||i.get(A).__currentAnisotropy){const X=e.get("EXT_texture_filter_anisotropic");n.texParameterf(D,X.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(A.anisotropy,r.getMaxAnisotropy())),i.get(A).__currentAnisotropy=A.anisotropy}}}function z(D,A){let X=!1;D.__webglInit===void 0&&(D.__webglInit=!0,A.addEventListener("dispose",T));const ee=A.source;let he=d.get(ee);he===void 0&&(he={},d.set(ee,he));const xe=N(A);if(xe!==D.__cacheKey){he[xe]===void 0&&(he[xe]={texture:n.createTexture(),usedTimes:0},a.memory.textures++,X=!0),he[xe].usedTimes++;const Te=he[D.__cacheKey];Te!==void 0&&(he[D.__cacheKey].usedTimes--,Te.usedTimes===0&&w(A)),D.__cacheKey=xe,D.__webglTexture=he[xe].texture}return X}function W(D,A,X){return Math.floor(Math.floor(D/X)/A)}function q(D,A,X,ee){const xe=D.updateRanges;if(xe.length===0)t.texSubImage2D(n.TEXTURE_2D,0,0,0,A.width,A.height,X,ee,A.data);else{xe.sort((Ie,Me)=>Ie.start-Me.start);let Te=0;for(let Ie=1;Ie<xe.length;Ie++){const Me=xe[Te],Ae=xe[Ie],He=Me.start+Me.count,Fe=W(Ae.start,A.width,4),Ye=W(Me.start,A.width,4);Ae.start<=He+1&&Fe===Ye&&W(Ae.start+Ae.count-1,A.width,4)===Fe?Me.count=Math.max(Me.count,Ae.start+Ae.count-Me.start):(++Te,xe[Te]=Ae)}xe.length=Te+1;const te=t.getParameter(n.UNPACK_ROW_LENGTH),le=t.getParameter(n.UNPACK_SKIP_PIXELS),ge=t.getParameter(n.UNPACK_SKIP_ROWS);t.pixelStorei(n.UNPACK_ROW_LENGTH,A.width);for(let Ie=0,Me=xe.length;Ie<Me;Ie++){const Ae=xe[Ie],He=Math.floor(Ae.start/4),Fe=Math.ceil(Ae.count/4),Ye=He%A.width,K=Math.floor(He/A.width),ve=Fe,oe=1;t.pixelStorei(n.UNPACK_SKIP_PIXELS,Ye),t.pixelStorei(n.UNPACK_SKIP_ROWS,K),t.texSubImage2D(n.TEXTURE_2D,0,Ye,K,ve,oe,X,ee,A.data)}D.clearUpdateRanges(),t.pixelStorei(n.UNPACK_ROW_LENGTH,te),t.pixelStorei(n.UNPACK_SKIP_PIXELS,le),t.pixelStorei(n.UNPACK_SKIP_ROWS,ge)}}function ce(D,A,X){let ee=n.TEXTURE_2D;(A.isDataArrayTexture||A.isCompressedArrayTexture)&&(ee=n.TEXTURE_2D_ARRAY),A.isData3DTexture&&(ee=n.TEXTURE_3D);const he=z(D,A),xe=A.source;t.bindTexture(ee,D.__webglTexture,n.TEXTURE0+X);const Te=i.get(xe);if(xe.version!==Te.__version||he===!0){if(t.activeTexture(n.TEXTURE0+X),(typeof ImageBitmap<"u"&&A.image instanceof ImageBitmap)===!1){const oe=ft.getPrimaries(ft.workingColorSpace),Le=A.colorSpace===Ti?null:ft.getPrimaries(A.colorSpace),Se=A.colorSpace===Ti||oe===Le?n.NONE:n.BROWSER_DEFAULT_WEBGL;t.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,A.flipY),t.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,A.premultiplyAlpha),t.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,Se)}t.pixelStorei(n.UNPACK_ALIGNMENT,A.unpackAlignment);let le=p(A.image,!1,r.maxTextureSize);le=pe(A,le);const ge=s.convert(A.format,A.colorSpace),Ie=s.convert(A.type);let Me=S(A.internalFormat,ge,Ie,A.normalized,A.colorSpace,A.isVideoTexture);G(ee,A);let Ae;const He=A.mipmaps,Fe=A.isVideoTexture!==!0,Ye=Te.__version===void 0||he===!0,K=xe.dataReady,ve=M(A,le);if(A.isDepthTexture)Me=E(A.format===dr,A.type),Ye&&(Fe?t.texStorage2D(n.TEXTURE_2D,1,Me,le.width,le.height):t.texImage2D(n.TEXTURE_2D,0,Me,le.width,le.height,0,ge,Ie,null));else if(A.isDataTexture)if(He.length>0){Fe&&Ye&&t.texStorage2D(n.TEXTURE_2D,ve,Me,He[0].width,He[0].height);for(let oe=0,Le=He.length;oe<Le;oe++)Ae=He[oe],Fe?K&&t.texSubImage2D(n.TEXTURE_2D,oe,0,0,Ae.width,Ae.height,ge,Ie,Ae.data):t.texImage2D(n.TEXTURE_2D,oe,Me,Ae.width,Ae.height,0,ge,Ie,Ae.data);A.generateMipmaps=!1}else Fe?(Ye&&t.texStorage2D(n.TEXTURE_2D,ve,Me,le.width,le.height),K&&q(A,le,ge,Ie)):t.texImage2D(n.TEXTURE_2D,0,Me,le.width,le.height,0,ge,Ie,le.data);else if(A.isCompressedTexture)if(A.isCompressedArrayTexture){Fe&&Ye&&t.texStorage3D(n.TEXTURE_2D_ARRAY,ve,Me,He[0].width,He[0].height,le.depth);for(let oe=0,Le=He.length;oe<Le;oe++)if(Ae=He[oe],A.format!==di)if(ge!==null)if(Fe){if(K)if(A.layerUpdates.size>0){const Se=kd(Ae.width,Ae.height,A.format,A.type);for(const fe of A.layerUpdates){const Oe=Ae.data.subarray(fe*Se/Ae.data.BYTES_PER_ELEMENT,(fe+1)*Se/Ae.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(n.TEXTURE_2D_ARRAY,oe,0,0,fe,Ae.width,Ae.height,1,ge,Oe)}A.clearLayerUpdates()}else t.compressedTexSubImage3D(n.TEXTURE_2D_ARRAY,oe,0,0,0,Ae.width,Ae.height,le.depth,ge,Ae.data)}else t.compressedTexImage3D(n.TEXTURE_2D_ARRAY,oe,Me,Ae.width,Ae.height,le.depth,0,Ae.data,0,0);else Qe("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else Fe?K&&t.texSubImage3D(n.TEXTURE_2D_ARRAY,oe,0,0,0,Ae.width,Ae.height,le.depth,ge,Ie,Ae.data):t.texImage3D(n.TEXTURE_2D_ARRAY,oe,Me,Ae.width,Ae.height,le.depth,0,ge,Ie,Ae.data)}else{Fe&&Ye&&t.texStorage2D(n.TEXTURE_2D,ve,Me,He[0].width,He[0].height);for(let oe=0,Le=He.length;oe<Le;oe++)Ae=He[oe],A.format!==di?ge!==null?Fe?K&&t.compressedTexSubImage2D(n.TEXTURE_2D,oe,0,0,Ae.width,Ae.height,ge,Ae.data):t.compressedTexImage2D(n.TEXTURE_2D,oe,Me,Ae.width,Ae.height,0,Ae.data):Qe("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):Fe?K&&t.texSubImage2D(n.TEXTURE_2D,oe,0,0,Ae.width,Ae.height,ge,Ie,Ae.data):t.texImage2D(n.TEXTURE_2D,oe,Me,Ae.width,Ae.height,0,ge,Ie,Ae.data)}else if(A.isDataArrayTexture)if(Fe){if(Ye&&t.texStorage3D(n.TEXTURE_2D_ARRAY,ve,Me,le.width,le.height,le.depth),K)if(A.layerUpdates.size>0){const oe=kd(le.width,le.height,A.format,A.type);for(const Le of A.layerUpdates){const Se=le.data.subarray(Le*oe/le.data.BYTES_PER_ELEMENT,(Le+1)*oe/le.data.BYTES_PER_ELEMENT);t.texSubImage3D(n.TEXTURE_2D_ARRAY,0,0,0,Le,le.width,le.height,1,ge,Ie,Se)}A.clearLayerUpdates()}else t.texSubImage3D(n.TEXTURE_2D_ARRAY,0,0,0,0,le.width,le.height,le.depth,ge,Ie,le.data)}else t.texImage3D(n.TEXTURE_2D_ARRAY,0,Me,le.width,le.height,le.depth,0,ge,Ie,le.data);else if(A.isData3DTexture)Fe?(Ye&&t.texStorage3D(n.TEXTURE_3D,ve,Me,le.width,le.height,le.depth),K&&t.texSubImage3D(n.TEXTURE_3D,0,0,0,0,le.width,le.height,le.depth,ge,Ie,le.data)):t.texImage3D(n.TEXTURE_3D,0,Me,le.width,le.height,le.depth,0,ge,Ie,le.data);else if(A.isFramebufferTexture){if(Ye)if(Fe)t.texStorage2D(n.TEXTURE_2D,ve,Me,le.width,le.height);else{let oe=le.width,Le=le.height;for(let Se=0;Se<ve;Se++)t.texImage2D(n.TEXTURE_2D,Se,Me,oe,Le,0,ge,Ie,null),oe>>=1,Le>>=1}}else if(A.isHTMLTexture){if("texElementImage2D"in n){const oe=n.canvas;if(oe.hasAttribute("layoutsubtree")||oe.setAttribute("layoutsubtree","true"),le.parentNode!==oe){oe.appendChild(le),f.add(A),oe.onpaint=$e=>{const ot=$e.changedElements;for(const tt of f)ot.includes(tt.image)&&(tt.needsUpdate=!0)},oe.requestPaint();return}const Le=0,Se=n.RGBA,fe=n.RGBA,Oe=n.UNSIGNED_BYTE;n.texElementImage2D(n.TEXTURE_2D,Le,Se,fe,Oe,le),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_MIN_FILTER,n.LINEAR),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_WRAP_S,n.CLAMP_TO_EDGE),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_WRAP_T,n.CLAMP_TO_EDGE)}}else if(He.length>0){if(Fe&&Ye){const oe=Re(He[0]);t.texStorage2D(n.TEXTURE_2D,ve,Me,oe.width,oe.height)}for(let oe=0,Le=He.length;oe<Le;oe++)Ae=He[oe],Fe?K&&t.texSubImage2D(n.TEXTURE_2D,oe,0,0,ge,Ie,Ae):t.texImage2D(n.TEXTURE_2D,oe,Me,ge,Ie,Ae);A.generateMipmaps=!1}else if(Fe){if(Ye){const oe=Re(le);t.texStorage2D(n.TEXTURE_2D,ve,Me,oe.width,oe.height)}K&&t.texSubImage2D(n.TEXTURE_2D,0,0,0,ge,Ie,le)}else t.texImage2D(n.TEXTURE_2D,0,Me,ge,Ie,le);_(A)&&v(ee),Te.__version=xe.version,A.onUpdate&&A.onUpdate(A)}D.__version=A.version}function me(D,A,X){if(A.image.length!==6)return;const ee=z(D,A),he=A.source;t.bindTexture(n.TEXTURE_CUBE_MAP,D.__webglTexture,n.TEXTURE0+X);const xe=i.get(he);if(he.version!==xe.__version||ee===!0){t.activeTexture(n.TEXTURE0+X);const Te=ft.getPrimaries(ft.workingColorSpace),te=A.colorSpace===Ti?null:ft.getPrimaries(A.colorSpace),le=A.colorSpace===Ti||Te===te?n.NONE:n.BROWSER_DEFAULT_WEBGL;t.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,A.flipY),t.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,A.premultiplyAlpha),t.pixelStorei(n.UNPACK_ALIGNMENT,A.unpackAlignment),t.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,le);const ge=A.isCompressedTexture||A.image[0].isCompressedTexture,Ie=A.image[0]&&A.image[0].isDataTexture,Me=[];for(let fe=0;fe<6;fe++)!ge&&!Ie?Me[fe]=p(A.image[fe],!0,r.maxCubemapSize):Me[fe]=Ie?A.image[fe].image:A.image[fe],Me[fe]=pe(A,Me[fe]);const Ae=Me[0],He=s.convert(A.format,A.colorSpace),Fe=s.convert(A.type),Ye=S(A.internalFormat,He,Fe,A.normalized,A.colorSpace),K=A.isVideoTexture!==!0,ve=xe.__version===void 0||ee===!0,oe=he.dataReady;let Le=M(A,Ae);G(n.TEXTURE_CUBE_MAP,A);let Se;if(ge){K&&ve&&t.texStorage2D(n.TEXTURE_CUBE_MAP,Le,Ye,Ae.width,Ae.height);for(let fe=0;fe<6;fe++){Se=Me[fe].mipmaps;for(let Oe=0;Oe<Se.length;Oe++){const $e=Se[Oe];A.format!==di?He!==null?K?oe&&t.compressedTexSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,Oe,0,0,$e.width,$e.height,He,$e.data):t.compressedTexImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,Oe,Ye,$e.width,$e.height,0,$e.data):Qe("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):K?oe&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,Oe,0,0,$e.width,$e.height,He,Fe,$e.data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,Oe,Ye,$e.width,$e.height,0,He,Fe,$e.data)}}}else{if(Se=A.mipmaps,K&&ve){Se.length>0&&Le++;const fe=Re(Me[0]);t.texStorage2D(n.TEXTURE_CUBE_MAP,Le,Ye,fe.width,fe.height)}for(let fe=0;fe<6;fe++)if(Ie){K?oe&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,0,0,0,Me[fe].width,Me[fe].height,He,Fe,Me[fe].data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,0,Ye,Me[fe].width,Me[fe].height,0,He,Fe,Me[fe].data);for(let Oe=0;Oe<Se.length;Oe++){const ot=Se[Oe].image[fe].image;K?oe&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,Oe+1,0,0,ot.width,ot.height,He,Fe,ot.data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,Oe+1,Ye,ot.width,ot.height,0,He,Fe,ot.data)}}else{K?oe&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,0,0,0,He,Fe,Me[fe]):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,0,Ye,He,Fe,Me[fe]);for(let Oe=0;Oe<Se.length;Oe++){const $e=Se[Oe];K?oe&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,Oe+1,0,0,He,Fe,$e.image[fe]):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+fe,Oe+1,Ye,He,Fe,$e.image[fe])}}}_(A)&&v(n.TEXTURE_CUBE_MAP),xe.__version=he.version,A.onUpdate&&A.onUpdate(A)}D.__version=A.version}function Q(D,A,X,ee,he,xe){const Te=s.convert(X.format,X.colorSpace),te=s.convert(X.type),le=S(X.internalFormat,Te,te,X.normalized,X.colorSpace),ge=i.get(A),Ie=i.get(X);if(Ie.__renderTarget=A,!ge.__hasExternalTextures){const Me=Math.max(1,A.width>>xe),Ae=Math.max(1,A.height>>xe);he===n.TEXTURE_3D||he===n.TEXTURE_2D_ARRAY?t.texImage3D(he,xe,le,Me,Ae,A.depth,0,Te,te,null):t.texImage2D(he,xe,le,Me,Ae,0,Te,te,null)}t.bindFramebuffer(n.FRAMEBUFFER,D),Pe(A)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,ee,he,Ie.__webglTexture,0,de(A)):(he===n.TEXTURE_2D||he>=n.TEXTURE_CUBE_MAP_POSITIVE_X&&he<=n.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&n.framebufferTexture2D(n.FRAMEBUFFER,ee,he,Ie.__webglTexture,xe),t.bindFramebuffer(n.FRAMEBUFFER,null)}function ie(D,A,X){if(n.bindRenderbuffer(n.RENDERBUFFER,D),A.depthBuffer){const ee=A.depthTexture,he=ee&&ee.isDepthTexture?ee.type:null,xe=E(A.stencilBuffer,he),Te=A.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;Pe(A)?o.renderbufferStorageMultisampleEXT(n.RENDERBUFFER,de(A),xe,A.width,A.height):X?n.renderbufferStorageMultisample(n.RENDERBUFFER,de(A),xe,A.width,A.height):n.renderbufferStorage(n.RENDERBUFFER,xe,A.width,A.height),n.framebufferRenderbuffer(n.FRAMEBUFFER,Te,n.RENDERBUFFER,D)}else{const ee=A.textures;for(let he=0;he<ee.length;he++){const xe=ee[he],Te=s.convert(xe.format,xe.colorSpace),te=s.convert(xe.type),le=S(xe.internalFormat,Te,te,xe.normalized,xe.colorSpace);Pe(A)?o.renderbufferStorageMultisampleEXT(n.RENDERBUFFER,de(A),le,A.width,A.height):X?n.renderbufferStorageMultisample(n.RENDERBUFFER,de(A),le,A.width,A.height):n.renderbufferStorage(n.RENDERBUFFER,le,A.width,A.height)}}n.bindRenderbuffer(n.RENDERBUFFER,null)}function be(D,A,X){const ee=A.isWebGLCubeRenderTarget===!0;if(t.bindFramebuffer(n.FRAMEBUFFER,D),!(A.depthTexture&&A.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");const he=i.get(A.depthTexture);if(he.__renderTarget=A,(!he.__webglTexture||A.depthTexture.image.width!==A.width||A.depthTexture.image.height!==A.height)&&(A.depthTexture.image.width=A.width,A.depthTexture.image.height=A.height,A.depthTexture.needsUpdate=!0),ee){if(he.__webglInit===void 0&&(he.__webglInit=!0,A.depthTexture.addEventListener("dispose",T)),he.__webglTexture===void 0){he.__webglTexture=n.createTexture(),t.bindTexture(n.TEXTURE_CUBE_MAP,he.__webglTexture),G(n.TEXTURE_CUBE_MAP,A.depthTexture);const ge=s.convert(A.depthTexture.format),Ie=s.convert(A.depthTexture.type);let Me;A.depthTexture.format===qi?Me=n.DEPTH_COMPONENT24:A.depthTexture.format===dr&&(Me=n.DEPTH24_STENCIL8);for(let Ae=0;Ae<6;Ae++)n.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+Ae,0,Me,A.width,A.height,0,ge,Ie,null)}}else Y(A.depthTexture,0);const xe=he.__webglTexture,Te=de(A),te=ee?n.TEXTURE_CUBE_MAP_POSITIVE_X+X:n.TEXTURE_2D,le=A.depthTexture.format===dr?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;if(A.depthTexture.format===qi)Pe(A)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,le,te,xe,0,Te):n.framebufferTexture2D(n.FRAMEBUFFER,le,te,xe,0);else if(A.depthTexture.format===dr)Pe(A)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,le,te,xe,0,Te):n.framebufferTexture2D(n.FRAMEBUFFER,le,te,xe,0);else throw new Error("Unknown depthTexture format")}function De(D){const A=i.get(D),X=D.isWebGLCubeRenderTarget===!0;if(A.__boundDepthTexture!==D.depthTexture){const ee=D.depthTexture;if(A.__depthDisposeCallback&&A.__depthDisposeCallback(),ee){const he=()=>{delete A.__boundDepthTexture,delete A.__depthDisposeCallback,ee.removeEventListener("dispose",he)};ee.addEventListener("dispose",he),A.__depthDisposeCallback=he}A.__boundDepthTexture=ee}if(D.depthTexture&&!A.__autoAllocateDepthBuffer)if(X)for(let ee=0;ee<6;ee++)be(A.__webglFramebuffer[ee],D,ee);else{const ee=D.texture.mipmaps;ee&&ee.length>0?be(A.__webglFramebuffer[0],D,0):be(A.__webglFramebuffer,D,0)}else if(X){A.__webglDepthbuffer=[];for(let ee=0;ee<6;ee++)if(t.bindFramebuffer(n.FRAMEBUFFER,A.__webglFramebuffer[ee]),A.__webglDepthbuffer[ee]===void 0)A.__webglDepthbuffer[ee]=n.createRenderbuffer(),ie(A.__webglDepthbuffer[ee],D,!1);else{const he=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,xe=A.__webglDepthbuffer[ee];n.bindRenderbuffer(n.RENDERBUFFER,xe),n.framebufferRenderbuffer(n.FRAMEBUFFER,he,n.RENDERBUFFER,xe)}}else{const ee=D.texture.mipmaps;if(ee&&ee.length>0?t.bindFramebuffer(n.FRAMEBUFFER,A.__webglFramebuffer[0]):t.bindFramebuffer(n.FRAMEBUFFER,A.__webglFramebuffer),A.__webglDepthbuffer===void 0)A.__webglDepthbuffer=n.createRenderbuffer(),ie(A.__webglDepthbuffer,D,!1);else{const he=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,xe=A.__webglDepthbuffer;n.bindRenderbuffer(n.RENDERBUFFER,xe),n.framebufferRenderbuffer(n.FRAMEBUFFER,he,n.RENDERBUFFER,xe)}}t.bindFramebuffer(n.FRAMEBUFFER,null)}function ye(D,A,X){const ee=i.get(D);A!==void 0&&Q(ee.__webglFramebuffer,D,D.texture,n.COLOR_ATTACHMENT0,n.TEXTURE_2D,0),X!==void 0&&De(D)}function _e(D){const A=D.texture,X=i.get(D),ee=i.get(A);D.addEventListener("dispose",x);const he=D.textures,xe=D.isWebGLCubeRenderTarget===!0,Te=he.length>1;if(Te||(ee.__webglTexture===void 0&&(ee.__webglTexture=n.createTexture()),ee.__version=A.version,a.memory.textures++),xe){X.__webglFramebuffer=[];for(let te=0;te<6;te++)if(A.mipmaps&&A.mipmaps.length>0){X.__webglFramebuffer[te]=[];for(let le=0;le<A.mipmaps.length;le++)X.__webglFramebuffer[te][le]=n.createFramebuffer()}else X.__webglFramebuffer[te]=n.createFramebuffer()}else{if(A.mipmaps&&A.mipmaps.length>0){X.__webglFramebuffer=[];for(let te=0;te<A.mipmaps.length;te++)X.__webglFramebuffer[te]=n.createFramebuffer()}else X.__webglFramebuffer=n.createFramebuffer();if(Te)for(let te=0,le=he.length;te<le;te++){const ge=i.get(he[te]);ge.__webglTexture===void 0&&(ge.__webglTexture=n.createTexture(),a.memory.textures++)}if(D.samples>0&&Pe(D)===!1){X.__webglMultisampledFramebuffer=n.createFramebuffer(),X.__webglColorRenderbuffer=[],t.bindFramebuffer(n.FRAMEBUFFER,X.__webglMultisampledFramebuffer);for(let te=0;te<he.length;te++){const le=he[te];X.__webglColorRenderbuffer[te]=n.createRenderbuffer(),n.bindRenderbuffer(n.RENDERBUFFER,X.__webglColorRenderbuffer[te]);const ge=s.convert(le.format,le.colorSpace),Ie=s.convert(le.type),Me=S(le.internalFormat,ge,Ie,le.normalized,le.colorSpace,D.isXRRenderTarget===!0),Ae=de(D);n.renderbufferStorageMultisample(n.RENDERBUFFER,Ae,Me,D.width,D.height),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+te,n.RENDERBUFFER,X.__webglColorRenderbuffer[te])}n.bindRenderbuffer(n.RENDERBUFFER,null),D.depthBuffer&&(X.__webglDepthRenderbuffer=n.createRenderbuffer(),ie(X.__webglDepthRenderbuffer,D,!0)),t.bindFramebuffer(n.FRAMEBUFFER,null)}}if(xe){t.bindTexture(n.TEXTURE_CUBE_MAP,ee.__webglTexture),G(n.TEXTURE_CUBE_MAP,A);for(let te=0;te<6;te++)if(A.mipmaps&&A.mipmaps.length>0)for(let le=0;le<A.mipmaps.length;le++)Q(X.__webglFramebuffer[te][le],D,A,n.COLOR_ATTACHMENT0,n.TEXTURE_CUBE_MAP_POSITIVE_X+te,le);else Q(X.__webglFramebuffer[te],D,A,n.COLOR_ATTACHMENT0,n.TEXTURE_CUBE_MAP_POSITIVE_X+te,0);_(A)&&v(n.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Te){for(let te=0,le=he.length;te<le;te++){const ge=he[te],Ie=i.get(ge);let Me=n.TEXTURE_2D;(D.isWebGL3DRenderTarget||D.isWebGLArrayRenderTarget)&&(Me=D.isWebGL3DRenderTarget?n.TEXTURE_3D:n.TEXTURE_2D_ARRAY),t.bindTexture(Me,Ie.__webglTexture),G(Me,ge),Q(X.__webglFramebuffer,D,ge,n.COLOR_ATTACHMENT0+te,Me,0),_(ge)&&v(Me)}t.unbindTexture()}else{let te=n.TEXTURE_2D;if((D.isWebGL3DRenderTarget||D.isWebGLArrayRenderTarget)&&(te=D.isWebGL3DRenderTarget?n.TEXTURE_3D:n.TEXTURE_2D_ARRAY),t.bindTexture(te,ee.__webglTexture),G(te,A),A.mipmaps&&A.mipmaps.length>0)for(let le=0;le<A.mipmaps.length;le++)Q(X.__webglFramebuffer[le],D,A,n.COLOR_ATTACHMENT0,te,le);else Q(X.__webglFramebuffer,D,A,n.COLOR_ATTACHMENT0,te,0);_(A)&&v(te),t.unbindTexture()}D.depthBuffer&&De(D)}function Ne(D){const A=D.textures;for(let X=0,ee=A.length;X<ee;X++){const he=A[X];if(_(he)){const xe=b(D),Te=i.get(he).__webglTexture;t.bindTexture(xe,Te),v(xe),t.unbindTexture()}}}const ae=[],Ee=[];function k(D){if(D.samples>0){if(Pe(D)===!1){const A=D.textures,X=D.width,ee=D.height;let he=n.COLOR_BUFFER_BIT;const xe=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,Te=i.get(D),te=A.length>1;if(te)for(let ge=0;ge<A.length;ge++)t.bindFramebuffer(n.FRAMEBUFFER,Te.__webglMultisampledFramebuffer),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+ge,n.RENDERBUFFER,null),t.bindFramebuffer(n.FRAMEBUFFER,Te.__webglFramebuffer),n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0+ge,n.TEXTURE_2D,null,0);t.bindFramebuffer(n.READ_FRAMEBUFFER,Te.__webglMultisampledFramebuffer);const le=D.texture.mipmaps;le&&le.length>0?t.bindFramebuffer(n.DRAW_FRAMEBUFFER,Te.__webglFramebuffer[0]):t.bindFramebuffer(n.DRAW_FRAMEBUFFER,Te.__webglFramebuffer);for(let ge=0;ge<A.length;ge++){if(D.resolveDepthBuffer&&(D.depthBuffer&&(he|=n.DEPTH_BUFFER_BIT),D.stencilBuffer&&D.resolveStencilBuffer&&(he|=n.STENCIL_BUFFER_BIT)),te){n.framebufferRenderbuffer(n.READ_FRAMEBUFFER,n.COLOR_ATTACHMENT0,n.RENDERBUFFER,Te.__webglColorRenderbuffer[ge]);const Ie=i.get(A[ge]).__webglTexture;n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0,n.TEXTURE_2D,Ie,0)}n.blitFramebuffer(0,0,X,ee,0,0,X,ee,he,n.NEAREST),l===!0&&(ae.length=0,Ee.length=0,ae.push(n.COLOR_ATTACHMENT0+ge),D.depthBuffer&&D.resolveDepthBuffer===!1&&(ae.push(xe),Ee.push(xe),n.invalidateFramebuffer(n.DRAW_FRAMEBUFFER,Ee)),n.invalidateFramebuffer(n.READ_FRAMEBUFFER,ae))}if(t.bindFramebuffer(n.READ_FRAMEBUFFER,null),t.bindFramebuffer(n.DRAW_FRAMEBUFFER,null),te)for(let ge=0;ge<A.length;ge++){t.bindFramebuffer(n.FRAMEBUFFER,Te.__webglMultisampledFramebuffer),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+ge,n.RENDERBUFFER,Te.__webglColorRenderbuffer[ge]);const Ie=i.get(A[ge]).__webglTexture;t.bindFramebuffer(n.FRAMEBUFFER,Te.__webglFramebuffer),n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0+ge,n.TEXTURE_2D,Ie,0)}t.bindFramebuffer(n.DRAW_FRAMEBUFFER,Te.__webglMultisampledFramebuffer)}else if(D.depthBuffer&&D.resolveDepthBuffer===!1&&l){const A=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;n.invalidateFramebuffer(n.DRAW_FRAMEBUFFER,[A])}}}function de(D){return Math.min(r.maxSamples,D.samples)}function Pe(D){const A=i.get(D);return D.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&A.__useRenderToTexture!==!1}function we(D){const A=a.render.frame;u.get(D)!==A&&(u.set(D,A),D.update())}function pe(D,A){const X=D.colorSpace,ee=D.format,he=D.type;return D.isCompressedTexture===!0||D.isVideoTexture===!0||X!==Vs&&X!==Ti&&(ft.getTransfer(X)===bt?(ee!==di||he!==Yt)&&Qe("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):pt("WebGLTextures: Unsupported texture color space:",X)),A}function Re(D){return typeof HTMLImageElement<"u"&&D instanceof HTMLImageElement?(c.width=D.naturalWidth||D.width,c.height=D.naturalHeight||D.height):typeof VideoFrame<"u"&&D instanceof VideoFrame?(c.width=D.displayWidth,c.height=D.displayHeight):(c.width=D.width,c.height=D.height),c}this.allocateTextureUnit=F,this.resetTextureUnits=L,this.getTextureUnits=U,this.setTextureUnits=I,this.setTexture2D=Y,this.setTexture2DArray=j,this.setTexture3D=Z,this.setTextureCube=O,this.rebindTextures=ye,this.setupRenderTarget=_e,this.updateRenderTargetMipmap=Ne,this.updateMultisampleRenderTarget=k,this.setupDepthRenderbuffer=De,this.setupFrameBufferTexture=Q,this.useMultisampledRTT=Pe,this.isReversedDepthBuffer=function(){return t.buffers.depth.getReversed()}}function IM(n,e){function t(i,r=Ti){let s;const a=ft.getTransfer(r);if(i===Yt)return n.UNSIGNED_BYTE;if(i===Zh)return n.UNSIGNED_SHORT_4_4_4_4;if(i===$h)return n.UNSIGNED_SHORT_5_5_5_1;if(i===Fm)return n.UNSIGNED_INT_5_9_9_9_REV;if(i===Nm)return n.UNSIGNED_INT_10F_11F_11F_REV;if(i===Lm)return n.BYTE;if(i===Im)return n.SHORT;if(i===Ha)return n.UNSIGNED_SHORT;if(i===Kh)return n.INT;if(i===Ui)return n.UNSIGNED_INT;if(i===fi)return n.FLOAT;if(i===Yi)return n.HALF_FLOAT;if(i===Om)return n.ALPHA;if(i===Bm)return n.RGB;if(i===di)return n.RGBA;if(i===qi)return n.DEPTH_COMPONENT;if(i===dr)return n.DEPTH_STENCIL;if(i===km)return n.RED;if(i===Jh)return n.RED_INTEGER;if(i===Jr)return n.RG;if(i===Qh)return n.RG_INTEGER;if(i===ef)return n.RGBA_INTEGER;if(i===Zo||i===$o||i===Jo||i===Qo)if(a===bt)if(s=e.get("WEBGL_compressed_texture_s3tc_srgb"),s!==null){if(i===Zo)return s.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(i===$o)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(i===Jo)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(i===Qo)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(s=e.get("WEBGL_compressed_texture_s3tc"),s!==null){if(i===Zo)return s.COMPRESSED_RGB_S3TC_DXT1_EXT;if(i===$o)return s.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(i===Jo)return s.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(i===Qo)return s.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(i===ku||i===zu||i===Gu||i===Hu)if(s=e.get("WEBGL_compressed_texture_pvrtc"),s!==null){if(i===ku)return s.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(i===zu)return s.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(i===Gu)return s.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(i===Hu)return s.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(i===Vu||i===Wu||i===Xu||i===ju||i===Yu||i===ul||i===qu)if(s=e.get("WEBGL_compressed_texture_etc"),s!==null){if(i===Vu||i===Wu)return a===bt?s.COMPRESSED_SRGB8_ETC2:s.COMPRESSED_RGB8_ETC2;if(i===Xu)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:s.COMPRESSED_RGBA8_ETC2_EAC;if(i===ju)return s.COMPRESSED_R11_EAC;if(i===Yu)return s.COMPRESSED_SIGNED_R11_EAC;if(i===ul)return s.COMPRESSED_RG11_EAC;if(i===qu)return s.COMPRESSED_SIGNED_RG11_EAC}else return null;if(i===Ku||i===Zu||i===$u||i===Ju||i===Qu||i===eh||i===th||i===nh||i===ih||i===rh||i===sh||i===ah||i===oh||i===lh)if(s=e.get("WEBGL_compressed_texture_astc"),s!==null){if(i===Ku)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:s.COMPRESSED_RGBA_ASTC_4x4_KHR;if(i===Zu)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:s.COMPRESSED_RGBA_ASTC_5x4_KHR;if(i===$u)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:s.COMPRESSED_RGBA_ASTC_5x5_KHR;if(i===Ju)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:s.COMPRESSED_RGBA_ASTC_6x5_KHR;if(i===Qu)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:s.COMPRESSED_RGBA_ASTC_6x6_KHR;if(i===eh)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:s.COMPRESSED_RGBA_ASTC_8x5_KHR;if(i===th)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:s.COMPRESSED_RGBA_ASTC_8x6_KHR;if(i===nh)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:s.COMPRESSED_RGBA_ASTC_8x8_KHR;if(i===ih)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:s.COMPRESSED_RGBA_ASTC_10x5_KHR;if(i===rh)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:s.COMPRESSED_RGBA_ASTC_10x6_KHR;if(i===sh)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:s.COMPRESSED_RGBA_ASTC_10x8_KHR;if(i===ah)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:s.COMPRESSED_RGBA_ASTC_10x10_KHR;if(i===oh)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:s.COMPRESSED_RGBA_ASTC_12x10_KHR;if(i===lh)return a===bt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:s.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(i===ch||i===uh||i===hh)if(s=e.get("EXT_texture_compression_bptc"),s!==null){if(i===ch)return a===bt?s.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:s.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(i===uh)return s.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(i===hh)return s.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(i===fh||i===dh||i===hl||i===ph)if(s=e.get("EXT_texture_compression_rgtc"),s!==null){if(i===fh)return s.COMPRESSED_RED_RGTC1_EXT;if(i===dh)return s.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(i===hl)return s.COMPRESSED_RED_GREEN_RGTC2_EXT;if(i===ph)return s.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return i===Hs?n.UNSIGNED_INT_24_8:n[i]!==void 0?n[i]:null}return{convert:t}}const FM=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,NM=`
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

}`;class OM{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){const i=new Km(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=i}}getMesh(e){if(this.texture!==null&&this.mesh===null){const t=e.cameras[0].viewport,i=new ln({vertexShader:FM,fragmentShader:NM,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new Yn(new es(20,20),i)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class BM extends mi{constructor(e,t){super();const i=this;let r=null,s=1,a=null,o="local-floor",l=1,c=null,u=null,f=null,h=null,d=null,m=null;const g=typeof XRWebGLBinding<"u",p=new OM,_={},v=t.getContextAttributes();let b=null,S=null;const E=[],M=[],T=new Xe;let x=null;const y=new Hn;y.viewport=new Ut;const w=new Hn;w.viewport=new Ut;const C=[y,w],R=new jv;let L=null,U=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(z){let W=E[z];return W===void 0&&(W=new _c,E[z]=W),W.getTargetRaySpace()},this.getControllerGrip=function(z){let W=E[z];return W===void 0&&(W=new _c,E[z]=W),W.getGripSpace()},this.getHand=function(z){let W=E[z];return W===void 0&&(W=new _c,E[z]=W),W.getHandSpace()};function I(z){const W=M.indexOf(z.inputSource);if(W===-1)return;const q=E[W];q!==void 0&&(q.update(z.inputSource,z.frame,c||a),q.dispatchEvent({type:z.type,data:z.inputSource}))}function F(){r.removeEventListener("select",I),r.removeEventListener("selectstart",I),r.removeEventListener("selectend",I),r.removeEventListener("squeeze",I),r.removeEventListener("squeezestart",I),r.removeEventListener("squeezeend",I),r.removeEventListener("end",F),r.removeEventListener("inputsourceschange",N);for(let z=0;z<E.length;z++){const W=M[z];W!==null&&(M[z]=null,E[z].disconnect(W))}L=null,U=null,p.reset();for(const z in _)delete _[z];e.setRenderTarget(b),d=null,h=null,f=null,r=null,S=null,G.stop(),i.isPresenting=!1,e.setPixelRatio(x),e.setSize(T.width,T.height,!1),i.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(z){s=z,i.isPresenting===!0&&Qe("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(z){o=z,i.isPresenting===!0&&Qe("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||a},this.setReferenceSpace=function(z){c=z},this.getBaseLayer=function(){return h!==null?h:d},this.getBinding=function(){return f===null&&g&&(f=new XRWebGLBinding(r,t)),f},this.getFrame=function(){return m},this.getSession=function(){return r},this.setSession=async function(z){if(r=z,r!==null){if(b=e.getRenderTarget(),r.addEventListener("select",I),r.addEventListener("selectstart",I),r.addEventListener("selectend",I),r.addEventListener("squeeze",I),r.addEventListener("squeezestart",I),r.addEventListener("squeezeend",I),r.addEventListener("end",F),r.addEventListener("inputsourceschange",N),v.xrCompatible!==!0&&await t.makeXRCompatible(),x=e.getPixelRatio(),e.getSize(T),g&&"createProjectionLayer"in XRWebGLBinding.prototype){let q=null,ce=null,me=null;v.depth&&(me=v.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,q=v.stencil?dr:qi,ce=v.stencil?Hs:Ui);const Q={colorFormat:t.RGBA8,depthFormat:me,scaleFactor:s};f=this.getBinding(),h=f.createProjectionLayer(Q),r.updateRenderState({layers:[h]}),e.setPixelRatio(1),e.setSize(h.textureWidth,h.textureHeight,!1),S=new Qt(h.textureWidth,h.textureHeight,{format:di,type:Yt,depthTexture:new Xi(h.textureWidth,h.textureHeight,ce,void 0,void 0,void 0,void 0,void 0,void 0,q),stencilBuffer:v.stencil,colorSpace:e.outputColorSpace,samples:v.antialias?4:0,resolveDepthBuffer:h.ignoreDepthValues===!1,resolveStencilBuffer:h.ignoreDepthValues===!1})}else{const q={antialias:v.antialias,alpha:!0,depth:v.depth,stencil:v.stencil,framebufferScaleFactor:s};d=new XRWebGLLayer(r,t,q),r.updateRenderState({baseLayer:d}),e.setPixelRatio(1),e.setSize(d.framebufferWidth,d.framebufferHeight,!1),S=new Qt(d.framebufferWidth,d.framebufferHeight,{format:di,type:Yt,colorSpace:e.outputColorSpace,stencilBuffer:v.stencil,resolveDepthBuffer:d.ignoreDepthValues===!1,resolveStencilBuffer:d.ignoreDepthValues===!1})}S.isXRRenderTarget=!0,this.setFoveation(l),c=null,a=await r.requestReferenceSpace(o),G.setContext(r),G.start(),i.isPresenting=!0,i.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(r!==null)return r.environmentBlendMode},this.getDepthTexture=function(){return p.getDepthTexture()};function N(z){for(let W=0;W<z.removed.length;W++){const q=z.removed[W],ce=M.indexOf(q);ce>=0&&(M[ce]=null,E[ce].disconnect(q))}for(let W=0;W<z.added.length;W++){const q=z.added[W];let ce=M.indexOf(q);if(ce===-1){for(let Q=0;Q<E.length;Q++)if(Q>=M.length){M.push(q),ce=Q;break}else if(M[Q]===null){M[Q]=q,ce=Q;break}if(ce===-1)break}const me=E[ce];me&&me.connect(q)}}const Y=new $,j=new $;function Z(z,W,q){Y.setFromMatrixPosition(W.matrixWorld),j.setFromMatrixPosition(q.matrixWorld);const ce=Y.distanceTo(j),me=W.projectionMatrix.elements,Q=q.projectionMatrix.elements,ie=me[14]/(me[10]-1),be=me[14]/(me[10]+1),De=(me[9]+1)/me[5],ye=(me[9]-1)/me[5],_e=(me[8]-1)/me[0],Ne=(Q[8]+1)/Q[0],ae=ie*_e,Ee=ie*Ne,k=ce/(-_e+Ne),de=k*-_e;if(W.matrixWorld.decompose(z.position,z.quaternion,z.scale),z.translateX(de),z.translateZ(k),z.matrixWorld.compose(z.position,z.quaternion,z.scale),z.matrixWorldInverse.copy(z.matrixWorld).invert(),me[10]===-1)z.projectionMatrix.copy(W.projectionMatrix),z.projectionMatrixInverse.copy(W.projectionMatrixInverse);else{const Pe=ie+k,we=be+k,pe=ae-de,Re=Ee+(ce-de),D=De*be/we*Pe,A=ye*be/we*Pe;z.projectionMatrix.makePerspective(pe,Re,D,A,Pe,we),z.projectionMatrixInverse.copy(z.projectionMatrix).invert()}}function O(z,W){W===null?z.matrixWorld.copy(z.matrix):z.matrixWorld.multiplyMatrices(W.matrixWorld,z.matrix),z.matrixWorldInverse.copy(z.matrixWorld).invert()}this.updateCamera=function(z){if(r===null)return;let W=z.near,q=z.far;p.texture!==null&&(p.depthNear>0&&(W=p.depthNear),p.depthFar>0&&(q=p.depthFar)),R.near=w.near=y.near=W,R.far=w.far=y.far=q,(L!==R.near||U!==R.far)&&(r.updateRenderState({depthNear:R.near,depthFar:R.far}),L=R.near,U=R.far),R.layers.mask=z.layers.mask|6,y.layers.mask=R.layers.mask&-5,w.layers.mask=R.layers.mask&-3;const ce=z.parent,me=R.cameras;O(R,ce);for(let Q=0;Q<me.length;Q++)O(me[Q],ce);me.length===2?Z(R,y,w):R.projectionMatrix.copy(y.projectionMatrix),H(z,R,ce)};function H(z,W,q){q===null?z.matrix.copy(W.matrixWorld):(z.matrix.copy(q.matrixWorld),z.matrix.invert(),z.matrix.multiply(W.matrixWorld)),z.matrix.decompose(z.position,z.quaternion,z.scale),z.updateMatrixWorld(!0),z.projectionMatrix.copy(W.projectionMatrix),z.projectionMatrixInverse.copy(W.projectionMatrixInverse),z.isPerspectiveCamera&&(z.fov=_h*2*Math.atan(1/z.projectionMatrix.elements[5]),z.zoom=1)}this.getCamera=function(){return R},this.getFoveation=function(){if(!(h===null&&d===null))return l},this.setFoveation=function(z){l=z,h!==null&&(h.fixedFoveation=z),d!==null&&d.fixedFoveation!==void 0&&(d.fixedFoveation=z)},this.hasDepthSensing=function(){return p.texture!==null},this.getDepthSensingMesh=function(){return p.getMesh(R)},this.getCameraTexture=function(z){return _[z]};let B=null;function V(z,W){if(u=W.getViewerPose(c||a),m=W,u!==null){const q=u.views;d!==null&&(e.setRenderTargetFramebuffer(S,d.framebuffer),e.setRenderTarget(S));let ce=!1;q.length!==R.cameras.length&&(R.cameras.length=0,ce=!0);for(let be=0;be<q.length;be++){const De=q[be];let ye=null;if(d!==null)ye=d.getViewport(De);else{const Ne=f.getViewSubImage(h,De);ye=Ne.viewport,be===0&&(e.setRenderTargetTextures(S,Ne.colorTexture,Ne.depthStencilTexture),e.setRenderTarget(S))}let _e=C[be];_e===void 0&&(_e=new Hn,_e.layers.enable(be),_e.viewport=new Ut,C[be]=_e),_e.matrix.fromArray(De.transform.matrix),_e.matrix.decompose(_e.position,_e.quaternion,_e.scale),_e.projectionMatrix.fromArray(De.projectionMatrix),_e.projectionMatrixInverse.copy(_e.projectionMatrix).invert(),_e.viewport.set(ye.x,ye.y,ye.width,ye.height),be===0&&(R.matrix.copy(_e.matrix),R.matrix.decompose(R.position,R.quaternion,R.scale)),ce===!0&&R.cameras.push(_e)}const me=r.enabledFeatures;if(me&&me.includes("depth-sensing")&&r.depthUsage=="gpu-optimized"&&g){f=i.getBinding();const be=f.getDepthInformation(q[0]);be&&be.isValid&&be.texture&&p.init(be,r.renderState)}if(me&&me.includes("camera-access")&&g){e.state.unbindTexture(),f=i.getBinding();for(let be=0;be<q.length;be++){const De=q[be].camera;if(De){let ye=_[De];ye||(ye=new Km,_[De]=ye);const _e=f.getCameraImage(De);ye.sourceTexture=_e}}}}for(let q=0;q<E.length;q++){const ce=M[q],me=E[q];ce!==null&&me!==void 0&&me.update(ce,W,c||a)}B&&B(z,W),W.detectedPlanes&&i.dispatchEvent({type:"planesdetected",data:W}),m=null}const G=new t0;G.setAnimationLoop(V),this.setAnimationLoop=function(z){B=z},this.dispose=function(){}}}const kM=new zt,l0=new rt;l0.set(-1,0,0,0,1,0,0,0,1);function zM(n,e){function t(p,_){p.matrixAutoUpdate===!0&&p.updateMatrix(),_.value.copy(p.matrix)}function i(p,_){_.color.getRGB(p.fogColor.value,Zm(n)),_.isFog?(p.fogNear.value=_.near,p.fogFar.value=_.far):_.isFogExp2&&(p.fogDensity.value=_.density)}function r(p,_,v,b,S){_.isNodeMaterial?_.uniformsNeedUpdate=!1:_.isMeshBasicMaterial?s(p,_):_.isMeshLambertMaterial?(s(p,_),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)):_.isMeshToonMaterial?(s(p,_),f(p,_)):_.isMeshPhongMaterial?(s(p,_),u(p,_),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)):_.isMeshStandardMaterial?(s(p,_),h(p,_),_.isMeshPhysicalMaterial&&d(p,_,S)):_.isMeshMatcapMaterial?(s(p,_),m(p,_)):_.isMeshDepthMaterial?s(p,_):_.isMeshDistanceMaterial?(s(p,_),g(p,_)):_.isMeshNormalMaterial?s(p,_):_.isLineBasicMaterial?(a(p,_),_.isLineDashedMaterial&&o(p,_)):_.isPointsMaterial?l(p,_,v,b):_.isSpriteMaterial?c(p,_):_.isShadowMaterial?(p.color.value.copy(_.color),p.opacity.value=_.opacity):_.isShaderMaterial&&(_.uniformsNeedUpdate=!1)}function s(p,_){p.opacity.value=_.opacity,_.color&&p.diffuse.value.copy(_.color),_.emissive&&p.emissive.value.copy(_.emissive).multiplyScalar(_.emissiveIntensity),_.map&&(p.map.value=_.map,t(_.map,p.mapTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.bumpMap&&(p.bumpMap.value=_.bumpMap,t(_.bumpMap,p.bumpMapTransform),p.bumpScale.value=_.bumpScale,_.side===on&&(p.bumpScale.value*=-1)),_.normalMap&&(p.normalMap.value=_.normalMap,t(_.normalMap,p.normalMapTransform),p.normalScale.value.copy(_.normalScale),_.side===on&&p.normalScale.value.negate()),_.displacementMap&&(p.displacementMap.value=_.displacementMap,t(_.displacementMap,p.displacementMapTransform),p.displacementScale.value=_.displacementScale,p.displacementBias.value=_.displacementBias),_.emissiveMap&&(p.emissiveMap.value=_.emissiveMap,t(_.emissiveMap,p.emissiveMapTransform)),_.specularMap&&(p.specularMap.value=_.specularMap,t(_.specularMap,p.specularMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest);const v=e.get(_),b=v.envMap,S=v.envMapRotation;b&&(p.envMap.value=b,p.envMapRotation.value.setFromMatrix4(kM.makeRotationFromEuler(S)).transpose(),b.isCubeTexture&&b.isRenderTargetTexture===!1&&p.envMapRotation.value.premultiply(l0),p.reflectivity.value=_.reflectivity,p.ior.value=_.ior,p.refractionRatio.value=_.refractionRatio),_.lightMap&&(p.lightMap.value=_.lightMap,p.lightMapIntensity.value=_.lightMapIntensity,t(_.lightMap,p.lightMapTransform)),_.aoMap&&(p.aoMap.value=_.aoMap,p.aoMapIntensity.value=_.aoMapIntensity,t(_.aoMap,p.aoMapTransform))}function a(p,_){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,_.map&&(p.map.value=_.map,t(_.map,p.mapTransform))}function o(p,_){p.dashSize.value=_.dashSize,p.totalSize.value=_.dashSize+_.gapSize,p.scale.value=_.scale}function l(p,_,v,b){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,p.size.value=_.size*v,p.scale.value=b*.5,_.map&&(p.map.value=_.map,t(_.map,p.uvTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest)}function c(p,_){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,p.rotation.value=_.rotation,_.map&&(p.map.value=_.map,t(_.map,p.mapTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest)}function u(p,_){p.specular.value.copy(_.specular),p.shininess.value=Math.max(_.shininess,1e-4)}function f(p,_){_.gradientMap&&(p.gradientMap.value=_.gradientMap)}function h(p,_){p.metalness.value=_.metalness,_.metalnessMap&&(p.metalnessMap.value=_.metalnessMap,t(_.metalnessMap,p.metalnessMapTransform)),p.roughness.value=_.roughness,_.roughnessMap&&(p.roughnessMap.value=_.roughnessMap,t(_.roughnessMap,p.roughnessMapTransform)),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)}function d(p,_,v){p.ior.value=_.ior,_.sheen>0&&(p.sheenColor.value.copy(_.sheenColor).multiplyScalar(_.sheen),p.sheenRoughness.value=_.sheenRoughness,_.sheenColorMap&&(p.sheenColorMap.value=_.sheenColorMap,t(_.sheenColorMap,p.sheenColorMapTransform)),_.sheenRoughnessMap&&(p.sheenRoughnessMap.value=_.sheenRoughnessMap,t(_.sheenRoughnessMap,p.sheenRoughnessMapTransform))),_.clearcoat>0&&(p.clearcoat.value=_.clearcoat,p.clearcoatRoughness.value=_.clearcoatRoughness,_.clearcoatMap&&(p.clearcoatMap.value=_.clearcoatMap,t(_.clearcoatMap,p.clearcoatMapTransform)),_.clearcoatRoughnessMap&&(p.clearcoatRoughnessMap.value=_.clearcoatRoughnessMap,t(_.clearcoatRoughnessMap,p.clearcoatRoughnessMapTransform)),_.clearcoatNormalMap&&(p.clearcoatNormalMap.value=_.clearcoatNormalMap,t(_.clearcoatNormalMap,p.clearcoatNormalMapTransform),p.clearcoatNormalScale.value.copy(_.clearcoatNormalScale),_.side===on&&p.clearcoatNormalScale.value.negate())),_.dispersion>0&&(p.dispersion.value=_.dispersion),_.iridescence>0&&(p.iridescence.value=_.iridescence,p.iridescenceIOR.value=_.iridescenceIOR,p.iridescenceThicknessMinimum.value=_.iridescenceThicknessRange[0],p.iridescenceThicknessMaximum.value=_.iridescenceThicknessRange[1],_.iridescenceMap&&(p.iridescenceMap.value=_.iridescenceMap,t(_.iridescenceMap,p.iridescenceMapTransform)),_.iridescenceThicknessMap&&(p.iridescenceThicknessMap.value=_.iridescenceThicknessMap,t(_.iridescenceThicknessMap,p.iridescenceThicknessMapTransform))),_.transmission>0&&(p.transmission.value=_.transmission,p.transmissionSamplerMap.value=v.texture,p.transmissionSamplerSize.value.set(v.width,v.height),_.transmissionMap&&(p.transmissionMap.value=_.transmissionMap,t(_.transmissionMap,p.transmissionMapTransform)),p.thickness.value=_.thickness,_.thicknessMap&&(p.thicknessMap.value=_.thicknessMap,t(_.thicknessMap,p.thicknessMapTransform)),p.attenuationDistance.value=_.attenuationDistance,p.attenuationColor.value.copy(_.attenuationColor)),_.anisotropy>0&&(p.anisotropyVector.value.set(_.anisotropy*Math.cos(_.anisotropyRotation),_.anisotropy*Math.sin(_.anisotropyRotation)),_.anisotropyMap&&(p.anisotropyMap.value=_.anisotropyMap,t(_.anisotropyMap,p.anisotropyMapTransform))),p.specularIntensity.value=_.specularIntensity,p.specularColor.value.copy(_.specularColor),_.specularColorMap&&(p.specularColorMap.value=_.specularColorMap,t(_.specularColorMap,p.specularColorMapTransform)),_.specularIntensityMap&&(p.specularIntensityMap.value=_.specularIntensityMap,t(_.specularIntensityMap,p.specularIntensityMapTransform))}function m(p,_){_.matcap&&(p.matcap.value=_.matcap)}function g(p,_){const v=e.get(_).light;p.referencePosition.value.setFromMatrixPosition(v.matrixWorld),p.nearDistance.value=v.shadow.camera.near,p.farDistance.value=v.shadow.camera.far}return{refreshFogUniforms:i,refreshMaterialUniforms:r}}function GM(n,e,t,i){let r={},s={},a=[];const o=n.getParameter(n.MAX_UNIFORM_BUFFER_BINDINGS);function l(v,b){const S=b.program;i.uniformBlockBinding(v,S)}function c(v,b){let S=r[v.id];S===void 0&&(m(v),S=u(v),r[v.id]=S,v.addEventListener("dispose",p));const E=b.program;i.updateUBOMapping(v,E);const M=e.render.frame;s[v.id]!==M&&(h(v),s[v.id]=M)}function u(v){const b=f();v.__bindingPointIndex=b;const S=n.createBuffer(),E=v.__size,M=v.usage;return n.bindBuffer(n.UNIFORM_BUFFER,S),n.bufferData(n.UNIFORM_BUFFER,E,M),n.bindBuffer(n.UNIFORM_BUFFER,null),n.bindBufferBase(n.UNIFORM_BUFFER,b,S),S}function f(){for(let v=0;v<o;v++)if(a.indexOf(v)===-1)return a.push(v),v;return pt("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function h(v){const b=r[v.id],S=v.uniforms,E=v.__cache;n.bindBuffer(n.UNIFORM_BUFFER,b);for(let M=0,T=S.length;M<T;M++){const x=Array.isArray(S[M])?S[M]:[S[M]];for(let y=0,w=x.length;y<w;y++){const C=x[y];if(d(C,M,y,E)===!0){const R=C.__offset,L=Array.isArray(C.value)?C.value:[C.value];let U=0;for(let I=0;I<L.length;I++){const F=L[I],N=g(F);typeof F=="number"||typeof F=="boolean"?(C.__data[0]=F,n.bufferSubData(n.UNIFORM_BUFFER,R+U,C.__data)):F.isMatrix3?(C.__data[0]=F.elements[0],C.__data[1]=F.elements[1],C.__data[2]=F.elements[2],C.__data[3]=0,C.__data[4]=F.elements[3],C.__data[5]=F.elements[4],C.__data[6]=F.elements[5],C.__data[7]=0,C.__data[8]=F.elements[6],C.__data[9]=F.elements[7],C.__data[10]=F.elements[8],C.__data[11]=0):ArrayBuffer.isView(F)?C.__data.set(new F.constructor(F.buffer,F.byteOffset,C.__data.length)):(F.toArray(C.__data,U),U+=N.storage/Float32Array.BYTES_PER_ELEMENT)}n.bufferSubData(n.UNIFORM_BUFFER,R,C.__data)}}}n.bindBuffer(n.UNIFORM_BUFFER,null)}function d(v,b,S,E){const M=v.value,T=b+"_"+S;if(E[T]===void 0)return typeof M=="number"||typeof M=="boolean"?E[T]=M:ArrayBuffer.isView(M)?E[T]=M.slice():E[T]=M.clone(),!0;{const x=E[T];if(typeof M=="number"||typeof M=="boolean"){if(x!==M)return E[T]=M,!0}else{if(ArrayBuffer.isView(M))return!0;if(x.equals(M)===!1)return x.copy(M),!0}}return!1}function m(v){const b=v.uniforms;let S=0;const E=16;for(let T=0,x=b.length;T<x;T++){const y=Array.isArray(b[T])?b[T]:[b[T]];for(let w=0,C=y.length;w<C;w++){const R=y[w],L=Array.isArray(R.value)?R.value:[R.value];for(let U=0,I=L.length;U<I;U++){const F=L[U],N=g(F),Y=S%E,j=Y%N.boundary,Z=Y+j;S+=j,Z!==0&&E-Z<N.storage&&(S+=E-Z),R.__data=new Float32Array(N.storage/Float32Array.BYTES_PER_ELEMENT),R.__offset=S,S+=N.storage}}}const M=S%E;return M>0&&(S+=E-M),v.__size=S,v.__cache={},this}function g(v){const b={boundary:0,storage:0};return typeof v=="number"||typeof v=="boolean"?(b.boundary=4,b.storage=4):v.isVector2?(b.boundary=8,b.storage=8):v.isVector3||v.isColor?(b.boundary=16,b.storage=12):v.isVector4?(b.boundary=16,b.storage=16):v.isMatrix3?(b.boundary=48,b.storage=48):v.isMatrix4?(b.boundary=64,b.storage=64):v.isTexture?Qe("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(v)?(b.boundary=16,b.storage=v.byteLength):Qe("WebGLRenderer: Unsupported uniform value type.",v),b}function p(v){const b=v.target;b.removeEventListener("dispose",p);const S=a.indexOf(b.__bindingPointIndex);a.splice(S,1),n.deleteBuffer(r[b.id]),delete r[b.id],delete s[b.id]}function _(){for(const v in r)n.deleteBuffer(r[v]);a=[],r={},s={}}return{bind:l,update:c,dispose:_}}const HM=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]);let bi=null;function VM(){return bi===null&&(bi=new Dv(HM,16,16,Jr,Yi),bi.name="DFG_LUT",bi.minFilter=Gt,bi.magFilter=Gt,bi.wrapS=Vi,bi.wrapT=Vi,bi.generateMipmaps=!1,bi.needsUpdate=!0),bi}class WM{constructor(e={}){const{canvas:t=ov(),context:i=null,depth:r=!0,stencil:s=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:u="default",failIfMajorPerformanceCaveat:f=!1,reversedDepthBuffer:h=!1,outputBufferType:d=Yt}=e;this.isWebGLRenderer=!0;let m;if(i!==null){if(typeof WebGLRenderingContext<"u"&&i instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");m=i.getContextAttributes().alpha}else m=a;const g=d,p=new Set([ef,Qh,Jh]),_=new Set([Yt,Ui,Ha,Hs,Zh,$h]),v=new Uint32Array(4),b=new Int32Array(4),S=new $;let E=null,M=null;const T=[],x=[];let y=null;this.domElement=t,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=Di,this.toneMappingExposure=1,this.transmissionResolutionScale=1;const w=this;let C=!1,R=null;this._outputColorSpace=Tt;let L=0,U=0,I=null,F=-1,N=null;const Y=new Ut,j=new Ut;let Z=null;const O=new ut(0);let H=0,B=t.width,V=t.height,G=1,z=null,W=null;const q=new Ut(0,0,B,V),ce=new Ut(0,0,B,V);let me=!1;const Q=new Ym;let ie=!1,be=!1;const De=new zt,ye=new $,_e=new Ut,Ne={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let ae=!1;function Ee(){return I===null?G:1}let k=i;function de(P,J){return t.getContext(P,J)}try{const P={alpha:!0,depth:r,stencil:s,antialias:o,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:u,failIfMajorPerformanceCaveat:f};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${Ja}`),t.addEventListener("webglcontextlost",fe,!1),t.addEventListener("webglcontextrestored",Oe,!1),t.addEventListener("webglcontextcreationerror",$e,!1),k===null){const J="webgl2";if(k=de(J,P),k===null)throw de(J)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(P){throw pt("WebGLRenderer: "+P.message),P}let Pe,we,pe,Re,D,A,X,ee,he,xe,Te,te,le,ge,Ie,Me,Ae,He,Fe,Ye,K,ve,oe;function Le(){Pe=new Vy(k),Pe.init(),K=new IM(k,Pe),we=new Fy(k,Pe,e,K),pe=new UM(k,Pe),we.reversedDepthBuffer&&h&&pe.buffers.depth.setReversed(!0),Re=new jy(k),D=new vM,A=new LM(k,Pe,pe,D,we,K,Re),X=new Hy(w),ee=new Zv(k),ve=new Ly(k,ee),he=new Wy(k,ee,Re,ve),xe=new qy(k,he,ee,ve,Re),He=new Yy(k,we,A),Ie=new Ny(D),Te=new _M(w,X,Pe,we,ve,Ie),te=new zM(w,D),le=new yM,ge=new wM(Pe),Ae=new Uy(w,X,pe,xe,m,l),Me=new DM(w,xe,we),oe=new GM(k,Re,we,pe),Fe=new Iy(k,Pe,Re),Ye=new Xy(k,Pe,Re),Re.programs=Te.programs,w.capabilities=we,w.extensions=Pe,w.properties=D,w.renderLists=le,w.shadowMap=Me,w.state=pe,w.info=Re}Le(),g!==Yt&&(y=new Zy(g,t.width,t.height,r,s));const Se=new BM(w,k);this.xr=Se,this.getContext=function(){return k},this.getContextAttributes=function(){return k.getContextAttributes()},this.forceContextLoss=function(){const P=Pe.get("WEBGL_lose_context");P&&P.loseContext()},this.forceContextRestore=function(){const P=Pe.get("WEBGL_lose_context");P&&P.restoreContext()},this.getPixelRatio=function(){return G},this.setPixelRatio=function(P){P!==void 0&&(G=P,this.setSize(B,V,!1))},this.getSize=function(P){return P.set(B,V)},this.setSize=function(P,J,ue=!0){if(Se.isPresenting){Qe("WebGLRenderer: Can't change size while VR device is presenting.");return}B=P,V=J,t.width=Math.floor(P*G),t.height=Math.floor(J*G),ue===!0&&(t.style.width=P+"px",t.style.height=J+"px"),y!==null&&y.setSize(t.width,t.height),this.setViewport(0,0,P,J)},this.getDrawingBufferSize=function(P){return P.set(B*G,V*G).floor()},this.setDrawingBufferSize=function(P,J,ue){B=P,V=J,G=ue,t.width=Math.floor(P*ue),t.height=Math.floor(J*ue),this.setViewport(0,0,P,J)},this.setEffects=function(P){if(g===Yt){pt("THREE.WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(P){for(let J=0;J<P.length;J++)if(P[J].isOutputPass===!0){Qe("THREE.WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}y.setEffects(P||[])},this.getCurrentViewport=function(P){return P.copy(Y)},this.getViewport=function(P){return P.copy(q)},this.setViewport=function(P,J,ue,re){P.isVector4?q.set(P.x,P.y,P.z,P.w):q.set(P,J,ue,re),pe.viewport(Y.copy(q).multiplyScalar(G).round())},this.getScissor=function(P){return P.copy(ce)},this.setScissor=function(P,J,ue,re){P.isVector4?ce.set(P.x,P.y,P.z,P.w):ce.set(P,J,ue,re),pe.scissor(j.copy(ce).multiplyScalar(G).round())},this.getScissorTest=function(){return me},this.setScissorTest=function(P){pe.setScissorTest(me=P)},this.setOpaqueSort=function(P){z=P},this.setTransparentSort=function(P){W=P},this.getClearColor=function(P){return P.copy(Ae.getClearColor())},this.setClearColor=function(){Ae.setClearColor(...arguments)},this.getClearAlpha=function(){return Ae.getClearAlpha()},this.setClearAlpha=function(){Ae.setClearAlpha(...arguments)},this.clear=function(P=!0,J=!0,ue=!0){let re=0;if(P){let se=!1;if(I!==null){const ke=I.texture.format;se=p.has(ke)}if(se){const ke=I.texture.type,Ve=_.has(ke),Be=Ae.getClearColor(),je=Ae.getClearAlpha(),qe=Be.r,nt=Be.g,it=Be.b;Ve?(v[0]=qe,v[1]=nt,v[2]=it,v[3]=je,k.clearBufferuiv(k.COLOR,0,v)):(b[0]=qe,b[1]=nt,b[2]=it,b[3]=je,k.clearBufferiv(k.COLOR,0,b))}else re|=k.COLOR_BUFFER_BIT}J&&(re|=k.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),ue&&(re|=k.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),re!==0&&k.clear(re)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(P){P.setRenderer(this),R=P},this.dispose=function(){t.removeEventListener("webglcontextlost",fe,!1),t.removeEventListener("webglcontextrestored",Oe,!1),t.removeEventListener("webglcontextcreationerror",$e,!1),Ae.dispose(),le.dispose(),ge.dispose(),D.dispose(),X.dispose(),xe.dispose(),ve.dispose(),oe.dispose(),Te.dispose(),Se.dispose(),Se.removeEventListener("sessionstart",vi),Se.removeEventListener("sessionend",Zn),Ft.stop()};function fe(P){P.preventDefault(),ml("WebGLRenderer: Context Lost."),C=!0}function Oe(){ml("WebGLRenderer: Context Restored."),C=!1;const P=Re.autoReset,J=Me.enabled,ue=Me.autoUpdate,re=Me.needsUpdate,se=Me.type;Le(),Re.autoReset=P,Me.enabled=J,Me.autoUpdate=ue,Me.needsUpdate=re,Me.type=se}function $e(P){pt("WebGLRenderer: A WebGL context could not be created. Reason: ",P.statusMessage)}function ot(P){const J=P.target;J.removeEventListener("dispose",ot),tt(J)}function tt(P){Vt(P),D.remove(P)}function Vt(P){const J=D.get(P).programs;J!==void 0&&(J.forEach(function(ue){Te.releaseProgram(ue)}),P.isShaderMaterial&&Te.releaseShaderCache(P))}this.renderBufferDirect=function(P,J,ue,re,se,ke){J===null&&(J=Ne);const Ve=se.isMesh&&se.matrixWorld.determinant()<0,Be=os(P,J,ue,re,se);pe.setMaterial(re,Ve);let je=ue.index,qe=1;if(re.wireframe===!0){if(je=he.getWireframeAttribute(ue),je===void 0)return;qe=2}const nt=ue.drawRange,it=ue.attributes.position;let Ke=nt.start*qe,ht=(nt.start+nt.count)*qe;ke!==null&&(Ke=Math.max(Ke,ke.start*qe),ht=Math.min(ht,(ke.start+ke.count)*qe)),je!==null?(Ke=Math.max(Ke,0),ht=Math.min(ht,je.count)):it!=null&&(Ke=Math.max(Ke,0),ht=Math.min(ht,it.count));const Dt=ht-Ke;if(Dt<0||Dt===1/0)return;ve.setup(se,re,Be,ue,je);let Pt,_t=Fe;if(je!==null&&(Pt=ee.get(je),_t=Ye,_t.setIndex(Pt)),se.isMesh)re.wireframe===!0?(pe.setLineWidth(re.wireframeLinewidth*Ee()),_t.setMode(k.LINES)):_t.setMode(k.TRIANGLES);else if(se.isLine){let Et=re.linewidth;Et===void 0&&(Et=1),pe.setLineWidth(Et*Ee()),se.isLineSegments?_t.setMode(k.LINES):se.isLineLoop?_t.setMode(k.LINE_LOOP):_t.setMode(k.LINE_STRIP)}else se.isPoints?_t.setMode(k.POINTS):se.isSprite&&_t.setMode(k.TRIANGLES);if(se.isBatchedMesh)if(Pe.get("WEBGL_multi_draw"))_t.renderMultiDraw(se._multiDrawStarts,se._multiDrawCounts,se._multiDrawCount);else{const Et=se._multiDrawStarts,We=se._multiDrawCounts,rn=se._multiDrawCount,at=je?ee.get(je).bytesPerElement:1,xn=D.get(re).currentProgram.getUniforms();for(let yn=0;yn<rn;yn++)xn.setValue(k,"_gl_DrawID",yn),_t.render(Et[yn]/at,We[yn])}else if(se.isInstancedMesh)_t.renderInstances(Ke,Dt,se.count);else if(ue.isInstancedBufferGeometry){const Et=ue._maxInstanceCount!==void 0?ue._maxInstanceCount:1/0,We=Math.min(ue.instanceCount,Et);_t.renderInstances(Ke,Dt,We)}else _t.render(Ke,Dt)};function Kt(P,J,ue){P.transparent===!0&&P.side===An&&P.forceSinglePass===!1?(P.side=on,P.needsUpdate=!0,Ii(P,J,ue),P.side=ji,P.needsUpdate=!0,Ii(P,J,ue),P.side=An):Ii(P,J,ue)}this.compile=function(P,J,ue=null){ue===null&&(ue=P),M=ge.get(ue),M.init(J),x.push(M),ue.traverseVisible(function(se){se.isLight&&se.layers.test(J.layers)&&(M.pushLight(se),se.castShadow&&M.pushShadow(se))}),P!==ue&&P.traverseVisible(function(se){se.isLight&&se.layers.test(J.layers)&&(M.pushLight(se),se.castShadow&&M.pushShadow(se))}),M.setupLights();const re=new Set;return P.traverse(function(se){if(!(se.isMesh||se.isPoints||se.isLine||se.isSprite))return;const ke=se.material;if(ke)if(Array.isArray(ke))for(let Ve=0;Ve<ke.length;Ve++){const Be=ke[Ve];Kt(Be,ue,se),re.add(Be)}else Kt(ke,ue,se),re.add(ke)}),M=x.pop(),re},this.compileAsync=function(P,J,ue=null){const re=this.compile(P,J,ue);return new Promise(se=>{function ke(){if(re.forEach(function(Ve){D.get(Ve).currentProgram.isReady()&&re.delete(Ve)}),re.size===0){se(P);return}setTimeout(ke,10)}Pe.get("KHR_parallel_shader_compile")!==null?ke():setTimeout(ke,10)})};let In=null;function _i(P){In&&In(P)}function vi(){Ft.stop()}function Zn(){Ft.start()}const Ft=new t0;Ft.setAnimationLoop(_i),typeof self<"u"&&Ft.setContext(self),this.setAnimationLoop=function(P){In=P,Se.setAnimationLoop(P),P===null?Ft.stop():Ft.start()},Se.addEventListener("sessionstart",vi),Se.addEventListener("sessionend",Zn),this.render=function(P,J){if(J!==void 0&&J.isCamera!==!0){pt("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(C===!0)return;R!==null&&R.renderStart(P,J);const ue=Se.enabled===!0&&Se.isPresenting===!0,re=y!==null&&(I===null||ue)&&y.begin(w,I);if(P.matrixWorldAutoUpdate===!0&&P.updateMatrixWorld(),J.parent===null&&J.matrixWorldAutoUpdate===!0&&J.updateMatrixWorld(),Se.enabled===!0&&Se.isPresenting===!0&&(y===null||y.isCompositing()===!1)&&(Se.cameraAutoUpdate===!0&&Se.updateCamera(J),J=Se.getCamera()),P.isScene===!0&&P.onBeforeRender(w,P,J,I),M=ge.get(P,x.length),M.init(J),M.state.textureUnits=A.getTextureUnits(),x.push(M),De.multiplyMatrices(J.projectionMatrix,J.matrixWorldInverse),Q.setFromProjectionMatrix(De,Ri,J.reversedDepth),be=this.localClippingEnabled,ie=Ie.init(this.clippingPlanes,be),E=le.get(P,T.length),E.init(),T.push(E),Se.enabled===!0&&Se.isPresenting===!0){const Ve=w.xr.getDepthSensingMesh();Ve!==null&&ri(Ve,J,-1/0,w.sortObjects)}ri(P,J,0,w.sortObjects),E.finish(),w.sortObjects===!0&&E.sort(z,W),ae=Se.enabled===!1||Se.isPresenting===!1||Se.hasDepthSensing()===!1,ae&&Ae.addToRenderList(E,P),this.info.render.frame++,ie===!0&&Ie.beginShadows();const se=M.state.shadowsArray;if(Me.render(se,P,J),ie===!0&&Ie.endShadows(),this.info.autoReset===!0&&this.info.reset(),(re&&y.hasRenderPass())===!1){const Ve=E.opaque,Be=E.transmissive;if(M.setupLights(),J.isArrayCamera){const je=J.cameras;if(Be.length>0)for(let qe=0,nt=je.length;qe<nt;qe++){const it=je[qe];rs(Ve,Be,P,it)}ae&&Ae.render(P);for(let qe=0,nt=je.length;qe<nt;qe++){const it=je[qe];ra(E,P,it,it.viewport)}}else Be.length>0&&rs(Ve,Be,P,J),ae&&Ae.render(P),ra(E,P,J)}I!==null&&U===0&&(A.updateMultisampleRenderTarget(I),A.updateRenderTargetMipmap(I)),re&&y.end(w),P.isScene===!0&&P.onAfterRender(w,P,J),ve.resetDefaultState(),F=-1,N=null,x.pop(),x.length>0?(M=x[x.length-1],A.setTextureUnits(M.state.textureUnits),ie===!0&&Ie.setGlobalState(w.clippingPlanes,M.state.camera)):M=null,T.pop(),T.length>0?E=T[T.length-1]:E=null,R!==null&&R.renderEnd()};function ri(P,J,ue,re){if(P.visible===!1)return;if(P.layers.test(J.layers)){if(P.isGroup)ue=P.renderOrder;else if(P.isLOD)P.autoUpdate===!0&&P.update(J);else if(P.isLightProbeGrid)M.pushLightProbeGrid(P);else if(P.isLight)M.pushLight(P),P.castShadow&&M.pushShadow(P);else if(P.isSprite){if(!P.frustumCulled||Q.intersectsSprite(P)){re&&_e.setFromMatrixPosition(P.matrixWorld).applyMatrix4(De);const Ve=xe.update(P),Be=P.material;Be.visible&&E.push(P,Ve,Be,ue,_e.z,null)}}else if((P.isMesh||P.isLine||P.isPoints)&&(!P.frustumCulled||Q.intersectsObject(P))){const Ve=xe.update(P),Be=P.material;if(re&&(P.boundingSphere!==void 0?(P.boundingSphere===null&&P.computeBoundingSphere(),_e.copy(P.boundingSphere.center)):(Ve.boundingSphere===null&&Ve.computeBoundingSphere(),_e.copy(Ve.boundingSphere.center)),_e.applyMatrix4(P.matrixWorld).applyMatrix4(De)),Array.isArray(Be)){const je=Ve.groups;for(let qe=0,nt=je.length;qe<nt;qe++){const it=je[qe],Ke=Be[it.materialIndex];Ke&&Ke.visible&&E.push(P,Ve,Ke,ue,_e.z,it)}}else Be.visible&&E.push(P,Ve,Be,ue,_e.z,null)}}const ke=P.children;for(let Ve=0,Be=ke.length;Ve<Be;Ve++)ri(ke[Ve],J,ue,re)}function ra(P,J,ue,re){const{opaque:se,transmissive:ke,transparent:Ve}=P;M.setupLightsView(ue),ie===!0&&Ie.setGlobalState(w.clippingPlanes,ue),re&&pe.viewport(Y.copy(re)),se.length>0&&ss(se,J,ue),ke.length>0&&ss(ke,J,ue),Ve.length>0&&ss(Ve,J,ue),pe.buffers.depth.setTest(!0),pe.buffers.depth.setMask(!0),pe.buffers.color.setMask(!0),pe.setPolygonOffset(!1)}function rs(P,J,ue,re){if((ue.isScene===!0?ue.overrideMaterial:null)!==null)return;if(M.state.transmissionRenderTarget[re.id]===void 0){const Ke=Pe.has("EXT_color_buffer_half_float")||Pe.has("EXT_color_buffer_float");M.state.transmissionRenderTarget[re.id]=new Qt(1,1,{generateMipmaps:!0,type:Ke?Yi:Yt,minFilter:Gr,samples:Math.max(4,we.samples),stencilBuffer:s,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:ft.workingColorSpace})}const ke=M.state.transmissionRenderTarget[re.id],Ve=re.viewport||Y;ke.setSize(Ve.z*w.transmissionResolutionScale,Ve.w*w.transmissionResolutionScale);const Be=w.getRenderTarget(),je=w.getActiveCubeFace(),qe=w.getActiveMipmapLevel();w.setRenderTarget(ke),w.getClearColor(O),H=w.getClearAlpha(),H<1&&w.setClearColor(16777215,.5),w.clear(),ae&&Ae.render(ue);const nt=w.toneMapping;w.toneMapping=Di;const it=re.viewport;if(re.viewport!==void 0&&(re.viewport=void 0),M.setupLightsView(re),ie===!0&&Ie.setGlobalState(w.clippingPlanes,re),ss(P,ue,re),A.updateMultisampleRenderTarget(ke),A.updateRenderTargetMipmap(ke),Pe.has("WEBGL_multisampled_render_to_texture")===!1){let Ke=!1;for(let ht=0,Dt=J.length;ht<Dt;ht++){const Pt=J[ht],{object:_t,geometry:Et,material:We,group:rn}=Pt;if(We.side===An&&_t.layers.test(re.layers)){const at=We.side;We.side=on,We.needsUpdate=!0,sa(_t,ue,re,Et,We,rn),We.side=at,We.needsUpdate=!0,Ke=!0}}Ke===!0&&(A.updateMultisampleRenderTarget(ke),A.updateRenderTargetMipmap(ke))}w.setRenderTarget(Be,je,qe),w.setClearColor(O,H),it!==void 0&&(re.viewport=it),w.toneMapping=nt}function ss(P,J,ue){const re=J.isScene===!0?J.overrideMaterial:null;for(let se=0,ke=P.length;se<ke;se++){const Ve=P[se],{object:Be,geometry:je,group:qe}=Ve;let nt=Ve.material;nt.allowOverride===!0&&re!==null&&(nt=re),Be.layers.test(ue.layers)&&sa(Be,J,ue,je,nt,qe)}}function sa(P,J,ue,re,se,ke){P.onBeforeRender(w,J,ue,re,se,ke),P.modelViewMatrix.multiplyMatrices(ue.matrixWorldInverse,P.matrixWorld),P.normalMatrix.getNormalMatrix(P.modelViewMatrix),se.onBeforeRender(w,J,ue,re,P,ke),se.transparent===!0&&se.side===An&&se.forceSinglePass===!1?(se.side=on,se.needsUpdate=!0,w.renderBufferDirect(ue,J,re,se,P,ke),se.side=ji,se.needsUpdate=!0,w.renderBufferDirect(ue,J,re,se,P,ke),se.side=An):w.renderBufferDirect(ue,J,re,se,P,ke),P.onAfterRender(w,J,ue,re,se,ke)}function Ii(P,J,ue){J.isScene!==!0&&(J=Ne);const re=D.get(P),se=M.state.lights,ke=M.state.shadowsArray,Ve=se.state.version,Be=Te.getParameters(P,se.state,ke,J,ue,M.state.lightProbeGridArray),je=Te.getProgramCacheKey(Be);let qe=re.programs;re.environment=P.isMeshStandardMaterial||P.isMeshLambertMaterial||P.isMeshPhongMaterial?J.environment:null,re.fog=J.fog;const nt=P.isMeshStandardMaterial||P.isMeshLambertMaterial&&!P.envMap||P.isMeshPhongMaterial&&!P.envMap;re.envMap=X.get(P.envMap||re.environment,nt),re.envMapRotation=re.environment!==null&&P.envMap===null?J.environmentRotation:P.envMapRotation,qe===void 0&&(P.addEventListener("dispose",ot),qe=new Map,re.programs=qe);let it=qe.get(je);if(it!==void 0){if(re.currentProgram===it&&re.lightsStateVersion===Ve)return so(P,Be),it}else Be.uniforms=Te.getUniforms(P),R!==null&&P.isNodeMaterial&&R.build(P,ue,Be),P.onBeforeCompile(Be,w),it=Te.acquireProgram(Be,je),qe.set(je,it),re.uniforms=Be.uniforms;const Ke=re.uniforms;return(!P.isShaderMaterial&&!P.isRawShaderMaterial||P.clipping===!0)&&(Ke.clippingPlanes=Ie.uniform),so(P,Be),re.needsLights=oa(P),re.lightsStateVersion=Ve,re.needsLights&&(Ke.ambientLightColor.value=se.state.ambient,Ke.lightProbe.value=se.state.probe,Ke.directionalLights.value=se.state.directional,Ke.directionalLightShadows.value=se.state.directionalShadow,Ke.spotLights.value=se.state.spot,Ke.spotLightShadows.value=se.state.spotShadow,Ke.rectAreaLights.value=se.state.rectArea,Ke.ltc_1.value=se.state.rectAreaLTC1,Ke.ltc_2.value=se.state.rectAreaLTC2,Ke.pointLights.value=se.state.point,Ke.pointLightShadows.value=se.state.pointShadow,Ke.hemisphereLights.value=se.state.hemi,Ke.directionalShadowMatrix.value=se.state.directionalShadowMatrix,Ke.spotLightMatrix.value=se.state.spotLightMatrix,Ke.spotLightMap.value=se.state.spotLightMap,Ke.pointShadowMatrix.value=se.state.pointShadowMatrix),re.lightProbeGrid=M.state.lightProbeGridArray.length>0,re.currentProgram=it,re.uniformsList=null,it}function as(P){if(P.uniformsList===null){const J=P.currentProgram.getUniforms();P.uniformsList=tl.seqWithValue(J.seq,P.uniforms)}return P.uniformsList}function so(P,J){const ue=D.get(P);ue.outputColorSpace=J.outputColorSpace,ue.batching=J.batching,ue.batchingColor=J.batchingColor,ue.instancing=J.instancing,ue.instancingColor=J.instancingColor,ue.instancingMorph=J.instancingMorph,ue.skinning=J.skinning,ue.morphTargets=J.morphTargets,ue.morphNormals=J.morphNormals,ue.morphColors=J.morphColors,ue.morphTargetsCount=J.morphTargetsCount,ue.numClippingPlanes=J.numClippingPlanes,ue.numIntersection=J.numClipIntersection,ue.vertexAlphas=J.vertexAlphas,ue.vertexTangents=J.vertexTangents,ue.toneMapping=J.toneMapping}function ao(P,J){if(P.length===0)return null;if(P.length===1)return P[0].texture!==null?P[0]:null;S.setFromMatrixPosition(J.matrixWorld);for(let ue=0,re=P.length;ue<re;ue++){const se=P[ue];if(se.texture!==null&&se.boundingBox.containsPoint(S))return se}return null}function os(P,J,ue,re,se){J.isScene!==!0&&(J=Ne),A.resetTextureUnits();const ke=J.fog,Ve=re.isMeshStandardMaterial||re.isMeshLambertMaterial||re.isMeshPhongMaterial?J.environment:null,Be=I===null?w.outputColorSpace:I.isXRRenderTarget===!0?I.texture.colorSpace:ft.workingColorSpace,je=re.isMeshStandardMaterial||re.isMeshLambertMaterial&&!re.envMap||re.isMeshPhongMaterial&&!re.envMap,qe=X.get(re.envMap||Ve,je),nt=re.vertexColors===!0&&!!ue.attributes.color&&ue.attributes.color.itemSize===4,it=!!ue.attributes.tangent&&(!!re.normalMap||re.anisotropy>0),Ke=!!ue.morphAttributes.position,ht=!!ue.morphAttributes.normal,Dt=!!ue.morphAttributes.color;let Pt=Di;re.toneMapped&&(I===null||I.isXRRenderTarget===!0)&&(Pt=w.toneMapping);const _t=ue.morphAttributes.position||ue.morphAttributes.normal||ue.morphAttributes.color,Et=_t!==void 0?_t.length:0,We=D.get(re),rn=M.state.lights;if(ie===!0&&(be===!0||P!==N)){const mt=P===N&&re.id===F;Ie.setState(re,P,mt)}let at=!1;re.version===We.__version?(We.needsLights&&We.lightsStateVersion!==rn.state.version||We.outputColorSpace!==Be||se.isBatchedMesh&&We.batching===!1||!se.isBatchedMesh&&We.batching===!0||se.isBatchedMesh&&We.batchingColor===!0&&se.colorTexture===null||se.isBatchedMesh&&We.batchingColor===!1&&se.colorTexture!==null||se.isInstancedMesh&&We.instancing===!1||!se.isInstancedMesh&&We.instancing===!0||se.isSkinnedMesh&&We.skinning===!1||!se.isSkinnedMesh&&We.skinning===!0||se.isInstancedMesh&&We.instancingColor===!0&&se.instanceColor===null||se.isInstancedMesh&&We.instancingColor===!1&&se.instanceColor!==null||se.isInstancedMesh&&We.instancingMorph===!0&&se.morphTexture===null||se.isInstancedMesh&&We.instancingMorph===!1&&se.morphTexture!==null||We.envMap!==qe||re.fog===!0&&We.fog!==ke||We.numClippingPlanes!==void 0&&(We.numClippingPlanes!==Ie.numPlanes||We.numIntersection!==Ie.numIntersection)||We.vertexAlphas!==nt||We.vertexTangents!==it||We.morphTargets!==Ke||We.morphNormals!==ht||We.morphColors!==Dt||We.toneMapping!==Pt||We.morphTargetsCount!==Et||!!We.lightProbeGrid!=M.state.lightProbeGridArray.length>0)&&(at=!0):(at=!0,We.__version=re.version);let xn=We.currentProgram;at===!0&&(xn=Ii(re,J,se),R&&re.isNodeMaterial&&R.onUpdateProgram(re,xn,We));let yn=!1,Fn=!1,xi=!1;const xt=xn.getUniforms(),Lt=We.uniforms;if(pe.useProgram(xn.program)&&(yn=!0,Fn=!0,xi=!0),re.id!==F&&(F=re.id,Fn=!0),We.needsLights){const mt=ao(M.state.lightProbeGridArray,se);We.lightProbeGrid!==mt&&(We.lightProbeGrid=mt,Fn=!0)}if(yn||N!==P){pe.buffers.depth.getReversed()&&P.reversedDepth!==!0&&(P._reversedDepth=!0,P.updateProjectionMatrix()),xt.setValue(k,"projectionMatrix",P.projectionMatrix),xt.setValue(k,"viewMatrix",P.matrixWorldInverse);const si=xt.map.cameraPosition;si!==void 0&&si.setValue(k,ye.setFromMatrixPosition(P.matrixWorld)),we.logarithmicDepthBuffer&&xt.setValue(k,"logDepthBufFC",2/(Math.log(P.far+1)/Math.LN2)),(re.isMeshPhongMaterial||re.isMeshToonMaterial||re.isMeshLambertMaterial||re.isMeshBasicMaterial||re.isMeshStandardMaterial||re.isShaderMaterial)&&xt.setValue(k,"isOrthographic",P.isOrthographicCamera===!0),N!==P&&(N=P,Fn=!0,xi=!0)}if(We.needsLights&&(rn.state.directionalShadowMap.length>0&&xt.setValue(k,"directionalShadowMap",rn.state.directionalShadowMap,A),rn.state.spotShadowMap.length>0&&xt.setValue(k,"spotShadowMap",rn.state.spotShadowMap,A),rn.state.pointShadowMap.length>0&&xt.setValue(k,"pointShadowMap",rn.state.pointShadowMap,A)),se.isSkinnedMesh){xt.setOptional(k,se,"bindMatrix"),xt.setOptional(k,se,"bindMatrixInverse");const mt=se.skeleton;mt&&(mt.boneTexture===null&&mt.computeBoneTexture(),xt.setValue(k,"boneTexture",mt.boneTexture,A))}se.isBatchedMesh&&(xt.setOptional(k,se,"batchingTexture"),xt.setValue(k,"batchingTexture",se._matricesTexture,A),xt.setOptional(k,se,"batchingIdTexture"),xt.setValue(k,"batchingIdTexture",se._indirectTexture,A),xt.setOptional(k,se,"batchingColorTexture"),se._colorsTexture!==null&&xt.setValue(k,"batchingColorTexture",se._colorsTexture,A));const $n=ue.morphAttributes;if(($n.position!==void 0||$n.normal!==void 0||$n.color!==void 0)&&He.update(se,ue,xn),(Fn||We.receiveShadow!==se.receiveShadow)&&(We.receiveShadow=se.receiveShadow,xt.setValue(k,"receiveShadow",se.receiveShadow)),(re.isMeshStandardMaterial||re.isMeshLambertMaterial||re.isMeshPhongMaterial)&&re.envMap===null&&J.environment!==null&&(Lt.envMapIntensity.value=J.environmentIntensity),Lt.dfgLUT!==void 0&&(Lt.dfgLUT.value=VM()),Fn){if(xt.setValue(k,"toneMappingExposure",w.toneMappingExposure),We.needsLights&&aa(Lt,xi),ke&&re.fog===!0&&te.refreshFogUniforms(Lt,ke),te.refreshMaterialUniforms(Lt,re,G,V,M.state.transmissionRenderTarget[P.id]),We.needsLights&&We.lightProbeGrid){const mt=We.lightProbeGrid;Lt.probesSH.value=mt.texture,Lt.probesMin.value.copy(mt.boundingBox.min),Lt.probesMax.value.copy(mt.boundingBox.max),Lt.probesResolution.value.copy(mt.resolution)}tl.upload(k,as(We),Lt,A)}if(re.isShaderMaterial&&re.uniformsNeedUpdate===!0&&(tl.upload(k,as(We),Lt,A),re.uniformsNeedUpdate=!1),re.isSpriteMaterial&&xt.setValue(k,"center",se.center),xt.setValue(k,"modelViewMatrix",se.modelViewMatrix),xt.setValue(k,"normalMatrix",se.normalMatrix),xt.setValue(k,"modelMatrix",se.matrixWorld),re.uniformsGroups!==void 0){const mt=re.uniformsGroups;for(let si=0,ai=mt.length;si<ai;si++){const Fi=mt[si];oe.update(Fi,xn),oe.bind(Fi,xn)}}return xn}function aa(P,J){P.ambientLightColor.needsUpdate=J,P.lightProbe.needsUpdate=J,P.directionalLights.needsUpdate=J,P.directionalLightShadows.needsUpdate=J,P.pointLights.needsUpdate=J,P.pointLightShadows.needsUpdate=J,P.spotLights.needsUpdate=J,P.spotLightShadows.needsUpdate=J,P.rectAreaLights.needsUpdate=J,P.hemisphereLights.needsUpdate=J}function oa(P){return P.isMeshLambertMaterial||P.isMeshToonMaterial||P.isMeshPhongMaterial||P.isMeshStandardMaterial||P.isShadowMaterial||P.isShaderMaterial&&P.lights===!0}this.getActiveCubeFace=function(){return L},this.getActiveMipmapLevel=function(){return U},this.getRenderTarget=function(){return I},this.setRenderTargetTextures=function(P,J,ue){const re=D.get(P);re.__autoAllocateDepthBuffer=P.resolveDepthBuffer===!1,re.__autoAllocateDepthBuffer===!1&&(re.__useRenderToTexture=!1),D.get(P.texture).__webglTexture=J,D.get(P.depthTexture).__webglTexture=re.__autoAllocateDepthBuffer?void 0:ue,re.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(P,J){const ue=D.get(P);ue.__webglFramebuffer=J,ue.__useDefaultFramebuffer=J===void 0};const Je=k.createFramebuffer();this.setRenderTarget=function(P,J=0,ue=0){I=P,L=J,U=ue;let re=null,se=!1,ke=!1;if(P){const Be=D.get(P);if(Be.__useDefaultFramebuffer!==void 0){pe.bindFramebuffer(k.FRAMEBUFFER,Be.__webglFramebuffer),Y.copy(P.viewport),j.copy(P.scissor),Z=P.scissorTest,pe.viewport(Y),pe.scissor(j),pe.setScissorTest(Z),F=-1;return}else if(Be.__webglFramebuffer===void 0)A.setupRenderTarget(P);else if(Be.__hasExternalTextures)A.rebindTextures(P,D.get(P.texture).__webglTexture,D.get(P.depthTexture).__webglTexture);else if(P.depthBuffer){const nt=P.depthTexture;if(Be.__boundDepthTexture!==nt){if(nt!==null&&D.has(nt)&&(P.width!==nt.image.width||P.height!==nt.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");A.setupDepthRenderbuffer(P)}}const je=P.texture;(je.isData3DTexture||je.isDataArrayTexture||je.isCompressedArrayTexture)&&(ke=!0);const qe=D.get(P).__webglFramebuffer;P.isWebGLCubeRenderTarget?(Array.isArray(qe[J])?re=qe[J][ue]:re=qe[J],se=!0):P.samples>0&&A.useMultisampledRTT(P)===!1?re=D.get(P).__webglMultisampledFramebuffer:Array.isArray(qe)?re=qe[ue]:re=qe,Y.copy(P.viewport),j.copy(P.scissor),Z=P.scissorTest}else Y.copy(q).multiplyScalar(G).floor(),j.copy(ce).multiplyScalar(G).floor(),Z=me;if(ue!==0&&(re=Je),pe.bindFramebuffer(k.FRAMEBUFFER,re)&&pe.drawBuffers(P,re),pe.viewport(Y),pe.scissor(j),pe.setScissorTest(Z),se){const Be=D.get(P.texture);k.framebufferTexture2D(k.FRAMEBUFFER,k.COLOR_ATTACHMENT0,k.TEXTURE_CUBE_MAP_POSITIVE_X+J,Be.__webglTexture,ue)}else if(ke){const Be=J;for(let je=0;je<P.textures.length;je++){const qe=D.get(P.textures[je]);k.framebufferTextureLayer(k.FRAMEBUFFER,k.COLOR_ATTACHMENT0+je,qe.__webglTexture,ue,Be)}}else if(P!==null&&ue!==0){const Be=D.get(P.texture);k.framebufferTexture2D(k.FRAMEBUFFER,k.COLOR_ATTACHMENT0,k.TEXTURE_2D,Be.__webglTexture,ue)}F=-1},this.readRenderTargetPixels=function(P,J,ue,re,se,ke,Ve,Be=0){if(!(P&&P.isWebGLRenderTarget)){pt("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let je=D.get(P).__webglFramebuffer;if(P.isWebGLCubeRenderTarget&&Ve!==void 0&&(je=je[Ve]),je){pe.bindFramebuffer(k.FRAMEBUFFER,je);try{const qe=P.textures[Be],nt=qe.format,it=qe.type;if(P.textures.length>1&&k.readBuffer(k.COLOR_ATTACHMENT0+Be),!we.textureFormatReadable(nt)){pt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!we.textureTypeReadable(it)){pt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}J>=0&&J<=P.width-re&&ue>=0&&ue<=P.height-se&&k.readPixels(J,ue,re,se,K.convert(nt),K.convert(it),ke)}finally{const qe=I!==null?D.get(I).__webglFramebuffer:null;pe.bindFramebuffer(k.FRAMEBUFFER,qe)}}},this.readRenderTargetPixelsAsync=async function(P,J,ue,re,se,ke,Ve,Be=0){if(!(P&&P.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let je=D.get(P).__webglFramebuffer;if(P.isWebGLCubeRenderTarget&&Ve!==void 0&&(je=je[Ve]),je)if(J>=0&&J<=P.width-re&&ue>=0&&ue<=P.height-se){pe.bindFramebuffer(k.FRAMEBUFFER,je);const qe=P.textures[Be],nt=qe.format,it=qe.type;if(P.textures.length>1&&k.readBuffer(k.COLOR_ATTACHMENT0+Be),!we.textureFormatReadable(nt))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!we.textureTypeReadable(it))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");const Ke=k.createBuffer();k.bindBuffer(k.PIXEL_PACK_BUFFER,Ke),k.bufferData(k.PIXEL_PACK_BUFFER,ke.byteLength,k.STREAM_READ),k.readPixels(J,ue,re,se,K.convert(nt),K.convert(it),0);const ht=I!==null?D.get(I).__webglFramebuffer:null;pe.bindFramebuffer(k.FRAMEBUFFER,ht);const Dt=k.fenceSync(k.SYNC_GPU_COMMANDS_COMPLETE,0);return k.flush(),await lv(k,Dt,4),k.bindBuffer(k.PIXEL_PACK_BUFFER,Ke),k.getBufferSubData(k.PIXEL_PACK_BUFFER,0,ke),k.deleteBuffer(Ke),k.deleteSync(Dt),ke}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(P,J=null,ue=0){const re=Math.pow(2,-ue),se=Math.floor(P.image.width*re),ke=Math.floor(P.image.height*re),Ve=J!==null?J.x:0,Be=J!==null?J.y:0;A.setTexture2D(P,0),k.copyTexSubImage2D(k.TEXTURE_2D,ue,0,0,Ve,Be,se,ke),pe.unbindTexture()};const Cr=k.createFramebuffer(),Ql=k.createFramebuffer();this.copyTextureToTexture=function(P,J,ue=null,re=null,se=0,ke=0){let Ve,Be,je,qe,nt,it,Ke,ht,Dt;const Pt=P.isCompressedTexture?P.mipmaps[ke]:P.image;if(ue!==null)Ve=ue.max.x-ue.min.x,Be=ue.max.y-ue.min.y,je=ue.isBox3?ue.max.z-ue.min.z:1,qe=ue.min.x,nt=ue.min.y,it=ue.isBox3?ue.min.z:0;else{const Lt=Math.pow(2,-se);Ve=Math.floor(Pt.width*Lt),Be=Math.floor(Pt.height*Lt),P.isDataArrayTexture?je=Pt.depth:P.isData3DTexture?je=Math.floor(Pt.depth*Lt):je=1,qe=0,nt=0,it=0}re!==null?(Ke=re.x,ht=re.y,Dt=re.z):(Ke=0,ht=0,Dt=0);const _t=K.convert(J.format),Et=K.convert(J.type);let We;J.isData3DTexture?(A.setTexture3D(J,0),We=k.TEXTURE_3D):J.isDataArrayTexture||J.isCompressedArrayTexture?(A.setTexture2DArray(J,0),We=k.TEXTURE_2D_ARRAY):(A.setTexture2D(J,0),We=k.TEXTURE_2D),pe.activeTexture(k.TEXTURE0),pe.pixelStorei(k.UNPACK_FLIP_Y_WEBGL,J.flipY),pe.pixelStorei(k.UNPACK_PREMULTIPLY_ALPHA_WEBGL,J.premultiplyAlpha),pe.pixelStorei(k.UNPACK_ALIGNMENT,J.unpackAlignment);const rn=pe.getParameter(k.UNPACK_ROW_LENGTH),at=pe.getParameter(k.UNPACK_IMAGE_HEIGHT),xn=pe.getParameter(k.UNPACK_SKIP_PIXELS),yn=pe.getParameter(k.UNPACK_SKIP_ROWS),Fn=pe.getParameter(k.UNPACK_SKIP_IMAGES);pe.pixelStorei(k.UNPACK_ROW_LENGTH,Pt.width),pe.pixelStorei(k.UNPACK_IMAGE_HEIGHT,Pt.height),pe.pixelStorei(k.UNPACK_SKIP_PIXELS,qe),pe.pixelStorei(k.UNPACK_SKIP_ROWS,nt),pe.pixelStorei(k.UNPACK_SKIP_IMAGES,it);const xi=P.isDataArrayTexture||P.isData3DTexture,xt=J.isDataArrayTexture||J.isData3DTexture;if(P.isDepthTexture){const Lt=D.get(P),$n=D.get(J),mt=D.get(Lt.__renderTarget),si=D.get($n.__renderTarget);pe.bindFramebuffer(k.READ_FRAMEBUFFER,mt.__webglFramebuffer),pe.bindFramebuffer(k.DRAW_FRAMEBUFFER,si.__webglFramebuffer);for(let ai=0;ai<je;ai++)xi&&(k.framebufferTextureLayer(k.READ_FRAMEBUFFER,k.COLOR_ATTACHMENT0,D.get(P).__webglTexture,se,it+ai),k.framebufferTextureLayer(k.DRAW_FRAMEBUFFER,k.COLOR_ATTACHMENT0,D.get(J).__webglTexture,ke,Dt+ai)),k.blitFramebuffer(qe,nt,Ve,Be,Ke,ht,Ve,Be,k.DEPTH_BUFFER_BIT,k.NEAREST);pe.bindFramebuffer(k.READ_FRAMEBUFFER,null),pe.bindFramebuffer(k.DRAW_FRAMEBUFFER,null)}else if(se!==0||P.isRenderTargetTexture||D.has(P)){const Lt=D.get(P),$n=D.get(J);pe.bindFramebuffer(k.READ_FRAMEBUFFER,Cr),pe.bindFramebuffer(k.DRAW_FRAMEBUFFER,Ql);for(let mt=0;mt<je;mt++)xi?k.framebufferTextureLayer(k.READ_FRAMEBUFFER,k.COLOR_ATTACHMENT0,Lt.__webglTexture,se,it+mt):k.framebufferTexture2D(k.READ_FRAMEBUFFER,k.COLOR_ATTACHMENT0,k.TEXTURE_2D,Lt.__webglTexture,se),xt?k.framebufferTextureLayer(k.DRAW_FRAMEBUFFER,k.COLOR_ATTACHMENT0,$n.__webglTexture,ke,Dt+mt):k.framebufferTexture2D(k.DRAW_FRAMEBUFFER,k.COLOR_ATTACHMENT0,k.TEXTURE_2D,$n.__webglTexture,ke),se!==0?k.blitFramebuffer(qe,nt,Ve,Be,Ke,ht,Ve,Be,k.COLOR_BUFFER_BIT,k.NEAREST):xt?k.copyTexSubImage3D(We,ke,Ke,ht,Dt+mt,qe,nt,Ve,Be):k.copyTexSubImage2D(We,ke,Ke,ht,qe,nt,Ve,Be);pe.bindFramebuffer(k.READ_FRAMEBUFFER,null),pe.bindFramebuffer(k.DRAW_FRAMEBUFFER,null)}else xt?P.isDataTexture||P.isData3DTexture?k.texSubImage3D(We,ke,Ke,ht,Dt,Ve,Be,je,_t,Et,Pt.data):J.isCompressedArrayTexture?k.compressedTexSubImage3D(We,ke,Ke,ht,Dt,Ve,Be,je,_t,Pt.data):k.texSubImage3D(We,ke,Ke,ht,Dt,Ve,Be,je,_t,Et,Pt):P.isDataTexture?k.texSubImage2D(k.TEXTURE_2D,ke,Ke,ht,Ve,Be,_t,Et,Pt.data):P.isCompressedTexture?k.compressedTexSubImage2D(k.TEXTURE_2D,ke,Ke,ht,Pt.width,Pt.height,_t,Pt.data):k.texSubImage2D(k.TEXTURE_2D,ke,Ke,ht,Ve,Be,_t,Et,Pt);pe.pixelStorei(k.UNPACK_ROW_LENGTH,rn),pe.pixelStorei(k.UNPACK_IMAGE_HEIGHT,at),pe.pixelStorei(k.UNPACK_SKIP_PIXELS,xn),pe.pixelStorei(k.UNPACK_SKIP_ROWS,yn),pe.pixelStorei(k.UNPACK_SKIP_IMAGES,Fn),ke===0&&J.generateMipmaps&&k.generateMipmap(We),pe.unbindTexture()},this.initRenderTarget=function(P){D.get(P).__webglFramebuffer===void 0&&A.setupRenderTarget(P)},this.initTexture=function(P){P.isCubeTexture?A.setTextureCube(P,0):P.isData3DTexture?A.setTexture3D(P,0):P.isDataArrayTexture||P.isCompressedArrayTexture?A.setTexture2DArray(P,0):A.setTexture2D(P,0),pe.unbindTexture()},this.resetState=function(){L=0,U=0,I=null,pe.reset(),ve.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Ri}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const t=this.getContext();t.drawingBufferColorSpace=ft._getDrawingBufferColorSpace(e),t.unpackColorSpace=ft._getUnpackColorSpace()}}function XM(){var n=Object.create(null);function e(r,s){var a=r.id,o=r.name,l=r.dependencies;l===void 0&&(l=[]);var c=r.init;c===void 0&&(c=function(){});var u=r.getTransferables;if(u===void 0&&(u=null),!n[a])try{l=l.map(function(h){return h&&h.isWorkerModule&&(e(h,function(d){if(d instanceof Error)throw d}),h=n[h.id].value),h}),c=i("<"+o+">.init",c),u&&(u=i("<"+o+">.getTransferables",u));var f=null;typeof c=="function"?f=c.apply(void 0,l):console.error("worker module init function failed to rehydrate"),n[a]={id:a,value:f,getTransferables:u},s(f)}catch(h){h&&h.noLog||console.error(h),s(h)}}function t(r,s){var a,o=r.id,l=r.args;(!n[o]||typeof n[o].value!="function")&&s(new Error("Worker module "+o+": not found or its 'init' did not return a function"));try{var c=(a=n[o]).value.apply(a,l);c&&typeof c.then=="function"?c.then(u,function(f){return s(f instanceof Error?f:new Error(""+f))}):u(c)}catch(f){s(f)}function u(f){try{var h=n[o].getTransferables&&n[o].getTransferables(f);(!h||!Array.isArray(h)||!h.length)&&(h=void 0),s(f,h)}catch(d){console.error(d),s(d)}}}function i(r,s){var a=void 0;self.troikaDefine=function(l){return a=l};var o=URL.createObjectURL(new Blob(["/** "+r.replace(/\*/g,"")+` **/

troikaDefine(
`+s+`
)`],{type:"application/javascript"}));try{importScripts(o)}catch(l){console.error(l)}return URL.revokeObjectURL(o),delete self.troikaDefine,a}self.addEventListener("message",function(r){var s=r.data,a=s.messageId,o=s.action,l=s.data;try{o==="registerModule"&&e(l,function(c){c instanceof Error?postMessage({messageId:a,success:!1,error:c.message}):postMessage({messageId:a,success:!0,result:{isCallable:typeof c=="function"}})}),o==="callModule"&&t(l,function(c,u){c instanceof Error?postMessage({messageId:a,success:!1,error:c.message}):postMessage({messageId:a,success:!0,result:c},u||void 0)})}catch(c){postMessage({messageId:a,success:!1,error:c.stack})}})}function jM(n){var e=function(){for(var t=[],i=arguments.length;i--;)t[i]=arguments[i];return e._getInitResult().then(function(r){if(typeof r=="function")return r.apply(void 0,t);throw new Error("Worker module function was called but `init` did not return a callable function")})};return e._getInitResult=function(){var t=n.dependencies,i=n.init;t=Array.isArray(t)?t.map(function(s){return s&&(s=s.onMainThread||s,s._getInitResult&&(s=s._getInitResult())),s}):[];var r=Promise.all(t).then(function(s){return i.apply(null,s)});return e._getInitResult=function(){return r},r},e}var c0=function(){var n=!1;if(typeof window<"u"&&typeof window.document<"u")try{var e=new Worker(URL.createObjectURL(new Blob([""],{type:"application/javascript"})));e.terminate(),n=!0}catch(t){console.log("Troika createWorkerModule: web workers not allowed; falling back to main thread execution. Cause: ["+t.message+"]")}return c0=function(){return n},n},YM=0,qM=0,Vc=!1,Na=Object.create(null),Oa=Object.create(null),Mh=Object.create(null);function ea(n){if((!n||typeof n.init!="function")&&!Vc)throw new Error("requires `options.init` function");var e=n.dependencies,t=n.init,i=n.getTransferables,r=n.workerId,s=jM(n);r==null&&(r="#default");var a="workerModule"+ ++YM,o=n.name||a,l=null;e=e&&e.map(function(u){return typeof u=="function"&&!u.workerModuleData&&(Vc=!0,u=ea({workerId:r,name:"<"+o+"> function dependency: "+u.name,init:`function(){return (
`+nl(u)+`
)}`}),Vc=!1),u&&u.workerModuleData&&(u=u.workerModuleData),u});function c(){for(var u=[],f=arguments.length;f--;)u[f]=arguments[f];if(!c0())return s.apply(void 0,u);if(!l){l=cp(r,"registerModule",c.workerModuleData);var h=function(){l=null,Oa[r].delete(h)};(Oa[r]||(Oa[r]=new Set)).add(h)}return l.then(function(d){var m=d.isCallable;if(m)return cp(r,"callModule",{id:a,args:u});throw new Error("Worker module function was called but `init` did not return a callable function")})}return c.workerModuleData={isWorkerModule:!0,id:a,name:o,dependencies:e,init:nl(t),getTransferables:i&&nl(i)},c.onMainThread=s,c}function KM(n){Oa[n]&&Oa[n].forEach(function(e){e()}),Na[n]&&(Na[n].terminate(),delete Na[n])}function nl(n){var e=n.toString();return!/^function/.test(e)&&/^\w+\s*\(/.test(e)&&(e="function "+e),e}function ZM(n){var e=Na[n];if(!e){var t=nl(XM);e=Na[n]=new Worker(URL.createObjectURL(new Blob(["/** Worker Module Bootstrap: "+n.replace(/\*/g,"")+` **/

;(`+t+")()"],{type:"application/javascript"}))),e.onmessage=function(i){var r=i.data,s=r.messageId,a=Mh[s];if(!a)throw new Error("WorkerModule response with empty or unknown messageId");delete Mh[s],a(r)}}return e}function cp(n,e,t){return new Promise(function(i,r){var s=++qM;Mh[s]=function(a){a.success?i(a.result):r(new Error("Error in worker "+e+" call: "+a.error))},ZM(n).postMessage({messageId:s,action:e,data:t})})}function u0(){var n=(function(e){function t(j,Z,O,H,B,V,G,z){var W=1-G;z.x=W*W*j+2*W*G*O+G*G*B,z.y=W*W*Z+2*W*G*H+G*G*V}function i(j,Z,O,H,B,V,G,z,W,q){var ce=1-W;q.x=ce*ce*ce*j+3*ce*ce*W*O+3*ce*W*W*B+W*W*W*G,q.y=ce*ce*ce*Z+3*ce*ce*W*H+3*ce*W*W*V+W*W*W*z}function r(j,Z){for(var O=/([MLQCZ])([^MLQCZ]*)/g,H,B,V,G,z;H=O.exec(j);){var W=H[2].replace(/^\s*|\s*$/g,"").split(/[,\s]+/).map(function(q){return parseFloat(q)});switch(H[1]){case"M":G=B=W[0],z=V=W[1];break;case"L":(W[0]!==G||W[1]!==z)&&Z("L",G,z,G=W[0],z=W[1]);break;case"Q":{Z("Q",G,z,G=W[2],z=W[3],W[0],W[1]);break}case"C":{Z("C",G,z,G=W[4],z=W[5],W[0],W[1],W[2],W[3]);break}case"Z":(G!==B||z!==V)&&Z("L",G,z,B,V);break}}}function s(j,Z,O){O===void 0&&(O=16);var H={x:0,y:0};r(j,function(B,V,G,z,W,q,ce,me,Q){switch(B){case"L":Z(V,G,z,W);break;case"Q":{for(var ie=V,be=G,De=1;De<O;De++)t(V,G,q,ce,z,W,De/(O-1),H),Z(ie,be,H.x,H.y),ie=H.x,be=H.y;break}case"C":{for(var ye=V,_e=G,Ne=1;Ne<O;Ne++)i(V,G,q,ce,me,Q,z,W,Ne/(O-1),H),Z(ye,_e,H.x,H.y),ye=H.x,_e=H.y;break}}})}var a="precision highp float;attribute vec2 aUV;varying vec2 vUV;void main(){vUV=aUV;gl_Position=vec4(mix(vec2(-1.0),vec2(1.0),aUV),0.0,1.0);}",o="precision highp float;uniform sampler2D tex;varying vec2 vUV;void main(){gl_FragColor=texture2D(tex,vUV);}",l=new WeakMap,c={premultipliedAlpha:!1,preserveDrawingBuffer:!0,antialias:!1,depth:!1};function u(j,Z){var O=j.getContext?j.getContext("webgl",c):j,H=l.get(O);if(!H){let ce=function(ye){var _e=V[ye];if(!_e&&(_e=V[ye]=O.getExtension(ye),!_e))throw new Error(ye+" not supported");return _e},me=function(ye,_e){var Ne=O.createShader(_e);return O.shaderSource(Ne,ye),O.compileShader(Ne),Ne},Q=function(ye,_e,Ne,ae){if(!G[ye]){var Ee={},k={},de=O.createProgram();O.attachShader(de,me(_e,O.VERTEX_SHADER)),O.attachShader(de,me(Ne,O.FRAGMENT_SHADER)),O.linkProgram(de),G[ye]={program:de,transaction:function(we){O.useProgram(de),we({setUniform:function(Re,D){for(var A=[],X=arguments.length-2;X-- >0;)A[X]=arguments[X+2];var ee=k[D]||(k[D]=O.getUniformLocation(de,D));O["uniform"+Re].apply(O,[ee].concat(A))},setAttribute:function(Re,D,A,X,ee){var he=Ee[Re];he||(he=Ee[Re]={buf:O.createBuffer(),loc:O.getAttribLocation(de,Re),data:null}),O.bindBuffer(O.ARRAY_BUFFER,he.buf),O.vertexAttribPointer(he.loc,D,O.FLOAT,!1,0,0),O.enableVertexAttribArray(he.loc),B?O.vertexAttribDivisor(he.loc,X):ce("ANGLE_instanced_arrays").vertexAttribDivisorANGLE(he.loc,X),ee!==he.data&&(O.bufferData(O.ARRAY_BUFFER,ee,A),he.data=ee)}})}}}G[ye].transaction(ae)},ie=function(ye,_e){W++;try{O.activeTexture(O.TEXTURE0+W);var Ne=z[ye];Ne||(Ne=z[ye]=O.createTexture(),O.bindTexture(O.TEXTURE_2D,Ne),O.texParameteri(O.TEXTURE_2D,O.TEXTURE_MIN_FILTER,O.NEAREST),O.texParameteri(O.TEXTURE_2D,O.TEXTURE_MAG_FILTER,O.NEAREST)),O.bindTexture(O.TEXTURE_2D,Ne),_e(Ne,W)}finally{W--}},be=function(ye,_e,Ne){var ae=O.createFramebuffer();q.push(ae),O.bindFramebuffer(O.FRAMEBUFFER,ae),O.activeTexture(O.TEXTURE0+_e),O.bindTexture(O.TEXTURE_2D,ye),O.framebufferTexture2D(O.FRAMEBUFFER,O.COLOR_ATTACHMENT0,O.TEXTURE_2D,ye,0);try{Ne(ae)}finally{O.deleteFramebuffer(ae),O.bindFramebuffer(O.FRAMEBUFFER,q[--q.length-1]||null)}},De=function(){V={},G={},z={},W=-1,q.length=0};var B=typeof WebGL2RenderingContext<"u"&&O instanceof WebGL2RenderingContext,V={},G={},z={},W=-1,q=[];O.canvas.addEventListener("webglcontextlost",function(ye){De(),ye.preventDefault()},!1),l.set(O,H={gl:O,isWebGL2:B,getExtension:ce,withProgram:Q,withTexture:ie,withTextureFramebuffer:be,handleContextLoss:De})}Z(H)}function f(j,Z,O,H,B,V,G,z){G===void 0&&(G=15),z===void 0&&(z=null),u(j,function(W){var q=W.gl,ce=W.withProgram,me=W.withTexture;me("copy",function(Q,ie){q.texImage2D(q.TEXTURE_2D,0,q.RGBA,B,V,0,q.RGBA,q.UNSIGNED_BYTE,Z),ce("copy",a,o,function(be){var De=be.setUniform,ye=be.setAttribute;ye("aUV",2,q.STATIC_DRAW,0,new Float32Array([0,0,2,0,0,2])),De("1i","image",ie),q.bindFramebuffer(q.FRAMEBUFFER,z||null),q.disable(q.BLEND),q.colorMask(G&8,G&4,G&2,G&1),q.viewport(O,H,B,V),q.scissor(O,H,B,V),q.drawArrays(q.TRIANGLES,0,3)})})})}function h(j,Z,O){var H=j.width,B=j.height;u(j,function(V){var G=V.gl,z=new Uint8Array(H*B*4);G.readPixels(0,0,H,B,G.RGBA,G.UNSIGNED_BYTE,z),j.width=Z,j.height=O,f(G,z,0,0,H,B)})}var d=Object.freeze({__proto__:null,withWebGLContext:u,renderImageData:f,resizeWebGLCanvasWithoutClearing:h});function m(j,Z,O,H,B,V){V===void 0&&(V=1);var G=new Uint8Array(j*Z),z=H[2]-H[0],W=H[3]-H[1],q=[];s(O,function(ye,_e,Ne,ae){q.push({x1:ye,y1:_e,x2:Ne,y2:ae,minX:Math.min(ye,Ne),minY:Math.min(_e,ae),maxX:Math.max(ye,Ne),maxY:Math.max(_e,ae)})}),q.sort(function(ye,_e){return ye.maxX-_e.maxX});for(var ce=0;ce<j;ce++)for(var me=0;me<Z;me++){var Q=be(H[0]+z*(ce+.5)/j,H[1]+W*(me+.5)/Z),ie=Math.pow(1-Math.abs(Q)/B,V)/2;Q<0&&(ie=1-ie),ie=Math.max(0,Math.min(255,Math.round(ie*255))),G[me*j+ce]=ie}return G;function be(ye,_e){for(var Ne=1/0,ae=1/0,Ee=q.length;Ee--;){var k=q[Ee];if(k.maxX+ae<=ye)break;if(ye+ae>k.minX&&_e-ae<k.maxY&&_e+ae>k.minY){var de=_(ye,_e,k.x1,k.y1,k.x2,k.y2);de<Ne&&(Ne=de,ae=Math.sqrt(Ne))}}return De(ye,_e)&&(ae=-ae),ae}function De(ye,_e){for(var Ne=0,ae=q.length;ae--;){var Ee=q[ae];if(Ee.maxX<=ye)break;var k=Ee.y1>_e!=Ee.y2>_e&&ye<(Ee.x2-Ee.x1)*(_e-Ee.y1)/(Ee.y2-Ee.y1)+Ee.x1;k&&(Ne+=Ee.y1<Ee.y2?1:-1)}return Ne!==0}}function g(j,Z,O,H,B,V,G,z,W,q){V===void 0&&(V=1),z===void 0&&(z=0),W===void 0&&(W=0),q===void 0&&(q=0),p(j,Z,O,H,B,V,G,null,z,W,q)}function p(j,Z,O,H,B,V,G,z,W,q,ce){V===void 0&&(V=1),W===void 0&&(W=0),q===void 0&&(q=0),ce===void 0&&(ce=0);for(var me=m(j,Z,O,H,B,V),Q=new Uint8Array(me.length*4),ie=0;ie<me.length;ie++)Q[ie*4+ce]=me[ie];f(G,Q,W,q,j,Z,1<<3-ce,z)}function _(j,Z,O,H,B,V){var G=B-O,z=V-H,W=G*G+z*z,q=W?Math.max(0,Math.min(1,((j-O)*G+(Z-H)*z)/W)):0,ce=j-(O+q*G),me=Z-(H+q*z);return ce*ce+me*me}var v=Object.freeze({__proto__:null,generate:m,generateIntoCanvas:g,generateIntoFramebuffer:p}),b="precision highp float;uniform vec4 uGlyphBounds;attribute vec2 aUV;attribute vec4 aLineSegment;varying vec4 vLineSegment;varying vec2 vGlyphXY;void main(){vLineSegment=aLineSegment;vGlyphXY=mix(uGlyphBounds.xy,uGlyphBounds.zw,aUV);gl_Position=vec4(mix(vec2(-1.0),vec2(1.0),aUV),0.0,1.0);}",S="precision highp float;uniform vec4 uGlyphBounds;uniform float uMaxDistance;uniform float uExponent;varying vec4 vLineSegment;varying vec2 vGlyphXY;float absDistToSegment(vec2 point,vec2 lineA,vec2 lineB){vec2 lineDir=lineB-lineA;float lenSq=dot(lineDir,lineDir);float t=lenSq==0.0 ? 0.0 : clamp(dot(point-lineA,lineDir)/lenSq,0.0,1.0);vec2 linePt=lineA+t*lineDir;return distance(point,linePt);}void main(){vec4 seg=vLineSegment;vec2 p=vGlyphXY;float dist=absDistToSegment(p,seg.xy,seg.zw);float val=pow(1.0-clamp(dist/uMaxDistance,0.0,1.0),uExponent)*0.5;bool crossing=(seg.y>p.y!=seg.w>p.y)&&(p.x<(seg.z-seg.x)*(p.y-seg.y)/(seg.w-seg.y)+seg.x);bool crossingUp=crossing&&vLineSegment.y<vLineSegment.w;gl_FragColor=vec4(crossingUp ? 1.0/255.0 : 0.0,crossing&&!crossingUp ? 1.0/255.0 : 0.0,0.0,val);}",E="precision highp float;uniform sampler2D tex;varying vec2 vUV;void main(){vec4 color=texture2D(tex,vUV);bool inside=color.r!=color.g;float val=inside ? 1.0-color.a : color.a;gl_FragColor=vec4(val);}",M=new Float32Array([0,0,2,0,0,2]),T=null,x=!1,y={},w=new WeakMap;function C(j){if(!x&&!I(j))throw new Error("WebGL generation not supported")}function R(j,Z,O,H,B,V,G){if(V===void 0&&(V=1),G===void 0&&(G=null),!G&&(G=T,!G)){var z=typeof OffscreenCanvas=="function"?new OffscreenCanvas(1,1):typeof document<"u"?document.createElement("canvas"):null;if(!z)throw new Error("OffscreenCanvas or DOM canvas not supported");G=T=z.getContext("webgl",{depth:!1})}C(G);var W=new Uint8Array(j*Z*4);u(G,function(Q){var ie=Q.gl,be=Q.withTexture,De=Q.withTextureFramebuffer;be("readable",function(ye,_e){ie.texImage2D(ie.TEXTURE_2D,0,ie.RGBA,j,Z,0,ie.RGBA,ie.UNSIGNED_BYTE,null),De(ye,_e,function(Ne){U(j,Z,O,H,B,V,ie,Ne,0,0,0),ie.readPixels(0,0,j,Z,ie.RGBA,ie.UNSIGNED_BYTE,W)})})});for(var q=new Uint8Array(j*Z),ce=0,me=0;ce<W.length;ce+=4)q[me++]=W[ce];return q}function L(j,Z,O,H,B,V,G,z,W,q){V===void 0&&(V=1),z===void 0&&(z=0),W===void 0&&(W=0),q===void 0&&(q=0),U(j,Z,O,H,B,V,G,null,z,W,q)}function U(j,Z,O,H,B,V,G,z,W,q,ce){V===void 0&&(V=1),W===void 0&&(W=0),q===void 0&&(q=0),ce===void 0&&(ce=0),C(G);var me=[];s(O,function(Q,ie,be,De){me.push(Q,ie,be,De)}),me=new Float32Array(me),u(G,function(Q){var ie=Q.gl,be=Q.isWebGL2,De=Q.getExtension,ye=Q.withProgram,_e=Q.withTexture,Ne=Q.withTextureFramebuffer,ae=Q.handleContextLoss;if(_e("rawDistances",function(Ee,k){(j!==Ee._lastWidth||Z!==Ee._lastHeight)&&ie.texImage2D(ie.TEXTURE_2D,0,ie.RGBA,Ee._lastWidth=j,Ee._lastHeight=Z,0,ie.RGBA,ie.UNSIGNED_BYTE,null),ye("main",b,S,function(de){var Pe=de.setAttribute,we=de.setUniform,pe=!be&&De("ANGLE_instanced_arrays"),Re=!be&&De("EXT_blend_minmax");Pe("aUV",2,ie.STATIC_DRAW,0,M),Pe("aLineSegment",4,ie.DYNAMIC_DRAW,1,me),we.apply(void 0,["4f","uGlyphBounds"].concat(H)),we("1f","uMaxDistance",B),we("1f","uExponent",V),Ne(Ee,k,function(D){ie.enable(ie.BLEND),ie.colorMask(!0,!0,!0,!0),ie.viewport(0,0,j,Z),ie.scissor(0,0,j,Z),ie.blendFunc(ie.ONE,ie.ONE),ie.blendEquationSeparate(ie.FUNC_ADD,be?ie.MAX:Re.MAX_EXT),ie.clear(ie.COLOR_BUFFER_BIT),be?ie.drawArraysInstanced(ie.TRIANGLES,0,3,me.length/4):pe.drawArraysInstancedANGLE(ie.TRIANGLES,0,3,me.length/4)})}),ye("post",a,E,function(de){de.setAttribute("aUV",2,ie.STATIC_DRAW,0,M),de.setUniform("1i","tex",k),ie.bindFramebuffer(ie.FRAMEBUFFER,z),ie.disable(ie.BLEND),ie.colorMask(ce===0,ce===1,ce===2,ce===3),ie.viewport(W,q,j,Z),ie.scissor(W,q,j,Z),ie.drawArrays(ie.TRIANGLES,0,3)})}),ie.isContextLost())throw ae(),new Error("webgl context lost")})}function I(j){var Z=!j||j===T?y:j.canvas||j,O=w.get(Z);if(O===void 0){x=!0;var H=null;try{var B=[97,106,97,61,99,137,118,80,80,118,137,99,61,97,106,97],V=R(4,4,"M8,8L16,8L24,24L16,24Z",[0,0,32,32],24,1,j);O=V&&B.length===V.length&&V.every(function(G,z){return G===B[z]}),O||(H="bad trial run results",console.info(B,V))}catch(G){O=!1,H=G.message}H&&console.warn("WebGL SDF generation not supported:",H),x=!1,w.set(Z,O)}return O}var F=Object.freeze({__proto__:null,generate:R,generateIntoCanvas:L,generateIntoFramebuffer:U,isSupported:I});function N(j,Z,O,H,B,V){B===void 0&&(B=Math.max(H[2]-H[0],H[3]-H[1])/2),V===void 0&&(V=1);try{return R.apply(F,arguments)}catch(G){return console.info("WebGL SDF generation failed, falling back to JS",G),m.apply(v,arguments)}}function Y(j,Z,O,H,B,V,G,z,W,q){B===void 0&&(B=Math.max(H[2]-H[0],H[3]-H[1])/2),V===void 0&&(V=1),z===void 0&&(z=0),W===void 0&&(W=0),q===void 0&&(q=0);try{return L.apply(F,arguments)}catch(ce){return console.info("WebGL SDF generation failed, falling back to JS",ce),g.apply(v,arguments)}}return e.forEachPathCommand=r,e.generate=N,e.generateIntoCanvas=Y,e.javascript=v,e.pathToLineSegments=s,e.webgl=F,e.webglUtils=d,Object.defineProperty(e,"__esModule",{value:!0}),e})({});return n}function $M(){var n=(function(e){var t={R:"13k,1a,2,3,3,2+1j,ch+16,a+1,5+2,2+n,5,a,4,6+16,4+3,h+1b,4mo,179q,2+9,2+11,2i9+7y,2+68,4,3+4,5+13,4+3,2+4k,3+29,8+cf,1t+7z,w+17,3+3m,1t+3z,16o1+5r,8+30,8+mc,29+1r,29+4v,75+73",EN:"1c+9,3d+1,6,187+9,513,4+5,7+9,sf+j,175h+9,qw+q,161f+1d,4xt+a,25i+9",ES:"17,2,6dp+1,f+1,av,16vr,mx+1,4o,2",ET:"z+2,3h+3,b+1,ym,3e+1,2o,p4+1,8,6u,7c,g6,1wc,1n9+4,30+1b,2n,6d,qhx+1,h0m,a+1,49+2,63+1,4+1,6bb+3,12jj",AN:"16o+5,2j+9,2+1,35,ed,1ff2+9,87+u",CS:"18,2+1,b,2u,12k,55v,l,17v0,2,3,53,2+1,b",B:"a,3,f+2,2v,690",S:"9,2,k",WS:"c,k,4f4,1vk+a,u,1j,335",ON:"x+1,4+4,h+5,r+5,r+3,z,5+3,2+1,2+1,5,2+2,3+4,o,w,ci+1,8+d,3+d,6+8,2+g,39+1,9,6+1,2,33,b8,3+1,3c+1,7+1,5r,b,7h+3,sa+5,2,3i+6,jg+3,ur+9,2v,ij+1,9g+9,7+a,8m,4+1,49+x,14u,2+2,c+2,e+2,e+2,e+1,i+n,e+e,2+p,u+2,e+2,36+1,2+3,2+1,b,2+2,6+5,2,2,2,h+1,5+4,6+3,3+f,16+2,5+3l,3+81,1y+p,2+40,q+a,m+13,2r+ch,2+9e,75+hf,3+v,2+2w,6e+5,f+6,75+2a,1a+p,2+2g,d+5x,r+b,6+3,4+o,g,6+1,6+2,2k+1,4,2j,5h+z,1m+1,1e+f,t+2,1f+e,d+3,4o+3,2s+1,w,535+1r,h3l+1i,93+2,2s,b+1,3l+x,2v,4g+3,21+3,kz+1,g5v+1,5a,j+9,n+v,2,3,2+8,2+1,3+2,2,3,46+1,4+4,h+5,r+5,r+a,3h+2,4+6,b+4,78,1r+24,4+c,4,1hb,ey+6,103+j,16j+c,1ux+7,5+g,fsh,jdq+1t,4,57+2e,p1,1m,1m,1m,1m,4kt+1,7j+17,5+2r,d+e,3+e,2+e,2+10,m+4,w,1n+5,1q,4z+5,4b+rb,9+c,4+c,4+37,d+2g,8+b,l+b,5+1j,9+9,7+13,9+t,3+1,27+3c,2+29,2+3q,d+d,3+4,4+2,6+6,a+o,8+6,a+2,e+6,16+42,2+1i",BN:"0+8,6+d,2s+5,2+p,e,4m9,1kt+2,2b+5,5+5,17q9+v,7k,6p+8,6+1,119d+3,440+7,96s+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+75,6p+2rz,1ben+1,1ekf+1,1ekf+1",NSM:"lc+33,7o+6,7c+18,2,2+1,2+1,2,21+a,1d+k,h,2u+6,3+5,3+1,2+3,10,v+q,2k+a,1n+8,a,p+3,2+8,2+2,2+4,18+2,3c+e,2+v,1k,2,5+7,5,4+6,b+1,u,1n,5+3,9,l+1,r,3+1,1m,5+1,5+1,3+2,4,v+1,4,c+1,1m,5+4,2+1,5,l+1,n+5,2,1n,3,2+3,9,8+1,c+1,v,1q,d,1f,4,1m+2,6+2,2+3,8+1,c+1,u,1n,g+1,l+1,t+1,1m+1,5+3,9,l+1,u,21,8+2,2,2j,3+6,d+7,2r,3+8,c+5,23+1,s,2,2,1k+d,2+4,2+1,6+a,2+z,a,2v+3,2+5,2+1,3+1,q+1,5+2,h+3,e,3+1,7,g,jk+2,qb+2,u+2,u+1,v+1,1t+1,2+6,9,3+a,a,1a+2,3c+1,z,3b+2,5+1,a,7+2,64+1,3,1n,2+6,2,2,3+7,7+9,3,1d+g,1s+3,1d,2+4,2,6,15+8,d+1,x+3,3+1,2+2,1l,2+1,4,2+2,1n+7,3+1,49+2,2+c,2+6,5,7,4+1,5j+1l,2+4,k1+w,2db+2,3y,2p+v,ff+3,30+1,n9x+3,2+9,x+1,29+1,7l,4,5,q+1,6,48+1,r+h,e,13+7,q+a,1b+2,1d,3+3,3+1,14,1w+5,3+1,3+1,d,9,1c,1g,2+2,3+1,6+1,2,17+1,9,6n,3,5,fn5,ki+f,h+f,r2,6b,46+4,1af+2,2+1,6+3,15+2,5,4m+1,fy+3,as+1,4a+a,4x,1j+e,1l+2,1e+3,3+1,1y+2,11+4,2+7,1r,d+1,1h+8,b+3,3,2o+2,3,2+1,7,4h,4+7,m+1,1m+1,4,12+6,4+4,5g+7,3+2,2,o,2d+5,2,5+1,2+1,6n+3,7+1,2+1,s+1,2e+7,3,2+1,2z,2,3+5,2,2u+2,3+3,2+4,78+8,2+1,75+1,2,5,41+3,3+1,5,x+5,3+1,15+5,3+3,9,a+5,3+2,1b+c,2+1,bb+6,2+5,2d+l,3+6,2+1,2+1,3f+5,4,2+1,2+6,2,21+1,4,2,9o+1,f0c+4,1o+6,t5,1s+3,2a,f5l+1,43t+2,i+7,3+6,v+3,45+2,1j0+1i,5+1d,9,f,n+4,2+e,11t+6,2+g,3+6,2+1,2+4,7a+6,c6+3,15t+6,32+6,gzhy+6n",AL:"16w,3,2,e+1b,z+2,2+2s,g+1,8+1,b+m,2+t,s+2i,c+e,4h+f,1d+1e,1bwe+dp,3+3z,x+c,2+1,35+3y,2rm+z,5+7,b+5,dt+l,c+u,17nl+27,1t+27,4x+6n,3+d",LRO:"6ct",RLO:"6cu",LRE:"6cq",RLE:"6cr",PDF:"6cs",LRI:"6ee",RLI:"6ef",FSI:"6eg",PDI:"6eh"},i={},r={};i.L=1,r[1]="L",Object.keys(t).forEach(function(ae,Ee){i[ae]=1<<Ee+1,r[i[ae]]=ae}),Object.freeze(i);var s=i.LRI|i.RLI|i.FSI,a=i.L|i.R|i.AL,o=i.B|i.S|i.WS|i.ON|i.FSI|i.LRI|i.RLI|i.PDI,l=i.BN|i.RLE|i.LRE|i.RLO|i.LRO|i.PDF,c=i.S|i.WS|i.B|s|i.PDI|l,u=null;function f(){if(!u){u=new Map;var ae=0;for(var Ee in t)if(t.hasOwnProperty(Ee))for(var k=t[Ee],de="",Pe=void 0,we=!1,pe=0,Re=0;Re<=k.length+1;Re+=1){var D=k[Re];if(D!==","&&Re!==k.length)D==="+"?(we=!0,pe=ae=pe+parseInt(de,36),de=""):de+=D;else{we?Pe=ae+parseInt(de,36):(pe=ae=pe+parseInt(de,36),Pe=ae),we=!1,de="",pe=Pe;for(var A=ae;A<Pe+1;A+=1)u.set(A,i[Ee])}}}}function h(ae){return f(),u.get(ae.codePointAt(0))||i.L}function d(ae){return r[h(ae)]}var m={pairs:"14>1,1e>2,u>2,2wt>1,1>1,1ge>1,1wp>1,1j>1,f>1,hm>1,1>1,u>1,u6>1,1>1,+5,28>1,w>1,1>1,+3,b8>1,1>1,+3,1>3,-1>-1,3>1,1>1,+2,1s>1,1>1,x>1,th>1,1>1,+2,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,4q>1,1e>2,u>2,2>1,+1",canonical:"6f1>-6dx,6dy>-6dx,6ec>-6ed,6ee>-6ed,6ww>2jj,-2ji>2jj,14r4>-1e7l,1e7m>-1e7l,1e7m>-1e5c,1e5d>-1e5b,1e5c>-14qx,14qy>-14qx,14vn>-1ecg,1ech>-1ecg,1edu>-1ecg,1eci>-1ecg,1eda>-1ecg,1eci>-1ecg,1eci>-168q,168r>-168q,168s>-14ye,14yf>-14ye"};function g(ae,Ee){var k=36,de=0,Pe=new Map,we=Ee&&new Map,pe;return ae.split(",").forEach(function Re(D){if(D.indexOf("+")!==-1)for(var A=+D;A--;)Re(pe);else{pe=D;var X=D.split(">"),ee=X[0],he=X[1];ee=String.fromCodePoint(de+=parseInt(ee,k)),he=String.fromCodePoint(de+=parseInt(he,k)),Pe.set(ee,he),Ee&&we.set(he,ee)}}),{map:Pe,reverseMap:we}}var p,_,v;function b(){if(!p){var ae=g(m.pairs,!0),Ee=ae.map,k=ae.reverseMap;p=Ee,_=k,v=g(m.canonical,!1).map}}function S(ae){return b(),p.get(ae)||null}function E(ae){return b(),_.get(ae)||null}function M(ae){return b(),v.get(ae)||null}var T=i.L,x=i.R,y=i.EN,w=i.ES,C=i.ET,R=i.AN,L=i.CS,U=i.B,I=i.S,F=i.ON,N=i.BN,Y=i.NSM,j=i.AL,Z=i.LRO,O=i.RLO,H=i.LRE,B=i.RLE,V=i.PDF,G=i.LRI,z=i.RLI,W=i.FSI,q=i.PDI;function ce(ae,Ee){for(var k=125,de=new Uint32Array(ae.length),Pe=0;Pe<ae.length;Pe++)de[Pe]=h(ae[Pe]);var we=new Map;function pe(Tn,li){var En=de[Tn];de[Tn]=li,we.set(En,we.get(En)-1),En&o&&we.set(o,we.get(o)-1),we.set(li,(we.get(li)||0)+1),li&o&&we.set(o,(we.get(o)||0)+1)}for(var Re=new Uint8Array(ae.length),D=new Map,A=[],X=null,ee=0;ee<ae.length;ee++)X||A.push(X={start:ee,end:ae.length-1,level:Ee==="rtl"?1:Ee==="ltr"?0:Jf(ee,!1)}),de[ee]&U&&(X.end=ee,X=null);for(var he=B|H|O|Z|s|q|V|U,xe=function(Tn){return Tn+(Tn&1?1:2)},Te=function(Tn){return Tn+(Tn&1?2:1)},te=0;te<A.length;te++){X=A[te];var le=[{_level:X.level,_override:0,_isolate:0}],ge=void 0,Ie=0,Me=0,Ae=0;we.clear();for(var He=X.start;He<=X.end;He++){var Fe=de[He];if(ge=le[le.length-1],we.set(Fe,(we.get(Fe)||0)+1),Fe&o&&we.set(o,(we.get(o)||0)+1),Fe&he)if(Fe&(B|H)){Re[He]=ge._level;var Ye=(Fe===B?Te:xe)(ge._level);Ye<=k&&!Ie&&!Me?le.push({_level:Ye,_override:0,_isolate:0}):Ie||Me++}else if(Fe&(O|Z)){Re[He]=ge._level;var K=(Fe===O?Te:xe)(ge._level);K<=k&&!Ie&&!Me?le.push({_level:K,_override:Fe&O?x:T,_isolate:0}):Ie||Me++}else if(Fe&s){Fe&W&&(Fe=Jf(He+1,!0)===1?z:G),Re[He]=ge._level,ge._override&&pe(He,ge._override);var ve=(Fe===z?Te:xe)(ge._level);ve<=k&&Ie===0&&Me===0?(Ae++,le.push({_level:ve,_override:0,_isolate:1,_isolInitIndex:He})):Ie++}else if(Fe&q){if(Ie>0)Ie--;else if(Ae>0){for(Me=0;!le[le.length-1]._isolate;)le.pop();var oe=le[le.length-1]._isolInitIndex;oe!=null&&(D.set(oe,He),D.set(He,oe)),le.pop(),Ae--}ge=le[le.length-1],Re[He]=ge._level,ge._override&&pe(He,ge._override)}else Fe&V?(Ie===0&&(Me>0?Me--:!ge._isolate&&le.length>1&&(le.pop(),ge=le[le.length-1])),Re[He]=ge._level):Fe&U&&(Re[He]=X.level);else Re[He]=ge._level,ge._override&&Fe!==N&&pe(He,ge._override)}for(var Le=[],Se=null,fe=X.start;fe<=X.end;fe++){var Oe=de[fe];if(!(Oe&l)){var $e=Re[fe],ot=Oe&s,tt=Oe===q;Se&&$e===Se._level?(Se._end=fe,Se._endsWithIsolInit=ot):Le.push(Se={_start:fe,_end:fe,_level:$e,_startsWithPDI:tt,_endsWithIsolInit:ot})}}for(var Vt=[],Kt=0;Kt<Le.length;Kt++){var In=Le[Kt];if(!In._startsWithPDI||In._startsWithPDI&&!D.has(In._start)){for(var _i=[Se=In],vi=void 0;Se&&Se._endsWithIsolInit&&(vi=D.get(Se._end))!=null;)for(var Zn=Kt+1;Zn<Le.length;Zn++)if(Le[Zn]._start===vi){_i.push(Se=Le[Zn]);break}for(var Ft=[],ri=0;ri<_i.length;ri++)for(var ra=_i[ri],rs=ra._start;rs<=ra._end;rs++)Ft.push(rs);for(var ss=Re[Ft[0]],sa=X.level,Ii=Ft[0]-1;Ii>=0;Ii--)if(!(de[Ii]&l)){sa=Re[Ii];break}var as=Ft[Ft.length-1],so=Re[as],ao=X.level;if(!(de[as]&s)){for(var os=as+1;os<=X.end;os++)if(!(de[os]&l)){ao=Re[os];break}}Vt.push({_seqIndices:Ft,_sosType:Math.max(sa,ss)%2?x:T,_eosType:Math.max(ao,so)%2?x:T})}}for(var aa=0;aa<Vt.length;aa++){var oa=Vt[aa],Je=oa._seqIndices,Cr=oa._sosType,Ql=oa._eosType,P=Re[Je[0]]&1?x:T;if(we.get(Y))for(var J=0;J<Je.length;J++){var ue=Je[J];if(de[ue]&Y){for(var re=Cr,se=J-1;se>=0;se--)if(!(de[Je[se]]&l)){re=de[Je[se]];break}pe(ue,re&(s|q)?F:re)}}if(we.get(y))for(var ke=0;ke<Je.length;ke++){var Ve=Je[ke];if(de[Ve]&y)for(var Be=ke-1;Be>=-1;Be--){var je=Be===-1?Cr:de[Je[Be]];if(je&a){je===j&&pe(Ve,R);break}}}if(we.get(j))for(var qe=0;qe<Je.length;qe++){var nt=Je[qe];de[nt]&j&&pe(nt,x)}if(we.get(w)||we.get(L))for(var it=1;it<Je.length-1;it++){var Ke=Je[it];if(de[Ke]&(w|L)){for(var ht=0,Dt=0,Pt=it-1;Pt>=0&&(ht=de[Je[Pt]],!!(ht&l));Pt--);for(var _t=it+1;_t<Je.length&&(Dt=de[Je[_t]],!!(Dt&l));_t++);ht===Dt&&(de[Ke]===w?ht===y:ht&(y|R))&&pe(Ke,ht)}}if(we.get(y))for(var Et=0;Et<Je.length;Et++){var We=Je[Et];if(de[We]&y){for(var rn=Et-1;rn>=0&&de[Je[rn]]&(C|l);rn--)pe(Je[rn],y);for(Et++;Et<Je.length&&de[Je[Et]]&(C|l|y);Et++)de[Je[Et]]!==y&&pe(Je[Et],y)}}if(we.get(C)||we.get(w)||we.get(L))for(var at=0;at<Je.length;at++){var xn=Je[at];if(de[xn]&(C|w|L)){pe(xn,F);for(var yn=at-1;yn>=0&&de[Je[yn]]&l;yn--)pe(Je[yn],F);for(var Fn=at+1;Fn<Je.length&&de[Je[Fn]]&l;Fn++)pe(Je[Fn],F)}}if(we.get(y))for(var xi=0,xt=Cr;xi<Je.length;xi++){var Lt=Je[xi],$n=de[Lt];$n&y?xt===T&&pe(Lt,T):$n&a&&(xt=$n)}if(we.get(o)){var mt=x|y|R,si=mt|T,ai=[];{for(var Fi=[],ls=0;ls<Je.length;ls++)if(de[Je[ls]]&o){var la=ae[Je[ls]],Vf=void 0;if(S(la)!==null)if(Fi.length<63)Fi.push({char:la,seqIndex:ls});else break;else if((Vf=E(la))!==null)for(var ca=Fi.length-1;ca>=0;ca--){var ec=Fi[ca].char;if(ec===Vf||ec===E(M(la))||S(M(ec))===la){ai.push([Fi[ca].seqIndex,ls]),Fi.length=ca;break}}}ai.sort(function(Tn,li){return Tn[0]-li[0]})}for(var tc=0;tc<ai.length;tc++){for(var Wf=ai[tc],oo=Wf[0],nc=Wf[1],Xf=!1,oi=0,ic=oo+1;ic<nc;ic++){var jf=Je[ic];if(de[jf]&si){Xf=!0;var Yf=de[jf]&mt?x:T;if(Yf===P){oi=Yf;break}}}if(Xf&&!oi){oi=Cr;for(var rc=oo-1;rc>=0;rc--){var qf=Je[rc];if(de[qf]&si){var Kf=de[qf]&mt?x:T;Kf!==P?oi=Kf:oi=P;break}}}if(oi){if(de[Je[oo]]=de[Je[nc]]=oi,oi!==P){for(var ua=oo+1;ua<Je.length;ua++)if(!(de[Je[ua]]&l)){h(ae[Je[ua]])&Y&&(de[Je[ua]]=oi);break}}if(oi!==P){for(var ha=nc+1;ha<Je.length;ha++)if(!(de[Je[ha]]&l)){h(ae[Je[ha]])&Y&&(de[Je[ha]]=oi);break}}}}for(var er=0;er<Je.length;er++)if(de[Je[er]]&o){for(var Zf=er,sc=er,ac=Cr,fa=er-1;fa>=0;fa--)if(de[Je[fa]]&l)Zf=fa;else{ac=de[Je[fa]]&mt?x:T;break}for(var $f=Ql,da=er+1;da<Je.length;da++)if(de[Je[da]]&(o|l))sc=da;else{$f=de[Je[da]]&mt?x:T;break}for(var oc=Zf;oc<=sc;oc++)de[Je[oc]]=ac===$f?ac:P;er=sc}}}for(var Nn=X.start;Nn<=X.end;Nn++){var Zg=Re[Nn],lo=de[Nn];if(Zg&1?lo&(T|y|R)&&Re[Nn]++:lo&x?Re[Nn]++:lo&(R|y)&&(Re[Nn]+=2),lo&l&&(Re[Nn]=Nn===0?X.level:Re[Nn-1]),Nn===X.end||h(ae[Nn])&(I|U))for(var co=Nn;co>=0&&h(ae[co])&c;co--)Re[co]=X.level}}return{levels:Re,paragraphs:A};function Jf(Tn,li){for(var En=Tn;En<ae.length;En++){var tr=de[En];if(tr&(x|j))return 1;if(tr&(U|T)||li&&tr===q)return 0;if(tr&s){var Qf=$g(En);En=Qf===-1?ae.length:Qf}}return 0}function $g(Tn){for(var li=1,En=Tn+1;En<ae.length;En++){var tr=de[En];if(tr&U)break;if(tr&q){if(--li===0)return En}else tr&s&&li++}return-1}}var me="14>1,j>2,t>2,u>2,1a>g,2v3>1,1>1,1ge>1,1wd>1,b>1,1j>1,f>1,ai>3,-2>3,+1,8>1k0,-1jq>1y7,-1y6>1hf,-1he>1h6,-1h5>1ha,-1h8>1qi,-1pu>1,6>3u,-3s>7,6>1,1>1,f>1,1>1,+2,3>1,1>1,+13,4>1,1>1,6>1eo,-1ee>1,3>1mg,-1me>1mk,-1mj>1mi,-1mg>1mi,-1md>1,1>1,+2,1>10k,-103>1,1>1,4>1,5>1,1>1,+10,3>1,1>8,-7>8,+1,-6>7,+1,a>1,1>1,u>1,u6>1,1>1,+5,26>1,1>1,2>1,2>2,8>1,7>1,4>1,1>1,+5,b8>1,1>1,+3,1>3,-2>1,2>1,1>1,+2,c>1,3>1,1>1,+2,h>1,3>1,a>1,1>1,2>1,3>1,1>1,d>1,f>1,3>1,1a>1,1>1,6>1,7>1,13>1,k>1,1>1,+19,4>1,1>1,+2,2>1,1>1,+18,m>1,a>1,1>1,lk>1,1>1,4>1,2>1,f>1,3>1,1>1,+3,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,6>1,4j>1,j>2,t>2,u>2,2>1,+1",Q;function ie(){if(!Q){var ae=g(me,!0),Ee=ae.map,k=ae.reverseMap;k.forEach(function(de,Pe){Ee.set(Pe,de)}),Q=Ee}}function be(ae){return ie(),Q.get(ae)||null}function De(ae,Ee,k,de){var Pe=ae.length;k=Math.max(0,k==null?0:+k),de=Math.min(Pe-1,de==null?Pe-1:+de);for(var we=new Map,pe=k;pe<=de;pe++)if(Ee[pe]&1){var Re=be(ae[pe]);Re!==null&&we.set(pe,Re)}return we}function ye(ae,Ee,k,de){var Pe=ae.length;k=Math.max(0,k==null?0:+k),de=Math.min(Pe-1,de==null?Pe-1:+de);var we=[];return Ee.paragraphs.forEach(function(pe){var Re=Math.max(k,pe.start),D=Math.min(de,pe.end);if(Re<D){for(var A=Ee.levels.slice(Re,D+1),X=D;X>=Re&&h(ae[X])&c;X--)A[X]=pe.level;for(var ee=pe.level,he=1/0,xe=0;xe<A.length;xe++){var Te=A[xe];Te>ee&&(ee=Te),Te<he&&(he=Te|1)}for(var te=ee;te>=he;te--)for(var le=0;le<A.length;le++)if(A[le]>=te){for(var ge=le;le+1<A.length&&A[le+1]>=te;)le++;le>ge&&we.push([ge+Re,le+Re])}}}),we}function _e(ae,Ee,k,de){var Pe=Ne(ae,Ee,k,de),we=[].concat(ae);return Pe.forEach(function(pe,Re){we[Re]=(Ee.levels[pe]&1?be(ae[pe]):null)||ae[pe]}),we.join("")}function Ne(ae,Ee,k,de){for(var Pe=ye(ae,Ee,k,de),we=[],pe=0;pe<ae.length;pe++)we[pe]=pe;return Pe.forEach(function(Re){for(var D=Re[0],A=Re[1],X=we.slice(D,A+1),ee=X.length;ee--;)we[A-ee]=X[ee]}),we}return e.closingToOpeningBracket=E,e.getBidiCharType=h,e.getBidiCharTypeName=d,e.getCanonicalBracket=M,e.getEmbeddingLevels=ce,e.getMirroredCharacter=be,e.getMirroredCharactersMap=De,e.getReorderSegments=ye,e.getReorderedIndices=Ne,e.getReorderedString=_e,e.openingToClosingBracket=S,Object.defineProperty(e,"__esModule",{value:!0}),e})({});return n}const h0=/\bvoid\s+main\s*\(\s*\)\s*{/g;function Sh(n){const e=/^[ \t]*#include +<([\w\d./]+)>/gm;function t(i,r){let s=st[r];return s?Sh(s):i}return n.replace(e,t)}const un=[];for(let n=0;n<256;n++)un[n]=(n<16?"0":"")+n.toString(16);function JM(){const n=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,i=Math.random()*4294967295|0;return(un[n&255]+un[n>>8&255]+un[n>>16&255]+un[n>>24&255]+"-"+un[e&255]+un[e>>8&255]+"-"+un[e>>16&15|64]+un[e>>24&255]+"-"+un[t&63|128]+un[t>>8&255]+"-"+un[t>>16&255]+un[t>>24&255]+un[i&255]+un[i>>8&255]+un[i>>16&255]+un[i>>24&255]).toUpperCase()}const Ir=Object.assign||function(){let n=arguments[0];for(let e=1,t=arguments.length;e<t;e++){let i=arguments[e];if(i)for(let r in i)Object.prototype.hasOwnProperty.call(i,r)&&(n[r]=i[r])}return n},QM=Date.now(),up=new WeakMap,hp=new Map;let eS=1e10;function Th(n,e){const t=rS(e);let i=up.get(n);if(i||up.set(n,i=Object.create(null)),i[t])return new i[t];const r=`_onBeforeCompile${t}`,s=function(c,u){n.onBeforeCompile.call(this,c,u);const f=this.customProgramCacheKey()+"|"+c.vertexShader+"|"+c.fragmentShader;let h=hp[f];if(!h){const d=tS(this,c,e,t);h=hp[f]=d}c.vertexShader=h.vertexShader,c.fragmentShader=h.fragmentShader,Ir(c.uniforms,this.uniforms),e.timeUniform&&(c.uniforms[e.timeUniform]={get value(){return Date.now()-QM}}),this[r]&&this[r](c)},a=function(){return o(e.chained?n:n.clone())},o=function(c){const u=Object.create(c,l);return Object.defineProperty(u,"baseMaterial",{value:n}),Object.defineProperty(u,"id",{value:eS++}),u.uuid=JM(),u.uniforms=Ir({},c.uniforms,e.uniforms),u.defines=Ir({},c.defines,e.defines),u.defines[`TROIKA_DERIVED_MATERIAL_${t}`]="",u.extensions=Ir({},c.extensions,e.extensions),u._listeners=void 0,u},l={constructor:{value:a},isDerivedMaterial:{value:!0},type:{get:()=>n.type,set:c=>{n.type=c}},isDerivedFrom:{writable:!0,configurable:!0,value:function(c){const u=this.baseMaterial;return c===u||u.isDerivedMaterial&&u.isDerivedFrom(c)||!1}},customProgramCacheKey:{writable:!0,configurable:!0,value:function(){return n.customProgramCacheKey()+"|"+t}},onBeforeCompile:{get(){return s},set(c){this[r]=c}},copy:{writable:!0,configurable:!0,value:function(c){return n.copy.call(this,c),!n.isShaderMaterial&&!n.isDerivedMaterial&&(Ir(this.extensions,c.extensions),Ir(this.defines,c.defines),Ir(this.uniforms,$m.clone(c.uniforms))),this}},clone:{writable:!0,configurable:!0,value:function(){const c=new n.constructor;return o(c).copy(this)}},getDepthMaterial:{writable:!0,configurable:!0,value:function(){let c=this._depthMaterial;return c||(c=this._depthMaterial=Th(n.isDerivedMaterial?n.getDepthMaterial():new Jm({depthPacking:J_}),e),c.defines.IS_DEPTH_MATERIAL="",c.uniforms=this.uniforms),c}},getDistanceMaterial:{writable:!0,configurable:!0,value:function(){let c=this._distanceMaterial;return c||(c=this._distanceMaterial=Th(n.isDerivedMaterial?n.getDistanceMaterial():new Qm,e),c.defines.IS_DISTANCE_MATERIAL="",c.uniforms=this.uniforms),c}},dispose:{writable:!0,configurable:!0,value(){const{_depthMaterial:c,_distanceMaterial:u}=this;c&&c.dispose(),u&&u.dispose(),n.dispose.call(this)}}};return i[t]=a,new a}function tS(n,{vertexShader:e,fragmentShader:t},i,r){let{vertexDefs:s,vertexMainIntro:a,vertexMainOutro:o,vertexTransform:l,fragmentDefs:c,fragmentMainIntro:u,fragmentMainOutro:f,fragmentColorTransform:h,customRewriter:d,timeUniform:m}=i;if(s=s||"",a=a||"",o=o||"",c=c||"",u=u||"",f=f||"",(l||d)&&(e=Sh(e)),(h||d)&&(t=t.replace(/^[ \t]*#include <((?:tonemapping|encodings|colorspace|fog|premultiplied_alpha|dithering)_fragment)>/gm,`
//!BEGIN_POST_CHUNK $1
$&
//!END_POST_CHUNK
`),t=Sh(t)),d){let g=d({vertexShader:e,fragmentShader:t});e=g.vertexShader,t=g.fragmentShader}if(h){let g=[];t=t.replace(/^\/\/!BEGIN_POST_CHUNK[^]+?^\/\/!END_POST_CHUNK/gm,p=>(g.push(p),"")),f=`${h}
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
`,e=e.replace(/\b(position|normal|uv)\b/g,(g,p,_,v)=>/\battribute\s+vec[23]\s+$/.test(v.substr(0,_))?p:`troika_${p}_${r}`),n.map&&n.map.channel>0||(e=e.replace(/\bMAP_UV\b/g,`troika_uv_${r}`))),e=fp(e,r,s,a,o),t=fp(t,r,c,u,f),{vertexShader:e,fragmentShader:t}}function fp(n,e,t,i,r){return(i||r||t)&&(n=n.replace(h0,`
${t}
void troikaOrigMain${e}() {`),n+=`
void main() {
  ${i}
  troikaOrigMain${e}();
  ${r}
}`),n}function nS(n,e){return n==="uniforms"?void 0:typeof e=="function"?e.toString():e}let iS=0;const dp=new Map;function rS(n){const e=JSON.stringify(n,nS);let t=dp.get(e);return t==null&&dp.set(e,t=++iS),t}/*!
Custom build of Typr.ts (https://github.com/fredli74/Typr.ts) for use in Troika text rendering.
Original MIT license applies: https://github.com/fredli74/Typr.ts/blob/master/LICENSE
*/function sS(){return typeof window>"u"&&(self.window=self),(function(n){var e={parse:function(r){var s=e._bin,a=new Uint8Array(r);if(s.readASCII(a,0,4)=="ttcf"){var o=4;s.readUshort(a,o),o+=2,s.readUshort(a,o),o+=2;var l=s.readUint(a,o);o+=4;for(var c=[],u=0;u<l;u++){var f=s.readUint(a,o);o+=4,c.push(e._readFont(a,f))}return c}return[e._readFont(a,0)]},_readFont:function(r,s){var a=e._bin,o=s;a.readFixed(r,s),s+=4;var l=a.readUshort(r,s);s+=2,a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2;for(var c=["cmap","head","hhea","maxp","hmtx","name","OS/2","post","loca","glyf","kern","CFF ","GDEF","GPOS","GSUB","SVG "],u={_data:r,_offset:o},f={},h=0;h<l;h++){var d=a.readASCII(r,s,4);s+=4,a.readUint(r,s),s+=4;var m=a.readUint(r,s);s+=4;var g=a.readUint(r,s);s+=4,f[d]={offset:m,length:g}}for(h=0;h<c.length;h++){var p=c[h];f[p]&&(u[p.trim()]=e[p.trim()].parse(r,f[p].offset,f[p].length,u))}return u},_tabOffset:function(r,s,a){for(var o=e._bin,l=o.readUshort(r,a+4),c=a+12,u=0;u<l;u++){var f=o.readASCII(r,c,4);c+=4,o.readUint(r,c),c+=4;var h=o.readUint(r,c);if(c+=4,o.readUint(r,c),c+=4,f==s)return h}return 0}};e._bin={readFixed:function(r,s){return(r[s]<<8|r[s+1])+(r[s+2]<<8|r[s+3])/65540},readF2dot14:function(r,s){return e._bin.readShort(r,s)/16384},readInt:function(r,s){return e._bin._view(r).getInt32(s)},readInt8:function(r,s){return e._bin._view(r).getInt8(s)},readShort:function(r,s){return e._bin._view(r).getInt16(s)},readUshort:function(r,s){return e._bin._view(r).getUint16(s)},readUshorts:function(r,s,a){for(var o=[],l=0;l<a;l++)o.push(e._bin.readUshort(r,s+2*l));return o},readUint:function(r,s){return e._bin._view(r).getUint32(s)},readUint64:function(r,s){return 4294967296*e._bin.readUint(r,s)+e._bin.readUint(r,s+4)},readASCII:function(r,s,a){for(var o="",l=0;l<a;l++)o+=String.fromCharCode(r[s+l]);return o},readUnicode:function(r,s,a){for(var o="",l=0;l<a;l++){var c=r[s++]<<8|r[s++];o+=String.fromCharCode(c)}return o},_tdec:typeof window<"u"&&window.TextDecoder?new window.TextDecoder:null,readUTF8:function(r,s,a){var o=e._bin._tdec;return o&&s==0&&a==r.length?o.decode(r):e._bin.readASCII(r,s,a)},readBytes:function(r,s,a){for(var o=[],l=0;l<a;l++)o.push(r[s+l]);return o},readASCIIArray:function(r,s,a){for(var o=[],l=0;l<a;l++)o.push(String.fromCharCode(r[s+l]));return o},_view:function(r){return r._dataView||(r._dataView=r.buffer?new DataView(r.buffer,r.byteOffset,r.byteLength):new DataView(new Uint8Array(r).buffer))}},e._lctf={},e._lctf.parse=function(r,s,a,o,l){var c=e._bin,u={},f=s;c.readFixed(r,s),s+=4;var h=c.readUshort(r,s);s+=2;var d=c.readUshort(r,s);s+=2;var m=c.readUshort(r,s);return s+=2,u.scriptList=e._lctf.readScriptList(r,f+h),u.featureList=e._lctf.readFeatureList(r,f+d),u.lookupList=e._lctf.readLookupList(r,f+m,l),u},e._lctf.readLookupList=function(r,s,a){var o=e._bin,l=s,c=[],u=o.readUshort(r,s);s+=2;for(var f=0;f<u;f++){var h=o.readUshort(r,s);s+=2;var d=e._lctf.readLookupTable(r,l+h,a);c.push(d)}return c},e._lctf.readLookupTable=function(r,s,a){var o=e._bin,l=s,c={tabs:[]};c.ltype=o.readUshort(r,s),s+=2,c.flag=o.readUshort(r,s),s+=2;var u=o.readUshort(r,s);s+=2;for(var f=c.ltype,h=0;h<u;h++){var d=o.readUshort(r,s);s+=2;var m=a(r,f,l+d,c);c.tabs.push(m)}return c},e._lctf.numOfOnes=function(r){for(var s=0,a=0;a<32;a++)(r>>>a&1)!=0&&s++;return s},e._lctf.readClassDef=function(r,s){var a=e._bin,o=[],l=a.readUshort(r,s);if(s+=2,l==1){var c=a.readUshort(r,s);s+=2;var u=a.readUshort(r,s);s+=2;for(var f=0;f<u;f++)o.push(c+f),o.push(c+f),o.push(a.readUshort(r,s)),s+=2}if(l==2){var h=a.readUshort(r,s);for(s+=2,f=0;f<h;f++)o.push(a.readUshort(r,s)),s+=2,o.push(a.readUshort(r,s)),s+=2,o.push(a.readUshort(r,s)),s+=2}return o},e._lctf.getInterval=function(r,s){for(var a=0;a<r.length;a+=3){var o=r[a],l=r[a+1];if(r[a+2],o<=s&&s<=l)return a}return-1},e._lctf.readCoverage=function(r,s){var a=e._bin,o={};o.fmt=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);return s+=2,o.fmt==1&&(o.tab=a.readUshorts(r,s,l)),o.fmt==2&&(o.tab=a.readUshorts(r,s,3*l)),o},e._lctf.coverageIndex=function(r,s){var a=r.tab;if(r.fmt==1)return a.indexOf(s);if(r.fmt==2){var o=e._lctf.getInterval(a,s);if(o!=-1)return a[o+2]+(s-a[o])}return-1},e._lctf.readFeatureList=function(r,s){var a=e._bin,o=s,l=[],c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readASCII(r,s,4);s+=4;var h=a.readUshort(r,s);s+=2;var d=e._lctf.readFeatureTable(r,o+h);d.tag=f.trim(),l.push(d)}return l},e._lctf.readFeatureTable=function(r,s){var a=e._bin,o=s,l={},c=a.readUshort(r,s);s+=2,c>0&&(l.featureParams=o+c);var u=a.readUshort(r,s);s+=2,l.tab=[];for(var f=0;f<u;f++)l.tab.push(a.readUshort(r,s+2*f));return l},e._lctf.readScriptList=function(r,s){var a=e._bin,o=s,l={},c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readASCII(r,s,4);s+=4;var h=a.readUshort(r,s);s+=2,l[f.trim()]=e._lctf.readScriptTable(r,o+h)}return l},e._lctf.readScriptTable=function(r,s){var a=e._bin,o=s,l={},c=a.readUshort(r,s);s+=2,c>0&&(l.default=e._lctf.readLangSysTable(r,o+c));var u=a.readUshort(r,s);s+=2;for(var f=0;f<u;f++){var h=a.readASCII(r,s,4);s+=4;var d=a.readUshort(r,s);s+=2,l[h.trim()]=e._lctf.readLangSysTable(r,o+d)}return l},e._lctf.readLangSysTable=function(r,s){var a=e._bin,o={};a.readUshort(r,s),s+=2,o.reqFeature=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);return s+=2,o.features=a.readUshorts(r,s,l),o},e.CFF={},e.CFF.parse=function(r,s,a){var o=e._bin;(r=new Uint8Array(r.buffer,s,a))[s=0],r[++s],r[++s],r[++s],s++;var l=[];s=e.CFF.readIndex(r,s,l);for(var c=[],u=0;u<l.length-1;u++)c.push(o.readASCII(r,s+l[u],l[u+1]-l[u]));s+=l[l.length-1];var f=[];s=e.CFF.readIndex(r,s,f);var h=[];for(u=0;u<f.length-1;u++)h.push(e.CFF.readDict(r,s+f[u],s+f[u+1]));s+=f[f.length-1];var d=h[0],m=[];s=e.CFF.readIndex(r,s,m);var g=[];for(u=0;u<m.length-1;u++)g.push(o.readASCII(r,s+m[u],m[u+1]-m[u]));if(s+=m[m.length-1],e.CFF.readSubrs(r,s,d),d.CharStrings){s=d.CharStrings,m=[],s=e.CFF.readIndex(r,s,m);var p=[];for(u=0;u<m.length-1;u++)p.push(o.readBytes(r,s+m[u],m[u+1]-m[u]));d.CharStrings=p}if(d.ROS){s=d.FDArray;var _=[];for(s=e.CFF.readIndex(r,s,_),d.FDArray=[],u=0;u<_.length-1;u++){var v=e.CFF.readDict(r,s+_[u],s+_[u+1]);e.CFF._readFDict(r,v,g),d.FDArray.push(v)}s+=_[_.length-1],s=d.FDSelect,d.FDSelect=[];var b=r[s];if(s++,b!=3)throw b;var S=o.readUshort(r,s);for(s+=2,u=0;u<S+1;u++)d.FDSelect.push(o.readUshort(r,s),r[s+2]),s+=3}return d.Encoding&&(d.Encoding=e.CFF.readEncoding(r,d.Encoding,d.CharStrings.length)),d.charset&&(d.charset=e.CFF.readCharset(r,d.charset,d.CharStrings.length)),e.CFF._readFDict(r,d,g),d},e.CFF._readFDict=function(r,s,a){var o;for(var l in s.Private&&(o=s.Private[1],s.Private=e.CFF.readDict(r,o,o+s.Private[0]),s.Private.Subrs&&e.CFF.readSubrs(r,o+s.Private.Subrs,s.Private)),s)["FamilyName","FontName","FullName","Notice","version","Copyright"].indexOf(l)!=-1&&(s[l]=a[s[l]-426+35])},e.CFF.readSubrs=function(r,s,a){var o=e._bin,l=[];s=e.CFF.readIndex(r,s,l);var c,u=l.length;c=u<1240?107:u<33900?1131:32768,a.Bias=c,a.Subrs=[];for(var f=0;f<l.length-1;f++)a.Subrs.push(o.readBytes(r,s+l[f],l[f+1]-l[f]))},e.CFF.tableSE=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,0,111,112,113,114,0,115,116,117,118,119,120,121,122,0,123,0,124,125,126,127,128,129,130,131,0,132,133,0,134,135,136,137,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,138,0,139,0,0,0,0,140,141,142,143,0,0,0,0,0,144,0,0,0,145,0,0,146,147,148,149,0,0,0,0],e.CFF.glyphByUnicode=function(r,s){for(var a=0;a<r.charset.length;a++)if(r.charset[a]==s)return a;return-1},e.CFF.glyphBySE=function(r,s){return s<0||s>255?-1:e.CFF.glyphByUnicode(r,e.CFF.tableSE[s])},e.CFF.readEncoding=function(r,s,a){e._bin;var o=[".notdef"],l=r[s];if(s++,l!=0)throw"error: unknown encoding format: "+l;var c=r[s];s++;for(var u=0;u<c;u++)o.push(r[s+u]);return o},e.CFF.readCharset=function(r,s,a){var o=e._bin,l=[".notdef"],c=r[s];if(s++,c==0)for(var u=0;u<a;u++){var f=o.readUshort(r,s);s+=2,l.push(f)}else{if(c!=1&&c!=2)throw"error: format: "+c;for(;l.length<a;){f=o.readUshort(r,s),s+=2;var h=0;for(c==1?(h=r[s],s++):(h=o.readUshort(r,s),s+=2),u=0;u<=h;u++)l.push(f),f++}}return l},e.CFF.readIndex=function(r,s,a){var o=e._bin,l=o.readUshort(r,s)+1,c=r[s+=2];if(s++,c==1)for(var u=0;u<l;u++)a.push(r[s+u]);else if(c==2)for(u=0;u<l;u++)a.push(o.readUshort(r,s+2*u));else if(c==3)for(u=0;u<l;u++)a.push(16777215&o.readUint(r,s+3*u-1));else if(l!=1)throw"unsupported offset size: "+c+", count: "+l;return(s+=l*c)-1},e.CFF.getCharString=function(r,s,a){var o=e._bin,l=r[s],c=r[s+1];r[s+2],r[s+3],r[s+4];var u=1,f=null,h=null;l<=20&&(f=l,u=1),l==12&&(f=100*l+c,u=2),21<=l&&l<=27&&(f=l,u=1),l==28&&(h=o.readShort(r,s+1),u=3),29<=l&&l<=31&&(f=l,u=1),32<=l&&l<=246&&(h=l-139,u=1),247<=l&&l<=250&&(h=256*(l-247)+c+108,u=2),251<=l&&l<=254&&(h=256*-(l-251)-c-108,u=2),l==255&&(h=o.readInt(r,s+1)/65535,u=5),a.val=h??"o"+f,a.size=u},e.CFF.readCharString=function(r,s,a){for(var o=s+a,l=e._bin,c=[];s<o;){var u=r[s],f=r[s+1];r[s+2],r[s+3],r[s+4];var h=1,d=null,m=null;u<=20&&(d=u,h=1),u==12&&(d=100*u+f,h=2),u!=19&&u!=20||(d=u,h=2),21<=u&&u<=27&&(d=u,h=1),u==28&&(m=l.readShort(r,s+1),h=3),29<=u&&u<=31&&(d=u,h=1),32<=u&&u<=246&&(m=u-139,h=1),247<=u&&u<=250&&(m=256*(u-247)+f+108,h=2),251<=u&&u<=254&&(m=256*-(u-251)-f-108,h=2),u==255&&(m=l.readInt(r,s+1)/65535,h=5),c.push(m??"o"+d),s+=h}return c},e.CFF.readDict=function(r,s,a){for(var o=e._bin,l={},c=[];s<a;){var u=r[s],f=r[s+1];r[s+2],r[s+3],r[s+4];var h=1,d=null,m=null;if(u==28&&(m=o.readShort(r,s+1),h=3),u==29&&(m=o.readInt(r,s+1),h=5),32<=u&&u<=246&&(m=u-139,h=1),247<=u&&u<=250&&(m=256*(u-247)+f+108,h=2),251<=u&&u<=254&&(m=256*-(u-251)-f-108,h=2),u==255)throw m=o.readInt(r,s+1)/65535,h=5,"unknown number";if(u==30){var g=[];for(h=1;;){var p=r[s+h];h++;var _=p>>4,v=15&p;if(_!=15&&g.push(_),v!=15&&g.push(v),v==15)break}for(var b="",S=[0,1,2,3,4,5,6,7,8,9,".","e","e-","reserved","-","endOfNumber"],E=0;E<g.length;E++)b+=S[g[E]];m=parseFloat(b)}u<=21&&(d=["version","Notice","FullName","FamilyName","Weight","FontBBox","BlueValues","OtherBlues","FamilyBlues","FamilyOtherBlues","StdHW","StdVW","escape","UniqueID","XUID","charset","Encoding","CharStrings","Private","Subrs","defaultWidthX","nominalWidthX"][u],h=1,u==12&&(d=["Copyright","isFixedPitch","ItalicAngle","UnderlinePosition","UnderlineThickness","PaintType","CharstringType","FontMatrix","StrokeWidth","BlueScale","BlueShift","BlueFuzz","StemSnapH","StemSnapV","ForceBold",0,0,"LanguageGroup","ExpansionFactor","initialRandomSeed","SyntheticBase","PostScript","BaseFontName","BaseFontBlend",0,0,0,0,0,0,"ROS","CIDFontVersion","CIDFontRevision","CIDFontType","CIDCount","UIDBase","FDArray","FDSelect","FontName"][f],h=2)),d!=null?(l[d]=c.length==1?c[0]:c,c=[]):c.push(m),s+=h}return l},e.cmap={},e.cmap.parse=function(r,s,a){r=new Uint8Array(r.buffer,s,a),s=0;var o=e._bin,l={};o.readUshort(r,s),s+=2;var c=o.readUshort(r,s);s+=2;var u=[];l.tables=[];for(var f=0;f<c;f++){var h=o.readUshort(r,s);s+=2;var d=o.readUshort(r,s);s+=2;var m=o.readUint(r,s);s+=4;var g="p"+h+"e"+d,p=u.indexOf(m);if(p==-1){var _;p=l.tables.length,u.push(m);var v=o.readUshort(r,m);v==0?_=e.cmap.parse0(r,m):v==4?_=e.cmap.parse4(r,m):v==6?_=e.cmap.parse6(r,m):v==12?_=e.cmap.parse12(r,m):console.debug("unknown format: "+v,h,d,m),l.tables.push(_)}if(l[g]!=null)throw"multiple tables for one platform+encoding";l[g]=p}return l},e.cmap.parse0=function(r,s){var a=e._bin,o={};o.format=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);s+=2,a.readUshort(r,s),s+=2,o.map=[];for(var c=0;c<l-6;c++)o.map.push(r[s+c]);return o},e.cmap.parse4=function(r,s){var a=e._bin,o=s,l={};l.format=a.readUshort(r,s),s+=2;var c=a.readUshort(r,s);s+=2,a.readUshort(r,s),s+=2;var u=a.readUshort(r,s);s+=2;var f=u/2;l.searchRange=a.readUshort(r,s),s+=2,l.entrySelector=a.readUshort(r,s),s+=2,l.rangeShift=a.readUshort(r,s),s+=2,l.endCount=a.readUshorts(r,s,f),s+=2*f,s+=2,l.startCount=a.readUshorts(r,s,f),s+=2*f,l.idDelta=[];for(var h=0;h<f;h++)l.idDelta.push(a.readShort(r,s)),s+=2;for(l.idRangeOffset=a.readUshorts(r,s,f),s+=2*f,l.glyphIdArray=[];s<o+c;)l.glyphIdArray.push(a.readUshort(r,s)),s+=2;return l},e.cmap.parse6=function(r,s){var a=e._bin,o={};o.format=a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2,a.readUshort(r,s),s+=2,o.firstCode=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);s+=2,o.glyphIdArray=[];for(var c=0;c<l;c++)o.glyphIdArray.push(a.readUshort(r,s)),s+=2;return o},e.cmap.parse12=function(r,s){var a=e._bin,o={};o.format=a.readUshort(r,s),s+=2,s+=2,a.readUint(r,s),s+=4,a.readUint(r,s),s+=4;var l=a.readUint(r,s);s+=4,o.groups=[];for(var c=0;c<l;c++){var u=s+12*c,f=a.readUint(r,u+0),h=a.readUint(r,u+4),d=a.readUint(r,u+8);o.groups.push([f,h,d])}return o},e.glyf={},e.glyf.parse=function(r,s,a,o){for(var l=[],c=0;c<o.maxp.numGlyphs;c++)l.push(null);return l},e.glyf._parseGlyf=function(r,s){var a=e._bin,o=r._data,l=e._tabOffset(o,"glyf",r._offset)+r.loca[s];if(r.loca[s]==r.loca[s+1])return null;var c={};if(c.noc=a.readShort(o,l),l+=2,c.xMin=a.readShort(o,l),l+=2,c.yMin=a.readShort(o,l),l+=2,c.xMax=a.readShort(o,l),l+=2,c.yMax=a.readShort(o,l),l+=2,c.xMin>=c.xMax||c.yMin>=c.yMax)return null;if(c.noc>0){c.endPts=[];for(var u=0;u<c.noc;u++)c.endPts.push(a.readUshort(o,l)),l+=2;var f=a.readUshort(o,l);if(l+=2,o.length-l<f)return null;c.instructions=a.readBytes(o,l,f),l+=f;var h=c.endPts[c.noc-1]+1;for(c.flags=[],u=0;u<h;u++){var d=o[l];if(l++,c.flags.push(d),(8&d)!=0){var m=o[l];l++;for(var g=0;g<m;g++)c.flags.push(d),u++}}for(c.xs=[],u=0;u<h;u++){var p=(2&c.flags[u])!=0,_=(16&c.flags[u])!=0;p?(c.xs.push(_?o[l]:-o[l]),l++):_?c.xs.push(0):(c.xs.push(a.readShort(o,l)),l+=2)}for(c.ys=[],u=0;u<h;u++)p=(4&c.flags[u])!=0,_=(32&c.flags[u])!=0,p?(c.ys.push(_?o[l]:-o[l]),l++):_?c.ys.push(0):(c.ys.push(a.readShort(o,l)),l+=2);var v=0,b=0;for(u=0;u<h;u++)v+=c.xs[u],b+=c.ys[u],c.xs[u]=v,c.ys[u]=b}else{var S;c.parts=[];do{S=a.readUshort(o,l),l+=2;var E={m:{a:1,b:0,c:0,d:1,tx:0,ty:0},p1:-1,p2:-1};if(c.parts.push(E),E.glyphIndex=a.readUshort(o,l),l+=2,1&S){var M=a.readShort(o,l);l+=2;var T=a.readShort(o,l);l+=2}else M=a.readInt8(o,l),l++,T=a.readInt8(o,l),l++;2&S?(E.m.tx=M,E.m.ty=T):(E.p1=M,E.p2=T),8&S?(E.m.a=E.m.d=a.readF2dot14(o,l),l+=2):64&S?(E.m.a=a.readF2dot14(o,l),l+=2,E.m.d=a.readF2dot14(o,l),l+=2):128&S&&(E.m.a=a.readF2dot14(o,l),l+=2,E.m.b=a.readF2dot14(o,l),l+=2,E.m.c=a.readF2dot14(o,l),l+=2,E.m.d=a.readF2dot14(o,l),l+=2)}while(32&S);if(256&S){var x=a.readUshort(o,l);for(l+=2,c.instr=[],u=0;u<x;u++)c.instr.push(o[l]),l++}}return c},e.GDEF={},e.GDEF.parse=function(r,s,a,o){var l=s;s+=4;var c=e._bin.readUshort(r,s);return{glyphClassDef:c===0?null:e._lctf.readClassDef(r,l+c)}},e.GPOS={},e.GPOS.parse=function(r,s,a,o){return e._lctf.parse(r,s,a,o,e.GPOS.subt)},e.GPOS.subt=function(r,s,a,o){var l=e._bin,c=a,u={};if(u.fmt=l.readUshort(r,a),a+=2,s==1||s==2||s==3||s==7||s==8&&u.fmt<=2){var f=l.readUshort(r,a);a+=2,u.coverage=e._lctf.readCoverage(r,f+c)}if(s==1&&u.fmt==1){var h=l.readUshort(r,a);a+=2,h!=0&&(u.pos=e.GPOS.readValueRecord(r,a,h))}else if(s==2&&u.fmt>=1&&u.fmt<=2){h=l.readUshort(r,a),a+=2;var d=l.readUshort(r,a);a+=2;var m=e._lctf.numOfOnes(h),g=e._lctf.numOfOnes(d);if(u.fmt==1){u.pairsets=[];var p=l.readUshort(r,a);a+=2;for(var _=0;_<p;_++){var v=c+l.readUshort(r,a);a+=2;var b=l.readUshort(r,v);v+=2;for(var S=[],E=0;E<b;E++){var M=l.readUshort(r,v);v+=2,h!=0&&(R=e.GPOS.readValueRecord(r,v,h),v+=2*m),d!=0&&(L=e.GPOS.readValueRecord(r,v,d),v+=2*g),S.push({gid2:M,val1:R,val2:L})}u.pairsets.push(S)}}if(u.fmt==2){var T=l.readUshort(r,a);a+=2;var x=l.readUshort(r,a);a+=2;var y=l.readUshort(r,a);a+=2;var w=l.readUshort(r,a);for(a+=2,u.classDef1=e._lctf.readClassDef(r,c+T),u.classDef2=e._lctf.readClassDef(r,c+x),u.matrix=[],_=0;_<y;_++){var C=[];for(E=0;E<w;E++){var R=null,L=null;h!=0&&(R=e.GPOS.readValueRecord(r,a,h),a+=2*m),d!=0&&(L=e.GPOS.readValueRecord(r,a,d),a+=2*g),C.push({val1:R,val2:L})}u.matrix.push(C)}}}else if(s==4&&u.fmt==1)u.markCoverage=e._lctf.readCoverage(r,l.readUshort(r,a)+c),u.baseCoverage=e._lctf.readCoverage(r,l.readUshort(r,a+2)+c),u.markClassCount=l.readUshort(r,a+4),u.markArray=e.GPOS.readMarkArray(r,l.readUshort(r,a+6)+c),u.baseArray=e.GPOS.readBaseArray(r,l.readUshort(r,a+8)+c,u.markClassCount);else if(s==6&&u.fmt==1)u.mark1Coverage=e._lctf.readCoverage(r,l.readUshort(r,a)+c),u.mark2Coverage=e._lctf.readCoverage(r,l.readUshort(r,a+2)+c),u.markClassCount=l.readUshort(r,a+4),u.mark1Array=e.GPOS.readMarkArray(r,l.readUshort(r,a+6)+c),u.mark2Array=e.GPOS.readBaseArray(r,l.readUshort(r,a+8)+c,u.markClassCount);else{if(s==9&&u.fmt==1){var U=l.readUshort(r,a);a+=2;var I=l.readUint(r,a);if(a+=4,o.ltype==9)o.ltype=U;else if(o.ltype!=U)throw"invalid extension substitution";return e.GPOS.subt(r,o.ltype,c+I)}console.debug("unsupported GPOS table LookupType",s,"format",u.fmt)}return u},e.GPOS.readValueRecord=function(r,s,a){var o=e._bin,l=[];return l.push(1&a?o.readShort(r,s):0),s+=1&a?2:0,l.push(2&a?o.readShort(r,s):0),s+=2&a?2:0,l.push(4&a?o.readShort(r,s):0),s+=4&a?2:0,l.push(8&a?o.readShort(r,s):0),s+=8&a?2:0,l},e.GPOS.readBaseArray=function(r,s,a){var o=e._bin,l=[],c=s,u=o.readUshort(r,s);s+=2;for(var f=0;f<u;f++){for(var h=[],d=0;d<a;d++)h.push(e.GPOS.readAnchorRecord(r,c+o.readUshort(r,s))),s+=2;l.push(h)}return l},e.GPOS.readMarkArray=function(r,s){var a=e._bin,o=[],l=s,c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=e.GPOS.readAnchorRecord(r,a.readUshort(r,s+2)+l);f.markClass=a.readUshort(r,s),o.push(f),s+=4}return o},e.GPOS.readAnchorRecord=function(r,s){var a=e._bin,o={};return o.fmt=a.readUshort(r,s),o.x=a.readShort(r,s+2),o.y=a.readShort(r,s+4),o},e.GSUB={},e.GSUB.parse=function(r,s,a,o){return e._lctf.parse(r,s,a,o,e.GSUB.subt)},e.GSUB.subt=function(r,s,a,o){var l=e._bin,c=a,u={};if(u.fmt=l.readUshort(r,a),a+=2,s!=1&&s!=2&&s!=4&&s!=5&&s!=6)return null;if(s==1||s==2||s==4||s==5&&u.fmt<=2||s==6&&u.fmt<=2){var f=l.readUshort(r,a);a+=2,u.coverage=e._lctf.readCoverage(r,c+f)}if(s==1&&u.fmt>=1&&u.fmt<=2){if(u.fmt==1)u.delta=l.readShort(r,a),a+=2;else if(u.fmt==2){var h=l.readUshort(r,a);a+=2,u.newg=l.readUshorts(r,a,h),a+=2*u.newg.length}}else if(s==2&&u.fmt==1){h=l.readUshort(r,a),a+=2,u.seqs=[];for(var d=0;d<h;d++){var m=l.readUshort(r,a)+c;a+=2;var g=l.readUshort(r,m);u.seqs.push(l.readUshorts(r,m+2,g))}}else if(s==4)for(u.vals=[],h=l.readUshort(r,a),a+=2,d=0;d<h;d++){var p=l.readUshort(r,a);a+=2,u.vals.push(e.GSUB.readLigatureSet(r,c+p))}else if(s==5&&u.fmt==2){if(u.fmt==2){var _=l.readUshort(r,a);a+=2,u.cDef=e._lctf.readClassDef(r,c+_),u.scset=[];var v=l.readUshort(r,a);for(a+=2,d=0;d<v;d++){var b=l.readUshort(r,a);a+=2,u.scset.push(b==0?null:e.GSUB.readSubClassSet(r,c+b))}}}else if(s==6&&u.fmt==3){if(u.fmt==3){for(d=0;d<3;d++){h=l.readUshort(r,a),a+=2;for(var S=[],E=0;E<h;E++)S.push(e._lctf.readCoverage(r,c+l.readUshort(r,a+2*E)));a+=2*h,d==0&&(u.backCvg=S),d==1&&(u.inptCvg=S),d==2&&(u.ahedCvg=S)}h=l.readUshort(r,a),a+=2,u.lookupRec=e.GSUB.readSubstLookupRecords(r,a,h)}}else{if(s==7&&u.fmt==1){var M=l.readUshort(r,a);a+=2;var T=l.readUint(r,a);if(a+=4,o.ltype==9)o.ltype=M;else if(o.ltype!=M)throw"invalid extension substitution";return e.GSUB.subt(r,o.ltype,c+T)}console.debug("unsupported GSUB table LookupType",s,"format",u.fmt)}return u},e.GSUB.readSubClassSet=function(r,s){var a=e._bin.readUshort,o=s,l=[],c=a(r,s);s+=2;for(var u=0;u<c;u++){var f=a(r,s);s+=2,l.push(e.GSUB.readSubClassRule(r,o+f))}return l},e.GSUB.readSubClassRule=function(r,s){var a=e._bin.readUshort,o={},l=a(r,s),c=a(r,s+=2);s+=2,o.input=[];for(var u=0;u<l-1;u++)o.input.push(a(r,s)),s+=2;return o.substLookupRecords=e.GSUB.readSubstLookupRecords(r,s,c),o},e.GSUB.readSubstLookupRecords=function(r,s,a){for(var o=e._bin.readUshort,l=[],c=0;c<a;c++)l.push(o(r,s),o(r,s+2)),s+=4;return l},e.GSUB.readChainSubClassSet=function(r,s){var a=e._bin,o=s,l=[],c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readUshort(r,s);s+=2,l.push(e.GSUB.readChainSubClassRule(r,o+f))}return l},e.GSUB.readChainSubClassRule=function(r,s){for(var a=e._bin,o={},l=["backtrack","input","lookahead"],c=0;c<l.length;c++){var u=a.readUshort(r,s);s+=2,c==1&&u--,o[l[c]]=a.readUshorts(r,s,u),s+=2*o[l[c]].length}return u=a.readUshort(r,s),s+=2,o.subst=a.readUshorts(r,s,2*u),s+=2*o.subst.length,o},e.GSUB.readLigatureSet=function(r,s){var a=e._bin,o=s,l=[],c=a.readUshort(r,s);s+=2;for(var u=0;u<c;u++){var f=a.readUshort(r,s);s+=2,l.push(e.GSUB.readLigature(r,o+f))}return l},e.GSUB.readLigature=function(r,s){var a=e._bin,o={chain:[]};o.nglyph=a.readUshort(r,s),s+=2;var l=a.readUshort(r,s);s+=2;for(var c=0;c<l-1;c++)o.chain.push(a.readUshort(r,s)),s+=2;return o},e.head={},e.head.parse=function(r,s,a){var o=e._bin,l={};return o.readFixed(r,s),s+=4,l.fontRevision=o.readFixed(r,s),s+=4,o.readUint(r,s),s+=4,o.readUint(r,s),s+=4,l.flags=o.readUshort(r,s),s+=2,l.unitsPerEm=o.readUshort(r,s),s+=2,l.created=o.readUint64(r,s),s+=8,l.modified=o.readUint64(r,s),s+=8,l.xMin=o.readShort(r,s),s+=2,l.yMin=o.readShort(r,s),s+=2,l.xMax=o.readShort(r,s),s+=2,l.yMax=o.readShort(r,s),s+=2,l.macStyle=o.readUshort(r,s),s+=2,l.lowestRecPPEM=o.readUshort(r,s),s+=2,l.fontDirectionHint=o.readShort(r,s),s+=2,l.indexToLocFormat=o.readShort(r,s),s+=2,l.glyphDataFormat=o.readShort(r,s),s+=2,l},e.hhea={},e.hhea.parse=function(r,s,a){var o=e._bin,l={};return o.readFixed(r,s),s+=4,l.ascender=o.readShort(r,s),s+=2,l.descender=o.readShort(r,s),s+=2,l.lineGap=o.readShort(r,s),s+=2,l.advanceWidthMax=o.readUshort(r,s),s+=2,l.minLeftSideBearing=o.readShort(r,s),s+=2,l.minRightSideBearing=o.readShort(r,s),s+=2,l.xMaxExtent=o.readShort(r,s),s+=2,l.caretSlopeRise=o.readShort(r,s),s+=2,l.caretSlopeRun=o.readShort(r,s),s+=2,l.caretOffset=o.readShort(r,s),s+=2,s+=8,l.metricDataFormat=o.readShort(r,s),s+=2,l.numberOfHMetrics=o.readUshort(r,s),s+=2,l},e.hmtx={},e.hmtx.parse=function(r,s,a,o){for(var l=e._bin,c={aWidth:[],lsBearing:[]},u=0,f=0,h=0;h<o.maxp.numGlyphs;h++)h<o.hhea.numberOfHMetrics&&(u=l.readUshort(r,s),s+=2,f=l.readShort(r,s),s+=2),c.aWidth.push(u),c.lsBearing.push(f);return c},e.kern={},e.kern.parse=function(r,s,a,o){var l=e._bin,c=l.readUshort(r,s);if(s+=2,c==1)return e.kern.parseV1(r,s-2,a,o);var u=l.readUshort(r,s);s+=2;for(var f={glyph1:[],rval:[]},h=0;h<u;h++){s+=2,a=l.readUshort(r,s),s+=2;var d=l.readUshort(r,s);s+=2;var m=d>>>8;if((m&=15)!=0)throw"unknown kern table format: "+m;s=e.kern.readFormat0(r,s,f)}return f},e.kern.parseV1=function(r,s,a,o){var l=e._bin;l.readFixed(r,s),s+=4;var c=l.readUint(r,s);s+=4;for(var u={glyph1:[],rval:[]},f=0;f<c;f++){l.readUint(r,s),s+=4;var h=l.readUshort(r,s);s+=2,l.readUshort(r,s),s+=2;var d=h>>>8;if((d&=15)!=0)throw"unknown kern table format: "+d;s=e.kern.readFormat0(r,s,u)}return u},e.kern.readFormat0=function(r,s,a){var o=e._bin,l=-1,c=o.readUshort(r,s);s+=2,o.readUshort(r,s),s+=2,o.readUshort(r,s),s+=2,o.readUshort(r,s),s+=2;for(var u=0;u<c;u++){var f=o.readUshort(r,s);s+=2;var h=o.readUshort(r,s);s+=2;var d=o.readShort(r,s);s+=2,f!=l&&(a.glyph1.push(f),a.rval.push({glyph2:[],vals:[]}));var m=a.rval[a.rval.length-1];m.glyph2.push(h),m.vals.push(d),l=f}return s},e.loca={},e.loca.parse=function(r,s,a,o){var l=e._bin,c=[],u=o.head.indexToLocFormat,f=o.maxp.numGlyphs+1;if(u==0)for(var h=0;h<f;h++)c.push(l.readUshort(r,s+(h<<1))<<1);if(u==1)for(h=0;h<f;h++)c.push(l.readUint(r,s+(h<<2)));return c},e.maxp={},e.maxp.parse=function(r,s,a){var o=e._bin,l={},c=o.readUint(r,s);return s+=4,l.numGlyphs=o.readUshort(r,s),s+=2,c==65536&&(l.maxPoints=o.readUshort(r,s),s+=2,l.maxContours=o.readUshort(r,s),s+=2,l.maxCompositePoints=o.readUshort(r,s),s+=2,l.maxCompositeContours=o.readUshort(r,s),s+=2,l.maxZones=o.readUshort(r,s),s+=2,l.maxTwilightPoints=o.readUshort(r,s),s+=2,l.maxStorage=o.readUshort(r,s),s+=2,l.maxFunctionDefs=o.readUshort(r,s),s+=2,l.maxInstructionDefs=o.readUshort(r,s),s+=2,l.maxStackElements=o.readUshort(r,s),s+=2,l.maxSizeOfInstructions=o.readUshort(r,s),s+=2,l.maxComponentElements=o.readUshort(r,s),s+=2,l.maxComponentDepth=o.readUshort(r,s),s+=2),l},e.name={},e.name.parse=function(r,s,a){var o=e._bin,l={};o.readUshort(r,s),s+=2;var c=o.readUshort(r,s);s+=2,o.readUshort(r,s);for(var u,f=["copyright","fontFamily","fontSubfamily","ID","fullName","version","postScriptName","trademark","manufacturer","designer","description","urlVendor","urlDesigner","licence","licenceURL","---","typoFamilyName","typoSubfamilyName","compatibleFull","sampleText","postScriptCID","wwsFamilyName","wwsSubfamilyName","lightPalette","darkPalette"],h=s+=2,d=0;d<c;d++){var m=o.readUshort(r,s);s+=2;var g=o.readUshort(r,s);s+=2;var p=o.readUshort(r,s);s+=2;var _=o.readUshort(r,s);s+=2;var v=o.readUshort(r,s);s+=2;var b=o.readUshort(r,s);s+=2;var S,E=f[_],M=h+12*c+b;if(m==0)S=o.readUnicode(r,M,v/2);else if(m==3&&g==0)S=o.readUnicode(r,M,v/2);else if(g==0)S=o.readASCII(r,M,v);else if(g==1)S=o.readUnicode(r,M,v/2);else if(g==3)S=o.readUnicode(r,M,v/2);else{if(m!=1)throw"unknown encoding "+g+", platformID: "+m;S=o.readASCII(r,M,v),console.debug("reading unknown MAC encoding "+g+" as ASCII")}var T="p"+m+","+p.toString(16);l[T]==null&&(l[T]={}),l[T][E!==void 0?E:_]=S,l[T]._lang=p}for(var x in l)if(l[x].postScriptName!=null&&l[x]._lang==1033)return l[x];for(var x in l)if(l[x].postScriptName!=null&&l[x]._lang==0)return l[x];for(var x in l)if(l[x].postScriptName!=null&&l[x]._lang==3084)return l[x];for(var x in l)if(l[x].postScriptName!=null)return l[x];for(var x in l){u=x;break}return console.debug("returning name table with languageID "+l[u]._lang),l[u]},e["OS/2"]={},e["OS/2"].parse=function(r,s,a){var o=e._bin.readUshort(r,s);s+=2;var l={};if(o==0)e["OS/2"].version0(r,s,l);else if(o==1)e["OS/2"].version1(r,s,l);else if(o==2||o==3||o==4)e["OS/2"].version2(r,s,l);else{if(o!=5)throw"unknown OS/2 table version: "+o;e["OS/2"].version5(r,s,l)}return l},e["OS/2"].version0=function(r,s,a){var o=e._bin;return a.xAvgCharWidth=o.readShort(r,s),s+=2,a.usWeightClass=o.readUshort(r,s),s+=2,a.usWidthClass=o.readUshort(r,s),s+=2,a.fsType=o.readUshort(r,s),s+=2,a.ySubscriptXSize=o.readShort(r,s),s+=2,a.ySubscriptYSize=o.readShort(r,s),s+=2,a.ySubscriptXOffset=o.readShort(r,s),s+=2,a.ySubscriptYOffset=o.readShort(r,s),s+=2,a.ySuperscriptXSize=o.readShort(r,s),s+=2,a.ySuperscriptYSize=o.readShort(r,s),s+=2,a.ySuperscriptXOffset=o.readShort(r,s),s+=2,a.ySuperscriptYOffset=o.readShort(r,s),s+=2,a.yStrikeoutSize=o.readShort(r,s),s+=2,a.yStrikeoutPosition=o.readShort(r,s),s+=2,a.sFamilyClass=o.readShort(r,s),s+=2,a.panose=o.readBytes(r,s,10),s+=10,a.ulUnicodeRange1=o.readUint(r,s),s+=4,a.ulUnicodeRange2=o.readUint(r,s),s+=4,a.ulUnicodeRange3=o.readUint(r,s),s+=4,a.ulUnicodeRange4=o.readUint(r,s),s+=4,a.achVendID=[o.readInt8(r,s),o.readInt8(r,s+1),o.readInt8(r,s+2),o.readInt8(r,s+3)],s+=4,a.fsSelection=o.readUshort(r,s),s+=2,a.usFirstCharIndex=o.readUshort(r,s),s+=2,a.usLastCharIndex=o.readUshort(r,s),s+=2,a.sTypoAscender=o.readShort(r,s),s+=2,a.sTypoDescender=o.readShort(r,s),s+=2,a.sTypoLineGap=o.readShort(r,s),s+=2,a.usWinAscent=o.readUshort(r,s),s+=2,a.usWinDescent=o.readUshort(r,s),s+=2},e["OS/2"].version1=function(r,s,a){var o=e._bin;return s=e["OS/2"].version0(r,s,a),a.ulCodePageRange1=o.readUint(r,s),s+=4,a.ulCodePageRange2=o.readUint(r,s),s+=4},e["OS/2"].version2=function(r,s,a){var o=e._bin;return s=e["OS/2"].version1(r,s,a),a.sxHeight=o.readShort(r,s),s+=2,a.sCapHeight=o.readShort(r,s),s+=2,a.usDefault=o.readUshort(r,s),s+=2,a.usBreak=o.readUshort(r,s),s+=2,a.usMaxContext=o.readUshort(r,s),s+=2},e["OS/2"].version5=function(r,s,a){var o=e._bin;return s=e["OS/2"].version2(r,s,a),a.usLowerOpticalPointSize=o.readUshort(r,s),s+=2,a.usUpperOpticalPointSize=o.readUshort(r,s),s+=2},e.post={},e.post.parse=function(r,s,a){var o=e._bin,l={};return l.version=o.readFixed(r,s),s+=4,l.italicAngle=o.readFixed(r,s),s+=4,l.underlinePosition=o.readShort(r,s),s+=2,l.underlineThickness=o.readShort(r,s),s+=2,l},e==null&&(e={}),e.U==null&&(e.U={}),e.U.codeToGlyph=function(r,s){var a=r.cmap,o=-1;if(a.p0e4!=null?o=a.p0e4:a.p3e1!=null?o=a.p3e1:a.p1e0!=null?o=a.p1e0:a.p0e3!=null&&(o=a.p0e3),o==-1)throw"no familiar platform and encoding!";var l=a.tables[o];if(l.format==0)return s>=l.map.length?0:l.map[s];if(l.format==4){for(var c=-1,u=0;u<l.endCount.length;u++)if(s<=l.endCount[u]){c=u;break}return c==-1||l.startCount[c]>s?0:65535&(l.idRangeOffset[c]!=0?l.glyphIdArray[s-l.startCount[c]+(l.idRangeOffset[c]>>1)-(l.idRangeOffset.length-c)]:s+l.idDelta[c])}if(l.format==12){if(s>l.groups[l.groups.length-1][1])return 0;for(u=0;u<l.groups.length;u++){var f=l.groups[u];if(f[0]<=s&&s<=f[1])return f[2]+(s-f[0])}return 0}throw"unknown cmap table format "+l.format},e.U.glyphToPath=function(r,s){var a={cmds:[],crds:[]};if(r.SVG&&r.SVG.entries[s]){var o=r.SVG.entries[s];return o==null?a:(typeof o=="string"&&(o=e.SVG.toPath(o),r.SVG.entries[s]=o),o)}if(r.CFF){var l={x:0,y:0,stack:[],nStems:0,haveWidth:!1,width:r.CFF.Private?r.CFF.Private.defaultWidthX:0,open:!1},c=r.CFF,u=r.CFF.Private;if(c.ROS){for(var f=0;c.FDSelect[f+2]<=s;)f+=2;u=c.FDArray[c.FDSelect[f+1]].Private}e.U._drawCFF(r.CFF.CharStrings[s],l,c,u,a)}else r.glyf&&e.U._drawGlyf(s,r,a);return a},e.U._drawGlyf=function(r,s,a){var o=s.glyf[r];o==null&&(o=s.glyf[r]=e.glyf._parseGlyf(s,r)),o!=null&&(o.noc>-1?e.U._simpleGlyph(o,a):e.U._compoGlyph(o,s,a))},e.U._simpleGlyph=function(r,s){for(var a=0;a<r.noc;a++){for(var o=a==0?0:r.endPts[a-1]+1,l=r.endPts[a],c=o;c<=l;c++){var u=c==o?l:c-1,f=c==l?o:c+1,h=1&r.flags[c],d=1&r.flags[u],m=1&r.flags[f],g=r.xs[c],p=r.ys[c];if(c==o)if(h){if(!d){e.U.P.moveTo(s,g,p);continue}e.U.P.moveTo(s,r.xs[u],r.ys[u])}else d?e.U.P.moveTo(s,r.xs[u],r.ys[u]):e.U.P.moveTo(s,(r.xs[u]+g)/2,(r.ys[u]+p)/2);h?d&&e.U.P.lineTo(s,g,p):m?e.U.P.qcurveTo(s,g,p,r.xs[f],r.ys[f]):e.U.P.qcurveTo(s,g,p,(g+r.xs[f])/2,(p+r.ys[f])/2)}e.U.P.closePath(s)}},e.U._compoGlyph=function(r,s,a){for(var o=0;o<r.parts.length;o++){var l={cmds:[],crds:[]},c=r.parts[o];e.U._drawGlyf(c.glyphIndex,s,l);for(var u=c.m,f=0;f<l.crds.length;f+=2){var h=l.crds[f],d=l.crds[f+1];a.crds.push(h*u.a+d*u.b+u.tx),a.crds.push(h*u.c+d*u.d+u.ty)}for(f=0;f<l.cmds.length;f++)a.cmds.push(l.cmds[f])}},e.U._getGlyphClass=function(r,s){var a=e._lctf.getInterval(s,r);return a==-1?0:s[a+2]},e.U._applySubs=function(r,s,a,o){for(var l=r.length-s-1,c=0;c<a.tabs.length;c++)if(a.tabs[c]!=null){var u,f=a.tabs[c];if(!f.coverage||(u=e._lctf.coverageIndex(f.coverage,r[s]))!=-1){if(a.ltype==1)r[s],f.fmt==1?r[s]=r[s]+f.delta:r[s]=f.newg[u];else if(a.ltype==4)for(var h=f.vals[u],d=0;d<h.length;d++){var m=h[d],g=m.chain.length;if(!(g>l)){for(var p=!0,_=0,v=0;v<g;v++){for(;r[s+_+(1+v)]==-1;)_++;m.chain[v]!=r[s+_+(1+v)]&&(p=!1)}if(p){for(r[s]=m.nglyph,v=0;v<g+_;v++)r[s+v+1]=-1;break}}}else if(a.ltype==5&&f.fmt==2)for(var b=e._lctf.getInterval(f.cDef,r[s]),S=f.cDef[b+2],E=f.scset[S],M=0;M<E.length;M++){var T=E[M],x=T.input;if(!(x.length>l)){for(p=!0,v=0;v<x.length;v++){var y=e._lctf.getInterval(f.cDef,r[s+1+v]);if(b==-1&&f.cDef[y+2]!=x[v]){p=!1;break}}if(p){var w=T.substLookupRecords;for(d=0;d<w.length;d+=2)w[d],w[d+1]}}}else if(a.ltype==6&&f.fmt==3){if(!e.U._glsCovered(r,f.backCvg,s-f.backCvg.length)||!e.U._glsCovered(r,f.inptCvg,s)||!e.U._glsCovered(r,f.ahedCvg,s+f.inptCvg.length))continue;var C=f.lookupRec;for(M=0;M<C.length;M+=2){b=C[M];var R=o[C[M+1]];e.U._applySubs(r,s+b,R,o)}}}}},e.U._glsCovered=function(r,s,a){for(var o=0;o<s.length;o++)if(e._lctf.coverageIndex(s[o],r[a+o])==-1)return!1;return!0},e.U.glyphsToPath=function(r,s,a){for(var o={cmds:[],crds:[]},l=0,c=0;c<s.length;c++){var u=s[c];if(u!=-1){for(var f=c<s.length-1&&s[c+1]!=-1?s[c+1]:0,h=e.U.glyphToPath(r,u),d=0;d<h.crds.length;d+=2)o.crds.push(h.crds[d]+l),o.crds.push(h.crds[d+1]);for(a&&o.cmds.push(a),d=0;d<h.cmds.length;d++)o.cmds.push(h.cmds[d]);a&&o.cmds.push("X"),l+=r.hmtx.aWidth[u],c<s.length-1&&(l+=e.U.getPairAdjustment(r,u,f))}}return o},e.U.P={},e.U.P.moveTo=function(r,s,a){r.cmds.push("M"),r.crds.push(s,a)},e.U.P.lineTo=function(r,s,a){r.cmds.push("L"),r.crds.push(s,a)},e.U.P.curveTo=function(r,s,a,o,l,c,u){r.cmds.push("C"),r.crds.push(s,a,o,l,c,u)},e.U.P.qcurveTo=function(r,s,a,o,l){r.cmds.push("Q"),r.crds.push(s,a,o,l)},e.U.P.closePath=function(r){r.cmds.push("Z")},e.U._drawCFF=function(r,s,a,o,l){for(var c=s.stack,u=s.nStems,f=s.haveWidth,h=s.width,d=s.open,m=0,g=s.x,p=s.y,_=0,v=0,b=0,S=0,E=0,M=0,T=0,x=0,y=0,w=0,C={val:0,size:0};m<r.length;){e.CFF.getCharString(r,m,C);var R=C.val;if(m+=C.size,R=="o1"||R=="o18")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0;else if(R=="o3"||R=="o23")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0;else if(R=="o4")c.length>1&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),d&&e.U.P.closePath(l),p+=c.pop(),e.U.P.moveTo(l,g,p),d=!0;else if(R=="o5")for(;c.length>0;)g+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,g,p);else if(R=="o6"||R=="o7")for(var L=c.length,U=R=="o6",I=0;I<L;I++){var F=c.shift();U?g+=F:p+=F,U=!U,e.U.P.lineTo(l,g,p)}else if(R=="o8"||R=="o24"){L=c.length;for(var N=0;N+6<=L;)_=g+c.shift(),v=p+c.shift(),b=_+c.shift(),S=v+c.shift(),g=b+c.shift(),p=S+c.shift(),e.U.P.curveTo(l,_,v,b,S,g,p),N+=6;R=="o24"&&(g+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,g,p))}else{if(R=="o11")break;if(R=="o1234"||R=="o1235"||R=="o1236"||R=="o1237")R=="o1234"&&(v=p,b=(_=g+c.shift())+c.shift(),w=S=v+c.shift(),M=S,x=p,g=(T=(E=(y=b+c.shift())+c.shift())+c.shift())+c.shift(),e.U.P.curveTo(l,_,v,b,S,y,w),e.U.P.curveTo(l,E,M,T,x,g,p)),R=="o1235"&&(_=g+c.shift(),v=p+c.shift(),b=_+c.shift(),S=v+c.shift(),y=b+c.shift(),w=S+c.shift(),E=y+c.shift(),M=w+c.shift(),T=E+c.shift(),x=M+c.shift(),g=T+c.shift(),p=x+c.shift(),c.shift(),e.U.P.curveTo(l,_,v,b,S,y,w),e.U.P.curveTo(l,E,M,T,x,g,p)),R=="o1236"&&(_=g+c.shift(),v=p+c.shift(),b=_+c.shift(),w=S=v+c.shift(),M=S,T=(E=(y=b+c.shift())+c.shift())+c.shift(),x=M+c.shift(),g=T+c.shift(),e.U.P.curveTo(l,_,v,b,S,y,w),e.U.P.curveTo(l,E,M,T,x,g,p)),R=="o1237"&&(_=g+c.shift(),v=p+c.shift(),b=_+c.shift(),S=v+c.shift(),y=b+c.shift(),w=S+c.shift(),E=y+c.shift(),M=w+c.shift(),T=E+c.shift(),x=M+c.shift(),Math.abs(T-g)>Math.abs(x-p)?g=T+c.shift():p=x+c.shift(),e.U.P.curveTo(l,_,v,b,S,y,w),e.U.P.curveTo(l,E,M,T,x,g,p));else if(R=="o14"){if(c.length>0&&!f&&(h=c.shift()+a.nominalWidthX,f=!0),c.length==4){var Y=c.shift(),j=c.shift(),Z=c.shift(),O=c.shift(),H=e.CFF.glyphBySE(a,Z),B=e.CFF.glyphBySE(a,O);e.U._drawCFF(a.CharStrings[H],s,a,o,l),s.x=Y,s.y=j,e.U._drawCFF(a.CharStrings[B],s,a,o,l)}d&&(e.U.P.closePath(l),d=!1)}else if(R=="o19"||R=="o20")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0,m+=u+7>>3;else if(R=="o21")c.length>2&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),p+=c.pop(),g+=c.pop(),d&&e.U.P.closePath(l),e.U.P.moveTo(l,g,p),d=!0;else if(R=="o22")c.length>1&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),g+=c.pop(),d&&e.U.P.closePath(l),e.U.P.moveTo(l,g,p),d=!0;else if(R=="o25"){for(;c.length>6;)g+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,g,p);_=g+c.shift(),v=p+c.shift(),b=_+c.shift(),S=v+c.shift(),g=b+c.shift(),p=S+c.shift(),e.U.P.curveTo(l,_,v,b,S,g,p)}else if(R=="o26")for(c.length%2&&(g+=c.shift());c.length>0;)_=g,v=p+c.shift(),g=b=_+c.shift(),p=(S=v+c.shift())+c.shift(),e.U.P.curveTo(l,_,v,b,S,g,p);else if(R=="o27")for(c.length%2&&(p+=c.shift());c.length>0;)v=p,b=(_=g+c.shift())+c.shift(),S=v+c.shift(),g=b+c.shift(),p=S,e.U.P.curveTo(l,_,v,b,S,g,p);else if(R=="o10"||R=="o29"){var V=R=="o10"?o:a;if(c.length==0)console.debug("error: empty stack");else{var G=c.pop(),z=V.Subrs[G+V.Bias];s.x=g,s.y=p,s.nStems=u,s.haveWidth=f,s.width=h,s.open=d,e.U._drawCFF(z,s,a,o,l),g=s.x,p=s.y,u=s.nStems,f=s.haveWidth,h=s.width,d=s.open}}else if(R=="o30"||R=="o31"){var W=c.length,q=(N=0,R=="o31");for(N+=W-(L=-3&W);N<L;)q?(v=p,b=(_=g+c.shift())+c.shift(),p=(S=v+c.shift())+c.shift(),L-N==5?(g=b+c.shift(),N++):g=b,q=!1):(_=g,v=p+c.shift(),b=_+c.shift(),S=v+c.shift(),g=b+c.shift(),L-N==5?(p=S+c.shift(),N++):p=S,q=!0),e.U.P.curveTo(l,_,v,b,S,g,p),N+=4}else{if((R+"").charAt(0)=="o")throw console.debug("Unknown operation: "+R,r),R;c.push(R)}}}s.x=g,s.y=p,s.nStems=u,s.haveWidth=f,s.width=h,s.open=d};var t=e,i={Typr:t};return n.Typr=t,n.default=i,Object.defineProperty(n,"__esModule",{value:!0}),n})({}).Typr}/*!
Custom bundle of woff2otf (https://github.com/arty-name/woff2otf) with fflate
(https://github.com/101arrowz/fflate) for use in Troika text rendering. 
Original licenses apply: 
- fflate: https://github.com/101arrowz/fflate/blob/master/LICENSE (MIT)
- woff2otf.js: https://github.com/arty-name/woff2otf/blob/master/woff2otf.js (Apache2)
*/function aS(){return(function(n){var e=Uint8Array,t=Uint16Array,i=Uint32Array,r=new e([0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0,0,0,0]),s=new e([0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,0,0]),a=new e([16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]),o=function(R,L){for(var U=new t(31),I=0;I<31;++I)U[I]=L+=1<<R[I-1];var F=new i(U[30]);for(I=1;I<30;++I)for(var N=U[I];N<U[I+1];++N)F[N]=N-U[I]<<5|I;return[U,F]},l=o(r,2),c=l[0],u=l[1];c[28]=258,u[258]=28;for(var f=o(s,0)[0],h=new t(32768),d=0;d<32768;++d){var m=(43690&d)>>>1|(21845&d)<<1;m=(61680&(m=(52428&m)>>>2|(13107&m)<<2))>>>4|(3855&m)<<4,h[d]=((65280&m)>>>8|(255&m)<<8)>>>1}var g=function(R,L,U){for(var I=R.length,F=0,N=new t(L);F<I;++F)++N[R[F]-1];var Y,j=new t(L);for(F=0;F<L;++F)j[F]=j[F-1]+N[F-1]<<1;{Y=new t(1<<L);var Z=15-L;for(F=0;F<I;++F)if(R[F])for(var O=F<<4|R[F],H=L-R[F],B=j[R[F]-1]++<<H,V=B|(1<<H)-1;B<=V;++B)Y[h[B]>>>Z]=O}return Y},p=new e(288);for(d=0;d<144;++d)p[d]=8;for(d=144;d<256;++d)p[d]=9;for(d=256;d<280;++d)p[d]=7;for(d=280;d<288;++d)p[d]=8;var _=new e(32);for(d=0;d<32;++d)_[d]=5;var v=g(p,9),b=g(_,5),S=function(R){for(var L=R[0],U=1;U<R.length;++U)R[U]>L&&(L=R[U]);return L},E=function(R,L,U){var I=L/8|0;return(R[I]|R[I+1]<<8)>>(7&L)&U},M=function(R,L){var U=L/8|0;return(R[U]|R[U+1]<<8|R[U+2]<<16)>>(7&L)},T=["unexpected EOF","invalid block type","invalid length/literal","invalid distance","stream finished","no stream handler",,"no callback","invalid UTF-8 data","extra field too long","date not in range 1980-2099","filename too long","stream finishing","invalid zip data"],x=function(R,L,U){var I=new Error(L||T[R]);if(I.code=R,Error.captureStackTrace&&Error.captureStackTrace(I,x),!U)throw I;return I},y=function(R,L,U){var I=R.length;if(!I||U&&!U.l&&I<5)return L||new e(0);var F=!L||U,N=!U||U.i;U||(U={}),L||(L=new e(3*I));var Y,j=function(ge){var Ie=L.length;if(ge>Ie){var Me=new e(Math.max(2*Ie,ge));Me.set(L),L=Me}},Z=U.f||0,O=U.p||0,H=U.b||0,B=U.l,V=U.d,G=U.m,z=U.n,W=8*I;do{if(!B){U.f=Z=E(R,O,1);var q=E(R,O+1,3);if(O+=3,!q){var ce=R[(k=((Y=O)/8|0)+(7&Y&&1)+4)-4]|R[k-3]<<8,me=k+ce;if(me>I){N&&x(0);break}F&&j(H+ce),L.set(R.subarray(k,me),H),U.b=H+=ce,U.p=O=8*me;continue}if(q==1)B=v,V=b,G=9,z=5;else if(q==2){var Q=E(R,O,31)+257,ie=E(R,O+10,15)+4,be=Q+E(R,O+5,31)+1;O+=14;for(var De=new e(be),ye=new e(19),_e=0;_e<ie;++_e)ye[a[_e]]=E(R,O+3*_e,7);O+=3*ie;var Ne=S(ye),ae=(1<<Ne)-1,Ee=g(ye,Ne);for(_e=0;_e<be;){var k,de=Ee[E(R,O,ae)];if(O+=15&de,(k=de>>>4)<16)De[_e++]=k;else{var Pe=0,we=0;for(k==16?(we=3+E(R,O,3),O+=2,Pe=De[_e-1]):k==17?(we=3+E(R,O,7),O+=3):k==18&&(we=11+E(R,O,127),O+=7);we--;)De[_e++]=Pe}}var pe=De.subarray(0,Q),Re=De.subarray(Q);G=S(pe),z=S(Re),B=g(pe,G),V=g(Re,z)}else x(1);if(O>W){N&&x(0);break}}F&&j(H+131072);for(var D=(1<<G)-1,A=(1<<z)-1,X=O;;X=O){var ee=(Pe=B[M(R,O)&D])>>>4;if((O+=15&Pe)>W){N&&x(0);break}if(Pe||x(2),ee<256)L[H++]=ee;else{if(ee==256){X=O,B=null;break}var he=ee-254;if(ee>264){var xe=r[_e=ee-257];he=E(R,O,(1<<xe)-1)+c[_e],O+=xe}var Te=V[M(R,O)&A],te=Te>>>4;if(Te||x(3),O+=15&Te,Re=f[te],te>3&&(xe=s[te],Re+=M(R,O)&(1<<xe)-1,O+=xe),O>W){N&&x(0);break}F&&j(H+131072);for(var le=H+he;H<le;H+=4)L[H]=L[H-Re],L[H+1]=L[H+1-Re],L[H+2]=L[H+2-Re],L[H+3]=L[H+3-Re];H=le}}U.l=B,U.p=X,U.b=H,B&&(Z=1,U.m=G,U.d=V,U.n=z)}while(!Z);return H==L.length?L:(function(ge,Ie,Me){(Me==null||Me>ge.length)&&(Me=ge.length);var Ae=new(ge instanceof t?t:ge instanceof i?i:e)(Me-Ie);return Ae.set(ge.subarray(Ie,Me)),Ae})(L,0,H)},w=new e(0),C=typeof TextDecoder<"u"&&new TextDecoder;try{C.decode(w,{stream:!0})}catch{}return n.convert_streams=function(R){var L=new DataView(R),U=0;function I(){var Q=L.getUint16(U);return U+=2,Q}function F(){var Q=L.getUint32(U);return U+=4,Q}function N(Q){ce.setUint16(me,Q),me+=2}function Y(Q){ce.setUint32(me,Q),me+=4}for(var j={signature:F(),flavor:F(),length:F(),numTables:I(),reserved:I(),totalSfntSize:F(),majorVersion:I(),minorVersion:I(),metaOffset:F(),metaLength:F(),metaOrigLength:F(),privOffset:F(),privLength:F()},Z=0;Math.pow(2,Z)<=j.numTables;)Z++;Z--;for(var O=16*Math.pow(2,Z),H=16*j.numTables-O,B=12,V=[],G=0;G<j.numTables;G++)V.push({tag:F(),offset:F(),compLength:F(),origLength:F(),origChecksum:F()}),B+=16;var z,W=new Uint8Array(12+16*V.length+V.reduce((function(Q,ie){return Q+ie.origLength+4}),0)),q=W.buffer,ce=new DataView(q),me=0;return Y(j.flavor),N(j.numTables),N(O),N(Z),N(H),V.forEach((function(Q){Y(Q.tag),Y(Q.origChecksum),Y(B),Y(Q.origLength),Q.outOffset=B,(B+=Q.origLength)%4!=0&&(B+=4-B%4)})),V.forEach((function(Q){var ie,be=R.slice(Q.offset,Q.offset+Q.compLength);if(Q.compLength!=Q.origLength){var De=new Uint8Array(Q.origLength);ie=new Uint8Array(be,2),y(ie,De)}else De=new Uint8Array(be);W.set(De,Q.outOffset);var ye=0;(B=Q.outOffset+Q.origLength)%4!=0&&(ye=4-B%4),W.set(new Uint8Array(ye).buffer,Q.outOffset+Q.origLength),z=B+ye})),q.slice(0,z)},Object.defineProperty(n,"__esModule",{value:!0}),n})({}).convert_streams}function oS(n,e){const t={M:2,L:2,Q:4,C:6,Z:0},i={C:"18g,ca,368,1kz",D:"17k,6,2,2+4,5+c,2+6,2+1,10+1,9+f,j+11,2+1,a,2,2+1,15+2,3,j+2,6+3,2+8,2,2,2+1,w+a,4+e,3+3,2,3+2,3+5,23+w,2f+4,3,2+9,2,b,2+3,3,1k+9,6+1,3+1,2+2,2+d,30g,p+y,1,1+1g,f+x,2,sd2+1d,jf3+4,f+3,2+4,2+2,b+3,42,2,4+2,2+1,2,3,t+1,9f+w,2,el+2,2+g,d+2,2l,2+1,5,3+1,2+1,2,3,6,16wm+1v",R:"17m+3,2,2,6+3,m,15+2,2+2,h+h,13,3+8,2,2,3+1,2,p+1,x,5+4,5,a,2,2,3,u,c+2,g+1,5,2+1,4+1,5j,6+1,2,b,2+2,f,2+1,1s+2,2,3+1,7,1ez0,2,2+1,4+4,b,4,3,b,42,2+2,4,3,2+1,2,o+3,ae,ep,x,2o+2,3+1,3,5+1,6",L:"x9u,jff,a,fd,jv",T:"4t,gj+33,7o+4,1+1,7c+18,2,2+1,2+1,2,21+a,2,1b+k,h,2u+6,3+5,3+1,2+3,y,2,v+q,2k+a,1n+8,a,p+3,2+8,2+2,2+4,18+2,3c+e,2+v,1k,2,5+7,5,4+6,b+1,u,1n,5+3,9,l+1,r,3+1,1m,5+1,5+1,3+2,4,v+1,4,c+1,1m,5+4,2+1,5,l+1,n+5,2,1n,3,2+3,9,8+1,c+1,v,1q,d,1f,4,1m+2,6+2,2+3,8+1,c+1,u,1n,3,7,6+1,l+1,t+1,1m+1,5+3,9,l+1,u,21,8+2,2,2j,3+6,d+7,2r,3+8,c+5,23+1,s,2,2,1k+d,2+4,2+1,6+a,2+z,a,2v+3,2+5,2+1,3+1,q+1,5+2,h+3,e,3+1,7,g,jk+2,qb+2,u+2,u+1,v+1,1t+1,2+6,9,3+a,a,1a+2,3c+1,z,3b+2,5+1,a,7+2,64+1,3,1n,2+6,2,2,3+7,7+9,3,1d+d,1,1+1,1s+3,1d,2+4,2,6,15+8,d+1,x+3,3+1,2+2,1l,2+1,4,2+2,1n+7,3+1,49+2,2+c,2+6,5,7,4+1,5j+1l,2+4,ek,3+1,r+4,1e+4,6+5,2p+c,1+3,1,1+2,1+b,2db+2,3y,2p+v,ff+3,30+1,n9x,1+2,2+9,x+1,29+1,7l,4,5,q+1,6,48+1,r+h,e,13+7,q+a,1b+2,1d,3+3,3+1,14,1w+5,3+1,3+1,d,9,1c,1g,2+2,3+1,6+1,2,17+1,9,6n,3,5,fn5,ki+f,h+f,5s,6y+2,ea,6b,46+4,1af+2,2+1,6+3,15+2,5,4m+1,fy+3,as+1,4a+a,4x,1j+e,1l+2,1e+3,3+1,1y+2,11+4,2+7,1r,d+1,1h+8,b+3,3,2o+2,3,2+1,7,4h,4+7,m+1,1m+1,4,12+6,4+4,5g+7,3+2,2,o,2d+5,2,5+1,2+1,6n+3,7+1,2+1,s+1,2e+7,3,2+1,2z,2,3+5,2,2u+2,3+3,2+4,78+8,2+1,75+1,2,5,41+3,3+1,5,x+9,15+5,3+3,9,a+5,3+2,1b+c,2+1,bb+6,2+5,2,2b+l,3+6,2+1,2+1,3f+5,4,2+1,2+6,2,21+1,4,2,9o+1,470+8,at4+4,1o+6,t5,1s+3,2a,f5l+1,2+3,43o+2,a+7,1+7,3+6,v+3,45+2,1j0+1i,5+1d,9,f,n+4,2+e,11t+6,2+g,3+6,2+1,2+4,7a+6,c6+3,15t+6,32+6,1,gzau,v+2n,3l+6n"},r=1,s=2,a=4,o=8,l=16,c=32;let u;function f(T){if(!u){const x={R:s,L:r,D:a,C:l,U:c,T:o};u=new Map;for(let y in i){let w=0;i[y].split(",").forEach(C=>{let[R,L]=C.split("+");R=parseInt(R,36),L=L?parseInt(L,36):0,u.set(w+=R,x[y]);for(let U=L;U--;)u.set(++w,x[y])})}}return u.get(T)||c}const h=1,d=2,m=3,g=4,p=[null,"isol","init","fina","medi"];function _(T){const x=new Uint8Array(T.length);let y=c,w=h,C=-1;for(let R=0;R<T.length;R++){const L=T.codePointAt(R);let U=f(L)|0,I=h;U&o||(y&(r|a|l)?U&(s|a|l)?(I=m,(w===h||w===m)&&x[C]++):U&(r|c)&&(w===d||w===g)&&x[C]--:y&(s|c)&&(w===d||w===g)&&x[C]--,w=x[R]=I,y=U,C=R,L>65535&&R++)}return x}function v(T,x){const y=[];for(let C=0;C<x.length;C++){const R=x.codePointAt(C);R>65535&&C++,y.push(n.U.codeToGlyph(T,R))}const w=T.GSUB;if(w){const{lookupList:C,featureList:R}=w;let L;const U=/^(rlig|liga|mset|isol|init|fina|medi|half|pres|blws|ccmp)$/,I=[];R.forEach(F=>{if(U.test(F.tag))for(let N=0;N<F.tab.length;N++){if(I[F.tab[N]])continue;I[F.tab[N]]=!0;const Y=C[F.tab[N]],j=/^(isol|init|fina|medi)$/.test(F.tag);j&&!L&&(L=_(x));for(let Z=0;Z<y.length;Z++)(!L||!j||p[L[Z]]===F.tag)&&n.U._applySubs(y,Z,Y,C)}})}return y}function b(T,x){const y=new Int16Array(x.length*3);let w=0;for(;w<x.length;w++){const U=x[w];if(U===-1)continue;y[w*3+2]=T.hmtx.aWidth[U];const I=T.GPOS;if(I){const F=I.lookupList;for(let N=0;N<F.length;N++){const Y=F[N];for(let j=0;j<Y.tabs.length;j++){const Z=Y.tabs[j];if(Y.ltype===1){if(n._lctf.coverageIndex(Z.coverage,U)!==-1&&Z.pos){L(Z.pos,w);break}}else if(Y.ltype===2){let O=null,H=C();if(H!==-1){const B=n._lctf.coverageIndex(Z.coverage,x[H]);if(B!==-1){if(Z.fmt===1){const V=Z.pairsets[B];for(let G=0;G<V.length;G++)V[G].gid2===U&&(O=V[G])}else if(Z.fmt===2){const V=n.U._getGlyphClass(x[H],Z.classDef1),G=n.U._getGlyphClass(U,Z.classDef2);O=Z.matrix[V][G]}if(O){O.val1&&L(O.val1,H),O.val2&&L(O.val2,w);break}}}}else if(Y.ltype===4){const O=n._lctf.coverageIndex(Z.markCoverage,U);if(O!==-1){const H=C(R),B=H===-1?-1:n._lctf.coverageIndex(Z.baseCoverage,x[H]);if(B!==-1){const V=Z.markArray[O],G=Z.baseArray[B][V.markClass];y[w*3]=G.x-V.x+y[H*3]-y[H*3+2],y[w*3+1]=G.y-V.y+y[H*3+1];break}}}else if(Y.ltype===6){const O=n._lctf.coverageIndex(Z.mark1Coverage,U);if(O!==-1){const H=C();if(H!==-1){const B=x[H];if(S(T,B)===3){const V=n._lctf.coverageIndex(Z.mark2Coverage,B);if(V!==-1){const G=Z.mark1Array[O],z=Z.mark2Array[V][G.markClass];y[w*3]=z.x-G.x+y[H*3]-y[H*3+2],y[w*3+1]=z.y-G.y+y[H*3+1];break}}}}}}}}else if(T.kern&&!T.cff){const F=C();if(F!==-1){const N=T.kern.glyph1.indexOf(x[F]);if(N!==-1){const Y=T.kern.rval[N].glyph2.indexOf(U);Y!==-1&&(y[F*3+2]+=T.kern.rval[N].vals[Y])}}}}return y;function C(U){for(let I=w-1;I>=0;I--)if(x[I]!==-1&&(!U||U(x[I])))return I;return-1}function R(U){return S(T,U)===1}function L(U,I){for(let F=0;F<3;F++)y[I*3+F]+=U[F]||0}}function S(T,x){const y=T.GDEF&&T.GDEF.glyphClassDef;return y?n.U._getGlyphClass(x,y):0}function E(...T){for(let x=0;x<T.length;x++)if(typeof T[x]=="number")return T[x]}function M(T){const x=Object.create(null),y=T["OS/2"],w=T.hhea,C=T.head.unitsPerEm,R=E(y&&y.sTypoAscender,w&&w.ascender,C),L={unitsPerEm:C,ascender:R,descender:E(y&&y.sTypoDescender,w&&w.descender,0),capHeight:E(y&&y.sCapHeight,R),xHeight:E(y&&y.sxHeight,R),lineGap:E(y&&y.sTypoLineGap,w&&w.lineGap),supportsCodePoint(U){return n.U.codeToGlyph(T,U)>0},forEachGlyph(U,I,F,N){let Y=0;const j=1/L.unitsPerEm*I,Z=v(T,U);let O=0;const H=b(T,Z);return Z.forEach((B,V)=>{if(B!==-1){let G=x[B];if(!G){const{cmds:z,crds:W}=n.U.glyphToPath(T,B);let q="",ce=0;for(let De=0,ye=z.length;De<ye;De++){const _e=t[z[De]];q+=z[De];for(let Ne=1;Ne<=_e;Ne++)q+=(Ne>1?",":"")+W[ce++]}let me,Q,ie,be;if(W.length){me=Q=1/0,ie=be=-1/0;for(let De=0,ye=W.length;De<ye;De+=2){let _e=W[De],Ne=W[De+1];_e<me&&(me=_e),Ne<Q&&(Q=Ne),_e>ie&&(ie=_e),Ne>be&&(be=Ne)}}else me=ie=Q=be=0;G=x[B]={index:B,advanceWidth:T.hmtx.aWidth[B],xMin:me,yMin:Q,xMax:ie,yMax:be,path:q}}N.call(null,G,Y+H[V*3]*j,H[V*3+1]*j,O),Y+=H[V*3+2]*j,F&&(Y+=F*I)}O+=U.codePointAt(O)>65535?2:1}),Y}};return L}return function(x){const y=new Uint8Array(x,0,4),w=n._bin.readASCII(y,0,4);if(w==="wOFF")x=e(x);else if(w==="wOF2")throw new Error("woff2 fonts not supported");return M(n.parse(x)[0])}}const lS=ea({name:"Typr Font Parser",dependencies:[sS,aS,oS],init(n,e,t){const i=n(),r=e();return t(i,r)}});/*!
Custom bundle of @unicode-font-resolver/client v1.0.2 (https://github.com/lojjic/unicode-font-resolver)
for use in Troika text rendering. 
Original MIT license applies
*/function cS(){return(function(n){var e=function(){this.buckets=new Map};e.prototype.add=function(b){var S=b>>5;this.buckets.set(S,(this.buckets.get(S)||0)|1<<(31&b))},e.prototype.has=function(b){var S=this.buckets.get(b>>5);return S!==void 0&&(S&1<<(31&b))!=0},e.prototype.serialize=function(){var b=[];return this.buckets.forEach((function(S,E){b.push((+E).toString(36)+":"+S.toString(36))})),b.join(",")},e.prototype.deserialize=function(b){var S=this;this.buckets.clear(),b.split(",").forEach((function(E){var M=E.split(":");S.buckets.set(parseInt(M[0],36),parseInt(M[1],36))}))};var t=Math.pow(2,8),i=t-1,r=~i;function s(b){var S=(function(M){return M&r})(b).toString(16),E=(function(M){return(M&r)+t-1})(b).toString(16);return"codepoint-index/plane"+(b>>16)+"/"+S+"-"+E+".json"}function a(b,S){var E=b&i,M=S.codePointAt(E/6|0);return((M=(M||48)-48)&1<<E%6)!=0}function o(b,S){var E;(E=b,E.replace(/U\+/gi,"").replace(/^,+|,+$/g,"").split(/,+/).map((function(M){return M.split("-").map((function(T){return parseInt(T.trim(),16)}))}))).forEach((function(M){var T=M[0],x=M[1];x===void 0&&(x=T),S(T,x)}))}function l(b,S){o(b,(function(E,M){for(var T=E;T<=M;T++)S(T)}))}var c={},u={},f=new WeakMap,h="https://cdn.jsdelivr.net/gh/lojjic/unicode-font-resolver@v1.0.1/packages/data";function d(b){var S=f.get(b);return S||(S=new e,l(b.ranges,(function(E){return S.add(E)})),f.set(b,S)),S}var m,g=new Map;function p(b,S,E){return b[S]?S:b[E]?E:(function(M){for(var T in M)return T})(b)}function _(b,S){var E=S;if(!b.includes(E)){E=1/0;for(var M=0;M<b.length;M++)Math.abs(b[M]-S)<Math.abs(E-S)&&(E=b[M])}return E}function v(b){return m||(m=new Set,l("9-D,20,85,A0,1680,2000-200A,2028-202F,205F,3000",(function(S){m.add(S)}))),m.has(b)}return n.CodePointSet=e,n.clearCache=function(){c={},u={}},n.getFontsForString=function(b,S){S===void 0&&(S={});var E,M=S.lang;M===void 0&&(M=new RegExp("\\p{Script=Hangul}","u").test(E=b)?"ko":new RegExp("\\p{Script=Hiragana}|\\p{Script=Katakana}","u").test(E)?"ja":"en");var T=S.category;T===void 0&&(T="sans-serif");var x=S.style;x===void 0&&(x="normal");var y=S.weight;y===void 0&&(y=400);var w=(S.dataUrl||h).replace(/\/$/g,""),C=new Map,R=new Uint8Array(b.length),L={},U={},I=new Array(b.length),F=new Map,N=!1;function Y(O){var H=g.get(O);return H||(H=fetch(w+"/"+O).then((function(B){if(!B.ok)throw new Error(B.statusText);return B.json().then((function(V){if(!Array.isArray(V)||V[0]!==1)throw new Error("Incorrect schema version; need 1, got "+V[0]);return V[1]}))})).catch((function(B){if(w!==h)return N||(console.error('unicode-font-resolver: Failed loading from dataUrl "'+w+'", trying default CDN. '+B.message),N=!0),w=h,g.delete(O),Y(O);throw B})),g.set(O,H)),H}for(var j=function(O){var H=b.codePointAt(O),B=s(H);I[O]=B,c[B]||F.has(B)||F.set(B,Y(B).then((function(V){c[B]=V}))),H>65535&&(O++,Z=O)},Z=0;Z<b.length;Z++)j(Z);return Promise.all(F.values()).then((function(){F.clear();for(var O=function(B){var V=b.codePointAt(B),G=null,z=c[I[B]],W=void 0;for(var q in z){var ce=U[q];if(ce===void 0&&(ce=U[q]=new RegExp(q).test(M||"en")),ce){for(var me in W=q,z[q])if(a(V,z[q][me])){G=me;break}break}}if(!G){e:for(var Q in z)if(Q!==W){for(var ie in z[Q])if(a(V,z[Q][ie])){G=ie;break e}}}G||(console.debug("No font coverage for U+"+V.toString(16)),G="latin"),I[B]=G,u[G]||F.has(G)||F.set(G,Y("font-meta/"+G+".json").then((function(be){u[G]=be}))),V>65535&&(B++,H=B)},H=0;H<b.length;H++)O(H);return Promise.all(F.values())})).then((function(){for(var O,H=null,B=0;B<b.length;B++){var V=b.codePointAt(B);if(H&&(v(V)||d(H).has(V)))R[B]=R[B-1];else{H=u[I[B]];var G=L[H.id];if(!G){var z=H.typeforms,W=p(z,T,"sans-serif"),q=p(z[W],x,"normal"),ce=_((O=z[W])===null||O===void 0?void 0:O[q],y);G=L[H.id]=w+"/font-files/"+H.id+"/"+W+"."+q+"."+ce+".woff"}var me=C.get(G);me==null&&(me=C.size,C.set(G,me)),R[B]=me}V>65535&&(B++,R[B]=R[B-1])}return{fontUrls:Array.from(C.keys()),chars:R}}))},Object.defineProperty(n,"__esModule",{value:!0}),n})({})}function uS(n,e){const t=Object.create(null),i=Object.create(null);function r(a,o){const l=c=>{console.error(`Failure loading font ${a}`,c)};try{const c=new XMLHttpRequest;c.open("get",a,!0),c.responseType="arraybuffer",c.onload=function(){if(c.status>=400)l(new Error(c.statusText));else if(c.status>0)try{const u=n(c.response);u.src=a,o(u)}catch(u){l(u)}},c.onerror=l,c.send()}catch(c){l(c)}}function s(a,o){let l=t[a];l?o(l):i[a]?i[a].push(o):(i[a]=[o],r(a,c=>{c.src=a,t[a]=c,i[a].forEach(u=>u(c)),delete i[a]}))}return function(a,o,{lang:l,fonts:c=[],style:u="normal",weight:f="normal",unicodeFontsURL:h}={}){const d=new Uint8Array(a.length),m=[];a.length||v();const g=new Map,p=[];if(u!=="italic"&&(u="normal"),typeof f!="number"&&(f=f==="bold"?700:400),c&&!Array.isArray(c)&&(c=[c]),c=c.slice().filter(S=>!S.lang||S.lang.test(l)).reverse(),c.length){let T=0;(function x(y=0){for(let w=y,C=a.length;w<C;w++){const R=a.codePointAt(w);if(T===1&&m[d[w-1]].supportsCodePoint(R)||w>0&&/\s/.test(a[w]))d[w]=d[w-1],T===2&&(p[p.length-1][1]=w);else for(let L=d[w],U=c.length;L<=U;L++)if(L===U){const I=T===2?p[p.length-1]:p[p.length]=[w,w];I[1]=w,T=2}else{d[w]=L;const{src:I,unicodeRange:F}=c[L];if(!F||b(R,F)){const N=t[I];if(!N){s(I,()=>{x(w)});return}if(N.supportsCodePoint(R)){let Y=g.get(N);typeof Y!="number"&&(Y=m.length,m.push(N),g.set(N,Y)),d[w]=Y,T=1;break}}}R>65535&&w+1<C&&(d[w+1]=d[w],w++,T===2&&(p[p.length-1][1]=w))}_()})()}else p.push([0,a.length-1]),_();function _(){if(p.length){const S=p.map(E=>a.substring(E[0],E[1]+1)).join(`
`);e.getFontsForString(S,{lang:l||void 0,style:u,weight:f,dataUrl:h}).then(({fontUrls:E,chars:M})=>{const T=m.length;let x=0;p.forEach(w=>{for(let C=0,R=w[1]-w[0];C<=R;C++)d[w[0]+C]=M[x++]+T;x++});let y=0;E.forEach((w,C)=>{s(w,R=>{m[C+T]=R,++y===E.length&&v()})})})}else v()}function v(){o({chars:d,fonts:m})}function b(S,E){for(let M=0;M<E.length;M++){const[T,x=T]=E[M];if(T<=S&&S<=x)return!0}return!1}}}const hS=ea({name:"FontResolver",dependencies:[uS,lS,cS],init(n,e,t){return n(e,t())}});function fS(n,e){const i=/[\u00AD\u034F\u061C\u115F-\u1160\u17B4-\u17B5\u180B-\u180E\u200B-\u200F\u202A-\u202E\u2060-\u206F\u3164\uFE00-\uFE0F\uFEFF\uFFA0\uFFF0-\uFFF8]/,r="[^\\S\\u00A0]",s=new RegExp(`${r}|[\\-\\u007C\\u00AD\\u2010\\u2012-\\u2014\\u2027\\u2056\\u2E17\\u2E40]`);function a({text:m,lang:g,fonts:p,style:_,weight:v,preResolvedFonts:b,unicodeFontsURL:S},E){const M=({chars:T,fonts:x})=>{let y,w;const C=[];for(let R=0;R<T.length;R++)T[R]!==w?(w=T[R],C.push(y={start:R,end:R,fontObj:x[T[R]]})):y.end=R;E(C)};b?M(b):n(m,M,{lang:g,fonts:p,style:_,weight:v,unicodeFontsURL:S})}function o({text:m="",font:g,lang:p,sdfGlyphSize:_=64,fontSize:v=400,fontWeight:b=1,fontStyle:S="normal",letterSpacing:E=0,lineHeight:M="normal",maxWidth:T=1/0,direction:x,textAlign:y="left",textIndent:w=0,whiteSpace:C="normal",overflowWrap:R="normal",anchorX:L=0,anchorY:U=0,metricsOnly:I=!1,unicodeFontsURL:F,preResolvedFonts:N=null,includeCaretPositions:Y=!1,chunkedBoundsSize:j=8192,colorRanges:Z=null},O){const H=f(),B={fontLoad:0,typesetting:0};m.indexOf("\r")>-1&&(console.info("Typesetter: got text with \\r chars; normalizing to \\n"),m=m.replace(/\r\n/g,`
`).replace(/\r/g,`
`)),v=+v,E=+E,T=+T,M=M||"normal",w=+w,a({text:m,lang:p,style:S,weight:b,fonts:typeof g=="string"?[{src:g}]:g,unicodeFontsURL:F,preResolvedFonts:N},V=>{B.fontLoad=f()-H;const G=isFinite(T);let z=null,W=null,q=null,ce=null,me=null,Q=null,ie=null,be=null,De=0,ye=0,_e=C!=="nowrap";const Ne=new Map,ae=f();let Ee=w,k=0,de=new h;const Pe=[de];V.forEach(A=>{const{fontObj:X}=A,{ascender:ee,descender:he,unitsPerEm:xe,lineGap:Te,capHeight:te,xHeight:le}=X;let ge=Ne.get(X);if(!ge){const Fe=v/xe,Ye=M==="normal"?(ee-he+Te)*Fe:M*v,K=(Ye-(ee-he)*Fe)/2,ve=Math.min(Ye,(ee-he)*Fe),oe=(ee+he)/2*Fe+ve/2;ge={index:Ne.size,src:X.src,fontObj:X,fontSizeMult:Fe,unitsPerEm:xe,ascender:ee*Fe,descender:he*Fe,capHeight:te*Fe,xHeight:le*Fe,lineHeight:Ye,baseline:-K-ee*Fe,caretTop:oe,caretBottom:oe-ve},Ne.set(X,ge)}const{fontSizeMult:Ie}=ge,Me=m.slice(A.start,A.end+1);let Ae,He;X.forEachGlyph(Me,v,E,(Fe,Ye,K,ve)=>{Ye+=k,ve+=A.start,Ae=Ye,He=Fe;const oe=m.charAt(ve),Le=Fe.advanceWidth*Ie,Se=de.count;let fe;if("isEmpty"in Fe||(Fe.isWhitespace=!!oe&&new RegExp(r).test(oe),Fe.canBreakAfter=!!oe&&s.test(oe),Fe.isEmpty=Fe.xMin===Fe.xMax||Fe.yMin===Fe.yMax||i.test(oe)),!Fe.isWhitespace&&!Fe.isEmpty&&ye++,_e&&G&&!Fe.isWhitespace&&Ye+Le+Ee>T&&Se){if(de.glyphAt(Se-1).glyphObj.canBreakAfter)fe=new h,Ee=-Ye;else for(let $e=Se;$e--;)if($e===0&&R==="break-word"){fe=new h,Ee=-Ye;break}else if(de.glyphAt($e).glyphObj.canBreakAfter){fe=de.splitAt($e+1);const ot=fe.glyphAt(0).x;Ee-=ot;for(let tt=fe.count;tt--;)fe.glyphAt(tt).x-=ot;break}fe&&(de.isSoftWrapped=!0,de=fe,Pe.push(de),De=T)}let Oe=de.glyphAt(de.count);Oe.glyphObj=Fe,Oe.x=Ye+Ee,Oe.y=K,Oe.width=Le,Oe.charIndex=ve,Oe.fontData=ge,oe===`
`&&(de=new h,Pe.push(de),Ee=-(Ye+Le+E*v)+w)}),k=Ae+He.advanceWidth*Ie+E*v});let we=0;Pe.forEach(A=>{let X=!0;for(let ee=A.count;ee--;){const he=A.glyphAt(ee);X&&!he.glyphObj.isWhitespace&&(A.width=he.x+he.width,A.width>De&&(De=A.width),X=!1);let{lineHeight:xe,capHeight:Te,xHeight:te,baseline:le}=he.fontData;xe>A.lineHeight&&(A.lineHeight=xe);const ge=le-A.baseline;ge<0&&(A.baseline+=ge,A.cap+=ge,A.ex+=ge),A.cap=Math.max(A.cap,A.baseline+Te),A.ex=Math.max(A.ex,A.baseline+te)}A.baseline-=we,A.cap-=we,A.ex-=we,we+=A.lineHeight});let pe=0,Re=0;if(L&&(typeof L=="number"?pe=-L:typeof L=="string"&&(pe=-De*(L==="left"?0:L==="center"?.5:L==="right"?1:c(L)))),U&&(typeof U=="number"?Re=-U:typeof U=="string"&&(Re=U==="top"?0:U==="top-baseline"?-Pe[0].baseline:U==="top-cap"?-Pe[0].cap:U==="top-ex"?-Pe[0].ex:U==="middle"?we/2:U==="bottom"?we:U==="bottom-baseline"?-Pe[Pe.length-1].baseline:c(U)*we)),!I){const A=e.getEmbeddingLevels(m,x);z=new Uint16Array(ye),W=new Uint8Array(ye),q=new Float32Array(ye*2),ce={},ie=[1/0,1/0,-1/0,-1/0],be=[],Y&&(Q=new Float32Array(m.length*4)),Z&&(me=new Uint8Array(ye*3));let X=0,ee=-1,he=-1,xe,Te;if(Pe.forEach((te,le)=>{let{count:ge,width:Ie}=te;if(ge>0){let Me=0;for(let ve=ge;ve--&&te.glyphAt(ve).glyphObj.isWhitespace;)Me++;let Ae=0,He=0;if(y==="center")Ae=(De-Ie)/2;else if(y==="right")Ae=De-Ie;else if(y==="justify"&&te.isSoftWrapped){let ve=0;for(let oe=ge-Me;oe--;)te.glyphAt(oe).glyphObj.isWhitespace&&ve++;He=(De-Ie)/ve}if(He||Ae){let ve=0;for(let oe=0;oe<ge;oe++){let Le=te.glyphAt(oe);const Se=Le.glyphObj;Le.x+=Ae+ve,He!==0&&Se.isWhitespace&&oe<ge-Me&&(ve+=He,Le.width+=He)}}const Fe=e.getReorderSegments(m,A,te.glyphAt(0).charIndex,te.glyphAt(te.count-1).charIndex);for(let ve=0;ve<Fe.length;ve++){const[oe,Le]=Fe[ve];let Se=1/0,fe=-1/0;for(let Oe=0;Oe<ge;Oe++)if(te.glyphAt(Oe).charIndex>=oe){let $e=Oe,ot=Oe;for(;ot<ge;ot++){let tt=te.glyphAt(ot);if(tt.charIndex>Le)break;ot<ge-Me&&(Se=Math.min(Se,tt.x),fe=Math.max(fe,tt.x+tt.width))}for(let tt=$e;tt<ot;tt++){const Vt=te.glyphAt(tt);Vt.x=fe-(Vt.x+Vt.width-Se)}break}}let Ye;const K=ve=>Ye=ve;for(let ve=0;ve<ge;ve++){const oe=te.glyphAt(ve);Ye=oe.glyphObj;const Le=Ye.index,Se=A.levels[oe.charIndex]&1;if(Se){const fe=e.getMirroredCharacter(m[oe.charIndex]);fe&&oe.fontData.fontObj.forEachGlyph(fe,0,0,K)}if(Y){const{charIndex:fe,fontData:Oe}=oe,$e=oe.x+pe,ot=oe.x+oe.width+pe;Q[fe*4]=Se?ot:$e,Q[fe*4+1]=Se?$e:ot,Q[fe*4+2]=te.baseline+Oe.caretBottom+Re,Q[fe*4+3]=te.baseline+Oe.caretTop+Re;const tt=fe-ee;tt>1&&u(Q,ee,tt),ee=fe}if(Z){const{charIndex:fe}=oe;for(;fe>he;)he++,Z.hasOwnProperty(he)&&(Te=Z[he])}if(!Ye.isWhitespace&&!Ye.isEmpty){const fe=X++,{fontSizeMult:Oe,src:$e,index:ot}=oe.fontData,tt=ce[$e]||(ce[$e]={});tt[Le]||(tt[Le]={path:Ye.path,pathBounds:[Ye.xMin,Ye.yMin,Ye.xMax,Ye.yMax]});const Vt=oe.x+pe,Kt=oe.y+te.baseline+Re;q[fe*2]=Vt,q[fe*2+1]=Kt;const In=Vt+Ye.xMin*Oe,_i=Kt+Ye.yMin*Oe,vi=Vt+Ye.xMax*Oe,Zn=Kt+Ye.yMax*Oe;In<ie[0]&&(ie[0]=In),_i<ie[1]&&(ie[1]=_i),vi>ie[2]&&(ie[2]=vi),Zn>ie[3]&&(ie[3]=Zn),fe%j===0&&(xe={start:fe,end:fe,rect:[1/0,1/0,-1/0,-1/0]},be.push(xe)),xe.end++;const Ft=xe.rect;if(In<Ft[0]&&(Ft[0]=In),_i<Ft[1]&&(Ft[1]=_i),vi>Ft[2]&&(Ft[2]=vi),Zn>Ft[3]&&(Ft[3]=Zn),z[fe]=Le,W[fe]=ot,Z){const ri=fe*3;me[ri]=Te>>16&255,me[ri+1]=Te>>8&255,me[ri+2]=Te&255}}}}}),Q){const te=m.length-ee;te>1&&u(Q,ee,te)}}const D=[];Ne.forEach(({index:A,src:X,unitsPerEm:ee,ascender:he,descender:xe,lineHeight:Te,capHeight:te,xHeight:le})=>{D[A]={src:X,unitsPerEm:ee,ascender:he,descender:xe,lineHeight:Te,capHeight:te,xHeight:le}}),B.typesetting=f()-ae,O({glyphIds:z,glyphFontIndices:W,glyphPositions:q,glyphData:ce,fontData:D,caretPositions:Q,glyphColors:me,chunkedBounds:be,fontSize:v,topBaseline:Re+Pe[0].baseline,blockBounds:[pe,Re-we,pe+De,Re],visibleBounds:ie,timings:B})})}function l(m,g){o({...m,metricsOnly:!0},p=>{const[_,v,b,S]=p.blockBounds;g({width:b-_,height:S-v})})}function c(m){let g=m.match(/^([\d.]+)%$/),p=g?parseFloat(g[1]):NaN;return isNaN(p)?0:p/100}function u(m,g,p){const _=m[g*4],v=m[g*4+1],b=m[g*4+2],S=m[g*4+3],E=(v-_)/p;for(let M=0;M<p;M++){const T=(g+M)*4;m[T]=_+E*M,m[T+1]=_+E*(M+1),m[T+2]=b,m[T+3]=S}}function f(){return(self.performance||Date).now()}function h(){this.data=[]}const d=["glyphObj","x","y","width","charIndex","fontData"];return h.prototype={width:0,lineHeight:0,baseline:0,cap:0,ex:0,isSoftWrapped:!1,get count(){return Math.ceil(this.data.length/d.length)},glyphAt(m){let g=h.flyweight;return g.data=this.data,g.index=m,g},splitAt(m){let g=new h;return g.data=this.data.splice(m*d.length),g}},h.flyweight=d.reduce((m,g,p,_)=>(Object.defineProperty(m,g,{get(){return this.data[this.index*d.length+p]},set(v){this.data[this.index*d.length+p]=v}}),m),{data:null,index:0}),{typeset:o,measure:l}}const Wr=()=>(self.performance||Date).now(),Bl=u0();let pp;function dS(n,e,t,i,r,s,a,o,l,c,u=!0){return u?mS(n,e,t,i,r,s,a,o,l,c).then(null,f=>(pp||(console.warn("WebGL SDF generation failed, falling back to JS",f),pp=!0),gp(n,e,t,i,r,s,a,o,l,c))):gp(n,e,t,i,r,s,a,o,l,c)}const il=[],pS=5;let Eh=0;function f0(){const n=Wr();for(;il.length&&Wr()-n<pS;)il.shift()();Eh=il.length?setTimeout(f0,0):0}const mS=(...n)=>new Promise((e,t)=>{il.push(()=>{const i=Wr();try{Bl.webgl.generateIntoCanvas(...n),e({timing:Wr()-i})}catch(r){t(r)}}),Eh||(Eh=setTimeout(f0,0))}),gS=4,_S=2e3,mp={};let vS=0;function gp(n,e,t,i,r,s,a,o,l,c){const u="TroikaTextSDFGenerator_JS_"+vS++%gS;let f=mp[u];return f||(f=mp[u]={workerModule:ea({name:u,workerId:u,dependencies:[u0,Wr],init(h,d){const m=h().javascript.generate;return function(...g){const p=d();return{textureData:m(...g),timing:d()-p}}},getTransferables(h){return[h.textureData.buffer]}}),requests:0,idleTimer:null}),f.requests++,clearTimeout(f.idleTimer),f.workerModule(n,e,t,i,r,s).then(({textureData:h,timing:d})=>{const m=Wr(),g=new Uint8Array(h.length*4);for(let p=0;p<h.length;p++)g[p*4+c]=h[p];return Bl.webglUtils.renderImageData(a,g,o,l,n,e,1<<3-c),d+=Wr()-m,--f.requests===0&&(f.idleTimer=setTimeout(()=>{KM(u)},_S)),{timing:d}})}function xS(n){n._warm||(Bl.webgl.isSupported(n),n._warm=!0)}const yS=Bl.webglUtils.resizeWebGLCanvasWithoutClearing,Da={unicodeFontsURL:null,sdfGlyphSize:64,sdfMargin:1/16,sdfExponent:9,textureWidth:2048},bS=new ut;function As(){return(self.performance||Date).now()}const _p=Object.create(null);function MS(n,e){n=TS({},n);const t=As(),i=[];if(n.font&&i.push({label:"user",src:ES(n.font)}),n.font=i,n.text=""+n.text,n.sdfGlyphSize=n.sdfGlyphSize||Da.sdfGlyphSize,n.unicodeFontsURL=n.unicodeFontsURL||Da.unicodeFontsURL,n.colorRanges!=null){let h={};for(let d in n.colorRanges)if(n.colorRanges.hasOwnProperty(d)){let m=n.colorRanges[d];typeof m!="number"&&(m=bS.set(m).getHex()),h[d]=m}n.colorRanges=h}Object.freeze(n);const{textureWidth:r,sdfExponent:s}=Da,{sdfGlyphSize:a}=n,o=r/a*4;let l=_p[a];if(!l){const h=document.createElement("canvas");h.width=r,h.height=a*256/o,l=_p[a]={glyphCount:0,sdfGlyphSize:a,sdfCanvas:h,sdfTexture:new Jt(h,void 0,void 0,void 0,Gt,Gt),contextLost:!1,glyphsByFont:new Map},l.sdfTexture.generateMipmaps=!1,SS(l)}const{sdfTexture:c,sdfCanvas:u}=l;m0(n).then(h=>{const{glyphIds:d,glyphFontIndices:m,fontData:g,glyphPositions:p,fontSize:_,timings:v}=h,b=[],S=new Float32Array(d.length*4);let E=0,M=0;const T=As(),x=g.map(L=>{let U=l.glyphsByFont.get(L.src);return U||l.glyphsByFont.set(L.src,U=new Map),U});d.forEach((L,U)=>{const I=m[U],{src:F,unitsPerEm:N}=g[I];let Y=x[I].get(L);if(!Y){const{path:B,pathBounds:V}=h.glyphData[F][L],G=Math.max(V[2]-V[0],V[3]-V[1])/a*(Da.sdfMargin*a+.5),z=l.glyphCount++,W=[V[0]-G,V[1]-G,V[2]+G,V[3]+G];x[I].set(L,Y={path:B,atlasIndex:z,sdfViewBox:W}),b.push(Y)}const{sdfViewBox:j}=Y,Z=p[M++],O=p[M++],H=_/N;S[E++]=Z+j[0]*H,S[E++]=O+j[1]*H,S[E++]=Z+j[2]*H,S[E++]=O+j[3]*H,d[U]=Y.atlasIndex}),v.quads=(v.quads||0)+(As()-T);const y=As();v.sdf={};const w=u.height,C=Math.ceil(l.glyphCount/o),R=Math.pow(2,Math.ceil(Math.log2(C*a)));R>w&&(console.info(`Increasing SDF texture size ${w}->${R}`),yS(u,r,R),c.dispose()),Promise.all(b.map(L=>d0(L,l,n.gpuAccelerateSDF).then(({timing:U})=>{v.sdf[L.atlasIndex]=U}))).then(()=>{b.length&&!l.contextLost&&(p0(l),c.needsUpdate=!0),v.sdfTotal=As()-y,v.total=As()-t,e(Object.freeze({parameters:n,sdfTexture:c,sdfGlyphSize:a,sdfExponent:s,glyphBounds:S,glyphAtlasIndices:d,glyphColors:h.glyphColors,caretPositions:h.caretPositions,chunkedBounds:h.chunkedBounds,ascender:h.ascender,descender:h.descender,lineHeight:h.lineHeight,capHeight:h.capHeight,xHeight:h.xHeight,topBaseline:h.topBaseline,blockBounds:h.blockBounds,visibleBounds:h.visibleBounds,timings:h.timings}))})}),Promise.resolve().then(()=>{l.contextLost||xS(u)})}function d0({path:n,atlasIndex:e,sdfViewBox:t},{sdfGlyphSize:i,sdfCanvas:r,contextLost:s},a){if(s)return Promise.resolve({timing:-1});const{textureWidth:o,sdfExponent:l}=Da,c=Math.max(t[2]-t[0],t[3]-t[1]),u=Math.floor(e/4),f=u%(o/i)*i,h=Math.floor(u/(o/i))*i,d=e%4;return dS(i,i,n,t,c,l,r,f,h,d,a)}function SS(n){const e=n.sdfCanvas;e.addEventListener("webglcontextlost",t=>{console.log("Context Lost",t),t.preventDefault(),n.contextLost=!0}),e.addEventListener("webglcontextrestored",t=>{console.log("Context Restored",t),n.contextLost=!1;const i=[];n.glyphsByFont.forEach(r=>{r.forEach(s=>{i.push(d0(s,n,!0))})}),Promise.all(i).then(()=>{p0(n),n.sdfTexture.needsUpdate=!0})})}function TS(n,e){for(let t in e)e.hasOwnProperty(t)&&(n[t]=e[t]);return n}let Go;function ES(n){return Go||(Go=typeof document>"u"?{}:document.createElement("a")),Go.href=n,Go.href}function p0(n){if(typeof createImageBitmap!="function"){console.info("Safari<15: applying SDF canvas workaround");const{sdfCanvas:e,sdfTexture:t}=n,{width:i,height:r}=e,s=n.sdfCanvas.getContext("webgl");let a=t.image.data;(!a||a.length!==i*r*4)&&(a=new Uint8Array(i*r*4),t.image={width:i,height:r,data:a},t.flipY=!1,t.isDataTexture=!0),s.readPixels(0,0,i,r,s.RGBA,s.UNSIGNED_BYTE,a)}}const wS=ea({name:"Typesetter",dependencies:[fS,hS,$M],init(n,e,t){return n(e,t())}}),m0=ea({name:"Typesetter",dependencies:[wS],init(n){return function(e){return new Promise(t=>{n.typeset(e,t)})}},getTransferables(n){const e=[];for(let t in n)n[t]&&n[t].buffer&&e.push(n[t].buffer);return e}});m0.onMainThread;const vp={};function AS(n){let e=vp[n];return e||(e=vp[n]=new es(1,1,n,n).translate(.5,.5,0)),e}const RS="aTroikaGlyphBounds",xp="aTroikaGlyphIndex",CS="aTroikaGlyphColor";class PS extends Wv{constructor(){super(),this.detail=1,this.curveRadius=0,this.groups=[{start:0,count:1/0,materialIndex:0},{start:0,count:1/0,materialIndex:1}],this.boundingSphere=new Js,this.boundingBox=new $s}computeBoundingSphere(){}computeBoundingBox(){}set detail(e){if(e!==this._detail){this._detail=e,(typeof e!="number"||e<1)&&(e=1);let t=AS(e);["position","normal","uv"].forEach(i=>{this.attributes[i]=t.attributes[i].clone()}),this.setIndex(t.getIndex().clone())}}get detail(){return this._detail}set curveRadius(e){e!==this._curveRadius&&(this._curveRadius=e,this._updateBounds())}get curveRadius(){return this._curveRadius}updateGlyphs(e,t,i,r,s){this.updateAttributeData(RS,e,4),this.updateAttributeData(xp,t,1),this.updateAttributeData(CS,s,3),this._blockBounds=i,this._chunkedBounds=r,this.instanceCount=t.length,this._updateBounds()}_updateBounds(){const e=this._blockBounds;if(e){const{curveRadius:t,boundingBox:i}=this;if(t){const{PI:r,floor:s,min:a,max:o,sin:l,cos:c}=Math,u=r/2,f=r*2,h=Math.abs(t),d=e[0]/h,m=e[2]/h,g=s((d+u)/f)!==s((m+u)/f)?-h:a(l(d)*h,l(m)*h),p=s((d-u)/f)!==s((m-u)/f)?h:o(l(d)*h,l(m)*h),_=s((d+r)/f)!==s((m+r)/f)?h*2:o(h-c(d)*h,h-c(m)*h);i.min.set(g,e[1],t<0?-_:0),i.max.set(p,e[3],t<0?0:_)}else i.min.set(e[0],e[1],0),i.max.set(e[2],e[3],0);i.getBoundingSphere(this.boundingSphere)}}applyClipRect(e){let t=this.getAttribute(xp).count,i=this._chunkedBounds;if(i)for(let r=i.length;r--;){t=i[r].end;let s=i[r].rect;if(s[1]<e.w&&s[3]>e.y&&s[0]<e.z&&s[2]>e.x)break}this.instanceCount=t}updateAttributeData(e,t,i){const r=this.getAttribute(e);t?r&&r.array.length===t.length?(r.array.set(t),r.needsUpdate=!0):(this.setAttribute(e,new Uv(t,i)),delete this._maxInstanceCount,this.dispose()):r&&this.deleteAttribute(e)}}const DS=`
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
`,US=`
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
`,LS=`
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
`,IS=`
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
`;function FS(n){const e=Th(n,{chained:!0,extensions:{derivatives:!0},uniforms:{uTroikaSDFTexture:{value:null},uTroikaSDFTextureSize:{value:new Xe},uTroikaSDFGlyphSize:{value:0},uTroikaSDFExponent:{value:0},uTroikaTotalBounds:{value:new Ut(0,0,0,0)},uTroikaClipRect:{value:new Ut(0,0,0,0)},uTroikaEdgeOffset:{value:0},uTroikaFillOpacity:{value:1},uTroikaPositionOffset:{value:new Xe},uTroikaCurveRadius:{value:0},uTroikaBlurRadius:{value:0},uTroikaStrokeWidth:{value:0},uTroikaStrokeColor:{value:new ut},uTroikaStrokeOpacity:{value:1},uTroikaOrient:{value:new rt},uTroikaUseGlyphColors:{value:!0},uTroikaSDFDebug:{value:!1}},vertexDefs:DS,vertexTransform:US,fragmentDefs:LS,fragmentColorTransform:IS,customRewriter({vertexShader:t,fragmentShader:i}){let r=/\buniform\s+vec3\s+diffuse\b/;return r.test(i)&&(i=i.replace(r,"varying vec3 vTroikaGlyphColor").replace(/\bdiffuse\b/g,"vTroikaGlyphColor"),r.test(t)||(t=t.replace(h0,`uniform vec3 diffuse;
$&
vTroikaGlyphColor = uTroikaUseGlyphColors ? aTroikaGlyphColor / 255.0 : diffuse;
`))),{vertexShader:t,fragmentShader:i}}});return e.transparent=!0,e.forceSinglePass=!0,Object.defineProperties(e,{isTroikaTextMaterial:{value:!0},shadowSide:{get(){return this.side},set(){}}}),e}const of=new sf({color:16777215,side:An,transparent:!0}),yp=8421504,bp=new zt,Ho=new $,Wc=new $,Ea=[],NS=new $,Xc="+x+y";function Mp(n){return Array.isArray(n)?n[0]:n}let g0=()=>{const n=new Yn(new es(1,1),of);return g0=()=>n,n},_0=()=>{const n=new Yn(new es(1,1,32,1),of);return _0=()=>n,n};const OS={type:"syncstart"},BS={type:"synccomplete"},v0=["font","fontSize","fontStyle","fontWeight","lang","letterSpacing","lineHeight","maxWidth","overflowWrap","text","direction","textAlign","textIndent","whiteSpace","anchorX","anchorY","colorRanges","sdfGlyphSize"],kS=v0.concat("material","color","depthOffset","clipRect","curveRadius","orientation","glyphGeometryDetail");class wh extends Yn{constructor(){const e=new PS;super(e,null),this.text="",this.anchorX=0,this.anchorY=0,this.curveRadius=0,this.direction="auto",this.font=null,this.unicodeFontsURL=null,this.fontSize=.1,this.fontWeight="normal",this.fontStyle="normal",this.lang=null,this.letterSpacing=0,this.lineHeight="normal",this.maxWidth=1/0,this.overflowWrap="normal",this.textAlign="left",this.textIndent=0,this.whiteSpace="normal",this.material=null,this.color=null,this.colorRanges=null,this.outlineWidth=0,this.outlineColor=0,this.outlineOpacity=1,this.outlineBlur=0,this.outlineOffsetX=0,this.outlineOffsetY=0,this.strokeWidth=0,this.strokeColor=yp,this.strokeOpacity=1,this.fillOpacity=1,this.depthOffset=0,this.clipRect=null,this.orientation=Xc,this.glyphGeometryDetail=1,this.sdfGlyphSize=null,this.gpuAccelerateSDF=!0,this.debugSDF=!1}sync(e){this._needsSync&&(this._needsSync=!1,this._isSyncing?(this._queuedSyncs||(this._queuedSyncs=[])).push(e):(this._isSyncing=!0,this.dispatchEvent(OS),MS({text:this.text,font:this.font,lang:this.lang,fontSize:this.fontSize||.1,fontWeight:this.fontWeight||"normal",fontStyle:this.fontStyle||"normal",letterSpacing:this.letterSpacing||0,lineHeight:this.lineHeight||"normal",maxWidth:this.maxWidth,direction:this.direction||"auto",textAlign:this.textAlign,textIndent:this.textIndent,whiteSpace:this.whiteSpace,overflowWrap:this.overflowWrap,anchorX:this.anchorX,anchorY:this.anchorY,colorRanges:this.colorRanges,includeCaretPositions:!0,sdfGlyphSize:this.sdfGlyphSize,gpuAccelerateSDF:this.gpuAccelerateSDF,unicodeFontsURL:this.unicodeFontsURL},t=>{this._isSyncing=!1,this._textRenderInfo=t,this.geometry.updateGlyphs(t.glyphBounds,t.glyphAtlasIndices,t.blockBounds,t.chunkedBounds,t.glyphColors);const i=this._queuedSyncs;i&&(this._queuedSyncs=null,this._needsSync=!0,this.sync(()=>{i.forEach(r=>r&&r())})),this.dispatchEvent(BS),e&&e()})))}onBeforeRender(e,t,i,r,s,a){this.sync(),s.isTroikaTextMaterial&&this._prepareForRender(s)}dispose(){this.geometry.dispose()}get textRenderInfo(){return this._textRenderInfo||null}createDerivedMaterial(e){return FS(e)}get material(){let e=this._derivedMaterial;const t=this._baseMaterial||this._defaultMaterial||(this._defaultMaterial=of.clone());if((!e||!e.isDerivedFrom(t))&&(e=this._derivedMaterial=this.createDerivedMaterial(t),t.addEventListener("dispose",function i(){t.removeEventListener("dispose",i),e.dispose()})),this.hasOutline()){let i=e._outlineMtl;return i||(i=e._outlineMtl=Object.create(e,{id:{value:e.id+.1}}),i.isTextOutlineMaterial=!0,i.depthWrite=!1,i.map=null,e.addEventListener("dispose",function r(){e.removeEventListener("dispose",r),i.dispose()})),[i,e]}else return e}set material(e){e&&e.isTroikaTextMaterial?(this._derivedMaterial=e,this._baseMaterial=e.baseMaterial):this._baseMaterial=e}hasOutline(){return!!(this.outlineWidth||this.outlineBlur||this.outlineOffsetX||this.outlineOffsetY)}get glyphGeometryDetail(){return this.geometry.detail}set glyphGeometryDetail(e){this.geometry.detail=e}get curveRadius(){return this.geometry.curveRadius}set curveRadius(e){this.geometry.curveRadius=e}get customDepthMaterial(){return Mp(this.material).getDepthMaterial()}set customDepthMaterial(e){}get customDistanceMaterial(){return Mp(this.material).getDistanceMaterial()}set customDistanceMaterial(e){}_prepareForRender(e){const t=e.isTextOutlineMaterial,i=e.uniforms,r=this.textRenderInfo;if(r){const{sdfTexture:o,blockBounds:l}=r;i.uTroikaSDFTexture.value=o,i.uTroikaSDFTextureSize.value.set(o.image.width,o.image.height),i.uTroikaSDFGlyphSize.value=r.sdfGlyphSize,i.uTroikaSDFExponent.value=r.sdfExponent,i.uTroikaTotalBounds.value.fromArray(l),i.uTroikaUseGlyphColors.value=!t&&!!r.glyphColors;let c=0,u=0,f=0,h,d,m,g=0,p=0;if(t){let{outlineWidth:v,outlineOffsetX:b,outlineOffsetY:S,outlineBlur:E,outlineOpacity:M}=this;c=this._parsePercent(v)||0,u=Math.max(0,this._parsePercent(E)||0),h=M,g=this._parsePercent(b)||0,p=this._parsePercent(S)||0}else f=Math.max(0,this._parsePercent(this.strokeWidth)||0),f&&(m=this.strokeColor,i.uTroikaStrokeColor.value.set(m??yp),d=this.strokeOpacity,d==null&&(d=1)),h=this.fillOpacity;i.uTroikaEdgeOffset.value=c,i.uTroikaPositionOffset.value.set(g,p),i.uTroikaBlurRadius.value=u,i.uTroikaStrokeWidth.value=f,i.uTroikaStrokeOpacity.value=d,i.uTroikaFillOpacity.value=h??1,i.uTroikaCurveRadius.value=this.curveRadius||0;let _=this.clipRect;if(_&&Array.isArray(_)&&_.length===4)i.uTroikaClipRect.value.fromArray(_);else{const v=(this.fontSize||.1)*100;i.uTroikaClipRect.value.set(l[0]-v,l[1]-v,l[2]+v,l[3]+v)}this.geometry.applyClipRect(i.uTroikaClipRect.value)}i.uTroikaSDFDebug.value=!!this.debugSDF,e.polygonOffset=!!this.depthOffset,e.polygonOffsetFactor=e.polygonOffsetUnits=this.depthOffset||0;const s=t?this.outlineColor||0:this.color;if(s==null)delete e.color;else{const o=e.hasOwnProperty("color")?e.color:e.color=new ut;(s!==o._input||typeof s=="object")&&o.set(o._input=s)}let a=this.orientation||Xc;if(a!==e._orientation){let o=i.uTroikaOrient.value;a=a.replace(/[^-+xyz]/g,"");let l=a!==Xc&&a.match(/^([-+])([xyz])([-+])([xyz])$/);if(l){let[,c,u,f,h]=l;Ho.set(0,0,0)[u]=c==="-"?1:-1,Wc.set(0,0,0)[h]=f==="-"?-1:1,bp.lookAt(NS,Ho.cross(Wc),Wc),o.setFromMatrix4(bp)}else o.identity();e._orientation=a}}_parsePercent(e){if(typeof e=="string"){let t=e.match(/^(-?[\d.]+)%$/),i=t?parseFloat(t[1]):NaN;e=(isNaN(i)?0:i/100)*this.fontSize}return e}localPositionToTextCoords(e,t=new Xe){t.copy(e);const i=this.curveRadius;return i&&(t.x=Math.atan2(e.x,Math.abs(i)-Math.abs(e.z))*Math.abs(i)),t}worldPositionToTextCoords(e,t=new Xe){return Ho.copy(e),this.localPositionToTextCoords(this.worldToLocal(Ho),t)}raycast(e,t){const{textRenderInfo:i,curveRadius:r}=this;if(i){const s=i.blockBounds,a=r?_0():g0(),o=a.geometry,{position:l,uv:c}=o.attributes;for(let u=0;u<c.count;u++){let f=s[0]+c.getX(u)*(s[2]-s[0]);const h=s[1]+c.getY(u)*(s[3]-s[1]);let d=0;r&&(d=r-Math.cos(f/r)*r,f=Math.sin(f/r)*r),l.setXYZ(u,f,h,d)}o.boundingSphere=this.geometry.boundingSphere,o.boundingBox=this.geometry.boundingBox,a.matrixWorld=this.matrixWorld,a.material.side=this.material.side,Ea.length=0,a.raycast(e,Ea);for(let u=0;u<Ea.length;u++)Ea[u].object=this,t.push(Ea[u])}}copy(e){const t=this.geometry;return super.copy(e),this.geometry=t,kS.forEach(i=>{this[i]=e[i]}),this}clone(){return new this.constructor().copy(this)}}v0.forEach(n=>{const e="_private_"+n;Object.defineProperty(wh.prototype,n,{get(){return this[e]},set(t){t!==this[e]&&(this[e]=t,this._needsSync=!0)}})});new ut;const Sp={type:"change"},lf={type:"start"},x0={type:"end"},Vo=new Fl,Tp=new hr,zS=Math.cos(70*hv.DEG2RAD),Zt=new $,wn=2*Math.PI,St={NONE:-1,ROTATE:0,DOLLY:1,PAN:2,TOUCH_ROTATE:3,TOUCH_PAN:4,TOUCH_DOLLY_PAN:5,TOUCH_DOLLY_ROTATE:6},jc=1e-6;class GS extends qv{constructor(e,t=null){super(e,t),this.state=St.NONE,this.target=new $,this.cursor=new $,this.minDistance=0,this.maxDistance=1/0,this.minZoom=0,this.maxZoom=1/0,this.minTargetRadius=0,this.maxTargetRadius=1/0,this.minPolarAngle=0,this.maxPolarAngle=Math.PI,this.minAzimuthAngle=-1/0,this.maxAzimuthAngle=1/0,this.enableDamping=!1,this.dampingFactor=.05,this.enableZoom=!0,this.zoomSpeed=1,this.enableRotate=!0,this.rotateSpeed=1,this.keyRotateSpeed=1,this.enablePan=!0,this.panSpeed=1,this.screenSpacePanning=!0,this.keyPanSpeed=7,this.zoomToCursor=!1,this.autoRotate=!1,this.autoRotateSpeed=2,this.keys={LEFT:"ArrowLeft",UP:"ArrowUp",RIGHT:"ArrowRight",BOTTOM:"ArrowDown"},this.mouseButtons={LEFT:Is.ROTATE,MIDDLE:Is.DOLLY,RIGHT:Is.PAN},this.touches={ONE:Ps.ROTATE,TWO:Ps.DOLLY_PAN},this.target0=this.target.clone(),this.position0=this.object.position.clone(),this.zoom0=this.object.zoom,this._cursorStyle="auto",this._domElementKeyEvents=null,this._lastPosition=new $,this._lastQuaternion=new Mr,this._lastTargetPosition=new $,this._quat=new Mr().setFromUnitVectors(e.up,new $(0,1,0)),this._quatInverse=this._quat.clone().invert(),this._spherical=new Od,this._sphericalDelta=new Od,this._scale=1,this._panOffset=new $,this._rotateStart=new Xe,this._rotateEnd=new Xe,this._rotateDelta=new Xe,this._panStart=new Xe,this._panEnd=new Xe,this._panDelta=new Xe,this._dollyStart=new Xe,this._dollyEnd=new Xe,this._dollyDelta=new Xe,this._dollyDirection=new $,this._mouse=new Xe,this._performCursorZoom=!1,this._pointers=[],this._pointerPositions={},this._controlActive=!1,this._onPointerMove=VS.bind(this),this._onPointerDown=HS.bind(this),this._onPointerUp=WS.bind(this),this._onContextMenu=$S.bind(this),this._onMouseWheel=YS.bind(this),this._onKeyDown=qS.bind(this),this._onTouchStart=KS.bind(this),this._onTouchMove=ZS.bind(this),this._onMouseDown=XS.bind(this),this._onMouseMove=jS.bind(this),this._interceptControlDown=JS.bind(this),this._interceptControlUp=QS.bind(this),this.domElement!==null&&this.connect(this.domElement),this.update()}set cursorStyle(e){this._cursorStyle=e,e==="grab"?this.domElement.style.cursor="grab":this.domElement.style.cursor="auto"}get cursorStyle(){return this._cursorStyle}connect(e){super.connect(e),this.domElement.addEventListener("pointerdown",this._onPointerDown),this.domElement.addEventListener("pointercancel",this._onPointerUp),this.domElement.addEventListener("contextmenu",this._onContextMenu),this.domElement.addEventListener("wheel",this._onMouseWheel,{passive:!1}),this.domElement.getRootNode().addEventListener("keydown",this._interceptControlDown,{passive:!0,capture:!0}),this.domElement.style.touchAction="none"}disconnect(){this.domElement.removeEventListener("pointerdown",this._onPointerDown),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.domElement.removeEventListener("pointercancel",this._onPointerUp),this.domElement.removeEventListener("wheel",this._onMouseWheel),this.domElement.removeEventListener("contextmenu",this._onContextMenu),this.stopListenToKeyEvents(),this.domElement.getRootNode().removeEventListener("keydown",this._interceptControlDown,{capture:!0}),this.domElement.style.touchAction=""}dispose(){this.disconnect()}getPolarAngle(){return this._spherical.phi}getAzimuthalAngle(){return this._spherical.theta}getDistance(){return this.object.position.distanceTo(this.target)}listenToKeyEvents(e){e.addEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=e}stopListenToKeyEvents(){this._domElementKeyEvents!==null&&(this._domElementKeyEvents.removeEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=null)}saveState(){this.target0.copy(this.target),this.position0.copy(this.object.position),this.zoom0=this.object.zoom}reset(){this.target.copy(this.target0),this.object.position.copy(this.position0),this.object.zoom=this.zoom0,this.object.updateProjectionMatrix(),this.dispatchEvent(Sp),this.update(),this.state=St.NONE}pan(e,t){this._pan(e,t),this.update()}dollyIn(e){this._dollyIn(e),this.update()}dollyOut(e){this._dollyOut(e),this.update()}rotateLeft(e){this._rotateLeft(e),this.update()}rotateUp(e){this._rotateUp(e),this.update()}update(e=null){const t=this.object.position;Zt.copy(t).sub(this.target),Zt.applyQuaternion(this._quat),this._spherical.setFromVector3(Zt),this.autoRotate&&this.state===St.NONE&&this._rotateLeft(this._getAutoRotationAngle(e)),this.enableDamping?(this._spherical.theta+=this._sphericalDelta.theta*this.dampingFactor,this._spherical.phi+=this._sphericalDelta.phi*this.dampingFactor):(this._spherical.theta+=this._sphericalDelta.theta,this._spherical.phi+=this._sphericalDelta.phi);let i=this.minAzimuthAngle,r=this.maxAzimuthAngle;isFinite(i)&&isFinite(r)&&(i<-Math.PI?i+=wn:i>Math.PI&&(i-=wn),r<-Math.PI?r+=wn:r>Math.PI&&(r-=wn),i<=r?this._spherical.theta=Math.max(i,Math.min(r,this._spherical.theta)):this._spherical.theta=this._spherical.theta>(i+r)/2?Math.max(i,this._spherical.theta):Math.min(r,this._spherical.theta)),this._spherical.phi=Math.max(this.minPolarAngle,Math.min(this.maxPolarAngle,this._spherical.phi)),this._spherical.makeSafe(),this.enableDamping===!0?this.target.addScaledVector(this._panOffset,this.dampingFactor):this.target.add(this._panOffset),this.target.sub(this.cursor),this.target.clampLength(this.minTargetRadius,this.maxTargetRadius),this.target.add(this.cursor);let s=!1;if(this.zoomToCursor&&this._performCursorZoom||this.object.isOrthographicCamera)this._spherical.radius=this._clampDistance(this._spherical.radius);else{const a=this._spherical.radius;this._spherical.radius=this._clampDistance(this._spherical.radius*this._scale),s=a!=this._spherical.radius}if(Zt.setFromSpherical(this._spherical),Zt.applyQuaternion(this._quatInverse),t.copy(this.target).add(Zt),this.object.lookAt(this.target),this.enableDamping===!0?(this._sphericalDelta.theta*=1-this.dampingFactor,this._sphericalDelta.phi*=1-this.dampingFactor,this._panOffset.multiplyScalar(1-this.dampingFactor)):(this._sphericalDelta.set(0,0,0),this._panOffset.set(0,0,0)),this.zoomToCursor&&this._performCursorZoom){let a=null;if(this.object.isPerspectiveCamera){const o=Zt.length();a=this._clampDistance(o*this._scale);const l=o-a;this.object.position.addScaledVector(this._dollyDirection,l),this.object.updateMatrixWorld(),s=!!l}else if(this.object.isOrthographicCamera){const o=new $(this._mouse.x,this._mouse.y,0);o.unproject(this.object);const l=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),this.object.updateProjectionMatrix(),s=l!==this.object.zoom;const c=new $(this._mouse.x,this._mouse.y,0);c.unproject(this.object),this.object.position.sub(c).add(o),this.object.updateMatrixWorld(),a=Zt.length()}else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - zoom to cursor disabled."),this.zoomToCursor=!1;a!==null&&(this.screenSpacePanning?this.target.set(0,0,-1).transformDirection(this.object.matrix).multiplyScalar(a).add(this.object.position):(Vo.origin.copy(this.object.position),Vo.direction.set(0,0,-1).transformDirection(this.object.matrix),Math.abs(this.object.up.dot(Vo.direction))<zS?this.object.lookAt(this.target):(Tp.setFromNormalAndCoplanarPoint(this.object.up,this.target),Vo.intersectPlane(Tp,this.target))))}else if(this.object.isOrthographicCamera){const a=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),a!==this.object.zoom&&(this.object.updateProjectionMatrix(),s=!0)}return this._scale=1,this._performCursorZoom=!1,s||this._lastPosition.distanceToSquared(this.object.position)>jc||8*(1-this._lastQuaternion.dot(this.object.quaternion))>jc||this._lastTargetPosition.distanceToSquared(this.target)>jc?(this.dispatchEvent(Sp),this._lastPosition.copy(this.object.position),this._lastQuaternion.copy(this.object.quaternion),this._lastTargetPosition.copy(this.target),!0):!1}_getAutoRotationAngle(e){return e!==null?wn/60*this.autoRotateSpeed*e:wn/60/60*this.autoRotateSpeed}_getZoomScale(e){const t=Math.abs(e*.01);return Math.pow(.95,this.zoomSpeed*t)}_rotateLeft(e){this._sphericalDelta.theta-=e}_rotateUp(e){this._sphericalDelta.phi-=e}_panLeft(e,t){Zt.setFromMatrixColumn(t,0),Zt.multiplyScalar(-e),this._panOffset.add(Zt)}_panUp(e,t){this.screenSpacePanning===!0?Zt.setFromMatrixColumn(t,1):(Zt.setFromMatrixColumn(t,0),Zt.crossVectors(this.object.up,Zt)),Zt.multiplyScalar(e),this._panOffset.add(Zt)}_pan(e,t){const i=this.domElement;if(this.object.isPerspectiveCamera){const r=this.object.position;Zt.copy(r).sub(this.target);let s=Zt.length();s*=Math.tan(this.object.fov/2*Math.PI/180),this._panLeft(2*e*s/i.clientHeight,this.object.matrix),this._panUp(2*t*s/i.clientHeight,this.object.matrix)}else this.object.isOrthographicCamera?(this._panLeft(e*(this.object.right-this.object.left)/this.object.zoom/i.clientWidth,this.object.matrix),this._panUp(t*(this.object.top-this.object.bottom)/this.object.zoom/i.clientHeight,this.object.matrix)):(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled."),this.enablePan=!1)}_dollyOut(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale/=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_dollyIn(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale*=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_updateZoomParameters(e,t){if(!this.zoomToCursor)return;this._performCursorZoom=!0;const i=this.domElement.getBoundingClientRect(),r=e-i.left,s=t-i.top,a=i.width,o=i.height;this._mouse.x=r/a*2-1,this._mouse.y=-(s/o)*2+1,this._dollyDirection.set(this._mouse.x,this._mouse.y,1).unproject(this.object).sub(this.object.position).normalize()}_clampDistance(e){return Math.max(this.minDistance,Math.min(this.maxDistance,e))}_handleMouseDownRotate(e){this._rotateStart.set(e.clientX,e.clientY)}_handleMouseDownDolly(e){this._updateZoomParameters(e.clientX,e.clientX),this._dollyStart.set(e.clientX,e.clientY)}_handleMouseDownPan(e){this._panStart.set(e.clientX,e.clientY)}_handleMouseMoveRotate(e){this._rotateEnd.set(e.clientX,e.clientY),this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(wn*this._rotateDelta.x/t.clientHeight),this._rotateUp(wn*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd),this.update()}_handleMouseMoveDolly(e){this._dollyEnd.set(e.clientX,e.clientY),this._dollyDelta.subVectors(this._dollyEnd,this._dollyStart),this._dollyDelta.y>0?this._dollyOut(this._getZoomScale(this._dollyDelta.y)):this._dollyDelta.y<0&&this._dollyIn(this._getZoomScale(this._dollyDelta.y)),this._dollyStart.copy(this._dollyEnd),this.update()}_handleMouseMovePan(e){this._panEnd.set(e.clientX,e.clientY),this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd),this.update()}_handleMouseWheel(e){this._updateZoomParameters(e.clientX,e.clientY),e.deltaY<0?this._dollyIn(this._getZoomScale(e.deltaY)):e.deltaY>0&&this._dollyOut(this._getZoomScale(e.deltaY)),this.update()}_handleKeyDown(e){let t=!1;switch(e.code){case this.keys.UP:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(wn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,this.keyPanSpeed),t=!0;break;case this.keys.BOTTOM:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(-wn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,-this.keyPanSpeed),t=!0;break;case this.keys.LEFT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(wn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(this.keyPanSpeed,0),t=!0;break;case this.keys.RIGHT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(-wn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(-this.keyPanSpeed,0),t=!0;break}t&&(e.preventDefault(),this.update())}_handleTouchStartRotate(e){if(this._pointers.length===1)this._rotateStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),i=.5*(e.pageX+t.x),r=.5*(e.pageY+t.y);this._rotateStart.set(i,r)}}_handleTouchStartPan(e){if(this._pointers.length===1)this._panStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),i=.5*(e.pageX+t.x),r=.5*(e.pageY+t.y);this._panStart.set(i,r)}}_handleTouchStartDolly(e){const t=this._getSecondPointerPosition(e),i=e.pageX-t.x,r=e.pageY-t.y,s=Math.sqrt(i*i+r*r);this._dollyStart.set(0,s)}_handleTouchStartDollyPan(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enablePan&&this._handleTouchStartPan(e)}_handleTouchStartDollyRotate(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enableRotate&&this._handleTouchStartRotate(e)}_handleTouchMoveRotate(e){if(this._pointers.length==1)this._rotateEnd.set(e.pageX,e.pageY);else{const i=this._getSecondPointerPosition(e),r=.5*(e.pageX+i.x),s=.5*(e.pageY+i.y);this._rotateEnd.set(r,s)}this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(wn*this._rotateDelta.x/t.clientHeight),this._rotateUp(wn*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd)}_handleTouchMovePan(e){if(this._pointers.length===1)this._panEnd.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),i=.5*(e.pageX+t.x),r=.5*(e.pageY+t.y);this._panEnd.set(i,r)}this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd)}_handleTouchMoveDolly(e){const t=this._getSecondPointerPosition(e),i=e.pageX-t.x,r=e.pageY-t.y,s=Math.sqrt(i*i+r*r);this._dollyEnd.set(0,s),this._dollyDelta.set(0,Math.pow(this._dollyEnd.y/this._dollyStart.y,this.zoomSpeed)),this._dollyOut(this._dollyDelta.y),this._dollyStart.copy(this._dollyEnd);const a=(e.pageX+t.x)*.5,o=(e.pageY+t.y)*.5;this._updateZoomParameters(a,o)}_handleTouchMoveDollyPan(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enablePan&&this._handleTouchMovePan(e)}_handleTouchMoveDollyRotate(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enableRotate&&this._handleTouchMoveRotate(e)}_addPointer(e){this._pointers.push(e.pointerId)}_removePointer(e){delete this._pointerPositions[e.pointerId];for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId){this._pointers.splice(t,1);return}}_isTrackingPointer(e){for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId)return!0;return!1}_trackPointer(e){let t=this._pointerPositions[e.pointerId];t===void 0&&(t=new Xe,this._pointerPositions[e.pointerId]=t),t.set(e.pageX,e.pageY)}_getSecondPointerPosition(e){const t=e.pointerId===this._pointers[0]?this._pointers[1]:this._pointers[0];return this._pointerPositions[t]}_customWheelEvent(e){const t=e.deltaMode,i={clientX:e.clientX,clientY:e.clientY,deltaY:e.deltaY};switch(t){case 1:i.deltaY*=16;break;case 2:i.deltaY*=100;break}return e.ctrlKey&&!this._controlActive&&(i.deltaY*=10),i}}function HS(n){this.enabled!==!1&&(this._pointers.length===0&&(this.domElement.setPointerCapture(n.pointerId),this.domElement.ownerDocument.addEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.addEventListener("pointerup",this._onPointerUp)),!this._isTrackingPointer(n)&&(this._addPointer(n),n.pointerType==="touch"?this._onTouchStart(n):this._onMouseDown(n),this._cursorStyle==="grab"&&(this.domElement.style.cursor="grabbing")))}function VS(n){this.enabled!==!1&&(n.pointerType==="touch"?this._onTouchMove(n):this._onMouseMove(n))}function WS(n){switch(this._removePointer(n),this._pointers.length){case 0:this.domElement.releasePointerCapture(n.pointerId),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.dispatchEvent(x0),this.state=St.NONE,this._cursorStyle==="grab"&&(this.domElement.style.cursor="grab");break;case 1:const e=this._pointers[0],t=this._pointerPositions[e];this._onTouchStart({pointerId:e,pageX:t.x,pageY:t.y});break}}function XS(n){let e;switch(n.button){case 0:e=this.mouseButtons.LEFT;break;case 1:e=this.mouseButtons.MIDDLE;break;case 2:e=this.mouseButtons.RIGHT;break;default:e=-1}switch(e){case Is.DOLLY:if(this.enableZoom===!1)return;this._handleMouseDownDolly(n),this.state=St.DOLLY;break;case Is.ROTATE:if(n.ctrlKey||n.metaKey||n.shiftKey){if(this.enablePan===!1)return;this._handleMouseDownPan(n),this.state=St.PAN}else{if(this.enableRotate===!1)return;this._handleMouseDownRotate(n),this.state=St.ROTATE}break;case Is.PAN:if(n.ctrlKey||n.metaKey||n.shiftKey){if(this.enableRotate===!1)return;this._handleMouseDownRotate(n),this.state=St.ROTATE}else{if(this.enablePan===!1)return;this._handleMouseDownPan(n),this.state=St.PAN}break;default:this.state=St.NONE}this.state!==St.NONE&&this.dispatchEvent(lf)}function jS(n){switch(this.state){case St.ROTATE:if(this.enableRotate===!1)return;this._handleMouseMoveRotate(n);break;case St.DOLLY:if(this.enableZoom===!1)return;this._handleMouseMoveDolly(n);break;case St.PAN:if(this.enablePan===!1)return;this._handleMouseMovePan(n);break}}function YS(n){this.enabled===!1||this.enableZoom===!1||this.state!==St.NONE||(n.preventDefault(),this.dispatchEvent(lf),this._handleMouseWheel(this._customWheelEvent(n)),this.dispatchEvent(x0))}function qS(n){this.enabled!==!1&&this._handleKeyDown(n)}function KS(n){switch(this._trackPointer(n),this._pointers.length){case 1:switch(this.touches.ONE){case Ps.ROTATE:if(this.enableRotate===!1)return;this._handleTouchStartRotate(n),this.state=St.TOUCH_ROTATE;break;case Ps.PAN:if(this.enablePan===!1)return;this._handleTouchStartPan(n),this.state=St.TOUCH_PAN;break;default:this.state=St.NONE}break;case 2:switch(this.touches.TWO){case Ps.DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchStartDollyPan(n),this.state=St.TOUCH_DOLLY_PAN;break;case Ps.DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchStartDollyRotate(n),this.state=St.TOUCH_DOLLY_ROTATE;break;default:this.state=St.NONE}break;default:this.state=St.NONE}this.state!==St.NONE&&this.dispatchEvent(lf)}function ZS(n){switch(this._trackPointer(n),this.state){case St.TOUCH_ROTATE:if(this.enableRotate===!1)return;this._handleTouchMoveRotate(n),this.update();break;case St.TOUCH_PAN:if(this.enablePan===!1)return;this._handleTouchMovePan(n),this.update();break;case St.TOUCH_DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchMoveDollyPan(n),this.update();break;case St.TOUCH_DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchMoveDollyRotate(n),this.update();break;default:this.state=St.NONE}}function $S(n){this.enabled!==!1&&n.preventDefault()}function JS(n){n.key==="Control"&&(this._controlActive=!0,this.domElement.getRootNode().addEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function QS(n){n.key==="Control"&&(this._controlActive=!1,this.domElement.getRootNode().removeEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function Gi(n){if(n===void 0)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return n}function y0(n,e){n.prototype=Object.create(e.prototype),n.prototype.constructor=n,n.__proto__=e}/*!
 * GSAP 3.15.0
 * https://gsap.com
 *
 * @license Copyright 2008-2026, GreenSock. All rights reserved.
 * Subject to the terms at https://gsap.com/standard-license
 * @author: Jack Doyle, jack@greensock.com
*/var jn={autoSleep:120,force3D:"auto",nullTargetWarn:1,units:{lineHeight:""}},Va={duration:.5,overwrite:!1,delay:0},cf,fn,It,ni=1e8,Ct=1/ni,Ah=Math.PI*2,e2=Ah/4,t2=0,b0=Math.sqrt,n2=Math.cos,i2=Math.sin,cn=function(e){return typeof e=="string"},Ht=function(e){return typeof e=="function"},Ki=function(e){return typeof e=="number"},uf=function(e){return typeof e>"u"},Li=function(e){return typeof e=="object"},Cn=function(e){return e!==!1},hf=function(){return typeof window<"u"},Wo=function(e){return Ht(e)||cn(e)},M0=typeof ArrayBuffer=="function"&&ArrayBuffer.isView||function(){},vn=Array.isArray,r2=/random\([^)]+\)/g,s2=/,\s*/g,Ep=/(?:-?\.?\d|\.)+/gi,S0=/[-+=.]*\d+[.e\-+]*\d*[e\-+]*\d*/g,Us=/[-+=.]*\d+[.e-]*\d*[a-z%]*/g,Yc=/[-+=.]*\d+\.?\d*(?:e-|e\+)?\d*/gi,T0=/[+-]=-?[.\d]+/,a2=/[^,'"\[\]\s]+/gi,o2=/^[+\-=e\s\d]*\d+[.\d]*([a-z]*|%)\s*$/i,Bt,Mi,Rh,ff,qn={},yl={},E0,w0=function(e){return(yl=Xs(e,qn))&&Ln},df=function(e,t){return console.warn("Invalid property",e,"set to",t,"Missing plugin? gsap.registerPlugin()")},Wa=function(e,t){return!t&&console.warn(e)},A0=function(e,t){return e&&(qn[e]=t)&&yl&&(yl[e]=t)||qn},Xa=function(){return 0},l2={suppressEvents:!0,isStart:!0,kill:!1},rl={suppressEvents:!0,kill:!1},c2={suppressEvents:!0},pf={},xr=[],Ch={},R0,Gn={},qc={},wp=30,sl=[],mf="",gf=function(e){var t=e[0],i,r;if(Li(t)||Ht(t)||(e=[e]),!(i=(t._gsap||{}).harness)){for(r=sl.length;r--&&!sl[r].targetTest(t););i=sl[r]}for(r=e.length;r--;)e[r]&&(e[r]._gsap||(e[r]._gsap=new Z0(e[r],i)))||e.splice(r,1);return e},Xr=function(e){return e._gsap||gf(ii(e))[0]._gsap},C0=function(e,t,i){return(i=e[t])&&Ht(i)?e[t]():uf(i)&&e.getAttribute&&e.getAttribute(t)||i},Pn=function(e,t){return(e=e.split(",")).forEach(t)||e},Wt=function(e){return Math.round(e*1e5)/1e5||0},Ot=function(e){return Math.round(e*1e7)/1e7||0},Ns=function(e,t){var i=t.charAt(0),r=parseFloat(t.substr(2));return e=parseFloat(e),i==="+"?e+r:i==="-"?e-r:i==="*"?e*r:e/r},u2=function(e,t){for(var i=t.length,r=0;e.indexOf(t[r])<0&&++r<i;);return r<i},bl=function(){var e=xr.length,t=xr.slice(0),i,r;for(Ch={},xr.length=0,i=0;i<e;i++)r=t[i],r&&r._lazy&&(r.render(r._lazy[0],r._lazy[1],!0)._lazy=0)},_f=function(e){return!!(e._initted||e._startAt||e.add)},P0=function(e,t,i,r){xr.length&&!fn&&bl(),e.render(t,i,!!(fn&&t<0&&_f(e))),xr.length&&!fn&&bl()},D0=function(e){var t=parseFloat(e);return(t||t===0)&&(e+"").match(a2).length<2?t:cn(e)?e.trim():e},U0=function(e){return e},Kn=function(e,t){for(var i in t)i in e||(e[i]=t[i]);return e},h2=function(e){return function(t,i){for(var r in i)r in t||r==="duration"&&e||r==="ease"||(t[r]=i[r])}},Xs=function(e,t){for(var i in t)e[i]=t[i];return e},Ap=function n(e,t){for(var i in t)i!=="__proto__"&&i!=="constructor"&&i!=="prototype"&&(e[i]=Li(t[i])?n(e[i]||(e[i]={}),t[i]):t[i]);return e},Ml=function(e,t){var i={},r;for(r in e)r in t||(i[r]=e[r]);return i},Ba=function(e){var t=e.parent||Bt,i=e.keyframes?h2(vn(e.keyframes)):Kn;if(Cn(e.inherit))for(;t;)i(e,t.vars.defaults),t=t.parent||t._dp;return e},f2=function(e,t){for(var i=e.length,r=i===t.length;r&&i--&&e[i]===t[i];);return i<0},L0=function(e,t,i,r,s){var a=e[r],o;if(s)for(o=t[s];a&&a[s]>o;)a=a._prev;return a?(t._next=a._next,a._next=t):(t._next=e[i],e[i]=t),t._next?t._next._prev=t:e[r]=t,t._prev=a,t.parent=t._dp=e,t},kl=function(e,t,i,r){i===void 0&&(i="_first"),r===void 0&&(r="_last");var s=t._prev,a=t._next;s?s._next=a:e[i]===t&&(e[i]=a),a?a._prev=s:e[r]===t&&(e[r]=s),t._next=t._prev=t.parent=null},Sr=function(e,t){e.parent&&(!t||e.parent.autoRemoveChildren)&&e.parent.remove&&e.parent.remove(e),e._act=0},jr=function(e,t){if(e&&(!t||t._end>e._dur||t._start<0))for(var i=e;i;)i._dirty=1,i=i.parent;return e},d2=function(e){for(var t=e.parent;t&&t.parent;)t._dirty=1,t.totalDuration(),t=t.parent;return e},Ph=function(e,t,i,r){return e._startAt&&(fn?e._startAt.revert(rl):e.vars.immediateRender&&!e.vars.autoRevert||e._startAt.render(t,!0,r))},p2=function n(e){return!e||e._ts&&n(e.parent)},Rp=function(e){return e._repeat?js(e._tTime,e=e.duration()+e._rDelay)*e:0},js=function(e,t){var i=Math.floor(e=Ot(e/t));return e&&i===e?i-1:i},Sl=function(e,t){return(e-t._start)*t._ts+(t._ts>=0?0:t._dirty?t.totalDuration():t._tDur)},zl=function(e){return e._end=Ot(e._start+(e._tDur/Math.abs(e._ts||e._rts||Ct)||0))},Gl=function(e,t){var i=e._dp;return i&&i.smoothChildTiming&&e._ts&&(e._start=Ot(i._time-(e._ts>0?t/e._ts:((e._dirty?e.totalDuration():e._tDur)-t)/-e._ts)),zl(e),i._dirty||jr(i,e)),e},I0=function(e,t){var i;if((t._time||!t._dur&&t._initted||t._start<e._time&&(t._dur||!t.add))&&(i=Sl(e.rawTime(),t),(!t._dur||to(0,t.totalDuration(),i)-t._tTime>Ct)&&t.render(i,!0)),jr(e,t)._dp&&e._initted&&e._time>=e._dur&&e._ts){if(e._dur<e.duration())for(i=e;i._dp;)i.rawTime()>=0&&i.totalTime(i._tTime),i=i._dp;e._zTime=-Ct}},wi=function(e,t,i,r){return t.parent&&Sr(t),t._start=Ot((Ki(i)?i:i||e!==Bt?Qn(e,i,t):e._time)+t._delay),t._end=Ot(t._start+(t.totalDuration()/Math.abs(t.timeScale())||0)),L0(e,t,"_first","_last",e._sort?"_start":0),Dh(t)||(e._recent=t),r||I0(e,t),e._ts<0&&Gl(e,e._tTime),e},F0=function(e,t){return(qn.ScrollTrigger||df("scrollTrigger",t))&&qn.ScrollTrigger.create(t,e)},N0=function(e,t,i,r,s){if(xf(e,t,s),!e._initted)return 1;if(!i&&e._pt&&!fn&&(e._dur&&e.vars.lazy!==!1||!e._dur&&e.vars.lazy)&&R0!==Vn.frame)return xr.push(e),e._lazy=[s,r],1},m2=function n(e){var t=e.parent;return t&&t._ts&&t._initted&&!t._lock&&(t.rawTime()<0||n(t))},Dh=function(e){var t=e.data;return t==="isFromStart"||t==="isStart"},g2=function(e,t,i,r){var s=e.ratio,a=t<0||!t&&(!e._start&&m2(e)&&!(!e._initted&&Dh(e))||(e._ts<0||e._dp._ts<0)&&!Dh(e))?0:1,o=e._rDelay,l=0,c,u,f;if(o&&e._repeat&&(l=to(0,e._tDur,t),u=js(l,o),e._yoyo&&u&1&&(a=1-a),u!==js(e._tTime,o)&&(s=1-a,e.vars.repeatRefresh&&e._initted&&e.invalidate())),a!==s||fn||r||e._zTime===Ct||!t&&e._zTime){if(!e._initted&&N0(e,t,r,i,l))return;for(f=e._zTime,e._zTime=t||(i?Ct:0),i||(i=t&&!f),e.ratio=a,e._from&&(a=1-a),e._time=0,e._tTime=l,c=e._pt;c;)c.r(a,c.d),c=c._next;t<0&&Ph(e,t,i,!0),e._onUpdate&&!i&&Wn(e,"onUpdate"),l&&e._repeat&&!i&&e.parent&&Wn(e,"onRepeat"),(t>=e._tDur||t<0)&&e.ratio===a&&(a&&Sr(e,1),!i&&!fn&&(Wn(e,a?"onComplete":"onReverseComplete",!0),e._prom&&e._prom()))}else e._zTime||(e._zTime=t)},_2=function(e,t,i){var r;if(i>t)for(r=e._first;r&&r._start<=i;){if(r.data==="isPause"&&r._start>t)return r;r=r._next}else for(r=e._last;r&&r._start>=i;){if(r.data==="isPause"&&r._start<t)return r;r=r._prev}},Ys=function(e,t,i,r){var s=e._repeat,a=Ot(t)||0,o=e._tTime/e._tDur;return o&&!r&&(e._time*=a/e._dur),e._dur=a,e._tDur=s?s<0?1e10:Ot(a*(s+1)+e._rDelay*s):a,o>0&&!r&&Gl(e,e._tTime=e._tDur*o),e.parent&&zl(e),i||jr(e.parent,e),e},Cp=function(e){return e instanceof Rn?jr(e):Ys(e,e._dur)},v2={_start:0,endTime:Xa,totalDuration:Xa},Qn=function n(e,t,i){var r=e.labels,s=e._recent||v2,a=e.duration()>=ni?s.endTime(!1):e._dur,o,l,c;return cn(t)&&(isNaN(t)||t in r)?(l=t.charAt(0),c=t.substr(-1)==="%",o=t.indexOf("="),l==="<"||l===">"?(o>=0&&(t=t.replace(/=/,"")),(l==="<"?s._start:s.endTime(s._repeat>=0))+(parseFloat(t.substr(1))||0)*(c?(o<0?s:i).totalDuration()/100:1)):o<0?(t in r||(r[t]=a),r[t]):(l=parseFloat(t.charAt(o-1)+t.substr(o+1)),c&&i&&(l=l/100*(vn(i)?i[0]:i).totalDuration()),o>1?n(e,t.substr(0,o-1),i)+l:a+l)):t==null?a:+t},ka=function(e,t,i){var r=Ki(t[1]),s=(r?2:1)+(e<2?0:1),a=t[s],o,l;if(r&&(a.duration=t[1]),a.parent=i,e){for(o=a,l=i;l&&!("immediateRender"in o);)o=l.vars.defaults||{},l=Cn(l.vars.inherit)&&l.parent;a.immediateRender=Cn(o.immediateRender),e<2?a.runBackwards=1:a.startAt=t[s-1]}return new jt(t[0],a,t[s+1])},Rr=function(e,t){return e||e===0?t(e):t},to=function(e,t,i){return i<e?e:i>t?t:i},gn=function(e,t){return!cn(e)||!(t=o2.exec(e))?"":t[1]},x2=function(e,t,i){return Rr(i,function(r){return to(e,t,r)})},Uh=[].slice,O0=function(e,t){return e&&Li(e)&&"length"in e&&(!t&&!e.length||e.length-1 in e&&Li(e[0]))&&!e.nodeType&&e!==Mi},y2=function(e,t,i){return i===void 0&&(i=[]),e.forEach(function(r){var s;return cn(r)&&!t||O0(r,1)?(s=i).push.apply(s,ii(r)):i.push(r)})||i},ii=function(e,t,i){return It&&!t&&It.selector?It.selector(e):cn(e)&&!i&&(Rh||!qs())?Uh.call((t||ff).querySelectorAll(e),0):vn(e)?y2(e,i):O0(e)?Uh.call(e,0):e?[e]:[]},Lh=function(e){return e=ii(e)[0]||Wa("Invalid scope")||{},function(t){var i=e.current||e.nativeElement||e;return ii(t,i.querySelectorAll?i:i===e?Wa("Invalid scope")||ff.createElement("div"):e)}},B0=function(e){return e.sort(function(){return .5-Math.random()})},k0=function(e){if(Ht(e))return e;var t=Li(e)?e:{each:e},i=Yr(t.ease),r=t.from||0,s=parseFloat(t.base)||0,a={},o=r>0&&r<1,l=isNaN(r)||o,c=t.axis,u=r,f=r;return cn(r)?u=f={center:.5,edges:.5,end:1}[r]||0:!o&&l&&(u=r[0],f=r[1]),function(h,d,m){var g=(m||t).length,p=a[g],_,v,b,S,E,M,T,x,y;if(!p){if(y=t.grid==="auto"?0:(t.grid||[1,ni])[1],!y){for(T=-ni;T<(T=m[y++].getBoundingClientRect().left)&&y<g;);y<g&&y--}for(p=a[g]=[],_=l?Math.min(y,g)*u-.5:r%y,v=y===ni?0:l?g*f/y-.5:r/y|0,T=0,x=ni,M=0;M<g;M++)b=M%y-_,S=v-(M/y|0),p[M]=E=c?Math.abs(c==="y"?S:b):b0(b*b+S*S),E>T&&(T=E),E<x&&(x=E);r==="random"&&B0(p),p.max=T-x,p.min=x,p.v=g=(parseFloat(t.amount)||parseFloat(t.each)*(y>g?g-1:c?c==="y"?g/y:y:Math.max(y,g/y))||0)*(r==="edges"?-1:1),p.b=g<0?s-g:s,p.u=gn(t.amount||t.each)||0,i=i&&g<0?L2(i):i}return g=(p[h]-p.min)/p.max||0,Ot(p.b+(i?i(g):g)*p.v)+p.u}},Ih=function(e){var t=Math.pow(10,((e+"").split(".")[1]||"").length);return function(i){var r=Ot(Math.round(parseFloat(i)/e)*e*t);return(r-r%1)/t+(Ki(i)?0:gn(i))}},z0=function(e,t){var i=vn(e),r,s;return!i&&Li(e)&&(r=i=e.radius||ni,e.values?(e=ii(e.values),(s=!Ki(e[0]))&&(r*=r)):e=Ih(e.increment)),Rr(t,i?Ht(e)?function(a){return s=e(a),Math.abs(s-a)<=r?s:a}:function(a){for(var o=parseFloat(s?a.x:a),l=parseFloat(s?a.y:0),c=ni,u=0,f=e.length,h,d;f--;)s?(h=e[f].x-o,d=e[f].y-l,h=h*h+d*d):h=Math.abs(e[f]-o),h<c&&(c=h,u=f);return u=!r||c<=r?e[u]:a,s||u===a||Ki(a)?u:u+gn(a)}:Ih(e))},G0=function(e,t,i,r){return Rr(vn(e)?!t:i===!0?!!(i=0):!r,function(){return vn(e)?e[~~(Math.random()*e.length)]:(i=i||1e-5)&&(r=i<1?Math.pow(10,(i+"").length-2):1)&&Math.floor(Math.round((e-i/2+Math.random()*(t-e+i*.99))/i)*i*r)/r})},b2=function(){for(var e=arguments.length,t=new Array(e),i=0;i<e;i++)t[i]=arguments[i];return function(r){return t.reduce(function(s,a){return a(s)},r)}},M2=function(e,t){return function(i){return e(parseFloat(i))+(t||gn(i))}},S2=function(e,t,i){return V0(e,t,0,1,i)},H0=function(e,t,i){return Rr(i,function(r){return e[~~t(r)]})},T2=function n(e,t,i){var r=t-e;return vn(e)?H0(e,n(0,e.length),t):Rr(i,function(s){return(r+(s-e)%r)%r+e})},E2=function n(e,t,i){var r=t-e,s=r*2;return vn(e)?H0(e,n(0,e.length-1),t):Rr(i,function(a){return a=(s+(a-e)%s)%s||0,e+(a>r?s-a:a)})},ja=function(e){return e.replace(r2,function(t){var i=t.indexOf("[")+1,r=t.substring(i||7,i?t.indexOf("]"):t.length-1).split(s2);return G0(i?r:+r[0],i?0:+r[1],+r[2]||1e-5)})},V0=function(e,t,i,r,s){var a=t-e,o=r-i;return Rr(s,function(l){return i+((l-e)/a*o||0)})},w2=function n(e,t,i,r){var s=isNaN(e+t)?0:function(d){return(1-d)*e+d*t};if(!s){var a=cn(e),o={},l,c,u,f,h;if(i===!0&&(r=1)&&(i=null),a)e={p:e},t={p:t};else if(vn(e)&&!vn(t)){for(u=[],f=e.length,h=f-2,c=1;c<f;c++)u.push(n(e[c-1],e[c]));f--,s=function(m){m*=f;var g=Math.min(h,~~m);return u[g](m-g)},i=t}else r||(e=Xs(vn(e)?[]:{},e));if(!u){for(l in t)vf.call(o,e,l,"get",t[l]);s=function(m){return Mf(m,o)||(a?e.p:e)}}}return Rr(i,s)},Pp=function(e,t,i){var r=e.labels,s=ni,a,o,l;for(a in r)o=r[a]-t,o<0==!!i&&o&&s>(o=Math.abs(o))&&(l=a,s=o);return l},Wn=function(e,t,i){var r=e.vars,s=r[t],a=It,o=e._ctx,l,c,u;if(s)return l=r[t+"Params"],c=r.callbackScope||e,i&&xr.length&&bl(),o&&(It=o),u=l?s.apply(c,l):s.call(c),It=a,u},Ua=function(e){return Sr(e),e.scrollTrigger&&e.scrollTrigger.kill(!!fn),e.progress()<1&&Wn(e,"onInterrupt"),e},Ls,W0=[],X0=function(e){if(e)if(e=!e.name&&e.default||e,hf()||e.headless){var t=e.name,i=Ht(e),r=t&&!i&&e.init?function(){this._props=[]}:e,s={init:Xa,render:Mf,add:vf,kill:V2,modifier:H2,rawVars:0},a={targetTest:0,get:0,getSetter:bf,aliases:{},register:0};if(qs(),e!==r){if(Gn[t])return;Kn(r,Kn(Ml(e,s),a)),Xs(r.prototype,Xs(s,Ml(e,a))),Gn[r.prop=t]=r,e.targetTest&&(sl.push(r),pf[t]=1),t=(t==="css"?"CSS":t.charAt(0).toUpperCase()+t.substr(1))+"Plugin"}A0(t,r),e.register&&e.register(Ln,r,Dn)}else W0.push(e)},wt=255,La={aqua:[0,wt,wt],lime:[0,wt,0],silver:[192,192,192],black:[0,0,0],maroon:[128,0,0],teal:[0,128,128],blue:[0,0,wt],navy:[0,0,128],white:[wt,wt,wt],olive:[128,128,0],yellow:[wt,wt,0],orange:[wt,165,0],gray:[128,128,128],purple:[128,0,128],green:[0,128,0],red:[wt,0,0],pink:[wt,192,203],cyan:[0,wt,wt],transparent:[wt,wt,wt,0]},Kc=function(e,t,i){return e+=e<0?1:e>1?-1:0,(e*6<1?t+(i-t)*e*6:e<.5?i:e*3<2?t+(i-t)*(2/3-e)*6:t)*wt+.5|0},j0=function(e,t,i){var r=e?Ki(e)?[e>>16,e>>8&wt,e&wt]:0:La.black,s,a,o,l,c,u,f,h,d,m;if(!r){if(e.substr(-1)===","&&(e=e.substr(0,e.length-1)),La[e])r=La[e];else if(e.charAt(0)==="#"){if(e.length<6&&(s=e.charAt(1),a=e.charAt(2),o=e.charAt(3),e="#"+s+s+a+a+o+o+(e.length===5?e.charAt(4)+e.charAt(4):"")),e.length===9)return r=parseInt(e.substr(1,6),16),[r>>16,r>>8&wt,r&wt,parseInt(e.substr(7),16)/255];e=parseInt(e.substr(1),16),r=[e>>16,e>>8&wt,e&wt]}else if(e.substr(0,3)==="hsl"){if(r=m=e.match(Ep),!t)l=+r[0]%360/360,c=+r[1]/100,u=+r[2]/100,a=u<=.5?u*(c+1):u+c-u*c,s=u*2-a,r.length>3&&(r[3]*=1),r[0]=Kc(l+1/3,s,a),r[1]=Kc(l,s,a),r[2]=Kc(l-1/3,s,a);else if(~e.indexOf("="))return r=e.match(S0),i&&r.length<4&&(r[3]=1),r}else r=e.match(Ep)||La.transparent;r=r.map(Number)}return t&&!m&&(s=r[0]/wt,a=r[1]/wt,o=r[2]/wt,f=Math.max(s,a,o),h=Math.min(s,a,o),u=(f+h)/2,f===h?l=c=0:(d=f-h,c=u>.5?d/(2-f-h):d/(f+h),l=f===s?(a-o)/d+(a<o?6:0):f===a?(o-s)/d+2:(s-a)/d+4,l*=60),r[0]=~~(l+.5),r[1]=~~(c*100+.5),r[2]=~~(u*100+.5)),i&&r.length<4&&(r[3]=1),r},Y0=function(e){var t=[],i=[],r=-1;return e.split(yr).forEach(function(s){var a=s.match(Us)||[];t.push.apply(t,a),i.push(r+=a.length+1)}),t.c=i,t},Dp=function(e,t,i){var r="",s=(e+r).match(yr),a=t?"hsla(":"rgba(",o=0,l,c,u,f;if(!s)return e;if(s=s.map(function(h){return(h=j0(h,t,1))&&a+(t?h[0]+","+h[1]+"%,"+h[2]+"%,"+h[3]:h.join(","))+")"}),i&&(u=Y0(e),l=i.c,l.join(r)!==u.c.join(r)))for(c=e.replace(yr,"1").split(Us),f=c.length-1;o<f;o++)r+=c[o]+(~l.indexOf(o)?s.shift()||a+"0,0,0,0)":(u.length?u:s.length?s:i).shift());if(!c)for(c=e.split(yr),f=c.length-1;o<f;o++)r+=c[o]+s[o];return r+c[f]},yr=(function(){var n="(?:\\b(?:(?:rgb|rgba|hsl|hsla)\\(.+?\\))|\\B#(?:[0-9a-f]{3,4}){1,2}\\b",e;for(e in La)n+="|"+e+"\\b";return new RegExp(n+")","gi")})(),A2=/hsl[a]?\(/,q0=function(e){var t=e.join(" "),i;if(yr.lastIndex=0,yr.test(t))return i=A2.test(t),e[1]=Dp(e[1],i),e[0]=Dp(e[0],i,Y0(e[1])),!0},Ya,Vn=(function(){var n=Date.now,e=500,t=33,i=n(),r=i,s=1e3/240,a=s,o=[],l,c,u,f,h,d,m=function g(p){var _=n()-r,v=p===!0,b,S,E,M;if((_>e||_<0)&&(i+=_-t),r+=_,E=r-i,b=E-a,(b>0||v)&&(M=++f.frame,h=E-f.time*1e3,f.time=E=E/1e3,a+=b+(b>=s?4:s-b),S=1),v||(l=c(g)),S)for(d=0;d<o.length;d++)o[d](E,h,M,p)};return f={time:0,frame:0,tick:function(){m(!0)},deltaRatio:function(p){return h/(1e3/(p||60))},wake:function(){E0&&(!Rh&&hf()&&(Mi=Rh=window,ff=Mi.document||{},qn.gsap=Ln,(Mi.gsapVersions||(Mi.gsapVersions=[])).push(Ln.version),w0(yl||Mi.GreenSockGlobals||!Mi.gsap&&Mi||{}),W0.forEach(X0)),u=typeof requestAnimationFrame<"u"&&requestAnimationFrame,l&&f.sleep(),c=u||function(p){return setTimeout(p,a-f.time*1e3+1|0)},Ya=1,m(2))},sleep:function(){(u?cancelAnimationFrame:clearTimeout)(l),Ya=0,c=Xa},lagSmoothing:function(p,_){e=p||1/0,t=Math.min(_||33,e)},fps:function(p){s=1e3/(p||240),a=f.time*1e3+s},add:function(p,_,v){var b=_?function(S,E,M,T){p(S,E,M,T),f.remove(b)}:p;return f.remove(p),o[v?"unshift":"push"](b),qs(),b},remove:function(p,_){~(_=o.indexOf(p))&&o.splice(_,1)&&d>=_&&d--},_listeners:o},f})(),qs=function(){return!Ya&&Vn.wake()},dt={},R2=/^[\d.\-M][\d.\-,\s]/,C2=/["']/g,P2=function(e){for(var t={},i=e.substr(1,e.length-3).split(":"),r=i[0],s=1,a=i.length,o,l,c;s<a;s++)l=i[s],o=s!==a-1?l.lastIndexOf(","):l.length,c=l.substr(0,o),t[r]=isNaN(c)?c.replace(C2,"").trim():+c,r=l.substr(o+1).trim();return t},D2=function(e){var t=e.indexOf("(")+1,i=e.indexOf(")"),r=e.indexOf("(",t);return e.substring(t,~r&&r<i?e.indexOf(")",i+1):i)},U2=function(e){var t=(e+"").split("("),i=dt[t[0]];return i&&t.length>1&&i.config?i.config.apply(null,~e.indexOf("{")?[P2(t[1])]:D2(e).split(",").map(D0)):dt._CE&&R2.test(e)?dt._CE("",e):i},L2=function(e){return function(t){return 1-e(1-t)}},Yr=function(e,t){return e&&(Ht(e)?e:dt[e]||U2(e))||t},ts=function(e,t,i,r){i===void 0&&(i=function(l){return 1-t(1-l)}),r===void 0&&(r=function(l){return l<.5?t(l*2)/2:1-t((1-l)*2)/2});var s={easeIn:t,easeOut:i,easeInOut:r},a;return Pn(e,function(o){dt[o]=qn[o]=s,dt[a=o.toLowerCase()]=i;for(var l in s)dt[a+(l==="easeIn"?".in":l==="easeOut"?".out":".inOut")]=dt[o+"."+l]=s[l]}),s},K0=function(e){return function(t){return t<.5?(1-e(1-t*2))/2:.5+e((t-.5)*2)/2}},Zc=function n(e,t,i){var r=t>=1?t:1,s=(i||(e?.3:.45))/(t<1?t:1),a=s/Ah*(Math.asin(1/r)||0),o=function(u){return u===1?1:r*Math.pow(2,-10*u)*i2((u-a)*s)+1},l=e==="out"?o:e==="in"?function(c){return 1-o(1-c)}:K0(o);return s=Ah/s,l.config=function(c,u){return n(e,c,u)},l},$c=function n(e,t){t===void 0&&(t=1.70158);var i=function(a){return a?--a*a*((t+1)*a+t)+1:0},r=e==="out"?i:e==="in"?function(s){return 1-i(1-s)}:K0(i);return r.config=function(s){return n(e,s)},r};Pn("Linear,Quad,Cubic,Quart,Quint,Strong",function(n,e){var t=e<5?e+1:e;ts(n+",Power"+(t-1),e?function(i){return Math.pow(i,t)}:function(i){return i},function(i){return 1-Math.pow(1-i,t)},function(i){return i<.5?Math.pow(i*2,t)/2:1-Math.pow((1-i)*2,t)/2})});dt.Linear.easeNone=dt.none=dt.Linear.easeIn;ts("Elastic",Zc("in"),Zc("out"),Zc());(function(n,e){var t=1/e,i=2*t,r=2.5*t,s=function(o){return o<t?n*o*o:o<i?n*Math.pow(o-1.5/e,2)+.75:o<r?n*(o-=2.25/e)*o+.9375:n*Math.pow(o-2.625/e,2)+.984375};ts("Bounce",function(a){return 1-s(1-a)},s)})(7.5625,2.75);ts("Expo",function(n){return Math.pow(2,10*(n-1))*n+n*n*n*n*n*n*(1-n)});ts("Circ",function(n){return-(b0(1-n*n)-1)});ts("Sine",function(n){return n===1?1:-n2(n*e2)+1});ts("Back",$c("in"),$c("out"),$c());dt.SteppedEase=dt.steps=qn.SteppedEase={config:function(e,t){e===void 0&&(e=1);var i=1/e,r=e+(t?0:1),s=t?1:0,a=1-Ct;return function(o){return((r*to(0,a,o)|0)+s)*i}}};Va.ease=dt["quad.out"];Pn("onComplete,onUpdate,onStart,onRepeat,onReverseComplete,onInterrupt",function(n){return mf+=n+","+n+"Params,"});var Z0=function(e,t){this.id=t2++,e._gsap=this,this.target=e,this.harness=t,this.get=t?t.get:C0,this.set=t?t.getSetter:bf},qa=(function(){function n(t){this.vars=t,this._delay=+t.delay||0,(this._repeat=t.repeat===1/0?-2:t.repeat||0)&&(this._rDelay=t.repeatDelay||0,this._yoyo=!!t.yoyo||!!t.yoyoEase),this._ts=1,Ys(this,+t.duration,1,1),this.data=t.data,It&&(this._ctx=It,It.data.push(this)),Ya||Vn.wake()}var e=n.prototype;return e.delay=function(i){return i||i===0?(this.parent&&this.parent.smoothChildTiming&&this.startTime(this._start+i-this._delay),this._delay=i,this):this._delay},e.duration=function(i){return arguments.length?this.totalDuration(this._repeat>0?i+(i+this._rDelay)*this._repeat:i):this.totalDuration()&&this._dur},e.totalDuration=function(i){return arguments.length?(this._dirty=0,Ys(this,this._repeat<0?i:(i-this._repeat*this._rDelay)/(this._repeat+1))):this._tDur},e.totalTime=function(i,r){if(qs(),!arguments.length)return this._tTime;var s=this._dp;if(s&&s.smoothChildTiming&&this._ts){for(Gl(this,i),!s._dp||s.parent||I0(s,this);s&&s.parent;)s.parent._time!==s._start+(s._ts>=0?s._tTime/s._ts:(s.totalDuration()-s._tTime)/-s._ts)&&s.totalTime(s._tTime,!0),s=s.parent;!this.parent&&this._dp.autoRemoveChildren&&(this._ts>0&&i<this._tDur||this._ts<0&&i>0||!this._tDur&&!i)&&wi(this._dp,this,this._start-this._delay)}return(this._tTime!==i||!this._dur&&!r||this._initted&&Math.abs(this._zTime)===Ct||!this._initted&&this._dur&&i||!i&&!this._initted&&(this.add||this._ptLookup))&&(this._ts||(this._pTime=i),P0(this,i,r)),this},e.time=function(i,r){return arguments.length?this.totalTime(Math.min(this.totalDuration(),i+Rp(this))%(this._dur+this._rDelay)||(i?this._dur:0),r):this._time},e.totalProgress=function(i,r){return arguments.length?this.totalTime(this.totalDuration()*i,r):this.totalDuration()?Math.min(1,this._tTime/this._tDur):this.rawTime()>=0&&this._initted?1:0},e.progress=function(i,r){return arguments.length?this.totalTime(this.duration()*(this._yoyo&&!(this.iteration()&1)?1-i:i)+Rp(this),r):this.duration()?Math.min(1,this._time/this._dur):this.rawTime()>0?1:0},e.iteration=function(i,r){var s=this.duration()+this._rDelay;return arguments.length?this.totalTime(this._time+(i-1)*s,r):this._repeat?js(this._tTime,s)+1:1},e.timeScale=function(i,r){if(!arguments.length)return this._rts===-Ct?0:this._rts;if(this._rts===i)return this;var s=this.parent&&this._ts?Sl(this.parent._time,this):this._tTime;return this._rts=+i||0,this._ts=this._ps||i===-Ct?0:this._rts,this.totalTime(to(-Math.abs(this._delay),this.totalDuration(),s),r!==!1),zl(this),d2(this)},e.paused=function(i){return arguments.length?(this._ps!==i&&(this._ps=i,i?(this._pTime=this._tTime||Math.max(-this._delay,this.rawTime()),this._ts=this._act=0):(qs(),this._ts=this._rts,this.totalTime(this.parent&&!this.parent.smoothChildTiming?this.rawTime():this._tTime||this._pTime,this.progress()===1&&Math.abs(this._zTime)!==Ct&&(this._tTime-=Ct)))),this):this._ps},e.startTime=function(i){if(arguments.length){this._start=Ot(i);var r=this.parent||this._dp;return r&&(r._sort||!this.parent)&&wi(r,this,this._start-this._delay),this}return this._start},e.endTime=function(i){return this._start+(Cn(i)?this.totalDuration():this.duration())/Math.abs(this._ts||1)},e.rawTime=function(i){var r=this.parent||this._dp;return r?i&&(!this._ts||this._repeat&&this._time&&this.totalProgress()<1)?this._tTime%(this._dur+this._rDelay):this._ts?Sl(r.rawTime(i),this):this._tTime:this._tTime},e.revert=function(i){i===void 0&&(i=c2);var r=fn;return fn=i,_f(this)&&(this.timeline&&this.timeline.revert(i),this.totalTime(-.01,i.suppressEvents)),this.data!=="nested"&&i.kill!==!1&&this.kill(),fn=r,this},e.globalTime=function(i){for(var r=this,s=arguments.length?i:r.rawTime();r;)s=r._start+s/(Math.abs(r._ts)||1),r=r._dp;return!this.parent&&this._sat?this._sat.globalTime(i):s},e.repeat=function(i){return arguments.length?(this._repeat=i===1/0?-2:i,Cp(this)):this._repeat===-2?1/0:this._repeat},e.repeatDelay=function(i){if(arguments.length){var r=this._time;return this._rDelay=i,Cp(this),r?this.time(r):this}return this._rDelay},e.yoyo=function(i){return arguments.length?(this._yoyo=i,this):this._yoyo},e.seek=function(i,r){return this.totalTime(Qn(this,i),Cn(r))},e.restart=function(i,r){return this.play().totalTime(i?-this._delay:0,Cn(r)),this._dur||(this._zTime=-Ct),this},e.play=function(i,r){return i!=null&&this.seek(i,r),this.reversed(!1).paused(!1)},e.reverse=function(i,r){return i!=null&&this.seek(i||this.totalDuration(),r),this.reversed(!0).paused(!1)},e.pause=function(i,r){return i!=null&&this.seek(i,r),this.paused(!0)},e.resume=function(){return this.paused(!1)},e.reversed=function(i){return arguments.length?(!!i!==this.reversed()&&this.timeScale(-this._rts||(i?-Ct:0)),this):this._rts<0},e.invalidate=function(){return this._initted=this._act=0,this._zTime=-Ct,this},e.isActive=function(){var i=this.parent||this._dp,r=this._start,s;return!!(!i||this._ts&&this._initted&&i.isActive()&&(s=i.rawTime(!0))>=r&&s<this.endTime(!0)-Ct)},e.eventCallback=function(i,r,s){var a=this.vars;return arguments.length>1?(r?(a[i]=r,s&&(a[i+"Params"]=s),i==="onUpdate"&&(this._onUpdate=r)):delete a[i],this):a[i]},e.then=function(i){var r=this,s=r._prom;return new Promise(function(a){var o=Ht(i)?i:U0,l=function(){var u=r.then;r.then=null,s&&s(),Ht(o)&&(o=o(r))&&(o.then||o===r)&&(r.then=u),a(o),r.then=u};r._initted&&r.totalProgress()===1&&r._ts>=0||!r._tTime&&r._ts<0?l():r._prom=l})},e.kill=function(){Ua(this)},n})();Kn(qa.prototype,{_time:0,_start:0,_end:0,_tTime:0,_tDur:0,_dirty:0,_repeat:0,_yoyo:!1,parent:null,_initted:!1,_rDelay:0,_ts:1,_dp:0,ratio:0,_zTime:-Ct,_prom:0,_ps:!1,_rts:1});var Rn=(function(n){y0(e,n);function e(i,r){var s;return i===void 0&&(i={}),s=n.call(this,i)||this,s.labels={},s.smoothChildTiming=!!i.smoothChildTiming,s.autoRemoveChildren=!!i.autoRemoveChildren,s._sort=Cn(i.sortChildren),Bt&&wi(i.parent||Bt,Gi(s),r),i.reversed&&s.reverse(),i.paused&&s.paused(!0),i.scrollTrigger&&F0(Gi(s),i.scrollTrigger),s}var t=e.prototype;return t.to=function(r,s,a){return ka(0,arguments,this),this},t.from=function(r,s,a){return ka(1,arguments,this),this},t.fromTo=function(r,s,a,o){return ka(2,arguments,this),this},t.set=function(r,s,a){return s.duration=0,s.parent=this,Ba(s).repeatDelay||(s.repeat=0),s.immediateRender=!!s.immediateRender,new jt(r,s,Qn(this,a),1),this},t.call=function(r,s,a){return wi(this,jt.delayedCall(0,r,s),a)},t.staggerTo=function(r,s,a,o,l,c,u){return a.duration=s,a.stagger=a.stagger||o,a.onComplete=c,a.onCompleteParams=u,a.parent=this,new jt(r,a,Qn(this,l)),this},t.staggerFrom=function(r,s,a,o,l,c,u){return a.runBackwards=1,Ba(a).immediateRender=Cn(a.immediateRender),this.staggerTo(r,s,a,o,l,c,u)},t.staggerFromTo=function(r,s,a,o,l,c,u,f){return o.startAt=a,Ba(o).immediateRender=Cn(o.immediateRender),this.staggerTo(r,s,o,l,c,u,f)},t.render=function(r,s,a){var o=this._time,l=this._dirty?this.totalDuration():this._tDur,c=this._dur,u=r<=0?0:Ot(r),f=this._zTime<0!=r<0&&(this._initted||!c),h,d,m,g,p,_,v,b,S,E,M,T;if(this!==Bt&&u>l&&r>=0&&(u=l),u!==this._tTime||a||f){if(o!==this._time&&c&&(u+=this._time-o,r+=this._time-o),h=u,S=this._start,b=this._ts,_=!b,f&&(c||(o=this._zTime),(r||!s)&&(this._zTime=r)),this._repeat){if(M=this._yoyo,p=c+this._rDelay,this._repeat<-1&&r<0)return this.totalTime(p*100+r,s,a);if(h=Ot(u%p),u===l?(g=this._repeat,h=c):(E=Ot(u/p),g=~~E,g&&g===E&&(h=c,g--),h>c&&(h=c)),E=js(this._tTime,p),!o&&this._tTime&&E!==g&&this._tTime-E*p-this._dur<=0&&(E=g),M&&g&1&&(h=c-h,T=1),g!==E&&!this._lock){var x=M&&E&1,y=x===(M&&g&1);if(g<E&&(x=!x),o=x?0:u%c?c:u,this._lock=1,this.render(o||(T?0:Ot(g*p)),s,!c)._lock=0,this._tTime=u,!s&&this.parent&&Wn(this,"onRepeat"),this.vars.repeatRefresh&&!T&&(this.invalidate()._lock=1,E=g),o&&o!==this._time||_!==!this._ts||this.vars.onRepeat&&!this.parent&&!this._act)return this;if(c=this._dur,l=this._tDur,y&&(this._lock=2,o=x?c:-1e-4,this.render(o,!0),this.vars.repeatRefresh&&!T&&this.invalidate()),this._lock=0,!this._ts&&!_)return this}}if(this._hasPause&&!this._forcing&&this._lock<2&&(v=_2(this,Ot(o),Ot(h)),v&&(u-=h-(h=v._start))),this._tTime=u,this._time=h,this._act=!!b,this._initted||(this._onUpdate=this.vars.onUpdate,this._initted=1,this._zTime=r,o=0),!o&&u&&c&&!s&&!E&&(Wn(this,"onStart"),this._tTime!==u))return this;if(h>=o&&r>=0)for(d=this._first;d;){if(m=d._next,(d._act||h>=d._start)&&d._ts&&v!==d){if(d.parent!==this)return this.render(r,s,a);if(d.render(d._ts>0?(h-d._start)*d._ts:(d._dirty?d.totalDuration():d._tDur)+(h-d._start)*d._ts,s,a),h!==this._time||!this._ts&&!_){v=0,m&&(u+=this._zTime=-Ct);break}}d=m}else{d=this._last;for(var w=r<0?r:h;d;){if(m=d._prev,(d._act||w<=d._end)&&d._ts&&v!==d){if(d.parent!==this)return this.render(r,s,a);if(d.render(d._ts>0?(w-d._start)*d._ts:(d._dirty?d.totalDuration():d._tDur)+(w-d._start)*d._ts,s,a||fn&&_f(d)),h!==this._time||!this._ts&&!_){v=0,m&&(u+=this._zTime=w?-Ct:Ct);break}}d=m}}if(v&&!s&&(this.pause(),v.render(h>=o?0:-Ct)._zTime=h>=o?1:-1,this._ts))return this._start=S,zl(this),this.render(r,s,a);this._onUpdate&&!s&&Wn(this,"onUpdate",!0),(u===l&&this._tTime>=this.totalDuration()||!u&&o)&&(S===this._start||Math.abs(b)!==Math.abs(this._ts))&&(this._lock||((r||!c)&&(u===l&&this._ts>0||!u&&this._ts<0)&&Sr(this,1),!s&&!(r<0&&!o)&&(u||o||!l)&&(Wn(this,u===l&&r>=0?"onComplete":"onReverseComplete",!0),this._prom&&!(u<l&&this.timeScale()>0)&&this._prom())))}return this},t.add=function(r,s){var a=this;if(Ki(s)||(s=Qn(this,s,r)),!(r instanceof qa)){if(vn(r))return r.forEach(function(o){return a.add(o,s)}),this;if(cn(r))return this.addLabel(r,s);if(Ht(r))r=jt.delayedCall(0,r);else return this}return this!==r?wi(this,r,s):this},t.getChildren=function(r,s,a,o){r===void 0&&(r=!0),s===void 0&&(s=!0),a===void 0&&(a=!0),o===void 0&&(o=-ni);for(var l=[],c=this._first;c;)c._start>=o&&(c instanceof jt?s&&l.push(c):(a&&l.push(c),r&&l.push.apply(l,c.getChildren(!0,s,a)))),c=c._next;return l},t.getById=function(r){for(var s=this.getChildren(1,1,1),a=s.length;a--;)if(s[a].vars.id===r)return s[a]},t.remove=function(r){return cn(r)?this.removeLabel(r):Ht(r)?this.killTweensOf(r):(r.parent===this&&kl(this,r),r===this._recent&&(this._recent=this._last),jr(this))},t.totalTime=function(r,s){return arguments.length?(this._forcing=1,!this._dp&&this._ts&&(this._start=Ot(Vn.time-(this._ts>0?r/this._ts:(this.totalDuration()-r)/-this._ts))),n.prototype.totalTime.call(this,r,s),this._forcing=0,this):this._tTime},t.addLabel=function(r,s){return this.labels[r]=Qn(this,s),this},t.removeLabel=function(r){return delete this.labels[r],this},t.addPause=function(r,s,a){var o=jt.delayedCall(0,s||Xa,a);return o.data="isPause",this._hasPause=1,wi(this,o,Qn(this,r))},t.removePause=function(r){var s=this._first;for(r=Qn(this,r);s;)s._start===r&&s.data==="isPause"&&Sr(s),s=s._next},t.killTweensOf=function(r,s,a){for(var o=this.getTweensOf(r,a),l=o.length;l--;)mr!==o[l]&&o[l].kill(r,s);return this},t.getTweensOf=function(r,s){for(var a=[],o=ii(r),l=this._first,c=Ki(s),u;l;)l instanceof jt?u2(l._targets,o)&&(c?(!mr||l._initted&&l._ts)&&l.globalTime(0)<=s&&l.globalTime(l.totalDuration())>s:!s||l.isActive())&&a.push(l):(u=l.getTweensOf(o,s)).length&&a.push.apply(a,u),l=l._next;return a},t.tweenTo=function(r,s){s=s||{};var a=this,o=Qn(a,r),l=s,c=l.startAt,u=l.onStart,f=l.onStartParams,h=l.immediateRender,d,m=jt.to(a,Kn({ease:s.ease||"none",lazy:!1,immediateRender:!1,time:o,overwrite:"auto",duration:s.duration||Math.abs((o-(c&&"time"in c?c.time:a._time))/a.timeScale())||Ct,onStart:function(){if(a.pause(),!d){var p=s.duration||Math.abs((o-(c&&"time"in c?c.time:a._time))/a.timeScale());m._dur!==p&&Ys(m,p,0,1).render(m._time,!0,!0),d=1}u&&u.apply(m,f||[])}},s));return h?m.render(0):m},t.tweenFromTo=function(r,s,a){return this.tweenTo(s,Kn({startAt:{time:Qn(this,r)}},a))},t.recent=function(){return this._recent},t.nextLabel=function(r){return r===void 0&&(r=this._time),Pp(this,Qn(this,r))},t.previousLabel=function(r){return r===void 0&&(r=this._time),Pp(this,Qn(this,r),1)},t.currentLabel=function(r){return arguments.length?this.seek(r,!0):this.previousLabel(this._time+Ct)},t.shiftChildren=function(r,s,a){a===void 0&&(a=0);var o=this._first,l=this.labels,c;for(r=Ot(r);o;)o._start>=a&&(o._start+=r,o._end+=r),o=o._next;if(s)for(c in l)l[c]>=a&&(l[c]+=r);return jr(this)},t.invalidate=function(r){var s=this._first;for(this._lock=0;s;)s.invalidate(r),s=s._next;return n.prototype.invalidate.call(this,r)},t.clear=function(r){r===void 0&&(r=!0);for(var s=this._first,a;s;)a=s._next,this.remove(s),s=a;return this._dp&&(this._time=this._tTime=this._pTime=0),r&&(this.labels={}),jr(this)},t.totalDuration=function(r){var s=0,a=this,o=a._last,l=ni,c,u,f;if(arguments.length)return a.timeScale((a._repeat<0?a.duration():a.totalDuration())/(a.reversed()?-r:r));if(a._dirty){for(f=a.parent;o;)c=o._prev,o._dirty&&o.totalDuration(),u=o._start,u>l&&a._sort&&o._ts&&!a._lock?(a._lock=1,wi(a,o,u-o._delay,1)._lock=0):l=u,u<0&&o._ts&&(s-=u,(!f&&!a._dp||f&&f.smoothChildTiming)&&(a._start+=Ot(u/a._ts),a._time-=u,a._tTime-=u),a.shiftChildren(-u,!1,-1/0),l=0),o._end>s&&o._ts&&(s=o._end),o=c;Ys(a,a===Bt&&a._time>s?a._time:s,1,1),a._dirty=0}return a._tDur},e.updateRoot=function(r){if(Bt._ts&&(P0(Bt,Sl(r,Bt)),R0=Vn.frame),Vn.frame>=wp){wp+=jn.autoSleep||120;var s=Bt._first;if((!s||!s._ts)&&jn.autoSleep&&Vn._listeners.length<2){for(;s&&!s._ts;)s=s._next;s||Vn.sleep()}}},e})(qa);Kn(Rn.prototype,{_lock:0,_hasPause:0,_forcing:0});var I2=function(e,t,i,r,s,a,o){var l=new Dn(this._pt,e,t,0,1,ng,null,s),c=0,u=0,f,h,d,m,g,p,_,v;for(l.b=i,l.e=r,i+="",r+="",(_=~r.indexOf("random("))&&(r=ja(r)),a&&(v=[i,r],a(v,e,t),i=v[0],r=v[1]),h=i.match(Yc)||[];f=Yc.exec(r);)m=f[0],g=r.substring(c,f.index),d?d=(d+1)%5:g.substr(-5)==="rgba("&&(d=1),m!==h[u++]&&(p=parseFloat(h[u-1])||0,l._pt={_next:l._pt,p:g||u===1?g:",",s:p,c:m.charAt(1)==="="?Ns(p,m)-p:parseFloat(m)-p,m:d&&d<4?Math.round:0},c=Yc.lastIndex);return l.c=c<r.length?r.substring(c,r.length):"",l.fp=o,(T0.test(r)||_)&&(l.e=0),this._pt=l,l},vf=function(e,t,i,r,s,a,o,l,c,u){Ht(r)&&(r=r(s||0,e,a));var f=e[t],h=i!=="get"?i:Ht(f)?c?e[t.indexOf("set")||!Ht(e["get"+t.substr(3)])?t:"get"+t.substr(3)](c):e[t]():f,d=Ht(f)?c?k2:eg:yf,m;if(cn(r)&&(~r.indexOf("random(")&&(r=ja(r)),r.charAt(1)==="="&&(m=Ns(h,r)+(gn(h)||0),(m||m===0)&&(r=m))),!u||h!==r||Fh)return!isNaN(h*r)&&r!==""?(m=new Dn(this._pt,e,t,+h||0,r-(h||0),typeof f=="boolean"?G2:tg,0,d),c&&(m.fp=c),o&&m.modifier(o,this,e),this._pt=m):(!f&&!(t in e)&&df(t,r),I2.call(this,e,t,h,r,d,l||jn.stringFilter,c))},F2=function(e,t,i,r,s){if(Ht(e)&&(e=za(e,s,t,i,r)),!Li(e)||e.style&&e.nodeType||vn(e)||M0(e))return cn(e)?za(e,s,t,i,r):e;var a={},o;for(o in e)a[o]=za(e[o],s,t,i,r);return a},$0=function(e,t,i,r,s,a){var o,l,c,u;if(Gn[e]&&(o=new Gn[e]).init(s,o.rawVars?t[e]:F2(t[e],r,s,a,i),i,r,a)!==!1&&(i._pt=l=new Dn(i._pt,s,e,0,1,o.render,o,0,o.priority),i!==Ls))for(c=i._ptLookup[i._targets.indexOf(s)],u=o._props.length;u--;)c[o._props[u]]=l;return o},mr,Fh,xf=function n(e,t,i){var r=e.vars,s=r.ease,a=r.startAt,o=r.immediateRender,l=r.lazy,c=r.onUpdate,u=r.runBackwards,f=r.yoyoEase,h=r.keyframes,d=r.autoRevert,m=e._dur,g=e._startAt,p=e._targets,_=e.parent,v=_&&_.data==="nested"?_.vars.targets:p,b=e._overwrite==="auto"&&!cf,S=e.timeline,E=r.easeReverse||f,M,T,x,y,w,C,R,L,U,I,F,N,Y;if(S&&(!h||!s)&&(s="none"),e._ease=Yr(s,Va.ease),e._rEase=E&&(Yr(E)||e._ease),e._from=!S&&!!r.runBackwards,e._from&&(e.ratio=1),!S||h&&!r.stagger){if(L=p[0]?Xr(p[0]).harness:0,N=L&&r[L.prop],M=Ml(r,pf),g&&(g._zTime<0&&g.progress(1),t<0&&u&&o&&!d?g.render(-1,!0):g.revert(u&&m?rl:l2),g._lazy=0),a){if(Sr(e._startAt=jt.set(p,Kn({data:"isStart",overwrite:!1,parent:_,immediateRender:!0,lazy:!g&&Cn(l),startAt:null,delay:0,onUpdate:c&&function(){return Wn(e,"onUpdate")},stagger:0},a))),e._startAt._dp=0,e._startAt._sat=e,t<0&&(fn||!o&&!d)&&e._startAt.revert(rl),o&&m&&t<=0&&i<=0){t&&(e._zTime=t);return}}else if(u&&m&&!g){if(t&&(o=!1),x=Kn({overwrite:!1,data:"isFromStart",lazy:o&&!g&&Cn(l),immediateRender:o,stagger:0,parent:_},M),N&&(x[L.prop]=N),Sr(e._startAt=jt.set(p,x)),e._startAt._dp=0,e._startAt._sat=e,t<0&&(fn?e._startAt.revert(rl):e._startAt.render(-1,!0)),e._zTime=t,!o)n(e._startAt,Ct,Ct);else if(!t)return}for(e._pt=e._ptCache=0,l=m&&Cn(l)||l&&!m,T=0;T<p.length;T++){if(w=p[T],R=w._gsap||gf(p)[T]._gsap,e._ptLookup[T]=I={},Ch[R.id]&&xr.length&&bl(),F=v===p?T:v.indexOf(w),L&&(U=new L).init(w,N||M,e,F,v)!==!1&&(e._pt=y=new Dn(e._pt,w,U.name,0,1,U.render,U,0,U.priority),U._props.forEach(function(j){I[j]=y}),U.priority&&(C=1)),!L||N)for(x in M)Gn[x]&&(U=$0(x,M,e,F,w,v))?U.priority&&(C=1):I[x]=y=vf.call(e,w,x,"get",M[x],F,v,0,r.stringFilter);e._op&&e._op[T]&&e.kill(w,e._op[T]),b&&e._pt&&(mr=e,Bt.killTweensOf(w,I,e.globalTime(t)),Y=!e.parent,mr=0),e._pt&&l&&(Ch[R.id]=1)}C&&ig(e),e._onInit&&e._onInit(e)}e._onUpdate=c,e._initted=(!e._op||e._pt)&&!Y,h&&t<=0&&S.render(ni,!0,!0)},N2=function(e,t,i,r,s,a,o,l){var c=(e._pt&&e._ptCache||(e._ptCache={}))[t],u,f,h,d;if(!c)for(c=e._ptCache[t]=[],h=e._ptLookup,d=e._targets.length;d--;){if(u=h[d][t],u&&u.d&&u.d._pt)for(u=u.d._pt;u&&u.p!==t&&u.fp!==t;)u=u._next;if(!u)return Fh=1,e.vars[t]="+=0",xf(e,o),Fh=0,l?Wa(t+" not eligible for reset. Try splitting into individual properties"):1;c.push(u)}for(d=c.length;d--;)f=c[d],u=f._pt||f,u.s=(r||r===0)&&!s?r:u.s+(r||0)+a*u.c,u.c=i-u.s,f.e&&(f.e=Wt(i)+gn(f.e)),f.b&&(f.b=u.s+gn(f.b))},O2=function(e,t){var i=e[0]?Xr(e[0]).harness:0,r=i&&i.aliases,s,a,o,l;if(!r)return t;s=Xs({},t);for(a in r)if(a in s)for(l=r[a].split(","),o=l.length;o--;)s[l[o]]=s[a];return s},B2=function(e,t,i,r){var s=t.ease||r||"power1.inOut",a,o;if(vn(t))o=i[e]||(i[e]=[]),t.forEach(function(l,c){return o.push({t:c/(t.length-1)*100,v:l,e:s})});else for(a in t)o=i[a]||(i[a]=[]),a==="ease"||o.push({t:parseFloat(e),v:t[a],e:s})},za=function(e,t,i,r,s){return Ht(e)?e.call(t,i,r,s):cn(e)&&~e.indexOf("random(")?ja(e):e},J0=mf+"repeat,repeatDelay,yoyo,repeatRefresh,yoyoEase,easeReverse,autoRevert",Q0={};Pn(J0+",id,stagger,delay,duration,paused,scrollTrigger",function(n){return Q0[n]=1});var jt=(function(n){y0(e,n);function e(i,r,s,a){var o;typeof r=="number"&&(s.duration=r,r=s,s=null),o=n.call(this,a?r:Ba(r))||this;var l=o.vars,c=l.duration,u=l.delay,f=l.immediateRender,h=l.stagger,d=l.overwrite,m=l.keyframes,g=l.defaults,p=l.scrollTrigger,_=r.parent||Bt,v=(vn(i)||M0(i)?Ki(i[0]):"length"in r)?[i]:ii(i),b,S,E,M,T,x,y,w;if(o._targets=v.length?gf(v):Wa("GSAP target "+i+" not found. https://gsap.com",!jn.nullTargetWarn)||[],o._ptLookup=[],o._overwrite=d,m||h||Wo(c)||Wo(u)){r=o.vars;var C=r.easeReverse||r.yoyoEase;if(b=o.timeline=new Rn({data:"nested",defaults:g||{},targets:_&&_.data==="nested"?_.vars.targets:v}),b.kill(),b.parent=b._dp=Gi(o),b._start=0,h||Wo(c)||Wo(u)){if(M=v.length,y=h&&k0(h),Li(h))for(T in h)~J0.indexOf(T)&&(w||(w={}),w[T]=h[T]);for(S=0;S<M;S++)E=Ml(r,Q0),E.stagger=0,C&&(E.easeReverse=C),w&&Xs(E,w),x=v[S],E.duration=+za(c,Gi(o),S,x,v),E.delay=(+za(u,Gi(o),S,x,v)||0)-o._delay,!h&&M===1&&E.delay&&(o._delay=u=E.delay,o._start+=u,E.delay=0),b.to(x,E,y?y(S,x,v):0),b._ease=dt.none;b.duration()?c=u=0:o.timeline=0}else if(m){Ba(Kn(b.vars.defaults,{ease:"none"})),b._ease=Yr(m.ease||r.ease||"none");var R=0,L,U,I;if(vn(m))m.forEach(function(F){return b.to(v,F,">")}),b.duration();else{E={};for(T in m)T==="ease"||T==="easeEach"||B2(T,m[T],E,m.easeEach);for(T in E)for(L=E[T].sort(function(F,N){return F.t-N.t}),R=0,S=0;S<L.length;S++)U=L[S],I={ease:U.e,duration:(U.t-(S?L[S-1].t:0))/100*c},I[T]=U.v,b.to(v,I,R),R+=I.duration;b.duration()<c&&b.to({},{duration:c-b.duration()})}}c||o.duration(c=b.duration())}else o.timeline=0;return d===!0&&!cf&&(mr=Gi(o),Bt.killTweensOf(v),mr=0),wi(_,Gi(o),s),r.reversed&&o.reverse(),r.paused&&o.paused(!0),(f||!c&&!m&&o._start===Ot(_._time)&&Cn(f)&&p2(Gi(o))&&_.data!=="nested")&&(o._tTime=-Ct,o.render(Math.max(0,-u)||0)),p&&F0(Gi(o),p),o}var t=e.prototype;return t.render=function(r,s,a){var o=this._time,l=this._tDur,c=this._dur,u=r<0,f=r>l-Ct&&!u?l:r<Ct?0:r,h,d,m,g,p,_,v,b;if(!c)g2(this,r,s,a);else if(f!==this._tTime||!r||a||!this._initted&&this._tTime||this._startAt&&this._zTime<0!==u||this._lazy){if(h=f,b=this.timeline,this._repeat){if(g=c+this._rDelay,this._repeat<-1&&u)return this.totalTime(g*100+r,s,a);if(h=Ot(f%g),f===l?(m=this._repeat,h=c):(p=Ot(f/g),m=~~p,m&&m===p?(h=c,m--):h>c&&(h=c)),_=this._yoyo&&m&1,_&&(h=c-h),p=js(this._tTime,g),h===o&&!a&&this._initted&&m===p)return this._tTime=f,this;m!==p&&this.vars.repeatRefresh&&!_&&!this._lock&&h!==g&&this._initted&&(this._lock=a=1,this.render(Ot(g*m),!0).invalidate()._lock=0)}if(!this._initted){if(N0(this,u?r:h,a,s,f))return this._tTime=0,this;if(o!==this._time&&!(a&&this.vars.repeatRefresh&&m!==p))return this;if(c!==this._dur)return this.render(r,s,a)}if(this._rEase){var S=h<o;if(S!==this._inv){var E=S?o:c-o;this._inv=S,this._from&&(this.ratio=1-this.ratio),this._invRatio=this.ratio,this._invTime=o,this._invRecip=E?(S?-1:1)/E:0,this._invScale=S?-this.ratio:1-this.ratio,this._invEase=S?this._rEase:this._ease}this.ratio=v=this._invRatio+this._invScale*this._invEase((h-this._invTime)*this._invRecip)}else this.ratio=v=this._ease(h/c);if(this._from&&(this.ratio=v=1-v),this._tTime=f,this._time=h,!this._act&&this._ts&&(this._act=1,this._lazy=0),!o&&f&&!s&&!p&&(Wn(this,"onStart"),this._tTime!==f))return this;for(d=this._pt;d;)d.r(v,d.d),d=d._next;b&&b.render(r<0?r:b._dur*b._ease(h/this._dur),s,a)||this._startAt&&(this._zTime=r),this._onUpdate&&!s&&(u&&Ph(this,r,s,a),Wn(this,"onUpdate")),this._repeat&&m!==p&&this.vars.onRepeat&&!s&&this.parent&&Wn(this,"onRepeat"),(f===this._tDur||!f)&&this._tTime===f&&(u&&!this._onUpdate&&Ph(this,r,!0,!0),(r||!c)&&(f===this._tDur&&this._ts>0||!f&&this._ts<0)&&Sr(this,1),!s&&!(u&&!o)&&(f||o||_)&&(Wn(this,f===l?"onComplete":"onReverseComplete",!0),this._prom&&!(f<l&&this.timeScale()>0)&&this._prom()))}return this},t.targets=function(){return this._targets},t.invalidate=function(r){return(!r||!this.vars.runBackwards)&&(this._startAt=0),this._pt=this._op=this._onUpdate=this._lazy=this.ratio=0,this._ptLookup=[],this.timeline&&this.timeline.invalidate(r),n.prototype.invalidate.call(this,r)},t.resetTo=function(r,s,a,o,l){Ya||Vn.wake(),this._ts||this.play();var c=Math.min(this._dur,(this._dp._time-this._start)*this._ts),u;return this._initted||xf(this,c),u=this._ease(c/this._dur),N2(this,r,s,a,o,u,c,l)?this.resetTo(r,s,a,o,1):(Gl(this,0),this.parent||L0(this._dp,this,"_first","_last",this._dp._sort?"_start":0),this.render(0))},t.kill=function(r,s){if(s===void 0&&(s="all"),!r&&(!s||s==="all"))return this._lazy=this._pt=0,this.parent?Ua(this):this.scrollTrigger&&this.scrollTrigger.kill(!!fn),this;if(this.timeline){var a=this.timeline.totalDuration();return this.timeline.killTweensOf(r,s,mr&&mr.vars.overwrite!==!0)._first||Ua(this),this.parent&&a!==this.timeline.totalDuration()&&Ys(this,this._dur*this.timeline._tDur/a,0,1),this}var o=this._targets,l=r?ii(r):o,c=this._ptLookup,u=this._pt,f,h,d,m,g,p,_;if((!s||s==="all")&&f2(o,l))return s==="all"&&(this._pt=0),Ua(this);for(f=this._op=this._op||[],s!=="all"&&(cn(s)&&(g={},Pn(s,function(v){return g[v]=1}),s=g),s=O2(o,s)),_=o.length;_--;)if(~l.indexOf(o[_])){h=c[_],s==="all"?(f[_]=s,m=h,d={}):(d=f[_]=f[_]||{},m=s);for(g in m)p=h&&h[g],p&&((!("kill"in p.d)||p.d.kill(g)===!0)&&kl(this,p,"_pt"),delete h[g]),d!=="all"&&(d[g]=1)}return this._initted&&!this._pt&&u&&Ua(this),this},e.to=function(r,s){return new e(r,s,arguments[2])},e.from=function(r,s){return ka(1,arguments)},e.delayedCall=function(r,s,a,o){return new e(s,0,{immediateRender:!1,lazy:!1,overwrite:!1,delay:r,onComplete:s,onReverseComplete:s,onCompleteParams:a,onReverseCompleteParams:a,callbackScope:o})},e.fromTo=function(r,s,a){return ka(2,arguments)},e.set=function(r,s){return s.duration=0,s.repeatDelay||(s.repeat=0),new e(r,s)},e.killTweensOf=function(r,s,a){return Bt.killTweensOf(r,s,a)},e})(qa);Kn(jt.prototype,{_targets:[],_lazy:0,_startAt:0,_op:0,_onInit:0});Pn("staggerTo,staggerFrom,staggerFromTo",function(n){jt[n]=function(){var e=new Rn,t=Uh.call(arguments,0);return t.splice(n==="staggerFromTo"?5:4,0,0),e[n].apply(e,t)}});var yf=function(e,t,i){return e[t]=i},eg=function(e,t,i){return e[t](i)},k2=function(e,t,i,r){return e[t](r.fp,i)},z2=function(e,t,i){return e.setAttribute(t,i)},bf=function(e,t){return Ht(e[t])?eg:uf(e[t])&&e.setAttribute?z2:yf},tg=function(e,t){return t.set(t.t,t.p,Math.round((t.s+t.c*e)*1e6)/1e6,t)},G2=function(e,t){return t.set(t.t,t.p,!!(t.s+t.c*e),t)},ng=function(e,t){var i=t._pt,r="";if(!e&&t.b)r=t.b;else if(e===1&&t.e)r=t.e;else{for(;i;)r=i.p+(i.m?i.m(i.s+i.c*e):Math.round((i.s+i.c*e)*1e4)/1e4)+r,i=i._next;r+=t.c}t.set(t.t,t.p,r,t)},Mf=function(e,t){for(var i=t._pt;i;)i.r(e,i.d),i=i._next},H2=function(e,t,i,r){for(var s=this._pt,a;s;)a=s._next,s.p===r&&s.modifier(e,t,i),s=a},V2=function(e){for(var t=this._pt,i,r;t;)r=t._next,t.p===e&&!t.op||t.op===e?kl(this,t,"_pt"):t.dep||(i=1),t=r;return!i},W2=function(e,t,i,r){r.mSet(e,t,r.m.call(r.tween,i,r.mt),r)},ig=function(e){for(var t=e._pt,i,r,s,a;t;){for(i=t._next,r=s;r&&r.pr>t.pr;)r=r._next;(t._prev=r?r._prev:a)?t._prev._next=t:s=t,(t._next=r)?r._prev=t:a=t,t=i}e._pt=s},Dn=(function(){function n(t,i,r,s,a,o,l,c,u){this.t=i,this.s=s,this.c=a,this.p=r,this.r=o||tg,this.d=l||this,this.set=c||yf,this.pr=u||0,this._next=t,t&&(t._prev=this)}var e=n.prototype;return e.modifier=function(i,r,s){this.mSet=this.mSet||this.set,this.set=W2,this.m=i,this.mt=s,this.tween=r},n})();Pn(mf+"parent,duration,ease,delay,overwrite,runBackwards,startAt,yoyo,immediateRender,repeat,repeatDelay,data,paused,reversed,lazy,callbackScope,stringFilter,id,yoyoEase,stagger,inherit,repeatRefresh,keyframes,autoRevert,scrollTrigger,easeReverse",function(n){return pf[n]=1});qn.TweenMax=qn.TweenLite=jt;qn.TimelineLite=qn.TimelineMax=Rn;Bt=new Rn({sortChildren:!1,defaults:Va,autoRemoveChildren:!0,id:"root",smoothChildTiming:!0});jn.stringFilter=q0;var qr=[],al={},X2=[],Up=0,j2=0,Jc=function(e){return(al[e]||X2).map(function(t){return t()})},Nh=function(){var e=Date.now(),t=[];e-Up>2&&(Jc("matchMediaInit"),qr.forEach(function(i){var r=i.queries,s=i.conditions,a,o,l,c;for(o in r)a=Mi.matchMedia(r[o]).matches,a&&(l=1),a!==s[o]&&(s[o]=a,c=1);c&&(i.revert(),l&&t.push(i))}),Jc("matchMediaRevert"),t.forEach(function(i){return i.onMatch(i,function(r){return i.add(null,r)})}),Up=e,Jc("matchMedia"))},rg=(function(){function n(t,i){this.selector=i&&Lh(i),this.data=[],this._r=[],this.isReverted=!1,this.id=j2++,t&&this.add(t)}var e=n.prototype;return e.add=function(i,r,s){Ht(i)&&(s=r,r=i,i=Ht);var a=this,o=function(){var c=It,u=a.selector,f;return c&&c!==a&&c.data.push(a),s&&(a.selector=Lh(s)),It=a,f=r.apply(a,arguments),Ht(f)&&a._r.push(f),It=c,a.selector=u,a.isReverted=!1,f};return a.last=o,i===Ht?o(a,function(l){return a.add(null,l)}):i?a[i]=o:o},e.ignore=function(i){var r=It;It=null,i(this),It=r},e.getTweens=function(){var i=[];return this.data.forEach(function(r){return r instanceof n?i.push.apply(i,r.getTweens()):r instanceof jt&&!(r.parent&&r.parent.data==="nested")&&i.push(r)}),i},e.clear=function(){this._r.length=this.data.length=0},e.kill=function(i,r){var s=this;if(i?(function(){for(var o=s.getTweens(),l=s.data.length,c;l--;)c=s.data[l],c.data==="isFlip"&&(c.revert(),c.getChildren(!0,!0,!1).forEach(function(u){return o.splice(o.indexOf(u),1)}));for(o.map(function(u){return{g:u._dur||u._delay||u._sat&&!u._sat.vars.immediateRender?u.globalTime(0):-1/0,t:u}}).sort(function(u,f){return f.g-u.g||-1/0}).forEach(function(u){return u.t.revert(i)}),l=s.data.length;l--;)c=s.data[l],c instanceof Rn?c.data!=="nested"&&(c.scrollTrigger&&c.scrollTrigger.revert(),c.kill()):!(c instanceof jt)&&c.revert&&c.revert(i);s._r.forEach(function(u){return u(i,s)}),s.isReverted=!0})():this.data.forEach(function(o){return o.kill&&o.kill()}),this.clear(),r)for(var a=qr.length;a--;)qr[a].id===this.id&&qr.splice(a,1)},e.revert=function(i){this.kill(i||{})},n})(),Y2=(function(){function n(t){this.contexts=[],this.scope=t,It&&It.data.push(this)}var e=n.prototype;return e.add=function(i,r,s){Li(i)||(i={matches:i});var a=new rg(0,s||this.scope),o=a.conditions={},l,c,u;It&&!a.selector&&(a.selector=It.selector),this.contexts.push(a),r=a.add("onMatch",r),a.queries=i;for(c in i)c==="all"?u=1:(l=Mi.matchMedia(i[c]),l&&(qr.indexOf(a)<0&&qr.push(a),(o[c]=l.matches)&&(u=1),l.addListener?l.addListener(Nh):l.addEventListener("change",Nh)));return u&&r(a,function(f){return a.add(null,f)}),this},e.revert=function(i){this.kill(i||{})},e.kill=function(i){this.contexts.forEach(function(r){return r.kill(i,!0)})},n})(),Tl={registerPlugin:function(){for(var e=arguments.length,t=new Array(e),i=0;i<e;i++)t[i]=arguments[i];t.forEach(function(r){return X0(r)})},timeline:function(e){return new Rn(e)},getTweensOf:function(e,t){return Bt.getTweensOf(e,t)},getProperty:function(e,t,i,r){cn(e)&&(e=ii(e)[0]);var s=Xr(e||{}).get,a=i?U0:D0;return i==="native"&&(i=""),e&&(t?a((Gn[t]&&Gn[t].get||s)(e,t,i,r)):function(o,l,c){return a((Gn[o]&&Gn[o].get||s)(e,o,l,c))})},quickSetter:function(e,t,i){if(e=ii(e),e.length>1){var r=e.map(function(u){return Ln.quickSetter(u,t,i)}),s=r.length;return function(u){for(var f=s;f--;)r[f](u)}}e=e[0]||{};var a=Gn[t],o=Xr(e),l=o.harness&&(o.harness.aliases||{})[t]||t,c=a?function(u){var f=new a;Ls._pt=0,f.init(e,i?u+i:u,Ls,0,[e]),f.render(1,f),Ls._pt&&Mf(1,Ls)}:o.set(e,l);return a?c:function(u){return c(e,l,i?u+i:u,o,1)}},quickTo:function(e,t,i){var r,s=Ln.to(e,Kn((r={},r[t]="+=0.1",r.paused=!0,r.stagger=0,r),i||{})),a=function(l,c,u){return s.resetTo(t,l,c,u)};return a.tween=s,a},isTweening:function(e){return Bt.getTweensOf(e,!0).length>0},defaults:function(e){return e&&e.ease&&(e.ease=Yr(e.ease,Va.ease)),Ap(Va,e||{})},config:function(e){return Ap(jn,e||{})},registerEffect:function(e){var t=e.name,i=e.effect,r=e.plugins,s=e.defaults,a=e.extendTimeline;(r||"").split(",").forEach(function(o){return o&&!Gn[o]&&!qn[o]&&Wa(t+" effect requires "+o+" plugin.")}),qc[t]=function(o,l,c){return i(ii(o),Kn(l||{},s),c)},a&&(Rn.prototype[t]=function(o,l,c){return this.add(qc[t](o,Li(l)?l:(c=l)&&{},this),c)})},registerEase:function(e,t){dt[e]=Yr(t)},parseEase:function(e,t){return arguments.length?Yr(e,t):dt},getById:function(e){return Bt.getById(e)},exportRoot:function(e,t){e===void 0&&(e={});var i=new Rn(e),r,s;for(i.smoothChildTiming=Cn(e.smoothChildTiming),Bt.remove(i),i._dp=0,i._time=i._tTime=Bt._time,r=Bt._first;r;)s=r._next,(t||!(!r._dur&&r instanceof jt&&r.vars.onComplete===r._targets[0]))&&wi(i,r,r._start-r._delay),r=s;return wi(Bt,i,0),i},context:function(e,t){return e?new rg(e,t):It},matchMedia:function(e){return new Y2(e)},matchMediaRefresh:function(){return qr.forEach(function(e){var t=e.conditions,i,r;for(r in t)t[r]&&(t[r]=!1,i=1);i&&e.revert()})||Nh()},addEventListener:function(e,t){var i=al[e]||(al[e]=[]);~i.indexOf(t)||i.push(t)},removeEventListener:function(e,t){var i=al[e],r=i&&i.indexOf(t);r>=0&&i.splice(r,1)},utils:{wrap:T2,wrapYoyo:E2,distribute:k0,random:G0,snap:z0,normalize:S2,getUnit:gn,clamp:x2,splitColor:j0,toArray:ii,selector:Lh,mapRange:V0,pipe:b2,unitize:M2,interpolate:w2,shuffle:B0},install:w0,effects:qc,ticker:Vn,updateRoot:Rn.updateRoot,plugins:Gn,globalTimeline:Bt,core:{PropTween:Dn,globals:A0,Tween:jt,Timeline:Rn,Animation:qa,getCache:Xr,_removeLinkedListItem:kl,reverting:function(){return fn},context:function(e){return e&&It&&(It.data.push(e),e._ctx=It),It},suppressOverwrites:function(e){return cf=e}}};Pn("to,from,fromTo,delayedCall,set,killTweensOf",function(n){return Tl[n]=jt[n]});Vn.add(Rn.updateRoot);Ls=Tl.to({},{duration:0});var q2=function(e,t){for(var i=e._pt;i&&i.p!==t&&i.op!==t&&i.fp!==t;)i=i._next;return i},K2=function(e,t){var i=e._targets,r,s,a;for(r in t)for(s=i.length;s--;)a=e._ptLookup[s][r],a&&(a=a.d)&&(a._pt&&(a=q2(a,r)),a&&a.modifier&&a.modifier(t[r],e,i[s],r))},Qc=function(e,t){return{name:e,headless:1,rawVars:1,init:function(r,s,a){a._onInit=function(o){var l,c;if(cn(s)&&(l={},Pn(s,function(u){return l[u]=1}),s=l),t){l={};for(c in s)l[c]=t(s[c]);s=l}K2(o,s)}}}},Ln=Tl.registerPlugin({name:"attr",init:function(e,t,i,r,s){var a,o,l;this.tween=i;for(a in t)l=e.getAttribute(a)||"",o=this.add(e,"setAttribute",(l||0)+"",t[a],r,s,0,0,a),o.op=a,o.b=l,this._props.push(a)},render:function(e,t){for(var i=t._pt;i;)fn?i.set(i.t,i.p,i.b,i):i.r(e,i.d),i=i._next}},{name:"endArray",headless:1,init:function(e,t){for(var i=t.length;i--;)this.add(e,i,e[i]||0,t[i],0,0,0,0,0,1)}},Qc("roundProps",Ih),Qc("modifiers"),Qc("snap",z0))||Tl;jt.version=Rn.version=Ln.version="3.15.0";E0=1;hf()&&qs();dt.Power0;dt.Power1;dt.Power2;dt.Power3;dt.Power4;dt.Linear;dt.Quad;dt.Cubic;dt.Quart;dt.Quint;dt.Strong;dt.Elastic;dt.Back;dt.SteppedEase;dt.Bounce;dt.Sine;dt.Expo;dt.Circ;/*!
 * CSSPlugin 3.15.0
 * https://gsap.com
 *
 * Copyright 2008-2026, GreenSock. All rights reserved.
 * Subject to the terms at https://gsap.com/standard-license
 * @author: Jack Doyle, jack@greensock.com
*/var Lp,gr,Os,Sf,Hr,Ip,Tf,Z2=function(){return typeof window<"u"},Zi={},Br=180/Math.PI,Bs=Math.PI/180,Rs=Math.atan2,Fp=1e8,Ef=/([A-Z])/g,$2=/(left|right|width|margin|padding|x)/i,J2=/[\s,\(]\S/,Ci={autoAlpha:"opacity,visibility",scale:"scaleX,scaleY",alpha:"opacity"},Oh=function(e,t){return t.set(t.t,t.p,Math.round((t.s+t.c*e)*1e4)/1e4+t.u,t)},Q2=function(e,t){return t.set(t.t,t.p,e===1?t.e:Math.round((t.s+t.c*e)*1e4)/1e4+t.u,t)},eT=function(e,t){return t.set(t.t,t.p,e?Math.round((t.s+t.c*e)*1e4)/1e4+t.u:t.b,t)},tT=function(e,t){return t.set(t.t,t.p,e===1?t.e:e?Math.round((t.s+t.c*e)*1e4)/1e4+t.u:t.b,t)},nT=function(e,t){var i=t.s+t.c*e;t.set(t.t,t.p,~~(i+(i<0?-.5:.5))+t.u,t)},sg=function(e,t){return t.set(t.t,t.p,e?t.e:t.b,t)},ag=function(e,t){return t.set(t.t,t.p,e!==1?t.b:t.e,t)},iT=function(e,t,i){return e.style[t]=i},rT=function(e,t,i){return e.style.setProperty(t,i)},sT=function(e,t,i){return e._gsap[t]=i},aT=function(e,t,i){return e._gsap.scaleX=e._gsap.scaleY=i},oT=function(e,t,i,r,s){var a=e._gsap;a.scaleX=a.scaleY=i,a.renderTransform(s,a)},lT=function(e,t,i,r,s){var a=e._gsap;a[t]=i,a.renderTransform(s,a)},kt="transform",Un=kt+"Origin",cT=function n(e,t){var i=this,r=this.target,s=r.style,a=r._gsap;if(e in Zi&&s){if(this.tfm=this.tfm||{},e!=="transform")e=Ci[e]||e,~e.indexOf(",")?e.split(",").forEach(function(o){return i.tfm[o]=Hi(r,o)}):this.tfm[e]=a.x?a[e]:Hi(r,e),e===Un&&(this.tfm.zOrigin=a.zOrigin);else return Ci.transform.split(",").forEach(function(o){return n.call(i,o,t)});if(this.props.indexOf(kt)>=0)return;a.svg&&(this.svgo=r.getAttribute("data-svg-origin"),this.props.push(Un,t,"")),e=kt}(s||t)&&this.props.push(e,t,s[e])},og=function(e){e.translate&&(e.removeProperty("translate"),e.removeProperty("scale"),e.removeProperty("rotate"))},uT=function(){var e=this.props,t=this.target,i=t.style,r=t._gsap,s,a;for(s=0;s<e.length;s+=3)e[s+1]?e[s+1]===2?t[e[s]](e[s+2]):t[e[s]]=e[s+2]:e[s+2]?i[e[s]]=e[s+2]:i.removeProperty(e[s].substr(0,2)==="--"?e[s]:e[s].replace(Ef,"-$1").toLowerCase());if(this.tfm){for(a in this.tfm)r[a]=this.tfm[a];r.svg&&(r.renderTransform(),t.setAttribute("data-svg-origin",this.svgo||"")),s=Tf(),(!s||!s.isStart)&&!i[kt]&&(og(i),r.zOrigin&&i[Un]&&(i[Un]+=" "+r.zOrigin+"px",r.zOrigin=0,r.renderTransform()),r.uncache=1)}},lg=function(e,t){var i={target:e,props:[],revert:uT,save:cT};return e._gsap||Ln.core.getCache(e),t&&e.style&&e.nodeType&&t.split(",").forEach(function(r){return i.save(r)}),i},cg,Bh=function(e,t){var i=gr.createElementNS?gr.createElementNS((t||"http://www.w3.org/1999/xhtml").replace(/^https/,"http"),e):gr.createElement(e);return i&&i.style?i:gr.createElement(e)},Xn=function n(e,t,i){var r=getComputedStyle(e);return r[t]||r.getPropertyValue(t.replace(Ef,"-$1").toLowerCase())||r.getPropertyValue(t)||!i&&n(e,Ks(t)||t,1)||""},Np="O,Moz,ms,Ms,Webkit".split(","),Ks=function(e,t,i){var r=t||Hr,s=r.style,a=5;if(e in s&&!i)return e;for(e=e.charAt(0).toUpperCase()+e.substr(1);a--&&!(Np[a]+e in s););return a<0?null:(a===3?"ms":a>=0?Np[a]:"")+e},kh=function(){Z2()&&window.document&&(Lp=window,gr=Lp.document,Os=gr.documentElement,Hr=Bh("div")||{style:{}},Bh("div"),kt=Ks(kt),Un=kt+"Origin",Hr.style.cssText="border-width:0;line-height:0;position:absolute;padding:0",cg=!!Ks("perspective"),Tf=Ln.core.reverting,Sf=1)},Op=function(e){var t=e.ownerSVGElement,i=Bh("svg",t&&t.getAttribute("xmlns")||"http://www.w3.org/2000/svg"),r=e.cloneNode(!0),s;r.style.display="block",i.appendChild(r),Os.appendChild(i);try{s=r.getBBox()}catch{}return i.removeChild(r),Os.removeChild(i),s},Bp=function(e,t){for(var i=t.length;i--;)if(e.hasAttribute(t[i]))return e.getAttribute(t[i])},ug=function(e){var t,i;try{t=e.getBBox()}catch{t=Op(e),i=1}return t&&(t.width||t.height)||i||(t=Op(e)),t&&!t.width&&!t.x&&!t.y?{x:+Bp(e,["x","cx","x1"])||0,y:+Bp(e,["y","cy","y1"])||0,width:0,height:0}:t},hg=function(e){return!!(e.getCTM&&(!e.parentNode||e.ownerSVGElement)&&ug(e))},Tr=function(e,t){if(t){var i=e.style,r;t in Zi&&t!==Un&&(t=kt),i.removeProperty?(r=t.substr(0,2),(r==="ms"||t.substr(0,6)==="webkit")&&(t="-"+t),i.removeProperty(r==="--"?t:t.replace(Ef,"-$1").toLowerCase())):i.removeAttribute(t)}},_r=function(e,t,i,r,s,a){var o=new Dn(e._pt,t,i,0,1,a?ag:sg);return e._pt=o,o.b=r,o.e=s,e._props.push(i),o},kp={deg:1,rad:1,turn:1},hT={grid:1,flex:1},Er=function n(e,t,i,r){var s=parseFloat(i)||0,a=(i+"").trim().substr((s+"").length)||"px",o=Hr.style,l=$2.test(t),c=e.tagName.toLowerCase()==="svg",u=(c?"client":"offset")+(l?"Width":"Height"),f=100,h=r==="px",d=r==="%",m,g,p,_;if(r===a||!s||kp[r]||kp[a])return s;if(a!=="px"&&!h&&(s=n(e,t,i,"px")),_=e.getCTM&&hg(e),(d||a==="%")&&(Zi[t]||~t.indexOf("adius")))return m=_?e.getBBox()[l?"width":"height"]:e[u],Wt(d?s/m*f:s/100*m);if(o[l?"width":"height"]=f+(h?a:r),g=r!=="rem"&&~t.indexOf("adius")||r==="em"&&e.appendChild&&!c?e:e.parentNode,_&&(g=(e.ownerSVGElement||{}).parentNode),(!g||g===gr||!g.appendChild)&&(g=gr.body),p=g._gsap,p&&d&&p.width&&l&&p.time===Vn.time&&!p.uncache)return Wt(s/p.width*f);if(d&&(t==="height"||t==="width")){var v=e.style[t];e.style[t]=f+r,m=e[u],v?e.style[t]=v:Tr(e,t)}else(d||a==="%")&&!hT[Xn(g,"display")]&&(o.position=Xn(e,"position")),g===e&&(o.position="static"),g.appendChild(Hr),m=Hr[u],g.removeChild(Hr),o.position="absolute";return l&&d&&(p=Xr(g),p.time=Vn.time,p.width=g[u]),Wt(h?m*s/f:m&&s?f/m*s:0)},Hi=function(e,t,i,r){var s;return Sf||kh(),t in Ci&&t!=="transform"&&(t=Ci[t],~t.indexOf(",")&&(t=t.split(",")[0])),Zi[t]&&t!=="transform"?(s=Za(e,r),s=t!=="transformOrigin"?s[t]:s.svg?s.origin:wl(Xn(e,Un))+" "+s.zOrigin+"px"):(s=e.style[t],(!s||s==="auto"||r||~(s+"").indexOf("calc("))&&(s=El[t]&&El[t](e,t,i)||Xn(e,t)||C0(e,t)||(t==="opacity"?1:0))),i&&!~(s+"").trim().indexOf(" ")?Er(e,t,s,i)+i:s},fT=function(e,t,i,r){if(!i||i==="none"){var s=Ks(t,e,1),a=s&&Xn(e,s,1);a&&a!==i?(t=s,i=a):t==="borderColor"&&(i=Xn(e,"borderTopColor"))}var o=new Dn(this._pt,e.style,t,0,1,ng),l=0,c=0,u,f,h,d,m,g,p,_,v,b,S,E;if(o.b=i,o.e=r,i+="",r+="",r.substring(0,6)==="var(--"&&(r=Xn(e,r.substring(4,r.indexOf(")")))),r==="auto"&&(g=e.style[t],e.style[t]=r,r=Xn(e,t)||r,g?e.style[t]=g:Tr(e,t)),u=[i,r],q0(u),i=u[0],r=u[1],h=i.match(Us)||[],E=r.match(Us)||[],E.length){for(;f=Us.exec(r);)p=f[0],v=r.substring(l,f.index),m?m=(m+1)%5:(v.substr(-5)==="rgba("||v.substr(-5)==="hsla(")&&(m=1),p!==(g=h[c++]||"")&&(d=parseFloat(g)||0,S=g.substr((d+"").length),p.charAt(1)==="="&&(p=Ns(d,p)+S),_=parseFloat(p),b=p.substr((_+"").length),l=Us.lastIndex-b.length,b||(b=b||jn.units[t]||S,l===r.length&&(r+=b,o.e+=b)),S!==b&&(d=Er(e,t,g,b)||0),o._pt={_next:o._pt,p:v||c===1?v:",",s:d,c:_-d,m:m&&m<4||t==="zIndex"?Math.round:0});o.c=l<r.length?r.substring(l,r.length):""}else o.r=t==="display"&&r==="none"?ag:sg;return T0.test(r)&&(o.e=0),this._pt=o,o},zp={top:"0%",bottom:"100%",left:"0%",right:"100%",center:"50%"},dT=function(e){var t=e.split(" "),i=t[0],r=t[1]||"50%";return(i==="top"||i==="bottom"||r==="left"||r==="right")&&(e=i,i=r,r=e),t[0]=zp[i]||i,t[1]=zp[r]||r,t.join(" ")},pT=function(e,t){if(t.tween&&t.tween._time===t.tween._dur){var i=t.t,r=i.style,s=t.u,a=i._gsap,o,l,c;if(s==="all"||s===!0)r.cssText="",l=1;else for(s=s.split(","),c=s.length;--c>-1;)o=s[c],Zi[o]&&(l=1,o=o==="transformOrigin"?Un:kt),Tr(i,o);l&&(Tr(i,kt),a&&(a.svg&&i.removeAttribute("transform"),r.scale=r.rotate=r.translate="none",Za(i,1),a.uncache=1,og(r)))}},El={clearProps:function(e,t,i,r,s){if(s.data!=="isFromStart"){var a=e._pt=new Dn(e._pt,t,i,0,0,pT);return a.u=r,a.pr=-10,a.tween=s,e._props.push(i),1}}},Ka=[1,0,0,1,0,0],fg={},dg=function(e){return e==="matrix(1, 0, 0, 1, 0, 0)"||e==="none"||!e},Gp=function(e){var t=Xn(e,kt);return dg(t)?Ka:t.substr(7).match(S0).map(Wt)},wf=function(e,t){var i=e._gsap||Xr(e),r=e.style,s=Gp(e),a,o,l,c;return i.svg&&e.getAttribute("transform")?(l=e.transform.baseVal.consolidate().matrix,s=[l.a,l.b,l.c,l.d,l.e,l.f],s.join(",")==="1,0,0,1,0,0"?Ka:s):(s===Ka&&!e.offsetParent&&e!==Os&&!i.svg&&(l=r.display,r.display="block",a=e.parentNode,(!a||!e.offsetParent&&!e.getBoundingClientRect().width)&&(c=1,o=e.nextElementSibling,Os.appendChild(e)),s=Gp(e),l?r.display=l:Tr(e,"display"),c&&(o?a.insertBefore(e,o):a?a.appendChild(e):Os.removeChild(e))),t&&s.length>6?[s[0],s[1],s[4],s[5],s[12],s[13]]:s)},zh=function(e,t,i,r,s,a){var o=e._gsap,l=s||wf(e,!0),c=o.xOrigin||0,u=o.yOrigin||0,f=o.xOffset||0,h=o.yOffset||0,d=l[0],m=l[1],g=l[2],p=l[3],_=l[4],v=l[5],b=t.split(" "),S=parseFloat(b[0])||0,E=parseFloat(b[1])||0,M,T,x,y;i?l!==Ka&&(T=d*p-m*g)&&(x=S*(p/T)+E*(-g/T)+(g*v-p*_)/T,y=S*(-m/T)+E*(d/T)-(d*v-m*_)/T,S=x,E=y):(M=ug(e),S=M.x+(~b[0].indexOf("%")?S/100*M.width:S),E=M.y+(~(b[1]||b[0]).indexOf("%")?E/100*M.height:E)),r||r!==!1&&o.smooth?(_=S-c,v=E-u,o.xOffset=f+(_*d+v*g)-_,o.yOffset=h+(_*m+v*p)-v):o.xOffset=o.yOffset=0,o.xOrigin=S,o.yOrigin=E,o.smooth=!!r,o.origin=t,o.originIsAbsolute=!!i,e.style[Un]="0px 0px",a&&(_r(a,o,"xOrigin",c,S),_r(a,o,"yOrigin",u,E),_r(a,o,"xOffset",f,o.xOffset),_r(a,o,"yOffset",h,o.yOffset)),e.setAttribute("data-svg-origin",S+" "+E)},Za=function(e,t){var i=e._gsap||new Z0(e);if("x"in i&&!t&&!i.uncache)return i;var r=e.style,s=i.scaleX<0,a="px",o="deg",l=getComputedStyle(e),c=Xn(e,Un)||"0",u,f,h,d,m,g,p,_,v,b,S,E,M,T,x,y,w,C,R,L,U,I,F,N,Y,j,Z,O,H,B,V,G;return u=f=h=g=p=_=v=b=S=0,d=m=1,i.svg=!!(e.getCTM&&hg(e)),l.translate&&((l.translate!=="none"||l.scale!=="none"||l.rotate!=="none")&&(r[kt]=(l.translate!=="none"?"translate3d("+(l.translate+" 0 0").split(" ").slice(0,3).join(", ")+") ":"")+(l.rotate!=="none"?"rotate("+l.rotate+") ":"")+(l.scale!=="none"?"scale("+l.scale.split(" ").join(",")+") ":"")+(l[kt]!=="none"?l[kt]:"")),r.scale=r.rotate=r.translate="none"),T=wf(e,i.svg),i.svg&&(i.uncache?(Y=e.getBBox(),c=i.xOrigin-Y.x+"px "+(i.yOrigin-Y.y)+"px",N=""):N=!t&&e.getAttribute("data-svg-origin"),zh(e,N||c,!!N||i.originIsAbsolute,i.smooth!==!1,T)),E=i.xOrigin||0,M=i.yOrigin||0,T!==Ka&&(C=T[0],R=T[1],L=T[2],U=T[3],u=I=T[4],f=F=T[5],T.length===6?(d=Math.sqrt(C*C+R*R),m=Math.sqrt(U*U+L*L),g=C||R?Rs(R,C)*Br:0,v=L||U?Rs(L,U)*Br+g:0,v&&(m*=Math.abs(Math.cos(v*Bs))),i.svg&&(u-=E-(E*C+M*L),f-=M-(E*R+M*U))):(G=T[6],B=T[7],Z=T[8],O=T[9],H=T[10],V=T[11],u=T[12],f=T[13],h=T[14],x=Rs(G,H),p=x*Br,x&&(y=Math.cos(-x),w=Math.sin(-x),N=I*y+Z*w,Y=F*y+O*w,j=G*y+H*w,Z=I*-w+Z*y,O=F*-w+O*y,H=G*-w+H*y,V=B*-w+V*y,I=N,F=Y,G=j),x=Rs(-L,H),_=x*Br,x&&(y=Math.cos(-x),w=Math.sin(-x),N=C*y-Z*w,Y=R*y-O*w,j=L*y-H*w,V=U*w+V*y,C=N,R=Y,L=j),x=Rs(R,C),g=x*Br,x&&(y=Math.cos(x),w=Math.sin(x),N=C*y+R*w,Y=I*y+F*w,R=R*y-C*w,F=F*y-I*w,C=N,I=Y),p&&Math.abs(p)+Math.abs(g)>359.9&&(p=g=0,_=180-_),d=Wt(Math.sqrt(C*C+R*R+L*L)),m=Wt(Math.sqrt(F*F+G*G)),x=Rs(I,F),v=Math.abs(x)>2e-4?x*Br:0,S=V?1/(V<0?-V:V):0),i.svg&&(N=e.getAttribute("transform"),i.forceCSS=e.setAttribute("transform","")||!dg(Xn(e,kt)),N&&e.setAttribute("transform",N))),Math.abs(v)>90&&Math.abs(v)<270&&(s?(d*=-1,v+=g<=0?180:-180,g+=g<=0?180:-180):(m*=-1,v+=v<=0?180:-180)),t=t||i.uncache,i.x=u-((i.xPercent=u&&(!t&&i.xPercent||(Math.round(e.offsetWidth/2)===Math.round(-u)?-50:0)))?e.offsetWidth*i.xPercent/100:0)+a,i.y=f-((i.yPercent=f&&(!t&&i.yPercent||(Math.round(e.offsetHeight/2)===Math.round(-f)?-50:0)))?e.offsetHeight*i.yPercent/100:0)+a,i.z=h+a,i.scaleX=Wt(d),i.scaleY=Wt(m),i.rotation=Wt(g)+o,i.rotationX=Wt(p)+o,i.rotationY=Wt(_)+o,i.skewX=v+o,i.skewY=b+o,i.transformPerspective=S+a,(i.zOrigin=parseFloat(c.split(" ")[2])||!t&&i.zOrigin||0)&&(r[Un]=wl(c)),i.xOffset=i.yOffset=0,i.force3D=jn.force3D,i.renderTransform=i.svg?gT:cg?pg:mT,i.uncache=0,i},wl=function(e){return(e=e.split(" "))[0]+" "+e[1]},eu=function(e,t,i){var r=gn(t);return Wt(parseFloat(t)+parseFloat(Er(e,"x",i+"px",r)))+r},mT=function(e,t){t.z="0px",t.rotationY=t.rotationX="0deg",t.force3D=0,pg(e,t)},Fr="0deg",wa="0px",Nr=") ",pg=function(e,t){var i=t||this,r=i.xPercent,s=i.yPercent,a=i.x,o=i.y,l=i.z,c=i.rotation,u=i.rotationY,f=i.rotationX,h=i.skewX,d=i.skewY,m=i.scaleX,g=i.scaleY,p=i.transformPerspective,_=i.force3D,v=i.target,b=i.zOrigin,S="",E=_==="auto"&&e&&e!==1||_===!0;if(b&&(f!==Fr||u!==Fr)){var M=parseFloat(u)*Bs,T=Math.sin(M),x=Math.cos(M),y;M=parseFloat(f)*Bs,y=Math.cos(M),a=eu(v,a,T*y*-b),o=eu(v,o,-Math.sin(M)*-b),l=eu(v,l,x*y*-b+b)}p!==wa&&(S+="perspective("+p+Nr),(r||s)&&(S+="translate("+r+"%, "+s+"%) "),(E||a!==wa||o!==wa||l!==wa)&&(S+=l!==wa||E?"translate3d("+a+", "+o+", "+l+") ":"translate("+a+", "+o+Nr),c!==Fr&&(S+="rotate("+c+Nr),u!==Fr&&(S+="rotateY("+u+Nr),f!==Fr&&(S+="rotateX("+f+Nr),(h!==Fr||d!==Fr)&&(S+="skew("+h+", "+d+Nr),(m!==1||g!==1)&&(S+="scale("+m+", "+g+Nr),v.style[kt]=S||"translate(0, 0)"},gT=function(e,t){var i=t||this,r=i.xPercent,s=i.yPercent,a=i.x,o=i.y,l=i.rotation,c=i.skewX,u=i.skewY,f=i.scaleX,h=i.scaleY,d=i.target,m=i.xOrigin,g=i.yOrigin,p=i.xOffset,_=i.yOffset,v=i.forceCSS,b=parseFloat(a),S=parseFloat(o),E,M,T,x,y;l=parseFloat(l),c=parseFloat(c),u=parseFloat(u),u&&(u=parseFloat(u),c+=u,l+=u),l||c?(l*=Bs,c*=Bs,E=Math.cos(l)*f,M=Math.sin(l)*f,T=Math.sin(l-c)*-h,x=Math.cos(l-c)*h,c&&(u*=Bs,y=Math.tan(c-u),y=Math.sqrt(1+y*y),T*=y,x*=y,u&&(y=Math.tan(u),y=Math.sqrt(1+y*y),E*=y,M*=y)),E=Wt(E),M=Wt(M),T=Wt(T),x=Wt(x)):(E=f,x=h,M=T=0),(b&&!~(a+"").indexOf("px")||S&&!~(o+"").indexOf("px"))&&(b=Er(d,"x",a,"px"),S=Er(d,"y",o,"px")),(m||g||p||_)&&(b=Wt(b+m-(m*E+g*T)+p),S=Wt(S+g-(m*M+g*x)+_)),(r||s)&&(y=d.getBBox(),b=Wt(b+r/100*y.width),S=Wt(S+s/100*y.height)),y="matrix("+E+","+M+","+T+","+x+","+b+","+S+")",d.setAttribute("transform",y),v&&(d.style[kt]=y)},_T=function(e,t,i,r,s){var a=360,o=cn(s),l=parseFloat(s)*(o&&~s.indexOf("rad")?Br:1),c=l-r,u=r+c+"deg",f,h;return o&&(f=s.split("_")[1],f==="short"&&(c%=a,c!==c%(a/2)&&(c+=c<0?a:-a)),f==="cw"&&c<0?c=(c+a*Fp)%a-~~(c/a)*a:f==="ccw"&&c>0&&(c=(c-a*Fp)%a-~~(c/a)*a)),e._pt=h=new Dn(e._pt,t,i,r,c,Q2),h.e=u,h.u="deg",e._props.push(i),h},Hp=function(e,t){for(var i in t)e[i]=t[i];return e},vT=function(e,t,i){var r=Hp({},i._gsap),s="perspective,force3D,transformOrigin,svgOrigin",a=i.style,o,l,c,u,f,h,d,m;r.svg?(c=i.getAttribute("transform"),i.setAttribute("transform",""),a[kt]=t,o=Za(i,1),Tr(i,kt),i.setAttribute("transform",c)):(c=getComputedStyle(i)[kt],a[kt]=t,o=Za(i,1),a[kt]=c);for(l in Zi)c=r[l],u=o[l],c!==u&&s.indexOf(l)<0&&(d=gn(c),m=gn(u),f=d!==m?Er(i,l,c,m):parseFloat(c),h=parseFloat(u),e._pt=new Dn(e._pt,o,l,f,h-f,Oh),e._pt.u=m||0,e._props.push(l));Hp(o,r)};Pn("padding,margin,Width,Radius",function(n,e){var t="Top",i="Right",r="Bottom",s="Left",a=(e<3?[t,i,r,s]:[t+s,t+i,r+i,r+s]).map(function(o){return e<2?n+o:"border"+o+n});El[e>1?"border"+n:n]=function(o,l,c,u,f){var h,d;if(arguments.length<4)return h=a.map(function(m){return Hi(o,m,c)}),d=h.join(" "),d.split(h[0]).length===5?h[0]:d;h=(u+"").split(" "),d={},a.forEach(function(m,g){return d[m]=h[g]=h[g]||h[(g-1)/2|0]}),o.init(l,d,f)}});var mg={name:"css",register:kh,targetTest:function(e){return e.style&&e.nodeType},init:function(e,t,i,r,s){var a=this._props,o=e.style,l=i.vars.startAt,c,u,f,h,d,m,g,p,_,v,b,S,E,M,T,x,y;Sf||kh(),this.styles=this.styles||lg(e),x=this.styles.props,this.tween=i;for(g in t)if(g!=="autoRound"&&(u=t[g],!(Gn[g]&&$0(g,t,i,r,e,s)))){if(d=typeof u,m=El[g],d==="function"&&(u=u.call(i,r,e,s),d=typeof u),d==="string"&&~u.indexOf("random(")&&(u=ja(u)),m)m(this,e,g,u,i)&&(T=1);else if(g.substr(0,2)==="--")c=(getComputedStyle(e).getPropertyValue(g)+"").trim(),u+="",yr.lastIndex=0,yr.test(c)||(p=gn(c),_=gn(u),_?p!==_&&(c=Er(e,g,c,_)+_):p&&(u+=p)),this.add(o,"setProperty",c,u,r,s,0,0,g),a.push(g),x.push(g,0,o[g]);else if(d!=="undefined"){if(l&&g in l?(c=typeof l[g]=="function"?l[g].call(i,r,e,s):l[g],cn(c)&&~c.indexOf("random(")&&(c=ja(c)),gn(c+"")||c==="auto"||(c+=jn.units[g]||gn(Hi(e,g))||""),(c+"").charAt(1)==="="&&(c=Hi(e,g))):c=Hi(e,g),h=parseFloat(c),v=d==="string"&&u.charAt(1)==="="&&u.substr(0,2),v&&(u=u.substr(2)),f=parseFloat(u),g in Ci&&(g==="autoAlpha"&&(h===1&&Hi(e,"visibility")==="hidden"&&f&&(h=0),x.push("visibility",0,o.visibility),_r(this,o,"visibility",h?"inherit":"hidden",f?"inherit":"hidden",!f)),g!=="scale"&&g!=="transform"&&(g=Ci[g],~g.indexOf(",")&&(g=g.split(",")[0]))),b=g in Zi,b){if(this.styles.save(g),y=u,d==="string"&&u.substring(0,6)==="var(--"){if(u=Xn(e,u.substring(4,u.indexOf(")"))),u.substring(0,5)==="calc("){var w=e.style.perspective;e.style.perspective=u,u=Xn(e,"perspective"),w?e.style.perspective=w:Tr(e,"perspective")}f=parseFloat(u)}if(S||(E=e._gsap,E.renderTransform&&!t.parseTransform||Za(e,t.parseTransform),M=t.smoothOrigin!==!1&&E.smooth,S=this._pt=new Dn(this._pt,o,kt,0,1,E.renderTransform,E,0,-1),S.dep=1),g==="scale")this._pt=new Dn(this._pt,E,"scaleY",E.scaleY,(v?Ns(E.scaleY,v+f):f)-E.scaleY||0,Oh),this._pt.u=0,a.push("scaleY",g),g+="X";else if(g==="transformOrigin"){x.push(Un,0,o[Un]),u=dT(u),E.svg?zh(e,u,0,M,0,this):(_=parseFloat(u.split(" ")[2])||0,_!==E.zOrigin&&_r(this,E,"zOrigin",E.zOrigin,_),_r(this,o,g,wl(c),wl(u)));continue}else if(g==="svgOrigin"){zh(e,u,1,M,0,this);continue}else if(g in fg){_T(this,E,g,h,v?Ns(h,v+u):u);continue}else if(g==="smoothOrigin"){_r(this,E,"smooth",E.smooth,u);continue}else if(g==="force3D"){E[g]=u;continue}else if(g==="transform"){vT(this,u,e);continue}}else g in o||(g=Ks(g)||g);if(b||(f||f===0)&&(h||h===0)&&!J2.test(u)&&g in o)p=(c+"").substr((h+"").length),f||(f=0),_=gn(u)||(g in jn.units?jn.units[g]:p),p!==_&&(h=Er(e,g,c,_)),this._pt=new Dn(this._pt,b?E:o,g,h,(v?Ns(h,v+f):f)-h,!b&&(_==="px"||g==="zIndex")&&t.autoRound!==!1?nT:Oh),this._pt.u=_||0,b&&y!==u?(this._pt.b=c,this._pt.e=y,this._pt.r=tT):p!==_&&_!=="%"&&(this._pt.b=c,this._pt.r=eT);else if(g in o)fT.call(this,e,g,c,v?v+u:u);else if(g in e)this.add(e,g,c||e[g],v?v+u:u,r,s);else if(g!=="parseTransform"){df(g,u);continue}b||(g in o?x.push(g,0,o[g]):typeof e[g]=="function"?x.push(g,2,e[g]()):x.push(g,1,c||e[g])),a.push(g)}}T&&ig(this)},render:function(e,t){if(t.tween._time||!Tf())for(var i=t._pt;i;)i.r(e,i.d),i=i._next;else t.styles.revert()},get:Hi,aliases:Ci,getSetter:function(e,t,i){var r=Ci[t];return r&&r.indexOf(",")<0&&(t=r),t in Zi&&t!==Un&&(e._gsap.x||Hi(e,"x"))?i&&Ip===i?t==="scale"?aT:sT:(Ip=i||{})&&(t==="scale"?oT:lT):e.style&&!uf(e.style[t])?iT:~t.indexOf("-")?rT:bf(e,t)},core:{_removeProperty:Tr,_getMatrix:wf}};Ln.utils.checkPrefix=Ks;Ln.core.getStyleSaver=lg;(function(n,e,t,i){var r=Pn(n+","+e+","+t,function(s){Zi[s]=1});Pn(e,function(s){jn.units[s]="deg",fg[s]=1}),Ci[r[13]]=n+","+e,Pn(i,function(s){var a=s.split(":");Ci[a[1]]=r[a[0]]})})("x,y,z,scale,scaleX,scaleY,xPercent,yPercent","rotation,rotationX,rotationY,skewX,skewY","transform,transformOrigin,svgOrigin,force3D,smoothOrigin,transformPerspective","0:translateX,1:translateY,2:translateZ,8:rotate,8:rotationZ,8:rotateZ,9:rotateX,10:rotateY");Pn("x,y,z,top,right,bottom,left,width,height,fontSize,padding,margin,perspective",function(n){jn.units[n]="px"});Ln.registerPlugin(mg);var ol=Ln.registerPlugin(mg)||Ln;ol.core.Tween;/**
 * postprocessing v6.39.5 build Wed Sep 09 2026
 * https://github.com/pmndrs/postprocessing
 * Copyright 2015-2026 Raoul van Rüschen
 * @license Zlib
 */var xT=(()=>{const n=new Float32Array([-1,-1,0,3,-1,0,-1,3,0]),e=new Float32Array([0,0,2,0,0,2]),t=new Rt;return t.setAttribute("position",new Nt(n,3)),t.setAttribute("uv",new Nt(e,2)),t})(),gi=class Gh{static get fullscreenGeometry(){return xT}constructor(e="Pass",t=new vh,i=new af){this.name=e,this.renderer=null,this.scene=t,this.camera=i,this.screen=null,this.rtt=!0,this.needsSwap=!0,this.needsDepthBlit=!1,this.needsDepthTexture=!1,this.enabled=!0}get renderToScreen(){return!this.rtt}set renderToScreen(e){if(this.rtt===e){const t=this.fullscreenMaterial;t!==null&&(t.needsUpdate=!0),this.rtt=!e}}set mainScene(e){}set mainCamera(e){}setRenderer(e){this.renderer=e}isEnabled(){return this.enabled}setEnabled(e){this.enabled=e}get fullscreenMaterial(){return this.screen!==null?this.screen.material:null}set fullscreenMaterial(e){let t=this.screen;t!==null?t.material=e:(t=new Yn(Gh.fullscreenGeometry,e),t.frustumCulled=!1,this.scene===null&&(this.scene=new vh),this.scene.add(t),this.screen=t)}getFullscreenMaterial(){return this.fullscreenMaterial}setFullscreenMaterial(e){this.fullscreenMaterial=e}getDepthTexture(){return null}setDepthTexture(e,t=Qa){}render(e,t,i,r,s){throw new Error("Render method not implemented!")}setSize(e,t){}initialize(e,t,i){}dispose(){for(const e of Object.keys(this)){const t=this[e];(t instanceof Qt||t instanceof $i||t instanceof Jt||t instanceof Gh)&&this[e].dispose()}this.fullscreenMaterial!==null&&this.fullscreenMaterial.dispose()}},yT=class extends gi{constructor(){super("ClearMaskPass",null,null),this.needsSwap=!1}render(n,e,t,i,r){const s=n.state.buffers.stencil;s.setLocked(!1),s.setTest(!1)}},bT=`#ifdef COLOR_WRITE
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
}`,gg="varying vec2 vUv;void main(){vUv=position.xy*0.5+0.5;gl_Position=vec4(position.xy,1.0,1.0);}",_g=class extends ln{constructor(){super({name:"CopyMaterial",defines:{COLOR_SPACE_CONVERSION:"1",DEPTH_PACKING:"0",COLOR_WRITE:"1"},uniforms:{inputBuffer:new vt(null),depthBuffer:new vt(null),channelWeights:new vt(null),opacity:new vt(1)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:bT,vertexShader:gg}),this.depthFunc=cl}get inputBuffer(){return this.uniforms.inputBuffer.value}set inputBuffer(n){const e=n!==null;this.colorWrite!==e&&(e?this.defines.COLOR_WRITE=!0:delete this.defines.COLOR_WRITE,this.colorWrite=e,this.needsUpdate=!0),this.uniforms.inputBuffer.value=n}get depthBuffer(){return this.uniforms.depthBuffer.value}set depthBuffer(n){const e=n!==null;this.depthWrite!==e&&(e?this.defines.DEPTH_WRITE=!0:delete this.defines.DEPTH_WRITE,this.depthTest=e,this.depthWrite=e,this.needsUpdate=!0),this.uniforms.depthBuffer.value=n}set depthPacking(n){this.defines.DEPTH_PACKING=n.toFixed(0),this.needsUpdate=!0}get colorSpaceConversion(){return this.defines.COLOR_SPACE_CONVERSION!==void 0}set colorSpaceConversion(n){this.colorSpaceConversion!==n&&(n?this.defines.COLOR_SPACE_CONVERSION=!0:delete this.defines.COLOR_SPACE_CONVERSION,this.needsUpdate=!0)}get channelWeights(){return this.uniforms.channelWeights.value}set channelWeights(n){n!==null?(this.defines.USE_WEIGHTS="1",this.uniforms.channelWeights.value=n):delete this.defines.USE_WEIGHTS,this.needsUpdate=!0}setInputBuffer(n){this.uniforms.inputBuffer.value=n}getOpacity(n){return this.uniforms.opacity.value}setOpacity(n){this.uniforms.opacity.value=n}},MT=class extends gi{constructor(n,e=!0){super("CopyPass"),this.fullscreenMaterial=new _g,this.needsSwap=!1,this.renderTarget=n,n===void 0&&(this.renderTarget=new Qt(1,1,{minFilter:Gt,magFilter:Gt,stencilBuffer:!1,depthBuffer:!1}),this.renderTarget.texture.name="CopyPass.Target"),this.autoResize=e}get resize(){return this.autoResize}set resize(n){this.autoResize=n}get texture(){return this.renderTarget.texture}getTexture(){return this.renderTarget.texture}setAutoResizeEnabled(n){this.autoResize=n}render(n,e,t,i,r){this.fullscreenMaterial.inputBuffer=e.texture,n.setRenderTarget(this.renderToScreen?null:this.renderTarget),n.render(this.scene,this.camera)}setSize(n,e){this.autoResize&&this.renderTarget.setSize(n,e)}initialize(n,e,t){t!==void 0&&(this.renderTarget.texture.type=t,t!==Yt?this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1":n!==null&&n.outputColorSpace===Tt&&(this.renderTarget.texture.colorSpace=Tt))}},Vp=new ut,vg=class extends gi{constructor(n=!0,e=!0,t=!1){super("ClearPass",null,null),this.needsSwap=!1,this.color=n,this.depth=e,this.stencil=t,this.overrideClearColor=null,this.overrideClearAlpha=-1}setClearFlags(n,e,t){this.color=n,this.depth=e,this.stencil=t}getOverrideClearColor(){return this.overrideClearColor}setOverrideClearColor(n){this.overrideClearColor=n}getOverrideClearAlpha(){return this.overrideClearAlpha}setOverrideClearAlpha(n){this.overrideClearAlpha=n}render(n,e,t,i,r){const s=this.overrideClearColor,a=this.overrideClearAlpha,o=n.getClearAlpha(),l=s!==null,c=a>=0;l?(n.getClearColor(Vp),n.setClearColor(s,c?a:o)):c&&n.setClearAlpha(a),n.setRenderTarget(this.renderToScreen?null:e),n.clear(this.color,this.depth,this.stencil),l?n.setClearColor(Vp,o):c&&n.setClearAlpha(o)}},ST=class extends gi{constructor(n,e){super("MaskPass",n,e),this.needsSwap=!1,this.clearPass=new vg(!1,!1,!0),this.inverse=!1}set mainScene(n){this.scene=n}set mainCamera(n){this.camera=n}get inverted(){return this.inverse}set inverted(n){this.inverse=n}get clear(){return this.clearPass.enabled}set clear(n){this.clearPass.enabled=n}getClearPass(){return this.clearPass}isInverted(){return this.inverted}setInverted(n){this.inverted=n}render(n,e,t,i,r){const s=n.getContext(),a=n.state.buffers,o=this.scene,l=this.camera,c=this.clearPass,u=this.inverted?0:1,f=1-u;a.color.setMask(!1),a.depth.setMask(!1),a.color.setLocked(!0),a.depth.setLocked(!0),a.stencil.setTest(!0),a.stencil.setOp(s.REPLACE,s.REPLACE,s.REPLACE),a.stencil.setFunc(s.ALWAYS,u,4294967295),a.stencil.setClear(f),a.stencil.setLocked(!0),this.clearPass.enabled&&(this.renderToScreen?c.render(n,null):(c.render(n,e),c.render(n,t))),this.renderToScreen?(n.setRenderTarget(null),n.render(o,l)):(n.setRenderTarget(e),n.render(o,l),n.setRenderTarget(t),n.render(o,l)),a.color.setLocked(!1),a.depth.setLocked(!1),a.stencil.setLocked(!1),a.stencil.setFunc(s.EQUAL,1,4294967295),a.stencil.setOp(s.KEEP,s.KEEP,s.KEEP),a.stencil.setLocked(!0)}};function TT(n,e){const t=n.getContext();if(e<=0||typeof t.renderbufferStorageMultisample!="function")return 0;const i=t.getParameter(t.MAX_SAMPLES),r=Math.min(e,i);if(r<=0)return 0;const s=t.getParameter(t.RENDERBUFFER_BINDING),a=t.createRenderbuffer();try{return t.bindRenderbuffer(t.RENDERBUFFER,a),t.renderbufferStorageMultisample(t.RENDERBUFFER,r,t.RGBA8,1,1),r}catch{return 0}finally{t.bindRenderbuffer(t.RENDERBUFFER,s),t.deleteRenderbuffer(a)}}var tu=1/1e3,ET=1e3,wT=class{constructor(){this.startTime=performance.now(),this.previousTime=0,this.currentTime=0,this._delta=0,this._elapsed=0,this._fixedDelta=1e3/60,this.timescale=1,this.useFixedDelta=!1,this._autoReset=!1}get autoReset(){return this._autoReset}set autoReset(n){typeof document<"u"&&document.hidden!==void 0&&(n?document.addEventListener("visibilitychange",this):document.removeEventListener("visibilitychange",this),this._autoReset=n)}get delta(){return this._delta*tu}get fixedDelta(){return this._fixedDelta*tu}set fixedDelta(n){this._fixedDelta=n*ET}get elapsed(){return this._elapsed*tu}update(n){this.useFixedDelta?this._delta=this.fixedDelta:(this.previousTime=this.currentTime,this.currentTime=(n!==void 0?n:performance.now())-this.startTime,this._delta=this.currentTime-this.previousTime),this._delta*=this.timescale,this._elapsed+=this._delta}reset(){this._delta=0,this._elapsed=0,this.currentTime=performance.now()-this.startTime}getDelta(){return this.delta}getElapsed(){return this.elapsed}handleEvent(n){document.hidden||(this.currentTime=performance.now()-this.startTime)}dispose(){this.autoReset=!1}},AT=class{constructor(n=null,{depthBuffer:e=!0,stencilBuffer:t=!1,multisampling:i=0,frameBufferType:r=Yt}={}){this.renderer=null,this.inputBuffer=this.createBuffer(e,t,r,i),this.outputBuffer=this.inputBuffer.clone(),this.copyPass=new MT,this.depthRenderTarget=null,this.passes=[],this.timer=new wT,this.autoRenderToScreen=!0,this.setRenderer(n)}get stableDepthTexture(){return this.depthRenderTarget===null?null:this.depthRenderTarget.depthTexture}get multisampling(){return this.inputBuffer.samples}set multisampling(n){const e=this.renderer===null?n:TT(this.renderer,n);this.multisampling!==e&&(this.inputBuffer.samples=e,this.outputBuffer.samples=e,this.inputBuffer.dispose(),this.outputBuffer.dispose())}getTimer(){return this.timer}getRenderer(){return this.renderer}setRenderer(n){if(this.renderer=n,n!==null){const e=n.getSize(new Xe),t=n.getContext().getContextAttributes().alpha,i=this.inputBuffer.texture.type;i===Yt&&n.outputColorSpace===Tt&&(this.inputBuffer.texture.colorSpace=Tt,this.outputBuffer.texture.colorSpace=Tt,this.inputBuffer.dispose(),this.outputBuffer.dispose());const r=this.multisampling;this.multisampling=r,n.autoClear=!1,this.setSize(e.width,e.height);for(const s of this.passes)s.initialize(n,t,i)}}replaceRenderer(n,e=!0){const t=this.renderer,i=t.domElement.parentNode;return this.setRenderer(n),e&&i!==null&&(i.removeChild(t.domElement),i.appendChild(n.domElement)),t}createDepthTexture(){const n=new Xi;n.name="EffectComposer.InputDepth",this.inputBuffer.stencilBuffer?(n.format=dr,n.type=Hs):n.type=fi;const e=new Xi;e.format=n.format,e.type=n.type,e.name="EffectComposer.OutputDepth";const t=new Xi;t.format=n.format,t.type=n.type,t.name="EffectComposer.StableDepth",this.inputBuffer.depthTexture=n,this.outputBuffer.depthTexture=e,this.inputBuffer.dispose(),this.outputBuffer.dispose();const{width:i,height:r}=this.inputBuffer;this.depthRenderTarget=new Qt(i,r,{depthBuffer:!0,stencilBuffer:this.inputBuffer.stencilBuffer,depthTexture:t})}blitDepthBuffer(n){const e=this.renderer,t=this.depthRenderTarget,i=e.properties,r=e.getContext();e.setRenderTarget(t);const s=i.get(n).__webglFramebuffer,a=i.get(t).__webglFramebuffer,o=n.stencilBuffer?r.DEPTH_BUFFER_BIT|r.STENCIL_BUFFER_BIT:r.DEPTH_BUFFER_BIT;r.bindFramebuffer(r.READ_FRAMEBUFFER,s),r.bindFramebuffer(r.DRAW_FRAMEBUFFER,a),r.blitFramebuffer(0,0,n.width,n.height,0,0,t.width,t.height,o,r.NEAREST),r.bindFramebuffer(r.READ_FRAMEBUFFER,null),r.bindFramebuffer(r.DRAW_FRAMEBUFFER,null),e.setRenderTarget(null)}deleteDepthTexture(){const n=this.stableDepthTexture;for(const e of this.passes)e.getDepthTexture()===n&&e.setDepthTexture(null);this.depthRenderTarget!==null&&(this.depthRenderTarget.dispose(),this.depthRenderTarget=null),this.inputBuffer.depthTexture!==null&&(this.inputBuffer.depthTexture.dispose(),this.inputBuffer.depthTexture=null),this.outputBuffer.depthTexture!==null&&(this.outputBuffer.depthTexture.dispose(),this.outputBuffer.depthTexture=null)}createBuffer(n,e,t,i){const r=this.renderer,s=r===null?new Xe:r.getDrawingBufferSize(new Xe),a=new Qt(s.width,s.height,{minFilter:Gt,magFilter:Gt,samples:i,stencilBuffer:e,depthBuffer:n,type:t});return t===Yt&&r!==null&&r.outputColorSpace===Tt&&(a.texture.colorSpace=Tt),a.texture.name="EffectComposer.Buffer",a.texture.generateMipmaps=!1,a}setMainScene(n){for(const e of this.passes)e.mainScene=n}setMainCamera(n){for(const e of this.passes)e.mainCamera=n}addPass(n,e){const t=this.passes,i=this.renderer,r=i.getDrawingBufferSize(new Xe),s=i.getContext().getContextAttributes().alpha,a=this.inputBuffer.texture.type;if(n.renderer=i,n.setSize(r.width,r.height),n.initialize(i,s,a),this.autoRenderToScreen&&(t.length>0&&(t[t.length-1].renderToScreen=!1),n.renderToScreen&&(this.autoRenderToScreen=!1)),e!==void 0?t.splice(e,0,n):t.push(n),this.autoRenderToScreen&&(t[t.length-1].renderToScreen=!0),n.needsDepthTexture||this.depthRenderTarget!==null)if(this.depthRenderTarget===null){this.createDepthTexture();for(const o of t)o.setDepthTexture(this.stableDepthTexture)}else n.setDepthTexture(this.stableDepthTexture)}removePass(n){const e=this.passes,t=e.indexOf(n);if(t!==-1&&e.splice(t,1).length>0){const s=this.stableDepthTexture;if(s!==null){const a=(l,c)=>l||c.needsDepthTexture;e.reduce(a,!1)||(n.getDepthTexture()===s&&n.setDepthTexture(null),this.deleteDepthTexture())}this.autoRenderToScreen&&t===e.length&&(n.renderToScreen=!1,e.length>0&&(e[e.length-1].renderToScreen=!0))}}removeAllPasses(){const n=this.passes;this.deleteDepthTexture(),n.length>0&&(this.autoRenderToScreen&&(n[n.length-1].renderToScreen=!1),this.passes=[])}render(n){const e=this.renderer,t=this.copyPass;let i=this.inputBuffer,r=this.outputBuffer,s,a=!1;n===void 0&&(this.timer.update(),n=this.timer.getDelta());for(const o of this.passes)if(o.enabled){if(o.render(e,i,r,n,a),o.needsDepthBlit&&this.depthRenderTarget!==null&&this.blitDepthBuffer(i),o.needsSwap){if(a){t.renderToScreen=o.renderToScreen;const l=e.getContext(),c=e.state.buffers.stencil;c.setFunc(l.NOTEQUAL,1,4294967295),t.render(e,i,r,n,a),c.setFunc(l.EQUAL,1,4294967295)}s=i,i=r,r=s}o instanceof ST?a=!0:o instanceof yT&&(a=!1)}}setSize(n,e,t){const i=this.renderer,r=i.getSize(new Xe);(n===void 0||e===void 0)&&(n=r.width,e=r.height),(r.width!==n||r.height!==e)&&i.setSize(n,e,t);const s=i.getDrawingBufferSize(new Xe);this.inputBuffer.setSize(s.width,s.height),this.outputBuffer.setSize(s.width,s.height),this.depthRenderTarget!==null&&this.depthRenderTarget.setSize(s.width,s.height);for(const a of this.passes)a.setSize(s.width,s.height)}reset(){this.dispose(),this.autoRenderToScreen=!0}dispose(){for(const n of this.passes)n.dispose();this.deleteDepthTexture(),this.inputBuffer.dispose(),this.outputBuffer.dispose(),this.copyPass.dispose(),this.timer.dispose(),this.passes=[],gi.fullscreenGeometry.dispose()}},Kr={NONE:0,DEPTH:1,CONVOLUTION:2},gt={FRAGMENT_HEAD:"FRAGMENT_HEAD",FRAGMENT_MAIN_UV:"FRAGMENT_MAIN_UV",FRAGMENT_MAIN_IMAGE:"FRAGMENT_MAIN_IMAGE",VERTEX_HEAD:"VERTEX_HEAD",VERTEX_MAIN_SUPPORT:"VERTEX_MAIN_SUPPORT"},RT=class{constructor(){this.shaderParts=new Map([[gt.FRAGMENT_HEAD,null],[gt.FRAGMENT_MAIN_UV,null],[gt.FRAGMENT_MAIN_IMAGE,null],[gt.VERTEX_HEAD,null],[gt.VERTEX_MAIN_SUPPORT,null]]),this.defines=new Map,this.uniforms=new Map,this.blendModes=new Map,this.extensions=new Set,this.attributes=Kr.NONE,this.varyings=new Set,this.uvTransformation=!1,this.readDepth=!1,this.colorSpace=Vs}},nu=!1,Wp=class{constructor(n=null){this.originalMaterials=new Map,this.material=null,this.materials=null,this.materialsBackSide=null,this.materialsDoubleSide=null,this.materialsFlatShaded=null,this.materialsFlatShadedBackSide=null,this.materialsFlatShadedDoubleSide=null,this.setMaterial(n),this.meshCount=0,this.replaceMaterial=e=>{if(e.isMesh){let t;if(e.material.flatShading)switch(e.material.side){case An:t=this.materialsFlatShadedDoubleSide;break;case on:t=this.materialsFlatShadedBackSide;break;default:t=this.materialsFlatShaded;break}else switch(e.material.side){case An:t=this.materialsDoubleSide;break;case on:t=this.materialsBackSide;break;default:t=this.materials;break}this.originalMaterials.set(e,e.material),e.isSkinnedMesh?e.material=t[2]:e.isInstancedMesh?e.material=t[1]:e.material=t[0],++this.meshCount}}}cloneMaterial(n){if(!(n instanceof ln))return n.clone();const e=n.uniforms,t=new Map;for(const r in e){const s=e[r].value;s.isRenderTargetTexture&&(e[r].value=null,t.set(r,s))}const i=n.clone();for(const r of t)e[r[0]].value=r[1],i.uniforms[r[0]].value=r[1];return i}setMaterial(n){if(this.disposeMaterials(),this.material=n,n!==null){const e=this.materials=[this.cloneMaterial(n),this.cloneMaterial(n),this.cloneMaterial(n)];for(const t of e)t.uniforms=Object.assign({},n.uniforms),t.side=ji;e[2].skinning=!0,this.materialsBackSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.side=on,i}),this.materialsDoubleSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.side=An,i}),this.materialsFlatShaded=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.flatShading=!0,i}),this.materialsFlatShadedBackSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.flatShading=!0,i.side=on,i}),this.materialsFlatShadedDoubleSide=e.map(t=>{const i=this.cloneMaterial(t);return i.uniforms=Object.assign({},n.uniforms),i.flatShading=!0,i.side=An,i})}}render(n,e,t){const i=n.shadowMap.enabled;if(n.shadowMap.enabled=!1,nu){const r=this.originalMaterials;this.meshCount=0,e.traverse(this.replaceMaterial),n.render(e,t);for(const s of r)s[0].material=s[1];this.meshCount!==r.size&&r.clear()}else{const r=e.overrideMaterial;e.overrideMaterial=this.material,n.render(e,t),e.overrideMaterial=r}n.shadowMap.enabled=i}disposeMaterials(){if(this.material!==null){const n=this.materials.concat(this.materialsBackSide).concat(this.materialsDoubleSide).concat(this.materialsFlatShaded).concat(this.materialsFlatShadedBackSide).concat(this.materialsFlatShadedDoubleSide);for(const e of n)e.dispose()}}dispose(){this.originalMaterials.clear(),this.disposeMaterials()}static get workaroundEnabled(){return nu}static set workaroundEnabled(n){nu=n}},cr=-1,Pi=class extends mi{constructor(n=null,e=cr,t=cr,i=1){super(),n!==null&&this.addEventListener("change",()=>n.setSize(this.baseSize.width,this.baseSize.height)),this.baseSize=new Xe(1,1),this.preferredSize=new Xe(e,t),this.target=this.preferredSize,this.s=i,this.effectiveSize=new Xe,this.addEventListener("change",()=>this.updateEffectiveSize()),this.updateEffectiveSize()}updateEffectiveSize(){const n=this.baseSize,e=this.preferredSize,t=this.effectiveSize,i=this.scale;e.width!==cr?t.width=e.width:e.height!==cr?t.width=Math.round(e.height*(n.width/Math.max(n.height,1))):t.width=Math.round(n.width*i),e.height!==cr?t.height=e.height:e.width!==cr?t.height=Math.round(e.width/Math.max(n.width/Math.max(n.height,1),1)):t.height=Math.round(n.height*i)}get width(){return this.effectiveSize.width}set width(n){this.preferredWidth=n}get height(){return this.effectiveSize.height}set height(n){this.preferredHeight=n}getWidth(){return this.width}getHeight(){return this.height}get scale(){return this.s}set scale(n){this.s!==n&&(this.s=n,this.preferredSize.setScalar(cr),this.dispatchEvent({type:"change"}))}getScale(){return this.scale}setScale(n){this.scale=n}get baseWidth(){return this.baseSize.width}set baseWidth(n){this.baseSize.width!==n&&(this.baseSize.width=n,this.dispatchEvent({type:"change"}))}getBaseWidth(){return this.baseWidth}setBaseWidth(n){this.baseWidth=n}get baseHeight(){return this.baseSize.height}set baseHeight(n){this.baseSize.height!==n&&(this.baseSize.height=n,this.dispatchEvent({type:"change"}))}getBaseHeight(){return this.baseHeight}setBaseHeight(n){this.baseHeight=n}setBaseSize(n,e){(this.baseSize.width!==n||this.baseSize.height!==e)&&(this.baseSize.set(n,e),this.dispatchEvent({type:"change"}))}get preferredWidth(){return this.preferredSize.width}set preferredWidth(n){this.preferredSize.width!==n&&(this.preferredSize.width=n,this.dispatchEvent({type:"change"}))}getPreferredWidth(){return this.preferredWidth}setPreferredWidth(n){this.preferredWidth=n}get preferredHeight(){return this.preferredSize.height}set preferredHeight(n){this.preferredSize.height!==n&&(this.preferredSize.height=n,this.dispatchEvent({type:"change"}))}getPreferredHeight(){return this.preferredHeight}setPreferredHeight(n){this.preferredHeight=n}setPreferredSize(n,e){(this.preferredSize.width!==n||this.preferredSize.height!==e)&&(this.preferredSize.set(n,e),this.dispatchEvent({type:"change"}))}copy(n){this.s=n.scale,this.baseSize.set(n.baseWidth,n.baseHeight),this.preferredSize.set(n.preferredWidth,n.preferredHeight),this.dispatchEvent({type:"change"})}static get AUTO_SIZE(){return cr}},ct={ADD:0,ALPHA:1,AVERAGE:2,COLOR:3,COLOR_BURN:4,COLOR_DODGE:5,DARKEN:6,DIFFERENCE:7,DIVIDE:8,DST:9,EXCLUSION:10,HARD_LIGHT:11,HARD_MIX:12,HUE:13,INVERT:14,INVERT_RGB:15,LIGHTEN:16,LINEAR_BURN:17,LINEAR_DODGE:18,LINEAR_LIGHT:19,LUMINOSITY:20,MULTIPLY:21,NEGATION:22,NORMAL:23,OVERLAY:24,PIN_LIGHT:25,REFLECT:26,SATURATION:27,SCREEN:28,SOFT_LIGHT:29,SRC:30,SUBTRACT:31,VIVID_LIGHT:32},CT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",PT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return mix(dst,src,src.a*opacity);}",DT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=(dst.rgb+src.rgb)*0.5;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",UT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(b.xy,a.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",LT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=dst.rgb,b=src.rgb;vec3 c=mix(step(0.0,b)*(1.0-min(vec3(1.0),(1.0-a)/max(b,1e-9))),vec3(1.0),step(1.0,a));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",IT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=dst.rgb,b=src.rgb;vec3 c=step(0.0,a)*mix(min(vec3(1.0),a/max(1.0-b,1e-9)),vec3(1.0),step(1.0,b));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",FT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=min(dst.rgb,src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",NT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=abs(dst.rgb-src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",OT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb/max(src.rgb,1e-9);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",BT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb-2.0*dst.rgb*src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",kT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=min(dst.rgb,1.0);vec3 b=min(src.rgb,1.0);vec3 c=mix(2.0*a*b,1.0-2.0*(1.0-a)*(1.0-b),step(0.5,b));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",zT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=step(1.0,dst.rgb+src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",GT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(b.x,a.yz));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",HT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(1.0-src.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",VT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=src.rgb*max(1.0-dst.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",WT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(dst.rgb,src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",XT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=clamp(src.rgb+dst.rgb-1.0,0.0,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",jT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=min(dst.rgb+src.rgb,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",YT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=clamp(2.0*src.rgb+dst.rgb-1.0,0.0,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",qT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(a.xy,b.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",KT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb*src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",ZT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(1.0-abs(1.0-dst.rgb-src.rgb),0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",$T="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return mix(dst,src,opacity);}",JT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=2.0*src.rgb*dst.rgb;vec3 b=1.0-2.0*(1.0-src.rgb)*(1.0-dst.rgb);vec3 c=mix(a,b,step(0.5,dst.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",QT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 src2=2.0*src.rgb;vec3 c=mix(mix(src2,dst.rgb,step(0.5*dst.rgb,src.rgb)),max(src2-1.0,vec3(0.0)),step(dst.rgb,src2-1.0));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",eE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=min(dst.rgb*dst.rgb/max(1.0-src.rgb,1e-9),1.0);vec3 c=mix(a,src.rgb,step(1.0,src.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",tE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(a.x,b.y,a.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",nE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb-min(dst.rgb*src.rgb,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",iE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 src2=2.0*src.rgb;vec3 d=dst.rgb+(src2-1.0);vec3 w=step(0.5,src.rgb);vec3 a=dst.rgb-(1.0-src2)*dst.rgb*(1.0-dst.rgb);vec3 b=mix(d*(sqrt(dst.rgb)-dst.rgb),d*dst.rgb*((16.0*dst.rgb-12.0)*dst.rgb+3.0),w*(1.0-step(0.25,dst.rgb)));vec3 c=mix(a,b,w);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",rE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return src;}",sE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(dst.rgb-src.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",aE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=mix(max(1.0-min((1.0-dst.rgb)/(2.0*src.rgb),1.0),0.0),min(dst.rgb/(2.0*(1.0-src.rgb)),1.0),step(0.5,src.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",oE=new Map([[ct.ADD,CT],[ct.ALPHA,PT],[ct.AVERAGE,DT],[ct.COLOR,UT],[ct.COLOR_BURN,LT],[ct.COLOR_DODGE,IT],[ct.DARKEN,FT],[ct.DIFFERENCE,NT],[ct.DIVIDE,OT],[ct.DST,null],[ct.EXCLUSION,BT],[ct.HARD_LIGHT,kT],[ct.HARD_MIX,zT],[ct.HUE,GT],[ct.INVERT,HT],[ct.INVERT_RGB,VT],[ct.LIGHTEN,WT],[ct.LINEAR_BURN,XT],[ct.LINEAR_DODGE,jT],[ct.LINEAR_LIGHT,YT],[ct.LUMINOSITY,qT],[ct.MULTIPLY,KT],[ct.NEGATION,ZT],[ct.NORMAL,$T],[ct.OVERLAY,JT],[ct.PIN_LIGHT,QT],[ct.REFLECT,eE],[ct.SATURATION,tE],[ct.SCREEN,nE],[ct.SOFT_LIGHT,iE],[ct.SRC,rE],[ct.SUBTRACT,sE],[ct.VIVID_LIGHT,aE]]),lE=class extends mi{constructor(n,e=1){super(),this._blendFunction=n,this.opacity=new vt(e)}getOpacity(){return this.opacity.value}setOpacity(n){this.opacity.value=n}get blendFunction(){return this._blendFunction}set blendFunction(n){this._blendFunction=n,this.dispatchEvent({type:"change"})}getBlendFunction(){return this.blendFunction}setBlendFunction(n){this.blendFunction=n}getShaderCode(){return oE.get(this.blendFunction)}},cE=class extends mi{constructor(n,e,{attributes:t=Kr.NONE,blendFunction:i=ct.NORMAL,defines:r=new Map,uniforms:s=new Map,extensions:a=null,vertexShader:o=null}={}){super(),this.name=n,this.renderer=null,this.attributes=t,this.fragmentShader=e,this.vertexShader=o,this.defines=r,this.uniforms=s,this.extensions=a,this.blendMode=new lE(i),this.blendMode.addEventListener("change",l=>this.setChanged()),this._inputColorSpace=Vs,this._outputColorSpace=Ti}get inputColorSpace(){return this._inputColorSpace}set inputColorSpace(n){this._inputColorSpace=n,this.setChanged()}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(n){this._outputColorSpace=n,this.setChanged()}set mainScene(n){}set mainCamera(n){}getName(){return this.name}setRenderer(n){this.renderer=n}getDefines(){return this.defines}getUniforms(){return this.uniforms}getExtensions(){return this.extensions}getBlendMode(){return this.blendMode}getAttributes(){return this.attributes}setAttributes(n){this.attributes=n,this.setChanged()}getFragmentShader(){return this.fragmentShader}setFragmentShader(n){this.fragmentShader=n,this.setChanged()}getVertexShader(){return this.vertexShader}setVertexShader(n){this.vertexShader=n,this.setChanged()}setChanged(){this.dispatchEvent({type:"change"})}setDepthTexture(n,e=Qa){}update(n,e,t){}setSize(n,e){}initialize(n,e,t){}dispose(){for(const n of Object.keys(this)){const e=this[n];(e instanceof Qt||e instanceof $i||e instanceof Jt||e instanceof gi)&&this[n].dispose()}}},Af={MEDIUM:2,LARGE:3},uE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;void main(){vec4 sum=texture2D(inputBuffer,vUv0);sum+=texture2D(inputBuffer,vUv1);sum+=texture2D(inputBuffer,vUv2);sum+=texture2D(inputBuffer,vUv3);gl_FragColor=sum*0.25;
#include <colorspace_fragment>
}`,hE="uniform vec4 texelSize;uniform float kernel;uniform float scale;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;void main(){vec2 uv=position.xy*0.5+0.5;vec2 dUv=(texelSize.xy*vec2(kernel)+texelSize.zw)*scale;vUv0=vec2(uv.x-dUv.x,uv.y+dUv.y);vUv1=vec2(uv.x+dUv.x,uv.y+dUv.y);vUv2=vec2(uv.x+dUv.x,uv.y-dUv.y);vUv3=vec2(uv.x-dUv.x,uv.y-dUv.y);gl_Position=vec4(position.xy,1.0,1.0);}",fE=[new Float32Array([0,0]),new Float32Array([0,1,1]),new Float32Array([0,1,1,2]),new Float32Array([0,1,2,2,3]),new Float32Array([0,1,2,3,4,4,5]),new Float32Array([0,1,2,3,4,5,7,8,9,10])],dE=class extends ln{constructor(n=new Ut){super({name:"KawaseBlurMaterial",uniforms:{inputBuffer:new vt(null),texelSize:new vt(new Ut),scale:new vt(1),kernel:new vt(0)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:uE,vertexShader:hE}),this.setTexelSize(n.x,n.y),this.kernelSize=Af.MEDIUM}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.inputBuffer=n}get kernelSequence(){return fE[this.kernelSize]}get scale(){return this.uniforms.scale.value}set scale(n){this.uniforms.scale.value=n}getScale(){return this.uniforms.scale.value}setScale(n){this.uniforms.scale.value=n}getKernel(){return null}get kernel(){return this.uniforms.kernel.value}set kernel(n){this.uniforms.kernel.value=n}setKernel(n){this.kernel=n}setTexelSize(n,e){this.uniforms.texelSize.value.set(n,e,n*.5,e*.5)}setSize(n,e){const t=1/n,i=1/e;this.uniforms.texelSize.value.set(t,i,t*.5,i*.5)}},pE=class extends gi{constructor({kernelSize:n=Af.MEDIUM,resolutionScale:e=.5,width:t=Pi.AUTO_SIZE,height:i=Pi.AUTO_SIZE,resolutionX:r=t,resolutionY:s=i}={}){super("KawaseBlurPass"),this.renderTargetA=new Qt(1,1,{depthBuffer:!1}),this.renderTargetA.texture.name="Blur.Target.A",this.renderTargetB=this.renderTargetA.clone(),this.renderTargetB.texture.name="Blur.Target.B";const a=this.resolution=new Pi(this,r,s,e);a.addEventListener("change",o=>this.setSize(a.baseWidth,a.baseHeight)),this._blurMaterial=new dE,this._blurMaterial.kernelSize=n,this.copyMaterial=new _g}getResolution(){return this.resolution}get blurMaterial(){return this._blurMaterial}set blurMaterial(n){this._blurMaterial=n}get dithering(){return this.copyMaterial.dithering}set dithering(n){this.copyMaterial.dithering=n}get kernelSize(){return this.blurMaterial.kernelSize}set kernelSize(n){this.blurMaterial.kernelSize=n}get width(){return this.resolution.width}set width(n){this.resolution.preferredWidth=n}get height(){return this.resolution.height}set height(n){this.resolution.preferredHeight=n}get scale(){return this.blurMaterial.scale}set scale(n){this.blurMaterial.scale=n}getScale(){return this.blurMaterial.scale}setScale(n){this.blurMaterial.scale=n}getKernelSize(){return this.kernelSize}setKernelSize(n){this.kernelSize=n}getResolutionScale(){return this.resolution.scale}setResolutionScale(n){this.resolution.scale=n}render(n,e,t,i,r){const s=this.scene,a=this.camera,o=this.renderTargetA,l=this.renderTargetB,c=this.blurMaterial,u=c.kernelSequence;let f=e;this.fullscreenMaterial=c;for(let h=0,d=u.length;h<d;++h){const m=(h&1)===0?o:l;c.kernel=u[h],c.inputBuffer=f.texture,n.setRenderTarget(m),n.render(s,a),f=m}this.fullscreenMaterial=this.copyMaterial,this.copyMaterial.inputBuffer=f.texture,n.setRenderTarget(this.renderToScreen?null:t),n.render(s,a)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e);const i=t.width,r=t.height;this.renderTargetA.setSize(i,r),this.renderTargetB.setSize(i,r),this.blurMaterial.setSize(n,e)}initialize(n,e,t){t!==void 0&&(this.renderTargetA.texture.type=t,this.renderTargetB.texture.type=t,t!==Yt?(this.blurMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1",this.copyMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1"):n!==null&&n.outputColorSpace===Tt&&(this.renderTargetA.texture.colorSpace=Tt,this.renderTargetB.texture.colorSpace=Tt))}static get AUTO_SIZE(){return Pi.AUTO_SIZE}},mE=`#include <common>
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
}`,gE=class extends ln{constructor(n=!1,e=null){super({name:"LuminanceMaterial",defines:{THREE_REVISION:Ja.replace(/\D+/g,"")},uniforms:{inputBuffer:new vt(null),threshold:new vt(0),smoothing:new vt(1),range:new vt(null)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:mE,vertexShader:gg}),this.colorOutput=n,this.luminanceRange=e}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.uniforms.inputBuffer.value=n}get threshold(){return this.uniforms.threshold.value}set threshold(n){this.smoothing>0||n>0?this.defines.THRESHOLD="1":delete this.defines.THRESHOLD,this.uniforms.threshold.value=n}getThreshold(){return this.threshold}setThreshold(n){this.threshold=n}get smoothing(){return this.uniforms.smoothing.value}set smoothing(n){this.threshold>0||n>0?this.defines.THRESHOLD="1":delete this.defines.THRESHOLD,this.uniforms.smoothing.value=n}getSmoothingFactor(){return this.smoothing}setSmoothingFactor(n){this.smoothing=n}get useThreshold(){return this.threshold>0||this.smoothing>0}set useThreshold(n){}get colorOutput(){return this.defines.COLOR!==void 0}set colorOutput(n){n?this.defines.COLOR="1":delete this.defines.COLOR,this.needsUpdate=!0}isColorOutputEnabled(n){return this.colorOutput}setColorOutputEnabled(n){this.colorOutput=n}get useRange(){return this.luminanceRange!==null}set useRange(n){this.luminanceRange=null}get luminanceRange(){return this.uniforms.range.value}set luminanceRange(n){n!==null?this.defines.RANGE="1":delete this.defines.RANGE,this.uniforms.range.value=n,this.needsUpdate=!0}getLuminanceRange(){return this.luminanceRange}setLuminanceRange(n){this.luminanceRange=n}},_E=class extends gi{constructor({renderTarget:n,luminanceRange:e,colorOutput:t,resolutionScale:i=1,width:r=Pi.AUTO_SIZE,height:s=Pi.AUTO_SIZE,resolutionX:a=r,resolutionY:o=s}={}){super("LuminancePass"),this.fullscreenMaterial=new gE(t,e),this.needsSwap=!1,this.renderTarget=n,this.renderTarget===void 0&&(this.renderTarget=new Qt(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="LuminancePass.Target");const l=this.resolution=new Pi(this,a,o,i);l.addEventListener("change",c=>this.setSize(l.baseWidth,l.baseHeight))}get texture(){return this.renderTarget.texture}getTexture(){return this.renderTarget.texture}getResolution(){return this.resolution}render(n,e,t,i,r){const s=this.fullscreenMaterial;s.inputBuffer=e.texture,n.setRenderTarget(this.renderToScreen?null:this.renderTarget),n.render(this.scene,this.camera)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e),this.renderTarget.setSize(t.width,t.height)}initialize(n,e,t){t!==void 0&&t!==Yt&&(this.renderTarget.texture.type=t,this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1")}},vE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
#define WEIGHT_INNER 0.125
#define WEIGHT_OUTER 0.05556
varying vec2 vUv;varying vec2 vUv00;varying vec2 vUv01;varying vec2 vUv02;varying vec2 vUv03;varying vec2 vUv04;varying vec2 vUv05;varying vec2 vUv06;varying vec2 vUv07;varying vec2 vUv08;varying vec2 vUv09;varying vec2 vUv10;varying vec2 vUv11;float clampToBorder(const in vec2 uv){return float(uv.s>=0.0&&uv.s<=1.0&&uv.t>=0.0&&uv.t<=1.0);}void main(){vec4 c=vec4(0.0);vec4 w=WEIGHT_INNER*vec4(clampToBorder(vUv00),clampToBorder(vUv01),clampToBorder(vUv02),clampToBorder(vUv03));c+=w.x*texture2D(inputBuffer,vUv00);c+=w.y*texture2D(inputBuffer,vUv01);c+=w.z*texture2D(inputBuffer,vUv02);c+=w.w*texture2D(inputBuffer,vUv03);w=WEIGHT_OUTER*vec4(clampToBorder(vUv04),clampToBorder(vUv05),clampToBorder(vUv06),clampToBorder(vUv07));c+=w.x*texture2D(inputBuffer,vUv04);c+=w.y*texture2D(inputBuffer,vUv05);c+=w.z*texture2D(inputBuffer,vUv06);c+=w.w*texture2D(inputBuffer,vUv07);w=WEIGHT_OUTER*vec4(clampToBorder(vUv08),clampToBorder(vUv09),clampToBorder(vUv10),clampToBorder(vUv11));c+=w.x*texture2D(inputBuffer,vUv08);c+=w.y*texture2D(inputBuffer,vUv09);c+=w.z*texture2D(inputBuffer,vUv10);c+=w.w*texture2D(inputBuffer,vUv11);c+=WEIGHT_OUTER*texture2D(inputBuffer,vUv);gl_FragColor=c;
#include <colorspace_fragment>
}`,xE="uniform vec2 texelSize;varying vec2 vUv;varying vec2 vUv00;varying vec2 vUv01;varying vec2 vUv02;varying vec2 vUv03;varying vec2 vUv04;varying vec2 vUv05;varying vec2 vUv06;varying vec2 vUv07;varying vec2 vUv08;varying vec2 vUv09;varying vec2 vUv10;varying vec2 vUv11;void main(){vUv=position.xy*0.5+0.5;vUv00=vUv+texelSize*vec2(-1.0,1.0);vUv01=vUv+texelSize*vec2(1.0,1.0);vUv02=vUv+texelSize*vec2(-1.0,-1.0);vUv03=vUv+texelSize*vec2(1.0,-1.0);vUv04=vUv+texelSize*vec2(-2.0,2.0);vUv05=vUv+texelSize*vec2(0.0,2.0);vUv06=vUv+texelSize*vec2(2.0,2.0);vUv07=vUv+texelSize*vec2(-2.0,0.0);vUv08=vUv+texelSize*vec2(2.0,0.0);vUv09=vUv+texelSize*vec2(-2.0,-2.0);vUv10=vUv+texelSize*vec2(0.0,-2.0);vUv11=vUv+texelSize*vec2(2.0,-2.0);gl_Position=vec4(position.xy,1.0,1.0);}",yE=class extends ln{constructor(){super({name:"DownsamplingMaterial",uniforms:{inputBuffer:new vt(null),texelSize:new vt(new Xe)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:vE,vertexShader:xE})}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setSize(n,e){this.uniforms.texelSize.value.set(1/n,1/e)}},bE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;uniform mediump sampler2D supportBuffer;
#else
uniform lowp sampler2D inputBuffer;uniform lowp sampler2D supportBuffer;
#endif
uniform float radius;varying vec2 vUv;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;varying vec2 vUv4;varying vec2 vUv5;varying vec2 vUv6;varying vec2 vUv7;void main(){vec4 c=vec4(0.0);c+=texture2D(inputBuffer,vUv0)*0.0625;c+=texture2D(inputBuffer,vUv1)*0.125;c+=texture2D(inputBuffer,vUv2)*0.0625;c+=texture2D(inputBuffer,vUv3)*0.125;c+=texture2D(inputBuffer,vUv)*0.25;c+=texture2D(inputBuffer,vUv4)*0.125;c+=texture2D(inputBuffer,vUv5)*0.0625;c+=texture2D(inputBuffer,vUv6)*0.125;c+=texture2D(inputBuffer,vUv7)*0.0625;vec4 baseColor=texture2D(supportBuffer,vUv);gl_FragColor=mix(baseColor,c,radius);
#include <colorspace_fragment>
}`,ME="uniform vec2 texelSize;varying vec2 vUv;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;varying vec2 vUv4;varying vec2 vUv5;varying vec2 vUv6;varying vec2 vUv7;void main(){vUv=position.xy*0.5+0.5;vUv0=vUv+texelSize*vec2(-1.0,1.0);vUv1=vUv+texelSize*vec2(0.0,1.0);vUv2=vUv+texelSize*vec2(1.0,1.0);vUv3=vUv+texelSize*vec2(-1.0,0.0);vUv4=vUv+texelSize*vec2(1.0,0.0);vUv5=vUv+texelSize*vec2(-1.0,-1.0);vUv6=vUv+texelSize*vec2(0.0,-1.0);vUv7=vUv+texelSize*vec2(1.0,-1.0);gl_Position=vec4(position.xy,1.0,1.0);}",SE=class extends ln{constructor(){super({name:"UpsamplingMaterial",uniforms:{inputBuffer:new vt(null),supportBuffer:new vt(null),texelSize:new vt(new Xe),radius:new vt(.85)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:bE,vertexShader:ME})}set inputBuffer(n){this.uniforms.inputBuffer.value=n}set supportBuffer(n){this.uniforms.supportBuffer.value=n}get radius(){return this.uniforms.radius.value}set radius(n){this.uniforms.radius.value=n}setSize(n,e){this.uniforms.texelSize.value.set(1/n,1/e)}},TE=class extends gi{constructor(){super("MipmapBlurPass"),this.needsSwap=!1,this.renderTarget=new Qt(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="Upsampling.Mipmap0",this.downsamplingMipmaps=[],this.upsamplingMipmaps=[],this.downsamplingMaterial=new yE,this.upsamplingMaterial=new SE,this.resolution=new Xe}get texture(){return this.renderTarget.texture}get levels(){return this.downsamplingMipmaps.length}set levels(n){if(this.levels!==n){const e=this.renderTarget;this.dispose(),this.downsamplingMipmaps=[],this.upsamplingMipmaps=[];for(let t=0;t<n;++t){const i=e.clone();i.texture.name="Downsampling.Mipmap"+t,this.downsamplingMipmaps.push(i)}this.upsamplingMipmaps.push(e);for(let t=1,i=n-1;t<i;++t){const r=e.clone();r.texture.name="Upsampling.Mipmap"+t,this.upsamplingMipmaps.push(r)}this.setSize(this.resolution.x,this.resolution.y)}}get radius(){return this.upsamplingMaterial.radius}set radius(n){this.upsamplingMaterial.radius=n}render(n,e,t,i,r){const{scene:s,camera:a}=this,{downsamplingMaterial:o,upsamplingMaterial:l}=this,{downsamplingMipmaps:c,upsamplingMipmaps:u}=this;let f=e;this.fullscreenMaterial=o;for(let h=0,d=c.length;h<d;++h){const m=c[h];o.setSize(f.width,f.height),o.inputBuffer=f.texture,n.setRenderTarget(m),n.render(s,a),f=m}this.fullscreenMaterial=l;for(let h=u.length-1;h>=0;--h){const d=u[h];l.setSize(f.width,f.height),l.inputBuffer=f.texture,l.supportBuffer=c[h].texture,n.setRenderTarget(d),n.render(s,a),f=d}}setSize(n,e){const t=this.resolution;t.set(n,e);let i=t.width,r=t.height;for(let s=0,a=this.downsamplingMipmaps.length;s<a;++s)i=Math.round(i*.5),r=Math.round(r*.5),this.downsamplingMipmaps[s].setSize(i,r),s<this.upsamplingMipmaps.length&&this.upsamplingMipmaps[s].setSize(i,r)}initialize(n,e,t){if(t!==void 0){const i=this.downsamplingMipmaps.concat(this.upsamplingMipmaps);for(const r of i)r.texture.type=t;if(t!==Yt)this.downsamplingMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1",this.upsamplingMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1";else if(n!==null&&n.outputColorSpace===Tt)for(const r of i)r.texture.colorSpace=Tt}}dispose(){super.dispose();for(const n of this.downsamplingMipmaps.concat(this.upsamplingMipmaps))n.dispose()}},EE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D map;
#else
uniform lowp sampler2D map;
#endif
uniform float intensity;void mainImage(const in vec4 inputColor,const in vec2 uv,out vec4 outputColor){outputColor=texture2D(map,uv)*intensity;}`,wE=class extends cE{constructor({blendFunction:n=ct.SCREEN,luminanceThreshold:e=1,luminanceSmoothing:t=.03,mipmapBlur:i=!0,intensity:r=1,radius:s=.85,levels:a=8,kernelSize:o=Af.LARGE,resolutionScale:l=.5,width:c=Pi.AUTO_SIZE,height:u=Pi.AUTO_SIZE,resolutionX:f=c,resolutionY:h=u}={}){super("BloomEffect",EE,{blendFunction:n,uniforms:new Map([["map",new vt(null)],["intensity",new vt(r)]])}),this.renderTarget=new Qt(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="Bloom.Target",this.blurPass=new pE({kernelSize:o}),this.luminancePass=new _E({colorOutput:!0}),this.luminanceMaterial.threshold=e,this.luminanceMaterial.smoothing=t,this.mipmapBlurPass=new TE,this.mipmapBlurPass.enabled=i,this.mipmapBlurPass.radius=s,this.mipmapBlurPass.levels=a,this.uniforms.get("map").value=i?this.mipmapBlurPass.texture:this.renderTarget.texture;const d=this.resolution=new Pi(this,f,h,l);d.addEventListener("change",m=>this.setSize(d.baseWidth,d.baseHeight))}get texture(){return this.mipmapBlurPass.enabled?this.mipmapBlurPass.texture:this.renderTarget.texture}getTexture(){return this.texture}getResolution(){return this.resolution}getBlurPass(){return this.blurPass}getLuminancePass(){return this.luminancePass}get luminanceMaterial(){return this.luminancePass.fullscreenMaterial}getLuminanceMaterial(){return this.luminancePass.fullscreenMaterial}get width(){return this.resolution.width}set width(n){this.resolution.preferredWidth=n}get height(){return this.resolution.height}set height(n){this.resolution.preferredHeight=n}get dithering(){return this.blurPass.dithering}set dithering(n){this.blurPass.dithering=n}get kernelSize(){return this.blurPass.kernelSize}set kernelSize(n){this.blurPass.kernelSize=n}get distinction(){return console.warn(this.name,"distinction was removed"),1}set distinction(n){console.warn(this.name,"distinction was removed")}get intensity(){return this.uniforms.get("intensity").value}set intensity(n){this.uniforms.get("intensity").value=n}getIntensity(){return this.intensity}setIntensity(n){this.intensity=n}getResolutionScale(){return this.resolution.scale}setResolutionScale(n){this.resolution.scale=n}update(n,e,t){const i=this.renderTarget,r=this.luminancePass;r.enabled?(r.render(n,e),this.mipmapBlurPass.enabled?this.mipmapBlurPass.render(n,r.renderTarget):this.blurPass.render(n,r.renderTarget,i)):this.mipmapBlurPass.enabled?this.mipmapBlurPass.render(n,e):this.blurPass.render(n,e,i)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e),this.renderTarget.setSize(t.width,t.height),this.blurPass.resolution.copy(t),this.luminancePass.setSize(n,e),this.mipmapBlurPass.setSize(n,e)}initialize(n,e,t){this.blurPass.initialize(n,e,t),this.luminancePass.initialize(n,e,t),this.mipmapBlurPass.initialize(n,e,t),t!==void 0&&(this.renderTarget.texture.type=t,n!==null&&n.outputColorSpace===Tt&&(this.renderTarget.texture.colorSpace=Tt))}},AE=class extends gi{constructor(n,e,t=null){super("RenderPass",n,e),this.needsSwap=!1,this.needsDepthBlit=!0,this.clearPass=new vg,this.overrideMaterialManager=t===null?null:new Wp(t),this.ignoreBackground=!1,this.skipShadowMapUpdate=!1,this.selection=null}set mainScene(n){this.scene=n}set mainCamera(n){this.camera=n}get renderToScreen(){return super.renderToScreen}set renderToScreen(n){super.renderToScreen=n,this.clearPass.renderToScreen=n}get overrideMaterial(){const n=this.overrideMaterialManager;return n!==null?n.material:null}set overrideMaterial(n){const e=this.overrideMaterialManager;n!==null?e!==null?e.setMaterial(n):this.overrideMaterialManager=new Wp(n):e!==null&&(e.dispose(),this.overrideMaterialManager=null)}getOverrideMaterial(){return this.overrideMaterial}setOverrideMaterial(n){this.overrideMaterial=n}get clear(){return this.clearPass.enabled}set clear(n){this.clearPass.enabled=n}getSelection(){return this.selection}setSelection(n){this.selection=n}isBackgroundDisabled(){return this.ignoreBackground}setBackgroundDisabled(n){this.ignoreBackground=n}isShadowMapDisabled(){return this.skipShadowMapUpdate}setShadowMapDisabled(n){this.skipShadowMapUpdate=n}getClearPass(){return this.clearPass}render(n,e,t,i,r){const s=this.scene,a=this.camera,o=this.selection,l=a.layers.mask,c=s.background,u=n.shadowMap.autoUpdate,f=this.renderToScreen?null:e;o!==null&&a.layers.set(o.getLayer()),this.skipShadowMapUpdate&&(n.shadowMap.autoUpdate=!1),(this.ignoreBackground||this.clearPass.overrideClearColor!==null)&&(s.background=null),this.clearPass.enabled&&this.clearPass.render(n,e),n.setRenderTarget(f),this.overrideMaterialManager!==null?this.overrideMaterialManager.render(n,s,a):n.render(s,a),a.layers.mask=l,s.background=c,n.shadowMap.autoUpdate=u}},RE=`#include <common>
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
}`,CE="uniform vec2 resolution;uniform vec2 texelSize;uniform float cameraNear;uniform float cameraFar;uniform float aspect;uniform float time;varying vec2 vUv;VERTEX_HEAD void main(){vUv=position.xy*0.5+0.5;VERTEX_MAIN_SUPPORT gl_Position=vec4(position.xy,1.0,1.0);}",PE=class extends ln{constructor(n,e,t,i,r=!1){super({name:"EffectMaterial",defines:{THREE_REVISION:Ja.replace(/\D+/g,""),DEPTH_PACKING:"0",ENCODE_OUTPUT:"1"},uniforms:{inputBuffer:new vt(null),depthBuffer:new vt(null),resolution:new vt(new Xe),texelSize:new vt(new Xe),cameraNear:new vt(.3),cameraFar:new vt(1e3),aspect:new vt(1),time:new vt(0)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,dithering:r}),n&&this.setShaderParts(n),e&&this.setDefines(e),t&&this.setUniforms(t),this.copyCameraSettings(i)}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.uniforms.inputBuffer.value=n}get depthBuffer(){return this.uniforms.depthBuffer.value}set depthBuffer(n){this.uniforms.depthBuffer.value=n}get depthPacking(){return Number(this.defines.DEPTH_PACKING)}set depthPacking(n){this.defines.DEPTH_PACKING=n.toFixed(0),this.needsUpdate=!0}setDepthBuffer(n,e=Qa){this.depthBuffer=n,this.depthPacking=e}setShaderData(n){this.setShaderParts(n.shaderParts),this.setDefines(n.defines),this.setUniforms(n.uniforms),this.setExtensions(n.extensions)}setShaderParts(n){return this.fragmentShader=RE.replace(gt.FRAGMENT_HEAD,n.get(gt.FRAGMENT_HEAD)||"").replace(gt.FRAGMENT_MAIN_UV,n.get(gt.FRAGMENT_MAIN_UV)||"").replace(gt.FRAGMENT_MAIN_IMAGE,n.get(gt.FRAGMENT_MAIN_IMAGE)||""),this.vertexShader=CE.replace(gt.VERTEX_HEAD,n.get(gt.VERTEX_HEAD)||"").replace(gt.VERTEX_MAIN_SUPPORT,n.get(gt.VERTEX_MAIN_SUPPORT)||""),this.needsUpdate=!0,this}setDefines(n){for(const e of n.entries())this.defines[e[0]]=e[1];return this.needsUpdate=!0,this}setUniforms(n){for(const e of n.entries())this.uniforms[e[0]]=e[1];return this}setExtensions(n){this.extensions={};for(const e of n)this.extensions[e]=!0;return this}get encodeOutput(){return this.defines.ENCODE_OUTPUT!==void 0}set encodeOutput(n){this.encodeOutput!==n&&(n?this.defines.ENCODE_OUTPUT="1":delete this.defines.ENCODE_OUTPUT,this.needsUpdate=!0)}isOutputEncodingEnabled(n){return this.encodeOutput}setOutputEncodingEnabled(n){this.encodeOutput=n}get time(){return this.uniforms.time.value}set time(n){this.uniforms.time.value=n}setDeltaTime(n){this.uniforms.time.value+=n}adoptCameraSettings(n){this.copyCameraSettings(n)}copyCameraSettings(n){n&&(this.uniforms.cameraNear.value=n.near,this.uniforms.cameraFar.value=n.far,n instanceof Hn?this.defines.PERSPECTIVE_CAMERA="1":delete this.defines.PERSPECTIVE_CAMERA,this.needsUpdate=!0)}setSize(n,e){const t=this.uniforms;t.resolution.value.set(n,e),t.texelSize.value.set(1/n,1/e),t.aspect.value=n/e}static get Section(){return gt}};function Xp(n,e,t){for(const i of e){const r="$1"+n+i.charAt(0).toUpperCase()+i.slice(1),s=new RegExp("([^\\.])(\\b"+i+"\\b)","g");for(const a of t.entries())a[1]!==null&&t.set(a[0],a[1].replace(s,r))}}function DE(n,e,t){let i=e.getFragmentShader(),r=e.getVertexShader();const s=i!==void 0&&/mainImage/.test(i),a=i!==void 0&&/mainUv/.test(i);if(t.attributes|=e.getAttributes(),i===void 0)throw new Error(`Missing fragment shader (${e.name})`);if(a&&(t.attributes&Kr.CONVOLUTION)!==0)throw new Error(`Effects that transform UVs are incompatible with convolution effects (${e.name})`);if(!s&&!a)throw new Error(`Could not find mainImage or mainUv function (${e.name})`);{const o=/\w+\s+(\w+)\([\w\s,]*\)\s*{/g,l=t.shaderParts;let c=l.get(gt.FRAGMENT_HEAD)||"",u=l.get(gt.FRAGMENT_MAIN_UV)||"",f=l.get(gt.FRAGMENT_MAIN_IMAGE)||"",h=l.get(gt.VERTEX_HEAD)||"",d=l.get(gt.VERTEX_MAIN_SUPPORT)||"";const m=new Set,g=new Set;if(a&&(u+=`	${n}MainUv(UV);
`,t.uvTransformation=!0),r!==null&&/mainSupport/.test(r)){const v=/mainSupport *\([\w\s]*?uv\s*?\)/.test(r);d+=`	${n}MainSupport(`,d+=v?`vUv);
`:`);
`;for(const b of r.matchAll(/(?:varying\s+\w+\s+([\S\s]*?);)/g))for(const S of b[1].split(/\s*,\s*/))t.varyings.add(S),m.add(S),g.add(S);for(const b of r.matchAll(o))g.add(b[1])}for(const v of i.matchAll(o))g.add(v[1]);for(const v of e.defines.keys())g.add(v.replace(/\([\w\s,]*\)/g,""));for(const v of e.uniforms.keys())g.add(v);g.delete("while"),g.delete("for"),g.delete("if"),e.uniforms.forEach((v,b)=>t.uniforms.set(n+b.charAt(0).toUpperCase()+b.slice(1),v)),e.defines.forEach((v,b)=>t.defines.set(n+b.charAt(0).toUpperCase()+b.slice(1),v));const p=new Map([["fragment",i],["vertex",r]]);Xp(n,g,t.defines),Xp(n,g,p),i=p.get("fragment"),r=p.get("vertex");const _=e.blendMode;if(t.blendModes.set(_.blendFunction,_),s){e.inputColorSpace!==null&&e.inputColorSpace!==t.colorSpace&&(f+=e.inputColorSpace===Tt?`color0 = sRGBTransferOETF(color0);
	`:`color0 = sRGBToLinear(color0);
	`),e.outputColorSpace!==Ti?t.colorSpace=e.outputColorSpace:e.inputColorSpace!==null&&(t.colorSpace=e.inputColorSpace);const v=/MainImage *\([\w\s,]*?depth[\w\s,]*?\)/;f+=`${n}MainImage(color0, UV, `,(t.attributes&Kr.DEPTH)!==0&&v.test(i)&&(f+="depth, ",t.readDepth=!0),f+=`color1);
	`;const b=n+"BlendOpacity";t.uniforms.set(b,_.opacity),f+=`color0 = blend${_.blendFunction}(color0, color1, ${b});

	`,c+=`uniform float ${b};

`}if(c+=i+`
`,r!==null&&(h+=r+`
`),l.set(gt.FRAGMENT_HEAD,c),l.set(gt.FRAGMENT_MAIN_UV,u),l.set(gt.FRAGMENT_MAIN_IMAGE,f),l.set(gt.VERTEX_HEAD,h),l.set(gt.VERTEX_MAIN_SUPPORT,d),e.extensions!==null)for(const v of e.extensions)t.extensions.add(v)}}var UE=class extends gi{constructor(n,...e){super("EffectPass"),this.fullscreenMaterial=new PE(null,null,null,n),this.listener=t=>this.handleEvent(t),this.effects=[],this.setEffects(e),this.skipRendering=!1,this.minTime=1,this.maxTime=Number.POSITIVE_INFINITY,this.timeScale=1}set mainScene(n){for(const e of this.effects)e.mainScene=n}set mainCamera(n){this.fullscreenMaterial.copyCameraSettings(n);for(const e of this.effects)e.mainCamera=n}get encodeOutput(){return this.fullscreenMaterial.encodeOutput}set encodeOutput(n){this.fullscreenMaterial.encodeOutput=n}get dithering(){return this.fullscreenMaterial.dithering}set dithering(n){const e=this.fullscreenMaterial;e.dithering=n,e.needsUpdate=!0}setEffects(n){for(const e of this.effects)e.removeEventListener("change",this.listener);this.effects=n.sort((e,t)=>t.attributes-e.attributes);for(const e of this.effects)e.addEventListener("change",this.listener)}updateMaterial(){const n=new RT;let e=0;for(const a of this.effects)if(a.blendMode.blendFunction===ct.DST)n.attributes|=a.getAttributes()&Kr.DEPTH;else{if((n.attributes&a.getAttributes()&Kr.CONVOLUTION)!==0)throw new Error(`Convolution effects cannot be merged (${a.name})`);DE("e"+e++,a,n)}let t=n.shaderParts.get(gt.FRAGMENT_HEAD),i=n.shaderParts.get(gt.FRAGMENT_MAIN_IMAGE),r=n.shaderParts.get(gt.FRAGMENT_MAIN_UV);const s=/\bblend\b/g;for(const a of n.blendModes.values())t+=a.getShaderCode().replace(s,`blend${a.blendFunction}`)+`
`;(n.attributes&Kr.DEPTH)!==0?(n.readDepth&&(i=`float depth = readDepth(UV);

	`+i),this.needsDepthTexture=this.getDepthTexture()===null):this.needsDepthTexture=!1,n.colorSpace===Tt&&(i+=`color0 = sRGBToLinear(color0);
	`),n.uvTransformation?(r=`vec2 transformedUv = vUv;
`+r,n.defines.set("UV","transformedUv")):n.defines.set("UV","vUv"),n.shaderParts.set(gt.FRAGMENT_HEAD,t),n.shaderParts.set(gt.FRAGMENT_MAIN_IMAGE,i),n.shaderParts.set(gt.FRAGMENT_MAIN_UV,r);for(const[a,o]of n.shaderParts)o!==null&&n.shaderParts.set(a,o.trim().replace(/^#/,`
#`));this.skipRendering=e===0,this.needsSwap=!this.skipRendering,this.fullscreenMaterial.setShaderData(n)}recompile(){this.updateMaterial()}getDepthTexture(){return this.fullscreenMaterial.depthBuffer}setDepthTexture(n,e=Qa){this.fullscreenMaterial.depthBuffer=n,this.fullscreenMaterial.depthPacking=e;for(const t of this.effects)t.setDepthTexture(n,e)}render(n,e,t,i,r){for(const s of this.effects)s.update(n,e,i);if(!this.skipRendering||this.renderToScreen){const s=this.fullscreenMaterial;s.inputBuffer=e.texture,s.time+=i*this.timeScale,n.setRenderTarget(this.renderToScreen?null:t),n.render(this.scene,this.camera)}}setSize(n,e){this.fullscreenMaterial.setSize(n,e);for(const t of this.effects)t.setSize(n,e)}initialize(n,e,t){this.renderer=n;for(const i of this.effects)i.initialize(n,e,t);this.updateMaterial(),t!==void 0&&t!==Yt&&(this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1")}dispose(){super.dispose();for(const n of this.effects)n.removeEventListener("change",this.listener),n.dispose()}handleEvent(n){switch(n.type){case"change":this.recompile();break}}};const xg=(n,e)=>{if(typeof n=="number"){if(e===3)return{mode:"rgb",r:(n>>8&15|n>>4&240)/255,g:(n>>4&15|n&240)/255,b:(n&15|n<<4&240)/255};if(e===4)return{mode:"rgb",r:(n>>12&15|n>>8&240)/255,g:(n>>8&15|n>>4&240)/255,b:(n>>4&15|n&240)/255,alpha:(n&15|n<<4&240)/255};if(e===6)return{mode:"rgb",r:(n>>16&255)/255,g:(n>>8&255)/255,b:(n&255)/255};if(e===8)return{mode:"rgb",r:(n>>24&255)/255,g:(n>>16&255)/255,b:(n>>8&255)/255,alpha:(n&255)/255}}},LE={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},IE=n=>xg(LE[n.toLowerCase()],6),FE=/^#?([0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{4}|[0-9a-f]{3})$/i,NE=n=>{let e;return(e=n.match(FE))?xg(parseInt(e[1],16),e[1].length):void 0},br="([+-]?\\d*\\.?\\d+(?:[eE][+-]?\\d+)?)",Ga=`${br}%`,Rf=`(?:${br}%|${br})`,OE=`(?:${br}(deg|grad|rad|turn)|${br})`,Zs="\\s*,\\s*",BE=new RegExp(`^rgba?\\(\\s*${br}${Zs}${br}${Zs}${br}\\s*(?:,\\s*${Rf}\\s*)?\\)$`),kE=new RegExp(`^rgba?\\(\\s*${Ga}${Zs}${Ga}${Zs}${Ga}\\s*(?:,\\s*${Rf}\\s*)?\\)$`),zE=n=>{let e={mode:"rgb"},t;if(t=n.match(BE))t[1]!==void 0&&(e.r=t[1]/255),t[2]!==void 0&&(e.g=t[2]/255),t[3]!==void 0&&(e.b=t[3]/255);else if(t=n.match(kE))t[1]!==void 0&&(e.r=t[1]/100),t[2]!==void 0&&(e.g=t[2]/100),t[3]!==void 0&&(e.b=t[3]/100);else return;return t[4]!==void 0?e.alpha=Math.max(0,Math.min(1,t[4]/100)):t[5]!==void 0&&(e.alpha=Math.max(0,Math.min(1,+t[5]))),e},GE=(n,e)=>n===void 0?void 0:typeof n!="object"?ZE(n):n.mode!==void 0?n:e?{...n,mode:e}:void 0,Cf=(n="rgb")=>e=>(e=GE(e,n))!==void 0?e.mode===n?e:Ai[e.mode][n]?Ai[e.mode][n](e):n==="rgb"?Ai[e.mode].rgb(e):Ai.rgb[n](Ai[e.mode].rgb(e)):void 0,Ai={},yg={},Al=[],bg={},HE=n=>n,yt=n=>(Ai[n.mode]={...Ai[n.mode],...n.toMode},Object.keys(n.fromMode||{}).forEach(e=>{Ai[e]||(Ai[e]={}),Ai[e][n.mode]=n.fromMode[e]}),n.ranges||(n.ranges={}),n.difference||(n.difference={}),n.channels.forEach(e=>{if(n.ranges[e]===void 0&&(n.ranges[e]=[0,1]),!n.interpolate[e])throw new Error(`Missing interpolator for: ${e}`);typeof n.interpolate[e]=="function"&&(n.interpolate[e]={use:n.interpolate[e]}),n.interpolate[e].fixup||(n.interpolate[e].fixup=HE)}),yg[n.mode]=n,(n.parse||[]).forEach(e=>{VE(e,n.mode)}),Cf(n.mode)),Mg=n=>yg[n],VE=(n,e)=>{if(typeof n=="string"){if(!e)throw new Error("'mode' required when 'parser' is a string");bg[n]=e}else typeof n=="function"&&Al.indexOf(n)<0&&Al.push(n)},Hh=/[^\x00-\x7F]|[a-zA-Z_]/,WE=/[^\x00-\x7F]|[-\w]/,Ue={Function:"function",Ident:"ident",Number:"number",Percentage:"percentage",ParenClose:")",None:"none",Hue:"hue",Alpha:"alpha"};let et=0;function Xo(n){let e=n[et],t=n[et+1];return e==="-"||e==="+"?/\d/.test(t)||t==="."&&/\d/.test(n[et+2]):e==="."?/\d/.test(t):/\d/.test(e)}function Vh(n){if(et>=n.length)return!1;let e=n[et];if(Hh.test(e))return!0;if(e==="-"){if(n.length-et<2)return!1;let t=n[et+1];return!!(t==="-"||Hh.test(t))}return!1}const XE={deg:1,rad:180/Math.PI,grad:9/10,turn:360};function Aa(n){let e="";if((n[et]==="-"||n[et]==="+")&&(e+=n[et++]),e+=jo(n),n[et]==="."&&/\d/.test(n[et+1])&&(e+=n[et++]+jo(n)),(n[et]==="e"||n[et]==="E")&&((n[et+1]==="-"||n[et+1]==="+")&&/\d/.test(n[et+2])?e+=n[et++]+n[et++]+jo(n):/\d/.test(n[et+1])&&(e+=n[et++]+jo(n))),Vh(n)){let t=Rl(n);return t==="deg"||t==="rad"||t==="turn"||t==="grad"?{type:Ue.Hue,value:e*XE[t]}:void 0}return n[et]==="%"?(et++,{type:Ue.Percentage,value:+e}):{type:Ue.Number,value:+e}}function jo(n){let e="";for(;/\d/.test(n[et]);)e+=n[et++];return e}function Rl(n){let e="";for(;et<n.length&&WE.test(n[et]);)e+=n[et++];return e}function jE(n){let e=Rl(n);return n[et]==="("?(et++,{type:Ue.Function,value:e}):e==="none"?{type:Ue.None,value:void 0}:{type:Ue.Ident,value:e}}function YE(n=""){let e=n.trim(),t=[],i;for(et=0;et<e.length;){if(i=e[et++],i===`
`||i==="	"||i===" "){for(;et<e.length&&(e[et]===`
`||e[et]==="	"||e[et]===" ");)et++;continue}if(i===",")return;if(i===")"){t.push({type:Ue.ParenClose});continue}if(i==="+"){if(et--,Xo(e)){t.push(Aa(e));continue}return}if(i==="-"){if(et--,Xo(e)){t.push(Aa(e));continue}if(Vh(e)){t.push({type:Ue.Ident,value:Rl(e)});continue}return}if(i==="."){if(et--,Xo(e)){t.push(Aa(e));continue}return}if(i==="/"){for(;et<e.length&&(e[et]===`
`||e[et]==="	"||e[et]===" ");)et++;let r;if(Xo(e)&&(r=Aa(e),r.type!==Ue.Hue)){t.push({type:Ue.Alpha,value:r});continue}if(Vh(e)&&Rl(e)==="none"){t.push({type:Ue.Alpha,value:{type:Ue.None,value:void 0}});continue}return}if(/\d/.test(i)){et--,t.push(Aa(e));continue}if(Hh.test(i)){et--,t.push(jE(e));continue}return}return t}function qE(n){n._i=0;let e=n[n._i++];if(!e||e.type!==Ue.Function||e.value!=="color"||(e=n[n._i++],e.type!==Ue.Ident))return;const t=bg[e.value];if(!t)return;const i={mode:t},r=Sg(n,!1);if(!r)return;const s=Mg(t).channels;for(let a=0,o,l;a<s.length;a++)o=r[a],l=s[a],o.type!==Ue.None&&(i[l]=o.type===Ue.Number?o.value:o.value/100,l==="alpha"&&(i[l]=Math.max(0,Math.min(1,i[l]))));return i}function Sg(n,e){const t=[];let i;for(;n._i<n.length;){if(i=n[n._i++],i.type===Ue.None||i.type===Ue.Number||i.type===Ue.Alpha||i.type===Ue.Percentage||e&&i.type===Ue.Hue){t.push(i);continue}if(i.type===Ue.ParenClose){if(n._i<n.length)return;continue}return}if(!(t.length<3||t.length>4)){if(t.length===4){if(t[3].type!==Ue.Alpha)return;t[3]=t[3].value}return t.length===3&&t.push({type:Ue.None,value:void 0}),t.every(r=>r.type!==Ue.Alpha)?t:void 0}}function KE(n,e){n._i=0;let t=n[n._i++];if(!t||t.type!==Ue.Function)return;let i=Sg(n,e);if(i)return i.unshift(t.value),i}const ZE=n=>{if(typeof n!="string")return;const e=YE(n),t=e?KE(e,!0):void 0;let i,r=0,s=Al.length;for(;r<s;)if((i=Al[r++](n,t))!==void 0)return i;return e?qE(e):void 0};function $E(n,e){if(!e||e[0]!=="rgb"&&e[0]!=="rgba")return;const t={mode:"rgb"},[,i,r,s,a]=e;if(!(i.type===Ue.Hue||r.type===Ue.Hue||s.type===Ue.Hue))return i.type!==Ue.None&&(t.r=i.type===Ue.Number?i.value/255:i.value/100),r.type!==Ue.None&&(t.g=r.type===Ue.Number?r.value/255:r.value/100),s.type!==Ue.None&&(t.b=s.type===Ue.Number?s.value/255:s.value/100),a.type!==Ue.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ue.Number?a.value:a.value/100))),t}const JE=n=>n==="transparent"?{mode:"rgb",r:0,g:0,b:0,alpha:0}:void 0,QE=(n,e,t)=>n+t*(e-n),e3=n=>{let e=[];for(let t=0;t<n.length-1;t++){let i=n[t],r=n[t+1];i===void 0&&r===void 0?e.push(void 0):i!==void 0&&r!==void 0?e.push([i,r]):e.push(i!==void 0?[i,i]:[r,r])}return e},t3=n=>e=>{let t=e3(e);return i=>{let r=i*t.length,s=i>=1?t.length-1:Math.max(Math.floor(r),0),a=t[s];return a===void 0?void 0:n(a[0],a[1],r-s)}},ze=t3(QE),nn=n=>{let e=!1,t=n.map(i=>i!==void 0?(e=!0,i):1);return e?t:n},ta={mode:"rgb",channels:["r","g","b","alpha"],parse:[$E,NE,zE,IE,JE,"srgb"],serialize:"srgb",interpolate:{r:ze,g:ze,b:ze,alpha:{use:ze,fixup:nn}},gamut:!0,white:{r:1,g:1,b:1},black:{r:0,g:0,b:0}},iu=(n=0)=>Math.pow(Math.abs(n),563/256)*Math.sign(n),jp=n=>{let e=iu(n.r),t=iu(n.g),i=iu(n.b),r={mode:"xyz65",x:.5766690429101305*e+.1855582379065463*t+.1882286462349947*i,y:.297344975250536*e+.6273635662554661*t+.0752914584939979*i,z:.0270313613864123*e+.0706888525358272*t+.9913375368376386*i};return n.alpha!==void 0&&(r.alpha=n.alpha),r},ru=n=>Math.pow(Math.abs(n),256/563)*Math.sign(n),Yp=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"a98",r:ru(n*2.0415879038107465-e*.5650069742788597-.3447313507783297*t),g:ru(n*-.9692436362808798+e*1.8759675015077206+.0415550574071756*t),b:ru(n*.0134442806320312-e*.1183623922310184+1.0151749943912058*t)};return i!==void 0&&(r.alpha=i),r},su=(n=0)=>{const e=Math.abs(n);return e<=.04045?n/12.92:(Math.sign(n)||1)*Math.pow((e+.055)/1.055,2.4)},na=({r:n,g:e,b:t,alpha:i})=>{let r={mode:"lrgb",r:su(n),g:su(e),b:su(t)};return i!==void 0&&(r.alpha=i),r},ns=n=>{let{r:e,g:t,b:i,alpha:r}=na(n),s={mode:"xyz65",x:.4123907992659593*e+.357584339383878*t+.1804807884018343*i,y:.2126390058715102*e+.715168678767756*t+.0721923153607337*i,z:.0193308187155918*e+.119194779794626*t+.9505321522496607*i};return r!==void 0&&(s.alpha=r),s},au=(n=0)=>{const e=Math.abs(n);return e>.0031308?(Math.sign(n)||1)*(1.055*Math.pow(e,1/2.4)-.055):n*12.92},ia=({r:n,g:e,b:t,alpha:i},r="rgb")=>{let s={mode:r,r:au(n),g:au(e),b:au(t)};return i!==void 0&&(s.alpha=i),s},is=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=ia({r:n*3.2409699419045226-e*1.537383177570094-.4986107602930034*t,g:n*-.9692436362808796+e*1.8759675015077204+.0415550574071756*t,b:n*.0556300796969936-e*.2039769588889765+1.0569715142428784*t});return i!==void 0&&(r.alpha=i),r},n3={...ta,mode:"a98",parse:["a98-rgb"],serialize:"a98-rgb",fromMode:{rgb:n=>Yp(ns(n)),xyz65:Yp},toMode:{rgb:n=>is(jp(n)),xyz65:jp}},dn=n=>(n=n%360)<0?n+360:n,i3=(n,e)=>n.map((t,i,r)=>{if(t===void 0)return t;let s=dn(t);return i===0||n[i-1]===void 0?s:e(s-dn(r[i-1]))}).reduce((t,i)=>!t.length||i===void 0||t[t.length-1]===void 0?(t.push(i),t):(t.push(i+t[t.length-1]),t),[]),Ji=n=>i3(n,e=>Math.abs(e)<=180?e:e-360*Math.sign(e)),an=[-.14861,1.78277,-.29227,-.90649,1.97294,0],r3=Math.PI/180,s3=180/Math.PI;let qp=an[3]*an[4],Kp=an[1]*an[4],Zp=an[1]*an[2]-an[0]*an[3];const a3=({r:n,g:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(Zp*t+n*qp-e*Kp)/(Zp+qp-Kp),s=t-r,a=(an[4]*(e-r)-an[2]*s)/an[3],o={mode:"cubehelix",l:r,s:r===0||r===1?void 0:Math.sqrt(s*s+a*a)/(an[4]*r*(1-r))};return o.s&&(o.h=Math.atan2(a,s)*s3-120),i!==void 0&&(o.alpha=i),o},o3=({h:n,s:e,l:t,alpha:i})=>{let r={mode:"rgb"};n=(n===void 0?0:n+120)*r3,t===void 0&&(t=0);let s=e===void 0?0:e*t*(1-t),a=Math.cos(n),o=Math.sin(n);return r.r=t+s*(an[0]*a+an[1]*o),r.g=t+s*(an[2]*a+an[3]*o),r.b=t+s*(an[4]*a+an[5]*o),i!==void 0&&(r.alpha=i),r},Hl=(n,e)=>{if(n.h===void 0||e.h===void 0||!n.s||!e.s)return 0;let t=dn(n.h),i=dn(e.h),r=Math.sin((i-t+360)/2*Math.PI/180);return 2*Math.sqrt(n.s*e.s)*r},l3=(n,e)=>{if(n.h===void 0||e.h===void 0)return 0;let t=dn(n.h),i=dn(e.h);return Math.abs(i-t)>180?t-(i-360*Math.sign(i-t)):i-t},Vl=(n,e)=>{if(n.h===void 0||e.h===void 0||!n.c||!e.c)return 0;let t=dn(n.h),i=dn(e.h),r=Math.sin((i-t+360)/2*Math.PI/180);return 2*Math.sqrt(n.c*e.c)*r},Qi=n=>{let e=n.reduce((i,r)=>{if(r!==void 0){let s=r*Math.PI/180;i.sin+=Math.sin(s),i.cos+=Math.cos(s)}return i},{sin:0,cos:0}),t=Math.atan2(e.sin,e.cos)*180/Math.PI;return t<0?360+t:t},c3={mode:"cubehelix",channels:["h","s","l","alpha"],parse:["--cubehelix"],serialize:"--cubehelix",ranges:{h:[0,360],s:[0,4.614],l:[0,1]},fromMode:{rgb:a3},toMode:{rgb:o3},interpolate:{h:{use:ze,fixup:Ji},s:ze,l:ze,alpha:{use:ze,fixup:nn}},difference:{h:Hl},average:{h:Qi}},wr=({l:n,a:e,b:t,alpha:i},r="lch")=>{e===void 0&&(e=0),t===void 0&&(t=0);let s=Math.sqrt(e*e+t*t),a={mode:r,l:n,c:s};return s&&(a.h=dn(Math.atan2(t,e)*180/Math.PI)),i!==void 0&&(a.alpha=i),a},Ar=({l:n,c:e,h:t,alpha:i},r="lab")=>{t===void 0&&(t=0);let s={mode:r,l:n,a:e?e*Math.cos(t/180*Math.PI):0,b:e?e*Math.sin(t/180*Math.PI):0};return i!==void 0&&(s.alpha=i),s},Tg=Math.pow(29,3)/Math.pow(3,3),Eg=Math.pow(6,3)/Math.pow(29,3),qt={X:.3457/.3585,Y:1,Z:(1-.3457-.3585)/.3585},ks={X:.3127/.329,Y:1,Z:(1-.3127-.329)/.329};let ou=n=>Math.pow(n,3)>Eg?Math.pow(n,3):(116*n-16)/Tg;const wg=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(n+16)/116,s=e/500+r,a=r-t/200,o={mode:"xyz65",x:ou(s)*ks.X,y:ou(r)*ks.Y,z:ou(a)*ks.Z};return i!==void 0&&(o.alpha=i),o},Wl=n=>is(wg(n)),lu=n=>n>Eg?Math.cbrt(n):(Tg*n+16)/116,Ag=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=lu(n/ks.X),s=lu(e/ks.Y),a=lu(t/ks.Z),o={mode:"lab65",l:116*s-16,a:500*(r-s),b:200*(s-a)};return i!==void 0&&(o.alpha=i),o},Xl=n=>{let e=Ag(ns(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},Cl=1,Rg=1,$a=26/180*Math.PI,Pl=Math.cos($a),Dl=Math.sin($a),Cg=100/Math.log(139/100),Wh=({l:n,c:e,h:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"lab65",l:(Math.exp(n*Cl/Cg)-1)/.0039},s=(Math.exp(.0435*e*Rg*Cl)-1)/.075,a=s*Math.cos(t/180*Math.PI-$a),o=s*Math.sin(t/180*Math.PI-$a);return r.a=a*Pl-o/.83*Dl,r.b=a*Dl+o/.83*Pl,i!==void 0&&(r.alpha=i),r},Xh=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=e*Pl+t*Dl,s=.83*(t*Pl-e*Dl),a=Math.sqrt(r*r+s*s),o={mode:"dlch",l:Cg/Cl*Math.log(1+.0039*n),c:Math.log(1+.075*a)/(.0435*Rg*Cl)};return o.c&&(o.h=dn((Math.atan2(s,r)+$a)/Math.PI*180)),i!==void 0&&(o.alpha=i),o},$p=n=>Wh(wr(n,"dlch")),Jp=n=>Ar(Xh(n),"dlab"),u3={mode:"dlab",parse:["--din99o-lab"],serialize:"--din99o-lab",toMode:{lab65:$p,rgb:n=>Wl($p(n))},fromMode:{lab65:Jp,rgb:n=>Jp(Xl(n))},channels:["l","a","b","alpha"],ranges:{l:[0,100],a:[-40.09,45.501],b:[-40.469,44.344]},interpolate:{l:ze,a:ze,b:ze,alpha:{use:ze,fixup:nn}}},h3={mode:"dlch",parse:["--din99o-lch"],serialize:"--din99o-lch",toMode:{lab65:Wh,dlab:n=>Ar(n,"dlab"),rgb:n=>Wl(Wh(n))},fromMode:{lab65:Xh,dlab:n=>wr(n,"dlch"),rgb:n=>Xh(Xl(n))},channels:["l","c","h","alpha"],ranges:{l:[0,100],c:[0,51.484],h:[0,360]},interpolate:{l:ze,c:ze,h:{use:ze,fixup:Ji},alpha:{use:ze,fixup:nn}},difference:{h:Vl},average:{h:Qi}};function f3({h:n,s:e,i:t,alpha:i}){n=dn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.abs(n/60%2-1),s;switch(Math.floor(n/60)){case 0:s={r:t*(1+e*(3/(2-r)-1)),g:t*(1+e*(3*(1-r)/(2-r)-1)),b:t*(1-e)};break;case 1:s={r:t*(1+e*(3*(1-r)/(2-r)-1)),g:t*(1+e*(3/(2-r)-1)),b:t*(1-e)};break;case 2:s={r:t*(1-e),g:t*(1+e*(3/(2-r)-1)),b:t*(1+e*(3*(1-r)/(2-r)-1))};break;case 3:s={r:t*(1-e),g:t*(1+e*(3*(1-r)/(2-r)-1)),b:t*(1+e*(3/(2-r)-1))};break;case 4:s={r:t*(1+e*(3*(1-r)/(2-r)-1)),g:t*(1-e),b:t*(1+e*(3/(2-r)-1))};break;case 5:s={r:t*(1+e*(3/(2-r)-1)),g:t*(1-e),b:t*(1+e*(3*(1-r)/(2-r)-1))};break;default:s={r:t*(1-e),g:t*(1-e),b:t*(1-e)}}return s.mode="rgb",i!==void 0&&(s.alpha=i),s}function d3({r:n,g:e,b:t,alpha:i}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsi",s:n+e+t===0?0:1-3*s/(n+e+t),i:(n+e+t)/3};return r-s!==0&&(a.h=(r===n?(e-t)/(r-s)+(e<t)*6:r===e?(t-n)/(r-s)+2:(n-e)/(r-s)+4)*60),i!==void 0&&(a.alpha=i),a}const p3={mode:"hsi",toMode:{rgb:f3},parse:["--hsi"],serialize:"--hsi",fromMode:{rgb:d3},channels:["h","s","i","alpha"],ranges:{h:[0,360]},gamut:"rgb",interpolate:{h:{use:ze,fixup:Ji},s:ze,i:ze,alpha:{use:ze,fixup:nn}},difference:{h:Hl},average:{h:Qi}};function m3({h:n,s:e,l:t,alpha:i}){n=dn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let r=t+e*(t<.5?t:1-t),s=r-(r-t)*2*Math.abs(n/60%2-1),a;switch(Math.floor(n/60)){case 0:a={r,g:s,b:2*t-r};break;case 1:a={r:s,g:r,b:2*t-r};break;case 2:a={r:2*t-r,g:r,b:s};break;case 3:a={r:2*t-r,g:s,b:r};break;case 4:a={r:s,g:2*t-r,b:r};break;case 5:a={r,g:2*t-r,b:s};break;default:a={r:2*t-r,g:2*t-r,b:2*t-r}}return a.mode="rgb",i!==void 0&&(a.alpha=i),a}function g3({r:n,g:e,b:t,alpha:i}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsl",s:r===s?0:(r-s)/(1-Math.abs(r+s-1)),l:.5*(r+s)};return r-s!==0&&(a.h=(r===n?(e-t)/(r-s)+(e<t)*6:r===e?(t-n)/(r-s)+2:(n-e)/(r-s)+4)*60),i!==void 0&&(a.alpha=i),a}const _3=(n,e)=>{switch(e){case"deg":return+n;case"rad":return n/Math.PI*180;case"grad":return n/10*9;case"turn":return n*360}},v3=new RegExp(`^hsla?\\(\\s*${OE}${Zs}${Ga}${Zs}${Ga}\\s*(?:,\\s*${Rf}\\s*)?\\)$`),x3=n=>{let e=n.match(v3);if(!e)return;let t={mode:"hsl"};return e[3]!==void 0?t.h=+e[3]:e[1]!==void 0&&e[2]!==void 0&&(t.h=_3(e[1],e[2])),e[4]!==void 0&&(t.s=Math.min(Math.max(0,e[4]/100),1)),e[5]!==void 0&&(t.l=Math.min(Math.max(0,e[5]/100),1)),e[6]!==void 0?t.alpha=Math.max(0,Math.min(1,e[6]/100)):e[7]!==void 0&&(t.alpha=Math.max(0,Math.min(1,+e[7]))),t};function y3(n,e){if(!e||e[0]!=="hsl"&&e[0]!=="hsla")return;const t={mode:"hsl"},[,i,r,s,a]=e;if(i.type!==Ue.None){if(i.type===Ue.Percentage)return;t.h=i.value}if(r.type!==Ue.None){if(r.type===Ue.Hue)return;t.s=r.value/100}if(s.type!==Ue.None){if(s.type===Ue.Hue)return;t.l=s.value/100}return a.type!==Ue.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ue.Number?a.value:a.value/100))),t}const Pg={mode:"hsl",toMode:{rgb:m3},fromMode:{rgb:g3},channels:["h","s","l","alpha"],ranges:{h:[0,360]},gamut:"rgb",parse:[y3,x3],serialize:n=>`hsl(${n.h!==void 0?n.h:"none"} ${n.s!==void 0?n.s*100+"%":"none"} ${n.l!==void 0?n.l*100+"%":"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:ze,fixup:Ji},s:ze,l:ze,alpha:{use:ze,fixup:nn}},difference:{h:Hl},average:{h:Qi}};function Dg({h:n,s:e,v:t,alpha:i}){n=dn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.abs(n/60%2-1),s;switch(Math.floor(n/60)){case 0:s={r:t,g:t*(1-e*r),b:t*(1-e)};break;case 1:s={r:t*(1-e*r),g:t,b:t*(1-e)};break;case 2:s={r:t*(1-e),g:t,b:t*(1-e*r)};break;case 3:s={r:t*(1-e),g:t*(1-e*r),b:t};break;case 4:s={r:t*(1-e*r),g:t*(1-e),b:t};break;case 5:s={r:t,g:t*(1-e),b:t*(1-e*r)};break;default:s={r:t*(1-e),g:t*(1-e),b:t*(1-e)}}return s.mode="rgb",i!==void 0&&(s.alpha=i),s}function Ug({r:n,g:e,b:t,alpha:i}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsv",s:r===0?0:1-s/r,v:r};return r-s!==0&&(a.h=(r===n?(e-t)/(r-s)+(e<t)*6:r===e?(t-n)/(r-s)+2:(n-e)/(r-s)+4)*60),i!==void 0&&(a.alpha=i),a}const Lg={mode:"hsv",toMode:{rgb:Dg},parse:["--hsv"],serialize:"--hsv",fromMode:{rgb:Ug},channels:["h","s","v","alpha"],ranges:{h:[0,360]},gamut:"rgb",interpolate:{h:{use:ze,fixup:Ji},s:ze,v:ze,alpha:{use:ze,fixup:nn}},difference:{h:Hl},average:{h:Qi}};function b3({h:n,w:e,b:t,alpha:i}){if(e===void 0&&(e=0),t===void 0&&(t=0),e+t>1){let r=e+t;e/=r,t/=r}return Dg({h:n,s:t===1?1:1-e/(1-t),v:1-t,alpha:i})}function M3(n){let e=Ug(n);if(e===void 0)return;let t=e.s!==void 0?e.s:0,i=e.v!==void 0?e.v:0,r={mode:"hwb",w:(1-t)*i,b:1-i};return e.h!==void 0&&(r.h=e.h),e.alpha!==void 0&&(r.alpha=e.alpha),r}function S3(n,e){if(!e||e[0]!=="hwb")return;const t={mode:"hwb"},[,i,r,s,a]=e;if(i.type!==Ue.None){if(i.type===Ue.Percentage)return;t.h=i.value}if(r.type!==Ue.None){if(r.type===Ue.Hue)return;t.w=r.value/100}if(s.type!==Ue.None){if(s.type===Ue.Hue)return;t.b=s.value/100}return a.type!==Ue.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ue.Number?a.value:a.value/100))),t}const T3={mode:"hwb",toMode:{rgb:b3},fromMode:{rgb:M3},channels:["h","w","b","alpha"],ranges:{h:[0,360]},gamut:"rgb",parse:[S3],serialize:n=>`hwb(${n.h!==void 0?n.h:"none"} ${n.w!==void 0?n.w*100+"%":"none"} ${n.b!==void 0?n.b*100+"%":"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:ze,fixup:Ji},w:ze,b:ze,alpha:{use:ze,fixup:nn}},difference:{h:l3},average:{h:Qi}},Ig=203,jl=.1593017578125,Fg=78.84375,Yl=.8359375,ql=18.8515625,Kl=18.6875;function cu(n){if(n<0)return 0;const e=Math.pow(n,1/Fg);return 1e4*Math.pow(Math.max(0,e-Yl)/(ql-Kl*e),1/jl)}function uu(n){if(n<0)return 0;const e=Math.pow(n/1e4,jl);return Math.pow((Yl+ql*e)/(1+Kl*e),Fg)}const hu=n=>Math.max(n/Ig,0),Qp=({i:n,t:e,p:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r=cu(n+.008609037037932761*e+.11102962500302593*t),s=cu(n-.00860903703793275*e-.11102962500302599*t),a=cu(n+.5600313357106791*e-.32062717498731885*t),o={mode:"xyz65",x:hu(2.070152218389422*r-1.3263473389671556*s+.2066510476294051*a),y:hu(.3647385209748074*r+.680566024947227*s-.0453045459220346*a),z:hu(-.049747207535812*r-.0492609666966138*s+1.1880659249923042*a)};return i!==void 0&&(o.alpha=i),o},fu=(n=0)=>Math.max(n*Ig,0),em=({x:n,y:e,z:t,alpha:i})=>{const r=fu(n),s=fu(e),a=fu(t),o=uu(.3592832590121217*r+.6976051147779502*s-.0358915932320289*a),l=uu(-.1920808463704995*r+1.1004767970374323*s+.0753748658519118*a),c=uu(.0070797844607477*r+.0748396662186366*s+.8433265453898765*a),u=.5*o+.5*l,f=1.61376953125*o-3.323486328125*l+1.709716796875*c,h=4.378173828125*o-4.24560546875*l-.132568359375*c,d={mode:"itp",i:u,t:f,p:h};return i!==void 0&&(d.alpha=i),d},E3={mode:"itp",channels:["i","t","p","alpha"],parse:["--ictcp"],serialize:"--ictcp",toMode:{xyz65:Qp,rgb:n=>is(Qp(n))},fromMode:{xyz65:em,rgb:n=>em(ns(n))},ranges:{i:[0,.581],t:[-.369,.272],p:[-.164,.331]},interpolate:{i:ze,t:ze,p:ze,alpha:{use:ze,fixup:nn}}},w3=134.03437499999998,A3=16295499532821565e-27,du=n=>{if(n<0)return 0;let e=Math.pow(n/1e4,jl);return Math.pow((Yl+ql*e)/(1+Kl*e),w3)},pu=(n=0)=>Math.max(n*203,0),Ng=({x:n,y:e,z:t,alpha:i})=>{n=pu(n),e=pu(e),t=pu(t);let r=1.15*n-.15*t,s=.66*e+.34*n,a=du(.41478972*r+.579999*s+.014648*t),o=du(-.20151*r+1.120649*s+.0531008*t),l=du(-.0166008*r+.2648*s+.6684799*t),c=(a+o)/2,u={mode:"jab",j:.44*c/(1-.56*c)-A3,a:3.524*a-4.066708*o+.542708*l,b:.199076*a+1.096799*o-1.295875*l};return i!==void 0&&(u.alpha=i),u},R3=134.03437499999998,tm=16295499532821565e-27,mu=n=>{if(n<0)return 0;let e=Math.pow(n,1/R3);return 1e4*Math.pow((Yl-e)/(Kl*e-ql),1/jl)},gu=n=>n/203,Og=({j:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(n+tm)/(.44+.56*(n+tm)),s=mu(r+.13860504*e+.058047316*t),a=mu(r-.13860504*e-.058047316*t),o=mu(r-.096019242*e-.8118919*t),l={mode:"xyz65",x:gu(1.661373024652174*s-.914523081304348*a+.23136208173913045*o),y:gu(-.3250758611844533*s+1.571847026732543*a-.21825383453227928*o),z:gu(-.090982811*s-.31272829*a+1.5227666*o)};return i!==void 0&&(l.alpha=i),l},Bg=n=>{let e=Ng(ns(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},kg=n=>is(Og(n)),C3={mode:"jab",channels:["j","a","b","alpha"],parse:["--jzazbz"],serialize:"--jzazbz",fromMode:{rgb:Bg,xyz65:Ng},toMode:{rgb:kg,xyz65:Og},ranges:{j:[0,.222],a:[-.109,.129],b:[-.185,.134]},interpolate:{j:ze,a:ze,b:ze,alpha:{use:ze,fixup:nn}}},nm=({j:n,a:e,b:t,alpha:i})=>{e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.sqrt(e*e+t*t),s={mode:"jch",j:n,c:r};return r&&(s.h=dn(Math.atan2(t,e)*180/Math.PI)),i!==void 0&&(s.alpha=i),s},im=({j:n,c:e,h:t,alpha:i})=>{t===void 0&&(t=0);let r={mode:"jab",j:n,a:e?e*Math.cos(t/180*Math.PI):0,b:e?e*Math.sin(t/180*Math.PI):0};return i!==void 0&&(r.alpha=i),r},P3={mode:"jch",parse:["--jzczhz"],serialize:"--jzczhz",toMode:{jab:im,rgb:n=>kg(im(n))},fromMode:{rgb:n=>nm(Bg(n)),jab:nm},channels:["j","c","h","alpha"],ranges:{j:[0,.221],c:[0,.19],h:[0,360]},interpolate:{h:{use:ze,fixup:Ji},c:ze,j:ze,alpha:{use:ze,fixup:nn}},difference:{h:Vl},average:{h:Qi}},Zl=Math.pow(29,3)/Math.pow(3,3),Pf=Math.pow(6,3)/Math.pow(29,3);let _u=n=>Math.pow(n,3)>Pf?Math.pow(n,3):(116*n-16)/Zl;const Df=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=(n+16)/116,s=e/500+r,a=r-t/200,o={mode:"xyz50",x:_u(s)*qt.X,y:_u(r)*qt.Y,z:_u(a)*qt.Z};return i!==void 0&&(o.alpha=i),o},no=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=ia({r:n*3.1341359569958707-e*1.6173863321612538-.4906619460083532*t,g:n*-.978795502912089+e*1.916254567259524+.03344273116131949*t,b:n*.07195537988411677-e*.2289768264158322+1.405386058324125*t});return i!==void 0&&(r.alpha=i),r},zg=n=>no(Df(n)),io=n=>{let{r:e,g:t,b:i,alpha:r}=na(n),s={mode:"xyz50",x:.436065742824811*e+.3851514688337912*t+.14307845442264197*i,y:.22249319175623702*e+.7168870538238823*t+.06061979053616537*i,z:.013923904500943465*e+.09708128566574634*t+.7140993584005155*i};return r!==void 0&&(s.alpha=r),s},vu=n=>n>Pf?Math.cbrt(n):(Zl*n+16)/116,Uf=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=vu(n/qt.X),s=vu(e/qt.Y),a=vu(t/qt.Z),o={mode:"lab",l:116*s-16,a:500*(r-s),b:200*(s-a)};return i!==void 0&&(o.alpha=i),o},Gg=n=>{let e=Uf(io(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e};function D3(n,e){if(!e||e[0]!=="lab")return;const t={mode:"lab"},[,i,r,s,a]=e;if(!(i.type===Ue.Hue||r.type===Ue.Hue||s.type===Ue.Hue))return i.type!==Ue.None&&(t.l=Math.min(Math.max(0,i.value),100)),r.type!==Ue.None&&(t.a=r.type===Ue.Number?r.value:r.value*125/100),s.type!==Ue.None&&(t.b=s.type===Ue.Number?s.value:s.value*125/100),a.type!==Ue.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ue.Number?a.value:a.value/100))),t}const Lf={mode:"lab",toMode:{xyz50:Df,rgb:zg},fromMode:{xyz50:Uf,rgb:Gg},channels:["l","a","b","alpha"],ranges:{l:[0,100],a:[-125,125],b:[-125,125]},parse:[D3],serialize:n=>`lab(${n.l!==void 0?n.l:"none"} ${n.a!==void 0?n.a:"none"} ${n.b!==void 0?n.b:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{l:ze,a:ze,b:ze,alpha:{use:ze,fixup:nn}}},U3={...Lf,mode:"lab65",parse:["--lab-d65"],serialize:"--lab-d65",toMode:{xyz65:wg,rgb:Wl},fromMode:{xyz65:Ag,rgb:Xl},ranges:{l:[0,100],a:[-125,125],b:[-125,125]}};function L3(n,e){if(!e||e[0]!=="lch")return;const t={mode:"lch"},[,i,r,s,a]=e;if(i.type!==Ue.None){if(i.type===Ue.Hue)return;t.l=Math.min(Math.max(0,i.value),100)}if(r.type!==Ue.None&&(t.c=Math.max(0,r.type===Ue.Number?r.value:r.value*150/100)),s.type!==Ue.None){if(s.type===Ue.Percentage)return;t.h=s.value}return a.type!==Ue.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ue.Number?a.value:a.value/100))),t}const If={mode:"lch",toMode:{lab:Ar,rgb:n=>zg(Ar(n))},fromMode:{rgb:n=>wr(Gg(n)),lab:wr},channels:["l","c","h","alpha"],ranges:{l:[0,100],c:[0,150],h:[0,360]},parse:[L3],serialize:n=>`lch(${n.l!==void 0?n.l:"none"} ${n.c!==void 0?n.c:"none"} ${n.h!==void 0?n.h:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:ze,fixup:Ji},c:ze,l:ze,alpha:{use:ze,fixup:nn}},difference:{h:Vl},average:{h:Qi}},I3={...If,mode:"lch65",parse:["--lch-d65"],serialize:"--lch-d65",toMode:{lab65:n=>Ar(n,"lab65"),rgb:n=>Wl(Ar(n,"lab65"))},fromMode:{rgb:n=>wr(Xl(n),"lch65"),lab65:n=>wr(n,"lch65")},ranges:{l:[0,100],c:[0,150],h:[0,360]}},Hg=({l:n,u:e,v:t,alpha:i})=>{e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.sqrt(e*e+t*t),s={mode:"lchuv",l:n,c:r};return r&&(s.h=dn(Math.atan2(t,e)*180/Math.PI)),i!==void 0&&(s.alpha=i),s},Vg=({l:n,c:e,h:t,alpha:i})=>{t===void 0&&(t=0);let r={mode:"luv",l:n,u:e?e*Math.cos(t/180*Math.PI):0,v:e?e*Math.sin(t/180*Math.PI):0};return i!==void 0&&(r.alpha=i),r},Wg=(n,e,t)=>4*n/(n+15*e+3*t),Xg=(n,e,t)=>9*e/(n+15*e+3*t),F3=Wg(qt.X,qt.Y,qt.Z),N3=Xg(qt.X,qt.Y,qt.Z),O3=n=>n<=Pf?Zl*n:116*Math.cbrt(n)-16,jh=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=O3(e/qt.Y),s=Wg(n,e,t),a=Xg(n,e,t);!isFinite(s)||!isFinite(a)?r=s=a=0:(s=13*r*(s-F3),a=13*r*(a-N3));let o={mode:"luv",l:r,u:s,v:a};return i!==void 0&&(o.alpha=i),o},B3=(n,e,t)=>4*n/(n+15*e+3*t),k3=(n,e,t)=>9*e/(n+15*e+3*t),z3=B3(qt.X,qt.Y,qt.Z),G3=k3(qt.X,qt.Y,qt.Z),Yh=({l:n,u:e,v:t,alpha:i})=>{if(n===void 0&&(n=0),n===0)return{mode:"xyz50",x:0,y:0,z:0};e===void 0&&(e=0),t===void 0&&(t=0);let r=e/(13*n)+z3,s=t/(13*n)+G3,a=qt.Y*(n<=8?n/Zl:Math.pow((n+16)/116,3)),o=a*(9*r)/(4*s),l=a*(12-3*r-20*s)/(4*s),c={mode:"xyz50",x:o,y:a,z:l};return i!==void 0&&(c.alpha=i),c},H3=n=>Hg(jh(io(n))),V3=n=>no(Yh(Vg(n))),W3={mode:"lchuv",toMode:{luv:Vg,rgb:V3},fromMode:{rgb:H3,luv:Hg},channels:["l","c","h","alpha"],parse:["--lchuv"],serialize:"--lchuv",ranges:{l:[0,100],c:[0,176.956],h:[0,360]},interpolate:{h:{use:ze,fixup:Ji},c:ze,l:ze,alpha:{use:ze,fixup:nn}},difference:{h:Vl},average:{h:Qi}},X3={...ta,mode:"lrgb",toMode:{rgb:ia},fromMode:{rgb:na},parse:["srgb-linear"],serialize:"srgb-linear"},j3={mode:"luv",toMode:{xyz50:Yh,rgb:n=>no(Yh(n))},fromMode:{xyz50:jh,rgb:n=>jh(io(n))},channels:["l","u","v","alpha"],parse:["--luv"],serialize:"--luv",ranges:{l:[0,100],u:[-84.936,175.042],v:[-125.882,87.243]},interpolate:{l:ze,u:ze,v:ze,alpha:{use:ze,fixup:nn}}},jg=({r:n,g:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.cbrt(.412221469470763*n+.5363325372617348*e+.0514459932675022*t),s=Math.cbrt(.2119034958178252*n+.6806995506452344*e+.1073969535369406*t),a=Math.cbrt(.0883024591900564*n+.2817188391361215*e+.6299787016738222*t),o={mode:"oklab",l:.210454268309314*r+.7936177747023054*s-.0040720430116193*a,a:1.9779985324311684*r-2.42859224204858*s+.450593709617411*a,b:.0259040424655478*r+.7827717124575296*s-.8086757549230774*a};return i!==void 0&&(o.alpha=i),o},$l=n=>{let e=jg(na(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},ro=({l:n,a:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=Math.pow(n+.3963377773761749*e+.2158037573099136*t,3),s=Math.pow(n-.1055613458156586*e-.0638541728258133*t,3),a=Math.pow(n-.0894841775298119*e-1.2914855480194092*t,3),o={mode:"lrgb",r:4.076741636075957*r-3.3077115392580616*s+.2309699031821044*a,g:-1.2684379732850317*r+2.6097573492876887*s-.3413193760026573*a,b:-.0041960761386756*r-.7034186179359362*s+1.7076146940746117*a};return i!==void 0&&(o.alpha=i),o},Jl=n=>ia(ro(n));function qh(n){const i=1.170873786407767;return .5*(i*n-.206+Math.sqrt((i*n-.206)*(i*n-.206)+4*.03*i*n))}function Ul(n){return(n*n+.206*n)/(1.170873786407767*(n+.03))}function Y3(n,e){let t,i,r,s,a,o,l,c;-1.88170328*n-.80936493*e>1?(t=1.19086277,i=1.76576728,r=.59662641,s=.75515197,a=.56771245,o=4.0767416621,l=-3.3077115913,c=.2309699292):1.81444104*n-1.19445276*e>1?(t=.73956515,i=-.45954404,r=.08285427,s=.1254107,a=.14503204,o=-1.2684380046,l=2.6097574011,c=-.3413193965):(t=1.35733652,i=-.00915799,r=-1.1513021,s=-.50559606,a=.00692167,o=-.0041960863,l=-.7034186147,c=1.707614701);let u=t+i*n+r*e+s*n*n+a*n*e,f=.3963377774*n+.2158037573*e,h=-.1055613458*n-.0638541728*e,d=-.0894841775*n-1.291485548*e;{let m=1+u*f,g=1+u*h,p=1+u*d,_=m*m*m,v=g*g*g,b=p*p*p,S=3*f*m*m,E=3*h*g*g,M=3*d*p*p,T=6*f*f*m,x=6*h*h*g,y=6*d*d*p,w=o*_+l*v+c*b,C=o*S+l*E+c*M,R=o*T+l*x+c*y;u=u-w*C/(C*C-.5*w*R)}return u}function Ff(n,e){let t=Y3(n,e),i=ro({l:1,a:t*n,b:t*e}),r=Math.cbrt(1/Math.max(i.r,i.g,i.b)),s=r*t;return[r,s]}function q3(n,e,t,i,r,s=null){s||(s=Ff(n,e));let a;if((t-r)*s[1]-(s[0]-r)*i<=0)a=s[1]*r/(i*s[0]+s[1]*(r-t));else{a=s[1]*(r-1)/(i*(s[0]-1)+s[1]*(r-t));{let o=t-r,l=i,c=.3963377774*n+.2158037573*e,u=-.1055613458*n-.0638541728*e,f=-.0894841775*n-1.291485548*e,h=o+l*c,d=o+l*u,m=o+l*f;{let g=r*(1-a)+a*t,p=a*i,_=g+p*c,v=g+p*u,b=g+p*f,S=_*_*_,E=v*v*v,M=b*b*b,T=3*h*_*_,x=3*d*v*v,y=3*m*b*b,w=6*h*h*_,C=6*d*d*v,R=6*m*m*b,L=4.0767416621*S-3.3077115913*E+.2309699292*M-1,U=4.0767416621*T-3.3077115913*x+.2309699292*y,I=4.0767416621*w-3.3077115913*C+.2309699292*R,F=U/(U*U-.5*L*I),N=-L*F,Y=-1.2684380046*S+2.6097574011*E-.3413193965*M-1,j=-1.2684380046*T+2.6097574011*x-.3413193965*y,Z=-1.2684380046*w+2.6097574011*C-.3413193965*R,O=j/(j*j-.5*Y*Z),H=-Y*O,B=-.0041960863*S-.7034186147*E+1.707614701*M-1,V=-.0041960863*T-.7034186147*x+1.707614701*y,G=-.0041960863*w-.7034186147*C+1.707614701*R,z=V/(V*V-.5*B*G),W=-B*z;N=F>=0?N:1e6,H=O>=0?H:1e6,W=z>=0?W:1e6,a+=Math.min(N,Math.min(H,W))}}}return a}function Nf(n,e,t=null){t||(t=Ff(n,e));let i=t[0],r=t[1];return[r/i,r/(1-i)]}function Yg(n,e,t){let i=Ff(e,t),r=q3(e,t,n,1,n,i),s=Nf(e,t,i),a=.11516993+1/(7.4477897+4.1590124*t+e*(-2.19557347+1.75198401*t+e*(-2.13704948-10.02301043*t+e*(-4.24894561+5.38770819*t+4.69891013*e)))),o=.11239642+1/(1.6132032-.68124379*t+e*(.40370612+.90148123*t+e*(-.27087943+.6122399*t+e*(.00299215-.45399568*t-.14661872*e)))),l=r/Math.min(n*s[0],(1-n)*s[1]),c=n*a,u=(1-n)*o,f=.9*l*Math.sqrt(Math.sqrt(1/(1/(c*c*c*c)+1/(u*u*u*u))));return c=n*.4,u=(1-n)*.8,[Math.sqrt(1/(1/(c*c)+1/(u*u))),f,r]}function rm(n){const e=n.l!==void 0?n.l:0,t=n.a!==void 0?n.a:0,i=n.b!==void 0?n.b:0,r={mode:"okhsl",l:qh(e)};n.alpha!==void 0&&(r.alpha=n.alpha);let s=Math.sqrt(t*t+i*i);if(!s)return r.s=0,r;let[a,o,l]=Yg(e,t/s,i/s),c;if(s<o){let u=0,f=.8*a,h=1-f/o;c=(s-u)/(f+h*(s-u))*.8}else{let u=o,f=.2*o*o*1.25*1.25/a,h=1-f/(l-o);c=.8+.2*((s-u)/(f+h*(s-u)))}return c&&(r.s=c,r.h=dn(Math.atan2(i,t)*180/Math.PI)),r}function sm(n){let e=n.h!==void 0?n.h:0,t=n.s!==void 0?n.s:0,i=n.l!==void 0?n.l:0;const r={mode:"oklab",l:Ul(i)};if(n.alpha!==void 0&&(r.alpha=n.alpha),!t||i===1)return r.a=r.b=0,r;let s=Math.cos(e/180*Math.PI),a=Math.sin(e/180*Math.PI),[o,l,c]=Yg(r.l,s,a),u,f,h,d;t<.8?(u=1.25*t,f=0,h=.8*o,d=1-h/l):(u=5*(t-.8),f=l,h=.2*l*l*1.25*1.25/o,d=1-h/(c-l));let m=f+u*h/(1-d*u);return r.a=m*s,r.b=m*a,r}const K3={...Pg,mode:"okhsl",channels:["h","s","l","alpha"],parse:["--okhsl"],serialize:"--okhsl",fromMode:{oklab:rm,rgb:n=>rm($l(n))},toMode:{oklab:sm,rgb:n=>Jl(sm(n))}};function am(n){let e=n.l!==void 0?n.l:0,t=n.a!==void 0?n.a:0,i=n.b!==void 0?n.b:0,r=Math.sqrt(t*t+i*i),s=r?t/r:1,a=r?i/r:1,[o,l]=Nf(s,a),c=.5,u=1-c/o,f=l/(r+e*l),h=f*e,d=f*r,m=Ul(h),g=d*m/h,p=ro({l:m,a:s*g,b:a*g}),_=Math.cbrt(1/Math.max(p.r,p.g,p.b,0));e=e/_,r=r/_*qh(e)/e,e=qh(e);const v={mode:"okhsv",s:r?(c+l)*d/(l*c+l*u*d):0,v:e?e/h:0};return v.s&&(v.h=dn(Math.atan2(i,t)*180/Math.PI)),n.alpha!==void 0&&(v.alpha=n.alpha),v}function om(n){const e={mode:"oklab"};n.alpha!==void 0&&(e.alpha=n.alpha);const t=n.h!==void 0?n.h:0,i=n.s!==void 0?n.s:0,r=n.v!==void 0?n.v:0,s=Math.cos(t/180*Math.PI),a=Math.sin(t/180*Math.PI),[o,l]=Nf(s,a),c=.5,u=1-c/o,f=1-i*c/(c+l-l*u*i),h=i*l*c/(c+l-l*u*i),d=Ul(f),m=h*d/f,g=ro({l:d,a:s*m,b:a*m}),p=Math.cbrt(1/Math.max(g.r,g.g,g.b,0)),_=Ul(r*f),v=h*_/f;return e.l=_*p,e.a=v*s*p,e.b=v*a*p,e}const Z3={...Lg,mode:"okhsv",channels:["h","s","v","alpha"],parse:["--okhsv"],serialize:"--okhsv",fromMode:{oklab:am,rgb:n=>am($l(n))},toMode:{oklab:om,rgb:n=>Jl(om(n))}};function $3(n,e){if(!e||e[0]!=="oklab")return;const t={mode:"oklab"},[,i,r,s,a]=e;if(!(i.type===Ue.Hue||r.type===Ue.Hue||s.type===Ue.Hue))return i.type!==Ue.None&&(t.l=Math.min(Math.max(0,i.type===Ue.Number?i.value:i.value/100),1)),r.type!==Ue.None&&(t.a=r.type===Ue.Number?r.value:r.value*.4/100),s.type!==Ue.None&&(t.b=s.type===Ue.Number?s.value:s.value*.4/100),a.type!==Ue.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ue.Number?a.value:a.value/100))),t}const J3={...Lf,mode:"oklab",toMode:{lrgb:ro,rgb:Jl},fromMode:{lrgb:jg,rgb:$l},ranges:{l:[0,1],a:[-.4,.4],b:[-.4,.4]},parse:[$3],serialize:n=>`oklab(${n.l!==void 0?n.l:"none"} ${n.a!==void 0?n.a:"none"} ${n.b!==void 0?n.b:"none"}${n.alpha<1?` / ${n.alpha}`:""})`};function Q3(n,e){if(!e||e[0]!=="oklch")return;const t={mode:"oklch"},[,i,r,s,a]=e;if(i.type!==Ue.None){if(i.type===Ue.Hue)return;t.l=Math.min(Math.max(0,i.type===Ue.Number?i.value:i.value/100),1)}if(r.type!==Ue.None&&(t.c=Math.max(0,r.type===Ue.Number?r.value:r.value*.4/100)),s.type!==Ue.None){if(s.type===Ue.Percentage)return;t.h=s.value}return a.type!==Ue.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ue.Number?a.value:a.value/100))),t}const ew={...If,mode:"oklch",toMode:{oklab:n=>Ar(n,"oklab"),rgb:n=>Jl(Ar(n,"oklab"))},fromMode:{rgb:n=>wr($l(n),"oklch"),oklab:n=>wr(n,"oklch")},parse:[Q3],serialize:n=>`oklch(${n.l!==void 0?n.l:"none"} ${n.c!==void 0?n.c:"none"} ${n.h!==void 0?n.h:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,ranges:{l:[0,1],c:[0,.4],h:[0,360]}},lm=n=>{let{r:e,g:t,b:i,alpha:r}=na(n),s={mode:"xyz65",x:.486570948648216*e+.265667693169093*t+.1982172852343625*i,y:.2289745640697487*e+.6917385218365062*t+.079286914093745*i,z:0*e+.0451133818589026*t+1.043944368900976*i};return r!==void 0&&(s.alpha=r),s},cm=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r=ia({r:n*2.4934969119414263-e*.9313836179191242-.402710784450717*t,g:n*-.8294889695615749+e*1.7626640603183465+.0236246858419436*t,b:n*.0358458302437845-e*.0761723892680418+.9568845240076871*t},"p3");return i!==void 0&&(r.alpha=i),r},tw={...ta,mode:"p3",parse:["display-p3"],serialize:"display-p3",fromMode:{rgb:n=>cm(ns(n)),xyz65:cm},toMode:{rgb:n=>is(lm(n)),xyz65:lm}},xu=n=>{let e=Math.abs(n);return e>=1/512?Math.sign(n)*Math.pow(e,1/1.8):16*n},um=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"prophoto",r:xu(n*1.3457868816471585-e*.2555720873797946-.0511018649755453*t),g:xu(n*-.5446307051249019+e*1.5082477428451466+.0205274474364214*t),b:xu(n*0+e*0+1.2119675456389452*t)};return i!==void 0&&(r.alpha=i),r},yu=(n=0)=>{let e=Math.abs(n);return e>=16/512?Math.sign(n)*Math.pow(e,1.8):n/16},hm=n=>{let e=yu(n.r),t=yu(n.g),i=yu(n.b),r={mode:"xyz50",x:.7977666449006423*e+.1351812974005331*t+.0313477341283922*i,y:.2880748288194013*e+.7118352342418731*t+899369387256e-16*i,z:0*e+0*t+.8251046025104602*i};return n.alpha!==void 0&&(r.alpha=n.alpha),r},nw={...ta,mode:"prophoto",parse:["prophoto-rgb"],serialize:"prophoto-rgb",fromMode:{xyz50:um,rgb:n=>um(io(n))},toMode:{xyz50:hm,rgb:n=>no(hm(n))}},fm=1.09929682680944,iw=.018053968510807,bu=n=>{const e=Math.abs(n);return e>iw?(Math.sign(n)||1)*(fm*Math.pow(e,.45)-(fm-1)):4.5*n},dm=({x:n,y:e,z:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let r={mode:"rec2020",r:bu(n*1.7166511879712683-e*.3556707837763925-.2533662813736599*t),g:bu(n*-.6666843518324893+e*1.6164812366349395+.0157685458139111*t),b:bu(n*.0176398574453108-e*.0427706132578085+.9421031212354739*t)};return i!==void 0&&(r.alpha=i),r},pm=1.09929682680944,rw=.018053968510807,Mu=(n=0)=>{let e=Math.abs(n);return e<rw*4.5?n/4.5:(Math.sign(n)||1)*Math.pow((e+pm-1)/pm,1/.45)},mm=n=>{let e=Mu(n.r),t=Mu(n.g),i=Mu(n.b),r={mode:"xyz65",x:.6369580483012911*e+.1446169035862083*t+.1688809751641721*i,y:.262700212011267*e+.6779980715188708*t+.059301716469862*i,z:0*e+.0280726930490874*t+1.0609850577107909*i};return n.alpha!==void 0&&(r.alpha=n.alpha),r},sw={...ta,mode:"rec2020",fromMode:{xyz65:dm,rgb:n=>dm(ns(n))},toMode:{xyz65:mm,rgb:n=>is(mm(n))},parse:["rec2020"],serialize:"rec2020"},Zr=.0037930732552754493,qg=Math.cbrt(Zr),Su=n=>Math.cbrt(n)-qg,aw=n=>{const{r:e,g:t,b:i,alpha:r}=na(n),s=Su(.3*e+.622*t+.078*i+Zr),a=Su(.23*e+.692*t+.078*i+Zr),o=Su(.2434226892454782*e+.2047674442449682*t+.5518098665095535*i+Zr),l={mode:"xyb",x:(s-a)/2,y:(s+a)/2,b:o-(s+a)/2};return r!==void 0&&(l.alpha=r),l},Tu=n=>Math.pow(n+qg,3),ow=({x:n,y:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r=Tu(n+e)-Zr,s=Tu(e-n)-Zr,a=Tu(t+e)-Zr,o=ia({r:11.031566904639861*r-9.866943908131562*s-.16462299650829934*a,g:-3.2541473810744237*r+4.418770377582723*s-.16462299650829934*a,b:-3.6588512867136815*r+2.7129230459360922*s+1.9459282407775895*a});return i!==void 0&&(o.alpha=i),o},lw={mode:"xyb",channels:["x","y","b","alpha"],parse:["--xyb"],serialize:"--xyb",toMode:{rgb:ow},fromMode:{rgb:aw},ranges:{x:[-.0154,.0281],y:[0,.8453],b:[-.2778,.388]},interpolate:{x:ze,y:ze,b:ze,alpha:{use:ze,fixup:nn}}},cw={mode:"xyz50",parse:["xyz-d50"],serialize:"xyz-d50",toMode:{rgb:no,lab:Uf},fromMode:{rgb:io,lab:Df},channels:["x","y","z","alpha"],ranges:{x:[0,.964],y:[0,.999],z:[0,.825]},interpolate:{x:ze,y:ze,z:ze,alpha:{use:ze,fixup:nn}}},uw=n=>{let{x:e,y:t,z:i,alpha:r}=n;e===void 0&&(e=0),t===void 0&&(t=0),i===void 0&&(i=0);let s={mode:"xyz50",x:1.0479298208405488*e+.0229467933410191*t-.0501922295431356*i,y:.0296278156881593*e+.990434484573249*t-.0170738250293851*i,z:-.0092430581525912*e+.0150551448965779*t+.7518742899580008*i};return r!==void 0&&(s.alpha=r),s},hw=n=>{let{x:e,y:t,z:i,alpha:r}=n;e===void 0&&(e=0),t===void 0&&(t=0),i===void 0&&(i=0);let s={mode:"xyz65",x:.9554734527042182*e-.0230985368742614*t+.0632593086610217*i,y:-.0283697069632081*e+1.0099954580058226*t+.021041398966943*i,z:.0123140016883199*e-.0205076964334779*t+1.3303659366080753*i};return r!==void 0&&(s.alpha=r),s},fw={mode:"xyz65",toMode:{rgb:is,xyz50:uw},fromMode:{rgb:ns,xyz50:hw},ranges:{x:[0,.95],y:[0,1],z:[0,1.088]},channels:["x","y","z","alpha"],parse:["xyz","xyz-d65"],serialize:"xyz-d65",interpolate:{x:ze,y:ze,z:ze,alpha:{use:ze,fixup:nn}}},dw=({r:n,g:e,b:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r={mode:"yiq",y:.29889531*n+.58662247*e+.11448223*t,i:.59597799*n-.2741761*e-.32180189*t,q:.21147017*n-.52261711*e+.31114694*t};return i!==void 0&&(r.alpha=i),r},pw=({y:n,i:e,q:t,alpha:i})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const r={mode:"rgb",r:n+.95608445*e+.6208885*t,g:n-.27137664*e-.6486059*t,b:n-1.10561724*e+1.70250126*t};return i!==void 0&&(r.alpha=i),r},mw={mode:"yiq",toMode:{rgb:pw},fromMode:{rgb:dw},channels:["y","i","q","alpha"],parse:["--yiq"],serialize:"--yiq",ranges:{i:[-.595,.595],q:[-.522,.522]},interpolate:{y:ze,i:ze,q:ze,alpha:{use:ze,fixup:nn}}},gw=n=>{n[0]===void 0&&(n[0]=0),n[n.length-1]===void 0&&(n[n.length-1]=1);let e=1,t,i,r,s;for(;e<n.length;){if(n[e]===void 0){for(i=e,r=n[e-1],t=e;n[t]===void 0;)t++;for(s=(n[t]-r)/(t-e+1);e<t;)n[e]=r+(e+1-i)*s,e++}else n[e]<n[e-1]&&(n[e]=n[e-1]);e++}return n},_w=(n=.5)=>e=>n<=0?1:n>=1?0:Math.pow(e,Math.log(.5)/Math.log(n)),Yo=n=>typeof n=="function",Or=n=>n&&typeof n=="object",gm=n=>typeof n=="number",vw=(n,e="rgb",t,i)=>{let r=Mg(e),s=Cf(e),a=[],o=[],l={};n.forEach(h=>{Array.isArray(h)?(a.push(s(h[0])),o.push(h[1])):gm(h)||Yo(h)?l[o.length]=h:(a.push(s(h)),o.push(void 0))}),gw(o);let c=r.channels.reduce((h,d)=>{let m;return Or(t)&&Or(t[d])&&t[d].fixup?m=t[d].fixup:Or(r.interpolate[d])&&r.interpolate[d].fixup?m=r.interpolate[d].fixup:m=g=>g,h[d]=m(a.map(g=>g[d])),h},{}),u=r.channels.reduce((h,d)=>{let m;return Yo(t)?m=t:Or(t)&&Yo(t[d])?m=t[d]:Or(t)&&Or(t[d])&&t[d].use?m=t[d].use:Yo(r.interpolate[d])?m=r.interpolate[d]:Or(r.interpolate[d])&&(m=r.interpolate[d].use),h[d]=m(c[d]),h},{}),f=a.length-1;return h=>{if(h=Math.min(Math.max(0,h),1),h<=o[0])return a[0];if(h>o[f])return a[f];let d=0;for(;o[d]<h;)d++;let m=o[d-1],g=o[d]-m,p=(h-m)/g,_=l[d]||l[0];_!==void 0&&(gm(_)&&(_=_w((_-m)/g)),p=_(p));let v=(d-1+p)/f;return r.channels.reduce((b,S)=>{let E=u[S](v);return E!==void 0&&(b[S]=E),b},{mode:e})}},xw=(n,e="rgb",t)=>vw(n,e,t);yt(n3);yt(c3);yt(u3);yt(h3);yt(p3);yt(Pg);yt(Lg);yt(T3);yt(E3);yt(C3);yt(P3);yt(Lf);yt(U3);yt(If);yt(I3);yt(W3);yt(X3);yt(j3);yt(K3);yt(Z3);yt(J3);yt(ew);yt(tw);yt(nw);yt(sw);yt(ta);yt(lw);yt(cw);yt(fw);yt(mw);function ei(n){let e=n>>>0;return()=>{e|=0,e=e+1831565813|0;let t=Math.imul(e^e>>>15,1|e);return t=t+Math.imul(t^t>>>7,61|t)^t,((t^t>>>14)>>>0)/4294967296}}const yw=[{id:"beidou",name_zh:"北斗",lore:"天枢·北斗之首，主枢机；七星斟酌元气，运乎中央，临制四方",stars:[{x:-.6456,y:.4576,mag:1.81,name:"天枢"},{x:-.7715,y:.1074,mag:2.34,name:"天璇"},{x:-.3043,y:-.1753,mag:2.41,name:"天玑"},{x:-.08,y:.0366,mag:3.32,name:"天权"},{x:.2846,y:-.0219,mag:1.76,name:"玉衡"},{x:.5838,y:-.0447,mag:2.23,name:"开阳"},{x:.9331,y:-.3597,mag:1.85,name:"摇光"}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6]]},{id:"beiji",name_zh:"北极",lore:"北极五星，紫微中枢，帝星所居——北辰居其所而众星共之",stars:[{x:.4553,y:-.5791,mag:3},{x:.141,y:-.3243,mag:2.07},{x:-.053,y:-.1338,mag:4.25},{x:-.1729,y:.1083,mag:4.8},{x:-.3703,y:.9289,mag:5.38}],lines:[[0,1],[1,2],[2,3],[3,4]]},{id:"gouchen",name_zh:"勾陈",lore:"勾陈六星，天皇大帝之御座，主后宫，亦掌兵革",stars:[{x:.572,y:.2057,mag:4.7},{x:.3764,y:.489,mag:4.24},{x:.0615,y:.418,mag:1.97},{x:-.04,y:.0144,mag:4.35},{x:-.2588,y:-.4241,mag:4.21},{x:-.7112,y:-.703,mag:4.29}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5]]},{id:"ziwei_zuoyuan",name_zh:"紫微左垣",lore:"紫微东藩，左垣八星，如臣卫帝庭之左",stars:[{x:-.6802,y:-.3579,mag:3.29},{x:-.5188,y:-.4593,mag:4.01},{x:-.3731,y:-.3887,mag:2.73},{x:-.1488,y:-.2772,mag:3.17},{x:.1973,y:-.0506,mag:4.82},{x:.3691,y:.1925,mag:5.18},{x:.5624,y:.5353,mag:4.41},{x:.5921,y:.8058,mag:5.42}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7]]},{id:"ziwei_youyuan",name_zh:"紫微右垣",lore:"紫微西藩，右垣七星，如臣卫帝庭之右",stars:[{x:.9449,y:.203,mag:3.67},{x:.5853,y:-3e-4,mag:3.85},{x:.4498,y:-.1479,mag:3.82},{x:.1037,y:-.2654,mag:4.54},{x:-.393,y:-.1982,mag:5.11},{x:-.7644,y:.0323,mag:4.26},{x:-.9264,y:.3765,mag:4.74}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6]]},{id:"huagai",name_zh:"华盖",lore:"华盖七星，覆于帝座之上，主遮护銮驾",stars:[{x:-.0126,y:.128,mag:5.82},{x:.1535,y:.9881,mag:5.28},{x:-.3751,y:.597,mag:5.87},{x:-.5879,y:-.3058,mag:5.32},{x:-.1661,y:-.5295,mag:4.72},{x:.307,y:-.5517,mag:5.57},{x:.681,y:-.3262,mag:4.97}],lines:[[0,1],[0,2],[0,3],[0,4],[0,5],[0,6]]},{id:"wenchang",name_zh:"文昌",lore:"文昌六星，司禄主文，掌天下文运科名",stars:[{x:.4513,y:.8924,mag:3.78},{x:.5423,y:.002,mag:4.55},{x:.0387,y:-.4454,mag:3.17},{x:-.6297,y:-.4344,mag:4.46},{x:-.4025,y:-.0145,mag:4.8}],lines:[[0,1],[1,2],[2,3],[3,4]]},{id:"santai",name_zh:"三台",lore:"三台六星，上下两阶，天子陟降之梯，主德政升降",stars:[{x:-.8426,y:.5181,mag:3.12},{x:-.8074,y:.4499,mag:3.57},{x:-.0157,y:.0855,mag:3.45},{x:.0452,y:-.0028,mag:3.06},{x:.8033,y:-.4744,mag:3.49},{x:.8172,y:-.5763,mag:3.79}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5]]},{id:"wudi_neizuo",name_zh:"五帝内座",lore:"五帝内座五星，五方天帝之便座，承帝居于紫微",stars:[{x:.0387,y:-.0175,mag:5.49},{x:-.8678,y:-.4969,mag:5.27},{x:-.1558,y:.5448,mag:5.8},{x:.2515,y:-.4707,mag:5.44},{x:.7334,y:.4402,mag:5.1}],lines:[[0,1],[0,2],[0,3],[0,4]]},{id:"taiwei_zuoyuan",name_zh:"太微左垣",lore:"太微东藩，左垣五星，列卿大夫之位",stars:[{x:-.5895,y:-.524,mag:3.89},{x:-.1576,y:-.5858,mag:2.74},{x:.1166,y:-.203,mag:3.39},{x:.2419,y:.3914,mag:2.85},{x:.3886,y:.9214,mag:4.32}],lines:[[0,1],[1,2],[2,3],[3,4]]},{id:"taiwei_youyuan",name_zh:"太微右垣",lore:"太微西藩，右垣五星，列将相之班",stars:[{x:.5787,y:-.8155,mag:3.59},{x:-.0877,y:-.4314,mag:4.05},{x:-.0255,y:-.0301,mag:4},{x:-.2334,y:.408,mag:3.33},{x:-.2322,y:.869,mag:2.56}],lines:[[0,1],[1,2],[2,3],[3,4]]},{id:"wudizuo",name_zh:"五帝座",lore:"太微之中，五帝座五星，天子临朝听政之正位",stars:[{x:-.0986,y:-.0128,mag:2.14},{x:-.0792,y:.7029,mag:6.05},{x:-.5008,y:-.1439,mag:6.51},{x:.5836,y:.4493,mag:5.53},{x:.095,y:-.9955,mag:6.37}],lines:[[0,1],[0,2],[0,3],[0,4]]},{id:"tianshi_zuoyuan",name_zh:"天市左垣",lore:"天市东藩，十一星以诸侯为名，主四方商贾之事",stars:[{x:-.3742,y:.5321,mag:3.12},{x:-.2501,y:.5673,mag:4.41},{x:-.1289,y:.6184,mag:3.42},{x:.0299,y:.6533,mag:3.84},{x:.3792,y:.4119,mag:5.43},{x:.4972,y:.1634,mag:2.99},{x:.4329,y:-.1618,mag:4.62},{x:.1464,y:-.4012,mag:3.23},{x:-.0391,y:-.6417,mag:3.32},{x:-.2253,y:-.8579,mag:3.54},{x:-.4681,y:-.8837,mag:2.43}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10]]},{id:"tianshi_youyuan",name_zh:"天市右垣",lore:"天市西藩，十一星以都邑为号，主市井度量之制",stars:[{x:.2745,y:.6377,mag:2.78},{x:.182,y:.5196,mag:3.74},{x:.0256,y:.4156,mag:5},{x:-.1068,y:.35,mag:3.85},{x:-.2244,y:.3403,mag:3.65},{x:-.3602,y:.1113,mag:3.8},{x:-.2522,y:-.0849,mag:2.63},{x:-.1762,y:-.1775,mag:3.71},{x:.1023,y:-.5699,mag:2.73},{x:.1504,y:-.6193,mag:3.23},{x:.385,y:-.9229,mag:2.54}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10]]},{id:"jiao",name_zh:"角宿",lore:"东方苍龙之首，角二星为天门，主万物生发",stars:[{x:-.2177,y:-.976,mag:.98},{x:.2177,y:.976,mag:3.38}],lines:[[0,1]]},{id:"kang",name_zh:"亢宿",lore:"苍龙之颈，亢四星，主朝廷礼乐，亦司疾疫",stars:[{x:-.2463,y:-.3728,mag:4.18},{x:-.1236,y:.3179,mag:4.07},{x:.3693,y:.9293,mag:4.81},{x:6e-4,y:-.8744,mag:4.52}],lines:[[0,1],[1,2],[0,3]]},{id:"xin",name_zh:"心宿",lore:"苍龙之心，心三星为天王明堂，心宿二即大火，观之以授时",stars:[{x:-.7951,y:.5347,mag:2.9},{x:.0663,y:.1501,mag:1.06},{x:.7288,y:-.6848,mag:2.82}],lines:[[0,1],[1,2]]},{id:"dou",name_zh:"斗宿",lore:"北方玄武之首，南斗六星，主爵禄寿命之权衡",stars:[{x:-.8231,y:.5679,mag:3.84},{x:-.4305,y:.0908,mag:2.82},{x:.0174,y:-.0783,mag:3.17},{x:.259,y:-.003,mag:2.05},{x:.5468,y:-.1665,mag:3.32},{x:.4303,y:-.4109,mag:2.6}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5]]},{id:"kui",name_zh:"奎宿",lore:"西方白虎之库，奎十六星如破鞋，主文章武库",stars:[{x:-.0516,y:-.5016,mag:4.4},{x:-.2394,y:-.4275,mag:4.08},{x:-.1846,y:-.1406,mag:5.55},{x:-.388,y:-2e-4,mag:4.34},{x:-.3683,y:.1285,mag:3.27},{x:-.4004,y:.3699,mag:4.34},{x:-.1616,y:.9869,mag:4.53},{x:-.0518,y:.7626,mag:3.86},{x:.1675,y:.5204,mag:2.07},{x:.111,y:.2309,mag:6.28},{x:.2121,y:.0585,mag:4.51},{x:.3882,y:-.0482,mag:5.23},{x:.363,y:-.1725,mag:4.74},{x:.2634,y:-.4004,mag:4.67},{x:.2272,y:-.7012,mag:4.66},{x:.1132,y:-.6655,mag:5.33}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10],[10,11],[11,12],[12,13],[13,14],[14,15],[15,0]]},{id:"bi",name_zh:"毕宿",lore:"白虎之网，毕八星，主边兵弋猎，毕宿五为虎视",stars:[{x:.1127,y:.4028,mag:3.53},{x:.0087,y:.226,mag:4.3},{x:-.077,y:.1719,mag:3.77},{x:-.1842,y:-.0971,mag:3.65},{x:.3609,y:.0288,mag:.87},{x:.1132,y:-.0504,mag:3.84},{x:.0378,y:-.099,mag:4.48},{x:-.8479,y:-.5301,mag:3.41},{x:.4757,y:-.0529,mag:4.67}],lines:[[0,1],[1,2],[2,3],[4,5],[5,6],[6,3],[3,7],[4,8]]},{id:"shen",name_zh:"参宿",lore:"白虎之躯，参宿七星，中三星为腰带，主斩刈权衡",stars:[{x:.4907,y:.8713,mag:.45},{x:.1222,y:-.0875,mag:1.74},{x:.0069,y:-.0122,mag:1.69},{x:-.1,y:.0795,mag:2.25},{x:-.5438,y:-.7306,mag:.18},{x:-.2754,y:.7598,mag:1.64},{x:.2993,y:-.8803,mag:2.07}],lines:[[0,1],[1,2],[2,3],[3,4],[3,5],[1,6]]},{id:"liu",name_zh:"柳宿",lore:"南方朱雀之喙，柳八星，主草木庖厨",stars:[{x:-.1153,y:.1717,mag:4.35},{x:-.3232,y:-.2171,mag:4.3},{x:-.5015,y:-.2258,mag:4.45},{x:-.5436,y:.1519,mag:4.14},{x:-.1808,y:.2646,mag:3.38},{x:.1609,y:.189,mag:3.11},{x:.5821,y:.0544,mag:4.99},{x:.9214,y:-.3887,mag:3.89}],lines:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7]]}],bw={asterisms:yw},At=100,Of=At/400,Ia=.3*At,fr=.54*At,Mw=.95*At,Eu=At+22*Of,qo=At+52*Of,wu=At+37*Of,Sw=-160,kn=15262418,Au=14462549,_m=15781247,Fa=[-145,-72,-2,52,160],vm=[-108,-37,25,106,-170],xm=["天枢","天璇","天玑","天权","玉衡","开阳","摇光"],Tw=[...Fa,200,262],$t={blueWhite:[.78,.86,1],moonWhite:[.949,.929,.878],warmGold:[.98,.8,.45],softOrange:[.93,.66,.44]},Ew=new Map(bw.asterisms.map(n=>[n.id,n])),Kg={系统:{id:"dou",name:"斗宿"},学习力:{id:"kui",name:"奎宿"},基础:{id:"huagai",name:"华盖"},操作:{id:"shen",name:"参宿"},感知:{id:"bi",name:"毕宿"},研究:{id:"wenchang",name:"文昌"},中间件:{id:"kang",name:"亢宿"},影响力:{id:"liu",name:"柳宿"},导航:{id:"yi",name:"翼宿"},战略:{id:"fang",name:"房宿"},运动:{id:"ji",name:"箕宿"},控制:{id:"zhen",name:"轸宿"},领导力:{id:"xuanyuan",name:"轩辕"},仿真:{id:"xu",name:"虚宿"}};function ww(n){var e;return((e=Kg[n])==null?void 0:e.name)??n}const ym=[{slots:[[0,4,1.15],[-.5,-1.5,.68],[-4,-6,.62],[-8,-8.5,.78],[-11.2,-7.2,.58],[3,-5.5,.62],[6.8,-7.8,.72]],links:[[0,1],[1,2],[2,3],[3,4],[1,5],[5,6]]},{slots:[[-11.8,2.8,.62],[-6,.5,.72],[-.5,-1,.92],[5,-.5,.68],[10.8,1.8,.6]],links:[[0,1],[1,2],[2,3],[3,4]]},{slots:[[-8.8,-1.8,.62],[-4.5,2,.7],[0,3.5,.9],[4.5,2,.7],[8.8,-1.8,.62]],links:[[0,1],[1,2],[2,3],[3,4]]},{slots:[[-2,-1.2,.85],[2.2,-.8,.65],[0,2,.6]],links:[[0,1],[1,2],[2,0]]},{slots:[[-9.2,-2.5,.62],[-4,2.2,.72],[1,-2.2,.82],[6,2.5,.65],[10.2,-.8,.6]],links:[[0,1],[1,2],[2,3],[3,4]]}],Aw=[[-40,18,.72,1],[-78,11.5,.6,0],[-112,15.5,.68,0],[-148,12.5,.58,0],[168,19,.78,1],[142,11.5,.58,0],[116,17,.65,0],[88,11,.58,0],[58,15,.72,1],[34,21,.6,0],[-32,24,.62,0],[-95,22.5,.65,1]],Rw=[[0,1],[1,2],[2,3],[5,6],[6,7],[8,9]];function zn(n,e){const t=e*Math.PI/180;return[n*Math.cos(t),n*Math.sin(t)]}function Cw(n){return n=n%360,n>180&&(n-=360),n<-180&&(n+=360),n}function Pw(n){const e=ei(20260921),t=n.categories.reduce((B,V)=>B+V.count,0)||1,i=[];let r=Sw;for(const B of n.categories){const V=B.count/t*360;i.push({id:B.id,name:B.name,asterism:ww(B.name),start:r,width:V,count:B.count}),r+=V}const s=B=>i.find(V=>V.id===B),a=[.961,.918,.824],o={plan:[],deep:[],size:[],opacity:[],core:[],ring:[],legacyRing:[],color:[],deepColor:[],filler:[],deepOpScale:[],deepSizeScale:[]},l=(B,V,G,z,W,q,ce,me,Q,ie,be,De,ye,_e,Ne=$t.moonWhite)=>{o.plan.push(B,V,0),o.deep.push(G,z,W),o.size.push(q),o.opacity.push(ce),o.core.push(De),o.ring.push(ye),o.legacyRing.push(_e),o.color.push(Q[0],Q[1],Q[2]),o.deepColor.push(Ne[0],Ne[1],Ne[2]),o.filler.push(me?1:0),o.deepOpScale.push(ie),o.deepSizeScale.push(be)},c=()=>[(e()*2-1)*250,(e()*2-1)*140,40-e()*180],u=new Map;for(const B of n.skills)u.has(B.category)||u.set(B.category,[]),u.get(B.category).push(B);for(const B of n.skills){if(B.lit||B.status==="learning")continue;const V=s(B.category);if(!V)continue;const G=V.start+1.5+e()*(V.width-3),z=At*(.34+.58*Math.sqrt(e())),[W,q]=zn(z,G),[ce,me,Q]=c();l(W,q,ce,me,Q,.62+e()*.2,.34+e()*.08,!1,a,.6,.55,0,1,e()<.3?1:0)}const f=1800;for(const B of i){const V=Math.round(B.count/t*f);for(let G=0;G<V;G++){let z,W;if(e()<.15){if(z=e()*360,W=Ia*(.52+.46*e()),Math.abs(Cw(z))<25)continue}else z=B.start+1.3+e()*(B.width-2.6),W=At*(.33+.61*Math.sqrt(e()));const[q,ce]=zn(W,z),[me,Q,ie]=c(),be=[1,.88,.69],De=[.74,.81,1],ye=e(),_e=ye>.975?be:ye>.95?De:a,Ne=Math.pow(e(),8),ae=Ne>.42,Ee=Math.min(1.15,.15+Math.pow(e(),1.8)*.55+Ne*.75),k=.35+Math.pow(e(),2)*.35+Ne*.6,de=ae?$t.blueWhite:ye>.92?$t.softOrange:ye>.88?$t.warmGold:$t.moonWhite;l(q,ce,me,Q,ie,ae?.62:.34+e()*.22,ae?.38:.1+e()*.12,!0,_e,Ee,k,1,0,e()<.18?1:0,de)}}const h={plan:[],deep:[],size:[],opacity:[],core:[],ring:[],color:[],deepColor:[],links:[],skills:[]},d={plan:[],deep:[],size:[],opacity:[],color:[],deepColor:[]},m=[],g=[],p=new Map;n.evidence.forEach(B=>B.skill_ids.forEach(V=>p.set(V,(p.get(V)||0)+1)));let _=0;n.categories.forEach((B,V)=>{const G=s(B.id);if(!G)return;const z=Kg[B.name],W=z?Ew.get(z.id):void 0,q=(u.get(B.id)||[]).filter(ae=>ae.lit||ae.status==="learning");if(!q.length&&!z)return;const ce=G.start+G.width/2,[me,Q]=zn(At*.72,ce),ie=ei(500+V);let be,De,ye;if(W){const ae=G.width*Math.PI/180*(At*.72),Ee=Math.min(11,Math.max(6,ae*.24)),k=(ce-90)*Math.PI/180,de=Math.cos(k),Pe=Math.sin(k);be=W.stars.map(we=>{const pe=we.mag??5,Re=.55+Math.min(3,Math.max(0,5.6-pe))*.11;return[(we.x*de-we.y*Pe)*Ee,(we.x*Pe+we.y*de)*Ee,Re]}),ye=W.stars.map(we=>(we.mag??5)<3?$t.blueWhite:$t.moonWhite),De=W.lines}else{const ae=ym[V%ym.length];be=ae.slots.map(Ee=>[Ee[0],Ee[1],Ee[2]]),ye=ae.slots.map(()=>$t.moonWhite),De=ae.links}for(;be.length<q.length;){const ae=be[be.length-1];be.push([ae[0]+4.5,ae[1]+(ie()-.5)*3,.58]),ye.push($t.moonWhite)}const _e=be.map(([ae,Ee])=>[me+ae*1.08,Q+Ee*1.08,(ie()-.5)*36]);for(const[ae,Ee]of De)ae>=be.length||Ee>=be.length||(m.push(me+be[ae][0],Q+be[ae][1],0,me+be[Ee][0],Q+be[Ee][1],0),g.push(_e[ae][0],_e[ae][1],_e[ae][2],_e[Ee][0],_e[Ee][1],_e[Ee][2]));const Ne=_;q.forEach((ae,Ee)=>{const[k,de,Pe]=be[Ee],we=W?0:(ie()-.5)*1.6,pe=W?0:(ie()-.5)*1.6,Re=me+k+we,D=Q+de+pe,[A,X,ee]=_e[Ee];h.plan.push(Re,D,0),h.deep.push(A,X,ee),h.size.push(Pe*(ae.lit?1.15:.9)),h.opacity.push(ae.lit?.95:.55),h.core.push(1),h.ring.push(ae.lit?1:0),h.color.push(.961,.918,.824);const he=ye[Ee];h.deepColor.push(he[0],he[1],he[2]),h.skills.push({id:ae.id,label:ae.label,category:ae.category,status:ae.status,evidenceCount:p.get(ae.id)||0}),_+=1});for(let ae=q.length;ae<be.length;ae++){const[Ee,k,de]=be[ae],[Pe,we,pe]=_e[ae];d.plan.push(me+Ee,Q+k,0),d.deep.push(Pe,we,pe),d.size.push(Math.max(.7,de*.85)),d.opacity.push(.16),d.color.push($t.moonWhite[0],$t.moonWhite[1],$t.moonWhite[2]);const Re=ye[ae];d.deepColor.push(Re[0],Re[1],Re[2])}if(q.length>=3)for(const[ae,Ee]of De)ae<q.length&&Ee<q.length&&h.links.push(Ne+ae,Ne+Ee)});const v=n.goals.filter(B=>B.status!=="completed"),b=n.goals.filter(B=>B.status==="completed"),E=[...v.slice(0,Fa.length).map((B,V)=>({g:B,angle:Fa[V],seat:V})),...b.slice(0,vm.length).map((B,V)=>({g:B,angle:vm[V],seat:-1}))].map(({g:B,angle:V,seat:G},z)=>{const[W,q]=zn(fr,V),ce=ei(900+z),me=G>=0?58+G*26:60,[Q,ie]=zn(me,V);return{id:B.id,title:B.title,status:B.status||"active",angle:V,seatName:G>=0?xm[G]:void 0,plan:[W,q,0],deep:[Q,ie,(ce()-.5)*20]}}),M=Tw.map((B,V)=>{var G;return{name:xm[V],angle:B,goalIndex:V<Fa.length&&((G=E[V])!=null&&G.seatName)?V:null}}),T={plan:[],size:[],gold:[],links:Rw};for(const[B,V,G,z]of Aw){const[W,q]=zn(V,B);T.plan.push(W,q,0),T.size.push(G),T.gold.push(z)}const x=new Map(n.skills.map(B=>[B.id,B.category])),y=new Map(E.map((B,V)=>[B.id,V])),w=new Map(E.map(B=>[B.id,B.angle])),C=new Map(E.map(B=>[B.id,B.deep])),R=[-13,9,-6,15],L=new Map;let U=0;const I=[],N=58+v.slice(0,Fa.length).length*26+18;n.projects.forEach(B=>{const V=(B.goal_ids||[]).find(ie=>w.has(ie));let G,z,W=-1,q;const ce=ei(3e3+I.length);if(V!==void 0){W=y.get(V)??-1;const ie=L.get(V)||0;L.set(V,ie+1),G=w.get(V)+R[ie%R.length],z=fr+(ie%2===0?-10:10);const be=C.get(V),De=5+Math.min(ie,4)*2.2,[ye,_e]=zn(De,ce()*360);q=[be[0]+ye,be[1]+_e,be[2]+(ce()-.5)*8]}else{G=-170+U*42,U+=1,z=fr+24;const[ie,be]=zn(N,G);q=[ie,be,(ce()-.5)*12]}const[me,Q]=zn(z,G);I.push({id:B.id,title:B.title,status:B.status,progress:B.progress,taskCount:B.task_count,goalIndex:W,plan:[me,Q,0],deep:q})});const Y={plan:[],deep:[],size:[],opacity:[]};I.forEach((B,V)=>{const G=ei(3100+V);for(let z=0;z<Math.min(B.taskCount,5);z++){const W=G()*360,q=3.8+G()*2.4,[ce,me]=zn(q,W);Y.plan.push(B.plan[0]+ce,B.plan[1]+me,0),Y.deep.push(B.deep[0]+ce*1.3,B.deep[1]+me*1.3,B.deep[2]+(G()-.5)*4),Y.size.push(.42),Y.opacity.push(B.status==="active"?.55:.3)}});const j={weak:4,unrated:4,medium:6.5,strong:9,high_trust:12},Z=[];n.evidence.filter(B=>B.flying).forEach((B,V)=>{const G=ei(3200+V),z=G()*360,W=At*(.42+.42*G()),[q,ce]=zn(W,z);Z.push({id:B.id,title:B.title,date:B.date,strength:B.strength,review:B.review_status,plan:[q,ce,0],deep:[(G()*2-1)*230,(G()*2-1)*120,30-G()*150],tailDir:z+90+(G()-.5)*30,tailLen:j[B.strength]||5})});const O={plan:[],deep:[],size:[],opacity:[]};n.evidence.filter(B=>!B.flying).forEach((B,V)=>{const G=ei(3300+V);let z,W;const q=B.project_refs.length&&I.find(ce=>ce.id===B.project_refs[0]);if(q){const[ce,me]=zn(5.5+G()*4,G()*360);z=q.plan[0]+ce,W=q.plan[1]+me}else{const ce=B.skill_ids.length?x.get(B.skill_ids[0]):void 0,me=ce&&s(ce)||i[Math.floor(G()*i.length)];if(!me)return;const Q=me.start+2+G()*(me.width-4),ie=At*(.45+.43*Math.sqrt(G()));[z,W]=zn(ie,Q)}O.plan.push(z,W,0),O.deep.push((G()*2-1)*240,(G()*2-1)*130,40-G()*170),O.size.push(.5),O.opacity.push(.4)});const H={plan:[],deep:[],size:[],opacity:[],trailPlan:[],trailDeep:[]};{const B=[-1.15*At,-.35*At],V=[-.42*At,.28*At],G=[.42*At,-.58*At],z=[1.15*At,.04*At],W=n.evidence.length;n.evidence.forEach((q,ce)=>{const me=ei(3400+ce),Q=W<=1?0:ce/(W-1),ie=1-Q,be=ie*ie*ie*B[0]+3*ie*ie*Q*V[0]+3*ie*Q*Q*G[0]+Q*Q*Q*z[0],De=ie*ie*ie*B[1]+3*ie*ie*Q*V[1]+3*ie*Q*Q*G[1]+Q*Q*Q*z[1];let ye=3*ie*ie*(V[0]-B[0])+6*ie*Q*(G[0]-V[0])+3*Q*Q*(z[0]-G[0]),_e=3*ie*ie*(V[1]-B[1])+6*ie*Q*(G[1]-V[1])+3*Q*Q*(z[1]-G[1]);const Ne=Math.hypot(ye,_e)||1;ye/=Ne,_e/=Ne;const ae=be+(me()-.5)*10,Ee=De+(me()-.5)*10,k=be*1.9+(me()-.5)*20,de=De*1.9+(me()-.5)*16,Pe=30-Q*130+(me()-.5)*20;H.plan.push(ae,Ee,0),H.deep.push(k,de,Pe),H.trailPlan.push(ae,Ee,0,ae-ye*2.6,Ee-_e*2.6,0),H.trailDeep.push(k,de,Pe,k-ye*4.9,de-_e*4.9,Pe-2.2),H.size.push(.75),H.opacity.push(q.review_status==="needs_review"?.38:.2)})}return{sectors:i,dim:o,lit:h,goals:E,seats:M,court:T,planets:I,moons:Y,guests:Z,seated:O,dust:H,etched:d,shapeLinesPlan:m,shapeLinesDeep:g}}const Dw="/assets/NotoSerifSC-subset-Cx3VUXg0.ttf",ur="/assets/IMing-subset-Kpo8eYZB.ttf",Uw="/assets/IMFellEnglish-subset-DL3qchp1.ttf",Ru=(n,e)=>Math.min(1,Math.max(0,(n-e)/.4));function bm(n,e){const t={plan:[],deep:[],size:[],opacity:[],core:[],ring:[],color:[],deepColor:[],filler:[],deepOpScale:[],deepSizeScale:[]};for(let i=0;i<n.filler.length;i++)n.filler[i]===1===e&&(t.plan.push(n.plan[i*3],n.plan[i*3+1],n.plan[i*3+2]),t.deep.push(n.deep[i*3],n.deep[i*3+1],n.deep[i*3+2]),t.size.push(n.size[i]),t.opacity.push(n.opacity[i]),t.core.push(n.core[i]),t.ring.push(n.ring[i]),t.color.push(n.color[i*3],n.color[i*3+1],n.color[i*3+2]),t.deepColor.push(n.deepColor[i*3],n.deepColor[i*3+1],n.deepColor[i*3+2]),t.filler.push(n.filler[i]),t.deepOpScale.push(n.deepOpScale[i]),t.deepSizeScale.push(n.deepSizeScale[i]));return t}class Lw{constructor(e,t,i,r={}){Ce(this,"root");Ce(this,"heart");Ce(this,"snapshot");Ce(this,"opts");Ce(this,"L");Ce(this,"renderer");Ce(this,"composer");Ce(this,"bloom");Ce(this,"fxPass");Ce(this,"scene",new vh);Ce(this,"camera");Ce(this,"chart",new Ds);Ce(this,"canvas");Ce(this,"bgStone");Ce(this,"bgDeep");Ce(this,"bgDusk");Ce(this,"vignette");Ce(this,"tooltip");Ce(this,"fadeMats",[]);Ce(this,"fadeFns",[]);Ce(this,"shapeLines",null);Ce(this,"asterLinks",null);Ce(this,"orbitRings",[]);Ce(this,"planetTrails",[]);Ce(this,"trailTimer",0);Ce(this,"coreLerp",[]);Ce(this,"labelObjs",[]);Ce(this,"morphables",[]);Ce(this,"reveal");Ce(this,"dimPts");Ce(this,"dimBgPts");Ce(this,"bgLayer",new Ds);Ce(this,"litPts");Ce(this,"goalPts");Ce(this,"northPts");Ce(this,"northVacant");Ce(this,"planetPts");Ce(this,"guestPts");Ce(this,"planetInnerPts");Ce(this,"moonPts");Ce(this,"guestTails");Ce(this,"glows",[]);Ce(this,"guestGlows",[]);Ce(this,"nebulae",[]);Ce(this,"dustRiver",[]);Ce(this,"tiered",[]);Ce(this,"colored",[]);Ce(this,"goalLabelGroups",[]);Ce(this,"selRing");Ce(this,"controls",null);Ce(this,"state",{t:0,density:1,bloom:1,w1:0,w2:.3,w3:.6,duskPos:.45,duskAmt:1,ch1:0,ch2:0,ch3:0});Ce(this,"tween",null);Ce(this,"hoverIdx",-1);Ce(this,"selectedIdx",-1);Ce(this,"hoverables",[]);Ce(this,"clickables",[]);Ce(this,"focusTween",null);Ce(this,"focusToken",0);Ce(this,"dragging",!1);Ce(this,"dragLastX",0);Ce(this,"dragLastT",0);Ce(this,"dragDist",0);Ce(this,"spinVel",0);Ce(this,"spinFactor",1);Ce(this,"lastPointerActive",-1e9);Ce(this,"clock",new Yv);Ce(this,"rafId",0);Ce(this,"disposed",!1);Ce(this,"resizeObserver",null);Ce(this,"labelsPending",0);Ce(this,"segPending",0);Ce(this,"labelGrpSeq",0);Ce(this,"collisionTick",0);Ce(this,"reducedMotion");Ce(this,"coarsePointer");Ce(this,"softGL");Ce(this,"camPlan",{pos:new $(0,4,346),look:new $(0,0,0)});Ce(this,"camDeep",{pos:new $(0,72,232),look:new $(0,-4,0)});Ce(this,"goalPeriods");Ce(this,"planetPeriods");Ce(this,"guestPeriods");Ce(this,"goalPhase");Ce(this,"planetPhase");Ce(this,"guestPhase");Ce(this,"goalDeepBase");Ce(this,"planetDeepBase");Ce(this,"guestDeepBase");Ce(this,"moonDeepBase");Ce(this,"moonPlanet",[]);Ce(this,"tailOffsets",[]);Ce(this,"guestBaseOpacity");Ce(this,"onPointerMoveWindow",e=>this.onPointerMove(e));Ce(this,"onPointerActive",()=>{this.lastPointerActive=performance.now()});Ce(this,"onClickWindow",e=>this.onClick(e));Ce(this,"onKeydown",e=>{e.key==="Escape"&&this.closeDetail()});Ce(this,"onWheel",(()=>{let e=0;return t=>{e+=t.deltaY,Math.abs(e)>260&&(this.goTo(e<0?1:0),e=0)}})());var x;this.root=e,this.heart=t,this.snapshot=i,this.opts=r,this.L=Pw(i),this.northVacant=!(((x=i.north)==null?void 0:x.is_set)??i.north_star.trim().length>0),this.reducedMotion=matchMedia("(prefers-reduced-motion: reduce)").matches,this.coarsePointer=matchMedia("(pointer: coarse)").matches,this.reveal=r.reveal??!1,this.state.t=r.initialState==="deepspace"?1:0;const s=y=>{const w=document.createElement("div");return w.className=y,this.root.appendChild(w),w};this.bgStone=s("starmap-bg"),this.bgDusk=s("starmap-bg"),this.bgDeep=s("starmap-bg"),this.vignette=s("starmap-vignette"),this.canvas=document.createElement("canvas"),this.canvas.className="starmap-canvas",this.heart.appendChild(this.canvas),this.tooltip=s("starmap-tooltip"),this.tooltip.style.display="none",this.renderer=new WM({canvas:this.canvas,antialias:!0,alpha:!0}),this.renderer.setClearColor(0,0),this.renderer.setPixelRatio(Math.min(window.devicePixelRatio,2)),this.camera=new Hn(45,1,1,2e3),this.fitPlanCamera(),this.scene.add(this.chart),this.chart.add(this.bgLayer),this.bakeBackgrounds(),this.buildLinework();const a=bm(this.L.dim,!1),o=bm(this.L.dim,!0);this.dimPts=this.makePoints(a),this.dimBgPts=this.makePoints(o,this.bgLayer);for(const y of[this.dimPts,this.dimBgPts])y.userData.filler=y===this.dimBgPts?o.filler:a.filler,y.userData.baseOpacity=new Float32Array(y.geometry.attributes.aOpacity.array),y.userData.baseSize=new Float32Array(y.geometry.attributes.aSize.array),y.userData.baseRing=new Float32Array(y.geometry.attributes.aRing.array);this.dimPts.userData.deepOpScale=new Float32Array(a.deepOpScale),this.dimPts.userData.deepSizeScale=new Float32Array(a.deepSizeScale),this.dimBgPts.userData.deepOpScale=new Float32Array(o.deepOpScale),this.dimBgPts.userData.deepSizeScale=new Float32Array(o.deepSizeScale),this.litPts=this.makePoints({plan:this.L.lit.plan,deep:this.L.lit.deep,size:this.L.lit.size,opacity:this.L.lit.opacity,core:this.L.lit.core,ring:this.L.lit.ring,color:this.L.lit.color,deepColor:this.L.lit.deepColor}),this.addTier(this.litPts,1.15,1);const l=[.949,.929,.878];this.goalPts=this.makePoints({plan:this.L.goals.flatMap(y=>y.plan),deep:this.L.goals.flatMap(y=>y.deep),size:this.L.goals.map(y=>y.status==="completed"?2.2:2.6),opacity:this.L.goals.map(y=>y.status==="completed"?.3:y.status==="paused"?.55:1),core:this.L.goals.map(y=>y.status==="completed"?0:1),ring:this.L.goals.map(()=>1),color:this.L.goals.flatMap(y=>y.status==="completed"?l:[.91,.72,.36]),deepColor:this.L.goals.flatMap(y=>y.status==="completed"?[...$t.moonWhite]:[.95,.76,.34])}),this.addTier(this.goalPts,1.18,1);const c=this.makePoints({plan:this.L.court.plan,deep:this.L.court.plan.map((y,w)=>w%3===2?y||0:y*1.6),size:this.L.court.size,opacity:this.L.court.gold.map(y=>y?1:.85),core:this.L.court.gold.map(()=>1),ring:this.L.court.gold.map(()=>0),color:this.L.court.gold.flatMap(y=>y?[.91,.72,.36]:[.961,.918,.824])});this.northPts=this.makePoints(this.northVacant?{plan:[0,0,0],deep:[0,0,0],size:[4.4],opacity:[.3],core:[0],ring:[1],color:l}:{plan:[0,0,0],deep:[0,0,0],size:[4.4],opacity:[1],core:[1],ring:[0],color:[.98,.85,.55],deepColor:[...$t.warmGold]}),this.northVacant||this.addTier(this.northPts,1.35,1),this.planetPts=this.makePoints({plan:this.L.planets.flatMap(y=>y.plan),deep:this.L.planets.flatMap(y=>y.deep),size:this.L.planets.map(()=>3),opacity:this.L.planets.map(y=>y.status==="active"?.9:.35),core:this.L.planets.map(()=>.4),ring:this.L.planets.map(()=>1),color:this.L.planets.flatMap(()=>[.961,.918,.824]),deepColor:this.L.planets.flatMap(()=>[...$t.softOrange])}),this.addTier(this.planetPts,.6,.85),this.moonPts=this.makePoints({plan:this.L.moons.plan,deep:this.L.moons.deep,size:this.L.moons.size,opacity:this.L.moons.opacity,core:this.L.moons.size.map(()=>1),ring:this.L.moons.size.map(()=>0),color:this.L.moons.size.flatMap(()=>[.961,.918,.824]),deepColor:this.L.moons.size.flatMap(()=>[...$t.moonWhite])}),this.addTier(this.moonPts,.9,1);const u=this.makePoints({plan:this.L.seated.plan,deep:this.L.seated.deep,size:this.L.seated.size,opacity:this.L.seated.opacity,core:this.L.seated.size.map(()=>1),ring:this.L.seated.size.map(()=>0),color:this.L.seated.size.flatMap(()=>[.961,.918,.824]),deepColor:this.L.seated.size.flatMap(()=>[...$t.moonWhite])});this.addTier(u,.9,1),this.guestPts=this.makePoints({plan:this.L.guests.flatMap(y=>y.plan),deep:this.L.guests.flatMap(y=>y.deep),size:this.L.guests.map(()=>1.15),opacity:this.L.guests.map(()=>.95),core:this.L.guests.map(()=>1),ring:this.L.guests.map(()=>0),color:this.L.guests.flatMap(()=>[1,.95,.85]),deepColor:this.L.guests.flatMap(()=>[...$t.blueWhite])}),this.addTier(this.guestPts,.95,null);const f=this.makePoints({plan:this.L.dust.plan,deep:this.L.dust.deep,size:this.L.dust.size,opacity:this.L.dust.opacity,core:this.L.dust.size.map(()=>1),ring:this.L.dust.size.map(()=>0),color:this.L.dust.size.flatMap(()=>[.961,.918,.824]),deepColor:this.L.dust.size.flatMap(()=>[.88,.9,.94])});this.addTier(f,.8,1);const h=this.makePoints({plan:this.L.etched.plan,deep:this.L.etched.deep,size:this.L.etched.size,opacity:this.L.etched.opacity,core:this.L.etched.size.map(()=>0),ring:this.L.etched.size.map(()=>1),color:this.L.etched.color,deepColor:this.L.etched.deepColor.slice(),deepCore:this.L.etched.size.map(()=>.85)});this.addTier(h,1.05,1.8);const d=(()=>{const y=new Rt;y.setAttribute("position",new Nt(new Float32Array(this.L.dust.trailPlan),3));const w=new or(y,this.lineMat(kn,.26,.22,3));this.chart.add(w);const C=w;return C.userData.plan=new Float32Array(this.L.dust.trailPlan),C.userData.deep=new Float32Array(this.L.dust.trailDeep),C})();if(this.planetInnerPts=this.makePoints({plan:this.L.planets.flatMap(y=>y.plan),deep:this.L.planets.flatMap(y=>y.deep),size:this.L.planets.map(()=>2),opacity:this.L.planets.map(y=>y.status==="active"?.9:.35),core:this.L.planets.map(()=>0),ring:this.L.planets.map(()=>1),color:this.L.planets.flatMap(()=>[.961,.918,.824]),deepColor:this.L.planets.flatMap(()=>[...$t.softOrange])}),this.addTier(this.planetInnerPts,.6,.85),this.L.shapeLinesPlan.length){const y=new Rt;y.setAttribute("position",new Nt(new Float32Array(this.L.shapeLinesPlan),3));const w=new Cs({color:kn,transparent:!0,opacity:.14,depthWrite:!1}),C=new or(y,w);this.chart.add(C),this.shapeLines=C,this.shapeLines.userData.plan=new Float32Array(this.L.shapeLinesPlan),this.shapeLines.userData.deep=new Float32Array(this.L.shapeLinesDeep),this.fadeFns.push({mat:w,fn:(R,L,U)=>.14*(1-R)+.05*U})}{const y=ei(6600);for(const w of this.L.planets){if(w.goalIndex<0)continue;const C=this.L.goals[w.goalIndex],R=Math.hypot(w.deep[0]-C.deep[0],w.deep[1]-C.deep[1]),L=new Cs({color:Au,transparent:!0,opacity:0,depthWrite:!1}),U=new Nc(new Rt().setFromPoints(this.circlePoints(R,72)),L);this.chart.add(U);const I=new Cs({color:_m,transparent:!0,opacity:0,depthWrite:!1}),F=[];for(let Y=0;Y<=10;Y++){const j=Y/10*(Math.PI*2)*.045;F.push(new $(R*Math.cos(j),R*Math.sin(j),0))}const N=new xl(new Rt().setFromPoints(F),I);U.add(N),this.orbitRings.push({ring:U,ringMat:L,flow:N,flowMat:I,goalIdx:w.goalIndex,phase:y()*Math.PI*2,shimmer:y()*Math.PI*2})}}{const y=[];for(const w of this.L.planets){if(w.goalIndex<0)continue;const C=this.L.goals[w.goalIndex];y.push(new $(w.plan[0],w.plan[1],0)),y.push(new $(C.plan[0],C.plan[1],0))}this.chart.add(new or(new Rt().setFromPoints(y),this.lineMat(kn,.22,0,1)))}{const y=[];for(const w of this.L.planets){if(w.progress===null||w.progress===void 0||w.progress<=0)continue;const C=32,R=4.6;for(let L=0;L<C;L++){const U=Math.PI/2-L/C*w.progress*Math.PI*2,I=Math.PI/2-(L+1)/C*w.progress*Math.PI*2;y.push(new $(w.plan[0]+R*Math.cos(U),w.plan[1]+R*Math.sin(U),0)),y.push(new $(w.plan[0]+R*Math.cos(I),w.plan[1]+R*Math.sin(I),0))}}y.length&&this.chart.add(new or(new Rt().setFromPoints(y),this.lineMat(Au,.55,0,1)))}this.guestTails=(()=>{const y=[],w=[];for(const L of this.L.guests){const U=L.tailDir*Math.PI/180,I=Math.cos(U),F=Math.sin(U),N=-F,Y=I,j=5;for(let Z=0;Z<j;Z++)for(const O of[Z/j,(Z+1)/j]){const H=Math.sin(O*2.5)*1.1;y.push(L.plan[0]-I*L.tailLen*O+N*H,L.plan[1]-F*L.tailLen*O+Y*H,0),w.push(L.deep[0]-I*L.tailLen*1.3*O+N*H,L.deep[1]-F*L.tailLen*1.3*O+Y*H,L.deep[2])}}const C=new Rt;C.setAttribute("position",new Nt(new Float32Array(y),3));const R=new or(C,this.lineMat(kn,.55,.4,3));return this.chart.add(R),R})();{const y=this.guestTails;y.userData.plan=new Float32Array(y.geometry.attributes.position.array),y.userData.deep=new Float32Array(this.L.guests.flatMap(w=>{const C=w.tailDir*Math.PI/180,R=Math.cos(C),L=Math.sin(C),U=-L,I=R,F=[],N=5;for(let Y=0;Y<N;Y++)for(const j of[Y/N,(Y+1)/N]){const Z=Math.sin(j*2.5)*1.1;F.push(w.deep[0]-R*w.tailLen*1.3*j+U*Z,w.deep[1]-L*w.tailLen*1.3*j+I*Z,w.deep[2])}return F}))}const m=this.makeGlowTexture(),g=(y,w,C,R)=>{const L=new Ca({map:m,color:C,transparent:!0,opacity:0,blending:ll,depthWrite:!1}),U=new bo(L);return U.scale.set(w,w,1),this.chart.add(U),this.glows.push({spr:U,mat:L,getPos:y,maxOpacity:R}),U};g(()=>[0,0,0],20,16767370,this.northVacant?0:.8),g(()=>[0,0,0],40,9873628,this.northVacant?0:.1),this.L.goals.forEach((y,w)=>g(()=>{const C=this.goalPts.geometry.attributes.position.array;return[C[w*3],C[w*3+1],C[w*3+2]]},9,16764280,y.status==="completed"?0:y.status==="paused"?.12:.35)),this.guestGlows=this.L.guests.map((y,w)=>{const C=new Ca({map:m,color:14543103,transparent:!0,opacity:0,blending:ll,depthWrite:!1}),R=new bo(C);return R.scale.set(5.5,5.5,1),this.chart.add(R),{spr:R,mat:C,idx:w,breathe:y.review==="needs_review"}});{const y=this.L.dust.deep.length/3;if(y>0){const w=ei(7700),C=Math.max(6,Math.min(26,Math.round(y*.6))),R=Math.min(1,y/24);for(let L=0;L<C;L++){const U=C<=1?0:L/(C-1),I=Math.min(y-1,Math.floor(U*y)),F=new Ca({map:m,color:9410989,transparent:!0,opacity:0,depthWrite:!1}),N=new bo(F),Y=30+w()*26;N.scale.set(Y,Y,1),N.position.set(this.L.dust.deep[I*3],this.L.dust.deep[I*3+1],this.L.dust.deep[I*3+2]-4),N.visible=!1,N.renderOrder=-1,this.chart.add(N);const j=Math.hypot(this.L.dust.deep[I*3],this.L.dust.deep[I*3+1]),Z=Math.min(1.15,Math.max(.3,1.25-j/240));this.dustRiver.push({spr:N,mat:F,base:.06*R*Z*(.7+w()*.6)})}}}for(const[y,w,C,R,L,U]of[[150,70,-120,260,8017464,.13],[-170,-60,-100,300,6119536,.1],[0,120,-140,200,4608634,.085]]){const I=new Ca({map:m,color:L,transparent:!0,opacity:0,depthWrite:!1}),F=new bo(I);F.position.set(y,w,C),F.scale.set(R,R,1),F.visible=!1,this.scene.add(F),this.nebulae.push({mat:I,op:U,spr:F})}this.buildLabels();const p=this.renderer.getContext(),_=p.getExtension("WEBGL_debug_renderer_info"),v=_?String(p.getParameter(_.UNMASKED_RENDERER_WEBGL)):"";this.softGL=/swiftshader|llvmpipe|software/i.test(v),this.composer=new AT(this.renderer),this.composer.addPass(new AE(this.scene,this.camera)),this.bloom=new wE({luminanceThreshold:.65,intensity:0,mipmapBlur:!0}),this.fxPass=new UE(this.camera,this.bloom),this.composer.addPass(this.fxPass),this.composer.setSize(this.heart.clientWidth||1600,this.heart.clientHeight||900),this.morphables=[this.dimPts,this.dimBgPts,this.litPts,this.goalPts,c,this.northPts,this.planetPts,this.planetInnerPts,this.moonPts,u,this.guestPts,f,h,this.guestTails,d],this.shapeLines&&this.morphables.push(this.shapeLines),this.asterLinks&&this.morphables.push(this.asterLinks);for(const y of[this.goalPts,this.planetPts,this.planetInnerPts,this.moonPts,this.guestPts,this.guestTails])y.userData.orbitManaged=!0;const b=this.L.seats.filter(y=>y.goalIndex===null);if(b.length){const y=b.flatMap(C=>{const R=C.angle*Math.PI/180;return[fr*Math.cos(R),fr*Math.sin(R),0]}),w=this.makePoints({plan:y,deep:y.slice(),size:b.map(()=>2),opacity:b.map(()=>.16),core:b.map(()=>0),ring:b.map(()=>1),color:b.flatMap(()=>[.961,.918,.824])});this.morphables.push(w)}this.goalPeriods=this.L.goals.map((y,w)=>150+w*36),this.planetPeriods=this.L.planets.map((y,w)=>100+w*14),this.guestPeriods=this.L.guests.map((y,w)=>26+w*6.5),this.goalPhase=this.L.goals.map(()=>0),this.planetPhase=this.L.planets.map(()=>0),this.guestPhase=this.L.guests.map(()=>0),this.guestDeepBase=this.L.guests.map(y=>y.deep.slice()),this.planetDeepBase=this.L.planets.map(y=>y.deep.slice()),this.goalDeepBase=this.L.goals.map(y=>y.deep.slice()),this.L.planets.forEach((y,w)=>{for(let C=0;C<Math.min(y.taskCount,5);C++)this.moonPlanet.push(w)}),this.moonDeepBase=[];for(let y=0;y<this.L.moons.deep.length;y+=3)this.moonDeepBase.push(this.L.moons.deep.slice(y,y+3));const S=this.guestTails;this.L.guests.forEach((y,w)=>{const C=[];for(let R=0;R<10;R++){const L=(w*10+R)*3;C.push([S.userData.deep[L]-y.deep[0],S.userData.deep[L+1]-y.deep[1],S.userData.deep[L+2]-y.deep[2]])}this.tailOffsets.push(C)});const E=(y,w)=>{const C=y.geometry.attributes.position.array;return[C[w*3],C[w*3+1],C[w*3+2]]};this.hoverables=[{title:"北极星",info:this.northVacant?"虚位 · 点击立星":i.north_star.split(/[，。]/)[0],pos:()=>[0,0,0]},...this.L.goals.map((y,w)=>({title:y.title,info:y.status==="completed"?"刻痕星 · 已镌刻":y.status==="paused"?"目标恒星 · 暂停":"目标恒星",pos:()=>E(this.goalPts,w)})),...this.L.planets.map((y,w)=>({title:y.title,info:`${y.status==="active"?"行星 · 在轨":"行星 · 归档"} · 任务 ${y.taskCount}`+(y.progress!==null&&y.progress!==void 0?` · 进度 ${Math.round(y.progress*100)}%`:""),pos:()=>E(this.planetPts,w)})),...this.L.guests.map((y,w)=>({title:y.title,info:`客星 · ${y.date} · ${y.strength}${y.review==="needs_review"?" · 待评审":""}`,pos:()=>E(this.guestPts,w)}))],this.clickables=[{kind:"north",id:"north",idx:-1,title:"北极星",pos:()=>[0,0,0]},...this.L.goals.map((y,w)=>({kind:"goal",id:y.id,idx:w,title:y.title,pos:()=>E(this.goalPts,w)})),...this.L.planets.map((y,w)=>({kind:"planet",id:y.id,idx:w,title:y.title,pos:()=>E(this.planetPts,w)})),...this.L.guests.map((y,w)=>({kind:"guest",id:y.id,idx:w,title:y.title,pos:()=>E(this.guestPts,w)})),...this.L.lit.skills.map((y,w)=>({kind:"skill",id:y.id,idx:w,title:y.label,pos:()=>E(this.litPts,w)}))],this.selRing=new Nc(new Rt().setFromPoints(this.circlePoints(3.2,48)),new Cs({color:_m,transparent:!0,opacity:.8,depthWrite:!1})),this.selRing.visible=!1,this.chart.add(this.selRing);const M=new ResizeObserver(()=>this.onResize());M.observe(this.heart),this.resizeObserver=M,window.addEventListener("pointermove",this.onPointerMoveWindow,{passive:!0}),window.addEventListener("pointermove",this.onPointerActive,{passive:!0}),window.addEventListener("click",this.onClickWindow),window.addEventListener("keydown",this.onKeydown),window.addEventListener("wheel",this.onWheel,{passive:!0}),this.canvas.addEventListener("pointerdown",y=>{var w;this.focusToken+=1,(w=this.focusTween)==null||w.kill(),this.focusTween=null,!(this.coarsePointer||this.state.t>=.5)&&(this.dragging=!0,this.dragLastX=y.clientX,this.dragLastT=performance.now(),this.dragDist=0,this.spinVel=0,this.canvas.setPointerCapture(y.pointerId))}),this.canvas.addEventListener("pointermove",y=>{if(!this.dragging)return;const w=performance.now(),C=y.clientX-this.dragLastX,R=Math.max((w-this.dragLastT)/1e3,.008);this.dragLastX=y.clientX,this.dragLastT=w,this.dragDist+=Math.abs(C);const L=C*.004;this.chart.rotation.z+=L,this.spinVel=this.spinVel*.75+L/R*.25});const T=()=>{this.dragging=!1};this.canvas.addEventListener("pointerup",T),this.canvas.addEventListener("pointercancel",T),this.coarsePointer&&(this.controls=new GS(this.camera,this.canvas),this.controls.enableRotate=!1,this.controls.enableDamping=!0,this.controls.dampingFactor=.08,this.controls.enableZoom=!0,this.controls.zoomSpeed=.9,this.controls.enablePan=!0,this.controls.panSpeed=.8),this.guestBaseOpacity=new Float32Array(this.guestPts.geometry.attributes.aOpacity.array),this.onResize(),this.applyMorph(),r.initialState==="deepspace"&&this.goTo(1,!0),this.loop()}goTo(e,t=!1){var i;if(this.tween&&this.tween.kill(),this.focusToken+=1,(i=this.focusTween)==null||i.kill(),this.focusTween=null,this.closeDetail(),t||this.reducedMotion){this.state.t=e,this.applyMorph();return}this.tween=ol.to(this.state,{t:e,duration:2.4,ease:"power2.inOut",onUpdate:()=>this.applyMorph()})}focusStar(e){var s;const t=this.clickables.findIndex(a=>a.id===e);if(t<0||this.disposed)return!1;this.lastPointerActive=performance.now();const i=++this.focusToken;(s=this.focusTween)==null||s.kill(),this.focusTween=null;const r=()=>{i!==this.focusToken||this.disposed||this.runFocus(t,i)};return this.state.t>.5?(this.tween&&this.tween.kill(),this.closeDetail(),this.reducedMotion?(this.state.t=0,this.applyMorph(),r(),!0):(this.tween=ol.to(this.state,{t:0,duration:2.4,ease:"power2.inOut",onUpdate:()=>this.applyMorph(),onComplete:r}),!0)):(r(),!0)}runFocus(e,t){const i=this.clickables[e],r=()=>{t===this.focusToken&&!this.disposed&&this.openDetail(e)},s=i.pos();if(Math.hypot(s[0],s[1])<1){r();return}let l=90-(Math.atan2(s[1],s[0])*180/Math.PI+this.chart.rotation.z*180/Math.PI);l=(l+540)%360-180;const c=this.chart.rotation.z+l*Math.PI/180;if(this.reducedMotion){this.chart.rotation.z=c,r();return}this.focusTween=ol.to(this.chart.rotation,{z:c,duration:1.1,ease:"power2.inOut",onComplete:r})}toggle(){this.goTo(this.state.t>.5?0:1)}setReveal(e){if(!(e===this.reveal||this.disposed)){this.reveal=e;for(const{t}of this.labelObjs)this.chart.remove(t),t.dispose();this.labelObjs=[],this.goalLabelGroups=[],this.buildLabels(),this.applyMorph()}}deselect(){this.closeDetail()}dispose(){var e,t,i;this.disposed=!0,(e=this.resizeObserver)==null||e.disconnect(),cancelAnimationFrame(this.rafId),this.tween&&this.tween.kill(),(t=this.focusTween)==null||t.kill(),window.removeEventListener("pointermove",this.onPointerMoveWindow),window.removeEventListener("pointermove",this.onPointerActive),window.removeEventListener("click",this.onClickWindow),window.removeEventListener("keydown",this.onKeydown),window.removeEventListener("wheel",this.onWheel),(i=this.controls)==null||i.dispose(),this.scene.traverse(r=>{const s=r;s.geometry&&s.geometry.dispose();const a=s.material;Array.isArray(a)?a.forEach(o=>o.dispose()):a==null||a.dispose()}),this.composer.dispose(),this.renderer.dispose();for(const r of[this.bgStone,this.bgDeep,this.bgDusk,this.vignette,this.tooltip])r.remove();this.canvas.remove()}fitPlanCamera(){const e=this.heart.clientWidth||1600,t=this.heart.clientHeight||900,i=Math.tan(this.camera.fov*Math.PI/360);this.camPlan.pos.z=(qo+16)/(i*Math.min(1,e/t))}bakeBackgrounds(){const e=Cf("rgb"),t=(a,o,l)=>{const c=e(xw([a,o],"oklch")(l));return[Math.round(c.r*255),Math.round(c.g*255),Math.round(c.b*255)]},i=t("#1c2c4e","#10172c",.4),r=t("#182642","#0d1322",.4),s=a=>{const c=document.createElement("canvas");c.width=1024,c.height=640;const u=c.getContext("2d"),f=a==="stone",h=a==="dusk",d=f?[37,64,94]:h?i:[36,44,62],m=f?[29,52,80]:h?r:[26,31,46],g=u.createLinearGradient(0,0,0,640);g.addColorStop(0,`rgb(${d.join(",")})`),g.addColorStop(1,`rgb(${m.join(",")})`),u.fillStyle=g,u.fillRect(0,0,1024,640);const p=ei(f?41:h?43:42);for(let S=0;S<9;S++){const E=p()*1024,M=p()*640,T=120+p()*260,x=p()>.5,y=(f?.05:h?.04:.035)*(.7+p()*.6),w=u.createRadialGradient(E,M,0,E,M,T);w.addColorStop(0,x?`rgba(70,98,132,${y})`:`rgba(10,20,36,${y})`),w.addColorStop(1,"rgba(0,0,0,0)"),u.fillStyle=w,u.fillRect(E-T,M-T,T*2,T*2)}if(h){const S=u.createRadialGradient(512,396.8,0,512,396.8,348.16);S.addColorStop(0,"rgba(196,138,64,0.13)"),S.addColorStop(.55,"rgba(150,100,52,0.05)"),S.addColorStop(1,"rgba(150,100,52,0)"),u.fillStyle=S,u.fillRect(0,0,1024,640)}const _=u.getImageData(0,0,1024,640),v=f?.028:h?.04:.05,b=f?.045:h?.032:.02;for(let S=0;S<640;S++){const E=S/640;for(let M=0;M<1024;M++){const T=M/1024,x=Math.exp(-Math.pow((T*.82+E*.57-.78)*5,2))*v,y=(p()-.5)*b,w=(S*1024+M)*4,C=(x+y)*255;_.data[w]=Math.max(0,Math.min(255,_.data[w]+C*.9)),_.data[w+1]=Math.max(0,Math.min(255,_.data[w+1]+C*.88)),_.data[w+2]=Math.max(0,Math.min(255,_.data[w+2]+C*.82))}}return u.putImageData(_,0,0),c};this.bgStone.style.backgroundImage=`url(${s("stone").toDataURL("image/png")})`,this.bgDusk.style.backgroundImage=`url(${s("dusk").toDataURL("image/png")})`,this.bgDusk.style.opacity="0",this.bgDeep.style.backgroundImage=`url(${s("deep").toDataURL("image/png")})`,this.bgDeep.style.opacity="0"}applyBackground(e,t){e<=t?(this.bgDusk.style.opacity=String(e/t),this.bgDeep.style.opacity="0"):(this.bgDusk.style.opacity="1",this.bgDeep.style.opacity=String((e-t)/(1-t)))}lineMat(e,t,i,r=1){const s=new Cs({color:e,transparent:!0,opacity:t,depthWrite:!1});return this.fadeMats.push({mat:s,plan:t,deep:i,ch:r}),s}circlePoints(e,t=160){const i=[];for(let r=0;r<=t;r++){const s=r/t*Math.PI*2;i.push(new $(e*Math.cos(s),e*Math.sin(s),0))}return i}buildLinework(){const e=this.L,t=this.lineMat(kn,.42,0,1),i=this.lineMat(kn,.55,0,1),r=this.lineMat(kn,.18,0,1),s=this.lineMat(kn,.08,0,1),a=this.lineMat(kn,.5,0,1),o=this.lineMat(kn,.52,.12,2),l=this.lineMat(kn,.35,0,1),c=(d,m,g=!1)=>{const p=new Rt().setFromPoints(d),_=g?new Nc(p,m):new xl(p,m);return this.chart.add(_),_},u=ei(53),f=(d,m,g,p)=>{const _=[];for(let v=0;v<=4;v++){const b=d+(m-d)*v/4,E=(g+(v>0&&v<4?(u()-.5)*1.4:0))*Math.PI/180;_.push(new $(b*Math.cos(E),b*Math.sin(E),0))}c(_,p)};for(const[d,m]of[[fr,t],[Mw,t],[At,i],[Eu,a],[qo,a]])c(this.circlePoints(d),m,!0);{const d=[];for(let m=18;m<=342;m+=2){const g=m*Math.PI/180;d.push(new $(Ia*Math.cos(g),Ia*Math.sin(g),0))}c(d,t)}{const d=[];for(let g=0;g<360;g+=6){const p=g*Math.PI/180,_=At+(g%30===0?3.25:1.5);d.push(new $(At*Math.cos(p),At*Math.sin(p),0)),d.push(new $(_*Math.cos(p),_*Math.sin(p),0))}const m=new Rt().setFromPoints(d);this.chart.add(new or(m,i))}const h=d=>(d=d%360,d>180&&(d-=360),d<-180&&(d+=360),d);for(const d of e.sectors){Math.abs(h(d.start))>=12&&f(Ia,At,d.start,r);const m=Math.max(1,Math.round(d.count/6)),g=[];for(let _=1;_<m;_++)g.push(_/m+(u()-.5)*.5/m);g.sort();for(const _ of g){const v=d.start+d.width*_;Math.abs(h(v))>=12&&f(Ia,At,v,s)}const p=d.start*Math.PI/180;c([new $(Eu*Math.cos(p),Eu*Math.sin(p),0),new $(qo*Math.cos(p),qo*Math.sin(p),0)],a)}{const d=[],m=[],g=e.lit.plan,p=e.lit.deep;for(let b=0;b<e.lit.links.length;b+=2){const S=e.lit.links[b]*3,E=e.lit.links[b+1]*3;d.push(new $(g[S],g[S+1],0)),d.push(new $(g[E],g[E+1],0)),m.push(p[S],p[S+1],p[S+2],p[E],p[E+1],p[E+2])}const _=new Rt().setFromPoints(d),v=new or(_,o);this.chart.add(v),this.asterLinks=v,this.asterLinks.userData.plan=new Float32Array(d.flatMap(b=>[b.x,b.y,b.z])),this.asterLinks.userData.deep=new Float32Array(m)}{const d=[],m=e.court.plan;for(const[p,_]of e.court.links)d.push(new $(m[p*3],m[p*3+1],0)),d.push(new $(m[_*3],m[_*3+1],0));const g=new Rt().setFromPoints(d);this.chart.add(new or(g,l))}c(this.circlePoints(4.2,64),this.lineMat(kn,.55,0,1),!0)}makePoints(e,t){const{plan:i,deep:r,size:s,opacity:a,core:o,ring:l,color:c}=e,u=new Rt;u.setAttribute("position",new Nt(new Float32Array(i),3)),u.setAttribute("aSize",new Nt(new Float32Array(s),1)),u.setAttribute("aOpacity",new Nt(new Float32Array(a),1)),u.setAttribute("aCore",new Nt(new Float32Array(o),1)),u.setAttribute("aRing",new Nt(new Float32Array(l),1)),u.setAttribute("aColor",new Nt(new Float32Array(c),3));const f=new ln({transparent:!0,depthWrite:!1,blending:Vr,uniforms:{uScale:{value:1},uGlobal:{value:1}},vertexShader:`
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
      `}),h=new Ov(u,f);return h.userData.plan=new Float32Array(i),h.userData.deep=new Float32Array(r),e.deepColor&&this.colored.push({pts:h,plan:new Float32Array(c),deep:new Float32Array(e.deepColor)}),e.deepCore&&this.coreLerp.push({pts:h,plan:new Float32Array(o),deep:new Float32Array(e.deepCore)}),(t??this.chart).add(h),h}addTier(e,t,i){this.tiered.push({pts:e,baseSize:new Float32Array(e.geometry.attributes.aSize.array),baseOp:i===null?null:new Float32Array(e.geometry.attributes.aOpacity.array),ds:t,dop:i??1})}makeGlowTexture(){const e=document.createElement("canvas");e.width=e.height=128;const t=e.getContext("2d"),i=t.createRadialGradient(64,64,0,64,64,64);return i.addColorStop(0,"rgba(255,255,255,1)"),i.addColorStop(.25,"rgba(255,255,255,0.35)"),i.addColorStop(1,"rgba(255,255,255,0)"),t.fillStyle=i,t.fillRect(0,0,128,128),new Bv(e)}addLabel(e,t={}){const{size:i=3.4,color:r=kn,font:s=Dw,pos:a=[0,0,0],deepPos:o=null,rotZ:l=0,anchorX:c="center",fade:u="band",prio:f=2}=t,h=new wh;return h.text=e,h.font=s,h.fontSize=i,h.color=r,h.anchorX=c,h.anchorY="middle",h.position.set(a[0],a[1],a[2]??0),h.rotation.z=l,h.material.transparent=!0,h.outlineWidth="5%",h.outlineColor=726566,h.outlineOpacity=.85,this.chart.add(h),this.labelObjs.push({t:h,fade:u,planPos:a.slice(),deepPos:o?o.slice():null,rotZ:l,prio:f,grpId:this.labelGrpSeq++,ca:1,caTarget:1}),h}addSegmentedLabel(e,t){const{size:i=3.6,color:r=15652502,pos:s,align:a="left",fade:o="goal",goalIdx:l=-1,prio:c=1}=t,u=this.labelGrpSeq++,f=e.split(/([A-Za-z0-9.]+)/).filter(Boolean),h={goalIdx:l,segs:[],base:[],anchor:s.slice()},d=f.map(g=>{const p=/^[A-Za-z0-9.]+$/.test(g),_=new wh;return _.text=g,_.font=p?Uw:ur,_.fontSize=i,_.color=r,_.anchorX="left",_.anchorY="middle",_.material.transparent=!0,_.outlineWidth="5%",_.outlineColor=726566,_.outlineOpacity=.85,this.chart.add(_),this.labelObjs.push({t:_,fade:o,planPos:s.slice(),deepPos:null,rotZ:0,prio:c,grpId:u,ca:1,caTarget:1}),h.segs.push(_),_});l>=0&&this.goalLabelGroups.push(h),this.segPending+=d.length;let m=d.length;d.forEach(g=>g.sync(()=>{if(this.segPending-=1,m-=1,m===0){const p=d.map(b=>{const S=b.textRenderInfo&&b.textRenderInfo.blockBounds;return S?Math.max(.1,S[2]-S[0]):b.text.length*i*.6}),_=p.reduce((b,S)=>b+S,0)+.4*(d.length-1);let v=s[0]-(a==="right"?_:a==="center"?_/2:0);d.forEach((b,S)=>{b.position.set(v,s[1],0),v+=p[S]+.4}),h.base=d.map(b=>[b.position.x,b.position.y])}}))}followGoal(e,t){this.goalLabelGroups.push({goalIdx:e,segs:t,base:t.map(i=>[i.position.x,i.position.y]),anchor:[]})}buildLabels(){const e=this.L;for(const t of e.sectors){const i=t.start+t.width/2,r=Array.from(this.reveal?t.name:t.asterism),s=this.reveal?Au:11907232,a=3.2*1.25/wu*(180/Math.PI),o=i-a*(r.length-1)/2;r.forEach((l,c)=>{const u=(o+c*a)*Math.PI/180;this.addLabel(l,{size:3.2,color:s,font:ur,fade:"band",pos:[wu*Math.cos(u),wu*Math.sin(u),0],rotZ:u+Math.PI/2})})}e.goals.forEach((t,i)=>{const r=Math.cos(t.angle*Math.PI/180),s=r>.35?"left":r<-.35?"right":"center",a=fr+8,o=t.angle*Math.PI/180,l=a*Math.cos(o)+(s==="left"?1:s==="right"?-1:0),c=a*Math.sin(o);if(t.status==="completed"){this.addSegmentedLabel(t.title,{size:3.6,color:10130038,align:s,goalIdx:i,pos:[l,c,0]});return}if(!this.reveal){const u=this.addLabel(t.seatName??t.title,{size:3.8,color:15652502,font:ur,fade:"goal",pos:[l,c,0]});this.followGoal(i,[u]);return}this.addSegmentedLabel(t.title,{size:3.6,color:15652502,align:s,goalIdx:i,pos:[l,c,0]})});for(const t of e.seats){if(t.goalIndex!==null)continue;const i=t.angle*Math.PI/180,r=fr+8;this.addLabel(`${t.name}·虚位`,{size:2.8,color:9274994,font:ur,fade:"goal",pos:[r*Math.cos(i),r*Math.sin(i),0]})}if(this.northVacant)this.addLabel("虚位",{size:3.8,color:9274994,font:ur,anchorX:"left",pos:[6.5,.4,0],deepPos:[10.5,-10.6,0],fade:"north",prio:0});else if(!this.reveal)this.addLabel("北极星",{size:3.8,color:15652502,font:ur,anchorX:"left",pos:[6.5,.4,0],deepPos:[10.5,-10.6,0],fade:"north",prio:0});else{const t=this.snapshot.north_star.split(/[，。]/)[0],i=t.indexOf("成为"),r=i>0?[t.slice(0,i+2),t.slice(i+2)]:[t,""];this.addLabel(r[0],{size:3.8,color:15652502,font:ur,anchorX:"left",pos:[6.5,3.4,0],deepPos:[10.5,-8.5,0],fade:"north",prio:0}),r[1]&&this.addLabel(r[1],{size:3.8,color:15652502,font:ur,anchorX:"left",pos:[6.5,-2.6,0],deepPos:[10.5,-13.6,0],fade:"north",prio:0})}this.labelsPending=this.labelObjs.length;for(const{t}of this.labelObjs)t.sync(()=>{this.labelsPending-=1})}applyMorph(){var c,u;const e=this.state.t,t=Ru(e,this.state.w1),i=Ru(e,this.state.w2),r=Ru(e,this.state.w3);this.state.ch1=t,this.state.ch2=i,this.state.ch3=r;for(const f of this.morphables){if(f.userData.orbitManaged)continue;const h=f.geometry.attributes.position,d=f.userData.plan,m=f.userData.deep,g=h.array;for(let p=0;p<g.length;p++)g[p]=d[p]+(m[p]-d[p])*i;h.needsUpdate=!0}this.chart.rotation.x=-1.05*i,this.camera.position.lerpVectors(this.camPlan.pos,this.camDeep.pos,i),this.camera.lookAt(new $().lerpVectors(this.camPlan.look,this.camDeep.look,i));for(const{mat:f,plan:h,deep:d,ch:m}of this.fadeMats){const g=m===1?t:m===3?r:i;f.opacity=h+(d-h)*g}for(const{mat:f,fn:h}of this.fadeFns)f.opacity=h(t,i,r);for(const{t:f,fade:h,planPos:d,deepPos:m}of this.labelObjs)h==="band"?(f.material.opacity=1-i,f.visible=i<.98):h==="north"&&m&&(f.material.opacity=1-.25*i,f.position.set(d[0]+(m[0]-d[0])*i,d[1]+(m[1]-d[1])*i,0));for(const f of this.glows){f.mat.opacity=f.maxOpacity*r,f.spr.visible=f.mat.opacity>.004;const h=f.getPos();f.spr.position.set(h[0],h[1],h[2])}for(const f of this.nebulae)f.mat.opacity=f.op*r,f.spr.visible=f.mat.opacity>.004;const s=Math.exp(-Math.pow((i-this.state.duskPos)/.13,2))*this.state.duskAmt,a=this.glows[0];if(s>.01){a.mat.opacity=Math.min(1,Math.max(a.mat.opacity,a.maxOpacity*s*.6)),a.spr.visible=!0;const f=20*(1+.55*s);a.spr.scale.set(f,f,1)}else a.spr.scale.set(20,20,1);for(const f of[this.dimPts,this.dimBgPts]){const h=f.geometry.attributes.aOpacity,d=f.geometry.attributes.aSize,m=f.geometry.attributes.aRing,g=f.userData.baseOpacity,p=f.userData.baseSize,_=f.userData.baseRing,v=f.userData.deepOpScale,b=f.userData.deepSizeScale,S=f.userData.filler;for(let E=0;E<h.array.length;E++){const M=S[E]?this.state.density:1;h.array[E]=g[E]*M*(1+(v[E]-1)*r),d.array[E]=p[E]*(1+(b[E]-1)*r),m.array[E]=_[E]*(1-.55*r)}h.needsUpdate=!0,d.needsUpdate=!0,m.needsUpdate=!0}for(const f of this.tiered){const h=f.pts.geometry.attributes.aSize,d=h.array,m=1+(f.ds-1)*r;for(let g=0;g<d.length;g++)d[g]=f.baseSize[g]*m;if(h.needsUpdate=!0,f.baseOp){const g=f.pts.geometry.attributes.aOpacity,p=g.array,_=1+(f.dop-1)*r;for(let v=0;v<p.length;v++)p[v]=f.baseOp[v]*_;g.needsUpdate=!0}}for(const f of this.colored){const h=f.pts.geometry.attributes.aColor,d=h.array;for(let m=0;m<d.length;m++)d[m]=f.plan[m]+(f.deep[m]-f.plan[m])*i;h.needsUpdate=!0}for(const f of this.coreLerp){const h=f.pts.geometry.attributes.aCore,d=h.array;for(let m=0;m<d.length;m++)d[m]=f.plan[m]+(f.deep[m]-f.plan[m])*i;h.needsUpdate=!0}for(const f of this.dustRiver)f.mat.opacity=f.base*r,f.spr.visible=f.mat.opacity>.004;this.applyBackground(i,this.state.duskPos),this.fxPass.enabled=!this.softGL&&r>.02,this.bloom.intensity=.7*r*this.state.bloom,this.vignette.style.opacity=String(.55+.45*i);const o=String(1-i),l=this.opts.domRefs;l!=null&&l.cartouche&&(l.cartouche.style.opacity=o),l!=null&&l.briefing&&(l.briefing.style.opacity=o),l!=null&&l.toggle&&(l.toggle.textContent=e>.5?"图":"境"),(u=(c=this.opts).onMorph)==null||u.call(c,e)}screenOf(e){const t=new $(e[0],e[1],e[2]??0);this.chart.localToWorld(t),t.project(this.camera);const i=this.heart.getBoundingClientRect();return[i.left+(t.x*.5+.5)*i.width,i.top+(-t.y*.5+.5)*i.height]}onPointerMove(e){this.hoverIdx=-1;let t=26;this.hoverables.forEach((i,r)=>{const[s,a]=this.screenOf(i.pos()),o=Math.hypot(s-e.clientX,a-e.clientY);o<t&&(t=o,this.hoverIdx=r)})}updateTooltip(){const e=this.tooltip;if(this.hoverIdx<0||!this.hoverables[this.hoverIdx]){e.style.display="none";return}const t=this.hoverables[this.hoverIdx],[i,r]=this.screenOf(t.pos());e.innerHTML='<div class="tt-title"></div><div class="tt-info"></div>',e.querySelector(".tt-title").textContent=t.title,e.querySelector(".tt-info").textContent=t.info,e.style.display="block";const s=e.offsetWidth;e.style.left=Math.min(window.innerWidth-s-12,i+16)+"px",e.style.top=Math.max(10,r-44)+"px"}detailRows(e){var a,o;const t=this.snapshot;if(e.kind==="north"){const l=t.north;return this.northVacant?[["类型","北极星 · 虚位"],["铭文","（尚未立星 — 点「重刻」写下北极星）"]]:[["类型","北极星"],["铭文",l.full||t.north_star],["简称",l.brief||"—"],["可见性",l.visibility==="public"?"可公开":"仅本地"]]}if(e.kind==="goal"){const l=t.goals.find(f=>f.id===e.id)??{status:((a=this.L.goals[e.idx])==null?void 0:a.status)??"active",start:"",target:"",summary:""},c=l.status==="completed"?"已镌刻":l.status==="paused"?"已暂停":"进行中",u=(o=this.L.goals[e.idx])==null?void 0:o.seatName;return[["状态",c],...u?[["星位",u]]:[],["起始",l.start||"—"],["目标",l.target||"—"],["铭文",l.summary||"—"]]}if(e.kind==="planet"){const l=t.projects[e.idx],c=this.L.planets[e.idx].goalIndex;return[["状态",l.status==="active"?"在轨":"归档"],["所属目标",c>=0?this.L.goals[c].title:"（自由轨道）"],["任务",`${l.task_count} 项`],["进度",l.progress===null||l.progress===void 0?"—":`${Math.round(l.progress*100)}%`],["时间范围",l.time_range||"—"]]}if(e.kind==="guest"){const l=t.evidence.find(c=>c.id===this.L.guests[e.idx].id)??this.L.guests[e.idx];return[["类型","type"in l?l.type:"—"],["强度",l.strength||"—"],["日期",l.date||"—"],["评审","review_status"in l&&l.review_status==="needs_review"?"待评审":"已入座"],["摘要","summary"in l&&l.summary?l.summary:"—"]]}const i=this.L.lit.skills[e.idx],r=t.evidence.filter(l=>l.skill_ids.includes(i.id)).slice(0,3).map(l=>l.title),s=[["类别",i.category],["状态",i.status],["关联证据",`${i.evidenceCount} 条`]];return r.forEach((l,c)=>s.push([c===0?"入座证据":"",`· ${l}`])),s}openDetail(e){var i,r;this.selectedIdx=e;const t=this.clickables[e];(r=(i=this.opts).onSelect)==null||r.call(i,{kind:t.kind,id:t.id,title:t.title,rows:this.detailRows(t)})}closeDetail(){var e,t;this.selectedIdx<0||(this.selectedIdx=-1,this.selRing.visible=!1,(t=(e=this.opts).onSelect)==null||t.call(e,null))}onClick(e){if(this.dragDist>6){this.dragDist=0;return}const t=e.target;if(!t.isConnected||t.closest("[data-starmap-ui]"))return;let i=-1,r=26;this.clickables.forEach((s,a)=>{const[o,l]=this.screenOf(s.pos()),c=Math.hypot(o-e.clientX,l-e.clientY);c<r&&(r=c,i=a)}),i>=0?this.openDetail(i):this.closeDetail()}updatePointScale(){const t=this.renderer.domElement.height/(2*Math.tan(this.camera.fov*Math.PI/360));for(const i of this.morphables){const r=i;r.isPoints&&(r.material.uniforms.uScale.value=t)}}onResize(){const e=this.heart.clientWidth||1,t=this.heart.clientHeight||1;this.renderer.setSize(e,t),this.composer.setSize(e,t),this.camera.aspect=e/t,this.camera.updateProjectionMatrix(),this.fitPlanCamera(),this.controls&&(this.controls.minDistance=this.camPlan.pos.z*.65,this.controls.maxDistance=this.camPlan.pos.z*1.6),this.updatePointScale(),this.applyMorph()}loop(){if(this.disposed)return;this.rafId=requestAnimationFrame(()=>this.loop());const e=Math.min(this.clock.getDelta(),.1),t=this.clock.elapsedTime,{ch2:i,ch3:r}=this.state,s=this.L,a=performance.now(),l=this.dragging||this.hoverIdx>=0||this.selectedIdx>=0||a-this.lastPointerActive<3e3||this.reducedMotion?0:1;this.spinFactor+=(l-this.spinFactor)*Math.min(1,e/.8);const c=Math.PI*2/3600;this.chart.rotation.z+=e*c*this.spinFactor*(1+2.5*Math.sin(i*Math.PI)),!this.dragging&&Math.abs(this.spinVel)>1e-4&&(this.chart.rotation.z+=this.spinVel*e,this.spinVel*=Math.exp(-e/1.2)),this.bgLayer.rotation.z=-.7*i*this.chart.rotation.z;const u=(d,m,g)=>[d*Math.cos(g)-m*Math.sin(g),d*Math.sin(g)+m*Math.cos(g)];{const d=this.goalPts.geometry.attributes.position,m=s.goals.map((M,T)=>{const x=this.goalDeepBase[T];this.goalPhase[T]+=e*(2*Math.PI/this.goalPeriods[T])*r;const[y,w]=u(x[0],x[1],this.goalPhase[T]);return[M.plan[0]+(x[0]-M.plan[0])*i+(y-x[0]),M.plan[1]+(x[1]-M.plan[1])*i+(w-x[1]),M.plan[2]+(x[2]-M.plan[2])*i]});m.forEach((M,T)=>d.setXYZ(T,M[0],M[1],M[2])),d.needsUpdate=!0;const g=1+.9*i;for(const M of this.goalLabelGroups){if(!M.base.length)continue;const T=m[M.goalIdx],x=s.goals[M.goalIdx].plan;M.segs.forEach((y,w)=>y.position.set(T[0]+(M.base[w][0]-x[0])*g,T[1]+(M.base[w][1]-x[1])*g,0))}const p=this.planetPts.geometry.attributes.position,_=this.planetInnerPts.geometry.attributes.position,v=this.moonPts.geometry.attributes.position,b=s.planets.map((M,T)=>{const x=this.planetDeepBase[T];this.planetPhase[T]+=e*(2*Math.PI/this.planetPeriods[T])*r;const y=M.goalIndex,w=y>=0?this.goalDeepBase[y]:[0,0,0],C=y>=0?m[y]:[0,0,0],[R,L]=u(x[0]-w[0],x[1]-w[1],this.planetPhase[T]),U=M.plan[0]+(x[0]-M.plan[0])*i,I=M.plan[1]+(x[1]-M.plan[1])*i;return[U+(C[0]-w[0])+(R-(x[0]-w[0])),I+(C[1]-w[1])+(L-(x[1]-w[1])),M.plan[2]+(x[2]-M.plan[2])*i]});b.forEach((M,T)=>{p.setXYZ(T,M[0],M[1],M[2]),_.setXYZ(T,M[0],M[1],M[2])}),p.needsUpdate=!0,_.needsUpdate=!0,this.moonDeepBase.forEach((M,T)=>{const x=this.moonPlanet[T];x!==void 0&&v.setXYZ(T,M[0]+(b[x][0]-this.planetDeepBase[x][0]),M[1]+(b[x][1]-this.planetDeepBase[x][1]),M[2])}),v.needsUpdate=!0;for(const M of this.orbitRings){const T=m[M.goalIdx];M.ring.position.set(T[0],T[1],T[2]);const x=this.reducedMotion?1:.92+.08*Math.sin(t*.5+M.shimmer);M.ringMat.opacity=.22*r*x,M.ring.visible=M.ringMat.opacity>.004,this.reducedMotion?(M.flowMat.opacity=0,M.flow.visible=!1):(M.phase+=e*(2*Math.PI/46),M.flow.rotation.z=M.phase,M.flowMat.opacity=.5*r*x,M.flow.visible=M.flowMat.opacity>.004)}const S=this.guestPts.geometry.attributes.position,E=this.guestTails.geometry.attributes.position;s.guests.forEach((M,T)=>{const x=this.guestDeepBase[T];this.guestPhase[T]+=e*(2*Math.PI/this.guestPeriods[T])*r;const y=4*r,w=M.plan[0]+(x[0]-M.plan[0])*i+y*Math.cos(this.guestPhase[T]+T*1.3),C=M.plan[1]+(x[1]-M.plan[1])*i+y*Math.sin(this.guestPhase[T]+T*1.3),R=M.plan[2]+(x[2]-M.plan[2])*i;S.setXYZ(T,w,C,R),this.guestGlows[T].spr.position.set(w,C,R),this.tailOffsets[T].forEach((U,I)=>E.setXYZ(T*10+I,w+U[0]*i,C+U[1]*i,R+U[2]*i))}),S.needsUpdate=!0,E.needsUpdate=!0}for(const d of this.labelObjs)d.fade!=="band"&&(d.t.rotation.z=d.rotZ-this.chart.rotation.z*i);this.collisionTick+=1;const f=i>.6;if(f&&this.collisionTick%12===0){const m=this.labelObjs.filter(p=>p.fade!=="band"&&p.t.visible&&p.t.textRenderInfo).map(p=>{const[_,v]=this.screenOf([p.t.position.x,p.t.position.y,0]),b=p.t.textRenderInfo.blockBounds,S=Math.max(.5,b[2]-b[0]),E=Math.max(.5,b[3]-b[1]),[M]=this.screenOf([p.t.position.x+1,p.t.position.y,0]),T=Math.abs(M-_)||1,x=S*T,y=E*T,w=p.t.anchorX==="left"?0:p.t.anchorX==="right"?-x:-x/2;return{r:p,x0:_+w,y0:v-y/2,x1:_+w+x,y1:v+y/2}}),g=new Set;for(let p=0;p<m.length;p++)for(let _=p+1;_<m.length;_++){const v=m[p],b=m[_];v.r.grpId===b.r.grpId||!(Math.min(v.x1,b.x1)-Math.max(v.x0,b.x0)>1&&Math.min(v.y1,b.y1)-Math.max(v.y0,b.y0)>1)||g.add(v.r.prio===b.r.prio?Math.max(v.r.grpId,b.r.grpId):v.r.prio>b.r.prio?v.r.grpId:b.r.grpId)}for(const p of this.labelObjs)p.caTarget=g.has(p.grpId)?0:1}else if(!f)for(const d of this.labelObjs)d.caTarget=1;for(const d of this.labelObjs){if(d.fade==="band")continue;d.ca+=(d.caTarget-d.ca)*Math.min(1,e/.35);const m=d.fade==="north"?1-.25*i:1;d.t.material.opacity=m*d.ca}const h=d=>d<.25?.5-.5*Math.cos(d/.25*Math.PI):d<.45?1:.5+.5*Math.cos((d-.45)/.55*Math.PI);if(this.reducedMotion)for(const d of this.guestGlows)d.mat.opacity=(.34+.3*r)*.925,d.spr.visible=d.mat.opacity>.004;else for(const d of this.guestGlows){const m=.34+.3*r,g=d.breathe?h((t/11+d.idx*.31)%1):.4;d.mat.opacity=m*(.85+.15*g),d.spr.visible=d.mat.opacity>.004;const p=5.5*(1+.4*r);d.spr.scale.set(p,p,1)}{const d=this.guestPts.geometry.attributes.aOpacity;let m=!1;for(let g=0;g<d.array.length;g++)d.array[g]!==this.guestBaseOpacity[g]&&(d.array[g]=this.guestBaseOpacity[g],m=!0);m&&(d.needsUpdate=!0)}if(this.updateTooltip(),this.northVacant){const d=this.northPts.geometry.attributes.aOpacity;d.array[0]=this.reducedMotion?.3:.28+.14*Math.sin(t*.9),d.needsUpdate=!0}if(this.selectedIdx>=0){const d=this.clickables[this.selectedIdx].pos();this.selRing.visible=!0,this.selRing.position.set(d[0],d[1],d[2]??0);const m=this.reducedMotion?1:1+.04*Math.sin(t*3);this.selRing.scale.set(m,m,1)}if(this.controls){this.controls.enabled=this.state.t<.5,this.controls.update();const d=this.controls.target,m=Math.max(-70,Math.min(70,d.x)),g=Math.max(-70,Math.min(70,d.y));(m!==d.x||g!==d.y)&&(this.camera.position.x+=m-d.x,this.camera.position.y+=g-d.y,d.x=m,d.y=g,d.z=0)}this.fxPass.enabled?this.composer.render():this.renderer.render(this.scene,this.camera)}}const Iw="/assets/title-v2-b-ibfvihIe.svg";function Ow({snapshot:n}){const{name:e=""}=u_(),t=Ze.useRef(null),i=Ze.useRef(null),r=Ze.useRef(null),s=Ze.useRef(null),a=Ze.useRef(null),o=Ze.useRef(null),l=Ze.useRef(null),[c,u]=Ze.useState(null),[f,h]=Ze.useState(!1),[d,m]=Ze.useState(!1),[g,p]=Ze.useState(!1),[_,v]=Ze.useState(()=>localStorage.getItem("nblane.starmap.reveal")==="1"),b=Ze.useRef(_);b.current=_;const S=h_(e);Ze.useEffect(()=>{const M=t.current,T=i.current;if(!M||!T)return;let x=null;try{x=new Lw(M,T,n,{onSelect:w=>{l.current=null,u(w)},domRefs:{cartouche:r.current,briefing:s.current,toggle:a.current},reveal:b.current})}catch{p(!0);return}o.current=x;const y=l.current;if(y&&performance.now()-y.at<6e3){if(!x.focusStar(y.id)){l.current=null;const w=n.goals.find(C=>C.id===y.id);w&&u({kind:"goal",id:w.id,title:w.title,rows:ed(w)})}}else l.current=null;return()=>{x==null||x.dispose(),o.current=null}},[n]);const E=Ze.useMemo(()=>{var T;const M=`「${n.counts.evidence_needs_review} 条客星待评审，${n.counts.projects_active} 颗行星在轨。」`;return p_(M,d_(((T=S.data)==null?void 0:T.entries)??[]))},[n,S.data]);return Ze.useEffect(()=>{const M=T=>{var x;T.key==="Escape"&&(h(!1),m(!1),u(null),l.current=null,(x=o.current)==null||x.deselect())};return window.addEventListener("keydown",M),()=>window.removeEventListener("keydown",M)},[]),ne.jsxs("div",{className:`starmap-root${d?" divining":""}`,ref:t,"data-testid":"starmap-root",children:[ne.jsxs("div",{className:"starmap-layout",children:[ne.jsx("div",{className:"starmap-mount-top",children:ne.jsx("img",{className:"starmap-cartouche",ref:r,src:Iw,alt:"成长星图"})}),ne.jsx("div",{className:"starmap-heart",ref:i,"data-testid":"starmap-heart"}),ne.jsx("div",{className:"starmap-mount-bottom",children:ne.jsx("div",{className:"starmap-briefing",ref:s,"data-testid":"starmap-briefing",children:E})})]}),!g&&ne.jsxs(ne.Fragment,{children:[ne.jsx("button",{type:"button",className:"starmap-div-btn","data-starmap-ui":!0,"data-testid":"starmap-div-btn","aria-label":"占卜","aria-pressed":d,title:"占卜 — 星尘聚卦",onClick:()=>m(M=>!M),children:"卜"}),ne.jsx("button",{type:"button",className:"starmap-toggle",ref:a,"data-starmap-ui":!0,"data-testid":"starmap-toggle","aria-label":"切换 境态/图态",title:"境态 ⇄ 图态",onClick:()=>{var M;return(M=o.current)==null?void 0:M.toggle()},children:"境"}),ne.jsx("button",{type:"button",className:"starmap-reveal-toggle","data-starmap-ui":!0,"data-testid":"starmap-reveal-toggle","aria-pressed":_,"aria-label":"显真",title:_?"真·朱文 — 点击钤回古名":"真·白文 — 点击显现真名（已记住此偏好）",onClick:()=>{var T;const M=!_;v(M),localStorage.setItem("nblane.starmap.reveal",M?"1":"0"),(T=o.current)==null||T.setReveal(M)},children:"真"}),ne.jsx("button",{type:"button",className:"starmap-catalog-btn","data-starmap-ui":!0,"data-testid":"starmap-catalog-btn","aria-label":"星表","aria-expanded":f,onClick:()=>h(M=>!M),children:"＋"})]}),ne.jsx(y_,{profile:e}),ne.jsx(__,{profile:e,open:d,onClose:()=>m(!1)}),ne.jsx(w_,{open:f,snapshot:n,profile:e,selection:c,onFocus:M=>{var y;if(((y=o.current)==null?void 0:y.focusStar(M))??!1){l.current={id:M,at:performance.now()};return}l.current=null;const x=n.goals.find(w=>w.id===M);x&&u({kind:"goal",id:x.id,title:x.title,rows:ed(x)})}}),ne.jsx("div",{className:`starmap-detail${c?" open":""}`,"data-starmap-ui":!0,"data-testid":"starmap-detail",children:c&&ne.jsx(M_,{selection:c,snapshot:n,profile:e,onSaved:u},`${c.kind}:${c.id}`)}),g&&ne.jsxs("div",{className:"starmap-fallback","data-testid":"starmap-fallback",children:[ne.jsx("div",{className:"fb-title",children:"成长星图"}),ne.jsx("div",{className:"fb-line",children:n.north.is_set?n.north_star:"尚未设置北极星 — 北极星虚位以待。"}),ne.jsx("div",{className:"fb-line",children:E}),ne.jsx("div",{className:"fb-line",children:"此浏览器不支持 WebGL，以上为静态简报。"})]})]})}export{Ow as StarmapView};
